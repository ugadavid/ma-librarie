import io
import zipfile
import zlib
from pathlib import Path
from unicodedata import normalize
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree
from .i18n import error_text, msg

try:
    from pypdf import PdfReader, apply_configuration
except ImportError:
    PdfReader = None


BOOK_EXTENSIONS = frozenset(("epub", "mobi", "pdf", "azw", "azw3"))
XML_LIMIT = 2 * 1024 * 1024
PDF_LIMIT = 64 * 1024 * 1024
EPUB_LIMIT = 128 * 1024 * 1024
PACKAGE_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
DC = "{http://purl.org/dc/elements/1.1/}"
OPF = "{http://www.idpf.org/2007/opf}"
EMPTY = ("", "")


class MetadataError(ValueError):
    pass


class MetadataTree(ElementTree.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise MetadataError(msg("declaration_dtd_ignoree"))


def read_xml(stream):
    data = stream.read(XML_LIMIT + 1)
    if len(data) > XML_LIMIT:
        raise MetadataError(msg("metadonnees_xml_trop_volumineuses"))
    try:
        return ElementTree.fromstring(data, parser=ElementTree.XMLParser(target=MetadataTree()))
    except ElementTree.ParseError as exc:
        raise MetadataError(error_text(exc)) from exc


def clean(value):
    return " ".join(value.split())[:4096] if isinstance(value, str) else ""


def opf_fields(package):
    metadata = package.find(f"{OPF}metadata")
    if metadata is None:
        metadata = package.find("metadata")
    if metadata is None:
        return EMPTY
    return tuple(
        clean(" / ".join(dict.fromkeys(
            value for node in metadata.iter(f"{DC}{tag}")
            if (value := clean("".join(node.itertext())))
        )))
        for tag in ("title", "creator")
    )


def epub_package(book):
    with book.open("META-INF/container.xml") as container:
        package = read_xml(container).find(f".//{{{PACKAGE_NS}}}rootfile")
    if package is None:
        raise MetadataError(msg("paquet_epub_introuvable"))
    name = package.attrib["full-path"]
    if any(part in ("", ".", "..") for part in name.split("/")) or ":" in name or "\\" in name:
        raise MetadataError(msg("reference_de_paquet_epub_non_locale"))
    with book.open(name) as opf:
        return name, read_xml(opf)


def epub_metadata(path):
    try:
        with path.open("rb") as stream:
            stream.seek(0, 2)
            if stream.tell() > EPUB_LIMIT:
                raise MetadataError(msg("epub_trop_volumineux_pour_lextraction"))
            stream.seek(0)
            with zipfile.ZipFile(stream) as book:
                _, package = epub_package(book)
                return opf_fields(package)
    except (KeyError, zipfile.BadZipFile, EOFError, RuntimeError, zlib.error) as exc:
        raise MetadataError(error_text(exc)) from exc


def pdf_metadata(path):
    if PdfReader is None:
        return None
    if path.stat().st_size > PDF_LIMIT:
        raise MetadataError(msg("pdf_trop_volumineux_pour_lextraction"))
    with path.open("rb") as stream:
        data = stream.read(PDF_LIMIT + 1)
    if len(data) > PDF_LIMIT:
        raise MetadataError(msg("pdf_trop_volumineux_pour_lextraction"))
    with apply_configuration(xmp_maximum_input_length=XML_LIMIT, jbig2dec_binary=None):
        try:
            reader = PdfReader(io.BytesIO(data), strict=True, xref_stream_maximum_entries=250_000)
            if reader.is_encrypted:
                return EMPTY
        except Exception as exc:
            raise MetadataError(error_text(exc)) from exc
        try:
            info = reader.metadata
            title, author = (clean(info.title), clean(info.author)) if info else EMPTY
        except Exception:
            title, author = EMPTY
        if not title or not author:
            try:
                xmp = reader.xmp_metadata
                if xmp is not None:
                    titles = xmp.dc_title or {}
                    title = title or clean(titles.get("x-default") or next(iter(titles.values()), ""))
                    authors = (clean(name) for name in xmp.dc_creator or ())
                    author = author or clean(" / ".join(filter(None, authors)))
            except Exception:
                # A malformed optional XMP packet cannot invalidate the Info dictionary.
                pass
        return title, author


def normalized(value):
    return normalize("NFC", clean(value).casefold())


def explicit_names(package):
    names = set()
    for tag in ("manifest/item", "guide/reference"):
        namespaced = "/".join(f"{OPF}{part}" for part in tag.split("/"))
        for node in [*package.findall(tag), *package.findall(namespaced)]:
            try:
                uri = urlsplit(node.get("href", ""))
            except ValueError:
                continue
            filename = unquote(uri.path).removeprefix("./")
            if (not (uri.scheme or uri.netloc or uri.query)
                    and not any(char in filename for char in "/\\:\0")
                    and Path(filename).suffix.removeprefix(".").casefold() in BOOK_EXTENSIONS):
                names.add(normalized(filename))
    return names


def companion_metadata(path, book_names):
    """Return the fields and all formats of a single, unambiguously matched stem."""
    with path.open("rb") as stream:
        package = read_xml(stream)
    if package.tag not in ("package", f"{OPF}package"):
        raise MetadataError(msg("paquet_opf_introuvable"))
    fields = opf_fields(package)
    references = explicit_names(package)
    stems = {name: normalized(Path(name).stem) for name in book_names}
    if references:
        matches = {stem for name, stem in stems.items() if normalized(name) in references}
    else:
        title = normalized(fields[0])
        authors = [normalized(author) for author in fields[1].split(" / ")]
        matches = {
            stem for stem in stems.values()
            if title and (stem == title or any(
                author and stem == f"{title} - {author}" for author in authors
            ))
        }
    if len(matches) != 1:
        return EMPTY, set()
    stem, = matches
    formats = {name for name, base in stems.items() if base == stem}
    extensions = {Path(name).suffix.casefold() for name in formats}
    return (fields, formats) if len(formats) == len(extensions) else (EMPTY, set())


def stored_fields(old, origin):
    return tuple(old[field] if old and old[f"{field}_source"] == origin else ""
                 for field in ("title", "author"))


def book_metadata(path, extension, size, modified, old, companion, errors, label):
    native = EMPTY
    origin = f"{extension}-embedded"
    if extension in ("epub", "pdf"):
        previous = stored_fields(old, origin)
        if old and all(previous) and old["size"] == size and old["modified"] == modified:
            native = previous
        else:
            try:
                reader = epub_metadata if extension == "epub" else pdf_metadata
                native = reader(path)
                if native is None:  # PDF reader absent.
                    native = previous
            except OSError as exc:
                errors.append(msg("metadata_error", path=label, format=extension.upper(), error=error_text(exc)))
                native = previous
            except MetadataError as exc:
                if extension == "epub":
                    errors.append(msg("metadata_error", path=label, format="EPUB", error=error_text(exc)))

    if companion is None:  # A previously associated OPF could not be checked.
        companion = stored_fields(old, "opf")
    values = tuple(primary or fallback for primary, fallback in zip(native, companion))
    origins = tuple(origin if primary else "opf" if fallback else ""
                    for primary, fallback in zip(native, companion))
    return (*values, *origins)
