"""wallhaven anonymous smoke checks: exactly eight HTTP attempts.

Eight read-only GETs against the Wallhaven JSON API (``https://wallhaven.cc``,
``api/v1``), every value taken from ``smoke.wallhaven``; the page numbers and
the pause come from that section, falling back to the root ``smoke`` section
for the same keys. In order: two ``api/v1/search`` pages for the configured
query, one ``api/v1/search`` for the configured exact-tag query, one
``api/v1/w/{wallpaper_id}`` detail, one ``api/v1/tag/{tag_id}``, one
``api/v1/collections/{username}``, one
``api/v1/collections/{username}/{collection_id}``, and a missing wallpaper id.

Search and collection wallpapers share one envelope -- ``{"data": [...],
"meta": {...}}`` -- whose entries are checked for the documented summary
fields: ``id``, ``url``, ``short_url``, ``views``, ``favorites``, ``source``,
``purity``, ``category``, ``dimension_x``, ``dimension_y``, ``resolution``,
``ratio``, ``file_size``, ``file_type``, ``created_at``, ``colors``, ``path``
and ``thumbs`` with its ``large``/``original``/``small`` addresses. Only the
search ``meta`` also carries ``query`` (a string, ``null`` or an
``{"id", "tag"}`` object) and ``seed``; the collection ``meta`` stops at
``current_page``, ``last_page``, ``per_page`` and ``total``. Every listing
that names a page must report that page back, and each returned
``purity``/``category`` must fall inside the configured three-flag mask, so a
change to the configured filters is observable without pinning site-wide
counts, ordering or page-id disjointness.

The wallpaper detail adds the ``uploader`` object (``username``, ``group``
and the four ``avatar`` addresses) and the ``tags`` array; each tag is
checked for ``id``, ``name``, ``alias``, ``category_id``, ``category``,
``purity`` and ``created_at``. ``api/v1/tag/{tag_id}`` is one such object and
must echo the requested id, and when the exact-tag search reports a ``query``
object its ``id`` must match the configured tag id. The public collections
listing is a bare
``{"data": [...]}`` with ``id``, ``label``, ``views``, ``public`` and
``count`` per entry; its length is never pinned because another account's
public set can change.

No line printed by this file contains a wallpaper ``path``, ``url`` or
``source`` value, a tag name, a tag alias or a collection label: the output
reports identifiers, key names, lengths and counts, and no media byte is ever
requested. The missing wallpaper id must arrive as HTTP 404 through the
shared ``AnybooruHTTPError``; that body is inspected for the site's own
``{"error": "Nothing here"}`` wording. The client is built with an explicit
empty ``apikey``, so the run stays anonymous whatever the configuration
holds; redirects are disabled, no request is retried, and every call pauses
for the configured number of seconds, the first one included. Recorded in
docs/verification.md.
"""

import argparse
from functools import partial
import time


WALLPAPER_FIELDS = {'id': str, 'url': str, 'short_url': str, 'views': int,
                    'favorites': int, 'source': str, 'purity': str,
                    'category': str, 'dimension_x': int, 'dimension_y': int,
                    'resolution': str, 'ratio': str, 'file_size': int,
                    'file_type': str, 'created_at': str, 'colors': list,
                    'path': str, 'thumbs': dict}
THUMB_FIELDS = {'large': str, 'original': str, 'small': str}
UPLOADER_FIELDS = {'username': str, 'group': str, 'avatar': dict}
AVATAR_FIELDS = {'200px': str, '128px': str, '32px': str, '20px': str}
TAG_FIELDS = {'id': int, 'name': str, 'alias': str, 'category_id': int,
              'category': str, 'purity': str, 'created_at': str}
DETAIL_FIELDS = dict(WALLPAPER_FIELDS, uploader=dict, tags=list)
SEARCH_META_FIELDS = {'current_page': int, 'last_page': int, 'per_page': int,
                      'total': int}
SEARCH_META_NULLABLE = {'query': (str, dict, type(None)),
                        'seed': (str, type(None))}
COLLECTION_META_FIELDS = dict(SEARCH_META_FIELDS)
COLLECTION_FIELDS = {'id': int, 'label': str, 'views': int, 'public': int,
                     'count': int}
ENVELOPE_FIELDS = {'data': list, 'meta': dict}
PURITY_BITS = ('sfw', 'sketchy', 'nsfw')
CATEGORY_BITS = ('general', 'anime', 'people')


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


def mask_matches(value, params, key, bits):
    """Every entry's value must sit inside the configured three-flag mask."""
    mask = (params or {}).get(key)
    if mask is None:
        return
    require(type(mask) is str and len(mask) == 3,
            f'{key}: expected three flags, got {mask!r}')
    allowed = {bits[index] for index, flag in enumerate(mask) if flag == '1'}
    require(value[key] in allowed,
            f"{key}={value[key]!r} outside the configured mask {mask!r}")


def wallpaper_item(value, params=None):
    """Check one list entry, and never echo its media addresses."""
    detail = fields(value, WALLPAPER_FIELDS)
    fields(value['thumbs'], THUMB_FIELDS)
    for color in value['colors']:
        require(type(color) is str, f'color: got {type(color).__name__}')
    mask_matches(value, params, 'purity', PURITY_BITS)
    mask_matches(value, params, 'category', CATEGORY_BITS)
    return detail


def wallpaper_page(value, meta_fields, meta_nullable, page, params):
    """Check one listing envelope and report the first entry without URLs."""
    detail = fields(value, ENVELOPE_FIELDS)
    for item in value['data']:
        wallpaper_item(item, params)
    meta = value['meta']
    fields(meta, meta_fields)
    nullable(meta, meta_nullable)
    require(meta['last_page'] >= meta['current_page'],
            f"last_page={meta['last_page']} < current_page={meta['current_page']}")
    require(meta['total'] >= 0, f"total={meta['total']}")
    if page is not None:
        require(meta['current_page'] == page,
                f"current_page={meta['current_page']}, requested {page}")
    first = value['data'][0] if value['data'] else None
    if first is None:
        lead = 'first=none'
    else:
        lead = (f"first={first['id']} purity={first['purity']} "
                f"category={first['category']} "
                f"resolution={first['dimension_x']}x{first['dimension_y']} "
                f"views={first['views']} favorites={first['favorites']} "
                f"file_size={first['file_size']} colors={len(first['colors'])}")
    return (f"{detail} | page={meta['current_page']} "
            f"last_page={meta['last_page']} per_page={meta['per_page']} "
            f"total={meta['total']} wallpapers={len(value['data'])} "
            f"ids={[item['id'] for item in value['data']]} {lead}")


def search_page(value, page, params):
    """A plain keyword search must echo its ``q`` back in ``meta.query``."""
    detail = wallpaper_page(value, SEARCH_META_FIELDS, SEARCH_META_NULLABLE,
                            page, params)
    query = params.get('q')
    checked = query is not None and not query.startswith('@')
    if checked:
        require(value['meta']['query'] == query,
                f"meta.query={value['meta']['query']!r} does not echo "
                f"q={query!r}")
    return detail + (' query_echo_matches' if checked else '')


def exact_tag_page(value, tag_id, params):
    """An ``id:`` search answers its tag object under ``meta.query``."""
    detail = wallpaper_page(value, SEARCH_META_FIELDS, SEARCH_META_NULLABLE,
                            None, params)
    query = value['meta']['query']
    require(type(query) is dict,
            f'expected the exact-tag query object, got {type(query).__name__}')
    require(query.get('id') == tag_id,
            f"meta.query id={query.get('id')!r}, configured tag_id={tag_id!r}")
    return f"{detail} exact_tag_id={query.get('id')}"


def wallpaper_detail(value, wallpaper_id):
    """Check the detail object; uploader and media addresses stay unprinted."""
    detail = fields(value, DETAIL_FIELDS)
    require(value['id'] == wallpaper_id,
            f"wallpaper id={value['id']!r}, requested {wallpaper_id!r}")
    fields(value['thumbs'], THUMB_FIELDS)
    fields(value['uploader'], UPLOADER_FIELDS)
    fields(value['uploader']['avatar'], AVATAR_FIELDS)
    for color in value['colors']:
        require(type(color) is str, f'color: got {type(color).__name__}')
    for tag in value['tags']:
        fields(tag, TAG_FIELDS)
    return (f"{detail} | id={value['id']} "
            f"uploader_group={value['uploader']['group']} "
            f"uploader_username_chars={len(value['uploader']['username'])} "
            f"avatar_keys={sorted(value['uploader']['avatar'])} "
            f"purity={value['purity']} category={value['category']} "
            f"resolution={value['dimension_x']}x{value['dimension_y']} "
            f"views={value['views']} favorites={value['favorites']} "
            f"tags={len(value['tags'])} "
            f"tag_categories={sorted({tag['category'] for tag in value['tags']})} "
            f"colors={len(value['colors'])} thumbs_keys={sorted(value['thumbs'])}")


def tag_detail(value, tag_id):
    """Check one tag object; its name and alias stay unprinted."""
    detail = fields(value, TAG_FIELDS)
    require(value['id'] == tag_id,
            f"tag id={value['id']!r}, requested {tag_id!r}")
    return (f"{detail} | id={value['id']} category={value['category']} "
            f"purity={value['purity']} name_chars={len(value['name'])} "
            f"alias_chars={len(value['alias'])} category_id={value['category_id']}")


def collections(value):
    """The public listing is a bare data array; its size is not pinned."""
    require(type(value) is dict, f'expected object, got {type(value).__name__}')
    fields(value, {'data': list})
    for entry in value['data']:
        fields(entry, COLLECTION_FIELDS)
        require(entry['public'] in (0, 1),
                f"public={entry['public']!r} is not the documented 0/1")
        require(entry['count'] >= 0, f"count={entry['count']}")
    return (f"data:list | collections={len(value['data'])} "
            f"ids={[entry['id'] for entry in value['data']]} "
            f"public={[entry['public'] for entry in value['data']]} "
            f"counts={[entry['count'] for entry in value['data']]}")


def exercise(client, settings):
    from anybooru import AnybooruHTTPError
    from requests import RequestException

    counts = {'requests': 0, 'passed': 0, 'failed': 0}
    # One call = one HTTP attempt: never follow redirects or retry.
    client.client.request = partial(client.client.request, allow_redirects=False)

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

    def missing_error(error):
        """The configured missing id must carry the site's Nothing-here body."""
        require(client.last_call.get('status_code') == error.http_code,
                f"last_call status_code={client.last_call.get('status_code')!r}, "
                f'expected {error.http_code}')
        require(client.last_call.get('url') == error.url,
                f"last_call url={client.last_call.get('url')!r}, expected {error.url!r}")
        require(type(error.data) is dict,
                f'expected a JSON error object, got {type(error.data).__name__}')
        require(error.data.get('error') == 'Nothing here',
                f"error body {error.data.get('error')!r} is not 'Nothing here'")
        content_type = error.response.headers.get('Content-Type', 'no Content-Type')
        return (f"data={type(error.data).__name__} error='Nothing here' "
                f"body_chars={len(error.body)} content_type={content_type!r} "
                f"last_call=HTTP {client.last_call['status_code']} "
                f"{client.last_call['url']}")

    pages = settings['pages']
    search_query = settings['search_query']
    tag_query = settings['tag_query']
    wallpaper_id = settings['wallpaper_id']
    tag_id = settings['tag_id']
    username = settings['username']
    collection_id = settings['collection_id']
    collection_query = settings['collection_query']

    check(f'wallpaper_search page {pages[0]}',
          lambda: client.wallpaper_search(page=pages[0], **search_query),
          lambda value: search_page(value, pages[0], search_query))
    check(f'wallpaper_search page {pages[1]}',
          lambda: client.wallpaper_search(page=pages[1], **search_query),
          lambda value: search_page(value, pages[1], search_query))
    check('wallpaper_search configured exact tag',
          lambda: client.wallpaper_search(**tag_query),
          lambda value: exact_tag_page(value, tag_id, tag_query))
    check('wallpaper_show configured id',
          lambda: client.wallpaper_show(wallpaper_id),
          lambda value: wallpaper_detail(value, wallpaper_id))
    check('tag_show configured id',
          lambda: client.tag_show(tag_id),
          lambda value: tag_detail(value, tag_id))
    check('user_collections configured user',
          lambda: client.user_collections(username),
          collections)
    check('collection_wallpapers configured collection',
          lambda: client.collection_wallpapers(username, collection_id,
                                               **collection_query),
          lambda value: wallpaper_page(value, COLLECTION_META_FIELDS, {},
                                       collection_query.get('page'),
                                       collection_query))
    check('wallpaper_show missing id',
          lambda: client.wallpaper_show(settings['missing_wallpaper_id']),
          missing_error, expected=404)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Wallhaven
        from anybooru.resources import load_config

        smoke = load_config(args.config)['smoke']
        settings = dict(smoke['wallhaven'])
        for key in ('pages', 'pause_seconds'):
            settings.setdefault(key, smoke[key])
        client = Wallhaven(settings['site'], apikey='', config_file=args.config)
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY wallhaven | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; '
              'anonymous apikey=""', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
