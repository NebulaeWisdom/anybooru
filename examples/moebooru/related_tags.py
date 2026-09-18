# -*- coding: utf-8 -*-
"""查询 Moebooru 系站点的相关标签（与给定标签共现的标签）。

调用 tag_related(tags='touhou', type='general')，对应 GET /tag/related.json?tags=touhou&type=general；
返回值是对象 {"touhou": [["标签名", 共现次数], …]}（每组最多 25 项、没有 limit），
脚本保留这个分组结构并按查询标签逐组打印前若干项。
"""

import argparse

from anybooru import Moebooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='查询 Moebooru 相关标签')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        related = client.tag_related(tags=example['related_tags'],
                                     type=example['related_type'])
        for tag, matches in related.items():
            print('tag:', tag)
            for name, count in matches[:example['limit']]:
                print(name, count)


if __name__ == '__main__':
    main()
