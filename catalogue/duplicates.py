import hashlib
import os
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .windows import SourceProblem, verified_file


BLOCK_SIZE = 1024 * 1024
ISSUE_LABELS = {
    "offline": "Hors ligne",
    "missing": "Absents",
    "error": "Illisibles",
    "changed": "Modifiés pendant la vérification",
}


class Cancelled(Exception):
    pass


@dataclass(frozen=True)
class Issue:
    row: dict
    category: str
    message: str


class ReadProblem(Exception):
    def __init__(self, row, category, message):
        super().__init__(message)
        self.issue = Issue(row, category, message)


@dataclass(frozen=True)
class Copy:
    row: dict
    size: int
    signature: tuple


@dataclass(frozen=True)
class Result:
    groups: list
    issues: list


def signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def identity(row):
    return row["volume"], row["volume_path"]


def changed(row):
    return ReadProblem(row, "changed", "Le fichier a changé pendant la vérification.")


@contextmanager
def checked_reader(row, expected=None):
    args = row["root_path"], row["volume"], row["root_relative"], row["relative"]
    try:
        source, target, info = verified_file(*args)
        if info.st_dev != Path(source.volume).stat().st_dev:
            raise ReadProblem(row, "error", "Le fichier est sur un autre volume.")
        path_signature = signature(info)
        with target.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            handle_signature = signature(opened)
            # Windows can report a different ctime for path and handle lookups.
            # Compare that field only between observations made the same way.
            if handle_signature[:4] != path_signature[:4]:
                raise changed(row)
            if expected is not None and expected != handle_signature:
                raise changed(row)
            yield stream, opened
            if signature(os.fstat(stream.fileno())) != handle_signature:
                raise changed(row)
        _, _, info = verified_file(*args)
        if signature(info) != path_signature:
            raise changed(row)
    except SourceProblem as exc:
        if expected is not None and exc.state == "missing":
            raise changed(row) from exc
        category = exc.state if exc.state in ("offline", "missing") else "error"
        raise ReadProblem(row, category, str(exc)) from exc
    except FileNotFoundError as exc:
        raise changed(row) from exc
    except OSError as exc:
        raise ReadProblem(row, "error", str(exc)) from exc


def read_block(stream, row):
    try:
        return stream.read(BLOCK_SIZE)
    except OSError as exc:
        # Keep the failing side when two files are open for comparison.
        raise ReadProblem(row, "error", str(exc)) from exc


def hash_copy(copy, check):
    digest = hashlib.sha256()
    with checked_reader(copy.row, copy.signature) as (stream, _):
        while True:
            check()
            block = read_block(stream, copy.row)
            if not block:
                break
            digest.update(block)
    return digest.digest()


def same_content(left, right, check):
    with checked_reader(left.row, left.signature) as (first, _):
        with checked_reader(right.row, right.signature) as (second, _):
            while True:
                check()
                a = read_block(first, left.row)
                b = read_block(second, right.row)
                if a != b:
                    return False
                if not a:
                    return True


def compare_bucket(copies, check, record_issue, advance):
    groups = []
    for copy in copies:
        check()
        matched = False
        for group in groups:
            while group:
                try:
                    equal = same_content(copy, group[0], check)
                except ReadProblem as exc:
                    record_issue(exc)
                    if exc.issue.row is copy.row:
                        matched = True  # Exclude this copy from all groups.
                        break
                    group.pop(0)  # Try another stable representative, if any.
                    continue
                if equal:
                    group.append(copy)
                    matched = True
                break
            if matched:
                break
        if not matched:
            groups.append([copy])
        advance()
    return groups


class DuplicateCheck:
    def __init__(self, cancelled, progress):
        self.cancelled = cancelled
        self.progress = progress
        self.issues = {}

    def check(self):
        if self.cancelled.is_set():
            raise Cancelled()

    def record_issue(self, error):
        self.issues[identity(error.issue.row)] = error.issue

    def meter(self, phase, total):
        self.progress(phase, 0, total)
        done = 0
        last = time.monotonic()

        def advance():
            nonlocal done, last
            done += 1
            now = time.monotonic()
            if done == total or now - last >= 0.15:
                self.progress(phase, done, total)
                last = now

        return advance

    def inspect(self, aliases):
        names = sorted({row["collection_name"] for row in aliases}, key=lambda n: (n.casefold(), n))
        issues = []
        for row in aliases:
            self.check()
            row = dict(row, collection_names=" · ".join(names))
            try:
                with checked_reader(row) as (_, info):
                    copy = Copy(row, info.st_size, signature(info))
                return copy
            except ReadProblem as exc:
                issues.append(exc)
        priority = {"changed": 0, "error": 1, "missing": 2, "offline": 3}
        self.record_issue(min(issues, key=lambda exc: priority[exc.issue.category]))
        return None

    def run(self, rows):
        locations = defaultdict(list)
        for row in rows:
            self.check()
            locations[identity(row)].append(row)

        sizes = defaultdict(list)
        advance = self.meter("Vérification des chemins", len(locations))
        for aliases in locations.values():
            copy = self.inspect(aliases)
            if copy is not None:
                sizes[copy.size].append(copy)
            advance()

        candidates = [copy for copies in sizes.values() if len(copies) > 1 for copy in copies]
        fingerprints = defaultdict(list)
        advance = self.meter("Calcul des empreintes SHA-256", len(candidates))
        for copy in candidates:
            self.check()
            try:
                fingerprints[copy.size, hash_copy(copy, self.check)].append(copy)
            except ReadProblem as exc:
                self.record_issue(exc)
            advance()

        buckets = [copies for copies in fingerprints.values() if len(copies) > 1]
        advance = self.meter("Comparaison des contenus", sum(map(len, buckets)))
        groups = []
        for bucket in buckets:
            groups.extend(compare_bucket(bucket, self.check, self.record_issue, advance))

        inspected = [copy for copies in sizes.values() for copy in copies]
        advance = self.meter("Contrôle final de la stabilité", len(inspected))
        for copy in inspected:
            self.check()
            if identity(copy.row) not in self.issues:
                try:
                    with checked_reader(copy.row, copy.signature):
                        pass
                except ReadProblem as exc:
                    self.record_issue(exc)
            advance()

        stable = []
        for group in groups:
            self.check()
            copies = [copy for copy in group if identity(copy.row) not in self.issues]
            if len(copies) > 1:
                stable.append(sorted(copies, key=lambda copy: (
                    copy.row["name"].casefold(), copy.row["full_path"]
                )))
        stable.sort(key=lambda group: (group[0].row["name"].casefold(), group[0].row["full_path"]))
        self.check()
        return Result(stable, list(self.issues.values()))


def find_duplicates(catalogue, collection, extension, scope, library, cancelled, progress, *, shelf=None, locations=None):
    check = DuplicateCheck(cancelled, progress)
    with catalogue.mutation():
        check.check()
        return check.run(catalogue.duplicate_candidates(
            collection, extension, scope, library, shelf=shelf, locations=locations
        ))
