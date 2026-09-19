# -*- coding: utf-8 -*-
"""列出 Anime-Pictures 帖子：按配置页码取两页 JSON 列表（固定 2 次匿名 GET）。

依次调用：

1. ``posts_list(page=0, search_tag='hatsune miku', posts_per_page=2, order_by='rating')``
   → ``GET https://api.anime-pictures.net/api/v3/posts?page=0&search_tag=hatsune+miku&posts_per_page=2&order_by=rating``，
   返回顶层信封 ``posts_per_page``、``response_posts_count``、``page_number``、``posts``、
   ``posts_count``、``max_pages``。``posts`` 每项含 ``id``、``md5``、``width``、``height``、
   ``score``、``score_number``、``tags_count``、``erotics``、``ext``（带点，如 ``.png``）、
   ``status`` 等；``status_type`` 等字段会缺失，脚本不读它。列表对象没有预览地址。
2. 同参但 ``page=1`` → ``GET https://api.anime-pictures.net/api/v3/posts?page=1&search_tag=hatsune+miku&posts_per_page=2&order_by=rating``。

``'posts'`` 是相对 API 基址的路径；以 ``/`` 开头会变成主机根路径（如 ``'/api/v3/posts'``），
本家族与其它家族在这点上不同。``search_tag`` 里的空格由共享层编码后送出，脚本不手工拼 URL。
默认配置对应这两次请求，实际 URL 由 ``last_call`` 打印。

教学写法（字面参数，自足）：

    from anybooru import AnimePictures

    with AnimePictures('anime_pictures', authorization='', cookie='') as client:
        first_page = client.posts_list(
            page=0, search_tag='hatsune miku', posts_per_page=2, order_by='rating')
        print(first_page['page_number'], first_page['posts_count'],
              first_page['max_pages'], first_page['posts'][0]['id'])

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL，以及
``page_number``/``posts_count``/``max_pages``/当页 ``ids`` 与帖子摘要。不下载媒体、
不打印标签正文。参数与站点名取自配置文件的 ``examples.anime_pictures`` 段（默认读包内
``anybooru.json``）；``--config`` 换配置、``--site`` 换站点，不传时取
``examples.anime_pictures.site``。``authorization`` 与 ``cookie`` 显式传空串，按
``pause_seconds`` 串行暂停，不重试、不跟随跳转。
"""

import argparse
from functools import partial
import json
import time

from anybooru import AnimePictures
from anybooru.resources import load_config


def post_summary(post):
    """帖子摘要：只报列表对象里的字段，不打印标签正文或媒体地址。"""
    return {'id': post['id'], 'md5': post['md5'], 'width': post['width'],
            'height': post['height'], 'score': post['score'],
            'score_number': post['score_number'],
            'tags_count': post['tags_count'], 'erotics': post['erotics'],
            'ext': post['ext'], 'status': post['status']}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='列出 Anime-Pictures 帖子并按配置页码翻页')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.anime_pictures.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['anime_pictures']
    site = example['site'] if args.site is None else args.site

    with AnimePictures(site, config_file=args.config,
                       authorization='', cookie='') as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        for step, page in enumerate(example['pages']):
            if step:
                time.sleep(example['pause_seconds'])
            envelope = client.posts_list(page=page, **example['post_query'])
            emit(client, 'posts_list', requested_page=page,
                 page_number=envelope['page_number'],
                 posts_per_page=envelope['posts_per_page'],
                 response_posts_count=envelope['response_posts_count'],
                 posts_count=envelope['posts_count'],
                 max_pages=envelope['max_pages'],
                 count=len(envelope['posts']),
                 ids=[post['id'] for post in envelope['posts']],
                 posts=[post_summary(post) for post in envelope['posts']])


if __name__ == '__main__':
    main()
