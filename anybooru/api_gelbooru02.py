"""Gelbooru 0.2 read methods supported by TBIB evidence.

The site identifies itself as "Running Gelbooru 0.2". Its own help at
https://tbib.org/index.php?page=help&topic=dapi documents post, deleted-post
and comment routes; the tag route is confirmed by anonymous responses.
There is no service-source snapshot or finer patch-version evidence.

Posts support JSON, but tags and comments return XML even with json=1.
XML stays response text: callers may parse it with the standard library.
No method unwraps the response, changes field names or builds media URLs.
"""


class Gelbooru02Api_Mixin:
    """Four read methods; account routes and autocomplete are not wrapped."""

    def post_list(self, *, response_format="json", **params):
        """Read posts, or select one by id, as JSON or unchanged XML text.

        Parameters accepted by the site's help:
            limit: Requested number of posts. Help says hard limit 100,
                but limit=101 returned 101. Actual upper bound unconfirmed.
            pid: Page number; XML reports the resulting offset separately.
            tags: Website search string, e.g. 'rating:safe'.
            cid: Change ID in Unix time; not exercised.
            id: Post ID, not a separate show route.

        JSON is an array of post objects with id, directory, image, hash,
        width, height, change, owner, parent_id, rating, sample,
        sample_width, sample_height, score and tags. Unlike the XML form,
        it has no file_url/sample_url/preview_url or root count/offset.
        XML preserves these attributes as text. Ratings differ by format:
        the observed JSON 'safe' is XML 's'; the client does not convert.
        """
        return self.request("dapi", params=dict(params, s="post", q="index"),
                            response_format=response_format)

    def post_deleted(self, **params):
        """Read the help-documented deleted stream as unchanged XML text.

        last_id selects records above that number according to help.
        limit is not documented for this stream. TBIB returned HTTP 500
        and incomplete XML for last_id=0, limit=1, with or without json=1;
        this method preserves the HTTP error rather than repairing it.
        s=deleted is a different, observed empty-body route and is not used.
        """
        return self.request("dapi", params=dict(
            params, s="post", q="index", deleted="show"))

    def tag_list(self, **params):
        """Read unchanged XML text rooted at tags, with child tag elements.

        limit=1 returned one tag. Observed child attributes are id, name,
        count, type and ambiguous; all remain XML text. The site's help
        does not document tag filtering, ordering or maximum page size.
        json=1 does not change this endpoint to JSON.
        """
        return self.request("dapi", params=dict(params, s="tag", q="index"))

    def comment_list(self, post_id, **params):
        """Read unchanged XML text for the help-documented post_id query.

        The help describes post_id ambiguously as a comment ID. The only
        observed sample post_id=1 returned <comments type="array"/>;
        nonempty comment fields and identifier semantics remain unverified.
        json=1 still returns XML. No comment-child schema is invented.
        """
        return self.request("dapi", params=dict(
            params, post_id=post_id, s="comment", q="index"))
