# -*- coding: utf-8 -*-
"""浏览 Anime-Pictures 的帖子详情、评论、上传者与单条评论（固定 4 次匿名 GET）。

依次调用：

1. ``post_show(382872)`` → ``GET https://api.anime-pictures.net/api/v3/posts/382872``，
   返回含 ``post``、``user``、``tags``、``file_url`` 等键的对象；该帖没有 ``source``，
   不能照搬其它帖子的字段集合。详情里的 ``post`` 比列表对象多 ``small_preview``、
   ``medium_preview``、``big_preview`` 三个预览地址（只是文本，脚本不下载）；``file_url``
   是含空格的**文件名**而不是地址，可作为一个路径段传给 ``image_get``。``tags`` 每项是
   ``{'tag', 'user', 'relation'}``；脚本打印实际顶层键，而不假定每帖都有来源对象。
   ``user`` 含 ``id``、``name``、``login``、``avatar_version``、``isavatar``、``site_score``、
   ``groups``、``gender``、``register_date``，没有头像地址。
2. ``post_comments(382872)`` → ``GET https://api.anime-pictures.net/api/v3/posts/382872/comments``，
   返回 ``{'success': True, 'comments': [{'comment': {...}, 'user': {...}}]}``；``comment``
   含 ``id``、``datetime``、``language``、``text``、``html``，信封里没有 ``offset``/``limit``/
   ``count``，脚本不按分页参数请求。
3. 用第 1 步 ``detail['user']['id']`` 调 ``user_show`` → ``GET https://api.anime-pictures.net/api/v3/users/<id>``，
   返回 ``{'success': True, 'user': {...}, 'errormsg': None}``。
4. 用第 2 步首条评论的 ``comment['id']`` 调 ``comment_show`` →
   ``GET https://api.anime-pictures.net/api/v3/comments/<id>``，返回
   ``{'success': True, 'comment': {...}, 'user': {...}}``。
   评论为空时跳过这一步并打印说明（那时只有 3 次请求）。

教学写法（字面参数，自足）：

    from anybooru import AnimePictures

    with AnimePictures('anime_pictures', authorization='', cookie='') as client:
        detail = client.post_show(382872)
        comments = client.post_comments(382872)
        author = client.user_show(detail['user']['id'])
        if comments['comments']:
            one = client.comment_show(comments['comments'][0]['comment']['id'])
            print(one['comment']['id'], one['comment']['language'])

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL 与字段摘要；
评论只报正文长度，不打印正文。参数与站点名取自配置文件的 ``examples.anime_pictures`` 段
（默认读包内 ``anybooru.json``）；``--config`` 换配置、``--site`` 换站点，不传时取
``examples.anime_pictures.site``。``authorization`` 与 ``cookie`` 显式传空串，按
``pause_seconds`` 串行暂停，不重试、不跟随跳转，也不访问任何媒体地址。
"""

import argparse
from functools import partial
import json
import time

from anybooru import AnimePictures
from anybooru.resources import load_config


def comment_summary(comment, user):
    """评论摘要：报字段与正文长度，不打印正文。"""
    return {'id': comment['id'], 'datetime': comment['datetime'],
            'language': comment['language'], 'chars': len(comment['text']),
            'user_id': user['id'], 'user_name': user['name']}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 Anime-Pictures 的帖子详情、评论与用户')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.anime_pictures.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['anime_pictures']
    site = example['site'] if args.site is None else args.site

    with AnimePictures(site, config_file=args.config,
                       authorization='', cookie='') as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        detail = client.post_show(example['post_id'])
        post = detail['post']
        emit(client, 'post_show', post_id=post['id'], md5=post['md5'],
             width=post['width'], height=post['height'], score=post['score'],
             score_number=post['score_number'], tags_count=post['tags_count'],
             ext=post['ext'], file_url=detail['file_url'],
             small_preview=post['small_preview'],
             medium_preview=post['medium_preview'],
             big_preview=post['big_preview'], detail_keys=list(detail),
             user_id=detail['user']['id'], user_name=detail['user']['name'],
             tag_count=len(detail['tags']))

        time.sleep(example['pause_seconds'])
        comments = client.post_comments(example['post_id'])
        emit(client, 'post_comments', success=comments['success'],
             count=len(comments['comments']),
             first=(comment_summary(comments['comments'][0]['comment'],
                                    comments['comments'][0]['user'])
                    if comments['comments'] else None))

        time.sleep(example['pause_seconds'])
        user = client.user_show(detail['user']['id'])['user']
        emit(client, 'user_show', user_id=user['id'], name=user['name'],
             avatar_version=user['avatar_version'],
             isavatar=user['isavatar'], site_score=user['site_score'],
             groups=user['groups'], gender=user['gender'],
             register_date=user['register_date'])

        if comments['comments']:
            time.sleep(example['pause_seconds'])
            envelope = client.comment_show(comments['comments'][0]['comment']['id'])
            emit(client, 'comment_show',
                 **comment_summary(envelope['comment'], envelope['user']))
        else:
            print(json.dumps({'method': 'comment_show',
                              'skipped': 'post_comments returned no comments'},
                             ensure_ascii=False))


if __name__ == '__main__':
    main()
