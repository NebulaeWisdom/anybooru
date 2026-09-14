# -*- coding: utf-8 -*-
"""取一页 wiki 页面（GET /wiki_pages/<id 或标题>.json）。

标题里的特殊字符会被 URL 转义，所以可以直接传 "help:api" 这种标题。
"""

import argparse
import json

from pybooru import Danbooru


def main():
    parser = argparse.ArgumentParser(description='读取一个 wiki 页面')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        page = client.wiki_page_show(example['wiki_title'])
        print(page['title'])
        print(page['body'][:example['preview_chars']])


if __name__ == '__main__':
    main()
