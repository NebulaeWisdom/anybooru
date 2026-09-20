# nhentai 客户端用法

`Nhentai` 访问 nhentai（`https://nhentai.net`）的 JSON API v2。站点发布 OpenAPI 3.1.0 规范（`https://nhentai.net/api/v2/openapi.json`）与 changelog。它是**独立家族**，不是 Danbooru / Moebooru / Gelbooru 模板站点：路由在 `api/v2/...`，列表项与详情是两套字段，分页是 `page` + `per_page`，标签是带 `type` 与 `count` 的对象，需凭据的路由用 `Authorization: Key <key>` 而不是 Basic / Bearer。

客户端一共 **36 个原生方法**：**31 个 `GET` + 4 个 `POST` + 1 个 `DELETE`**，其中 **32 个只读**（31 个 `GET` 加只读的 `POST api/v2/tags/search`，即 `tag_search()`），**4 个写方法**是 `favorite_add()`、`favorite_remove()`、`blacklist_update()` 与 `gallery_download()`（只申请整卷下载地址，**不下载文件**）；**10 个方法需要凭据**（`gallery_favorite` / `favorite_list` / `favorite_random` / `blacklist_list` / `blacklist_ids` / `user_me` 六个 `GET`，加 4 个写方法）。

**每个方法的完整参数、路由与逐字段返回在[方法参考](nhentai-api.md)**，「我要做什么 → 用哪个方法」与 36 方法完整索引见[能力入口](nhentai-capabilities.md)；本页只讲**这个类怎么用**：构造、认证、`request()` 与参数编码、返回值与 `last_call`、错误、几个能直接抄的调用、脚本入口、边界。本轮的匿名只读请求与响应摘要见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)：31 条选中的 `GET` 路由全部有直接 HTTP 证据（25 个 `200`、6 个需要凭据的 `401`），随仓库的冒烟与两个示例也真的跑过（10 次请求 10 PASS、3 次与 5 次 `200`，退出码全 `0`，共 9 个 Python 原生方法）；**4 个写方法与 `tag_search()` 一个都没发**，带 Key 的请求一次都没发过。没有样本的部分集中在[边界与未实测](#边界与未实测)。**本库不下载任何媒体**：`cover` / `thumbnail` / `pages[].path` 都只是路径字符串，`gallery_download()` 返回的也只是 `{url, expires_at}`。

## 为什么单独一个家族，而且只做 `.net`

判据是**契约**而不是站名：路由形状、参数名、列表与详情两套字段、`page` + `per_page` 的分页、标签对象、`Authorization: Key` 的鉴权方式，整体不符合现有十一个家族的契约，所以需要独立客户端。按哪条 JSON Pointer、排除了哪些操作（第一方与内部路由、`User Token` 专属写操作、PoW/CAPTCHA、广告位、管理类写操作），见[契约附注](nhentai-contract-notes.md)。

“nhentai”下面是两个互不相干的站点，本库只做其中一个：

| | `nhentai.net`（本库目标） | `nhentai.to`（**排除**） |
| :--- | :--- | :--- |
| 接口 | 官方 JSON API v2 + OpenAPI 规范 | 服务端渲染 HTML；详情页内嵌 `var gallery = new N.gallery({…})`，**该段不是合法 JSON**（数字后带尾逗号） |
| `/api/**` | 本库只接入 v2 资源；旧路径样本 `/api/gallery/658856` 为 `403 text/plain`，指向 v2 文档 | 已测 7 条 API 路径为 `404`，但 `/trending-searches` 为 `200` JSON 数组；不推断完整路由表 |
| 作品 id | 就是 API 的 `id` | **与 `.net` 不通用**（同一段 `658856` 在两站是不同作品） |
| 标签 id | `tags[].id` | `.to` 本地 `id` 不能直接互换；样本 `nh_id="2937"` 对应 `.net` 标签 2937，另有语义未明的负值 |

因此本库不解析 clone HTML、不转换 id，也不把 `.to` 加作同一家族的站点。

## 依据与主机

- `GET https://nhentai.net/api/v2/openapi.json`：OpenAPI 3.1.0，`info.version` = `2.0.0+14bccf7`，98 path / 114 operation / 129 schema。36 个方法都能按 JSON Pointer 查到，例如列表是 `#/paths/~1api~1v2~1galleries/get`（`get_all_galleries_api_v2_galleries_get`）、列表项是 `#/components/schemas/GalleryListItem`。
- `/api/v2/changelog`、`/api/v2/config`、`/api/v2/cdn` 是运行时事实来源。v2 上线后已有多处 Breaking 变更，**别把版本号当冻结契约**。
- 包内 `sites.nhentai` 的 `url` 是站点根 `https://nhentai.net`，36 个方法都接在它后面，原生路径形如 `api/v2/galleries/658856`。`service_info()` 走站点根下的 `api/v2` 本身（**没有尾斜杠**）。
- `i1`–`i4` / `t1`–`t4.nhentai.net`（原图与缩略图服务器）本轮**一个都没请求过**。
- 网页 HTML、`/api/*` 旧路由与 `nhentai.to` 都不包装、不抓取、不回退。
- 规范里的 `security` 字段**不能单独用来判断“是否公开”**：多数只读路由被列成需要 User Token/API Key，而同一条操作的描述文字写的是 `**Auth:** Public (optional User Token or API Key for personalization)`，匿名实测也是 `200`。本库按描述文字把这些路由当公开只读，不替你做权限判断。

## 构造与配置

签名：`Nhentai(site_name=None, site_url=None, api_key=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 段里的键名 | 不选命名站点，需显式给 `site_url` | `Nhentai('nhentai')` |
| `site_url` | 字符串，站点基地址；本类必须是**站点根** | 读取所选站点的 `url`（包内是 `https://nhentai.net`） | `Nhentai(site_url='https://nhentai.net')` |
| `api_key` | 字符串，**非空**才按 `Authorization: Key <api_key>` 发送 | `None` 且有站点名就读站点条目的 `api_key`（包内为空串）；显式 `''` 表示明确匿名 | `Nhentai('nhentai', api_key='…')` |
| `proxies` | 字典，按 `http` / `https` 指定代理，`{}` 表示直连 | 使用 `request.proxies`；**不读环境变量** | `Nhentai('nhentai', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json` | `Nhentai('nhentai', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout` | `Nhentai('nhentai', timeout=10)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent` | `Nhentai('nhentai', user_agent='MyApp/1.0 (https://example.org)')` |

**构造不发任何请求**，也不校验 key；用完记得 `client.close()`，或用 `with` 语句块。包内站点条目只有两个字段：`{"nhentai": {"url": "https://nhentai.net", "api_key": ""}}`。复制完整配置、加自己的 key 见[配置指南](configuration.md)。规范的 `info.description` 要求带**描述性的 `User-Agent`**（`AppName/version (contact or project URL)`）；本库原样发送你给的值，不代填、不校验。

## 认证：`api_key` 的三种语义

规范在 `#/components/securitySchemes` 里定义两套头，都放 `Authorization`：`API Key`（`Key <key>`，第三方客户端用）与 `User Token`（`User <token>`，站点自家会话）。本库没有 User Token 构造参数或登录方法；通用 `request(headers=...)` 仍可显式传入任意认证头。

- `api_key=None`：有 `site_name` 就取配置里的 `api_key`（包内空串 = 匿名）。
- `api_key=''`：**显式匿名**，即使配置里填了 key 也不发送任何鉴权头。
- `api_key='<非空>'`：每次请求带 `Authorization: Key <api_key>`，原样发送（`Key ` 前缀由客户端补）。

公开读取不需要 key；单次调用可以覆盖——`request(..., headers={...})` 里同名头优先于实例凭据，例如 `client.request('GET', 'api/v2/user', headers={'Authorization': 'Key <另一把 key>'})` 临时换一把 key。**Key 的成功路径本轮没有样本**（所有请求都是匿名的），只有规范依据。

## 通用入口 `request()`

签名：`request(method, path, *, params=None, data=None, headers=None)`。原生方法只是把参数拼好再调它，`path` **去掉前导 `/` 后拼在站点根后面**：

| `path` 写法 | 实际请求的地址 |
| :--- | :--- |
| `'api/v2/galleries'` | `https://nhentai.net/api/v2/galleries`（原生方法的写法） |
| `'/api/v2/galleries'` | 同上：前导 `/` 被去掉，两种写法等价 |
| `'api/v2/galleries/658856'` | `https://nhentai.net/api/v2/galleries/658856`（路径段不自动编码，编号自己拼） |
| `'api/v2'` | `https://nhentai.net/api/v2`（`service_info()` 走它，没有尾斜杠） |

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词，例如 `'GET'` / `'POST'` / `'DELETE'` | 必填 | `client.request('GET', 'api/v2/galleries', params={'page': 1})` |
| `path` | 上表的写法 | 必填 | `client.request('GET', 'api/v2/galleries/658856')` |
| `params` | 查询参数字典，按下面的规则编码 | `None`，不发查询参数 | `client.request('GET', 'api/v2/galleries', params={'page': 1, 'per_page': 2})` |
| `data` | JSON 请求体；字典内显式 `None` 编码为 `null`，空数组保留 | 顶层 `None` 不带正文 | `client.request('POST', 'api/v2/tags/search', data={'query': 'engli', 'type': 'language'})`（未执行） |
| `headers` | 额外请求头，只作用于本次；**同名时覆盖实例的凭据头** | `None`，不附加 | `client.request('GET', 'api/v2/user', headers={'Authorization': 'Key <key>'})` |

**查询参数编码**用本库共享编码，规则三条：

| 你传的值 | 发出去的样子 | 例子 |
| :--- | :--- | :--- |
| `None` | 整个键**丢弃**（`data` 里的 `None` 不丢） | `params={'page': 1, 'q': None}` → 只发 `page=1` |
| 布尔 | 小写 `true` / `false` | `params={'blacklisted': True}` → `blacklisted=true` |
| 列表 / 元组 / 嵌套字典 | 键带方括号：`key[]=值`（重复）、`key[子键]=值` | `params={'ids': ['12227', '6346']}` → `ids%5B%5D=12227&ids%5B%5D=6346` |

所以**逗号串要写成字符串**（`tag_ids('12227,6346')`），传数组会变成站点不认识的 `ids[]=…`；`data` 不受这套编码影响，是纯 JSON。客户端不补前缀、不补尾斜杠、不拆信封、不改字段名、不重试、不钳位参数，也不做本地校验。

## 返回值、`last_call` 与错误

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | 解析后的对象，**一层都不拆**：分页是 `{"result", "num_pages", "per_page", "total"}`；`tags/ids`、`tags/search`、`galleries/popular`、`blacklist/ids` 是**裸数组**；`tags/{type}/{slug}` 是**裸对象**；`comments/count` 是**裸整数**；`galleries/random` 与 `favorites/random` 是规范未固定字段的对象 |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`（原始文本）、`data`（能解析成 JSON 时是解析结果，否则 `None`） |
| 2xx 但正文为空 | 返回 `None` |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError` |
| 网络错误 | requests 自己的异常原样抛出，没有重试与退避 |

`client.last_call` 是最近一次请求的 `API`（路由路径）、`url`（含查询串）、`status_code`、`status`、`headers`；**它在每次请求前清空**，所以失败时记录的就是那次失败请求。例如 `client.gallery_list(page=1, per_page=2)` 之后，`client.last_call['status_code']` 是 `200`，`client.last_call['url']` 是含查询串的真实地址。

站点错误是 `{"error": "…"}` 的 JSON（`ErrorResponse`）：越界参数实测 `400` `{"error": "Validation error", "details": ["query -> page: Input should be greater than or equal to 1"]}`，不存在画廊实测 `404` `{"error": "Gallery not found"}`，缺凭据实测 `401` `{"error": "Authentication required"}`。**规范给参数校验声明的是 `422`（`{"detail": […]}`），站点实际回 `400`**——本库不归一化，谁先来就抛谁，按 `error.http_code` 分支时以线上实测为准。分页参数与配额（`429` 等）的完整说明见[分页](pagination.md)与[错误处理](errors.md)；规范给每条路由写了每分钟配额，但**本轮没有触发过 `429`**。

## 常用调用：四段能直接抄的代码

列表与翻页（`page` **从 1 起**）：

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    first = client.gallery_list(page=1, per_page=2)
    # GET https://nhentai.net/api/v2/galleries?page=1&per_page=2
    # 200 {"result": [列表项, …], "num_pages": …, "per_page": 2, "total": …}
    print(len(first['result']), first['per_page'], first['num_pages'], first['total'])
    item = first['result'][0]
    print(item['id'], item['media_id'], item['num_pages'], item['num_favorites'])
    print(item['thumbnail'], item['tag_ids'][:5])

    second = client.gallery_list(page=2, per_page=2)
    # GET https://nhentai.net/api/v2/galleries?page=2&per_page=2 → 自己把 page 加一
    print([entry['id'] for entry in second['result']])
```

列表项字段：`id`（画廊编号，也是路径里那一段）、`media_id`（**字符串**，拼图片地址用）、`english_title` / `japanese_title`（标题文本，示例不打印）、`thumbnail`（路径）与 `thumbnail_width` / `thumbnail_height`、`num_pages`（页数，**不是**页码）、`num_favorites`、`tag_ids`（标签 id 数组）、`blacklisted`。`total` 允许为 `null`，且 **`num_pages` 不等于 `ceil(total / per_page)`**（匿名样本 646010 / 2 → 323037）；两个都是快照数字，别互相反推。

详情（唯一给出每页尺寸与全部标签的读取）：

```python
from anybooru import AnybooruHTTPError, Nhentai

with Nhentai('nhentai') as client:
    detail = client.gallery_show(658856, include='comments,related')
    # GET https://nhentai.net/api/v2/galleries/658856?include=comments%2Crelated
    print(detail['id'], detail['media_id'], detail['num_pages'], detail['num_favorites'])
    print(list(detail['title'].keys()), detail['cover']['path'], detail['scanlator'])
    tag = detail['tags'][0]
    print(tag['id'], tag['type'], tag['slug'], tag['count'])
    print(len(detail['pages']), detail['pages'][0]['number'], detail['pages'][0]['path'])
    print(detail['comment_count'], len(detail['related']))    # include 带出来的两个键

    try:
        client.gallery_show(999999999)                        # 预期错误路径
    except AnybooruHTTPError as error:
        print(error.http_code, error.data)                    # 404 {'error': 'Gallery not found'}
```

详情字段：`title` 是 `{english, japanese, pretty}` 对象；`cover` / `thumbnail` 是 `{path, width, height}`；`pages` 是每页 `{number, path, width, height, thumbnail, …}` 的数组；`tags` 是 TagResponse 对象数组（`id` / `type` / `slug` / `name` / `url` / `count` / 可空的 `description` / `is_community` / `pending_describe_id`；**列表项里的标签没有最后两个键**）；另有 `scanlator`、`upload_date`（整数，单位规范未写）。`include` 是逗号串（`comments` / `related` / `favorite` / `suggestions`）：匿名请求**不会**多出 `is_favorited`；`include=comments` 只带评论预览，完整分页用 `gallery_comments()`。`gallery_related(658856)` 是不带 `include` 的独立入口，返回 `{"result": [列表项, …]}`，**没有分页字段**。

搜索（`query` 必填，既可位置传入也可关键字传入；规范的可选查询参数是 `sort` 与 `page`，不含 `per_page`）：

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    found = client.search(query='language:english', sort='popular', page=1)
    # GET https://nhentai.net/api/v2/search?query=language%3Aenglish&sort=popular&page=1
    print(found['total'], found['num_pages'], len(found['result']))
    print([item['id'] for item in found['result']])
```

规范支持的查询写法：`word`、`"exact phrase"`、`-word` / `-artist:name`、`artist:name` / `language:english` / `tag:"big breasts"`、`pages:>10` / `favorites:>=100`、`uploaded:<7d` / `uploaded:>1m`。`sort` ∈ `date` / `popular` / `popular-today` / `popular-week` / `popular-month`，缺省 `date`；不带 `query` 或传非法 `sort` 是 `400`，搜不到东西是 `200` 加空 `result`。冒号与引号由 requests 编码，但**整串不要拼成数组或逗号串**——它就是站点自己的查询语言。

标签（四个入口）：

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:
    labels = client.tag_list('language', sort='name', page=1)
    # GET https://nhentai.net/api/v2/tags/language?sort=name&page=1
    # {"result": [TagResponse, …], "num_pages": …, "per_page": …, "total": …, "alphabet": …}
    print(labels['total'], labels['per_page'], len(labels['result']))
    print(list(labels['alphabet']) if labels.get('alphabet') else 'no alphabet')

    one = client.tag_show('language', 'english')
    # GET https://nhentai.net/api/v2/tags/language/english → **裸 TagResponse 对象**
    print(one['id'], one['type'], one['slug'], one['count'])

    batch = client.tag_ids('12227,6346')
    # GET https://nhentai.net/api/v2/tags/ids?ids=12227%2C6346 → **裸数组**（ids 是逗号串，最多 100 个）
    print([tag['slug'] for tag in batch])
```

`tag_list()` 的 `tag_type` 只有七个值：`artist` / `category` / `character` / `group` / `language` / `parody` / `tag`，非法值 `400`；`sort` ∈ `name` / `popular`；**`alphabet` 只在 `sort=name` 时出现**。`tag_show()` 与 `tag_search()` 返回裸对象 / 裸数组，没有 `result` 信封——**`tag_list()` 才有**。

## 常见工作流

| 我要做什么 | 调用 | 关键返回 |
| :--- | :--- | :--- |
| 看最新画廊 | `client.gallery_list(page=1, per_page=2)` | `result[]`（列表项）、`per_page`、`num_pages`、`total`（可为 `null`） |
| 翻下一页 | `client.gallery_list(page=2, per_page=2)` | 自己把 `page` 加一；客户端不翻页、不合并 |
| 关键词 / 条件搜索 | `client.search(query='language:english', sort='date', page=1)` | `result[]`、`total`、`num_pages`；`per_page` 不是这个路由的参数 |
| 取一张画廊的详情 | `client.gallery_show(658856, include='comments,related')` | `title` / `cover` / `tags[]` / `pages[]` / `num_pages` / `num_favorites`（+`comments`、`comment_count`、`related`） |
| 看标签 | `client.tag_show('language', 'english')` / `client.tag_list('language', sort='name')` / `client.tag_ids('12227,6346')` | **裸 TagResponse** / 分页信封（`sort=name` 才有 `alphabet`）/ **裸数组** |
| 读评论 | `client.gallery_comments(658856, page=1, per_page=2)`；只要数量用 `client.gallery_comment_count(658856)` | 评论分页信封（`result[]` 含 `poster` / `post_date` / `body`）/ **裸整数** |
| 预期错误路径 | `client.gallery_show(999999999)` → `404`；`client.gallery_list(page=0, per_page=2)` → 站点实测 `400`（规范写 `422`） | 都抛 `AnybooruHTTPError`，读 `error.http_code` / `error.data` |

翻页最常踩两条：**页码从 1 起**，且**每页条数不都听你的**——`tags/{tag_type}` 要 1 回 120、`taxonomy/resolved` 要 2 回 50、`search` 的 `per_page` 被忽略、`galleries` 的 `per_page` 上限 100，越界回 `400`；**“到末页了”没有可靠算法**——越界页码不报错而是返回重复的尾部（`page=100000` 是 `200`），别用“条数变少 / 空数组 / `total` ÷ `per_page`”判末尾。完整分页语义见[分页](pagination.md)。

## 媒体地址与整卷下载

`cover` / `thumbnail` / `pages[].path` / `pages[].thumbnail` 都是**路径字符串**。完整地址 = 运行时服务器前缀 + `/` + 路径。服务器列表用 `site_config()`（`config`）或 `cdn_config()`（`cdn`，少一个 `announcement`）取，例如 `client.site_config()['image_servers'][0] + '/' + detail['pages'][0]['path']`。**别写死子域、别自己改扩展名**；本库只把地址字符串给你，取字节用你自己的下载代码。整卷下载走 `gallery_download(658856, format='cbz')`，需 Key，返回 `{"url", "expires_at"}`，要在 `expires_at` 前取用；**不要在 CDN 上逐页拼整卷**。本轮没有请求过任何媒体主机。

## 可运行示例

两个示例都匿名只读（显式 `api_key=''`、不跟随跳转、不重试、按配置的 `pause_seconds` 停顿），参数取自配置的 `examples.nhentai` 段，脚本里没有硬编码站点或查询值。`list_galleries.py` 用 `list_query`（`{"per_page": 2}`）走两页 `gallery_list()`，再用 `search_query` 走一次 `search()`，共 3 次 `GET`。`browse_resources.py` 走 `gallery_show(658856)` → `tag_show('language', 'english')` → `tag_ids('12227,6346')` → `gallery_comments(658856, page=1, per_page=2)` → `site_config()`，共 5 次 `GET`；只打印结构信息，不打印标题、评论正文与标签说明，也不访问媒体地址。

```bash
python examples/nhentai/list_galleries.py
python examples/nhentai/browse_resources.py
python test/nhentai.py
```

以上默认读包内配置；需要自备网络设置时加 `--config my-anybooru.json`。标签补全的 POST 调用形态见方法参考，不混入上面的匿名 GET 教学片段。

轻量冒烟 `test/nhentai.py` 匿名、只读、最多 10 次请求、不 mock、不进 CI，参数取自 `smoke.nhentai`；每行输出 `PASS/FAIL`，末尾输出 `SUMMARY`，有失败退出 `1`。它覆盖两页列表、详情、搜索、热门、标签详情、评论数与评论页、缺失画廊（预期 `404`）与越界列表参数两条错误路径，**不含任何写方法**。

本轮这三个脚本都真的跑过：`test/nhentai.py` **10 次请求 10 PASS、0 FAIL、退出 0**（8 个 `200` 加两条预期错误路径）；`list_galleries.py` **3 次 `200`、退出 0**；`browse_resources.py` **5 次 `200`、退出 0**；stderr 为空；合计 **9 个 Python 原生方法**实际执行。逐条命令、URL、状态码与退出码见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)，本页不复述整张逐请求表。**注意两层证据的口径**：“实测”除了这些 Python 调用，还包括对 31 条 `GET` 路由的**直接 HTTP** 观察——脚本只覆盖其中 9 个方法，不等于 36 个方法逐一跑过。

## 边界与未实测

- **写方法与只读 `POST` 都没发过**：`favorite_add()`、`favorite_remove()`、`blacklist_update()`、`gallery_download()`、`tag_search()` 的成功、`401`、`503` 形态都没有样本，只有规范依据。
- **带 Key 的成功路径没有样本**：本轮全部匿名；`Authorization: Key …` 被接受时返回什么、错误 key 回什么、`user_me()` 的 `email` 是否一定为 `null`，都未实测。本库没有 User Token 登录/构造参数，通用头覆盖也未实测。
- **功能开关与限流未实测**：`allow_gts` / `allow_taxonomy` / `allow_favorites` / `allow_downloads` 关闭时的 `503` 未实测；规范写了每条路由的每分钟配额，输入资料提到 `429` 与极端页码 `503`，本轮既没触发也没验证。
- **媒体字节零请求**：服务器列表和媒体相对路径已有 JSON 样本，但没有验证这些地址的可下载性、Referer 或 Range。公告本轮为 `null`，非空形态未实测。
- **空样本与没穷尽的枚举**：本轮选中的画廊评论为空、提案编辑史为空，所以 `CommentResponse` 元素字段与编辑史元素只有规范依据；`include` 的全部取值与非法值行为、`taxonomy` 的 `tier` / `status` / `action`、`gts_backlog` 的 `sort_by`、`tag_search` 的属性组合、各单位每页条数的真实上限，都只有规范或单次样本。
- **规范与站点会不一致**：参数越界规范写 `422`、站点实测回 `400`；`num_pages` 与 `total` / `per_page` 也对不上。本库原样透出，不归一化、不修补。数据与规范都在变：`total`、`num_pages`、`num_favorites`、标签 `count` 都是快照，v2 已有多次 Breaking 变更，本页对应 `2.0.0+14bccf7`。
- **`.to` 的结论来自有限样本**：7 条 `/api/**` 的 `404` 不能证明所有路由不存在，`GET` 不能证明 `POST` 路由不可用；作品 id 不通用、标签 id 只有部分对得上，所以本库不做映射与兜底。

继续阅读：[方法参考](nhentai-api.md) · [能力入口](nhentai-capabilities.md) · [依据与排除](nhentai-contract-notes.md) · [验证记录](verification.md#nhentai匿名只读实测2026-09-20)。
