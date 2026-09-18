# -*- coding: utf-8 -*-
"""按标签分页列出 Moebooru 系站点的帖子编号与原图地址。

走匿名只读的 GET /post.json：配置 examples.moebooru 提供站点、标签（示例 rating:s）、页码与每页条数，
对应的字面调用是 post_list(tags='rating:s', page=1, limit=3)。不登录、不发写请求。
打印每页的页码，以及该页每个帖子的 id 与 file_url。
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
