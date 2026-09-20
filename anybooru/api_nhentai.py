"""Native JSON methods for nhentai (nhentai.net, API v2).

nhentai is a gallery site of its own rather than one of the booru engines
this package ships for: its routes, parameters, identifiers and JSON shapes
are its own. This family covers the JSON API of ``nhentai.net`` only. The
``.to`` clone has a different catalogue and response structure. The sampled
API paths on that host returned 404; that does not enumerate its route table.
Nothing here reaches that host, converts identifiers, or falls back to it.
Its embedded ``nh_id`` values include negative strings (-2 and -289), whose
meaning and mapping coverage have not been established.

The evidence for this family is the site's own OpenAPI document, fetched from
``GET https://nhentai.net/api/v2/openapi.json`` (``info.version``
``2.0.0+14bccf7``, OpenAPI 3.1.0, 98 paths, 114 operations, 129 schemas).
Every route below is one of that document's operations, and each docstring
reports the response fields and error statuses that document declares rather
than a response this project observed: a key it declares can still be absent
or move in a live body, a default it declares is the site's, and no count
here is a promise. An anonymous read-only probe run then called all 31 GET
routes below over HTTP: 25 answered 200 and 6 answered 401 without a
credential, and what that run saw is written into the docstrings as observed
values beside the declared ones. Where the two disagree -- a status the
document declares as 422 that the run saw as 400, or a parameter the site
ignored -- both are stated and neither is resolved locally.

The five remaining methods are a POST that only searches (``tag_search``) and
four that were never sent by this project: ``favorite_add``,
``favorite_remove`` and ``blacklist_update`` change the authenticated
account's lists and ``gallery_download`` allocates a short-lived download
URL. Which calls have actually been made against the live site is recorded in
docs/verification.md.

Shared facts declared by that document:

    * Base URL ``https://nhentai.net``. The JSON API sits under ``/api/v2``,
      so every native path below starts with ``api/v2/`` and the base URL of
      the client is the site root, not the API prefix. The document itself
      lives at ``api/v2/openapi.json`` and has no method here.
    * Authentication is a request header, ``Authorization: Key <api_key>``.
      The document's own description says to generate the key in the site's
      account settings and pass it that way, and it marks each operation
      "Public (no authentication required)", "Public (optional User Token or
      API Key for personalization)" or "User Token or API Key". The routes in
      the last group answer 401 to a caller without a credential. This
      client's configured credential is always of the ``Key`` form: it has no
      User Token parameter, builds no other authorization header and never
      refuses a call for lack of a credential. A caller who has a User Token
      can still pass it per call through ``headers``, which overrides the
      configured key; that path is the caller's, not something these methods
      do or check.
    * Two gallery bodies, and neither is reduced to the other. List routes
      answer an envelope of ``result`` (the gallery objects), ``num_pages``,
      ``per_page`` and ``total``; the detail route answers ``title``
      (``english``/``japanese``/``pretty``), ``cover`` and ``thumbnail``
      (``path``/``width``/``height``), ``scanlator``, ``upload_date``,
      ``tags``, ``num_pages``, ``num_favorites``, ``pages`` and the optional
      blocks ``comments``, ``comment_count``, ``related``, ``is_favorited``
      and ``suggestions``. A ``result`` entry carries ``id``, ``media_id``,
      ``english_title``, ``japanese_title``, ``thumbnail``,
      ``thumbnail_width``, ``thumbnail_height``, ``num_pages``,
      ``num_favorites``, ``tag_ids`` and ``blacklisted``. A tag carries
      ``id``, ``type``, ``name``, ``slug``, ``url``, ``count``,
      ``description``, ``is_community`` and ``pending_describe_id``.
    * ``path`` and ``thumbnail`` values are relative to a media server, and
      the document's cdn section asks callers to take a server from
      ``cdn_config`` and concatenate it, to use a returned path exactly as it
      is, and never to guess an extension, suffix or numbering. This client
      builds no media URL and downloads no file, so those values reach the
      caller as stored.
    * ``tag_type`` is a tag's class name. The document types the path segment
      as a free string and does not enumerate it; the classes it names
      elsewhere in the document are ``tag``, ``artist``, ``parody``,
      ``character``, ``group``, ``language`` and ``category``.
    * Errors are the site's own JSON: ``{"error": "..."}`` for the document's
      ``ErrorResponse``, the shape it declares on the failures the methods
      below describe (400, 401, 404, 429 and 503 among them), and
      ``{"detail": [...]}`` for its ``HTTPValidationError``, which it declares
      for 422. The probe run never saw a 422: the cases the document attributes
      to its validator -- an out-of-range ``page`` or ``per_page``, a missing
      search ``query``, a bad ``sort`` -- arrived as 400 with an ``error``
      string and a ``details`` array. The method docstrings say which status
      was declared and which was observed. Nothing is caught, retried,
      rewritten or repaired here.
    * Nothing is unwrapped, renamed, defaulted, clamped or paged locally: the
      JSON body is returned exactly as received, arrays and bare integers
      included. Identifiers are percent-encoded as single path segments with
      no safe characters.

The document's moderation operations, its taxonomy and GTS writes, its
first-party user and auth group (of which ``user_me`` is the one exception,
being a plain read of the configured account), its proof-of-work and captcha
routes and its ad-zone routes are not part of this family at all.

Classes:
    NhentaiApi_Mixin -- nhentai service, gallery, tag-suggestion, tag,
        taxonomy, comment, search, favorite, blacklist and user methods.
"""

# Standard library imports
from urllib.parse import quote


class NhentaiApi_Mixin:
    """nhentai API v2 methods, each a thin ``Nhentai.request()`` call."""

    # ------------------------------------------------------------------
    # Service
    # ------------------------------------------------------------------

    def service_info(self):
        """Read the API root (``GET api/v2``).

        Declared body (``ApiRootResponse``): ``version`` and ``message``,
        both strings. The document declares this route public, and the probe
        run's anonymous call answered 200 with those two keys (the version
        string being the API build the site reports), so this is a live check
        that the host serves API v2 at all. The path is the API prefix itself
        and has no trailing slash.
        """
        return self.request("GET", "api/v2")

    def cdn_config(self):
        """Read the media server lists (``GET api/v2/cdn``).

        Declared body (``CdnConfigResponse``): ``image_servers`` and
        ``thumb_servers``, each an array of server strings. A media URL is
        one of those servers concatenated with a ``path`` or ``thumbnail``
        value from a gallery body, which is why that value arrives relative.

        The document's cdn section asks callers to take a server from this
        answer rather than hardcode a subdomain, to use a returned path
        exactly as it is, and warns that a client which guesses paths or
        sustains rates far above normal browsing is eventually banned. This
        method returns the lists and fetches no media; public route, and the
        probe run's anonymous call answered 200 with four image servers and
        four thumbnail servers. The servers that answer today are not a
        permanent list: the document says it can change, so read it per run
        rather than storing it in code.
        """
        return self.request("GET", "api/v2/cdn")

    def site_config(self):
        """Read the site configuration (``GET api/v2/config``).

        Declared body (``ConfigResponse``): ``image_servers`` and
        ``thumb_servers`` (the same two arrays ``cdn_config`` returns) plus
        ``announcement``, which is either null or an object with ``message``
        (a string) and ``links`` (an array of ``{"text", "url"}`` objects).
        Public route; the probe run's anonymous call answered 200 with all
        three keys and ``announcement`` null, so a null announcement is a
        normal answer and not a failure -- this is the route to call when a
        caller wants the CDN lists and the announcement in one request.
        """
        return self.request("GET", "api/v2/config")

    # ------------------------------------------------------------------
    # Galleries
    # ------------------------------------------------------------------

    def gallery_list(self, **params):
        """List galleries, newest first (``GET api/v2/galleries``).

        Declared parameters, both optional and forwarded unchanged:
            page (int): Page number, minimum 1, default 1.
            per_page (int): Items per page, minimum 1, maximum 100,
                default 25.

        Declared body (``PaginatedResponse_GalleryListItem_``): ``result``
        (the ``GalleryListItem`` objects), ``num_pages``, ``per_page`` and
        ``total``. The probe run answered that shape: 2 entries for each of
        ``page=1`` and ``page=2`` with ``per_page=2``, ``per_page`` echoed
        back, and ``total`` 646010 then. Two of those fields are the site's
        own arithmetic rather than a boundary a caller can compute:
        ``num_pages`` was 323037 at ``per_page=2`` (``646010/2`` rounded up is
        323005) and 25843 at ``per_page=25``, and ``total`` is a snapshot that
        moves as galleries are added. Paging past the end is not a terminator
        either: ``page=100000&per_page=25`` answered 200 with 24 entries --
        the catalogue's tail repeated -- rather than an empty page, so a
        short or empty page is not a stop signal this client produces or
        recommends.

        A ``GalleryListItem`` declares ``id``, ``media_id``,
        ``english_title``, ``japanese_title``, ``thumbnail``,
        ``thumbnail_width``, ``thumbnail_height``, ``num_pages`` (0 when
        absent), ``num_favorites``, ``tag_ids`` and ``blacklisted``; the
        probe run's entries carried every one of them. The titles are flat
        here while ``gallery_show`` nests the same text in a ``title`` object,
        so the two gallery shapes are not interchangeable.

        The document declares the route public with an optional credential:
        15 requests a minute per IP anonymously and 30 with one, and 429 when
        that limit is hit. For a paging value it declares 422, while the probe
        run saw 400 ``{"error": "Validation error", "details": [...]}`` for
        ``page=0`` and for ``per_page=101`` and 200 with 100 entries for
        ``per_page=100``. Both statuses are the site's business: this client
        sends the value it is given and returns the answer it gets.
        """
        return self.request("GET", "api/v2/galleries", params=params)

    def gallery_tagged(self, tag_id, **params):
        """List the galleries carrying one tag (``GET api/v2/galleries/tagged``).

        ``tag_id`` is required and is a tag's numeric id, not its name: it
        becomes the ``tag_id`` query parameter, so a call carries
        ``tag_id=12227``. Get one from ``tag_list``, ``tag_show``,
        ``tag_search`` or ``tag_ids`` -- it is the ``id`` field of a
        ``TagResponse``.

        Declared parameters, forwarded unchanged:
            sort (str): ``date``, ``popular``, ``popular-today``,
                ``popular-week`` or ``popular-month``; default ``date``.
            page (int): Page number, minimum 1, default 1.
            per_page (int): Items per page, minimum 1, maximum 100,
                default 25.

        Declared body: the ``PaginatedResponse_GalleryListItem_`` envelope of
        ``gallery_list`` with the same ``GalleryListItem`` entries. The probe
        run's ``tag_id=12227&page=1&per_page=2`` answered 200 with 2 entries,
        ``num_pages`` 73670 and ``total`` null, so ``total`` is not always a
        number on this route. An unknown tag id answered 404 ``{"error":
        ...}``, the status the document declares for it. The document also
        declares 422 for its validator and 429 for rate limiting, and the
        route is public with an optional credential.
        """
        return self.request("GET", "api/v2/galleries/tagged",
                            params=dict(params, tag_id=tag_id))

    def gallery_popular(self):
        """Read today's popular galleries (``GET api/v2/galleries/popular``).

        Declared body: a bare JSON array of ``GalleryListItem`` objects, with
        the entry fields of ``gallery_list`` but without the ``result``
        envelope, the page count or a total, so the array's length is
        whatever the site chose to send and is not a page size. The probe run
        got 5 entries; the document declares no length for this array, so 5
        describes that run and is not a rule. The route takes no parameters,
        which is why this method has none.

        The document declares it public with an optional credential and
        allows 8 requests a minute per IP, the lowest limit of the family's
        reads.
        """
        return self.request("GET", "api/v2/galleries/popular")

    def gallery_random(self):
        """Read one random gallery id (``GET api/v2/galleries/random``).

        Declared 200 body: a JSON object whose keys the document leaves open
        (``additionalProperties`` with no properties declared), carrying the
        id of a random gallery. The probe run answered ``{"id": 641056}``, so
        ``id`` is the key to read today; because the document guarantees no
        key name here, nothing is read out of the object in this method and it
        reaches the caller as sent.

        The document declares the route public with an optional credential
        and lists no 404 for it, so how an empty catalogue answers is not
        described.
        """
        return self.request("GET", "api/v2/galleries/random")

    def gallery_show(self, gallery_id, **params):
        """Read one gallery (``GET api/v2/galleries/{gallery_id}``).

        ``gallery_id`` is the numeric ``id`` of a ``GalleryListItem``. It is
        percent-encoded as one path segment and sent unvalidated, so a
        non-numeric value reaches the site and the site's own status is kept.

        Declared parameter, optional and forwarded unchanged:
            include (str): comma-separated subset of ``comments``,
                ``related``, ``favorite`` and ``suggestions``; default empty,
                which includes none of them. Those four names correspond to
                the optional blocks declared in the body below; the document
                describes the value no further, so this client passes it
                through and does not assemble or validate the list.

        Declared body (``GalleryDetailResponse``): ``id``, ``media_id``,
        ``title`` (``english``, ``japanese``, ``pretty``), ``cover`` and
        ``thumbnail`` (``path``, ``width``, ``height``), ``scanlator``,
        ``upload_date`` (a unix timestamp), ``tags`` (``TagResponse``
        objects), ``num_pages``, ``num_favorites`` and ``pages``, each page
        carrying ``number``, ``path``, ``width``, ``height``, ``thumbnail``,
        ``thumbnail_width`` and ``thumbnail_height``. The probe run's detail
        of gallery 658856 carried exactly those eleven keys (18 ``pages``
        entries against ``num_pages`` 18) and none of the optional blocks.
        Adding ``include=comments,related,favorite,suggestions`` brought in
        ``comments`` (empty), ``comment_count`` (0), ``related`` (5 entries)
        and ``suggestions``, while ``is_favorited`` stayed absent on the
        anonymous call even though ``favorite`` was asked for. A block an
        ``include`` name promises can therefore still be missing, and nothing
        is inserted here to fill the gap. ``num_pages``, ``num_favorites`` and
        the page list are snapshots of a live catalogue rather than constants,
        so treat them as values to read rather than identities to compare.

        The document declares 404 for an id it does not know and 422 for its
        validator; the probe run's unknown id 999999999 answered 404
        ``{"error": "Gallery not found"}``. 429 is declared for rate limiting,
        and the route is public with an optional credential (20 requests a
        minute per IP anonymously, 45 with one).
        """
        return self.request(
            "GET", "api/v2/galleries/{}".format(quote(str(gallery_id), safe="")),
            params=params)

    def gallery_related(self, gallery_id):
        """Read galleries similar to one gallery (``GET api/v2/galleries/{gallery_id}/related``).

        ``gallery_id`` is the numeric gallery id, encoded as one path
        segment. Declared body (``RelatedGalleriesResponse``): only
        ``result``, an array of ``GalleryListItem`` objects -- there is no
        page count, no ``per_page`` and no ``total`` in this answer, so it is
        not a page of the listing envelope. The probe run's call for 658856
        answered ``{"result": [...]}`` with 5 entries of that entry shape, but
        5 is that run's number and not a promise: the document fixes no length
        for the array.

        The document declares 404 for an id it does not know, 422 for its
        validator (which a non-numeric path segment fails before the route
        sees it) and 429 for rate limiting, and allows 12 requests a minute
        per IP anonymously, 30 with a credential.
        """
        return self.request(
            "GET", "api/v2/galleries/{}/related".format(quote(str(gallery_id), safe="")))

    def gallery_favorite(self, gallery_id):
        """Check whether one gallery is in the account's favorites (``GET api/v2/galleries/{gallery_id}/favorite``).

        Declared body (``FavoriteResponse``): ``favorited`` (a boolean) and
        ``num_favorites`` (an integer or null).

        Needs a User Token or an API key. The probe run's anonymous call
        answered 401 ``{"error": "Authentication required"}``, which is what a
        caller without a configured key gets; the document declares 401 and
        422, and 429 for the per-user limit of 15 a minute. Nothing is changed
        by this call -- the write side is ``favorite_add`` and
        ``favorite_remove``.
        """
        return self.request(
            "GET",
            "api/v2/galleries/{}/favorite".format(quote(str(gallery_id), safe="")))

    def favorite_add(self, gallery_id):
        """Add one gallery to the account's favorites (``POST api/v2/galleries/{gallery_id}/favorite``).

        **This changes the authenticated account.** ``gallery_id`` is
        percent-encoded as one path segment; the path is the whole request,
        so no body and no query parameter is sent.

        Declared body: the same ``FavoriteResponse`` as ``gallery_favorite``
        (``favorited``, ``num_favorites``). Needs a User Token or API key,
        and the document gates the route behind the site's
        ``allow_favorites`` flag: it declares 401 without a credential, 404
        for an id it does not know, 503 when the feature is off and 429 when
        the per-user limit of 15 a minute is hit. A 2xx means the site
        accepted the call, not that the favorite list ends up in the state
        the caller expects, so reading it back is the caller's step. This
        project has never sent this request.
        """
        return self.request(
            "POST",
            "api/v2/galleries/{}/favorite".format(quote(str(gallery_id), safe="")))

    def favorite_remove(self, gallery_id):
        """Remove one gallery from the account's favorites (``DELETE api/v2/galleries/{gallery_id}/favorite``).

        **This changes the authenticated account.** ``gallery_id`` is
        percent-encoded as one path segment and the request carries no body.
        Declared body: the ``FavoriteResponse`` object (``favorited``,
        ``num_favorites``) that ``gallery_favorite`` returns.

        Needs a User Token or API key and the site's ``allow_favorites``
        flag: the document declares 401 without a credential, 404 for an id
        it does not know, 503 when the feature is off and 429 for the
        per-user limit. Removing a gallery that is not in the list is a
        change to nothing, and the document does not describe how that case
        answers. This project has never sent this request.
        """
        return self.request(
            "DELETE",
            "api/v2/galleries/{}/favorite".format(quote(str(gallery_id), safe="")))

    def gallery_suggestions(self, gallery_id, **params):
        """List current tag-change proposals on one gallery (``GET api/v2/galleries/{gallery_id}/suggestions``).

        ``gallery_id`` is the numeric gallery id, encoded as one path
        segment. Declared parameters, forwarded unchanged:
            tier (str): ``all``, ``trending``, ``active``, ``declined``,
                ``hidden``, ``mine`` or ``history``; default ``all``.
            limit (int): 1 to 100, default 20.

        Declared body (``SuggestionListResponse``): ``result`` (the
        ``SuggestionResponse`` objects), ``has_more``, ``num_pages`` and
        ``total``. The document marks the last three optional, and the probe
        run's default-tier call for gallery 658856 answered only ``result``,
        empty -- a gallery with no open proposal, not an error. A suggestion
        declares ``id`` (a string), ``gallery_id``, ``tag``, ``action``
        (``add`` or ``remove``), ``status`` (``pending``, ``accepted``,
        ``rejected`` or ``superseded``), ``score``, ``voter_count``,
        ``proposer``, ``created_at``, ``resolved_at``, ``resolver``,
        ``resolution_note``, ``reverted_at``, ``reverter``, ``my_vote`` and
        ``tier``. The resolution and revert fields (``resolved_at``,
        ``resolver``, ``resolution_note``, ``reverted_at``, ``reverter``) are
        the moderation trail and are null unless the site fills them, while
        ``my_vote`` and ``tier`` describe the viewer's own state.

        The document declares the route public with an optional credential
        and gates it behind the site's ``allow_gts`` flag: a 503 is declared
        when that flag is off, 422 for its validator and 429 for rate
        limiting (60 a minute per IP).
        """
        return self.request(
            "GET",
            "api/v2/galleries/{}/suggestions".format(quote(str(gallery_id), safe="")),
            params=params)

    def gts_backlog(self, **params):
        """List pending tag-change suggestions across galleries (``GET api/v2/gts/backlog``).

        Declared parameters, all optional and forwarded unchanged:
            page (int): 1 to 200, default 1.
            per_page (int): 1 to 50, default 20.
            tag_id (int): only suggestions about this tag id; must be above 0.
            action (str): ``add`` or ``remove``.
            sort_by (str): ``starvation``, ``voters``, ``score``,
                ``gallery_age`` or ``created_at``; default ``starvation``.
            sort (str): ``asc`` or ``desc``; default ``asc``.

        Declared body (``BacklogListResponse``): ``result`` (``BacklogRow``
        objects, each pairing a ``suggestion`` with the ``gallery`` it applies
        to), ``has_more``, ``num_pages`` and ``total``. The probe run's
        ``per_page=2`` answered 2 entries with ``has_more`` true,
        ``num_pages`` 27919 and ``total`` 55838, so all four keys arrive here;
        those counts are snapshots of a moving backlog.

        Public with an optional credential but gated behind the site's
        ``allow_gts`` flag: the document declares 503 when that flag is off,
        422 for a value its validator rejects, and 429 (60 requests a minute
        per IP).
        """
        return self.request("GET", "api/v2/gts/backlog", params=params)

    def gts_new_tags(self, **params):
        """List the most recently community-minted tags (``GET api/v2/gts/new-tags``).

        Declared parameter, optional and forwarded unchanged:
            limit (int): 1 to 50, default 25.

        Declared body (``NewTagIndexResponse``): ``result``, an array of
        ``NewTagIndexEntry`` objects, each carrying ``tag`` (a
        ``TagResponse``), ``created_at`` (a unix timestamp) and
        ``pending_gts_count`` (how many pending tag-change suggestions
        reference that tag).

        The probe run's ``limit=2`` answered 200 with 2 entries of that shape.
        The document declares no credential for this route at all, so no key
        is needed; it is still gated behind the site's ``allow_gts`` flag,
        and 503 is declared when that flag is off (422 for its validator and
        429 for the 60-a-minute-per-IP limit are declared too).
        """
        return self.request("GET", "api/v2/gts/new-tags", params=params)

    def gallery_download(self, gallery_id, **params):
        """Allocate a download URL for one gallery (``POST api/v2/galleries/{gallery_id}/download``).

        **This asks the site to mint a URL for an account.** ``gallery_id``
        is percent-encoded as one path segment. Declared parameter, optional
        and forwarded unchanged:
            format (str): ``zip``, ``cbz`` or ``torrent``; default ``zip``.

        Declared body (``DownloadResponse``): ``url`` (a string) and
        ``expires_at`` (a unix timestamp). Only those two fields are
        returned: this project never fetches the archive or torrent the URL
        points at, does not store the URL, does not refresh it after
        ``expires_at`` and adds no local retry. The URL is short-lived, so
        fetch it before that timestamp -- that rule is the site's, stated in
        the route's own description.

        Needs a User Token or API key, and the document gates the route
        behind the site's ``allow_downloads`` flag and gives separate limits
        per format (for the default ``zip`` and for ``cbz``, 10 calls per 5
        minutes per IP; for ``torrent``, 5 a minute per IP). It declares 503
        when the feature is off, 422 for its validator and 429 for the
        limits. This project has never sent this request.
        """
        return self.request(
            "POST",
            "api/v2/galleries/{}/download".format(quote(str(gallery_id), safe="")),
            params=params)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_ids(self, ids):
        """Look up several tags by id (``GET api/v2/tags/ids``).

        ``ids`` is required and is the comma-separated string the route's own
        ``ids`` parameter takes: ``tag_ids('12227,6346')`` asks for those two
        tags. It is a string, not a sequence, so nothing is joined here -- the
        caller writes the separator.

        Declared body: a bare JSON array of ``TagResponse`` objects (no
        ``result`` envelope, no page count), each carrying ``id``, ``type``,
        ``name``, ``slug``, ``url``, ``count``, ``description``,
        ``is_community`` and ``pending_describe_id``. The probe run's
        ``ids='12227,6346'`` answered that bare array with 2 objects, each
        carrying all nine keys, with ``description``, ``is_community`` and
        ``pending_describe_id`` null where the site has nothing to put there
        (one of the two had a description, the other did not). The document
        limits the route to 100 ids per request but this client neither counts
        nor splits them: an oversized call reaches the site and the site's
        answer is kept. Public route, 15 requests a minute per IP, and the
        document declares 422 and 429.
        """
        return self.request("GET", "api/v2/tags/ids", params={"ids": ids})

    def tag_search(self, **attributes):
        """Search tags by name prefix (``POST api/v2/tags/search``).

        Each keyword argument becomes one field of the JSON request body and
        is sent exactly as written: ``tag_search(query='english',
        type='language', limit=3)`` posts that object, and ``tag_search()``
        posts an empty one. Declared body fields (``AutocompleteRequest``):
        ``type`` (a tag class name or null), ``query`` (the prefix, or null)
        and ``limit`` (default 10). The document requires none of them, so no
        field is filled in, no null is filtered out and no value is validated
        here; omitting ``type`` searches across all tag types.

        Declared 200 body: a bare JSON array of ``TagResponse`` objects. This
        POST changes nothing. Public route, 30 requests a minute per IP; the
        document declares 400 for a body the site rejects, 422 for its
        validator and 429 for the limit. This project has never sent this
        request -- the probe run covered the GET routes only -- so neither the
        shape of a real answer nor how the site takes an empty object is
        verified here.
        """
        return self.request("POST", "api/v2/tags/search", data=attributes)

    def tag_list(self, tag_type, **params):
        """List tags of one class with pagination (``GET api/v2/tags/{tag_type}``).

        ``tag_type`` is the class name and is percent-encoded as one path
        segment: ``tag_list('language')`` calls ``api/v2/tags/language``.
        The document types the segment as a free string without enumerating
        it and declares a 400 on this route for a request the site rejects,
        so no name is checked here and no list of accepted ones is assumed.

        Declared parameters, forwarded unchanged:
            sort (str): ``name`` or ``popular``; default ``popular``.
            page (int): Page number, minimum 1, default 1.
            per_page (int): Items per page, minimum 1, maximum 100,
                default 25.

        Declared body (``TagPaginatedResponse``): ``result`` (the
        ``TagResponse`` objects), ``num_pages``, ``per_page``, ``total`` and
        ``alphabet``, an object or null whose keys the document does not
        describe.

        The probe run showed two things a caller has to know. First, the page
        size that comes back is not the one asked for: ``per_page=1`` answered
        120 entries with ``per_page`` 120 on both ``tags/tag`` and
        ``tags/language``, and the document's response schema says 120 while
        its request parameter says 25 with a maximum of 100 -- so read
        ``per_page`` out of the answer and never size a loop from the request.
        Second, ``alphabet`` belongs to ``sort=name``: the default ``popular``
        answer carried no ``alphabet`` key at all, while the ``sort=name``
        answer carried a 27-key object. The list entries also omitted
        ``is_community`` and ``pending_describe_id`` (no entry of the probe's
        ``tags/tag`` page had either key) and omitted ``description`` where
        the site has none, so a list entry is a narrower object than the
        ``tag_show`` detail.

        An unknown class name answered 400 ``{"error": ...}``, the status the
        document declares on this route; 422 and 429 are declared as well.
        The route is public, and 15 requests a minute per IP are allowed
        anonymously (30 with a credential).
        """
        return self.request(
            "GET", "api/v2/tags/{}".format(quote(str(tag_type), safe="")),
            params=params)

    def tag_show(self, tag_type, slug):
        """Read one tag (``GET api/v2/tags/{tag_type}/{slug}``).

        Both segments are required and both are percent-encoded as single
        path segments: ``tag_show('language', 'english')`` calls
        ``api/v2/tags/language/english``. The slug is the tag's stored slug
        (the ``slug`` field a ``TagResponse`` carries), not its display name.

        Declared body (``TagResponse``): ``id``, ``type``, ``name``,
        ``slug``, ``url``, ``count``, ``description``, ``is_community`` and
        ``pending_describe_id``. ``url`` is the site's own tag page path, not
        an API URL, and ``description`` is the tag description (null when the
        site has none); ``pending_describe_id`` is the id of an open
        description proposal or null. The probe run's ``language/english``
        answered 200 with all nine keys, ``description`` filled and the other
        two null. The document declares 404 for a pair it does not know, 422
        for its validator and 429; public route.
        """
        return self.request(
            "GET", "api/v2/tags/{}/{}".format(
                quote(str(tag_type), safe=""), quote(str(slug), safe="")))

    # ------------------------------------------------------------------
    # Taxonomy suggestions
    # ------------------------------------------------------------------

    def taxonomy_list(self, **params):
        """List pending taxonomy suggestions (``GET api/v2/taxonomy``).

        Declared parameters, all optional and forwarded unchanged:
            tier (str): ``all``, ``trending``, ``active``, ``declined`` or
                ``mine``; default ``all``.
            page (int): Page number, minimum 1, default 1.
            per_page (int): 1 to 200, default 50.
            q (str): Search text, 1 to 100 characters.
            target_tag_id (int): only suggestions about this tag id; above 0.
            sort_by (str): ``score`` (sum of votes), ``votes`` (unique voter
                count), ``comment_count``, ``last_comment_at`` or
                ``created_at``; default ``score``.
            sort (str): ``asc`` or ``desc``; default ``desc``.
            action (str): comma-separated subset of ``create``, ``rename``,
                ``merge`` and ``describe``; the default is all of them.
            discussion (str): ``with`` for suggestions that have at least one
                comment, ``without`` for none, omitted for either.
            edited (str): ``yes`` for edited suggestions, ``no`` for never
                edited, omitted for either.

        Declared body (``TaxonomySuggestionListResponse``): ``result`` (the
        ``TaxonomySuggestionResponse`` objects), ``has_more``, ``num_pages``
        and ``total``. A suggestion declares ``id`` (a string), ``action``
        (``create``/``rename``/``merge``/``describe``), ``status``
        (``pending``/``accepted``/``rejected``/``withdrawn``), ``score``,
        ``voter_count``, ``proposer``, ``proposer_note``, ``created_at``,
        ``edited_at``, ``resolved_at``, ``resolution_note``, ``resolver``,
        ``target_tag``, ``merge_into_tag``, ``new_name``, ``new_type``,
        ``new_description``, ``accepted_type``, ``accepted_name``,
        ``accepted_description``, ``resolved_tag``, ``my_vote``, ``tier``,
        ``tier_page``, ``comment_count`` and ``recent_comments``.

        The probe run's ``per_page=2`` answered 200 with 2 entries,
        ``has_more`` true, ``num_pages`` 1492 and ``total`` 2984, so all four
        envelope keys arrive on this route. Public with an optional credential
        but gated behind the site's ``allow_taxonomy`` flag: 503 is declared
        when that flag is off, 422 for its validator and 429 (120 requests a
        minute per IP).
        """
        return self.request("GET", "api/v2/taxonomy", params=params)

    def taxonomy_stats(self):
        """Read the taxonomy activity summary (``GET api/v2/taxonomy/stats``).

        Declared body (``TaxonomySuggestionStats``): the counters ``pending``,
        ``accepted_total``, ``rejected_total``, ``accepted_30d``,
        ``accepted_7d``, ``created_30d``, ``renamed_30d``, ``merged_30d``,
        ``described_30d``, and the tier counters ``trending_count`` (0 when
        absent), ``active_count`` and ``declined_count``, plus
        ``recent_accepted``, an array of recently accepted
        ``TaxonomySuggestionResponse`` objects. Everything is a number or an
        array of objects; nothing here is derived or added up locally.

        The document declares this route public without a credential (no
        security entry), and gates it behind ``allow_taxonomy``: a 503 is
        declared when that flag is off, 429 for rate limiting (30 requests a
        minute per IP). The probe run's answer carried the whole declared key
        set, ``recent_accepted`` included.
        """
        return self.request("GET", "api/v2/taxonomy/stats")

    def taxonomy_resolved(self, **params):
        """List resolved taxonomy suggestions (``GET api/v2/taxonomy/resolved``).

        Declared parameters, all optional and forwarded unchanged:
            status (str): ``all``, ``accepted`` or ``rejected``; default
                ``all``.
            q (str): Search text, 1 to 100 characters.
            discussion (str): ``with`` or ``without``; omitted for either.
            edited (str): ``yes`` or ``no``; omitted for either.
            action (str): comma-separated subset of ``create``, ``rename``,
                ``merge`` and ``describe``.
            sort_by (str): ``resolved_at`` (the default), ``score``,
                ``votes``, ``comment_count``, ``last_comment_at`` or
                ``created_at``.
            sort (str): ``asc`` or ``desc``; the document declares no default
                here.
            page (int): Page number, minimum 1, default 1.
            per_page (int): Items per page, minimum 1, maximum 100,
                default 25.

        Declared body: the ``TaxonomySuggestionListResponse`` envelope of
        ``taxonomy_list`` (``result``, ``has_more``, ``num_pages``,
        ``total``) with the same suggestion objects.

        This route ignored the page size it was asked for: the probe run's
        ``per_page=2`` answered 50 entries with ``num_pages`` 4 and ``total``
        196, and an undeclared ``limit=2`` was ignored in the same way and
        returned the same 50. The effective page size and the real ceiling of
        this route were not established, so read ``per_page`` out of the
        answer rather than trusting the request. Public with an optional
        credential, gated behind ``allow_taxonomy``: 503 when that flag is
        off, 422 for its validator and 429 (90 requests a minute per IP).
        """
        return self.request("GET", "api/v2/taxonomy/resolved", params=params)

    def taxonomy_show(self, suggestion_id):
        """Read one taxonomy suggestion with its newest comment preview (``GET api/v2/taxonomy/{suggestion_id}``).

        ``suggestion_id`` is the suggestion's string id (the document types
        it as a UUID string, not an integer), percent-encoded as one path
        segment and sent unvalidated.

        Declared body (``TaxonomySuggestionResponse``): the fields listed in
        ``taxonomy_list``, of which ``recent_comments`` is the comment
        preview attached to this answer. The probe run's answer carried the
        suggestion object without ``tier`` and ``tier_page``, keys the list
        route did include, so a key present in a list entry can be absent from
        the detail. Public with an optional credential, gated behind
        ``allow_taxonomy``: 404 for an id it does not know, 503 when that flag
        is off, 422 for its validator and 429 (120 requests a minute per IP).
        """
        return self.request(
            "GET", "api/v2/taxonomy/{}".format(quote(str(suggestion_id), safe="")))

    def taxonomy_comments(self, suggestion_id, **params):
        """List the comments on one taxonomy suggestion (``GET api/v2/taxonomy/{suggestion_id}/comments``).

        ``suggestion_id`` is the suggestion's string id, encoded as one path
        segment. Declared parameters, forwarded unchanged:
            page (int): Page number, minimum 1, default 1.
            per_page (int): Items per page, minimum 1, maximum 100,
                default 50.

        Declared body (``TaxonomyCommentListResponse``): ``result`` (the
        comment objects), ``has_more``, ``num_pages`` and ``total``. Each
        comment declares ``id`` (a string), ``body`` (the comment's text),
        ``author``, ``created_at``, ``can_delete`` (a boolean, false when
        absent) and ``link_previews`` (an array of link previews, gallery or
        taxonomy shaped, empty when absent). The probe run's
        ``page=1&per_page=2`` answered 2 entries with ``has_more`` true,
        ``num_pages`` 10 and ``total`` 19, so all four envelope keys arrive
        here. The body text is returned as stored and is not shortened,
        escaped or filtered here.

        Public with an optional credential, gated behind ``allow_taxonomy``:
        404 for an unknown suggestion, 503 when that flag is off, 422 and 429
        (120 requests a minute per IP) are declared.
        """
        return self.request(
            "GET",
            "api/v2/taxonomy/{}/comments".format(quote(str(suggestion_id), safe="")),
            params=params)

    def taxonomy_edits(self, suggestion_id):
        """List one suggestion's edit history (``GET api/v2/taxonomy/{suggestion_id}/edits``).

        ``suggestion_id`` is the suggestion's string id, encoded as one path
        segment. Declared body (``TaxonomySuggestionEditListResponse``): only
        ``result``, an array of edit events, each carrying ``id`` (a string),
        ``created_at``, ``summary`` (a free-text note or null), ``changes``
        (the fields one edit changed) and ``editor``. There is no page count
        or total in this answer. The probe run's answer was ``{"result": []}``
        for a suggestion that had never been edited, so those entry fields are
        the document's description of the shape and not something that run
        saw filled in.

        The document declares this route public without a credential and
        gates it behind ``allow_taxonomy``: 404 for an unknown suggestion, 503
        when that flag is off, 422 and 429 (120 requests a minute per IP).
        """
        return self.request(
            "GET",
            "api/v2/taxonomy/{}/edits".format(quote(str(suggestion_id), safe="")))

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def gallery_comments(self, gallery_id, **params):
        """List the visible comments on one gallery, newest first (``GET api/v2/galleries/{gallery_id}/comments``).

        ``gallery_id`` is the numeric gallery id, encoded as one path
        segment. Declared parameters, forwarded unchanged:
            page (int): Page number, minimum 1, maximum 2000, default 1.
            per_page (int): Items per page, minimum 1, maximum 50,
                default 50. Note that this route's per-page ceiling is 50,
                not the 100 of the gallery listing.

        Declared body (``PaginatedResponse_CommentResponse_``): ``result``
        (the comment objects), ``num_pages``, ``per_page`` and ``total``. The
        probe run's ``page=1&per_page=2`` for gallery 658856 answered 200 with
        ``result`` empty, ``num_pages`` 0, ``per_page`` 2 and ``total`` 0 --
        an empty list is a normal answer. A comment declares ``id``,
        ``gallery_id``, ``poster`` (a public user: ``id``, ``username``,
        ``slug``, ``avatar_url``, ``is_superuser``, ``is_staff``),
        ``post_date`` (a unix timestamp) and ``body`` (the comment's text,
        returned as stored and never shortened, escaped or filtered here).
        The site's own changelog note caps this route at 50 comments a page,
        which is the ceiling the document already declares.

        Public with an optional credential (30 requests a minute per IP
        anonymously, 60 with one), and the document declares 404 for an
        unknown gallery, 422 and 429.
        """
        return self.request(
            "GET",
            "api/v2/galleries/{}/comments".format(quote(str(gallery_id), safe="")),
            params=params)

    def gallery_comment_count(self, gallery_id):
        """Read the visible comment count of one gallery (``GET api/v2/galleries/{gallery_id}/comments/count``).

        ``gallery_id`` is the numeric gallery id, encoded as one path
        segment. The declared 200 body is a bare JSON integer -- the count
        itself, not an object wrapping it -- so this method returns a number
        for a successful call, unlike the rest of the family; the probe run
        got ``0`` for gallery 658856, which has no comments.

        The document declares this route public without a credential, and
        declares 404 for an unknown gallery, 422 and 429 (12 requests a
        minute per IP anonymously, 20 with a credential).
        """
        return self.request(
            "GET",
            "api/v2/galleries/{}/comments/count".format(quote(str(gallery_id), safe="")))

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query, **params):
        """Search galleries (``GET api/v2/search``).

        ``query`` is required and is the search expression; it carries at
        least one character according to the document, and it becomes the
        ``query`` parameter. The document describes the grammar it accepts:
        bare keywords (``word``), exact phrases in double quotes
        (``"exact phrase"``), negation (``-word``, ``-"exact phrase"``,
        ``-artist:name``), tag filters (``artist:name``,
        ``language:english``, ``tag:"big breasts"``), numeric filters
        (``pages:>10``, ``favorites:>=100``) and date filters
        (``uploaded:<7d``, ``uploaded:>1m``). Nothing here parses, rewrites
        or validates that expression: it is sent as written and an invalid
        one gets the site's own answer.

        Declared parameters, optional and forwarded unchanged:
            sort (str): ``date``, ``popular``, ``popular-today``,
                ``popular-week`` or ``popular-month``; default ``date``.
            page (int): Page number, minimum 1, default 1.

        Declared body: the ``PaginatedResponse_GalleryListItem_`` envelope of
        ``gallery_list`` (``result``, ``num_pages``, ``per_page``,
        ``total``) with the same ``GalleryListItem`` entries. The probe run's
        ``query=language:english`` answered 25 entries with ``per_page`` 25,
        ``total`` 147497 and ``num_pages`` 5900, and asking it for an
        undeclared ``per_page=2`` changed nothing -- this route has no
        per-page parameter, so the page size in the answer is the site's.
        A query nothing matches is a 200 with an empty ``result``, ``total``
        0 and ``num_pages`` 0, not an error; a missing ``query`` and a bad
        ``sort`` both answered 400 ``{"error": ..., "details": [...]}`` where
        the document declares 422 for its validator. Public with an optional
        credential, and this route's anonymous limit of 10 requests a minute
        per IP (20 with a credential) is the tightest read of the family; 429
        is declared as well.
        """
        return self.request("GET", "api/v2/search", params=dict(params, query=query))

    # ------------------------------------------------------------------
    # Favorites
    # ------------------------------------------------------------------

    def favorite_list(self, **params):
        """List the account's favorite galleries (``GET api/v2/favorites``).

        Declared parameters, optional and forwarded unchanged:
            q (str): text to search within the favorites.
            page (int): Page number, minimum 1, default 1. The document
                declares no per-page parameter on this route.

        Declared body: the ``PaginatedResponse_GalleryListItem_`` envelope
        (``result``, ``num_pages``, ``per_page``, ``total``) with
        ``GalleryListItem`` entries, the same shape as a search page.

        Needs a User Token or API key: the document declares 401 for a caller
        without one, 422 and 429 (15 requests a minute per user or per key
        owner). The probe run's anonymous call answered 401 ``{"error":
        "Authentication required"}``.
        """
        return self.request("GET", "api/v2/favorites", params=params)

    def favorite_random(self):
        """Read one random gallery id from the account's favorites (``GET api/v2/favorites/random``).

        Declared 200 body: a JSON object whose keys the document leaves open,
        carrying the id of one favorite gallery, in the same undocumented
        shape as ``gallery_random``; nothing is read out of it here.

        Needs a User Token or API key: the document declares 401 without one
        and also declares 404 on this route without describing when it
        happens; the probe run's anonymous call answered 401 ``{"error":
        "Authentication required"}``. The client neither translates nor
        retries either status, and the route allows 15 requests a minute per
        user or per key owner.
        """
        return self.request("GET", "api/v2/favorites/random")

    # ------------------------------------------------------------------
    # Blacklist
    # ------------------------------------------------------------------

    def blacklist_list(self):
        """Read the account's blacklisted tags (``GET api/v2/blacklist``).

        Declared body (``BlacklistListResponse``): ``tags``, an array of
        blacklisted tag objects each carrying ``id``, ``type``, ``name``,
        ``slug`` and ``count``, and ``count``, the number of entries in
        ``tags``. The entries are the site's tag records, so they hold no
        per-gallery or per-user setting.

        Needs a User Token or API key: the document declares 401 for a caller
        without one and 429 (15 requests a minute per user or per key owner).
        The probe run's anonymous call answered 401 ``{"error":
        "Authentication required"}``.
        """
        return self.request("GET", "api/v2/blacklist")

    def blacklist_update(self, **attributes):
        """Add tags to or remove tags from the account's blacklist (``POST api/v2/blacklist``).

        **This changes the authenticated account.** Each keyword argument
        becomes one field of the JSON request body and the body is sent
        exactly as written: ``blacklist_update(added=[12227])`` posts
        ``{"added": [12227]}``, and ``blacklist_update(added=[], removed=[])``
        keeps both empty arrays instead of dropping them, because an empty
        array is a value the site can mean. Declared body fields
        (``BlacklistUpdateRequest``): ``added`` and ``removed``, each an
        array of tag ids defaulting to an empty array on the server side.
        Nothing is validated, renamed or filtered here.

        Declared body (``BlacklistResponse``): ``success`` (a boolean) and
        ``count`` (the size of the blacklist afterwards). Needs a User Token
        or API key: the document declares 401 without a credential, 400 for a
        body the site rejects, 422 for its validator and 429 (20 calls per 15
        minutes per user or per key owner, the family's slowest write limit).
        This project has never sent this request.
        """
        return self.request("POST", "api/v2/blacklist", data=attributes)

    def blacklist_ids(self):
        """Read just the blacklisted tag ids (``GET api/v2/blacklist/ids``).

        Declared body: a bare JSON array of integers -- the tag ids -- with
        no names, no counts and no envelope, so it is lighter than
        ``blacklist_list`` and loses the tags' names.

        Needs a User Token or API key: the document declares 401 for a caller
        without one and 429 (45 requests a minute per user). The probe run's
        anonymous call answered 401 ``{"error": "Authentication required"}``.
        """
        return self.request("GET", "api/v2/blacklist/ids")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def user_show(self, user_id, slug):
        """Read a public user profile (``GET api/v2/users/{user_id}/{slug}``).

        Both segments are required and both are percent-encoded as single
        path segments: the numeric user id and the username slug the route
        pairs with it. The document says both have to be correct, so the id
        alone is not enough, and a pair that does not match is the site's own
        404 rather than an empty profile.

        Declared body (``UserProfileResponse``): ``id``, ``username``,
        ``slug``, ``avatar_url``, ``is_superuser`` (false when absent),
        ``is_staff`` (false when absent), ``date_joined`` (a unix timestamp),
        ``about`` (an empty string when absent), ``favorite_tags`` (an empty
        string when absent), ``recent_favorites`` (gallery cards: ``id``,
        ``media_id``, ``thumbnail``, ``thumbnail_width``,
        ``thumbnail_height``, ``english_title``, ``japanese_title``,
        ``num_pages``, ``tag_ids``) and ``recent_comments`` (``id``,
        ``gallery_id``, ``body``, ``post_date``, ``gallery_title``).

        The probe run's pair answered 200 with every declared key:
        ``recent_favorites`` and ``recent_comments`` carried 5 entries each,
        ``about`` and ``favorite_tags`` were empty strings and the two flags
        false. Public with an optional credential, and the document's
        anonymous limit of 5 requests a minute per IP (10 with a credential)
        is the lowest limit declared for any read of the family. 404, 422 and
        429 are declared.
        """
        return self.request(
            "GET", "api/v2/users/{}/{}".format(
                quote(str(user_id), safe=""), quote(str(slug), safe="")))

    def user_me(self):
        """Read the configured account's own profile (``GET api/v2/user``).

        Needs a User Token or API key. The probe run's anonymous call
        answered 401 ``{"error": "Authentication required"}``, which is what a
        caller without a configured key gets. This is the family's one route
        from the document's first-party user tag; every other operation of
        that tag, and the auth group beside it, is outside this client, which
        also implements no login, session, token or key management.

        Declared body (``UserMeResponse``): ``id``, ``username``, ``slug``,
        ``avatar_url``, ``theme`` (the string ``'black'`` when absent),
        ``is_staff``, ``is_superuser``, ``about``, ``favorite_tags`` and
        ``email``, which the document says is hidden (null) when the
        credential is an API key -- so a caller with an API key configured
        gets a profile without the address. 429 is declared as well (45
        requests a minute per user or per key owner).
        """
        return self.request("GET", "api/v2/user")
