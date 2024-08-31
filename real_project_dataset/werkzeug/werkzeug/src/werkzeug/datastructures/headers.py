from __future__ import annotations
import re
import typing as t
from .._internal import _missing
from ..exceptions import BadRequestKeyError
from .mixins import ImmutableHeadersMixin
from .structures import iter_multi_items
from .structures import MultiDict


class Headers:

    def __init__(self, defaults=None):
        self._list = []
        if defaults is not None:
            self.extend(defaults)

    def __getitem__(self, key, _get_mode=False):
        if not _get_mode:
            if isinstance(key, int):
                return self._list[key]
            elif isinstance(key, slice):
                return self.__class__(self._list[key])
        if not isinstance(key, str):
            raise BadRequestKeyError(key)
        ikey = key.lower()
        for k, v in self._list:
            if k.lower() == ikey:
                return v
        if _get_mode:
            raise KeyError()
        raise BadRequestKeyError(key)

    def __eq__(self, other):

        def lowered(item):
            return (item[0].lower(),) + item[1:]

        return other.__class__ is self.__class__ and set(
            map(lowered, other._list)
        ) == set(map(lowered, self._list))

    __hash__ = None

    def get(self, key, default=None, type=None):
        try:
            rv = self.__getitem__(key, _get_mode=True)
        except KeyError:
            return default
        if type is None:
            return rv
        try:
            return type(rv)
        except ValueError:
            return default

    def getlist(self, key, type=None):
        ikey = key.lower()
        result = []
        for k, v in self:
            if k.lower() == ikey:
                if type is not None:
                    try:
                        v = type(v)
                    except ValueError:
                        continue
                result.append(v)
        return result

    def get_all(self, name):
        return self.getlist(name)

    def items(self, lower=False):
        for key, value in self:
            if lower:
                key = key.lower()
            yield key, value

    def keys(self, lower=False):
        for key, _ in self.items(lower):
            yield key

    def values(self):
        for _, value in self.items():
            yield value

    def extend(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError(f"update expected at most 1 arguments, got {len(args)}")
        if args:
            for key, value in iter_multi_items(args[0]):
                self.add(key, value)
        for key, value in iter_multi_items(kwargs):
            self.add(key, value)

    def __delitem__(self, key, _index_operation=True):
        if _index_operation and isinstance(key, (int, slice)):
            del self._list[key]
            return
        key = key.lower()
        new = []
        for k, v in self._list:
            if k.lower() != key:
                new.append((k, v))
        self._list[:] = new

    def remove(self, key):
        return self.__delitem__(key, _index_operation=False)

    def pop(self, key=None, default=_missing):
        if key is None:
            return self._list.pop()
        if isinstance(key, int):
            return self._list.pop(key)
        try:
            rv = self[key]
            self.remove(key)
        except KeyError:
            if default is not _missing:
                return default
            raise
        return rv

    def popitem(self):
        return self.pop()

    def __contains__(self, key):
        try:
            self.__getitem__(key, _get_mode=True)
        except KeyError:
            return False
        return True

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def add(self, _key, _value, **kw):
        if kw:
            _value = _options_header_vkw(_value, kw)
        _value = _str_header_value(_value)
        self._list.append((_key, _value))

    def add_header(self, _key, _value, **_kw):
        self.add(_key, _value, **_kw)

    def clear(self):
        del self._list[:]

    def set(self, _key, _value, **kw):
        if kw:
            _value = _options_header_vkw(_value, kw)
        _value = _str_header_value(_value)
        if not self._list:
            self._list.append((_key, _value))
            return
        listiter = iter(self._list)
        ikey = _key.lower()
        for idx, (old_key, _old_value) in enumerate(listiter):
            if old_key.lower() == ikey:
                self._list[idx] = _key, _value
                break
        else:
            self._list.append((_key, _value))
            return
        self._list[idx + 1 :] = [t for t in listiter if t[0].lower() != ikey]

    def setlist(self, key, values):
        if values:
            values_iter = iter(values)
            self.set(key, next(values_iter))
            for value in values_iter:
                self.add(key, value)
        else:
            self.remove(key)

    def setdefault(self, key, default):
        if key in self:
            return self[key]
        self.set(key, default)
        return default

    def setlistdefault(self, key, default):
        if key not in self:
            self.setlist(key, default)
        return self.getlist(key)

    def __setitem__(self, key, value):
        if isinstance(key, (slice, int)):
            if isinstance(key, int):
                value = [value]
            value = [(k, _str_header_value(v)) for k, v in value]
            if isinstance(key, int):
                self._list[key] = value[0]
            else:
                self._list[key] = value
        else:
            self.set(key, value)

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError(f"update expected at most 1 arguments, got {len(args)}")
        if args:
            mapping = args[0]
            if isinstance(mapping, (Headers, MultiDict)):
                for key in mapping.keys():
                    self.setlist(key, mapping.getlist(key))
            elif isinstance(mapping, dict):
                for key, value in mapping.items():
                    if isinstance(value, (list, tuple)):
                        self.setlist(key, value)
                    else:
                        self.set(key, value)
            else:
                for key, value in mapping:
                    self.set(key, value)
        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)):
                self.setlist(key, value)
            else:
                self.set(key, value)

    def to_wsgi_list(self):
        return list(self)

    def copy(self):
        return self.__class__(self._list)

    def __copy__(self):
        return self.copy()

    def __str__(self):
        strs = []
        for key, value in self.to_wsgi_list():
            strs.append(f"{key}: {value}")
        strs.append("\r\n")
        return "\r\n".join(strs)

    def __repr__(self):
        return f"{type(self).__name__}({list(self)!r})"


def _options_header_vkw(value: str, kw: dict[str, t.Any]):
    return http.dump_options_header(
        value, {k.replace("_", "-"): v for k, v in kw.items()}
    )


_newline_re = re.compile("[\\r\\n]")


def _str_header_value(value: t.Any) -> str:
    if not isinstance(value, str):
        value = str(value)
    if _newline_re.search(value) is not None:
        raise ValueError("Header values must not contain newline characters.")
    return value


class EnvironHeaders(ImmutableHeadersMixin, Headers):

    def __init__(self, environ):
        self.environ = environ

    def __eq__(self, other):
        return self.environ is other.environ

    __hash__ = None

    def __getitem__(self, key, _get_mode=False):
        if not isinstance(key, str):
            raise KeyError(key)
        key = key.upper().replace("-", "_")
        if key in {"CONTENT_TYPE", "CONTENT_LENGTH"}:
            return self.environ[key]
        return self.environ[f"HTTP_{key}"]

    def __len__(self):
        return len(list(iter(self)))

    def __iter__(self):
        for key, value in self.environ.items():
            if key.startswith("HTTP_") and key not in {
                "HTTP_CONTENT_TYPE",
                "HTTP_CONTENT_LENGTH",
            }:
                yield key[5:].replace("_", "-").title(), value
            elif key in {"CONTENT_TYPE", "CONTENT_LENGTH"} and value:
                yield key.replace("_", "-").title(), value

    def copy(self):
        raise TypeError(f"cannot create {type(self).__name__!r} copies")


from .. import http
