# -*- coding: utf-8 -*-
"""相关标签查询（GET /related_tag.json，匿名只读）。

搜索条件放在 search 字典里（编码成 search[...]），limit 等顶层参数走 **params。
examples.danbooru 的值：related_query='touhou'、related_category=0、related_order='frequency'、
search_sample_size=1000、tag_sample_size=100、limit=3，等价字面调用：
Danbooru('danbooru').related_tag(search={'query': 'touhou', 'category': 0,
    'order': 'frequency', 'search_sample_size': 1000, 'tag_sample_size': 100}, limit=3)

返回一个对象（不是数组）：query、post_count、tag、related_tags、wiki_page_tags；
相关标签在 related_tags 里，每项含 tag（标签对象，含 name 与 post_count）。
"""

import argparse

from anybooru import Danbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='查询相关标签')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

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
