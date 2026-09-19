# -*- coding: utf-8 -*-
"""搜索 Sakuria 插画并按 page+1 翻页，默认最多两次匿名 GET。

配置默认对应 ``illust_search(q='blue', size=2, sort='new', page=1)``，
请求 ``https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=1``，
随后请求 page=2。返回完整的 items/page/pageSize/total/totalPages/hasMore/nextPage 对象。
脚本分开打印 pageSize 与实际条数；按 id 去重，不按数值 nextPage 跳页。
遇到 hasMore=false 或 nextPage=null 提前结束；末页分支是否实际执行见验证记录。

所有输入取自 examples.sakuria，支持 --config / --site。输出每次真实 URL、HTTP 状态、
Content-Type、分页字段与作品摘要；最后给出去重编号和重复条数。
access_token 显式空串；按 pause_seconds 暂停，不重试、不跟随跳转、不下载媒体。
"""

import argparse
from functools import partial
import json
import time

from anybooru import Sakuria
from anybooru.resources import load_config


def item_summary(item):
    """插画摘要：只报名号级字段，不打印媒体地址。"""
    return {'id': item['id'], 'title': item['title'], 'type': item['type'],
            'pages': item['pages'], 'tag_count': len(item['tags']),
            'is_ai': item['isAi'], 'is_r18': item['isR18']}


def has_more(envelope):
    """末尾判定只看 hasMore / nextPage=null；数值 nextPage 不参与翻页。"""
    if not envelope['hasMore']:
        return False
    return not ('nextPage' in envelope and envelope['nextPage'] is None)


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'content_type': client.last_call['headers'].get('Content-Type'),
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='搜索 Sakuria 插画并按 page+1 翻页')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None,
                        help='站点名，默认取 examples.sakuria.site')
    args = parser.parse_args()

    example = load_config(args.config)['examples']['sakuria']
    site = example['site'] if args.site is None else args.site

    with Sakuria(site, config_file=args.config, access_token='') as client:
        client.client.request = partial(client.client.request, allow_redirects=False)

        def pause():
            time.sleep(example['pause_seconds'])

        requested_pages = []
        unique_ids = []
        seen = set()
        fetched = 0
        page = example['pages'][0]
        for step in range(len(example['pages'])):
            if step:
                page += 1
                pause()
            envelope = client.illust_search(**example['illust_query'], page=page)
            requested_pages.append(page)

            ids = [item['id'] for item in envelope['items']]
            fetched += len(ids)
            remembered = len(unique_ids)
            for illust_id in ids:
                if illust_id not in seen:
                    seen.add(illust_id)
                    unique_ids.append(illust_id)
            emit(client, 'illust_search', requested_page=page,
                 page=envelope['page'], page_size=envelope['pageSize'],
                 total=envelope['total'], total_pages=envelope['totalPages'],
                 has_more=envelope['hasMore'], next_page=envelope['nextPage'],
                 hidden_count=envelope.get('hiddenCount'),
                 count=len(envelope['items']), ids=ids,
                 new_ids=unique_ids[remembered:],
                 items=[item_summary(item) for item in envelope['items']])

            if not has_more(envelope):
                break

        print(json.dumps({'method': 'illust_search summary',
                          'requested_pages': requested_pages,
                          'unique_ids': unique_ids,
                          'duplicate_count': fetched - len(unique_ids)},
                         ensure_ascii=False))


if __name__ == '__main__':
    main()
