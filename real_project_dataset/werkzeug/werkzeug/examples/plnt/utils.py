import re
from os import path
from jinja2 import Environment
from jinja2 import FileSystemLoader
from werkzeug.local import Local
from werkzeug.local import LocalManager
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.utils import cached_property
from werkzeug.wrappers import Response

local = Local()
local_manager = LocalManager([local])
request = local("request")
application = local("application")
url_adapter = local("url_adapter")
template_path = path.join(path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(template_path))
url_map = Map([Rule("/shared/<path:file>", endpoint="shared")])
endpoints = {}
_par_re = re.compile("\\n{2,}")
_entity_re = re.compile("&([^;]+);")
_striptags_re = re.compile("(<!--.*-->|<[^>]*>)")
from html.entities import name2codepoint

html_entities = name2codepoint.copy()
html_entities["apos"] = 39
del name2codepoint


def expose(url_rule, endpoint=None, **kwargs):

    def decorate(f):
        e = endpoint or f.__name__
        endpoints[e] = f
        url_map.add(Rule(url_rule, endpoint=e, **kwargs))
        return f

    return decorate


def render_template(template_name, **context):
    tmpl = jinja_env.get_template(template_name)
    context["url_for"] = url_for
    return Response(tmpl.render(context), mimetype="text/html")


def nl2p(s):
    return "\n".join(f"<p>{p}</p>" for p in _par_re.split(s))


def url_for(endpoint, **kw):
    return url_adapter.build(endpoint, kw)


def strip_tags(s):

    def handle_match(m):
        name = m.group(1)
        if name in html_entities:
            return chr(html_entities[name])
        if name[:2] in ("#x", "#X"):
            try:
                return chr(int(name[2:], 16))
            except ValueError:
                return ""
        elif name.startswith("#"):
            try:
                return chr(int(name[1:]))
            except ValueError:
                return ""
        return ""

    return _entity_re.sub(handle_match, _striptags_re.sub("", s))


class Pagination:

    def __init__(self, query, per_page, page, endpoint):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.endpoint = endpoint

    @cached_property
    def entries(self):
        return (
            self.query.offset((self.page - 1) * self.per_page)
            .limit(self.per_page)
            .all()
        )

    @cached_property
    def count(self):
        return self.query.count()

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def previous(self):
        return url_for(self.endpoint, page=self.page - 1)

    @property
    def next(self):
        return url_for(self.endpoint, page=self.page + 1)

    @property
    def pages(self):
        return max(0, self.count - 1) // self.per_page + 1
