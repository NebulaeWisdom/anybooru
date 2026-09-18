# -*- coding: utf-8 -*-

"""
Anybooru

Anybooru is an API client for Danbooru, Moebooru, Serika, e621ng, Zerochan and
Gelbooru based sites.

Anybooru requires "requests" package to work.

Anybooru modules:
    anybooru -- Contains the shared transport base class.
    moebooru -- Contains Moebooru main class.
    danbooru -- Contains Danbooru main class.
    serika -- Contains Serika main class.
    e621 -- Contains E621 main class for e621ng sites.
    zerochan -- Contains Zerochan main class.
    gelbooru -- Contains Gelbooru main class.
    api_moebooru -- Contains all Moebooru API functions.
    api_danbooru -- Contains all Danbooru API functions.
    api_serika -- Contains official v1 and internal Serika API functions.
    api_e621 -- Contains native e621ng API functions.
    api_zerochan -- Contains native Zerochan API functions.
    api_gelbooru -- Contains native Gelbooru API functions.
    exceptions -- Manages and builds Anybooru errors messages.
    resources -- Packaged default parameters (DEFAULT_CONFIG_FILE) and encoding.
"""

__version__ = "0.1.0.dev1"
__license__ = "MIT"
__source_url__ = "https://github.com/NebulaeWisdom/anybooru"
__author__ = "NebulaeWisdom <rezerols[at]gmail[dot]com>"

# anybooru imports
from .moebooru import Moebooru
from .danbooru import Danbooru
from .serika import Serika
from .e621 import E621
from .zerochan import Zerochan
from .gelbooru import Gelbooru
from .exceptions import (AnybooruError, AnybooruAPIError, AnybooruHTTPError)
from .resources import DEFAULT_CONFIG_FILE
