# -*- coding: utf-8 -*-
"""列出 Zerochan 条目，再读取配置中指定条目的详情。

站点、查询、条目 ID 与调用间隔来自 examples.zerochan；--config / --site
可显式覆盖。User-Agent 需在配置中补入使用者自己的 Zerochan 用户名。
"""

import argparse
import json
import time

from anybooru import Zerochan
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Zerochan 条目与详情')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.zerochan.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['zerochan']
    site = example['site'] if args.site is None else args.site
    with Zerochan(site, config_file=args.config) as client:
        entries = client.entry_list(**example['entry_query'])
        print(json.dumps({
            'method': 'entry_list',
            'status_code': client.last_call['status_code'],
            'url': client.last_call['url'],
            'count': len(entries),
            'entries': [{'id': entry['id'], 'tag': entry['tag'],
                         'width': entry['width'], 'height': entry['height']}
                        for entry in entries],
        }, ensure_ascii=False))

        time.sleep(example['pause_seconds'])
        entry = client.entry_show(example['entry_id'])
        print(json.dumps({
            'method': 'entry_show',
            'status_code': client.last_call['status_code'],
            'url': client.last_call['url'],
            'entry': {key: entry[key] for key in
                      ('id', 'primary', 'width', 'height', 'size', 'full', 'source')},
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()
