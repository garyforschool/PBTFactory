from unittest import mock
from requests.help import info


def test_system_ssl():
    assert info()["system_ssl"]["version"] != ""


class VersionedPackage:

    def __init__(self, version):
        self.__version__ = version


def test_idna_without_version_attribute():
    with mock.patch("requests.help.idna", new=None):
        assert info()["idna"] == {"version": ""}


def test_idna_with_version_attribute():
    with mock.patch("requests.help.idna", new=VersionedPackage("2.6")):
        assert info()["idna"] == {"version": "2.6"}
