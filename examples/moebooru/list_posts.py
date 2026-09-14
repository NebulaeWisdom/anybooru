# -*- coding: utf-8 -*-
"""列出 Moebooru 系站点的帖子。

Moebooru 面的方法签名保持旧版不变，参数直接作为顶层参数发送。
其线上可用性尚未验证，详见 docs/moebooru.md。
"""

import argparse
import json

from pybooru import Moebooru


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 系站点的帖子')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        posts = client.post_list(tags=example['tags'], limit=example['limit'])
        for post in posts:
            print(post['id'], post['file_url'])


if __name__ == '__main__':
    main()
