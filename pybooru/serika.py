"""Configured client for the Serika engine's two HTTP API surfaces."""

from .api_serika import SerikaApi_Mixin
from .pybooru import _Pybooru
from .resources import json_params


class Serika(_Pybooru, SerikaApi_Mixin):
    """Access official v1 and unversioned internal routes on Serika instances.

    API keys use Bearer authentication. An empty key sends no authentication;
    this client does not implement the site's browser-cookie login flow.
    """

    def __init__(self, site_name=None, site_url=None, api_key=None, proxies=None,
                 *, config_file="pybooru.json", timeout=None, user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.api_key = (self.site_settings["api_key"]
                        if api_key is None and site_name else api_key)
        if self.api_key:
            self.client.headers["Authorization"] = "Bearer " + self.api_key

    def request(self, method, path, *, params=None, data=None, files=None,
                binary=False, envelope=None):
        """Call a relative route without adding a suffix or API version.

        Query parameters are flat scalars; CSV parameters such as tags and
        ratings are strings, not Rails arrays. None values are omitted.
        data is JSON unless files is supplied, when it is multipart form data.

        By default return the JSON body unchanged. envelope='data' returns the
        official data field and records meta in last_call['meta'].
        envelope='users' handles the official users-list exception, returning
        users and recording pagination in last_call['meta']['pagination'].
        Internal methods preserve their original JSON envelopes.

        binary=True returns bytes, with Content-Type and image identifiers in
        last_call['headers']. All non-2xx responses raise PybooruHTTPError,
        retaining HTTP status and the error body, including a JSON code.
        """
        path = path.lstrip("/")
        request_args = {"params": params}
        if files is None:
            request_args["json"] = json_params(data)
        else:
            request_args.update(data=data, files=files)
        url = "{}/{}".format(self.site_url, path)
        if binary:
            return self._request_bytes(url, path, request_args, method)
        result = self._request(url, path, request_args, method)
        if result is None:
            return None
        if envelope == "data":
            self.last_call["meta"] = result["meta"]
            return result["data"]
        if envelope == "users":
            self.last_call["meta"] = {"pagination": result["pagination"]}
            return result["users"]
        return result
