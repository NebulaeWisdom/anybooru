"""Configured JSON client for Gelbooru (gelbooru.com)."""

from .api_gelbooru import GelbooruApi_Mixin
from .anybooru import _Anybooru


class Gelbooru(_Anybooru, GelbooruApi_Mixin):
    """Access Gelbooru's single ``index.php`` dispatcher over GET.

    The site publishes no resource paths: a call is
    ``<site root>/index.php?page=<page>&...``. The official API is the
    ``dapi`` page, which requires an account's ``api_key`` and ``user_id``
    and answers XML unless ``json=1`` is sent, so the client always sends
    ``json=1`` there. The in-site ``autocomplete2`` page answers JSON with
    no credentials. Bodies are returned exactly as received.
    """

    def __init__(self, site_name=None, site_url=None, api_key=None,
                 user_id=None, proxies=None, *, config_file=None,
                 timeout=None, user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.api_key = (self.site_settings["api_key"]
                        if api_key is None and site_name else api_key)
        self.user_id = (self.site_settings["user_id"]
                        if user_id is None and site_name else user_id)

    def request(self, page, *, params=None):
        """Call one ``index.php`` page with a GET request.

        `page` is the dispatcher value (`'dapi'`, `'autocomplete2'`, ...).
        `params` are that page's own parameters and are sent as given; None
        values are omitted.

        Only `page='dapi'` asks for JSON and carries credentials: `json=1`
        is added, and the configured `api_key` and `user_id` are added when
        they are non-empty. Leaving both empty sends an anonymous dapi
        request, which the site answers with `401` and an empty body. Other
        pages are called with exactly the parameters the caller passed.

        The JSON body is returned unchanged. Gelbooru's dapi payload has not
        been observed with an account, so no layer is unwrapped, no field is
        renamed and no shape is inferred; a JSON array stays an array and an
        object stays an object. HTTP errors keep their status and body,
        `last_call` records the final URL and status, there is no retry,
        validation or fallback, and the account's request quota is not
        enforced locally.
        """
        request_params = dict(params or {}, page=page)
        if page == "dapi":
            request_params["json"] = 1
            if self.api_key:
                request_params["api_key"] = self.api_key
            if self.user_id:
                request_params["user_id"] = self.user_id
        return self._request("{}/index.php".format(self.site_url), page,
                             {"params": request_params})
