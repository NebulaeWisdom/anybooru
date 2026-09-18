# -*- coding: utf-8 -*-
"""Anonymous smoke checks for konachan.com (Moebooru engine).

Budget: 4 GETs, one API call per check, no redirects, no retries, no media
downloads, no extra requests:

  1. post_list(tags='rating:s', page=1, limit=2, api_version=2) -> 200 and the
     version-2 envelope {"posts": [...]} holds exactly `limit` posts; every post
     has id:int, rating:str, tags:str, width:int, height:int and the ids descend
     (the index is ordered by p.id DESC).
  2. post_list(tags='id:<id from check 1>') -> exactly one post, same id.
     There is no JSON post_show route, so the id search is the detail read.
  3. post_list(page=2, same tags/limit/api_version) -> a full page whose ids are
     all earlier than page 1 and share no id with it.
  4. comment_show(0) -> HTTP 404 and a JSON object. Konachan differs from
     yande.re, whose observed 404 body is HTML (data is None). Konachan's
     JSON carries status (integer 404) and error (string).

Construction is anonymous on purpose: username='' and password='' are passed
explicitly, so the run never depends on the config happening to hold empty
credentials. The client still reads url, api_version and hash_string from
sites.konachan, and every query value comes from the root smoke section.
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

    moebooru_settings = settings['moebooru']
    limit = settings['limit']
    post_fields = {'id': int, 'rating': str, 'tags': str, 'width': int, 'height': int}

    def page_of(page):
        return client.post_list(tags=moebooru_settings['tags'], page=page, limit=limit,
                                api_version=moebooru_settings['api_version'])

    def posts_of(value):
        require(type(value) is dict, f'expected object, got {type(value).__name__}')
        require('posts' in value, 'missing field posts')
        require(type(value['posts']) is list,
                f"posts: expected list, got {type(value['posts']).__name__}")
        return value['posts']

    def inspect_page(value):
        posts = posts_of(value)
        require(len(posts) == limit, f'posts: expected {limit}, got {len(posts)}')
        for post in posts:
            fields(post, post_fields)
        ids = [post['id'] for post in posts]
        require(ids == sorted(ids, reverse=True), f'ids: expected descending, got {ids}')
        return f'posts={len(posts)} ids={ids} {fields(posts[0], post_fields)}'

    def inspect_post(value):
        posts = posts_of(value)
        require(len(posts) == 1, f'posts: expected 1, got {len(posts)}')
        require(posts[0]['id'] == post_id, f'id: expected {post_id}, got {posts[0]["id"]}')
        return f'posts=1 selected_id={post_id} {fields(posts[0], post_fields)}'

    def inspect_missing(data):
        fields(data, {'status': int, 'error': str})
        require(data['status'] == 404,
                f'expected error status 404, got {data["status"]!r}')
        return f'AnybooruHTTPError; data=dict; error={data!r}'

    first_page = check(f'post_list page {settings["pages"][0]}',
                       lambda: page_of(settings['pages'][0]), inspect_page)
    if first_page is None:
        print('SKIP post_list id | - | no HTTP | page 1 returned no ids', flush=True)
        print('SKIP post_list page 2 | - | no HTTP | page 1 returned no ids', flush=True)
    else:
        post_id = first_page['posts'][0]['id']
        check(f'post_list id:{post_id}',
              lambda: client.post_list(tags=f'id:{post_id}', limit=limit,
                                       api_version=moebooru_settings['api_version']),
              inspect_post)

        page_one_ids = [post['id'] for post in first_page['posts']]

        def inspect_page_two(value):
            posts = posts_of(value)
            require(len(posts) == limit, f'posts: expected {limit}, got {len(posts)}')
            for post in posts:
                fields(post, post_fields)
            page_two_ids = [post['id'] for post in posts]
            require(not set(page_two_ids) & set(page_one_ids),
                    f'page 2 overlaps page 1: {page_two_ids} vs {page_one_ids}')
            require(max(page_two_ids) < min(page_one_ids),
                    f'page 2 ids not earlier: {max(page_two_ids)} vs {min(page_one_ids)}')
            return f'posts={len(posts)} ids={page_two_ids} earlier_than={min(page_one_ids)}'

        check(f'post_list page {settings["pages"][1]}',
              lambda: page_of(settings['pages'][1]), inspect_page_two)

    check(f'comment_show {settings["missing_id"]}',
          lambda: client.comment_show(settings['missing_id']),
          lambda error: inspect_missing(error.data), expected=404)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Moebooru
        client = Moebooru('konachan', username='', password='',
                          config_file=args.config)
        settings = client.config['smoke']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY konachan | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
