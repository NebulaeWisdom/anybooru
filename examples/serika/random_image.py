# -*- coding: utf-8 -*-
"""读取官方匿名随机图片的原始字节，不把二进制当作 JSON。"""

import argparse
import json

from pybooru import Serika
from pybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='读取 Serika 匿名随机图片字节')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 pybooru.json）')
    parser.add_argument('--site', default='', help='留空则取 examples.serika.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['serika']['site']

    with Serika(site, config_file=args.config) as client:
        example = client.config['examples']['serika']
        image = client.random_image(**example['random_size'],
                                    **example['random_query'])
        print(json.dumps({'method': 'random_image',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'python_type': type(image).__name__,
                          'bytes': len(image),
                          'headers': dict(client.last_call['headers'])}))


if __name__ == '__main__':
    main()
