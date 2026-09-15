# Serika 方法参考：官方 v1 与站内匿名读

Serika 客户端共 **30 个原生方法**，分两面：官方版本化 `/api/v1`（16 个）与站内未版本化
`/api/*` 的匿名只读（14 个，统一 `internal_` 前缀）。选哪一面看
[能力总览](serika-capabilities.md)，契约出处、逐条状态与官方文档矛盾见
[契约审计附注](serika-contract-notes.md)。本页按站点控制器整理：官方文档页只收录 16 个动词里的
10 个，未收录的以控制器为准。

**本页分两级**：每个资源组先给常用方法的完整片段与真实返回形状，其余方法按
`签名 — 何时用；返回要点` 一行列出。参数钳位、错误码、上游出处与逐条参数表在
[附注的长尾方法参数与错误码](serika-contract-notes.md#长尾方法参数与错误码)；
全部 30 个实际签名另有[总表](serika-contract-notes.md#方法签名总表30)。
方法都是 `Serika.request()` 的一行薄封装：参数原样交给服务端，库不校验、不钳位、不重试、不翻页。

## 官方 v1：共同模式

* **认证**：配置了 `api_key` 就固定发 `Authorization: Bearer sk_serika_*`；服务端也接受
  `X-API-Key: sk_serika_*`，本库只发前者。无 key 时可达的只有 4 个方法（`api_index`、`stats`、
  `user_list`、`random_image`），其余会被拒：缺 key 是 `401`，key 缺权限是 `403`，超限是 `429`，
  但三种情况的正文 `code` 都可能是 `UNAUTHORIZED`，要连 HTTP 状态一起看。
* **信封**：多数方法走 `envelope="data"`——返回 `data`，整个服务端 `meta` 留在 `last_call['meta']`。
  两个例外：`api_index` 是裸对象、`user_list` 用 `users` 键；`random_image` 返回图片字节。
* **参数**：扁平字典；`tags`/`ratings`/`exclude_tags` 是逗号分隔**字符串**，不是列表，也不是
  搜索表达式；布尔落成小写 `true`/`false`；`None` 不发送。无文件时请求体是 JSON 并保留显式空数组。
* **分页**：`meta.pagination` 带 `page`/`limit`/`total`/`pages`（`has_next`/`has_prev` 视路由与分支）。
* **ID**：官方图片路由用**内部图片 id**（响应里的 `id`/`dbid`），站内详情与评论用**公开序号**
  （响应里的 `post_id`）；两者数值不同、不可互换。

### 前置块（下面所有片段共用）

```python
from pybooru import Serika

client = Serika('serika')
example = client.config['examples']['serika']
```

每个片段都用这个 `client`，参数从 `example`（配置 `examples.serika`）取，不硬编码；
片段之间可以独立接续运行，全部结束后调用 `client.close()`。想一次性用完即关，也可以写
`with Serika('serika') as client:`。

### 索引、统计、用户目录（常用）

`api_index()` — `GET /api/v1`，公开。

```python
info = client.api_index()
print(info['name'], info['version'])      # 实测：SerikaART API 1.0.0
```

返回裸对象：`name`、`version`、`description`、`documentation`、`endpoints`、`authentication`、
`rate_limits`，没有 `success`/`data` 信封。

`stats()` — `GET /api/v1/stats`，公开。

```python
statistics = client.stats()
print(statistics['totals'])
```

返回 `totals{images,tags,users}`、`images_by_rating{safe,questionable,explicit}`、
`images_by_type{ai_generated,non_ai}`、`activity{uploads_last_24h}`。实测 `totals`：
images **4237843**、tags **730851**、users **3058**；按评级 safe **3499663**、questionable
**324774**、explicit **413406**，AI 图 **14195**、非 AI 图 **4223648**、最近 24h 上传 **0**。

`user_list(page=None, limit=None, q=None, sort=None)` — `GET /api/v1/users`，公开。

```python
users = client.user_list(**example['user_query'])
print(users[0]['username'], client.last_call['meta']['pagination'])
```

返回 `users` 数组（`envelope="users"` 特例：服务端既没有 `data` 也没有 `meta`），分页放在
`last_call['meta']['pagination']`，只有 `page`/`limit`/`total`/`pages`。每项是 camelCase：
`_id`、`id`、`username`、`avatarUrl`、`rank`、`createdAt`、`uploadCount`（只数公开图）。
实测返回 1 个用户 `Giru`，pagination `page=1 limit=1 total=3058 pages=3058`。

本组其余方法：

* `user_show(identifier)` — 按账号 id（文本主键）或用户名取单个用户（需 `users:read`）；
  返回 `{id, username, avatar_url, rank, stats{images,total_upvotes,total_views}, created_at}`。

### 官方图片

权限按方法区分：`image_list`、`image_show`、`image_similar`、`image_batch` 要 `images:read`；
`image_delete` 要 `images:delete`（发 key 时只有 admin/owner 能拿到这个权限位）。
ID 一律是**内部图片 id**。

* `image_list(page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, q=None, user_id=None, min_width=None, min_height=None)` — 官方图片列表：`tags` 逗号字符串取**交集**，`ratings` 缺省即只看 `safe`，`sort` 支持 `newest`/`oldest`/`popular`/`favorites`/`views`/`random`；返回图片数组 + `meta.pagination`。
* `image_show(image_id)` — 按内部 id 取单图；返回完整行（`post_id`、`original_filename`、`stats.score`、评论计数等），每次成功调用会让 `views` 加一。
* `image_similar(image_id, limit=None)` — 找同 rating 的公开相似图；返回 `{"source_id","similar","count"}`，按共享标签数、再按 upvotes 排序，每项带 `shared_tags`。
* `image_batch(ids)` — 一次按多个内部 id 批量取图，`ids` 走 JSON 体；返回 `{"images","found","requested"}`，命中项按请求顺序。
* `image_delete(image_id)` — 删除图片及其依赖行；返回 `{"deleted": true, "id": "..."}`，非属主且 rank 不是 admin/owner 会被拒。

### 官方随机

`random_image(width, height, fit=None, format=None, quality=None, tags=None, ratings=None, exclude_tags=None, blur=None, grayscale=None, ai=None, no_ai=None, match_size=None, aspect_tolerance=None)`
— `GET /api/v1/random/:width/:height/image.png`，**公开**，返回原始字节。

```python
picture = client.random_image(**example['random_size'], **example['random_query'])
print(len(picture), client.last_call['headers']['Content-Type'])
```

实测：Python 类型 `bytes`、**81224 字节**、`Content-Type: image/png`。
`last_call['headers']` 另带 `X-Image-Id`/`X-DBID`（内部 id **2796776**）、`X-Post-Id`
（顺序号 **1416106**）、`X-Original-Width`/`X-Original-Height`/`X-Rating`。这些标识由服务端
随机选图产生，每次调用都可能不同。`width`/`height` 是路径段，服务端接受 16..8000，
越界返回 `400` 纯文本。
**注意**：无匹配时服务端仍回 `200`，但正文是灰色占位 PNG，控制器内部出错时是红色占位 PNG；
只有命中才带上面那些 `X-*` 头，所以 HTTP 200 本身不能证明选到了图。

本组其余方法：

* `random_list(count=None, ratings=None, tags=None, exclude_tags=None, min_width=None, min_height=None, max_width=None, max_height=None, ai=None, no_ai=None)` — 官方随机**元数据**列表（需 `random:read`）：生效 `count` 为 1 时 `data` 是对象、否则是数组，`meta` 另带 `count`/`requested`。

### 标签、搜索与热门

* `tag_list(page=None, limit=None, q=None, type=None, sort=None, min_count=None)` — 官方标签列表（需 `tags:read`）：默认按 `count` 排序，`q` 是名称子串，`type` 只认五个枚举值；返回 `[{id,name,type,count,created_at}]` + `meta.pagination`。
* `tag_show(name)` — 单个标签 + 最多 5 张 safe 样本图（需 `tags:read`）；`count` 是重算的公开图计数。
* `search(q, type=None, limit=None, ratings=None)` — 一次搜图片/标签/用户（需 `images:read`）：`q` 至少 2 个字符，`type` 取 `all`/`images`/`tags`/`users`；返回只含被请求的分支。
* `trending(period=None, limit=None, ratings=None)` — 一段时间的热门图与标签（需 `images:read`）：`period` 取 `day`/`week`/`month`；返回 `{period, images, tags}`，图片带 `trend_score`，标签最多 20 个。

### 上传

* `upload(file, tags, rating, is_ai_generated=None, source=None, description=None)` — 上传图片（需 `upload` 权限，唯一的 multipart 端点）：`file` 传 requests 的 `(filename, fileobj, content_type)` 三元组并**显式给 MIME**（服务端只收 `image/jpeg`/`image/png`/`image/gif`/`image/webp` 且 ≤50MB），`tags` 是原样发送的字符串；返回新图对象与 `meta.message`。

## 站内匿名读：共同模式

站内面**没有版本号、没有兼容承诺**，路径不带 `.json` 后缀，动词由各路由自己决定。

* **不拆信封**：`internal_*` 全部返回原始 JSON（`{"success": true, ...}` 加各自资源键，如 `images`、
  `image`、`comments`、`tags`、`artists`、`user`），分页留在返回体里；官方的 `data`/`meta` 拆封不适用。
* **参数**：扁平字典，服务端字段名**大小写敏感**，Python 形参层用下划线：`hide_ai=` → 线上
  `hideAI=`，`user_id=` → 线上 `userId=`，`query=` → 线上 `q=`。`tags`/`ratings` 同样是逗号字符串。
* **ID**：图片详情与评论用**公开序号**，即列表响应里的 `post_id`/`sequential_id`（内部图片 id
  只属于官方 v1 接口和列表数据本身），两者不可互换。
* 参数默认值由服务端决定；不传就是不传，库不补默认值、不做钳位。
* 下面的片段继续用同一个 `client` 与 `example`，可独立接续运行。

### 站内图片（常用）

`internal_image_list(*, page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, hide_ai=None, query=None, user_id=None, username=None)`
— `GET /api/images`。

```python
listing = client.internal_image_list(**example['image_query'])
print(listing['pagination'])
print(listing['images'][0]['id'], listing['images'][0]['post_id'])
```

实测：3 张 safe 图，内部 id **7323837/7323836/7323835**，对应 post_id
**4237836/4237835/4237834**；`pagination.total=3499663`、`pages=1166555`、`has_next=true`。
返回 `{"success": true, "images": [...], "pagination": {page,limit,total,pages,has_next}}`。
每项同时给数据库名与前端别名：`id`/`dbid`/`_id`（内部 id）、
`sequential_id`/`post_id`/`sequentialId`（公开序号）、`url`、`thumbnail_url`/`thumbnailUrl`、
`width`、`height`、`rating`、`is_ai_generated`、`user_id`/`userId`、`username`、`upvotes`、
`downvotes`、`favorites`、`views`、`created_at`、`tags`。

`internal_image_show(image_id)` — `GET /api/images/:id`，路径段是**公开序号 `post_id`**。

```python
detail = client.internal_image_show(listing['images'][0]['post_id'])['image']
print(detail['id'], detail['post_id'], detail['rating'], detail['url'])
```

实测：用列表首图的 `post_id=4237836` 取到同一资源（内部 id **7323837**、rating `safe`），
URL 与列表相同。返回 `{"success": true, "image": {...}}`，比列表多 `original_filename`、
`content_type`、`source`、`description`、`deleted`、`unlisted` 与 `updated_at` 等字段。

本组其余方法：

* `internal_image_comments(image_id)` — 按公开序号读某图评论；返回 `{"success": true, "comments": [...]}`，按创建时间升序。

### 站内标签（常用）

`internal_tag_list(*, query=None, limit=None, type=None)` — `GET /api/tags`。

```python
tags = client.internal_tag_list(**example['tag_query'])['tags']
print([(tag['name'], tag['count']) for tag in tags])
```

实测：`highres: 3402288`、`1girl: 3223922`、`solo: 2597729`。返回
`{"success": true, "tags": [...], "grouped": {...}}`：`tags` 按使用计数降序，每行是标签整行
（`id`、`name`、`type`、`count`、`created_at`）；`grouped` 是同一批行按 `type` 分桶。

本组其余方法：

* `internal_tag_show(name)` — 按名读单个标签，空格与下划线变体都能命中；返回 `{"success": true, "tag": {_id,id,name,type,count,createdAt}}`。
* `internal_tag_autocomplete(query, *, limit=None)` — POST 只读的输入补全；返回 `{"success": true, "suggestions": [...]}`，按完全匹配、前缀、词边界、使用计数排序。
* `internal_tag_complementary(tag)` — POST 只读的搭配标签；返回最多 3 条 `{name,type,count}`。

### 站内画师（常用）

`internal_artist_list(*, page=None, limit=None)` — `GET /api/artists`。

```python
artists = client.internal_artist_list(**example['artist_query'])['artists']
print([(artist['tagName'], artist['postCount']) for artist in artists])
```

实测：`dairi: 17186`、`inoino: 4265`、`nyantcha: 2785`。返回
`{"success": true, "artists": [...], "pagination": {page,limit,total,pages}}`（没有 `has_next`），
按画师标签的使用计数降序；每行 `_id`、`tagId`（都是字符串）、`tagName`、`claimedByUserId`、
`claimedByUsername`、`verified`、`avatarUrl`、`bannerUrl`、`bio`、`socials`、`postCount`、
`createdAt`。

本组其余方法：

* `internal_artist_show(tag_name)` — 画师页（标签 `type` 必须是 `artist`）；返回 `tag`、`artist`（标签存在但没有资料行时为 `null`）与 `reviews{count, averages}`。
* `internal_artist_wiki(tag_name)` — 画师 wiki；返回 `{"success": true, "wiki": {...} | null}`，含 `content`、`infobox`、`lastEditedBy`、`lastEditedAt`、`editCount`。
* `internal_artist_reviews(tag_name)` — 画师评价，最新的在前；每行含 `ratings`（`trust`/`quality`/`communication` 必有，`pricing` 可选）与 `comment`。

### 站内用户

* `internal_user_list(username)` — 注意这是**按用户名查单个用户**（`username` 必填）；返回 `{"success": true, "user": {...}}`。
* `internal_user_show(user_id)` — 按**账号 id**（文本主键）取用户；返回 `{"success": true, "user": {id, username, avatarUrl, rank, createdAt}}`。
* `internal_user_activity(user_id, *, type=None)` — 用户的点赞与评论，`user_id` 也可传用户名，`type` 取 `all`/`likes`/`comments`；每段最多 50 条。

## 通用入口

没有原生封装的路由（例如将来新增的 v1 动词）直接用通用入口，仍然复用上面的 `client`：

```python
body = client.request('GET', 'api/v1/stats')
rows = client.request('GET', 'api/v1/tags', envelope='data')
```

`request(method, path, *, params=None, data=None, files=None, binary=False, envelope=None)`：
`path` 是相对路径，不自动补后缀也不补版本；动态路径段的转义由原生方法负责，
通用入口里的完整路径由调用方负责。`envelope` 只取 `'data'` 或 `'users'`，不做形状猜测或后备字段搜索。

## 错误与状态码

非 2xx 一律抛 `PybooruHTTPError`；JSON `code` 从 `error.data['code']` 读，非 JSON 正文时 `data` 为 `None`。
官方 v1 的缺 key / key 缺权限 / 超限分别是 HTTP `401` / `403` / `429`，但**三种情况的正文 `code`
都可能是 `UNAUTHORIZED`**（只有"删别人的图且不是 admin/owner"才是 `FORBIDDEN`），
所以判断失败原因要连 HTTP 状态码一起看。

## 边界与未实测

* **已实测**（2026-09-15 匿名实跑，命令与真实输出见
  [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)）：`api_index`、`stats`、
  `user_list`、`random_image` 与 `internal_image_list`、`internal_image_show`、`internal_tag_list`、
  `internal_artist_list`，共 8 次调用、8 个 HTTP `200`。
* **需 key 的 12 个官方方法成功路径全部未实测**：`image_list`、`image_show`、`image_delete`、
  `image_similar`、`image_batch`、`random_list`、`tag_list`、`tag_show`、`user_show`、`search`、
  `trending`、`upload`；其中 8 个 GET 有匿名 `401` 的历史记录，另 4 个动词只有源码依据。
* **站内其余 10 个方法仅源码对齐**：`internal_image_comments`、`internal_tag_show`、
  `internal_tag_autocomplete`、`internal_tag_complementary`、`internal_artist_show`、
  `internal_artist_wiki`、`internal_artist_reviews`、`internal_user_list`、`internal_user_show`、
  `internal_user_activity`。
* 自托管部署、认证成功路径、权限/限流、上传/删除、PNG 占位图的错误分支与参数组合均未实测；
  逐条状态见 [附注的路由清单](serika-contract-notes.md#路由清单与逐条状态)。

继续阅读：[客户端用法](serika.md) · [能力总览](serika-capabilities.md) ·
[契约审计附注](serika-contract-notes.md) · [错误处理](errors.md) · [线上验证状态](verification.md)。
