# -*- coding: utf-8 -*-
"""匿名读取 Moebooru 的最新评论；不发送写请求。"""

import argparse
import json

from pybooru import Moebooru


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 评论')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        comments = client.comment_search(example['comment_query'])
        print('comments:', len(comments))
        for comment in comments[:example['limit']]:
            print(comment['id'], comment['post_id'],
                  comment['body'][:example['preview_chars']])


if __name__ == '__main__':
    main()
