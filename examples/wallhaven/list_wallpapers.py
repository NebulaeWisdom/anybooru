# -*- coding: utf-8 -*-
"""列出 Wallhaven 的过滤搜索两页与一次精确标签编号搜索（固定 3 次匿名 GET）。

Wallhaven 的 JSON API 在站点根的 ``/api/v1`` 下，参数与返回字段见站点 API 页
``https://wallhaven.cc/help/api``（本文件用到其中的 "Searching and listings"）。

依次调用：

1. ``wallpaper_search(page=1, q='nature', categories='100', purity='100', sorting='date_added', order='desc')``
   → ``GET https://wallhaven.cc/api/v1/search?page=1&q=nature&categories=100&purity=100&sorting=date_added&order=desc``，
   返回 ``{"data": [...], "meta": {...}}``。``data`` 每项是壁纸摘要对象：``id``（六字符站内编号）、
   ``url``（形如 ``https://wallhaven.cc/w/2166q9``）、``short_url``（``https://whvn.cc/2166q9``）、
   ``views``、``favorites``、``source``、``purity``（``sfw``/``sketchy``/``nsfw``）、``category``
   （``general``/``anime``/``people``）、``dimension_x``/``dimension_y``/``resolution``/``ratio``、
   ``file_size``、``file_type``、``created_at``、``colors`` 与媒体地址 ``path``、``thumbs``
   （``large``/``original``/``small``）——完整图与缩略图地址只当字符串打印，脚本不下载媒体；
   摘要里**没有** ``uploader`` 与 ``tags``，这两个键只在单张详情里出现（见 browse_resources.py）。
   ``meta`` 带 ``current_page``、``last_page``、``per_page``、``total``、``query``、``seed``：
   普通关键词搜索的 ``query`` 是字符串（这里 ``'nature'``），``seed`` 只有 ``sorting='random'`` 时才有值，
   本文件不是随机排序所以是 ``null``。``page`` 从 1 起，每页 24 条（站点文档值；客户端不补 ``per_page``，
   也不夹取页码）。
2. 同参但 ``page=2`` → 同一路由的第二页，用来观察翻页。两页是实时数据，翻页期间新壁纸会挤进来，
   脚本只并排打印编号，不做“两页无交集”的断言，也不自行去重或补页。
3. ``wallpaper_search(q='id:1', purity='100')`` →
   ``GET https://wallhaven.cc/api/v1/search?q=id%3A1&purity=100``，``id:1`` 是精确标签编号搜索
   （编号 1 是 ``anime``）。此时 ``meta.query`` 不再是字符串，而是 ``{"id": 1, "tag": "anime"}``
   对象——同一个 ``meta`` 键在两种查询下形状不同，读之前先看类型。``id:`` 查询不能与别的查询片段
   组合；相似壁纸用 ``q='like:<编号>'``、某人的上传用 ``q='@用户名'``，API v1 没有单独的 similar
   或 user 路由。

边界（全部由站点自己的答复决定，客户端不补默认值、不夹取、不重试）：``page`` 超出末页返回 400
``{"error": "Bad Request"}``，``page=0`` 返回 500，非数字 ``page`` 被站点当成第 1 页返回 200；
``sorting`` 写成非法值仍是 200，但 ``data`` 是空数组而 ``meta.total``/``last_page`` 仍是正数——
所以**空数组不等于翻到底**。匿名请求 ``purity='001'``（请求 ``nsfw`` 位）返回空结果，请求 NSFW 位
不带有效 key 时站点返回 401 ``{"error": "Unauthorized"}``，本文件只请求 ``sfw``（``purity='100'``）。

教学写法（字面参数，自足）：

    from anybooru import Wallhaven

    with Wallhaven('wallhaven', apikey='') as client:
        first_page = client.wallpaper_search(
            page=1, q='nature', categories='100', purity='100',
            sorting='date_added', order='desc')
        print(first_page['meta']['total'], [item['id'] for item in first_page['data']])
        second_page = client.wallpaper_search(
            page=2, q='nature', categories='100', purity='100',
            sorting='date_added', order='desc')
        print([item['short_url'] for item in second_page['data']])
        exact_tag_search = client.wallpaper_search(q='id:1', purity='100')
        print(exact_tag_search['meta']['query'], exact_tag_search['meta']['total'])

每次调用打印一行 JSON：方法名、真实 ``status_code``、``Content-Type``、真实 ``url``，以及该路由的
关键字段（请求的页码/查询、``meta`` 逐键、条数、编号列表与壁纸摘要）。``colors``、``path``、
``thumbs`` 只当字符串打印，不下载媒体。参数与站点名取自配置文件的 ``examples.wallhaven`` 段
（默认读包内 ``anybooru.json``）：``search_query`` 是前两次的查询、``pages`` 是页码列表、
``tag_query`` 是第三次的精确标签查询；``--config`` 换配置、``--site`` 换站点，不传时取
``examples.wallhaven.site``。``apikey`` 显式传空串保持匿名，不跟随跳转、不重试，每次请求前
（含第一次）都按 ``pause_seconds`` 串行暂停。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Wallhaven
from anybooru.resources import load_config


def wallpaper_summary(item):
    """搜索条目的摘要：媒体地址只当字符串打印，不下载。"""
    return {'id': item['id'], 'url': item['url'], 'short_url': item['short_url'],
            'views': item['views'], 'favorites': item['favorites'],
            'source': item['source'], 'purity': item['purity'],
            'category': item['category'], 'resolution': item['resolution'],
            'ratio': item['ratio'], 'file_size': item['file_size'],
            'file_type': item['file_type'], 'created_at': item['created_at'],
            'colors': item['colors'], 'path': item['path'],
            'thumb_keys': sorted(item['thumbs'])}


def meta_summary(meta):
    """meta 逐键打印：关键词搜索有 query/seed，先看键集再取值。"""
    line = {'meta_keys': sorted(meta), 'current_page': meta['current_page'],
            'last_page': meta['last_page'], 'per_page': meta['per_page'],
            'total': meta['total']}
    for key in ('query', 'seed'):
        if key in meta:
            line[key] = meta[key]
    return line


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='列出 Wallhaven 的搜索页与精确标签查询')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.wallhaven.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['wallhaven']
    site = example['site'] if args.site is None else args.site
    search_query = example['search_query']
    tag_query = example['tag_query']

    with Wallhaven(site, apikey='', config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        for page in example['pages']:
            # 每次请求前都暂停，第一次也不例外。
            time.sleep(example['pause_seconds'])
            listing = client.wallpaper_search(page=page, **search_query)
            emit(client, 'wallpaper_search', requested_page=page,
                 requested_query=search_query['q'], search_query=search_query,
                 count=len(listing['data']),
                 ids=[item['id'] for item in listing['data']],
                 wallpapers=[wallpaper_summary(item) for item in listing['data']],
                 **meta_summary(listing['meta']))

        time.sleep(example['pause_seconds'])
        found = client.wallpaper_search(**tag_query)
        emit(client, 'wallpaper_search', requested_tag_query=tag_query,
             count=len(found['data']),
             ids=[item['id'] for item in found['data']],
             wallpapers=[wallpaper_summary(item) for item in found['data']],
             **meta_summary(found['meta']))


if __name__ == '__main__':
    main()
