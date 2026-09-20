# -*- coding: utf-8 -*-
"""列出 nhentai 画廊：两页列表 + 一次按标签语法搜索（固定 3 次匿名 GET）。

依次调用：

1. ``gallery_list(page=1, per_page=2)`` → ``GET https://nhentai.net/api/v2/galleries?page=1&per_page=2``，
   返回 ``{'result': [...], 'num_pages': N, 'per_page': N, 'total': N|null}``。``result`` 的每项是
   列表用的轻量画廊对象：``id``（站内整数编号）、``media_id``（媒体编号字符串）、``english_title``
   与 ``japanese_title``（可能为 null）、``thumbnail``（缩略图路径）、``thumbnail_width``/
   ``thumbnail_height``、``num_pages``、``num_favorites``、``tag_ids``（整数标签编号数组）与
   ``blacklisted``（该画廊是否命中当前调用者的黑名单，匿名与非匿名都可能出现）。``total`` 可为
   null，``num_pages`` 是站点按当前 ``per_page`` 算出的页数，两者都会随站点内容变化，脚本
   照实打印而不当成固定值。
2. 同参但 ``page=2`` → 同上路由，用来观察翻页：脚本把两页的编号都打印出来，是否重复由输出
   直接看出，脚本不自行去重、不补页、也不假设站点一定给满一页。
3. ``search(query='language:english', sort='date', page=1)`` →
   ``GET https://nhentai.net/api/v2/search?query=language%3Aenglish&sort=date&page=1``，返回与列表
   路由**同一个信封**，所以两个路由的消费方式一致。``query`` 是站点自己的搜索语法：关键词、
   ``"exact phrase"``、``-word`` 取反、``artist:name`` / ``language:english`` / ``tag:"two words"``
   这类标签过滤、``pages:>10`` / ``favorites:>=100`` 数值过滤与 ``uploaded:<7d`` 日期过滤；
   ``:`` 由共享层按查询串规则编码成 ``%3A``，``sort`` 取 ``date``/``popular``/``popular-today``/
   ``popular-week``/``popular-month``，脚本不手工拼 URL、也不改写站点回来的排序。

本文件的输出遵守一条硬规则：**不打印任何作品标题、评论正文或标签名/标签描述**。每个条目只打印
编号与结构信息——``id``、``media_id``、页数、收藏数、``tag_ids`` 条数、``blacklisted``、缩略图
宽高、``japanese_title`` 是否存在、以及该条目的字段名列表；文本字段只报字符数或是否存在。
也不请求任何图片或缩略图。

教学写法（字面参数，自足）：

    from anybooru import Nhentai

    with Nhentai('nhentai', api_key='') as client:
        first = client.gallery_list(page=1, per_page=2)
        print(first['num_pages'], first['total'], [item['id'] for item in first['result']])
        second = client.gallery_list(page=2, per_page=2)
        print([item['media_id'] for item in second['result']])
        found = client.search(query='language:english', sort='date', page=1)
        print(found['num_pages'], [item['id'] for item in found['result']])

每次调用打印两行 JSON：第一行是**调用后立刻**回显的真实 ``url``、状态码与 ``Content-Type``
（在任何字段解析之前打印，所以后续取值即使抛错也能看到这次请求的真实状态），第二行是本次的
结构摘要（请求的页码/每页条数、站点回的 ``num_pages``/``per_page``/``total``、条数、编号列表与
条目摘要）。参数与站点名取自配置文件的 ``examples.nhentai`` 段（默认读包内 ``anybooru.json``）；
``--config`` 换配置、``--site`` 换站点，不传时取 ``examples.nhentai.site``。``api_key`` 显式传空串
保持匿名，按 ``pause_seconds`` 串行暂停，不重试、不跟随跳转。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Nhentai
from anybooru.resources import load_config


def item_summary(item):
    """列表条目摘要：只给编号与结构，标题等文本一律不出现在输出里。"""
    return {'id': item['id'], 'media_id': item['media_id'],
            'num_pages': item['num_pages'], 'num_favorites': item['num_favorites'],
            'tag_ids': len(item['tag_ids']), 'blacklisted': item['blacklisted'],
            'thumbnail': [item['thumbnail_width'], item['thumbnail_height']],
            'japanese_title': 'japanese_title' in item,
            'field_keys': sorted(item)}


def evidence(client, method):
    """调用后立刻回显真实 URL、状态码与 Content-Type，先于任何字段解析。"""
    print(json.dumps({'method': method,
                      'status_code': client.last_call['status_code'],
                      'content_type': client.last_call['headers'].get('Content-Type'),
                      'url': client.last_call['url']}, ensure_ascii=False), flush=True)


def summary(method, **fields):
    line = {'method': method}
    line.update(fields)
    print(json.dumps(line, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description='列出 nhentai 画廊并按页码翻页与搜索')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.nhentai.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['nhentai']
    site = example['site'] if args.site is None else args.site

    with Nhentai(site, api_key='', config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        def pause():
            """首次请求不等待；其后每次请求前按 pause_seconds 串行暂停。"""
            if client.last_call:
                time.sleep(example['pause_seconds'])

        for page in example['pages']:
            pause()
            envelope = client.gallery_list(page=page, **example['list_query'])
            evidence(client, 'gallery_list')
            summary('gallery_list', requested_page=page,
                    requested_per_page=example['list_query']['per_page'],
                    num_pages=envelope['num_pages'],
                    per_page=envelope['per_page'],
                    total=envelope.get('total'),
                    count=len(envelope['result']),
                    ids=[item['id'] for item in envelope['result']],
                    items=[item_summary(item) for item in envelope['result']])

        pause()
        found = client.search(**example['search_query'])
        evidence(client, 'search')
        summary('search', search_query=example['search_query'],
                num_pages=found['num_pages'], per_page=found['per_page'],
                total=found.get('total'), count=len(found['result']),
                ids=[item['id'] for item in found['result']],
                items=[item_summary(item) for item in found['result']])


if __name__ == '__main__':
    main()
