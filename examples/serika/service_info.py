# -*- coding: utf-8 -*-
"""读取官方 v1 的匿名索引、统计和用户目录；不调用需 key 路由。"""

import argparse
import json

from anybooru import Serika
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='读取 Serika 官方匿名信息')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='留空则取 examples.serika.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['serika']['site']

    with Serika(site, config_file=args.config) as client:
        example = client.config['examples']['serika']
        info = client.api_index()
        print(json.dumps({'method': 'api_index',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'name': info['name'], 'version': info['version']}))
        statistics = client.stats()
        print(json.dumps({'method': 'stats',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'statistics': statistics,
                          'meta': client.last_call['meta']}))
        users = client.user_list(**example['user_query'])
        print(json.dumps({'method': 'user_list',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'], 'users': users,
                          'pagination': client.last_call['meta']['pagination']}))


if __name__ == '__main__':
    main()
