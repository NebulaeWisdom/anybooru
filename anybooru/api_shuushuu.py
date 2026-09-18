# -*- coding: utf-8 -*-

"""Native read-only JSON methods for e-shuushuu (e-shuushuu.net).

e-shuushuu runs a FastAPI backend whose own title is "Shuushuu API 2.0.0";
the frontend is a SvelteKit application. Unlike the old single-script
Gelbooru API, every route is a REST path below ``/api/v1`` and every method
here is a thin ``Shuushuu.request()`` call with the full site-relative path
(``api/v1/...``) already included. The machine-readable contract is the
site's own OpenAPI document:

    * OpenAPI: https://e-shuushuu.net/api/openapi.json
    * Swagger UI: https://e-shuushuu.net/api/docs

Shared facts:
    * Base URL: ``https://e-shuushuu.net``. Bodies are JSON in and out
      (uploads use ``multipart/form-data``); timestamps are ISO 8601 UTC,
      for example ``2026-09-18T15:02:36Z``.
    * List pagination is ``page`` (from 1) and ``per_page`` (default 20,
      maximum 100); a larger ``per_page`` is rejected with **422** whose
      detail says "Input should be less than or equal to 100". List bodies
      are ``{"total", "page", "per_page", "<resource>": [...]}``, where the
      array key matches the resource: ``images``, ``tags``, ``comments``,
      ``users`` or ``news``. The tag search route (``search``) is the
      exception: it takes ``limit`` (default 20) and ``offset`` (default 0)
      and answers ``{"query", "entity", "hits", "total", "limit",
      "offset"}``.
    * Tag filters on the image routes take **numeric tag IDs in a
      comma-separated string** (``tags='46,169'``), never tag names. A name
      is resolved first through ``search(q=...)`` or
      ``tag_list(search=...)``. The string is sent exactly as given: this
      client does not split, join or convert Python lists.
    * ``status`` on the image list is an array parameter: pass a sequence
      and the transport repeats the key (``?status=1&status=2``). Every
      other multi-value parameter is a comma string.
    * Errors are FastAPI's: 404 with ``{"detail": "<message>"}`` (e.g. an
      unknown image), 422 with ``{"detail": [{"type", "loc", "msg",
      "ctx"}]}`` for an out-of-range parameter, 401 when a protected path
      is read without a token.
    * Nothing is unwrapped, renamed, clamped, defaulted, retried or
      paged locally: the JSON body is returned exactly as it arrived,
      envelopes included.
    * Authentication is not handled here. The 36 native ``GET`` methods
      include public-resource reads and one explicitly private read,
      ``user_ratings`` (the user themselves or a moderator holding
      ``USER_EDIT_PROFILE``). Viewer-dependent history fields and the
      ``reported`` filter have permission rules; not every read or parameter
      combination has been exercised anonymously. No method logs in on its
      own, and personal/admin GET routes must not be called public merely
      because their HTTP method is GET.
    * Not wrapped because they are not JSON reads of this kind: writes
      (upload, tag/rating/favorite/report/comment edits), admin and privmsg
      routes, permission-bound report/ML/suggestion routes, the
      recommendation, bookmark and ``/users/me`` profile routes, the
      duplicate ``/favorites/*`` routes, banners, donations and
      character-source links, plus ``images.atom`` / ``tags/{id}/
      images.atom`` (Atom XML) and ``images/random`` (a 302 redirect).
      ``Shuushuu.request()`` supports JSON routes, not Atom or media decoding.

Corrections and additions to the supplied session reference, per this
schema:
    * ``images/{image_id}/reposts`` takes no pagination at all; its body
      is ``{total, items}`` without ``page``/``per_page``.
    * ``users/{user_id}/ratings`` accepts more than ``page``/``per_page``:
      also ``min_rating``/``max_rating`` (1-10, filtering the subject
      user's own score) and ``sort_by`` (``image_id``, ``rating``,
      ``rated_at``; default ``image_id``).
    * ``users/{user_id}/ratings`` is private (self or a moderator with
      ``USER_EDIT_PROFILE``), and the ``reported`` image filter needs
      ``report_view``; these are not anonymous reads, so the reference's
      blanket "every read works anonymously" claim is wrong about them.
    * ``images/{image_id}/similar`` also returns the ``query_image_id``
      alongside the hits, which the reference does not mention.

One inconsistency inside the official document itself: the tags route
description ends with the example ``/tags?type_id=1`` although the
declared query parameter is named ``type``. The declared parameter wins
here; ``tag_list(type=1)`` is the working spelling.

Which routes have actually been called against the live site is recorded
in docs/verification.md.

Classes:
    ShuushuuApi_Mixin -- e-shuushuu image, tag, user, comment and site reads.
"""

# __future__ imports
from __future__ import absolute_import

# Standard library imports
from urllib.parse import quote


def _segment(value):
    """Escape one raw path segment (image, tag, user, comment or news id)."""
    return quote(str(value), safe="")


class ShuushuuApi_Mixin(object):
    """Native e-shuushuu API calls.

    * OpenAPI: https://e-shuushuu.net/api/openapi.json
    * Doc: https://e-shuushuu.net/api/docs
    """

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------

    def image_list(self, **params):
        """Get a paginated list of images (``GET api/v1/images``).

        The main image search. Every query parameter is passed through
        untouched, so the spellings and value formats below are the ones the
        server receives.

        Parameters:
            tags (str): Comma-separated tag IDs to require, e.g.
                ``'46,169'``. Sent as given; a list is not converted.
            tags_mode (str): ``'any'`` (default) keeps images carrying at
                least one of ``tags``; ``'all'`` requires every one.
            exclude_tags (str): Comma-separated tag IDs to exclude, e.g.
                ``'4,5,6'``.
            exclude_descendants (bool): ``True`` also excludes each excluded
                tag's child tags (its whole hierarchy); default ``False``,
                which excludes the tag itself only.
            tag_depth (int): How many levels of child tags the ``tags``
                filter includes, 0-9. ``0`` is the exact tag only, ``1``
                adds direct children, up to ``9``; omit for full hierarchy.
            missing_tag_types (str): Comma-separated tag type IDs the image
                must be MISSING: ``1`` Theme, ``2`` Source, ``3`` Artist,
                ``4`` Character.
            missing_tag_types_mode (str): ``'any'`` (default) or ``'all'``
                for the missing-type test.
            user_id (int): Only images uploaded by this user.
            favorited_by_user_id (int): Only images this user favorited.
            exclude_user_id (str): Comma-separated user IDs whose uploads
                are hidden, e.g. ``'5,6'``.
            exclude_favorited_by_user_id (str): Comma-separated user IDs;
                hide images any of them favorited.
            commenter (int): Only images this user commented on.
            exclude_commenter (str): Comma-separated user IDs; hide images
                any of them commented on.
            commentsearch (str): Text searched inside a single comment.
                ``all_words`` semantics: every term must appear as a
                case-insensitive substring, ``"quoted phrase"`` keeps word
                order and ``-term`` excludes. A blank value filters
                nothing. Every term is evaluated against one comment row,
                not the image's comments together.
            commentsearch_mode (str): ``'all_words'`` (default), ``'like'``
                (the whole string as one substring, ``%``/``_`` treated as
                literals), or ``'natural'``/``'boolean'``, which the server
                accepts but treats as ``all_words``.
            hascomments (bool): ``True`` only images with comments,
                ``False`` only images without.
            date_from (str) / date_to (str): Upload date bounds as
                ``YYYY-MM-DD``; both inclusive.
            min_width (int) / max_width (int): Width bounds in pixels,
                each at least 1.
            min_height (int) / max_height (int): Height bounds in pixels,
                each at least 1.
            min_rating (float): Minimum average rating, 1-10.
            min_favorites (int): Minimum favorite count, at least 0.
            min_num_ratings (int): Minimum number of ratings, at least 0.
            status (int or sequence of int): Status filter; repeat the
                parameter for several values. ``-4`` Review, ``-2``
                Inappropriate, ``-1`` Repost, ``0`` Other, ``1`` Active,
                ``2`` Spoiler.
            reported (bool): Only images with a pending report. Requires
                the ``report_view`` permission and is ignored for other
                viewers, so it is not an anonymous filter.
            include_comments (bool): ``True`` bundles every comment on the
                returned images into the response's ``comments`` map,
                grouped by image id; default ``False``, and then
                ``comments`` is null.
            page (int): Page number, from 1; default 1.
            per_page (int): Images per page, 1-100; default 20. A larger
                value is rejected with 422.
            sort_by (str): ``image_id``, ``date_added``, ``last_post``,
                ``total_pixels``, ``bayesian_rating`` or ``favorites``.
                Default ``image_id``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "images", "comments"}``.
        ``comments`` is null unless ``include_comments`` is true, otherwise
        it maps each image id to the list of that image's comments. Each
        ``images`` entry carries ``image_id``, ``filename``, ``ext``,
        ``original_filename``, ``md5_hash``, ``filesize``, ``width``,
        ``height``, ``caption``, ``miscmeta``, ``source_url``, ``status``,
        ``rating``, ``bayesian_rating``, ``num_ratings``, ``favorites``,
        ``posts`` (the comment count), ``user_id``, ``user`` (user_id,
        username, avatar, user_title, groups, avatar_url), ``date_added``,
        ``locked``, ``medium``, ``large``, ``replacement_id``,
        ``r2_location``, ``tags`` (each with tag_id, title, type,
        usage_count, context_source_tag_id, type_name), ``is_favorited``,
        ``user_rating``, ``prev_image_id``, ``next_image_id`` (null in list
        results), ``has_open_report``, ``reason_category``,
        ``status_reason``, ``ml_suggestion_count``, ``url``,
        ``thumbnail_url``, ``medium_url`` and ``large_url``.
        """
        return self.request("GET", "api/v1/images", params=params)

    def image_show(self, image_id):
        """Get one image (``GET api/v1/images/{image_id}``).

        Parameters:
            image_id (int): The image number, the digits in the image page
                URL (``/images/<image_id>``).

        Returns one image object without an envelope, carrying the same
        fields as an ``image_list`` entry; unlike in list results,
        ``prev_image_id`` and ``next_image_id`` are filled with the
        neighbouring images. An unknown id answers 404.
        """
        return self.request("GET",
                            "api/v1/images/{0}".format(_segment(image_id)))

    def image_tags(self, image_id):
        """Get all tags of an image (``GET api/v1/images/{image_id}/tags``).

        Parameters:
            image_id (int): Image number.

        Returns ``{"image_id", "tags"}`` where each tag is ``{"tag_id",
        "tag", "type_id"}`` and ``tag`` is the tag's name. Not paginated:
        the whole tag list of the image is returned at once.
        """
        return self.request("GET", "api/v1/images/{0}/tags".format(
            _segment(image_id)))

    def image_tag_history(self, image_id, **params):
        """Get an image's tag add/remove history
        (``GET api/v1/images/{image_id}/tag-history``).

        Parameters:
            image_id (int): Image number.
            page (int): Page number, from 1; default 1.
            per_page (int): Entries per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "items"}``, most recent
        first. Each item carries ``tag_history_id``, ``image_id``,
        ``tag_id``, ``action``, ``user`` (user_id, username, avatar,
        user_title, groups, avatar_url), ``date`` and ``tag`` (tag_id,
        title, type, usage_count). Additions still on the image are derived
        from the current tag links; removals and adds of tags no longer
        linked come from the history table.
        """
        return self.request("GET", "api/v1/images/{0}/tag-history".format(
            _segment(image_id)), params=params)

    def image_status_history(self, image_id, **params):
        """Get an image's status-change history
        (``GET api/v1/images/{image_id}/status-history``).

        Parameters:
            image_id (int): Image number.
            page (int): Page number, from 1; default 1.
            per_page (int): Entries per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "items"}``. Each item
        carries ``id``, ``image_id``, ``old_status``, ``old_status_label``,
        ``new_status``, ``new_status_label``, ``reason_category``,
        ``reason``, ``report_id``, ``review_id``, ``user`` and
        ``created_at``. ``user`` is present only for publicly visible
        transitions (repost, spoiler, active); the free-text ``reason`` is
        shown only for public destinations, or to the image's owner and
        moderators, while ``reason_category`` is always shown.
        """
        return self.request("GET", "api/v1/images/{0}/status-history".format(
            _segment(image_id)), params=params)

    def image_reposts(self, image_id):
        """Get the images currently marked as reposts of an image
        (``GET api/v1/images/{image_id}/reposts``).

        Parameters:
            image_id (int): Image number of the original.

        This route takes no pagination: its body is ``{"total", "items"}``
        with no ``page``/``per_page``, because a handful of reposts per
        image is expected. Each item is ``{"image_id", "user", "marked_at"}``
        where ``user`` is who marked the repost (or null). The list comes
        from the live ``replacement_id`` pointer, filtered to images whose
        status is still reposted.
        """
        return self.request("GET", "api/v1/images/{0}/reposts".format(
            _segment(image_id)))

    def image_reviews(self, image_id, **params):
        """Get an image's closed review sessions
        (``GET api/v1/images/{image_id}/reviews``).

        Parameters:
            image_id (int): Image number.
            page (int): Page number, from 1; default 1.
            per_page (int): Entries per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "items"}`` of completed
        reviews only; open or in-progress sessions are excluded. Each item
        is ``{"review_id", "reason_category", "reason_category_label",
        "outcome", "outcome_label", "created_at", "closed_at"}``. Internal
        fields (initiator, votes) are not exposed.
        """
        return self.request("GET", "api/v1/images/{0}/reviews".format(
            _segment(image_id)), params=params)

    def image_favorites(self, image_id, **params):
        """Get the users who favorited an image
        (``GET api/v1/images/{image_id}/favorites``).

        Parameters:
            image_id (int): Image number.
            page (int): Page number, from 1; default 1.
            per_page (int): Users per page, 1-100; default 20.
            sort_by (str): ``user_id`` (default), ``username``,
                ``date_joined``, ``last_login``, ``last_active``,
                ``image_posts``, ``posts`` or ``favorites``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "users"}``. Each user
        carries ``user_id``, ``username``, ``user_title``, ``avatar``,
        ``avatar_url``, ``groups``, ``admin``, ``active``, ``posts``,
        ``image_posts``, ``favorites``, ``date_joined``, ``last_login``,
        ``last_active``, ``location``, ``website``, ``interests``,
        ``gender`` and ``maximgperday``.
        """
        return self.request("GET", "api/v1/images/{0}/favorites".format(
            _segment(image_id)), params=params)

    def image_ratings(self, image_id, **params):
        """Get the users who rated an image, with their scores
        (``GET api/v1/images/{image_id}/ratings``).

        Parameters:
            image_id (int): Image number.
            page (int): Page number, from 1; default 1.
            per_page (int): Users per page, 1-100; default 20.
            sort_by (str): ``rating`` (default), ``date``, ``user_id``,
                ``username`` or ``date_joined``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "users"}``. Each entry is a
        user profile (username, location, website, interests, user_title,
        avatar, avatar_url, gender, posts, image_posts, favorites, user_id,
        date_joined, last_login, last_active, active, admin, groups,
        maximgperday) plus ``rating`` (the score given, an integer) and
        ``rated_at`` (or null).
        """
        return self.request("GET", "api/v1/images/{0}/ratings".format(
            _segment(image_id)), params=params)

    def image_similar(self, image_id, **params):
        """Find images similar to an image through IQDB
        (``GET api/v1/images/{image_id}/similar``).

        Parameters:
            image_id (int): Image number of the source image.
            threshold (float): Minimum similarity score, 0-100. Omitted
                means no minimum.

        IQDB is queried with the image's thumbnail and the matches come back
        ordered by similarity, highest first, with the query image itself
        excluded. Returns ``{"query_image_id", "similar_images"}``; each
        similar image carries the fields of an image object plus
        ``similarity_score``.
        """
        return self.request("GET", "api/v1/images/{0}/similar".format(
            _segment(image_id)), params=params)

    def image_by_hash(self, md5_hash):
        """Look an image up by file MD5
        (``GET api/v1/images/search/by-hash/{md5_hash}``).

        Parameters:
            md5_hash (str): The 32-character MD5 of the file, e.g.
                ``'de9c2f0aa6b358e3f041d2c933c31785'``. Sent as one path
                segment and escaped if it contains anything unsafe.

        Returns ``{"md5_hash", "found", "images"}`` where ``found`` is the
        number of exact matches and ``images`` holds them as basic image
        objects (image_id, filename, ext, md5_hash, filesize, width,
        height, caption, source_url, status, rating, counts, uploader,
        dates, url and thumbnail/medium/large urls) without the embedded
        ``tags`` array of an ``image_list`` entry.
        """
        return self.request("GET",
                            "api/v1/images/search/by-hash/{0}".format(
                                _segment(md5_hash)))

    def image_stats(self):
        """Get overall image statistics
        (``GET api/v1/images/stats/summary``).

        Returns ``{"total_images", "total_favorites", "average_rating"}``
        for the whole site.
        """
        return self.request("GET", "api/v1/images/stats/summary")

    def image_import_sites(self):
        """List the sites the URL importer accepts
        (``GET api/v1/images/import-sites``).

        Returns a bare array of ``{"site", "example_url"}`` objects, one per
        supported importer with a sample URL shape. Public, static and
        cacheable; not paginated. The upload page fetches it to build its
        supported-sites popover, so the list cannot drift from the importer
        registry.
        """
        return self.request("GET", "api/v1/images/import-sites")

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_list(self, **params):
        """List and search tags (``GET api/v1/tags``).

        Parameters:
            search (str): Tag name search. Fewer than 3 characters match as
                a prefix (``'sa'`` finds ``sakura kinomoto``); 3 or more
                characters match every word as a case-insensitive substring
                in any order, so ``'sakura kinomoto'`` also finds
                ``kinomoto sakura``. Omitted lists every tag.
            type (int): Tag type filter: ``1`` Theme, ``2`` Source,
                ``3`` Artist, ``4`` Character.
            ids (str): Comma-separated tag IDs to fetch precisely, e.g.
                ``'1,2,3'``. Non-numeric entries are skipped and reported
                back in ``invalid_ids``.
            parent_tag_id (int): Only the child tags of this parent tag.
            exclude_aliases (bool): ``True`` drops alias tags and keeps only
                canonical ones; default ``False``.
            page (int): Page number, from 1; default 1.
            per_page (int): Tags per page, 1-100; default 20.
            sort_by (str): ``usage_count``, ``title``, ``date_added``,
                ``tag_id`` or ``type``. The schema gives no default.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "tags", "invalid_ids"}``.
        Each tag carries ``tag_id``, ``title``, ``desc``, ``type`` (0 All,
        1 Theme, 2 Source, 3 Artist, 4 Character), ``date_added``,
        ``usage_count``, ``is_alias``, and for aliases ``alias_of`` (the
        canonical tag's id), ``alias_of_name`` and
        ``alias_of_usage_count``. There is no ``limit`` parameter: passing
        one is ignored and the page size stays ``per_page``.
        """
        return self.request("GET", "api/v1/tags", params=params)

    def tag_show(self, tag_id):
        """Get one tag with its usage statistics
        (``GET api/v1/tags/{tag_id}``).

        Parameters:
            tag_id (int): Tag ID, the number used to filter images, for
                example ``46`` for ``long hair``.

        Returns one tag object without an envelope: every ``tag_list``
        field, plus ``total_image_count`` (images counted through the child
        hierarchy), ``aliased_tag_id``, ``aliases``, ``parent_tag_id``,
        ``child_count``, ``created_by`` (a user summary), ``links``
        (link_id, url, date_added, dead_at, archive_url, position, site,
        external_id), ``sources`` and ``characters`` (linked tags with
        link_id, picture, shared_image_count). An unknown id answers 404.
        """
        return self.request("GET",
                            "api/v1/tags/{0}".format(_segment(tag_id)))

    def tag_images(self, tag_id, **params):
        """Get the images carrying one tag
        (``GET api/v1/tags/{tag_id}/images``).

        Aliases are resolved to the canonical tag and the child tags of the
        hierarchy are included: asking for ``dress`` also returns
        ``sundress``, ``cocktail dress`` and so on. For several tags at
        once use ``image_list(tags='1,2,3')`` instead.

        Parameters:
            tag_id (int): Tag ID.
            tag_depth (int): How many levels of child tags to include, 0-9.
                ``0`` is the exact tag only, ``1`` adds direct children, up
                to ``9``; omit for the full hierarchy.
            page (int): Page number, from 1; default 1.
            per_page (int): Images per page, 1-100; default 20.
            sort_by (str): ``image_id``, ``date_added``, ``last_post``,
                ``total_pixels``, ``bayesian_rating`` or ``favorites``.
                Default ``image_id``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "images"}`` with basic image
        objects: image_id, filename, ext, original_filename, md5_hash,
        filesize, width, height, caption, miscmeta, source_url, status,
        rating, bayesian_rating, num_ratings, favorites, posts, user_id,
        user, date_added, locked, medium, large, replacement_id,
        r2_location, url, thumbnail_url, medium_url and large_url. Unlike
        an ``image_list`` entry they have no embedded ``tags`` array, no
        ``is_favorited``/``user_rating`` and no neighbouring ids. This route
        does not apply the same default status visibility as ``/images``,
        so its ``total`` for the same tag can differ from
        ``image_list(tags='<id>')``.
        """
        return self.request("GET", "api/v1/tags/{0}/images".format(
            _segment(tag_id)), params=params)

    def tag_characters(self, tag_id, **params):
        """Get the character tags linked to a source tag
        (``GET api/v1/tags/{tag_id}/characters``).

        Parameters:
            tag_id (int): Tag ID of a Source-type tag. A tag of any other
                type answers 400, and an unknown tag answers 404.
            page (int): Page number, from 1; default 1.
            per_page (int): Characters per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "tags", "invalid_ids"}``
        where each entry is a tag object (tag_id, title, desc, type,
        date_added, usage_count, is_alias, alias_of, alias_of_name,
        alias_of_usage_count).
        """
        return self.request("GET", "api/v1/tags/{0}/characters".format(
            _segment(tag_id)), params=params)

    def tag_history(self, tag_id, **params):
        """Get a tag's metadata change history
        (``GET api/v1/tags/{tag_id}/history``).

        Parameters:
            tag_id (int): Tag ID.
            page (int): Page number, from 1; default 1.
            per_page (int): Entries per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "items"}`` covering
        renames, type changes, description changes, alias changes,
        inheritance changes and character-source links. Each item carries
        ``id``, ``tag_id``, ``action_type``, the old/new pairs
        (``old_title``/``new_title``, ``old_type``/``new_type``,
        ``old_desc``/``new_desc``, ``old_alias_of``/``new_alias_of``,
        ``old_parent_id``/``new_parent_id``, ``old_archive_url``/
        ``new_archive_url``), the involved tags (``alias_tag``,
        ``parent_tag``, ``character_tag``, ``source_tag``, ``subject_tag``),
        ``link_url``, ``user`` and ``created_at``.
        """
        return self.request("GET", "api/v1/tags/{0}/history".format(
            _segment(tag_id)), params=params)

    def tag_usage_history(self, tag_id, **params):
        """Get a tag's add/remove history on images
        (``GET api/v1/tags/{tag_id}/usage-history``).

        Parameters:
            tag_id (int): Tag ID.
            page (int): Page number, from 1; default 1.
            per_page (int): Entries per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "items"}``, most recent
        first, merging upload-time adds from the image tag links with the
        edit history. Each item carries ``tag_history_id``, ``image_id``,
        ``tag_id``, ``action``, ``user`` and ``date``.
        """
        return self.request("GET", "api/v1/tags/{0}/usage-history".format(
            _segment(tag_id)), params=params)

    def search(self, **params):
        """Search tags (``GET api/v1/search``).

        This route searches **tags**, always; the response's ``entity`` is
        the string ``"tags"``. Image search is ``image_list``. There is no
        ``query``, ``entity`` or ``search`` parameter: they are ignored,
        and only ``q`` selects the query.

        Parameters:
            q (str): The search query. Not required by the server: empty
                (the default) lists all tags while the filters and sort
                still apply. At most 200 characters.
            type (int): Tag type filter: ``1`` Theme, ``2`` Source,
                ``3`` Artist, ``4`` Character.
            aliases (str): ``'hide'`` hides alias rows, ``'only'`` keeps
                only alias rows, ``'all'`` (default) keeps both.
            min_usage (int) / max_usage (int): Bounds on the effective
                usage count, at least 0; for an alias the canonical tag's
                count is used.
            added_from (str) / added_to (str): Tag creation date bounds as
                ``YYYY-MM-DD``.
            has_alias (str): ``'yes'`` or ``'no'`` -- whether an alias
                points at the tag.
            is_child (str): ``'yes'`` or ``'no'`` -- whether the tag has a
                parent.
            has_children (str): ``'yes'`` or ``'no'`` -- whether the tag is
                a parent itself.
            source_linked (str): ``'yes'`` or ``'no'`` -- for a character,
                whether it has a source link; for a source, whether it has a
                linked character. Requires ``type`` 2 or 4.
            limit (int): Maximum results, 1-100; default 20.
            offset (int): Results to skip, 0-500000; default 0.
            sort_by (str): ``usage_count``, ``title``, ``date_added``,
                ``tag_id`` or ``type``; omit for relevance ranking, which
                is the default.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"query", "entity", "hits", "total", "limit", "offset"}``.
        ``query`` echoes ``q`` (an empty string when it was omitted),
        ``entity`` is always ``"tags"``, and each hit carries the tag
        fields (tag_id, title, desc, type, date_added, usage_count,
        is_alias, alias_of, alias_of_name, alias_of_usage_count) plus
        ``matched_identity``.
        """
        return self.request("GET", "api/v1/search", params=params)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def user_list(self, **params):
        """List users (``GET api/v1/users``).

        Parameters:
            search (str): Partial, case-insensitive match on the username.
            page (int): Page number, from 1; default 1.
            per_page (int): Users per page, 1-100; default 20.
            sort_by (str): ``user_id`` (default), ``username``,
                ``date_joined``, ``last_login``, ``last_active``,
                ``image_posts``, ``posts`` or ``favorites``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "users"}``. Each user
        carries ``user_id``, ``username``, ``user_title``, ``avatar``,
        ``avatar_url``, ``groups``, ``admin``, ``active``, ``posts``,
        ``image_posts``, ``favorites``, ``date_joined``, ``last_login``,
        ``last_active``, ``location``, ``website``, ``interests``,
        ``gender`` and ``maximgperday``.
        """
        return self.request("GET", "api/v1/users", params=params)

    def user_show(self, user_id):
        """Get one user's profile (``GET api/v1/users/{user_id}``).

        Parameters:
            user_id (int): User ID (the uploader id found on images and
                comments), not a username.

        Returns one user object without an envelope: the same fields as a
        ``user_list`` entry. ``maximgperday`` is only filled for the user
        viewing their own profile or for a moderator holding
        ``USER_EDIT_PROFILE``; other viewers get null. An unknown id
        answers 404.
        """
        return self.request("GET",
                            "api/v1/users/{0}".format(_segment(user_id)))

    def user_images(self, user_id, **params):
        """Get the images uploaded by a user
        (``GET api/v1/users/{user_id}/images``).

        A convenience route for the common case; for further filtering use
        ``image_list(user_id=<id>, ...)``.

        Parameters:
            user_id (int): User ID.
            page (int): Page number, from 1; default 1.
            per_page (int): Images per page, 1-100; default 20.
            sort_by (str): ``image_id``, ``date_added``, ``last_post``,
                ``total_pixels``, ``bayesian_rating`` or ``favorites``.
                Default ``image_id``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "images", "comments"}``
        with the detailed image objects of ``image_list`` (embedded user and
        ``tags`` array included). ``comments`` is null here; this route
        takes no ``include_comments`` parameter.
        """
        return self.request("GET", "api/v1/users/{0}/images".format(
            _segment(user_id)), params=params)

    def user_favorites(self, user_id, **params):
        """Get the images favorited by a user
        (``GET api/v1/users/{user_id}/favorites``).

        Parameters:
            user_id (int): User ID.
            page (int): Page number, from 1; default 1.
            per_page (int): Images per page, 1-100; default 20.
            sort_by (str): ``image_id``, ``date_added``, ``last_post``,
                ``total_pixels``, ``bayesian_rating`` or ``favorites`` --
                the sort applies to the images, not to when they were
                favorited. Default ``image_id``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "images", "comments"}``
        with the detailed image objects of ``image_list``; ``comments`` is
        null. The deprecated ``/favorites/user/{user_id}`` route is not
        wrapped; this is the same read.
        """
        return self.request("GET", "api/v1/users/{0}/favorites".format(
            _segment(user_id)), params=params)

    def user_favorite_tags(self, user_id):
        """Get a user's public favorite tags
        (``GET api/v1/users/{user_id}/favorite-tags``).

        Parameters:
            user_id (int): User ID.

        Takes no query parameters. Returns ``{"characters", "sources",
        "artists"}``: characters are ``{"link_id", "position", "character",
        "source", "picture"}`` entries (``character``/``source`` are linked
        tags; ``picture`` is ``{"image_id", "thumbnail_url", "crop_x",
        "crop_y", "crop_w", "crop_h"}`` or null when the link has none or
        its image is no longer publicly visible), while sources and artists
        are ``{"position", "tag"}`` entries ordered by position.
        """
        return self.request("GET", "api/v1/users/{0}/favorite-tags".format(
            _segment(user_id)))

    def user_ratings(self, user_id, **params):
        """Get the images a user rated, with their scores
        (``GET api/v1/users/{user_id}/ratings``).

        Private: visible only to the user themselves and to moderators
        holding ``USER_EDIT_PROFILE``. An anonymous request is not part of
        the public surface. Moderators see every rated image regardless of
        status, deactivated ones included.

        Parameters:
            user_id (int): User ID of the rater.
            min_rating (int) / max_rating (int): Bounds, 1-10, on the score
                this user gave. Note that ``image_list(min_rating=...)``
                means the image's average instead.
            page (int): Page number, from 1; default 1.
            per_page (int): Images per page, 1-100; default 20.
            sort_by (str): ``image_id`` (default), ``rating`` or
                ``rated_at``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "images"}``. Each image
        carries the detailed image fields (embedded user, ``tags`` array,
        ``is_favorited``, ``user_rating`` and so on) plus ``subject_rating``
        (the score this user gave) and ``rated_at``.
        """
        return self.request("GET", "api/v1/users/{0}/ratings".format(
            _segment(user_id)), params=params)

    def user_history(self, user_id, **params):
        """Get the changes a user made
        (``GET api/v1/users/{user_id}/history``).

        Only publicly visible activity is included: tag metadata changes,
        tag adds/removes on images (upload-time adds included), and image
        status changes to REPOST, SPOILER or ACTIVE. Changes to hidden
        statuses (REVIEW, LOW_QUALITY, INAPPROPRIATE, OTHER) are dropped.

        Parameters:
            user_id (int): User ID.
            page (int): Page number, from 1; default 1.
            per_page (int): Entries per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "items"}``, most recent
        first. Each item's fields depend on its ``type``: ``'tag_metadata'``,
        ``'tag_usage'`` or ``'status_change'``. They are drawn from
        ``event_id``, ``created_at``, ``date``, ``image_id``, ``tag``,
        ``action``, ``old_status``/``new_status``/``new_status_label``, the
        metadata old/new pairs (``action_type``, ``old_title``/``new_title``,
        ``old_type``/``new_type``, ``old_desc``/``new_desc``), ``alias_tag``,
        ``parent_tag``, ``source_tag``, ``character_tag``, ``link_url`` and
        ``old_archive_url``/``new_archive_url``.
        """
        return self.request("GET", "api/v1/users/{0}/history".format(
            _segment(user_id)), params=params)

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def comment_list(self, **params):
        """Search and list comments (``GET api/v1/comments``).

        Parameters:
            image_id (int): Only comments on this image.
            image_ids (str): Comma-separated image IDs to fetch several
                images' comments at once, e.g. ``'123,456,789'``.
            user_id (int): Only comments written by this user.
            search_text (str): Text searched inside the comment.
                ``all_words`` semantics: every term must appear as a
                case-insensitive substring, ``"quoted phrase"`` keeps word
                order and ``-term`` excludes. A blank value filters nothing.
            search_mode (str): ``'all_words'`` (default), ``'like'`` (the
                whole string as one substring, ``%``/``_`` literal), or
                ``'natural'``/``'boolean'``, which behave as ``all_words``.
            date_from (str) / date_to (str): Comment date bounds as
                ``YYYY-MM-DD``.
            page (int): Page number, from 1; default 1.
            per_page (int): Comments per page, 1-100; default 20.
            sort_by (str): ``date`` (default), ``post_id`` or
                ``update_count``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "comments"}``. Each comment
        carries ``post_id``, ``image_id``, ``user_id``, ``user`` (a user
        summary), ``post_text`` (Markdown), ``post_text_html`` (rendered
        HTML), ``parent_comment_id``, ``deleted``, ``date``,
        ``update_count``, ``last_updated`` and ``last_updated_user_id``.
        """
        return self.request("GET", "api/v1/comments", params=params)

    def comment_show(self, comment_id):
        """Get one comment (``GET api/v1/comments/{comment_id}``).

        Parameters:
            comment_id (int): Comment number, the ``post_id`` seen in a
                comment list.

        Returns one comment object without an envelope: post_id, image_id,
        user_id, user, post_text, post_text_html, parent_comment_id,
        deleted, date, update_count, last_updated and
        last_updated_user_id. An unknown id answers 404.
        """
        return self.request("GET",
                            "api/v1/comments/{0}".format(_segment(comment_id)))

    def comment_image(self, image_id, **params):
        """Get the comments on one image
        (``GET api/v1/comments/image/{image_id}``).

        The same read as ``comment_list(image_id=<id>)``, as a convenience
        for image detail pages.

        Parameters:
            image_id (int): Image number.
            page (int): Page number, from 1; default 1.
            per_page (int): Comments per page, 1-100; default 20.
            sort_by (str): ``date`` (default), ``post_id`` or
                ``update_count``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "comments"}`` with the
        comment objects described in ``comment_list``.
        """
        return self.request("GET", "api/v1/comments/image/{0}".format(
            _segment(image_id)), params=params)

    def comment_user(self, user_id, **params):
        """Get the comments written by one user
        (``GET api/v1/comments/user/{user_id}``).

        The same read as ``comment_list(user_id=<id>)``, as a convenience
        for user profile pages.

        Parameters:
            user_id (int): User ID.
            page (int): Page number, from 1; default 1.
            per_page (int): Comments per page, 1-100; default 20.
            sort_by (str): ``date`` (default), ``post_id`` or
                ``update_count``.
            sort_order (str): ``ASC`` or ``DESC``; default ``DESC``.

        Returns ``{"total", "page", "per_page", "comments"}`` with the
        comment objects described in ``comment_list``.
        """
        return self.request("GET", "api/v1/comments/user/{0}".format(
            _segment(user_id)), params=params)

    def comment_stats(self):
        """Get overall comment statistics
        (``GET api/v1/comments/stats/summary``).

        Returns ``{"total_comments", "total_images_with_comments",
        "average_comments_per_image"}``; the average is taken across the
        images that have at least one comment.
        """
        return self.request("GET", "api/v1/comments/stats/summary")

    # ------------------------------------------------------------------
    # Site
    # ------------------------------------------------------------------

    def news_list(self, **params):
        """List news items (``GET api/v1/news``).

        Parameters:
            page (int): Page number, from 1; default 1.
            per_page (int): Items per page, 1-100; default 20.

        Returns ``{"total", "page", "per_page", "news"}``, newest first.
        Each item carries ``news_id``, ``title``, ``news_text``, ``date``,
        ``edited``, ``user_id`` and ``username``.
        """
        return self.request("GET", "api/v1/news", params=params)

    def news_show(self, news_id):
        """Get one news item (``GET api/v1/news/{news_id}``).

        Parameters:
            news_id (int): News number.

        Returns one news object without an envelope: news_id, title,
        news_text, date, edited, user_id and username. An unknown id
        answers 404.
        """
        return self.request("GET",
                            "api/v1/news/{0}".format(_segment(news_id)))

    def meta_config(self):
        """Get the site's public configuration (``GET api/v1/meta/config``).

        The one route that exposes both the site limits and the tag type
        mapping, so a client reads it first. Returns
        ``{"max_search_tags", "max_search_users", "max_image_size",
        "max_avatar_size", "upload_delay_seconds", "search_delay_seconds",
        "tag_types", "ml_tag_suggestions_enabled",
        "ml_character_suggestions_enabled"}``. ``max_image_size`` and
        ``max_avatar_size`` are byte counts; ``tag_types`` maps the type id
        as a string to its name (``{"0": "All", "1": "Theme", "2":
        "Source", "3": "Artist", "4": "Character"}``).
        """
        return self.request("GET", "api/v1/meta/config")

    def permission_list(self):
        """List every permission name (``GET api/v1/permissions``).

        Returns a flat object mapping each permission's enum name to the
        value stored in the database, for example ``{"IMAGE_TAG_ADD":
        "image_tag_add", "TAG_CREATE": "tag_create"}``. Public information
        the frontend uses for permission checks; not paginated.
        """
        return self.request("GET", "api/v1/permissions")
