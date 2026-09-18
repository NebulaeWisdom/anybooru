"""TBIB (Gelbooru 0.2) anonymous smoke checks: at most 6 HTTP attempts.

Six read-only GETs against the site's ``index.php?page=dapi`` dispatcher:
a JSON post list, a JSON single-post lookup by the first id, the same id as
XML text parsed with ElementTree, an XML page with ``pid`` from the config,
an XML tag list, and an XML comment list for the configured ``post_id``.
The JSON form carries the media-free fields and ``rating`` as ``safe``; the
XML form carries ``file_url``/``sample_url``/``preview_url`` and ``rating``
as ``s``. The two id lookups skip when the first list call failed or came
back empty. No credentials, media, redirects or retries. Baseline:
docs/verification.md#gelbooru02tbib匿名只读实测2026-09-19.
"""

import argparse
from functools import partial
import time
from xml.etree import ElementTree


JSON_POST_FIELDS = {'directory': int, 'hash': str, 'height': int, 'id': int,
                    'image': str, 'change': int, 'owner': str,
                    'parent_id': int, 'rating': str, 'sample': bool,
                    'sample_height': int, 'sample_width': int, 'score': int,
                    'tags': str, 'width': int}
TAG_ATTRIBUTES = ('id', 'name', 'count', 'type', 'ambiguous')


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

    query = settings['tbib']
    limit = settings['limit']
    pages = query['pages']
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

    def post_rows(value):
        require(type(value) is list, f'expected JSON list, got {type(value).__name__}')
        require(0 < len(value) <= limit,
                f'{len(value)} posts, expected 1 to {limit} for limit={limit}')
        for post in value:
            fields(post, JSON_POST_FIELDS)
            require(post['rating'] == 'safe',
                    f"rating={post['rating']!r}, expected 'safe'")
        return (f"posts={len(value)} ids={[post['id'] for post in value]} "
                f"ratings={[post['rating'] for post in value]} "
                f"first={fields(value[0], JSON_POST_FIELDS)}")

    def post_detail(value, selected):
        require(type(value) is list, f'expected JSON list, got {type(value).__name__}')
        require(len(value) == 1, f'{len(value)} posts for id={selected}, expected 1')
        fields(value[0], JSON_POST_FIELDS)
        require(value[0]['id'] == selected,
                f"id={value[0]['id']} does not match the listed {selected}")
        return (f"id={value[0]['id']} rating={value[0]['rating']} "
                f"width={value[0]['width']} height={value[0]['height']} "
                f"tags={len(value[0]['tags'].split())}")

    def xml_root(value, tag):
        require(type(value) is str, f'expected XML text, got {type(value).__name__}')
        root = ElementTree.fromstring(value)
        require(root.tag == tag, f'root={root.tag}, expected {tag}')
        count = root.get('count')
        if tag == 'posts':
            require(count is not None and count.isdigit(),
                    f'posts count attribute={count!r} is not a decimal string')
        return root

    def xml_post_id(value, selected):
        root = xml_root(value, 'posts')
        children = root.findall('post')
        require(len(children) == 1,
                f'{len(children)} post elements for id={selected}, expected 1')
        post = children[0]
        require(post.get('id') == str(selected),
                f"id={post.get('id')!r} does not match the listed {selected}")
        for attribute in ('file_url', 'sample_url', 'preview_url'):
            url = post.get(attribute)
            require(type(url) is str and url.startswith('http'),
                    f'{attribute}={url!r} is not an absolute URL')
        require(post.get('rating') == 's',
                f"rating={post.get('rating')!r}, XML safe form is 's'")
        return (f"root count={root.get('count')} offset={root.get('offset')} "
                f"post id={post.get('id')} rating={post.get('rating')} "
                f"file_url={post.get('file_url')} md5={post.get('md5')}")

    def xml_page(value):
        root = xml_root(value, 'posts')
        offset = pages[1] * limit
        require(root.get('offset') == str(offset),
                f"offset={root.get('offset')!r}, expected {offset} for pid={pages[1]} limit={limit}")
        children = root.findall('post')
        require(len(children) <= limit,
                f'{len(children)} posts, limit={limit}')
        for post in children:
            require(post.get('rating') == 's',
                    f"rating={post.get('rating')!r}, expected 's' for tags=rating:safe")
        return (f"pid={pages[1]} offset={root.get('offset')} count={root.get('count')} "
                f"posts={len(children)} ids={[post.get('id') for post in children]}")

    def xml_tags(value):
        root = xml_root(value, 'tags')
        require(root.get('type') == 'array',
                f"root type={root.get('type')!r}, expected 'array'")
        children = root.findall('tag')
        require(0 < len(children) <= limit,
                f'{len(children)} tag elements for limit={limit}')
        for tag in children:
            for attribute in TAG_ATTRIBUTES:
                require(attribute in tag.attrib,
                        f'tag {tag.get("id")} is missing attribute {attribute}')
                require(type(tag.get(attribute)) is str,
                        f'tag attribute {attribute} is not XML text')
            require(tag.get('id').isdigit() and tag.get('count').isdigit()
                    and tag.get('type').isdigit(),
                    f'tag {tag.get("name")} has a non-decimal numeric attribute')
            require(tag.get('ambiguous') in ('true', 'false'),
                    f"tag {tag.get('name')} ambiguous={tag.get('ambiguous')!r}")
        return (f"type=array tags={len(children)} "
                f"names={[tag.get('name') for tag in children]} "
                f"attributes={sorted(children[0].attrib)}")

    def xml_comments(value):
        root = xml_root(value, 'comments')
        require(root.get('type') == 'array',
                f"root type={root.get('type')!r}, expected 'array'")
        children = list(root)
        return (f"type=array comments={len(children)} "
                f"children={[(child.tag, sorted(child.attrib)) for child in children]}")

    posts = check(
        'post_list json',
        lambda: client.post_list(pid=pages[0], limit=limit,
                                 response_format='json', **query['post_query']),
        post_rows)
    if not posts:
        print('SKIP post_list json id | - | no HTTP | '
              'post_list json failed or returned no posts', flush=True)
        print('SKIP post_list xml id | - | no HTTP | '
              'post_list json failed or returned no posts', flush=True)
    else:
        selected = posts[0]['id']
        check('post_list json id',
              lambda: client.post_list(id=selected, limit=limit,
                                       response_format='json'),
              lambda value: post_detail(value, selected))
        check('post_list xml id',
              lambda: client.post_list(id=selected, response_format='xml'),
              lambda value: xml_post_id(value, selected))

    check('post_list xml page',
          lambda: client.post_list(pid=pages[1], limit=limit,
                                   response_format='xml', **query['post_query']),
          xml_page)
    check('tag_list xml', lambda: client.tag_list(limit=limit), xml_tags)
    check('comment_list xml',
          lambda: client.comment_list(query['comment_post_id'], limit=limit),
          xml_comments)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Gelbooru02
        client = Gelbooru02('tbib', config_file=args.config)
        settings = client.config['smoke']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY tbib | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
