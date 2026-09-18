"""Zerochan anonymous smoke checks: at most 4 HTTP attempts.

List, matching detail, second page, and a missing entry (HTTP 404).
Baseline: docs/verification.md; the 999999999 boundary was observed on
2026-09-18. No credentials, redirects, retries or media downloads.
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

    site = settings['zerochan']
    limit = settings['limit']
    first_page, second_page = settings['pages'][0], settings['pages'][1]
    entry_fields = {'id': int, 'width': int, 'height': int, 'tag': str,
                    'tags': list}
    detail_fields = {'id': int, 'primary': str, 'full': str, 'width': int,
                     'height': int, 'size': int, 'tags': list}

    def string_list(value, label):
        require(type(value) is list,
                f'{label}: expected list, got {type(value).__name__}')
        for item in value:
            require(type(item) is str,
                    f'{label}: expected str item, got {type(item).__name__}')

    def listing_detail(value, expected_page):
        require(type(value) is list,
                f'expected the items array, got {type(value).__name__}')
        require(len(value) == limit,
                f'expected {limit} entries, got {len(value)}')
        for entry in value:
            fields(entry, entry_fields)
            string_list(entry['tags'], 'tags')
        return (f'entries={len(value)} page={expected_page} '
                f'ids={[entry["id"] for entry in value]}')

    listing = check(
        f'entry_list page {first_page}',
        lambda: client.entry_list(p=first_page, l=limit, s=site['sort']),
        lambda value: listing_detail(value, first_page))

    def detail_detail(value, selected):
        detail = fields(value, detail_fields)
        string_list(value['tags'], 'tags')
        require(value['id'] == selected['id'],
                f'id {value["id"]} does not match the listed {selected["id"]}')
        return (f'{detail} | id={value["id"]} primary={value["primary"]} '
                f'size={value["size"]} full={value["full"]}')

    if listing is None:
        print('SKIP entry_show first id | - | no HTTP | '
              'the page 1 listing failed', flush=True)
    else:
        selected = listing[0]
        check('entry_show first id',
              lambda: client.entry_show(selected['id']),
              lambda value: detail_detail(value, selected))

    def second_listing_detail(value):
        detail = listing_detail(value, second_page)
        if listing is not None:
            listed = {entry['id'] for entry in listing}
            repeated = listed & {entry['id'] for entry in value}
            require(not repeated,
                    f'page {second_page} repeats page {first_page} '
                    f'ids {sorted(repeated)}')
        return detail

    check(
        f'entry_list page {second_page}',
        lambda: client.entry_list(p=second_page, l=limit, s=site['sort']),
        second_listing_detail)

    # Observed missing-entry boundary; a 200 empty body is a failure.
    check('entry_show missing id',
          lambda: client.entry_show(site['missing_id']),
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
        from anybooru import Zerochan
        client = Zerochan('zerochan', config_file=args.config)
        settings = client.config['smoke']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY zerochan | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
