"""Configured client for nhentai (nhentai.net, API v2).

nhentai is a gallery site of its own rather than one of the booru engines this
package ships for: its JSON API lives under one ``/api/v2`` prefix on the site
root, it authenticates with an ``Authorization: Key`` header, and its list and
detail bodies keep the shapes the site declares in its own OpenAPI document,
which the mixin's docstrings report. This client wraps that JSON API and never
downloads media: gallery and thumbnail ``path`` values are relative to a media
server and reach the caller exactly as the site sent them.
"""

from .api_nhentai import NhentaiApi_Mixin
from .anybooru import _Anybooru


class Nhentai(_Anybooru, NhentaiApi_Mixin):
    """Read the nhentai JSON API anonymously or with an explicit API key.

    ``api_key=None`` selects ``sites.<site_name>.api_key`` from the loaded
    parameter file, matching the other families; the packaged value is empty.
    An explicit empty string stays empty and forbids using a configured key,
    so anonymous access is always available. A non-empty key is sent as
    ``Authorization: Key <api_key>``, the header form the site's own
    documentation asks for; no ``Bearer`` prefix, no query parameter and no
    other scheme is invented for it. A configured key can be overridden per
    call through ``headers``, as described below.

    This class has no User Token parameter and no login, token exchange or
    key management: it holds one optional key and nothing else. A caller who
    has a User Token instead can still pass it per call through ``headers``,
    where it overrides the configured key, and the site's own answer is what
    comes back. Which operations work anonymously is the site's decision and
    its API document marks it per route; the client never refuses a call for
    lack of a key and never falls back to another credential. An anonymous
    read-only probe run of all 31 GET routes of this family found 25 answering
    200 and six answering 401 -- ``gallery_favorite``, ``favorite_list``,
    ``favorite_random``, ``blacklist_list``, ``blacklist_ids`` and
    ``user_me`` -- which is the split this class leaves alone. It implements
    no login, no token exchange and no key management either. The constructor
    sends no request, so building a client cannot fail on a credential.
    """

    def __init__(self, site_name=None, site_url=None, api_key=None,
                 proxies=None, *, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.api_key = (self.site_settings["api_key"]
                        if api_key is None and site_name else api_key)

    def _headers(self, headers):
        """Merge the configured key with one call's own headers.

        Returns a new mapping every time: ``Authorization: Key <api_key>``
        first when the key is non-empty, then ``headers`` over it, so a
        caller-supplied ``Authorization`` or any other header wins. Nothing
        is added when both are empty.
        """
        request_headers = {}
        if self.api_key:
            request_headers["Authorization"] = "Key " + self.api_key
        request_headers.update(headers or {})
        return request_headers

    def request(self, method, path, *, params=None, data=None, headers=None):
        """Call one site-relative route and return the complete decoded JSON.

        ``path`` is resolved under the configured base URL with a leading
        slash removed, so ``'api/v2/galleries'`` and ``'/api/v2/galleries'``
        are the same route; it is not otherwise rewritten, validated or
        escaped, so identifiers and query strings are the caller's text --
        the native methods percent-encode a single identifier as one path
        segment. The base URL is the site root rather than the API prefix, so
        every native path starts with ``api/v2/``.

        ``params`` is the query mapping and is sent as given: ``None`` values
        are dropped, booleans are written lowercase, and nested mappings and
        sequences use the shared Rails-style encoding. Paging, filters and
        ordering are never filled in, clamped or converted, an unrecognized
        parameter name is still sent, and a value the site rejects produces
        the site's own status rather than a local error.

        ``data`` is written to the request's JSON body exactly as supplied,
        ``None`` values included; it is not cleaned, renamed or passed through
        the query encoder, and this method builds no form body. That is what
        the two methods with a JSON body use: each keyword argument of
        ``tag_search`` and ``blacklist_update`` becomes one field, so an empty
        call posts an empty object and an empty array stays an empty array.

        ``headers`` are sent verbatim for this request and are merged over the
        configured key, so a per-call ``Authorization`` or any other override
        is never dropped; no header is added when neither is set. The response
        body is returned exactly as the site sent it, its envelope, arrays and
        bare integers included. Non-2xx responses raise the shared HTTP error,
        which keeps the status and the body, and ``last_call`` holds the actual
        URL, status and response headers of the last request. Requests are
        never retried and the client adds no pagination, no format detection
        and no media download.
        """
        path = path.lstrip("/")
        url = "{}/{}".format(self.site_url, path)
        request_args = {}
        if params is not None:
            request_args["params"] = params
        if data is not None:
            request_args["json"] = data
        request_headers = self._headers(headers)
        if request_headers:
            request_args["headers"] = request_headers
        return self._request(url, path, request_args, method)
