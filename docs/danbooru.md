# Danbooru 客户端

`Danbooru` 类负责 Danbooru 引擎系站点的全部访问：读取根配置、构造请求、附加认证、把服务端 JSON
原样返回。

## 构造

```python
from pybooru import Danbooru

client = Danbooru('danbooru', config_file='pybooru.json')
```

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `site_name` | str | `sites` 段的键名，如 `'danbooru'`、`'safebooru'` |
| `config_file` | str | 配置文件路径，默认当前工作目录下的 `pybooru.json` |
| `site_url` | str | 显式覆盖站点地址 |
| `username` | str | 显式覆盖用户名 |
| `api_key` | str | 显式覆盖 API key |
| `proxies` | dict | 显式覆盖代理 |
| `timeout` | number | 显式覆盖超时秒数 |
| `user_agent` | str | 显式覆盖 `User-Agent` |

构造函数参数优先于配置文件中的同名值；`config_file` 指向的文件不存在时直接抛 `FileNotFoundError`，
不会回落到任何内置站点。配置结构的完整说明见 [configuration.md](configuration.md)。

## 读到的配置

解析后的配置挂在公开属性 `config` 上：

```python
client.config['request']['timeout']              # 30
client.config['sites']['danbooru']['url']        # https://danbooru.donmai.us
client.config['examples']['danbooru']['tags']    # rating:g
```

可以随时改 `site_url` 属性切换站点地址：

```python
client.site_url = 'https://safebooru.donmai.us'
```

## 通用请求入口

所有原生方法都是 `request()` 的薄封装。需要访问还没有原生方法的端点时，直接用 `request()`：

```python
client.request('GET', 'posts.json', params={'tags': 'rating:g', 'limit': 3})
client.request('GET', 'posts/1.json')
client.request('POST', 'comments', data={'comment': {'post_id': 1, 'body': '示例评论'}})
```

```python
request(method, path, *, params=None, data=None, files=None)
```

| 参数 | 说明 |
| :--- | :--- |
| `method` | HTTP 方法，如 `'GET'`、`'POST'`、`'PUT'`、`'DELETE'` |
| `path` | 相对路径，带不带 `.json` 都可以（`'posts.json'` 与 `'posts'` 等价） |
| `params` | 查询参数，都会按 Rails 括号形式拼进 URL 的查询串 |
| `data` | 结构化请求体（嵌套 dict 就是一层嵌套键） |
| `files` | 上传的文件；非 `None` 时请求体改用 multipart 编码 |

行为约定：

* **不做隐式兜底**：`path` 就是站点根地址之后的那一段，只做两件事——去掉开头的 `/`、缺 `.json` 时补上；
  路径里的 ID 需要调用者自己转义，客户端不猜测、不改写；
* **不自动重试**：网络错误、限流、5xx 都直接把结果抛给调用者；
* **权限交给服务端**：`username` 或 `api_key` 任一非空就附加 HTTP Basic（缺项为空串），两项都空才匿名；
  不做本地鉴权判断；
* **请求头固定**：`User-Agent` 取配置，`Accept: application/json`；
* **不走环境变量代理**：会话关闭了 requests 的 `trust_env`，代理只来自配置或显式参数。

## 参数编码

分两套编码，取决于这次请求有没有文件：

| 情形 | 编码方式 |
| :--- | :--- |
| `params`（查询串） | Rails 括号形式：嵌套 dict → `a[b]`，列表 → 重复键 `a[]`，布尔 → `true`/`false`，`None` 不发送 |
| `data`（请求体，无文件） | **JSON 请求体**：嵌套 dict 就是嵌套的 JSON 对象，结构原样保留 |
| `data` + `files`（有文件） | Rails 表单 / multipart 编码（同下表的括号规则） |

无文件时用 JSON 请求体的意义在于**保留结构而不是压成字符串**：例如
`pool_update(pool_id, post_ids=[])` 会把显式的空数组真的发出去（用于清空合集内容），
而表单编码会把它丢掉。`None` 值同样不会被发送。

有文件时（`upload_create(files=[...])`）走 multipart，文件字段用**字面**键名：

```python
upload[files][0]
```

requests 不会为 multipart 字段展开括号，所以这类字段名要按服务端约定原样书写。

搜索字典（`search`）也是嵌套结构，由原生方法负责放进对应的层：

```python
client.tag_list(search=example['tag_search'], limit=example['limit'])
client.related_tag(search={'query': example['related_query'], 'order': example['related_order']},
                   limit=example['limit'])
```

有一个例外要记住：**帖子列表不读 `search` 字典**，它的过滤条件全部写在 `tags` 查询串里作为元标签
（`rating:g`、`score:>10`、`order:score`、`limit:50`）：

```python
client.post_list(tags='rating:g order:score', limit=10)
```

## 返回值

| 服务端响应 | 返回值 |
| :--- | :--- |
| JSON 响应体 | 解析后的 Python 对象（dict / list / 标量），原样返回，不改字段、不包装 |
| `204 No Content` 或空响应体 | `None` |
| HTTP 错误状态 | 抛 `PybooruHTTPError`，携带状态码、URL 与响应内容 |
| 网络层错误 | 原样抛出 requests 的异常 |

详见 [errors.md](errors.md)。

## 上一次请求的信息

每次请求后，`last_call` 都会更新为本次请求的实际情况：

```python
posts = client.post_list(tags=example['tags'])
client.last_call
# {'API': 'posts.json',
#  'url': 'https://danbooru.donmai.us/posts.json?tags=rating%3Ag',
#  'status_code': 200,
#  'status': 'OK',
#  'headers': {...}}
```

`url` 是包含查询串的最终地址，可以直接用于排查“参数到底发成了什么样”。

## 原生方法

Danbooru 面为常用资源提供了原生方法，命名规则统一：

```python
def xxx_list(self, search=None, **params)   # 列表 / 搜索
def xxx_show(self, xxx_id)                  # 单条详情
def xxx_create / xxx_update / xxx_delete    # 写操作（需要登录）
```

* `search` 是**完整的搜索参数字典**，整包透传成 `search[...]`，不做白名单拦截；
* 其余顶层参数（`limit`、`page`、`tags` 等）走 `**params` 原样发送；ID 游标是 `page='a<ID>'` / `'b<ID>'`，没有通用 `cursor` 字段；
* 分页相关见 [pagination.md](pagination.md)。

```python
posts = client.post_list(tags=example['tags'], limit=example['limit'])
tags = client.tag_list(search=example['tag_search'], limit=example['limit'])
post = client.post_show(posts[0]['id'])
```

完整端点清单（含认证要求、画师查询语义与路由来源）见 [danbooru-api.md](danbooru-api.md)。

## 关闭与上下文管理

客户端持有可复用的连接会话，用完关掉即可：

```python
client = Danbooru('danbooru')
try:
    posts = client.post_list(tags=example['tags'])
finally:
    client.close()
```

也可以直接用上下文管理器：

```python
with Danbooru('danbooru') as client:
    posts = client.post_list(tags=example['tags'])
```
