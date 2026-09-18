# -*- coding: utf-8 -*-
"""Anonymous smoke checks for safebooru.donmai.us (Danbooru engine).

Budget: 4 HTTP attempts, GET only, no redirects, no retries, no media downloads;
credentials are passed explicitly empty, so the run is anonymous.
Same Danbooru-family parameters as the smoke section's danbooru entry are used.
Checks: posts list (safe tag, limit from the smoke section), one post detail
using the id the list returned, an id cursor page that must be strictly older
and disjoint from page one, and a missing post id that must answer HTTP 404
with success=false plus error/message strings.
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

    safe_tags = settings['danbooru']['tags']
    limit = settings['limit']
    missing_id = settings['missing_id']

    def inspect_post(post):
        require(type(post) is dict, f'expected post object, got {type(post).__name__}')
        detail = fields(post, {'id': int, 'rating': str, 'tag_string': str})
        return f'{detail} tags={len(post["tag_string"].split())}'

    def inspect_page(posts):
        require(type(posts) is list, f'expected list, got {type(posts).__name__}')
        require(len(posts) == limit, f'expected {limit} posts, got {len(posts)}')
        for post in posts:
            inspect_post(post)
        return f'ids={[post["id"] for post in posts]} rating={posts[0]["rating"]}'

    def inspect_detail(post, expected_id):
        summary = inspect_post(post)
        require(post['id'] == expected_id, f'detail id {post["id"]} != listed id {expected_id}')
        return summary

    def inspect_cursor(posts, cursor, seen):
        inspect_page(posts)
        ids = [post['id'] for post in posts]
        require(all(post_id < cursor for post_id in ids),
                f'cursor page contains ids >= {cursor}: {ids}')
        require(not seen.intersection(ids), f'cursor page repeats page one ids: {ids}')
        return f'cursor={cursor} ids={ids}'

    def inspect_missing(error):
        require(type(error.data) is dict,
                f'body is not a JSON object: {type(error.data).__name__}')
        require(error.data.get('success') is False, 'body has no success=false')
        require(type(error.data.get('error')) is str, 'body error is not a string')
        require(type(error.data.get('message')) is str, 'body message is not a string')
        return f'success=false error={error.data["error"]}'

    posts = check('post_list', lambda: client.post_list(tags=safe_tags, limit=limit),
                  inspect_page)

    if posts is None:
        print('SKIP post_show | - | no HTTP | post_list returned no ids', flush=True)
    else:
        post_id = posts[0]['id']
        check('post_show', lambda: client.post_show(post_id),
              lambda post: inspect_detail(post, post_id))

    if posts is None:
        print('SKIP post_list_cursor | - | no HTTP | post_list returned no ids', flush=True)
    else:
        cursor = posts[-1]['id']
        seen = {post['id'] for post in posts}
        check('post_list_cursor',
              lambda: client.post_list(tags=safe_tags, limit=limit, page=f'b{cursor}'),
              lambda page: inspect_cursor(page, cursor, seen))

    check('post_show_missing', lambda: client.post_show(missing_id),
          inspect_missing, expected=404)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Danbooru
        client = Danbooru('safebooru', username='', api_key='', config_file=args.config)
        settings = client.config['smoke']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY safebooru | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
