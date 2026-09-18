# -*- coding: utf-8 -*-
"""列出标签（GET /tags.json，匿名只读）。

搜索条件放在 search 字典里（编码成 search[...]），limit 是顶层参数。
examples.danbooru.tag_search = {'order': 'count'}、limit = 3，等价字面调用：
Danbooru('danbooru').tag_list(search={'order': 'count'}, limit=3)
请求 URL：https://danbooru.donmai.us/tags.json?search%5Border%5D=count&limit=3
返回 tag 数组，这里打印 name 与 post_count；每项另有 id / category / is_deprecated。
"""

import argparse

from anybooru import Danbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Danbooru 系站点的标签')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        tags = client.tag_list(search=example['tag_search'], limit=example['limit'])
        for tag in tags:
            print(tag['name'], tag['post_count'])


if __name__ == '__main__':
    main()
