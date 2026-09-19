# -*- coding: utf-8 -*-
"""列出 Cosine Gallery 图片：两页列表 + 两个 offset 的筛选搜索（固定 4 次匿名 GET）。

依次调用：

1. ``image_list(page=1, pageSize=2)`` → ``GET https://pic.cosine.ren/api/list?page=1&pageSize=2``，
   返回外层信封 ``{'images': [...], 'total': N}``。``images`` 每项是入库记录而不是「作品」：
   ``id`` 是站内自增主键（与上游编号无关）、``pid`` 是上游编号字符串、``userid``/``username``
   是投稿人、``author``/``authorid`` 是画师、``platform`` 是来源站（``twitter``/``pixiv`` 等）、
   ``page`` 是这张图在作品里的页码（Twitter 从 1 起、Pixiv 从 0 起）、``width``/``height``、
   ``filename``、``extension``，另有 ``title``、``rawurl``/``thumburl``（媒体地址文本）、
   ``tags``（字符串数组）与 ``size``/``guest``/``r18``/``ai`` 四个布尔/数值位。本轮 ``/api/list``
   样本里 ``size`` 是 ``null``、``guest`` 是 ``false``，但详情样本取到过非退化值（见
   ``browse_resources.py``），所以脚本照实打印、不外推这两个字段的含义。
2. 同参但 ``page=2`` → 同上路由，``total`` 不随页码变化。
3. ``search(q='初音', limit=2, offset=0, platform='twitter', r18=False, sort='create_time:desc')``
   → ``GET https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2&offset=0&platform=twitter&r18=false&sort=create_time%3Adesc``，
   返回 ``{'success': True, 'data': {...}}``，``data`` 含 ``hits``、``query``、``total``、
   ``limit``、``offset``、``processingTimeMs``。命中项的字段名与 ``/api/list`` 不同：``id``
   是**字符串**（本轮样本 ``'2760'``）、``tags`` 仍是字符串数组，另多出 ``searchable_content``
   与 ``_formatted``。``q`` 里的中文由共享层按 UTF-8 百分号编码，``r18=False`` 编码成
   ``r18=false``（布尔小写）、``sort`` 里的 ``:`` 编码成 ``%3A``，脚本不手工拼 URL。
4. 同参但 ``offset=2`` → 同上路由，用来观察第 3 条之后的一页。

``total`` 是站点的估计命中数：本轮不带筛选的 ``q=初音&limit=2`` 样本是 ``255``，空 ``q``
样本被夹到 ``1000``，``offset=100000`` 样本返回的 ``offset`` 被站点改成 ``1000`` 且 ``hits``
为空——所以脚本照实打印站点回来的 ``total``/``offset``，不把它当精确计数、也不自己钳位。
站点按 ``platform``/``r18``/``sort`` 过滤与排序的效果由站点决定，脚本只报返回条数与编号，
不校验过滤是否正确；带筛选的组合（``platform=twitter`` + ``r18=false`` + ``sort=create_time:desc``）
的实际命中见验证记录。

教学写法（字面参数，自足）：

    from anybooru import Cosine

    with Cosine('cosine', revalidate_secret='') as client:
        first_page = client.image_list(page=1, pageSize=2)
        print(first_page['total'], [image['id'] for image in first_page['images']])
        hits = client.search(q='初音', limit=2, offset=0, platform='twitter',
                             r18=False, sort='create_time:desc')
        print(hits['data']['total'], hits['data']['hits'][0]['id'])

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL，以及本次请求的
页码/偏移、站点返回的 ``total``/``limit``/``offset``/``processingTimeMs``、条数、编号列表与
列表项的资源摘要；搜索项只展示编号、实际字段名、媒体地址与标签条数，标题可能缺失。
只打印标签条数，不打印标签正文，也不下载媒体。参数与站点名取自配置文件的 ``examples.cosine``
段（默认读包内 ``anybooru.json``）；``--config`` 换配置、``--site`` 换站点，不传时取
``examples.cosine.site``。``revalidate_secret`` 显式传空串保持匿名（本脚本的两个路由都不需要
密钥），按 ``pause_seconds`` 串行暂停，不重试、不跟随跳转。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Cosine
from anybooru.resources import load_config


def image_summary(image):
    """列表项摘要：媒体地址只当字符串打印，标签只报条数。"""
    return {'id': image['id'], 'pid': image['pid'],
            'platform': image['platform'], 'page': image['page'],
            'title': image['title'], 'userid': image['userid'],
            'author': image['author'], 'authorid': image['authorid'],
            'width': image['width'], 'height': image['height'],
            'filename': image['filename'], 'extension': image['extension'],
            'size': image['size'], 'guest': image['guest'],
            'r18': image['r18'], 'ai': image['ai'],
            'tag_count': len(image['tags']),
            'rawurl': image['rawurl'], 'thumburl': image['thumburl']}


def hit_summary(hit):
    """搜索项可能缺少标题；展示真实字段名，不补造缺失字段。"""
    return {'id': hit['id'], 'field_keys': sorted(hit),
            'tag_count': len(hit['tags']),
            'rawurl': hit['rawurl'], 'thumburl': hit['thumburl']}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='列出 Cosine Gallery 图片并按页码与偏移翻页')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.cosine.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['cosine']
    site = example['site'] if args.site is None else args.site

    with Cosine(site, config_file=args.config, revalidate_secret='') as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        def pause():
            """首次请求不等待；其后每次请求前按 pause_seconds 串行暂停。"""
            if client.last_call:
                time.sleep(example['pause_seconds'])

        for page in example['pages']:
            pause()
            envelope = client.image_list(page=page, **example['list_query'])
            emit(client, 'image_list', requested_page=page,
                 total=envelope['total'], count=len(envelope['images']),
                 ids=[image['id'] for image in envelope['images']],
                 images=[image_summary(image) for image in envelope['images']])

        for offset in example['offsets']:
            pause()
            result = client.search(offset=offset, **example['search_query'])
            data = result['data']
            emit(client, 'search', requested_offset=offset,
                 success=result['success'], query=data['query'],
                 total=data['total'], limit=data['limit'], offset=data['offset'],
                 processing_time_ms=data['processingTimeMs'],
                 count=len(data['hits']),
                 ids=[hit['id'] for hit in data['hits']],
                 hits=[hit_summary(hit) for hit in data['hits']])


if __name__ == '__main__':
    main()
