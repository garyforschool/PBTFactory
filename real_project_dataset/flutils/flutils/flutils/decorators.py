import asyncio
from typing import Any

__all__ = ["cached_property"]


class cached_property:

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func

    def __get__(self, obj: Any, cls):
        if obj is None:
            return self
        if asyncio.iscoroutinefunction(self.func):
            return self._wrap_in_coroutine(obj)
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value

    def _wrap_in_coroutine(self, obj):

        @asyncio.coroutine
        def wrapper():
            future = asyncio.ensure_future(self.func(obj))
            obj.__dict__[self.func.__name__] = future
            return future

        return wrapper()
