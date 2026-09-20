# Serika 客户端用法

`Serika` 与 `Danbooru` / `Moebooru` / `E621` / `Zerochan` / `Gelbooru` 并列，是六个引擎客户端之一，访问 `serika.art` 及同引擎的自托管实例。同一个 `Serika` 类提供两套接口：

- **官方接口 `/api/v1/*`**：带版本号，站点自述为 `SerikaART API 1.0.0`，共 16 个方法。其中 4 个（`api_index`、`stats`、`user_list`、`random_image`）不带 API key 也能读，另外 12 个要 key。
- **站内接口 `/api/*`**：没有版本号、没有兼容承诺，是 serika.art 网页前端自己调用的路由，共 14 个方法；本库统一加 `internal_` 前缀，全部可以不带任何凭据读取（评论、标签、画师、用户都在这面）。

选哪面看[能力总览](serika-capabilities.md)，逐条签名与返回字段看[方法参考](serika-api.md)；本页只回答“这个类怎么用”。

最小用法，复制即可运行，不需要 key：

```python
from anybooru import Serika

with Serika('serika') as client:
    info = client.api_index()        # GET https://serika.art/api/v1
    print(info['name'], info['version'])
```

```text
SerikaART API 1.0.0
```

`Serika('serika')` 里的 `'serika'` 是随包默认配置 `anybooru/anybooru.json` 里 `sites` 段的键，它的 `url` 是 `https://serika.art`。上面打印的两个值是 2026-09-15 匿名调用的真实输出，命令与逐调用响应摘要见 [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。

## 构造与自托管实例

```text
Serika(site_name=None, site_url=None, api_key=None, proxies=None,
       *, config_file=None, timeout=None, user_agent=None)
```

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `site_name` | str，配置 `sites` 段的键 | 用这个键下的 `url` 与 `api_key` | `None`：不选站点条目，必须给 `site_url`；两个都不给时找不到 `url`，构造会抛 `KeyError` | `Serika('serika')` |
| `site_url` | str，站点根地址 | 直接指定要访问的地址，替换站点条目里的 `url` | `None`：取 `sites.<site_name>.url`，末尾的 `/` 会被去掉 | `Serika(site_url='https://serika.art')` |
| `api_key` | str | 官方接口的凭据 | `None`：取 `sites.<site_name>.api_key`。空字符串不发送认证头；非空则每个请求都带 `Authorization: Bearer <key>` | `Serika('serika', api_key='sk_serika_xxx')` |
| `proxies` | dict，requests 的 `proxies` | 每个请求都带上 | `None`：取配置 `request.proxies` | `Serika('serika', proxies={'https': 'http://proxy.example:3128'})` |
| `config_file` | 文件路径 | 读哪个参数文件 | `None`：读随包安装的 `anybooru/anybooru.json`；给路径则读那个文件 | `Serika('serika', config_file='my.json')` |
| `timeout` | 数字，或 `[连接秒数, 读取秒数]` | requests 的超时 | `None`：取配置 `request.timeout`；列表形式在构造时转成元组 | `Serika('serika', timeout=10)` |
| `user_agent` | str | 每个请求的 `User-Agent` | `None`：取配置 `request.user_agent` | `Serika('serika', user_agent='my-app/1.0')` |

会话固定只加两个请求头：`User-Agent`（上面的值）与 `Accept: application/json`。`trust_env` 被关掉，`HTTP_PROXY` 这类环境变量不会生效，代理只能走 `proxies` 参数或配置文件。构造参数里没有 `username`、密码或密码哈希——`Serika` 把它们写死为空值，也不读 `sites.<站点>.username`，因为官方 API key 与站内会话 token 是两种不同的凭据，本库只实现前者的发送。

自托管实例：在配置 `sites` 下新增一个和 `sites.serika` 同结构的两字段条目（`url` + `api_key`），把 `url` 改成实例根地址，再把这个键传给 `Serika`；也可以用 `Serika(site_url='https://实例地址')` 直接给地址。没有自动探测、没有引擎自动切换，也不需要改代码。配置是应用输入：示例里的分页、评级与图片尺寸都来自 [anybooru.json](../anybooru/anybooru.json)。

用完记得 `client.close()`，或像上面那样用 `with` 语句块。

## 通用请求入口

原生方法都是下面这个入口的一行封装，参数原样交给服务端：

```text
request(method, path, *, params=None, data=None, files=None, binary=False, envelope=None)
```

| 参数 | 类型与取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `method` | str，`'GET'` / `'POST'` / `'DELETE'` 等 | 原样交给 requests | 必填 | `'GET'` |
| `path` | str，相对路径 | 拼在站点地址后面；不会自动补 `.json` 或 API 版本，开头的 `/` 会被去掉 | 必填 | `'api/v1/stats'` |
| `params` | dict | 查询串。`None` 的值不发送；布尔编码成小写 `true` / `false`；列表编码成重复的 `key[]` | `None`：不带查询串 | `{'limit': 3, 'sort': 'newest'}` |
| `data` | dict | 没有 `files` 时是 JSON 请求体，值里的 `None` 会被去掉、显式空数组保留；有 `files` 时改成表单字段 | `None`：不带请求体 | `{'ids': [7323837]}` |
| `files` | dict | multipart 文件，键是字段名 | `None`：请求体走 JSON | `{'file': ('a.png', fh, 'image/png')}` |
| `binary` | bool | `True` 时返回原始字节，不做 JSON 解码 | `False`：按 JSON 解析 | `True` |
| `envelope` | `None` / `'data'` / `'users'` | 只对官方两套响应结构生效，见下节 | `None`：原样返回整个 JSON | `'data'` |

三件要自己负责的事：`path` 里的动态段（图片编号、用户名、标签名）在通用入口不转义，要自己 `quote()`；库不检查 key 权限、不钳位参数、不自动重试、不自动翻页；官方接口的错误不会改走站内路由。另外官方接口的 `tags`、`ratings`、`exclude_tags` 是逗号分隔的字符串（如 `'blue archive,1girl'`），不是列表，也不是 Danbooru 的搜索表达式。请求体的两种形状别混：`image_batch` 的 `ids` 走 JSON 数组 `{"ids": [...]}`，`upload` 的 `tags` 是 multipart 表单里的文本字段，两个都用 `data=` 传，但一个有 `files=`、一个没有，服务端读的位置不同。

同一个 `client` 可以一直用通用入口调没有原生封装的路由：

```python
from anybooru import Serika

with Serika('serika') as client:
    body = client.request('GET', 'api/v1/stats')                    # GET https://serika.art/api/v1/stats
    print(body['data']['totals']['images'])  # 图片总数在整个响应的 data -> totals -> images 中
    statistics = client.request('GET', 'api/v1/stats', envelope='data')
    # GET https://serika.art/api/v1/stats；只返回 data 对应的统计信息字典。
    print(sorted(statistics))  # ['activity', 'images_by_rating', 'images_by_type', 'totals']
```

## 返回值与 last_call

服务端的正文结构决定你拿到什么，库不做形状猜测：

| 调用 | 你拿到的 Python 值 | 其余信息在哪 |
| :--- | :--- | :--- |
| `api_index()` | 整个响应对象：`{"name": "SerikaART API", "version": "1.0.0", "description": ..., "documentation": ..., "endpoints": ..., "authentication": ..., "rate_limits": ...}` | 这个路由没有 `data` / `meta`，所有键都在返回对象里 |
| 官方其余 15 个方法 | 响应里 `data` 字段的内容（图片数组、标签数组、单个对象等） | 整个 `meta` 放进 `last_call['meta']`，里面有 `timestamp`，分页路由还有 `pagination` |
| `user_list()` | 响应里 `users` 数组，每项 `{_id, id, username, avatarUrl, rank, createdAt, uploadCount}` | 分页在 `last_call['meta']['pagination']`（只有 `page` / `limit` / `total` / `pages`） |
| `random_image()` | 图片字节，Python 类型是 `bytes` | `Content-Type` 与 `X-Image-Id` / `X-Post-Id` 等响应头在 `last_call['headers']` |
| `internal_*()` | 整个响应对象，例如 `{"success": true, "images": [...], "pagination": {...}}` 或 `{"success": true, "tag": {...}}` | 分页就在返回对象里；官方那套 `data` / `meta` 拆分不适用于站内面 |
| 正文为空的 2xx | `None`（JSON 通路）、`b''`（`binary=True`） | `last_call` 仍然记录这次请求 |

`request()` 的 `envelope` 默认 `None`，原样返回整个 JSON；`envelope='data'` 与 `envelope='users'` 是官方两套已知结构的显式开关，不做后备字段搜索。`last_call` 是普通字典，键为 `API`（相对路径）、`url`（真实完整地址）、`status_code`、`status`（如 `OK`）、`headers`，官方两套结构再加 `meta`。它只表示最近一次请求，下一次调用会先清空，跨请求要保留的分页得自己先存下来。非 2xx 抛异常时 `last_call` 依然是这一次请求的记录。

下面的片段同时看到 `user_list` 的数组返回、分页位置与 `last_call`：

```python
from anybooru import Serika

with Serika('serika') as client:
    users = client.user_list(page=1, limit=1, sort='newest')
    # GET https://serika.art/api/v1/users?page=1&limit=1&sort=newest
    print(users[0]['username'])                        # 2026-09-15 实测：Giru
    print(client.last_call['status_code'])             # 200
    print(client.last_call['meta']['pagination'])      # {'page': 1, 'limit': 1, 'total': 3058, 'pages': 3058}
```

站内面的返回是整个字典，不要只取其中一个字段：

```python
from anybooru import Serika

with Serika('serika') as client:
    listing = client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')
    # GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest
    first = listing['images'][0]
    print(listing['success'], listing['pagination'])   # True {'page': 1, 'limit': 3, 'total': 3499663, ...}
    print(first['id'], first['post_id'], first['rating'], first['url'])
    # 2026-09-15 实测：7323837 4237836 safe https://cdn.serika.art/uploads/1788013605888-1788013605888-1q2b2g-danbooru-12074741.png
```

`random_image()` 返回字节，不是 JSON：

```python
from anybooru import Serika

with Serika('serika') as client:
    picture = client.random_image(400, 400, fit='cover', format='png', ratings='safe')
    # GET https://serika.art/api/v1/random/400/400/image.png?fit=cover&format=png&ratings=safe
    print(type(picture).__name__, len(picture))              # bytes 81224（2026-09-15 实测字节数）
    print(client.last_call['headers']['Content-Type'])       # image/png
    print(client.last_call['headers'].get('X-Image-Id'))     # 2026-09-15 实测 2796776；占位图没有这个头
```

## 五个要记住的坑

1. **两类图片编号不互换**：官方 `image_show` / `image_delete` / `image_similar` / `image_batch` 要内部图片 id（响应里的 `id` / `dbid`），站内 `internal_image_show` / `internal_image_comments` 要公开序号（响应里的 `post_id`）。同一张图 2026-09-15 实测 `id=7323837`、`post_id=4237836`，两个数字不同；官方文档页给 v1 详情标的是顺序号，实现查的却是内部 id，以控制器为准。
2. **`safe` 默认只出现在一部分路由**：带评级过滤的列表、随机、搜索与热门路由，不传 `ratings` 时只看 `safe`（服务端的回退行为，不是客户端补的）；详情、similar 等路由按各自规则来，详情不加评级条件，similar 强制与源图同评级。
3. **未知标签不总是 404**：官方图片列表与 `random_list` 只在部分标签名解析不到时回 `404 TAG_NOT_FOUND`；全部解析不到时是 `200` 加空数组。站内图片列表还受服务端标签缓存影响，二进制随机图在标签无交集时可能返回不含这些标签的随机图。
4. **二进制 `200` 不等于选到了图**：无匹配时服务端返回灰色占位 PNG，控制器内部出错时返回红色占位 PNG，两者都是 HTTP `200`；只有真正命中才带 `X-Image-Id` / `X-Post-Id` 这些头。客户端照原样返回字节，不会替换成别的图片。
5. **错误的数字文本不等于不传参数**：例如把数量写成非数字文本，服务端 `parseInt` 得到 `NaN`，并不保证改用默认数量。数量范围、排序值和过滤规则见方法参考，不要依赖无效输入的结果。

逐条源码对照见[契约审计附注](serika-contract-notes.md#官方文档矛盾逐条)，本页只留使用时要记住的结论。

## 错误处理

非 2xx 在 JSON 与二进制两条通路里都抛 `AnybooruHTTPError`，异常对象带 `http_code`（状态码）、`url`、`body`（原始正文）、`data`（正文能解析成 JSON 时是那个字典，否则是 `None`）、`response`。服务端给了 JSON `code` 时用 `error.data['code']` 读。2xx 但正文非空又解析不了 JSON 时抛 `AnybooruAPIError`；网络层的异常保持 requests 的原异常不变。

```python
from anybooru import AnybooruHTTPError, Serika

with Serika('serika') as client:
    try:
        client.internal_image_show(999999999)     # GET https://serika.art/api/images/999999999
    except AnybooruHTTPError as error:
        print(error.http_code, error.data)         # 404 {'success': False, 'error': 'Image not found'}
    try:
        client.random_image(8, 8)                 # GET https://serika.art/api/v1/random/8/8/image.png
    except AnybooruHTTPError as error:
        print(error.http_code, error.data)         # 400 None：这个分支的正文是纯文本，不是 JSON
```

第一条的可读法：站内详情路由把“图不存在”和“图已删除/未列出”都答成 404 加同一个 `error` 文本，两者不能区分（源码分支，本页未实测这一次 404）。第二条的可读法：`width` / `height` 只接受 16..8000，越界的正文是纯文本，所以 `error.data` 是 `None`，要看 `error.body`。

官方 v1 的缺 key / key 缺权限 / 限流分别是 HTTP `401` / `403` / `429`，但三种情况的正文 `code` 都可能等于 `UNAUTHORIZED`，只能连 HTTP 状态码与原始正文一起判断；只有“删别人的图且 rank 不是 admin/owner”这一条给 `FORBIDDEN`。详见 [errors.md](errors.md)。

## 可运行示例

三个脚本都支持 `--config` 与 `--site`：`--config` 省略即读包内默认配置，`--site` 留空则取 `examples.serika.site`，只调用匿名可达的路径。

```bash
.venv/Scripts/python.exe examples/serika/service_info.py
.venv/Scripts/python.exe examples/serika/browse.py
.venv/Scripts/python.exe examples/serika/random_image.py
```

- `service_info.py`：`api_index()`（整个响应对象）、`stats()`（返回 `data` 字段的内容、`meta` 留在 `last_call`）、`user_list(page=1, limit=1, sort='newest')`（返回 `users` 数组、分页在 `last_call`），一次看到三种返回形态。
- `browse.py`：`internal_image_list(...)` 取 3 张图 → 用首图的 `post_id` 调 `internal_image_show` 查同一张图的详情 → `internal_tag_list(...)` 与 `internal_artist_list(...)`；不拿内部 id 去查站内详情。
- `random_image.py`：`random_image(400, 400, ...)` 读字节，打印字节数、真实 `Content-Type` 与响应头，不保存图片。

三条命令均已实际运行、退出 `0`，合计 **8 个 HTTP 200**（4 个官方 v1 + 4 个站内）；命令与逐调用输出见 [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。

## 边界与未实测

- 已经实测的只有上面那 8 次匿名调用（官方 `api_index`、`stats`、`user_list`、`random_image`，站内 `internal_image_list`、`internal_image_show`、`internal_tag_list`、`internal_artist_list`）。
- **官方 12 个需 key 的方法成功路径全部未实测**：本轮 `api_key` 保持空值，不申请、不索要凭据；站内另外 10 个方法只有源码对齐，没有发过请求。
- 自托管部署（换 `site_url` 指到别的实例）未实测；认证成功路径、权限与限流、上传与删除、灰色/红色占位 PNG 的错误分支、各参数组合均未实测。本页的源码级结论来自站点控制器，没有为它们额外发探测请求。
- 逐条状态与排除项见[契约审计附注](serika-contract-notes.md#路由清单与逐条状态)；能力与不提供的范围见[能力总览](serika-capabilities.md#本库不提供的能力)。
