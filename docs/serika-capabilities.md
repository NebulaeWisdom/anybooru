# Serika 能力总览：先确认你在读哪一面

**不知道有哪些接口，先看这页。** 逐条签名与返回见 [方法参考](serika-api.md)，
契约出处、逐条状态与排除清单见 [契约审计附注](serika-contract-notes.md)。

- **Serika 是四家族中的独立引擎**：与 Danbooru、Moebooru、e621ng 均不同。项目自述是 Next.js 自研的
  "Danbooru-style" 图站，对外**没有** `/posts.json`、`/post.json` 这类 Danbooru 契约；
  它自己仓库里对 `/posts.json` 的调用是 Serika 作为 Danbooru **消费者**的导入器，
  不能反推它提供 Danbooru 接口。
- **两个 API 面**：
  - **官方面 `/api/v1/*`**：自称 "SerikaART API 1.0.0"，带版本号，用 `Authorization: Bearer
    sk_serika_*`（服务端也收 `X-API-Key`）认证，成功响应是 `{success, data, meta}` 信封，16 个方法。
  - **站内面 `/api/*`**：**未版本化**、没有对外文档，是 Serika 网页前端自己调用的路由。
    其中一批读接口不需要任何凭据，本库统一用 `internal_` 前缀暴露，14 个方法，原始 JSON 不拆信封。
- **认证形态是第三种**：官方面用 API key，站内面正常靠会话凭据（`session_token` cookie 或账号服务
  签发的会话 token）。**本库只实现 API key 与站内匿名读，不实现浏览器 cookie 登录**，
  也不提供获取、配置或刷新会话身份的方法。
- **库负责 API 请求**，不是自动采集器：不自动保存图片、不自动翻页；官方随机图片方法直接返回 `bytes`。
- **有接口不等于本站已启用，也不等于都实测过**：本页文末统一汇总实测边界，逐条状态与排除项在
  [契约审计附注](serika-contract-notes.md#路由清单与逐条状态)。

## 按目的找入口

下表的 `c` 是按配置创建的 `Serika` 客户端；查询取自 `examples.serika` 或应用自定配置，
`post_id`、`tag_name`、`username`、`user_id` 从实际响应取得，不是写死在库里的默认输入。

| 我想做什么 | 能力与方法 | 最简调用形态 | 是否需要凭据 |
| :--- | :--- | :--- | :--- |
| 按标签、评分、排序浏览图片（无 key） | `internal_image_list`：站内图片列表，标签取交集、评分过滤、多种排序 | `c.internal_image_list(**example['image_query'])` | 匿名可读 |
| 按同样条件浏览图片（有 key，版本化契约） | 官方 `image_list`，参数与错误码更完整 | 见 [serika-api.md](serika-api.md#官方图片) | 需 `images:read` 权限的 key |
| 看一张图的详情 | `internal_image_show`：按**公开序号**读取 | `c.internal_image_show(post_id)` | 匿名可读 |
| 看某张图的评论 | `internal_image_comments` | `c.internal_image_comments(post_id)` | 匿名可读 |
| 检索标签、查单个标签 | `internal_tag_list` / `internal_tag_show` | `c.internal_tag_list(**example['tag_query'])`；`c.internal_tag_show(tag_name)` | 匿名可读 |
| 输入时给标签补全、找搭配标签 | `internal_tag_autocomplete` / `internal_tag_complementary` | `c.internal_tag_autocomplete(tag_name)`；`c.internal_tag_complementary(tag_name)` | 匿名可读（都是 POST 只读查询） |
| 查画师页、简介与评价 | `internal_artist_list` / `internal_artist_show` / `internal_artist_wiki` / `internal_artist_reviews` | `c.internal_artist_show(artist_tag_name)`；`c.internal_artist_wiki(artist_tag_name)` | 匿名可读 |
| 按用户名或账号 id 查用户 | `internal_user_list`（按用户名）/ `internal_user_show`（按账号 id） | `c.internal_user_list(username)`；`c.internal_user_show(user_id)` | 匿名可读 |
| 看某用户点赞过什么、发过什么评论 | `internal_user_activity` | `c.internal_user_activity(user_id)` | 匿名可读 |
| 站点统计、热门、搜索、随机图（官方面） | 官方 `stats`、`trending`、`search`、`random_list`、`random_image` 等 | 见 [serika-api.md](serika-api.md) | `stats` 与二进制随机图匿名可用，其余要求 key |
| 上传图片（官方面） | 官方 `upload`（multipart） | 见 [serika-api.md](serika-api.md#上传) | 需 `upload` 权限，发 key 时限制可获此权限的等级 |
| 删除图片、批量读取（官方面） | 官方 `image_delete` / `image_batch` | 见 [serika-api.md](serika-api.md#官方图片) | 分别需 `images:delete` / `images:read` |

**三个容易选错的地方**：① 站内 `/api/images/:id` 用**公开序号**（响应里的 `post_id`），官方
`/api/v1/images/:id` 用**内部图片 id**（响应里的 `id`/`dbid`）（详见下面的 [ID 语义](#id-语义四个同名不同义的数字)）；
② 站内面的 `tags`/`ratings` 是**逗号字符串**，不是数组；③ 使用评级过滤的列表、随机、搜索与热门路由
不传 `ratings` 时只返回 `safe`（详情、similar 等不适用这条泛化），这是服务端默认，不是客户端兜底。

## 认证边界

| 身份 / 凭据 | 能做什么 | 主要边界 |
| :--- | :--- | :--- |
| 匿名（无任何凭据） | 全部 `internal_*` 读方法；官方 `api_index`、`user_list`、`stats`、`random_image` | 其余 12 个官方方法需 key：其中 8 个 GET 的匿名 `401` 有历史记录，另 4 个动词仅源码依据 |
| 官方 API key（`sk_serika_*`，`Authorization: Bearer` 或 `X-API-Key`） | 官方 `/api/v1/*` 中与该 key 权限相符的读写 | 权限集是 `images:read/write/delete`、`tags:read/write`、`users:read`、`random:read`、`upload`；默认 key 只有 `*:read`。限流按 key 自身的限流值执行（不按 rank 现算），超限 HTTP `429`，但正文 `code` 与非超限失败一样是 `UNAUTHORIZED`，要连 HTTP 状态一起看 |
| 会话（`session_token` cookie 或账号服务签发的会话 token） | 站内写操作与私有交互 | **本库不实现会话登录与会话写方法**；官方 API key 不等于会话 token |

- 站内匿名读方法的共同点是：**存在一条不需要会话就走得通的分支**，本页方法走的都是这条。
  多数 handler 完全不看会话；`internal_image_show` 是例外——它会**有条件地**读取会话以放宽可见性，
  没有凭据时走的正是公开分支。
- 站点根中间件只保护上传页与用户页，**不拦截 `/api/*`**；每个站内路由的可见性完全由它自己决定。

## ID 语义：四个同名不同义的数字

| 标识（响应字段） | 含义 | 谁在用它 |
| :--- | :--- | :--- |
| **内部图片 id**：`id` / `dbid` / `_id` | 图片在站点内部的自增编号（后两个是字符串形式） | 官方 `/api/v1/images/:id`、`/similar`、`/batch/images`；评论的 `imageId`；点赞列表里的 `id` |
| **公开序号**：`post_id` / `sequential_id` / `sequentialId` | 图片对外的公开编号 | **站内** `/api/images/:id`、`/api/images/:id/comments`、`/api/users/:id/activity` 的图片引用；二进制随机图的 `X-Post-Id` |
| **账号 id**：站内 `user_id` / `userId`，官方用户对象里的 `id` / `_id` | 账号服务的账号编号（文本，形如 `692ad0df032c62f79b57a08d`） | 上传者 `userId`、评论 `userId`、投票/收藏归属、站内用户路由、画师认领 |
| **标签内部 id** | 标签在站点内部的编号 | `image_tags`、画师资料、评论的画师标签关联；站内对外一律用**标签名**访问 |

实测过的差异：同一个对象的 `id = 7323837` 与 `post_id = 4237836` 是两个不同的数字，
不要拿一个去查另一个接口。评论的 `_id` 是评论自己的内部编号，也不是公开序号。
数据库列定义、列名与上游行号见[附注](serika-contract-notes.md#id-语义sql)。

## 官方 v1 面：16 个方法

**成功信封**是 `{"success": true, "data": ..., "meta": {"timestamp": ...}}`；错误既改 HTTP 状态码，
也在正文给 `{"success": false, "error": ..., "code": ...}`。两个例外：`/api/v1`（index）直接返回 API
自述对象；`/api/v1/users` 列表返回 `{"success": true, "users": [...], "pagination": {...}}`，
没有 `data`；此外二进制随机图返回图片本身。

| 方法 | 做什么 |
| :--- | :--- |
| `api_index` | API 自述：名称、版本、endpoint 地图、认证与限流说明（公开） |
| `image_list` | 图片列表：标签交集、评级、排序、AI 过滤、子串搜索、尺寸下限 |
| `image_show` | 按**内部 id** 取单图详情（含 `stats.score` 与评论计数） |
| `image_delete` | 按内部 id 删除图片及其依赖行 |
| `image_similar` | 按内部 id 找同评级的公开相似图（标签交集排序） |
| `image_batch` | 按多个内部 id 一次批量取图（JSON 体，最多 100 个） |
| `random_list` | 随机图片的元数据列表（有 `count`/尺寸/标签/评级/排除条件） |
| `random_image` | 随机图片的**字节**，按给定尺寸与格式返回（公开） |
| `tag_list` | 标签列表：名称子串、类型、排序、最小计数 |
| `tag_show` | 单个标签 + 最多 5 张 safe 样本图（`count` 为重算值） |
| `user_list` | 用户目录（公开；camelCase 字段，排除占位账号） |
| `user_show` | 按账号 id 或用户名取单个用户及其上传统计 |
| `search` | 一次搜图片/标签/用户（只返回被请求的分支） |
| `trending` | 一段时间的热门图与热门标签 |
| `stats` | 站点统计：总量、按评级、按 AI、最近 24h 上传（公开） |
| `upload` | 上传图片（multipart，需 `upload` 权限） |

方法签名、参数与返回形状见 [方法参考](serika-api.md#官方-v1共同模式)；
官方文档只收录其中 10 个动词，我们的清单以控制器为准。

## 站内面（未版本化）：14 个匿名读方法

站内面没有版本号、没有兼容承诺，形状可能随时改。共同点：

- 路径以 `api/` 开头，**没有 `.json` 后缀**，也不接受 Danbooru/Moebooru 那种格式后缀；
- 响应不统一拆封：一般是 `{"success": true, ...}` 加各自资源键（`images`、`image`、`comments`、
  `tags`、`artists`、`user` 等），分页在返回体里；失败也用 `{"success": false, "error", "code"}`；
- 查询参数是扁平字典，服务端字段名**大小写敏感**（`userId`、`hideAI`）；本库只在 Python 形参层用
  下划线，例如 `hide_ai=` 对应线上 `hideAI=`；
- `tags`、`ratings` 是**逗号分隔字符串**，不是数组；布尔按小写 `true`/`false` 发送；
- 不传的参数不会被客户端补成服务端默认值；默认值、钳位与回落一律由服务端决定；
- 站内面**没有游标分页**，翻页一律是页码。

| 方法 | 做什么 |
| :--- | :--- |
| `internal_image_list` | 站内图片列表：标签交集、评级、多种排序、AI 开关、子串搜索、上传者过滤 |
| `internal_image_show` | 按**公开序号**取单图详情（匿名看不到软删/未列出的图） |
| `internal_image_comments` | 按公开序号读某图的评论 |
| `internal_tag_list` | 标签列表（按使用计数降序，另给按类型分桶的 `grouped`） |
| `internal_tag_show` | 按名读单个标签（空格与下划线变体都能命中） |
| `internal_tag_autocomplete` | POST 只读：输入补全建议 |
| `internal_tag_complementary` | POST 只读：搭配标签建议（最多 3 条） |
| `internal_artist_list` | 画师页列表（按画师标签计数降序） |
| `internal_artist_show` | 画师页：标签、资料行（可能为 `null`）与评价汇总 |
| `internal_artist_wiki` | 画师 wiki（没写过时为 `null`） |
| `internal_artist_reviews` | 画师评价（最新在前） |
| `internal_user_list` | 按用户名查用户（该路径**不是**列出全部用户） |
| `internal_user_show` | 按账号 id 查用户（本地没有时会由服务端向账号服务补齐） |
| `internal_user_activity` | 用户的点赞与评论，每段最多 50 条 |

参数、服务端默认值、缓存影响与逐路由分支见
[附注的站内逐路由](serika-contract-notes.md#站内逐路由游标之外的实现细节)。

## 本库不提供的能力

- **站内会话登录**：没有 cookie 登录、没有会话 token 的获取/配置/刷新。官方 API key 与会话 token
  是两种凭据，前者不能代替后者。
- **站内写操作与私有交互**：发评论、投票、收藏、改标签类型、改画师资料/wiki/评价、画师认领、
  图片编辑与删除、举报与客服、API key 管理与审核/管理面都没有方法。
- **会话语义探针与站点广告位**：匿名时只返回常量的接口（如"能否以画师身份评论"、私有交互状态）
  与需要第三方广告网络的接口都不封。
- **自动采集**：不自动翻页、不自动保存图片、不自动重试、不做引擎自动识别。
- 逐条排除理由（含每个路由的动词）见[附注的排除项](serika-contract-notes.md#排除项有路由但本库不封方法)。

## 边界与未实测

- 站内 14 个方法中，本轮用客户端实际运行过 4 个（图片列表、图片详情、标签列表、画师列表）；
  官方 v1 实际运行过 4 个公开入口（index、stats、用户目录、随机图片字节），合计 **8 次匿名请求、
  8 个 HTTP `200`**，命令与真实输出见
  [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。
- **官方 12 个需 key 的方法成功路径未实测**（用户没有也不申请 key）；站内其余 10 个方法仅源码对齐。
- 自托管部署、认证成功路径、权限/限流、上传/删除、PNG 占位错误分支与参数组合均未实测；
  逐条状态见[附注的路由清单](serika-contract-notes.md#路由清单与逐条状态)。

继续阅读：[方法参考](serika-api.md) · [客户端用法](serika.md) · [契约审计附注](serika-contract-notes.md) ·
[配置](configuration.md) · [错误处理](errors.md) · [线上验证状态](verification.md)。
