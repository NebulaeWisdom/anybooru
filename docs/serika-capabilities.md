# Serika 能力总览：两个面，先确认你在读哪一个

**不知道有哪些接口，先看这页；要逐条参数与形状，见 [官方 v1 API 参考](serika-api.md) 与下面的站内路由小节。**

- **Serika 是第三类站点**：既不是 Danbooru 也不是 Moebooru。项目自述是 Next.js 自研的 "Danbooru-style" 图站，
  但它对外**没有** `/posts.json`、`/post.json` 这类 Danbooru 契约。仓库里 `lib/danbooru.ts` 对 `/posts.json`
  的调用是 Serika 作为 Danbooru **消费者**的导入器，不能反推它提供 Danbooru 接口。
- **它有两个 API 面**：
  - **官方面 `/api/v1/*`**：自称 "SerikaART API 1.0.0"，带版本号，用 `Authorization: Bearer sk_serika_*`
    或 `X-API-Key` 认证，成功响应有 `{success, data, meta}` 信封。参数与权限逐条见
    [serika-api.md](serika-api.md)（另一份文档维护，本页只概括能力）。
  - **站内面 `/api/*`**：**未版本化**、无对外文档，是 Serika 网页前端自己调用的路由（Next.js route handler）。
    其中一批读接口不需要任何凭据，本页逐路由列出；本库对它们统一用 `internal_` 前缀的方法暴露。
- **认证形态是第三种**：官方面用 API key（Bearer / `X-API-Key`），站内面用 `session_token` cookie 或
  同样经账号服务校验的 Bearer 会话 token。**本库只实现 API key，不实现浏览器 cookie 登录**，
  不提供获取、配置或刷新 Serika Accounts 会话身份的方法。
- **库负责 API 请求**，不是自动采集器：不自动保存图片或翻页；官方随机图片方法直接返回 `bytes`。
- **有接口不等于本站已启用，也不是全部实测过**。本页把「有历史线上证据」和「仅源码对齐」分开标注。

## 先按目的找入口

下表的 `c` 是按根配置创建的 `Serika` 客户端；查询字典取自 `examples.serika` 或应用自定配置，
`post_id`、`tag_name`、`username`、`user_id` 从实际响应取得，不是写死在库里的默认输入。

| 我想做什么 | 能力与方法 | 最简调用形态 | 是否需要凭据 |
| :--- | :--- | :--- | :--- |
| 按标签、评分、排序浏览图片（无 key） | `internal_image_list`：站内图片列表，标签取交集、评分过滤、多种排序 | `c.internal_image_list(**example['image_query'])` | 匿名可读 |
| 按同样条件浏览图片（有 key，版本化契约） | 官方 `image_list`，参数与错误码更完整 | 见 [serika-api.md](serika-api.md) | 需 `images:read` 权限的 key |
| 看一张图的详情 | `internal_image_show`：按**公开序号**读取 | `c.internal_image_show(post_id)` | 匿名可读 |
| 看某张图的评论 | `internal_image_comments` | `c.internal_image_comments(post_id)` | 匿名可读 |
| 检索标签、查单个标签 | `internal_tag_list` / `internal_tag_show` | `c.internal_tag_list(**example['tag_query'])`；`c.internal_tag_show(tag_name)` | 匿名可读 |
| 输入时给标签补全、找搭配标签 | `internal_tag_autocomplete` / `internal_tag_complementary` | `c.internal_tag_autocomplete(tag_name)`；`c.internal_tag_complementary(tag_name)` | 匿名可读（都是 POST 只读查询） |
| 查画师页、简介与评价 | `internal_artist_list` / `internal_artist_show` / `internal_artist_wiki` / `internal_artist_reviews` | `c.internal_artist_show(artist_tag_name)`；`c.internal_artist_wiki(artist_tag_name)` | 匿名可读 |
| 按用户名或账号 id 查用户 | `internal_user_list`（按用户名）/ `internal_user_show`（按账号 id） | `c.internal_user_list(username)`；`c.internal_user_show(user_id)` | 匿名可读 |
| 看某用户点赞过什么、发过什么评论 | `internal_user_activity` | `c.internal_user_activity(user_id)` | 匿名可读 |
| 站点统计、热门、搜索、随机图（官方面） | 官方 `stats`、`trending`、`search`、`random_list`、`random_image` 等 | 见 [serika-api.md](serika-api.md) | `stats` 与二进制随机图匿名可用，其余要求 key |
| 上传图片（官方面） | 官方 `upload`（multipart） | 见 [serika-api.md](serika-api.md) | 需 `upload` 权限，发 key 时限制可获此权限的等级 |
| 删除图片、批量读取（官方面） | 官方 `image_delete` / `image_batch` | 见 [serika-api.md](serika-api.md) | 分别需 `images:delete` / `images:read` |

**三个容易选错的地方**：① 站内 `/api/images/:id` 用的是**公开序号 `sequential_id`**，而官方 `/api/v1/images/:id`
用的是**内部自增 `images.id`**（详见下面的 [ID 语义](#id-语义四个同名不同义的数字)）；② 站内面的
`tags`/`ratings` 是**逗号字符串**，不是数组；③ 使用 `ratingFilter` 的列表/随机/搜索/热门路由
不传 `ratings` 时只返回 `safe`（详情、similar 等不适用这条泛化），这是服务端默认，不是客户端兜底。

## 认证边界

| 身份 / 凭据 | 能做什么 | 主要边界 |
| :--- | :--- | :--- |
| 匿名（无任何凭据） | 全部 `internal_*` 读方法；官方 `api_index`、`user_list`、`stats`、`random_image` | 其余 12 个官方方法需 key：其中 8 个 GET 的匿名 `401` 有历史记录，另 4 个动词仅源码依据 |
| 官方 API key（`sk_serika_*`，`Authorization: Bearer` 或 `X-API-Key`） | 官方 `/api/v1/*` 中与该 key 权限相符的读写 | 权限集是 `images:read/write/delete`、`tags:read/write`、`users:read`、`random:read`、`upload`；默认 key 只有 `*:read`。限流执行的是 key 行上存的 `rate_limit`（不是按 rank 现算），超限 HTTP `429`，正文 `code` 为 `UNAUTHORIZED`；细节见 [serika-api.md](serika-api.md) |
| 会话（`session_token` cookie 或账号服务签发的 Bearer 会话 token） | 站内写操作与私有交互 | **本库不实现会话登录/会话写方法**；官方 API key 不等于会话 token |

- 官方面认证在 `lib/apiAuth.ts`，站内面会话在 `lib/auth.ts:18`（`getCurrentUser()`：cookie 里的
  `session_token`，其次 `Authorization: Bearer`，再向账号服务 `accounts.serika.dev` 校验）。
- **站内匿名读方法的共同点是：存在一条不需要会话就能走通的分支**，本页方法走的都是这条分支（逐条来源见下）。
  多数 handler 完全不看会话；`internal_image_show` 是例外——它会**有条件地**用 `getCurrentUser()`
  放宽可见性，没有凭据时走的正是公开分支。
- 根仓库 `middleware.ts` 只匹配 `/upload/:path*` 与 `/user/:path*`，**不拦截 `/api/*`**；
  每个站内路由的可见性完全由它自己的 handler 决定。

## 官方 v1 面（概括）

官方面共 **15 个路由文件 / 16 个动词与方法**：index、images 列表、images/:id（GET/DELETE）、images/:id/similar、batch/images（POST）、
random、random/:width/:height/image.png（二进制）、tags 列表、tags/:name、users 列表、users/:id、search、
trending、stats、upload（multipart）。

- **成功信封**是 `{"success": true, "data": ..., "meta": {"timestamp": ...}}`；错误既改 HTTP 状态码，
  也在正文给 `{"success": false, "error": ..., "code": ...}`。两个例外：`/api/v1`（index）直接返回 API
  自述对象（`name`/`version`/`endpoints`/`authentication`/`rate_limits`，没有 `success`/`data`）；
  `/api/v1/users` 列表返回 `{"success": true, "users": [...], "pagination": {...}}`，没有 `data`。
- **官方面多数请求要 key**，匿名可用的只有 4 条：`/api/v1`（index）、`/api/v1/users`（列表）、
  `/api/v1/stats` 与二进制随机图端点（最后一条是 `<img>` 直接可用的 URL）；这 4 条有匿名 200 的实测记录。
  缺 key 时**实测**这 8 条回 `401`：`images` 列表与详情、`tags` 列表与详情、`trending`、`search`、`random`、
  `users/:id`；`image_similar`、`image_batch`、`image_delete`、`upload` 只有源码认证依据，没有线上调用记录。
- 官方面自身的文档在 `app/api-docs/endpoints.ts`，与本页的站内面无关；**该文件对 images/:id 的 id 描述与
  实现矛盾**（文档写 sequential `post_id`，代码是 `WHERE i.id = $1`），以代码为准。
- 方法名、参数、权限与错误码：见 [serika-api.md](serika-api.md)。

## 站内面（未版本化）共同契约

站内面没有版本号、没有对外兼容承诺，形状可能随时改；下面是 2026-09-15 对本地只读 clone
（`Serika.art/`，HEAD `ef11dd12`）核对出的实际行为。行号引用格式为 `app/api/.../route.ts:N`。

### 路径、动词与响应

- 路径以 `api/` 开头，**没有 `.json` 后缀**，也不接受 Danbooru/Moebooru 那种格式后缀；
  这些路由都是 Next.js App Router 的 route handler，动词由导出的 `GET`/`POST` 决定；
- **站内原始 JSON 不统一拆封**：通常为 `{"success": true, ...}` 加各自资源键
  （`images`、`image`、`comments`、`tags`、`tag`、`artists`、`artist`、`wiki`、`reviews`、`user`）；
  用户活动接口为 `{success, likes?, comments?}`。它们不使用官方的 `data` / `meta` 信封。
- 失败分两类：**业务态**也在 `{"success": false, "error": ...}` 里（图片列表的
  `{"success": false, "error": "One or more specified tags were not found", "code": "TAG_NOT_FOUND"}`
  就是这种，HTTP 同时是 404），**以及 5xx 的 `Failed to ...`**。非 2xx 一律由库抛
  `PybooruHTTPError`，正文原样保留。

### 参数编码

- 查询参数是**扁平的**：`page`、`limit`、`tags`、`ratings`、`sort`、`q`、`userId`、`username`、`type`；
  **保持大小写敏感的服务端字段名**（`userId`、`hideAI` 就是这样拼的），本库只在 Python 形参层用下划线，
  例如 `hide_ai=` 对应线上 `hideAI=`、`user_id=` 对应线上 `userId=`；
- `tags`、`ratings` 是**逗号分隔字符串**（`'blue archive,1girl'`），**不是** Rails 数组、不要传列表；
- 布尔开关按字符串比较：服务端写的是 `=== 'true'`（`app/api/images/route.ts:17-18`），
  所以传 Python 的 `True` 会被编码成字面量 `true`；
- 未指定的参数（`None`）由客户端直接省略，**不会补上服务端的默认值**：默认值始终由服务端决定，
  本页标注的 default 是**服务端行为**，不是客户端兜底。

### 分页

| 接口 | 分页参数 | 服务端行为 |
| :--- | :--- | :--- |
| `internal_image_list` | `page` / `limit` | 缺省或空字符串时 `page=1`、`limit=24`，limit 仅做 ≤100 的上限钳位；正常页有 `has_next`，早退空结果不一定有（`app/api/images/route.ts`） |
| `internal_artist_list` | `page` / `limit` | 缺省或空字符串时 `page=1`、`limit=50`，limit 仅做 ≤100 的上限钳位；没有 `has_next` |
| `internal_tag_list` | `limit` | 没有 `page`；limit 缺省或空字符串为 50，没有上限钳位 |
| `internal_user_activity` | — | 没有分页参数，点赞与评论各自写死 `LIMIT 50`（`app/api/users/[id]/activity/route.ts:40,84`） |

上述数字默认发生在 `parseInt` 之前；非空非法文本可能解析为 `NaN`，不能说“解析失败自动回默认”。

站内面**没有游标分页**；翻页一律是页码。

### 缓存（影响你看到的结果，不是客户端行为）

- 图片列表的计数与「标签名 → 标签 id」查表都有服务端缓存：标签 id 缓存 5 分钟、计数缓存 10 分钟
  （`app/api/images/route.ts:6-7`）；图片列表响应头是 `public, s-maxage=30, stale-while-revalidate=120`，
  只有 `sort=random` 是 `no-store`（`app/api/images/route.ts:246-249`）；
- 标签补全结果缓存 120 秒（`app/api/tags/route.ts` 补全分支）；
- 命中缓存的标签名**不会回查数据库**，所以刚改动过的标签在缓存窗口内可能仍按旧 id/计数解析。

### 匿名可见性过滤

- 图片列表把 `deleted = FALSE AND unlisted = FALSE` 硬编码进查询（`lib/contentFilters.ts:46-47`），
  评分默认只取 `safe`；列表的 `SELECT` 甚至不选 `deleted`/`unlisted` 列；
- 图片详情对匿名把已删除/未列出**当作不存在**处理：`{"success": false, "error": "Image not found"}` + 404，
  与真的 id 不存在无法区分（`app/api/images/[id]/route.ts:42-66`）；
- 各资源的可见性由各自控制器决定，不能从图片列表的规则推断评论、画师或用户路由的过滤方式。

### ID 语义：四个同名不同义的数字

| 标识 | 定义处 | 含义 | 谁在用它 |
| :--- | :--- | :--- | :--- |
| `images.id` | `lib/db.ts:409`（`SERIAL PRIMARY KEY`） | 内部自增 bigint；站内响应里也叫 `dbid` / `_id`（字符串形式） | 官方 `/api/v1/images/:id`、`/similar`；评论的 `imageId`；点赞列表里的 `id` |
| `images.sequential_id` | `lib/db.ts:410`（`INTEGER UNIQUE`） | **公开序号**；站内响应里叫 `post_id` / `sequentialId` | **站内** `/api/images/:id`、`/api/images/:id/comments`、`/api/users/:id/activity` 的图片引用；二进制随机图的 `X-Post-Id` |
| `users.id` | `lib/db.ts:389`（`TEXT PRIMARY KEY`） | 账号服务 `accounts.serika.dev` 的账号 id（形如 `692ad0df032c62f79b57a08d`） | 上传者 `user_id`/`userId`、评论 `userId`、投票/收藏归属、`/api/users/:id`、`/api/users/:id/activity`、画师认领 |
| `tags.id` | `lib/db.ts:400`（`SERIAL`） | 标签内部自增 | `image_tags`、`artists.tag_id`、评论的 `artist_tag_id`；站内对外一律用**标签名**访问 |

实测过的差异：同一个对象 `id = 7323837` 与 `post_id = 4237836` 是两个不同的数字，
不要拿一个去查另一个接口。评论的 `_id` 是 `comments.id`（内部自增），也不是公开序号。

## 站内逐路由

本节每条都是**站内非版本化私有契约**，并另标线上证据：`已实测`＝有历史匿名 200 且本轮已通过
客户端运行同一路由；`源码对齐`＝只核对控制器，本轮未发请求。具体输入与响应见 [verification.md](verification.md)。

### 图片

#### `internal_image_list` — `GET /api/images` 【已实测】

| 参数 | 服务端行为（来源 `app/api/images/route.ts`） |
| :--- | :--- |
| `page` | 页码；缺省或空字符串时为 `1`，再经 parseInt（`:12`） |
| `limit` | 每页条数；缺省或空字符串时为 `24`，再经 parseInt 并夹到 ≤100（`:13`） |
| `tags` | 逗号分隔标签名，语义是**交集**（全部命中才返回）。服务端 lowercase 后查 `tags` 表（`:14,62-65`） |
| `ratings` | 逗号分隔的 `safe`/`questionable`/`explicit` 子集；**空或全非法回落 `['safe']`**，三者齐全则完全不加评分过滤（`lib/contentFilters.ts:9-31`） |
| `sort` | `newest`（回落）、`popular`、`favorites`、`views`、`oldest`、`filesize`、`filesize-asc`、`resolution`、`aspectratio`、`alphabetical`、`alphabetical-reverse`、`random`；**未知值不报错，按回落处理**（`:146-159`） |
| `ai` | 字面量 `true` 时只要 AI 生成图（`:17`） |
| `hideAI` | 字面量 `true` 时排除 AI 生成图（`:18`）；与 `ai` 同时给会互相抵消成空结果 |
| `q` | 对 description、上传者 username、标签名做不区分大小写的子串匹配（`:127-141`） |
| `userId` | 上传者账号 id；字面量 `null` 表示"上传者为空（匿名上传）"（`:34-40`） |
| `username` | 上传者用户名，不区分大小写；**优先级高于 `userId`**（`:30-33`） |

返回：`{"success": true, "images": [...], "pagination": {page, limit, total, pages, has_next}}`。
每个 image 同时带数据库名和前端别名：`id`/`dbid`(str)/`_id`(str) 是内部 id，`sequential_id`/`post_id`/`sequentialId`
是公开序号，另有 `user_id`/`userId`、`username`、`url`、`thumbnail_url`/`thumbnailUrl`、`width`、`height`、
`file_size`/`fileSize`、`rating`、`is_ai_generated`/`isAIGenerated`、`upvotes`、`downvotes`、`favorites`、`views`、
`created_at`/`createdAt`，以及 `tags`（`[{_id, id, name, type, count}]`）。

> **未知标签的分支比"一律 404"更细**（`app/api/images/route.ts:61-96`）：标签名先查 5 分钟缓存，
> 缓存未命中的才批量查库。若查库发现缺名字，且**此时一个 tag id 都没解析出来**（即全部标签都不存在），
> 返回的是 **200 + 空 `images` + `total: 0`**；只有**已经解析出至少一个 tag id**（例如部分名字来自缓存）
> 时才是 `404` + `code: "TAG_NOT_FOUND"`。所以"未知标签"的结果同时取决于缓存状态，
> 不能简单记成"错误"或"空数组"。

#### `internal_image_show` — `GET /api/images/:id` 【已实测】

- 路径参数是**公开序号 `sequential_id`**（`app/api/images/[id]/route.ts:24-29`）；非数字 400。
- 这个 GET 会**有条件地**问一次会话（`:42-50`：`getCurrentUser()`，仅用于让上传者/版主看到未列出或
  已删除的图）。**没有任何凭据时走公开分支**，所以它仍是匿名可读方法，只是拿不到那些隐藏记录。
- 返回 `{"success": true, "image": {...}}`：除列表字段外还有 `original_filename`/`originalFilename`、
  `content_type`/`contentType`、`source`、`description`、`deleted`、`unlisted` 及删除/未列出的审计列、
  `updated_at`/`updatedAt`。
- 匿名把已删除/未列出当 404（`:42-66`）。
- **副作用**：读取会把 `views` 自增（`:85-88`，fire-and-forget），响应里的 `views` 是 `+1` 后的值。
  这是站点自己的计数器，不涉及调用方会话状态，方法仍是匿名读。
- 写动词 `PATCH`/`DELETE` 不属于本轮匿名读取范围，本库不提供。

#### `internal_image_comments` — `GET /api/images/:id/comments` 【源码对齐】

- 路径参数是公开序号，先 `SELECT id FROM images WHERE sequential_id = $1`；图不存在 404（`:19-27`）。
- 返回 `{"success": true, "comments": [...]}`，按创建时间升序。字段：`_id`（`comments.id` 字符串）、
  `imageId`（内部 bigint 的字符串）、`userId`（账号 id）、`username`、`avatarUrl`、`rank`（缺失时 `user`）、
  `content`、`parentId`（字符串，顶层评论不存在该键）、`asArtist`、`artistTagName`（仅以画师身份评论时）、
  `createdAt`/`updatedAt`。
- 发评论的 `POST` 要登录（`:85-90`），不在本库范围内。

### 标签

#### `internal_tag_list` — `GET /api/tags` 【已实测】

| 参数 | 服务端行为（`app/api/tags/route.ts`） |
| :--- | :--- |
| `q` | 标签名子串，不区分大小写（`:15-19`） |
| `limit` | 返回条数；回落 `50`，**没有上限夹取**（`:8`） |
| `type` | 只在 `general`/`artist`/`character`/`copyright`/`meta` 时生效；**其他值被静默忽略**，等于不加类型过滤（`:21-25`） |

返回 `{"success": true, "tags": [...], "grouped": {...}}`：`tags` 按使用计数降序，每行是 `tags` 表的整行
（`id`、`name`、`type`、`count`、`created_at`）；`grouped` 是按 `type` 分桶的同一批行。

#### `internal_tag_show` — `GET /api/tags/:name` 【源码对齐】

- 名字会同时尝试原样、空格换下划线、下划线换空格三种形态（全部 lowercase），所以 `blue archive` 与
  `blue_archive` 都能命中（`app/api/tags/[name]/route.ts:14-22`）。
- 返回 `{"success": true, "tag": {_id, id, name, type, count, createdAt}}`（`_id` 是 id 的字符串形式）；
  没命中 404。修改标签类型是管理员 `PATCH`，不在本库范围内。

#### `internal_tag_autocomplete` — `POST /api/tags` 【源码对齐】

- 该文件里 `POST` **不是写资源**：它只查 `tags` 表和缓存，不调用 `getCurrentUser`，是纯粹的补全查询
  （`app/api/tags/route.ts:59-107`）。请求体是 **JSON**（不是表单）。
- 参数：`query`（输入的片段；缺失或非字符串时服务端直接返回 200 + 空 `suggestions`，而不是报错）、
  `limit`（回落 10，夹到 1..50，`:63-68`）。
- 返回 `{"success": true, "suggestions": [...]}`；建议是 `tags` 行，排序权重是"完全相等 > 前缀 > 词边界 >
  使用计数"，返回前会去掉内部 `score` 字段；结果缓存 120 秒。

#### `internal_tag_complementary` — `POST /api/tags/complementary` 【源码对齐】

- 同样是 **POST 只读**接口，JSON 体，服务端不调用 `getCurrentUser`。
- 参数：`tag`（源标签名，服务端 lowercase + trim）；缺失时 400（`app/api/tags/complementary/route.ts:38-45`）。
- 返回 `{"success": true, "suggestions": [{name, type, count}]}`，最多 3 条：
  - 命中 `:7-33` 那张硬编码关系表（约 20 个常见 copyright/character/普通标签）时，返回表里的名字；
    库里还没有该标签行的名字会补成 `{name, type: 'general', count: 0}`；
  - 否则用 `image_tags` 自连接找共现最多的 3 个标签；
  - 源标签在库里不存在时返回空数组。

### 画师

#### `internal_artist_list` — `GET /api/artists` 【已实测】

| 参数 | 服务端行为（`app/api/artists/route.ts`） |
| :--- | :--- |
| `page` | 回落 1（`:7`） |
| `limit` | 回落 50，夹到 ≤100（`:8`） |

按画师标签的使用计数降序（`:16`）。返回 `{"success": true, "artists": [...], "pagination": {page, limit, total, pages}}`
（**没有 `has_next`**）。每行：`_id`、`tagId`（都是字符串）、`tagName`、`claimedByUserId`、
`claimedByUsername`、`verified`、`avatarUrl`、`bannerUrl`、`bio`、`socials`（对象，缺失时空对象）、
`postCount`（来自 `tags.count`）、`createdAt`。

#### `internal_artist_show` — `GET /api/artists/:tagName` 【源码对齐】

- 路径参数是**画师标签名**（同样接受空格/下划线变体），且标签的 `type` 必须是 `artist`，
  否则 404 `Artist not found`（`app/api/artists/[tagName]/route.ts:18-24`）。
- 返回 `{"success": true, "tag": {_id, id, name, type, count}, "artist": {...} | null,
  "reviews": {count, averages: {trust, quality, communication, pricing}}}`：
  `artist` 是画师资料行（`_id`/`tagId` 字符串、`tagName`、认领与验证字段、`avatarUrl`、`bannerUrl`、`bio`、
  `socials`、`createdAt`），标签存在但还没有资料行时为 `null`；`averages.pricing` 在无人打该项时是 `null`，
  其余平均分无评价时为 `0`。
- 更新资料是"已验证画师本人"的 `PATCH`，不在本库范围内。

#### `internal_artist_wiki` — `GET /api/artists/:tagName/wiki` 【源码对齐】

- 返回 `{"success": true, "wiki": {...} | null}`：`content`、`infobox`（自由结构）、
  `lastEditedBy`（编辑者用户名）、`lastEditedAt`、`editCount`（服务端只存最近 50 条历史，长度即它）。
  该画师还没有 wiki 时 `wiki` 为 `null`；画师标签本身不存在时 404（`app/api/artists/[tagName]/wiki/route.ts:16-33`）。
- 编辑 wiki 是登录后的 `POST`，不在本库范围内。

#### `internal_artist_reviews` — `GET /api/artists/:tagName/reviews` 【源码对齐】

- 返回 `{"success": true, "reviews": [...]}`，按创建时间降序；每行 `_id`（字符串）、`userId`（账号 id）、
  `username`、`ratings`（`trust`/`quality`/`communication` 必有、`pricing` 可选，各 1-5）、`comment`（可为 null）、
  `createdAt`。画师标签不存在 404（`app/api/artists/[tagName]/reviews/route.ts:16-38`）。
- 提交评价是登录后的 `POST`（每人每画师一条，冲突则覆盖），不在本库范围内。

### 用户

#### `internal_user_list` — `GET /api/users?username=` 【源码对齐】

- **这个集合路径实际是"按用户名查单个用户"**，`username` 必填，缺失 400
  （`app/api/users/route.ts:11-16`）；没有"列出全部用户"的模式。
- 先查本地 `users` 表（不区分大小写），**没有账号服务兜底**：查不到就是 404。
- 返回 `{"success": true, "user": {id, username, avatarUrl, bannerUrl, rank, createdAt, isPremium, isVerified}}`；
  其中 `bannerUrl`、`isPremium`、`isVerified` 需要服务端用内部 service key 调 `accounts.serika.dev`
  （`:30-47`，5 秒超时，失败静默降级），所以它们可能是空/`false` 而其余字段正常，**按尽力而为理解**。

#### `internal_user_show` — `GET /api/users/:id` 【源码对齐】

- 路径参数是**账号 id**（`users.id`，TEXT 主键），不是用户名、不是公开序号。
- 本地有该行就直接返回 `{"success": true, "user": {id, username, avatarUrl, rank, createdAt}}`；
  本地没有时服务端带内部 service key 调账号服务，把结果 **upsert 进本地 `users` 表**（`lib/db.ts` 的
  `ON CONFLICT (id) DO UPDATE`，`app/api/users/[id]/route.ts:60-68`）再返回。这个写入是服务端在镜像自己的
  账号服务，不需要调用方会话，方法仍是匿名读。
- 账号服务也不认识该 id 时 404。

#### `internal_user_activity` — `GET /api/users/:id/activity` 【源码对齐】

- 路径参数可以是账号 id，**也可以是用户名**：服务端先按 id 查，查不到再按用户名不区分大小写重查
  （`app/api/users/[id]/activity/route.ts:14-24`）；两者都没有 404。
- `type`：`all`（回落值，两段都返回）、`likes`、`comments`；**其他值返回 `{"success": true}`，两段都没有**。
- 返回 `{"success": true, "likes": [...], "comments": [...]}`，只含请求的段，每段最多 50 条：
  - `likes` 是该用户的**点赞（upvote）**列表，元素是图片对象，带 `id`/`dbid`/`_id`、`sequential_id`/`sequentialId`、
    `thumbnailUrl`、`tags` 等列表别名；
  - `comments` 每行 `_id`、`content`、`createdAt`、`image`（`{sequentialId, thumbnailUrl}`，图片行已消失时为 `null`）。

## 站内面排除项（有路由，但本库不封方法）

| 路由 | 动词 | 为什么不封 |
| :--- | :--- | :--- |
| `/api/images/:id/artist-status` | GET | **会话语义探针**：匿名时 `getCurrentUser()` 返回 null 就直接回 `{"success": true, "canCommentAsArtist": false, "artistTags": []}`，**不读任何公开资源**；只有登录后才有意义（`app/api/images/[id]/artist-status/route.ts:11-20`） |
| `/api/images/:id/user-interaction` | GET | 私有交互状态：匿名恒定返回 `{"success": true, "vote": null, "isFavorited": false}`，同样只有登录后才有信息 |
| `/api/images/:id/comments` | POST | 发表评论需要登录 |
| `/api/images/:id` | PATCH / DELETE | 编辑/删除是写操作，不属于本轮站内匿名读取范围 |
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

官方 `image_batch` 虽用 POST，但属于批量读取；`upload` 与 `image_delete` 才是资源写操作。
它们均需要 API key，本轮只做源码对齐，详见 [serika-api.md](serika-api.md)。

## 验证状态

站内面 14 个方法中，**4 个路由已用本轮客户端实际运行**，其余 10 个仅源码对齐。
本轮共执行 8 次匿名请求（4 个站内 + 4 个官方 v1），输入、真实响应摘要及命令见
[verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。不把历史 401 请求算作本轮调用。

**有历史匿名线上证据（2026-09-15，经代理 `proxy-host:port`，记录在 [verification.md](verification.md)）**：

| 路由 | 结果 | 对应方法 |
| :--- | :--- | :--- |
| `GET /api/images` | 200 | `internal_image_list` |
| `GET /api/images/:id` | 200 | `internal_image_show` |
| `GET /api/tags` | 200 | `internal_tag_list` |
| `GET /api/artists` | 200 | `internal_artist_list` |
| `GET /api/v1` / `stats` / `users?limit=1` | 200 | 官方面（另有 `random/400/400/image.png` 返回 PNG） |
| `GET /api/v1/{images,images/:id,tags,tags/:name,trending,search,random,users/:id}` | 401 | 官方面缺 key 时的边界 |

**仅源码对齐、本轮未实测**：`internal_image_comments`、`internal_tag_show`、`internal_tag_autocomplete`、
`internal_tag_complementary`、`internal_artist_show`、`internal_artist_wiki`、`internal_artist_reviews`、
`internal_user_list`、`internal_user_show`、`internal_user_activity`。它们的分支、字段与错误码来自
`Serika.art/app/api/**/route.ts` 的逐一核对，**没有被请求验证过**，站点也随时可能改这些未版本化路由。

**成功路径未实测**：官方面所有需 key 的 12 个方法（既包括读，也包括上传/删除；本轮不索要 key、
不发这些请求）。站内会话写操作与私有交互不实现，也未实测。

契约来源可追溯性：本地只读 clone `Serika.art/`（HEAD `ef11dd12`），本页行号引用均为
`app/api/...`、`lib/...` 下的实际文件行；数据库字段语义来自 `lib/db.ts:387-543`。

继续阅读：[官方 v1 API 参考](serika-api.md) · [客户端用法](serika.md) · [配置](configuration.md) ·
[错误处理](errors.md) · [线上验证状态](verification.md)。
