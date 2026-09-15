# Danbooru 客户端用法

```python
from pybooru import Danbooru
with Danbooru('danbooru') as client:                       # 读包内默认 pybooru.json
    print(client.wiki_page_show(client.config['examples']['danbooru']['wiki_title'])['title'])
```

真实字段值（2026-09-15 匿名验证中按标题查询得到的 `title`）：

```text
help:api
```

另一次执行 `examples/danbooru/related_tag.py` 得到 `query: touhou posts: 1096795` 与
`1girl`、`solo`、`hat`，逐条见 [verification.md](verification.md)。

`Danbooru` 类负责 Danbooru 引擎系站点的全部访问：读配置、构造请求、附加认证、把服务端 JSON
原样返回。方法清单见 [方法参考](danbooru-api.md)，按目的找入口见
[能力入口](danbooru-capabilities.md)，逐条路由与上游出处见 [契约审计附注](danbooru-contract-notes.md)。

## 构造

```python
Danbooru(site_name=None, site_url=None, username=None, api_key=None, proxies=None,
         *, config_file=None, timeout=None, user_agent=None)
```

`site_name` 是 `sites` 段的键名（如 `'danbooru'`、`'safebooru'`），同时决定读取哪个站点的
`api_key`；`config_file` 默认 `None`，即读随包安装的 `pybooru/pybooru.json`
（`pybooru.DEFAULT_CONFIG_FILE`），显式传路径才读别的文件，指到的文件不存在直接抛
`FileNotFoundError` 而不回落到默认文件或内置站点；其余参数显式覆盖配置文件同名值。见 [configuration.md](configuration.md)。

解析后的配置挂在公开属性 `config` 上：`config['request']['timeout']`（`30`）、
`config['sites']['danbooru']['url']`、`config['examples']['danbooru']['tags']`（`rating:g`）；
示例脚本都从 `config['examples']['danbooru']` 取关键词与条数，切换站点改 `client.site_url` 即可。

## 认证

`username` 或 `api_key` **任一非空**就附加 HTTP Basic（缺项按空串补），两项都空才匿名；权限由服务端
判定，返回 `401`（凭据无效/不完整，不会静默降级为匿名）或 `403`（权限不足），详见
[authentication.md](authentication.md)。

## 通用请求入口

`request(method, path, *, params=None, data=None, files=None)` 是所有原生方法的底座，没有原生方法的
JSON 路由也直接用它：

```python
client = Danbooru('danbooru')     # 本节自己构造一个，不依赖上面 with 块里已关闭的客户端
client.request('GET', 'explore/posts/popular.json', params={'scale': 'week', 'limit': 5})
client.request('POST', 'comments.json', data={'comment': {'post_id': 1, 'body': '示例评论'}})
```

* `method` 是 `'GET'` / `'POST'` / `'PUT'` / `'DELETE'` 等；`path` 带不带 `.json` 都可以
  （`'posts.json'` 与 `'posts'` 等价），开头的 `/` 会去掉；`params` 是查询参数（Rails 括号形式）；
  `data` 是结构化请求体；`files` 非空时请求体改用 multipart；
* **不做隐式兜底**：路径里的 ID 要调用者自己转义（`wiki_page_show` 已内置转义），不自动重试，
  网络错误、限流、5xx 全抛给调用者；
* **请求头固定**：`User-Agent` 取配置，`Accept: application/json`；会话 `trust_env=False`，
  代理只来自配置或显式参数，不读环境变量。

## 参数编码

查询串用 Rails 括号形式：嵌套 dict → `a[b]`，列表 → 重复键 `a[]`，布尔 → `true`/`false`，`None`
不发送。请求体分两套：**无文件发 JSON**（嵌套 dict 就是嵌套对象，结构原样保留），**带文件发
Rails 表单 / multipart**。无文件用 JSON 的意义是保留结构——`pool_update(pool_id, post_ids=[])`
会把显式空数组真的发出去（用于清空合集内容），表单编码会丢掉它。带文件的字段名是**字面**键
（`upload[files][0]`、`post_replacement[replacement_file]`）：requests 不为 multipart 字段展开括号，
键名由客户端按服务端约定拼好。

搜索字典（`search`）是嵌套结构，由原生方法放进 `search[...]` 层：

```python
client.tag_list(search={'name_matches': 'touhou'}, limit=2)      # 验证记录：touhou，tag id 29
client.related_tag(search={'query': 'touhou', 'order': 'frequency'}, limit=2)
```

**帖子的列表查询是例外**：它不读 `search` 字典，过滤条件全写在顶层 `tags` 里当元标签：

```python
client.post_list(tags='rating:g order:score', limit=10)
```

## 返回值与上一次请求

JSON 响应体解析后原样返回（dict / list / 标量，不改字段、不包装）；`204` 或空正文返回 `None`；
非 2xx 抛 `PybooruHTTPError`（带状态码、URL、响应内容），2xx 但非 JSON 抛 `PybooruAPIError`，
网络层异常原样抛出，见 [errors.md](errors.md)。`last_call` 记录每次请求的实际情况，其 `url` 是含查询串的最终地址，可直接排查“参数到底发成了什么样”：

```python
client.post_list(tags='rating:g', limit=2)
client.last_call  # {'API': 'posts.json', 'status_code': 200, 'status': 'OK', 'headers': {...},
              #  'url': 'https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=2'}
```

## 常见坑

* **帖子列表不吃 `search`**：写 `search={'tags': ...}` 会被静默忽略，表现为“返回最新全集”；
* **`GET` 不带请求体**：带 body 的 GET 由服务端 `400` 拒绝，客户端也不会把 `data` 放进 GET；
* **空字符串的 `search` 值会被清理**：服务端剔除空白项后 `302`，`None` 由客户端直接省略；
* **`old_*` 用于并发合并**：`post_update` 的 `old_tag_string` / `old_source` / `old_rating` /
  `old_parent_id` 把你编辑前看到的值一起发出去，服务端据此避免覆盖别人的改动；
* **发帖分两步**：`upload_create` 只是上传，还要用 `post_create(upload_media_asset_id, ...)` 发布，
  且该 id 是**顶层**参数；
* **能力依赖**：`post_versions_list` / `pool_versions_list` 在未配置 archive 服务的站点返回 `501`，
  IQDB 未配置时返回空数组；推荐服务也依赖站点配置，各自结果见方法参考。

命名规则：`xxx_list` 列表/搜索（`search` + `**params`），`xxx_show` 单条详情，`xxx_create` /
`xxx_update` / `xxx_delete` 写操作；ID 游标是 `page='a<ID>'` / `'b<ID>'`，没有通用 `cursor` 字段，
翻页见 [pagination.md](pagination.md)。

## 边界与未实测

`danbooru.donmai.us` 的早期匿名验证共 15 次：12×200 与 404/410/422 各一次，另有画师重定向验证。
读路径覆盖 `post_list`、`post_show`、`tag_list`、`artist_list`、`artist_show_or_new`、`related_tag`、
`wiki_page_list`、`wiki_page_show`、`comment_list`、`pool_list`；写路径、上传媒体与可选服务仍未实测。
同族站点另有独立探测：Safebooru 匿名可用且为 Danbooru。
逐路径、身份与参数范围以 [verification.md](verification.md) 为准；本次重排没有新增网络请求。
示例结束后用 `client.close()` 关闭非 `with` 方式建立的客户端。
