"""Anonymous Gelbooru 0.2 client, observed on TBIB.

Other Gelbooru 0.2 deployments have not been checked. This is separate from
Gelbooru's current JSON-only contract at gelbooru.com.
"""

from .api_gelbooru02 import Gelbooru02Api_Mixin
from .anybooru import _Anybooru


class Gelbooru02(_Anybooru, Gelbooru02Api_Mixin):
    """Read JSON posts and unchanged XML text without format detection."""

    def __init__(self, site_name=None, site_url=None, proxies=None, *,
                 config_file=None, timeout=None, user_agent=None):
        super().__init__(site_name, site_url, "", proxies,
                         config_file=config_file, timeout=timeout,
                         user_agent=user_agent)

    def _request_xml(self, url, api_call, request_args):
        return self._send(url, api_call, request_args, "GET").text

    def request(self, page, *, params=None, response_format="xml"):
        """GET one dispatcher page with an explicit response format.

        ``response_format='xml'`` returns ``response.text`` unchanged,
        including the declaration, root, attributes and whitespace. It does
        not parse or validate XML. ``response_format='json'`` adds ``json=1``
        and returns the complete decoded JSON using the shared transport.
        No Content-Type detection, XML-to-JSON conversion or fallback occurs.

        HTTP errors are raised before decoding; ``last_call`` preserves the
        actual URL, status and headers. Neither credentials, retries, local
        parameter limits nor automatic pagination are added.
        """
        request_params = dict(params or {}, page=page)
        if response_format == "json":
            request_params["json"] = 1
        send = {"xml": self._request_xml, "json": self._request}[response_format]
        return send("{}/index.php".format(self.site_url), page,
                    {"params": request_params})
