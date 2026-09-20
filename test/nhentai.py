"""nhentai anonymous smoke checks: at most 10 HTTP attempts.

Ten read-only GETs against the nhentai JSON API (``https://nhentai.net``,
``api/v2``), every value taken from ``smoke.nhentai``; the page numbers and the
pause come from the root ``smoke`` section, which ``smoke.nhentai`` may still
override. In order: two ``api/v2/galleries`` pages at the configured
``per_page``, ``api/v2/galleries/{gallery_id}``, ``api/v2/search`` for the
configured query, ``api/v2/galleries/popular``, ``api/v2/tags/{tag_type}/{slug}``,
that gallery's ``comments/count`` and its ``comments`` at the configured
``per_page``, a missing gallery id, and an out-of-range page.

List and comment answers share one envelope -- ``{"result": [...],
"num_pages": N, "per_page": N, "total": N|null}`` -- and it is consumed as it
arrives. Gallery entries are checked for the schema's required ``id``,
``media_id``, ``english_title``, ``thumbnail``, ``thumbnail_width`` and
``thumbnail_height`` plus the defaulted ``num_pages``, ``num_favorites``,
``tag_ids`` and ``blacklisted``; the detail adds the ``title``, ``cover``,
``thumbnail``, ``upload_date``, ``tags`` and ``pages`` objects, and its
nullable extras (``comments``, ``comment_count``, ``related``,
``is_favorited``, ``suggestions``) are type-checked only when the key is
there, because the schema allows both null and omission. ``popular`` answers a
bare array whose length is not pinned (it has no documented size, so a run
must not demand five); ``comments/count`` answers a bare integer; and
``api/v2/tags/{tag_type}/{slug}`` answers one tag object whose ``type`` and
``slug`` must echo the configured pair.

No line printed by this file contains a gallery title, a comment body or a tag
name: the output reports identifiers, key names, lengths and counts, and the
media paths are never requested. Page identifiers are reported without requiring
disjoint pages: newly added galleries can shift pagination between requests.
The missing id must arrive as HTTP 404 and the bad page as HTTP 400, both through the shared
``AnybooruHTTPError``, whose body wording is only measured, never asserted:
the read-only probe batch observed 400 for an out-of-range ``page`` while the
schema documents 422 for a ``page`` below its minimum, so this check pins the
observed 400 and leaves the status the site's to decide, never mapping it
locally.

The client is built with an explicit empty ``api_key``, so the run stays
anonymous whatever the configuration holds; redirects are disabled, no request
is retried, and consecutive calls pause for the configured number of seconds.
If the configured gallery cannot be read, its two comment checks are reported
as SKIP rather than sending requests for an id the site has already refused.
Recorded in docs/verification.md.
"""

import argparse
from functools import partial
import time


ENVELOPE_FIELDS = {'result': list, 'num_pages': int, 'per_page': int}
ENVELOPE_NULLABLE = {'total': (int, type(None))}
GALLERY_ITEM_FIELDS = {'id': int, 'media_id': str, 'english_title': str,
                       'thumbnail': str, 'thumbnail_width': int,
                       'thumbnail_height': int, 'num_pages': int,
                       'num_favorites': int, 'tag_ids': list,
                       'blacklisted': bool}
GALLERY_ITEM_NULLABLE = {'japanese_title': (str, type(None))}
TITLE_FIELDS = {'english': str, 'pretty': str}
TITLE_NULLABLE = {'japanese': (str, type(None))}
COVER_FIELDS = {'path': str, 'width': int, 'height': int}
PAGE_INFO_FIELDS = {'number': int, 'path': str, 'width': int, 'height': int,
                    'thumbnail': str, 'thumbnail_width': int,
                    'thumbnail_height': int}
TAG_FIELDS = {'id': int, 'type': str, 'name': str, 'slug': str, 'url': str,
              'count': int}
TAG_NULLABLE = {'description': (str, type(None)),
                'is_community': (bool, type(None)),
                'pending_describe_id': (str, type(None))}
DETAIL_FIELDS = {'id': int, 'media_id': str, 'title': dict, 'cover': dict,
                 'thumbnail': dict, 'upload_date': int, 'tags': list,
                 'num_pages': int, 'num_favorites': int, 'scanlator': str,
                 'pages': list}
DETAIL_NULLABLE = {'comments': (list, type(None)),
                   'comment_count': (int, type(None)),
                   'related': (list, type(None)),
                   'is_favorited': (bool, type(None)),
                   'suggestions': (dict, type(None))}
POSTER_FIELDS = {'id': int, 'username': str, 'slug': str, 'avatar_url': str,
                 'is_superuser': bool, 'is_staff': bool}
COMMENT_FIELDS = {'id': int, 'gallery_id': int, 'poster': dict,
                  'post_date': int, 'body': str}


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


def nullable(value, expected):
    """Type-check the nullable fields the schema may also leave out entirely."""
    seen = []
    for key, kind in expected.items():
        if key in value:
            kind_of(key, value[key], kind)
            seen.append(key)
    return seen


def gallery_item(value):
    """Check one list entry, and never echo its textual title fields."""
    detail = fields(value, GALLERY_ITEM_FIELDS)
    for tag_id in value['tag_ids']:
        require(type(tag_id) is int,
                f'tag_ids entry: got {type(tag_id).__name__}')
    nullable(value, GALLERY_ITEM_NULLABLE)
    return detail


def tag_entity(value):
    detail = fields(value, TAG_FIELDS)
    nullable(value, TAG_NULLABLE)
    return detail


def gallery_page(value, page, per_page=None):
    detail = fields(value, ENVELOPE_FIELDS)
    nullable(value, ENVELOPE_NULLABLE)
    for item in value['result']:
        gallery_item(item)
    ids = [item['id'] for item in value['result']]
    first = value['result'][0] if value['result'] else None
    if first is None:
        lead = 'first=none'
    else:
        lead = (f"first={first['id']} media_id={first['media_id']} "
                f"pages={first['num_pages']} favorites={first['num_favorites']} "
                f"tag_ids={len(first['tag_ids'])} blacklisted={first['blacklisted']} "
                f"thumbnail={first['thumbnail_width']}x{first['thumbnail_height']}")
    requested = f'requested_per_page={per_page} ' if per_page is not None else ''
    return (f"{detail} | page={page} {requested}"
            f"num_pages={value['num_pages']} total={value.get('total')} "
            f"galleries={len(value['result'])} ids={ids} {lead}")


def gallery_detail(value, gallery_id):
    """Check the detail object; titles and tag names stay unprinted."""
    detail = fields(value, DETAIL_FIELDS)
    seen = nullable(value, DETAIL_NULLABLE)
    require(value['id'] == gallery_id,
            f"gallery id={value['id']}, requested {gallery_id}")
    fields(value['title'], TITLE_FIELDS)
    nullable(value['title'], TITLE_NULLABLE)
    for key in ('cover', 'thumbnail'):
        fields(value[key], COVER_FIELDS)
    for tag in value['tags']:
        tag_entity(tag)
    for page in value['pages']:
        fields(page, PAGE_INFO_FIELDS)
    page_keys = sorted(value['pages'][0]) if value['pages'] else None
    return (f"{detail} | id={value['id']} media_id={value['media_id']} "
            f"title_keys={sorted(value['title'])} "
            f"cover={value['cover']['width']}x{value['cover']['height']} "
            f"scanlator_chars={len(value['scanlator'])} "
            f"upload_date={value['upload_date']} pages={value['num_pages']} "
            f"favorites={value['num_favorites']} tags={len(value['tags'])} "
            f"tag_types={sorted({tag['type'] for tag in value['tags']})} "
            f"page_objects={len(value['pages'])} page_keys={page_keys} "
            f"nullable_present={seen}")


def popular_galleries(value):
    """The route documents no size, so only the array itself is required."""
    require(type(value) is list,
            f'expected a bare array, got {type(value).__name__}')
    for item in value:
        gallery_item(item)
    return f"galleries={len(value)} ids={[item['id'] for item in value]}"


def tag_detail(value, tag_type, slug):
    """Check one tag object, and never echo its name or description text."""
    detail = tag_entity(value)
    require(value['type'] == tag_type, 'tag type does not match the requested type')
    require(value['slug'] == slug, 'tag slug does not match the requested slug')
    return (f"{detail} | id={value['id']} count={value['count']} "
            f"name_chars={len(value['name'])} type_matches slug_matches "
            f"description_present={value.get('description') is not None}")


def comment_count(value, gallery_id):
    require(type(value) is int,
            f'expected an integer, got {type(value).__name__}')
    return f'gallery_id={gallery_id} comment_count={value}'


def comments_page(value, gallery_id, per_page):
    detail = fields(value, ENVELOPE_FIELDS)
    nullable(value, ENVELOPE_NULLABLE)
    for comment in value['result']:
        fields(comment, COMMENT_FIELDS)
        fields(comment['poster'], POSTER_FIELDS)
        require(comment['gallery_id'] == gallery_id,
                'comment gallery id does not match the requested gallery')
    return (f"{detail} | gallery_id={gallery_id} requested_per_page={per_page} "
            f"num_pages={value['num_pages']} total={value.get('total')} "
            f"comments={len(value['result'])} "
            f"comment_ids={[comment['id'] for comment in value['result']]} "
            f"poster_ids={[comment['poster']['id'] for comment in value['result']]} "
            f"body_chars={[len(comment['body']) for comment in value['result']]} "
            f"post_dates={[comment['post_date'] for comment in value['result']]}")


def exercise(client, settings):
    from anybooru import AnybooruHTTPError
    from requests import RequestException

    counts = {'requests': 0, 'passed': 0, 'failed': 0}
    # One call = one HTTP attempt: never follow redirects or retry.
    client.client.request = partial(client.client.request, allow_redirects=False)

    def check(name, call, inspect, expected=200):
        codes = expected if isinstance(expected, tuple) else (expected,)
        wanted = ' or '.join(str(code) for code in codes)
        if counts['requests']:
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
            elif isinstance(error, RequestException) and error.request is not None:
                url = error.request.url
            elif client.last_call:
                url = client.last_call['url']
                status = f"HTTP {client.last_call['status_code']}"
            counts['failed'] += 1
            print(f'FAIL {name} | {url} | {status} | {type(error).__name__}: {error}', flush=True)
            return None
        counts['passed'] += 1
        print(f'PASS {name} | {url} | {status} | {detail}', flush=True)
        return result if 200 in codes else None

    def expected_error(error):
        """Consume a documented failure without asserting the site's wording."""
        require(client.last_call.get('status_code') == error.http_code,
                f"last_call status_code={client.last_call.get('status_code')!r}, "
                f'expected {error.http_code}')
        require(client.last_call.get('url') == error.url,
                f"last_call url={client.last_call.get('url')!r}, expected {error.url!r}")
        content_type = error.response.headers.get('Content-Type', 'no Content-Type')
        return (f'data={type(error.data).__name__} body_chars={len(error.body)} '
                f'content_type={content_type!r} '
                f'last_call=HTTP {client.last_call["status_code"]} {client.last_call["url"]}')

    pages = settings['pages']
    list_query = settings['list_query']
    search_query = settings['search_query']
    gallery_id = settings['gallery_id']
    per_page = list_query['per_page']

    check(f'gallery_list page {pages[0]}',
          lambda: client.gallery_list(page=pages[0], **list_query),
          lambda value: gallery_page(value, pages[0], per_page))
    check(f'gallery_list page {pages[1]}',
          lambda: client.gallery_list(page=pages[1], **list_query),
          lambda value: gallery_page(value, pages[1], per_page))
    detailed = check('gallery_show configured id',
                     lambda: client.gallery_show(gallery_id),
                     lambda value: gallery_detail(value, gallery_id))
    check('search configured query', lambda: client.search(**search_query),
          lambda value: gallery_page(value, search_query['page']))
    check('gallery_popular', client.gallery_popular, popular_galleries)
    check('tag_show configured slug',
          lambda: client.tag_show(settings['tag_type'], settings['tag_slug']),
          lambda value: tag_detail(value, settings['tag_type'], settings['tag_slug']))
    if detailed is None:
        print('SKIP gallery_comment_count | - | no HTTP | '
              'gallery_show configured id failed', flush=True)
        print('SKIP gallery_comments configured gallery | - | no HTTP | '
              'gallery_show configured id failed', flush=True)
    else:
        check('gallery_comment_count',
              lambda: client.gallery_comment_count(gallery_id),
              lambda value: comment_count(value, gallery_id))
        check('gallery_comments configured gallery',
              lambda: client.gallery_comments(gallery_id, per_page=per_page),
              lambda value: comments_page(value, gallery_id, per_page))
    check('gallery_show missing id',
          lambda: client.gallery_show(settings['missing_id']),
          expected_error, expected=404)
    check('gallery_list rejected page',
          lambda: client.gallery_list(**settings['invalid_query']),
          expected_error, expected=400)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Nhentai
        from anybooru.resources import load_config

        smoke = load_config(args.config)['smoke']
        settings = dict(smoke['nhentai'])
        for key in ('pages', 'pause_seconds'):
            settings.setdefault(key, smoke[key])
        client = Nhentai(settings['site'], api_key='', config_file=args.config)
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY nhentai | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; '
              'anonymous api_key=""', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
