# -*- coding: utf-8 -*-
"""浏览 Shuushuu 的标签、评论、用户与新闻四个匿名只读入口。

依次调用（都是匿名 GET，固定 4 次）：

1. ``tag_show(46)`` → ``GET /api/v1/tags/46``，返回 ``TagWithStats``：标签名 ``title``、
   使用次数 ``usage_count``、图片总数 ``total_image_count``、别名 ``aliases``、外部链接
   ``links``、关联来源 ``sources`` 与角色 ``characters``。
2. ``comment_list(image_id=1118862, per_page=2)`` → ``GET /api/v1/comments``，返回
   ``{"total", "page", "per_page", "comments": [...]}``，每条含 ``post_id``、``image_id``、
   ``user``、``date`` 与正文 ``post_text``（本脚本只报正文长度）。
3. ``user_list(search='whitekitten', per_page=2)`` → ``GET /api/v1/users``，返回
   ``{"total", "page", "per_page", "users": [...]}``，每条含 ``user_id``、``username``、
   ``image_posts``、``favorites``、``active`` 等。
4. ``news_list(per_page=1)`` → ``GET /api/v1/news``，返回 ``{"total", "page", "per_page",
   "news": [...]}``，每条含 ``news_id``、``title``、``username``、``date``。

每行打印一个 JSON 对象：方法名、HTTP 状态码、真实 URL 与本次拿到的字段；正文类字段
只报长度，不打印内容。编号、数量与调用间隔取自配置文件的 ``examples.shuushuu`` 段
（默认读包内 ``anybooru.json``）；``--config`` 换配置、``--site`` 换站点，不传时用
``examples.shuushuu.site``。用户名、密码、access_token 显式留空。
"""

import argparse
import json
import time

from anybooru import Shuushuu
from anybooru.resources import load_config


def comment_summary(comment):
    """评论正文只报长度，不打印内容。"""
    return {'post_id': comment['post_id'], 'image_id': comment['image_id'],
            'username': comment['user']['username'], 'date': comment['date'],
            'post_chars': len(comment['post_text'])}


def user_summary(user):
    return {'user_id': user['user_id'], 'username': user['username'],
            'image_posts': user['image_posts'], 'favorites': user['favorites'],
            'active': user['active']}


def news_summary(item):
    """新闻正文只报长度，不打印内容。"""
    return {'news_id': item['news_id'], 'title': item['title'],
            'username': item['username'], 'date': item['date'],
            'text_chars': None if item['news_text'] is None
                          else len(item['news_text'])}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 Shuushuu 的匿名资源入口')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.shuushuu.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['shuushuu']
    site = example['site'] if args.site is None else args.site

    with Shuushuu(site, config_file=args.config, username='', password='',
                  access_token='') as client:
        def pause():
            time.sleep(example['pause_seconds'])

        tag = client.tag_show(example['tag_id'])
        emit(client, 'tag_show', tag_id=tag['tag_id'], title=tag['title'],
             type=tag['type'], usage_count=tag['usage_count'],
             total_image_count=tag['total_image_count'],
             aliases=len(tag['aliases']), links=len(tag['links']),
             sources=len(tag['sources']), characters=len(tag['characters']))

        pause()
        comments = client.comment_list(**example['comment_query'])
        emit(client, 'comment_list', total=comments['total'],
             page=comments['page'], per_page=comments['per_page'],
             count=len(comments['comments']),
             first=comment_summary(comments['comments'][0])
                   if comments['comments'] else None)

        pause()
        users = client.user_list(**example['user_query'])
        emit(client, 'user_list', total=users['total'], page=users['page'],
             per_page=users['per_page'], count=len(users['users']),
             first=user_summary(users['users'][0]) if users['users'] else None)

        pause()
        news = client.news_list(**example['news_query'])
        emit(client, 'news_list', total=news['total'], page=news['page'],
             per_page=news['per_page'], count=len(news['news']),
             first=news_summary(news['news'][0]) if news['news'] else None)


if __name__ == '__main__':
    main()
