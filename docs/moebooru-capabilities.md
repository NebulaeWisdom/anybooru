# Moebooru 能力总览：我想做什么，该用哪个接口？

**不知道从哪个方法查起就看这页；已经知道端点要看参数表，去[方法参考](moebooru-api.md)。**
逐条源码出处、权限过滤器与被排除的浏览器页面在[契约审计附注](moebooru-contract-notes.md)。

- **不登录就能读**：帖子、标签、相关标签、标签别名与蕴含列表、画师、wiki、评论、笔记、合集、论坛、用户目录、收藏者名单、热门帖、相似图。
- **登录后才能写**：上传、改帖、投票、评论、笔记、合集维护、wiki 编辑、论坛发帖；删除与审核还要更高等级。
- **库只负责调用 JSON API**：不保存图片、不自动翻页、不把 HTML 页面变成 JSON。
- **有接口不等于本站启用，也不等于跑过**：本页不新增线上探测，真实执行范围集中在最后一节。

## 先按目的找入口

下表左边是你要做的事，中间是方法与关键参数，右边是可以直接抄的字面调用（`client` 是已经构造好的
`Moebooru`，构造见[客户端用法](moebooru.md)）。

| 我想做什么 | 方法与关键参数 | 直接抄的调用 |
| :--- | :--- | :--- |
| 按标签/评分/时间找图 | `post_list(tags=<站点标签语言>, page=, limit=)`；`rating:s`、`order:score`、`score:>10` 等元标签都可用 | `client.post_list(tags='rating:s', page=1, limit=3)` |
| 看某个编号的帖子 | `post_list(tags='id:<编号>')`；返回空数组表示不存在或当前身份看不见 | `client.post_list(tags='id:1269034')` |
| 按 md5 反查帖子 | `post_list(tags='md5:<哈希>')`，哈希从帖子对象的 `md5` 字段复制 | `client.post_list(tags='md5:' + posts[0]['md5'])` |
| 同时查询图片、标签、投票与合集 | `api_version='2'` 返回字典，三个 `include_*='1'` 参数决定额外加入哪些内容 | `client.post_list(tags='rating:s', limit=3, api_version='2', include_tags='1', include_votes='1', include_pools='1')` |
| 下载原图或预览图 | 用列表返回的 `file_url` / `sample_url` / `preview_url` / `jpeg_url`，自己用 HTTP 客户端保存；本库没有下载方法 | `posts[0]['file_url']` |
| 查画师记录 | `artist_list(name=<名字子串>)` 或 `artist_list(url=<主页地址>)`；返回 `id` / `name` / `alias_id` / `group_id` / `urls` | `client.artist_list(name='fuzichoco')` |
| 找标签、别名、相关标签 | `tag_list(name=)`；`tag_alias_list(query=)`；`tag_related(tags=, type=)` | `client.tag_related(tags='touhou', type='general')` |
| 让输入框补全 | `tag_autocomplete_name(term)` 最多 20 个名字；`user_autocomplete_name(term)` 关键词短于 2 字符回空数组 | `client.tag_autocomplete_name('touh')` |
| 查 wiki 正文与版本 | `wiki_list(query='title:<标题>')`；`wiki_history(title=<标题>)`；`wiki_recent_changes()`。**没有 `wiki_show`** | `client.wiki_list(query='title:touhou', limit=3)` |
| 读评论 | 单帖评论 `comment_list(post_id=<编号>)`；评论流 `comment_search(query='')`；单条 `comment_show(id)` | `client.comment_search(query='')` |
| 读笔记与笔记版本 | `note_list(post_id=)`（页码是帖子页）；`note_search(query=)`；`note_history(post_id=)` | `client.note_list(post_id=1269034)` |
| 按合集看系列 | `pool_list(query='order:name')`；`pool_show(<合集编号>)` 返回合集对象，帖子在里面的 `posts` 数组 | `client.pool_show(99411)` |
| 查用户、看谁收藏了 | `user_list(name=)` 每行只有 `name`/`id`；`favorite_list_users(<帖子编号>)` 返回 `{"favorited_users": "甲,乙"}` | `client.favorite_list_users(1269034)` |
| 看论坛 | `forum_list(page=1)` 主题；`forum_list(parent_id=<主题编号>)` 回复；`forum_search(query=)` | `client.forum_list(latest='1')` |
| 看最近热门 | `post_popular_recent(period='1w')`；还有 `post_popular_by_day/week/month(year=, month=, day=)`，最多 40 条 | `client.post_popular_recent(period='1w')` |
| 以图搜图 | `post_similar(url=)`、`post_similar(id=<帖子编号>)` 或 `post_similar(file=<已打开文件>)`；依赖站点开了相似图服务 | `client.post_similar(url='https://example.org/a.jpg')` |
| 上传作品 | `post_create(tags, file=<已打开文件>)` 或只给来源 `post_create(tags, source='https://…')` | `client.post_create('1girl rating:s', source='https://example.org/a.jpg')` |
| 改帖标签/来源/父帖 | `post_update(<帖子编号>, tags=…)`；**不能换文件** | `client.post_update(1269034, tags='1girl solo rating:s')` |
| 投票 / 标记待删 / 恢复 | `post_vote(<编号>, score=1)`；`post_flag(<编号>, reason='…')`；`post_undelete(<编号>)` | `client.post_vote(1269034, score=1)` |
| 审核与释出 hold | `post_moderate({编号: 1}, commit='Approve')`（janitor）；`post_activate([编号])`（成员，非版主限自己的） | `client.post_activate([1269034])` |
| 维护合集 | `pool_create(name)`、`pool_update(<编号>, name=…)`、`pool_add_post(<合集>, <帖子>)`、`pool_remove_post`、`pool_import`、`pool_order`、`pool_copy`、`pool_destroy` | `client.pool_add_post(99411, 1269034)` |
| 写笔记 / 回滚版本 | `note_update(post_id=, x=, y=, width=, height=, body=)`；`note_revert(<笔记编号>, version=)`；`history_undo([变更编号])` | `client.note_update(post_id=1269034, x=10, y=10, width=100, height=100, body='译注')` |
| 发/改/删评论 | `comment_create(<帖子编号>, '正文')`；`comment_update(<评论编号>, body='…')`；`comment_destroy`；`comment_mark_as_spam` | `client.comment_create(1269034, '好图')` |
| 编辑或改名 wiki | `wiki_create(title, body)`；`wiki_update(title, new_title=…)`；`wiki_revert`、`wiki_lock`、`wiki_unlock`、`wiki_destroy` | `client.wiki_update('old_title', new_title='new_title')` |
| 论坛发帖与管理 | `forum_create(title, body, parent_id=0)`；`forum_update`、`forum_destroy`、`forum_lock`、`forum_unlock`、`forum_stick`、`forum_unstick` | `client.forum_create('标题', '正文')` |
| 维护画师与标签 | `artist_create(name, urls=…)`、`artist_update(<编号>, urls=…)`、`artist_destroy(<编号>)`、`tag_update(name, tag_type=1)`、`tag_mass_edit(start, result)` | `client.tag_update('touhou', tag_type=1)` |
| 审批别名与蕴含 | `tag_alias_create(name, alias_name)`；`tag_alias_update({编号: 1}, commit='Approve')`；蕴含同理 | `client.tag_alias_update({100: 1}, commit='Approve')` |
| 账号相关 | `user_check(username, password)`（明文，按协议）；`user_create(name, password, password_confirmation)`；`user_update(...)`；`user_modify_blacklist(add=['tag'])`；`user_reset_password(name, email)` | `client.user_modify_blacklist(add=['bad_tag'])` |

**五个容易选错的地方**：① Moebooru **没有** `search[...]` 字典，过滤条件放顶层；
② **没有 `post_show` 和 `wiki_show`**，单帖用 `tags='id:<编号>'`，wiki 用 `wiki_list` / `wiki_history`；
③ `comment_list` **必须带 `post_id`**，不带只会查到空列表，按页读评论流要用 `comment_search(query='')`；
④ 每页条数由服务端写死，`comment_list`、`note_history`、`artist_list` **不读 `limit`**（见[方法参考的上限表](moebooru-api.md#分页与实际上限)）；
⑤ 写动作要传引擎按字符串比较的字面值（`unflag='1'`、`redo='1'`、`commit='Approve'`），传 Python 布尔不生效。

## 匿名 vs 登录，能做的事差在哪

“匿名可查”只表示源码允许不带凭据进入该接口，不保证有结果、也不保证能看到全部记录。

| 身份 | 能做什么 | 边界 |
| :--- | :--- | :--- |
| 匿名 | 帖子列表与单帖、标签、相关标签、别名/蕴含列表、画师列表、wiki 列表与版本、评论、笔记、笔记版本、合集、论坛、用户目录、收藏者名单、热门帖、相似图 | 帖子可见性、私密设置与站点的反垃圾逻辑照样生效；被删帖的 `file_url` 等地址字段会缺失 |
| 已登录普通账号 | 上传、改帖、投票、标记、发评论、写笔记、维护合集、编辑 wiki、发论坛帖 | 登录不等于全站写权限，还要看是不是自己的东西、帖子是否锁定与账号等级 |
| contributor / privileged / janitor / mod / admin | 合集复制（contributor）、删画师（privileged）、恢复与审核（janitor）、wiki 锁定/删除与论坛主题管理（mod） | 各动作要求不同，逐条见表与[方法参考](moebooru-api.md) |

返回结构只要记住这几条（细节字段见[方法参考](moebooru-api.md#返回结构)）：

- 写成功的标准回包是 `{"success": true}`；部分动作会多带键：`count`（`post_activate`）、
  `vote`（`post_vote` 只读）、`new_id`/`old_id`/`formatted_body`（`note_update`）、
  `location`（`wiki_create`）、`result`（黑名单、密码重置）。
- 有些动作（别名/蕴含创建、合集导入与排序、论坛写操作）服务端只回重定向，客户端跟过去拿到的是目标页面的
  JSON，**那不是写入确认**，失败也可能重定向到同一页。
- `forum_mark_all_read()` 是 `204` 空响应，客户端返回 `None`。
- `post_list` 不带 `api_version='2'` 返回图片列表；带上后返回 `{"posts": [...]}`。
  `include_tags='1'` 添加 `tags`，`include_votes='1'` 添加 `votes`，`include_pools='1'` 添加 `pool_posts` 和 `pools`；
  `tag_related` 返回对象 `{"touhou": [["标签名", 共现次数], …]}`；
  `favorite_list_users` 返回 `{"favorited_users": "名字1,名字2"}`（服务端把名字拼成了一个字符串）。

## 完整原生方法索引（90 个）

下面按资源列出 `anybooru/api_moebooru.py` 的每个方法：签名、关键参数与默认值、返回什么、要什么身份。
参数表、字面 URL 与可复制代码见[方法参考](moebooru-api.md)。

### 帖子（17）

- `post_list(**params)` — `tags`（站点标签语言，单帖用 `id:<编号>`）、`limit`（默认 40，上限 1000）、`page`、`filter='1'`、`api_version='2'`、`include_tags` / `include_votes` / `include_pools`；返回帖子数组（`id`、`tags`、`source`、`score`、`md5`、`file_url`、`preview_url`、`sample_url`、`jpeg_url`、`width`、`height`、`rating`、`status`、`parent_id`、`creator_id`、`is_held`），已删除的帖子没有那几个地址字段。匿名可查。
- `post_create(tags, *, file=None, source=None, md5=None, anonymous=None, **attributes)` — multipart 上传；`post[file]` 只在给了文件时发送；只给 `source='https://…'` 时服务端自己去下载；顶层 `md5` 是上传后的校验（不匹配会删帖并回 420）；`post[rating]`、`post[parent_id]`、`post[is_held]` 为附加属性；重复 md5 → 423，超出每日限额 → 421。需成员。
- `post_update(post_id, **attributes)` — 可改 `post[tags]`、`post[old_tags]`、`post[source]`、`post[parent_id]`、`post[rating]`、`post[is_held]`、`post[is_shown_in_index]`、`post[is_note_locked]`、`post[is_rating_locked]`、`post[frames_pending_string]`；**没有文件替换**；缺 `post[...]` 属性回 422 空正文。需登录（上传者或版主）。
- `post_destroy(post_id, reason=None, *, destroy=None)` — `destroy='1'` 是从数据库永久删除（仅版主，否则 403）；普通删除要有权限（版主、帖子被 hold、或上传未满一天）。需登录。
- `post_revert_tags(post_id, history_id)` — `history_id` 是标签历史条目的 id，未知回 404；只回 `{"success": true}`，不带帖子数据。需登录。
- `post_vote(post_id, score=None)` — 不传 `score` 是读自己当前的投票 `{"success": true, "vote": 1}`；写入 `1` 好 / `2` 很好 / `3` 收藏、`0` 清除；非版主负分或大于 3 → 424，重复投票 → 423。需登录。
- `post_activate(post_ids)` — `post_ids` 必须是列表（发成重复的 `post_ids[]`），释出被 hold 的帖子；非版主只能释出自己的；回 `{"success": true, "count": N}`，传非列表得到空 204（客户端返回 `None`）。需成员。
- `post_acknowledge_new_deleted_posts()` — 无参数，标记“新删除帖”提示已读；匿名也能进，但不会更新任何用户状态。
- `post_update_batch(post)` — `post` 是 `{帖子编号: {属性: 值}}`，发成 `post[<编号>][属性]`；只有编号的条目表示只订阅回包；返回被触及帖子的批量数据。需登录。
- `post_moderate(ids, commit, reason=None, reason2=None)` — `ids` 是 `{帖子编号: 任意值}`、`commit='Approve'` 或 `'Delete'`；返回被处理帖子的批量数据。需 janitor。
- `post_flag(post_id, reason=None, *, unflag=None)` — 标记待删；`unflag='1'` 取消（本人或版主）；非 active 的帖子标记、非 flagged 的帖子取消都回 500；返回该帖的批量数据。需登录。
- `post_undelete(post_id)` — 恢复已删除的帖子，返回该帖与其父帖的批量数据。需 janitor。
- `post_similar(*, file=None, **params)` — `url=`、`id=`（对比帖，未知回 404）、`search_id=`、`services='local'`、`threshold`、`forcegray='1'`、`width`、`height`、`initial='1'`，或给已打开文件；返回 `{"success": true, "posts": […], "source": …, "search_id": …, "error": …}`，没有任何查询依据回 503。匿名。
- `post_popular_recent(**params)` — `period` 取 `'1w'` / `'1m'` / `'1y'`，其他值被服务端换成 `'1d'`；返回最多 40 条，按 `score` 降序。匿名。
- `post_popular_by_day(**params)` — `year` / `month` / `day`，缺省取当天，日期非法回 400 空正文；返回当天最多 40 条。匿名。
- `post_popular_by_week(**params)` — 同上，三个日期参数指该周内任意一天。匿名。
- `post_popular_by_month(**params)` — 同上，指该月内任意一天。匿名。

### 合集（10）

- `pool_list(**params)` — `query`（`order:name`、`limit:50`（上限 100）、`posts:1-10`）、`order`（`name` / `date` / `updated` / `id`）、`page`（每页 20）；返回 `id`、`name`、`created_at`、`updated_at`、`user_id`、`is_public`、`post_count`、`description`。匿名。
- `pool_show(pool_id, **params)` — 返回**一个合集对象**，帖子在它自己的 `posts` 数组里，每页 24 个（账号开了合集浏览模式时 1000）；编号不存在也会重定向到合集列表，最终可能读到列表。匿名。
- `pool_create(name, **attributes)` — 属性 `pool[description]`、`pool[is_public]`、`pool[is_active]`；只回 `{"success": true}`，**不回新编号**，要用 `pool_list` 再查。需登录。
- `pool_update(pool_id, **attributes)` — 同一组属性，`PUT` 没路由所以方法发 POST；不是合集所有者且合集不公开 → 403。需登录。
- `pool_destroy(pool_id)` — 回 `{"success": true}`，无更新权限 → 403。需登录。
- `pool_add_post(pool_id, post_id, sequence=None)` — `sequence` 省略即追加到末尾；回 `{"success": true}`（不带合集内容）；帖子已在合集里 → 423。需登录。
- `pool_remove_post(pool_id, post_id)` — 返回被移除帖子的批量数据，响应头带 `X-Post-Id`。需登录。
- `pool_copy(pool_id, name=None)` — 连帖子一起复制，`name` 省略时服务端追加 ` (copy)`；JSON 只有 `{"success": true}`，新编号只出现在 HTML 重定向里。需 contributor。
- `pool_import(pool_id, posts)` — `posts` 是 `{帖子编号: 顺序}`，按顺序升序加入；POST 恒重定向到合集页，跟过去读到的合集 JSON 不是写入确认。需登录。
- `pool_order(pool_id, sequences)` — `sequences` 是 `{合集内帖子记录编号: 顺序}`；同样恒重定向，读到的合集 JSON 不是写入确认。需登录。

### 笔记、历史、收藏、内联与站内信（11）

- `note_list(**params)` — `post_id` 限定单帖，`page` 是**帖子页**（不带 `post_id` 每页 16 个有笔记的帖子），返回铺平后的笔记数组，字段 `id`、`post_id`、`x`、`y`、`width`、`height`、`body`、`is_active`、`version`、`creator_id`；`limit` 不生效。匿名。
- `note_search(query, **params)` — `query` 必需（不给会落到 HTML 分支得 406），每页 25，返回匹配的笔记数组。匿名。
- `note_history(**params)` — 取值优先级 `id`（笔记编号）→ `post_id` → `user_id`；每页 25，按 `post_id` / `user_id` 过滤时 50；**不读 `limit`**；按版本倒序返回 `version`、`post_id`、`body`、坐标、`creator_id`、`created_at`。匿名。
- `note_revert(note_id, version)` — `version` 是笔记历史版本号；锁定帖回 422；成功回 `{"success": true}`。需登录。
- `note_update(note_id=None, **attributes)` — 传 `note_id` 是更新，不传是新建（新建必须给 `note[post_id]`）；可改 `note[x]`、`note[y]`、`note[width]`、`note[height]`、`note[body]`、`note[is_active]`；返回 `{"success": true, "new_id": …, "old_id": …, "formatted_body": …}`。需登录。
- `history_undo(change_ids, redo=None)` — `change_ids` 是**变更条目**的 id（发成逗号连接的 `id`），`redo='1'` 表示重做；跨多条历史且等级低于 privileged → 403；返回 `{"success": true, "successful": …, "failed": …, "errors": …}`。需登录。
- `favorite_list_users(post_id)` — 返回 `{"favorited_users": "名字1,名字2"}`（无人收藏是空串），帖子不存在回 404。匿名。
- `inline_list(**params)` — `page`，每页 20，返回 `id`、`description`、`user_id`、`images`。匿名。
- `inline_copy(inline_id)` — 复制自己的内联图组，回 `{"success": true}`，新编号只出现在重定向里。需登录。
- `inline_delete(inline_id)` — 删除自己的内联图组，不是本人（且非版主）→ 403。需登录。
- `dmail_mark_all_read()` — 站内信全部标记已读，回 `{"success": true}`；协议固定值 `commit='Yes'`。需登录。

### 画师（4）

- `artist_list(**params)` — `name`（子串匹配）、`url`、`order`（`name` 默认 / `date`）、`page`；每页 25，带 `name` / `url` 过滤时 50；**不读 `limit`**；返回 `id`、`name`、`alias_id`、`group_id`、`urls`（数组）。匿名。
- `artist_create(name, **attributes)` — 可填 `artist[alias_name]`、`artist[alias_names]`、`artist[member_names]`、`artist[urls]`、`artist[notes]`；`artist[alias]` 与 `artist[group]` **不是**允许字段；校验失败回 420。需成员。
- `artist_update(artist_id, **attributes)` — 同一组字段再加 `name`，`PUT` 没路由所以发 POST；回 `{"success": true}`。需成员。
- `artist_destroy(artist_id)` — 必须带协议值 `commit='Yes'` 才是删除并回 `{"success": true}`，否则重定向回列表且不删。需 privileged。

### 标签、别名与蕴含（12）

- `tag_list(**params)` — `name`（子串，带 `*` 直接当 SQL 模式）、`id`、`type`（0 通用 / 1 画师 / 3 版权 / 4 角色）、`after_id`、`order`（`name` 默认 / `date` / `count`）、`limit`（默认 50，`0` 返回全部）、`page`；返回 `id`、`name`、`count`、`type`、`ambiguous`。匿名。
- `tag_related(**params)` — `tags`（空白分隔，服务端会剥掉 `%`、`/`、`*` 并转小写）、`type`（站点 tag_types 的键）；返回对象 `{"查询标签": [["名称", 共现次数], …]}`，每组最多 25 项、没有 `limit`。匿名。
- `tag_update(name, **attributes)` — 只发 POST，键名是 `tag[name]`（顶层 `name` 不生效）；可改 `tag[tag_type]`、`tag[is_ambiguous]='1'`；未知标签回 404。需成员。
- `tag_autocomplete_name(term)` — 返回最多 20 个名字，按长度再按字母序。匿名。
- `tag_summary(**params)` — `version` 是上次拿到的版本号，未变化时回 `{"version": …, "unchanged": true}`，否则回带 `data` 的摘要。匿名。
- `tag_mass_edit(start, result)` — 全站把 `start` 改名成 `result`；只有站点开了异步任务的部署会同步回 `{"success": true}`，同步分支没有 JSON 响应；`start` 为空回 424。需 mod。
- `tag_alias_list(**params)` — `query`、`page`（每页 20）；`commit='Search Implications'` 会带上同一个 query 跳到蕴含列表；返回 `id`、`name`、`alias_id`、`pending`。匿名。
- `tag_alias_create(name, alias_name, reason=None)` — `name` 是别名本身、`alias_name` 是目标标签（线上字段是 `tag_alias[alias]`）；建出来的是待审记录，随后重定向到别名列表。需成员。
- `tag_alias_update(aliases, commit, reason=None)` — `aliases` 是 `{别名编号: 任意值}`，`commit='Approve'` 或 `'Delete'`（其他值回 400）；`Delete` 重定向到列表，`Approve` 重定向到只有 HTML 的任务页，可能拿到 500 或非 JSON，不要盲目重试。需 mod（删除时待审记录的创建者也可以）。
- `tag_implication_list(**params)` — `query`、`page`（每页 20）；返回 `id`、`consequent_id`、`predicate_id`、`pending`。匿名。
- `tag_implication_create(predicate, consequent, reason=None)` — 申请“predicate 蕴含 consequent”，建的是待审记录，随后重定向到蕴含列表。需成员。
- `tag_implication_update(implications, commit, reason=None)` — 语义与返回同别名审批，`implications` 是 `{蕴含编号: 任意值}`。需 mod。

### 评论（7）

- `comment_list(**params)` — `post_id`（**必须带**，不带就等于查 0 号帖，返回空数组）、`page`（每页 25，`limit` 不读）；返回 `id`、`created_at`、`post_id`、`creator`、`creator_id`、`body`。匿名。
- `comment_search(query, **params)` — `query` 支持 `user:<名字>`，`query=''` 时不启用全文过滤、可当评论流；每页 30；空数组是正常结果。匿名。
- `comment_show(comment_id)` — 返回单条评论，字段同列表；不存在的编号回 404 HTML 页（`AnybooruHTTPError.data` 为 `None`）。匿名。
- `comment_create(post_id, body)` — 发 `comment[post_id]` 与 `comment[body]`；`comment[anonymous]` 不是允许字段；小时限额回 421、校验失败回 420。需登录。
- `comment_update(comment_id, **attributes)` — 改 `comment[body]`、`comment[post_id]`；无权回 403。需登录（本人或版主）。
- `comment_destroy(comment_id)` — 回 `{"success": true}`；无权回 403。需登录（本人或版主）。
- `comment_mark_as_spam(comment_id)` — 标记垃圾并回 `{"success": true}`；该路由没有登录过滤器，匿名也能进，但它**不是只读接口**。

### Wiki（9）

- `wiki_list(**params)` — `query`（普通词走全文检索，`title:` 前缀改成标题匹配）、`order`（`title` 默认 / `date`）、`limit`（默认 25）、`page`；返回 `id`、`created_at`、`updated_at`、`title`、`body`、`updater_id`、`locked`、`version`。匿名。
- `wiki_history(title=None, **params)` — `title` 或 `id` 指定页面；按版本倒序返回该页面的**全部**版本，不分页。匿名。
- `wiki_recent_changes(**params)` — `user_id`、`per_page`（默认 25）、`page`。匿名。
- `wiki_create(title, body)` — 发 `wiki_page[title]`、`wiki_page[body]`；返回 `{"success": true, "location": …}`，校验失败回 420。需成员。
- `wiki_update(title, *, new_title=None, **attributes)` — 顶层 `title` 选中页面，`new_title` 写进 `wiki_page[title]`、`body` 写进 `wiki_page[body]`；必须至少给一个 `wiki_page[...]` 属性否则 400；锁定页回 422。需成员。
- `wiki_destroy(title)` — 删除页面，回 `{"success": true}`。需 mod。
- `wiki_lock(title)` / `wiki_unlock(title)` — 锁定/解锁，回 `{"success": true}`；不存在的标题在 lock / unlock 上回 500。需 mod。
- `wiki_revert(title, version)` — 回滚到某个历史版本号，锁定页回 422。需登录。

### 论坛（11）

- `forum_list(**params)` — `parent_id` 看某个主题的回复（每页 100）、`latest='1'` 取第一页 10 条、`page`（主题每页 30）；返回 `id`、`parent_id`、`title`、`body`、`creator`、`creator_id`、`updated_at`、`pages`。匿名。
- `forum_show(forum_id, **params)` — 返回单个论坛帖对象，字段与列表相同。匿名。
- `forum_search(query, **params)` — `query`、`page`，每页 30，返回匹配的论坛帖数组。匿名。
- `forum_create(title, body, **attributes)` — `forum_post[title]`、`forum_post[body]`；`parent_id` 为 `0` 或省略是发新主题，否则是回复；随后重定向到主题页。需登录。
- `forum_update(forum_id, **attributes)` — 改 `title` / `body` / `parent_id`；无权回 403，随后重定向回主题，读到的 JSON 不是写入确认。需登录（创建者或版主）。
- `forum_destroy(forum_id)` — 删除帖子或主题，重定向到主题或论坛索引，读到的是重定向后的页面 JSON。需登录（创建者或版主）。
- `forum_lock(forum_id)` / `forum_unlock(forum_id)` / `forum_stick(forum_id)` / `forum_unstick(forum_id)` — 主题管理，结果同样只体现在重定向后的主题页 JSON；`forum_lock` 的编号在请求体里。需 mod。
- `forum_mark_all_read()` — 全部标记已读，服务端回空 `204`，客户端返回 `None`。需登录。

### 账号（9）

- `user_list(**params)` — `name`（子串）、`level`、`id`、`order`、`page`（每页 20）；每行只有 `{"name": …, "id": …}`。匿名。
- `user_autocomplete_name(term)` — 返回名字数组（最多 20 个，关键词短于 2 个字符回空数组）。匿名。
- `user_check(username, password)` — 独立端点，按协议**明文**发送 `username` + `password`（不是配置里的密码哈希）；返回 `{"response": "success" | "unknown-user" | "wrong-password", …}`。未实测。
- `user_create(name, password, password_confirmation, **attributes)` — 注册；**失败也是 200**：返回 `{"response": "success" | "error", "errors": […]}`；其余 `user[...]` 设置与 `user_update` 同组。未实测。
- `user_update(**attributes)` — 改 `email`、`password`、`current_password`、`blacklisted_tags`、`always_resize_images`、`receive_dmails`、`show_samples`、`use_browser`、`show_advanced_editing`、`pool_browse_mode`；**不接受 `name`**；校验失败回 420。需登录。
- `user_authenticate(**params)` — `url` 是回跳路径，回 `{"success": true}`。需登录。
- `user_modify_blacklist(add=None, remove=None)` — 列表发成重复键 `add[]` / `remove[]`；返回 `{"success": true, "result": […]}`。需登录。
- `user_reset_password(name, email)` — 请求重置邮件，成功回 `{"result": "success"}`；账号不存在 / 没有邮箱 / 邮箱不符分别回 `unknown-user` / `no-email` / `wrong-email`（500），SMTP 拒收是 `invalid-email`。未实测。
- `user_record_destroy(user_record_id)` — 删除用户记录，无权回 403。需 privileged（且版主或该记录的提交者）。

## 找不到原生方法时

**90 个方法只覆盖有 JSON 的端点**：浏览页面、JS 交互、Atom/RSS 订阅源和合集 ZIP 都被有意排除
（它们在站点上都有真实路由，只是没有 JSON）。完整清单与原因见[契约审计附注](moebooru-contract-notes.md)；
需要时直接用通用入口，参数写法与原生方法一致：

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    posts = client.request('GET', 'post/popular_recent', params={'period': '1w'})
    # GET https://yande.re/post/popular_recent.json?period=1w -> 最多 40 个帖子字典，按 score 降序
    print(len(posts), posts[0]['id'], posts[0]['score'])
```

`request()` 不会把 HTML 变成 JSON，也不会替你判断重定向后的结果是不是写入成功。
连接生命周期用 `client.close()` 或 `with Moebooru(...) as client:` 管理，这两个不算 API 方法。

## 边界与未实测汇总

- 本页不新增线上探测：匿名只读端点在 `yande.re` 上的逐条执行记录见 [verification.md](verification.md)。
- **全部写接口与账号动作只做源码对齐，没有线上实测**；`user_check` / `user_create` / `user_reset_password`
  没有可用凭据，只保证请求形态与源码一致。
- 未指名执行过的读接口（相似图、其余热门查询、补全、标签摘要、别名与蕴含列表、论坛详情与搜索等）
  同样只是源码对齐。
- 方法存在不等于目标站点启用了该能力：相似图服务、异步任务后端、站点自己关掉的功能都可能缺失，
  由服务端决定结果；本库不加兜底、不伪造替代响应。逐条状态见[契约审计附注](moebooru-contract-notes.md)。

继续阅读：[客户端用法](moebooru.md) · [方法参考](moebooru-api.md) ·
[契约审计附注](moebooru-contract-notes.md) · [翻页方式](pagination.md)。
