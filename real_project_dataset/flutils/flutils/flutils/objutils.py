from collections import UserList, deque
from collections.abc import Iterator, KeysView, ValuesView
from typing import Any as _Any

__all__ = [
    "has_any_attrs",
    "has_any_callables",
    "has_attrs",
    "has_callables",
    "is_list_like",
    "is_subclass_of_any",
]
_LIST_LIKE = (
    list,
    set,
    frozenset,
    tuple,
    deque,
    Iterator,
    ValuesView,
    KeysView,
    UserList,
)


def has_any_attrs(obj: _Any, *attrs: str) -> bool:
    for attr in attrs:
        if hasattr(obj, attr) is True:
            return True
    return False


def has_any_callables(obj: _Any, *attrs: str) -> bool:
    if has_any_attrs(obj, *attrs) is True:
        for attr in attrs:
            if callable(getattr(obj, attr)) is True:
                return True
    return False


def has_attrs(obj: _Any, *attrs: str) -> bool:
    for attr in attrs:
        if hasattr(obj, attr) is False:
            return False
    return True


def has_callables(obj: _Any, *attrs: str) -> bool:
    if has_attrs(obj, *attrs) is True:
        for attr in attrs:
            if callable(getattr(obj, attr)) is False:
                return False
        return True
    return False


def is_list_like(obj: _Any) -> bool:
    if is_subclass_of_any(obj, *_LIST_LIKE):
        return True
    return False


def is_subclass_of_any(obj: _Any, *classes: _Any) -> bool:
    for cls in classes:
        if issubclass(obj.__class__, cls):
            return True
    return False
