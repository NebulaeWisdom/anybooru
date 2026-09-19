"""Native JSON methods for Anime-Pictures (api.anime-pictures.net/api/v3).

Anime-Pictures is a site of its own rather than one of the booru engines this
package ships for, so the paths, envelopes and error codes are this site's
own. This family has weak evidence: the site's API manual page exists but
answers a Cloudflare challenge and cannot be read from a command line, there
is no OpenAPI document and no server source. The routes here come from
anonymous read responses observed on the API host on the day recorded in
docs/verification.md and, where noted, from a supplied client reference
whose field lists disagree with the sample in places. The field lists below
are candidate shapes of those samples, not a schema this project verified,
and keys may be missing or change.

Shared observed facts:
    * Base URL: ``https://api.anime-pictures.net/api/v3``. The web host
      ``anime-pictures.net`` answers a Cloudflare challenge and reaches the
      same routes only through a ``302`` to the API host, which this client
      does not rely on.
    * The API host's JSON routes are ``GET``. Two of them need rights and
      were called anonymously here: ``posts/{id}/tags`` answered 403 with an
      error object, and the host-root image entry answered 403 with an empty
      body. This project sent no write request; the supplied reference
      reports ``POST posts`` answering 401 anonymously with an error object.
    * The route prefix belongs to the base URL here, so the method paths are
      relative (``posts``). A caller may still pass an absolute host path
      such as ``/api/v3/posts`` or ``/``: see ``AnimePictures.request`` for
      how a leading slash is treated, which differs from the other families.
    * Errors are JSON of the form ``{"errormsg", "success": false}``. An
      unknown post answered 410 while an unknown tag, user and comment
      answered 404; an unknown route answered 404 with an empty body. A path
      segment that is not an integer answered 400 with a plain-text body:
      that body is not JSON and reaches the caller as the shared HTTP error
      with an unparsed body, not as a decoded object.
    * ``score`` is not always ``0.0``: the reverse-date sample carried
      ``score`` 73.0 with ``score_number`` 70, and the rating sample 1446.0
      with 629. Both fields are returned as received and neither is derived
      locally. The sampled ``ext`` carried a leading dot (``'.png'``).
    * ``max_pages`` was 0 for an empty result (a tag no post carries), so the
      ``ceil(posts_count / posts_per_page) - 1`` formula a supplied reference
      gives does not hold everywhere; the field is returned as received and
      never recomputed.
    * Sample values drift: the ``tag_ru`` of the sampled tag differs in case
      from the value the supplied reference shows, and counts such as
      ``score_number`` and ``download_count`` moved between visits, so no
      number here is a contract.
    * Nothing is unwrapped, renamed, defaulted, clamped, retried or paged
      locally: the JSON body is returned exactly as received. Identifiers are
      percent-encoded as single path segments with no safe characters.

Which calls have actually been made against the live site is recorded in
docs/verification.md.

Classes:
    AnimePicturesApi_Mixin -- Anime-Pictures post, tag, user and comment
        reads plus the submit method. The bytes-returning ``image_get`` is
        defined on ``AnimePictures`` because it does not answer JSON.
"""

# Standard library imports
from urllib.parse import quote


class AnimePicturesApi_Mixin:
    """Anime-Pictures JSON methods, each a thin ``AnimePictures.request()``."""

    # ------------------------------------------------------------------
    # Service
    # ------------------------------------------------------------------

    def service_info(self):
        """Read the API host root (``GET https://api.anime-pictures.net/``).

        Observed body: ``{"message": "Hello, World!"}``. The path is the host
        root, not the ``/api/v3`` prefix.
        """
        return self.request("GET", "/")

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def posts_list(self, **params):
        """List posts (``GET posts``).

        Observed envelope: ``posts`` (the post objects), ``posts_per_page``
        (the page size the server used), ``response_posts_count`` (objects in
        this response), ``page_number`` (the requested page echoed back),
        ``posts_count`` (total posts under the current filter) and
        ``max_pages`` (the site's last page number, 0 when the filter matched
        nothing).

        Observed post object keys: ``id``, ``md5``, ``md5_pixels``,
        ``juser_id``, ``width``, ``height``, ``pubtime``, ``datetime``,
        ``score``, ``score_number``, ``size``, ``download_count``,
        ``erotics``, ``color`` (an RGB array in the sample), ``ext``,
        ``status``, ``status_type``, ``spoiler``, ``have_alpha``,
        ``tags_count``, ``artefacts_degree`` and ``smooth_degree``. This
        route gave no preview URL; ``post_show`` did. ``status_type`` was
        present in the sample and is not guaranteed.

        Parameters are forwarded unchanged and none is interpreted here:
        ``page``, ``posts_per_page``, ``search_tag``, ``denied_tags``,
        ``order_by``, ``ldate``, ``aspect``, ``color``, ``ext_jpg``,
        ``ext_png``, ``ext_gif``, ``user``, ``stars_by`` and ``lang``. No
        value is filled in, validated, clamped or dropped. Observed on this
        route, one sample per value rather than an enumeration: a missing or
        non-integer ``page`` answered 400, ``page=-1`` answered 500, and a
        page past the end answered 200 with an empty ``posts``;
        ``posts_per_page`` defaulted to 80, echoed 1, 2, 3 and 100, fell back
        to 60 for 101, 150, 1000 and 0 and to 80 for -1, so the echoed value
        is the page size the site chose and not a promise of how many objects
        come back; ``order_by`` values ``date``, ``date_r``, ``rating``,
        ``views``, ``size``, ``tag_num`` and ``id`` each answered an order
        consistent with that field, while ``random`` answered the ``date``
        ids; and ``search_tag`` reached the site with its spaces as ``+``.
        The bounds and the way the values combine were not enumerated.
        """
        return self.request("GET", "posts", params=params)

    def post_show(self, post_id, **params):
        """Read one post (``GET posts/{post_id}``).

        The identifier is encoded as one path segment and sent unvalidated,
        so a non-numeric value reaches the site and its own error is kept.

        Observed body on post 929452: the top-level keys ``post``,
        ``source``, ``user``, ``moderator``, ``tags``, ``file_url``,
        ``star_it``, ``favorites_users`` and ``tied``, where ``source``
        carries ``kind``, ``url`` and ``verification``. That set is not
        fixed: the older post 382872 answered the same route without
        ``source``, so a key present in one response can be missing in
        another. The sampled ``post`` object repeated the list fields and
        added the preview URLs ``small_preview``, ``medium_preview`` and
        ``big_preview``; each ``tags`` entry carries ``tag``, ``user`` and
        ``relation``. The top-level ``user`` carried ``login``, which the
        single-user object of ``user_show`` did not, so the two user shapes
        are not interchangeable.

        ``file_url`` is a file name, not a URL -- the sample held spaces --
        and it is what ``image_get`` takes. An unknown post id answered 410
        rather than 404.
        """
        return self.request("GET", "posts/{}".format(quote(str(post_id), safe="")),
                            params=params)

    def post_comments(self, post_id, **params):
        """Read one post's comments (``GET posts/{post_id}/comments``).

        Observed body: ``{"success": true, "comments": [...]}`` where each
        entry is ``{"comment": {...}, "user": {...}}`` and the comment object
        carries ``id``, ``datetime``, ``language``, ``text`` and ``html``.

        The sample carried no offset, limit or count field, and this project
        did not establish that paging parameters do anything here, so no
        default is added: ``params`` is forwarded unchanged.
        """
        return self.request(
            "GET", "posts/{}/comments".format(quote(str(post_id), safe="")),
            params=params)

    def post_tags(self, post_id, **params):
        """Read one post's tags (``GET posts/{post_id}/tags``).

        This route needs rights: the sampled anonymous call answered 403
        ``{"errormsg": "You not have rights", "success": false}``, so the
        successful body is unobserved. The client adds no credential of its
        own here; configure one if you have it and the outcome is unverified.
        """
        return self.request(
            "GET", "posts/{}/tags".format(quote(str(post_id), safe="")),
            params=params)

    def post_create(self, data, *, idempotency_key=None):
        """Submit a post (``POST posts``).

        ``data`` is the JSON request body and is sent exactly as given,
        ``None`` values included: no field is named, added, renamed or
        removed here, because the accepted body is unknown. It has to be a
        mapping the caller assembled.

        ``idempotency_key`` becomes the ``Idempotency-Key`` request header
        when it is not ``None``. The supplied reference reports the write
        route's CORS preflight accepting an ``authorization`` and an
        ``idempotency-key`` request header, and reports the anonymous write
        answering 401 ``{"errormsg": "You have no rights", "success":
        false}``; this project re-observed neither and has sent no write
        request, so no accepted header value, body or response of this route
        was observed.
        """
        headers = None
        if idempotency_key is not None:
            headers = {"Idempotency-Key": idempotency_key}
        return self.request("POST", "posts", data=data, headers=headers)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tags_list(self, **params):
        """List tags (``GET tags``).

        Observed envelope: ``success``, ``offset``, ``limit``, ``count`` and
        ``tags``. An observed tag object carried ``id``, ``tag``, ``tag_ru``,
        ``tag_jp``, ``num``, ``num_pub``, ``type``, ``description_en``,
        ``description_ru``, ``description_jp``, ``alias``, ``parent`` and
        ``views``. ``type`` was an integer with no name in the response, so
        this client does not map it.

        In the samples ``tag=hatsune miku`` answered a single exact match
        while ``tag=hatsune`` (a partial name) answered none, and
        ``search=hatsune`` answered the same first rows and ``count`` as no
        filter at all. The list defaulted to ``offset`` 0 and ``limit`` 20,
        ``offset=2`` skipped the first two rows, ``limit=1000`` answered 100,
        and ``type`` filtered to one integer class per value with 0..7
        answering rows and 8 answering none. No value is treated specially
        here: every parameter is forwarded unchanged, so an unmatched name is
        still sent.
        """
        return self.request("GET", "tags", params=params)

    def tag_show(self, tag_id, **params):
        """Read one tag (``GET tags/{tag_id}``).

        Observed body: ``{"success": true, "tag": {...}}`` with the tag
        object of ``tags_list``. An unknown tag id answered 404.
        """
        return self.request("GET", "tags/{}".format(quote(str(tag_id), safe="")),
                            params=params)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def users_list(self, **params):
        """List users (``GET users``).

        Observed envelope: ``success``, ``offset``, ``limit``, ``count`` and
        ``users``. In the sample ``limit`` and ``offset`` were echoed back
        and ``count`` (225284) was far larger than the two users returned, so
        it is not the size of the page. The list defaulted to ``offset`` 0
        and ``limit`` 20, ``offset=2`` skipped the first two rows, and
        ``limit=101`` answered 100 users. The list entry carried ``login``,
        which the single-user object of ``user_show`` did not.
        """
        return self.request("GET", "users", params=params)

    def user_show(self, user_id, **params):
        """Read one user (``GET users/{user_id}``).

        Observed body: ``success``, ``user`` and ``errormsg``, with
        ``errormsg`` null on success in the sample; the supplied reference
        omits that key, and the sample is what callers of this method see.
        The single-user ``user`` object carried ``id``, ``name``,
        ``avatar_version``, ``isavatar``, ``site_score``, ``groups``,
        ``gender`` and ``register_date``. It did not carry ``login`` in the
        sample, while the user-list entries and the nested ``user`` of
        ``post_show`` did, so the two shapes are not interchangeable. It
        carried no avatar URL, so no avatar address is built here or anywhere
        else in this family. An unknown user id answered 404.
        """
        return self.request("GET", "users/{}".format(quote(str(user_id), safe="")),
                            params=params)

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def comments_list(self, **params):
        """List comments site-wide (``GET comments``).

        Observed envelope: ``success``, ``offset``, ``limit``, ``count`` and
        ``comments``, each entry ``{"comment": {...}, "user": {...},
        "post": {...}}``. Inside this envelope the sampled ``post`` object
        carried no preview URL, unlike the ``post`` of ``post_show``. The
        list defaulted to ``offset`` 0 and ``limit`` 20, ``offset=2`` skipped
        the first two rows and ``limit=101`` answered 100 comments.
        """
        return self.request("GET", "comments", params=params)

    def comment_show(self, comment_id, **params):
        """Read one comment (``GET comments/{comment_id}``).

        Observed body: ``success``, ``comment`` and ``user``, the comment
        object being the one ``comments_list`` nests. The supplied reference
        does not list the top-level ``user`` key, and the sample is what this
        client returns. An unknown comment id answered 404.
        """
        return self.request(
            "GET", "comments/{}".format(quote(str(comment_id), safe="")),
            params=params)
