from __future__ import annotations
import logging
import re
import sys
import typing as t
from datetime import datetime
from datetime import timezone

if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIEnvironment
    from .wrappers.request import Request
_logger: logging.Logger | None = None


class _Missing:

    def __repr__(self) -> str:
        return "no value"

    def __reduce__(self) -> str:
        return "_missing"


_missing = _Missing()


def _wsgi_decoding_dance(s: str) -> str:
    return s.encode("latin1").decode(errors="replace")


def _wsgi_encoding_dance(s: str) -> str:
    return s.encode().decode("latin1")


def _get_environ(obj: WSGIEnvironment | Request) -> WSGIEnvironment:
    env = getattr(obj, "environ", obj)
    assert isinstance(
        env, dict
    ), f"{type(obj).__name__!r} is not a WSGI environment (has to be a dict)"
    return env


def _has_level_handler(logger: logging.Logger) -> bool:
    level = logger.getEffectiveLevel()
    current = logger
    while current:
        if any(handler.level <= level for handler in current.handlers):
            return True
        if not current.propagate:
            break
        current = current.parent
    return False


class _ColorStreamHandler(logging.StreamHandler):

    def __init__(self) -> None:
        try:
            import colorama
        except ImportError:
            stream = None
        else:
            stream = colorama.AnsiToWin32(sys.stderr)
        super().__init__(stream)


def _log(type: str, message: str, *args: t.Any, **kwargs: t.Any) -> None:
    global _logger
    if _logger is None:
        _logger = logging.getLogger("werkzeug")
        if _logger.level == logging.NOTSET:
            _logger.setLevel(logging.INFO)
        if not _has_level_handler(_logger):
            _logger.addHandler(_ColorStreamHandler())
    getattr(_logger, type)(message.rstrip(), *args, **kwargs)


@t.overload
def _dt_as_utc(dt: None) -> None: ...


@t.overload
def _dt_as_utc(dt: datetime) -> datetime: ...


def _dt_as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        return dt.astimezone(timezone.utc)
    return dt


_TAccessorValue = t.TypeVar("_TAccessorValue")


class _DictAccessorProperty(t.Generic[_TAccessorValue]):
    read_only = False

    def __init__(
        self,
        name: str,
        default: _TAccessorValue | None = None,
        load_func: t.Callable[[str], _TAccessorValue] | None = None,
        dump_func: t.Callable[[_TAccessorValue], str] | None = None,
        read_only: bool | None = None,
        doc: str | None = None,
    ) -> None:
        self.name = name
        self.default = default
        self.load_func = load_func
        self.dump_func = dump_func
        if read_only is not None:
            self.read_only = read_only
        self.__doc__ = doc

    def lookup(self, instance: t.Any) -> t.MutableMapping[str, t.Any]:
        raise NotImplementedError

    @t.overload
    def __get__(
        self, instance: None, owner: type
    ) -> _DictAccessorProperty[_TAccessorValue]: ...

    @t.overload
    def __get__(self, instance: t.Any, owner: type) -> _TAccessorValue: ...

    def __get__(
        self, instance: t.Any | None, owner: type
    ) -> _TAccessorValue | _DictAccessorProperty[_TAccessorValue]:
        if instance is None:
            return self
        storage = self.lookup(instance)
        if self.name not in storage:
            return self.default
        value = storage[self.name]
        if self.load_func is not None:
            try:
                return self.load_func(value)
            except (ValueError, TypeError):
                return self.default
        return value

    def __set__(self, instance: t.Any, value: _TAccessorValue) -> None:
        if self.read_only:
            raise AttributeError("read only property")
        if self.dump_func is not None:
            self.lookup(instance)[self.name] = self.dump_func(value)
        else:
            self.lookup(instance)[self.name] = value

    def __delete__(self, instance: t.Any) -> None:
        if self.read_only:
            raise AttributeError("read only property")
        self.lookup(instance).pop(self.name, None)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name}>"


_plain_int_re = re.compile("-?\\d+", re.ASCII)


def _plain_int(value: str) -> int:
    value = value.strip()
    if _plain_int_re.fullmatch(value) is None:
        raise ValueError
    return int(value)
