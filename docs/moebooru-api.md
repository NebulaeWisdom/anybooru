# Moebooru 方法参考

`Moebooru` 客户端共 **90 个原生方法**，每个都是 `Moebooru.request()` 的薄封装，对应 Moebooru 引擎
（只读参考 `moebooru/` HEAD `206455e1`）确实提供 JSON 的端点。本页按资源分组：每组先给 2–4 个
**常用**方法的实际签名、可复制片段与返回要点，其余方法以「签名 — 何时用；返回什么」一行式列出，
不再重复代码块。逐条权限、上游坐标、排除项与源码对齐/已实测状态在
[契约审计附注](moebooru-contract-notes.md)。

## 共享前置

下文的 `c` 都是这个已按配置构造好的客户端（站点名与其余输入取自 `sites` / `examples.moebooru` 段；
那份清单是样例，不是支持边界，任何跑 Moebooru 引擎的站点都可以 `site_url=` + `api_version=` 直接接入）：

```python
from anybooru import Moebooru

c = Moebooru('yandere')
```

片段里的 `post_id` / `pool_id` / `comment_id` / `note_id` / `artist_id` / `title` 等是**从读响应里取到的值**
（例如 `post_id = posts[0]['id']`、`title = pages[0]['title']`），本页不预设任何额外的配置键。

通用入口（没有原生方法的端点直接用它）：`request(method, path, *, params=None, data=None, files=None)`

* `path` 是相对路径，带不带 `.json` 都可以（`'post'` 与 `'post.json'` 等价）；路径里的 id 由调用者转义。
* `params` 是查询串；`data` 是 **Rails 表单**（Moebooru 面没有 JSON 请求体）：嵌套 dict → `a[b]`，列表 → 重复键 `a[]`，布尔 → `true`/`false`，`None` 不发送；`files` 非空时请求体改为 multipart。
* 认证：配置了凭据时 `GET`/`HEAD` 把 `login` + `password_hash` 放进查询串，其他动词放进表单体；两项凭据都为空才是匿名。
* 不做隐式兜底：不自动重试、不自动翻页、不做本地分页上限、不预判权限；传入的文件对象由调用者关闭。

**参数分层**：读方法的过滤与分页（`tags`、`query`、`name`、`limit`、`page`…）都是**顶层参数**，没有 Danbooru 的 `search[...]` 字典；写方法是「语义必需字段显式 + 其余属性按模型名嵌套」，键名就是 `post[...]`、`pool[...]`、`note[...]`、`tag[...]`、`tag_alias[...]`、`wiki_page[...]`、`comment[...]`、`forum_post[...]`、`artist[...]`、`user[...]`。引擎按字符串比较的开关要传**字面值**，不要传 Python 布尔：`unflag='1'`、`redo='1'`、`forcegray='1'`、`anonymous='1'`、`filter='1'`、`commit='Yes' | 'Approve' | 'Delete' | 'Post'`、`api_version='2'`。

### 两个 `api_version` 不要混

| 位置 | 作用 |
| :--- | :--- |
| 构造参数 / 站点条目的 `api_version` | 选择**列表路径形态**：`1.13.0` / `1.13.0+update.1` / `1.13.0+update.2` 时裸集合路径补成 `/index`；现役站点自述 `1.13.0+update.3`，走的是非 `/index` 形态 |
| `post_list` 的查询参数 `api_version='2'` | 选择**响应信封**：不带是顶层数组，带 `'2'` 是 `{posts, pool_posts, pools, tags, votes}` |

### 返回值

| 服务端响应 | 客户端拿到 |
| :--- | :--- |
| JSON 响应体 | 解析后的 Python 对象，原样返回，不改字段、不包装（列表是数组，详情是单个对象） |
| `204` 或空响应体 | `None`（`forum_mark_all_read`） |
| HTTP 错误状态 | `AnybooruHTTPError`，带 `http_code` / `url` / `body` / `data`；`.data` 只在正文本身是 JSON 时有值 |
| 2xx 但正文不是 JSON | `AnybooruAPIError` |
| 网络层错误 | 原样抛出 requests 的异常 |

排查「参数到底发成了什么样」看 `c.last_call['url']`（`last_call` 只表示最近一次请求）。
异常类型见 [errors.md](errors.md)。各族的具体形态见文末[响应形态](#响应形态)。

## 帖子（17）

读是 `post_list(**params)`，写是「必需字段显式 + `post[...]` 属性」；**没有 `post_show`**。

```python
posts = c.post_list(tags='rating:s', page=1, limit=3)
print(posts[0]['id'], posts[0]['file_url'])
```

`post_list(**params)` 返回**顶层数组**，每项含 `id / tags / source / score / md5 / file_url / preview_url / sample_url / jpeg_url / width / height / rating / status / parent_id / creator_id / is_held / last_noted_at` 等；已删除的帖子不带 `file_url` / `sample_url` / `jpeg_url`。
单帖用 `tags='id:<id>'`（md5 用 `tags='md5:<hash>'`），空数组表示不存在或当前身份不可见；带 `api_version='2'` 才切到信封；`limit` 默认 40、上限 1000。

```python
with open('image.jpg', 'rb') as upload_file:
    c.post_create('1girl rating:s', file=upload_file, source='https://example.org/1.jpg')
```

`post_create(tags, *, file=None, source=None, md5=None, anonymous=None, **attributes)` 需要登录；也可以**只给来源 URL**（不带文件时服务端自己下载）。顶层 `md5=` 是上传后校验，不匹配会销毁帖子并回 420；重复 md5 → 423；超出每日上传限额 → 421；`is_rating_locked` / `is_note_locked` 在创建接口不生效。返回 `{success: true, post: {...}, tags: {...}}`。

```python
c.post_update(post_id, tags='1girl solo rating:s', source='https://example.org/1.jpg')
c.post_vote(post_id, score=1)          # 1 好 / 2 很好 / 3 收藏；0 清除
c.post_vote(post_id)                   # 不传 score 只读当前投票 → {'success': True, 'vote': 1}
```

`post_update(post_id, **attributes)` **不能替换文件**（本方法没有文件参数），允许属性是 `tags` / `old_tags` / `source` / `parent_id` / `rating` / `is_held` / `is_shown_in_index` / `is_note_locked` / `is_rating_locked` / `frames_pending_string`；缺少任何 `post[...]` 属性 → 422 空正文，非版主改已删除帖 → 422 `Post Locked`。
`post_vote(post_id, score=None)` 写入时返回被触及帖子的批量负载（见[响应形态](#响应形态)），重复投票 → 423。

其余方法（按需查上面的参数分层与返回形态即可）：

- `post_destroy(post_id, reason=None, *, destroy=None)` — 按理由删除；已标记删除的帖子要 `destroy='1'` 才是永久删除（版主，否则 403）；返回 `{success: true}`。
- `post_revert_tags(post_id, history_id)` — 把帖子标签回滚到某条标签历史；`history_id` 是该次标签改动的 id；返回 `{success: true}`，不带帖子数据。
- `post_activate(post_ids)` — 释出被 hold 的帖子；`post_ids` 必须是列表，非版主只能释出自己的；返回 `{success: true, count: N}`（传非数组得到空 204 → `None`）。
- `post_acknowledge_new_deleted_posts()` — 标记「新删除帖」提示已读；返回 `{success: true}`，匿名调用不会更新任何用户状态。
- `post_update_batch(post)` — 一次改多个：`{post_id: {'tags': ..., 'rating': ...}}`，只带 id 的条目表示只订阅回包；返回被触及帖子的批量负载 `{posts, pool_posts, pools, tags, votes}`。
- `post_moderate(ids, commit, reason=None, reason2=None)` — 批量 `'Approve'` / `'Delete'`（janitor+），`ids` 是 `{post_id: 任意值}` 映射；返回被处理帖子（含父帖）的批量负载 `{posts, pool_posts, pools, tags, votes}`。
- `post_flag(post_id, reason=None, *, unflag=None)` — 标记待删，`unflag='1'` 取消自己（或版主）的标记；返回该帖的批量负载 `{posts, pool_posts, pools, tags, votes}`；非 active 的帖子标记、非 flagged 的帖子取消都回 500。
- `post_undelete(post_id)` — 恢复已删除的帖子（janitor+）；返回该帖及其父帖的批量负载 `{posts, pool_posts, pools, tags, votes}`。
- `post_similar(*, file=None, **params)` — 以图搜图：`url=`、`id=`（对比帖）、`search_id=` 或已打开文件，另有 `services`（默认 `'local'`）/ `threshold` / `forcegray='1'` / `width` / `height` / `initial='1'`；返回 `{success: true, posts, source, search_id, error}`，没有查询依据 → 503。
- `post_popular_recent(**params)` — `period` 取 `'1w'` / `'1m'` / `'1y'`（其他值被服务端强制成 `'1d'`）；返回最多 40 个帖子对象，按 `score` 降序。
- `post_popular_by_day(**params)` — 看某日热门：`year` / `month` / `day`（缺省取当天，非法日期 → 400 空正文）；返回当天最多 40 个帖子对象。
- `post_popular_by_week(**params)` — 看某周热门：`year` / `month` / `day` 指该周内任意一天；返回该周最多 40 个帖子对象。
- `post_popular_by_month(**params)` — 看某月热门：`year` / `month` / `day` 指该月内任意一天；返回该月最多 40 个帖子对象。

## 合集（10）

合集的所有写路由都同时挂着 GET，但 **GET 只是渲染表单页，写入必须 POST**——下面的方法已经发 POST。

```python
pools = c.pool_list(query='order:name', page=1)
print(pools[0]['id'], pools[0]['name'], pools[0]['post_count'])
```

`pool_list(**params)` 返回**顶层数组**，每项 `id / name / created_at / updated_at / user_id / is_public / post_count / description`；每页 20，`query` 里的 `limit:N` 上限 100，`order` 取 `name` / `date` / `updated` / `id`。

```python
pool = c.pool_show(pool_id)            # 单个合集对象，帖子在 pool['posts'] 里
print(pool['name'], [post['id'] for post in pool['posts']])
```

`pool_show(pool_id, **params)` **不返回数组**：返回一个合集对象，每页 24 个帖子（账号启用合集浏览模式时 1000）。未知 id 会重定向到合集列表，最终可能读到一个列表。

```python
c.pool_add_post(pool_id, post_id, sequence=1)   # sequence 省略即追加到末尾
```

`pool_add_post(pool_id, post_id, sequence=None)` 返回 `{success: true}`（不带合集内容）；帖子已在合集 → 423。

- `pool_create(name, **attributes)` — 新建合集（`description` / `is_public` / `is_active`）；返回 `{success: true}`，**不回传新 id**，要用 `pool_list` 再查。
- `pool_update(pool_id, **attributes)` — 改名、描述与公开/启用状态（同一组属性）；返回 `{success: true}`，不是所有者且合集非公开 → 403。
- `pool_destroy(pool_id)` — 删除合集；返回 `{success: true}`，无更新权限 → 403。
- `pool_remove_post(pool_id, post_id)` — 移除帖子；返回被移除帖子的批量负载 `{posts, pool_posts, pools, tags, votes}`，响应头带 `X-Post-Id`。
- `pool_copy(pool_id, name=None)` — 连帖子一起复制（contributor+），`name` 省略时服务端追加 ` (copy)`；JSON 只有 `{success: true}`，新 id 只在 HTML 重定向里。
- `pool_import(pool_id, posts)` — `{post_id: sequence}` 按 sequence 升序批量加入；POST 恒重定向到合集页，读到的合集 JSON 不是写入确认。
- `pool_order(pool_id, sequences)` — `{pool_post_id: sequence}` 重排；同样恒重定向到合集页，读到合集 JSON。

## 笔记、历史、收藏、内联与站内信（11）

```python
notes = c.note_list(post_id=post_id)
print(notes[0]['x'], notes[0]['y'], notes[0]['body'])
```

`note_list(**params)` 返回**扁平数组**，每项 `id / post_id / x / y / width / height / body / is_active / version / creator_id / created_at / updated_at`。**分页单位是帖子**：不带 `post_id` 时服务端先按帖子分页（每页 16 个「有笔记的帖子」），再展平这些帖子的全部笔记，所以不是「每页 16 条笔记」，`limit` 也不生效。

```python
c.note_history(post_id=post_id)        # 也可用 id=<笔记 id>、user_id=<作者>
```

`note_history(**params)` 返回版本数组（`version / post_id / body / x / y / width / height / is_active / creator_id / created_at` …），**按版本倒序**；每页 25，按 `post_id` / `user_id` 过滤时 50；`limit` 被忽略，翻页仍用 `page`。

```python
c.note_update(post_id=post_id, x=10, y=10, width=100, height=100, body='译注')
c.note_update(note_id, body='改过的正文')       # 传 note_id 就是更新
```

`note_update(note_id=None, **attributes)` 返回 `{success: true, new_id, old_id, formatted_body}`；不传 `note_id` 是**新建**且必须给 `note[post_id]`；锁定帖 → 422。

- `note_search(query, **params)` — 全文搜索正文，每页 25；**`query` 必需**，不给会落到 HTML 分支得到 406；返回匹配的笔记数组。
- `note_revert(note_id, version)` — 回滚笔记，`version` 是笔记的历史版本号；返回 `{success: true}`，锁定帖 → 422。
- `history_undo(change_ids, redo=None)` — 撤销/重做一批历史变更；`change_ids` 要传**变更条目的 id**（不是历史批次的 id，发送时逗号连接），`redo='1'` 表示重做；返回 `{success: true, successful, failed, errors}`。
- `favorite_list_users(post_id)` — 收藏者名单：返回原始对象 `{'favorited_users': 'name1,name2'}`（服务端拼成一个字符串，无人收藏是空串）；帖子不存在 → 404。
- `inline_list(**params)` — 内联图组列表，每页 20；返回数组，每项 `id / description / user_id / images`。
- `inline_copy(inline_id)` — 复制自己的内联图组；返回 `{success: true}`，新组 id 只在 HTML 重定向里。
- `inline_delete(inline_id)` — 删除自己的内联图组；返回 `{success: true}`，不是本人（且非版主）→ 403。
- `dmail_mark_all_read()` — 站内信全部标记已读；返回 `{success: true}`。

## 画师（4）

```python
artists = c.artist_list(name='fuzichoco')      # 也可 url='https://...'；name 是子串匹配
print(artists[0]['id'], artists[0]['name'], artists[0]['urls'])
```

`artist_list(**params)` 返回 `id / name / alias_id / group_id / urls`（`urls` 是数组）；每页 25，按 `name` / `url` 过滤时 50，**`limit` 被忽略**。`name` 不是精确相等（子串命中即可）。

```python
c.artist_update(artist_id, urls='https://www.pixiv.net/users/27517', notes='备注')
```

`artist_update(artist_id, **attributes)` 需要登录；允许 `name / alias_name / alias_names / member_names / urls / notes`，返回 `{success: true}`。

- `artist_create(name, **attributes)` — 新建画师，允许字段同上（`name` 已在签名里，`alias` / `group` 不是允许键）；返回 `{success: true}`，校验失败 → 420。
- `artist_destroy(artist_id)` — 删除画师（privileged+）；只有协议要求的 `commit='Yes'` 才返回 `{success: true}`，缺了会重定向回索引而不删除。

## 标签、别名与蕴含（12）

```python
tags = c.tag_list(name='touhou', limit=3, order='count')
print([(tag['name'], tag['count']) for tag in tags])
```

`tag_list(**params)` 返回 `id / name / count / type / ambiguous`；`name` 子串匹配（`*` 会变成原始 SQL 模式），`order` 取 `name` / `date` / `count`，默认每页 50，`limit=0` 返回**全部**标签（站点很大时很重）。

```python
related = c.tag_related(tags='touhou', type='general')
for name, count in related['touhou'][:3]:
    print(name, count)
```

`tag_related(**params)` 返回**对象** `{查询标签: [[名称, 共现次数], ...]}`，每组最多 25 项，**没有 `limit`**；`type` 必须是站点 `tag_types` 里的键；请求里的 `%`、`/`、`*` 会被剥掉并转小写。

```python
c.tag_update('tag_name', tag_type=1, is_ambiguous='1')
```

`tag_update(name, **attributes)` 发 POST，且键名是 `tag[name]`（顶层的 `name` 不会生效，`PUT` 未路由）；返回 `{success: true}`，未知标签 → 404。

- `tag_autocomplete_name(term)` — 名字补全；返回最多 20 个名字的数组（按长度再按字母序）。
- `tag_summary(**params)` — 标签缓存摘要；返回 `{version, data}`，带上次拿到的 `version` 且未变化时是 `{version, unchanged: True}`。
- `tag_mass_edit(start, result)` — 全站把 `start` 改名成 `result`（mod+）；开启异步任务的站点同步返回 `{success: true}`，同步分支没有 JSON 响应；`start` 为空 → 424。
- `tag_alias_list(**params)` — 别名列表（`query` / `page`，每页 20）；返回数组，每项 `id / name / alias_id / pending`。
- `tag_alias_create(name, alias_name, reason=None)` — 申请别名：`name` 是别名本身、`alias_name` 是目标标签；创建的是待审记录，随后重定向到别名列表，读到的列表 JSON 不是写入确认。
- `tag_alias_update(aliases, commit, reason=None)` — 审批或删除别名：`aliases` 是 `{别名 id: 任意值}`，`commit='Approve'` / `'Delete'`（其他值 → 400）；`'Delete'` 重定向到别名列表，`'Approve'` 见下方注意。
- `tag_implication_list(**params)` — 蕴含列表；返回数组，每项 `id / predicate_id / consequent_id / pending`。
- `tag_implication_create(predicate, consequent, reason=None)` — 申请蕴含（`predicate` 蕴含 `consequent`）；建的是待审记录，随后重定向到蕴含列表。
- `tag_implication_update(implications, commit, reason=None)` — 审批或删除蕴含：`implications` 是 `{蕴含 id: 任意值}`，语义与返回同别名审批。

`Approve` 分支重定向到 HTML-only 的任务页：**即使审批任务已经建好，也可能拿到 500 或非 JSON 响应**，不要据此盲目重试——写完后用 `tag_alias_list` / `tag_implication_list` 自己确认。

## 评论（7）

```python
comments = c.comment_list(post_id=post_id)
print([comment['creator'] for comment in comments])
```

`comment_list(**params)` 返回 `id / created_at / post_id / creator / creator_id / body`。**必须带 `post_id`**：不带时查询恒为 `post_id=0` 并返回空数组——它不是全站最新评论；每页 25，`limit` 被忽略。

```python
recent = c.comment_search(query='', page=1)     # 空 query 不启用全文过滤，可当评论流用
c.comment_search(query='user:touhou_fan')       # 按作者过滤
```

`comment_search(query, **params)` 每页 30，返回评论数组；**空列表是正常结果**，不是失败。

```python
c.comment_create(post_id, '来评论一句')
```

`comment_create(post_id, body)` 需要登录；返回 `{success: true}`；小时限额 → 421，校验失败 → 420；`comment[anonymous]` 不是允许字段。

- `comment_show(comment_id)` — 读一条评论，字段与列表相同；不存在的 id 回 404 HTML 页（`.data` 为 `None`）。
- `comment_update(comment_id, **attributes)` — 改 `body`（本人或版主）；返回 `{success: true}`，无权 → 403。
- `comment_destroy(comment_id)` — 删除（本人或版主）；返回 `{success: true}`，无权 → 403。
- `comment_mark_as_spam(comment_id)` — 标记为垃圾并返回 `{success: true}`；该路由没有登录过滤器，匿名也能进，但它**不是只读接口**。

## Wiki（9）

```python
pages = c.wiki_list(query='touhou', limit=3)
print(pages[0]['title'], pages[0]['version'])
```

`wiki_list(**params)` 返回 `id / title / body / updater_id / locked / version / created_at / updated_at`；`limit` 生效（默认 25），`order` 取 `title`（默认）或 `date`。**没有 `wiki_show`**：`wiki/show` 只渲染 HTML，要正文用 `wiki_list(query='title:<标题>')`。

```python
c.wiki_history(title='alphes')        # 也可 id=<页面 id>
```

`wiki_history(title=None, **params)` 返回该页面的全部版本，**按版本倒序、不分页**（`title` 或 `id` 指定页面）。更宽的范围用 `wiki_recent_changes`。

```python
c.wiki_update('old_title', new_title='new_title')
c.wiki_update('title', body='新正文')
```

`wiki_update(title, *, new_title=None, **attributes)` 的顶层 `title` 用来**选中页面**，`new_title` 才是写出 `wiki_page[title]` 的那一个——两个同名参数已经拆开，可以同时传。返回 `{success: true}`；必须至少给一个 `wiki_page[...]` 属性，否则 400；锁定页 → 422。

- `wiki_recent_changes(**params)` — 最近的 wiki 改动：`user_id` / `per_page`（默认 25）/ `page`；返回改动数组。
- `wiki_create(title, body)` — 新建页面；返回 `{success: true, location}`，校验失败 → 420。
- `wiki_destroy(title)` / `wiki_lock(title)` / `wiki_unlock(title)` — 删除 / 锁定 / 解锁（mod+）；返回 `{success: true}`，不存在的标题在 lock / unlock 上会 500。
- `wiki_revert(title, version)` — 回滚到某个历史版本号；返回 `{success: true}`，锁定页 → 422。

## 论坛（11）

```python
topics = c.forum_list(page=1)          # 主题每页 30
print(topics[0]['id'], topics[0]['title'], topics[0]['pages'])
```

`forum_list(**params)` 返回 `id / parent_id / title / body / creator / creator_id / updated_at / pages`；`parent_id=` 看某个主题的回复（每页 100），`latest='1'` 固定第一页 10 条。

```python
c.forum_create('主题标题', '正文', parent_id=0)    # parent_id 为 0 或省略 = 新主题，否则是回复
```

`forum_create(title, body, **attributes)` 需要登录；写动作会重定向到主题页，客户端跟随后的结果**不是写入确认**。

- `forum_show(forum_id, **params)` — 读一个论坛帖，字段与列表相同。
- `forum_search(query, **params)` — 全文搜索，每页 30；返回匹配的论坛帖数组。
- `forum_update(forum_id, **attributes)` — 改 `title` / `body` / `parent_id`（创建者或版主）；重定向回主题，读到的主题 JSON 不是写入确认，无权 → 403。
- `forum_destroy(forum_id)` — 删除帖子或主题（创建者或版主）；重定向到主题或论坛索引；返回的是重定向后的页面 JSON，不是删除确认。
- `forum_lock(forum_id)` / `forum_unlock(forum_id)` / `forum_stick(forum_id)` / `forum_unstick(forum_id)` — 主题管理（mod+）；结果同样只体现在重定向后的主题页 JSON。
- `forum_mark_all_read()` — 全部标记已读；`204` 空响应，客户端返回 `None`。

## 账号（9）

```python
users = c.user_list(name='admin')       # 每页 20
print([user['name'] for user in users])
```

`user_list(**params)` 返回的**每一行只有 `{name, id}`**，不是完整用户对象。

```python
c.user_update(show_samples='1', receive_dmails='0')
```

`user_update(**attributes)` 需登录；**不接受 `name`**，改密码或邮箱要带 `current_password`；返回 `{success: true}`。两个方法共用的 `user[...]` 设置是 `email` / `blacklisted_tags` / `always_resize_images` / `receive_dmails` / `show_samples` / `use_browser` / `show_advanced_editing` / `pool_browse_mode`，注册时另有 `password` / `password_confirmation`（已在签名里）。

- `user_autocomplete_name(term)` — 名字补全；返回名字数组（最多 20 个，关键词短于 2 个字符返回空数组）。
- `user_check(username, password)` — 独立端点，按协议**明文**发送 `username` + `password`（不是配置里的密码哈希）；返回 `{response, exists, name, id, no_email, pass_hash, user_info}`，`response` 为 `'success'` / `'unknown-user'` / `'wrong-password'`。
- `user_create(name, password, password_confirmation, **attributes)` — 注册；**失败也是 200**：返回 `{response: 'success' | 'error', errors: [...]}`，其余 `user[...]` 设置与 `user_update` 同组。
- `user_authenticate(**params)` — 重新认证当前会话（`url=` 是回跳路径）；返回 `{success: true}`。
- `user_modify_blacklist(add=None, remove=None)` — 增删自己的标签黑名单（列表发成 `add[]` / `remove[]`）；返回 `{success: true, result: [...]}`。
- `user_reset_password(name, email)` — 请求重置邮件；返回 `{result: 'success'}`；账号不存在 / 没有邮箱 / 邮箱不符分别是 `'unknown-user'` / `'no-email'` / `'wrong-email'`（500），SMTP 拒收是 `'invalid-email'`。
- `user_record_destroy(user_record_id)` — 删除用户记录（privileged+，且需版主或该记录提交者）；返回 `{success: true}`，无权 → 403。

## 分页与实际上限

页码从 1 开始，服务端把 `page` 夹在 `1..1000000`。**每页大小由服务端写死**，下表是它的真实行为，
不是客户端的限制：

| 端点 | 每页 / 上限 |
| :--- | :--- |
| `post_list` | 默认 40（`limit:` 元标签可覆盖）；超过 1000 一律夹到 1000 |
| `pool_list` | 每页 20；`query` 里的 `limit:N` 夹到 ≤100 |
| `pool_show` | 每页 24 个帖子（账号启用合集浏览模式时 1000） |
| `note_list` | 先按帖子分页（带 `post_id` 每页 100 个帖子，否则 16 个），再展平这些帖子的全部笔记 |
| `note_history` | 25；按 `post_id` / `user_id` 时 50；`limit` 被忽略 |
| `note_search` | 25 |
| `comment_list` | 25；`limit` 被忽略 |
| `comment_search` | 30 |
| `forum_list` | 带 `parent_id` 时 100，否则 30；`latest` 固定第一页 10 条 |
| `wiki_list` | `limit` 生效，默认 25 |
| `wiki_recent_changes` | `per_page` 生效，默认 25 |
| `artist_list` | 带 `name` / `url` 时 50，否则 25；`limit` 被忽略 |
| `tag_list` | 默认 50；`limit=0` 返回全部 |
| `tag_related` | 没有 `limit`，每组上限 25 |
| `tag_autocomplete_name` / `user_autocomplete_name` | 上限 20 |
| `tag_alias_list` / `tag_implication_list` / `inline_list` / `user_list` | 20 |
| `post_popular_recent` / `_by_day` / `_by_week` / `_by_month` | 最多 40 条，按 `score` 降序 |

## 响应形态

| 服务端动作 | 客户端拿到 |
| :--- | :--- |
| 列表 | 顶层数组（`tag_related`、`favorite_list_users` 除外，见下） |
| 写成功 | `{success: true}`，部分带额外键：`count`（`post_activate`）、`vote`（`post_vote` 读）、`new_id` / `old_id` / `formatted_body`（`note_update`）、`location`（`wiki_create`）、`result`（黑名单、密码重置） |
| 批量写 | 被触及帖子的批量负载 `{posts, pool_posts, pools, tags, votes}`（`post_update_batch`、`post_moderate`、`post_vote`、`post_flag`、`pool_remove_post`、`post_undelete`） |
| 跟随重定向 | 目标页的 JSON：可能是数组（别名 / 蕴含 / 论坛索引）或单个对象（合集、主题） |
| `204` | `None` |
| 原始对象 | `favorite_list_users` → `{'favorited_users': 'name1,name2'}`；`tag_related` → `{标签: [[名称, 计数], ...]}` |
| 错误 | `AnybooruHTTPError`；正文不是 JSON 时 `.data` 为 `None`，原文在 `.body` |

## 边界与未实测汇总

* 本页全部条目按上游源码对齐。**写动作与账号动作没有线上实测**；匿名只读的真实执行范围和逐条命令见
  [verification.md](verification.md)，逐条状态与上游坐标见 [契约审计附注](moebooru-contract-notes.md)。
* 只提供有 JSON 契约的端点：HTML / JS 页面、Atom/RSS 订阅源与合集 ZIP 都没有包装方法，
  它们仍然有真实路由。其中 `help/api` 特殊——本库固定发 `Accept: application/json`，而该页只有 HTML
  模板，所以 `request('GET', 'help/api')` 得到 404（`yande.re` 是它的 HTML 404 页，`konachan.com` /
  `sakugabooru.com` 是空正文），换 `Accept: text/html` 就是 200。完整排除项见附注。
* 方法存在 ≠ 目标站点启用了该能力：相似图服务、异步任务后端、站点自行关闭的功能都可能缺失，
  由服务端决定结果，本库不做本地补丁或替代实现。

相关文档：[客户端用法](moebooru.md) · [能力总览](moebooru-capabilities.md) ·
[契约审计附注](moebooru-contract-notes.md) · [错误与状态码](errors.md) · [分页](pagination.md)。
