# -*- coding: utf-8 -*-

"""Native JSON methods for Gelbooru (gelbooru.com).

Gelbooru has no resource paths and no API version: everything is dispatched
by one script, ``https://gelbooru.com/index.php?page=<page>``, and the
official API adds ``s`` (resource) and ``q`` (action). The methods here
differ only in the ``page`` / ``s`` / ``q`` values they set, so the whole
surface is six calls:

    * ``page=dapi&s=post&q=index`` -- posts (``post_list``)
    * ``page=dapi&s=post&q=index&deleted=show`` -- deleted posts
      (``post_deleted``)
    * ``page=dapi&s=tag&q=index`` -- tags (``tag_list``)
    * ``page=dapi&s=user&q=index`` -- users (``user_list``)
    * ``page=dapi&s=comment&q=index`` -- comments (``comment_list``)
    * ``page=autocomplete2`` -- suggestions (``autocomplete``)

Credentials:
    Anonymous requests through all five dapi methods returned 401 with an
    empty body. Account access uses the ``api_key`` and ``user_id`` shown
    under "API Access Credentials" on ``index.php?page=account&s=options``.
    Authenticated success responses have not been observed.
    ``autocomplete2`` is an anonymous JSON route.
    ``user_id`` is the numeric account id, not the user name.

Formats:
    dapi answers XML by default and JSON only when ``json=1`` is present;
    ``Gelbooru.request`` adds ``json=1`` to every dapi call, so these
    methods always ask for JSON. The XML form is not implemented. Nothing
    is unwrapped, renamed or reduced: the JSON body is returned exactly as
    it arrived, top-level metadata included.

Response shape:
    The field names and nesting of dapi JSON have not been observed with an
    account, and the official page documents the parameters rather than the
    payload, so no field list is asserted here and the client does not
    guess one. A single post is read with ``post_list(id=<id>)``; there is
    no ``post_show`` because the API has no separate show action. On error
    the old help page describes a success value of false and a message,
    without specifying their JSON representation. HTTP failures keep their
    status and body.

Scope:
    Only the resources the official API page lists are wrapped: post (with
    the deleted-post audit stream under it), tag, user and comment. The
    ``artist`` / ``pool`` / ``wiki`` dapi resources that community clients
    use are absent from that page, so there are no methods for them; they
    can still be attempted through ``request('dapi', params={...})``. The
    HTML pages (``page=tags``, ``page=wiki``, ``page=post``, ...) are the
    site's own browser routes, not the API, and are deliberately not
    wrapped or scraped.

Doc: https://gelbooru.com/index.php?page=wiki&s=view&id=18780
"""

# __future__ imports
from __future__ import absolute_import


class GelbooruApi_Mixin(object):
    """Native Gelbooru API calls.

    * Doc: https://gelbooru.com/index.php?page=wiki&s=view&id=18780
    """

    # ------------------------------------------------------------------
    # Official API (page=dapi, account required)
    # ------------------------------------------------------------------

    def post_list(self, **params):
        """Get a list of posts, or one post when ``id`` is given.

        Parameters:
            limit (int): Posts per request. The API page describes a default
                of 100; the older help page describes a hard limit of 100.
                Those are two different claims and neither has been checked.
            pid (int): Page number, starting at 0.
            tags (str): The site's own search string, the same one the
                search box takes: ``'1girl solo'`` requires both tags,
                ``'-rating:explicit'`` excludes a rating, ``'score:>=10'``
                and ``'width:>=1000'`` compare numbers, ``'id:1'``,
                ``'md5:<hash>'``, ``'user:<name>'``, ``'pool:<id>'``,
                ``'source:ab*'`` and ``'sort:random'`` all work here.
            cid (int): Unix timestamp used to filter by change id.
            id (int): A post id. This is the way to read one post: the API
                has no separate show action, so ``post_list(id=1)`` is the
                single-post call.

        Returns the JSON body as sent. The post payload's field names are
        not documented by the API page and have not been observed with an
        account, so no field is renamed, dropped or filled in.
        """
        return self.request("dapi", params=dict(params, s="post", q="index"))

    def post_deleted(self, **params):
        """Get the deleted-post audit stream.

        The same post index with ``deleted=show``; the page lists it
        separately and gives it ``last_id`` instead of ``pid``.

        Parameters:
            last_id (int): Return records whose id is greater than this
                value; the page does not say what happens when it is
                omitted.
            limit (int): Sent if supplied; the deleted-images section does
                not document support or a default for this parameter.
        """
        return self.request("dapi", params=dict(
            params, s="post", q="index", deleted="show"))

    def tag_list(self, **params):
        """Get a list of tags.

        Parameters:
            id (int): One tag by its library id.
            name (str): One tag by exact name.
            names (str): Several tag names in one space-separated string,
                e.g. ``'schoolgirl moon cat'``.
            name_pattern (str): LIKE pattern, where ``_`` matches one
                character and ``%`` matches any run, e.g.
                ``'%choolgirl%'``.
            after_id (int): Tags whose id is greater than this value, for
                reading the list in order.
            limit (int): Tags per request; the page describes a default of
                100.
            orderby (str): ``date``, ``count`` or ``name``.
            order (str): ``ASC`` or ``DESC``.

        Returns the JSON body as sent; the tag payload's field names have
        not been observed with an account.
        """
        return self.request("dapi", params=dict(params, s="tag", q="index"))

    def user_list(self, **params):
        """Get a list of users.

        Parameters:
            name (str): One user name.
            name_pattern (str): Wildcard match on the user name.
            limit (int): Users per request; the page describes a default of
                100.
            pid (int): Page number, starting at 0.

        Returns the JSON body as sent; the user payload's field names have
        not been observed with an account.
        """
        return self.request("dapi", params=dict(params, s="user", q="index"))

    def comment_list(self, post_id, **params):
        """Get the comments of one post.

        Parameters:
            post_id (int): The supplied reference interprets this as the
                post id. The wiki instead says "comment" id; this wording
                conflict is recorded in the contract notes. Required here.

        Returns the JSON body as sent; the comment payload's field names
        have not been observed with an account.
        """
        return self.request("dapi", params=dict(
            params, post_id=post_id, s="comment", q="index"))

    # ------------------------------------------------------------------
    # In-site JSON (no account)
    # ------------------------------------------------------------------

    def autocomplete(self, term, **params):
        """Get autocomplete suggestions for a partial term.

        Parameters:
            term (str): What the user has typed so far; the supplied
                reference uses underscores, e.g. ``'hatsune_miku'``.
            type (str): The site script binds ``tag``, ``tag_query``,
                ``artist``, ``pool``, ``user``, ``wiki_page``,
                ``favorite_group``, ``saved_search_label`` and ``mention``.
                Calls with all nine values returned tag suggestions when
                nonempty; misspelled ``taq`` and unlisted ``wiki`` did too.
            limit (int): Requested suggestion count; the site script sends
                10. The observed ``limit=3`` request still returned 10.

        Returns a JSON array. Observed tag suggestions carry ``type``,
        ``label`` (display form), ``value`` (the form to search with),
        ``post_count`` (a string) and ``category``. The site script also
        reads ``name`` / ``level`` and ``antecedent`` in other rendering
        branches, but no such fields were observed, including requests
        with ``type='user'``. The array is returned unchanged.
        """
        return self.request("autocomplete2", params=dict(params, term=term))
