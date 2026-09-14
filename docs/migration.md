# 从 Pybooru 4.x 迁移

5.x（`5.0.0.dev1`）以本地上游引擎源码为契约重写了对 Danbooru 面的访问，Moebooru 面同步了共享配置用法。
本文列出所有需要改调用方的地方。

## 一、破坏性变更总览

### 1. 站点清单消失，改为根配置文件

4.x 把默认站点硬编码在 `pybooru/resources.py` 的 `SITE_LIST` 里，并允许用 `site_url=` 传任意地址。
5.x 删除 `SITE_LIST`，站点、凭据、代理、超时、User-Agent 全部来自 `pybooru.json`：

```python
# 4.x
from pybooru import Danbooru
client = Danbooru('danbooru')
client = Danbooru(site_url='https://danbooru.donmai.us')

# 5.x
client = Danbooru('danbooru')                       # sites 段的键名
client = Danbooru('danbooru', config_file='pybooru.json')
client = Danbooru('danbooru', site_url='https://safebooru.donmai.us')   # 仍可显式覆盖
```

* 配置文件**必须存在**，否则抛 `FileNotFoundError`；没有内置站点后备，也不读环境变量；
* 文件放哪、怎么指向见 [configuration.md](configuration.md)。

### 2. 通用请求入口取代 `_get()`

```python
# 4.x（内部方法，且每个方法带 auth= 开关）
client._get('posts.json', {'tags': 'rating:g'})

# 5.x
client.request('GET', 'posts.json', params={'tags': 'rating:g'})
```

`request(method, path, *, params=None, data=None, files=None)` 成为唯一出口（5.x 的 Danbooru 面**不再有**
`_get()`；Moebooru 面保留自己的 `_get`）：

* `path` 是相对路径，自动补 `.json`；
* 查询参数与 multipart 表单使用 Rails 括号编码；无文件的 `data` 使用 JSON 请求体，保留空数组；`None` 省略；
* 认证按“`username` 或 `api_key` 任一非空就附加 HTTP Basic（缺项为空串）”自动处理，**不再有 `auth=` 参数**；
  只有两项都为空才是匿名请求，凭据不全会由服务端返回 `401`；
* 不自动重试，不做本地权限判断。

详见 [danbooru.md](danbooru.md)。

### 3. 方法命名与签名统一

| 4.x | 5.x |
| :--- | :--- |
| 各方法零散参数（`name=`, `order=`, `limit=` …） | 列表方法统一 `xxx_list(search=None, **params)` |
| `auth=False` 开关 | 无（凭据决定） |
| 写方法逐个显式参数 | `xxx_create(**attributes)` / `xxx_update(id, **attributes)`，键名与 Rails strong params 一致 |
| 本地 `raise PybooruAPIError(...)` 校验参数 | 不做本地校验，交给服务端 |
| `limit > 1000` 触发 `warnings.warn` | 删除，`limit` 原样透传 |
| 文件参数 `file_=open(...)` | 文件对象由调用者传入并负责关闭 |

### 4. 返回与异常

| 情形 | 4.x | 5.x |
| :--- | :--- | :--- |
| JSON 响应 | 解析后的对象 | 同 |
| `204` / 空响应体 | `204` 返回 `True`，其余成功状态仍尝试解析 JSON | 统一返回 `None` |
| HTTP 错误 | `PybooruHTTPError(msg, http_code, url)` | `PybooruHTTPError(response)`，带 `http_code` / `url` / `body` / `data` / `response` |
| 2xx 但非 JSON | 包装为 `PybooruError`，错误处理可能再失败 | `PybooruAPIError(message, response=...)` |

详见 [errors.md](errors.md)。

### 5. 资源命名对齐上游

* wiki 相关：`wiki_*` → `wiki_page_*`（`wiki_list` → `wiki_page_list`、`wiki_show` → `wiki_page_show` 等）；
* 版本列表：`*_versions` → `*_versions_list`；
* 别名与蕴含：`tag_aliases` → `tag_aliases_list`、`tag_implications` → `tag_implications_list`；
* 相关标签：`tag_related` → `related_tag`（签名不同，见下）；
* 投票：`post_vote` → `post_vote_create`、`comment_vote` → `comment_vote_create`；
* 收藏：`favorite_add` / `favorite_remove` → `favorite_create` / `favorite_delete`；
* 计数：`count_posts` → `counts_posts`。

## 二、逐方法对照

### 帖子

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `post_list(**params)` | `post_list(**params)` | 顶层 `tags` / `page` / `limit` 照旧；posts 控制器不读取 `search[...]`，其他过滤写入 `tags` 元标签 |
| `post_show(post_id)` | `post_show(post_id)` | 不变 |
| `post_update(post_id, tag_string=..., ...)` | `post_update(post_id, **attributes)` | 旧的 `is_rating_locked` / `is_note_locked` / `is_status_locked` 已不在上游允许更新字段里；现在按 `post[...]` 透传 |
| `post_revert(post_id, version_id)` | `post_revert(post_id, version_id)` | 不变 |
| `post_copy_notes(post_id, other_post_id)` | `post_copy_notes(post_id, other_post_id)` | 不变 |
| `post_mark_translated(post_id, check_translation, partially_translated)` | `post_mark_as_translated(post_id, check_translation=None, partially_translated=None)` | 名字对齐路由 |
| `post_vote(post_id, score)` | `post_vote_create(post_id, score)` | |
| `post_unvote(post_id)` | **删除**，改用 `post_vote_delete(vote_id)` | 4.x 请求的 `PUT posts/<id>/unvote` 已无该路由 |
| `post_flag_list(creator_id=..., ...)` | `post_flags_list(search=None, **params)` | 过滤条件统一走 `search`；`is_resolved` 已废，现用 `status=pending/succeeded/rejected` 与 `category` |
| `post_flag_show(flag_id)` | `post_flag_show(flag_id)` | 修正：4.x 实际请求的是 `post_appeals/<flag_id>`，拿 flag id 去查 appeal |
| `post_flag_create(post_id, reason)` | `post_flag_create(post_id, reason, **attributes)` | `post_flag[post_id, reason]` |
| `post_appeals_list(creator_id=..., ...)` | `post_appeals_list(search=None, **params)` | 旧的把过滤条件发成了顶层参数，等于不过滤 |
| `post_appeals_show(appeal_id)` | `post_appeal_show(appeal_id)` | |
| `post_appeals_create(post_id, reason)` | `post_appeal_create(post_id, reason, **attributes)` | |
| `post_versions_list(updater_name=..., ...)` | `post_versions_list(search=None, **params)` | `search[start_id]` 从不存在；改用 `post_id` / `updater_id` / `changed_tags` / `is_new`；站点未配置 archive 服务时整个端点返回 501 |
| `post_versions_show(version_id)` | **删除**（无该路由） | 上游只路由了 `post_versions` 的 index 与 undo，没有单版本查询；版本数据只能整表检索或用 `post_version_undo()` |
| `post_versions_undo(version_id)` | `post_version_undo(version_id)` | 路由本身未变 |

### 上传与媒体

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `upload_list(uploader_id=..., ...)` | `upload_list(search=None, **params)` | 顶层 `user_id` / `limit` / `mode` / `size`；过滤走 `search`。**可见范围收紧**：非 moderator 只能看到自己的上传 |
| `upload_show(upload_id)` | `upload_show(upload_id)` | 同上（仅本人或 moderator） |
| `upload_create(tags, rating, file_=..., ...)` | `upload_create(files=None, source=None, referer_url=None)` | 上传接口不再接受 `tag_string` / `rating` / `parent_id`；文件字段是字面键名 `upload[files][<索引>]`，打标改走 `post_create()` |
| — | `upload_assets_list` / `upload_media_assets_list` / `upload_media_asset_show` | 新增上传资源查询 |
| — | `media_assets_list` / `media_asset_show` / `media_asset_delete` / `media_metadata_list` / `ai_tags_list` / `ai_tag_tag` | 新增媒体资源与 AI 标签 |

### 标签

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `tag_list(name_matches=..., ...)` | `tag_list(search=None, **params)` | 过滤条件走 `search`；删除 `limit > 1000` 的本地告警 |
| `tag_show(tag_id)` | `tag_show(tag_id)` | 不变 |
| `tag_update(tag_id, category)` | `tag_update(tag_id, **attributes)` | 修正：4.x 请求的是 `pools/<id>`（会把 tag id 当 pool id）；另支持 `tag[is_deprecated]` |
| `tag_aliases(name_matches=..., ...)` | `tag_aliases_list(search=None, **params)` | 另有 `tag_alias_show` / `tag_alias_delete`（等同拒绝） |
| `tag_implications(...)` | `tag_implications_list(search=None, **params)` | 同上，另有 `implied_from` / `implied_to` |
| `tag_related(query, category=None)` | `related_tag(search=None, **params)` | `query` / `category` / `order` / `search_sample_size` / `tag_sample_size` 放入 `search`；`limit` / `media_asset_id` 在顶层 |
| — | `tag_versions_list` / `tag_version_show` | 新增 |

> 创建别名/蕴含请走 `bulk_update_request_create()`（现役站点不再提供直接的 alias/implication 创建接口）。

### 画师

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `artist_list(query=None, artist_id=..., ...)` | `artist_list(search=None, **params)` | `search[name]` 语义已变：模糊匹配用 `any_name_matches`，URL 用 `url_matches`；`empty_only` / `is_active` / `creator_name` / `creator_id` 已不在搜索字段内 |
| `artist_show(artist_id)` | `artist_show(artist_id)` | 不变 |
| — | `artist_show_or_new(name)` | 新增（名字存在时 302 重定向） |
| `artist_create(name, ...)` | `artist_create(name, **attributes)` | 修正：4.x 调用了不存在的 `self.get(...)`，必然 `AttributeError` |
| `artist_update(artist_id, ...)` | `artist_update(artist_id, **attributes)` | 同上 |
| `artist_delete(artist_id)` | `artist_delete(artist_id)` | 不变（置 `is_deleted=true`）；服务端 `redirect_to`，客户端跟随重定向，最终格式以目标端点为准（写类未实测） |
| `artist_undelete(artist_id)` | **删除**，改用 `artist_update(artist_id, is_deleted=False)` | 上游无 `artists/<id>/undelete` 路由 |
| `artist_banned()` | **删除**，改用 `artist_list(search={'is_banned': True})` | 上游无 `artists/banned` 路由 |
| `artist_revert(artist_id, version_id)` | `artist_revert(artist_id, version_id)` | 不变 |
| — | `artist_ban` / `artist_unban` | 新增（需 admin）；服务端 `redirect_to`，未实测 |
| `artist_versions(name=..., ...)` | `artist_versions_list(search=None, **params)` | `search[is_active]` 已废，现为 `is_deleted` / `is_banned` |
| `artist_commentary_list(...)` | `artist_commentaries_list(search=None, **params)` | |
| `artist_commentary_create_update(post_id, ...)` | `artist_commentary_create_or_update(post_id, **attributes)` | 动词改为 PUT，参数嵌套在 `artist_commentary` |
| `artist_commentary_revert(id_, version_id)` | `artist_commentary_revert(post_id, version_id)` | 路径里的 `:id` 实为 **post_id**，4.x 文档描述有误导 |
| `artist_commentary_versions(post_id, updater_id)` | `artist_commentary_versions_list(search=None, **params)` | 另有 `artist_commentary_version_show` |

按 URL 查画师、pixiv id → tag 的推荐写法见 [danbooru-artists.md](danbooru-artists.md)。

### 评论与笔记

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `comment_list(group_by, ...)` | `comment_list(search=None, **params)` | `group_by` 变可选（默认按 comment）；补 `is_sticky` / `score` / `is_edited` / `updater_*` |
| `comment_create(post_id, body, ...)` | `comment_create(post_id, body, **attributes)` | `comment[post_id, body, do_not_bump_post, is_sticky]` |
| `comment_update(comment_id, body)` | `comment_update(comment_id, **attributes)` | |
| `comment_show` / `comment_delete` / `comment_undelete` | 同名 | `comment_create` 之外的读/删保持原样 |
| `comment_vote(comment_id, score)` | `comment_vote_create(comment_id, score)` | |
| `comment_unvote(comment_id)` | **删除**，改用 `comment_vote_delete(vote_id)` | 4.x 请求的 `posts/<id>/unvote` 已无该路由 |
| `note_list(...)` | `note_list(search=None, **params)` | `search[creator_id]` / `[creator_name]` 已不在搜索字段内 |
| `note_show(note_id)` | `note_show(note_id)` | 不变 |
| `note_create(post_id, coor_x, coor_y, width, height, body)` | `note_create(post_id, x, y, width, height, body, **attributes)` | 坐标形参更名为上游字段 `x` / `y` |
| `note_delete(note_id)` | `note_delete(note_id)` | 仍为软删除（`is_active=false`） |
| `note_revert(note_id, version_id)` | `note_revert(note_id, version_id)` | 不变 |
| `note_update(note_id, ...)` | `note_update(note_id, **attributes)` | 修正：4.x 路由拼成 `notes/<id>.jso`（缺 n） |
| `note_versions(...)` | `note_versions_list(search=None, **params)` | 另有 `note_version_show` |
| — | `note_preview(body)` | 新增 |

### 合集与 wiki

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `pool_list(name_matches=..., ...)` | `pool_list(search=None, **params)` | `name_matches` 仍有效（Pool.name 是 text）；另支持 `name` / `name_contains`；`is_active` / `creator_*` 已废，现为 `is_deleted` |
| `pool_update(pool_id, ..., is_active=...)` | `pool_update(pool_id, **attributes)` | `pool[is_active]` 已废；`post_ids` 保留，另有 `post_ids_string` |
| `pool_create` / `pool_show` / `pool_delete` / `pool_undelete` / `pool_revert` / `pool_versions` | 同名（`pool_versions` → `pool_versions_list`） | `pool_delete` / `pool_undelete` 需要 **builder** 权限；`pool_update` 允许的字段是 `name` / `description` / `category` / `post_ids` / `post_ids_string`（`is_active` 不在其中） |
| — | `pool_gallery` / `pool_element_create` / `pool_version_diff` | 新增 |
| `wiki_list(...)` | `wiki_page_list(search=None, **params)` | `search[creator_id]` / `[creator_name]` 已废；标题模糊用 `title_normalize` / `title_or_body_matches` |
| `wiki_show(wiki_page_id)` | `wiki_page_show(id_or_title)` | 支持标题；标题需 URL 转义 |
| `wiki_create(title, body, other_names=None)` | `wiki_page_create(title, **attributes)` | `body`、`other_names` 改为关键字属性 |
| `wiki_update(page_id, ...)` | `wiki_page_update(page_id, **attributes)` | 4.x 声明的 `is_locked` / `is_deleted` 是死参数（从未发送），现在会真正透传 |
| `wiki_delete(page_id)` | `wiki_page_delete(page_id)` | |
| `wiki_revert(wiki_page_id, version_id)` | `wiki_page_revert(page_id, version_id)` | |
| `wiki_versions_list(page_id, updater_id)` | `wiki_page_versions_list(search=None, **params)` | 修正：4.x 键名拼成 `earch[updater_id]`（永不发送） |
| `wiki_versions_show(page_id)` | `wiki_page_version_show(version_id)` | 语义修正：取的是**版本 id** |
| — | `wiki_page_show_or_new(title)` / `wiki_page_versions_diff(...)` | 新增 |

### 用户、收藏、站内信

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `user_list(name=None, name_matches=..., ...)` | `user_list(search=None, **params)` | 顶层 `name` 仍可用（会转成 `name_or_past_name_matches`）；补 `is_banned` |
| `user_show(user_id)` | `user_show(user_id)` | 不变 |
| — | `user_create` / `user_update` / `user_profile` / `user_actions_list` / `user_events_list` / `user_feedbacks_*` / `user_name_change_requests_*` | 新增 |
| `favorite_list(user_id=None)` | `favorite_list(search=None, **params)` | 新增顶层 `post_id` 与 `search[...]` |
| `favorite_add(post_id)` | `favorite_create(post_id)` | |
| `favorite_remove(post_id)` | `favorite_delete(post_id)` | 路由未变（`DELETE favorites/<post_id>`） |
| — | `favorite_groups_list` / `favorite_group_show` / `favorite_group_create` / `favorite_group_update` / `favorite_group_delete` / `favorite_group_add_post` / `favorite_group_remove_post` | 新增收藏分组全套 |
| `dmail_list(message_matches=..., read=...)` | `dmail_list(search=None, **params)` | `search[read]` 不存在，改用 `is_read`；补 `folder` |
| `dmail_show(dmail_id)` | `dmail_show(dmail_id)` | 不变，只能读取获授权的邮件 |
| `dmail_create(to_name, title, body)` | `dmail_create(title, body, to_name=None, to_id=None)` | 收件人改为关键字参数；同时支持 `to_id` |
| `dmail_delete(dmail_id)` | **删除**，改用 `dmail_update(dmail_id, is_deleted=True)` | 上游无 `DELETE dmails/<id>` |
| — | `dmail_update` / `dmails_mark_all_as_read` | 新增 |

### 论坛

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `forum_topic_list(title_matches=..., ...)` | `forum_topics_list(search=None, **params)` | 过滤条件走 `search` |
| `forum_topic_create(title, body, category=None)` | `forum_topic_create(title, body, **attributes)` | |
| `forum_topic_update(topic_id, ...)` | `forum_topic_update(topic_id, **attributes)` | 属性嵌套在 `forum_topic` |
| `forum_post_create(topic_id, body)` | `forum_post_create(topic_id, body)` | 参数与路由不变 |
| `forum_post_list(topic_title_matches=..., topic_category_id=...)` | `forum_posts_list(search=None, **params)` | 改为 `search[topic][title_matches]`、`search[topic][category_id]` |
| `forum_post_update(topic_id, body)` | `forum_post_update(post_id, body)` | 形参名误导：传的是论坛**帖子** id |
| `forum_topic_show(topic_id)` | `forum_topic_show(topic_id)` | 路由不变 |
| `forum_topic_delete(topic_id)` | `forum_topic_delete(topic_id)` | 路由不变，删除需相应权限 |
| `forum_topic_undelete(topic_id)` | `forum_topic_undelete(topic_id)` | 路由不变 |
| `forum_post_delete(post_id)` | `forum_post_delete(post_id)` | 路由不变 |
| `forum_post_undelete(post_id)` | `forum_post_undelete(post_id)` | 路由不变 |
| — | `forum_post_show(post_id)` | 新增原生详情方法 |
| — | `forum_post_votes_list` / `forum_post_vote_create` / `forum_post_vote_delete` / `forum_topic_visits_list` / `forum_topics_mark_all_as_read` | 新增 |

### 计数与杂项

| 4.x | 5.x | 说明 |
| :--- | :--- | :--- |
| `count_posts(tags=None)` | `counts_posts(tags=None, estimate_count=None, skip_cache=None)` | 新增 `estimate_count` / `skip_cache` |
| — | `status` / `source_show` / `iqdb_query` / `autocomplete_list` | 新增 |
| — | `ban_*` / `ip_ban_*` / `ip_address_show` / `ip_geolocations_list` / `mod_actions_*` / `modqueue_list` / `moderation_reports_*` / `news_updates_*` / `saved_searches_*` / `site_credentials_*` / `reactions_*` / `report_show` / `jobs_list` / `job_*` / `dtext_links_list` / `recommended_posts_list` / `rate_limits_list` / `api_key_*` / `bulk_update_request_*` | 新增（多数需要相应权限） |

## 三、4.x 中被修正的实现缺陷

这些是 4.x 里“看起来能用、实际发错请求”的地方，升级后行为会变：

1. `post_update` 把 `source` 拼成了 `ost[source]`，该参数从未生效；
2. `post_flag_show` 请求 `post_appeals/<id>`，用 flag id 查 appeal；
3. `post_appeals_list` 的过滤条件发成了顶层参数，不产生过滤效果；
4. `post_versions_list` 发送不存在的 `search[start_id]`；
5. `post_unvote` / `comment_unvote` 指向不存在的 `unvote` 路由；
6. `upload_create` 发送已不被允许的 `upload[tag_string]` 等字段，并在文件参数为 `None` 时崩溃；
7. `artist_create` / `artist_update` 调用不存在的 `self.get(...)`，直接 `AttributeError`；
8. `artist_banned` / `artist_undelete` 指向不存在的路由；
9. `tag_update` 请求 `pools/<id>`（完全错路由）；
10. `note_update` 路由拼成 `notes/<id>.jso`；
11. `wiki_versions_list` 键名拼成 `earch[updater_id]`，从不发送；
12. `wiki_update` 的 `is_locked` / `is_deleted` 是死参数；
13. `pool_list` 的 `creator_id` / `creator_name` / `is_active` 已不在搜索属性内（`name_matches` 仍有效）；
14. `forum_post_list` 发送已不存在的扁平参数 `topic_title_matches` / `topic_category_id`；
15. `dmail_list` 使用不存在的 `search[read]`；
16. `artist_versions` 使用已废的 `search[is_active]`；
17. 文件句柄：旧 `_get(file_=open(...))` 打开的句柄从不关闭，现在由调用者管理。

## 四、迁移检查清单

1. 准备一份 `pybooru.json`（从仓库根样例复制），填好站点与凭据；
2. 把 `Danbooru('danbooru')` 之外的站点构造改为 `sites` 段的键名，删掉对 `SITE_LIST` 的依赖；
3. 除 `post_list(**params)` 与 `autocomplete_list(query, ...)` 外，列表过滤迁至 `search={...}`；分页保持顶层；
4. 写接口改用 `**attributes` 形式，删掉 `auth=` 参数；
5. 替换已删除的方法（`post_unvote` / `comment_unvote` / `artist_undelete` / `artist_banned` /
   `dmail_delete`）；
6. 捕获异常时改用新字段（`PybooruHTTPError.http_code` / `.url` / `.body` / `.data`）；
7. Moebooru 调用方只需改构造与配置来源，方法签名未变（详见 [moebooru.md](moebooru.md)）。

## 五、未验证项

* 所有需要登录的写接口都只做了源码对齐，**未做线上实测**；
* Moebooru 面未做线上验证；
* 已完成的匿名只读验证记录（如有）见 [danbooru-api.md](danbooru-api.md) 的“验证状态”一节。
