# e621ng 方法参考

`E621` 的 **18 个原生方法**都是 `request()` 的薄封装，一个方法对应一条上游 `GET` JSON 路由，只读；
构造、认证、参数编码与 `last_call` 见 [客户端用法](e621.md)，按目的找入口见
[能力入口](e621-capabilities.md)。每个方法的上游行号、权限分支与状态见
[契约审计附注](e621-contract-notes.md)。

## 共用前置

本页片段都接着这段前置写：`client` 已构造好，`example` 是配置里的样例输入，`verified` 是返回形态与
权限分支的复核输入。片段里的 id、名称和文件标识由前一次响应读取，本库不代取；结束后调用 `client.close()`，
也可以把整段放进 `with E621(...) as client:`。

```python
from pybooru import E621

client = E621('e621')                              # 读包内默认 pybooru.json
example = client.config['examples']['e621']        # 站点、查询、条数与调用间隔
verified = client.config['verification']['e621']   # count_query / v2_query / only_query / related_search
```

## 全页通用契约

* **认证**：`username` 或 `api_key` 任一非空即发 HTTP Basic，两项都空才匿名；权限完全由服务端判定，
  客户端不预判、不降级。需要成员权限的方法匿名以 `403` 失败。
* **参数分层**：列表方法的过滤条件放 `search` 字典（整包发成 `search[...]`），顶层参数走 `**params`
  （`limit`、`page`、`expiry`、`group_by` 等）。**帖子三个查询方法没有 `search` 字典**：过滤条件全部写成
  顶层 `tags` 元标签。
* **搜索语义**（上游 `attribute_matches`）：数值与时间收 `5`、`>5`、`5..10`、`5,6,7`；布尔收
  `true`/`false`/`1`/`0`/`yes`/`no`；文本含 `*` 时按 `LIKE`，否则按 Postgres 全文；用户类字段成对出现
  （`creator_id` / `creator_name`、`linked_user_id` / `linked_user_name`），`*_id` 收逗号分隔列表。
  **集合之外的搜索键被静默忽略**，表现为“返回全集”；客户端不拦截、不报错。
* **分页**：`page` 收纯数字页码，或游标 `b<id>`（id 小于该值，更旧）与 `a<id>`（id 大于该值，更新），
  两种游标都按 id 逆序返回；`limit` 收 `0..320`，
  缺省 `75`（帖子走账号每页设置）；页码越界或 `limit` 非法回 `410`。见 [pagination.md](pagination.md)。
* **评级**：查询评级取首字母识别 `s` / `q` / `e`，因此 `rating:safe` 等全称也生效；
  首字母不在词表内的值（如 Danbooru 的 `rating:g`）被静默丢弃。e926 的过滤来自站点部署配置。
* **失败**：非 2xx 抛 `PybooruHTTPError`（保留状态码、URL 与正文）；`404` 正文是
  `{"success": false, "reason": "not found"}`，权限不足 `403` 是 `{"success": false, "reason": "Access Denied"}`，
  其余预期错误走 `{"success": false, "message": ..., "code": ...}`。状态码与出处见
  [契约审计附注](e621-contract-notes.md#sec-errors)。

## 帖子（4 个方法）

帖子返回哪一种形状**按来源请求分支决定**，不是调用者随便挑的开关：默认是 legacy 负载加 `posts`/`post`
信封，`md5` 命中时是单帖，`only` 为非空值或 `v2=true` 时上游直接输出裸 JSON。

| 请求 | 上游分支 | 本库返回 |
| :--- | :--- | :--- |
| 无 `md5`，`only` 为空、未给 `v2=true` | legacy 蓝图 + `{"posts": [...]}` | 帖子数组（每个是 25 键 legacy 对象） |
| `md5=<32 位 md5>` | `find_by!(md5:)` → 单帖 + `{"post": {...}}` | 单个 legacy 对象；未命中 `404` |
| 无 `md5`，但 `only` 为非空值 | legacy 蓝图**直接输出**数组 | 裸数组（字段**不裁剪**） |
| `md5=...` 且 `only` 为非空值 | 同上，单帖 | 裸 legacy 对象 |
| `v2=true` | 新蓝图（`files` / `stats`），**永不包信封** | 裸数组或裸对象 |
| `v2=true&mode=extended` | 新蓝图 `view: extended` | 同上，`tags` 是九类字典 |
| `v2=true&mode=thumbnail`（或 `thumbnails`） | 缩略图蓝图（源码：扁平 24 键） | 同上，`flags` / `pools` / `tags` 都是字符串 |
| `v2=true&mode=<其它值>` | 新蓝图 `view: basic` | 同上，`tags` 是标签名数组 |

legacy 键集（实测 25 键）：`id`、`created_at`、`updated_at`、`file`、`preview`、`sample`、`score`、`tags`、
`locked_tags`、`change_seq`、`flags`、`rating`、`fav_count`、`sources`、`pools`、`relationships`、
`approver_id`、`uploader_id`、`uploader_name`、`description`、`comment_count`、`is_favorited`、`vote`、
`has_notes`、`duration`。其中 `file` 是 `{width, height, ext, size, md5, url}`，`preview` 是
`{width, height, url, alt}`，`sample` 是 `{has, width, height, url, alt, alternates}`，`score` 是
`{up, down, total}`，`tags` 是九个类别到标签名数组的字典（`general`、`artist`、`contributor`、`copyright`、
`character`、`species`、`invalid`、`meta`、`lore`），`flags` 是
`{pending, flagged, note_locked, status_locked, rating_locked, deleted}`，`sources` 是字符串数组，
`pools` 是合集 id 数组，`relationships` 是 `{parent_id, has_children, has_active_children, children}`。
**当前身份不可见的帖子不会删键，而是把值置空**：`file.url`、`preview.url` / `preview.alt`、`sample.url` /
`sample.alt` 只在可见时有值，否则是 `null`；`file.md5` / `file.ext` 由蓝图直接取自模型（模型自己的
序列化会对不可见帖子隐藏它们），两条路径的区别见[附注](e621-contract-notes.md#sec-post-shapes)。

v2 蓝图（实测 18 键）：`id`、`created_at`、`updated_at`、`change_seq`、`files`、`uploader_id`、
`uploader_name`、`approver_id`、`stats`、`flags`、`has`、`relationships`、`pools`、`rating`、`locked_tags`、
`sources`、`description`、`tags`；`files` 是 `{meta, original, preview, sample[, video]}`，`stats` 是
`{score: {up, down, total}, fav_count, is_favorited, vote, comment_count, hotness}`，`has` 是
`{parent, children, active_children, notes, sample}`。

`post_list(**params)` — `GET /posts.json`，搜索或列出帖子；给 `md5` 时是单帖查询。
```python
posts = client.post_list(**example['post_query'])        # {"tags": "rating:s", "limit": 2}
post = client.post_list(md5=posts[0]['file']['md5'])
new_format = client.post_list(**dict(verified['post_query'], **verified['v2_query']))
```
实测：列表中两帖为 `6709455`（`jpg`，`score.total` 0）与 `6709449`（`png`，score 2）；`md5` 分支返回单帖；
`v2=true` 与 `only` 分支各有实测记录，`mode=extended` / `mode=thumbnail` 两个视图仅源码对齐。
参数：`tags`（标签/元标签查询）、`limit`、`page`（含 `a<id>` / `b<id>` 游标）、`md5`、`v2`、`mode`、
`only`（非空即拆信封）、`random`（只影响上游随机状态，排序要 `order:random`）、`post`（嵌套 `post[tags]`，
`tags` 缺席时用）。

`post_show(post_id, **params)` — `GET /posts/<post_id>.json`，读一个帖子的详情。
```python
post = client.post_show(posts[0]['id'])                  # 实测 6709455
```
参数：`post_id`、`v2`、`mode`、`only`、`post_set_id`、`pool_id`。`post_set_id` / `pool_id` 会被接受，但只
影响 HTML 视图里的集合上下文，不改变 JSON 负载结构。

`post_random(**params)` — `GET /posts/random.json`，在查询范围内随机取一帖。
```python
random_post = client.post_random(**example['random_query'])   # {"tags": "rating:s"}，实测 1434546
```
参数：`tags`、`v2`、`mode`、`only`。上游在该查询后追加 `order:random`，取不到匹配帖时 `404`。

`post_count(**params)` — `GET /posts/count.json`，统计匹配的帖子数。
```python
count = client.post_count(**verified['count_query'])     # {"tags": "rating:s"}
# 实测两个站点都得到 {'count': 240001, 'capped': True}
```
返回 `{"count": N, "capped": bool}`；`capped=True` 表示查询撞上分页上限，`count` 只是下限。
参数：`tags`、`post`（嵌套 `post[tags]`）。

## 标签（2 个方法）

`tag_list(search=None, **params)` — `GET /tags.json`，搜索标签。
```python
tags = client.tag_list(**example['tag_query'])           # {"limit": 2}
# 实测：anthro（id 7115，category 0，post_count 4464327）、mammal（id 12054，category 5）
```
`search`：`name`（逗号分隔、精确；先归一化大小写与空格再匹配）、`name_matches`（先归一化，再按 `*`
通配 LIKE）、`fuzzy_name_matches`（原样做 `%` 相似度匹配，不归一化）、`category`（逗号分隔的数字，`0` general、`1` artist、`2` contributor、
`3` copyright、`4` character、`5` species、`6` invalid、`7` meta、`8` lore）、`hide_empty`、`has_wiki`、
`has_artist`、`is_locked`、`order`（`name` / `similarity` / `id_asc` / `id_desc` / `date`，否则按
post_count 降序）。**不给 `hide_empty` 时上游默认只返回 `post_count > 0` 的标签。**
返回 tag 对象数组，键为 `id`、`name`、`post_count`、`category`、`related_tags`、
`related_tags_updated_at`、`created_at`、`updated_at`、`is_locked`。

`tag_show(tag_id, **params)` — `GET /tags/<tag_id>.json`，按 id 或名称读一个标签。
```python
tag = client.tag_show(tags[0]['id'])                     # 实测 7115 → anthro
by_name = client.tag_show(tags[0]['name'])               # 名称分支仅源码对齐
```
纯数字路径段按 id 查，否则**按原样精确匹配名称**（`Tag.find_by!(name:)`，不做大小写或空格归一化；画师的
`named` 与 wiki 的 `titled` 才会归一化，别把三者混为一谈），未命中 `404`。
返回单个 tag 对象，字段同上。

## 画师（2 个方法）

`artist_list(search=None, **params)` — `GET /artists.json`，搜索画师。
```python
artists = client.artist_list(**example['artist_query'])   # {"limit": 2}
# 实测：miindfang（id 126653，urls: https://x.com/miindfang）、weirdmichelle69（id 126652）
```
`search`：`name`、`group_name`、`any_name_matches`（名称与别名，自动加 `*`）、`any_other_name_like`、
`any_other_name_matches`、`any_name_or_url_matches`、`url_matches`、`creator_id` / `creator_name`、
`linked_user_id` / `linked_user_name`、`has_tag`（画师名是否有对应标签）、`is_linked`、`order`
（`name` / `updated_at` / `post_count`）。顶层还可以给单一 `name`，上游把它并进 `search[name]`；
`expiry`（天）允许中间层缓存该响应。返回 artist 对象数组，键为 `id`、`name`、`creator_id`、`is_active`、
`group_name`、`created_at`、`updated_at`、`other_names`、`linked_user_id`、`is_locked`，并**总是带
`urls` 数组**（每个是画师的 `artist_urls` 行）；此外还有 `notes`——它不是表列，而是模型上声明的属性
（`app/models/artist.rb:37` 的 `attribute :notes, :string`），未填写时为 `null`。分页计数只在能收窄结果的
搜索上启用，这属于上游行为。

`artist_show(artist_id, **params)` — `GET /artists/<artist_id>.json`，按 id 或名称读一个画师。
```python
artist = client.artist_show(artists[0]['id'])            # 实测 126653 → miindfang
by_name = client.artist_show(artists[0]['name'])         # 名称分支仅源码对齐
```
纯数字路径段按 id 查，否则按名称查（`Artist.named` 会归一化大小写与空格）；JSON 请求下未知名称返回
`404`（HTML 请求会被重定向到新建入口）。
返回对象除上面那些键外还带 `domains`。

## 评论（2 个方法）

`comment_list(search=None, **params)` — `GET /comments.json`，搜索评论；默认按评论分页。
```python
comments = client.comment_list(**example['comment_query'])   # {"group_by": "comment", "limit": 2}
# 实测：10071234（post 6702219，creator_name ksharbaugh）、10071233
```
`search`：`id`、`body_matches`、`post_id`（收逗号分隔的 id 列表）、`creator_id` / `creator_name`、
`poster_id` / `poster_name`（按**帖子上传者**过滤，不是评论者）、
`post_note_updater_id` / `post_note_updater_name`、`is_sticky`、`do_not_bump_post`、`order`、
`advanced_search`（正文搜索用 websearch 全文语法）；**成员**另可用 `post_tags_match`，**staff** 另可用
`is_hidden`，**admin** 另可用 `ip_addr`。返回 `CommentBlueprint` 数组：`id`、`created_at`、`updated_at`、
`post_id`、`creator_id`、`body`、`score`、`updater_id`、`do_not_bump_post`、`is_hidden`、`is_sticky`、
`warning_type`、`warning_user_id`、`creator_name`、`updater_name`、`vote`。
可见性：匿名看不到 `is_hidden` 评论与评论被关闭帖子的评论；未给 `search={'id': ...}` 时再套
“`is_sticky` 或评分达阈值”的过滤，所以这里**不是全站最新评论**。
`group_by='post'` 会切到按帖子视图：返回裸帖子对象数组，**不含评论内容**，也不是本页的 legacy 帖子负载。

`comment_show(comment_id, **params)` — `GET /comments/<comment_id>.json`，读一条评论。
```python
comment = client.comment_show(comments[0]['id'])         # 实测 10071234
```
返回单个评论对象（字段同上，无信封）；目标评论不可见时 `403`，不存在时 `404`。

## 合集（2 个方法）

`pool_list(search=None, **params)` — `GET /pools.json`，搜索合集。
```python
pools = client.pool_list(**example['pool_query'])         # {"limit": 2}
# 实测：58878（collection，post_count 15）、59177（series，is_active false）
```
`search`：`name_matches`（自动加 `*`）、`description_matches`、`creator_id` / `creator_name`、
`category`（`series` / `collection`）、`is_active`、`order`（`name` / `created_at` / `post_count`，
否则按 `updated_at` 降序）；`expiry`（天）允许缓存。返回 pool 对象数组，键为 `id`、`name`、`creator_id`、
`description`、`is_active`、`post_ids`（帖子 id 数组）、`created_at`、`updated_at`、`category`，
外加 `creator_name` 与 `post_count`。

`pool_show(pool_id, **params)` — `GET /pools/<pool_id>.json`，读一个合集，含 `post_ids`。
```python
pool = client.pool_show(pools[0]['id'])                  # 实测 58878
```
参数：`pool_id`；`page` / `limit` 会被接受，但它们只影响 HTML 视图的分页。

## 笔记（2 个方法）

`note_list(search=None, **params)` — `GET /notes.json`，搜索笔记。
```python
notes = client.note_list(**example['note_query'])         # {"limit": 2}
# 实测：506555 与 506554（都在 post 6709256，坐标与尺寸为真实值）
```
`search`：`id`、`body_matches`、`is_active`、`post_id`（逗号分隔列表）、`creator_id` / `creator_name`、
`post_note_updater_id` / `post_note_updater_name`、`order`；**成员**另可用 `post_tags_match`。
返回 note 对象数组，键为 `id`、`creator_id`、`post_id`、`x`、`y`、`width`、`height`、`is_active`、`body`、
`created_at`、`updated_at`、`version`，外加 `creator_name`（IP 类字段不下发）。

`note_show(note_id, **params)` — `GET /notes/<note_id>.json`，读一个笔记。
```python
note = client.note_show(notes[0]['id'])                  # 实测 506555
```
返回单个 note 对象，字段同上。

## wiki 页面（2 个方法）

`wiki_page_list(search=None, **params)` — `GET /wiki_pages.json`，搜索 wiki 页面。
```python
pages = client.wiki_page_list(**example['wiki_query'])    # {"limit": 2}
# 实测：rusty_seas（id 112045，category_id 3）、buckteeth（id 8473）
```
`search`：`title`（`*` 通配 LIKE，服务端会小写化并把空格转下划线）、`body_matches`、`other_names_match`
（别名匹配）、`other_names_present`、`parent`（父页面标题，重定向页用）、`creator_id` / `creator_name`、
`is_locked`、`is_deleted`、`hide_deleted`、`order`（`title` / `post_count`，否则按 `updated_at` 降序）；
顶层 `title` 会被上游并进 `search[title]`；`expiry`（天）允许缓存。返回 wiki 页面数组，键为 `id`、
`creator_id`、`title`、`body`、`is_locked`、`created_at`、`updated_at`、`updater_id`、`other_names`、
`is_deleted`、`parent`、`featured_posts`，外加 `creator_name` 与 `category_id`（没有对应标签时为 `null`）。

`wiki_page_show(title_or_id, **params)` — `GET /wiki_pages/<title_or_id>.json`，按 id 或标题读一个页面。
```python
page = client.wiki_page_show(example['wiki_title'])       # 实测 "help:api" → id 11224，is_locked true
```
纯数字路径段按 id 查，否则按标题查（服务端小写化、空格转下划线）；标题里的冒号等字符由客户端转义，
所以 `help:api` 直接传即可；未命中 `404`。返回对象字段同上。注意站点上的 `/help/api` 是另一种记录
（`help_pages` 路由下的 HelpPage），不在本方法内，需要时用 `request()` 取。

## 相关标签（2 个方法，成员权限）

两个方法在上游控制器级就要求成员身份，匿名请求 `403`（实测返回
`{"success": false, "reason": "Access Denied"}`）；成员身份需要凭据，本轮**没有成功路径实测**，
返回形状来自上游查询对象源码。

`related_tag(search=None, **params)` — `GET /related_tag.json`，求与一个查询相关的标签。
```python
related = client.related_tag(search=verified['related_search'])  # search[query] / search[category_id]
```
参数在 `search` 字典里：`query`（一个标签名，或含 `*` 的通配查询）、`category_id`（把计算限制到某个标签
类别）。返回 `[{"name": ..., "category_id": ...}]`；通配查询走另一分支，按 post_count 降序取前 50 个匹配标签
再按名称排序。`limit` 会被路由接受，但控制器总是返回自己的结果集。

`related_tag_bulk(query, category_id=None)` — `GET /related_tag/bulk.json`，一次为多个标签求相关标签。
```python
related = client.related_tag_bulk(**verified['related_search'])  # 顶层 query / category_id
```
`query` 是空格分隔的标签名（上游最多取前 25 个），`category_id` 是顶层参数。返回
`{标签名: [{"name": ..., "count": ..., "category_id": ...}]}`；`query` 为空时返回 `{}`。

继续阅读：[客户端用法](e621.md) · [能力入口](e621-capabilities.md) ·
[契约审计附注](e621-contract-notes.md) · [错误处理](errors.md) · [分页](pagination.md)。
