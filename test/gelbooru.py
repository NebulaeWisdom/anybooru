"""Gelbooru anonymous smoke checks: at most 6 HTTP attempts.

1 autocomplete + 5 expected anonymous dapi denials. No login, media,
redirects or retries. Baseline: docs/verification.md, Gelbooru G4/G5.
Autocomplete limit is not a server-side result-count ceiling.
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

    query = settings['gelbooru']

    def suggestions(items):
        require(type(items) is list, f'expected list, got {type(items).__name__}')
        require(len(items) > 0, 'autocomplete returned no suggestions')
        shape = {'type': str, 'label': str, 'value': str,
                 'post_count': str, 'category': str}
        for item in items:
            fields(item, shape)
            require(item['type'] == 'tag', f"suggestion type={item['type']!r}, expected tag")
            require(item['post_count'].isdigit(), 'post_count is not a decimal string')
        return (f"count={len(items)} requested_limit={query['limit']} "
                f"first={items[0]['value']} post_count={items[0]['post_count']!r}; "
                f"{fields(items[0], shape)}")

    def denied(error):
        require(error.body == '' and error.data is None,
                f'expected empty denial body, got {len(error.body)} characters')
        return 'anonymous access denied as expected; body_chars=0 data=None'

    check('autocomplete',
          lambda: client.autocomplete(query['term'], type=query['type'], limit=query['limit']),
          suggestions)
    check('posts.anonymous_denied', lambda: client.post_list(limit=settings['limit']), denied, expected=401)
    check('tags.anonymous_denied', lambda: client.tag_list(limit=settings['limit']), denied, expected=401)
    check('users.anonymous_denied', lambda: client.user_list(limit=settings['limit']), denied, expected=401)
    check('comments.anonymous_denied', lambda: client.comment_list(query['post_id']), denied, expected=401)
    check('deleted.anonymous_denied', lambda: client.post_deleted(last_id=query['last_id']), denied, expected=401)
    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Gelbooru
        client = Gelbooru('gelbooru', config_file=args.config, api_key='', user_id='')
        settings = client.config['smoke']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY gelbooru | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
