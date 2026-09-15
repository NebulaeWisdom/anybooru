# -*- coding: utf-8 -*-
"""列出 Moebooru 系站点的 wiki 页面。

query 是顶层标题搜索参数，不使用 Danbooru 的 search 字典。
"""

import argparse

from pybooru import Moebooru
from pybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 系站点的 wiki 页面')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        for page in client.wiki_list(query=example['wiki_query'],
                                     limit=example['limit']):
            print(page['title'])


if __name__ == '__main__':
    main()
