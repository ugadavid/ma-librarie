import sys
from importlib.metadata import distribution
from pathlib import Path
from runpy import run_path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo,
)


root = Path(SPECPATH).resolve().parents[1]
package = root / "catalogue"
product = run_path(str(package / "__init__.py"))
version = product["__version__"]
file_version = (*map(int, version.split(".")), 0)
icon = package / "art" / "Ma-Mediatheque.ico"
metadata = VSVersionInfo(
    ffi=FixedFileInfo(filevers=file_version, prodvers=file_version, fileType=1),
    kids=[
        StringFileInfo([StringTable("040c04b0", [
            StringStruct("CompanyName", product["EDITORIAL_BRAND"]),
            StringStruct("FileDescription", product["APP_NAME"]),
            StringStruct("FileVersion", version),
            StringStruct("InternalName", "Ma-Mediatheque"),
            StringStruct("OriginalFilename", "Ma-Mediatheque.exe"),
            StringStruct("ProductName", product["APP_NAME"]),
            StringStruct("ProductVersion", version),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x040C, 1200])]),
    ],
)

runtime = Path(sys.base_prefix)
notices = [
    (str(runtime / "LICENSE.txt"), "licenses/CPython"),
    (str(runtime / "tcl" / "tk8.6" / "license.terms"), "licenses/Tcl-Tk"),
]
for dependency in ("Pillow", "pypdf", "PyInstaller"):
    package_metadata = distribution(dependency)
    notices.extend(
        (str(package_metadata.locate_file(path)), f"licenses/{dependency}")
        for path in package_metadata.files
        if path.name.lower().startswith(("license", "copying", "notice"))
    )

analysis = Analysis(
    [str(package / "__main__.py")],
    pathex=[str(root)],
    datas=[(str(package / name), f"catalogue/{name}") for name in ("art", "locales")] + notices,
)
bundle = PYZ(analysis.pure)
executable = EXE(
    bundle, analysis.scripts, [],
    exclude_binaries=True,
    name="Ma-Mediatheque",
    console=False,
    icon=str(icon),
    version=metadata,
    upx=False,
)
collection = COLLECT(
    executable, analysis.binaries, analysis.datas,
    name="Ma-Mediatheque",
    upx=False,
)
