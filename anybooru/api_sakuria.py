"""Native read methods for Sakuria (sakuria-api.syarolia.com).

Sakuria is not a booru: it is a third-party Pixiv mirror, so works, novels,
series and users keep Pixiv's identifiers and data model. This family has the
weakest evidence of any in this package. There is no official API page, no
OpenAPI document and no server source, and the ``docs`` link the service
returns points at a placeholder repository. The routes and parameters below
come from anonymous responses observed on the API host and, where noted, from
a supplied session reference; the field lists are candidate shapes, not a
schema this project verified, and fields may be omitted or change.

Shared candidate facts:
    * Base URL: ``https://sakuria-api.syarolia.com``. Reads are ``GET`` and
      answer JSON. The same host serves ``/img/...`` image bytes, which this
      client never requests; relative ``/img/...`` paths in responses must be
      joined to the site URL by the caller.
    * Detail routes (``/illust/{id}``, ``/novels/{id}``, ``/series/{id}``,
      ``/users/{id}``, ``/spotlight/{id}``) answered bare objects, without
      the list envelope.
    * List routes answered an envelope built around ``items`` and a subset of
      ``page``, ``pageSize``, ``total``, ``totalPages``, ``hasMore`` and
      ``nextPage``, with ``hiddenCount`` where the site withheld items. The
      observed numbers did not describe the item stream: ``total`` grew by
      about one page per page, ``nextPage`` was not the next page number, and
      the item count ignored the requested ``size`` (``size=1`` answered 5
      items, ``size=24`` answered 29, 24 and 33 on successive pages,
      ``size=48`` answered 39). Successive pages overlapped heavily (24 of
      one page's 29 items reappeared on the next), so callers must
      deduplicate. No end-of-list page was reached, so the terminating signal
      is unconfirmed.
    * Recognized parameters are validated: ``page=0``, ``size=0``, ``size=49``
      and an unknown ``sort`` each answered 400 ``invalid_search_filter`` with
      the offending ``field``, while ``limit=__invalid__`` was still answered
      200 with the same ids and paging fields as the baseline. A 200 therefore
      does not prove a parameter took effect, and unrecognized names other
      than that one value were not tested.
    * Errors are JSON with an ``error`` key. Observed: 400 (invalid path id,
      ``invalid_search_filter``, and ``unsupported_filter_for_scope`` when a
      work-type filter reaches novel search), 401 (``auth_required`` for the
      paid-only ``type=illust`` filter and for ``ai=exclude`` on novel search,
      and ``sakuria_session_required`` for ``/me/likes``), 404 (unknown
      illust) and 503 (``retryable`` for ``/spotlight/0``). The supplied
      reference also lists 403 (no sample) and 426.
    * Every observed work carried ``isR18: false`` and ``xRestrict: 0``, and
      the search envelopes reported ``hiddenCount``; this project sent no
      parameter to change that. Logged-in and paid behaviour was not
      observed.
    * Authentication is a JWT in ``Authorization: Bearer <token>``. Only
      ``/me/likes`` of the 17 ``/me/*`` reads was requested: without a
      data-contract header it answered 426 ``upgrade_required`` with
      ``requiredDataContract: 2``, and with that header it answered 401
      ``sakuria_session_required``. The other 16 come from the reference
      alone, were not requested, and have unknown response shapes. The
      reference found no login or token route on the API host, and this
      client implements no login, refresh or account-changing helper either
      way: pass a token you already have, or stay anonymous.
    * ``x-sakuria-data-contract: 2`` is the client's contract version
      selector. It is not sent implicitly; pass it in ``headers``.
    * Nothing is unwrapped, renamed, defaulted, clamped, retried or paged
      locally: the JSON body is returned exactly as received.

Which calls have actually been made against the live site is recorded in
docs/verification.md.

Classes:
    SakuriaApi_Mixin -- Sakuria illust, novel, series, spotlight, tag, user
        and account reads.
"""

# Standard library imports
from urllib.parse import quote


class SakuriaApi_Mixin:
    """Sakuria read methods, each a thin ``Sakuria.request()`` GET call."""

    # ------------------------------------------------------------------
    # Service
    # ------------------------------------------------------------------

    def index(self, **params):
        """Read the service identity (``GET /``).

        Candidate body: ``{name, ok, docs}``; the ``docs`` URL points at a
        placeholder repository rather than real documentation.
        """
        return self.request("GET", "/", params=params)

    def stats(self, **params):
        """Read the site's own counters (``GET /stats``).

        Candidate body: ``{newToday, totalIllusts, totalCreators,
        totalUsers}``. The reference cautions that these counters need not
        describe the whole mirrored catalogue.
        """
        return self.request("GET", "/stats", params=params)

    def health(self, **params):
        """Read the deployment health report (``GET /healthz``).

        Candidate body: ``{ok, releaseSha, releaseVersionId, checks}``, where
        ``checks`` holds boolean dependency flags plus ``cacheBackend`` and
        ``databaseDriver``.
        """
        return self.request("GET", "/healthz", params=params)

    def app_config(self, **params):
        """Read the client startup configuration (``GET /app/config``).

        Candidate body: upgrade fields (``latestVersion``, ``latestBuild``,
        ``updateUrl``, ``releaseNotes``, ``updateAvailable``,
        ``updateRequired``), ``maintenance``, ``announcement``, ``flags``,
        ``servers``, ``imageProxy`` (with ``turboBase``), ``imageProxyPro``,
        ``iap`` and ``appAttest``. ``servers`` lists the backend hosts and
        which of them are member-only; the anonymous host is the one this
        client is configured for.
        """
        return self.request("GET", "/app/config", params=params)

    def ai_config(self, **params):
        """Read the AI feature configuration (``GET /ai/config``).

        Candidate body: ``enabled``, per-feature switches (``metaEnabled``,
        ``novelEnabled``, ``mangaEnabled``, ``commentEnabled``, ...),
        ``cacheTtlDays``, ``billingMode``, ``models`` and ``languages``.
        """
        return self.request("GET", "/ai/config", params=params)

    # ------------------------------------------------------------------
    # Illust
    # ------------------------------------------------------------------

    def illust_search(self, **params):
        """Search illusts (``GET /search/illust``).

        Candidate parameters, with the values this project actually sent:
            q (str): Tag substring match, case-insensitive; the reference
                reports an empty or omitted value answering an empty list.
            page (int): Page number, from 1; ``page=0`` answered 400
                ``invalid_search_filter`` with ``field=page``.
            size (int): Requested items per page. ``size=1`` and ``size=48``
                were accepted while ``size=0`` and ``size=49`` answered 400
                with ``field=size``, but the returned count did not match the
                value (1 answered 5 items, 24 answered 29/24/33 on successive
                pages, 48 answered 39), so ``size`` guarantees nothing.
            sort (str): ``'new'`` and ``'popular'`` were accepted; an unknown
                value answered 400 with ``field=sort``.
            type (str): ``type=illust`` answered 401 ``auth_required``, so
                the value needs the paid tier; the reference calls ``'all'``
                the anonymous value.
            ai (str): the reference calls ``'include'`` anonymous and
                ``'exclude'`` paid; this project did not send it.
            mode (str): the reference describes it as recognized but with no
                usable value, and the sample value answered 400 with
                ``field=mode``.

        Unrecognized names are not validated here: ``limit=__invalid__`` was
        still answered 200 with the baseline ids and paging fields, and the
        envelope values do not describe the item stream. See the module
        docstring.
        """
        return self.request("GET", "/search/illust", params=params)

    def illust_show(self, illust_id, **params):
        """Read one illust as a bare object (``GET /illust/{id}``).

        Candidate fields include ``id``, ``title``, ``type``, ``pages``,
        ``urls`` (``thumb``/``small``/``regular``/``original`` plus ``w`` and
        ``h``), ``pageUrls`` when ``pages > 1``, ``author``, ``tags``,
        ``stats``, ``publishedAt``, ``publishedDays``, ``isAi``, ``isR18``,
        ``xRestrict``, ``sl`` and ``series``. The reference reports no
        parameter having an effect, and the id is passed through unvalidated:
        ``/illust/0`` answered 404 and a non-numeric id 400.
        """
        return self.request("GET", "/illust/{}".format(illust_id), params=params)

    def illust_comments(self, illust_id, **params):
        """Read an illust's comments (``GET /illust/{id}/comments``).

        Candidate parameters: ``page`` (int) and ``size`` (int), described by
        the reference as 1-30 with a default of 12. The sampled call
        ``page=1&size=2`` answered two items and ``hasMore: true``; the
        reference reports out-of-range values falling back to the default
        instead of answering 400, which this project did not test. Candidate
        envelope: ``{items, hasMore}`` without ``total``. Candidate comment
        fields: ``id``, ``author`` (same shape as an illust author but without
        ``stats``), ``text``, ``repliesCount``, ``likes``, ``createdAt`` and
        ``timeLabel``.
        """
        return self.request(
            "GET", "/illust/{}/comments".format(illust_id), params=params)

    def illust_comment_replies(self, illust_id, comment_id, **params):
        """Read one comment's replies (``GET /illust/{id}/comments/{cid}/replies``).

        Candidate envelope: ``{items}`` only, without ``hasMore``, with the
        same candidate reply fields as a comment. The reference reports no
        parameter having an effect.
        """
        return self.request(
            "GET", "/illust/{}/comments/{}/replies".format(illust_id, comment_id),
            params=params)

    def illust_related(self, illust_id, **params):
        """Read related illusts (``GET /illust/{id}/related``).

        Candidate parameter: ``size`` (int), described by the reference as
        1-30 with a default of 30; the sampled ``size=2`` answered two items.
        Candidate envelope: ``{items}`` with no pagination fields; the
        reference reports page-like parameters changing nothing.
        """
        return self.request(
            "GET", "/illust/{}/related".format(illust_id), params=params)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def user_search(self, **params):
        """Search users (``GET /search/user``).

        Candidate parameters: ``q`` (str, matches name or handle) and ``page``
        (int, from 1). Candidate envelope: ``{items, total}`` with items
        shaped ``{user, previews}``, where ``previews`` holds up to three
        small work objects. For ``q=mika``, ``page=1``, ``2`` and ``3``
        answered 6, 12 and 21 items with ``total`` equal to the item count
        each time and no id shared between pages, so ``total`` was not a
        cumulative count in these samples. This client returns the field
        unchanged and does not interpret it.
        """
        return self.request("GET", "/search/user", params=params)

    def user_show(self, user_id, **params):
        """Read one user as a bare object (``GET /users/{id}``).

        Candidate fields: ``id``, ``name``, ``handle``, ``accent``,
        ``avatar``, ``stats``, ``social``, plus optional ``bio``,
        ``banner`` and ``location``. ``avatar`` appeared either as a
        site-relative ``/img/...`` path or as an absolute external URL. The
        reference reports a missing id answering 404 and a non-numeric one
        400.
        """
        return self.request("GET", "/users/{}".format(user_id), params=params)

    def user_illusts(self, user_id, **params):
        """Read a user's illusts (``GET /users/{id}/illusts``).

        ``page=1`` and ``page=2`` each answered 45 items sharing 23 ids, and
        the envelope's ``nextPage`` moved from 3 to 4 while ``pageSize``
        stayed 24, so ``page`` did advance but the pages overlap and
        ``pageSize`` does not bound the item count. Candidate parameter:
        ``page`` (int); the reference reports size, limit, offset and
        ordering parameters changing nothing. Envelope: the shared list
        envelope with Illust items.
        """
        return self.request(
            "GET", "/users/{}/illusts".format(user_id), params=params)

    def user_novels(self, user_id, **params):
        """Read a user's novels (``GET /users/{id}/novels``).

        Candidate parameter: ``page`` (int). The envelope additionally
        carried ``nextCursor`` when more pages existed; the observed value
        was an upstream service URL that cannot be replayed against this
        site. Items are novel summaries without the body text.
        """
        return self.request(
            "GET", "/users/{}/novels".format(user_id), params=params)

    def user_bookmarks(self, user_id, **params):
        """Read a user's public bookmarks (``GET /users/{id}/bookmarks``).

        Candidate envelope: ``{items, pageSize, hasMore, nextCursor,
        hiddenCount}``. ``page=1`` and ``page=2`` returned identical bodies
        (19 items, the same numeric ``nextCursor``), so ``page`` advanced
        nothing here; other paging names come from the reference and were not
        tested. Parameters are still forwarded unchanged.
        """
        return self.request(
            "GET", "/users/{}/bookmarks".format(user_id), params=params)

    def user_followers(self, user_id, **params):
        """Read a user's followers (``GET /users/{id}/followers``).

        Candidate parameter: ``page`` (int). The sampled ``page=1`` and
        ``page=2`` both echoed the page back and answered an empty ``items``
        list, so no item shape is known; whether the list is ever non-empty
        was not established.
        """
        return self.request(
            "GET", "/users/{}/followers".format(user_id), params=params)

    def user_series(self, user_id, **params):
        """Read a user's series list (``GET /users/{id}/series``).

        Candidate parameter: ``page`` (int). The sampled account answered an
        empty list, so no item shape was observed; the reference describes
        items as ``{id, title, caption, total}`` and warns that these ids
        belong to the novel series namespace, while ``series_show`` expects
        illust series ids.
        """
        return self.request(
            "GET", "/users/{}/series".format(user_id), params=params)

    def user_related(self, user_id, **params):
        """Read related users (``GET /users/{id}/related``).

        Candidate envelope: ``{items}`` with the ``{user, previews}`` items
        of ``user_search``. The reference reports no parameter having an
        effect.
        """
        return self.request(
            "GET", "/users/{}/related".format(user_id), params=params)

    # ------------------------------------------------------------------
    # Novels
    # ------------------------------------------------------------------

    def novel_search(self, **params):
        """Search novels (``GET /search/novel``).

        Candidate parameters:
            q (str): Keyword matched against tags; the reference reports an
                empty value answering an empty list.
            page (int): Page number, from 1.
            sort (str): ``'popular'``, ``'new'`` or ``'old'`` per the
                reference; not sent by this project.
            ai (str): ``ai=exclude`` answered 401 ``auth_required`` here, so
                it needs the paid tier; the reference says 403.
            mode (str): ``'text'`` or ``'keyword'``, both paid per the
                reference.

        A work-type filter is rejected instead of ignored: ``type=illust``
        answered 400 ``unsupported_filter_for_scope`` with ``field=type``.
        Items are novel summaries without the body text; the envelope is the
        shared list envelope.
        """
        return self.request("GET", "/search/novel", params=params)

    def novel_show(self, novel_id, **params):
        """Read one novel as a bare object, body included (``GET /novels/{id}``).

        Candidate fields add ``text`` and ``document`` (with
        ``uploadedImages`` and ``pixivImages``) to the summary fields, plus
        optional ``caption``/``captionHtml`` and ``series``. The sampled novel
        returned those keys with an empty top-level ``text`` and a
        ``document.text`` holding only uploaded-image markers (four
        ``uploadedImages`` entries and an empty ``pixivImages``). Nonempty
        prose was not observed; the image descriptions were returned without
        downloading their bytes. The two text fields are not interchangeable.
        """
        return self.request("GET", "/novels/{}".format(novel_id), params=params)

    def novel_comments(self, novel_id, **params):
        """Read a novel's comments (``GET /novels/{id}/comments``).

        Candidate parameter: ``page`` (int). Candidate envelope:
        ``{items, hasMore}``; the sampled novel answered an empty list, so no
        comment object was observed. The reference describes comment fields
        as the illust comment shape plus ``stampId`` and ``stampUrl``.
        """
        return self.request(
            "GET", "/novels/{}/comments".format(novel_id), params=params)

    def novel_related(self, novel_id, **params):
        """Read related novels (``GET /novels/{id}/related``).

        The sampled novel answered an empty list, so neither an item nor a
        ``nextCursor`` value was observed; the reference reports ``page``
        changing nothing, items as novel summaries and ``nextCursor`` as an
        upstream URL that cannot be replayed against this site.
        """
        return self.request(
            "GET", "/novels/{}/related".format(novel_id), params=params)

    # ------------------------------------------------------------------
    # Series and spotlight
    # ------------------------------------------------------------------

    def series_show(self, series_id, **params):
        """Read one illust series as a bare object (``GET /series/{id}``).

        Candidate parameter: ``page`` (int). Candidate body: ``{id, title,
        caption, total, author, items, hasMore}`` without
        ``page``/``pageSize``, with full Illust objects in ``items``. An
        illust series id answered 30 items with ``total: 219`` and
        ``hasMore: true``, while a novel series id answered 200 with an empty
        list, so the two id spaces differ; the reference adds that novel
        ``series.id`` values answer 404. No series search or list route is
        known.
        """
        return self.request("GET", "/series/{}".format(series_id), params=params)

    def spotlight_list(self, **params):
        """Read the spotlight (Pixivision) list (``GET /spotlight``).

        Candidate parameters:
            page (int): Page number, from 1; the reference reports invalid
                values falling back to 1.
            lang (str): ``'zh-cn'`` (what this project sent), ``'zh-tw'``,
                ``'ja'``, ``'ko'`` or ``'en'``; the reference reports unknown
                values falling back to English.

        Candidate envelope: ``{items, page, pageSize, hasMore}``. The sampled
        page returned 20 items while ``pageSize`` said 12, and ``hasMore``
        was ``true``; no further page was fetched, so whether it ever goes
        false was not observed. Candidate item keys: ``id``, ``title``,
        ``caption``, ``coverSvg``, ``cover``, ``tag``, ``tags``, ``date``,
        ``articleUrl`` and ``works`` (empty in the list).
        """
        return self.request("GET", "/spotlight", params=params)

    def spotlight_show(self, spotlight_id, **params):
        """Read one spotlight article as a bare object (``GET /spotlight/{id}``).

        Candidate parameter: ``lang`` (same values as the list; the reference
        reports it also switching the language segment inside ``cover`` and
        ``articleUrl``). Candidate body: ``{id, title, date, description,
        cover, tags, articles, works, relatedLatest, relatedRecommend,
        articleUrl}``. The sampled article had 19 ``articles`` while
        ``works`` and both related item lists were empty. ``/spotlight/0``
        answered 503 ``retryable`` rather than 404; the reference reports a
        malformed id answering 400.
        """
        return self.request(
            "GET", "/spotlight/{}".format(spotlight_id), params=params)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_illusts(self, tag, **params):
        """Read one tag's illusts (``GET /tags/{tag}``).

        The tag comes from the path segment and is percent-encoded as one raw
        segment, so CJK tags work. The route takes the ``illust_search``
        parameters and answers the same envelope shape, but equivalence with
        ``illust_search(q=tag)`` is not established: a request with
        ``page=1&size=24`` returned 25 items from ``/tags/blue`` against 29
        from ``/search/illust?q=blue`` (25 shared), and the two requests were
        not simultaneous, so time or caching could account for the
        difference. The reference's claim that an unknown tag answers 200
        with an empty list was not rechecked.
        """
        return self.request("GET", "/tags/{}".format(quote(tag, safe="")),
                            params=params)

    def tag_search(self, **params):
        """Read the default illust list (``GET /tags/search``).

        ``?q=blue&size=2`` and ``?size=2`` returned identical JSON (11
        items), so ``q`` had no effect on these two calls; the route takes the
        ``illust_search`` filters and answers the same envelope. The
        reference reports that spellings such as ``/tags/autocomplete`` are
        treated as tag names; whether an autocomplete route exists elsewhere
        was not searched for.
        """
        return self.request("GET", "/tags/search", params=params)

    # ------------------------------------------------------------------
    # Account (/me/*; login-only per the reference, shapes unknown)
    # ------------------------------------------------------------------

    def me(self, **params):
        """Read the signed-in account (``GET /me``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown. Nothing above the token header
        is handled by this client.
        """
        return self.request("GET", "/me", params=params)

    def me_capabilities(self, **params):
        """Read the account's capabilities (``GET /me/capabilities``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/capabilities", params=params)

    def me_bookmarks(self, **params):
        """Read the account's bookmarks (``GET /me/bookmarks``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown. Parameters are forwarded
        unchanged.
        """
        return self.request("GET", "/me/bookmarks", params=params)

    def me_likes(self, **params):
        """Read the account's likes (``GET /me/likes``).

        Login-only, and the one account route this project requested:
        without a data-contract header it answered 426 ``upgrade_required``
        with ``requiredDataContract: 2``, and with
        ``x-sakuria-data-contract: 2`` it answered 401
        ``sakuria_session_required``. The authenticated body shape is
        unknown; pass the header through the client's ``headers``.
        """
        return self.request("GET", "/me/likes", params=params)

    def me_following(self, **params):
        """Read the accounts this account follows (``GET /me/following``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/following", params=params)

    def me_notifications(self, **params):
        """Read the account's notifications (``GET /me/notifications``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/notifications", params=params)

    def me_history(self, **params):
        """Read the account's browsing history (``GET /me/history``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/history", params=params)

    def me_settings(self, **params):
        """Read the account's settings (``GET /me/settings``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/settings", params=params)

    def me_illusts(self, **params):
        """Read the account's own illusts (``GET /me/illusts``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/illusts", params=params)

    def me_novels(self, **params):
        """Read the account's own novels (``GET /me/novels``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/novels", params=params)

    def me_series(self, **params):
        """Read the account's own series (``GET /me/series``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/series", params=params)

    def me_credits(self, **params):
        """Read the account's credit balance (``GET /me/credits``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/credits", params=params)

    def me_plus(self, **params):
        """Read the account's subscription tier (``GET /me/plus``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/plus", params=params)

    def me_subscription(self, **params):
        """Read the account's subscription (``GET /me/subscription``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/subscription", params=params)

    def me_favorites(self, **params):
        """Read the account's favorites (``GET /me/favorites``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/favorites", params=params)

    def me_search_history(self, **params):
        """Read the account's search history (``GET /me/search-history``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/search-history", params=params)

    def me_recommend(self, **params):
        """Read the account's recommendations (``GET /me/recommend``).

        Login-only per the supplied reference; this project did not request
        it, so the response shape is unknown.
        """
        return self.request("GET", "/me/recommend", params=params)
