# -*- coding: utf-8 -*-

"""pybooru.api_danbooru

This module contains all API calls of Danbooru.

Every method is one thin call to ``Danbooru.request()`` against a route from
``danbooru/config/routes.rb``; parameters follow the controllers' strong
parameters (``app/policies``) and search parameters (``def search`` in
``app/models``). Paths are relative and end in ``.json``.

Conventions:
    * List methods take ``search`` (a full search-parameter dictionary that is
      sent as ``search[...]``) and ``**params`` (top-level parameters such as
      ``limit``, ``page``, ``tags``, ``post_id``). Nothing is filtered or
      clamped locally; the server validates.
    * Write methods take a semantic signature plus ``**attributes``; the
      attributes become the model's nested parameters (for example
      ``post[tag_string]``). Top-level parameters that the controller reads
      outside the model namespace are passed explicitly in the signature.
      Attribute values are passed as a structured body, so empty lists and
      booleans keep their meaning. :meth:`upload_create` is the one method
      that sends a multipart body, because it uploads files.
    * Authentication is not decided here. The client attaches HTTP Basic
      credentials when a username and API key are configured and the server
      applies its own permissions.
    * Write endpoints are aligned with the current source but were not
      exercised against a live site.

Classes:
    DanbooruApi_Mixin -- Contains all API endpoints.
"""

# __future__ imports
from __future__ import absolute_import

# Standard library imports
from urllib.parse import quote


def _search(search, params):
    """Merge a full search-parameter dictionary into top-level parameters."""
    if search is None:
        return params
    return dict(params, search=search)


def _model(model, attributes):
    """Nest attribute values under their model's strong-parameter key."""
    return {model: attributes}


class DanbooruApi_Mixin(object):
    """Contains all Danbooru API calls.

    * Source: https://github.com/danbooru/danbooru (config/routes.rb)
    * Doc: https://danbooru.donmai.us/wiki_pages/help%3Aapi
    """

    # ------------------------------------------------------------------
    # Status and account
    # ------------------------------------------------------------------

    def status(self):
        """Get the server status (including the current user's level)."""
        return self.request("GET", "status.json")

    def api_keys_list(self, search=None, **params):
        """Get a list of API keys (requires login; only your own are visible)."""
        return self.request("GET", "api_keys.json", params=_search(search, params))

    def api_key_create(self, **attributes):
        """Create an API key (requires login; source-aligned, untested).

        Attributes:
            name (str): The name of the key.
            permitted_ip_addresses (str): Space-separated allowed IP ranges.
            permissions (list): Permission names.
        """
        return self.request("POST", "api_keys.json", data=_model("api_key", attributes))

    def api_key_update(self, api_key_id, **attributes):
        """Update an API key (requires login; source-aligned, untested).

        Attributes: see :meth:`api_key_create`.
        """
        return self.request("PUT", "api_keys/{0}.json".format(api_key_id),
                            data=_model("api_key", attributes))

    def api_key_delete(self, api_key_id):
        """Delete an API key (requires login; source-aligned, untested)."""
        return self.request("DELETE", "api_keys/{0}.json".format(api_key_id))

    def rate_limits_list(self, search=None, **params):
        """Get a list of rate limits.

        Parameters:
            search (dict): ``id``, ``action``, ``key``, ``limited``, ``points``.
            limit (int): Limits per page.
            page (int): Page number.
        """
        return self.request("GET", "rate_limits.json", params=_search(search, params))

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def post_list(self, **params):
        """Get a list of posts.

        The posts index does not read a ``search`` dictionary: it builds its
        query through ``PostSets::Post``, so every filter has to be expressed
        as a metatag inside the ``tags`` query string (``rating:g``,
        ``score:>10``, ``order:score``, ``limit:50``, ``id:>123``, ...).

        Parameters:
            tags (str): The tag query.
            limit (int): Posts per page (the server caps this at 200).
            page (int): Page number (an ``a<id>``/``b<id>`` value also works).
            md5 (str): Return the single post with this MD5 instead of a list.
            random (bool): Return a randomized page instead of the newest posts.
            size (str): Preview size, e.g. ``"medium"``.
            show_votes (bool): Include the current user's votes in `tag_string`.
            only (str): Side-load extra attributes, e.g. ``"id,media_asset"``.
        """
        return self.request("GET", "posts.json", params=params)

    def post_show(self, post_id):
        """Get a specific post.

        Parameters:
            post_id (int): The post id.
        """
        return self.request("GET", "posts/{0}.json".format(post_id))

    def post_random(self, tags=None):
        """Get one random post matching a tag query.

        Parameters:
            tags (str): Tag query; empty means any post.
        """
        return self.request("GET", "posts/random.json", params={"tags": tags})

    def post_create(self, upload_media_asset_id, **attributes):
        """Create a post from an uploaded file (requires login).

        The file must already exist as an upload media asset (see
        :meth:`upload_create` and :meth:`upload_assets_list`); the server
        refuses assets that are not yours. Source-aligned, untested.

        Parameters:
            upload_media_asset_id (int): The upload media asset id. It is read
                as a **top-level** parameter, so it must not be nested inside
                ``post`` (the controller would otherwise pass it on as an
                unknown attribute).

        Attributes:
            tag_string (str): Space-separated tags.
            rating (str): ``g``, ``s``, ``q`` or ``e``.
            parent_id (int): The parent post id.
            source (str): The source URL or text.
            is_pending (bool): Post the upload as pending moderation.
            artist_commentary (dict): ``original_title``,
                ``original_description``, ``translated_title``,
                ``translated_description``.
        """
        return self.request("POST", "posts.json",
                            data=dict(_model("post", attributes),
                                      upload_media_asset_id=upload_media_asset_id))

    def post_update(self, post_id, **attributes):
        """Update a post (requires login; source-aligned, untested).

        Attributes:
            tag_string (str): The new space-separated tags.
            old_tag_string (str): The previous tags, for conflict detection.
            parent_id (int): The parent post id.
            old_parent_id (int): The previous parent, for conflict detection.
            source (str): The new source.
            old_source (str): The previous source, for conflict detection.
            rating (str): ``g``, ``s``, ``q`` or ``e``.
            old_rating (str): The previous rating, for conflict detection.
            has_embedded_notes (bool): Whether the post has notes in the image.
        """
        return self.request("PUT", "posts/{0}.json".format(post_id),
                            data=_model("post", attributes))

    def post_delete(self, post_id, reason, move_favorites=None):
        """Delete a post (requires approver level and above).

        The controller only deletes when the ``commit`` parameter is
        ``Delete``, so it is sent here; a blank reason makes the server roll
        the deletion back (the deletion is recorded as a post flag, which
        requires a reason). Source-aligned, untested.

        Parameters:
            post_id (int): The post id.
            reason (str): The deletion reason.
            move_favorites (bool): Move favorites to the parent post.
        """
        data = {"commit": "Delete",
                "post": {"reason": reason, "move_favorites": move_favorites}}
        return self.request("DELETE", "posts/{0}.json".format(post_id), data=data)

    def post_revert(self, post_id, version_id):
        """Revert a post to a previous version (requires login).

        Parameters:
            post_id (int): The post id.
            version_id (int): The post version id to revert to.
        """
        return self.request("PUT", "posts/{0}/revert.json".format(post_id),
                            data={"version_id": version_id})

    def post_copy_notes(self, post_id, other_post_id):
        """Copy a post's notes to another post (requires login).

        Returns ``None`` on success: the server answers 204 with an empty body
        (and 400 with ``{"success": false, "reason": ...}`` on failure).

        Parameters:
            post_id (int): The post to copy notes from.
            other_post_id (int): The post to copy notes to (top-level).
        """
        return self.request("PUT", "posts/{0}/copy_notes.json".format(post_id),
                            data={"other_post_id": other_post_id})

    def post_mark_as_translated(self, post_id, check_translation=None,
                                partially_translated=None):
        """Update the translation tags of a post (requires login).

        Parameters:
            post_id (int): The post id.
            check_translation (bool): Add or remove ``check_translation``.
            partially_translated (bool): Add or remove ``partially_translated``.
        """
        data = _model("post", {"check_translation": check_translation,
                               "partially_translated": partially_translated})
        return self.request("PUT", "posts/{0}/mark_as_translated.json".format(post_id),
                            data=data)

    def post_events_list(self, search=None, **params):
        """Get a list of post events (tag/rating/source changes).

        Parameters:
            search (dict): ``post_id``, ``category``, ``event_at``,
                ``creator_id``, ``creator_name``, ``order``.
            post_id (int): Restrict to one post (top-level parameter).
            limit (int): Events per page.
            page (int): Page number.
        """
        return self.request("GET", "post_events.json", params=_search(search, params))

    def post_versions_list(self, search=None, **params):
        """Get a list of post versions (requires the archive service).

        Danbooru only routes the index and the undo action for post versions
        (``resources :post_versions, only: [:index]``), so there is no
        single-version route to call.

        Parameters:
            search (dict): ``id``, ``post_id``, ``updater_id``, ``updater_name``,
                ``tags``, ``added_tags``, ``removed_tags``, ``changed_tags``,
                ``all_changed_tags``, ``any_changed_tags``, ``tag_matches``,
                ``rating``, ``parent_id``, ``source``, ``version``, ``is_new``.
            limit (int): Versions per page.
            page (int): Page number.
        """
        return self.request("GET", "post_versions.json", params=_search(search, params))

    def post_version_undo(self, version_id):
        """Undo a post version (requires login; source-aligned, untested).

        Parameters:
            version_id (int): The post version id to undo.
        """
        return self.request("PUT", "post_versions/{0}/undo.json".format(version_id))

    def post_votes_list(self, search=None, **params):
        """Get a list of post votes.

        Parameters:
            search (dict): ``post_id``, ``user_id``, ``user_name``, ``score``,
                ``is_deleted``.
            limit (int): Votes per page.
            page (int): Page number.
        """
        return self.request("GET", "post_votes.json", params=_search(search, params))

    def post_vote_show(self, vote_id):
        """Get a specific post vote.

        Parameters:
            vote_id (int): The post vote id.
        """
        return self.request("GET", "post_votes/{0}.json".format(vote_id))

    def post_vote_create(self, post_id, score):
        """Vote on a post (requires login).

        Parameters:
            post_id (int): The post id.
            score (str): ``up`` or ``down``.
        """
        return self.request("POST", "posts/{0}/votes.json".format(post_id),
                            data={"score": score})

    def post_vote_delete(self, vote_id):
        """Delete (retract) a post vote (requires login).

        Danbooru has no route for retracting a vote by post id; look the vote
        id up through :meth:`post_votes_list` (``search={"post_id": ...}``).

        Parameters:
            vote_id (int): The post vote id.
        """
        return self.request("DELETE", "post_votes/{0}.json".format(vote_id))

    def post_favorites_list(self, post_id, search=None, **params):
        """Get the favorites of a post.

        Parameters:
            post_id (int): The post id.
            limit (int): Favorites per page.
            page (int): Page number.
        """
        return self.request("GET", "posts/{0}/favorites.json".format(post_id),
                            params=_search(search, params))

    def post_replacements_list(self, search=None, **params):
        """Get a list of post replacements.

        Parameters:
            search (dict): ``post_id``, ``creator_id``, ``creator_name``,
                ``status``, ``order``.
            post_id (int): Restrict to one post (top-level parameter).
            limit (int): Replacements per page.
            page (int): Page number.
        """
        return self.request("GET", "post_replacements.json", params=_search(search, params))

    def post_replacement_show(self, replacement_id):
        """Get a specific post replacement.

        Parameters:
            replacement_id (int): The post replacement id.
        """
        return self.request("GET", "post_replacements/{0}.json".format(replacement_id))

    def post_replacement_create(self, post_id, replacement_file=None, **attributes):
        """Replace a post's file (requires moderator; source-aligned, untested).

        Parameters:
            post_id (int): The post to replace (top-level).
            replacement_file (file): Open binary file owned by the caller.

        Attributes:
            replacement_url (str): URL of the new file.
            final_source (str): The source of the replacement.
            tags (str): Tags to add to the post.
        """
        files = (None if replacement_file is None else
                 {"post_replacement[replacement_file]": replacement_file})
        return self.request("POST", "post_replacements.json",
                            data=dict(_model("post_replacement", attributes),
                                      post_id=post_id), files=files)

    def post_replacement_update(self, replacement_id, **attributes):
        """Update a post replacement (requires login; source-aligned, untested).

        Attributes:
            old_file_ext, old_file_size, old_image_width, old_image_height,
            old_md5, file_ext, file_size, image_width, image_height, md5,
            original_url, replacement_url.
        """
        return self.request("PUT", "post_replacements/{0}.json".format(replacement_id),
                            data=_model("post_replacement", attributes))

    def post_regeneration_create(self, post_id, category=None):
        """Schedule regeneration of a post's image (requires moderator level).

        Parameters:
            post_id (int): The post id (top-level).
            category (str): `post` for the original file, `large` or `preview`
                for a single size.
        """
        return self.request("POST", "post_regenerations.json",
                            data={"post_id": post_id, "category": category})

    def post_approvals_list(self, search=None, **params):
        """Get a list of post approvals.

        Parameters:
            search (dict): ``post_id``, ``user_id``, ``user_name``.
            limit (int): Approvals per page.
            page (int): Page number.
        """
        return self.request("GET", "post_approvals.json", params=_search(search, params))

    def post_approval_show(self, approval_id):
        """Get a specific post approval.

        Parameters:
            approval_id (int): The post approval id.
        """
        return self.request("GET", "post_approvals/{0}.json".format(approval_id))

    def post_approval_create(self, post_id):
        """Approve a post (requires approver level; source-aligned, untested).

        Parameters:
            post_id (int): The post id (top-level).
        """
        return self.request("POST", "post_approvals.json", data={"post_id": post_id})

    def post_disapprovals_list(self, search=None, **params):
        """Get a list of post disapprovals.

        Parameters:
            search (dict): ``post_id``, ``user_id``, ``user_name``, ``reason``,
                ``message_matches``.
            limit (int): Disapprovals per page.
            page (int): Page number.
        """
        return self.request("GET", "post_disapprovals.json", params=_search(search, params))

    def post_disapproval_show(self, disapproval_id):
        """Get a specific post disapproval.

        Parameters:
            disapproval_id (int): The post disapproval id.
        """
        return self.request("GET", "post_disapprovals/{0}.json".format(disapproval_id))

    def post_disapproval_create(self, post_id, **attributes):
        """Disapprove a post (requires approver level; source-aligned, untested).

        Parameters:
            post_id (int): The disapproved post (inside ``post_disapproval``,
                as the controller reads it there).

        Attributes:
            reason (str): ``borderline_quality``, ``borderline_safety``,
                ``breaks_rules``, ``disinterest`` or ``poor_quality``.
            message (str): An optional explanation.
        """
        return self.request("POST", "post_disapprovals.json",
                            data=_model("post_disapproval", dict(attributes, post_id=post_id)))

    def post_disapproval_update(self, disapproval_id, **attributes):
        """Update a post disapproval (requires login; source-aligned, untested).

        Attributes: see :meth:`post_disapproval_create`.
        """
        return self.request("PUT", "post_disapprovals/{0}.json".format(disapproval_id),
                            data=_model("post_disapproval", attributes))

    def post_flags_list(self, search=None, **params):
        """Get a list of post flags.

        Parameters:
            search (dict): ``id``, ``post_id``, ``reason_matches``, ``status``
                (``pending``/``succeeded``/``rejected``), ``category``
                (``normal``/``unapproved``/``rejected``/``deleted``),
                ``creator_id``, ``creator_name``.
            limit (int): Flags per page.
            page (int): Page number.
        """
        return self.request("GET", "post_flags.json", params=_search(search, params))

    def post_flag_show(self, flag_id):
        """Get a specific post flag.

        Parameters:
            flag_id (int): The post flag id.
        """
        return self.request("GET", "post_flags/{0}.json".format(flag_id))

    def post_flag_create(self, post_id, reason, **attributes):
        """Flag a post (requires login; source-aligned, untested).

        Parameters:
            post_id (int): The post to flag.
            reason (str): The reason for flagging.
        """
        return self.request("POST", "post_flags.json",
                            data=_model("post_flag", dict(attributes, post_id=post_id,
                                                          reason=reason)))

    def post_flag_update(self, flag_id, reason, **attributes):
        """Update a post flag (requires login; source-aligned, untested).

        Parameters:
            flag_id (int): The post flag id.
            reason (str): The updated reason.
        """
        return self.request("PUT", "post_flags/{0}.json".format(flag_id),
                            data=_model("post_flag", dict(attributes, reason=reason)))

    def post_appeals_list(self, search=None, **params):
        """Get a list of post appeals.

        Parameters:
            search (dict): ``id``, ``post_id``, ``reason_matches``, ``status``,
                ``creator_id``, ``creator_name``.
            limit (int): Appeals per page.
            page (int): Page number.
        """
        return self.request("GET", "post_appeals.json", params=_search(search, params))

    def post_appeal_show(self, appeal_id):
        """Get a specific post appeal.

        Parameters:
            appeal_id (int): The post appeal id.
        """
        return self.request("GET", "post_appeals/{0}.json".format(appeal_id))

    def post_appeal_create(self, post_id, reason, **attributes):
        """Appeal a deleted post (requires login; source-aligned, untested).

        Parameters:
            post_id (int): The deleted post to appeal.
            reason (str): The reason for appealing.
        """
        return self.request("POST", "post_appeals.json",
                            data=_model("post_appeal", dict(attributes, post_id=post_id,
                                                            reason=reason)))

    def post_appeal_update(self, appeal_id, reason, **attributes):
        """Update a post appeal (requires login; source-aligned, untested).

        Parameters:
            appeal_id (int): The post appeal id.
            reason (str): The updated reason.
        """
        return self.request("PUT", "post_appeals/{0}.json".format(appeal_id),
                            data=_model("post_appeal", dict(attributes, reason=reason)))

    # ------------------------------------------------------------------
    # Media assets, media metadata, AI tags
    # ------------------------------------------------------------------

    def media_assets_list(self, search=None, **params):
        """Get a list of media assets.

        Parameters:
            search (dict): ``id``, ``md5``, ``pixel_hash``, ``status``,
                ``file_ext``, ``file_size``, ``image_width``, ``image_height``,
                ``duration``, ``is_public``, ``metadata``, ``ai_tags_match``,
                ``min_score``, ``is_posted``, ``order``.
            limit (int): Assets per page.
            page (int): Page number.
        """
        return self.request("GET", "media_assets.json", params=_search(search, params))

    def media_asset_show(self, media_asset_id):
        """Get a specific media asset.

        Assets that are not visible to the current user come back without
        ``md5``, ``file_key`` and ``variants``.

        Parameters:
            media_asset_id (int): The media asset id.
        """
        return self.request("GET", "media_assets/{0}.json".format(media_asset_id))

    def media_asset_delete(self, media_asset_id):
        """Delete a media asset (requires moderator level; source-aligned, untested).

        Parameters:
            media_asset_id (int): The media asset id.
        """
        return self.request("DELETE", "media_assets/{0}.json".format(media_asset_id))

    def media_metadata_list(self, search=None, **params):
        """Get a list of media metadata records.

        Parameters:
            search (dict): ``media_asset_id``, ``metadata``.
            limit (int): Records per page.
            page (int): Page number.
        """
        return self.request("GET", "media_metadata.json", params=_search(search, params))

    def ai_tags_list(self, search=None, **params):
        """Get a list of AI-generated tags.

        Parameters:
            search (dict): ``media_asset_id``, ``tag_id``, ``tag_name``,
                ``post_id``, ``score``, ``is_posted``, ``order``.
            limit (int): Tags per page.
            page (int): Page number.
        """
        return self.request("GET", "ai_tags.json", params=_search(search, params))

    def ai_tag_tag(self, media_asset_id, tag_id, tag=None, mode=None):
        """Apply an AI-generated tag to its post (requires login).

        Parameters:
            media_asset_id (int): The media asset id.
            tag_id (int): The AI tag id.
            tag (str): Revert to this tag instead of the AI tag's own name.
            mode (str): ``remove`` to remove the tag instead of adding it.
        """
        data = {"tag": tag, "mode": mode}
        return self.request("PUT", "ai_tags/{0}/{1}/tag.json".format(media_asset_id, tag_id),
                            data=data)

    # ------------------------------------------------------------------
    # Uploads and upload media assets
    # ------------------------------------------------------------------

    def upload_list(self, search=None, **params):
        """Get a list of uploads (requires login for other users' uploads).

        Parameters:
            search (dict): ``id``, ``source``, ``referer_url``, ``status``,
                ``media_asset_count``, ``uploader_id``, ``uploader_name``,
                ``ai_tags_match``, ``min_score``, ``is_posted``,
                ``any_source_matches``, ``order``.
            user_id (int): Restrict to one uploader (top-level parameter).
            limit (int): Uploads per page.
            page (int): Page number.
        """
        return self.request("GET", "uploads.json", params=_search(search, params))

    def upload_show(self, upload_id):
        """Get a specific upload, including its media assets (requires login).

        Parameters:
            upload_id (int): The upload id.
        """
        return self.request("GET", "uploads/{0}.json".format(upload_id))

    def upload_create(self, files=None, source=None, referer_url=None):
        """Create an upload from files or a source URL (requires login).

        Source-aligned, untested. At least one of ``files`` or ``source`` is
        required by the server; archive files are expanded server-side. This is
        the only endpoint that sends a multipart body. The returned upload
        media assets are turned into posts with :meth:`post_create`.

        Parameters:
            files (list): Open file objects to upload, in order. The caller
                owns their lifetime (close them after the call).
            source (str): A source URL the server should download.
            referer_url (str): The referer of ``source``, for private sites.
        """
        upload_files = {"upload[files][{0}]".format(index): file
                        for index, file in enumerate(files or ())}
        data = {"upload": {"source": source, "referer_url": referer_url}}
        return self.request("POST", "uploads.json", data=data,
                            files=upload_files or None)

    def upload_assets_list(self, upload_id, search=None, **params):
        """Get the media assets of one upload.

        Parameters:
            upload_id (int): The upload id.
            search (dict): ``id``, ``status``, ``source_url``, ``page_url``,
                ``error``, ``media_asset_id``, ``post_id``, ``is_posted``,
                ``order``.
            limit (int): Assets per page (the server defaults to 200).
            page (int): Page number.
        """
        return self.request("GET", "uploads/{0}/assets.json".format(upload_id),
                            params=_search(search, params))

    def upload_media_assets_list(self, search=None, **params):
        """Get a list of upload media assets.

        Parameters:
            search (dict): ``id``, ``status``, ``source_url``, ``page_url``,
                ``error``, ``upload_id``, ``media_asset_id``, ``post_id``,
                ``is_posted``, ``order``.
            limit (int): Assets per page.
            page (int): Page number.
        """
        return self.request("GET", "upload_media_assets.json", params=_search(search, params))

    def upload_media_asset_show(self, upload_media_asset_id):
        """Get a specific upload media asset.

        Parameters:
            upload_media_asset_id (int): The upload media asset id.
        """
        return self.request("GET", "upload_media_assets/{0}.json".format(upload_media_asset_id))

    # ------------------------------------------------------------------
    # Tags, tag versions, aliases, implications, related tags, autocomplete
    # ------------------------------------------------------------------

    def tag_list(self, search=None, **params):
        """Get a list of tags.

        Parameters:
            search (dict): ``id``, ``name``, ``name_matches``,
                ``name_or_alias_matches``, ``name_normalize``,
                ``fuzzy_name_matches``, ``category``, ``is_deprecated``,
                ``post_count``, ``is_empty``, ``hide_empty``, ``has_wiki_page``,
                ``has_artist``, ``has_antecedent_alias``,
                ``has_consequent_aliases``, ``order`` (``name``, ``date``,
                ``count``, ``similarity``).
            limit (int): Tags per page (the server caps this at 1000).
            page (int): Page number.
        """
        return self.request("GET", "tags.json", params=_search(search, params))

    def tag_show(self, tag_id):
        """Get a specific tag.

        Parameters:
            tag_id (int): The tag id.
        """
        return self.request("GET", "tags/{0}.json".format(tag_id))

    def tag_update(self, tag_id, **attributes):
        """Update a tag (requires login; source-aligned, untested).

        Attributes:
            category (int): 0 general, 1 artist, 3 copyright, 4 character
                (Builder level and above).
            is_deprecated (bool): Whether the tag is deprecated (Builder level
                and above).
        """
        return self.request("PUT", "tags/{0}.json".format(tag_id),
                            data=_model("tag", attributes))

    def tag_versions_list(self, search=None, **params):
        """Get a list of tag versions.

        Parameters:
            search (dict): ``tag_id``, ``updater_id``, ``updater_name``,
                ``name_matches``, ``category``, ``is_deprecated``, ``version``,
                ``order`` (``created_at``, ``updated_at``, ``id`` and their
                ``_asc`` forms).
            limit (int): Versions per page.
            page (int): Page number.
        """
        return self.request("GET", "tag_versions.json", params=_search(search, params))

    def tag_version_show(self, version_id):
        """Get a specific tag version.

        Parameters:
            version_id (int): The tag version id.
        """
        return self.request("GET", "tag_versions/{0}.json".format(version_id))

    def tag_aliases_list(self, search=None, **params):
        """Get a list of tag aliases.

        Parameters:
            search (dict): ``id``, ``antecedent_name``, ``consequent_name``,
                ``name_matches``, ``antecedent_name_matches``,
                ``consequent_name_matches``, ``status`` (``active``,
                ``deleted``, ``retired``), ``category``, ``creator_id``,
                ``creator_name``, ``approver_id``, ``forum_topic_id``,
                ``order`` (``created_at``, ``updated_at``, ``name``,
                ``antecedent_tag_count``, ``consequent_tag_count``).
            limit (int): Aliases per page.
            page (int): Page number.
        """
        return self.request("GET", "tag_aliases.json", params=_search(search, params))

    def tag_alias_show(self, tag_alias_id):
        """Get a specific tag alias.

        Parameters:
            tag_alias_id (int): The tag alias id.
        """
        return self.request("GET", "tag_aliases/{0}.json".format(tag_alias_id))

    def tag_alias_delete(self, tag_alias_id):
        """Reject (delete) a tag alias (requires login; source-aligned, untested).

        Aliases are created through a bulk update request
        (:meth:`bulk_update_request_create`), not through this resource.

        Parameters:
            tag_alias_id (int): The tag alias id.
        """
        return self.request("DELETE", "tag_aliases/{0}.json".format(tag_alias_id))

    def tag_implications_list(self, search=None, **params):
        """Get a list of tag implications.

        Parameters:
            search (dict): ``id``, ``antecedent_name``, ``consequent_name``,
                ``name_matches``, ``antecedent_name_matches``,
                ``consequent_name_matches``, ``status``, ``category``,
                ``creator_id``, ``creator_name``, ``approver_id``,
                ``forum_topic_id``, ``implied_from``, ``implied_to``, ``order``.
            limit (int): Implications per page.
            page (int): Page number.
        """
        return self.request("GET", "tag_implications.json", params=_search(search, params))

    def tag_implication_show(self, tag_implication_id):
        """Get a specific tag implication.

        Parameters:
            tag_implication_id (int): The tag implication id.
        """
        return self.request("GET", "tag_implications/{0}.json".format(tag_implication_id))

    def tag_implication_delete(self, tag_implication_id):
        """Reject (delete) a tag implication (requires login; source-aligned, untested).

        Implications are created through a bulk update request
        (:meth:`bulk_update_request_create`), not through this resource.

        Parameters:
            tag_implication_id (int): The tag implication id.
        """
        return self.request("DELETE", "tag_implications/{0}.json".format(tag_implication_id))

    def related_tag(self, search=None, **params):
        """Get the tags related to a tag query.

        Parameters:
            search (dict): The search parameters, sent as ``search[...]``:
                ``query`` (required; a tag query such as ``"pixiv"`` or
                ``"pixiv rating:g"``), ``category`` or ``categories``
                (comma/space separated tag categories, e.g. ``"general"``),
                ``order`` (``frequency`` (default), ``cosine``, ``jaccard``,
                ``overlap``), ``search_sample_size`` (default 5000) and
                ``tag_sample_size`` (default 500).
            limit (int): How many related tags to return; the server clamps
                this to 0..1000 and defaults to 100 (top-level parameter).
            media_asset_id (int): Base the query on a media asset's AI tags
                instead of on ``query`` (top-level parameter).

        Returns:
            dict: ``{"query": ..., "post_count": ..., "tag": ...,
            "related_tags": [...], "wiki_page_tags": [...]}``.

        Example:
            >>> danbooru.related_tag({"query": "pixiv", "order": "cosine"})
        """
        return self.request("GET", "related_tag.json", params=_search(search, params))

    def autocomplete_list(self, query, type=None, limit=None):
        """Get autocomplete suggestions.

        Returns a list of suggestion strings.

        Parameters:
            query (str): The text to complete.
            type (str): ``tag`` (default), ``tag_query`` (search sample),
                ``artist``, ``wiki_page``, ``user``, ``pool``, ``comment`` or
                ``saved_search`` are accepted by the server.
            limit (int): Maximum number of suggestions (the server defaults to
                10, and caps `tag` suggestions itself).
        """
        params = {"search": {"query": query, "type": type}, "limit": limit}
        return self.request("GET", "autocomplete.json", params=params)

    # ------------------------------------------------------------------
    # Artists, artist URLs, artist versions, artist commentaries
    # ------------------------------------------------------------------

    def artist_list(self, search=None, **params):
        """Get a list of artists.

        Parameters:
            search (dict): ``id``, ``name`` (exact, or several comma-separated
                names), ``name_like``/``name_ilike``/``name_regex``,
                ``any_name_matches`` (name, other names or group, supporting
                ``*`` wildcards and ``/regex/``), ``any_name_or_url_matches``,
                ``any_other_name_like``, ``url_matches`` (a profile URL, a
                domain, ``*foo*`` or ``/regex/``; several values may be
                space-separated), ``group_name``, ``other_names_include_any``,
                ``is_deleted``, ``is_banned``, ``has_urls``, ``has_wiki_page``,
                ``has_tag_alias``, ``has_tag``, ``order`` (``name``,
                ``updated_at``, ``post_count``).
            name (str): Shorthand for ``search[name]`` (top-level parameter).
            limit (int): Artists per page.
            page (int): Page number.

        Example:
            >>> danbooru.artist_list(
            ...     search={"url_matches": "https://www.pixiv.net/users/27517"})
        """
        return self.request("GET", "artists.json", params=_search(search, params))

    def artist_show(self, artist_id):
        """Get a specific artist.

        Parameters:
            artist_id (int): The artist id.
        """
        return self.request("GET", "artists/{0}.json".format(artist_id))

    def artist_show_or_new(self, name=None):
        """Get the artist with this name, or an empty artist with that name.

        Parameters:
            name (str): The artist name; a blank name redirects to the new
                artist route, subject to that route's permissions.
        """
        return self.request("GET", "artists/show_or_new.json", params={"name": name})

    def artist_create(self, name, **attributes):
        """Create an artist (requires login; source-aligned, untested).

        Parameters:
            name (str): The artist's primary name (the future tag name).

        Attributes:
            other_names (list) or other_names_string (str): Alternative names.
            group_name (str): The group the artist belongs to.
            url_string (str): Whitespace-separated profile URLs.
            is_deleted (bool): Create the artist as deleted.
            source (str): A source URL used to prefill the artist's URLs.
        """
        return self.request("POST", "artists.json",
                            data=_model("artist", dict(attributes, name=name)))

    def artist_update(self, artist_id, **attributes):
        """Update an artist (requires login; source-aligned, untested).

        Attributes: see :meth:`artist_create`.
        """
        return self.request("PUT", "artists/{0}.json".format(artist_id),
                            data=_model("artist", attributes))

    def artist_delete(self, artist_id):
        """Delete an artist (requires builder level; sets ``is_deleted``).

        The controller redirects to the artist page. The client follows it
        with Accept: application/json and returns the final JSON response;
        a non-JSON final response raises PybooruAPIError. This write is untested.

        Parameters:
            artist_id (int): The artist id.
        """
        return self.request("DELETE", "artists/{0}.json".format(artist_id))

    def artist_revert(self, artist_id, version_id):
        """Revert an artist to a previous version (requires login).

        Parameters:
            artist_id (int): The artist id.
            version_id (int): The artist version id to revert to.
        """
        return self.request("PUT", "artists/{0}/revert.json".format(artist_id),
                            data={"version_id": version_id})

    def artist_ban(self, artist_id):
        """Ban an artist (requires admin level; source-aligned, untested).

        The controller redirects to the artist page. The client follows it
        with Accept: application/json; the final response determines the result.
        This write is source-aligned and untested.

        Parameters:
            artist_id (int): The artist id.
        """
        return self.request("PUT", "artists/{0}/ban.json".format(artist_id))

    def artist_unban(self, artist_id):
        """Unban an artist (requires admin level; source-aligned, untested).

        Like :meth:`artist_ban`, this follows the redirect to the artist page
        and returns its final response. This write is untested.

        Parameters:
            artist_id (int): The artist id.
        """
        return self.request("PUT", "artists/{0}/unban.json".format(artist_id))

    def artist_urls_list(self, search=None, **params):
        """Get a list of artist URLs.

        Parameters:
            search (dict): ``id``, ``artist_id``, ``url``,
                ``url_matches`` (same matching rules as artist search),
                ``is_active``, ``has_artist``, ``order`` (``id``,
                ``artist_id``, ``url``, ``is_active``, ``created_at``,
                ``updated_at`` and ``_asc``).
            limit (int): URLs per page.
            page (int): Page number.
        """
        return self.request("GET", "artist_urls.json", params=_search(search, params))

    def artist_versions_list(self, search=None, **params):
        """Get a list of artist versions.

        Parameters:
            search (dict): ``artist_id``, ``updater_id``, ``updater_name``,
                ``name``, ``group_name``, ``other_names_include_any``,
                ``is_deleted``, ``is_banned``, ``order`` (``id``,
                ``created_at``, ``updated_at``, ``name`` and ``_asc``).
            limit (int): Versions per page.
            page (int): Page number.
        """
        return self.request("GET", "artist_versions.json", params=_search(search, params))

    def artist_version_show(self, version_id):
        """Get a specific artist version.

        Parameters:
            version_id (int): The artist version id.
        """
        return self.request("GET", "artist_versions/{0}.json".format(version_id))

    def artist_commentaries_list(self, search=None, **params):
        """Get a list of artist commentaries.

        Parameters:
            search (dict): ``post_id``, ``original_title``,
                ``original_description``, ``translated_title``,
                ``translated_description``, ``text_matches``,
                ``original_present``, ``translated_present``, ``is_deleted``,
                ``order`` (``post_id``, ``updated_at``, ``id`` and ``_asc``).
            limit (int): Commentaries per page.
            page (int): Page number.
        """
        return self.request("GET", "artist_commentaries.json", params=_search(search, params))

    def artist_commentary_show(self, post_id):
        """Get the artist commentary of a post.

        Parameters:
            post_id (int): The post id.
        """
        return self.request("GET", "posts/{0}/artist_commentary.json".format(post_id))

    def artist_commentary_create_or_update(self, post_id, **attributes):
        """Create or update a post's artist commentary (requires login).

        Source-aligned, untested.

        Parameters:
            post_id (int): The post id (taken from the route).

        Attributes:
            original_title (str), original_description (str),
            translated_title (str), translated_description (str),
            commentary_tags (str).
        """
        return self.request("PUT",
                            "posts/{0}/artist_commentary/create_or_update.json".format(post_id),
                            data=_model("artist_commentary", attributes))

    def artist_commentary_revert(self, post_id, version_id):
        """Revert a post's artist commentary to a previous version.

        Requires login; source-aligned, untested. The route's id is the
        **post** id, not the commentary id.

        Parameters:
            post_id (int): The post id.
            version_id (int): The artist commentary version id to revert to.
        """
        return self.request("PUT", "artist_commentaries/{0}/revert.json".format(post_id),
                            data={"version_id": version_id})

    def artist_commentary_versions_list(self, search=None, **params):
        """Get a list of artist commentary versions.

        Parameters:
            search (dict): ``post_id``, ``updater_id``, ``updater_name``,
                ``text_matches``, ``original_title``, ``original_description``,
                ``translated_title``, ``translated_description``.
            limit (int): Versions per page.
            page (int): Page number.
        """
        return self.request("GET", "artist_commentary_versions.json",
                            params=_search(search, params))

    def artist_commentary_version_show(self, version_id):
        """Get a specific artist commentary version.

        Parameters:
            version_id (int): The artist commentary version id.
        """
        return self.request("GET", "artist_commentary_versions/{0}.json".format(version_id))

    # ------------------------------------------------------------------
    # Comments and comment votes
    # ------------------------------------------------------------------

    def comment_list(self, search=None, **params):
        """Get a list of comments.

        Parameters:
            search (dict): ``id``, ``body_matches``, ``post_id``,
                ``post_tags_match``, ``creator_id``, ``creator_name``,
                ``updater_id``, ``is_deleted``, ``is_sticky``,
                ``do_not_bump_post``, ``score``, ``is_edited``, ``order``.
            group_by (str): ``"comment"`` (default, newest comments) or
                ``"post"`` (newest commented posts).
            limit (int): Comments per page.
            page (int): Page number.
        """
        return self.request("GET", "comments.json", params=_search(search, params))

    def comment_show(self, comment_id):
        """Get a specific comment.

        Parameters:
            comment_id (int): The comment id.
        """
        return self.request("GET", "comments/{0}.json".format(comment_id))

    def comment_create(self, post_id, body, **attributes):
        """Create a comment (requires login).

        Parameters:
            post_id (int): The post to comment on.
            body (str): The comment body, in DText.

        Attributes:
            do_not_bump_post (bool): Do not bump the post to the top of the
                comment listing.
            is_sticky (bool): Pin the comment (requires moderator level).
        """
        return self.request("POST", "comments.json",
                            data=_model("comment", dict(attributes, post_id=post_id,
                                                        body=body)))

    def comment_update(self, comment_id, **attributes):
        """Update a comment (requires login; source-aligned, untested).

        Parameters:
            comment_id (int): The comment id.

        Attributes:
            body (str): The new body.
            is_deleted (bool): Whether the comment is deleted.
            is_sticky (bool): Pin the comment (requires moderator level).
        """
        return self.request("PUT", "comments/{0}.json".format(comment_id),
                            data=_model("comment", attributes))

    def comment_delete(self, comment_id):
        """Delete a comment (requires login; source-aligned, untested).

        Parameters:
            comment_id (int): The comment id.
        """
        return self.request("DELETE", "comments/{0}.json".format(comment_id))

    def comment_undelete(self, comment_id):
        """Undelete a comment (requires moderator level; source-aligned, untested).

        Parameters:
            comment_id (int): The comment id.
        """
        return self.request("POST", "comments/{0}/undelete.json".format(comment_id))

    def comment_votes_list(self, search=None, **params):
        """Get a list of comment votes.

        Parameters:
            search (dict): ``comment_id``, ``user_id``, ``user_name``,
                ``score``, ``is_deleted``.
            limit (int): Votes per page.
            page (int): Page number.
        """
        return self.request("GET", "comment_votes.json", params=_search(search, params))

    def comment_vote_show(self, vote_id):
        """Get a specific comment vote.

        Parameters:
            vote_id (int): The comment vote id.
        """
        return self.request("GET", "comment_votes/{0}.json".format(vote_id))

    def comment_vote_create(self, comment_id, score):
        """Vote on a comment (requires login).

        Parameters:
            comment_id (int): The comment id.
            score (str): ``up`` or ``down``.
        """
        return self.request("POST", "comments/{0}/votes.json".format(comment_id),
                            data={"score": score})

    def comment_vote_delete(self, vote_id):
        """Retract a comment vote (requires login).

        Danbooru has no route for retracting a vote by comment id; look the
        vote id up through :meth:`comment_votes_list`.

        Parameters:
            vote_id (int): The comment vote id.
        """
        return self.request("DELETE", "comment_votes/{0}.json".format(vote_id))

    # ------------------------------------------------------------------
    # Notes and note versions
    # ------------------------------------------------------------------

    def note_list(self, search=None, **params):
        """Get a list of notes.

        Parameters:
            search (dict): ``id``, ``post_id``, ``post_tags_match``,
                ``body_matches``, ``is_active``, ``x``, ``y``, ``width``,
                ``height``, ``version``.
            limit (int): Notes per page.
            page (int): Page number.
        """
        return self.request("GET", "notes.json", params=_search(search, params))

    def note_show(self, note_id):
        """Get a specific note.

        Parameters:
            note_id (int): The note id.
        """
        return self.request("GET", "notes/{0}.json".format(note_id))

    def note_create(self, post_id, x, y, width, height, body, **attributes):
        """Create a note (requires login; source-aligned, untested).

        Parameters:
            post_id (int): The post the note belongs to.
            x (int): Left offset in pixels.
            y (int): Top offset in pixels.
            width (int): Note width in pixels.
            height (int): Note height in pixels.
            body (str): The note body, in DText.

        Attributes:
            html_id (str): Client-side element id to correlate the response.
        """
        note = dict(attributes, post_id=post_id, x=x, y=y, width=width,
                    height=height, body=body)
        return self.request("POST", "notes.json", data=_model("note", note))

    def note_update(self, note_id, **attributes):
        """Update a note (requires login; source-aligned, untested).

        Parameters:
            note_id (int): The note id.

        Attributes:
            x (int), y (int), width (int), height (int), body (str).
        """
        return self.request("PUT", "notes/{0}.json".format(note_id),
                            data=_model("note", attributes))

    def note_delete(self, note_id):
        """Delete a note (requires login; source-aligned, untested).

        Parameters:
            note_id (int): The note id.
        """
        return self.request("DELETE", "notes/{0}.json".format(note_id))

    def note_revert(self, note_id, version_id):
        """Revert a note to a previous version (requires login).

        Parameters:
            note_id (int): The note id.
            version_id (int): The note version id to revert to.
        """
        return self.request("PUT", "notes/{0}/revert.json".format(note_id),
                            data={"version_id": version_id})

    def note_preview(self, body):
        """Render a note body to sanitized HTML.

        Parameters:
            body (str): The note body, in DText.
        """
        return self.request("POST", "notes/preview.json", data={"body": body})

    def note_versions_list(self, search=None, **params):
        """Get a list of note versions.

        Parameters:
            search (dict): ``note_id``, ``post_id``, ``updater_id``,
                ``is_active``, ``x``, ``y``, ``width``, ``height``, ``body``,
                ``version``.
            limit (int): Versions per page.
            page (int): Page number.
        """
        return self.request("GET", "note_versions.json", params=_search(search, params))

    def note_version_show(self, version_id):
        """Get a specific note version.

        Parameters:
            version_id (int): The note version id.
        """
        return self.request("GET", "note_versions/{0}.json".format(version_id))

    # ------------------------------------------------------------------
    # Pools, pool elements, pool versions
    # ------------------------------------------------------------------

    def pool_list(self, search=None, **params):
        """Get a list of pools.

        Parameters:
            search (dict): ``id``, ``name``, ``name_matches``, ``name_contains``,
                ``description_matches``, ``post_ids``, ``is_deleted``,
                ``category`` (``series`` or ``collection``),
                ``post_tags_match``, ``linked_to``, ``not_linked_to``,
                ``order`` (``name``, ``created_at``, ``post_count``).
            limit (int): Pools per page.
            page (int): Page number.
        """
        return self.request("GET", "pools.json", params=_search(search, params))

    def pool_show(self, pool_id):
        """Get a specific pool.

        Parameters:
            pool_id (int): The pool id.
        """
        return self.request("GET", "pools/{0}.json".format(pool_id))

    def pool_create(self, name, **attributes):
        """Create a pool (requires login; source-aligned, untested).

        Parameters:
            name (str): The pool name.

        Attributes:
            description (str): The pool description, in DText.
            category (str): ``series`` or ``collection``.
            post_ids_string (str): Space-separated initial post ids.
            post_ids (list): Initial post ids.
        """
        return self.request("POST", "pools.json",
                            data=_model("pool", dict(attributes, name=name)))

    def pool_update(self, pool_id, **attributes):
        """Update a pool (requires login; source-aligned, untested).

        Parameters:
            pool_id (int): The pool id.

        Attributes: see :meth:`pool_create`.
        """
        return self.request("PUT", "pools/{0}.json".format(pool_id),
                            data=_model("pool", attributes))

    def pool_delete(self, pool_id):
        """Delete a pool (requires login; sets ``is_deleted``).

        Parameters:
            pool_id (int): The pool id.
        """
        return self.request("DELETE", "pools/{0}.json".format(pool_id))

    def pool_undelete(self, pool_id):
        """Undelete a pool (requires moderator level; source-aligned, untested).

        Parameters:
            pool_id (int): The pool id.
        """
        return self.request("POST", "pools/{0}/undelete.json".format(pool_id))

    def pool_revert(self, pool_id, version_id):
        """Revert a pool to a previous version (requires login).

        Parameters:
            pool_id (int): The pool id.
            version_id (int): The pool version id to revert to.
        """
        return self.request("PUT", "pools/{0}/revert.json".format(pool_id),
                            data={"version_id": version_id})

    def pool_gallery(self, search=None, **params):
        """Get the pool gallery (pools with one post preview each).

        Parameters:
            search (dict): Search parameters; defaults to
                ``{"category": "series"}`` server-side.
            limit (int): Pools per page.
            page (int): Page number.
        """
        return self.request("GET", "pools/gallery.json", params=_search(search, params))

    def pool_element_create(self, post_id, pool_id=None, pool_name=None):
        """Add a post to a pool (requires login; source-aligned, untested).

        Parameters:
            post_id (int): The post to add.
            pool_id (int): The pool id (either this or ``pool_name``).
            pool_name (str): The pool name (either this or ``pool_id``).
        """
        data = {"post_id": post_id, "pool_id": pool_id, "pool_name": pool_name}
        return self.request("POST", "pool_element.json", data=data)

    def pool_versions_list(self, search=None, **params):
        """Get a list of pool versions (requires the archive service).

        Parameters:
            search (dict): ``pool_id``, ``post_id``, ``updater_id``,
                ``updater_name``, ``name_contains``, ``is_new``, ``version``,
                ``category``, ``is_active``, ``is_deleted``.
            limit (int): Versions per page.
            page (int): Page number.
        """
        return self.request("GET", "pool_versions.json", params=_search(search, params))

    def pool_version_diff(self, pool_version_id, other_id=None, type=None):
        """Diff a pool version against another version.

        Parameters:
            pool_version_id (int): The pool version id.
            other_id (int): The version to compare against; defaults to the
                previous/next version chosen by ``type``.
            type (str): ``"previous"`` or ``"next"``.
        """
        return self.request("GET", "pool_versions/{0}/diff.json".format(pool_version_id),
                            params={"other_id": other_id, "type": type})

    # ------------------------------------------------------------------
    # Wiki pages and wiki page versions
    # ------------------------------------------------------------------

    def wiki_page_list(self, search=None, **params):
        """Get a list of wiki pages.

        Parameters:
            search (dict): ``id``, ``title``, ``title_normalize``,
                ``title_or_body_matches``, ``body_matches``,
                ``other_names_match``, ``other_names_present``, ``is_locked``,
                ``is_deleted``, ``hide_deleted``, ``linked_to``,
                ``not_linked_to``, ``embedded_post_id``,
                ``embedded_media_asset_id``, ``has_embedded_media``,
                ``has_tag``, ``has_artist``, ``order`` (``title``,
                ``post_count``).
            title (str): Redirects to a title search (top-level parameter).
            limit (int): Pages per page.
            page (int): Page number.
        """
        return self.request("GET", "wiki_pages.json", params=_search(search, params))

    def wiki_page_show(self, id_or_title):
        """Get a wiki page by id or title.

        Parameters:
            id_or_title (int or str): A page id, or a page title such as
                ``"help:api"``; any character that is not URL-safe is escaped.
        """
        return self.request("GET", "wiki_pages/{0}.json".format(
            quote(str(id_or_title), safe="")))

    def wiki_page_create(self, title, **attributes):
        """Create a wiki page (requires login; source-aligned, untested).

        Parameters:
            title (str): The page title.

        Attributes:
            body (str): The page body, in DText.
            other_names (list) or other_names_string (str): Alternate titles.
            is_deleted (bool): Create the page as deleted (Builder level).
            is_locked (bool): Prevent edits (Builder level).
        """
        return self.request("POST", "wiki_pages.json",
                            data=_model("wiki_page", dict(attributes, title=title)))

    def wiki_page_update(self, wiki_page_id, **attributes):
        """Update a wiki page (requires login; source-aligned, untested).

        Parameters:
            wiki_page_id (int or str): The page id or title.

        Attributes: see :meth:`wiki_page_create`.
        """
        return self.request("PUT", "wiki_pages/{0}.json".format(
            quote(str(wiki_page_id), safe="")), data=_model("wiki_page", attributes))

    def wiki_page_delete(self, wiki_page_id):
        """Delete a wiki page (requires builder level; sets ``is_deleted``).

        Parameters:
            wiki_page_id (int or str): The page id or title.
        """
        return self.request("DELETE", "wiki_pages/{0}.json".format(
            quote(str(wiki_page_id), safe="")))

    def wiki_page_revert(self, wiki_page_id, version_id):
        """Revert a wiki page to a previous version (requires login).

        Parameters:
            wiki_page_id (int or str): The page id or title.
            version_id (int): The wiki page version id to revert to.
        """
        return self.request("PUT", "wiki_pages/{0}/revert.json".format(
            quote(str(wiki_page_id), safe="")), data={"version_id": version_id})

    def wiki_page_show_or_new(self, title=None):
        """Get the wiki page with this title, or the "new page" page.

        Parameters:
            title (str): The page title.
        """
        return self.request("GET", "wiki_pages/show_or_new.json", params={"title": title})

    def wiki_page_versions_list(self, search=None, **params):
        """Get a list of wiki page versions.

        Parameters:
            search (dict): ``wiki_page_id``, ``updater_id``,
                ``updater_name``, ``title``, ``title_like``, ``title_ilike``,
                ``title_regex``, ``body_matches``, ``other_names_include_any``,
                ``is_locked``, ``is_deleted``.
            limit (int): Versions per page.
            page (int): Page number.
        """
        return self.request("GET", "wiki_page_versions.json", params=_search(search, params))

    def wiki_page_version_show(self, version_id):
        """Get a specific wiki page version.

        Parameters:
            version_id (int): The wiki page version id.
        """
        return self.request("GET", "wiki_page_versions/{0}.json".format(version_id))

    def wiki_page_versions_diff(self, thispage=None, otherpage=None, type=None):
        """Diff two wiki page versions.

        Parameters:
            thispage (int): The first version id.
            otherpage (int): The second version id.
            type (str): ``"previous"`` or ``"next"`` when only one id is given.
        """
        return self.request("GET", "wiki_page_versions/diff.json",
                            params={"thispage": thispage, "otherpage": otherpage,
                                    "type": type})

    # ------------------------------------------------------------------
    # Users, favorites, favorite groups, user activity
    # ------------------------------------------------------------------

    def user_list(self, search=None, **params):
        """Get a list of users.

        Parameters:
            search (dict): ``id``, ``name_matches`` (also accepts ``name``),
                ``any_name_matches``, ``name_or_past_name_matches``, ``level``,
                ``min_level``, ``max_level``, ``is_banned``, ``has_posts``,
                ``has_comments``, ``order`` (``name``, ``post_upload_count``,
                ``note_count``, ``post_update_count``).
            name (str): Shorthand that searches current and past names
                (top-level parameter).
            limit (int): Users per page.
            page (int): Page number.
        """
        return self.request("GET", "users.json", params=_search(search, params))

    def user_show(self, user_id):
        """Get a specific user.

        Parameters:
            user_id (int): The user id.
        """
        return self.request("GET", "users/{0}.json".format(user_id))

    def user_create(self, name, password, password_confirmation):
        """Create a user account (source-aligned, untested).

        The server applies its own captcha and invite checks, so this may fail
        for sites that require them.

        Parameters:
            name (str): The user name.
            password (str): The password.
            password_confirmation (str): The password, repeated.
        """
        user = {"name": name, "password": password,
                "password_confirmation": password_confirmation}
        return self.request("POST", "users.json", data=_model("user", user))

    def user_update(self, user_id, **attributes):
        """Update a user's settings (requires login; only your own account).

        Source-aligned, untested.

        Attributes:
            comment_threshold (int), default_image_size (str),
            favorite_tags (str), blacklisted_tags (str), time_zone (str),
            per_page (int), custom_style (str), theme (str),
            receive_email_notifications (bool),
            new_post_navigation_layout (bool), enable_private_favorites (bool),
            show_deleted_posts (bool), show_deleted_children (bool),
            disable_categorized_saved_searches (bool),
            disable_tagged_filenames (bool), disable_mobile_gestures (bool),
            enable_safe_mode (bool), enable_desktop_mode (bool),
            disable_post_tooltips (bool).
        """
        return self.request("PUT", "users/{0}.json".format(user_id),
                            data=_model("user", attributes))

    def user_profile(self):
        """Get the logged-in user (requires login; same shape as user_show)."""
        return self.request("GET", "profile.json")

    def user_actions_list(self, search=None, **params):
        """Get a list of user actions (the activity feed; requires moderator
        level).

        Parameters:
            search (dict): ``user_id``, ``user_name``, ``event_type``,
                ``model_type``/``model_id``, ``order`` (``event_at_asc``; the
                default is newest first).
            user_id (int): Restrict to one user (top-level parameter).
            limit (int): Actions per page.
            page (int): Page number.
        """
        return self.request("GET", "user_actions.json", params=_search(search, params))

    def user_action_show(self, user_action_id):
        """Get a specific user action.

        Parameters:
            user_action_id (int): The user action id.
        """
        return self.request("GET", "user_actions/{0}.json".format(user_action_id))

    def user_events_list(self, search=None, **params):
        """Get a list of user events (logins, uploads, feedback, ...).

        Parameters:
            search (dict): ``id``, ``user_id``, ``user_name``, ``category``,
                ``ip_addr``, ``session_id``, ``user_agent``, ``metadata``.
            user_id (int): Restrict to one user (top-level parameter).
            limit (int): Events per page.
            page (int): Page number.
        """
        return self.request("GET", "user_events.json", params=_search(search, params))

    def user_feedbacks_list(self, search=None, **params):
        """Get a list of user feedbacks.

        Parameters:
            search (dict): ``id``, ``user_id``, ``user_name``, ``creator_id``,
                ``creator_name``, ``category``, ``body_matches``,
                ``is_deleted``, ``hide_bans``.
            limit (int): Feedbacks per page.
            page (int): Page number.
        """
        return self.request("GET", "user_feedbacks.json", params=_search(search, params))

    def user_feedback_show(self, feedback_id):
        """Get a specific user feedback.

        Parameters:
            feedback_id (int): The feedback id.
        """
        return self.request("GET", "user_feedbacks/{0}.json".format(feedback_id))

    def user_feedback_create(self, **attributes):
        """Create user feedback (requires login; source-aligned, untested).

        Attributes:
            body (str): The feedback text.
            category (str): ``positive`` or ``negative``.
            user_id (int) or user_name (str): The user the feedback is about.
        """
        return self.request("POST", "user_feedbacks.json",
                            data=_model("user_feedback", attributes))

    def user_feedback_update(self, feedback_id, **attributes):
        """Update user feedback (requires login; source-aligned, untested).

        Attributes:
            body (str), category (str), is_deleted (bool).
        """
        return self.request("PUT", "user_feedbacks/{0}.json".format(feedback_id),
                            data=_model("user_feedback", attributes))

    def user_name_change_requests_list(self, search=None, **params):
        """Get a list of user name change requests.

        Parameters:
            search (dict): ``id``, ``user_id``, ``user_name``,
                ``original_name``, ``desired_name``.
            limit (int): Requests per page.
            page (int): Page number.
        """
        return self.request("GET", "user_name_change_requests.json",
                            params=_search(search, params))

    def user_name_change_request_show(self, request_id):
        """Get a specific user name change request.

        Parameters:
            request_id (int): The request id.
        """
        return self.request("GET", "user_name_change_requests/{0}.json".format(request_id))

    def user_name_change_request_create(self, **attributes):
        """Create a user name change request (requires login; untested).

        Attributes:
            user_id (int): The user whose name should change.
            desired_name (str): The requested name.
        """
        return self.request("POST", "user_name_change_requests.json",
                            data=_model("user_name_change_request", attributes))

    def favorite_list(self, search=None, **params):
        """Get a list of favorites (requires login for other users' favorites).

        Parameters:
            search (dict): ``post_id``, ``user_id``, ``user_name``.
            post_id (int): Restrict to one post (top-level parameter).
            user_id (int): Which user's favorites to list, defaults to yours.
            limit (int): Favorites per page.
            page (int): Page number.
        """
        return self.request("GET", "favorites.json", params=_search(search, params))

    def favorite_create(self, post_id):
        """Add a post to your favorites (requires login).

        Parameters:
            post_id (int): The post to favorite (top-level).
        """
        return self.request("POST", "favorites.json", data={"post_id": post_id})

    def favorite_delete(self, post_id):
        """Remove a post from your favorites (requires login).

        Parameters:
            post_id (int): The post to unfavorite (the route id is the post id).
        """
        return self.request("DELETE", "favorites/{0}.json".format(post_id))

    def favorite_groups_list(self, search=None, **params):
        """Get a list of favorite groups.

        Parameters:
            search (dict): ``id``, ``name``, ``name_contains``, ``is_public``,
                ``post_ids``, ``creator_id``, ``creator_name``, ``order``
                (``name``, ``created_at``, ``updated_at``, ``post_count``).
            user_id (int): Restrict to one creator (top-level parameter).
            limit (int): Groups per page.
            page (int): Page number.
        """
        return self.request("GET", "favorite_groups.json", params=_search(search, params))

    def favorite_group_show(self, group_id):
        """Get a specific favorite group.

        Parameters:
            group_id (int): The favorite group id.
        """
        return self.request("GET", "favorite_groups/{0}.json".format(group_id))

    def favorite_group_create(self, name, **attributes):
        """Create a favorite group (requires login; source-aligned, untested).

        Parameters:
            name (str): The group name.

        Attributes:
            post_ids_string (str): Space-separated post ids.
            post_ids (list): Post ids.
            is_public (bool), is_private (bool).
        """
        return self.request("POST", "favorite_groups.json",
                            data=_model("favorite_group", dict(attributes, name=name)))

    def favorite_group_update(self, group_id, **attributes):
        """Update a favorite group (requires login; source-aligned, untested).

        Parameters:
            group_id (int): The favorite group id.

        Attributes: see :meth:`favorite_group_create`.
        """
        return self.request("PUT", "favorite_groups/{0}.json".format(group_id),
                            data=_model("favorite_group", attributes))

    def favorite_group_delete(self, group_id):
        """Delete a favorite group (requires login; source-aligned, untested).

        Parameters:
            group_id (int): The favorite group id.
        """
        return self.request("DELETE", "favorite_groups/{0}.json".format(group_id))

    def favorite_group_add_post(self, group_id, post_id):
        """Add a post to a favorite group (requires login).

        Parameters:
            group_id (int): The favorite group id.
            post_id (int): The post to add (top-level).
        """
        return self.request("PUT", "favorite_groups/{0}/add_post.json".format(group_id),
                            data={"post_id": post_id})

    def favorite_group_remove_post(self, group_id, post_id):
        """Remove a post from a favorite group (requires login).

        Parameters:
            group_id (int): The favorite group id.
            post_id (int): The post to remove (top-level).
        """
        return self.request("PUT", "favorite_groups/{0}/remove_post.json".format(group_id),
                            data={"post_id": post_id})

    # ------------------------------------------------------------------
    # Forum topics, forum posts, votes, visits
    # ------------------------------------------------------------------

    def forum_topics_list(self, search=None, **params):
        """Get a list of forum topics.

        Parameters:
            search (dict): ``id``, ``title``, ``title_matches``, ``category``
                or ``category_id`` (0 general, 1 tags, 2 bugs, 3 bulk update
                requests), ``min_level``, ``is_sticky``, ``is_locked``,
                ``is_deleted``, ``is_private``, ``is_read``, ``status``
                (``pending``, ``approved``, ``rejected``), ``creator_id``,
                ``creator_name``, ``order`` (``sticky``, ``id``).
            limit (int): Topics per page.
            page (int): Page number.
        """
        return self.request("GET", "forum_topics.json", params=_search(search, params))

    def forum_topic_show(self, topic_id):
        """Get a specific forum topic.

        Parameters:
            topic_id (int): The forum topic id.
        """
        return self.request("GET", "forum_topics/{0}.json".format(topic_id))

    def forum_topic_create(self, title, body, **attributes):
        """Create a forum topic (requires login; source-aligned, untested).

        Parameters:
            title (str): The topic title.
            body (str): The body of the topic's first post.

        Attributes:
            category_id (int): 0 general, 1 tags, 2 bugs and features,
                3 bulk update requests.
            min_level (int): Minimum level required to reply (Moderator+).
        """
        topic = dict(attributes, title=title,
                     original_post_attributes={"body": body})
        return self.request("POST", "forum_topics.json",
                            data=_model("forum_topic", topic))

    def forum_topic_update(self, topic_id, **attributes):
        """Update a forum topic (requires login; source-aligned, untested).

        Parameters:
            topic_id (int): The forum topic id.

        Attributes:
            title (str), category_id (int), is_sticky (bool) and is_locked
            (bool) (Moderator+), min_level (int) (Moderator+).
        """
        return self.request("PUT", "forum_topics/{0}.json".format(topic_id),
                            data=_model("forum_topic", attributes))

    def forum_topic_delete(self, topic_id):
        """Delete a forum topic (requires moderator level; untested).

        Parameters:
            topic_id (int): The forum topic id.
        """
        return self.request("DELETE", "forum_topics/{0}.json".format(topic_id))

    def forum_topic_undelete(self, topic_id):
        """Undelete a forum topic (requires moderator level; untested).

        Parameters:
            topic_id (int): The forum topic id.
        """
        return self.request("POST", "forum_topics/{0}/undelete.json".format(topic_id))

    def forum_topics_mark_all_as_read(self):
        """Mark every forum topic as read (requires login).

        The controller redirects to the topic list. The client follows it
        with Accept: application/json and returns the final JSON response;
        a non-JSON final response raises PybooruAPIError. This write is untested.
        """
        return self.request("POST", "forum_topics/mark_all_as_read.json")

    def forum_posts_list(self, search=None, **params):
        """Get a list of forum posts.

        Parameters:
            search (dict): ``id``, ``body_matches``, ``creator_id``,
                ``creator_name``, ``topic_id``, ``linked_to``, and nested
                topic filters such as ``{"topic": {"title_matches": ...}}`` or
                ``{"topic": {"category_id": 1}}``.
            limit (int): Posts per page.
            page (int): Page number.
        """
        return self.request("GET", "forum_posts.json", params=_search(search, params))

    def forum_post_show(self, post_id):
        """Get a specific forum post.

        Parameters:
            post_id (int): The forum post id.
        """
        return self.request("GET", "forum_posts/{0}.json".format(post_id))

    def forum_post_create(self, topic_id, body):
        """Create a forum post (requires login; source-aligned, untested).

        Parameters:
            topic_id (int): The topic to reply to.
            body (str): The post body, in DText.
        """
        return self.request("POST", "forum_posts.json",
                            data=_model("forum_post", {"topic_id": topic_id,
                                                       "body": body}))

    def forum_post_update(self, post_id, body):
        """Update a forum post (requires login; source-aligned, untested).

        Parameters:
            post_id (int): The forum post id.
            body (str): The new body.
        """
        return self.request("PUT", "forum_posts/{0}.json".format(post_id),
                            data=_model("forum_post", {"body": body}))

    def forum_post_delete(self, post_id):
        """Delete a forum post (requires moderator level; untested).

        Parameters:
            post_id (int): The forum post id.
        """
        return self.request("DELETE", "forum_posts/{0}.json".format(post_id))

    def forum_post_undelete(self, post_id):
        """Undelete a forum post (requires moderator level; untested).

        Parameters:
            post_id (int): The forum post id.
        """
        return self.request("POST", "forum_posts/{0}/undelete.json".format(post_id))

    def forum_post_votes_list(self, search=None, **params):
        """Get a list of forum post votes.

        Parameters:
            search (dict): ``forum_post_id``, ``creator_id``,
                ``creator_name``, ``score``.
            limit (int): Votes per page.
            page (int): Page number.
        """
        return self.request("GET", "forum_post_votes.json", params=_search(search, params))

    def forum_post_vote_show(self, vote_id):
        """Get a specific forum post vote.

        Parameters:
            vote_id (int): The forum post vote id.
        """
        return self.request("GET", "forum_post_votes/{0}.json".format(vote_id))

    def forum_post_vote_create(self, forum_post_id, score):
        """Vote on a forum post (requires login; source-aligned, untested).

        Parameters:
            forum_post_id (int): The forum post id (top-level).
            score (str): ``up`` or ``down``.
        """
        return self.request("POST", "forum_post_votes.json",
                            data=dict(_model("forum_post_vote", {"score": score}),
                                      forum_post_id=forum_post_id))

    def forum_post_vote_delete(self, vote_id):
        """Delete a forum post vote (requires login; untested).

        Parameters:
            vote_id (int): The forum post vote id.
        """
        return self.request("DELETE", "forum_post_votes/{0}.json".format(vote_id))

    def forum_topic_visits_list(self, search=None, **params):
        """Get a list of forum topic visits (requires login).

        Parameters:
            search (dict): ``user_id``, ``forum_topic_id``, ``last_read_at``.
            limit (int): Visits per page.
            page (int): Page number.
        """
        return self.request("GET", "forum_topic_visits.json", params=_search(search, params))

    # ------------------------------------------------------------------
    # Dmails
    # ------------------------------------------------------------------

    def dmail_list(self, search=None, **params):
        """Get a list of dmails (requires login; only your own are visible).

        Parameters:
            search (dict): ``id``, ``title``, ``body``, ``message_matches``,
                ``folder`` (``received``/``sent``/``all``), ``is_read``,
                ``is_deleted``, ``to_id``, ``to_name``, ``from_id``,
                ``from_name``.
            limit (int): Dmails per page.
            page (int): Page number.
        """
        return self.request("GET", "dmails.json", params=_search(search, params))

    def dmail_show(self, dmail_id):
        """Get a specific dmail (requires login; only your own).

        Parameters:
            dmail_id (int): The dmail id.
        """
        return self.request("GET", "dmails/{0}.json".format(dmail_id))

    def dmail_create(self, title, body, to_name=None, to_id=None):
        """Send a dmail (requires login; source-aligned, untested).

        Parameters:
            title (str): The message title.
            body (str): The message body, in DText.
            to_name (str) or to_id (int): The recipient.
        """
        return self.request("POST", "dmails.json",
                            data=_model("dmail", {"title": title, "body": body,
                                                  "to_name": to_name, "to_id": to_id}))

    def dmail_update(self, dmail_id, **attributes):
        """Update a dmail (requires login; source-aligned, untested).

        Danbooru has no destroy route for dmails; deleting means
        ``dmail_update(dmail_id, is_deleted=True)``.

        Parameters:
            dmail_id (int): The dmail id.

        Attributes:
            is_read (bool), is_deleted (bool).
        """
        return self.request("PUT", "dmails/{0}.json".format(dmail_id),
                            data=_model("dmail", attributes))

    def dmails_mark_all_as_read(self):
        """Mark every dmail as read (requires login)."""
        return self.request("POST", "dmails/mark_all_as_read.json")

    # ------------------------------------------------------------------
    # Bans, bulk update requests, IP data
    # ------------------------------------------------------------------

    def ban_list(self, search=None, **params):
        """Get a list of bans.

        Parameters:
            search (dict): ``id``, ``user_id``, ``user_name``, ``banner_id``,
                ``banner_name``, ``reason_matches``, ``duration``,
                ``expired``, ``order`` (``expires_at_desc``).
            limit (int): Bans per page.
            page (int): Page number.
        """
        return self.request("GET", "bans.json", params=_search(search, params))

    def ban_show(self, ban_id):
        """Get a specific ban.

        Parameters:
            ban_id (int): The ban id.
        """
        return self.request("GET", "bans/{0}.json".format(ban_id))

    def ban_create(self, **attributes):
        """Ban a user (requires moderator level; source-aligned, untested).

        Attributes:
            user_id (int) or user_name (str): The user to ban.
            reason (str): The ban reason.
            duration (str): A duration such as ``"1 week"``; blank is permanent.
            delete_posts (bool), post_deletion_reason (str),
            delete_comments (bool), delete_forum_posts (bool),
            delete_post_votes (bool), delete_comment_votes (bool).
        """
        return self.request("POST", "bans.json", data=_model("ban", attributes))

    def ban_update(self, ban_id, **attributes):
        """Update a ban (requires moderator level; source-aligned, untested).

        Attributes: reason (str), duration (str).
        """
        return self.request("PUT", "bans/{0}.json".format(ban_id),
                            data=_model("ban", attributes))

    def ban_delete(self, ban_id):
        """Delete (unban) a ban (requires moderator level; untested).

        Parameters:
            ban_id (int): The ban id.
        """
        return self.request("DELETE", "bans/{0}.json".format(ban_id))

    def bulk_update_requests_list(self, search=None, **params):
        """Get a list of bulk update requests.

        Parameters:
            search (dict): ``id``, ``script_matches``, ``title_matches``,
                ``user_id``, ``user_name``, ``approver_id``, ``approver_name``,
                ``forum_topic_id``, ``status`` (``pending``, ``approved``,
                ``rejected`` or a comma-separated list), ``tags``,
                ``can_approve``, ``score``, ``order`` (``id``, ``updated_at``,
                ``score`` and ``_asc``).
            limit (int): Requests per page.
            page (int): Page number.
        """
        return self.request("GET", "bulk_update_requests.json", params=_search(search, params))

    def bulk_update_request_show(self, request_id):
        """Get a specific bulk update request.

        Parameters:
            request_id (int): The bulk update request id.
        """
        return self.request("GET", "bulk_update_requests/{0}.json".format(request_id))

    def bulk_update_request_create(self, script, **attributes):
        """Create a bulk update request (requires login; untested).

        This is the current way to request tag aliases (``alias a -> b``),
        implications (``imply a -> b``) and mass tag edits.

        Parameters:
            script (str): The BUR script, for example ``"alias foo -> bar"``.

        Attributes:
            title (str): An optional title.
            reason (str): An optional reason.
            forum_topic_id (int): Post the request to an existing forum topic.
        """
        return self.request("POST", "bulk_update_requests.json",
                            data=_model("bulk_update_request", dict(attributes,
                                                                    script=script)))

    def bulk_update_request_update(self, request_id, **attributes):
        """Update a bulk update request (requires login; untested).

        Attributes:
            script (str), forum_topic_id (int), forum_post_id (int) (the last
            two require the ability to update the topic).
        """
        return self.request("PUT", "bulk_update_requests/{0}.json".format(request_id),
                            data=_model("bulk_update_request", attributes))

    def bulk_update_request_approve(self, request_id):
        """Approve a bulk update request (requires approver level; untested).

        Parameters:
            request_id (int): The bulk update request id.
        """
        return self.request("POST",
                            "bulk_update_requests/{0}/approve.json".format(request_id))

    def bulk_update_request_delete(self, request_id):
        """Reject a bulk update request (requires login; untested).

        Parameters:
            request_id (int): The bulk update request id.
        """
        return self.request("DELETE", "bulk_update_requests/{0}.json".format(request_id))

    def ip_bans_list(self, search=None, **params):
        """Get a list of IP bans.

        Parameters:
            search (dict): ``id``, ``ip_addr``, ``reason_matches``,
                ``category``, ``is_deleted``, ``hit_count``, ``last_hit_at``,
                ``creator_id``, ``creator_name``, ``order`` (``created_at``,
                ``updated_at``, ``last_hit_at`` and ``_asc``).
            limit (int): Bans per page.
            page (int): Page number.
        """
        return self.request("GET", "ip_bans.json", params=_search(search, params))

    def ip_ban_show(self, ip_ban_id):
        """Get a specific IP ban.

        Parameters:
            ip_ban_id (int): The IP ban id.
        """
        return self.request("GET", "ip_bans/{0}.json".format(ip_ban_id))

    def ip_ban_create(self, **attributes):
        """Create an IP ban (requires moderator level; untested).

        Attributes:
            ip_addr (str): The IP address or range.
            reason (str): The ban reason.
            category (str): ``warning`` or ``block``.
            is_deleted (bool).
        """
        return self.request("POST", "ip_bans.json", data=_model("ip_ban", attributes))

    def ip_ban_update(self, ip_ban_id, **attributes):
        """Update an IP ban (requires moderator level; untested).

        Attributes: see :meth:`ip_ban_create`.
        """
        return self.request("PUT", "ip_bans/{0}.json".format(ip_ban_id),
                            data=_model("ip_ban", attributes))

    def ip_address_show(self, ip_addr):
        """Get information about an IP address (requires moderator level).

        Parameters:
            ip_addr (str): The IP address, for example ``"1.2.3.4"``.
        """
        return self.request("GET", "ip_addresses/{0}.json".format(ip_addr))

    def ip_geolocations_list(self, search=None, **params):
        """Get a list of IP geolocations (requires moderator level).

        Parameters:
            search (dict): ``ip_addr``, ``network``, ``country``, ``region``,
                ``city``, ``asn``, ``is_proxy``.
            limit (int): Records per page.
            page (int): Page number.
        """
        return self.request("GET", "ip_geolocations.json", params=_search(search, params))

    # ------------------------------------------------------------------
    # Moderation, news, reports, jobs, site data
    # ------------------------------------------------------------------

    def mod_actions_list(self, search=None, **params):
        """Get a list of mod actions.

        Listing is not restricted; moderator-only categories are filtered out
        of the results for other users.

        Parameters:
            search (dict): ``id``, ``category``, ``description_matches``,
                ``creator_id``, ``creator_name``, ``subject_type``,
                ``subject_id``, ``order`` (``created_at_asc``).
            limit (int): Actions per page.
            page (int): Page number.
        """
        return self.request("GET", "mod_actions.json", params=_search(search, params))

    def mod_action_show(self, mod_action_id):
        """Get a specific mod action (requires janitor level).

        Parameters:
            mod_action_id (int): The mod action id.
        """
        return self.request("GET", "mod_actions/{0}.json".format(mod_action_id))

    def modqueue_list(self, search=None, **params):
        """Get the moderation queue (requires approver level)."""
        return self.request("GET", "modqueue.json", params=_search(search, params))

    def moderation_reports_list(self, search=None, **params):
        """Get a list of moderation reports (requires moderator level).

        Parameters:
            search (dict): ``model_type``, ``model_id``, ``creator_id``,
                ``creator_name``, ``reason_matches``, ``status``,
                ``recipient_id``, ``recipient_name``.
            limit (int): Reports per page.
            page (int): Page number.
        """
        return self.request("GET", "moderation_reports.json", params=_search(search, params))

    def moderation_report_show(self, report_id):
        """Get a specific moderation report (requires moderator level).

        Parameters:
            report_id (int): The moderation report id.
        """
        return self.request("GET", "moderation_reports/{0}.json".format(report_id))

    def moderation_report_create(self, **attributes):
        """Report a post, comment or user (requires login; untested).

        Attributes:
            model_type (str): ``Post``, ``Comment`` or ``User``.
            model_id (int): The id of the reported record.
            reason (str): The reason for the report.
        """
        return self.request("POST", "moderation_reports.json",
                            data=_model("moderation_report", attributes))

    def moderation_report_update(self, report_id, **attributes):
        """Update a moderation report (requires moderator level; untested).

        Attributes: status (str).
        """
        return self.request("PUT", "moderation_reports/{0}.json".format(report_id),
                            data=_model("moderation_report", attributes))

    def news_updates_list(self, search=None, **params):
        """Get a list of news updates.

        Parameters:
            search (dict): ``message_matches``, ``creator_id``, ``creator_name``,
                ``is_deleted``, ``order`` (``created_at_asc``).
            limit (int): Updates per page.
            page (int): Page number.
        """
        return self.request("GET", "news_updates.json", params=_search(search, params))

    def news_update_show(self, news_update_id):
        """Get a specific news update.

        Parameters:
            news_update_id (int): The news update id.
        """
        return self.request("GET", "news_updates/{0}.json".format(news_update_id))

    def news_update_create(self, message, **attributes):
        """Create a news update (requires admin level; untested).

        Parameters:
            message (str): The banner text, in DText.

        Attributes:
            duration (str) or duration_in_days (int): How long to display it.
            is_deleted (bool).
        """
        return self.request("POST", "news_updates.json",
                            data=_model("news_update", dict(attributes, message=message)))

    def news_update_update(self, news_update_id, **attributes):
        """Update a news update (requires admin level; untested).

        Attributes: see :meth:`news_update_create`.
        """
        return self.request("PUT", "news_updates/{0}.json".format(news_update_id),
                            data=_model("news_update", attributes))

    def news_update_delete(self, news_update_id):
        """Delete a news update (requires admin level; untested).

        Parameters:
            news_update_id (int): The news update id.
        """
        return self.request("DELETE", "news_updates/{0}.json".format(news_update_id))

    def saved_searches_list(self, search=None, **params):
        """Get a list of saved searches (requires login).

        Parameters:
            search (dict): ``query_matches``, ``label``, ``disable_labels``,
                ``order`` (``query``, ``label``).
            limit (int): Saved searches per page.
            page (int): Page number.
        """
        return self.request("GET", "saved_searches.json", params=_search(search, params))

    def saved_search_create(self, **attributes):
        """Create a saved search (requires login; untested).

        Attributes:
            query (str): The tag query.
            label_string (str): A display label.
            disable_labels (bool): Hide the search's labels.
        """
        return self.request("POST", "saved_searches.json",
                            data=_model("saved_search", attributes))

    def saved_search_update(self, saved_search_id, **attributes):
        """Update a saved search (requires login; untested).

        Attributes: see :meth:`saved_search_create`.
        """
        return self.request("PUT", "saved_searches/{0}.json".format(saved_search_id),
                            data=_model("saved_search", attributes))

    def saved_search_delete(self, saved_search_id):
        """Delete a saved search (requires login; untested).

        Parameters:
            saved_search_id (int): The saved search id.
        """
        return self.request("DELETE", "saved_searches/{0}.json".format(saved_search_id))

    def site_credentials_list(self, search=None, **params):
        """Get a list of site credentials (requires admin level).

        Parameters:
            search (dict): ``site``, ``is_enabled``, ``is_public``, ``status``,
                ``creator_id``, ``updater_id``, ``order``.
            limit (int): Credentials per page.
            page (int): Page number.
        """
        return self.request("GET", "site_credentials.json", params=_search(search, params))

    def site_credential_show(self, site_credential_id):
        """Get a specific site credential (requires admin level).

        Parameters:
            site_credential_id (int): The site credential id.
        """
        return self.request("GET", "site_credentials/{0}.json".format(site_credential_id))

    def site_credential_create(self, site, **attributes):
        """Create a site credential (requires admin level; untested).

        Parameters:
            site (str): The site name, e.g. ``"pixiv"``.

        Attributes:
            is_enabled (bool).
            credential (dict): Keys are site specific, e.g. ``login`` and
                ``password``.
        """
        return self.request("POST", "site_credentials.json",
                            data=_model("site_credential", dict(attributes, site=site)))

    def site_credential_update(self, site_credential_id, **attributes):
        """Update a site credential (requires admin level; untested).

        Attributes: is_enabled (bool).
        """
        return self.request("PUT", "site_credentials/{0}.json".format(site_credential_id),
                            data=_model("site_credential", attributes))

    def site_credential_delete(self, site_credential_id):
        """Delete a site credential (requires admin level; untested).

        Parameters:
            site_credential_id (int): The site credential id.
        """
        return self.request("DELETE", "site_credentials/{0}.json".format(site_credential_id))

    def reactions_list(self, search=None, **params):
        """Get a list of reactions.

        Parameters:
            search (dict): ``model_type``, ``model_id``, ``creator_id``,
                ``reaction_id``.
            limit (int): Reactions per page.
            page (int): Page number.
        """
        return self.request("GET", "reactions.json", params=_search(search, params))

    def reaction_show(self, reaction_id):
        """Get a specific reaction.

        Parameters:
            reaction_id (int): The reaction id.
        """
        return self.request("GET", "reactions/{0}.json".format(reaction_id))

    def reaction_create(self, **attributes):
        """React to a post, comment or forum post (requires login; untested).

        Attributes:
            model_type (str): ``Post``, ``Comment`` or ``ForumPost``.
            model_id (int): The id of the record to react to.
            reaction_id (str): The emoji, e.g. ``"heart"``.
        """
        return self.request("POST", "reactions.json", data=_model("reaction", attributes))

    def reaction_delete(self, reaction_id):
        """Delete a reaction (requires login; untested).

        Parameters:
            reaction_id (int): The reaction id.
        """
        return self.request("DELETE", "reactions/{0}.json".format(reaction_id))

    def report_show(self, report, search=None, **params):
        """Get a statistics report.

        Parameters:
            report (str): One of ``posts``, ``post_approvals``,
                ``post_appeals``, ``post_flags``, ``post_replacements``,
                ``post_votes``, ``media_assets``, ``pools``, ``comments``,
                ``comment_votes``, ``forum_posts``, ``bulk_update_requests``,
                ``tag_aliases``, ``tag_implications``, ``artist_versions``,
                ``artist_commentary_versions``, ``note_versions``,
                ``wiki_page_versions``, ``mod_actions``, ``bans``, ``users``.
            search (dict): ``period``, ``from``, ``to``, ``columns``,
                ``group``, ``group_limit``, ``mode`` and the model's own
                search parameters.
        """
        return self.request("GET", "reports/{0}.json".format(report),
                            params=_search(search, params))

    def jobs_list(self, search=None, **params):
        """Get a list of background jobs.

        Reading the queue is not restricted; `serialized_params` is only
        returned to admins.

        Parameters:
            search (dict): ``id``, ``active_job_id``, ``job_class``,
                ``queue_name``, ``labels``, ``priority``, ``status``,
                ``name`` (job class, matched fuzzily).
            limit (int): Jobs per page.
            page (int): Page number.
        """
        return self.request("GET", "jobs.json", params=_search(search, params))

    def job_cancel(self, job_id):
        """Cancel a background job (requires janitor level; untested).

        Parameters:
            job_id (str): The job's ActiveJob id.
        """
        return self.request("PUT", "jobs/{0}/cancel.json".format(job_id))

    def job_retry(self, job_id):
        """Retry a background job (requires janitor level; untested).

        Parameters:
            job_id (str): The job's ActiveJob id.
        """
        return self.request("PUT", "jobs/{0}/retry.json".format(job_id))

    def job_run(self, job_id):
        """Run a background job now (requires janitor level; untested).

        Parameters:
            job_id (str): The job's ActiveJob id.
        """
        return self.request("PUT", "jobs/{0}/run.json".format(job_id))

    def job_delete(self, job_id):
        """Delete a background job (requires janitor level; untested).

        Parameters:
            job_id (str): The job's ActiveJob id.
        """
        return self.request("DELETE", "jobs/{0}.json".format(job_id))

    def dtext_links_list(self, search=None, **params):
        """Get a list of DText links.

        Parameters:
            search (dict): ``link_type``, ``link_target``, ``model_type``,
                ``model_id``, ``linked_wiki_id``, ``linked_tag_id``.
            limit (int): Links per page.
            page (int): Page number.
        """
        return self.request("GET", "dtext_links.json", params=_search(search, params))

    def recommended_posts_list(self, search=None, **params):
        """Get recommended posts.

        Parameters:
            search (dict): Search parameters forwarded to the recommender,
                typically ``{"user_id": ...}`` or ``{"post_id": ...}``.
            limit (int): Posts to return (the server caps this at 200).
        """
        return self.request("GET", "recommended_posts.json", params=_search(search, params))

    def counts_posts(self, tags=None, estimate_count=None, skip_cache=None):
        """Count the posts matching a tag query.

        Returns a mapping shaped ``{"counts": {"posts": <int>}}``.

        Parameters:
            tags (str): The tag query; empty counts all posts.
            estimate_count (bool): Use a fast estimate instead of an exact
                count (the server default).
            skip_cache (bool): Bypass the count cache.
        """
        params = {"tags": tags, "estimate_count": estimate_count,
                  "skip_cache": skip_cache}
        return self.request("GET", "counts/posts.json", params=params)

    # ------------------------------------------------------------------
    # Sources and IQDB
    # ------------------------------------------------------------------

    def source_show(self, url, ref=None, mode=None):
        """Extract the source data of an artist or image URL.

        Parameters:
            url (str): The URL to inspect, e.g. a Pixiv artist page.
            ref (str): A referer URL, for sites that need one.
            mode (str): ``"card"`` (default) or ``"post"`` for the display mode.
        """
        return self.request("GET", "source.json",
                            params={"url": url, "ref": ref, "mode": mode})

    def iqdb_query(self, **params):
        """Search IQDB for similar posts.

        Parameters:
            url, file_url, image_url (str): The image to search for.
            hash (str): A precomputed image hash.
            post_id (int): Search for a post's own image.
            media_asset_id (int): Search for a media asset's image.
            limit (int): Matches to return (the server caps this at 1000).
        """
        return self.request("GET", "iqdb_queries.json", params=params)
