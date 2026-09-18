# Danbooru 客户端用法

`Danbooru` 访问 Danbooru 引擎系站点的 JSON 接口：读配置、拼请求、附加认证，把服务端返回的 JSON
原样交给你。方法清单见 [方法参考](danbooru-api.md)，按目的找入口见
[能力入口](danbooru-capabilities.md)，逐条路由与上游出处见
[契约审计附注](danbooru-contract-notes.md)。

## 三行上手

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:      # 读随包安装的 anybooru/anybooru.json
    page = client.wiki_page_show('help:api')
    # GET https://danbooru.donmai.us/wiki_pages/help%3Aapi.json
    print(page['title'])                  # wiki 页面标题
    related = client.related_tag(search={'query': 'touhou', 'order': 'frequency'}, limit=3)
    # GET https://danbooru.donmai.us/related_tag.json?search%5Bquery%5D=touhou&search%5Border%5D=frequency&limit=3
    print(related['query'], related['post_count'])
    print([item['tag']['name'] for item in related['related_tags']])
```

```text
help:api
touhou 1096795
['1girl', 'solo', 'hat']
```

上面的字段取值来自早前匿名只读验证的记录（`related_tag` 的 `post_count` 是查询当时的快照，两次记录
分别是 `1096790` 与 `1096795`），命令与逐请求结果见 [verification.md](verification.md)。这次文档重写
没有新增网络请求，片段照抄即可运行。

`Danbooru('danbooru')` 的 `'danbooru'` 是配置 `sites` 段的键：它同时决定请求发往哪个地址、读哪一组
凭据。包内默认配置里 `sites.danbooru` 是 `{"url": "https://danbooru.donmai.us", "username": "",
"api_key": ""}`，两项凭据为空，所以上面是匿名请求。

## 构造

`Danbooru(site_name=None, site_url=None, username=None, api_key=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `site_name` | str，配置 `sites` 段的键，如 `'danbooru'`、`'safebooru'` | 选定站点条目；同时决定 `username` / `api_key` 从哪个条目读 | 不读站点条目，此时必须自己给 `site_url` | `Danbooru('safebooru')` |
| `site_url` | str，站点根地址，如 `'https://danbooru.donmai.us'` | 覆盖配置里的 `url`；尾部 `/` 会被去掉 | 用 `sites[site_name]['url']` | `Danbooru(site_url='https://danbooru.donmai.us')` |
| `username` | str | 覆盖配置里的 `username`；与 `api_key` 一起发 HTTP Basic | 用 `sites[site_name]['username']`；`site_name` 也没给时为空 | `Danbooru('danbooru', username='me')` |
| `api_key` | str | 覆盖配置里的 `api_key`；非空即发认证 | 用 `sites[site_name]['api_key']` | `Danbooru('danbooru', api_key='...')` |
| `proxies` | dict，如 `{'https': 'http://proxy.example:8080'}` | 传给 requests 的代理设置 | 用配置 `request.proxies`（包内默认 `{}`，即不走代理） | `Danbooru('danbooru', proxies={'https': 'http://proxy.example:8080'})` |
| `config_file` | str 路径 | 读这份配置文件，而不是包内默认文件 | `None`，即读随包安装的 `anybooru/anybooru.json` | `Danbooru('danbooru', config_file='my-sites.json')` |
| `timeout` | int/float 秒，或它们的列表（会转成 tuple） | 单次请求超时 | 用配置 `request.timeout`（包内默认 `30`） | `Danbooru('danbooru', timeout=10)` |
| `user_agent` | str | 覆盖 `User-Agent` 请求头 | 用配置 `request.user_agent`（包内默认 `Anybooru/0.1.0.dev1`） | `Danbooru('danbooru', user_agent='my-app/1.0')` |

三条来自实现的硬行为：

* `config_file` 指向的文件不存在时直接抛 `FileNotFoundError`，不会回落到包内默认文件，也不会内置站点；
* `site_name` 与 `site_url` 都不给时，构造读 `sites[...]['url']` 失败并抛 `KeyError: 'url'`；
* 会话设了 `trust_env=False`：`HTTP_PROXY` / `HTTPS_PROXY` 等环境变量一律不读，代理只能从配置或
  `proxies` 参数来。

配置解析后挂在公开属性上：`client.config['request']['timeout']` 是 `30`，
`client.config['sites']['danbooru']['url']` 是 `'https://danbooru.donmai.us'`，`client.site_url` 是当前
实际使用的根地址（改这个属性即换站点），`client.site_name` 是构造时给的键名。字段含义见
[configuration.md](configuration.md)。

## 示例脚本从哪里取参数

`examples/danbooru/*.py` 不把值写死，而是从 `client.config['examples']['danbooru']` 取，再用
`--config` / `--site` 覆盖；文档里的片段一律直接写字面值。对应关系如下，右边一列就是可以直接抄的调用：

| 配置键（`examples.danbooru`） | 包内默认值 | 等价字面调用 |
| :--- | :--- | :--- |
| `site` | `'danbooru'` | `Danbooru('danbooru')` |
| `tags` / `limit` | `'rating:g'` / `3` | `client.post_list(tags='rating:g', limit=3)` |
| `pages` | `[1, 2]` | `client.post_list(tags='rating:g', page=1, limit=3)`、`page=2` |
| `tag_search` | `{'order': 'count'}` | `client.tag_list(search={'order': 'count'}, limit=3)` |
| `wiki_title` / `preview_chars` | `'help:api'` / `200` | `client.wiki_page_show('help:api')` 后取 `page['body'][:200]` |
| `related_query` / `related_category` / `related_order` | `'touhou'` / `0` / `'frequency'` | `client.related_tag(search={'query': 'touhou', 'category': 0, 'order': 'frequency'}, limit=3)` |
| `search_sample_size` / `tag_sample_size` | `1000` / `100` | 同上再加 `search={'search_sample_size': 1000, 'tag_sample_size': 100}` |
| `post_id` / `comment_body` | `1` / `'示例评论'` | `client.comment_create(post_id=1, body='示例评论')`（写操作，需登录） |
| `wiki_query` | `'help:api'` | 列表查询用 `client.wiki_page_list(search={'title': 'help:api'}, limit=3)` |

## 认证

只要 `username` 或 `api_key` **任一非空**，就发 HTTP Basic（缺的那项按空字符串补），两项都空才匿名；
客户端不做本地鉴权判断，权限完全由服务端判定。

| 构造值 | 发出的请求 | 典型结果 |
| :--- | :--- | :--- |
| `username=''`、`api_key=''` | 无 `Authorization` 头，身份是站点匿名用户 | 公开读接口 `200` |
| `username='me'`、`api_key=''` | `Authorization: Basic base64("me:")` | 凭据不完整，服务端 `401`（不会静默降级为匿名） |
| `username=''`、`api_key='key'` | `Authorization: Basic base64(":key")` | 视 key 是否有效与权限：无效 `401`，权限不足 `403` |
| `username='me'`、`api_key='key'` | `Authorization: Basic base64("me:key")` | 同上，按 key 的权限位放行 |

`401` 是凭据无效或不完整，`403` 是权限不足，两者都以 `AnybooruHTTPError` 抛出，可用
`error.http_code` 区分。背景见 [authentication.md](authentication.md)，异常见 [errors.md](errors.md)。

## 通用请求入口

`request(method, path, *, params=None, data=None, files=None)` 是所有原生方法的底座，没有原生方法的
JSON 路由也直接用它。它自己构造客户端，不依赖别的片段：

```python
from anybooru import Danbooru

client = Danbooru('danbooru')            # 本节不写 with，用完调用 client.close()
posts = client.request('GET', 'explore/posts/popular.json',
                       params={'scale': 'week', 'limit': 5})
# GET https://danbooru.donmai.us/explore/posts/popular.json?scale=week&limit=5
# 返回 post 数组，每项含 id / rating / tag_string / md5 / source
client.close()
```

| 参数 | 类型与取值 | 含义 | 不传时 | 例子 |
| :--- | :--- | :--- | :--- | :--- |
| `method` | str，`'GET'` / `'POST'` / `'PUT'` / `'DELETE'` 等 | HTTP 动词，原样使用 | 必填 | `'GET'` |
| `path` | str，站点根地址之后的相对路径 | 开头的 `/` 会去掉；结尾不是 `.json` 时自动补上，所以 `'posts.json'` 与 `'posts'` 等价 | 必填 | `'posts.json'` |
| `params` | dict，值可为标量 / dict / list | 查询串参数，按 Rails 括号形式编码 | `None`，不带查询串 | `params={'tags': 'rating:g', 'limit': 5}` |
| `data` | dict，值可为标量 / dict / list | 请求体；无 `files` 时以 JSON 发送（嵌套结构与显式空数组原样保留） | `None`，不发请求体 | `data={'comment': {'post_id': 1, 'body': '你好'}}` |
| `files` | dict `{字段名: 文件对象}` 或 `(字段名, 文件对象)` 列表 | 非空时改用 multipart 请求体，字段名是**字面**键（如 `'upload[files][0]'`），requests 不会为 multipart 展开括号 | `None`，走 JSON 通路 | `files={'upload[files][0]': open('a.jpg', 'rb')}` |

三条约定：

* 路径里的 ID 由调用者自己转义（`wiki_page_show` 内部已用 `quote(..., safe='')` 转义标题）；
* 不做任何隐式处理：不自动重试、不猜权限、不钳位 `limit`、不自动翻页，网络错误、限流、`5xx` 全抛给调用者；
* 请求头固定为 `User-Agent`（配置值）与 `Accept: application/json`。

## 参数编码

**查询串**（`params`）用 Rails 括号形式：嵌套 dict 展开成 `a[b]`，列表展开成重复键 `a[]`，布尔写成
小写 `true` / `false`，`None` 整项不发送。所以
`client.tag_list(search={'name_matches': 'touhou'}, limit=2)` 发出的查询串是
`?search%5Bname_matches%5D=touhou&limit=2`。

**请求体**分两套：

* 无文件发 **JSON**（嵌套 dict 就是嵌套对象，结构原样保留）。用 JSON 的意义是保住显式空值：
  `pool_update(pool_id, post_ids=[])` 会把空数组真的发出去（用于清空合集内容），表单编码会丢掉它；
  值为 `None` 的键在两层里都会被省略。
* 带文件发 **Rails 表单 / multipart**，字段名是字面键：`upload[files][0]`、`post_replacement[replacement_file]`。

**搜索字典**（`search`）是嵌套结构，由原生方法放进 `search[...]` 层；`limit`、`page`、`post_id` 这类
顶层参数走 `**params`：

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    tags = client.tag_list(search={'name_matches': 'touhou'}, limit=2)
    # GET https://danbooru.donmai.us/tags.json?search%5Bname_matches%5D=touhou&limit=2
    # 返回 tag 数组，每项含 id / name / post_count / category / is_deprecated
    print(tags[0]['name'], tags[0]['post_count'])
    related = client.related_tag(search={'query': 'touhou', 'order': 'frequency'}, limit=2)
    # GET https://danbooru.donmai.us/related_tag.json?search%5Bquery%5D=touhou&search%5Border%5D=frequency&limit=2
    # 返回单个对象：query / post_count / tag / related_tags / wiki_page_tags
    print(related['related_tags'][0]['tag']['name'])
```

**帖子的列表查询是例外**：`post_list` 不读 `search` 字典，过滤条件全部写成顶层 `tags` 里的元标签
（`rating:g`、`score:>10`、`order:score`、`id:>123`）：

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    posts = client.post_list(tags='rating:g order:score', limit=10)
    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag+order%3Ascore&limit=10
    # 返回 post 数组，每项含 id / rating / tag_string / md5 / source
    print(posts[0]['id'])
```

## 返回值与上一次请求

* 响应体是 JSON ⇒ 解析后原样返回：服务端给数组就是 `list`，给对象就是 `dict`，字段不改名、不包装；
* `204` 或空正文 ⇒ 返回 `None`（例如 `post_copy_notes` 成功、`DELETE` 类接口）；
* 状态码不是 2xx ⇒ 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`、`data` 与原始 `response`；
* 状态码 2xx 但正文不是 JSON ⇒ 抛 `AnybooruAPIError`；
* 网络层异常（连不上、超时、TLS 失败）不包装，直接抛 requests 自己的异常，此时 `last_call` 仍是 `{}`。

`last_call` 每次请求后重写，记录这次请求的实际结果：

| 键 | 类型 | 内容 |
| :--- | :--- | :--- |
| `API` | str | 库里记的路由，如 `'posts.json'` |
| `url` | str | 最终完整地址，含查询串，可用来核对“参数到底发成了什么样” |
| `status_code` | int | HTTP 状态码 |
| `status` | str | 状态原因短语，如 `'OK'` |
| `headers` | `requests` 响应头对象 | 含 `X-Rate-Limit` 等站点头 |

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    client.post_list(tags='rating:g', limit=2)
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=2
```

失败时 `last_call` 仍然可用，但它只说明服务端回了什么，不说明写入是否生效——尤其重定向类写操作。

## 常见坑

* **`post_list` 不吃 `search`**：写 `search={'tags': 'rating:g'}` 会被静默忽略，表现是“返回最新全集”；
  过滤条件写成顶层 `tags='rating:g'`。
* **`GET` 不能带请求体**：服务端对带体的 GET 直接 `400`；客户端按你给的参数原样发送，不会替你拦下，
  所以别给 `method='GET'` 的调用传 `data`。
* **空字符串的搜索值会被服务端清掉**：`search={'name_matches': ''}` 会被服务端剔除空白后 `302`；
  值为 `None` 由客户端直接省略，不会发出去。
* **`old_*` 是并发合并输入**：`post_update` 的 `old_tag_string` / `old_source` / `old_rating` /
  `old_parent_id` 要把你编辑前看到的值一起发出去，服务端据此避免覆盖别人的改动；它们不是本次要写入的值。
* **发帖分两步**：`upload_create` 只建上传，还要用返回的 `upload_media_assets[0]['id']` 调
  `post_create(upload_media_asset_id, ...)` 才发布，且这个 id 是**顶层**参数，不能塞进 `post[...]`。
* **能力依赖站点配置**：站点未配置 archive 服务时 `post_versions_list` / `pool_versions_list` 返回
  `501`；IQDB 未配置则 `iqdb_query` 返回空数组；推荐服务同样依赖站点配置，各自结果见
  [方法参考](danbooru-api.md)。
* **未知搜索参数被静默忽略**：参数名写错不报错，只表现为过滤没生效、返回全集。

命名规则：`xxx_list` 列表/搜索（`search` + `**params`），`xxx_show` 单条详情，`xxx_create` /
`xxx_update` / `xxx_delete` 写操作；ID 游标是 `page='a<ID>'`（更新方向）与 `'b<ID>'`（更旧方向），
没有通用 `cursor` 字段，翻页见 [pagination.md](pagination.md)。

## 边界与未实测

本节集中说明未执行、不可用与免责内容，主干用法不逐段重复这些限制。

* `danbooru.donmai.us` 的匿名只读验证共 15 次请求：12 次 `200`，`404` / `410` / `422` 各一次，另有
  `artist_show_or_new` 的 `302 → 200 JSON` 重定向验证。覆盖的方法：`post_list`（含 `tags` 与
  `page='b<id>'` 游标）、`post_show`、`tag_list`、`artist_list`（URL 匹配、布尔过滤、`order`、
  `any_name_matches`）、`artist_show_or_new`、`related_tag`、`wiki_page_list`、`wiki_page_show`、
  `comment_list`、`pool_list`。
* **其余 217 个方法只有源码依据，没有线上成功记录**；所有写操作（上传、发帖、评论、投票、编辑、删除、
  审核、站内信）都未执行，本仓库不带凭据，也没有为它们发过写请求。
* archive 版本历史、IQDB、推荐服务等可选能力的成功路径未实测；同族站点另有独立只读探测记录（Safebooru
  匿名可用且是 Danbooru 引擎）。
* 逐路径、逐身份与参数范围的完整记录以 [verification.md](verification.md) 为准；本次文档重排没有新增
  网络请求。
* 非 `with` 方式建立的客户端在示例结束后调用 `client.close()` 释放连接池。
