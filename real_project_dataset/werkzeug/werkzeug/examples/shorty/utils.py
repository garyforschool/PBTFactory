from os import path
from random import randrange
from random import sample
from urllib.parse import urlsplit
from jinja2 import Environment
from jinja2 import FileSystemLoader
from sqlalchemy import MetaData
from sqlalchemy.orm import create_session
from sqlalchemy.orm import scoped_session
from werkzeug.local import Local
from werkzeug.local import LocalManager
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.utils import cached_property
from werkzeug.wrappers import Response

TEMPLATE_PATH = path.join(path.dirname(__file__), "templates")
STATIC_PATH = path.join(path.dirname(__file__), "static")
ALLOWED_SCHEMES = frozenset(["http", "https", "ftp", "ftps"])
URL_CHARS = "abcdefghijkmpqrstuvwxyzABCDEFGHIJKLMNPQRST23456789"
local = Local()
local_manager = LocalManager([local])
application = local("application")
metadata = MetaData()
url_map = Map([Rule("/static/<file>", endpoint="static", build_only=True)])
session = scoped_session(
    lambda: create_session(
        application.database_engine, autocommit=False, autoflush=False
    )
)
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))


def expose(rule, **kw):

    def decorate(f):
        kw["endpoint"] = f.__name__
        url_map.add(Rule(rule, **kw))
        return f

    return decorate


def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)


jinja_env.globals["url_for"] = url_for


def render_template(template, **context):
    return Response(
        jinja_env.get_template(template).render(**context), mimetype="text/html"
    )


def validate_url(url):
    return urlsplit(url)[0] in ALLOWED_SCHEMES


def get_random_uid():
    return "".join(sample(URL_CHARS, randrange(3, 9)))


class Pagination:

    def __init__(self, query, per_page, page, endpoint):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.endpoint = endpoint

    @cached_property
    def count(self):
        return self.query.count()

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
        return url_for(self.endpoint, page=self.page - 1)

    @property
    def next(self):
        return url_for(self.endpoint, page=self.page + 1)

    @property
    def pages(self):
        return max(0, self.count - 1) // self.per_page + 1
