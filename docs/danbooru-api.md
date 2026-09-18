# Danbooru 方法参考

`Danbooru` 的 227 个原生方法都是 `request()` 的薄封装：一个方法对应一条 JSON 路由，参数原样交给
服务端，库不校验、不钳位、不重试、不翻页。构造、认证、参数编码与返回值见
[客户端用法](danbooru.md)；按目的找入口见 [能力入口](danbooru-capabilities.md)；每个方法的逐条路由、
凭据、上游出处与验证状态见 [契约审计附注](danbooru-contract-notes.md) 的对应小节。

**怎么读本页**：每个资源组先给常用方法的完整片段——片段自己 `import`、自己 `with Danbooru('danbooru')
as client`，参数全是字面值，旁边标出真实请求 URL 与返回的关键字段；组内其余方法用一张参数表列出，
每行写明参数名、类型与取值、含义、不传时的行为与示例，以及“给什么 → 返回什么”。带「写」字样的方法
需要登录或更高等级，本页只给用法，全部未执行；未实测范围的汇总见[边界与未实测](#边界与未实测)。

## 全页通用契约

* **认证**：`username` 或 `api_key` 任一非空即发 HTTP Basic（缺项按空串补）；凭据不完整或无效由服务端
  以 `401` 拒绝，不会静默降级为匿名；匿名读接口默认放行，权限不足返回 `403`。需要登录的方法在各自
  条目里标注。
* **参数分层**：列表方法的过滤条件放 `search` 字典（整包发成 `search[...]`），顶层参数走 `**params`
  （`limit`、`page`、`tags`、`post_id` 等）。**帖子列表是唯一例外**：过滤条件全部写成顶层 `tags` 元标签。
* **搜索后缀**：string 属性有 `_present`/`_eq`/`_not_eq`/`_like`/`_ilike`/`_regex`/`_array`/`_comma`/
  `_space`/`_lower_array` 等；text 另有 `_matches`（全文，含 `*` 时按 `ILIKE`）；数值与时间支持 `5`、
  `>5`、`5..10`、`5,6,7`；布尔收 `true`/`false`/`1`/`0`/`yes`/`no`；关联字段另有 `assoc_name`、
  `assoc_tags_match`、`has_assoc` 与嵌套 `search[assoc][...]`。**集合之外的参数被静默忽略**——旧参数
  失效时表现为“返回全集”，不报错。
* **分页与配额**：默认每页 20；通用 `limit` 上限 1000，`posts` 与 `uploads` / `upload_media_assets` /
  `media_assets` / `ai_tags` 为 200；页码上限普通账号 1000、Gold 5000，超出返回 `410`；一次查询的标签数
  上限匿名 2、Gold 6、Platinum 不限，超出返回 `422`。`page` 也接受 ID 游标 `a<id>`（更新方向）/
  `b<id>`（更旧方向）。翻页见 [pagination.md](pagination.md)。
* **端点无关的顶层参数**：`only`（选返回字段与嵌套关联，如 `only=id,url,artist[name]`，只对 json/xml
  生效）、`redirect=true`（结果唯一时 `302` 到对象页面）、`safe_mode`（强制 `rating:g`）、`save_data`
  （省流模式）。
* **失败**：非 2xx 抛 `AnybooruHTTPError`（保留状态码、URL 与正文），2xx 但非 JSON 抛
  `AnybooruAPIError`；archive 未配置返回 `501`，IQDB 未配置返回空数组，各可选服务分别判断。见
  [errors.md](errors.md)。

## 状态、账号与限流（6 个方法）

状态接口匿名可读；`api_keys_*` 四个方法要求登录，且控制器带 `requires_reauthentication`——只用
HTTP Basic（本库的发法）可能过不了这道检查，未实测。本组方法的逐条路由、参数键与凭据见
[附注的 状态节](danbooru-contract-notes.md#sec-status)。

**常用方法**

**`status()`** — 查服务、数据库与缓存状态。不给参数，匿名可调；返回一个对象：`ip`、`headers`、
`instance`、`version`、`server`、`postgres`、`redis`，例如 `state['postgres']['up']` 是数据库是否可用。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    state = client.status()
    # GET https://danbooru.donmai.us/status.json
    # 返回 ip / headers / instance / version / server / postgres / redis
    print(state['version'], state['postgres']['up'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| — | — | 没有参数，路由也不带路径变量 | — | `client.status()` |

**`api_keys_list(search=None, **params)`** — 列出自己可管理的 API key（需登录）。返回 api_key 数组，
每项含 `id`、`user_id`、`name`、`permissions`；响应里**不含** `key`，明文只在 `api_key_create` 的
响应里出现一次。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    keys = client.api_keys_list(limit=10)
    # GET https://danbooru.donmai.us/api_keys.json?limit=10
    # 返回数组，每项含 id / user_id / name / permissions（不含 key）
    print([item['name'] for item in keys])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，如 `{'id': 5}`、`{'key': 'abc'}`、`{'user_id': 42}` | API key 的过滤条件，发成 `search[...]` | 不发送 `search`，列出全部可见项 | `search={'user_id': 42}` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 `'a<id>'` / `'b<id>'` | 页码或 ID 游标 | 第一页 | `page=2` |

**本组其余 4 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `rate_limits_list(search=None, **params)` | `search`：dict，可筛 `id`、`action`（如 `'post_create'`）、`key`、`limited`（bool）、`points`（int）；`limit`：int 每页条数；`page`：int 页码 | 查限流记录，匿名可读（源码对齐、未实测）→ rate_limit 数组，字段随站点配置；例 `client.rate_limits_list(search={'action': 'post_create'})` |
| `api_key_create(**attributes)` | `name`：str 这把 key 的名字，如 `'我的脚本'`；`permitted_ip_addresses`：str 空格分隔的允许 IP 段，不传时未规定；`permissions`：list 权限名 | **写**：新建一把 API key（需登录）→ 新建的 api_key 对象，含 `id`、`name`、`permissions` 与**明文 `key`**（只有这一次会返回）；例 `client.api_key_create(name='我的脚本', permitted_ip_addresses='203.0.113.0/24')` |
| `api_key_update(api_key_id, **attributes)` | `api_key_id`：int，如 `7`（要先从 `api_keys_list` 取）；属性同 `api_key_create`（`name` / `permitted_ip_addresses` / `permissions`），不传的属性保持原值 | **写**：改名称、允许 IP 或权限（需登录）→ 更新后的 api_key 对象，不含 `key`；例 `client.api_key_update(7, name='新名字')` |
| `api_key_delete(api_key_id)` | `api_key_id`：int，如 `7` | **写**：删除一把 key（需登录）→ 被删除的 api_key 对象，不含 `key`；例 `client.api_key_delete(7)` |

## posts（帖子）— 37 个方法

`post_list` 的过滤条件全部写在顶层 `tags` 元标签里（`rating:g`、`score:>10`、`order:score`、`date:..`），
**不吃 `search` 字典**；`md5=` 直接返回单个 post，`random=true` 会 `302`。发布新帖要先上传，见
[上传与上传媒体](#上传与上传媒体6-个方法)。本组方法的路由、凭据与参数键见
[附注的 posts 节](danbooru-contract-notes.md#sec-posts)。

**常用方法**

**`post_list(**params)`** — 搜索或列出帖子。过滤条件写进顶层 `tags`，每条常见元标签的写法见参数表；
返回 post 数组，常用字段为 `id`、`rating`、`tag_string`、`md5`、`source`，图片地址类字段
（`file_url` / `large_file_url` / `preview_file_url`）只在帖子对当前身份可见时出现。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    posts = client.post_list(tags='rating:g order:score', limit=2)
    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag+order%3Ascore&limit=2
    # 返回数组，每项含 id / rating / tag_string / md5 / source（可见时另有 file_url 等）
    print(posts[0]['id'], posts[0]['rating'], posts[0]['tag_string'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | str，标签查询串；元标签如 `rating:g`、`score:>10`、`order:score`、`date:2024-01-01..`、`id:>123` | 过滤条件与排序，空格分隔多个条件 | 空值即最新一页全部帖子 | `tags='rating:g order:score'` |
| `limit` | int，服务端上限 200 | 每页帖子数 | 服务端默认每页 20 | `limit=50` |
| `page` | int 或 `'a<id>'` / `'b<id>'` | 页码或 ID 游标 | 第一页 | `page='b12090564'` |
| `md5` | str，32 位小写十六进制 | 直接返回这个 MD5 对应的单个 post，而不是数组 | 不发送，返回列表 | `md5='0f343b0931126a20f133d67c2b018a3b'` |
| `random` | bool（`true` / `false`） | 返回随机一页而不是最新帖子 | `false` | `random=True` |
| `size` | str，如 `'medium'` | 请求哪个预览尺寸 | 服务端默认尺寸 | `size='medium'` |
| `show_votes` | bool | 把当前用户的投票并进 `tag_string`（表现为 `upvoted` / `downvoted` 标签） | 不发送 | `show_votes=True` |
| `only` | str，逗号分隔字段与嵌套关联 | 只返回指定字段，如 `'id,media_asset'` | 返回完整对象 | `only='id,rating'` |

**`post_show(post_id)`** — 读一个帖子的详情。给帖子编号，返回单个 post 对象，字段与 `post_list` 一致，
另外带上该帖的父帖 `parent_id`、来源 `source`、收藏数 `favorite_count`、评分 `score`、图片尺寸
（可见时含 `file_url`、`large_file_url`、`preview_file_url`、`file_size`、`image_width`、`image_height`）。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']   # 先取一个真实存在的编号
    post = client.post_show(post_id)
    # GET https://danbooru.donmai.us/posts/<post_id>.json
    # 返回单个对象：id / rating / tag_string / md5 / source / score / file_url（可见时）
    print(post['id'], post['source'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | int，帖子编号，如 `12090564` | 要读哪个帖子，会进 URL 路径 | 必填 | `client.post_show(12090564)` |
| `only` | str | 只返回指定字段（用 `request('GET', 'posts/<id>.json', params={'only': 'id,rating'})` 传，本方法签名没有该形参） | 返回完整对象 | `request('GET', 'posts/12090564.json', params={'only': 'id,rating'})` |

**`post_random(tags=None)`** — 在查询范围内随机取一帖。给标签查询串（空值表示任意帖子），返回单个
post 对象；查询无匹配时服务端返回 `404`。它不做分页，每次调用都是新的一次随机。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post = client.post_random(tags='rating:g')
    # GET https://danbooru.donmai.us/posts/random.json?tags=rating%3Ag
    # 返回单个对象：id / rating / tag_string / md5 / source
    print(post['id'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | str，任何 `post_list` 能吃的标签查询串 | 限定随机范围 | 空值 / `None` 表示任意帖子 | `client.post_random(tags='rating:g')` |

**`post_update(post_id, **attributes)`** — 改标签、来源、评分、父帖等属性（需登录，且对该帖有编辑
权限）。给帖子编号与要改的属性，返回写后的 post 对象（含 `id`、`rating`、`tag_string`、`source` 等）。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post = client.post_list(tags='rating:g', limit=1)[0]
    client.post_update(post['id'], tag_string='1girl solo',
                       old_tag_string=post['tag_string'])
    # PUT https://danbooru.donmai.us/posts/<post_id>.json
    # 请求体 {"post": {"tag_string": "1girl solo", "old_tag_string": "<编辑前的标签>"}}
    # 返回写后的对象：id / rating / tag_string / source
```

| 属性 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_string` | str，空格分隔的标签 | 本次要写入的完整标签集 | 不改标签 | `tag_string='1girl solo'` |
| `old_tag_string` | str | 你**编辑前**看到的标签，供服务端合并并发改动 | 不参与并发比对 | `old_tag_string=post['tag_string']` |
| `source` | str，来源 URL 或文本 | 本次要写入的来源 | 不改来源 | `source='https://www.pixiv.net/artworks/12345678'` |
| `old_source` | str | 编辑前的来源，同上用于并发比对 | 不参与比对 | `old_source=post['source']` |
| `rating` | str，`g` / `s` / `q` / `e` | 本次要写入的评分 | 不改评分 | `rating='s'` |
| `old_rating` | str，同上四值 | 编辑前的评分 | 不参与比对 | `old_rating=post['rating']` |
| `parent_id` | int 或 `null` | 父帖编号；`null` 表示清空父子关系 | 不改父帖 | `parent_id=12000000` |
| `old_parent_id` | int 或 `null` | 编辑前的父帖编号 | 不参与比对 | `old_parent_id=post['parent_id']` |
| `has_embedded_notes` | bool | 声明图内是否烧进了笔记内容 | 不发送 | `has_embedded_notes=False` |

**`post_votes_list(search=None, **params)`** — 查询帖子投票记录。返回 post_vote 数组，每项含 `id`、
`post_id`、`user_id`、`score`；非本人、非 moderator 的投票会被服务端按可见性过滤。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    votes = client.post_votes_list(search={'post_id': post_id}, limit=10)
    # GET https://danbooru.donmai.us/post_votes.json?search%5Bpost_id%5D=<post_id>&limit=10
    # 返回数组，每项含 id / post_id / user_id / score（score 为 1 或 -1）
    print([(vote['user_id'], vote['score']) for vote in votes])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `post_id`、`user_id`、`user_name`、`score`（`1` / `-1`）、`is_deleted` | 投票过滤条件 | 列出可见的全部投票 | `search={'post_id': 12090564}` |
| `limit` | int | 每页投票数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`post_vote_create(post_id, score)`** — 给帖子投票（需登录）。`score` 只接受数字：**`1` 是赞、`-1`
是踩**（源码 docstring 写的 `'up'` / `'down'` 与模型校验不符，模型只认 `1` / `-1`）。返回新建的
post_vote 对象，含 `id`、`post_id`、`user_id`、`score`。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    vote = client.post_vote_create(post_id, score=1)
    # POST https://danbooru.donmai.us/posts/<post_id>/votes.json
    # 请求体 {"score": 1}；返回新建对象：id / post_id / user_id / score
    print(vote['id'], vote['score'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | int，帖子编号 | 投给哪个帖子，会进 URL 路径 | 必填 | `client.post_vote_create(12090564, score=1)` |
| `score` | int，只接受 `1`（赞）或 `-1`（踩） | 投票方向 | 必填 | `score=-1` |

**`post_replacement_create(post_id, replacement_file=None, **attributes)`** — 用新文件或来源替换帖子
文件（需 moderator）。两条二选一：本地上传走 `replacement_file`（multipart，字段名
`post_replacement[replacement_file]`），或给 `replacement_url` 让服务端去取。返回新建的
post_replacement 对象。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    client.post_replacement_create(post_id,
                                   replacement_url='https://example.com/new.jpg',
                                   final_source='https://example.com/page')
    # POST https://danbooru.donmai.us/post_replacements.json
    # 请求体 {"post_replacement": {"replacement_url": "...", "final_source": "..."},
    #        "post_id": <post_id>}
    # 返回新建对象：id / post_id / creator_id / original_url / replacement_url / status
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | int，帖子编号 | 要替换哪个帖子（顶层参数） | 必填 | `post_id=12090564` |
| `replacement_file` | 以二进制打开的文件对象 | 本地新文件；由调用者负责关闭 | 不发文件，需改用 `replacement_url` | `replacement_file=open('new.jpg', 'rb')` |
| `replacement_url` | str | 服务端去下载的新文件地址 | 与 `replacement_file` 至少给一个 | `replacement_url='https://example.com/new.jpg'` |
| `final_source` | str | 替换后要显示的来源 | 不发送 | `final_source='https://example.com/page'` |
| `tags` | str，空格分隔 | 替换时要补的标签 | 不发送 | `tags='translated'` |

**`post_flags_list(search=None, **params)`** — 查询帖子的待删标记。返回 post_flag 数组，每项含 `id`、
`post_id`、`creator_id`、`reason`、`is_resolved`；非 moderator 看不到标记人的身份字段。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    flags = client.post_flags_list(search={'post_id': post_id, 'status': 'pending'}, limit=10)
    # GET https://danbooru.donmai.us/post_flags.json?search%5Bpost_id%5D=<post_id>&search%5Bstatus%5D=pending&limit=10
    # 返回数组，每项含 id / post_id / creator_id / reason / is_resolved
    print([(flag['id'], flag['reason']) for flag in flags])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`post_id`、`reason_matches`、`status`（`pending` / `succeeded` / `rejected`）、`category`（`normal` / `unapproved` / `rejected` / `deleted`）、`creator_id`、`creator_name` | 标记过滤条件 | 列出可见的全部标记 | `search={'post_id': 12090564, 'status': 'pending'}` |
| `limit` | int | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`post_approvals_list(search=None, **params)`** — 查询帖子批准记录。返回 post_approval 数组，每项含
`id`、`user_id`、`post_id`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    approvals = client.post_approvals_list(search={'post_id': post_id})
    # GET https://danbooru.donmai.us/post_approvals.json?search%5Bpost_id%5D=<post_id>
    # 返回数组，每项含 id / user_id / post_id
    print([(item['id'], item['user_id']) for item in approvals])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `post_id`、`user_id`、`user_name` | 批准记录过滤条件 | 列出可见的全部记录 | `search={'post_id': 12090564}` |
| `limit` | int | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**本组其余 28 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `post_create(upload_media_asset_id, **attributes)` | `upload_media_asset_id`：int，来自 `upload_create` 响应里 `upload_media_assets[0]['id']`，**顶层**参数，塞进 `post[...]` 会被当未知属性；`tag_string`：str 空格分隔标签，如 `'1girl solo'`；`rating`：`g` / `s` / `q` / `e`；`parent_id`：int 父帖编号；`source`：str 来源；`is_pending`：bool 发成待审；`artist_commentary`：dict（`original_title`、`original_description`、`translated_title`、`translated_description`）；不传的属性不发送 | **写**：把已上传的媒体发布成帖子（需登录，且该上传属于你）→ post 对象，含 `id`、`rating`、`tag_string`、`source`；例 `client.post_create(55, tag_string='1girl solo', rating='g')` |
| `post_delete(post_id, reason, move_favorites=None)` | `post_id`：int 帖子编号；`reason`：str 删除理由，**必填**，空理由服务端回滚（删除会记成 post flag，必须有理由）；`move_favorites`：bool 把收藏转到父帖，不传时未规定 | **写**：按理由删除帖子（approver+，方法自带顶层 `commit=Delete`）→ 删除后的 post 对象；例 `client.post_delete(12090564, reason='版权投诉')` |
| `post_revert(post_id, version_id)` | `post_id`：int 帖子编号；`version_id`：int 要恢复到的 post_version 编号，来自 `post_versions_list` 的 `id` | **写**：把帖子恢复到某个版本（需登录）→ 回退后的 post 对象；例 `client.post_revert(12090564, version_id=88)` |
| `post_copy_notes(post_id, other_post_id)` | `post_id`：int 笔记来源帖编号；`other_post_id`：int 目标帖编号（顶层） | **写**：把笔记复制到另一帖（需登录）→ 成功是 `204` 空正文，本库返回 `None`；失败 `400` + `{"success": false, "reason": ...}`（抛 `AnybooruHTTPError`）；例 `client.post_copy_notes(12090564, other_post_id=12070768)` |
| `post_mark_as_translated(post_id, check_translation=None, partially_translated=None)` | `post_id`：int 帖子编号；`check_translation`：bool，加/删 `check_translation` 标签；`partially_translated`：bool，加/删 `partially_translated` 标签；不传的标签不动 | **写**：改翻译状态（需登录）→ 更新后的 post 对象，`tag_string` 里能看到这两个标签；例 `client.post_mark_as_translated(12090564, check_translation=False)` |
| `post_events_list(search=None, **params)` | `search`：dict，可筛 `post_id`、`category`、`event_at`、`creator_id`、`creator_name`、`order`；顶层 `post_id`：int 也能限定单个帖子；`limit`：int 每页条数 | 查帖子事件（标签、评分、来源等改动），匿名可读 → post_event 数组；例 `client.post_events_list(post_id=12090564, limit=10)` |
| `post_versions_list(search=None, **params)` | `search`：dict，可筛 `id`、`post_id`、`updater_id`、`updater_name`、`tags`、`added_tags`、`removed_tags`、`changed_tags`、`all_changed_tags`、`any_changed_tags`、`tag_matches`、`rating`、`parent_id`、`source`、`version`、`is_new`；`limit`：int 每页条数 | 查帖子版本，站点未配置 archive 服务时 `501`；**没有单版本的 JSON 路由** → post_version 数组，含 `id`、`post_id`、`updater_id`、`version`、`parent_changed`；例 `client.post_versions_list(search={'post_id': 12090564})` |
| `post_version_undo(version_id)` | `version_id`：int，要撤销的版本编号 | **写**：撤销某个版本带来的改动（需登录，未实测）→ 撤销后的 post_version 对象；例 `client.post_version_undo(88)` |
| `post_vote_show(vote_id)` | `vote_id`：int 投票编号，来自 `post_votes_list` 的 `id` | 读一条帖子投票，可见范围受限 → 单个 post_vote 对象，含 `id`、`post_id`、`user_id`、`score`；例 `client.post_vote_show(1234)` |
| `post_vote_delete(vote_id)` | `vote_id`：int 投票编号 | **写**：按投票编号撤回（需登录）；**没有按帖子撤票的路由**，要先 `post_votes_list(search={'post_id': ...})` 取 id → 被更新/删除后的 post_vote 对象；例 `client.post_vote_delete(1234)` |
| `post_favorites_list(post_id, search=None, **params)` | `post_id`：int 帖子编号；`search`：dict 可筛 `user_id` 等；`limit`：int 每页条数 | 读某帖的收藏记录，匿名可读 → favorite 数组，含 `id`、`post_id`、`user_id`；例 `client.post_favorites_list(12090564, limit=10)` |
| `post_replacements_list(search=None, **params)` | `search`：dict，可筛 `post_id`、`creator_id`、`creator_name`、`status`、`order`；顶层 `post_id`：int 也能限定单帖；`limit`：int 每页条数 | 查文件替换记录，匿名可读 → post_replacement 数组，含 `id`、`post_id`、`creator_id`、`original_url`、`replacement_url`；例 `client.post_replacements_list(post_id=12090564)` |
| `post_replacement_show(replacement_id)` | `replacement_id`：int，替换记录编号，来自 `post_replacements_list` 的 `id` | 读一次文件替换，匿名可读 → 单个 post_replacement 对象，含 `id`、`post_id`、`creator_id`、`original_url`、`replacement_url`；例 `client.post_replacement_show(77)` |
| `post_replacement_update(replacement_id, **attributes)` | `replacement_id`：int 替换记录编号；属性：`md5`、`file_ext`、`file_size`、`image_width`、`image_height`、`original_url`、`replacement_url` 及对应的 `old_*` 版本；不传的属性不动 | **写**：改替换记录的 MD5、尺寸与来源（需登录）→ 写后的 post_replacement 对象；例 `client.post_replacement_update(77, replacement_url='https://example.com/fixed.jpg')` |
| `post_regeneration_create(post_id, category=None)` | `post_id`：int 帖子编号（顶层）；`category`：str 取 `'post'`（原图）/ `'large'` / `'preview'`，不传时服务端默认（未规定具体值） | **写**：提交媒体重建任务（moderator）→ 提交重建的 post 对象；例 `client.post_regeneration_create(12090564, category='large')` |
| `post_approval_show(approval_id)` | `approval_id`：int 批准记录编号 | 读一条批准记录，匿名可读 → 单个 post_approval 对象，含 `id`、`user_id`、`post_id`；例 `client.post_approval_show(9)` |
| `post_approval_create(post_id)` | `post_id`：int 帖子编号（顶层） | **写**：批准一个帖子（approver+）→ 写后的 post_approval 对象，含 `id`、`user_id`、`post_id`；例 `client.post_approval_create(12090564)` |
| `post_disapprovals_list(search=None, **params)` | `search`：dict，可筛 `post_id`、`user_id`、`user_name`、`reason`、`message_matches`；`limit`：int 每页条数 | 查不批准记录，非 moderator 只看得到自己的 → post_disapproval 数组，含 `id`、`user_id`、`post_id`、`reason`、`message`；例 `client.post_disapprovals_list(search={'post_id': 12090564})` |
| `post_disapproval_show(disapproval_id)` | `disapproval_id`：int 记录编号 | 读一条不批准记录，可见范围受限 → 单个 post_disapproval 对象（`id`、`user_id`、`post_id`、`reason`、`message`）；例 `client.post_disapproval_show(5)` |
| `post_disapproval_create(post_id, **attributes)` | `post_id`：int 被不批准的帖子（放在 `post_disapproval[...]` 里）；`reason`：str，模型只接受 `disinterest` / `poor_quality` / `breaks_rules` 三种（源码 docstring 多写了 `borderline_quality`、`borderline_safety` 两个不存在的值）；`message`：str 可选补充说明，**最长 140 字符**，不传则只记理由 | **写**：记录不批准决定（approver+）→ 写后的 post_disapproval 对象（`id`、`user_id`、`post_id`、`reason`、`message`）；例 `client.post_disapproval_create(12090564, reason='poor_quality', message='分辨率过低')` |
| `post_disapproval_update(disapproval_id, **attributes)` | `disapproval_id`：int 记录编号；属性同 `post_disapproval_create`（`reason`、`message`） | **写**：修改不批准记录（需登录，未实测）→ 写后的对象；例 `client.post_disapproval_update(5, message='补充说明')` |
| `post_flag_show(flag_id)` | `flag_id`：int 标记编号 | 读一个待删标记，身份字段受限 → 单个 post_flag 对象（`id`、`post_id`、`creator_id`、`reason`、`is_resolved`）；例 `client.post_flag_show(31)` |
| `post_flag_create(post_id, reason, **attributes)` | `post_id`：int 帖子编号；`reason`：str 待删理由，必填 | **写**：为帖子提交待删理由（登录即可，**不等于删除**）→ 写后的 post_flag 对象；例 `client.post_flag_create(12090564, reason='疑似转载未授权')` |
| `post_flag_update(flag_id, reason, **attributes)` | `flag_id`：int 标记编号；`reason`：str 新理由，必填 | **写**：修改待处理标记的理由（本人且 pending）→ 写后的 post_flag 对象；例 `client.post_flag_update(31, reason='补充理由')` |
| `post_appeals_list(search=None, **params)` | `search`：dict，可筛 `id`、`post_id`、`reason_matches`、`status`、`creator_id`、`creator_name`；`limit`：int 每页条数 | 查帖子申诉，匿名可读 → post_appeal 数组，含 `id`、`post_id`、`creator_id`、`reason`、`status`；例 `client.post_appeals_list(search={'post_id': 12090564})` |
| `post_appeal_show(appeal_id)` | `appeal_id`：int 申诉编号 | 读一条申诉，可见范围受限 → 单个 post_appeal 对象（`id`、`post_id`、`creator_id`、`reason`、`status`）；例 `client.post_appeal_show(12)` |
| `post_appeal_create(post_id, reason, **attributes)` | `post_id`：int 被删除的帖子编号；`reason`：str 申诉理由，必填 | **写**：对被删除的帖子提出申诉（需登录）→ 写后的 post_appeal 对象；例 `client.post_appeal_create(12090564, reason='原图由本人绘制')` |
| `post_appeal_update(appeal_id, reason, **attributes)` | `appeal_id`：int 申诉编号；`reason`：str 新理由 | **写**：修改待处理申诉（本人且 pending）→ 写后的 post_appeal 对象；例 `client.post_appeal_update(12, reason='补充证明材料')` |

## 媒体资源与 AI 标签（6 个方法）

`media_assets` 是文件层面的资源记录（一个文件一条），字段按可见性裁剪；AI 候选标签来自站点的识别
服务，可以按帖子或媒体查。本组路由、凭据与参数键见
[附注的 媒体节](danbooru-contract-notes.md#sec-media)。

**常用方法**

**`media_assets_list(search=None, **params)`** — 查询媒体资源。给文件指纹（`md5`、`pixel_hash`）或尺寸、
状态等条件，返回 media_asset 数组，每项含 `id`、`md5`、`file_ext`、`file_size`、`image_width`、
`image_height`、`status`；对当前身份不可见的资产会省掉 `md5`、`file_key`、`variants`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    md5 = client.post_list(tags='rating:g', limit=1)[0]['md5']
    assets = client.media_assets_list(search={'md5': md5})
    # GET https://danbooru.donmai.us/media_assets.json?search%5Bmd5%5D=<md5>
    # 返回数组，每项含 id / md5 / file_ext / file_size / image_width / image_height / status
    print(assets[0]['id'], assets[0]['file_ext'], assets[0]['file_size'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`md5`、`pixel_hash`、`status`、`file_ext`、`file_size`、`image_width`、`image_height`、`duration`、`is_public`、`metadata`、`ai_tags_match`、`min_score`、`is_posted`、`order` | 资源过滤条件 | 列出可见的全部资源 | `search={'md5': '0f343b0931126a20f133d67c2b018a3b'}` |
| `limit` | int，服务端上限 200 | 每页条数 | 服务端默认每页 20 | `limit=50` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`ai_tags_list(search=None, **params)`** — 查询某个帖子或媒体的 AI 候选标签。给 `post_id`、
`media_asset_id`、`tag_name`、`score` 等条件，返回 ai_tag 数组，每项含 `media_asset_id`、`tag_id`、
`score`、`is_posted`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    tags = client.ai_tags_list(search={'post_id': post_id, 'is_posted': False}, limit=20)
    # GET https://danbooru.donmai.us/ai_tags.json?search%5Bpost_id%5D=<post_id>&search%5Bis_posted%5D=false&limit=20
    # 返回数组，每项含 media_asset_id / tag_id / score / is_posted
    print([(item['tag_id'], item['score']) for item in tags])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `media_asset_id`、`tag_id`、`tag_name`、`post_id`、`score`、`is_posted`、`order` | 候选标签过滤条件 | 列出可见的全部候选标签 | `search={'post_id': 12090564, 'is_posted': False}` |
| `limit` | int，服务端上限 200 | 每页条数 | 服务端默认每页 20 | `limit=20` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**本组其余 4 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `media_asset_show(media_asset_id)` | `media_asset_id`：int 媒体资源编号，来自 `media_assets_list` 的 `id`；路径变量，无其它参数 | 读一条媒体资源，匿名可读 → 单个 media_asset 对象；对当前身份不可见时省掉 `md5`、`file_key`、`variants`；例 `client.media_asset_show(987654)` |
| `media_asset_delete(media_asset_id)` | `media_asset_id`：int 媒体资源编号 | **写**：删除媒体资源 → 删除后的 media_asset 对象；客户端 docstring 写 moderator，上游 policy 实为 **admin**，以 admin 为准（见[附注矛盾项 5](danbooru-contract-notes.md#矛盾易错点与客户端取舍)）；例 `client.media_asset_delete(987654)` |
| `media_metadata_list(search=None, **params)` | `search`：dict，可筛 `media_asset_id`、`metadata`；`limit`：int 每页条数 | 查媒体资源的附加快照信息（media_metadata 记录），匿名可读 → media_metadata 数组，含 `id`、`media_asset_id`、`metadata`；例 `client.media_metadata_list(search={'media_asset_id': 987654})` |
| `ai_tag_tag(media_asset_id, tag_id, tag=None, mode=None)` | `media_asset_id`：int 媒体资源编号；`tag_id`：int AI 标签编号，来自 `ai_tags_list` 的 `tag_id`；`tag`：str 改用这个名字而不是 AI 自己的名字，不传则用 AI 标签名；`mode`：str 传 `'remove'` 表示撤下这个标签，不传表示应用 | **写**：把 AI 候选标签应用到帖子（需登录，且对该帖有编辑权限）→ 被更新的 ai_tag 对象，同时会改动对应帖子的标签；例 `client.ai_tag_tag(987654, 456, mode='remove')` |

## 上传与上传媒体（6 个方法）

上传新帖分两步：`upload_create` 建上传（**唯一用于上传新媒体的 multipart 端点**；另一条 multipart 是
`post_replacement_create` 的 `replacement_file`），再用返回的 `upload_media_assets[0]['id']` 调
`post_create(upload_media_asset_id, ...)` 发布。`files` 与 `source` 互斥，至少给一个；压缩包由服务端
展开，单次上传文件数上限 100。本组路由、凭据与参数键见
[附注的 上传节](danbooru-contract-notes.md#sec-uploads)。

**常用方法**

**`upload_create(files=None, source=None, referer_url=None)`** — 从本地文件或来源 URL 建上传（需登录）。
至少给 `files` 或 `source` 之一：本地文件走 multipart 字面键 `upload[files][0]`、`upload[files][1]`…，
来源 URL 让服务端自己去下载。返回 upload 对象（`id`、`source`、`status`、`media_asset_count` 等），
并带上 `upload_media_assets` 关联数组。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    upload = client.upload_create(source='https://example.com/a.jpg')
    # POST https://danbooru.donmai.us/uploads.json
    # 请求体 {"upload": {"source": "https://example.com/a.jpg"}}；None 值的 referer_url 不会发送。
    # 返回 upload 对象：id / source / status / media_asset_count + upload_media_assets 关联数组
    upload_media_asset_id = upload['upload_media_assets'][0]['id']
    post = client.post_create(upload_media_asset_id, tag_string='1girl solo', rating='g')
    # POST https://danbooru.donmai.us/posts.json
    # 请求体 {"post": {"tag_string": "1girl solo", "rating": "g"}, "upload_media_asset_id": 55}
    # 返回 post 对象：id / rating / tag_string / source
    print(post['id'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `files` | list，元素是**以二进制打开**的文件对象，按顺序上传 | 本地文件，按顺序发成 `upload[files][0]`、`upload[files][1]`…；文件对象的生命周期由调用者负责（调用后自己 `close()`） | 不发文件，必须改用 `source` | `files=[open('a.jpg', 'rb')]` |
| `source` | str，来源 URL | 让服务端去下载这个地址 | 不发来源，必须改用 `files` | `source='https://example.com/a.jpg'` |
| `referer_url` | str | `source` 的 referer，给需要它的私有站点用 | 不发送 | `referer_url='https://private.example.com/page'` |

**`upload_list(search=None, **params)`** — 查询当前用户可见的上传记录。非 moderator 只能看到自己的；
返回 upload 数组（含 `id`、`source`、`uploader_id`、`status`、`referer_url`、`media_asset_count`）。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    uploads = client.upload_list(limit=10)
    # GET https://danbooru.donmai.us/uploads.json?limit=10
    # 返回数组，每项含 id / source / uploader_id / status / referer_url / media_asset_count
    print([(item['id'], item['status']) for item in uploads])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`source`、`referer_url`、`status`、`media_asset_count`、`uploader_id`、`uploader_name`、`ai_tags_match`、`min_score`、`is_posted`、`any_source_matches`、`order` | 上传记录过滤条件 | 列出可见的全部上传 | `search={'status': 'completed'}` |
| `user_id` | int | 只看某个上传者的上传（顶层参数） | 不限定上传者 | `client.upload_list(user_id=42)` |
| `limit` | int，服务端钳到 `0..200` | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**本组其余 4 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `upload_show(upload_id)` | `upload_id`：int 上传编号，来自 `upload_create` 或 `upload_list` 的 `id` | 读一次上传的处理状态与关联媒体（需登录，本人或 moderator）→ 单个 upload 对象，含 `id`、`source`、`uploader_id`、`status`、`referer_url`，并内嵌 `upload_media_assets`；例 `client.upload_show(123)` |
| `upload_assets_list(upload_id, search=None, **params)` | `upload_id`：int 上传编号；`search`：dict 可筛 `id`、`status`、`source_url`、`page_url`、`error`、`media_asset_id`、`post_id`、`is_posted`、`order`；`limit`：int 每页条数（服务端默认 200） | 列出一次上传关联的媒体 → upload_media_asset 数组，含 `id`、`media_asset_id`、`status`、`post_id`、`page_url`、`error`；例 `client.upload_assets_list(123)` |
| `upload_media_assets_list(search=None, **params)` | `search`：dict，可筛 `id`、`status`、`source_url`、`page_url`、`error`、`upload_id`、`media_asset_id`、`post_id`、`is_posted`、`order`；`limit`：int 每页条数（服务端上限 200） | 查上传媒体记录 → upload_media_asset 数组，字段同上；例 `client.upload_media_assets_list(search={'upload_id': 123})` |
| `upload_media_asset_show(upload_media_asset_id)` | `upload_media_asset_id`：int 上传媒体编号，来自 upload 响应里 `upload_media_assets[0]['id']` | 读一条上传媒体记录 → 单个 upload_media_asset 对象，含 `id`、`upload_id`、`media_asset_id`、`status`、`source_url`、`page_url`，已发布时含 `post_id`；例 `client.upload_media_asset_show(55)` |

## tags、别名、蕴含与相关标签（13 个方法）

创建别名与蕴含没有专用方法，要走 `bulk_update_request_create`；`tag_alias_delete` /
`tag_implication_delete` 的语义是**拒绝请求**，不是删除既有关系。本组路由、凭据与参数键见
[附注的 tags 节](danbooru-contract-notes.md#sec-tags)。

**常用方法**

**`tag_list(search=None, **params)`** — 搜索标签。`search` 里放过滤条件（名称匹配、类别、`post_count`、
排序等），返回 tag 数组，每项含 `id`、`name`、`post_count`、`category`、`is_deprecated`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    tags = client.tag_list(search={'name_matches': 'touhou', 'order': 'count'}, limit=2)
    # GET https://danbooru.donmai.us/tags.json?search%5Bname_matches%5D=touhou&search%5Border%5D=count&limit=2
    # 返回数组，每项含 id / name / post_count / category / is_deprecated
    print([(tag['id'], tag['name'], tag['post_count']) for tag in tags])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`name`、`name_matches`、`name_normalize`、`name_or_alias_matches`、`fuzzy_name_matches`、`category`（`0` 通用 / `1` 画师 / `3` 版权 / `4` 角色 / `5` 元标签）、`is_deprecated`、`post_count`、`is_empty`、`hide_empty`、`has_wiki_page`、`has_artist`、`has_antecedent_alias`、`has_consequent_aliases`、`order`（`name` / `date` / `count` / `similarity`） | 标签过滤条件 | 列出标签全集，按服务端默认排序 | `search={'name_matches': 'touhou'}` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=2` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

JSON 下 `hide_empty` **没有默认值**：不传就不过滤空标签，只有显式传 `True` 才走 `nonempty`
（HTML 页面才有默认过滤）。

**`related_tag(search=None, **params)`** — 根据标签查询取相关标签建议。`search['query']` 必填，
返回**一个对象**而不是数组：`query`、`post_count`、`tag`、`related_tags`（每项含 `tag` 与共现统计）、
`wiki_page_tags`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    related = client.related_tag(search={'query': 'touhou', 'order': 'frequency'}, limit=5)
    # GET https://danbooru.donmai.us/related_tag.json?search%5Bquery%5D=touhou&search%5Border%5D=frequency&limit=5
    # 返回对象：query / post_count / tag / related_tags（每项含 tag）/ wiki_page_tags
    print(related['query'], related['post_count'])
    print([item['tag']['name'] for item in related['related_tags']])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['query']` | str，标签查询串，如 `'touhou'`、`'pixiv rating:g'` | 基于哪些标签找相关标签 | **必填**，不给会被服务端拒绝 | `search={'query': 'touhou'}` |
| `search['category']` / `search['categories']` | int 或 str，标签类别，如 `0`、`'general'`、逗号/空格分隔多个 | 只统计这些类别的标签 | 不限类别 | `search={'query': 'touhou', 'category': 0}` |
| `search['order']` | str，`frequency`（默认）/ `cosine` / `jaccard` / `overlap`；其它值一律按 `frequency` 处理 | 相关度排序方式 | `frequency` | `search={'query': 'touhou', 'order': 'cosine'}` |
| `search['search_sample_size']` | int，服务端钳到 `0..100000` | 参与统计的查询样本量 | 服务端默认 5000（传 0 也回到 5000） | `search={'query': 'touhou', 'search_sample_size': 1000}` |
| `search['tag_sample_size']` | int，服务端钳到 `0..1000` | 每个样本统计的标签量 | 服务端默认 500（传 0 也回到 500） | `search={'query': 'touhou', 'tag_sample_size': 100}` |
| `limit` | int，服务端钳到 `0..1000` | 返回多少个相关标签（顶层参数） | 服务端默认 100 | `limit=5` |
| `media_asset_id` | int，媒体资源编号 | 改用该媒体的 AI 标签做查询（顶层参数，替代 `query`） | 用 `search['query']` | `client.related_tag(media_asset_id=987654)` |

**本组其余 11 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `tag_show(tag_id)` | `tag_id`：int 标签编号，如 `29`（`touhou` 的编号），来自 `tag_list` 的 `id` | 读标签详情，匿名可读 → 单个 tag 对象，含 `id`、`name`、`post_count`、`category`、`is_deprecated`；例 `client.tag_show(29)` |
| `tag_update(tag_id, **attributes)` | `tag_id`：int 标签编号；`category`：int `0` 通用 / `1` 画师 / `3` 版权 / `4` 角色 / `5` 元标签（改它要 Builder 及以上）；`is_deprecated`：bool（Builder 及以上）；不传的属性不动 | **写**：改获授权的标签属性（需登录）→ 写后的 tag 对象；例 `client.tag_update(29, is_deprecated=True)` |
| `tag_versions_list(search=None, **params)` | `search`：dict，可筛 `tag_id`、`updater_id`、`updater_name`、`name_matches`、`category`、`is_deprecated`、`version`、`order`（`created_at` / `updated_at` / `id` 及 `_asc` 形式）；`limit`：int 每页条数 | 查标签修改历史，匿名可读 → tag_version 数组，含 `id`、`tag_id`、`updater_id`、`previous_version_id`、`version`；例 `client.tag_versions_list(search={'tag_id': 29})` |
| `tag_version_show(version_id)` | `version_id`：int 版本编号，来自 `tag_versions_list` 的 `id` | 读一个标签版本 → 单个 tag_version 对象，含 `id`、`tag_id`、`updater_id`、`previous_version_id`、`version`；例 `client.tag_version_show(456)` |
| `tag_aliases_list(search=None, **params)` | `search`：dict，可筛 `id`、`antecedent_name`、`consequent_name`、`name_matches`、`antecedent_name_matches`、`consequent_name_matches`、`status`（`active` / `deleted` / `retired`）、`category`、`creator_id`、`creator_name`、`approver_id`、`forum_topic_id`、`order`（`created_at` / `updated_at` / `name` / `antecedent_tag_count` / `consequent_tag_count`）；`limit`：int 每页条数 | 查标签别名关系，匿名可读 → tag_alias 数组，含 `id`、`antecedent_name`、`consequent_name`、`status`、`creator_id`、`forum_topic_id`；例 `client.tag_aliases_list(search={'consequent_name': 'touhou'})` |
| `tag_alias_show(tag_alias_id)` | `tag_alias_id`：int 别名记录编号 | 读一条别名关系 → 单个 tag_alias 对象，字段同上；例 `client.tag_alias_show(19)` |
| `tag_alias_delete(tag_alias_id)` | `tag_alias_id`：int 别名请求编号 | **写**：**拒绝**一条别名请求（需登录；语义是拒绝，不是删除既有别名）→ 被更新/删除后的 tag_alias 对象，`status` 会变成 `rejected`；例 `client.tag_alias_delete(19)` |
| `tag_implications_list(search=None, **params)` | `search`：dict，可筛 `id`、`antecedent_name`、`consequent_name`、`name_matches`、`antecedent_name_matches`、`consequent_name_matches`、`status`、`category`、`creator_id`、`creator_name`、`approver_id`、`forum_topic_id`、`implied_from`、`implied_to`、`order`；`limit`：int 每页条数 | 查标签蕴含关系，匿名可读 → tag_implication 数组，含 `id`、`antecedent_name`、`consequent_name`、`status`、`forum_topic_id`；例 `client.tag_implications_list(search={'antecedent_name': '1girl'})` |
| `tag_implication_show(tag_implication_id)` | `tag_implication_id`：int 蕴含记录编号 | 读一条蕴含关系 → 单个 tag_implication 对象，字段同上；例 `client.tag_implication_show(23)` |
| `tag_implication_delete(tag_implication_id)` | `tag_implication_id`：int 蕴含请求编号 | **写**：拒绝一条蕴含请求（需登录）→ 被更新/删除后的 tag_implication 对象；例 `client.tag_implication_delete(23)` |
| `autocomplete_list(query, type=None, limit=None)` | `query`：str 要补全的文本，如 `'touh'`（放进 `search[query]`）；`type`：str 取 `tag`（默认）/ `tag_query` / `artist` / `wiki_page` / `user` / `pool` / `comment` / `saved_search`，不传即 `tag`；`limit`：int 最多几条，不传时服务端默认 10 | 取输入补全建议，匿名可读 → 结果数组，元素形状随 `type` 不同（`tag` 给标签名与 `post_count`）；例 `client.autocomplete_list('touh', type='tag', limit=5)` |

<a id="artists"></a>

## artists（画师与主页记录）— 18 个方法

画师记录里的 `name` 是与作品上的画师标签对应的名称，**不是**外部站点的作者 ID；主页地址是独立的
`artist_urls` 记录。`search['url_matches']` 由服务端归一化后匹配：完整 `https://` 地址会先按来源解析
成规范主页地址，也接受 `/正则/`、含 `*` 的通配与普通子串。本组路由、凭据与参数键见
[附注的 artists 节](danbooru-contract-notes.md#sec-artists)。

**常用方法**

**`artist_list(search=None, **params)`** — 按名称、主页 URL、是否封禁等条件搜索画师。返回 artist 数组，
每项含 `id`、`name`、`is_banned`、`is_deleted`、`group_name`、`other_names`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    artists = client.artist_list(search={'url_matches': 'https://www.pixiv.net/users/27517',
                                         'has_tag': True, 'order': 'name'})
    # GET https://danbooru.donmai.us/artists.json?search%5Burl_matches%5D=https%3A%2F%2Fwww.pixiv.net%2Fusers%2F27517&search%5Bhas_tag%5D=true&search%5Border%5D=name
    # 返回数组，每项含 id / name / is_banned / is_deleted / group_name / other_names
    print([(artist['id'], artist['name']) for artist in artists])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`name`、`name_like` / `name_ilike` / `name_regex`、`any_name_matches`（名称/其他名/团体名，支持 `*` 与 `/正则/`）、`any_name_or_url_matches`、`any_other_name_like`、`url_matches`（主页 URL、域名、`*foo*` 或 `/正则/`）、`group_name`、`other_names_include_any`、`is_deleted`、`is_banned`、`has_urls`、`has_wiki_page`、`has_tag_alias`、`has_tag`、`order`（`name` / `updated_at` / `post_count`） | 画师过滤条件 | 列出全部画师 | `search={'has_tag': True, 'order': 'name'}` |
| `name` | str，精确名字，也接受逗号分隔多个 | `search['name']` 的简写（顶层参数） | 不按名字过滤 | `client.artist_list(name='fuzichoco')` |
| `limit` | int | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`artist_show_or_new(name=None)`** — 按名称查画师，未找到时返回新记录形态。名字已存在时服务端 `302`
到该画师；客户端带 `Accept: application/json` 跟随重定向，拿到的仍是该画师的 JSON（已实测）。名字不
存在时返回一个未保存的 artist 对象（`id` 为 `null`，带 `name`），可以拿它做创建前的预填。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    artist = client.artist_show_or_new(name='fuzichoco')
    # GET https://danbooru.donmai.us/artists/show_or_new.json?name=fuzichoco
    # 302 → https://danbooru.donmai.us/artists/show_or_new.json?...（目标仍是 JSON）
    # 返回单个 artist 对象：id / name / is_banned / group_name / other_names
    print(artist['id'], artist['name'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `name` | str，画师名 | 按名字定位 | `None` 或空串会重定向到“新建画师”入口，受该路由权限约束 | `client.artist_show_or_new(name='fuzichoco')` |

**本组其余 16 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `artist_show(artist_id)` | `artist_id`：int 画师编号，如 `8704`（`fuzichoco` 的编号），来自 `artist_list` 的 `id` | 读一个画师记录，匿名可读 → 单个 artist 对象，含 `id`、`name`、`is_banned`、`group_name`、`other_names`；例 `client.artist_show(8704)` |
| `artist_create(name, **attributes)` | `name`：str 主名称，也是将来的标签名，必填；`other_names`（list）/ `other_names_string`（str）：其他名；`group_name`：str 团体名；`url_string`：str 空格分隔的主页地址；`is_deleted`：bool 建成就标记删除；`source`：str 用来预填主页地址的来源；不传的属性不发送 | **写**：创建画师（需登录）→ 写后的 artist 对象；例 `client.artist_create('fuzichoco', url_string='https://www.pixiv.net/users/27517')` |
| `artist_update(artist_id, **attributes)` | `artist_id`：int 画师编号；属性同 `artist_create`（`other_names_string`、`group_name`、`url_string` 等） | **写**：改名称、其他名、团体与主页（需登录）→ 写后的 artist 对象；例 `client.artist_update(8704, group_name='')` |
| `artist_delete(artist_id)` | `artist_id`：int 画师编号 | **写**：软删除画师（置 `is_deleted`，需 builder）；服务端重定向到画师页，客户端跟随；最终响应不是 JSON 会抛 `AnybooruAPIError`，重定向是否成功未实测 → 最终响应对象；例 `client.artist_delete(8704)` |
| `artist_revert(artist_id, version_id)` | `artist_id`：int 画师编号；`version_id`：int 要恢复到的版本编号，来自 `artist_versions_list` 的 `id` | **写**：恢复画师记录的指定版本（需登录）→ 写后的 artist 对象；例 `client.artist_revert(8704, version_id=158)` |
| `artist_ban(artist_id)` | `artist_id`：int 画师编号 | **写**：封禁画师（admin）；服务端重定向到画师页，最终响应决定结果（未实测）→ 最终响应对象；例 `client.artist_ban(8704)` |
| `artist_unban(artist_id)` | `artist_id`：int 画师编号 | **写**：解除画师封禁（admin）；重定向同上 → 最终响应对象；例 `client.artist_unban(8704)` |
| `artist_urls_list(search=None, **params)` | `search`：dict，可筛 `id`、`artist_id`、`url`、`url_matches`（匹配规则同画师搜索）、`is_active`、`has_artist`、`order`（`id` / `artist_id` / `url` / `is_active` / `created_at` / `updated_at` 及 `_asc`）；`limit`：int 每页条数 | 查画师关联的主页地址记录 → artist_url 数组，含 `id`、`artist_id`、`url`、`is_active`；例 `client.artist_urls_list(search={'artist_id': 8704})` |
| `artist_versions_list(search=None, **params)` | `search`：dict，可筛 `artist_id`、`updater_id`、`updater_name`、`name`、`group_name`、`other_names_include_any`、`is_deleted`、`is_banned`、`order`（`id` / `created_at` / `updated_at` / `name` 及 `_asc`）；`limit`：int 每页条数 | 查画师记录修改历史 → artist_version 数组，含 `id`、`artist_id`、`name`、`updater_id`、`group_name`；例 `client.artist_versions_list(search={'artist_id': 8704})` |
| `artist_version_show(version_id)` | `version_id`：int 版本编号 | 读一个画师记录版本 → 单个 artist_version 对象（`id`、`artist_id`、`name`、`updater_id`、`group_name`）；例 `client.artist_version_show(158)` |
| `artist_commentaries_list(search=None, **params)` | `search`：dict，可筛 `post_id`、`original_title`、`original_description`、`translated_title`、`translated_description`、`text_matches`、`original_present`、`translated_present`、`is_deleted`、`order`（`post_id` / `updated_at` / `id` 及 `_asc`）；`limit`：int 每页条数 | 搜索作品的原作者说明与译文 → artist_commentary 数组，含 `id`、`post_id`、`original_title`、`original_description`、`translated_title`；例 `client.artist_commentaries_list(search={'original_present': True})` |
| `artist_commentary_show(post_id)` | `post_id`：int 帖子编号 | 读某帖的原作者说明，匿名可读 → 该帖的 artist_commentary 对象（没有说明时服务端返回 `404`）；例 `client.artist_commentary_show(12090564)` |
| `artist_commentary_create_or_update(post_id, **attributes)` | `post_id`：int 帖子编号（从路由取）；`original_title` / `original_description` / `translated_title` / `translated_description`：str；`commentary_tags`：str；不传的字段保持原值 | **写**：创建或更新某帖说明与翻译（需登录，用 PUT）→ 该帖的 artist_commentary 对象；例 `client.artist_commentary_create_or_update(12090564, translated_title='标题')` |
| `artist_commentary_revert(post_id, version_id)` | `post_id`：int 帖子编号（**路径里的 id 就是 post_id**，不是说明 id）；`version_id`：int 要恢复到的说明版本编号 | **写**：恢复说明的指定版本（需登录）→ 写后的 artist_commentary 对象；例 `client.artist_commentary_revert(12090564, version_id=302)` |
| `artist_commentary_versions_list(search=None, **params)` | `search`：dict，可筛 `post_id`、`updater_id`、`updater_name`、`text_matches`、`original_title`、`original_description`、`translated_title`、`translated_description`；`limit`：int 每页条数 | 查说明修改历史 → artist_commentary_version 数组，含 `id`、`post_id`、`updater_id`、`original_title`、`original_description`；例 `client.artist_commentary_versions_list(search={'post_id': 12090564})` |
| `artist_commentary_version_show(version_id)` | `version_id`：int 说明版本编号 | 读一个说明版本 → 单个 artist_commentary_version 对象（`id`、`post_id`、`updater_id`、`original_title`、`original_description`）；例 `client.artist_commentary_version_show(302)` |

## comments（评论与评论投票）— 10 个方法

非 moderator 看已删除评论时，正文、投票分与作者字段会被服务端省掉，按这些字段检索也受限（只能查到
“自己的已删评论 + 全部未删除”）。本组路由、凭据与参数键见
[附注的 comments 节](danbooru-contract-notes.md#sec-comments)。

**常用方法**

**`comment_list(search=None, **params)`** — 搜索或列出评论。返回 comment 数组，每项含 `id`、`post_id`、
`creator_id`、`body`、`score`、`is_deleted`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    comments = client.comment_list(search={'post_id': post_id}, limit=10)
    # GET https://danbooru.donmai.us/comments.json?search%5Bpost_id%5D=<post_id>&limit=10
    # 返回数组，每项含 id / post_id / creator_id / body / score / is_deleted
    print([(comment['id'], comment['score']) for comment in comments])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`body_matches`、`post_id`、`post_tags_match`、`creator_id`、`creator_name`、`updater_id`、`is_deleted`、`is_sticky`、`do_not_bump_post`、`score`、`is_edited`、`order` | 评论过滤条件 | 列出全部可见评论（最新在前） | `search={'post_id': 12090564}` |
| `group_by` | str，`'comment'`（默认：**带 `search` 时**服务端自动补上，按评论时间）/ `'post'`（按最新被评论的帖子）；不传 `search` 且不传 `group_by` 时服务端走 `index_by_post`，返回的是**帖子列表**而不是评论 | 结果分组方式（顶层参数） | 带 `search` 时为 `'comment'`；否则按帖子分组 | `client.comment_list(group_by='post', limit=10)` |
| `limit` | int | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`comment_show(comment_id)`** — 读一条评论。给评论编号，返回单个 comment 对象，字段同上；评论已删除
且当前身份看不到时，响应会省掉 `body`、`score`、`creator_id`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    # 带 search 时 group_by 默认 comment，返回的是评论；不带 search 返回的是帖子列表
    comment_id = client.comment_list(search={'is_deleted': False}, limit=1)[0]['id']
    comment = client.comment_show(comment_id)
    # GET https://danbooru.donmai.us/comments/<comment_id>.json
    # 返回单个对象：id / post_id / creator_id / body / score / is_deleted
    print(comment['id'], comment['body'][:40])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `comment_id` | int 评论编号 | 要读哪条评论，会进 URL 路径 | 必填 | `client.comment_show(3456789)` |

**本组其余 8 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `comment_create(post_id, body, **attributes)` | `post_id`：int 帖子编号；`body`：str 正文，DText 格式，必填；`do_not_bump_post`：bool 不把帖子顶到评论列表前面，不传即会顶；`is_sticky`：bool 置顶（需 moderator） | **写**：在帖子下发表评论（需登录）→ 写后的 comment 对象，含 `id`、`post_id`、`creator_id`、`body`、`score`；例 `client.comment_create(post_id=12090564, body='画得很细腻')` |
| `comment_update(comment_id, **attributes)` | `comment_id`：int 评论编号；`body`：str 新正文；`is_deleted`：bool 标记删除；`is_sticky`：bool 置顶（需 moderator） | **写**：改正文、删除标记或置顶（需登录，作者或 moderator）→ 写后的 comment 对象；例 `client.comment_update(3456789, body='更正：已找到来源')` |
| `comment_delete(comment_id)` | `comment_id`：int 评论编号 | **写**：软删除评论（需登录，作者或 moderator）→ 被更新/删除后的 comment 对象；例 `client.comment_delete(3456789)` |
| `comment_undelete(comment_id)` | `comment_id`：int 评论编号 | **写**：恢复已删除评论（需 moderator）→ 恢复后的 comment 对象；例 `client.comment_undelete(3456789)` |
| `comment_votes_list(search=None, **params)` | `search`：dict，可筛 `comment_id`、`user_id`、`user_name`、`score`（`1` / `-1`）、`is_deleted`；顶层 `comment_id`：int 也兼容；`limit`：int 每页条数 | 查评论投票 → comment_vote 数组，含 `id`、`comment_id`、`user_id`、`score`；例 `client.comment_votes_list(search={'comment_id': 3456789})` |
| `comment_vote_show(vote_id)` | `vote_id`：int 投票编号，来自 `comment_votes_list` 的 `id` | 读一条评论投票，可见范围受限 → 单个 comment_vote 对象（`id`、`comment_id`、`user_id`、`score`）；例 `client.comment_vote_show(7654321)` |
| `comment_vote_create(comment_id, score)` | `comment_id`：int 评论编号；`score`：int，只接受 `1`（赞）/ `-1`（踩）——模型校验是 `[1, -1]`，docstring 写的 `'up'` / `'down'` 不合法 | **写**：给评论投票（需登录）→ 新建的 comment_vote 对象；例 `client.comment_vote_create(3456789, score=1)` |
| `comment_vote_delete(vote_id)` | `vote_id`：int 投票编号 | **写**：撤票只能用投票编号（需登录；**没有按评论撤票的路由**）→ 被更新/删除后的 comment_vote 对象；例 `client.comment_vote_delete(7654321)` |

## notes（图上笔记与笔记历史）— 9 个方法

笔记正文是 DText；坐标单位是像素（`x` / `y` 是左上角偏移，`width` / `height` 是宽高）。创建与更新
失败时服务端返回 `422` + `{"success": false, "reasons": [...]}`。`note_list` **没有** `creator_id` /
`creator_name` 过滤参数，写了会被静默忽略。本组路由、凭据与参数键见
[附注的 notes 节](danbooru-contract-notes.md#sec-notes)。

**常用方法**

**`note_list(search=None, **params)`** — 查询图上笔记。返回 note 数组，每项含 `id`、`post_id`、`x`、
`y`、`width`、`height`、`body`、`is_active`、`version`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    notes = client.note_list(search={'post_id': post_id, 'is_active': True})
    # GET https://danbooru.donmai.us/notes.json?search%5Bpost_id%5D=<post_id>&search%5Bis_active%5D=true
    # 返回数组，每项含 id / post_id / x / y / width / height / body / is_active / version
    print([(note['id'], note['x'], note['y']) for note in notes])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`post_id`、`post_tags_match`、`body_matches`、`is_active`、`x`、`y`、`width`、`height`、`version` | 笔记过滤条件；**没有** `creator_id` / `creator_name` | 列出全部可见笔记 | `search={'post_id': 12090564, 'is_active': True}` |
| `limit` | int | 每页条数 | 服务端默认每页 20 | `limit=20` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`note_preview(body)`** — 给笔记的 HTML 正文，返回清理后的 `sanitized_body`，可以先看显示结果再决定是否保存。
这个 POST 只预览、不保存；业务权限允许匿名，但本轮匿名 POST 被 CSRF 校验拒绝（403），尚未取得成功预览。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    preview = client.note_preview('<b>说明</b>')
    # POST https://danbooru.donmai.us/notes/preview.json
    # JSON 请求体 {"body": "<b>说明</b>"}；返回 sanitized_body，不创建或修改笔记。
    print(preview['sanitized_body'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `body` | str，笔记 HTML 正文 | 要预览的文字和 HTML | 必填 | `client.note_preview('<b>说明</b>')` |

**本组其余 7 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `note_show(note_id)` | `note_id`：int 笔记编号，来自 `note_list` 的 `id` | 读一个笔记，匿名可读 → 单个 note 对象，含 `id`、`post_id`、`x`、`y`、`width`、`height`、`body`、`is_active`；例 `client.note_show(12345)` |
| `note_create(post_id, x, y, width, height, body, **attributes)` | `post_id`：int 帖子编号；`x` / `y`：int 左上角偏移像素；`width` / `height`：int 笔记宽高像素；`body`：str DText 正文；`html_id`：str 客户端元素 id，用于对上响应，不传不发送 | **写**：在指定帖子与坐标创建笔记（需登录）；失败 `422` → 写后的 note 对象；例 `client.note_create(12090564, 10, 20, 100, 60, '角色名')` |
| `note_update(note_id, **attributes)` | `note_id`：int 笔记编号；`x` / `y` / `width` / `height`：int 新几何值；`body`：str 新正文 | **写**：改位置、尺寸或正文（需登录）→ 写后的 note 对象；例 `client.note_update(12345, x=30, y=40)` |
| `note_delete(note_id)` | `note_id`：int 笔记编号 | **写**：停用笔记（置 `is_active=false`，需登录）→ 被更新/删除后的 note 对象；例 `client.note_delete(12345)` |
| `note_revert(note_id, version_id)` | `note_id`：int 笔记编号；`version_id`：int 要恢复到的版本编号 | **写**：恢复笔记的指定版本（需登录）→ 写后的 note 对象；例 `client.note_revert(12345, version_id=678)` |
| `note_versions_list(search=None, **params)` | `search`：dict，可筛 `note_id`、`post_id`、`updater_id`、`is_active`、`x`、`y`、`width`、`height`、`body`、`version`；`limit`：int 每页条数 | 查笔记修改历史 → note_version 数组，含 `id`、`note_id`、`post_id`、`updater_id`、`x`、`y`、`width`、`height`；例 `client.note_versions_list(search={'note_id': 12345})` |
| `note_version_show(version_id)` | `version_id`：int 版本编号 | 读一个笔记版本 → 单个 note_version 对象，字段同上；例 `client.note_version_show(678)` |

## pools（合集）— 11 个方法

`post_ids` 就是帖子编号数组；`pool_update` 传显式空数组会真的发出 `[]`（用于清空合集内容，表单编码
丢不掉它）。合集有两个类别：`series`（系列）与 `collection`（集合）。本组路由、凭据与参数键见
[附注的 pools 节](danbooru-contract-notes.md#sec-pools)。

**常用方法**

**`pool_list(search=None, **params)`** — 搜索合集。返回 pool 数组，每项含 `id`、`name`、`description`、
`category`、`is_active`、`is_deleted`、`post_ids`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    pools = client.pool_list(search={'name_matches': 'touhou'}, limit=5)
    # GET https://danbooru.donmai.us/pools.json?search%5Bname_matches%5D=touhou&limit=5
    # 返回数组，每项含 id / name / description / category / is_active / post_ids
    print([(pool['id'], pool['name'], len(pool['post_ids'])) for pool in pools])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`name`、`name_matches`、`name_contains`、`description_matches`、`post_ids`、`is_deleted`、`category`（`series` / `collection`）、`post_tags_match`、`linked_to`、`not_linked_to`、`order`（`name` / `created_at` / `post_count`） | 合集过滤条件 | 列出全部合集 | `search={'name_matches': 'touhou'}` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=5` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`pool_show(pool_id)`** — 读合集及其帖子编号列表。返回单个 pool 对象，`post_ids` 是整数数组，按合集
内顺序排列，可直接拿去 `post_show` 或当 `post_list(tags='id:...')` 的输入。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    pool_id = client.pool_list(search={'name_matches': 'touhou'}, limit=1)[0]['id']
    pool = client.pool_show(pool_id)
    # GET https://danbooru.donmai.us/pools/<pool_id>.json
    # 返回单个对象：id / name / description / category / is_active / post_ids
    print(pool['name'], len(pool['post_ids']))
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `pool_id` | int 合集编号 | 要读哪个合集，会进 URL 路径 | 必填 | `client.pool_show(12345)` |
| `page` / `limit` | int | 分页读 `post_ids`（用 `request('GET', 'pools/<id>.json', params={'page': 2})` 传，本方法签名没有这两个形参） | 第一页、服务端默认条数 | `request('GET', 'pools/12345.json', params={'page': 2})` |

**本组其余 9 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `pool_create(name, **attributes)` | `name`：str 合集名，必填；`description`：str DText 说明；`category`：`series` / `collection`；`post_ids_string`：str 空格分隔的初始帖子编号；`post_ids`：list 初始帖子编号 | **写**：创建合集（需登录）→ 写后的 pool 对象；例 `client.pool_create('东方 Project', category='series', post_ids=[12090564])` |
| `pool_update(pool_id, **attributes)` | `pool_id`：int 合集编号；属性同 `pool_create`（`name`、`description`、`category`、`post_ids` / `post_ids_string`）；传 `post_ids=[]` 会真的发空数组，即清空合集内容 | **写**：修改说明或帖子成员（需登录）→ 写后的 pool 对象；例 `client.pool_update(12345, post_ids=[12090564, 12070768])` |
| `pool_delete(pool_id)` | `pool_id`：int 合集编号 | **写**：软删除合集（需 builder）→ 被更新/删除后的 pool 对象，`is_deleted` 变 `true`；例 `client.pool_delete(12345)` |
| `pool_undelete(pool_id)` | `pool_id`：int 合集编号 | **写**：恢复已删除合集（需 moderator）→ 写后的 pool 对象；例 `client.pool_undelete(12345)` |
| `pool_revert(pool_id, version_id)` | `pool_id`：int 合集编号；`version_id`：int 要恢复到的版本编号，来自 `pool_versions_list` 的 `id` | **写**：恢复合集的指定版本（需登录）→ 写后的 pool 对象；例 `client.pool_revert(12345, version_id=88)` |
| `pool_gallery(search=None, **params)` | `search`：dict 搜索条件（服务端默认 `{"category": "series"}`）；`limit`：int 每页条数 | 合集画廊，匿名可读 → pool 数组，每项带一张预览帖（`post_ids` 只含预览帖）；例 `client.pool_gallery(limit=10)` |
| `pool_element_create(post_id, pool_id=None, pool_name=None)` | `post_id`：int 要加入的帖子（顶层）；`pool_id`：int 目标合集编号；`pool_name`：str 目标合集名；`pool_id` 与 `pool_name` 二选一，都不给时未规定 | **写**：向合集加入帖子（需登录，且对该合集有更新权限）→ 加入后所属的 pool 对象；例 `client.pool_element_create(12090564, pool_id=12345)` |
| `pool_versions_list(search=None, **params)` | `search`：dict，可筛 `pool_id`、`post_id`、`updater_id`、`updater_name`、`name_contains`、`is_new`、`version`、`category`、`is_active`、`is_deleted`；`limit`：int 每页条数 | 查合集修改历史；站点未配置 archive 服务时 `501` → pool_version 数组，含 `id`、`pool_id`、`updater_id`、`version`、`name`、`post_ids`；例 `client.pool_versions_list(search={'pool_id': 12345})` |
| `pool_version_diff(pool_version_id, other_id=None, type=None)` | `pool_version_id`：int 版本编号（路径变量）；`other_id`：int 要对比的版本编号，不传时由 `type` 决定用前一版还是后一版；`type`：str 取 `'previous'` / `'next'`，不传时未规定 | 比较两个合集版本 → 两个 pool_version 的差异对象（含两版字段与原值）；例 `client.pool_version_diff(88, type='previous')` |

## wiki（wiki 页面与历史）— 10 个方法

`wiki_page_show` 的路径部分接受编号或标题（标题会被 URL 转义，所以 `'help:api'` 可以直接传）；要列表
结果必须用 `search={'title': ...}`，顶层参数 `title=` 会被服务端 `302` 到标题搜索页。本组路由、凭据与
参数键见 [附注的 wiki 节](danbooru-contract-notes.md#sec-wiki)。

**常用方法**

**`wiki_page_list(search=None, **params)`** — 搜索 wiki 页面。返回 wiki_page 数组，每项含 `id`、`title`、
`body`、`is_locked`、`other_names`、`is_deleted`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    pages = client.wiki_page_list(search={'title': 'help:api'}, limit=2)
    # GET https://danbooru.donmai.us/wiki_pages.json?search%5Btitle%5D=help%3Aapi&limit=2
    # 返回数组，每项含 id / title / body / is_locked / other_names / is_deleted
    print([(page['id'], page['title']) for page in pages])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`title`、`title_normalize`、`title_or_body_matches`、`body_matches`、`other_names_match`、`other_names_present`、`is_locked`、`is_deleted`、`hide_deleted`、`linked_to`、`not_linked_to`、`embedded_post_id`、`embedded_media_asset_id`、`has_embedded_media`、`has_tag`、`has_artist`、`order`（`title` / `post_count`） | 页面过滤条件 | 列出全部页面 | `search={'title': 'help:api'}` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=2` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |
| `title` | str | 顶层 `title=` 会被服务端 `302` 到标题搜索，不是列表过滤；要列表结果请放进 `search` | 不发送 | 别用；改用 `search={'title': 'help:api'}` |

**`wiki_page_show(id_or_title)`** — 按编号或标题读 wiki 页面。给 `'help:api'` 这种标题时内部会 URL 转义
（`:` → `%3A`）；标题不存在时服务端返回 `404`。返回单个 wiki_page 对象（`title`、`body`、`other_names`、
`is_locked` 等）。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    page = client.wiki_page_show('help:api')
    # GET https://danbooru.donmai.us/wiki_pages/help%3Aapi.json
    # 返回单个对象：title / body / other_names / is_locked / is_deleted
    print(page['title'], len(page['body']))
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `id_or_title` | int 页面编号，或 str 标题（如 `'help:api'`） | 读哪一页；标题里的非 URL 安全字符会被转义 | 必填 | `client.wiki_page_show('help:api')` |

**本组其余 8 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `wiki_page_create(title, **attributes)` | `title`：str 页面标题，必填；`body`：str DText 正文；`other_names`（list）/ `other_names_string`（str）：别名标题；`is_deleted`：bool 建成就标记删除（需 Builder）；`is_locked`：bool 锁定编辑（需 Builder） | **写**：创建页面（需登录）→ 写后的 wiki_page 对象；例 `client.wiki_page_create('help:custom', body='自定义说明')` |
| `wiki_page_update(wiki_page_id, **attributes)` | `wiki_page_id`：int 编号或 str 标题（转义后进路径）；属性同 `wiki_page_create`，另有 `is_deleted` | **写**：改正文、其他名或删除标记（需登录）→ 写后的 wiki_page 对象；例 `client.wiki_page_update('help:api', body='<新正文>')` |
| `wiki_page_delete(wiki_page_id)` | `wiki_page_id`：int 编号或 str 标题 | **写**：软删除并返回对象（需 builder）→ 被更新/删除后的 wiki_page 对象，`is_deleted` 为 `true`；例 `client.wiki_page_delete('help:custom')` |
| `wiki_page_revert(wiki_page_id, version_id)` | `wiki_page_id`：int 编号或 str 标题；`version_id`：int 要恢复到的版本编号 | **写**：恢复指定版本（需登录）→ 写后的 wiki_page 对象；例 `client.wiki_page_revert('help:api', version_id=4321)` |
| `wiki_page_show_or_new(title=None)` | `title`：str 页面标题（顶层参数）；不传时未规定（源码 docstring 未写空标题行为） | 按标题定位页面或新建入口（服务端 `302`）→ 标题已存在时跟随重定向拿到该页面对象，否则返回未保存的 wiki_page 对象；例 `client.wiki_page_show_or_new('help:api')` |
| `wiki_page_versions_list(search=None, **params)` | `search`：dict，可筛 `wiki_page_id`、`updater_id`、`updater_name`、`title`、`title_like`、`title_ilike`、`title_regex`、`body_matches`、`other_names_include_any`、`is_locked`、`is_deleted`；`limit`：int 每页条数 | 查 wiki 修改历史 → wiki_page_version 数组，含 `id`、`wiki_page_id`、`updater_id`、`title`、`body`；例 `client.wiki_page_versions_list(search={'wiki_page_id': 1234})` |
| `wiki_page_version_show(version_id)` | `version_id`：int 版本编号 | 读一个 wiki 版本 → 单个 wiki_page_version 对象，字段同上；例 `client.wiki_page_version_show(4321)` |
| `wiki_page_versions_diff(thispage=None, otherpage=None, type=None)` | `thispage`：int 第一版编号；`otherpage`：int 第二版编号；`type`：str 取 `'previous'` / `'next'`，只在给了一个 id 时用来选对照版本；都不给时未规定 | 比较两个版本，匿名可读 → 两个 wiki_page_version 的差异对象（含两版字段与原值）；例 `client.wiki_page_versions_diff(thispage=4321, otherpage=4320)` |

## users（用户、用户记录与改名）— 15 个方法

匿名只拿到 `id`、`created_at`、`name`、`inviter_id`、`level`、`level_string`、各类计数与
`is_banned` / `is_deleted`；偏好设置类字段（`favorite_tags`、`blacklisted_tags`、`per_page`、`theme` 等）
只有本人可见。注意 `search['name']` 在 User 上会被服务端改写成模糊匹配的 `name_matches`。本组路由、
凭据与参数键见 [附注的 users 节](danbooru-contract-notes.md#sec-users)。

**常用方法**

**`user_list(search=None, **params)`** — 搜索用户。返回 user 数组，字段按身份裁剪（匿名只有上面那批
公开字段，本人多出偏好设置）。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    users = client.user_list(search={'name_matches': 'fuzichoco', 'order': 'name'}, limit=2)
    # GET https://danbooru.donmai.us/users.json?search%5Bname_matches%5D=fuzichoco&search%5Border%5D=name&limit=2
    # 返回数组，每项含 id / name / level / level_string / post_upload_count / is_banned
    print([(user['id'], user['name'], user['level']) for user in users])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`name_matches`（也接受 `name`）、`any_name_matches`、`name_or_past_name_matches`、`level`、`min_level`、`max_level`、`is_banned`、`has_posts`、`has_comments`、`order`（`name` / `post_upload_count` / `note_count` / `post_update_count`） | 用户过滤条件 | 列出全部用户 | `search={'name_matches': 'fuzichoco'}` |
| `name` | str | `search[name]` 的简写，同时搜当前名与曾用名（顶层参数） | 不按名字过滤 | `client.user_list(name='fuzichoco')` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=2` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`user_show(user_id)`** — 读用户资料。给用户编号，返回单个 user 对象；字段按身份裁剪，本人视角比
看别人多出偏好设置（`favorite_tags`、`blacklisted_tags`、`per_page`、`theme` 等）。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    users = client.user_list(search={'name_matches': 'fuzichoco'}, limit=1)
    # GET https://danbooru.donmai.us/users.json?limit=1&search%5Bname_matches%5D=fuzichoco
    # 本轮返回 []：画师标签名不一定是站内用户名，不能直接访问 users[0]。
    print([(user['id'], user['name']) for user in users])
    # 查到用户后，把其中的 id 交给 user_show；该名字没有命中，所以本轮没有执行详情请求。
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | int 用户编号 | 读哪个用户，会进 URL 路径 | 必填 | `client.user_show(270235)` |
| `only` | str | 只返回指定字段（用 `request('GET', 'users/<id>.json', params={'only': 'id,name'})` 传） | 返回完整对象 | `request('GET', 'users/270235.json', params={'only': 'id,name'})` |

**`user_profile()`** — 读当前登录用户（需登录）。不接受参数，返回当前登录的 user 对象，字段比
`user_show` 看别人多（含偏好设置与 `favorite_count`、`statement_timeout` 等）。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    me = client.user_profile()
    # GET https://danbooru.donmai.us/profile.json
    # 返回当前登录的 user 对象：id / name / level / per_page / favorite_tags / blacklisted_tags
    print(me['id'], me['name'], me['per_page'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| — | — | 没有参数，返回当前登录用户 | — | `client.user_profile()` |

**本组其余 12 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `user_create(name, password, password_confirmation)` | `name`：str 用户名；`password`：str 密码；`password_confirmation`：str 再输一遍 | **写**：提交注册（不需凭据，但站点会做验证码/邀请检查，可能因此失败）→ 写后的 user 对象；例 `client.user_create('newbie', 'secret123', 'secret123')` |
| `user_update(user_id, **attributes)` | `user_id`：int 自己的编号（只能改自己）；属性：`comment_threshold`（int）、`default_image_size`（str）、`favorite_tags`（str）、`blacklisted_tags`（str）、`time_zone`（str）、`per_page`（int）、`custom_style`（str）、`theme`（str）、`receive_email_notifications`（bool）、`new_post_navigation_layout`（bool）、`enable_private_favorites`（bool）、`show_deleted_posts`（bool）、`show_deleted_children`（bool）、`disable_categorized_saved_searches`（bool）、`disable_tagged_filenames`（bool）、`disable_mobile_gestures`（bool）、`enable_safe_mode`（bool）、`enable_desktop_mode`（bool）、`disable_post_tooltips`（bool）；不传的项保持原值 | **写**：修改自己的用户设置（需登录）→ 写后的 user 对象，含 `id`、`name`、`inviter_id`、`level`、`last_logged_in_at`；例 `client.user_update(270235, per_page=50, blacklisted_tags='guro')` |
| `user_actions_list(search=None, **params)` | `search`：dict，可筛 `user_id`、`user_name`、`event_type`、`model_type` / `model_id`、`order`（`event_at_asc`，默认最新在前）；顶层 `user_id`：int 也能限定单个用户；`limit`：int 每页条数 | 查用户活动记录（moderator）→ user_action 数组；例 `client.user_actions_list(user_id=270235, limit=20)` |
| `user_action_show(user_action_id)` | `user_action_id`：int 记录编号，来自 `user_actions_list` 的 `id` | 读一条用户活动记录（moderator）→ 单个 user_action 对象；例 `client.user_action_show(9876543)` |
| `user_events_list(search=None, **params)` | `search`：dict，可筛 `id`、`user_id`、`user_name`、`category`、`ip_addr`、`session_id`、`user_agent`、`metadata`；顶层 `user_id`：int；`limit`：int 每页条数 | 查用户事件（登录、上传、评价等）→ user_event 数组，含 `id`、`user_id`、`user_session_id`、`category`、`ip_addr`；非 moderator 看不到 `session_id` / `user_agent`；例 `client.user_events_list(user_id=270235, limit=20)` |
| `user_feedbacks_list(search=None, **params)` | `search`：dict，可筛 `id`、`user_id`、`user_name`、`creator_id`、`creator_name`、`category`（`positive` / `negative`）、`body_matches`、`is_deleted`、`hide_bans`；`limit`：int 每页条数 | 查用户评价，可见范围受限 → user_feedback 数组；例 `client.user_feedbacks_list(search={'user_id': 270235})` |
| `user_feedback_show(feedback_id)` | `feedback_id`：int 评价编号 | 读一条评价，可见范围受限 → 单个 user_feedback 对象；例 `client.user_feedback_show(456)` |
| `user_feedback_create(**attributes)` | `body`：str 评价正文；`category`：str 取 `positive` / `negative`；`user_id`（int）或 `user_name`（str）：评价对象 | **写**：创建评价（需登录）→ 写后的 user_feedback 对象；例 `client.user_feedback_create(user_id=270235, category='positive', body='绘图质量稳定')` |
| `user_feedback_update(feedback_id, **attributes)` | `feedback_id`：int 评价编号；`body`：str 新正文；`category`：str；`is_deleted`：bool | **写**：改评价正文、类别或删除标记（需登录）→ 写后的 user_feedback 对象；例 `client.user_feedback_update(456, is_deleted=True)` |
| `user_name_change_requests_list(search=None, **params)` | `search`：dict，可筛 `id`、`user_id`、`user_name`、`original_name`、`desired_name`；`limit`：int 每页条数 | 查改名请求（非匿名）→ user_name_change_request 数组，含 `id`、`user_id`、`original_name`、`desired_name`；例 `client.user_name_change_requests_list(search={'user_id': 270235})` |
| `user_name_change_request_show(request_id)` | `request_id`：int 请求编号 | 读一条改名请求（非匿名）→ 单个 user_name_change_request 对象，字段同上；例 `client.user_name_change_request_show(12)` |
| `user_name_change_request_create(**attributes)` | `user_id`：int 要改名的用户；`desired_name`：str 想要的新名字 | **写**：提交改名请求（需登录）→ 写后的 user_name_change_request 对象，含 `id`、`user_id`、`original_name`、`desired_name`；例 `client.user_name_change_request_create(user_id=270235, desired_name='new_name')` |

## favorites（收藏与收藏组）— 10 个方法

`favorite_list` 默认列自己的收藏，用顶层 `user_id` 指定看别人的；取消收藏的路径 id 就是 `post_id`
（没有单独的收藏记录编号）。私密收藏只有本人看得到。本组路由、凭据与参数键见
[附注的 users 节](danbooru-contract-notes.md#sec-users)。

**常用方法**

**`favorite_list(search=None, **params)`** — 查询收藏。返回 favorite 数组，每项含 `id`、`user_id`、
`post_id`；`post_id` 可以继续拿去 `post_show`。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    favorites = client.favorite_list(user_id=42, limit=5)
    # GET https://danbooru.donmai.us/favorites.json?user_id=42&limit=5
    # 返回数组，每项含 id / user_id / post_id；私密收藏只有本人看得到
    print([(item['id'], item['post_id']) for item in favorites])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `post_id`、`user_id`、`user_name` | 收藏过滤条件 | 列出可见的全部收藏 | `search={'post_id': 12090564}` |
| `post_id` | int 帖子编号 | 只看某个帖子的收藏（顶层参数） | 不按帖子限定 | `client.favorite_list(post_id=12090564)` |
| `user_id` | int 用户编号 | 看谁的收藏（顶层参数） | 登录时是自己的收藏 | `client.favorite_list(user_id=42)` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=5` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`favorite_create(post_id)`** — 收藏一个帖子（需登录）。返回**被收藏的 post 对象**（不是 favorite
记录）。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    post_id = client.post_list(tags='rating:g', limit=1)[0]['id']
    post = client.favorite_create(post_id)
    # POST https://danbooru.donmai.us/favorites.json
    # 请求体 {"post_id": <post_id>}；返回被收藏的 post 对象：id / rating / tag_string / source
    print(post['id'], post['favorite_count'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | int 帖子编号（顶层参数） | 收藏哪个帖子 | 必填 | `client.favorite_create(12090564)` |

**本组其余 8 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `favorite_delete(post_id)` | `post_id`：int 帖子编号（**路径里的 id 就是 post_id**） | **写**：取消收藏一个帖子（需登录）→ 取消收藏后的 post 对象；例 `client.favorite_delete(12090564)` |
| `favorite_groups_list(search=None, **params)` | `search`：dict，可筛 `id`、`name`、`name_contains`、`is_public`、`post_ids`、`creator_id`、`creator_name`、`order`（`name` / `created_at` / `updated_at` / `post_count`）；顶层 `user_id`：int 限定创建者；`limit`：int 每页条数 | 查收藏组，可见范围受限 → favorite_group 数组，含 `id`、`name`、`creator_id`、`post_ids`、`is_public`；例 `client.favorite_groups_list(user_id=270235)` |
| `favorite_group_show(group_id)` | `group_id`：int 收藏组编号，来自 `favorite_groups_list` 的 `id`；另有 `page` / `limit` 读 `post_ids`（签名外，用 `request()` 传） | 读一个收藏组 → 单个 favorite_group 对象（`id`、`name`、`creator_id`、`post_ids`、`is_public`）；例 `client.favorite_group_show(31)` |
| `favorite_group_create(name, **attributes)` | `name`：str 组名，必填；`post_ids`（list）或 `post_ids_string`（str 空格分隔）：初始帖子；`is_public`：bool 公开；`is_private`：bool 私有 | **写**：创建收藏组（需登录）→ 写后的 favorite_group 对象；例 `client.favorite_group_create('喜欢的风景', post_ids=[12090564], is_public=True)` |
| `favorite_group_update(group_id, **attributes)` | `group_id`：int 组编号；属性同 `favorite_group_create`（`name`、`post_ids`、`is_public`、`is_private`） | **写**：改设置或成员（需登录）→ 写后的 favorite_group 对象；例 `client.favorite_group_update(31, is_public=False)` |
| `favorite_group_delete(group_id)` | `group_id`：int 组编号 | **写**：删除收藏组（需登录）→ 被更新/删除后的 favorite_group 对象；例 `client.favorite_group_delete(31)` |
| `favorite_group_add_post(group_id, post_id)` | `group_id`：int 组编号（顶层）；`post_id`：int 帖子编号（顶层） | **写**：加帖进收藏组（需登录）→ 更新后的 favorite_group 对象，`post_ids` 里能看到它；例 `client.favorite_group_add_post(31, 12090564)` |
| `favorite_group_remove_post(group_id, post_id)` | `group_id`：int 组编号（顶层）；`post_id`：int 帖子编号（顶层） | **写**：从收藏组移除帖子（需登录）→ 更新后的 favorite_group 对象；例 `client.favorite_group_remove_post(31, 12090564)` |

## forum（论坛主题、帖子与投票）— 18 个方法

公开主题可匿名读，并按 `min_level` 过滤（等级不够的看不到）；发主题、回帖与投票需要登录，删除类
动作需要 moderator。本组路由、凭据与参数键见
[附注的 forum 节](danbooru-contract-notes.md#sec-forum)。

**常用方法**

**`forum_topics_list(search=None, **params)`** — 搜索可见的论坛主题。返回 forum_topic 数组，每项含
`id`、`creator_id`、`updater_id`、`title`、`response_count`、`is_sticky`、`is_locked`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    topics = client.forum_topics_list(search={'order': 'sticky'}, limit=5)
    # GET https://danbooru.donmai.us/forum_topics.json?search%5Border%5D=sticky&limit=5
    # 返回数组，每项含 id / creator_id / updater_id / title / response_count / is_sticky / is_locked
    print([(topic['id'], topic['title']) for topic in topics])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`title`、`title_matches`、`category` / `category_id`（枚举只有 `0` General / `1` Tags / `2` Bugs &amp; Features；**没有** 3 号“批量变更请求”类别，写 3 会被枚举校验拒绝）、`min_level`、`is_sticky`、`is_locked`、`is_deleted`、`is_private`、`is_read`、`status`（`pending` / `approved` / `rejected`）、`creator_id`、`creator_name`、`order`（`sticky` / `id`） | 主题过滤条件 | 列出可见的全部主题 | `search={'category_id': 1}` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=5` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`forum_posts_list(search=None, **params)`** — 搜索论坛帖子。返回 forum_post 数组，每项含 `id`、
`topic_id`、`creator_id`、`updater_id`、`body`、`is_deleted`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    topic_id = client.forum_topics_list(limit=1)[0]['id']
    posts = client.forum_posts_list(search={'topic_id': topic_id}, limit=10)
    # GET https://danbooru.donmai.us/forum_posts.json?search%5Btopic_id%5D=<topic_id>&limit=10
    # 返回数组，每项含 id / topic_id / creator_id / updater_id / body / is_deleted
    print([(post['id'], post['creator_id']) for post in posts])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`body_matches`、`creator_id`、`creator_name`、`topic_id`、`linked_to`，以及嵌套主题条件 `{'topic': {'title_matches': ...}}`、`{'topic': {'category_id': 1}}` | 帖子过滤条件 | 列出可见的全部帖子 | `search={'topic_id': 12345}` |
| `limit` | int，服务端上限 1000 | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**本组其余 16 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `forum_topic_show(topic_id)` | `topic_id`：int 主题编号；另有 `page` / `limit` 控制内嵌回复分页（签名外，用 `request()` 传） | 读主题详情，内嵌 `forum_posts` → 单个 forum_topic 对象（`id`、`creator_id`、`updater_id`、`title`、`response_count`、`forum_posts`）；例 `client.forum_topic_show(12345)` |
| `forum_topic_create(title, body, **attributes)` | `title`：str 标题；`body`：str 首帖正文（DText）；`category_id`：int，枚举只有 `0` General / `1` Tags / `2` Bugs &amp; Features，不传时 `General`；`min_level`：int 回帖最低等级（默认 `0` 不限，改它要 moderator+） | **写**：建主题及首帖（需登录）→ 写后的 forum_topic 对象；例 `client.forum_topic_create('标签建议', '建议把 x 别名到 y', category_id=1)` |
| `forum_topic_update(topic_id, **attributes)` | `topic_id`：int 主题编号；`title`：str；`category_id`：int；`is_sticky` / `is_locked`：bool（moderator+）；`min_level`：int（moderator+）；不传的项不动 | **写**：改标题、分类、置顶、锁定、等级门槛（需登录）→ 写后的 forum_topic 对象；例 `client.forum_topic_update(12345, is_locked=True)` |
| `forum_topic_delete(topic_id)` | `topic_id`：int 主题编号 | **写**：软删除主题（需 moderator）→ 被更新/删除后的 forum_topic 对象；例 `client.forum_topic_delete(12345)` |
| `forum_topic_undelete(topic_id)` | `topic_id`：int 主题编号 | **写**：恢复已删除主题（需 moderator）→ 写后的 forum_topic 对象；例 `client.forum_topic_undelete(12345)` |
| `forum_topics_mark_all_as_read()` | 无参数 | **写**：把论坛主题全部标为已读（需登录）；服务端重定向到主题列表，最终响应决定结果（未实测）→ 最终响应对象；例 `client.forum_topics_mark_all_as_read()` |
| `forum_post_show(post_id)` | `post_id`：int 论坛帖子编号 | 读一个论坛帖子（**不返回已删除的**，已删会 `404`）→ 单个 forum_post 对象（`id`、`topic_id`、`creator_id`、`updater_id`、`body`）；例 `client.forum_post_show(678901)` |
| `forum_post_create(topic_id, body)` | `topic_id`：int 回复哪个主题；`body`：str 正文（DText） | **写**：向主题发表回复（需登录）→ 写后的 forum_post 对象；例 `client.forum_post_create(12345, '附议这个建议')` |
| `forum_post_update(post_id, body)` | `post_id`：int 帖子编号；`body`：str 新正文 | **写**：改帖子正文（需登录，作者或 moderator）→ 写后的 forum_post 对象；例 `client.forum_post_update(678901, '更正后的正文')` |
| `forum_post_delete(post_id)` | `post_id`：int 帖子编号 | **写**：删除帖子（需 moderator）→ 被更新/删除后的 forum_post 对象；例 `client.forum_post_delete(678901)` |
| `forum_post_undelete(post_id)` | `post_id`：int 帖子编号 | **写**：恢复已删除帖子（需 moderator）→ 写后的 forum_post 对象；例 `client.forum_post_undelete(678901)` |
| `forum_post_votes_list(search=None, **params)` | `search`：dict，可筛 `forum_post_id`、`creator_id`、`creator_name`、`score`；`limit`：int 每页条数 | 查论坛帖子投票 → forum_post_vote 数组，含 `id`、`forum_post_id`、`creator_id`、`score`；例 `client.forum_post_votes_list(search={'forum_post_id': 678901})` |
| `forum_post_vote_show(vote_id)` | `vote_id`：int 投票编号 | 读一条论坛帖子投票，可见范围受限 → 单个 forum_post_vote 对象（`id`、`forum_post_id`、`creator_id`、`score`）；例 `client.forum_post_vote_show(24680)` |
| `forum_post_vote_create(forum_post_id, score)` | `forum_post_id`：int 论坛帖子编号（顶层）；`score`：int，只接受 `1`（赞）/ `-1`（踩）/ `0`（中性）——模型校验是 `[-1, 0, 1]` | **写**：给论坛帖子投票（需登录）→ 新建的 forum_post_vote 对象；例 `client.forum_post_vote_create(678901, score=1)` |
| `forum_post_vote_delete(vote_id)` | `vote_id`：int 投票编号 | **写**：撤回论坛帖子投票（需登录，本人）→ 被更新/删除后的 forum_post_vote 对象；例 `client.forum_post_vote_delete(24680)` |
| `forum_topic_visits_list(search=None, **params)` | `search`：dict，可筛 `user_id`、`forum_topic_id`、`last_read_at`；`limit`：int 每页条数 | 查自己的主题阅读记录（需登录，本人）→ forum_topic_visit 数组，含 `id`、`user_id`、`forum_topic_id`、`last_read_at`；例 `client.forum_topic_visits_list(search={'forum_topic_id': 12345})` |

## dmails（站内信）— 5 个方法

只能看自己的站内信；**没有独立的删除方法**，删除就是 `dmail_update(dmail_id, is_deleted=True)`。
本组路由、凭据与参数键见 [附注的 dmails 节](danbooru-contract-notes.md#sec-dmails)。

**常用方法**

**`dmail_list(search=None, **params)`** — 查询自己的站内信（需登录）。返回 dmail 数组，每项含 `id`、
`owner_id`、`from_id`、`to_id`、`title`、`is_read`、`is_deleted`。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    dmails = client.dmail_list(search={'folder': 'received', 'is_read': False}, limit=10)
    # GET https://danbooru.donmai.us/dmails.json?search%5Bfolder%5D=received&search%5Bis_read%5D=false&limit=10
    # 返回数组，每项含 id / owner_id / from_id / to_id / title / is_read / is_deleted
    print([(item['id'], item['title']) for item in dmails])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `id`、`title`、`body`、`message_matches`、`folder`（`received` / `sent` / `all`）、`is_read`、`is_deleted`、`to_id`、`to_name`、`from_id`、`from_name` | 站内信过滤条件 | 列出可见的全部站内信 | `search={'folder': 'received'}` |
| `limit` | int | 每页条数 | 服务端默认每页 20 | `limit=10` |
| `page` | int 或 ID 游标 | 页码 | 第一页 | `page=2` |

**`dmail_create(title, body, to_name=None, to_id=None)`** — 发送站内信（需登录）。收件人用 `to_name`
（用户名）或 `to_id`（用户编号）指定；返回写后的 dmail 对象。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    dmail = client.dmail_create(title='关于标签建议', body='已在论坛开帖，麻烦看一下。',
                                to_name='someone')
    # POST https://danbooru.donmai.us/dmails.json
    # 请求体 {"dmail": {"title": "...", "body": "...", "to_name": "someone", "to_id": null}}
    # 返回写后的对象：id / owner_id / from_id / to_id / title / is_read / is_deleted
    print(dmail['id'], dmail['to_id'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `title` | str 标题 | 站内信标题 | 必填 | `title='关于标签建议'` |
| `body` | str 正文，DText | 站内信正文 | 必填 | `body='已在论坛开帖，麻烦看一下。'` |
| `to_name` | str 用户名 | 收件人（与 `to_id` 二选一） | 两者都给时未规定谁优先 | `to_name='someone'` |
| `to_id` | int 用户编号 | 收件人（与 `to_name` 二选一） | 同上 | `to_id=270235` |

**本组其余 3 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `dmail_show(dmail_id)` | `dmail_id`：int 站内信编号，来自 `dmail_list` 的 `id` | 读一封站内信（需登录，本人）→ 单个 dmail 对象，含 `id`、`owner_id`、`from_id`、`to_id`、`title`、`is_read`；响应还可能带签名的 `key` 字段；例 `client.dmail_show(1234)` |
| `dmail_update(dmail_id, **attributes)` | `dmail_id`：int 站内信编号；`is_read`：bool 标记已读；`is_deleted`：bool 标记删除（**删除邮件就走这里**） | **写**：改已读/删除状态（需登录，本人）→ 写后的 dmail 对象；例 `client.dmail_update(1234, is_read=True)` |
| `dmails_mark_all_as_read()` | 无参数 | **写**：全部标为已读（需登录）→ 被标为已读的站内信集合；例 `client.dmails_mark_all_as_read()` |

## bans 与 bulk update requests（封禁与批量标签变更）— 11 个方法

批量变更请求（BUR）是申请别名（`alias a -> b`）、蕴含（`imply a -> b`）与批量改标签的正规入口；
`bulk_update_request_delete` 的语义是**拒绝**该请求（不是删除记录），批准要 approver。本组路由、凭据与
参数键见 [附注的 审核节](danbooru-contract-notes.md#sec-bans)。

**常用方法**

**`bulk_update_request_create(script, **attributes)`** — 提交批量标签变更请求（需登录）。`script` 是
BUR 脚本，别名写 `alias foo -> bar`、蕴含写 `imply foo -> bar`；返回写后的 bulk_update_request 对象，
`status` 初始为 `pending`。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    request = client.bulk_update_request_create('alias foo -> bar', reason='统一写法')
    # POST https://danbooru.donmai.us/bulk_update_requests.json
    # 请求体 {"bulk_update_request": {"script": "alias foo -> bar", "reason": "统一写法"}}
    # 返回写后的对象：id / user_id / forum_topic_id / script / status
    print(request['id'], request['status'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `script` | str，BUR 脚本，如 `'alias foo -> bar'`、`'imply 1girl -> solo'` | 要申请的关系或批量改动 | 必填 | `'alias foo -> bar'` |
| `title` | str | 可选标题 | 不发送 | `title='统一命名'` |
| `reason` | str | 可选理由，审批时给审批者看 | 不发送 | `reason='统一写法'` |
| `forum_topic_id` | int | 把请求挂到已有论坛主题下 | 不发送，服务端自行处理 | `forum_topic_id=12345` |

**本组其余 10 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `ban_list(search=None, **params)` | `search`：dict，可筛 `id`、`user_id`、`user_name`、`banner_id`、`banner_name`、`reason_matches`、`duration`、`expired`、`order`（`expires_at_desc`）；`limit`：int 每页条数 | 查用户封禁记录，匿名可读 → ban 数组，含 `id`、`user_id`、`reason`、`banner_id`、`duration`；例 `client.ban_list(search={'user_id': 270235})` |
| `ban_show(ban_id)` | `ban_id`：int 封禁记录编号 | 读一条封禁记录，匿名可读 → 单个 ban 对象（`id`、`user_id`、`reason`、`banner_id`、`duration`）；例 `client.ban_show(31)` |
| `ban_create(**attributes)` | `user_id`（int）或 `user_name`（str）：封谁；`reason`：str 理由，最长 600 字符；`duration`：str **必填**（模型 `presence` 校验，留空会被拒），合法值只有 `1 day` / `3 days` / `7 days` / `1 month` / `3 months` / `6 months` / `1 year` / `100 years`（`100 years` 就是永久封禁）；`delete_posts`、`delete_comments`、`delete_forum_posts`、`delete_post_votes`、`delete_comment_votes`：bool 是否连带删除（只覆盖最近 3 天的数据）；`post_deletion_reason`：str 删除帖子的理由 | **写**：封禁用户（需 moderator）→ 写后的 ban 对象；例 `client.ban_create(user_id=270235, reason='刷屏', duration='1 week')` |
| `ban_update(ban_id, **attributes)` | `ban_id`：int 封禁记录编号；`reason`：str 新理由；`duration`：str 新期限 | **写**：改理由或期限（需 moderator）→ 写后的 ban 对象；例 `client.ban_update(31, duration='1 month')` |
| `ban_delete(ban_id)` | `ban_id`：int 封禁记录编号 | **写**：解除封禁（需 moderator）→ 被更新/删除后的 ban 对象；例 `client.ban_delete(31)` |
| `bulk_update_requests_list(search=None, **params)` | `search`：dict，可筛 `id`、`script_matches`、`title_matches`、`user_id`、`user_name`、`approver_id`、`approver_name`、`forum_topic_id`、`status`（`pending` / `approved` / `rejected` 或逗号分隔多个）、`tags`、`can_approve`、`score`、`order`（`id` / `updated_at` / `score` 及 `_asc`）；`limit`：int 每页条数 | 查批量变更请求，匿名可读 → bulk_update_request 数组，含 `id`、`user_id`、`forum_topic_id`、`script`、`status`；例 `client.bulk_update_requests_list(search={'status': 'pending'})` |
| `bulk_update_request_show(request_id)` | `request_id`：int 请求编号，来自列表的 `id` | 读一个批量变更请求，匿名可读 → 单个 bulk_update_request 对象，字段同上；例 `client.bulk_update_request_show(4567)` |
| `bulk_update_request_update(request_id, **attributes)` | `request_id`：int 请求编号；`script`：str 新脚本；`forum_topic_id` / `forum_post_id`：int（需要该主题的更新权限） | **写**：改脚本或关联话题（需登录，本人）→ 写后的 bulk_update_request 对象；例 `client.bulk_update_request_update(4567, script='alias foo -> baz')` |
| `bulk_update_request_approve(request_id)` | `request_id`：int 请求编号 | **写**：批准（需 approver）→ 写后的 bulk_update_request 对象，`status` 变 `approved`；例 `client.bulk_update_request_approve(4567)` |
| `bulk_update_request_delete(request_id)` | `request_id`：int 请求编号 | **写**：语义是**拒绝**该请求（需登录，本人或 moderator）→ 被更新/删除后的 bulk_update_request 对象，`status` 变 `rejected`；例 `client.bulk_update_request_delete(4567)` |

## IP、审核日志、队列与举报（13 个方法）

审核队列返回的是**帖子列表**（不是队列记录）；举报要求登录且对象类型可举报；处理状态只有 moderator
能改。本组路由、凭据与参数键见 [附注的 审核节](danbooru-contract-notes.md#sec-moderation)。

**常用方法**

**`modqueue_list(search=None, **params)`** — 读取待审核帖子队列（要求 approver 权限）。返回**post
数组**，可以直接用 `post_show` 的字段集处理；服务端默认 `search[order]=modqueue`，`limit` 钳到 200。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    queue = client.modqueue_list(limit=20)
    # GET https://danbooru.donmai.us/modqueue.json?limit=20
    # 返回 post 数组（不是队列记录）：id / rating / tag_string / md5 / source
    print([post['id'] for post in queue])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search` | dict，可筛 `order`（默认 `modqueue`）、`tags` | 队列过滤条件 | 服务端按 `modqueue` 顺序给默认队列 | `search={'order': 'modqueue'}` |
| `mode` | str，默认 `'gallery'` | 返回模式（顶层参数） | `'gallery'` | `client.modqueue_list(mode='gallery')` |
| `limit` | int，服务端钳到 `0..200` | 每页条数 | 服务端默认每页数 | `limit=20` |

**`moderation_report_create(**attributes)`** — 举报评论、论坛帖子或站内信（需登录）。`model_type` 只接受
`'Comment'`、`'ForumPost'`、`'Dmail'`（模型 `ModerationReport::MODEL_TYPES`；客户端 docstring 写的
`Post` / `User` 在本版源码里**不是**可举报类型，带上会被校验拒绝），且被举报对象的 `reportable?` 还要
通过（例如不能举报自己的评论、不能举报 moderator 的内容、只能是最近一年内的）。返回写后的
moderation_report 对象，`status` 初始为 `pending`。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    comment_id = client.comment_list(search={'is_deleted': False}, limit=1)[0]['id']
    report = client.moderation_report_create(model_type='Comment', model_id=comment_id,
                                             reason='垃圾广告')
    # POST https://danbooru.donmai.us/moderation_reports.json
    # 请求体 {"moderation_report": {"model_type": "Comment", "model_id": <comment_id>, "reason": "垃圾广告"}}
    # 返回写后的对象：id / model_type / model_id / creator_id / reason / status
    print(report['id'], report['status'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `model_type` | str，只接受 `'Comment'` / `'ForumPost'` / `'Dmail'` | 举报对象类型 | 必填 | `model_type='Comment'` |
| `model_id` | int | 举报对象的编号：评论编号、论坛帖子编号或站内信编号 | 必填 | `model_id=3456789` |
| `reason` | str 举报理由 | 给审核者看的说明 | 必填 | `reason='垃圾广告'` |

**本组其余 11 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `mod_actions_list(search=None, **params)` | `search`：dict，可筛 `id`、`category`、`description_matches`、`creator_id`、`creator_name`、`subject_type`、`subject_id`、`order`（`created_at_asc`）；`limit`：int 每页条数 | 查管理操作日志，匿名可读（非 moderator 的结果里会滤掉敏感类目）→ mod_action 数组，含 `id`、`creator_id`、`description`、`category`、`subject_type`；例 `client.mod_actions_list(limit=10)` |
| `mod_action_show(mod_action_id)` | `mod_action_id`：int 记录编号 | 读一条管理操作日志（需 janitor）→ 单个 mod_action 对象，字段同上；例 `client.mod_action_show(7654321)` |
| `ip_bans_list(search=None, **params)` | `search`：dict，可筛 `id`、`ip_addr`、`reason_matches`、`category`（`warning` / `block`）、`is_deleted`、`hit_count`、`last_hit_at`、`creator_id`、`creator_name`、`order`（`created_at` / `updated_at` / `last_hit_at` 及 `_asc`）；`limit`：int 每页条数 | 查 IP 封禁（需 moderator+；docstring 未写前提，两处口径见[附注矛盾项](danbooru-contract-notes.md#矛盾易错点与客户端取舍)）→ ip_ban 数组，含 `id`、`creator_id`、`ip_addr`、`reason`、`category`、`is_deleted`；例 `client.ip_bans_list(search={'category': 'block'})` |
| `ip_ban_show(ip_ban_id)` | `ip_ban_id`：int IP 封禁编号 | 读一条 IP 封禁（需 moderator+，同上口径）→ 单个 ip_ban 对象，字段同上；例 `client.ip_ban_show(42)` |
| `ip_ban_create(**attributes)` | `ip_addr`：str IP 或网段，如 `'203.0.113.0/24'`；`reason`：str 理由；`category`：str 取 `warning` / `block`；`is_deleted`：bool | **写**：创建 IP 封禁（需 moderator+）→ 写后的 ip_ban 对象；例 `client.ip_ban_create(ip_addr='203.0.113.7', reason='刷屏', category='block')` |
| `ip_ban_update(ip_ban_id, **attributes)` | `ip_ban_id`：int 记录编号；属性同 `ip_ban_create`（`ip_addr`、`reason`、`category`、`is_deleted`） | **写**：修改 IP 封禁（需 moderator+）→ 写后的 ip_ban 对象；例 `client.ip_ban_update(42, category='warning')` |
| `ip_address_show(ip_addr)` | `ip_addr`：str IP 地址，如 `'203.0.113.7'`（**路径里的 id 就是 IP 字符串**） | 查询 IP 地址信息（需 moderator+）→ 该 IP 的查询结果对象（位置、ASN 等，字段随站点服务）；例 `client.ip_address_show('203.0.113.7')` |
| `ip_geolocations_list(search=None, **params)` | `search`：dict，可筛 `ip_addr`、`network`、`country`、`region`、`city`、`asn`、`is_proxy`；`limit`：int 每页条数 | 查 IP 地理信息（需 moderator）→ ip_geolocation 数组，含 `id`、`ip_addr`、`network`、`asn`、`is_proxy`；例 `client.ip_geolocations_list(search={'ip_addr': '203.0.113.7'})` |
| `moderation_reports_list(search=None, **params)` | `search`：dict，可筛 `model_type`、`model_id`、`creator_id`、`creator_name`、`reason_matches`、`status`、`recipient_id`、`recipient_name`；`limit`：int 每页条数 | 查举报：非 moderator 只看得到自己的（docstring 写“需 moderator”，两条口径见附注）→ moderation_report 数组，含 `id`、`model_type`、`model_id`、`creator_id`、`reason`、`status`；例 `client.moderation_reports_list(search={'model_type': 'Comment'})` |
| `moderation_report_show(report_id)` | `report_id`：int 举报编号，来自 `moderation_reports_list` 的 `id` | 读一个举报（同样：非 moderator 只看自己的）→ 单个 moderation_report 对象，字段同上；例 `client.moderation_report_show(2468)` |
| `moderation_report_update(report_id, **attributes)` | `report_id`：int 举报编号；`status`：str，枚举 `pending` / `rejected` / `handled`；不传则状态不变 | **写**：更新举报处理状态（需 moderator）→ 写后的 moderation_report 对象；例 `client.moderation_report_update(2468, status='handled')` |

## 公告、保存的搜索、站点凭据与反应（18 个方法）

公告与站点凭据是 admin 面；保存的搜索与反应属于已登录用户自己的数据。本组路由、凭据与参数键见
[附注的 运维节](danbooru-contract-notes.md#sec-moderation)。

**常用方法**

**`saved_search_create(**attributes)`** — 保存一个搜索查询（需登录）。给查询串与显示标签，返回写后的
saved_search 对象；之后在站点的保存搜索列表里能看到这条（`labels` 字段是标签数组）。

```python
from anybooru import Danbooru

with Danbooru('danbooru', username='me', api_key='my-key') as client:
    saved = client.saved_search_create(query='rating:g order:score', label_string='我关注的标签')
    # POST https://danbooru.donmai.us/saved_searches.json
    # 请求体 {"saved_search": {"query": "rating:g order:score", "label_string": "我关注的标签"}}
    # 返回写后的对象：id / user_id / query / labels
    print(saved['id'], saved['query'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | str，标签查询串 | 要保存的查询 | 必填 | `query='rating:g order:score'` |
| `label_string` | str | 显示名称 | 不发送，站点显示原始查询 | `label_string='我关注的标签'` |
| `disable_labels` | bool | 隐藏这个搜索的标签 | 不发送 | `disable_labels=True` |

**本组其余 17 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `news_updates_list(search=None, **params)` | `search`：dict，可筛 `message_matches`、`creator_id`、`creator_name`、`is_deleted`、`order`（`created_at_asc`）；`limit`：int 每页条数 | 查站点公告（需 admin）→ news_update 数组，含 `id`、`message`、`creator_id`、`updater_id`、`duration`；例 `client.news_updates_list(limit=10)` |
| `news_update_show(news_update_id)` | `news_update_id`：int 公告编号 | 读一条公告（需 admin）→ 单个 news_update 对象，字段同上；例 `client.news_update_show(12)` |
| `news_update_create(message, **attributes)` | `message`：str 公告文本（DText banner）；`duration`（str）或 `duration_in_days`（int）：展示多久；`is_deleted`：bool | **写**：创建公告（需 admin）→ 写后的 news_update 对象；例 `client.news_update_create('维护公告', duration_in_days=3)` |
| `news_update_update(news_update_id, **attributes)` | `news_update_id`：int 公告编号；属性同 `news_update_create`（`message`、`duration` 等） | **写**：修改公告（需 admin）→ 写后的 news_update 对象；例 `client.news_update_update(12, message='维护延长')` |
| `news_update_delete(news_update_id)` | `news_update_id`：int 公告编号 | **写**：软删除公告（需 admin）→ 被更新/删除后的 news_update 对象；例 `client.news_update_delete(12)` |
| `saved_searches_list(search=None, **params)` | `search`：dict，可筛 `query_matches`、`label`、`disable_labels`、`order`（`query` / `label`）；`limit`：int 每页条数 | 查保存的搜索（需登录）→ saved_search 数组，含 `id`、`user_id`、`query`、`labels`；例 `client.saved_searches_list(limit=10)` |
| `saved_search_update(saved_search_id, **attributes)` | `saved_search_id`：int 保存的搜索编号；属性同 `saved_search_create`（`query`、`label_string`、`disable_labels`） | **写**：修改保存的搜索（需登录，本人）→ 写后的 saved_search 对象；例 `client.saved_search_update(31, label_string='新标签')` |
| `saved_search_delete(saved_search_id)` | `saved_search_id`：int 保存的搜索编号 | **写**：删除保存的搜索（需登录，本人）→ 被更新/删除后的 saved_search 对象；例 `client.saved_search_delete(31)` |
| `site_credentials_list(search=None, **params)` | `search`：dict，可筛 `site`（如 `'pixiv'`）、`is_enabled`、`is_public`、`status`、`creator_id`、`updater_id`、`order`；`limit`：int 每页条数 | 查获授权管理的外部站点凭据（需 admin）→ site_credential 数组，含 `id`、`site`、`creator_id`、`is_enabled`、`is_public`；例 `client.site_credentials_list(search={'site': 'pixiv'})` |
| `site_credential_show(site_credential_id)` | `site_credential_id`：int 凭据编号 | 读一条站点凭据：公开项需 admin，私有项需本人 → 单个 site_credential 对象，字段同上；例 `client.site_credential_show(3)` |
| `site_credential_create(site, **attributes)` | `site`：str 站点名，如 `'pixiv'`；`credential`：dict，键随站点而定（如 `login`、`password`）；`is_enabled`：bool | **写**：添加外部站点凭据（需 admin）→ 写后的 site_credential 对象；例 `client.site_credential_create('pixiv', credential={'login': 'me', 'password': '...'})` |
| `site_credential_update(site_credential_id, **attributes)` | `site_credential_id`：int 凭据编号；`is_enabled`：bool | **写**：改启用状态（需 admin 或本人）→ 写后的 site_credential 对象；例 `client.site_credential_update(3, is_enabled=False)` |
| `site_credential_delete(site_credential_id)` | `site_credential_id`：int 凭据编号 | **写**：删除站点凭据（公开项需 owner，私有项需本人）→ 被更新/删除后的 site_credential 对象；例 `client.site_credential_delete(3)` |
| `reactions_list(search=None, **params)` | `search`：dict，可筛 `model_type`、`model_id`、`creator_id`、`reaction_id`；`limit`：int 每页条数 | 查反应记录，可见范围受限 → reaction 数组，含 `id`、`creator_id`、`reaction_id`、`model_type`、`model_id`；例 `client.reactions_list(search={'model_type': 'Post', 'model_id': 12090564})` |
| `reaction_show(reaction_id)` | `reaction_id`：int 反应记录编号 | 读一条反应，可见范围受限 → 单个 reaction 对象，字段同上；例 `client.reaction_show(99)` |
| `reaction_create(**attributes)` | `model_type`：str，模型允许 `Post` / `Comment` / `ForumPost` / `User` / `Tag` / `Pool`（docstring 只列了前三种）；`model_id`：int 对象编号；`reaction_id`：str 反应名，取值来自站点的 `reactions` 配置，包内默认配置是空字典（即未规定有哪些），给未配置的名字会被校验拒绝 | **写**：为帖子、评论或论坛帖子添加反应（需登录）→ 写后的 reaction 对象；例 `client.reaction_create(model_type='Post', model_id=12090564, reaction_id='heart')` |
| `reaction_delete(reaction_id)` | `reaction_id`：int 反应记录编号 | **写**：撤回反应（需登录）→ 被更新/删除后的 reaction 对象；例 `client.reaction_delete(99)` |

## 报表、后台任务与杂项（11 个方法）

`counts_posts` 默认走估算与缓存（要精确计数或绕过缓存得显式传参）；`source_show`、`iqdb_query` 依赖
站点的来源解析与 IQDB 服务，**方法存在不代表每个站点都启用**。本组路由、凭据与参数键见
[附注的 杂项节](danbooru-contract-notes.md#sec-misc)。

**常用方法**

**`counts_posts(tags=None, estimate_count=None, skip_cache=None)`** — 统计标签查询匹配的帖子数。返回
`{"counts": {"posts": <int>}}`；默认用估算值并走缓存，要精确计数传 `estimate_count=False`，要绕过缓存
传 `skip_cache=True`。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    counts = client.counts_posts(tags='rating:g', estimate_count=False, skip_cache=True)
    # GET https://danbooru.donmai.us/counts/posts.json?tags=rating%3Ag&estimate_count=false&skip_cache=true
    # 返回 {"counts": {"posts": <int>}}
    print(counts['counts']['posts'])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | str 标签查询串 | 统计哪些帖子；空值统计全站 | 空值即统计全部帖子 | `tags='rating:g'` |
| `estimate_count` | bool | 用快速估算代替精确计数 | 服务端默认估算（`true`） | `estimate_count=False` |
| `skip_cache` | bool | 绕过计数缓存 | 服务端默认用缓存 | `skip_cache=True` |

**`source_show(url, ref=None, mode=None)`** — 请求站点解析来源 URL。给一个作品页或画师页地址，站点用
自己的来源规则解析出规范信息（画师、作品编号等）；返回解析出的来源数据对象，字段随站点配置与来源
类型而定。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    source = client.source_show('https://www.pixiv.net/users/27517')
    # GET https://danbooru.donmai.us/source.json?url=https%3A%2F%2Fwww.pixiv.net%2Fusers%2F27517
    # 返回站点解析出的来源数据对象（画师／作品信息，字段随来源类型而定）
    print(source)
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `url` | str，要解析的页面地址 | 来源解析的输入 | 必填 | `'https://www.pixiv.net/users/27517'` |
| `ref` | str，referer 地址 | 给需要 referer 的来源站点用 | 不发送 | `ref='https://www.pixiv.net/'` |
| `mode` | str，`'card'`（默认）或 `'post'` | 展示模式 | `'card'` | `mode='post'` |

**`iqdb_query(**params)`** — 通过站点的 IQDB 服务查相似图。给图片地址、预计算的 hash、帖子编号或媒体
资源编号之一；返回匹配结果数组，每项含 `score`、`post` 等。**站点未配置 IQDB 时返回空数组**（不是报错）。

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    matches = client.iqdb_query(post_id=12211425)
    # GET https://danbooru.donmai.us/iqdb_queries.json?post_id=12211425
    # 返回匹配数组，每项含 score / post（post 是命中的帖子对象）
    print([(match['score'], match['post']['id']) for match in matches])
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `url` / `file_url` / `image_url` | str，图片地址 | 要搜哪张图（三选一，语义相同） | 与 `hash` / `post_id` / `media_asset_id` 至少给一个 | `url='https://example.com/a.jpg'` |
| `hash` | str，预先算好的图片哈希 | 免去下载图片直接查 | 不发送 | `hash='0f343b0931126a20f133d67c2b018a3b'` |
| `post_id` | int 帖子编号 | 用该帖自己的图去搜 | 不发送 | `post_id=12090564` |
| `media_asset_id` | int 媒体资源编号 | 用该媒体资源的图去搜 | 不发送 | `media_asset_id=987654` |
| `limit` | int，服务端上限 1000 | 返回多少条匹配 | 服务端默认值 | `limit=10` |

**本组其余 8 个方法**

| 方法 | 参数：类型 / 取值 / 含义 / 不传时 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `report_show(report, search=None, **params)` | `report`：str，取 `posts`、`post_approvals`、`post_appeals`、`post_flags`、`post_replacements`、`post_votes`、`media_assets`、`pools`、`comments`、`comment_votes`、`forum_posts`、`bulk_update_requests`、`tag_aliases`、`tag_implications`、`artist_versions`、`artist_commentary_versions`、`note_versions`、`wiki_page_versions`、`mod_actions`、`bans`、`users` 之一（共 21 个，取自控制器的名字表）；`search`：dict，可筛 `period`、`from`、`to`、`columns`、`group`、`group_limit`、`mode` 与该模型自己的搜索参数；`mode` 不传时为 `chart`，`from`/`to` 不传时分别是「一个月前」与「现在」，`columns` 用空白或逗号分隔，`group_limit` 不传时为 10 | 查统计报表，匿名可读 → 报表对象，列与分组由 `columns`、`group` 决定；例 `client.report_show('posts', search={'group': 'rating'})` |
| `jobs_list(search=None, **params)` | `search`：dict，可筛 `id`、`active_job_id`、`job_class`、`queue_name`、`labels`、`priority`、`status`、`name`（按 job class 模糊匹配）；`limit`：int 每页条数 | 查后台任务，匿名可读；非 admin 看不到 `serialized_params` → background_job 数组，含 `id`、`job_class`、`queue_name`、`status`、`active_job_id` 与 `runtime_latency` / `queue_latency`；例 `client.jobs_list(limit=10)` |
| `job_cancel(job_id)` | `job_id`：str，任务的 ActiveJob id（响应里的 `active_job_id`） | **写**：取消任务（需 janitor）→ 写后的 background_job 对象；例 `client.job_cancel('a1b2c3d4-...')` |
| `job_retry(job_id)` | `job_id`：str ActiveJob id | **写**：重试任务（需 janitor）→ 写后的 background_job 对象；例 `client.job_retry('a1b2c3d4-...')` |
| `job_run(job_id)` | `job_id`：str ActiveJob id | **写**：立即运行任务（需 janitor）→ 写后的 background_job 对象；例 `client.job_run('a1b2c3d4-...')` |
| `job_delete(job_id)` | `job_id`：str ActiveJob id | **写**：删除任务（需 janitor）→ 被更新/删除后的 background_job 对象；例 `client.job_delete('a1b2c3d4-...')` |
| `dtext_links_list(search=None, **params)` | `search`：dict，可筛 `link_type`、`link_target`、`model_type`、`model_id`、`linked_wiki_id`、`linked_tag_id`；`limit`：int 每页条数 | 查正文里的 DText 链接关系，匿名可读 → dtext_link 数组，含 `id`、`model_type`、`model_id`、`link_type`、`link_target`；例 `client.dtext_links_list(search={'model_type': 'Post', 'model_id': 12090564})` |
| `recommended_posts_list(search=None, **params)` | `search`：dict，原样发给站点的推荐服务，典型是 `{'user_id': ...}` 或 `{'post_id': ...}`；`limit`：int，服务端上限 200 | 向站点推荐服务查询，匿名可读（依赖站点配置）→ post 数组，含 `id`、`up_score`、`down_score`、`score`、`source`；例 `client.recommended_posts_list(search={'post_id': 12090564}, limit=10)` |

## 看清不存在图片的错误

给不存在的图片编号时，服务器返回 404，不是一个空的图片列表。异常对象里能看到 URL 和错误正文：

```python
from anybooru import Danbooru, AnybooruHTTPError

with Danbooru('danbooru') as client:
    try:
        missing_post = client.post_show(0)
        # GET https://danbooru.donmai.us/posts/0.json
    except AnybooruHTTPError as error:
        print(error.http_code, error.url)  # 404 https://danbooru.donmai.us/posts/0.json
        print(error.data['message'])  # That record was not found.
```

## 边界与未实测

本节集中说明本家族的实测状态与不可用分支，主干条目里不再逐段插入免责声明。

`note_preview` 返回403（`ActionController::InvalidAuthenticityToken`），这些不是成功响应。
用户搜索 `fuzichoco` 返回200空列表，旧示例据此访问首项时越界；上面的示例已改为直接显示列表，修改后未重跑。

**已实测（匿名只读，2026-09-15，`danbooru.donmai.us` 经代理，无凭据）**：15 次请求中 12 次 `200`，
3 次为预期失败（`404` 不存在的帖子、`410` 页码超限、`422` 标签数超限），另外单独验证了重定向端点
`artist_show_or_new`（`302` → JSON）。覆盖的方法：`post_list`（含 `tags` 搜索与 `page=b<id>` 游标）、
`post_show`、`tag_list`、`artist_list`（URL 匹配、布尔过滤、`order`、`any_name_matches`）、
`artist_show_or_new`、`related_tag`、`wiki_page_list`、`wiki_page_show`、`comment_list`、`pool_list`。
逐条记录见 [verification.md](verification.md)。

**源码对齐但未实测**：其余 217 个方法没有线上成功记录。

* **写接口**：`post_create`、`post_update`、`post_delete`、投票、收藏、评论、笔记、合集编辑、审核动作、
  站内信、批量变更请求、公告、后台任务等全部未执行——本仓库不带凭据，也没有为这些方法发过写请求。
* **上传与媒体链路**：`upload_create`（multipart）与 `post_replacement_create`（`replacement_file`）只有
  源码依据，上传归属与压缩包展开行为未验证。
* **高权限与重新认证**：`api_keys_*`、`site_credentials_*`、`ip_*`、`jobs_*`、公告类动作未验证。
* **重定向类写操作**：`artist_delete` / `artist_ban` / `artist_unban` / `forum_topics_mark_all_as_read` /
  `wiki_page_show_or_new` 在服务端是 `redirect_to`；只有 `artist_show_or_new` 的跟随重定向实测过，写类
  重定向未实测，因此不断言成功或失败——最终响应不是 JSON 时会抛 `AnybooruAPIError`，用
  `last_call['status_code']` 与 `last_call['url']` 判断实际结果。
* **能力依赖**：archive 未配置时 `post_versions_list` / `pool_versions_list` 返回 `501`；IQDB 未配置时
  `iqdb_query` 返回空数组（与 archive 的 `501` 是不同分支）；推荐服务依赖站点配置，未验证成功路径。
* 同族站点另有独立只读探测（Safebooru 匿名可用且是 Danbooru）；候选站复核访问过 `/users.json`、
  `/autocomplete.json` 等读路径，不能把上面的早期覆盖清单当作全量当前状态。
* 未列出的路由只有源码依据；「已实测」只覆盖当时那次调用用到的参数组合，换参数、换身份、换站点都不算
  已验证。完整路由、参数与上游出处见 [契约审计附注](danbooru-contract-notes.md)。

本次文档重排没有新增网络请求。

