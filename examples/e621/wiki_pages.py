# -*- coding: utf-8 -*-
"""列出 e621 系站点的 wiki 页面，再取配置里那个标题的页面。

查询、数量、调用间隔、标题与站点名全部来自配置文件 examples.e621 段（默认读包内
pybooru.json），可以用 --config / --site 覆盖。标题里的冒号会被 URL 转义，
所以 "help:api" 这类标题可以直接传。
"""

import argparse
import json
import time

from pybooru import E621
from pybooru.resources import load_config


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
                        help='配置文件路径（默认包内 pybooru.json）')
    parser.add_argument('--site', default=None, help='站点名，默认取 examples.e621.site')
    args = parser.parse_args()

    configured = load_config(args.config)['examples']['e621']
    site = configured['site'] if args.site is None else args.site

    with E621(site, config_file=args.config) as client:
        example = client.config['examples']['e621']

        pages = client.wiki_page_list(**example['wiki_query'])
        emit(client, 'wiki_page_list', count=len(pages),
             pages=[page_summary(page) for page in pages])

        time.sleep(example['pause_seconds'])
        page = client.wiki_page_show(example['wiki_title'])
        emit(client, 'wiki_page_show', page=page_summary(page))


if __name__ == '__main__':
    main()
