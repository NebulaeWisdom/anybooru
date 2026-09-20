# Serika 方法参考：官方 v1 与站内匿名读

Serika 客户端共 **30 个原生方法**，分两面：

- **官方版本化 `/api/v1`**：16 个方法。其中 4 个公开、12 个要 API key；成功响应带版本号与自述。
- **站内未版本化 `/api/*`**：14 个方法，统一 `internal_` 前缀，匿名可读，含两个只读 POST。没有版本号，也没有兼容承诺。

本页按资源分组。每个方法给出 HTTP 路由、所需权限、逐参数表（名称 / 类型与取值 / 含义 / 不传时的行为 / 可直接抄的示例）、返回 JSON 的具体字段，以及可复制片段。

所有方法都是 `Serika.request()` 的一行封装：参数原样交给服务端；库不校验、不钳位、不重试、不自动翻页，也不会把官方接口的错误改走站内路由。

选哪一面看[能力总览](serika-capabilities.md)。源码出处、权限过滤器、官方文档矛盾与逐条线上状态见[契约审计附注](serika-contract-notes.md)（官方文档页只收录 16 个动词里的 10 个，未收录的以控制器为准）。30 个方法的实际签名另见附注的[签名总表](serika-contract-notes.md#方法签名总表30)。

## 官方 v1：共同模式

先解释两个词：

- **API key**：服务端签发的访问凭证，形如 `sk_serika_*`。
- **内部图片 id**：数据库里的图片主键；公开序号是站内展示号，响应里叫 `sequential_id` / `post_id`。两者不可互换。

### 认证

- `api_key` 非空时，每个请求带 `Authorization: Bearer sk_serika_*`。
- 服务端也接受 `X-API-Key: sk_serika_*`，本库只发前者。
- 不带 key 时，只有 4 个方法可达：`api_index`、`stats`、`user_list`、`random_image`。
- 缺 key 是 HTTP `401`，key 缺权限是 `403`，超限是 `429`；三种情况的正文 `code` 都可能等于 `UNAUTHORIZED`，要连 HTTP 状态一起看。

### 成功响应结构

多数方法返回：

```text
{"success": true, "data": <内容>, "meta": {"timestamp": ..., ...}}
```

方法拆出 `data` 的内容返回；整个 `meta` 放进 `last_call['meta']`。

两个例外：

- `GET /api/v1` 直接返回自述对象，没有 `data` / `meta`。
- `GET /api/v1/users` 返回 `{"success": true, "users": [...], "pagination": {...}}`，没有 `data`。

`random_image` 返回图片本身，不是 JSON。

### 失败响应结构

```text
{"success": false, "error": <文本>, "code": <代码>}
```

HTTP 状态与 `code` 大致同步。

### 参数编码

- 查询串是扁平字典。
- `tags` / `ratings` / `exclude_tags` 是逗号分隔**字符串**，如 `'blue archive,1girl'`，不是列表，也不是搜索表达式。
- 布尔编码成小写 `true` / `false`。
- `None` 不发送。
- 没有 `files` 时请求体是 JSON；`ids: []` 这样的显式空数组会照发。

### 分页

- `meta.pagination` 有 `page` / `limit` / `total` / `pages`。
- `has_next` / `has_prev` 只在非空结果分支出现。
- `/api/v1/users` 的两个键都没有。

### ID

- 官方图片路由 `images/:id`、`similar`、`batch` 用**内部图片 id**，即响应里的 `id` / `dbid`，字符串形式的自增大整数。
- 公开序号是另一列 `sequential_id`，在响应里叫 `post_id`。
- 两者不可互换。

## 官方 v1：索引、统计、用户目录

### `api_index()`

`GET /api/v1`，**公开**，无参数。

返回整个自述对象，字段：`name`、`version`、`description`、`documentation`、`endpoints`、`authentication`、`rate_limits`。没有 `success` / `data` / `meta`。

`name` 是 `"SerikaART API"`，`version` 是 `"1.0.0"`。

`endpoints` 覆盖七个面：`images`（列表 / 详情 / 删除）、`random`（列表 / 图片字节）、`tags`（列表 / 详情）、`users`（只写单用户路由）、`search`、`upload`、`stats`。它**没有**列 `batch/images`、用户目录和 `trending`；以路由清单为准。

`rate_limits` 只是文档性数据：user `60/min`、premium 与 moderator `120/min`、admin `1000/min`。运行时按 key 自身的限流值执行。

```python
from anybooru import Serika

with Serika('serika') as client:
    info = client.api_index()            # GET https://serika.art/api/v1
    print(info['name'], info['version'])                 # 2026-09-15 实测：SerikaART API 1.0.0
    print(sorted(info['endpoints']))     # ['images', 'random', 'search', 'stats', 'tags', 'upload', 'users']
```

### `stats()`

`GET /api/v1/stats`，**公开**，无参数。返回 `data` 的内容：

| 字段 | 含义 |
| :--- | :--- |
| `totals` | `{"images": ..., "tags": ..., "users": ...}`。`images` 只数公开图；`tags` 与 `users` 是整表计数，**含**用户目录排除掉的占位账号 |
| `images_by_rating` | `{"safe": ..., "questionable": ..., "explicit": ...}` |
| `images_by_type` | `{"ai_generated": ..., "non_ai": ...}` |
| `activity` | `{"uploads_last_24h": ...}`，最近 24 小时上传数 |

2026-09-15 实测：`totals` 为 images **4237843**、tags **730851**、users **3058**；按评级 safe **3499663**、questionable **324774**、explicit **413406**；AI 图 **14195**、非 AI 图 **4223648**、最近 24h 上传 **0**。`last_call['meta']` 里有 `timestamp`，实测 `2026-09-14T22:18:21.628Z`。

```python
from anybooru import Serika

with Serika('serika') as client:
    statistics = client.stats()          # GET https://serika.art/api/v1/stats
    print(sorted(statistics))            # ['activity', 'images_by_rating', 'images_by_type', 'totals']
    print(statistics['totals']['images'])                # 2026-09-15 实测 4237843
    print(client.last_call['meta']['timestamp'])         # 2026-09-15 实测 2026-09-14T22:18:21.628Z
```

### `user_list(page=None, limit=None, q=None, sort=None)`

`GET /api/v1/users`，**公开**。

返回响应里的 `users` 数组；分页在 `last_call['meta']['pagination']`，只有 `page` / `limit` / `total` / `pages`。

每项都是 camelCase：`_id` 与 `id`（同一个账号 id 字符串的两个名字）、`username`、`avatarUrl`、`rank`、`createdAt`、`uploadCount`（只数公开图）。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | int | 页码 | 服务端取 `1`；`<1` 抬到 1 | `page=2` |
| `limit` | int，1..100 | 每页用户数 | 服务端取 `50` | `limit=1` |
| `q` | str | 用户名子串，不区分大小写 | 不过滤 | `q='gir'` |
| `sort` | `newest` / `oldest` / `alphabetical` / `alphabetical-reverse` / `uploads` / `uploads-asc` | 排序；`uploads` 按公开图数降序 | 服务端取 `newest`，即 `created_at` 降序；其它值也按 `newest` | `sort='uploads'` |

`^user_[A-Za-z0-9]{6}$` 形式的自动占位账号被服务端排除，所以 `total` 可以小于 `stats()['totals']['users']`。2026-09-15 实测两者恰好都是 3058；不能推断它们每次必定不同。

```python
from anybooru import Serika

with Serika('serika') as client:
    users = client.user_list(page=1, limit=1, sort='newest')
    # GET https://serika.art/api/v1/users?page=1&limit=1&sort=newest
    print(users[0]['username'], users[0]['uploadCount'])       # 2026-09-15 实测：Giru 与公开图数
    print(client.last_call['meta']['pagination'])              # {'page': 1, 'limit': 1, 'total': 3058, 'pages': 3058}
```

### `user_show(identifier)`

`GET /api/v1/users/:identifier`，需要 `users:read` 权限的 key；匿名访问是 `401`。**未执行。**

`identifier` 先按账号 id（文本主键）精确匹配，再退回不区分大小写的用户名匹配；都查不到是 `404 NOT_FOUND`。

返回 `data`：`{id, username, avatar_url, rank, stats, created_at}`。`stats` 是 `{images, total_upvotes, total_views}`，只统计该用户名下的图片表行，不过滤已删除 / 未列出。

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    user = client.user_show('Giru')      # GET https://serika.art/api/v1/users/Giru
    print(user['username'], user['stats']['images'], user['rank'])
```

## 官方 v1：图片

权限：`image_list`、`image_show`、`image_similar`、`image_batch` 都要 `images:read`；`image_delete` 要 `images:delete`，发 key 时只有 admin / owner 能拿到这个权限位。

五条路由的成功路径**全部未执行**：`image_list` 与 `image_show` 有匿名 `401` 的历史记录；其余三条只有源码依据。

下面所有 `image_id`、`ids` 都是**内部图片 id**，对应服务端 `WHERE i.id = ...`，不是公开序号 `post_id`。

### `image_list(page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, q=None, user_id=None, min_width=None, min_height=None)`

`GET /api/v1/images`，需要 `images:read`。**未执行。**

返回 `data` 是图片数组；`meta.pagination` 带 `page` / `limit` / `total` / `pages`，非空分支才有 `has_next` / `has_prev`。标签全部解析不到时 `total: 0`、`pages: 0`。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | int | 页码 | 服务端取 `1`；`<1` 抬到 1 | `page=2` |
| `limit` | int，1..100 | 每页图片数 | 服务端取 `20` | `limit=24` |
| `tags` | str，逗号分隔标签名 | **交集**：图片必须同时带全部标签 | 不筛标签 | `tags='blue archive,1girl'` |
| `ratings` | str，逗号分隔 `safe` / `questionable` / `explicit` | 评级过滤 | 回退为只看 `safe`；非法值被剔除，剔除后为空也回退 `safe`；三个全给则不加评级条件 | `ratings='safe,questionable'` |
| `sort` | `newest` / `oldest` / `popular` / `favorites` / `views` / `random` | `popular` 是 upvotes 降序再 views 降序；`random` 不确定 | 服务端取 `newest`，即 `created_at` 降序；其它值也按 `newest` | `sort='popular'` |
| `ai` | bool | 只要 AI 生成图 | 不筛 | `ai=True` |
| `q` | str | 子串匹配标签名、`description`、上传者用户名 | 不筛 | `q='genshin'` |
| `user_id` | str，上传者的账号 id | 按上传者过滤 | 不筛 | `user_id='<形如 692ad0df032c62f79b57a08d 的账号 id，取自 user_list 的 id>'` |
| `min_width` | int | 最小宽度，单位像素 | 不筛；只有 `>0` 才生效 | `min_width=1920` |
| `min_height` | int | 最小高度，单位像素 | 不筛；只有 `>0` 才生效 | `min_height=1080` |

未知标签分支：

- **部分**名字解析不到，返回 `404` `TAG_NOT_FOUND`。同一个名字在列表里重复也算缺失，因为每个名字只查回一行。
- **全部**解析不到，或标签都存在但没有图，返回 `200` 加空 `data`。

每项图片字段：`id` / `dbid`（内部 id 的字符串）、`post_id`（即 `sequential_id`）、`url`、`thumbnail_url`、`width`、`height`、`file_size`、`content_type`、`rating`、`is_ai_generated`、`source`、`description`、`tags`（`[{"name", "type"}]`，**不带** `shared_tags`）、`stats`（`upvotes` / `downvotes` / `favorites` / `views`）、`user`（`{id, username}`，`id` 可以是 `null`；没有用户名时使用字符串 `"Anonymous"`）、`created_at`、`updated_at`。

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    images = client.image_list(page=1, limit=3, tags='blue archive', ratings='safe', sort='popular')
    # GET https://serika.art/api/v1/images?page=1&limit=3&tags=blue+archive&ratings=safe&sort=popular
    print(images[0]['id'], images[0]['post_id'], images[0]['stats']['upvotes'])
    print(client.last_call['meta']['pagination'])        # page / limit / total / pages / has_next / has_prev
```

### `image_show(image_id)`

`GET /api/v1/images/:image_id`，需要 `images:read`。**未执行。**

给一张图的**内部 id**。非数字是 `400 INVALID_ID`；不存在是 `404 NOT_FOUND`。

返回 `data` 是完整一行：列表那些字段之外，还有 `original_filename`、`source`、`description`、`stats.score`（upvotes 减 downvotes）、`stats.comments`（评论数）、`updated_at`。

副作用：每次成功调用让这张图的 `views` 加一。

这条路由**不加** `deleted` / `unlisted` 与评级条件；软删或未列出的图按 id 照样能取到。

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    image = client.image_show(7323837)   # GET https://serika.art/api/v1/images/7323837
    print(image['post_id'], image['original_filename'], image['stats']['score'], image['stats']['comments'])
```

### `image_similar(image_id, limit=None)`

`GET /api/v1/images/:image_id/similar`，需要 `images:read`。**未执行。**

源图必须是公开图，即 `deleted = FALSE AND unlisted = FALSE`，否则 `404 NOT_FOUND`。

返回 `{"source_id": <路径段原文>, "similar": [...], "count": <数量>}`。

候选只取与源图**同评级**的公开图，按共享标签数降序，再按 upvotes 降序。

每项含 `id` / `dbid`、`post_id`、`sequential_id`、`url`、`thumbnail_url`、`width`、`height`、`rating`、`is_ai_generated`、`shared_tags`（共享标签个数）、最多 10 个 `tags`、`stats`（没有 `score` / `comments`）。

没有相似图不是错误：`similar` 是空数组，`count` 是 0。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | int | 源图的**内部图片 id** | 必填 | `7323837` |
| `limit` | int，1..50 | 返回多少张相似图 | 服务端取 `10` | `limit=5` |

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    similar = client.image_similar(7323837, limit=5)   # GET https://serika.art/api/v1/images/7323837/similar?limit=5
    print(similar['count'], similar['similar'][0]['shared_tags'])
```

### `image_batch(ids)`

`POST /api/v1/batch/images`，需要 `images:read`。**未执行**；官方文档页没有收录这个动词。

`ids` 走 JSON 请求体 `{"ids": [...]}`，不是查询串。

返回 `{"images": [...], "found": <命中数>, "requested": <请求数>}`；命中项按请求顺序排列。

每项和 `image_list` 的图片项同构，但额外有 `sequential_id`；匿名上传者的 `user` 是 `null`，不是 `"Anonymous"`。

和 `image_show` 一样，这条路由不筛 `deleted` / `unlisted`，不加评级条件。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `ids` | list，整数或数字字符串，最多 100 个 | 要批量取回的**内部图片 id** | 必填。空或非数组 `400 INVALID_REQUEST`；超 100 个 `400 TOO_MANY_IDS`；全部解析不成整数 `400 INVALID_IDS` | `[7323837, 7323836]` |

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    batch = client.image_batch([7323837, 7323836])   # POST https://serika.art/api/v1/batch/images
    print(batch['found'], batch['requested'], len(batch['images']))
```

### `image_delete(image_id)`

`DELETE /api/v1/images/:image_id`，需要 `images:delete`；发 key 时只授予 admin / owner。**写操作，未执行。**

给**内部图片 id**。非数字是 `400 INVALID_ID`；不存在是 `404 NOT_FOUND`。

返回 `{"deleted": true, "id": "<内部 id>"}`。

服务端在一个事务里删掉这张图的 `votes`、`favorites`、`comments`、`image_tags` 与 `images` 行，并把受影响标签的 `count` 减一。

不属自己、rank 又不是 `admin` / `owner` 时是 `403 FORBIDDEN`；这是官方面唯一给 `FORBIDDEN` 的分支。匿名上传（`user_id` 为 `NULL`）的图没有属主，这一项校验会被跳过。

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    result = client.image_delete(7323837)   # DELETE https://serika.art/api/v1/images/7323837
    print(result['deleted'], result['id'])  # 返回 {"deleted": true, "id": "7323837"}
```

## 官方 v1：随机

### `random_image(width, height, fit=None, format=None, quality=None, tags=None, ratings=None, exclude_tags=None, blur=None, grayscale=None, ai=None, no_ai=None, match_size=None, aspect_tolerance=None)`

`GET /api/v1/random/:width/:height/image.png`，**公开**，是四个公开路由之一。

返回图片字节，Python 类型是 `bytes`。`last_call['headers']` 里有 `Content-Type`，以及命中时才带的 `X-Image-Id` / `X-DBID`（内部 id）、`X-Post-Id`（公开序号）、`X-Original-Width` / `X-Original-Height` / `X-Rating`。

这条地址也是浏览器 `<img src>` 直接可用的。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `width` | int，16..8000 | 输出宽度，单位像素，走路径段 | 必填；越界或非数字是 `400` 加**纯文本**正文 | `400` |
| `height` | int，16..8000 | 输出高度，单位像素，走路径段 | 必填；同上 | `400` |
| `fit` | `cover` / `contain` / `fill` / `inside` / `outside` | 缩放方式 | 服务端取 `cover`；其它值也按 `cover` | `fit='cover'` |
| `format` | `png` / `jpeg` / `jpg` / `webp` | 输出格式 | 服务端取 `png`；其它值也输出 PNG | `format='png'` |
| `quality` | int，1..100 | 输出质量 | 服务端取 `85`。文档说只对 jpeg / webp 生效，控制器对 PNG 也传了它；PNG 的 `quality` 要配 palette 才生效，差异未实测 | `quality=90` |
| `tags` | str，逗号分隔标签名 | 希望图带这些标签 | 不筛 | `tags='blue archive'` |
| `ratings` | str，逗号分隔评级 | 评级过滤 | 回退为只看 `safe` | `ratings='safe'` |
| `exclude_tags` | str，逗号分隔标签名 | 排除带这些标签的图 | 不排除 | `exclude_tags='guys'` |
| `blur` | bool | 高斯模糊，σ≈10 | 不模糊 | `blur=True` |
| `grayscale` | bool | 转灰度 | 不变 | `grayscale=True` |
| `ai` | bool | 只要 AI 生成图 | 不筛；与 `no_ai` 同时给时 `ai` 优先 | `ai=False` |
| `no_ai` | bool | 排除 AI 生成图 | 不筛 | `no_ai=True` |
| `match_size` | bool | 优先挑不小于请求尺寸、且宽高比在 `aspect_tolerance` 内的图；候选下限取 `min(请求尺寸, 400)` | 直接随机 | `match_size=True` |
| `aspect_tolerance` | float | 宽高比容差 | 服务端取 `0.2` | `aspect_tolerance=0.3` |

这条路由从不因为标签报错：只有“每个标签名都存在**且**存在同时带全部标签的图”时才给查询加上标签条件；否则条件被整体丢弃，于是可能返回**不带**这些标签的随机图。

无匹配时服务端仍回 `200`，正文是灰色占位 PNG，`Cache-Control` 带 `stale-while-revalidate`。控制器内部出错（抓源图、缩放失败）也是 `200`，但换成红色占位 PNG 且 `Cache-Control: no-cache`。只有连占位图都生成不出来才是 `500` 纯文本 `Error generating image`。

占位图和命中只能靠 `X-*` 头区分。命中时会给该图的 `views` 加一。

2026-09-15 实测：`random_image(400, 400, fit='cover', format='png', ratings='safe')` 返回 **81224 字节**、`Content-Type: image/png`；头里 `x-image-id` / `x-dbid` 都是 **2796776**、`x-post-id` **1416106**、`x-original-width` **1168**、`x-original-height` **2057**、`x-rating` `safe`。每次调用都可能选到别的图。

```python
from anybooru import Serika

with Serika('serika') as client:
    picture = client.random_image(400, 400, fit='cover', format='png', ratings='safe')
    # GET https://serika.art/api/v1/random/400/400/image.png?fit=cover&format=png&ratings=safe
    print(type(picture).__name__, len(picture), client.last_call['headers']['Content-Type'])
    print(client.last_call['headers'].get('X-Post-Id'))     # 命中才有；占位图是 None
```

### `random_list(count=None, ratings=None, tags=None, exclude_tags=None, min_width=None, min_height=None, max_width=None, max_height=None, ai=None, no_ai=None)`

`GET /api/v1/random`，需要 `random:read` 权限的 key；匿名 `401`。**未执行。**

返回描述随机图的 JSON；`data` 里是图片对象，不是图片字节。

生效的 `count` 是 1 时，`data` 是**单个对象**；否则是数组。命中时 `meta` 另带 `count`（实际返回数）与 `requested`（请求数）。没有匹配时 `data` 是空数组、`meta` 只有 `message`，此时**没有** `count` / `requested`。

排序是 `ORDER BY RANDOM()`，不保证两次请求不同或去重。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `count` | int，1..50 | 要几张 | 服务端取 `1` | `count=3` |
| `ratings` | str，逗号分隔评级 | 评级过滤 | 回退为只看 `safe`；三个全给则不加评级条件 | `ratings='safe'` |
| `tags` | str，逗号分隔标签名 | 交集：图必须带全部标签 | 不筛。**部分**名字不存在是 `404 TAG_NOT_FOUND`；全部不存在或没有交集是 `200` 加空数组与 `message` | `tags='blue archive'` |
| `exclude_tags` | str，逗号分隔标签名 | 命中其中一个就排除 | 不排除；未知名字在这里被忽略，不报错 | `exclude_tags='guys'` |
| `min_width` / `min_height` | int | 最小宽 / 高 | 不筛；只有 `>0` 才生效 | `min_width=1920` |
| `max_width` / `max_height` | int | 最大宽 / 高 | 不筛；只有 `>0` 才生效 | `max_width=4000` |
| `ai` | bool | 只要 AI 生成图 | 不筛；与 `no_ai` 同时给时 `ai` 优先 | `ai=True` |
| `no_ai` | bool | 排除 AI 生成图 | 不筛 | `no_ai=True` |

每项字段与 `image_list` 的图片项相同：`id` / `dbid`、`post_id`、`url`、`thumbnail_url`、`width`、`height`、`file_size`、`content_type`、`rating`、`is_ai_generated`、`source`、`description`、`tags`、`stats`、`user`、`created_at`。

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    picked = client.random_list(count=2, ratings='safe', min_width=1920)
    # GET https://serika.art/api/v1/random?count=2&ratings=safe&min_width=1920
    print(len(picked), picked[0]['post_id'], client.last_call['meta']['requested'])
```

## 官方 v1：标签

### `tag_list(page=None, limit=None, q=None, type=None, sort=None, min_count=None)`

`GET /api/v1/tags`，需要 `tags:read` 权限的 key；匿名 `401`。**未执行。**

返回 `data` 是标签数组，每项 `[{"id", "name", "type", "count", "created_at"}]`。`meta.pagination` 与图片列表同构，含 `has_next` / `has_prev`。

这里的 `count` 是标签表里存着的计数，删图时会减一；与 `tag_show` 重算出来的值可能不同。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | int | 页码 | 服务端取 `1`；`<1` 抬到 1 | `page=1` |
| `limit` | int，1..500 | 每页标签数 | 服务端取 `100` | `limit=5` |
| `q` | str | 标签名子串，不区分大小写 | 不过滤 | `q='blue'` |
| `type` | `general` / `artist` / `character` / `copyright` / `meta` | 标签类型 | 不筛类型；其它值被服务端静默忽略，等于不筛 | `type='artist'` |
| `sort` | `count` / `name` / `newest` / `oldest` | 排序 | 服务端取 `count`，即计数降序；其它值也按 `count` | `sort='count'` |
| `min_count` | int | 使用计数下限 | 不筛；只有 `>0` 才生效 | `min_count=1000000` |

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    tags = client.tag_list(page=1, limit=5, type='artist', sort='count')
    # GET https://serika.art/api/v1/tags?page=1&limit=5&type=artist&sort=count
    print([(tag['name'], tag['count']) for tag in tags])
```

### `tag_show(name)`

`GET /api/v1/tags/:name`，需要 `tags:read`。**未执行**；官方文档页没有收录。

`name` 由服务端 `toLowerCase().trim()` 后精确匹配；不存在是 `404 NOT_FOUND`。

返回 `{id, name, type, count, created_at, sample_images}`。

`count` 是**重算**的公开图计数。`sample_images` 最多 5 项，都是 `safe` 且公开的图，字段为 `{id, thumbnail_url, rating}`，按 upvotes 从高到低排列。`thumbnail_url` 为空时，使用该图片的 `url`。

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    tag = client.tag_show('blue archive')   # GET https://serika.art/api/v1/tags/blue%20archive
    print(tag['name'], tag['count'], len(tag['sample_images']))
```

## 官方 v1：搜索与热门

### `search(q, type=None, limit=None, ratings=None)`

`GET /api/v1/search`，需要 `images:read`。**未执行**；官方文档页没有收录。

一次搜图片 / 标签 / 用户。返回 `{"images": [...], "tags": [...], "users": [...]}`，**只含被请求的分支**；`meta` 回显 `query` 与 `type`。

图片段命中条件是“标签名含 `q`”或 `description` / 上传者用户名含 `q`”，按 upvotes 降序。每项只有 `id` / `dbid` / `post_id` / `url` / `thumbnail_url` / `width` / `height` / `rating` / 最多 5 个标签名 / `stats{upvotes, views}`。

标签段是 `{id, name, type, count}`。用户段是 `{id, username, avatar_url, rank}`。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `q` | str，至少 2 个字符 | 查询词 | 必填；少于 2 个字符是 `400 INVALID_QUERY` | `q='blue archive'` |
| `type` | `all` / `images` / `tags` / `users` | 搜哪一段 | 服务端取 `all`；其它值一个分支都不跑，返回空对象 `{}` | `type='images'` |
| `limit` | int，1..50 | 每段返回多少条 | 服务端取 `10` | `limit=3` |
| `ratings` | str，逗号分隔评级 | 只影响图片段 | 图片段回退为只看 `safe` | `ratings='safe'` |

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    found = client.search('blue archive', type='images', limit=3)
    # GET https://serika.art/api/v1/search?q=blue+archive&type=images&limit=3
    print(sorted(found), found['images'][0]['post_id'])
```

### `trending(period=None, limit=None, ratings=None)`

`GET /api/v1/trending`，需要 `images:read`。**未执行**；官方文档页没有收录。

返回 `{"period", "images", "tags"}`。

图片按热度分 `upvotes * 3 + favorites * 5 + views * 0.1` 降序；每项带 `trend_score`（取整）、最多 5 个标签名、`uploaded_at`（即 `created_at`）。

`tags` 是这批图里出现最多的标签，最多 20 条，字段为 `id` / `name` / `type` / `trending_count` / `total_count`；**不受 `limit` 影响**。

没有结果时返回 `{"period": ..., "images": [], "tags": []}`。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `period` | `day` / `week` / `month` | 统计窗口，对应 24 小时 / 7 天 / 30 天 | 服务端取 `day`；其它值也按 `day` | `period='week'` |
| `limit` | int，1..50 | 返回多少张图 | 服务端取 `20` | `limit=5` |
| `ratings` | str，逗号分隔评级 | 评级过滤 | 回退为只看 `safe`；三个全给则不加评级条件 | `ratings='safe,questionable'` |

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    hot = client.trending(period='week', limit=5)
    # GET https://serika.art/api/v1/trending?period=week&limit=5
    print(hot['period'], len(hot['images']), [tag['name'] for tag in hot['tags'][:3]])
```

## 官方 v1：上传

### `upload(file, tags, rating, is_ai_generated=None, source=None, description=None)`

`POST /api/v1/upload`，需要 `upload` 权限；发 key 时只授予 moderator / admin / owner。**写操作，未执行。**

这是唯一发 multipart 请求体的端点：`file` 与其他字段都是表单字段。

服务端存下原图与一张 320x320 JPEG 缩略图，复用或新建标签行，并从计数器领取下一个公开序号。

返回新图对象：`id` / `dbid`、`post_id`、`url`、`thumbnail_url`、`width`、`height`、`file_size`、`content_type`、`rating`、`is_ai_generated`、`tags`、`created_at`。`meta.message` 是 `"Image uploaded successfully"`。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `file` | requests 的 `(文件名, 文件对象, MIME)` 三元组 | 要上传的图片 | 必填。只收 `image/jpeg` / `image/png` / `image/gif` / `image/webp` 且 ≤ 50MB。缺失 `400 MISSING_FILE`；类型不对 `INVALID_FILE_TYPE`；过大 `FILE_TOO_LARGE` | `('sample.png', picture, 'image/png')` |
| `tags` | str | 标签，原样发送 | 必填。服务端两种格式都吃：JSON 数组文本（`[{"name": "nature", "type": "general"}]` 或纯字符串数组）或逗号分隔。空是 `400 MISSING_TAGS`；超 100 个是 `TOO_MANY_TAGS`；未知 `type` 回落 `general` | `'1girl, solo'` |
| `rating` | `safe` / `questionable` / `explicit` | 评级 | 必填；其它值 `400 INVALID_RATING` | `'safe'` |
| `is_ai_generated` | bool | 标记为 AI 生成 | 不标记。服务端拿表单值跟字符串 `'true'` 比较，只有编码成小写字符串才生效；控制器还接受 `isAIGenerated` 拼写，本客户端不发 | `True` |
| `source` | str | 原始来源地址 | 不发送 | `'https://example.com/original'` |
| `description` | str | 图片描述 | 不发送 | `'示例描述'` |

`file` **必须**写成三元组并显式给 MIME。裸文件对象不带 part 的 `Content-Type`，会被服务端读成 `application/octet-stream` 并拒绝。文件对象的关闭由调用方负责。

```python
from anybooru import Serika

with Serika('serika', api_key='sk_serika_xxx') as client:
    with open('sample.png', 'rb') as picture:            # 本地待上传文件，只读不写
        # POST https://serika.art/api/v1/upload（multipart 表单，文件字段名是 file）
        image = client.upload(('sample.png', picture, 'image/png'),
                              tags='1girl, solo', rating='safe')
    print(image['post_id'], image['url'], client.last_call['meta']['message'])
```

## 站内匿名读：共同模式

站内面路径以 `api/` 开头，**没有 `.json` 后缀**，也不接受 Danbooru / Moebooru 那种格式后缀。动词由各控制器自己决定，其中两个是 POST 只读查询。

共同点：

- **返回整个 JSON**：成功是 `{"success": true, ...}` 加各自资源键（`images`、`image`、`comments`、`tags`、`tag`、`artists`、`artist`、`wiki`、`reviews`、`user`）；分页就在返回体里。失败是 `{"success": false, "error": ..., "code": ...}`；非 2xx 一样抛 `AnybooruHTTPError`。
- **参数是扁平字典**，服务端字段名大小写敏感：`hide_ai=` 线上是 `hideAI=`，`user_id=` 线上是 `userId=`，`query=` 线上是 `q=`。`tags` / `ratings` 同样是逗号分隔字符串；布尔按小写 `true` / `false` 发送，服务端写的是 `=== 'true'`。
- **不传就是不传**：库不会把 `None` 补成服务端默认值；默认值、钳位与回落都由服务端决定。
- **ID**：站内图片详情与评论用**公开序号**，即列表响应里的 `post_id` / `sequential_id`。官方 v1 图片路由与列表数据里的 `id` / `dbid` 是内部 id。两者不可互换。
- 站内面没有游标分页，翻页一律是页码。

## 站内：图片

### `internal_image_list(*, page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, hide_ai=None, query=None, user_id=None, username=None)`

`GET /api/images`，匿名可读，**已实测**（2026-09-15 返回 `200`）。

返回整个响应：

```text
{"success": true, "images": [...], "pagination": {page, limit, total, pages, has_next}}
```

每个图片项同时给数据库名与前端别名：`id` / `dbid` / `_id`（内部 id，后两个是字符串）、`sequential_id` / `post_id` / `sequentialId`（公开序号）、`user_id` / `userId`、`username`、`url`、`thumbnail_url` / `thumbnailUrl`、`width`、`height`、`file_size` / `fileSize`、`rating`、`is_ai_generated` / `isAIGenerated`、`upvotes`、`downvotes`、`favorites`、`views`、`created_at` / `createdAt`、`tags`（`[{"_id", "id", "name", "type", "count"}]`）。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | int | 页码 | 服务端取 `1` | `page=1` |
| `limit` | int，最大 100 | 每页图片数 | 服务端取 `24`；只在超过 100 时被钳住 | `limit=3` |
| `tags` | str，逗号分隔标签名 | 交集：图必须带全部标签 | 不筛。部分名字解析不到是 `404 TAG_NOT_FOUND`；一个都没解析到是 `200` 加空列表 | `tags='highres,1girl'` |
| `ratings` | str，逗号分隔 `safe` / `questionable` / `explicit` | 评级过滤 | 空或全非法回落为只看 `safe`；三个全给则不加评级条件 | `ratings='safe'` |
| `sort` | `newest`（回落）/ `popular` / `favorites` / `views` / `oldest` / `filesize` / `filesize-asc` / `resolution` / `aspectratio` / `alphabetical` / `alphabetical-reverse` / `random` | 排序 | 服务端取 `newest`；未知值不报错，按回落处理 | `sort='newest'` |
| `ai` | bool | `True` 只要 AI 生成图 | 不筛 | `ai=False` |
| `hide_ai` | bool | `True` 排除 AI 生成图 | 不筛；与 `ai=True` 同时给会互相抵消成空结果 | `hide_ai=True` |
| `query` | str | 子串匹配 `description`、上传者用户名、标签名，不区分大小写 | 不筛 | `query='genshin'` |
| `user_id` | str，上传者账号 id | 按上传者过滤 | 不筛；字面量 `'null'` 表示“上传者为空，即匿名上传” | `user_id='null'` |
| `username` | str | 上传者用户名，不区分大小写 | 不筛；**优先级高于 `user_id`** | `username='Giru'` |

未知标签分支同时受服务端标签缓存影响：标签 id 缓存 5 分钟、计数缓存 10 分钟。名字先查缓存，缓存没命中的才批量查库。全部名字都不存在时是 `200` 加空 `images` 与 `total: 0`；只有已经解析出至少一个标签 id 时才是 `404` 加 `code: "TAG_NOT_FOUND"`。所以同一个请求在缓存前后可能给出不同结果。

2026-09-15 实测 `internal_image_list(page=1, limit=3, ratings='safe', sort='newest')`：3 张 `safe` 图，内部 id **7323837 / 7323836 / 7323835**，对应 `post_id` **4237836 / 4237835 / 4237834**；`pagination` 为 `total=3499663`、`pages=1166555`、`has_next=true`。

```python
from anybooru import Serika

with Serika('serika') as client:
    listing = client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')
    # GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest
    print(listing['pagination'])
    print([(image['id'], image['post_id']) for image in listing['images']])
    # 2026-09-15 实测 [(7323837, 4237836), (7323836, 4237835), (7323835, 4237834)]
```

### `internal_image_show(image_id)`

`GET /api/images/:image_id`，匿名可读，**已实测**（`200`）。

路径段是**公开序号 `post_id`**；非数字是 `400`。

返回 `{"success": true, "image": {...}}`。除列表那些别名外，还多 `original_filename` / `originalFilename`、`file_size`、`content_type` / `contentType`、`source`、`description`、`deleted`、`unlisted`、删除与未列出的审计列、`updated_at` / `updatedAt`。

读一张可见的图会让服务端的 `views` 自增；响应里的 `views` 是加一后的值。这是站点自己的计数器，不是调用方的会话写操作。

匿名看不到已删除 / 未列出的图：这些图和真的不存在的 id 一样答 `404` 加 `{"success": false, "error": "Image not found"}`，两者无法区分。

2026-09-15 实测 `internal_image_show(4237836)`：返回内部 id **7323837**、`post_id` **4237836**、`rating` `safe`；`url` 与列表首图相同。

```python
from anybooru import Serika

with Serika('serika') as client:
    detail = client.internal_image_show(4237836)['image']
    # GET https://serika.art/api/images/4237836
    print(detail['id'], detail['post_id'], detail['rating'], detail['url'])
    # 2026-09-15 实测：7323837 4237836 safe https://cdn.serika.art/uploads/1788013605888-1788013605888-1q2b2g-danbooru-12074741.png
```

### `internal_image_comments(image_id)`

`GET /api/images/:image_id/comments`，匿名可读，仅源码对齐，未发过请求。

路径段是**公开序号**；图不存在是 `404`。

返回 `{"success": true, "comments": [...]}`，按创建时间升序。每行含 `_id`（评论自己的行 id 字符串）、`imageId`（**内部 id** 的字符串）、`userId`（账号 id）、`username`、`avatarUrl`、`rank`（缺失时是 `user`）、`content`、`parentId`（字符串，顶层评论没有这个键）、`asArtist`、`artistTagName`（只有以画师身份评论时才有）、`createdAt` / `updatedAt`。

```python
from anybooru import Serika

with Serika('serika') as client:
    comments = client.internal_image_comments(4237836)['comments']
    # GET https://serika.art/api/images/4237836/comments
    print(len(comments))                                     # 这张图没有评论时是 0
    if comments:
        print(comments[0]['username'], comments[0]['content'])
```

## 站内：标签

### `internal_tag_list(*, query=None, limit=None, type=None)`

`GET /api/tags`，匿名可读，**已实测**（`200`）。

返回 `{"success": true, "tags": [...], "grouped": {...}}`。`tags` 按使用计数降序，每行是标签表的整行：`id`、`name`、`type`、`count`、`created_at`。`grouped` 是同一批行按 `type` 分桶。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | str | 标签名子串，不区分大小写 | 不过滤 | `query='blue'` |
| `limit` | int | 返回行数 | 服务端取 `50`，**没有上限钳位** | `limit=3` |
| `type` | `general` / `artist` / `character` / `copyright` / `meta` | 标签类型 | 不筛类型；其它值被服务端静默忽略 | `type='character'` |

2026-09-15 实测 `internal_tag_list(limit=3)`：`highres: 3402288`、`1girl: 3223922`、`solo: 2597729`。

```python
from anybooru import Serika

with Serika('serika') as client:
    tags = client.internal_tag_list(limit=3)['tags']
    # GET https://serika.art/api/tags?limit=3
    print([(tag['name'], tag['count']) for tag in tags])
    # 2026-09-15 实测 [('highres', 3402288), ('1girl', 3223922), ('solo', 2597729)]
```

### `internal_tag_show(name)`

`GET /api/tags/:name`，匿名可读，仅源码对齐。

服务端会拿原名、空格换下划线、下划线换空格三种形态，都转小写后各试一次，所以 `blue archive` 与 `blue_archive` 都能命中；都没命中是 `404`。

返回 `{"success": true, "tag": {"_id", "id", "name", "type", "count", "createdAt"}}`；`_id` 是 `id` 的字符串形式。

```python
from anybooru import Serika

with Serika('serika') as client:
    tag = client.internal_tag_show('highres')['tag']
    # GET https://serika.art/api/tags/highres
    print(tag['name'], tag['type'], tag['count'])       # 2026-09-15 标签列表里 highres 计数 3402288
```

### `internal_tag_autocomplete(query, *, limit=None)`

`POST /api/tags`，匿名可读，**只读查询不是写接口**：这个 POST 只查标签表与缓存，不看会话；请求体是 JSON。

返回 `{"success": true, "suggestions": [...]}`。每条是一个标签行。排序权重是“完全相等 > 前缀 > 词边界 > 使用计数”；返回前会去掉内部 `score` 字段。结果缓存 120 秒。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | str | 已输入的前缀或片段 | 必填；缺失或不是字符串时服务端返回 `200` 加空 `suggestions`，**不报错** | `'blue arch'` |
| `limit` | int，1..50 | 返回多少条建议 | 服务端取 `10` | `limit=5` |

```python
from anybooru import Serika

with Serika('serika') as client:
    suggestions = client.internal_tag_autocomplete('blue arch', limit=5)['suggestions']
    # POST https://serika.art/api/tags，JSON 体 {"query": "blue arch", "limit": 5}
    print([(item['name'], item['type']) for item in suggestions])
```

### `internal_tag_complementary(tag)`

`POST /api/tags/complementary`，匿名可读，同样是只读的 POST，请求体是 JSON。

返回 `{"success": true, "suggestions": [{"name", "type", "count"}]}`，**最多 3 条**。

命中一张约二十条的硬编码关系表（常见的版权 / 角色 / 普通标签）时，给出表里的名字；库里还没有该标签行的名字补成 `{"name": ..., "type": "general", "count": 0}`。否则用共现统计找最常一起出现的 3 个标签。源标签在库里不存在时返回空数组。

`tag` 由服务端转小写并去空格；缺失是 `400`。

```python
from anybooru import Serika

with Serika('serika') as client:
    paired = client.internal_tag_complementary('blue archive')['suggestions']
    # POST https://serika.art/api/tags/complementary，JSON 体 {"tag": "blue archive"}
    print([(item['name'], item['count']) for item in paired])
```

## 站内：画师

### `internal_artist_list(*, page=None, limit=None)`

`GET /api/artists`，匿名可读，**已实测**（`200`）。

返回 `{"success": true, "artists": [...], "pagination": {page, limit, total, pages}}`。这套分页**没有** `has_next`。列表按画师标签的使用计数降序。

每行有 `_id` 与 `tagId`（都是字符串）、`tagName`、`claimedByUserId`、`claimedByUsername`、`verified`、`avatarUrl`、`bannerUrl`、`bio`、`socials`、`postCount`（取自标签的 `count`）、`createdAt`。

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | int | 页码 | 服务端取 `1` | `page=1` |
| `limit` | int，最大 100 | 每页画师数 | 服务端取 `50`；只在超过 100 时被钳住 | `limit=3` |

2026-09-15 实测 `internal_artist_list(page=1, limit=3)`：`dairi: 17186`、`inoino: 4265`、`nyantcha: 2785`。

```python
from anybooru import Serika

with Serika('serika') as client:
    artists = client.internal_artist_list(page=1, limit=3)['artists']
    # GET https://serika.art/api/artists?page=1&limit=3
    print([(artist['tagName'], artist['postCount']) for artist in artists])
    # 2026-09-15 实测 [('dairi', 17186), ('inoino', 4265), ('nyantcha', 2785)]
```

### `internal_artist_show(tag_name)`

`GET /api/artists/:tagName`，匿名可读，仅源码对齐。

路径参数是**画师标签名**，空格 / 下划线变体都接受。标签的 `type` 必须是 `artist`，否则 `404` `Artist not found`。

返回：

```text
{
  "success": true,
  "tag": {"_id", "id", "name", "type", "count"},
  "artist": {...} | null,
  "reviews": {"count", "averages": {"trust", "quality", "communication", "pricing"}}
}
```

`artist` 是画师资料行：`_id` / `tagId` 字符串、`tagName`、认领与验证字段、`avatarUrl`、`bannerUrl`、`bio`、`socials`、`createdAt`。标签存在但还没有资料行时是 `null`。

`averages.pricing` 在没人打这项分时是 `null`；其余平均分在没有任何评价时是 `0`。

```python
from anybooru import Serika

with Serika('serika') as client:
    artist_page = client.internal_artist_show('dairi')
    # GET https://serika.art/api/artists/dairi
    print(artist_page['tag']['name'], artist_page['reviews']['count'])
    print(artist_page['artist']['tagName'] if artist_page['artist'] else '还没有资料行')
```

### `internal_artist_wiki(tag_name)`

`GET /api/artists/:tagName/wiki`，匿名可读，仅源码对齐。

返回 `{"success": true, "wiki": {...} | null}`。`wiki` 含 `content`、`infobox`（自由结构）、`lastEditedBy`（编辑者用户名）、`lastEditedAt`、`editCount`。服务端只存最近 50 条历史，`editCount` 就是该历史长度。

画师还没有 wiki 时是 `null`；画师标签本身不存在是 `404`。

```python
from anybooru import Serika

with Serika('serika') as client:
    wiki = client.internal_artist_wiki('dairi')['wiki']
    # GET https://serika.art/api/artists/dairi/wiki
    if wiki is None:
        print('这个画师还没有 wiki')
    else:
        print(wiki['lastEditedBy'], wiki['editCount'])
```

### `internal_artist_reviews(tag_name)`

`GET /api/artists/:tagName/reviews`，匿名可读，仅源码对齐。

返回 `{"success": true, "reviews": [...]}`，按创建时间降序，最新的在前。

每行有 `_id`（字符串）、`userId`（账号 id，不是公开序号）、`username`、`ratings`（`trust` / `quality` / `communication` 必有，`pricing` 可选，每项 1..5）、`comment`（可以是 `null`）、`createdAt`。画师标签不存在是 `404`。

```python
from anybooru import Serika

with Serika('serika') as client:
    reviews = client.internal_artist_reviews('dairi')['reviews']
    # GET https://serika.art/api/artists/dairi/reviews
    print(len(reviews))                                      # 没有评价时是 0
    if reviews:
        print(reviews[0]['username'], reviews[0]['ratings'])
```

## 站内：用户

### `internal_user_list(username)`

`GET /api/users?username=`，匿名可读，仅源码对齐。

注意：集合路径实际是“按用户名查单个用户”。`username` 必填，缺失是 `400`；没有“列出全部用户”的模式。

服务端只查本地 `users` 表，不区分大小写，**不向账号服务回退**；查不到就是 `404`。

返回 `{"success": true, "user": {...}}`，含 `id`（账号 id 字符串）、`username`、`avatarUrl`、`bannerUrl`、`rank`、`createdAt`、`isPremium`、`isVerified`。

其中 `bannerUrl`、`isPremium`、`isVerified` 靠服务端用内部 service key 调账号服务补齐，超时 5 秒，失败就静默降级。这三个可能是空或 `false`，按“尽力而为”理解。

```python
from anybooru import Serika

with Serika('serika') as client:
    user = client.internal_user_list('Giru')['user']
    # GET https://serika.art/api/users?username=Giru
    print(user['username'], user['rank'], user['avatarUrl'])
```

### `internal_user_show(user_id)`

`GET /api/users/:id`，匿名可读，仅源码对齐。

路径参数是**账号 id**，即 `users.id`，文本主键，形如 `692ad0df032c62f79b57a08d`；不是用户名，也不是公开序号。

返回 `{"success": true, "user": {id, username, avatarUrl, rank, createdAt}}`。

本地有这行就直接返回。本地没有时，服务端带内部 service key 去账号服务要，把结果写进本地 `users` 表再返回，写法是 `ON CONFLICT (id) DO UPDATE`。这个写入是服务端在镜像自己的账号服务，不需要调用方会话；方法本身仍是匿名读。账号服务也不认识这个 id 时是 `404`。

```python
from anybooru import Serika

with Serika('serika') as client:
    account_id = client.internal_user_list('Giru')['user']['id']
    # GET https://serika.art/api/users?username=Giru（上一步取到账号 id）
    detail = client.internal_user_show(account_id)['user']
    # GET https://serika.art/api/users/<account_id>
    print(detail['id'], detail['username'], detail['createdAt'])
```

### `internal_user_activity(user_id, *, type=None)`

`GET /api/users/:id/activity`，匿名可读，仅源码对齐。

路径参数可以是账号 id，**也可以是用户名**。服务端先按 id 查，查不到再按用户名不区分大小写重查；两者都没有是 `404`。

返回 `{"success": true, "likes": [...], "comments": [...]}`，只含被请求的段；每段最多 50 条，服务端把 `LIMIT 50` 写死。

`likes` 是该用户的点赞（upvote）列表，元素是图片对象，带列表那套别名：`id` / `dbid` / `_id`、`sequential_id` / `sequentialId`、`thumbnailUrl`、`tags` 等。

`comments` 每行有 `_id`、`content`、`createdAt` 和 `image`。`image` 是 `{"sequentialId", "thumbnailUrl"}`；图片行已经消失时是 `null`。

`type` 取 `all`（回落值，两段都返回）、`likes`、`comments`；其它值返回 `{"success": true}` 加两段都没有。

```python
from anybooru import Serika

with Serika('serika') as client:
    activity = client.internal_user_activity('Giru', type='likes')
    # GET https://serika.art/api/users/Giru/activity?type=likes
    print(len(activity['likes']), sorted(activity))           # 只有被请求的段：['likes', 'success']
    if activity['likes']:
        print(activity['likes'][0]['sequential_id'])
```

## 通用入口

没有原生封装的路由，例如将来新增的 v1 动词，直接用 `request()`：

```python
from anybooru import Serika

with Serika('serika') as client:
    body = client.request('GET', 'api/v1/stats')
    # GET https://serika.art/api/v1/stats；保留整个 {"success": true, "data": {...}, "meta": {...}}。
    print(sorted(body))  # ['data', 'meta', 'success']
    statistics = client.request('GET', 'api/v1/stats', envelope='data')
    # GET https://serika.art/api/v1/stats；只返回 data 里的统计信息。
    print(sorted(statistics))  # ['activity', 'images_by_rating', 'images_by_type', 'totals']
```

`request(method, path, *, params=None, data=None, files=None, binary=False, envelope=None)` 的完整说明见[客户端用法](serika.md#通用请求入口)。

`path` 是相对路径，不自动补后缀也不补版本。动态路径段的转义由原生方法负责；通用入口里的完整路径要调用方自己转义。`envelope` 只接受 `'data'` 与 `'users'`，不做形状猜测。

## 错误与状态码

非 2xx 一律抛 `AnybooruHTTPError`。`error.data['code']` 是服务端给的 JSON `code`；正文不是 JSON 时，`data` 是 `None`。

官方 v1 的缺 key / key 缺权限 / 超限分别是 HTTP `401` / `403` / `429`，但三种情况的正文 `code` 都可能是 `UNAUTHORIZED`。只有“删别人的图且 rank 不是 admin / owner”才是 `FORBIDDEN`。判断失败原因要连 HTTP 状态码一起看。

常见 `code`：

- `UNAUTHORIZED`（401 / 403 / 429）
- `INVALID_ID`（400）
- `NOT_FOUND`（404）
- `TAG_NOT_FOUND`（404）
- `INVALID_QUERY`（400）
- `INVALID_REQUEST` / `INVALID_IDS` / `TOO_MANY_IDS`（400）
- `FORBIDDEN`（403，只有删图越权）
- `INTERNAL_ERROR`（500）
- 上传相关：`MISSING_FILE` / `INVALID_FILE_TYPE` / `FILE_TOO_LARGE` / `MISSING_TAGS` / `TOO_MANY_TAGS` / `INVALID_RATING`（400）

站内面失败同样是 `{"success": false, "error": ..., "code": ...}` 加非 2xx 状态码。

## 边界与未实测

- **已实测**（2026-09-15 匿名实跑，命令与真实输出见 [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)）：`api_index`、`stats`、`user_list`、`random_image`、`internal_image_list`、`internal_image_show`、`internal_tag_list`、`internal_artist_list`，共 8 次调用、8 个 HTTP `200`。
- **官方 12 个需 key 的方法成功路径全部未实测**：`image_list`、`image_show`、`image_delete`、`image_similar`、`image_batch`、`random_list`、`tag_list`、`tag_show`、`user_show`、`search`、`trending`、`upload`。用户没有也不申请 key。其中 8 个 GET 另有匿名 `401` 的历史记录；`image_similar`、`image_delete`、`image_batch`、`upload` 四个动词只有源码依据。
- **站内其余 10 个方法只有源码对齐、没发过请求**：`internal_image_comments`、`internal_tag_show`、`internal_tag_autocomplete`、`internal_tag_complementary`、`internal_artist_show`、`internal_artist_wiki`、`internal_artist_reviews`、`internal_user_list`、`internal_user_show`、`internal_user_activity`。
- 本页所有需 key 的片段都写成 `Serika('serika', api_key='sk_serika_xxx')`。`sk_serika_` 是服务端要求的 key 前缀，`xxx` 是占位符，不是可用凭据。把 `sites.serika.api_key` 配成真 key 后，这些片段才可能返回文中字段。
- 自托管部署、认证成功路径、权限与限流、上传与删除、灰色 / 红色占位 PNG 的错误分支、参数组合（含 `match_size`、`aspect_tolerance`、`min_*` / `max_*` 边界）均未实测。逐条状态见[附注的路由清单](serika-contract-notes.md#路由清单与逐条状态)。

继续阅读：[客户端用法](serika.md) · [能力总览](serika-capabilities.md) · [契约审计附注](serika-contract-notes.md) · [错误处理](errors.md) · [线上验证状态](verification.md)。
