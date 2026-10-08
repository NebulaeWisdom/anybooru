"""Native methods for pixiv (www.pixiv.net and app-api.pixiv.net).

pixiv is an illustration site of its own rather than one of the booru engines
this package ships for, and it exposes two JSON APIs on two hosts. The web API
is the site's own front end under ``https://www.pixiv.net``: its routes are
``ajax/...``, ``ranking.php`` and a few ``rpc`` scripts, and it answers
``{"error": false, "message": "", "body": {...}}`` envelopes. The app API is
the official mobile client API under ``https://app-api.pixiv.net``, whose
routes are ``v1/...``, ``v2/...`` and ``webview/...``, and it answers bare
JSON with no envelope. Every method is named for the route it calls and is
prefixed ``web_`` or ``app_`` for the host it speaks to; each is a thin
``Pixiv.request()`` call that forwards the caller's values unchanged. No
method logs in, retries, downloads media, or fills in a parameter the caller
left out.

Evidence. There is no official pixiv API specification. The web methods are
grounded in live anonymous reads of the site (``docs/verification.md``) and in
four community sources, none of them a server specification: W
(``YieldRay/pixiv-web-api``), N (``FreeNowOrg/PixivNow`` docs), D
(``daydreamer-json/pixiv-ajax-api-docs``, whose author marks it stale) and S
(a community novel-endpoint reference); ``showcase_article`` follows P
(``pixivpy3/aapi.py``). The app methods follow P (``pixivpy3/aapi.py`` and its
models), the ZipFile capture of the Android client and the gallery-dl client
source. Where a route has an
observed status or field it is quoted as such; where a body comes only from a
source it is described, never claimed as verified. A source that does not
guarantee a write's response fields is not given invented ones. The graded
contract notes are ``docs/pixiv-contract-notes.md``.

Shared observed facts:
    * Base URLs: ``https://www.pixiv.net`` for the web host and
      ``https://app-api.pixiv.net`` for the app host. ``Pixiv.request``
      selects one with ``api='web'`` or ``api='app'`` and joins the route onto
      it.
    * Web reads answer ``{"error": <bool>, "message": <str>, "body": ...}``.
      The ``ajax`` search, ranking and comment routes were observed to answer
      ``{"error": ..., "body": ...}`` without ``message``; ``ranking.php``
      answers a bare object with no envelope at all. Nothing here reshapes any
      of them.
    * A web read of an unknown id answers an envelope with ``error: true`` and
      the site's own status -- ``ajax/illust/59580629`` gave 404
      ``{"error": true, "message": "", "body": []}`` and ``ajax/illust/0``
      gave 400. An out-of-range ``ranking.php`` page gave 404 with the bare
      ``{"error": "<message>"}`` object. A web ``error: true`` body that
      arrives with a 200 stays data; the shared transport only turns a non-2xx
      into an error, keeping that status and body.
    * Most ``ajax`` reads work with the ``Referer: <web root>/`` header this
      client sends by default and with no cookie. Routes scoped to the
      signed-in account (a user's following list, the followed feed, the
      account dashboard) answer 400 or 401 without a session cookie
      (``ajax/user/<id>/following`` and ``ajax/discovery/artworks`` were
      observed 400 anonymously); they are still provided because a caller who
      supplies a ``Cookie`` can reach them. A read of another user's public
      bookmarks also answered 400 anonymously in a probe.
    * List-valued query values use the shared encoder, i.e. repeated
      ``name[]`` pairs; the illustration recommendation continuation was
      verified live to take the same bracketed form, so every list on either
      host goes through the shared encoder.
    * The app host answers bare JSON and authenticates with
      ``Authorization: Bearer <access_token>``. Most app routes need a token
      and an anonymous call is rejected: ``v1/illust/detail?illust_id=
      59580629`` answered HTTP 400 with a bare ``{"error": {...}}`` object,
      not a 401 and not the web envelope. Two app routes are anonymous and
      both answered 200 without a token: ``v1/application-info/android`` and
      ``v1/emoji``. The app routes take ``filter`` (``for_ios``/``for_android``
      in the client source), but this client injects no such default. No
      ``x-client-time``/``x-client-hash`` is needed for these business routes
      and none is fabricated; only the token is added.
    * App listings return an absolute ``next_url`` a caller passes back to
      ``Pixiv.request`` verbatim; web listings carry the site's own page
      counters instead (``lastPage``, ``total``, ``page``, ``next``). Nothing
      is incremented, clamped or auto-followed here.
    * The write methods (bookmarks, likes, comments, follows, blocks, series
      watches, the AI-display setting) are documented so the contract is
      visible; each is a ``POST`` except ``web_bookmark_rename_progress``,
      which the site answers by ``GET``. This project never calls any of them.
    * Media addresses (``urls``, ``url``, ``image``, ``profile_img``,
      ``zip_urls``, ``image_urls``, ``coverUrl``) point at ``i.pximg.net`` and
      are returned exactly as received; nothing is downloaded or rewritten.

Classes:
    PixivApi_Mixin -- pixiv web and app reads plus the documented writes.
"""

# Standard library imports
from urllib.parse import quote


class PixivApi_Mixin:
    """pixiv reads and writes, each a thin ``Pixiv.request()`` call.

    The ``web_`` methods call the web host (``api='web'``, the ``request``
    default) and the ``app_`` methods the app host (``api='app'``). Required
    identifiers are named in each signature and percent-encoded as one path
    segment; values the web host expects in the query are merged into the
    query under the route's own key, and values an app route expects in the
    query are merged the same way (the app host puts its ids in the query, not
    the path). Every other value is forwarded to ``request`` unchanged, so
    pagination, ordering and filters are the caller's. No source default is
    injected.
    """

    # ------------------------------------------------------------------
    # Web host: illustrations
    # ------------------------------------------------------------------

    def web_illust_show(self, illust_id, **params):
        """Read one illustration's detail page (``GET ajax/illust/<id>``).

        ``illust_id`` is the illustration number, taken from an artwork URL
        such as ``https://www.pixiv.net/artworks/149040133`` or from a listing
        entry's ``id``. It is quoted as one path segment. ``params`` is
        forwarded unchanged; the site's own pages add ``full=1`` and a
        ``lang``, neither of which is sent unless passed.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``id``/``illustId``, ``illustTitle``/``title``, ``description``,
        ``userId``/``userName``, ``illustType`` (0 illust, 1 manga, 2 ugoira),
        ``urls`` with ``mini``/``thumb``/``small``/``regular``/``original``
        addresses, ``width``, ``height``, ``pageCount``, ``createDate``,
        ``xRestrict``, ``sl``, ``tags`` (``authorId`` plus a ``tags`` array of
        ``tag``/``translatedName``), and view/bookmark counters. A live read
        of ``149040133`` returned 200 with that envelope and ``body.pageCount``
        1.

        Example:
            ``client.web_illust_show('149040133')``
        """
        return self.request(
            "GET", "ajax/illust/{}".format(quote(str(illust_id), safe="")),
            params=params)

    def web_illust_pages(self, illust_id, **params):
        """Read the per-page image addresses of one illustration
        (``GET ajax/illust/<id>/pages``).

        ``illust_id`` is the illustration number, as in ``web_illust_show``.
        ``params`` carries ``lang`` when wanted.

        Returns the ``{"error", "message", "body"}`` envelope, where ``body``
        is an array with one entry per page in reading order. Each entry holds
        ``width``, ``height`` and ``urls`` with ``thumb_mini``, ``small``,
        ``regular`` and ``original`` addresses. A live read of ``149040133``
        returned 200 with a one-entry ``body``. The client downloads none of
        them.

        Example:
            ``client.web_illust_pages('149040133')``
        """
        return self.request(
            "GET", "ajax/illust/{}/pages".format(quote(str(illust_id), safe="")),
            params=params)

    def web_ugoira_metadata(self, illust_id, **params):
        """Read a ugoira illustration's frame data
        (``GET ajax/illust/<id>/ugoira_meta``).

        ``illust_id`` is a ugoira illustration's number, as in
        ``web_illust_show``. ``params`` carries ``lang`` when wanted.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``src`` and ``originalSrc`` (the zip addresses on ``i.pximg.net``),
        ``mime_type`` and ``frames``, an array of ``{"file": ..., "delay":
        <ms>}``. The zip addresses are returned as strings; nothing is
        downloaded. Only illustrations whose ``illustType`` is 2 have this
        metadata.

        Example:
            ``client.web_ugoira_metadata('149040133')``
        """
        return self.request(
            "GET",
            "ajax/illust/{}/ugoira_meta".format(quote(str(illust_id), safe="")),
            params=params)

    def web_illust_new(self, **params):
        """List newly posted illustrations (``GET ajax/illust/new``).

        ``params`` carries ``lastId`` (the cursor, the last seen id),
        ``limit``, ``type`` (``illust``/``manga``/``all``) and ``r18`` as
        given. A probe sending ``lastId=0&limit=2&type=illust&r18=False``
        answered 400, so this route is parameter-sensitive and its anonymous
        contract is not established.

        Returns the ``{"error", "message", "body"}`` envelope with the
        new-work entries shaped like the search entries.

        Example:
            ``client.web_illust_new(limit=10, type='illust')``
        """
        return self.request("GET", "ajax/illust/new", params=params)

    def web_illust_recommend_init(self, illust_id, **params):
        """Read the first page of an illustration's related works
        (``GET ajax/illust/<id>/recommend/init``).

        ``illust_id`` is the illustration number, as in ``web_illust_show``.
        ``params`` carries ``limit`` and ``lang``.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``illusts`` (the recommended works), ``nextIds`` (the ids to pass to
        ``web_illust_recommend_illusts`` for more) and ``details``. A live read
        of ``149040133`` with ``limit=2`` returned 200 with that envelope.

        Example:
            ``client.web_illust_recommend_init('149040133', limit=2)``
        """
        return self.request(
            "GET",
            "ajax/illust/{}/recommend/init".format(quote(str(illust_id), safe="")),
            params=params)

    def web_illust_recommend_illusts(self, illust_ids, **params):
        """Read more related works for a set of illustrations
        (``GET ajax/illust/recommend/illusts``).

        ``illust_ids`` is the list ``web_illust_recommend_init`` returned as
        ``nextIds``, sent through the shared encoder as repeated
        ``illust_ids[]`` query pairs. ``params`` carries ``lang`` and is sent
        normally.

        Returns the ``{"error", "message", "body"}`` envelope whose ``body``
        holds ``illusts``. A live read with two ids as ``illust_ids[]``
        returned 200 with that body; the same request with unbracketed
        ``illust_ids`` returned 400, which is why the bracketed form above is
        the one used.

        Example:
            ``client.web_illust_recommend_illusts(['147208254', '143484250'])``
        """
        return self.request("GET", "ajax/illust/recommend/illusts",
                            params=dict(params, illust_ids=illust_ids))

    def web_illust_discovery(self, **params):
        """List the older illustration discover feed
        (``GET ajax/illust/discovery``).

        ``params`` carries ``mode`` (``safe``/``all``) and ``max`` as given.
        A live read with ``mode=safe&max=2`` returned 200.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``recommendations`` and ``thumbnails``.

        Example:
            ``client.web_illust_discovery(mode='safe', max=18)``
        """
        return self.request("GET", "ajax/illust/discovery", params=params)

    def web_illust_series(self, series_id, **params):
        """Read one illustration series (``GET ajax/series/<id>``).

        ``series_id`` is the series number. ``params`` carries ``p`` (page)
        and ``lang``.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        the series ``id``/``title`` and ``thumbnails``/``page`` data. Only
        series-scoped works appear here; a series is otherwise visible in an
        illustration's own detail body.

        Example:
            ``client.web_illust_series('12345')``
        """
        return self.request(
            "GET", "ajax/series/{}".format(quote(str(series_id), safe="")),
            params=params)

    def web_illust_comments(self, illust_id, **params):
        """List one illustration's top-level comments
        (``GET ajax/illusts/comments/roots``).

        ``illust_id`` is sent as the ``illust_id`` query value; ``params``
        carries ``offset``, ``limit`` and ``lang`` as given.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``comments`` (each with ``id``, ``comment``, ``user``, ``date`` and
        reply data) and ``hasNext``. A live read of ``149040133`` with
        ``offset=0&limit=2`` returned 200 with that envelope. Replies to a
        comment are ``web_illust_comment_replies``.

        Example:
            ``client.web_illust_comments('149040133', offset=0, limit=2)``
        """
        return self.request("GET", "ajax/illusts/comments/roots",
                            params=dict(params, illust_id=illust_id))

    def web_illust_comment_replies(self, comment_id, **params):
        """List the replies to one illustration comment
        (``GET ajax/illusts/comments/replies``).

        ``comment_id`` is sent as the ``comment_id`` query value; ``params``
        carries ``page`` and ``lang`` as given.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``comments`` and ``hasNext``.

        Example:
            ``client.web_illust_comment_replies('123456789')``
        """
        return self.request("GET", "ajax/illusts/comments/replies",
                            params=dict(params, comment_id=comment_id))

    # ------------------------------------------------------------------
    # Web host: novels
    # ------------------------------------------------------------------

    def web_novel_show(self, novel_id, **params):
        """Read one novel (``GET ajax/novel/<id>``).

        ``novel_id`` is the novel number, from a URL such as
        ``https://www.pixiv.net/novel/show.php?id=12345678``. ``params``
        carries ``lang``.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``id``, ``title``, ``content`` (the novel text), ``userId``,
        ``userName``, ``coverUrl``, ``tags``, ``seriesNavData`` and share
        counts. A live read of a novel id returned 200 with that envelope.

        Example:
            ``client.web_novel_show('12345678')``
        """
        return self.request(
            "GET", "ajax/novel/{}".format(quote(str(novel_id), safe="")),
            params=params)

    def web_user_novels(self, user_id, **params):
        """Read several of one user's novels at once
        (``GET ajax/user/<id>/novels``).

        ``user_id`` is the user number. ``params`` carries ``ids`` (a list,
        encoded as repeated ``ids[]`` query pairs) and ``lang``.

        Returns the ``{"error", "message", "body"}`` envelope, whose ``body``
        is keyed by novel id with the novel data.

        Example:
            ``client.web_user_novels('27517', ids=['12345678'])``
        """
        return self.request(
            "GET", "ajax/user/{}/novels".format(quote(str(user_id), safe="")),
            params=params)

    def web_novel_discovery(self, **params):
        """List the older novel discover feed (``GET ajax/novel/discovery``).

        ``params`` carries ``mode`` (``safe``/``all``) and ``limit``. A live
        read with ``mode=safe`` returned 200.

        Returns the ``{"error", "message", "body"}`` envelope with ``novels``
        and ``details``.

        Example:
            ``client.web_novel_discovery(mode='safe')``
        """
        return self.request("GET", "ajax/novel/discovery", params=params)

    def web_novel_new(self, **params):
        """List newly posted novels (``GET ajax/novel/new``).

        ``params`` carries ``lastId``, ``limit``, ``r18`` and ``lang`` as
        given.

        Returns the ``{"error", "message", "body"}`` envelope with the novel
        entries.

        Example:
            ``client.web_novel_new(limit=10)``
        """
        return self.request("GET", "ajax/novel/new", params=params)

    def web_novel_recommend_init(self, novel_id, **params):
        """Read the first page of a novel's related novels
        (``GET ajax/novel/<id>/recommend/init``).

        ``novel_id`` is the novel number. ``params`` carries ``limit`` and
        ``lang``.

        Returns the ``{"error", "message", "body"}`` envelope with ``novels``,
        ``nextIds`` and ``details``. A live read with ``limit=2`` returned 200.

        Example:
            ``client.web_novel_recommend_init('12345678', limit=2)``
        """
        return self.request(
            "GET",
            "ajax/novel/{}/recommend/init".format(quote(str(novel_id), safe="")),
            params=params)

    def web_novel_recommend_novels(self, **params):
        """List more related novels for a set of novels
        (``GET ajax/novel/recommend/novels``).

        ``params`` carries ``novelIds`` (a list, sent as repeated
        ``novelIds[]`` query pairs) and ``lang``.

        Returns the ``{"error", "message", "body"}`` envelope with ``novels``.

        Example:
            ``client.web_novel_recommend_novels(novelIds=['12345678'])``
        """
        return self.request("GET", "ajax/novel/recommend/novels", params=params)

    def web_novel_editors_picks(self, **params):
        """List the editors' picks novels (``GET ajax/novel/editors_picks``).

        ``params`` carries ``limit`` and ``lang``. Returns the
        ``{"error", "message", "body"}`` envelope with the picked novels.

        Example:
            ``client.web_novel_editors_picks(limit=10)``
        """
        return self.request("GET", "ajax/novel/editors_picks", params=params)

    def web_top_novel(self, **params):
        """Read the novel home page content (``GET ajax/top/novel``).

        ``params`` carries ``mode`` and ``lang``. Returns the
        ``{"error", "message", "body"}`` envelope with the homepage blocks.

        Example:
            ``client.web_top_novel(mode='all')``
        """
        return self.request("GET", "ajax/top/novel", params=params)

    def web_novel_genre(self, genre, **params):
        """List novels of one genre (``GET ajax/genre/novel/<genre>``).

        ``genre`` is a genre key (for example ``original`` or a numeric genre
        id) quoted as one path segment. ``params`` carries ``mode`` and
        ``lang``. Returns the ``{"error", "message", "body"}`` envelope with
        the genre listing.

        Example:
            ``client.web_novel_genre('original')``
        """
        return self.request(
            "GET", "ajax/genre/novel/{}".format(quote(str(genre), safe="")),
            params=params)

    def web_novel_bookmark_data(self, novel_id, **params):
        """Read the signed-in user's bookmark data for one novel
        (``GET ajax/novel/<id>/bookmarkData``).

        ``novel_id`` is the novel number; ``params`` carries ``lang``.
        Returns the ``{"error", "message", "body"}`` envelope with ``id``,
        ``isBookmarkable`` and ``bookmarkData``; without a session the
        bookmark-specific values are the site's own empty/absent answer.

        Example:
            ``client.web_novel_bookmark_data('12345678')``
        """
        return self.request(
            "GET",
            "ajax/novel/{}/bookmarkData".format(quote(str(novel_id), safe="")),
            params=params)

    def web_novel_comments(self, novel_id, **params):
        """List one novel's top-level comments
        (``GET ajax/novels/comments/roots``).

        ``novel_id`` is sent as the ``novel_id`` query value; ``params``
        carries ``offset``, ``limit`` and ``lang``. Returns the
        ``{"error", "message", "body"}`` envelope with ``comments`` and
        ``hasNext``.

        Example:
            ``client.web_novel_comments('12345678', offset=0, limit=2)``
        """
        return self.request("GET", "ajax/novels/comments/roots",
                            params=dict(params, novel_id=novel_id))

    def web_novel_comment_replies(self, comment_id, **params):
        """List the replies to one novel comment
        (``GET ajax/novels/comments/replies``).

        ``comment_id`` is sent as the ``comment_id`` query value; ``params``
        carries ``page`` and ``lang``. Returns the ``{"error", "message",
        "body"}`` envelope with ``comments`` and ``hasNext``.

        Example:
            ``client.web_novel_comment_replies('123456789')``
        """
        return self.request("GET", "ajax/novels/comments/replies",
                            params=dict(params, comment_id=comment_id))

    def web_novel_series(self, series_id, **params):
        """Read one novel series (``GET ajax/novel/series/<id>``).

        ``series_id`` is the series number; ``params`` carries ``lang``.
        Returns the ``{"error", "message", "body"}`` envelope with ``id``,
        ``title``, ``caption``, ``publishedContentCount``, ``firstNovelId``
        and ``latestNovelId``.

        Example:
            ``client.web_novel_series('12345')``
        """
        return self.request(
            "GET", "ajax/novel/series/{}".format(quote(str(series_id), safe="")),
            params=params)

    def web_novel_series_content(self, series_id, **params):
        """List the novels inside one novel series
        (``GET ajax/novel/series_content/<id>``).

        ``series_id`` is the series number. ``params`` carries ``limit``,
        ``last_order``, ``order_by``, ``page``, ``size`` and ``lang`` as
        given. ``order_by`` is documented by the source as ``asc``, ``dsc``
        (the source's spelling, kept literal) or a string; it is not silently
        normalised. Returns the ``{"error", "message", "body"}`` envelope
        whose ``body`` holds ``thumbnails`` (``illust`` and ``novel`` arrays),
        ``tagTranslation``, ``illustSeries``, ``requests``, ``users`` and
        ``page``, whose ``page.seriesContents`` array is the series' novels. A
        live read with ``limit=2&last_order=0&order_by=asc`` returned 200 with
        those keys.

        Example:
            ``client.web_novel_series_content('12345', limit=10, order_by='asc')``
        """
        return self.request(
            "GET",
            "ajax/novel/series_content/{}".format(quote(str(series_id), safe="")),
            params=params)

    def web_novel_series_titles(self, series_id, **params):
        """List the titles in one novel series
        (``GET ajax/novel/series/<id>/content_titles``).

        ``series_id`` is the series number; ``params`` carries ``lang``.
        Returns the ``{"error", "message", "body"}`` envelope whose ``body``
        is an array of ``{"id", "title", "available"}`` -- a live read showed
        no ``order`` field, so none is claimed.

        Example:
            ``client.web_novel_series_titles('12345')``
        """
        return self.request(
            "GET",
            "ajax/novel/series/{}/content_titles".format(
                quote(str(series_id), safe="")),
            params=params)

    # ------------------------------------------------------------------
    # Web host: search
    # ------------------------------------------------------------------

    def web_search_artworks(self, word, **params):
        """Search illustrations and manga by keyword
        (``GET ajax/search/artworks/<word>``).

        ``word`` is the keyword, one quoted path segment; it is also sent as
        the ``word`` query value, which is what the site's own front end does,
        and a ``word`` in ``params`` cannot displace it. ``params`` is the
        search query forwarded unchanged. The site's own values are ``order``
        (``date_d`` newest first, ``date`` oldest first, ``popular_d`` most
        bookmarked), ``mode`` (``all``, ``safe``, ``r18``), ``s_mode``
        (``s_tag`` tag match, ``s_tag_full`` exact tag, ``s_tc``
        title/caption), ``type`` (``all``, ``illust``, ``manga``), ``p`` (page
        number, 1-based), and the advanced filters ``ai_type``, ``dgw``,
        ``wlt``/``wgt``, ``hlt``/``hgt``, ``ratio``, ``tool``, ``scd``/``ecd``
        (start/end date) and ``blt``/``bgt`` (bookmark counts). Nothing is
        filled in or clamped.

        Returns the ``{"error", "body"}`` envelope. ``body.illustManga`` holds
        ``data``, ``total`` and ``lastPage``; ``body`` also holds ``popular``,
        ``relatedTags``, ``tagTranslation``, ``zoneConfig``, ``extraData`` and
        ``suggestChips``. Each entry has ``id``, ``title``, ``illustType``,
        ``url``, ``tags``, ``userId``, ``userName``, ``width``, ``height``,
        ``pageCount``, ``xRestrict`` and ``sl``. A live read of ``cat`` with
        ``order=date_d&mode=all&p=2&s_mode=s_tag&type=all`` returned 200 with
        that shape; ``p=10000`` still returned 200, so a short ``data`` is not
        proof of the end -- ``illustManga.lastPage`` is.

        Example:
            ``client.web_search_artworks('cat', order='date_d', mode='all',
            p=1, s_mode='s_tag', type='all')``
        """
        return self.request(
            "GET", "ajax/search/artworks/{}".format(quote(str(word), safe="")),
            params=dict(params, word=word))

    def web_search_illustrations(self, word, **params):
        """Search illustrations only (``GET ajax/search/illustrations/<word>``).

        ``word`` is one quoted path segment and is also sent as the ``word``
        query value. ``params`` is the search query forwarded unchanged, with
        the same names as ``web_search_artworks`` and ``type`` limited to
        ``illust_and_ugoira``, ``illust`` or ``ugoira``.

        Returns the ``{"error", "body"}`` envelope, where ``body.illust``
        holds ``data``, ``total`` and ``lastPage`` (the other body blocks are
        the same as ``web_search_artworks``).

        Example:
            ``client.web_search_illustrations('cat', p=1, type='illust')``
        """
        return self.request(
            "GET",
            "ajax/search/illustrations/{}".format(quote(str(word), safe="")),
            params=dict(params, word=word))

    def web_search_manga(self, word, **params):
        """Search manga only (``GET ajax/search/manga/<word>``).

        ``word`` is one quoted path segment and is also sent as the ``word``
        query value. ``params`` is the search query forwarded unchanged, with
        the same names as ``web_search_artworks`` plus ``work_lang`` and
        ``type='manga'``.

        Returns the ``{"error", "body"}`` envelope, where ``body.manga`` holds
        ``data``, ``total`` and ``lastPage``.

        Example:
            ``client.web_search_manga('cat', p=1)``
        """
        return self.request(
            "GET", "ajax/search/manga/{}".format(quote(str(word), safe="")),
            params=dict(params, word=word))

    def web_search_novels(self, word, **params):
        """Search novels by keyword (``GET ajax/search/novels/<word>``).

        ``word`` is one quoted path segment and is also sent as the ``word``
        query value. ``params`` is the search query forwarded unchanged: the
        names ``order``, ``mode``, ``p`` and ``s_mode`` as at
        ``web_search_artworks``, plus ``work_lang``, ``gs``, ``tlt``/``tgt``,
        ``wlt``/``wgt``, ``original_only``, ``genre`` and ``csw``.

        Returns the ``{"error", "body"}`` envelope, where ``body.novel`` holds
        ``data``, ``total`` and ``lastPage``. A live read of ``cat`` returned
        200.

        Example:
            ``client.web_search_novels('cat', order='date_d', p=1)``
        """
        return self.request(
            "GET", "ajax/search/novels/{}".format(quote(str(word), safe="")),
            params=dict(params, word=word))

    def web_search_top(self, word, **params):
        """Read the aggregated search page for a keyword
        (``GET ajax/search/top/<word>``).

        ``word`` is one quoted path segment and is also sent as the ``word``
        query value; ``params`` carries ``lang``. Returns the ``{"error",
        "body"}`` envelope with ``novel``, ``illust``, ``manga``, ``popular``
        and ``relatedTags``.

        Example:
            ``client.web_search_top('cat')``
        """
        return self.request(
            "GET", "ajax/search/top/{}".format(quote(str(word), safe="")),
            params=dict(params, word=word))

    def web_search_tags(self, tag, **params):
        """Read the search page for one tag (``GET ajax/search/tags/<tag>``).

        ``tag`` is one quoted path segment; ``params`` carries ``lang``.
        Returns the ``{"error", "body"}`` envelope with ``tag``, ``word``,
        ``pixpedia``, ``breadcrumbs`` and ``tagTranslation``.

        Example:
            ``client.web_search_tags('初音ミク')``
        """
        return self.request(
            "GET", "ajax/search/tags/{}".format(quote(str(tag), safe="")),
            params=params)

    def web_search_users(self, **params):
        """Search users (``GET ajax/search/users``).

        ``params`` carries ``nick`` (the nickname to match), ``s_mode``,
        ``i`` (page number) and ``lang`` as given. Returns the ``{"error",
        "message", "body"}`` envelope with the user entries and a page block.

        Example:
            ``client.web_search_users(nick='cat')``
        """
        return self.request("GET", "ajax/search/users", params=params)

    def web_search_suggestion(self, **params):
        """Read search suggestions (``GET ajax/search/suggestion``).

        ``params`` carries ``mode`` and ``lang``. Returns the ``{"error",
        "message", "body"}`` envelope with ``popularTags``, ``recommendTags``,
        ``recommendByTags``, ``myFavoriteTags``, ``tagTranslation`` and
        ``thumbnails``.

        Example:
            ``client.web_search_suggestion(mode='all')``
        """
        return self.request("GET", "ajax/search/suggestion", params=params)

    def web_search_autocomplete(self, keyword, **params):
        """Read keyword autocompletion (``GET rpc/cps.php``).

        ``keyword`` is sent as the ``keyword`` query value (this route's own
        key); ``params`` carries ``lang``. Returns a bare object with a
        ``candidates`` array, each entry holding ``access_count``,
        ``tag_name``, ``tag_translation`` and ``type``.

        Example:
            ``client.web_search_autocomplete('初音')``
        """
        return self.request("GET", "rpc/cps.php",
                            params=dict(params, keyword=keyword))

    # ------------------------------------------------------------------
    # Web host: users
    # ------------------------------------------------------------------

    def web_user_show(self, user_id, **params):
        """Read one user's profile (``GET ajax/user/<id>``).

        ``user_id`` is the user number, taken from a profile URL such as
        ``https://www.pixiv.net/users/27517`` or from an illustration's
        ``userId``. It is quoted as one path segment. ``params`` is forwarded
        unchanged; ``full=1`` asks for the fuller profile the site's own page
        loads, and is not sent unless passed.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``userId``, ``name``, ``image``/``imageBig``, ``comment`` and
        ``commentHtml``, ``webpage``, ``social``, ``following``,
        ``mypixivCount``, ``premium``, ``isFollowed``, ``background``, and the
        privacy-gated ``region``/``birthDay``/``gender``/``job``/``workspace``
        blocks, each with its own ``privacyLevel``. A live read of ``27517``
        with ``full=1`` returned 200 with ``body.name`` and ``body.userId``
        set.

        Example:
            ``client.web_user_show('27517', full=1)``
        """
        return self.request(
            "GET", "ajax/user/{}".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_profile_all(self, user_id, **params):
        """Read the id index of everything one user has posted
        (``GET ajax/user/<id>/profile/all``).

        ``user_id`` is the user number; ``params`` carries ``lang``.

        Returns the ``{"error", "message", "body"}`` envelope. ``body`` holds
        ``illusts`` and ``manga`` as objects keyed by work id (each value
        ``null``), ``novels``/``mangaSeries``/``novelSeries``/``collections``/
        ``collectionIds``/``pickup`` arrays, ``bookmarkCount`` split into
        ``public``/``private`` per work type, ``externalSiteWorksStatus``,
        ``request`` and ``shouldShowSensitiveNotice``. A live read of ``27517``
        returned 200 with hundreds of ids in ``body.illusts``. The ids are the
        input to ``web_illust_show`` and ``web_user_profile_illusts``; no work
        bodies are fetched here.

        Example:
            ``client.web_user_profile_all('27517')``
        """
        return self.request(
            "GET", "ajax/user/{}/profile/all".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_profile_top(self, user_id, **params):
        """Read one user's pinned/top works (``GET ajax/user/<id>/profile/top``).

        ``user_id`` is the user number; ``params`` carries ``lang``. Returns
        the ``{"error", "message", "body"}`` envelope with ``illusts``,
        ``manga``, ``novels`` and ``pickup``. A live read of ``27517``
        returned 200; the exact top-level keys of ``body`` are read from the
        source and can differ from this list.

        Example:
            ``client.web_user_profile_top('27517')``
        """
        return self.request(
            "GET", "ajax/user/{}/profile/top".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_profile_illusts(self, user_id, **params):
        """Read several of one user's works at once
        (``GET ajax/user/<id>/profile/illusts``).

        ``user_id`` is the user number. ``params`` carries ``ids`` (a list,
        encoded as repeated ``ids[]`` query pairs), ``work_category``
        (``illustManga``/``manga``) and ``is_first_page``. Returns the
        ``{"error", "message", "body"}`` envelope, whose ``body`` has a
        ``works`` object keyed by work id. A live read of ``27517`` with two
        ids returned 200.

        Example:
            ``client.web_user_profile_illusts('27517',
            ids=['149040133'], work_category='illustManga', is_first_page=1)``
        """
        return self.request(
            "GET",
            "ajax/user/{}/profile/illusts".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_profile_novels(self, user_id, **params):
        """Read several of one user's novels at once
        (``GET ajax/user/<id>/profile/novels``).

        ``user_id`` is the user number. ``params`` carries ``ids`` (a list)
        and ``is_first_page``. Returns the ``{"error", "message", "body"}``
        envelope, whose ``body`` has a ``works`` object keyed by novel id,
        plus ``zoneConfig`` and ``extraData``. A live read of two ids returned
        200 with those keys.

        Example:
            ``client.web_user_profile_novels('27517', ids=['12345678'])``
        """
        return self.request(
            "GET",
            "ajax/user/{}/profile/novels".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_illusts(self, user_id, **params):
        """Read several illustrations of one user at once
        (``GET ajax/user/<id>/illusts``).

        ``user_id`` is the user number. ``params`` carries ``ids`` (a list)
        and ``lang``. Returns the ``{"error", "message", "body"}`` envelope
        keyed by illustration id.

        Example:
            ``client.web_user_illusts('27517', ids=['149040133'])``
        """
        return self.request(
            "GET", "ajax/user/{}/illusts".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_meta(self, user_id, **params):
        """Read one user's meta block (``GET ajax/user/<id>/meta``).

        ``user_id`` is the user number; ``params`` carries ``lang``. Returns
        the ``{"error", "message", "body"}`` envelope with the meta values the
        profile page uses.

        Example:
            ``client.web_user_meta('27517')``
        """
        return self.request(
            "GET", "ajax/user/{}/meta".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_works_latest(self, user_id, **params):
        """Read one user's latest works (``GET ajax/user/<id>/works/latest``).

        ``user_id`` is the user number; ``params`` carries ``lang``. Returns
        the ``{"error", "message", "body"}`` envelope with ``illusts`` and
        ``novels``.

        Example:
            ``client.web_user_works_latest('27517')``
        """
        return self.request(
            "GET", "ajax/user/{}/works/latest".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_following(self, user_id, **params):
        """List the users one user follows (``GET ajax/user/<id>/following``).

        ``user_id`` is the user number. ``params`` carries ``offset``,
        ``limit``, ``rest`` (``show``/``hide``) and ``lang``. A live anonymous
        read of ``27517`` returned 400, so this route needs a session cookie
        for a private list and its anonymous contract is not established.

        Returns the ``{"error", "message", "body"}`` envelope with ``users``,
        ``total`` and ``followUserTags``.

        Example:
            ``client.web_user_following('27517', offset=0, limit=24)``
        """
        return self.request(
            "GET", "ajax/user/{}/following".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_followers(self, user_id, **params):
        """List the users following one user (``GET ajax/user/<id>/followers``).

        ``user_id`` is the user number; ``params`` carries ``offset``,
        ``limit`` and ``lang``. Returns the ``{"error", "message", "body"}``
        envelope with the follower entries.

        Example:
            ``client.web_user_followers('27517', offset=0, limit=24)``
        """
        return self.request(
            "GET", "ajax/user/{}/followers".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_recommends(self, user_id, **params):
        """List users recommended alongside one user
        (``GET ajax/user/<id>/recommends``).

        ``user_id`` is the user number. ``params`` carries ``userNum``,
        ``workNum``, ``isR18`` and ``lang``. Returns the ``{"error",
        "message", "body"}`` envelope with ``recommendUsers`` and
        ``thumbnails``.

        Example:
            ``client.web_user_recommends('27517', userNum=10)``
        """
        return self.request(
            "GET", "ajax/user/{}/recommends".format(quote(str(user_id), safe="")),
            params=params)

    def web_user_tagged(self, user_id, work_type, **params):
        """List one user's works carrying a tag
        (``GET ajax/user/<id>/<work_type>/tag``).

        ``user_id`` is the user number and ``work_type`` one of ``illusts``,
        ``manga``, ``illustmanga`` or ``novels``; both are quoted path
        segments and neither is validated here, so an unknown value reaches
        the site's own route. ``params`` carries ``tag``, ``offset``,
        ``limit`` and ``lang``. Returns the ``{"error", "message", "body"}``
        envelope with the works and a ``total``.

        Example:
            ``client.web_user_tagged('27517', 'illusts', tag='cat')``
        """
        return self.request(
            "GET", "ajax/user/{}/{}/tag".format(
                quote(str(user_id), safe=""), quote(str(work_type), safe="")),
            params=params)

    def web_user_tags(self, user_id, work_type, **params):
        """List one user's tags (``GET ajax/user/<id>/<work_type>/tags``).

        ``user_id`` is the user number and ``work_type`` one of ``illusts``,
        ``manga``, ``illustmanga`` or ``novels``; both are quoted path
        segments. ``params`` carries ``all`` and ``lang``. Returns the
        ``{"error", "message", "body"}`` envelope whose ``body`` is an array
        of ``tag``/``count`` entries.

        Example:
            ``client.web_user_tags('27517', 'illusts')``
        """
        return self.request(
            "GET", "ajax/user/{}/{}/tags".format(
                quote(str(user_id), safe=""), quote(str(work_type), safe="")),
            params=params)

    def web_user_bookmarks(self, user_id, work_type, **params):
        """List one user's bookmarks (``GET ajax/user/<id>/<work_type>/bookmarks``).

        ``user_id`` is the user number and ``work_type`` one of ``illusts`` or
        ``novels``; both are quoted path segments. ``params`` carries ``tag``,
        ``offset``, ``limit``, ``rest`` and ``lang``. A live anonymous read of
        illusts bookmarks for ``27517`` returned 400, so a private listing
        needs the owner's session cookie; the public one is the site's
        decision. Returns the ``{"error", "message", "body"}`` envelope with
        the works and a ``total``.

        Example:
            ``client.web_user_bookmarks('27517', 'illusts', offset=0, limit=24,
            rest='show')``
        """
        return self.request(
            "GET", "ajax/user/{}/{}/bookmarks".format(
                quote(str(user_id), safe=""), quote(str(work_type), safe="")),
            params=params)

    def web_user_bookmark_tags(self, user_id, work_type, **params):
        """List the bookmark tags of one user
        (``GET ajax/user/<id>/<work_type>/bookmark/tags``).

        ``user_id`` is the user number and ``work_type`` one of ``illusts`` or
        ``novels``; both are quoted path segments. ``params`` carries ``lang``.
        Returns the ``{"error", "message", "body"}`` envelope with ``public``,
        ``private``, ``tooManyBookmark`` and ``tooManyBookmarkTags``.

        Example:
            ``client.web_user_bookmark_tags('27517', 'illusts')``
        """
        return self.request(
            "GET", "ajax/user/{}/{}/bookmark/tags".format(
                quote(str(user_id), safe=""), quote(str(work_type), safe="")),
            params=params)

    def web_user_extra(self, **params):
        """Read the extra sidebar user block for the signed-in account
        (``GET ajax/user/extra``).

        ``params`` carries ``is_smartphone``, ``version`` and ``lang``.
        Returns the ``{"error", "message", "body"}`` envelope with
        ``background``, ``followers``, ``following`` and ``mypixivCount``;
        without a session the account-specific values are the site's own.

        Example:
            ``client.web_user_extra(is_smartphone=1)``
        """
        return self.request("GET", "ajax/user/extra", params=params)

    # ------------------------------------------------------------------
    # Web host: feeds and discovery
    # ------------------------------------------------------------------

    def web_follow_latest(self, work_type, **params):
        """List the latest works from the followed accounts
        (``GET ajax/follow_latest/<work_type>``).

        ``work_type`` is ``illust`` or ``novel``, one quoted path segment.
        ``params`` carries ``mode``, ``p`` and ``lang``. A live anonymous read
        of the illust feed returned 400, so this route needs a session cookie.
        Returns the ``{"error", "message", "body"}`` envelope with ``page``
        and ``thumbnails``.

        Example:
            ``client.web_follow_latest('illust', mode='all', p=1)``
        """
        return self.request(
            "GET", "ajax/follow_latest/{}".format(quote(str(work_type), safe="")),
            params=params)

    def web_mypixiv_latest(self, **params):
        """List the latest works from MyPixiv (``GET ajax/mypixiv_latest/illust``).

        ``params`` carries ``p`` and ``lang``. Returns the ``{"error",
        "message", "body"}`` envelope with the MyPixiv feed.

        Example:
            ``client.web_mypixiv_latest(p=1)``
        """
        return self.request("GET", "ajax/mypixiv_latest/illust", params=params)

    def web_watch_list(self, work_type, **params):
        """List watched series (``GET ajax/watch_list/<work_type>``).

        ``work_type`` is ``manga`` or ``novel``, one quoted path segment.
        ``params`` carries ``p``, ``new`` and ``lang``. Returns the
        ``{"error", "message", "body"}`` envelope with the watched-series
        listing.

        Example:
            ``client.web_watch_list('manga', p=1)``
        """
        return self.request(
            "GET", "ajax/watch_list/{}".format(quote(str(work_type), safe="")),
            params=params)

    def web_street(self, section, **params):
        """Read one home-page section (``GET ajax/street/<section>``).

        ``section`` is one of ``recommend_tags``, ``latest``, ``sub`` or
        ``for_you``, one quoted path segment. ``params`` carries ``lang``.
        Returns the ``{"error", "message", "body"}`` envelope with that
        section's content. This is where the home page's "trending" tags come
        from -- there is no separate trending route.

        Example:
            ``client.web_street('recommend_tags')``
        """
        return self.request(
            "GET", "ajax/street/{}".format(quote(str(section), safe="")),
            params=params)

    def web_top_illust(self, **params):
        """Read the illustration home page content (``GET ajax/top/illust``).

        ``params`` carries ``mode`` and ``lang``. A live anonymous read
        returned 400, so this route needs a session cookie. Returns the
        ``{"error", "message", "body"}`` envelope with the homepage blocks.

        Example:
            ``client.web_top_illust(mode='all')``
        """
        return self.request("GET", "ajax/top/illust", params=params)

    def web_discovery_artworks(self, **params):
        """Read the current artwork discovery feed
        (``GET ajax/discovery/artworks``).

        ``params`` carries ``mode``, ``limit`` and ``lang``. A live anonymous
        read with ``mode=all&limit=2`` returned 400 (not 401), so this route
        needs a session cookie. Returns the ``{"error", "message", "body"}``
        envelope with ``thumbnails`` and ``recommendations``.

        Example:
            ``client.web_discovery_artworks(mode='all', limit=18)``
        """
        return self.request("GET", "ajax/discovery/artworks", params=params)

    def web_discovery_novels(self, **params):
        """Read the current novel discovery feed
        (``GET ajax/discovery/novels``).

        ``params`` carries ``mode``, ``limit`` and ``lang``. Returns the
        ``{"error", "message", "body"}`` envelope with ``thumbnails``,
        ``recommendedNovelIds`` and ``recommendNovelDetails``.

        Example:
            ``client.web_discovery_novels(mode='all', limit=18)``
        """
        return self.request("GET", "ajax/discovery/novels", params=params)

    def web_discovery_users(self, **params):
        """Read the user discovery feed (``GET ajax/discovery/users``).

        ``params`` carries ``limit`` and ``lang``. Returns the ``{"error",
        "message", "body"}`` envelope with ``users`` and ``thumbnails``.

        Example:
            ``client.web_discovery_users(limit=18)``
        """
        return self.request("GET", "ajax/discovery/users", params=params)

    # ------------------------------------------------------------------
    # Web host: ranking
    # ------------------------------------------------------------------

    def web_ranking(self, **params):
        """Read an illustration ranking page (``GET ranking.php``).

        ``params`` is the ranking query forwarded unchanged, with
        ``format='json'`` added first as this route's JSON-format protocol
        step; passing ``format`` yourself replaces it. The site's own values
        are ``mode`` (``daily``; also ``weekly``, ``monthly``, ``rookie``,
        ``daily_r18`` and the ``*_male``/``*_female``/``*_manga`` variants),
        ``content`` (``all``/``illust``/``manga``), ``date`` (``YYYYMMDD``)
        and ``p`` (page number, 1-based). Nothing else is filled in.

        Returns a bare object with no envelope: ``contents`` (the ranked
        entries), ``content`` (``illust`` or ``manga``), ``mode``, ``page``,
        ``prev``, ``next``, ``date``, ``prev_date``, ``next_date``,
        ``rank_total``, ``date_range_text``, ``meta`` and ``zoneConfig``. Each
        entry has ``rank``, ``yes_rank``, ``illust_id``, ``title``, ``url``,
        ``user_id``, ``user_name``, ``profile_img``, ``illust_type``,
        ``illust_page_count``, ``illust_content_type``, ``tags``, ``width``,
        ``height``, ``rating_count``, ``view_count`` and ``date``. Live reads
        of ``mode=daily`` returned 200 with ``page`` 1 and 2 and a populated
        ``contents``; ``p=10000`` returned 404 with the bare
        ``{"error": "<message>"}`` object, kept as the raised error's data.

        Example:
            ``client.web_ranking(mode='daily', p=1)``
        """
        query = {"format": "json"}
        query.update(params)
        return self.request("GET", "ranking.php", params=query)

    def web_novel_ranking(self, **params):
        """Read a novel ranking page (``GET ajax/ranking/novel``).

        ``params`` carries ``mode``, ``date``, ``p``, ``content`` and ``lang``
        as given; unlike ``ranking.php`` this route is already JSON. Returns
        the ``{"error", "body"}`` envelope with ``display_a`` (``rank_a``,
        ``date``, ``start``, ``end``, ``h_title`` and the novel entries). A
        live read with ``mode=daily&p=1`` returned 200.

        Example:
            ``client.web_novel_ranking(mode='daily', p=1)``
        """
        return self.request("GET", "ajax/ranking/novel", params=params)

    # ------------------------------------------------------------------
    # Web host: showcase and tags
    # ------------------------------------------------------------------

    def web_showcase_article(self, article_id, **params):
        """Read one spotlight/showcase article (``GET ajax/showcase/article``).

        ``article_id`` is sent as the ``article_id`` query value (this route's
        key, not a path segment); ``params`` carries ``lang``. Returns the
        ``{"error", "message", "body"}`` envelope with the article's metadata
        and its ``illusts``/``novels`` blocks. This route is reached with the
        web ``Referer`` this client sends by default.

        Example:
            ``client.web_showcase_article('123')``
        """
        return self.request("GET", "ajax/showcase/article",
                            params=dict(params, article_id=article_id))

    def web_tag_info(self, tag, **params):
        """Read one tag's information (``GET ajax/tag/info``).

        ``tag`` is sent as the ``tag`` query value; ``params`` carries
        ``lang``. Returns the ``{"error", "message", "body"}`` envelope with
        ``tag``, ``abstract``, ``thumbnail``, and the ``en``/``ja``
        translation blocks.

        Example:
            ``client.web_tag_info('初音ミク')``
        """
        return self.request("GET", "ajax/tag/info",
                            params=dict(params, tag=tag))

    def web_frequent_tags(self, work_type, **params):
        """List the tags that co-occur with the given works
        (``GET ajax/tags/frequent/<work_type>``).

        ``work_type`` is ``illust`` or ``novel``, one quoted path segment.
        ``params`` carries ``ids`` (a list, sent as repeated ``ids[]`` query
        pairs) and ``lang``. Returns the ``{"error", "message", "body"}``
        envelope whose ``body`` is an array of tag entries.

        Example:
            ``client.web_frequent_tags('illust', ids=['149040133'])``
        """
        return self.request(
            "GET", "ajax/tags/frequent/{}".format(quote(str(work_type), safe="")),
            params=params)

    def web_suggest_tags(self, word, **params):
        """Read tag suggestions for a word (``GET ajax/tags/suggest_by_word``).

        ``word`` is sent as the ``word`` query value; ``params`` carries
        ``lang``. Returns the ``{"error", "message", "body"}`` envelope with
        ``illust_count``, ``tag_name`` and ``total_count``.

        Example:
            ``client.web_suggest_tags('初音')``
        """
        return self.request("GET", "ajax/tags/suggest_by_word",
                            params=dict(params, word=word))

    # ------------------------------------------------------------------
    # Web host: writes (documented, never called by this project)
    # ------------------------------------------------------------------

    def web_bookmark_add(self, work_type, **attributes):
        """Bookmark works (``POST ajax/<work_type>/bookmarks/add``, JSON body).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illusts`` or ``novels`` (a quoted path segment).
        ``attributes`` is the JSON body exactly as given; the source's names
        are ``illust_id`` or ``novel_id``, ``restrict`` (``0`` public/``1``
        private), ``comment`` and ``tags`` (a list, written as ``tags[]``).
        The response body is the site's JSON; the source does not guarantee
        its keys. Needs a session cookie and the matching CSRF token.

        Example:
            ``client.web_bookmark_add('illusts', illust_id='149040133',
            restrict='0')``
        """
        return self.request(
            "POST", "ajax/{}/bookmarks/add".format(quote(str(work_type), safe="")),
            data=attributes)

    def web_bookmark_delete(self, work_type, **attributes):
        """Remove a bookmark (``POST ajax/<work_type>/bookmarks/delete``, form body).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illusts`` or ``novels``. This route takes a form
        body, not JSON: ``attributes`` is encoded by the shared encoder, with
        the source's names ``bookmark_id`` (illusts) or ``book_id`` and
        ``del='1'`` (novels). Needs a session cookie and CSRF token.

        Example:
            ``client.web_bookmark_delete('illusts', bookmark_id='123')``
        """
        return self.request(
            "POST",
            "ajax/{}/bookmarks/delete".format(quote(str(work_type), safe="")),
            form=attributes)

    def web_bookmark_add_tags(self, work_type, **attributes):
        """Add tags to bookmarks (``POST ajax/<work_type>/bookmarks/add_tags``,
        JSON body).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illusts`` or ``novels``. ``attributes`` is the JSON
        body as given: the source's names are ``bookmark_ids`` (a list) and
        ``tags`` (a list). Needs a session cookie and CSRF token.

        Example:
            ``client.web_bookmark_add_tags('illusts',
            bookmark_ids=['123'], tags=['cat'])``
        """
        return self.request(
            "POST",
            "ajax/{}/bookmarks/add_tags".format(quote(str(work_type), safe="")),
            data=attributes)

    def web_bookmark_edit_restrict(self, work_type, **attributes):
        """Change bookmarks' visibility
        (``POST ajax/<work_type>/bookmarks/edit_restrict``, JSON body).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illusts`` or ``novels``. ``attributes`` is the JSON
        body as given: the source's names are ``bookmarkIds`` (a list) and
        ``bookmarkRestrict`` (``'private'``/``'public'``). Needs a session
        cookie and CSRF token.

        Example:
            ``client.web_bookmark_edit_restrict('illusts',
            bookmarkIds=['123'], bookmarkRestrict='private')``
        """
        return self.request(
            "POST",
            "ajax/{}/bookmarks/edit_restrict".format(
                quote(str(work_type), safe="")),
            data=attributes)

    def web_bookmark_remove(self, work_type, **attributes):
        """Remove several bookmarks (``POST ajax/<work_type>/bookmarks/remove``,
        JSON body).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illusts`` or ``novels``. ``attributes`` is the JSON
        body as given; the source's name is ``bookmarkIds`` (a list). Needs a
        session cookie and CSRF token.

        Example:
            ``client.web_bookmark_remove('illusts', bookmarkIds=['123'])``
        """
        return self.request(
            "POST",
            "ajax/{}/bookmarks/remove".format(quote(str(work_type), safe="")),
            data=attributes)

    def web_bookmark_rename_progress(self, work_type, **params):
        """Read the progress of a bookmark-tag rename
        (``GET ajax/<work_type>/bookmarks/rename_tag_progress``).

        This one interaction is a ``GET``, not a ``POST``. ``work_type`` is
        ``illusts`` or ``novels``; ``params`` is forwarded unchanged. Returns
        the ``{"error", "message", "body"}`` envelope whose ``body`` carries
        ``isInProgress``. Needs a session cookie.

        Example:
            ``client.web_bookmark_rename_progress('illusts')``
        """
        return self.request(
            "GET",
            "ajax/{}/bookmarks/rename_tag_progress".format(
                quote(str(work_type), safe="")),
            params=params)

    def web_like(self, work_type, **attributes):
        """Like works (``POST ajax/<work_type>/like``, JSON body).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illusts`` or ``novels``. ``attributes`` is the JSON
        body as given; the source's names are ``illust_id`` or ``novel_id``.
        The response body's ``is_liked`` is reported by the source; the source
        claims no undo. Needs a session cookie and CSRF token.

        Example:
            ``client.web_like('illusts', illust_id='149040133')``
        """
        return self.request(
            "POST", "ajax/{}/like".format(quote(str(work_type), safe="")),
            data=attributes)

    def web_comment_post(self, work_type, **attributes):
        """Post an illustration or novel comment
        (``POST rpc/post_comment.php`` or ``POST novel/rpc/post_comment.php``).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illust`` or ``novel`` and chooses the route; it is
        not a path segment on the site. This route takes a form body:
        ``attributes`` is encoded by the shared encoder, with the source's
        names ``type`` (``'comment'`` or ``'stamp'``), ``illust_id`` or
        ``novel_id``, ``author_user_id``, ``comment``, ``parent_id`` and, for
        a stamp, ``stamp_id``. The root JSON holds ``comment_id``, ``comment``,
        ``user_id``, ``user_name``, ``stamp_id`` and ``parent_id``. Needs a
        session cookie and CSRF token.

        Example:
            ``client.web_comment_post('illust', illust_id='149040133',
            comment='nice')``
        """
        path = {"illust": "rpc/post_comment.php",
                "novel": "novel/rpc/post_comment.php"}[work_type]
        return self.request("POST", path, form=attributes)

    def web_comment_delete(self, work_type, **attributes):
        """Delete one illustration or novel comment
        (``POST rpc_delete_comment.php`` or ``POST novel/rpc_delete_comment.php``).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illust`` or ``novel`` and chooses the route. This
        route takes a form body: ``attributes`` carries the source's names
        ``i_id`` and ``del_id``. The response keys are not declared by the
        source. Needs a session cookie and CSRF token.

        Example:
            ``client.web_comment_delete('illust', i_id='149040133',
            del_id='123')``
        """
        path = {"illust": "rpc_delete_comment.php",
                "novel": "novel/rpc_delete_comment.php"}[work_type]
        return self.request("POST", path, form=attributes)

    def web_user_follow_add(self, user_id, **attributes):
        """Follow one user (``POST bookmark_add.php``, form body).

        A write, documented for completeness and never called by this project.
        ``user_id`` and the protocol constants ``mode='add'``, ``type='user'``
        and ``format='json'`` form the body first; ``attributes`` are applied
        over them, so the caller's values win. The source's names are
        ``restrict`` (``0``/``1``) and ``tag``. Needs a session cookie and
        CSRF token.

        Example:
            ``client.web_user_follow_add('27517', restrict='0')``
        """
        form = {"mode": "add", "type": "user", "format": "json",
                "user_id": user_id}
        form.update(attributes)
        return self.request("POST", "bookmark_add.php", form=form)

    def web_user_follow_delete(self, user_id, **attributes):
        """Unfollow one user (``POST rpc_group_setting.php``, form body).

        A write, documented for completeness and never called by this project.
        ``user_id`` and the protocol constants ``mode='del'``,
        ``type='bookuser'`` and ``id=<user_id>`` form the body first;
        ``attributes`` are applied over them. Needs a session cookie and CSRF
        token.

        Example:
            ``client.web_user_follow_delete('27517')``
        """
        form = {"mode": "del", "type": "bookuser", "id": user_id}
        form.update(attributes)
        return self.request("POST", "rpc_group_setting.php", form=form)

    def web_user_block(self, user_id, action, **attributes):
        """Block or unblock one user (``POST ajax/block/save``, JSON body).

        A write, documented for completeness and never called by this project.
        ``user_id`` and ``action`` (``'block'``/``'unblock'``) go into the JSON
        body; ``attributes`` are the rest of the body as given. Needs a
        session cookie and CSRF token.

        Example:
            ``client.web_user_block('27517', 'block')``
        """
        return self.request("POST", "ajax/block/save",
                            data=dict(attributes, user_id=user_id, action=action))

    def web_series_watch(self, work_type, series_id, **attributes):
        """Watch a series (``POST ajax/<work_type>/series/<id>/watch``, JSON body).

        A write, documented for completeness and never called by this project.
        ``work_type`` is ``illust`` or ``novel``; ``series_id`` is the series
        number. ``attributes`` is the JSON body, which may be empty. Needs a
        session cookie and CSRF token.

        Example:
            ``client.web_series_watch('illust', '12345')``
        """
        return self.request(
            "POST", "ajax/{}/series/{}/watch".format(
                quote(str(work_type), safe=""), quote(str(series_id), safe="")),
            data=attributes)

    def web_series_unwatch(self, work_type, series_id, **attributes):
        """Stop watching a series
        (``POST ajax/<work_type>/series/<id>/unwatch``, JSON body).

        A write, documented for completeness and never called by this project.
        Parameters and body are as at ``web_series_watch``. Needs a session
        cookie and CSRF token.

        Example:
            ``client.web_series_unwatch('illust', '12345')``
        """
        return self.request(
            "POST", "ajax/{}/series/{}/unwatch".format(
                quote(str(work_type), safe=""), quote(str(series_id), safe="")),
            data=attributes)

    def web_series_notify_on(self, work_type, series_id, **attributes):
        """Turn on notifications for a series
        (``POST ajax/<work_type>/series/<id>/watchlist/notification/turn_on``,
        JSON body).

        A write, documented for completeness and never called by this project.
        Parameters and body are as at ``web_series_watch``. Needs a session
        cookie and CSRF token.

        Example:
            ``client.web_series_notify_on('illust', '12345')``
        """
        return self.request(
            "POST", "ajax/{}/series/{}/watchlist/notification/turn_on".format(
                quote(str(work_type), safe=""), quote(str(series_id), safe="")),
            data=attributes)

    def web_series_notify_off(self, work_type, series_id, **attributes):
        """Turn off notifications for a series
        (``POST ajax/<work_type>/series/<id>/watchlist/notification/turn_off``,
        JSON body).

        A write, documented for completeness and never called by this project.
        Parameters and body are as at ``web_series_watch``. Needs a session
        cookie and CSRF token.

        Example:
            ``client.web_series_notify_off('illust', '12345')``
        """
        return self.request(
            "POST", "ajax/{}/series/{}/watchlist/notification/turn_off".format(
                quote(str(work_type), safe=""), quote(str(series_id), safe="")),
            data=attributes)

    def web_illust_tag_add(self, illust_id, tag, **attributes):
        """Add a tag to one illustration
        (``POST ajax/tags/illust/<id>/add``, JSON body).

        A write, documented for completeness and never called by this project.
        ``illust_id`` is a quoted path segment; ``tag`` goes into the JSON body
        and ``attributes`` are the rest of the body as given. Needs a session
        cookie and CSRF token.

        Example:
            ``client.web_illust_tag_add('149040133', 'cat')``
        """
        return self.request(
            "POST", "ajax/tags/illust/{}/add".format(
                quote(str(illust_id), safe="")),
            data=dict(attributes, tag=tag))

    # ------------------------------------------------------------------
    # App host: users
    # ------------------------------------------------------------------

    def app_user_detail(self, user_id, **params):
        """Read one user's detail (``GET v1/user/detail``).

        ``user_id`` is the numeric account id, sent as the ``user_id`` query
        value. ``params`` is forwarded unchanged; the client source's own name
        is ``filter`` (``for_ios`` there), which this client does not inject.

        Response is bare JSON with no envelope: ``user``, ``profile``,
        ``profile_publicity`` and ``workspace``. ``user`` carries ``id``,
        ``name``, ``account``, ``profile_image_urls``, ``comment`` and
        ``is_followed``; ``profile`` carries totals such as ``total_illusts``,
        ``total_manga`` and ``total_illust_bookmarks_public``. Needs the token;
        an anonymous call gets the site's own HTTP 400 ``{"error": {...}}``.

        Example:
            ``client.app_user_detail('27517')``
        """
        return self.request("GET", "v1/user/detail", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_illusts(self, user_id, **params):
        """List a user's illustrations or manga (``GET v1/user/illusts``).

        ``user_id`` is sent as ``user_id``. ``params`` is forwarded unchanged;
        the client source's names are ``type`` (``illust`` or ``manga``),
        ``filter`` (``for_ios``) and ``offset``.

        Response ``{"user": {...}, "illusts": [...], "next_url": "..."}``. An
        ``illusts`` entry is the illustration object described at
        ``app_illust_detail``; pass the returned ``next_url`` to
        ``client.request('GET', next_url, api='app')`` for the next page.

        Example:
            ``client.app_user_illusts('27517', type='illust')``
        """
        return self.request("GET", "v1/user/illusts", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_bookmarks_illust(self, user_id, **params):
        """List a user's bookmarked illustrations
        (``GET v1/user/bookmarks/illust``).

        ``user_id`` is sent as ``user_id``, and ``restrict`` (``public`` or
        ``private``) is required in the route's own terms even though the
        client source often fills ``public``; it is forwarded only when
        passed. Other names: ``filter``, ``max_bookmark_id`` (the page cursor)
        and ``tag``.

        Response ``{"illusts": [...], "next_url": "..."}``. Reading another
        user's private bookmarks needs that user's authorization and is not
        available to a bare token.

        Example:
            ``client.app_user_bookmarks_illust('27517', restrict='public')``
        """
        return self.request("GET", "v1/user/bookmarks/illust", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_bookmarks_novel(self, user_id, **params):
        """List a user's bookmarked novels (``GET v1/user/bookmarks/novel``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``restrict``
        (``public``/``private``), ``filter``, ``max_bookmark_id`` and ``tag``
        as given.

        Response ``{"novels": [...], "next_url": "..."}``; a ``novels`` entry
        is the novel object described at ``app_novel_detail``.

        Example:
            ``client.app_user_bookmarks_novel('27517', restrict='public')``
        """
        return self.request("GET", "v1/user/bookmarks/novel", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_related(self, seed_user_id, **params):
        """List users related to one user (``GET v1/user/related``).

        ``seed_user_id`` is the user to base the list on, sent as
        ``seed_user_id``. ``params`` carries ``filter`` and ``offset`` as
        given.

        Response ``{"user_previews": [...], "next_url": "..."}``; each
        ``user_previews`` entry wraps a ``user`` object and its ``illusts``.

        Example:
            ``client.app_user_related('27517')``
        """
        return self.request("GET", "v1/user/related", api="app",
                            params=dict(params, seed_user_id=seed_user_id))

    def app_user_recommended(self, **params):
        """List the signed-in account's recommended users
        (``GET v1/user/recommended``).

        No required value; ``params`` carries ``filter`` and ``offset`` as
        given. Needs the token.

        Response ``{"user_previews": [...], "next_url": "..."}``.

        Example:
            ``client.app_user_recommended()``
        """
        return self.request("GET", "v1/user/recommended", api="app",
                            params=params)

    def app_user_following(self, user_id, **params):
        """List the users one user follows (``GET v1/user/following``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``restrict``
        (``public``/``private``) and ``offset`` as given.

        Response ``{"user_previews": [...], "next_url": "..."}``. A private
        following list needs that user's authorization.

        Example:
            ``client.app_user_following('27517', restrict='public')``
        """
        return self.request("GET", "v1/user/following", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_follower(self, user_id, **params):
        """List the users following one user (``GET v1/user/follower``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``filter`` and
        ``offset`` as given.

        Response ``{"user_previews": [...], "next_url": "..."}``.

        Example:
            ``client.app_user_follower('27517')``
        """
        return self.request("GET", "v1/user/follower", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_mypixiv(self, user_id, **params):
        """List one user's MyPixiv (``GET v1/user/mypixiv``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``offset`` as
        given.

        Response ``{"user_previews": [...], "next_url": "..."}``.

        Example:
            ``client.app_user_mypixiv('27517')``
        """
        return self.request("GET", "v1/user/mypixiv", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_list(self, user_id, **params):
        """List one user's public user groups (``GET v2/user/list``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``filter`` and
        ``offset`` as given.

        Response ``{"user_previews": [...], "next_url": "..."}``.

        Example:
            ``client.app_user_list('27517')``
        """
        return self.request("GET", "v2/user/list", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_bookmark_tags_illust(self, user_id, **params):
        """List the bookmark tags of one user's illustrations
        (``GET v1/user/bookmark-tags/illust``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``restrict``
        (``public``/``private``) and ``offset`` as given.

        Response ``{"bookmark_tags": [...], "next_url": "..."}``; each tag
        carries ``tag``, ``count`` and a ``name`` map.

        Example:
            ``client.app_user_bookmark_tags_illust('27517')``
        """
        return self.request("GET", "v1/user/bookmark-tags/illust", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_bookmark_tags_novel(self, user_id, **params):
        """List the bookmark tags of one user's novels
        (``GET v1/user/bookmark-tags/novel``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``restrict``
        (``public``/``private``) and ``offset`` as given. Response
        ``{"bookmark_tags": [...], "next_url": "..."}``, from the ZipFile
        capture; needs the token and is not verified here.

        Example:
            ``client.app_user_bookmark_tags_novel('27517')``
        """
        return self.request("GET", "v1/user/bookmark-tags/novel", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_follow_detail(self, user_id, **params):
        """Read the signed-in user's follow state for one user
        (``GET v1/user/follow/detail``).

        ``user_id`` is sent as ``user_id``; ``params`` is forwarded unchanged.
        Response ``{"follow_detail": {"is_followed": <bool>, "restrict":
        ...}}``, from the ZipFile capture; needs the token and is not verified
        here.

        Example:
            ``client.app_user_follow_detail('27517')``
        """
        return self.request("GET", "v1/user/follow/detail", api="app",
                            params=dict(params, user_id=user_id))

    def app_user_browsing_history_illusts(self, **params):
        """List the signed-in account's illustration browsing history
        (``GET v1/user/browsing-history/illusts``).

        No required value (the source states no required ``user_id``);
        ``params`` carries ``offset`` as given. Needs the token. Response
        ``{"illusts": [...], "next_url": "..."}``, from the ZipFile capture;
        not verified here.

        Example:
            ``client.app_user_browsing_history_illusts()``
        """
        return self.request("GET", "v1/user/browsing-history/illusts",
                            api="app", params=params)

    def app_user_browsing_history_novels(self, **params):
        """List the signed-in account's novel browsing history
        (``GET v1/user/browsing-history/novels``).

        No required value; ``params`` carries ``offset`` as given. Needs the
        token. Response ``{"novels": [...], "next_url": "..."}``, from the
        ZipFile capture; not verified here.

        Example:
            ``client.app_user_browsing_history_novels()``
        """
        return self.request("GET", "v1/user/browsing-history/novels",
                            api="app", params=params)

    def app_user_state(self, **params):
        """Read the signed-in account's own state (``GET v1/user/me/state``).

        No required value; ``params`` is forwarded unchanged. Needs the token.
        Response ``{"user_state": {"is_mail_authorized": <bool>}}``, from the
        ZipFile capture; not verified here.

        Example:
            ``client.app_user_state()``
        """
        return self.request("GET", "v1/user/me/state", api="app",
                            params=params)

    # ------------------------------------------------------------------
    # App host: illustrations
    # ------------------------------------------------------------------

    def app_illust_detail(self, illust_id, **params):
        """Read one illustration's detail (``GET v1/illust/detail``).

        ``illust_id`` is the illustration number, sent as the ``illust_id``
        query value (the app host puts ids in the query, not the path). An
        ``illust_id`` in ``params`` cannot displace it; other ``params`` are
        forwarded unchanged.

        Response is bare JSON with no envelope: ``{"illust": {...}}``, whose
        ``illust`` holds ``id``, ``title``, ``type`` (``illust``/``manga``/
        ``ugoira``), ``image_urls``, ``meta_single_page``/``meta_pages``,
        ``user``, ``tags``, ``page_count``, ``width``, ``height`` and
        counters. Needs the token; a live anonymous call returned HTTP 400
        with a bare ``{"error": {...}}`` object, so the success body is
        documented from the client source rather than verified here.

        Example:
            ``client.app_illust_detail('149040133')``
        """
        return self.request("GET", "v1/illust/detail", api="app",
                            params=dict(params, illust_id=illust_id))

    def app_illust_follow(self, **params):
        """List illustrations from the accounts the signed-in user follows
        (``GET v2/illust/follow``).

        No required value; ``params`` carries ``restrict`` and ``offset`` as
        given. Needs the token.

        Response ``{"illusts": [...], "next_url": "..."}``.

        Example:
            ``client.app_illust_follow(restrict='public')``
        """
        return self.request("GET", "v2/illust/follow", api="app",
                            params=params)

    def app_illust_mypixiv(self, **params):
        """List MyPixiv illustrations (``GET v2/illust/mypixiv``).

        No required value; ``params`` carries ``offset`` as given. Needs the
        token. Response ``{"illusts": [...], "next_url": "..."}``, from the
        ZipFile capture; not verified here.

        Example:
            ``client.app_illust_mypixiv()``
        """
        return self.request("GET", "v2/illust/mypixiv", api="app",
                            params=params)

    def app_illust_popular(self, **params):
        """List popular illustrations (``GET v1/illust/popular``).

        No required value is documented: the ZipFile capture records the route
        but no schema and no required ``illust_id``, so none is claimed here;
        ``params`` is forwarded unchanged. Needs the token, and no response
        fields are asserted.

        Example:
            ``client.app_illust_popular()``
        """
        return self.request("GET", "v1/illust/popular", api="app",
                            params=params)

    def app_illust_comments(self, illust_id, **params):
        """List one illustration's comments (``GET v1/illust/comments``).

        ``illust_id`` is sent as ``illust_id``; ``params`` carries ``offset``
        and ``include_total_comments`` (a boolean) as given.

        Response ``{"comments": [...], "next_url": "..."}`` and, with
        ``include_total_comments``, ``total_comments``. Each comment holds
        ``id``, ``comment``, ``date``, ``user``, ``parent_comment`` and
        ``has_replies``.

        Example:
            ``client.app_illust_comments('149040133')``
        """
        return self.request("GET", "v1/illust/comments", api="app",
                            params=dict(params, illust_id=illust_id))

    def app_illust_comment_replies(self, comment_id, **params):
        """List the replies to one illustration comment
        (``GET v1/illust/comment/replies``).

        ``comment_id`` is sent as ``comment_id``; ``params`` is forwarded
        unchanged. This is the app host's reply listing, distinct from
        ``app_illust_comments``, which returns top-level comments.

        Response ``{"comments": [...], "next_url": "..."}``, from the
        third-party spec; needs the token and is not verified here.

        Example:
            ``client.app_illust_comment_replies('123456789')``
        """
        return self.request("GET", "v1/illust/comment/replies", api="app",
                            params=dict(params, comment_id=comment_id))

    def app_illust_comments_v3(self, illust_id, **params):
        """List one illustration's comments from the v3 route
        (``GET v3/illust/comments``).

        ``illust_id`` is sent as ``illust_id``; ``params`` carries the
        ``next_url`` cursor fields the caller takes from a previous response
        (the source's first call sends only ``illust_id``, so no cursor
        default is invented). This named v3 route is the current gallery-dl
        client's, distinct from ``app_illust_comments`` (v1); neither is an
        alias of the other.

        Response ``{"comments": [...], "next_url": "..."}``, from the
        gallery-dl source; needs the token. An anonymous first-call
        observation is pending, so the success body is described from the
        source and not verified here.

        Example:
            ``client.app_illust_comments_v3('149040133')``
        """
        return self.request("GET", "v3/illust/comments", api="app",
                            params=dict(params, illust_id=illust_id))

    def app_illust_related(self, illust_id, **params):
        """List illustrations related to one (``GET v2/illust/related``).

        ``illust_id`` is sent as ``illust_id``; ``params`` carries ``filter``,
        ``seed_illust_ids`` (a list, encoded as repeated ``seed_illust_ids[]``
        query pairs), ``offset`` and ``viewed`` (a list).

        Response ``{"illusts": [...], "next_url": "..."}``.

        Example:
            ``client.app_illust_related('149040133')``
        """
        return self.request("GET", "v2/illust/related", api="app",
                            params=dict(params, illust_id=illust_id))

    def app_illust_recommended(self, **params):
        """List recommended illustrations (``GET v1/illust/recommended``).

        No required value; ``params`` carries ``content_type``
        (``illust``/``manga``), ``include_ranking_label``,
        ``max_bookmark_id_for_recommend``,
        ``min_bookmark_id_for_recent_illust``, ``include_ranking_illusts``,
        ``include_privacy_policy``, ``offset`` and ``viewed`` (a list) as
        given. Needs the token.

        Response ``{"illusts": [...], "ranking_illusts": [...],
        "next_url": "..."}`` and, per the requested options,
        ``contest_exists`` and ``privacy_policy``.

        Example:
            ``client.app_illust_recommended(content_type='illust')``
        """
        return self.request("GET", "v1/illust/recommended", api="app",
                            params=params)

    def app_illust_ranking(self, **params):
        """List an illustration ranking (``GET v1/illust/ranking``).

        No required value; ``params`` carries ``mode``, ``filter``, ``date``
        (``YYYY-MM-DD``) and ``offset`` as given. The client source's ``mode``
        values include ``day``, ``day_male``, ``day_female``,
        ``week_original``, ``week_rookie``, ``week``, ``month``, ``day_r18``,
        ``day_male_r18``, ``day_female_r18``, ``week_r18``, ``week_r18g`` and
        the manga variants; none is injected.

        Response ``{"illusts": [...], "next_url": "..."}``.

        Example:
            ``client.app_illust_ranking(mode='day')``
        """
        return self.request("GET", "v1/illust/ranking", api="app",
                            params=params)

    def app_illust_new(self, **params):
        """List newly posted illustrations (``GET v1/illust/new``).

        No required value; ``params`` carries ``content_type``
        (``illust``/``manga``), ``filter`` and ``max_illust_id`` (the cursor)
        as given.

        Response ``{"illusts": [...], "next_url": "..."}``.

        Example:
            ``client.app_illust_new(content_type='illust')``
        """
        return self.request("GET", "v1/illust/new", api="app", params=params)

    def app_illust_series(self, illust_series_id, **params):
        """Read one illustration series (``GET v1/illust/series``).

        ``illust_series_id`` is the series number, sent as the
        ``illust_series_id`` query value -- this route's own key, which is not
        ``series_id``. ``params`` carries ``offset`` as given.

        Response ``{"illusts": [...], "next_url": "...",
        "illust_series_detail": {"title": ..., "caption": ...,
        "series_work_count": ...}}``, from the gallery-dl client source; needs
        the token. A live anonymous read of
        ``?illust_series_id=257832&offset=0`` answered HTTP 400 with the OAuth
        ``invalid_request`` error, so the success body is described from the
        source and not verified here.

        Example:
            ``client.app_illust_series('257832')``
        """
        return self.request("GET", "v1/illust/series", api="app",
                            params=dict(params,
                                        illust_series_id=illust_series_id))

    def app_ugoira_metadata(self, illust_id, **params):
        """Read a ugoira illustration's frame data (``GET v1/ugoira/metadata``).

        ``illust_id`` is sent as ``illust_id``; ``params`` is forwarded
        unchanged.

        Response ``{"ugoira_metadata": {"zip_urls": {"medium": "...",
        "original": "..."}, "frames": [{"file": "...", "delay": <ms>}, ...]}}``.
        The ``zip_urls`` point at ``i.pximg.net`` and are returned as strings;
        the client downloads nothing.

        Example:
            ``client.app_ugoira_metadata('149040133')``
        """
        return self.request("GET", "v1/ugoira/metadata", api="app",
                            params=dict(params, illust_id=illust_id))

    def app_trending_tags_illust(self, **params):
        """List trending illustration tags (``GET v1/trending-tags/illust``).

        No required value; ``params`` carries ``filter`` as given.

        Response ``{"trend_tags": [...]}``; each entry carries ``tag``,
        ``translated_name`` and ``illust``.

        Example:
            ``client.app_trending_tags_illust()``
        """
        return self.request("GET", "v1/trending-tags/illust", api="app",
                            params=params)

    def app_trending_tags_manga(self, **params):
        """List trending manga tags (``GET v1/trending-tags/manga``).

        No required value; ``params`` carries ``filter`` as given. The source
        records only the route and declares no successful schema, so no
        response fields are claimed. Needs the token.

        Example:
            ``client.app_trending_tags_manga()``
        """
        return self.request("GET", "v1/trending-tags/manga", api="app",
                            params=params)

    def app_trending_tags_novel(self, **params):
        """List trending novel tags (``GET v1/trending-tags/novel``).

        No required value; ``params`` carries ``filter`` as given. The source
        records only the route and declares no successful schema, so no
        response fields are claimed. Needs the token.

        Example:
            ``client.app_trending_tags_novel()``
        """
        return self.request("GET", "v1/trending-tags/novel", api="app",
                            params=params)

    def app_manga_recommended(self, **params):
        """List recommended manga (``GET v1/manga/recommended``).

        No required value; ``params`` carries ``filter``,
        ``include_ranking_illusts``, ``max_bookmark_id`` and ``offset`` as
        given. Response ``{"illusts": [...], "ranking_illusts": [...],
        "next_url": "..."}``, from the ZipFile capture; needs the token and is
        not verified here.

        Example:
            ``client.app_manga_recommended()``
        """
        return self.request("GET", "v1/manga/recommended", api="app",
                            params=params)

    # ------------------------------------------------------------------
    # App host: search
    # ------------------------------------------------------------------

    def app_search_illust(self, word, **params):
        """Search illustrations (``GET v1/search/illust``).

        ``word`` is the keyword, sent as the ``word`` query value. ``params``
        is forwarded unchanged; the client source's names are ``search_target``
        (``partial_match_for_tags``, ``exact_match_for_tags``,
        ``title_and_caption``, ``keyword``), ``sort`` (``date_desc``,
        ``date_asc``, ``popular_desc``), ``duration`` (``within_last_day``,
        ``within_last_week``, ``within_last_month``), ``start_date``,
        ``end_date`` (``YYYY-MM-DD``), ``filter``, ``search_ai_type`` (0/1)
        and ``offset``.

        Response ``{"illusts": [...], "next_url": "...",
        "search_span_limit": ..., "show_ai": ...}``.

        Example:
            ``client.app_search_illust('cat', sort='date_desc')``
        """
        return self.request("GET", "v1/search/illust", api="app",
                            params=dict(params, word=word))

    def app_search_novel(self, word, **params):
        """Search novels (``GET v1/search/novel``).

        ``word`` is the keyword, sent as ``word``. ``params`` is forwarded
        unchanged; names are as at ``app_search_illust`` plus
        ``merge_plain_keyword_results``,
        ``include_translated_tag_results`` and (for novel text)
        ``search_target='text'``.

        Response ``{"novels": [...], "next_url": "...",
        "search_span_limit": ..., "show_ai": ...}``.

        Example:
            ``client.app_search_novel('cat')``
        """
        return self.request("GET", "v1/search/novel", api="app",
                            params=dict(params, word=word))

    def app_search_user(self, word, **params):
        """Search users (``GET v1/search/user``).

        ``word`` is the keyword, sent as ``word``; ``params`` carries ``sort``,
        ``duration``, ``filter`` and ``offset`` as given.

        Response ``{"user_previews": [...], "next_url": "..."}``.

        Example:
            ``client.app_search_user('cat')``
        """
        return self.request("GET", "v1/search/user", api="app",
                            params=dict(params, word=word))

    def app_search_autocomplete(self, word, **params):
        """Read keyword autocompletion (``GET v1/search/autocomplete``).

        ``word`` is sent as the ``word`` query value; ``params`` is forwarded
        unchanged. Response ``{"search_auto_complete_keywords": [...]}``, from
        the ZipFile capture, whose elements it does not declare, so no entry
        fields are claimed. Needs the token.

        Example:
            ``client.app_search_autocomplete('初音')``
        """
        return self.request("GET", "v1/search/autocomplete", api="app",
                            params=dict(params, word=word))

    # ------------------------------------------------------------------
    # App host: novels
    # ------------------------------------------------------------------

    def app_novel_detail(self, novel_id, **params):
        """Read one novel's detail (``GET v2/novel/detail``).

        ``novel_id`` is sent as ``novel_id``; ``params`` is forwarded
        unchanged.

        Response is bare JSON ``{"novel": {...}}``; ``novel`` holds ``id``,
        ``title``, ``caption``, ``image_urls``, ``tags``, ``page_count``,
        ``text_length``, ``user``, ``series`` and counters. Needs the token;
        an anonymous call is rejected with the site's own HTTP 400.

        Example:
            ``client.app_novel_detail('12345678')``
        """
        return self.request("GET", "v2/novel/detail", api="app",
                            params=dict(params, novel_id=novel_id))

    def app_novel_series(self, series_id, **params):
        """Read one novel series (``GET v2/novel/series``).

        ``series_id`` is sent as ``series_id``; ``params`` carries ``filter``
        and ``last_order`` (the cursor, an integer as a string) as given.

        Response ``{"novel_series_detail": {...}, "novels": [...],
        "next_url": "..."}``.

        Example:
            ``client.app_novel_series('12345')``
        """
        return self.request("GET", "v2/novel/series", api="app",
                            params=dict(params, series_id=series_id))

    def app_novel_comments(self, novel_id, **params):
        """List one novel's comments (``GET v1/novel/comments``).

        ``novel_id`` is sent as ``novel_id``; ``params`` carries ``offset``
        and ``include_total_comments`` as given.

        Response ``{"comments": [...], "next_url": "...",
        "comment_access_control": ...}`` and, on request, ``total_comments``.

        Example:
            ``client.app_novel_comments('12345678')``
        """
        return self.request("GET", "v1/novel/comments", api="app",
                            params=dict(params, novel_id=novel_id))

    def app_novel_recommended(self, **params):
        """List recommended novels (``GET v1/novel/recommended``).

        No required value; ``params`` carries ``include_ranking_label``,
        ``filter``, ``offset``, ``include_ranking_novels``,
        ``already_recommended`` (a comma-separated string, e.g.
        ``'12345,67890'``), ``max_bookmark_id_for_recommend`` and
        ``include_privacy_policy`` as given.

        Response ``{"novels": [...], "ranking_novels": [...],
        "next_url": "..."}`` and, per the options, ``privacy_policy``.

        Example:
            ``client.app_novel_recommended()``
        """
        return self.request("GET", "v1/novel/recommended", api="app",
                            params=params)

    def app_novel_new(self, **params):
        """List newly posted novels (``GET v1/novel/new``).

        No required value; ``params`` carries ``filter`` and ``max_novel_id``
        (the cursor) as given.

        Response ``{"novels": [...], "next_url": "..."}``.

        Example:
            ``client.app_novel_new()``
        """
        return self.request("GET", "v1/novel/new", api="app", params=params)

    def app_novel_follow(self, **params):
        """List novels from the accounts the signed-in user follows
        (``GET v1/novel/follow``).

        No required value; ``params`` carries ``restrict`` (``public``/
        ``private``/``all``) and ``offset`` as given. Needs the token.

        Response ``{"novels": [...], "next_url": "..."}``.

        Example:
            ``client.app_novel_follow(restrict='public')``
        """
        return self.request("GET", "v1/novel/follow", api="app", params=params)

    def app_novel_ranking(self, **params):
        """List a novel ranking (``GET v1/novel/ranking``).

        No required value; ``params`` carries ``mode``, ``date`` and
        ``offset`` as given. The source's ``mode`` values are ``day``,
        ``day_male``, ``day_female``, ``week_rookie``, ``week``, ``day_r18``
        and ``week_r18``; none is injected. Response ``{"novels": [...],
        "next_url": "..."}``, from the ZipFile capture; needs the token and
        is not verified here.

        Example:
            ``client.app_novel_ranking(mode='day')``
        """
        return self.request("GET", "v1/novel/ranking", api="app",
                            params=params)

    def app_novel_bookmark_detail(self, novel_id, **params):
        """Read the signed-in user's bookmark state for one novel
        (``GET v2/novel/bookmark/detail``).

        ``novel_id`` is sent as ``novel_id``; ``params`` is forwarded
        unchanged. Response ``{"bookmark_detail": {"is_bookmarked": <bool>,
        "restrict": ..., "tags": [{"name", "count", "is_registered"}]}}``,
        from the ZipFile capture; needs the token and is not verified here.

        Example:
            ``client.app_novel_bookmark_detail('12345678')``
        """
        return self.request("GET", "v2/novel/bookmark/detail", api="app",
                            params=dict(params, novel_id=novel_id))

    def app_novel_mypixiv(self, **params):
        """List MyPixiv novels (``GET v1/novel/mypixiv``).

        No required value; ``params`` carries ``offset`` as given. Response
        ``{"novels": [...], "next_url": "..."}``, from the ZipFile capture;
        needs the token and is not verified here.

        Example:
            ``client.app_novel_mypixiv()``
        """
        return self.request("GET", "v1/novel/mypixiv", api="app",
                            params=params)

    def app_novel_popular(self, **params):
        """List popular novels (``GET v1/novel/popular``).

        No required value is documented: the ZipFile capture records the route
        but no schema and no required ``novel_id``, so none is claimed here;
        ``params`` is forwarded unchanged. Needs the token, and no response
        fields are asserted.

        Example:
            ``client.app_novel_popular()``
        """
        return self.request("GET", "v1/novel/popular", api="app",
                            params=params)

    def app_user_novels(self, user_id, **params):
        """List a user's novels (``GET v1/user/novels``).

        ``user_id`` is sent as ``user_id``; ``params`` carries ``filter`` and
        ``offset`` as given.

        Response ``{"user": {...}, "novels": [...], "next_url": "..."}``.

        Example:
            ``client.app_user_novels('27517')``
        """
        return self.request("GET", "v1/user/novels", api="app",
                            params=dict(params, user_id=user_id))

    def app_webview_novel(self, novel_id, **params):
        """Read a novel's webview page as raw HTML (``GET webview/v2/novel``).

        ``novel_id`` is sent as the ``id`` query value (the route's own key).
        ``params`` is forwarded unchanged; the client source adds
        ``viewer_version`` (a date-coded build string such as
        ``'20221031_ai'``), which this client does not inject, so pass it
        explicitly -- e.g. ``viewer_version='20221031_ai'`` -- when the site
        requires it.

        This is the one method that returns HTML, not JSON: the body is
        returned as unchanged text through ``response_format='text'`` and is
        not parsed. The novel text and metadata are embedded in that page;
        extracting them is the caller's job. Needs the token.

        Example:
            ``client.app_webview_novel('12345678',
            viewer_version='20221031_ai')``
        """
        return self.request("GET", "webview/v2/novel", api="app",
                            params=dict(params, id=novel_id),
                            response_format="text")

    # ------------------------------------------------------------------
    # App host: bookmark and follow state
    # ------------------------------------------------------------------

    def app_illust_bookmark_detail(self, illust_id, **params):
        """Read the signed-in user's bookmark state for one illustration
        (``GET v2/illust/bookmark/detail``).

        ``illust_id`` is sent as ``illust_id``; ``params`` is forwarded
        unchanged.

        Response ``{"bookmark_detail": {"is_bookmarked": <bool>, "tags":
        [...]}}``. Needs the token.

        Example:
            ``client.app_illust_bookmark_detail('149040133')``
        """
        return self.request("GET", "v2/illust/bookmark/detail", api="app",
                            params=dict(params, illust_id=illust_id))

    def app_illust_bookmark_add(self, illust_id, **attributes):
        """Bookmark one illustration (``POST v2/illust/bookmark/add``).

        A write, documented for completeness and never called by this project.
        ``illust_id`` is sent in the form body; ``attributes`` are the rest of
        the form as given -- the client source's names are ``restrict``
        (``public``/``private``) and ``tags`` (a list, encoded as repeated
        ``tags[]`` fields by the shared encoder).

        Response is the site's JSON; the client source does not guarantee
        success keys. Needs the token.

        Example:
            ``client.app_illust_bookmark_add('149040133', restrict='public',
            tags=['cat'])``
        """
        return self.request("POST", "v2/illust/bookmark/add", api="app",
                            form=dict(attributes, illust_id=illust_id))

    def app_illust_bookmark_delete(self, illust_id, **attributes):
        """Remove one illustration from the signed-in user's bookmarks
        (``POST v1/illust/bookmark/delete``).

        A write, documented for completeness and never called by this
        project. ``illust_id`` is sent in the form body; ``attributes`` are
        the rest of the form as given.

        Response is the site's JSON. Needs the token.

        Example:
            ``client.app_illust_bookmark_delete('149040133')``
        """
        return self.request("POST", "v1/illust/bookmark/delete", api="app",
                            form=dict(attributes, illust_id=illust_id))

    def app_illust_browsing_history_add(self, illust_ids, **attributes):
        """Record illustrations in the browsing history
        (``POST v2/user/browsing-history/illust/add``, form body).

        A write, documented for completeness and never called by this project.
        ``illust_ids`` is a list sent in the form body as repeated
        ``illust_ids[]`` fields (the source's wire form); ``attributes`` are
        the rest of the form as given. The source declares the response as an
        empty JSON object. Needs the token.

        Example:
            ``client.app_illust_browsing_history_add(['149040133'])``
        """
        return self.request("POST", "v2/user/browsing-history/illust/add",
                            api="app",
                            form=dict(attributes, illust_ids=illust_ids))

    def app_user_follow_add(self, user_id, **attributes):
        """Follow one user (``POST v1/user/follow/add``).

        A write, documented for completeness and never called by this
        project. ``user_id`` is sent in the form body; ``attributes`` are the
        rest of the form as given -- the client source's name is ``restrict``
        (``public``/``private``).

        Response is the site's JSON. Needs the token.

        Example:
            ``client.app_user_follow_add('27517', restrict='public')``
        """
        return self.request("POST", "v1/user/follow/add", api="app",
                            form=dict(attributes, user_id=user_id))

    def app_user_follow_delete(self, user_id, **attributes):
        """Unfollow one user (``POST v1/user/follow/delete``).

        A write, documented for completeness and never called by this
        project. ``user_id`` is sent in the form body; ``attributes`` are the
        rest of the form as given.

        Response is the site's JSON. Needs the token.

        Example:
            ``client.app_user_follow_delete('27517')``
        """
        return self.request("POST", "v1/user/follow/delete", api="app",
                            form=dict(attributes, user_id=user_id))

    def app_user_edit_ai_show_settings(self, show_ai, **attributes):
        """Change whether AI-generated works are shown (``POST
        v1/user/ai-show-settings/edit``).

        A write, documented for completeness and never called by this
        project. ``show_ai`` is a boolean sent in the form body under the key
        ``show_ai`` (the shared encoder writes it lowercase, ``true``/
        ``false``); ``attributes`` are the rest of the form as given.

        Response is the site's JSON. Needs the token.

        Example:
            ``client.app_user_edit_ai_show_settings(True)``
        """
        return self.request("POST", "v1/user/ai-show-settings/edit", api="app",
                            form=dict(attributes, show_ai=show_ai))

    # ------------------------------------------------------------------
    # App host: application, emoji and spotlight
    # ------------------------------------------------------------------

    def app_application_info(self, **params):
        """Read the Android application info (``GET
        v1/application-info/android``).

        No required value; ``params`` is forwarded unchanged. This route is
        anonymous and was observed to answer 200 without a token.

        Response ``{"application_info": {...}}``: the latest version,
        ``update_required``, ``update_available``, ``update_message`` and
        ``store_url``.

        Example:
            ``client.app_application_info()``
        """
        return self.request("GET", "v1/application-info/android", api="app",
                            params=params)

    def app_emoji(self, **params):
        """Read the emoji list (``GET v1/emoji``).

        No required value; ``params`` is forwarded unchanged. This route is
        anonymous and was observed to answer 200 without a token.

        Response ``{"emoji_definitions": [...]}``; each entry carries ``id``,
        ``slug`` and ``image_url_medium`` (a ``s.pximg.net`` address returned
        as a string).

        Example:
            ``client.app_emoji()``
        """
        return self.request("GET", "v1/emoji", api="app", params=params)

    def app_spotlight_articles(self, **params):
        """List spotlight articles (``GET v1/spotlight/articles``).

        No required value; ``params`` carries ``category`` (``all``/
        ``manga``) and ``offset`` as given. Needs the token per the client
        source; an anonymous probe answered HTTP 400.

        Response ``{"spotlight_articles": [...], "next_url": "..."}``.

        Example:
            ``client.app_spotlight_articles(category='all')``
        """
        return self.request("GET", "v1/spotlight/articles", api="app",
                            params=params)
