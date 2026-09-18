# -*- coding: utf-8 -*-
"""搜索 Moebooru 系站点的 wiki 页面标题。

调用 wiki_list(query='touhou', limit=3)，对应 GET /wiki.json?query=touhou&limit=3，打印命中页面的 title。
Moebooru 没有 wiki_show：要看正文或全部版本，用 wiki_list(query='title:<标题>') 或 wiki_history(title=…)。
"""

import argparse

from anybooru import Moebooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 系站点的 wiki 页面')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
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
