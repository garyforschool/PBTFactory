from typing import Any, Dict, Generator, List, NamedTuple, Optional, Tuple, Union, cast
from distutils.version import StrictVersion

__all__ = ["bump_version"]
_BUMP_VERSION_MAJOR: int = 0
_BUMP_VERSION_MINOR: int = 1
_BUMP_VERSION_PATCH: int = 2
_BUMP_VERSION_MINOR_ALPHA: int = 3
_BUMP_VERSION_MINOR_BETA: int = 4
_BUMP_VERSION_MINORS: Tuple[int, ...] = (
    _BUMP_VERSION_MINOR,
    _BUMP_VERSION_MINOR_ALPHA,
    _BUMP_VERSION_MINOR_BETA,
)
_BUMP_VERSION_PATCH_ALPHA: int = 5
_BUMP_VERSION_PATCH_BETA: int = 6
_BUMP_VERSION_PATCHES: Tuple[int, ...] = (
    _BUMP_VERSION_PATCH,
    _BUMP_VERSION_PATCH_ALPHA,
    _BUMP_VERSION_PATCH_BETA,
)
_BUMP_VERSION_POSITION_NAMES: Dict[int, str] = {
    _BUMP_VERSION_MAJOR: "major",
    _BUMP_VERSION_MINOR: "minor",
    _BUMP_VERSION_PATCH: "patch",
}


class _VersionPart(NamedTuple):
    pos: int
    txt: str
    num: int
    pre_txt: str
    pre_num: int
    name: str


def _each_version_part(ver_obj: StrictVersion) -> Generator[_VersionPart, None, None]:
    version: Tuple[int, int, int] = ver_obj.version
    prerelease: Union[Tuple[str, int], None] = ver_obj.prerelease
    prerelease_built = False
    for pos, num in enumerate(version):
        txt = "%s" % num
        if pos == 2 and num == 0:
            txt = ""
        kwargs: Dict[str, Any] = {
            "pos": pos,
            "txt": txt,
            "num": num,
            "pre_txt": "",
            "pre_num": -1,
            "name": _BUMP_VERSION_POSITION_NAMES[pos],
        }
        if prerelease_built is False and pos > 0 and prerelease is not None:
            prerelease = cast(Tuple[str, int], prerelease)
            should_add = True
            if pos == 1 and version[2] != 0:
                should_add = False
            if should_add is True:
                kwargs["txt"] = "%s%s%s" % (kwargs["txt"], prerelease[0], prerelease[1])
                kwargs["pre_txt"] = prerelease[0]
                kwargs["pre_num"] = prerelease[1]
                prerelease_built = True
        yield _VersionPart(**kwargs)


class _VersionInfo(NamedTuple):
    version: str
    major: _VersionPart
    minor: _VersionPart
    patch: _VersionPart
    pre_pos: int


def _build_version_info(version: str) -> _VersionInfo:
    ver_obj = StrictVersion(version)
    pre_pos = -1
    args: List[Any] = [version]
    for part in _each_version_part(ver_obj):
        if part.pre_txt:
            pre_pos = part.pos
        args.append(part)
    args.append(pre_pos)
    return _VersionInfo(*args)


def _build_version_bump_position(position: int) -> int:
    pos_min = -3
    pos_max = 2
    if (pos_min <= position <= pos_max) is False:
        raise ValueError(
            "The given value for 'position', %r, must be an 'int' between (%r) and (%r)."
            % (position, pos_min, pos_max)
        )
    if position < 0:
        pos_max += 1
        return pos_max + position
    return position


def _build_version_bump_type(
    position_positive: int, pre_release: Union[str, None]
) -> int:
    if pre_release is None:
        prerelease = ""
    else:
        pre_release = cast(str, pre_release)
        prerelease = pre_release.strip().lower()
    if prerelease == "":
        if position_positive == 0:
            return _BUMP_VERSION_MAJOR
        if position_positive == 1:
            return _BUMP_VERSION_MINOR
        return _BUMP_VERSION_PATCH
    if prerelease in ("a", "alpha", "b", "beta"):
        is_alpha = False
        if prerelease in ("a", "alpha"):
            is_alpha = True
        if position_positive == 0:
            raise ValueError(
                "Only the 'minor' or 'patch' parts of the version number can get a prerelease bump."
            )
        if position_positive == 1:
            if is_alpha is True:
                return _BUMP_VERSION_MINOR_ALPHA
            return _BUMP_VERSION_MINOR_BETA
        if is_alpha is True:
            return _BUMP_VERSION_PATCH_ALPHA
        return _BUMP_VERSION_PATCH_BETA
    raise ValueError(
        "The given value for 'pre_release', %r, can only be one of: 'a', 'alpha', 'b', 'beta', None."
    )


def bump_version(
    version: str, position: int = 2, pre_release: Optional[str] = None
) -> str:
    ver_info = _build_version_info(version)
    position = _build_version_bump_position(position)
    bump_type = _build_version_bump_type(position, pre_release)
    hold: List[Union[int, str]] = []
    if bump_type == _BUMP_VERSION_MAJOR:
        hold = [ver_info.major.num + 1, 0]
    elif bump_type in _BUMP_VERSION_MINORS:
        if bump_type == _BUMP_VERSION_MINOR:
            if ver_info.minor.pre_txt:
                hold = [ver_info.major.num, ver_info.minor.num]
            else:
                hold = [ver_info.major.num, ver_info.minor.num + 1]
        else:
            if bump_type == _BUMP_VERSION_MINOR_ALPHA:
                if ver_info.minor.pre_txt == "a":
                    part = "%sa%s" % (ver_info.minor.num, ver_info.minor.pre_num + 1)
                else:
                    part = "{}a0".format(ver_info.minor.num + 1)
            elif ver_info.minor.pre_txt == "a":
                part = "{}b0".format(ver_info.minor.num)
            elif ver_info.minor.pre_txt == "b":
                part = "%sb%s" % (ver_info.minor.num, ver_info.minor.pre_num + 1)
            else:
                part = "{}b0".format(ver_info.minor.num + 1)
            hold = [ver_info.major.num, part]
    elif bump_type == _BUMP_VERSION_PATCH:
        if ver_info.patch.pre_txt:
            hold = [ver_info.major.num, ver_info.minor.num, ver_info.patch.num]
        else:
            hold = [ver_info.major.num, ver_info.minor.num, ver_info.patch.num + 1]
    else:
        if bump_type == _BUMP_VERSION_PATCH_ALPHA:
            if ver_info.patch.pre_txt == "a":
                part = "%sa%s" % (ver_info.patch.num, ver_info.patch.pre_num + 1)
            else:
                part = "{}a0".format(ver_info.patch.num + 1)
        elif ver_info.patch.pre_txt == "a":
            part = "{}b0".format(ver_info.patch.num)
        elif ver_info.patch.pre_txt == "b":
            part = "%sb%s" % (ver_info.patch.num, ver_info.patch.pre_num + 1)
        else:
            part = "{}b0".format(ver_info.patch.num + 1)
        hold = [ver_info.major.num, ver_info.minor.num, part]
    out = ".".join(map(str, hold))
    return out
