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
      (``pool_import``, ``pool_order``, ``pool_copy`` and the alias,
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
        """Approve pending posts (requires login; janitor level).

        Parameters:
            post_ids (list): Post ids, sent as repeated ``post_ids[]`` fields.
                The server expects an array and answers an empty 204 for any
                other value.
        """
        return self.request("POST", "post/activate",
                            data={"post_ids": post_ids})

    def post_acknowledge_new_deleted_posts(self):
        """Mark the new-deleted-posts notice as seen (requires login)."""
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

        The action redirects to the new pool, whose JSON page the client
        follows; that page does not by itself confirm the copy. The reply is
        ``{success: true}`` and the new id is only in the redirect.
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
            post_id (int): Restrict to one post (100 notes per page); without
                it only posts that carry notes are listed, 16 per page.
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

    def tag_list(self, **params):
        """Get a list of tags.

        Parameters:
            name (str): The exact name of the tag.
            id (int): The id number of the tag.
            limit (int): How many tags to retrieve. Setting this to 0 will
                         return every tag (Default value: 0).
            page (int): The page number.
            order (str): Can be 'date', 'name' or 'count'.
            after_id (int): Return all tags that have an id number greater
                            than this.
        """
        return self.request('GET', 'tag', params=params)

    def tag_update(self, name=None, tag_type=None, is_ambiguous=None):
        """Action to lets you update tag (Requires login) (UNTESTED).

        Parameters:
            name (str): The name of the tag to update.
            tag_type (int):
                * General: 0.
                * artist: 1.
                * copyright: 3.
                * character: 4.
            is_ambiguous (int): Whether or not this tag is ambiguous. Use 1
                                for True and 0 for False.
        """
        params = {
            'name': name,
            'tag[tag_type]': tag_type,
            'tag[is_ambiguous]': is_ambiguous
            }
        return self.request('PUT', 'tag/update', data=params)

    def tag_related(self, **params):
        """Get a list of related tags.

        Parameters:
            tags (str): The tag names to query.
            type (str): Restrict results to this tag type. Can be general,
                        artist, copyright, or character.
        """
        return self.request('GET', 'tag/related', params=params)

    def artist_list(self, **params):
        """Get a list of artists.

        Parameters:
            name (str): The name (or a fragment of the name) of the artist.
            order (str): Can be date or name.
            page (int): The page number.
        """
        return self.request('GET', 'artist', params=params)

    def artist_create(self, name, urls=None, alias=None, group=None):
        """Function to create an artist (Requires login) (UNTESTED).

        Parameters:
            name (str): The artist's name.
            urls (str): A list of URLs associated with the artist, whitespace
                        delimited.
            alias (str): The artist that this artist is an alias for. Simply
                         enter the alias artist's name.
            group (str): The group or cicle that this artist is a member of.
                         Simply:param  enter the group's name.
        """
        params = {
            'artist[name]': name,
            'artist[urls]': urls,
            'artist[alias]': alias,
            'artist[group]': group
            }
        return self.request('POST', 'artist/create', data=params)

    def artist_update(self, artist_id, name=None, urls=None, alias=None,
                      group=None):
        """Function to update artists (Requires Login) (UNTESTED).

        Only the artist_id parameter is required. The other parameters are
        optional.

        Parameters:
            artist_id (int): The id of thr artist to update (Type: INT).
            name (str): The artist's name.
            urls (str): A list of URLs associated with the artist, whitespace
                        delimited.
            alias (str): The artist that this artist is an alias for. Simply
                         enter the alias artist's name.
            group (str): The group or cicle that this artist is a member of.
                         Simply enter the group's name.
        """
        params = {
            'id': artist_id,
            'artist[name]': name,
            'artist[urls]': urls,
            'artist[alias]': alias,
            'artist[group]': group
            }
        return self.request('PUT', 'artist/update', data=params)

    def artist_destroy(self, artist_id):
        """Action to lets you remove artist (Requires login) (UNTESTED).

        Parameters:
            artist_id (int): The id of the artist to destroy.
        """
        return self.request('POST', 'artist/destroy', data={'id': artist_id})

    def comment_show(self, comment_id):
        """Get a specific comment.

        Parameters:
            comment_id (str): The id number of the comment to retrieve.
        """
        return self.request('GET', 'comment/show', params={'id': comment_id})

    def comment_create(self, post_id, comment_body, anonymous=None):
        """Action to lets you create a comment (Requires login).

        Parameters:
            post_id (int): The post id number to which you are responding.
            comment_body (str): The body of the comment.
            anonymous (int): Set to 1 if you want to post this comment
                             anonymously.
        """
        params = {
            'comment[post_id]': post_id,
            'comment[body]': comment_body,
            'comment[anonymous]': anonymous
            }
        return self.request('POST', 'comment/create', data=params)

    def comment_destroy(self, comment_id):
        """Remove a specific comment (Requires login).

        Parameters:
            comment_id (int): The id number of the comment to remove.
        """
        return self.request('DELETE', 'comment/destroy', data={'id': comment_id})

    def wiki_list(self, **params):
        """Function to retrieves a list of every wiki page.

        Parameters:
            query (str): A word or phrase to search for (Default: None).
            order (str): Can be: title, date (Default: title).
            limit (int): The number of pages to retrieve (Default: 100).
            page (int): The page number.
        """
        return self.request('GET', 'wiki', params=params)

    def wiki_create(self, title, body):
        """Action to lets you create a wiki page (Requires login) (UNTESTED).

        Parameters:
            title (str): The title of the wiki page.
            body (str): The body of the wiki page.
        """
        params = {'wiki_page[title]': title, 'wiki_page[body]': body}
        return self.request('POST', 'wiki/create', data=params)

    def wiki_update(self, title, new_title=None, page_body=None):
        """Action to lets you update a wiki page (Requires login) (UNTESTED).

        Parameters:
            title (str): The title of the wiki page to update.
            new_title (str): The new title of the wiki page.
            page_body (str): The new body of the wiki page.
        """
        params = {
            'title': title,
            'wiki_page[title]': new_title,
            'wiki_page[body]': page_body
            }
        return self.request('PUT', 'wiki/update', data=params)

    def wiki_show(self, **params):
        """Get a specific wiki page.

        Parameters:
            title (str): The title of the wiki page to retrieve.
            version (int): The version of the page to retrieve.
        """
        return self.request('GET', 'wiki/show', params=params)

    def wiki_destroy(self, title):
        """Function to delete a specific wiki page (Requires login)
        (Only moderators) (UNTESTED).

        Parameters:
            title (str): The title of the page to delete.
        """
        return self.request('DELETE', 'wiki/destroy', data={'title': title})

    def wiki_lock(self, title):
        """Function to lock a specific wiki page (Requires login)
        (Only moderators) (UNTESTED).

        Parameters:
            title (str): The title of the page to lock.
        """
        return self.request('POST', 'wiki/lock', data={'title': title})

    def wiki_unlock(self, title):
        """Function to unlock a specific wiki page (Requires login)
        (Only moderators) (UNTESTED).

        Parameters:
            title (str): The title of the page to unlock.
        """
        return self.request('POST', 'wiki/unlock', data={'title': title})

    def wiki_revert(self, title, version):
        """Function to revert a specific wiki page (Requires login) (UNTESTED).

        Parameters:
            title (str): The title of the wiki page to update.
            version (int): The version to revert to.
        """
        params = {'title': title, 'version': version}
        return self.request('PUT', 'wiki/revert', data=params)

    def wiki_history(self, title):
        """Get history of specific wiki page.

        Parameters:
            title (str): The title of the wiki page to retrieve versions for.
        """
        return self.request('GET', 'wiki/history', params={'title': title})

    def user_search(self, **params):
        """Search users.

        If you don't specify any parameters you'll _get a listing of all users.

        Parameters:
            id (int): The id number of the user.
            name (str): The name of the user.
        """
        return self.request('GET', 'user', params=params)

    def forum_list(self, **params):
        """Function to get forum posts.

        If you don't specify any parameters you'll _get a listing of all users.

        Parameters:
            parent_id (int): The parent ID number. You'll return all the
                             responses to that forum post.
        """
        return self.request('GET', 'forum', params=params)
