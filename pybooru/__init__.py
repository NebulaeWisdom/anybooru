# -*- coding: utf-8 -*-

"""
Pybooru

Pybooru is an API client for Danbooru, Moebooru and Serika based sites.

Pybooru requires "requests" package to work.

Pybooru modules:
    pybooru -- Main module of Pybooru, contains Pybooru class.
    moebooru -- Contains Moebooru main class.
    danbooru -- Contains Danbooru main class.
    serika -- Contains Serika main class.
    api_moebooru -- Contains all Moebooru API functions.
    api_danbooru -- Contains all Danbooru API functions.
    api_serika -- Contains official v1 and internal Serika API functions.
    exceptions -- Manages and builds Pybooru errors messages.
    resources -- Packaged default parameters (DEFAULT_CONFIG_FILE) and encoding.
"""

__version__ = "5.0.0.dev1"
__license__ = "MIT"
__source_url__ = "https://github.com/LuqueDaniel/pybooru"
__author__ = "Daniel Luque <danielluque14[at]gmail[dot]com>"

# pybooru imports
from .moebooru import Moebooru
from .danbooru import Danbooru
from .serika import Serika
from .exceptions import (PybooruError, PybooruAPIError, PybooruHTTPError)
from .resources import DEFAULT_CONFIG_FILE
