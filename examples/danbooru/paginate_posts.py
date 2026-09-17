# -*- coding: utf-8 -*-
"""分页示例：编号分页与按 ID 的游标分页。

客户端不自动翻页，page / limit 原样传给服务端。
"""

import argparse

from anybooru import Danbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='Danbooru 分页示例')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']

        # 编号分页
        for page in example['pages']:
            posts = client.post_list(tags=example['tags'], page=page,
                                     limit=example['limit'])
            print('page', page, [post['id'] for post in posts])

        # 向较旧帖子翻页：page=b<id> 表示“id 小于该值的记录”
        first = client.post_list(tags=example['tags'], limit=example['limit'])
        following = client.post_list(tags=example['tags'],
                                     page='b{0}'.format(first[-1]['id']),
                                     limit=example['limit'])
        print('before', first[-1]['id'], [post['id'] for post in following])


if __name__ == '__main__':
    main()
