# -*- coding: utf-8 -*-
"""浏览 Sakuria 插画、评论与作者，固定三次匿名 GET。

默认先请求 ``illust_show(70937229)``，即
``https://sakuria-api.syarolia.com/illust/70937229``，返回直接含 id/urls/author/tags/stats
的作品对象；然后 ``illust_comments(70937229, page=1, size=2)`` 读取 items/hasMore，
最后用作品里的 author.id 调 user_show，读取用户的 id/name/handle/avatar/stats/social。
每次打印真实 URL、HTTP 状态、Content-Type 与字段摘要，不打印评论正文。

输入取自 examples.sakuria 的 illust_id、comment_query、site 与 pause_seconds，
支持 --config / --site。access_token 显式空串；请求之间暂停，不重试、不跟随跳转，
媒体地址仅作为 JSON 字符串打印，不下载媒体。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Sakuria
from anybooru.resources import load_config


def comment_summary(comment):
    """评论只报字段与正文长度，不打印正文。"""
    return {'id': comment['id'], 'author_id': comment['author']['id'],
            'author_name': comment['author']['name'], 'likes': comment['likes'],
            'replies_count': comment['repliesCount'],
            'chars': len(comment['text']), 'created_at': comment['createdAt'],
            'time_label': comment['timeLabel']}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 Sakuria 的插画详情、评论与作者')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.sakuria.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['sakuria']
    site = example['site'] if args.site is None else args.site

    with Sakuria(site, config_file=args.config, access_token='') as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        def pause():
            time.sleep(example['pause_seconds'])

        detail = client.illust_show(example['illust_id'])
        author = detail['author']
        emit(client, 'illust_show',
             illust_id=detail['id'], title=detail['title'], type=detail['type'],
             pages=detail['pages'], tag_count=len(detail['tags']),
             stats=detail['stats'], is_ai=detail['isAi'], is_r18=detail['isR18'],
             x_restrict=detail['xRestrict'], thumb=detail['urls']['thumb'],
             published_at=detail['publishedAt'], author_id=author['id'],
             author_name=author['name'])

        pause()
        comments = client.illust_comments(example['illust_id'],
                                          **example['comment_query'])
        emit(client, 'illust_comments', count=len(comments['items']),
             has_more=comments['hasMore'],
             first=(comment_summary(comments['items'][0])
                    if comments['items'] else None))

        pause()
        user = client.user_show(author['id'])
        emit(client, 'user_show', user_id=user['id'], name=user['name'],
             handle=user['handle'], accent=user['accent'], avatar=user['avatar'],
             stats=user['stats'], social=user.get('social'))


if __name__ == '__main__':
    main()
