# -*- coding: utf-8 -*-
"""列出 TBIB（Gelbooru 0.2）的帖子：先取 JSON 列表，再按同一编号取 XML 详情。

依次调用（都是匿名只读 GET，固定 2 次）：

1. ``post_list(tags='rating:safe', pid=0, limit=2, response_format='json')`` →
   ``GET https://tbib.org/index.php?tags=rating%3Asafe&pid=0&limit=2&s=post&q=index&page=dapi&json=1``，
   返回 JSON 数组（无外层信封、无 ``count``/``offset``），每项含 ``id``、``rating``
   （JSON 里是 ``safe``）、``width``/``height``、``score``、``tags``、``directory``、
   ``image``、``hash`` 等；JSON 里没有 ``file_url``/``sample_url``/``preview_url``，
   脚本也不会拿 ``directory``/``image``/``hash`` 拼媒体地址。
2. 取第 1 步第一条的 ``id`` 调 ``post_list(id=<该 id>, response_format='xml')`` →
   ``GET https://tbib.org/index.php?id=<该 id>&s=post&q=index&page=dapi``，返回 XML 文本：
   根 ``<posts>`` 带 ``count``/``offset``，子 ``<post>`` 带 ``file_url``、``sample_url``、
   ``preview_url``、``rating``（XML 里 safe 写作 ``s``）等属性。

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL 与摘要字段
（编号、评级、宽高、评分、标签条数；XML 另给根元数据与三个媒体地址）。不下载媒体、
不打印大段正文。参数与站点名取自配置文件的 ``examples.gelbooru02`` 段（默认读包内
``anybooru.json``）；``--config`` 换配置、``--site`` 换站点，不传时取
``examples.gelbooru02.site``。脚本不带任何凭据。
"""

import argparse
from functools import partial
import json
import time
from xml.etree import ElementTree

from anybooru import Gelbooru02
from anybooru.resources import load_config


def post_summary(post):
    """JSON 帖子摘要；只报标签条数，不打印标签全文。"""
    return {'id': post['id'], 'rating': post['rating'], 'width': post['width'],
            'height': post['height'], 'score': post['score'],
            'tag_count': len(post['tags'].split())}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='列出 TBIB 帖子并取同一编号的 XML 详情')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.gelbooru02.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['gelbooru02']
    site = example['site'] if args.site is None else args.site

    with Gelbooru02(site, config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)
        posts = client.post_list(response_format='json', **example['post_query'])
        emit(client, 'post_list', count=len(posts),
             posts=[post_summary(post) for post in posts])

        if not posts:
            print(json.dumps({'method': 'post_list xml',
                              'skipped': 'post_list returned no posts'}))
            return
        time.sleep(example['pause_seconds'])
        detail = client.post_list(id=posts[0]['id'], response_format='xml')
        root = ElementTree.fromstring(detail)
        post = root.find('post')
        emit(client, 'post_list xml',
             root={'tag': root.tag, 'count': root.get('count'),
                   'offset': root.get('offset')},
             post={'id': post.get('id'), 'rating': post.get('rating'),
                   'width': post.get('width'), 'height': post.get('height'),
                   'md5': post.get('md5'), 'file_url': post.get('file_url'),
                   'sample_url': post.get('sample_url'),
                   'preview_url': post.get('preview_url')})


if __name__ == '__main__':
    main()
