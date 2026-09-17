# -*- coding: utf-8 -*-
"""发表一条评论（需要登录，会真的写入）。

写接口按上游源码对齐，未经线上实测。凭据来自配置文件的 sites 段：
username 与 api_key 任一非空，客户端就会带上 HTTP Basic。
"""

import argparse

from anybooru import Danbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='发表一条评论')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        comment = client.comment_create(post_id=example['post_id'],
                                        body=example['comment_body'])
        print(comment['id'], comment['body'])
        print(client.last_call['url'])


if __name__ == '__main__':
    main()
