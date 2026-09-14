# -*- coding: utf-8 -*-
"""相关标签查询（GET /related_tag.json）。

搜索条件放在 search 字典里（编码成 search[...]），limit 等顶层参数走 **params。
返回一个对象，相关标签在 related_tags 里。
"""

import argparse
import json

from pybooru import Danbooru


def main():
    parser = argparse.ArgumentParser(description='查询相关标签')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        related = client.related_tag(search={
            'query': example['related_query'],
            'category': example['related_category'],
            'order': example['related_order'],
            'search_sample_size': example['search_sample_size'],
            'tag_sample_size': example['tag_sample_size'],
        }, limit=example['limit'])

        print('query:', related['query'], 'posts:', related['post_count'])
        for item in related['related_tags']:
            print(item['tag']['name'])


if __name__ == '__main__':
    main()
