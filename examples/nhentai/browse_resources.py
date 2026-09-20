# -*- coding: utf-8 -*-
"""浏览 nhentai 的画廊详情、标签、标签编号、画廊评论与站点配置（固定 5 次匿名 GET）。

依次调用：

1. ``gallery_show(658856)`` → ``GET https://nhentai.net/api/v2/galleries/658856``，返回详情对象：
   ``id``、``media_id``、``title``（``{'english': ..., 'japanese': ...|null, 'pretty': ...}``）、
   ``cover``/``thumbnail``（``{'path': ..., 'width': ..., 'height': ...}``）、``scanlator``（无则为
   空串）、``upload_date``（unix 时间戳）、``tags``（**完整标签对象**数组，字段见第 2 条）、
   ``num_pages``、``num_favorites`` 与 ``pages``（阅读器用的每一页：
   ``number``/``path``/``width``/``height``/``thumbnail``/``thumbnail_width``/``thumbnail_height``）。
   另外五个字段是可选块：``comments``、``related``、``suggestions`` 与两个标量 ``comment_count``、
   ``is_favorited``；它们默认是 null，只有在该路由的 ``include`` 查询参数里点名（``comments``、
   ``related``、``favorite``、``suggestions``，逗号分隔）才带上数据。本脚本**不传** ``include``，
   只报告这几个键里哪些非 null，不对它们的条数做任何期待。
2. ``tag_show('language', 'english')`` → ``GET https://nhentai.net/api/v2/tags/language/english``，
   返回一个完整标签对象 ``{'id': …, 'type': …, 'name': …, 'slug': …, 'url': …, 'count': …}``，
   另有可空的 ``description``、``is_community``、``pending_describe_id``。``type``/``slug`` 必须
   回显请求的两段路径；``count`` 是该标签下的画廊数。标签名与描述属于成人文本，脚本只打印
   类型、编号、``count`` 与名字字符数，**从不打印** ``name``/``description``。
3. ``tag_ids('12227,6346')`` → ``GET https://nhentai.net/api/v2/tags/ids?ids=12227%2C6346``，返回
   **裸数组**（没有信封），元素与第 2 条同形。``ids`` 是一个逗号分隔的字符串参数，客户端不做
   隐式拼接、也不把数组摊平，所以脚本直接把配置里的整串传进去，并把请求串与回来的编号并排
   打印——查不到的编号站点怎么处理由站点决定，脚本不补造条目。该路由单次上限 100 个编号。
4. ``gallery_comments(658856, page=1, per_page=2)`` →
   ``GET https://nhentai.net/api/v2/galleries/658856/comments?page=1&per_page=2``，返回与列表路由
   **同一个信封**（``result``/``num_pages``/``per_page``/``total``），每项是评论对象 ``{'id': …,
   'gallery_id': …, 'poster': {'id': …, 'username': …, 'slug': …, 'avatar_url': …, 'is_superuser': …,
   'is_staff': …}, 'post_date': …, 'body': …}``。``per_page`` 上限是 50（评论路由比列表路由的 100
   更小）。评论正文属于成人文本，脚本只打印编号、发布者编号、正文**字符数**与时间戳。
5. ``site_config()`` → ``GET https://nhentai.net/api/v2/config``，返回
   ``{'image_servers': [...], 'thumb_servers': [...], 'announcement': {...}|null}``：媒体与缩略图
   使用的服务器列表，加当前公告（可空）。脚本只打印服务器条数与公告的键名，不打印公告正文，
   也不据此拼任何媒体地址。

教学写法（字面参数，自足）：

    from anybooru import Nhentai

    with Nhentai('nhentai', api_key='') as client:
        detail = client.gallery_show(658856)
        print(detail['id'], detail['num_pages'], len(detail['tags']))
        tag = client.tag_show('language', 'english')
        print(tag['id'], tag['type'], tag['count'])
        tags = client.tag_ids('12227,6346')
        print([item['id'] for item in tags])
        comments = client.gallery_comments(658856, page=1, per_page=2)
        print(comments['num_pages'], [item['id'] for item in comments['result']])
        config = client.site_config()
        print(len(config['image_servers']), len(config['thumb_servers']))

每次调用打印两行 JSON：第一行是**调用后立刻**回显的真实 ``url``、状态码与 ``Content-Type``
（先于任何字段解析，所以后续取值即使抛错也能看到这次请求的真实状态），第二行是本次的结构
摘要（请求的编号/页码/每页条数、站点回的 ``num_pages``/``per_page``/``total``、条数、编号列表、
字段名列表与计数）。全篇不打印作品标题、评论正文与标签名/描述，也不下载任何媒体。参数与站点名
取自配置文件的 ``examples.nhentai`` 段（默认读包内 ``anybooru.json``）；``--config`` 换配置、
``--site`` 换站点，不传时取 ``examples.nhentai.site``。``api_key`` 显式传空串保持匿名，按
``pause_seconds`` 串行暂停，不重试、不跟随跳转。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Nhentai
from anybooru.resources import load_config

OPTIONAL_BLOCKS = ('comments', 'comment_count', 'related', 'is_favorited',
                   'suggestions')


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


def populated(detail):
    """可选块里哪些非 null：只报键名，不报内容。"""
    return [key for key in OPTIONAL_BLOCKS if detail.get(key) is not None]


def main():
    parser = argparse.ArgumentParser(description='浏览 nhentai 的画廊、标签、评论与站点配置')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.nhentai.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['nhentai']
    gallery_id = example['gallery_id']
    comments_query = example['comments_query']
    site = example['site'] if args.site is None else args.site

    with Nhentai(site, api_key='', config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        def pause():
            """首次请求不等待；其后每次请求前按 pause_seconds 串行暂停。"""
            if client.last_call:
                time.sleep(example['pause_seconds'])

        detail = client.gallery_show(gallery_id)
        evidence(client, 'gallery_show')
        summary('gallery_show', gallery_id=gallery_id,
                media_id=detail['media_id'],
                title_keys=sorted(detail['title']),
                cover=[detail['cover']['width'], detail['cover']['height']],
                scanlator_chars=len(detail['scanlator']),
                upload_date=detail['upload_date'],
                pages=detail['num_pages'], favorites=detail['num_favorites'],
                tags=len(detail['tags']),
                tag_types=sorted({tag['type'] for tag in detail['tags']}),
                page_objects=len(detail['pages']),
                page_keys=sorted(detail['pages'][0]) if detail['pages'] else None,
                populated_optional=populated(detail),
                field_keys=sorted(detail))

        pause()
        tag = client.tag_show(example['tag_type'], example['tag_slug'])
        evidence(client, 'tag_show')
        summary('tag_show', requested_type=example['tag_type'],
                requested_slug=example['tag_slug'], id=tag['id'],
                type=tag['type'], count=tag['count'],
                name_chars=len(tag['name']),
                description_present=tag.get('description') is not None,
                field_keys=sorted(tag))

        pause()
        tags = client.tag_ids(example['tag_ids'])
        evidence(client, 'tag_ids')
        summary('tag_ids', requested_ids=example['tag_ids'], count=len(tags),
                ids=[item['id'] for item in tags],
                types=[item['type'] for item in tags],
                field_keys=sorted(tags[0]) if tags else None)

        pause()
        comments = client.gallery_comments(gallery_id, **comments_query)
        evidence(client, 'gallery_comments')
        summary('gallery_comments', gallery_id=gallery_id,
                requested_page=comments_query['page'],
                requested_per_page=comments_query['per_page'],
                num_pages=comments['num_pages'], per_page=comments['per_page'],
                total=comments.get('total'), count=len(comments['result']),
                comment_ids=[item['id'] for item in comments['result']],
                poster_ids=[item['poster']['id'] for item in comments['result']],
                body_chars=[len(item['body']) for item in comments['result']],
                post_dates=[item['post_date'] for item in comments['result']])

        pause()
        config = client.site_config()
        evidence(client, 'site_config')
        announcement = config['announcement']
        summary('site_config', image_servers=len(config['image_servers']),
                thumb_servers=len(config['thumb_servers']),
                announcement_keys=sorted(announcement) if announcement else None,
                field_keys=sorted(config))


if __name__ == '__main__':
    main()
