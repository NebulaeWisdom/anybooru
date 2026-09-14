# -*- coding: utf-8 -*-
"""列出 Moebooru 系站点的 wiki 页面。

Moebooru 面未重写，只迁移了共享配置用法；未做线上验证。
"""

import argparse
import json

from pybooru import Moebooru


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 系站点的 wiki 页面')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        for page in client.wiki_list(limit=example['limit']):
            print(page['title'])


if __name__ == '__main__':
    main()
