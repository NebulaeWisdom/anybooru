# -*- coding: utf-8 -*-
"""列出标签。

搜索条件放在 search 字典里（会编码成 search[...]），limit 是顶层参数。
"""

import argparse

from pybooru import Danbooru
from pybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Danbooru 系站点的标签')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        tags = client.tag_list(search=example['tag_search'], limit=example['limit'])
        for tag in tags:
            print(tag['name'], tag['post_count'])


if __name__ == '__main__':
    main()
