"""Shared configured HTTP transport for the supported engine families."""

import requests

from .exceptions import PybooruAPIError, PybooruHTTPError
from .resources import encode_params, load_config


class _Pybooru:
    """Load one parameter file and own one requests session.

    `config_file=None` selects the `pybooru.json` installed inside this
    package; any other value is used as the path of the file to load.
    """

    def __init__(self, site_name=None, site_url=None, username=None, proxies=None,
                 *, config_file=None, timeout=None, user_agent=None):
        self.config = load_config(config_file)
        self.site_settings = self.config["sites"][site_name] if site_name else {}
        settings = self.config["request"]
        self.site_name = site_name
        self.site_url = (self.site_settings["url"] if site_url is None
                         else site_url).rstrip("/")
        self.username = (self.site_settings["username"]
                         if username is None and site_name else username)
        self.proxies = settings["proxies"] if proxies is None else proxies
        self.timeout = settings["timeout"] if timeout is None else timeout
        if isinstance(self.timeout, list):
            self.timeout = tuple(self.timeout)
        self.client = requests.Session()
        self.client.trust_env = False
        self.client.headers.update({
            "User-Agent": settings["user_agent"] if user_agent is None else user_agent,
            "Accept": "application/json",
        })
        self.last_call = {}

    def close(self):
        """Release the connection pool."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _send(self, url, api_call, request_args, method):
        """Send HTTP, record the response, and preserve non-success bodies."""
        for key in ("params", "data"):
            if key in request_args:
                request_args[key] = encode_params(request_args[key])
        self.last_call = {}
        response = self.client.request(
            method, url, proxies=self.proxies, timeout=self.timeout, **request_args)
        self.last_call = {
            "API": api_call,
            "url": response.url,
            "status_code": response.status_code,
            "status": response.reason,
            "headers": response.headers,
        }
        if not 200 <= response.status_code < 300:
            raise PybooruHTTPError(response)
        return response

    def _request_bytes(self, url, api_call, request_args, method="GET"):
        """Return raw successful response bytes, without JSON decoding."""
        return self._send(url, api_call, request_args, method).content

    def _request(self, url, api_call, request_args, method="GET"):
        """Return JSON, or None for an empty successful response."""
        response = self._send(url, api_call, request_args, method)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise PybooruAPIError(
                "Invalid JSON response from {}: {}".format(response.url, error),
                response=response) from error
