import re
from itertools import chain
from sys import hexversion
from textwrap import TextWrapper
from typing import List, Optional, Sequence, cast

if hexversion >= 50855936:
    from functools import cached_property
else:
    from .decorators import cached_property
__all__ = ["len_without_ansi", "AnsiTextWrapper"]
_ANSI_RE = re.compile("(\x1b\\[[0-9;:]+[ABCDEFGHJKSTfhilmns])")


def len_without_ansi(seq: Sequence) -> int:
    if hasattr(seq, "capitalize"):
        _text: str = cast(str, seq)
        seq = [c for c in _ANSI_RE.split(_text) if c]
    seq = [c for c in chain(*map(_ANSI_RE.split, seq)) if c]
    seq = cast(Sequence[str], seq)
    out = 0
    for text in seq:
        if hasattr(text, "capitalize"):
            if text.startswith("\x1b[") and text.endswith("m"):
                continue
            else:
                out += len(text)
    return out


class AnsiTextWrapper(TextWrapper):

    def __init__(
        self,
        width: int = 70,
        initial_indent: str = "",
        subsequent_indent: str = "",
        expand_tabs: bool = True,
        replace_whitespace: bool = True,
        fix_sentence_endings: bool = False,
        break_long_words: bool = True,
        drop_whitespace: bool = True,
        break_on_hyphens: bool = True,
        tabsize: int = 8,
        *,
        max_lines: Optional[int] = None,
        placeholder: str = " [...]"
    ) -> None:
        self.__initial_indent: str = ""
        self.__subsequent_indent: str = ""
        self.__placeholder: str = ""
        self.width: int = width
        self.initial_indent = initial_indent
        self.subsequent_indent = subsequent_indent
        self.expand_tabs: bool = expand_tabs
        self.replace_whitespace: bool = replace_whitespace
        self.fix_sentence_endings: bool = fix_sentence_endings
        self.break_long_words: bool = break_long_words
        self.drop_whitespace: bool = drop_whitespace
        self.break_on_hyphens: bool = break_on_hyphens
        self.tabsize: int = tabsize
        self.max_lines: Optional[int] = max_lines
        self.placeholder = placeholder

    @property
    def initial_indent(self) -> str:
        return self.__initial_indent

    @initial_indent.setter
    def initial_indent(self, value: str) -> None:
        self.__initial_indent = value
        if "initial_indent_len" in self.__dict__.keys():
            del self.__dict__["initial_indent_len"]

    @cached_property
    def initial_indent_len(self) -> int:
        if not self.initial_indent:
            return 0
        return len_without_ansi(self.initial_indent)

    @property
    def subsequent_indent(self) -> str:
        return self.__subsequent_indent

    @subsequent_indent.setter
    def subsequent_indent(self, value: str) -> None:
        self.__subsequent_indent = value
        if "subsequent_indent_len" in self.__dict__.keys():
            del self.__dict__["subsequent_indent_len"]

    @cached_property
    def subsequent_indent_len(self) -> int:
        if not self.subsequent_indent:
            return 0
        return len_without_ansi(self.subsequent_indent)

    @property
    def placeholder(self) -> str:
        return self.__placeholder

    @placeholder.setter
    def placeholder(self, value: str) -> None:
        self.__placeholder = value
        if "placeholder_len" in self.__dict__.keys():
            del self.__dict__["placeholder_len"]

    @cached_property
    def placeholder_len(self) -> int:
        if not self.placeholder.lstrip():
            return 0
        return len_without_ansi(self.placeholder)

    def _split(self, text: str) -> List[str]:
        chunks = super()._split(text)
        return [c for c in chain(*map(_ANSI_RE.split, chunks)) if c]

    def _wrap_chunks(self, chunks: List[str]) -> List[str]:
        lines = []
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)
        if self.max_lines is not None:
            if self.max_lines > 1:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            indent_len = len_without_ansi(indent)
            _placeholder_len = len_without_ansi(self.placeholder.lstrip())
            if indent_len + _placeholder_len > self.width:
                raise ValueError("placeholder too large for max width")
            del _placeholder_len
        chunks.reverse()
        while chunks:
            cur_line = []
            cur_len = 0
            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            indent_len = len_without_ansi(indent)
            width = self.width - indent_len
            if self.drop_whitespace and chunks[-1].strip() == "" and lines:
                del chunks[-1]
            while chunks:
                l = len_without_ansi(chunks[-1])
                if cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l
                    continue
                else:
                    break
            if chunks and len_without_ansi(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
                cur_len = sum(map(len_without_ansi, cur_line))
            if self.drop_whitespace and cur_line and cur_line[-1].strip() == "":
                cur_len -= len_without_ansi(cur_line[-1])
                del cur_line[-1]
            if cur_line:
                if (
                    self.max_lines is None
                    or len(lines) + 1 < self.max_lines
                    or (
                        not chunks
                        or self.drop_whitespace
                        and len(chunks) == 1
                        and not chunks[0].strip()
                    )
                    and cur_len <= width
                ):
                    lines.append(indent + "".join(cur_line))
                else:
                    while cur_line:
                        if (
                            cur_line[-1].strip()
                            and cur_len + self.placeholder_len <= width
                        ):
                            cur_line.append(self.placeholder)
                            lines.append(indent + "".join(cur_line))
                            break
                        cur_len -= len_without_ansi(cur_line[-1])
                        del cur_line[-1]
                    else:
                        if lines:
                            prev_line = lines[-1].rstrip()
                            prev_line_len = len_without_ansi(prev_line)
                            if prev_line_len + self.placeholder_len <= self.width:
                                lines[-1] = prev_line + self.placeholder
                                break
                        lines.append(indent + self.placeholder.lstrip())
                    break
        return lines

    def wrap(self, text: str) -> List[str]:
        return super().wrap(text)

    def fill(self, text: str) -> str:
        return super().fill(text)
