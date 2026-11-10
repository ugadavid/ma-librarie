import ctypes
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from ctypes import wintypes
from .i18n import msg


class SourceProblem(OSError):
    def __init__(self, state, message):
        super().__init__(message)
        self.state = state


@dataclass(frozen=True)
class Location:
    path: Path
    volume: str
    relative: str

    @property
    def scan_path(self):
        return Path(self.volume) / self.relative


def is_reparse(info):
    return bool(info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def locate(folder):
    """Resolve an existing directory and identify its local Windows volume."""
    try:
        path = Path(folder).resolve(strict=True)
        if not stat.S_ISDIR(path.stat().st_mode):
            raise SourceProblem("offline", msg("le_dossier_source_est_introuvable"))
    except FileNotFoundError as exc:
        raise SourceProblem("offline", msg("le_dossier_source_est_introuvable")) from exc
    except SourceProblem:
        raise
    except OSError as exc:
        # Disconnected media may report device/drive errors instead of ENOENT.
        if getattr(exc, "winerror", None) in (3, 15, 21, 55, 1167):
            raise SourceProblem("offline", msg("le_volume_est_indisponible")) from exc
        raise SourceProblem("error", str(exc)) from exc

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    mount = ctypes.create_unicode_buffer(32768)
    volume = ctypes.create_unicode_buffer(64)
    for name, source, result in (
        ("GetVolumePathNameW", str(path), mount),
        ("GetVolumeNameForVolumeMountPointW", mount, volume),
    ):
        call = getattr(kernel, name)
        call.argtypes = (wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD)
        call.restype = wintypes.BOOL
        if not call(source, result, len(result)):
            raise SourceProblem("relocate", msg("volume_non_identifiable_relocalisez_la_source"))
    return Location(path, volume.value.lower(), os.path.relpath(path, mount.value))


def verify(folder, volume, relative):
    try:
        current = locate(folder)
    except SourceProblem as exc:
        if exc.state == "offline":
            # A reassigned drive may not have the original directory at all.
            for parent in Path(folder).parents:
                try:
                    ancestor = locate(parent)
                except SourceProblem as problem:
                    if problem.state != "offline":
                        break
                    continue
                if ancestor.volume != volume:
                    raise SourceProblem(
                        "relocate", msg("le_volume_a_change_relocalisez_le_dossier")
                    ) from exc
                break
        raise
    if (current.volume, current.relative) != (volume, relative):
        raise SourceProblem("relocate", msg("la_source_a_change_relocalisez_le_dossier"))
    return current


def verified_file(folder, volume, relative, file_relative):
    source = verify(folder, volume, relative)
    # Check each component so a new link cannot redirect an indexed path.
    target = source.scan_path
    try:
        for part in Path(file_relative).parts:
            target /= part
            info = target.lstat()
            if is_reparse(info):
                raise SourceProblem("error", msg("le_chemin_passe_desormais_par_un_lien"))
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise SourceProblem("missing", msg("le_fichier_a_disparu_depuis_le_dernier")) from exc
    if not stat.S_ISREG(info.st_mode):
        raise SourceProblem("missing", msg("le_chemin_ne_designe_plus_un_fichier"))
    return source, target, info


def explorer_target(folder, volume, relative, file_relative):
    source, _, _ = verified_file(folder, volume, relative, file_relative)
    verify(folder, volume, relative)
    return source.path / file_relative


def select_in_explorer(path):
    """Ask the Windows shell to select one item by its absolute PIDL."""
    ole = ctypes.OleDLL("ole32")
    shell = ctypes.OleDLL("shell32")
    pidl = ctypes.c_void_p()
    ole.CoInitializeEx.argtypes = (ctypes.c_void_p, wintypes.DWORD)
    ole.CoTaskMemFree.argtypes = (ctypes.c_void_p,)
    ole.CoTaskMemFree.restype = None
    ole.CoUninitialize.restype = None
    shell.SHParseDisplayName.argtypes = (
        wintypes.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
    )
    shell.SHOpenFolderAndSelectItems.argtypes = (
        ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p, wintypes.DWORD,
    )
    ole.CoInitializeEx(None, 2)
    try:
        shell.SHParseDisplayName(str(path), None, ctypes.byref(pidl), 0, None)
        shell.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
    finally:
        ole.CoTaskMemFree(pidl)
        ole.CoUninitialize()
