# -*- coding: utf-8 -*-
"""读取官方匿名随机图片的原始字节，不把二进制当作 JSON。

``client.random_image(...)`` 对应 ``GET /api/v1/random/400/400/image.png``（默认配置下的
``random_size`` 与 ``random_query`` 就是 ``width=400, height=400, fit='cover', format='png',
ratings='safe'``），返回 Python ``bytes``：``Content-Type`` 与 ``X-Image-Id`` / ``X-DBID`` /
``X-Post-Id`` 等响应头都在 ``client.last_call['headers']`` 里，只有真正命中才带 ``X-*`` 标识。
脚本只打印字节数与响应头，不把图片写进磁盘。
"""

import argparse
import json

from anybooru import Serika
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='读取 Serika 匿名随机图片字节')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='留空则取 examples.serika.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['serika']['site']

    with Serika(site, config_file=args.config) as client:
        example = client.config['examples']['serika']
        # 默认配置下 = GET https://serika.art/api/v1/random/400/400/image.png?fit=cover&format=png&ratings=safe
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
