from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import join
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.orm import create_session
from sqlalchemy.orm import mapper
from sqlalchemy.orm import relation
from sqlalchemy.orm import scoped_session
from .utils import application
from .utils import parse_creole

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    from threading import get_ident
metadata = MetaData()


def new_db_session():
    return create_session(application.database_engine, autoflush=True, autocommit=False)


session = scoped_session(new_db_session, get_ident)
page_table = Table(
    "pages",
    metadata,
    Column("page_id", Integer, primary_key=True),
    Column("name", String(60), unique=True),
)
revision_table = Table(
    "revisions",
    metadata,
    Column("revision_id", Integer, primary_key=True),
    Column("page_id", Integer, ForeignKey("pages.page_id")),
    Column("timestamp", DateTime),
    Column("text", String),
    Column("change_note", String(200)),
)


class Revision:
    query = session.query_property()

    def __init__(self, page, text, change_note="", timestamp=None):
        if isinstance(page, int):
            self.page_id = page
        else:
            self.page = page
        self.text = text
        self.change_note = change_note
        self.timestamp = timestamp or datetime.utcnow()

    def render(self):
        return parse_creole(self.text)

    def __repr__(self):
        return f"<{type(self).__name__} {self.page_id!r}:{self.revision_id!r}>"


class Page:
    query = session.query_property()

    def __init__(self, name):
        self.name = name

    @property
    def title(self):
        return self.name.replace("_", " ")

    def __repr__(self):
        return f"<{type(self).__name__} {self.name!r}>"


class RevisionedPage(Page, Revision):
    query = session.query_property()

    def __init__(self):
        raise TypeError(
            "cannot create WikiPage instances, use the Page and Revision classes for data manipulation."
        )

    def __repr__(self):
        return f"<{type(self).__name__} {self.name!r}:{self.revision_id!r}>"


mapper(Revision, revision_table)
mapper(
    Page,
    page_table,
    properties=dict(
        revisions=relation(
            Revision, backref="page", order_by=Revision.revision_id.desc()
        )
    ),
)
mapper(
    RevisionedPage,
    join(page_table, revision_table),
    properties=dict(page_id=[page_table.c.page_id, revision_table.c.page_id]),
)
