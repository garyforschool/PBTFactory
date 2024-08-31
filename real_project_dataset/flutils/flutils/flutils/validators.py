import keyword
from collections import UserString
from typing import Union

__all__ = ["validate_identifier"]
_BUILTIN_NAMES = tuple(
    filter(lambda x: x.startswith("__") and x.endswith("__"), dir("__builtins__"))
)


def validate_identifier(
    identifier: Union[str, UserString], allow_underscore: bool = True
) -> None:
    if isinstance(identifier, UserString):
        identifier = str(identifier)
    if not isinstance(identifier, str):
        raise TypeError(
            "The given 'identifier' must be a 'str'.  Got: %r"
            % type(identifier).__name__
        )
    identifier = identifier.strip()
    if not identifier:
        raise SyntaxError("The given 'identifier' cannot be empty")
    if allow_underscore is False and identifier[0:1] == "_":
        raise SyntaxError(
            f"The given 'identifier', {identifier!r}, cannot start with an underscore '_'"
        )
    if identifier[0:1].isdigit():
        raise SyntaxError(
            f"The given 'identifier', {identifier!r}, cannot start with a number"
        )
    if not identifier.isidentifier():
        raise SyntaxError(f"The given 'identifier', {identifier!r}, is invalid.")
    if keyword.iskeyword(identifier):
        raise SyntaxError(
            f"The given 'identifier', {identifier!r}, cannot be a keyword"
        )
    if identifier in _BUILTIN_NAMES:
        raise SyntaxError(
            f"The given 'identifier', {identifier!r}, cannot be a builtin name"
        )
