"""Catalogue local de fichiers pour Windows."""

APP_NAME = "Ma Médiathèque"
EDITORIAL_BRAND = "Trucabule"
__version__ = "alpha-0.1.20"
WINDOWS_VERSION = (*map(int, __version__.removeprefix("alpha-").split(".")), 0)
