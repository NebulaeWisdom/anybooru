# e-shuushuu：我要做什么，用哪个方法？

e-shuushuu 接口是标准 REST，基础路径 `https://e-shuushuu.net/api/v1`。本库分三档：**35 个公开资源读方法**（匿名实际执行范围见文末）、**1 个私有读方法** `user_ratings`（本人或持 `USER_EDIT_PROFILE` 的版主）、**5 个认证方法**（都要显式调用，本轮一次都没执行）。完整参数表、逐字段说明与可复制片段见[方法参考](shuushuu-api.md)；接口依据、权限与排除项见[接口依据与排除项](shuushuu-contract-notes.md)。

共同约定：

* `client` 由 `Shuushuu('shuushuu')` 创建，默认匿名；只有显式给出 `access_token` 才带 Bearer。
* 筛图只认 `tag_id`：先用 `search(q='标签名')` 或 `tag_list(search='标签名')` 拿编号，再用编号筛图。
* 分页统一是 `page`（从 1 开始）与 `per_page`（默认 20，最大 100）；`/search` 用 `limit`（默认 20）与 `offset`（默认 0）。客户端不设默认、不钳位，超限由服务端回 `422`。
* 多值 `status` 重复同一个键（`status=1&status=2`）；逗号串参数（`tags`、`exclude_tags`、`ids`、`image_ids`）自己拼成 `'46,169'`。
* 示例编号、标签名与 md5（`46`、`1119196`、`846421`、`629189`、`de9c2f0aa6b358e3f041d2c933c31785` 等）来自接口文档既有记录（T），字段名与结构来自官方 OpenAPI；本库请求结果见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。

## 按目的找调用

| 我要做什么 | 调用 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| 标签名换成 tag_id | `client.search(q='long hair', limit=5)` | 标签名 → `{"query", "entity": "tags", "hits": [{"tag_id", "title", "type", "usage_count", …}], "total", "limit", "offset"}`；`hits[].tag_id` 用于筛图 |
| 多个标签同时筛图 | `client.image_list(tags='46,169', tags_mode='all', per_page=2)` | 逗号串 tag_id + 模式 → `{"total", "page", "per_page", "images": [完整图片对象], "comments": null}` |
| 排除标签、按层级展开 | `client.image_list(tags='46', exclude_tags='169', tag_depth=1)` | `tag_depth` 0–9 控制子标签层数（0=只要该标签）→ 同上 |
| 按尺寸/评分/收藏数/日期筛 | `client.image_list(min_width=1920, min_height=1080, min_rating=8, min_favorites=10, date_from='2024-01-01')` | 阈值（`min_rating` 1–10）→ 同上 |
| 按上传者/收藏者/评论者筛 | `client.image_list(user_id=5, favorited_by_user_id=7, commenter=10)` | 用户编号 → 同上 |
| 按评论正文筛图 | `client.image_list(commentsearch='happy -sad')` | 词按单条评论求值，支持 `"短语"` 与 `-排除词` → 同上 |
| 翻下一页 | `client.image_list(tags='46', page=2, per_page=100)` | 页码 + 每页数（≤100）→ 该页；不自动请求下一页 |
| 让每张图带评论 | `client.image_list(tags='46', include_comments=True)` | `true` 时 `comments` 变成 `{image_id: [评论, …]}`；默认 `null` |
| 看一张图 | `client.image_show(1119196)` | 图片编号 → 单个完整图片对象（`image_id`、`md5_hash`、`width`、`height`、`caption`、`source_url`、`status`、`rating`、`favorites`、`tags`、`url`、`thumbnail_url`、`medium_url`、`large_url` …） |
| 看图的标签 | `client.image_tags(1119196)` | 图片编号 → `{"image_id", "tags": [{"tag_id", "tag", "type_id"}]}`；标签名在 `tag`，编号在 `tag_id` |
| 图标签增删流水 | `client.image_tag_history(1119196, per_page=20)` | 图片编号 → `{"total", "page", "per_page", "items": [{"action", "user", "date", "tag", …}]}` |
| 图状态变更流水 | `client.image_status_history(1119196)` | 图片编号 → 同上形状，条目含新旧状态与原因；部分字段按查看者身份隐藏 |
| 图被转载的记录 | `client.image_reposts(1119196)` | 图片编号 → `{"total", "items": [{"image_id", "user", "marked_at"}]}`；没有分页参数 |
| 图已关闭的审核 | `client.image_reviews(1119196)` | 图片编号 → `{"total", "page", "per_page", "items": [{"review_id", "reason_category", "outcome", "created_at", "closed_at"}]}` |
| 图被谁收藏 | `client.image_favorites(1119196, per_page=20)` | 图片编号 → `{"total", "page", "per_page", "users": [用户对象]}`；可按 `sort_by=username` 等排序 |
| 图被谁评分 | `client.image_ratings(1119196, sort_by='rating')` | 图片编号 → `{"total", "page", "per_page", "users": [带评分的用户对象]}` |
| 以图搜相似图 | `client.image_similar(1119196, threshold=70)` | 图片编号 + 最低相似度（0–100）→ `{"query_image_id", "similar_images": [按相似度降序]}` |
| 按 md5 查重 | `client.image_by_hash('de9c2f0aa6b358e3f041d2c933c31785')` | 32 位 md5 → `{"md5_hash", "found": 命中数, "images": [基础图片对象]}` |
| 全站图片统计 | `client.image_stats()` | 无参数 → `{"total_images", "total_favorites", "average_rating"}` |
| 支持导入的站点 | `client.image_import_sites()` | 无参数 → `[{"site", "example_url"}]` |
| 搜标签、看使用次数与别名 | `client.tag_list(search='long hair', type=1, per_page=20)` | 名字/类型 → `{"total", "page", "per_page", "tags": [标签对象], "invalid_ids"}`；没有 `limit` 参数 |
| 标签完整资料 | `client.tag_show(46)` | 标签编号 → 标签对象 + `total_image_count`、`aliases`、`aliased_tag_id`、`parent_tag_id`、`child_count`、`created_by`、`links`、`sources`、`characters` |
| 标签下的图（含子标签） | `client.tag_images(46, tag_depth=0, per_page=2)` | 标签编号；`tag_depth` 省略=整棵层级，0=只要该标签 → `{"total", "page", "per_page", "images": [基础图片对象]}`；这里的图片项没有 `tags` 数组 |
| 作品下的角色 | `client.tag_characters(6209, per_page=2)` | 需要 Source 类型标签编号；先由 `tag_show(6209)` 核对 `type=2`，不要把类型值 2 当成标签编号 → 角色 `tags` 列表；不是 Source 类型回 400 |
| 标签资料改动史 | `client.tag_history(46, per_page=20)` | 标签编号 → `{"total", "page", "per_page", "items": [改名/改类型/改说明/改别名/改继承]}` |
| 标签在图片上的增删史 | `client.tag_usage_history(46, per_page=20)` | 标签编号 → `{"total", "page", "per_page", "items": [图片级的加/删标签流水]}` |
| 搜标签（比 `tag_list` 更多过滤） | `client.search(q='sakura', aliases='hide', has_children='yes', sort_by='usage_count')` | 关键词 + 过滤/排序 → `{"query", "entity": "tags", "hits", "total", "limit", "offset"}` |
| 找用户 | `client.user_list(search='whitekitten', per_page=2)` | 名字片段 → `{"total", "page", "per_page", "users": [用户对象]}` |
| 看一个用户 | `client.user_show(846421)` | 用户编号 → 用户对象（`username`、`user_title`、`avatar_url`、`groups`、`admin`、`active`、`posts`、`image_posts`、`favorites`、`date_joined`、`last_login`、`last_active`、`location`、`website`、`interests`、`gender`、`maximgperday`） |
| 用户上传的图 | `client.user_images(846421, per_page=2, sort_by='date_added')` | 用户编号 → `{"total", "page", "per_page", "images": [完整图片对象]}` |
| 用户收藏的图 | `client.user_favorites(846421, per_page=2)` | 用户编号 → 同上形状（完整图片对象） |
| 用户公开的收藏标签 | `client.user_favorite_tags(846421)` | 用户编号 → `{"characters": [...], "sources": [...], "artists": [...]}`，按位置排序 |
| 用户公开改动史 | `client.user_history(846421, per_page=20)` | 用户编号 → `{"total", "page", "per_page", "items": [标签改动、图片标签增删、公开状态变更]}` |
| 用户给哪些图评过分 | `client.user_ratings(846421, min_rating=8)` | **私有**：本人或持 `USER_EDIT_PROFILE` 的版主；参数 `min_rating`/`max_rating`（1–10）、`page`、`per_page`、`sort_by`、`sort_order` → `{"total", "page", "per_page", "images": [带本人评分的图片对象]}` |
| 按图读评论 | `client.comment_image(1118862, per_page=2)` | 图片编号 → `{"total", "page", "per_page", "comments": [评论对象]}` |
| 按用户读评论 | `client.comment_user(59006, per_page=20)` | 用户编号 → 同上 |
| 搜评论 | `client.comment_list(image_ids='1118862,1119196', search_text='happy', per_page=2)` | 过滤项 → 同上；`search_mode` 取 `all_words`（默认）/ `like` / `natural` / `boolean` |
| 看一条评论 | `client.comment_show(629189)` | 评论编号 → 单个评论对象（`post_id`、`image_id`、`user_id`、`user`、`post_text`、`post_text_html`、`parent_comment_id`、`deleted`、`date`、`update_count`） |
| 全站评论统计 | `client.comment_stats()` | 无参数 → `{"total_comments", "total_images_with_comments", "average_comments_per_image"}` |
| 站点新闻 | `client.news_list(page=1, per_page=1)` | 分页 → `{"total", "page", "per_page", "news": [{"title", "news_text", "date", "news_id", …}]}` |
| 一条新闻 | `client.news_show(1)` | 新闻编号 → 单条新闻对象 |
| 站点限制与标签类型表 | `client.meta_config()` | 无参数 → `{"max_search_tags": 5, "max_search_users": 5, "max_image_size": …, "max_avatar_size": …, "upload_delay_seconds": …, "search_delay_seconds": …, "tag_types": {"1": "Theme", …}, "ml_tag_suggestions_enabled": …, "ml_character_suggestions_enabled": …}` |
| 全部权限名 | `client.permission_list()` | 无参数 → 权限名到数据库值的映射，例如 `{"IMAGE_TAG_ADD": "image_tag_add", "TAG_CREATE": "tag_create", …}` |
| 登录拿 token | `client.auth_login('myname', 'secret')` | 用户名 + 密码（不传就用配置值）→ `access_token/token_type/expires_in/user`，并接收 Cookie；需真实账号，执行状态见文末 |
| 续期 | `client.auth_refresh()` | 无参数（用 Cookie 里的 refresh token）→ 同登录返回。未执行 |
| 当前用户 | `client.auth_me()` | 无参数 → 当前用户资料对象；接口没给字段表。未执行，匿名调用只会得到 `401` |
| 登出 | `client.auth_logout()` | 无参数 → `{"message": …}`，成功后客户端清本地 token 与 Cookie。未执行 |
| 登出全部设备 | `client.auth_logout_all()` | 无参数（需 Bearer）→ `{"message": …}`。未执行 |

## 完整方法索引（35 公开读 + 1 私有读 + 5 认证）

每个原生方法一行；参数范围、默认值和字段表只放在[方法参考](shuushuu-api.md)。以下路径均接在 `https://e-shuushuu.net` 后面。

### 图片

* `image_list(**params)` → `GET /api/v1/images`，按数字标签ID、上传者、尺寸等筛图，保留分页与 `images`。
* `image_show(image_id)` → `GET /api/v1/images/{image_id}`，完整图像信息与媒体URL。
* `image_tags(image_id)` → `GET /api/v1/images/{image_id}/tags`，标签名在 `tag`，编号在 `tag_id`。
* `image_tag_history(image_id, **params)` → `GET /api/v1/images/{image_id}/tag-history`，`items` 记录加删标签。
* `image_status_history(image_id, **params)` → `GET /api/v1/images/{image_id}/status-history`，新旧状态及按身份遮罩的原因。
* `image_reposts(image_id)` → `GET /api/v1/images/{image_id}/reposts`，不分页的 `total/items`。
* `image_reviews(image_id, **params)` → `GET /api/v1/images/{image_id}/reviews`，已关闭审核会话。
* `image_favorites(image_id, **params)` → `GET /api/v1/images/{image_id}/favorites`，收藏者 `users`。
* `image_ratings(image_id, **params)` → `GET /api/v1/images/{image_id}/ratings`，带 `rating/rated_at` 的评分者。
* `image_similar(image_id, **params)` → `GET /api/v1/images/{image_id}/similar`，IQDB相似度结果 `similar_images`。
* `image_by_hash(md5_hash)` → `GET /api/v1/images/search/by-hash/{md5_hash}`，命中数 `found` 与基础图片。
* `image_stats()` → `GET /api/v1/images/stats/summary`，全站图片数、收藏总数与平均分。
* `image_import_sites()` → `GET /api/v1/images/import-sites`，支持导入的站点与示例URL。

### 标签与标签搜索

* `tag_list(**params)` → `GET /api/v1/tags`，名字/类型/编号查标签，数量参数是 `per_page`。
* `tag_show(tag_id)` → `GET /api/v1/tags/{tag_id}`，标签关系、外链与 `total_image_count`。
* `tag_images(tag_id, **params)` → `GET /api/v1/tags/{tag_id}/images`，基础图片，不含详细 `tags`。
* `tag_characters(tag_id, **params)` → `GET /api/v1/tags/{tag_id}/characters`，Source标签关联的角色。
* `tag_history(tag_id, **params)` → `GET /api/v1/tags/{tag_id}/history`，标签名字/类型等资料的改动。
* `tag_usage_history(tag_id, **params)` → `GET /api/v1/tags/{tag_id}/usage-history`，标签在图片上的加删。
* `search(**params)` → `GET /api/v1/search`，标签搜索，`hits` 不是图片。

### 用户

* `user_list(**params)` → `GET /api/v1/users`，按用户名片段查公开资料。
* `user_show(user_id)` → `GET /api/v1/users/{user_id}`，指定用户的公开资料。
* `user_images(user_id, **params)` → `GET /api/v1/users/{user_id}/images`，上传过的完整图片对象。
* `user_favorites(user_id, **params)` → `GET /api/v1/users/{user_id}/favorites`，收藏的完整图片对象。
* `user_favorite_tags(user_id)` → `GET /api/v1/users/{user_id}/favorite-tags`，按位置分组的角色、来源与画师收藏。
* `user_ratings(user_id, **params)` → `GET /api/v1/users/{user_id}/ratings`，**私有**评分记录，本人或USER_EDIT_PROFILE版主可见。
* `user_history(user_id, **params)` → `GET /api/v1/users/{user_id}/history`，该用户公开的标签与状态改动。

### 评论

* `comment_list(**params)` → `GET /api/v1/comments`，按图片、用户或评论文字筛选。
* `comment_show(comment_id)` → `GET /api/v1/comments/{comment_id}`，编号取评论的 `post_id`。
* `comment_image(image_id, **params)` → `GET /api/v1/comments/image/{image_id}`，指定图的评论。
* `comment_user(user_id, **params)` → `GET /api/v1/comments/user/{user_id}`，指定用户发表的评论。
* `comment_stats()` → `GET /api/v1/comments/stats/summary`，评论总数、有评论的图片数与平均数。

### 新闻与站点信息

* `news_list(**params)` → `GET /api/v1/news`，按新到旧返回 `news` 数组。
* `news_show(news_id)` → `GET /api/v1/news/{news_id}`，新闻标题、正文、作者与日期。
* `meta_config()` → `GET /api/v1/meta/config`，限制值、标签类型与ML功能开关。
* `permission_list()` → `GET /api/v1/permissions`，权限枚举名与数据库值的映射。

### 显式认证

* `auth_login(username=None, password=None)` → `POST /api/v1/auth/login`，发送JSON凭据，保存返回的token与Cookie。
* `auth_refresh()` → `POST /api/v1/auth/refresh`，只用同会话refresh Cookie换新token。
* `auth_me()` → `GET /api/v1/auth/me`，需登录，返回未定型的当前用户对象。
* `auth_logout()` → `POST /api/v1/auth/logout`，吊销当前refresh token，成功清除本地认证状态。
* `auth_logout_all()` → `POST /api/v1/auth/logout-all`，吊销所有设备refresh token，成功清除本地认证状态。

## 本库不封装的能力

这些都有真实路由，只按当前范围排除；需要时用通用 `request()` 自己发（**只有 JSON 才解析**）。

| 类别 | 例子 | 为什么不封装 |
| :--- | :--- | :--- |
| 内容写接口 | `POST /api/v1/images/upload`、`PATCH /api/v1/images/{id}`、`POST /api/v1/images/{id}/rating?rating=8`、`POST /api/v1/images/{id}/favorite`、`POST /api/v1/comments`、`POST /api/v1/tags`、`POST /api/v1/tags/batch`、`PUT /api/v1/tags/{id}` | 需要登录且会改站点内容；本家族不提供这些原生方法 |
| 个人面读接口 | `GET /api/v1/users/me`、`/users/me/warnings`、`/users/me/taste-profile`、`GET /api/v1/images/recommended`、`/images/bookmark/me`、`/images/bookmark/page` | 需要登录，属于个人资料、推荐与书签 |
| 举报与审核相关读接口 | `GET /api/v1/images/{id}/reports`、`/api/v1/admin/reports*`、`/api/v1/admin/reviews*` | 需要 `report_view` 或管理权限 |
| 机器学习标签建议 | `/api/v1/ml-tag-suggestions/analyze`、`/api/v1/ml-suggestions*`、`GET /api/v1/images/{id}/ml-tag-suggestions`、`GET /api/v1/tags/suggestion-stats` | 需要相应权限，且属于审核流程 |
| 私信 | `/api/v1/privmsgs*` 全部 | 需要登录且是私人内容 |
| 横幅、捐赠、角色—来源链接 | `GET /api/v1/banners/`、`/banners/current`、`GET /api/v1/donations`、`/api/v1/character-source-links*` | 站点展示或维护性数据，与图片浏览无关 |
| 重复的收藏入口 | `GET /api/v1/favorites/user/{user_id}`、`GET /api/v1/favorites/image/{image_id}` | 接口自身标为 deprecated，等价数据已由 `user_favorites` / `image_favorites` 提供 |
| 非 JSON 响应 | `GET /api/v1/images.atom`、`/api/v1/tags/{id}/images.atom`、`GET /api/v1/images/random`（`302` 跳转）、`/images/{filename}` 与 `/thumbs/*` 等媒体路由 | 不是 JSON，客户端不解码字节或 HTML |
| 管理面 | `/api/v1/admin/*` 全部 | 需要管理员权限 |

## 边界与未实测

* 真实执行覆盖 **10 个公开读方法**（`search`、`tag_list`、`image_list`、`image_show`、`tag_show`、`comment_list`、`image_stats`、`meta_config`、`user_list`、`news_list`）：10 次冒烟请求里 8 次 `200`、1 次 `422`（`per_page` 超上限）、1 次 `404`（不存在的图片编号），两个示例各 4 次 `200`；其余 **25 个公开读方法**没有本轮样本，依据是OpenAPI及明确标注的T既有记录，逐条见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。
* **私有与认证面一次都没执行**：`user_ratings` 需要本人或版主权限；5 个认证方法需要账号。不要把它们写成“匿名可用”，也不要用 `auth_me()` 当匿名探针。
* **按身份变化的字段未逐条实测**：`image_status_history` 会按查看者隐藏原因与操作者，其匿名成功形态与登录对照均没有本轮样本。
* **写入与个人面都没有方法**：本库不做上传、评分、收藏、评论、私信、管理与审核动作，也不提供推荐、书签、个人资料接口；需要时用 `request()` 自己发，并自行承担凭据与副作用。
* 站点限制、冷却时间与标签类型映射以 `meta_config()` 的实时返回为准；不要把接口文档里记录过的数字当作永久常量。

继续阅读：[客户端用法](shuushuu.md) · [方法参考](shuushuu-api.md) ·
[接口依据与排除项](shuushuu-contract-notes.md) · [验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。
