# -*- coding: utf-8 -*-
"""浏览 Serika 站内非版本化路由的匿名图片、标签与画师资源。

四次调用都返回原始 JSON（不拆 ``data`` / ``meta``），默认配置下对应：

* ``internal_image_list``  —— ``GET /api/images?page=1&limit=3&ratings=safe&sort=newest``：
  返回 ``{"success": true, "images": [...], "pagination": {...}}``，每项同时给内部 id 与 ``post_id``；
* ``internal_image_show``  —— ``GET /api/images/<post_id>``：路径段是**公开序号**，
  返回 ``{"success": true, "image": {...}}``；
* ``internal_tag_list``    —— ``GET /api/tags?limit=3``：返回按使用计数降序的 ``tags`` 标签表整行；
* ``internal_artist_list`` —— ``GET /api/artists?page=1&limit=3``：返回 ``artists`` 与分页。

不拿列表里的内部 id 去查站内详情，也不用任何凭据。
"""

import argparse
import json

from anybooru import Serika
from anybooru.resources import load_config


def main():
    parser = argparse.ArgumentParser(description='浏览 Serika 站内匿名资源（私有契约）')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default='', help='留空则取 examples.serika.site')
    args = parser.parse_args()

    site = args.site or load_config(args.config)['examples']['serika']['site']

    with Serika(site, config_file=args.config) as client:
        example = client.config['examples']['serika']
        # 默认配置下 = GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest
        listing = client.internal_image_list(**example['image_query'])
        print(json.dumps({'method': 'internal_image_list',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'pagination': listing['pagination'],
                          'images': [{'id': image['id'], 'post_id': image['post_id'],
                                      'rating': image['rating'], 'url': image['url']}
                                     for image in listing['images']]}))
        # 站内详情用 post_id/sequential_id，绝不能传列表里的内部数据库 id。
        # 默认配置下 = GET https://serika.art/api/images/<首图 post_id>
        for image in listing['images'][:1]:
            detail = client.internal_image_show(image['post_id'])['image']
            print(json.dumps({'method': 'internal_image_show',
                              'status': client.last_call['status_code'],
                              'url': client.last_call['url'],
                              'id': detail['id'], 'post_id': detail['post_id'],
                              'rating': detail['rating'], 'image_url': detail['url']}))
        # 默认配置下 = GET https://serika.art/api/tags?limit=3；返回按计数降序的 tags 行
        tags = client.internal_tag_list(**example['tag_query'])['tags']
        print(json.dumps({'method': 'internal_tag_list',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'tags': [{'name': tag['name'], 'count': tag['count']}
                                   for tag in tags]}))
        # 默认配置下 = GET https://serika.art/api/artists?page=1&limit=3；分页没有 has_next
        artists = client.internal_artist_list(**example['artist_query'])['artists']
        print(json.dumps({'method': 'internal_artist_list',
                          'status': client.last_call['status_code'],
                          'url': client.last_call['url'],
                          'artists': [{'tagName': artist['tagName'],
                                       'postCount': artist['postCount']}
                                      for artist in artists]}))


if __name__ == '__main__':
    main()
