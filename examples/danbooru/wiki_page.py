# -*- coding: utf-8 -*-
"""取一页 wiki 页面（GET /wiki_pages/<id 或标题>.json）。

标题里的特殊字符会被 URL 转义，所以可以直接传 "help:api" 这种标题。
"""

import argparse

from anybooru import Danbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='读取一个 wiki 页面')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        page = client.wiki_page_show(example['wiki_title'])
        print(page['title'])
        print(page['body'][:example['preview_chars']])


if __name__ == '__main__':
    main()
