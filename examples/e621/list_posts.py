# -*- coding: utf-8 -*-
"""列出 e621 系站点的帖子，再取其中一帖的详情与一帖随机帖。

标签、数量、调用间隔与站点名全部来自配置文件 examples.e621 段（默认读包内
anybooru.json），可以用 --config / --site 覆盖，不使用环境变量。
每次调用打印一行 JSON：方法名、状态码、真实 URL 与返回摘要。
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

        posts = client.post_list(**example['post_query'])
        emit(client, 'post_list', count=len(posts),
             posts=[summarize(post) for post in posts])

        if posts:
            pause()
            post = client.post_show(posts[0]['id'])
            emit(client, 'post_show', post=summarize(post))
        else:
            print(json.dumps({'method': 'post_show',
                              'skipped': 'post_list returned no posts'}))

        pause()
        random_post = client.post_random(**example['random_query'])
        emit(client, 'post_random', post=summarize(random_post))


if __name__ == '__main__':
    main()
