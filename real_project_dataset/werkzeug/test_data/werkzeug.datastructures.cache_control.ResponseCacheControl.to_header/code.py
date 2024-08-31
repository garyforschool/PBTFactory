from __future__ import annotations
from .mixins import ImmutableDictMixin
from .mixins import UpdateDictMixin


def cache_control_property(key, empty, type):
    return property(
        lambda x: x._get_cache_value(key, empty, type),
        lambda x, v: x._set_cache_value(key, v, type),
        lambda x: x._del_cache_value(key),
        f"accessor for {key!r}",
    )


class _CacheControl(UpdateDictMixin, dict):
    no_cache = cache_control_property("no-cache", "*", None)
    no_store = cache_control_property("no-store", None, bool)
    max_age = cache_control_property("max-age", -1, int)
    no_transform = cache_control_property("no-transform", None, bool)

    def __init__(self, values=(), on_update=None):
        dict.__init__(self, values or ())
        self.on_update = on_update
        self.provided = values is not None

    def _get_cache_value(self, key, empty, type):
        if type is bool:
            return key in self
        if key in self:
            value = self[key]
            if value is None:
                return empty
            elif type is not None:
                try:
                    value = type(value)
                except ValueError:
                    pass
            return value
        return None

    def _set_cache_value(self, key, value, type):
        if type is bool:
            if value:
                self[key] = None
            else:
                self.pop(key, None)
        elif value is None:
            self.pop(key, None)
        elif value is True:
            self[key] = None
        elif type is not None:
            self[key] = type(value)
        else:
            self[key] = value

    def _del_cache_value(self, key):
        if key in self:
            del self[key]

    def to_header(self):
        return http.dump_header(self)

    def __str__(self):
        return self.to_header()

    def __repr__(self):
        kv_str = " ".join(f"{k}={v!r}" for k, v in sorted(self.items()))
        return f"<{type(self).__name__} {kv_str}>"

    cache_property = staticmethod(cache_control_property)


class RequestCacheControl(ImmutableDictMixin, _CacheControl):
    max_stale = cache_control_property("max-stale", "*", int)
    min_fresh = cache_control_property("min-fresh", None, int)
    only_if_cached = cache_control_property("only-if-cached", None, bool)


class ResponseCacheControl(_CacheControl):
    public = cache_control_property("public", None, bool)
    private = cache_control_property("private", "*", None)
    must_revalidate = cache_control_property("must-revalidate", None, bool)
    proxy_revalidate = cache_control_property("proxy-revalidate", None, bool)
    s_maxage = cache_control_property("s-maxage", None, int)
    immutable = cache_control_property("immutable", None, bool)
    must_understand = cache_control_property("must-understand", None, bool)


from .. import http