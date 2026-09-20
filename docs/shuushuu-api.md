# Shuushuu 方法参考

REST 接口指用固定网址加 HTTP 动词读写数据的服务。e-shuushuu.net 自称 **Shuushuu API 2.0.0**，全部端点挂在 `https://e-shuushuu.net/api/v1` 前缀下。本页列出 `Shuushuu` 的全部原生方法：**35 个公共资源 `GET` + 1 个私有 `GET`（`user_ratings`）+ 5 个显式认证方法**，共 41 个。客户端怎么构造、`request()` 与 `last_call` 见[客户端用法](shuushuu.md)；站点能力与排除项见[能力入口](shuushuu-capabilities.md)。

## 依据标注与阅读方式

每条事实都标来源，四类互不混淆：

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **O** | 站点自带的机器可读契约 `https://e-shuushuu.net/api/openapi.json`（交互式文档 `https://e-shuushuu.net/api/docs`） | 端点、参数名、类型、范围、默认值、响应 schema 名 |
| **T** | 既有匿名只读记录（未登录、无 token，访问 `https://e-shuushuu.net`） | 某些路由确实匿名返回过 `200`；具体条数与字段只在那次记录内成立 |
| **L** | 本库本次真实执行，集中在[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19) | 冒烟10次（8×200、预期422与404），两个示例合计8×200；仅证明记录里的参数组合 |
| **[未实测]** | 只有 O/T 依据、没有本库执行记录 | 参数表与字段仍可用，但成功/失败分支未经验证 |

不是“所有 GET 都匿名”。41 个方法里只有 35 个 `GET` 是公开读取面；`user_ratings` 是私有数据（只有本人与持 `USER_EDIT_PROFILE` 的版主可读）；5 个认证方法只有显式调用才动作，`auth_login` 本身不要求已有 token。个人与管理员读路径（`/users/me*`、`/privmsgs/*`、`/images/recommended`、`/images/bookmark/*`、`/admin/*`）不属于本库原生方法，见[能力入口](shuushuu-capabilities.md)。

## 全页通用约定

* **基地址**：`https://e-shuushuu.net`；本页所有路由都补在它之后。
* **认证**：原生只读方法默认匿名。显式配置非空 `access_token` 时客户端带 `Authorization: Bearer <access_token>`；`username` / `password` 只在显式调用 `auth_login()` 时使用，不会自动登录。
* **分页（列表信封）**：`page` 从 **1** 开始，`per_page` 默认 **20**、最大 **100**（O）。列表响应固定是 `{"total": 总数, "page": 当前页, "per_page": 每页数, "<资源名>": [...]}`：图片用 `images`、标签用 `tags`、评论用 `comments`、用户用 `users`、新闻用 `news`。例外：`/api/v1/search` 用 `limit`（默认 20，1–100）+ `offset`（默认 0，0–500000），返回 `query` / `entity` / `hits` / `total` / `limit` / `offset`。
* **逗号串参数**：`tags`、`ids`、`exclude_tags`、`image_ids` 收英文逗号分隔的字符串（如 `'46,169'`），不是数组。`status` 是唯一的数组参数，重复传（`status=1&status=2`）表示多选。
* **标签必须用数字 ID**：筛图参数只认 `tag_id`。要按名字找图，先用 `search(q='long hair')` 或 `tag_list(search='long hair')` 查到 `tag_id`，再拼成 `tags='46,169'`。
* **布尔与日期**：布尔收 `true` / `false`；日期收 `YYYY-MM-DD`；时间字段是 ISO 8601 UTC（一种带时区的标准时间写法）。
* **排序**：`sort_order` 只有 `ASC`（升序）/ `DESC`（降序），多数接口默认 `DESC`；`sort_by` 的可选值按接口不同，见各方法表。
* **错误**：未登录 `401`；查不到 `404 {"detail": "..."}`；参数非法 `422`，正文是 FastAPI 的 `{"detail": [{"type", "loc", "msg", "ctx"}, ...]}`。业务错误同样走 `detail` 字段，见[错误处理](errors.md)。
* **三处最容易踩**：`tags` 必须用逗号（用 `+` 连接会被当成非法值、过滤被静默丢弃）；`/api/v1/search` 搜的是标签不是图片；`/api/v1/tags` 没有 `limit` 参数（只有 `per_page`）。

## 图片（13 个方法）

图片在站点里叫 image，编号是 `image_id`。

### image_list

签名：`image_list(**params)`。路由 `GET /api/v1/images`。

给筛选条件，返回 `ImageDetailedListResponse`：`total`、`page`、`per_page`、`images`（`ImageDetailedResponse` 数组）。传 `include_comments=true` 时另带 `comments`（按图片编号分组的评论映射，否则为 `null`）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | `str`，逗号分隔的 tag ID | 按标签筛图，例如 `'1,2,3'` | 不过滤 | `tags='46,169'` |
| `tags_mode` | `'any'` / `'all'` | 命中任一标签 / 必须同时含全部标签 | O 默认 `any` | `tags='46,169', tags_mode='all'` |
| `exclude_tags` | `str`，逗号分隔的 tag ID | 排除含这些标签的图 | 不排除 | `exclude_tags='1'` |
| `exclude_descendants` | `bool` | `true` 时连被排除标签的子标签一起排除 | O 默认 `false`（只排除标签本身） | `exclude_tags='1', exclude_descendants=True` |
| `tag_depth` | `int` 0–9 | 向下包含几层子标签：`0` 只匹配该标签、`1` 加直接子标签……`9` 九层 | 不传 = 整棵层级 | `tag_depth=0` |
| `missing_tag_types` | `str`，逗号分隔的类型 ID | 要求图片**缺少**这些类型：`1` Theme、`2` Source、`3` Artist、`4` Character | 不过滤 | `missing_tag_types='3'` |
| `missing_tag_types_mode` | `'any'` / `'all'` | 缺任一 / 必须全缺 | O 默认 `any` | `missing_tag_types='3,4', missing_tag_types_mode='all'` |
| `user_id` | `int` | 只取该用户上传的图 | 不过滤 | `user_id=5` |
| `favorited_by_user_id` | `int` | 只取被该用户收藏的图 | 不过滤 | `favorited_by_user_id=5` |
| `exclude_user_id` | `str`，逗号分隔的 user ID | 排除这些用户上传的图 | 不排除 | `exclude_user_id='5,6'` |
| `exclude_favorited_by_user_id` | `str`，逗号分隔的 user ID | 排除被这些任一用户收藏的图 | 不排除 | `exclude_favorited_by_user_id='5'` |
| `commenter` | `int` user ID | 只取该用户评论过的图 | 不过滤 | `commenter=10` |
| `exclude_commenter` | `str`，逗号分隔的 user ID | 排除这些用户评论过的图 | 不排除 | `exclude_commenter='10'` |
| `commentsearch` | `str` | 按评论正文筛图（对**单条评论**求值，不把一张图的所有评论合并求值） | 空串或纯空白不启用过滤；非空但没有任何可搜索内容（如 `'!!!'`）命中 0 张 | `commentsearch='happy birthday'` |
| `commentsearch_mode` | `'all_words'` / `'like'` / `'natural'` / `'boolean'` | `all_words`：每个词都要出现（不区分大小写的子串），支持 `"精确短语"` 与 `-排除词`；`like`：整串当一个子串（`%`、`_` 按字面）；`natural`、`boolean` 与 `all_words` 行为相同 | O 默认 `all_words` | `commentsearch='"happy birthday"', commentsearch_mode='all_words'` |
| `hascomments` | `bool` | `true` 只留有评论的图，`false` 只留无评论的图 | 不过滤 | `hascomments=False` |
| `date_from` / `date_to` | `str` `YYYY-MM-DD` | 上传日期起止（含当天） | 不限 | `date_from='2024-01-01'` |
| `min_width` / `max_width` / `min_height` / `max_height` | `int` ≥ 1 | 宽 / 高上下限（像素） | 不限 | `min_width=1920, min_height=1080` |
| `min_rating` | `number` 1–10 | 最低**平均**评分 | 不限 | `min_rating=4` |
| `min_favorites` | `int` ≥ 0 | 最少收藏数 | 不限 | `min_favorites=10` |
| `min_num_ratings` | `int` ≥ 0 | 最少评分人数 | 不限 | `min_num_ratings=5` |
| `status` | `int`，可重复：`-4` Review、`-2` Inappropriate、`-1` Repost、`0` Other、`1` Active、`2` Spoiler | 按状态过滤 | 按站点可见性 | `status=1` |
| `reported` | `bool` | 只取有未处理举报的图 | 不过滤；该参数需要 `report_view` 权限，其它人传了会被忽略 | `reported=True` |
| `include_comments` | `bool` | `true` 时把每张图的所有评论按图片编号归组放进响应的 `comments` | O 默认 `false`（`comments` 为 `null`） | `include_comments=True` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`image_id` / `date_added` / `last_post` / `total_pixels` / `bayesian_rating` / `favorites` | 排序字段 | O 默认 `image_id` | `sort_by='favorites'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    images = client.image_list(tags='46,169', tags_mode='all', tag_depth=0,
                               per_page=2, sort_by='favorites', sort_order='DESC')
    # GET https://e-shuushuu.net/api/v1/images?tags=46%2C169&tags_mode=all&tag_depth=0&per_page=2&sort_by=favorites&sort_order=DESC
    # 返回 {"total": ..., "page": 1, "per_page": 2, "images": [...]}；
    # images 每项含 image_id、filename、ext、md5_hash、width、height、rating、
    # favorites、user_id、date_added、tags、url、thumbnail_url、medium_url、large_url 等键。
    print(images['total'], images['per_page'])
    for image in images['images']:
        print(image['image_id'], image['rating'], image['favorites'], image['url'])
```

T 记录过同形状的匿名 `200`：`tags=46&per_page=2&sort_by=favorites&sort_order=DESC` 返回 `total=722908`，前两张 `image_id` 为 `186447`、`1101184`；`tags=1,2` 返回 `total=334211`；写成 `tags=1+2` 时过滤被静默丢弃、返回全库。条数会随时间变化，不要当固定值。

### image_show

签名：`image_show(image_id)`。路由 `GET /api/v1/images/{image_id}`。

给图片编号，返回单个 `ImageDetailedResponse`（没有 `total`/`page` 外层字典）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号，见页面 `/images/<id>` | 必填 | `image_show(1119196)` |

`ImageDetailedResponse` 的键：`image_id`、`filename`（形如 `2026-09-18-1119196`）、`ext`、`original_filename`、`md5_hash`、`filesize`、`width`、`height`、`caption`、`miscmeta`、`source_url`、`status`（`-4` Review / `-2` Inappropriate / `-1` Repost / `0` Other / `1` Active / `2` Spoiler）、`rating`（平均分）、`bayesian_rating`、`num_ratings`、`favorites`、`posts`（评论数）、`user_id`、`user`（`UserSummary`：`user_id`/`username`/`avatar`/`user_title`/`groups`…）、`date_added`、`locked`、`medium` / `large`（是否有该尺寸变体，1/0）、`replacement_id`、`r2_location`、`tags`（`TagSummary` 数组，含 `tag_id`/`title`/`type`/`usage_count`/`type_name`/`context_source_tag_id`）、`is_favorited`、`user_rating`（未登录为 `null`）、`prev_image_id` / `next_image_id`（列表接口里为 `null`）、`has_open_report`、`reason_category` / `status_reason`、`ml_suggestion_count`、`url`、`thumbnail_url`（恒为 WebP）、`medium_url` / `large_url`（没有该变体时为 `null`）。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    image = client.image_show(1119196)
    # GET https://e-shuushuu.net/api/v1/images/1119196
    # 返回单个图片字典（无 total/page 外层）；tags 是 TagSummary 数组。
    print(image['image_id'], image['filename'], image['width'], image['height'])
    print(image['url'], image['thumbnail_url'], image['medium_url'], image['large_url'])
    print([(tag['tag_id'], tag['title'], tag['type_name']) for tag in image['tags']])
```

编号不存在时返回 `404 {"detail": "Image not found"}`（T 记录：`image_show(999999999)`）。

### image_tags

签名：`image_tags(image_id)`。路由 `GET /api/v1/images/{image_id}/tags`。

给图片编号，返回 `ImageTagsResponse`：`{"image_id": ..., "tags": [{"tag_id": ..., "tag": ..., "type_id": ...}, ...]}`。这里的 `tag` 是标签名字符串，不是 `ImageDetailedResponse.tags` 里的 `TagSummary` 对象。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    result = client.image_tags(1119196)
    # GET https://e-shuushuu.net/api/v1/images/1119196/tags
    # 返回 {"image_id": 1119196, "tags": [{"tag_id": ..., "tag": "...", "type_id": ...}]}
    print(result['image_id'], [(tag['tag_id'], tag['tag'], tag['type_id']) for tag in result['tags']])
```

### image_tag_history

签名：`image_tag_history(image_id, **params)`。路由 `GET /api/v1/images/{image_id}/tag-history`。

给图片编号，返回 `ImageTagHistoryListResponse`（分页信封）。内容是标签增删流水（最近在前），上传时就写入 `tag_links` 的“添加”事件也会出现在这里。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号 | 必填 | `image_tag_history(1119196)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    history = client.image_tag_history(1119196, per_page=2)
    # GET https://e-shuushuu.net/api/v1/images/1119196/tag-history?per_page=2
    # 返回 {"total": ..., "page": 1, "per_page": 2, "items": [...]}；
    # 每条是标签增删事件，含 tag_history_id、image_id、tag_id、action、user、date、tag。
    print(history['total'], history['per_page'])
```

### image_status_history

签名：`image_status_history(image_id, **params)`。路由 `GET /api/v1/images/{image_id}/status-history`。

给图片编号，返回 `ImageStatusHistoryListResponse`（分页信封）。O 说明：用户信息只在公开状态变更（repost / spoiler / active）里出现；自由文本原因只对公开变更或图片所有者 / 版主可见，`reason_category` 始终可见。**匿名下这些遮罩具体如何生效没有匿名样本，未验证**（见文末边界表）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号 | 必填 | `image_status_history(1119196)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    history = client.image_status_history(1119196, per_page=2)
    # GET https://e-shuushuu.net/api/v1/images/1119196/status-history?per_page=2
    # 返回分页信封（total/page/per_page 与条目数组）；状态值含义见 image_list 的 status。
    print(history['total'], history['page'])
```

### image_reposts

签名：`image_reposts(image_id)`。路由 `GET /api/v1/images/{image_id}/reposts`。

给原图编号，返回 `ImageRepostListResponse`：正文是 `{"total": 总数, "items": [...]}`、**没有** `page`/`per_page`，每条是 `{"image_id", "user", "marked_at"}`（`user` 是标记人，可为 `null`）。O 明确说明该端点不分页，数据来自图片行上的 `replacement_id`，只返回仍处于 repost 状态的记录。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 原图编号 | 必填 | `image_reposts(1119196)` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    reposts = client.image_reposts(1119196)
    # GET https://e-shuushuu.net/api/v1/images/1119196/reposts
    # 返回不分页的结果对象；条目是当前仍标记为转载的图片（replacement_id 指向本图）。
    print(reposts)
```

### image_reviews

签名：`image_reviews(image_id, **params)`。路由 `GET /api/v1/images/{image_id}/reviews`。

给图片编号，返回 `ImageReviewListResponse`（分页信封）。O 说明只返回**已结束**的审核会话，内部字段（发起人、投票明细）出于隐私不返回。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号 | 必填 | `image_reviews(1119196)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    reviews = client.image_reviews(1119196, per_page=2)
    # GET https://e-shuushuu.net/api/v1/images/1119196/reviews?per_page=2
    # 返回分页信封；每条是已结束的审核会话（不含发起人与投票明细）。
    print(reviews['total'], reviews['per_page'])
```

### image_favorites

签名：`image_favorites(image_id, **params)`。路由 `GET /api/v1/images/{image_id}/favorites`。

给图片编号，返回 `UserListResponse`（分页信封，`users` 数组），即收藏了这张图的用户。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号 | 必填 | `image_favorites(1119196)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`user_id` / `username` / `date_joined` / `last_login` / `last_active` / `image_posts` / `posts` / `favorites` | 用户排序字段 | O 默认 `user_id` | `sort_by='username'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='ASC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    favorites = client.image_favorites(1119196, per_page=2, sort_by='username', sort_order='ASC')
    # GET https://e-shuushuu.net/api/v1/images/1119196/favorites?per_page=2&sort_by=username&sort_order=ASC
    # 返回 {"total": ..., "page": 1, "per_page": 2, "users": [...]}；每项是 UserResponse。
    for user in favorites['users']:
        print(user['user_id'], user['username'], user['avatar_url'])
```

### image_ratings

签名：`image_ratings(image_id, **params)`。路由 `GET /api/v1/images/{image_id}/ratings`。

给图片编号，返回 `ImageRatingsListResponse`（分页信封），即给这张图评过分的用户与分数。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号 | 必填 | `image_ratings(1119196)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`rating` / `date` / `user_id` / `username` / `date_joined` | 排序字段 | O 默认 `rating` | `sort_by='date'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    ratings = client.image_ratings(1119196, per_page=2, sort_by='date')
    # GET https://e-shuushuu.net/api/v1/images/1119196/ratings?per_page=2&sort_by=date
    # 返回分页信封；每条含评分者信息与分数（rating）。
    print(ratings['total'])
```

### image_similar

签名：`image_similar(image_id, **params)`。路由 `GET /api/v1/images/{image_id}/similar`。

给图片编号，返回 `SimilarImagesResponse`：`query_image_id`、`similar_images`（数组，按相似度从高到低，含 `similarity_score`），查询图自己不在结果里。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号 | 必填 | `image_similar(1119196)` |
| `threshold` | `number` 0–100 | 最低相似度 | 不限 | `threshold=80` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    similar = client.image_similar(1119196, threshold=80)
    # GET https://e-shuushuu.net/api/v1/images/1119196/similar?threshold=80
    # 返回 {"query_image_id": ..., "similar_images": [...]}；无相似图时数组为空。
    print(similar['query_image_id'], len(similar['similar_images']))
```

### image_by_hash

签名：`image_by_hash(md5_hash)`。路由 `GET /api/v1/images/search/by-hash/{md5_hash}`。

给文件 MD5（一种 32 位十六进制的文件指纹），返回 `ImageHashSearchResponse`：`md5_hash`、`found`（命中数）、`images`（命中的图片数组，每条是**基础**图片对象，没有嵌入的 `tags` 数组）。常用于判重 / 反查。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `md5_hash` | `str`，32 位 MD5 十六进制 | 文件 MD5，取自 `ImageDetailedResponse.md5_hash` | 必填 | `image_by_hash('de9c2f0aa6b358e3f041d2c933c31785')` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    result = client.image_by_hash('de9c2f0aa6b358e3f041d2c933c31785')
    # GET https://e-shuushuu.net/api/v1/images/search/by-hash/de9c2f0aa6b358e3f041d2c933c31785
    # 返回 {"md5_hash": ..., "found": 1, "images": [...]}（T 记录过 found=1）。
    print(result['md5_hash'], result['found'])
```

### image_stats

签名：`image_stats()`。路由 `GET /api/v1/images/stats/summary`。无参数。

返回 `ImageStatsResponse`：`total_images`、`total_favorites`、`average_rating`（全站口径）。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    stats = client.image_stats()
    # GET https://e-shuushuu.net/api/v1/images/stats/summary
    # 返回 {"total_images": ..., "total_favorites": ..., "average_rating": ...}
    # （T 记录：total_images=1102272、average_rating=3.76；数字会增长，不应当常量）。
    print(stats['total_images'], stats['total_favorites'], stats['average_rating'])
```

### image_import_sites

签名：`image_import_sites()`。路由 `GET /api/v1/images/import-sites`。无参数。

返回 `ImportSiteResponse` 数组，每项 `{"site": ..., "example_url": ...}`：URL 导入器接受的站点与示例地址。O 说明该列表公开且可缓存。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    sites = client.image_import_sites()
    # GET https://e-shuushuu.net/api/v1/images/import-sites
    # 返回数组，每项 {"site": "...", "example_url": "..."}
    print([(item['site'], item['example_url']) for item in sites])
```

## 标签（7 个方法）

### tag_list

签名：`tag_list(**params)`。路由 `GET /api/v1/tags`。

给筛选条件，返回 `TagListResponse`：`total`、`page`、`per_page`、`tags`（`TagResponse` 数组）、`invalid_ids`（`ids` 里非数字的项）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | `str` | 标签名搜索：**少于 3 个字符按前缀匹配**（`sa` 命中 `sakura kinomoto`）；**3 个字符及以上按词匹配**，每个词都要出现（不区分大小写的子串），且不要求词序（`sakura kinomoto` 能命中 `kinomoto sakura`） | 返回全部标签 | `search='long hair'` |
| `type` | `int`：`1` Theme / `2` Source / `3` Artist / `4` Character | 按标签类型过滤 | 不过滤 | `type=3` |
| `ids` | `str`，逗号分隔的 tag ID | 精确取若干标签；非数字项被跳过并列进 `invalid_ids` | 不过滤 | `ids='46,169'` |
| `parent_tag_id` | `int` | 取某个父标签的子标签 | 不过滤 | `parent_tag_id=46` |
| `exclude_aliases` | `bool` | 排除别名标签（只保留正式标签） | O 默认 `false` | `exclude_aliases=True` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`usage_count` / `title` / `date_added` / `tag_id` / `type` | 排序字段 | O 没有给默认值，不传时由服务端决定 | `sort_by='usage_count'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

`TagResponse` 的键：`tag_id`、`title`、`desc`、`type`（`0` All / `1` Theme / `2` Source / `3` Artist / `4` Character）、`date_added`、`usage_count`、`is_alias`、`alias_of`、`alias_of_name`、`alias_of_usage_count`。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    tags = client.tag_list(search='long hair', type=1, per_page=2, sort_by='usage_count')
    # GET https://e-shuushuu.net/api/v1/tags?search=long%20hair&type=1&per_page=2&sort_by=usage_count
    # 返回 {"total": ..., "page": 1, "per_page": 2, "tags": [...], "invalid_ids": ...}
    for tag in tags['tags']:
        print(tag['tag_id'], tag['title'], tag['type'], tag['usage_count'], tag['is_alias'])
```

T 记录过匿名 `200`：`?search=cat` 返回 `total=425`、`per_page=20`；`?search=cat&limit=3` 仍返回 20 条，说明 `limit` **不是**这个接口的参数（每页由 `per_page` 决定）。

### tag_show

签名：`tag_show(tag_id)`。路由 `GET /api/v1/tags/{tag_id}`。

给标签编号，返回 `TagWithStats`，在 `TagResponse` 的基础上多出：`total_image_count`（含子标签的图片总数）、`aliases`（指向本标签的别名）、`aliased_tag_id`、`parent_tag_id`、`child_count`、`created_by`（`UserSummary`）、`links`（外部链接）、`sources` / `characters`（角色与作品的关联标签）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | `int` | 标签编号，取自 `tag_list` / `search` 的返回 | 必填 | `tag_show(46)` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    tag = client.tag_show(46)
    # GET https://e-shuushuu.net/api/v1/tags/46
    # T 记录：total_image_count=722907，links/sources/characters 为空数组。
    print(tag['tag_id'], tag['title'], tag['type'], tag['total_image_count'])
    print(len(tag['aliases']), len(tag['links']), len(tag['sources']), len(tag['characters']))
```

### tag_images

签名：`tag_images(tag_id, **params)`。路由 `GET /api/v1/tags/{tag_id}/images`。

给标签编号，返回 `ImageListResponse`（**基础图片列表，不是** `ImageDetailedListResponse`：图片对象没有嵌入的 `tags` 数组，也没有 `is_favorited` / `user_rating` 与邻接的 `prev_image_id` / `next_image_id`；`url` / `thumbnail_url` / `medium_url` / `large_url` 等地址字段仍在）。O 说明该入口会自动跟随别名与子标签层级（查 `dress` 会带上 `sundress` 等子标签的图）；要按多个标签组合筛图请用 `image_list`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | `int` | 标签编号 | 必填 | `tag_images(46)` |
| `tag_depth` | `int` 0–9 | 向下包含几层子标签 | 不传 = 整棵层级 | `tag_depth=1` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`image_id` / `date_added` / `last_post` / `total_pixels` / `bayesian_rating` / `favorites` | 排序字段 | O 默认 `image_id` | `sort_by='favorites'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    listing = client.tag_images(46, tag_depth=0, per_page=2, sort_by='favorites')
    # GET https://e-shuushuu.net/api/v1/tags/46/images?tag_depth=0&per_page=2&sort_by=favorites
    # 返回 {"total": ..., "page": 1, "per_page": 2, "images": [...]}；
    # images 是基础图片对象（字段比 image_show 的详细结构少）。
    print(listing['total'])
```

T 记录：`/tags/46/images?per_page=1` 与 `/images?tags=46` 的 `total` **不一致**（前者 `729779`、后者 `722908`；`/tags/46` 的 `total_image_count` 又是 `722907`），说明三个入口的统计口径不同；要“这个标签共有多少图”就取你实际调用的那个接口的 `total`。

### tag_characters

签名：`tag_characters(tag_id, **params)`。路由 `GET /api/v1/tags/{tag_id}/characters`。

给 **Source** 标签编号，返回 `TagListResponse`：该 Source 关联的全部角色标签。O 说明：目标不是 Source 类型返回 `400`，标签不存在返回 `404`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | `int` | Source 类标签编号（先 `tag_show` 看 `type` 是否为 `2`） | 必填 | `tag_characters(6209)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    characters = client.tag_characters(6209, per_page=2)
    # GET https://e-shuushuu.net/api/v1/tags/6209/characters?per_page=2
    # 返回 {"total": ..., "page": 1, "per_page": 2, "tags": [...], "invalid_ids": ...}
    print(characters['total'], [tag['title'] for tag in characters['tags']])
```

### tag_history

签名：`tag_history(tag_id, **params)`。路由 `GET /api/v1/tags/{tag_id}/history`。

给标签编号，返回 `TagAuditLogListResponse`（分页信封）。内容是标签元数据变更：改名、改类型、改说明、改别名、改继承、角色-来源关联。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | `int` | 标签编号 | 必填 | `tag_history(46)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    history = client.tag_history(46, per_page=2)
    # GET https://e-shuushuu.net/api/v1/tags/46/history?per_page=2
    # 返回分页信封；每条是一次元数据变更（改名前后的标题、变更人、时间等）。
    print(history['total'], history['per_page'])
```

### tag_usage_history

签名：`tag_usage_history(tag_id, **params)`。路由 `GET /api/v1/tags/{tag_id}/usage-history`。

给标签编号，返回 `TagHistoryListResponse`（分页信封）。内容是标签在图片上的增删流水（最近在前），O 说明它把上传时的 `tag_links` 与编辑流的 `tag_history` 合并。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | `int` | 标签编号 | 必填 | `tag_usage_history(46)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    usage = client.tag_usage_history(46, per_page=2)
    # GET https://e-shuushuu.net/api/v1/tags/46/usage-history?per_page=2
    # 返回分页信封；每条是某张图加/删这个标签的事件。
    print(usage['total'], usage['per_page'])
```

### search

签名：`search(**params)`。路由 `GET /api/v1/search`。**搜标签，不搜图片**。

返回 `SearchResponse`：`query`（回显查询词）、`entity`（**恒为 `"tags"`**）、`hits`（`TagSearchHit` 数组，字段同 `TagResponse` 外加 `matched_identity`）、`total`、`limit`、`offset`。O 说明 `q` 不是必填：空串表示列全部，过滤与排序仍然生效；排序默认按相关度，给了 `sort_by` 就以排序字段为准。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `q` | `str` | 查询词（标签名） | O 默认空串（列全部） | `q='long hair'` |
| `type` | `int`：`1` Theme / `2` Source / `3` Artist / `4` Character | 按类型过滤 | 不过滤 | `type=3` |
| `aliases` | `'hide'` / `'only'` / `'all'` | 隐藏别名行 / 只看别名行 / 全部 | O 默认 `all` | `aliases='hide'` |
| `min_usage` / `max_usage` | `int` 0–2147483647 | 有效使用次数范围（别名取其正式标签的次数） | 不限 | `min_usage=1000` |
| `added_from` / `added_to` | `str` `YYYY-MM-DD` | 标签创建日期范围 | 不限 | `added_from='2024-01-01'` |
| `has_alias` | `'yes'` / `'no'` | 是否有别名指向它 | 不过滤 | `has_alias='yes'` |
| `is_child` | `'yes'` / `'no'` | 是否有父标签 | 不过滤 | `is_child='no'` |
| `has_children` | `'yes'` / `'no'` | 是否是某些标签的父标签 | 不过滤 | `has_children='yes'` |
| `source_linked` | `'yes'` / `'no'` | 角色有来源链接 / 来源有角色；需要 `type=2` 或 `type=4` 配合 | 不过滤 | `type=2, source_linked='yes'` |
| `limit` | `int` 1–100 | 返回条数 | O 默认 `20` | `limit=2` |
| `offset` | `int` 0–500000 | 跳过条数 | O 默认 `0` | `offset=20` |
| `sort_by` | `str`：`usage_count` / `title` / `date_added` / `tag_id` / `type` | 排序字段 | 不传 = 按相关度排序 | `sort_by='usage_count'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    hits = client.search(q='long hair', limit=2, sort_by='usage_count')
    # GET https://e-shuushuu.net/api/v1/search?q=long%20hair&limit=2&sort_by=usage_count
    # 返回 {"query": ..., "entity": "tags", "hits": [...], "total": ..., "limit": 2, "offset": 0}
    print(hits['query'], hits['entity'], hits['total'])
    print([(hit['tag_id'], hit['title']) for hit in hits['hits']])   # 拿到的 tag_id 用来筛图
```

T 记录：`?q=long hair` 返回 `entity="tags"`；`?entity=images&query=cat&q=cat` 里 `entity` / `query` **都不是这个接口的参数**，行为等同 `?q=cat`，返回的 `entity` 仍是 `"tags"`——本接口没有图片搜索模式。

## 用户（7 个方法）

### user_list

签名：`user_list(**params)`。路由 `GET /api/v1/users`。

给筛选条件，返回 `UserListResponse`（分页信封，`users` 数组）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | `str` | 用户名不分大小写的部分匹配 | 不过滤（列出全部用户） | `search='whitekitten'` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`user_id` / `username` / `date_joined` / `last_login` / `last_active` / `image_posts` / `posts` / `favorites` | 排序字段 | O 默认 `user_id` | `sort_by='username'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='ASC'` |

`UserResponse` 的键：`user_id`、`username`、`user_title`、`avatar`（空串表示没有）、`avatar_url`、`groups`（用户组名数组）、`admin`、`active`、`posts`、`image_posts`、`favorites`、`date_joined`、`last_login`、`last_active`、`location`、`website`、`interests`、`gender`、`maximgperday`。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    users = client.user_list(search='whitekitten', per_page=2, sort_by='username', sort_order='ASC')
    # GET https://e-shuushuu.net/api/v1/users?search=whitekitten&per_page=2&sort_by=username&sort_order=ASC
    # 返回 {"total": ..., "page": 1, "per_page": 2, "users": [...]}
    for user in users['users']:
        print(user['user_id'], user['username'], user['image_posts'], user['favorites'])
```

T 记录过匿名 `200`（`?per_page=1` 返回 `total=18109`）。

### user_show

签名：`user_show(user_id)`。路由 `GET /api/v1/users/{user_id}`。

给用户编号，返回单个 `UserResponse`。O 说明 `maximgperday`（每日上传上限）只对本人或持 `USER_EDIT_PROFILE` 的版主可见，其它查看者拿到的是 `null`（字段仍在）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `int` | 用户编号，取自 `user_list` 的返回 | 必填 | `user_show(846421)` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    user = client.user_show(846421)
    # GET https://e-shuushuu.net/api/v1/users/846421
    # 返回单个用户字典；maximgperday 只对本人/版主可见。
    print(user['user_id'], user['username'], user['groups'], user.get('maximgperday'))
```

### user_images

签名：`user_images(user_id, **params)`。路由 `GET /api/v1/users/{user_id}/images`。

给用户编号，返回 `ImageDetailedListResponse`（与 `image_list` 相同的详细图片结构）。要更复杂的过滤，改用 `image_list(user_id=...)`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `int` | 用户编号 | 必填 | `user_images(846421)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`image_id` / `date_added` / `last_post` / `total_pixels` / `bayesian_rating` / `favorites` | 排序字段 | O 默认 `image_id` | `sort_by='favorites'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    uploads = client.user_images(846421, per_page=2, sort_by='favorites')
    # GET https://e-shuushuu.net/api/v1/users/846421/images?per_page=2&sort_by=favorites
    # 返回 {"total": ..., "page": 1, "per_page": 2, "images": [...]}（详细图片结构）
    print(uploads['total'], [image['image_id'] for image in uploads['images']])
```

### user_favorites

签名：`user_favorites(user_id, **params)`。路由 `GET /api/v1/users/{user_id}/favorites`。

给用户编号，返回 `ImageDetailedListResponse`（详细图片结构）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `int` | 用户编号 | 必填 | `user_favorites(846421)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`image_id` / `date_added` / `last_post` / `total_pixels` / `bayesian_rating` / `favorites` | 排序字段 | O 默认 `image_id` | `sort_by='favorites'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    favorites = client.user_favorites(846421, per_page=2)
    # GET https://e-shuushuu.net/api/v1/users/846421/favorites?per_page=2
    # 返回与 user_images 相同形状的详细图片列表。
    print(favorites['total'])
```

### user_favorite_tags

签名：`user_favorite_tags(user_id)`。路由 `GET /api/v1/users/{user_id}/favorite-tags`。无参数。

给用户编号，返回 `UserFavoriteTagsResponse`：用户公开资料里的收藏分组与位置顺序；角色部分按「角色 + 来源」关联，带该关联设置的图片（图片仍公开时）与链接信息。O 说明这是**公开**资料。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `int` | 用户编号 | 必填 | `user_favorite_tags(846421)` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    favorite_tags = client.user_favorite_tags(846421)
    # GET https://e-shuushuu.net/api/v1/users/846421/favorite-tags
    # 返回按分组组织、带位置顺序的收藏；角色条目可能带 link 图片信息。
    print(list(favorite_tags))
```

### user_ratings

签名：`user_ratings(user_id, **params)`。路由 `GET /api/v1/users/{user_id}/ratings`。

给用户编号，返回 `UserRatingsListResponse`：`total/page/per_page/images`；每个 `images` 项是详细图片对象加 `subject_rating`（目标用户打的整数分）与 `rated_at`（评分时间，可为 `null`）。图片的 `rating` 仍是全体平均分，`user_rating` 是当前访问者的分，不要把这三个字段混用。

**这是本组唯一的私有读取接口（O 原文：Private — 只有该用户本人与持 `USER_EDIT_PROFILE` 的版主可读）**，所以匿名调用不属于“公开读取面”。`min_rating` / `max_rating` 过滤的是**该用户打出的分**，与 `image_list` 的 `min_rating`（图片平均分）含义不同。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `int` | 用户编号 | 必填 | `user_ratings(846421)` |
| `min_rating` / `max_rating` | `int` 1–10 | 该用户打出分数的范围 | 不限 | `min_rating=8` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `'image_id'` / `'rating'` / `'rated_at'` | 图片编号 / 目标用户评分 / 评分时间排序 | O 默认 `image_id` | `sort_by='rated_at'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu', config_file='my-anybooru.json') as client:
    # 自备配置已填 access_token，且账号就是846421或具有USER_EDIT_PROFILE；未实测。
    ratings = client.user_ratings(846421, min_rating=8, per_page=2)
    # GET https://e-shuushuu.net/api/v1/users/846421/ratings?min_rating=8&per_page=2
    # 本人或版主：返回该用户打过分数的图片列表；其他人不会拿到成功响应。
    print(ratings['total'])
```

### user_history

签名：`user_history(user_id, **params)`。路由 `GET /api/v1/users/{user_id}/history`。

给用户编号，返回 `UserHistoryListResponse`（分页信封）。O 说明它汇总三类来源：标签元数据变更（tag audit log）、图片上的标签增删（tag history + 上传时的 tag_links）、图片状态变更（只含公开状态 REPOST / SPOILER / ACTIVE；REVIEW、LOW_QUALITY、INAPPROPRIATE、OTHER 等隐藏状态不返回）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `int` | 用户编号 | 必填 | `user_history(846421)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    history = client.user_history(846421, per_page=2)
    # GET https://e-shuushuu.net/api/v1/users/846421/history?per_page=2
    # 返回分页信封；条目混合标签变更、标签增删与公开状态变更。
    print(history['total'], history['per_page'])
```

## 评论（5 个方法）

### comment_list

签名：`comment_list(**params)`。路由 `GET /api/v1/comments`。

给筛选条件，返回 `CommentListResponse`：`total`、`page`、`per_page`、`comments`（`CommentResponse` 数组）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 只看某张图的评论 | 不过滤 | `image_id=1118862` |
| `image_ids` | `str`，逗号分隔的图片编号 | 一次取多张图的评论，如 `'123,456,789'` | 不过滤 | `image_ids='1118862,1119196'` |
| `user_id` | `int` | 只看某个用户发的评论 | 不过滤 | `user_id=59006` |
| `search_text` | `str` | 评论正文搜索；与 `image_list.commentsearch` 同一套语义（`all_words` 下每个词都要出现，支持 `"精确短语"` 与 `-排除词`；空串不启用过滤） | 不过滤 | `search_text='happy birthday'` |
| `search_mode` | `'all_words'` / `'like'` / `'natural'` / `'boolean'` | 搜索模式；`like` 把整串当一个子串，`natural`、`boolean` 与 `all_words` 相同 | O 默认 `all_words` | `search_mode='like'` |
| `date_from` / `date_to` | `str` `YYYY-MM-DD` | 评论日期范围 | 不限 | `date_from='2024-01-01'` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`post_id` / `date` / `update_count` | 排序字段（`post_id` 就是评论编号） | O 默认 `date` | `sort_by='update_count'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

`CommentResponse` 的键：`post_id`（评论编号）、`image_id`、`user_id`、`user`（`UserSummary`）、`post_text`（原文，Markdown）、`post_text_html`（渲染后的 HTML）、`parent_comment_id`（回复关系，顶层为 `null`）、`deleted`、`date`、`update_count`、`last_updated`、`last_updated_user_id`。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    comments = client.comment_list(image_id=1118862, per_page=2, sort_by='date')
    # GET https://e-shuushuu.net/api/v1/comments?image_id=1118862&per_page=2&sort_by=date
    # 返回 {"total": ..., "page": 1, "per_page": 2, "comments": [...]}
    for comment in comments['comments']:
        print(comment['post_id'], comment['image_id'], comment['user_id'],
              comment['update_count'], len(comment['post_text']))
```

T 记录过匿名 `200`：`?per_page=1` 返回 `total=556038`，首条含 `post_text_html`；`?image_id=1118862` 返回该图评论。

### comment_show

签名：`comment_show(comment_id)`。路由 `GET /api/v1/comments/{comment_id}`。

给评论编号，返回单个 `CommentResponse`。`comment_id` 就是列表里的 `post_id`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `comment_id` | `int` | 评论编号（评论列表项里的 `post_id`） | 必填 | `comment_show(629189)` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    comment = client.comment_show(629189)
    # GET https://e-shuushuu.net/api/v1/comments/629189
    # 返回单个评论字典；post_text 是 Markdown 原文，post_text_html 是渲染结果。
    print(comment['post_id'], comment['image_id'], comment['deleted'])
```

### comment_image

签名：`comment_image(image_id, **params)`。路由 `GET /api/v1/comments/image/{image_id}`。

给图片编号，返回 `CommentListResponse`。O 说明它只是把列表接口的 `image_id` 过滤固定下来的便捷入口。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `image_id` | `int` | 图片编号 | 必填 | `comment_image(1118862)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`post_id` / `date` / `update_count` | 排序字段 | O 默认 `date` | `sort_by='date'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    comments = client.comment_image(1118862, per_page=2, sort_order='ASC')
    # GET https://e-shuushuu.net/api/v1/comments/image/1118862?per_page=2&sort_order=ASC
    # 返回 {"total": ..., "page": 1, "per_page": 2, "comments": [...]}
    print(comments['total'], [comment['post_id'] for comment in comments['comments']])
```

### comment_user

签名：`comment_user(user_id, **params)`。路由 `GET /api/v1/comments/user/{user_id}`。

给用户编号，返回 `CommentListResponse`：某个用户在所有图片下的评论。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `int` | 用户编号 | 必填 | `comment_user(59006)` |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=2` |
| `sort_by` | `str`：`post_id` / `date` / `update_count` | 排序字段 | O 默认 `date` | `sort_by='post_id'` |
| `sort_order` | `'ASC'` / `'DESC'` | 排序方向 | O 默认 `DESC` | `sort_order='DESC'` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    comments = client.comment_user(59006, per_page=2)
    # GET https://e-shuushuu.net/api/v1/comments/user/59006?per_page=2
    # 返回该用户的评论分页信封（comments 数组）。
    print(comments['total'], [comment['image_id'] for comment in comments['comments']])
```

### comment_stats

签名：`comment_stats()`。路由 `GET /api/v1/comments/stats/summary`。无参数。

返回 `CommentStatsResponse`：`total_comments`、`total_images_with_comments`、`average_comments_per_image`（在有评论的图片范围内求平均）。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    stats = client.comment_stats()
    # GET https://e-shuushuu.net/api/v1/comments/stats/summary
    # 返回 {"total_comments": ..., "total_images_with_comments": ..., "average_comments_per_image": ...}
    print(stats['total_comments'], stats['total_images_with_comments'], stats['average_comments_per_image'])
```

## 新闻与站点元信息（4 个方法）

### news_list

签名：`news_list(**params)`。路由 `GET /api/v1/news`。

返回 `NewsListResponse`（分页信封，`news` 数组），按新到旧。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `int` ≥ 1 | 页码 | O 默认 `1` | `page=2` |
| `per_page` | `int` 1–100 | 每页条数 | O 默认 `20` | `per_page=1` |

`NewsResponse` 的键：`title`、`news_text`、`date`、`edited`、`news_id`、`user_id`、`username`。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    news = client.news_list(per_page=1)
    # GET https://e-shuushuu.net/api/v1/news?per_page=1
    # 返回 {"total": ..., "page": 1, "per_page": 1, "news": [...]}
    for item in news['news']:
        print(item['news_id'], item['title'], item['date'], item['username'])
```

T 记录过匿名 `200`（`?per_page=1` 返回 `total=32`）。

### news_show

签名：`news_show(news_id)`。路由 `GET /api/v1/news/{news_id}`。

给新闻编号，返回单个 `NewsResponse`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `news_id` | `int` | 新闻编号，取自 `news_list` 的 `news_id` | 必填 | `news_show(32)` |

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    item = client.news_show(32)
    # GET https://e-shuushuu.net/api/v1/news/32
    # 返回单个新闻字典；news_text 是正文。
    print(item['news_id'], item['title'], len(item['news_text']))
```

### meta_config

签名：`meta_config()`。路由 `GET /api/v1/meta/config`。无参数。

返回 `PublicConfig`，站点公开配置与限制。T 记录到的键与值：`max_search_tags=5`、`max_search_users=5`、`max_image_size=33554432`、`max_avatar_size=1048576`、`upload_delay_seconds=30`、`search_delay_seconds=2`、`tag_types={"0": "All", "1": "Theme", "2": "Source", "3": "Artist", "4": "Character"}`、`ml_tag_suggestions_enabled=true`、`ml_character_suggestions_enabled=false`。写客户端时优先拉这个接口取站点限制，不要照抄页面文字。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    config = client.meta_config()
    # GET https://e-shuushuu.net/api/v1/meta/config
    # 返回公开配置：搜索标签/用户上限、上传与搜索冷却秒数、标签类型映射等。
    print(config['max_search_tags'], config['max_search_users'], config['search_delay_seconds'])
    print(config['tag_types'])
```

### permission_list

签名：`permission_list()`。路由 `GET /api/v1/permissions`。无参数。

返回权限名到值（数据库标题）的映射，例如 `{"IMAGE_TAG_ADD": "image_tag_add", "TAG_CREATE": "tag_create"}`。O 说明这是公开信息，供前端做权限判断。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    permissions = client.permission_list()
    # GET https://e-shuushuu.net/api/v1/permissions
    # 返回 {"权限名": "数据库标题", ...}
    print(len(permissions), permissions.get('IMAGE_TAG_ADD'))
```

## 认证方法（5 个，均未实测）

这五个方法是显式调用才动作：普通请求不会自动登录，也不会自动刷新 token。签名：`auth_login(username=None, password=None)`、`auth_refresh()`、`auth_me()`、`auth_logout()`、`auth_logout_all()`。`auth_login()` 用参数或配置里的 `username` / `password`，成功后把返回的 `access_token` 收进客户端并继续复用会话 Cookie；`auth_refresh()` 只靠 Cookie 里的 `refresh_token` 换新 token。**五个方法都没有成功响应记录**，下面是 O 描述的请求形状与参数，不是实测结果。

| 方法 | 路由 | 参数 | 成功返回（O） |
| :--- | :--- | :--- | :--- |
| `auth_login(username=None, password=None)` | `POST /api/v1/auth/login` | JSON 体 `LoginRequest`：`username`（3–30 字符）、`password`（1–255 字符）；省略时取配置里的同名值 | `TokenResponse`：`access_token`、`token_type`（默认 `bearer`）、`expires_in`（秒）、`user`（**可为 `null`**）；同时下发 HTTPOnly Cookie |
| `auth_refresh()` | `POST /api/v1/auth/refresh` | 无查询参数；用 Cookie `refresh_token` | `TokenResponse`；旧 refresh token 立即失效（轮换） |
| `auth_me()` | `GET /api/v1/auth/me` | 无 | O 里这个响应是**未定型对象**，不保证等于 `UserPrivateResponse`；只用于验证 token 是否有效 |
| `auth_logout()` | `POST /api/v1/auth/logout` | 无 | `MessageResponse`：`{"message": ...}` |
| `auth_logout_all()` | `POST /api/v1/auth/logout-all` | 无；需 Bearer | `MessageResponse` |

O 记录的账号安全规则（未实测）：连续 5 次登录失败锁账号 15 分钟、成功即清零；access token 30 分钟、refresh token 30 天；refresh token 轮换时旧 token 立即吊销，**10 秒内**的并发刷新只补发 access token，超出该窗口复用已吊销 token 会被当作盗用并吊销整族 token。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    # 未实测：登录会写入真实会话，本轮没有执行。
    session = client.auth_login('你的用户名', '你的密码')
    # POST https://e-shuushuu.net/api/v1/auth/login，JSON 体 {"username": ..., "password": ...}
    # 成功返回 {"access_token": ..., "token_type": "bearer", "expires_in": ..., "user": {...}}
    print(session['token_type'], session['expires_in'])
    me = client.auth_me()
    # GET https://e-shuushuu.net/api/v1/auth/me
    print(me)
```

## 不在原生方法里的接口

下面这些读写路径**不是**本库原生方法，需要时用通用 `request()` 直接指定路径：

* **需要登录的个人 / 管理读路径**：`/api/v1/users/me`、`/users/me/warnings`、`/users/me/taste-profile`、`/api/v1/images/recommended`、`/images/bookmark/me`、`/images/bookmark/page`、`/api/v1/privmsgs/*`、`/api/v1/admin/*`。
* **权限绑定的读路径**：`/api/v1/images/{image_id}/reports`（需要 `REPORT_VIEW`，O 标注 Mod-only）、`/api/v1/ml-suggestions*` 与 `/images/{image_id}/ml-tag-suggestions`（标签建议工作流）。
* **写路径**：上传（`POST /images/upload`）、改图（`PATCH/DELETE /images/{id}`）、加删标签（`POST/DELETE /images/{id}/tags/{tag_id}`）、评分与收藏（`POST /images/{id}/rating?rating=N`、`POST/DELETE /images/{id}/favorite`）、举报、`POST /comments` 与 `PATCH/DELETE /comments/{id}`、`POST /tags`、`PUT/DELETE /tags/{id}`、用户资料与头像、新闻增改删、私信、全部 `/admin/*` 管理动作。它们需要 `Authorization: Bearer` 与具体权限，本轮没有调用这些写路径。
* **不是 JSON 的路径**：`/api/v1/images/random`（`302` 跳转，T 记录）、`/api/v1/images.atom` 与 `/api/v1/tags/{tag_id}/images.atom`（Atom，`Content-Type: application/atom+xml`）、`/images/{filename}` 等按文件名的图片路由（匿名 `302`，T 记录）。通用 `request()` 只按 JSON 返回体工作，不解析 Atom 也不解码媒体字节；这些路径要自己换用其它 HTTP 客户端。
* **重复入口**：`/api/v1/favorites/user/{user_id}` 与 `/api/v1/favorites/image/{image_id}`（O 标为 deprecated，与 `user_favorites` / `image_favorites` 等价）；O 里的角色-来源链接、横幅、捐赠等接口也没有原生方法。

## 边界与未实测

| 范围 | 事实与边界 |
| :--- | :--- |
| 公共资源读取（35 个 `GET`） | L 本次成功调用 `search`、`tag_list`、`image_list`、`image_show`、`tag_show`、`comment_list`、`image_stats`、`meta_config`、`user_list`、`news_list`。T 另记录过图片标签、按 MD5、空相似结果、标签图片入口。其余图片/标签历史与关联资源、用户详情/图片/收藏/收藏标签/历史、评论详情/按图/按用户/统计、新闻详情、权限表与导入站点均没有本轮 L；不把35个方法概括为35个匿名成功实测。 |
| 私有 `GET` | `user_ratings` 是私有数据（本人或持 `USER_EDIT_PROFILE` 的版主）；匿名不会成功，本页只给调用形状。 |
| 认证 5 个方法 | **全部未实测**；token 有效期、轮换、盗用吊销、登录锁定等规则来自 O 描述。 |
| 分页与总数 | `per_page` 上限100（O）；L 的101得到422，`detail[].loc=['query','per_page']`、`ctx.le=100`。同一标签在 `/images?tags=`、`/tags/{id}/images`、`/tags/{id}` 三处的总数不同（T），不要混用；本轮未调用 `tag_images` 复核该差异。 |
| 排序默认值 | `image_list` / `tag_images` / `user_images` / `user_favorites` / `user_ratings` 的 `sort_by` 默认 O 写的是 `image_id`；`tag_list` 与 `search` 的 `sort_by` 没有默认值（`search` 不给就按相关度）。 |
| 未做过的行为 | 全部写请求、私有读、认证、其它排序与过滤组合、`threshold` 有结果时的 `similarity_score`、`include_comments=true` 的 `comments` 映射结构、CDN 受保护路径的带登录行为，都没有执行。`image_status_history` 的遮罩（谁在什么身份下看到用户与原因文本）也只有 O 描述，没有匿名样本。 |
| 与页面说明的冲突 | 站内帮助页对标签/用户上限的说法与 `meta_config` 一致（各为 5），但页面其它位置出现过别的数字；以 `meta/config` 为准（O/T）。旧 PHP 站路由（`/httpreq.php`、`/search/process/`、`/random.php`、`/index.php`）在该站已不存在，不要照抄老客户端。 |

继续阅读：[客户端用法](shuushuu.md) · [能力入口](shuushuu-capabilities.md) · [错误处理](errors.md)。
