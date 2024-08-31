import importlib
import keyword
import sys
from collections import defaultdict
from importlib import util
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import (
    Any,
    DefaultDict,
    Dict,
    Generator,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

__all__ = ["cherry_pick", "lazy_import_module"]
_STRIPPED_DUNDERS = (
    "author",
    "author_email",
    "description",
    "doc",
    "download_url",
    "file",
    "license",
    "loadermaintainer",
    "maintainer_email",
    "path",
    "python_requires",
    "test_suite",
    "url",
    "version",
)
_DUNDERS = tuple("__%s__" % x for x in _STRIPPED_DUNDERS)
_BUILTIN_NAMES = tuple(
    filter(lambda x: x.startswith("__") and x.endswith("__"), dir("__builtins__"))
)


def _validate_attr_identifier(identifier: str, line: str) -> str:
    identifier = identifier.strip()
    if identifier == "":
        return identifier
    error: str = ""
    is_valid: bool = identifier.isidentifier()
    if is_valid is True and keyword.iskeyword(identifier):
        is_valid = False
        error = " Cannot be a keyword."
    if is_valid is True and identifier in _BUILTIN_NAMES:
        is_valid = False
        error = " Cannot be a builtin name."
    if is_valid is True and identifier in _DUNDERS:
        is_valid = False
        error = " Cannot be a special dunder."
    if is_valid is False:
        raise AttributeError(
            f"__attr_map__ contains an invalid item of: {line!r}. The identifier, {identifier!r}, is invalid.{error}"
        )
    return identifier


class _AttrMapping(NamedTuple):
    attr_name: str
    """The name of the cherry-picked module."""
    mod_name: str
    """The name of the cherry-picked module attribute; can be an empty str."""
    mod_attr_name: str
    """The pre-expanded __attr_map__ item (aka the foreign-name)"""
    item: str


def _expand_attr_map_item(foreign_name: str) -> _AttrMapping:
    if not isinstance(foreign_name, str):
        raise AttributeError("__attr_map__ must be a tuple containing strings.")
    mod, _, attr_name = foreign_name.partition(",")
    mod_name, _, mod_attr_name = mod.strip().partition(":")
    attr_name = _validate_attr_identifier(attr_name, foreign_name)
    mod_name = mod_name.strip()
    mod_attr_name = _validate_attr_identifier(mod_attr_name, foreign_name)
    if attr_name == "":
        if mod_attr_name != "":
            attr_name = mod_attr_name
        else:
            attr_name = mod_name.split(".")[-1]
    return _AttrMapping(attr_name, mod_name, mod_attr_name, foreign_name)


def _expand_attr_map(attr_map: Tuple[str, ...]) -> Generator[_AttrMapping, None, None]:
    hold: Set = set()
    for attr_mapping in map(_expand_attr_map_item, attr_map):
        if attr_mapping not in hold:
            hold.add(attr_mapping)
            yield attr_mapping


class _CherryPickMap(NamedTuple):
    modules: DefaultDict[str, List[_AttrMapping]]
    """The cherry-picking module attribute identifiers as the key. And the
    value is the module name, which should be the key in ``modules``
    """
    identifiers: Dict[str, str]


class CherryPickError(ImportError):

    def __init__(self, fullname, msg):
        msg = "%s.%s" % (fullname, msg)
        super().__init__(msg)


def _parse_attr_map(attr_map: Tuple[str, ...], fullname: str) -> _CherryPickMap:
    if not isinstance(attr_map, tuple):
        raise CherryPickError(
            fullname, "__attr_map__ must be a tuple not %r" % type(attr_map).__name__
        )
    modules: DefaultDict = defaultdict(list)
    identifiers: Dict = dict()
    try:
        for attr_mapping in _expand_attr_map(attr_map):
            modules[attr_mapping.mod_name].append(attr_mapping)
            if attr_mapping.attr_name in identifiers:
                raise CherryPickError(
                    fullname,
                    "__attr_map__ has the attribute %r defined multiple times"
                    % attr_mapping.attr_name,
                )
            identifiers[attr_mapping.attr_name] = attr_mapping.mod_name
    except AttributeError as err:
        raise CherryPickError(fullname, "%s" % err)
    return _CherryPickMap(modules, identifiers)


_CHERRY_PICK: str = "__cherry_pick__"
_EMPTY_CHERRY_PICK_MAP = _CherryPickMap(defaultdict(list), dict())


class _CherryPickingModule(ModuleType):

    def __getattribute__(self, attr: str) -> Any:
        _dict_ = object.__getattribute__(self, "__dict__")
        _cherry_pick_map_: _CherryPickMap = _dict_.get(
            "__cherry_pick_map__", _EMPTY_CHERRY_PICK_MAP
        )
        if attr in _cherry_pick_map_.identifiers:
            if _dict_[attr] == _CHERRY_PICK:
                mod_name = _cherry_pick_map_.identifiers[attr]
                module = importlib.import_module(mod_name)
                for attr_mapping in _cherry_pick_map_.modules[mod_name]:
                    if attr_mapping.mod_attr_name:
                        object.__setattr__(
                            self,
                            attr_mapping.attr_name,
                            getattr(module, attr_mapping.mod_attr_name),
                        )
                    else:
                        object.__setattr__(self, attr_mapping.attr_name, module)
        return object.__getattribute__(self, attr)


class _CherryPickingLoader(Loader):

    def create_module(self, spec):
        mod = ModuleType(spec.name)
        mod.__spec__ = spec
        return mod

    def exec_module(self, module: ModuleType) -> None:
        spec = module.__spec__
        module.__cherry_pick_map__ = _parse_attr_map(
            spec.loader_state["attr_map"], module.__name__
        )
        module.__attr_map__ = spec.loader_state["attr_map"]
        _all_ = list()
        iden_keys = module.__cherry_pick_map__.identifiers.keys
        for attr in iden_keys():
            _all_.append(attr)
            setattr(module, attr, _CHERRY_PICK)
        state_items = spec.loader_state["addtl_attrs"].items
        for key, val in state_items():
            if not key.startswith("_"):
                _all_.append(key)
            setattr(module, key, val)
        module.__all__ = list(sorted(_all_))
        module.__class__ = _CherryPickingModule


class _CherryPickFinder:

    def __init__(self):
        self._cache = dict()

    def __repr__(self):
        return "%s.%s" % (__name__, self.__class__.__name__)

    @classmethod
    def load(cls):
        for obj in sys.meta_path:
            if type(obj).__name__ == cls.__name__:
                return obj
        obj = cls()
        sys.meta_path.insert(0, obj)
        return obj

    @classmethod
    def add(
        cls,
        fullname: str,
        origin: str,
        path: Union[str, List],
        attr_map: Tuple[str, ...],
        **addtl_attrs: Any,
    ) -> None:
        obj = cls.load()
        obj._cache[fullname] = dict(
            fullname=fullname,
            origin=origin,
            path=path,
            attr_map=attr_map,
            addtl_attrs=addtl_attrs,
        )

    def find_spec(
        self, fullname: str, path: str, target: str = None
    ) -> Union[ModuleSpec, None]:
        if fullname in self._cache:
            loader_state = self._cache[fullname]
            kwargs = dict(origin=loader_state["origin"], loader_state=loader_state)
            loader = _CherryPickingLoader()
            if loader_state["path"]:
                kwargs["is_package"] = True
            return ModuleSpec(fullname, loader, **kwargs)
        return None


def cherry_pick(namespace: dict) -> None:
    fullname = namespace.get("__name__")
    fullname = cast(str, fullname)
    origin = namespace.get("__file__", "")
    origin = cast(str, origin)
    path = namespace.get("__path__")
    path = cast(List, path)
    attr_map: Tuple[str, ...] = namespace.get("__attr_map__", tuple())
    if not attr_map or not isinstance(attr_map, tuple):
        raise ImportError(
            "__attr_map__ must be defined as a tuple of strings in %r." % fullname
        )
    addtl_attrs = dict()
    for key in _DUNDERS:
        val: Any = namespace.get(key)
        if val:
            addtl_attrs[key] = val
    spec = util.find_spec(fullname)
    if spec is None:
        raise ImportError(f"Unable to find the spec for {fullname!r}")
    addtl_attrs["__loader__"] = spec.loader
    additional: Dict[str, Any] = namespace.get("__additional_attrs__", dict())
    if not isinstance(additional, dict):
        raise ImportError("__additional_attrs__ must be a dict in %r" % fullname)
    for key, val in additional.items():
        if not isinstance(key, str):
            raise ImportError(
                "__additional_attrs__ keys must be strings. in %r" % fullname
            )
        addtl_attrs[key] = val
    _CherryPickFinder.add(fullname, origin, path, attr_map, **addtl_attrs)
    if fullname in sys.modules:
        importlib.reload(sys.modules[fullname])
    else:
        importlib.import_module(fullname)


class _LazyModule(ModuleType):
    is_loaded: bool = False

    def __getattribute__(self, attr: str) -> Any:
        if attr == "is_loaded":
            return object.__getattribute__(self, "is_loaded")
        self.__class__ = ModuleType
        original_name = self.__spec__.name
        attrs_then = self.__spec__.loader_state["__dict__"]
        attrs_now = self.__dict__
        attrs_updated = {}
        for key, value in attrs_now.items():
            if key not in attrs_then:
                attrs_updated[key] = value
            elif id(attrs_now[key]) != id(attrs_then[key]):
                attrs_updated[key] = value
        self.__spec__.loader.exec_module(self)
        self.is_loaded = True
        if original_name in sys.modules:
            if id(self) != id(sys.modules[original_name]):
                raise ValueError(
                    f"module object for {original_name!r} substituted in sys.modules during a lazy load"
                )
        self.__dict__.update(attrs_updated)
        return getattr(self, attr)

    def __delattr__(self, attr: str) -> None:
        self.__getattribute__(attr)
        delattr(self, attr)


class _LazyLoader(Loader):

    @staticmethod
    def __check_eager_loader(loader: Loader) -> None:
        if not hasattr(loader, "exec_module"):
            raise TypeError("loader must define exec_module()")

    def __init__(self, loader: Loader) -> None:
        self.__check_eager_loader(loader)
        self.loader = loader

    def create_module(self, spec: ModuleSpec) -> Optional[ModuleType]:
        return self.loader.create_module(spec)

    def exec_module(self, module: ModuleType):
        module.__spec__.loader = self.loader
        module.__loader__ = self.loader
        loader_state = dict()
        loader_state["__dict__"] = module.__dict__.copy()
        loader_state["__class__"] = module.__class__
        module.__spec__.loader_state = loader_state
        module.__class__ = _LazyModule


def lazy_import_module(name: str, package: Optional[str] = None) -> ModuleType:
    if isinstance(package, str) and package:
        package = cast(str, package)
        fullname = util.resolve_name(name, package=package)
    else:
        fullname = util.resolve_name(name, package="")
    if fullname in sys.modules:
        return sys.modules[fullname]
    spec = util.find_spec(fullname)
    if spec is None:
        raise ImportError("name=%r package=%r" % (name, package))
    loader = spec.loader
    loader = cast(Loader, loader)
    lazy_loader = _LazyLoader(loader)
    if hasattr(spec.loader, "create_module"):
        module = lazy_loader.create_module(spec)
    else:
        module = None
    if module is None:
        module = ModuleType(fullname)
    module.__spec__ = spec
    lazy_loader.exec_module(module)
    sys.modules[fullname] = module
    return module
