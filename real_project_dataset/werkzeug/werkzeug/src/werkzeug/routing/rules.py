from __future__ import annotations
import ast
import re
import typing as t
from dataclasses import dataclass
from string import Template
from types import CodeType
from urllib.parse import quote
from ..datastructures import iter_multi_items
from ..urls import _urlencode
from .converters import ValidationError

if t.TYPE_CHECKING:
    from .converters import BaseConverter
    from .map import Map


class Weighting(t.NamedTuple):
    number_static_weights: int
    static_weights: list[tuple[int, int]]
    number_argument_weights: int
    argument_weights: list[int]


@dataclass
class RulePart:
    content: str
    final: bool
    static: bool
    suffixed: bool
    weight: Weighting


_part_re = re.compile(
    """
    (?:
        (?P<slash>/)                                 # a slash
      |
        (?P<static>[^</]+)                           # static rule data
      |
        (?:
          <
            (?:
              (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)   # converter name
              (?:\\((?P<arguments>.*?)\\))?             # converter arguments
              :                                       # variable delimiter
            )?
            (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)      # variable name
           >
        )
    )
    """,
    re.VERBOSE,
)
_simple_rule_re = re.compile("<([^>]+)>")
_converter_args_re = re.compile(
    """
    \\s*
    ((?P<name>\\w+)\\s*=\\s*)?
    (?P<value>
        True|False|
        \\d+.\\d+|
        \\d+.|
        \\d+|
        [\\w\\d_.]+|
        [urUR]?(?P<stringval>"[^"]*?"|'[^']*')
    )\\s*,
    """,
    re.VERBOSE,
)
_PYTHON_CONSTANTS = {"None": None, "True": True, "False": False}


def _find(value: str, target: str, pos: int) -> int:
    try:
        return value.index(target, pos)
    except ValueError:
        return len(value)


def _pythonize(value: str) -> None | bool | int | float | str:
    if value in _PYTHON_CONSTANTS:
        return _PYTHON_CONSTANTS[value]
    for convert in (int, float):
        try:
            return convert(value)
        except ValueError:
            pass
    if value[:1] == value[-1:] and value[0] in "\"'":
        value = value[1:-1]
    return str(value)


def parse_converter_args(argstr: str) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    argstr += ","
    args = []
    kwargs = {}
    position = 0
    for item in _converter_args_re.finditer(argstr):
        if item.start() != position:
            raise ValueError(
                f"Cannot parse converter argument '{argstr[position:item.start()]}'"
            )
        value = item.group("stringval")
        if value is None:
            value = item.group("value")
        value = _pythonize(value)
        if not item.group("name"):
            args.append(value)
        else:
            name = item.group("name")
            kwargs[name] = value
        position = item.end()
    return tuple(args), kwargs


class RuleFactory:

    def get_rules(self, map: Map) -> t.Iterable[Rule]:
        raise NotImplementedError()


class Subdomain(RuleFactory):

    def __init__(self, subdomain: str, rules: t.Iterable[RuleFactory]) -> None:
        self.subdomain = subdomain
        self.rules = rules

    def get_rules(self, map: Map) -> t.Iterator[Rule]:
        for rulefactory in self.rules:
            for rule in rulefactory.get_rules(map):
                rule = rule.empty()
                rule.subdomain = self.subdomain
                yield rule


class Submount(RuleFactory):

    def __init__(self, path: str, rules: t.Iterable[RuleFactory]) -> None:
        self.path = path.rstrip("/")
        self.rules = rules

    def get_rules(self, map: Map) -> t.Iterator[Rule]:
        for rulefactory in self.rules:
            for rule in rulefactory.get_rules(map):
                rule = rule.empty()
                rule.rule = self.path + rule.rule
                yield rule


class EndpointPrefix(RuleFactory):

    def __init__(self, prefix: str, rules: t.Iterable[RuleFactory]) -> None:
        self.prefix = prefix
        self.rules = rules

    def get_rules(self, map: Map) -> t.Iterator[Rule]:
        for rulefactory in self.rules:
            for rule in rulefactory.get_rules(map):
                rule = rule.empty()
                rule.endpoint = self.prefix + rule.endpoint
                yield rule


class RuleTemplate:

    def __init__(self, rules: t.Iterable[Rule]) -> None:
        self.rules = list(rules)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> RuleTemplateFactory:
        return RuleTemplateFactory(self.rules, dict(*args, **kwargs))


class RuleTemplateFactory(RuleFactory):

    def __init__(
        self, rules: t.Iterable[RuleFactory], context: dict[str, t.Any]
    ) -> None:
        self.rules = rules
        self.context = context

    def get_rules(self, map: Map) -> t.Iterator[Rule]:
        for rulefactory in self.rules:
            for rule in rulefactory.get_rules(map):
                new_defaults = subdomain = None
                if rule.defaults:
                    new_defaults = {}
                    for key, value in rule.defaults.items():
                        if isinstance(value, str):
                            value = Template(value).substitute(self.context)
                        new_defaults[key] = value
                if rule.subdomain is not None:
                    subdomain = Template(rule.subdomain).substitute(self.context)
                new_endpoint = rule.endpoint
                if isinstance(new_endpoint, str):
                    new_endpoint = Template(new_endpoint).substitute(self.context)
                yield Rule(
                    Template(rule.rule).substitute(self.context),
                    new_defaults,
                    subdomain,
                    rule.methods,
                    rule.build_only,
                    new_endpoint,
                    rule.strict_slashes,
                )


def _prefix_names(src: str) -> ast.stmt:
    tree = ast.parse(src).body[0]
    if isinstance(tree, ast.Expr):
        tree = tree.value
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            node.id = f".{node.id}"
    return tree


_CALL_CONVERTER_CODE_FMT = "self._converters[{elem!r}].to_url()"
_IF_KWARGS_URL_ENCODE_CODE = """if kwargs:
    params = self._encode_query_vars(kwargs)
    q = "?" if params else ""
else:
    q = params = "\"
"""
_IF_KWARGS_URL_ENCODE_AST = _prefix_names(_IF_KWARGS_URL_ENCODE_CODE)
_URL_ENCODE_AST_NAMES = _prefix_names("q"), _prefix_names("params")


class Rule(RuleFactory):

    def __init__(
        self,
        string: str,
        defaults: t.Mapping[str, t.Any] | None = None,
        subdomain: str | None = None,
        methods: t.Iterable[str] | None = None,
        build_only: bool = False,
        endpoint: t.Any | None = None,
        strict_slashes: bool | None = None,
        merge_slashes: bool | None = None,
        redirect_to: str | t.Callable[..., str] | None = None,
        alias: bool = False,
        host: str | None = None,
        websocket: bool = False,
    ) -> None:
        if not string.startswith("/"):
            raise ValueError(f"URL rule '{string}' must start with a slash.")
        self.rule = string
        self.is_leaf = not string.endswith("/")
        self.is_branch = string.endswith("/")
        self.map: Map = None
        self.strict_slashes = strict_slashes
        self.merge_slashes = merge_slashes
        self.subdomain = subdomain
        self.host = host
        self.defaults = defaults
        self.build_only = build_only
        self.alias = alias
        self.websocket = websocket
        if methods is not None:
            if isinstance(methods, str):
                raise TypeError("'methods' should be a list of strings.")
            methods = {x.upper() for x in methods}
            if "HEAD" not in methods and "GET" in methods:
                methods.add("HEAD")
            if websocket and methods - {"GET", "HEAD", "OPTIONS"}:
                raise ValueError(
                    "WebSocket rules can only use 'GET', 'HEAD', and 'OPTIONS' methods."
                )
        self.methods = methods
        self.endpoint: t.Any = endpoint
        self.redirect_to = redirect_to
        if defaults:
            self.arguments = set(map(str, defaults))
        else:
            self.arguments = set()
        self._converters: dict[str, BaseConverter] = {}
        self._trace: list[tuple[bool, str]] = []
        self._parts: list[RulePart] = []

    def empty(self) -> Rule:
        return type(self)(self.rule, **self.get_empty_kwargs())

    def get_empty_kwargs(self) -> t.Mapping[str, t.Any]:
        defaults = None
        if self.defaults:
            defaults = dict(self.defaults)
        return dict(
            defaults=defaults,
            subdomain=self.subdomain,
            methods=self.methods,
            build_only=self.build_only,
            endpoint=self.endpoint,
            strict_slashes=self.strict_slashes,
            redirect_to=self.redirect_to,
            alias=self.alias,
            host=self.host,
        )

    def get_rules(self, map: Map) -> t.Iterator[Rule]:
        yield self

    def refresh(self) -> None:
        self.bind(self.map, rebind=True)

    def bind(self, map: Map, rebind: bool = False) -> None:
        if self.map is not None and not rebind:
            raise RuntimeError(f"url rule {self!r} already bound to map {self.map!r}")
        self.map = map
        if self.strict_slashes is None:
            self.strict_slashes = map.strict_slashes
        if self.merge_slashes is None:
            self.merge_slashes = map.merge_slashes
        if self.subdomain is None:
            self.subdomain = map.default_subdomain
        self.compile()

    def get_converter(
        self,
        variable_name: str,
        converter_name: str,
        args: tuple[t.Any, ...],
        kwargs: t.Mapping[str, t.Any],
    ) -> BaseConverter:
        if converter_name not in self.map.converters:
            raise LookupError(f"the converter {converter_name!r} does not exist")
        return self.map.converters[converter_name](self.map, *args, **kwargs)

    def _encode_query_vars(self, query_vars: t.Mapping[str, t.Any]) -> str:
        items: t.Iterable[tuple[str, str]] = iter_multi_items(query_vars)
        if self.map.sort_parameters:
            items = sorted(items, key=self.map.sort_key)
        return _urlencode(items)

    def _parse_rule(self, rule: str) -> t.Iterable[RulePart]:
        content = ""
        static = True
        argument_weights = []
        static_weights: list[tuple[int, int]] = []
        final = False
        convertor_number = 0
        pos = 0
        while pos < len(rule):
            match = _part_re.match(rule, pos)
            if match is None:
                raise ValueError(f"malformed url rule: {rule!r}")
            data = match.groupdict()
            if data["static"] is not None:
                static_weights.append((len(static_weights), -len(data["static"])))
                self._trace.append((False, data["static"]))
                content += data["static"] if static else re.escape(data["static"])
            if data["variable"] is not None:
                if static:
                    content = re.escape(content)
                static = False
                c_args, c_kwargs = parse_converter_args(data["arguments"] or "")
                convobj = self.get_converter(
                    data["variable"], data["converter"] or "default", c_args, c_kwargs
                )
                self._converters[data["variable"]] = convobj
                self.arguments.add(data["variable"])
                if not convobj.part_isolating:
                    final = True
                content += f"(?P<__werkzeug_{convertor_number}>{convobj.regex})"
                convertor_number += 1
                argument_weights.append(convobj.weight)
                self._trace.append((True, data["variable"]))
            if data["slash"] is not None:
                self._trace.append((False, "/"))
                if final:
                    content += "/"
                else:
                    if not static:
                        content += "\\Z"
                    weight = Weighting(
                        -len(static_weights),
                        static_weights,
                        -len(argument_weights),
                        argument_weights,
                    )
                    yield RulePart(
                        content=content,
                        final=final,
                        static=static,
                        suffixed=False,
                        weight=weight,
                    )
                    content = ""
                    static = True
                    argument_weights = []
                    static_weights = []
                    final = False
                    convertor_number = 0
            pos = match.end()
        suffixed = False
        if final and content[-1] == "/":
            suffixed = True
            content = content[:-1] + "(?<!/)(/?)"
        if not static:
            content += "\\Z"
        weight = Weighting(
            -len(static_weights),
            static_weights,
            -len(argument_weights),
            argument_weights,
        )
        yield RulePart(
            content=content,
            final=final,
            static=static,
            suffixed=suffixed,
            weight=weight,
        )
        if suffixed:
            yield RulePart(
                content="", final=False, static=True, suffixed=False, weight=weight
            )

    def compile(self) -> None:
        assert self.map is not None, "rule not bound"
        if self.map.host_matching:
            domain_rule = self.host or ""
        else:
            domain_rule = self.subdomain or ""
        self._parts = []
        self._trace = []
        self._converters = {}
        if domain_rule == "":
            self._parts = [
                RulePart(
                    content="",
                    final=False,
                    static=True,
                    suffixed=False,
                    weight=Weighting(0, [], 0, []),
                )
            ]
        else:
            self._parts.extend(self._parse_rule(domain_rule))
        self._trace.append((False, "|"))
        rule = self.rule
        if self.merge_slashes:
            rule = re.sub("/{2,}?", "/", self.rule)
        self._parts.extend(self._parse_rule(rule))
        self._build: t.Callable[..., tuple[str, str]]
        self._build = self._compile_builder(False).__get__(self, None)
        self._build_unknown: t.Callable[..., tuple[str, str]]
        self._build_unknown = self._compile_builder(True).__get__(self, None)

    @staticmethod
    def _get_func_code(code: CodeType, name: str) -> t.Callable[..., tuple[str, str]]:
        globs: dict[str, t.Any] = {}
        locs: dict[str, t.Any] = {}
        exec(code, globs, locs)
        return locs[name]

    def _compile_builder(
        self, append_unknown: bool = True
    ) -> t.Callable[..., tuple[str, str]]:
        defaults = self.defaults or {}
        dom_ops: list[tuple[bool, str]] = []
        url_ops: list[tuple[bool, str]] = []
        opl = dom_ops
        for is_dynamic, data in self._trace:
            if data == "|" and opl is dom_ops:
                opl = url_ops
                continue
            if is_dynamic and data in defaults:
                data = self._converters[data].to_url(defaults[data])
                opl.append((False, data))
            elif not is_dynamic:
                opl.append((False, quote(data, safe="!$&'()*+,/:;=@")))
            else:
                opl.append((True, data))

        def _convert(elem: str) -> ast.stmt:
            ret = _prefix_names(_CALL_CONVERTER_CODE_FMT.format(elem=elem))
            ret.args = [ast.Name(str(elem), ast.Load())]
            return ret

        def _parts(ops: list[tuple[bool, str]]) -> list[ast.AST]:
            parts = [
                (_convert(elem) if is_dynamic else ast.Constant(elem))
                for is_dynamic, elem in ops
            ]
            parts = parts or [ast.Constant("")]
            ret = [parts[0]]
            for p in parts[1:]:
                if isinstance(p, ast.Constant) and isinstance(ret[-1], ast.Constant):
                    ret[-1] = ast.Constant(ret[-1].value + p.value)
                else:
                    ret.append(p)
            return ret

        dom_parts = _parts(dom_ops)
        url_parts = _parts(url_ops)
        if not append_unknown:
            body = []
        else:
            body = [_IF_KWARGS_URL_ENCODE_AST]
            url_parts.extend(_URL_ENCODE_AST_NAMES)

        def _join(parts: list[ast.AST]) -> ast.AST:
            if len(parts) == 1:
                return parts[0]
            return ast.JoinedStr(parts)

        body.append(
            ast.Return(ast.Tuple([_join(dom_parts), _join(url_parts)], ast.Load()))
        )
        pargs = [
            elem
            for is_dynamic, elem in dom_ops + url_ops
            if is_dynamic and elem not in defaults
        ]
        kargs = [str(k) for k in defaults]
        func_ast: ast.FunctionDef = _prefix_names("def _(): pass")
        func_ast.name = f"<builder:{self.rule!r}>"
        func_ast.args.args.append(ast.arg(".self", None))
        for arg in pargs + kargs:
            func_ast.args.args.append(ast.arg(arg, None))
        func_ast.args.kwarg = ast.arg(".kwargs", None)
        for _ in kargs:
            func_ast.args.defaults.append(ast.Constant(""))
        func_ast.body = body
        module = ast.parse("")
        module.body = [func_ast]
        for node in ast.walk(module):
            if "lineno" in node._attributes:
                node.lineno = 1
            if "end_lineno" in node._attributes:
                node.end_lineno = node.lineno
            if "col_offset" in node._attributes:
                node.col_offset = 0
            if "end_col_offset" in node._attributes:
                node.end_col_offset = node.col_offset
        code = compile(module, "<werkzeug routing>", "exec")
        return self._get_func_code(code, func_ast.name)

    def build(
        self, values: t.Mapping[str, t.Any], append_unknown: bool = True
    ) -> tuple[str, str] | None:
        try:
            if append_unknown:
                return self._build_unknown(**values)
            else:
                return self._build(**values)
        except ValidationError:
            return None

    def provides_defaults_for(self, rule: Rule) -> bool:
        return bool(
            not self.build_only
            and self.defaults
            and self.endpoint == rule.endpoint
            and self != rule
            and self.arguments == rule.arguments
        )

    def suitable_for(
        self, values: t.Mapping[str, t.Any], method: str | None = None
    ) -> bool:
        if (
            method is not None
            and self.methods is not None
            and method not in self.methods
        ):
            return False
        defaults = self.defaults or ()
        for key in self.arguments:
            if key not in defaults and key not in values:
                return False
        if defaults:
            for key, value in defaults.items():
                if key in values and value != values[key]:
                    return False
        return True

    def build_compare_key(self) -> tuple[int, int, int]:
        return 1 if self.alias else 0, -len(self.arguments), -len(self.defaults or ())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self._trace == other._trace

    __hash__ = None

    def __str__(self) -> str:
        return self.rule

    def __repr__(self) -> str:
        if self.map is None:
            return f"<{type(self).__name__} (unbound)>"
        parts = []
        for is_dynamic, data in self._trace:
            if is_dynamic:
                parts.append(f"<{data}>")
            else:
                parts.append(data)
        parts_str = "".join(parts).lstrip("|")
        methods = f" ({', '.join(self.methods)})" if self.methods is not None else ""
        return f"<{type(self).__name__} {parts_str!r}{methods} -> {self.endpoint}>"
