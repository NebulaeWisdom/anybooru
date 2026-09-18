# -*- coding: utf-8 -*-
"""读取官方 v1 的三个匿名入口，不调用需 key 路由。

三次调用各自的返回形态不同，正好当模板抄：

* ``client.api_index()``  —— ``GET /api/v1``：整个自述对象，拿 ``info['name']`` / ``info['version']``；
* ``client.stats()``      —— ``GET /api/v1/stats``：返回 ``data`` 的内容，整个 ``meta``（含 timestamp）
  留在 ``client.last_call['meta']``；
* ``client.user_list()``  —— ``GET /api/v1/users``：返回 ``users`` 数组，分页在
  ``client.last_call['meta']['pagination']``（page / limit / total / pages）。

参数从 ``examples.serika`` 读，默认配置下就是下面注释里那几个字面值。
"""

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
        info = client.api_index()             # GET https://serika.art/api/v1
        print(json.dumps({'method': 'api_index',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'name': info['name'], 'version': info['version']}))
        statistics = client.stats()           # GET https://serika.art/api/v1/stats
        print(json.dumps({'method': 'stats',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'statistics': statistics,
                          'meta': client.last_call['meta']}))
        # 默认配置下 = GET https://serika.art/api/v1/users?page=1&limit=1&sort=newest
        users = client.user_list(**example['user_query'])
        print(json.dumps({'method': 'user_list',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'], 'users': users,
                          'pagination': client.last_call['meta']['pagination']}))


if __name__ == '__main__':
    main()
