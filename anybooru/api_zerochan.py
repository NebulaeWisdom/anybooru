# -*- coding: utf-8 -*-

"""Native read-only JSON methods for Zerochan.

No Zerochan engine source is available for this implementation, so the
contract is the API page (https://www.zerochan.net/api), read through its
2024 archived snapshot (https://web.archive.org/web/2024/https://www.zerochan.net/api),
together with the responses actually observed from it. Every method is a
thin ``Zerochan.request()`` call based on those two sources.
Provenance, exclusions and the questions left open are collected in
docs/zerochan-contract-notes.md.

URL grammar, all ``GET``:
    * ``/?json`` -- every entry.
    * ``/<Tag>?json`` -- filtered by one tag. The page documents this
      endpoint as not available for meta tags.
    * ``/<Tag>?json&strict`` -- strict mode, that is, entries whose primary
      tag is the tag being matched.
    * ``/<TagA>,<TagB>?json`` -- filtered by several tags.
    * ``/<id>?json`` -- detailed information about one entry.

Envelopes:
    * Observed list responses contain ``{"items": [...]}`` without paging
      metadata; only ``items`` is unwrapped.
    * The detail endpoint answers the entry object itself, so it is returned
      unchanged.

Documented query parameters (all optional): ``p`` page, ``l`` limit with a
documented range of 1-250, ``s`` sort (``id`` recency or ``fav``
popularity), ``t`` the popularity window (``0`` all time, ``1`` the last
7000 entries, ``2`` the last 15000 entries), ``d`` picture dimension
(``large``, ``huge``, ``landscape``, ``portrait``, ``square``) and ``c``
overall colour. They are passed through untouched: page size, sort order and
window defaults belong to the server, and nothing is chosen, clamped or
validated locally.

``json`` is how an endpoint is asked for JSON, and the client sends it as an
empty query value. The documented ``xml`` form is deliberately not
implemented and no ``.json`` path suffix is used.

The documented rate limit of 60 requests per minute is not enforced here: a
caller paging through results paces itself. No login is implemented; the
page requires a user-agent carrying the project name and the caller's
Zerochan username, configured through ``request.user_agent``. Anonymous
requests can succeed but the page warns that anonymous projects may be banned.

Which combinations were actually called against the live site is recorded
in docs/verification.md.

Classes:
    ZerochanApi_Mixin -- Zerochan entry list and detail calls.
"""

# __future__ imports
from __future__ import absolute_import

# Standard library imports
from urllib.parse import quote_plus


class ZerochanApi_Mixin(object):
    """Native Zerochan API calls.

    * Doc: https://www.zerochan.net/api
    """

    # ------------------------------------------------------------------
    # Entries
    # ------------------------------------------------------------------

    def entry_list(self, tags=None, strict=False, **params):
        """Get a list of entries.

        Parameters:
            tags (None, str or sequence of str): ``None`` lists every entry;
                a string is one tag; a list or tuple is several tags. Each
                name is escaped as a whole path segment (a space becomes
                ``+``) and the names are joined with commas. Names are never
                lowercased and a string is never split on spaces or commas,
                so ``"Genshin Impact"`` is one tag while ``["Lumine",
                "Flower"]`` is two.
            strict (bool): Send the ``strict`` presence marker, keeping only
                entries whose primary tag is the matched tag. The page
                documents this mode on the single-tag endpoint.
            **params: The documented query parameters, passed through
                unchanged: ``p`` page, ``l`` limit (1-250), ``s`` sort
                (``id`` or ``fav``), ``t`` popularity window (``0``, ``1``
                or ``2``), ``d`` dimension (``large``, ``huge``,
                ``landscape``, ``portrait``, ``square``) and ``c`` colour.

        Returns the ``items`` list. Observed responses have no paging
        metadata; the fields observed per entry are id, width, height, md5,
        thumbnail, source, tag (primary tag) and tags (tag list).
        """
        if tags is None:
            path = ""
        elif isinstance(tags, str):
            path = quote_plus(tags, safe="")
        else:
            path = ",".join(quote_plus(name, safe="") for name in tags)
        if strict:
            params["strict"] = ""
        return self.request(path, params=params, envelope="items")

    def entry_show(self, entry_id):
        """Get detailed information about one entry.

        Parameters:
            entry_id (int): The entry id, as returned by ``entry_list``.

        Returns the entry object itself: this endpoint has no envelope. The
        fields observed are the id, the small/medium/large/full image URLs,
        width, height, size, hash, source, the primary tag and the tag list.
        """
        return self.request(str(entry_id))
