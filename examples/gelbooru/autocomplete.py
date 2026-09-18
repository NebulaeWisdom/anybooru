# -*- coding: utf-8 -*-
"""查询 Gelbooru 的标签自动补全，打印条数、完整建议与本次请求的真实地址。

examples.gelbooru 给脚本提供站点与查询参数，这次调用等价于
client.autocomplete('blue', type='tag', limit=3)：term 是用户已经输入的前缀
（多词标签用下划线，如 'hatsune_miku'），type 选择补全种类（tag 是标签），
limit 是请求数量而非本地截断：本次 limit=3 实际返回10条。此路径无需账号。
--config / --site 可以换配置文件或站点。
"""

import argparse
import json

from anybooru import Gelbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='查询 Gelbooru 的自动补全建议')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.gelbooru.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['gelbooru']
    site = example['site'] if args.site is None else args.site

    with Gelbooru(site, config_file=args.config) as client:
        suggestions = client.autocomplete(**example['autocomplete_query'])
        print(json.dumps({
            'method': 'autocomplete',
            'status_code': client.last_call['status_code'],
            'url': client.last_call['url'],
            'count': len(suggestions),
            'suggestions': suggestions,
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()
