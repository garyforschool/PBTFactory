"""Implements a number of Python exceptions which can be raised from within
a view to trigger a standard HTTP non-200 response.

Usage Example
-------------

.. code-block:: python

    from werkzeug.wrappers.request import Request
    from werkzeug.exceptions import HTTPException, NotFound

    def view(request):
        raise NotFound()

    @Request.application
    def application(request):
        try:
            return view(request)
        except HTTPException as e:
            return e

As you can see from this example those exceptions are callable WSGI
applications. However, they are not Werkzeug response objects. You
can get a response object by calling ``get_response()`` on a HTTP
exception.

Keep in mind that you may have to pass an environ (WSGI) or scope
(ASGI) to ``get_response()`` because some errors fetch additional
information relating to the request.

If you want to hook in a different exception page to say, a 404 status
code, you can add a second except for a specific subclass of an error:

.. code-block:: python

    @Request.application
    def application(request):
        try:
            return view(request)
        except NotFound as e:
            return not_found(request)
        except HTTPException as e:
            return e

"""

from __future__ import annotations
import typing as t
from datetime import datetime
from markupsafe import escape
from markupsafe import Markup
from ._internal import _get_environ

if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIEnvironment
    from .datastructures import WWWAuthenticate
    from .sansio.response import Response
    from .wrappers.request import Request as WSGIRequest
    from .wrappers.response import Response as WSGIResponse


class HTTPException(Exception):
    code: int | None = None
    description: str | None = None

    def __init__(
        self, description: str | None = None, response: Response | None = None
    ) -> None:
        super().__init__()
        if description is not None:
            self.description = description
        self.response = response

    @property
    def name(self) -> str:
        from .http import HTTP_STATUS_CODES

        return HTTP_STATUS_CODES.get(self.code, "Unknown Error")

    def get_description(
        self,
        environ: WSGIEnvironment | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> str:
        if self.description is None:
            description = ""
        else:
            description = self.description
        description = escape(description).replace("\n", Markup("<br>"))
        return f"<p>{description}</p>"

    def get_body(
        self,
        environ: WSGIEnvironment | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> str:
        return f"""<!doctype html>
<html lang=en>
<title>{self.code} {escape(self.name)}</title>
<h1>{escape(self.name)}</h1>
{self.get_description(environ)}
"""

    def get_headers(
        self,
        environ: WSGIEnvironment | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> list[tuple[str, str]]:
        return [("Content-Type", "text/html; charset=utf-8")]

    def get_response(
        self,
        environ: WSGIEnvironment | WSGIRequest | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> Response:
        from .wrappers.response import Response as WSGIResponse

        if self.response is not None:
            return self.response
        if environ is not None:
            environ = _get_environ(environ)
        headers = self.get_headers(environ, scope)
        return WSGIResponse(self.get_body(environ, scope), self.code, headers)

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> t.Iterable[bytes]:
        response = t.cast("WSGIResponse", self.get_response(environ))
        return response(environ, start_response)

    def __str__(self) -> str:
        code = self.code if self.code is not None else "???"
        return f"{code} {self.name}: {self.description}"

    def __repr__(self) -> str:
        code = self.code if self.code is not None else "???"
        return f"<{type(self).__name__} '{code}: {self.name}'>"


class BadRequest(HTTPException):
    code = 400
    description = (
        "The browser (or proxy) sent a request that this server could not understand."
    )


class BadRequestKeyError(BadRequest, KeyError):
    _description = BadRequest.description
    show_exception = False

    def __init__(self, arg: str | None = None, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        if arg is None:
            KeyError.__init__(self)
        else:
            KeyError.__init__(self, arg)

    @property
    def description(self) -> str:
        if self.show_exception:
            return f"{self._description}\n{KeyError.__name__}: {KeyError.__str__(self)}"
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value


class ClientDisconnected(BadRequest):
    pass


class SecurityError(BadRequest):
    pass


class BadHost(BadRequest):
    pass


class Unauthorized(HTTPException):
    code = 401
    description = "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required."

    def __init__(
        self,
        description: str | None = None,
        response: Response | None = None,
        www_authenticate: None | (WWWAuthenticate | t.Iterable[WWWAuthenticate]) = None,
    ) -> None:
        super().__init__(description, response)
        from .datastructures import WWWAuthenticate

        if isinstance(www_authenticate, WWWAuthenticate):
            www_authenticate = (www_authenticate,)
        self.www_authenticate = www_authenticate

    def get_headers(
        self,
        environ: WSGIEnvironment | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> list[tuple[str, str]]:
        headers = super().get_headers(environ, scope)
        if self.www_authenticate:
            headers.extend(("WWW-Authenticate", str(x)) for x in self.www_authenticate)
        return headers


class Forbidden(HTTPException):
    code = 403
    description = "You don't have the permission to access the requested resource. It is either read-protected or not readable by the server."


class NotFound(HTTPException):
    code = 404
    description = "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."


class MethodNotAllowed(HTTPException):
    code = 405
    description = "The method is not allowed for the requested URL."

    def __init__(
        self,
        valid_methods: t.Iterable[str] | None = None,
        description: str | None = None,
        response: Response | None = None,
    ) -> None:
        super().__init__(description=description, response=response)
        self.valid_methods = valid_methods

    def get_headers(
        self,
        environ: WSGIEnvironment | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> list[tuple[str, str]]:
        headers = super().get_headers(environ, scope)
        if self.valid_methods:
            headers.append(("Allow", ", ".join(self.valid_methods)))
        return headers


class NotAcceptable(HTTPException):
    code = 406
    description = "The resource identified by the request is only capable of generating response entities which have content characteristics not acceptable according to the accept headers sent in the request."


class RequestTimeout(HTTPException):
    code = 408
    description = "The server closed the network connection because the browser didn't finish the request within the specified time."


class Conflict(HTTPException):
    code = 409
    description = "A conflict happened while processing the request. The resource might have been modified while the request was being processed."


class Gone(HTTPException):
    code = 410
    description = "The requested URL is no longer available on this server and there is no forwarding address. If you followed a link from a foreign page, please contact the author of this page."


class LengthRequired(HTTPException):
    code = 411
    description = "A request with this method requires a valid <code>Content-Length</code> header."


class PreconditionFailed(HTTPException):
    code = 412
    description = (
        "The precondition on the request for the URL failed positive evaluation."
    )


class RequestEntityTooLarge(HTTPException):
    code = 413
    description = "The data value transmitted exceeds the capacity limit."


class RequestURITooLarge(HTTPException):
    code = 414
    description = "The length of the requested URL exceeds the capacity limit for this server. The request cannot be processed."


class UnsupportedMediaType(HTTPException):
    code = 415
    description = (
        "The server does not support the media type transmitted in the request."
    )


class RequestedRangeNotSatisfiable(HTTPException):
    code = 416
    description = "The server cannot provide the requested range."

    def __init__(
        self,
        length: int | None = None,
        units: str = "bytes",
        description: str | None = None,
        response: Response | None = None,
    ) -> None:
        super().__init__(description=description, response=response)
        self.length = length
        self.units = units

    def get_headers(
        self,
        environ: WSGIEnvironment | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> list[tuple[str, str]]:
        headers = super().get_headers(environ, scope)
        if self.length is not None:
            headers.append(("Content-Range", f"{self.units} */{self.length}"))
        return headers


class ExpectationFailed(HTTPException):
    code = 417
    description = "The server could not meet the requirements of the Expect header"


class ImATeapot(HTTPException):
    code = 418
    description = "This server is a teapot, not a coffee machine"


class UnprocessableEntity(HTTPException):
    code = 422
    description = "The request was well-formed but was unable to be followed due to semantic errors."


class Locked(HTTPException):
    code = 423
    description = "The resource that is being accessed is locked."


class FailedDependency(HTTPException):
    code = 424
    description = "The method could not be performed on the resource because the requested action depended on another action and that action failed."


class PreconditionRequired(HTTPException):
    code = 428
    description = 'This request is required to be conditional; try using "If-Match" or "If-Unmodified-Since".'


class _RetryAfter(HTTPException):

    def __init__(
        self,
        description: str | None = None,
        response: Response | None = None,
        retry_after: datetime | int | None = None,
    ) -> None:
        super().__init__(description, response)
        self.retry_after = retry_after

    def get_headers(
        self,
        environ: WSGIEnvironment | None = None,
        scope: dict[str, t.Any] | None = None,
    ) -> list[tuple[str, str]]:
        headers = super().get_headers(environ, scope)
        if self.retry_after:
            if isinstance(self.retry_after, datetime):
                from .http import http_date

                value = http_date(self.retry_after)
            else:
                value = str(self.retry_after)
            headers.append(("Retry-After", value))
        return headers


class TooManyRequests(_RetryAfter):
    code = 429
    description = "This user has exceeded an allotted request count. Try again later."


class RequestHeaderFieldsTooLarge(HTTPException):
    code = 431
    description = "One or more header fields exceeds the maximum size."


class UnavailableForLegalReasons(HTTPException):
    code = 451
    description = "Unavailable for legal reasons."


class InternalServerError(HTTPException):
    code = 500
    description = "The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application."

    def __init__(
        self,
        description: str | None = None,
        response: Response | None = None,
        original_exception: BaseException | None = None,
    ) -> None:
        self.original_exception = original_exception
        super().__init__(description=description, response=response)


class NotImplemented(HTTPException):
    code = 501
    description = "The server does not support the action requested by the browser."


class BadGateway(HTTPException):
    code = 502
    description = (
        "The proxy server received an invalid response from an upstream server."
    )


class ServiceUnavailable(_RetryAfter):
    code = 503
    description = "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later."


class GatewayTimeout(HTTPException):
    code = 504
    description = "The connection to an upstream server timed out."


class HTTPVersionNotSupported(HTTPException):
    code = 505
    description = (
        "The server does not support the HTTP protocol version used in the request."
    )


default_exceptions: dict[int, type[HTTPException]] = {}


def _find_exceptions() -> None:
    for obj in globals().values():
        try:
            is_http_exception = issubclass(obj, HTTPException)
        except TypeError:
            is_http_exception = False
        if not is_http_exception or obj.code is None:
            continue
        old_obj = default_exceptions.get(obj.code, None)
        if old_obj is not None and issubclass(obj, old_obj):
            continue
        default_exceptions[obj.code] = obj


_find_exceptions()
del _find_exceptions


class Aborter:

    def __init__(
        self,
        mapping: dict[int, type[HTTPException]] | None = None,
        extra: dict[int, type[HTTPException]] | None = None,
    ) -> None:
        if mapping is None:
            mapping = default_exceptions
        self.mapping = dict(mapping)
        if extra is not None:
            self.mapping.update(extra)

    def __call__(
        self, code: int | Response, *args: t.Any, **kwargs: t.Any
    ) -> t.NoReturn:
        from .sansio.response import Response

        if isinstance(code, Response):
            raise HTTPException(response=code)
        if code not in self.mapping:
            raise LookupError(f"no exception for {code!r}")
        raise self.mapping[code](*args, **kwargs)


def abort(status: int | Response, *args: t.Any, **kwargs: t.Any) -> t.NoReturn:
    _aborter(status, *args, **kwargs)


_aborter: Aborter = Aborter()