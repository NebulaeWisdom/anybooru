# -*- coding: utf-8 -*-
"""按标签名查图：先搜到 tag_id，再逐页列图，最后取第一张的详情。

依次调用（都是匿名只读 GET，最多 4 次）：

1. ``search(q='long hair', limit=5)`` → ``GET /api/v1/search?q=long+hair&limit=5``，
   返回 ``{"query", "entity", "hits": [...], "total", "limit", "offset"}``；
   从 ``hits`` 里挑 ``title`` 恰好等于 ``long hair`` 的那条，读它的 ``tag_id``。
   找不到就报错，绝不拿别的标签猜一个 ID 顶替。
2. ``image_list(tags='46', page=1, tags_mode='all', tag_depth=0, per_page=2,
   sort_by='favorites', sort_order='DESC')`` → ``GET /api/v1/images``，返回
   ``{"total", "page", "per_page", "images": [...]}``；``tags`` 收的是逗号分隔的
   tag ID 字符串（脚本把上一步的 ``tag_id`` 转成字符串），不是标签名。
3. 同样的 ``image_list`` 换成 ``page=2``。
4. 第一页非空时取 ``images[0]['image_id']`` 调 ``image_show(<该 id>)`` →
   ``GET /api/v1/images/<该 id>``，返回无信封的单图对象，含 ``md5_hash``、
   ``width``/``height``、``favorites``、``tags`` 与 ``url``。

每行打印一个 JSON 对象：方法名、HTTP 状态码、真实 URL 与本次拿到的字段，
不下载任何媒体。标签名、数量、页码、调用间隔与站点名取自配置文件的
``examples.shuushuu`` 段（默认读包内 ``anybooru.json``）；``--config`` 换配置、
``--site`` 换站点，不传时用 ``examples.shuushuu.site``。用户名、密码、
access_token 显式留空，脚本只做匿名只读请求。
"""

import argparse
import json
import time

from anybooru import Shuushuu
from anybooru.resources import load_config


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='按标签名列出 Shuushuu 图片与详情')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.shuushuu.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['shuushuu']
    site = example['site'] if args.site is None else args.site

    with Shuushuu(site, config_file=args.config, username='', password='',
                  access_token='') as client:
        def pause():
            time.sleep(example['pause_seconds'])

        result = client.search(**example['search_query'])
        tag_hit = next((hit for hit in result['hits']
                        if hit['title'] == example['tag_title']), None)
        if tag_hit is None:
            raise ValueError(
                f"搜索结果里没有标题恰为 {example['tag_title']!r} 的标签")
        emit(client, 'search', query=result['query'], entity=result['entity'],
             hits=len(result['hits']), total=result['total'],
             tag_id=tag_hit['tag_id'], tag_title=tag_hit['title'],
             usage_count=tag_hit['usage_count'])

        tag_id = str(tag_hit['tag_id'])
        first_page_images = None
        for page in example['pages']:
            pause()
            listing = client.image_list(tags=tag_id, page=page,
                                        **example['image_query'])
            if first_page_images is None:
                first_page_images = listing['images']
            emit(client, 'image_list', page=listing['page'],
                 total=listing['total'], per_page=listing['per_page'],
                 count=len(listing['images']),
                 image_ids=[image['image_id'] for image in listing['images']])

        if not first_page_images:
            print(json.dumps({'method': 'image_show',
                              'skipped': 'image_list returned no images'}))
            return
        pause()
        detail = client.image_show(first_page_images[0]['image_id'])
        emit(client, 'image_show', image_id=detail['image_id'],
             md5_hash=detail['md5_hash'], width=detail['width'],
             height=detail['height'], favorites=detail['favorites'],
             tags=len(detail['tags']), image_url=detail['url'],
             thumbnail_url=detail['thumbnail_url'])


if __name__ == '__main__':
    main()
