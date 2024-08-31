from __future__ import annotations


class IfRange:

    def __init__(self, etag=None, date=None):
        self.etag = etag
        self.date = date

    def to_header(self):
        if self.date is not None:
            return http.http_date(self.date)
        if self.etag is not None:
            return http.quote_etag(self.etag)
        return ""

    def __str__(self):
        return self.to_header()

    def __repr__(self):
        return f"<{type(self).__name__} {str(self)!r}>"


class Range:

    def __init__(self, units, ranges):
        self.units = units
        self.ranges = ranges
        for start, end in ranges:
            if start is None or end is not None and (start < 0 or start >= end):
                raise ValueError(f"{start, end} is not a valid range.")

    def range_for_length(self, length):
        if self.units != "bytes" or length is None or len(self.ranges) != 1:
            return None
        start, end = self.ranges[0]
        if end is None:
            end = length
            if start < 0:
                start += length
        if http.is_byte_range_valid(start, end, length):
            return start, min(end, length)
        return None

    def make_content_range(self, length):
        rng = self.range_for_length(length)
        if rng is not None:
            return ContentRange(self.units, rng[0], rng[1], length)
        return None

    def to_header(self):
        ranges = []
        for begin, end in self.ranges:
            if end is None:
                ranges.append(f"{begin}-" if begin >= 0 else str(begin))
            else:
                ranges.append(f"{begin}-{end - 1}")
        return f"{self.units}={','.join(ranges)}"

    def to_content_range_header(self, length):
        range = self.range_for_length(length)
        if range is not None:
            return f"{self.units} {range[0]}-{range[1] - 1}/{length}"
        return None

    def __str__(self):
        return self.to_header()

    def __repr__(self):
        return f"<{type(self).__name__} {str(self)!r}>"


def _callback_property(name):

    def fget(self):
        return getattr(self, name)

    def fset(self, value):
        setattr(self, name, value)
        if self.on_update is not None:
            self.on_update(self)

    return property(fget, fset)


class ContentRange:

    def __init__(self, units, start, stop, length=None, on_update=None):
        assert http.is_byte_range_valid(start, stop, length), "Bad range provided"
        self.on_update = on_update
        self.set(start, stop, length, units)

    units = _callback_property("_units")
    start = _callback_property("_start")
    stop = _callback_property("_stop")
    length = _callback_property("_length")

    def set(self, start, stop, length=None, units="bytes"):
        assert http.is_byte_range_valid(start, stop, length), "Bad range provided"
        self._units = units
        self._start = start
        self._stop = stop
        self._length = length
        if self.on_update is not None:
            self.on_update(self)

    def unset(self):
        self.set(None, None, units=None)

    def to_header(self):
        if self.units is None:
            return ""
        if self.length is None:
            length = "*"
        else:
            length = self.length
        if self.start is None:
            return f"{self.units} */{length}"
        return f"{self.units} {self.start}-{self.stop - 1}/{length}"

    def __bool__(self):
        return self.units is not None

    def __str__(self):
        return self.to_header()

    def __repr__(self):
        return f"<{type(self).__name__} {str(self)!r}>"


from .. import http
