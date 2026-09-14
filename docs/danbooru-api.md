# Danbooru API 面与端点清单

本文按 Danbooru 引擎（本地只读参考 `danbooru/`）的 `config/routes.rb`、`app/controllers/*`、
`app/models/*`、`app/policies/*` 整理端点契约，是 `Danbooru` 客户端原生方法的路由来源。

> **验证状态**：全部条目都是**源码对齐**（路由、动词、参数、可见范围按上游源码逐条核对）。
> 需要凭据的端点**一律未实测**；匿名只读端点的线上验证记录见文末[验证状态](#验证状态)。

## 全局契约

### 路径与格式

* 路径是站点根地址之后的相对路径，**没有** API 版本前缀；
* 原生方法显式使用 `.json`，`request()` 会为无后缀路径补齐；重定向目标即使没有后缀，也可通过 `Accept: application/json` 协商 JSON；
* 路径里的 ID 或标题若含特殊字符，需要调用者自行 URL 转义（`wiki_page_show` 已内置）；
* 请求了不支持的格式会得到 `406`。

### 认证

* HTTP Basic：`Authorization: Basic base64(username:api_key)`；
* 服务端还接受 `?login=<name>&api_key=<key>` 这种查询参数形式；
* 只要出现认证信息但**不完整或无效**，服务端返回 `401`——不会静默降级为匿名；
* 匿名身份代入 `User.anonymous`，读接口默认放行，权限由服务端 Pundit 判定；权限不足返回 `403`；
* 客户端行为见 [authentication.md](authentication.md)。

### 参数分层

| 层 | 形式 | 说明 |
| :--- | :--- | :--- |
| 顶层参数 | `?limit=10&page=2&tags=...` | 分页、内容搜索、控制器直接读取的字段 |
| 搜索参数 | `?search[x]=y` | 模型 `search` 方法认识的过滤条件 |

列表方法的签名统一为：

```python
def xxx_list(self, search=None, **params)
```

`search` 是**完整的搜索参数字典**，整包透传成 `search[...]`，不做白名单拦截；`**params` 是顶层参数。
帖子列表例外（`post_list(**params)`）：查询走 `tags` 元标签，不吃 `search` 字典。`autocomplete_list(query, type=None, limit=None)` 则显式接收查询词并放入 `search`。

写方法的 `post[...]`、`comment[...]` 这类属性名就是请求体里的嵌套键：没有文件时整个 `data` 以 **JSON
请求体**发送（结构原样保留，显式的空数组也会发出去），带文件时改用 Rails 表单 / multipart 编码。
查询串 `params` 始终是 Rails 括号形式。详见 [danbooru.md](danbooru.md#参数编码)。

端点无关的顶层参数：

| 参数 | 作用 |
| :--- | :--- |
| `page` / `limit` | 分页，见 [pagination.md](pagination.md) |
| `only` | 选择返回字段及嵌套关联，如 `only=id,url,artist[name]`（只对 json/xml 生效） |
| `redirect` | `redirect=true` 且结果唯一时 302 跳到该对象的页面 |
| `safe_mode` | 强制 `rating:g` |
| `save_data` | 省流模式 |

两点容易踩的坑：

* **`GET` 请求不能带请求体**，否则 `400`；
* `GET` 上不要发送**空字符串**的 `search` 值：站点会把它剔除并 `302` 到清理后的 URL
  （`None` 值由客户端直接省略，不受影响）。

### 通用搜索后缀

模型先声明可搜索属性，`SearchContext` 再按列类型生成参数族（上游 `app/logical/concerns/searchable.rb`）：

| 列类型 | 可用参数（`name` 为属性名） |
| :--- | :--- |
| string | `name`、`name_present`、`name_eq`、`name_not_eq`、`name_like`、`name_ilike`、`name_regex`、`name_array`、`name_comma`、`name_space`、`name_lower_array`、… |
| text | string 的全部 **+** `name_matches`（全文；含 `*` 时按 `ILIKE`） |
| 数值 / 时间 | `name`（`5`、`>5`、`5..10`、`5,6,7`）、`name_not`、`name_gt`、`name_gteq`、`name_lt`、`name_lteq` |
| boolean | `name`（`true/false/1/0/yes/no`） |
| 关联 | FK 字段族；关联对象是 User 时 `assoc_name`，是 Post 时 `assoc_tags_match`；`has_assoc=true/false`；嵌套 `search[assoc][...]` |
| 通用 | `search[id]` 支持 `1,2,3` 与范围；`order` 由各模型自解释 |

搜索属性集合之外的参数会被**静默忽略**（不报错）——这正是旧参数失效时表现为“返回全集”的原因。

### 分页与上限

* 默认每页 `20`（`Danbooru.config.posts_per_page`）；通用上限 `1000`，posts 为 `200`；
  uploads / upload_media_assets / media_assets / ai_tags 的 `limit` 被限制在 `0..200`；
* 页码上限：匿名与普通用户 1000，Gold 及以上 5000，超出返回 `410`；
* 标签查询上限：匿名 2 个标签，Gold 6 个，Platinum 不限；超出返回 `422`。

### 失败

非 2xx 抛 `PybooruHTTPError`，2xx 但非 JSON 抛 `PybooruAPIError`；状态码清单见
[errors.md](errors.md)。`post_versions*` / `pool_versions*` 在站点未配置 archive 服务时会返回
`501`——这类“能力依赖”在下面各表里已标注。

## 状态与账号

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `status()` | `GET status.json` | 匿名 | — |
| `rate_limits_list(search=None, **params)` | `GET rate_limits.json` | 匿名 | `search[id, action, key, limited, points]` |
| `user_profile()` | `GET profile.json` | 需登录 | — |
| `api_keys_list(search=None, **params)` | `GET api_keys.json` | 需登录 + 重新认证 | `search[id, key, user_id]`；返回里**不含** `key` |
| `api_key_create(**attributes)` | `POST api_keys.json` | 需登录 | `api_key[name, permitted_ip_addresses, permissions]`；创建时返回明文 key |
| `api_key_update(api_key_id, **attributes)` | `PUT api_keys/<id>.json` | 需登录 | 同 `api_key_create` |
| `api_key_delete(api_key_id)` | `DELETE api_keys/<id>.json` | 需登录 | — |

## posts（帖子）

> **最大的新手陷阱**：posts 的列表查询**不使用** `search[...]`。标签查询走**顶层** `tags=`，
> 分页走顶层 `page`/`limit`。

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `post_list(**params)` | `GET posts.json` | 匿名 | 顶层 `tags`、`md5`、`random`、`page`、`limit`、`size`、`show_votes`、`only`。**不读 `search` 字典**：过滤条件全部写成 `tags` 里的元标签（`rating:g`、`score:>10`、`order:score`）；`md5=` 直接返回单个 post；`random=true` 会 302 |
| `post_show(post_id)` | `GET posts/<id>.json` | 匿名 | `only` |
| `post_random(tags=None)` | `GET posts/random.json` | 匿名 | 顶层 `tags`；无结果 404 |
| `post_create(upload_media_asset_id, **attributes)` | `POST posts.json` | 需登录（member+，且是上传者） | 顶层 `upload_media_asset_id`；`post[tag_string, rating, parent_id, source, is_pending, artist_commentary][...]`。文件必须先经 `upload_create()` 上传 |
| `post_update(post_id, **attributes)` | `PUT posts/<id>.json` | 需登录 | `post[tag_string, old_tag_string, parent_id, old_parent_id, source, old_source, rating, old_rating, has_embedded_notes]`；`old_*` 是并发保护字段 |
| `post_delete(post_id, reason, move_favorites=None)` | `DELETE posts/<id>.json` | 需登录（approver+） | 顶层 `commit=Delete`（方法已带）+ `post[reason, move_favorites]`。理由为必填形参 |
| `post_revert(post_id, version_id)` | `PUT posts/<id>/revert.json` | 需登录 | 顶层 `version_id` |
| `post_copy_notes(post_id, other_post_id)` | `PUT posts/<id>/copy_notes.json` | 需登录 | 顶层 `other_post_id`；成功 **204**（返回 `None`），失败 400 `{success:false, reason:...}` |
| `post_mark_as_translated(post_id, check_translation=None, partially_translated=None)` | `PUT posts/<id>/mark_as_translated.json` | 需登录 | `post[check_translation, partially_translated]` |
| `post_events_list(search=None, **params)` | `GET post_events.json` | 匿名 | 顶层 `post_id`；`search[model_type, model_id, post_id, creator_id, category, event_at]` |
| `post_versions_list(search=None, **params)` | `GET post_versions.json` | 匿名（能力依赖） | `search[id, updated_at, updater_id, updater_name, post_id, tags, added_tags, removed_tags, rating, parent_id, source, version, changed_tags, all_changed_tags, any_changed_tags, tag_matches, is_new]`；未配置 archive 服务时 501 |
| `post_version_undo(version_id)` | `PUT post_versions/<id>/undo.json` | 需登录 | — |
| `post_votes_list(search=None, **params)` | `GET post_votes.json` | 匿名（可见范围受限） | `search[id, score, is_deleted, user_id, post_id]` |
| `post_vote_show(vote_id)` | `GET post_votes/<id>.json` | 受限 | — |
| `post_vote_create(post_id, score)` | `POST posts/<post_id>/votes.json` | 需登录（member） | 顶层 `score`（`up`/`down` 或 `1`/`-1`） |
| `post_vote_delete(vote_id)` | `DELETE post_votes/<id>.json` | 本人或 admin | 没有按 post_id 撤销投票的路由，需先查投票 id |
| `post_favorites_list(post_id, search=None, **params)` | `GET posts/<post_id>/favorites.json` | 匿名 | — |
| `post_replacements_list(search=None, **params)` | `GET post_replacements.json` | 匿名 | 顶层 `post_id`；`search[id, md5, old_md5, file_ext, original_url, replacement_url, creator_id, creator_name, post_id]` |
| `post_replacement_show(replacement_id)` | `GET post_replacements/<id>.json` | 匿名 | — |
| `post_replacement_create(post_id, replacement_file=None, **attributes)` | `POST post_replacements.json` | 需 moderator | 顶层 `post_id`；`post_replacement[replacement_url, final_source, tags]`；本地文件通过 `replacement_file` 开放二进制句柄发送 multipart |
| `post_replacement_update(replacement_id, **attributes)` | `PUT post_replacements/<id>.json` | 需 moderator | `post_replacement[old_file_ext, md5, original_url, replacement_url, ...]` |
| `post_regeneration_create(post_id, category=None)` | `POST post_regenerations.json` | 需 moderator | 顶层 `post_id`、`category` |
| `post_approvals_list(search=None, **params)` | `GET post_approvals.json` | 匿名 | `search[id, user_id, post_id]` |
| `post_approval_show(approval_id)` | `GET post_approvals/<id>.json` | 匿名 | — |
| `post_approval_create(post_id)` | `POST post_approvals.json` | 需 approver | 顶层 `post_id` |
| `post_disapprovals_list(search=None, **params)` | `GET post_disapprovals.json` | 匿名（非 moderator 只看自己的） | `search[id, message, reason, post_id, user_id, has_message]` |
| `post_disapproval_show(disapproval_id)` | `GET post_disapprovals/<id>.json` | 匿名（受限） | — |
| `post_disapproval_create(post_id, **attributes)` | `POST post_disapprovals.json` | 需登录 | `post_disapproval[post_id, reason, message]` |
| `post_disapproval_update(disapproval_id, **attributes)` | `PUT post_disapprovals/<id>.json` | 需登录（本人） | 同上 |
| `post_flags_list(search=None, **params)` | `GET post_flags.json` | 匿名（flag 人字段受限） | `search[id, reason, status, post_id, creator_id, creator_name, category]` |
| `post_flag_show(flag_id)` | `GET post_flags/<id>.json` | 受限 | — |
| `post_flag_create(post_id, reason, **attributes)` | `POST post_flags.json` | 需登录 | `post_flag[post_id, reason]` |
| `post_flag_update(flag_id, reason, **attributes)` | `PUT post_flags/<id>.json` | 需登录（本人且 pending） | `post_flag[reason]` |
| `post_appeals_list(search=None, **params)` | `GET post_appeals.json` | 匿名 | `search[id, reason, status, post_id, creator_id, creator_name]` |
| `post_appeal_show(appeal_id)` | `GET post_appeals/<id>.json` | 受限 | — |
| `post_appeal_create(post_id, reason, **attributes)` | `POST post_appeals.json` | 需登录 | `post_appeal[post_id, reason]` |
| `post_appeal_update(appeal_id, reason, **attributes)` | `PUT post_appeals/<id>.json` | 需登录（本人且 pending） | `post_appeal[reason]` |

> `post_versions` 的 JSON 数据读取只有 index，修改有 undo；另有 HTML 搜索页。没有单版本 JSON show，因此没有 `post_version_show`。

## uploads 与媒体资源

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `upload_list(search=None, **params)` | `GET uploads.json` | 需登录（非 moderator 只能看自己的） | `search[id, source, referer_url, status, uploader_id, uploader_name, media_asset_count, is_posted, ai_tags_match, any_source_matches, order]`、`page`/`limit` |
| `upload_show(upload_id)` | `GET uploads/<id>.json` | 需登录（本人/mod） | — |
| `upload_create(files=None, source=None, referer_url=None)` | `POST uploads.json` | 需登录（member+） | `upload[source]` **或** `upload[files][<索引>]`（多文件/压缩包，字面键名）、`upload[referer_url]`。`source` 与文件互斥；旧字段 `upload[tag_string]`/`[rating]`/`[parent_id]`/`[file]` 已不存在 |
| `upload_assets_list(upload_id, search=None, **params)` | `GET uploads/<upload_id>/assets.json` | 需登录（本人/mod） | `limit` ≤ 200 |
| `upload_media_assets_list(search=None, **params)` | `GET upload_media_assets.json` | 需登录 | `search[id, status, source_url, page_url, error, upload_id, media_asset_id, post_id, is_posted]` |
| `upload_media_asset_show(upload_media_asset_id)` | `GET upload_media_assets/<id>.json` | 需登录（本人/mod） | — |
| `media_assets_list(search=None, **params)` | `GET media_assets.json` | 匿名 | `search[id, md5, pixel_hash, file_ext, file_size, image_width, image_height, duration, status, is_public, metadata]`；不可见时返回里会剔除 `md5`/`file_key`/`variants` |
| `media_asset_show(media_asset_id)` | `GET media_assets/<id>.json` | 匿名 | — |
| `media_asset_delete(media_asset_id)` | `DELETE media_assets/<id>.json` | 需 admin | — |
| `media_metadata_list(search=None, **params)` | `GET media_metadata.json` | 匿名 | `search[id, media_asset_id, metadata]` |
| `ai_tags_list(search=None, **params)` | `GET ai_tags.json` | 匿名 | `search[media_asset_id, tag_id, post_id, score]`、`limit`、`mode`、`size` |
| `ai_tag_tag(media_asset_id, tag_id, tag=None, mode=None)` | `PUT ai_tags/<media_asset_id>/<tag_id>/tag.json` | 需登录且能改该 post | 顶层 `tag`、`mode=remove` 表示撤销 |

> 上传新帖的两步流程：① `upload_create(files=[...])` 或 `upload_create(source=...)` 拿到
> `upload_media_asset_id`；② `post_create(upload_media_asset_id=..., tag_string=..., rating=...)`。

## tags、别名、蕴含、相关标签

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `tag_list(search=None, **params)` | `GET tags.json` | 匿名 | `search[id, name, name_matches, name_normalize, name_or_alias_matches, fuzzy_name_matches, category, post_count, hide_empty, is_empty, has_wiki_page, has_artist, is_deprecated, order=name/date/count/similarity]`；JSON 下 `hide_empty` **没有默认值** |
| `tag_show(tag_id)` | `GET tags/<id>.json` | 匿名 | — |
| `tag_update(tag_id, **attributes)` | `PUT tags/<id>.json` | 需登录（改 category 需更高权限） | `tag[category]`、`tag[is_deprecated]` |
| `tag_versions_list(search=None, **params)` | `GET tag_versions.json` | 匿名 | `search[id, name, name_matches, category, is_deprecated, tag_id, updater_id, updater_name, version, order]`、顶层 `tag_id`/`updater_id` |
| `tag_version_show(version_id)` | `GET tag_versions/<id>.json` | 匿名 | — |
| `tag_aliases_list(search=None, **params)` | `GET tag_aliases.json` | 匿名 | `search[id, antecedent_name, consequent_name, status, reason, creator_id, creator_name, approver_id, name_matches]` |
| `tag_alias_show(tag_alias_id)` | `GET tag_aliases/<id>.json` | 匿名 | — |
| `tag_alias_delete(tag_alias_id)` | `DELETE tag_aliases/<id>.json` | 需登录 | 语义是**拒绝**该请求 |
| `tag_implications_list(search=None, **params)` | `GET tag_implications.json` | 匿名 | 同别名，另有 `search[implied_from, implied_to]` |
| `tag_implication_show(tag_implication_id)` | `GET tag_implications/<id>.json` | 匿名 | — |
| `tag_implication_delete(tag_implication_id)` | `DELETE tag_implications/<id>.json` | 需登录 | 同上 |
| `related_tag(search=None, **params)` | `GET related_tag.json` | 匿名 | `search[query]`（必需）、`search[category]`/`search[categories]`、`search[order]` ∈ `frequency`(默认)/`cosine`/`jaccard`/`overlap`、`search[search_sample_size]`（默认 5000）、`search[tag_sample_size]`（默认 500）；顶层 `limit`（默认 100、上限 1000）、`media_asset_id`。服务端也接受裸参数写法，本方法统一用 `search[...]` |
| `autocomplete_list(query, type=None, limit=None)` | `GET autocomplete.json` | 匿名 | `search[query]`、`search[type]`（`tag`/`tag_query`/`artist`/`wiki_page`/`user`/…）、顶层 `limit`（服务端默认 10）；返回类型依搜索种类而定，不做客户端转换 |

创建别名/蕴含的正规入口是 **bulk update request**（见“审核与运维”），没有 `tag_alias_create` /
`tag_implication_create`。

## artists

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `artist_list(search=None, **params)` | `GET artists.json` | 匿名 | 顶层 `name`（会被折成 `search[name]`，精确）；`search[id, name, name_matches, any_name_matches, any_name_or_url_matches, any_other_name_like, url_matches, group_name, other_names_*, is_deleted, is_banned, has_tag, order=name/updated_at/post_count]` |
| `artist_show(artist_id)` | `GET artists/<id>.json` | 匿名 | `only` |
| `artist_show_or_new(name=None)` | `GET artists/show_or_new.json` | 匿名 | 顶层 `name`；名字已存在时服务端 302 到画师页面，跟随重定向后仍得到该画师的 JSON（已实测）；名字不存在时返回未保存的 artist 对象 |
| `artist_create(name, **attributes)` | `POST artists.json` | 需登录 | `artist[name, other_names_string, group_name, url_string, is_deleted]` |
| `artist_update(artist_id, **attributes)` | `PUT artists/<id>.json` | 需登录 | 同 `artist_create` |
| `artist_delete(artist_id)` | `DELETE artists/<id>.json` | 需登录 | 置 `is_deleted=true`；服务端 `redirect_to`（见下方重定向说明） |
| `artist_revert(artist_id, version_id)` | `PUT artists/<id>/revert.json` | 需登录 | 顶层 `version_id` |
| `artist_ban(artist_id)` | `PUT artists/<id>/ban.json` | 需 admin | 服务端 `redirect_to` |
| `artist_unban(artist_id)` | `PUT artists/<id>/unban.json` | 需 admin | 服务端 `redirect_to` |
| `artist_urls_list(search=None, **params)` | `GET artist_urls.json` | 匿名 | `search[id, url, url_matches, is_active, artist_id, order]` |
| `artist_versions_list(search=None, **params)` | `GET artist_versions.json` | 匿名 | `search[id, name, group_name, urls, other_names, updater_id, updater_name, artist_id, is_deleted, is_banned, order]` |
| `artist_version_show(version_id)` | `GET artist_versions/<id>.json` | 匿名 | — |
| `artist_commentaries_list(search=None, **params)` | `GET artist_commentaries.json` | 匿名 | `search[text_matches, post_id, post_tags_match, original_present, translated_present, is_deleted, order]` |
| `artist_commentary_show(post_id)` | `GET posts/<post_id>/artist_commentary.json` | 匿名 | 也可用 `GET artist_commentaries/<id>.json` |
| `artist_commentary_create_or_update(post_id, **attributes)` | `PUT posts/<post_id>/artist_commentary/create_or_update.json` | 需登录 | `artist_commentary[original_title, original_description, translated_title, translated_description, commentary_tags]`；必须是 PUT |
| `artist_commentary_revert(post_id, version_id)` | `PUT artist_commentaries/<post_id>/revert.json` | 需登录 | 路径里的 id 是 **post_id**；顶层 `version_id` |
| `artist_commentary_versions_list(search=None, **params)` | `GET artist_commentary_versions.json` | 匿名 | `search[post_id, updater_id, updater_name, text_matches, original_title, ...]` |
| `artist_commentary_version_show(version_id)` | `GET artist_commentary_versions/<id>.json` | 匿名 | — |

`url_matches` 支持四种形态：完整 `http(s)://` 地址（会走来源归一化）、`/正则/`、含 `*` 的通配、
普通子串。按 URL 查画师与 pixiv id → tag 的完整用法见 [danbooru-artists.md](danbooru-artists.md)。

> **关于重定向类端点**：`artist_delete`、`artist_ban`、`artist_unban`、`wiki_page_show_or_new`、
> `forum_topics_mark_all_as_read` 等动作在服务端是 `redirect_to`。客户端会跟随重定向，
> 最终拿到什么格式**取决于目标端点的格式协商**——因为客户端始终发送 `Accept: application/json`，
> 目标端点通常仍返回 JSON（已实测 `artist_show_or_new` 跟随重定向后拿到 `200` +
> `application/json`，见 [verification.md](verification.md)）。
> 写类重定向端点**未实测**，因此不断言成功或失败；若最终响应不是 JSON，会抛
> `PybooruAPIError`，此时用 `last_call['status_code']` 与 `last_call['url']` 判断实际结果。

## comments、notes、投票

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `comment_list(search=None, **params)` | `GET comments.json` | 匿名 | 顶层 `group_by`（`comment`/`post`，带 `search` 时默认 `comment`）、`tags`（`group_by=post` 时）；`search[id, body_matches, post_id, post_tags_match, creator_id, creator_name, updater_id, updater_name, is_deleted, score, do_not_bump_post, is_sticky, is_edited, order]` |
| `comment_show(comment_id)` | `GET comments/<id>.json` | 匿名 | — |
| `comment_create(post_id, body, **attributes)` | `POST comments.json` | 需登录 | `comment[post_id, body, do_not_bump_post, is_sticky]`（`is_sticky` 需 moderator） |
| `comment_update(comment_id, **attributes)` | `PUT comments/<id>.json` | 需登录（作者或 moderator） | `comment[body, is_deleted]` |
| `comment_delete(comment_id)` | `DELETE comments/<id>.json` | 需登录（作者或 moderator） | 软删除 |
| `comment_undelete(comment_id)` | `POST comments/<id>/undelete.json` | 需登录 | — |
| `comment_votes_list(search=None, **params)` | `GET comment_votes.json` | 匿名（受限） | `search[id, score, is_deleted, comment_id, user_id]`、顶层 `comment_id` 亦兼容 |
| `comment_vote_show(vote_id)` | `GET comment_votes/<id>.json` | 受限 | — |
| `comment_vote_create(comment_id, score)` | `POST comments/<comment_id>/votes.json` | 需登录 | 顶层 `score` |
| `comment_vote_delete(vote_id)` | `DELETE comment_votes/<id>.json` | 需登录 | 没有按 comment_id 撤销投票的路由 |
| `note_list(search=None, **params)` | `GET notes.json` | 匿名 | `search[id, is_active, x, y, width, height, body, version, post_id, post_tags_match]`；**没有** `creator_id`/`creator_name`，旧参数会被静默忽略 |
| `note_show(note_id)` | `GET notes/<id>.json` | 匿名 | — |
| `note_create(post_id, x, y, width, height, body, **attributes)` | `POST notes.json` | 需登录 | `note[post_id, x, y, width, height, body]`；失败时 422 `{success:false, reasons:[...]}` |
| `note_update(note_id, **attributes)` | `PUT notes/<id>.json` | 需登录 | `note[x, y, width, height, body]` |
| `note_delete(note_id)` | `DELETE notes/<id>.json` | 需登录 | 置 `is_active=false` |
| `note_revert(note_id, version_id)` | `PUT notes/<id>/revert.json` | 需登录 | 顶层 `version_id` |
| `note_preview(body)` | `POST notes/preview.json`（GET 亦可） | 匿名 | 顶层 `body`；返回 `sanitized_body` |
| `note_versions_list(search=None, **params)` | `GET note_versions.json` | 匿名 | `search[id, is_active, x, y, width, height, body, version, note_id, post_id, updater_id, updater_name]` |
| `note_version_show(version_id)` | `GET note_versions/<id>.json` | 匿名 | — |

评论可见性：非 moderator 时，已删除评论不返回 `creator_id`/`updater_id`/`body`/`score`/
`do_not_bump_post`/`is_sticky`，且按这些字段检索会被限制为“自己的删除评论 + 全部未删除”。

## pools（合集）

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `pool_list(search=None, **params)` | `GET pools.json` | 匿名 | `search[id, name, name_contains, description, post_ids, is_deleted, post_tags_match, linked_to, not_linked_to, category=series/collection, order=name/created_at/post_count]` |
| `pool_show(pool_id)` | `GET pools/<id>.json` | 匿名 | `page`、`limit`；`post_ids` 是 id 数组 |
| `pool_create(name, **attributes)` | `POST pools.json` | 需登录 | `pool[name, description, category, post_ids]` |
| `pool_update(pool_id, **attributes)` | `PUT pools/<id>.json` | 需登录 | 同上 |
| `pool_delete(pool_id)` | `DELETE pools/<id>.json` | 需 builder | 软删除 |
| `pool_undelete(pool_id)` | `POST pools/<id>/undelete.json` | 需 builder | — |
| `pool_revert(pool_id, version_id)` | `PUT pools/<id>/revert.json` | 需登录 | 顶层 `version_id` |
| `pool_gallery(search=None, **params)` | `GET pools/gallery.json` | 匿名 | `search[...]`（默认 `category=series`） |
| `pool_element_create(post_id, pool_id=None, pool_name=None)` | `POST pool_element.json` | 需登录（有该 pool 的更新权限） | 顶层 `post_id`、`pool_id` 或 `pool_name` |
| `pool_versions_list(search=None, **params)` | `GET pool_versions.json` | 匿名（能力依赖） | `search[id, pool_id, post_ids, added_post_ids, removed_post_ids, updater_id, updater_name, description, name, version, is_active, is_deleted, category]`；未配置 archive 服务时 501 |
| `pool_version_diff(pool_version_id, other_id=None, type=None)` | `GET pool_versions/<id>/diff.json` | 匿名 | 顶层 `other_id`、`type` |

## wiki

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `wiki_page_list(search=None, **params)` | `GET wiki_pages.json` | 匿名 | `search[id, title, title_normalize, title_or_body_matches, body, body_matches, other_names_*, other_names_present, is_deleted, is_locked, hide_deleted, linked_to, not_linked_to, embedded_post_id, embedded_media_asset_id, order=title/post_count]`；**顶层 `title=` 会 302 到标题搜索** |
| `wiki_page_show(id_or_title)` | `GET wiki_pages/<id 或标题>.json` | 匿名 | 标题不存在时 404 |
| `wiki_page_create(title, **attributes)` | `POST wiki_pages.json` | 需登录 | `wiki_page[title, body, other_names, other_names_string, is_locked(builder)]` |
| `wiki_page_update(wiki_page_id, **attributes)` | `PUT wiki_pages/<id 或标题>.json` | 需登录 | 同上 + `wiki_page[is_deleted]` |
| `wiki_page_delete(wiki_page_id)` | `DELETE wiki_pages/<id 或标题>.json` | 需登录 | 软删除并返回对象 |
| `wiki_page_revert(wiki_page_id, version_id)` | `PUT wiki_pages/<id 或标题>/revert.json` | 需登录 | 顶层 `version_id` |
| `wiki_page_show_or_new(title=None)` | `GET wiki_pages/show_or_new.json` | 匿名 | 顶层 `title`；服务端 302 到页面 |
| `wiki_page_versions_list(search=None, **params)` | `GET wiki_page_versions.json` | 匿名 | `search[id, title, body, other_names, is_locked, is_deleted, updater_id, updater_name, wiki_page_id, order]` |
| `wiki_page_version_show(version_id)` | `GET wiki_page_versions/<id>.json` | 匿名 | — |
| `wiki_page_versions_diff(thispage=None, otherpage=None, type=None)` | `GET wiki_page_versions/diff.json` | 匿名 | 顶层 `thispage`、`otherpage`、`type` |

## users、收藏、收藏分组

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `user_list(search=None, **params)` | `GET users.json` | 匿名 | 顶层 `name`、`redirect`；`search[id, name, name_matches, any_name_matches, name_or_past_name_matches, level, min_level, max_level, is_banned, is_deleted, post_upload_count, post_update_count, note_update_count, favorite_count, order=name/post_upload_count/note_count/post_update_count]`；注意 `search[name]` 在 User 上会被改写成模糊的 `name_matches` |
| `user_show(user_id)` | `GET users/<id>.json` | 匿名 | `only`；本人可见更多字段 |
| `user_create(name, password, password_confirmation)` | `POST users.json` | 匿名（站点侧有验证码/邀请检查） | — |
| `user_update(user_id, **attributes)` | `PUT users/<id>.json` | 需登录（只能改自己） | `user[comment_threshold, default_image_size, favorite_tags, blacklisted_tags, time_zone, per_page, ...]` |
| `user_actions_list(search=None, **params)` | `GET user_actions.json` / `GET users/<user_id>/actions.json` | 需 moderator | `search[event_type, user_id, user_name, model_type, model_id]`、顶层 `user_id` |
| `user_action_show(user_action_id)` | `GET user_actions/<id>.json` | 需 moderator | — |
| `user_events_list(search=None, **params)` | `GET user_events.json` / `GET users/<user_id>/events.json` | 匿名（内容受限） | `search[id, category, user_id, ip_addr, session_id, user_agent]`；非 moderator 看不到 `session_id`/`user_agent` |
| `user_feedbacks_list(search=None, **params)` | `GET user_feedbacks.json` | 受限 | `search[id, category, body, is_deleted, creator_id, user_id]` |
| `user_feedback_show(feedback_id)` | `GET user_feedbacks/<id>.json` | 受限 | — |
| `user_feedback_create(**attributes)` | `POST user_feedbacks.json` | 需登录 | `user_feedback[body, category, user_id, user_name]` |
| `user_feedback_update(feedback_id, **attributes)` | `PUT user_feedbacks/<id>.json` | 需登录 | `user_feedback[body, category, is_deleted]` |
| `user_name_change_requests_list(search=None, **params)` | `GET user_name_change_requests.json` | 非匿名 | `search[user_id, original_name, desired_name]` |
| `user_name_change_request_show(request_id)` | `GET user_name_change_requests/<id>.json` | 非匿名 | — |
| `user_name_change_request_create(**attributes)` | `POST user_name_change_requests.json` | 需登录 | `user_name_change_request[user_id, desired_name]` |
| `favorite_list(search=None, **params)` | `GET favorites.json` | 匿名（只看得到公开收藏） | 顶层 `post_id`、`user_id`；`search[post_id, user_id, user_name]` |
| `favorite_create(post_id)` | `POST favorites.json` | 需登录（member） | 顶层 `post_id`；返回该 post 对象 |
| `favorite_delete(post_id)` | `DELETE favorites/<post_id>.json` | 需登录（本人） | 路径里的 id 就是 post_id |
| `favorite_groups_list(search=None, **params)` | `GET favorite_groups.json` / `GET users/<user_id>/favorite_groups.json` | 受限 | 顶层 `user_id`；`search[id, name, is_public, post_ids, creator_id, creator_name]` |
| `favorite_group_show(group_id)` | `GET favorite_groups/<id>.json` | 受限 | `page`、`limit` |
| `favorite_group_create(name, **attributes)` | `POST favorite_groups.json` | 需登录 | `favorite_group[name, post_ids_string, is_public, is_private, post_ids]` |
| `favorite_group_update(group_id, **attributes)` | `PUT favorite_groups/<id>.json` | 需登录 | 同上 |
| `favorite_group_delete(group_id)` | `DELETE favorite_groups/<id>.json` | 需登录 | — |
| `favorite_group_add_post(group_id, post_id)` | `PUT favorite_groups/<id>/add_post.json` | 需登录 | 顶层 `post_id` |
| `favorite_group_remove_post(group_id, post_id)` | `PUT favorite_groups/<id>/remove_post.json` | 需登录 | 顶层 `post_id` |

User 的字段级可见性最强：匿名只能拿到 `id`、`created_at`、`name`、`inviter_id`、`level`、
`level_string`、各类计数与 `is_banned`/`is_deleted`；本人才能看到偏好设置等字段。

## forum（论坛）

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `forum_topics_list(search=None, **params)` | `GET forum_topics.json` | 匿名（按 `min_level` 过滤） | `search[id, title, title_matches, category, category_id, is_sticky, is_locked, is_deleted, min_level, response_count, creator_id, creator_name, order]`；顶层 `title`/`title_matches` 会折进 `search` |
| `forum_topic_show(topic_id)` | `GET forum_topics/<id>.json` | 匿名（等级限制） | `page`、`limit`；内嵌 `forum_posts` |
| `forum_topic_create(title, body, **attributes)` | `POST forum_topics.json` | 需登录 | `forum_topic[title, category_id, original_post_attributes][body]`；`is_sticky`/`is_locked`/`min_level` 需 moderator |
| `forum_topic_update(topic_id, **attributes)` | `PUT forum_topics/<id>.json` | 需登录 | 同上 |
| `forum_topic_delete(topic_id)` | `DELETE forum_topics/<id>.json` | 需 moderator | 软删除 |
| `forum_topic_undelete(topic_id)` | `POST forum_topics/<id>/undelete.json` | 需 moderator | — |
| `forum_topics_mark_all_as_read()` | `POST forum_topics/mark_all_as_read.json` | 需登录 | 服务端 `redirect_to`（见 artists 表下方的重定向说明） |
| `forum_posts_list(search=None, **params)` | `GET forum_posts.json` | 匿名 | `search[id, body, is_deleted, creator_id, creator_name, topic_id, topic_title_matches, topic_category_id, linked_to]` |
| `forum_post_show(post_id)` | `GET forum_posts/<id>.json` | 匿名（不返回已删） | — |
| `forum_post_create(topic_id, body)` | `POST forum_posts.json` | 需登录 | `forum_post[topic_id, body]` |
| `forum_post_update(post_id, body)` | `PUT forum_posts/<id>.json` | 需登录（作者/mod） | `forum_post[body]` |
| `forum_post_delete(post_id)` | `DELETE forum_posts/<id>.json` | 需 moderator | — |
| `forum_post_undelete(post_id)` | `POST forum_posts/<id>/undelete.json` | 需 moderator | — |
| `forum_post_votes_list(search=None, **params)` | `GET forum_post_votes.json` | 匿名 | `search[id, score, creator_id, creator_name, forum_post_id]` |
| `forum_post_vote_show(vote_id)` | `GET forum_post_votes/<id>.json` | 受限 | — |
| `forum_post_vote_create(forum_post_id, score)` | `POST forum_post_votes.json` | 需登录 | 顶层 `forum_post_id`；`forum_post_vote[score]` |
| `forum_post_vote_delete(vote_id)` | `DELETE forum_post_votes/<id>.json` | 需登录（本人） | — |
| `forum_topic_visits_list(search=None, **params)` | `GET forum_topic_visits.json` | 受限（本人） | `search[user_id, forum_topic_id, last_read_at]` |

## dmails（站内信）

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `dmail_list(search=None, **params)` | `GET dmails.json` | 需登录（只能看自己的） | `search[id, title, body, message_matches, is_read, is_deleted, to_id, to_name, from_id, from_name, folder]` |
| `dmail_show(dmail_id)` | `GET dmails/<id>.json` | 需登录（本人） | 也支持 `key=` 签名链接 |
| `dmail_create(title, body, to_name=None, to_id=None)` | `POST dmails.json` | 需登录 | `dmail[to_name, to_id, title, body]` |
| `dmail_update(dmail_id, **attributes)` | `PUT dmails/<id>.json` | 需登录（本人） | `dmail[is_read, is_deleted]`；**删除邮件也走这里** |
| `dmails_mark_all_as_read()` | `POST dmails/mark_all_as_read.json` | 需登录 | — |

## 审核与运维

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `ban_list(search=None, **params)` | `GET bans.json` | 匿名 | `search[id, duration, reason, user_id, banner_id, banner_name, expired]` |
| `ban_show(ban_id)` | `GET bans/<id>.json` | 匿名 | — |
| `ban_create(**attributes)` | `POST bans.json` | 需 moderator | `ban[reason, duration, user_id, user_name, delete_posts, ...]` |
| `ban_update(ban_id, **attributes)` | `PUT bans/<id>.json` | 需 moderator | `ban[reason, duration]` |
| `ban_delete(ban_id)` | `DELETE bans/<id>.json` | 需 moderator | 解除封禁 |
| `bulk_update_requests_list(search=None, **params)` | `GET bulk_update_requests.json` | 匿名 | `search[id, script, tags, user_id, user_name, status, approver_id, forum_topic_id, forum_post_id, order]` |
| `bulk_update_request_show(request_id)` | `GET bulk_update_requests/<id>.json` | 匿名 | — |
| `bulk_update_request_create(script, **attributes)` | `POST bulk_update_requests.json` | 需登录 | `bulk_update_request[script, title, reason, forum_topic_id]`；**别名/蕴含的正规创建入口** |
| `bulk_update_request_update(request_id, **attributes)` | `PUT bulk_update_requests/<id>.json` | 需登录（本人） | 同上 |
| `bulk_update_request_approve(request_id)` | `POST bulk_update_requests/<id>/approve.json` | 需 approver | — |
| `bulk_update_request_delete(request_id)` | `DELETE bulk_update_requests/<id>.json` | 需登录（本人/mod） | 语义是拒绝 |
| `ip_bans_list(search=None, **params)` | `GET ip_bans.json` | 需 moderator+ | `search[id, ip_addr, reason, category, is_deleted, hit_count, last_hit_at, creator_id]` |
| `ip_ban_show(ip_ban_id)` | `GET ip_bans/<id>.json` | 需 moderator+ | — |
| `ip_ban_create(**attributes)` | `POST ip_bans.json` | 需 moderator+ | `ip_ban[ip_addr, reason, is_deleted, category]` |
| `ip_ban_update(ip_ban_id, **attributes)` | `PUT ip_bans/<id>.json` | 需 moderator+ | 同 `ip_ban_create` |
| `ip_address_show(ip_addr)` | `GET ip_addresses/<ip>.json` | 需 moderator+ | 路径里的 id 是 IP 字符串 |
| `ip_geolocations_list(search=None, **params)` | `GET ip_geolocations.json` | 需 moderator+ | `search[id, ip_addr, network, asn, country, city, ...]` |
| `mod_actions_list(search=None, **params)` | `GET mod_actions.json` | 匿名（`show` 对非 moderator 排除敏感类目） | `search[id, category, description, creator_id, creator_name, subject_type, subject_id, order]` |
| `mod_action_show(mod_action_id)` | `GET mod_actions/<id>.json` | 受限 | — |
| `modqueue_list(search=None, **params)` | `GET modqueue.json` | 需 approver | 顶层 `mode`（默认 `gallery`）、`limit`（默认每页数，上限 200）、`size`；`search[order]`（默认 `modqueue`）、`search[tags]`；返回**帖子列表** JSON |
| `moderation_reports_list(search=None, **params)` | `GET moderation_reports.json` | 非匿名（非 mod 只看自己） | `search[id, reason, creator_id, creator_name, model_type, model_id, status, recipient_id]` |
| `moderation_report_show(report_id)` | `GET moderation_reports/<id>.json` | 非匿名 | — |
| `moderation_report_create(**attributes)` | `POST moderation_reports.json` | 需登录 | `moderation_report[model_type, model_id, reason]` |
| `moderation_report_update(report_id, **attributes)` | `PUT moderation_reports/<id>.json` | 需 moderator | `moderation_report[status]` |
| `news_updates_list(search=None, **params)` | `GET news_updates.json` | 需 admin | `search[id, message, creator_id, updater_id]` |
| `news_update_show(news_update_id)` | `GET news_updates/<id>.json` | 需 admin | — |
| `news_update_create(message, **attributes)` | `POST news_updates.json` | 需 admin | `news_update[message, duration, duration_in_days]` |
| `news_update_update(news_update_id, **attributes)` | `PUT news_updates/<id>.json` | 需 admin | 同上 |
| `news_update_delete(news_update_id)` | `DELETE news_updates/<id>.json` | 需 admin | 软删除 |
| `saved_searches_list(search=None, **params)` | `GET saved_searches.json` | 需登录 | `search[id, query, label]` |
| `saved_search_create(**attributes)` | `POST saved_searches.json` | 需登录 | `saved_search[query, label_string]` |
| `saved_search_update(saved_search_id, **attributes)` | `PUT saved_searches/<id>.json` | 需登录（本人） | 同上 |
| `saved_search_delete(saved_search_id)` | `DELETE saved_searches/<id>.json` | 需登录（本人） | — |
| `site_credentials_list(search=None, **params)` | `GET site_credentials.json` | 需 admin | `search[id, site, is_enabled, is_public, status, creator_id, usage_count]` |
| `site_credential_show(site_credential_id)` | `GET site_credentials/<id>.json` | 公开项需 admin / 私有项需本人 | — |
| `site_credential_create(site, **attributes)` | `POST site_credentials.json` | 需 admin | `site_credential[site, is_enabled, credential]` |
| `site_credential_update(site_credential_id, **attributes)` | `PUT site_credentials/<id>.json` | 需 admin / 本人 | `site_credential[is_enabled]` |
| `site_credential_delete(site_credential_id)` | `DELETE site_credentials/<id>.json` | 公开项需 owner / 私有项需本人 | — |
| `reactions_list(search=None, **params)` | `GET reactions.json` | 受限 | `search[id, creator_id, model_type, model_id, reaction_id]` |
| `reaction_show(reaction_id)` | `GET reactions/<id>.json` | 受限 | — |
| `reaction_create(**attributes)` | `POST reactions.json` | 需登录 | `reaction[model_type, model_id, reaction_id]` |
| `reaction_delete(reaction_id)` | `DELETE reactions/<id>.json` | 需登录 | — |
| `report_show(report, search=None, **params)` | `GET reports/<report>.json` | 匿名 | `search[mode, period, from, to, columns, group, group_limit]` |
| `jobs_list(search=None, **params)` | `GET jobs.json` | 匿名 | `search[id, queue_name, job_class, error, scheduled_at, finished_at, active_job_id, cron_key, labels]`；非 admin 看不到 `serialized_params` |
| `job_cancel(job_id)` | `PUT jobs/<id>/cancel.json` | 需 admin | job id = `active_job_id` |
| `job_retry(job_id)` | `PUT jobs/<id>/retry.json` | 需 admin | — |
| `job_run(job_id)` | `PUT jobs/<id>/run.json` | 需 admin | — |
| `job_delete(job_id)` | `DELETE jobs/<id>.json` | 需 admin | — |
| `dtext_links_list(search=None, **params)` | `GET dtext_links.json` | 匿名 | `search[id, link_type, link_target, model_type, model_id, linked_wiki, linked_tag]` |
| `recommended_posts_list(search=None, **params)` | `GET recommended_posts.json` | 匿名 | `limit` ≤ 200；`search[...]` 透传给推荐服务 |

## 杂项

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `counts_posts(tags=None, estimate_count=None, skip_cache=None)` | `GET counts/posts.json` | 匿名 | 顶层 `tags`、`estimate_count`、`skip_cache`；返回 `{"counts":{"posts":N}}` |
| `source_show(url, ref=None, mode=None)` | `GET source.json` | 匿名 | 顶层 `url`、`ref`、`mode` |
| `iqdb_query(**params)` | `GET iqdb_queries.json`（同一 action 也接受 `POST`） | 匿名（能力依赖） | `search[url, hash, image_url, file_url, post_id, media_asset_id, limit, similarity]`，裸参数亦兼容 |

## 可调用但没有原生方法的 JSON 路由

这些路由是正常的 JSON 端点，只是没有对应的原生方法，用
`request(method, path, params=..., data=...)` 访问即可：

| 路由 | 凭据 | 说明 |
| :--- | :--- | :--- |
| `GET metrics.json`、`GET statistics.json`、`GET metrics/statistics.json`、`GET metrics/instance.json` | 匿名 | 默认格式是 text，显式 `.json` 可用 |
| `GET emails.json` | 需 moderator+ | `search[user_id, address, is_verified, is_deliverable]` |
| `GET emails/<id>.json` | 本人或 moderator | — |
| `GET|PUT|DELETE users/<user_id>/email.json` | 需登录 + 重新认证 | 顶层 `emails` 资源只有 `index`/`show` |
| `GET users/<user_id>/email/verify.json`、`POST .../send_confirmation.json` | 需登录 | — |
| `GET password/edit.json`、`PUT password.json`、`GET users/<user_id>/password/edit.json`、`PUT users/<user_id>/password.json` | 需登录 | `user[current_password, password, password_confirmation, verification_code]` |
| `PUT password_reset.json` | 持签名 `signed_id` | `user[signed_id, password, password_confirmation]` |
| `GET users/<user_id>/totp/edit.json`、`PUT|DELETE users/<user_id>/totp.json` | 本人 + 重新认证 | `totp[signed_secret, verification_code]` |
| `GET|POST users/<user_id>/backup_codes.json`、`GET users/<user_id>/backup_codes/confirm_recover.json`、`POST .../recover.json` | 本人 + 重新认证 | — |
| `GET upgrade_codes.json` | 需 owner | `search[code, status, creator_id, redeemer_id]` |
| `POST upgrade_codes/upgrade.json` | 需登录 | `upgrade_code[code]` |
| `GET user_upgrades.json`、`GET user_upgrades/<id>.json` | 需登录（visible 过滤） | `search[id, upgrade_type, status, transaction_id, recipient_id, purchaser_id]` |
| `GET upgrade.json` | 匿名 | `user_id` 选择收件人，返回未保存的 UserUpgrade；`GET user_upgrades/new` 是到此的重定向 |
| `POST user_upgrades.json`、`PUT user_upgrades/<id>/refund.json` | 非匿名 / owner | `upgrade_type`、`payment_processor`、`country`、`promo` |
| `GET pools/<pool_id>/order/edit.json` | 需登录（pool 更新权限） | 返回 pool，用于排序编辑 |
| `GET favorite_groups/<id>/order/edit.json` | 需登录 | 返回 favorite group |
| `POST moderator/post/posts/<id>/ban.json`、`/unban.json` | 需 approver+ | 返回该 post |
| `GET post/index.json`、`GET tag/index.json` | 匿名 | Danbooru 1 遗留 API，字段集与 `/posts.json` 不同（`has_comments`、`status`、`author`、`file_url` 等） |
| `GET up.json`、`/up/postgres`、`/up/redis` | 匿名 | 健康检查，`head 204/503`，无响应体 |

### 初始化、编辑与嵌套路由

`new` / `edit` 并不天然是 HTML-only。以下控制器动作显式 `respond_with`，在已有 `.json` 路由上可返回对象，均未实测；用 `request()` 调用。`new` 权限继承该资源的 `create?`，`edit` 继承 `update?`，API keys 仍需重新认证。初始化参数使用对应创建方法的属性命名空间，详情编辑路径用资源 ID；两者均不分页。

| 路径模式（全部 GET，后缀 `.json`） | 已有资源 / 控制器 |
| :--- | :--- |
| `<资源>/new` 和 `<资源>/<id>/edit` | `api_keys`、`artists`、`bans`、`bulk_update_requests`、`comments`、`favorite_groups`、`forum_posts`、`forum_topics`、`news_updates`、`pools`、`post_appeals`、`post_flags`、`user_feedbacks`、`users`、`wiki_pages` |
| `<资源>/new` | `dmails`、`ip_bans`、`moderation_reports`、`post_replacements`、`site_credentials`、`uploads`、`user_name_change_requests` |
| `<资源>/<id>/edit` | `post_disapprovals`、`saved_searches`、`tags` |

证据入口：对应 `app/controllers/<资源>_controller.rb` 的 `new`/`edit` 与 `ApplicationPolicy` 第 23–36 行；`site_credentials_controller.rb:18-20` 明确 `respond_with`，不是 HTML-only。`uploads/new` 还接受顶层 `url`、`ref`；`dmails/new` 支持 `respond_to_id`、`forward`；`comments/new` 支持引用评论的 `id`；`users/new` 接受 `user[url]` 或 `url`。具体预填字段均服从相应 policy。

上文资源还存在下列嵌套形式，与对应顶层控制器共享参数、分页和权限；`request()` 可以直接调用，无须新建客户端子类：

* `/posts/<post_id>/events`、`/posts/<post_id>/favorites`、`/posts/<post_id>/replacements`、`/posts/<post_id>/replacements/new`；
* `/uploads/<upload_id>/assets/<id>`；
* `/users/<user_id>/actions`、`favorites`、`favorite_groups`、`uploads`、`events`；
* `/users/<user_id>/api_keys` 以及 `new` / `<id>/edit` / `<id>` 的创建、更新、删除，动作与顶层 API key 资源相同；
* `GET /users/<id>/change_name` 同 `user_name_change_requests#new`；
* `GET /comments/<comment_id>/votes` 同 `comment_votes#index`；`POST /post_votes` 接受顶层 `post_id` / `score`，等价于原生嵌套投票方法。

注意 `DELETE /posts/<post_id>/votes` 和 `DELETE /comments/<comment_id>/votes` 虽然在路由中存在，但控制器读取的是 `params[:id]`（单数嵌套路径不提供它）；撤票使用上文原生 `post_vote_delete(vote_id)` / `comment_vote_delete(vote_id)`，不使用这两个缺少标识的动作。收藏删除则以 post ID 为标识，走 `favorite_delete(post_id)`。

### explore（发现内容）

以下均为真实 JSON 动作，未实测。来源：`routes.rb:37-46`、`app/controllers/explore/posts_controller.rb:7-52`；权限见 `ExplorePostPolicy`。不使用模型 `search` 字典。

| GET 路径（后缀 `.json`） | 参数与返回 |
| :--- | :--- |
| `explore/posts/popular` | 顶层 `date`、`scale=day/week/month`、`page`、`limit`；按日期范围返回高分帖子 |
| `explore/posts/viewed` | 顶层 `date`、`scale`；Reportbooru 浏览热度帖子 |
| `explore/posts/searches` | 顶层 `date`、`scale`；Reportbooru 搜索排名 |
| `explore/posts/missed_searches` | Reportbooru 未命中搜索排名 |

后三项依赖站点 Reportbooru 服务配置，库不添加兜底。原生 `*_show(id)` 若没有 `**params` 形参，而该路由还接受 `only`、分页、签名 key 等参数，请用 `request('GET', '<资源>/<id>.json', params={...})` 传递。

## 排除项（不作为端点使用）

### 控制器没有 JSON 响应

| 路由 | 原因 |
| :--- | :--- |
| `sessions` 全部动作（`/session*`、`/login`、`/logout`、`confirm_password`、`reauthenticate`、`verify_totp`） | `respond_to :html`，浏览器会话流程 |
| `admin/users#edit|update`、`maintenance/user/count_fixes#new|create` | 无 `respond_to`，只有 HTML 模板或重定向 |
| `dmcas#show|create|template`（`/dmca*`） | 无 `respond_to`，也没有对应视图目录 |
| `webhooks#receive` | 恒 `head 400` |

### `respond_to` 含 json，但视图层面不是 JSON

* `reports#index`（`GET reports.json`）：只有 `.html.erb`（注意 `GET reports/<id>.json` 是正常 JSON）；
* `post_versions/search`、`pool_versions/search`、`forum_posts/search`：只有 `.html.erb`；
* `static` 站点页面：`privacy`、`terms_of_service`、`contact`、`site_map`、`opensearch` 等；
* `moderator/post/posts/<id>/expunge`（仅 `.js.erb`）、`confirm_move_favorites`（仅 `.html.erb`）；
* `upgrade_codes/redeem`、`password_reset`（GET/edit）、`dtext_preview`：响应是 HTML 字符串；
* `robots`：`respond_to :text`。

### 纯重定向

`/artist`、`/artist/show/:id`、`/artist/show`、`/forum`、`/forum/show/:id`、`/pool/show/:id`、
`/post/index`、`/post/show/:id`、`/tag`、`/tag/index`、`/user/show/:id`、`/wiki/show`、`/help/:title`、
`/uploads/batch`、`/iqdb_queries/check`、`/comments/search`、`/user_upgrades/new`（→ `/upgrade`）、
`/user_upgrades/<id>/receipt|payment`、`/moderator/post/posts/<id>/move_favorites` 等历史与便利跳转。

### mock 与挂载引擎

`/mock/**`（非 local 环境直接 403）、`mount GoodJob::Engine => "good_job"`。

### 路由存在但控制器没有对应动作

`GET /counts`、`/tags/new`、`POST /tags`、`DELETE /tags/<id>`、`PUT|DELETE /uploads/<id>`、
`/mod_actions/new|edit|create|update|destroy`、`DELETE /post_flags/<id>`、`DELETE /post_appeals/<id>`、
`DELETE /post_disapprovals/<id>`、`PUT /related_tag`、`/iqdb_queries/preview`、
`GET /posts/<post_id>/similar` 等。

这些路径**不能作为端点使用**；具体返回哪个状态码取决于框架层的错误处理，**未经线上验证，不做声明**。

## 验证状态

匿名只读验证已执行（2026-09-15，站点 `danbooru.donmai.us`，代理 + 项目 venv，无凭据），
共 15 次请求：12 次 `200`、3 次预期失败（`404` / `410` / `422`）；另外单独验证了重定向端点
`artist_show_or_new`（302 → JSON）。完整记录见 [verification.md](verification.md)。

**已实测**（匿名只读）的端点：

* `post_list`（含 `tags` 搜索与 `page=b<id>` 游标）、`post_show`
* `tag_list`（`search[name_matches]`）
* `artist_list`（`search[url_matches]` + `is_deleted` / `is_banned` / `has_tag` / `order`，以及 `any_name_matches`）
* `artist_show_or_new`（重定向后仍返回 JSON）
* `related_tag`（`search` 五个参数 + 顶层 `limit`）
* `wiki_page_list`、`wiki_page_show`（按标题）
* `comment_list`、`pool_list`
* 错误路径：`404`、`410`（页码超限）、`422`（标签数超限）

其余端点（尤其是**全部写接口**与 Moebooru 面）仍为源码对齐、**未实测**。
