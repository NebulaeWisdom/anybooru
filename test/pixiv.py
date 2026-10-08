"""pixiv anonymous smoke checks: exactly ten read-only HTTP attempts.

Ten GETs against pixiv's two JSON surfaces -- the site's own front end under
``https://www.pixiv.net`` (``/ajax/...`` and ``/ranking.php``) and the app API
under ``https://app-api.pixiv.net`` (``/v1/...``) -- every value taken from
``smoke.pixiv``; the page numbers and the pause come from that section. In
order: two ``web_ranking`` pages, two ``web_search_artworks`` pages for the
configured word, one ``web_illust_show``, one ``web_illust_pages``, one
``web_user_show`` with the configured user query, one ``web_user_profile_all``,
one missing illustration id, and one anonymous ``app_illust_detail``.

The web envelopes differ by route and each shape is checked as the site sends
it. ``web_illust_show``, ``web_illust_pages``, ``web_user_show`` and
``web_user_profile_all`` answer ``{"error": false, "message": "",
"body": ...}``: the illustration body carries the identifiers, title, type
flags, width/height, page count, dates, the four/five ``urls`` addresses and
the ``tags`` object whose ``tags`` array items hold ``tag``/``locked``/
``deletable`` (the ``userId``/``userName`` actor keys appear on some tags only
and are checked when present); the pages body is an
array of ``{"urls", "width", "height"}``; the user body carries ``userId``
(echoed back as the string it was requested by), ``name``, the two profile
image addresses, ``premium``, ``isFollowed``, ``partial`` and the counters
``following``/``mypixivCount``; the profile body carries the ``illusts`` id map
(an object keyed by illustration id), plus ``manga``/``novels``/
``bookmarkCount``. ``web_search_artworks`` instead answers
``{"error": false, "body": {"illustManga": {"data", "total", "lastPage", ...},
...}}``; this file reads only ``error`` and ``body`` and never touches any
optional ``message`` key. Its ``data`` array mixes the real artworks with
advertisement placeholders that carry only ``isAdContainer``; this file splits
the two, checks ``isAdContainer`` is true on each placeholder, reports the
``ad_slots`` count and validates the remaining rows as artworks for ``id``,
``title``, ``illustType``, ``xRestrict``,
``restrict``, ``sl``, ``url``, ``userId``, ``userName``, ``width``, ``height``,
``pageCount``, ``createDate``, ``updateDate``, ``description`` and ``alt``.
``web_ranking`` is a third shape: the bare root object with ``contents``,
``mode``, ``content``, ``page``, ``prev``, ``next``, ``date``, ``rank_total``
and ``meta``, no ``error``/``message`` wrapper; each of its 50 ``contents``
entries is checked for ``rank``, ``illust_id``, ``user_id``, ``width``,
``height``, ``view_count``, ``rating_count`` and the remaining documented keys
(``illust_series`` is accepted as either a boolean or an object), and the
returned ``page`` must equal the requested one.

Every listing reports its ``total``/``lastPage`` (search) or ``rank_total``
(ranking) and the entry count, but no line asserts that a page is full, that a
short page is the last one, or that two pages share no identifier: pixiv
rankings and listings are live, so those would turn real churn into false
failures. Page numbers are never clamped locally, so a 200 with a
non-matching body fails on the field check rather than being silently
accepted, and the two error paths prove the shared transport keeps the site's
own status: the configured missing illustration id must raise the shared
``AnybooruHTTPError`` with the documented ``{"error": true, "message": "",
"body": []}`` body, and the anonymous ``app_illust_detail`` call must raise it
with the OAuth ``invalid_request`` object the app host sends a request without
a token.

No line printed by this file contains an illustration ``url``/``urls``
address, a user ``image``, a ``profile_img`` or a ``profileImageUrl`` value:
the output reports identifiers, key names, lengths and counts, and no media
byte is ever requested. The client is built with explicit empty ``cookie``,
``access_token`` and ``csrf_token``, so the run stays anonymous whatever the
configuration holds; the client already disables redirects for every call, no
request is retried, and every call pauses for the configured number of
seconds, the first one included. Recorded in docs/verification.md.
"""

import argparse
import time


ENVELOPE_FIELDS = {'error': bool, 'message': str}
ILLUST_BODY_FIELDS = {'illustId': str, 'id': str, 'illustTitle': str,
                      'title': str, 'illustType': int, 'xRestrict': int,
                      'sl': int, 'userId': str, 'userName': str,
                      'userAccount': str, 'width': int, 'height': int,
                      'pageCount': int, 'createDate': str, 'uploadDate': str,
                      'description': str, 'illustComment': str,
                      'urls': dict, 'tags': dict}
ILLUST_URL_FIELDS = {'mini': str, 'thumb': str, 'small': str, 'regular': str,
                     'original': str}
ILLUST_TAG_FIELDS = {'tag': str, 'locked': bool, 'deletable': bool}
ILLUST_TAG_ACTOR_KEYS = ('userId', 'userName')
PAGE_ITEM_FIELDS = {'urls': dict, 'width': int, 'height': int}
PAGE_URL_FIELDS = {'thumb_mini': str, 'small': str, 'regular': str,
                   'original': str}
USER_BODY_FIELDS = {'userId': str, 'name': str, 'image': str, 'imageBig': str,
                    'premium': bool, 'isFollowed': bool, 'following': int,
                    'mypixivCount': int, 'partial': int}
PROFILE_BODY_FIELDS = {'illusts': dict, 'manga': dict, 'novels': list,
                       'bookmarkCount': dict}
SEARCH_ITEM_FIELDS = {'id': str, 'title': str, 'illustType': int,
                      'xRestrict': int, 'restrict': int, 'sl': int, 'url': str,
                      'userId': str, 'userName': str, 'width': int,
                      'height': int, 'pageCount': int, 'createDate': str,
                      'updateDate': str, 'description': str, 'alt': str}
RANKING_FIELDS = {'contents': list, 'mode': str, 'content': str, 'page': int,
                  'prev': (bool, int), 'next': (bool, int), 'date': str,
                  'rank_total': int, 'meta': dict}
RANKING_ITEM_FIELDS = {'title': str, 'date': str, 'tags': list, 'url': str,
                       'illust_type': str, 'illust_book_style': str,
                       'illust_page_count': str, 'user_name': str,
                       'profile_img': str, 'illust_id': int, 'width': int,
                       'height': int, 'user_id': int, 'rank': int,
                       'yes_rank': int, 'rating_count': int,
                       'view_count': int, 'illust_upload_timestamp': int,
                       'attr': str, 'illust_content_type': dict,
                       'illust_series': (bool, dict), 'is_masked': bool}


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def kind_of(key, value, kind):
    kinds = kind if isinstance(kind, tuple) else (kind,)
    require(type(value) in kinds,
            f'{key}: expected {"/".join(item.__name__ for item in kinds)}, '
            f'got {type(value).__name__}')


def fields(value, expected):
    require(type(value) is dict, f'expected object, got {type(value).__name__}')
    for key, kind in expected.items():
        require(key in value, f'missing field {key}')
        kind_of(key, value[key], kind)
    return ','.join(f'{key}:{value[key].__class__.__name__}' for key in expected)


def web_envelope(value, body_kind):
    """Check the ``error``/``message``/``body`` wrapper and its body kind."""
    detail = fields(value, ENVELOPE_FIELDS)
    require(value['error'] is False, f"error={value['error']!r}, expected false")
    kind_of('body', value['body'], body_kind)
    return detail


def illust_detail(value, illust_id):
    """Check one illustration detail; media addresses stay unprinted."""
    detail = web_envelope(value, dict)
    body = value['body']
    fields(body, ILLUST_BODY_FIELDS)
    require(body['illustId'] == illust_id,
            f"illustId={body['illustId']!r}, requested {illust_id!r}")
    require(body['id'] == illust_id,
            f"id={body['id']!r}, requested {illust_id!r}")
    fields(body['urls'], ILLUST_URL_FIELDS)
    fields(body['tags'], {'tags': list})
    actors = 0
    for tag in body['tags']['tags']:
        fields(tag, ILLUST_TAG_FIELDS)
        present = [key for key in ILLUST_TAG_ACTOR_KEYS if key in tag]
        if present:
            actors += 1
            for key in present:
                kind_of(key, tag[key], str)
    return (f"{detail} | illustId={body['illustId']} title_chars="
            f"{len(body['illustTitle'])} illustType={body['illustType']} "
            f"xRestrict={body['xRestrict']} sl={body['sl']} "
            f"size={body['width']}x{body['height']} "
            f"pageCount={body['pageCount']} userId={body['userId']} "
            f"account_chars={len(body['userAccount'])} "
            f"bookmarkCount={body['bookmarkCount']} "
            f"likeCount={body['likeCount']} viewCount={body['viewCount']} "
            f"tags={len(body['tags']['tags'])} tags_with_actor={actors} "
            f"actor_keys={list(ILLUST_TAG_ACTOR_KEYS)} "
            f"url_keys={sorted(body['urls'])}")


def illust_pages(value, illust_id):
    """Check the pages array; each entry only reports its size in the line."""
    detail = web_envelope(value, list)
    for item in value['body']:
        fields(item, PAGE_ITEM_FIELDS)
        fields(item['urls'], PAGE_URL_FIELDS)
    sizes = ['{}x{}'.format(item['width'], item['height'])
             for item in value['body']]
    return (f"{detail} | requested={illust_id} pages={len(value['body'])} "
            f"sizes={sizes} "
            f"url_keys={sorted(value['body'][0]['urls']) if value['body'] else []}")


def user_show(value, user_id):
    """Check one user profile; the two image addresses stay unprinted."""
    detail = web_envelope(value, dict)
    body = value['body']
    fields(body, USER_BODY_FIELDS)
    require(body['userId'] == user_id,
            f"userId={body['userId']!r}, requested {user_id!r}")
    return (f"{detail} | userId={body['userId']} name_chars={len(body['name'])} "
            f"premium={body['premium']} isFollowed={body['isFollowed']} "
            f"partial={body['partial']} following={body['following']} "
            f"mypixivCount={body['mypixivCount']} "
            f"image_chars={len(body['image'])} "
            f"imageBig_chars={len(body['imageBig'])}")


def user_profile_all(value, user_id):
    """Check the profile index; the ``illusts`` map is keyed by id string."""
    detail = web_envelope(value, dict)
    body = value['body']
    fields(body, PROFILE_BODY_FIELDS)
    require(all(type(key) is str for key in body['illusts']),
            'the illusts map must be keyed by illustration id strings')
    return (f"{detail} | requested={user_id} illusts={len(body['illusts'])} "
            f"manga={len(body['manga'])} novels={len(body['novels'])} "
            f"bookmarkCount_keys={sorted(body['bookmarkCount'])}")


def search_page(value, page, word):
    """Split the ad placeholders from the real artworks, dropping neither."""
    fields(value, {'error': bool, 'body': dict})
    require(value['error'] is False, f"error={value['error']!r}, expected false")
    manga = value['body']['illustManga']
    detail = fields(manga, {'data': list, 'total': int, 'lastPage': int})
    require(manga['total'] >= 0, f"total={manga['total']}")
    require(manga['lastPage'] >= 0, f"lastPage={manga['lastPage']}")
    slots = manga['data']
    ad_slots = [slot for slot in slots if 'isAdContainer' in slot]
    artworks = [slot for slot in slots if 'isAdContainer' not in slot]
    for slot in ad_slots:
        require(slot['isAdContainer'] is True,
                f"ad slot isAdContainer={slot['isAdContainer']!r}, expected true")
    for item in artworks:
        fields(item, SEARCH_ITEM_FIELDS)
        for tag in item['tags']:
            require(type(tag) is str, f'tag: got {type(tag).__name__}')
    lead = artworks[0] if artworks else None
    if lead is None:
        head = 'first=none'
    else:
        head = (f"first_id={lead['id']} first_type={lead['illustType']} "
                f"first_pages={lead['pageCount']} "
                f"first_size={lead['width']}x{lead['height']} "
                f"first_user={lead['userId']} first_tags={len(lead['tags'])}")
    return (f"{detail} | requested_page={page} word={word!r} "
            f"total={manga['total']} lastPage={manga['lastPage']} "
            f"slots={len(slots)} artworks={len(artworks)} "
            f"ad_slots={len(ad_slots)} "
            f"ad_slot_keys={[sorted(slot) for slot in ad_slots]} "
            f"ids={[item['id'] for item in artworks]} {head}")


def ranked_page(value, page):
    """Check one ranking root; its ``page`` must answer the request."""
    detail = fields(value, RANKING_FIELDS)
    require(value['page'] == page,
            f"page={value['page']!r}, requested {page!r}")
    require(value['rank_total'] >= 0, f"rank_total={value['rank_total']}")
    for item in value['contents']:
        fields(item, RANKING_ITEM_FIELDS)
        for tag in item['tags']:
            require(type(tag) is str, f'tag: got {type(tag).__name__}')
    lead = value['contents'][0] if value['contents'] else None
    if lead is None:
        head = 'first=none'
    else:
        head = (f"first_rank={lead['rank']} first_id={lead['illust_id']} "
                f"first_type={lead['illust_type']} "
                f"first_size={lead['width']}x{lead['height']} "
                f"first_views={lead['view_count']} "
                f"first_rating={lead['rating_count']} "
                f"first_user={lead['user_id']} "
                f"first_tags={len(lead['tags'])}")
    return (f"{detail} | page={value['page']} mode={value['mode']} "
            f"content={value['content']} prev={value['prev']!r} "
            f"next={value['next']!r} rank_total={value['rank_total']} "
            f"date={value['date']} entries={len(value['contents'])} "
            f"ranks={[item['rank'] for item in value['contents']]} {head}")


def exercise(client, settings):
    from anybooru import AnybooruHTTPError

    counts = {'requests': 0, 'passed': 0, 'failed': 0}
    # The family request already sends allow_redirects=False for every call.

    def check(name, call, inspect, expected=200):
        codes = expected if isinstance(expected, tuple) else (expected,)
        wanted = ' or '.join(str(code) for code in codes)
        time.sleep(settings['pause_seconds'])
        counts['requests'] += 1
        client.last_call = {}
        url, status = '-', 'no HTTP response'
        try:
            try:
                result = call()
            except AnybooruHTTPError as error:
                url, status = error.url, f'HTTP {error.http_code}'
                require(error.http_code in codes,
                        f'expected HTTP {wanted}; AnybooruHTTPError; '
                        f'body_chars={len(error.body)}')
                detail = inspect(error)
                status += ' AnybooruHTTPError (expected)'
            else:
                url = client.last_call['url']
                status = (f"HTTP {client.last_call['status_code']} "
                          f"{client.last_call['headers'].get('Content-Type', 'no Content-Type')}")
                require(200 in codes,
                        f'expected HTTP {wanted}, got a successful response')
                require(client.last_call['status_code'] == 200, 'expected HTTP 200')
                detail = inspect(result)
        except Exception as error:
            response = getattr(error, 'response', None)
            if response is not None:
                url, status = response.url, f'HTTP {response.status_code}'
            elif client.last_call:
                url = client.last_call['url']
                status = f"HTTP {client.last_call['status_code']}"
            counts['failed'] += 1
            print(f'FAIL {name} | {url} | {status} | {type(error).__name__}: {error}', flush=True)
            return None
        counts['passed'] += 1
        print(f'PASS {name} | {url} | {status} | {detail}', flush=True)
        return result if 200 in codes else None

    def missing_illust(error):
        """The configured missing id must carry the empty-error web body."""
        require(client.last_call.get('status_code') == error.http_code,
                f"last_call status_code={client.last_call.get('status_code')!r}, "
                f'expected {error.http_code}')
        require(client.last_call.get('url') == error.url,
                f"last_call url={client.last_call.get('url')!r}, expected {error.url!r}")
        require(type(error.data) is dict,
                f'expected a JSON error object, got {type(error.data).__name__}')
        require(error.data.get('error') is True,
                f"error body {error.data.get('error')!r} is not true")
        require(error.data.get('message') == '',
                f"error body message {error.data.get('message')!r} is not empty")
        require(error.data.get('body') == [],
                f"error body body {error.data.get('body')!r} is not []")
        content_type = error.response.headers.get('Content-Type', 'no Content-Type')
        return (f"data={type(error.data).__name__} error=True message='' body=[] "
                f"body_chars={len(error.body)} content_type={content_type!r} "
                f"last_call=HTTP {client.last_call['status_code']} "
                f"{client.last_call['url']}")

    def app_denied(error):
        """An anonymous app call must carry the OAuth invalid_request object."""
        require(client.last_call.get('status_code') == error.http_code,
                f"last_call status_code={client.last_call.get('status_code')!r}, "
                f'expected {error.http_code}')
        require(client.last_call.get('url') == error.url,
                f"last_call url={client.last_call.get('url')!r}, expected {error.url!r}")
        require(type(error.data) is dict,
                f'expected a JSON error object, got {type(error.data).__name__}')
        inner = error.data.get('error')
        require(type(inner) is dict,
                f'expected the error object, got {type(inner).__name__}')
        fields(inner, {'user_message': str, 'message': str, 'reason': str,
                       'user_message_details': dict})
        require('invalid_request' in inner['message'],
                f"message {inner['message']!r} does not mention invalid_request")
        content_type = error.response.headers.get('Content-Type', 'no Content-Type')
        return (f"data={type(error.data).__name__} error_keys={sorted(inner)} "
                f"message_chars={len(inner['message'])} mentions=invalid_request "
                f"reason={inner['reason']!r} body_chars={len(error.body)} "
                f"content_type={content_type!r} "
                f"last_call=HTTP {client.last_call['status_code']} "
                f"{client.last_call['url']}")

    pages = settings['pages']
    ranking_query = settings['ranking_query']
    search_query = settings['search_query']
    word = settings['word']
    illust_id = settings['illust_id']
    user_id = settings['user_id']
    user_query = settings['user_query']

    check(f'web_ranking page {pages[0]}',
          lambda: client.web_ranking(p=pages[0], **ranking_query),
          lambda value: ranked_page(value, pages[0]))
    check(f'web_ranking page {pages[1]}',
          lambda: client.web_ranking(p=pages[1], **ranking_query),
          lambda value: ranked_page(value, pages[1]))
    check(f'web_search_artworks page {pages[0]}',
          lambda: client.web_search_artworks(word, p=pages[0], **search_query),
          lambda value: search_page(value, pages[0], word))
    check(f'web_search_artworks page {pages[1]}',
          lambda: client.web_search_artworks(word, p=pages[1], **search_query),
          lambda value: search_page(value, pages[1], word))
    check('web_illust_show configured id',
          lambda: client.web_illust_show(illust_id),
          lambda value: illust_detail(value, illust_id))
    check('web_illust_pages configured id',
          lambda: client.web_illust_pages(illust_id),
          lambda value: illust_pages(value, illust_id))
    check('web_user_show configured id',
          lambda: client.web_user_show(user_id, **user_query),
          lambda value: user_show(value, user_id))
    check('web_user_profile_all configured id',
          lambda: client.web_user_profile_all(user_id),
          lambda value: user_profile_all(value, user_id))
    check('web_illust_show missing id',
          lambda: client.web_illust_show(settings['missing_illust_id']),
          missing_illust, expected=settings['missing_status'])
    check('app_illust_detail anonymous',
          lambda: client.app_illust_detail(illust_id),
          app_denied, expected=settings['app_error_status'])

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Pixiv
        from anybooru.resources import load_config

        smoke = load_config(args.config)['smoke']
        settings = dict(smoke['pixiv'])
        client = Pixiv(settings['site'], cookie='', access_token='',
                       csrf_token='', config_file=args.config)
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY pixiv | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; '
              'anonymous cookie="" access_token="" csrf_token=""', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
