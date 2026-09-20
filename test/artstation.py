"""ArtStation anonymous smoke checks: exactly ten HTTP attempts.

Ten read-only GETs against ``https://www.artstation.com``, every parameter
taken from ``smoke.artstation``: one ``projects.json`` page at the configured
``per_page``, two ``users/{username}/projects.json`` pages (the configured
page numbers, the same ``per_page``), ``random_project.json``, one
``api/v2/search/projects.json`` query, the bare
``api/v2/search/projects/filter_fields.json`` array,
``api/v2/community/projects/by_album.json`` for the configured album,
``artwork.rss`` for the configured ``sorting``, and two expected failures --
``users/{username}.json`` for a username the site has no account for (HTTP
404, plain text, empty body) and the same project search with a ``per_page``
below the route's minimum (HTTP 400 carrying ``{"message", "code"}``). Both
failures are inspected through ``AnybooruHTTPError`` and never converted into
successful data.

The listing routes do not return the same item shape and are checked apart:
``projects.json`` items carry an embedded ``user`` object and ``views_count``,
the user's project items do not, so only the fields that route really returns
are required. Both are checked against their envelope keys, item types, ids
and the requested ``per_page`` as an upper bound; the two pages are not
required to be disjoint, because the global listing is live and mutates while
the run is in flight. ``random_project.json`` returns one bare project object
whose ``tags`` is only required to be a list -- the sampled one was empty, so
no tag element type is asserted -- and whose assets are read from keys the
sample carries. Search items are the reduced 9-field card shape, the
filter-field array is a bare array of ``{"name", "type"}`` objects (extra keys
such as ``select_options`` are not assumed, only that a ``title`` filter is
still listed), the album listing returns its own item shape with
``album_id``/``album_title``/``assets``,
and the feed is consumed as the RSS text itself (XML declaration, ``<rss>``
element and an XML ``Content-Type``), not as decoded JSON.

No phrase, total, id, null or empty array is pinned beyond what the routes
established: ``total_count`` is only required to be a non-negative integer,
the 404 is consumed as an empty body with ``data is None`` and ``last_call``
kept, and the 400 only as that two-key object with both values strings.
Redirects are disabled and no request is retried, the client sends nothing but
these GETs, and every call pauses for the configured number of seconds before
it is sent, the first call included.
Baseline: docs/verification.md#artstation匿名只读实测2026-09-20.
"""

import argparse
from functools import partial
import time


GLOBAL_ENVELOPE = {'data': list, 'total_count': int}
GLOBAL_ITEM_FIELDS = {'id': int, 'hash_id': str, 'title': str,
                      'permalink': str, 'assets_count': int, 'cover': dict,
                      'tag_list': (list, type(None)), 'user': dict,
                      'views_count': int}
USER_ITEM_FIELDS = {'id': int, 'hash_id': str, 'title': str,
                    'permalink': str, 'assets_count': int, 'cover': dict,
                    'tag_list': (list, type(None))}
RANDOM_FIELDS = {'id': int, 'hash_id': str, 'title': str, 'permalink': str,
                 'tags': list, 'assets': list, 'user': dict, 'cover': dict}
SEARCH_ENVELOPE = {'total_count': int, 'data': list}
SEARCH_ITEM_FIELDS = {'id': int, 'hash_id': str, 'url': str,
                      'smaller_square_cover_url': str, 'hide_as_adult': bool,
                      'is_adult_content': bool, 'title': str, 'icons': dict,
                      'user': dict}
FILTER_ITEM_FIELDS = {'name': str, 'type': str}
ALBUM_ITEM_FIELDS = {'id': int, 'hash_id': str, 'title': str, 'permalink': str,
                     'album_id': int, 'album_title': str, 'cover': dict,
                     'assets': list}
SEARCH_ERROR_FIELDS = {'message': str, 'code': str}


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def fields(value, expected):
    require(type(value) is dict, f'expected object, got {type(value).__name__}')
    for key, kind in expected.items():
        require(key in value, f'missing field {key}')
        kinds = kind if isinstance(kind, tuple) else (kind,)
        require(type(value[key]) in kinds,
                f'{key}: expected {"/".join(item.__name__ for item in kinds)}, '
                f'got {type(value[key]).__name__}')
    return ','.join(f'{key}:{value[key].__class__.__name__}' for key in expected)


def page_items(value, query):
    """Check the shared listing envelope and return its bounded item list."""
    detail = fields(value, GLOBAL_ENVELOPE)
    per_page = query['per_page']
    items = value['data']
    require(value['total_count'] >= 0,
            f"total_count={value['total_count']!r} is negative")
    require(0 < len(items) <= per_page,
            f'per_page={per_page} but {len(items)} projects came back')
    for item in items:
        require(item['permalink'].startswith('http'),
                f"permalink={item['permalink']!r} is not an absolute URL")
    return detail, items


def exercise(client, settings):
    from anybooru import AnybooruHTTPError
    from requests import RequestException

    counts = {'requests': 0, 'passed': 0, 'failed': 0}
    # One call = one HTTP attempt: never follow redirects or retry.
    client.client.request = partial(client.client.request, allow_redirects=False)

    def check(name, call, inspect, expected=200):
        # Every call pauses first, the first one included: a run never sends
        # a request the moment the previous process ended.
        time.sleep(settings['pause_seconds'])
        counts['requests'] += 1
        client.last_call = {}
        url, status = '-', 'no HTTP response'
        try:
            try:
                result = call()
            except AnybooruHTTPError as error:
                url, status = error.url, f'HTTP {error.http_code}'
                require(error.http_code == expected,
                        f'expected HTTP {expected}; AnybooruHTTPError; body_chars={len(error.body)}')
                detail = inspect(error)
                status += ' AnybooruHTTPError (expected)'
            else:
                url = client.last_call['url']
                status = (f"HTTP {client.last_call['status_code']} "
                          f"{client.last_call['headers'].get('Content-Type', 'no Content-Type')}")
                require(client.last_call['status_code'] == expected,
                        f'expected HTTP {expected}')
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
        return result if expected == 200 else None

    def global_page(value, query):
        """projects.json item: global list adds user and views_count."""
        detail, items = page_items(value, query)
        for item in items:
            fields(item, GLOBAL_ITEM_FIELDS)
        first = items[0]
        return (f"{detail} | per_page<={query['per_page']} count={len(items)} "
                f"total_count={value['total_count']} ids={[item['id'] for item in items]} "
                f"first: id={first['id']} hash_id={first['hash_id']} "
                f"title={first['title']!r} assets_count={first['assets_count']} "
                f"tag_list={type(first['tag_list']).__name__} "
                f"user={first['user']['username']} views_count={first['views_count']}")

    def user_page(value, query, username):
        """users/{username}/projects.json item: no user/views_count."""
        detail, items = page_items(value, query)
        for item in items:
            fields(item, USER_ITEM_FIELDS)
        first = items[0]
        return (f"{detail} | user={username} per_page<={query['per_page']} "
                f"count={len(items)} total_count={value['total_count']} "
                f"ids={[item['id'] for item in items]} first: id={first['id']} "
                f"hash_id={first['hash_id']} title={first['title']!r} "
                f"assets_count={first['assets_count']} "
                f"tag_list={type(first['tag_list']).__name__} "
                f"cover_keys={len(first['cover'])} item_keys={len(first)}")

    def random_project(value):
        """random_project.json: one bare project object, not a list card."""
        detail = fields(value, RANDOM_FIELDS)
        assets = value['assets']
        asset = (f"id={assets[0]['id']} asset_type={assets[0]['asset_type']} "
                 f"width={assets[0]['width']} height={assets[0]['height']}"
                 if assets else 'none')
        return (f"{detail} | id={value['id']} hash_id={value['hash_id']} "
                f"title={value['title']!r} permalink={value['permalink']} "
                f"tags={value['tags']} assets={len(assets)} first_asset={asset} "
                f"user={value['user']['username']} cover_id={value['cover']['id']}")

    def search_page(value, query):
        """api/v2/search/projects.json: reduced card shape."""
        detail = fields(value, SEARCH_ENVELOPE)
        items = value['data']
        per_page = query['per_page']
        require(value['total_count'] >= 0,
                f"total_count={value['total_count']!r} is negative")
        require(0 < len(items) <= per_page,
                f'per_page={per_page} but {len(items)} results came back')
        for item in items:
            fields(item, SEARCH_ITEM_FIELDS)
            require(item['url'].startswith('http')
                    and item['smaller_square_cover_url'].startswith('http'),
                    'search card carries a non-absolute media URL')
        first = items[0]
        return (f"{detail} | per_page<={per_page} count={len(items)} "
                f"total_count={value['total_count']} ids={[item['id'] for item in items]} "
                f"first: id={first['id']} hash_id={first['hash_id']} "
                f"title={first['title']!r} url={first['url']} "
                f"is_adult_content={first['is_adult_content']} "
                f"hide_as_adult={first['hide_as_adult']} "
                f"user={first['user']['username']}")

    def filter_fields(value):
        """filter_fields.json: bare array; select_options is not on every item."""
        require(type(value) is list,
                f'expected a bare array, got {type(value).__name__}')
        require(value, 'filter_fields returned an empty array')
        for item in value:
            fields(item, FILTER_ITEM_FIELDS)
        names = [item['name'] for item in value]
        require('title' in names,
                f'the title filter is gone; names={names}')
        return f'items={len(value)} names={names}'

    def album_page(value, query, album_id):
        """by_album.json: album items have their own shape with album_id."""
        detail, items = page_items(value, query)
        for item in items:
            fields(item, ALBUM_ITEM_FIELDS)
            require(item['album_id'] == album_id,
                    f"album_id={item['album_id']}, requested {album_id}")
        first = items[0]
        return (f"{detail} | album_id={album_id} per_page<={query['per_page']} "
                f"count={len(items)} total_count={value['total_count']} "
                f"ids={[item['id'] for item in items]} first: id={first['id']} "
                f"hash_id={first['hash_id']} title={first['title']!r} "
                f"album_title={first['album_title']!r} "
                f"assets={len(first['assets'])}")

    def feed_xml(value):
        require(type(value) is str,
                f'expected the RSS text, got {type(value).__name__}')
        require(value.lstrip().startswith('<?xml'),
                'the returned text does not open with an XML declaration')
        require('<rss' in value, 'no <rss> element in the returned text')
        content_type = client.last_call['headers'].get('Content-Type', 'no Content-Type')
        require('xml' in content_type.lower(),
                f'Content-Type={content_type!r} is not XML')
        return (f"chars={len(value)} items={value.count('<item>')} "
                f"content_type={content_type!r}")

    def missing_user(error, username):
        """Consume the 404 without asserting the site's own wording."""
        require(client.last_call.get('status_code') == error.http_code,
                f"last_call status_code={client.last_call.get('status_code')!r}, "
                f'expected {error.http_code}')
        require(client.last_call.get('url') == error.url,
                f"last_call url={client.last_call.get('url')!r}, expected {error.url!r}")
        require(error.data is None,
                f'expected no decoded body, got {type(error.data).__name__}')
        require(not error.body,
                f'expected an empty body, got {len(error.body)} chars')
        content_type = error.response.headers.get('Content-Type', 'no Content-Type')
        return (f'user={username} data={type(error.data).__name__} '
                f'body_chars={len(error.body)} content_type={content_type!r} '
                f'last_call=HTTP {error.http_code} {error.url}')

    def invalid_search(error):
        """The 400 keeps the site's own {"message", "code"} types, no text."""
        require(client.last_call.get('status_code') == error.http_code,
                f"last_call status_code={client.last_call.get('status_code')!r}, "
                f'expected {error.http_code}')
        require(client.last_call.get('url') == error.url,
                f"last_call url={client.last_call.get('url')!r}, expected {error.url!r}")
        detail = fields(error.data, SEARCH_ERROR_FIELDS)
        content_type = error.response.headers.get('Content-Type', 'no Content-Type')
        return (f'{detail} | code={error.data["code"]!r} '
                f'message_chars={len(error.data["message"])} '
                f'body_chars={len(error.body)} content_type={content_type!r}')

    project_query = settings['project_query']
    user_project_query = settings['user_project_query']
    username = settings['username']
    pages = settings['pages']
    search_query = settings['search_query']
    album_id = settings['album_id']
    album_query = settings['album_query']
    feed_query = settings['feed_query']

    check('project_list configured page',
          lambda: client.project_list(**project_query),
          lambda value: global_page(value, project_query))
    check(f'user_projects page {pages[0]}',
          lambda: client.user_projects(username, page=pages[0], **user_project_query),
          lambda value: user_page(value, user_project_query, username))
    check(f'user_projects page {pages[1]}',
          lambda: client.user_projects(username, page=pages[1], **user_project_query),
          lambda value: user_page(value, user_project_query, username))
    check('project_random', client.project_random, random_project)
    check('project_search configured query',
          lambda: client.project_search(**search_query),
          lambda value: search_page(value, search_query))
    check('search_filter_fields', client.search_filter_fields, filter_fields)
    check('album_projects configured album',
          lambda: client.album_projects(album_id, **album_query),
          lambda value: album_page(value, album_query, album_id))
    check('feed configured sorting',
          lambda: client.feed(**feed_query), feed_xml)
    check('user_show missing username',
          lambda: client.user_show(settings['missing_username']),
          lambda error: missing_user(error, settings['missing_username']),
          expected=404)
    check('project_search per_page below minimum',
          lambda: client.project_search(**settings['invalid_search_query']),
          invalid_search, expected=400)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import ArtStation
        from anybooru.resources import load_config
        settings = load_config(args.config)['smoke']['artstation']
        client = ArtStation(settings['site'], config_file=args.config)
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY artstation | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; '
              'anonymous, no credentials', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
