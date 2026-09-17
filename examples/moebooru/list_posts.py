# -*- coding: utf-8 -*-
"""列出 Moebooru 系站点的帖子。

搜索与分页参数按顶层参数发送；页码和样本数量从配置读取。
"""

import argparse

from anybooru import Moebooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 系站点的帖子')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        for page in example['pages']:
            posts = client.post_list(tags=example['tags'], page=page,
                                     limit=example['limit'])
            print('page:', page)
            for post in posts:
                print(post['id'], post['file_url'])


if __name__ == '__main__':
    main()
