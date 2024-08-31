from __future__ import annotations


class UserAgent:
    platform: str | None = None
    """The OS name, if it could be parsed from the string."""
    browser: str | None = None
    """The browser name, if it could be parsed from the string."""
    version: str | None = None
    """The browser version, if it could be parsed from the string."""
    language: str | None = None
    """The browser language, if it could be parsed from the string."""

    def __init__(self, string: str) -> None:
        self.string: str = string
        """The original header value."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.browser}/{self.version}>"

    def __str__(self) -> str:
        return self.string

    def __bool__(self) -> bool:
        return bool(self.browser)

    def to_header(self) -> str:
        return self.string
