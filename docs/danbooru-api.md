# Danbooru 方法参考

`Danbooru` 的 227 个原生方法都是 `request()` 的薄封装，一个方法对应一条 JSON 路由。构造、认证、
参数编码与返回值见 [客户端用法](danbooru.md)；按目的找入口见
[能力入口](danbooru-capabilities.md)。

**读法**：每组先给通用模式和 2–4 个常用方法的可复制片段（含返回形状与特有注意），其余方法用一行式
条目列出“何时用 + 返回要点”。每个方法的完整路由、凭据、参数键、上游出处与验证状态在
[契约审计附注](danbooru-contract-notes.md) 的对应小节。

## 共用前置

本页所有片段都接着这段前置写：`client` 已构造好，`example` 是配置里的样例输入。每个片段自己把用到的
id 读出来或赋值（例如从 `post_list` 的响应取 `post_id`），本库不代取；结束后调用 `client.close()`，
也可以把整段放入 `with Danbooru(...) as client:`，见 [客户端用法](danbooru.md)。

```python
from anybooru import Danbooru

client = Danbooru('danbooru')                     # 读包内默认 anybooru.json
example = client.config['examples']['danbooru']   # 样例输入：站点、关键词、条数等
```

## 全页通用契约

* **认证**：`username` 或 `api_key` 任一非空即发 HTTP Basic；凭据不完整或无效由服务端以 `401`
  拒绝，不会静默降级为匿名；匿名读接口默认放行，权限不足返回 `403`。
* **参数分层**：列表方法的过滤条件放 `search` 字典（整包发成 `search[...]`），顶层参数走
  `**params`（`limit`、`page`、`tags`、`post_id` 等）。**帖子列表是唯一例外**：过滤条件全部写成顶层
  `tags` 元标签，不吃 `search` 字典。
* **搜索后缀**：string 属性有 `_present`/`_eq`/`_not_eq`/`_like`/`_ilike`/`_regex`/`_array`/
  `_comma`/`_space`/`_lower_array` 等；text 另有 `_matches`（全文，含 `*` 时按 `ILIKE`）；数值与时间
  支持 `5`、`>5`、`5..10`、`5,6,7`；布尔收 `true/false/1/0/yes/no`；关联字段另有 `assoc_name`、
  `assoc_tags_match`、`has_assoc` 与嵌套 `search[assoc][...]`。**集合之外的参数被静默忽略**——
  旧参数失效时表现为“返回全集”。
* **分页与配额**：默认每页 20；通用上限 1000，`posts` 与 `uploads` / `upload_media_assets` /
  `media_assets` / `ai_tags` 为 200；页码上限普通 1000、Gold 5000，超出 `410`；标签数上限匿名 2、
  Gold 6、Platinum 不限，超出 `422`。翻页见 [pagination.md](pagination.md)。
* **端点无关的顶层参数**：`only`（选返回字段与嵌套关联，如 `only=id,url,artist[name]`，只对
  json/xml 生效）、`redirect=true`（结果唯一时 302 到对象页面）、`safe_mode`（强制 `rating:g`）、
  `save_data`（省流模式）。
* **失败**：非 2xx 抛 `AnybooruHTTPError`（保留状态码、URL 与正文），2xx 但非 JSON 抛
  `AnybooruAPIError`；archive 未配置返回 `501`，IQDB 未配置则返回空数组，各可选服务分别判断。见
  [errors.md](errors.md)。

## 状态、账号与限流（6 个方法）

`status` 读服务状态，`api_keys_list` / `rate_limits_list` 读 key 与限流记录，`api_key_*` 是写；API key 的读接口还要求重新认证。

`status()` — 查服务、数据库与缓存状态（不需要登录）。
```python
state = client.status()
```
返回对象：`ip`、`headers`、`instance`、`version`、`server`、`postgres`、`redis`；例如 `postgres['up']` 表示数据库状态。

`api_keys_list(search=None, **params)` — 列出自己可管理的 API key。
```python
keys = client.api_keys_list(limit=10)
```
返回 api_key 数组（含 `id`、`user_id`、`name`、`permissions`）；响应里**不含** `key`。

其余方法（完整参数键、路由与凭据见[附注的 状态节](danbooru-contract-notes.md#sec-status)）：

- `rate_limits_list(search=None, **params)` — 查询限流记录；返回 rate_limit 数组。
- `api_key_create(**attributes)` — 新建 API key（`name`、`permitted_ip_addresses`、`permissions`）；返回新建的 api_key 对象，**明文 `key` 只在这个响应里出现**。
- `api_key_update(api_key_id, **attributes)` — 改名称、允许 IP 或权限；返回更新后的 api_key 对象（不含 `key`）。
- `api_key_delete(api_key_id)` — 删除一把 API key；返回被删除的 api_key 对象（不含 `key`）。

## posts（帖子）— 37 个方法

`post_list` 的过滤条件全部写在顶层 `tags` 元标签里（`rating:g`、`score:>10`、`order:score`、`date:..`），**不吃 `search` 字典**；`md5=` 直接返回单个 post，`random=true` 会 302。发布新帖要先上传，见[上传节](#上传与上传媒体6-个方法)。

`post_list(**params)` — 搜索或列出帖子。
```python
posts = client.post_list(tags=example['tags'], limit=example['limit'])
```
返回 post 数组，常用字段为 `id`、`rating`、`tag_string`、`md5`、`source`；媒体 URL 随可见性提供。

`post_show(post_id)` — 读一个帖子的详情。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']   # 取一个真实存在的 id
post = client.post_show(post_id)
```
返回单个 post 对象，常用字段为 `id`、`rating`、`tag_string`、`md5`、`source`。

`post_random(tags=None)` — 在查询范围内随机取一帖。
```python
random_post = client.post_random(tags=example['tags'])
```
返回单个 post 对象；查询无匹配时 `404`。

`post_update(post_id, **attributes)` — 改标签、来源、评分、父帖等属性。
```python
post = client.post_list(tags=example['tags'], limit=1)[0]
client.post_update(post['id'], tag_string='1girl solo',
                   old_tag_string=post['tag_string'])
```
返回写后的 post 对象，含 `id`、`rating`、`tag_string`、`source` 等。

* `old_tag_string` / `old_parent_id` / `old_source` / `old_rating` 发送**编辑前看到的值**，供服务端处理并发编辑；不要把它们当作本次要写入的新值。

其余方法（完整参数键、路由与凭据见[附注的 posts 节](danbooru-contract-notes.md#sec-posts)）：

- `post_create(upload_media_asset_id, **attributes)` — 用上传媒体发布新帖；这个 id 是顶层参数，两步流程见[上传节](#上传与上传媒体6-个方法)；返回 post 对象，含 `id`、`rating`、`tag_string`、`source` 等。
- `post_delete(post_id, reason, move_favorites=None)` — 按理由删除帖子（approver+）；顶层 `commit=Delete` 由方法带上，理由为空时服务端回滚；返回删除后的 post 对象。
- `post_revert(post_id, version_id)` — 把帖子恢复到某个版本；返回回退后的 post 对象。
- `post_copy_notes(post_id, other_post_id)` — 把笔记复制到另一帖；成功时 `204`／空正文 → `None`，失败 `400` + `{success: false, reason}`。
- `post_mark_as_translated(post_id, check_translation=None, partially_translated=None)` — 增删 `check_translation` / `partially_translated`；返回更新后的 post 对象。
- `post_events_list(search=None, **params)` — 查询帖子事件（标签、评分、来源等改动）；顶层 `post_id` 亦可；返回 post_event 数组。
- `post_versions_list(search=None, **params)` — 查询帖子版本；站点未配置 archive 服务时 `501`，且没有单版本 JSON 路由；返回 post_version 数组（含 `id`、`post_id`、`updater_id`、`version`、`parent_changed`）。
- `post_version_undo(version_id)` — 撤销某个帖子版本带来的改动；返回撤销后的 post_version 对象。
- `post_favorites_list(post_id, search=None, **params)` — 某帖的收藏记录；返回 favorite 数组（含 `id`、`post_id`、`user_id`）。

### 帖子投票（4 个方法）

`score` 是数字：帖子与评论投票只接受 `1` / `-1`；论坛帖子投票另接受 `0`（中性）。字符串 `'up'` / `'down'` 不是合法值。

`post_votes_list(search=None, **params)` — 查询帖子投票记录。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']
votes = client.post_votes_list(search={'post_id': post_id})
```
返回 post_vote 数组（含 `id`、`post_id`、`user_id`、`score`）。

`post_vote_create(post_id, score)` — 给帖子投票，`1` 赞、`-1` 踩。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']   # 取一个真实存在的 id
client.post_vote_create(post_id, score=1)
```
返回新建的 post_vote 对象（含 `id`、`post_id`、`user_id`、`score`）。

其余方法（完整参数键、路由与凭据见[附注的 posts 节](danbooru-contract-notes.md#sec-posts)）：

- `post_vote_delete(vote_id)` — 按投票 id 撤回帖子投票（没有按帖子撤票的路由）；返回被更新/删除后的 post_vote 对象（含 `id`、`post_id`、`user_id`、`score`）。
- `post_vote_show(vote_id)` — 读取一条帖子投票；可见范围受限；返回单个 post_vote 对象（含 `id`、`post_id`、`user_id`、`score`）。

### 文件替换与再生（5 个方法）

替换已有帖子的文件是**第二条 multipart 路径**（第一条是 `upload_create`）：本地文件走 `replacement_file`，或给 `replacement_url`；需要 moderator 权限。

`post_replacement_create(post_id, replacement_file=None, **attributes)` — 用新文件或来源替换帖子文件。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']
client.post_replacement_create(post_id,
                               replacement_url='https://example.com/new.jpg',
                               final_source='https://example.com/page')
```
返回新建的 post_replacement 对象。

其余方法（完整参数键、路由与凭据见[附注的 posts 节](danbooru-contract-notes.md#sec-posts)）：

- `post_replacements_list(search=None, **params)` — 查询文件替换记录；顶层 `post_id` 亦可；返回 post_replacement 数组（含 `id`、`post_id`、`creator_id`、`original_url`、`replacement_url`）。
- `post_replacement_show(replacement_id)` — 读一次文件替换；返回单个 post_replacement 对象（含 `id`、`post_id`、`creator_id`、`original_url`、`replacement_url`）。
- `post_replacement_update(replacement_id, **attributes)` — 修改替换记录的 MD5、尺寸与来源等；返回写后的 post_replacement 对象（含 `id`、`post_id`、`creator_id`、`original_url`、`replacement_url`）。
- `post_regeneration_create(post_id, category=None)` — 提交媒体重建任务（moderator）；`category` 取 `post` / `large` / `preview`；返回提交重建的 post 对象。

## 批准、不批准、待删标记与申诉（15 个方法）

以列表与单条读为主；写动作分别要求 approver、登录或本人，提交待删标记不等于删除。

`post_flags_list(search=None, **params)` — 查询帖子的待删标记。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']
flags = client.post_flags_list(search={'post_id': post_id})
```
返回 post_flag 数组（含 `id`、`post_id`、`creator_id`、`reason`、`is_resolved`）。

`post_approvals_list(search=None, **params)` — 查询帖子批准记录。
```python
client.post_approvals_list(search={'post_id': post_id})
```
返回 post_approval 数组（含 `id`、`user_id`、`post_id`）。

其余方法（完整参数键、路由与凭据见[附注的 posts 节](danbooru-contract-notes.md#sec-posts)）：

- `post_disapprovals_list(search=None, **params)` — 查询帖子不批准记录；返回 post_disapproval 数组（含 `id`、`user_id`、`post_id`、`reason`、`message`）。
- `post_approval_show(approval_id)` — 读取一条批准记录；返回单个 post_approval 对象（含 `id`、`user_id`、`post_id`）。
- `post_approval_create(post_id)` — 批准一个帖子（approver+）；`post_id` 顶层；返回写后的 post_approval 对象（含 `id`、`user_id`、`post_id`）。
- `post_disapproval_show(disapproval_id)` — 读取一条不批准记录；返回单个 post_disapproval 对象（含 `id`、`user_id`、`post_id`、`reason`、`message`）。
- `post_disapproval_create(post_id, **attributes)` — 记录不批准决定；`reason` 取 `borderline_quality` / `borderline_safety` / `breaks_rules` / `disinterest` / `poor_quality`；返回写后的 post_disapproval 对象（含 `id`、`user_id`、`post_id`、`reason`、`message`）。
- `post_disapproval_update(disapproval_id, **attributes)` — 修改不批准记录；返回写后的 post_disapproval 对象（含 `id`、`user_id`、`post_id`、`reason`、`message`）。
- `post_flag_show(flag_id)` — 读取一个待删标记；返回单个 post_flag 对象（含 `id`、`post_id`、`creator_id`、`reason`、`is_resolved`）。
- `post_flag_create(post_id, reason, **attributes)` — 为帖子提交待删理由（登录即可，不等于删除）；返回写后的 post_flag 对象（含 `id`、`post_id`、`creator_id`、`reason`、`is_resolved`）。
- `post_flag_update(flag_id, reason, **attributes)` — 修改待处理标记的理由；返回写后的 post_flag 对象（含 `id`、`post_id`、`creator_id`、`reason`、`is_resolved`）。
- `post_appeals_list(search=None, **params)` — 查询帖子申诉；返回 post_appeal 数组（含 `id`、`post_id`、`creator_id`、`reason`、`status`）。
- `post_appeal_show(appeal_id)` — 读取一条申诉；可见范围受限；返回单个 post_appeal 对象（含 `id`、`post_id`、`creator_id`、`reason`、`status`）。
- `post_appeal_create(post_id, reason, **attributes)` — 对被删除的帖子提出申诉；返回写后的 post_appeal 对象（含 `id`、`post_id`、`creator_id`、`reason`、`status`）。
- `post_appeal_update(appeal_id, reason, **attributes)` — 修改待处理申诉（本人且 pending）；返回写后的 post_appeal 对象（含 `id`、`post_id`、`creator_id`、`reason`、`status`）。

## 媒体资源与 AI 标签（6 个方法）

`media_assets` 是文件层面的资源记录，字段按可见性裁剪；AI 候选标签来自站点的识别服务。

`media_assets_list(search=None, **params)` — 查询媒体资源。
```python
post = client.post_list(tags=example['tags'], limit=1)[0]
client.media_assets_list(search={'md5': post['md5']})
```
返回 media_asset 数组（含 `id`、`md5`、`file_ext`、`file_size`、`image_width`）。

`ai_tags_list(search=None, **params)` — 查询某个帖子或媒体的 AI 候选标签。
```python
post = client.post_list(tags=example['tags'], limit=1)[0]
client.ai_tags_list(search={'post_id': post['id']})
```
返回 ai_tag 数组（含 `media_asset_id`、`tag_id`、`score`）。

其余方法（完整参数键、路由与凭据见[附注的 媒体节](danbooru-contract-notes.md#sec-media)）：

- `media_asset_show(media_asset_id)` — 读媒体资源；不可见的资产会省掉 `md5`、`file_key`、`variants`。
- `media_asset_delete(media_asset_id)` — 删除媒体资源（admin）；返回删除后的 media_asset 对象（需 admin，见附注矛盾项）。
- `media_metadata_list(search=None, **params)` — 查询媒体元数据；返回 media_metadata 数组（含 `id`、`media_asset_id`、`metadata`）。
- `ai_tag_tag(media_asset_id, tag_id, tag=None, mode=None)` — 把 AI 候选标签应用到帖子；`mode='remove'` 表示撤下；返回被更新的 ai_tag 对象（同时会改动对应帖子的标签）。

## 上传与上传媒体（6 个方法）

上传新帖分两步：`upload_create` 建上传（**唯一用于上传新媒体的 multipart 端点**；另一条 multipart 是 `post_replacement_create` 的 `replacement_file`），再用 `post_create(upload_media_asset_id, ...)` 发布。`files` 与 `source` 互斥，至少给一个；压缩包由服务端展开。

`upload_create(files=None, source=None, referer_url=None)` — 从本地文件或来源 URL 建上传，并把返回的 upload media asset 发布成帖子。
```python
upload = client.upload_create(source='https://example.com/a.jpg')   # 或 files=[open('a.jpg', 'rb')]
upload_media_asset_id = upload['upload_media_assets'][0]['id']
post = client.post_create(upload_media_asset_id, tag_string='1girl solo', rating='g')
```
返回 upload 对象（`id`、`source`、`status`、`media_asset_count` 等），并带上 `upload_media_assets` 关联。

`upload_list(search=None, **params)` — 查询当前用户可见的上传记录。
```python
uploads = client.upload_list(limit=10)
```
返回 upload 数组（含 `id`、`source`、`uploader_id`、`status`、`referer_url`）。

其余方法（完整参数键、路由与凭据见[附注的 上传节](danbooru-contract-notes.md#sec-uploads)）：

- `upload_assets_list(upload_id, search=None, **params)` — 列出一次上传关联的媒体；`upload_id` 用上传响应里的 `id`；返回 upload_media_asset 数组（含 `id`、`media_asset_id`、`status`、`post_id`、`page_url`）。
- `upload_media_asset_show(upload_media_asset_id)` — 读一条上传媒体记录；返回单个 upload_media_asset 对象（含 `id`、`upload_id`、`media_asset_id`、`status`、`source_url`）。
- `upload_show(upload_id)` — 读取上传处理状态与关联媒体（需登录、本人或 moderator）；返回单个 upload 对象（含 `id`、`source`、`uploader_id`、`status`、`referer_url`）。
- `upload_media_assets_list(search=None, **params)` — 查询上传媒体记录；返回 upload_media_asset 数组（含 `id`、`upload_id`、`media_asset_id`、`status`、`source_url`）。

## tags、别名、蕴含与相关标签（13 个方法）

创建别名与蕴含没有专用方法，走 `bulk_update_request_create`；`tag_alias_delete` / `tag_implication_delete` 的语义是拒绝请求。

`tag_list(search=None, **params)` — 搜索标签。
```python
tags = client.tag_list(search={'name_matches': 'touhou'}, limit=2)
```
返回 tag 数组（含 `id`、`name`、`post_count`、`category`、`is_deprecated`）。

`related_tag(search=None, **params)` — 根据标签查询取相关标签建议。
```python
related = client.related_tag(search={'query': 'touhou', 'order': 'frequency'}, limit=5)
```
返回对象：`query`、`post_count`、`tag`、`related_tags`（每项含 `tag`）、`wiki_page_tags`。

其余方法（完整参数键、路由与凭据见[附注的 tags 节](danbooru-contract-notes.md#sec-tags)）：

- `tag_show(tag_id)` — 读取标签详情；返回单个 tag 对象（含 `id`、`name`、`post_count`、`category`、`is_deprecated`）。
- `tag_update(tag_id, **attributes)` — 改 `category` / `is_deprecated`（改 category 要更高等级）；返回写后的 tag 对象（含 `id`、`name`、`post_count`、`category`、`is_deprecated`）。
- `tag_versions_list(search=None, **params)` — 查询标签修改历史；返回 tag_version 数组（含 `id`、`tag_id`、`updater_id`、`previous_version_id`、`version`）。
- `tag_version_show(version_id)` — 读取一个标签版本；返回单个 tag_version 对象（含 `id`、`tag_id`、`updater_id`、`previous_version_id`、`version`）。
- `tag_aliases_list(search=None, **params)` — 查询标签别名关系；返回 tag_alias 数组（含 `id`、`antecedent_name`、`consequent_name`、`creator_id`、`forum_topic_id`）。
- `tag_alias_show(tag_alias_id)` — 读取一条别名关系；返回单个 tag_alias 对象（含 `id`、`antecedent_name`、`consequent_name`、`creator_id`、`forum_topic_id`）。
- `tag_alias_delete(tag_alias_id)` — **拒绝**一条别名请求，不是删除既有别名；返回被更新/删除后的 tag_alias 对象（含 `id`、`antecedent_name`、`consequent_name`、`creator_id`、`forum_topic_id`）。
- `tag_implications_list(search=None, **params)` — 查询标签蕴含关系；返回 tag_implication 数组（含 `id`、`antecedent_name`、`consequent_name`、`creator_id`、`forum_topic_id`）。
- `tag_implication_show(tag_implication_id)` — 读取一条蕴含关系；返回单个 tag_implication 对象（含 `id`、`antecedent_name`、`consequent_name`、`creator_id`、`forum_topic_id`）。
- `tag_implication_delete(tag_implication_id)` — 拒绝一条蕴含请求；返回被更新/删除后的 tag_implication 对象（含 `id`、`antecedent_name`、`consequent_name`、`creator_id`、`forum_topic_id`）。
- `autocomplete_list(query, type=None, limit=None)` — 取输入补全建议；返回结果数组，元素形状随 `type` 不同；支持 `tag`（默认）/ `tag_query` / `artist` / `wiki_page` / `user` / `pool` / `comment` / `saved_search`，默认 10 条。

<a id="artists"></a>

## artists（画师与主页记录）— 18 个方法

画师记录里的 `name` 是与作品上的画师标签对应的名称，不是外部站点的作者 ID；主页地址是独立的 `artist_urls` 记录，`search[url_matches]` 由服务端归一化后匹配（完整地址按来源解析，也接受 `/正则/`、含 `*` 的通配与普通子串）。

`artist_list(search=None, **params)` — 按名称、主页 URL、是否封禁等条件搜索画师。
```python
artists = client.artist_list(search={'url_matches': 'https://www.pixiv.net/users/27517',
                                     'has_tag': True, 'order': 'name'})
```
返回 artist 数组（含 `id`、`name`、`is_banned`、`group_name`、`other_names`）。

`artist_show_or_new(name=None)` — 按名称查画师，未找到时返回新记录形态。
```python
artist = client.artist_show_or_new(name='fuzichoco')
```
名字已存在时重定向到该画师（`Accept: application/json` 下仍是 JSON），否则返回未保存的 artist 对象。

其余方法（完整参数键、路由与凭据见[附注的 artists 节](danbooru-contract-notes.md#sec-artists)）：

- `artist_urls_list(search=None, **params)` — 查询画师关联的主页地址记录；返回 artist_url 数组（含 `id`、`artist_id`、`url`、`is_active`）。
- `artist_show(artist_id)` — 读取一个画师记录；返回单个 artist 对象（含 `id`、`name`、`is_banned`、`group_name`、`other_names`）。
- `artist_create(name, **attributes)` — 创建画师（`name` 就是将来的标签名）；`other_names_string`、`group_name`、`url_string` 等属性；返回写后的 artist 对象（含 `id`、`name`、`is_banned`、`group_name`、`other_names`）。
- `artist_update(artist_id, **attributes)` — 改名称、其他名、团体与主页；返回写后的 artist 对象（含 `id`、`name`、`is_banned`、`group_name`、`other_names`）。
- `artist_delete(artist_id)` — 软删除画师（置 `is_deleted`，需 builder）；服务端重定向到画师页，最终响应决定结果（不是 JSON 会抛 `AnybooruAPIError`）。
- `artist_revert(artist_id, version_id)` — 恢复画师记录的指定版本；返回写后的 artist 对象（含 `id`、`name`、`is_banned`、`group_name`、`other_names`）。
- `artist_ban(artist_id)` — 封禁画师（admin）；服务端重定向到画师页，最终响应决定结果。
- `artist_unban(artist_id)` — 解除画师封禁（admin）；服务端重定向到画师页，最终响应决定结果。
- `artist_versions_list(search=None, **params)` — 查询画师记录修改历史；返回 artist_version 数组（含 `id`、`artist_id`、`name`、`updater_id`、`group_name`）。
- `artist_version_show(version_id)` — 读取一个画师记录版本；返回单个 artist_version 对象（含 `id`、`artist_id`、`name`、`updater_id`、`group_name`）。
- `artist_commentaries_list(search=None, **params)` — 搜索作品的原作者说明与译文；返回 artist_commentary 数组（含 `id`、`post_id`、`original_title`、`original_description`、`translated_title`）。
- `artist_commentary_show(post_id)` — 读取某帖的原作者说明；返回该帖的 artist_commentary 对象。
- `artist_commentary_create_or_update(post_id, **attributes)` — 创建或更新某帖说明与翻译（PUT）；返回该帖的 artist_commentary 对象（新建或更新后）。
- `artist_commentary_revert(post_id, version_id)` — 恢复说明的指定版本；路径里的 id 是 **post_id**；返回写后的 artist_commentary 对象（含 `id`、`post_id`、`original_title`、`original_description`、`translated_title`）。
- `artist_commentary_versions_list(search=None, **params)` — 查询说明修改历史；返回 artist_commentary_version 数组（含 `id`、`post_id`、`updater_id`、`original_title`、`original_description`）。
- `artist_commentary_version_show(version_id)` — 读取一个说明版本；返回单个 artist_commentary_version 对象（含 `id`、`post_id`、`updater_id`、`original_title`、`original_description`）。

## comments（评论与评论投票）— 10 个方法

非 moderator 看已删除评论时，正文、投票分与作者字段会被服务端省掉，按这些字段检索也受限。

`comment_list(search=None, **params)` — 搜索或列出评论。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']
comments = client.comment_list(search={'post_id': post_id})
```
返回 comment 数组（含 `id`、`post_id`、`creator_id`、`body`、`score`）。

`comment_show(comment_id)` — 读一条评论。
```python
comment = client.comment_list(limit=1)[0]        # 最近一条可见评论
client.comment_show(comment['id'])
```
返回单个 comment 对象（含 `id`、`post_id`、`creator_id`、`body`、`score`）。

其余方法（完整参数键、路由与凭据见[附注的 comments 节](danbooru-contract-notes.md#sec-comments)）：

- `comment_create(post_id, body, **attributes)` — 在帖子下发表评论（需登录）；返回写后的 comment 对象（含 `id`、`post_id`、`creator_id`、`body`、`score`）。
- `comment_update(comment_id, **attributes)` — 改正文、`is_deleted`、`is_sticky`（sticky 需 moderator）；返回写后的 comment 对象（含 `id`、`post_id`、`creator_id`、`body`、`score`）。
- `comment_delete(comment_id)` — 软删除评论（作者或 moderator）；返回被更新/删除后的 comment 对象（含 `id`、`post_id`、`creator_id`、`body`、`score`）。
- `comment_undelete(comment_id)` — 恢复已删除评论；返回恢复后的 comment 对象。
- `comment_votes_list(search=None, **params)` — 查询评论投票；顶层 `comment_id` 亦兼容；返回 comment_vote 数组（含 `id`、`comment_id`、`user_id`、`score`）。
- `comment_vote_show(vote_id)` — 读取一条评论投票；可见范围受限；返回单个 comment_vote 对象（含 `id`、`comment_id`、`user_id`、`score`）。
- `comment_vote_create(comment_id, score)` — 给评论投票，`score` 取 `1` / `-1`；返回新建的 comment_vote 对象（含 `id`、`comment_id`、`user_id`、`score`）。
- `comment_vote_delete(vote_id)` — 撤票只能用投票 id（没有按评论撤票的路由）；返回被更新/删除后的 comment_vote 对象（含 `id`、`comment_id`、`user_id`、`score`）。

## notes（图上笔记与笔记历史）— 9 个方法

笔记正文是 DText；创建与更新失败时返回 `422`。

`note_list(search=None, **params)` — 查询图上笔记。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']
notes = client.note_list(search={'post_id': post_id})
```
返回 note 数组（含 `id`、`post_id`、`x`、`y`、`width`）。

`note_preview(body)` — 预览笔记正文的渲染结果，不保存。
```python
client.note_preview('**正文**')
```
返回未保存的 note 对象，其中 `sanitized_body` 是渲染后的正文。

其余方法（完整参数键、路由与凭据见[附注的 notes 节](danbooru-contract-notes.md#sec-notes)）：

- `note_show(note_id)` — 读取一个笔记；返回单个 note 对象（含 `id`、`post_id`、`x`、`y`、`width`）。
- `note_create(post_id, x, y, width, height, body, **attributes)` — 在指定帖子与坐标创建笔记；`body` 为 DText，失败时 `422`；返回写后的 note 对象（含 `id`、`post_id`、`x`、`y`、`width`）。
- `note_update(note_id, **attributes)` — 改位置、尺寸或正文；返回写后的 note 对象（含 `id`、`post_id`、`x`、`y`、`width`）。
- `note_delete(note_id)` — 停用笔记（置 `is_active=false`）；返回被更新/删除后的 note 对象（含 `id`、`post_id`、`x`、`y`、`width`）。
- `note_revert(note_id, version_id)` — 恢复笔记的指定版本；返回写后的 note 对象（含 `id`、`post_id`、`x`、`y`、`width`）。
- `note_versions_list(search=None, **params)` — 查询笔记修改历史；**没有**按创建者过滤的参数；返回 note_version 数组（含 `id`、`note_id`、`post_id`、`updater_id`、`x`）。
- `note_version_show(version_id)` — 读取一个笔记版本；返回单个 note_version 对象（含 `id`、`note_id`、`post_id`、`updater_id`、`x`）。

## pools（合集）— 11 个方法

`post_ids` 就是帖子 id 数组；`pool_update` 传显式空数组可以清空内容（客户端会真的把空数组发出去）。

`pool_list(search=None, **params)` — 搜索合集。
```python
pools = client.pool_list(search={'name_matches': 'touhou'}, limit=5)
```
返回 pool 数组（含 `id`、`name`、`description`、`is_active`、`post_ids`）。

`pool_show(pool_id)` — 读合集及其帖子 id 列表。
```python
pool = client.pool_list(search={'name_matches': 'touhou'}, limit=1)[0]
client.pool_show(pool['id'])
```
返回单个 pool 对象（含 `id`、`name`、`description`、`is_active`、`post_ids`）。

其余方法（完整参数键、路由与凭据见[附注的 pools 节](danbooru-contract-notes.md#sec-pools)）：

- `pool_update(pool_id, **attributes)` — 修改合集说明或帖子成员；传 `post_ids=[]` 会真的发空数组（清空内容）；返回写后的 pool 对象（含 `id`、`name`、`description`、`is_active`、`post_ids`）。
- `pool_element_create(post_id, pool_id=None, pool_name=None)` — 向合集加入帖子；返回加入后所属的 pool 对象。
- `pool_create(name, **attributes)` — 创建合集（`description`、`category`、`post_ids`）；返回写后的 pool 对象（含 `id`、`name`、`description`、`is_active`、`post_ids`）。
- `pool_delete(pool_id)` — 软删除合集（builder）；返回被更新/删除后的 pool 对象（含 `id`、`name`、`description`、`is_active`、`post_ids`）。
- `pool_undelete(pool_id)` — 恢复已删除合集（builder）；返回写后的 pool 对象（含 `id`、`name`、`description`、`is_active`、`post_ids`）。
- `pool_revert(pool_id, version_id)` — 恢复合集的指定版本；返回写后的 pool 对象（含 `id`、`name`、`description`、`is_active`、`post_ids`）。
- `pool_gallery(search=None, **params)` — 合集画廊；服务端默认 `category=series`；返回 pool 数组（每项带一张预览帖）。
- `pool_versions_list(search=None, **params)` — 查询合集修改历史；未配置 archive 服务时 `501`；返回 pool_version 数组（含 `id`、`pool_id`、`updater_id`、`version`、`name`）。
- `pool_version_diff(pool_version_id, other_id=None, type=None)` — 比较两个版本，`type` 取 `previous` / `next`；返回两个 pool_version 的差异对象。

## wiki（wiki 页面与历史）— 10 个方法

`wiki_page_show` 的路径部分接受 id 或标题（标题会被 URL 转义）；列表要用 `search={'title': ...}`，顶层 `title=` 会被服务端 302 到标题搜索。

`wiki_page_list(search=None, **params)` — 搜索 wiki 页面。
```python
pages = client.wiki_page_list(search={'title': 'help:api'}, limit=2)
```
返回 wiki_page 数组（含 `id`、`title`、`body`、`is_locked`、`other_names`）。

`wiki_page_show(id_or_title)` — 按 id 或标题读 wiki 页面。
```python
client.wiki_page_show('help:api')
```
返回单个 wiki_page 对象（`title`、`body`、`other_names`、`is_locked` 等）。

其余方法（完整参数键、路由与凭据见[附注的 wiki 节](danbooru-contract-notes.md#sec-wiki)）：

- `wiki_page_create(title, **attributes)` — 创建页面（`body`、`other_names_string`、`is_locked` 需 builder）；返回写后的 wiki_page 对象（含 `id`、`title`、`body`、`is_locked`、`other_names`）。
- `wiki_page_update(wiki_page_id, **attributes)` — 改正文、其他名或 `is_deleted`；返回写后的 wiki_page 对象（含 `id`、`title`、`body`、`is_locked`、`other_names`）。
- `wiki_page_delete(wiki_page_id)` — 软删除并返回对象（builder）。
- `wiki_page_revert(wiki_page_id, version_id)` — 恢复指定版本；返回写后的 wiki_page 对象（含 `id`、`title`、`body`、`is_locked`、`other_names`）。
- `wiki_page_show_or_new(title=None)` — 按标题定位页面或新建入口；服务端 `302`；返回标题已存在时重定向到该页面，否则返回未保存的 wiki_page 对象。
- `wiki_page_versions_list(search=None, **params)` — 查询 wiki 修改历史；返回 wiki_page_version 数组（含 `id`、`wiki_page_id`、`updater_id`、`title`、`body`）。
- `wiki_page_version_show(version_id)` — 读取一个 wiki 版本；返回单个 wiki_page_version 对象（含 `id`、`wiki_page_id`、`updater_id`、`title`、`body`）。
- `wiki_page_versions_diff(thispage=None, otherpage=None, type=None)` — 比较两个版本；返回两个 wiki_page_version 的差异对象。

## users（用户、用户记录与改名）— 15 个方法

匿名只拿到 `id`、`created_at`、`name`、`inviter_id`、`level`、各类计数与封禁/删除标记；偏好设置类字段只有本人可见。`search[name]` 在 User 上会变成模糊的 `name_matches`。

`user_list(search=None, **params)` — 搜索用户。
```python
users = client.user_list(search={'name_matches': 'fuzichoco'}, limit=2)
```
返回 user 数组（字段按身份裁剪：匿名只有 `id`、`name`、`level` 等，本人多出偏好设置）。

`user_show(user_id)` — 读用户资料。
```python
user = client.user_list(search={'name_matches': 'fuzichoco'}, limit=1)[0]
client.user_show(user['id'])
```
返回单个 user 对象（字段按身份裁剪，本人视角多出偏好设置，见附注权限过滤器）。

`user_profile()` — 读当前登录用户。
```python
client.user_profile()
```
返回当前登录的 user 对象（本人视角，字段比 `user_show` 多）。

其余方法（完整参数键、路由与凭据见[附注的 users 节](danbooru-contract-notes.md#sec-users)）：

- `user_update(user_id, **attributes)` — 修改自己的用户设置（只能改自己）；返回写后的 user 对象（含 `id`、`name`、`inviter_id`、`level`、`last_logged_in_at`）。
- `user_create(name, password, password_confirmation)` — 提交注册；仍受站点验证码/邀请规则约束；返回写后的 user 对象（含 `id`、`name`、`inviter_id`、`level`、`last_logged_in_at`）。
- `user_actions_list(search=None, **params)` — 查询用户活动记录（moderator）；顶层 `user_id` 亦可；返回 user_action 数组。
- `user_action_show(user_action_id)` — 读取一条用户活动记录（moderator）；返回单个 user_action 对象。
- `user_events_list(search=None, **params)` — 查询用户事件；非 moderator 看不到 `session_id` / `user_agent`；返回 user_event 数组（含 `id`、`user_id`、`user_session_id`、`category`、`ip_addr`）。
- `user_feedbacks_list(search=None, **params)` — 查询用户评价；返回 user_feedback 数组。
- `user_feedback_show(feedback_id)` — 读取一条评价；返回单个 user_feedback 对象。
- `user_feedback_create(**attributes)` — 创建评价（`body`、`category`、`user_id` / `user_name`）；返回写后的 user_feedback 对象。
- `user_feedback_update(feedback_id, **attributes)` — 改评价正文、类别或删除标记；返回写后的 user_feedback 对象。
- `user_name_change_requests_list(search=None, **params)` — 查询改名请求（非匿名）；返回 user_name_change_request 数组（含 `id`、`user_id`、`original_name`、`desired_name`）。
- `user_name_change_request_show(request_id)` — 读取一条改名请求；返回单个 user_name_change_request 对象（含 `id`、`user_id`、`original_name`、`desired_name`）。
- `user_name_change_request_create(**attributes)` — 提交改名请求（`user_id`、`desired_name`）；返回写后的 user_name_change_request 对象（含 `id`、`user_id`、`original_name`、`desired_name`）。

## favorites（收藏与收藏组）— 10 个方法

`favorite_list` 默认列自己的收藏，顶层 `user_id` 指定别人；取消收藏的路径 id 就是 `post_id`。

`favorite_list(search=None, **params)` — 查询当前用户可见的收藏。
```python
user_id = client.user_list(search={'name_matches': 'fuzichoco'}, limit=1)[0]['id']
favorites = client.favorite_list(user_id=user_id)
```
返回 favorite 数组（含 `id`、`user_id`、`post_id`）。

`favorite_create(post_id)` — 收藏一个帖子。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']
client.favorite_create(post_id)
```
返回被收藏的 post 对象。

其余方法（完整参数键、路由与凭据见[附注的 收藏节](danbooru-contract-notes.md#sec-users)）：

- `favorite_delete(post_id)` — 取消收藏一个帖子；路径里的 id 就是 `post_id`；返回取消收藏后的 post 对象。
- `favorite_groups_list(search=None, **params)` — 查询收藏组；顶层 `user_id` 亦兼容；返回 favorite_group 数组（含 `id`、`name`、`creator_id`、`post_ids`、`is_public`）。
- `favorite_group_show(group_id)` — 读取一个收藏组；返回单个 favorite_group 对象（含 `id`、`name`、`creator_id`、`post_ids`、`is_public`）。
- `favorite_group_create(name, **attributes)` — 创建收藏组（`post_ids` / `post_ids_string`、`is_public`、`is_private`）；返回写后的 favorite_group 对象（含 `id`、`name`、`creator_id`、`post_ids`、`is_public`）。
- `favorite_group_update(group_id, **attributes)` — 改设置或成员；返回写后的 favorite_group 对象（含 `id`、`name`、`creator_id`、`post_ids`、`is_public`）。
- `favorite_group_delete(group_id)` — 删除收藏组；返回被更新/删除后的 favorite_group 对象（含 `id`、`name`、`creator_id`、`post_ids`、`is_public`）。
- `favorite_group_add_post(group_id, post_id)` — 加帖进收藏组；`post_id` 是顶层参数；返回更新后的 favorite_group 对象。
- `favorite_group_remove_post(group_id, post_id)` — 从收藏组移除帖子；返回更新后的 favorite_group 对象。

## forum（论坛主题、帖子与投票）— 18 个方法

公开主题可匿名读，按 `min_level` 过滤；发主题、回帖与投票需要登录，删除类动作需要 moderator。

`forum_topics_list(search=None, **params)` — 搜索可见的论坛主题。
```python
topics = client.forum_topics_list(limit=5)
```
返回 forum_topic 数组（含 `id`、`creator_id`、`updater_id`、`title`、`response_count`）。

`forum_posts_list(search=None, **params)` — 搜索论坛帖子。
```python
topic_id = client.forum_topics_list(limit=1)[0]['id']
client.forum_posts_list(search={'topic_id': topic_id})
```
返回 forum_post 数组（含 `id`、`topic_id`、`creator_id`、`updater_id`、`body`）。

其余方法（完整参数键、路由与凭据见[附注的 forum 节](danbooru-contract-notes.md#sec-forum)）：

- `forum_topic_show(topic_id)` — 读主题详情，内嵌 `forum_posts`；返回单个 forum_topic 对象（含 `id`、`creator_id`、`updater_id`、`title`、`response_count`）。
- `forum_post_create(topic_id, body)` — 向主题发表回复；返回写后的 forum_post 对象（含 `id`、`topic_id`、`creator_id`、`updater_id`、`body`）。
- `forum_topic_create(title, body, **attributes)` — 建主题及首帖（`category_id`；置顶/锁定需 moderator）；返回写后的 forum_topic 对象（含 `id`、`creator_id`、`updater_id`、`title`、`response_count`）。
- `forum_topic_update(topic_id, **attributes)` — 改标题、分类、置顶、锁定、`min_level`；返回写后的 forum_topic 对象（含 `id`、`creator_id`、`updater_id`、`title`、`response_count`）。
- `forum_topic_delete(topic_id)` — 软删除主题（moderator）；返回被更新/删除后的 forum_topic 对象（含 `id`、`creator_id`、`updater_id`、`title`、`response_count`）。
- `forum_topic_undelete(topic_id)` — 恢复已删除主题（moderator）；返回写后的 forum_topic 对象（含 `id`、`creator_id`、`updater_id`、`title`、`response_count`）。
- `forum_topics_mark_all_as_read()` — 把论坛主题全部标为已读；服务端重定向到主题列表，最终响应决定结果。
- `forum_post_show(post_id)` — 读取一个论坛帖子（不返回已删除的）。
- `forum_post_update(post_id, body)` — 改帖子正文；返回写后的 forum_post 对象（含 `id`、`topic_id`、`creator_id`、`updater_id`、`body`）。
- `forum_post_delete(post_id)` — 删除帖子（moderator）；返回被更新/删除后的 forum_post 对象（含 `id`、`topic_id`、`creator_id`、`updater_id`、`body`）。
- `forum_post_undelete(post_id)` — 恢复已删除帖子（moderator）；返回写后的 forum_post 对象（含 `id`、`topic_id`、`creator_id`、`updater_id`、`body`）。
- `forum_post_votes_list(search=None, **params)` — 查询论坛帖子投票；返回 forum_post_vote 数组（含 `id`、`forum_post_id`、`creator_id`、`score`）。
- `forum_post_vote_show(vote_id)` — 读取一条论坛帖子投票；可见范围受限；返回单个 forum_post_vote 对象（含 `id`、`forum_post_id`、`creator_id`、`score`）。
- `forum_post_vote_create(forum_post_id, score)` — 给论坛帖子投票，`score` 取 `1` / `-1` / `0`，`forum_post_id` 是顶层参数；返回新建的 forum_post_vote 对象。
- `forum_post_vote_delete(vote_id)` — 撤回论坛帖子投票；返回被更新/删除后的 forum_post_vote 对象（含 `id`、`forum_post_id`、`creator_id`、`score`）。
- `forum_topic_visits_list(search=None, **params)` — 查询论坛主题阅读记录（登录，本人）；返回 forum_topic_visit 数组（含 `id`、`user_id`、`forum_topic_id`、`last_read_at`）。

## dmails（站内信）— 5 个方法

只能看自己的站内信；删除没有独立方法，改用 `dmail_update(dmail_id, is_deleted=True)`。

`dmail_list(search=None, **params)` — 查询自己的站内信。
```python
dmails = client.dmail_list(search={'folder': 'received'})
```
返回 dmail 数组（含 `id`、`owner_id`、`from_id`、`to_id`、`title`）。

`dmail_create(title, body, to_name=None, to_id=None)` — 发送站内信。
```python
client.dmail_create(title='标题', body='正文', to_name='someone')
```
返回写后的 dmail 对象（含 `id`、`owner_id`、`from_id`、`to_id`、`title`）。

其余方法（完整参数键、路由与凭据见[附注的 dmails 节](danbooru-contract-notes.md#sec-dmails)）：

- `dmail_update(dmail_id, **attributes)` — 改已读、删除等状态；删除邮件也是走这里（`is_deleted=True`）；返回写后的 dmail 对象（含 `id`、`owner_id`、`from_id`、`to_id`、`title`）。
- `dmail_show(dmail_id)` — 读取一封站内信（本人）；返回单个 dmail 对象（含 `id`、`owner_id`、`from_id`、`to_id`、`title`）。
- `dmails_mark_all_as_read()` — 全部标为已读；返回被标为已读的站内信集合。

## bans 与 bulk update requests（封禁与批量标签变更）— 11 个方法

批量变更请求（BUR）是申请别名（`alias a -> b`）、蕴含（`imply a -> b`）与批量改标签的正规入口；删除 / 批准分别要求本人或 approver。

`bulk_update_request_create(script, **attributes)` — 提交批量标签变更请求。
```python
client.bulk_update_request_create('alias foo -> bar')
```
返回写后的 bulk_update_request 对象（含 `id`、`user_id`、`forum_topic_id`、`script`、`status`）。

其余方法（完整参数键、路由与凭据见[附注的 审核节](danbooru-contract-notes.md#sec-bans)）：

- `ban_list(search=None, **params)` — 查询用户封禁记录；返回 ban 数组（含 `id`、`user_id`、`reason`、`banner_id`、`duration`）。
- `ban_create(**attributes)` — 封禁用户（moderator+）；返回写后的 ban 对象（含 `id`、`user_id`、`reason`、`banner_id`、`duration`）。
- `bulk_update_requests_list(search=None, **params)` — 查询批量变更请求；返回 bulk_update_request 数组（含 `id`、`user_id`、`forum_topic_id`、`script`、`status`）。
- `ban_show(ban_id)` — 读取一条封禁记录；返回单个 ban 对象（含 `id`、`user_id`、`reason`、`banner_id`、`duration`）。
- `ban_update(ban_id, **attributes)` — 改理由或期限；返回写后的 ban 对象（含 `id`、`user_id`、`reason`、`banner_id`、`duration`）。
- `ban_delete(ban_id)` — 解除封禁；返回被更新/删除后的 ban 对象（含 `id`、`user_id`、`reason`、`banner_id`、`duration`）。
- `bulk_update_request_show(request_id)` — 读取一个批量变更请求；返回单个 bulk_update_request 对象（含 `id`、`user_id`、`forum_topic_id`、`script`、`status`）。
- `bulk_update_request_update(request_id, **attributes)` — 改脚本或关联话题（本人）；返回写后的 bulk_update_request 对象（含 `id`、`user_id`、`forum_topic_id`、`script`、`status`）。
- `bulk_update_request_approve(request_id)` — 批准（approver）；返回写后的 bulk_update_request 对象（含 `id`、`user_id`、`forum_topic_id`、`script`、`status`）。
- `bulk_update_request_delete(request_id)` — 语义是**拒绝**该请求；返回被更新/删除后的 bulk_update_request 对象（含 `id`、`user_id`、`forum_topic_id`、`script`、`status`）。

## IP、审核日志、队列与举报（13 个方法）

审核队列返回的是帖子列表；举报要求登录且对象类型可举报，处理状态只有 moderator 能改。

`modqueue_list(search=None, **params)` — 读取待审核帖子队列（approver）。
```python
client.modqueue_list(limit=20)
```
返回待审核的 post 数组（不是队列记录）。

`moderation_report_create(**attributes)` — 举报帖子、评论或用户。
```python
post_id = client.post_list(tags=example['tags'], limit=1)[0]['id']
client.moderation_report_create(model_type='Post', model_id=post_id, reason='理由')
```
返回写后的 moderation_report 对象（含 `id`、`model_type`、`model_id`、`creator_id`、`reason`）。

其余方法（完整参数键、路由与凭据见[附注的 审核节](danbooru-contract-notes.md#sec-moderation)）：

- `mod_actions_list(search=None, **params)` — 查询当前用户可见的管理操作日志；返回 mod_action 数组（含 `id`、`creator_id`、`description`、`category`、`subject_type`）。
- `ip_bans_list(search=None, **params)` — 查询 IP 封禁（moderator+）；返回 ip_ban 数组（含 `id`、`creator_id`、`ip_addr`、`reason`、`category`）。
- `ip_ban_show(ip_ban_id)` — 读取一条 IP 封禁；返回单个 ip_ban 对象（含 `id`、`creator_id`、`ip_addr`、`reason`、`category`）。
- `ip_ban_create(**attributes)` — 创建 IP 封禁（`ip_addr`、`reason`、`category`）；返回写后的 ip_ban 对象（含 `id`、`creator_id`、`ip_addr`、`reason`、`category`）。
- `ip_ban_update(ip_ban_id, **attributes)` — 修改 IP 封禁；返回写后的 ip_ban 对象（含 `id`、`creator_id`、`ip_addr`、`reason`、`category`）。
- `ip_address_show(ip_addr)` — 查询 IP 地址信息（moderator+，路径里的 id 是 IP 字符串）；返回该 IP 的查询结果对象（位置、ASN 等）。
- `ip_geolocations_list(search=None, **params)` — 查询 IP 地理信息（moderator+）；返回 ip_geolocation 数组（含 `id`、`ip_addr`、`network`、`asn`、`is_proxy`）。
- `mod_action_show(mod_action_id)` — 读取一条管理操作日志；返回单个 mod_action 对象（含 `id`、`creator_id`、`description`、`category`、`subject_type`）。
- `moderation_reports_list(search=None, **params)` — 查询举报；非 moderator 只看自己的；返回 moderation_report 数组（含 `id`、`model_type`、`model_id`、`creator_id`、`reason`）。
- `moderation_report_show(report_id)` — 读取一个举报；返回单个 moderation_report 对象（含 `id`、`model_type`、`model_id`、`creator_id`、`reason`）。
- `moderation_report_update(report_id, **attributes)` — 更新举报处理状态（moderator）；返回写后的 moderation_report 对象（含 `id`、`model_type`、`model_id`、`creator_id`、`reason`）。

## 公告、保存的搜索、站点凭据与反应（18 个方法）

公告与站点凭据是 admin 面；保存的搜索与反应属于已登录用户自己的数据。

`saved_search_create(**attributes)` — 保存一个搜索查询。
```python
client.saved_search_create(query=example['tags'], label_string='我关注的标签')
```
返回写后的 saved_search 对象（含 `id`、`user_id`、`query`、`labels`）。

其余方法（完整参数键、路由与凭据见[附注的 运维节](danbooru-contract-notes.md#sec-moderation)）：

- `news_updates_list(search=None, **params)` — 查询站点公告记录；返回 news_update 数组（含 `id`、`message`、`creator_id`、`updater_id`、`duration`）。
- `saved_searches_list(search=None, **params)` — 查询保存的搜索；返回 saved_search 数组（含 `id`、`user_id`、`query`、`labels`）。
- `site_credentials_list(search=None, **params)` — 查询获授权管理的外部站点凭据；返回 site_credential 数组（含 `id`、`site`、`creator_id`、`is_enabled`、`is_public`）。
- `reaction_create(**attributes)` — 为帖子、评论或论坛帖子添加反应；返回写后的 reaction 对象（含 `id`、`creator_id`、`reaction_id`、`model_type`、`model_id`）。
- `news_update_show(news_update_id)` — 读取一条公告；返回单个 news_update 对象（含 `id`、`message`、`creator_id`、`updater_id`、`duration`）。
- `news_update_create(message, **attributes)` — 创建公告（`duration` / `duration_in_days`）；返回写后的 news_update 对象（含 `id`、`message`、`creator_id`、`updater_id`、`duration`）。
- `news_update_update(news_update_id, **attributes)` — 修改公告；返回写后的 news_update 对象（含 `id`、`message`、`creator_id`、`updater_id`、`duration`）。
- `news_update_delete(news_update_id)` — 软删除公告；返回被更新/删除后的 news_update 对象（含 `id`、`message`、`creator_id`、`updater_id`、`duration`）。
- `saved_search_update(saved_search_id, **attributes)` — 修改保存的搜索；返回写后的 saved_search 对象（含 `id`、`user_id`、`query`、`labels`）。
- `saved_search_delete(saved_search_id)` — 删除保存的搜索；返回被更新/删除后的 saved_search 对象（含 `id`、`user_id`、`query`、`labels`）。
- `site_credential_show(site_credential_id)` — 读取一条站点凭据；返回单个 site_credential 对象（含 `id`、`site`、`creator_id`、`is_enabled`、`is_public`）。
- `site_credential_create(site, **attributes)` — 添加外部站点凭据（`credential` 键随站点而定）；返回写后的 site_credential 对象（含 `id`、`site`、`creator_id`、`is_enabled`、`is_public`）。
- `site_credential_update(site_credential_id, **attributes)` — 改启用状态；返回写后的 site_credential 对象（含 `id`、`site`、`creator_id`、`is_enabled`、`is_public`）。
- `site_credential_delete(site_credential_id)` — 删除站点凭据；返回被更新/删除后的 site_credential 对象（含 `id`、`site`、`creator_id`、`is_enabled`、`is_public`）。
- `reactions_list(search=None, **params)` — 查询反应记录；返回 reaction 数组（含 `id`、`creator_id`、`reaction_id`、`model_type`、`model_id`）。
- `reaction_show(reaction_id)` — 读取一条反应；返回单个 reaction 对象（含 `id`、`creator_id`、`reaction_id`、`model_type`、`model_id`）。
- `reaction_delete(reaction_id)` — 撤回反应；返回被更新/删除后的 reaction 对象（含 `id`、`creator_id`、`reaction_id`、`model_type`、`model_id`）。

## 报表、后台任务与杂项（11 个方法）

`counts_posts` 默认走估算与缓存；`source_show`、`iqdb_query` 依赖站点的来源解析与 IQDB 服务，方法存在不代表每个站点都启用。

`counts_posts(tags=None, estimate_count=None, skip_cache=None)` — 统计标签查询匹配的帖子数。
```python
client.counts_posts(tags=example['tags'])
```
返回 `{"counts": {"posts": <int>}}`。

`source_show(url, ref=None, mode=None)` — 请求站点解析来源 URL。
```python
client.source_show('https://www.pixiv.net/users/27517')
```
返回站点解析出的来源数据对象（画师／图片信息）。

`iqdb_query(**params)` — 通过站点的 IQDB 服务查相似图。
```python
client.iqdb_query(url='https://example.com/a.jpg')
```
返回匹配结果数组，每项含 `score`、`post` 等；IQDB 未配置或服务查询错误分支返回空数组。

其余方法（完整参数键、路由与凭据见[附注的 杂项节](danbooru-contract-notes.md#sec-misc)）：

- `report_show(report, search=None, **params)` — 查统计报表，`report` 取 `posts`、`post_votes`、`comments`、`users` 等模型名；返回报表对象（列与分组由 `columns`、`group` 参数决定）。
- `jobs_list(search=None, **params)` — 查询后台任务；非 admin 看不到 `serialized_params`；返回 background_job 数组。
- `job_cancel(job_id)` — 取消任务（janitor+），job id 是 `active_job_id`；返回写后的 background_job 对象。
- `job_retry(job_id)` — 重试任务；返回写后的 background_job 对象。
- `job_run(job_id)` — 立即运行任务；返回写后的 background_job 对象。
- `job_delete(job_id)` — 删除任务；返回被更新/删除后的 background_job 对象。
- `dtext_links_list(search=None, **params)` — 查询正文里的 DText 链接关系；返回 dtext_link 数组（含 `id`、`model_type`、`model_id`、`link_type`、`link_target`）。
- `recommended_posts_list(search=None, **params)` — 向站点推荐服务查询；`limit` 上限 200；返回 post 数组（含 `id`、`up_score`、`down_score`、`score`、`source`）。

## 边界与未实测

早期匿名只读验证已执行（本地 2026-09-15，站点 `danbooru.donmai.us`，代理 + 项目 venv，无凭据）：
15 次请求中 12 次 `200`，3 次为预期失败（`404` 不存在的帖子、`410` 页码超限、`422` 标签数超限），
另外单独验证了重定向端点 `artist_show_or_new`（302 → JSON）。该早期批次覆盖：
`post_list`（含 `tags` 搜索与 `page=b<id>` 游标）、`post_show`、`tag_list`、`artist_list`（URL 匹配、
布尔过滤、`order`、`any_name_matches`）、`artist_show_or_new`、`related_tag`、`wiki_page_list`、
`wiki_page_show`、`comment_list`、`pool_list`，以及三条错误路径。逐条记录见
[verification.md](verification.md)。

**写接口、上传媒体、高权限/重新认证、写重定向及 archive/IQDB/推荐服务仍未做线上成功验证**。
后续候选站复核另外访问过 `/users.json` 与 `/autocomplete.json` 等读路径，不能把早期覆盖清单当作全量当前状态。
Safebooru 匿名可用且为 Danbooru。
所有批次、路径与参数范围见 [verification.md](verification.md)，未列出的路由仍只有源码依据。
本次文档重排没有新增网络请求；完整路由、参数、权限与上游出处见
[契约审计附注](danbooru-contract-notes.md)。
