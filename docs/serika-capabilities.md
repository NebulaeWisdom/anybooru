# Serika 能力总览：先确认你在读哪一面

**不知道有哪些接口，先看这页。** 逐条签名、参数与返回字段见[方法参考](serika-api.md)；
源码出处、逐条线上状态与排除清单见[契约审计附注](serika-contract-notes.md)。

* **Serika 是六家族中的独立引擎**：与 Danbooru、Moebooru、e621ng、Zerochan、Gelbooru 都不同。站点是 Next.js
  自研的 "Danbooru-style" 图站，对外**没有** `/posts.json`、`/post.json` 这类 Danbooru 路由；
  Serika 自己仓库里对 `/posts.json` 的调用是它作为 Danbooru **消费者**的导入器，不能反推它提供
  Danbooru 接口。
* **两套接口**：
  * **官方 `/api/v1/*`**：带版本号，站点自述为 "SerikaART API 1.0.0"；用
    `Authorization: Bearer sk_serika_*`（服务端也收 `X-API-Key`），成功正文是
    `{"success": true, "data": ..., "meta": {...}}`；共 16 个方法，4 个公开、12 个要 key。
  * **站内 `/api/*`**：**没有版本号**、没有对外文档，是 Serika 网页前端自己调用的路由；其中一批读
    接口不需要任何凭据，本库统一用 `internal_` 前缀暴露，共 14 个方法，返回原始 JSON 不做字段提取。
* **认证是第三种形态**：官方面用 API key；站内面正常靠会话凭据（`session_token` cookie 或账号服务
  签发的会话 token）。**本库只实现 API key 与站内匿名读，不实现浏览器 cookie 登录**，也不提供获取、
  配置或刷新会话身份的方法。
* **库只负责发 API 请求**，不是采集器：不自动保存图片、不自动翻页；官方随机图片方法直接返回
  Python `bytes`。
* **有接口不等于本站已启用，也不等于都实测过**：文末统一汇总实测边界，逐条状态与排除项在
  [契约审计附注](serika-contract-notes.md#路由清单与逐条状态)。

## 按目的找入口

下表里的 `client` 指 `Serika('serika')` 的实例；最简调用栏写的就是可直接抄的字面参数（`3`、`'safe'`、
`'dairi'` 都是真值），`post_id`、`user_id` 这类要从实际响应里取（来源写在括号里）。

| 我想做什么 | 用哪个方法 | 最简调用形态 | 是否需要凭据 |
| :--- | :--- | :--- | :--- |
| 按标签、评分、排序浏览图片 | `internal_image_list`：站内图片列表，标签取交集、评级过滤、12 种排序 | `client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')` | 匿名可读 |
| 用同一批条件但走版本化接口 | 官方 `image_list`：多出 `user_id`、子串搜索与 `total` 等分页字段 | `client.image_list(page=1, limit=3, tags='blue archive', ratings='safe')` | 需 `images:read` 权限的 key |
| 看一张图的详情 | `internal_image_show`：按**公开序号**读取 | `client.internal_image_show(4237836)`（序号取自列表响应的 `post_id`） | 匿名可读 |
| 看某张图的评论 | `internal_image_comments`：按公开序号，按时间升序 | `client.internal_image_comments(4237836)` | 匿名可读 |
| 检索标签、查单个标签 | `internal_tag_list`（按计数降序）/ `internal_tag_show`（空格与下划线变体都能命中） | `client.internal_tag_list(limit=3)`；`client.internal_tag_show('highres')` | 匿名可读 |
| 输入时给标签补全、找搭配标签 | `internal_tag_autocomplete`（按完全匹配 > 前缀 > 词边界 > 计数排序）/ `internal_tag_complementary`（最多 3 条） | `client.internal_tag_autocomplete('blue arch', limit=5)`；`client.internal_tag_complementary('blue archive')` | 匿名可读（都是 POST 只读查询） |
| 查画师页、简介与评价 | `internal_artist_list`（按画师标签计数降序）/ `internal_artist_show` / `internal_artist_wiki` / `internal_artist_reviews` | `client.internal_artist_list(page=1, limit=3)`；`client.internal_artist_show('dairi')`；`client.internal_artist_wiki('dairi')`；`client.internal_artist_reviews('dairi')` | 匿名可读 |
| 按用户名或账号 id 查用户 | `internal_user_list`（按用户名）/ `internal_user_show`（按账号 id） | `client.internal_user_list('Giru')`；`client.internal_user_show(account_id)`（`account_id` 取自前一个响应的 `user.id`） | 匿名可读 |
| 看某用户点赞过什么、发过什么评论 | `internal_user_activity`：两段各最多 50 条 | `client.internal_user_activity('Giru', type='likes')` | 匿名可读 |
| 站点统计、随机图（官方公开面） | 官方 `stats`（总量 / 评级 / AI / 24 小时上传）、`random_image`（返回图片字节） | `client.stats()`；`client.random_image(400, 400, format='png', ratings='safe')` | 匿名可用 |
| 热门、搜索、随机图描述（官方面） | 官方 `trending`（`upvotes*3 + favorites*5 + views*0.1` 排序）、`search`（一次搜图片 / 标签 / 用户）、`random_list`（`data` 里是图片对象） | `client.trending(period='week', limit=5)`；`client.search('blue archive', type='images')`；`client.random_list(count=2, ratings='safe')` | 需 key（分别是 `images:read`、`images:read`、`random:read`） |
| 上传图片（官方面） | 官方 `upload`：唯一 multipart 端点 | `client.upload(('sample.png', picture, 'image/png'), tags='1girl', rating='safe')`（`picture` 是以 `'rb'` 打开的文件对象） | 需 `upload` 权限，发 key 时只授予 moderator/admin/owner |
| 删除图片、批量读取（官方面） | 官方 `image_delete`（事务删依赖行并减标签计数）/ `image_batch`（JSON 体一次取最多 100 张） | `client.image_delete(7323837)`；`client.image_batch([7323837, 7323836])` | 分别需 `images:delete` / `images:read` |
| 调没有原生封装的路由 | `client.request('GET', 'api/v1/stats')`，见[通用请求入口](serika.md#通用请求入口) | `client.request('GET', 'api/v1/stats', envelope='data')` | 看该路由本身 |

**三个容易选错的地方**：① 站内 `/api/images/:id` 用**公开序号**（响应里的 `post_id`），官方
`/api/v1/images/:id` 用**内部图片 id**（响应里的 `id` / `dbid`），详见下面的
[ID 语义](#id-语义四个同名不同义的数字)；② 两面的 `tags` / `ratings` 都是**逗号分隔字符串**，
不是数组，也不是 Danbooru 的搜索表达式；③ 带评级过滤的列表、随机、搜索与热门路由，不传 `ratings`
时只返回 `safe`（详情与 similar 不适用这条泛化），这是服务端行为，不是客户端补的。

## 认证边界

| 身份 / 凭据 | 能做什么 | 主要边界 |
| :--- | :--- | :--- |
| 匿名（不带任何凭据） | 全部 14 个 `internal_*` 读方法；官方 `api_index`、`stats`、`user_list`、`random_image` | 其余 12 个官方方法要 key；其中 8 个 GET 有匿名 `401` 的历史记录，另 4 个动词只有源码依据 |
| 官方 API key（`sk_serika_*`，`Authorization: Bearer` 或 `X-API-Key`） | 官方 `/api/v1/*` 中与该 key 权限相符的读写 | 权限共 8 种：`images:read/write/delete`、`tags:read/write`、`users:read`、`random:read`、`upload`；新建 key 默认只有四个 `*:read`。限流按 key 自己的限流值执行，不按 rank 现算，超限 HTTP `429`，但正文 `code` 与非超限失败一样是 `UNAUTHORIZED` |
| 站内会话（`session_token` cookie 或账号服务签发的会话 token） | 站内写操作与私有交互 | **本库不实现会话登录与会话写方法**；官方 API key 不等于会话 token，两者不能互相替代 |

* 站内 14 个方法的共同点是：**存在一条不需要会话就走得通的分支**，本页列出的方法走的都是这条。
  多数控制器完全不看会话；`internal_image_show` 是例外——它会**有条件地**读一次会话以放宽可见性，
  没有凭据时走的正是公开分支。
* 站点根中间件只保护上传页与用户页（`/upload/:path*`、`/user/:path*`），**不拦截 `/api/*`**；
  每个站内路由的可见性完全由它自己的控制器决定。

## ID 语义：四个同名不同义的数字

| 标识（响应字段） | 含义 | 谁在用它 |
| :--- | :--- | :--- |
| **内部图片 id**：`id` / `dbid` / `_id` | 图片在站点内部的自增编号（后两个是字符串形式） | 官方 `/api/v1/images/:id`、`/similar`、`/batch/images`；评论里的 `imageId`；点赞列表元素里的 `id` |
| **公开序号**：`post_id` / `sequential_id` / `sequentialId` | 图片对外的公开编号 | **站内** `/api/images/:id` 与 `/api/images/:id/comments` 的路径段、`/api/users/:id/activity` 里对图片的引用；二进制随机图的 `X-Post-Id` |
| **账号 id**：站内 `user_id` / `userId`，官方用户对象里的 `id` / `_id` | 账号服务的账号编号（文本，形如 `692ad0df032c62f79b57a08d`） | 上传者的 `userId`、评论的 `userId`、投票与收藏的归属、两个站内用户路由、画师认领字段 |
| **标签内部 id** | 标签在站点内部的编号 | `image_tags`、画师资料、评论与画师标签的关联；站内对外一律用**标签名**访问 |

2026-09-15 实测的差异：同一个对象的 `id = 7323837` 与 `post_id = 4237836` 是两个不同的数字，
不要拿一个去查另一个接口。评论的 `_id` 是评论自己的内部编号，也不是公开序号。
数据库列定义、列名与上游行号见[附注](serika-contract-notes.md#id-语义sql)。

## 官方 v1 面：16 个方法

**成功正文**是 `{"success": true, "data": <内容>, "meta": {"timestamp": ...}}`；失败既改 HTTP 状态码，
也在正文给 `{"success": false, "error": <文本>, "code": <代码>}`。两个例外：`GET /api/v1` 直接返回
自述对象；`GET /api/v1/users` 返回 `{"success": true, "users": [...], "pagination": {...}}`，没有
`data`。另外二进制随机图返回的是图片本身。

| 方法（路由） | 做什么 | 凭据 |
| :--- | :--- | :--- |
| `api_index`（`GET /api/v1`） | 自述：名称 `SerikaART API`、版本 `1.0.0`、endpoint 地图、认证与限流说明 | 公开 |
| `image_list`（`GET /api/v1/images`） | 图片列表：标签交集、评级、6 种排序、`ai`、子串 `q`、上传者 `user_id`、宽高下限 | `images:read` |
| `image_show`（`GET /api/v1/images/:id`） | 按**内部 id** 取单图整行：含 `original_filename`、`stats.score`、评论计数，并让 `views` 加一 | `images:read` |
| `image_delete`（`DELETE /api/v1/images/:id`） | 按内部 id 删图：一个事务删掉 votes/favorites/comments/image_tags/images 并减标签计数 | `images:delete` |
| `image_similar`（`GET /api/v1/images/:id/similar`） | 找**同评级**的公开相似图，按共享标签数、再按 upvotes 排序，每项带 `shared_tags` | `images:read` |
| `image_batch`（`POST /api/v1/batch/images`） | 一次按最多 100 个内部 id 批量取图，`ids` 走 JSON 体，命中项按请求顺序 | `images:read` |
| `random_list`（`GET /api/v1/random`） | 随机图的描述 JSON：`count` 为 1 时 `data` 是对象，否则是数组 | `random:read` |
| `random_image`（`GET /api/v1/random/:width/:height/image.png`） | 随机图的**字节**，按给定尺寸与格式返回；尺寸走路径段（16..8000） | 公开 |
| `tag_list`（`GET /api/v1/tags`） | 标签列表：名称子串、5 种类型、4 种排序、最小计数 | `tags:read` |
| `tag_show`（`GET /api/v1/tags/:name`） | 单个标签 + 最多 5 张 safe 样本图；`count` 是重算的公开图计数 | `tags:read` |
| `user_list`（`GET /api/v1/users`） | 用户目录：camelCase 字段，排除 `user_xxxxxx` 占位账号，分页在 `last_call` | 公开 |
| `user_show`（`GET /api/v1/users/:id_or_username`） | 按账号 id 或用户名取单个用户及其上传统计 `{images, total_upvotes, total_views}` | `users:read` |
| `search`（`GET /api/v1/search`） | 一次搜图片 / 标签 / 用户，只返回被请求的分支；`q` 至少 2 个字符 | `images:read` |
| `trending`（`GET /api/v1/trending`） | 一段时间的热门图与热门标签；标签部分最多 20 条且不受 `limit` 影响 | `images:read` |
| `stats`（`GET /api/v1/stats`） | 站点统计：总量、按评级、按 AI、最近 24 小时上传 | 公开 |
| `upload`（`POST /api/v1/upload`） | 上传图片（唯一 multipart 端点），返回新图对象与 `meta.message` | `upload` |

方法签名、逐参数表与返回字段见[方法参考](serika-api.md#官方-v1索引统计用户目录)；
官方文档只收录其中 10 个动词，我们的清单以控制器为准。

## 站内面（未版本化）：14 个匿名读方法

站内面没有版本号、没有兼容承诺，形状可能随时改。共同点：路径以 `api/` 开头、**没有 `.json` 后缀**；
返回原始 JSON（一般是 `{"success": true, ...}` 加资源键，失败是
`{"success": false, "error": ..., "code": ...}`）；查询参数是扁平字典，服务端字段名大小写敏感
（线上是 `userId`、`hideAI`），本库只在 Python 形参层用下划线；`tags` / `ratings` 是逗号分隔字符串；
不传的参数不会被客户端补成服务端默认值；站内面**没有游标分页**，翻页一律是页码。

| 方法（路由） | 做什么 | 返回里最关键的东西 |
| :--- | :--- | :--- |
| `internal_image_list`（`GET /api/images`） | 图片列表：标签交集、评级、12 种排序、`ai` / `hide_ai`、子串 `query`、上传者 `user_id` 或 `username` | `images` 数组（内部 id 与 `post_id` 成对出现）与 `pagination{page,limit,total,pages,has_next}` |
| `internal_image_show`（`GET /api/images/:id`） | 按**公开序号**取单图详情；匿名看不到软删/未列出的图（与不存在一样是 404） | `image` 对象，比列表多 `original_filename`、`content_type`、`source`、`deleted`、`unlisted`、`updated_at` |
| `internal_image_comments`（`GET /api/images/:id/comments`） | 按公开序号读某图的评论，按创建时间升序 | `comments` 数组，每行含 `_id`、`imageId`（内部 id）、`userId`、`content`、`parentId`、`asArtist` |
| `internal_tag_list`（`GET /api/tags`） | 标签列表，按使用计数降序 | `tags`（标签表整行）与 `grouped`（同一批行按 `type` 分桶） |
| `internal_tag_show`（`GET /api/tags/:name`） | 按名读单个标签，原名、空格换下划线、下划线换空格三种形态都试 | `tag{_id,id,name,type,count,createdAt}` |
| `internal_tag_autocomplete`（`POST /api/tags`） | POST 只读：输入补全建议，排序是完全匹配 > 前缀 > 词边界 > 计数 | `suggestions`（标签行，内部 `score` 已去掉；结果缓存 120 秒） |
| `internal_tag_complementary`（`POST /api/tags/complementary`） | POST 只读：搭配标签建议，最多 3 条 | `suggestions[{name,type,count}]`；命中硬编码关系表时库里没有的名字补成 `count: 0` |
| `internal_artist_list`（`GET /api/artists`） | 画师页列表，按画师标签的使用计数降序 | `artists`（`tagName`、`postCount`、`verified`、`avatarUrl`、`socials` 等）与**没有 `has_next`** 的分页 |
| `internal_artist_show`（`GET /api/artists/:tagName`） | 画师页：标签必须是 `artist` 类型 | `tag`、`artist`（标签存在但没有资料行时是 `null`）、`reviews{count, averages}` |
| `internal_artist_wiki`（`GET /api/artists/:tagName/wiki`） | 画师 wiki | `wiki`（`content`、`infobox`、`lastEditedBy`、`editCount`），没写过时为 `null` |
| `internal_artist_reviews`（`GET /api/artists/:tagName/reviews`） | 画师评价，最新的在前 | `reviews`，每行 `ratings{trust,quality,communication,pricing}` 与 `comment` |
| `internal_user_list`（`GET /api/users?username=`） | **按用户名查单个用户**，该路径**不是**列出全部用户；`username` 必填 | `user{id,username,avatarUrl,bannerUrl,rank,createdAt,isPremium,isVerified}`（后三个字段是尽力而为） |
| `internal_user_show`（`GET /api/users/:id`） | 按**账号 id** 查用户；本地没有时由服务端向账号服务补齐并写回本地表 | `user{id,username,avatarUrl,rank,createdAt}` |
| `internal_user_activity`（`GET /api/users/:id/activity`） | 用户的点赞与评论，每段最多 50 条；路径参数也可以传用户名 | `likes`（图片对象数组）与 `comments`（含 `image{sequentialId,thumbnailUrl}`） |

参数、服务端默认值与逐路由分支见[附注的站内逐路由](serika-contract-notes.md#站内逐路由游标之外的实现细节)，
逐参数表见[方法参考](serika-api.md#站内匿名读共同模式)。

## 本库不提供的能力

* **站内会话登录**：没有 cookie 登录，也没有会话 token 的获取 / 配置 / 刷新。官方 API key 与会话
  token 是两种凭据，前者不能代替后者。
* **站内写操作与私有交互**：发评论、投票、收藏、改标签类型、改画师资料 / wiki / 评价、画师认领、
  图片编辑与删除、举报与客服、API key 管理与审核/管理面都没有方法。
* **只有登录才有意义的接口与站点广告位**：匿名时只返回常量的探测接口（如"能否以画师身份评论"、
  私有交互状态）与需要第三方广告网络的接口都不封装。
* **自动采集**：不自动翻页、不自动保存图片、不自动重试、不做引擎自动识别。库也不做形状猜测：
  官方那套 `data` / `meta` 只在两个明确的 `envelope` 模式下拆，站内 JSON 原样返回。
* 逐条排除理由（含每个路由的动词）见[附注的排除项](serika-contract-notes.md#排除项有路由但本库不封方法)。

## 边界与未实测

* 站内 14 个方法中，本轮用客户端实际运行过 4 个（图片列表、图片详情、标签列表、画师列表）；
  官方 v1 实际运行过 4 个公开入口（索引、统计、用户目录、随机图片字节），合计 **8 次匿名请求、
  8 个 HTTP `200`**，命令与真实输出见
  [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。
* **官方 12 个需 key 的方法成功路径未实测**（用户没有也不申请 key）；站内其余 10 个方法只有源码
  对齐，没有发过线上请求。
* 自托管部署、认证成功路径、权限与限流、上传与删除、灰色/红色占位 PNG 的错误分支、参数组合均
  未实测；逐条状态见[附注的路由清单](serika-contract-notes.md#路由清单与逐条状态)。

继续阅读：[方法参考](serika-api.md) · [客户端用法](serika.md) · [契约审计附注](serika-contract-notes.md) ·
[配置](configuration.md) · [错误处理](errors.md) · [线上验证状态](verification.md)。
