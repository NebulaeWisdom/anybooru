# -*- coding: utf-8 -*-
"""先列一页帖子，再用列表里的 id 取详情。

不直接使用 examples 段里的 post_id，避免依赖一个可能不存在的固定 ID。
"""

import argparse

from anybooru import Danbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='取一个帖子的详情')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        posts = client.post_list(tags=example['tags'], limit=example['limit'])

        post = client.post_show(posts[0]['id'])
        print(post['id'], post['rating'], post['tag_string'])


if __name__ == '__main__':
    main()
