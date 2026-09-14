# -*- coding: utf-8 -*-
"""读取官方匿名随机图片的原始字节，不把二进制当作 JSON。"""

import argparse
import json

from pybooru import Serika


def main():
    parser = argparse.ArgumentParser(description='读取 Serika 匿名随机图片字节')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='留空则取 examples.serika.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['serika']['site']

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
