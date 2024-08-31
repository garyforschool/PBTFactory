from __future__ import annotations
from collections.abc import MutableSet
from copy import deepcopy
from .. import exceptions
from .._internal import _missing
from .mixins import ImmutableDictMixin
from .mixins import ImmutableListMixin
from .mixins import ImmutableMultiDictMixin
from .mixins import UpdateDictMixin


def is_immutable(self):
    raise TypeError(f"{type(self).__name__!r} objects are immutable")


def iter_multi_items(mapping):
    if isinstance(mapping, MultiDict):
        yield from mapping.items(multi=True)
    elif isinstance(mapping, dict):
        for key, value in mapping.items():
            if isinstance(value, (tuple, list)):
                for v in value:
                    yield key, v
            else:
                yield key, value
    else:
        yield from mapping


class ImmutableList(ImmutableListMixin, list):

    def __repr__(self):
        return f"{type(self).__name__}({list.__repr__(self)})"


class TypeConversionDict(dict):

    def get(self, key, default=None, type=None):
        try:
            rv = self[key]
        except KeyError:
            return default
        if type is not None:
            try:
                rv = type(rv)
            except (ValueError, TypeError):
                rv = default
        return rv


class ImmutableTypeConversionDict(ImmutableDictMixin, TypeConversionDict):

    def copy(self):
        return TypeConversionDict(self)

    def __copy__(self):
        return self


class MultiDict(TypeConversionDict):

    def __init__(self, mapping=None):
        if isinstance(mapping, MultiDict):
            dict.__init__(self, ((k, vs[:]) for k, vs in mapping.lists()))
        elif isinstance(mapping, dict):
            tmp = {}
            for key, value in mapping.items():
                if isinstance(value, (tuple, list)):
                    if len(value) == 0:
                        continue
                    value = list(value)
                else:
                    value = [value]
                tmp[key] = value
            dict.__init__(self, tmp)
        else:
            tmp = {}
            for key, value in mapping or ():
                tmp.setdefault(key, []).append(value)
            dict.__init__(self, tmp)

    def __getstate__(self):
        return dict(self.lists())

    def __setstate__(self, value):
        dict.clear(self)
        dict.update(self, value)

    def __iter__(self):
        return dict.__iter__(self)

    def __getitem__(self, key):
        if key in self:
            lst = dict.__getitem__(self, key)
            if len(lst) > 0:
                return lst[0]
        raise exceptions.BadRequestKeyError(key)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, [value])

    def add(self, key, value):
        dict.setdefault(self, key, []).append(value)

    def getlist(self, key, type=None):
        try:
            rv = dict.__getitem__(self, key)
        except KeyError:
            return []
        if type is None:
            return list(rv)
        result = []
        for item in rv:
            try:
                result.append(type(item))
            except ValueError:
                pass
        return result

    def setlist(self, key, new_list):
        dict.__setitem__(self, key, list(new_list))

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        else:
            default = self[key]
        return default

    def setlistdefault(self, key, default_list=None):
        if key not in self:
            default_list = list(default_list or ())
            dict.__setitem__(self, key, default_list)
        else:
            default_list = dict.__getitem__(self, key)
        return default_list

    def items(self, multi=False):
        for key, values in dict.items(self):
            if multi:
                for value in values:
                    yield key, value
            else:
                yield key, values[0]

    def lists(self):
        for key, values in dict.items(self):
            yield key, list(values)

    def values(self):
        for values in dict.values(self):
            yield values[0]

    def listvalues(self):
        return dict.values(self)

    def copy(self):
        return self.__class__(self)

    def deepcopy(self, memo=None):
        return self.__class__(deepcopy(self.to_dict(flat=False), memo))

    def to_dict(self, flat=True):
        if flat:
            return dict(self.items())
        return dict(self.lists())

    def update(self, mapping):
        for key, value in iter_multi_items(mapping):
            MultiDict.add(self, key, value)

    def pop(self, key, default=_missing):
        try:
            lst = dict.pop(self, key)
            if len(lst) == 0:
                raise exceptions.BadRequestKeyError(key)
            return lst[0]
        except KeyError:
            if default is not _missing:
                return default
            raise exceptions.BadRequestKeyError(key) from None

    def popitem(self):
        try:
            item = dict.popitem(self)
            if len(item[1]) == 0:
                raise exceptions.BadRequestKeyError(item[0])
            return item[0], item[1][0]
        except KeyError as e:
            raise exceptions.BadRequestKeyError(e.args[0]) from None

    def poplist(self, key):
        return dict.pop(self, key, [])

    def popitemlist(self):
        try:
            return dict.popitem(self)
        except KeyError as e:
            raise exceptions.BadRequestKeyError(e.args[0]) from None

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return self.deepcopy(memo=memo)

    def __repr__(self):
        return f"{type(self).__name__}({list(self.items(multi=True))!r})"


class _omd_bucket:
    __slots__ = "prev", "key", "value", "next"

    def __init__(self, omd, key, value):
        self.prev = omd._last_bucket
        self.key = key
        self.value = value
        self.next = None
        if omd._first_bucket is None:
            omd._first_bucket = self
        if omd._last_bucket is not None:
            omd._last_bucket.next = self
        omd._last_bucket = self

    def unlink(self, omd):
        if self.prev:
            self.prev.next = self.next
        if self.next:
            self.next.prev = self.prev
        if omd._first_bucket is self:
            omd._first_bucket = self.next
        if omd._last_bucket is self:
            omd._last_bucket = self.prev


class OrderedMultiDict(MultiDict):

    def __init__(self, mapping=None):
        dict.__init__(self)
        self._first_bucket = self._last_bucket = None
        if mapping is not None:
            OrderedMultiDict.update(self, mapping)

    def __eq__(self, other):
        if not isinstance(other, MultiDict):
            return NotImplemented
        if isinstance(other, OrderedMultiDict):
            iter1 = iter(self.items(multi=True))
            iter2 = iter(other.items(multi=True))
            try:
                for k1, v1 in iter1:
                    k2, v2 = next(iter2)
                    if k1 != k2 or v1 != v2:
                        return False
            except StopIteration:
                return False
            try:
                next(iter2)
            except StopIteration:
                return True
            return False
        if len(self) != len(other):
            return False
        for key, values in self.lists():
            if other.getlist(key) != values:
                return False
        return True

    __hash__ = None

    def __reduce_ex__(self, protocol):
        return type(self), (list(self.items(multi=True)),)

    def __getstate__(self):
        return list(self.items(multi=True))

    def __setstate__(self, values):
        dict.clear(self)
        for key, value in values:
            self.add(key, value)

    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self, key)[0].value
        raise exceptions.BadRequestKeyError(key)

    def __setitem__(self, key, value):
        self.poplist(key)
        self.add(key, value)

    def __delitem__(self, key):
        self.pop(key)

    def keys(self):
        return (key for key, value in self.items())

    def __iter__(self):
        return iter(self.keys())

    def values(self):
        return (value for key, value in self.items())

    def items(self, multi=False):
        ptr = self._first_bucket
        if multi:
            while ptr is not None:
                yield ptr.key, ptr.value
                ptr = ptr.next
        else:
            returned_keys = set()
            while ptr is not None:
                if ptr.key not in returned_keys:
                    returned_keys.add(ptr.key)
                    yield ptr.key, ptr.value
                ptr = ptr.next

    def lists(self):
        returned_keys = set()
        ptr = self._first_bucket
        while ptr is not None:
            if ptr.key not in returned_keys:
                yield ptr.key, self.getlist(ptr.key)
                returned_keys.add(ptr.key)
            ptr = ptr.next

    def listvalues(self):
        for _key, values in self.lists():
            yield values

    def add(self, key, value):
        dict.setdefault(self, key, []).append(_omd_bucket(self, key, value))

    def getlist(self, key, type=None):
        try:
            rv = dict.__getitem__(self, key)
        except KeyError:
            return []
        if type is None:
            return [x.value for x in rv]
        result = []
        for item in rv:
            try:
                result.append(type(item.value))
            except ValueError:
                pass
        return result

    def setlist(self, key, new_list):
        self.poplist(key)
        for value in new_list:
            self.add(key, value)

    def setlistdefault(self, key, default_list=None):
        raise TypeError("setlistdefault is unsupported for ordered multi dicts")

    def update(self, mapping):
        for key, value in iter_multi_items(mapping):
            OrderedMultiDict.add(self, key, value)

    def poplist(self, key):
        buckets = dict.pop(self, key, ())
        for bucket in buckets:
            bucket.unlink(self)
        return [x.value for x in buckets]

    def pop(self, key, default=_missing):
        try:
            buckets = dict.pop(self, key)
        except KeyError:
            if default is not _missing:
                return default
            raise exceptions.BadRequestKeyError(key) from None
        for bucket in buckets:
            bucket.unlink(self)
        return buckets[0].value

    def popitem(self):
        try:
            key, buckets = dict.popitem(self)
        except KeyError as e:
            raise exceptions.BadRequestKeyError(e.args[0]) from None
        for bucket in buckets:
            bucket.unlink(self)
        return key, buckets[0].value

    def popitemlist(self):
        try:
            key, buckets = dict.popitem(self)
        except KeyError as e:
            raise exceptions.BadRequestKeyError(e.args[0]) from None
        for bucket in buckets:
            bucket.unlink(self)
        return key, [x.value for x in buckets]


class CombinedMultiDict(ImmutableMultiDictMixin, MultiDict):

    def __reduce_ex__(self, protocol):
        return type(self), (self.dicts,)

    def __init__(self, dicts=None):
        self.dicts = list(dicts) or []

    @classmethod
    def fromkeys(cls, keys, value=None):
        raise TypeError(f"cannot create {cls.__name__!r} instances by fromkeys")

    def __getitem__(self, key):
        for d in self.dicts:
            if key in d:
                return d[key]
        raise exceptions.BadRequestKeyError(key)

    def get(self, key, default=None, type=None):
        for d in self.dicts:
            if key in d:
                if type is not None:
                    try:
                        return type(d[key])
                    except ValueError:
                        continue
                return d[key]
        return default

    def getlist(self, key, type=None):
        rv = []
        for d in self.dicts:
            rv.extend(d.getlist(key, type))
        return rv

    def _keys_impl(self):
        rv = set()
        rv.update(*self.dicts)
        return rv

    def keys(self):
        return self._keys_impl()

    def __iter__(self):
        return iter(self.keys())

    def items(self, multi=False):
        found = set()
        for d in self.dicts:
            for key, value in d.items(multi):
                if multi:
                    yield key, value
                elif key not in found:
                    found.add(key)
                    yield key, value

    def values(self):
        for _key, value in self.items():
            yield value

    def lists(self):
        rv = {}
        for d in self.dicts:
            for key, values in d.lists():
                rv.setdefault(key, []).extend(values)
        return list(rv.items())

    def listvalues(self):
        return (x[1] for x in self.lists())

    def copy(self):
        return MultiDict(self)

    def to_dict(self, flat=True):
        if flat:
            return dict(self.items())
        return dict(self.lists())

    def __len__(self):
        return len(self._keys_impl())

    def __contains__(self, key):
        for d in self.dicts:
            if key in d:
                return True
        return False

    def __repr__(self):
        return f"{type(self).__name__}({self.dicts!r})"


class ImmutableDict(ImmutableDictMixin, dict):

    def __repr__(self):
        return f"{type(self).__name__}({dict.__repr__(self)})"

    def copy(self):
        return dict(self)

    def __copy__(self):
        return self


class ImmutableMultiDict(ImmutableMultiDictMixin, MultiDict):

    def copy(self):
        return MultiDict(self)

    def __copy__(self):
        return self


class ImmutableOrderedMultiDict(ImmutableMultiDictMixin, OrderedMultiDict):

    def _iter_hashitems(self):
        return enumerate(self.items(multi=True))

    def copy(self):
        return OrderedMultiDict(self)

    def __copy__(self):
        return self


class CallbackDict(UpdateDictMixin, dict):

    def __init__(self, initial=None, on_update=None):
        dict.__init__(self, initial or ())
        self.on_update = on_update

    def __repr__(self):
        return f"<{type(self).__name__} {dict.__repr__(self)}>"


class HeaderSet(MutableSet):

    def __init__(self, headers=None, on_update=None):
        self._headers = list(headers or ())
        self._set = {x.lower() for x in self._headers}
        self.on_update = on_update

    def add(self, header):
        self.update((header,))

    def remove(self, header):
        key = header.lower()
        if key not in self._set:
            raise KeyError(header)
        self._set.remove(key)
        for idx, key in enumerate(self._headers):
            if key.lower() == header:
                del self._headers[idx]
                break
        if self.on_update is not None:
            self.on_update(self)

    def update(self, iterable):
        inserted_any = False
        for header in iterable:
            key = header.lower()
            if key not in self._set:
                self._headers.append(header)
                self._set.add(key)
                inserted_any = True
        if inserted_any and self.on_update is not None:
            self.on_update(self)

    def discard(self, header):
        try:
            self.remove(header)
        except KeyError:
            pass

    def find(self, header):
        header = header.lower()
        for idx, item in enumerate(self._headers):
            if item.lower() == header:
                return idx
        return -1

    def index(self, header):
        rv = self.find(header)
        if rv < 0:
            raise IndexError(header)
        return rv

    def clear(self):
        self._set.clear()
        del self._headers[:]
        if self.on_update is not None:
            self.on_update(self)

    def as_set(self, preserve_casing=False):
        if preserve_casing:
            return set(self._headers)
        return set(self._set)

    def to_header(self):
        return ", ".join(map(http.quote_header_value, self._headers))

    def __getitem__(self, idx):
        return self._headers[idx]

    def __delitem__(self, idx):
        rv = self._headers.pop(idx)
        self._set.remove(rv.lower())
        if self.on_update is not None:
            self.on_update(self)

    def __setitem__(self, idx, value):
        old = self._headers[idx]
        self._set.remove(old.lower())
        self._headers[idx] = value
        self._set.add(value.lower())
        if self.on_update is not None:
            self.on_update(self)

    def __contains__(self, header):
        return header.lower() in self._set

    def __len__(self):
        return len(self._set)

    def __iter__(self):
        return iter(self._headers)

    def __bool__(self):
        return bool(self._set)

    def __str__(self):
        return self.to_header()

    def __repr__(self):
        return f"{type(self).__name__}({self._headers!r})"


from .. import http
