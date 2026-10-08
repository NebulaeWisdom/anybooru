# -*- coding: utf-8 -*-
"""浏览 pixiv 的单张插画、分页图地址、用户资料与作品索引（固定 4 次匿名 GET）。

pixiv 的 web 前端接口在 ``https://www.pixiv.net`` 下的 ``/ajax`` 里，本文件用到插画与用户两组：

依次调用：

1. ``web_illust_show('149040133')`` → ``GET https://www.pixiv.net/ajax/illust/149040133``，返回
   ``{"error": false, "message": "", "body": {...}}``。``body`` 含 ``illustId``/``id``（同一个字符串
   编号）、``illustTitle``/``title``、``description``/``illustComment``、``illustType``、``xRestrict``、
   ``sl``、``createDate``/``uploadDate``、宽高 ``width``/``height``、``pageCount``、``userId``/
   ``userName``/``userAccount``、计数 ``bookmarkCount``/``likeCount``/``commentCount``/``viewCount``；
   图片地址在 ``urls`` 对象里，五个键 ``mini``/``thumb``/``small``/``regular``/``original``；
   ``tags`` 是对象，其 ``tags`` 数组每项含 ``tag``（标签名）、``locked``/``deletable``（布尔）、
   ``userId``/``userName``。所有图片地址只当字符串打印，脚本不下载媒体。
2. ``web_illust_pages('149040133')`` → ``GET https://www.pixiv.net/ajax/illust/149040133/pages``，
   返回 ``{"error": false, "message": "", "body": [...]}``：``body`` 是数组，每张图一项，含
   ``urls``（``thumb_mini``/``small``/``regular``/``original`` 四个地址）、``width``、``height``。
   这条路由一次给全所有分页的地址，没有页码参数。
3. ``web_user_show('27517', full=1)`` → ``GET https://www.pixiv.net/ajax/user/27517?full=1``，返回
   ``{"error": false, "message": "", "body": {...}}``。``body`` 含 ``userId``（字符串，和请求的一致）、
   ``name``、头像地址 ``image``/``imageBig``、``premium``（是否会员）、``isFollowed``、``partial``、
   ``following``（关注数）、``mypixivCount`` 等；``full=1`` 让这些统计字段一次带出。头像地址只当字符串
   打印。
4. ``web_user_profile_all('27517')`` → ``GET https://www.pixiv.net/ajax/user/27517/profile/all``，返回
   ``{"error": false, "message": "", "body": {...}}``。``body`` 是作品索引：``illusts`` 是
   ``{"作品编号": null}`` 的字典（编号有序、值一律是 ``null``，只给出编号清单，要详情再逐条调
   ``web_illust_show``）、``manga`` 同形、``novels`` 是数组、还有 ``mangaSeries``/``novelSeries``/
   ``collections``/``collectionIds``/``pickup``/``bookmarkCount`` 等。这条路由不分页。

边界（按站点自己的答复，客户端不补默认值、不夹取、不重试）：不存在的插画编号返回 404
``{"error": true, "message": "", "body": []}``（``body`` 是空数组而不是对象）；编号 ``0`` 这类非法值
返回 400 ``{"error": true, "message": "不正なリクエストです。", "body": []}``。同样路径的 app 面
``app_illust_detail`` 需要 ``Authorization: Bearer`` 令牌，匿名请求返回 400，正文是
``{"error": {"user_message": "", "message": "... invalid_request", "reason": "",
"user_message_details": {}}}``——本文件不带令牌，也不调 app 面。

教学写法（字面参数，自足）：

    from anybooru import Pixiv

    with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
        illust = client.web_illust_show('149040133')['body']
        print(illust['illustId'], illust['illustTitle'], illust['pageCount'],
              illust['urls']['original'])
        pages = client.web_illust_pages('149040133')['body']
        print(len(pages), pages[0]['width'], pages[0]['height'])
        user = client.web_user_show('27517', full=1)['body']
        print(user['userId'], user['name'], user['premium'])
        profile = client.web_user_profile_all('27517')['body']
        print(len(profile['illusts']), len(profile['manga']),
              profile['bookmarkCount'])

每次调用打印一行 JSON：方法名、真实 ``status_code``、``Content-Type``、真实 ``url``，以及该路由的
关键字段（请求的编号、标题、类型、宽高、分页数、标签、计数；用户报 userId、会员标志与关注统计；索引
报 ``illusts``/``manga``/``novels`` 条数与 ``bookmarkCount``）。图片地址（``urls``、头像 ``image``/
``imageBig``）只当字符串打印，不下载媒体；每行顶层的 ``url`` 永远指本次请求的真实地址，插画的地址
嵌在 ``urls`` 字典、用户的头像在 ``image``/``imageBig`` 键里，不会覆盖它。参数与站点名取自配置文件的
``examples.pixiv`` 段（默认读包内 ``anybooru.json``）：``illust_id``、``user_id`` 与 ``user_query``
分别对应上面四次调用；``--config`` 换配置、``--site`` 换站点，不传时取 ``examples.pixiv.site``。
``cookie``/``access_token``/``csrf_token`` 显式传空串保持匿名，不跟随跳转、不重试，每次请求前
（含第一次）都按 ``pause_seconds`` 串行暂停。
"""

import argparse
import json
import time

from anybooru import Pixiv
from anybooru.resources import load_config


def illust_summary(body):
    """详情 body：图片地址整块放在 urls 里，只当字符串打印，不下载。"""
    return {'illustId': body['illustId'], 'id': body['id'],
            'illustTitle': body['illustTitle'], 'title': body['title'],
            'illustType': body['illustType'], 'xRestrict': body['xRestrict'],
            'sl': body['sl'], 'userId': body['userId'],
            'userName': body['userName'], 'userAccount': body['userAccount'],
            'width': body['width'], 'height': body['height'],
            'pageCount': body['pageCount'], 'createDate': body['createDate'],
            'uploadDate': body['uploadDate'],
            'bookmarkCount': body['bookmarkCount'],
            'likeCount': body['likeCount'], 'viewCount': body['viewCount'],
            'commentCount': body['commentCount'],
            'description_chars': len(body['description']),
            'urls': body['urls'],
            'tags': [tag['tag'] for tag in body['tags']['tags']],
            'field_keys': sorted(body)}


def pages_summary(body):
    """分页路由一次性给全所有图：报张数、尺寸与各自的地址键。"""
    return {'count': len(body),
            'sizes': ['{}x{}'.format(page['width'], page['height'])
                      for page in body],
            'page_urls': [page['urls'] for page in body]}


def user_summary(body):
    """用户资料：头像地址在 image/imageBig 键里，只当字符串打印。"""
    return {'userId': body['userId'], 'name': body['name'],
            'premium': body['premium'], 'isFollowed': body['isFollowed'],
            'partial': body['partial'], 'following': body['following'],
            'mypixivCount': body['mypixivCount'],
            'image': body['image'], 'imageBig': body['imageBig'],
            'field_keys': sorted(body)}


def profile_summary(body):
    """作品索引：illusts 是编号到 null 的字典，只报条数与样本编号。"""
    ids = list(body['illusts'])
    return {'illusts_count': len(ids), 'illusts_sample_ids': ids[:5],
            'illusts_values_all_null': all(
                value is None for value in body['illusts'].values()),
            'manga_count': len(body['manga']),
            'novels_count': len(body['novels']),
            'bookmarkCount': body['bookmarkCount'],
            'field_keys': sorted(body)}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 pixiv 的插画详情、分页、用户与作品索引')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.pixiv.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['pixiv']
    site = example['site'] if args.site is None else args.site

    with Pixiv(site, cookie='', access_token='', csrf_token='',
               config_file=args.config) as client:
        # 每次请求前都暂停，第一次也不例外。
        time.sleep(example['pause_seconds'])
        detail = client.web_illust_show(example['illust_id'])
        emit(client, 'web_illust_show',
             requested_illust_id=example['illust_id'],
             **illust_summary(detail['body']))

        time.sleep(example['pause_seconds'])
        pages = client.web_illust_pages(example['illust_id'])
        emit(client, 'web_illust_pages',
             requested_illust_id=example['illust_id'],
             **pages_summary(pages['body']))

        time.sleep(example['pause_seconds'])
        user = client.web_user_show(example['user_id'], **example['user_query'])
        emit(client, 'web_user_show', requested_user_id=example['user_id'],
             **user_summary(user['body']))

        time.sleep(example['pause_seconds'])
        profile = client.web_user_profile_all(example['user_id'])
        emit(client, 'web_user_profile_all',
             requested_user_id=example['user_id'],
             **profile_summary(profile['body']))


if __name__ == '__main__':
    main()
