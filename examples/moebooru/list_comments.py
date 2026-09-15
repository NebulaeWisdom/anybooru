# -*- coding: utf-8 -*-
"""匿名读取 Moebooru 的最新评论；不发送写请求。"""

import argparse

from pybooru import Moebooru
from pybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 评论')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        comments = client.comment_search(example['comment_query'])
        print('comments:', len(comments))
        for comment in comments[:example['limit']]:
            print(comment['id'], comment['post_id'],
                  comment['body'][:example['preview_chars']])


if __name__ == '__main__':
    main()
