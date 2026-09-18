# -*- coding: utf-8 -*-
"""列出 Danbooru 系站点的帖子（GET /posts.json，匿名只读）。

站点名、关键词、条数来自配置 examples.danbooru：site='danbooru'、tags='rating:g'、limit=3
（默认读包内 anybooru.json），可以用 --config / --site 覆盖，不使用环境变量。
等价字面调用：Danbooru('danbooru').post_list(tags='rating:g', limit=3)
请求 URL：https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=3
返回数组，每条含 id / rating / tag_string；过滤条件写在顶层 tags 元标签里，不吃 search 字典。
"""

import argparse

from anybooru import Danbooru
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='列出 Danbooru 系站点的帖子')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']
        posts = client.post_list(tags=example['tags'], limit=example['limit'])
        for post in posts:
            print(post['id'], post['rating'], post['tag_string'])


if __name__ == '__main__':
    main()
