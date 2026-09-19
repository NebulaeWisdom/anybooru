"""Sakuria anonymous smoke checks: at most 10 HTTP attempts.

Ten read-only GETs against the Sakuria API host: ``/stats``, two
``/search/illust`` pages, ``/illust/{id}`` for the first id listed on page 1,
``/search/novel``, ``/spotlight``, ``/illust/{id}/comments`` for the
configured illust id, and ``/users/{id}`` for that illust's author, plus two
expected failures -- a missing illust id (HTTP 404) and a rejected ``size``
value (HTTP 400 whose body carries ``field='size'``). Expected failures are
inspected through AnybooruHTTPError, not converted to successful data.

List envelopes are checked for the documented keys and types only: no count
bound and no "page 1 and page 2 do not overlap" assertion, because the site
reports inconsistent ``total``/``pageSize``/``nextPage`` values. The detail
lookup skips when the first listing failed or came back empty, and the author
lookup skips when the detail failed; skipped calls send no request. Every
parameter comes from the ``smoke.sakuria`` configuration and the client is
constructed with an explicit empty ``access_token``, so the requests stay
anonymous. No credentials, media, redirects or retries.
Baseline: docs/verification.md#sakuria匿名只读实测2026-09-19.
"""

import argparse
from functools import partial
import time


NUMBER = (int, float)
STATS_FIELDS = {'likes': int, 'bookmarks': int, 'views': int, 'comments': int}
USER_STATS_FIELDS = {'followers': int, 'following': int, 'works': int,
                     'totalLikes': int, 'totalBookmarks': int}
AUTHOR_FIELDS = {'id': str, 'name': str, 'handle': str, 'accent': str,
                 'avatar': str, 'stats': dict}
AUTHOR_BRIEF_FIELDS = {'id': str, 'name': str, 'handle': str, 'accent': str,
                       'avatar': str}
URL_FIELDS = {'thumb': str, 'small': str, 'regular': str, 'original': str,
              'w': NUMBER, 'h': NUMBER}
ILLUSTR_FIELDS = {'id': str, 'title': str, 'type': str, 'pages': NUMBER,
                  'urls': dict, 'author': dict, 'tags': list, 'stats': dict,
                  'publishedAt': str, 'publishedDays': NUMBER, 'isAi': bool,
                  'isR18': bool, 'xRestrict': NUMBER, 'sl': NUMBER}
NOVEL_FIELDS = {'id': str, 'title': str, 'author': dict, 'tags': list,
                'textLength': NUMBER, 'cover': dict, 'stats': dict,
                'publishedAt': str, 'publishedDays': NUMBER, 'isAi': bool,
                'isR18': bool, 'xRestrict': NUMBER, 'sl': NUMBER}
COMMENT_FIELDS = {'author': dict, 'text': str, 'repliesCount': int,
                  'likes': int, 'createdAt': str, 'timeLabel': str}


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


def illust_entity(value):
    """Check the keys shared by every place an Illust object appears."""
    detail = fields(value, ILLUSTR_FIELDS)
    urls = value['urls']
    fields(urls, URL_FIELDS)
    for size in ('thumb', 'small', 'regular', 'original'):
        require(urls[size].startswith('/img/'),
                f'urls.{size}={urls[size]!r} is not a documented /img/ relative path')
    fields(value['author'], AUTHOR_FIELDS)
    fields(value['author']['stats'], USER_STATS_FIELDS)
    for tag in value['tags']:
        fields(tag, {'name': str, 'alt': int})
        if 'translated' in tag:
            require(type(tag['translated']) is str,
                    'tags[].translated: expected str, got '
                    f'{type(tag["translated"]).__name__}')
    fields(value['stats'], STATS_FIELDS)
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

    def stats_detail(value):
        detail = fields(value, {'newToday': int, 'totalIllusts': int,
                                'totalCreators': int, 'totalUsers': int})
        return (f"{detail} | newToday={value['newToday']} "
                f"totalIllusts={value['totalIllusts']} "
                f"totalCreators={value['totalCreators']} "
                f"totalUsers={value['totalUsers']}")

    def search_page(value, page):
        detail = fields(value, {'items': list, 'page': int, 'pageSize': int,
                                'total': int, 'totalPages': int, 'hasMore': bool})
        require(value['page'] == page, f"page={value['page']}, requested {page}")
        for item in value['items']:
            illust_entity(item)
        first = value['items'][0] if value['items'] else None
        tail = (f"first={first['id']} title={first['title']!r} "
                f"urls.original={first['urls']['original']}") if first else 'first=none'
        return (f"{detail} | page={value['page']} items={len(value['items'])} "
                f"pageSize={value['pageSize']} total={value['total']} "
                f"totalPages={value['totalPages']} hasMore={value['hasMore']} "
                f"hiddenCount={value.get('hiddenCount')} "
                f"ids={[item['id'] for item in value['items']]} {tail}")

    def illust_detail(value, selected):
        illus = illust_entity(value)
        require(value['id'] == selected,
                f"id={value['id']}, requested {selected}")
        return (f"{illus} | id={value['id']} title={value['title']!r} "
                f"type={value['type']} pages={value['pages']} "
                f"author={value['author']['id']} tags={len(value['tags'])} "
                f"stats={value['stats']} urls.original={value['urls']['original']}")

    def novel_page(value, page):
        detail = fields(value, {'items': list, 'page': int, 'pageSize': int,
                                'total': int, 'totalPages': int, 'hasMore': bool})
        require(value['page'] == page, f"page={value['page']}, requested {page}")
        for item in value['items']:
            fields(item, NOVEL_FIELDS)
            present(item, ['coverSvg'])
            require('text' not in item,
                    'novel list item carries the full text field')
            fields(item['cover'], URL_FIELDS)
            fields(item['author'], AUTHOR_BRIEF_FIELDS)
        first = value['items'][0] if value['items'] else None
        tail = (f"first={first['id']} title={first['title']!r} "
                f"textLength={first['textLength']} "
                f"cover.regular={first['cover']['regular']}") if first else 'first=none'
        return (f"{detail} | page={value['page']} items={len(value['items'])} "
                f"pageSize={value['pageSize']} total={value['total']} "
                f"hasMore={value['hasMore']} hiddenCount={value.get('hiddenCount')} "
                f"ids={[item['id'] for item in value['items']]} {tail}")

    def spotlight_page(value, page):
        detail = fields(value, {'items': list, 'page': int, 'pageSize': int,
                                'hasMore': bool})
        require(value['page'] == page, f"page={value['page']}, requested {page}")
        for item in value['items']:
            fields(item, {'title': str, 'cover': str, 'tags': list,
                          'date': str, 'articleUrl': str, 'works': list})
            present(item, ['id', 'caption', 'coverSvg', 'tag'])
            for tag in item['tags']:
                present(tag, ['id', 'name'])
        first = value['items'][0] if value['items'] else None
        tail = (f"first={first['id']} title={first['title']!r} "
                f"cover={first['cover']} articleUrl={first['articleUrl']} "
                f"tags={len(first['tags'])} works={len(first['works'])}") if first else 'first=none'
        return (f"{detail} | page={value['page']} items={len(value['items'])} "
                f"pageSize={value['pageSize']} hasMore={value['hasMore']} "
                f"ids={[item['id'] for item in value['items']]} {tail}")

    def comments_detail(value):
        detail = fields(value, {'items': list, 'hasMore': bool})
        for item in value['items']:
            fields(item, COMMENT_FIELDS)
            present(item, ['id'])
            fields(item['author'], AUTHOR_BRIEF_FIELDS)
        first = value['items'][0] if value['items'] else None
        tail = (f"first={first['id']} timeLabel={first['timeLabel']!r} "
                f"text_chars={len(first['text'])}") if first else 'first=none'
        return (f"{detail} | items={len(value['items'])} hasMore={value['hasMore']} "
                f"ids={[item['id'] for item in value['items']]} "
                f"likes={[item['likes'] for item in value['items']]} {tail}")

    def user_detail(value, user_id):
        detail = fields(value, {'id': str, 'name': str, 'handle': str,
                                'accent': str, 'avatar': str, 'stats': dict,
                                'social': list})
        fields(value['stats'], USER_STATS_FIELDS)
        require(value['id'] == user_id,
                f"id={value['id']}, requested {user_id}")
        return (f"{detail} | id={value['id']} name={value['name']!r} "
                f"handle={value['handle']} stats={value['stats']} "
                f"social={len(value['social'])} avatar={value['avatar']}")

    def missing_illust(error):
        require(type(error.data) is dict,
                f'expected JSON body, got {type(error.data).__name__}')
        message = error.data.get('error')
        require(type(message) is str and message,
                'expected a non-empty string error message')
        return f"error={message!r} body_chars={len(error.body)}"

    def invalid_size(error):
        require(type(error.data) is dict,
                f'expected JSON body, got {type(error.data).__name__}')
        message = error.data.get('error')
        require(type(message) is str and message,
                'expected a non-empty string error message')
        require(error.data.get('field') == 'size',
                f"field={error.data.get('field')!r}, expected 'size'")
        code = error.data.get('code')
        require(type(code) is str and code,
                f'code={code!r} is not a non-empty string')
        return (f"error={message!r} code={code!r} field={error.data['field']!r} "
                f"body_chars={len(error.body)}")

    pages = settings['pages']
    illust_query = settings['illust_query']
    novel_query = settings['novel_query']
    spotlight_query = settings['spotlight_query']

    check('stats', client.stats, stats_detail)

    listed = check('illust_search page 1',
                   lambda: client.illust_search(page=pages[0], **illust_query),
                   lambda value: search_page(value, pages[0]))
    if listed is None:
        print('SKIP illust_show first id | - | no HTTP | '
              'illust_search page 1 failed', flush=True)
        detail = None
    elif not listed['items']:
        print('SKIP illust_show first id | - | no HTTP | '
              'illust_search page 1 returned no items', flush=True)
        detail = None
    else:
        selected = listed['items'][0]['id']
        detail = check('illust_show first id',
                       lambda: client.illust_show(selected),
                       lambda value: illust_detail(value, selected))

    check('illust_search page 2',
          lambda: client.illust_search(page=pages[1], **illust_query),
          lambda value: search_page(value, pages[1]))
    check('novel_search', lambda: client.novel_search(**novel_query),
          lambda value: novel_page(value, novel_query['page']))
    check('spotlight_list', lambda: client.spotlight_list(**spotlight_query),
          lambda value: spotlight_page(value, spotlight_query['page']))
    check('illust_comments',
          lambda: client.illust_comments(settings['comment_illust_id'],
                                         **settings['comment_query']),
          comments_detail)

    if detail is None:
        print('SKIP user_show detail author | - | no HTTP | '
              'illust detail failed or was skipped', flush=True)
    else:
        author_id = detail['author']['id']
        check('user_show detail author',
              lambda: client.user_show(author_id),
              lambda value: user_detail(value, author_id))

    check('illust_show missing id',
          lambda: client.illust_show(settings['missing_id']),
          missing_illust, expected=404)
    check('illust_search size over maximum',
          lambda: client.illust_search(q=illust_query['q'],
                                       size=settings['invalid_size']),
          invalid_size, expected=400)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Sakuria
        client = Sakuria('sakuria', access_token='', config_file=args.config)
        settings = client.config['smoke']['sakuria']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY sakuria | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
