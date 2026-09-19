"""Native methods for Cosine Gallery (pic.cosine.ren).

Cosine Gallery is the image site of a Telegram channel, not one of the booru
engines this package ships for: it is a Next.js application with its own
routes, envelopes, identifiers and error codes, so nothing here reuses a
booru parameter name, default or field list. The routes below and the field
lists in their docstrings come from anonymous read responses captured on the
day recorded in ``docs/verification.md`` plus the site's public frontend
sources for the route shape. They describe those samples rather than a
schema, so a key can be missing or move and no number here is a contract.

Shared observed facts:
    * Base URL: ``https://pic.cosine.ren``. The JSON routes sit under
      ``/api``; ``feed.xml`` is the one route of this family that answers
      something other than JSON.
    * Four response envelopes, none of which is unwrapped locally: the
      superjson ``{"json": ..., "meta": ...}`` of ``/api/artwork/{id}`` and
      ``/api/random``, the ``{"images": [...], "total": N}`` and
      ``{"artists": [...], "total": N, "hasNextPage": ...}`` listings of
      ``/api/list``, ``/api/artist`` and ``/api/artists``, the
      ``{"success": true, "data": {...}}`` wrapper of the search routes, and
      a bare array for ``/api/tag`` and ``/api/tags``.
    * ``meta`` holds superjson's type map. Its ``values`` keys are bare
      field names for a single object (``userid``, ``create_time``,
      ``authorid`` in the samples) and index-prefixed for an array
      (``0.userid``, ``1.create_time``), where the samples also carried
      ``referentialEqualities``, so no fixed set of keys can be assumed.
    * The artwork ``id`` is the site's row identifier, not the upstream
      ``pid``. Samples have separate ``userid``/``username`` and
      ``author``/``authorid`` fields; their upstream meanings are described
      in the contract notes.
    * ``tags`` is a list of strings on every observed route, its entries can
      repeat (the detail sample carried eight entries over four distinct
      values), and the routes disagree on the leading ``#``, which is kept
      as stored. A caller matching tags should strip ``#`` itself.
    * Errors are the site's own and are kept as they arrive: ``/api/tag``
      without ``tag`` answered 400 ``{"error": "标签参数缺失"}``,
      ``/api/artist`` without ``platform`` answered 400, an unknown artwork
      answered 404, and a non-numeric path segment answered 500 rather than
      400. Nothing is retried, rewritten or repaired, and a 200 with an
      empty list is a normal answer.
    * No method of this family fetches media bytes: ``rawurl`` and
      ``thumburl`` are returned as received, and the rules for requesting
      them are documentation, not code. The client also sends no write
      request on its own; the two POST routes exist as methods and were
      never called by this project.
    * The sampled responses carried no ``Access-Control-Allow-Origin`` for
      the ``Origin`` sent and no ``RateLimit-*`` header, so no quota is
      promised here.

Which calls have actually been made against the live site is recorded in
``docs/verification.md``.

Classes:
    CosineApi_Mixin -- Cosine Gallery artwork, tag, artist, search and feed
        methods, plus the two POST routes this project never called.
"""

# Standard library imports
from urllib.parse import quote


class CosineApi_Mixin:
    """Cosine Gallery methods, each a thin ``Cosine.request()`` call."""

    # ------------------------------------------------------------------
    # Artworks
    # ------------------------------------------------------------------

    def image_list(self, **params):
        """List artworks (``GET api/list``).

        ``params`` is forwarded unchanged; the route's own names are ``page``
        (1-based) and ``pageSize``, and neither is filled in here, so the
        site's defaults apply when they are absent. The page number is
        entirely the caller's: ``page=0`` and ``page=-1`` each answered 500
        in the samples while a page past the end answered 200 with an empty
        ``images``.

        Observed envelope: ``{"images": [...], "total": N}``, with ``total``
        the site's count and each entry an artwork object carrying ``id``,
        ``pid``, ``userid``, ``username``, ``author``, ``authorid``,
        ``platform``, ``title``, ``page``, ``filename``, ``extension``,
        ``rawurl``, ``thumburl``, ``width``, ``height``, ``create_time``,
        ``size``, ``guest``, ``r18``, ``ai`` and ``tags``. Two of those
        fields drift between rows rather than describing the media: the
        newer sample rows carried ``size`` null and ``guest`` false while
        the older ``artwork_show`` sample carried a numeric size and
        ``guest`` true. These are samples, not constant field values.
        Nothing here sorts, filters or de-duplicates the page.
        """
        return self.request("GET", "api/list", params=params)

    def artwork_show(self, artwork_id):
        """Read one artwork (``GET api/artwork/{artwork_id}``).

        The identifier is percent-encoded as one path segment with no safe
        characters and sent unvalidated, so a non-numeric value reaches the
        site and its own status is kept: ``abc`` answered 500, not 400, and
        a number with no row answered 404.

        Observed body: the superjson envelope ``{"json": {...}, "meta":
        {...}}``, the artwork object sitting in ``json`` and the type map in
        ``meta``. The object repeats the ``image_list`` fields and adds no
        media helper: the detail sample carried no ``originUrl`` or
        ``authorUrl``, which only ``image_random`` adds. ``tags`` is the
        stored list, so it can repeat values and keep a leading ``#``: the
        sample of artwork 1 held eight entries covering four distinct tags.
        """
        return self.request(
            "GET", "api/artwork/{}".format(quote(str(artwork_id), safe="")))

    def image_random(self, **params):
        """Read random artworks (``GET api/random``).

        ``params`` is forwarded unchanged; the route's own name is
        ``count``. The body's shape follows the count and this client does
        not normalize it: ``count=1`` answered a ``json`` object while
        ``count=3`` and ``count=100`` answered a ``json`` array, and the
        site clamps rather than the client -- ``count=0`` and ``count=-5``
        came back in the single-object form, and ``count=100`` came back
        with 20 objects. A non-numeric ``count`` answered 404.

        The envelope is the superjson one of ``artwork_show``, and for an
        array its ``meta.values`` keys are index-prefixed. Each object adds
        ``originUrl`` and ``authorUrl`` to the artwork fields, and the
        sample rewrote the ``i.pximg.net`` host of ``rawurl``/``thumburl``
        to ``piv.cosine.ren``; both are returned as received, so the two
        routes' URLs for the same artwork need not match.
        """
        return self.request("GET", "api/random", params=params)

    def artwork_revalidate(self, artwork_id, *, secret=None):
        """Submit one artwork for revalidation (``POST api/artwork/revalidate``).

        This project never sent this request, so the successful body, the
        unknown-artwork status and the answer to a wrong secret are all
        unverified; what is written here is the request the site's own
        frontend builds. The JSON body is ``{"artworkId": artwork_id,
        "secret": secret}``. ``secret=None`` uses the client's
        ``revalidate_secret``, an explicit ``secret`` wins over it, and an
        empty secret is still sent unchanged: whether it is accepted is the
        site's decision, not a local check, so no error is raised here for a
        missing credential. The secret never becomes a request header, no
        other route receives it, and the call is not retried or pre-checked.

        ``artwork_id`` travels in the body as given and is not encoded into
        the path, so a non-numeric value is the site's problem to reject.
        """
        data = {
            "artworkId": artwork_id,
            "secret": (self.revalidate_secret if secret is None else secret),
        }
        return self.request("POST", "api/artwork/revalidate", data=data)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_images(self, tag, **params):
        """List one tag's artworks (``GET api/tag``).

        ``tag`` is required and is sent as the query name ``tag``. The value
        is matched against the stored tag: the sample of ``GenshinImpact``
        returned rows, and a lowercase spelling ``genshinimpact`` returned
        rows too, while ``#GenshinImpact`` and the comma-joined
        ``原神,GenshinImpact`` each answered an empty array. A tag no row
        carries also answered 200, so an empty array is how this route ends
        and how a miss looks, and omitting ``tag`` altogether answered 400
        ``{"error": "标签参数缺失"}``.

        The body is a bare array of the artwork objects ``image_list``
        returns, with no envelope and no ``total``: its length is the page
        size, not the number of matching artworks. ``params`` is forwarded
        unchanged; the route's own names are ``start`` (the offset) and
        ``limit``, and ``start=2&limit=2`` answered rows further down the
        list, so the offset is honoured as given.
        """
        return self.request("GET", "api/tag", params=dict(params, tag=tag))

    def tag_list(self):
        """List every tag with the site's count (``GET api/tags``).

        The body is a bare array, with no envelope and no ``total``, of
        ``{"tag": ..., "count": ...}`` objects; the sample held 2128 rows
        and carried no ``#`` prefix. ``count`` is the site's own tag-row
        figure -- the published route source groups the image-tag rows by
        tag and counts those rows after stripping a leading ``#`` -- so it
        is not the number of artworks ``tag_images`` returns for the same
        string and neither value can be converted into the other. The list
        is returned as received: it is not paged, sorted, filtered or
        joined with other routes to turn ``count`` into an artwork count.
        """
        return self.request("GET", "api/tags")

    # ------------------------------------------------------------------
    # Artists
    # ------------------------------------------------------------------

    def artist_images(self, platform, authorid, **params):
        """List an artist's artworks or the artist record (``GET api/artist``).

        ``platform`` and ``authorid`` are both required and are sent as
        those query names, with ``authorid`` a string (the sample used
        ``'54390221'``). Omitting ``platform`` answered 400 and a
        non-numeric ``authorid`` answered 500, so neither is checked here.

        One route answers two shapes: with ``infoOnly`` absent or ``1``
        the sampled body is ``{"images": [...], "total": N}``, while
        ``infoOnly='true'`` answers a bare artist object
        ``{"author": ..., "authorid": ..., "platform": ...,
        "artworkCount": ...}`` with no envelope at all, and an artist with
        no artwork answered 404 on that branch. The two are not
        interchangeable: the record's ``author`` differed from the list's
        ``author`` for the same artist in the sample, so this client
        forwards ``infoOnly`` as given and merges nothing.

        ``params`` is forwarded unchanged; the list branch's other names
        are ``page`` and ``pageSize``.
        """
        return self.request("GET", "api/artist",
                            params=dict(params, platform=platform,
                                        authorid=authorid))

    def artist_list(self, **params):
        """List artists (``GET api/artists``).

        Observed envelope: ``{"artists": [...], "total": N,
        "hasNextPage": ...}``, which no other listing route of this family
        uses. Each artist object carried ``platform``, ``authorid``,
        ``author``, ``artworkCount``, ``latestImageThumb``,
        ``latestImageFilename``, ``lastUpdateTime``,
        ``latestImageWidth`` and ``latestImageHeight``, so one row already
        points at a preview address -- returned as received, never fetched.
        The sample answered ``total`` 1708 with ``hasNextPage`` true for a
        two-row page.

        ``params`` is forwarded unchanged; the route's own names are
        ``page``, ``pageSize`` and ``sortBy``. ``sortBy`` was tried with
        ``artworks``, ``random`` and ``lastUpdate``, and an unrecognized
        ``unknown`` answered 200 like the rest, so the value is the site's
        to interpret and this client neither validates nor translates it.
        ``hasNextPage`` is passed through unread.
        """
        return self.request("GET", "api/artists", params=params)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, **params):
        """Search the artwork index (``GET api/search``).

        Observed envelope: ``{"success": true, "data": {...}}`` whose
        ``data`` holds ``hits``, ``query``, ``total``, ``limit``,
        ``offset`` and ``processingTimeMs``. A hit is not the artwork
        object the list routes return: it carries ``id`` as a string,
        ``author``, ``platform``, ``tags`` (a list of strings),
        ``pid``, ``authorid``, ``width``, ``height``, ``filename``,
        ``thumburl``, ``rawurl``, ``create_time``, ``r18``, ``ai``, the
        indexed text ``searchable_content`` and a ``_formatted`` copy of
        itself, whose values carry Meilisearch's ``<em>`` highlights and
        whose numeric fields are strings, while it has no ``userid``,
        ``username``, ``page``, ``size``, ``guest`` or ``extension``.
        ``title`` was present in some hits and absent from another live
        result. Neither missing fields nor formatted values are filled in.

        ``params`` is forwarded unchanged; the route's own names are ``q``,
        ``limit``, ``offset``, ``platform``, ``tags``, ``r18`` and ``sort``,
        where ``sort`` takes a Meilisearch expression such as
        ``'create_time:desc'``. The site's own limits show through and this
        client applies none of its own: an empty ``q`` matched the whole
        index and reported ``total`` 1000, ``offset=100000`` came back as
        ``offset`` 1000 with no hits, and ``limit=-1``, ``offset=-5`` and
        ``sort=bogus`` each answered 500. ``total`` is therefore an
        estimate the site caps and not a row count, and it must not be
        paged through as though it were.
        """
        return self.request("GET", "api/search", params=params)

    def search_suggestions(self, **params):
        """Read search-box suggestions (``GET api/search/suggestions``).

        Observed envelope: ``{"success": true, "data": {"suggestions":
        [...], "query": ...}}``, each suggestion a ``{"text": ...,
        "type": ...}`` object whose ``type`` was ``'general'`` in the
        samples. ``params`` is forwarded unchanged; the route's own
        names are ``q`` and ``limit``.

        The short-query cutoff and the page size are the site's: ``q=a``
        answered an empty ``suggestions`` list with 200, ``q=miku``
        answered 10 entries and ``q=miku&limit=50`` answered 15, so the
        client neither pads a short ``q`` nor counts what comes back.
        """
        return self.request("GET", "api/search/suggestions", params=params)

    def search_index_status(self):
        """Read the index report (``GET api/search/admin``).

        This GET changes nothing; it is the read side of the route whose
        POST sibling is ``search_index_admin``. Observed body:
        ``{"success": true, "data": {...}}`` with ``totalImages``,
        ``indexedImages``, ``indexHealth`` and ``lastSyncTime``; the sample
        reported 4953 images, 3353 indexed and ``indexHealth`` "partial".
        The sample caller was anonymous, so no credential was needed for
        this read. Every value is returned as received: nothing here
        computes a backlog, caches the answer or interprets the health
        string.
        """
        return self.request("GET", "api/search/admin")

    def search_index_admin(self, action, **params):
        """Change the site's search index (``POST api/search/admin``).

        **This writes to the live site.** The route rebuilds, initializes or
        deletes the search index of ``pic.cosine.ren`` depending on the
        action; the read side of the same path answered an anonymous caller
        here and the sources this project read describe the POST as carrying
        no authentication either. This project has never sent this request,
        so no response and no permission check of the write route is
        verified. Call it only if you are entitled to change that site's
        index; nothing here asks for confirmation, checks a permission,
        offers a dry run or undoes the call afterwards.

        ``action`` is required and becomes the JSON body's ``action``; the
        action names the site's own code uses are ``initialize``,
        ``index_all``, ``sync_recent``, ``rebuild`` and ``validate``, and no
        value is validated here, so an unknown one is still sent. ``params``
        such as ``batchSize`` and ``hours`` are merged into the same JSON
        object and forwarded unchanged, so the caller writes whichever of
        them the action takes. The response is returned as sent -- a 2xx
        means the site accepted the request, not that the index ends up in
        the state the caller expects, which is another reason to read
        ``search_index_status`` afterwards.
        """
        return self.request("POST", "api/search/admin",
                            data=dict(params, action=action))

    # ------------------------------------------------------------------
    # Feed
    # ------------------------------------------------------------------

    def feed(self):
        """Read the site feed (``GET feed.xml``) as unchanged XML text.

        This is the one method of the family that does not answer JSON: it
        asks ``Cosine.request`` for ``response_format='xml'``, so the whole
        response text -- declaration, root element, whitespace and all -- is
        returned and never parsed, validated or converted.

        The sample response was RSS 2.0 as ``application/xml;
        charset=utf-8`` with 20 items, and its ``lastBuildDate`` and item
        ids (3290, 3288, 3289) did not match the newest rows of
        ``image_list``; the feed is therefore not a view of the current 20
        artworks and this client does not treat it as one, builds no item
        count and follows no link from it.
        """
        return self.request("GET", "feed.xml", response_format="xml")
