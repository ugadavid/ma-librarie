import io
import os
import posixpath
import stat
import struct
import zipfile
import zlib
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .book_metadata import (
    BOOK_EXTENSIONS, EPUB_LIMIT, OPF, MetadataError, companion_metadata, epub_package, normalized,
)
from .windows import SourceProblem, is_reparse, verified_file

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = ImageOps = None


IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_PIXELS = 16_000_000
THUMBNAIL_SIZE = (215, 245)
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
DIRECTORY_LIMIT = 4096


def thumbnail(stream, size):
    data = stream.read(IMAGE_BYTES + 1)
    if len(data) > IMAGE_BYTES:
        return None
    try:
        with Image.open(io.BytesIO(data), formats=("JPEG", "PNG")) as image:
            if image.width * image.height > IMAGE_PIXELS or max(image.size) > 8192:
                return None
            image = ImageOps.exif_transpose(image)
            image.thumbnail(size)
            result = io.BytesIO()
            image.convert("RGBA").save(result, format="PNG")
            return result.getvalue()
    except (OSError, ValueError, SyntaxError, EOFError, OverflowError, struct.error,
            Image.DecompressionBombError):
        return None


def archive_reference(package_name, href):
    try:
        uri = urlsplit(href)
    except ValueError:
        return None
    path = unquote(uri.path)
    if uri.scheme or uri.netloc or uri.query or not path or path.startswith("/"):
        return None
    if any(char in path for char in "\\:\0"):
        return None
    member = posixpath.normpath(posixpath.join(posixpath.dirname(package_name), path))
    if member == ".." or member.startswith("../"):
        return None
    return member


def epub_cover(path, size):
    try:
        with path.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell() > EPUB_LIMIT:
                return None
            stream.seek(0)
            with zipfile.ZipFile(stream) as book:
                name, package = epub_package(book)
                items = [*package.findall(f"{OPF}manifest/{OPF}item"),
                         *package.findall("manifest/item")]
                legacy = next((node.get("content") for node in
                               [*package.findall(f"{OPF}metadata/{OPF}meta"),
                                *package.findall("metadata/meta")]
                               if node.get("name") == "cover"), None)
                declared = [item for item in items if "cover-image" in item.get("properties", "").split()]
                if legacy:
                    declared.extend(item for item in items if item.get("id") == legacy)
                for item in declared[:8]:
                    member = archive_reference(name, item.get("href", ""))
                    if member is None:
                        continue
                    try:
                        with book.open(member) as cover:
                            if data := thumbnail(cover, size):
                                return data
                    except (KeyError, OSError, RuntimeError, EOFError, zlib.error):
                        continue
    except (OSError, MetadataError, KeyError, ValueError, RuntimeError, EOFError, zipfile.BadZipFile,
            zlib.error):
        pass
    return None


def siblings(folder):
    names = []
    complete = True
    with os.scandir(folder) as entries:
        for index, entry in enumerate(entries):
            if index == DIRECTORY_LIMIT:
                return names, False
            suffix = Path(entry.name).suffix.casefold()
            if suffix not in IMAGE_EXTENSIONS and suffix[1:] not in BOOK_EXTENSIONS and (
                    entry.name.casefold() != "metadata.opf"):
                continue
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                complete = False
                continue
            if stat.S_ISREG(info.st_mode) and not is_reparse(info):
                names.append(entry.name)
    return names, complete


def load_cover(row, *, size=THUMBNAIL_SIZE):
    if Image is None:
        return None, "Couvertures indisponibles sans Pillow."

    source_args = row["root_path"], row["volume"], row["root_relative"]
    relative = Path(row["relative"])
    try:
        _, path, _ = verified_file(*source_args, str(relative))
    except SourceProblem as exc:
        return None, ("Couverture indisponible hors ligne." if exc.state == "offline" else
                      "Couverture indisponible pour ce fichier.")
    except OSError:
        return None, "Couverture indisponible pour ce fichier."

    def sibling_path(name):
        return verified_file(*source_args, str(relative.with_name(name)))[1]

    def local_image(name):
        try:
            with sibling_path(name).open("rb") as stream:
                return thumbnail(stream, size)
        except OSError:
            return None

    try:
        names, complete = siblings(path.parent)
    except OSError:
        names, complete = [], False

    named = [name for name in names if Path(name).stem.casefold() == relative.stem.casefold()
             and Path(name).suffix.casefold() in IMAGE_EXTENSIONS and name.casefold() != "cover.jpg"]
    named.sort(key=lambda n: (IMAGE_EXTENSIONS.index(Path(n).suffix.casefold()), n.casefold(), n))
    for name in named[:8]:
        if data := local_image(name):
            return data, "Image de même nom"

    if row["extension"] == "epub":
        if data := epub_cover(path, size):
            return data, "Couverture intégrée à l’EPUB"

    if complete:
        generic = [name for name in names if name.casefold() == "cover.jpg"]
        books = [name for name in names if Path(name).suffix.casefold()[1:] in BOOK_EXTENSIONS]
        sidecars = [name for name in names if name.casefold() == "metadata.opf"]
        # The indexed book is the only title represented by the live siblings,
        # or the companion explicitly disambiguates it using ML-008 rules.
        stems = {normalized(Path(name).stem) for name in books}
        formats = {Path(name).suffix.casefold() for name in books}
        associated = relative.name in books and len(stems) == 1 and len(formats) == len(books)
        if generic and not associated and len(sidecars) == 1:
            try:
                _, matched = companion_metadata(sibling_path(sidecars[0]), books)
                associated = relative.name in matched
            except (OSError, MetadataError):
                pass
        if len(generic) == 1 and associated and (data := local_image(generic[0])):
            return data, "Couverture générique associée"
    return None, "Aucune couverture locale lisible."
