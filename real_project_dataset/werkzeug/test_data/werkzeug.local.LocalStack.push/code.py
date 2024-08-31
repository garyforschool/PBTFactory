from __future__ import annotations
import copy
import math
import operator
import typing as t
from contextvars import ContextVar
from functools import partial
from functools import update_wrapper
from operator import attrgetter
from .wsgi import ClosingIterator

if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment
T = t.TypeVar("T")
F = t.TypeVar("F", bound=t.Callable[..., t.Any])


def release_local(local: Local | LocalStack[t.Any]) -> None:
    local.__release_local__()


class Local:
    __slots__ = ("__storage",)

    def __init__(self, context_var: ContextVar[dict[str, t.Any]] | None = None) -> None:
        if context_var is None:
            context_var = ContextVar(f"werkzeug.Local<{id(self)}>.storage")
        object.__setattr__(self, "_Local__storage", context_var)

    def __iter__(self) -> t.Iterator[tuple[str, t.Any]]:
        return iter(self.__storage.get({}).items())

    def __call__(
        self, name: str, *, unbound_message: str | None = None
    ) -> LocalProxy[t.Any]:
        return LocalProxy(self, name, unbound_message=unbound_message)

    def __release_local__(self) -> None:
        self.__storage.set({})

    def __getattr__(self, name: str) -> t.Any:
        values = self.__storage.get({})
        if name in values:
            return values[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: t.Any) -> None:
        values = self.__storage.get({}).copy()
        values[name] = value
        self.__storage.set(values)

    def __delattr__(self, name: str) -> None:
        values = self.__storage.get({})
        if name in values:
            values = values.copy()
            del values[name]
            self.__storage.set(values)
        else:
            raise AttributeError(name)


class LocalStack(t.Generic[T]):
    __slots__ = ("_storage",)

    def __init__(self, context_var: ContextVar[list[T]] | None = None) -> None:
        if context_var is None:
            context_var = ContextVar(f"werkzeug.LocalStack<{id(self)}>.storage")
        self._storage = context_var

    def __release_local__(self) -> None:
        self._storage.set([])

    def push(self, obj: T) -> list[T]:
        stack = self._storage.get([]).copy()
        stack.append(obj)
        self._storage.set(stack)
        return stack

    def pop(self) -> T | None:
        stack = self._storage.get([])
        if len(stack) == 0:
            return None
        rv = stack[-1]
        self._storage.set(stack[:-1])
        return rv

    @property
    def top(self) -> T | None:
        stack = self._storage.get([])
        if len(stack) == 0:
            return None
        return stack[-1]

    def __call__(
        self, name: str | None = None, *, unbound_message: str | None = None
    ) -> LocalProxy[t.Any]:
        return LocalProxy(self, name, unbound_message=unbound_message)


class LocalManager:
    __slots__ = ("locals",)

    def __init__(
        self,
        locals: None | (
            Local | LocalStack[t.Any] | t.Iterable[Local | LocalStack[t.Any]]
        ) = None,
    ) -> None:
        if locals is None:
            self.locals = []
        elif isinstance(locals, Local):
            self.locals = [locals]
        else:
            self.locals = list(locals)

    def cleanup(self) -> None:
        for local in self.locals:
            release_local(local)

    def make_middleware(self, app: WSGIApplication) -> WSGIApplication:

        def application(
            environ: WSGIEnvironment, start_response: StartResponse
        ) -> t.Iterable[bytes]:
            return ClosingIterator(app(environ, start_response), self.cleanup)

        return application

    def middleware(self, func: WSGIApplication) -> WSGIApplication:
        return update_wrapper(self.make_middleware(func), func)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} storages: {len(self.locals)}>"


class _ProxyLookup:
    __slots__ = "bind_f", "fallback", "is_attr", "class_value", "name"

    def __init__(
        self,
        f: t.Callable[..., t.Any] | None = None,
        fallback: t.Callable[[LocalProxy[t.Any]], t.Any] | None = None,
        class_value: t.Any | None = None,
        is_attr: bool = False,
    ) -> None:
        bind_f: t.Callable[[LocalProxy[t.Any], t.Any], t.Callable[..., t.Any]] | None
        if hasattr(f, "__get__"):

            def bind_f(
                instance: LocalProxy[t.Any], obj: t.Any
            ) -> t.Callable[..., t.Any]:
                return f.__get__(obj, type(obj))

        elif f is not None:

            def bind_f(
                instance: LocalProxy[t.Any], obj: t.Any
            ) -> t.Callable[..., t.Any]:
                return partial(f, obj)

        else:
            bind_f = None
        self.bind_f = bind_f
        self.fallback = fallback
        self.class_value = class_value
        self.is_attr = is_attr

    def __set_name__(self, owner: LocalProxy[t.Any], name: str) -> None:
        self.name = name

    def __get__(self, instance: LocalProxy[t.Any], owner: type | None = None) -> t.Any:
        if instance is None:
            if self.class_value is not None:
                return self.class_value
            return self
        try:
            obj = instance._get_current_object()
        except RuntimeError:
            if self.fallback is None:
                raise
            fallback = self.fallback.__get__(instance, owner)
            if self.is_attr:
                return fallback()
            return fallback
        if self.bind_f is not None:
            return self.bind_f(instance, obj)
        return getattr(obj, self.name)

    def __repr__(self) -> str:
        return f"proxy {self.name}"

    def __call__(
        self, instance: LocalProxy[t.Any], *args: t.Any, **kwargs: t.Any
    ) -> t.Any:
        return self.__get__(instance, type(instance))(*args, **kwargs)


class _ProxyIOp(_ProxyLookup):
    __slots__ = ()

    def __init__(
        self,
        f: t.Callable[..., t.Any] | None = None,
        fallback: t.Callable[[LocalProxy[t.Any]], t.Any] | None = None,
    ) -> None:
        super().__init__(f, fallback)

        def bind_f(instance: LocalProxy[t.Any], obj: t.Any) -> t.Callable[..., t.Any]:

            def i_op(self: t.Any, other: t.Any) -> LocalProxy[t.Any]:
                f(self, other)
                return instance

            return i_op.__get__(obj, type(obj))

        self.bind_f = bind_f


def _l_to_r_op(op: F) -> F:

    def r_op(obj: t.Any, other: t.Any) -> t.Any:
        return op(other, obj)

    return t.cast(F, r_op)


def _identity(o: T) -> T:
    return o


class LocalProxy(t.Generic[T]):
    __slots__ = "__wrapped", "_get_current_object"
    _get_current_object: t.Callable[[], T]
    """Return the current object this proxy is bound to. If the proxy is
    unbound, this raises a ``RuntimeError``.

    This should be used if you need to pass the object to something that
    doesn't understand the proxy. It can also be useful for performance
    if you are accessing the object multiple times in a function, rather
    than going through the proxy multiple times.
    """

    def __init__(
        self,
        local: ContextVar[T] | Local | LocalStack[T] | t.Callable[[], T],
        name: str | None = None,
        *,
        unbound_message: str | None = None,
    ) -> None:
        if name is None:
            get_name = _identity
        else:
            get_name = attrgetter(name)
        if unbound_message is None:
            unbound_message = "object is not bound"
        if isinstance(local, Local):
            if name is None:
                raise TypeError("'name' is required when proxying a 'Local' object.")

            def _get_current_object() -> T:
                try:
                    return get_name(local)
                except AttributeError:
                    raise RuntimeError(unbound_message) from None

        elif isinstance(local, LocalStack):

            def _get_current_object() -> T:
                obj = local.top
                if obj is None:
                    raise RuntimeError(unbound_message)
                return get_name(obj)

        elif isinstance(local, ContextVar):

            def _get_current_object() -> T:
                try:
                    obj = local.get()
                except LookupError:
                    raise RuntimeError(unbound_message) from None
                return get_name(obj)

        elif callable(local):

            def _get_current_object() -> T:
                return get_name(local())

        else:
            raise TypeError(f"Don't know how to proxy '{type(local)}'.")
        object.__setattr__(self, "_LocalProxy__wrapped", local)
        object.__setattr__(self, "_get_current_object", _get_current_object)

    __doc__ = _ProxyLookup(
        class_value=__doc__, fallback=lambda self: type(self).__doc__, is_attr=True
    )
    __wrapped__ = _ProxyLookup(
        fallback=lambda self: self._LocalProxy__wrapped, is_attr=True
    )
    __repr__ = _ProxyLookup(
        repr, fallback=lambda self: f"<{type(self).__name__} unbound>"
    )
    __str__ = _ProxyLookup(str)
    __bytes__ = _ProxyLookup(bytes)
    __format__ = _ProxyLookup()
    __lt__ = _ProxyLookup(operator.lt)
    __le__ = _ProxyLookup(operator.le)
    __eq__ = _ProxyLookup(operator.eq)
    __ne__ = _ProxyLookup(operator.ne)
    __gt__ = _ProxyLookup(operator.gt)
    __ge__ = _ProxyLookup(operator.ge)
    __hash__ = _ProxyLookup(hash)
    __bool__ = _ProxyLookup(bool, fallback=lambda self: False)
    __getattr__ = _ProxyLookup(getattr)
    __setattr__ = _ProxyLookup(setattr)
    __delattr__ = _ProxyLookup(delattr)
    __dir__ = _ProxyLookup(dir, fallback=lambda self: [])
    __class__ = _ProxyLookup(fallback=lambda self: type(self), is_attr=True)
    __instancecheck__ = _ProxyLookup(lambda self, other: isinstance(other, self))
    __subclasscheck__ = _ProxyLookup(lambda self, other: issubclass(other, self))
    __call__ = _ProxyLookup(lambda self, *args, **kwargs: self(*args, **kwargs))
    __len__ = _ProxyLookup(len)
    __length_hint__ = _ProxyLookup(operator.length_hint)
    __getitem__ = _ProxyLookup(operator.getitem)
    __setitem__ = _ProxyLookup(operator.setitem)
    __delitem__ = _ProxyLookup(operator.delitem)
    __iter__ = _ProxyLookup(iter)
    __next__ = _ProxyLookup(next)
    __reversed__ = _ProxyLookup(reversed)
    __contains__ = _ProxyLookup(operator.contains)
    __add__ = _ProxyLookup(operator.add)
    __sub__ = _ProxyLookup(operator.sub)
    __mul__ = _ProxyLookup(operator.mul)
    __matmul__ = _ProxyLookup(operator.matmul)
    __truediv__ = _ProxyLookup(operator.truediv)
    __floordiv__ = _ProxyLookup(operator.floordiv)
    __mod__ = _ProxyLookup(operator.mod)
    __divmod__ = _ProxyLookup(divmod)
    __pow__ = _ProxyLookup(pow)
    __lshift__ = _ProxyLookup(operator.lshift)
    __rshift__ = _ProxyLookup(operator.rshift)
    __and__ = _ProxyLookup(operator.and_)
    __xor__ = _ProxyLookup(operator.xor)
    __or__ = _ProxyLookup(operator.or_)
    __radd__ = _ProxyLookup(_l_to_r_op(operator.add))
    __rsub__ = _ProxyLookup(_l_to_r_op(operator.sub))
    __rmul__ = _ProxyLookup(_l_to_r_op(operator.mul))
    __rmatmul__ = _ProxyLookup(_l_to_r_op(operator.matmul))
    __rtruediv__ = _ProxyLookup(_l_to_r_op(operator.truediv))
    __rfloordiv__ = _ProxyLookup(_l_to_r_op(operator.floordiv))
    __rmod__ = _ProxyLookup(_l_to_r_op(operator.mod))
    __rdivmod__ = _ProxyLookup(_l_to_r_op(divmod))
    __rpow__ = _ProxyLookup(_l_to_r_op(pow))
    __rlshift__ = _ProxyLookup(_l_to_r_op(operator.lshift))
    __rrshift__ = _ProxyLookup(_l_to_r_op(operator.rshift))
    __rand__ = _ProxyLookup(_l_to_r_op(operator.and_))
    __rxor__ = _ProxyLookup(_l_to_r_op(operator.xor))
    __ror__ = _ProxyLookup(_l_to_r_op(operator.or_))
    __iadd__ = _ProxyIOp(operator.iadd)
    __isub__ = _ProxyIOp(operator.isub)
    __imul__ = _ProxyIOp(operator.imul)
    __imatmul__ = _ProxyIOp(operator.imatmul)
    __itruediv__ = _ProxyIOp(operator.itruediv)
    __ifloordiv__ = _ProxyIOp(operator.ifloordiv)
    __imod__ = _ProxyIOp(operator.imod)
    __ipow__ = _ProxyIOp(operator.ipow)
    __ilshift__ = _ProxyIOp(operator.ilshift)
    __irshift__ = _ProxyIOp(operator.irshift)
    __iand__ = _ProxyIOp(operator.iand)
    __ixor__ = _ProxyIOp(operator.ixor)
    __ior__ = _ProxyIOp(operator.ior)
    __neg__ = _ProxyLookup(operator.neg)
    __pos__ = _ProxyLookup(operator.pos)
    __abs__ = _ProxyLookup(abs)
    __invert__ = _ProxyLookup(operator.invert)
    __complex__ = _ProxyLookup(complex)
    __int__ = _ProxyLookup(int)
    __float__ = _ProxyLookup(float)
    __index__ = _ProxyLookup(operator.index)
    __round__ = _ProxyLookup(round)
    __trunc__ = _ProxyLookup(math.trunc)
    __floor__ = _ProxyLookup(math.floor)
    __ceil__ = _ProxyLookup(math.ceil)
    __enter__ = _ProxyLookup()
    __exit__ = _ProxyLookup()
    __await__ = _ProxyLookup()
    __aiter__ = _ProxyLookup()
    __anext__ = _ProxyLookup()
    __aenter__ = _ProxyLookup()
    __aexit__ = _ProxyLookup()
    __copy__ = _ProxyLookup(copy.copy)
    __deepcopy__ = _ProxyLookup(copy.deepcopy)