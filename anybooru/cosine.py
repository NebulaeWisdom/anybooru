"""Configured client for Cosine Gallery (pic.cosine.ren).

Cosine Gallery is the image site of a Telegram channel, not one of the booru
engines this package ships for: it is a Next.js application with its own
routes, four response envelopes and its own error codes, and this client
keeps every one of them as received. It wraps the JSON routes and the RSS
feed and never downloads the preview or original images those responses
point at. Two of its routes are POSTs: one carries a revalidation secret and
the other can rebuild or delete the site's search index, so both are
documented and never called by this project.
"""

from .api_cosine import CosineApi_Mixin
from .anybooru import _Anybooru


class Cosine(_Anybooru, CosineApi_Mixin):
    """Read Cosine Gallery JSON and its feed, anonymously by default.

    ``revalidate_secret=None`` selects
    ``sites.<site_name>.revalidate_secret`` from the loaded parameter file,
    matching the other families; the packaged value is empty. An explicit
    empty string stays empty, so the default ``artwork_revalidate`` body
    carries ``secret=''`` and the site's answer is what the caller gets.
    The value is used in that one POST body and nowhere else: no header is
    built from it and no other route receives it, and whether the site
    accepts it is never decided locally.

    Either way this class logs in nowhere, and the constructor sends no
    request, so building a client cannot fail on a credential.
    """

    def __init__(self, site_name=None, site_url=None, revalidate_secret=None,
                 proxies=None, *, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.revalidate_secret = (
            self.site_settings["revalidate_secret"]
            if revalidate_secret is None and site_name else revalidate_secret)

    def _request_text(self, url, api_call, request_args, method):
        """Return a successful response body as unchanged text."""
        return self._send(url, api_call, request_args, method).text

    def request(self, method, path, *, params=None, data=None, headers=None,
                response_format="json"):
        """Call one site-relative route and return the body it asked for.

        ``path`` is resolved under the configured base URL with a leading
        slash removed, so ``'api/list'`` and ``'/api/list'`` are the same
        route and ``'feed.xml'`` reaches ``/feed.xml``; the path always stays
        under the site root and is not otherwise rewritten, validated or
        escaped, so identifiers and query strings are the caller's text --
        the native methods percent-encode a single identifier as one
        segment.

        ``params`` is the query mapping and is sent as given: ``None`` values
        are dropped, booleans are written lowercase, and nested mappings and
        sequences use the shared Rails-style encoding. Paging, filters and
        ordering are never filled in, clamped or converted, an unrecognized
        parameter name is still sent, and a value the site rejects produces
        the site's own error rather than a local one.

        ``data`` is written to the request's JSON body exactly as supplied,
        ``None`` values included; it is not cleaned, renamed or passed
        through the query encoder, and this method builds no form body.

        ``headers`` are sent verbatim for this request and nothing is added
        to them: this family's only credential travels in one JSON body, so
        no header is derived from it and no authentication header is
        invented.

        ``response_format`` is explicit and never sniffed: ``'json'`` (the
        default) returns the complete decoded JSON body through the shared
        transport, and ``'xml'`` returns ``response.text`` unchanged --
        declaration, root, whitespace and all -- without parsing or
        validating it. Any other value raises ``KeyError`` rather than
        guessing a format, and no Content-Type is consulted to choose one.

        The body is returned exactly as the site sent it, envelope included:
        the superjson ``{"json", "meta"}``, the listing objects and the
        ``{"success", "data"}`` wrapper are not split or renamed here.
        Non-2xx responses raise the shared HTTP error, which keeps the status
        and the body, and ``last_call`` holds the actual URL, status and
        response headers of the last request. Requests are never retried and
        the client adds no pagination and downloads no media.
        """
        path = path.lstrip("/")
        url = "{}/{}".format(self.site_url, path)
        request_args = {}
        if params is not None:
            request_args["params"] = params
        if data is not None:
            request_args["json"] = data
        if headers:
            request_args["headers"] = headers
        send = {"json": self._request, "xml": self._request_text}
        return send[response_format](url, path, request_args, method)
