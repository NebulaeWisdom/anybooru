# -*- coding: utf-8 -*-
"""浏览 ArtStation 的用户资料、专辑、随机作品与评论（固定 4 次匿名 GET）。

依次调用：

1. ``user_show('timwarnock')`` → ``GET https://www.artstation.com/users/timwarnock.json``，
   返回**没有信封**的用户对象，实测样本 70 个键：``id``、``username``、``full_name``、
   ``headline``、``permalink``、``projects_count``、``followers_count``、
   ``followees_count``，以及 ``albums_with_community_projects``（默认专辑，实测样本一项：
   ``id=95733``、``title='All'``、``album_type='all_projects'``）。同一个人还有另外两个
   用户路由：``user_quick`` 与 ``user_profile`` 返回的键集不同（实测样本 59 与 63 个键），
   所以脚本只读 ``user_show`` 这一份对象自己的键，并按原值打印 ``headline``。
2. ``album_projects(104104, page=1, per_page=4)`` →
   ``GET https://www.artstation.com/api/v2/community/projects/by_album.json?album_id=104104&page=1&per_page=4``，
   返回 ``{"total_count": N, "data": [...]}``（实测样本 ``total_count=49``、4 条）。专辑编号
   是**查询参数** ``album_id``，不是路径段。专辑条目是另一套键（实测样本 13 个）：它带
   ``album_id``、``album_title``、``position`` 和 ``assets`` 数组，却没有全局列表的
   ``user``/``views_count``/``tag_list``/``assets_count``；实测样本的 asset 有 ``id``、
   ``asset_type``、``width``、``height``、``title``、``has_embedded_player``、
   ``small_image_url``、``large_image_url``——这几个键跟随机作品那条路由的 asset 不是同一套，
   别互相套用。
3. ``project_random()`` → ``GET https://www.artstation.com/random_project.json``，返回一个
   **裸作品对象**（不是 ``{"data": [...]}``）：``id``、``hash_id``、``title``、``permalink``、
   ``assets``、``tags``、``software_items``、``user``、``cover``。实测样本里 ``tags`` 是空
   数组，不能据此断定标签一定是对象；``assets`` 项的 ``original_url`` 是 ``null``，所以脚本
   只打印 ``image_url``/``small_image_url`` 与宽高，不拿 ``original_url`` 当必有地址。
4. ``project_comments(22897630)`` →
   ``GET https://www.artstation.com/api/v2/community/projects/22897630/comments.json``，返回
   ``{"total_count": 0, "data": []}``。实测样本这条作品没有评论，所以**非空评论的形状未实测**，
   脚本只报总数与条数，不猜评论字段。

教学写法（字面参数，自足）：

    from anybooru import ArtStation

    with ArtStation('artstation') as client:
        user = client.user_show('timwarnock')
        print(user['id'], user['username'], user['projects_count'])
        album = client.album_projects(104104, page=1, per_page=4)
        print(album['total_count'], [item['hash_id'] for item in album['data']])
        project = client.project_random()
        print(project['id'], project['hash_id'], project['title'])
        comments = client.project_comments(22897630)
        print(comments['total_count'], len(comments['data']))

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL 与关键字段。
图片地址只当字符串打印，不下载媒体；四个路由都是公开只读 GET，不需要任何账号或凭据。
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


def album_summary(item):
    """专辑条目摘要：媒体地址只当字符串打印，assets 只报条数。"""
    return {'id': item['id'], 'hash_id': item['hash_id'],
            'title': item['title'], 'album_id': item['album_id'],
            'album_title': item['album_title'], 'position': item['position'],
            'permalink': item['permalink'], 'assets': len(item['assets'])}


def random_summary(project):
    """随机作品摘要：不读 assets 项的 original_url（实测样本为 null）。"""
    assets = project['assets']
    first = assets[0] if assets else None
    return {'id': project['id'], 'hash_id': project['hash_id'],
            'title': project['title'], 'permalink': project['permalink'],
            'tags': project['tags'], 'assets': len(assets),
            'user': project['user']['username'],
            'cover_id': project['cover']['id'],
            'first_asset': ({'id': first['id'],
                             'asset_type': first['asset_type'],
                             'width': first['width'], 'height': first['height'],
                             'image_url': first['image_url'],
                             'small_image_url': first['small_image_url']}
                            if first else None)}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 ArtStation 的用户、专辑、随机作品与评论')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.artstation.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['artstation']
    site = example['site'] if args.site is None else args.site
    album_query = example['album_query']

    with ArtStation(site, config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        # 每次请求前都暂停，第一次也不例外。
        time.sleep(example['pause_seconds'])
        user = client.user_show(example['username'])
        albums = user['albums_with_community_projects']
        emit(client, 'user_show', username=user['username'], user_id=user['id'],
             full_name=user['full_name'], headline=user['headline'],
             permalink=user['permalink'], projects_count=user['projects_count'],
             followers_count=user['followers_count'], key_count=len(user),
             album_count=len(albums),
             first_album=(albums[0]['title'] if albums else None))

        time.sleep(example['pause_seconds'])
        album = client.album_projects(example['album_id'], **album_query)
        emit(client, 'album_projects', album_id=example['album_id'],
             page=album_query['page'], per_page=album_query['per_page'],
             total_count=album['total_count'], count=len(album['data']),
             ids=[item['id'] for item in album['data']],
             projects=[album_summary(item) for item in album['data']])

        time.sleep(example['pause_seconds'])
        project = client.project_random()
        emit(client, 'project_random', **random_summary(project))

        time.sleep(example['pause_seconds'])
        comments = client.project_comments(example['project_id'])
        emit(client, 'project_comments', project_id=example['project_id'],
             total_count=comments['total_count'], count=len(comments['data']))


if __name__ == '__main__':
    main()
