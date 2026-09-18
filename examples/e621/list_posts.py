# -*- coding: utf-8 -*-
"""列出 e621 系站点的帖子，再取其中一帖的详情与一帖随机帖。

依次调用（都是匿名可读的 GET）：

1. ``post_list(tags='rating:s', limit=2)`` → ``/posts.json?tags=rating%3As&limit=2``，
   从 ``{"posts": [...]}`` 里取出数组，得到两帖；对应配置键 ``post_query``。
2. ``post_show(<第一帖的 id>)`` → ``/posts/<id>.json``，得到单个帖子的字典。
3. ``post_random(tags='rating:s')`` → ``/posts/random.json?tags=rating%3As``，
   上游在查询后加 ``order:random`` 取一条。

每行打印一个 JSON 对象：方法名、HTTP 状态码、真实 URL 与主题摘要。
``summarize()`` 只取帖子编号、评级、``file`` 的 md5/尺寸/字节数、``score.total``
与九类标签的条数，不打印媒体地址、标签正文和描述。

标签、数量、调用间隔与站点名来自配置文件的 ``examples.e621`` 段（默认读包内
``anybooru.json``），可用 ``--config`` / ``--site`` 覆盖，不使用环境变量；
不传 ``--site`` 时取 ``examples.e621.site``（包内为 ``e621``），
传 ``--site e926`` 即换到安全内容镜像站。
"""

import argparse
import json
import time

from anybooru import E621
from anybooru.resources import load_config


def summarize(post):
    """帖子的身份、评级与文件嵌套。

    只打印文件 md5 与尺寸，不打印媒体 URL、标签文本或描述正文。
    """
    return {
        'id': post['id'],
        'rating': post['rating'],
        'file': {'ext': post['file']['ext'], 'size': post['file']['size'],
                 'width': post['file']['width'], 'height': post['file']['height'],
                 'md5': post['file']['md5']},
        'score': post['score']['total'],
        'tags': {category: len(names) for category, names in post['tags'].items()},
    }


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='列出 e621 系站点的帖子')
    parser.add_argument('--config', default=None,
                        help='配置文件路径（默认包内 anybooru.json）')
    parser.add_argument('--site', default=None, help='站点名，默认取 examples.e621.site')
    args = parser.parse_args()

    configured = load_config(args.config)['examples']['e621']
    site = configured['site'] if args.site is None else args.site

    with E621(site, config_file=args.config) as client:
        example = client.config['examples']['e621']

        def pause():
            time.sleep(example['pause_seconds'])

        # GET /posts.json：从 {"posts": [...]} 取数组。
        posts = client.post_list(**example['post_query'])
        emit(client, 'post_list', count=len(posts),
             posts=[summarize(post) for post in posts])

        if posts:
            pause()
            # GET /posts/<id>.json：从 {"post": {...}} 取单帖，字段与列表元素同组。
            post = client.post_show(posts[0]['id'])
            emit(client, 'post_show', post=summarize(post))
        else:
            print(json.dumps({'method': 'post_show',
                              'skipped': 'post_list returned no posts'}))

        pause()
        # GET /posts/random.json：上游在查询后加 order:random 取一条。
        random_post = client.post_random(**example['random_query'])
        emit(client, 'post_random', post=summarize(random_post))


if __name__ == '__main__':
    main()
