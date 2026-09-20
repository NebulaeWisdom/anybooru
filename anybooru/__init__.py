# -*- coding: utf-8 -*-

"""
Anybooru

Anybooru is an API client for Danbooru, Moebooru, Serika, e621ng, Zerochan,
Gelbooru, e-shuushuu, Gelbooru 0.2 based sites, Sakuria, Anime-Pictures,
Cosine and nhentai APIs.

Anybooru requires "requests" package to work.

Anybooru modules:
    anybooru -- Contains the shared transport base class.
    moebooru -- Contains Moebooru main class.
    danbooru -- Contains Danbooru main class.
    serika -- Contains Serika main class.
    e621 -- Contains E621 main class for e621ng sites.
    zerochan -- Contains Zerochan main class.
    gelbooru -- Contains Gelbooru main class.
    shuushuu -- Contains Shuushuu main class.
    gelbooru02 -- Contains Gelbooru02 main class for Gelbooru 0.2 sites.
    sakuria -- Contains Sakuria main class for the Sakuria API.
    anime_pictures -- Contains AnimePictures main class.
    cosine -- Contains Cosine main class.
    nhentai -- Contains Nhentai main class for the nhentai API.
    api_moebooru -- Contains all Moebooru API functions.
    api_danbooru -- Contains all Danbooru API functions.
    api_serika -- Contains official v1 and internal Serika API functions.
    api_e621 -- Contains native e621ng API functions.
    api_zerochan -- Contains native Zerochan API functions.
    api_gelbooru -- Contains native Gelbooru API functions.
    api_shuushuu -- Contains native e-shuushuu API functions.
    api_gelbooru02 -- Contains native Gelbooru 0.2 API functions.
    api_sakuria -- Contains native Sakuria API functions.
    api_anime_pictures -- Contains native Anime-Pictures API functions.
    api_cosine -- Contains native Cosine Gallery API functions.
    api_nhentai -- Contains native nhentai API functions.
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
from .shuushuu import Shuushuu
from .gelbooru02 import Gelbooru02
from .sakuria import Sakuria
from .anime_pictures import AnimePictures
from .cosine import Cosine
from .nhentai import Nhentai
from .exceptions import (AnybooruError, AnybooruAPIError, AnybooruHTTPError)
from .resources import DEFAULT_CONFIG_FILE
