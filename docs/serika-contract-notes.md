# Serika 契约审计附注

面向维护者：上游文件与行号、权限过滤器、官方文档与实现的矛盾、SQL 与缓存实现、逐条线上状态、排除项。
面向使用者的三页是 [客户端用法](serika.md)、[方法参考](serika-api.md)、[能力总览](serika-capabilities.md)；
本页只承载那三页没有重复写的源码级细节（方法参数与返回字段在方法参考里），原有事实不删除。

## 来源与版本

- 只读 clone `Serika.art/`，本轮核对 HEAD `ef11dd12`（2026-09-15）；该 clone 未修改、未提交。
- 权威顺序：`app/api/v1/**/route.ts` 与站内 `app/api/**/route.ts` 控制器 + `lib/apiAuth.ts` +
  `lib/contentFilters.ts` **优于**官方文档页 `app/api-docs/endpoints.ts` / `page.tsx`；后者只覆盖
  10 个动词，且在 ID 语义与错误码上与控制器矛盾。
- 官方面自述在 `app/api/v1/route.ts`（`SerikaART API` / `1.0.0`）与 `/api-docs`
  （"All endpoints are versioned under `/api/v1`"）。
- 数据库字段语义来自 `lib/db.ts:387-543`；站内会话来自 `lib/auth.ts:18`（`getCurrentUser()`：
  先读 cookie `session_token`，再读 `Authorization: Bearer`，再向 `accounts.serika.dev` 校验）；
  根 `middleware.ts` 只匹配 `/upload/:path*` 与 `/user/:path*`，**不拦截 `/api/*`**。
- 本库侧实现是 `anybooru/api_serika.py` 的 `SerikaApi_Mixin`（`Serika` 客户端）；
  本页每个方法的 `Serika.request()` 调用就是它对应的路由。
- Serika 自己仓库里对 Danbooru 的 `lib/danbooru.ts:177`（`get('/posts.json')`）是它作为
  Danbooru **消费者**的导入器，不能反推它提供 Danbooru 路由。
- 规模：官方 `app/api/v1/` 是 **15 个 `route.ts` / 16 个导出动词**（`images/[id]/route.ts` 一个文件
  导出 `GET` + `DELETE`）；站内面本库封 **14 个**匿名读方法。

## 方法签名总表（30）

官方 v1（16）：

| 方法 | 实际签名 |
| :--- | :--- |
| `api_index` | `api_index()` |
| `image_list` | `image_list(page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, q=None, user_id=None, min_width=None, min_height=None)` |
| `image_show` | `image_show(image_id)` |
| `image_delete` | `image_delete(image_id)` |
| `image_similar` | `image_similar(image_id, limit=None)` |
| `image_batch` | `image_batch(ids)` |
| `random_list` | `random_list(count=None, ratings=None, tags=None, exclude_tags=None, min_width=None, min_height=None, max_width=None, max_height=None, ai=None, no_ai=None)` |
| `random_image` | `random_image(width, height, fit=None, format=None, quality=None, tags=None, ratings=None, exclude_tags=None, blur=None, grayscale=None, ai=None, no_ai=None, match_size=None, aspect_tolerance=None)` |
| `tag_list` | `tag_list(page=None, limit=None, q=None, type=None, sort=None, min_count=None)` |
| `tag_show` | `tag_show(name)` |
| `user_list` | `user_list(page=None, limit=None, q=None, sort=None)` |
| `user_show` | `user_show(identifier)` |
| `search` | `search(q, type=None, limit=None, ratings=None)` |
| `trending` | `trending(period=None, limit=None, ratings=None)` |
| `stats` | `stats()` |
| `upload` | `upload(file, tags, rating, is_ai_generated=None, source=None, description=None)` |

站内非版本化（14，`*` 之后为仅关键字参数）：

| 方法 | 实际签名 | 路由 |
| :--- | :--- | :--- |
| `internal_image_list` | `internal_image_list(*, page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, hide_ai=None, query=None, user_id=None, username=None)` | `GET /api/images` |
| `internal_image_show` | `internal_image_show(image_id)` | `GET /api/images/:id` |
| `internal_image_comments` | `internal_image_comments(image_id)` | `GET /api/images/:id/comments` |
| `internal_tag_list` | `internal_tag_list(*, query=None, limit=None, type=None)` | `GET /api/tags` |
| `internal_tag_show` | `internal_tag_show(name)` | `GET /api/tags/:name` |
| `internal_tag_autocomplete` | `internal_tag_autocomplete(query, *, limit=None)` | `POST /api/tags` |
| `internal_tag_complementary` | `internal_tag_complementary(tag)` | `POST /api/tags/complementary` |
| `internal_artist_list` | `internal_artist_list(*, page=None, limit=None)` | `GET /api/artists` |
| `internal_artist_show` | `internal_artist_show(tag_name)` | `GET /api/artists/:tagName` |
| `internal_artist_wiki` | `internal_artist_wiki(tag_name)` | `GET /api/artists/:tagName/wiki` |
| `internal_artist_reviews` | `internal_artist_reviews(tag_name)` | `GET /api/artists/:tagName/reviews` |
| `internal_user_list` | `internal_user_list(username)` | `GET /api/users?username=` |
| `internal_user_show` | `internal_user_show(user_id)` | `GET /api/users/:id` |
| `internal_user_activity` | `internal_user_activity(user_id, *, type=None)` | `GET /api/users/:id/activity` |

全部是 `Serika.request(...)` 的一行薄封装：普通调用返回原始 JSON；官方多数方法传
`envelope="data"`（返回 `data`，整个 `meta` 进 `last_call["meta"]`）；`user_list` 传
`envelope="users"`；`random_image` 传 `binary=True`。库不校验、不钳位、不重试、不翻页，也不把官方错误
改走站内路由。

## 路由清单与逐条状态

官方 v1（`Q`＝官方 `/api-docs` 是否收录该动词）：

| # | 路由 | 动词 | 客户端方法 | Q | 线上状态（2026-09-15） |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `/api/v1` | GET | `api_index` | 否 | 本轮匿名 `200`（真实输出） |
| 2 | `/api/v1/images` | GET | `image_list` | 是 | 匿名 `401` 历史记录；成功路径未实测 |
| 3 | `/api/v1/images/:id` | GET | `image_show` | 是 | 匿名 `401` 历史记录；成功路径未实测 |
| 4 | `/api/v1/images/:id` | DELETE | `image_delete` | 是 | 仅源码对齐，无线上记录 |
| 5 | `/api/v1/images/:id/similar` | GET | `image_similar` | 是 | 仅源码对齐，无线上记录 |
| 6 | `/api/v1/batch/images` | POST | `image_batch` | 否 | 仅源码对齐，无线上记录 |
| 7 | `/api/v1/random` | GET | `random_list` | 是 | 匿名 `401` 历史记录；成功路径未实测 |
| 8 | `/api/v1/random/:width/:height/image.png` | GET | `random_image` | 是 | 本轮匿名 `200` 且正文是 PNG（真实输出） |
| 9 | `/api/v1/tags` | GET | `tag_list` | 是 | 匿名 `401` 历史记录；成功路径未实测 |
| 10 | `/api/v1/tags/:name` | GET | `tag_show` | 否 | 匿名 `401` 历史记录；成功路径未实测 |
| 11 | `/api/v1/users` | GET | `user_list` | 否 | 本轮匿名 `200`（真实输出） |
| 12 | `/api/v1/users/:id` | GET | `user_show` | 是 | 匿名 `401` 历史记录；成功路径未实测 |
| 13 | `/api/v1/search` | GET | `search` | 否 | 匿名 `401` 历史记录；成功路径未实测 |
| 14 | `/api/v1/trending` | GET | `trending` | 否 | 匿名 `401` 历史记录；成功路径未实测 |
| 15 | `/api/v1/stats` | GET | `stats` | 是 | 本轮匿名 `200`（真实输出） |
| 16 | `/api/v1/upload` | POST | `upload` | 是 | 仅源码对齐，无线上记录 |

站内非版本化（控制器路径相对 clone 根）：

| # | 控制器 | 动词 | 客户端方法 | 线上状态 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `app/api/images/route.ts` | GET | `internal_image_list` | 本轮匿名 `200`（真实输出） |
| 2 | `app/api/images/[id]/route.ts` | GET | `internal_image_show` | 本轮匿名 `200`（真实输出） |
| 3 | `app/api/images/[id]/comments/route.ts` | GET | `internal_image_comments` | 仅源码对齐 |
| 4 | `app/api/tags/route.ts` | GET | `internal_tag_list` | 本轮匿名 `200`（真实输出） |
| 5 | `app/api/tags/[name]/route.ts` | GET | `internal_tag_show` | 仅源码对齐 |
| 6 | `app/api/tags/route.ts` | POST | `internal_tag_autocomplete` | 仅源码对齐 |
| 7 | `app/api/tags/complementary/route.ts` | POST | `internal_tag_complementary` | 仅源码对齐 |
| 8 | `app/api/artists/route.ts` | GET | `internal_artist_list` | 本轮匿名 `200`（真实输出） |
| 9 | `app/api/artists/[tagName]/route.ts` | GET | `internal_artist_show` | 仅源码对齐 |
| 10 | `app/api/artists/[tagName]/wiki/route.ts` | GET | `internal_artist_wiki` | 仅源码对齐 |
| 11 | `app/api/artists/[tagName]/reviews/route.ts` | GET | `internal_artist_reviews` | 仅源码对齐 |
| 12 | `app/api/users/route.ts` | GET | `internal_user_list` | 仅源码对齐 |
| 13 | `app/api/users/[id]/route.ts` | GET | `internal_user_show` | 仅源码对齐 |
| 14 | `app/api/users/[id]/activity/route.ts` | GET | `internal_user_activity` | 仅源码对齐 |

汇总：本轮 8 次匿名调用全部 `200`（4 个官方 v1 + 4 个站内），真实输出在
[verification.md](verification.md#serika2026-09-15-实现后的匿名调用)；**需 key 的 12 个方法的成功路径
全部未实测**（用户没有也不申请 key，勿再索要），其中 8 个 GET 另有改造前的匿名 `401` 记录；
站内其余 10 个方法仅源码对齐。

改造前的匿名边界探测（维护者在本机经代理执行，**不是本轮**的客户端调用）用到的实际路径：
`GET /api/v1`、`/api/v1/stats`、`/api/v1/users?limit=1`、`/api/v1/random/400/400/image.png`
（均 `200`，最后一条返回 PNG 字节），以及 `GET /api/v1/images`、`/api/v1/images/:id`、`/api/v1/tags`、
`/api/v1/tags/:name`、`/api/v1/trending`、`/api/v1/search`、`/api/v1/random`、`/api/v1/users/:id`
（均 `401`）。本轮真实运行的示例用到的实测 URL：`/api/v1/users?page=1&limit=1&sort=newest`、
`/api/v1/random/400/400/image.png?fit=cover&format=png&ratings=safe`、
`/api/images?page=1&limit=3&ratings=safe&sort=newest`、`/api/images/4237836`、`/api/tags?limit=3`、
`/api/artists?page=1&limit=3`。

## 全局规则（官方 v1 源码细节）

### 认证失败梯度（`lib/apiAuth.ts` 的 `validateApiKey`）

| 情形 | HTTP | 说明 |
| :--- | :--- | :--- |
| 没有 key | `401` | — |
| 前缀不是 `sk_serika_` | `401` | "Invalid API key format" |
| hash 查不到或 `is_active = FALSE` | `401` | — |
| `expires_at` 已过 | `401` | — |
| 超过限流 | `429` | 计数见下 |
| 权限不足 | `403` | "Missing required permission: ..." |

**但正文 `code` 不镜像这些差异**：所有 v1 控制器把 key 校验失败统一包装成
`apiError(error, statusCode, 'UNAUTHORIZED')`，因此 401/403/429 三种情况的 `code` 都是
`UNAUTHORIZED`。`FORBIDDEN` 只在"删别人的图且 rank 不是 `admin`/`owner`"这一条业务分支出现；
`RATE_LIMITED` 只出现在**未被任何 v1 路由使用**的 `withApiAuth` 辅助函数里，官方文档页写的是
`RATE_LIMITED`——以控制器为准。

### 权限集

`images:read`、`images:write`、`images:delete`、`tags:read`、`tags:write`、`users:read`、
`random:read`、`upload` 共 8 种；新建 key 的默认权限是 `images:read` + `tags:read` +
`users:read` + `random:read`（不含 write/delete/upload）。`images:write` 与 `tags:write` 在
`/api/v1` **没有任何路由读取**（本面没有图片或标签的改/建路由），这两个权限位在 v1 无消费者；
站内未版本化面不用 API key，不能据此推断它们的用途。

逐路由要求（源码 `validateApiKey(request, [...])` 的第二参数）：

| 路由 | 要求的权限 | 公开（不调用校验） |
| :--- | :--- | :--- |
| `GET /api/v1` | — | ✔ |
| `GET /api/v1/images` | `images:read` | |
| `GET /api/v1/images/:id` | `images:read` | |
| `DELETE /api/v1/images/:id` | `images:delete` | |
| `GET /api/v1/images/:id/similar` | `images:read` | |
| `POST /api/v1/batch/images` | `images:read` | |
| `GET /api/v1/random` | `random:read` | |
| `GET /api/v1/random/:width/:height/image.png` | — | ✔ |
| `GET /api/v1/tags` | `tags:read` | |
| `GET /api/v1/tags/:name` | `tags:read` | |
| `GET /api/v1/users` | — | ✔ |
| `GET /api/v1/users/:id` | `users:read` | |
| `GET /api/v1/search` | `images:read` | |
| `GET /api/v1/trending` | `images:read` | |
| `GET /api/v1/stats` | — | ✔ |
| `POST /api/v1/upload` | `upload` | |

即：图片组里只有删除要求 `images:delete`，其余四条都是 `images:read`；`search` 与 `trending`
复用 `images:read`，`random` 面用 `random:read`，两类标签路由用 `tags:read`，
用户详情用 `users:read`。发 key 时 `images:delete` 只授予 admin/owner、`upload` 只授予
moderator/admin/owner。

### 限流实现

- 运行时按 **API key 行上的 `api_keys.rate_limit` 列**执行，固定 60 秒窗口，计数放缓存，
  不按 rank 现算。
- 官方文档里的 rank 表（user 60、premium 120、moderator 120、admin 1000；`/api-docs` 页另有
  owner 10000）只体现在**发 key 时**的钳位：`app/api/keys/route.ts` 取
  `Math.min(Math.max(10, rateLimit), maxRateLimit)`，`maxRateLimit` 按 rank 为 60/120/1000/10000。
- 超限 HTTP `429`，正文 `code` 是 `UNAUTHORIZED`。

### 成功与错误的正文结构

- 成功（`apiResponse`）：`{"success": true, "data": <payload>, "meta": {"timestamp": ..., ...}}`。
- 错误（`apiError`）：`{"success": false, "error": <文本>, "code": <代码>}`，HTTP 状态与 `code`
  语义同步。
- 三个例外：`GET /api/v1` 直接返回自述对象（没有 `success`/`data`/`meta` 三个键）；
  `GET /api/v1/users` 是 `{"success": true, "users": [...], "pagination": {...}}`（无 `data`，
  也无 `meta.timestamp`）；`GET /api/v1/random/:w/:h/image.png` 是图片字节。
- 常见 `code`：`UNAUTHORIZED`(401/403/429)、`INVALID_ID`(400)、`NOT_FOUND`(404)、
  `TAG_NOT_FOUND`(404)、`INVALID_QUERY`(400)、`INVALID_REQUEST`/`INVALID_IDS`/`TOO_MANY_IDS`(400)、
  `FORBIDDEN`(403，仅删图越权)、`INTERNAL_ERROR`(500)、`MISSING_FILE`/`INVALID_FILE_TYPE`/
  `FILE_TOO_LARGE`/`MISSING_TAGS`/`TOO_MANY_TAGS`/`INVALID_RATING`(400，上传)。

### ID 语义（SQL）

| 路由参数 | 代码里的比较 | 含义 |
| :--- | :--- | :--- |
| `/api/v1/images/:id`（GET/DELETE） | `WHERE i.id = $1` | **内部 `images.id`**（`SERIAL` bigint） |
| `/api/v1/images/:id/similar` | `WHERE id = $1 AND deleted = FALSE AND unlisted = FALSE` | **内部 `images.id`** |
| `/api/v1/batch/images` 的 `ids` | `WHERE i.id = ANY($1)` | **内部 `images.id`** |

- 顺序号是另一列 `images.sequential_id`（`lib/db.ts:410`，`INTEGER UNIQUE`，由 `counters` 表发放），
  对外叫 `post_id`；`GET /api/v1/images/:id` 与 similar 的数组项还会额外给 `sequential_id`。
  列表/详情里的 `id` 与 `dbid` 都是内部 bigint 的字符串形式。
- 列定义：`images.id` = `lib/db.ts:409`（`SERIAL PRIMARY KEY`）、`tags.id` = `lib/db.ts:400`（`SERIAL`）、
  `users.id` = `lib/db.ts:389`（`TEXT PRIMARY KEY`）。
- 实测样本（同一资源）：内部 `id 7323837` ↔ `post_id 4237836`，两者不相等。
- 用户标识符是**文本**主键 `users.id`（`TEXT PRIMARY KEY`，形如 `692ad0df032c62f79b57a08d`），
  `/api/v1/users/:id` 先试 `id = $1`，再退回大小写不敏感的 `LOWER(username) = LOWER($1)`。
- 标签名由服务端 `toLowerCase().trim()` 后精确匹配。
- 关联列：标签内部 id 出现在 `image_tags`、`artists.tag_id`、评论的 `artist_tag_id`；
  站内对外一律用**标签名**访问。画师列表的 `postCount` 取自 `tags.count`。
- 客户端对 `:id`、`:name`、`:identifier`、`:width`、`:height` 每个路径段单独
  `quote(str(value), safe='')`。

### 参数编码

- 查询串与 multipart 表单走同一套 Rails 编码（`encode_params`）：布尔→小写 `true`/`false`，
  `None` 直接不发送，列表→`key[]`；没有文件时请求体是 JSON（`json_params` 去掉 `None`
  但保留显式空数组）。
- 服务端判定布尔用的是**字符串比较**（`=== 'true'`），所以 `ai`、`no_ai`、`blur`、`grayscale`、
  `match_size`、上传的 `is_ai_generated` 只有编码成小写字符串才生效。
- **CSV 参数**（`tags`、`ratings`、`exclude_tags`）只接受逗号分隔的**字符串**（例如
  `tags='blue archive,1girl'`）：客户端不做数组转换，也不解析 Rails 数组语法。
- 官方分页在 `meta.pagination`（`page`、`limit`、`total`、`pages`；`has_next`/`has_prev`
  视路由与分支，`/api/v1/users` 没有这两个键）。

### 内容过滤（`lib/contentFilters.ts`）

- `publicImageFilter()` = `deleted = FALSE AND unlisted = FALSE`，出现在 `images` 列表、
  `random` 两种、`search`、`trending`、`stats`、`tags/:name` 的样本与计数里。
  **它不作用于 `images/:id`(GET) 与 `batch/images`**：这两条按 ID 直查，软删/隐藏的图照样返回；
  `similar` 则对源图和候选图各自加这组条件。
- `ratingFilter(ratings)` 先 `normalizeRatings`：过滤掉非法值后若为空，**回退为 `['safe']`**；
  恰好等于全部三个合法值时不加条件（无过滤）。因此"不传 `ratings`"等于"只看 safe"，不是"全部"。
- 只有接受 `ratings` 的路由会用到这个助手：`images` 列表、`random` 两种、`search` 的 images 段、
  `trending`。`images/:id`(GET) 不加 rating 条件；`similar` 强制与源图同 rating；
  `tags/:name` 的样本图硬编码 `safe`；`batch/images` 无 rating 条件。

## 长尾方法参数与错误码

本节顺序：官方长尾 12 个 → 官方常用方法的补充参数 → 站内长尾 10 个。
逐参数表（名称 / 类型与取值 / 含义 / 不传时的行为 / 字面示例）与返回字段在
[方法参考](serika-api.md)；这里保留服务端的钳位、分支与错误码这类源码级细节。

官方长尾（12 个，全部需 key，成功路径未实测）：

### `image_list(page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, q=None, user_id=None, min_width=None, min_height=None)`

| 参数 | 服务端行为 |
| :--- | :--- |
| `page` | `<1` 被抬到 1 |
| `limit` | 钳位 1..100，默认 20 |
| `tags` | 逗号分隔标签名，**交集**。**部分**名字存在 → `404 TAG_NOT_FOUND`（同一名字在列表里重复也算缺失，因为查询每个名字只回一行）；**全部**不存在 → `200` + `data: []`；名字都存在但无图 → 同样 `200` + `data: []` |
| `ratings` | 逗号分隔 `safe`/`questionable`/`explicit`；非法值剔除、空则回退 `safe`；三个全给 = 不加过滤 |
| `sort` | `newest`(默认)/`oldest`/`popular`(upvotes↓,views↓)/`favorites`/`views`/`random`（非确定）；未知值按 `newest` |
| `ai` | 仅 AI 生成 |
| `q` | 对标签名、`description`、`username` 做子串匹配 |
| `user_id` | 上传者 ID（文本 `users.id`） |
| `min_width` / `min_height` | 最小宽/高（`>0` 才生效） |

返回图片数组 + `meta.pagination`；**空结果分支没有 `has_next`/`has_prev`**，标签全部解析不到时
`total: 0`，只有非空分支才带这两个字段。图片对象字段：`id`/`dbid`（内部 bigint 字符串）、
`post_id`（`sequential_id`）、`url`、`thumbnail_url`、`width`、`height`、`file_size`、
`content_type`、`rating`、`is_ai_generated`、`source`、`description`、`tags`（`[{name, type}]`，
**不带** `shared_tags`）、`stats`（`upvotes`/`downvotes`/`favorites`/`views`）、
`user`（`{id, username}`，`id` 可为 `null`，用户名回退 `"Anonymous"`）、`created_at`、`updated_at`。

### `image_show(image_id)`

参数是**内部 `images.id`**；非数字 → `400 INVALID_ID`；不存在 → `404 NOT_FOUND`。
返回单张图片对象 + `original_filename`、`source`、`description`、`stats.score`(upvotes-downvotes)、
`stats.comments`(评论计数)、`updated_at`。副作用：每次成功调用把 `views` 加一（非阻塞，失败只记日志）。
该路由不加 `deleted`/`unlisted` 与 rating 条件，软删/隐藏的图按 ID 仍能取到。

### `image_delete(image_id)`

权限 `images:delete`（发 key 时仅 admin/owner 可被授予）。参数是内部 `images.id`；非数字 →
`400 INVALID_ID`；不存在 → `404 NOT_FOUND`；不属自己且 rank 不是 `admin`/`owner` → `403 FORBIDDEN`。
返回 `{"deleted": true, "id": "<内部 id>"}`。一个事务里删除 `votes`、`favorites`、`comments`、
`image_tags` 与 `images` 行，并给受影响标签的 `count` 减一。匿名上传（`user_id` 为 `NULL`）的图片
没有属主，属主校验被跳过。

### `image_similar(image_id, limit=None)`

源图是**内部 `images.id`**，且必须 `deleted = FALSE AND unlisted = FALSE`，否则 `404 NOT_FOUND`；
`limit` 钳位 1..50，默认 10。返回 `{"source_id": <路径段原文>, "similar": [...], "count": <int>}`。
算法是标签交集：只找**同 rating** 的公开图，按共享标签数降序、再按 upvotes 降序。每项含
`id`/`dbid`、`post_id`、`sequential_id`、`url`、`thumbnail_url`、`width`、`height`、`rating`、
`is_ai_generated`、`shared_tags`（int）、最多 10 个 `tags`、`stats`（无 `score`/`comments`）。
无结果不是错误：`similar: []`、`count: 0`。

### `image_batch(ids)`

`ids` 是内部 `images.id` 数组，作为 JSON 体 `{"ids": [...]}` 发送；字符串或整数都能被
`parseInt`。非数组或空 → `400 INVALID_REQUEST` "ids must be a non-empty array"；
超过 100 → `400 TOO_MANY_IDS`；全部无法解析 → `400 INVALID_IDS`。
返回 `{"images": [...], "found": <int>, "requested": <int>}`，命中的项按请求顺序排列。
每项与列表对象同构但额外有 `sequential_id`，且匿名上传者时 `user` 为 `null`（不是 `Anonymous`）。
与 `image_show` 一样不加 `deleted`/`unlisted` 与 rating 条件。

### `random_list(...)`

`count` 钳位 1..50，默认 1；`ratings` 同 `image_list`；`tags` 全部命中，**部分**名字不存在 →
`404 TAG_NOT_FOUND`，全部不存在或交集为空 → `200` + `data: []` + `meta.message`；
`exclude_tags` 命中其一即排除，未知标签在此**被忽略**（不报错）；
`min_width`/`min_height`/`max_width`/`max_height` `>0` 才生效；`ai` 优先于 `no_ai`
（`if ai … else if no_ai`）。生效 `count == 1` 时 `data` 是**单个对象**，否则是数组；
`meta` 额外带 `count`（实际返回数）与 `requested`。排序是 `ORDER BY RANDOM()`，
不保证两次请求不同或去重。

### `tag_list(page=None, limit=None, q=None, type=None, sort=None, min_count=None)`

`page` `<1` 抬到 1；`limit` 钳位 1..500，默认 100；`q` 是名称子串（`ILIKE`）；`type` 仅接受
`general`/`artist`/`character`/`copyright`/`meta`，**其它值被静默忽略**（等于不筛类型）；
`sort` 取 `count`(默认)/`name`/`newest`/`oldest`，未知值按 `count`；`min_count` `>0` 时筛
`count >=`。返回 `data` = `[{id, name, type, count, created_at}]`，`meta.pagination` 与图片列表
同构（含 `has_next`/`has_prev`）。`count` 是标签表里存的计数（删除图片时会减一），与
`tag_show` 的重算值可能不同。

### `tag_show(name)`

`name` 经 `toLowerCase().trim()` 后精确匹配；不存在 → `404 NOT_FOUND`。返回
`{id, name, type, count, created_at, sample_images}`。`count` 是**重算**的公开图计数；
`sample_images` 是最多 5 项 `safe` 且公开的图（`{id, thumbnail_url, rating}`，按 upvotes 降序；
`thumbnail_url` 为空时回退 `url`）。

### `user_show(identifier)`

`identifier` 先按 `WHERE id = $1`（文本主键），再退回 `LOWER(username) = LOWER($1)`；都查不到 →
`404 NOT_FOUND`。返回 `{id, username, avatar_url, rank, stats: {images, total_upvotes,
total_views}, created_at}`。`stats` 只统计该用户的图片表行（不过滤 `deleted`/`unlisted`，
也不排除 `NULL` 属主情形）。

### `search(q, type=None, limit=None, ratings=None)`

`q` 必填，长度 < 2 → `400 INVALID_QUERY`；`type` 取 `all`(默认)/`images`/`tags`/`users`，
**其它值一个分支都不跑**，返回空对象 `{}`；`limit` 钳位 1..50，默认 10；`ratings` 只影响
`images` 段（语义同 `image_list`）。返回 `{images: [...], tags: [...], users: [...]}`，只包含被请求的
分支；`meta` 回显 `query` 与 `type`。`images` 段按 upvotes 降序，命中条件是"标签名含 `q`"或
`description`/`username` 含 `q`；每项只有 `id`/`dbid`/`post_id`/`url`/`thumbnail_url`/`width`/`height`/
`rating`/最多 5 个标签名/`stats{upvotes, views}`。`tags` 段是 `{id, name, type, count}`；
`users` 段是 `{id, username, avatar_url, rank}`（字符串 `id`）。

### `trending(period=None, limit=None, ratings=None)`

`period` 取 `day`(默认)/`week`/`month`，对应 24h/7d/30d，未知值按 `day`；`limit` 钳位 1..50，
默认 20；`ratings` **默认 `safe`**，非法值剔除后回退 `safe`，三个全给 = 不过滤。
热度分 `upvotes*3 + favorites*5 + views*0.1`，按分数降序。返回 `{period, images: [...], tags: [...]}`；
图片项含 `trend_score`（取整）、最多 5 个标签名、`uploaded_at`（即 `created_at`）；
`tags` 是这批图里出现最多的**最多 20 个**标签（`id`/`name`/`type`/`trending_count`/`total_count`），
**不受 `limit` 影响**。无结果时是 `{period, images: [], tags: []}`。

### `upload(file, tags, rating, is_ai_generated=None, source=None, description=None)`

权限 `upload`（发 key 时仅 moderator/admin/owner 可被授予；路由本身只查权限位）。**唯一 multipart
端点**：文件键 `file`，其余字段是表单字段。

| 字段 | 说明 |
| :--- | :--- |
| `file` | 必填；只收 `image/jpeg`/`image/png`/`image/gif`/`image/webp` 且 ≤ 50MB。缺失 → `400 MISSING_FILE`，类型错 → `INVALID_FILE_TYPE`，过大 → `FILE_TOO_LARGE`。**必须传 requests 的 `(filename, fileobj, content_type)` 三元组并显式给 MIME**：裸文件对象不发 part 的 `Content-Type`，被解析成 `application/octet-stream` 后会被拒；文件对象生命周期由调用者负责 |
| `tags` | 必填；**原样发送的字符串**，服务端两种格式都吃：JSON 数组文本（`[{"name":"x","type":"general"}]` 或纯字符串数组）或逗号分隔。空/超 100 → `400 MISSING_TAGS` / `TOO_MANY_TAGS`；未知 `type` 回退 `general`；名字按 `lowercase + 空白→下划线` 归一后再查/建标签 |
| `rating` | 必填；仅 `safe`/`questionable`/`explicit`，否则 `400 INVALID_RATING` |
| `is_ai_generated` | 服务端用"表单值 == `'true'`"判定；控制器**还接受** `isAIGenerated` 拼写，本客户端只发 `is_ai_generated` |
| `source` / `description` | 来源 URL 与描述，可空字符串 |

返回新图对象（`id`/`dbid`、`post_id`、`url`、`thumbnail_url`、`width`、`height`、`file_size`、
`content_type`、`rating`、`is_ai_generated`、`tags`、`created_at`），`meta.message` =
"Image uploaded successfully"。服务端在存储上传原图与 320x320 JPEG 缩略图后，于一个事务里建/取标签、
从 `counters` 领 `imageSequentialId`、插入 `images`（`upvotes/downvotes/favorites/views` 全 0，
`deleted`/`unlisted` 为 `FALSE`）并累加标签 `count`。存储后端由 `USE_LOCAL_STORAGE` 环境变量在部署侧
决定（B2 或本地），与本客户端无关。

### 常用方法补充参数（官方 v1）

`api_index()`：`endpoints` 覆盖 `images`（list/get/delete）、`random`（metadata/image）、`tags`（list/get）、
`users`（**只有单用户** `GET /api/v1/users/:id_or_username`）、`search`、`upload`、`stats` 七个面；
它**没有**列出 `batch/images`、`users` 列表和 `trending`，以路由清单为准。`rate_limits` 是文档性数据，
不含 owner 行，运行时并不按 rank 限流。

`stats()`：所有计数都限制在**公开**（未删除、未隐藏）图片上，即 `totals.images` 只数公开图；
`totals.tags` 与 `totals.users` 是整表计数（**含** `user_list` 排除的占位账号）。
实测按评级 safe **3499663**、questionable **324774**、explicit **413406**；
AI 图 **14195**、非 AI 图 **4223648**、最近 24h 上传 **0**。

`user_list(...)`：`page` `<1` 被抬到 1；`limit` 钳位 1..100，默认 50；`q` 是用户名子串（`ILIKE`）；
`sort` 取 `newest`（默认，`created_at DESC, id DESC`）/`oldest`/`alphabetical`/`alphabetical-reverse`/
`uploads`/`uploads-asc`，未知值按 `newest`。`^user_[A-Za-z0-9]{6}$` 形式的占位账号被排除，
所以 `total` 可以小于 `stats()['totals']['users']`；本轮实测两者恰好都是 **3058**，
**不能据源码推断它们每次必定不同**。用户对象字段：`_id`、`id`（同一个值的两个名字）、`username`、
`avatarUrl`、`rank`、`createdAt`、`uploadCount`（只数公开图）。

`random_image(...)`：

| 参数 | 服务端行为 |
| :--- | :--- |
| `width` / `height` | 路径段，接受 16..8000，越界或非数字 → `400` **纯文本**正文 |
| `fit` | `cover`(默认)/`contain`/`fill`/`inside`/`outside`；未知值回退 `cover` |
| `format` | `png`(默认)/`jpeg`/`jpg`/`webp`；未知值输出 PNG |
| `quality` | 钳位 1..100，默认 85；文档说只对 jpeg/webp 生效，控制器对 PNG 也传了它（sharp 的 PNG quality 需要 palette 才生效，未实测差异） |
| `tags` | 逗号分隔。该路由**从不因标签报错**：只有"每个名字都存在**且**存在同时含全部标签的图"时才加上标签条件，否则条件被整体丢弃（代码注释写"退回占位图"，实际是把 where 条件跳过），可能返回**不含**这些标签的随机图 |
| `ratings` | 缺省即 `['safe']`；非法值被剔除后回退 `safe` |
| `exclude_tags` | 逗号分隔排除；名字不存在则不排除任何图，排除条件只在名字存在且命中图时才构造 |
| `blur` / `grayscale` | 高斯模糊（σ≈10）／灰度 |
| `ai` / `no_ai` | `ai` 优先（`if ai … else if no_ai`） |
| `match_size` | 优先挑"不小于请求尺寸（候选下限取 `min(请求尺寸, 400)`）且宽高比在 `aspect_tolerance` 内"的图；找不到再退回纯随机 |
| `aspect_tolerance` | 宽高比容差，服务器默认 0.2 |

响应头：`X-Image-Id`、`X-DBID`（内部 id）、`X-Post-Id`（顺序号）、`X-Original-Width`、
`X-Original-Height`、`X-Rating`、`Cache-Control`。这条路由也是浏览器 `<img>` 直接可用的 URL
（公开、无 key）。本轮实测请求
`GET /api/v1/random/400/400/image.png?fit=cover&format=png&ratings=safe` 返回 `200` 与 PNG 字节，
响应头 `x-image-id`/`x-dbid` = **2796776**、`x-post-id` = **1416106**、`x-original-width` **1168**、
`x-original-height` **2057**、`x-rating` `safe`。
**无匹配时返回 `200` 的灰色占位 PNG**（`#808080`，带 `stale-while-revalidate` 缓存头），所以占位图与命中
只能靠响应头区分（只有命中才带 `X-*` 标识）。控制器内部出错（抓源图、缩放失败等）走 `catch`：
**同样是 `200`**，但返回红色占位 PNG（`#C83232`）且 `Cache-Control: no-cache`；只有连占位图都生成不出来时
才是 `500` 纯文本 `Error generating image`。命中时会给该图 `views` 加一。

站内长尾（10 个，全部仅源码对齐）：

### `internal_image_comments(image_id)`

路径参数是公开序号，先 `SELECT id FROM images WHERE sequential_id = $1`；图不存在 404。
返回 `{"success": true, "comments": [...]}`，按创建时间升序。字段：`_id`（`comments.id` 字符串）、
`imageId`（内部 bigint 的字符串）、`userId`（账号 id）、`username`、`avatarUrl`、`rank`
（缺失时 `user`）、`content`、`parentId`（字符串，顶层评论不存在该键）、`asArtist`、
`artistTagName`（仅以画师身份评论时）、`createdAt`/`updatedAt`。
行号：`app/api/images/[id]/comments/route.ts:19-27`（图查询）、`:85-90`（发评论的 `POST` 要登录）。

### `internal_tag_show(name)`

名字同时尝试原样、空格换下划线、下划线换空格三种形态（全部 lowercase），所以 `blue archive` 与
`blue_archive` 都能命中。返回 `{"success": true, "tag": {_id, id, name, type, count, createdAt}}`
（`_id` 是 id 的字符串形式）；没命中 404。修改标签类型是管理员 `PATCH`。
行号：`app/api/tags/[name]/route.ts:14-22`。

### `internal_tag_autocomplete(query, *, limit=None)`

该文件的 `POST` **不是写资源**：只查 `tags` 表和缓存，不调用 `getCurrentUser`；请求体是 **JSON**。
`query` 缺失或非字符串时服务端直接返回 200 + 空 `suggestions`（不是报错）；`limit` 回落 10，
夹到 1..50。返回 `{"success": true, "suggestions": [...]}`；建议是 `tags` 行，排序权重是
"完全相等 > 前缀 > 词边界 > 使用计数"，返回前去掉内部 `score` 字段；结果缓存 120 秒。
行号：`app/api/tags/route.ts:59-107`（`limit` 夹取在 `:63-68`）。

### `internal_tag_complementary(tag)`

同样是 POST 只读，JSON 体。`tag` 经服务端 lowercase + trim；缺失时 400。返回
`{"success": true, "suggestions": [{name, type, count}]}`，最多 3 条：命中一张硬编码关系表
（约 20 个常见 copyright/character/普通标签）时返回表里的名字，库里还没有该标签行的名字补成
`{name, type: 'general', count: 0}`；否则用 `image_tags` 自连接找共现最多的 3 个标签；
源标签在库里不存在时返回空数组。
行号：`app/api/tags/complementary/route.ts:7-33`（硬编码关系表）、`:38-45`（`tag` 缺失 400）。

### `internal_artist_show(tag_name)`

路径参数是**画师标签名**（接受空格/下划线变体），且标签的 `type` 必须是 `artist`，否则 404
`Artist not found`。返回 `{"success": true, "tag": {_id, id, name, type, count}, "artist": {...} |
null, "reviews": {count, averages: {trust, quality, communication, pricing}}}`：`artist` 是画师资料行
（`_id`/`tagId` 字符串、`tagName`、认领与验证字段、`avatarUrl`、`bannerUrl`、`bio`、`socials`、
`createdAt`），标签存在但还没有资料行时为 `null`；`averages.pricing` 在无人打该项时是 `null`，
其余平均分无评价时为 `0`。更新资料是"已验证画师本人"的 `PATCH`。
行号：`app/api/artists/[tagName]/route.ts:18-24`。

### `internal_artist_wiki(tag_name)`

返回 `{"success": true, "wiki": {...} | null}`：`content`、`infobox`（自由结构）、`lastEditedBy`
（编辑者用户名）、`lastEditedAt`、`editCount`（服务端只存最近 50 条历史，长度即它）。该画师还没有
wiki 时 `wiki` 为 `null`；画师标签本身不存在时 404。编辑 wiki 是登录后的 `POST`。
行号：`app/api/artists/[tagName]/wiki/route.ts:16-33`。

### `internal_artist_reviews(tag_name)`

返回 `{"success": true, "reviews": [...]}`，按创建时间降序；每行 `_id`（字符串）、`userId`
（账号 id）、`username`、`ratings`（`trust`/`quality`/`communication` 必有、`pricing` 可选，各 1-5）、
`comment`（可为 null）、`createdAt`。画师标签不存在 404。提交评价是登录后的 `POST`
（每人每画师一条，冲突则覆盖）。
行号：`app/api/artists/[tagName]/reviews/route.ts:16-38`。

### `internal_user_list(username)`

**集合路径实际是"按用户名查单个用户"**，`username` 必填，缺失 400；没有"列出全部用户"的模式。
先查本地 `users` 表（不区分大小写），**没有账号服务回退**：查不到就是 404。返回
`{"success": true, "user": {id, username, avatarUrl, bannerUrl, rank, createdAt, isPremium,
isVerified}}`；其中 `bannerUrl`、`isPremium`、`isVerified` 需要服务端用内部 service key 调
`accounts.serika.dev`（5 秒超时，失败静默降级），所以它们可能是空/`false` 而其余字段正常，
**按尽力而为理解**。
行号：`app/api/users/route.ts:11-16`（`username` 必填）、`:30-47`（账号服务镜像）。

### `internal_user_show(user_id)`

路径参数是**账号 id**（`users.id`，TEXT 主键），不是用户名、不是公开序号。本地有该行就直接返回
`{"success": true, "user": {id, username, avatarUrl, rank, createdAt}}`；本地没有时服务端带内部
service key 调账号服务，把结果 **upsert 进本地 `users` 表**（`ON CONFLICT (id) DO UPDATE`）再返回。
这个写入是服务端在镜像自己的账号服务，不需要调用方会话，方法仍是匿名读。账号服务也不认识该 id 时
404。
行号：`app/api/users/[id]/route.ts:60-68`（`ON CONFLICT (id) DO UPDATE`）。

### `internal_user_activity(user_id, *, type=None)`

路径参数可以是账号 id，**也可以是用户名**：服务端先按 id 查，查不到再按用户名不区分大小写重查；
两者都没有 404。`type` 取 `all`（回落值，两段都返回）、`likes`、`comments`；**其他值返回
`{"success": true}`，两段都没有**。返回 `{"success": true, "likes": [...], "comments": [...]}`，
只含请求的段，每段最多 50 条：`likes` 是该用户的**点赞（upvote）**列表，元素是图片对象，带
`id`/`dbid`/`_id`、`sequential_id`/`sequentialId`、`thumbnailUrl`、`tags` 等列表别名；
`comments` 每行 `_id`、`content`、`createdAt`、`image`（`{sequentialId, thumbnailUrl}`，
图片行已消失时为 `null`）。
行号：`app/api/users/[id]/activity/route.ts:14-24`（id→用户名回退）、`:40,84`（两段各写死 `LIMIT 50`）。

## 站内逐路由（游标之外的实现细节）

### 路径、动词与响应

- 路径以 `api/` 开头，**没有 `.json` 后缀**，也不接受 Danbooru/Moebooru 那种格式后缀；这些路由都是
  Next.js App Router 的 route handler，动词由导出的 `GET`/`POST` 决定。
- **站内原始 JSON 不拆分**：通常为 `{"success": true, ...}` 加各自资源键
  （`images`、`image`、`comments`、`tags`、`tag`、`artists`、`artist`、`wiki`、`reviews`、`user`）；
  用户活动接口为 `{success, likes?, comments?}`。它们不套官方的 `data` / `meta` 结构。
- 失败分两类：**业务态**也在 `{"success": false, "error": ...}` 里（图片列表的
  `{"success": false, "error": "One or more specified tags were not found", "code":
  "TAG_NOT_FOUND"}` 就是这种，HTTP 同时是 404），**以及 5xx 的 `Failed to ...`**。
  非 2xx 一律由库抛 `AnybooruHTTPError`，正文原样保留。

### 参数命名

- 查询参数是**扁平的**：`page`、`limit`、`tags`、`ratings`、`sort`、`q`、`userId`、`username`、`type`；
  **保持大小写敏感的服务端字段名**（`userId`、`hideAI` 就是这样拼的），本库只在 Python 形参层用下划线，
  例如 `hide_ai=` 对应线上 `hideAI=`、`user_id=` 对应线上 `userId=`、`query=` 对应线上 `q=`。
- 布尔开关按字符串比较：服务端写的是 `=== 'true'`（`app/api/images/route.ts:17-18`），
  所以传 Python 的 `True` 会被编码成字面量 `true`。
- 未指定的参数（`None`）由客户端直接省略，**不会补上服务端的默认值**。

### 分页

| 接口 | 分页参数 | 服务端行为 |
| :--- | :--- | :--- |
| `internal_image_list` | `page` / `limit` | 缺省或空字符串时 `page=1`、`limit=24`，limit 仅做 ≤100 的上限钳位；正常页有 `has_next`，早退空结果不一定有（`app/api/images/route.ts:12-13`） |
| `internal_artist_list` | `page` / `limit` | 缺省或空字符串时 `page=1`、`limit=50`，limit 仅做 ≤100 的上限钳位；没有 `has_next`（`app/api/artists/route.ts:7-8`）；列表按画师标签的使用计数降序（`:16`） |
| `internal_tag_list` | `limit` | 没有 `page`；limit 缺省或空字符串为 50，没有上限钳位（`app/api/tags/route.ts:8`） |
| `internal_user_activity` | — | 没有分页参数，点赞与评论各自写死 `LIMIT 50`（`app/api/users/[id]/activity/route.ts:40,84`） |

上述数字默认发生在 `parseInt` 之前；非空非法文本可能解析为 `NaN`，**不能说"解析失败自动回默认"**。
站内面**没有游标分页**，翻页一律是页码。

### 缓存

- 图片列表的计数与「标签名 → 标签 id」查表都有服务端缓存：标签 id 缓存 5 分钟、计数缓存 10 分钟
  （`app/api/images/route.ts:6-7`）；图片列表响应头是 `public, s-maxage=30,
  stale-while-revalidate=120`，只有 `sort=random` 是 `no-store`（`app/api/images/route.ts:246-249`）。
- 标签补全结果缓存 120 秒（`app/api/tags/route.ts` 补全分支）。
- 命中缓存的标签名**不会回查数据库**，所以刚改动过的标签在缓存窗口内可能仍按旧 id/计数解析。

### 匿名可见性

- 图片列表把 `deleted = FALSE AND unlisted = FALSE` 硬编码进查询（`lib/contentFilters.ts:46-47`），
  评分默认只取 `safe`；列表的 `SELECT` 甚至不选 `deleted`/`unlisted` 列。
- 图片详情对匿名把已删除/未列出**当作不存在**处理：`{"success": false, "error": "Image not found"}`
  + 404，与真的 id 不存在无法区分（`app/api/images/[id]/route.ts:42-66`）。
- 各资源的可见性由各自控制器决定，不能从图片列表的规则推断评论、画师或用户路由的过滤方式。

### 站内逐路由参数（原审计主体）

**`internal_image_list`**（`app/api/images/route.ts`）

| 参数 | 服务端行为 |
| :--- | :--- |
| `page` | 缺省或空字符串时为 `1`，再经 parseInt（`:12`） |
| `limit` | 缺省或空字符串时为 `24`，再经 parseInt 并夹到 ≤100（`:13`） |
| `tags` | 逗号分隔标签名，语义是**交集**（全部命中才返回）。服务端 lowercase 后查 `tags` 表（`:14,62-65`） |
| `ratings` | 逗号分隔的 `safe`/`questionable`/`explicit` 子集；**空或全非法回落 `['safe']`**，三者齐全则完全不加评分过滤（`lib/contentFilters.ts:9-31`） |
| `sort` | `newest`（回落）、`popular`、`favorites`、`views`、`oldest`、`filesize`、`filesize-asc`、`resolution`、`aspectratio`、`alphabetical`、`alphabetical-reverse`、`random`；**未知值不报错，按回落处理**（`:146-159`） |
| `ai` | 字面量 `true` 时只要 AI 生成图（`:17`） |
| `hideAI` | 字面量 `true` 时排除 AI 生成图（`:18`）；与 `ai` 同时给会互相抵消成空结果 |
| `q` | 对 description、上传者 username、标签名做不区分大小写的子串匹配（`:127-141`） |
| `userId` | 上传者账号 id；字面量 `null` 表示"上传者为空（匿名上传）"（`:34-40`） |
| `username` | 上传者用户名，不区分大小写；**优先级高于 `userId`**（`:30-33`） |

返回 `{"success": true, "images": [...], "pagination": {page, limit, total, pages, has_next}}`。
每个 image 同时带数据库名和前端别名：`id`/`dbid`(str)/`_id`(str) 是内部 id，
`sequential_id`/`post_id`/`sequentialId` 是公开序号，另有 `user_id`/`userId`、`username`、`url`、
`thumbnail_url`/`thumbnailUrl`、`width`、`height`、`file_size`/`fileSize`、`rating`、
`is_ai_generated`/`isAIGenerated`、`upvotes`、`downvotes`、`favorites`、`views`、
`created_at`/`createdAt`，以及 `tags`（`[{_id, id, name, type, count}]`）。

> **未知标签的分支比"一律 404"更细**（`app/api/images/route.ts:61-96`）：标签名先查 5 分钟缓存，
> 缓存未命中的才批量查库。若查库发现缺名字，且**此时一个 tag id 都没解析出来**（即全部标签都不存在），
> 返回的是 **200 + 空 `images` + `total: 0`**；只有**已经解析出至少一个 tag id**（例如部分名字来自缓存）
> 时才是 **404** + `code: "TAG_NOT_FOUND"`。所以"未知标签"的结果同时取决于缓存状态，
> 不能简单记成"错误"或"空数组"。

**`internal_image_show`**（`app/api/images/[id]/route.ts`）

- 路径参数是**公开序号 `sequential_id`**（`app/api/images/[id]/route.ts:24-29`）；非数字 400。
- GET 会**有条件地**问一次会话（`:42-50`：`getCurrentUser()`，仅用于让上传者/版主看到未列出或已删除的图）；
  没有任何凭据时走公开分支，所以它仍是匿名可读方法，只是拿不到那些隐藏记录。
- 返回 `{"success": true, "image": {...}}`：除列表字段外还有 `original_filename`/`originalFilename`、
  `content_type`/`contentType`、`source`、`description`、`deleted`、`unlisted` 及删除/未列出的审计列、
  `updated_at`/`updatedAt`。
- **副作用**：读取会把 `views` 自增（`:85-88`，fire-and-forget），响应里的 `views` 是 `+1` 后的值。
  这是站点自己的计数器，不涉及调用方会话状态。
- 写动词 `PATCH`/`DELETE` 不属于本库的匿名读取范围。

**`internal_tag_list`**（`app/api/tags/route.ts`）

`q` 是标签名子串，不区分大小写（`:15-19`）；`limit` 回落 `50`，**没有上限夹取**（`:8`）；
`type` 只在五个枚举值时生效，**其他值被静默忽略**（`:21-25`）。返回
`{"success": true, "tags": [...], "grouped": {...}}`：`tags` 按使用计数降序，每行是 `tags` 表的整行
（`id`、`name`、`type`、`count`、`created_at`）；`grouped` 是按 `type` 分桶的同一批行。

## 官方文档矛盾（逐条）

以控制器为准，以下是 `app/api-docs/endpoints.ts` / `page.tsx`（以及常见转述）与源码的出入：

| # | 文档说法 | 源码实际 |
| :--- | :--- | :--- |
| 1 | 只收录 10 个动词 | 实际 16 个动词：未收录 `GET /api/v1`、`POST /api/v1/batch/images`、`GET /api/v1/search`、`GET /api/v1/trending`、`GET /api/v1/users`（列表）、`GET /api/v1/tags/:name` |
| 2 | `images/:id`(GET/DELETE)、similar 的 `:id` 是 "sequential ID (post_id)" | 三处都用**内部 `images.id`**（`WHERE i.id = $1`）；`batch/images` 的 `ids` 同样是内部 id。顺序号是另一列 `sequential_id`，响应里叫 `post_id` |
| 3 | 权限不足 → `403 FORBIDDEN` | 缺权限时路由包装成 `code: "UNAUTHORIZED"`；`FORBIDDEN` 只在"删别人的图且非 admin"这一条业务分支出现 |
| 4 | 超限 → `429 RATE_LIMITED` | HTTP 是 `429`，但正文 `code` 是 `UNAUTHORIZED`；`RATE_LIMITED` 只出现在未被 v1 路由使用的 `withApiAuth` 辅助函数里 |
| 5 | 按 rank 的限流表（60/120/1000，页面上还有 owner 10000） | 运行时按 `api_keys.rate_limit` 字段；rank 只决定**发 key 时**的钳位上限（60/120/1000/10000） |
| 6 | 参数默认值（如 `ratings` 默认 `safe`） | 一致，但实现是"非法值剔除后回退 `safe`"，且**三个全给 = 不加过滤**；文档没写这两个细节 |
| 7 | 未提未知标签的分支 | `images` 列表与 `random` 只在**部分**名字不存在时返回 `404 TAG_NOT_FOUND`；全部不存在（或交集为空）返回 `200` + `data: []`。`tag_show` 不存在 → `404 NOT_FOUND`。`random/:w/:h/image.png` 则把标签条件整体丢弃、返回其它随机图 |
| 8 | 未提二进制细节 | `random/:w/:h/image.png` 无匹配时返回 `200` 灰色占位 PNG（`#808080`），控制器内部异常也是 `200` 但为红色占位 PNG（`#C83232`）且 `Cache-Control: no-cache`；只有连占位图都生成不出来时才是 `500` 纯文本 `Error generating image`；越界尺寸返回 `400` **纯文本**正文 |
| 9 | `quality` 只对 jpeg/webp 生效 | 控制器对 PNG 也传了 `quality`（sharp 的 PNG quality 需要 palette 才生效，未实测输出差异） |
| 10 | upload "Requires moderator rank or above" | 路由只看 `upload` 权限位；moderator+ 门槛在 `/api/keys` 发 key 时执行（`images:delete` 同理只给 admin/owner） |
| 11 | 未文档化的字段名 | `users` 列表用 camelCase（`avatarUrl`/`uploadCount`/`createdAt`）且同时给 `_id` 与 `id`；`tags/:name` 的 `count` 是重算值；`stats.totals.users` 含占位账号 |
| 12 | `/api/v1` 索引的 `endpoints` 自述 | 未列 `batch/images`、`users` 列表、`trending`；`users` 面只写单用户路由（`tags/:name`、`search`、`stats`、`upload` 有列） |

### 与代码注释的出入（PNG 标签过滤）

`random/:w/:h/image.png` 的注释说"无匹配时回占位图"，实际实现是：只有**每个标签名都存在且存在同时含
全部标签的图**时才给 SQL 加标签条件，否则条件被整体跳过，于是可能返回**不含**这些标签的随机图。
同理 `tags` 未知时 v1 的 `random` 列表路由的 404/空数组分支与 PNG 路由完全不同（见矛盾表第 7 条）。

## 排除项（有路由，但本库不封方法）

| 路由 | 动词 | 为什么不封 |
| :--- | :--- | :--- |
| `/api/images/:id/artist-status` | GET | **会话语义探针**：匿名时 `getCurrentUser()` 返回 null 就直接回 `{"success": true, "canCommentAsArtist": false, "artistTags": []}`，**不读任何公开资源**；只有登录后才有意义（`app/api/images/[id]/artist-status/route.ts:11-20`） |
| `/api/images/:id/user-interaction` | GET | 私有交互状态：匿名恒定返回 `{"success": true, "vote": null, "isFavorited": false}`，同样只有登录后才有信息 |
| `/api/images/:id/comments` | POST | 发表评论需要登录 |
| `/api/images/:id` | PATCH / DELETE | 编辑/删除是写操作，不属于站内匿名读取范围 |
| `/api/tags/:name` | PATCH | 改标签类型需要 admin/owner |
| `/api/artists/:tagName` | PATCH | 改画师资料需要"已验证的画师本人" |
| `/api/artists/:tagName/wiki`、`/reviews` | POST | 编辑 wiki、提交评价需要登录 |
| `/api/artists/:tagName/claim` | POST | 画师认领需要登录 |
| `/api/comments/:id` | PATCH / DELETE | 评论编辑/删除需要作者或版主 |
| `/api/vote` | POST | 投票是会话写操作 |
| `/api/favorite` | GET / POST | 收藏状态与收藏动作都属于私有用户交互 |
| `/api/dmca`、`/api/dmca/:id` | POST / GET / PATCH | 提交申请、列表与状态修改分别属于写操作和 admin/mod 范围 |
| `/api/contact` | POST | 发送邮件，是写操作 |
| `/api/keys` | GET / POST / DELETE | API key 管理需要登录 |
| `/api/auth/{login,logout,exchange,me}` | POST / GET | 会话登录流程本身；**本库不实现 cookie 会话** |
| `/api/moderation/action` | POST | 审核动作需要登录 |
| `/api/admin/*`（含 `/admin/import/*`） | GET / POST / PATCH / PUT / DELETE | admin/owner 专用，连 GET 都要管理员 |
| `/api/upload`、`/api/upload/{claim-file,profile,wiki}` | POST | 上传是写操作；除 `/api/upload` 允许匿名上传外都需要登录 |
| `/api/ad` | GET | 站点第三方广告位：必填 `zoneId` 且会再向外部广告网络 `s.magsrv.com` 发请求，不属于站点内容读取 |

官方 `image_batch` 虽用 POST，但属于批量读取；`upload` 与 `image_delete` 才是资源写操作，
它们需要 API key，只做源码对齐。站内另有两条 **POST 只读查询**（`internal_tag_autocomplete`、
`internal_tag_complementary`），不是写接口，已封为方法。`internal_image_show` 的浏览计数、
`internal_user_show` 的服务端账号镜像都是控制器自带副作用，不是客户端登录能力。

## 未解决事项

- 官方需 key 的 12 个方法：认证成功路径、权限位实际效果、限流触发、JSON 批量读取、multipart 上传、
  删除事务与全部参数组合均未实测（无凭据，也不申请）。
- 站内 10 个方法只核对匿名可读分支，未发线上请求；这些路由未版本化，站点可随时改。
- PNG 错误占位（灰/红）分支与二进制错误状态未探测；`quality` 对 PNG 的实际输出差异未实测。
- 其他自托管部署、`internal_user_list`/`internal_user_show` 的账号服务降级路径未实测。
- 本库未实现站内 cookie 会话、私有交互与资源写操作，也未新增任何相关配置键。
