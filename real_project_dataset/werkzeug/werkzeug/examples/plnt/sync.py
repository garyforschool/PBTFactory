"""Does the synchronization. Called by "manage-plnt.py sync"."""

from datetime import datetime
import feedparser
from markupsafe import escape
from .database import Blog
from .database import Entry
from .database import session
from .utils import nl2p
from .utils import strip_tags

HTML_MIMETYPES = {"text/html", "application/xhtml+xml"}


def sync():
    for blog in Blog.query.all():
        feed = feedparser.parse(blog.feed_url)
        for entry in feed.entries:
            guid = entry.get("id") or entry.get("link")
            if not guid:
                continue
            old_entry = Entry.query.filter_by(guid=guid).first()
            if "title_detail" in entry:
                title = entry.title_detail.get("value") or ""
                if entry.title_detail.get("type") in HTML_MIMETYPES:
                    title = strip_tags(title)
                else:
                    title = escape(title)
            else:
                title = entry.get("title")
            url = entry.get("link") or blog.blog_url
            text = (
                entry.content[0] if "content" in entry else entry.get("summary_detail")
            )
            if not title or not text:
                continue
            if text.get("type") not in HTML_MIMETYPES:
                text = escape(nl2p(text.get("value") or ""))
            else:
                text = text.get("value") or ""
            if not text.strip():
                continue
            pub_date = (
                entry.get("published_parsed")
                or entry.get("created_parsed")
                or entry.get("date_parsed")
            )
            updated = entry.get("updated_parsed") or pub_date
            pub_date = pub_date or updated
            if not pub_date:
                continue
            pub_date = datetime(*pub_date[:6])
            updated = datetime(*updated[:6])
            if old_entry and updated <= old_entry.last_update:
                continue
            entry = old_entry or Entry()
            entry.blog = blog
            entry.guid = guid
            entry.title = title
            entry.url = url
            entry.text = text
            entry.pub_date = pub_date
            entry.last_update = updated
            session.add(entry)
    session.commit()
