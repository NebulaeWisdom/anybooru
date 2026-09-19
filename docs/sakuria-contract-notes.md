# Sakuria：接口依据、权限与排除项

本页供核对依据，不代替[客户端用法](sakuria.md)或[方法参考](sakuria-api.md)。
本类一共 **44 个原生方法**：**27 个匿名只读方法**加 **17 个 `/me/*` 账号路由透传**，
全部只做 `GET` 路由与 JSON 原样返回；没有认证方法、没有写方法、没有媒体下载。

依据只有**匿名响应**：没有上游源码、没有官方 API 页面、没有 OpenAPI。本页把
「本轮真实跑过的」（L）与「输入文档候选、本轮没测到的」（T）分开写，
**T 的部分集中在[边界与未实测](#边界与未实测)，不进正文结论**。

## 资料来源与等级

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **L：本轮匿名只读实测** | 54 次直接 HTTP 观察，逐条 URL、状态与字段见[验证记录](verification.md#sakuria匿名只读实测2026-09-19) | 27 个公共 JSON 路由各有样本；账号路由仅 `/me/likes` 两次拒绝。直接路由证据不等于运行过对应 Python 方法 |
| **T：输入文档（候选）** | 接入时收到的《Sakuria 接口文档（综合版）》，自称内容来自对同一主机的匿名 HTTP 实测，**没有可公开核对的发布链接**；文档自己也写明没有官方文档与 OpenAPI | 尚未复测的参数取值与默认值、完整枚举、错误码全集、权限现象、字段语义与那些怪行为。这些一律只列在[边界与未实测](#边界与未实测) |
| **没有 O / H 来源** | 无官方 API 页面、无 OpenAPI、无服务端源码 | 输入文档记录 `/openapi.json`、`/docs`、`/swagger.json` 全部 `404`；本轮 `GET /` 的响应里 `docs` 就是占位仓库 `https://github.com/your-org/sakuria` |

三点必须记住：

1. **L 覆盖 27 个公共 JSON 路由及 `/me/likes` 的两次匿名拒绝**，
   没有账号成功样本；客户端方法实际执行范围另见验证记录。
2. **没有 L 的说法不当契约**：输入文档里的默认值、枚举、上限、错误码全集、字段语义都只算候选，
   集中在边界一节；不要用它们推断未测参数的行为。
3. **样本不是固定数据集**：多次搜索的计数、条数与 `hiddenCount` 不同，
   数字只作当时响应的例子，不据此推断变化原因。

## 44 个方法的逐条依据

「本轮 L」列只统计 54 次直接 HTTP 路由观察；不包含随后冒烟、示例的 15 次客户端请求。
其余 16 个账号路由本轮未请求。路径都接在 `https://sakuria-api.syarolia.com` 后面。

### 站点与配置（5，匿名）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `index()` | `GET /` | 1 | `200 {name:"sakuria-api", ok:true, docs:"https://github.com/your-org/sakuria"}` |
| `stats()` | `GET /stats` | 1 | `200 {newToday, totalIllusts, totalCreators, totalUsers}`，都是整数 |
| `health()` | `GET /healthz` | 1 | `200 {ok, releaseSha, releaseVersionId, checks:{…}}`，`checks` 含 `db`/`jwt`/`pxve`/`cache`/`cacheBackend`/`databaseDriver` |
| `app_config()` | `GET /app/config` | 1 | `200`，键含 `latestVersion`/`latestBuild`/`updateUrl`/`releaseNotes`/`updateAvailable`/`updateRequired`/`announcement`/`maintenance`/`flags`/`servers`（2 条）/`imageProxy`/`imageProxyPro`/`iap` |
| `ai_config()` | `GET /ai/config` | 1 | `200`，键含 `enabled`/`metaEnabled`/`novelEnabled`/`mangaEnabled`/`mangaInputMode`/`commentEnabled`/`cacheTtlDays`/`billingMode`/`models`（2 条） |

### 插画（5）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `illust_search(**params)` | `GET /search/illust` | 13 | page1/2/3 与 `size`/`sort`/`limit`/`type`/`mode`/`page=0` 各种组合；信封键 `items`/`page`/`pageSize`/`total`/`totalPages`/`hasMore`/`nextPage`/`hiddenCount` |
| `illust_show(illust_id, **params)` | `GET /illust/{illust_id}` | 3 | 存在 id `200` 裸对象；`/illust/0` → `404 {"error":"illust not found"}`；`/illust/abc` → `400 {"error":"invalid id"}` |
| `illust_comments(illust_id, **params)` | `GET /illust/{illust_id}/comments` | 1 | `200 {items:[2], hasMore:true}`，评论键 `id`/`author`/`text`/`repliesCount`/`likes`/`createdAt`/`timeLabel` |
| `illust_comment_replies(illust_id, comment_id, **params)` | `GET /illust/{illust_id}/comments/{comment_id}/replies` | 1 | `200 {items:[1]}`，只有 `items` |
| `illust_related(illust_id, **params)` | `GET /illust/{illust_id}/related` | 1 | `200 {items:[2]}`（`size=2`），只有 `items` |

### 用户（8）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `user_search(**params)` | `GET /search/user` | 3 | `q=mika` 的 page1/2/3：`items` 与 `total` 都是 6/12/21，各页 `id` 无重叠；信封只有 `items`/`total` |
| `user_show(user_id, **params)` | `GET /users/{user_id}` | 1 | 裸对象，键 `id`/`name`/`handle`/`accent`/`avatar`/`banner`/`stats`/`social`；`stats` 本轮非全 0 |
| `user_illusts(user_id, **params)` | `GET /users/{user_id}/illusts` | 2 | page1/2 各 45 条、`pageSize` 24、`nextPage` 3/4、`hiddenCount` 3、两页交集 23 |
| `user_novels(user_id, **params)` | `GET /users/{user_id}/novels` | 1 | `200` 24 条；`nextCursor` 是上游 `app-api.pixiv.net` 地址；item 带 `series` |
| `user_bookmarks(user_id, **params)` | `GET /users/{user_id}/bookmarks` | 2 | `page=1` 与 `page=2` 完整 JSON 相同（19 条、`nextCursor` `"9175901406"`、`hiddenCount` 5） |
| `user_followers(user_id, **params)` | `GET /users/{user_id}/followers` | 2 | page1/2 皆空 `items`，`page` 回显 1/2，`pageSize` 12，`hasMore` false |
| `user_series(user_id, **params)` | `GET /users/{user_id}/series` | 1 | 本轮为空 `items`，`pageSize` 24，`hasMore` false |
| `user_related(user_id, **params)` | `GET /users/{user_id}/related` | 1 | `200 {items:[12]}`，item 是 `{user, previews}` |

### 小说（4）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `novel_search(**params)` | `GET /search/novel` | 4 | page1 24 条（`total` 48）、page2 26 条（`total` 72）；`type=illust` → `400 unsupported_filter_for_scope field=type`；`ai=exclude` → `401 auth_required` |
| `novel_show(novel_id, **params)` | `GET /novels/{novel_id}` | 1 | 裸对象；本轮顶层 `text` 是空串，而 `document.text` 是 4 行 `[uploadedimage:…]` 标记，`document.uploadedImages` 4 条、`pixivImages` 为空 |
| `novel_comments(novel_id, **params)` | `GET /novels/{novel_id}/comments` | 1 | 本轮空集合，`hasMore` false |
| `novel_related(novel_id, **params)` | `GET /novels/{novel_id}/related` | 1 | 本轮空集合（`pageSize` 12、`total` 0、`hasMore` false） |

### 系列、特辑与标签（5）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `series_show(series_id, **params)` | `GET /series/{series_id}` | 2 | `198059` → 30 项 `items`、`total` 219、`hasMore` true；`12064` → 空 `items`、`total` 7 |
| `spotlight_list(**params)` | `GET /spotlight` | 1 | 一页 20 条而信封 `pageSize` 12、`hasMore` true；item 的 `works` 为空 |
| `spotlight_show(spotlight_id, **params)` | `GET /spotlight/{spotlight_id}` | 2 | `11971` 有 19 篇 `articles`、`works` 空、两个 related 的 `items` 空；`cover` 是以 `/` 开头的相对路径；`/spotlight/0` → `503 retryable:true` |
| `tag_illusts(tag, **params)` | `GET /tags/{tag}` | 1 | `blue` 与 `search/illust?q=blue` 同为 `page=1&size=24` 时分别 25 与 29 条、交集 25、`hiddenCount` 65 |
| `tag_search(**params)` | `GET /tags/search` | 2 | 带 `q=blue` 与不带 `q`（`size=2`）的完整 JSON 相同，均 11 条 |

### 账号面（17）

| 方法 | 路由 | 本轮 L | 状态 |
| :--- | :--- | :--- | :--- |
| `me(**params)` | `GET /me` | 0 | 需登录、返回结构未知 |
| `me_capabilities(**params)` | `GET /me/capabilities` | 0 | 需登录、返回结构未知 |
| `me_bookmarks(**params)` | `GET /me/bookmarks` | 0 | 需登录、返回结构未知 |
| `me_likes(**params)` | `GET /me/likes` | **2** | 不带 `x-sakuria-data-contract` → `426 {"error":"upgrade_required","requiredDataContract":2}`；带 `x-sakuria-data-contract: 2` → `401 {"error":"sakuria_session_required"}`；成功结构未知 |
| `me_following(**params)` | `GET /me/following` | 0 | 需登录、返回结构未知 |
| `me_notifications(**params)` | `GET /me/notifications` | 0 | 需登录、返回结构未知 |
| `me_history(**params)` | `GET /me/history` | 0 | 需登录、返回结构未知 |
| `me_settings(**params)` | `GET /me/settings` | 0 | 需登录、返回结构未知 |
| `me_illusts(**params)` | `GET /me/illusts` | 0 | 需登录、返回结构未知 |
| `me_novels(**params)` | `GET /me/novels` | 0 | 需登录、返回结构未知 |
| `me_series(**params)` | `GET /me/series` | 0 | 需登录、返回结构未知 |
| `me_credits(**params)` | `GET /me/credits` | 0 | 需登录、返回结构未知 |
| `me_plus(**params)` | `GET /me/plus` | 0 | 需登录、返回结构未知 |
| `me_subscription(**params)` | `GET /me/subscription` | 0 | 需登录、返回结构未知 |
| `me_favorites(**params)` | `GET /me/favorites` | 0 | 需登录、返回结构未知 |
| `me_search_history(**params)` | `GET /me/search-history` | 0 | 需登录、返回结构未知 |
| `me_recommend(**params)` | `GET /me/recommend` | 0 | 需登录、返回结构未知 |

## 权限与访问面

* **27 个公共路由各有匿名 200 样本**，不计付费筛选成功路径；
  包装方法运行范围不同，见验证记录。
* **图片代理主机**：公开 API 主机的 `/img/…` 前缀只从响应字段里读到地址，**本轮没有请求任何图片字节**；
  另外两个 `sakuria-pximg*` 主机与会员线路 `sakuria-app-api` 本轮一次都没请求。
* **会员筛选**：本轮跑到两次 `401 {"error":"高级筛选需要 Sakuria+","code":"auth_required","feature":"advanced_search"}`
  ——插画搜索 `type=illust` 与小说搜索 `ai=exclude` 各一次。
* **数据契约头**：`GET /me/likes` 不带 `x-sakuria-data-contract` → `426 {"error":"upgrade_required","requiredDataContract":2}`；
  显式带上 `x-sakuria-data-contract: 2` → `401 {"error":"sakuria_session_required"}`。
  本库**不自动补这个头**，要发就显式写进 `request(..., headers={…})`（44 个包装方法不接 `headers`）。
* **限流**：本轮没有观察到任何 `RateLimit-*` / `Retry-After` 响应头，站点也没有公开配额说明；
  调用方不应假设有配额，本库也不做节流与退避。

### 账号方法与访问面

17 条 `/me/*` 的凭据要求是「需登录」；本轮**只有 `me_likes` 被请求过**（两条拒绝样本），
其余 16 条既没有请求、也没有返回结构。

| 方法 | 路由 | 凭据要求 | 本轮状态 |
| :--- | :--- | :--- | :--- |
| `me()` | `GET /me` | 需登录 | 未请求、返回结构未知 |
| `me_capabilities()` | `GET /me/capabilities` | 需登录 | 未请求、返回结构未知 |
| `me_bookmarks()` | `GET /me/bookmarks` | 需登录 | 未请求、返回结构未知 |
| `me_likes()` | `GET /me/likes` | 需登录（先要求 `x-sakuria-data-contract: 2`） | 两次拒绝样本：`426` → `401`；成功结构未知 |
| `me_following()` | `GET /me/following` | 需登录 | 未请求、返回结构未知 |
| `me_notifications()` | `GET /me/notifications` | 需登录 | 未请求、返回结构未知 |
| `me_history()` | `GET /me/history` | 需登录 | 未请求、返回结构未知 |
| `me_settings()` | `GET /me/settings` | 需登录 | 未请求、返回结构未知 |
| `me_illusts()` | `GET /me/illusts` | 需登录 | 未请求、返回结构未知 |
| `me_novels()` | `GET /me/novels` | 需登录 | 未请求、返回结构未知 |
| `me_series()` | `GET /me/series` | 需登录 | 未请求、返回结构未知 |
| `me_credits()` | `GET /me/credits` | 需登录 | 未请求、返回结构未知 |
| `me_plus()` | `GET /me/plus` | 需登录 | 未请求、返回结构未知 |
| `me_subscription()` | `GET /me/subscription` | 需登录 | 未请求、返回结构未知 |
| `me_favorites()` | `GET /me/favorites` | 需登录 | 未请求、返回结构未知 |
| `me_search_history()` | `GET /me/search-history` | 需登录 | 未请求、返回结构未知 |
| `me_recommend()` | `GET /me/recommend` | 需登录 | 未请求、返回结构未知 |

17 个账号方法按输入资料保留路由映射；除 `/me/likes` 的拒绝之外，
不承诺其余路由当前部署的可达性、成功字段、外层结构或分页行为。

## 实测与输入文档的矛盾

只列本轮 54 个请求能定性的差异；**输入文档没被推翻的部分也不当契约**，见[边界与未实测](#边界与未实测)。

| 项目 | 输入文档的说法 | 本轮实测（L）与处理 |
| :--- | :--- | :--- |
| `/search/user` 的 `total` | 说是「本页条数而不是全局总数」，而同节给的 page1/2/3 = 6/12/20 又像累计值 | **L 支持「本页条数」**：`q=mika` 的 page1/2/3 的 `items` 与 `total` 都是 6/12/21，且各页 `id` 互不重叠；此前怀疑的「累计值」没有证据，**禁止写成累计值**。该端点信封没有 `hasMore`/`nextPage`，翻页判据仍然缺失 |
| `/search/novel` 的 `type` | 同节先把 `type` 列进「静默忽略」，紧接着又说传值会 `400` | **L 站后者**：`type=illust` → `400 {"error":"小说不支持该作品筛选条件","code":"unsupported_filter_for_scope","field":"type"}`；输入文档「静默忽略」那句错 |
| `/search/novel` 的 `ai=exclude` | 说返回 `403` | **L 是 `401`**：`{"error":"高级筛选需要 Sakuria+","code":"auth_required","feature":"advanced_search"}`；本轮没有任何 `403` 样本 |
| 小说详情的 `document.text` 与顶层 `text` | 说两者「内容相同」 | **L 推翻**：`novel_show(29167620)` 的顶层 `text` 是**空串**，而 `document.text` 是 4 行 `[uploadedimage:25719695]` 之类的上传图标记；`document.uploadedImages` 有 4 条、`pixivImages` 为空。不能按「两者相同」取正文，也不能把本轮当成拿到了非空正文 |
| `/tags/{tag}` 与 `/search/illust` 的关系 | 说是同一批结果（别名） | **L 不是**：同 `page=1&size=24` 下 `/tags/blue` 25 条、`/search/illust?q=blue` 29 条、交集 25；两次请求不同刻，本轮不定性差异原因，不写成等价 |
| 相邻页重叠的程度 | 举例 `q=blue` 的 page1∩page2 = 21/24 | **L 是 24 个相同 `id`（page1 29 条）与 10 个（page2 24 条）**；现象一致，具体数字不同，文档只写复数与去重要求 |
| `nextPage` 的数值 | 说在 2/4/4/6 之间跳变 | **L 是 4/4/6**（对应 page1/2/3，`totalPages` 也是 4/4/6）；无论如何都不等于相邻页码，不能用于导航 |
| 用户 `stats` 计数 | 给出全 0 样本并说“实测常全为 0” | 本轮 `following=11,works=8,totalBookmarks=13`；这不与“常全为0”直接矛盾，只说明不能外推为恒0 |
| `/users/{id}/followers` | 说 `page` 生效但 `items` 恒空、功能疑似未实现 | **L 只能说到**：page1/2 都是空 `items` 且 `page` 回显 1/2、`hasMore` false；不能据此断言分页无效或功能未实现，非空 item 没有样本 |
| `/users/{id}/bookmarks` 的分页 | 说所有分页参数实测全部无效 | **L 只证**`page=1` 与 `page=2` 的完整 JSON 相同；其它写法没有样本 |
| `/stats` 的计数 | 样本 `totalCreators=194` | 本轮为 197；样本数不同不是字段契约矛盾，原因未进一步核实 |
| `/users/{id}/illusts` 的字段 | 列出的外层键没有 `nextPage` | 本轮 `page=1/2` 均含该键，分别为 3/4；字段清单需要补充 |

## 候选字段与未验证语义

本轮实测到的公共对象键（L）：Illust 是
`id`/`title`/`type`/`pages`/`description`/`urls`/`pageUrls?`/`author`/`tags`/`stats`/
`publishedAt`/`publishedDays`/`isAi`/`isR18`/`xRestrict`/`sl`（外加系列里的 `series`）；
用户是 `id`/`name`/`handle`/`accent`/`avatar`/`banner?`/`stats`/`social?`；
评论是 `id`/`author`/`text`/`repliesCount`/`likes`/`createdAt`/`timeLabel`；
小说列表项是 `id`/`title`/`author`/`tags`/`textLength`/`coverSvg`/`cover`/`stats`/
`publishedAt`/`publishedDays`/`isAi`/`isR18`/`xRestrict`/`sl`/`series?`，详情再加
`caption?`/`captionHtml?`/`text`/`document`。

**尚未定性的语义**（输入文档候选，本轮没有样本或样本不足以定性）：
`sl` 的含义（本轮样本恒 2）、`hiddenCount` 的过滤规则、标签 `alt` 的取余规律、
`translated` 缺失时整键省略、`xRestrict` 的完整取值集合、`stats` 各键的统计口径、
ugoira 的帧信息、`pageUrls` 与 `urls` 的对应关系、`document.uploadedImages`/`pixivImages`
的内容规则（本轮 `uploadedImages` 4 条、`pixivImages` 为空，且 `document.text` 与顶层 `text`
**不同**）、其它小说的正文形态、`nextCursor` 的确切用途（本轮只见到它是指向上游的地址）。
这些不要当字段保证，逐条依据见[边界与未实测](#边界与未实测)。

## 本轮请求覆盖

| 面 | 覆盖情况 |
| :--- | :--- |
| 站点与配置（5） | 各 1 次，全部 `200` |
| 插画（5） | `illust_search` 13 次（含 `size`/`page`/`sort`/`mode`/`type`/`limit` 组合与 5 条 `400`）、`illust_show` 3 次（1 次 `200`、1 次 `404`、1 次 `400`）、评论/回复/相关各 1 次 |
| 用户（8） | 13 次，全部 `200`（搜索 3 次、作品 2 次、收藏 2 次、关注者 2 次，其余各 1 次） |
| 小说（4） | 7 次：搜索 2 次 `200` + `type`/`ai` 各 1 次拒绝，详情/评论/相关各 1 次 `200` |
| 系列·特辑·标签（5） | 8 次：系列 2 次、特辑 2 次 `200` + `spotlight/0` `503`、标签 3 次 |
| 账号面（17） | `me_likes` 2 次（`426` → `401`），其余 16 条 0 次 |
| 媒体与其它主机 | 0 次（一次都没下载、没请求） |

另有一条**用法路径**的真实执行（不计入上面的 54 次探测）：轻量冒烟 `test/sakuria.py` 跑了
10 次请求、`passed 10 / failed 0`、退出码 0（8 次 `200`，外加 `illust_show(0)` 的 `404` 与
`size=49` 的 `400` 两条预期错误路径）；`examples/sakuria/search_illusts.py` 2 次请求、
`browse_resources.py` 3 次请求，全部 `200`、退出码 0。逐条命令、URL 与输出摘要见
[验证记录](verification.md#sakuria匿名只读实测2026-09-19)。

本轮**没有**跑到：有数据的末页（`hasMore=false` 只出现在空集合样本上）、`nextPage=null`、
任何 `403`、任何 ugoira 样本、任何非空的小说正文、任何 `/me/*` 成功响应。

## 客户端取舍

1. **44 个方法一条不多一条不少**：27 个匿名只读沿用站点路由；17 个 `/me/*` 保留为路由透传，
   文档逐条标注需登录与返回未知，不因为“没凭据”就删掉接口，也不伪造成匿名可用。
2. **JSON 原样交付**：不拆 `items` 信封、不合并分页、不改字段名、不把 `total` 当真实总数，
   详情的裸对象也不套一层。
3. **凭据显式**：只有非空 `access_token` 才发 `Authorization: Bearer`；`''` 表示明确不带凭据；
   不登录、不刷新、不后台续期，也不要求用户名密码。
4. **不发隐式头**：`x-sakuria-data-contract` 这类站点自定义头一律由调用者通过 `headers` 显式给出。
5. **不碰媒体**：不下载图片、不提供字节方法、不拼接 `/img/…` 地址、不嗅探 `Content-Type`。
6. **不做客户端兜底**：不重试、不钳位、不做本地参数校验，不因 `503` 或空集合换路由。
   共享 requests 会话默认跟随重定向；只有本轮探测、冒烟和示例显式关闭跟随。
7. **原生方法只做 GET**：包含 17 个账号读取方法，但没有账号写入或登录方法。

## 排除项

逐类清单与理由见[能力入口的排除表](sakuria-capabilities.md#本库不封装的能力)。一句话概括：
写接口（输入文档称 CORS 预检允许 `POST`/`PUT`/`DELETE`，但没有实测路由）、
登录/注册/令牌（输入文档记录在 API 主机上不存在，本轮未请求）、
媒体与两个图片代理主机（本库不下载）、Sakuria+ 线路与付费筛选（需会员态，照原样抛错）、
Web 前端（输入文档称 Cloudflare 挑战、非数据接口）、标签补全（本轮没有寻找）、
以及输入文档记录为 `404` 的一批子路径，都不在本库内。

## 边界与未实测

**这一节集中放输入文档（T）候选、本轮 54 个请求没有测到的说法**；正文结论不依赖它们。

* **未请求的面**：媒体字节（一次没下载）、`sakuria-app-api` / `sakuria-pximg*` 三个主机、
  Web 前端与登录/注册端点、任何写接口、`/me/*` 里除 `me_likes` 之外的 16 条。
* **`/me/*` 返回结构**：17 条全部未知，`me_likes` 也只有两次拒绝样本。
* **媒体**：输入文档称 `/img/…` 缺文件返回 `200` + `image/svg+xml` 占位图（不是 `404`）、
  `/img/*` 的查询参数被忽略、两个 pximg 主机需要服务端签发的图片 token——**均未复测**；
  按用户要求保留这条提醒，但本轮既没有下载也没有请求任何图片。
* **参数取值、默认值与枚举**：`size` 的可用范围与默认值、`page` 的上界、
  `sort`/`type`/`ai`/`mode`/`ratio` 的完整取值、各列表的默认页大小、`lang` 的取值与未知值回退，
  都只有输入文档说法。本轮只测到：`size` 的 0/1/24/48/49（0 与 49 被拒）、`page=0`、
  `sort=popular` 与非法值、`mode=text`、`limit=__invalid__`、`type=illust`、`ai=exclude`。
* **参数忽略**：输入文档列了一批会被静默忽略的参数名；本轮**只证 `limit` 这一个取值**
  在 `/search/illust` 上被忽略，不要推广。
* **错误码全集**：本轮见到的只有 `400`/`401`/`404`/`426`/`503` 的少数形态；
  输入文档列的 `403`、按资源类型区分的 `invalid user id`/`invalid novel id`/`invalid series id`/
  `invalid spotlight id`、`Not Found` 路由错误体、`bad path` 都没有样本。
* **末页判据**：输入文档说翻页只看 `hasMore=false` 或 `nextPage=null`；本轮
  `hasMore=false` 只出现在空集合样本（关注者、用户系列、小说评论、小说相关、`series/12064`），
  **翻到有数据的末页**与 `nextPage=null` 都没跑到。
* **字段语义**：`sl`、`hiddenCount` 的过滤规则、`alt` 的取余规律、`translated` 省略行为、
  `r18`/`safe` 参数是否被忽略、`stats` 的口径、ugoira 的帧信息、头像绝对外链形态、
  `hiddenCount` 与「免费通道拿不到 R18」的关系，都只有输入文档依据。
* **同类对象一致性**：不要因为某两个端点返回同名字段，就推断所有端点都一致；
  本轮只在具体请求上见到具体键。
* **限流**：没有观察到 `RateLimit-*` / `Retry-After` 头，也没有公开配额说明；既有结论不覆盖配额。
* **范围声明**：本页只证明上面列出的请求与依据，不扩写为发布验证；没有运行格式化、lint、
  项目级测试套件或构建。

继续阅读：[客户端用法](sakuria.md) · [方法参考](sakuria-api.md) ·
[能力入口](sakuria-capabilities.md) · [验证记录](verification.md#sakuria匿名只读实测2026-09-19)。
