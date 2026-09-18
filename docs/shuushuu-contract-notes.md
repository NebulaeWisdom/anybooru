# e-shuushuu：接口依据、权限与排除项

本页供核对接口依据，不代替[客户端用法](shuushuu.md)或[方法参考](shuushuu-api.md)。
客户端一共 **35 个公开读方法 + 1 个私有读方法（`user_ratings`）+ 5 个认证方法 = 41 个**，
没有图片/评论等内容写方法、没有 HTML 抓取、没有媒体下载；认证里的 POST 会改变账号会话，必须显式调用。

## 资料来源与等级

| 标记 | 来源 | 证明范围 |
| :--- | :--- | :--- |
| **O：官方 OpenAPI** | `https://e-shuushuu.net/api/openapi.json`（服务自称 **Shuushuu API 2.0.0**，`openapi` 版本 `3.1.0`），本轮抓取成功（HTTP 200） | 41 个方法的路径、HTTP 动词、参数名/类型/范围/默认值、请求体与 200 响应的 schema 名；**本文的字段与默认值以它为准** |
| **T：随附接口文档** | 接入时收到的《e-shuushuu 接口文档（综合版）》，没有可公开核对的发布链接 | 认证流程与账号安全规则的文字说明、若干匿名请求的具体结果（`per_page=200` → `422`、`/search` 的 `entity` 恒为 `"tags"`、`tags=1+2` 过滤被静默丢弃、`/tags` 传 `limit` 无效、随机图与媒体路由 `302`） |
| **L：本库真实执行** | 维护者写入[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19) | 导入与构造退出 0；冒烟 10 次请求（8×200、1×422、1×404）；两个示例各 4×200、退出 0、stderr 为空（UTC 2026-09-18T18:14:32Z–18:15:18Z）。覆盖 10 个公开读方法，并实际发出了重复键 `status=1&status=2` 与 `include_comments=false` |

说明三点：

* **O 的“指针”**：本文用 OpenAPI 的 JSON 指针定位，例如
  `#/paths/~1api~1v1~1images/get`、`#/components/schemas/ImageDetailedResponse`。
  指针里的 `~1` 是 JSON Pointer 对 `/` 的转义。
* **如出现行号，都是本次格式化副本的行号**（例如图片列表操作在副本 4216–4221 行、
  `ImageSortBy` schema 在 15687 行、`TokenResponse` 在 21162 行），那是打印排版位置，
  **不是上游源码行号**，引用时按指针核对。
* **不把 T 的记录升级成 L**：T 里那些匿名结果仍是“接口文档记录过”，本页如实标注；
  本库自己的执行范围只认 L。

## 41 个方法的逐条依据

“面”一列按资源用途与接口描述分为公开、私有、认证；**公开不等于本轮匿名成功实测**，权限敏感字段见后文。

### 图片（13，全部公开）

| 方法 | 请求 | OpenAPI 依据（指针 · operationId · 200 schema） | 面 |
| :--- | :--- | :--- | :--- |
| `image_list(**params)` | `GET /api/v1/images` | `#/paths/~1api~1v1~1images/get` · `list_images_api_v1_images_get` · `ImageDetailedListResponse` | 公开 |
| `image_show(image_id)` | `GET /api/v1/images/{image_id}` | `#/paths/~1api~1v1~1images~1{image_id}/get` · `get_image_api_v1_images__image_id__get` · `ImageDetailedResponse` | 公开 |
| `image_tags(image_id)` | `GET /api/v1/images/{image_id}/tags` | `…/images~1{image_id}~1tags/get` · `get_image_tags_api_v1_images__image_id__tags_get` · `ImageTagsResponse` | 公开 |
| `image_tag_history(image_id, **params)` | `GET /api/v1/images/{image_id}/tag-history` | `…/tag-history/get` · `get_image_tag_history_api_v1_images__image_id__tag_history_get` · `ImageTagHistoryListResponse` | 公开 |
| `image_status_history(image_id, **params)` | `GET /api/v1/images/{image_id}/status-history` | `…/status-history/get` · `get_image_status_history_api_v1_images__image_id__status_history_get` · `ImageStatusHistoryListResponse` | 公开（部分字段按身份隐藏） |
| `image_reposts(image_id)` | `GET /api/v1/images/{image_id}/reposts` | `…/reposts/get` · `get_image_reposts_api_v1_images__image_id__reposts_get` · `ImageRepostListResponse` | 公开（无分页） |
| `image_reviews(image_id, **params)` | `GET /api/v1/images/{image_id}/reviews` | `…/reviews/get` · `get_image_reviews_api_v1_images__image_id__reviews_get` · `ImageReviewListResponse` | 公开 |
| `image_favorites(image_id, **params)` | `GET /api/v1/images/{image_id}/favorites` | `…/favorites/get` · `get_image_favorites_api_v1_images__image_id__favorites_get` · `UserListResponse` | 公开 |
| `image_ratings(image_id, **params)` | `GET /api/v1/images/{image_id}/ratings` | `…/ratings/get` · `get_image_ratings_users_api_v1_images__image_id__ratings_get` · `ImageRatingsListResponse` | 公开 |
| `image_similar(image_id, **params)` | `GET /api/v1/images/{image_id}/similar` | `…/similar/get` · `get_similar_images_api_v1_images__image_id__similar_get` · `SimilarImagesResponse` | 公开（依赖站点 IQDB） |
| `image_by_hash(md5_hash)` | `GET /api/v1/images/search/by-hash/{md5_hash}` | `…/search~1by-hash~1{md5_hash}/get` · `search_by_hash_api_v1_images_search_by_hash__md5_hash__get` · `ImageHashSearchResponse` | 公开 |
| `image_stats()` | `GET /api/v1/images/stats/summary` | `…/stats~1summary/get` · `get_stats_api_v1_images_stats_summary_get` · `ImageStatsResponse` | 公开 |
| `image_import_sites()` | `GET /api/v1/images/import-sites` | `…/import-sites/get` · `list_import_sites_api_v1_images_import_sites_get` · `ImportSiteResponse` 数组 | 公开 |

`image_favorites` 与 `image_ratings` 都用 `users` 数组，但项类型不同：前者是 `UserResponse`，
后者是 `UserWithRatingResponse`，多出该用户给图的 `rating` 与 `rated_at`。

### 标签（6，全部公开）

| 方法 | 请求 | OpenAPI 依据 | 面 |
| :--- | :--- | :--- | :--- |
| `tag_list(**params)` | `GET /api/v1/tags` | `#/paths/~1api~1v1~1tags/get` · `list_tags_api_v1_tags_get` · `TagListResponse` | 公开 |
| `tag_show(tag_id)` | `GET /api/v1/tags/{tag_id}` | `…/tags~1{tag_id}/get` · `get_tag_api_v1_tags__tag_id__get` · `TagWithStats` | 公开 |
| `tag_images(tag_id, **params)` | `GET /api/v1/tags/{tag_id}/images` | `…/images/get` · `get_images_by_tag_api_v1_tags__tag_id__images_get` · `ImageListResponse` | 公开 |
| `tag_characters(tag_id, **params)` | `GET /api/v1/tags/{tag_id}/characters` | `…/characters/get` · `get_characters_for_source_api_v1_tags__tag_id__characters_get` · `TagListResponse` | 公开（非 Source 类型回 `400`） |
| `tag_history(tag_id, **params)` | `GET /api/v1/tags/{tag_id}/history` | `…/history/get` · `get_tag_history_api_v1_tags__tag_id__history_get` · `TagAuditLogListResponse` | 公开 |
| `tag_usage_history(tag_id, **params)` | `GET /api/v1/tags/{tag_id}/usage-history` | `…/usage-history/get` · `get_tag_usage_history_api_v1_tags__tag_id__usage_history_get` · `TagHistoryListResponse` | 公开 |

**两个图片列表 schema 不一样，这是本轮必须写清的一点**：

* `tag_images` 用 `ImageListResponse` → `ImageResponse`（基础图片数据），**没有 `tags` 数组**；
* `user_images` / `user_favorites` 用 `ImageDetailedListResponse` → `ImageDetailedResponse`（完整对象，含 `tags`）；
* 同理 `image_by_hash` 的 `images` 也是 `ImageResponse`。

### 搜索（1，公开）

| 方法 | 请求 | OpenAPI 依据 | 面 |
| :--- | :--- | :--- | :--- |
| `search(**params)` | `GET /api/v1/search` | `#/paths/~1api~1v1~1search/get` · `search_api_v1_search_get` · `SearchResponse` | 公开 |

`SearchResponse.entity` 是字符串；T 记录的匿名请求里它恒为 `"tags"`，`q` 之外的
`entity` / `query` / `search` / `term` 参数都不在 O 的参数表里。

### 用户（7：6 公开 + 1 私有）

| 方法 | 请求 | OpenAPI 依据 | 面 |
| :--- | :--- | :--- | :--- |
| `user_list(**params)` | `GET /api/v1/users` | `#/paths/~1api~1v1~1users/get` · `list_users_api_v1_users_get` · `UserListResponse` | 公开 |
| `user_show(user_id)` | `GET /api/v1/users/{user_id}` | `…/users~1{user_id}/get` · `get_user_api_v1_users__user_id__get` · `UserResponse` | 公开 |
| `user_images(user_id, **params)` | `GET /api/v1/users/{user_id}/images` | `…/images/get` · `get_user_images_api_v1_users__user_id__images_get` · `ImageDetailedListResponse` | 公开 |
| `user_favorites(user_id, **params)` | `GET /api/v1/users/{user_id}/favorites` | `…/favorites/get` · `get_user_favorites_api_v1_users__user_id__favorites_get` · `ImageDetailedListResponse` | 公开 |
| `user_favorite_tags(user_id)` | `GET /api/v1/users/{user_id}/favorite-tags` | `…/favorite-tags/get` · `get_user_favorite_tags_api_v1_users__user_id__favorite_tags_get` · `UserFavoriteTagsResponse` | 公开 |
| `user_ratings(user_id, **params)` | `GET /api/v1/users/{user_id}/ratings` | `…/ratings/get` · `get_user_ratings_api_v1_users__user_id__ratings_get` · `UserRatingsListResponse` | **私有** |
| `user_history(user_id, **params)` | `GET /api/v1/users/{user_id}/history` | `…/history/get` · `get_user_history_api_v1_users__user_id__history_get` · `UserHistoryListResponse` | 公开（只含公开状态） |

`user_ratings` 的 O 描述原文是 “**Private:** visible only to the user themselves and to moderators holding
`USER_EDIT_PROFILE`”，并且同一段说明里提醒 `min_rating` / `max_rating` 过滤的是**该用户自己给的分**，
与 `/images?min_rating=` 过滤**图片平均分**不是一回事。

### 评论（5，全部公开）

| 方法 | 请求 | OpenAPI 依据 | 面 |
| :--- | :--- | :--- | :--- |
| `comment_list(**params)` | `GET /api/v1/comments` | `#/paths/~1api~1v1~1comments/get` · `list_comments_api_v1_comments_get` · `CommentListResponse` | 公开 |
| `comment_show(comment_id)` | `GET /api/v1/comments/{comment_id}` | `…/comments~1{comment_id}/get` · `get_comment_api_v1_comments__comment_id__get` · `CommentResponse` | 公开 |
| `comment_image(image_id, **params)` | `GET /api/v1/comments/image/{image_id}` | `…/comments~1image~1{image_id}/get` · `get_image_comments_api_v1_comments_image__image_id__get` · `CommentListResponse` | 公开 |
| `comment_user(user_id, **params)` | `GET /api/v1/comments/user/{user_id}` | `…/comments~1user~1{user_id}/get` · `get_user_comments_api_v1_comments_user__user_id__get` · `CommentListResponse` | 公开 |
| `comment_stats()` | `GET /api/v1/comments/stats/summary` | `…/comments~1stats~1summary/get` · `get_comment_stats_api_v1_comments_stats_summary_get` · `CommentStatsResponse` | 公开 |

### 新闻与站点信息（4，全部公开）

| 方法 | 请求 | OpenAPI 依据 | 面 |
| :--- | :--- | :--- | :--- |
| `news_list(**params)` | `GET /api/v1/news` | `#/paths/~1api~1v1~1news/get` · `list_news_api_v1_news_get` · `NewsListResponse` | 公开 |
| `news_show(news_id)` | `GET /api/v1/news/{news_id}` | `…/news~1{news_id}/get` · `get_news_api_v1_news__news_id__get` · `NewsResponse` | 公开 |
| `meta_config()` | `GET /api/v1/meta/config` | `#/paths/~1api~1v1~1meta~1config/get` · `get_public_config_api_v1_meta_config_get` · `PublicConfig` | 公开 |
| `permission_list()` | `GET /api/v1/permissions` | `#/paths/~1api~1v1~1permissions/get` · `list_permission_names_api_v1_permissions_get` · 内联对象（权限名 → 字符串值） | 公开 |

### 认证（5，全部需要显式调用）

| 方法 | 请求 | OpenAPI 依据 | 面 |
| :--- | :--- | :--- | :--- |
| `auth_login(username=None, password=None)` | `POST /api/v1/auth/login` | `#/paths/~1api~1v1~1auth~1login/post` · `login_api_v1_auth_login_post` · 请求体 `LoginRequest`（`username` 3–30、`password` 1–255）→ `TokenResponse` | 认证 |
| `auth_refresh()` | `POST /api/v1/auth/refresh` | `…/auth~1refresh/post` · `refresh_token_api_v1_auth_refresh_post` · `TokenResponse` | 认证 |
| `auth_me()` | `GET /api/v1/auth/me` | `…/auth~1me/get` · `get_current_user_info_api_v1_auth_me_get` · 200 是**无类型对象** | 认证 |
| `auth_logout()` | `POST /api/v1/auth/logout` | `…/auth~1logout/post` · `logout_api_v1_auth_logout_post` · `MessageResponse` | 认证 |
| `auth_logout_all()` | `POST /api/v1/auth/logout-all` | `…/auth~1logout-all/post` · `logout_all_devices_api_v1_auth_logout_all_post` · `MessageResponse` | 认证 |

`auth_me` 的 200 在 O 里是 `{"type": "object", "additionalProperties": true}`（标题
`Response Get Current User Info Api V1 Auth Me Get`），**没有绑定 `UserPrivateResponse`**。
T 说它返回当前用户资料并列出字段，但 O 没有承诺这些键，所以客户端原样返回、文档不把它们写死。

`TokenResponse` 的字段是 `access_token`（必填）、`token_type`（默认 `"bearer"`）、
`expires_in`（必填，秒）、`user`（**可以为 `null`**，O 里是
`anyOf: [UserPrivateResponse, null]`），且不在必填字段表中；不能据此承诺每次都带完整用户资料。

## 关键参数的官方默认值与范围

| 参数 | 出现在 | 取值 / 默认（O） | 说明 |
| :--- | :--- | :--- | :--- |
| `page` | 声明 page/per_page 的列表 | `integer`，最小 1，默认 1 | 页码从 1 开始，reposts等非分页对象不适用 |
| `per_page` | 声明 page/per_page 的列表 | `integer`，最小 1，**最大 100**，默认 20 | 超上限由服务端回 `422`；客户端不钳位 |
| `sort_order` | 所有可排序列表 | 枚举 `ASC` / `DESC`，默认 `DESC` | — |
| `sort_by`（图片） | `image_list`、`tag_images`、`user_images`、`user_favorites` | `$ref: ImageSortBy`，**默认 `image_id`**（默认值写在 `$ref` 旁边，解引用时不能丢） | `ImageSortBy` 枚举：`image_id`、`date_added`、`last_post`、`total_pixels`、`bayesian_rating`、`favorites` |
| `sort_by`（用户） | `user_list`、`image_favorites` | 内联枚举，默认 `user_id` | `user_id`、`username`、`date_joined`、`last_login`、`last_active`、`image_posts`、`posts`、`favorites` |
| `sort_by`（图片评分者） | `image_ratings` | 内联枚举，默认 `rating` | `rating`、`date`、`user_id`、`username`、`date_joined` |
| `sort_by`（评论） | `comment_list` | 内联枚举，默认 `date` | `post_id`、`date`、`update_count` |
| `sort_by`（标签搜索） | `search` | 内联枚举，**可省略** | 省略时按相关度排序；给了就是 `usage_count`、`title`、`date_added`、`tag_id`、`type` |
| `sort_by`（用户评分记录） | `user_ratings` | `image_id` / `rating` / `rated_at`，默认 `image_id` | 私有接口 |
| `tag_depth` | `image_list`、`tag_images` | `integer` 0–9，可空 | 0=只匹配该标签；**省略=整棵层级**（O 描述：`Omit for full hierarchy`） |
| `threshold` | `image_similar` | `number` 0–100，可空 | 最低相似度 |
| `min_rating` / `max_rating` | `image_list`（1–10）、`user_ratings`（1–10） | 含边界 1 与 10 | 前者过滤图片平均分，后者过滤该用户自己给的分 |
| `status` | `image_list` | **数组**，重复键传多个 | O 描述只给了 `1=active, 2=spoiler, etc`；完整映射（`-4` Review、`-2` Inappropriate、`-1` Repost、`0` Other、`1` Active、`2` Spoiler）来自 T，未逐个实测 |
| `q` | `search` | 字符串，默认 `""` | **不是必填**：空串表示列全部，过滤与排序照旧生效 |
| `limit` / `offset` | `search` | 1–100 / 0–500000，默认 20 / 0 | 与列表的 `page`/`per_page` 是两套 |
| `aliases` | `search` | 枚举 `hide` / `only` / `all`，默认 `all` | — |
| `include_comments` | `image_list` | 布尔，默认 `false` | `true` 时响应里的 `comments` 是 `{image_id: [CommentResponse]}`；默认 `null` |
| `tags` / `exclude_tags` / `ids` / `image_ids` / `exclude_user_id` 等 | 多个列表 | 字符串（逗号串） | 发送时必须自己拼逗号串；T 记录 `tags=1+2` 会被当非法值并静默丢过滤 |
| `access_token` | 几乎所有操作 | Cookie 参数，可选 | 见下节：它的存在不代表该接口需要登录 |

## 权限与访问面

* **公开资源读**：13 个图片方法、6 个标签方法、`search`、6 个用户方法（不含 `user_ratings`）、
  5 个评论方法及4个站点方法；匿名执行只覆盖 L 列出的10个，状态历史等路径尚待实际响应证明。
* **私有读**＝`user_ratings`：O 描述原文 “Private: visible only to the user themselves and to moderators
  holding `USER_EDIT_PROFILE`”。
* **认证**＝5 个 `auth_*` 方法：登录本身匿名可调，`auth_me` / `auth_logout_all` 需要令牌，
  `auth_refresh` / `auth_logout` 靠 Cookie 里的 refresh token。
* **不属于本库的私有/管理读**：`/users/me`、`/users/me/warnings`、`/users/me/taste-profile`、
  `/images/recommended`、`/images/bookmark/me`、`/images/bookmark/page`、`/images/{id}/reports`、
  `/privmsgs/*`、`/ml-*`、`/admin/*`。

### 为什么不能只看 OpenAPI 的 `security` 字段判断“要不要登录”

O 在**绝大多数操作**上都写了同一段：

```json
"security": [{"HTTPBearer": []}]
```

这包括实测匿名可用的 `GET /api/v1/images`（副本 4217–4220 行）。同时 O 几乎给每个操作都加了一个
可选的 Cookie 参数 `access_token`，而 `refresh_token` Cookie 只出现在 `/auth/refresh` 与 `/auth/logout`。
也就是说：

* O 把 Bearer 写成了 security requirement，但真实部署的部分路由仍允许匿名，声明不能代替权限实测；
* 可选 `access_token` Cookie 的存在同样不能证明该路由必须登录。

因此本库对访问面的判定用的是 **O 的接口描述文本 + T 的匿名记录 + L 的真实响应**，
而不是 `security` 字段。匿名请求受保护接口会得到 `401`、响应头带 `www-authenticate: Bearer`（T 记录）。

## T 与 O 的差异与需要纠正的说法

| 项目 | T 的说法 / 既有写法 | 处理 |
| :--- | :--- | :--- |
| 读接口是否都能匿名 | “所有读接口都已实测匿名可用” | **纠正**：`user_ratings` 是私有读接口。全库口径是 **35 公开读 + 1 私有读 + 5 认证**，不能写“所有 GET 都匿名” |
| `auth_me` 的返回 | 返回 `UserPrivateResponse` 并列出字段 | O 的 200 是**无类型对象**；文档改为“当前用户资料对象，O 未给字段表”，客户端原样返回 |
| 登录返回的用户资料 | 登录/刷新一并返回 | O 的 `TokenResponse.user` 是 `anyOf: [UserPrivateResponse, null]`，**可以为 `null`**；不把“一定带资料”写成保证 |
| `tag_images` 的图片对象 | 与用户图片一样列了 `tags` 等字段 | O 里它是 `ImageListResponse` → `ImageResponse`（基础数据），**没有 `tags` 数组**；文档按 schema 分开写 |
| `/tags` 的 `limit` | 社区客户端常用 `?search=cat&limit=10` | O 的参数表**没有 `limit`**；T 实测传了仍返回 20 条。客户端只提供 `per_page`，也不做本地裁剪 |
| `/api/v1/search` 的定位 | “这个接口搜的是标签，不是图片” | 与 O 一致（`SearchResponse.entity`；参数表里没有图片搜索参数）。文档直接写成**标签搜索** |
| `tags=1+2` | T 记录：过滤被静默丢弃，返回全库 | 客户端**不做分隔符转换**，只发调用者给的字符串；文档把它列为常见坑 |
| `per_page` 上限 | T 记录 `per_page=200` → `422 Input should be less than or equal to 100` | 与 O 的 `maximum: 100` 一致；文档写上限 100，客户端不钳位 |
| `status` 多值 | 重复 `status=1&status=2` | 与 O 的数组参数一致；客户端把序列发成重复键，**不写 `status[]`** |
| 随机图与媒体路由 | `GET /api/v1/images/random` 与 `/images/{filename}`、`/thumbs/*` 都是 `302` | 非 JSON，客户端不封装、不解码；要取图用响应里的 `url` / `thumbnail_url` / `medium_url` / `large_url` |
| 限流 | 站点由 Cloudflare 前置，200/401 响应都不带 `X-RateLimit-*` | 客户端不做节流、不做退避；`meta_config()` 里的 `search_delay_seconds` / `upload_delay_seconds` 只是站点公布的冷却值，是否强制未验证 |
| 旧接口 | 旧 PHP 路由（`/index.php`、`/random.php`、`/search/process/` 等）已 404 | 与 O 的 `/api/v1` 结构一致；文档不提旧路径作为可用入口 |

## 客户端取舍

1. **路径由调用者给全**：`request(method, path, ...)` 收的是含 `api/v1` 的站点相对路径，
   客户端不加版本号、不猜资源名、不补 `.json`。
2. **35 + 1 + 5 全部保留**：私有方法与认证方法都留在实现里，文档写清权限要求，
   不因为“没有凭据”就删掉接口，也不伪造成匿名可用。
3. **JSON 原样交付**：不拆 `total` / `page` / `per_page` 外层，不把 `images`、`users`、`items`
   映射成统一模型，不裁剪字段，不拼 CDN 地址（响应里已经给了 `url`、`thumbnail_url`、
   `medium_url`、`large_url`）。
4. **认证显式**：只有非空 `access_token` 才加 `Authorization: Bearer`；配置里的
   `username` / `password` 只在显式调用 `auth_login()` 时使用；不自动登录、不自动续期、不后台刷新。
5. **只有 JSON**：Atom 订阅源、媒体路由、`302` 随机图都不封装；`request()` 拿到非 JSON 响应会抛
   `AnybooruAPIError`，不会把字节或 HTML 当数据返回。
6. **参数不猜**：不设默认值、不钳位 `per_page`、不转换逗号串、不纠正 `+` 分隔符、不重试、不回退。

## 排除项（有真实路由，只是不在本库内）

逐类清单（含路径示例）见[能力入口的排除表](shuushuu-capabilities.md#本库不封装的能力)。

| 类别 | 代表路径（O 指针前缀） | 排除原因 |
| :--- | :--- | :--- |
| 写动作 | `#/paths/~1api~1v1~1images~1upload/post`、`…~1images~1{image_id}/patch`、`…~1images~1{image_id}~1rating/post`、`…~1comments/post`、`…~1tags/post`、`…~1tags~1batch/post` | 需要登录，且会改站点数据 |
| 个人面读 | `#/paths/~1api~1v1~1users~1me/get`、`…~1users~1me~1warnings/get`、`…~1users~1me~1taste-profile/get`、`…~1images~1recommended/get`、`…~1images~1bookmark~1me/get` | 需要登录，是个人资料/推荐/书签 |
| 举报与审核 | `…~1images~1{image_id}~1reports/get`、`#/paths/~1api~1v1~1admin~1reports*/get`、`…~1admin~1reviews*/get` | 需要 `report_view` 或管理权限 |
| 机器学习建议 | `…~1ml-tag-suggestions~1analyze/post`、`…~1ml-suggestions*/get`、`…~1images~1{image_id}~1ml-tag-suggestions/get`、`…~1tags~1suggestion-stats/get` | 权限相关，属审核流程 |
| 私信 | `#/paths/~1api~1v1~1privmsgs*` | 需要登录且是私人内容 |
| 站点展示/维护 | `#/paths/~1api~1v1~1banners~1/get`、`…~1banners~1preferences/get`、`…~1donations/get`、`…~1character-source-links/post` | 与图片浏览无关 |
| 重复的收藏入口 | `…~1favorites~1user~1{user_id}/get`、`…~1favorites~1image~1{image_id}/get` | O 里这一组标着 `favorites (deprecated)`；等价数据由 `user_favorites` / `image_favorites` 提供 |
| 非 JSON 路由 | `#/paths/~1api~1v1~1images.atom/get`、`…~1tags~1{tag_id}~1images.atom/get`、`…~1images~1random/get`、`#/paths/~1images~1{filename}/get`、`…~1thumbs~1{filename}/get` | Atom、`302` 跳转或二进制，客户端不解码 |
| 管理面 | `#/paths/~1api~1v1~1admin/*` | 需要管理员权限 |

## 边界与未实测

* **L 只覆盖 10 个公开读方法**：`search`、`tag_list`、`image_list`、`image_show`、`tag_show`、
  `comment_list`、`image_stats`、`meta_config`、`user_list`、`news_list`。其余 **25 个公开读方法**
  （含 4 个图片子资源历史、相似图、按 hash 查重、标签历史/角色、评论的按图与按用户入口等）
  没有本库本轮真实样本；T 的既有观察仍单独保留，不升级为 L。命令与 URL 见
  [验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。
* **5 个认证方法一次都没执行**：登录、续期、`auth_me`、登出、全部登出；T 描述的
  “5 次失败锁 15 分钟”“refresh token 10 秒并发宽限”“盗用整族吊销”等规则都没有实测。
* **`user_ratings` 没有实测**：没有可用凭据，私有可见性只有 O 描述。
* **全部内容写接口、个人面、举报审核、ML 建议、私信、管理面都没有实测**，也没有原生方法；通用JSON请求入口仍可显式调用。
* **按身份变化的字段没有逐条实测**：`image_status_history` 的说明写了按查看者隐藏原因/操作者，
  匿名响应与登录响应可能不同；本轮连它的匿名成功形态也未调用验证。
* **返回结构只按 schema 对齐**：`include_comments=true` 时的 `comments` 映射内容、
  `image_similar` 有结果时的 `similar_images` 取值、`user_history` 各个 `type` 的字段差异，
  都还没有本轮真实样本；L 只发送了 `include_comments=false`，输出没有另存响应的 `comments` 键。
* **`status` 的完整取值映射来自 T**（O 只写 `1=active`、`2=spoiler` 与 “etc”），未逐个实测。
* **媒体路由带登录态的行为未验证**：匿名请求受保护图片路由会 `302`，跳转目标与是否有
  `X-Accel-Redirect` 没有进一步验证。

继续阅读：[客户端用法](shuushuu.md) · [方法参考](shuushuu-api.md) ·
[能力入口](shuushuu-capabilities.md) · [验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。
