from __future__ import annotations
import base64
import binascii
import typing as t
from ..http import dump_header
from ..http import parse_dict_header
from ..http import quote_header_value
from .structures import CallbackDict

if t.TYPE_CHECKING:
    import typing_extensions as te


class Authorization:

    def __init__(
        self,
        auth_type: str,
        data: dict[str, str | None] | None = None,
        token: str | None = None,
    ) -> None:
        self.type = auth_type
        """The authorization scheme, like ``basic``, ``digest``, or ``bearer``."""
        if data is None:
            data = {}
        self.parameters = data
        """A dict of parameters parsed from the header. Either this or :attr:`token`
        will have a value for a given scheme.
        """
        self.token = token
        """A token parsed from the header. Either this or :attr:`parameters` will have a
        value for a given scheme.

        .. versionadded:: 2.3
        """

    def __getattr__(self, name: str) -> str | None:
        return self.parameters.get(name)

    def __getitem__(self, name: str) -> str | None:
        return self.parameters.get(name)

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.parameters.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.parameters

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Authorization):
            return NotImplemented
        return (
            other.type == self.type
            and other.token == self.token
            and other.parameters == self.parameters
        )

    @classmethod
    def from_header(cls, value: str | None) -> te.Self | None:
        if not value:
            return None
        scheme, _, rest = value.partition(" ")
        scheme = scheme.lower()
        rest = rest.strip()
        if scheme == "basic":
            try:
                username, _, password = base64.b64decode(rest).decode().partition(":")
            except (binascii.Error, UnicodeError):
                return None
            return cls(scheme, {"username": username, "password": password})
        if "=" in rest.rstrip("="):
            return cls(scheme, parse_dict_header(rest), None)
        return cls(scheme, None, rest)

    def to_header(self) -> str:
        if self.type == "basic":
            value = base64.b64encode(
                f"{self.username}:{self.password}".encode()
            ).decode("ascii")
            return f"Basic {value}"
        if self.token is not None:
            return f"{self.type.title()} {self.token}"
        return f"{self.type.title()} {dump_header(self.parameters)}"

    def __str__(self) -> str:
        return self.to_header()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.to_header()}>"


class WWWAuthenticate:

    def __init__(
        self,
        auth_type: str,
        values: dict[str, str | None] | None = None,
        token: str | None = None,
    ):
        self._type = auth_type.lower()
        self._parameters: dict[str, str | None] = CallbackDict(
            values, lambda _: self._trigger_on_update()
        )
        self._token = token
        self._on_update: t.Callable[[WWWAuthenticate], None] | None = None

    def _trigger_on_update(self) -> None:
        if self._on_update is not None:
            self._on_update(self)

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str) -> None:
        self._type = value
        self._trigger_on_update()

    @property
    def parameters(self) -> dict[str, str | None]:
        return self._parameters

    @parameters.setter
    def parameters(self, value: dict[str, str]) -> None:
        self._parameters = CallbackDict(value, lambda _: self._trigger_on_update())
        self._trigger_on_update()

    @property
    def token(self) -> str | None:
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        self._token = value
        self._trigger_on_update()

    def __getitem__(self, key: str) -> str | None:
        return self.parameters.get(key)

    def __setitem__(self, key: str, value: str | None) -> None:
        if value is None:
            if key in self.parameters:
                del self.parameters[key]
        else:
            self.parameters[key] = value
        self._trigger_on_update()

    def __delitem__(self, key: str) -> None:
        if key in self.parameters:
            del self.parameters[key]
            self._trigger_on_update()

    def __getattr__(self, name: str) -> str | None:
        return self[name]

    def __setattr__(self, name: str, value: str | None) -> None:
        if name in {"_type", "_parameters", "_token", "_on_update"}:
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name: str) -> None:
        del self[name]

    def __contains__(self, key: str) -> bool:
        return key in self.parameters

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WWWAuthenticate):
            return NotImplemented
        return (
            other.type == self.type
            and other.token == self.token
            and other.parameters == self.parameters
        )

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.parameters.get(key, default)

    @classmethod
    def from_header(cls, value: str | None) -> te.Self | None:
        if not value:
            return None
        scheme, _, rest = value.partition(" ")
        scheme = scheme.lower()
        rest = rest.strip()
        if "=" in rest.rstrip("="):
            return cls(scheme, parse_dict_header(rest), None)
        return cls(scheme, None, rest)

    def to_header(self) -> str:
        if self.token is not None:
            return f"{self.type.title()} {self.token}"
        if self.type == "digest":
            items = []
            for key, value in self.parameters.items():
                if key in {"realm", "domain", "nonce", "opaque", "qop"}:
                    value = quote_header_value(value, allow_token=False)
                else:
                    value = quote_header_value(value)
                items.append(f"{key}={value}")
            return f"Digest {', '.join(items)}"
        return f"{self.type.title()} {dump_header(self.parameters)}"

    def __str__(self) -> str:
        return self.to_header()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.to_header()}>"
