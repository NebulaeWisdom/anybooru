# Moebooru 客户端

`Moebooru` 类负责 Moebooru 引擎系站点（yande.re、konachan、sakugabooru 等）的访问：读取根配置、
构造请求、附加 `password_hash` 认证、把服务端 JSON 原样返回。

契约以本地只读的上游源码 `moebooru/`（HEAD `206455e1`）为准：路由看 `config/routes.rb`，
参数与权限看 `app/controllers/` 下各控制器（`ApplicationController`）。官方 `help/api` 页还在仓库里
（`app/views/help/api.en.html.erb`），但它的部分条目已经过期（例如仍在写 `post[file]` 可替换文件、
`post_show` 可用、`+/-1` 投票），**以当前路由与控制器为准**。

## 站点

根样例 `pybooru.json` 的 `sites` 段里，Moebooru 系条目都做过匿名线上探测，除注明外
均为「页脚显示运行 Moebooru、`help/api` 自述 API 版本、各只读列表端点返回 JSON」。
**下表是样例清单，不是支持边界**：任何跑 Moebooru 引擎的站点都可以用
`Moebooru(site_url=..., api_version=...)` 直接接入，不必先在配置里登记；反过来，
列在这里也不保证每个能力都可用（站点会自行关闭部分功能）。清单语义见
[configuration.md](configuration.md#sites-段)。

| 键 | 地址 | 站点自述 API 版本 | 备注 |
| :--- | :--- | :--- | :--- |
| `yandere` | `https://yande.re` | `1.13.0+update.3` | 上游项目的参考部署 |
| `konachan` | `https://konachan.com` | `1.13.0+update.3` | `.net` 是同站的**过滤镜像**（会少掉部分帖子），需要完整内容时用 `.com` |
| `sakugabooru` | `https://sakugabooru.com` | `1.13.0+update.3` | 动画作画片段站（视频向 fork），标签体系与图片站不同 |


> **验证状态**：接口契约已按上游源码对齐；部分匿名只读场景已在 yande.re 实际执行，
> 逐条结果见 [verification.md](verification.md)。全部写动作和账号认证仍**未实测**，
> 本库不在本地预判权限。

## 构造

```python
from pybooru import Moebooru

client = Moebooru('yandere', config_file='pybooru.json')
```

| 参数 | 说明 |
| :--- | :--- |
| `site_name` | `sites` 段的键名，如 `'yandere'`、`'konachan'`；站点条目里的 `url` / `username` / `password` / `hash_string` / `api_version` 按同名字段读入 |
| `site_url` | 显式覆盖站点地址；不通过 `site_name` 读取站点条目时必须同时给出 `api_version`，否则构造会失败 |
| `username` / `password` | 显式覆盖登录凭据（匿名只读不必填） |
| `hash_string` | 显式覆盖站点加盐模板（站点条目里为 `null` 时必须显式给出，否则无法登录） |
| `api_version` | 显式覆盖 API 版本，决定列表路径形态 |
| `proxies` | 显式覆盖代理 |
| `timeout` / `user_agent` | 显式覆盖超时与 `User-Agent` |
| `config_file` | 配置文件路径，默认当前工作目录的 `pybooru.json` |

构造参数优先于配置文件中的同名值。配置结构见 [configuration.md](configuration.md)。

```python
# 只读、匿名
client = Moebooru('yandere')

# 需要登录时：凭据同样可以显式传入
client = Moebooru('konachan', username='me', password='secret')

# 自定义站点：显式地址 + 显式 API 版本 + 加盐模板
client = Moebooru(site_url='https://example.org', api_version='1.13.0+update.3',
                  username='me', password='secret', hash_string='salt--{0}--')
```

## 读到的配置

解析后的根配置挂在 `config` 上，客户端从站点条目派生的字段也可直接读：

```python
client.config['sites']['yandere']['url']   # https://yande.re
client.api_version                         # 1.13.0+update.3
client.password_hash                       # 匿名构造时为 None
client.last_call                           # 上一次请求的最终 URL、状态码与响应头
```

## 通用请求入口

Moebooru 面与 Danbooru 面一样提供 `request()`，所有原生方法都是它的薄封装；缺少原生方法的端点
直接用 `request()`：

```python
client.request('GET', 'post', params={'tags': 'rating:s', 'limit': 3})
client.request('POST', 'post/vote', data={'id': 1, 'score': 1})
```

```python
request(method, path, *, params=None, data=None, files=None)
```

| 参数 | 说明 |
| :--- | :--- |
| `method` | HTTP 方法，如 `'GET'`、`'POST'`、`'PUT'`、`'DELETE'` |
| `path` | 相对路径，带不带 `.json` 都可以（`'post'` 与 `'post.json'` 等价） |
| `params` | 查询参数，按 Rails 括号形式拼进查询串 |
| `data` | 表单请求体（Moebooru 面**恒用 Rails 表单**，不是 JSON 请求体） |
| `files` | 上传文件；非 `None` 时请求体改为 multipart |

行为约定：

* **基础路径处理**：去掉开头的 `/`、补 `.json`；裸集合路径另按下述版本映射处理。路径里的 ID 由调用者自行转义；
* **列表路径的旧版本映射**：`api_version` 为 `1.13.0` / `1.13.0+update.1` / `1.13.0+update.2` 时，
  不带 `/` 的裸集合路径（`post`、`pool`、`note`、`tag`、`artist`、`comment`、`wiki`、`forum`、`user`）
  会补成 `/index`；配置里的三个站点都声明 `1.13.0+update.3`，走的是非 `/index` 形态；
* **表单而非 JSON 体**：`data` 一律编码成 Rails 表单（嵌套 dict → `a[b]`，列表 → 重复键 `a[]`，
  布尔 → `true`/`false`，`None` 不发送），这与 Danbooru 面无文件时使用 JSON 请求体不同；
* **认证自动附加**：配置了凭据时，`GET` / `HEAD` 把 `login` 与 `password_hash` 放进查询串，
  其他动词放进表单体；两项凭据都为空才是匿名；
* **不做隐式兜底**：不自动重试、不自动翻页、不做本地分页上限、不做客户端权限判断；
* **请求头固定**：`User-Agent` 取配置，`Accept: application/json`；会话关闭 `trust_env`，代理只来自配置；
* **文件由调用者管理**：传入的文件对象由调用者负责关闭。

## 返回值

| 服务端响应 | 返回值 |
| :--- | :--- |
| JSON 响应体 | 解析后的 Python 对象（dict / list / 标量），原样返回，不改字段、不包装 |
| `204 No Content` 或空响应体 | `None`（例如 `forum_mark_all_read`） |
| HTTP 错误状态 | 抛 `PybooruHTTPError`，带 `http_code` / `url` / `body` / `data`；`.data` 只在响应体本身是 JSON 时有值，HTML 错误页时为 `None` |
| 2xx 但响应体不是 JSON | 抛 `PybooruAPIError` |
| 网络层错误 | 原样抛出 requests 的异常 |

各族的实际形态（顶层数组、`{success:true}`、`batch_api_data`、跟随重定向后拿到的目标页 JSON）见
[moebooru-api.md 的响应形态](moebooru-api.md#响应形态)；异常类型见 [errors.md](errors.md)。

## 上一次请求的信息

每次请求后 `last_call` 都会更新为本次请求的情况（`API` 是相对路径，`url` 是包含查询串的最终地址）：

```python
client.post_list(tags='rating:s')
client.last_call   # {'API': 'post.json', 'url': ..., 'status_code': ..., 'status': ..., 'headers': ...}
```

排查“参数到底发成了什么样”时看 `url` 即可。

## 认证

Moebooru 不用 HTTP Basic：登录信息随请求一起提交，字段是 `login` 与 `password_hash`：

```
password_hash = SHA1(hash_string.format(password))
```

`hash_string` 是站点 `help/api` 约定的加盐模板（含 `{0}` 占位符），`username` / `password` /
`hash_string` 都来自根配置的站点条目：

```json
"sites": {
  "yandere": {
    "url": "https://yande.re",
    "username": "your-username",
    "password": "your-password",
    "hash_string": "choujin-steiner--{0}--",
    "api_version": "1.13.0+update.3"
  }
}
```

* 匿名只读请求不带登录字段；`password_hash` 在构造时算好，不参与后续每次请求的重新计算；
* `hash_string` 为 `null`（站点条目没有内置模板）且要登录时，必须显式传 `hash_string`；
* 服务端还接受 `username` + `api_key` 查询参数、会话 Cookie、`user[name]` + `user[password]` 明文等
  方式，本库只实现 `password_hash` 一种；`api_key` 身份受 `limit_api` 限制，只有 `json` / `xml` / `zip`
  格式被放行，所以这类客户端必须请求 `.json`。

细节见 [authentication.md](authentication.md)。

## 路由形态与格式

* **列表**：现役站点是 `GET /post.json`、`GET /pool.json`、`GET /note.json` 等；`/post/index.json`
  这类别名在上游已被标注 “FIXME: remove this”，官方帮助的版本记录也写明 `1.13.0+update.3` 移除了
  `/index`，新代码不要依赖别名；
* **单帖详情没有 JSON 端点**：`post/show` 在路由里带 `:format => false`（`routes.rb:153`），
  只渲染 HTML；请求 `/post/show.json` 会落到兜底路由 `errors#not_found`，得到**空正文 404**。
  取单帖请用 `post_list(tags='id:<id>')`（用 md5 时 `tags='md5:<hash>'`），需要外层信封再附带
  `api_version=2`；`id` 查询本身不要求 `api_version`；
* **HTML-only 不等于没有路由**：`post/browse`、`post/upload`、`tag/cloud`、`wiki/show`、
  `history/index` 等都有真实路由，只是只渲染页面 / JS / 订阅源，本库不提供对应包装方法；
* **`wiki_show` 已从 JSON 方法里移除**：`wiki/show` 的 `respond_to` 只有 `format.html`
  （`wiki_controller.rb:110-130`），请求 `.json` 得到 `406`，不是 “路由不存在”；
* 请求了不支持的格式时，Rails 会返回 `UnknownFormat`（`406`）或 `MissingTemplate`（`500`），
  取决于该动作是否声明了 JSON 分支。

## 写请求的重定向与结果歧义

`requests` 会跟随 `302` / `303` 并保留 `Accept`，所以**读到最终 JSON 是可能的**——例如
`tag_alias_create` 成功后重定向到 `tag_alias#index`，而该索引页支持 JSON。但要把两件事分开：

* **重定向不等于写入成功**：仅靠 flash 提示的校验失败也会重定向到同一目标页；
* **跟随重定向后的 200 不是写入确认**：它只是目标页面的读取结果。判定写入是否生效，最可靠的是
  写入后自己再查询一次目标资源；
* **`tag_alias_update` / `tag_implication_update` 的 Approve 分支重定向到 `job_task#index`**，
  该目标是 HTML-only：即使改动已经生效，调用方也可能拿到 `500` 或非 JSON 响应；**不要据此盲目重试**。

各方法的返回形态差异（`{success:true}`、目标页 JSON、或空成功）在
[moebooru-api.md](moebooru-api.md) 的“响应形态”一节按族列出。

## 原生方法命名

```python
def xxx_list(self, **params)                  # 列表 / 搜索：过滤与分页参数都在顶层
def xxx_show(self, xxx_id, **params)          # 单条详情
def xxx_create(self, 语义必需字段, **attributes)  # 写：必需字段显式，其余嵌套在模型名下
def xxx_update(self, xxx_id, **attributes)
def xxx_destroy(self, xxx_id)
```

* Moebooru **没有** Danbooru 的 `search={...}` 字典：`tags`、`query`、`name`、`limit`、`page` 等
  过滤条件本身就是**顶层参数**（`note/wiki/list` 里的 `query` 只是普通查询词名）；
* 写方法的属性按引擎的嵌套键名透传：`post[...]`、`pool[...]`、`note[...]`、`tag[...]`、
  `tag_alias[...]`、`wiki_page[...]`、`comment[...]`、`forum_post[...]`、`artist[...]`、`user[...]`；
* 引擎里按字符串比较的开关（`unflag`、`redo`、`forcegray`、`include_*`、`commit`）要传引擎期望的
  字面值（如 `'1'` / `'Yes'`），不要传 Python 布尔值。

完整签名与路由来源见 [moebooru-api.md](moebooru-api.md)，按目的查找见
[moebooru-capabilities.md](moebooru-capabilities.md)。

## 用法示例

示例脚本从根配置的 `examples.moebooru` 段读取参数（当前配置指向 `yandere`），全部为匿名只读：

```python
from pybooru import Moebooru

with Moebooru('yandere', config_file='pybooru.json') as client:
    example = client.config['examples']['moebooru']

    for post in client.post_list(tags=example['tags'], page=example['pages'][0], limit=example['limit']):
        print(post['id'], post['file_url'])

    for tag in client.tag_list(limit=example['limit'], order=example['tag_order']):
        print(tag['name'], tag['count'])

    related = client.tag_related(tags=example['related_tags'], type=example['related_type'])
    for name, count in related[example['related_tags']][:example['limit']]:
        print(name, count)
```

可运行脚本（参数全部来自根配置，不硬编码站点与代理）：

```bash
.venv/Scripts/python.exe examples/moebooru/list_posts.py
.venv/Scripts/python.exe examples/moebooru/list_tags.py
.venv/Scripts/python.exe examples/moebooru/wiki_list.py
.venv/Scripts/python.exe examples/moebooru/list_comments.py
.venv/Scripts/python.exe examples/moebooru/related_tags.py
```

| 脚本 | 用途 | 用到的配置键 |
| :--- | :--- | :--- |
| `list_posts.py` | 按标签分页列出帖子 | `tags`、`limit`、`pages` |
| `list_tags.py` | 按 `order` 列出标签 | `limit`、`tag_order` |
| `wiki_list.py` | 搜索 wiki 页面 | `wiki_query`、`limit` |
| `list_comments.py` | 用 `comment_search` 读取评论流并打印条数；`comment_list` 不带 `post_id` 时查询会退化成 `post_id=0` 并返回空数组，所以全局评论走前者 | `comment_query`、`limit`、`preview_chars` |
| `related_tags.py` | 查询相关标签，保留按查询标签分组的原始形态 | `related_tags`、`related_type`、`limit` |

`--config` 指定配置文件路径，`--site` 覆盖站点名（留空取 `examples.moebooru.site`）。

## 关闭与上下文管理

```python
client = Moebooru('yandere')
try:
    posts = client.post_list(tags='rating:s')
finally:
    client.close()

with Moebooru('yandere') as client:          # 等价写法
    posts = client.post_list(tags='rating:s')
```

## 与 Danbooru 面的差异

| 项目 | Danbooru 面 | Moebooru 面 |
| :--- | :--- | :--- |
| 通用请求入口 | `request(method, path, *, params, data, files)` | 同名同签名，但 `data` **恒为 Rails 表单**，无 JSON 请求体分支 |
| 列表参数风格 | `xxx_list(search={...}, **params)`，过滤编码成 `search[...]` | 没有 `search` 字典，过滤条件与分页同在顶层 |
| 认证 | HTTP Basic | `login` + `password_hash`；GET 进查询串，其他动词进表单 |
| 单帖详情 | `post_show(post_id)` | 没有 `post_show`：`post_list(tags='id:<id>')` |
| API 版本 | 不需要 | `api_version` 影响列表路径的 `/index` 形态 |
| 权限模型 | Pundit 策略 | 控制器 `before_action` 过滤器 + 模型方法，无独立策略层 |

下一步的延伸阅读：端点契约 [moebooru-api.md](moebooru-api.md)、能力总览
[moebooru-capabilities.md](moebooru-capabilities.md)、线上证据 [verification.md](verification.md)。
