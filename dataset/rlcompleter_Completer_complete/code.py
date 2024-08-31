_readline_available = False

import atexit
import builtins
import inspect
import __main__

__all__ = ["Completer"]


class Completer:

    def __init__(self, namespace=None):
        if namespace and not isinstance(namespace, dict):
            raise TypeError("namespace must be a dictionary")
        if namespace is None:
            self.use_main_ns = 1
        else:
            self.use_main_ns = 0
            self.namespace = namespace

    def complete(self, text, state):
        if self.use_main_ns:
            self.namespace = __main__.__dict__
        if not text.strip():
            if state == 0:
                if _readline_available:
                    readline.insert_text("\t")
                    readline.redisplay()
                    return ""
                else:
                    return "\t"
            else:
                return None
        if state == 0:
            if "." in text:
                self.matches = self.attr_matches(text)
            else:
                self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def _callable_postfix(self, val, word):
        if callable(val):
            word += "("
            try:
                if not inspect.signature(val).parameters:
                    word += ")"
            except ValueError:
                pass
        return word

    def global_matches(self, text):
        import keyword

        matches = []
        seen = {"__builtins__"}
        n = len(text)
        for word in keyword.kwlist:
            if word[:n] == text:
                seen.add(word)
                if word in {"finally", "try"}:
                    word = word + ":"
                elif word not in {
                    "False",
                    "None",
                    "True",
                    "break",
                    "continue",
                    "pass",
                    "else",
                }:
                    word = word + " "
                matches.append(word)
        for nspace in [self.namespace, builtins.__dict__]:
            for word, val in nspace.items():
                if word[:n] == text and word not in seen:
                    seen.add(word)
                    matches.append(self._callable_postfix(val, word))
        return matches

    def attr_matches(self, text):
        import re

        m = re.match("(\\w+(\\.\\w+)*)\\.(\\w*)", text)
        if not m:
            return []
        expr, attr = m.group(1, 3)
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            return []
        words = set(dir(thisobject))
        words.discard("__builtins__")
        if hasattr(thisobject, "__class__"):
            words.add("__class__")
            words.update(get_class_members(thisobject.__class__))
        matches = []
        n = len(attr)
        if attr == "":
            noprefix = "_"
        elif attr == "_":
            noprefix = "__"
        else:
            noprefix = None
        while True:
            for word in words:
                if word[:n] == attr and not (noprefix and word[: n + 1] == noprefix):
                    match = "%s.%s" % (expr, word)
                    if isinstance(getattr(type(thisobject), word, None), property):
                        matches.append(match)
                        continue
                    if (value := getattr(thisobject, word, None)) is not None:
                        matches.append(self._callable_postfix(value, match))
                    else:
                        matches.append(match)
            if matches or not noprefix:
                break
            if noprefix == "_":
                noprefix = "__"
            else:
                noprefix = None
        matches.sort()
        return matches


def get_class_members(klass):
    ret = dir(klass)
    if hasattr(klass, "__bases__"):
        for base in klass.__bases__:
            ret = ret + get_class_members(base)
    return ret
