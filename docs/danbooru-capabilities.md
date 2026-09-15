# Danbooru 能力入口：我想做什么，该用哪个接口？

**不知道从哪个方法查起，先看这页；已经知道端点，再看 [方法参考](danbooru-api.md)。**

- **不登录也能开始**：找图、查帖子、标签、画师、wiki、公开评论、笔记、合集、用户和公开收藏。
- **登录后才能改内容**：上传、发帖、评论、收藏、投票、编辑等；删除、审核、管理还可能要求更高等级。
- **库负责调用 JSON API**，不是下载器或自动采集器：不自动保存图片、不自动翻页，也不保证每条记录都向匿名用户开放文件地址。

## 先按目的找入口

下表的 `client` 是已按配置创建的 `Danbooru` 客户端；`query`、`url`、各类 ID 等代表你从配置或前一次响应
取得的值，不是库的默认参数。初始化方式见 [客户端用法](danbooru.md)。

| 我想做什么 | 能力与方法 | 最简调用形态 | 是否需要登录 |
| :--- | :--- | :--- | :--- |
| 按标签、评分、时间找图 | `post_list`：组合标签和 `score:`、`date:`、`order:` 等元标签查询 | `client.post_list(tags=query)` | 匿名可查，搜索配额与内容可见性受限 |
| 看一张图的详情，或随机找图 | `post_show` / `post_random` | `client.post_show(post_id)`；`client.post_random(tags=query)` | 匿名可查 |
| 取得原图或预览图地址 | `post_show`：拿**当前身份允许访问**的文件信息；保存文件要另用 HTTP 客户端 | `post = client.post_show(post_id)` | 地址取决于帖子对当前用户是否可见，匿名不保证拿到 |
| 按作者找作品 | `post_list`：已知画师标签时直接当标签搜索 | `client.post_list(tags=artist_name)` | 匿名可查 |
| 查画师与主页 URL | `artist_list` / `artist_urls_list` / `artist_show` | `client.artist_list(search={'url_matches': url})` | 匿名可查 |
| 找标签、同义名与相关标签 | `tag_list` / `tag_aliases_list` / `related_tag` | `client.tag_list(search={'name_matches': name})` | 匿名可查 |
| 输入关键词时给出补全建议 | `autocomplete_list` | `client.autocomplete_list(query, type=search_type)` | 匿名可查 |
| 查 wiki 或原作者说明 | `wiki_page_list` / `wiki_page_show` / `artist_commentary_show` | `client.wiki_page_show(title)` | 匿名可查可见内容 |
| 看评论和图上笔记 | `comment_list` / `note_list` | `client.comment_list(search={'post_id': post_id})` | 匿名可读；发表与修改需登录 |
| 按合集看系列作品 | `pool_list` / `pool_show` / `pool_gallery` | `client.pool_show(pool_id)` | 匿名可读；创建、修改需登录 |
| 查用户，查看或整理收藏、保存搜索 | `user_show` / `favorite_list` / `favorite_create` / `favorite_group_create` / `saved_search_create` | `client.favorite_create(post_id)` | 公开资料与公开收藏可匿名；自己的收藏操作需登录 |
| 上传文件并发帖 | `upload_create` → `post_create` | `client.post_create(media_asset_id, tag_string=tags, rating=rating)` | 需登录，且受上传归属与账号权限限制 |
| 修改标签、来源、翻译状态 | `post_update` / `post_mark_as_translated` | `client.post_update(post_id, tag_string=tags, old_tag_string=before)` | 需登录，且有该帖的编辑权限 |
| 投票、请求删除或提出申诉 | `post_vote_create` / `post_flag_create` / `post_appeal_create` | `client.post_vote_create(post_id, score=1)` | 需登录；不等同于审核员直接删除 |
| 举报行为或处理审核队列 | `moderation_report_create` / `modqueue_list` / `post_approval_create` | `client.modqueue_list()` | 举报需登录且对象可举报；审核需 approver 等权限 |
| 查论坛或发送站内信 | `forum_topics_list` / `forum_posts_list` / `dmail_create` | `client.dmail_create(title, body, to_name=name)` | 公开论坛可匿名读；发帖和站内信需登录 |
| 查修改历史、统计或来源 | `post_versions_list` / `counts_posts` / `source_show` | `client.counts_posts(tags=query)`；`client.source_show(url)` | 多数可匿名读；版本历史依赖站点 archive 服务 |
| 以图搜图或看推荐 | `iqdb_query` / `recommended_posts_list` | `client.iqdb_query(url=url)` | 源码提供匿名入口，但依赖站点配置的服务 |

**两个容易选错的地方**：帖子列表把过滤写在顶层 `tags`，其他大多数列表放在 `search` 字典；上传成功不等于
已发帖，还要用上传媒体 id 调 `post_create`。翻页看 [pagination.md](pagination.md)，请求失败看
[errors.md](errors.md)。

## 匿名和登录，能力差在哪里？

“可匿名”只表示源码允许进入该读接口，不保证一定有结果、能看到所有记录，或拿到全部返回字段。

| 身份 / 条件 | 可以期待的能力 | 主要边界 |
| :--- | :--- | :--- |
| 匿名 | 读公开帖子、标签、画师、wiki、评论、笔记、合集、论坛、用户、公开收藏 | 内容可见性、私密设置与搜索配额仍生效 |
| 已登录 + 有效 API key | 在获授权范围内上传、发帖、编辑、评论、收藏、投票、发站内信、保存搜索 | 还看对象归属、封禁状态与 key 权限 |
| builder / approver / moderator / admin | 部分删除、恢复、审核、文件替换、账号管理与后台任务 | 不同动作要求不同角色 |
| 站点启用了可选后端 | archive 版本历史、IQDB、推荐服务 | 方法存在不保证每个 Danbooru 系站点都启用 |

返回字段只需记住这几条：

- **帖子与媒体**：`file_url` / `large_file_url` / `preview_file_url` 只在帖子对当前用户可见时出现，
  不可见时连 `md5` 也会被省去，所以不能按 `post['file_url']` 必存在来写代码。
- **用户**：公开资料可查；`favorite_tags`、`blacklisted_tags`、`per_page` 等偏好通常只在查自己时出现。
- **评论、投票与举报**：已删除正文、参与者身份等可能被隐藏；公开收藏可匿名读，私密收藏、上传详情与
  私信还要看归属与权限。

以上是上游权限过滤器的行为概括，逐条规则与出处见
[附注的权限过滤器](danbooru-contract-notes.md#权限与字段级过滤器)。

## 完整原生方法索引

以下是 `api_danbooru.py` 的 **227 个原生方法**，每项只解释“干什么”。签名与可复制调用见
[方法参考](danbooru-api.md)，每个方法的参数键、路由与状态见
[契约审计附注](danbooru-contract-notes.md#逐资源路由参数键与状态227-个原生方法)。

### 状态、API key 与限流

- `status` — 查询服务状态及当前身份信息。
- `api_keys_list` — 列出自己可管理的 API key。
- `api_key_create` — 创建 API key。
- `api_key_update` — 修改 API key 设置。
- `api_key_delete` — 删除 API key。
- `rate_limits_list` — 查询限流记录。

### 帖子与修改历史

- `post_list` — 搜索或列出帖子。
- `post_show` — 读取一个帖子的详情。
- `post_random` — 在查询范围内随机取得一个帖子。
- `post_create` — 将已上传的媒体发布为帖子。
- `post_update` — 更新帖子的标签、来源等属性。
- `post_delete` — 按给定理由删除帖子。
- `post_revert` — 将帖子恢复到指定版本。
- `post_copy_notes` — 把一个帖子的笔记复制到另一个帖子。
- `post_mark_as_translated` — 更新帖子的翻译状态标签。
- `post_events_list` — 查询帖子发生过的事件。
- `post_versions_list` — 查询帖子修改版本，依赖 archive 服务。
- `post_version_undo` — 撤销一个帖子修改版本。
- `post_favorites_list` — 查询某个帖子的收藏记录。

### 帖子投票

- `post_votes_list` — 查询帖子投票记录。
- `post_vote_show` — 读取一条帖子投票。
- `post_vote_create` — 对帖子投票。
- `post_vote_delete` — 按投票 ID 撤回帖子投票。

### 文件替换与重建

- `post_replacements_list` — 查询帖子文件替换记录。
- `post_replacement_show` — 读取一次文件替换的详情。
- `post_replacement_create` — 用新文件或来源替换帖子文件。
- `post_replacement_update` — 修改文件替换记录。
- `post_regeneration_create` — 提交帖子媒体重建任务。

### 批准、不批准、待删标记与申诉

- `post_approvals_list` — 查询帖子批准记录。
- `post_approval_show` — 读取一条批准记录。
- `post_approval_create` — 批准一个帖子。
- `post_disapprovals_list` — 查询帖子不批准记录。
- `post_disapproval_show` — 读取一条不批准记录。
- `post_disapproval_create` — 记录不批准某帖的决定与理由。
- `post_disapproval_update` — 修改不批准记录。
- `post_flags_list` — 查询帖子的待删标记。
- `post_flag_show` — 读取一个待删标记。
- `post_flag_create` — 为帖子提交待删理由。
- `post_flag_update` — 修改待处理标记的理由。
- `post_appeals_list` — 查询帖子申诉。
- `post_appeal_show` — 读取一条申诉。
- `post_appeal_create` — 对被删除的帖子提出申诉。
- `post_appeal_update` — 修改待处理申诉。

### 媒体资源与 AI 标签

- `media_assets_list` — 查询媒体资源。
- `media_asset_show` — 读取媒体资源详情。
- `media_asset_delete` — 删除媒体资源。
- `media_metadata_list` — 查询媒体元数据。
- `ai_tags_list` — 查询 AI 生成的候选标签。
- `ai_tag_tag` — 将 AI 候选标签应用到帖子或撤下。

### 上传及上传媒体

- `upload_list` — 查询当前用户可见的上传记录。
- `upload_show` — 读取上传处理状态和关联媒体。
- `upload_create` — 从文件或来源 URL 创建上传。
- `upload_assets_list` — 列出一次上传关联的媒体。
- `upload_media_assets_list` — 查询上传媒体记录。
- `upload_media_asset_show` — 读取一条上传媒体记录。

### 标签、别名、蕴含与搜索建议

- `tag_list` — 搜索标签。
- `tag_show` — 读取标签详情。
- `tag_update` — 修改获授权的标签属性。
- `tag_versions_list` — 查询标签修改历史。
- `tag_version_show` — 读取一个标签版本。
- `tag_aliases_list` — 查询标签别名关系。
- `tag_alias_show` — 读取一条别名关系。
- `tag_alias_delete` — 拒绝一条别名请求。
- `tag_implications_list` — 查询标签蕴含关系。
- `tag_implication_show` — 读取一条蕴含关系。
- `tag_implication_delete` — 拒绝一条蕴含请求。
- `related_tag` — 根据查询取得相关标签建议。
- `autocomplete_list` — 取得指定类型的自动补全建议。

### 画师与主页记录

- `artist_list` — 按名称、URL 等条件搜索画师。
- `artist_show` — 读取一个画师记录。
- `artist_show_or_new` — 按名称查画师，未找到时返回新记录形态。
- `artist_create` — 创建画师记录。
- `artist_update` — 修改画师名称、主页等信息。
- `artist_delete` — 软删除画师记录。
- `artist_revert` — 恢复画师记录的指定版本。
- `artist_ban` — 封禁画师。
- `artist_unban` — 解除画师封禁。
- `artist_urls_list` — 查询画师关联的主页地址。
- `artist_versions_list` — 查询画师记录修改历史。
- `artist_version_show` — 读取一个画师记录版本。
- `artist_commentaries_list` — 搜索作品的原作者说明与译文。
- `artist_commentary_show` — 读取某帖的原作者说明。
- `artist_commentary_create_or_update` — 创建或更新某帖的原作者说明与翻译。
- `artist_commentary_revert` — 恢复原作者说明的指定版本。
- `artist_commentary_versions_list` — 查询原作者说明修改历史。
- `artist_commentary_version_show` — 读取一个原作者说明版本。

### 评论与评论投票

- `comment_list` — 搜索或列出评论。
- `comment_show` — 读取一条评论。
- `comment_create` — 在帖子下发表评论。
- `comment_update` — 修改评论。
- `comment_delete` — 删除评论。
- `comment_undelete` — 恢复获授权的已删除评论。
- `comment_votes_list` — 查询评论投票记录。
- `comment_vote_show` — 读取一条评论投票。
- `comment_vote_create` — 对评论投票。
- `comment_vote_delete` — 按投票 ID 撤回评论投票。

### 图上笔记及笔记历史

- `note_list` — 查询图上笔记。
- `note_show` — 读取一个笔记。
- `note_create` — 在指定帖子和坐标创建笔记。
- `note_update` — 修改笔记位置、尺寸或正文。
- `note_delete` — 停用一个笔记。
- `note_revert` — 恢复笔记的指定版本。
- `note_preview` — 预览笔记正文的处理结果，不保存笔记。
- `note_versions_list` — 查询笔记修改历史。
- `note_version_show` — 读取一个笔记版本。

### 合集及合集历史

- `pool_list` — 搜索合集。
- `pool_show` — 读取合集和其帖子列表信息。
- `pool_create` — 创建合集。
- `pool_update` — 修改合集说明或帖子成员。
- `pool_delete` — 软删除合集。
- `pool_undelete` — 恢复已删除合集。
- `pool_revert` — 恢复合集的指定版本。
- `pool_gallery` — 查询合集画廊。
- `pool_element_create` — 向合集加入帖子。
- `pool_versions_list` — 查询合集修改历史，依赖 archive 服务。
- `pool_version_diff` — 比较两个合集版本。

### wiki 及 wiki 历史

- `wiki_page_list` — 搜索 wiki 页面。
- `wiki_page_show` — 按 ID 或标题读取 wiki 页面。
- `wiki_page_create` — 创建 wiki 页面。
- `wiki_page_update` — 修改 wiki 页面。
- `wiki_page_delete` — 软删除 wiki 页面。
- `wiki_page_revert` — 恢复 wiki 页面的指定版本。
- `wiki_page_show_or_new` — 按标题定位 wiki 页面或其新建入口。
- `wiki_page_versions_list` — 查询 wiki 修改历史。
- `wiki_page_version_show` — 读取一个 wiki 版本。
- `wiki_page_versions_diff` — 比较两个 wiki 版本。

### 用户、用户记录与改名

- `user_list` — 搜索用户。
- `user_show` — 读取用户公开资料及获授权的附加信息。
- `user_create` — 向站点提交注册请求，仍受注册与验证码规则约束。
- `user_update` — 修改自己的用户设置。
- `user_profile` — 读取当前登录用户资料。
- `user_actions_list` — 查询用户活动记录。
- `user_action_show` — 读取一条用户活动记录。
- `user_events_list` — 查询当前用户可见的用户事件。
- `user_feedbacks_list` — 查询用户评价记录。
- `user_feedback_show` — 读取一条用户评价。
- `user_feedback_create` — 创建用户评价。
- `user_feedback_update` — 修改用户评价。
- `user_name_change_requests_list` — 查询用户改名请求。
- `user_name_change_request_show` — 读取一条改名请求。
- `user_name_change_request_create` — 提交用户改名请求。

### 收藏与收藏组

- `favorite_list` — 查询当前用户可见的收藏。
- `favorite_create` — 收藏一个帖子。
- `favorite_delete` — 取消收藏一个帖子。
- `favorite_groups_list` — 查询当前用户可见的收藏组。
- `favorite_group_show` — 读取一个收藏组。
- `favorite_group_create` — 创建收藏组。
- `favorite_group_update` — 修改收藏组设置或成员。
- `favorite_group_delete` — 删除收藏组。
- `favorite_group_add_post` — 向收藏组加入帖子。
- `favorite_group_remove_post` — 从收藏组移除帖子。

### 论坛主题、帖子与投票

- `forum_topics_list` — 搜索可见的论坛主题。
- `forum_topic_show` — 读取论坛主题及其讨论。
- `forum_topic_create` — 创建论坛主题及首帖。
- `forum_topic_update` — 修改论坛主题。
- `forum_topic_delete` — 删除论坛主题。
- `forum_topic_undelete` — 恢复已删除主题。
- `forum_topics_mark_all_as_read` — 将论坛主题全部标为已读。
- `forum_posts_list` — 搜索论坛帖子。
- `forum_post_show` — 读取一个论坛帖子。
- `forum_post_create` — 向主题发表回复。
- `forum_post_update` — 修改论坛帖子正文。
- `forum_post_delete` — 删除论坛帖子。
- `forum_post_undelete` — 恢复已删除论坛帖子。
- `forum_post_votes_list` — 查询论坛帖子投票。
- `forum_post_vote_show` — 读取一条论坛帖子投票。
- `forum_post_vote_create` — 为允许投票的论坛帖子投票。
- `forum_post_vote_delete` — 撤回论坛帖子投票。
- `forum_topic_visits_list` — 查询论坛主题阅读记录。

### 站内信

- `dmail_list` — 查询当前用户可见的站内信。
- `dmail_show` — 读取一封站内信。
- `dmail_create` — 发送站内信。
- `dmail_update` — 修改站内信的已读、删除等状态。
- `dmails_mark_all_as_read` — 将站内信全部标为已读。

### 用户封禁与批量标签变更

- `ban_list` — 查询用户封禁记录。
- `ban_show` — 读取一条封禁记录。
- `ban_create` — 封禁用户。
- `ban_update` — 修改封禁理由或期限。
- `ban_delete` — 解除用户封禁。
- `bulk_update_requests_list` — 查询批量标签变更请求。
- `bulk_update_request_show` — 读取一个批量变更请求。
- `bulk_update_request_create` — 提交批量变更，包括别名或蕴含关系申请。
- `bulk_update_request_update` — 修改批量变更请求。
- `bulk_update_request_approve` — 批准批量变更请求。
- `bulk_update_request_delete` — 拒绝批量变更请求。

### IP、审核日志与举报处理

- `ip_bans_list` — 查询 IP 封禁记录。
- `ip_ban_show` — 读取一条 IP 封禁。
- `ip_ban_create` — 创建 IP 封禁。
- `ip_ban_update` — 修改 IP 封禁记录。
- `ip_address_show` — 查询 IP 地址信息。
- `ip_geolocations_list` — 查询 IP 地理信息。
- `mod_actions_list` — 查询当前用户可见的管理操作日志。
- `mod_action_show` — 读取一条管理操作日志。
- `modqueue_list` — 读取待审核帖子队列。
- `moderation_reports_list` — 查询当前用户可见的举报。
- `moderation_report_show` — 读取一个举报。
- `moderation_report_create` — 举报获授权类型的内容或行为。
- `moderation_report_update` — 更新举报处理状态。

### 站点公告与保存的搜索

- `news_updates_list` — 查询站点公告记录。
- `news_update_show` — 读取一条公告。
- `news_update_create` — 创建公告。
- `news_update_update` — 修改公告。
- `news_update_delete` — 删除公告。
- `saved_searches_list` — 查询保存的搜索。
- `saved_search_create` — 保存一个搜索查询。
- `saved_search_update` — 修改保存的搜索。
- `saved_search_delete` — 删除保存的搜索。

### 站点凭据与反应

- `site_credentials_list` — 查询获授权管理的外部站点凭据。
- `site_credential_show` — 读取一条站点凭据记录。
- `site_credential_create` — 添加外部站点凭据。
- `site_credential_update` — 修改站点凭据设置。
- `site_credential_delete` — 删除站点凭据。
- `reactions_list` — 查询内容上的反应记录。
- `reaction_show` — 读取一条反应。
- `reaction_create` — 为支持的内容添加反应。
- `reaction_delete` — 撤回反应。

### 报表、后台任务、来源与推荐

- `report_show` — 查询指定统计报表。
- `jobs_list` — 查询后台任务列表。
- `job_cancel` — 取消后台任务。
- `job_retry` — 重试后台任务。
- `job_run` — 立即运行后台任务。
- `job_delete` — 删除后台任务。
- `dtext_links_list` — 查询正文中的 DText 链接关系。
- `recommended_posts_list` — 向站点推荐服务查询结果。
- `counts_posts` — 统计标签查询匹配的帖子数。
- `source_show` — 请求站点解析来源 URL。
- `iqdb_query` — 通过站点的 IQDB 服务查询相似图片。

## 边界与未实测

早期 Danbooru 匿名验证为 15 次（12×200 与 404/410/422 各一次），另有画师重定向结果；后续候选站复核还访问过 users/autocomplete 等读路径。Safebooru 匿名可用且为 Danbooru。每个批次的具体路由与参数范围见 [verification.md](verification.md)，不把早期清单当作全量当前状态。全部写路径、上传媒体、高权限及可选服务成功路径仍未实测；本次总览重排没有新增网络请求。

`request()` 还能调到发现内容、指标、部分账号管理等没有原生方法的 JSON 路由，已有路由与非 JSON 排除项见[契约审计附注](danbooru-contract-notes.md)；它不是图片下载方法，也不会把 HTML 页面变成 JSON。客户端另有 `close()` 与 `with Danbooru(...) as client`，这两个是客户端操作，不计入上面的方法数。

继续阅读：[客户端用法](danbooru.md) · [完整方法与参数](danbooru-api.md) · [翻页方式](pagination.md) · [错误与权限失败](errors.md)
