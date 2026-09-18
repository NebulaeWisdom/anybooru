# -*- coding: utf-8 -*-
"""按使用次数列出 Moebooru 系站点的标签名与计数。

调用 tag_list(limit=3, order='count')，对应 GET /tag.json?limit=3&order=count；
打印每个标签的 name 与 count。过滤与排序都是顶层参数——Moebooru 没有 Danbooru 那种 search[...] 字典。
"""

import argparse

from anybooru import Moebooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 系站点的标签')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        for tag in client.tag_list(limit=example['limit'],
                                   order=example['tag_order']):
            print(tag['name'], tag['count'])


if __name__ == '__main__':
    main()
