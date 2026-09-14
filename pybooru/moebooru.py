# -*- coding: utf-8 -*-

"""pybooru.moebooru

This module contains Moebooru class for access to API calls,
authentication, build url and return JSON response.

Classes:
   Moebooru -- Moebooru classs.
"""

# __furute__ imports
from __future__ import absolute_import

# External imports
import hashlib

# Pybooru imports
from .pybooru import _Pybooru
from .api_moebooru import MoebooruApi_Mixin
from .exceptions import PybooruError


class Moebooru(_Pybooru, MoebooruApi_Mixin):
    """Moebooru class (inherits: Pybooru and MoebooruApi_Mixin).

    Named sites and request settings come from the explicit JSON config_file.
    To use an unlisted site, provide site_url and api_version. Authentication
    uses username, password and the site's hash_string. Explicit constructor
    arguments override the matching configuration values.

    Attributes:
        site_name (str): Get or set site name set.
        site_url (str): Get or set the URL of Moebooru/Danbooru based site.
        api_version (str): Version of Moebooru API.
        username (str): Return user name.
        password (str): Return password in plain text.
        hash_string (str): Return hash_string of the site.
        last_call (dict) last call.
    """

    def __init__(self, site_name=None, site_url=None, username=None, password=None,
                 hash_string=None, api_version=None, proxies=None, *,
                 config_file="pybooru.json", timeout=None, user_agent=None):
        """Initialize Moebooru.

        Keyword arguments:
            site_name (str): Get or set site name set.
            site_url (str): Get or set the URL of Moebooru/Danbooru based site.
            api_version (str): Version of Moebooru API.
            hash_string (str): String that is hashed (required to login).
                               (See the API documentation of the site for more
                               information).
            username (str): Your username of the site (Required only for
                             functions that modify the content).
            password (str): Your user password in plain text (Required only
                            for functions that modify the content).
            config_file (str): Project JSON parameter file.
            timeout (float or tuple): Request timeout override.
            user_agent (str): HTTP User-Agent override.
            proxies (dict): Explicit requests proxy mapping override.
        """
        super(Moebooru, self).__init__(
            site_name, site_url, username, proxies, config_file=config_file,
            timeout=timeout, user_agent=user_agent)

        self.api_version = (self.site_settings['api_version']
                            if api_version is None else api_version).lower()
        self.hash_string = (self.site_settings['hash_string']
                            if hash_string is None and site_name else hash_string)
        self.password = (self.site_settings['password']
                         if password is None and site_name else password)
        self.password_hash = None


    def _build_url(self, api_call):
        """Build request url.

        Parameters:
            api_call (str): Base API Call.

        Returns:
            Complete url (str).
        """
        if self.api_version in ('1.13.0', '1.13.0+update.1', '1.13.0+update.2'):
            if '/' not in api_call:
                return "{0}/{1}/index.json".format(self.site_url, api_call)
        return "{0}/{1}.json".format(self.site_url, api_call)

    def _build_hash_string(self):
        """Function for build password hash string.

        Raises:
            PybooruError: When isn't provide hash string.
            PybooruError: When aren't provide username or password.
            PybooruError: When Pybooru can't add password to hash strring.
        """
        # Build AUTENTICATION hash_string
        # Check if hash_string exists
        if self.hash_string:
            if self.username and self.password:
                try:
                    hash_string = self.hash_string.format(self.password)
                except TypeError:
                    raise PybooruError("Pybooru can't add 'password' "
                                       "to 'hash_string'")
                # encrypt hashed_string to SHA1 and return hexdigest string
                self.password_hash = hashlib.sha1(
                    hash_string.encode('utf-8')).hexdigest()
            else:
                raise PybooruError("Specify the 'username' and 'password' "
                                   "parameters of the Pybooru object, for "
                                   "setting 'password_hash' attribute.")
        else:
            raise PybooruError(
                "Specify the 'hash_string' parameter of the Pybooru"
                " object, for the functions that requires login.")

    def _get(self, api_call, params, method='GET', file_=None):
        """Function to preapre API call.

        Parameters:
            api_call (str): API function to be called.
            params (dict): API function parameters.
            method (str): (Defauld: GET) HTTP method 'GET' or 'POST'
            file_ (file): File to upload.
        """
        url = self._build_url(api_call)

        if method == 'GET':
            request_args = {'params': params}
        else:
            if self.password_hash is None:
                self._build_hash_string()

            # Set login
            params['login'] = self.username
            params['password_hash'] = self.password_hash
            request_args = {'data': params, 'files': file_}

        # Do call
        return self._request(url, api_call, request_args, method)
