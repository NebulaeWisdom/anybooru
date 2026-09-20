# nhentai：我要做什么，用哪个方法？

nhentai（`https://nhentai.net`）发布 JSON API v2 与 OpenAPI 3.1.0 规范（`https://nhentai.net/api/v2/openapi.json`，`info.version` = `2.0.0+14bccf7`，98 path / 114 operation / 129 schema）。本库按规范实现其中 **36 个原生方法**：**31 个 `GET`** + **4 个 `POST`** + **1 个 `DELETE`**。

其中 **32 个只读**：31 个 `GET` 加只读的 `POST /api/v2/tags/search`，即 `tag_search()`，语义是标签名补全。
**4 个写方法**是 `favorite_add()`、`favorite_remove()`、`blacklist_update()`、`gallery_download()`。`gallery_download()` 只申请整卷下载地址，**不下载文件**。

**为什么算新家族**：判据是契约而不是站名。路由在 `api/v2/...`；列表项与详情是两套字段；分页是 `page` + `per_page`；标签对象带 `type` 与 `count`；需凭据的路由用 `Authorization: Key <key>`。这些跟现有十一个家族（Danbooru / Moebooru / Serika / e621ng / Zerochan / Gelbooru / Gelbooru02 / Shuushuu / Sakuria / Anime-Pictures / Cosine）的完整契约均不同。

只覆盖 `.net` API v2。不做 `.to` 的 HTML 解析、跨站 ID 转换或失败回退；理由与样本见[契约附注](nhentai-contract-notes.md#6-to-与-net-的区别)。

**证据范围**：2026-09-20 的一批匿名只读请求让 31 条选中的 `GET` 路由**全部有直接 HTTP 证据**（25 个 `200`、6 个需要凭据的 `401`）。随仓库的脚本随后真的跑过：`test/nhentai.py` **10 次请求全部 PASS**（8 个 `200` 加两条预期错误路径）；两个示例各 **3 次与 5 次 `200`**，退出码都是 `0`；共 **9 个 Python 原生方法**实际执行。逐条 URL、状态码与响应摘要见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)。

方法存在不等于成功路径测过。每个方法的完整参数与逐字段说明在[方法参考](nhentai-api.md)；依据与排除项在[契约附注](nhentai-contract-notes.md)。本页只做「目的 → 方法」对照与一行索引，不重复参数表。

## 用法共同约定

细节见[客户端用法](nhentai.md)。

* `client` 由 `Nhentai('nhentai')` 创建，包内默认匿名。
* **返回一层都不拆**：分页是 `{"result", "num_pages", "per_page", "total"}`；`tags/ids`、`tags/search`、`galleries/popular`、`blacklist/ids` 是**裸数组**；`tags/{type}/{slug}` 是**裸对象**；`comments/count` 是**裸整数**；`galleries/random` 与 `favorites/random` 是规范未固定字段的对象。
* **页码从 1 起**。每页条数不都听你的：`tags/{tag_type}` 要 `1` 回 `120`；`taxonomy/resolved` 要 `2` 回 `50`；`search` 没有 `per_page`，传了被忽略。末页没有可靠判据，越界页码返回重复尾部。
* 参数越界规范写 `422`、站点实测回 `400`，带 `details` 数组。本库不归一化、不本地校验、不钳位、不重试。
* **本库不下载媒体**：只给 `path` 字符串与服务器列表，用 `site_config()` / `cdn_config()` 拿服务器列表；整卷用 `gallery_download()` 申请地址。

## 按目的找调用

| 我要做什么 | 调用 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| 看 API 版本 / 拿图片服务器列表 | `client.service_info()` / `client.site_config()` / `client.cdn_config()` | 无参数 → `GET /api/v2`（**没有尾斜杠**）返回 `{"version", "message"}` / `{"image_servers", "thumb_servers", "announcement"}` / 少一个 `announcement`。拼媒体地址用服务器列表，本库不下载 |
| 浏览最新画廊 / 翻页 | `client.gallery_list(page=1, per_page=2)` | 页码（从 1 起）+ 每页条数 → `{"result": [列表项], "num_pages", "per_page", "total"}`。翻下一页自己把 `page` 加一，客户端不翻页、不合并；`total` 可为 `null` |
| 按标签浏览 | `client.gallery_tagged(12227, sort='popular', page=1)` | 标签 id（不是标签名）+ 排序 + 页码 → 列表信封。`tag_id` 不存在是 `404` |
| 今日热门 / 随机一个 | `client.gallery_popular()` / `client.gallery_random()` | 无参数 → **裸数组**（列表项；别当固定条数）/ 规范未固定字段的对象 |
| 取一张画廊的详情 | `client.gallery_show(658856, include='comments,related')` | 画廊编号 + 逗号串 `include` → `title` / `cover` / `tags[]` / `pages[]` / `num_pages` / `num_favorites`。`include` 再追加 `comments`、`comment_count`、`related`、`suggestions` |
| 看相似画廊 | `client.gallery_related(658856)` | 画廊编号 → `{"result": [列表项, …]}`，**没有分页字段** |
| 看某画廊的标签提案 | `client.gallery_suggestions(658856, tier='all', limit=20)` | 画廊编号与筛选 → `result` 提案数组，可能带分页字段。完整取值见方法参考 |
| 找不存在的画廊 | `client.gallery_show(999999999)` | → `404 {"error": "Gallery not found"}`，抛 `AnybooruHTTPError` |
| 关键词 / 条件搜索 | `client.search(query='language:english', sort='date', page=1)` | 查询串（必备）+ `sort` + `page` → 列表信封。查询语法支持 `word`、`"exact phrase"`、`-word`、`type:value`、`pages:>10`、`uploaded:<7d` |
| 看单个标签 | `client.tag_show('language', 'english')` | 类别 + slug → **裸 TagResponse**：`id` / `type` / `name` / `slug` / `url` / `count` / 可空的 `description` 等 |
| 列某一类标签 | `client.tag_list('language', sort='name')` | 类别（七选一）+ `sort`（`name` / `popular`）→ 列表信封。`alphabet` 只在 `sort=name` 时出现 |
| 按 id 批量取标签 | `client.tag_ids('12227,6346')` | **一个逗号串**，最多 100 个，不是数组 → **裸数组** |
| 按前缀搜标签 | `client.tag_search(query='engli', type='language', limit=3)` | 请求体属性 `query` / `type` / `limit`。前两个可空，都不是必填 → **裸数组**；**本轮未发出** |
| 读某画廊的评论 / 只要数量 | `client.gallery_comments(658856, page=1, per_page=2)` / `client.gallery_comment_count(658856)` | 画廊编号 + 分页 → `{"result": [评论], "num_pages", "per_page", "total"}`（元素含 `poster` / `post_date` / `body`）/ **裸整数** |
| 看自己的收藏 | `client.favorite_list(page=1)` / `client.favorite_random()` / `client.gallery_favorite(658856)`（**需 Key**） | 页码，可选 `q` → 收藏列表信封 / 规范未固定字段的对象 / 画廊编号 → `{"favorited", "num_favorites"}`，只读检查 |
| 收藏 / 取消收藏 | `client.favorite_add(658856)` / `client.favorite_remove(658856)`（**需 Key**） | 画廊编号 → `{"favorited", "num_favorites"}`。需要 `allow_favorites` |
| 看 / 改黑名单 | `client.blacklist_list()` / `client.blacklist_ids()` / `client.blacklist_update(added=[12227], removed=[])`（**需 Key**） | 无参数 → `{"tags", "count"}` / **裸整数数组** / 请求体 `{"added": [整数], "removed": [整数]}` → `{"success", "count"}` |
| 申请整卷下载地址 | `client.gallery_download(658856, format='cbz')`（**需 Key**） | `format` ∈ `zip` / `cbz` / `torrent` → `{"url", "expires_at"}`。**只给地址，不下载文件** |
| 看自己 / 别人的账号 | `client.user_me()`（**需 Key**）/ `client.user_show(981330, 'jegutimantion')` | 自己的资料对象，API key 鉴权时 `email` 为 `null` / 公开资料，数字 id **加**正确 slug，缺一个就 `404` |
| 看社区标签提案 | `client.taxonomy_list(per_page=2)` / `client.taxonomy_stats()` / `client.gts_new_tags(limit=2)` | 提案列表、处理统计与新标签。从列表取 UUID 后，用下方的详情、评论和编辑历史方法继续读取 |
| 用别的路径或动词 | `client.request('GET', '/api/v2/galleries', params={'page': 1})` | 动词 + 路径 + `params` / `data` / `headers` → 同一条通路。前导 `/` 去掉，`data` 是纯 JSON 正文 |

## 完整方法索引：31 `GET` + 4 `POST` + 1 `DELETE` = 36

每个方法一行。参数范围、缺省与逐字段说明只放在[方法参考](nhentai-api.md)。路径都接在站点根 `https://nhentai.net` 后面，**除 `service_info()`（`api/v2` 本身）外都在 `api/v2/...` 下**。带「**需凭据**」的行需要已有认证；其成功路径均未实测。

### 服务、配置与搜索（4 个 `GET`，匿名可读）

* `service_info()` → `GET api/v2`，没有尾斜杠，返回 `{"version", "message"}`。
* `cdn_config()` → `GET api/v2/cdn`，返回 `{"image_servers", "thumb_servers"}`。
* `site_config()` → `GET api/v2/config`，返回 `{"image_servers", "thumb_servers", "announcement"}`，`announcement` 可空。
* `search(query, **params)` → `GET api/v2/search`，返回分页信封。`query` 必备；`**params` 里只有 `sort` 与 `page`，**没有 `per_page`**。

### 画廊浏览（7 个 `GET`，匿名可读）

* `gallery_list(**params)` → `GET api/v2/galleries`，分页信封；参数 `page`、`per_page`。
* `gallery_tagged(tag_id, **params)` → `GET api/v2/galleries/tagged`，分页信封；`tag_id` 必填，加 `sort` / `page` / `per_page`。
* `gallery_popular()` → `GET api/v2/galleries/popular`，**裸数组**，无参数。
* `gallery_random()` → `GET api/v2/galleries/random`，规范未固定字段的对象。
* `gallery_show(gallery_id, **params)` → `GET api/v2/galleries/{gallery_id}`，详情对象；`include` 是逗号串。
* `gallery_related(gallery_id)` → `GET api/v2/galleries/{gallery_id}/related`，返回 `{"result": [列表项]}`。
* `gallery_suggestions(gallery_id, **params)` → `GET api/v2/galleries/{gallery_id}/suggestions`，提案列表信封；参数 `tier`、`limit`；需要 `allow_gts`。

### 标签（4 个：3 个 `GET` 加 1 个只读 `POST`）

* `tag_ids(ids)` → `GET api/v2/tags/ids`，**裸数组**；`ids` 是逗号串。
* `tag_search(**attributes)` → `POST api/v2/tags/search`，**裸数组**；请求体 `{"query", "type", "limit"}`；本轮未发出。
* `tag_list(tag_type, **params)` → `GET api/v2/tags/{tag_type}`，分页对象；`alphabet` 按排序分支出现。
* `tag_show(tag_type, slug)` → `GET api/v2/tags/{tag_type}/{slug}`，**裸 TagResponse 对象**。

### 评论（2 个 `GET`，匿名可读）

* `gallery_comments(gallery_id, **params)` → `GET api/v2/galleries/{gallery_id}/comments`，分页信封；参数 `page`、`per_page`。
* `gallery_comment_count(gallery_id)` → `GET api/v2/galleries/{gallery_id}/comments/count`，**裸整数**。

### 收藏、黑名单与下载（9 个，**全部需凭据**；其中 3 个 `POST` 与 1 个 `DELETE`）

* `gallery_favorite(gallery_id)` → `GET api/v2/galleries/{gallery_id}/favorite`，返回 `{"favorited", "num_favorites"}`，只读检查。
* `favorite_add(gallery_id)` → `POST api/v2/galleries/{gallery_id}/favorite`；**写**，需要 `allow_favorites`。
* `favorite_remove(gallery_id)` → `DELETE api/v2/galleries/{gallery_id}/favorite`；**写**，需要 `allow_favorites`。
* `favorite_list(**params)` → `GET api/v2/favorites`，分页信封；参数 `q`、`page`，没有 `per_page`。
* `favorite_random()` → `GET api/v2/favorites/random`，规范未固定字段的对象。
* `blacklist_list()` → `GET api/v2/blacklist`，返回 `{"tags", "count"}`。
* `blacklist_update(**attributes)` → `POST api/v2/blacklist`；请求体 `{"added": [整数], "removed": [整数]}`，两者都不是必填、缺省 `[]`，客户端原样发送；**写**。
* `blacklist_ids()` → `GET api/v2/blacklist/ids`，**裸整数数组**。
* `gallery_download(gallery_id, **params)` → `POST api/v2/galleries/{gallery_id}/download`，返回 `{"url", "expires_at"}`；`format` 三选一；需要 `allow_downloads`；**只申请地址**。

### GTS 与 taxonomy（8 个 `GET`，匿名可读，需要功能开关）

* `gts_backlog(**params)` → `GET api/v2/gts/backlog`，分页信封；参数 `page` / `per_page` / `tag_id` / `action` / `sort_by` / `sort`；需要 `allow_gts`。
* `gts_new_tags(**params)` → `GET api/v2/gts/new-tags`，返回 `{"result": […]}`；参数 `limit`；需要 `allow_gts`。
* `taxonomy_list(**params)` → `GET api/v2/taxonomy`，提案列表信封；参数 `tier` / `page` / `per_page` / `q` / `target_tag_id` / `sort_by` / `sort` / `action` / `discussion` / `edited`；需要 `allow_taxonomy`。
* `taxonomy_stats()` → `GET api/v2/taxonomy/stats`，统计对象，含 `pending` / `accepted_30d` / `recent_accepted` 等；需要 `allow_taxonomy`。
* `taxonomy_resolved(**params)` → `GET api/v2/taxonomy/resolved`，提案列表信封；比列表多 `status` 与 `resolved_at` 排序。
* `taxonomy_show(suggestion_id)` → `GET api/v2/taxonomy/{suggestion_id}`，单条提案对象；`suggestion_id` 是 UUID 字符串。
* `taxonomy_comments(suggestion_id, **params)` → `GET api/v2/taxonomy/{suggestion_id}/comments`，评论分页信封。
* `taxonomy_edits(suggestion_id)` → `GET api/v2/taxonomy/{suggestion_id}/edits`，返回 `{"result": […]}`。

### 用户（2 个 `GET`；1 个公开、1 个需凭据）

* `user_show(user_id, slug)` → `GET api/v2/users/{user_id}/{slug}`，公开资料对象；数字 id 与 slug 两个都要对。
* `user_me()` → `GET api/v2/user`，自己的账号资料；**需凭据**。

另有通用入口 `request(method, path, *, params=None, data=None, headers=None)`：动词、路径、查询、JSON 正文与额外请求头由你给全。前导 `/` 去掉后拼站点根；`params` 按共享编码发出，`None` 丢弃、布尔小写、数组编成 `key[]=`；`data` 是纯 JSON 正文；同名请求头覆盖实例的 `api_key` 凭据。

## 本库不封装的能力

下面这些都在官方规范的 98 个 path 里，但**不在本库的 36 个方法内**。需要时用 `client.request(method, path, params=…, data=…, headers=…)` 自己发。本库不登录、不签 PoW、不填 CAPTCHA。

| 类别 | 规范里的例子 | 为什么不封装 |
| :--- | :--- | :--- |
| 第一方账号与认证 | `POST /auth/login`、`register`、`reset`、`GET /user/keys` | 规范把 `auth` / `user` 两组标为第一方 / 内部使用。**例外是 `GET /api/v2/user`，即 `user_me()`**，它被明确允许用 API key |
| `User Token` 专属写操作与管理 | 画廊编辑、提案投票 / 撤回、`PUT` / `DELETE /api/v2/user`、`moderation/*` | 规范只给站点会话或管理权限，不提供原生封装 |
| 评论与提案写入 | `POST /galleries/{id}/comments`、`POST` / `PATCH` / `DELETE /taxonomy*` | 写操作 + PoW + CAPTCHA |
| 反自动化挑战与广告位 | `/pow`、`/captcha`、`/zones`、`/zones/i` | 与数据读取无关 |
| 旧版路由、网页与镜像站 | `/api/gallery/{id}`，实测 `403 text/plain`：`Use new API …/api/v2/docs`；`nhentai.net` 页面；`nhentai.to` 的 HTML 与内嵌 JS | 本库不抓 HTML、不解析内嵌 JavaScript、**不做 `.to` ↔ `.net` 的 id 转换**，也没有兜底路径 |
| 媒体字节 | `i1`–`i4` / `t1`–`t4.nhentai.net` 上的图片 | 本库不下载媒体；整卷用 `gallery_download()` 申请地址后由你自己取 |

## 边界与未实测

* **没发过的方法**：`tag_search()` 与 4 个写方法（`favorite_add()`、`favorite_remove()`、`blacklist_update()`、`gallery_download()`）本轮**零请求**，只有规范依据。带 Key 的成功路径、错误 key、`user_me()` 的 `email` 是否一定为 `null` 也没有实测样本。本库没有 User Token 登录 / 构造参数，通用头覆盖未实测。
* **两层证据都跑过，口径不同**：31 条 `GET` 路由是**直接 HTTP** 观察。随仓库的 `test/nhentai.py`（10 次请求 10 PASS、退出 0）与两个示例（3 次、5 次 `200`，退出 0）是 **Python 方法**的实际执行，只覆盖其中 **9 个**方法。逐条命令与响应见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)。
* **功能开关、限流与媒体**：`allow_gts` / `allow_taxonomy` / `allow_favorites` / `allow_downloads` 关闭时的 `503` 未实测。规范写了每分钟配额，输入资料提到 `429` 与极端页码 `503`，本轮既没触发也没验证。所有 CDN 主机零请求，没有任何图片字节。
* **空样本与没穷尽的枚举**：`announcement` 非空形态、评论非空元素、`taxonomy_edits` 非空元素、`galleries/random` 与 `favorites/random` 的固定字段都没有样本。`include` 的取值与非法值行为、`taxonomy` 的 `tier` / `status` / `action`、`gts_backlog` 的 `sort_by`、`tag_search` 的属性组合、各单位每页条数的上限，都只有规范或单次样本。
* **规范与站点会不一致**：参数越界规范写 `422`、站点实测回 `400`；`num_pages` 不等于 `ceil(total/per_page)`。本库原样透出，不归一化。
* **`.to` 的结论来自有限样本**：7 条 `/api/**` 的 `404` 不能证明所有路由不存在，`GET` 不能证明 `POST` 路由不可用。作品 id 不通用、标签 id 只有部分对得上，含负值，所以不做映射与兜底。

更细的未实测清单见[客户端用法](nhentai.md#边界与未实测)；逐条命令与响应见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)；依据出处与排除项见[契约附注](nhentai-contract-notes.md)。

继续阅读：[客户端用法](nhentai.md) · [方法参考](nhentai-api.md) · [验证记录](verification.md#nhentai匿名只读实测2026-09-20)。
