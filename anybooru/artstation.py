"""Configured client for ArtStation (www.artstation.com).

ArtStation is a portfolio and community site, not one of the booru engines
this package ships for: it has its own root JSON routes, its own ``/api/v2``
community and search routes and an RSS feed, and this client keeps every
answer as received. It wraps the fifteen anonymous read routes of
``ArtStationApi_Mixin`` and never downloads the cover or asset images those
responses point at. The native methods do not log in, send writes or derive
credentials; authenticated and write routes have no native wrapper. The
general ``request`` entry point accepts an explicit method and headers.

Constructor options, the ``request`` entry point, return values and
``last_call`` are documented in ``docs/artstation.md``; the per-method
parameter and field reference is ``docs/artstation-api.md``.
"""

from .api_artstation import ArtStationApi_Mixin
from .anybooru import _Anybooru


class ArtStation(_Anybooru, ArtStationApi_Mixin):
    """Read ArtStation's public JSON routes and its artwork feed anonymously.

    The constructor takes no credential: ``sites.artstation`` holds only the
    base URL and the native methods are anonymous by default. Construction
    sends no request. ``username=''`` is passed to the shared transport, which
    then never reads a ``username`` setting for this site.

    Redirects keep the shared transport's behaviour, namely ``requests``
    following them. A caller that wants a response body tied to the URL it
    asked for can turn that off in its own process, as the packaged scripts
    do: ``client.client.request = partial(client.client.request,
    allow_redirects=False)``.
    """

    def __init__(self, site_name=None, site_url=None, proxies=None, *,
                 config_file=None, timeout=None, user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)

    def _request_text(self, url, api_call, request_args, method):
        """Return a successful response body as unchanged text."""
        return self._send(url, api_call, request_args, method).text

    def request(self, method, path, *, params=None, data=None, headers=None,
                response_format="json"):
        """Call one site-relative route and return the body it asked for.

        ``path`` is resolved under the configured base URL with a leading
        slash removed, so ``'projects.json'`` and ``'/projects.json'`` are the
        same route; the path always stays under the site root and is not
        otherwise rewritten, validated or escaped, so identifiers and query
        strings are the caller's text -- the native methods percent-encode a
        single identifier as one segment. The sampled unknown root paths
        answered with Explore HTML and status 200, so a 200 alone does not
        prove that a route exists. JSON decoding errors are preserved rather
        than retried as HTML.

        ``params`` is the query mapping and is sent as given: ``None`` values
        are dropped, booleans are written lowercase, and nested mappings and
        sequences use the shared Rails-style encoding. Paging, filters and
        ordering are never filled in, clamped or converted, an unrecognized
        parameter name is still sent, and a value the site rejects produces
        the site's own error rather than a local one. A route that wants one
        JSON string among its query values (``project_search``'s ``filters``)
        gets exactly the string the caller passed; a list arrives as repeated
        ``key[]`` pairs.

        ``data`` is written to the request's JSON body exactly as supplied,
        ``None`` values included; it is not cleaned, renamed or passed through
        the query encoder, and no form body is built. The fifteen native
        methods send no body at all, because the site's write routes are out
        of scope.

        ``headers`` are sent verbatim for this request and nothing is added to
        them; there is no credential to derive one from and no authentication
        header is invented.

        ``response_format`` is explicit and never sniffed: ``'json'`` (the
        default) returns the complete decoded JSON body through the shared
        transport, and ``'xml'`` and ``'html'`` both return ``response.text``
        unchanged -- declaration, root, whitespace and all -- without parsing
        or validating it. Any other value raises ``KeyError`` rather than
        guessing a format, and no ``Content-Type`` is consulted to choose one.

        The body is returned exactly as the site sent it, envelope included:
        the ``{"data", "total_count"}`` listings, the bare project object of
        ``random_project.json`` and the bare array of ``filter_fields.json``
        are not split or renamed here. Non-2xx responses raise the shared HTTP
        error, which keeps the status and the body, and ``last_call`` holds
        the actual URL, status and response headers of the last request.
        Requests are never retried and no media is downloaded.
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
        send = {"json": self._request, "xml": self._request_text,
                "html": self._request_text}
        return send[response_format](url, path, request_args, method)
