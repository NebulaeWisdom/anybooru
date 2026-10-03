"""Configured client for Wallhaven (wallhaven.cc, API v1).

Wallhaven is a wallpaper site of its own rather than one of the booru engines
this package ships for: its JSON API sits under ``/api/v1`` on the site root,
it takes the account key as an ``apikey`` query value, and it returns the
``{"data": ...}`` detail bodies and ``{"data": [...], "meta": {...}}``
listings the site's own API page documents. This client wraps that read API
and never downloads media: wallpaper ``path``, ``thumbs`` and user ``avatar``
values reach the caller exactly as the site sent them.

Constructor options, the ``request`` entry point, return values and
``last_call`` are documented in ``docs/wallhaven.md``; the per-method
parameter and field reference is ``docs/wallhaven-api.md``.
"""

from .api_wallhaven import WallhavenApi_Mixin
from .anybooru import _Anybooru


class Wallhaven(_Anybooru, WallhavenApi_Mixin):
    """Read the Wallhaven API v1 anonymously or with an explicit API key.

    ``apikey=None`` selects ``sites.<site_name>.apikey`` from the loaded
    parameter file, matching the other families; the packaged value is empty.
    An explicit empty string stays empty and forbids using a configured key,
    so anonymous access is always available. A non-empty key is merged into
    every request as the ``apikey`` query value the site's API page asks for,
    and it can be overridden per call by passing ``apikey`` in ``params``
    (including an explicit ``''`` for one anonymous call).

    The API page also accepts the key as an ``X-API-Key`` header. This class
    never sends both forms at once: the query value is the configured one,
    and a caller who prefers the header passes it through ``headers`` on the
    call it wants. There is no login, token exchange or key management here;
    a missing or rejected key just gets the site's own 401, and an NSFW
    wallpaper stays unreachable without a valid key because the client grants
    no purity bit of its own. The constructor sends no request, so building a
    client cannot fail on a credential.

    The site documents a limit of 45 calls per minute and answers 429 beyond
    it. This class does not throttle, retry or spread calls out: pacing is
    the caller's, as the packaged scripts do.
    """

    def __init__(self, site_name=None, site_url=None, apikey=None,
                 proxies=None, *, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.apikey = (self.site_settings["apikey"]
                       if apikey is None and site_name else apikey)

    def _params(self, params):
        """Merge the configured key with one call's own query values.

        Returns a new mapping every time: ``apikey`` first when the key is
        non-empty, then ``params`` over it, so a caller-supplied ``apikey``
        (including an empty string that turns one call anonymous) wins and
        every other caller value is kept. The shared encoder then drops
        ``None`` values and leaves the rest as given.
        """
        request_params = {}
        if self.apikey:
            request_params["apikey"] = self.apikey
        request_params.update(params or {})
        return request_params

    def request(self, method, path, *, params=None, headers=None):
        """Call one site-relative route and return the complete decoded JSON.

        ``path`` is resolved under the configured base URL with a leading
        slash removed, so ``'api/v1/search'`` and ``'/api/v1/search'`` are
        the same route; the base URL is the site root rather than the API
        prefix, so every native path starts with ``api/v1/``. The path is not
        otherwise rewritten, validated or escaped, so identifiers and query
        strings are the caller's text -- the native methods percent-encode
        one identifier as one path segment.

        ``params`` is the query mapping, merged over the configured key as
        ``_params`` describes, and is then sent as given: ``None`` values are
        dropped, booleans are written lowercase, and nested mappings and
        sequences use the shared Rails-style encoding, so a Python list
        arrives as repeated ``key[]`` pairs -- pass a comma-separated string
        for the routes that take a list value. Paging, filters and ordering
        are never filled in, clamped or converted, an unrecognized parameter
        name is still sent, and a value the site rejects produces the site's
        own status rather than a local error.

        ``headers`` are sent verbatim for this request, which is how the
        site's ``X-API-Key`` form is reachable; nothing is added when they
        are empty, and the configured key is never duplicated into a header.

        The body is returned exactly as the site sent it: the ``{"data":
        ...}`` and ``{"data": [...], "meta": {...}}`` envelopes are not
        split, and a bare error object is kept as the raised error's data.
        Non-2xx responses raise the shared HTTP error, which keeps the
        status and the body, and ``last_call`` holds the actual URL, status
        and response headers of the last request. Requests are never retried
        and no media is downloaded.
        """
        path = path.lstrip("/")
        url = "{}/{}".format(self.site_url, path)
        request_args = {}
        request_params = self._params(params)
        if request_params:
            request_args["params"] = request_params
        if headers:
            request_args["headers"] = headers
        return self._request(url, path, request_args, method)
