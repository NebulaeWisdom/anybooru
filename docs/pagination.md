# 分页

## 客户端行为

五个家族的页码参数名不一样：Danbooru、Moebooru、Serika、e621ng 用 `page` / `limit`，
Zerochan 用 `p` / `l`。本库只负责把参数发对：

* 页码与每页数量原样发给服务端，不裁剪、不改写、不补默认值（服务端自己的默认值与上限见下文各节）；
* 不自动翻页：没有生成器，也没有内部循环，一次调用就是一次请求；
* 失败不自动重试，包括被限流的情况；
* 返回服务端给的那一页：有的家族直接返回数组，有的把数组包在 `{"posts": [...]}` 或 `{"items": [...]}` 里，
  见各节。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&page=1&limit=2
    page_1 = client.post_list(tags='rating:g', page=1, limit=2)   # 数组；每项有 id / rating / tag_string / file_url
    for post in page_1:
        print(post['id'], post['rating'], post['file_url'])

    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&page=2&limit=2
    page_2 = client.post_list(tags='rating:g', page=2, limit=2)
    print(len(page_1), len(page_2))

    # 不传 page / limit：交给服务端默认值（帖子列表默认每页 20 条）
    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag；返回图片列表，含 id、rating、file_url。
    default_page = client.post_list(tags='rating:g')
    print(len(default_page))
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

游标分页推荐配合按 ID 排序的搜索使用，逐页向旧记录走：

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    # 12211420 是此前图片列表返回过的编号；b 放在编号前，查询比它更旧的图片。
    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&page=b12211420&limit=2
    older_posts = client.post_list(tags='rating:g', page='b12211420', limit=2)
    print(len(older_posts), older_posts[-1]['id'])
```

`b` 游标取 ID 小于给定值的那一批。想往新记录走就用 `a` 游标（ID 大于给定值）：返回数组同样按 ID 从大到小，
所以要用当前页的 `posts[0]['id']` 继续，用末项会原地打转。

## Moebooru 系站点的分页

Moebooru 面同样不做本地分页：`page` 就是页码（服务端把它夹在 `1..1000000`），每页数量由端点自己决定，
而且各端点并不一致：

| 端点 | 每页 / 上限 |
| :--- | :--- |
| `post_list` | `limit` 默认 40，超过 1000 一律夹到 1000；`tags` 里的 `limit:` 元标签可以覆盖 |
| `pool_list` | 20；`query` 里的 `limit:N` 被夹到 ≤100 |
| `pool_show` | `page × 24`（账号开启合集浏览模式时 ×1000） |
| `note_list` | 先按帖子分页：100（带 `post_id`）/ 16 个帖子，再返回这些帖子的全部笔记；不是笔记条数上限 |
| `note_history` | 25（按 `post_id`、`user_id` 时 50），**`limit` 被忽略** |
| `comment_list` | 25，**`limit` 被忽略** |
| `comment_search` / `forum_search` | 30 |
| `forum_list` | 100（带 `parent_id`）/ 30；`latest` 固定第一页 10 条 |
| `wiki_list` | `limit` 生效，默认 25；`wiki_recent_changes` 用 `per_page`，默认 25 |
| `artist_list` | 50（带 `name` / `url`）/ 25，**`limit` 被忽略** |
| `tag_list` | 默认 50；`limit=0` 返回全部 |

逐条来源见 [Moebooru 契约审计附注](moebooru-contract-notes.md)。Moebooru **没有** Danbooru
那样的 `page=a1000` / `b1000` 游标形式，`page` 只接受编号。

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    for page in (1, 2):
        # GET https://yande.re/post.json?tags=rating%3As&page=1&limit=3
        # 第二次是 GET https://yande.re/post.json?tags=rating%3As&page=2&limit=3
        posts = client.post_list(tags='rating:s', page=page, limit=3)
        # 数组；每项有 id / file_url / tags / score / rating
        print('page:', page, 'posts:', len(posts), 'first id:', posts[0]['id'] if posts else None)
```

## e621ng 系站点的分页

e621ng 用自己的 `Danbooru::Paginator`（与 Danbooru 同名但不是同一份实现），`page` 也有编号与游标两种形式：

| 形式 | 含义 |
| :--- | :--- |
| `page=1`、`page=2` | 编号分页：第 N 页；超过站点上限（`750`，`Danbooru.config.max_numbered_pages`）报错 |
| `page=b1000` | 顺序分页：ID **小于** 1000 的记录，按 ID 倒序返回 |
| `page=a1000` | 顺序分页：ID **大于** 1000 的记录，取数时升序、返回前再倒过来 |

* 三种形式之外的值（非数字、游标 ID 超出 32 位整数上限）抛 `PaginationError` → HTTP `410`，
  正文是 `{"success": false, "message": ...}`；编号页超过上限同样是 `410`；
* `limit` 收纯数字，取值范围 `0..320`（`Danbooru.config.max_per_page`）；缺省或空串取站点默认 `75`
  （`Danbooru.config.records_per_page`），只有帖子分页额外使用账号的 `per_page`；
* `tags` 里的 `limit:` 元标签同样能给出每页数量，但只在**顶层 `limit` 缺省时**生效
  （上游 `PostSets::Post` 里是 `limit || 元标签` 的顺序）；
* 帖子列表的顶层 `random` 参数**不是**分页/排序手段：它只影响服务端的呈现判定，要随机结果得用
  `order:random` 元标签或 `post_random`。

`a` 游标返回的数组同样是新的 ID 在前：继续向新记录翻页时取当前页首项，取末项会重复。

```python
from anybooru import E621

with E621('e621') as client:
    # GET https://e621.net/posts.json?tags=rating%3As&limit=2
    posts = client.post_list(tags='rating:s', limit=2)      # 数组；每项有 id / rating / file.url / tags
    print(posts[0]['id'], posts[0]['file']['url'])

    # GET https://e621.net/posts/count.json?tags=rating%3As
    counts = client.post_count(tags='rating:s')             # {'count': …, 'capped': bool}
    print(counts['count'], counts['capped'])

    # 6715093 是已取得的帖子编号，b 前缀表示只查编号比它小的帖子。
    # GET https://e621.net/posts.json?tags=rating%3As&page=b6715093&limit=2
    older_posts = client.post_list(tags='rating:s', page='b6715093', limit=2)
    print(len(older_posts))
```

计数端点 `post_count` 走 `/posts/count.json`（不是 `/counts/posts.json`，那是 Danbooru 的路径），
返回 `{"count": N, "capped": bool}`；`capped` 为 `true` 时表示搜索触到了分页上限
（`750 × 320 + 1 = 240001`），此时的 `count` 是下限而不是精确值。

## Serika 的分页

Serika 的两个面各带自己的翻页信息，客户端都不替你剥出来：

| 方法 | 参数 | 翻页信息在返回的哪里 |
| :--- | :--- | :--- |
| `internal_image_list(page=…, limit=…)`（站内匿名读） | 服务端把空 `page` 当 `1`、空 `limit` 当 `24`，并把 `limit` 压在 `100` 以内；客户端不钳位 | 返回体是 `{"success": true, "images": [...], "pagination": {page, limit, total, pages, has_next}}`，条目在 `images`、翻页在 `pagination` |
| `image_list(...)` / `tag_list(...)`（官方 v1，分别需要 `images:read` / `tags:read`） | 服务端把 `page` 抬到至少 `1`、把 `limit` 夹在 `1..100` | 方法返回 `data` 里的内容，`meta` 留在 `client.last_call['meta']`，里面有 `pagination`（`page` / `limit` / `total` / `pages`，只有非空页才有 `has_next` / `has_prev`） |
| `user_list(...)`（官方 v1，匿名可达） | 服务端自己的默认值 | 返回的是 `users` 数组，翻页在 `client.last_call['meta']['pagination']`（只有 `page` / `limit` / `total` / `pages`） |
| `internal_artist_list(page=…, limit=…)` | 同上 | 返回体 `{"success": true, "artists": [...], "pagination": {page, limit, total, pages}}`，没有 `has_next` |

`last_call` 只保留**最近一次**请求，要跨请求用就先把它取出来存好。

```python
from anybooru import Serika

with Serika('serika') as client:
    # GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest
    body = client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')
    print(body['pagination']['page'], body['pagination']['limit'], body['pagination']['has_next'])
    for image in body['images']:
        # post_id 是公开序号，id 是站内数据库 id，两者不能互换
        print(image['post_id'], image['url'])

    # GET https://serika.art/api/images?page=2&limit=3&ratings=safe&sort=newest
    page_2 = client.internal_image_list(page=2, limit=3, ratings='safe', sort='newest')
    print(len(page_2['images']))
```

官方 v1 的 `image_list` / `tag_list`（`https://serika.art/api/v1/images?page=1&limit=3` 这类地址）需要 API key，
本仓库没有凭据，只对过源码，没有实测成功响应。

## Zerochan 的分页

`entry_list` 用 `p`（页码）与 `l`（每页条数），不是 `page` / `limit`。API 页面写 `l` 的范围是 `1–250`，
没有公布缺省值，也没有公布 `p` 的边界；客户端不做钳位、不补默认值。
列表接口的正文是 `{"items": [...]}`，方法给你里面的数组；已观察到的响应里没有 `total` / `page` 这类
翻页信息，所以库不构造总数，也不给你下一页游标。

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    # GET https://www.zerochan.net/?p=1&l=2&s=id&json=
    entries = client.entry_list(p=1, l=2, s='id')     # 数组；每项有 id / width / height / md5 / thumbnail / source / tag / tags
    for entry in entries:
        print(entry['id'], entry['tag'], entry['thumbnail'])

    # GET https://www.zerochan.net/?p=2&l=2&s=id&json=
    page_2 = client.entry_list(p=2, l=2, s='id')
    print(len(page_2))
```

`s` 换 `fav` 时按人气排序，配合 `t`（`0` / `1` / `2`）选择人气统计窗口，例如
`client.entry_list(l=2, s='fav', t=0)`。默认每页条数与分页请求记录见
[Zerochan 验证](verification.md#zerochan匿名只读实测2026-09-18)，参数说明见
[Zerochan 方法参考](zerochan-api.md)。末页、越界页码和非法 `l` 会怎样，还没有实测。

## 相关文档

* [方法参考导航](index.md#按家族选文档)：各家族参数与返回形状
* [errors.md](errors.md)：限流、参数错误等失败情形
