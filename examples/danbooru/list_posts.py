# -*- coding: utf-8 -*-
"""列出 Danbooru 系站点的帖子。

站点名、关键词、数量等参数全部来自根配置文件 pybooru.json 的 examples 段，
可以用 --config / --site 覆盖，不使用环境变量。
"""

import argparse
import json

from pybooru import Danbooru


def main():
    parser = argparse.ArgumentParser(description='列出 Danbooru 系站点的帖子')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        posts = client.post_list(tags=example['tags'], limit=example['limit'])
        for post in posts:
            print(post['id'], post['rating'], post['tag_string'])


if __name__ == '__main__':
    main()
