"""Configured JSON client for sites running the Danbooru engine."""

from .api_danbooru import DanbooruApi_Mixin
from .pybooru import _Pybooru


class Danbooru(_Pybooru, DanbooruApi_Mixin):
    """Access Danbooru routes with Rails parameters and HTTP Basic API auth."""

    def __init__(self, site_name=None, site_url=None, username=None, api_key=None,
                 proxies=None, *, config_file="pybooru.json", timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, username, proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.api_key = (self.site_settings["api_key"]
                        if api_key is None and site_name else api_key)

    def request(self, method, path, *, params=None, data=None, files=None):
        """Call a relative JSON route; nested dicts become Rails parameters.

        `params` is the query string and `data` is the form body. File fields
        use requests' files mapping or list of (field, file) pairs. Route IDs
        in a raw path must already be URL-escaped. No API permissions, search
        parameters, limits or site capabilities are guessed locally.
        """
        path = path.lstrip("/")
        if not path.endswith(".json"):
            path += ".json"
        request_args = {"params": params, "data": data, "files": files}
        if self.username and self.api_key:
            request_args["auth"] = (self.username, self.api_key)
        return self._request("{}/{}".format(self.site_url, path), path,
                             request_args, method)

    def _get(self, api_call, params=None, method='GET', auth=False, file_=None):
        url = "{0}/{1}".format(self.site_url, api_call)
        if method == 'GET':
            request_args = {'params': params}
        else:
            request_args = {'data': params, 'files': file_}
        if self.username and self.api_key:
            request_args['auth'] = (self.username, self.api_key)
        return self._request(url, api_call, request_args, method)
