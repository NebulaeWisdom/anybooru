# nhentai 方法参考

nhentai（站点根 `https://nhentai.net`）不是本包已有的任何一种 booru 引擎，也不是它们的变体。它自带 OpenAPI 规范，公开 JSON API v2（路由在 `/api/v2/...` 下）。列表与详情是两套不同对象（列表瘦、详情胖）。认证是 `Authorization: Key <api_key>`。分页信封为 `result` / `num_pages` / `per_page` / `total`。它是独立家族，`Nhentai` 之外没有类能顶替。

本页列出 `Nhentai` 的全部 36 个原生方法：31 个 `GET`、3 个 `POST`（`favorite_add()`、`gallery_download()`、`blacklist_update()`）、1 个 `POST` 但只读（`tag_search()`）、1 个 `DELETE`（`favorite_remove()`）。另有通用入口 `request(method, path, *, params=None, data=None, headers=None)`。
`tag_search()` 只读，但本轮只授权匿名 `GET`，未被执行。4 个写方法（3 个 `POST` + 1 个 `DELETE`）一次都不会执行，本页只写调用形态。

调用写法、`api_key` 来源、`last_call` 查看、错误抛出见[客户端用法](nhentai.md)；「想做什么→用哪个方法」见[能力入口](nhentai-capabilities.md)；依据、排除项与规范矛盾见[契约审计附注](nhentai-contract-notes.md)；真实 URL、状态码与 `Content-Type` 见[验证记录](verification.md)。

## 依据与阅读方式

本页用三个标记标注结论来源：

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **规范** | [官方 OpenAPI](https://nhentai.net/api/v2/openapi.json)，版本 `2.0.0+14bccf7`，OpenAPI 3.1.0；98 路径 / 114 操作 / 129 schema。每方法给 JSON Pointer 与 `operationId` | 路径、参数、类型、范围、服务端默认值、认证、响应 schema。`required` 决定键是否必须存在，`nullable` 决定值是否可为 `null`；两者不同。声明与实际响应冲突时分别记录 |
| **实测** | 两档站点侧观察：① 匿名只读 `GET` 直接 HTTP 观察——61 次请求，串行、相邻 ≥1.3 秒、不重试、不跟随跳转、不下载媒体、不带任何凭据；② 本包冒烟与示例真跑——`test/nhentai.py` 10 个请求全 PASS（8 个 `200` + 一个预期 `404` + 一个预期 `400`）退出 0，两个示例分别 3 个与 5 个 `GET` 全 `200` 退出 0，共覆盖 9 个原生方法。逐条见[验证记录](verification.md#nhentai匿名只读实测2026-09-20) | 对应路由当次的状态码、错误体形状、信封键、字段是否出现、参数是否被采纳，以及「照本页写法调得通」。它是某一时刻读数：计数、页数、条目数都会变，本页一切数字都只是例子 |
| **客户端** | 本包 `Nhentai` 自身固定行为（构造参数、路径拼法、参数进查询串方式、凭据头、返回值） | 调用形态、参数编码、返回值、异常。与站点侧取值无关 |

规矩：

* **参数表**以**规范**为准（参数名、类型、范围、枚举、服务端默认值逐条给 JSON Pointer）；**状态码、错误体、信封键、参数是否被采纳**以**实测**为准，两者冲突按实测写并指出。最典型：规范给校验失败写 `422 HTTPValidationError`，实测是 `400 {"error": "Validation error", "details": […]}`。
* 数字与字段值三种写法：**实测**过的标实测、**规范**给字段形状不含取值、两者都没有写「未实测」。HTTP 样本与 Python 片段执行范围不同：只有验证记录列出的脚本真跑过；其它片段是调用示范，不是逐段执行证据。
* 本页不引用输入研究文档：结论要么被规范覆盖，要么被本轮实测覆盖，两者都没有写「待实测」。

### 本轮实测覆盖了什么

* 61 次匿名只读直接 HTTP 请求，全部为 `GET`。
* 36 个原生方法里 31 个 `GET` 路由全部被直接请求过：25 个成功、6 个因要求凭据回 `401`（`user_me`、`favorite_list`、`favorite_random`、`blacklist_list`、`blacklist_ids`、`gallery_favorite`）。
* 一次都没跑：`tag_search()`（`POST`，只读但本轮只授权 `GET`）、`favorite_add()` / `favorite_remove()` / `blacklist_update()` / `gallery_download()`（写与资源分配）；带凭据成功路径、账号权限、first-party 登录、PoW/captcha、moderation、广告位、任何媒体字节与 CDN 主机、限流触发（`429`）、非法 Key。
* 空白项与后果集中写在[边界与未实测](#边界与未实测)。

## 规范元数据（**规范**）

| 项目 | 值 |
| :--- | :--- |
| 规范地址 | <https://nhentai.net/api/v2/openapi.json> |
| `info.version` | `2.0.0+14bccf7`（版本号带构建后缀，站点改版会变） |
| OpenAPI 版本 | `3.1.0` |
| 规模 | 98 路径 / 114 操作 / 129 schema（**实测**：本轮直接抓规范，读到 `98/114/129`） |
| 规范本身可取 | `GET https://nhentai.net/api/v2/openapi.json` → `200 application/json`（**实测**） |
| `servers` | **规范里没有这个字段**，基地址读不出；规范由 `https://nhentai.net` 宿主提供，客户端把站点根 `https://nhentai.net` 与路径拼起来（**客户端**） |
| 本页覆盖 | 114 个操作里的 36 个（第三方契约内原生操作），其余 78 个排除理由见[边界与未实测](#边界与未实测) |

### 两种认证方式（**规范**：`#/components/securitySchemes`）

| 方案 | 位置 | 值的样子 | 谁能用 |
| :--- | :--- | :--- | :--- |
| `API Key` | 请求头 `Authorization` | `Key <你的 API Key>` | 第三方客户端（本包只支持这一种） |
| `User Token` | 请求头 `Authorization` | `User <token>` | 站点自家服务与内部用途，本包**不提供** User Token 构造参数 |

两者共用 `Authorization` 头，一次只能带一个。本包只带 `API Key`：构造时 `api_key` 非空，每个请求带 `Authorization: Key <api_key>`；`api_key=''` 匿名，不带认证头（**客户端**）。

规范 `info.description`（**规范**：`#/info/description`）三段站点自述：

* API Key 在账号设置页生成：<https://nhentai.net/user/settings#apikeys>，按 `Authorization: Key YOUR_API_KEY` 传。
* 建议带描述性 `User-Agent`，格式 `AppName/version (contact or project URL)`——站点靠它识别流量并在需要时联系你。本包构造参数 `user_agent=None` 时用包内配置默认值；换成自己的写 `Nhentai('nhentai', user_agent='myapp/1.0 (https://example.com)')`（**客户端**）。
* 需要更高限额联系 `support@nhentai.net`；变更日志写在 `/api/v2/changelog`（网页地址，**不是**规范 98 条路径之一，本页没有对应客户端方法）。

### 规范给分组写的说明（**规范**：`#/tags`）

| 分组 | 规范原话要点 |
| :--- | :--- |
| `cdn` | 列表与详情的 `path`/`thumbnail` 都是相对路径：先从 `GET /api/v2/cdn` 取服务器列表，把其中一个与 `path` 拼成完整 URL；不要硬编码子域（列表会变）；原样使用 `path`，不要猜扩展名、后缀或编号——CDN 只认已知媒体路由固定样式，反复猜会被延长封禁；正常浏览限额宽松，整册缩略图短时突发不会吃 `429`，但持续远超正常速率或反复请求非法样式会被临时封禁（封禁很短、自动解除）；把 `429` 当退避信号；整册压缩包走 `POST /api/v2/galleries/{id}/download`，不要靠爬 CDN 单页 URL 拼 |
| `galleries` | 浏览、检索、读取画廊数据 |
| `tags` | 标签查询、列举与检索 |
| `GTS` | 画廊标签建议：用户提议给某张画廊加/去一个标签并互相投票，staff 决定接受或拒绝 |
| `taxonomy` | 全局标签体系的社区提议：新建、改名、合并、补描述；已处理条目是带 staff `resolution_note` 的公开账本 |
| `search` | 带过滤条件的全文画廊检索 |
| `comments` | 画廊评论 |
| `users` | 公开用户资料 |
| `favorites` | 收藏管理 |
| `blacklist` | 标签黑名单管理 |
| `user` | **规范原话**：`**First-party and internal only**, bar `GET /api/v2/user`.`——除 `GET /api/v2/user` 例外，其它 `user` 与 `auth` 路由明确只给站点自家服务用、第三方不应调用、会被强制拦截，第三方请用 `Authorization: Key YOUR_API_KEY`。本包收录 `user_me()`，其余 `user/*` 与全部 `auth/*` 不封装 |
| `moderation` | staff 专用审核工具（本包全部不封装） |
| `zones` | 规范里这个分组没有任何描述（广告位相关路由，本包全部不封装） |

## 服务端默认值不是客户端默认值

这是本家族最容易踩的一条：

* 规范里每个参数的 `default` 是服务端在不传该参数时用的值，例如 `gallery_list` 的 `page` 默认 `1`、`per_page` 默认 `25`。客户端不读也不填这些默认值：`client.gallery_list()` 发出的 URL 是 `https://nhentai.net/api/v2/galleries`，查询串没有 `page=1&per_page=25`（**客户端**）。真正的 `1` 与 `25` 由站点补。
* 同理，`minimum` / `maximum` 是服务端校验范围。客户端不钳位、不取整、不改名：`client.gallery_list(per_page=101)` 照发 `per_page=101`，由站点拒绝（该值实测 `400`，不是规范列的 `422`，见[状态码与错误体](#状态码与错误体)）。
* **传了也不一定生效**：实测几个端点不采纳显式传的 `per_page`（`tag_list()` 传 `per_page=1` 回 120 条、`taxonomy_resolved()` 传 `per_page=2` 回 50 条），`search()` 规范没有 `per_page`，已测样本传 2 仍回显 25。读取服务端返回的分页信息；没有 `per_page` 回显的响应不要自行补造。
* 想让请求出现确定值，显式传参：`client.gallery_list(page=1, per_page=2)`。
* 因此参数表的「不传时怎样」写的是服务端行为（规范写的），不是代码里的行为；某格与实测对不上时会明确写。

## 客户端与通用约定（**客户端**）

* **类**：`Nhentai`，用法与其它家族一致：`with Nhentai('nhentai') as client:`。
* **构造**：`Nhentai(site_name=None, site_url=None, api_key=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。`api_key=None` 读包内配置 `sites.nhentai.api_key`；显式传 `api_key=''` 匿名；非空则每个请求带 `Authorization: Key <api_key>`。没有 User Token 构造参数。
* **站点根**：`https://nhentai.net`，不是 `https://nhentai.net/api/v2`。`api/v2` 属于路径一部分，每个原生方法自带。
* **路径**：本页表格「路由」列写相对 `api/v2` 的部分（如 `galleries/tagged`），方法内部拼成 `api/v2/galleries/tagged`；真实 URL 是 `https://nhentai.net/api/v2/galleries/tagged`。路径段（`gallery_id`、`tag_type`、`slug`、`suggestion_id`）按 `quote(str(x), safe='')` 转义后拼入（**客户端**），直接传 Python 字符串即可。
* **通用入口**：`request(method, path, *, params=None, data=None, headers=None)`。`path` 前导 `/` 去掉再拼到站点根后：`client.request('GET', 'api/v2/config')` 与 `client.site_config()` 打到同一地址。
* **查询参数编码**：`None` 的键不发送；布尔写成小写 `true` / `false`；其余原样进查询串。库不改参数名、不加参数、不排序。`tag_ids()` 的 `ids` 是一个逗号分隔字符串，库不会把 Python 列表拼成 CSV：写 `tag_ids('12227,6346')`，不要写 `tag_ids([12227, 6346])`。
* **正文**：`data`（以及 `tag_search()` / `blacklist_update()` 的 `**attributes`）原样作为 JSON 正文发出。库不补默认值、不补空数组、不删键。
* **请求头**：`headers` 同名键覆盖客户端配置的认证头（**客户端**），例如单次换 `Authorization` 写 `client.request('GET', 'api/v2/user', headers={'Authorization': 'Key 另一个Key'})`。
* **返回**：成功 JSON 正文完整解析后原样返回，不拆信封、不改字段名、不转换类型。信封在 `result` 键里（不是顶层数组）的方法占多数；只有 `gallery_popular()`、`tag_ids()`、`tag_search()`、`blacklist_ids()` 返回顶层数组，`gallery_comment_count()` 返回裸整数。
* **错误**：非 2xx 抛 `AnybooruHTTPError`（带 `http_code` / `url` / `body` / `data`）；2xx 但正文不是 JSON 时由共享请求层抛 `AnybooruAPIError`；2xx 空正文返回 `None`。库不重试、不降级；底层 requests 默认跟随重定向，冒烟与示例显式关闭跟随。
* **哪些方法要凭据**：`gallery_favorite()`、`favorite_add()`、`favorite_remove()`、`favorite_list()`、`favorite_random()`、`blacklist_list()`、`blacklist_update()`、`blacklist_ids()`、`gallery_download()`、`user_me()`——这 10 个规范写 `User Token or API Key`；构造器只提供 API Key 参数。其余 26 个匿名可调。其中 6 个匿名 `GET`（`gallery_favorite` / `favorite_list` / `favorite_random` / `blacklist_list` / `blacklist_ids` / `user_me`）实测回 `401 {"error": "Authentication required"}`，不带 Key 调它们拿到异常是预期行为。
* **`client.last_call`**：最近一次请求的 `API`（去掉前导 `/` 的路径原文）、`url`、`status_code`、`status`、`headers`。调试真实 URL 先看 `client.last_call['url']`。

## 36 个方法索引

「路由」列省略共同前缀 `/api/v2`；`JSON Pointer` 指向 <https://nhentai.net/api/v2/openapi.json> 内部。

| 方法 | 路由 | `operationId` | `JSON Pointer` | 认证 | 返回 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [`service_info()`](#service_info) | `GET /api/v2` | `api_root_api_v2_get` | `#/paths/~1api~1v2/get` | 匿名 | `ApiRootResponse` |
| [`cdn_config()`](#cdn_config) | `GET /api/v2/cdn` | `get_cdn_config_api_v2_cdn_get` | `#/paths/~1api~1v2~1cdn/get` | 匿名 | `CdnConfigResponse` |
| [`site_config()`](#site_config) | `GET /api/v2/config` | `get_config_api_v2_config_get` | `#/paths/~1api~1v2~1config/get` | 匿名 | `ConfigResponse` |
| [`gallery_list()`](#gallery_list) | `GET /api/v2/galleries` | `get_all_galleries_api_v2_galleries_get` | `#/paths/~1api~1v2~1galleries/get` | 匿名或 Key | `PaginatedResponse_GalleryListItem_` |
| [`gallery_tagged()`](#gallery_tagged) | `GET /api/v2/galleries/tagged` | `get_galleries_by_tag_api_v2_galleries_tagged_get` | `#/paths/~1api~1v2~1galleries~1tagged/get` | 匿名或 Key | `PaginatedResponse_GalleryListItem_` |
| [`gallery_popular()`](#gallery_popular) | `GET /api/v2/galleries/popular` | `get_popular_galleries_api_v2_galleries_popular_get` | `#/paths/~1api~1v2~1galleries~1popular/get` | 匿名或 Key | **顶层数组** `GalleryListItem[]` |
| [`gallery_random()`](#gallery_random) | `GET /api/v2/galleries/random` | `get_random_gallery_api_v2_galleries_random_get` | `#/paths/~1api~1v2~1galleries~1random/get` | 匿名或 Key | 对象（键名未规定） |
| [`gallery_show()`](#gallery_show) | `GET /api/v2/galleries/{gallery_id}` | `get_gallery_api_v2_galleries__gallery_id__get` | `#/paths/~1api~1v2~1galleries~1{gallery_id}/get` | 匿名或 Key | `GalleryDetailResponse` |
| [`gallery_related()`](#gallery_related) | `GET /api/v2/galleries/{gallery_id}/related` | `get_related_galleries_api_v2_galleries__gallery_id__related_get` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1related/get` | 匿名或 Key | `RelatedGalleriesResponse` |
| [`gallery_favorite()`](#gallery_favorite) | `GET /api/v2/galleries/{gallery_id}/favorite` | `check_favorite_api_v2_galleries__gallery_id__favorite_get` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1favorite/get` | **Key 必需** | `FavoriteResponse` |
| [`favorite_add()`](#favorite_add) | `POST /api/v2/galleries/{gallery_id}/favorite` | `add_to_favorites_api_v2_galleries__gallery_id__favorite_post` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1favorite/post` | **Key 必需**（写） | `FavoriteResponse` |
| [`favorite_remove()`](#favorite_remove) | `DELETE /api/v2/galleries/{gallery_id}/favorite` | `remove_from_favorites_api_v2_galleries__gallery_id__favorite_delete` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1favorite/delete` | **Key 必需**（写） | `FavoriteResponse` |
| [`gallery_suggestions()`](#gallery_suggestions) | `GET /api/v2/galleries/{gallery_id}/suggestions` | `list_gallery_suggestions_api_v2_galleries__gallery_id__suggestions_get` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1suggestions/get` | 匿名或 Key | `SuggestionListResponse` |
| [`gts_backlog()`](#gts_backlog) | `GET /api/v2/gts/backlog` | `list_gts_backlog_api_v2_gts_backlog_get` | `#/paths/~1api~1v2~1gts~1backlog/get` | 匿名或 Key | `BacklogListResponse` |
| [`gts_new_tags()`](#gts_new_tags) | `GET /api/v2/gts/new-tags` | `list_new_tag_index_api_v2_gts_new_tags_get` | `#/paths/~1api~1v2~1gts~1new-tags/get` | 匿名 | `NewTagIndexResponse` |
| [`gallery_download()`](#gallery_download) | `POST /api/v2/galleries/{gallery_id}/download` | `issue_download_url_api_v2_galleries__gallery_id__download_post` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1download/post` | **Key 必需**（写，未执行） | `DownloadResponse` |
| [`tag_ids()`](#tag_ids) | `GET /api/v2/tags/ids` | `get_tags_by_ids_api_v2_tags_ids_get` | `#/paths/~1api~1v2~1tags~1ids/get` | 匿名 | **顶层数组** `TagResponse[]` |
| [`tag_search()`](#tag_search) | `POST /api/v2/tags/search` | `search_tags_api_v2_tags_search_post` | `#/paths/~1api~1v2~1tags~1search/post` | 匿名（只读，未执行） | **顶层数组** `TagResponse[]` |
| [`tag_list()`](#tag_list) | `GET /api/v2/tags/{tag_type}` | `get_tags_by_type_api_v2_tags__tag_type__get` | `#/paths/~1api~1v2~1tags~1{tag_type}/get` | 匿名或 Key | `TagPaginatedResponse` |
| [`tag_show()`](#tag_show) | `GET /api/v2/tags/{tag_type}/{slug}` | `get_tag_by_slug_api_v2_tags__tag_type___slug__get` | `#/paths/~1api~1v2~1tags~1{tag_type}~1{slug}/get` | 匿名或 Key | `TagResponse` |
| [`taxonomy_list()`](#taxonomy_list) | `GET /api/v2/taxonomy` | `list_taxonomy_suggestions_api_v2_taxonomy_get` | `#/paths/~1api~1v2~1taxonomy/get` | 匿名或 Key | `TaxonomySuggestionListResponse` |
| [`taxonomy_stats()`](#taxonomy_stats) | `GET /api/v2/taxonomy/stats` | `get_taxonomy_suggestion_stats_api_v2_taxonomy_stats_get` | `#/paths/~1api~1v2~1taxonomy~1stats/get` | 匿名 | `TaxonomySuggestionStats` |
| [`taxonomy_resolved()`](#taxonomy_resolved) | `GET /api/v2/taxonomy/resolved` | `list_resolved_taxonomy_suggestions_api_v2_taxonomy_resolved_get` | `#/paths/~1api~1v2~1taxonomy~1resolved/get` | 匿名或 Key | `TaxonomySuggestionListResponse` |
| [`taxonomy_show()`](#taxonomy_show) | `GET /api/v2/taxonomy/{suggestion_id}` | `get_taxonomy_suggestion_api_v2_taxonomy__suggestion_id__get` | `#/paths/~1api~1v2~1taxonomy~1{suggestion_id}/get` | 匿名或 Key | `TaxonomySuggestionResponse` |
| [`taxonomy_comments()`](#taxonomy_comments) | `GET /api/v2/taxonomy/{suggestion_id}/comments` | `list_taxonomy_comments_api_v2_taxonomy__suggestion_id__comments_get` | `#/paths/~1api~1v2~1taxonomy~1{suggestion_id}~1comments/get` | 匿名或 Key | `TaxonomyCommentListResponse` |
| [`taxonomy_edits()`](#taxonomy_edits) | `GET /api/v2/taxonomy/{suggestion_id}/edits` | `list_taxonomy_edits_api_v2_taxonomy__suggestion_id__edits_get` | `#/paths/~1api~1v2~1taxonomy~1{suggestion_id}~1edits/get` | 匿名 | `TaxonomySuggestionEditListResponse` |
| [`gallery_comments()`](#gallery_comments) | `GET /api/v2/galleries/{gallery_id}/comments` | `get_gallery_comments_api_v2_galleries__gallery_id__comments_get` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1comments/get` | 匿名或 Key | `PaginatedResponse_CommentResponse_` |
| [`gallery_comment_count()`](#gallery_comment_count) | `GET /api/v2/galleries/{gallery_id}/comments/count` | `get_gallery_comment_count_api_v2_galleries__gallery_id__comments_count_get` | `#/paths/~1api~1v2~1galleries~1{gallery_id}~1comments~1count/get` | 匿名 | **裸整数** |
| [`search()`](#search) | `GET /api/v2/search` | `search_galleries_api_v2_search_get` | `#/paths/~1api~1v2~1search/get` | 匿名或 Key | `PaginatedResponse_GalleryListItem_` |
| [`favorite_list()`](#favorite_list) | `GET /api/v2/favorites` | `get_favorites_api_v2_favorites_get` | `#/paths/~1api~1v2~1favorites/get` | **Key 必需** | `PaginatedResponse_GalleryListItem_` |
| [`favorite_random()`](#favorite_random) | `GET /api/v2/favorites/random` | `get_random_favorite_api_v2_favorites_random_get` | `#/paths/~1api~1v2~1favorites~1random/get` | **Key 必需** | 对象（键名未规定） |
| [`blacklist_list()`](#blacklist_list) | `GET /api/v2/blacklist` | `get_blacklist_api_v2_blacklist_get` | `#/paths/~1api~1v2~1blacklist/get` | **Key 必需** | `BlacklistListResponse` |
| [`blacklist_update()`](#blacklist_update) | `POST /api/v2/blacklist` | `update_blacklist_api_v2_blacklist_post` | `#/paths/~1api~1v2~1blacklist/post` | **Key 必需**（写，未执行） | `BlacklistResponse` |
| [`blacklist_ids()`](#blacklist_ids) | `GET /api/v2/blacklist/ids` | `get_blacklist_ids_api_v2_blacklist_ids_get` | `#/paths/~1api~1v2~1blacklist~1ids/get` | **Key 必需** | **顶层整数数组** |
| [`user_show()`](#user_show) | `GET /api/v2/users/{user_id}/{slug}` | `get_user_profile_api_v2_users__user_id___slug__get` | `#/paths/~1api~1v2~1users~1{user_id}~1{slug}/get` | 匿名或 Key | `UserProfileResponse` |
| [`user_me()`](#user_me) | `GET /api/v2/user` | `get_me_api_v2_user_get` | `#/paths/~1api~1v2~1user/get` | **Key 必需** | `UserMeResponse` |

「认证」列：**匿名** = 规范 `Public (no authentication required)`；**匿名或 Key** = 规范 `Public (optional User Token or API Key for personalization)`，不带凭据也能 `200`，带 Key 只是让 `blacklisted`、`is_favorited`、`my_vote` 等个性化字段有意义；**Key 必需** = 规范 `User Token or API Key`，不带凭据按规范回 `401`。

## 服务与配置（3 个方法）

匿名只读，拿站点自报版本、CDN 服务器列表与公告。服务器列表是拼图片地址的唯一正确来源（见[规范给分组写的说明](#规范给分组写的说明规范tags)里的 `cdn` 条目）。

### service_info

给什么：无参数，无请求头要求，匿名。路由 `GET /api/v2`（没有结尾斜杠）。`operationId=api_root_api_v2_get`，JSON Pointer `#/paths/~1api~1v2/get`（`#/info` 之外，这是规范里最短的一条路径）。

返回 `ApiRootResponse`（**规范**：`#/components/schemas/ApiRootResponse`）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `version` | string | 是 | 服务端自报版本串。规范 `info.version` 是 `2.0.0+14bccf7`；**实测**这个键在 |
| `message` | string | 是 | 一句自报信息。**实测**这个键在，内容随站点变动 |

规范只列 `200`（无 422/429 条目——无参数，不在限流说明里）。**实测**：`GET https://nhentai.net/api/v2` → `200 application/json`，`version` 与 `message` 都在。老 API 路径 `/api/gallery/...` 是另一回事（回 `403`，见[边界与未实测](#旧的-api-与站点侧其它观察)）。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    root = client.service_info()
    # 真实 URL：GET https://nhentai.net/api/v2
    # 实测：200 application/json，两个键都在（具体取值未记录）
    print(root['version'], root['message'])
```

### cdn_config

给什么：无参数，匿名。路由 `GET /api/v2/cdn`。`operationId=get_cdn_config_api_v2_cdn_get`，JSON Pointer `#/paths/~1api~1v2~1cdn/get`。规范 `tags` 打 `cdn`。

返回 `CdnConfigResponse`（**规范**：`#/components/schemas/CdnConfigResponse`），两组字符串数组：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `image_servers` | string[] | 是 | 图片服务器前缀列表（规范说「URL 前缀」；**实测**键在，具体字符串未记录——列表会变，别硬编码子域） |
| `thumb_servers` | string[] | 是 | 缩略图服务器前缀列表 |

用法（**规范**：`#/tags/cdn`）：`GalleryListItem.thumbnail` 与 `PageInfo.path` 是相对路径，与这里一个服务器拼成完整 URL；不要硬编码子域，不要把 `path` 的扩展名、后缀、编号改掉或猜。规范只说「concatenate」，斜杠形态没写，拼法本身**待实测**，本页不写死 `rstrip('/') + path`。

规范只列 `200`。**实测**：`GET https://nhentai.net/api/v2/cdn` → `200 application/json`，正文只有 `image_servers` 与 `thumb_servers`（没有 `announcement`，那个在 `site_config()`）。服务器字符串会变，本页不抄。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    cdn = client.cdn_config()
    # 真实 URL：GET https://nhentai.net/api/v2/cdn
    # 规范返回：{"image_servers": [<string>, …], "thumb_servers": [<string>, …]}（取值待实测）
    print(cdn['image_servers'], cdn['thumb_servers'])
    # 拼完整地址：拿一个 image_servers 前缀 + gallery_show() 里 PageInfo 的 path（原样，不改不猜）
```

### site_config

给什么：无参数，匿名。路由 `GET /api/v2/config`。`operationId=get_config_api_v2_config_get`，JSON Pointer `#/paths/~1api~1v2~1config/get`。规范摘要：CDN 服务器 + 当前公告。

返回 `ConfigResponse`（**规范**：`#/components/schemas/ConfigResponse`）——`CdnConfigResponse` 加公告字段：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `image_servers` | string[] | 是 | 同 `cdn_config()` 图片服务器列表 |
| `thumb_servers` | string[] | 是 | 同 `cdn_config()` 缩略图服务器列表 |
| `announcement` | `Announcement` 或 `null` | 否（schema 可空） | 当前公告。**实测**：站点当时没有公告，键在、值是 `null`——不是缺键。判断有没有公告用「键存在且不为 `null`」，不要用 `'announcement' in config` |

`Announcement`（**规范**：`#/components/schemas/Announcement`）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `message` | string | 是 | 公告正文 |
| `links` | `AnnouncementLink[]`，默认 `[]` | 否 | 链接数组；缺省时服务端给空数组 |

`AnnouncementLink`（**规范**：`#/components/schemas/AnnouncementLink`）：`text`（string，必在）、`url`（string，必在）——纯字符串，规范没规定 `url` 是绝对还是站内相对。

规范只列 `200`。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    config = client.site_config()
    # 真实 URL：GET https://nhentai.net/api/v2/config
    # 规范返回：{"image_servers": […], "thumb_servers": […], "announcement": {"message": …, "links": […]}|null}
    print(config['thumb_servers'])
    if config.get('announcement'):
        print(config['announcement']['message'])
        print([link['url'] for link in config['announcement']['links']])
```

## 画廊：列表、详情、随机与相关（6 个方法）

六个方法共用对象：列表元素是 [`GalleryListItem`](#gallerylistitem)，详情是 [`GalleryDetailResponse`](#gallerydetailresponse)。列表类方法信封为 [`PaginatedResponse_*`](#分页信封paginatedresponse_)。

### gallery_list

给什么：`gallery_list(**params)`。路由 `GET /api/v2/galleries`。`operationId=get_all_galleries_api_v2_galleries_get`，JSON Pointer `#/paths/~1api~1v2~1galleries/get`。规范摘要（**规范**：`#/paths/~1api~1v2~1galleries/get/description`）：按最新在前分页返回画廊。认证：匿名可用，带 Key 让个性化字段有意义。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样（服务端） | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码（从 1 起，不是偏移量） | 服务端用 `1` | `page=2` |
| `per_page` | 整数，`1 ≤ per_page ≤ 100`，默认 `25` | 每页条数 | 服务端用 `25` | `per_page=2` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有上面两个参数；写别的名字站点收到陌生参数，行为未规定 |

返回 `PaginatedResponse_GalleryListItem_`（**规范**：`#/components/schemas/PaginatedResponse_GalleryListItem_`）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `result` | `GalleryListItem[]` | 是 | 本页画廊，元素见 [`GalleryListItem`](#gallerylistitem) |
| `num_pages` | integer | 是 | 总页数（按同一 `per_page` 计算） |
| `per_page` | integer，默认 `25` | 否 | 回显每页条数 |
| `total` | integer 或 `null` | 否 | 命中总数；schema 允许 `null`。**实测**：同类字段在 `gallery_tagged()` 上真的回 `null`，别当必有整数 |

**实测**（匿名 `GET`）：

* `GET https://nhentai.net/api/v2/galleries?page=1&per_page=2` → `200 application/json`，键 `result` / `num_pages` / `per_page` / `total`，`result` 2 条；`page=2&per_page=2` 同样 2 条。当次 `total` `646010`、`num_pages` `323037`——`num_pages` 不等于 `ceil(total / per_page)`（那样是 323005）。不要用 `total` 与 `per_page` 推页码边界，也别当精确总量。
* `per_page=100` → `200`，`result` 100 条；`per_page=101` → `400`（超上限，错误体见下）。
* `page=0&per_page=2` → **`400`**，正文 `{"error": "Validation error", "details": ["query -> page: Input should be greater than or equal to 1"]}`——不是规范的 `422 HTTPValidationError`。本库原样抛出，不做状态码归一化。
* `page=100000&per_page=25` → `200`，但只回 24 条且 id 从 25、24、22… 跳——超末页既不是空数组也不是干净最后一页。不要把「空 `result`」或「条数不足 `per_page`」当翻页终止条件。自己设页码上限或按业务范围取。

状态码（**规范**：`#/paths/~1api~1v2~1galleries/get/responses`）：`200`；`422`（参数校验失败，**实测为 `400`**）；`429`。限流（**规范**：同路径 `/get/description`）：匿名 `15/1min per IP`，带 User Token 或 Key `30/1min per IP`。本库不做节流与退避，打满限额会收到 `AnybooruHTTPError`（`http_code` `429`），调用方自己放慢。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    first = client.gallery_list(per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries?per_page=2
    # 实测：200，键 result/num_pages/per_page/total，per_page=2 时 result 2 条（具体 id 未记录）
    # 注意：num_pages 不等于 ceil(total / per_page)，不要自己折算
    for item in first['result']:
        print(item['id'], item['media_id'], item['num_pages'], item['tag_ids'])
    print(first['num_pages'], first['per_page'], first['total'])

with Nhentai('nhentai') as client:
    second = client.gallery_list(page=2, per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries?page=2&per_page=2
    print([item['id'] for item in second['result']])
```

### gallery_tagged

给什么：`gallery_tagged(tag_id, **params)`。路由 `GET /api/v2/galleries/tagged`。`operationId=get_galleries_by_tag_api_v2_galleries_tagged_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1tagged/get`。认证：匿名或 Key。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | 整数，**必填**（查询参数 `tag_id`） | 标签 id（不是名字、不是 slug） | 必填；不给属于参数校验失败（**实测**回 `400`）。规范的 `404` 是「标签/画廊查不到」 | `gallery_tagged(12227)` |
| `sort` | 枚举 `date` / `popular` / `popular-today` / `popular-week` / `popular-month`，默认 `date` | 排序方式 | 服务端用 `date` | `sort='popular'` |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码 | 服务端用 `1` | `page=2` |
| `per_page` | 整数，`1..100`，默认 `25` | 每页条数 | 服务端用 `25` | `per_page=2` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有上面四个参数；`tag`（名字）或 `tag_slug` 都不是它认识的参数名 |

`tag_id` 来源：用 [`tag_ids()`](#tag_ids)（一次多个，最多 100 个）或 [`tag_show()`](#tag_show)（`tag_show('language', 'english')`）拿对象的 `id`。本包示例配置字面值 `12227` 与 `6346`。

返回 `PaginatedResponse_GalleryListItem_`，字段同上。

状态码（**规范**）：`200`、`404`（标签不存在）、`422`、`429`。限流同上：匿名 `15/1min per IP`、带凭据 `30/1min per IP`。

**实测**（匿名 `GET`）：

* `GET https://nhentai.net/api/v2/galleries/tagged?tag_id=12227&per_page=2` → `200 application/json`，`result` 2 条、`num_pages` `73670`、**`total` 是 `null`**——「`total` 可空」实例：别做除法、别当总数，手上只有 `num_pages` 和本页条数。
* `tag_id=999999999` → `404`（本轮记录状态码；错误体没逐条记录，画廊 404 正文是 `{"error": "Gallery not found"}`，形状见[状态码与错误体](#状态码与错误体)）。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    tagged = client.gallery_tagged(12227, sort='popular', per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/tagged?tag_id=12227&sort=popular&per_page=2
    # 实测：200，键 result/num_pages/per_page/total，tag_id=12227、per_page=2 时 result 2 条、total 为 null
    print([item['id'] for item in tagged['result']])

with Nhentai('nhentai') as client:
    tag = client.tag_show('language', 'english')
    # 真实 URL：GET https://nhentai.net/api/v2/tags/language/english
    # 用同一次调用拿到的 id 去过滤，避免把标签名当 id
    print(tag['id'], tag['name'], tag['count'])
```

### gallery_popular

给什么：无参数，匿名或 Key。路由 `GET /api/v2/galleries/popular`。`operationId=get_popular_galleries_api_v2_galleries_popular_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1popular/get`。规范摘要：今天的热门画廊。

返回**顶层数组** `GalleryListItem[]`（**规范**：`#/paths/~1api~1v2~1galleries~1popular/get/responses/200/content/application~1json/schema` 的 `type: array` + `items: $ref GalleryListItem`）。条数由服务端决定，规范没写数量——不要断言固定 5 条。

状态码（**规范**）：`200`、`429`。限流：`8/1min per IP`（不分匿名与凭据）。

**实测**：`GET https://nhentai.net/api/v2/galleries/popular` → `200 application/json`，当次裸数组 5 条。规范没有 `minItems`/`maxItems`，`5` 只是那一刻读数，不是契约：别把 `len(popular) == 5` 写进断言。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    popular = client.gallery_popular()
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/popular
    # 规范返回：顶层数组 [GalleryListItem, …]（长度由服务端决定，规范未写）
    print(len(popular), popular[0]['id'], popular[0]['english_title'])
```

### gallery_random

给什么：无参数，匿名或 Key。路由 `GET /api/v2/galleries/random`。`operationId=get_random_gallery_api_v2_galleries_random_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1random/get`。规范摘要：返回一个随机画廊 id。

返回（**规范**：`#/paths/~1api~1v2~1galleries~1random/get/responses/200/content/application~1json/schema` 的 `{"type": "object", "additionalProperties": true}`）——规范没列字段名。**实测**：`GET https://nhentai.net/api/v2/galleries/random` → `200 application/json`，正文 `{"id": 641056}`——键名是 `id`。但规范仍没承诺只有这一个键，按 `random_gallery['id']` 取。拿到后接 [`gallery_show()`](#gallery_show)：

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    random_gallery = client.gallery_random()
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/random
    # 规范返回：一个 JSON 对象，字段名未规定（additionalProperties: true）
    # 实测：200，正文 {"id": <画廊编号>}
    print(random_gallery['id'])
    print(client.gallery_show(random_gallery['id'], include='')['media_id'])
```

状态码（**规范**）：`200`、`429`。限流：匿名 `20/1min per IP`，带凭据 `30/1min per IP`。

### gallery_show

给什么：`gallery_show(gallery_id, **params)`。路由 `GET /api/v2/galleries/{gallery_id}`。`operationId=get_gallery_api_v2_galleries__gallery_id__get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}/get`。规范摘要：单张画廊完整详情，可选附带数据。认证：匿名或 Key。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，**路径段**，必填 | 画廊编号，即 `GalleryListItem.id`（示例配置 `658856`） | 必填 | `gallery_show(658856)` |
| `include` | 字符串，默认 `""`；规范原文 `Comma-separated: comments,related,favorite,suggestions` | 逗号分隔，要求额外把哪些数据塞进响应 | 服务端用空串 = 不附带 | `include='comments,related'` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有 `include` 一个查询参数 |

返回 `GalleryDetailResponse`（**规范**：`#/components/schemas/GalleryDetailResponse`），完整字段见 [`GalleryDetailResponse`](#gallerydetailresponse)。要点：

* `title` 是对象不是字符串（`english` / `japanese` / `pretty`），见 [`GalleryTitle`](#gallerytitle)。
* `cover` 与 `thumbnail` 是 `CoverInfo`（`path` + `width` + `height`），`pages` 是 `PageInfo[]`。
* `comments`、`related`、`is_favorited`、`suggestions` 在 schema 里可空，与 `include` 四个取值对应（`favorite` 对应 `is_favorited`）。**实测**：带 `include` 时对应键才出现（`comments`、`comment_count`、`related`、`suggestions` 都现身过），不带 `include` 的样本没有；规范只标「可空」，取用一律 `gallery.get('related')`。
* `comment_count` schema 是 `int|null`，不在 `include` 四个取值里，但跟着 `include='comments,...'` 出现——更像 `comments` 伴随计数。规范没写规则，带 `include='comments'` 之外的条件**未实测**。
* `scanlator` schema 默认 `""`（没有汉化组就是空串）。

**实测**（匿名 `GET`）：

* `GET https://nhentai.net/api/v2/galleries/658856` → `200 application/json`：`media_id` `4006343`、`num_pages` `18`、`pages` 18 项（页数就是 `pages` 长度）；`title` 是对象，列表接口给 `english_title` / `japanese_title` 平铺字段——同一概念两套对象形状不同，解析分开处理。
* `include='comments,related,favorite,suggestions'` → `comments`、`comment_count`、`related`、`suggestions` 都出现，**但 `is_favorited` 没出现**。单独 `include='favorite'` 时响应形状与不带 `include` 相同，也没有可选字段——匿名下 `is_favorited` 没被填出。这符合直觉，但规范没写规则，带 Key 行为**未实测**：判断收藏状态用 [`gallery_favorite()`](#gallery_favorite)（要求凭据）。
* `GET https://nhentai.net/api/v2/galleries/999999999` → `404`，正文形状 `{"error": "Gallery not found"}`。
* 计数与 `pages` 长度是快照，会变，别当常量。

状态码（**规范**）：`200`、`404`（画廊不存在）、`422`、`429`。限流：匿名 `20/1min per IP`，带凭据 `45/1min per IP`。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    gallery = client.gallery_show(658856, include='comments,related')
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/658856?include=comments%2Crelated
    # 实测：200，id/media_id/num_pages/pages 等键与规范一致（具体取值未记录）
    print(gallery['id'], gallery['media_id'], gallery['num_pages'], gallery['num_favorites'])
    print(gallery['title']['english'], gallery['title']['pretty'], gallery['scanlator'])
    print(gallery['cover']['path'], gallery['thumbnail']['width'], gallery['thumbnail']['height'])
    for page in gallery['pages']:
        print(page['number'], page['path'], page['width'], page['height'])
    for tag in gallery['tags']:
        print(tag['type'], tag['name'], tag['slug'], tag['count'])
```

`include` 里没写的项不会附带；一次多项写成一整个逗号串：

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    gallery = client.gallery_show(658856, include='comments,related,favorite,suggestions')
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/658856?
    #          include=comments%2Crelated%2Cfavorite%2Csuggestions
    # 实测：这四个键出现（is_favorited 匿名时没出现）；具体内容未记录
    print(gallery['is_favorited'], gallery['comment_count'], gallery['related'])
    print(gallery['suggestions'])
```

### gallery_related

给什么：`gallery_related(gallery_id)`。路由 `GET /api/v2/galleries/{gallery_id}/related`。`operationId=get_related_galleries_api_v2_galleries__gallery_id__related_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1related/get`。规范摘要：与指定画廊相似的画廊。认证：匿名或 Key。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 参照画廊编号 | 必填 | `gallery_related(658856)` |

返回 `RelatedGalleriesResponse`（**规范**：`#/components/schemas/RelatedGalleriesResponse`）：只有 `result`（`GalleryListItem[]`，必在）。没有 `num_pages` / `per_page` / `total`，与分页信封不是一套，别照抄列表方法键名。

状态码（**规范**）：`200`、`404`、`422`、`429`。限流：匿名 `12/1min per IP`，带凭据 `30/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/galleries/658856/related` → `200 application/json`，正文 `{"result": [5 条 GalleryListItem]}`。条数规范没约束（无 `minItems`/`maxItems`），`5` 只是当次读数。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    related = client.gallery_related(658856)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/658856/related
    # 规范返回：{"result": [GalleryListItem, …]}（没有 total / num_pages）
    print([item['id'] for item in related['result']])
```

## 画廊收藏（3 个方法）

三个方法都要 Key（规范：`User Token or API Key`）：匿名调用**实测**回 `401 {"error": "Authentication required"}`，规范也列 `401`。三个返回同一个 `FavoriteResponse`（`favorited` + `num_favorites`）。后两个是写操作，本页与整个项目都不会执行，片段只写调用形态。

### gallery_favorite

给什么：`gallery_favorite(gallery_id)`。路由 `GET /api/v2/galleries/{gallery_id}/favorite`。`operationId=check_favorite_api_v2_galleries__gallery_id__favorite_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1favorite/get`。规范摘要：检查画廊是否在当前用户/Key 持有者收藏里——与 `gallery_show(..., include='favorite')` 同一件事，但独立请求，不拉整份详情。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 画廊编号 | 必填 | `gallery_favorite(658856)` |

返回 `FavoriteResponse`（**规范**：`#/components/schemas/FavoriteResponse`）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `favorited` | boolean | 是 | `true` = 在收藏里，`false` = 不在 |
| `num_favorites` | integer 或 `null` | 否 | 该画廊总收藏数 |

状态码（**规范**）：`200`、`401`（没带有效凭据）、`422`、`429`。限流：`15/1min per user` 与 `15/1min per API key owner`。

**实测**：匿名 `GET https://nhentai.net/api/v2/galleries/658856/favorite` → **`401 application/json`**，正文 `{"error": "Authentication required"}`。带 Key 成功响应**未实测**（本轮零凭据），`favorited` 实际取值无样本。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    favorite = client.gallery_favorite(658856)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/658856/favorite
    # 发送的头：Authorization: Key <你的 API Key>
    # 未实测：带 Key 的成功响应（匿名请求实测为 401 {"error": "Authentication required"}）
    print(favorite['favorited'], favorite['num_favorites'])
```

### favorite_add

> **写操作：会改账号数据，本项目从未执行过。** 规范要求站点侧开关 `allow_favorites` 打开，关掉时按规范回 `503`（`Feature is currently disabled`）。

给什么：`favorite_add(gallery_id)`。路由 `POST /api/v2/galleries/{gallery_id}/favorite`。`operationId=add_to_favorites_api_v2_galleries__gallery_id__favorite_post`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1favorite/post`。规范摘要：把画廊加进当前用户收藏。没有查询参数，也没有 JSON 正文——`POST` 不带 body。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 要收藏的画廊编号 | 必填 | `favorite_add(658856)`——**不要执行** |

返回 `FavoriteResponse`，字段同上。状态码（**规范**）：`200`、`401`、`404`（画廊不存在）、`422`、`503`（功能被关）、`429`。限流更细：`15/1min per user`、`15/1min per API key owner`、`15/1min per IP + user`、`15/1min per IP + API key owner`。

**未执行**：只说明调用形态，响应字段真实取值无实测。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    # POST https://nhentai.net/api/v2/galleries/658856/favorite
    # 未执行：写操作，本项目不发写请求。
    # 规范返回：{"favorited": true, "num_favorites": <int|null>}（规范只保证字段存在，取值未实测）
    result = client.favorite_add(658856)
    print(result['favorited'], result['num_favorites'])
```

### favorite_remove

> **写操作：会改账号数据，本项目从未执行过。** 同样受 `allow_favorites` 开关与 `503` 约束。

给什么：`favorite_remove(gallery_id)`。路由 `DELETE /api/v2/galleries/{gallery_id}/favorite`。`operationId=remove_from_favorites_api_v2_galleries__gallery_id__favorite_delete`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1favorite/delete`。规范摘要：把画廊从当前用户收藏移除。无查询参数、无正文。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 要取消收藏的画廊编号 | 必填 | `favorite_remove(658856)`——**不要执行** |

返回 `FavoriteResponse`；状态码、限流与 `favorite_add()` 完全相同（`200` / `401` / `404` / `422` / `503` / `429`）。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    # DELETE https://nhentai.net/api/v2/galleries/658856/favorite
    # 未执行：写操作。
    # 规范返回：{"favorited": false, "num_favorites": <int|null>}（规范只保证字段存在，取值未实测）
    result = client.favorite_remove(658856)
    print(result['favorited'], result['num_favorites'])
```

## 画廊标签建议（GTS，3 个方法）

GTS = Gallery Tag Suggestion：用户给某张画廊提议加或去一个标签，其他人投票，staff 决定接受或拒绝（**规范**：`#/tags/GTS`）。三个方法只读，都要求站点侧开关 `allow_gts` 打开，关掉时按规范回 `503`。提议、投票、接受/拒绝全是写操作或 moderation 路由，不在本包范围。

### gallery_suggestions

给什么：`gallery_suggestions(gallery_id, **params)`。路由 `GET /api/v2/galleries/{gallery_id}/suggestions`。`operationId=list_gallery_suggestions_api_v2_galleries__gallery_id__suggestions_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1suggestions/get`。规范摘要：列出该画廊当前的标签变更提议。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 画廊编号 | 必填 | `gallery_suggestions(658856)` |
| `tier` | 字符串，正则 `^(all\|trending\|active\|declined\|hidden\|mine\|history)$`，默认 `all` | 分类：全部 / 正在热 / 活跃 / 已否决 / 隐藏 / 我提的 / 历史 | 服务端用 `all` | `tier='active'` |
| `limit` | 整数，`1..100`，默认 `20` | 最多返回多少条 | 服务端用 `20` | `limit=2` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有 `tier` 与 `limit`；**没有分页参数**（不是 `page`/`per_page`） |

返回 `SuggestionListResponse`（**规范**：`#/components/schemas/SuggestionListResponse`）：`result`（`SuggestionResponse[]`，必在）、`has_more`（boolean 或 `null`）、`num_pages`（integer 或 `null`）、`total`（integer 或 `null`）。信封里只有 `result` 保证在，其余三个除类型可空外，规范没写何时给值。**实测**：当次正文 `{"result": []}`，三个可空键一个都没出现——取用写 `.get('total')`。元素见 [`SuggestionResponse`](#suggestionresponse)。

状态码（**规范**）：`200`、`422`、`503`、`429`。限流：`60/1min per IP`（不分匿名与凭据）。

**实测**：`GET https://nhentai.net/api/v2/galleries/658856/suggestions` → `200 application/json`，正文 `{"result": []}`——只有 `result`。功能开关当时开着（没吃 `503`），但只说明那一刻开着。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    suggestions = client.gallery_suggestions(658856, tier='active', limit=2)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/658856/suggestions?tier=active&limit=2
    # 规范返回：{"result": [SuggestionResponse, …], "has_more": <bool|null>, "num_pages": <int|null>, "total": <int|null>}
    for item in suggestions['result']:
        print(item['id'], item['action'], item['status'], item['tag']['name'], item['voter_count'])
```

### gts_backlog

给什么：`gts_backlog(**params)`。路由 `GET /api/v2/gts/backlog`。`operationId=list_gts_backlog_api_v2_gts_backlog_get`，JSON Pointer `#/paths/~1api~1v2~1gts~1backlog/get`。规范摘要：跨画廊列出还挂着的标签变更提议。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | 整数，`1..200`，默认 `1` | 页码 | 服务端用 `1` | `page=2` |
| `per_page` | 整数，`1..50`，默认 `20` | 每页条数 | 服务端用 `20` | `per_page=2` |
| `tag_id` | 整数且 `> 0`，或 `null` | 只看涉及这个标签 id 的提议 | 不筛（规范允许 `null`） | `tag_id=12227` |
| `action` | 字符串 `add` 或 `remove`，或 `null` | 只看「加标签」或「去标签」 | 不筛 | `action='add'` |
| `sort_by` | 字符串，正则 `^(starvation\|voters\|score\|gallery_age\|created_at)$`，默认 `starvation` | 饥饿度 / 投票人数 / 得分 / 画廊年龄 / 创建时间 | 服务端用 `starvation` | `sort_by='voters'` |
| `sort` | 字符串，正则 `^(asc\|desc)$`，默认 `asc` | 排序方向，与 `sort_by` 配对 | 服务端用 `asc` | `sort='desc'` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有上面六个参数 |

返回 `BacklogListResponse`（**规范**：`#/components/schemas/BacklogListResponse`）：`result`（`BacklogRow[]`，必在）、`has_more`（boolean，默认 `false`）、`num_pages`（integer 或 `null`）、`total`（integer 或 `null`）。每行 `{"suggestion": SuggestionResponse, "gallery": BacklogGallery}`，字段见 [`BacklogRow` / `BacklogGallery`](#backlogrow-与-backloggallery)。

状态码（**规范**）：`200`、`422`、`503`、`429`。限流：`60/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/gts/backlog?page=1&per_page=2` → `200 application/json`，`result` 2 条、`has_more` `true`、`num_pages` `27919`、`total` `55838`；每行确实是 `{"suggestion": …, "gallery": …}`。这里 `per_page` **被采纳**（回 2 条），和 `tag_list()` / `taxonomy_resolved()` 不一样——参数是否被采纳按端点看。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    backlog = client.gts_backlog(page=1, per_page=2, sort_by='voters', sort='desc')
    # 真实 URL：GET https://nhentai.net/api/v2/gts/backlog?page=1&per_page=2&sort_by=voters&sort=desc
    # 规范返回：{"result": [{"suggestion": …, "gallery": …}, …], "has_more": <bool>, "num_pages": <int|null>, "total": <int|null>}
    for row in backlog['result']:
        print(row['gallery']['id'], row['gallery']['age_days'],
              row['suggestion']['action'], row['suggestion']['tag']['name'])
```

### gts_new_tags

给什么：`gts_new_tags(**params)`。路由 `GET /api/v2/gts/new-tags`。`operationId=list_new_tag_index_api_v2_gts_new_tags_get`，JSON Pointer `#/paths/~1api~1v2~1gts~1new-tags/get`。规范摘要：列出最近由社区新铸的标签。认证：`Public (no authentication required)`——不需要凭据。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | 整数，`1..50`，默认 `25` | 最多返回多少个新标签 | 服务端用 `25` | `limit=2` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有 `limit` |

返回 `NewTagIndexResponse`（**规范**：`#/components/schemas/NewTagIndexResponse`）：只有 `result`（`NewTagIndexEntry[]`，必在）。条目见 [`NewTagIndexEntry`](#newtagindexentry)。

状态码（**规范**）：`200`、`422`、`503`、`429`。限流：`60/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/gts/new-tags?limit=2` → `200 application/json`，`result` 2 条，每条目键正是 `tag` / `created_at` / `pending_gts_count`。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    new_tags = client.gts_new_tags(limit=2)
    # 真实 URL：GET https://nhentai.net/api/v2/gts/new-tags?limit=2
    # 规范返回：{"result": [{"tag": TagResponse, "created_at": <int>, "pending_gts_count": <int>}, …]}
    for entry in new_tags['result']:
        print(entry['tag']['type'], entry['tag']['name'], entry['created_at'], entry['pending_gts_count'])
```

## 下载地址（1 个方法）

### gallery_download

> **写操作（分配资源）：会向站点申请短时效下载地址，本项目从未执行过。** 规范要求站点侧开关 `allow_downloads` 打开，关掉时按规范回 `503`。

给什么：`gallery_download(gallery_id, **params)`。路由 `POST /api/v2/galleries/{gallery_id}/download`。`operationId=issue_download_url_api_v2_galleries__gallery_id__download_post`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1download/post`。规范摘要：返回短时效 URL，指向 zip / cbz / torrent 文件；必须在 `expires_at`（unix 时间戳）之前取 `url`。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 画廊编号 | 必填 | `gallery_download(658856)`——**不要执行** |
| `format` | 枚举 `zip` / `cbz` / `torrent`，默认 `zip` | 打包格式 | 服务端用 `zip` | `format='cbz'`——**不要执行** |

返回 `DownloadResponse`（**规范**：`#/components/schemas/DownloadResponse`）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `url` | string | 是 | 下载地址；短时效，过期时间见 `expires_at` |
| `expires_at` | integer | 是 | 过期时刻 unix 时间戳（秒）；规范没写有效期多长，也没写要提前多久取才安全 |

状态码（**规范**）：`200`、`422`、`503`、`429`。限流按 `format` 分档（**规范**）：`format=torrent` 时 `5/1min per IP`、`10/5min per user`、`5/1min per API key owner`；`format=zip|cbz` 时 `10/5min per IP`、`7/5min per user`、`10/5min per API key owner`。

本库只给 URL 字符串，不下载字节，没有下载/解压/开种子方法。`url` 指向的主机与路径形态规范没写（本轮没跑，**未实测**）。按 `cdn` 组规范，整册压缩包走这条路由，不要自己拼 CDN 页面地址。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    # POST https://nhentai.net/api/v2/galleries/658856/download?format=cbz
    # 未执行：会分配站点资源的写操作，本项目不发。
    # 规范返回：{"url": <string>, "expires_at": <int>}（取值未实测）
    ticket = client.gallery_download(658856, format='cbz')
    print(ticket['url'], ticket['expires_at'])
    # 过期前自己去取；本库不替你下载任何字节
```

## 标签（4 个方法）

标签对象统一是 [`TagResponse`](#tagresponse)（`id` / `type` / `name` / `slug` / `url` / `count` / …）。`id` 是数字，`gallery_tagged()` 与 `gts_backlog(tag_id=…)` 要的就是它；`type` 与 `slug` 是 `tag_show()` / `tag_list()` 路径两段。这一组都不需要凭据（规范：`Public (no authentication required)`）。

### tag_ids

给什么：`tag_ids(ids)`。路由 `GET /api/v2/tags/ids`。`operationId=get_tags_by_ids_api_v2_tags_ids_get`，JSON Pointer `#/paths/~1api~1v2~1tags~1ids/get`。规范摘要：按 id 批量查标签，单次最多 100 个。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `ids` | 字符串，**必填**；规范原文 `Comma-separated tag IDs` | 一个逗号分隔字符串，如 `'12227,6346'` | 必填 | `tag_ids('12227,6346')` |

**`ids` 不是列表**：库原样放进查询串，不会替你 join。写 `tag_ids([12227, 6346])` 得到查询编码器对序列的输出（重复键），不是站点要的单串，请自己拼好字符串再传（**客户端**）。标签 id 来源：`TagResponse.id`（从 `tag_show()` 或 `gallery_show()` 的 `tags[].id` 拿）。

返回**顶层数组** `TagResponse[]`（**规范**：`#/paths/~1api~1v2~1tags~1ids/get/responses/200/content/application~1json/schema` 是 `type: array`）。不是分页信封，没有 `total`。规范没写「其中一个 id 不存在」时数组少一项还是给 `null`——**待实测**。

状态码（**规范**）：`200`、`422`、`429`。限流：`15/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/tags/ids?ids=12227%2C6346` → `200 application/json`，裸数组 2 条（就是这两个标签）。单次上限 100 是规范写的，本轮没试超 100。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    tags = client.tag_ids('12227,6346')
    # 真实 URL：GET https://nhentai.net/api/v2/tags/ids?ids=12227%2C6346
    # 规范返回：顶层数组 [TagResponse, …]（没有 total）
    for tag in tags:
        print(tag['id'], tag['type'], tag['name'], tag['slug'], tag['count'])
```

### tag_search

> **本轮没有执行过。** 这条路由是 `POST`，但只读检索：不改站点数据、不需要凭据（规范：`Public (no authentication required)`）。本轮只授权匿名 `GET`，一次都没发过；下面只有规范字段与调用形态。

给什么：`tag_search(**attributes)`。路由 `POST /api/v2/tags/search`。`operationId=search_tags_api_v2_tags_search_post`，JSON Pointer `#/paths/~1api~1v2~1tags~1search/post`。规范摘要：按名字前缀检索标签；`type` 不传跨全部类型搜。`**attributes` 原样成为 JSON 正文（**客户端**），正文 schema 是 `AutocompleteRequest`（**规范**：`#/paths/~1api~1v2~1tags~1search/post/requestBody/content/application~1json/schema` → `#/components/schemas/AutocompleteRequest`）：

| 正文键 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | 字符串或 `null`；schema **没有**标必填 | 检索前缀关键词 | 规范层面可整键不出现（`null` 也合法）；服务端怎么处理 `null`/缺键**规范没写，待实测** | `query='english'` |
| `type` | 字符串或 `null`；同样非必填 | 限定标签类型（如 `language`）；不传全部类型 | 同上 | `type='language'` |
| `limit` | 整数，`1 ≤ limit ≤ 50`，默认 `10` | 最多返回多少个标签 | 服务端用 `10` | `limit=3` |

三个键都能省，空正文 `{}` 规范层面合法（服务端给什么**待实测**）。调用形态（**未执行**）：

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    # POST https://nhentai.net/api/v2/tags/search
    # JSON 正文：{"query": "english", "type": "language", "limit": 3}
    # 未执行：本轮只发匿名 GET。
    # 规范返回：顶层数组 [TagResponse, …]
    matches = client.tag_search(query='english', type='language', limit=3)
    for tag in matches:
        print(tag['id'], tag['type'], tag['name'], tag['count'])

with Nhentai('nhentai') as client:
    # POST https://nhentai.net/api/v2/tags/search   正文：{}
    # 未执行：空正文在规范层面合法（三个键都不是必填），服务端行为待实测。
    all_types = client.tag_search()
    print(all_types)
```

返回**顶层数组** `TagResponse[]`（与 `tag_ids()` 一样，不是分页信封）。状态码（**规范**）：`200`、`400`（请求体不合法）、`422`、`429`。限流：`30/1min per IP`。

### tag_list

给什么：`tag_list(tag_type, **params)`。路由 `GET /api/v2/tags/{tag_type}`。`operationId=get_tags_by_type_api_v2_tags__tag_type__get`，JSON Pointer `#/paths/~1api~1v2~1tags~1{tag_type}/get`。规范摘要：按类型分页列出标签，同时支持页码分页与游标分页。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_type` | 字符串，**路径段**，必填 | 标签分类名（示例用 `language`） | 必填；不存在的分类按规范回 `400` | `tag_list('language')` |
| `sort` | 枚举 `name` / `popular`，默认 `popular` | 按名字或按热度（`count`） | 服务端用 `popular` | `sort='name'` |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码 | 服务端用 `1` | `page=1` |
| `per_page` | 整数，`1..100`，默认 `25` | 每页条数。**实测没被采纳**：请求 `per_page=1` 回 120 条、`per_page` 回显 120 | 服务端用 `25`（端点 schema 这么写；实测回显 120，两处对不上，以响应回显为准） | `per_page=2` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范条目只有上面三个参数，**没有任何游标参数名**（见「边界与未实测」） |

`tag_type` 允许值规范**没有列举**（只写 `type: string`）。示例配置用 `language`，配合 `tag_show('language', 'english')`。**实测**：不存在的分类名回 `400`，「调一次看是不是 `400`」是确认分类名的可靠办法（本轮 `tag` 与 `language` 都回 `200`）。

返回 `TagPaginatedResponse`（**规范**：`#/components/schemas/TagPaginatedResponse`）——分页信封变体，多一个 `alphabet`：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `result` | `TagResponse[]` | 是 | 本页标签 |
| `num_pages` | integer | 是 | 总页数 |
| `per_page` | integer，schema 默认 `120` | 否 | 每页条数。**注意**：端点参数 `per_page` 默认 `25`、上限 `100`，响应字段 schema 默认 `120`——不一致，以回显为准 |
| `total` | integer 或 `null` | 否 | 标签总数 |
| `alphabet` | object 或 `null` | 否 | 字母索引：对象值是「整数数组或 `null`」。**实测**：只有 `sort=name` 时出现，默认 `popular` 时没有；内部键名本轮没记录，**未实测** |

状态码（**规范**）：`200`、`400`（分类不合法）、`422`、`429`。限流：匿名 `15/1min per IP`，带 User Token 或 Key `30/1min per IP`。

**实测**（匿名 `GET`）——三个反直觉点：

* `GET https://nhentai.net/api/v2/tags/tag?per_page=1` → `200 application/json`，`result` **120 条**、`per_page` 回显 `120`、`total` `4722`、`num_pages` `40`、没有 `alphabet`（`sort` 默认 `popular`）。请求写了 `per_page=1`，站点没采纳，用了 120。
* `GET https://nhentai.net/api/v2/tags/language?sort=name&per_page=1` → `200`，`result` `14` 条、`per_page` `120`、`total` `14`、`num_pages` `1`，**`alphabet` 键在**。`alphabet` 跟着 `sort=name` 来（本轮样本如此），默认 `popular` 没有。内部结构本轮没记录，**键名与值形态未实测**，别猜。
* **列表元素与详情的字段不一致**：列表项没有 `is_community` 与 `pending_describe_id`，`tag_show()` 详情里这两个键在（值可为 `null`）。同一 `TagResponse` 两处填充不同，按列表渲染别指望这两个键。
* 分类名不是随便写的：`tag_type` 不存在 → `400`（实测）；本轮用过 `tag` 与 `language` 都回 `200`。规范没列允许值，能用名字以站点实际为准。
* 分页参数被忽略意味着 `result` 条数由服务端定（120），`num_pages` 也按服务端 `per_page` 算；不要用你请求的 `per_page` 乘页码。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    page = client.tag_list('language', sort='popular', per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/tags/language?sort=popular&per_page=2
    # 规范返回：{"result": [TagResponse, …], "num_pages": <int>, "per_page": <int>, "total": <int|null>, "alphabet": <object|null>}
    for tag in page['result']:
        print(tag['id'], tag['name'], tag['count'])
    print(page['num_pages'], page['per_page'], page['total'], page['alphabet'])

with Nhentai('nhentai') as client:
    by_name = client.tag_list('language', sort='name', page=1, per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/tags/language?sort=name&page=1&per_page=2
    print([tag['name'] for tag in by_name['result']])
```

### tag_show

给什么：`tag_show(tag_type, slug)`。路由 `GET /api/v2/tags/{tag_type}/{slug}`。`operationId=get_tag_by_slug_api_v2_tags__tag_type___slug__get`，JSON Pointer `#/paths/~1api~1v2~1tags~1{tag_type}~1{slug}/get`。规范摘要：按类型 + slug 取一个标签。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_type` | 字符串，路径段，必填 | 标签分类名，同 `tag_list()` | 必填 | `tag_show('language', 'english')` |
| `slug` | 字符串，路径段，必填 | 标签 slug（`TagResponse.slug`，如 `english`、`big-breasts`） | 必填 | `tag_show('language', 'english')` |

返回单个 `TagResponse`（**规范**：`#/components/schemas/TagResponse`），字段见 [`TagResponse`](#tagresponse)。`count` 是该标签下画廊数（规范只写 `integer`，口径**待实测**）。

状态码（**规范**）：`200`、`404`（类型或 slug 不存在）、`422`、`429`。限流：匿名 `15/1min per IP`，带凭据 `30/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/tags/language/english` → `200 application/json`，正文裸对象（没信封），键有 `id`、`type`、`name`、`slug`、`url`、`count`、`description`、`is_community`、`pending_describe_id`——比 `tag_list()` 列表元素多后两个。`count` 是那一刻该标签下画廊数，会变。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    tag = client.tag_show('language', 'english')
    # 真实 URL：GET https://nhentai.net/api/v2/tags/language/english
    # 规范返回：{"id": <int>, "type": "language", "name": …, "slug": "english", "url": …, "count": <int>, …}
    print(tag['id'], tag['type'], tag['slug'], tag['count'])
    # 这个 id 就是 gallery_tagged() 与 gts_backlog(tag_id=…) 要传的值
    print(client.gallery_tagged(tag['id'], per_page=2)['result'][0]['id'])
```

## 标签体系建议（taxonomy，6 个方法）

taxonomy 是全局标签体系的提议账本：新建 / 改名 / 合并 / 补描述（**规范**：`#/tags/taxonomy`），与 GTS「某张画廊加个标签」不是一回事。6 个方法只读，都要求站点侧开关 `allow_taxonomy` 打开，关掉时按规范回 `503`；写路由（发起提议、投票、改提议、删提议、发评论）不在本包范围。

### taxonomy_list

给什么：`taxonomy_list(**params)`。路由 `GET /api/v2/taxonomy`。`operationId=list_taxonomy_suggestions_api_v2_taxonomy_get`，JSON Pointer `#/paths/~1api~1v2~1taxonomy/get`。规范摘要：列出还挂着的标签体系提议。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tier` | 字符串，正则 `^(all\|trending\|active\|declined\|mine)$`，默认 `all` | 分类筛选（比 GTS 的 `tier` 少 `hidden` 与 `history`） | 服务端用 `all` | `tier='active'` |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码 | 服务端用 `1` | `page=1` |
| `per_page` | 整数，`1..200`，默认 `50` | 每页条数（上限 200） | 服务端用 `50` | `per_page=2` |
| `q` | 字符串，长度 `1..100`，或 `null` | 关键词过滤 | 不筛 | `q='english'` |
| `target_tag_id` | 整数且 `> 0`，或 `null` | 只看针对某个标签 id 的提议 | 不筛 | `target_tag_id=12227` |
| `sort_by` | 字符串，正则 `^(score\|votes\|comment_count\|last_comment_at\|created_at)$`，默认 `score` | 得分（票数和）/ 投票人数 / 评论数 / 最后评论时间 / 创建时间 | 服务端用 `score` | `sort_by='votes'` |
| `sort` | 字符串，正则 `^(asc\|desc)$`，默认 `desc` | 排序方向，与 `sort_by` 配对 | 服务端用 `desc` | `sort='asc'` |
| `action` | 字符串或 `null`；规范原文 `Comma-separated subset of create,rename,merge,describe. Defaults to all.` | 只看某几类动作，多个逗号隔开 | 服务端默认全部四类 | `action='create,rename'` |
| `discussion` | 字符串，正则 `^(with\|without)$`，或 `null`；`with` = 至少一条评论，`without` = 一条都没有 | 按有没有讨论筛 | 不筛 | `discussion='with'` |
| `edited` | 字符串，正则 `^(yes\|no)$`，或 `null`；`yes` = 被编辑过，`no` = 从未编辑 | 按有没有被改过筛 | 不筛 | `edited='yes'` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有上面十个参数 |

返回 `TaxonomySuggestionListResponse`（**规范**：`#/components/schemas/TaxonomySuggestionListResponse`）：`result`（`TaxonomySuggestionResponse[]`，必在）、`has_more`（boolean 或 `null`）、`num_pages`（integer 或 `null`）、`total`（integer 或 `null`）。元素见 [`TaxonomySuggestionResponse`](#taxonomysuggestionresponse)。

状态码（**规范**）：`200`、`422`、`503`、`429`。限流：`120/1min per IP`（这组限额普遍更高）。

**实测**：`GET https://nhentai.net/api/v2/taxonomy?per_page=2` → `200 application/json`，`result` 2 条、`has_more` `true`、`num_pages` `1492`、`total` `2984`；这里 `per_page` 被采纳。当次一条提议 id `9d1099af-1f2e-4a22-ab73-3f935f4a6b54`——uuid 就这样，可直接拿去 [`taxonomy_show()`](#taxonomy_show)（随时可能被处理掉，取不到就当过期）。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    pending = client.taxonomy_list(sort_by='votes', sort='desc', per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/taxonomy?sort_by=votes&sort=desc&per_page=2
    # 规范返回：{"result": [TaxonomySuggestionResponse, …], "has_more": <bool|null>, "num_pages": <int|null>, "total": <int|null>}
    for item in pending['result']:
        print(item['id'], item['action'], item['status'], item['score'], item['voter_count'])
```

### taxonomy_stats

给什么：无参数，匿名。路由 `GET /api/v2/taxonomy/stats`。`operationId=get_taxonomy_suggestion_stats_api_v2_taxonomy_stats_get`，JSON Pointer `#/paths/~1api~1v2~1taxonomy~1stats/get`。规范摘要：taxonomy 活动概览 = 待处理数量 + 最近被接受的提议。

返回 `TaxonomySuggestionStats`（**规范**：`#/components/schemas/TaxonomySuggestionStats`），字段多，全是计数（除最后数组）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `pending` | integer | 是 | 还在挂着的提议数 |
| `accepted_total` / `rejected_total` | integer | 是 | 历史累计被接受 / 被拒绝的提议数 |
| `accepted_30d` / `accepted_7d` | integer | 是 | 近 30 天 / 近 7 天被接受的提议数 |
| `created_30d` | integer | 是 | 近 30 天新建的提议数 |
| `renamed_30d` / `merged_30d` / `described_30d` | integer | 是 | 近 30 天改名 / 合并 / 补描述数量 |
| `trending_count` / `active_count` / `declined_count` | integer，默认 `0` | 否 | 各分类当前条数 |
| `recent_accepted` | [`TaxonomySuggestionResponse`](#taxonomysuggestionresponse) | 是 | 最近被接受的提议列表，元素见 [`TaxonomySuggestionResponse`](#taxonomysuggestionresponse)；条数规范没写，本轮也没记录当次长度 |

规范只写字段名与类型，每个计数时间口径（滚动 30 天？自然月？）没说，别把 `*_30d` 当某个具体日期统计对账。

状态码（**规范**）：`200`、`503`、`429`（没有 `422`——无参数）。限流：`30/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/taxonomy/stats` → `200 application/json`，正文键数 13 个，与上表一一对上（含 `recent_accepted`）。具体计数值不抄，是快照。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    stats = client.taxonomy_stats()
    # 真实 URL：GET https://nhentai.net/api/v2/taxonomy/stats
    # 规范返回：{"pending": <int>, "accepted_total": <int>, …, "recent_accepted": [TaxonomySuggestionResponse, …]}
    print(stats['pending'], stats['accepted_7d'], stats['merged_30d'], len(stats['recent_accepted']))
```

### taxonomy_resolved

给什么：`taxonomy_resolved(**params)`。路由 `GET /api/v2/taxonomy/resolved`。`operationId=list_resolved_taxonomy_suggestions_api_v2_taxonomy_resolved_get`，JSON Pointer `#/paths/~1api~1v2~1taxonomy~1resolved/get`。规范摘要：列出已处理的提议（规范 `taxonomy` 分组说这是带 staff 结论的公开账本）。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `status` | 字符串，正则 `^(all\|accepted\|rejected)$`，默认 `all` | 只看被接受 / 被拒绝 / 全部 | 服务端用 `all` | `status='accepted'` |
| `q` | 字符串，长度 `1..100`，或 `null` | 关键词过滤 | 不筛 | `q='english'` |
| `discussion` | 字符串，正则 `^(with\|without)$`，或 `null` | 按有没有评论筛 | 不筛 | `discussion='without'` |
| `edited` | 字符串，正则 `^(yes\|no)$`，或 `null` | 按有没有被编辑过筛 | 不筛 | `edited='no'` |
| `action` | 字符串或 `null`；规范原文 `Comma-separated subset of create,rename,merge,describe.` | 只看某几类动作（**注意**：这条没写 `Defaults to all`，省略时行为规范没明说） | 不筛（规范未明说） | `action='merge'` |
| `sort_by` | 字符串，正则 `^(resolved_at\|score\|votes\|comment_count\|last_comment_at\|created_at)$`，默认 `resolved_at` | 排序字段（默认按处理时间，与 `taxonomy_list()` 默认 `score` 不同） | 服务端用 `resolved_at` | `sort_by='resolved_at'` |
| `sort` | 字符串，正则 `^(asc\|desc)$`，默认 `desc` | 排序方向 | 服务端用 `desc` | `sort='desc'` |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码 | 服务端用 `1` | `page=1` |
| `per_page` | 整数，`1..100`，默认 `25` | 每页条数（上限 100，比 `taxonomy_list()` 的 200 小） | 服务端用 `25` | `per_page=2` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有上面九个参数 |

返回 `TaxonomySuggestionListResponse`，与 `taxonomy_list()` 同一套（`result` / `has_more` / `num_pages` / `total`）。

状态码（**规范**）：`200`、`422`、`503`、`429`。限流：`90/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/taxonomy/resolved?per_page=2` → `200 application/json`，可 `result` 回 **50 条**、`num_pages` `4`、`total` `196`、`has_more` `true`——你传的 `per_page=2` 没被采纳（站点用 50）。本轮另试规范里没有的 `limit=2`，同样回 50 条，说明它不是被识别的分页参数。这条路由每页条数不要指望自己控制；`num_pages` 按服务端每页条数算（`196 / 50` 上取整 = 4）。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    ledger = client.taxonomy_resolved(status='accepted', sort_by='resolved_at', per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/taxonomy/resolved?status=accepted&sort_by=resolved_at&per_page=2
    # 规范返回：{"result": [TaxonomySuggestionResponse, …], "has_more": <bool|null>, "num_pages": <int|null>, "total": <int|null>}
    for item in ledger['result']:
        print(item['id'], item['action'], item['resolved_at'], item['resolver'], item['resolution_note'])
```

### taxonomy_show

给什么：`taxonomy_show(suggestion_id)`。路由 `GET /api/v2/taxonomy/{suggestion_id}`。`operationId=get_taxonomy_suggestion_api_v2_taxonomy__suggestion_id__get`，JSON Pointer `#/paths/~1api~1v2~1taxonomy~1{suggestion_id}/get`。规范摘要：取一条提议，附带最近一条评论预览。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `suggestion_id` | 字符串，格式 **uuid**（`format: uuid`），路径段，必填 | 提议编号，从 `taxonomy_list()` / `taxonomy_resolved()` 的 `result[].id` 拿 | 必填 | `taxonomy_show('9d1099af-1f2e-4a22-ab73-3f935f4a6b54')`（本轮实测请求过的一个 uuid，可能已过期） |

**这是 uuid 不是数字**：`id` 在 `TaxonomySuggestionResponse` 是 string + `format: uuid`，传整数会被编码成十进制写法，站点按「不是合法 uuid」处理（规范列 `404`）。**实测**：`GET https://nhentai.net/api/v2/taxonomy/9d1099af-1f2e-4a22-ab73-3f935f4a6b54` → `200 application/json`（这个 uuid 从 `taxonomy_list()` 当次结果取，之后可能已被处理掉）。另一条：**列表元素带 `tier` 与 `tier_page`，详情里这两个键没出现**——同一 schema 不同路由填的字段不一样，别假定详情一定有。

返回单个 `TaxonomySuggestionResponse`（字段见 [`TaxonomySuggestionResponse`](#taxonomysuggestionresponse)），其中 `target_tag` / `merge_into_tag` / `new_name` / `new_type` / `new_description` / `accepted_*` / `resolved_tag` 按提议动作类型取用：`create` 用 `new_*`，`rename`/`merge` 用 `target_tag` 与 `merge_into_tag`，`describe` 用 `new_description`，被接受后最终取值在 `accepted_*` / `resolved_tag`（**规范**：`#/components/schemas/TaxonomySuggestionResponse` 的字段清单与 `#/components/schemas/TaxonomySuggestionEditChange/description`；**哪个动作填哪几个字段，规范没逐条写清，待实测**）。

状态码（**规范**）：`200`、`404`、`422`、`503`、`429`。限流：`120/1min per IP`。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    listing = client.taxonomy_list(per_page=1)
    if listing['result']:
        suggestion_id = listing['result'][0]['id']   # uuid 字符串，直接从列表里取
        suggestion = client.taxonomy_show(suggestion_id)
        # 真实 URL：GET https://nhentai.net/api/v2/taxonomy/<uuid>
        # 规范返回：TaxonomySuggestionResponse（含 recent_comments）
        print(suggestion['action'], suggestion['status'], suggestion['tier'], suggestion['comment_count'])
        print(suggestion['target_tag'], suggestion['new_name'], suggestion['resolved_tag'])
```

### taxonomy_comments

给什么：`taxonomy_comments(suggestion_id, **params)`。路由 `GET /api/v2/taxonomy/{suggestion_id}/comments`。`operationId=list_taxonomy_comments_api_v2_taxonomy__suggestion_id__comments_get`，JSON Pointer `#/paths/~1api~1v2~1taxonomy~1{suggestion_id}~1comments/get`。规范摘要：列出某条提议下的评论。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `suggestion_id` | 字符串 uuid，路径段，必填 | 提议编号 | 必填 | 同上，从列表接口取 |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码 | 服务端用 `1` | `page=1` |
| `per_page` | 整数，`1..100`，默认 `50` | 每页条数 | 服务端用 `50` | `per_page=2` |

返回 `TaxonomyCommentListResponse`（**规范**：`#/components/schemas/TaxonomyCommentListResponse`）：`result`（`TaxonomyCommentResponse[]`，必在）、`has_more`（boolean 或 `null`）、`num_pages`（integer 或 `null`）、`total`（integer 或 `null`）。元素见 [`TaxonomyCommentResponse`](#taxonomycommentresponse)。

状态码（**规范**）：`200`、`404`、`422`、`503`、`429`。限流：`120/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/taxonomy/<uuid>/comments?page=1&per_page=2` → `200 application/json`，`result` 2 条、`has_more` `true`、`num_pages` `10`、`total` `19`——这条路由 `per_page` **被采纳**。每条评论键与 [`TaxonomyCommentResponse`](#taxonomycommentresponse) 一致（`id`、`body`、`author`、`created_at`、`can_delete`、`link_previews`）。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    listing = client.taxonomy_list(per_page=1)
    if listing['result']:
        comments = client.taxonomy_comments(listing['result'][0]['id'], per_page=2)
        # 真实 URL：GET https://nhentai.net/api/v2/taxonomy/<uuid>/comments?per_page=2
        # 实测：200，result 2 条、has_more true、num_pages 10、total 19（计数会变）
        for comment in comments['result']:
            print(comment['id'], comment['author']['username'], comment['created_at'], comment['can_delete'])
            print(comment['body'])   # 展示时请遵守站点内容规范
```

### taxonomy_edits

给什么：`taxonomy_edits(suggestion_id)`。路由 `GET /api/v2/taxonomy/{suggestion_id}/edits`。`operationId=list_taxonomy_edits_api_v2_taxonomy__suggestion_id__edits_get`，JSON Pointer `#/paths/~1api~1v2~1taxonomy~1{suggestion_id}~1edits/get`。规范摘要：列出某条提议的编辑历史。认证：匿名（无需凭据）。无查询参数。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `suggestion_id` | 字符串 uuid，路径段，必填 | 提议编号 | 必填 | 同上，从列表接口取 |

返回 `TaxonomySuggestionEditListResponse`（**规范**：`#/components/schemas/TaxonomySuggestionEditListResponse`）：只有 `result`（`TaxonomySuggestionEditEntry[]`，必在）——没有分页键。条目、字段改动见 [`TaxonomySuggestionEditEntry`](#taxonomysuggestioneditentry)。要点：一次编辑事件里 `changes[]` 每项是「字段名 + 旧值 + 新值」，标签类字段（`target_tag`、`merge_into_tag`）存 `type:name` 人类可读快照，不是 id（**规范**：`#/components/schemas/TaxonomySuggestionEditChange/description`），标签被删历史也看得懂。

状态码（**规范**）：`200`、`404`、`422`、`503`、`429`。限流：`120/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/taxonomy/<uuid>/edits` → `200 application/json`，正文 `{"result": []}`——当次那条提议没被编辑过，空数组是正常结果，不是错误，且这种时候连 `result` 以外的键都没有。非空编辑历史本轮没拿到。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    listing = client.taxonomy_list(per_page=1)
    if listing['result']:
        edits = client.taxonomy_edits(listing['result'][0]['id'])
        # 真实 URL：GET https://nhentai.net/api/v2/taxonomy/<uuid>/edits
        # 规范返回：{"result": [{"id": <uuid>, "created_at": …, "summary": …, "changes": […], "editor": …}, …]}
        for entry in edits['result']:
            print(entry['created_at'], entry['summary'], entry['editor'])
            for change in entry['changes']:
                print(change['field'], change['old_value'], change['new_value'])
```

## 画廊评论（2 个方法）

评论对象是 [`CommentResponse`](#commentresponse)（`id` / `gallery_id` / `poster` / `post_date` / `body`）。`schema` 注释写「匹配 Django 格式」——`post_date` 是整数 unix 时间戳、`poster` 是 [`UserPublic`](#userpublic) 对象，不是用户名字符串。

### gallery_comments

给什么：`gallery_comments(gallery_id, **params)`。路由 `GET /api/v2/galleries/{gallery_id}/comments`。`operationId=get_gallery_comments_api_v2_galleries__gallery_id__comments_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1comments/get`。规范摘要：分页列出某张画廊的可见评论，最新在前。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 画廊编号 | 必填 | `gallery_comments(658856, per_page=2)` |
| `page` | 整数，`1 ≤ page ≤ 2000`，默认 `1` | 页码（上限 2000，比其它列表宽） | 服务端用 `1` | `page=1` |
| `per_page` | 整数，`1..50`，默认 `50` | 每页条数（注意 `gallery_list()` 是 100，这里 50） | 服务端用 `50` | `per_page=2` |

返回 `PaginatedResponse_CommentResponse_`（**规范**：`#/components/schemas/PaginatedResponse_CommentResponse_`）：`result`（`CommentResponse[]`，必在）、`num_pages`（integer，必在）、`per_page`（integer，schema 默认 `25`——又与端点默认 `50` 不一致，以回显为准）、`total`（integer 或 `null`）。

状态码（**规范**）：`200`、`404`、`422`、`429`。限流：匿名 `30/1min per IP`，带 User Token 或 Key `60/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/galleries/658856/comments?page=1&per_page=2` → `200 application/json`，正文 `{"result": [], "num_pages": 0, "per_page": 2, "total": 0}`。该画廊当次没有可见评论：「没有评论」是空 `result` + `num_pages` `0` + `total` `0`，不是 `404`；`total` 这里给整数 `0`（规范允许 `null`，但没出现）。`per_page=2` 被采纳。**非空评论样本本轮没拿到**，`poster`、`post_date` 真实取值无实测（形状按规范）。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    comments = client.gallery_comments(658856, page=1, per_page=2)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/658856/comments?page=1&per_page=2
    # 实测：200 {"result": [], "num_pages": 0, "per_page": 2, "total": 0}（这条画廊当次没有评论）
    print(comments['result'], comments['num_pages'], comments['per_page'], comments['total'])
```

### gallery_comment_count

给什么：`gallery_comment_count(gallery_id)`。路由 `GET /api/v2/galleries/{gallery_id}/comments/count`。`operationId=get_gallery_comment_count_api_v2_galleries__gallery_id__comments_count_get`，JSON Pointer `#/paths/~1api~1v2~1galleries~1{gallery_id}~1comments~1count/get`。规范摘要：取某张画廊的可见评论数。认证：匿名（无需凭据）。无查询参数。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `gallery_id` | 整数，路径段，必填 | 画廊编号 | 必填 | `gallery_comment_count(658856)` |

返回**一个裸整数**（**规范**：`#/paths/~1api~1v2~1galleries~1{gallery_id}~1comments~1count/get/responses/200/content/application~1json/schema` 的 `type: integer`）——不是对象、不是信封，库里不会替你包一层。

状态码（**规范**）：`200`、`404`、`422`、`429`。限流：匿名 `12/1min per IP`，带 User Token 或 Key `20/1min per IP`。

**实测**：`GET https://nhentai.net/api/v2/galleries/658856/comments/count` → `200 application/json`，正文 `0`（该画廊当次没有评论）。站点变更日志页提到评论有 50 条上限，正好和规范 `gallery_comments()` 的 `per_page` 上限 50 对上；该日志页地址 `/api/v2/changelog`（`200 text/html`，**实测**，见[边界与未实测](#旧的-api-与站点侧其它观察)）。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    count = client.gallery_comment_count(658856)
    # 真实 URL：GET https://nhentai.net/api/v2/galleries/658856/comments/count
    # 实测：200，正文是裸整数 0（这条画廊当次没有评论）
    print(count, isinstance(count, int))
```

## 搜索（1 个方法）

### search

给什么：`search(query, **params)`。路由 `GET /api/v2/search`。`operationId=search_galleries_api_v2_search_get`，JSON Pointer `#/paths/~1api~1v2~1search/get`。规范摘要：全文检索画廊，支持关键词、精确短语、排除、标签过滤、数字过滤与日期过滤。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | 字符串，`minLength: 1`，**必填** | 检索式，语法见下表 | 必填；不给按规范回 `422`（**实测回 `400`**，见下） | `search('language:english', sort='date', page=1)` |
| `sort` | 枚举 `date` / `popular` / `popular-today` / `popular-week` / `popular-month`，默认 `date` | 排序方式（与 `gallery_tagged()` 同一套） | 服务端用 `date` | `sort='popular-week'` |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码 | 服务端用 `1` | `page=2` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有上面三个参数，**没有 `per_page`**（详见下） |

`query` 语法（**规范**：`#/paths/~1api~1v2~1search/get/description` 原文举例）：

| 写法 | 含义 |
| :--- | :--- |
| `word` | 关键词 |
| `"exact phrase"` | 精确短语 |
| `-word`、`-"exact phrase"`、`-artist:name` | 排除 |
| `artist:name`、`language:english`、`tag:"big breasts"` | 标签过滤（分类 + 名字/slug） |
| `pages:>10`、`favorites:>=100` | 数字过滤 |
| `uploaded:<7d`、`uploaded:>1m` | 日期过滤 |

返回 `PaginatedResponse_GalleryListItem_`（`result` / `num_pages` / `per_page` / `total`），元素是 [`GalleryListItem`](#gallerylistitem)——与 `gallery_list()` 同一套信封。

状态码（**规范**）：`200`、`422`、`429`。限流：匿名 `10/1min per IP`，带 User Token 或 Key `20/1min per IP`（这组最低，翻页要克制）。

**实测**（匿名 `GET`）：

* `GET https://nhentai.net/api/v2/search?query=language%3Aenglish&sort=date&page=1` → `200 application/json`，`per_page` `25`、`total` `147497`、`num_pages` `5900`，`result` 25 条。
* **`per_page` 不存在**：带 `per_page=2` 仍回 25 条、`per_page` 回显 `25`——未声明参数被忽略（不是报错）。每条查询固定一页 25 条，只能靠 `page` 翻。
* 检索式写错或查不到：`unknown` 之类在 `page=2` → `200`，`result` 空、`total` `0`、`num_pages` `0`——查不到不是错误。
* 缺 `query` → **`400`**（规范写 `422`）；`sort` 传非法值 → `400`。错误体形状见[状态码与错误体](#状态码与错误体)。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    hits = client.search('language:english', sort='date', page=1)
    # 真实 URL：GET https://nhentai.net/api/v2/search?query=language%3Aenglish&sort=date&page=1
    # 实测：200，per_page 25、total 147497、num_pages 5900、result 25 条（计数会变）
    print(hits['per_page'], hits['total'], hits['num_pages'], len(hits['result']))
    for item in hits['result']:
        print(item['id'], item['media_id'], item['num_pages'], item['num_favorites'])

with Nhentai('nhentai') as client:
    empty = client.search('definitely-no-such-tag-or-word', page=2)
    # 实测：200，result 为空、total 0、num_pages 0——查不到是正常结果
    print(empty['result'], empty['total'], empty['num_pages'])
```

## 收藏与黑名单（5 个方法）

这一组全都要 Key（规范：`User Token or API Key`）：匿名一律 `401`（**实测**，错误体 `{"error": "Authentication required"}`）。`blacklist_update()` 是写操作，从未执行。

### favorite_list

给什么：`favorite_list(**params)`。路由 `GET /api/v2/favorites`。`operationId=get_favorites_api_v2_favorites_get`，JSON Pointer `#/paths/~1api~1v2~1favorites/get`。规范摘要：取已认证用户（Key 持有者）的收藏画廊。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `q` | 字符串或 `null` | 在收藏里再搜一次 | 不筛（规范允许 `null`） | `q='english'` |
| `page` | 整数，`minimum: 1`，默认 `1` | 页码 | 服务端用 `1` | `page=1` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 规范只有 `q` 与 `page`，**没有 `per_page`** |

返回 `PaginatedResponse_GalleryListItem_`，与 `gallery_list()` 同一套信封。状态码（**规范**）：`200`、`401`、`422`、`429`。限流：`15/1min per user` 与 `15/1min per API key owner`。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    favorites = client.favorite_list(page=1)
    # 真实 URL：GET https://nhentai.net/api/v2/favorites?page=1
    # 未实测：带 Key 的成功响应本轮没有样本（匿名请求实测为 401）
    print(favorites['total'], [item['id'] for item in favorites['result']])
```

### favorite_random

给什么：无参数。路由 `GET /api/v2/favorites/random`。`operationId=get_random_favorite_api_v2_favorites_random_get`，JSON Pointer `#/paths/~1api~1v2~1favorites~1random/get`。规范摘要：从已认证用户收藏里随机取一个画廊 id。

返回一个 JSON 对象，schema `{"type": "object", "additionalProperties": true}`——规范没列字段名。姊妹路由 `gallery_random()` 实测回 `{"id": …}`，这条本轮没拿到成功样本（匿名 `401`），键名**未实测**，别把 `gallery_random()` 结论直接搬过来。

状态码（**规范**）：`200`、`401`、`404`、`429`。限流：`15/1min per user` 与 `15/1min per API key owner`。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    pick = client.favorite_random()
    # 真实 URL：GET https://nhentai.net/api/v2/favorites/random
    # 未实测：键名规范没写（匿名请求实测为 401）
    print(pick)
```

### blacklist_list

给什么：无参数。路由 `GET /api/v2/blacklist`。`operationId=get_blacklist_api_v2_blacklist_get`，JSON Pointer `#/paths/~1api~1v2~1blacklist/get`。规范摘要：取已认证用户的黑名单标签。

返回 `BlacklistListResponse`（**规范**：`#/components/schemas/BlacklistListResponse`）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `tags` | `BlacklistedTagResponse[]` | 是 | 黑名单标签，每个 `id` / `type` / `name` / `slug` / `count`（字段全必在） |
| `count` | integer | 是 | 黑名单条数（与 `len(tags)` 一致可能性很大，但规范没写明关系） |

状态码（**规范**）：`200`、`401`、`429`（没有 `422`——无参数）。限流：`15/1min per user` 与 `15/1min per API key owner`。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    blacklist = client.blacklist_list()
    # 真实 URL：GET https://nhentai.net/api/v2/blacklist
    # 未实测：匿名请求实测为 401
    print(blacklist['count'])
    for tag in blacklist['tags']:
        print(tag['id'], tag['type'], tag['name'], tag['slug'])
```

### blacklist_update

> **写操作：会改账号数据，本项目从未执行过。**

给什么：`blacklist_update(**attributes)`。路由 `POST /api/v2/blacklist`。`operationId=update_blacklist_api_v2_blacklist_post`，JSON Pointer `#/paths/~1api~1v2~1blacklist/post`。规范摘要：往黑名单加标签或去掉标签。正文 schema `BlacklistUpdateRequest`（**规范**：`#/components/schemas/BlacklistUpdateRequest`）：

| 正文键 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `added` | 整数数组，默认 `[]` | 要加进黑名单的**标签 id** 数组（不是名字） | 服务端按空数组处理（schema 默认 `[]`） | `added=[12227]`——**不要执行** |
| `removed` | 整数数组，默认 `[]` | 要从黑名单移除的标签 id 数组 | 服务端按空数组处理 | `removed=[6346]`——**不要执行** |
| `**attributes` | 其它键原样进 JSON 正文（**客户端**） | — | — | 命令性调用 `client.blacklist_update(added=[12227], removed=[6346])` |

正文给标签 id（数字），不是名字；id 从 [`tag_show()`](#tag_show) / [`tag_ids()`](#tag_ids) 拿。两个数组都可给空数组，库不会删掉或替成 `null`（**客户端**）。

返回 `BlacklistResponse`（**规范**：`#/components/schemas/BlacklistResponse`）：`success`（boolean，必在）、`count`（integer，必在，操作后黑名单条数）。

状态码（**规范**）：`200`、`400`、`401`、`422`、`429`。限流：`20/15min per user` 与 `20/15min per API key owner`——每 15 分钟 20 次，比别的紧得多。

**未执行**：只写调用形态；正文与响应都无实测。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    # POST https://nhentai.net/api/v2/blacklist
    # JSON 正文：{"added": [12227], "removed": [6346]}
    # 未执行：写操作，本项目不发写请求。
    # 规范返回：{"success": <bool>, "count": <int>}
    result = client.blacklist_update(added=[12227], removed=[6346])
    print(result['success'], result['count'])
```

### blacklist_ids

给什么：无参数。路由 `GET /api/v2/blacklist/ids`。`operationId=get_blacklist_ids_api_v2_blacklist_ids_get`，JSON Pointer `#/paths/~1api~1v2~1blacklist~1ids/get`。规范摘要：只要黑名单的标签 id。

返回**顶层整数数组**（**规范**：`#/paths/~1api~1v2~1blacklist~1ids/get/responses/200/content/application~1json/schema` 是 `type: array` + `items: {type: integer}`）——没有 `tags`、没有 `count`。

状态码（**规范**）：`200`、`401`、`429`。限流：`45/1min per user`（规范只写一档，没有「per API key owner」）。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    ids = client.blacklist_ids()
    # 真实 URL：GET https://nhentai.net/api/v2/blacklist/ids
    # 未实测：匿名请求实测为 401；规范返回是整数数组，不是 {"tags": …}
    print(ids)
```

## 用户（2 个方法）

规范把 `user` 分组标成 **First-party and internal only**，但明确挖了一个例外：`GET /api/v2/user`（原话：`First-party and internal only, bar GET /api/v2/user`）。本包收录 `user_me()`，其余 `user/*`（改资料、删账号、换头像、API Key 管理）与全部 `auth/*` 都不封装。`user_show()` 属于公开 `users`（复数）分组，与内部 `user` 分组不是一回事。

### user_show

给什么：`user_show(user_id, slug)`。路由 `GET /api/v2/users/{user_id}/{slug}`。`operationId=get_user_profile_api_v2_users__user_id___slug__get`，JSON Pointer `#/paths/~1api~1v2~1users~1{user_id}~1{slug}/get`。规范摘要：取某个用户公开资料，必须同时给对用户 id 与用户名 slug。

| 参数 | 类型与取值（**规范**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 整数，路径段，必填 | 用户数字 id | 必填 | `user_show(981330, 'jegutimantion')` |
| `slug` | 字符串，路径段，必填 | 用户名 slug（小写/连字符形式） | 必填 | 同上 |

两段必须配套：id 对而 slug 错，按规范是 `404`（规范摘要强调「correct username slug」）。`slug` 来源：`TaxonomyCommentAuthor.slug`、`SuggestionProposer.slug`、`CommentResponse.poster.slug`。

返回 `UserProfileResponse`（**规范**：`#/components/schemas/UserProfileResponse`），字段见 [`UserProfileResponse`](#userprofileresponse)。要点：`recent_favorites` 与 `recent_comments` 是两个数组字段（不是分页信封），元素分别是 [`RecentFavorite`](#recentfavorite) 与 [`RecentComment`](#recentcomment)；`date_joined` 是整数 unix 时间戳；`about` 与 `favorite_tags` 是字符串（规范默认空串），不是数组——别按数组遍历（用户自己写的文本，展示前自行处理）。

状态码（**规范**）：`200`、`404`、`422`、`429`。限流：匿名 `5/1min per IP`，带 User Token 或 Key `10/1min per IP`——全站最紧，一分钟只能匿名查 5 次，批量拉资料前想清楚。

**实测**：`GET https://nhentai.net/api/v2/users/981330/jegutimantion` → `200 application/json`，正文键与 `UserProfileResponse` 完全一致：`id`、`username`、`slug`、`avatar_url`、`is_superuser`、`is_staff`、`date_joined`、`about`、`favorite_tags`、`recent_favorites`、`recent_comments`——包括两个「规范默认空串」字段也在。当次两个数组内容没记录，本页不写。

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    profile = client.user_show(981330, 'jegutimantion')
    # 真实 URL：GET https://nhentai.net/api/v2/users/981330/jegutimantion
    # 实测：200，键与 UserProfileResponse 一致（上面列出的 11 个）
    print(profile['id'], profile['username'], profile['slug'], profile['date_joined'])
    print(len(profile['recent_favorites']), len(profile['recent_comments']), profile['is_staff'])
```

### user_me

给什么：无参数。路由 `GET /api/v2/user`。`operationId=get_me_api_v2_user_get`，JSON Pointer `#/paths/~1api~1v2~1user/get`。规范摘要：取自己资料；用 API Key 认证时 `email` 会被隐藏。

这个方法是规范里「First-party 分组唯一对第三方开放的例外」，本包收它。

返回 `UserMeResponse`（**规范**：`#/components/schemas/UserMeResponse`）：

| 字段 | 类型 | 必在 | 含义 |
| :--- | :--- | :--- | :--- |
| `id` / `username` / `slug` / `avatar_url` | 依次 integer / string / string / string | 是 | 账号身份与头像地址 |
| `theme` | string，默认 `"black"` | 否 | 站点主题设置 |
| `is_staff` / `is_superuser` | boolean，默认 `false` | 否 | 权限位 |
| `about` / `favorite_tags` | string，默认 `""` | 否 | 自我介绍与收藏标签文本（都是字符串） |
| `email` | string 或 `null` | 否 | 邮箱；用 API Key 认证时按规范隐藏（实测只看到 `401`，带 Key 时是 `null` 还是缺键**未实测**） |

状态码（**规范**）：`200`、`401`、`429`。限流：`45/1min per user` 与 `45/1min per API key owner`。

**实测**：匿名 `GET https://nhentai.net/api/v2/user` → **`401 application/json`**，正文 `{"error": "Authentication required"}`——没凭据拿不到，与规范一致。

```python
from anybooru import Nhentai

with Nhentai('nhentai', api_key='<你的 API Key>') as client:
    me = client.user_me()
    # 真实 URL：GET https://nhentai.net/api/v2/user
    # 未实测：带 Key 的成功响应（匿名请求实测为 401）
    print(me['id'], me['username'], me['slug'])
    print(me.get('email'), me.get('theme'), me.get('is_staff'))
```

## 状态码与错误体

规范给每条路由列状态码清单，实测只拿到一部分。不一致按实测写：

| 状态 | 什么时候出现 | 正文形状 | 本轮样本 |
| :--- | :--- | :--- | :--- |
| `200` | 正常（含查不到、没有评论、空数组等正常空结果） | 三种：分页信封（`result` + 计数）、裸数组（`gallery_popular()` / `tag_ids()` / `tag_search()` / `blacklist_ids()`）、裸整数（`gallery_comment_count()`） | 25 个成功样本 |
| `400` | 参数校验失败 | `{"error": "Validation error", "details": ["query -> page: Input should be greater than or equal to 1"]}`——带 `details` 字符串数组 | **实测**：`page=0`、`per_page=101`、缺 `query`、非法 `sort`、非法 `tag_type` |
| `401` | 缺凭据或凭据无效 | `{"error": "Authentication required"}` | **实测**：`gallery_favorite()`、`favorite_list()`、`favorite_random()`、`blacklist_list()`、`blacklist_ids()`、`user_me()` 六个方法匿名调用 |
| `404` | 编号不存在 | `{"error": "Gallery not found"}`（画廊）；其它资源文案可能不同 | **实测**：`galleries/999999999`、`galleries/tagged?tag_id=999999999` |
| `422` | 规范把「参数校验失败」写成这个码 + `HTTPValidationError`（`{"detail": [{"loc": …, "msg": …, "type": …, "input": …, "ctx": …}]}`） | 规范如此 | **本轮 0 个样本**：实测校验失败全是 `400` |
| `429` | 触发限流 | 规范写 `ErrorResponse`（`{"error": …}`） | **本轮 0 个样本**：60 多次请求没触发限流，限流数字只是规范声明，没有实测验证；头里有没有 `Retry-After` 也没记录 |
| `503` | 站点侧功能开关关着（GTS / taxonomy / favorites / downloads） | `ErrorResponse` | **本轮 0 个样本**：相关 `GET` 都回 `200` |

三条要记住：

1. **别按规范写 `422` 分支**：至少对查询参数校验，站点实际给 `400`，错误体 `{"error": "Validation error", "details": […]}`——`details` 里英文原文（形如 `query -> page: Input should be greater than or equal to 1`）由站点生成，本库原样抛出、不改写。
2. **本库不归一化状态码**：非 2xx 一律抛 `AnybooruHTTPError`（`http_code` / `url` / `body` / `data`），按 `error.http_code` 分支，别指望库把 `400` 变 `422`。
3. **空结果不是错误**：`result: []`（`total` 0 或 `num_pages` 0）在评论、建议、编辑历史、搜索无命中上都实测过。

```python
from anybooru import AnybooruHTTPError, Nhentai

with Nhentai('nhentai') as client:
    try:
        client.gallery_list(page=0, per_page=2)
    except AnybooruHTTPError as error:
        # 实测：400 {"error": "Validation error", "details": ["query -> page: Input should be greater than or equal to 1"]}
        print(error.http_code, error.data['error'], error.data['details'])
```

## 服务端限流一览（**规范**）

数字抄自规范各路由 `description` 的 `**Rate limits:**` 段。本轮没触发任何限流，这些数字是站点声明、不是实测；本库不做节流、退避、重试——打满限额会拿到 `429` 的 `AnybooruHTTPError`，自己减速。

| 方法 | 服务端限额（规范原文口径） |
| :--- | :--- |
| `gallery_list()` | 匿名 `15/1min per IP`；带 User Token 或 Key `30/1min per IP` |
| `gallery_tagged()` | 同上 |
| `gallery_popular()` | `8/1min per IP`（不分匿名/凭据） |
| `gallery_random()` | 匿名 `20/1min per IP`；带凭据 `30/1min per IP` |
| `gallery_show()` | 匿名 `20/1min per IP`；带凭据 `45/1min per IP` |
| `gallery_related()` | 匿名 `12/1min per IP`；带凭据 `30/1min per IP` |
| `gallery_favorite()` | `15/1min per user`；`15/1min per API key owner` |
| `favorite_add()` / `favorite_remove()` | `15/1min` × 四档：per user、per API key owner、per IP + user、per IP + API key owner |
| `gallery_suggestions()` | `60/1min per IP` |
| `gts_backlog()` | `60/1min per IP` |
| `gts_new_tags()` | `60/1min per IP` |
| `gallery_download()` | `format=torrent`：`5/1min per IP`、`10/5min per user`、`5/1min per API key owner`；`format=zip\|cbz`：`10/5min per IP`、`7/5min per user`、`10/5min per API key owner` |
| `tag_ids()` | `15/1min per IP` |
| `tag_search()` | `30/1min per IP` |
| `tag_list()` | 匿名 `15/1min per IP`；带凭据 `30/1min per IP` |
| `tag_show()` | 匿名 `15/1min per IP`；带凭据 `30/1min per IP` |
| `taxonomy_list()` | `120/1min per IP` |
| `taxonomy_stats()` | `30/1min per IP` |
| `taxonomy_resolved()` | `90/1min per IP` |
| `taxonomy_show()` / `taxonomy_comments()` / `taxonomy_edits()` | 各 `120/1min per IP` |
| `gallery_comments()` | 匿名 `30/1min per IP`；带凭据 `60/1min per IP` |
| `gallery_comment_count()` | 匿名 `12/1min per IP`；带凭据 `20/1min per IP` |
| `search()` | 匿名 `10/1min per IP`；带凭据 `20/1min per IP` |
| `favorite_list()` / `favorite_random()` / `blacklist_list()` | `15/1min per user`；`15/1min per API key owner` |
| `blacklist_update()` | `20/15min per user`；`20/15min per API key owner`（15 分钟 20 次） |
| `blacklist_ids()` | `45/1min per user` |
| `user_show()` | 匿名 `5/1min per IP`；带凭据 `10/1min per IP`（全站最紧） |
| `user_me()` | `45/1min per user`；`45/1min per API key owner` |
| `service_info()` / `cdn_config()` / `site_config()` | 规范没有写限流段 |

最需要小心：`user_show()`（匿名 5 次/分钟）、`search()`（匿名 10 次/分钟）、`gallery_popular()`（8 次/分钟）、`blacklist_update()`（15 分钟 20 次）。

## 响应对象

按规范和组件里的对象逐个列字段。**「必在」以规范 `required` 为准**：带 `*` 规范声明一定有，其余可能出现——实测已抓到多处「同一 schema 不同路由填充不同」（标签列表 vs 详情、taxonomy 列表 vs 详情），读可选字段一律 `.get(...)`。类型后标 `| null` 表示可空。

### GalleryListItem

规范：`#/components/schemas/GalleryListItem`（列表轻量对象，出现在搜索结果、标签列表、首页）。`gallery_list()` / `gallery_tagged()` / `gallery_related()` / `search()` / `favorite_list()` 的 `result[]` 都是它；`gallery_popular()` 直接是它的数组。

| 字段 | 类型（`*` = 规范必在） | 说明 |
| :--- | :--- | :--- |
| `id` | integer* | 画廊编号，`gallery_show()` 要的 id |
| `media_id` | string* | 媒体编号，**字符串**（实测形如 `"4006343"`），不是数字 |
| `english_title` | string* | 英文标题（扁平字符串；详情是 `title` 对象） |
| `japanese_title` | string \| null | 日文标题，可为 `null` |
| `thumbnail` | string* | 缩略图相对路径（配 `cdn_config()` 服务器前缀） |
| `thumbnail_width` / `thumbnail_height` | integer* | 缩略图宽高 |
| `num_pages` | integer（默认 `0`） | 页数 |
| `num_favorites` | integer（默认 `0`） | 收藏数 |
| `tag_ids` | integer[]（默认 `[]`） | 标签 id 数组——拿名字另调 `tag_ids()` |
| `blacklisted` | boolean（默认 `false`） | 是否命中你自己的黑名单；匿名单次请求没意义 |

按规范字段拼的形状（不是响应样本，取值占位）：

```json
{
  "id": 658856,
  "media_id": "4006343",
  "english_title": "<string>",
  "japanese_title": "<string|null>",
  "thumbnail": "<相对路径>",
  "thumbnail_width": 250,
  "thumbnail_height": 350,
  "num_pages": 18,
  "num_favorites": 0,
  "tag_ids": [12227, 6346],
  "blacklisted": false
}
```

### GalleryDetailResponse

规范：`#/components/schemas/GalleryDetailResponse`（详情，必要时带 `comments` / `related` / `favorite` / `suggestions`）。`gallery_show()` 返回它。

| 字段 | 类型（`*` = 必在） | 说明 |
| :--- | :--- | :--- |
| `id` | integer* | 画廊编号 |
| `media_id` | string* | 媒体编号 |
| `title` | [`GalleryTitle`](#gallerytitle)`*` | 对象：`english` / `japanese` / `pretty` |
| `cover` | [`CoverInfo`](#coverinfo)`*` | 封面：`path` + `width` + `height` |
| `thumbnail` | [`CoverInfo`](#coverinfo)`*` | 缩略图：`path` + 宽高 |
| `scanlator` | string（默认 `""`） | 汉化组；「没有」就是空串 |
| `upload_date` | integer* | 上传时刻 unix 时间戳 |
| `tags` | [`TagResponse`](#tagresponse)`[]*` | 全部标签（分类在每项 `type`） |
| `num_pages` | integer* | 页数 |
| `num_favorites` | integer* | 收藏数 |
| `pages` | [`PageInfo`](#pageinfo)`[]` | 每页图片路径与尺寸；实测当次 `len(pages)` 等于 `num_pages` |
| `comments` | [`CommentResponse`](#commentresponse)`[]` 或 `null` | 带 `include=comments` 时出现 |
| `comment_count` | integer 或 `null` | 实测跟随 `include=comments` 出现 |
| `related` | [`GalleryListItem`](#gallerylistitem)`[]` 或 `null` | 带 `include=related` 时出现 |
| `is_favorited` | boolean 或 `null` | 对应 `include=favorite`；**匿名实测没出现**，判断收藏状态用 `gallery_favorite()` |
| `suggestions` | [`GallerySuggestionsBundle`](#gallerysuggestionsbundle) 或 `null` | 带 `include=suggestions` 时出现 |

```json
{
  "id": 658856,
  "media_id": "4006343",
  "title": {"english": "<string>", "japanese": "<string|null>", "pretty": "<string>"},
  "cover": {"path": "<相对路径>", "width": 350, "height": 500},
  "thumbnail": {"path": "<相对路径>", "width": 250, "height": 350},
  "scanlator": "",
  "upload_date": 1700000000,
  "tags": [{"id": 12227, "type": "language", "name": "<string>", "slug": "english",
            "url": "/tag/english", "count": 0, "description": null,
            "is_community": false, "pending_describe_id": null}],
  "num_pages": 18,
  "num_favorites": 0,
  "pages": [{"number": 1, "path": "<相对路径>", "width": 1280, "height": 1810,
             "thumbnail": "<相对路径>", "thumbnail_width": 250, "thumbnail_height": 350}]
}
```

### GalleryTitle

规范：`#/components/schemas/GalleryTitle`。

| 字段 | 类型（`*` = 必在） | 说明 |
| :--- | :--- | :--- |
| `english` | string* | 英文标题 |
| `japanese` | string \| null | 日文标题 |
| `pretty` | string* | 站点排版用美化标题（可能含样式字符，原样返回） |

### CoverInfo

规范：`#/components/schemas/CoverInfo`：`path`（string*）、`width`（integer*）、`height`（integer*）。`path` 是相对路径，配 `cdn_config()` 前缀。

### PageInfo

规范：`#/components/schemas/PageInfo`：`number`（integer*，第几页）、`path`（string*，相对路径）、`width`（integer*）、`height`（integer*）、`thumbnail`（string*）、`thumbnail_width`（integer*）、`thumbnail_height`（integer*）。全部必在。**本库不下载这些路径指向的字节**，只给路径。

### TagResponse

规范：`#/components/schemas/TagResponse`（注释：匹配 Django 格式）。`tag_show()` 返回单个，`tag_ids()` / `tag_search()` 返回数组，`tag_list()` 的 `result[]`、画廊详情 `tags[]`、GTS/backlog 行里的 `tag` 也是它——但填充不同。

| 字段 | 类型（`*` = 必在） | 说明 |
| :--- | :--- | :--- |
| `id` | integer* | 标签 id：`gallery_tagged(12227)`、`gts_backlog(tag_id=…)`、`blacklist_update(added=[…])` 要的 |
| `type` | string* | 分类（`language`、`tag` 等；规范没列允许值） |
| `name` | string* | 展示名（可含空格、非 ASCII） |
| `slug` | string* | URL slug，`tag_show(type, slug)` 第二段 |
| `url` | string* | 标签页面路径（规范只写 string，实测形如 `/tag/english`） |
| `count` | integer* | 该标签下画廊数（快照） |
| `description` | string \| null | 标签说明；本页不转载文本 |
| `is_community` | boolean \| null | **实测只在 `tag_show()` 出现**，`tag_list()` 列表项没这个键 |
| `pending_describe_id` | string \| null | 同上：只在详情出现 |

### 分页信封（PaginatedResponse_*）

规范里三个同构分页信封，字段名一样、`per_page` schema 默认值不同：

| schema | 谁在用 | `result` 元素 | 额外字段 |
| :--- | :--- | :--- | :--- |
| `#/components/schemas/PaginatedResponse_GalleryListItem_` | `gallery_list()`、`gallery_tagged()`、`search()`、`favorite_list()` | [`GalleryListItem`](#gallerylistitem) | `num_pages`（integer*）、`per_page`（integer，schema 默认 `25`）、`total`（integer\|null） |
| `#/components/schemas/PaginatedResponse_CommentResponse_` | `gallery_comments()` | [`CommentResponse`](#commentresponse) | 同上，`per_page` schema 默认也是 `25`（端点默认 `50`，以回显为准） |
| `#/components/schemas/TagPaginatedResponse` | `tag_list()` | [`TagResponse`](#tagresponse) | `num_pages`*、`per_page`（schema 默认 `120`）、`total`（integer\|null）、`alphabet`（object\|null） |

`result` 与 `num_pages` 必在；`per_page` 与 `total` 可选。表格型几个（`SuggestionListResponse` / `TaxonomySuggestionListResponse` / `TaxonomyCommentListResponse` / `BacklogListResponse`）不用 `num_pages*` 而用 `has_more`（boolean\|null），字段见各自小节。

### UserPublic

规范：`#/components/schemas/UserPublic`：`id`（integer*）、`username`（string*）、`slug`（string*）、`avatar_url`（string*）、`is_superuser`（boolean，默认 `false`）、`is_staff`（boolean，默认 `false`）。

### UserMeResponse

规范：`#/components/schemas/UserMeResponse`（完整资料，API Key 认证时邮箱隐藏）。`user_me()` 返回它：`id`*、`username`*、`slug`*、`avatar_url`*（以上必在）、`theme`（string，默认 `"black"`）、`is_staff`（bool，默认 `false`）、`is_superuser`（bool，默认 `false`）、`about`（string，默认 `""`）、`favorite_tags`（string，默认 `""`）、`email`（string\|null，API Key 认证时隐藏）。

### UserProfileResponse

规范：`#/components/schemas/UserProfileResponse`（公开资料）。`user_show()` 返回它：`id`*、`username`*、`slug`*、`avatar_url`*、`is_superuser`（默认 `false`）、`is_staff`（默认 `false`）、`date_joined`（integer*，unix 时间戳）、`about`（string，默认 `""`）、`favorite_tags`（string，默认 `""`）、`recent_favorites`（[`RecentFavorite`](#recentfavorite)`[]*`）、`recent_comments`（[`RecentComment`](#recentcomment)`[]*`）。**实测**：这些键在一次匿名请求里全部出现。两个 `recent_*` 是数组、不是分页信封，条数规范没写；`about` 与 `favorite_tags` 是用户写的文本字符串（不是标签数组）。

### RecentFavorite

规范：`#/components/schemas/RecentFavorite`：`id`*、`media_id`*、`thumbnail`*、`thumbnail_width`*、`thumbnail_height`*、`english_title`*、`japanese_title`（string\|null）、`num_pages`（integer，默认 `0`）、`tag_ids`（integer[]，默认 `[]`）。比 [`GalleryListItem`](#gallerylistitem) 少 `num_favorites` 与 `blacklisted`。

### RecentComment

规范：`#/components/schemas/RecentComment`：`id`*、`gallery_id`*、`body`*（评论正文，本页不转载）、`post_date`*（integer，unix 时间戳）、`gallery_title`*（string）。

### CommentResponse

规范：`#/components/schemas/CommentResponse`（注释：匹配 Django 格式）：`id`*、`gallery_id`*、`poster`*（[`UserPublic`](#userpublic)）、`post_date`*（integer，unix 时间戳）、`body`*（评论正文）。**实测只拿到空数组**（画廊 658856 当次没有评论），真实取值无样本。

### SuggestionResponse

规范：`#/components/schemas/SuggestionResponse`——GTS 提议（`gallery_suggestions()`、`gts_backlog().result[].suggestion`、`GallerySuggestionsBundle` 元素）。

| 字段 | 类型（`*` = 必在） | 说明 |
| :--- | :--- | :--- |
| `id` | string（uuid）* | 提议编号 |
| `gallery_id` | integer* | 针对哪张画廊 |
| `tag` | [`SuggestionTag`](#suggestiontag)`*` | 要加/去的标签 |
| `action` | string*，枚举 `add` / `remove` | 加还是去 |
| `status` | string*，枚举 `pending` / `accepted` / `rejected` / `superseded` | 状态（有 `superseded`，被后来的提议顶掉） |
| `score` | integer \| null | 得分（规范没写算法） |
| `voter_count` | integer* | 投票人数 |
| `proposer` | [`SuggestionProposer`](#suggestionproposer)`*` | 谁提的 |
| `created_at` / `resolved_at` / `reverted_at` | string（date-time）* / \| null / \| null | 创建、处理、被回退时间 |
| `resolver` / `reverter` | [`SuggestionProposer`](#suggestionproposer) \| null | 处理人 / 回退人 |
| `resolution_note` | string \| null | 处理结论 |
| `my_vote` | integer \| null | 你自己投的票；匿名没意义 |
| `tier` | string \| null，枚举 `trending` / `active` / `declined` / `hidden` | 分类（实测列表里带，`taxonomy_show()` 详情里没有类似 `tier`） |

### SuggestionTag

规范：`#/components/schemas/SuggestionTag`：`id`*、`type`*、`name`*、`slug`*、`url`*、`description`（string\|null）。与 [`TagResponse`](#tagresponse) 区别是**没有 `count`**。

### SuggestionProposer

规范：`#/components/schemas/SuggestionProposer`：`id`*、`username`*、`slug`（string\|null）、`avatar_url`（string\|null）。

### GallerySuggestionsBundle

规范：`#/components/schemas/GallerySuggestionsBundle`（`gallery_show(..., include='suggestions')` 载荷）：`trending`（[`SuggestionResponse`](#suggestionresponse)`[]*`）、`active`（同类型，*）、`mine`（同类型，默认 `[]`——已认证者自己在这张画廊上的待处理提议，匿名时空数组）、`counts`（[`SuggestionTierCounts`](#suggestiontiercounts)`*`）。

### SuggestionTierCounts

规范：`#/components/schemas/SuggestionTierCounts`：`trending` / `active` / `declined` / `hidden`，四个 integer、默认 `0`。

### BacklogRow 与 BacklogGallery

`gts_backlog()` 的 `result[]` 是 `BacklogRow`（规范：`#/components/schemas/BacklogRow`，一条待处理标签变更提议 + 针对画廊）：`suggestion`（[`SuggestionResponse`](#suggestionresponse)`*`）、`gallery`（`BacklogGallery`*）。**实测**这两个键都在。

`BacklogGallery`（规范：`#/components/schemas/BacklogGallery`）：`id`*、`media_id`*、`thumbnail`*、`thumbnail_width`*、`thumbnail_height`*、`english_title`*、`japanese_title`（string\|null）、`num_pages`*、`num_favorites`*、`upload_date`*（integer，unix 时间戳）、`age_days`*（integer，`upload_date` 距今天数）、`tags`（[`TagResponse`](#tagresponse)`[]`，默认 `[]`）。

### NewTagIndexEntry

规范：`#/components/schemas/NewTagIndexEntry`（最近新铸标签 + 提到它的待处理提议数）：`tag`（[`TagResponse`](#tagresponse)`*`）、`created_at`（integer*，unix 时间戳）、`pending_gts_count`（integer*）。**实测**这三个键都在；外层 `{"result": [...]}`。

### TaxonomySuggestionResponse

规范：`#/components/schemas/TaxonomySuggestionResponse`——taxonomy 提议（列表与详情都用）。字段多，按用途分三组：

| 字段 | 类型（`*` = 必在） | 说明 |
| :--- | :--- | :--- |
| `id` | string（uuid）* | 提议编号，`taxonomy_show()` 等要的路径段 |
| `action` | string*，枚举 `create` / `rename` / `merge` / `describe` | 提议类型 |
| `status` | string*，枚举 `pending` / `accepted` / `rejected` / `withdrawn` | 状态（**没有** GTS 的 `superseded`，多了 `withdrawn`） |
| `score` / `voter_count` | integer* / integer* | 得分与投票人数 |
| `proposer` | [`TaxonomySuggestionProposer`](#taxonomysuggestionproposer)`*` | 提议人 |
| `proposer_note` | string \| null | 提议人附言 |
| `created_at` / `edited_at` / `resolved_at` | string（date-time）* / \| null / \| null | 创建、最后编辑、处理时间 |
| `resolution_note` / `resolver` | string \| null / [`TaxonomySuggestionResolver`](#taxonomysuggestionresolver) \| null | 处理结论与处理人 |
| `target_tag` / `merge_into_tag` | [`TaxonomySuggestionTag`](#taxonomysuggestiontag) \| null | 被改的标签 / 合并目标 |
| `new_name` / `new_type` / `new_description` | string \| null | `create` / `rename` / `describe` 想改成什么 |
| `accepted_type` / `accepted_name` / `accepted_description` | string \| null | 被接受后最终取名 |
| `resolved_tag` | [`TaxonomySuggestionTag`](#taxonomysuggestiontag) \| null | 处理完落到哪个标签 |
| `my_vote` | integer \| null | 你自己的票（匿名无意义） |
| `tier` | string \| null，枚举 `trending` / `active` / `declined` / `hidden` / `mine` | 分类；**实测列表元素带它、`taxonomy_show()` 详情里没这个键** |
| `tier_page` | integer \| null | 该提议在分类里的页码；同样只在列表实测到 |
| `comment_count` | integer（默认 `0`） | 评论数 |
| `recent_comments` | [`TaxonomyCommentResponse`](#taxonomycommentresponse)`[]*` | 最近评论预览 |

哪个 `action` 填哪几个字段，规范没逐条写清（`create` 用 `new_*`、`rename`/`merge` 用 `target_tag`/`merge_into_tag`、`describe` 用 `new_description`，被接受后看 `accepted_*`/`resolved_tag` 是合理读法，但本轮没分动作取样）。

### TaxonomySuggestionTag

规范：`#/components/schemas/TaxonomySuggestionTag`：`id`（integer\|null）、`type`*、`name`*、`slug`*、`url`（string\|null）、`count`（integer\|null）、`description`（string\|null）。比 [`TagResponse`](#tagresponse) 松：`id`、`url`、`count` 可空——提议可能在标签不存在时就建了。

### TaxonomySuggestionProposer

规范：`#/components/schemas/TaxonomySuggestionProposer`：`id`*、`username`*、`slug`（string\|null）、`avatar_url`（string\|null）。

### TaxonomySuggestionResolver

规范：`#/components/schemas/TaxonomySuggestionResolver`（处理提议的 staff，只出现在已处理条目）：`id`*、`username`*、`slug`（string\|null）、`avatar_url`（string\|null）。字段与 proposer 一样。

### TaxonomyCommentResponse

规范：`#/components/schemas/TaxonomyCommentResponse`：`id`*（string uuid）、`body`*（正文，本页不转载）、`author`*（[`TaxonomyCommentAuthor`](#taxonomycommentauthor)）、`created_at`*（string date-time）、`can_delete`（boolean，默认 `false`——已认证者能不能删这条）、`link_previews`（数组，默认 `[]`）。**实测**这些键都在。

`link_previews[]` 多态（**规范**：`#/components/schemas/TaxonomyCommentResponse/properties/link_previews/items` 用 `oneOf` + `discriminator.propertyName = "kind"`）：

| `kind` | 对应 schema | 字段 |
| :--- | :--- | :--- |
| `"taxonomy"`（默认） | `TaxonomyLinkPreview` | `start`*、`end`*（正文字符区间）、`matched`*（命中文本）、`kind`、`suggestion`*（[`TaxonomySuggestionResponse`](#taxonomysuggestionresponse)） |
| `"gallery"` | `GalleryLinkPreview` | `start`*、`end`*、`matched`*、`kind`、`gallery`*（[`GalleryListItem`](#gallerylistitem)） |

按 `kind` 分支取 `suggestion` 或 `gallery`。

### TaxonomyCommentAuthor

规范：`#/components/schemas/TaxonomyCommentAuthor`：`id`*、`username`*、`slug`*、`avatar_url`（string\|null）、`is_staff`（boolean，默认 `false`）、`is_superuser`（boolean，默认 `false`）。比 [`UserPublic`](#userpublic) 多两个权限位、且 `slug` 必在。

### TaxonomySuggestionEditEntry

规范：`#/components/schemas/TaxonomySuggestionEditEntry`（一次编辑事件 = 一次 `PATCH` 改了什么 + 谁何时改的 + 可选说明）：`id`*（string uuid）、`created_at`*（string date-time）、`summary`（string\|null，改动说明）、`changes`*（数组，*）、`editor`（[`TaxonomySuggestionProposer`](#taxonomysuggestionproposer) \| null）。

`changes[]` 是 `TaxonomySuggestionEditChange`（规范：`#/components/schemas/TaxonomySuggestionEditChange`）：`field`*（字段名）、`old_value`（string\|null）、`new_value`（string\|null）。规范注释：标签类字段（`target_tag`、`merge_into_tag`）存 `type:name` 人类可读快照而不是 id，标签被删历史仍读得懂——别拿 `old_value`/`new_value` 当 id 用。

### TaxonomySuggestionStats

规范：`#/components/schemas/TaxonomySuggestionStats`。**实测**返回 13 个键，与下表一致：

| 字段 | 类型（`*` = 必在） | 说明 |
| :--- | :--- | :--- |
| `pending` | integer* | 待处理提议数 |
| `accepted_total` / `rejected_total` | integer* | 累计接受 / 拒绝数 |
| `accepted_30d` / `accepted_7d` | integer* | 近 30 天 / 近 7 天接受数 |
| `created_30d` | integer* | 近 30 天新建数 |
| `renamed_30d` / `merged_30d` / `described_30d` | integer* | 近 30 天改名 / 合并 / 补描述数 |
| `trending_count` / `active_count` / `declined_count` | integer（默认 `0`） | 各分类当前条数 |
| `recent_accepted` | [`TaxonomySuggestionResponse`](#taxonomysuggestionresponse)`[]*` | 最近被接受的提议 |

`*_30d` 口径（滚动 30 天还是自然月）规范没写，本页不替它解释。

### 其余小对象

| schema | 字段 | 谁在用 |
| :--- | :--- | :--- |
| `#/components/schemas/ApiRootResponse` | `version`*、`message`*（都是 string） | `service_info()` |
| `#/components/schemas/CdnConfigResponse` | `image_servers`*（string[]）、`thumb_servers`*（string[]） | `cdn_config()` |
| `#/components/schemas/ConfigResponse` | `image_servers`*、`thumb_servers`*、`announcement`（`Announcement` \| null） | `site_config()` |
| `#/components/schemas/Announcement` | `message`*（string）、`links`（数组，默认 `[]`，元素 `AnnouncementLink`） | `site_config().announcement` |
| `#/components/schemas/AnnouncementLink` | `text`*、`url`*（都是 string） | 同上 |
| `#/components/schemas/FavoriteResponse` | `favorited`*（boolean）、`num_favorites`（integer\|null） | `gallery_favorite()`、`favorite_add()`、`favorite_remove()` |
| `#/components/schemas/DownloadResponse` | `url`*（string）、`expires_at`*（integer，unix 时间戳） | `gallery_download()` |
| `#/components/schemas/RelatedGalleriesResponse` | `result`*（[`GalleryListItem`](#gallerylistitem)`[]`） | `gallery_related()` |
| `#/components/schemas/NewTagIndexResponse` | `result`*（[`NewTagIndexEntry`](#newtagindexentry)`[]`） | `gts_new_tags()` |
| `#/components/schemas/BlacklistListResponse` | `tags`*（数组，元素 `BlacklistedTagResponse`）、`count`*（integer） | `blacklist_list()` |
| `#/components/schemas/BlacklistedTagResponse` | `id`*、`type`*、`name`*、`slug`*、`count`*（前四者如上文 `TagResponse`） | `blacklist_list().tags[]` |
| `#/components/schemas/BlacklistUpdateRequest` | `added`（integer[]，默认 `[]`）、`removed`（integer[]，默认 `[]`） | `blacklist_update()` 正文 |
| `#/components/schemas/BlacklistResponse` | `success`*（boolean）、`count`*（integer） | `blacklist_update()` |
| `#/components/schemas/ErrorResponse` | `error`*（string） | 401 / 404 / 429 / 503 等错误体 |
| `#/components/schemas/HTTPValidationError` | `detail`（数组，元素 `ValidationError`：`loc`*、`msg`*、`type`*、`input`、`ctx`） | 规范给 `422` 用；**本轮没实测到** |
| `#/components/schemas/SuggestionListResponse` | `result`*（[`SuggestionResponse`](#suggestionresponse)`[]`）、`has_more`（bool\|null）、`num_pages`（int\|null）、`total`（int\|null） | `gallery_suggestions()` |
| `#/components/schemas/BacklogListResponse` | `result`*（[`BacklogRow`](#backlogrow-与-backloggallery)`[]`）、`has_more`（bool，默认 `false`）、`num_pages`（int\|null）、`total`（int\|null） | `gts_backlog()` |
| `#/components/schemas/TaxonomySuggestionListResponse` | `result`*（[`TaxonomySuggestionResponse`](#taxonomysuggestionresponse)`[]`）、`has_more`（bool\|null）、`num_pages`（int\|null）、`total`（int\|null） | `taxonomy_list()`、`taxonomy_resolved()` |
| `#/components/schemas/TaxonomyCommentListResponse` | `result`*（[`TaxonomyCommentResponse`](#taxonomycommentresponse)`[]`）、`has_more`（bool\|null）、`num_pages`（int\|null）、`total`（int\|null） | `taxonomy_comments()` |
| `#/components/schemas/TaxonomySuggestionEditListResponse` | `result`*（[`TaxonomySuggestionEditEntry`](#taxonomysuggestioneditentry)`[]`）——没有分页键 | `taxonomy_edits()` |

## 边界与未实测

### 旧的 API 与站点侧其它观察

* **老接口已下线**：`GET https://nhentai.net/api/gallery/658856`（老教程里的 `/api/gallery/…`）→ **`403`**，`Content-Type: text/plain`，正文一句英文 `Use new API https://nhentai.net/api/v2/docs`（43 字节）。照抄老代码路径拿不到数据，这个 `403` 不是 `/api/v2` 行为——`/api/v2` 根本身 `200`（见 [`service_info()`](#service_info)）。
* `/api/v2/docs` 是站点给新 API 的文档/说明页（不是本包封装的路由，规范里也没有对应 operation）。
* `/api/v2/changelog` → `200 text/html`：站点自己的变更日志网页（规范 `info.description` 里也链了它），不是 API 资源。页内自述提到评论上限 50 条、以及 `/pages` 与 `/pages/{page_number}` 两个接口已于 4 月删除——这两条与规范 `gallery_comments()` 的 `per_page` 上限 50 互相印证。
* 本页没有任何媒体请求：`thumbnail`、`path`、`cover.path` 都是相对路径字符串，服务器前缀来自 `cdn_config()` / `site_config()`；CDN 主机一次都没请求过，也没验证 `Referer`、`Range`、限速等取图细节。本包不下载字节。

### 为什么没有把 `.to` 克隆站并进来

`.to` 域名站点与 `.net` 共用同一批画廊编号和标签语义，但接口契约不是同一套，所以本家族不把它登记为同族站点，也不做页面解析、不做 ID 转换、不做兜底回退。依据（**实测**）：

* 7 条 `/api/**` 路径全部 `404`：`/api/gallery/658856`、`/api/v2/galleries/658856`、`/api/definitely-not-a-route-xyz`、`/api/v2/openapi.json`、`/api/gallery/1`（`Accept: text/html`）、`/api/galleries/search?query=test`、`/api/v1/gallery/658856`。带 `Accept: application/json` 时，这些 `404` 正文是 `application/json` 的 `{"message": ""}`；带 `Accept: text/html` 时回 `text/html; charset=UTF-8` 完整错误页。**这只说明这些路径 404**：有限样本不能证明「`.to` 下不存在任何 `/api/**` 路由」，也不能证明写路由都坏了（`GET` 证明不了 `POST`）。
* 但不能说 `.to` 完全没有 JSON：`/trending-searches` → `200 application/json`，正文裸数组 10 条。「`.to` 只有 HTML、没有 JSON」这种笼统说法是错的。
* `.to` 的画廊页是 HTML：`/g/658856/` → `200 text/html`，页面内嵌 `new N.gallery(...)` 数据块，且那段不是合法 JSON（`num_pages` 后面带尾随逗号）。内嵌编号与 `.net` 不同（内嵌 `id` `642949`、`media_id` `3994845`，而 URL 是 `658856`、`.net` 这边 `media_id` 是 `4006343`）。
* `.to` 的标签对象额外带一个 `nh_id`，指向 `.net` 的标签 id（有样本对上：`.to` 本地 `tags.id` `22` ↔ `nh_id` `2937` ↔ `.net` `tags/tag/big-breasts` 的 `id` `2937`），**但实测出现负值**：`nh_id` 为 `-2`（`group` 分类）与 `-289`（`artist` 分类）。不存在覆盖全部标签的固定映射，任何「本地 id ↔ 站点 id」换算都可能是错的。

结论：`.to` 是另一套前端（HTML + 内嵌数据 + 少量自有 JSON 路由），与 `.net` 的 API v2 没有共同契约；并进本家族会让 `Nhentai` 返回值形状取决于站点，这正是本项目禁止的隐式兜底。完整依据与排除清单见[契约审计附注](nhentai-contract-notes.md)。

### 规范与实测不一致的地方（务必按实测写代码）

| 地方 | 规范说 | 实测是 | 你该怎么做 |
| :--- | :--- | :--- | :--- |
| 参数校验失败的状态码 | `422` + `HTTPValidationError`（`{"detail": [...]}`） | **`400`** + `{"error": "Validation error", "details": [...]}` | 按 `400` 分支处理；`details` 是字符串数组 |
| `search()` 的分页 | 参数表只有 `query` / `sort` / `page` | 传 `per_page=2` 被**忽略**（回 25 条、`per_page` 回显 `25`） | 只靠 `page` 翻页，固定一页条数 |
| `tag_list()` 的 `per_page` | `1..100`，默认 `25` | 传 `per_page=1` 被**忽略**（回 120 条、`per_page` 回显 `120`） | 别用自己的 `per_page` 算页码 |
| `taxonomy_resolved()` 的 `per_page` | `1..100`，默认 `25` | 传 `per_page=2` 被**忽略**（回 50 条）；未文档化的 `limit=2` 也无效 | 别依赖自己设的每页条数 |
| `num_pages` 与 `total` 的关系 | 规范只写类型 | `gallery_list()` 当次 `total` `646010`、`num_pages` `323037`，而 `total / per_page` 上取整是 `323005` | **不要**用 `total`/`per_page` 推算页数 |
| 翻页到底 | 无 | `page=100000&per_page=25` → `200`，只回 24 条且 id 重复尾部 | **不要**用「空结果」或「短页」当终止条件；自己设页码范围 |
| `total` 是否可空 | `integer \| null` | `gallery_tagged()` 当次 `total` 是 `null` | 用 `.get('total')`，别当整数算 |
| `tag_list()` 的 `alphabet` | `object \| null` | 只有 `sort=name` 时出现，默认 `popular` 时没有 | 切到 `sort=name` 再取，别猜键名 |
| 列表元素字段 | 与详情共用 `TagResponse` | 列表项缺 `is_community` / `pending_describe_id`；taxonomy 列表有 `tier` / `tier_page` 而详情没有 | 可选字段一律 `.get(...)` |
| `tags/search` 的正文 | `type` / `query` / `limit` 三个键都不是必填 | 本轮**没跑**这条 `POST` | 空正文规范层面合法，服务端行为**未实测** |

### 完全没实测的部分（不要当成已证实）

* **写与资源分配**：`favorite_add()`、`favorite_remove()`、`blacklist_update()`、`gallery_download()`，以及只读但属于 `POST` 的 `tag_search()`——一次都没发过。成功响应、错误文案、副作用、幂等性都无样本；`blacklist_update()` 正文形状来自规范，`tag_search()` 的空正文与未知 `query` 行为同样来自规范。
* **凭据路径**：整轮零凭据。带 Key 成功响应（`user_me()` 的 `email` 是否真的隐藏、`favorite_list()` / `blacklist_list()` / `gallery_favorite()` / `favorite_random()` 真实内容）全部未实测；无效 Key 会回什么也没试。
* **限流与开关**：`429` 与 `503` 一个样本都没有；规范限流表没被验证，响应头有没有 `Retry-After` 也没记录。`allow_favorites` / `allow_gts` / `allow_taxonomy` / `allow_downloads` 四个开关当次都开着（`GET` 都回 `200`），关掉时什么样未实测。
* **first-party 与内部路由**：`auth/*`（登录、注册、刷新、登出、会话）、`user/*`（改资料、删账号、头像、API Key 管理）、`moderation/*`（41 个操作）、`pow`、`captcha`、`zones/*`（4 个）——全部没请求过，本包也全部不封装。`user_me()` 是规范里 `user` 分组唯一对第三方开放的那一个。
* **数据内容**：非空评论（画廊 658856 当次没有评论）、非空编辑历史（当次那条提议没被编辑过）、非空公告（当次 `announcement` 是 `null`）、`recent_favorites` / `recent_comments` 内容、`taxonomy` 各种 `action` 的字段填充——都没样本。
* **其它参数面**：`gallery_tagged()` 除 `date` 外的排序值、`search()` 的数字/日期过滤语法（`pages:>10`、`uploaded:<7d`）、`user_show()` 的 id/slug 不匹配、`tag_ids()` 一次超过 100 个 id 或含不存在的 id、`include` 的其它组合、`gallery_comments()` 的 `page` 上限 2000、各枚举边界值——都没试。
* **媒体与 CDN**：零请求。服务器前缀、`path` 拼接斜杠形态、`Referer`、Range、被封的触发条件都没验证。
* **Python 方法覆盖面**：冒烟与两个示例已真跑 `gallery_list`、`gallery_show`、`search`、`gallery_popular`、`tag_show`、`gallery_comment_count`、`gallery_comments`、`tag_ids`、`site_config` 共 9 个原生方法；三个脚本退出 0，包含预期 404/400 错误请求，不是全部请求 200。其余 27 个方法没有以 Python 调用形式执行；31 个 `GET` 路径另有直接 HTTP 观察，逐条见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)。
* **数字全是快照**：`total`、`num_pages`、`count`、`num_favorites`、各 `*_count`、uuid、用户 id/slug、样本条目数都会随站点数据变化，本页每个具体数字都只是例子。

继续阅读：[客户端用法](nhentai.md) · [能力入口](nhentai-capabilities.md) · [契约审计附注](nhentai-contract-notes.md) · [验证记录](verification.md#nhentai匿名只读实测2026-09-20)
