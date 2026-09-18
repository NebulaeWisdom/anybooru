# -*- coding: utf-8 -*-
"""匿名读取 Moebooru 系站点的评论流；不登录、不发写请求。

调用 comment_search('')：空 query 表示不启用全文过滤，对应 GET /comment/search.json?query=，
先打印真实条数，再打印前若干条评论的 id、post_id 与正文开头。打印 0 条是正常结果
（线上常常为空，不是失败）。只读某一帖的评论要用 comment_list(post_id=…)，它必须带 post_id。
"""

import argparse

from anybooru import Moebooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Moebooru 评论')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.moebooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['moebooru']['site']

    with Moebooru(site, config_file=args.config) as client:
        example = client.config['examples']['moebooru']
        comments = client.comment_search(example['comment_query'])
        print('comments:', len(comments))
        for comment in comments[:example['limit']]:
            print(comment['id'], comment['post_id'],
                  comment['body'][:example['preview_chars']])


if __name__ == '__main__':
    main()
