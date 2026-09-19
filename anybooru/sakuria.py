"""Configured client for Sakuria (sakuria-api.syarolia.com).

Sakuria is a third-party Pixiv mirror, not a booru. This client wraps the
JSON read routes of the API host: anonymous calls need no token, and a
non-empty token is attached for the routes that expect one.
"""

from .api_sakuria import SakuriaApi_Mixin
from .anybooru import _Anybooru


class Sakuria(_Anybooru, SakuriaApi_Mixin):
    """Read Sakuria JSON as an anonymous caller or with an explicit token.

    ``access_token=None`` selects ``sites.<site_name>.access_token`` from the
    loaded parameter file, matching the other families; the packaged value is
    empty. An explicit empty string stays empty and forbids using a configured
    credential, so anonymous access is always available. A non-empty token is
    sent as ``Authorization: Bearer``.

    No login helper is implemented: this class only attaches a token the
    caller already has, and it never fetches media bytes.
    """

    def __init__(self, site_name=None, site_url=None, access_token=None,
                 proxies=None, *, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.access_token = (self.site_settings["access_token"]
                             if access_token is None and site_name else access_token)

    def request(self, method, path, *, params=None, headers=None):
        """Call one site-relative route and return the complete decoded JSON.

        ``path`` may carry a leading slash (``'/me/likes'`` and
        ``'me/likes'`` are the same route); it is not otherwise rewritten,
        validated or escaped, so identifiers and query strings are the
        caller's text.

        ``params`` is the query mapping and is sent as given: ``None`` values
        are dropped, booleans are written lowercase, and nested mappings and
        sequences use the shared Rails-style encoding. Search, paging and
        size values are never filled in, clamped or converted, and an
        unrecognized parameter name is still sent: this client neither
        validates parameter names nor drops the ones it does not know.

        ``headers`` are sent verbatim for this request. When ``access_token``
        is non-empty, ``Authorization: Bearer <token>`` is added first and the
        caller's headers are merged over it, so an explicit
        ``x-sakuria-data-contract`` (or any other contract header) is never
        dropped. No other header is added implicitly.

        The response body is returned exactly as the site sent it, envelope
        included. Non-2xx responses raise the shared HTTP error and keep the
        body; ``last_call`` holds the actual URL, status and response headers
        of the last request. Requests are never retried, and the local
        client adds no pagination, no format detection and no media download.
        """
        path = path.lstrip("/")
        url = "{}/{}".format(self.site_url, path)
        request_headers = {}
        if self.access_token:
            request_headers["Authorization"] = "Bearer " + self.access_token
        request_headers.update(headers or {})
        request_args = {}
        if params is not None:
            request_args["params"] = params
        if request_headers:
            request_args["headers"] = request_headers
        return self._request(url, path, request_args, method)
