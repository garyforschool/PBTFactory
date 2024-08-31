from __future__ import annotations
from collections.abc import Collection


class ETags(Collection):

    def __init__(self, strong_etags=None, weak_etags=None, star_tag=False):
        if not star_tag and strong_etags:
            self._strong = frozenset(strong_etags)
        else:
            self._strong = frozenset()
        self._weak = frozenset(weak_etags or ())
        self.star_tag = star_tag

    def as_set(self, include_weak=False):
        rv = set(self._strong)
        if include_weak:
            rv.update(self._weak)
        return rv

    def is_weak(self, etag):
        return etag in self._weak

    def is_strong(self, etag):
        return etag in self._strong

    def contains_weak(self, etag):
        return self.is_weak(etag) or self.contains(etag)

    def contains(self, etag):
        if self.star_tag:
            return True
        return self.is_strong(etag)

    def contains_raw(self, etag):
        from ..http import unquote_etag

        etag, weak = unquote_etag(etag)
        if weak:
            return self.contains_weak(etag)
        return self.contains(etag)

    def to_header(self):
        if self.star_tag:
            return "*"
        return ", ".join(
            [f'"{x}"' for x in self._strong] + [f'W/"{x}"' for x in self._weak]
        )

    def __call__(self, etag=None, data=None, include_weak=False):
        if [etag, data].count(None) != 1:
            raise TypeError("either tag or data required, but at least one")
        if etag is None:
            from ..http import generate_etag

            etag = generate_etag(data)
        if include_weak:
            if etag in self._weak:
                return True
        return etag in self._strong

    def __bool__(self):
        return bool(self.star_tag or self._strong or self._weak)

    def __str__(self):
        return self.to_header()

    def __len__(self):
        return len(self._strong)

    def __iter__(self):
        return iter(self._strong)

    def __contains__(self, etag):
        return self.contains(etag)

    def __repr__(self):
        return f"<{type(self).__name__} {str(self)!r}>"
