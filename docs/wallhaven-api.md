# Wallhaven 方法参考

Wallhaven（`https://wallhaven.cc`）不是本包任何一种 booru 引擎的部署：它在站点根下自带一套 JSON API v1（路由都在 `/api/v1/...`），账号密钥作为查询值 `apikey`（或请求头 `X-API-Key`）传递，详情返回 `{"data": {...}}`、列表返回 `{"data": [...], "meta": {...}}`。这些形状与 Danbooru/Moebooru 系都不同，所以它是独立家族。

本页列出 `Wallhaven` 的全部 **7 个原生方法，全是只读 `GET`**，逐条对应站点 [官方 API 页面](https://wallhaven.cc/help/api)（标题 *API v1 Documentation*）的七条路由：

| 方法 | 路由（拼在站点根后） | 官方页面小节 | 返回外层 |
| :--- | :--- | :--- | :--- |
| [`wallpaper_search()`](#wallpaper_search) | `GET /api/v1/search` | Searching and listings（`#search`） | `{"data": [...], "meta": {...}}` |
| [`wallpaper_show()`](#wallpaper_show) | `GET /api/v1/w/{wallpaper_id}` | Accessing Wallpaper information（`#wallpapers`） | `{"data": {...}}` |
| [`tag_show()`](#tag_show) | `GET /api/v1/tag/{tag_id}` | Tag info（`#tags`） | `{"data": {...}}` |
| [`user_settings()`](#user_settings) | `GET /api/v1/settings` | User Settings（`#user-settings`） | `{"data": {...}}` |
| [`collection_list()`](#collection_list) | `GET /api/v1/collections` | User Collections | `{"data": [...]}` |
| [`user_collections()`](#user_collections) | `GET /api/v1/collections/{username}` | User Collections | `{"data": [...]}` |
| [`collection_wallpapers()`](#collection_wallpapers) | `GET /api/v1/collections/{username}/{collection_id}` | User Collections | `{"data": [...], "meta": {...}}`（`meta` 无 `query`/`seed`） |

官方页面里 User Collections 小节把 `id` 写成了 `#user-settings`（与上一节重复），链接仍指向官方页面的 User Collections 一节；本页按标题引用。

另有通用入口 [`request()`](#通用入口-request)，用来调用这 7 条之外的站点相对路径。

“类怎么用、参数怎么编码、`last_call` 在哪看”见[客户端用法](wallhaven.md)；“我要做什么 → 用哪个方法”见[能力入口](wallhaven-capabilities.md)；依据出处、排除项与文档/实测矛盾见[契约审计附注](wallhaven-contract-notes.md)；真实 URL、状态码、`Content-Type` 见[验证记录](verification.md#wallhaven匿名只读实测2026-10-03)。

## 依据与阅读方式

本页每条结论标注来源：

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **官方** | 官方 API 页面 <https://wallhaven.cc/help/api>（本轮匿名 `GET` 为 `200 text/html`） | 路径、查询参数名与取值、默认值、认证方式、限流与错误状态、响应示例的字段形状 |
| **实测** | 本轮对站点发起的匿名只读 `GET`（串行、不重试、不跟随跳转、不下载媒体、不带任何凭据） | 对应路由当次的状态码、`Content-Type`、错误体、信封键、字段是否出现、参数是否被采纳 |
| **客户端** | 本包 `Wallhaven` 自身固定行为（构造、路径拼法、参数进查询串方式、返回值） | 调用形态、参数编码、返回值、异常 |

规矩：

* **参数表**的名称、枚举、默认值以**官方**页面为准；**状态码、错误体、信封键、字段是否被采纳**以**实测**为准，两者冲突时照实写并指出。
* 数字（`total`、`last_page`、`views`、条数）都是**当次快照**，站点内容随时变化，只作例子。
* **未实测**的路径（带密钥成功、私有收藏、`429` 触发、`X-API-Key` 头）集中标在各自小节与[边界与未实测](#边界与未实测)，不当契约。
* 本页不引用输入研究文档，也不编造服务端源码行号 / OpenAPI schema：本轮没有取得墙纸站的服务端源码或 OpenAPI 规范。

## 客户端与通用约定（**客户端**）

* **类**：`Wallhaven`，用法与其它家族一致：`with Wallhaven('wallhaven') as client:`。
* **构造**：`Wallhaven(site_name=None, site_url=None, apikey=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。`apikey=None` 读包内配置 `sites.wallhaven.apikey`；显式传 `apikey=''` 保持匿名（即使配置里有密钥也不用）；非空密钥每个请求作为查询值 `apikey` 发出。构造函数不联网、不登录。
* **站点根**：`https://wallhaven.cc`，不是 `https://wallhaven.cc/api/v1`。`api/v1` 属于路径一部分，每个原生方法自带。真实 URL = 站点根 + `/` + 方法路径。
* **路径段编码**：`wallpaper_id`、`tag_id`、`username`、`collection_id` 逐个按 `quote(str(x), safe='')` 编码后拼入路径（**客户端**），直接传 Python 字符串 / 整数即可；客户端不校验它们的形状，站点怎么回就怎么抛。
* **查询参数编码**：`**params` 原样进查询串。共享编码器把 `None` 值的键丢掉、布尔写成小写 `true`/`false`、嵌套字典写成 `key[child]`、序列写成重复的 `key[]`。因此**列表值要写字面逗号串**：`resolutions='1920x1080,1920x1200'`，不要写 `resolutions=['1920x1080', '1920x1200']`（后者会变成 `resolutions[]=...`）。客户端不填默认值、不钳位、不猜上限、不改参数名。
* **认证**：官方页面给两种等价方式——URL 加 `?apikey=<API KEY>`，或请求头 `X-API-Key: <API KEY>`。客户端只会把**配置的密钥**作为 `apikey` 查询值发送；要用请求头形式，在该次调用显式传 `headers={'X-API-Key': '<你的密钥>'}`，客户端不会两种都发、也不会替你补。单次调用可用 `params={'apikey': ''}` 或 `params={'apikey': '<另一个密钥>'}` 覆盖本次的查询值（**客户端**）。
* **相似与用户入口**：官方页面只列 7 条路径，没有单独列出“相似壁纸”或“用户资料/上传”路径；相似壁纸用搜索 `q='like:<wallpaper_id>'`，用户上传用搜索 `q='@<username>'`。客户端不为它们另造方法，也不把候选路径 `/w/{id}/similar`、`/user` 当接口（见[契约审计附注](wallhaven-contract-notes.md#3-相似与用户入口官方-7-条路径里没有独立路由)）。
* **返回**：成功 JSON 正文完整解析后原样返回，不拆 `data`、不改字段名、不转换类型。列表就是 `{"data": [...], "meta": {...}}` 这个字典本身；详情就是 `{"data": {...}}`。
* **错误**：非 2xx 抛 `AnybooruHTTPError`（带 `http_code` / `url` / `body` / `data`），站点自己的状态码与错误体原样保留；客户端不重试、不降级、不把错误正文补成正常结构。
* **`last_call`**：最近一次请求的 `API`（去掉前导 `/` 的路径原文，如 `api/v1/search`）、`url`、`status_code`、`status`、`headers`。调试真实 URL 先看 `client.last_call['url']`。
* **媒体**：`path`、`thumbs`、`avatar` 都只是**原样字符串**；客户端不请求、不拼接、不改写，也没有任何下载方法。

## 通用入口 request()

`request(method, path, *, params=None, headers=None)`

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串，如 `'GET'` | 必填（Python 报缺参） | `client.request('GET', 'api/v1/search')` |
| `path` | 站点相对路径；前导 `/` 会被去掉后拼在站点根后，例如 `'api/v1/search'` 与 `'/api/v1/search'` 是同一路由 | 必填 | `client.request('GET', 'api/v1/tag/1')` |
| `params` | 查询参数字典，经共享编码后拼进查询串；配置的密钥会先并进来，再被本次同名键覆盖（`apikey=''` 可让本次匿名） | `None`，只带配置的密钥（若有） | `client.request('GET', 'api/v1/search', params={'q': 'nature', 'page': 2})` |
| `headers` | 本次请求的额外请求头字典，原样发送 | `None`，只带客户端默认头 | `client.request('GET', 'api/v1/settings', headers={'X-API-Key': '<你的密钥>'})` |

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    page = client.request('GET', 'api/v1/search', params={'q': 'nature', 'page': 2})
    # 真实 URL：GET https://wallhaven.cc/api/v1/search?q=nature&page=2
    # 实测：200 application/json，{"data": [...24 条...], "meta": {...}}
    print(client.last_call['url'], client.last_call['status_code'])
```

## 壁纸

### wallpaper_search

给什么：`wallpaper_search(**params)`。给一组官方搜索参数，返回一页壁纸摘要。路由 `GET /api/v1/search`，官方页面 **Searching and listings** 一节。不带参数时官方页面说明“显示最新 SFW 壁纸”；传 `apikey` 时按该账号的浏览设置与默认过滤执行。每页固定 24 条（官方页面原文 *Listings are limited to 24 results per page*），没有可传的 `per_page`。

| 参数 | 取值（**官方**） | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `q` | 搜索语法的字符串，见[下面的 q 语法](#q-搜索语法) | 主搜索条件 | 未规定（不传即不加该参数；等效于浏览最新） | `client.wallpaper_search(q='nature')` |
| `categories` | 三位 0/1 字符串，顺序 general/anime/people；官方默认 `111` | 打开(1)或关闭(0)三大分类 | 服务端用 `111`（全开） | `client.wallpaper_search(categories='100')` |
| `purity` | 三位 0/1 字符串，顺序 sfw/sketchy/nsfw；官方默认 `100` | 打开(1)或关闭(0)三档分级；官方原文 *NSFW requires a valid API key* | 服务端用 `100`（仅 SFW） | `client.wallpaper_search(purity='110')` |
| `sorting` | `date_added`（默认）、`relevance`、`random`、`views`、`favorites`、`toplist` | 结果排序方式 | 服务端用 `date_added` | `client.wallpaper_search(sorting='views')` |
| `order` | `desc`（默认）、`asc` | 升降序 | 服务端用 `desc` | `client.wallpaper_search(sorting='views', order='asc')` |
| `topRange` | `1d`、`3d`、`1w`、`1M`（默认）、`3M`、`6M`、`1y` | 榜单时间范围；官方原文 *Sorting MUST be set to 'toplist'* | 服务端用 `1M`（仅在 `sorting='toplist'` 时有意义） | `client.wallpaper_search(sorting='toplist', topRange='1w')` |
| `atleast` | 分辨率，如 `1920x1080` | 最低允许分辨率 | 未规定 | `client.wallpaper_search(atleast='1920x1080')` |
| `resolutions` | 一个精确分辨率，或多个用逗号拼成一个字符串，如 `1920x1080,1920x1200`；官方原文 *Single resolution allowed* | 精确分辨率清单 | 未规定 | `client.wallpaper_search(resolutions='1920x1080,1920x1200')` |
| `ratios` | 一个宽高比，或多个逗号串，如 `16x9,16x10`；官方原文 *Single ratio allowed* | 宽高比清单 | 未规定 | `client.wallpaper_search(ratios='16x9,16x10')` |
| `colors` | 单个六位十六进制色值（不带 `#`）；官方页面 Search by color | 按主色搜索 | 未规定 | `client.wallpaper_search(colors='660000')` |
| `page` | 页码，从 `1` 开始（官方标注 ¹ Not actually infinite） | 第几页 | 未规定（观察为第 1 页） | `client.wallpaper_search(page=2)` |
| `seed` | 六个 `[a-zA-Z0-9]` 字符，如 `abc123` | 固定 `sorting='random'` 的随机种子 | 未规定（服务端会自己产生并在 `meta.seed` 回显） | `client.wallpaper_search(sorting='random', seed='abc123')` |

官方参数表里带 `*` 的默认值（`categories` `111`、`purity` `100`、`sorting` `date_added`、`order` `desc`、`topRange` `1M`）是**服务端**默认：客户端不传这些参数时不会在 URL 里补上它们，例如 `client.wallpaper_search()` 的真实 URL 是 `https://wallhaven.cc/api/v1/search`（**客户端**）。

#### q 搜索语法

`q` 是单个字符串，官方页面给出以下形态（可组合的用空格分隔）：

| 写法 | 含义 | 字面示例 |
| :--- | :--- | :--- |
| `tagname` | 模糊匹配标签 / 关键词 | `q='nature'` |
| `-tagname` | 排除标签 / 关键词 | 与下一条合写成 `q='+nature -anime'` |
| `+tag1 +tag2` | 必须同时含 tag1 与 tag2 | `q='+nature +anime'` |
| `+tag1 -tag2` | 必须含 tag1 且不含 tag2 | `q='+nature -anime'` |
| `@username` | 某账号的上传 | `q='@LewisMweir13'` |
| `id:123` | 精确标签搜索（官方原文 *can not be combined*，指不能再与其它 `q` 表达式组合；`purity`、`page` 等其它查询参数仍可一起传） | `q='id:1'` |
| `type:png` / `type:jpg` | 按文件类型（`jpg` = `jpeg`） | `q='type:png'` |
| `like:<wallpaper ID>` | 找出标签相似的壁纸（官方把相似壁纸写成这个搜索语法） | `q='like:pom5lj'` |

#### colors 的 29 个取值

官方页面 Search by color 列出以下 29 个色值（去掉 `#` 的六位十六进制），客户端原样发送其中之一：

```
660000  990000  cc0000  cc3333  ea4c88  993399
663399  333399  0066cc  0099cc  66cccc  77cc33
669900  336600  666600  999900  cccc33  ffff00
ffcc33  ff9900  ff6600  cc6633  996633  663300
000000  999999  cccccc  ffffff  424153
```

#### 返回字段

外层 `{"data": [...], "meta": {...}}`。`data` 是这一页的**壁纸摘要**数组（每项键如下），`meta` 是分页信息。

`data[]` 每项（**实测**样本 `pom5lj`）：

| 键 | 类型 | 含义 / 样本 |
| :--- | :--- | :--- |
| `id` | str | 六字符站内编号，`"pom5lj"` |
| `url` | str | 网页地址，`"https://wallhaven.cc/w/pom5lj"` |
| `short_url` | str | 短链，`"https://whvn.cc/pom5lj"` |
| `views` | int | 浏览量，`6` |
| `favorites` | int | 收藏数，`0` |
| `source` | str | 来源链接，常为空串；详情样本里出现过 `"https://www.artstation.com/artwork/EaDPkK"` |
| `purity` | str | `"sfw"` / `"sketchy"` / `"nsfw"` |
| `category` | str | `"general"` / `"anime"` / `"people"` |
| `dimension_x` | int | 宽，`3840` |
| `dimension_y` | int | 高，`2160` |
| `resolution` | str | `"3840x2160"` |
| `ratio` | str | 宽高比字符串，`"1.78"` |
| `file_size` | int | 字节数，`878885` |
| `file_type` | str | MIME，`"image/jpeg"` 或 `"image/png"` |
| `created_at` | str | 上传时间，`"2026-10-03 05:19:29"` |
| `colors` | str[] | 5 个带 `#` 的主色，如 `["#000000", "#663300", "#e7d8b1", "#424153", "#996633"]` |
| `path` | str | 原图地址（原样字符串），`"https://w.wallhaven.cc/full/po/wallhaven-pom5lj.jpg"` |
| `thumbs` | object | 缩略图三档：`large` / `original` / `small`，值都是原样 URL |

摘要项**没有** `uploader`、`tags`——这两个键只在详情里出现。

`meta` 键（**实测**）：

| 键 | 类型 | 含义 |
| :--- | :--- | :--- |
| `current_page` | int | 当前页 |
| `last_page` | int | 站点给出的最后一页 |
| `per_page` | int | 每页条数，实测恒为 `24` |
| `total` | int | 命中总数（快照，会变） |
| `query` | str / null / object | 回显的查询：普通关键词回显原串（`"nature"`），无关键词为 `null`，某些条件回显空串 `""`，`id:N` 精确标签搜索回显对象 `{"id": 1, "tag": "anime"}` |
| `seed` | str / null | `sorting='random'` 时服务端给的种子，否则 `null` |

#### 实测（匿名 `GET`）

| 调用 | 真实 URL | 状态与关键返回 |
| :--- | :--- | :--- |
| `wallpaper_search()` | `GET https://wallhaven.cc/api/v1/search` | `200`；`data` 24 条，首条 `pom5lj`；`meta` `current_page=1,last_page=20890,per_page=24,total=501359,query=null,seed=null` |
| `wallpaper_search(q='nature')` | `GET https://wallhaven.cc/api/v1/search?q=nature` | `200`；`meta.total=73383,last_page=3058,query="nature"` |
| `wallpaper_search(categories='100')` | `...?categories=100` | `200`；`meta.total=337624` |
| `wallpaper_search(purity='110')` | `...?purity=110` | `200`；`meta.total=623918` |
| `wallpaper_search(purity='001')` | `...?purity=001` | `200`；`data=[]`，`meta.total=0,last_page=1`（匿名**没有** 401，也没有 NSFW 结果） |
| `wallpaper_search(q='nature', sorting='relevance')` | `...?q=nature&sorting=relevance` | `200`；`meta.total=73383` |
| `wallpaper_search(sorting='random', seed='abc123', page=1)` | `...?sorting=random&seed=abc123&page=1` | `200`；`meta.seed="wPpR1H"` |
| `wallpaper_search(sorting='random', seed='abc123', page=2)` | `...?sorting=random&seed=abc123&page=2` | `200`；`meta.seed="vMFVjx"`（**与第 1 页不同**，见[契约审计附注](wallhaven-contract-notes.md)） |
| `wallpaper_search(sorting='views', order='asc')` | `...?sorting=views&order=asc` | `200`；`data` 只有 2 条，而 `meta.per_page=24,total=501359`（短页不等于结果结束） |
| `wallpaper_search(sorting='favorites')` | `...?sorting=favorites` | `200`；`meta.total=501359` |
| `wallpaper_search(sorting='toplist', topRange='1w')` | `...?sorting=toplist&topRange=1w` | `200`；`meta.total=483,last_page=21` |
| `wallpaper_search(atleast='1920x1080')` | `...?atleast=1920x1080` | `200`；`meta.total=388133` |
| `wallpaper_search(resolutions='1920x1080,1920x1200')` | `...?resolutions=1920x1080%2C1920x1200` | `200`；`meta.total=151776` |
| `wallpaper_search(ratios='16x9,16x10')` | `...?ratios=16x9%2C16x10` | `200`；`meta.total=269019` |
| `wallpaper_search(colors='660000')` | `...?colors=660000` | `200`；`meta.total=38986` |
| `wallpaper_search(page=2)` | `...?page=2` | `200`；`meta.current_page=2` |
| `wallpaper_search(q='id:1')` | `...?q=id%3A1` | `200`；`meta.total=117056,query={"id":1,"tag":"anime"}` |
| `wallpaper_search(q='type:png')` | `...?q=type%3Apng` | `200`；`meta.total=115883,query=""` |
| `wallpaper_search(q='+nature -anime')` | `...?q=%2Bnature+-anime` | `200`；`meta.total=36460,query="+nature -anime"` |
| `wallpaper_search(q='@LewisMweir13')` | `...?q=%40LewisMweir13` | `200`；`data` 24 条，`meta.total=46,last_page=2,query=""` |

`q='like:<id>'`（官方文档中的相似壁纸写法）本轮两次都返回 `403 text/html`（Cloudflare 质询页，`Cf-Mitigated: challenge`），不是 JSON；客户端不解挑战、不绕过、不重试。这只是一次观察，不推广成 `like:` 永远不可用。

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    page = client.wallpaper_search(q='nature', page=2, sorting='relevance')
    # 真实 URL：GET https://wallhaven.cc/api/v1/search?q=nature&page=2&sorting=relevance
    # 实测同类：200 application/json
    print(client.last_call['url'], client.last_call['status_code'])
    print(page['meta']['current_page'], page['meta']['last_page'], page['meta']['total'])
    for w in page['data']:
        print(w['id'], w['resolution'], w['purity'], w['path'])
```

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    page = client.wallpaper_search(
        q='+nature -anime',
        categories='111',
        purity='100',
        resolutions='1920x1080,1920x1200',
        ratios='16x9,16x10',
        colors='660000',
        sorting='toplist',
        order='desc',
        topRange='1w',
    )
    # 真实 URL：GET https://wallhaven.cc/api/v1/search?
    #   q=%2Bnature+-anime&categories=111&purity=100&resolutions=1920x1080%2C1920x1200
    #   &ratios=16x9%2C16x10&colors=660000&sorting=toplist&order=desc&topRange=1w
    # 各参数单独实测均为 200 application/json；此组合未逐项实测
    print(page['meta'])
```

### wallpaper_show

给什么：`wallpaper_show(wallpaper_id, **params)`。给一个六字符站内编号，返回这张壁纸的完整详情（摘要字段 + 上传者 + 标签）。路由 `GET /api/v1/w/{wallpaper_id}`，官方页面 **Accessing Wallpaper information** 一节。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `wallpaper_id` | 字符串路径段，必填，如 `'pom5lj'` | 壁纸编号，即搜索摘要的 `id` | 必填 | `client.wallpaper_show('pom5lj')` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 官方只给 `apikey` 一个可选查询值 |

返回 `{"data": {...}}`：`data` 是搜索摘要的全部键，**再加**：

| 键 | 类型 | 含义 / 样本 |
| :--- | :--- | :--- |
| `uploader` | object | `{"username": "LewisMweir13", "group": "User", "avatar": {...}}` |
| `uploader.avatar` | object | 四档头像 URL，键是 `"200px"` / `"128px"` / `"32px"` / `"20px"`（不是合法 Python 标识符，用 `['200px']` 取） |
| `tags` | object[] | 每项：`id`（int）、`name`（str）、`alias`（str，可为空）、`category_id`（int）、`category`（str）、`purity`（str）、`created_at`（str） |

**实测**：

* `GET https://wallhaven.cc/api/v1/w/pom5lj` → `200 application/json`；`data.uploader.username="LewisMweir13"`、`group="User"`、头像四档；`data.tags` 4 项（`Geralt of Rivia` / `The Witcher 3: Wild Hunt` / `Playstation 5` / `Toussaint`），每项都带 `category` 与 `purity`。
* `GET https://wallhaven.cc/api/v1/w/9mjoy1` → `200`；`data.views=856409`、`favorites=5759`、`source="https://www.artstation.com/artwork/EaDPkK"`、8 个标签（`samurai`、`digital art`、`Mount Fuji`、`Japan`、`cherry blossom` 等）。
* `GET https://wallhaven.cc/api/v1/w/94x38z`（官方页面的示例编号）→ **`404 {"error": "Nothing here"}`**：示例里的壁纸已不存在。
* `GET https://wallhaven.cc/api/v1/w/000000` → `404 {"error": "Nothing here"}`。
* `GET https://wallhaven.cc/api/v1/w/pom5lj/similar`（把 `similar` 当子路径的候选写法）→ `404 {"error": "Not Found"}`：官方 7 条路径里没有它，相似壁纸走搜索。

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    wallpaper = client.wallpaper_show('pom5lj')
    # 真实 URL：GET https://wallhaven.cc/api/v1/w/pom5lj
    # 实测：200 application/json
    print(wallpaper['data']['id'], wallpaper['data']['resolution'])
    print(wallpaper['data']['uploader']['username'], wallpaper['data']['uploader']['group'])
    print(wallpaper['data']['uploader']['avatar']['128px'])
    for tag in wallpaper['data']['tags']:
        print(tag['id'], tag['name'], tag['category'], tag['purity'])
```

相似壁纸（用官方支持的搜索写法，不要走 `/w/{id}/similar`）：

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    client.wallpaper_search(q='like:pom5lj')
    # 真实 URL：GET https://wallhaven.cc/api/v1/search?q=like%3Apom5lj
    # 本轮实测：403 text/html（Cloudflare 质询页，不是 JSON），客户端抛 AnybooruHTTPError；
    # 不绕过、不重试。取到 200 JSON 时，返回的是与普通搜索相同的 {"data": [...], "meta": {...}}
```

## 标签

### tag_show

给什么：`tag_show(tag_id, **params)`。给一个数字标签编号，返回该标签。路由 `GET /api/v1/tag/{tag_id}`，官方页面 **Tag info** 一节。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | 数字路径段，必填 | 标签编号，即壁纸标签里的 `id`，`1` 是 `anime` | 必填 | `client.tag_show(1)` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 官方只给 `apikey` 一个可选查询值 |

返回 `{"data": {...}}`：

| 键 | 类型 | 含义 / 样本 |
| :--- | :--- | :--- |
| `id` | int | 标签编号，`1` |
| `name` | str | 标签名，`"anime"` |
| `alias` | str | 别名，`"Japanese cartoon, 動漫"`（可为空串） |
| `category_id` | int | 分类编号，`1` |
| `category` | str | 分类名，`"Anime & Manga"` |
| `purity` | str | `"sfw"` / `"sketchy"` / `"nsfw"` |
| `created_at` | str | 创建时间，`"2014-02-02 10:44:37"` |

**实测**：`GET https://wallhaven.cc/api/v1/tag/1` → `200 application/json`，`data.name="anime"`、`alias="Japanese cartoon, 動漫"`、`category="Anime & Manga"`、`purity="sfw"`。`GET https://wallhaven.cc/api/v1/tag/0` → `404 {"error": "Nothing here"}`。

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    tag = client.tag_show(1)
    # 真实 URL：GET https://wallhaven.cc/api/v1/tag/1
    # 实测：200 application/json
    print(tag['data']['id'], tag['data']['name'], tag['data']['category'])
```

## 账号与收藏

以下四条路由的官方页面小节是 **User Settings**（`settings`）与 **User Collections**（三条 collections）。`user_settings()`、`collection_list()` 以及私有的 `collection_wallpapers()` 都**需要有效密钥，成功路径本轮未实测**（本轮无可用密钥，也未索要）；`user_collections()` 与公开收藏的 `collection_wallpapers()` 已用匿名请求实测，见各自小节。

### user_settings

给什么：`user_settings(**params)`。读取当前密钥持有者的账号设置。路由 `GET /api/v1/settings`，官方页面 **User Settings** 一节。官方原文 *Authenticated users can read their user settings via .../settings?apikey=<API KEY>*：这条路由没有查询参数，必须有有效密钥（配置里的，或本次用 `headers` 传 `X-API-Key`）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | `client.user_settings()`（配合已配置的密钥或本次 `headers`） |

返回 `{"data": {...}}`（**官方**示例字段，**未实测**）：

| 键 | 类型 | 含义 / 官方示例 |
| :--- | :--- | :--- |
| `thumb_size` | str | 缩略图尺寸偏好，`"orig"` |
| `per_page` | str | 每页条数偏好，`"24"`（字符串） |
| `purity` | str[] | 打开的分级，`["sfw", "sketchy", "nsfw"]` |
| `categories` | str[] | 打开的分类，`["general", "anime", "people"]` |
| `resolutions` | str[] | 分辨率偏好，`["1920x1080", "2560x1440"]` |
| `aspect_ratios` | str[] | 宽高比偏好，`["16x9"]` |
| `toplist_range` | str | 榜单默认范围，`"6M"` |
| `tag_blacklist` | str[] | 标签黑名单 |
| `user_blacklist` | str[] | 用户黑名单 |

**实测（匿名）**：`GET https://wallhaven.cc/api/v1/settings` → `401 application/json`，正文 `{"error": "Unauthorized"}`。

```python
from anybooru import Wallhaven

# sites.wallhaven.apikey 非空（或本次用 headers 传 X-API-Key）时才可能成功；本轮无凭据，未实测成功路径。
with Wallhaven('wallhaven') as client:
    settings = client.user_settings()
    # 真实 URL（官方）：GET https://wallhaven.cc/api/v1/settings?apikey=<API KEY>
    print(settings['data']['per_page'], settings['data']['purity'], settings['data']['categories'])
```

### collection_list

给什么：`collection_list(**params)`。列出**密钥持有者自己**的收藏夹（含私有）。路由 `GET /api/v1/collections`，官方页面 **User Collections** 一节。官方原文：*When authenticated, you are able to view all of your own collections.*

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | `client.collection_list()`（需要密钥） |

返回 `{"data": [...]}`，每项（**官方**示例字段，**未实测**）：

| 键 | 类型 | 含义 / 官方示例 |
| :--- | :--- | :--- |
| `id` | int | 收藏夹编号，`15` |
| `label` | str | 名称，`"Default"` |
| `views` | int | 浏览数，`38` |
| `public` | int | `1` 公开 / `0` 私有 |
| `count` | int | 内含壁纸数，`10` |

**实测（匿名）**：`GET https://wallhaven.cc/api/v1/collections` → **`404 application/json`，正文 `{"error": "Nothing here"}`**——注意这条是 **404 不是 401**（该路由按密钥归属取“自己的”收藏，匿名时没有对象可给）。带密钥的成功返回**未实测**。

```python
from anybooru import Wallhaven

# 需要有效密钥；本轮无凭据，成功路径未实测。
with Wallhaven('wallhaven') as client:
    collections = client.collection_list()
    # 真实 URL（官方）：GET https://wallhaven.cc/api/v1/collections?apikey=<API KEY>
    for c in collections['data']:
        print(c['id'], c['label'], c['public'], c['count'])
```

### user_collections

给什么：`user_collections(username, **params)`。列出**某个用户公开的**收藏夹。路由 `GET /api/v1/collections/{username}`，官方页面 **User Collections** 一节。官方原文：*Only collections that are public will be accessible to other users.*

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `username` | 字符串路径段，必填 | 站点用户名 | 必填 | `client.user_collections('ThorRagnarok')` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | 官方只给 `apikey` 一个可选查询值 |

返回 `{"data": [...]}`，每项字段与 `collection_list` 相同（`id` / `label` / `views` / `public` / `count`）。

**实测（匿名）**：

* `GET https://wallhaven.cc/api/v1/collections/ThorRagnarok` → `200 application/json`，`data` 3 项：`{"id": 274175, "label": "Default", "views": 37584, "public": 1, "count": 537}`、`{"id": 400286, "label": "SFW - Women", "views": 80396, "public": 1, "count": 1703}`、`{"id": 384565, "label": "ArtD", "views": 52695, "public": 1, "count": 1757}`。
* `GET https://wallhaven.cc/api/v1/collections/EstlinLuna` → `200`，`data` 10 项，`label` 可为 CJK（`"本命"`、`"イリヤ"`）。
* `GET https://wallhaven.cc/api/v1/collections/LewisMweir13`、`.../rootkit` → `200`，正文 `{"data": []}`：这两个账号没有公开收藏夹——**空数组是正常成功，不是错误**。

官方 7 条路径里没有用户资料路由；候选 `GET https://wallhaven.cc/api/v1/user/LewisMweir13` 实测 `404 {"error": "Not Found"}`。要看某人的上传，用搜索 `q='@<username>'`。

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    collections = client.user_collections('ThorRagnarok')
    # 真实 URL：GET https://wallhaven.cc/api/v1/collections/ThorRagnarok
    # 实测：200 application/json，data 3 项
    for c in collections['data']:
        print(c['id'], c['label'], c['public'], c['count'])
    # 274175 Default 1 537
    # 400286 SFW - Women 1 1703
    # 384565 ArtD 1 1757

    uploads = client.wallpaper_search(q='@LewisMweir13')
    # 真实 URL：GET https://wallhaven.cc/api/v1/search?q=%40LewisMweir13
    # 实测：200，meta.total=46,last_page=2（快照）
    print(uploads['meta']['total'])
```

### collection_wallpapers

给什么：`collection_wallpapers(username, collection_id, **params)`。列出一个收藏夹里的壁纸。路由 `GET /api/v1/collections/{username}/{collection_id}`，官方页面 **User Collections** 一节。官方原文：*The result will be a similar listing as the search results above. However only the 'purity' filter will be available. Authenticated users can access their own private collections by using their API key.*

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `username` | 字符串路径段，必填 | 收藏夹所属用户名 | 必填 | `client.collection_wallpapers('ThorRagnarok', 274175)` |
| `collection_id` | 数字路径段，必填 | 收藏夹编号，即列表项的 `id` | 必填 | 同上 |
| `purity` | 三位 0/1 字符串，顺序 sfw/sketchy/nsfw | 该路由**唯一**可用的搜索过滤；官方原文 *only the 'purity' filter will be available* | 未规定 | `client.collection_wallpapers('ThorRagnarok', 274175, purity='100')` |
| `page` | 页码，从 `1` 开始 | 第几页；分页与 `wallpaper_search` 一致 | 未规定（观察为第 1 页） | `client.collection_wallpapers('ThorRagnarok', 274175, page=2)` |
| `**params` | 其它名字原样进查询串（**客户端**） | — | — | — |

返回 `{"data": [...], "meta": {...}}`。`data` 是壁纸摘要，字段与 `wallpaper_search` 的 `data[]` 完全相同。**`meta` 只有 `current_page` / `last_page` / `per_page` / `total` 四个键，没有 `query` 和 `seed`**（实测），这是它与搜索 `meta` 的唯一区别——别照抄搜索的分页解析。非公开收藏夹对他人不可见；密钥持有者可读自己的私有收藏夹。

**实测（匿名）**：

* `GET https://wallhaven.cc/api/v1/collections/ThorRagnarok/274175` → `200 application/json`；`data` 24 项，首项 `po86ve`（`3840x2160`、`image/png`、`views=4580`、`favorites=63`）；`meta` `{"current_page": 1, "last_page": 23, "per_page": 24, "total": 537}`。
* `GET https://wallhaven.cc/api/v1/collections/ThorRagnarok/274175?purity=100&page=2` → `200`；`meta.current_page=2`，首项 `135v7g`。
* `GET https://wallhaven.cc/api/v1/collections/ThorRagnarok/0` → `404 {"error": "Nothing here"}`（编号不存在）。

私有的、以及密钥持有者本人的收藏夹需有效密钥，**未实测**。

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    wallpapers = client.collection_wallpapers('ThorRagnarok', 274175, purity='100', page=1)
    # 真实 URL：GET https://wallhaven.cc/api/v1/collections/ThorRagnarok/274175?purity=100&page=1
    # 实测：200 application/json，data 24 项
    print(client.last_call['url'], client.last_call['status_code'])
    print(wallpapers['meta'])  # {"current_page": 1, "last_page": 23, "per_page": 24, "total": 537}
    for w in wallpapers['data']:
        print(w['id'], w['resolution'], w['file_type'], w['path'])
```

## 状态码与错误体

以下状态与正文形状都是**实测**（匿名只读），除注明“官方”者：

| 状态 | 何时 | `Content-Type` | 正文 |
| :--- | :--- | :--- | :--- |
| `200` | 成功；列表接口也可能 `200` 但 `data=[]`（如 `purity='001'`、无公开收藏） | `application/json` | 正常信封 `{"data": ...}` 或 `{"data": [...], "meta": {...}}` |
| `400` | 页码越界，如 `page=1000000` | `application/json` | `{"error": "Bad Request"}` |
| `401` | `settings` 匿名或密钥无效；官方说访问 NSFW 壁纸而无效密钥也是 `401` | `application/json` | `{"error": "Unauthorized"}` |
| `403` | `q='like:<id>'` 本轮命中 Cloudflare 质询 | `text/html; charset=UTF-8` | HTML 质询页，带 `Cf-Mitigated: challenge` |
| `404` | 命中路由但资源不存在或匿名无权：`/w/000000`、`/w/94x38z`、`/tag/0`、`/collections/ThorRagnarok/0`、匿名 `/collections` | `application/json` | `{"error": "Nothing here"}` |
| `404` | 官方 7 条路径之外的候选路径：`/w/{id}/similar`、`/user`、`/user/{name}` | `application/json` | `{"error": "Not Found"}` |
| `429` | 官方：超过 45 次/分钟 | —（**未触发**） | 官方未给正文 |
| `500` | `page=0`（实测） | `text/html; charset=UTF-8` | HTML 错误页（标题 *It broke*），不是 JSON |

限流：官方页面原文 *API calls are currently limited to 45 per minute*，超限回 `429`。实测响应头带 `X-RateLimit-Limit: 45` 与 `X-RateLimit-Remaining`，但**没有触发过 429**，阈值未验证。客户端不内置限流：调用方自行控制节奏（包内示例每次调用前停顿）。

## 边界与未实测

* **带密钥的成功路径全部未实测**：`user_settings()`、`collection_list()`、私有/本人收藏夹（`collection_wallpapers()` 的私有收藏）、NSFW 分级（`purity` 含 `nsfw` 位）、以及 `X-API-Key` 请求头形式。本轮无凭据，也不向站点索要；本页不给假密钥。
* **`collection_wallpapers()` 只测过公开收藏夹**（`ThorRagnarok/274175`，含第 1、2 页）；私有收藏与本人收藏需密钥，未实测。
* **`q='like:<id>'`** 本轮只有 `403 text/html` 质询样本；官方文档把“相似壁纸”写成这条搜索语法，而不是独立路由，但不保证每次都能取到 JSON。
* **`429` 未触发**：`X-RateLimit-Limit: 45` 只是响应头读数，滚动窗口与超限正文未验证。客户端无节流。
* **`page` / `sorting` 的异常取值**：`page=1000000` 是 `400`，`page=0` 是 `500 HTML`，`page='abc'` 是 `200` 且 `current_page=1`；`sorting='not-a-sort'`、`categories='abc'` 都是 `200`（`sorting` 非法时 `data=[]` 却仍报 `total=501359,last_page=20890`）。**`data=[]` 不等于结果集已到末尾**；也**不要**把这些越界行为当成客户端会修正的东西——客户端原样透传。
* **`sorting='random'` 的种子**：官方页面承诺“把返回的 seed 传给下一页可保证不重复”，本轮样本里两页返回的 `meta.seed` 并不相同（`abc123` 第 1 页得 `wPpR1H`，第 2 页得 `vMFVjx`；把 `wPpR1H` 传回第 2 页又得 `Ec2tSv`）。**本轮样本无法保证跨页无重复**（不推广为站点普遍行为），客户端也**不会**改写或固定 seed。
* **`sorting='views'&order='asc'` 短页**：`meta.per_page=24`、`total=501359`，但只回 2 条。少于 24 条**不等于**已到末尾。
* **官方示例编号会失效**：官方 `#wallpapers` 与 `#search` 示例都用 `94x38z`，实测该编号已 `404`；当前可用样本是 `pom5lj`、`9mjoy1`。示例中的计数与编号只是快照。
* **没有 `per_page`**：官方页面写死每页 24 条，参数表里没有 `per_page`；客户端也不发明它。
* **`hot` 不是 API 排序值**：官方搜索表只列 `date_added` / `relevance` / `random` / `views` / `favorites` / `toplist`（站点搜索框另有 `hot` 选项，但 API 参数表未列，本页不把它当 API 取值）。
* **媒体**：`path`、`thumbs`、`avatar` 一律原样交付，客户端不下载、不拼接、不探测可用性。
* **服务端源码 / OpenAPI**：本轮没有取得 Wallhaven 的服务端源码或 OpenAPI 规范，本页所有路径、参数、字段都以官方 API 页面与匿名响应为准，不编造源文件行号。

---

继续阅读：[客户端用法](wallhaven.md) · [能力入口](wallhaven-capabilities.md) · [契约审计附注](wallhaven-contract-notes.md) · [验证记录](verification.md#wallhaven匿名只读实测2026-10-03)
