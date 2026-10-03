"""Native methods for Wallhaven (wallhaven.cc, API v1).

Wallhaven is a wallpaper site of its own rather than one of the booru engines
this package ships for: its read API lives under ``/api/v1`` on the site
root, it takes the account key as an ``apikey`` query value (or as an
``X-API-Key`` header, which a caller can add through ``Wallhaven.request``'s
``headers``), and it returns the ``{"data": ...}`` detail bodies and
``{"data": [...], "meta": {...}}`` listings the site's own API page
describes under its ``#wallpapers``, ``#search``, ``#tags`` and
``#user-settings`` (including "User Collections") headings. Nothing here
reuses a booru parameter name, default or field list. All seven methods are
GET reads; no method logs in, writes, retries or downloads media.

Shared observed facts:
    * Base URL: ``https://wallhaven.cc``. ``Wallhaven.request`` resolves
      every path under it with a leading slash stripped.
    * Every error body is a JSON object with one ``error`` string and the
      site's own status: 400 for an out-of-range request, 401
      ``{"error": "Unauthorized"}`` for NSFW without a valid key, for an
      invalid key and for the anonymous settings read, 404
      ``{"error": "Nothing here"}`` from a matched wallpaper, tag or
      collection route whose id has no row and from the anonymous
      own-collections read, 404 ``{"error": "Not Found"}`` from a route the
      site does not have, and 429 when the documented limit of 45 calls per
      minute is exceeded. Nothing is retried or rewritten here.
    * The listings return 24 entries per page. The search listing's
      ``meta`` reports ``current_page``, ``last_page``, ``per_page``,
      ``total``, ``query`` and ``seed``; the collection listing's ``meta``
      holds only the first four of those, with no ``query`` and no
      ``seed``. A 200 with an empty ``data`` is a normal answer: an
      ignored parameter still returns entries, and past the end the site has
      been observed to reuse a positive ``total``, so an empty array is not
      proof that a result set is exhausted.
    * The wallpaper summary carries ``id``, ``url``, ``short_url``,
      ``views``, ``favorites``, ``source``, ``purity``, ``category``,
      ``dimension_x``, ``dimension_y``, ``resolution``, ``ratio``,
      ``file_size``, ``file_type``, ``created_at``, ``colors`` and
      ``thumbs``. ``purity`` is one of ``sfw``/``sketchy``/``nsfw`` and
      ``category`` one of ``general``/``anime``/``people``. Media addresses
      (``path``, ``thumbs``, tag colors) are returned exactly as received;
      nothing is downloaded or rewritten.
    * There is no similar-wallpaper route and no user-profile route in API
      v1: similar wallpapers are a search (``q='like:<id>'``) and a user's
      uploads are a search (``q='@username'``). The client fabricates
      neither route.
    * The API page documents an ``apikey`` query value and an
      ``X-API-Key`` header. This client sends only the configured query
      value; the header form is reachable through ``headers`` and is never
      added on top automatically.

Which calls have actually been made against the live site is recorded in
``docs/verification.md``; the full per-method parameter and field reference
is ``docs/wallhaven-api.md``.

Classes:
    WallhavenApi_Mixin -- Wallhaven wallpaper, tag, collection and settings
        reads.
"""

# Standard library imports
from urllib.parse import quote


class WallhavenApi_Mixin:
    """Wallhaven API v1 reads, each a thin ``Wallhaven.request()`` call.

    Methods never fill query values, clamp, retry, log in or download media.
    """

    # ------------------------------------------------------------------
    # Wallpapers
    # ------------------------------------------------------------------

    def wallpaper_search(self, **params):
        """Search wallpapers (``GET api/v1/search``; the API page's
        "Searching and listings" section).

        ``params`` is forwarded unchanged; the site's own query names and
        values are:

        ``q``
            Free search text. A bare tag keyword is matched fuzzily, a
            leading ``-`` excludes it, ``+tag1 +tag2`` requires all of them,
            ``@username`` lists that account's uploads, ``id:123`` is an
            exact tag-id search that cannot be combined with another query
            part, ``type:png`` / ``type:jpg`` filters by file type, and
            ``like:<wallpaper_id>`` finds wallpapers with similar tags.
        ``categories``
            Three 0/1 flags for general, anime and people, e.g. ``'111'``
            (the default).
        ``purity``
            Three 0/1 flags for sfw, sketchy and nsfw, e.g. ``'100'`` (the
            default). Requesting an ``nsfw`` bit without a valid key answers
            401.
        ``sorting``
            ``date_added`` (default), ``relevance``, ``random``, ``views``,
            ``favorites`` or ``toplist``.
        ``order``
            ``desc`` (default) or ``asc``.
        ``topRange``
            ``1d``, ``3d``, ``1w``, ``1M`` (default), ``3M``, ``6M`` or
            ``1y``; used when ``sorting='toplist'``.
        ``atleast``
            Minimum resolution, e.g. ``'1920x1080'``.
        ``resolutions``
            One exact resolution, or several in one comma-separated string,
            e.g. ``'1920x1080,1920x1200'``.
        ``ratios``
            One aspect ratio, or several in one comma-separated string,
            e.g. ``'16x9,16x10'``.
        ``colors``
            One hex color without ``#``. The documented set of 29 is
            ``660000``, ``990000``, ``cc0000``, ``cc3333``, ``ea4c88``,
            ``993399``, ``663399``, ``333399``, ``0066cc``, ``0099cc``,
            ``66cccc``, ``77cc33``, ``669900``, ``336600``, ``666600``,
            ``999900``, ``cccc33``, ``ffff00``, ``ffcc33``, ``ff9900``,
            ``ff6600``, ``cc6633``, ``996633``, ``663300``, ``000000``,
            ``999999``, ``cccccc``, ``ffffff`` and ``424153``.
        ``page``
            1-based page number; the site returns 24 entries per page.
        ``seed``
            Six ``[a-zA-Z0-9]`` characters, the site's own seed for
            reproducible ``sorting='random'`` paging; it is also reported
            back in ``meta.seed``.

        Pass ``resolutions``, ``ratios`` and ``colors`` as literal
        comma-separated strings: a Python list would be encoded as repeated
        ``key[]`` query pairs, which is not the form this route takes.

        Response ``{"data": [...], "meta": {...}}``. Each ``data`` entry is
        the summary object described in the module docstring; ``meta``
        carries ``current_page``, ``last_page``, ``per_page``, ``total``,
        ``query`` (a string, ``null``, or an ``{"id", "tag"}`` object for an
        exact tag search) and ``seed`` (a string or ``null``).
        """
        return self.request("GET", "api/v1/search", params=params)

    def wallpaper_show(self, wallpaper_id, **params):
        """Read one wallpaper (``GET api/v1/w/{wallpaper_id}``; the API
        page's "Accessing Wallpaper information" section).

        ``wallpaper_id`` is the six-character site id, e.g. ``'pom5lj'``.
        It is percent-encoded as a single path segment with no safe
        characters and is not validated here, so an unknown id reaches the
        site and returns its own 404 ``{"error": "Nothing here"}``, while an
        NSFW wallpaper without a valid key returns 401.

        Response ``{"data": {...}}``: the search summary fields plus
        ``uploader`` (``username``, ``group`` and ``avatar`` with
        ``200px``, ``128px``, ``32px`` and ``20px`` addresses) and ``tags``,
        each tag carrying ``id``, ``name``, ``alias``, ``category_id``,
        ``category``, ``purity`` and ``created_at``. There is no separate
        similar route; use ``wallpaper_search(q='like:<wallpaper_id>')``.
        """
        return self.request("GET", "api/v1/w/{}".format(
            quote(str(wallpaper_id), safe="")))

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_show(self, tag_id, **params):
        """Read one tag (``GET api/v1/tag/{tag_id}``; the API page's
        "Tag info" section).

        ``tag_id`` is the numeric tag id; ``1`` is ``anime``. It is
        percent-encoded as a single path segment and is not validated here,
        so a number with no tag returns the site's 404.

        Response ``{"data": {...}}``: ``id``, ``name``, ``alias``,
        ``category_id``, ``category`` (e.g. ``'Anime & Manga'``),
        ``purity`` and ``created_at``.
        """
        return self.request("GET", "api/v1/tag/{}".format(
            quote(str(tag_id), safe="")))

    # ------------------------------------------------------------------
    # User settings
    # ------------------------------------------------------------------

    def user_settings(self, **params):
        """Read the authenticated account's settings
        (``GET api/v1/settings``; the API page's "User Settings" section).

        The route has no query parameters and needs a valid key, whether
        configured on the client or passed with ``headers`` for this call;
        anonymous and invalid-key reads answer 401
        ``{"error": "Unauthorized"}``.

        Response ``{"data": {...}}``: ``thumb_size``, ``per_page``, the
        enabled ``purity`` and ``categories`` lists, ``resolutions``,
        ``aspect_ratios``, ``toplist_range``, and the ``tag_blacklist`` and
        ``user_blacklist`` lists.
        """
        return self.request("GET", "api/v1/settings", params=params)

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    def collection_list(self, **params):
        """List the authenticated account's own collections
        (``GET api/v1/collections``; the API page's "User Collections"
        section).

        The route is scoped to the sent key's owner, so it needs one: the
        anonymous read answers 404 ``{"error": "Nothing here"}`` rather
        than 401. With a key it returns all of that account's collections,
        private ones included.

        Response ``{"data": [...]}``: each entry has ``id``, ``label``,
        ``views``, ``public`` (``1`` or ``0``) and ``count``.
        """
        return self.request("GET", "api/v1/collections", params=params)

    def user_collections(self, username, **params):
        """List a user's public collections
        (``GET api/v1/collections/{username}``).

        ``username`` is the site handle, percent-encoded as a single path
        segment and not validated here. Other users see only the public
        collections of that account; the owner's own listing, private
        collections included, is ``collection_list``.

        Response ``{"data": [...]}`` with the same entry fields as
        ``collection_list``.
        """
        return self.request("GET", "api/v1/collections/{}".format(
            quote(str(username), safe="")))

    def collection_wallpapers(self, username, collection_id, **params):
        """List a collection's wallpapers
        (``GET api/v1/collections/{username}/{collection_id}``).

        ``username`` and ``collection_id`` are percent-encoded as two path
        segments and are not validated here. A missing collection answers
        404 ``{"error": "Nothing here"}``, like a missing wallpaper or tag.

        Response ``{"data": [...], "meta": {...}}``: the entries are the
        same summary objects as ``wallpaper_search``, but ``meta`` is
        smaller and holds only ``current_page``, ``last_page``, ``per_page``
        and ``total`` -- it has no ``query`` and no ``seed`` field, so a
        caller cannot read those two keys from this route even though
        ``wallpaper_search`` provides them. Only ``purity`` is available
        among the search parameters. A key lets the owner read a private
        collection; another user only sees public ones.
        """
        return self.request("GET", "api/v1/collections/{}/{}".format(
            quote(str(username), safe=""),
            quote(str(collection_id), safe="")))
