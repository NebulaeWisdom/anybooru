# 分页

## 客户端行为

十二个家族的页码参数名不一样：Danbooru、Moebooru、Serika、e621ng 用 `page` / `limit`，
Sakuria 用 `page` / `size`，Zerochan 用 `p` / `l`，Gelbooru 的 post/user 用 `pid` / `limit`，
tag 用 `after_id`，删除流用 `last_id`。
Gelbooru02（TBIB）用 `pid` / `limit`；Shuushuu 的资源列表用 `page` / `per_page`，
标签搜索 `search` 用 `limit` / `offset`。
Anime-Pictures 的帖子列表用 **0 起步**的 `page` / `posts_per_page`，标签、用户与评论列表用 `limit` / `offset`。
Cosine 的 `image_list` / `artist_list` 用 `page`（1 起）/ `pageSize`，`search` 用 `limit` / `offset`，
`tag_images` 用 `start` / `limit`。
nhentai 的画廊、标签、分类法与 GTS 列表用 `page`（1 起）/ `per_page`，`limit` 只出现在
`gallery_suggestions` / `gts_new_tags` / `tag_search` 上（取几条，不是页码）。

* 页码与每页数量原样发给服务端，不裁剪、不改写、不补默认值（服务端自己的默认值与上限见下文各节）；
* 不自动翻页：没有生成器，也没有内部循环，一次调用就是一次请求；
* 失败不自动重试，包括被限流的情况；
* 返回服务端给的那一页：有的家族直接返回数组，有的把数组包在 `{"posts": [...]}` 或 `{"items": [...]}` 里
  （nhentai 是 `{"result": [...]}`），见各节。

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

## Gelbooru 的分页

Gelbooru 面同样不做任何本地分页：`post_list(**params)` 这类方法把你给的查询键原样拼进
`index.php?page=dapi&…`，本库不补默认值、不裁剪、不自动翻页。

| dapi 方法 | 分页输入（官方 wiki 的参数名） | 字面调用 |
| :--- | :--- | :--- |
| `post_list` / `user_list` | `pid` 页码、`limit` 每页数量；wiki 写默认数量 100，外部资料记页码从 0 开始 | `client.post_list(pid=1, limit=2)` |
| `tag_list` | `after_id` 只取编号更大的标签、`limit` 数量，wiki 写默认 100 | `client.tag_list(after_id=100, limit=2)` |
| `post_deleted` | `last_id` 只取大于给定编号的删除记录，默认值未规定 | `client.post_deleted(last_id=100)` |
| `comment_list` | 只列 `post_id`，未列分页字段 | `client.comment_list(1)` |

这些 dapi 的分页成功返回均**未实测（需账号）**；另有五方法匿名401空正文的真实记录。旧 help 对帖子写硬上限100，
与 wiki 的默认 100 不能混为一谈；也没有依据承诺响应一定含总数、当前页或下一页链接。
完整自足代码见[Gelbooru 方法参考](gelbooru-api.md)，矛盾见[契约附注](gelbooru-contract-notes.md)。
`autocomplete` 不提供已确认的分页参数；本次 `limit=3` 仍收到 10 条，库不按它截断结果。

## Gelbooru02（TBIB）的分页

TBIB 帖子用 `pid`（页码）与 `limit`（每页条数）；示例第一页取 `pid=0`。显式请求 XML：

```python
from xml.etree import ElementTree
from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    posts_xml = client.post_list(tags='rating:safe', pid=1, limit=2, response_format='xml')
    # GET https://tbib.org/index.php?tags=rating%3Asafe&pid=1&limit=2&s=post&q=index&page=dapi
    posts = ElementTree.fromstring(posts_xml)
    print(posts.attrib['count'], posts.attrib['offset'])
```

实测 `pid=1&limit=2` 返回 `<posts count="7928682" offset="2">` 与两条 `post`。
不指定 `pid` 的 XML 首次请求根 `offset=0`；按单个 `id` 查时 `count=1,offset=0`。
**JSON 形式没有这层根信息**：`post_list` 默认返回数组，没有 `count/offset`；数组长度只表示本次条数，
不是匹配总数。客户端不补 `pid/limit`，也不读取根元素替你继续翻页。

站点 `index.php?page=help&topic=dapi` 写帖子 `limit` 硬上限 100，但实测 `limit=101` 返回 101 条，
真实上限未经确认。删除流由帮助页明确使用 `last_id`，不是 `pid`；其成功返回与游标推进未实测。
标签与评论的分页规则没有帮助页依据；删除流查询 `last_id=0,limit=1` 得到 `500`。逐方法说明见 [Gelbooru02 方法参考](gelbooru02-api.md)，
边界与来源见 [Gelbooru02 契约审计附注](gelbooru02-contract-notes.md)。

## Shuushuu 的分页

`page` 从 1 开始，`per_page` 范围 1–100、默认20。客户端保留完整列表响应，如
`{"total": 722909, "page": 1, "per_page": 2, "images": [...]}`，不拆掉页码和计数、不主动请求下一页。
以下两个调用各发一次 GET：

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    first_page = client.image_list(tags='46', page=1, per_page=2)
    # https://e-shuushuu.net/api/v1/images?tags=46&page=1&per_page=2
    second_page = client.image_list(tags='46', page=2, per_page=2)
    # https://e-shuushuu.net/api/v1/images?tags=46&page=2&per_page=2
    print(first_page['total'], second_page['page'])
```

`search(q='long hair', limit=2, offset=2)` 是标签搜索的偏移分页，`limit` 1–100 默认20，
`offset` 0–500000 默认0；不要把它搬进 `tag_list`，标签列表没有 `limit` 参数。
`image_reposts` 是不分页的 `total/items` 对象。各方法的精确字段见[方法参考](shuushuu-api.md)。
同一标签的 `image_list(tags=...)`、`tag_images(id)` 和 `tag_show(id)` 总数口径不同，不应互换计数。
`per_page=101` 的422及两页实际返回见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。

## Sakuria 的分页

Sakuria 插画搜索用 `page`（页码）与 `size`（请求条数）；其它路由不能照搬这组参数，
例如插画评论有 `page/size`，系列详情也收 `page`。客户端原样转发，不补默认值、不裁剪、不自动翻页。

```python
from anybooru import Sakuria

with Sakuria('sakuria', access_token='') as client:      # 显式空串 = 匿名，不读配置里的 token
    # GET https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=1
    first_page = client.illust_search(q='blue', size=2, sort='new', page=1)
    for illust in first_page['items']:
        print(illust['id'], illust['title'])

    # GET https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=2
    second_page = client.illust_search(q='blue', size=2, sort='new', page=2)
    print(second_page['page'], second_page['hasMore'], second_page['nextPage'])
```

不要把数值 `nextPage` 当下一相邻页；`page` 本身仍回显请求页码。`/search/illust?q=blue&size=24` 的 `page=1/2/3` 本轮分别返回
`total` 48/72/96、`totalPages` 4/4/6、`nextPage` 4/4/6，而第 1 页与第 2 页有 24 个相同的 `id`、
第 2 页与第 3 页有 10 个相同：**`total` 不是匹配总数，`nextPage` 也不是相邻页码**，
拿它们跳页会漏数据或打转。可靠的推进方式是**手动把 `page` 加 1**，并在展示前按 `id` 去重。
`hasMore` 为 `false` 表示列表到头——本轮没有跑到末页，「末页一定回 `hasMore: false`」仍只是候选输入的说法（未实测）。

`size` 只证实了两个边界样本：`size=1` 返回 5 条、`size=24` 返回 29/24/33 条、`size=48` 返回 39 条，
而 `size=0` 与 `size=49` 都是 `400`（`code: invalid_search_filter`、`field: size`）。
也就是 1 与 48 被接受、0 与 49 被拒绝；**响应条数不等于、也不保证不超过 `size`**，48 也不是已证实的最大返回条数。
客户端不做钳位、不补默认值，也不因为你传了 `size` 就假定拿到几条。

各路由的分页字段并不统一（下表全部是本轮匿名样本）。传了 `size` 的路由把 `pageSize` 原样回显
（`size=1/24/48` 都一一对应），但实际条数并不等于它；没传 `size` 的路由各自返回 12 或 24 的 `pageSize` 样本：

| 本轮请求 | 分页字段与样本 |
| :--- | :--- |
| `/search/illust?q=blue`、`/search/novel?q=blue`、`/tags/blue`、`/users/{id}/illusts` | `{items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}`；`/users/{id}/illusts` 的 `page=1/2` 各 45 条、两页交集 23 |
| `/users/{id}/novels`、`/users/{id}/bookmarks` | 用 `nextCursor` 而不是 `nextPage`；`/users/{id}/bookmarks` 的 `page=1` 与 `page=2` 返回**完全相同的 JSON**（19 条，`nextCursor` 都是 `9175901406`），这两个取值不能推进 |
| `/users/{id}/followers`、`/users/{id}/series` | 只有 `page` / `pageSize` / `hasMore`；`followers` 的 `page=1`、`page=2` 都是空 `items`，`page` 回显请求值 |
| `/spotlight`、`/novels/{id}/related` | 有 `hasMore`，没有 `nextPage`；`/spotlight?page=1&lang=zh-cn` 的 `pageSize` 是 12、`items` 是 20 条 |
| `/search/user?q=mika` | `total` 与当页 `items` 条数相同（`page=1/2/3` 分别 6/12/21），三页 `id` 互不重叠——**不是累计值**，页码越高每页越长 |
| `/illust/{id}/related`、`/users/{id}/related`、`/illust/{id}/comments/{cid}/replies` | 只有 `{items}`，没有页码字段；`/illust/{id}/comments` 是 `{items, hasMore}` |

以上只是样本：`page` 只试过列出的这些取值，越界、非数字与末页行为未测；
`/users/{id}/followers` 空列表、`/users/{id}/bookmarks` 分页不推进都只对试过的两个 `page` 值成立，
不能推广成「功能未实现」或「所有游标参数无效」。`/me/*` 的 17 个方法需要登录，分页语义未知。
逐条命令与响应见[验证记录](verification.md#sakuria匿名只读实测2026-09-19)与
[Sakuria 契约审计附注](sakuria-contract-notes.md)。

## Anime-Pictures 的分页

Anime-Pictures 的帖子列表用 `page`（**0 起步**）与 `posts_per_page`（每页条数），不叫 `page` / `limit`；
标签、用户与评论列表用的是 `limit` / `offset`。客户端原样转发，不补默认值、不裁剪、不自动翻页，
也不按 `max_pages` 替你停手。

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    # GET https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2
    first_page = client.posts_list(page=0, posts_per_page=2)
    # 信封是 posts 数组 + 五个分页字段：response_posts_count 是本页实际条数，
    # posts_per_page 是服务端实际使用的每页条数，page_number 回显请求页码（0 起步），
    # posts_count 是当前过滤条件下的总数，max_pages 是最后一个可用页码（也 0 起步）
    for post in first_page['posts']:
        print(post['id'], post['score_number'])
    print(first_page['page_number'], first_page['response_posts_count'],
          first_page['posts_count'], first_page['max_pages'])

    # GET https://api.anime-pictures.net/api/v3/posts?page=1&posts_per_page=2
    second_page = client.posts_list(page=1, posts_per_page=2)
    print([post['id'] for post in second_page['posts']])

    # GET https://api.anime-pictures.net/api/v3/tags?tag=hatsune+miku&limit=20&offset=0
    tags = client.tags_list(tag='hatsune miku', limit=20, offset=0)
    # 标签、用户、评论列表的回显字段是 offset / limit / count（count 是匹配总数，不是本页条数）
    print(tags['offset'], tags['limit'], tags['count'])
```

本轮实测（匿名、串行、每个请求只发一次）：`page=0` 与 `page=1` 都回 `200`，`page_number` 分别回显 `0` 与 `1`；
`posts_per_page=2` 时 `response_posts_count` 是 `2`，当天全库 `posts_count=667906`、`max_pages=333952`。
数量会变，字段与页码语义也只代表当前已测 API；客户端不会自动适配站点未来改动。
`post_comments` 的实测响应里只有 `success` 与 `comments`，没有观察到分页字段——这不能反推「任意分页参数无效」。

**已实测的边界**：

| 输入 | 实测 |
| :--- | :--- |
| 不传 `page` / `page=abc` | `400` JSON，``{"errormsg":"Missing or invalid `page` parameter","success":false}``——页码必填 |
| `page=-1` | `500` JSON，`{"errormsg":"Internal server error","success":false}` |
| `page=999999`（远超末页） | `200`，`posts` 是空数组、`response_posts_count=0`，但 `posts_count` / `max_pages` 仍回全量值 |
| `posts_per_page` 缺省 | `80` |
| `posts_per_page=1` / `2` / `3` / `100` | 原值回显，本页条数等于该值（**没有**穷举 `1..100`） |
| `posts_per_page=101` / `150` / `1000` / `0` | 回落成 `60` |
| `posts_per_page=-1` | 回到 `80` |
| 标签 / 用户 / 评论列表缺省 `offset` / `limit` | `0` / `20` |
| 标签 `limit=1000`、用户与评论 `limit=101` | 都回到 `100` |
| `offset=2` | 跳过基线的前两项（`offset` 回显请求值） |

`max_pages` 不能无条件按公式推：`search_tag=zzzznotexist` 返回 `posts_count=0`、`posts=[]`、`max_pages=0`
（不是 `-1`）。客户端不做钳位、不补默认值、不替你算 `max_pages`，越界页返回空数组也不报错；
参数与返回字段见[方法参考](anime-pictures-api.md)，逐条证据见
[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。

## Cosine 的分页

Cosine 面固定三套分页参数，互不通用；客户端原样转发，不补默认值、不裁剪、不自动翻页：

| 方法 | 输入 | 返回里怎么看下一页 |
| :--- | :--- | :--- |
| `image_list(page=…, pageSize=…)` | `page` 是**页码**（1 起）、`pageSize` 是每页条数；两者都不传时站点自己给每页 10 条 | 外壳 `{"images": [...], "total": N}`；`total` 是真实条数，但响应里没有页码字段，翻页靠自己把 `page` 加 1 |
| `artist_list(page=…, pageSize=…, sortBy=…)` | 同上 | 外壳 `{"artists": [...], "total": N, "hasNextPage": bool}`，另有 `hasNextPage` 布尔值提示是否还有下一页 |
| `search(q=…, limit=…, offset=…)` | `limit` 是每页条数（站点缺省 20）、`offset` 是已经跳过的条数（缺省 0） | 外壳 `{"success": true, "data": {...}}`；`data` 里回显 `limit` / `offset` 与 `total`，但 `total` 被夹到 **1000** |
| `tag_images(tag, start=…, limit=…)` | `start` 是已经跳过的条数、`limit` 是条数 | **裸数组、没有 `total`**：本页返回空数组就是到底了 |

`page` 与 `offset` 不是同一件事：`page` 是页码（`image_list` 第二页写 `page=2`），`offset` 是跳过的条数
（`search` 第二页写 `offset=2`，不是 `page=2`）。两者都不能按 `total` 反推总页数：`search` 的 `total` 是
Meilisearch 的**估计值**且被服务端夹在 1000——本轮查空 `q`（命中全库）拿到的 `total` 就是 1000，
它既不是本页条数也不是全库总量；`offset` 同样被夹到 1000，`offset=100000` 的样本回显 `offset=1000`
且 `hits` 为空数组。另外搜索**只覆盖站点的搜索索引**，不是数据库本身：同一天只读索引进度报的是
`totalImages` 4953、`indexedImages` 3353（`indexHealth` 为 `partial`），所以同一个标签在数据库路径与搜索路径
上的条数本来就可能不同。**不要拿 `total` 当全库数量，也不要拿它算翻页。**

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    # GET https://pic.cosine.ren/api/list?page=1&pageSize=2
    first_page = client.image_list(page=1, pageSize=2)
    # GET https://pic.cosine.ren/api/list?page=2&pageSize=2
    second_page = client.image_list(page=2, pageSize=2)
    print(first_page['total'], len(first_page['images']), len(second_page['images']))
    for image in first_page['images']:
        print(image['id'], image['pid'])            # 站内编号在 id，上游编号在 pid

    # GET https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2&offset=0
    head = client.search(q='初音', limit=2, offset=0)['data']
    # GET https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2&offset=2
    tail = client.search(q='初音', limit=2, offset=2)['data']
    print(head['total'], head['offset'], tail['offset'])   # total 是估计值（空 q 的样本被夹到 1000），offset 原样回显

    # GET https://pic.cosine.ren/api/tag?tag=GenshinImpact&start=0&limit=2
    tag_page = client.tag_images('GenshinImpact', start=0, limit=2)
    # 裸数组、没有 total：返回 [] 就是这一页没有了
    print(len(tag_page), [image['id'] for image in tag_page])
```

`tag_list()` 是 Cosine 面**唯一不带分页参数**的列表方法：一次返回全量标签（本轮样本 2128 项）。
它的 `count` 是标签行的行数，**不是**用了该标签的作品数——同一个 `RuanMei`，`tag_list` 里的 `count` 是
`9`，而 `tag_images('RuanMei', limit=100)` 实际回了 10 行（只有 8 个不同的 `pid`，这些行的 `tags` 逐项算
一共出现 14 次标签），`search` 的 `total` 又是另一个 `9`（搜索只覆盖索引），四个数字口径不同，
不能互换、也不能把作品数组里的标签累加起来当计数。标签的 `#` 前缀与重复项在各路由不一致，
本库不替你去重、不剥前缀，要匹配请先统一处理。

本轮实测的边界：`image_list` 的 `page=1` 与 `page=2` 都回 `200`，`page=0` 与 `page=-1` 回 `500`，
`page=100000` 与 `pageSize=0` 回 `200` 加空 `images`，`pageSize=-1` 回的是**最旧的 1 条**
（站点自己的反向语义），`pageSize=100` 回 100 条、当天 `total` 是 `4953`；`artist_list` 试过
`page=1&pageSize=2`（两行页的 `total` 是 `1708`、`hasNextPage` 为 `true`），`sortBy` 试过 `artworks`、
`random`、`lastUpdate` 与一个不认识的值：不认识的那个也回 `200`，样本里首两项与 `artworks` 相同，
所以“没报错”不等于取值生效；`search` 试过 `limit=2`、
`offset=0` / `2` / `100000`（最后这个被夹到 `1000` 且 `hits` 为空），另外 `limit=-1`、`offset=-5` 与
`sort=bogus` 都是 `500`；`limit=500` 回显 `limit: 100` 且 `hits` 100 条（**上限由站点夹**，客户端不钳位）；
`tag_images` 试过 `start=0` / `2` 与 `limit=2`，`start=2&limit=2` 返回更靠后的行，空数组是这一页到底的表示。
标签必须完整才能命中：`GenshinImpact` 与全小写的 `genshinimpact` 都有结果，`#GenshinImpact` 与逗号串
`原神,GenshinImpact` 都回空数组；`search` 的 `tags=原神,GenshinImpact` 是**多标签 AND**（当天 `total` 160）。
非数字页码与别的取值组合没有完整样本，所以客户端不做钳位、不补默认值、也不替你判末页。
逐条参数与返回字段见[方法参考](cosine-api.md)，状态码样本见[错误处理](errors.md#cosine)，
真实请求记录见[验证记录](verification.md#cosine匿名只读实测2026-09-20)。

## nhentai 的分页

nhentai 的列表用 `page`（页码，**1 起**）与 `per_page`（每页条数）；`gallery_suggestions`、`gts_new_tags`
与 `tag_search` 用 `limit`（取几条，不是页码）。客户端原样转发，不补默认值、不裁剪、不自动翻页，
也不替你判断末页。

| 方法 | 分页输入（取值与默认值来自站点 OpenAPI） | 翻页信息在回包的哪里 |
| :--- | :--- | :--- |
| `gallery_list(**params)` | `page` ≥ `1`，默认 `1`；`per_page` `1..100`，默认 `25` | `{"result": [...], "num_pages": N, "per_page": N, "total": N 或 null}` |
| `gallery_tagged(tag_id, **params)` | `tag_id` 必填；`sort` 取 `date` / `popular` / `popular-today` / `popular-week` / `popular-month`，默认 `date`；`page` / `per_page` 同上 | 同 `gallery_list` |
| `gallery_comments(gallery_id, **params)` | `page` `1..2000`，默认 `1`；`per_page` `1..50`，默认 `50` | 同 `gallery_list` |
| `tag_list(tag_type, **params)` | `sort` 取 `name` / `popular`，默认 `popular`；`page` ≥ `1` 默认 `1`；`per_page` `1..100` 默认 `25` | 同 `gallery_list`，另有 `alphabet`（实测只在 `sort=name` 的样本里出现） |
| `taxonomy_list(**params)` | `page` ≥ `1` 默认 `1`；`per_page` `1..200` 默认 `50`；另有 `tier` / `q` / `target_tag_id` / `sort_by` / `sort` / `action` / `discussion` / `edited` | `{"result": [...], "has_more": bool, "num_pages": N, "total": N}` |
| `taxonomy_resolved(**params)` | `page` ≥ `1` 默认 `1`；`per_page` `1..100` 默认 `25`；另有 `status` / `q` / `discussion` / `edited` / `action` / `sort_by` / `sort` | 同 `taxonomy_list` |
| `taxonomy_comments(suggestion_id, **params)` | `page` ≥ `1` 默认 `1`；`per_page` `1..100` 默认 `50` | 同 `taxonomy_list` |
| `gts_backlog(**params)` | `page` `1..200` 默认 `1`；`per_page` `1..50` 默认 `20`；另有 `tag_id` / `action` / `sort_by` / `sort` | 同 `taxonomy_list` |
| `gallery_suggestions(gallery_id, **params)` | `limit` `1..100` 默认 `20`；`tier` 默认 `all` | `{"result": [...]}`；`has_more` / `num_pages` / `total` 在 OpenAPI 里都是可选字段 |
| `gts_new_tags(**params)` | `limit` `1..50` 默认 `25` | `{"result": [...]}`，没有分页字段 |
| `tag_search(**attributes)` | 请求体里的 `limit` `1..50` 默认 `10`（`query` / `type` 都可省略） | 方法本身不分页；本轮**未调用**（`POST`） |

`search` 只有 `page`（≥ `1`，默认 `1`），**没有** `per_page`；`favorite_list` 只有 `q` 与 `page`。
`gallery_popular` / `gallery_random` / `gallery_related` / `gallery_comment_count` / `taxonomy_stats` /
`taxonomy_edits` / `tag_ids` / `tag_show` / `user_show` / `service_info` / `cdn_config` / `site_config`
**不接受分页参数**。

### 回包形状与实测样本

列表回包是对象，条目数组在 `result` 里；`result` 一定会出现，`num_pages` / `per_page` / `total` 在画廊与标签
列表里也会出现，其中 `total` **可能是 `null`**。分类法与 GTS 的列表另有 `has_more` 布尔值。以下都是本轮匿名
只读样本（每个请求只发一次，数字是快照，不是常量）：

| 请求 | 回包里的分页字段 |
| :--- | :--- |
| `GET /api/v2/galleries?page=1&per_page=2` 与 `page=2` | 两页各 `result` 2 条；样本 `total=646010`、`num_pages=323037`（`ceil(646010/2)` 是 `323005`，**两者不相等**） |
| `GET /api/v2/galleries/tagged?tag_id=12227&per_page=2` | `result` 2 条、`num_pages=73670`、`total` 为 **`null`** |
| `GET /api/v2/search?query=language:english` | `per_page=25`、`result` 25 条、样本 `total=147497`、`num_pages=5900` |
| `GET /api/v2/galleries/{id}/comments?page=1&per_page=2` | `result` 空数组、`num_pages=0`、`per_page=2`、`total=0`（该画廊当天没有可见评论） |
| `GET /api/v2/taxonomy?per_page=2` | `result` 2 条、`has_more=true`、`num_pages=1492`、`total=2984` |
| `GET /api/v2/taxonomy/{id}/comments?page=1&per_page=2` | `result` 2 条、`has_more=true`、`num_pages=10`、`total=19` |
| `GET /api/v2/gts/backlog?per_page=2` | `result` 2 条、`has_more=true`、`num_pages=27919`、`total=55838` |
| `GET /api/v2/gts/new-tags?limit=2` | `result` 2 条，没有分页字段 |

**不要拿 `total` 和 `per_page` 算末页**：`num_pages` 不是 `ceil(total / per_page)`（见上表第一行），
`total` 还可能是 `null`。要推进就手动把 `page` 加 1，走到哪算哪。

**不要用「这一页不满」或「这一页是空的」当停止条件**：实测 `GET /api/v2/galleries?page=100000&per_page=25`
回的是 `200` 加 24 条（编号从 25 往前重复列表尾部的条目），`num_pages` 仍是 `25843`——越界页会重复尾巴而不是
报错或回空数组，所以「短页 / 空页 = 到头」在本家族不成立。搜索无命中是另一回事：实测
`GET /api/v2/search?query=<不存在的词>&page=2` 回 `200` 加空 `result`、`total=0`、`num_pages=0`。

**`per_page` 不保证被采纳**：声明范围内的 `per_page=100` 实测回 100 条，越界的 `per_page=101` 被拒；
但在 `tag_list` 上请求 `per_page=1` 实测回 120 条、回包 `per_page` 是 `120`（同一个端点：请求参数的声明默认值是
`25`，回包 schema 里写的默认值却是 `120`），在 `taxonomy_resolved` 上请求 `per_page=2` 实测回 50 条
——这两个端点的分页密度由站点决定，客户端不钳位。`search` 上不存在的 `per_page=2` 被忽略（仍回 25 条、
`per_page` 回显 `25`）；`taxonomy_resolved` 上未被记录的 `limit=2` 同样回 50 条。
**「没报错」不等于「参数生效」。**

标签列表的 `alphabet` 也不是每个排序都有：`sort=name` 的样本里有它，默认 `sort=popular` 的样本里没有。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='') as client:            # 显式空串＝匿名，不读配置里的 key
    # GET https://nhentai.net/api/v2/galleries?page=1&per_page=2
    first_page = client.gallery_list(page=1, per_page=2)
    print(first_page['per_page'], first_page['num_pages'], first_page['total'])
    for gallery in first_page['result']:
        print(gallery['id'], gallery['media_id'])

    # GET https://nhentai.net/api/v2/galleries?page=2&per_page=2
    second_page = client.gallery_list(page=2, per_page=2)
    print([gallery['id'] for gallery in second_page['result']])

    # GET https://nhentai.net/api/v2/galleries/tagged?tag_id=12227&page=1&per_page=2
    tagged = client.gallery_tagged(12227, page=1, per_page=2)   # tag_id 是标签的编号，取自 tag_show 或 tag_list
    print(tagged['total'], tagged['num_pages'])                 # total 可能是 None

    # GET https://nhentai.net/api/v2/search?query=language%3Aenglish&sort=date&page=1
    hits = client.search(query='language:english', sort='date', page=1)
    print(len(hits['result']), hits['total'], hits['num_pages'])

    # GET https://nhentai.net/api/v2/tags/language?sort=name&page=1&per_page=2
    tags = client.tag_list('language', sort='name', page=1, per_page=2)
    print(tags['per_page'], tags['num_pages'], tags['alphabet'] is not None)
```

参数清单与每个方法的返回字段见[方法参考](nhentai-api.md)，`page=0` / `per_page=101` 这类越界的真实状态码见
[错误处理](errors.md#nhentai)，逐条请求记录见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)。

## 相关文档

* [方法参考导航](index.md#按家族选文档)：各家族参数与返回形状
* [errors.md](errors.md)：限流、参数错误等失败情形
