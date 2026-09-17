"""Configured JSON client for sites running the e621ng engine."""

from .api_e621 import E621Api_Mixin
from .anybooru import _Anybooru
from .resources import json_params


class E621(_Anybooru, E621Api_Mixin):
    """Access e621ng routes with Rails parameters and HTTP Basic API auth.

    The engine serves both e621.net and its safe mirror e926.net; a site name
    or an explicit URL selects which one the client talks to.
    """

    def __init__(self, site_name=None, site_url=None, username=None, api_key=None,
                 proxies=None, *, config_file=None, timeout=None,
                 user_agent=None):
        super().__init__(site_name, site_url, username, proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.api_key = (self.site_settings["api_key"]
                        if api_key is None and site_name else api_key)

    def request(self, method, path, *, params=None, data=None, files=None,
                envelope=None):
        """Call a relative JSON route; nested dicts become Rails parameters.

        `params` is the query string. `data` is a structured JSON body, or
        Rails form fields when `files` is supplied. File fields use requests'
        files mapping or list of (field, file) pairs. None values are omitted.
        Route IDs in a raw path must already be URL-escaped. No API
        permissions, search parameters, limits or site capabilities are
        guessed locally.

        The body is returned as it arrives. `envelope` names the single key
        the route put that body under, for the calls whose controller wraps
        it; an absent key raises rather than falling back to another shape.
        Credentials are sent only when a username or API key is configured:
        e621ng authenticates with HTTP Basic username and API key, and an
        anonymous client sends no Authorization header.
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
        result = self._request("{}/{}".format(self.site_url, path), path,
                               request_args, method)
        if envelope is None:
            return result
        return result[envelope]
