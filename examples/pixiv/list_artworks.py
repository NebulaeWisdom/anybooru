# -*- coding: utf-8 -*-
"""列出 pixiv 的关键词搜索结果两页，再取一次日榜第 1 页（固定 3 次匿名 GET）。

pixiv 的 web 前端接口在 ``https://www.pixiv.net`` 下：搜索走 ``/ajax/search/artworks/{词}``，
排行榜走站点根的 ``/ranking.php``。两者返回外壳不同，本文件各取一次。

依次调用：

1. ``web_search_artworks('cat', p=1, order='date_d', mode='all', s_mode='s_tag', type='all')``
   → ``GET https://www.pixiv.net/ajax/search/artworks/cat?word=cat&order=date_d&mode=all&p=1&s_mode=s_tag&type=all``，
   返回 ``{"error": false, "body": {...}}``——注意**没有** ``message`` 键（详情、用户那几条路由才有）。
   ``body["illustManga"]`` 是 ``{"data": [...], "total": 107077, "lastPage": 10, "bookmarkRanges": {...}}``：
   ``total`` 是命中总数、``lastPage`` 是站内允许的最大页码，``data`` 每项是一条插画摘要，含
   ``id``（字符串编号）、``title``、``illustType``（``0`` 插画 / ``1`` 漫画）、``xRestrict``、
   ``restrict``、``sl``、``url``（缩略图地址，只当字符串打印，不下载）、``description``、``tags``
   （字符串数组）、``userId``/``userName``、``width``/``height``、``pageCount``、``createDate``/
   ``updateDate``、``alt`` 等。``word`` 在路径段（``/artworks/cat``）与查询串（``?word=cat``）里
   各出现一次，客户端方法自己拼好，调用方只需传一次词。
2. 同参但 ``p=2`` → 同一路由的第二页，用来观察翻页。两页是实时数据，翻页期间新作品会挤进来，
   脚本只并排打印编号，不做“两页无交集”的断言，也不自行去重或补页。
3. ``web_ranking(mode='daily', p=1)`` → ``GET https://www.pixiv.net/ranking.php?mode=daily&p=1&format=json``
   （客户端方法会自动补 ``format=json``，否则该路由返回一整个 HTML 排行榜页）。这次返回**裸根对象**，
   不是 ``error``/``body`` 外壳：``{"contents": [...], "mode": "daily", "content": "all", "page": 1,
   "prev": false, "next": 2, "date": "20261007", "prev_date": ..., "next_date": ..., "rank_total": 500,
   "meta": {...}, "date_range_text": ..., "zoneConfig": {...}}``。``contents`` 每页 50 条，每项含
   ``rank``（页内名次）、``illust_id``（整数）、``user_id``（整数）、``title``、``url``（缩略图，只当
   字符串）、``illust_type``（字符串 ``"0"``/``"1"``）、``illust_page_count``（字符串）、``width``/
   ``height``、``view_count``/``rating_count``/``yes_rank``、``illust_content_type``（年龄分级布尔
   字段的对象）、``attr``、``is_masked`` 等。``rank_total`` 是榜单总名额（日榜 500），``next`` 是下一
   页码（``false`` 表示没有下一页）。

边界（按站点自己的答复，客户端不补默认值、不夹取、不重试）：``ranking.php`` 页码超出榜单范围返回 404
``{"error": "ランキング集計の範囲外です"}``；搜索 ``p=10000`` 仍是 200，但返回的是第 1 页样式的内容
（``lastPage`` 只有 10）——所以**HTTP 200 与数组非空都不代表这个页码有效**。本文件只请求配置文件里
列出的页码。

教学写法（字面参数，自足）：

    from anybooru import Pixiv

    with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
        first_page = client.web_search_artworks(
            'cat', p=1, order='date_d', mode='all', s_mode='s_tag', type='all')
        print(first_page['body']['illustManga']['total'],
              [item['id'] for item in first_page['body']['illustManga']['data']])
        second_page = client.web_search_artworks(
            'cat', p=2, order='date_d', mode='all', s_mode='s_tag', type='all')
        print([item['id'] for item in second_page['body']['illustManga']['data']])
        ranking = client.web_ranking(mode='daily', p=1)
        print(ranking['rank_total'], [item['rank'] for item in ranking['contents']])

每次调用打印一行 JSON：方法名、真实 ``status_code``、``Content-Type``、真实 ``url``，以及该路由的
关键字段（请求的页码/词、``total``/``lastPage``/``rank_total``、条数、编号与名次列表、摘要对象）。
缩略图 ``url`` 只当字符串打印，不下载媒体；每行顶层的 ``url`` 永远指本次请求的真实地址，条目自己的
缩略图地址嵌在 ``artworks``/``contents`` 数组里，不会覆盖它。参数与站点名取自配置文件的
``examples.pixiv`` 段（默认读包内 ``anybooru.json``）：``word`` 是搜索词、``search_query`` 是搜索
的查询参数、``pages`` 是页码列表、``ranking_query`` 是排行榜参数；``--config`` 换配置、``--site``
换站点，不传时取 ``examples.pixiv.site``。``cookie``/``access_token``/``csrf_token`` 显式传空串保持
匿名，不跟随跳转、不重试，每次请求前（含第一次）都按 ``pause_seconds`` 串行暂停。
"""

import argparse
import json
import time

from anybooru import Pixiv
from anybooru.resources import load_config


def artwork_summary(item):
    """搜索条目的摘要：缩略图地址只当字符串打印，不下载。"""
    return {'id': item['id'], 'title': item['title'],
            'illustType': item['illustType'], 'xRestrict': item['xRestrict'],
            'restrict': item['restrict'], 'sl': item['sl'],
            'url': item['url'], 'userId': item['userId'],
            'userName': item['userName'], 'width': item['width'],
            'height': item['height'], 'pageCount': item['pageCount'],
            'createDate': item['createDate'], 'updateDate': item['updateDate'],
            'description': item['description'], 'tags': item['tags'],
            'alt': item['alt']}


def search_summary(listing, page, word):
    """搜索返回 {"error", "body"}，插画数组在 body.illustManga 里，没有 message。"""
    manga = listing['body']['illustManga']
    return {'requested_page': page, 'requested_word': word,
            'error': listing['error'],
            'body_keys': sorted(listing['body']),
            'illustManga_keys': sorted(manga),
            'total': manga['total'], 'lastPage': manga['lastPage'],
            'count': len(manga['data']),
            'ids': [item['id'] for item in manga['data']],
            'artworks': [artwork_summary(item) for item in manga['data']]}


def ranking_summary(ranking):
    """排行榜是裸根对象，没有 error/body 外壳，逐键报告。"""
    return {'page': ranking['page'], 'mode': ranking['mode'],
            'content': ranking['content'], 'prev': ranking['prev'],
            'next': ranking['next'], 'date': ranking['date'],
            'rank_total': ranking['rank_total'],
            'field_keys': sorted(ranking),
            'count': len(ranking['contents']),
            'ranks': [item['rank'] for item in ranking['contents']],
            'ids': [item['illust_id'] for item in ranking['contents']],
            'contents': [{'rank': item['rank'], 'illust_id': item['illust_id'],
                          'user_id': item['user_id'], 'title': item['title'],
                          'illust_type': item['illust_type'],
                          'illust_page_count': item['illust_page_count'],
                          'width': item['width'], 'height': item['height'],
                          'url': item['url'], 'view_count': item['view_count'],
                          'rating_count': item['rating_count'],
                          'yes_rank': item['yes_rank'], 'attr': item['attr'],
                          'tags': item['tags']}
                         for item in ranking['contents']]}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='列出 pixiv 的搜索页与日榜一页')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.pixiv.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['pixiv']
    site = example['site'] if args.site is None else args.site
    word = example['word']
    search_query = example['search_query']

    with Pixiv(site, cookie='', access_token='', csrf_token='',
               config_file=args.config) as client:
        for page in example['pages']:
            # 每次请求前都暂停，第一次也不例外。
            time.sleep(example['pause_seconds'])
            listing = client.web_search_artworks(word, p=page, **search_query)
            emit(client, 'web_search_artworks',
                 **search_summary(listing, page, word))

        time.sleep(example['pause_seconds'])
        ranking = client.web_ranking(**example['ranking_query'])
        emit(client, 'web_ranking', **ranking_summary(ranking))


if __name__ == '__main__':
    main()
