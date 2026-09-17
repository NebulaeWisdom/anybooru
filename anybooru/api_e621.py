# -*- coding: utf-8 -*-

"""Native read-only JSON methods for e621ng (e621.net and e926.net).

Methods are thin calls to E621.request(), following the upstream routes,
controllers and model searches. Search dictionaries use search[...]; posts
use top-level tags. Parameters are never filtered, clamped or defaulted here.

Post methods select the legacy posts/post envelope from the request's
md5/only/v2 parameters, matching PostsController and JsonResponseHelper.
No response-shape guessing or field flattening is performed. Other methods
preserve the JSON body, including comments grouped by post. Counting uses
/posts/count.json, not Danbooru's /counts/posts.json.

Authentication belongs to E621; related_tag and related_tag_bulk require
member access and their authenticated success paths have not been exercised.
Full source references, search fields and visibility constraints are in
docs/e621-contract-notes.md. Upstream: https://github.com/e621ng/e621ng.
"""

# __future__ imports
from __future__ import absolute_import

# Standard library imports
from urllib.parse import quote


def _segment(value):
    """Escape one raw path segment (id, tag or artist name, page title)."""
    return quote(str(value), safe="")


def _search(search, params):
    """Merge a full search-parameter dictionary into top-level parameters."""
    if search is None:
        return params
    return dict(params, search=search)


def _present(value):
    """Report whether Rails would see this parameter value as present.

    ``present?`` is the negation of ``blank?``: nil, an empty or
    whitespace-only string, an empty collection and ``false`` are blank.
    Parameter values reach the server as strings, so a boolean is present.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True


def _unwrapped(params):
    """Report whether PostsController renders this call without a wrapper.

    ``render_json_with_wrapper`` renders the bare body when ``only`` is
    present, and ``pick_json_format`` renders it bare when ``v2`` is the
    string ``"true"`` (it compares the raw parameter, so the value a boolean
    becomes in the query string is what matters).
    """
    if _present(params.get("only")):
        return True
    v2 = params.get("v2")
    if isinstance(v2, bool):
        v2 = str(v2).lower()
    return v2 == "true"


def _md5_lookup(params):
    """Report whether posts#index takes its single-post md5 branch.

    The controller drops any non-string ``md5`` and branches on ``present?``,
    so only a non-blank string selects the single post.
    """
    md5 = params.get("md5")
    return isinstance(md5, str) and md5.strip() != ""


class E621Api_Mixin(object):
    """Native e621ng API calls.

    * Source: https://github.com/e621ng/e621ng (config/routes.rb)
    * Doc: https://e621.net/help/api
    """

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def post_list(self, **params):
        """Get a list of posts, or one post when ``md5`` is given.

        Parameters:
            tags (str): The tag/metatag query ("rating:s", "wolf order:score").
            limit (int): Posts per page.
            page (int): Page number; an "a<id>"/"b<id>" cursor works too.
            md5 (str): A 32 character MD5; the response holds that one post.
            v2 (bool or str): ``"true"`` switches to the new post blueprint,
                which the controller renders without the ``posts`` wrapper.
            mode (str): New-blueprint view: ``"basic"``, ``"extended"`` or
                ``"thumbnail"``.
            only (str): Any present value suppresses the wrapper.
            random (bool): Read by ``PostSets::Post`` as its own random state;
                the shuffled order itself comes from an ``order:random``
                metatag inside ``tags``.
            post (dict): Nested ``post[tags]``, used when ``tags`` is absent.

        Returns the ``posts`` list, or the single post when ``md5`` is a
        non-empty string; a call that asks for an unwrapped body (``only``,
        ``v2="true"``) returns that body as-is. The nested post schema is
        passed through untouched.
        """
        if _unwrapped(params):
            envelope = None
        else:
            envelope = "post" if _md5_lookup(params) else "posts"
        return self.request("GET", "posts", params=params, envelope=envelope)

    def post_show(self, post_id, **params):
        """Get a single post.

        Parameters:
            post_id (int): The post id.
            v2 (bool or str): ``"true"`` returns the new post blueprint.
            mode (str): New-blueprint view: ``"basic"``, ``"extended"`` or
                ``"thumbnail"``.
            only (str): Any present value suppresses the wrapper.
            post_set_id (int): Post set to report inside the body.
            pool_id (int): Pool to report inside the body.
        """
        envelope = None if _unwrapped(params) else "post"
        return self.request("GET", "posts/{0}".format(_segment(post_id)),
                            params=params, envelope=envelope)

    def post_random(self, **params):
        """Get one random post matching the query.

        The controller resolves the query with ``order:random`` and answers
        404 when nothing matches.

        Parameters:
            tags (str): The tag/metatag query.
            v2 (bool or str), mode (str), only (str): as in :meth:`post_show`.
        """
        envelope = None if _unwrapped(params) else "post"
        return self.request("GET", "posts/random", params=params,
                            envelope=envelope)

    def post_count(self, **params):
        """Count the posts matching a query.

        Parameters:
            tags (str): The tag/metatag query.
            post (dict): Nested ``post[tags]``, used when ``tags`` is absent.

        Returns ``{"count": N, "capped": bool}``; ``capped`` reports that the
        search stopped at the engine's page ceiling, so ``count`` is a floor.
        """
        return self.request("GET", "posts/count", params=params)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag_list(self, search=None, **params):
        """Get a list of tags.

        Parameters:
            search (dict): ``name``, ``name_matches``, ``fuzzy_name_matches``,
                ``category`` (0 general, 1 artist, 2 contributor, 3 copyright,
                4 character, 5 species, 6 invalid, 7 meta, 8 lore),
                ``hide_empty``, ``has_wiki``, ``has_artist``, ``is_locked``,
                ``order`` (``name``/``similarity``/``id_asc``/``id_desc``/
                ``date``; otherwise descending post_count).
            limit (int): Tags per page.
            page (int): Page number.
        """
        return self.request("GET", "tags", params=_search(search, params))

    def tag_show(self, tag_id, **params):
        """Get one tag by id or name.

        Parameters:
            tag_id (int or str): A numeric id, or the tag name (for example
                ``"wolf"``); anything not URL-safe is escaped.
        """
        return self.request("GET", "tags/{0}".format(_segment(tag_id)),
                            params=params)

    # ------------------------------------------------------------------
    # Artists
    # ------------------------------------------------------------------

    def artist_list(self, search=None, **params):
        """Get a list of artists.

        Parameters:
            search (dict): ``name``, ``group_name``, ``any_name_matches``,
                ``any_name_or_url_matches``, ``any_other_name_like``,
                ``any_other_name_matches``, ``url_matches``, ``creator_name``,
                ``creator_id``, ``linked_user_id``, ``linked_user_name``,
                ``is_linked``, ``has_tag``, ``order``
                (``name``/``updated_at``/``post_count``).
            name (str): A single name; the controller folds it into
                ``search[name]``.
            limit (int): Artists per page.
            page (int): Page number.
            expiry (int): Days the response may be cached.

        Each artist carries its ``urls`` array. Result counting for pagination
        is enabled by the server only for searches that narrow the result.
        """
        return self.request("GET", "artists", params=_search(search, params))

    def artist_show(self, artist_id, **params):
        """Get one artist by id or name.

        Parameters:
            artist_id (int or str): A numeric id or the artist name; an
                unknown name is a 404 for JSON requests.
        """
        return self.request("GET", "artists/{0}".format(_segment(artist_id)),
                            params=params)

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def comment_list(self, search=None, **params):
        """Get a list of comments.

        Parameters:
            search (dict): ``id``, ``body_matches``, ``post_id``,
                ``creator_name``, ``creator_id``, ``poster_name``,
                ``poster_id``, ``post_note_updater_name``,
                ``post_note_updater_id``, ``is_sticky``, ``do_not_bump_post``,
                ``order``, ``advanced_search``; members may also use
                ``post_tags_match``, staff ``is_hidden`` and admins
                ``ip_addr``.
            group_by (str): ``"post"`` returns bare Post model objects, not
                CommentBlueprint objects or the posts API's legacy schema.
                Comments themselves are not included in that JSON branch.
                Any other value keeps the comment list.
            tags (str): Top-level tag query for ``group_by="post"``.
            limit (int): Comments per page; the per-post view paginates five
                posts per page.
            page (int): Page number.

        The server excludes inaccessible comments. A separate score threshold
        applies unless an ``id`` search filter is given.
        """
        return self.request("GET", "comments", params=_search(search, params))

    def comment_show(self, comment_id, **params):
        """Get one comment.

        Parameters:
            comment_id (int): The comment id.
        """
        return self.request("GET", "comments/{0}".format(_segment(comment_id)),
                            params=params)

    # ------------------------------------------------------------------
    # Pools
    # ------------------------------------------------------------------

    def pool_list(self, search=None, **params):
        """Get a list of pools.

        Parameters:
            search (dict): ``name_matches``, ``description_matches``,
                ``creator_id``, ``creator_name``, ``is_active``, ``category``
                (``series``/``collection``), ``order``
                (``name``/``created_at``/``post_count``).
            limit (int): Pools per page.
            page (int): Page number.
            expiry (int): Days the response may be cached.
        """
        return self.request("GET", "pools", params=_search(search, params))

    def pool_show(self, pool_id, **params):
        """Get one pool, including its ``post_ids`` array.

        Parameters:
            pool_id (int): The pool id.
            page (int), limit (int): Accepted; they only paginate the HTML view.
        """
        return self.request("GET", "pools/{0}".format(_segment(pool_id)),
                            params=params)

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    def note_list(self, search=None, **params):
        """Get a list of notes.

        Parameters:
            search (dict): ``id``, ``body_matches``, ``is_active``,
                ``post_id``, ``creator_id``, ``creator_name``,
                ``post_note_updater_id``, ``post_note_updater_name``,
                ``order``; members may also use ``post_tags_match``.
            limit (int): Notes per page.
            page (int): Page number.
        """
        return self.request("GET", "notes", params=_search(search, params))

    def note_show(self, note_id, **params):
        """Get one note.

        Parameters:
            note_id (int): The note id.
        """
        return self.request("GET", "notes/{0}".format(_segment(note_id)),
                            params=params)

    # ------------------------------------------------------------------
    # Wiki pages
    # ------------------------------------------------------------------

    def wiki_page_list(self, search=None, **params):
        """Get a list of wiki pages.

        Parameters:
            search (dict): ``id``, ``title``, ``body_matches``,
                ``other_names_match``, ``other_names_present``, ``is_locked``,
                ``is_deleted``, ``hide_deleted``, ``parent``, ``creator_id``,
                ``creator_name``, ``order`` (``title``/``post_count``).
            title (str): The exact page title; the controller folds it into
                ``search[title]``.
            limit (int): Pages per page.
            page (int): Page number.
            expiry (int): Days the response may be cached.
        """
        return self.request("GET", "wiki_pages", params=_search(search, params))

    def wiki_page_show(self, title_or_id, **params):
        """Get one wiki page by id or title.

        Parameters:
            title_or_id (int or str): A page id, or a title such as
                ``"help:api"``; anything not URL-safe is escaped (the route
                accepts any segment without a slash).
        """
        return self.request("GET", "wiki_pages/{0}".format(_segment(title_or_id)),
                            params=params)

    # ------------------------------------------------------------------
    # Related tags
    # ------------------------------------------------------------------

    def related_tag(self, search=None, **params):
        """Get the tags related to a query (member level; 403 anonymously).

        Parameters:
            search (dict): ``query`` (a tag name, or a ``*`` wildcard query)
                and ``category_id`` (narrow the calculation to one tag
                category).
            limit (int): Accepted by the route; the controller always returns
                its own result set.

        Returns ``[{"name": ..., "category_id": ...}]``. A wildcard query
        instead returns the first 50 tags matching the pattern by name.
        """
        return self.request("GET", "related_tag", params=_search(search, params))

    def related_tag_bulk(self, query, category_id=None):
        """Get related tags for each of up to 25 queried tag names.

        Parameters:
            query (str): Whitespace separated tag names.
            category_id (int): Narrow the calculation to one tag category.

        Returns ``{tag_name: [{"name": ..., "count": ..., "category_id":
        ...}]}``, or ``{}`` when the query is blank. Member level; anonymous
        requests get HTTP 403.
        """
        return self.request("GET", "related_tag/bulk",
                            params={"query": query, "category_id": category_id})
