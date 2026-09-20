# -*- coding: utf-8 -*-
"""列出 ArtStation 的全局作品页与按标题过滤的搜索页（固定 4 次匿名 GET）。

依次调用：

1. ``project_list(page=1, per_page=2)`` →
   ``GET https://www.artstation.com/projects.json?page=1&per_page=2``，返回
   ``{"data": [...], "total_count": N}``。``data`` 每项是作品卡片，含站内 ``id``、短哈希
   ``hash_id``、``title``、``permalink``（形如 ``https://www.artstation.com/artwork/1LxzVq``）、
   ``assets_count``、封面对象 ``cover``（缩略图地址在 ``small_square_url`` 等键里）、
   标签 ``tag_list``（实测样本是 ``null``，所以脚本按原值打印而不当数组用）、投稿人
   ``user``（含 ``username``）与 ``views_count``。
2. ``project_list(page=2, per_page=2)`` → 同一路由的下一页。两页不保证互不重复：全局列表
   是实时数据，翻页期间新作品会挤进来，脚本因此只并排打印编号，不做“两页无交集”的断言。
3. ``project_search(query='', page=1, per_page=3, sorting='relevance', filters='[{"field":"title","method":"contain","value":"dragon"}]')``
   → ``GET https://www.artstation.com/api/v2/search/projects.json?query=&page=1&per_page=3&sorting=relevance&filters=%5B...%5D``，
   返回 ``{"total_count": N, "data": [...]}``。搜索卡片比全局列表瘦得多，只有 9 个键：
   ``id``、``hash_id``、``url``、``smaller_square_cover_url``、``hide_as_adult``、
   ``is_adult_content``、``title``、``icons``、``user``——没有 ``assets_count``、没有
   ``views_count``、没有 ``tag_list``，``user`` 也只有几个键，不要拿全局列表的字段集合去读它。
   ``filters`` 必须是 **JSON 字符串**（不是 Python 列表，也不是嵌套的 ``filters[][field]``
   表单参数），写成 ``'[{"field":"title","method":"contain","value":"dragon"}]'``；可过滤的字段名
   来自 ``search_filter_fields()``（当前 12 项，每项 ``{"name", "type"}``；``select_multiple``
   类型的项另带 ``select_options`` 数组——实测样本 ``category_ids`` 59 项、``asset_types`` 6 项、
   ``medium_ids``/``medium_id`` 11 项、``software_ids`` 410 项，而 ``title``/``artist_name``
   是 ``text``，没有这个键，所以别假定每项都有）。
4. ``project_search(..., page=2, ...)`` → 同一过滤条件的第 2 页。实测样本里该过滤条件命中的
   标题形如 ``Dragon and mouse``、``Omakase! Dragonslayer :: 屠龍``、``Dragon's Breath``。

这条路线的边界（都按站点自己的答复，客户端不补默认值、不夹取）：``projects.json`` 的
``per_page`` 上限是 50、``api/v2/search/projects.json`` 是 75，超出返回 HTTP 400；
搜索的 ``per_page`` 下限是 3，所以本文件用 ``per_page=3`` 而不是 2，``per_page=2`` 会直接
400；搜索缺 ``page`` 或 ``per_page`` 同样返回 400（错误体是 ``{"data": "..."}``），而不是
补成默认页码。``sorting`` 只实测过 ``relevance``，其它取值（如 ``likes``/``date``）未实测。

教学写法（字面参数，自足）：

    from anybooru import ArtStation

    with ArtStation('artstation') as client:
        page = client.project_list(page=1, per_page=2)
        print(page['total_count'], [item['hash_id'] for item in page['data']])
        hits = client.project_search(
            query='', page=1, per_page=3, sorting='relevance',
            filters='[{"field":"title","method":"contain","value":"dragon"}]')
        print(hits['total_count'], hits['data'][0]['title'],
              hits['data'][0]['smaller_square_cover_url'])

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL，以及该路由的关键
字段（编号、短哈希、标题、总数、条数、过滤条件）。封面与媒体地址只当字符串打印，不下载媒体。
参数与站点名取自配置文件的 ``examples.artstation`` 段（默认读包内 ``anybooru.json``）；
``--config`` 换配置、``--site`` 换站点，不传时取 ``examples.artstation.site``。不跟随跳转、
不重试，每次请求前（含第一次）都按 ``pause_seconds`` 串行暂停。
"""

import argparse
from functools import partial
import json
import time

from anybooru import ArtStation
from anybooru.resources import load_config


def project_summary(item):
    """全局作品卡片摘要：媒体地址只当字符串打印。"""
    return {'id': item['id'], 'hash_id': item['hash_id'],
            'title': item['title'], 'permalink': item['permalink'],
            'assets_count': item['assets_count'], 'tag_list': item['tag_list'],
            'views_count': item['views_count'],
            'user': item['user']['username'],
            'cover_small_square_url': item['cover']['small_square_url']}


def search_summary(item):
    """搜索卡片只有 9 个键，没有 assets_count/views_count/tag_list。"""
    return {'id': item['id'], 'hash_id': item['hash_id'],
            'title': item['title'], 'url': item['url'],
            'is_adult_content': item['is_adult_content'],
            'hide_as_adult': item['hide_as_adult'],
            'smaller_square_cover_url': item['smaller_square_cover_url'],
            'user': item['user']['username']}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='列出 ArtStation 的全局作品与过滤搜索')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.artstation.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['artstation']
    site = example['site'] if args.site is None else args.site
    list_query = example['list_query']
    search_query = example['search_query']

    with ArtStation(site, config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        for page in example['pages']:
            # 每次请求前都暂停，第一次也不例外。
            time.sleep(example['pause_seconds'])
            listing = client.project_list(page=page, **list_query)
            emit(client, 'project_list', page=page,
                 total_count=listing['total_count'],
                 count=len(listing['data']),
                 ids=[item['id'] for item in listing['data']],
                 projects=[project_summary(item) for item in listing['data']])

        for page in example['pages']:
            time.sleep(example['pause_seconds'])
            hits = client.project_search(page=page, **search_query)
            emit(client, 'project_search', page=page,
                 query=search_query['query'],
                 filters=search_query['filters'],
                 total_count=hits['total_count'], count=len(hits['data']),
                 ids=[item['id'] for item in hits['data']],
                 hash_ids=[item['hash_id'] for item in hits['data']],
                 results=[search_summary(item) for item in hits['data']])


if __name__ == '__main__':
    main()
