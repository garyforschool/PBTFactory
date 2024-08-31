from __future__ import annotations
from .mixins import UpdateDictMixin


def csp_property(key):
    return property(
        lambda x: x._get_value(key),
        lambda x, v: x._set_value(key, v),
        lambda x: x._del_value(key),
        f"accessor for {key!r}",
    )


class ContentSecurityPolicy(UpdateDictMixin, dict):
    base_uri = csp_property("base-uri")
    child_src = csp_property("child-src")
    connect_src = csp_property("connect-src")
    default_src = csp_property("default-src")
    font_src = csp_property("font-src")
    form_action = csp_property("form-action")
    frame_ancestors = csp_property("frame-ancestors")
    frame_src = csp_property("frame-src")
    img_src = csp_property("img-src")
    manifest_src = csp_property("manifest-src")
    media_src = csp_property("media-src")
    navigate_to = csp_property("navigate-to")
    object_src = csp_property("object-src")
    prefetch_src = csp_property("prefetch-src")
    plugin_types = csp_property("plugin-types")
    report_to = csp_property("report-to")
    report_uri = csp_property("report-uri")
    sandbox = csp_property("sandbox")
    script_src = csp_property("script-src")
    script_src_attr = csp_property("script-src-attr")
    script_src_elem = csp_property("script-src-elem")
    style_src = csp_property("style-src")
    style_src_attr = csp_property("style-src-attr")
    style_src_elem = csp_property("style-src-elem")
    worker_src = csp_property("worker-src")

    def __init__(self, values=(), on_update=None):
        dict.__init__(self, values or ())
        self.on_update = on_update
        self.provided = values is not None

    def _get_value(self, key):
        return self.get(key)

    def _set_value(self, key, value):
        if value is None:
            self.pop(key, None)
        else:
            self[key] = value

    def _del_value(self, key):
        if key in self:
            del self[key]

    def to_header(self):
        from ..http import dump_csp_header

        return dump_csp_header(self)

    def __str__(self):
        return self.to_header()

    def __repr__(self):
        kv_str = " ".join(f"{k}={v!r}" for k, v in sorted(self.items()))
        return f"<{type(self).__name__} {kv_str}>"