# -*- coding: utf-8 -*-
"""浏览 TBIB（Gelbooru 0.2）的标签与评论两个 XML 只读入口。

依次调用（都是匿名 GET，固定 2 次）：

1. ``tag_list(limit=2)`` → ``GET https://tbib.org/index.php?limit=2&s=tag&q=index&page=dapi``，
   返回 XML 文本：根 ``<tags type="array">``，子 ``<tag>`` 带 ``id``、``name``、``count``、
   ``type``、``ambiguous`` 五个属性，全部是字符串；``json=1`` 不会把这个端点变成 JSON。
2. ``comment_list(1)`` → ``GET https://tbib.org/index.php?post_id=1&s=comment&q=index&page=dapi``，
   返回 XML 文本：根 ``<comments type="array">``。站点 help 把 ``post_id`` 描述成“评论编号”，
   与“帖子编号”的说法有冲突，脚本只报子元素个数、标签名与属性名，不臆测评论字段。

每行打印一个 JSON 对象：方法名、HTTP 状态码、``Content-Type``、真实 URL 与解析出的摘要
（标签属性、评论子元素），不下载媒体、不打印大段正文。参数与站点名取自配置文件的
``examples.gelbooru02`` 段（默认读包内 ``anybooru.json``）；``--config`` 换配置、
``--site`` 换站点，不传时取 ``examples.gelbooru02.site``。脚本不带任何凭据。
"""

import argparse
from functools import partial
import json
import time
from xml.etree import ElementTree

from anybooru import Gelbooru02
from anybooru.resources import load_config


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 TBIB 的标签与评论 XML 入口')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.gelbooru02.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['gelbooru02']
    site = example['site'] if args.site is None else args.site

    with Gelbooru02(site, config_file=args.config) as client:
        client.client.request = partial(client.client.request, allow_redirects=False)
        tags_xml = client.tag_list(limit=example['tag_query']['limit'])
        root = ElementTree.fromstring(tags_xml)
        emit(client, 'tag_list',
             root={'tag': root.tag, 'type': root.get('type')},
             tags=[{'id': tag.get('id'), 'name': tag.get('name'),
                    'count': tag.get('count'), 'type': tag.get('type'),
                    'ambiguous': tag.get('ambiguous')}
                   for tag in root.findall('tag')])

        time.sleep(example['pause_seconds'])
        comments_xml = client.comment_list(example['comment_post_id'])
        comments = ElementTree.fromstring(comments_xml)
        emit(client, 'comment_list',
             root={'tag': comments.tag, 'type': comments.get('type')},
             count=len(list(comments)),
             children=[{'tag': child.tag, 'attributes': sorted(child.attrib)}
                       for child in comments])


if __name__ == '__main__':
    main()
