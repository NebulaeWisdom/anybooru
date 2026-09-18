# -*- coding: utf-8 -*-
"""列出 e621 系站点的 wiki 页面，再取配置里那个标题的页面。

两次匿名 GET：

1. ``wiki_page_list(limit=2)`` → ``/wiki_pages.json``，得到页面数组，每项含 ``id``、``title``、
   ``category_id``、``is_locked``、``other_names`` 与正文 ``body``。
2. ``wiki_page_show('help:api')`` → ``/wiki_pages/help%3Aapi.json``：标题里的冒号由客户端按路径段
   转义，所以带冒号的标题可以直接传。

每行打印一个 JSON 对象：方法名、HTTP 状态码、真实 URL 与摘要。``page_summary()`` 只取 id、title、
category_id、is_locked 与正文长度，不打印正文内容。

查询、数量、调用间隔、标题与站点名来自配置文件的 ``examples.e621`` 段（默认读包内
``anybooru.json``）：``wiki_query`` 对应列表调用、``wiki_title`` 对应详情调用的标题参数；
可以用 ``--config`` / ``--site`` 覆盖，不传 ``--site`` 时取 ``examples.e621.site``。
"""

import argparse
import json
import time

from anybooru import E621
from anybooru.resources import load_config


def page_summary(page):
    """页面正文只报长度，不打印内容。"""
    return {'id': page['id'], 'title': page['title'],
            'category_id': page['category_id'], 'is_locked': page['is_locked'],
            'body_chars': len(page['body'])}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='读取 e621 系站点的 wiki 页面')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None, help='站点名，默认取 examples.e621.site')
    args = parser.parse_args()

    configured = load_config(args.config)['examples']['e621']
    site = configured['site'] if args.site is None else args.site

    with E621(site, config_file=args.config) as client:
        example = client.config['examples']['e621']

        # GET /wiki_pages.json：页面数组，每项含 id/title/category_id/is_locked/body。
        pages = client.wiki_page_list(**example['wiki_query'])
        emit(client, 'wiki_page_list', count=len(pages),
             pages=[page_summary(page) for page in pages])

        time.sleep(example['pause_seconds'])
        # GET /wiki_pages/help%3Aapi.json：按标题查单个页面，冒号已被转义。
        page = client.wiki_page_show(example['wiki_title'])
        emit(client, 'wiki_page_show', page=page_summary(page))


if __name__ == '__main__':
    main()
