# -*- coding: utf-8 -*-

"""pybooru.api_serika

This module contains every call of the official SerikaART API (``/api/v1``).

SerikaART is neither a Danbooru nor a Moebooru site: it is a self-hosted
Next.js application whose own documentation calls ``/api/v1`` the versioned
"SerikaART API 1.0.0". Every method below is one thin call to
``Serika.request()`` against a route of ``app/api/v1/**/route.ts``, so the
controllers are the contract. ``app/api-docs/endpoints.ts`` documents only 10
of the 16 exported handlers and disagrees with the controllers about the image
``:id`` routes (see below).

The unversioned in-site routes of the same application are frontend internals
with no compatibility promise; the client exposes them with an ``internal_*``
prefix, outside this mixin's stable contract.

Shared v1 facts:
    * Envelope: ``{"success": true, "data": ..., "meta": {...}}``. Methods
      send ``envelope="data"``, so they return ``data`` and leave the whole
      ``meta`` mapping in ``last_call["meta"]``. Three routes do not follow
      it: the index (``/api/v1``) returns a bare object, ``/api/v1/users``
      returns ``{"success", "users", "pagination"}`` (``envelope="users"``),
      and the random-image route returns pixels (``binary=True``).
    * Failures keep their real HTTP status (``400``/``401``/``403``/``404``/
      ``429``/``500``) and a ``{"success": false, "error", "code"}`` body, so
      they surface as ``PybooruHTTPError`` with the parsed body in ``data``.
      The controllers pass ``UNAUTHORIZED`` as the code for **every** API-key
      failure, rate limiting included: a limited key gets HTTP ``429`` with
      ``code: "UNAUTHORIZED"`` (only the unused ``withApiAuth`` helper, and
      the public documentation, say ``RATE_LIMITED``).
    * Authentication: ``Authorization: Bearer sk_serika_*`` or ``X-API-Key``
      (the client attaches the configured key). A missing or malformed key is
      ``401``; a valid key lacking the required permission is ``403``. Only
      ``api_index``, ``stats``, ``user_list`` and ``random_image`` are
      reachable without a key.
    * IDs: the image routes filter on ``images.id`` (``WHERE i.id = $1`` for
      the single-image routes, ``= ANY($1)`` for the batch) — the internal
      bigint, returned as ``id``/``dbid`` — while
      ``app/api-docs/endpoints.ts`` documents the sequential post ID. The
      sequential ID is the separate ``sequential_id`` column, returned as
      ``post_id``. Both appear in responses and are not interchangeable; this
      client sends whatever ID the caller passes.
    * Pagination lives in ``meta.pagination`` (``page``, ``limit``,
      ``total``, ``pages`` and, except for ``/api/v1/users``, ``has_next`` /
      ``has_prev``). Server-side clamps are documented per method; no value is
      clamped, validated or replaced locally.
    * CSV parameters (``tags``, ``ratings``, ``exclude_tags``) are plain
      strings, sent exactly as given: the server splits on commas itself and
      never parses a Rails-style array.

Classes:
    SerikaApi_Mixin -- Contains all official SerikaART ``/api/v1`` calls.
"""

# __future__ imports
from __future__ import absolute_import

# Standard library imports
from urllib.parse import quote


def _segment(value):
    """Escape one raw path segment (image id, user identifier, tag name)."""
    return quote(str(value), safe="")


class SerikaApi_Mixin(object):
    """Contains all official SerikaART API calls.

    * Source: ``app/api/v1/**/route.ts`` in the SerikaART application.
    * Doc: https://serika.art/api-docs
    """

    # ------------------------------------------------------------------
    # API index
    # ------------------------------------------------------------------

    def api_index(self):
        """Get the API index of the official versioned surface.

        Official ``/api/v1`` route; public (no API key). The route returns a
        bare object without the ``success``/``data`` envelope, so it is passed
        through unchanged: name, version, the endpoint map,
        ``authentication`` and ``rate_limits``.

        The advertised rate limits (user 60/min, premium and moderator
        120/min, admin 1000/min) are documentation only: the server enforces
        the ``rate_limit`` column of the API key, which the key-creation route
        clamps per rank (60 for users, 120 for moderators/premium, 1000 for
        admins, 10000 for owners).
        """
        return self.request("GET", "api/v1")

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------

    def image_list(self, page=None, limit=None, tags=None, ratings=None,
                   sort=None, ai=None, q=None, user_id=None, min_width=None,
                   min_height=None):
        """Get a list of images (requires the ``images:read`` permission).

        Official ``/api/v1`` route. Source-aligned and untested: it needs a
        key, and anonymous requests are answered with ``401``.

        Deleted and unlisted images are excluded by the controller.

        Parameters:
            page (int): Page number (the server raises anything below 1 to 1).
            limit (int): Images per page (the server clamps to 1..100).
            tags (str): Comma-separated tag names. The match is an
                intersection: an image must carry **all** of them. The
                controller resolves the names first and answers ``404``
                ``TAG_NOT_FOUND`` only when *some* resolve and others do not
                (a name repeated in the list also counts as a miss, because
                the lookup returns one row per distinct name). When **none**
                of the names exists, or when no image carries the whole
                intersection, the request instead succeeds with an empty
                ``data``.
            ratings (str): Comma-separated ``safe``, ``questionable``,
                ``explicit``. Values outside that set are dropped by the
                server and a result with no valid value falls back to
                ``safe``, so omitting the parameter means ``safe``-only, not
                "everything"; listing all three removes the rating filter.
            sort (str): ``newest``, ``oldest``, ``popular``, ``favorites``,
                ``views`` or ``random`` (random is not deterministic).
            ai (bool): Only AI-generated images.
            q (str): Substring search over tag names, descriptions and
                uploader usernames.
            user_id (str): Uploader ID (the text ``users.id`` key).
            min_width (int): Minimum width in pixels.
            min_height (int): Minimum height in pixels.

        ``meta.pagination`` carries ``page``, ``limit``, ``total`` and
        ``pages``; ``has_next`` and ``has_prev`` are added only for a
        non-empty page (every empty branch returns the counters without them,
        and with ``total: 0`` when the tags resolved to nothing).
        """
        params = {"page": page, "limit": limit, "tags": tags,
                  "ratings": ratings, "sort": sort, "ai": ai, "q": q,
                  "user_id": user_id, "min_width": min_width,
                  "min_height": min_height}
        return self.request("GET", "api/v1/images", params=params,
                            envelope="data")

    def image_show(self, image_id):
        """Get one image with its tags and counters (``images:read``).

        Official ``/api/v1`` route. Source-aligned and untested (needs a key).

        Parameters:
            image_id (int): The **internal** ``images.id`` bigint. The
                controller runs ``WHERE i.id = $1``; the sequential post ID
                that ``app/api-docs/endpoints.ts`` documents for this route is
                a different number. A non-numeric value is answered with
                ``400`` ``INVALID_ID`` and an unknown ID with ``404``
                ``NOT_FOUND``.

        Returns the full row: ``id``/``dbid`` (internal bigint), ``post_id``
        (sequential), ``url``, ``thumbnail_url``, ``original_filename``,
        ``width``, ``height``, ``file_size``, ``content_type``, ``rating``,
        ``is_ai_generated``, ``source``, ``description``, ``tags``,
        ``stats`` (including ``score`` and the comment count), ``user``,
        ``created_at`` and ``updated_at``. Every successful call also
        increments the view counter.

        Unlike the list routes this one applies no ``deleted``/``unlisted``
        and no rating filter, so a soft-deleted or unlisted image is still
        returned by ID.
        """
        return self.request("GET",
                            "api/v1/images/{0}".format(_segment(image_id)),
                            envelope="data")

    def image_delete(self, image_id):
        """Delete an image and all of its dependent rows (``images:delete``).

        Official ``/api/v1`` route; a write, so source-aligned and untested.
        The server removes votes, favorites, comments and tag links in one
        transaction and decrements the affected tag counts. The key owner must
        own the image or hold the ``admin``/``owner`` rank, otherwise ``403``
        ``FORBIDDEN``.

        Parameters:
            image_id (int): The **internal** ``images.id`` bigint (the route
                filters on ``id``, not on the sequential post ID).

        Returns ``{"deleted": true, "id": "<image_id>"}``.
        """
        return self.request("DELETE",
                            "api/v1/images/{0}".format(_segment(image_id)),
                            envelope="data")

    def image_similar(self, image_id, limit=None):
        """Get images sharing tags with a source image (``images:read``).

        Official ``/api/v1`` route. Source-aligned and untested (needs a key).

        Parameters:
            image_id (int): The **internal** ``images.id`` bigint of the
                source image (the controller filters ``WHERE id = $1`` and
                also requires ``deleted = FALSE AND unlisted = FALSE``, so
                deleted or unlisted sources are ``404`` ``NOT_FOUND``).
            limit (int): Matches to return (the server clamps to 1..50).

        Only public images with the **same rating** as the source are
        considered; they are ordered by shared tag count and then by upvotes.
        Returns ``{"source_id": <echo of the path segment>, "similar": [...],
        "count": <int>}``; each entry carries ``id``/``dbid``, ``post_id``,
        ``sequential_id``, ``url``, ``thumbnail_url``, ``width``, ``height``,
        ``rating``, ``is_ai_generated``, ``shared_tags``, up to 10 ``tags``
        and ``stats``.
        """
        return self.request("GET",
                            "api/v1/images/{0}/similar".format(
                                _segment(image_id)),
                            params={"limit": limit}, envelope="data")

    def image_batch(self, ids):
        """Get many images by ID in one request (``images:read``).

        Official ``/api/v1`` route (``POST /api/v1/batch/images``) that
        ``app/api-docs/endpoints.ts`` does not document. Source-aligned and
        untested (needs a key). The list travels as a JSON body
        (``{"ids": [...]}``), not as a query string.

        Parameters:
            ids (list): Image IDs — the **internal** ``images.id`` bigints
                (the controller filters ``WHERE i.id = ANY($1)``). The server
                requires a non-empty list, rejects more than 100 entries with
                ``400`` ``TOO_MANY_IDS``, drops entries it cannot parse as
                integers, and answers ``400`` ``INVALID_IDS`` when none is
                parseable. Strings are accepted as well as integers.

        Returns ``{"images": [...], "found": <int>, "requested": <int>}`` with
        the found images ordered like ``ids``. Each image carries the same
        fields as :meth:`image_list` plus ``sequential_id``, and its ``user``
        is ``None`` for an anonymous uploader.

        As in :meth:`image_show`, these lookups apply no
        ``deleted``/``unlisted`` and no rating filter.
        """
        return self.request("POST", "api/v1/batch/images",
                            data={"ids": ids}, envelope="data")

    # ------------------------------------------------------------------
    # Random
    # ------------------------------------------------------------------

    def random_list(self, count=None, ratings=None, tags=None,
                    exclude_tags=None, min_width=None, min_height=None,
                    max_width=None, max_height=None, ai=None, no_ai=None):
        """Get random images with metadata (requires ``random:read``).

        Official ``/api/v1`` route. Source-aligned and untested: it needs a
        key, and anonymous requests are answered with ``401``.

        Parameters:
            count (int): How many images (the server clamps to 1..50; its
                default is 1).
            ratings (str): Comma-separated ``safe``, ``questionable``,
                ``explicit``; invalid values are dropped and an empty result
                falls back to ``safe``.
            tags (str): Comma-separated names that must all be present. As in
                :meth:`image_list`, ``404`` ``TAG_NOT_FOUND`` is only for a
                *partially* unresolvable list; when none of the names exists,
                or when no image carries the whole intersection, the request
                succeeds with an empty ``data`` and a ``meta.message``.
            exclude_tags (str): Comma-separated names to exclude. Unknown
                names are ignored here (they simply exclude nothing).
            min_width (int): Minimum width in pixels.
            min_height (int): Minimum height in pixels.
            max_width (int): Maximum width in pixels.
            max_height (int): Maximum height in pixels.
            ai (bool): Only AI-generated images (wins over ``no_ai``).
            no_ai (bool): Exclude AI-generated images.

        ``data`` is a **single object** when the effective ``count`` is 1 and
        a list otherwise. No match is not an error: it returns an empty list
        with a ``meta.message``. ``meta`` also carries ``count`` (returned)
        and ``requested``.
        """
        params = {"count": count, "ratings": ratings, "tags": tags,
                  "exclude_tags": exclude_tags, "min_width": min_width,
                  "min_height": min_height, "max_width": max_width,
                  "max_height": max_height, "ai": ai, "no_ai": no_ai}
        return self.request("GET", "api/v1/random", params=params,
                            envelope="data")

    def random_image(self, width, height, fit=None, format=None, quality=None,
                     tags=None, ratings=None, exclude_tags=None, blur=None,
                     grayscale=None, ai=None, no_ai=None, match_size=None,
                     aspect_tolerance=None):
        """Get a random image file resized to the given dimensions.

        Official ``/api/v1`` route; one of the four public v1 routes (with
        :meth:`api_index`, :meth:`stats` and :meth:`user_list`), so it needs
        no API key. Its response is the image itself, returned as
        ``bytes`` (``Content-Type`` ``image/png``, ``image/jpeg`` or
        ``image/webp`` depending on ``format``); the metadata headers
        (``X-Image-Id``, ``X-DBID``, ``X-Post-Id``, ``X-Original-Width``,
        ``X-Original-Height``, ``X-Rating``) are available in
        ``last_call["headers"]``.

        Parameters:
            width (int): Output width in pixels (the server accepts 16..8000
                and answers ``400`` with plain text outside that range).
            height (int): Output height in pixels (same range).
            fit (str): ``cover``, ``contain``, ``fill``, ``inside`` or
                ``outside``; anything else falls back to ``cover``.
            format (str): ``png``, ``jpeg``/``jpg`` or ``webp``; anything else
                produces PNG.
            quality (int): Output quality (the server clamps to 1..100; it
                only changes JPEG/WebP output).
            tags (str): Comma-separated names. This route never fails on
                them: the tag constraint is applied only when every name
                exists **and** some image carries all of them, and it is
                dropped entirely otherwise (the controller comment says the
                fallback is a placeholder, but the query is simply left
                without any tag condition), so the result can ignore the
                requested tags instead of answering ``404`` or an empty
                image.
            ratings (str): Comma-separated ratings; invalid values are dropped
                and an empty result falls back to ``safe``.
            exclude_tags (str): Comma-separated names to exclude. Unknown
                names exclude nothing, and the exclusion is only built when
                the names exist and match some image.
            blur (bool): Apply a Gaussian blur.
            grayscale (bool): Convert to grayscale.
            ai (bool): Only AI-generated images (wins over ``no_ai``).
            no_ai (bool): Exclude AI-generated images.
            match_size (bool): Prefer candidates at least as large as the
                requested size (capped at 400x400) whose aspect ratio is
                within ``aspect_tolerance``; without a match the server falls
                back to a completely random image.
            aspect_tolerance (float): Allowed aspect-ratio difference for
                ``match_size`` (the server's default is ``0.2``).

        When nothing matches, the server answers ``200`` with a gray PNG
        placeholder (``Cache-Control`` with ``stale-while-revalidate``), so a
        placeholder is indistinguishable from a hit except through the
        metadata headers — only a hit carries the ``X-*`` identifiers. A
        failure inside the controller (fetching the source image, resizing)
        is answered with ``200`` too, but with a red placeholder PNG and
        ``Cache-Control: no-cache``; only a failing placeholder yields the
        ``500`` plain-text body. Each successful request also increments the
        view counter of the selected image.
        """
        params = {"fit": fit, "format": format, "quality": quality,
                  "tags": tags, "ratings": ratings,
                  "exclude_tags": exclude_tags, "blur": blur,
                  "grayscale": grayscale, "ai": ai, "no_ai": no_ai,
                  "match_size": match_size,
                  "aspect_tolerance": aspect_tolerance}
        path = "api/v1/random/{0}/{1}/image.png".format(_segment(width),
                                                        _segment(height))
        return self.request("GET", path, params=params, binary=True)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_list(self, page=None, limit=None, q=None, type=None, sort=None,
                 min_count=None):
        """Get a list of tags (requires the ``tags:read`` permission).

        Official ``/api/v1`` route. Source-aligned and untested: it needs a
        key, and anonymous requests are answered with ``401``.

        Parameters:
            page (int): Page number (the server raises anything below 1 to 1).
            limit (int): Tags per page (the server clamps to 1..500; its
                default is 100).
            q (str): Case-insensitive substring match on the tag name.
            type (str): ``general``, ``artist``, ``character``, ``copyright``
                or ``meta``. Any other value is ignored (no type filter).
            sort (str): ``count``, ``name``, ``newest`` or ``oldest``; any
                other value falls back to ``count``.
            min_count (int): Only tags with at least this usage count.

        Each entry is ``{"id", "name", "type", "count", "created_at"}`` and
        ``meta.pagination`` carries ``page``, ``limit``, ``total``, ``pages``,
        ``has_next`` and ``has_prev``.
        """
        params = {"page": page, "limit": limit, "q": q, "type": type,
                  "sort": sort, "min_count": min_count}
        return self.request("GET", "api/v1/tags", params=params,
                            envelope="data")

    def tag_show(self, name):
        """Get one tag with sample images (requires ``tags:read``).

        Official ``/api/v1`` route that ``app/api-docs/endpoints.ts`` does not
        document. Source-aligned and untested (needs a key).

        Parameters:
            name (str): The tag name. The controller lowercases and trims it
                before matching, and an unknown name is ``404`` ``NOT_FOUND``.
                Characters outside ``A-Za-z0-9_.-~`` are percent-escaped here.

        Returns ``{"id", "name", "type", "count", "created_at",
        "sample_images"}``. ``count`` is recomputed from public images instead
        of the stored counter, and ``sample_images`` holds up to five ``safe``
        public images (``id``, ``thumbnail_url``, ``rating``) ordered by
        upvotes.
        """
        return self.request("GET",
                            "api/v1/tags/{0}".format(_segment(name)),
                            envelope="data")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def user_list(self, page=None, limit=None, q=None, sort=None):
        """Get the user directory.

        Official ``/api/v1`` route that ``app/api-docs/endpoints.ts`` does not
        document, and one of the four public routes (with :meth:`api_index`,
        :meth:`stats` and :meth:`random_image`): it requires no API key.

        Parameters:
            page (int): Page number (the server raises anything below 1 to 1).
            limit (int): Users per page (the server clamps to 1..100; its
                default is 50).
            q (str): Case-insensitive substring match on the username.
            sort (str): ``newest`` (default), ``oldest``, ``alphabetical``,
                ``alphabetical-reverse``, ``uploads`` or ``uploads-asc``. Any
                other value falls back to ``newest``.

        ``request()`` takes ``envelope="users"`` here: this route returns
        ``{"success": true, "users": [...], "pagination": {...}}`` — no
        ``data`` key and no ``meta.timestamp`` — so the method returns the
        ``users`` list and leaves the pagination mapping in
        ``last_call["meta"]["pagination"]`` (``page``, ``limit``, ``total``,
        ``pages``, without ``has_next``/``has_prev``).

        Auto-generated ``user_<6 alphanumerics>`` placeholder accounts are
        excluded, so this count is lower than ``stats()['totals']['users']``.
        Each entry is ``{"_id", "id", "username", "avatarUrl", "rank",
        "createdAt", "uploadCount"}`` — note the camelCase names, which the
        rest of the v1 surface does not use.
        """
        params = {"page": page, "limit": limit, "q": q, "sort": sort}
        return self.request("GET", "api/v1/users", params=params,
                            envelope="users")

    def user_show(self, identifier):
        """Get one user profile (requires the ``users:read`` permission).

        Official ``/api/v1`` route. Source-aligned and untested: it needs a
        key, and anonymous requests are answered with ``401``.

        Parameters:
            identifier (str): A user ID (the text ``users.id`` key) or a
                username; the controller tries ``WHERE id = $1`` first and
                then falls back to a case-insensitive ``LOWER(username)``
                match. An unknown identifier is ``404`` ``NOT_FOUND``.

        Returns ``{"id", "username", "avatar_url", "rank", "stats",
        "created_at"}`` where ``stats`` holds ``images``, ``total_upvotes``
        and ``total_views``.
        """
        return self.request("GET",
                            "api/v1/users/{0}".format(_segment(identifier)),
                            envelope="data")

    # ------------------------------------------------------------------
    # Search and trending
    # ------------------------------------------------------------------

    def search(self, q, type=None, limit=None, ratings=None):
        """Search images, tags and users at once (requires ``images:read``).

        Official ``/api/v1`` route that ``app/api-docs/endpoints.ts`` does not
        document. Source-aligned and untested (needs a key).

        Parameters:
            q (str): The query. The server requires at least 2 characters and
                otherwise answers ``400`` ``INVALID_QUERY``.
            type (str): ``all`` (default), ``images``, ``tags`` or ``users``.
                Any other value runs no branch at all and returns an empty
                object.
            limit (int): Results per section (the server clamps to 1..50; its
                default is 10).
            ratings (str): Comma-separated ratings; it only affects the
                ``images`` section, where invalid values are dropped and an
                empty result falls back to ``safe`` (all three valid values
                remove the filter).

        Returns ``{"images": [...], "tags": [...], "users": [...]}`` with only
        the requested sections present, and ``meta`` echoing ``query`` and
        ``type``. Image hits are ordered by upvotes and match a tag name, the
        description or the uploader username.
        """
        params = {"q": q, "type": type, "limit": limit, "ratings": ratings}
        return self.request("GET", "api/v1/search", params=params,
                            envelope="data")

    def trending(self, period=None, limit=None, ratings=None):
        """Get trending images and tags (requires ``images:read``).

        Official ``/api/v1`` route that ``app/api-docs/endpoints.ts`` does not
        document. Source-aligned and untested (needs a key).

        Parameters:
            period (str): ``day``, ``week`` or ``month``; any other value
                falls back to ``day``.
            limit (int): Images to return (the server clamps to 1..50; its
                default is 20).
            ratings (str): Comma-separated ``safe``, ``questionable``,
                ``explicit``. The value outside that set is dropped, an empty
                result falls back to ``safe``, and passing all three valid
                values removes the rating filter entirely.

        Ranking uses ``upvotes * 3 + favorites * 5 + views * 0.1`` over the
        images uploaded in the period. Returns ``{"period", "images", "tags"}``
        where each image carries ``trend_score`` (rounded), up to five tag
        names and ``uploaded_at``, and ``tags`` holds at most 20 entries
        (``id``, ``name``, ``type``, ``trending_count``, ``total_count``)
        regardless of ``limit``.
        """
        params = {"period": period, "limit": limit, "ratings": ratings}
        return self.request("GET", "api/v1/trending", params=params,
                            envelope="data")

    # ------------------------------------------------------------------
    # Stats and upload
    # ------------------------------------------------------------------

    def stats(self):
        """Get the platform statistics.

        Official ``/api/v1`` route and public: it needs no API key. Returns
        ``{"totals": {"images", "tags", "users"}, "images_by_rating": {"safe",
        "questionable", "explicit"}, "images_by_type": {"ai_generated",
        "non_ai"}, "activity": {"uploads_last_24h"}}``, all restricted to
        public (non-deleted, non-unlisted) images. ``totals["users"]`` counts
        every user row, including the placeholder accounts that
        :meth:`user_list` hides.
        """
        return self.request("GET", "api/v1/stats", envelope="data")

    def upload(self, file, tags, rating, is_ai_generated=None, source=None,
               description=None):
        """Upload an image (requires the ``upload`` permission).

        Official ``/api/v1`` route; a write, so source-aligned and untested.
        The key must carry the ``upload`` permission, which the key-creation
        route only grants to ``moderator``, ``admin`` and ``owner`` ranks.

        This is the only endpoint that sends a multipart body, so ``file`` and
        the metadata fields are form fields. The server generates a 320x320
        JPEG thumbnail, reuses or creates tag rows, and assigns the next
        sequential post ID.

        Parameters:
            file: The image. Pass a requests tuple
                ``(filename, fileobj, content_type)`` and **state the MIME
                explicitly**: the controller accepts only ``image/jpeg``,
                ``image/png``, ``image/gif`` and ``image/webp`` up to 50MB,
                and a bare file object is sent without a part
                ``Content-Type`` (the server reads it as
                ``application/octet-stream`` and answers ``400``
                ``INVALID_FILE_TYPE``). The caller owns the file object's
                lifetime. Oversized files are ``400`` ``FILE_TOO_LARGE``.
                Values are forwarded verbatim: this client does not sniff or
                guess the type.
            tags (str): The tags, as text. The field is sent verbatim and the
                server accepts either a JSON array (``[{"name": "nature",
                "type": "general"}]``, or plain strings) or a comma-separated
                list. Fewer than one or more than 100 tags is ``400``
                ``MISSING_TAGS`` / ``TOO_MANY_TAGS``; unknown tag types fall
                back to ``general`` server-side. The client never serialises
                this value itself.
            rating (str): ``safe``, ``questionable`` or ``explicit``; anything
                else is ``400`` ``INVALID_RATING``.
            is_ai_generated (bool): Mark the image as AI-generated. The server
                compares the form value with the string ``true`` (the shared
                transport encodes booleans that way). The controller also
                accepts the ``isAIGenerated`` spelling, which this client does
                not send.
            source (str): The original source URL.
            description (str): The image description.

        Returns the new image (``id``/``dbid``, ``post_id``, ``url``,
        ``thumbnail_url``, ``width``, ``height``, ``file_size``,
        ``content_type``, ``rating``, ``is_ai_generated``, ``tags``,
        ``created_at``) with ``meta.message``.
        """
        data = {"tags": tags, "rating": rating,
                "is_ai_generated": is_ai_generated, "source": source,
                "description": description}
        return self.request("POST", "api/v1/upload", data=data,
                            files={"file": file}, envelope="data")
