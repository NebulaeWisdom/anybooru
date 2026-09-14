# -*- coding: utf-8 -*-
"""pixiv 作者 ID → Danbooru 画师 tag。

流程：用根配置里的 URL 模板拼出画师主页地址 → 按 URL 反查 artist → 取 artist['name']
（这个 name 就是作品上使用的 tag）→ 再用它搜作品。

对应路由：GET /artists.json?search[url_matches]=<主页地址>、GET /posts.json?tags=<tag>
"""

import argparse
import json

from pybooru import Danbooru


def main():
    parser = argparse.ArgumentParser(description='pixiv 作者 ID 转 Danbooru tag')
    parser.add_argument('--config', default='pybooru.json',
                        help='根配置文件路径（默认 pybooru.json）')
    parser.add_argument('--site', default='', help='站点名，留空则取 examples.danbooru.site')
    args = parser.parse_args()

    with open(args.config, encoding='utf-8') as config_file:
        site = args.site or json.load(config_file)['examples']['danbooru']['site']

    with Danbooru(site, config_file=args.config) as client:
        example = client.config['examples']['danbooru']

        url = example['pixiv_url_template'].format(pixiv_id=example['pixiv_id'])
        print('画师主页:', url)

        artists = client.artist_list(search={'url_matches': url}, limit=example['limit'])

        for artist in artists:
            print('artist:', artist['id'], artist['name'])

            posts = client.post_list(tags=artist['name'], limit=example['limit'])
            for post in posts:
                print('post:', post['id'], post['rating'], post['tag_string'])


if __name__ == '__main__':
    main()
