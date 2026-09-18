# -*- coding: utf-8 -*-
"""对比普通标签查询、两个标签查询，以及只匹配主标签的 strict 查询。

examples.zerochan 给脚本提供标签、数量和间隔，例如 strict 对应
entry_list(tags='Genshin Impact', strict=True, l=2)，打印图片编号和主标签。
客户端把标签放进 URL；User-Agent 请配置项目名与自己的 Zerochan 用户名。
"""

import argparse
import json
import time

from anybooru import Zerochan
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='按标签过滤 Zerochan 条目')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.zerochan.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['zerochan']
    site = example['site'] if args.site is None else args.site
    with Zerochan(site, config_file=args.config) as client:
        for index, name in enumerate(('tag_query', 'multi_tag_query', 'strict_query')):
            if index:
                time.sleep(example['pause_seconds'])
            entries = client.entry_list(**example[name])
            print(json.dumps({
                'method': 'entry_list',
                'query': name,
                'status_code': client.last_call['status_code'],
                'url': client.last_call['url'],
                'count': len(entries),
                'entries': [{'id': entry['id'], 'tag': entry['tag']}
                            for entry in entries],
            }, ensure_ascii=False))


if __name__ == '__main__':
    main()
