from __future__ import annotations
import codecs
import re
from .structures import ImmutableList


class Accept(ImmutableList):

    def __init__(self, values=()):
        if values is None:
            list.__init__(self)
            self.provided = False
        elif isinstance(values, Accept):
            self.provided = values.provided
            list.__init__(self, values)
        else:
            self.provided = True
            values = sorted(
                values, key=lambda x: (self._specificity(x[0]), x[1]), reverse=True
            )
            list.__init__(self, values)

    def _specificity(self, value):
        return (value != "*",)

    def _value_matches(self, value, item):
        return item == "*" or item.lower() == value.lower()

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.quality(key)
        return list.__getitem__(self, key)

    def quality(self, key):
        for item, quality in self:
            if self._value_matches(key, item):
                return quality
        return 0

    def __contains__(self, value):
        for item, _quality in self:
            if self._value_matches(value, item):
                return True
        return False

    def __repr__(self):
        pairs_str = ", ".join(f"({x!r}, {y})" for x, y in self)
        return f"{type(self).__name__}([{pairs_str}])"

    def index(self, key):
        if isinstance(key, str):
            for idx, (item, _quality) in enumerate(self):
                if self._value_matches(key, item):
                    return idx
            raise ValueError(key)
        return list.index(self, key)

    def find(self, key):
        try:
            return self.index(key)
        except ValueError:
            return -1

    def values(self):
        for item in self:
            yield item[0]

    def to_header(self):
        result = []
        for value, quality in self:
            if quality != 1:
                value = f"{value};q={quality}"
            result.append(value)
        return ",".join(result)

    def __str__(self):
        return self.to_header()

    def _best_single_match(self, match):
        for client_item, quality in self:
            if self._value_matches(match, client_item):
                return client_item, quality
        return None

    def best_match(self, matches, default=None):
        result = default
        best_quality = -1
        best_specificity = (-1,)
        for server_item in matches:
            match = self._best_single_match(server_item)
            if not match:
                continue
            client_item, quality = match
            specificity = self._specificity(client_item)
            if quality <= 0 or quality < best_quality:
                continue
            if quality > best_quality or specificity > best_specificity:
                result = server_item
                best_quality = quality
                best_specificity = specificity
        return result

    @property
    def best(self):
        if self:
            return self[0][0]


_mime_split_re = re.compile("/|(?:\\s*;\\s*)")


def _normalize_mime(value):
    return _mime_split_re.split(value.lower())


class MIMEAccept(Accept):

    def _specificity(self, value):
        return tuple(x != "*" for x in _mime_split_re.split(value))

    def _value_matches(self, value, item):
        if "/" not in item:
            return False
        if "/" not in value:
            raise ValueError(f"invalid mimetype {value!r}")
        normalized_value = _normalize_mime(value)
        value_type, value_subtype = normalized_value[:2]
        value_params = sorted(normalized_value[2:])
        if value_type == "*" and value_subtype != "*":
            raise ValueError(f"invalid mimetype {value!r}")
        normalized_item = _normalize_mime(item)
        item_type, item_subtype = normalized_item[:2]
        item_params = sorted(normalized_item[2:])
        if item_type == "*" and item_subtype != "*":
            return False
        return (
            (
                item_type == "*"
                and item_subtype == "*"
                or value_type == "*"
                and value_subtype == "*"
            )
            or item_type == value_type
            and (
                item_subtype == "*"
                or value_subtype == "*"
                or item_subtype == value_subtype
                and item_params == value_params
            )
        )

    @property
    def accept_html(self):
        return (
            "text/html" in self or "application/xhtml+xml" in self or self.accept_xhtml
        )

    @property
    def accept_xhtml(self):
        return "application/xhtml+xml" in self or "application/xml" in self

    @property
    def accept_json(self):
        return "application/json" in self


_locale_delim_re = re.compile("[_-]")


def _normalize_lang(value):
    return _locale_delim_re.split(value.lower())


class LanguageAccept(Accept):

    def _value_matches(self, value, item):
        return item == "*" or _normalize_lang(value) == _normalize_lang(item)

    def best_match(self, matches, default=None):
        result = super().best_match(matches)
        if result is not None:
            return result
        fallback = Accept(
            [(_locale_delim_re.split(item[0], 1)[0], item[1]) for item in self]
        )
        result = fallback.best_match(matches)
        if result is not None:
            return result
        fallback_matches = [_locale_delim_re.split(item, 1)[0] for item in matches]
        result = super().best_match(fallback_matches)
        if result is not None:
            return next(item for item in matches if item.startswith(result))
        return default


class CharsetAccept(Accept):

    def _value_matches(self, value, item):

        def _normalize(name):
            try:
                return codecs.lookup(name).name
            except LookupError:
                return name.lower()

        return item == "*" or _normalize(value) == _normalize(item)
