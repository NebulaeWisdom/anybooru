# -*- coding: utf-8 -*-
"""读取官方 v1 的匿名索引、统计和用户目录；不调用需 key 路由。"""

import argparse
import json

from pybooru import Serika


def main():
    parser = argparse.ArgumentParser(description='读取 Serika 官方匿名信息')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='留空则取 examples.serika.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['serika']['site']

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
