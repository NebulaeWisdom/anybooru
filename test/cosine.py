"""Cosine anonymous smoke checks: at most 10 HTTP attempts.

Ten read-only GETs against ``https://pic.cosine.ren``, every parameter taken
from ``smoke.cosine``: two ``/api/list`` pages at the configured ``pageSize``,
``/api/artwork/{artwork_id}``, ``/api/random`` at each configured ``count``,
``/api/search`` for the configured query, ``/api/tag`` for the configured tag,
``/api/tags``, ``/feed.xml``, and a missing artwork id, which the site answers
with HTTP 404.

The four response envelopes are consumed exactly as the site sends them. The
superjson wrapper ``{json, meta}`` carries a single object for ``count=1`` and
an array for ``count=3``, so ``json`` is checked as an object in the first case
and as an array of the requested length in the second; ``/api/list`` answers
``{images, total}``; ``/api/search`` answers ``{success, data}`` with ``hits``,
``query``, ``total``, ``limit``, ``offset`` and ``processingTimeMs`` inside
``data``; ``/api/tag`` and ``/api/tags`` answer bare arrays (artworks, and
``{tag, count}`` pairs). ``feed`` is requested as XML, so the check requires the
RSS text itself -- a string that still opens with its XML declaration -- and not
a decoded object. Search hits are checked for the two shapes the client docs
call out: a string ``id`` and a list of string ``tags``.

The two additions the random route makes to an artwork are checked because the
client documents them: ``originUrl`` and ``authorUrl`` are present and absolute,
and ``rawurl`` no longer points at ``i.pximg.net``. Nothing else about media
fields is asserted, no random id, site total, tag name or count is pinned, and
the first two pages are only required not to repeat an artwork id.

The client is built with an explicit empty ``revalidate_secret``, so the run
stays anonymous whatever the configuration holds. Redirects are disabled and no
request is retried; consecutive calls pause for the configured number of
seconds. The missing artwork is expected to raise the shared HTTP error for
HTTP 404: only the status, its recording in ``last_call`` and the body size are
consumed, never the site's wording.
Baseline: docs/verification.md#cosine匿名只读实测2026-09-20.
"""

import argparse
from functools import partial
import time


NUMBER = (int, float)
ARTWORK_FIELDS = {'id': int, 'pid': str, 'platform': str, 'page': int,
                  'authorid': str, 'userid': str, 'create_time': str,
                  'rawurl': str, 'thumburl': str, 'tags': list}
RANDOM_FIELDS = {'originUrl': str, 'authorUrl': str}
LIST_ENVELOPE = {'images': list, 'total': int}
SUPERJSON_ENVELOPE = {'json': (dict, list), 'meta': dict}
SEARCH_ENVELOPE = {'success': bool, 'data': dict}
SEARCH_DATA_FIELDS = {'hits': list, 'query': str, 'total': int, 'limit': int,
                      'offset': int, 'processingTimeMs': NUMBER}
SEARCH_HIT_FIELDS = {'id': str, 'platform': str, 'pid': str,
                     'tags': list, 'rawurl': str, 'thumburl': str,
                     'searchable_content': str, '_formatted': dict}
TAG_LIST_FIELDS = {'tag': str, 'count': int}


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


def present(value, keys):
    """Require key presence for fields whose type the contract does not fix."""
    for key in keys:
        require(key in value, f'missing field {key}')


def artwork_entity(value):
    """Check the keys shared by every artwork object, listed or wrapped."""
    detail = fields(value, ARTWORK_FIELDS)
    for tag in value['tags']:
        require(type(tag) is str,
                f'expected a tag string, got {type(tag).__name__}')
    return detail


def exercise(client, settings):
    from anybooru import AnybooruHTTPError
    from requests import RequestException

    counts = {'requests': 0, 'passed': 0, 'failed': 0}
    # One call = one HTTP attempt: never follow redirects or retry.
    client.client.request = partial(client.client.request, allow_redirects=False)

    def check(name, call, inspect, expected=200):
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

    def list_page(value, page, previous=None, previous_page=None):
        detail = fields(value, LIST_ENVELOPE)
        for image in value['images']:
            artwork_entity(image)
        ids = [image['id'] for image in value['images']]
        relation = 'no earlier page to compare'
        if previous is not None:
            repeated = sorted({image['id'] for image in previous['images']} & set(ids))
            require(not repeated,
                    f'page {page} repeats artwork ids of page {previous_page}: {repeated}')
            relation = f'no id shared with page {previous_page}'
        first = value['images'][0] if value['images'] else None
        lead = (f"first={first['id']} pid={first['pid']} platform={first['platform']} "
                f"page={first['page']} rawurl={first['rawurl']}") if first else 'first=none'
        return (f"{detail} | page={page} total={value['total']} "
                f"images={len(value['images'])} ids={ids} {lead} | {relation}")

    def wrapped_artwork(value, artwork_id):
        detail = fields(value, SUPERJSON_ENVELOPE)
        present(value['meta'], ['values'])
        require(type(value['meta']['values']) is dict,
                f"meta.values: expected dict, got {type(value['meta']['values']).__name__}")
        artwork = value['json']
        require(type(artwork) is dict,
                f'expected one artwork object, got {type(artwork).__name__}')
        artwork_entity(artwork)
        require(artwork['id'] == artwork_id,
                f"artwork.id={artwork['id']}, requested {artwork_id}")
        return (f"{detail} | meta_keys={sorted(value['meta'])} "
                f"values={len(value['meta']['values'])} id={artwork['id']} "
                f"pid={artwork['pid']} platform={artwork['platform']} "
                f"page={artwork['page']} tags={len(artwork['tags'])}")

    def wrapped_random(value, count):
        detail = fields(value, SUPERJSON_ENVELOPE)
        present(value['meta'], ['values'])
        payload = value['json']
        if count == 1:
            require(type(payload) is dict,
                    f'count=1: expected a single artwork object, got {type(payload).__name__}')
            artworks = [payload]
        else:
            require(type(payload) is list,
                    f'count={count}: expected an array, got {type(payload).__name__}')
            require(len(payload) == count,
                    f'count={count}: got {len(payload)} artworks')
            artworks = payload
        for artwork in artworks:
            artwork_entity(artwork)
            fields(artwork, RANDOM_FIELDS)
            for key in RANDOM_FIELDS:
                require(artwork[key].startswith('http'),
                        f'{key}={artwork[key]!r} is not an absolute URL')
            require('i.pximg.net' not in artwork['rawurl'],
                    f'random rawurl still points at i.pximg.net: {artwork["rawurl"]}')
        return (f"{detail} | count={count} json={type(payload).__name__} "
                f"artworks={len(artworks)} ids={[artwork['id'] for artwork in artworks]} "
                f"hosts={sorted({artwork['rawurl'].split('/')[2] for artwork in artworks})}")

    def search_page(value, query):
        detail = (fields(value, SEARCH_ENVELOPE) + ' | '
                  + fields(value['data'], SEARCH_DATA_FIELDS))
        require(value['success'] is True, f"success={value['success']!r}, expected true")
        data = value['data']
        require(data['query'] == query['q'],
                f"query={data['query']!r}, requested {query['q']!r}")
        require(data['limit'] == query['limit'],
                f"limit={data['limit']}, requested {query['limit']}")
        for hit in data['hits']:
            fields(hit, SEARCH_HIT_FIELDS)
            for tag in hit['tags']:
                require(type(tag) is str,
                        f'expected a tag string, got {type(tag).__name__}')
        return (f"{detail} | query={data['query']!r} total={data['total']} "
                f"limit={data['limit']} offset={data['offset']} "
                f"processingTimeMs={data['processingTimeMs']} hits={len(data['hits'])} "
                f"hit_ids={[hit['id'] for hit in data['hits']]}")

    def tag_images_page(value, tag, query):
        require(type(value) is list,
                f'expected a bare array, got {type(value).__name__}')
        require(len(value) <= query['limit'],
                f"limit={query['limit']} but {len(value)} artworks came back")
        for image in value:
            artwork_entity(image)
        return (f"items={len(value)} ids={[image['id'] for image in value]} "
                f"tag={tag!r} start={query['start']} limit={query['limit']}")

    def tag_list_page(value):
        require(type(value) is list,
                f'expected a bare array, got {type(value).__name__}')
        require(value, 'tag_list returned an empty array')
        for item in value:
            fields(item, TAG_LIST_FIELDS)
        first = value[0]
        return (f"items={len(value)} first={first['tag']!r}/{first['count']} "
                f"names={[item['tag'] for item in value[:5]]}")

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

    def missing_artwork(error):
        """Consume the 404 without asserting the site's own wording."""
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
    tag_query = settings['tag_query']

    first_page = check(f'image_list page {pages[0]}',
                       lambda: client.image_list(page=pages[0], **list_query),
                       lambda value: list_page(value, pages[0]))
    check(f'image_list page {pages[1]}',
          lambda: client.image_list(page=pages[1], **list_query),
          lambda value: list_page(value, pages[1], previous=first_page,
                                  previous_page=pages[0]))
    check('artwork_show configured id',
          lambda: client.artwork_show(settings['artwork_id']),
          lambda value: wrapped_artwork(value, settings['artwork_id']))
    for count in settings['random_counts']:
        check(f'image_random count {count}',
              lambda count=count: client.image_random(count=count),
              lambda value, count=count: wrapped_random(value, count))
    check('search configured query', lambda: client.search(**search_query),
          lambda value: search_page(value, search_query))
    check('tag_images configured tag',
          lambda: client.tag_images(settings['tag'], **tag_query),
          lambda value: tag_images_page(value, settings['tag'], tag_query))
    check('tag_list', client.tag_list, tag_list_page)
    check('feed', client.feed, feed_xml)
    check('artwork_show missing id',
          lambda: client.artwork_show(settings['missing_id']),
          missing_artwork, expected=404)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Cosine
        client = Cosine('cosine', revalidate_secret='', config_file=args.config)
        settings = client.config['smoke']['cosine']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY cosine | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; '
              'anonymous revalidate_secret=""', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
