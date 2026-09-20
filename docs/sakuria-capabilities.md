# Sakuria：我要做什么，用哪个方法？

Sakuria 是 Pixiv 的第三方镜像站，不是 booru。本库包装其公开 API 主机 `https://sakuria-api.syarolia.com`，共 44 个原生方法。

* 27 个匿名只读方法：站点与配置 5 个、插画 5 个、用户 8 个、小说 4 个、系列·特辑·标签 5 个。
* 17 个 `/me/*` 账号路由透传：全部需要登录。本轮只请求过 `me_likes`，其余 16 条返回结构未知。

除位置参数外，所有方法都接 `**params`，原样拼进查询串。44 个包装方法都不接 `headers`；需要 `x-sakuria-data-contract` 这类头时，走通用入口。完整参数表见[方法参考](sakuria-api.md)；依据与差异见[依据与差异](sakuria-contract-notes.md)。

表中的数字来自直接 HTTP 路由观察，不是每个 Python 方法的执行记录。逐条 URL 与状态见[验证记录](verification.md#sakuria匿名只读实测2026-09-19)。编号、条数与计数只作形态示例。输入文档（T）里本轮没测到的候选说法不写进本页，集中列在[边界清单](sakuria-contract-notes.md#边界与未实测)。

## 共同约定

* 本文中的 `client` 由 `Sakuria('sakuria')` 创建，包内配置默认匿名。构造参数或配置中的 `access_token` 非空时才发 `Authorization: Bearer`。构造方式见[客户端用法](sakuria.md)。
* 所有路径接在 `https://sakuria-api.syarolia.com` 后面。路径中的编号就是 Pixiv 的 illust / novel / user 编号。
* 列表信封本轮出现过的键：`items`、`page`、`pageSize`、`total`、`totalPages`、`hasMore`、`nextPage`、`hiddenCount`。**`total`、`totalPages`、`nextPage` 不能用来导航**。
* 详情接口返回裸对象：`/illust/{id}`、`/novels/{id}`、`/series/{id}`、`/users/{id}`、`/spotlight/{id}`。
* 只有部分参数会被校验：非法值回 `400` 且带 `field`。本轮只证 `limit` 这一个取值会被忽略。
* 媒体只给地址：响应里的 `urls`、`cover` 等是以 `/` 开头的相对路径，拼 `client.site_url` 才是完整地址。本库不下载媒体。拼接方式见[客户端用法](sakuria.md#媒体地址只给地址拼接是你的事)。

## 按目的找调用

| 我要做什么 | 调用 | 给什么 → 返回什么（本轮实测） |
| :--- | :--- | :--- |
| 看服务标识 | `client.index()` | 无参数 → `200 {"name": "sakuria-api", "ok": true, "docs": "https://github.com/your-org/sakuria"}`；`docs` 是占位仓库地址 |
| 看站点计数 | `client.stats()` | 无参数 → `200 {"newToday": 30, "totalIllusts": 85, "totalCreators": 197, "totalUsers": 113}`；站点自述计数，随实时数据变动 |
| 看部署健康 | `client.health()` | 无参数 → `200`，键 `ok`/`releaseSha`/`releaseVersionId`/`checks`；`checks` 含 `db`、`jwt`、`pxve`、`cache`、`cacheBackend`、`databaseDriver` 等 |
| 看客户端配置 | `client.app_config()` | 无参数 → `200`，键含 `latestVersion`（本轮 `"1.0.0"`）、`latestBuild`、`updateUrl`、`updateAvailable`、`updateRequired`、`announcement`（本轮 `null`）、`maintenance`、`flags`、`servers`（2 条）、`imageProxy`、`iap` |
| 看 AI 功能配置 | `client.ai_config()` | 无参数 → `200`，键含 `enabled`、`metaEnabled`、`novelEnabled`、`mangaEnabled`、`mangaInputMode`（本轮 `"client_ocr_v1"`）、`commentEnabled`、`cacheTtlDays`、`billingMode`、`models`（本轮 2 条，每条带 `contextLength`、`ratePer1mIn`/`ratePer1mOut` 等） |
| 按关键词搜插画 | `client.illust_search(q='blue', page=1, size=24)` | 关键词 + 页码 + 每页数 → `200`，信封 `items` 本轮 29 条、`page` 1、`pageSize` 24、`total` 48、`totalPages` 4、`hasMore` true、`nextPage` 4、`hiddenCount` 61 |
| 翻插画搜索的下一页 | `client.illust_search(q='blue', page=2, size=24)`（再 `page=3`） | 手动递增 `page` → 本轮 page2 是 24 条（`total` 72、`nextPage` 4）、page3 是 33 条（`total` 96、`totalPages` 6、`nextPage` 6）；**page1∩page2 有 24 个相同 `id`**，自己按 `id` 去重 |
| 换每页大小 | `client.illust_search(q='blue', size=1)` / `size=48` | `size=1` 回 5 条、`size=48` 回 39 条；`size=0`、`size=49` 得到 `400 {"code": "invalid_search_filter", "field": "size"}`；**条数不等于 `size`** |
| 传非法页码/排序/模式 | `client.illust_search(q='blue', page=0)` / `sort='__invalid__'` / `mode='text'` | 分别得到 `400 {"error": "筛选参数无效", "code": "invalid_search_filter", "field": "page"/"sort"/"mode"}` |
| 对照一个额外参数 | `client.illust_search(q='blue', page=1, size=24, limit='__invalid__')` | `200`，ID 顺序与分页字段和不带该参数的基线相同；只证这一组取值，不能据此推断全部未知参数的规则 |
| 拿会员筛选 | `client.illust_search(q='blue', type='illust')` | `401 {"error": "高级筛选需要 Sakuria+", "code": "auth_required", "feature": "advanced_search"}` |
| 只按标签拿一批插画 | `client.tag_illusts('blue', page=1, size=24)` | 标签名（整段做 URL 编码）→ `200`，信封同上，本轮 25 条、`hiddenCount` 65；与 `illust_search(q='blue')` 的 29 条**不是同一批**（交集 25，两次请求不同刻） |
| 不带查询拉默认列表 | `client.tag_search(size=2)` | `200`，本轮与 `tags/search?q=blue&size=2` 的完整 JSON 相同（各 11 条）→ 在 `size=2` 下 `q` 没有影响 |
| 取一张插画 | `client.illust_show(70937229)` | 插画编号 → **裸 Illust 对象**：`id`/`title`/`type`/`pages`/`description`/`urls`/`author`/`tags`/`stats`/`publishedAt`/`publishedDays`/`isAi`/`isR18`/`xRestrict`/`sl`；本轮 `pages` 1、`urls.w/h` 1200/675、`tags` 9 条、`sl` 2 |
| 取多页插画的每页地址 | `client.illust_show(多页作品的 id)` | 同一编号 → 读 `pageUrls[]`（与 `urls` 同构、按页序）；**`pages=1` 时没有这个键**（本轮该样本就没有） |
| 取不存在的插画 | `client.illust_show(0)` / `client.illust_show('abc')` | `404 {"error": "illust not found"}` / `400 {"error": "invalid id"}` |
| 读插画评论 | `client.illust_comments(70937229, page=1, size=2)` | 插画编号 + 页码 + 每页 → `200 {"items": [评论, …], "hasMore": true}`；本轮 2 条，评论键 `id`/`author`/`text`/`repliesCount`/`likes`/`createdAt`/`timeLabel`，`author` 是 `{id, name, handle, accent, avatar}` |
| 读某条评论的回复 | `client.illust_comment_replies(70937229, 183991501)` | 插画编号 + 评论 `id` → `200 {"items": [回复, …]}`（本轮 1 条，键与评论同构，**没有 `hasMore`**） |
| 找相关插画 | `client.illust_related(128641898, size=2)` | 插画编号 + 条数 → `200 {"items": [Illust, …]}`（本轮 2 条，只有 `items`） |
| 按用户名找画师 | `client.user_search(q='mika', page=1)` | 关键词 + 页码 → `200 {"items": [{"user": …, "previews": […]}, …], "total": …}`；本轮 page1/2/3 的 `items` 与 `total` 都是 6/12/21 且各页 `id` 互不重叠 → `total` 是**本页条数**；信封没有 `hasMore`/`nextPage` |
| 看用户资料 | `client.user_show(129030276)` | user 编号 → **裸用户对象**：`id`/`name`/`handle`/`accent`/`avatar`/`banner`/`stats`/`social`；本轮 `stats` 是 `{"followers": 0, "following": 11, "works": 8, "totalLikes": 0, "totalBookmarks": 13}`、`social` 1 条 `{kind: "pixiv", …}` |
| 看某用户的插画 | `client.user_illusts(1039353, page=1)` | user 编号 + 页码 → Illust 信封；本轮 page1/page2 各 45 条、`pageSize` 24、`nextPage` 3/4、`hiddenCount` 3、两页交集 23 |
| 看某用户的小说 | `client.user_novels(3182410, page=1)` | user 编号 + 页码 → 小说信封；本轮 24 条、`nextCursor` 是上游地址 `https://app-api.pixiv.net/v1/user/novels?user_id=3182410&offset=30`（**不能拿去请求本站**） |
| 看某用户公开收藏 | `client.user_bookmarks(1554775)` | user 编号 → `{"items": [Illust, …], "pageSize", "hasMore", "nextCursor", "hiddenCount"}`；本轮 19 条、`nextCursor` `"9175901406"`、`hiddenCount` 5，且 **`page=1` 与 `page=2` 的完整 JSON 相同**（只证这两个取值没有推进） |
| 看某用户的关注者 | `client.user_followers(1039353, page=1)` | user 编号 + 页码 → 本轮 page1/page2 都是空 `items`、`pageSize` 12、`page` 分别回显 1/2、`hasMore` false；**不能据此说分页无效或功能未实现**，非空 item 结构没有样本 |
| 看某用户的小说系列 | `client.user_series(3182410, page=1)` | user 编号 + 页码 → 本轮是空 `items`、`pageSize` 24、`hasMore` false；item 结构没有样本 |
| 找相似画师 | `client.user_related(1039353)` | user 编号 → `{"items": [{"user", "previews"}, …]}`；本轮 12 条，只有 `items` |
| 搜小说 | `client.novel_search(q='blue', page=1)` | 关键词 + 页码 → 小说信封；本轮 page1 24 条（`total` 48、`nextPage` 2）、page2 26 条（`total` 72、`nextPage` 3）；item 不含正文 |
| 用小说不支持的筛选条件 | `client.novel_search(q='blue', type='illust')` / `ai='exclude'` | `400 {"error": "小说不支持该作品筛选条件", "code": "unsupported_filter_for_scope", "field": "type"}` / `401 {"error": "高级筛选需要 Sakuria+", "code": "auth_required", "feature": "advanced_search"}` |
| 读小说详情 | `client.novel_show(29167620)` | 小说编号 → **裸对象**，键含 `id`/`title`/`author`/`caption`/`captionHtml`/`tags`/`textLength`/`text`/`document`/`coverSvg`/`cover`/`stats`/`publishedAt`/`publishedDays`/`isAi`/`isR18`/`xRestrict`/`sl`；**本轮这部的 `text` 是空串，而 `document.text` 是 4 行 `[uploadedimage:…]` 标记**（`uploadedImages` 4 条、`pixivImages` 为空）——输入文档说两者内容相同，已被推翻；别把本轮当成拿到了非空正文 |
| 读小说评论 | `client.novel_comments(29167620, page=1)` | 小说编号 + 页码 → `{"items": […], "hasMore": false}`；本轮为空集合，评论与 `stamp*` 字段没有样本 |
| 找相关小说 | `client.novel_related(29167620)` | 小说编号 → 小说信封；本轮为空（`pageSize` 12、`total` 0、`hasMore` false），item 结构没有样本 |
| 列插画系列的内容 | `client.series_show(198059, page=1)` | 插画自己的 `series.id` → **裸对象** `{id, title, caption, total, author, items, hasMore}`；本轮 `items` 30 条、`total` 219、`hasMore` true；换成小说一侧的 id `12064` 则 `items` 为空、`total` 7 |
| 看特辑列表 | `client.spotlight_list(page=1, lang='zh-cn')` | 页码 + 语言 → `{"items": [{"id", "title", "caption", "tag", "coverSvg", "cover", "tags", "date", "articleUrl", "works"}, …], "page", "pageSize", "hasMore"}`；本轮 20 条而信封写 `pageSize` 12、`hasMore` true、`works` 全空 |
| 看一条特辑 | `client.spotlight_show(11971, lang='zh-cn')` | 特辑编号 + 语言 → **裸对象**，键含 `id`/`title`/`date`/`description`/`cover`/`tags`/`works`/`articles`/`relatedLatest`/`relatedRecommend`/`articleUrl`；本轮 `articles` 19 篇、`works` 空、两个 related 的 `items` 空；`cover` 是相对路径 `/p/embed.pixiv.net/…` |
| 查不存在的特辑 id | `client.spotlight_show(0)` | `503 {"error": "upstream temporarily unavailable", "retryable": true}`（不是 `404`） |
| 用别的路由/自定义头 | `client.request('GET', 'stats')` | 动词 + 站点相对路径 + `params` + `headers` → 与原生方法同一条通路，JSON 原样返回。见[通用入口](sakuria.md#通用入口-request) |

### 账号面（`/me/*`，17 条全部需登录、返回结构未知）

| 我要做什么 | 调用 | 本轮状态 |
| :--- | :--- | :--- |
| 读当前账号资料 | `client.me()` | 未请求、返回结构未知 |
| 看当前账号的能力开关 | `client.me_capabilities()` | 未请求、返回结构未知 |
| 读自己的收藏 | `client.me_bookmarks()` | 未请求、返回结构未知 |
| 读自己点过的赞 | `client.me_likes()` | **唯一的样本**：不带 `x-sakuria-data-contract` → `426 {"error": "upgrade_required", "requiredDataContract": 2}`；带 `x-sakuria-data-contract: 2` → `401 {"error": "sakuria_session_required"}`；成功结构未知 |
| 读自己的关注列表 | `client.me_following()` | 未请求、返回结构未知 |
| 读通知 | `client.me_notifications()` | 未请求、返回结构未知 |
| 读浏览历史 | `client.me_history()` | 未请求、返回结构未知 |
| 读账号设置 | `client.me_settings()` | 未请求、返回结构未知 |
| 读自己投稿的插画 | `client.me_illusts()` | 未请求、返回结构未知 |
| 读自己投稿的小说 | `client.me_novels()` | 未请求、返回结构未知 |
| 读自己的系列 | `client.me_series()` | 未请求、返回结构未知 |
| 读积分（credits） | `client.me_credits()` | 未请求、返回结构未知 |
| 读 Sakuria+ 状态 | `client.me_plus()` | 未请求、返回结构未知 |
| 读订阅信息 | `client.me_subscription()` | 未请求、返回结构未知 |
| 读收藏夹 | `client.me_favorites()` | 未请求、返回结构未知 |
| 读搜索历史 | `client.me_search_history()` | 未请求、返回结构未知 |
| 读推荐 | `client.me_recommend()` | 未请求、返回结构未知 |

**不要把它们写成匿名可用**，也不要用它们当匿名探针。逐条权限记录见[账号方法与访问面](sakuria-contract-notes.md#账号方法与访问面)。44 个包装方法只接位置参数与 `**params`、不接 `headers`；需要契约头时用 `client.request('GET', 'me/likes', headers={'x-sakuria-data-contract': '2'})`。

## 完整方法索引（27 匿名读 + 17 账号透传 = 44）

每个原生方法一行。参数范围与字段表见[方法参考](sakuria-api.md)。除 `index()` 的 `/` 之外，以下路径都接在 `https://sakuria-api.syarolia.com` 后面。**27 条匿名读路由本轮全部真发过至少一次**（部分只拿到空集合样本，例如小说评论与相关小说）。

### 站点与配置（5，匿名）

* `index()` → `GET /`，服务标识与占位 `docs` 链接。
* `stats()` → `GET /stats`，站点自述计数（`newToday`/`totalIllusts`/`totalCreators`/`totalUsers`）。
* `health()` → `GET /healthz`，部署健康与依赖检查（`releaseSha`、`releaseVersionId`、`checks`）。
* `app_config()` → `GET /app/config`，客户端线路、图片代理、内购与升级信息。
* `ai_config()` → `GET /ai/config`，AI 功能开关与模型表。

### 插画（5，匿名）

* `illust_search(**params)` → `GET /search/illust`，用 `q` 查询插画，完整对象带 `items`/`hasMore`。
* `illust_show(illust_id, **params)` → `GET /illust/{illust_id}`，**裸 Illust 对象**，含 `urls` 与（多页时）`pageUrls`。
* `illust_comments(illust_id, **params)` → `GET /illust/{illust_id}/comments`，信封只有 `items`/`hasMore`。
* `illust_comment_replies(illust_id, comment_id, **params)` → `GET /illust/{illust_id}/comments/{comment_id}/replies`，信封只有 `items`。
* `illust_related(illust_id, **params)` → `GET /illust/{illust_id}/related`，返回相关插画的 `items` 数组；相关性算法未验证。

### 用户（8，匿名）

* `user_search(**params)` → `GET /search/user`，按名字找画师，每项 `{user, previews}`，`total` 是本页条数。
* `user_show(user_id, **params)` → `GET /users/{user_id}`，**裸用户对象**。
* `user_illusts(user_id, **params)` → `GET /users/{user_id}/illusts`，该用户的插画。
* `user_novels(user_id, **params)` → `GET /users/{user_id}/novels`，该用户的小说，`nextCursor` 是上游地址。
* `user_bookmarks(user_id, **params)` → `GET /users/{user_id}/bookmarks`，公开收藏，本轮 `page=1/2` 结果相同。
* `user_followers(user_id, **params)` → `GET /users/{user_id}/followers`，本轮两页都为空。
* `user_series(user_id, **params)` → `GET /users/{user_id}/series`，该用户的小说系列，本轮为空。
* `user_related(user_id, **params)` → `GET /users/{user_id}/related`，相关用户，只有 `items`。

### 小说（4，匿名）

* `novel_search(**params)` → `GET /search/novel`，搜小说，列表项不含正文。
* `novel_show(novel_id, **params)` → `GET /novels/{novel_id}`，**裸对象**，含 `text` 与 `document`（本轮 `text` 为空串，`document.text` 是上传图标记，两者**不相同**）。
* `novel_comments(novel_id, **params)` → `GET /novels/{novel_id}/comments`，本轮空集合。
* `novel_related(novel_id, **params)` → `GET /novels/{novel_id}/related`，本轮空集合。

### 系列、特辑与标签（5，匿名）

* `series_show(series_id, **params)` → `GET /series/{series_id}`，插画系列内容，裸对象含 `items`。
* `spotlight_list(**params)` → `GET /spotlight`，Pixivision 特辑列表。
* `spotlight_show(spotlight_id, **params)` → `GET /spotlight/{spotlight_id}`，**裸对象**，比列表项多 `description` 与 `articles`。
* `tag_illusts(tag, **params)` → `GET /tags/{tag}`，按标签取插画；标签整段做 URL 编码。
* `tag_search(**params)` → `GET /tags/search`，本轮在 `size=2` 下与不带 `q` 的结果相同。

### 账号（17，全部需登录、返回结构未知）

* `me(**params)` → `GET /me`，当前账号资料。
* `me_capabilities(**params)` → `GET /me/capabilities`，账号能力开关。
* `me_bookmarks(**params)` → `GET /me/bookmarks`，自己的收藏。
* `me_likes(**params)` → `GET /me/likes`，自己点过的赞；不带 `x-sakuria-data-contract: 2` 时先得到 `426`。
* `me_following(**params)` → `GET /me/following`，自己的关注列表。
* `me_notifications(**params)` → `GET /me/notifications`，通知。
* `me_history(**params)` → `GET /me/history`，浏览历史。
* `me_settings(**params)` → `GET /me/settings`，账号设置。
* `me_illusts(**params)` → `GET /me/illusts`，自己投稿的插画。
* `me_novels(**params)` → `GET /me/novels`，自己投稿的小说。
* `me_series(**params)` → `GET /me/series`，自己的系列。
* `me_credits(**params)` → `GET /me/credits`，积分。
* `me_plus(**params)` → `GET /me/plus`，Sakuria+ 状态。
* `me_subscription(**params)` → `GET /me/subscription`，订阅信息。
* `me_favorites(**params)` → `GET /me/favorites`，收藏夹。
* `me_search_history(**params)` → `GET /me/search-history`，搜索历史。
* `me_recommend(**params)` → `GET /me/recommend`，推荐。

除 `me_likes` 的两条样本外，这 17 条**没有真实请求证据**；成功时的字段、信封与参数是否生效都未知。

## 本库不封装的能力

这些路由/主机不在本库范围内；需要时用 `client.request(method, path, params=…, headers=…)` 自己发（**只有 JSON 才解析**）。

| 类别 | 例子 | 为什么不封装 |
| :--- | :--- | :--- |
| 写接口 | 输入文档称 CORS 预检允许 `POST`/`PUT`/`DELETE`，但没有给出实测路由 | 本库不做写操作，也没有账号；无凭据时不探测（有副作用） |
| 登录 / 注册 / 令牌 | 输入文档记录的 `/auth/*`、`/login`、`/register`、`/session`、`/token`、`/oauth/token` 全 `404` | 本轮未请求这些路径；即使存在，本库也不做登录，令牌由调用者提供 |
| 图片代理与图片字节 | `https://sakuria-api.syarolia.com/img/…`、`sakuria-pximg.syarolia.com`、`sakuria-pximg-pro.syarolia.com` | 本库不下载媒体、不返回字节；相对路径怎么拼见[客户端用法](sakuria.md#媒体地址只给地址拼接是你的事) |
| Sakuria+ 会员线路 | `sakuria-app-api.syarolia.com` 整条线路 | 需要会员态；本库照原样抛出服务端的 `401`/`403`，不做兜底 |
| Web 前端 | `https://sakuria.syarolia.com` 的 HTML/JS 路径 | 输入文档称被 Cloudflare 挑战挡住；本轮未请求，本库也不做 HTML 解析 |
| 标签补全 / 联想 | 输入文档称 `/tags/autocomplete`、`/tags/suggest` 只是名字叫这个的普通标签，本站没有补全端点 | 本轮没有寻找补全端点，只在 `size=2` 下证了 `/tags/search` 忽略 `q`；不凭别家引擎的惯例造方法 |
| 不存在的路由 | 输入文档记录 `/series`、`/search/series`、`/novel/{id}`（单数）、`/users/{id}/following` 等均为 `404` | 本轮没有逐个复测；本库不发明方法，也不把它们的 404 包装成空结果 |
| `GET /` 里的 `docs` | `https://github.com/your-org/sakuria` | 本轮响应里就是这个占位地址，不是真实文档或源码 |

## 边界与未实测

* **未请求的面**：媒体字节、三个其它主机、Web 前端与登录/注册端点、任何写接口、`/me/*` 里除 `me_likes` 之外的 16 条——全部没有样本。
* **`/me/*` 返回结构**：17 条全部未知；只有 `426`（缺契约头）与 `401`（带契约头）两个样本。
* **输入文档候选但未复测**：`size` 的可用范围与默认值、`sort`/`type`/`ai`/`mode`/`ratio` 的完整枚举、各列表的默认页大小、`lang` 的取值与回退、错误码全集（`403` 本轮无样本）、末页判据（`hasMore=false` 只在空集合样本上出现过，`nextPage=null` 本轮未见）、`sl`/`hiddenCount`/`alt` 的语义、`r18`/`safe` 等参数的忽略清单、ugoira 的帧信息、媒体占位图与图片 token 主机。完整清单见[依据与差异的边界](sakuria-contract-notes.md#边界与未实测)。
* **本轮已证的相关行为**：`total`/`totalPages`/`nextPage` 不能用来导航；相邻页会重叠；`items` 条数不等于 `size`；`size=0/49` 回 `400 field=size`；`limit` 这一个取值会被忽略；用户搜画的 `total` 是本页条数；收藏 `page=1/2` 结果相同；关注者两页皆空；`/tags/blue` 与 `/search/illust?q=blue` 不是同一批；特辑 id 不存在回 `503`；小说详情的 `text` 与 `document.text` **不相同**。
* **用法路径另跑过**：轻量冒烟 10 次请求 `passed 10 / failed 0`（8 次 `200` + 预期的 `404`/`400`）、退出码 0；两个示例分别 2 次与 3 次请求全部 `200`、退出码 0。逐条见[验证记录](verification.md#sakuria匿名只读实测2026-09-19)；它们覆盖用法路径，不等于 44 个方法逐一验证。
* 站点数据实时变动：编号、条数、计数与 `hiddenCount` 都会变，别把本页的数字当契约。
* 依据出处、权限分支与输入文档矛盾的完整记录见[依据与差异](sakuria-contract-notes.md)。

继续阅读：[客户端用法](sakuria.md) · [方法参考](sakuria-api.md) ·
[依据与差异](sakuria-contract-notes.md) · [验证记录](verification.md#sakuria匿名只读实测2026-09-19)。
