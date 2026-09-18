"""Configured client for e-shuushuu's standalone REST API."""

from urllib.parse import urlencode

from .api_shuushuu import ShuushuuApi_Mixin
from .anybooru import _Anybooru
from .resources import json_params


class Shuushuu(_Anybooru, ShuushuuApi_Mixin):
    """Read public JSON anonymously; authenticate only on an explicit call.

    Configured username/password never trigger login. A supplied access_token
    is sent as Bearer; login and refresh helpers update it and retain the
    session's cookies. There is no automatic refresh or request retry.
    """

    def __init__(self, site_name=None, site_url=None, username=None,
                 password=None, access_token=None, proxies=None, *,
                 config_file=None, timeout=None, user_agent=None):
        super().__init__(site_name, site_url, username, proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)
        self.password = (self.site_settings["password"]
                         if password is None and site_name else password)
        self.access_token = (self.site_settings["access_token"]
                             if access_token is None and site_name else access_token)

    def request(self, method, path, *, params=None, data=None, files=None):
        """Call a site-relative JSON route, including its ``api/v1`` prefix.

        Flat query sequences repeat their key (status=1&status=2), not Rails
        bracket notation. CSV filters such as tags must be strings ('46,169').
        Booleans become true/false; None query values are omitted. Search,
        pagination and limits are sent exactly as supplied, never filled in.
        data is JSON unless files is supplied, when it is multipart form data.

        The entire JSON response is returned, including pagination metadata.
        Shared HTTP errors, JSON errors and last_call retain the actual server
        response. Atom feeds, media and redirect-only routes are not JSON.
        """
        path = path.lstrip("/")
        url = "{}/{}".format(self.site_url, path)
        if params is not None:
            query = urlencode([
                (key, str(item).lower() if isinstance(item, bool) else item)
                for key, value in params.items()
                for item in (value if isinstance(value, (list, tuple)) else (value,))
                if item is not None
            ])
            if query:
                url += "?" + query
        request_args = {}
        if self.access_token:
            request_args["headers"] = {"Authorization": "Bearer " + self.access_token}
        if files is None:
            request_args["json"] = json_params(data)
        else:
            request_args.update(data=data, files=files)
        return self._request(url, path, request_args, method)

    def auth_login(self, username=None, password=None):
        """Explicitly POST JSON username/password and retain token + cookies.

        None selects the configured credential; an empty string stays empty.
        Returns TokenResponse (access_token, token_type, expires_in, user).
        This account-changing route has not been exercised by this project.
        """
        result = self.request("POST", "api/v1/auth/login", data={
            "username": self.username if username is None else username,
            "password": self.password if password is None else password,
        })
        self.access_token = result["access_token"]
        return result

    def auth_refresh(self):
        """Explicitly rotate the session's refresh cookie and retain access_token.

        No refresh token is supplied in JSON. Returns TokenResponse; requires
        a refresh cookie previously received by this client's session.
        """
        result = self.request("POST", "api/v1/auth/refresh")
        self.access_token = result["access_token"]
        return result

    def auth_me(self):
        """Read the authenticated user's information from auth/me (JSON object)."""
        return self.request("GET", "api/v1/auth/me")

    def auth_logout(self):
        """Revoke the current refresh token; clear local token/cookies on success.

        Returns the server's message object. The server-issued access token
        itself remains valid until expiry; clearing it here is local state.
        """
        result = self.request("POST", "api/v1/auth/logout")
        self.access_token = ""
        self.client.cookies.clear()
        return result

    def auth_logout_all(self):
        """Revoke all account refresh tokens; clear local auth state on success.

        Requires authentication and affects all devices. Returns the server's
        message object. No automatic login, logout or token revocation occurs.
        """
        result = self.request("POST", "api/v1/auth/logout-all")
        self.access_token = ""
        self.client.cookies.clear()
        return result
