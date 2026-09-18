"""Serika (serika.art) smoke checks: 5 anonymous GET attempts.

Calls, in order:
  1. api_index() -- official /api/v1 index; name and version must be
     non-empty strings (the version is read, never pinned to a fixed value).
  2. internal_image_list(page=1, limit, ratings, sort) -- the station's own
     JSON: {"success": true, "images": [...], "pagination": {...}}, with
     pagination.page/limit matching the query, total/pages int and has_next
     bool; every image carries id/post_id (the two different id spaces) as
     int plus rating/url as str.
  3. internal_image_show(post_id of the first listed image) -- the detail
     route takes the public post_id, not the internal id; the returned image
     repeats the same id/post_id and the same field types.
  4. internal_image_list(page=2, ...) -- same structure, and its post_id set
     must not repeat page 1's.
  5. internal_image_show(smoke.missing_id) -- expected HTTP 404; the route
     answers 404 for a missing, deleted or unlisted image.

smoke.limit (2) and smoke.pages drive the sizes and page numbers,
smoke.serika supplies ratings/sort. The client is constructed with an
explicit empty api_key, so every call here is anonymous; GET only, redirects
disabled, no retry, and exactly one call per check.
"""

import argparse
from functools import partial
import time


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def fields(value, expected):
    require(type(value) is dict, f'expected object, got {type(value).__name__}')
    for key, kind in expected.items():
        require(key in value, f'missing field {key}')
        require(type(value[key]) is kind,
                f'{key}: expected {kind.__name__}, got {type(value[key]).__name__}')
    return ','.join(f'{key}:{kind.__name__}' for key, kind in expected.items())


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
                status = f"HTTP {client.last_call['status_code']}"
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

    site = settings['serika']
    limit = settings['limit']
    first_page, second_page = settings['pages'][0], settings['pages'][1]
    image_fields = {'id': int, 'post_id': int, 'rating': str, 'url': str}
    pagination_fields = {'page': int, 'limit': int, 'total': int,
                         'pages': int, 'has_next': bool}

    def index_detail(value):
        detail = fields(value, {'name': str, 'version': str})
        require(value['name'] != '' and value['version'] != '',
                'name/version must be non-empty strings')
        return f'{detail} | name={value["name"]} version={value["version"]}'

    def listing_detail(value, expected_page):
        detail = fields(value, {'success': bool, 'images': list,
                                'pagination': dict})
        require(value['success'] is True, 'success must be true')
        require(len(value['images']) == limit,
                f'expected {limit} images, got {len(value["images"])}')
        pagination = value['pagination']
        page_detail = fields(pagination, pagination_fields)
        require(pagination['page'] == expected_page,
                f'pagination.page is {pagination["page"]}, '
                f'expected {expected_page}')
        require(pagination['limit'] == limit,
                f'pagination.limit is {pagination["limit"]}, '
                f'expected {limit}')
        for image in value['images']:
            fields(image, image_fields)
        ids = [image['post_id'] for image in value['images']]
        return (f'{detail} | images={len(value["images"])} post_ids={ids} '
                f'pagination:{page_detail} total={pagination["total"]} '
                f'pages={pagination["pages"]} has_next={pagination["has_next"]}')

    check('api_index', client.api_index, index_detail)

    listing = check(
        f'internal_image_list page {first_page}',
        lambda: client.internal_image_list(page=first_page, limit=limit,
                                           ratings=site['ratings'],
                                           sort=site['sort']),
        lambda value: listing_detail(value, first_page))

    def second_listing_detail(value):
        detail = listing_detail(value, second_page)
        if listing is not None:
            listed = {image['post_id'] for image in listing['images']}
            repeated = listed & {image['post_id'] for image in value['images']}
            require(not repeated,
                    f'page {second_page} repeats page {first_page} '
                    f'post_ids {sorted(repeated)}')
        return detail

    def detail_detail(value, selected):
        fields(value, {'success': bool, 'image': dict})
        require(value['success'] is True, 'success must be true')
        image = value['image']
        detail = fields(image, image_fields)
        require(image['post_id'] == selected['post_id'],
                f'post_id {image["post_id"]} does not match '
                f'the listed {selected["post_id"]}')
        require(image['id'] == selected['id'],
                f'internal id {image["id"]} does not match '
                f'the listed {selected["id"]}')
        return (f'{detail} | id={image["id"]} post_id={image["post_id"]} '
                f'rating={image["rating"]} url={image["url"]}')

    if listing is None:
        print('SKIP internal_image_show first post_id | - | no HTTP | '
              'the page 1 listing failed', flush=True)
    else:
        selected = listing['images'][0]
        check('internal_image_show first post_id',
              lambda: client.internal_image_show(selected['post_id']),
              lambda value: detail_detail(value, selected))

    check(
        f'internal_image_list page {second_page}',
        lambda: client.internal_image_list(page=second_page, limit=limit,
                                           ratings=site['ratings'],
                                           sort=site['sort']),
        second_listing_detail)

    check('internal_image_show missing id',
          lambda: client.internal_image_show(settings['missing_id']),
          lambda error: (f'AnybooruHTTPError; body_chars={len(error.body)} '
                         f'data={type(error.data).__name__}'),
          expected=404)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Serika
        client = Serika('serika', api_key='', config_file=args.config)
        settings = client.config['smoke']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY serika | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
