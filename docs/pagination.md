# 分页

## 客户端行为

本库不做任何本地分页：

* `page` / `limit` 原样传给服务端，不设本地上限、不裁剪、不补默认值；
* 不自动翻页，也不隐式抓取下一页（没有生成器、没有内部循环）；
* 请求失败不自动重试，包括被限流的情况；
* 返回的就是服务端给的那一页数据，原样是 JSON 数组。

也就是说，分页策略完全由调用者决定，客户端只负责把参数发对。

```python
from pybooru import Danbooru

client = Danbooru('danbooru')
example = client.config['examples']['danbooru']

# 第 1 页，每页 limit 条
page_1 = client.post_list(tags=example['tags'], page=example['pages'][0], limit=example['limit'])
page_2 = client.post_list(tags=example['tags'], page=example['pages'][1], limit=example['limit'])

# limit 不传时用站点默认值
client.post_list(tags=example['tags'])
```

## Danbooru 系站点的分页语义

Danbooru 的 `page` 与 `limit` 都是**顶层参数**（不是 `search[...]` 的成员），语义来自上游
`app/logical/pagination_extension.rb`：

| 形式 | 含义 |
| :--- | :--- |
| `page=1`、`page=2` | 编号分页：第 N 页 |
| `page=a1000` | 按 ID 顺序分页：ID 大于 1000 的记录 |
| `page=b1000` | 按 ID 倒序分页：ID 小于 1000 的记录 |

页码超过账号上限时，Danbooru 返回 `410 Gone`。普通非数字 `page` 并不一定报错：上游会按 `to_i` 转换并归一到第一页；不要把任意非法文本当作稳定的错误触发方式。

`limit` 是每页数量，上限由站点与账号等级共同决定：

| 范围 | 值 | 来源 |
| :--- | :--- | :--- |
| 默认每页 | `20` | `Danbooru.config.posts_per_page` |
| 通用上限 | `1000` | 通用分页入口 |
| 帖子列表 | `200` | `PostSets::Post::MAX_PER_PAGE` |
| uploads / upload_media_assets / media_assets / ai_tags | `200` | 各控制器自行 clamp |
| 页码上限 | 匿名与普通用户 `1000`，Gold 及以上 `5000` | `User#page_limit` |

本库不预判这些上限，超限时由服务端裁剪或报错。帖子列表还支持标签里的 `limit:` 元标签
（如 `tags='rating:g limit:50'`），与顶层 `limit` 作用相同。

游标分页推荐配合按 ID 排序的搜索使用，逐页向外走：

```python
posts = client.post_list(tags=example['tags'], limit=example['limit'])
last_id = posts[-1]['id']
next_page = client.post_list(tags=example['tags'], page='b{0}'.format(last_id), limit=example['limit'])
```

上述 `b` 游标从当前页最小 ID 向旧记录翻页。`a` 游标查询更大 ID；返回数组仍按 ID 降序排列，继续向新记录翻页时取当前页的 `posts[0]['id']`，不要取末项导致重复。

## Moebooru 系站点的分页

Moebooru 面同样不做本地分页：`page` 就是页码（服务端把它夹在 `1..1000000`），每页数量由端点自己决定，
而且各端点并不一致：

| 端点 | 每页 / 上限 |
| :--- | :--- |
| `post_list` | `limit` 默认 40，超过 1000 一律夹到 1000；`tags` 里的 `limit:` 元标签可以覆盖 |
| `pool_list` | 20；`query` 里的 `limit:N` 被夹到 ≤100 |
| `pool_show` | `page × 24`（账号开启合集浏览模式时 ×1000） |
| `note_list` | 100（带 `post_id`）/ 16 |
| `note_history` | 25（按 `post_id`、`user_id` 时 50），**`limit` 被忽略** |
| `comment_list` | 25，**`limit` 被忽略** |
| `comment_search` / `forum_search` | 30 |
| `forum_list` | 100（带 `parent_id`）/ 30；`latest` 固定第一页 10 条 |
| `wiki_list` | `limit` 生效，默认 25；`wiki_recent_changes` 用 `per_page`，默认 25 |
| `artist_list` | 50（带 `name` / `url`）/ 25，**`limit` 被忽略** |
| `tag_list` | 默认 50；`limit=0` 返回全部 |

逐条来源见 [moebooru-api.md 的分页与上限表](moebooru-api.md#分页与实际上限)。Moebooru **没有** Danbooru
那样的 `page=a1000` / `b1000` 游标形式，`page` 只接受编号。

```python
from pybooru import Moebooru

with Moebooru('yandere', config_file='pybooru.json') as client:
    example = client.config['examples']['moebooru']

    for page in example['pages']:
        posts = client.post_list(tags=example['tags'], page=page, limit=example['limit'])
        print('page:', page, 'posts:', len(posts))
```

## 相关文档

* [danbooru-api.md](danbooru-api.md)：各端点的参数清单
* [errors.md](errors.md)：限流、参数错误等失败情形
