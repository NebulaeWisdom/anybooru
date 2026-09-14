# SerikaART API 面与端点清单

本文按 SerikaART 站点应用源码（本地只读 clone `Serika.art/`）整理官方 `/api/v1` 面，是
`Serika` 客户端 `SerikaApi_Mixin`（`pybooru/api_serika.py`）原生方法的路由来源。

**权威顺序**：`app/api/v1/**/route.ts` 控制器 + `lib/apiAuth.ts` + `lib/contentFilters.ts`
> 站内文档页 `app/api-docs/endpoints.ts` / `page.tsx`。后者只覆盖 10 个动词，且在 ID 语义与
错误码上与控制器矛盾，逐条见[文档与源码矛盾](#文档与源码矛盾)。

> **稳定性分级**：本文全部条目都是**官方版本化**的 `/api/v1`
> （`app/api/v1/route.ts` 自述 `SerikaART API 1.0.0`，`/api-docs` 承诺 "All endpoints are
> versioned under `/api/v1`"）。同一应用的**站内未版本化** `/api/*`（前端自用，无兼容承诺）
> 由 [站内能力与路由参考](serika-capabilities.md#站内逐路由) 单独记录，不混用稳定性等级。

## 验证状态

* **本轮（2026-09-15）没有做任何新的 key 实测**：用户没有站点 API key，也不申请 key；因此
  **所有需要 key 的路由一律是"源码对齐、未实测"**，本文不会把源码推断写成实测结论。
* 匿名可达的**历史实测事实**（2026-09-15 由主 agent 执行，代理 `proxy-host:port`，非本轮新增请求）：

  | 结果 | 路由 |
  | :--- | :--- |
  | `200` | `/api/v1`、`/api/v1/stats`、`/api/v1/users?limit=1`、`/api/v1/random/400/400/image.png`（PNG 字节） |
  | `401` | `/api/v1/images`、`/api/v1/images/:id`、`/api/v1/tags`、`/api/v1/tags/:name`、`/api/v1/trending`、`/api/v1/search`、`/api/v1/random`、`/api/v1/users/:id` |

* 上述 `401` 历史事实仅证明那些无 key 请求被拒绝，**不能**证明成功响应形状。
  `image_similar`、`image_batch`、`image_delete`、`upload` 只有源码认证依据，没有任何线上调用记录。
* 本轮经 `Serika` 实际运行的匿名示例见 [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)，
  包含上述 4 个公开 v1 入口；需要 key 的 **12 个方法成功路径均未实测**，本轮没有向它们发请求。
* 本文不含任何模拟成功、客户端校验或重试逻辑；客户端把参数原样交给服务端。

## 路由规模

`app/api/v1/` 下是 **15 个 `route.ts` 文件 / 16 个导出动词**（`images/[id]/route.ts` 一个文件
导出 `GET` + `DELETE`）：

| # | 路径 | 动词 | 客户端方法 | 文档页是否收录 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `/api/v1` | GET | `api_index` | 否 |
| 2 | `/api/v1/images` | GET | `image_list` | 是 |
| 3 | `/api/v1/images/:id` | GET | `image_show` | 是 |
| 4 | `/api/v1/images/:id` | DELETE | `image_delete` | 是 |
| 5 | `/api/v1/images/:id/similar` | GET | `image_similar` | 是 |
| 6 | `/api/v1/batch/images` | POST | `image_batch` | 否 |
| 7 | `/api/v1/random` | GET | `random_list` | 是 |
| 8 | `/api/v1/random/:width/:height/image.png` | GET | `random_image` | 是 |
| 9 | `/api/v1/tags` | GET | `tag_list` | 是 |
| 10 | `/api/v1/tags/:name` | GET | `tag_show` | 否 |
| 11 | `/api/v1/users` | GET | `user_list` | 否 |
| 12 | `/api/v1/users/:id` | GET | `user_show` | 是 |
| 13 | `/api/v1/search` | GET | `search` | 否 |
| 14 | `/api/v1/trending` | GET | `trending` | 否 |
| 15 | `/api/v1/stats` | GET | `stats` | 是 |
| 16 | `/api/v1/upload` | POST | `upload` | 是 |

## 全局契约

### 认证与权限

* 头：`Authorization: Bearer sk_serika_*`（首选）或 `X-API-Key: sk_serika_*`
  （`lib/apiAuth.ts`）。客户端配置了 key 就恒发 `Authorization: Bearer`；**没有** cookie
  会话写入流程，也不支持密码登录。
* 失败梯度（`validateApiKey`）：缺 key → `401`；前缀不是 `sk_serika_` → `401` "Invalid API
  key format"；hash 查不到或 `is_active = FALSE` → `401`；`expires_at` 已过 → `401`；
  限流 → `429`；权限不足 → `403` "Missing required permission: ..."。
* 8 种权限：`images:read`、`images:write`、`tags:read`、`tags:write`、`users:read`、
  `random:read`、`images:delete`、`upload`；新 key 的默认权限是
  `images:read` + `tags:read` + `users:read` + `random:read`（无 write/delete/upload）。
* `images:write` 与 `tags:write` 在 `/api/v1` **没有任何路由读取**：本面没有图片或标签的改/建
  路由，这两个权限位在 v1 无消费者（站内未版本化面不用 API key，不能据此推断它们的用途）。

### 响应信封

* 成功（`apiResponse`）：`{"success": true, "data": <payload>, "meta": {"timestamp": ..., ...}}`。
  客户端用 `envelope="data"` 返回 `data`，把整个 `meta` 放进 `last_call["meta"]`。
* 错误（`apiError`）：`{"success": false, "error": <文本>, "code": <代码>}`，HTTP 状态与
  `code` 语义同步。客户端抛 `PybooruHTTPError`，原始正文在 `.data`（非 JSON 正文时 `.data`
  为 `None`，见 [errors.md](errors.md)）。
* **三个例外**：

  | 路由 | 形状 | 客户端处理 |
  | :--- | :--- | :--- |
  | `GET /api/v1` | 裸对象（无 `success`/`data`/`meta`） | 无 `envelope`，原样返回 |
  | `GET /api/v1/users` | `{"success": true, "users": [...], "pagination": {...}}`，**没有 `data`，也没有 `meta.timestamp`** | `envelope="users"`，返回 `users`，`last_call["meta"]["pagination"]` 里是分页 |
  | `GET /api/v1/random/:w/:h/image.png` | 图片字节 | `binary=True`，返回 `bytes`，元数据在 `last_call["headers"]` |

* 常见 `code`：`UNAUTHORIZED`(401/403/429)、`INVALID_ID`(400)、`NOT_FOUND`(404)、
  `TAG_NOT_FOUND`(404)、`INVALID_QUERY`(400)、`INVALID_REQUEST`/`INVALID_IDS`/
  `TOO_MANY_IDS`(400)、`FORBIDDEN`(403，仅删图越权)、`INTERNAL_ERROR`(500)、
  `MISSING_FILE`/`INVALID_FILE_TYPE`/`FILE_TOO_LARGE`/`MISSING_TAGS`/`TOO_MANY_TAGS`/
  `INVALID_RATING`(400，上传)。

### 限流

* 实际执行按 **API key 行上的 `api_keys.rate_limit` 列**（固定 60 秒窗口，计数放在缓存里），
  不是按 rank 现算。
* 文档里的 rank 表（user 60 / premium 120 / moderator 120 / admin 1000；`/api-docs` 页另有
  owner 10000）只体现在**发 key 时**的钳位：`app/api/keys/route.ts` 取
  `Math.min(Math.max(10, rateLimit), maxRateLimit)`，`maxRateLimit` 按 rank 为
  60/120/1000/10000。
* 超限返回 HTTP `429`，但**正文 `code` 是 `UNAUTHORIZED`**（路由把 `validateApiKey` 的失败统一
  包装成 `apiError(error, statusCode, 'UNAUTHORIZED')`）。只有未被任何 v1 路由使用的
  `withApiAuth` 辅助函数才会写 `RATE_LIMITED`，文档页写的是 `RATE_LIMITED`——以控制器为准。

### ID 语义

| 路由参数 | 代码里的比较 | 含义 |
| :--- | :--- | :--- |
| `/api/v1/images/:id`（GET/DELETE） | `WHERE i.id = $1` | **内部 `images.id`（SERIAL bigint）** |
| `/api/v1/images/:id/similar` | `WHERE id = $1 AND deleted = FALSE AND unlisted = FALSE` | **内部 `images.id`** |
| `/api/v1/batch/images` 的 `ids` | `WHERE i.id = ANY($1)` | **内部 `images.id`** |

* 顺序号是另一列 `images.sequential_id`（`UNIQUE`，由 `counters` 表发放），响应里叫
  `post_id`；`GET /api/v1/images/:id` 与 similar 的数组项还会额外给 `sequential_id`。
  列表/详情里的 `id` 与 `dbid` 都是内部 bigint 的字符串形式。
* 文档页把 `images/:id` 写成 "accepts the sequential ID (post_id)"，**与控制器矛盾**；
  两者数值不同（历史实测样本：`id 7323837` ↔ `post_id 4237836`）。
* 用户标识符是**文本**主键 `users.id`（`TEXT PRIMARY KEY`，非数字），`/api/v1/users/:id`
  先试 `id = $1`，再退回大小写不敏感的 `LOWER(username) = LOWER($1)`；标签名由服务端
  `toLowerCase().trim()` 后精确匹配。
* 客户端对 `:id`、`:name`、`:identifier`、`:width`、`:height` 每个路径段单独
  `quote(str(value), safe='')`。

### 参数编码

* 查询串与 multipart 表单走同一套 Rails 编码：布尔→`true`/`false`（小写），`None` 直接不发送，
  列表→`key[]`；没有文件时请求体是 JSON（`data` 原样结构化，显式空数组保留）。
* 服务端判定布尔用的是字符串比较（`=== 'true'`），所以 `ai`、`no_ai`、`blur`、`grayscale`、
  `match_size`、上传的 `is_ai_generated` 只有落成小写字符串才会生效。
* **CSV 参数**（`tags`、`ratings`、`exclude_tags`）只接受逗号分隔的**字符串**，客户端不做数组
  转换，也不解析 Rails 数组语法。
* 分页一律放 `meta.pagination`（`page`、`limit`、`total`、`pages`，除 `/api/v1/users` 外还有
  `has_next` / `has_prev`）。

### 内容过滤（`contentFilters.ts`）

* `publicImageFilter()` = `deleted = FALSE AND unlisted = FALSE`，出现在 `images` 列表、
  `random` 两种、`search`、`trending`、`stats`、`tags/:name` 的样本与计数里。
  **它不作用于 `images/:id`(GET) 与 `batch/images`**：这两条按 ID 直查，软删/隐藏的图照样返回；
  `similar` 则对源图和候选图各自加这组条件。
* `ratingFilter(ratings)` 先 `normalizeRatings`：过滤掉非法值后若为空，**回退为
  `['safe']`**；恰好等于全部三个合法值时不加条件（无过滤）。因此"不传 `ratings`"等于
  "只看 safe"，不是"全部"。
* 只有接受 `ratings` 的路由会用到这个助手：`images` 列表、`random` 两种、`search` 的 images 段、
  `trending`。`images/:id`(GET) 不加 rating 条件；`similar` 强制与源图同 rating；
  `tags/:name` 的样本图硬编码 `safe`；`batch/images` 无 rating 条件。

## 端点清单（官方 v1）

### 1. `api_index`

| 项 | 值 |
| :--- | :--- |
| 方法 | `api_index()` |
| HTTP | `GET /api/v1` |
| 权限 | 公开（无 key） |
| 实测 | 匿名 `200`（历史事实） |
| 返回 | 裸对象：`name`、`version`、`description`、`documentation`、`endpoints`、`authentication`、`rate_limits` |

`endpoints` 覆盖 `images`（list/get/delete）、`random`（metadata/image）、`tags`（list/get）、
`users`（**只有单用户** `GET /api/v1/users/:id_or_username`）、`search`、`upload`、`stats`
七个面；它**没有**列出 `batch/images`、`users` 列表和 `trending`，以[路由规模](#路由规模)表为准。
`rate_limits` 是文档性数据，不含 owner 行，运行时并不按 rank 限流。

### 2. `image_list`

| 项 | 值 |
| :--- | :--- |
| 方法 | `image_list(page=None, limit=None, tags=None, ratings=None, sort=None, ai=None, q=None, user_id=None, min_width=None, min_height=None)` |
| HTTP | `GET /api/v1/images` |
| 权限 | `images:read` |
| 状态 | 官方 v1，源码对齐，**未实测**（匿名 `401` 已实测） |
| 返回 | `data` = 图片数组；`meta.pagination` = `page/limit/total/pages`（**空结果分支没有 `has_next`/`has_prev`**；标签全部解析不到时 `total: 0`），只有非空分支才带这两个字段 |

参数（服务器默认/钳位写在括号里，客户端不代做）：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `page` | int | 页码（`<1` 被抬到 1） |
| `limit` | int | 每页数量（钳位 1..100，默认 20） |
| `tags` | str | 逗号分隔标签名，**交集**：必须全部命中。先解析标签名：**部分**存在 → `404 TAG_NOT_FOUND`（同一名字在列表里重复也算缺失，因为查询每个名字只回一行）；**全部**不存在 → `200` + `data: []`；名字都存在但无图 → 同样 `200` + `data: []` |
| `ratings` | str | 逗号分隔 `safe`/`questionable`/`explicit`；非法值被剔除、空则回退 `safe`；三个全给 = 不加过滤 |
| `sort` | str | `newest`(默认)/`oldest`/`popular`(upvotes↓,views↓)/`favorites`/`views`/`random`（非确定）；未知值按 `newest` |
| `ai` | bool | 仅 AI 生成 |
| `q` | str | 对标签名、`description`、`username` 做子串匹配 |
| `user_id` | str | 上传者 ID（文本 `users.id`） |
| `min_width` / `min_height` | int | 最小宽/高（`>0` 才生效） |

返回字段（`image_list` 及下文同类"图片对象"）：`id`/`dbid`（内部 bigint 字符串）、
`post_id`（`sequential_id`）、`url`、`thumbnail_url`、`width`、`height`、`file_size`、
`content_type`、`rating`、`is_ai_generated`、`source`、`description`、`tags`
（`[{name, type}]`，**不带** `shared_tags`）、`stats`（`upvotes`/`downvotes`/`favorites`/
`views`）、`user`（`{id, username}`，`id` 可为 `null`，用户名回退 `"Anonymous"`）、
`created_at`、`updated_at`。

### 3. `image_show`

| 项 | 值 |
| :--- | :--- |
| 方法 | `image_show(image_id)` |
| HTTP | `GET /api/v1/images/:id` |
| 权限 | `images:read` |
| 状态 | 官方 v1，源码对齐，**未实测**（匿名 `401` 已实测） |
| 参数 | `image_id`：**内部 `images.id`**（文档写 sequential，矛盾）；非数字 → `400 INVALID_ID`；不存在 → `404 NOT_FOUND` |
| 返回 | 单张图片对象 + `original_filename`、`source`、`description`、`stats.score`(upvotes-downvotes)、`stats.comments`(评论计数)、`updated_at` |

副作用：每次成功调用都会把 `views` 加一（非阻塞，失败只记日志）。该路由**不加**
`deleted`/`unlisted` 与 rating 条件，软删/隐藏的图按 ID 仍能取到。

### 4. `image_delete`

| 项 | 值 |
| :--- | :--- |
| 方法 | `image_delete(image_id)` |
| HTTP | `DELETE /api/v1/images/:id` |
| 权限 | `images:delete`（发 key 时仅 admin/owner 可被授予） |
| 状态 | 官方 v1，**写操作，源码对齐，未实测** |
| 参数 | `image_id`：**内部 `images.id`**；非数字 → `400 INVALID_ID`；不存在 → `404 NOT_FOUND`；不属自己且 rank 不是 `admin`/`owner` → `403 FORBIDDEN` |
| 返回 | `{"deleted": true, "id": "<内部 id>"}` |

一个事务里删除 `votes`、`favorites`、`comments`、`image_tags` 与 `images` 行，并给受影响标签的
`count` 减一。注意匿名上传（`user_id` 为 `NULL`）的图片没有属主，属主校验被跳过。

### 5. `image_similar`

| 项 | 值 |
| :--- | :--- |
| 方法 | `image_similar(image_id, limit=None)` |
| HTTP | `GET /api/v1/images/:id/similar` |
| 权限 | `images:read` |
| 状态 | 官方 v1，源码对齐，**未实测**（`similar` 不在匿名边界实测清单里，需 key 的 `401` 只是源码行为） |
| 参数 | `image_id`：源图的**内部 `images.id`**；源图必须 `deleted = FALSE AND unlisted = FALSE`，否则 `404 NOT_FOUND`。`limit`：钳位 1..50，默认 10 |
| 返回 | `{"source_id": <路径段原文>, "similar": [...], "count": <int>}` |

算法是标签交集：只找**同 rating** 的公开图，按共享标签数降序、再按 upvotes 降序。每项含
`id`/`dbid`、`post_id`、`sequential_id`、`url`、`thumbnail_url`、`width`、`height`、`rating`、
`is_ai_generated`、`shared_tags`（int）、最多 10 个 `tags`、`stats`（无 `score`/`comments`）。
无结果不是错误：`similar: []`、`count: 0`。

### 6. `image_batch`

| 项 | 值 |
| :--- | :--- |
| 方法 | `image_batch(ids)` |
| HTTP | `POST /api/v1/batch/images` |
| 权限 | `images:read` |
| 状态 | 官方 v1（文档页未收录），源码对齐，**未实测** |
| 参数 | `ids`：图片 ID 数组（**内部 `images.id`**），作为 JSON 体 `{"ids": [...]}` 发送；字符串或整数都可被 `parseInt` |
| 约束 | 非数组或空 → `400 INVALID_REQUEST` "ids must be a non-empty array"；超过 100 → `400 TOO_MANY_IDS`；全部无法解析 → `400 INVALID_IDS` |
| 返回 | `{"images": [...], "found": <int>, "requested": <int>}`，按请求顺序排列命中的项 |

每项与列表对象同构，但额外有 `sequential_id`，且匿名上传者时 `user` 为 `null`（不是 `Anonymous`）。
与 `image_show` 一样，这里**不加** `deleted`/`unlisted` 与 rating 条件。

### 7. `random_list`

| 项 | 值 |
| :--- | :--- |
| 方法 | `random_list(count=None, ratings=None, tags=None, exclude_tags=None, min_width=None, min_height=None, max_width=None, max_height=None, ai=None, no_ai=None)` |
| HTTP | `GET /api/v1/random` |
| 权限 | `random:read` |
| 状态 | 官方 v1，源码对齐，**未实测**（匿名 `401` 已实测） |
| 返回 | 生效 `count == 1` 时 `data` 是**单个对象**，否则是数组；`meta` 额外带 `count`（实际返回数）与 `requested` |

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `count` | int | 钳位 1..50，默认 1 |
| `ratings` | str | 同 `image_list` 的语义（空→`safe`，三个全给=不过滤） |
| `tags` | str | 逗号分隔，全部命中；**部分**名字不存在 → `404 TAG_NOT_FOUND`；全部不存在或交集为空 → `200` + `data: []` + `meta.message` |
| `exclude_tags` | str | 逗号分隔，命中其一即排除；未知标签在这里被**忽略**（不报错） |
| `min_width`/`min_height`/`max_width`/`max_height` | int | `>0` 才生效 |
| `ai` / `no_ai` | bool | `ai` 优先（`if ai … else if no_ai`） |

图片对象同 `image_list`。排序是 `ORDER BY RANDOM()`，不保证两次请求不同或去重。

### 8. `random_image`

| 项 | 值 |
| :--- | :--- |
| 方法 | `random_image(width, height, fit=None, format=None, quality=None, tags=None, ratings=None, exclude_tags=None, blur=None, grayscale=None, ai=None, no_ai=None, match_size=None, aspect_tolerance=None)` |
| HTTP | `GET /api/v1/random/:width/:height/image.png` |
| 权限 | **公开（无 key）**——该文件不调用 `validateApiKey` |
| 实测 | 匿名 `200` 且正文是 PNG（历史事实，`400/400`） |
| 返回 | **原始字节**（`binary=True`）；`Content-Type` 依 `format`；元数据在响应头 |

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `width` / `height` | int（路径段） | 16..8000；越界或非数字 → `400` 纯文本（非 JSON 正文） |
| `fit` | str | `cover`(默认)/`contain`/`fill`/`inside`/`outside`；未知值回退 `cover` |
| `format` | str | `png`(默认)/`jpeg`/`jpg`/`webp`；未知值输出 PNG |
| `quality` | int | 钳位 1..100，默认 85；文档说只对 jpeg/webp 生效，控制器对 PNG 也传了 `quality`（sharp 的 PNG quality 需要 palette 才生效，未实测差异） |
| `tags` | str | 逗号分隔。该路由**从不因标签报错**：只有"每个名字都存在**且**存在同时含全部标签的图"时才加上标签条件，否则条件被整体丢弃（代码注释写"退回占位图"，实际是把 where 条件跳过），可能返回**不含**这些标签的随机图 |
| `ratings` | str | 缺省即 `['safe']`；非法值被剔除后回退 `safe` |
| `exclude_tags` | str | 逗号分隔排除；名字不存在则不排除任何图，排除条件只在名字存在且命中图时才构造 |
| `blur` / `grayscale` | bool | 高斯模糊（σ≈10）／灰度 |
| `ai` / `no_ai` | bool | `ai` 优先 |
| `match_size` | bool | 优先挑"不小于请求尺寸（候选下限取 `min(请求尺寸, 400)`）且宽高比在 `aspect_tolerance` 内"的图；找不到再退回纯随机 |
| `aspect_tolerance` | float | 宽高比容差，服务器默认 0.2 |

响应头：`X-Image-Id`、`X-DBID`（内部 id）、`X-Post-Id`（sequential）、`X-Original-Width`、
`X-Original-Height`、`X-Rating`、`Cache-Control`。**无匹配时返回 `200` 的灰色占位 PNG**
（`#808080`），所以占位图与命中只能靠响应头区分（只有命中才带 `X-*` 标识）。控制器内部出错
（抓源图、缩放失败等）走 `catch`：**同样是 `200`**，但返回红色占位 PNG（`#C83232`）且
`Cache-Control: no-cache`；只有连占位图都生成不出来时才是 `500` 纯文本
`Error generating image`。命中时会给该图 `views` 加一。

### 9. `tag_list`

| 项 | 值 |
| :--- | :--- |
| 方法 | `tag_list(page=None, limit=None, q=None, type=None, sort=None, min_count=None)` |
| HTTP | `GET /api/v1/tags` |
| 权限 | `tags:read` |
| 状态 | 官方 v1，源码对齐，**未实测**（匿名 `401` 已实测） |
| 返回 | `data` = `[{id, name, type, count, created_at}]`；`meta.pagination` 与图片列表同构（含 `has_next`/`has_prev`） |

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `page` | int | `<1` 抬到 1 |
| `limit` | int | 钳位 1..500，默认 100 |
| `q` | str | 名称子串（`ILIKE`） |
| `type` | str | 仅接受 `general`/`artist`/`character`/`copyright`/`meta`；**其它值被静默忽略**（等于不筛类型） |
| `sort` | str | `count`(默认)/`name`/`newest`/`oldest`；未知值按 `count` |
| `min_count` | int | `>0` 时筛 `count >=` |

`count` 是标签表里存的计数（删除图片时会减一），与 `tag_show` 的重算值可能不同。

### 10. `tag_show`

| 项 | 值 |
| :--- | :--- |
| 方法 | `tag_show(name)` |
| HTTP | `GET /api/v1/tags/:name` |
| 权限 | `tags:read` |
| 状态 | 官方 v1（文档页未收录），源码对齐，**未实测**（匿名 `401` 已实测） |
| 参数 | `name`：服务端 `toLowerCase().trim()` 后精确匹配；不存在 → `404 NOT_FOUND` |
| 返回 | `{id, name, type, count, created_at, sample_images}` |

`count` 是**重算**的公开图计数（与 `tag_list` 的存储值不同），`sample_images` 是最多 5 项
`safe` 且公开的图（`{id, thumbnail_url, rating}`，按 upvotes 降序；`thumbnail_url` 为空时回退
`url`）。

### 11. `user_list`

| 项 | 值 |
| :--- | :--- |
| 方法 | `user_list(page=None, limit=None, q=None, sort=None)` |
| HTTP | `GET /api/v1/users` |
| 权限 | **公开（无 key）**：该文件不调用 `validateApiKey` |
| 实测 | 匿名 `200`（历史事实，`?limit=1`） |
| 返回 | `envelope="users"`：方法返回 `users` 数组，`last_call["meta"]["pagination"]` = `{page, limit, total, pages}`（**无** `has_next`/`has_prev`，也**无** `meta.timestamp`） |

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `page` | int | `<1` 抬到 1 |
| `limit` | int | 钳位 1..100，默认 50 |
| `q` | str | 用户名子串（`ILIKE`） |
| `sort` | str | `newest`(默认, `created_at DESC, id DESC`)/`oldest`/`alphabetical`/`alphabetical-reverse`/`uploads`/`uploads-asc`；未知值按 `newest` |

用户对象：`_id`、`id`（同一个值的两个名字）、`username`、`avatarUrl`、`rank`、`createdAt`、
`uploadCount`（只数公开图）。**字段名是 camelCase**，与本面其它端点风格不同。
`^user_[A-Za-z0-9]{6}$` 形式的占位账号被排除，所以这里的 `total` 小于
`stats()['totals']['users']`。

### 12. `user_show`

| 项 | 值 |
| :--- | :--- |
| 方法 | `user_show(identifier)` |
| HTTP | `GET /api/v1/users/:id` |
| 权限 | `users:read` |
| 状态 | 官方 v1，源码对齐，**未实测**（匿名 `401` 已实测） |
| 参数 | `identifier`：先按 `WHERE id = $1`（文本主键），再退回 `LOWER(username) = LOWER($1)`；都查不到 → `404 NOT_FOUND` |
| 返回 | `{id, username, avatar_url, rank, stats: {images, total_upvotes, total_views}, created_at}` |

`stats` 只统计该用户的图片表行（不过滤 `deleted`/`unlisted`，也不排除 `NULL` 属主情形）。

### 13. `search`

| 项 | 值 |
| :--- | :--- |
| 方法 | `search(q, type=None, limit=None, ratings=None)` |
| HTTP | `GET /api/v1/search` |
| 权限 | `images:read` |
| 状态 | 官方 v1（文档页未收录），源码对齐，**未实测**（匿名 `401` 已实测） |
| 返回 | `{images: [...], tags: [...], users: [...]}`，只包含被请求的分支；`meta` 回显 `query` 与 `type` |

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `q` | str | 必填；长度 < 2 → `400 INVALID_QUERY` |
| `type` | str | `all`(默认)/`images`/`tags`/`users`；**其它值一个分支都不跑**，返回空对象 `{}` |
| `limit` | int | 每段上限，钳位 1..50，默认 10 |
| `ratings` | str | 只影响 `images` 段（语义同 `image_list`） |

`images` 段按 upvotes 降序，命中条件是"标签名含 `q`"或 `description`/`username` 含 `q`；每项只有
`id`/`dbid`/`post_id`/`url`/`thumbnail_url`/`width`/`height`/`rating`/最多 5 个标签名/`stats{upvotes,
views}`。`tags` 段是 `{id, name, type, count}`；`users` 段是 `{id, username, avatar_url, rank}`
（字符串 `id`）。

### 14. `trending`

| 项 | 值 |
| :--- | :--- |
| 方法 | `trending(period=None, limit=None, ratings=None)` |
| HTTP | `GET /api/v1/trending` |
| 权限 | `images:read` |
| 状态 | 官方 v1（文档页未收录），源码对齐，**未实测**（匿名 `401` 已实测） |
| 返回 | `{period, images: [...], tags: [...]}` |

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `period` | str | `day`(默认)/`week`/`month`，对应 24h/7d/30d；未知值按 `day` |
| `limit` | int | 图片条数，钳位 1..50，默认 20 |
| `ratings` | str | **默认 `safe`**；非法值剔除后回退 `safe`；三个全给 = 不过滤 |

热度分 `upvotes*3 + favorites*5 + views*0.1`，按分数降序。图片项含 `trend_score`（取整）、
最多 5 个标签名、`uploaded_at`（即 `created_at`）。`tags` 是这批图里出现最多的**最多 20 个**
标签（`id`/`name`/`type`/`trending_count`/`total_count`），**不受 `limit` 影响**。无结果时是
`{period, images: [], tags: []}`。

### 15. `stats`

| 项 | 值 |
| :--- | :--- |
| 方法 | `stats()` |
| HTTP | `GET /api/v1/stats` |
| 权限 | **公开（无 key）**：该文件不调用 `validateApiKey` |
| 实测 | 匿名 `200`（历史事实） |
| 返回 | `{totals: {images, tags, users}, images_by_rating: {safe, questionable, explicit}, images_by_type: {ai_generated, non_ai}, activity: {uploads_last_24h}}` |

`totals.images` 只数公开图；`totals.tags`、`totals.users` 是整表计数（**含** `user_list` 排除的
占位账号）。

### 16. `upload`

| 项 | 值 |
| :--- | :--- |
| 方法 | `upload(file, tags, rating, is_ai_generated=None, source=None, description=None)` |
| HTTP | `POST /api/v1/upload` |
| 权限 | `upload`（发 key 时仅 moderator/admin/owner 可被授予；路由本身只查权限位） |
| 状态 | 官方 v1，**写操作，源码对齐，未实测** |
| 编码 | **唯一的 multipart 端点**：文件键 `file`，其余字段是表单字段 |
| 返回 | 新图对象（`id`/`dbid`、`post_id`、`url`、`thumbnail_url`、`width`、`height`、`file_size`、`content_type`、`rating`、`is_ai_generated`、`tags`、`created_at`），`meta.message` = "Image uploaded successfully" |

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `file` | File | 必填；服务端只收 `image/jpeg`/`image/png`/`image/gif`/`image/webp` 且 ≤ 50MB。缺失 → `400 MISSING_FILE`，类型错 → `INVALID_FILE_TYPE`，过大 → `FILE_TOO_LARGE`。**必须传 requests 的 `(filename, fileobj, content_type)` 三元组并显式给 MIME**：裸文件对象不发 part 的 `Content-Type`，被解析成 `application/octet-stream` 后会被拒；文件对象生命周期由调用者负责 |
| `tags` | str | 必填；**原样发送的字符串**，服务端两种格式都吃：JSON 数组文本（`[{"name":"x","type":"general"}]` 或纯字符串数组）或逗号分隔。空/超 100 → `400 MISSING_TAGS` / `TOO_MANY_TAGS`；未知 `type` 回退 `general`；名字按 `lowercase + 空白→下划线` 归一后再查/建标签 |
| `rating` | str | 必填；仅 `safe`/`questionable`/`explicit`，否则 `400 INVALID_RATING` |
| `is_ai_generated` | bool | 服务端用"表单值 == `'true'`"判定；控制器**还接受** `isAIGenerated` 拼写，本客户端只发 `is_ai_generated` |
| `source` | str | 来源 URL，可空字符串 |
| `description` | str | 描述，可空字符串 |

服务端在存储上传原图与 320x320 JPEG 缩略图后，于一个事务里建/取标签、从 `counters`
领 `imageSequentialId`、插入 `images`（`upvotes/downvotes/favorites/views` 全 0，
`deleted`/`unlisted` 为 `FALSE`）并累加标签 `count`。存储后端由 `USE_LOCAL_STORAGE`
环境变量在部署侧决定（B2 或本地），与本客户端无关。

## 文档与源码矛盾

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
| 8 | 未提二进制细节 | `random/:w/:h/image.png` 无匹配时返回 `200` 灰色占位 PNG，控制器内部异常也是 `200` 但为红色占位 PNG（只有占位失败才 `500` 纯文本）；越界尺寸返回 `400` **纯文本**正文 |
| 9 | `quality` 只对 jpeg/webp 生效 | 控制器对 PNG 也传了 `quality`（sharp 的 PNG quality 需 palette 才生效，未实测输出差异） |
| 10 | upload "Requires moderator rank or above" | 路由只看 `upload` 权限位；moderator+ 门槛在 `/api/keys` 发 key 时执行（`images:delete` 同理只给 admin/owner） |
| 11 | 未文档化的字段名 | `users` 列表用 camelCase（`avatarUrl`/`uploadCount`/`createdAt`）且同时给 `_id` 与 `id`；`tags/:name` 的 `count` 是重算值；`stats.totals.users` 含占位账号 |
| 12 | `/api/v1/route.ts` 的 `endpoints` 自述 | 未列 `batch/images`、`users` 列表、`trending`；`users` 面只写单用户路由（`tags/:name`、`search`、`stats`、`upload` 有列） |

## 客户端方法签名一览

```python
api_index()
image_list(page=None, limit=None, tags=None, ratings=None, sort=None, ai=None,
           q=None, user_id=None, min_width=None, min_height=None)
image_show(image_id)
image_delete(image_id)
image_similar(image_id, limit=None)
image_batch(ids)
random_list(count=None, ratings=None, tags=None, exclude_tags=None,
            min_width=None, min_height=None, max_width=None, max_height=None,
            ai=None, no_ai=None)
random_image(width, height, fit=None, format=None, quality=None, tags=None,
             ratings=None, exclude_tags=None, blur=None, grayscale=None,
             ai=None, no_ai=None, match_size=None, aspect_tolerance=None)
tag_list(page=None, limit=None, q=None, type=None, sort=None, min_count=None)
tag_show(name)
user_list(page=None, limit=None, q=None, sort=None)
user_show(identifier)
search(q, type=None, limit=None, ratings=None)
trending(period=None, limit=None, ratings=None)
stats()
upload(file, tags, rating, is_ai_generated=None, source=None, description=None)
```

全部是 `self.request(...)` 的一行薄封装：普通返回原始 JSON；`envelope="data"` 拆 `data` 并把
`meta` 放进 `last_call["meta"]`；`envelope="users"` 专用于 `user_list`；`random_image` 用
`binary=True` 取字节。未覆盖的路由（例如将来新增的 v1 动词）直接用
`Serika.request(method, path, params=..., data=..., files=...)` 访问。
