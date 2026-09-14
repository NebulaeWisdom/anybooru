# -*- coding: utf-8 -*-
"""发表一条评论（需要登录，会真的写入）。

Moebooru 的登录信息随请求体发送：login + password_hash，
password_hash = SHA1(hash_string.format(password))，三者的来源是根配置文件的站点条目。
未做线上验证。
"""

import argparse
import json

from pybooru import Moebooru


def main():
    parser = argparse.ArgumentParser(description='发表一条 Moebooru 评论')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        client.comment_create(post_id=example['post_id'],
                              comment_body=example['comment_body'])
        print(client.last_call['url'])


if __name__ == '__main__':
    main()
