"""Implements the wiki WSGI application which dispatches requests to
specific wiki pages and actions.
"""

from os import path
from sqlalchemy import create_engine
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import redirect
from werkzeug.wsgi import ClosingIterator
from . import actions
from .database import metadata
from .database import session
from .specialpages import page_not_found
from .specialpages import pages
from .utils import href
from .utils import local
from .utils import local_manager
from .utils import Request

SHARED_DATA = path.join(path.dirname(__file__), "shared")


class SimpleWiki:

    def __init__(self, database_uri):
        self.database_engine = create_engine(database_uri)
        self._dispatch = SharedDataMiddleware(
            self.dispatch_request, {"/_shared": SHARED_DATA}
        )
        self._dispatch = local_manager.make_middleware(self._dispatch)

    def init_database(self):
        metadata.create_all(bind=self.database_engine)

    def bind_to_context(self):
        local.application = self

    def dispatch_request(self, environ, start_response):
        self.bind_to_context()
        request = Request(environ)
        request.bind_to_context()
        action_name = request.args.get("action") or "show"
        page_name = "_".join([x for x in request.path.strip("/").split() if x])
        if not page_name:
            response = redirect(href("Main_Page"))
        elif page_name.startswith("Special:"):
            if page_name[8:] not in pages:
                response = page_not_found(request, page_name)
            else:
                response = pages[page_name[8:]](request)
        else:
            action = getattr(actions, f"on_{action_name}", None)
            if action is None:
                response = actions.missing_action(request, action_name)
            else:
                response = action(request, page_name)
        return ClosingIterator(response(environ, start_response), session.remove)

    def __call__(self, environ, start_response):
        return self._dispatch(environ, start_response)
