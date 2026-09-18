# Danbooru 契约审计附注

面向维护者与契约核对者。用户页（[用法](danbooru.md)、[方法参考](danbooru-api.md)、
[能力入口](danbooru-capabilities.md)）只保留可操作的事实；上游行号、权限过滤器、源码与文档的矛盾、
SQL 与缓存行为、排除项和逐条状态记在这里。

审计依据：本地只读 clone `danbooru/`，HEAD `d4cdddd44`（2026-09-14）。权威来源是
`config/routes.rb`（路由）、`app/controllers/*`（动作与强参数）、`app/policies/*`（权限与字段过滤）、
`app/models/*`（搜索与校验）。客户端侧依据是 `anybooru/api_danbooru.py`（227 个原生方法）与
`anybooru/danbooru.py`（传输）。**本文行号都指该 clone 的当前版本**，上游更新后需重新核对。

## 状态口径与总量

* 客户端原生方法 **227 个**（`api_danbooru.py` 中 `DanbooruApi_Mixin` 的函数总数），逐条见下一节。
* **已实测（匿名只读，2026-09-15，`danbooru.donmai.us` 经代理）**：`post_list`、`post_show`、
  `tag_list`、`artist_list`、`artist_show_or_new`、`related_tag`、`wiki_page_list`、
  `wiki_page_show`、`comment_list`、`pool_list`，共 10 个。三条错误路径（`404` 帖子不存在、
  `410` 页码超限、`422` 标签数超限）与 `artist_show_or_new` 的 302 → JSON 也实测过。
* **源码对齐、未实测**：早期 15 次验证没有覆盖其余 217 个方法；写接口与高权限/重新认证动作始终未发请求。
  之后 Safebooru 与候选站的独立读路径探测见 [verification.md](verification.md)，不能再泛称其他站点全部未测。
  上传与媒体链路、archive/IQDB/推荐等可选能力仍没有成功路径实测。
* 「已实测」只覆盖当时那次调用用到的参数组合；同一方法换参数、换身份、换站点都不算已验证。

## 逐资源：路由、参数键与状态（227 个原生方法）

方法名、路由与参数键都从 `anybooru/api_danbooru.py` 读取：路由是方法内 `self.request(...)` 调用的字面量
（路径变量写成 `<id>`），参数键与括注直接摘自该方法的 docstring（英文原文，保留以不丢枚举值等事实）；
状态列的口径见上一节。带类型、取值范围、含义、不传时行为与可抄示例的**用户向参数表**在
[方法参考](danbooru-api.md) 的对应小节，本节只保留源码原文与状态，避免两处漂移。

<a id="sec-status"></a>

### 状态、账号与限流（6 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `status()` | `GET status.json` | — | 源码对齐，未实测（读） |
| `api_keys_list(search=None, **params)` | `GET api_keys.json` | requires login | 源码对齐，未实测（写/需权限） |
| `api_key_create(**attributes)` | `POST api_keys.json` | requires login | 源码对齐，未实测（写/需权限） |
| `api_key_update(api_key_id, **attributes)` | `PUT api_keys/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `api_key_delete(api_key_id)` | `DELETE api_keys/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `rate_limits_list(search=None, **params)` | `GET rate_limits.json` | — | 源码对齐，未实测（读） |

参数键：

- `status()` — 无参数（路径变量除外）
- `api_keys_list(search=None, **params)` — 无参数（路径变量除外）
- `api_key_create(**attributes)` — 顶层/属性：`name`（The name of the key）、`permitted_ip_addresses`（Space-separated allowed IP ranges）
- `api_key_update(api_key_id, **attributes)` — 顶层/属性：`attributes`（同对应的 create 方法（源码 docstring 用 see 引用））
- `api_key_delete(api_key_id)` — 无参数（路径变量除外）
- `rate_limits_list(search=None, **params)` — search：id, action, key, limited, points；顶层/属性：`limit`（Limits per page）

<a id="sec-posts"></a>

### posts（帖子、投票、替换、批准与申诉）（37 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `post_list(**params)` | `GET posts.json` | — | 已实测（匿名只读） |
| `post_show(post_id)` | `GET posts/<id>.json` | — | 已实测（匿名只读） |
| `post_random(tags=None)` | `GET posts/random.json` | — | 源码对齐，未实测（读） |
| `post_create(upload_media_asset_id, **attributes)` | `POST posts.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_update(post_id, **attributes)` | `PUT posts/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_delete(post_id, reason, move_favorites=None)` | `DELETE posts/<id>.json` | requires approver level and above | 源码对齐，未实测（写/需权限） |
| `post_revert(post_id, version_id)` | `PUT posts/<id>/revert.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_copy_notes(post_id, other_post_id)` | `PUT posts/<id>/copy_notes.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_mark_as_translated(post_id, check_translation=None, partially_translated=None)` | `PUT posts/<id>/mark_as_translated.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_events_list(search=None, **params)` | `GET post_events.json` | — | 源码对齐，未实测（读） |
| `post_versions_list(search=None, **params)` | `GET post_versions.json` | requires the archive service | 源码对齐，未实测（读，依赖 archive 服务） |
| `post_version_undo(version_id)` | `PUT post_versions/<id>/undo.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_votes_list(search=None, **params)` | `GET post_votes.json` | — | 源码对齐，未实测（读） |
| `post_vote_show(vote_id)` | `GET post_votes/<id>.json` | — | 源码对齐，未实测（读） |
| `post_vote_create(post_id, score)` | `POST posts/<id>/votes.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_vote_delete(vote_id)` | `DELETE post_votes/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_favorites_list(post_id, search=None, **params)` | `GET posts/<id>/favorites.json` | — | 源码对齐，未实测（读） |
| `post_replacements_list(search=None, **params)` | `GET post_replacements.json` | — | 源码对齐，未实测（读） |
| `post_replacement_show(replacement_id)` | `GET post_replacements/<id>.json` | — | 源码对齐，未实测（读） |
| `post_replacement_create(post_id, replacement_file=None, **attributes)` | `POST post_replacements.json` | requires moderator | 源码对齐，未实测（写/需权限） |
| `post_replacement_update(replacement_id, **attributes)` | `PUT post_replacements/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_regeneration_create(post_id, category=None)` | `POST post_regenerations.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `post_approvals_list(search=None, **params)` | `GET post_approvals.json` | — | 源码对齐，未实测（读） |
| `post_approval_show(approval_id)` | `GET post_approvals/<id>.json` | — | 源码对齐，未实测（读） |
| `post_approval_create(post_id)` | `POST post_approvals.json` | requires approver level | 源码对齐，未实测（写/需权限） |
| `post_disapprovals_list(search=None, **params)` | `GET post_disapprovals.json` | — | 源码对齐，未实测（读） |
| `post_disapproval_show(disapproval_id)` | `GET post_disapprovals/<id>.json` | — | 源码对齐，未实测（读） |
| `post_disapproval_create(post_id, **attributes)` | `POST post_disapprovals.json` | requires approver level | 源码对齐，未实测（写/需权限） |
| `post_disapproval_update(disapproval_id, **attributes)` | `PUT post_disapprovals/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_flags_list(search=None, **params)` | `GET post_flags.json` | — | 源码对齐，未实测（读） |
| `post_flag_show(flag_id)` | `GET post_flags/<id>.json` | — | 源码对齐，未实测（读） |
| `post_flag_create(post_id, reason, **attributes)` | `POST post_flags.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_flag_update(flag_id, reason, **attributes)` | `PUT post_flags/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_appeals_list(search=None, **params)` | `GET post_appeals.json` | — | 源码对齐，未实测（读） |
| `post_appeal_show(appeal_id)` | `GET post_appeals/<id>.json` | — | 源码对齐，未实测（读） |
| `post_appeal_create(post_id, reason, **attributes)` | `POST post_appeals.json` | requires login | 源码对齐，未实测（写/需权限） |
| `post_appeal_update(appeal_id, reason, **attributes)` | `PUT post_appeals/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |

参数键：

- `post_list(**params)` — 顶层/属性：`tags`（The tag query）、`limit`（Posts per page (the server caps this at 200)）、`page`（Page number (an a<id>/b<id> value also works)）、`md5`（Return the single post with this MD5 instead of a list）、`random`（Return a randomized page instead of the newest posts）、`size`（Preview size, e.g. "medium"）、`show_votes`（Include the current user's votes in `tag_string`）
- `post_show(post_id)` — 无参数（路径变量除外）
- `post_random(tags=None)` — 无参数（路径变量除外）
- `post_create(upload_media_asset_id, **attributes)` — 顶层/属性：`upload_media_asset_id`（The upload media asset id. It is read as a **top-level** parameter, so it must not be nested inside post (the controller would otherwise pass it on as an unknown attribute)）、`tag_string`（Space-separated tags）、`rating`（g, s, q or e）、`parent_id`（The parent post id）、`source`（The source URL or text）、`is_pending`（Post the upload as pending moderation）、`artist_commentary`（original_title, original_description, translated_title,）
- `post_update(post_id, **attributes)` — 顶层/属性：`tag_string`（The new space-separated tags）、`old_tag_string`（The previous tags, for conflict detection）、`parent_id`（The parent post id）、`old_parent_id`（The previous parent, for conflict detection）、`source`（The new source）、`old_source`（The previous source, for conflict detection）、`rating`（g, s, q or e）、`old_rating`（The previous rating, for conflict detection）
- `post_delete(post_id, reason, move_favorites=None)` — 顶层/属性：`post_id`（The post id）、`reason`（The deletion reason）
- `post_revert(post_id, version_id)` — 顶层/属性：`post_id`（The post id）
- `post_copy_notes(post_id, other_post_id)` — 顶层/属性：`post_id`（The post to copy notes from）
- `post_mark_as_translated(post_id, check_translation=None, partially_translated=None)` — 顶层/属性：`post_id`（The post id）、`check_translation`（Add or remove check_translation）
- `post_events_list(search=None, **params)` — search：post_id, category, event_at, creator_id, creator_name, order；顶层/属性：`post_id`（Restrict to one post (top-level parameter)）、`limit`（Events per page）
- `post_versions_list(search=None, **params)` — search：id, post_id, updater_id, updater_name, tags, added_tags, removed_tags, changed_tags, all_changed_tags, any_changed_tags, tag_matches, rating, parent_id, source, version, is_new；顶层/属性：`limit`（Versions per page）
- `post_version_undo(version_id)` — 无参数（路径变量除外）
- `post_votes_list(search=None, **params)` — search：post_id, user_id, user_name, score, is_deleted；顶层/属性：`limit`（Votes per page）
- `post_vote_show(vote_id)` — 无参数（路径变量除外）
- `post_vote_create(post_id, score)` — 顶层/属性：`post_id`（The post id）
- `post_vote_delete(vote_id)` — 无参数（路径变量除外）
- `post_favorites_list(post_id, search=None, **params)` — 顶层/属性：`post_id`（The post id）、`limit`（Favorites per page）
- `post_replacements_list(search=None, **params)` — search：post_id, creator_id, creator_name, status, order；顶层/属性：`post_id`（Restrict to one post (top-level parameter)）、`limit`（Replacements per page）
- `post_replacement_show(replacement_id)` — 无参数（路径变量除外）
- `post_replacement_create(post_id, replacement_file=None, **attributes)` — 顶层/属性：`post_id`（The post to replace (top-level)）、`replacement_file`（Open binary file owned by the caller）、`replacement_url`（URL of the new file）、`final_source`（The source of the replacement）
- `post_replacement_update(replacement_id, **attributes)` — 无参数（路径变量除外）
- `post_regeneration_create(post_id, category=None)` — 顶层/属性：`post_id`（The post id (top-level)）、`category`（`post` for the original file, `large` or `preview`）
- `post_approvals_list(search=None, **params)` — search：post_id, user_id, user_name；顶层/属性：`limit`（Approvals per page）
- `post_approval_show(approval_id)` — 无参数（路径变量除外）
- `post_approval_create(post_id)` — 无参数（路径变量除外）
- `post_disapprovals_list(search=None, **params)` — search：post_id, user_id, user_name, reason, message_matches；顶层/属性：`limit`（Disapprovals per page）
- `post_disapproval_show(disapproval_id)` — 无参数（路径变量除外）
- `post_disapproval_create(post_id, **attributes)` — 顶层/属性：`post_id`（The disapproved post (inside post_disapproval, as the controller reads it there)）、`reason`（borderline_quality, borderline_safety, breaks_rules, disinterest or poor_quality）
- `post_disapproval_update(disapproval_id, **attributes)` — 顶层/属性：`attributes`（同对应的 create 方法（源码 docstring 用 see 引用））
- `post_flags_list(search=None, **params)` — search：id, post_id, reason_matches, status (pending/succeeded/rejected), category (normal/unapproved/rejected/deleted), creator_id, creator_name；顶层/属性：`limit`（Flags per page）
- `post_flag_show(flag_id)` — 无参数（路径变量除外）
- `post_flag_create(post_id, reason, **attributes)` — 顶层/属性：`post_id`（The post to flag）
- `post_flag_update(flag_id, reason, **attributes)` — 顶层/属性：`flag_id`（The post flag id）
- `post_appeals_list(search=None, **params)` — search：id, post_id, reason_matches, status, creator_id, creator_name；顶层/属性：`limit`（Appeals per page）
- `post_appeal_show(appeal_id)` — 无参数（路径变量除外）
- `post_appeal_create(post_id, reason, **attributes)` — 顶层/属性：`post_id`（The deleted post to appeal）
- `post_appeal_update(appeal_id, reason, **attributes)` — 顶层/属性：`appeal_id`（The post appeal id）

<a id="sec-media"></a>

### 媒体资源、媒体元数据与 AI 标签（6 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `media_assets_list(search=None, **params)` | `GET media_assets.json` | — | 源码对齐，未实测（读） |
| `media_asset_show(media_asset_id)` | `GET media_assets/<id>.json` | — | 源码对齐，未实测（读） |
| `media_asset_delete(media_asset_id)` | `DELETE media_assets/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `media_metadata_list(search=None, **params)` | `GET media_metadata.json` | — | 源码对齐，未实测（读） |
| `ai_tags_list(search=None, **params)` | `GET ai_tags.json` | — | 源码对齐，未实测（读） |
| `ai_tag_tag(media_asset_id, tag_id, tag=None, mode=None)` | `PUT ai_tags/<id>/{1}/tag.json` | requires login | 源码对齐，未实测（写/需权限） |

参数键：

- `media_assets_list(search=None, **params)` — search：id, md5, pixel_hash, status, file_ext, file_size, image_width, image_height, duration, is_public, metadata, ai_tags_match, min_score, is_posted, order；顶层/属性：`limit`（Assets per page）
- `media_asset_show(media_asset_id)` — 无参数（路径变量除外）
- `media_asset_delete(media_asset_id)` — 无参数（路径变量除外）
- `media_metadata_list(search=None, **params)` — search：media_asset_id, metadata；顶层/属性：`limit`（Records per page）
- `ai_tags_list(search=None, **params)` — search：media_asset_id, tag_id, tag_name, post_id, score, is_posted, order；顶层/属性：`limit`（Tags per page）
- `ai_tag_tag(media_asset_id, tag_id, tag=None, mode=None)` — 顶层/属性：`media_asset_id`（The media asset id）、`tag_id`（The AI tag id）、`tag`（Revert to this tag instead of the AI tag's own name）

<a id="sec-uploads"></a>

### 上传与上传媒体（6 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `upload_list(search=None, **params)` | `GET uploads.json` | requires login for other users' uploads | 源码对齐，未实测（写/需权限） |
| `upload_show(upload_id)` | `GET uploads/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `upload_create(files=None, source=None, referer_url=None)` | `POST uploads.json` | requires login | 源码对齐，未实测（写/需权限） |
| `upload_assets_list(upload_id, search=None, **params)` | `GET uploads/<id>/assets.json` | — | 源码对齐，未实测（读） |
| `upload_media_assets_list(search=None, **params)` | `GET upload_media_assets.json` | — | 源码对齐，未实测（读） |
| `upload_media_asset_show(upload_media_asset_id)` | `GET upload_media_assets/<id>.json` | — | 源码对齐，未实测（读） |

参数键：

- `upload_list(search=None, **params)` — search：id, source, referer_url, status, media_asset_count, uploader_id, uploader_name, ai_tags_match, min_score, is_posted, any_source_matches, order；顶层/属性：`user_id`（Restrict to one uploader (top-level parameter)）、`limit`（Uploads per page）
- `upload_show(upload_id)` — 无参数（路径变量除外）
- `upload_create(files=None, source=None, referer_url=None)` — 顶层/属性：`files`（Open file objects to upload, in order. The caller owns their lifetime (close them after the call)）、`source`（A source URL the server should download）
- `upload_assets_list(upload_id, search=None, **params)` — search：id, status, source_url, page_url, error, media_asset_id, post_id, is_posted, order；顶层/属性：`upload_id`（The upload id）、`limit`（Assets per page (the server defaults to 200)）
- `upload_media_assets_list(search=None, **params)` — search：id, status, source_url, page_url, error, upload_id, media_asset_id, post_id, is_posted, order；顶层/属性：`limit`（Assets per page）
- `upload_media_asset_show(upload_media_asset_id)` — 无参数（路径变量除外）

<a id="sec-tags"></a>

### tags、别名、蕴含、相关标签与补全（13 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `tag_list(search=None, **params)` | `GET tags.json` | — | 已实测（匿名只读） |
| `tag_show(tag_id)` | `GET tags/<id>.json` | — | 源码对齐，未实测（读） |
| `tag_update(tag_id, **attributes)` | `PUT tags/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `tag_versions_list(search=None, **params)` | `GET tag_versions.json` | — | 源码对齐，未实测（读） |
| `tag_version_show(version_id)` | `GET tag_versions/<id>.json` | — | 源码对齐，未实测（读） |
| `tag_aliases_list(search=None, **params)` | `GET tag_aliases.json` | — | 源码对齐，未实测（读） |
| `tag_alias_show(tag_alias_id)` | `GET tag_aliases/<id>.json` | — | 源码对齐，未实测（读） |
| `tag_alias_delete(tag_alias_id)` | `DELETE tag_aliases/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `tag_implications_list(search=None, **params)` | `GET tag_implications.json` | — | 源码对齐，未实测（读） |
| `tag_implication_show(tag_implication_id)` | `GET tag_implications/<id>.json` | — | 源码对齐，未实测（读） |
| `tag_implication_delete(tag_implication_id)` | `DELETE tag_implications/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `related_tag(search=None, **params)` | `GET related_tag.json` | — | 已实测（匿名只读） |
| `autocomplete_list(query, type=None, limit=None)` | `GET autocomplete.json` | — | 候选站复核对应路由匿名 200、list[0]；见 verification D3 |

参数键：

- `tag_list(search=None, **params)` — search：id, name, name_matches, name_or_alias_matches, name_normalize, fuzzy_name_matches, category, is_deprecated, post_count, is_empty, hide_empty, has_wiki_page, has_artist, has_antecedent_alias, has_consequent_aliases, order (name, date, count, similarity)；顶层/属性：`limit`（Tags per page (the server caps this at 1000)）
- `tag_show(tag_id)` — 无参数（路径变量除外）
- `tag_update(tag_id, **attributes)` — 顶层/属性：`category`（0 general, 1 artist, 3 copyright, 4 character (Builder level and above)）、`is_deprecated`（Whether the tag is deprecated (Builder level）
- `tag_versions_list(search=None, **params)` — search：tag_id, updater_id, updater_name, name_matches, category, is_deprecated, version, order (created_at, updated_at, id and their _asc forms)；顶层/属性：`limit`（Versions per page）
- `tag_version_show(version_id)` — 无参数（路径变量除外）
- `tag_aliases_list(search=None, **params)` — search：id, antecedent_name, consequent_name, name_matches, antecedent_name_matches, consequent_name_matches, status (active, deleted, retired), category, creator_id, creator_name, approver_id, forum_topic_id, order (created_at, updated_at, name, antecedent_tag_count, consequent_tag_count)；顶层/属性：`limit`（Aliases per page）
- `tag_alias_show(tag_alias_id)` — 无参数（路径变量除外）
- `tag_alias_delete(tag_alias_id)` — 无参数（路径变量除外）
- `tag_implications_list(search=None, **params)` — search：id, antecedent_name, consequent_name, name_matches, antecedent_name_matches, consequent_name_matches, status, category, creator_id, creator_name, approver_id, forum_topic_id, implied_from, implied_to, order；顶层/属性：`limit`（Implications per page）
- `tag_implication_show(tag_implication_id)` — 无参数（路径变量除外）
- `tag_implication_delete(tag_implication_id)` — 无参数（路径变量除外）
- `related_tag(search=None, **params)` — search：The search parameters, sent as search[...]: query (required; a tag query such as "pixiv" or "pixiv rating:g"), category or categories (comma/space separated tag categories, e.g. "general"), order (frequency (default), cosine, jaccard, overlap), search_sample_size (default 5000) and tag_sample_size (default 500)；顶层/属性：`limit`（How many related tags to return; the server clamps this to 0..1000 and defaults to 100 (top-level parameter)）、`media_asset_id`（Base the query on a media asset's AI tags instead of on query (top-level parameter)）
- `autocomplete_list(query, type=None, limit=None)` — 顶层/属性：`query`（The text to complete）、`type`（tag (default), tag_query (search sample), artist, wiki_page, user, pool, comment or saved_search are accepted by the server）、`limit`（Maximum number of suggestions (the server defaults to）

<a id="sec-artists"></a>

### artists（画师、主页记录、版本与说明）（18 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `artist_list(search=None, **params)` | `GET artists.json` | — | 已实测（匿名只读） |
| `artist_show(artist_id)` | `GET artists/<id>.json` | — | 源码对齐，未实测（读） |
| `artist_show_or_new(name=None)` | `GET artists/show_or_new.json` | — | 已实测（匿名只读） |
| `artist_create(name, **attributes)` | `POST artists.json` | requires login | 源码对齐，未实测（写/需权限） |
| `artist_update(artist_id, **attributes)` | `PUT artists/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `artist_delete(artist_id)` | `DELETE artists/<id>.json` | requires builder level | 源码对齐，未实测（写/需权限） |
| `artist_revert(artist_id, version_id)` | `PUT artists/<id>/revert.json` | requires login | 源码对齐，未实测（写/需权限） |
| `artist_ban(artist_id)` | `PUT artists/<id>/ban.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `artist_unban(artist_id)` | `PUT artists/<id>/unban.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `artist_urls_list(search=None, **params)` | `GET artist_urls.json` | — | 源码对齐，未实测（读） |
| `artist_versions_list(search=None, **params)` | `GET artist_versions.json` | — | 源码对齐，未实测（读） |
| `artist_version_show(version_id)` | `GET artist_versions/<id>.json` | — | 源码对齐，未实测（读） |
| `artist_commentaries_list(search=None, **params)` | `GET artist_commentaries.json` | — | 源码对齐，未实测（读） |
| `artist_commentary_show(post_id)` | `GET posts/<id>/artist_commentary.json` | — | 源码对齐，未实测（读） |
| `artist_commentary_create_or_update(post_id, **attributes)` | `PUT posts/<id>/artist_commentary/create_or_update.json` | requires login | 源码对齐，未实测（写/需权限） |
| `artist_commentary_revert(post_id, version_id)` | `PUT artist_commentaries/<id>/revert.json` | — | 源码对齐，未实测（写/需权限） |
| `artist_commentary_versions_list(search=None, **params)` | `GET artist_commentary_versions.json` | — | 源码对齐，未实测（读） |
| `artist_commentary_version_show(version_id)` | `GET artist_commentary_versions/<id>.json` | — | 源码对齐，未实测（读） |

参数键：

- `artist_list(search=None, **params)` — search：id, name (exact, or several comma-separated names), name_like/name_ilike/name_regex, any_name_matches (name, other names or group, supporting * wildcards and /regex/), any_name_or_url_matches, any_other_name_like, url_matches (a profile URL, a domain, *foo* or /regex/; several values may be space-separated), group_name, other_names_include_any, is_deleted, is_banned, has_urls, has_wiki_page, has_tag_alias, has_tag, order (name, updated_at, post_count)；顶层/属性：`name`（Shorthand for search[name] (top-level parameter)）、`limit`（Artists per page）、`page`（Page number）
- `artist_show(artist_id)` — 无参数（路径变量除外）
- `artist_show_or_new(name=None)` — 顶层/属性：`name`（The artist name; a blank name redirects to the new）
- `artist_create(name, **attributes)` — 顶层/属性：`name`（The artist's primary name (the future tag name)）、`group_name`（The group the artist belongs to）、`url_string`（Whitespace-separated profile URLs）、`is_deleted`（Create the artist as deleted）
- `artist_update(artist_id, **attributes)` — 顶层/属性：`attributes`（同对应的 create 方法（源码 docstring 用 see 引用））
- `artist_delete(artist_id)` — 无参数（路径变量除外）
- `artist_revert(artist_id, version_id)` — 顶层/属性：`artist_id`（The artist id）
- `artist_ban(artist_id)` — 无参数（路径变量除外）
- `artist_unban(artist_id)` — 无参数（路径变量除外）
- `artist_urls_list(search=None, **params)` — search：id, artist_id, url, url_matches (same matching rules as artist search), is_active, has_artist, order (id, artist_id, url, is_active, created_at, updated_at and _asc)；顶层/属性：`limit`（URLs per page）
- `artist_versions_list(search=None, **params)` — search：artist_id, updater_id, updater_name, name, group_name, other_names_include_any, is_deleted, is_banned, order (id, created_at, updated_at, name and _asc)；顶层/属性：`limit`（Versions per page）
- `artist_version_show(version_id)` — 无参数（路径变量除外）
- `artist_commentaries_list(search=None, **params)` — search：post_id, original_title, original_description, translated_title, translated_description, text_matches, original_present, translated_present, is_deleted, order (post_id, updated_at, id and _asc)；顶层/属性：`limit`（Commentaries per page）
- `artist_commentary_show(post_id)` — 无参数（路径变量除外）
- `artist_commentary_create_or_update(post_id, **attributes)` — 顶层/属性：`post_id`（The post id (taken from the route)）
- `artist_commentary_revert(post_id, version_id)` — 顶层/属性：`post_id`（The post id）
- `artist_commentary_versions_list(search=None, **params)` — search：post_id, updater_id, updater_name, text_matches, original_title, original_description, translated_title, translated_description；顶层/属性：`limit`（Versions per page）
- `artist_commentary_version_show(version_id)` — 无参数（路径变量除外）

<a id="sec-comments"></a>

### comments（评论与评论投票）（10 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `comment_list(search=None, **params)` | `GET comments.json` | — | 已实测（匿名只读） |
| `comment_show(comment_id)` | `GET comments/<id>.json` | — | 源码对齐，未实测（读） |
| `comment_create(post_id, body, **attributes)` | `POST comments.json` | requires login | 源码对齐，未实测（写/需权限） |
| `comment_update(comment_id, **attributes)` | `PUT comments/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `comment_delete(comment_id)` | `DELETE comments/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `comment_undelete(comment_id)` | `POST comments/<id>/undelete.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `comment_votes_list(search=None, **params)` | `GET comment_votes.json` | — | 源码对齐，未实测（读） |
| `comment_vote_show(vote_id)` | `GET comment_votes/<id>.json` | — | 源码对齐，未实测（读） |
| `comment_vote_create(comment_id, score)` | `POST comments/<id>/votes.json` | requires login | 源码对齐，未实测（写/需权限） |
| `comment_vote_delete(vote_id)` | `DELETE comment_votes/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |

参数键：

- `comment_list(search=None, **params)` — search：id, body_matches, post_id, post_tags_match, creator_id, creator_name, updater_id, is_deleted, is_sticky, do_not_bump_post, score, is_edited, order；顶层/属性：`group_by`（"comment" (default, newest comments) or "post" (newest commented posts)）、`limit`（Comments per page）
- `comment_show(comment_id)` — 无参数（路径变量除外）
- `comment_create(post_id, body, **attributes)` — 顶层/属性：`post_id`（The post to comment on）、`body`（The comment body, in DText）、`do_not_bump_post`（Do not bump the post to the top of the comment listing）
- `comment_update(comment_id, **attributes)` — 顶层/属性：`comment_id`（The comment id）、`body`（The new body）、`is_deleted`（Whether the comment is deleted）
- `comment_delete(comment_id)` — 无参数（路径变量除外）
- `comment_undelete(comment_id)` — 无参数（路径变量除外）
- `comment_votes_list(search=None, **params)` — search：comment_id, user_id, user_name, score, is_deleted；顶层/属性：`limit`（Votes per page）
- `comment_vote_show(vote_id)` — 无参数（路径变量除外）
- `comment_vote_create(comment_id, score)` — 顶层/属性：`comment_id`（The comment id）
- `comment_vote_delete(vote_id)` — 无参数（路径变量除外）

<a id="sec-notes"></a>

### notes（笔记与笔记版本）（9 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `note_list(search=None, **params)` | `GET notes.json` | — | 源码对齐，未实测（读） |
| `note_show(note_id)` | `GET notes/<id>.json` | — | 源码对齐，未实测（读） |
| `note_create(post_id, x, y, width, height, body, **attributes)` | `POST notes.json` | requires login | 源码对齐，未实测（写/需权限） |
| `note_update(note_id, **attributes)` | `PUT notes/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `note_delete(note_id)` | `DELETE notes/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `note_revert(note_id, version_id)` | `PUT notes/<id>/revert.json` | requires login | 源码对齐，未实测（写/需权限） |
| `note_preview(body)` | `POST notes/preview.json` | 业务权限允许匿名，但仍受 CSRF 检查 | 本轮匿名POST返回403 InvalidAuthenticityToken；没有成功预览，不保存笔记 |
| `note_versions_list(search=None, **params)` | `GET note_versions.json` | — | 源码对齐，未实测（读） |
| `note_version_show(version_id)` | `GET note_versions/<id>.json` | — | 源码对齐，未实测（读） |

参数键：

- `note_list(search=None, **params)` — search：id, post_id, post_tags_match, body_matches, is_active, x, y, width, height, version；顶层/属性：`limit`（Notes per page）
- `note_show(note_id)` — 无参数（路径变量除外）
- `note_create(post_id, x, y, width, height, body, **attributes)` — 顶层/属性：`post_id`（The post the note belongs to）、`x`（Left offset in pixels）、`y`（Top offset in pixels）、`width`（Note width in pixels）、`height`（Note height in pixels）、`body`（The note body, in DText）
- `note_update(note_id, **attributes)` — 顶层/属性：`note_id`（The note id）
- `note_delete(note_id)` — 无参数（路径变量除外）
- `note_revert(note_id, version_id)` — 顶层/属性：`note_id`（The note id）
- `note_preview(body)` — 顶层 `body`：必填的笔记 HTML 字符串；返回 `sanitized_body`。
- `note_versions_list(search=None, **params)` — search：note_id, post_id, updater_id, is_active, x, y, width, height, body, version；顶层/属性：`limit`（Versions per page）
- `note_version_show(version_id)` — 无参数（路径变量除外）

<a id="sec-pools"></a>

### pools（合集、成员与版本）（11 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `pool_list(search=None, **params)` | `GET pools.json` | — | 已实测（匿名只读） |
| `pool_show(pool_id)` | `GET pools/<id>.json` | — | 源码对齐，未实测（读） |
| `pool_create(name, **attributes)` | `POST pools.json` | requires login | 源码对齐，未实测（写/需权限） |
| `pool_update(pool_id, **attributes)` | `PUT pools/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `pool_delete(pool_id)` | `DELETE pools/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `pool_undelete(pool_id)` | `POST pools/<id>/undelete.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `pool_revert(pool_id, version_id)` | `PUT pools/<id>/revert.json` | requires login | 源码对齐，未实测（写/需权限） |
| `pool_gallery(search=None, **params)` | `GET pools/gallery.json` | — | 源码对齐，未实测（读） |
| `pool_element_create(post_id, pool_id=None, pool_name=None)` | `POST pool_element.json` | requires login | 源码对齐，未实测（写/需权限） |
| `pool_versions_list(search=None, **params)` | `GET pool_versions.json` | requires the archive service | 源码对齐，未实测（读，依赖 archive 服务） |
| `pool_version_diff(pool_version_id, other_id=None, type=None)` | `GET pool_versions/<id>/diff.json` | — | 源码对齐，未实测（读） |

参数键：

- `pool_list(search=None, **params)` — search：id, name, name_matches, name_contains, description_matches, post_ids, is_deleted, category (series or collection), post_tags_match, linked_to, not_linked_to, order (name, created_at, post_count)；顶层/属性：`limit`（Pools per page）
- `pool_show(pool_id)` — 无参数（路径变量除外）
- `pool_create(name, **attributes)` — 顶层/属性：`name`（The pool name）、`description`（The pool description, in DText）、`category`（series or collection）、`post_ids_string`（Space-separated initial post ids）
- `pool_update(pool_id, **attributes)` — 顶层/属性：`pool_id`（The pool id）
- `pool_delete(pool_id)` — 无参数（路径变量除外）
- `pool_undelete(pool_id)` — 无参数（路径变量除外）
- `pool_revert(pool_id, version_id)` — 顶层/属性：`pool_id`（The pool id）
- `pool_gallery(search=None, **params)` — search：Search parameters; defaults to {"category": "series"} server-side；顶层/属性：`limit`（Pools per page）
- `pool_element_create(post_id, pool_id=None, pool_name=None)` — 顶层/属性：`post_id`（The post to add）、`pool_id`（The pool id (either this or pool_name)）
- `pool_versions_list(search=None, **params)` — search：pool_id, post_id, updater_id, updater_name, name_contains, is_new, version, category, is_active, is_deleted；顶层/属性：`limit`（Versions per page）
- `pool_version_diff(pool_version_id, other_id=None, type=None)` — 顶层/属性：`pool_version_id`（The pool version id）、`other_id`（The version to compare against; defaults to the previous/next version chosen by type）

<a id="sec-wiki"></a>

### wiki（页面与版本）（10 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `wiki_page_list(search=None, **params)` | `GET wiki_pages.json` | — | 已实测（匿名只读） |
| `wiki_page_show(id_or_title)` | `GET wiki_pages/<id>.json` | — | 已实测（匿名只读） |
| `wiki_page_create(title, **attributes)` | `POST wiki_pages.json` | requires login | 源码对齐，未实测（写/需权限） |
| `wiki_page_update(wiki_page_id, **attributes)` | `PUT wiki_pages/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `wiki_page_delete(wiki_page_id)` | `DELETE wiki_pages/<id>.json` | requires builder level | 源码对齐，未实测（写/需权限） |
| `wiki_page_revert(wiki_page_id, version_id)` | `PUT wiki_pages/<id>/revert.json` | requires login | 源码对齐，未实测（写/需权限） |
| `wiki_page_show_or_new(title=None)` | `GET wiki_pages/show_or_new.json` | — | 源码对齐，未实测（读） |
| `wiki_page_versions_list(search=None, **params)` | `GET wiki_page_versions.json` | — | 源码对齐，未实测（读） |
| `wiki_page_version_show(version_id)` | `GET wiki_page_versions/<id>.json` | — | 源码对齐，未实测（读） |
| `wiki_page_versions_diff(thispage=None, otherpage=None, type=None)` | `GET wiki_page_versions/diff.json` | — | 源码对齐，未实测（读） |

参数键：

- `wiki_page_list(search=None, **params)` — search：id, title, title_normalize, title_or_body_matches, body_matches, other_names_match, other_names_present, is_locked, is_deleted, hide_deleted, linked_to, not_linked_to, embedded_post_id, embedded_media_asset_id, has_embedded_media, has_tag, has_artist, order (title, post_count)；顶层/属性：`title`（Redirects to a title search (top-level parameter)）、`limit`（Pages per page）
- `wiki_page_show(id_or_title)` — 顶层/属性：`id_or_title`（A page id, or a page title such as）
- `wiki_page_create(title, **attributes)` — 顶层/属性：`title`（The page title）、`body`（The page body, in DText. other_names (list) or other_names_string (str): Alternate titles）、`is_deleted`（Create the page as deleted (Builder level)）
- `wiki_page_update(wiki_page_id, **attributes)` — 顶层/属性：`wiki_page_id`（The page id or title）
- `wiki_page_delete(wiki_page_id)` — 无参数（路径变量除外）
- `wiki_page_revert(wiki_page_id, version_id)` — 顶层/属性：`wiki_page_id`（The page id or title）
- `wiki_page_show_or_new(title=None)` — 无参数（路径变量除外）
- `wiki_page_versions_list(search=None, **params)` — search：wiki_page_id, updater_id, updater_name, title, title_like, title_ilike, title_regex, body_matches, other_names_include_any, is_locked, is_deleted；顶层/属性：`limit`（Versions per page）
- `wiki_page_version_show(version_id)` — 无参数（路径变量除外）
- `wiki_page_versions_diff(thispage=None, otherpage=None, type=None)` — 顶层/属性：`thispage`（The first version id）、`otherpage`（The second version id）

<a id="sec-users"></a>

### users 与 favorites（用户、收藏与收藏组）（25 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `user_list(search=None, **params)` | `GET users.json` | — | 候选站复核对应路由匿名 200；见 verification D3 |
| `user_show(user_id)` | `GET users/<id>.json` | — | 源码对齐，未实测（读） |
| `user_create(name, password, password_confirmation)` | `POST users.json` | — | 源码对齐，未实测（写/需权限） |
| `user_update(user_id, **attributes)` | `PUT users/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `user_profile()` | `GET profile.json` | requires login | 源码对齐，未实测（写/需权限） |
| `user_actions_list(search=None, **params)` | `GET user_actions.json` | requires moderator | 源码对齐，未实测（写/需权限） |
| `user_action_show(user_action_id)` | `GET user_actions/<id>.json` | — | 源码对齐，未实测（读） |
| `user_events_list(search=None, **params)` | `GET user_events.json` | — | 源码对齐，未实测（读） |
| `user_feedbacks_list(search=None, **params)` | `GET user_feedbacks.json` | — | 源码对齐，未实测（读） |
| `user_feedback_show(feedback_id)` | `GET user_feedbacks/<id>.json` | — | 源码对齐，未实测（读） |
| `user_feedback_create(**attributes)` | `POST user_feedbacks.json` | requires login | 源码对齐，未实测（写/需权限） |
| `user_feedback_update(feedback_id, **attributes)` | `PUT user_feedbacks/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `user_name_change_requests_list(search=None, **params)` | `GET user_name_change_requests.json` | — | 源码对齐，未实测（读） |
| `user_name_change_request_show(request_id)` | `GET user_name_change_requests/<id>.json` | — | 源码对齐，未实测（读） |
| `user_name_change_request_create(**attributes)` | `POST user_name_change_requests.json` | requires login | 源码对齐，未实测（写/需权限） |
| `favorite_list(search=None, **params)` | `GET favorites.json` | requires login for other users' favorites | 源码对齐，未实测（写/需权限） |
| `favorite_create(post_id)` | `POST favorites.json` | requires login | 源码对齐，未实测（写/需权限） |
| `favorite_delete(post_id)` | `DELETE favorites/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `favorite_groups_list(search=None, **params)` | `GET favorite_groups.json` | — | 源码对齐，未实测（读） |
| `favorite_group_show(group_id)` | `GET favorite_groups/<id>.json` | — | 源码对齐，未实测（读） |
| `favorite_group_create(name, **attributes)` | `POST favorite_groups.json` | requires login | 源码对齐，未实测（写/需权限） |
| `favorite_group_update(group_id, **attributes)` | `PUT favorite_groups/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `favorite_group_delete(group_id)` | `DELETE favorite_groups/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `favorite_group_add_post(group_id, post_id)` | `PUT favorite_groups/<id>/add_post.json` | requires login | 源码对齐，未实测（写/需权限） |
| `favorite_group_remove_post(group_id, post_id)` | `PUT favorite_groups/<id>/remove_post.json` | requires login | 源码对齐，未实测（写/需权限） |

参数键：

- `user_list(search=None, **params)` — search：id, name_matches (also accepts name), any_name_matches, name_or_past_name_matches, level, min_level, max_level, is_banned, has_posts, has_comments, order (name, post_upload_count, note_count, post_update_count)；顶层/属性：`name`（Shorthand that searches current and past names (top-level parameter)）、`limit`（Users per page）
- `user_show(user_id)` — 无参数（路径变量除外）
- `user_create(name, password, password_confirmation)` — 顶层/属性：`name`（The user name）、`password`（The password）
- `user_update(user_id, **attributes)` — 无参数（路径变量除外）
- `user_profile()` — 无参数（路径变量除外）
- `user_actions_list(search=None, **params)` — search：user_id, user_name, event_type, model_type/model_id, order (event_at_asc; the default is newest first)；顶层/属性：`user_id`（Restrict to one user (top-level parameter)）、`limit`（Actions per page）
- `user_action_show(user_action_id)` — 无参数（路径变量除外）
- `user_events_list(search=None, **params)` — search：id, user_id, user_name, category, ip_addr, session_id, user_agent, metadata；顶层/属性：`user_id`（Restrict to one user (top-level parameter)）、`limit`（Events per page）
- `user_feedbacks_list(search=None, **params)` — search：id, user_id, user_name, creator_id, creator_name, category, body_matches, is_deleted, hide_bans；顶层/属性：`limit`（Feedbacks per page）
- `user_feedback_show(feedback_id)` — 无参数（路径变量除外）
- `user_feedback_create(**attributes)` — 顶层/属性：`body`（The feedback text）、`category`（positive or negative）
- `user_feedback_update(feedback_id, **attributes)` — 无参数（路径变量除外）
- `user_name_change_requests_list(search=None, **params)` — search：id, user_id, user_name, original_name, desired_name；顶层/属性：`limit`（Requests per page）
- `user_name_change_request_show(request_id)` — 无参数（路径变量除外）
- `user_name_change_request_create(**attributes)` — 顶层/属性：`user_id`（The user whose name should change）
- `favorite_list(search=None, **params)` — search：post_id, user_id, user_name；顶层/属性：`post_id`（Restrict to one post (top-level parameter)）、`user_id`（Which user's favorites to list, defaults to yours）、`limit`（Favorites per page）
- `favorite_create(post_id)` — 无参数（路径变量除外）
- `favorite_delete(post_id)` — 无参数（路径变量除外）
- `favorite_groups_list(search=None, **params)` — search：id, name, name_contains, is_public, post_ids, creator_id, creator_name, order (name, created_at, updated_at, post_count)；顶层/属性：`user_id`（Restrict to one creator (top-level parameter)）、`limit`（Groups per page）
- `favorite_group_show(group_id)` — 无参数（路径变量除外）
- `favorite_group_create(name, **attributes)` — 顶层/属性：`name`（The group name）、`post_ids_string`（Space-separated post ids）、`post_ids`（Post ids）
- `favorite_group_update(group_id, **attributes)` — 顶层/属性：`group_id`（The favorite group id）
- `favorite_group_delete(group_id)` — 无参数（路径变量除外）
- `favorite_group_add_post(group_id, post_id)` — 顶层/属性：`group_id`（The favorite group id）
- `favorite_group_remove_post(group_id, post_id)` — 顶层/属性：`group_id`（The favorite group id）

<a id="sec-forum"></a>

### forum（主题、帖子、投票与阅读记录）（18 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `forum_topics_list(search=None, **params)` | `GET forum_topics.json` | — | 源码对齐，未实测（读） |
| `forum_topic_show(topic_id)` | `GET forum_topics/<id>.json` | — | 源码对齐，未实测（读） |
| `forum_topic_create(title, body, **attributes)` | `POST forum_topics.json` | requires login | 源码对齐，未实测（写/需权限） |
| `forum_topic_update(topic_id, **attributes)` | `PUT forum_topics/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `forum_topic_delete(topic_id)` | `DELETE forum_topics/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `forum_topic_undelete(topic_id)` | `POST forum_topics/<id>/undelete.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `forum_topics_mark_all_as_read()` | `POST forum_topics/mark_all_as_read.json` | requires login | 源码对齐，未实测（写/需权限） |
| `forum_posts_list(search=None, **params)` | `GET forum_posts.json` | — | 源码对齐，未实测（读） |
| `forum_post_show(post_id)` | `GET forum_posts/<id>.json` | — | 源码对齐，未实测（读） |
| `forum_post_create(topic_id, body)` | `POST forum_posts.json` | requires login | 源码对齐，未实测（写/需权限） |
| `forum_post_update(post_id, body)` | `PUT forum_posts/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `forum_post_delete(post_id)` | `DELETE forum_posts/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `forum_post_undelete(post_id)` | `POST forum_posts/<id>/undelete.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `forum_post_votes_list(search=None, **params)` | `GET forum_post_votes.json` | — | 源码对齐，未实测（读） |
| `forum_post_vote_show(vote_id)` | `GET forum_post_votes/<id>.json` | — | 源码对齐，未实测（读） |
| `forum_post_vote_create(forum_post_id, score)` | `POST forum_post_votes.json` | requires login | 源码对齐，未实测（写/需权限） |
| `forum_post_vote_delete(vote_id)` | `DELETE forum_post_votes/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `forum_topic_visits_list(search=None, **params)` | `GET forum_topic_visits.json` | requires login | 源码对齐，未实测（写/需权限） |

参数键：

- `forum_topics_list(search=None, **params)` — search：id, title, title_matches, category or category_id (0 general, 1 tags, 2 bugs, 3 bulk update requests), min_level, is_sticky, is_locked, is_deleted, is_private, is_read, status (pending, approved, rejected), creator_id, creator_name, order (sticky, id)；顶层/属性：`limit`（Topics per page）
- `forum_topic_show(topic_id)` — 无参数（路径变量除外）
- `forum_topic_create(title, body, **attributes)` — 顶层/属性：`title`（The topic title）、`body`（The body of the topic's first post）、`category_id`（0 general, 1 tags, 2 bugs and features, 3 bulk update requests）
- `forum_topic_update(topic_id, **attributes)` — 顶层/属性：`topic_id`（The forum topic id）
- `forum_topic_delete(topic_id)` — 无参数（路径变量除外）
- `forum_topic_undelete(topic_id)` — 无参数（路径变量除外）
- `forum_topics_mark_all_as_read()` — 无参数（路径变量除外）
- `forum_posts_list(search=None, **params)` — search：id, body_matches, creator_id, creator_name, topic_id, linked_to, and nested topic filters such as {"topic": {"title_matches": ...}} or {"topic": {"category_id": 1}}；顶层/属性：`limit`（Posts per page）
- `forum_post_show(post_id)` — 无参数（路径变量除外）
- `forum_post_create(topic_id, body)` — 顶层/属性：`topic_id`（The topic to reply to）
- `forum_post_update(post_id, body)` — 顶层/属性：`post_id`（The forum post id）
- `forum_post_delete(post_id)` — 无参数（路径变量除外）
- `forum_post_undelete(post_id)` — 无参数（路径变量除外）
- `forum_post_votes_list(search=None, **params)` — search：forum_post_id, creator_id, creator_name, score；顶层/属性：`limit`（Votes per page）
- `forum_post_vote_show(vote_id)` — 无参数（路径变量除外）
- `forum_post_vote_create(forum_post_id, score)` — 顶层/属性：`forum_post_id`（The forum post id (top-level)）
- `forum_post_vote_delete(vote_id)` — 无参数（路径变量除外）
- `forum_topic_visits_list(search=None, **params)` — search：user_id, forum_topic_id, last_read_at；顶层/属性：`limit`（Visits per page）

<a id="sec-dmails"></a>

### dmails（站内信）（5 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `dmail_list(search=None, **params)` | `GET dmails.json` | requires login | 源码对齐，未实测（写/需权限） |
| `dmail_show(dmail_id)` | `GET dmails/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `dmail_create(title, body, to_name=None, to_id=None)` | `POST dmails.json` | requires login | 源码对齐，未实测（写/需权限） |
| `dmail_update(dmail_id, **attributes)` | `PUT dmails/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `dmails_mark_all_as_read()` | `POST dmails/mark_all_as_read.json` | requires login | 源码对齐，未实测（写/需权限） |

参数键：

- `dmail_list(search=None, **params)` — search：id, title, body, message_matches, folder (received/sent/all), is_read, is_deleted, to_id, to_name, from_id, from_name；顶层/属性：`limit`（Dmails per page）
- `dmail_show(dmail_id)` — 无参数（路径变量除外）
- `dmail_create(title, body, to_name=None, to_id=None)` — 顶层/属性：`title`（The message title）、`body`（The message body, in DText）
- `dmail_update(dmail_id, **attributes)` — 顶层/属性：`dmail_id`（The dmail id）
- `dmails_mark_all_as_read()` — 无参数（路径变量除外）

<a id="sec-bans"></a>

### bans、bulk update requests 与 IP 数据（17 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `ban_list(search=None, **params)` | `GET bans.json` | — | 源码对齐，未实测（读） |
| `ban_show(ban_id)` | `GET bans/<id>.json` | — | 源码对齐，未实测（读） |
| `ban_create(**attributes)` | `POST bans.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `ban_update(ban_id, **attributes)` | `PUT bans/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `ban_delete(ban_id)` | `DELETE bans/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `bulk_update_requests_list(search=None, **params)` | `GET bulk_update_requests.json` | — | 源码对齐，未实测（读） |
| `bulk_update_request_show(request_id)` | `GET bulk_update_requests/<id>.json` | — | 源码对齐，未实测（读） |
| `bulk_update_request_create(script, **attributes)` | `POST bulk_update_requests.json` | requires login | 源码对齐，未实测（写/需权限） |
| `bulk_update_request_update(request_id, **attributes)` | `PUT bulk_update_requests/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `bulk_update_request_approve(request_id)` | `POST bulk_update_requests/<id>/approve.json` | requires approver level | 源码对齐，未实测（写/需权限） |
| `bulk_update_request_delete(request_id)` | `DELETE bulk_update_requests/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `ip_bans_list(search=None, **params)` | `GET ip_bans.json` | — | 源码对齐，未实测（读） |
| `ip_ban_show(ip_ban_id)` | `GET ip_bans/<id>.json` | — | 源码对齐，未实测（读） |
| `ip_ban_create(**attributes)` | `POST ip_bans.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `ip_ban_update(ip_ban_id, **attributes)` | `PUT ip_bans/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `ip_address_show(ip_addr)` | `GET ip_addresses/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `ip_geolocations_list(search=None, **params)` | `GET ip_geolocations.json` | requires moderator level | 源码对齐，未实测（写/需权限） |

参数键：

- `ban_list(search=None, **params)` — search：id, user_id, user_name, banner_id, banner_name, reason_matches, duration, expired, order (expires_at_desc)；顶层/属性：`limit`（Bans per page）
- `ban_show(ban_id)` — 无参数（路径变量除外）
- `ban_create(**attributes)` — 顶层/属性：`reason`（The ban reason）、`duration`（A duration such as "1 week"; blank is permanent. delete_posts (bool), post_deletion_reason (str), delete_comments (bool), delete_forum_posts (bool),）
- `ban_update(ban_id, **attributes)` — 无参数（路径变量除外）
- `ban_delete(ban_id)` — 无参数（路径变量除外）
- `bulk_update_requests_list(search=None, **params)` — search：id, script_matches, title_matches, user_id, user_name, approver_id, approver_name, forum_topic_id, status (pending, approved, rejected or a comma-separated list), tags, can_approve, score, order (id, updated_at, score and _asc)；顶层/属性：`limit`（Requests per page）
- `bulk_update_request_show(request_id)` — 无参数（路径变量除外）
- `bulk_update_request_create(script, **attributes)` — 顶层/属性：`script`（The BUR script, for example "alias foo -> bar"）、`title`（An optional title）、`reason`（An optional reason）
- `bulk_update_request_update(request_id, **attributes)` — 无参数（路径变量除外）
- `bulk_update_request_approve(request_id)` — 无参数（路径变量除外）
- `bulk_update_request_delete(request_id)` — 无参数（路径变量除外）
- `ip_bans_list(search=None, **params)` — search：id, ip_addr, reason_matches, category, is_deleted, hit_count, last_hit_at, creator_id, creator_name, order (created_at, updated_at, last_hit_at and _asc)；顶层/属性：`limit`（Bans per page）
- `ip_ban_show(ip_ban_id)` — 无参数（路径变量除外）
- `ip_ban_create(**attributes)` — 顶层/属性：`ip_addr`（The IP address or range）、`reason`（The ban reason）、`category`（warning or block）
- `ip_ban_update(ip_ban_id, **attributes)` — 顶层/属性：`attributes`（同对应的 create 方法（源码 docstring 用 see 引用））
- `ip_address_show(ip_addr)` — 无参数（路径变量除外）
- `ip_geolocations_list(search=None, **params)` — search：ip_addr, network, country, region, city, asn, is_proxy；顶层/属性：`limit`（Records per page）

<a id="sec-moderation"></a>

### 审核、公告、报表、后台任务与站点数据（34 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `mod_actions_list(search=None, **params)` | `GET mod_actions.json` | — | 源码对齐，未实测（读） |
| `mod_action_show(mod_action_id)` | `GET mod_actions/<id>.json` | requires janitor level | 源码对齐，未实测（写/需权限） |
| `modqueue_list(search=None, **params)` | `GET modqueue.json` | requires approver level | 源码对齐，未实测（写/需权限） |
| `moderation_reports_list(search=None, **params)` | `GET moderation_reports.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `moderation_report_show(report_id)` | `GET moderation_reports/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `moderation_report_create(**attributes)` | `POST moderation_reports.json` | requires login | 源码对齐，未实测（写/需权限） |
| `moderation_report_update(report_id, **attributes)` | `PUT moderation_reports/<id>.json` | requires moderator level | 源码对齐，未实测（写/需权限） |
| `news_updates_list(search=None, **params)` | `GET news_updates.json` | — | 源码对齐，未实测（读） |
| `news_update_show(news_update_id)` | `GET news_updates/<id>.json` | — | 源码对齐，未实测（读） |
| `news_update_create(message, **attributes)` | `POST news_updates.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `news_update_update(news_update_id, **attributes)` | `PUT news_updates/<id>.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `news_update_delete(news_update_id)` | `DELETE news_updates/<id>.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `saved_searches_list(search=None, **params)` | `GET saved_searches.json` | requires login | 源码对齐，未实测（写/需权限） |
| `saved_search_create(**attributes)` | `POST saved_searches.json` | requires login | 源码对齐，未实测（写/需权限） |
| `saved_search_update(saved_search_id, **attributes)` | `PUT saved_searches/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `saved_search_delete(saved_search_id)` | `DELETE saved_searches/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `site_credentials_list(search=None, **params)` | `GET site_credentials.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `site_credential_show(site_credential_id)` | `GET site_credentials/<id>.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `site_credential_create(site, **attributes)` | `POST site_credentials.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `site_credential_update(site_credential_id, **attributes)` | `PUT site_credentials/<id>.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `site_credential_delete(site_credential_id)` | `DELETE site_credentials/<id>.json` | requires admin level | 源码对齐，未实测（写/需权限） |
| `reactions_list(search=None, **params)` | `GET reactions.json` | — | 源码对齐，未实测（读） |
| `reaction_show(reaction_id)` | `GET reactions/<id>.json` | — | 源码对齐，未实测（读） |
| `reaction_create(**attributes)` | `POST reactions.json` | requires login | 源码对齐，未实测（写/需权限） |
| `reaction_delete(reaction_id)` | `DELETE reactions/<id>.json` | requires login | 源码对齐，未实测（写/需权限） |
| `report_show(report, search=None, **params)` | `GET reports/<id>.json` | — | 源码对齐，未实测（读） |
| `jobs_list(search=None, **params)` | `GET jobs.json` | — | 源码对齐，未实测（读） |
| `job_cancel(job_id)` | `PUT jobs/<id>/cancel.json` | requires janitor level | 源码对齐，未实测（写/需权限） |
| `job_retry(job_id)` | `PUT jobs/<id>/retry.json` | requires janitor level | 源码对齐，未实测（写/需权限） |
| `job_run(job_id)` | `PUT jobs/<id>/run.json` | requires janitor level | 源码对齐，未实测（写/需权限） |
| `job_delete(job_id)` | `DELETE jobs/<id>.json` | requires janitor level | 源码对齐，未实测（写/需权限） |
| `dtext_links_list(search=None, **params)` | `GET dtext_links.json` | — | 源码对齐，未实测（读） |
| `recommended_posts_list(search=None, **params)` | `GET recommended_posts.json` | — | 源码对齐，未实测（读） |
| `counts_posts(tags=None, estimate_count=None, skip_cache=None)` | `GET counts/posts.json` | — | 源码对齐，未实测（读） |

参数键：

- `mod_actions_list(search=None, **params)` — search：id, category, description_matches, creator_id, creator_name, subject_type, subject_id, order (created_at_asc)；顶层/属性：`limit`（Actions per page）
- `mod_action_show(mod_action_id)` — 无参数（路径变量除外）
- `modqueue_list(search=None, **params)` — 无参数（路径变量除外）
- `moderation_reports_list(search=None, **params)` — search：model_type, model_id, creator_id, creator_name, reason_matches, status, recipient_id, recipient_name；顶层/属性：`limit`（Reports per page）
- `moderation_report_show(report_id)` — 无参数（路径变量除外）
- `moderation_report_create(**attributes)` — 顶层/属性：`model_type`（Post, Comment or User）、`model_id`（The id of the reported record）
- `moderation_report_update(report_id, **attributes)` — 无参数（路径变量除外）
- `news_updates_list(search=None, **params)` — search：message_matches, creator_id, creator_name, is_deleted, order (created_at_asc)；顶层/属性：`limit`（Updates per page）
- `news_update_show(news_update_id)` — 无参数（路径变量除外）
- `news_update_create(message, **attributes)` — 顶层/属性：`message`（The banner text, in DText）
- `news_update_update(news_update_id, **attributes)` — 顶层/属性：`attributes`（同对应的 create 方法（源码 docstring 用 see 引用））
- `news_update_delete(news_update_id)` — 无参数（路径变量除外）
- `saved_searches_list(search=None, **params)` — search：query_matches, label, disable_labels, order (query, label)；顶层/属性：`limit`（Saved searches per page）
- `saved_search_create(**attributes)` — 顶层/属性：`query`（The tag query）、`label_string`（A display label）
- `saved_search_update(saved_search_id, **attributes)` — 顶层/属性：`attributes`（同对应的 create 方法（源码 docstring 用 see 引用））
- `saved_search_delete(saved_search_id)` — 无参数（路径变量除外）
- `site_credentials_list(search=None, **params)` — search：site, is_enabled, is_public, status, creator_id, updater_id, order；顶层/属性：`limit`（Credentials per page）
- `site_credential_show(site_credential_id)` — 无参数（路径变量除外）
- `site_credential_create(site, **attributes)` — 顶层/属性：`site`（The site name, e.g. "pixiv"）、`credential`（Keys are site specific, e.g. login and）
- `site_credential_update(site_credential_id, **attributes)` — 无参数（路径变量除外）
- `site_credential_delete(site_credential_id)` — 无参数（路径变量除外）
- `reactions_list(search=None, **params)` — search：model_type, model_id, creator_id, reaction_id；顶层/属性：`limit`（Reactions per page）
- `reaction_show(reaction_id)` — 无参数（路径变量除外）
- `reaction_create(**attributes)` — 顶层/属性：`model_type`（Post, Comment or ForumPost）、`model_id`（The id of the record to react to）
- `reaction_delete(reaction_id)` — 无参数（路径变量除外）
- `report_show(report, search=None, **params)` — search：period, from, to, columns, group, group_limit, mode and the model's own；顶层/属性：`report`（One of posts, post_approvals, post_appeals, post_flags, post_replacements, post_votes, media_assets, pools, comments, comment_votes, forum_posts, bulk_update_requests, tag_aliases, tag_implications, artist_versions, artist_commentary_versions, note_versions, wiki_page_versions, mod_actions, bans, users）
- `jobs_list(search=None, **params)` — search：id, active_job_id, job_class, queue_name, labels, priority, status, name (job class, matched fuzzily)；顶层/属性：`limit`（Jobs per page）
- `job_cancel(job_id)` — 无参数（路径变量除外）
- `job_retry(job_id)` — 无参数（路径变量除外）
- `job_run(job_id)` — 无参数（路径变量除外）
- `job_delete(job_id)` — 无参数（路径变量除外）
- `dtext_links_list(search=None, **params)` — search：link_type, link_target, model_type, model_id, linked_wiki_id, linked_tag_id；顶层/属性：`limit`（Links per page）
- `recommended_posts_list(search=None, **params)` — search：Search parameters forwarded to the recommender, typically {"user_id": ...} or {"post_id": ...}
- `counts_posts(tags=None, estimate_count=None, skip_cache=None)` — 顶层/属性：`tags`（The tag query; empty counts all posts）、`estimate_count`（Use a fast estimate instead of an exact count (the server default)）

<a id="sec-misc"></a>

### 来源与 IQDB（2 个方法）

| 方法 | 路由 | 源码 docstring 里的前提 | 状态 |
| :--- | :--- | :--- | :--- |
| `source_show(url, ref=None, mode=None)` | `GET source.json` | — | 源码对齐，未实测（读） |
| `iqdb_query(**params)` | `GET iqdb_queries.json` | — | 源码对齐，未实测（读） |

参数键：

- `source_show(url, ref=None, mode=None)` — 顶层/属性：`url`（The URL to inspect, e.g. a Pixiv artist page）、`ref`（A referer URL, for sites that need one）
- `iqdb_query(**params)` — 顶层/属性：`url, file_url, image_url`（The image to search for）、`hash`（A precomputed image hash）、`post_id`（Search for a post's own image）、`media_asset_id`（Search for a media asset's image）

合计 227 个方法。


## 附录：旧 API 页的逐资源契约表（原文迁入，未删改）

下面这张清单是重构前 `danbooru-api.md` 的逐资源方法表（方法、路由、凭据、关键参数）与随表说明，
按原文整段迁入这里，作为上节自动生成表格的交叉核对底本：凡上节没有体现的凭据细节（如「需登录 +
重新认证」「非 moderator 只看自己的」）与返回/语义注记，以本附录为准。本附录不再拆分到别处，也不在
用户页复制。

**已知取值错误**（保留原文以便对照，实际以模型为准，见「矛盾、易错点与客户端取舍」第 19 条）：
`moderation_report_create` 的 `model_type`、`post_disapproval_create` 的 `reason`、
`ban_create` 的 `duration`、`forum_topic_*` 的 `category_id`、`tag_update` 的 `category`、
`reaction_create` 的 `model_type` / `reaction_id`。这些字段在本附录与源码 docstring 里都还是旧值。

### 状态与账号

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `status()` | `GET status.json` | 匿名 | — |
| `rate_limits_list(search=None, **params)` | `GET rate_limits.json` | 匿名 | `search[id, action, key, limited, points]` |
| `user_profile()` | `GET profile.json` | 需登录 | — |
| `api_keys_list(search=None, **params)` | `GET api_keys.json` | 需登录 + 重新认证 | `search[id, key, user_id]`；返回里**不含** `key` |
| `api_key_create(**attributes)` | `POST api_keys.json` | 需登录 | `api_key[name, permitted_ip_addresses, permissions]`；创建时返回明文 key |
| `api_key_update(api_key_id, **attributes)` | `PUT api_keys/<id>.json` | 需登录 | 同 `api_key_create` |
| `api_key_delete(api_key_id)` | `DELETE api_keys/<id>.json` | 需登录 | — |

### posts（帖子）

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

### uploads 与媒体资源

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

### tags、别名、蕴含、相关标签

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

### artists

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

`Artist.name` 是与帖子上的画师标签对应的名称，不是外部站点的作者 ID。`Artist` 通过同名字段关联
`Tag`，默认标签类别为 artist；`urls` 则关联画师的地址记录。来源：`app/models/artist.rb:30-36`。

`search[url_matches]` 的匹配与归一化由上游完成，客户端只传递搜索值：

* `/artists.json`：完整 `http(s)://` 地址进入 `Source::Extractor.find(query).artists`，按来源解析得到
  规范主页地址，再通过 `Artist.has_normalized_url` 与 `ArtistURL.normalized_url_equals_any` 匹配；
  未识别来源进入 `ArtistFinder`，由 `ArtistURL.normalize_url` 归一化后查询。
  来源：`app/models/artist.rb:262-282,310-311`、`app/logical/source/extractor.rb:294-301`、
  `app/logical/artist_finder.rb:15-35`、`app/models/artist_url.rb:64-67,95-97`。
* `/artist_urls.json`：`ArtistURL.url_matches` 接受完整地址、`/正则/`、含 `*` 的通配与普通子串。
  完整地址经 `Source::URL` / `Source::Extractor` 解析主页，或进行 URL 归一化后再匹配；普通子串走
  大小写不敏感的包含匹配。`/artists.json` 的非完整 URL 查询也进入这一方法。
  来源：`app/models/artist_url.rb:19-21,43-67`、`app/models/artist.rb:271-278`。
* `any_name_or_url_matches` 根据输入是否为完整 `http(s)://` 地址，在 URL 与名称匹配之间选择；
  `any_name_matches` 查询当前名称、其他名称与团体名，并支持通配和正则。
  来源：`app/models/artist.rb:250-259,285-307`。

这些是 Danbooru 引擎的通用搜索契约，不包含客户端对特定外部平台的 ID 转换逻辑。

> **关于重定向类端点**：`artist_delete`、`artist_ban`、`artist_unban`、`wiki_page_show_or_new`、
> `forum_topics_mark_all_as_read` 等动作在服务端是 `redirect_to`。客户端会跟随重定向，
> 最终拿到什么格式**取决于目标端点的格式协商**——因为客户端始终发送 `Accept: application/json`，
> 目标端点通常仍返回 JSON（已实测 `artist_show_or_new` 跟随重定向后拿到 `200` +
> `application/json`，见 [verification.md](verification.md)）。
> 写类重定向端点**未实测**，因此不断言成功或失败；若最终响应不是 JSON，会抛
> `AnybooruAPIError`，此时用 `last_call['status_code']` 与 `last_call['url']` 判断实际结果。

### comments、notes、投票

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

### pools（合集）

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

### wiki

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

### users、收藏、收藏分组

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

### forum（论坛）

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

### dmails（站内信）

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `dmail_list(search=None, **params)` | `GET dmails.json` | 需登录（只能看自己的） | `search[id, title, body, message_matches, is_read, is_deleted, to_id, to_name, from_id, from_name, folder]` |
| `dmail_show(dmail_id)` | `GET dmails/<id>.json` | 需登录（本人） | 也支持 `key=` 签名链接 |
| `dmail_create(title, body, to_name=None, to_id=None)` | `POST dmails.json` | 需登录 | `dmail[to_name, to_id, title, body]` |
| `dmail_update(dmail_id, **attributes)` | `PUT dmails/<id>.json` | 需登录（本人） | `dmail[is_read, is_deleted]`；**删除邮件也走这里** |
| `dmails_mark_all_as_read()` | `POST dmails/mark_all_as_read.json` | 需登录 | — |

### 审核与运维

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
| `recommended_posts_list(search=None, **params)` | `GET recommended_posts.json` | 匿名 | `limit` ≤ 200；`search[...]` 原样发给推荐服务 |

### 杂项

| 方法 | 路由 | 凭据 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `counts_posts(tags=None, estimate_count=None, skip_cache=None)` | `GET counts/posts.json` | 匿名 | 顶层 `tags`、`estimate_count`、`skip_cache`；返回 `{"counts":{"posts":N}}` |
| `source_show(url, ref=None, mode=None)` | `GET source.json` | 匿名 | 顶层 `url`、`ref`、`mode` |
| `iqdb_query(**params)` | `GET iqdb_queries.json`（同一 action 也接受 `POST`） | 匿名（能力依赖） | `search[url, hash, image_url, file_url, post_id, media_asset_id, limit, similarity]`，裸参数亦兼容 |

## 全局契约与上游出处

### 路径与格式

* 路径是站点根地址之后的相对路径，**没有** API 版本前缀；原生方法显式用 `.json`，`request()` 为无后缀
  路径补上（`anybooru/danbooru.py`）。
* 重定向目标即使没有后缀，也可通过 `Accept: application/json` 协商到 JSON；请求了不支持的格式得到
  `406`（`app/controllers/application_controller.rb:141`）。
* 路径里的 ID 或标题若含特殊字符，需要调用者自行 URL 转义（`wiki_page_show` 内部已转义）。

### 认证

* HTTP Basic：`Authorization: Basic base64(username:api_key)`；服务端另接受
  `?login=<name>&api_key=<key>` 的查询参数形式。
* 只要出现认证信息但**不完整或无效**，服务端返回 `401`，不会静默降级为匿名；匿名身份代入
  `User.anonymous`，读接口默认放行，权限由服务端 Pundit 判定，权限不足 `403`。
* 客户端只在 `username` 或 `api_key` 非空时附加 Basic 头（缺项按空串补），不做本地鉴权判断。

### 参数分层

| 层 | 形式 | 说明 |
| :--- | :--- | :--- |
| 顶层参数 | `?limit=10&page=2&tags=...` | 分页、内容搜索、控制器直接读取的字段 |
| 搜索参数 | `?search[x]=y` | 模型 `search` 方法认识的过滤条件 |

* 列表方法签名统一为 `xxx_list(self, search=None, **params)`；`search` 整包原样发成 `search[...]`，
  不做白名单拦截；`**params` 是顶层参数。
* **帖子列表例外**（`post_list(**params)`）：查询走顶层 `tags` 元标签，不吃 `search` 字典
  （`app/controllers/posts_controller.rb:143` 读 `params[:tags]`，交给 `PostSets::Post`）。
* `autocomplete_list(query, type=None, limit=None)` 显式接收查询词并放进 `search`。
* 写方法的 `post[...]`、`comment[...]` 就是请求体里的嵌套键：无文件时整个 `data` 以 **JSON 请求体**
  发送（结构原样保留，显式空数组也会发出去），带文件时改用 Rails 表单 / multipart；查询串 `params`
  始终是 Rails 括号形式。
* 端点无关的顶层参数：`page` / `limit`、`only`（选字段与嵌套关联，只对 json/xml 生效）、
  `redirect`（结果唯一时 302 到对象页面）、`safe_mode`（强制 `rating:g`）、`save_data`（省流模式）。
* **未知搜索参数被静默忽略**，不报错——这正是旧参数失效时表现为「返回全集」的原因。

### 两个请求侧的硬性约束

* **`GET` 不能带请求体**：`RequestBodyNotAllowedError` → `400`
  （`app/controllers/application_controller.rb:126-127`；功能测试见
  `test/functional/application_controller_test.rb:22-28`）。
* **空字符串的 `search` 值会被清理**：服务端 `deep_reject_blank` 之后 `302` 到清理过的 URL
  （`app/controllers/application_controller.rb:318-326`）。客户端对 `None` 直接省略，不受影响。

### 分页与配额（上游出处）

| 项目 | 值 | 出处 |
| :--- | :--- | :--- |
| 默认每页 | `Danbooru.config.posts_per_page` | `app/logical/pagination_extension.rb:37` |
| 通用 `limit` 上限 | 1000 | 同上 `paginate(..., max_limit: 1000)` |
| posts `limit` 上限 | 200 | `app/logical/post_sets/post.rb:12`（`MAX_PER_PAGE`） |
| uploads / media_assets / ai_tags / modqueue 的 `limit` | clamp 到 `0..200` | `uploads_controller.rb:13`、`media_assets_controller.rb:7`、`modqueue_controller.rb:10` |
| 页码上限 | 匿名与普通用户 1000，Gold 及以上 5000 | `app/models/user.rb:674-680` |
| 超页 | `410` + `You cannot go beyond page N.` | `pagination_extension.rb:53-54`、`application_controller.rb:142-143` |
| 标签数上限 | 匿名 2、Gold 6、Platinum(member+promotion) 不限 | `app/models/user.rb:682-691` |
| 超标签数 | `422` + `You cannot search for more than N tags at a time.` | `post_query.rb:319-322`、`application_controller.rb:144-145` |
| ID 游标 | `page=a<id>`（更新）/`b<id>`（更旧） | `pagination_extension.rb` 的分页分支 |

### 搜索后缀（`app/logical/concerns/searchable.rb`）

模型先声明可搜索属性，`SearchContext` 再按列类型生成参数族：

| 列类型 | 可用参数（`name` 为属性名） |
| :--- | :--- |
| string | `name`、`name_present`、`name_eq`、`name_not_eq`、`name_like`、`name_ilike`、`name_regex`、`name_array`、`name_comma`、`name_space`、`name_lower_array`、… |
| text | string 的全部 **+** `name_matches`（全文；含 `*` 时按 `ILIKE`） |
| 数值 / 时间 | `name`（`5`、`>5`、`5..10`、`5,6,7`）、`name_not`、`name_gt`、`name_gteq`、`name_lt`、`name_lteq` |
| boolean | `name`（`true/false/1/0/yes/no`） |
| 关联 | FK 字段族；关联对象是 User 时 `assoc_name`，是 Post 时 `assoc_tags_match`；`has_assoc=true/false`；嵌套 `search[assoc][...]` |
| 通用 | `search[id]` 支持 `1,2,3` 与范围；`order` 由各模型自解释 |

### 失败与能力依赖

* 非 2xx 抛 `AnybooruHTTPError`（状态码、URL、正文原样保留），2xx 但非 JSON 抛 `AnybooruAPIError`；
  状态码清单见 [errors.md](errors.md)。
* **archive 服务未配置时 `501`**：`PostVersion.enabled?` 为假时 `post_versions#index|undo` 抛
  `NotImplementedError`（`post_versions_controller.rb:42-45`），`PoolVersion.enabled?` 同理
  （`pool_versions_controller.rb:40-42`），由 `application_controller.rb:156-157` 渲染成
  `501 This feature isn't available: ...`。
* IQDB 与推荐服务同样依赖站点配置，客户端不给它们任何本地替代行为。
* **纠正旧摘要中的 IQDB=501 泛化**：`app/logical/iqdb_client.rb:139-142` 在未配置服务时直接返回 `[]`；
  `app/controllers/iqdb_queries_controller.rb:14-16` 也把 `IqdbClient::Error` 转为空匹配数组。
  这与 archive 的 `NotImplementedError → 501` 是不同分支；未新增请求验证。
* `status()` 的真实序列化字段见 `app/logical/server_status.rb:19-63`：`ip`、`headers`、`instance`、
  `version`、`server`、`postgres`、`redis`；原摘要的“当前身份对象”不是它的返回结构。

## 权限与字段级过滤器

字段裁剪都由 Pundit policy 的 `api_attributes` 决定（`ApplicationRecord#api_attributes` 取
`Pundit.policy(user, self)`；`app/models/application_record.rb:85-89`）。未定制该方法的资源按
`ApplicationPolicy#api_attributes` 返回**全部列名**（`app/policies/application_policy.rb:116-119`）。

| 位置 | 过滤 |
| :--- | :--- |
| `post_policy.rb:118-124` | 补 `has_large`/`has_visible_children`/`media_asset` 与 `tag_string_<category>`；仅在帖子对当前用户可见时给 `file_url`/`large_file_url`/`preview_file_url`；不可见时**去掉 `md5`** |
| `post_policy.rb:99-116` | 强参数：create 收顶层 `upload_id`/`media_asset_id`/`upload_media_asset_id` + `post[...]`；update 收 `tag_string old_tag_string parent_id old_parent_id source old_source rating old_rating has_embedded_notes` |
| `api_key_policy.rb:32-34` | 去掉 `key`（明文只在创建响应里） |
| `dmail_policy.rb:47-49` | 追加 `key`（签名链接） |
| `media_asset_policy.rb:24-27` | 补 `variants`；`can_see_image?` 为假时去掉 `md5`/`file_key`/`variants` |
| `media_asset_policy.rb:8-10` | `destroy?` 要求 **admin**（见下文矛盾项） |
| `background_job_policy.rb:26-29` | 无 `can_see_params?` 时去掉 `serialized_params`，另补 `runtime_latency`/`queue_latency` |
| `comment_policy.rb:54-57` | 无 `can_see_creator?` 时去掉 `creator_id`；评论已删除且不可见时再去掉 `updater_id`/`body`/`score`/`do_not_bump_post`/`is_sticky` |
| `post_vote_policy.rb:32-35`、`post_flag_policy.rb:28-31`、`post_disapproval_policy.rb:32-35` | 分别去掉 `user_id` / `creator_id` / `user_id` |
| `user_event_policy.rb:16-19` | 无 `can_see_session?` 时去掉 `session_id`/`user_agent` |
| `user_policy.rb:85-104` | 匿名只有 `id created_at name inviter_id level level_string` + 各类计数 + `is_banned/is_deleted`；本人再追加偏好与 `favorite_count`、`statement_timeout`、`tag_query_limit` 等；`last_ip_addr` 另需 IP 地址权限 |
| `mod_action_policy.rb:8-10`、`pool_policy.rb:40-42`、`post_version_policy.rb:12-14` | 分别追加 `category_id`、`post_count`、`obsolete_*`/`unchanged_tags` |
| `app/models/upload.rb:42`、`post_vote.rb:25`、`api_key.rb:32`、`user_name_change_request.rb` 等 | `visible(user)` 作用域决定列表能看到谁：非 moderator 的上传列表、非本人投票、他人的 API key 等都不返回 |

强参数的其他出处：`upload_policy.rb:28-30`（`[:source, :referer_url, { files: {} }]`，所以文件字段是
`upload[files][<索引>]`）、`post_replacement_policy.rb:12-19`（create 收
`replacement_url replacement_file final_source tags`）。

## 矛盾、易错点与客户端取舍

1. **`upload_media_asset_id` 在顶层**：`posts#create` 直接读 `params[:upload_media_asset_id]`
   （`posts_controller.rb:62`），放进 `post[...]` 会被当成未知属性。同一 policy 里还允许
   `upload_id`、`media_asset_id` 两种旧式入口。
2. **`old_*` 是并发合并用的输入**：update 强参数里成对出现（`old_tag_string`、`old_parent_id`、
   `old_source`、`old_rating`），服务端在 `Post#merge_old_changes`（`app/models/post.rb:391-410`）
   里使用它们：`old_parent_id` / `old_source` / `old_rating` 与本次写入的值相同时回退成先前的值，
   `old_tag_string` 用于计算标签增删（`PostEdit`）。客户端只是把值原样发出去，不代填、不重试。
3. **posts 顶层 `tags`**：`post_list` 不吃 `search`；写成 `search={'tags': ...}` 会被静默忽略。
4. **`post_delete` 需要 `commit=Delete`**：控制器只在 `params[:commit] == "Delete"` 时删除
   （`posts_controller.rb:88-91`），方法是替你带上；理由为空会被回滚（删除会记为 post flag，必需理由）。
5. **`media_asset_delete` 是 admin 操作**：客户端 docstring 写的是 "requires moderator level"，上游
   `media_asset_policy.rb:8-10` 实为 `user.is_admin?`。以 policy 为准；docstring 待修。
6. **投票撤票只认投票 id**：`resources :post_votes`（`routes.rb:189`）存在 destroy，但控制器用
   `params[:id]`（`post_votes_controller.rb:33-37`），而嵌套的 `resource :votes`（`routes.rb:200`）
   是单数路由、不提供该 id——所以只能先查投票 id，再 `post_vote_delete(vote_id)`。`comment_votes`
   同理（`routes.rb:74,76`）。
7. **`modqueue_list` 返回帖子列表**，不是队列记录（`modqueue_controller.rb:7-13`：`mode` 默认
   `gallery`，`search[order]` 默认 `modqueue`，`limit` clamp 200）。
8. **`tag_list` 在 JSON 下 `hide_empty` 没有默认值**：只有显式传真值才走 `nonempty`
   （`app/models/tag.rb:405-409`），HTML 页面才有默认过滤。
9. **`note_list` 没有 `creator_id` / `creator_name`**：`Note.search` 声明的属性是
   `id created_at updated_at is_active x y width height body version post`（`app/models/note.rb:29-31`），
   旧参数会被静默忽略。
10. **`wiki_page_list` 的顶层 `title=` 会 302** 到标题搜索；要列表结果就用 `search={'title': ...}`。
11. **重定向类动作**：`artist_delete` / `artist_ban` / `artist_unban` / `wiki_page_show_or_new` /
    `forum_topics_mark_all_as_read` 在控制器里是 `redirect_to`。客户端始终发
    `Accept: application/json`，目标端点通常仍回 JSON（`artist_show_or_new` 已实测 302 → `200` +
    `application/json`）；最终响应不是 JSON 时抛 `AnybooruAPIError`。**写类重定向未实测**，因此不能
    断言成功或失败，只能看 `last_call`。
12. **`post_versions` 没有 show**：路由只有 index 与 undo，客户端因此没有 `post_version_show`
    （对照：tag/artist/wiki/note 都有版本 show）。
13. **`tag_alias_delete` / `tag_implication_delete` 的语义是拒绝**（BUR 审批流），不是删除既有别名；
    创建别名与蕴含没有专用方法，走 `bulk_update_request_create`。
14. **`dmail_update(is_deleted=True)` 才是删除**：dmails 没有 destroy 路由。
15. **`Artist.name` 不是外部站点作者 ID**：它是与作品上的画师标签对应的名称；主页地址是独立的
    `artist_urls` 记录。`URL`/`artist_urls` 的匹配规则见下节。
16. **投票分数是数字，docstring 写错了**：三个投票方法在源码 docstring 里写 ``up`` / ``down``，
    但模型校验只接受数字——`post_vote.rb:13` 与 `comment_vote.rb:11` 是 `[1, -1]`，
    `forum_post_vote.rb:9` 是 `[-1, 0, 1]`（0 为中性），控制器直接把 `params[:score]` 交给模型。
    用户页按 `1` / `-1`（论坛另加 `0`）记载。
17. **`ArtistURL` 匹配语义（`search[url_matches]`）**：`/artists.json` 的完整 `http(s)://` 查询先经
    `Source::Extractor` 按来源解析出规范主页地址，再经 `Artist.has_normalized_url` /
    `ArtistURL.normalized_url_equals_any` 匹配；未识别来源落到 `ArtistFinder`，用
    `ArtistURL.normalize_url` 归一化后查询（`app/models/artist.rb:262-282,310-311`、
    `app/logical/source/extractor.rb:294-301`、`app/logical/artist_finder.rb:15-35`、
    `app/models/artist_url.rb:64-67,95-97`）。`/artist_urls.json` 的 `url_matches` 还接受
    `/正则/`、含 `*` 的通配与普通子串（大小写不敏感的包含匹配，
    `app/models/artist_url.rb:19-21,43-67`）。`any_name_or_url_matches` 按输入是否为完整地址在 URL
    与名称之间选择，`any_name_matches` 覆盖当前名、其他名与团体名（`app/models/artist.rb:250-259,285-307`）。
    这些是引擎通用契约，**没有任何「平台作者 ID → 标签」的转换客户端逻辑**。
18. **部分方法的 docstring 前提与控制器/policy 事实不一致**（用户页按后者写，未实测）：
    * `media_asset_delete` 见上文第 5 条（docstring `moderator`，policy 实为 admin）。
    * `ip_bans_list` / `ip_ban_show`：docstring 没写前提，`IpBanPolicy#create?|index?|update?` 都是
      `user.is_moderator?`（`app/policies/ip_ban_policy.rb:4-16`，`show?` 继承 `index?`），因此列表与
      单条都要求 moderator 及以上。
    * `moderation_reports_list` / `moderation_report_show`：docstring 写 "requires moderator level"，
      但 `ModerationReportPolicy#index?|show?` 只要求非匿名（`app/policies/moderation_report_policy.rb:4-10`），
      可见范围由 `ModerationReport.visible` 决定——moderator 看全部，其他登录用户只看自己的
      （`app/models/moderation_report.rb:38-45`），用户页按这个口径写。
    * `site_credential_show` / `site_credential_delete`：公开项与私有项的判定分别落在 admin/owner
      与本人上，docstring 只写 "requires admin level"。
    * `favorite_list` / `upload_list`：docstring 的 "requires login for other users' ..." 与
      `visible(user)` 作用域一致——匿名仍能读公开收藏，登录后按归属过滤。
    * `api_keys_list` 及 `api_key_create|update|delete`：控制器有
      `before_action :requires_reauthentication`（`app/controllers/api_keys_controller.rb:4`），
      而本库只发 HTTP Basic，没有会话重新认证流程——这几个方法在真实站点上可能过不了这道检查，
      未实测（旧表记的「需登录 + 重新认证」就是指这个）。
    * `note_preview`：`NotePolicy#preview?` 明确返回 true（`app/policies/note_policy.rb:4-6`）；控制器
      只构造 `Note.new` 并返回 `sanitized_body`，不保存（`app/controllers/notes_controller.rb:64-68`）。
      正文走 `NoteSanitizer`（`app/models/note.rb:137-139`），是 HTML，不是 docstring 所说的 DText。
      本轮匿名 POST 实际被全局 CSRF 校验拒绝，返回403 `ActionController::InvalidAuthenticityToken`；
      policy允许访问不等于能越过此校验，不能把它记成成功预览。
19. **枚举值 docstring 与模型不符**（本轮逐条读上游模型后修正，用户页按模型写）：
    * **举报对象的类型**：`ModerationReport::MODEL_TYPES = %w[Dmail Comment ForumPost]`
      （`app/models/moderation_report.rb:4`），而客户端 docstring 与旧 API 表写的是
      `Post, Comment or User`——帖子和用户**不可举报**。可举报性还由各自 policy 的 `reportable?`
      决定：评论要非本人、作者非 moderator、未删除且一年内（`comment_policy.rb:12-14`），论坛帖子同理
      （`forum_post_policy.rb:36-38`），站内信要属于本人、是收件人、非自动消息、发件人非 moderator
      且一年内（`dmail_policy.rb:25-27`）。
    * **不批准理由**：`PostDisapproval::REASONS = %w[disinterest poor_quality breaks_rules]`
      （`app/models/post_disapproval.rb:5`），docstring 多写了 `borderline_quality` /
      `borderline_safety`；`message` 另受 140 字符长度校验（同文件 `:15`）。
    * **封禁期限**：`Ban::DURATIONS` 只有 1 day / 3 days / 7 days / 1 month / 3 months / 6 months /
      1 year / `FOREVER = 100.years`，且 `validates :duration, presence: true`
      （`app/models/ban.rb:4-5,36`）——docstring 的“blank is permanent”不成立；永久封禁要显式传
      `100 years`。批量删除数据只覆盖最近 3 天（同文件 `MAX_DELETION_AGE`，`:8`）。
    * **论坛分类**：`ForumTopic` 的 `category` 枚举只有 `General: 0` / `Tags: 1` /
      `Bugs & Features: 2`（`app/models/forum_topic.rb:6-10`），旧表里的 `3 = bulk update requests`
      不存在，传 3 会被枚举校验拒绝。
    * **标签类别**：`TagCategory` 是 `GENERAL 0` / `ARTIST 1` / `COPYRIGHT 3` / `CHARACTER 4` /
      `META 5`（`app/logical/tag_category.rb:9-13`），docstring 漏了 `5`（meta）。
    * **反应**：`Reaction::MODEL_TYPES = %w[Post Comment ForumPost User Tag Pool]`，`reaction_id` 必须
      来自站点配置的 `reactions` 键（`app/models/reaction.rb:4-6`，默认配置里 `reactions` 是空字典，
      `config/danbooru_default_config.rb`），docstring 只列了前三种类型并举例 `"heart"`。
    * **评论分组**：`group_by` 默认值只在带 `search` 时被补成 `"comment"`
      （`app/controllers/comments_controller.rb:14-22`）；不带 `search` 的调用落到 `index_by_post`，
      返回的是帖子列表——用户页已写明这一分支。

## SQL、缓存与服务端行为

* `counts_posts` 默认走**估算 + 缓存**（`counts_controller.rb:8-9` 把 `estimate_count`、`skip_cache`
  直接交给 `PostQuery#fast_count`）；要精确计数或绕过缓存必须显式传参。
* 计数与搜索都受 `statement_timeout` 影响（按等级取值，`user.rb:669-680`），超时是 `500`
  `The database timed out running your query.`（`application_controller.rb:123-124`）。
* `related_tag` 的采样规模由请求参数决定（`search_sample_size` 默认 5000、`tag_sample_size` 默认
  500），返回 `query`/`post_count`/`tag`/`related_tags`/`wiki_page_tags`。
* `posts` 列表走 `PostSets::Post`，查询在服务端被编译成元标签 AST；`page` 超过上限直接 `410`，
  不会退化成空页。
* 标签搜索的 `order`、`hide_empty`、`is_empty` 等由模型自身解释，客户端不排序、不缓存、不重试。
* 上传链路：**两条 multipart 路径**——`uploads#create`（`upload[files][<索引>]`，`files` 与 `source`
  互斥，`upload.rb:77-83`；压缩包由服务端展开，单次上传文件数上限 100，`upload.rb:93-118`）与
  `post_replacements#create`（`post_replacement[replacement_file]`，见
  `post_replacement_policy.rb:12-14`、`post_replacement_processor.rb:14`）。
  上传完成后用 `post_create(upload_media_asset_id=...)` 建帖，该 id 来自上传响应里
  `upload_media_assets` 关联记录的 `id`（`uploads_controller.rb:48` 显式 include 该关联）。

## 可调用但没有原生方法的 JSON 路由

这些是正常的 JSON 端点，只是没有原生方法，用 `request(method, path, params=..., data=...)` 访问。
均未实测。

| 路由 | 凭据 | 说明 |
| :--- | :--- | :--- |
| `GET metrics.json`、`GET statistics.json`、`GET metrics/statistics.json`、`GET metrics/instance.json` | 匿名 | 默认格式是 text，显式 `.json` 可用 |
| `GET emails.json` | moderator+ | `search[user_id, address, is_verified, is_deliverable]` |
| `GET emails/<id>.json` | 本人或 moderator | — |
| `GET|PUT|DELETE users/<user_id>/email.json` | 需登录 + 重新认证 | `emails` 资源只有 index/show |
| `GET users/<user_id>/email/verify.json`、`POST .../send_confirmation.json` | 需登录 | — |
| `GET password/edit.json`、`PUT password.json`、`GET users/<user_id>/password/edit.json`、`PUT users/<user_id>/password.json` | 需登录 | `user[current_password, password, password_confirmation, verification_code]` |
| `PUT password_reset.json` | 持签名 `signed_id` | `user[signed_id, password, password_confirmation]` |
| `GET users/<user_id>/totp/edit.json`、`PUT|DELETE users/<user_id>/totp.json` | 本人 + 重新认证 | `totp[signed_secret, verification_code]` |
| `GET|POST users/<user_id>/backup_codes.json`、`GET users/<user_id>/backup_codes/confirm_recover.json`、`POST .../recover.json` | 本人 + 重新认证 | — |
| `GET upgrade_codes.json` | owner | `search[code, status, creator_id, redeemer_id]` |
| `POST upgrade_codes/upgrade.json` | 需登录 | `upgrade_code[code]` |
| `GET user_upgrades.json`、`GET user_upgrades/<id>.json` | 需登录（visible 过滤） | `search[id, upgrade_type, status, transaction_id, recipient_id, purchaser_id]` |
| `GET upgrade.json` | 匿名 | `user_id` 选择收件人，返回未保存的 UserUpgrade；`GET user_upgrades/new` 是到此的重定向 |
| `POST user_upgrades.json`、`PUT user_upgrades/<id>/refund.json` | 非匿名 / owner | `upgrade_type`、`payment_processor`、`country`、`promo` |
| `GET pools/<pool_id>/order/edit.json` | 需登录（pool 更新权限） | 返回 pool，用于排序编辑 |
| `GET favorite_groups/<id>/order/edit.json` | 需登录 | 返回 favorite group |
| `POST moderator/post/posts/<id>/ban.json`、`/unban.json` | approver+ | 返回该 post |
| `GET post/index.json`、`GET tag/index.json` | 匿名 | Danbooru 1 遗留 API，字段集与 `/posts.json` 不同（`has_comments`、`status`、`author`、`file_url` 等） |
| `GET up.json`、`/up/postgres`、`/up/redis` | 匿名 | 健康检查，`head 204/503`，无响应体 |

### 初始化、编辑与嵌套路由

`new` / `edit` 并不天然是 HTML-only：下列控制器动作显式 `respond_with`，在已有 `.json` 路由上可返回
对象，均未实测。`new` 的权限继承该资源的 `create?`，`edit` 继承 `update?`，API keys 仍需重新认证。
初始化参数用对应的创建方法命名空间，详情编辑路径用资源 ID，两者都不分页。

| 路径模式（全部 GET，后缀 `.json`） | 已有资源 / 控制器 |
| :--- | :--- |
| `<资源>/new` 和 `<资源>/<id>/edit` | `api_keys`、`artists`、`bans`、`bulk_update_requests`、`comments`、`favorite_groups`、`forum_posts`、`forum_topics`、`news_updates`、`pools`、`post_appeals`、`post_flags`、`user_feedbacks`、`users`、`wiki_pages` |
| `<资源>/new` | `dmails`、`ip_bans`、`moderation_reports`、`post_replacements`、`site_credentials`、`uploads`、`user_name_change_requests` |
| `<资源>/<id>/edit` | `post_disapprovals`、`saved_searches`、`tags` |

出处：对应 `app/controllers/<资源>_controller.rb` 的 `new`/`edit` 与
`app/policies/application_policy.rb:23-36`；`site_credentials_controller.rb:18-20` 明确
`respond_with`，不是 HTML-only。`uploads/new` 还接受顶层 `url`、`ref`；`dmails/new` 支持
`respond_to_id`、`forward`；`comments/new` 支持引用评论的 `id`；`users/new` 接受 `user[url]` 或
`url`。具体预填字段服从相应 policy。

嵌套形式与顶层控制器共享参数、分页与权限，`request()` 可直接调用：

* `/posts/<post_id>/events`、`/posts/<post_id>/favorites`、`/posts/<post_id>/replacements`、
  `/posts/<post_id>/replacements/new`；
* `/uploads/<upload_id>/assets/<id>`；
* `/users/<user_id>/actions`、`favorites`、`favorite_groups`、`uploads`、`events`；
* `/users/<user_id>/api_keys` 及 `new` / `<id>/edit` / `<id>` 的创建、更新、删除，动作与顶层相同；
* `GET /users/<id>/change_name` 同 `user_name_change_requests#new`；
* `GET /comments/<comment_id>/votes` 同 `comment_votes#index`；`POST /post_votes` 接受顶层
  `post_id` / `score`，等价于原生嵌套投票方法。

注意 `DELETE /posts/<post_id>/votes` 与 `DELETE /comments/<comment_id>/votes` 虽然在路由中存在，但
控制器读 `params[:id]`，单数嵌套路径不提供它（见上文矛盾项 6），所以不要用这两条撤票；收藏删除以
post ID 为标识，走 `favorite_delete(post_id)`。

### explore（发现内容）

真实 JSON 动作，未实测。出处：`config/routes.rb:37-46`、
`app/controllers/explore/posts_controller.rb:7-52`；权限见 `ExplorePostPolicy`，不使用模型 `search` 字典。

| GET 路径（后缀 `.json`） | 参数与返回 |
| :--- | :--- |
| `explore/posts/popular` | 顶层 `date`、`scale=day/week/month`、`page`、`limit`；按日期范围返回高分帖子 |
| `explore/posts/viewed` | 顶层 `date`、`scale`；Reportbooru 浏览热度帖子 |
| `explore/posts/searches` | 顶层 `date`、`scale`；Reportbooru 搜索排名 |
| `explore/posts/missed_searches` | Reportbooru 未命中搜索排名 |

后三项依赖站点 Reportbooru 服务配置，库不提供本地替代数据。原生 `*_show(id)` 若没有 `**params` 形参而该路由
还接受 `only`、分页、签名 key 等参数，请用 `request('GET', '<资源>/<id>.json', params={...})` 传递。

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

这些路径**不能作为端点使用**；具体返回哪个状态码取决于框架层错误处理，未经线上验证，不做声明。

## 事实迁移记录（旧三页 → 新位置）

| 原事实（旧页） | 新位置 |
| :--- | :--- |
| `post_update` 的 `old_*` 属性长表 | 用户页保留“并发保护”提示与可复制调用（`danbooru-api.md#posts帖子-37-个方法`），属性全集在本文「权限与字段级过滤器」的 `post_policy.rb:99-116` 行 |
| posts 顶层 `tags`、不吃 `search` | 用户页 `danbooru-api.md` 的 posts 节与 `danbooru.md#常见坑` 各一处，上游出处本文「参数分层」 |
| `upload_media_asset_id` 顶层 | `danbooru.md#常见坑`、`danbooru-api.md` 的 posts/uploads 节，出处本文矛盾项 1 |
| archive 未配置 → `501` | `danbooru.md#边界与未实测`、`danbooru-api.md` 的 posts/pools 条目与末尾节，出处本文「失败与能力依赖」 |
| `ArtistURL` / `url_matches` 匹配语义与源码行号 | 用户页只剩一句语义提示（`danbooru-api.md#artists`），完整规则与行号在本文矛盾项 16 |
| 原 API 页的「可调用但没有原生方法的 JSON 路由」「排除项」「new/edit 与嵌套路由」「explore」 | 本文同名列的小节，内容未删 |
| 原 API 页逐方法表的「路由 / 凭据 / 关键参数」 | 本文「逐资源：路由、参数键与状态」（由源码与 docstring 生成，避免手抄漂移） |
| 原 API 页的「验证状态」节 | 本文「状态口径与总量」+ `danbooru-api.md` 末尾「边界与未实测」 |
| 原能力页引用的 `PostPolicy`/`UserPolicy` 等内部符号 | 本文「权限与字段级过滤器」，能力页改为用户可见的字段表现 |

* 本轮把枚举类事实逐条对回上游模型后修正了六处 docstring 偏差（举报对象类型、不批准理由、封禁期限、
  论坛分类、标签类别、反应类型），明细见「矛盾、易错点与客户端取舍」第 19 条；用户页已按模型取值改写，
  本次改动没有新增网络请求。
