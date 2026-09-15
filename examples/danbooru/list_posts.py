# -*- coding: utf-8 -*-
"""列出 Danbooru 系站点的帖子。

站点名、关键词、数量等参数全部来自配置文件的 examples 段（默认读包内 pybooru.json），
可以用 --config / --site 覆盖，不使用环境变量。
"""

import argparse

from pybooru import Danbooru
from pybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Danbooru 系站点的帖子')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        posts = client.post_list(tags=example['tags'], limit=example['limit'])
        for post in posts:
            print(post['id'], post['rating'], post['tag_string'])


if __name__ == '__main__':
    main()
