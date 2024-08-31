from collections import OrderedDict, namedtuple
from collections.abc import Mapping, Sequence
from functools import singledispatch
from types import SimpleNamespace
from typing import Any, List, NamedTuple, Tuple, Union, cast
from flutils.validators import validate_identifier

__all__ = ["to_namedtuple"]
_AllowedTypes = Union[List, Mapping, NamedTuple, SimpleNamespace, Tuple]


def to_namedtuple(obj: _AllowedTypes) -> Union[NamedTuple, Tuple, List]:
    return _to_namedtuple(obj)


@singledispatch
def _to_namedtuple(obj: Any, _started: bool = False) -> Any:
    if _started is False:
        raise TypeError(
            "Can convert only 'list', 'tuple', 'dict' to a NamedTuple; got: (%r) %s"
            % (type(obj).__name__, obj)
        )
    return obj


@_to_namedtuple.register(Mapping)
def _(obj: Mapping, _started: bool = False) -> Union[NamedTuple, Tuple]:
    keys = []
    for key in obj.keys():
        if hasattr(key, "capitalize"):
            key = cast(str, key)
            try:
                validate_identifier(key, allow_underscore=False)
            except SyntaxError:
                continue
            if key.isidentifier():
                keys.append(key)
    if not isinstance(obj, OrderedDict):
        keys = tuple(sorted(keys))
    args = []
    for key in keys:
        val: Any = obj[key]
        val = _to_namedtuple(val, _started=True)
        args.append(val)
    if args:
        make = namedtuple("NamedTuple", keys)
        out: NamedTuple = make(*args)
        return out
    make_empty = namedtuple("NamedTuple", "")
    out = make_empty()
    return out


@_to_namedtuple.register(Sequence)
def _(
    obj: Sequence, _started: bool = False
) -> Union[List[Any], Tuple[Any, ...], NamedTuple, str]:
    if hasattr(obj, "capitalize"):
        obj = cast(str, obj)
        if _started is False:
            raise TypeError(
                "Can convert only 'list', 'tuple', 'dict' to a NamedTuple; got: (%r) %s"
                % (type(obj).__name__, obj)
            )
        return obj
    if hasattr(obj, "_fields"):
        fields: List[str] = list(obj._fields)
        if fields:
            obj = cast(NamedTuple, obj)
            args = []
            for attr in obj._fields:
                val: Any = getattr(obj, attr)
                val = _to_namedtuple(val, _started=True)
                args.append(val)
            if args:
                make = namedtuple("NamedTuple", fields)
                out: NamedTuple = make(*args)
                return out
        return obj
    out = []
    for item in obj:
        val = _to_namedtuple(item, _started=True)
        out.append(val)
    if not hasattr(obj, "append"):
        return tuple(out)
    return out


@_to_namedtuple.register(SimpleNamespace)
def _(obj: SimpleNamespace, _started: bool = False) -> NamedTuple:
    return _to_namedtuple(obj.__dict__)
