# -*- coding: utf-8 -*-

"""pybooru.api_moebooru

This module contains all API calls of Moebooru.

Every method is one thin call to ``Moebooru.request()`` against a route from
``moebooru/config/routes.rb``; the client appends ``.json`` (and, on the
configured 1.13.0 / +update.1 / +update.2 sites, the legacy ``/index`` segment
for bare collection paths).

Conventions:
    * Read methods take ``**params`` - top-level query fields such as ``tags``,
      ``limit`` and ``page`` - plus the identifiers the route needs. Nothing is
      filtered, clamped or defaulted here; the server validates.
    * Write methods take the arguments the controller reads outside its model
      namespace (``id``, ``pool_id``, ``post_id``, ``commit``, ``title``) plus
      ``**attributes``, which become the model's nested Rails form key
      (``post[tags]``, ``wiki_page[body]``, ...). Bodies are form encoded: list
      values become repeated ``key[]`` fields and ``None`` values disappear.
    * Protocol selectors are the literal values the engine compares
      (``commit='Yes'``, ``unflag='1'``, ``redo='1'``, ``filter='1'``,
      ``api_version='2'``) and are passed as caller-supplied strings, never
      converted from booleans.
    * Authentication, permissions and validation stay server-side. The
      transport raises :class:`~pybooru.exceptions.PybooruHTTPError` for non-2xx
      answers: 403 access denied, 420 validation, 421 daily or hourly limits,
      423 already exists, 424 invalid value, 406 HTML-only format.
    * Raw JSON comes back unchanged: list actions return a top-level array (or
      the version-2 envelope), writes return ``{success: true, ...}`` and empty
      successes return ``None``.
    * Redirect-only actions whose target has a JSON page are exposed as well
      (``pool_import``, ``pool_order`` and the alias,
      implication and forum writes). The client follows the redirect, so the
      final GET does not confirm the write: a flash-only validation failure
      redirects to the same page.
    * HTML, JS, feed and ZIP surfaces are deliberately absent. ``post/show`` is
      ``format: false`` and HTML only - its ``.json`` form has no route - so a
      single post is read with ``post_list(tags='id:<id>')``. ``wiki/show``,
      ``tag/cloud``, ``tag/popular_*``, ``history``, ``pool/select``,
      ``post/browse``, ``post/atom`` and ``pool/zip`` are browser or feed
      routes, not JSON endpoints.
    * Write endpoints follow the current source but were not exercised against
      a live site.

Classes:
    MoebooruApi_Mixin -- Contains all Moebooru API calls.
"""

# __future__ imports
from __future__ import absolute_import


def _model(model, attributes):
    """Nest attribute values under their model's Rails form key."""
    return {model: attributes}


class MoebooruApi_Mixin(object):
    """Contains all Moebooru API calls.

    * Source: https://github.com/moebooru/moebooru (config/routes.rb)
    * Doc: https://yande.re/help/api (stale in places; controllers prevail)
    * API versions: 1.13.0+update.3 and 1.13.0
    """

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def post_list(self, **params):
        """Get a list of posts (the JSON post index).

        Parameters:
            tags (str): Tag query in the site's tag language; the meta tags of
                the web search work here (``id:123``, ``md5:<hash>``,
                ``rating:s``, ``score:>10``, ``order:score``).
            limit (int): Posts per page; the server defaults to 40 and caps the
                value at 1000.
            page (int): Page number.
            filter (str): ``'1'`` applies the caller's tag filter.
            api_version (str): ``'2'`` switches the reply from a bare array to
                ``{posts, pool_posts, pools, tags, votes}``; the server answers
                424 for a version-2 XML request.
            include_tags, include_votes, include_pools (str): ``'1'`` adds the
                matching dictionary to the version-2 envelope.

        There is no JSON post-show route: a single post is read with
        ``post_list(tags='id:<id>')`` (an empty list means "not found"), since
        ``post/show`` is HTML only and ``format: false``.
        """
        return self.request("GET", "post", params=params)

    def post_create(self, tags, *, file=None, source=None, md5=None,
                    anonymous=None, **attributes):
        """Create a post (requires login; multipart form).

        Parameters:
            tags (str): Space-delimited tag string.
            file: An open file object or a requests file tuple, sent as the
                multipart ``post[file]`` part; the caller owns the handle.
            source (str): Post source. With an ``http(s)`` URL and no file the
                server downloads the image itself, so a source-only upload is
                valid.
            md5 (str): Top-level checksum of the uploaded file; a mismatch
                destroys the post and answers 420.
            anonymous (str): ``'1'`` hides the uploader (contributor level).

        Attributes:
            rating (str): ``safe``, ``questionable`` or ``explicit``.
            parent_id (int): Parent post id.
            is_held (str): ``'1'`` holds the post for moderation.
            Further ``post[...]`` fields. ``is_rating_locked`` and
            ``is_note_locked`` are not permitted on creation and are dropped
            silently.

        A duplicate md5 answers 423; the member upload limit answers 421.
        """
        data = dict(_model("post", dict(attributes, tags=tags, source=source)),
                    md5=md5, anonymous=anonymous)
        files = {"post[file]": file} if file is not None else None
        return self.request("POST", "post/create", data=data, files=files)

    def post_update(self, post_id, **attributes):
        """Update one post (requires login; uploader or moderator).

        There is no file replacement path: ``post[file]`` is not a permitted
        key and would be dropped, so this method has no file argument.

        Parameters:
            post_id (int): The post id.

        Attributes:
            tags (str): Replacement tag string.
            old_tags (str): Tag string used for historical diffing.
            source (str), rating (str), parent_id (int),
            is_held, is_shown_in_index, is_note_locked, is_rating_locked (str),
            frames_pending_string (str).

        Returns ``{success: true, post: {...}, tags: {...}}``; validation
        answers 420 and a locked (deleted) post 422.
        """
        return self.request("POST", "post/update",
                            data=dict(_model("post", attributes), id=post_id))

    def post_destroy(self, post_id, reason=None, *, destroy=None):
        """Delete a post (requires login; uploader or moderator).

        Parameters:
            post_id (int): The post id.
            reason (str): Deletion reason.
            destroy (str): ``'1'`` removes the row from the database instead of
                marking it deleted (moderator only, otherwise 403).

        Users can delete their own uploads only while the post is active and
        younger than one day; the server answers 403 otherwise.
        """
        return self.request("POST", "post/destroy",
                            data={"id": post_id, "reason": reason,
                                  "destroy": destroy})

    def post_revert_tags(self, post_id, history_id):
        """Revert a post's tags to a tag history entry (requires login).

        Parameters:
            post_id (int): The post id.
            history_id (int): ``PostTagHistory`` id; an unknown id answers 404.
        """
        return self.request("POST", "post/revert_tags",
                            data={"id": post_id, "history_id": history_id})

    def post_vote(self, post_id, score=None):
        """Read or write the caller's vote on a post (requires login).

        Parameters:
            post_id (int): The post id.
            score (int): ``1`` (good), ``2`` (great) or ``3`` (favorite); ``0``
                clears the vote. Omitted, the call only reads the current vote.
                The server rejects values above 3 with 424 and negative values
                for non-moderators, and answers 423 when the vote exists.

        Returns ``{success: true, vote: <int>}``, plus the batch payload when a
        vote was written.
        """
        return self.request("POST", "post/vote",
                            data={"id": post_id, "score": score})

    def post_activate(self, post_ids):
        """Release held posts (member level; moderators may release others' posts).

        Parameters:
            post_ids (list): Post ids, sent as repeated ``post_ids[]`` fields.
                The server expects an array and answers an empty 204 for any
                other value.
        """
        return self.request("POST", "post/activate",
                            data={"post_ids": post_ids})

    def post_acknowledge_new_deleted_posts(self):
        """Mark the deletion notice as seen; anonymous calls do not update a user."""
        return self.request("POST", "post/acknowledge_new_deleted_posts")

    def post_update_batch(self, post):
        """Update several posts in one request (requires login).

        Parameters:
            post (dict): Post id -> attribute mapping, sent as
                ``post[<post_id>][attr]``. Permitted attributes are ``source``,
                ``parent_id``, ``rating``, ``tags``, ``old_tags``, ``is_held``,
                ``is_shown_in_index``, ``is_note_locked``, ``is_rating_locked``
                and ``frames_pending_string``. An entry with only an id asks
                for that post's current payload.

        Returns the batch payload ``{success: true, posts, pool_posts, pools,
        tags, votes}`` for every touched post and its neighbours.
        """
        return self.request("POST", "post/update_batch", data={"post": post})

    def post_moderate(self, ids, commit, reason=None, reason2=None):
        """Approve or delete several posts (janitor level; POST only).

        Parameters:
            ids (dict): Post id -> any value mapping, sent as
                ``ids[<post_id>]``; only the keys are read.
            commit (str): ``'Approve'`` or ``'Delete'``.
            reason (str): Reason stored with a deletion.
            reason2 (str): Alternative reason line, used when ``reason`` is
                blank.

        Returns the batch payload for the touched posts; the GET form of the
        route is the HTML moderation queue and is not wrapped here.
        """
        return self.request("POST", "post/moderate",
                            data={"ids": ids, "commit": commit,
                                  "reason": reason, "reason2": reason2})

    def post_flag(self, post_id, reason=None, *, unflag=None):
        """Flag or unflag a post (requires login; flagger or moderator).

        Parameters:
            post_id (int): The post id.
            reason (str): Public flag reason.
            unflag (str): Exact server flag ``'1'``, which removes an existing
                flag instead of adding one.

        Only active posts can be flagged and only flagged posts unflagged; the
        server answers 500 for the other states.
        """
        return self.request("POST", "post/flag",
                            data={"id": post_id, "reason": reason,
                                  "unflag": unflag})

    def post_undelete(self, post_id):
        """Restore a deleted post (janitor level).

        Parameters:
            post_id (int): The post id.

        Returns the batch payload of the post and its parent.
        """
        return self.request("POST", "post/undelete", data={"id": post_id})

    def post_similar(self, *, file=None, **params):
        """Search for visually similar posts (anonymous).

        Parameters:
            file: Open file object or requests file tuple; when supplied the
                request becomes a multipart POST with the ``file`` part (a
                value that is not an upload is discarded by the server).
            params: ``id`` (post to compare, 404 when unknown), ``url``
                (``http(s)`` or ``data:`` URL), ``search_id``, ``services``
                (``'local'``, ``'all'`` or comma-separated service names),
                ``threshold``, ``forcegray``, ``width``, ``height`` and
                ``initial``.

        Returns ``{success: true, posts, source, search_id, error}``. Without
        an id, url, file or valid search_id the server answers 503.
        """
        if file is None:
            return self.request("GET", "post/similar", params=params)
        return self.request("POST", "post/similar", data=params,
                            files={"file": file})

    def post_popular_recent(self, **params):
        """Get the highest scoring recent posts (anonymous).

        Parameters:
            period (str): ``'1w'``, ``'1m'`` or ``'1y'``; any other value is
                replaced by ``'1d'`` server-side.

        Returns at most 40 posts.
        """
        return self.request("GET", "post/popular_recent", params=params)

    def post_popular_by_day(self, **params):
        """Get the most popular posts of a day (anonymous).

        Parameters:
            year, month, day (int): Date to inspect; missing parts use the
                current date, invalid ones answer an empty 400.
        """
        return self.request("GET", "post/popular_by_day", params=params)

    def post_popular_by_week(self, **params):
        """Get the most popular posts of a week (anonymous).

        Parameters:
            year, month, day (int): Any day inside the week to inspect.
        """
        return self.request("GET", "post/popular_by_week", params=params)

    def post_popular_by_month(self, **params):
        """Get the most popular posts of a month (anonymous).

        Parameters:
            year, month, day (int): Any day inside the month to inspect.
        """
        return self.request("GET", "post/popular_by_month", params=params)

    # ------------------------------------------------------------------
    # Pools
    # ------------------------------------------------------------------

    def pool_list(self, **params):
        """Get a list of pools (anonymous).

        Parameters:
            query (str): Space-separated tokens such as ``order:name``,
                ``limit:50`` (capped at 100) and ``posts:1-10``.
            order (str): ``name``, ``date``, ``updated`` or ``id``.
            page (int): Page number (20 pools per page).
        """
        return self.request("GET", "pool", params=params)

    def pool_show(self, pool_id, **params):
        """Get one pool with its posts (anonymous).

        Parameters:
            pool_id (int): The pool id.
            params: ``page`` selects a window of 24 posts (1000 when the caller
                enabled the pool browse mode).

        Returns one pool object with a ``posts`` array; an unknown id redirects
        to the pool index even for JSON.
        """
        return self.request("GET", "pool/show",
                            params=dict(params, id=pool_id))

    def pool_create(self, name, **attributes):
        """Create a pool (requires login; POST only).

        Parameters:
            name (str): The pool name.

        Attributes:
            description (str), is_public, is_active (str).

        The reply is only ``{success: true}``: the new pool id is not returned,
        so read it back with :meth:`pool_list` when needed. Validation answers
        420.
        """
        return self.request("POST", "pool/create",
                            data=_model("pool", dict(attributes, name=name)))

    def pool_update(self, pool_id, **attributes):
        """Update a pool (requires login; public pool or owner/moderator).

        POST only - ``PUT /pool/update`` is not routed. Attributes are
        ``name``, ``description``, ``is_public`` and ``is_active``; the reply is
        ``{success: true}``.
        """
        return self.request("POST", "pool/update",
                            data=dict(_model("pool", attributes), id=pool_id))

    def pool_destroy(self, pool_id):
        """Delete a pool (requires login; POST only).

        ``DELETE /pool/destroy`` is not routed. The server answers 403 unless
        the pool is public or the caller may update it.
        """
        return self.request("POST", "pool/destroy", data={"id": pool_id})

    def pool_add_post(self, pool_id, post_id, sequence=None):
        """Add a post to a pool (requires login; POST only).

        Parameters:
            pool_id (int): The pool id.
            post_id (int): The post id.
            sequence (int): Position inside the pool; blank appends at the end.

        The reply is ``{success: true}`` without a pool payload; adding a post
        twice answers 423.
        """
        return self.request("POST", "pool/add_post",
                            data={"pool_id": pool_id, "post_id": post_id,
                                  "pool": {"sequence": sequence}})

    def pool_remove_post(self, pool_id, post_id):
        """Remove a post from a pool (requires login; POST only).

        Returns the removed post's batch payload; the server also sets an
        ``X-Post-Id`` header.
        """
        return self.request("POST", "pool/remove_post",
                            data={"pool_id": pool_id, "post_id": post_id})

    def pool_copy(self, pool_id, name=None):
        """Copy a pool including all of its posts (contributor level; POST).

        Parameters:
            pool_id (int): The pool to copy.
            name (str): Name of the copy; the server appends `` (copy)`` to the
                original name when blank.

        The JSON reply is ``{success: true}``; only the HTML redirect carries
        the new pool id, so JSON callers must query the pool list to find it.
        """
        return self.request("POST", "pool/copy",
                            data={"id": pool_id, "name": name})

    def pool_import(self, pool_id, posts):
        """Add posts to a pool in sequence order (requires login; POST).

        Parameters:
            pool_id (int): The pool id.
            posts (dict): Post id -> sequence mapping, sent as
                ``posts[<post_id>]`` and applied in ascending sequence order.

        The action always redirects to the pool page: following it lands on the
        pool JSON, which is not proof that the import was applied, because a
        validation failure redirects to the same page.
        """
        return self.request("POST", "pool/import",
                            data={"id": pool_id, "posts": posts})

    def pool_order(self, pool_id, sequences):
        """Reorder a pool's posts (requires login; POST).

        Parameters:
            pool_id (int): The pool id.
            sequences (dict): ``pool_post`` id -> sequence mapping, sent as
                ``pool_post_sequence[<pool_post_id>]``.

        Like :meth:`pool_import` this action always redirects to the pool page,
        and the final GET is not a write confirmation.
        """
        return self.request("POST", "pool/order",
                            data={"id": pool_id,
                                  "pool_post_sequence": sequences})

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    def note_list(self, **params):
        """Get notes (anonymous).

        Parameters:
            post_id (int): Restrict to one post; otherwise paginate 16 posts
                having notes. The server flattens all notes from those posts.
            page (int): Page number.

        The JSON reply is a flat array of every matching note.
        """
        return self.request("GET", "note", params=params)

    def note_search(self, query, **params):
        """Full-text search over note bodies (anonymous).

        Parameters:
            query (str): Search phrase. The server needs it for JSON: without a
                query the action falls into its HTML-only branch and answers
                406.
            page (int): Page number (25 notes per page).
        """
        return self.request("GET", "note/search",
                            params=dict(params, query=query))

    def note_history(self, **params):
        """Get note versions (anonymous).

        Parameters:
            id (int): Note id, evaluated before the other filters.
            post_id (int): Restrict to the notes of one post.
            user_id (int): Restrict to versions written by one user.
            page (int): Page number (25 versions, or 50 with post_id/user_id).

        The controller ignores ``limit``, so no such parameter is offered.
        """
        return self.request("GET", "note/history", params=params)

    def note_revert(self, note_id, version):
        """Revert a note to a previous version (requires login).

        Parameters:
            note_id (int): The note id.
            version (int): ``note_versions`` version number.

        A locked post answers 422.
        """
        return self.request("POST", "note/revert",
                            data={"id": note_id, "version": version})

    def note_update(self, note_id=None, **attributes):
        """Create or update a note (requires login).

        Parameters:
            note_id (int): Note id; omitted, the same endpoint creates a note.

        Attributes:
            post_id (int): The post the note belongs to; required for creation.
                The wire key is ``note[post_id]`` (``note[post]`` is ignored).
            x, y, width, height (int): Note geometry.
            body (str): Note text.
            is_active (str): ``'1'`` visible, ``'0'`` hidden.

        Returns ``{success: true, new_id, old_id, formatted_body}``; the
        engine's own interface treats a negative ``old_id`` as a creation. A
        locked post answers 422.
        """
        return self.request("POST", "note/update",
                            data=dict(_model("note", attributes), id=note_id))

    # ------------------------------------------------------------------
    # History and favorites
    # ------------------------------------------------------------------

    def history_undo(self, change_ids, redo=None):
        """Undo or redo history changes (requires login; POST only).

        Parameters:
            change_ids (iterable): ``HistoryChange`` ids (not ``History``
                ids), sent comma-joined in the ``id`` field.
            redo (str): Exact server flag ``'1'``, which reapplies the changes
                instead of undoing them.

        Returns ``{success: true, successful, failed, errors}``. Changes that
        belong to more than one history require privileged level (403).
        """
        return self.request("POST", "history/undo",
                            data={"id": ",".join(str(change_id)
                                                 for change_id in change_ids),
                                  "redo": redo})

    def favorite_list_users(self, post_id):
        """Get the users who favorited a post (anonymous; JSON only).

        Parameters:
            post_id (int): The post id; an unknown id answers 404.

        Returns the raw object ``{'favorited_users': 'name1,name2'}``. The
        server joins the names into one string (empty when nobody favorited),
        and the XML form of the route is not offered.
        """
        return self.request("GET", "favorite/list_users",
                            params={"id": post_id})

    # ------------------------------------------------------------------
    # Inline images and dmail
    # ------------------------------------------------------------------

    def inline_list(self, **params):
        """Get inline image groups (anonymous).

        Parameters:
            page (int): Page number (20 groups per page).
        """
        return self.request("GET", "inline", params=params)

    def inline_copy(self, inline_id):
        """Copy an inline image group (requires login).

        Parameters:
            inline_id (int): The group id to copy.
        """
        return self.request("POST", "inline/copy", data={"id": inline_id})

    def inline_delete(self, inline_id):
        """Delete an inline image group (requires login and ownership).

        Parameters:
            inline_id (int): The group id; the server answers 403 without
                permission on it.
        """
        return self.request("POST", "inline/delete", data={"id": inline_id})

    def dmail_mark_all_read(self):
        """Mark every dmail as read (requires login).

        The ``commit='Yes'`` selector is part of the endpoint's protocol, not a
        caller option.
        """
        return self.request("POST", "dmail/mark_all_read",
                            data={"commit": "Yes"})

    # ------------------------------------------------------------------
    # Artists
    # ------------------------------------------------------------------

    def artist_list(self, **params):
        """Get a list of artists (anonymous).

        Parameters:
            name (str): Name prefix filter.
            url (str): Filter by one of the artist's URLs.
            order (str): ``name`` (default) or ``date``.
            page (int): Page number (25 per page, 50 when filtering by name or
                url).

        Rows are ``{id, name, alias_id, group_id, urls}``; the controller does
        not read ``limit``.
        """
        return self.request("GET", "artist", params=params)

    def artist_create(self, name, **attributes):
        """Create an artist (requires login; member level).

        Parameters:
            name (str): The artist name.

        Attributes:
            alias_name (str): Name of the artist this one is an alias of.
            alias_names (str): Space-separated other names.
            member_names (str): Space-separated group members.
            urls (str): Whitespace-separated URLs.
            notes (str): Free-form notes.

        ``artist[alias]`` and ``artist[group]`` are not permitted keys. The
        reply is ``{success: true}``; validation answers 420.
        """
        return self.request("POST", "artist/create",
                            data=_model("artist", dict(attributes, name=name)))

    def artist_update(self, artist_id, **attributes):
        """Update an artist (requires login; member level).

        Parameters:
            artist_id (int): The artist id.

        Attributes: the same permitted set as :meth:`artist_create` plus
        ``name``. The reply is ``{success: true}``.
        """
        return self.request("POST", "artist/update",
                            data=dict(_model("artist", attributes),
                                      id=artist_id))

    def artist_destroy(self, artist_id):
        """Delete an artist (privileged level; POST).

        Parameters:
            artist_id (int): The artist id.

        The confirmation selector ``commit='Yes'`` is part of the endpoint:
        without it the action redirects to the artist index without deleting.
        """
        return self.request("POST", "artist/destroy",
                            data={"id": artist_id, "commit": "Yes"})

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_list(self, **params):
        """Get a list of tags (anonymous).

        Parameters:
            name (str): Substring match; ``*`` makes it a raw SQL pattern.
            id (int): Exact tag id.
            type (int): Tag type (0 general, 1 artist, 3 copyright,
                4 character).
            after_id (int): Tags with an id greater than or equal to this.
            order (str): ``name`` (default), ``date`` or ``count``.
            limit (int): Tags per page (default 50); ``0`` returns every tag.
            page (int): Page number.

        Rows are ``{id, name, count, type, ambiguous}``. The ``name_pattern``
        parameter of the old help page is not implemented by the controller.
        """
        return self.request("GET", "tag", params=params)

    def tag_related(self, **params):
        """Get tags that co-occur with the given tags (anonymous).

        Parameters:
            tags (str): Whitespace-separated tags; ``%``, ``/`` and ``*`` are
                stripped and names are lowercased by the controller.
            type (str): Restrict to one tag type from the site configuration.

        Returns the object ``{'tag': [[name, count], ...]}`` capped at 25
        entries; there is no limit parameter.
        """
        return self.request("GET", "tag/related", params=params)

    def tag_update(self, name, **attributes):
        """Update a tag (requires login; member level; POST only).

        Parameters:
            name (str): Tag name, sent as ``tag[name]`` (a top-level ``name``
                would be ignored; ``PUT /tag/update`` is not routed).

        Attributes:
            tag_type (int), is_ambiguous (str): ``'1'`` marks the tag
                ambiguous.

        The reply is ``{success: true}``; an unknown tag answers 404.
        """
        return self.request("POST", "tag/update",
                            data=_model("tag", dict(attributes, name=name)))

    def tag_autocomplete_name(self, term):
        """Autocomplete tag names (anonymous; JSON only).

        Parameters:
            term (str): Substring to match.

        Returns up to 20 names ordered by length then alphabetically.
        """
        return self.request("GET", "tag/autocomplete_name",
                            params={"term": term})

    def tag_summary(self, **params):
        """Get the cached tag summary (anonymous; JSON only).

        Parameters:
            version (int): Previously received summary version; when it is
                still current the reply is ``{version, unchanged: true}``.

        Otherwise the reply carries the summary data.
        """
        return self.request("GET", "tag/summary", params=params)

    def tag_mass_edit(self, start, result):
        """Rename one tag to another everywhere (moderator level; POST only).

        Parameters:
            start (str): Tag to replace.
            result (str): Replacement tag.

        The JSON contract exists only on sites with asynchronous tasks
        enabled, where the work is queued and answered with
        ``{success: true}``; the synchronous branch has no JSON response and
        fails with a format error instead. An empty ``start`` answers 424.
        """
        return self.request("POST", "tag/mass_edit",
                            data={"start": start, "result": result})

    def tag_alias_list(self, **params):
        """Get tag aliases (anonymous).

        Parameters:
            query (str): Match against alias names and their targets.
            page (int): Page number (20 per page).
            commit (str): ``'Search Implications'`` redirects to the
                implication list with the same query.

        Rows are ``{id, name, alias_id, pending}``.
        """
        return self.request("GET", "tag_alias", params=params)

    def tag_alias_create(self, name, alias_name, reason=None):
        """Create a tag alias (requires login; POST only).

        Parameters:
            name (str): The alias name, sent as ``tag_alias[name]``.
            alias_name (str): The target tag, sent as ``tag_alias[alias]``;
                named ``alias_name`` here because ``alias`` is a Python
                keyword.
            reason (str): Reason shown to moderators.

        The action redirects to the alias list, which the client follows; the
        final GET is not a write confirmation.
        """
        return self.request("POST", "tag_alias/create",
                            data=_model("tag_alias", {"name": name,
                                                      "alias": alias_name,
                                                      "reason": reason}))

    def tag_alias_update(self, aliases, commit, reason=None):
        """Approve or delete tag aliases (moderator level, or the creator of a
        pending alias when deleting).

        Parameters:
            aliases (dict): Alias id -> any value mapping, sent as
                ``aliases[<id>]``; only the keys are read.
            commit (str): ``'Delete'`` or ``'Approve'``; any other value
                answers 400.
            reason (str): Reason passed to the deletion notification.

        ``'Delete'`` redirects to the alias list, which the client follows.
        ``'Approve'`` redirects to the HTML-only job task page, so following it
        can raise an HTTP/JSON format error even after approval jobs were created:
        do not retry the call blindly, verify with :meth:`tag_alias_list`.
        """
        return self.request("POST", "tag_alias/update",
                            data={"aliases": aliases, "commit": commit,
                                  "reason": reason})

    def tag_implication_list(self, **params):
        """Get tag implications (anonymous).

        Parameters:
            query (str): Match against the predicate and consequent names.
            page (int): Page number (20 per page).
            commit (str): ``'Search Aliases'`` redirects to the alias list
                with the same query.

        Rows are ``{id, consequent_id, predicate_id, pending}``.
        """
        return self.request("GET", "tag_implication", params=params)

    def tag_implication_create(self, predicate, consequent, reason=None):
        """Create a tag implication (requires login; POST only).

        Parameters:
            predicate (str), consequent (str): Sent as
                ``tag_implication[predicate]`` and
                ``tag_implication[consequent]``.
            reason (str): Reason shown to moderators.

        The action redirects to the implication list, which the client follows;
        the final GET is not a write confirmation.
        """
        return self.request("POST", "tag_implication/create",
                            data=_model("tag_implication",
                                        {"predicate": predicate,
                                         "consequent": consequent,
                                         "reason": reason}))

    def tag_implication_update(self, implications, commit, reason=None):
        """Approve or delete tag implications (moderator level, or the creator
        of a pending implication when deleting).

        Parameters:
            implications (dict): Implication id -> any value mapping, sent as
                ``implications[<id>]``.
            commit (str): ``'Delete'`` or ``'Approve'``; any other value
                answers 400.
            reason (str): Reason passed to the deletion notification.

        ``'Delete'`` redirects to the implication list. ``'Approve'`` redirects
        to the HTML-only job task page, so the final HTTP/JSON response can fail
        even after approval jobs were created; verify the result instead of
        retrying blindly.
        """
        return self.request("POST", "tag_implication/update",
                            data={"implications": implications,
                                  "commit": commit, "reason": reason})

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def comment_list(self, **params):
        """Get comments (anonymous).

        Parameters:
            post_id (int): The post whose comments to list. If omitted, this
                revision queries post 0, not the global recent-comment feed.
            page (int): Page number (25 per page; ``limit`` is ignored by the
                controller).

        The route needs the explicit ``.json`` suffix, which the client always
        sends: the controller chooses JSON by format parameter, not by the
        Accept header, so an HTML request would be returned otherwise.
        """
        return self.request("GET", "comment", params=params)

    def comment_search(self, query, **params):
        """Full-text search over comment bodies (anonymous).

        Parameters:
            query (str): Search phrase; ``user:<name>`` narrows it to one
                author. An explicitly supplied empty string lists recent comments.
            page (int): Page number (30 per page).
        """
        return self.request("GET", "comment/search",
                            params=dict(params, query=query))

    def comment_show(self, comment_id):
        """Get one comment (anonymous).

        Parameters:
            comment_id (int): The comment id; unknown ids answer 404.
        """
        return self.request("GET", "comment/show", params={"id": comment_id})

    def comment_create(self, post_id, body):
        """Post a comment (requires login; member level; POST only).

        Parameters:
            post_id (int): The post to comment on, sent as
                ``comment[post_id]``.
            body (str): Comment text, sent as ``comment[body]``.

        ``comment[anonymous]`` is not a permitted key. The hourly member limit
        answers 421 and validation 420.
        """
        return self.request("POST", "comment/create",
                            data=_model("comment", {"post_id": post_id,
                                                    "body": body}))

    def comment_update(self, comment_id, **attributes):
        """Edit a comment (requires login; author or moderator).

        Parameters:
            comment_id (int): The comment id.

        Attributes:
            body (str), post_id (int).

        The server answers 403 without edit permission.
        """
        return self.request("POST", "comment/update",
                            data=dict(_model("comment", attributes),
                                      id=comment_id))

    def comment_destroy(self, comment_id):
        """Delete a comment (requires login; author or moderator).

        Parameters:
            comment_id (int): The comment id. The server answers 403 without
                permission.
        """
        return self.request("POST", "comment/destroy", data={"id": comment_id})

    def comment_mark_as_spam(self, comment_id):
        """Flag a comment as spam (POST only).

        Parameters:
            comment_id (int): The comment id.

        This route carries no login or permission filter in the controller, so
        an anonymous client can call it. The comment is only marked; the reply
        is ``{success: true}``.
        """
        return self.request("POST", "comment/mark_as_spam",
                            data={"id": comment_id})

    # ------------------------------------------------------------------
    # Wiki pages
    # ------------------------------------------------------------------

    def wiki_list(self, **params):
        """Get wiki pages (anonymous).

        Parameters:
            query (str): Title search; a ``title:`` prefix drops the body
                search.
            order (str): ``title`` (default) or ``date``.
            limit (int): Pages per response (default 25).
            page (int): Page number.

        Rows are ``{id, created_at, updated_at, title, body, updater_id,
        locked, version}``.
        """
        return self.request("GET", "wiki", params=params)

    def wiki_history(self, title=None, **params):
        """Get the versions of a wiki page (anonymous).

        Parameters:
            title (str): Page title.
            params: ``id`` selects the page by id when ``title`` is omitted.

        Returns every version, newest first, without pagination.
        """
        return self.request("GET", "wiki/history",
                            params=dict(params, title=title))

    def wiki_recent_changes(self, **params):
        """Get recently changed wiki pages (anonymous).

        Parameters:
            user_id (int): Restrict to one editor.
            per_page (int): Pages per response (default 25).
            page (int): Page number.
        """
        return self.request("GET", "wiki/recent_changes", params=params)

    def wiki_create(self, title, body):
        """Create a wiki page (requires login; member level; POST only).

        Parameters:
            title (str), body (str): Sent as ``wiki_page[title]`` and
                ``wiki_page[body]``.

        Returns ``{success: true, location}``; validation answers 420.
        """
        return self.request("POST", "wiki/create",
                            data=_model("wiki_page", {"title": title,
                                                      "body": body}))

    def wiki_update(self, title, *, new_title=None, **attributes):
        """Update a wiki page (requires login; member level; POST only).

        Parameters:
            title (str): Top-level selector for the page to update.
            new_title (str): New title, sent as ``wiki_page[title]`` without
                colliding with the top-level page selector.

        Attributes:
            body (str): New body.

        At least one ``wiki_page[...]`` key must be sent: the controller
        requires the nested hash and answers 400 when it is missing. A locked
        page answers 422.
        """
        return self.request("POST", "wiki/update",
                            data=dict(_model("wiki_page", dict(attributes, title=new_title)),
                                      title=title))

    def wiki_destroy(self, title):
        """Delete a wiki page (moderator level).

        Parameters:
            title (str): Page title.
        """
        return self.request("POST", "wiki/destroy", data={"title": title})

    def wiki_lock(self, title):
        """Lock a wiki page (moderator level).

        Parameters:
            title (str): Page title; an unknown title answers 500.
        """
        return self.request("POST", "wiki/lock", data={"title": title})

    def wiki_unlock(self, title):
        """Unlock a wiki page (moderator level).

        Parameters:
            title (str): Page title.
        """
        return self.request("POST", "wiki/unlock", data={"title": title})

    def wiki_revert(self, title, version):
        """Revert a wiki page to a previous version (requires login).

        Parameters:
            title (str): Page title.
            version (int): ``wiki_page_versions`` version to restore.

        A locked page answers 422. The HTML-only ``wiki/show`` page of the
        API's earlier help file is not a JSON route, so it is not wrapped here.
        """
        return self.request("POST", "wiki/revert",
                            data={"title": title, "version": version})

    # ------------------------------------------------------------------
    # Forum
    # ------------------------------------------------------------------

    def forum_list(self, **params):
        """Get forum posts (anonymous).

        Parameters:
            parent_id (int): Replies of one topic (100 per page).
            latest (str): The ten latest posts.
            page (int): Page number (30 topics per page).

        Rows are ``{id, parent_id, title, body, creator, creator_id,
        updated_at, pages}``.
        """
        return self.request("GET", "forum", params=params)

    def forum_show(self, forum_id, **params):
        """Get one forum post (anonymous).

        Parameters:
            forum_id (int): The post id.
            params: ``page`` paginates the replies in the HTML view only.

        Returns one forum post object.
        """
        return self.request("GET", "forum/show",
                            params=dict(params, id=forum_id))

    def forum_search(self, query, **params):
        """Full-text search over forum posts (anonymous).

        Parameters:
            query (str): Search phrase.
            page (int): Page number (30 per page).
        """
        return self.request("GET", "forum/search",
                            params=dict(params, query=query))

    def forum_create(self, title, body, **attributes):
        """Start a forum topic or reply to one (requires login; POST only).

        Parameters:
            title (str), body (str): Sent as ``forum_post[title]`` and
                ``forum_post[body]``.

        Attributes:
            parent_id (int): Post to reply to; ``0`` or omitted starts a new
                topic.

        The action redirects to the topic, whose JSON page the client follows;
        the final GET is not a write confirmation.
        """
        return self.request("POST", "forum/create",
                            data=_model("forum_post",
                                        dict(attributes, title=title,
                                             body=body)))

    def forum_update(self, forum_id, **attributes):
        """Edit a forum post (requires login; creator or moderator).

        Parameters:
            forum_id (int): The post id.

        Attributes:
            title (str), body (str), parent_id (int).

        The action redirects to the topic; the server answers 403 without edit
        permission.
        """
        return self.request("POST", "forum/update",
                            data=dict(_model("forum_post", attributes),
                                      id=forum_id))

    def forum_destroy(self, forum_id):
        """Delete a forum post or topic (requires login; creator or moderator).

        Parameters:
            forum_id (int): The post id.
        """
        return self.request("POST", "forum/destroy", data={"id": forum_id})

    def forum_lock(self, forum_id):
        """Lock a forum topic (moderator level).

        Parameters:
            forum_id (int): The topic id, read from the body for this route.
        """
        return self.request("POST", "forum/lock", data={"id": forum_id})

    def forum_unlock(self, forum_id):
        """Unlock a forum topic (moderator level).

        Parameters:
            forum_id (int): The topic id.
        """
        return self.request("POST", "forum/unlock", data={"id": forum_id})

    def forum_stick(self, forum_id):
        """Pin a forum topic (moderator level).

        Parameters:
            forum_id (int): The topic id.
        """
        return self.request("POST", "forum/stick", data={"id": forum_id})

    def forum_unstick(self, forum_id):
        """Unpin a forum topic (moderator level).

        Parameters:
            forum_id (int): The topic id.
        """
        return self.request("POST", "forum/unstick", data={"id": forum_id})

    def forum_mark_all_read(self):
        """Mark every forum post as read (requires login).

        The endpoint answers an empty 204, so the client returns ``None``.
        """
        return self.request("POST", "forum/mark_all_read")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def user_list(self, **params):
        """Get a list of users (anonymous).

        Parameters:
            name (str): Substring match on the name.
            level (int): Exact user level.
            id (int): Exact user id.
            order (str): Result order.
            page (int): Page number.

        Rows carry only ``{name, id}``.
        """
        return self.request("GET", "user", params=params)

    def user_autocomplete_name(self, term):
        """Autocomplete user names (anonymous; JSON only).

        Parameters:
            term (str): Substring to match; shorter than two characters, the
                server returns an empty list.
        """
        return self.request("GET", "user/autocomplete_name",
                            params={"term": term})

    def user_check(self, username, password):
        """Check a username and password (POST only).

        Parameters:
            username (str), password (str): Sent in clear text as top-level
                fields; this distinct endpoint expects the plain password, not
                the configured password hash.

        Returns the login helper payload ``{response, exists, name, id,
        no_email, pass_hash, user_info}``. Source-aligned only; not exercised
        against a live site.
        """
        return self.request("POST", "user/check",
                            data={"username": username, "password": password})

    def user_create(self, name, password, password_confirmation, **attributes):
        """Register a user (anonymous; POST only).

        Parameters:
            name (str), password (str), password_confirmation (str): Sent as
                ``user[name]``, ``user[password]`` and
                ``user[password_confirmation]``.

        Attributes: the remaining ``user[...]`` settings (``email``,
        ``blacklisted_tags`` and the display switches).

        Registration answers 200 even when it fails:
        ``{response: 'success' | 'error', errors: [...]}``. Source-aligned only;
        not exercised against a live site.
        """
        user = {"name": name, "password": password,
                "password_confirmation": password_confirmation}
        return self.request("POST", "user/create",
                            data=_model("user", dict(attributes, **user)))

    def user_update(self, **attributes):
        """Update the logged-in user's settings (requires login; POST).

        Attributes: ``email``, ``current_password``, ``password``,
        ``password_confirmation``, ``blacklisted_tags``,
        ``always_resize_images``, ``receive_dmails``, ``show_samples``,
        ``use_browser``, ``show_advanced_editing`` and ``pool_browse_mode``.

        The reply is ``{success: true}``; validation answers 420.
        """
        return self.request("POST", "user/update", data=_model("user", attributes))

    def user_authenticate(self, **params):
        """Re-authenticate the current session (requires login).

        Parameters:
            url (str): Site-relative path to return to; other values are
                ignored by the controller.
        """
        return self.request("POST", "user/authenticate", data=params)

    def user_modify_blacklist(self, add=None, remove=None):
        """Add to and remove from the logged-in user's tag blacklist (requires
        login).

        Parameters:
            add (list): Tags to append, sent as repeated ``add[]`` fields.
            remove (list): Tags to drop, sent as repeated ``remove[]`` fields.

        Returns ``{success: true, result: [...]}`` with the new blacklist.
        """
        return self.request("POST", "user/modify_blacklist",
                            data={"add": add, "remove": remove})

    def user_reset_password(self, name, email):
        """Request a password reset mail (anonymous; POST).

        Parameters:
            name (str), email (str): Sent as ``user[name]`` and
                ``user[email]``; both must match the same account.

        Returns ``{result: 'success'}``, or answers 500 with ``result`` set to
        ``'unknown-user'``, ``'no-email'`` or ``'wrong-email'``. Source-aligned
        only; not exercised against a live site.
        """
        return self.request("POST", "user/reset_password",
                            data=_model("user", {"name": name, "email": email}))

    def user_record_destroy(self, user_record_id):
        """Delete a user record (privileged level, and moderator or reporter).

        Parameters:
            user_record_id (int): The record id; the server answers 403
                without permission.
        """
        return self.request("POST", "user_record/destroy",
                            data={"id": user_record_id})
