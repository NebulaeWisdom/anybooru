"""Configured client for pixiv (www.pixiv.net and app-api.pixiv.net).

pixiv is an illustration site of its own rather than one of the booru engines
this package ships for, and its two JSON APIs live on two different hosts. The
web API is the site's own front end under ``/ajax`` on ``https://www.pixiv.net``
and answers ``{"error": ..., "body": ...}`` envelopes, some routes also
carrying ``message``; the
app API is the official mobile client API under ``/v1`` and ``/v2`` on
``https://app-api.pixiv.net`` and answers bare JSON. This client keeps both
shapes as received and never downloads media: illustration ``url``/``urls``,
user ``image`` and ugoira ``zip_urls`` values reach the caller exactly as the
site sent them.

Constructor options, the ``request`` entry point, return values and
``last_call`` are documented in ``docs/pixiv.md``; the per-method parameter and
field reference is ``docs/pixiv-api.md``.
"""

from urllib.parse import urljoin

from .api_pixiv import PixivApi_Mixin
from .anybooru import _Anybooru


class Pixiv(_Anybooru, PixivApi_Mixin):
    """Read the pixiv web and app JSON APIs anonymously or with credentials.

    ``cookie=None``, ``access_token=None`` and ``csrf_token=None`` each select
    the matching key of ``sites.<site_name>`` from the loaded parameter file,
    matching the other families; the packaged values are empty. An explicit
    empty string stays empty and forbids using a configured value, so
    anonymous access is always available. Each credential belongs to exactly
    one host: the web host takes the login session as a ``Cookie`` header and
    the CSRF token that goes with it, the app host takes
    ``Authorization: Bearer <access_token>``. Which headers a call receives
    follows only the ``api`` value it selects: the URL is never inspected to
    choose a credential, so a caller who passes an absolute ``next_url`` must
    also pass ``api='app'`` for the app listing it came from.

    ``site_url`` is the web root and defaults to ``sites.<site_name>.url``;
    ``app_url`` is the separate app root and defaults to
    ``sites.<site_name>.app_url``. Both may be given explicitly, which is how
    the class is used without a ``site_name``: ``Pixiv(site_url=...,
    app_url=...)`` needs no configured site entry, though the shared
    transport still reads the ``request`` block (timeout, proxies, user
    agent) from the loaded parameter file.

    This class has no login, no OAuth token exchange and no token refresh: it
    holds the values it was given and a rejected or expired one produces the
    site's own answer. The constructor sends no request, so building a client
    cannot fail on a credential.
    """

    def __init__(self, site_name=None, site_url=None, cookie=None,
                 access_token=None, proxies=None, *, app_url=None,
                 csrf_token=None, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.app_url = (self.site_settings["app_url"]
                        if app_url is None and site_name else app_url)
        if self.app_url is not None:
            self.app_url = self.app_url.rstrip("/")
        self.cookie = (self.site_settings["cookie"]
                       if cookie is None and site_name else cookie)
        self.access_token = (self.site_settings["access_token"]
                             if access_token is None and site_name
                             else access_token)
        self.csrf_token = (self.site_settings["csrf_token"]
                           if csrf_token is None and site_name
                           else csrf_token)

    def _headers(self, api, headers):
        """Merge the credentials of one host with one call's own headers.

        Returns a new mapping every time. A ``web`` call always gets
        ``Referer: <site_url>/``, plus ``Cookie`` and ``X-CSRF-Token`` only
        when those configured values are non-empty; an ``app`` call gets
        ``Authorization: Bearer <access_token>`` only when the token is
        non-empty. The caller's ``headers`` are applied last and therefore
        override any of them for one call.
        """
        request_headers = {}
        if api == "web":
            request_headers["Referer"] = self.site_url + "/"
            if self.cookie:
                request_headers["Cookie"] = self.cookie
            if self.csrf_token:
                request_headers["X-CSRF-Token"] = self.csrf_token
        elif self.access_token:
            request_headers["Authorization"] = "Bearer " + self.access_token
        request_headers.update(headers or {})
        return request_headers

    def _request_text(self, url, api_call, request_args, method):
        """Return a successful response body as unchanged text."""
        return self._send(url, api_call, request_args, method).text

    def request(self, method, path, *, api="web", params=None, data=None,
                form=None, headers=None, response_format="json"):
        """Call one route on the selected host and return the body asked for.

        ``api`` names the host explicitly and is never guessed from ``path``:
        ``'web'`` (the default) resolves under ``site_url``, the
        ``https://www.pixiv.net`` root whose routes are ``ajax/...``,
        ``ranking.php`` and the like; ``'app'`` resolves under ``app_url``,
        the ``https://app-api.pixiv.net`` root whose routes are ``v1/...``,
        ``v2/...`` and ``webview/...``. Any other value raises ``KeyError``.

        ``path`` is joined onto the selected root with one slash, so
        ``'ajax/illust/149040133'``, ``'/ajax/illust/149040133'`` and an
        absolute URL all reach the address they name; an app listing's
        ``next_url`` can therefore be passed back verbatim to continue that
        listing. The path is not otherwise rewritten, validated or escaped --
        the native methods percent-encode one identifier as one path segment.

        ``params`` is the query mapping and is sent as given: ``None`` values
        are dropped, booleans are written lowercase, and nested mappings and
        sequences use the shared Rails-style encoding. ``data`` is written to
        the request's JSON body exactly as supplied, ``None`` values included,
        and ``form`` is written to the request's form body through the same
        encoder as ``params``; each is the caller's own object, is not cleaned
        or renamed, and at most one body form is used per call. Paging,
        filters and ordering are never filled in, clamped or converted, an
        unrecognized parameter name is still sent, and a value the site
        rejects produces the site's own status rather than a local error.

        ``headers`` are merged over the credentials ``_headers`` describes and
        override them, so one call can replace ``Referer``, ``Cookie``,
        ``Authorization`` or anything else.

        ``response_format`` is explicit and never sniffed: ``'json'`` (the
        default) returns the complete decoded JSON body through the shared
        transport, and ``'text'`` returns ``response.text`` unchanged, which
        is what the app novel ``webview`` route answers with. Any other value
        raises ``KeyError`` rather than guessing a format, and no Content-Type
        is consulted to choose one.

        The body is returned exactly as the site sent it: the web
        ``{"error", "message", "body"}`` envelope and the app ``next_url``
        listings are not split or renamed, and a web ``error: true`` body
        arrives as data rather than being turned into a local error.
        Redirects are never followed -- a 3xx raises the shared HTTP error
        with its ``Location`` intact -- and any non-2xx raises that error with
        the status and body preserved, while ``last_call`` holds the actual
        URL, status and response headers of the last request. Requests are
        never retried and no media is downloaded.
        """
        root = {"web": self.site_url, "app": self.app_url}[api]
        url = urljoin(root + "/", path)
        request_args = {}
        if params is not None:
            request_args["params"] = params
        if data is not None:
            request_args["json"] = data
        if form is not None:
            request_args["data"] = form
        request_headers = self._headers(api, headers)
        if request_headers:
            request_args["headers"] = request_headers
        request_args["allow_redirects"] = False
        send = {"json": self._request, "text": self._request_text}
        return send[response_format](url, path, request_args, method)
