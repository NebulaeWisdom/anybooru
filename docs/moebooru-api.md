# Moebooru 方法参考

`Moebooru` 客户端一共 **90 个原生方法**，每个方法只做一件事：按上游 Moebooru 引擎（只读参考
`moebooru/` HEAD `206455e1`）确实提供 JSON 的那条路由，把参数发出去、把返回的 JSON 交给你。
本页给每个方法的**请求路径、参数（含默认值与不传时的行为）、返回字段、需要什么身份**，
常用方法配可复制的字面调用。逐条权限过滤器、上游文件行号与被排除的浏览器页面在
[契约审计附注](moebooru-contract-notes.md)；“我要做什么 → 用哪个方法”在[能力总览](moebooru-capabilities.md)。

## 本页怎么用

**每个代码块都能单独跑**：自己 import、自己 `with Moebooru('yandere') as client:`，参数写成字面值，
不需要任何额外的配置键。块内的变量名就是它装的内容（`posts` 装帖子数组、`post_id` 装一个帖子编号…）。
带“需要登录”的块照原样发出去会被服务端拒绝或改变线上数据，**本轮一次都没有执行**，只用来表明参数与请求体形状。

### 参数分两层

| 层 | 长什么样 | 例子 |
| :--- | :--- | :--- |
| 顶层查询参数（读接口全在这层） | `?tags=…&limit=…&page=…` | `client.post_list(tags='rating:s', page=1, limit=3)` → `GET https://yande.re/post.json?tags=rating%3As&page=1&limit=3` |
| 模型嵌套属性（只有写接口有） | 表单里 `模型名[字段]=值` | `client.post_update(1269034, tags='1girl solo')` → 表单体 `post%5Btags%5D=1girl+solo&id=1269034` |

Moebooru **没有** Danbooru 的 `search[...]` 搜索字典：`tags`、`query`、`name`、`limit`、`page` 就是顶层参数。
写接口用「语义必需的字段做成形参 + 其余属性收进 `**attributes`」，属性按模型名嵌套：
`post[…]`、`pool[…]`、`note[…]`、`tag[…]`、`tag_alias[…]`、`tag_implication[…]`、`wiki_page[…]`、
`comment[…]`、`forum_post[…]`、`artist[…]`、`user[…]`。

**引擎按字符串比较的开关必须传字面值**，传 Python 布尔不会生效：`unflag='1'`、`redo='1'`、
`forcegray='1'`、`anonymous='1'`、`filter='1'`、`api_version='2'`、
`commit='Yes'`（删画师）/`'Post'`（发评论）/`'Approve'`/`'Delete'`（审批）。

### 认证与路径

默认匿名：构造时 `username` 与 `password` 都空，请求里就没有 `login` 与 `password_hash`。
配置了凭据时，`GET`/`HEAD` 把 `login` + `password_hash` 放进查询串，其它动词放进表单体。
所有方法都请求 `.json`；`api_version` 为 `1.13.0` / `1.13.0+update.1` / `1.13.0+update.2` 的站点，
裸集合路径会被补成 `/index.json`，现役站点（`1.13.0+update.3`）是 `post.json` 这种形态。

### 返回结构

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | Python 对象原样返回：列表接口是数组，详情接口是单个字典 |
| `204` 或空正文 | `None`（只有 `forum_mark_all_read`） |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`：`http_code`、`url`、`body`、`data`（正文不是 JSON 时 `data` 是 `None`） |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError` |
| 连不上/超时 | requests 自己的异常，原样抛出 |

排查“参数到底发成什么样”看 `client.last_call['url']`（只保留最近一次请求），异常细节见 [errors.md](errors.md)。

### 分页与实际上限

页码从 1 开始，服务端把 `page` 夹在 `1..1000000`；**每页条数由服务端写死**，下表是引擎的真实行为，
不是客户端的限制。标 “`limit` 不读” 的端点传了也没用。

| 端点 | 每页 / 上限 |
| :--- | :--- |
| `post_list` | 默认 40，`limit` 上限 1000 |
| `pool_list` | 每页 20；`query` 里的 `limit:N` 上限 100 |
| `pool_show` | 每页 24 个帖子（账号开了合集浏览模式时 1000） |
| `note_list` | 按帖子分页（带 `post_id` 每页 100 个帖子，否则 16 个），再铺平这些帖子的全部笔记 |
| `note_history` | 25，按 `post_id` / `user_id` 过滤时 50；`limit` 不读 |
| `note_search` | 25 |
| `comment_list` | 25；`limit` 不读 |
| `comment_search` | 30 |
| `forum_list` | 带 `parent_id` 时 100，否则 30；`latest='1'` 固定第一页 10 条 |
| `wiki_list` | `limit` 生效，默认 25 |
| `wiki_recent_changes` | `per_page` 生效，默认 25 |
| `artist_list` | 带 `name` / `url` 时 50，否则 25；`limit` 不读 |
| `tag_list` | 默认 50；`limit=0` 返回全部标签 |
| `tag_related` | 没有 `limit`，每组最多 25 项 |
| `tag_autocomplete_name` / `user_autocomplete_name` | 最多 20 个名字 |
| `tag_alias_list` / `tag_implication_list` / `inline_list` / `user_list` | 20 |
| `post_popular_recent` / `_by_day` / `_by_week` / `_by_month` | 最多 40 条，按 `score` 降序 |
| `wiki_history` | 不分页，返回该页面的全部版本，按版本倒序 |

## 帖子（17）

读帖用 `post_list`，**没有 `post_show`**（那个动作只渲染 HTML）。

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    posts = client.post_list(tags='rating:s', page=1, limit=3)
    # GET https://yande.re/post.json?tags=rating%3As&page=1&limit=3
    # -> [{'id': 1269034, 'tags': '…', 'source': …, 'score': …, 'md5': …, 'file_url': …,
    #      'preview_url': …, 'sample_url': …, 'jpeg_url': …, 'width': …, 'height': …,
    #      'rating': 's', 'status': 'active', 'parent_id': …, 'creator_id': …}, …]
    print(posts[0]['id'], posts[0]['file_url'])
    post_id = posts[0]['id']
```

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    numbered_posts = client.post_list(tags='id:1269034')
    # GET https://yande.re/post.json?tags=id%3A1269034
    # 返回图片列表；每张有 id、md5、file_url 等字段，编号不存在时是空列表。
    print([(post['id'], post['file_url']) for post in numbered_posts])

    matching_posts = client.post_list(tags='md5:002d468b6f33d3572fc06c12353e150b')
    # GET https://yande.re/post.json?tags=md5%3A002d468b6f33d3572fc06c12353e150b
    # 这是图片 1269034 已返回过的 md5；按这个值查图片，返回相同结构的列表。
    print([post['id'] for post in matching_posts])

    page_data = client.post_list(tags='rating:s', limit=3, api_version='2')
    # GET https://yande.re/post.json?tags=rating%3As&limit=3&api_version=2
    # 返回字典 {"posts": [...]}；不传 include_* 时，没有 pools、tags 或 votes 这些键。
    print(len(page_data['posts']), list(page_data))

    expanded_data = client.post_list(tags='rating:s', limit=3, api_version='2',
                                     include_tags='1', include_votes='1', include_pools='1')
    # GET https://yande.re/post.json?tags=rating%3As&limit=3&api_version=2&include_tags=1&include_votes=1&include_pools=1
    # include_tags 加 tags，include_votes 加 votes，include_pools 加 pool_posts 和 pools。
    print(sorted(expanded_data), len(expanded_data['posts']))
```

```python
# 需要登录：上传一张新帖。file 是调用者打开的二进制文件，source-only 上传可以不给文件。
from anybooru import Moebooru

with open('image.jpg', 'rb') as upload_file:
    with Moebooru('yandere') as client:
        client.post_create('1girl rating:s', file=upload_file, source='https://example.org/1.jpg')
        # POST https://yande.re/post/create.json（multipart）
        # 部件 post[file]=<文件内容>、post[tags]=1girl rating:s、post[source]=https://example.org/1.jpg
        # -> {'success': True, 'post': {…}, 'tags': {…}}
```

```python
# 需要登录：改帖与投票。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.post_update(1269034, tags='1girl solo rating:s', source='https://example.org/1.jpg')
    # POST https://yande.re/post/update.json
    # 表单体 post%5Btags%5D=1girl+solo+rating%3As&post%5Bsource%5D=https%3A%2F%2Fexample.org%2F1.jpg&id=1269034
    # -> {'success': True, 'post': {…}, 'tags': {…}}
    client.post_vote(1269034, score=1)
    # POST https://yande.re/post/vote.json 表单体 id=1269034&score=1
    # -> {'success': True, 'posts': […], 'pool_posts': […], 'pools': […], 'tags': {…}, 'votes': {…}}
    client.post_vote(1269034)             # 不传 score 只读自己当前的投票 -> {'success': True, 'vote': 1}
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `post_list(**params)` | `GET post.json`（旧版本补成 `post/index.json`） | `tags` 站点标签语言，元标签全可用；`limit` 默认 40、上限 1000；`page` 默认 1；`filter='1'` 套用账号标签过滤；`api_version='2'` 换结构；`include_tags` / `include_votes` / `include_pools='1'` 在 v2 结构里多带对应字典 | 数组，字段见上面的块；已删除帖没有 `file_url` / `sample_url` / `jpeg_url` | 匿名 |
| `post_create(tags, *, file=None, source=None, md5=None, anonymous=None, **attributes)` | `POST post/create.json`（multipart） | `tags` 空格分隔标签串；`file` 打开的文件对象；`source` 来源地址，只有它也能上传（服务端自己下载）；`md5` 上传后校验，不匹配会销毁帖子并回 420；`anonymous='1'` 隐藏上传者（contributor）；`post[rating]` / `post[parent_id]` / `post[is_held]` 等属性 | `{'success': True, 'post': {…}, 'tags': {…}}`；重复 md5 → 423，超出每日上传限额 → 421 | 需登录（成员） |
| `post_update(post_id, **attributes)` | `POST post/update.json` | `post[tags]`、`post[old_tags]`、`post[source]`、`post[parent_id]`、`post[rating]`、`post[is_held]`、`post[is_shown_in_index]`、`post[is_note_locked]`、`post[is_rating_locked]`、`post[frames_pending_string]`；**没有文件替换**；缺少任何 `post[…]` 属性回 422 空正文 | `{'success': True, 'post': {…}, 'tags': {…}}`；非版主改已删除帖 → 422 | 需登录（上传者或版主） |
| `post_destroy(post_id, reason=None, *, destroy=None)` | `POST post/destroy.json` | `reason` 删除理由；`destroy='1'` 从数据库永久删除（仅版主，否则 403） | `{'success': True}` | 需登录，且是版主 / 帖子被 hold / 上传未满一天 |
| `post_revert_tags(post_id, history_id)` | `POST post/revert_tags.json` | `history_id` 是标签历史条目的 id，未知回 404 | `{'success': True}`，不带帖子数据 | 需登录 |
| `post_vote(post_id, score=None)` | `POST post/vote.json` | `score`：`1` 好 / `2` 很好 / `3` 收藏 / `0` 清除；不传就是只读当前投票；非版主负分或大于 3 → 424 | 只读 `{'success': True, 'vote': 1}`；写入回被触及帖子的批量数据 | 需登录 |
| `post_activate(post_ids)` | `POST post/activate.json` | `post_ids` 必须是列表，发成重复的 `post_ids[]`；传非列表得到空 204（客户端返回 `None`） | `{'success': True, 'count': N}` | 需登录（成员；非版主只能释出自己的 hold） |
| `post_acknowledge_new_deleted_posts()` | `POST post/acknowledge_new_deleted_posts.json` | 无参数 | `{'success': True}`；匿名调用不会更新任何用户状态 | 匿名可调 |
| `post_update_batch(post)` | `POST post/update_batch.json` | `post` 是 `{帖子编号: {属性: 值}}`，属性同 `post_update`；只有编号的条目表示只订阅回包 | 被触及帖子的批量数据 `{'posts': […], 'pool_posts': […], 'pools': […], 'tags': {…}, 'votes': {…}}` | 需登录 |
| `post_moderate(ids, commit, reason=None, reason2=None)` | `POST post/moderate.json` | `ids` 是 `{帖子编号: 任意值}`；`commit='Approve'` 或 `'Delete'`；`reason` / `reason2` 删除理由 | 被处理帖子（含父帖）的批量数据 | 需 janitor |
| `post_flag(post_id, reason=None, *, unflag=None)` | `POST post/flag.json` | `reason` 公开理由；`unflag='1'` 取消标记（本人或版主）；非 active 的帖子标记、非 flagged 的帖子取消都回 500 | 该帖的批量数据 | 需登录 |
| `post_undelete(post_id)` | `POST post/undelete.json` | 无其他参数 | 该帖及其父帖的批量数据 | 需 janitor |
| `post_similar(*, file=None, **params)` | 无文件 `GET post/similar.json`；有文件 `POST post/similar.json` | `id` 对比帖编号（未知回 404）、`url`、`search_id`、`services='local'`、`threshold`、`forcegray='1'`、`width`、`height`、`initial='1'`；文件走 multipart 的 `file` 部件；没有任何查询依据回 503 | `{'success': True, 'posts': [{'similarity': …, …}, …], 'source': …, 'search_id': …}`，部分服务报错时另带 `'error': [{'server', 'message', 'services'}]` | 匿名（依赖站点开了相似图服务） |
| `post_popular_recent(**params)` | `GET post/popular_recent.json` | `period`：`'1w'` / `'1m'` / `'1y'`，其他值被服务端换成 `'1d'` | 最多 40 个帖子，按 `score` 降序 | 匿名 |
| `post_popular_by_day(**params)` | `GET post/popular_by_day.json` | `year` / `month` / `day`，缺省取当天，日期非法回 400 空正文 | 当天最多 40 个帖子 | 匿名 |
| `post_popular_by_week(**params)` | `GET post/popular_by_week.json` | `year` / `month` / `day` 指该周内任意一天 | 该周最多 40 个帖子 | 匿名 |
| `post_popular_by_month(**params)` | `GET post/popular_by_month.json` | 同上，指该月内任意一天 | 该月最多 40 个帖子 | 匿名 |

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    similar_images = client.post_similar(id=1269034)
    # GET https://yande.re/post/similar.json?id=1269034
    # 根据站内图片编号比较相似图，结果的 posts 是匹配图片列表，success 表示是否完成查询。
    print(similar_images['success'], len(similar_images['posts']))
```

## 合集（10）

所有合集写路由都同时挂着 GET，但 **GET 只是渲染表单页，写入必须 POST**——下面的方法已经发 POST。

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    pools = client.pool_list(query='order:name', page=1)
    # GET https://yande.re/pool.json?query=order%3Aname&page=1
    # -> [{'id': 99411, 'name': …, 'created_at': …, 'updated_at': …, 'user_id': …,
    #      'is_public': True, 'post_count': …, 'description': …}, …]
    pool = client.pool_show(99411, page=1)
    # GET https://yande.re/pool/show.json?id=99411&page=1
    # -> 单个字典（不是数组）：{'id': 99411, 'name': …, 'created_at': …, 'updated_at': …, 'user_id': …,
    #    'is_public': True, 'post_count': …, 'description': …, 'posts': [
    #      {'id': …, 'tags': …, 'created_at': …, 'creator_id': …, 'author': …, 'source': …,
    #       'score': …, 'md5': …, 'file_size': …, 'file_url': …, 'preview_url': …,
    #       'sample_url': …, 'jpeg_url': …, 'rating': …, 'parent_id': …, 'status': …,
    #       'width': …, 'height': …, 'is_held': …}, …]}
    print(pools[0]['id'], pool['name'], len(pool['posts']))
```

```python
# 需要登录：往合集里加一个帖子（sequence 省略即追加到末尾）。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.pool_add_post(99411, 1269034, sequence=1)
    # POST https://yande.re/pool/add_post.json 表单体 pool_id=99411&post_id=1269034&pool%5Bsequence%5D=1
    # -> {'success': True}（不带合集内容）；帖子已在合集里 → 423
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `pool_list(**params)` | `GET pool.json` | `query` 支持 `order:name`、`limit:50`（上限 100）、`posts:1-10`；`order`：`name` / `date` / `updated` / `id`；`page` 默认 1，每页 20 | 数组：`id`、`name`、`created_at`、`updated_at`、`user_id`、`is_public`、`post_count`、`description` | 匿名 |
| `pool_show(pool_id, **params)` | `GET pool/show.json` | `id` 必给；`page` 选一页帖子，每页 24 个（账号开了合集浏览模式时 1000） | **一个合集字典**：`id`、`name`、`created_at`、`updated_at`、`user_id`、`is_public`、`post_count`、`description`，帖子在 `posts` 数组里（每项是 `id`、`tags`、`source`、`score`、`md5`、`file_url`、`preview_url`、`sample_url`、`jpeg_url`、`width`、`height`、`rating`、`status`、`parent_id`、`is_held` 等）；编号不存在会重定向到合集列表，最终可能读到列表 | 匿名 |
| `pool_create(name, **attributes)` | `POST pool/create.json` | `pool[description]`、`pool[is_public]`、`pool[is_active]` | `{'success': True}`，**不回新编号** | 需登录 |
| `pool_update(pool_id, **attributes)` | `POST pool/update.json` | 同上四个属性 | `{'success': True}`；不是所有者且合集不公开 → 403 | 需登录 |
| `pool_destroy(pool_id)` | `POST pool/destroy.json` | 无其他参数 | `{'success': True}`；无更新权限 → 403 | 需登录 |
| `pool_add_post(pool_id, post_id, sequence=None)` | `POST pool/add_post.json` | `pool_id` / `post_id` 是顶层字段；`pool[sequence]` 省略即追加 | `{'success': True}`；已在合集 → 423 | 需登录 |
| `pool_remove_post(pool_id, post_id)` | `POST pool/remove_post.json` | 无其他参数 | 被移除帖子的批量数据，响应头带 `X-Post-Id` | 需登录 |
| `pool_copy(pool_id, name=None)` | `POST pool/copy.json` | `name` 省略时服务端追加 ` (copy)` | JSON 只有 `{'success': True}`，新编号只在 HTML 重定向里 | 需 contributor |
| `pool_import(pool_id, posts)` | `POST pool/import.json` | `posts` 是 `{帖子编号: 顺序}`，按顺序升序加入 | POST 恒重定向到合集页，跟过去读到合集 JSON；**不是写入确认** | 需登录 |
| `pool_order(pool_id, sequences)` | `POST pool/order.json` | `sequences` 是 `{合集内帖子记录编号: 顺序}` | 同样恒重定向，读到合集 JSON；**不是写入确认** | 需登录 |

## 笔记、历史、收藏、内联与站内信（11）

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    notes = client.note_list(post_id=1269034)
    # GET https://yande.re/note.json?post_id=1269034
    # -> [{'id': …, 'post_id': 1269034, 'x': …, 'y': …, 'width': …, 'height': …,
    #      'body': …, 'is_active': True, 'version': …, 'creator_id': …}, …]
    versions = client.note_history(post_id=1269034)
    # GET https://yande.re/note/history.json?post_id=1269034
    # -> [{'version': …, 'post_id': 1269034, 'body': …, 'x': …, 'y': …, 'is_active': True, …}, …]（按版本倒序）
    print([(note['id'], note['body']) for note in notes])
    print([version['version'] for version in versions])
```

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    users = client.favorite_list_users(1269034)
    # GET https://yande.re/favorite/list_users.json?id=1269034
    # -> {'favorited_users': '名字1,名字2'}（服务端拼成一个字符串，无人收藏是空串；帖子不存在回 404）
    print(users['favorited_users'])
```

```python
# 需要登录：新建或修改一条笔记。传 note_id 是改，不传是新建（新建必须给 note[post_id]）。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.note_update(post_id=1269034, x=10, y=10, width=100, height=100, body='译注')
    # POST https://yande.re/note/update.json
    # 表单体 note%5Bpost_id%5D=1269034&note%5Bx%5D=10&note%5By%5D=10&note%5Bwidth%5D=100&note%5Bheight%5D=100&note%5Bbody%5D=译注
    # -> {'success': True, 'new_id': …, 'old_id': …, 'formatted_body': '…'}
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `note_list(**params)` | `GET note.json` | `post_id` 限定单帖；`page` 是**帖子页**，不带 `post_id` 时每页 16 个有笔记的帖子；`limit` 不读 | 铺平后的笔记数组：`id`、`post_id`、`x`、`y`、`width`、`height`、`body`、`is_active`、`version`、`creator_id`、`created_at`、`updated_at` | 匿名 |
| `note_search(query, **params)` | `GET note/search.json` | `query` **必需**（不给会落到 HTML 分支得 406）；`page` 每页 25 | 匹配的笔记数组 | 匿名 |
| `note_history(**params)` | `GET note/history.json` | 取值优先级 `id`（笔记编号）→ `post_id` → `user_id`；`page`；`limit` 不读 | 版本数组（`version`、`post_id`、`body`、坐标、`is_active`、`creator_id`、`created_at`），按版本倒序，每页 25（带 `post_id`/`user_id` 时 50） | 匿名 |
| `note_revert(note_id, version)` | `POST note/revert.json` | `version` 是笔记历史版本号 | `{'success': True}`；锁定帖 → 422 | 需登录 |
| `note_update(note_id=None, **attributes)` | `POST note/update.json` | 传 `note_id` 是更新，不传是新建；属性 `note[post_id]`（新建必需）、`note[x]`、`note[y]`、`note[width]`、`note[height]`、`note[body]`、`note[is_active]='1'/'0'` | `{'success': True, 'new_id': …, 'old_id': …, 'formatted_body': …}`；锁定帖 → 422 | 需登录 |
| `history_undo(change_ids, redo=None)` | `POST history/undo.json` | `change_ids` 是**变更条目**的 id（发成逗号连接的 `id`），不是历史批次 id；`redo='1'` 表示重做 | `{'success': True, 'successful': …, 'failed': …, 'errors': …}`；跨多条历史且等级低于 privileged → 403 | 需登录 |
| `favorite_list_users(post_id)` | `GET favorite/list_users.json` | `id` 必给 | `{'favorited_users': '名字1,名字2'}`；帖子不存在 → 404 | 匿名 |
| `inline_list(**params)` | `GET inline.json` | `page` 默认 1，每页 20 | 数组：`id`、`description`、`user_id`、`images` | 匿名 |
| `inline_copy(inline_id)` | `POST inline/copy.json` | 无其他参数 | `{'success': True}`，新编号只在 HTML 重定向里 | 需登录 |
| `inline_delete(inline_id)` | `POST inline/delete.json` | 无其他参数 | `{'success': True}`；不是本人（且非版主）→ 403 | 需登录 |
| `dmail_mark_all_read()` | `POST dmail/mark_all_read.json` | 协议固定值 `commit='Yes'` | `{'success': True}` | 需登录 |

## 画师（4）

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    artists = client.artist_list(name='fuzichoco')
    # GET https://yande.re/artist.json?name=fuzichoco
    # -> [{'id': …, 'name': 'fuzichoco', 'alias_id': None, 'group_id': None,
    #      'urls': ['https://www.pixiv.net/users/…', …]}, …]
    print([(artist['id'], artist['name'], artist['urls']) for artist in artists])
```

```python
# 需要登录：改画师记录（新建用 artist_create，允许字段相同）。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    artists = client.artist_list(name='fuzichoco')
    # GET https://yande.re/artist.json?name=fuzichoco -> [{'id': …, 'name': 'fuzichoco', 'urls': […]}, …]
    artist_id = artists[0]['id']
    client.artist_update(artist_id, urls='https://www.pixiv.net/users/27517', notes='备注')
    # POST https://yande.re/artist/update.json
    # 表单体 artist%5Burls%5D=https%3A%2F%2Fwww.pixiv.net%2Fusers%2F27517&artist%5Bnotes%5D=备注&id=<该画师编号>
    # -> {'success': True}
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `artist_list(**params)` | `GET artist.json` | `name`（子串匹配，不是精确相等）、`url`、`order`（`name` 默认 / `date`）、`page`；每页 25，带 `name`/`url` 时 50；`limit` 不读 | 数组：`id`、`name`、`alias_id`、`group_id`、`urls`（数组） | 匿名 |
| `artist_create(name, **attributes)` | `POST artist/create.json` | `artist[alias_name]`、`artist[alias_names]`、`artist[member_names]`、`artist[urls]`、`artist[notes]`；`artist[alias]` 与 `artist[group]` **不是**允许字段 | `{'success': True}`；校验失败 → 420 | 需登录（成员） |
| `artist_update(artist_id, **attributes)` | `POST artist/update.json` | 同一组字段再加 `name` | `{'success': True}`；`commit='Cancel'` 直接重定向回详情页 | 需登录（成员） |
| `artist_destroy(artist_id)` | `POST artist/destroy.json` | 协议值 `commit='Yes'` | 只有带 `commit='Yes'` 才回 `{'success': True}`，否则重定向回列表且不删除 | 需 privileged |

## 标签、别名与蕴含（12）

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    tags = client.tag_list(name='touhou', limit=3, order='count')
    # GET https://yande.re/tag.json?name=touhou&limit=3&order=count
    # -> [{'id': …, 'name': 'touhou', 'count': …, 'type': 3, 'ambiguous': False}, …]
    related = client.tag_related(tags='touhou', type='general')
    # GET https://yande.re/tag/related.json?tags=touhou&type=general
    # -> {'touhou': [['搭配标签', 共现次数], …]}（对象，不是数组；每组最多 25 项）
    print(tags[0]['name'], tags[0]['count'], related['touhou'][0])
    names = client.tag_autocomplete_name('touh')
    # GET https://yande.re/tag/autocomplete_name.json?term=touh -> ['touhou', …]（最多 20 个名字）
```

```python
# 需要登录：改标签类型；只发 POST，键名是 tag[name]。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.tag_update('touhou', tag_type=1, is_ambiguous='1')
    # POST https://yande.re/tag/update.json
    # 表单体 tag%5Bname%5D=touhou&tag%5Btag_type%5D=1&tag%5Bis_ambiguous%5D=1
    # -> {'success': True}；未知标签 → 404
```

```python
# 需要 mod：审批或删除标签别名。aliases 是 {别名编号: 任意值}。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    aliases = client.tag_alias_list(query='touhou')
    # GET https://yande.re/tag_alias.json?query=touhou -> [{'id': …, 'name': …, 'alias_id': …, 'pending': True}, …]
    alias_id = aliases[0]['id']
    client.tag_alias_update({alias_id: 1}, commit='Approve')
    # POST https://yande.re/tag_alias/update.json 表单体 aliases%5B<别名编号>%5D=1&commit=Approve
    # Approve 会把客户端带到只有 HTML 的任务页，最终可能拿到 500 或非 JSON——不代表没生效，先查 tag_alias_list 再说
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_list(**params)` | `GET tag.json` | `name` 子串匹配（带 `*` 就是原始 SQL 模式）、`id`、`type`（0 通用 / 1 画师 / 3 版权 / 4 角色）、`after_id`、`order`（`name` 默认 / `date` / `count`）、`limit`（默认 50，`0` 返回全部）、`page` | 数组：`id`、`name`、`count`、`type`、`ambiguous` | 匿名 |
| `tag_related(**params)` | `GET tag/related.json` | `tags` 空白分隔（服务端剥掉 `%`、`/`、`*` 并转小写）、`type` 必须是站点 tag_types 的键；没有 `limit` | 对象 `{'查询标签': [['名称', 共现次数], …]}`，每组最多 25 项 | 匿名 |
| `tag_update(name, **attributes)` | `POST tag/update.json` | 键名是 `tag[name]`（顶层 `name` 不生效）；`tag[tag_type]`、`tag[is_ambiguous]='1'` | `{'success': True}`；未知标签 → 404 | 需登录（成员） |
| `tag_autocomplete_name(term)` | `GET tag/autocomplete_name.json` | `term` 子串 | 名字数组，最多 20 个，按长度再按字母序 | 匿名 |
| `tag_summary(**params)` | `GET tag/summary.json` | `version` 是上次拿到的版本号 | 未变化时 `{'version': …, 'unchanged': True}`，否则返回带 `data` 的摘要 | 匿名 |
| `tag_mass_edit(start, result)` | `POST tag/mass_edit.json` | `start` 要被替换的标签、`result` 新标签；`start` 为空 → 424 | 只有开启异步任务的站点会同步回 `{'success': True}`；同步分支没有 JSON 响应 | 需 mod |
| `tag_alias_list(**params)` | `GET tag_alias.json` | `query`、`page` 每页 20；`commit='Search Implications'` 会带同一 query 跳到蕴含列表 | 数组：`id`、`name`、`alias_id`、`pending` | 匿名 |
| `tag_alias_create(name, alias_name, reason=None)` | `POST tag_alias/create.json` | `name` 是别名本身、`alias_name` 是目标标签（线上字段 `tag_alias[alias]`）、`reason` 给版主看的理由 | 建出待审记录，随后重定向到别名列表 | 需登录（成员） |
| `tag_alias_update(aliases, commit, reason=None)` | `POST tag_alias/update.json` | `aliases` 是 `{别名编号: 任意值}`；`commit='Approve'` 或 `'Delete'`（其他值 → 400）；`reason` | `Delete` 重定向到列表；`Approve` 重定向到只有 HTML 的任务页，可能拿到 500 或非 JSON | 需 mod（删除时待审记录的创建者也可以） |
| `tag_implication_list(**params)` | `GET tag_implication.json` | `query`、`page` 每页 20 | 数组：`id`、`consequent_id`、`predicate_id`、`pending` | 匿名 |
| `tag_implication_create(predicate, consequent, reason=None)` | `POST tag_implication/create.json` | 申请“predicate 蕴含 consequent”，字段是 `tag_implication[predicate]` / `[consequent]` / `[reason]` | 建出待审记录，随后重定向到蕴含列表 | 需登录（成员） |
| `tag_implication_update(implications, commit, reason=None)` | `POST tag_implication/update.json` | `implications` 是 `{蕴含编号: 任意值}`；`commit` / `reason` 同别名 | 同别名审批（`Approve` 分支可能拿到 500 或非 JSON） | 需 mod（同上例外） |

## 评论（7）

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    comments = client.comment_list(post_id=1269034)
    # GET https://yande.re/comment.json?post_id=1269034
    # -> [{'id': …, 'created_at': …, 'post_id': 1269034, 'creator': '名字', 'creator_id': …, 'body': …}, …]
    recent = client.comment_search(query='', page=1)
    # GET https://yande.re/comment/search.json?page=1&query=   （query 为空串 = 不启用全文过滤）
    # -> 评论数组；空数组是正常结果，不是失败
    print([(comment['id'], comment['body']) for comment in comments])
    print([(comment['id'], comment['post_id']) for comment in recent])
```

```python
# 需要登录：发表评论。comment[anonymous] 不是允许字段。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.comment_create(1269034, '好图')
    # POST https://yande.re/comment/create.json
    # 表单体 comment%5Bpost_id%5D=1269034&comment%5Bbody%5D=好图
    # -> {'success': True}；小时限额 → 421，校验失败 → 420
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `comment_list(**params)` | `GET comment.json` | `post_id` **必须带**（不带就等于查 0 号帖，得到空数组）；`page` 每页 25；`limit` 不读 | 数组：`id`、`created_at`、`post_id`、`creator`、`creator_id`、`body` | 匿名 |
| `comment_search(query, **params)` | `GET comment/search.json` | `query` 支持 `user:<名字>`；空串不启用全文过滤、可当评论流；`page` 每页 30 | 评论数组（空数组是正常结果） | 匿名 |
| `comment_show(comment_id)` | `GET comment/show.json` | `id` 必给 | 单条评论字典，字段同列表；不存在 → 404 HTML 页（`data` 为 `None`） | 匿名 |
| `comment_create(post_id, body)` | `POST comment/create.json` | `comment[post_id]`、`comment[body]` | `{'success': True}`；小时限额 → 421、校验失败 → 420 | 需登录（成员） |
| `comment_update(comment_id, **attributes)` | `POST comment/update.json` | `comment[body]`、`comment[post_id]` | `{'success': True}`；无权 → 403 | 需登录（本人或版主） |
| `comment_destroy(comment_id)` | `POST comment/destroy.json` | 无其他参数 | `{'success': True}`；无权 → 403 | 需登录（本人或版主） |
| `comment_mark_as_spam(comment_id)` | `POST comment/mark_as_spam.json` | 无其他参数 | `{'success': True}` | 路由没有登录过滤器，匿名也能调——但它**会改数据**，不是只读接口 |

## Wiki（9）

**没有 `wiki_show`**：`wiki/show` 只有 HTML 页面。

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    pages = client.wiki_list(query='title:touhou', limit=3)
    # GET https://yande.re/wiki.json?query=title%3Atouhou&limit=3
    # -> [{'id': …, 'title': 'touhou', 'body': …, 'updater_id': …, 'locked': False, 'version': …,
    #      'created_at': …, 'updated_at': …}, …]
    versions = client.wiki_history(title='touhou')
    # GET https://yande.re/wiki/history.json?title=touhou
    # -> 该页面的全部版本，按版本倒序，不分页
    recent = client.wiki_recent_changes(per_page=3)
    # GET https://yande.re/wiki/recent_changes.json?per_page=3 -> 改动数组
    print(pages[0]['title'], pages[0]['version'], len(versions), len(recent))
```

```python
# 需要登录：改正文，或改名。顶层 title 选中页面，new_title 才是新标题。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.wiki_update('touhou', body='新正文')
    # POST https://yande.re/wiki/update.json 表单体 wiki_page%5Bbody%5D=新正文&title=touhou
    # -> {'success': True}；必须至少给一个 wiki_page[...] 属性，否则 400
    client.wiki_update('old_title', new_title='new_title')
    # POST https://yande.re/wiki/update.json 表单体 wiki_page%5Btitle%5D=new_title&title=old_title
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `wiki_list(**params)` | `GET wiki.json` | `query` 普通词走全文检索、`title:` 前缀改成标题匹配；`order`（`title` 默认 / `date`）；`limit` 默认 25（生效）；`page` | 数组：`id`、`created_at`、`updated_at`、`title`、`body`、`updater_id`、`locked`、`version` | 匿名 |
| `wiki_history(title=None, **params)` | `GET wiki/history.json` | `title` 或 `id` 指定页面 | 该页面的全部版本（按版本倒序，不分页） | 匿名 |
| `wiki_recent_changes(**params)` | `GET wiki/recent_changes.json` | `user_id`、`per_page`（默认 25，生效）、`page` | 改动数组 | 匿名 |
| `wiki_create(title, body)` | `POST wiki/create.json` | `wiki_page[title]`、`wiki_page[body]` | `{'success': True, 'location': …}`；校验失败 → 420 | 需登录（成员） |
| `wiki_update(title, *, new_title=None, **attributes)` | `POST wiki/update.json` | 顶层 `title` 选页面；`new_title` → `wiki_page[title]`、`body` → `wiki_page[body]`；必须至少一个 `wiki_page[…]` | `{'success': True}`；缺嵌套属性 → 400；锁定页 → 422 | 需登录（成员） |
| `wiki_destroy(title)` | `POST wiki/destroy.json` | 顶层 `title` | `{'success': True}` | 需 mod |
| `wiki_lock(title)` / `wiki_unlock(title)` | `POST wiki/lock.json` / `wiki/unlock.json` | 顶层 `title` | `{'success': True}`；不存在的标题在 lock / unlock 上回 500 | 需 mod |
| `wiki_revert(title, version)` | `POST wiki/revert.json` | 顶层 `title` + `version`（历史版本号） | `{'success': True}`；锁定页 → 422 | 需登录 |

## 论坛（11）

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    topics = client.forum_list(page=1)
    # GET https://yande.re/forum.json?page=1
    # -> [{'id': …, 'parent_id': None, 'title': …, 'body': …, 'creator': …, 'creator_id': …,
    #      'updated_at': …, 'pages': …}, …]（主题每页 30）
    topic_id = topics[0]['id']
    replies = client.forum_list(parent_id=topic_id, page=1)
    # GET https://yande.re/forum.json?parent_id=<该主题编号>&page=1 -> 该主题的回复，每页 100
    one_topic = client.forum_show(topic_id)
    # GET https://yande.re/forum/show.json?id=<该主题编号> -> 单个论坛帖字典
    print(topics[0]['id'], topics[0]['title'], len(replies), one_topic['id'])
```

```python
# 需要登录：发新主题（parent_id=0 或省略是新主题，否则是回复）。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.forum_create('主题标题', '正文', parent_id=0)
    # POST https://yande.re/forum/create.json
    # 表单体 forum_post%5Btitle%5D=主题标题&forum_post%5Bbody%5D=正文&forum_post%5Bparent_id%5D=0
    # 随后 302 到主题页，跟过去读到的是主题 JSON——不是写入确认
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `forum_list(**params)` | `GET forum.json` | `parent_id` 看某个主题的回复（每页 100）；`latest='1'` 取第一页 10 条；`page`（主题每页 30） | 数组：`id`、`parent_id`、`title`、`body`、`creator`、`creator_id`、`updated_at`、`pages` | 匿名 |
| `forum_show(forum_id, **params)` | `GET forum/show.json` | `id` 必给；`page` 只在 HTML 视图里分页回复 | 单个论坛帖字典 | 匿名 |
| `forum_search(query, **params)` | `GET forum/search.json` | `query`、`page` 每页 30 | 论坛帖数组 | 匿名 |
| `forum_create(title, body, **attributes)` | `POST forum/create.json` | `forum_post[title]`、`forum_post[body]`；`forum_post[parent_id]` 为 `0` 或省略是发新主题 | 重定向到主题页，读到主题 JSON | 需登录 |
| `forum_update(forum_id, **attributes)` | `POST forum/update.json` | `forum_post[title]`、`forum_post[body]`、`forum_post[parent_id]` | 重定向回主题；无权 → 403 | 需登录（创建者或版主） |
| `forum_destroy(forum_id)` | `POST forum/destroy.json` | 无其他参数 | 重定向到主题或论坛索引，读到页面 JSON | 需登录（创建者或版主） |
| `forum_lock(forum_id)` / `forum_unlock(forum_id)` / `forum_stick(forum_id)` / `forum_unstick(forum_id)` | `POST forum/lock.json` / `forum/unlock.json` / `forum/stick.json` / `forum/unstick.json` | `forum_lock` 的编号放在请求体，其余在路径/参数里 | 重定向后的主题页 JSON | 需 mod |
| `forum_mark_all_read()` | `POST forum/mark_all_read.json` | 无参数 | 服务端回空 `204`，客户端返回 `None` | 需登录 |

## 账号（9）

账号面只做源码对齐，**没有可用测试账号，一次线上请求都没发**。

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    users = client.user_list(name='admin', page=1)
    # GET https://yande.re/user.json?name=admin&page=1
    # -> [{'name': 'admin', 'id': …}, …]（每行只有这两个字段；每页 20）
    names = client.user_autocomplete_name('adm')
    # GET https://yande.re/user/autocomplete_name.json?term=adm -> ['admin', …]（最多 20 个）
    print([(user['name'], user['id']) for user in users], names[:3])
```

```python
# 需要登录：增删自己的标签黑名单（列表发成重复键 add[] / remove[]）。
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.user_modify_blacklist(add=['bad_tag'], remove=['old_tag'])
    # POST https://yande.re/user/modify_blacklist.json
    # 表单体 add%5B%5D=bad_tag&remove%5B%5D=old_tag
    # -> {'success': True, 'result': ['…']}（返回新的黑名单）
```

| 方法 | 请求 | 参数（默认值 / 不传时） | 返回 | 身份 |
| :--- | :--- | :--- | :--- | :--- |
| `user_list(**params)` | `GET user.json` | `name` 子串、`level`、`id`、`order`、`page` 每页 20 | 数组，每行只有 `{'name': …, 'id': …}` | 匿名 |
| `user_autocomplete_name(term)` | `GET user/autocomplete_name.json` | `term`；短于 2 个字符回空数组 | 名字数组，最多 20 个 | 匿名 |
| `user_check(username, password)` | `POST user/check.json` | `username` + **明文** `password`（不是配置里的密码哈希） | `{'response': 'success' | 'unknown-user' | 'wrong-password', 'exists': …, 'name': …, 'id': …, 'no_email': …, 'pass_hash': …, 'user_info': …}` | 匿名（未实测） |
| `user_create(name, password, password_confirmation, **attributes)` | `POST user/create.json` | `user[name]`、`user[password]`、`user[password_confirmation]`，其余设置同 `user_update` | **失败也是 200**：`{'response': 'success' | 'error', 'errors': […]}` | 匿名（未实测） |
| `user_update(**attributes)` | `POST user/update.json` | `user[email]`、`user[password]`、`user[current_password]`、`user[blacklisted_tags]`、`user[always_resize_images]`、`user[receive_dmails]`、`user[show_samples]`、`user[use_browser]`、`user[show_advanced_editing]`、`user[pool_browse_mode]`；**不接受 `name`** | `{'success': True}`；校验失败 → 420 | 需登录 |
| `user_authenticate(**params)` | `POST user/authenticate.json` | `url` 回跳路径，其他值被控制器忽略 | `{'success': True}` | 需登录 |
| `user_modify_blacklist(add=None, remove=None)` | `POST user/modify_blacklist.json` | `add` / `remove` 是标签列表，发成重复键 `add[]` / `remove[]` | `{'success': True, 'result': […]}` | 需登录 |
| `user_reset_password(name, email)` | `POST user/reset_password.json` | `user[name]`、`user[email]`，两者要属于同一账号 | 成功 `{'result': 'success'}`；`'unknown-user'` / `'no-email'` / `'wrong-email'` 回 500，SMTP 拒收是 `'invalid-email'` | 匿名（未实测） |
| `user_record_destroy(user_record_id)` | `POST user_record/destroy.json` | 无其他参数 | `{'success': True}`；无权 → 403 | 需 privileged，且是版主或该记录的提交者 |

## 看清评论查询的错误响应

不存在的评论编号不会返回一个空评论，而是 HTTP 404。下面用编号 `0` 演示如何看到状态和服务器正文：

```python
from anybooru import Moebooru, AnybooruHTTPError

with Moebooru('yandere') as client:
    try:
        missing_comment = client.comment_show(0)
        # GET https://yande.re/comment/show.json?id=0
    except AnybooruHTTPError as error:
        print(error.http_code, error.url)  # 404 https://yande.re/comment/show.json?id=0
        print(error.data)  # None：这次错误正文是 HTML，不是 JSON
        print(error.body[:120])  # 查看服务器返回的 HTML 开头
```

## 边界与未实测

* 本页每个方法的参数、返回字段与身份都按上游源码对齐。**写动作与账号动作没有线上实测**；
  匿名只读的实际执行范围与逐条命令见 [verification.md](verification.md)，逐条状态与上游行号见
  [契约审计附注](moebooru-contract-notes.md)。
* 只包装有 JSON 的端点：HTML / JS 页面、Atom/RSS 订阅源与合集 ZIP 都没有方法，它们仍是有真实路由的。
  其中一个特殊情况是 `help/api`——本库固定发 `Accept: application/json`，而该页只有 HTML 模板，
  所以 `request('GET', 'help/api')` 会拿到 404（yande.re 是它的 HTML 404 页，konachan.com 与
  sakugabooru.com 是空正文），把 Accept 换成 `text/html` 就是 200。完整排除清单见附注。
* 方法存在不等于目标站点启用了该能力：相似图服务、异步任务后端、站点自己关掉的功能都可能缺失，
  结果由服务端决定，本库不做本地补丁或替代实现。

相关文档：[客户端用法](moebooru.md) · [能力总览](moebooru-capabilities.md) ·
[契约审计附注](moebooru-contract-notes.md) · [错误与状态码](errors.md) · [分页](pagination.md)。
