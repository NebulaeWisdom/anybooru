"""Configured JSON client for sites running the Moebooru engine."""

import hashlib

from .api_moebooru import MoebooruApi_Mixin
from .anybooru import _Anybooru


class Moebooru(_Anybooru, MoebooruApi_Mixin):
    """Access Moebooru routes with Rails forms and password-hash auth."""

    def __init__(self, site_name=None, site_url=None, username=None, password=None,
                 hash_string=None, api_version=None, proxies=None, *,
                 config_file=None, timeout=None, user_agent=None):
        super().__init__(site_name, site_url, username, proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.api_version = (self.site_settings["api_version"]
                            if api_version is None else api_version).lower()
        self.hash_string = (self.site_settings["hash_string"]
                            if hash_string is None and site_name else hash_string)
        self.password = (self.site_settings["password"]
                         if password is None and site_name else password)
        self.password_hash = (hashlib.sha1(
            self.hash_string.format(self.password).encode("utf-8")).hexdigest()
            if self.username or self.password else None)

    def request(self, method, path, *, params=None, data=None, files=None):
        """Call a relative JSON route using query parameters and Rails forms.

        `params` is the query string; `data` is the form body. Nested mappings
        become Rails bracket parameters. `files` uses requests' file mapping
        or list of (field, file) pairs; callers own the open file handles.
        None values are omitted. Authentication, when configured, is sent on
        reads as query fields and on writes as form fields, never HTTP Basic.
        Bare collection paths use /index on the configured legacy versions;
        explicit action paths are unchanged. The client appends .json, returns
        decoded JSON (or None for an empty success), and leaves permissions,
        input validation and optional site capabilities to the server.
        """
        method = method.upper()
        path = path.lstrip("/")
        if path.endswith(".json"):
            path = path[:-5]
        if "/" not in path and self.api_version in (
                "1.13.0", "1.13.0+update.1", "1.13.0+update.2"):
            path += "/index"
        path += ".json"
        request_args = {"params": params, "data": data, "files": files}
        if self.password_hash is not None:
            key = "params" if method in ("GET", "HEAD") else "data"
            request_args[key] = dict(request_args[key] or {},
                                     login=self.username,
                                     password_hash=self.password_hash)
        return self._request("{}/{}".format(self.site_url, path), path,
                             request_args, method)
