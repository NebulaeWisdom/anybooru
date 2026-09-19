# -*- coding: utf-8 -*-
"""浏览 Cosine Gallery 的作品详情、标签作品、画师作品与画师资料（固定 4 次匿名 GET）。

依次调用：

1. ``artwork_show(1)`` → ``GET https://pic.cosine.ren/api/artwork/1``，返回 superjson 外壳
   ``{'json': {...}, 'meta': {...}}``，作品对象在 ``json`` 里。``meta.values`` 对对象结果给出
   需要还原类型的字段名（本轮样本是 ``userid``、``create_time``、``authorid``，值是类型名数组
   ``["bigint"]``/``["Date"]``）；对数组结果（如 ``/api/random``）这些键会带下标前缀，脚本只打印
   键名与个数，不还原 ``json``。``json`` 的字段与 ``/api/list`` 项相同：站内 ``id``、上游 ``pid``、
   投稿人 ``userid``/``username``、画师 ``author``/``authorid``、``platform``、``page``、
   ``filename``/``extension``、``width``/``height``、``rawurl``/``thumburl``、``tags``、
   ``size``/``guest``/``r18``/``ai``。详情**没有** ``originUrl``/``authorUrl``（那两个字段只在
   ``/api/random`` 结果里出现），所以脚本不读它们。本轮样本里 ``id=1`` 的 ``size`` 是
   ``675622``、``guest`` 是 ``true``，说明这两个字段在新入库记录上退化的值不能外推；
   ``tags`` 有 8 项但只有 4 种且都带 ``#``，本站标签既可能带 ``#`` 也可能重复，不同作品之间
   前缀还不一致（``/api/list`` 样本项无 ``#``），做匹配要按作品自己归一化，脚本只报条数与去重数。
2. ``tag_images('GenshinImpact', start=0, limit=2)`` → ``GET https://pic.cosine.ren/api/tag?tag=GenshinImpact&start=0&limit=2``，
   返回**裸数组**（没有 ``total``、没有信封），元素字段与 ``/api/list`` 项相同；``start`` 是偏移、
   标签要写完整名且不带 ``#``。判末尾只能靠返回空数组，脚本因此不追加探测请求，只报本页条数。
3. ``artist_images(platform='pixiv', authorid='54390221', page=1, pageSize=2)`` →
   ``GET https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&page=1&pageSize=2``，
   返回 ``{'images': [...], 'total': N}``（本轮样本 ``total=78``），``images`` 元素字段同上。
4. ``artist_images(platform='pixiv', authorid='54390221', infoOnly=True)`` →
   ``GET https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&infoOnly=true``
   （``True`` 由共享层编码成字面量 ``true``），返回**不是列表信封**的裸资料对象
   ``{'author': 'makoron117', 'authorid': '54390221', 'platform': 'pixiv', 'artworkCount': 78}``。
   资料里的 ``author`` 与本文件第 3 步那页作品的作者名不同（``まころん夏コミC48土お52日``），
   两者来自不同查询，脚本照实并排打印而不要求相等。

教学写法（字面参数，自足）：

    from anybooru import Cosine

    with Cosine('cosine', revalidate_secret='') as client:
        detail = client.artwork_show(1)
        print(detail['json']['id'], detail['json']['platform'], detail['json']['tags'])
        tagged = client.tag_images('GenshinImpact', start=0, limit=2)
        print(len(tagged), tagged[0]['id'])
        artist = client.artist_images(platform='pixiv', authorid='54390221',
                                      page=1, pageSize=2)
        print(artist['total'], [image['id'] for image in artist['images']])
        profile = client.artist_images(platform='pixiv', authorid='54390221',
                                       infoOnly=True)
        print(profile['author'], profile['artworkCount'])

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL，以及该路由的
关键字段（详情的 ``meta.values`` 键名与作品摘要、标签作品与画师作品的条数/总数/编号/摘要、
资料的四个字段）。媒体地址只当字符串打印，标签只报条数，都不下载媒体。参数与站点名取自
配置文件的 ``examples.cosine`` 段（默认读包内 ``anybooru.json``）；``--config`` 换配置、
``--site`` 换站点，不传时取 ``examples.cosine.site``。``revalidate_secret`` 显式传空串保持匿名
（本脚本四个路由都不需要密钥），按 ``pause_seconds`` 串行暂停，不重试、不跟随跳转。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Cosine
from anybooru.resources import load_config


def image_summary(image):
    """作品摘要：媒体地址只当字符串打印，标签只报条数与去重数。"""
    return {'id': image['id'], 'pid': image['pid'],
            'platform': image['platform'], 'page': image['page'],
            'title': image['title'], 'userid': image['userid'],
            'author': image['author'], 'authorid': image['authorid'],
            'width': image['width'], 'height': image['height'],
            'filename': image['filename'], 'extension': image['extension'],
            'size': image['size'], 'guest': image['guest'],
            'r18': image['r18'], 'ai': image['ai'],
            'tag_count': len(image['tags']),
            'distinct_tag_count': len(set(image['tags'])),
            'rawurl': image['rawurl'], 'thumburl': image['thumburl']}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 Cosine Gallery 的作品、标签与画师')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.cosine.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['cosine']
    site = example['site'] if args.site is None else args.site
    artist_query = example['artist_query']

    with Cosine(site, config_file=args.config, revalidate_secret='') as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        def pause():
            """首次请求不等待；其后每次请求前按 pause_seconds 串行暂停。"""
            if client.last_call:
                time.sleep(example['pause_seconds'])

        detail = client.artwork_show(example['artwork_id'])
        artwork = detail['json']
        emit(client, 'artwork_show', artwork_id=example['artwork_id'],
             meta_value_keys=sorted(detail['meta']['values']),
             meta_value_count=len(detail['meta']['values']),
             **image_summary(artwork))

        pause()
        tagged = client.tag_images(example['tag'], **example['tag_query'])
        emit(client, 'tag_images', tag=example['tag'],
             start=example['tag_query']['start'],
             limit=example['tag_query']['limit'], count=len(tagged),
             ids=[image['id'] for image in tagged],
             images=[image_summary(image) for image in tagged])

        pause()
        artist = client.artist_images(platform=artist_query['platform'],
                                      authorid=artist_query['authorid'],
                                      page=artist_query['page'],
                                      pageSize=artist_query['pageSize'])
        emit(client, 'artist_images', platform=artist_query['platform'],
             authorid=artist_query['authorid'], page=artist_query['page'],
             total=artist['total'], count=len(artist['images']),
             ids=[image['id'] for image in artist['images']],
             images=[image_summary(image) for image in artist['images']])

        pause()
        profile = client.artist_images(platform=artist_query['platform'],
                                       authorid=artist_query['authorid'],
                                       infoOnly=True)
        emit(client, 'artist_images infoOnly',
             platform=profile['platform'], authorid=profile['authorid'],
             author=profile['author'], artwork_count=profile['artworkCount'])


if __name__ == '__main__':
    main()
