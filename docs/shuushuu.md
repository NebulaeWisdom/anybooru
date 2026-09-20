# e-shuushuu 客户端用法

`Shuushuu` 访问 e-shuushuu（`https://e-shuushuu.net`）的 REST 接口。REST 这里指资源路径 + HTTP 方法 + JSON。站点前端是 SvelteKit、后端是 FastAPI，接口自称 **Shuushuu API 2.0.0**，全部挂在 `/api/v1` 下。和 Gelbooru 那种“一个 `index.php` 用 `page`/`s` 分发”的老式接口不同。

默认匿名。只有显式给出 `access_token` 时才随请求发送 `Authorization: Bearer <token>`。配置了 `username`/`password` 也不会自动登录。

接口分三类：**35 个公开读方法**（图片、标签、搜索、用户、评论、新闻、站点配置）、**1 个私有读方法** `user_ratings`（只有本人或有 `USER_EDIT_PROFILE` 权限的版主能看）、**5 个认证方法**（登录、续期、当前用户、登出、全部登出）。逐条参数表与返回字段见[方法参考](shuushuu-api.md)，按目的找入口见[按目的找方法](shuushuu-capabilities.md)，接口依据、权限与排除项见[接口依据与排除项](shuushuu-contract-notes.md)。

## 第一次调用：标签名换 tag_id

筛图接口只认 **tag_id**（标签编号），不认标签名。先搜标签拿编号：

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    hits = client.search(q='long hair', limit=5)
    # GET https://e-shuushuu.net/api/v1/search?q=long+hair&limit=5
    # 返回 {"query": "long hair", "entity": "tags", "hits": [{"tag_id": 46, "title": "long hair",
    #       "type": 1, "usage_count": ..., "is_alias": False, ...}, ...], "total": ..., "limit": 5, "offset": 0}
    for hit in hits['hits']:
        print(hit['tag_id'], hit['title'], hit['usage_count'])
```

给 `q` 和 `limit` → 返回 `query`、`entity`、`hits`、`total`、`limit`、`offset`；`hits` 每项有 `tag_id`、`title`、`type`、`usage_count`、`is_alias` 等。代码注释里 `46`/`long hair` 的对应与字段名来自接口文档既有记录（T）和官方 OpenAPI 的 schema 名；本库自己的执行记录见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。

拿到 `tag_id` 后筛图：

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    page = client.image_list(tags='46,169', tags_mode='all', tag_depth=0,
                             per_page=2, sort_by='favorites', sort_order='DESC')
    # GET https://e-shuushuu.net/api/v1/images?tags=46%2C169&tags_mode=all&tag_depth=0
    #     &per_page=2&sort_by=favorites&sort_order=DESC
    # 返回 {"total": ..., "page": 1, "per_page": 2, "images": [ ... ], "comments": null}
    for image in page['images']:
        print(image['image_id'], image['width'], image['height'], image['url'])
```

`image_list` 给 `tags`、`tags_mode`、`tag_depth`、`per_page`、`sort_by`、`sort_order` → 返回 `total`、`page`、`per_page`、`images`、`comments`。`images` 每项是完整图片对象：`image_id`、`filename`、`md5_hash`、`width`、`height`、`caption`、`source_url`、`status`、`rating`、`favorites`、`tags`、`url`、`thumbnail_url`、`medium_url`、`large_url` 等。字段逐条见[方法参考](shuushuu-api.md)。上面的请求 URL 与返回字段来自接口自身的参数与 schema 定义。

匿名只读已真实跑过一轮：10 次冒烟请求里 8 次 `200`、1 次 `422`（`per_page` 超上限）、1 次 `404`（不存在的图片编号）；两个示例脚本各 4 次 `200`，全部退出码 `0`、stderr 为空。逐条命令、URL 与响应摘要见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。

## 构造与配置

签名：`Shuushuu(site_name=None, site_url=None, username=None, password=None, access_token=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 中的键名 | 不选命名站点，需显式给 `site_url` | `Shuushuu('shuushuu')` |
| `site_url` | 字符串，站点根地址，不带 `/api/v1` | 读取所选站点的 `url` | `Shuushuu(site_url='https://e-shuushuu.net')` |
| `username` | 字符串，登录用户名；**不会自动登录** | 有站点名时读取其 `username`，否则为 `None` | `Shuushuu('shuushuu', username='myname')` |
| `password` | 字符串，登录密码；只在显式调用 `auth_login()` 时使用 | 有站点名时读取其 `password`，否则为 `None` | `Shuushuu('shuushuu', password='secret')` |
| `access_token` | 字符串；非空就随请求发送 `Authorization: Bearer <token>`，`''` 表示不带 | 有站点名时读取其 `access_token`，否则为 `None` | `Shuushuu('shuushuu', access_token='')` |
| `proxies` | 字典，按 `http` / `https` 指定代理，`{}` 表示直连 | 使用 `request.proxies`，包内为 `{}`；不读环境变量 | `Shuushuu('shuushuu', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json`；指定文件不存在直接抛错 | `Shuushuu('shuushuu', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout`，包内为 `30` | `Shuushuu('shuushuu', timeout=10)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent`，包内为 `Anybooru/0.1.0.dev1` | `Shuushuu('shuushuu', user_agent='MyBooruApp/1.0')` |

包内站点条目为：

```json
{"shuushuu": {"url": "https://e-shuushuu.net", "username": "", "password": "", "access_token": ""}}
```

复制完整配置的方法见[配置指南](configuration.md)。显式构造参数优先于配置；空字符串是“明确留空”，`None` 才回落到站点条目。用完调用 `client.close()`，或用 `with` 语句块。

## 认证：默认匿名，登录必须显式调用

匿名请求不带 `Authorization` 头。受保护接口匿名访问会得到 **`401`**，响应头带 `www-authenticate: Bearer`（接口文档记录过这个行为）。Bearer 指把 token 放进 `Authorization` 头的方式；Cookie 指站点下发、由客户端会话保存并携带的小段凭据，HTTPOnly 表示脚本读不到。

五个认证方法（**本轮没有执行过任何一个**，都按接口定义与参数写入）：

| 方法 | 请求 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| `auth_login(username=None, password=None)` | `POST https://e-shuushuu.net/api/v1/auth/login`（JSON 体） | 用户名 + 密码（`username` 3–30 字符、`password` 至少 1 字符；不传就用配置里的 `username`/`password`）→ `{"access_token": "…", "token_type": "bearer", "expires_in": 1800, "user": {…}\|null}`；接口描述写明 refresh token 会写进 HTTPOnly Cookie，接口文档另记录登录同时下发 `access_token` 与 `refresh_token` 两个 Cookie；客户端把 `access_token` 记到 `client.access_token` |
| `auth_refresh()` | `POST https://e-shuushuu.net/api/v1/auth/refresh`（无请求体） | 不带参数，**靠 Cookie 里的 `refresh_token`** 换新的 access token（并轮换 refresh token）→ 同为 `{"access_token", "token_type", "expires_in", "user"}` |
| `auth_me()` | `GET https://e-shuushuu.net/api/v1/auth/me` | 不带参数，用当前凭据 → 当前用户资料对象；接口对它的 200 只声明“任意键的对象”，没有给出字段表，客户端原样返回 |
| `auth_logout()` | `POST https://e-shuushuu.net/api/v1/auth/logout` | 吊销 Cookie 里的 refresh token（access token 会在 30 分钟内自然过期）→ `{"message": "…"}`；成功后客户端清掉本地 token 与 Cookie |
| `auth_logout_all()` | `POST https://e-shuushuu.net/api/v1/auth/logout-all` | 用当前 Bearer 吊销该用户全部 refresh token → `{"message": "…"}` |

两个要点：

* **不会自动登录**：构造时给了 `username`/`password` 也不会自动换成 token，必须自己调用 `auth_login()`。手动拿到 token 时可以直接构造 `Shuushuu('shuushuu', access_token='…')`。
* **token 过期不会自动续期**：需要续期时显式调用 `auth_refresh()`；`refresh` 的凭据在 Cookie 里，不在请求体，调用前要保持同一个 `client`（同一个会话）的 Cookie。

## 通用 request：完整路径自己给

签名：`request(method, path, *, params=None, data=None, files=None)`。

路径要把 `api/v1` 一起写上（与 Serika 的通用入口相同），客户端不猜资源、不加版本号：

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    config = client.request('GET', 'api/v1/meta/config')
    # GET https://e-shuushuu.net/api/v1/meta/config
    # 返回 {"max_search_tags": 5, "max_search_users": 5, "max_image_size": 33554432,
    #       "max_avatar_size": 1048576, "upload_delay_seconds": 30, "search_delay_seconds": 2,
    #       "tag_types": {"0": "All", "1": "Theme", …}, "ml_tag_suggestions_enabled": true, …}
    # 这里的数值来自接口文档记录的一次匿名响应（T）；字段名来自官方 OpenAPI 的 PublicConfig
    print(config['max_search_tags'], config['tag_types'])
```

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串，`GET/POST/PATCH/PUT/DELETE` 等；允许哪个动词由站点决定 | 必填 | `client.request('GET', 'api/v1/meta/config')` |
| `path` | 站点相对路径，带 `api/v1`，不带查询串 | 必填 | `client.request('GET', 'api/v1/images/1119196')` |
| `params` | 扁平查询字典，布尔小写、`None` 省略、序列重复同名键 | `None`，不发查询参数 | `client.request('GET', 'api/v1/images', params={'tags': '46', 'per_page': 2})` |
| `data` | JSON 对象；`files` 不是 `None` 时改走表单 | `None`，不发请求体 | `client.request('POST', 'api/v1/auth/login', data={'username': 'myname', 'password': 'secret'})` |
| `files` | requests 文件字典或二元组列表，文件对象由调用者关闭 | `None`，不启用文件表单 | `files={'file': ('image.png', file_object, 'image/png')}`，`file_object` 是调用者用 `open('image.png', 'rb')` 打开的文件 |

客户端**不做**这些事：不拆响应外层（返回什么 JSON 就给你什么）、不钳位 `page`/`per_page`（不把超范围值改回允许值）、不自动翻页、不重试、不回退、不本地校验参数。它只支持 JSON 响应：Atom 订阅源（`/api/v1/images.atom`）、图片与头像文件路由、随机图 302 跳转都不封装，也**不会解码**。

## 参数编码

查询参数按扁平字典发送，规则只有四条：

* **布尔**写成小写字符串：`include_comments=True` → `include_comments=true`。
* **`None` 不发送**；想表达“不传”就直接省略该参数。
* **多值参数重复同一个键**：`status=[1, 2]` → `status=1&status=2`（不是 `status[]=1&status[]=2`）。
* **逗号串必须自己拼成字符串**：`tags='46,169'`，不要写 `tags=['46','169']`，也不要写成 `tags='46+169'`。

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    images = client.image_list(tags='46,169', tags_mode='all', status=[1], per_page=2)
    # GET https://e-shuushuu.net/api/v1/images?tags=46%2C169&tags_mode=all&status=1&per_page=2
    print(images['total'], len(images['images']))
```

`tags=1+2` 这种写法在服务端会被当成非法值并把过滤条件**静默丢掉**（接口文档记录的一次匿名请求返回了全库 `total=1087908`），所以客户端不会替你转换分隔符，也不会替你把列表还原成逗号串。

## 返回值与 last_call

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | 解析后的 Python 对象，一层都不拆：列表接口是 `{"total", "page", "per_page", "<资源>": [...]}`，详情接口是单个对象 |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`、`data`；`422` 的 `data` 是 FastAPI 的校验错误对象 |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError`（例如误用 `request()` 去取 Atom 或媒体文件） |
| 网络错误 | requests 自己的异常原样抛出，没有重试 |

每次收到响应后 `client.last_call` 是最近一次的情况：`API`（站点相对路径，不含 HTTP 方法）、`url`（含查询串的最终地址）、`status_code`、`status`、`headers`。核对“参数发成什么样”看它：

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    client.tag_show(46)
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://e-shuushuu.net/api/v1/tags/46
```

## 常见坑

1. **筛图只认 tag_id**：`tags`、`exclude_tags`、`missing_tag_types` 收的都是编号串，不是标签名。按名字查只有 `search(q=…)` 与 `tag_list(search=…)` 两个入口。
2. **`tags` 用英文逗号，不能用 `+`**：`tags=46,169` 是“同时含 46 与 169”（配 `tags_mode='all'`）；写成 `tags='46+169'` 会被当非法值、过滤被静默丢弃，返回整库。
3. **`/api/v1/search` 搜的是标签，不是图片**：它的 `entity` 恒为 `"tags"`，传 `entity=`、`query=`、`search=`、`term=` 都无效；图片搜索在 `image_list`。
4. **`/api/v1/tags` 没有 `limit` 参数**：传 `limit` 会被忽略，每页只认 `per_page`（默认 20，最大 100）。要限制条数用 `per_page`。
5. **`per_page` 上限是 100**：传 101 或 200 会得到 `422`（接口文档记录的报错是 `Input should be less than or equal to 100`）；`page` 从 1 开始。客户端不钳位，参数照发。
6. **`/tags/{id}/images` 与 `/images?tags={id}` 的 `total` 不一样**：前者会自动跟随别名与子标签、用的是基础图片对象（**没有 `tags` 数组**）；后者是完整图片对象。要算“某标签共有多少图”，以你实际调用的那个接口的 `total` 为准。
7. **站点限制看 `/api/v1/meta/config`**：`max_search_tags`、`max_search_users`、`max_image_size`、`search_delay_seconds` 等都在这里（客户端不读、不替你限流）。
8. **没有限流响应头**：接口文档记录的 200/401 响应都不带 `X-RateLimit-*`，站点由 Cloudflare 前置；客户端不做节流、不做退避。
9. **私有接口不要当公开接口用**：`user_ratings` 只有本人或持 `USER_EDIT_PROFILE` 的版主能看；其余 `/users/me*`、`/images/recommended`、`/images/bookmark/*`、`/privmsgs/*` 等需要登录，本库没有把它们封成方法（见[排除项](shuushuu-contract-notes.md)）。

## 可运行示例

两个脚本都匿名只读，`--config` 省略时读包内默认配置，`--site` 可覆盖站点名；参数全部来自 `examples.shuushuu`，脚本不硬编码分页或条数：

```bash
.venv/Scripts/python.exe examples/shuushuu/search_images.py
.venv/Scripts/python.exe examples/shuushuu/browse_resources.py
```

* `search_images.py`：先 `search(q='long hair')` 拿到标签，再按该标签的 `tag_id` 翻 `pages` 指定的页码调 `image_list`，最后对第一页第一张图调用 `image_show`；打印每次的 `method`、`status_code`、`url` 与返回的关键字段。
* `browse_resources.py`：`tag_show(46)`、`comment_list(image_id=1118862, per_page=2)`、`user_list(search='whitekitten', per_page=2)`、`news_list(per_page=1)` 各一次，同样只打印方法、状态码、URL 与少量字段。

两个脚本都以显式空凭据构造（匿名）。已实际运行：**各 4 次请求、全部 `200`、退出码 `0`、stderr 为空**；逐条命令与输出摘要见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。

## 边界与未实测

* 本页的请求 URL、参数范围与返回字段名来自官方 OpenAPI 描述（`https://e-shuushuu.net/api/openapi.json`）与随附的接口文档。真实执行只覆盖 10 个公开读方法（`search`、`tag_list`、`image_list`、`image_show`、`tag_show`、`comment_list`、`image_stats`、`meta_config`、`user_list`、`news_list`，见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)），其余方法**没有跑过**；接口文档记录过的事情不等于本库跑过，本页也不把两者混写。
* **5 个认证方法一次都没执行**：登录、续期、`auth_me`、登出、全部登出都只有接口定义与参数依据；账号锁定、refresh token 轮换、Cookie 行为都未实测；T 记录 `auth_me` 匿名返回401，本次没有调用。
* **`user_ratings` 是私有接口**：本人或持 `USER_EDIT_PROFILE` 才可见；本库没有用过凭据实测它。
* 35 个公开资源读方法中，多数只按 OpenAPI 描述对齐；`status-history` 会按查看者身份隐藏部分字段，其匿名成功响应与身份差异都没有本轮样本，不能把分类当成已测通过。
* **没有原生方法**：上传、打标签、评分、收藏、评论写入、私信、`/api/v1/admin/*` 管理面、机器学习建议、推荐与书签、横幅与捐赠。JSON 路径可通过 `request()` 显式调用，不会自动发生。
* Atom、图片/头像与随机图跳转不是 JSON；本客户端不解析这些响应，应另用 HTTP 客户端读取媒体。

继续阅读：[方法参考](shuushuu-api.md) · [按目的找方法](shuushuu-capabilities.md) ·
[接口依据与排除项](shuushuu-contract-notes.md) · [错误处理](errors.md)。
