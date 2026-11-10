"""Catalogue messages carry their French value and render only at the UI boundary."""
import json
from pathlib import Path


LANGUAGES = {"fr": "Français", "en": "English", "es": "Español"}
_DIRECTORY = Path(__file__).with_name("locales")
CATALOGUES = {
    language: json.loads((_DIRECTORY / f"{language}.json").read_text(encoding="utf-8"))
    for language in LANGUAGES
}


def language_code(value):
    return value if value in LANGUAGES else "fr"


class Message(str):
    def __new__(cls, key, fields, *, separator=None, parts=()):
        message = super().__new__(cls, cls._format("fr", key, fields, separator, parts))
        message.key = key
        message.fields = fields
        message.separator = separator
        message.parts = parts
        return message

    @staticmethod
    def _format(language, key, fields, separator, parts):
        if separator is not None:
            return separator.join(str(render(part, language)) for part in parts)
        if key not in CATALOGUES[language]:
            language = "fr"
        template = CATALOGUES[language].get(key, key)
        return template.format(**{name: render(value, language) for name, value in fields.items()})

    def localized(self, language):
        return self._format(language, self.key, self.fields, self.separator, self.parts)


def msg(key, **fields):
    return Message(key, fields)


def plural(key, count, **fields):
    form = "one" if count == 1 else "other"
    return msg(f"{key}.{form}", count=count, **fields)


def join(separator, parts):
    return Message(None, {}, separator=separator, parts=tuple(parts))


def render(value, language):
    return value.localized(language_code(language)) if isinstance(value, Message) else value


def error_text(exc):
    if len(exc.args) == 1 and isinstance(exc.args[0], Message):
        return exc.args[0]
    return str(exc) or type(exc).__name__
