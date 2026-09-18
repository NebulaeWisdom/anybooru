# Danbooru 能力入口：我想做什么，该用哪个接口？

**不知道从哪个方法查起，先看这页；已经知道端点，再看 [方法参考](danbooru-api.md)。**

- **不登录也能开始**：找图、查帖子、标签、画师、wiki、公开评论、笔记、合集、公开论坛、用户与公开收藏。
- **登录后才能改内容**：上传、发帖、评论、收藏、投票、编辑等；删除、审核、管理还可能要求更高等级。
- **库负责调用 JSON API**，不是下载器或自动采集器：不自动保存图片、不自动翻页，也不保证每条记录都向
  匿名用户开放文件地址。

## 先按目的找入口

下表的调用都是字面参数，`client` 是已创建的 `Danbooru` 客户端。初始化方式见
[客户端用法](danbooru.md)。

| 我想做什么 | 用哪个方法 | 可以直接抄的调用 | 是否需要登录 |
| :--- | :--- | :--- | :--- |
| 按标签、评分、时间找图 | `post_list`：过滤条件写成顶层 `tags` 元标签 | `client.post_list(tags='rating:g order:score', limit=20)` | 匿名可查；匿名一次最多 2 个标签，超出 `422` |
| 看一张图的详情 | `post_show` | `client.post_show(12090564)` | 匿名可查 |
| 随机取一张图 | `post_random`：可在 `tags` 里限定范围 | `client.post_random(tags='rating:g')` | 匿名可查；无匹配时 `404` |
| 取得原图或预览图地址 | `post_show` 返回的 `file_url` / `large_file_url` / `preview_file_url` | `post = client.post_show(12090564)` 后读 `post['file_url']` | 地址取决于该帖对当前身份是否可见；保存文件要用别的 HTTP 客户端 |
| 按作者找作品 | `post_list`：画师名本身就是标签 | `client.post_list(tags='fuzichoco', limit=20)` | 匿名可查 |
| 查画师与主页 URL | `artist_list` / `artist_urls_list` / `artist_show` | `client.artist_list(search={'url_matches': 'https://www.pixiv.net/users/27517'})` | 匿名可查 |
| 找标签、别名与相关标签 | `tag_list` / `tag_aliases_list` / `related_tag` | `client.tag_list(search={'name_matches': 'touhou'}, limit=10)` | 匿名可查 |
| 输入关键词时给出补全建议 | `autocomplete_list` | `client.autocomplete_list('touh', type='tag', limit=10)` | 匿名可查 |
| 查 wiki 或原作者说明 | `wiki_page_show` / `wiki_page_list` / `artist_commentary_show` | `client.wiki_page_show('help:api')` | 匿名可读可见页面 |
| 看评论和图上笔记 | `comment_list` / `note_list` | `client.comment_list(search={'post_id': 12090564})` | 匿名可读；发表与修改需登录 |
| 按合集看系列作品 | `pool_list` / `pool_show` / `pool_gallery` | `client.pool_show(12345)` | 匿名可读；创建、修改需登录 |
| 查用户，查看或整理收藏、保存搜索 | `user_show` / `favorite_list` / `favorite_create` / `favorite_group_create` / `saved_search_create` | `client.favorite_create(12090564)` | 公开资料与公开收藏可匿名；自己的收藏操作需登录 |
| 上传文件并发帖 | `upload_create` → `post_create` | `client.upload_create(source='https://example.com/a.jpg')`，再用返回的 `upload_media_assets[0]['id']` 调 `client.post_create(55, tag_string='1girl solo', rating='g')` | 需登录，且上传必须属于你 |
| 修改标签、来源、翻译状态 | `post_update` / `post_mark_as_translated` | `client.post_update(12090564, tag_string='1girl solo', old_tag_string='1girl')` | 需登录，且对该帖有编辑权限 |
| 投票、标记待删、提出申诉 | `post_vote_create` / `post_flag_create` / `post_appeal_create` | `client.post_vote_create(12090564, score=1)` | 需登录；标记不等于审核员删除 |
| 举报、看审核队列、批准帖子 | `moderation_report_create` / `modqueue_list` / `post_approval_create` | `client.modqueue_list(limit=20)` | 举报需登录，且只能举报评论、论坛帖子、站内信；队列与批准需 approver |
| 查论坛、发站内信 | `forum_topics_list` / `forum_posts_list` / `dmail_create` | `client.dmail_create(title='标题', body='正文', to_name='someone')` | 公开论坛可匿名读；发帖与站内信需登录 |
| 查修改历史、统计或来源 | `post_versions_list` / `counts_posts` / `source_show` | `client.counts_posts(tags='rating:g')` | 多数可匿名读；版本历史依赖站点 archive 服务 |
| 以图搜图或看推荐 | `iqdb_query` / `recommended_posts_list` | `client.iqdb_query(url='https://example.com/a.jpg')` | 源码提供匿名入口，但依赖站点配置的服务；IQDB 未配置返回空数组 |

**两个容易选错的地方**：帖子列表把过滤写在顶层 `tags`（写成 `search={'tags': ...}` 会被静默忽略），其他
大多数列表放在 `search` 字典；上传成功不等于已发帖，还要用上传媒体 id 调 `post_create`。翻页看
[pagination.md](pagination.md)，请求失败看 [errors.md](errors.md)。

## 匿名和登录，能力差在哪里？

“可匿名”只表示源码允许进入该读接口，不保证一定有结果、能看到所有记录，或拿到全部返回字段。

| 身份 / 条件 | 可以期待的能力 | 主要边界 |
| :--- | :--- | :--- |
| 匿名 | 读公开帖子、标签、画师、wiki、评论、笔记、合集、公开论坛、用户、公开收藏 | 一次最多 2 个查询标签（超出 `422`）、页码上限 1000（超出 `410`）；私密内容与偏好字段看不到 |
| 已登录 + 有效 API key | 在获授权范围内上传、发帖、编辑、评论、收藏、投票、发站内信、保存搜索 | 还看对象归属（别人的站内信、上传、投票看不到）、封禁状态与 key 的权限位；无效凭据是 `401`，权限不足是 `403` |
| builder / approver / moderator / admin | 部分删除、恢复、审核、文件替换、账号管理与后台任务 | 不同动作要求不同角色：批准与队列要 approver，文件替换要 moderator，公告与站点凭据要 admin |
| 站点启用了可选后端 | archive 版本历史、IQDB、推荐服务 | 方法存在不保证每个 Danbooru 系站点都启用：archive 未配置是 `501`，IQDB 未配置返回空数组 |

返回字段只需记住这几条：

- **帖子与媒体**：`file_url` / `large_file_url` / `preview_file_url` 只在帖子对当前用户可见时出现，
  不可见时连 `md5` 也会被省去（媒体资源还会少 `file_key` / `variants`），所以不能按
  `post['file_url']` 一定存在来写代码。
- **用户**：公开资料只给 `id`、`created_at`、`name`、`inviter_id`、`level`、`level_string`、各类计数与
  `is_banned` / `is_deleted`；`favorite_tags`、`blacklisted_tags`、`per_page` 等偏好只在查自己（或
  `user_profile()`）时出现。
- **评论、投票与举报**：非 moderator 看已删除评论时正文、投票分与作者字段会消失，按这些字段检索也受限；
  投票记录只对本人与 moderator 完整可见。
- **站内信与上传**：只有本人（或 moderator）看得到，列表接口返回的是服务端按身份过滤后的结果。

以上是上游权限过滤器的行为概括，逐条规则与出处见
[附注的权限过滤器](danbooru-contract-notes.md#权限与字段级过滤器)。

## 完整原生方法索引

以下是 `api_danbooru.py` 的 **227 个原生方法**，每行写清“给什么 → 拿什么”。签名与可复制调用见
[方法参考](danbooru-api.md)，每个方法的参数键、路由与状态见
[契约审计附注](danbooru-contract-notes.md#逐资源路由参数键与状态227-个原生方法)。

### 状态、API key 与限流

- `status()` — 不给参数 → 服务状态对象：`ip`、`headers`、`instance`、`version`、`server`、`postgres`、`redis`（`postgres['up']` 是数据库是否可用）；匿名。
- `api_keys_list(search=None, **params)` — 给自己的 key 列表，`search` 可筛 `id`、`key`、`user_id` → 数组，每项含 `id`、`user_id`、`name`、`permissions`（不含 `key`）；需登录。
- `api_key_create(**attributes)` — 给 `name`、`permitted_ip_addresses`、`permissions` → 新建的 key 对象，**明文 `key` 只在这个响应里出现**；需登录。
- `api_key_update(api_key_id, **attributes)` — 按 `api_key_id` 改名称/允许 IP/权限 → 更新后的 key 对象（不含 `key`）；需登录。
- `api_key_delete(api_key_id)` — 按 `api_key_id` 删除一把 key → 被删对象（不含 `key`）；需登录。
- `rate_limits_list(search=None, **params)` — 筛 `id`、`action`、`key`、`limited`、`points` → rate_limit 数组；匿名。

### 帖子与修改历史

- `post_list(**params)` — 给顶层 `tags`（`rating:g`、`score:>10`、`order:score`）、`limit`、`page`、`md5` → post 数组（`md5=` 时是单个 post），每项含 `id`、`rating`、`tag_string`、`md5`、`source`；可见时另有 `file_url` 等；匿名。
- `post_show(post_id)` — 给帖子编号（如 `12090564`）→ 该帖的 `id`、`rating`、`tag_string`、`source`、`score`、`parent_id`、`favorite_count` 与图片尺寸字段；匿名。
- `post_random(tags=None)` — 给标签查询串 → 范围内随机一个 post 对象（`id`、`rating`、`tag_string`、`md5`、`source`）；无匹配 `404`；匿名。
- `post_create(upload_media_asset_id, **attributes)` — 给上传媒体编号（顶层）+ `tag_string`、`rating`、`source` 等 → 发布出来的 post 对象；需登录且上传属于你。
- `post_update(post_id, **attributes)` — 给帖子编号 + `tag_string`、`source`、`rating`、`parent_id` 及对应 `old_*` → 写后的 post 对象；`old_*` 用于并发合并；需登录。
- `post_delete(post_id, reason, move_favorites=None)` — 给帖子编号与理由（理由必填）→ 删除后的 post 对象；approver+。
- `post_revert(post_id, version_id)` — 给帖子编号与版本编号 → 回退后的 post 对象；需登录。
- `post_copy_notes(post_id, other_post_id)` — 给来源帖与目标帖编号 → 成功是空正文（本库返回 `None`），失败 `400` + `{success: false, reason}`；需登录。
- `post_mark_as_translated(post_id, check_translation=None, partially_translated=None)` — 给帖子编号与两个布尔 → 更新后的 post 对象，`tag_string` 里能看见对应标签；需登录。
- `post_events_list(search=None, **params)` — 筛 `post_id`、`category`、`event_at`、`creator_id`、`order`（顶层 `post_id` 亦可）→ post_event 数组；匿名。
- `post_versions_list(search=None, **params)` — 筛 `post_id`、`updater_id`、`tags`、`added_tags`、`removed_tags`、`rating`、`version`、`is_new` 等 → post_version 数组（`id`、`post_id`、`updater_id`、`version`、`parent_changed`）；archive 未配置时 `501`。
- `post_version_undo(version_id)` — 给版本编号 → 撤销后的 post_version 对象；需登录。
- `post_favorites_list(post_id, search=None, **params)` — 给帖子编号 → favorite 数组（`id`、`post_id`、`user_id`）；匿名。

### 帖子投票

- `post_votes_list(search=None, **params)` — 筛 `post_id`、`user_id`、`score`、`is_deleted` → post_vote 数组（`id`、`post_id`、`user_id`、`score`）；可见范围受限。
- `post_vote_show(vote_id)` — 给投票编号 → 单个 post_vote 对象，含 `id`、`post_id`、`user_id`、`score`；可见范围受限。
- `post_vote_create(post_id, score)` — 给帖子编号与 `score`（`1` 赞 / `-1` 踩，数字，不是 `'up'`/`'down'`）→ 新建的 post_vote 对象；需登录。
- `post_vote_delete(vote_id)` — 给投票编号撤票（没有按帖子撤票的路由）→ 被更新/删除后的 post_vote 对象；需登录。

### 文件替换与重建

- `post_replacements_list(search=None, **params)` — 筛 `post_id`、`creator_id`、`status`、`order`（顶层 `post_id` 亦可）→ post_replacement 数组（`id`、`post_id`、`creator_id`、`original_url`、`replacement_url`）；匿名。
- `post_replacement_show(replacement_id)` — 给替换记录编号 → 单个 post_replacement 对象，含 `id`、`post_id`、`creator_id`、`original_url`、`replacement_url`、`status`；匿名。
- `post_replacement_create(post_id, replacement_file=None, **attributes)` — 给帖子编号 + `replacement_file`（multipart）或 `replacement_url`/`final_source` → 新建的 post_replacement 对象；需 moderator。
- `post_replacement_update(replacement_id, **attributes)` — 给替换记录编号 + `md5`、`file_ext`、尺寸、`original_url`、`replacement_url` 等 → 写后的 post_replacement 对象；需登录。
- `post_regeneration_create(post_id, category=None)` — 给帖子编号与 `category`（`post` / `large` / `preview`）→ 提交重建的 post 对象；需 moderator。

### 批准、不批准、待删标记与申诉

- `post_approvals_list(search=None, **params)` — 筛 `post_id`、`user_id`、`user_name` → post_approval 数组（`id`、`user_id`、`post_id`）；匿名。
- `post_approval_show(approval_id)` — 给批准记录编号 → 单个 post_approval 对象，含 `id`、`user_id`、`post_id`；匿名。
- `post_approval_create(post_id)` — 给帖子编号（顶层）→ 写后的 post_approval 对象；approver+。
- `post_disapprovals_list(search=None, **params)` — 筛 `post_id`、`user_id`、`reason`、`message_matches` → post_disapproval 数组（`id`、`user_id`、`post_id`、`reason`、`message`）；非 moderator 只看自己的。
- `post_disapproval_show(disapproval_id)` — 给记录编号 → 单个 post_disapproval 对象，含 `id`、`user_id`、`post_id`、`reason`、`message`；可见范围受限。
- `post_disapproval_create(post_id, **attributes)` — 给帖子编号 + `reason`（只接受 `disinterest`/`poor_quality`/`breaks_rules`）+ 可选 `message`（≤140 字符）→ 写后的 post_disapproval 对象；approver+。
- `post_disapproval_update(disapproval_id, **attributes)` — 给记录编号 + `reason`/`message` → 写后的 post_disapproval 对象；需登录。
- `post_flags_list(search=None, **params)` — 筛 `post_id`、`status`（`pending`/`succeeded`/`rejected`）、`category`、`creator_id` → post_flag 数组（`id`、`post_id`、`creator_id`、`reason`、`is_resolved`）；标记人字段受限。
- `post_flag_show(flag_id)` — 给标记编号 → 单个 post_flag 对象，含 `id`、`post_id`、`creator_id`、`reason`、`is_resolved`；身份字段受限。
- `post_flag_create(post_id, reason, **attributes)` — 给帖子编号与理由（必填）→ 写后的 post_flag 对象；需登录，**不等于删除**。
- `post_flag_update(flag_id, reason, **attributes)` — 给标记编号与新理由 → 写后的 post_flag 对象；需登录，本人且 pending。
- `post_appeals_list(search=None, **params)` — 筛 `post_id`、`status`、`creator_id`、`reason_matches` → post_appeal 数组（`id`、`post_id`、`creator_id`、`reason`、`status`）；匿名。
- `post_appeal_show(appeal_id)` — 给申诉编号 → 单个 post_appeal 对象，含 `id`、`post_id`、`creator_id`、`reason`、`status`；可见范围受限。
- `post_appeal_create(post_id, reason, **attributes)` — 给被删帖子编号与理由 → 写后的 post_appeal 对象；需登录。
- `post_appeal_update(appeal_id, reason, **attributes)` — 给申诉编号与新理由 → 写后的 post_appeal 对象；需登录，本人且 pending。

### 媒体资源与 AI 标签

- `media_assets_list(search=None, **params)` — 筛 `md5`、`pixel_hash`、`file_ext`、`file_size`、尺寸、`status`、`is_public`、`ai_tags_match`、`is_posted` → media_asset 数组（`id`、`md5`、`file_ext`、`file_size`、`image_width`、`image_height`）；匿名。
- `media_asset_show(media_asset_id)` — 给媒体资源编号 → 单个 media_asset 对象，含 `id`、`file_ext`、`file_size`、`image_width`、`image_height`、`status`；不可见时省掉 `md5`、`file_key`、`variants`。
- `media_asset_delete(media_asset_id)` — 给媒体资源编号 → 删除后的 media_asset 对象；**实为 admin**（docstring 写 moderator，见附注矛盾项）。
- `media_metadata_list(search=None, **params)` — 筛 `media_asset_id`、`metadata` → media_metadata 数组（`id`、`media_asset_id`、`metadata`）；匿名。
- `ai_tags_list(search=None, **params)` — 筛 `media_asset_id`、`tag_id`、`tag_name`、`post_id`、`score`、`is_posted` → ai_tag 数组（`media_asset_id`、`tag_id`、`score`、`is_posted`）；匿名。
- `ai_tag_tag(media_asset_id, tag_id, tag=None, mode=None)` — 给媒体与 AI 标签编号，`mode='remove'` 表示撤下 → 被更新的 ai_tag 对象，同时改动对应帖子的标签；需登录。

### 上传及上传媒体

- `upload_list(search=None, **params)` — 筛 `status`、`uploader_id`、`source`、`is_posted`（顶层 `user_id` 亦可）→ upload 数组（`id`、`source`、`uploader_id`、`status`、`referer_url`、`media_asset_count`）；非 moderator 只看自己的。
- `upload_show(upload_id)` — 给上传编号 → 单个 upload 对象（`id`、`source`、`uploader_id`、`status`、`referer_url`）并内嵌 `upload_media_assets`；需登录，本人或 moderator。
- `upload_create(files=None, source=None, referer_url=None)` — 给本地文件列表或多文件（`upload[files][<索引>]`）**或** `source` URL → upload 对象 + `upload_media_assets` 关联（取里面的 `id` 去 `post_create`）；需登录，唯一 multipart 上传端点。
- `upload_assets_list(upload_id, search=None, **params)` — 给上传编号 → upload_media_asset 数组（`id`、`media_asset_id`、`status`、`post_id`、`page_url`、`error`）；每页默认 200。
- `upload_media_assets_list(search=None, **params)` — 筛 `upload_id`、`status`、`source_url`、`post_id`、`is_posted` → upload_media_asset 数组；需登录。
- `upload_media_asset_show(upload_media_asset_id)` — 给上传媒体编号 → 单个 upload_media_asset 对象（含 `source_url`、`page_url`，已发布时含 `post_id`）；需登录，本人或 moderator。

### 标签、别名、蕴含与搜索建议

- `tag_list(search=None, **params)` — 筛 `name_matches`、`name_or_alias_matches`、`category`、`post_count`、`hide_empty`、`has_wiki_page`、`order` → tag 数组（`id`、`name`、`post_count`、`category`、`is_deprecated`）；匿名。
- `tag_show(tag_id)` — 给标签编号（`touhou` 是 `29`）→ 单个 tag 对象，含 `id`、`name`、`post_count`、`category`、`is_deprecated`；匿名。
- `tag_update(tag_id, **attributes)` — 给标签编号 + `category`（`0` 通用/`1` 画师/`3` 版权/`4` 角色/`5` 元标签）或 `is_deprecated` → 写后的 tag 对象；需登录，改类别要 Builder+。
- `tag_versions_list(search=None, **params)` — 筛 `tag_id`、`updater_id`、`name_matches`、`version`、`order` → tag_version 数组（`id`、`tag_id`、`updater_id`、`previous_version_id`、`version`）；匿名。
- `tag_version_show(version_id)` — 给版本编号 → 单个 tag_version 对象，含 `id`、`tag_id`、`updater_id`、`previous_version_id`、`version`；匿名。
- `tag_aliases_list(search=None, **params)` — 筛 `antecedent_name`、`consequent_name`、`status`（`active`/`deleted`/`retired`）、`category` → tag_alias 数组（`id`、`antecedent_name`、`consequent_name`、`status`、`forum_topic_id`）；匿名。
- `tag_alias_show(tag_alias_id)` — 给别名记录编号 → 单个 tag_alias 对象，含 `id`、`antecedent_name`、`consequent_name`、`status`、`forum_topic_id`；匿名。
- `tag_alias_delete(tag_alias_id)` — 给别名请求编号 → 被更新/删除后的 tag_alias 对象，`status` 变 `rejected`；语义是**拒绝**，需登录。
- `tag_implications_list(search=None, **params)` — 筛 `antecedent_name`、`consequent_name`、`status`、`implied_from`、`implied_to` → tag_implication 数组（`id`、`antecedent_name`、`consequent_name`、`forum_topic_id`）；匿名。
- `tag_implication_show(tag_implication_id)` — 给蕴含记录编号 → 单个 tag_implication 对象，含 `id`、`antecedent_name`、`consequent_name`、`status`、`forum_topic_id`；匿名。
- `tag_implication_delete(tag_implication_id)` — 给蕴含请求编号 → 被更新/删除后的 tag_implication 对象；拒绝语义，需登录。
- `related_tag(search=None, **params)` — 给 `search={'query': 'touhou'}`（必填）与 `order`（`frequency`/`cosine`/`jaccard`/`overlap`）、顶层 `limit` → 一个对象：`query`、`post_count`、`tag`、`related_tags`（每项含 `tag`）、`wiki_page_tags`；匿名。
- `autocomplete_list(query, type=None, limit=None)` — 给查询文本与 `type`（`tag`/`tag_query`/`artist`/`wiki_page`/`user`/`pool`/`comment`/`saved_search`）→ 建议数组，元素形状随 `type` 不同，默认 10 条；匿名。

### 画师与主页记录

- `artist_list(search=None, **params)` — 筛 `name`、`any_name_matches`、`url_matches`、`group_name`、`is_banned`、`has_tag`、`order`（顶层 `name` 亦可）→ artist 数组（`id`、`name`、`is_banned`、`group_name`、`other_names`）；匿名。
- `artist_show(artist_id)` — 给画师编号（`fuzichoco` 是 `8704`）→ 单个 artist 对象，含 `id`、`name`、`is_banned`、`group_name`、`other_names`；匿名。
- `artist_show_or_new(name=None)` — 给画师名 → 名字已存在时重定向后仍是该 artist 对象，否则返回未保存的 artist 对象；匿名。
- `artist_create(name, **attributes)` — 给主名称 + `other_names_string`、`group_name`、`url_string` → 写后的 artist 对象；需登录。
- `artist_update(artist_id, **attributes)` — 给画师编号 + 同上属性 → 写后的 artist 对象；需登录。
- `artist_delete(artist_id)` — 给画师编号 → 软删除（置 `is_deleted`）；服务端重定向，最终响应非 JSON 会抛 `AnybooruAPIError`；需 builder。
- `artist_revert(artist_id, version_id)` — 给画师编号与版本编号 → 写后的 artist 对象；需登录。
- `artist_ban(artist_id)` — 给画师编号 → 封禁；重定向到画师页，最终响应决定结果；需 admin。
- `artist_unban(artist_id)` — 给画师编号 → 解封；重定向同上；需 admin。
- `artist_urls_list(search=None, **params)` — 筛 `artist_id`、`url`、`url_matches`、`is_active` → artist_url 数组（`id`、`artist_id`、`url`、`is_active`）；匿名。
- `artist_versions_list(search=None, **params)` — 筛 `artist_id`、`updater_id`、`name`、`is_banned` → artist_version 数组（`id`、`artist_id`、`name`、`updater_id`、`group_name`）；匿名。
- `artist_version_show(version_id)` — 给版本编号 → 单个 artist_version 对象，含 `id`、`artist_id`、`name`、`updater_id`、`group_name`；匿名。
- `artist_commentaries_list(search=None, **params)` — 筛 `post_id`、`original_present`、`translated_present`、`text_matches` → artist_commentary 数组（`id`、`post_id`、`original_title`、`original_description`、`translated_title`）；匿名。
- `artist_commentary_show(post_id)` — 给帖子编号 → 该帖的 artist_commentary 对象，含 `id`、`post_id`、`original_title`、`original_description`、`translated_title`（没有说明时 `404`）；匿名。
- `artist_commentary_create_or_update(post_id, **attributes)` — 给帖子编号 + `original_title`/`original_description`/`translated_title`/`translated_description`/`commentary_tags`（PUT）→ 该帖说明对象；需登录。
- `artist_commentary_revert(post_id, version_id)` — 给帖子编号（路径里的 id 是 post_id）与版本编号 → 写后的说明对象；需登录。
- `artist_commentary_versions_list(search=None, **params)` — 筛 `post_id`、`updater_id`、`text_matches` → artist_commentary_version 数组（`id`、`post_id`、`updater_id`、`original_title`）；匿名。
- `artist_commentary_version_show(version_id)` — 给说明版本编号 → 单个 artist_commentary_version 对象，含 `id`、`post_id`、`updater_id`、`original_title`、`original_description`；匿名。

### 评论与评论投票

- `comment_list(search=None, **params)` — 筛 `post_id`、`body_matches`、`creator_id`、`score`、`is_deleted`（顶层 `group_by` 取 `comment`/`post`）→ comment 数组（`id`、`post_id`、`creator_id`、`body`、`score`）；匿名。
- `comment_show(comment_id)` — 给评论编号 → 单个 comment 对象，含 `id`、`post_id`、`creator_id`、`body`、`score`；已删除且不可见时省掉 `body`、`score`、`creator_id`。
- `comment_create(post_id, body, **attributes)` — 给帖子编号与正文（DText）+ 可选 `do_not_bump_post`、`is_sticky` → 写后的 comment 对象；需登录。
- `comment_update(comment_id, **attributes)` — 给评论编号 + `body`/`is_deleted`/`is_sticky` → 写后的 comment 对象；需登录，作者或 moderator。
- `comment_delete(comment_id)` — 给评论编号 → 软删除后的 comment 对象；需登录，作者或 moderator。
- `comment_undelete(comment_id)` — 给评论编号 → 恢复后的 comment 对象；需 moderator。
- `comment_votes_list(search=None, **params)` — 筛 `comment_id`、`user_id`、`score`（顶层 `comment_id` 亦可）→ comment_vote 数组（`id`、`comment_id`、`user_id`、`score`）；受限。
- `comment_vote_show(vote_id)` — 给投票编号 → 单个 comment_vote 对象，含 `id`、`comment_id`、`user_id`、`score`；可见范围受限。
- `comment_vote_create(comment_id, score)` — 给评论编号与 `score`（`1` / `-1`，数字）→ 新建的 comment_vote 对象；需登录。
- `comment_vote_delete(vote_id)` — 给投票编号撤票（没有按评论撤票的路由）→ 被更新/删除后的 comment_vote 对象；需登录。

### 图上笔记及笔记历史

- `note_list(search=None, **params)` — 筛 `post_id`、`is_active`、`x`、`y`、`width`、`height`、`body_matches`（**没有** `creator_id`/`creator_name`）→ note 数组（`id`、`post_id`、`x`、`y`、`width`、`height`、`body`、`is_active`）；匿名。
- `note_show(note_id)` — 给笔记编号 → 单个 note 对象，含 `id`、`post_id`、`x`、`y`、`width`、`height`、`body`、`is_active`；匿名。
- `note_create(post_id, x, y, width, height, body, **attributes)` — 给帖子编号、左上角 `x`/`y`、`width`/`height` 与 DText 正文 → 写后的 note 对象；失败 `422`；需登录。
- `note_update(note_id, **attributes)` — 给笔记编号 + `x`/`y`/`width`/`height`/`body` → 写后的 note 对象；需登录。
- `note_delete(note_id)` — 给笔记编号 → 停用后的 note 对象（`id`、`post_id`、`is_active=false`）；需登录。
- `note_revert(note_id, version_id)` — 给笔记编号与版本编号 → 写后的 note 对象；需登录。
- `note_preview(body)` — 给笔记 HTML → 返回清理后的 `sanitized_body`；匿名可预览，不保存笔记。
- `note_versions_list(search=None, **params)` — 筛 `note_id`、`post_id`、`updater_id`、`version` → note_version 数组（`id`、`note_id`、`post_id`、`updater_id`、`x`）；匿名。
- `note_version_show(version_id)` — 给版本编号 → 单个 note_version 对象，含 `id`、`note_id`、`post_id`、`updater_id`、`x`、`y`、`width`、`height`；匿名。

### 合集及合集历史

- `pool_list(search=None, **params)` — 筛 `name_matches`、`category`（`series`/`collection`）、`post_ids`、`post_tags_match`、`order` → pool 数组（`id`、`name`、`description`、`category`、`is_active`、`post_ids`）；匿名。
- `pool_show(pool_id)` — 给合集编号 → 单个 pool 对象，含 `id`、`name`、`description`、`category`、`is_active`，`post_ids` 是整数数组；匿名。
- `pool_create(name, **attributes)` — 给名字 + `description`、`category`、`post_ids`/`post_ids_string` → 写后的 pool 对象；需登录。
- `pool_update(pool_id, **attributes)` — 给合集编号 + 说明或成员；`post_ids=[]` 会真的发空数组（清空内容）→ 写后的 pool 对象；需登录。
- `pool_delete(pool_id)` — 给合集编号 → 软删除后的 pool 对象（`is_deleted` 为 `true`）；需 builder。
- `pool_undelete(pool_id)` — 给合集编号 → 恢复后的 pool 对象；需 moderator。
- `pool_revert(pool_id, version_id)` — 给合集编号与版本编号 → 写后的 pool 对象；需登录。
- `pool_gallery(search=None, **params)` — 给搜索条件（服务端默认 `category=series`）→ pool 数组，每项带一张预览帖；匿名。
- `pool_element_create(post_id, pool_id=None, pool_name=None)` — 给帖子编号与目标合集（编号或名字）→ 加入后所属的 pool 对象；需登录且有该合集更新权限。
- `pool_versions_list(search=None, **params)` — 筛 `pool_id`、`updater_id`、`version`、`category` → pool_version 数组（`id`、`pool_id`、`updater_id`、`version`、`name`）；archive 未配置时 `501`。
- `pool_version_diff(pool_version_id, other_id=None, type=None)` — 给版本编号，`type` 取 `previous`/`next` 指定对照版 → 两个 pool_version 的差异对象；匿名。

### wiki 及 wiki 历史

- `wiki_page_list(search=None, **params)` — 筛 `title`、`body_matches`、`other_names_match`、`is_locked`、`linked_to`、`order`（顶层 `title=` 会 `302`，别用）→ wiki_page 数组（`id`、`title`、`body`、`is_locked`、`other_names`）；匿名。
- `wiki_page_show(id_or_title)` — 给页面编号或标题（如 `'help:api'`，内部转义）→ 单个 wiki_page 对象，含 `title`、`body`、`other_names`、`is_locked`、`is_deleted`；标题不存在时 `404`；匿名。
- `wiki_page_create(title, **attributes)` — 给标题 + `body`、`other_names_string`、`is_deleted`、`is_locked` → 写后的 wiki_page 对象；需登录，`is_locked` 要 Builder。
- `wiki_page_update(wiki_page_id, **attributes)` — 给编号或标题 + 正文、其他名、`is_deleted` → 写后的 wiki_page 对象；需登录。
- `wiki_page_delete(wiki_page_id)` — 给编号或标题 → 软删除后的 wiki_page 对象；需 builder。
- `wiki_page_revert(wiki_page_id, version_id)` — 给编号或标题与版本编号 → 写后的 wiki_page 对象；需登录。
- `wiki_page_show_or_new(title=None)` — 给标题 → 已存在时重定向后是该 wiki_page 对象（含 `title`、`body`、`other_names`），否则是未保存的 wiki_page 对象；匿名。
- `wiki_page_versions_list(search=None, **params)` — 筛 `wiki_page_id`、`updater_id`、`title`、`body_matches` → wiki_page_version 数组（`id`、`wiki_page_id`、`updater_id`、`title`、`body`）；匿名。
- `wiki_page_version_show(version_id)` — 给版本编号 → 单个 wiki_page_version 对象，含 `id`、`wiki_page_id`、`updater_id`、`title`、`body`；匿名。
- `wiki_page_versions_diff(thispage=None, otherpage=None, type=None)` — 给两个版本编号（或一个 + `type`）→ 两个 wiki_page_version 的差异对象；匿名。

### 用户、用户记录与改名

- `user_list(search=None, **params)` — 筛 `name_matches`、`level`、`min_level`、`is_banned`、`has_posts`、`order`（顶层 `name` 亦可）→ user 数组，匿名只有 `id`、`name`、`level`、各类计数与封禁/删除标记；匿名。
- `user_show(user_id)` — 给用户编号 → 单个 user 对象，匿名时含 `id`、`created_at`、`name`、`inviter_id`、`level`、`level_string`、各类计数与 `is_banned`/`is_deleted`，本人视角多出偏好设置；匿名。
- `user_create(name, password, password_confirmation)` — 给用户名与两次密码 → 写后的 user 对象；站点验证码/邀请检查可能让请求失败。
- `user_update(user_id, **attributes)` — 给自己的编号 + `per_page`、`blacklisted_tags`、`favorite_tags`、`time_zone` 等 → 写后的 user 对象；需登录，只能改自己。
- `user_profile()` — 不给参数 → 当前登录的 user 对象（含偏好设置、`favorite_count`）；需登录。
- `user_actions_list(search=None, **params)` — 筛 `user_id`、`event_type`、`model_type`/`model_id`、`order`（顶层 `user_id` 亦可）→ user_action 数组；需 moderator。
- `user_action_show(user_action_id)` — 给记录编号 → 单个 user_action 对象（含记录类型与编号、时间、发起人等字段，随事件类型而变）；需 moderator。
- `user_events_list(search=None, **params)` — 筛 `user_id`、`category`、`ip_addr`（顶层 `user_id` 亦可）→ user_event 数组（`id`、`user_id`、`category`、`ip_addr`）；非 moderator 看不到 `session_id`/`user_agent`。
- `user_feedbacks_list(search=None, **params)` — 筛 `user_id`、`creator_id`、`category`、`is_deleted` → user_feedback 数组；受限。
- `user_feedback_show(feedback_id)` — 给评价编号 → 单个 user_feedback 对象，含 `id`、`user_id`、`creator_id`、`category`、`body`、`is_deleted`；可见范围受限。
- `user_feedback_create(**attributes)` — 给 `body`、`category`（`positive`/`negative`）与评价对象 → 写后的 user_feedback 对象；需登录。
- `user_feedback_update(feedback_id, **attributes)` — 给评价编号 + `body`/`category`/`is_deleted` → 写后的 user_feedback 对象；需登录。
- `user_name_change_requests_list(search=None, **params)` — 筛 `user_id`、`original_name`、`desired_name` → user_name_change_request 数组（`id`、`user_id`、`original_name`、`desired_name`）；非匿名。
- `user_name_change_request_show(request_id)` — 给请求编号 → 单个 user_name_change_request 对象，含 `id`、`user_id`、`original_name`、`desired_name`；非匿名。
- `user_name_change_request_create(**attributes)` — 给 `user_id` 与 `desired_name` → 写后的改名请求对象；需登录。

### 收藏与收藏组

- `favorite_list(search=None, **params)` — 筛 `post_id`、`user_id`（顶层 `post_id`/`user_id` 亦可）→ favorite 数组（`id`、`user_id`、`post_id`）；看别人的收藏需登录，私密收藏只有本人可见。
- `favorite_create(post_id)` — 给帖子编号（顶层）→ 被收藏的 post 对象（`id`、`rating`、`tag_string`、`favorite_count`）；需登录。
- `favorite_delete(post_id)` — 给帖子编号（路径里的 id 就是 post_id）→ 取消收藏后的 post 对象；需登录。
- `favorite_groups_list(search=None, **params)` — 筛 `name_contains`、`is_public`、`post_ids`、`creator_id`（顶层 `user_id` 亦可）→ favorite_group 数组（`id`、`name`、`creator_id`、`post_ids`、`is_public`）；受限。
- `favorite_group_show(group_id)` — 给组编号 → 单个 favorite_group 对象，含 `id`、`name`、`creator_id`、`post_ids`、`is_public`；可见范围受限。
- `favorite_group_create(name, **attributes)` — 给组名 + `post_ids`/`post_ids_string`、`is_public`、`is_private` → 写后的 favorite_group 对象；需登录。
- `favorite_group_update(group_id, **attributes)` — 给组编号 + 设置或成员 → 写后的 favorite_group 对象；需登录。
- `favorite_group_delete(group_id)` — 给组编号 → 被删除后的 favorite_group 对象；需登录。
- `favorite_group_add_post(group_id, post_id)` — 给组编号与帖子编号（都是顶层）→ 更新后的 favorite_group 对象，`post_ids` 里能看到它；需登录。
- `favorite_group_remove_post(group_id, post_id)` — 给组编号与帖子编号 → 更新后的 favorite_group 对象；需登录。

### 论坛主题、帖子与投票

- `forum_topics_list(search=None, **params)` — 筛 `title_matches`、`category_id`（只有 `0` General/`1` Tags/`2` Bugs &amp; Features）、`min_level`、`is_sticky`、`is_locked`、`order` → forum_topic 数组（`id`、`creator_id`、`updater_id`、`title`、`response_count`）；匿名，按 `min_level` 过滤。
- `forum_topic_show(topic_id)` — 给主题编号 → 单个 forum_topic 对象，含 `id`、`creator_id`、`updater_id`、`title`、`response_count`，内嵌 `forum_posts`；匿名。
- `forum_topic_create(title, body, **attributes)` — 给标题与首帖正文 + `category_id`、`min_level` → 写后的 forum_topic 对象；需登录。
- `forum_topic_update(topic_id, **attributes)` — 给主题编号 + `title`、`category_id`、`is_sticky`、`is_locked`、`min_level` → 写后的 forum_topic 对象；需登录，置顶/锁定/门槛要 moderator。
- `forum_topic_delete(topic_id)` — 给主题编号 → 软删除后的 forum_topic 对象；需 moderator。
- `forum_topic_undelete(topic_id)` — 给主题编号 → 恢复后的 forum_topic 对象；需 moderator。
- `forum_topics_mark_all_as_read()` — 不给参数 → 全部标为已读；服务端重定向，最终响应决定结果；需登录。
- `forum_posts_list(search=None, **params)` — 筛 `topic_id`、`body_matches`、`creator_id`、`linked_to` 与嵌套 `{'topic': {...}}` → forum_post 数组（`id`、`topic_id`、`creator_id`、`updater_id`、`body`）；匿名。
- `forum_post_show(post_id)` — 给帖子编号 → 单个 forum_post 对象，含 `id`、`topic_id`、`creator_id`、`updater_id`、`body`；已删除的返回 `404`。
- `forum_post_create(topic_id, body)` — 给主题编号与正文 → 写后的 forum_post 对象；需登录。
- `forum_post_update(post_id, body)` — 给帖子编号与新正文 → 写后的 forum_post 对象；需登录，作者或 moderator。
- `forum_post_delete(post_id)` — 给帖子编号 → 被删除后的 forum_post 对象；需 moderator。
- `forum_post_undelete(post_id)` — 给帖子编号 → 恢复后的 forum_post 对象；需 moderator。
- `forum_post_votes_list(search=None, **params)` — 筛 `forum_post_id`、`creator_id`、`score` → forum_post_vote 数组（`id`、`forum_post_id`、`creator_id`、`score`）；匿名。
- `forum_post_vote_show(vote_id)` — 给投票编号 → 单个 forum_post_vote 对象，含 `id`、`forum_post_id`、`creator_id`、`score`；可见范围受限。
- `forum_post_vote_create(forum_post_id, score)` — 给论坛帖子编号（顶层）与 `score`（`1`/`-1`/`0`，数字）→ 新建的 forum_post_vote 对象；需登录。
- `forum_post_vote_delete(vote_id)` — 给投票编号 → 被撤回后的 forum_post_vote 对象；需登录，本人。
- `forum_topic_visits_list(search=None, **params)` — 筛 `user_id`、`forum_topic_id`、`last_read_at` → forum_topic_visit 数组（`id`、`user_id`、`forum_topic_id`、`last_read_at`）；需登录，本人。

### 站内信

- `dmail_list(search=None, **params)` — 筛 `folder`（`received`/`sent`/`all`）、`is_read`、`is_deleted`、`from_id`、`to_id`、`message_matches` → dmail 数组（`id`、`owner_id`、`from_id`、`to_id`、`title`、`is_read`）；需登录，只能看自己的。
- `dmail_show(dmail_id)` — 给站内信编号 → 单个 dmail 对象，含 `id`、`owner_id`、`from_id`、`to_id`、`title`、`is_read`（可能带签名的 `key`）；需登录，本人。
- `dmail_create(title, body, to_name=None, to_id=None)` — 给标题、正文与收件人 → 写后的 dmail 对象；需登录。
- `dmail_update(dmail_id, **attributes)` — 给编号 + `is_read`/`is_deleted`（**删除邮件也走这里**）→ 写后的 dmail 对象；需登录，本人。
- `dmails_mark_all_as_read()` — 不给参数 → 被标为已读的站内信集合；需登录。

### 用户封禁与批量标签变更

- `ban_list(search=None, **params)` — 筛 `user_id`、`banner_id`、`reason_matches`、`expired`、`order` → ban 数组（`id`、`user_id`、`reason`、`banner_id`、`duration`）；匿名。
- `ban_show(ban_id)` — 给封禁记录编号 → 单个 ban 对象，含 `id`、`user_id`、`reason`、`banner_id`、`duration`；匿名。
- `ban_create(**attributes)` — 给封禁对象（`user_id`/`user_name`）+ `reason`、`duration`（必填，合法值 `1 day`/`3 days`/`7 days`/`1 month`/`3 months`/`6 months`/`1 year`/`100 years`，最后一个是永久）、若干 `delete_*` 布尔（只清最近 3 天数据）→ 写后的 ban 对象；需 moderator。
- `ban_update(ban_id, **attributes)` — 给编号 + `reason`/`duration` → 写后的 ban 对象；需 moderator。
- `ban_delete(ban_id)` — 给编号 → 解除封禁后的 ban 对象；需 moderator。
- `bulk_update_requests_list(search=None, **params)` — 筛 `status`（`pending`/`approved`/`rejected` 或逗号列表）、`script_matches`、`user_id`、`score`、`order` → bulk_update_request 数组（`id`、`user_id`、`forum_topic_id`、`script`、`status`）；匿名。
- `bulk_update_request_show(request_id)` — 给请求编号 → 单个 bulk_update_request 对象，含 `id`、`user_id`、`forum_topic_id`、`script`、`status`；匿名。
- `bulk_update_request_create(script, **attributes)` — 给脚本（`alias foo -> bar`、`imply a -> b`）+ 可选 `title`、`reason`、`forum_topic_id` → 写后的请求对象；**申请别名/蕴含的正规入口**，需登录。
- `bulk_update_request_update(request_id, **attributes)` — 给请求编号 + `script`/`forum_topic_id` → 写后的请求对象；需登录，本人。
- `bulk_update_request_approve(request_id)` — 给请求编号 → 写后的请求对象（`status` 变 `approved`）；需 approver。
- `bulk_update_request_delete(request_id)` — 给请求编号 → 被更新/删除后的请求对象（`status` 变 `rejected`）；语义是**拒绝**，需登录。

### IP、审核日志与举报处理

- `ip_bans_list(search=None, **params)` — 筛 `ip_addr`、`category`（`warning`/`block`）、`is_deleted`、`hit_count`、`creator_id` → ip_ban 数组（`id`、`creator_id`、`ip_addr`、`reason`、`category`）；需 moderator+（docstring 未写前提，见附注）。
- `ip_ban_show(ip_ban_id)` — 给编号 → 单个 ip_ban 对象，含 `id`、`creator_id`、`ip_addr`、`reason`、`category`；需 moderator+。
- `ip_ban_create(**attributes)` — 给 `ip_addr`、`reason`、`category`、`is_deleted` → 写后的 ip_ban 对象；需 moderator+。
- `ip_ban_update(ip_ban_id, **attributes)` — 给编号 + 同上属性 → 写后的 ip_ban 对象；需 moderator+。
- `ip_address_show(ip_addr)` — 给 IP 字符串（**路径里的 id 就是 IP**）→ 该 IP 的查询结果对象（位置、ASN 等）；需 moderator+。
- `ip_geolocations_list(search=None, **params)` — 筛 `ip_addr`、`network`、`country`、`city`、`asn`、`is_proxy` → ip_geolocation 数组（`id`、`ip_addr`、`network`、`asn`、`is_proxy`）；需 moderator。
- `mod_actions_list(search=None, **params)` — 筛 `category`、`description_matches`、`creator_id`、`subject_type`、`subject_id`、`order` → mod_action 数组（`id`、`creator_id`、`description`、`category`、`subject_type`）；匿名，敏感类目对非 moderator 过滤。
- `mod_action_show(mod_action_id)` — 给编号 → 单个 mod_action 对象，含 `id`、`creator_id`、`description`、`category`、`subject_type`；需 janitor。
- `modqueue_list(search=None, **params)` — 给 `search[order]`（默认 `modqueue`）、`mode`（默认 `gallery`）、`limit`（钳 200）→ **post 数组**（不是队列记录）；需 approver。
- `moderation_reports_list(search=None, **params)` — 筛 `model_type`、`model_id`、`status`、`creator_id`、`recipient_id` → moderation_report 数组（`id`、`model_type`、`model_id`、`creator_id`、`reason`、`status`）；非 moderator 只看自己的。
- `moderation_report_show(report_id)` — 给举报编号 → 单个 moderation_report 对象，含 `id`、`model_type`、`model_id`、`creator_id`、`reason`、`status`；非 moderator 只看自己的。
- `moderation_report_create(**attributes)` — 给 `model_type`（只接受 `Comment`/`ForumPost`/`Dmail`）、`model_id`、`reason` → 写后的 moderation_report 对象，`status` 初始 `pending`；需登录。
- `moderation_report_update(report_id, **attributes)` — 给举报编号 + `status` → 写后的 moderation_report 对象；需 moderator。

### 站点公告与保存的搜索

- `news_updates_list(search=None, **params)` — 筛 `message_matches`、`creator_id`、`is_deleted`、`order` → news_update 数组（`id`、`message`、`creator_id`、`updater_id`、`duration`）；需 admin。
- `news_update_show(news_update_id)` — 给公告编号 → 单个 news_update 对象，含 `id`、`message`、`creator_id`、`updater_id`、`duration`；需 admin。
- `news_update_create(message, **attributes)` — 给公告文本 + `duration`/`duration_in_days`、`is_deleted` → 写后的 news_update 对象；需 admin。
- `news_update_update(news_update_id, **attributes)` — 给编号 + `message` 等 → 写后的 news_update 对象；需 admin。
- `news_update_delete(news_update_id)` — 给编号 → 软删除后的 news_update 对象；需 admin。
- `saved_searches_list(search=None, **params)` — 筛 `query_matches`、`label`、`order` → saved_search 数组（`id`、`user_id`、`query`、`labels`）；需登录。
- `saved_search_create(**attributes)` — 给 `query` + `label_string`、`disable_labels` → 写后的 saved_search 对象；需登录。
- `saved_search_update(saved_search_id, **attributes)` — 给编号 + 同上属性 → 写后的 saved_search 对象；需登录，本人。
- `saved_search_delete(saved_search_id)` — 给编号 → 被删除后的 saved_search 对象；需登录，本人。

### 站点凭据与反应

- `site_credentials_list(search=None, **params)` — 筛 `site`（如 `pixiv`）、`is_enabled`、`is_public`、`status`、`creator_id` → site_credential 数组（`id`、`site`、`creator_id`、`is_enabled`、`is_public`）；需 admin。
- `site_credential_show(site_credential_id)` — 给编号 → 单个 site_credential 对象，含 `id`、`site`、`creator_id`、`is_enabled`、`is_public`；公开项需 admin，私有项需本人。
- `site_credential_create(site, **attributes)` — 给 `site` 与 `credential`（键随站点而定）、`is_enabled` → 写后的 site_credential 对象；需 admin。
- `site_credential_update(site_credential_id, **attributes)` — 给编号 + `is_enabled` → 写后的 site_credential 对象；需 admin 或本人。
- `site_credential_delete(site_credential_id)` — 给编号 → 被删除后的 site_credential 对象；公开项需 owner，私有项需本人。
- `reactions_list(search=None, **params)` — 筛 `model_type`、`model_id`、`creator_id`、`reaction_id` → reaction 数组（`id`、`creator_id`、`reaction_id`、`model_type`、`model_id`）；受限。
- `reaction_show(reaction_id)` — 给反应编号 → 单个 reaction 对象，含 `id`、`creator_id`、`reaction_id`、`model_type`、`model_id`；可见范围受限。
- `reaction_create(**attributes)` — 给 `model_type`（`Post`/`Comment`/`ForumPost`/`User`/`Tag`/`Pool`）、`model_id`、`reaction_id`（站点 `reactions` 配置里的名字，包内默认配置为空）→ 写后的 reaction 对象；需登录。
- `reaction_delete(reaction_id)` — 给反应编号 → 被撤回后的 reaction 对象；需登录。

### 报表、后台任务、来源与推荐

- `report_show(report, search=None, **params)` — 给报表名（`posts`、`post_votes`、`comments`、`users` 等 21 个模型之一）+ `columns`、`group`、`period` 等 → 报表对象，列与分组由参数决定；匿名。
- `jobs_list(search=None, **params)` — 筛 `job_class`、`queue_name`、`status`、`active_job_id`、`name` → background_job 数组（`id`、`job_class`、`queue_name`、`status`、`runtime_latency`、`queue_latency`）；非 admin 看不到 `serialized_params`。
- `job_cancel(job_id)` — 给 ActiveJob id（`active_job_id`）→ 写后的 background_job 对象；需 janitor。
- `job_retry(job_id)` — 给 ActiveJob id → 写后的 background_job 对象；需 janitor。
- `job_run(job_id)` — 给 ActiveJob id → 写后的 background_job 对象；需 janitor。
- `job_delete(job_id)` — 给 ActiveJob id → 被删除后的 background_job 对象；需 janitor。
- `dtext_links_list(search=None, **params)` — 筛 `link_type`、`link_target`、`model_type`、`model_id`、`linked_wiki_id`、`linked_tag_id` → dtext_link 数组（`id`、`model_type`、`model_id`、`link_type`、`link_target`）；匿名。
- `recommended_posts_list(search=None, **params)` — 给 `search={'post_id': 12090564}` 或 `{'user_id': ...}`；`limit` 上限 200 → post 数组（`id`、`up_score`、`down_score`、`score`、`source`）；依赖站点推荐服务。
- `counts_posts(tags=None, estimate_count=None, skip_cache=None)` — 给标签查询串与两个布尔 → `{"counts": {"posts": <int>}}`；默认估算 + 缓存；匿名。
- `source_show(url, ref=None, mode=None)` — 给页面地址 → 站点解析出的来源数据对象（画师／作品信息）；`mode` 取 `card`/`post`；匿名。
- `iqdb_query(**params)` — 给图片地址、`hash`、`post_id` 或 `media_asset_id` → 匹配数组，每项含 `score`、`post`；IQDB 未配置时返回空数组。

## 边界与未实测

- 已实测的只有 10 个匿名只读方法的早期批次（`post_list`、`post_show`、`tag_list`、`artist_list`、
  `artist_show_or_new`、`related_tag`、`wiki_page_list`、`wiki_page_show`、`comment_list`、`pool_list`）
  与三条错误路径（`404` / `410` / `422`）；逐请求记录见 [verification.md](verification.md)。
- 其余 217 个方法只有源码依据：全部写操作、上传媒体链路、高权限动作与可选服务（archive / IQDB /
  推荐）的成功路径都未执行；本仓库不带凭据。
- 同族站点另有独立只读探测（Safebooru 匿名可用且是 Danbooru）；不能把早期覆盖清单当作全量当前状态。
- 本次文档重排没有新增网络请求。

`request()` 还能调到发现内容、指标、部分账号管理等没有原生方法的 JSON 路由，已有路由与非 JSON 排除项见
[契约审计附注](danbooru-contract-notes.md)；它不是图片下载方法，也不会把 HTML 页面变成 JSON。客户端另有
`close()` 与 `with Danbooru(...) as client`，这两个是客户端操作，不计入上面的方法数。

继续阅读：[客户端用法](danbooru.md) · [完整方法与参数](danbooru-api.md) · [翻页方式](pagination.md) · [错误与权限失败](errors.md)

