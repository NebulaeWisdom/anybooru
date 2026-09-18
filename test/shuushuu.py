"""Shuushuu anonymous smoke checks: at most 10 HTTP attempts.

Ten read-only GETs under ``api/v1``: ``search``, ``tag_list``,
``image_list`` with comma separated tag ids, the matching ``image_show``,
``tag_show``, ``comment_list``, ``image_stats``, ``meta_config``, plus two
expected failures -- ``image_list`` with ``per_page`` above the documented
maximum (HTTP 422) and a missing image id (HTTP 404) -- which are reported
as genuine errors, not swallowed. Empty successful collections skip their
dependent detail call instead of failing. No credentials, writes,
redirects, retries or media downloads. Baseline: docs/verification.md,
section shuushuu-匿名只读实测2026-09-19.
"""

import argparse
from functools import partial
import time


NULLABLE_STR = (str, type(None))
NULLABLE_INT = (int, type(None))
NUMBER = (int, float)


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


def exercise(client, settings):
    from anybooru import AnybooruHTTPError
    from requests import RequestException

    query = settings['shuushuu']
    counts = {'requests': 0, 'passed': 0, 'failed': 0}
    # One call = one HTTP attempt: never follow redirects or retry.
    client.client.request = partial(client.client.request, allow_redirects=False)

    def check(name, call, inspect, expected=200):
        if counts['requests']:
            time.sleep(query['pause_seconds'])
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

    search_query = query['search_query']

    def search_detail(value):
        detail = fields(value, {'query': str, 'entity': str, 'hits': list,
                                'total': int, 'limit': int, 'offset': int})
        require(value['entity'] == 'tags', f"entity={value['entity']!r}, expected tags")
        require(value['limit'] == search_query['limit'],
                f"limit={value['limit']}, requested {search_query['limit']}")
        require(len(value['hits']) > 0, 'search returned no hits')
        for hit in value['hits']:
            fields(hit, {'tag_id': int, 'title': NULLABLE_STR, 'type': int,
                         'usage_count': int})
        first = value['hits'][0]
        return (f"{detail} | hits={len(value['hits'])} total={value['total']} "
                f"entity={value['entity']} first_title={first['title']!r} "
                f"first_tag_id={first['tag_id']}")

    tag_query = query['tag_query']

    def tags_detail(value):
        detail = fields(value, {'total': int, 'page': int, 'per_page': int,
                                'tags': list})
        require(value['per_page'] == tag_query['per_page'],
                f"per_page={value['per_page']}, requested {tag_query['per_page']}")
        require(len(value['tags']) > 0, 'tag search returned no tags')
        for tag in value['tags']:
            fields(tag, {'tag_id': int, 'title': NULLABLE_STR, 'type': int,
                         'usage_count': int, 'is_alias': bool})
        return (f"{detail} | tags={len(value['tags'])} total={value['total']} "
                f"titles={[tag['title'] for tag in value['tags']]}")

    image_query = query['image_query']
    required_tags = set(query['required_tag_ids'])

    def required_tag_ids_present(image):
        tag_ids = {tag['tag_id'] for tag in image['tags']}
        missing = required_tags - tag_ids
        require(not missing,
                f"image {image['image_id']} is missing tag IDs {sorted(missing)}")

    def images_detail(value):
        detail = fields(value, {'total': int, 'page': int, 'per_page': int,
                                'images': list})
        require(value['per_page'] == image_query['per_page'],
                f"per_page={value['per_page']}, requested {image_query['per_page']}")
        for image in value['images']:
            fields(image, {'image_id': int, 'url': str, 'thumbnail_url': str,
                           'favorites': int, 'tags': list})
            required_tag_ids_present(image)
        return (f"{detail} | total={value['total']} page={value['page']} "
                f"images={len(value['images'])} "
                f"ids={[image['image_id'] for image in value['images']]}")

    def image_detail(value):
        detail = fields(value, {'image_id': int, 'md5_hash': str, 'url': str,
                                'thumbnail_url': str, 'favorites': int,
                                'tags': list})
        require(value['image_id'] == selected,
                f"image_id={value['image_id']}, requested {selected}")
        required_tag_ids_present(value)
        return (f"{detail} | image_id={value['image_id']} "
                f"md5_hash={value['md5_hash']} favorites={value['favorites']} "
                f"tags={len(value['tags'])} url={value['url']}")

    def tag_detail(value):
        detail = fields(value, {'tag_id': int, 'date_added': NULLABLE_STR,
                                'total_image_count': int, 'title': NULLABLE_STR,
                                'usage_count': int, 'child_count': int,
                                'aliases': list, 'links': list, 'sources': list,
                                'characters': list})
        require(value['tag_id'] == query['tag_id'],
                f"tag_id={value['tag_id']}, requested {query['tag_id']}")
        return (f"{detail} | tag_id={value['tag_id']} title={value['title']!r} "
                f"usage_count={value['usage_count']} "
                f"total_image_count={value['total_image_count']}")

    comment_query = query['comment_query']

    def comments_detail(value):
        detail = fields(value, {'total': int, 'page': int, 'per_page': int,
                                'comments': list})
        require(value['per_page'] == comment_query['per_page'],
                f"per_page={value['per_page']}, requested {comment_query['per_page']}")
        for comment in value['comments']:
            fields(comment, {'post_id': int, 'user_id': int, 'date': str,
                             'update_count': int, 'user': dict,
                             'post_text': str, 'post_text_html': str,
                             'image_id': NULLABLE_INT})
            require(comment['image_id'] == comment_query['image_id'],
                    f"comment {comment['post_id']} has image_id "
                    f"{comment['image_id']}, requested {comment_query['image_id']}")
        return (f"{detail} | comments={len(value['comments'])} "
                f"total={value['total']} "
                f"post_ids={[comment['post_id'] for comment in value['comments']]}")

    def stats_detail(value):
        detail = fields(value, {'total_images': int, 'total_favorites': int,
                                'average_rating': NUMBER})
        return (f"{detail} | total_images={value['total_images']} "
                f"total_favorites={value['total_favorites']} "
                f"average_rating={value['average_rating']}")

    def config_detail(value):
        detail = fields(value, {'max_search_tags': int, 'max_search_users': int,
                                'max_image_size': int, 'max_avatar_size': int,
                                'upload_delay_seconds': int,
                                'search_delay_seconds': int, 'tag_types': dict,
                                'ml_tag_suggestions_enabled': bool,
                                'ml_character_suggestions_enabled': bool})
        return (f"{detail} | max_search_tags={value['max_search_tags']} "
                f"max_image_size={value['max_image_size']} "
                f"search_delay_seconds={value['search_delay_seconds']} "
                f"tag_types={len(value['tag_types'])}")

    def invalid_per_page(error):
        require(type(error.data) is dict,
                f'expected JSON body, got {type(error.data).__name__}')
        detail = error.data.get('detail')
        require(type(detail) is list and detail,
                f'expected non-empty detail array, got {type(detail).__name__}')
        for item in detail:
            require(type(item) is dict, 'detail item is not an object')
            loc = item.get('loc')
            require(loc == ['query', 'per_page'],
                    f"detail loc={loc}, expected query/per_page")
            require(type(item.get('msg')) is str and item['msg'],
                    'detail msg is not a non-empty string')
            context = item.get('ctx')
            require(type(context) is dict and 'le' in context,
                    'detail ctx has no le bound')
            require(context['le'] == query['per_page_maximum'],
                    f"ctx.le={context['le']}, expected {query['per_page_maximum']}")
        return (f"loc=query/per_page type={detail[0].get('type')} "
                f"ctx.le={detail[0]['ctx']['le']} body_chars={len(error.body)}")

    def missing_image(error):
        require(type(error.data) is dict,
                f'expected JSON body, got {type(error.data).__name__}')
        detail = error.data.get('detail')
        require(type(detail) is str and detail,
                f'expected non-empty string detail, got {type(detail).__name__}')
        return f'detail_chars={len(detail)} body_chars={len(error.body)}'

    check('search', lambda: client.search(**search_query), search_detail)
    check('tag_list', lambda: client.tag_list(**tag_query), tags_detail)

    images = check('image_list tags', lambda: client.image_list(**image_query),
                   images_detail)
    if images is None:
        print('SKIP image_show first id | - | no HTTP | image_list failed', flush=True)
    elif not images['images']:
        print('SKIP image_show first id | - | no HTTP | '
              'image_list returned no images', flush=True)
    else:
        selected = images['images'][0]['image_id']
        check('image_show first id', lambda: client.image_show(selected),
              image_detail)

    check('tag_show', lambda: client.tag_show(query['tag_id']), tag_detail)
    check('comment_list', lambda: client.comment_list(**comment_query),
          comments_detail)
    check('image_stats', client.image_stats, stats_detail)
    check('meta_config', client.meta_config, config_detail)
    check('image_list per_page over maximum',
          lambda: client.image_list(per_page=query['invalid_per_page']),
          invalid_per_page, expected=422)
    check('image_show missing id',
          lambda: client.image_show(query['missing_image_id']),
          missing_image, expected=404)

    print(f"SUMMARY {client.site_name} | requests={counts['requests']} | "
          f"passed={counts['passed']} failed={counts['failed']}")
    return int(counts['failed'] != 0)


def main():
    parser = argparse.ArgumentParser(description='Anonymous site smoke checks')
    parser.add_argument('--config', default=None, help='Configuration file (default: packaged anybooru.json)')
    args = parser.parse_args()
    try:
        from anybooru import Shuushuu
        client = Shuushuu('shuushuu', config_file=args.config,
                          username='', password='', access_token='')
        settings = client.config['smoke']
    except Exception as error:
        print(f'FAIL setup | - | no HTTP | {type(error).__name__}: {error}')
        print('SUMMARY shuushuu | requests=0 | passed=0 failed=1')
        return 1
    with client:
        print(f'PASS setup | {client.site_url} | no HTTP | import/config/client OK; anonymous', flush=True)
        return exercise(client, settings)


if __name__ == '__main__':
    raise SystemExit(main())
