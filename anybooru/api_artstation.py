"""Native methods for ArtStation (www.artstation.com).

ArtStation is a portfolio and community site rather than one of the booru
engines this package ships for: its public surface is the site's own root
JSON routes, the ``/api/v2`` community and search routes and one RSS feed,
so nothing here reuses a booru parameter name or field list. Seventeen
methods cover fifteen GET reads, explicit CSRF preparation and form POST
search. Response fields describe the anonymous samples recorded in
``docs/verification.md``, not a schema.

Shared observed facts:
    * Base URL: ``https://www.artstation.com``; ``ArtStation.request``
      resolves every path under it with a leading slash stripped.
    * Listing envelopes differ and are never unwrapped: ``{"data": [...],
      "total_count": N}`` on the root ``projects.json`` routes,
      ``{"total_count": N, "data": [...]}`` on the ``/api/v2/community`` and
      search routes, ``{"data": [...]}`` with no count on the explore route,
      and no envelope at all on ``random_project.json`` (a bare project
      object) and ``filter_fields.json`` (a bare array). Which of the two
      keys comes first in the body is a sample detail, not something a caller
      can rely on.
    * ``total_count`` is the site's own figure, not a page length and not a
      stable number: the samples returned 14522955 for the global list, 40
      for one user's portfolio, 64 for the channel list and 10000 for one
      channel. No client-side paging is derived from it.
    * Item shapes belong to one route and are not interchangeable: the global
      list entries carried 21 fields including ``views_count`` and ``user``,
      the user portfolio entries 19 without those two, search entries 9,
      channel and explore entries 10, album entries 13 with ``assets``. A
      field missing from one route's entry is never filled in from another.
    * Errors are kept as they arrive and are not retried or rewritten. An
      out-of-range parameter answered 400: the root list with an empty
      ``text/plain`` body, the search, album and explore routes with a JSON
      object (``{"message", "code"}``, or a bare string under ``data`` for
      the search route's missing ``page``). An unknown user answered 404 with
      an empty ``text/plain`` body. A non-JSON error body has no decoded
      object and reaches the caller as the shared HTTP error instead.
    * A 200 is not proof that a route exists: an unknown root path is
      answered by the site's Explore HTML page with status 200.
    * Media is never fetched here: cover and asset addresses are returned as
      the received strings, cache-query suffix included, and no address is
      built, resized or rewritten.
    * Out of scope, and reachable only through ``ArtStation.request``: the
      fixed project page ``/projects/{hash}.json`` (403, a Cloudflare
      challenge in the samples), the v2 detail ``/api/v2/community/projects/
      {id}.json`` (401 ``{"data": null}``), and content-writing or account
      operations. CSRF preparation and POST search are explicit methods.

Which calls have actually been made against the live site is recorded in
``docs/verification.md``; the full per-method parameter and field reference
is ``docs/artstation-api.md``.

Classes:
    ArtStationApi_Mixin -- ArtStation project, user, search, album, channel,
        comment, explore and feed reads.
"""

# Standard library imports
from urllib.parse import quote


class ArtStationApi_Mixin:
    """ArtStation reads, each a thin ``ArtStation.request()`` call.

    Methods never fill query values, clamp, retry or automatically obtain a
    token. The per-method parameter and field reference is
    ``docs/artstation-api.md``.
    """

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def project_list(self, **params):
        """List the newest projects (``GET projects.json``).

        ``params`` is forwarded unchanged for ``page`` (1-based) and
        ``per_page``; neither is filled in here. Observed envelope
        ``{"data": [...], "total_count": N}``: ``per_page=1`` answered one
        entry and ``per_page=50`` fifty, while ``per_page=51`` and
        ``page=999999`` answered 400 with an empty ``text/plain`` body, so no
        bound is applied or known locally. A sample entry carried ``id``,
        ``slug``, ``title``, ``hash_id``, ``permalink``, ``cover_asset_id``,
        ``assets_count``, ``views_count``, ``tag_list`` (null in the sample),
        ``user``, ``cover`` and ``icons``. The route is the whole site's
        newest work, so neither its order nor its entries are stable between
        calls.
        """
        return self.request("GET", "projects.json", params=params)

    def project_random(self):
        """Read one random project (``GET random_project.json``).

        Takes no arguments: no parameter was observed on this route and none
        is sent. The body is a bare project object rather than a listing
        envelope, 30 fields in the sample, adding ``assets``, ``tags``,
        ``categories``, ``mediums``, ``software_items``, ``shortlink``,
        ``visibilities``, ``is_promotional`` and the ``views_count``,
        ``likes_count`` and ``comments_count`` counters to the list entry.
        The sampled ``tags`` was ``[]``, which establishes the array but not
        its element type; each asset carried ``original_url`` (null in the
        sample), ``image_url``, ``small_image_url``, ``width``, ``height``
        and ``asset_type``. One call was observed, so nothing is promised
        about a repeat call's identity or uniqueness.
        """
        return self.request("GET", "random_project.json")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def user_show(self, username):
        """Read one portfolio profile (``GET users/{username}.json``).

        ``username`` is the site's handle (``timwarnock``), percent-encoded as
        a single path segment with no safe characters and not validated here:
        an unknown handle reached the site and answered 404 with an empty
        ``text/plain`` body. The body is a bare user object, 70 fields in the
        sample: ``id``, ``username``, ``full_name``, ``headline``,
        ``followers_count``, ``projects_count``, ``social_profiles``,
        ``skills``, ``software_items`` and ``albums_with_community_projects``
        -- the last holding one entry in the sample, ``id`` 95733 with
        ``title`` ``'All'`` and ``album_type`` ``'all_projects'``.
        """
        return self.request("GET", "users/{}.json".format(
            quote(str(username), safe="")))

    def user_quick(self, username):
        """Read the compact profile card (``GET users/{username}/quick.json``).

        Same handle and encoding as ``user_show``. A bare user object again,
        but a different one: 59 fields in the sample, which keeps
        ``albums_with_community_projects`` and adds ``is_artist``,
        ``is_beta`` and ``has_recruiter_badge`` while dropping
        ``projects_count``, ``social_profiles``, ``skills``,
        ``software_items``, ``badges`` and the ``first_name``/``last_name``
        pair, so it is neither a subset nor a shorthand for ``user_show``.
        """
        return self.request("GET", "users/{}/quick.json".format(
            quote(str(username), safe="")))

    def user_profile(self, username):
        """Read a profile header (``GET api/v2/user_profiles/{username}.json``).

        Same handle and encoding as ``user_show``. A third bare user object,
        63 fields in the sample: it keeps ``projects_count`` and
        ``community_projects_count`` (both 40 for the sample user) and adds
        ``is_artist``, ``is_beta``, ``subdomain``, ``freelance_profiles`` and
        ``website_default_album``, while it has none of the per-network
        ``twitter_url``-style links ``user_show`` carries. Which of the three
        user routes a page reads is the site's choice; the three shapes are
        not merged here.
        """
        return self.request("GET", "api/v2/user_profiles/{}.json".format(
            quote(str(username), safe="")))

    def user_projects(self, username, **params):
        """List a user's projects (``GET users/{username}/projects.json``).

        ``username`` is the handle and ``params`` is forwarded unchanged for
        ``page``, ``per_page`` and ``album_id``. Envelope ``{"data": [...],
        "total_count": N}`` (40 for the sample user), but the entries differ
        from ``project_list``: ``per_page=2`` answered two entries of 19
        fields with no ``user`` and no ``views_count``, so a caller cannot
        read those two keys from this route even though the global list
        carries them. ``page=9999`` came back 200 with an empty ``data`` and
        the unchanged ``total_count``, which is how a page past the end ends
        here rather than an error.
        """
        return self.request("GET", "users/{}/projects.json".format(
            quote(str(username), safe="")), params=params)

    def user_following(self, username, **params):
        """List followed users (``GET users/{username}/following.json``).

        ``params`` is forwarded unchanged for ``page`` and ``per_page``;
        neither is filled in here. Envelope ``{"data": [...], "total_count":
        N}`` (409 in the sample) whose entries are user cards rather than
        projects: 30 fields including ``username``, ``headline``,
        ``followers_count``, ``sample_projects``, ``skills``,
        ``software_items`` and ``following_back``.
        """
        return self.request("GET", "users/{}/following.json".format(
            quote(str(username), safe="")), params=params)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def project_search(self, **params):
        """Search projects (``GET api/v2/search/projects.json``).

        ``params`` is forwarded unchanged: ``query``, ``page`` (1-based),
        ``per_page``, ``sorting``, ``pro_first``, ``filters`` and
        ``additional_fields``. Only ``sorting=relevance`` was executed.
        Observed envelope ``{"total_count": N, "data": [...]}`` whose entries
        are not the list entries: nine fields, ``id``, ``hash_id``, ``url``,
        ``smaller_square_cover_url``, ``hide_as_adult``, ``is_adult_content``,
        ``title``, ``icons`` and ``user``.

        The site's own bounds are strict and are not enforced locally:
        ``per_page=3`` and ``per_page=75`` answered 3 and 75 entries while
        ``per_page=2`` and ``per_page=76`` answered 400
        ``{"message": "per_page should be >= 3", "code": "per_page"}`` and
        ``{"message": "per_page should be <= 75", "code": "per_page"}``; a
        missing ``page`` answered 400 ``{"data": "page should be given"}``
        and ``page=0`` answered 400 with a string under ``data``.
        ``filters`` must be one JSON **string** -- ``'[{"field": "title",
        "method": "contain", "value": "dragon"}]'``, which answered 200 with
        matching titles -- while the Rails form the shared encoder builds
        from a list (``filters[][field]=title``) answered 400.
        ``additional_fields`` is the opposite and was sent as a Rails array
        (``additional_fields[]=assets``), which answered 200 with the sample's
        first entry carrying the same nine fields.
        """
        return self.request("GET", "api/v2/search/projects.json",
                            params=params)

    def csrf_token(self, **attributes):
        """Request an anonymous CSRF token with an explicit JSON body.

        POST ``api/v2/csrf_protection/token.json`` returns the complete JSON
        object containing ``public_csrf_token``. The existing session keeps
        the server's paired Cookie. Pass the returned token explicitly to
        ``project_search_post`` on this same client; no token property,
        login, automatic refresh or search request is created here.
        """
        return self.request("POST", "api/v2/csrf_protection/token.json",
                            data=attributes)

    def project_search_post(self, public_csrf_token, **params):
        """Search with a form body, including explicit additional_fields.

        POST ``api/v2/search/projects.json`` sends ``params`` through the
        shared Rails form encoder. ``additional_fields=['assets',
        'description']`` becomes repeated ``additional_fields[]`` keys.
        The caller supplies PUBLIC-CSRF-TOKEN and uses the same client that
        obtained its paired Cookie. No token fetch, retry, refresh, response
        unwrapping or media download is performed.
        """
        return self.request("POST", "api/v2/search/projects.json", form=params,
                            headers={"PUBLIC-CSRF-TOKEN": public_csrf_token})

    def search_filter_fields(self):
        """List the searchable filter fields (``GET .../filter_fields.json``).

        The full route is ``api/v2/search/projects/filter_fields.json`` and
        it takes no parameters. The body is a bare array -- no envelope and
        no count -- of 12 ``{"name", "type"}`` objects in the sample:
        ``title`` and ``artist_name`` are ``text``, ``comments_count`` and
        ``artist_followers_count`` ``number``, ``following`` and
        ``editor_pick`` ``boolean``, ``tags`` type ``tags``, and
        ``category_ids``, ``asset_types``, ``medium_ids``, ``software_ids``
        and ``medium_id`` are ``select_multiple`` carrying a
        ``select_options`` array of ``{"id", "name"}`` (59, 6, 11, 410 and 11
        options), while the other seven items carry only ``name`` and
        ``type``. The list is returned as received; it is not turned into a
        ``filters`` value here.
        """
        return self.request("GET", "api/v2/search/projects/filter_fields.json")

    # ------------------------------------------------------------------
    # Community
    # ------------------------------------------------------------------

    def album_projects(self, album_id, **params):
        """List the projects in one album (``GET .../by_album.json``).

        The full route is ``api/v2/community/projects/by_album.json``.
        ``album_id`` is required and is added to ``params`` as ``album_id``,
        which is otherwise forwarded unchanged for ``page`` and ``per_page``.
        Envelope ``{"total_count": N, "data": [...]}`` (49 for the sample
        album) with 13-field entries: ``id``, ``slug``, ``hash_id``,
        ``title``, ``description``, ``album_id``, ``album_title``,
        ``position``, ``permalink``, ``cover``, ``assets``, ``created_at``
        and ``updated_at``. ``per_page=4`` answered four entries while
        ``per_page=3`` answered 400 ``{"message", "code"}``.
        """
        return self.request("GET", "api/v2/community/projects/by_album.json",
                            params=dict(params, album_id=album_id))

    def channel_list(self):
        """List the community channels (``GET .../channels/channels.json``).

        The full route is ``api/v2/community/channels/channels.json`` and it
        takes no parameters. Envelope ``{"total_count": N, "data": [...]}``;
        the sample answered all 64 channels at once with ``total_count`` 64.
        An entry has 24 fields: ``id``, ``name``, ``uri``, ``type``,
        ``featured``, ``state``, ``image_url``, ``icon_image_url``,
        ``artworks_only`` and a promo/intro block (``promo_text``,
        ``promo_link``, ``intro_title``, ``bg_image_url``,
        ``learning_sources``) that was mostly null for the sampled channel 70
        ``'Abstract'``. The observed ``channel_projects`` call used that same
        ``channel_id=70``.
        """
        return self.request("GET",
                            "api/v2/community/channels/channels.json")

    def channel_projects(self, channel_id, **params):
        """List one channel's projects (``GET .../channels/projects.json``).

        The full route is ``api/v2/community/channels/projects.json``.
        ``channel_id`` is required and is added to ``params`` as
        ``channel_id``, which is otherwise forwarded unchanged for ``page``,
        ``per_page``, ``sorting`` and ``dimension``. Envelope
        ``{"total_count": N, "data": [...]}`` whose entries have ten fields:
        the search entry's shape without ``is_adult_content`` and with
        ``is_highlighted`` and ``small_square_cover_url`` added.
        ``channel_id=70`` with ``per_page=5`` answered five entries and
        ``total_count`` 10000; this route's bounds were not measured.
        """
        return self.request("GET", "api/v2/community/channels/projects.json",
                            params=dict(params, channel_id=channel_id))

    def project_comments(self, project_id, **params):
        """List one project's comments (``GET .../projects/{id}/comments.json``).

        The full route is
        ``api/v2/community/projects/{project_id}/comments.json``.
        ``project_id`` is the numeric project id (``22897630``), percent-
        encoded as a single path segment; ``params`` is forwarded unchanged,
        and ``page`` and ``per_page`` are candidates only -- the route was
        called without them and its bounds were not measured. Envelope
        ``{"total_count": N, "data": [...]}``; the sample project answered
        ``{"total_count": 0, "data": []}``, so an empty array is a normal
        answer and the non-empty entry shape is untested.
        """
        return self.request("GET",
                            "api/v2/community/projects/{}/comments.json".format(
                                quote(str(project_id), safe="")),
                            params=params)

    def explore_latest(self, **params):
        """List the latest explore projects (``GET .../projects/latest.json``).

        The full route is
        ``api/v2/community/explore/projects/latest.json``. ``params`` is
        forwarded unchanged for ``page`` and ``per_page``. Envelope
        ``{"data": [...]}`` with no ``total_count``, whose entries have the
        channel entry's ten fields. ``per_page=10`` answered ten entries while
        ``per_page=9`` answered 400 ``{"message", "code"}``, so ten is the
        smallest value observed to be accepted; ``page`` was sent as 1 in
        every observed call.
        """
        return self.request("GET",
                            "api/v2/community/explore/projects/latest.json",
                            params=params)

    # ------------------------------------------------------------------
    # Feed
    # ------------------------------------------------------------------

    def feed(self, **params):
        """Read the artwork feed (``GET artwork.rss``) as unchanged XML text.

        The one method of this family that does not answer JSON: it asks
        ``ArtStation.request`` for ``response_format='xml'``, so the whole
        response text -- declaration, root element, whitespace and all -- is
        returned and never parsed, validated or converted. ``params`` is
        forwarded unchanged; ``sorting`` is the observed name, and
        ``sorting=latest`` answered RSS 2.0 as ``application/rss+xml;
        charset=utf-8`` with 50 ``<item>`` elements. The feed is not a page of
        any JSON route, so this client builds no item count from it and reads
        no link inside it.
        """
        return self.request("GET", "artwork.rss", params=params,
                            response_format="xml")
