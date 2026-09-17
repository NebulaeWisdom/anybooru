"""Configured JSON client for sites running the Danbooru engine."""

from .api_danbooru import DanbooruApi_Mixin
from .anybooru import _Anybooru
from .resources import json_params


class Danbooru(_Anybooru, DanbooruApi_Mixin):
    """Access Danbooru routes with Rails parameters and HTTP Basic API auth."""

    def __init__(self, site_name=None, site_url=None, username=None, api_key=None,
                 proxies=None, *, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, username, proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.api_key = (self.site_settings["api_key"]
                        if api_key is None and site_name else api_key)

    def request(self, method, path, *, params=None, data=None, files=None):
        """Call a relative JSON route; nested dicts become Rails parameters.

        `params` is the query string. `data` is a structured JSON body, or
        Rails form fields when `files` is supplied. File fields use requests'
        files mapping or list of (field, file) pairs. None values are omitted.
        Route IDs in a raw path must already be URL-escaped. No API permissions, search
        parameters, limits or site capabilities are guessed locally.
        """
        path = path.lstrip("/")
        if not path.endswith(".json"):
            path += ".json"
        request_args = {"params": params}
        if files is None:
            request_args["json"] = json_params(data)
        else:
            request_args.update(data=data, files=files)
        if self.username or self.api_key:
            request_args["auth"] = (self.username or "", self.api_key or "")
        return self._request("{}/{}".format(self.site_url, path), path,
                             request_args, method)

