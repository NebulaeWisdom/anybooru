# -*- coding: utf-8 -*-
"""浏览 Wallhaven 的单张详情、标签、某用户的公开合集与合集内容（固定 4 次匿名 GET）。

Wallhaven 的 JSON API 在站点根的 ``/api/v1`` 下，参数与返回字段见站点 API 页
``https://wallhaven.cc/help/api``（本文件用到 "Accessing Wallpaper information"、"Tag info"
与 "User Collections"）。

依次调用：

1. ``wallpaper_show('pom5lj')`` → ``GET https://wallhaven.cc/api/v1/w/pom5lj``，返回
   ``{"data": {...}}``。墙体对象就是在搜索摘要之上多了两个键：``uploader``
   （``username``、``group``，以及头像 ``avatar``，带 ``200px``/``128px``/``32px``/``20px``
   四个地址）与 ``tags``（每项是 ``id``、``name``、``alias``、``category_id``、``category``、
   ``purity``、``created_at`` 的完整标签对象）。其余键与搜索摘要相同（``id``、``url``、
   ``short_url``、``views``、``favorites``、``source``、``purity``、``category``、宽高与
   ``resolution``/``ratio``、``file_size``、``file_type``、``created_at``、``colors``、
   ``path``、``thumbs``）。头像与图地址只当字符串打印，脚本不下载媒体。API v1 **没有**单独的
   相似壁纸路由：相似用 ``wallpaper_search(q='like:pom5lj')``。
2. ``tag_show(1)`` → ``GET https://wallhaven.cc/api/v1/tag/1``，返回 ``{"data": {...}}``：
   ``id``、``name``、``alias``、``category_id``、``category``（如 ``'Anime & Manga'``）、
   ``purity``、``created_at``。编号 1 就是 ``anime``。编号是路径段，站点不认的编号返回它的 404。
3. ``user_collections('ThorRagnarok')`` → ``GET https://wallhaven.cc/api/v1/collections/ThorRagnarok``，
   返回 ``{"data": [...]}``，每项只有 ``id``、``label``（合集名）、``views``、``public``
   （``1``/``0``）、``count``（合集内壁纸数）。别人只看得到该账号的**公开**合集；账号本人连私有
   一起列出的是另一条路由 ``/api/v1/collections``，它按发送的 key 认人、匿名访问返回 404
   ``{"error": "Nothing here"}``（不是 401），本文件不带 key 所以不调它。
4. ``collection_wallpapers('ThorRagnarok', 274175, purity='100', page=1)`` →
   ``GET https://wallhaven.cc/api/v1/collections/ThorRagnarok/274175?purity=100&page=1``，返回
   ``{"data": [...], "meta": {...}}``：``data`` 与搜索摘要同形（每个条目都有 ``id``、``url``、
   ``short_url``、``path``、``thumbs`` 等，媒体地址只当字符串打印）。``meta`` 只有
   ``current_page``、``last_page``、``per_page``、``total`` **四个键**——和搜索不同，合集内容
   不带 ``query`` 与 ``seed``，所以别拿搜索的 ``meta`` 键集去套它。这条路由的参数里只有
   ``purity`` 是搜索参数；带 key 的本人能读私有合集，其他人只看得到公开的。

边界（全部按站点自己的答复，客户端不补默认值、不夹取、不重试）：不存在的壁纸编号（例如
``000000``）返回 404 ``{"error": "Nothing here"}``，不存在的标签编号也是 404；请求 NSFW 壁纸
而不带有效 key 返回 401 ``{"error": "Unauthorized"}``。本文件的样本 ``pom5lj`` 是 ``sfw``，
``tag_id=1`` 是 ``anime``，``ThorRagnarok`` 的公开合集实测有三项，``274175`` 是其中的 ``Default``。

教学写法（字面参数，自足）：

    from anybooru import Wallhaven

    with Wallhaven('wallhaven', apikey='') as client:
        wallpaper = client.wallpaper_show('pom5lj')['data']
        print(wallpaper['id'], wallpaper['resolution'],
              wallpaper['uploader']['username'], len(wallpaper['tags']))
        tag = client.tag_show(1)['data']
        print(tag['id'], tag['name'], tag['category'])
        collections = client.user_collections('ThorRagnarok')['data']
        print([(item['id'], item['label']) for item in collections])
        collection_page = client.collection_wallpapers('ThorRagnarok', 274175,
                                                       purity='100', page=1)
        print(collection_page['meta']['total'],
              [item['id'] for item in collection_page['data']])

每次调用打印一行 JSON：方法名、真实 ``status_code``、``Content-Type``、真实 ``url``，以及该路由的
关键字段（请求的编号/用户名、``meta`` 逐键、条数、编号列表与对象摘要；标签报 ``name``/``category``，
墙面报分辨率、体积、``purity``、``category``、上传者与标签数，合集报名字、浏览数、是否公开与条数）。
``path``、``thumbs``、头像地址只当字符串打印，不下载媒体。顶层 ``url`` 永远是这次请求的真实 URL；
壁纸自己的站内地址为了避免同名覆盖，在详情那一行打成 ``wallpaper_url``（合集条目嵌在 ``wallpapers``
数组里，仍叫 ``url``）。参数与站点名取自配置文件的
``examples.wallhaven`` 段（默认读包内 ``anybooru.json``）：``wallpaper_id``、``tag_id``、
``username``、``collection_id`` 与 ``collection_query`` 分别对应上面四次调用；``--config`` 换配置、
``--site`` 换站点，不传时取 ``examples.wallhaven.site``。``apikey`` 显式传空串保持匿名，不跟随跳转、
不重试，每次请求前（含第一次）都按 ``pause_seconds`` 串行暂停。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Wallhaven
from anybooru.resources import load_config


def wallpaper_summary(item):
    """搜索/合集条目的摘要：媒体地址只当字符串打印，不下载。"""
    return {'id': item['id'], 'url': item['url'], 'short_url': item['short_url'],
            'views': item['views'], 'favorites': item['favorites'],
            'source': item['source'], 'purity': item['purity'],
            'category': item['category'], 'resolution': item['resolution'],
            'ratio': item['ratio'], 'file_size': item['file_size'],
            'file_type': item['file_type'], 'created_at': item['created_at'],
            'colors': item['colors'], 'path': item['path'],
            'thumb_keys': sorted(item['thumbs'])}


def wallpaper_detail(data):
    """详情比摘要多 uploader 与 tags：标签名与类别照原值打印。

    顶层的 ``url`` 留给 ``emit`` 打这次请求的真实 URL，所以壁纸自己的站内地址在这里改名
    ``wallpaper_url``；合集条目嵌在 ``wallpapers`` 数组里不会碰撞，仍叫 ``url``。
    """
    uploader = data['uploader']
    summary = wallpaper_summary(data)
    summary['wallpaper_url'] = summary.pop('url')
    summary.update(
        uploader={'username': uploader['username'], 'group': uploader['group'],
                  'avatar_keys': sorted(uploader['avatar'])},
        tags=[{'id': tag['id'], 'name': tag['name'], 'alias': tag['alias'],
               'category_id': tag['category_id'], 'category': tag['category'],
               'purity': tag['purity'], 'created_at': tag['created_at']}
              for tag in data['tags']],
        field_keys=sorted(data))
    return summary


def tag_summary(data):
    """标签对象：编号 1 是 anime。"""
    return {'id': data['id'], 'name': data['name'], 'alias': data['alias'],
            'category_id': data['category_id'], 'category': data['category'],
            'purity': data['purity'], 'created_at': data['created_at'],
            'field_keys': sorted(data)}


def collection_summary(item):
    """公开合集条目只有 id/label/views/public/count 五个键。"""
    return {'id': item['id'], 'label': item['label'], 'views': item['views'],
            'public': item['public'], 'count': item['count'],
            'field_keys': sorted(item)}


def meta_summary(meta):
    """合集内容的 meta 只有四个键，所以逐键报告、缺的键不硬造。"""
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
    parser = argparse.ArgumentParser(description='浏览 Wallhaven 的详情、标签、用户合集与合集内容')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.wallhaven.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['wallhaven']
    site = example['site'] if args.site is None else args.site
    collection_query = example['collection_query']

    with Wallhaven(site, apikey='', config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        # 每次请求前都暂停，第一次也不例外。
        time.sleep(example['pause_seconds'])
        detail = client.wallpaper_show(example['wallpaper_id'])
        emit(client, 'wallpaper_show',
             requested_wallpaper_id=example['wallpaper_id'],
             **wallpaper_detail(detail['data']))

        time.sleep(example['pause_seconds'])
        tag = client.tag_show(example['tag_id'])
        emit(client, 'tag_show', requested_tag_id=example['tag_id'],
             **tag_summary(tag['data']))

        time.sleep(example['pause_seconds'])
        collections = client.user_collections(example['username'])
        emit(client, 'user_collections', requested_username=example['username'],
             count=len(collections['data']),
             ids=[item['id'] for item in collections['data']],
             labels=[item['label'] for item in collections['data']],
             collections=[collection_summary(item) for item in collections['data']])

        time.sleep(example['pause_seconds'])
        items = client.collection_wallpapers(
            example['username'], example['collection_id'], **collection_query)
        emit(client, 'collection_wallpapers', requested_username=example['username'],
             requested_collection_id=example['collection_id'],
             collection_query=collection_query, count=len(items['data']),
             ids=[item['id'] for item in items['data']],
             wallpapers=[wallpaper_summary(item) for item in items['data']],
             **meta_summary(items['meta']))


if __name__ == '__main__':
    main()
