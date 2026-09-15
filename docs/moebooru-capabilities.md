# Moebooru 能力总览：我想做什么，该用哪个接口？

**不知道从哪个方法查起，先看这页；已经知道端点，再看[方法参考](moebooru-api.md)。**

- **不登录也能开始**：找图、查帖子、标签、相关标签、画师、wiki、评论、笔记、合集、论坛、用户。
- **登录后才能改内容**：上传、编辑、投票、评论、笔记、合集维护、wiki、论坛；删除与审核还要求更高等级。
- **库负责调用 JSON API**，不是下载器或自动采集器：不自动保存图片、不自动翻页、不把 HTML 页面变成 JSON。
- **有接口不等于本站启用，也不等于已经实测**：本页不新增线上探测，真实执行范围单列在末尾一节。

## 先按目的找入口

下表的 `c` 是已按配置创建的 `Moebooru` 客户端（写法见[客户端用法](moebooru.md)）；
`tags`、各类 ID 等代表你先前取得的值。

| 我想做什么 | 能力与方法 | 最简调用形态 | 是否需要登录 |
| :--- | :--- | :--- | :--- |
| 按标签、评分、时间找图 | `post_list`：标签语言与网页搜索一致，支持 `id:` / `md5:` / `rating:` / `score:>` / `order:` 等元标签 | `c.post_list(tags=tags)` | 匿名可查 |
| 看一张图的详情 | `post_list`：**没有 `post_show`**，用 `tags='id:<id>'` 取单帖（空列表可能表示不存在或当前身份不可见） | `c.post_list(tags='id:{0}'.format(post_id))` | 匿名可查 |
| 下载原图或预览图 | `post_list` / `pool_show` 返回的 `file_url` / `sample_url` / `preview_url`；保存文件需另用 HTTP 客户端，本库没有下载方法 | `post = c.post_list(tags='id:{0}'.format(post_id))[0]` | 地址取决于帖子对当前用户是否可见 |
| 按作者找作品 | `post_list`：已知画师标签时直接当标签搜索 | `c.post_list(tags=artist_name)` | 匿名可查 |
| 查画师记录 | `artist_list`：按名字子串或主页 URL 过滤 | `c.artist_list(name=name)`；`c.artist_list(url=url)` | 匿名可查 |
| 找标签、同义名与相关标签 | `tag_list` / `tag_alias_list` / `tag_related` | `c.tag_list(limit=0)`；`c.tag_alias_list(query=name)`；`c.tag_related(tags=query, type='general')` | 匿名可查 |
| 让输入框给出标签/用户补全 | `tag_autocomplete_name` / `user_autocomplete_name` | `c.tag_autocomplete_name(term)` | 匿名可查 |
| 查 wiki 说明页与改动 | `wiki_list` / `wiki_history` / `wiki_recent_changes`：**没有 `wiki_show`**（页面只有 HTML） | `c.wiki_list(query=title)`；`c.wiki_history(title=title)` | 匿名可查 |
| 看评论、笔记与它们的版本 | `comment_list` / `comment_search` / `note_list` / `note_search` / `note_history` | `c.comment_list(post_id=post_id)`；`c.comment_search(query='')`；`c.note_list(post_id=post_id)` | 匿名可读；发表评论、改笔记需登录 |
| 按合集看系列作品 | `pool_list` / `pool_show`：`pool_list` 找合集，`pool_show` 拿**单个合集对象**（帖子在 `posts` 里） | `c.pool_list(query='order:name')`；`c.pool_show(pool_id)` | 匿名可读；维护合集需登录 |
| 查用户、看谁收藏了某帖 | `user_list` / `favorite_list_users` | `c.user_list(name=name)`；`c.favorite_list_users(post_id)` | 匿名可查 |
| 看论坛讨论 | `forum_list` / `forum_show` / `forum_search` | `c.forum_list(latest='1')`；`c.forum_search(query=query)` | 匿名可读；发帖需登录 |
| 找站点当前的热门帖 | `post_popular_recent` / `_by_day` / `_by_week` / `_by_month` | `c.post_popular_recent(period='1w')`；`c.post_popular_by_day(year=2026, month=9, day=15)` | 匿名可查 |
| 以图搜图 | `post_similar`：传 `url`、`id` 或已打开文件；文件由调用者用 `with open(...)` 管理 | `c.post_similar(url=url)`；`c.post_similar(file=upload_file)` | 匿名可用；依赖站点相似图服务 |
| 上传并发布作品 | `post_create`：已打开文件或**仅来源 URL**；文件由调用者负责关闭 | `c.post_create(tags, file=upload_file)`；`c.post_create(tags, source=url)` | 需登录（成员） |
| 改标签、来源、父帖、锁定状态 | `post_update` / `post_update_batch`：**没有文件替换** | `c.post_update(post_id, tags=tags)` | 需登录；还看帖子上传者与版主身份 |
| 投票、请求删除、恢复 | `post_vote` / `post_flag` / `post_undelete` | `c.post_vote(post_id, score=1)`；`c.post_flag(post_id, reason=reason)` | 投票与标记需登录；恢复需 janitor |
| 审核待删帖、释出被 hold 的帖子 | `post_moderate` / `post_activate` / `post_acknowledge_new_deleted_posts` | `c.post_moderate(ids={post_id: 1}, commit='Approve')`；`c.post_activate([post_id])` | 审核需 janitor；释出 hold 需成员，非版主仅限自己的帖子 |
| 维护合集 | `pool_create` / `pool_update` / `pool_add_post` / `pool_remove_post` / `pool_import` / `pool_order` / `pool_copy` / `pool_destroy` | `c.pool_add_post(pool_id, post_id)` | 需登录；复制需 contributor |
| 写笔记、回滚版本 | `note_update` / `note_revert` / `history_undo` | `c.note_update(post_id=post_id, x=1, y=1, width=10, height=10, body='…')` | 需登录 |
| 发评论、改评论、标垃圾 | `comment_create` / `comment_update` / `comment_destroy` / `comment_mark_as_spam` | `c.comment_create(post_id, body)` | 写评论需登录；`comment_mark_as_spam` 路由没有登录过滤器 |
| 编辑或重命名 wiki | `wiki_create` / `wiki_update` / `wiki_revert` / `wiki_lock` / `wiki_unlock` / `wiki_destroy` | `c.wiki_update(title, body=body)`；`c.wiki_update(title, new_title=new_title)` | 编辑需成员；锁定与删除需版主 |
| 发论坛帖、管理主题 | `forum_create` / `forum_update` / `forum_destroy` / `forum_lock` / `forum_unlock` / `forum_stick` / `forum_unstick` | `c.forum_create(title, body)` | 发帖需登录；主题管理需版主 |
| 维护画师与标签 | `artist_create` / `artist_update` / `artist_destroy` / `tag_update` / `tag_mass_edit` | `c.artist_update(artist_id, urls=urls)` | 画师与标签编辑需成员；删除画师需 privileged；批量改名需版主 |
| 审核别名与蕴含 | `tag_alias_create` / `tag_alias_update` / `tag_implication_create` / `tag_implication_update` | `c.tag_alias_update({alias_id: 1}, commit='Approve')` | 创建需成员；审批需版主（删除待审项时创建者也可以） |
| 账号相关 | `user_check` / `user_create` / `user_update` / `user_authenticate` / `user_modify_blacklist` / `user_reset_password` / `user_record_destroy` | `c.user_modify_blacklist(add=['tag'])` | 注册、凭据检查、密码重置可匿名进入；其余需登录，记录删除还需 privileged |

**四个容易选错的地方**：Moebooru **没有** `search` 字典，过滤条件放顶层；**没有 `post_show` / `wiki_show`**
这两个 JSON 方法，单帖用 `tags='id:<id>'`、wiki 用 `wiki_list` 或 `wiki_history`；`comment_list` **必须带
`post_id`**（否则返回空数组），要按分页读评论流用 `comment_search(query='')`；各端点的每页数量由服务端
写死，`comment_list`、`note_history`、`artist_list` **会忽略 `limit`**（见[方法参考的上限表](moebooru-api.md#分页与实际上限)）。

## 匿名和登录，能力差在哪里？

这里的「可匿名」表示源码允许进入该接口，不表示一定有结果或能看到全部记录。

| 身份 / 条件 | 可以期待的能力 | 主要边界 |
| :--- | :--- | :--- |
| 匿名 | 帖子、标签、相关标签、别名与蕴含列表、画师列表、wiki 列表/版本/最近改动、评论、笔记、合集、论坛、用户列表、收藏者名单、热门帖、相似图 | 内容可见性、私密设置与反垃圾过滤器仍然生效 |
| 已登录普通账号 | 上传、编辑帖子、投票、标记、评论、笔记、合集维护、wiki 编辑、论坛发帖 | 登录不是全站写权限，还要看对象归属、帖子锁定状态与账号等级 |
| contributor / privileged / janitor / mod / admin | 合集复制、画师删除、恢复与审核、wiki 锁定与删除、论坛主题管理、标签批量改名、用户记录删除 | 各动作要求的等级不同，逐条见[方法参考](moebooru-api.md)与[契约审计附注](moebooru-contract-notes.md) |

返回信息不必背字段表，只记住这几条：

- **写成功的标准回包**是 `{"success": true, ...}`；有些动作（别名/蕴含创建、合集导入与排序、论坛写操作）
  会让客户端跟随重定向拿到**目标页面的 JSON**，那不是写入确认，失败也可能重定向到同一页；
- `forum_mark_all_read` 是 `204` 空响应，客户端返回 `None`；
- 列表类动作返回**顶层数组**；`post_list` 带 `api_version='2'` 时返回
  `{posts, pool_posts, pools, tags, votes}` 信封；
- `tag_related` 的返回值是**对象** `{tag: [[name, count], ...]}`，不是数组；
- `favorite_list_users` 返回原始对象 `{'favorited_users': 'name1,name2'}`——服务端把名字拼成了一个字符串。

## 完整原生方法索引

以下按资源列出 `pybooru/api_moebooru.py` 的 **90 个原生方法**；每项只解释「干什么」，
签名、参数与返回字段见[方法参考](moebooru-api.md)。多数写动作需要登录或更高等级。

### 帖子（17）

- `post_list` — 搜索或列出帖子；单帖也用 `tags='id:<id>'`。
- `post_create` — 上传新帖（multipart 文件或仅来源 URL）。
- `post_update` — 更新帖子标签、来源、父帖与锁定状态（无文件替换）。
- `post_destroy` — 按理由删除帖子；对已删帖可永久删除（版主）。
- `post_revert_tags` — 把帖子标签回滚到某个标签历史。
- `post_vote` — 读取或写入自己对某帖的投票。
- `post_activate` — 释出被 hold 的帖子（非版主只能释出自己的）。
- `post_acknowledge_new_deleted_posts` — 标记「新删除帖」提示已读。
- `post_update_batch` — 一次请求改多个帖子。
- `post_moderate` — 批量通过或删除帖子（janitor）。
- `post_flag` — 标记待删，或取消自己的标记。
- `post_undelete` — 恢复已删除的帖子（janitor）。
- `post_similar` — 按 URL、帖子或文件查相似图。
- `post_popular_recent` — 最近一段时间的高分帖。
- `post_popular_by_day` — 某日热门帖。
- `post_popular_by_week` — 某周热门帖。
- `post_popular_by_month` — 某月热门帖。

### 合集（10）

- `pool_list` — 搜索或列出合集。
- `pool_show` — 读取一个合集及其帖子。
- `pool_create` — 新建合集（不回传新 id）。
- `pool_update` — 改名、描述与公开/启用状态。
- `pool_destroy` — 删除合集。
- `pool_add_post` — 往合集里加一个帖子。
- `pool_remove_post` — 从合集里移除一个帖子。
- `pool_copy` — 连帖子一起复制合集（contributor）。
- `pool_import` — 按顺序批量加入帖子。
- `pool_order` — 重排合集内帖子的顺序。

### 笔记、历史、收藏、内联与站内信（11）

- `note_list` — 列出笔记（可按帖子过滤）。
- `note_search` — 全文搜索笔记正文。
- `note_history` — 列出笔记的历史版本（`limit` 被忽略）。
- `note_revert` — 把笔记回滚到某个版本。
- `note_update` — 新建或更新笔记。
- `history_undo` — 撤销或重做一批历史变更。
- `favorite_list_users` — 读取收藏了某帖的用户名单（逗号字符串）。
- `inline_list` — 列出内联图组。
- `inline_copy` — 复制内联图组。
- `inline_delete` — 删除自己的内联图组。
- `dmail_mark_all_read` — 把站内信全部标记为已读。

### 画师（4）

- `artist_list` — 按名字子串或 URL 列出画师。
- `artist_create` — 新建画师记录。
- `artist_update` — 更新画师记录。
- `artist_destroy` — 删除画师记录（privileged）。

### 标签、别名与蕴含（12）

- `tag_list` — 列出或搜索标签（`limit=0` 取全部）。
- `tag_related` — 查询共现标签，返回按查询标签分组的结果。
- `tag_update` — 修改标签类型与歧义标记（POST，键名 `tag[name]`）。
- `tag_autocomplete_name` — 标签名补全。
- `tag_summary` — 读取标签缓存摘要。
- `tag_mass_edit` — 全站批量改名（版主，仅在启用异步任务的站点有 JSON 回包）。
- `tag_alias_list` — 列出标签别名。
- `tag_alias_create` — 申请标签别名。
- `tag_alias_update` — 批准或删除标签别名。
- `tag_implication_list` — 列出标签蕴含。
- `tag_implication_create` — 申请标签蕴含。
- `tag_implication_update` — 批准或删除标签蕴含。

### 评论（7）

- `comment_list` — 列出某一帖的评论（必须带 `post_id`，且必须走 `.json`；`limit` 被忽略）。
- `comment_search` — 全文搜索评论；`query=''` 时不启用全文过滤。
- `comment_show` — 读取一条评论。
- `comment_create` — 发表评论（成员每小时限额只在顶层 `commit='Post'` 时才会被检查）。
- `comment_update` — 编辑自己的评论（或版主编辑任意评论）。
- `comment_destroy` — 删除自己的评论（或版主删除任意评论）。
- `comment_mark_as_spam` — 把评论标记为垃圾。

### Wiki（9）

- `wiki_list` — 搜索或列出 wiki 页面。
- `wiki_history` — 读取某个页面的全部版本。
- `wiki_recent_changes` — 最近的 wiki 改动。
- `wiki_create` — 新建 wiki 页面。
- `wiki_update` — 更新或改名 wiki 页面。
- `wiki_destroy` — 删除 wiki 页面（版主）。
- `wiki_lock` — 锁定页面（版主）。
- `wiki_unlock` — 解锁页面（版主）。
- `wiki_revert` — 回滚到某个版本。

### 论坛（11）

- `forum_list` — 列出主题或某主题的回复。
- `forum_show` — 读取一个论坛帖。
- `forum_search` — 全文搜索论坛帖。
- `forum_create` — 发新主题或回复。
- `forum_update` — 编辑论坛帖。
- `forum_destroy` — 删除论坛帖或主题。
- `forum_lock` — 锁定主题。
- `forum_unlock` — 解锁主题。
- `forum_stick` — 置顶主题。
- `forum_unstick` — 取消置顶。
- `forum_mark_all_read` — 把论坛全部标记为已读（返回 `None`）。

### 账号（9）

- `user_list` — 列出用户（每条只有 `{name, id}`）。
- `user_autocomplete_name` — 用户名补全。
- `user_check` — 检查用户名与明文密码（独立端点，按协议要求明文）。
- `user_create` — 注册账号。
- `user_update` — 修改当前账号设置。
- `user_authenticate` — 重新认证当前会话。
- `user_modify_blacklist` — 增删自己的标签黑名单。
- `user_reset_password` — 请求重置密码邮件。
- `user_record_destroy` — 删除用户记录（privileged）。

## 找不到原生方法时

**90 个方法只覆盖有 JSON 契约的端点**：浏览型页面、JS 交互、Atom/RSS 订阅源与合集 ZIP 都被有意排除
（都有真实路由，只是没有 JSON）。完整清单、原因与逐条状态见
[契约审计附注](moebooru-contract-notes.md)的排除项一节；按需可以直接用通用入口：

```python
c.request('GET', 'post/popular_recent', params={'period': '1w'})
```

`request()` 不会把 HTML 变成 JSON，也不会替你判断写操作重定向后的结果。客户端另有 `close()` 与
`with Moebooru(...) as c` 管理连接生命周期，这两个不算 API 方法。

## 边界与未实测汇总

- 本页不新增线上探测，也不重复计数：匿名只读端点在 `yande.re` 上的逐条执行记录见
  [verification.md](verification.md)。
- **全部写接口与账号动作只做源码对齐，没有线上实测**；`user_check` / `user_create` /
  `user_reset_password` 没有可用凭据，只保证请求形态与源码一致。
- 未指名执行的读接口（相似图、其余热门查询、补全/标签摘要/别名/蕴含、论坛详情/搜索等）同样仅源码对齐。
- 方法存在不等于目标站点启用了该能力：相似图服务、异步任务后端、站点自行关闭的功能都可能缺失，
  由服务端决定结果；本库不加兜底、不伪造替代响应。逐条状态见[契约审计附注](moebooru-contract-notes.md)。

继续阅读：[客户端用法](moebooru.md) · [方法参考](moebooru-api.md) ·
[契约审计附注](moebooru-contract-notes.md) · [翻页方式](pagination.md) · [错误与权限失败](errors.md)。
