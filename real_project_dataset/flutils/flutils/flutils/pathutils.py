import functools
import getpass
import grp
import os
import pwd
import sys
from collections import deque
from os import PathLike
from pathlib import Path, PosixPath, WindowsPath
from typing import Deque, Generator, Optional, Union, cast

__all__ = [
    "chmod",
    "chown",
    "directory_present",
    "exists_as",
    "find_paths",
    "get_os_group",
    "get_os_user",
    "normalize_path",
    "path_absent",
]
_PATH = Union[PathLike, PosixPath, WindowsPath, bytes, str]
_STR_OR_INT_OR_NONE = Union[str, int, None]


def chmod(
    path: _PATH,
    mode_file: Optional[int] = None,
    mode_dir: Optional[int] = None,
    include_parent: bool = False,
) -> None:
    path = normalize_path(path)
    if mode_file is None:
        mode_file = 384
    if mode_dir is None:
        mode_dir = 448
    if "*" in path.as_posix():
        try:
            for sub_path in Path().glob(path.as_posix()):
                if sub_path.is_dir() is True:
                    sub_path.chmod(mode_dir)
                elif sub_path.is_file():
                    sub_path.chmod(mode_file)
        except NotImplementedError:
            pass
        else:
            if include_parent is True:
                parent = path.parent
                if parent.is_dir():
                    parent.chmod(mode_dir)
    elif path.exists() is True:
        if path.is_dir():
            path.chmod(mode_dir)
        elif path.is_file():
            path.chmod(mode_file)


def chown(
    path: _PATH,
    user: Optional[str] = None,
    group: Optional[str] = None,
    include_parent: bool = False,
) -> None:
    path = normalize_path(path)
    if isinstance(user, str) and user == "-1":
        uid = -1
    else:
        uid = get_os_user(user).pw_uid
    if isinstance(user, str) and group == "-1":
        gid = -1
    else:
        gid = get_os_group(group).gr_gid
    if "*" in path.as_posix():
        try:
            for sub_path in Path().glob(path.as_posix()):
                if sub_path.is_dir() or sub_path.is_file():
                    os.chown(sub_path.as_posix(), uid, gid)
        except NotImplementedError:
            pass
        else:
            if include_parent is True:
                path = path.parent
                if path.is_dir() is True:
                    os.chown(path.as_posix(), uid, gid)
    elif path.exists() is True:
        os.chown(path.as_posix(), uid, gid)


def directory_present(
    path: _PATH,
    mode: Optional[int] = None,
    user: Optional[str] = None,
    group: Optional[str] = None,
) -> Path:
    path = normalize_path(path)
    if "*" in path.as_posix():
        raise ValueError(
            "The path: %r must NOT contain any glob patterns." % path.as_posix()
        )
    if path.is_absolute() is False:
        raise ValueError(
            "The path: %r must be an absolute path.  A path is considered absolute if it has both a root and (if the flavour allows) a drive."
            % path.as_posix()
        )
    paths: Deque = deque()
    path_exists_as = exists_as(path)
    if path_exists_as == "":
        paths.append(path)
    elif path_exists_as != "directory":
        raise FileExistsError(
            "The path: %r can NOT be created as a directory because it already exists as a %s."
            % (path.as_posix(), path_exists_as)
        )
    parent = path.parent
    child = path
    while child.as_posix() != parent.as_posix():
        parent_exists_as = exists_as(parent)
        if parent_exists_as == "":
            paths.appendleft(parent)
            child = parent
            parent = parent.parent
        elif parent_exists_as == "directory":
            break
        else:
            raise FileExistsError(
                "Unable to create the directory: %r because theparent path: %r exists as a %s."
                % (path.as_posix, parent.as_posix(), parent_exists_as)
            )
    if mode is None:
        mode = 448
    if paths:
        for build_path in paths:
            build_path.mkdir(mode=mode)
            chown(build_path, user=user, group=group)
    else:
        chmod(path, mode_dir=mode)
        chown(path, user=user, group=group)
    return path


def exists_as(path: _PATH) -> str:
    path = normalize_path(path)
    if path.is_dir():
        return "directory"
    if path.is_file():
        return "file"
    if path.is_block_device():
        return "block device"
    if path.is_char_device():
        return "char device"
    if path.is_fifo():
        return "FIFO"
    if path.is_socket():
        return "socket"
    return ""


def find_paths(pattern: _PATH) -> Generator[Path, None, None]:
    pattern = normalize_path(pattern)
    search = pattern.as_posix()[len(pattern.anchor) :]
    yield from Path(pattern.anchor).glob(search)


def get_os_group(name: _STR_OR_INT_OR_NONE = None) -> grp.struct_group:
    if name is None:
        name = get_os_user().pw_gid
        name = cast(int, name)
    if isinstance(name, int):
        try:
            return grp.getgrgid(name)
        except KeyError:
            raise OSError(
                "The given gid: %r, is not a valid gid for this operating system."
                % name
            )
    try:
        return grp.getgrnam(name)
    except KeyError:
        raise OSError(
            'The given name: %r, is not a valid "group name" for this operating system.'
            % name
        )


def get_os_user(name: _STR_OR_INT_OR_NONE = None) -> pwd.struct_passwd:
    if isinstance(name, int):
        try:
            return pwd.getpwuid(name)
        except KeyError:
            raise OSError(
                "The given uid: %r, is not a valid uid for this operating system."
                % name
            )
    if name is None:
        name = getpass.getuser()
    try:
        return pwd.getpwnam(name)
    except KeyError:
        raise OSError(
            'The given name: %r, is not a valid "login name" for this operating system.'
            % name
        )


@functools.singledispatch
def normalize_path(path: _PATH) -> Path:
    path = cast(PathLike, path)
    path = os.path.expanduser(path)
    path = cast(PathLike, path)
    path = os.path.expandvars(path)
    path = cast(PathLike, path)
    if os.path.isabs(path) is False:
        path = os.path.join(os.getcwd(), path)
    path = cast(PathLike, path)
    path = os.path.normpath(path)
    path = cast(PathLike, path)
    path = os.path.normcase(path)
    path = cast(PathLike, path)
    return Path(path)


@normalize_path.register(bytes)
def _normalize_path_bytes(path: bytes) -> Path:
    out: str = path.decode(sys.getfilesystemencoding())
    return normalize_path(out)


@normalize_path.register(Path)
def _normalize_path_pathlib(path: Path) -> Path:
    return normalize_path(path.as_posix())


def path_absent(path: _PATH) -> None:
    path = normalize_path(path)
    path = path.as_posix()
    path = cast(str, path)
    if os.path.exists(path):
        if os.path.islink(path):
            os.unlink(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    p = os.path.join(root, name)
                    if os.path.isfile(p) or os.path.islink(p):
                        os.unlink(p)
                for name in dirs:
                    p = os.path.join(root, name)
                    if os.path.islink(p):
                        os.unlink(p)
                    else:
                        os.rmdir(p)
            if os.path.isdir(path):
                os.rmdir(path)
        else:
            os.unlink(path)
