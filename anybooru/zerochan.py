"""Configured JSON client for the Zerochan image board."""

from .api_zerochan import ZerochanApi_Mixin
from .anybooru import _Anybooru


class Zerochan(_Anybooru, ZerochanApi_Mixin):
    """Access Zerochan's read-only JSON API.

    Requests use ``GET`` and select JSON with a query marker. The API page
    requires a User-Agent containing the project name and the caller's
    Zerochan username; configure it through ``request.user_agent``. No login
    is implemented, and a site entry needs only its URL.
    """

    def __init__(self, site_name=None, site_url=None, proxies=None, *,
                 config_file=None, timeout=None, user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)

    def request(self, path, *, params=None, envelope=None):
        """Call a relative Zerochan path; the request is always a ``GET``.

        `path` is a relative URL path: empty for the entry list, URL-escaped
        tag names (comma-joined for multiple tags), or a numeric entry id.
        Raw paths are escaped by the caller; native methods encode tags.
        The ``json`` query value is added here, so callers never write it
        and no ``.json`` path suffix is used.

        `params` are the API page's own query parameters and are sent as
        given; None values are omitted. The body arrives as JSON and is
        returned unchanged, unless `envelope` names the single key it
        arrived under -- Zerochan's list endpoints wrap their entries in
        ``items``. A missing key raises rather than falling back to another
        shape.

        The API is read-only, so this entry point takes no method, body or
        files: every call is a ``GET`` and nothing is inferred about
        permissions, paging or defaults. The documented rate limit (60
        requests per minute) is not enforced here.
        """
        path = path.lstrip("/")
        params = dict(params or {}, json="")
        result = self._request("{}/{}".format(self.site_url, path), path,
                               {"params": params})
        if envelope is None:
            return result
        return result[envelope]
