"""Anime-Pictures anonymous smoke checks: at most 10 HTTP attempts.

Ten read-only GETs against the Anime-Pictures API host, all parameters taken
from ``smoke.anime_pictures``: two ``/posts`` pages (the configured
``posts_per_page``, page 0 and page 1), ``/posts/{id}`` for the first id listed
on page 0, ``/posts/{comment_post_id}/comments``, an exact ``/tags`` query,
``/tags/{tag_id}``, ``/users`` and ``/comments``. The final two calls are
expected failures: a missing post id (HTTP 410 with a JSON
``{errormsg, success:false}`` body) and an unparseable path segment (HTTP 400
with a plain-text body).

The 410 is inspected through ``AnybooruHTTPError.data`` (a dict, so the shared
layer parsed it) and the 400 for ``data is None`` with a non-empty ``body``:
the site answers the bad path segment with ``text/plain``, so that failure must
stay an ``AnybooruHTTPError`` and never surface as ``AnybooruAPIError``. Both
are also matched against ``client.last_call`` for the recorded URL and status,
and neither body's text is asserted. The detail lookup skips when page 0 failed
or came back empty and sends no request in that case; every other call still
runs.

The client is constructed with an explicit empty ``authorization`` and
``cookie``, so the run stays anonymous whatever the configuration holds;
redirects are disabled and requests are never retried. List envelopes are
checked for their documented keys and types plus the requested page number and
resource ids -- never for counts or wording that may drift.
Baseline: docs/verification.md#anime-pictures匿名只读实测2026-09-19.
"""

import argparse
from functools import partial
import time


NUMBER = (int, float)
POSTS_ENVELOPE = {'posts': list, 'posts_per_page': int, 'response_posts_count': int,
                  'page_number': int, 'posts_count': int, 'max_pages': int}
POST_FIELDS = {'id': int, 'md5': str, 'width': int, 'height': int,
               'score': NUMBER, 'score_number': int, 'ext': str,
               'tags_count': int}
POST_PRESENT = ['md5_pixels', 'juser_id', 'pubtime', 'datetime', 'size',
                'download_count', 'erotics', 'color', 'status', 'spoiler',
                'have_alpha', 'artefacts_degree', 'smooth_degree']
PREVIEW_FIELDS = {'small_preview': str, 'medium_preview': str,
                  'big_preview': str}
USER_FIELDS = {'id': int, 'name': str, 'login': str}
USER_PRESENT = ['avatar_version', 'isavatar', 'site_score', 'groups', 'gender',
                'register_date']
TAG_ENVELOPE = {'tags': list, 'success': bool, 'offset': int, 'limit': int,
                'count': int}
TAG_FIELDS = {'id': int, 'tag': str, 'num': int, 'type': int}
TAG_PRESENT = ['tag_ru', 'tag_jp', 'num_pub', 'description_en',
               'description_ru', 'description_jp', 'alias', 'parent', 'views']
COMMENTS_ENVELOPE = {'comments': list, 'success': bool, 'offset': int,
                     'limit': int, 'count': int}
COMMENT_FIELDS = {'id': int, 'text': str, 'datetime': str}


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


def post_entity(value):
    """Check the keys shared by a listed post and the detail's nested post."""
    detail = fields(value, POST_FIELDS)
    present(value, POST_PRESENT)
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

    def posts_page(value, page):
        detail = fields(value, POSTS_ENVELOPE)
        require(value['page_number'] == page,
                f"page_number={value['page_number']}, requested {page}")
        for post in value['posts']:
            post_entity(post)
        first = value['posts'][0] if value['posts'] else None
        tail = (f"first={first['id']} md5={first['md5']} "
                f"size={first['width']}x{first['height']} "
                f"score_number={first['score_number']} ext={first['ext']!r}") if first else 'first=none'
        return (f"{detail} | page_number={value['page_number']} "
                f"posts={len(value['posts'])} "
                f"response_posts_count={value['response_posts_count']} "
                f"posts_per_page={value['posts_per_page']} "
                f"posts_count={value['posts_count']} max_pages={value['max_pages']} "
                f"ids={[post['id'] for post in value['posts']]} {tail}")

    def post_detail(value, selected):
        require(type(value) is dict, f'expected object, got {type(value).__name__}')
        present(value, ['post', 'user', 'tags', 'file_url'])
        post = value['post']
        detail = post_entity(post)
        fields(post, PREVIEW_FIELDS)
        for name in PREVIEW_FIELDS:
            require(post[name], f'{name} is empty')
        require(post['id'] == selected, f"post.id={post['id']}, requested {selected}")
        fields(value['user'], USER_FIELDS)
        present(value['user'], USER_PRESENT)
        for tag in value['tags']:
            require(type(tag) is dict, f'expected object, got {type(tag).__name__}')
            present(tag, ['tag', 'user', 'relation'])
        require(type(value['file_url']) is str and value['file_url'],
                'file_url is not a non-empty string')
        detail_keys = ','.join(value)
        return (f"{detail} | id={post['id']} file_url={value['file_url']!r} "
                f"small_preview={post['small_preview']} tags={len(value['tags'])} "
                f"user={value['user']['id']} detail_keys={detail_keys}")

    def post_comments(value):
        detail = fields(value, {'success': bool, 'comments': list})
        require(value['success'] is True, f"success={value['success']!r}, expected true")
        for item in value['comments']:
            fields(item, {'comment': dict, 'user': dict})
            fields(item['comment'], COMMENT_FIELDS)
        first = value['comments'][0] if value['comments'] else None
        tail = (f"first={first['comment']['id']} "
                f"text_chars={len(first['comment']['text'])} "
                f"user={first['user'].get('id')}") if first else 'first=none'
        return f"{detail} | comments={len(value['comments'])} {tail}"

    def tags_page(value, query):
        detail = fields(value, TAG_ENVELOPE)
        require(value['success'] is True, f"success={value['success']!r}, expected true")
        for tag in value['tags']:
            fields(tag, TAG_FIELDS)
            present(tag, TAG_PRESENT)
        require(any(tag['tag'] == query['tag'] for tag in value['tags']),
                f"no tag named {query['tag']!r} in {[tag['tag'] for tag in value['tags']]}")
        first = value['tags'][0]
        return (f"{detail} | offset={value['offset']} limit={value['limit']} "
                f"count={value['count']} ids={[tag['id'] for tag in value['tags']]} "
                f"names={[tag['tag'] for tag in value['tags']]} "
                f"first={first['id']}/{first['tag']!r} num={first['num']}")

    def tag_detail(value, tag_id):
        detail = fields(value, {'success': bool, 'tag': dict})
        require(value['success'] is True, f"success={value['success']!r}, expected true")
        tag = value['tag']
        fields(tag, TAG_FIELDS)
        present(tag, TAG_PRESENT)
        require(tag['id'] == tag_id, f"tag.id={tag['id']}, requested {tag_id}")
        return (f"{detail} | id={tag['id']} tag={tag['tag']!r} num={tag['num']} "
                f"type={tag['type']}")

    def users_page(value, query):
        detail = fields(value, {'users': list, 'success': bool, 'offset': int,
                                'limit': int, 'count': int})
        require(value['success'] is True, f"success={value['success']!r}, expected true")
        require(value['offset'] == query['offset'],
                f"offset={value['offset']}, requested {query['offset']}")
        require(value['limit'] == query['limit'],
                f"limit={value['limit']}, requested {query['limit']}")
        for user in value['users']:
            fields(user, {'id': int})
            present(user, ['name', 'login'])
        return (f"{detail} | offset={value['offset']} limit={value['limit']} "
                f"count={value['count']} "
                f"user_ids={[user['id'] for user in value['users']]}")

    def comments_page(value, query):
        detail = fields(value, COMMENTS_ENVELOPE)
        require(value['success'] is True, f"success={value['success']!r}, expected true")
        require(value['offset'] == query['offset'],
                f"offset={value['offset']}, requested {query['offset']}")
        require(value['limit'] == query['limit'],
                f"limit={value['limit']}, requested {query['limit']}")
        for item in value['comments']:
            fields(item, {'comment': dict, 'post': dict, 'user': dict})
            fields(item['comment'], COMMENT_FIELDS)
        return (f"{detail} | offset={value['offset']} limit={value['limit']} "
                f"count={value['count']} "
                f"comment_ids={[item['comment']['id'] for item in value['comments']]} "
                f"post_ids={[item['post'].get('id') for item in value['comments']]}")

    def recorded(error):
        """Require the shared layer to have recorded this failed call."""
        require(client.last_call.get('status_code') == error.http_code,
                f"last_call status_code={client.last_call.get('status_code')!r}, "
                f'expected {error.http_code}')
        require(client.last_call.get('url') == error.url,
                f"last_call url={client.last_call.get('url')!r}, expected {error.url!r}")
        return f"last_call=HTTP {client.last_call['status_code']} {client.last_call['url']}"

    def missing_post(error):
        require(type(error.data) is dict,
                f'expected JSON body, got {type(error.data).__name__}')
        require(error.data.get('success') is False,
                f"success={error.data.get('success')!r}, expected false")
        message = error.data.get('errormsg')
        require(type(message) is str and message,
                'expected a non-empty errormsg string')
        return (f"data={sorted(error.data)} errormsg={message!r} "
                f'body_chars={len(error.body)} {recorded(error)}')

    def invalid_path(error):
        require(error.data is None,
                f'expected no JSON body, got {type(error.data).__name__}')
        require(type(error.body) is str and error.body.strip(),
                'expected a non-empty plain-text body')
        content_type = error.response.headers.get('Content-Type', '')
        require('json' not in content_type.lower(),
                f'Content-Type={content_type!r} is not plain text')
        return (f"data={error.data!r} body_chars={len(error.body)} "
                f"content_type={content_type!r} {recorded(error)}")

    pages = settings['pages']
    post_query = settings['post_query']
    tag_query = settings['tag_query']
    user_query = settings['user_query']
    comment_query = settings['comment_query']

    listed = check('posts_list page 0',
                   lambda: client.posts_list(page=pages[0], **post_query),
                   lambda value: posts_page(value, pages[0]))
    if listed is None:
        print('SKIP post_show first id | - | no HTTP | posts_list page 0 failed',
              flush=True)
    elif not listed['posts']:
        print('SKIP post_show first id | - | no HTTP | '
              'posts_list page 0 returned no posts', flush=True)
    else:
        selected = listed['posts'][0]['id']
        check('post_show first id',
              lambda: client.post_show(selected),
              lambda value: post_detail(value, selected))

    check('posts_list page 1',
          lambda: client.posts_list(page=pages[1], **post_query),
          lambda value: posts_page(value, pages[1]))
    check('post_comments configured post',
          lambda: client.post_comments(settings['comment_post_id']),
          post_comments)
    check('tags_list exact tag', lambda: client.tags_list(**tag_query),
          lambda value: tags_page(value, tag_query))
    check('tag_show configured id', lambda: client.tag_show(settings['tag_id']),
          lambda value: tag_detail(value, settings['tag_id']))
    check('users_list', lambda: client.users_list(**user_query),
          lambda value: users_page(value, user_query))
    check('comments_list', lambda: client.comments_list(**comment_query),
          lambda value: comments_page(value, comment_query))
    check('post_show missing id',
          lambda: client.post_show(settings['missing_id']),
          missing_post, expected=410)
    check('post_show invalid path',
          lambda: client.post_show(settings['invalid_post_id']),
          invalid_path, expected=400)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import AnimePictures
        client = AnimePictures('anime_pictures', authorization='', cookie='',
                               config_file=args.config)
        settings = client.config['smoke']['anime_pictures']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY anime_pictures | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; '
              'anonymous authorization="" cookie=""', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
