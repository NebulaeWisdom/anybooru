# -*- coding: utf-8 -*-
"""列出并取回 e621 系站点的标签、画师、评论、合集与笔记。

每类资源先列一页，再用列表里第一项的 id 取详情；列表为空时只报零，不取详情、
也不编造 ID。查询、数量、调用间隔与站点名全部来自配置文件 examples.e621 段
（默认读包内 anybooru.json），可以用 --config / --site 覆盖。
"""

import argparse
import json
import time

from anybooru import E621
from anybooru.resources import load_config


def tag_summary(tag):
    return {'id': tag['id'], 'name': tag['name'], 'category': tag['category'],
            'post_count': tag['post_count']}


def artist_summary(artist):
    return {'id': artist['id'], 'name': artist['name'],
            'group_name': artist['group_name'], 'is_active': artist['is_active'],
            'urls': [url['url'] for url in artist['urls']]}


def comment_summary(comment):
    """评论正文只报长度，不打印内容。"""
    return {'id': comment['id'], 'post_id': comment['post_id'],
            'creator_name': comment['creator_name'], 'score': comment['score'],
            'body_chars': len(comment['body'])}


def pool_summary(pool):
    return {'id': pool['id'], 'name': pool['name'], 'category': pool['category'],
            'is_active': pool['is_active'], 'post_count': pool['post_count']}


def note_summary(note):
    """笔记正文只报长度，不打印内容。"""
    return {'id': note['id'], 'post_id': note['post_id'], 'x': note['x'],
            'y': note['y'], 'width': note['width'], 'height': note['height'],
            'is_active': note['is_active'], 'body_chars': len(note['body'])}


def emit(client, method, **summary):
    line = {'method': method, 'status_code': client.last_call['status_code'],
            'url': client.last_call['url']}
    line.update(summary)
    print(json.dumps(line, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='浏览 e621 系站点的匿名资源')
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

        tags = client.tag_list(**example['tag_query'])
        emit(client, 'tag_list', count=len(tags),
             tags=[tag_summary(tag) for tag in tags])
        if tags:
            pause()
            tag = client.tag_show(tags[0]['id'])
            emit(client, 'tag_show', tag=tag_summary(tag))

        pause()
        artists = client.artist_list(**example['artist_query'])
        emit(client, 'artist_list', count=len(artists),
             artists=[artist_summary(artist) for artist in artists])
        if artists:
            pause()
            artist = client.artist_show(artists[0]['id'])
            emit(client, 'artist_show', artist=artist_summary(artist))

        pause()
        comments = client.comment_list(**example['comment_query'])
        emit(client, 'comment_list', count=len(comments),
             comments=[comment_summary(comment) for comment in comments])
        if comments:
            pause()
            comment = client.comment_show(comments[0]['id'])
            emit(client, 'comment_show', comment=comment_summary(comment))

        pause()
        pools = client.pool_list(**example['pool_query'])
        emit(client, 'pool_list', count=len(pools),
             pools=[pool_summary(pool) for pool in pools])
        if pools:
            pause()
            pool = client.pool_show(pools[0]['id'])
            emit(client, 'pool_show', pool=pool_summary(pool))

        pause()
        notes = client.note_list(**example['note_query'])
        emit(client, 'note_list', count=len(notes),
             notes=[note_summary(note) for note in notes])
        if notes:
            pause()
            note = client.note_show(notes[0]['id'])
            emit(client, 'note_show', note=note_summary(note))


if __name__ == '__main__':
    main()
