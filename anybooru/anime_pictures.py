"""Configured client for Anime-Pictures (api.anime-pictures.net/api/v3).

Anime-Pictures is a site of its own rather than one of the booru engines this
package ships for. This client wraps the JSON routes of the API host on the
one hand and the host-root image entry on the other; it never downloads the
preview or original images that responses point at. Some routes need rights,
and an anonymous caller gets the site's own error rather than a local guess;
a credential supplied to the constructor or to a single call is used
verbatim.
"""

from urllib.parse import quote, urljoin

from .api_anime_pictures import AnimePicturesApi_Mixin
from .anybooru import _Anybooru


class AnimePictures(_Anybooru, AnimePicturesApi_Mixin):
    """Read Anime-Pictures JSON anonymously or with explicit credentials.

    ``authorization=None`` and ``cookie=None`` select
    ``sites.<site_name>.authorization`` and ``sites.<site_name>.cookie`` from
    the loaded parameter file, matching the other families; both packaged
    values are empty. An explicit empty string stays empty and forbids using
    a configured credential, so anonymous access is always available.

    A non-empty value is sent under the site's own header name and unchanged:
    ``authorization`` as the ``Authorization`` header and ``cookie`` as the
    ``Cookie`` header. No scheme is prefixed and no cookie name is guessed,
    because which form the write routes accept was not observed. This client
    implements no login, no refresh and no token route either way: pass a
    credential you already have, or stay anonymous. The constructor sends no
    request, so building a client cannot fail on a credential.
    """

    def __init__(self, site_name=None, site_url=None, authorization=None,
                 cookie=None, proxies=None, *, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.authorization = (self.site_settings["authorization"]
                              if authorization is None and site_name
                              else authorization)
        self.cookie = (self.site_settings["cookie"]
                       if cookie is None and site_name else cookie)

    def _headers(self, headers):
        """Merge the instance credentials with one call's own headers.

        Returns a new mapping every time: the instance credentials first,
        then ``headers`` over them, so a caller-supplied value for the same
        header name wins. Nothing is added when both are empty.
        """
        request_headers = {}
        if self.authorization:
            request_headers["Authorization"] = self.authorization
        if self.cookie:
            request_headers["Cookie"] = self.cookie
        request_headers.update(headers or {})
        return request_headers

    def request(self, method, path, *, params=None, data=None, headers=None):
        """Call one route and return the complete decoded JSON body.

        ``path`` is resolved against the configured base URL, which already
        ends in ``/api/v3``: ``'posts'`` calls ``/api/v3/posts``, a leading
        slash makes the path absolute on the host, so ``'/api/v3/posts'`` is
        the same route and ``'/'`` is the host root that ``service_info``
        reads. That is deliberately different from the other families, which
        strip a leading slash and always stay under the base URL. Path
        identifiers and query strings are the caller's text: nothing is
        validated or escaped here, and the per-resource methods encode a
        single identifier as one segment.

        ``params`` is the query mapping and is sent as given: ``None`` values
        are dropped, booleans are written lowercase, and nested mappings and
        sequences use the shared Rails-style encoding. Paging, filters and
        ordering are never filled in, clamped or converted, and a parameter
        the client does not know is still sent.

        ``data`` is written to the request's JSON body exactly as supplied,
        ``None`` values included; it is not cleaned, renamed or passed
        through the query encoder. Sites that expect a form body are not
        handled by this method.

        ``headers`` are sent verbatim for this request, merged over the
        instance credentials, so a per-call ``Idempotency-Key`` or an
        explicit override is never dropped. No other header is added
        implicitly and no credential is turned into a ``Bearer`` token.

        The response body is returned exactly as the site sent it, envelope
        included. Non-2xx responses raise the shared HTTP error, which keeps
        the status and the body -- including the plain-text body a
        non-numeric path segment produces, which is not JSON and therefore
        has no decoded ``data``. ``last_call`` holds the actual URL, status
        and response headers of the last request. Requests are never retried,
        and the client neither unwraps nor renames a field.
        """
        url = urljoin(self.site_url + "/", path)
        request_args = {}
        if params is not None:
            request_args["params"] = params
        if data is not None:
            request_args["json"] = data
        request_headers = self._headers(headers)
        if request_headers:
            request_args["headers"] = request_headers
        return self._request(url, path, request_args, method)

    def image_get(self, file_url, *, headers=None):
        """Fetch the site's own image entry bytes (``GET /pictures/get_image``).

        ``file_url`` is the ``file_url`` field of ``post_show``: a file name,
        not a URL, and the sample values contain spaces. It is encoded as a
        single path segment, so those spaces travel as ``%20`` and the whole
        name stays one segment. The route is on the host root, not under the
        API prefix.

        This is the only method of the family that returns bytes: the
        successful body is returned exactly as received, without JSON
        decoding, content sniffing or writing to disk, and the caller decides
        what the file is. ``headers`` are merged over the instance
        credentials for this call only. An anonymous call answered 403 with
        an empty body and no ``Content-Type``, so what a successful body is,
        and whether a credential makes the call succeed, is unverified; the
        errors of this route are never retried or rewritten.
        """
        path = "/pictures/get_image/{}".format(quote(file_url, safe=""))
        url = urljoin(self.site_url + "/", path)
        request_args = {}
        request_headers = self._headers(headers)
        if request_headers:
            request_args["headers"] = request_headers
        return self._request_bytes(url, path, request_args)
