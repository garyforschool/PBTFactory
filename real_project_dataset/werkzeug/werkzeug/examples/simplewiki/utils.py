from os import path
from urllib.parse import quote
from urllib.parse import urlencode
import creoleparser
from genshi import Stream
from genshi.template import TemplateLoader
from werkzeug.local import Local
from werkzeug.local import LocalManager
from werkzeug.utils import cached_property
from werkzeug.wrappers import Request as BaseRequest
from werkzeug.wrappers import Response as BaseResponse

TEMPLATE_PATH = path.join(path.dirname(__file__), "templates")
template_loader = TemplateLoader(
    TEMPLATE_PATH, auto_reload=True, variable_lookup="lenient"
)
local = Local()
local_manager = LocalManager([local])
request = local("request")
application = local("application")
creole_parser = creoleparser.Parser(
    dialect=creoleparser.create_dialect(
        creoleparser.creole10_base,
        wiki_links_base_url="",
        wiki_links_path_func=lambda page_name: href(page_name),
        wiki_links_space_char="_",
        no_wiki_monospace=True,
    ),
    method="html",
)


def generate_template(template_name, **context):
    context.update(href=href, format_datetime=format_datetime)
    return template_loader.load(template_name).generate(**context)


def parse_creole(markup):
    return creole_parser.generate(markup)


def href(*args, **kw):
    result = [f"{request.script_root if request else ''}/"]
    for idx, arg in enumerate(args):
        result.append(f"{'/' if idx else ''}{quote(arg)}")
    if kw:
        result.append(f"?{urlencode(kw)}")
    return "".join(result)


def format_datetime(obj):
    return obj.strftime("%Y-%m-%d %H:%M")


class Request(BaseRequest):

    def bind_to_context(self):
        local.request = self


class Response(BaseResponse):
    default_mimetype = "text/html"

    def __init__(
        self, response=None, status=200, headers=None, mimetype=None, content_type=None
    ):
        if isinstance(response, Stream):
            response = response.render("html", encoding=None, doctype="html")
        super().__init__(response, status, headers, mimetype, content_type)


class Pagination:

    def __init__(self, query, per_page, page, link):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.link = link
        self._count = None

    @cached_property
    def entries(self):
        return (
            self.query.offset((self.page - 1) * self.per_page)
            .limit(self.per_page)
            .all()
        )

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def previous(self):
        return href(self.link, page=self.page - 1)

    @property
    def next(self):
        return href(self.link, page=self.page + 1)

    @cached_property
    def count(self):
        return self.query.count()

    @property
    def pages(self):
        return max(0, self.count - 1) // self.per_page + 1
