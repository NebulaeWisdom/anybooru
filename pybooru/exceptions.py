"""Errors returned by the HTTP and JSON API layers."""


class PybooruError(Exception):
    """Base exception for Pybooru errors."""


class PybooruHTTPError(PybooruError):
    """An unsuccessful HTTP response, including its original body."""

    def __init__(self, response):
        self.response = response
        self.http_code = response.status_code
        self.url = response.url
        self.body = response.text
        try:
            self.data = response.json()
        except ValueError:
            self.data = None
        super().__init__("{} {}: {} - URL: {}".format(
            self.http_code, response.reason, self.body, self.url))


class PybooruAPIError(PybooruError):
    """A successful HTTP response that cannot be decoded as JSON."""

    def __init__(self, message, response=None):
        self.response = response
        super().__init__(message)
