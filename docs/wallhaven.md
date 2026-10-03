# Wallhaven 客户端用法

`Wallhaven` 访问 wallhaven.cc 的 **API v1**。站点根是 `https://wallhaven.cc`，所有路由都在 `api/v1/` 下。它不是任何一套已有 booru 引擎的站点：列表接口返回 `{"data": [...], "meta": {...}}`（列表在 `data` 里、分页在 `meta` 里）、详情接口返回 `{"data": {...}}`（壁纸对象在 `data` 里）、账号 key 走 `apikey` 查询值、每页固定 24 条，所以是**独立家族**。

本类一共 **7 个原生方法，全部是只读 `GET`**，且都能匿名读公开数据；需要账号 key 的只有 `user_settings()`、`collection_list()` 和读取私有集合时的 `collection_wallpapers()`。没有登录方法、没有写请求、不下载图片：`path` / `thumbs` / `avatar` 里的地址原样给你，是否取字节由你自己决定。

**每个方法的完整参数、路由与逐字段返回在[方法参考](wallhaven-api.md)**；「我要做什么 → 用哪个方法」与 7 方法一行索引见[能力入口](wallhaven-capabilities.md)；依据、排除项与文档矛盾见[契约附注](wallhaven-contract-notes.md)。本页只讲**这个类怎么用**：构造、认证、`request()` 与参数编码、返回值与 `last_call`、错误、能直接抄的调用、脚本入口、边界。

## 依据

- 官方页面 `GET https://wallhaven.cc/help/api` 本轮实测 `200 text/html; charset=UTF-8`，标题 `API v1 - wallhaven.cc`。页面内锚点：`#wallpapers`（壁纸详情）、`#search`（搜索与列表）、`#tags`（标签）、`#user-settings`（用户设置；**“User Collections”一节复用了同一个 `#user-settings` 锚点**）、`#limits`（限流与错误）、`#auth`（认证）。本页按这些锚点引用原文。
- 站点侧事实来自本轮**匿名只读**直接 HTTP 请求：公开路由、列表与详情、标签、搜索的 12 个参数、集合列表与集合里的壁纸、分页与错误路径。逐条 URL、状态码、`Content-Type` 与响应摘要见[验证记录](verification.md#wallhaven匿名只读实测2026-10-03)。
- 本轮**没有** OpenAPI、没有服务端源码快照，也不引用源码行号：结论要么被官方页面覆盖，要么被匿名响应覆盖，两者都没有的一律写「未实测」。

## 三行上手

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    found = client.wallpaper_search(q='nature')
    print(found['meta']['total'], found['meta']['last_page'], len(found['data']))
    print(found['data'][0]['id'], found['data'][0]['resolution'], found['data'][0]['path'])
    print(client.last_call['status_code'], client.last_call['url'])
```

真实请求 `GET https://wallhaven.cc/api/v1/search?q=nature`（`page` 不传时服务端按第 1 页处理），本轮 `200`：`meta` 是 `{"current_page": 1, "last_page": 3058, "per_page": 24, "total": 73383, "query": "nature", "seed": null}`，`data` 是 24 条壁纸摘要。这些数字是当时的快照，不是固定值，也不是客户端常量。

## 构造与配置

```python
Wallhaven(site_name=None, site_url=None, apikey=None, proxies=None, *,
          config_file=None, timeout=None, user_agent=None)
```

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 段里的键名 | 不选命名站点，需显式给 `site_url` | `Wallhaven('wallhaven')` |
| `site_url` | 字符串，站点基地址；本类必须是**站点根**，不是 `api/v1` | 读取所选站点的 `url`（包内是 `https://wallhaven.cc`） | `Wallhaven(site_url='https://wallhaven.cc')` |
| `apikey` | 字符串，账号 API key；三种语义见[认证](#认证apikey-与-x-api-key) | `None` 且有站点名就读 `sites.<站点名>.apikey`（包内为空串） | `Wallhaven('wallhaven', apikey='')` |
| `proxies` | 字典，按 `http` / `https` 指定代理；`{}` 表示直连 | 使用 `request.proxies`；**不读环境变量** | `Wallhaven('wallhaven', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json` | `Wallhaven('wallhaven', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout` | `Wallhaven('wallhaven', timeout=30)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent` | `Wallhaven('wallhaven', user_agent='MyWallClient/1.0')` |

包内站点条目：

```json
{"wallhaven": {"url": "https://wallhaven.cc", "apikey": ""}}
```

**构造不发任何请求**，也不校验 key，所以没有 key 也能构造出可用客户端。用完 `client.close()`，或用 `with` 语句块自动释放会话。换一份自己的完整配置、往 `sites.wallhaven.apikey` 填 key 的写法见[配置指南](configuration.md)。

## 认证：apikey 与 X-API-Key

官方页面 `#auth` 写两种等价的传法：查询串 `?apikey=<API KEY>`，或请求头 `X-API-Key: <API KEY>`；`#limits` 补一句：没有 key 或 key 无效时请求 NSFW 壁纸、以及其它任何使用无效 key 的请求，都会得到 `401 Unauthorized`。官方页面开头写 key 由账号设置提供、可随时重置。

本类的固定做法：

- **配置的 key 只发查询值**：`apikey` 非空时，每次请求都把它合并成查询参数 `apikey=<key>`。
- **`X-API-Key` 头不会自动发**：要发就在这次调用的 `headers` 里显式给（见下面字面写法）。本类不会在同一次请求里自动同时发查询值和头；你显式两个都给，两个才会都出现。
- 三种语义：`apikey=None` → 有 `site_name` 就读 `sites.<站点名>.apikey`；`apikey=''` → **显式匿名**，即使配置里有 key 也不发查询值；`apikey='<非空>'` → 每次请求带 `apikey=<key>`。
- 单次调用可以覆盖：合并顺序是「先配置的 key，再本次 `params`」，所以 `params` 里的 `apikey` 一定赢。注意 `params={'apikey': ''}` 会发出**空值** `apikey=`（键还在，只是值为空），不是把键省掉；要让整整一次请求连键都不出现，用构造时 `apikey=''` 或构造实例上不配 key。

key 从哪来：在你的账号设置里生成。官方页面开头写 key 由账号设置提供、可随时重置。**不要把 key 写死在脚本里或提交进仓库**。下面的片段都只演示「怎么把你自己的 key 交给客户端」，本轮**一次都没有执行**（本节没有账号 key）。

复制包内配置成自己的文件、把 key 填进 `sites.wallhaven.apikey`，代码不用改就能读到：

```json
{"wallhaven": {"url": "https://wallhaven.cc", "apikey": "<你账号设置里生成的 API key>"}}
```

用显式构造参数时，key 由你现场提供（例如从输入读），片段本身不含任何真 key：

```python
from anybooru import Wallhaven

apikey = input('Wallhaven API key: ')      # 你自己的 key；不要写进源码或提交
with Wallhaven('wallhaven', apikey=apikey) as client:
    settings = client.user_settings()
    print(settings['data']['per_page'], settings['data']['purity'])
```

走请求头形式时，构造保持匿名，只给这一次调用加 `X-API-Key`：

```python
from anybooru import Wallhaven

apikey = input('Wallhaven API key: ')
with Wallhaven('wallhaven', apikey='') as client:      # 不自动带查询值 key
    settings = client.request('GET', 'api/v1/settings',
                              headers={'X-API-Key': apikey})
    print(settings['data']['thumb_size'])
```

实例上配了 key、只想让某一次调用匿名，就在那次 `params` 里给空串：

```python
with Wallhaven('wallhaven') as client:                  # 配置里若有 key
    public = client.wallpaper_search(q='nature', apikey='')   # 这一次不带配置里的 key，只发空值 apikey=
```

**匿名能得到什么、得不到什么**：公开壁纸、标签、公开集合都能匿名读。匿名 `GET api/v1/search?purity=001`（只要 NSFW 位）本轮是 `200` 且 `total: 0`——客户端**不会**替你补纯度位，也不会把 `001` 改写成 `100`，拿不到 NSFW 就是拿不到。匿名读 `GET api/v1/settings` 本轮实测 `401 {"error": "Unauthorized"}`；带 key 的成功响应本轮没有样本。

## 通用入口 `request()`

```python
request(method, path, *, params=None, headers=None)
```

原生方法只是把参数拼好再调它。`path` **去掉前导 `/` 后拼在站点根后面**：

| `path` 写法 | 实际请求的地址 |
| :--- | :--- |
| `'api/v1/search'` | `https://wallhaven.cc/api/v1/search`（原生方法的写法） |
| `'/api/v1/search'` | 同上：前导 `/` 被去掉，两种写法等价 |
| `'api/v1/w/pom5lj'` | `https://wallhaven.cc/api/v1/w/pom5lj`（路径段由原生方法逐段编码） |
| `'api/v1/collections/LewisMweir13'` | `https://wallhaven.cc/api/v1/collections/LewisMweir13` |

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词，例如 `'GET'` | 必填 | `client.request('GET', 'api/v1/search', params={'q': 'nature'})` |
| `path` | 上表的写法 | 必填 | `client.request('GET', 'api/v1/w/pom5lj')` |
| `params` | 查询参数字典，按下面的编码规则发送 | `None`，不发查询参数 | `client.request('GET', 'api/v1/search', params={'q': 'nature', 'page': 2})` |
| `headers` | 额外请求头，只作用于本次；`X-API-Key` 就走这里 | `None`，不附加 | `client.request('GET', 'api/v1/settings', headers={'X-API-Key': apikey})` |

**API v1 的 7 条原生路由全是 `GET`，所以这个入口没有 `data` / `form` 正文参数**，本类也没有发明写方法；要发正文得自己用共享传输，但那已经超出 API v1 的范围。

**查询参数编码**用本库共享编码，规则三条：

| 你传的值 | 发出去的样子 | 例子 |
| :--- | :--- | :--- |
| `None` | 整个键**丢弃** | `params={'page': 1, 'q': None}` → 只发 `page=1` |
| 布尔 | 小写 `true` / `false` | `params={'seed': True}` → `seed=true` |
| 列表 / 元组 / 嵌套字典 | 键带方括号：`key[]=值`（重复）、`key[子键]=值` | `params={'resolutions': ['1920x1080']}` → `resolutions%5B%5D=1920x1080` |

所以 `resolutions` / `ratios` / `colors` 这类**要逗号串的键必须写成字符串**（`resolutions='1920x1080,1920x1200'`）；传 Python 列表会变成站点不认识的 `resolutions[]=…`。客户端不补前缀、不补尾斜杠、不拆外层、不改字段名、不重试、不钳位页码或取值，也不做本地校验。

## 返回值、`last_call` 与错误

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | 解析后的对象，**一层都不拆**：`search` 与集合里的壁纸都是 `{"data": [...], "meta": {...}}`（但两者的 `meta` 键不同，见下）；壁纸详情、标签详情、设置是 `{"data": {...}}`；集合列表是 `{"data": [...]}`（**没有 `meta`**） |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`（原始文本）、`data`（能解析成 JSON 时是解析结果，否则 `None`）、`response` |
| 2xx 但正文为空 | 返回 `None` |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError` |
| 网络错误 | requests 自己的异常原样抛出，没有重试与退避 |

搜索的 `meta` 有 `current_page` / `last_page` / `per_page` / `total` / `query` / `seed` 六个键；集合里的壁纸 `meta` 只有 `current_page` / `last_page` / `per_page` / `total` 四个键——**两者的 `meta` 不一样**，别按搜索的 `meta` 去读集合列表。

`client.last_call` 是最近一次请求的 `API`（去掉前导 `/` 的路由）、`url`（含查询串的真实地址）、`status_code`、`status`（原因文本）、`headers`；**它在每次请求前清空**，所以失败时记录的就是那次失败请求，成功时就是那次成功请求。

```python
from anybooru import AnybooruHTTPError, Wallhaven

with Wallhaven('wallhaven') as client:
    client.wallpaper_show('pom5lj')
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://wallhaven.cc/api/v1/w/pom5lj

    try:
        client.wallpaper_show('000000')
    except AnybooruHTTPError as error:
        print(error.http_code, error.data)
        # 404 {'error': 'Nothing here'}
```

站点错误正文都是一个带 `error` 字符串的 JSON 对象。本轮实测到的真实状态与正文：

| 请求 | HTTP | 正文 | 说明 |
| :--- | :--- | :--- | :--- |
| `GET api/v1/w/pom5lj` | `200` | `{"data": {...}}` | 生效中的壁纸编号 |
| `GET api/v1/w/000000` | `404` | `{"error": "Nothing here"}` | 不存在的壁纸编号 |
| `GET api/v1/w/94x38z` | `404` | `{"error": "Nothing here"}` | 官方页面示例编号，现在已取不到（**照实记录，别当永久规律**） |
| `GET api/v1/w/pom5lj/similar` | `404` | `{"error": "Not Found"}` | 候选的相似壁纸 URL，实测无此路由；相似走 `q='like:<编号>'` |
| `GET api/v1/user/LewisMweir13` | `404` | `{"error": "Not Found"}` | 候选的用户资料 URL，实测无此路由；上传走 `q='@<用户名>'` |
| `GET api/v1/tag/0` | `404` | `{"error": "Nothing here"}` | 不存在的标签编号 |
| `GET api/v1/settings`（匿名） | `401` | `{"error": "Unauthorized"}` | 需要 key |
| `GET api/v1/collections`（匿名） | `404` | `{"error": "Nothing here"}` | 自己的集合需要 key，**匿名不是 401** |
| `GET api/v1/collections/ThorRagnarok/274175` | `200` | `{"data": [...], "meta": {...}}` | 公开集合的壁纸列表 |
| `GET api/v1/collections/ThorRagnarok/0` | `404` | `{"error": "Nothing here"}` | 不存在的集合编号 |
| `GET api/v1/search?page=1000000` | `400` | `{"error": "Bad Request"}` | 页码越界 |
| `GET api/v1/search?page=0` | `500` | `text/html` 错误页 | 非 JSON 错误正文，`error.data` 是 `None`，`error.body` 是 HTML |

`404` 有两种消息：资源编号不存在、以及自己的集合匿名读取都是 `{"error": "Nothing here"}`；未知路由是 `{"error": "Not Found"}`。`429`（官方 `#limits` 写每分钟 45 次）本轮没有触发，阈值未实测。错误分类与共享异常的完整说明见[错误处理](errors.md)。

## 搜索：代表用法

`wallpaper_search(**params)` 把站点自己的查询键原样发出去。最常用的写法：

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    latest = client.wallpaper_search(page=1)
    # GET https://wallhaven.cc/api/v1/search?page=1
    found = client.wallpaper_search(q='nature', page=2)
    # GET https://wallhaven.cc/api/v1/search?q=nature&page=2
    desktop = client.wallpaper_search(
        q='nature', categories='100', purity='100', atleast='1920x1080')
    # GET https://wallhaven.cc/api/v1/search?q=nature&categories=100&purity=100&atleast=1920x1080
    top_week = client.wallpaper_search(sorting='toplist', topRange='1w')
    # GET https://wallhaven.cc/api/v1/search?sorting=toplist&topRange=1w
    print(found['meta']['total'], [item['id'] for item in found['data'][:3]])
```

本轮样本（都是匿名、都是快照）：`q='nature'` → `total 73383`、`last_page 3058`；`categories='100'` → `337624`；`purity='110'` → `623918`；`atleast='1920x1080'` → `388133`；`sorting='toplist', topRange='1w'` → `483`。`page=2` 回 `meta.current_page=2`。

12 个查询键是 `q`、`categories`、`purity`、`sorting`、`order`、`topRange`、`atleast`、`resolutions`、`ratios`、`colors`、`page`、`seed`；每个键的取值范围、默认值与逐字段返回在[方法参考](wallhaven-api.md)。使用上只需记住两条：

- `resolutions` / `ratios` / `colors` 传**一个逗号串字符串**（`resolutions='1920x1080,1920x1200'`）；传 Python 列表会被编成站点不接受的 `resolutions[]=…`。
- 页码**从 1 起**、每页固定 **24** 条，没有 `per_page`；客户端不补参数、不钳位、不翻页。

`q` 是站点自己的搜索串：关键词、`-词` 排除、`+a +b` 同时满足、`@用户名` 看该用户上传、`type:png` 看文件类型。**相似壁纸用官方 `#search` 给出的 `q='like:<壁纸编号>'`，用户上传用 `q='@<用户名>'`**，都走 `wallpaper_search()`；候选 URL `/api/v1/w/<编号>/similar` 与 `/api/v1/user`、`/api/v1/user/<用户名>` 本轮实测都是 `404 {"error": "Not Found"}`，本类不替它们虚构方法。本轮 `q='like:pom5lj'` 被 Cloudflare 质询挡下（`403` HTML），没有成功样本。`q='id:<标签编号>'` 是官方标注的精确标签搜索（页面写 **"can not be combined"**），指的是它不能与别的 `q` 表达式拼在一起，`purity` / `categories` 这类独立查询参数不受此限；本轮 `q='id:1'` 的 `meta.query` 是对象 `{"id": 1, "tag": "anime"}`，`q='@LewisMweir13'` 是 `total 46`、`last_page 2`（`meta.query` 为空字符串）。

## 详情与标签

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    wallpaper = client.wallpaper_show('pom5lj')
    # GET https://wallhaven.cc/api/v1/w/pom5lj → 200 {"data": {...}}
    data = wallpaper['data']
    print(data['id'], data['resolution'], data['file_type'], data['file_size'])
    print(data['uploader']['username'], len(data['tags']))
    print(data['thumbs']['large'])

    tag = client.tag_show(1)
    # GET https://wallhaven.cc/api/v1/tag/1 → 200 {"data": {...}}
    print(tag['data']['id'], tag['data']['name'], tag['data']['category'])
```

`wallpaper_show('pom5lj')` 本轮样本：`uploader.username='LewisMweir13'`、`tags` 4 条、`resolution='3840x2160'`、`file_type='image/jpeg'`、`path='https://w.wallhaven.cc/full/po/wallhaven-pom5lj.jpg'`、`thumbs` 里有 `large` / `original` / `small`。列表里的壁纸摘要**没有** `uploader` 和 `tags`，这两个键只有详情才有；每张壁纸的全部字段见[方法参考](wallhaven-api.md)。`tag_show(1)` 本轮是 `name='anime'`、`category='Anime & Manga'`、`category_id=1`、`purity='sfw'`。

## 集合与设置（读私有才需要 key）

公开集合不需要 key：

```python
from anybooru import Wallhaven

with Wallhaven('wallhaven') as client:
    collections = client.user_collections('ThorRagnarok')
    # GET https://wallhaven.cc/api/v1/collections/ThorRagnarok → 200
    # {"data": [{"id": 274175, "label": "Default", "views": 37584, "public": 1, "count": 537}, …]}
    print([(item['id'], item['label'], item['count']) for item in collections['data']])

    wallpapers = client.collection_wallpapers('ThorRagnarok', 274175, purity='100', page=1)
    # GET https://wallhaven.cc/api/v1/collections/ThorRagnarok/274175?purity=100&page=1 → 200
    print(wallpapers['meta'])            # {'current_page': 1, 'last_page': 23, 'per_page': 24, 'total': 537}
    print(wallpapers['data'][0]['id'])   # 'po86ve'
```

`user_collections(username)` 只列该用户的**公开**集合，条目是 `id` / `label` / `views` / `public` / `count` 五个键；本轮 `ThorRagnarok`、`EstlinLuna` 返回非空 `data`，`LewisMweir13`、`rootkit` 返回空 `data`——空数组是正常成功。

`collection_wallpapers('ThorRagnarok', 274175, purity='100', page=1)` 本轮 `200`、`data` 24 条、`meta` 是 `{"current_page": 1, "last_page": 23, "per_page": 24, "total": 537}`。**集合壁纸的 `meta` 没有 `query` 和 `seed` 键**（只有搜索的 `meta` 才有），条目也没有 `uploader` / `tags`，要这两个键得再调 `wallpaper_show(<编号>)`。不存在的编号是 `404 {"error": "Nothing here"}`。官方 `#user-settings` 的 “User Collections” 一节说这条路由只有 `purity` 一个过滤参数可用。

要列**自己**的集合（含私有）用 `collection_list()`：需要你的 key，匿名是 `404 {"error": "Nothing here"}`（不是 `401`）。`user_settings()` 同样需要 key，匿名 `401`；带 key 的成功响应本轮没有样本。集合与设置的逐字段说明见[方法参考](wallhaven-api.md)。

## 翻页、随机种子与常见坑

- 页码**从 1 起**、每页固定 **24** 条，没有 `per_page`；`page=2` 本轮返回 `meta.current_page=2`。客户端不自动翻页、不合并。
- **空 `data` 不等于“到末页了”**：`sorting='not-a-sort'`（非法排序）本轮是 `200`、`data: []`，但 `meta` 仍给正的 `total` 与 `last_page`；`page=1000000` 才是 `400 {"error": "Bad Request"}`。
- 页码取值很宽：`page='abc'` 本轮是 `200` 且 `current_page` 回到 `1`（站点忽略非法值），`page=0` 是 `500` HTML 错误页。别把“少一页/空一页”当终止判据，按 `meta.last_page` 与站点自己的状态判断。
- **`sorting='random'` 的种子**：官方 `#search` 说 `sorting='random'` 会产生一个可在页间传递、用来避免翻页重复的 seed。本轮两次样本里 `seed='abc123'` 的第 1、2 页回报的 `meta.seed` 不同（`wPpR1H` / `vMFVjx`），把返回的 `wPpR1H` 再传给第 2 页又得到 `Ec2tSv`——样本不足以断定之后也会变，但客户端不改写 seed、也不替你去重，按实际返回处理。
- **短页 ≠ 结果耗尽**：`sorting='views', order='asc'` 本轮 `per_page 24`、`total 501359`，却只返回 2 条。不要用“本页不足 24 条”推断已到末尾。
- 越界/非法参数很多是 `200` 而不是报错：`categories='abc'` 本轮 `200`（过滤没生效，`total` 比默认还大）、非法 `sorting` 也是 `200`。别把 `200` 当参数被采纳的证明。
- `resolutions` / `ratios` / `colors` 传 Python 列表会被编成 `resolutions[]=…`，要用逗号串字符串。

## 媒体地址

`path`、`thumbs.large` / `thumbs.original` / `thumbs.small`、以及用户 `avatar` 里的 `200px` / `128px` / `32px` / `20px` 都是**完整地址字符串**，原样返回。本库不下载、不推导、不换分片、不改扩展名、不删查询串；返回一个地址不代表它当前可下载或获准使用。

## 可运行示例与冒烟脚本

```bash
python -X utf8 examples/wallhaven/list_wallpapers.py --config my-anybooru.json
python -X utf8 examples/wallhaven/browse_resources.py --config my-anybooru.json
python -X utf8 test/wallhaven.py --config my-anybooru.json
```

不传 `--config` 使用包内配置；示例还有 `--site`，缺省取 `examples.wallhaven.site`。两个示例都是**匿名只读**，调用来自 `examples.wallhaven`：

- `list_wallpapers.py`：按 `search_query`（`q='nature'`、`categories='100'`、`purity='100'`、`sorting='date_added'`、`order='desc'`）取 `pages` 里的第 1、2 页，再按 `tag_query`（`q='id:1'`、`purity='100'`）做一次精确标签查询——共 3 次 `GET`。
- `browse_resources.py`：依次读 `wallpaper_id='pom5lj'` 的详情、`tag_id=1` 的标签、`user_collections('ThorRagnarok')` 的公开集合列表，再按 `collection_id=274175` 与 `collection_query`（`purity='100'`、`page=1`）读集合里的壁纸——共 4 次 `GET`。

冒烟用 `smoke.wallhaven`（同样含 `pages` 两页、`tag_query`、壁纸、标签、集合与 `missing_wallpaper_id='000000'` 的预期 `404`，共 8 次请求），**脚本里没有硬编码的站点或查询值**。实测范围以[验证记录](verification.md#wallhaven匿名只读实测2026-10-03)为准；方法存在不等于每条参数组合都跑过。

## 边界与未实测

- **带 key 的成功路径一轮都没发过**：`apikey` 查询值、`X-API-Key` 请求头都只有官方页面依据，没有成功响应样本；错误 key 返回什么、NSFW 壁纸的 `401` 具体形态、带 key 后 `settings` / `collection_list` / 私有集合返回什么，都未实测。
- **集合壁纸与设置只有匿名样本**：集合里的壁纸有匿名 `200` 样本（`ThorRagnarok/274175` 第 1、2 页），但带 key 读私有集合、`collection_list()` 的带 key 成功形态没有样本；`user_settings()` 的带 key `{"data": {...}}` 也只有官方 `#user-settings` 示例，本轮只有它的匿名 `401`。
- **限流未触发**：官方 `#limits` 写每分钟 45 次、超出回 `429`；本轮只观察到站点回 `X-RateLimit-Limit: 45`，阈值与 `429` 正文没有验证。客户端不做节流，节奏由调用者控制。
- **随机种子与末页语义未穷尽**：`sorting='random'` 的稳定种子、去重行为、各排序的末页判据都只有单点样本，见上文「翻页、随机种子与常见坑」。
- **`like:` 相似搜索没有成功样本**：本轮唯一一次被 `403` HTML 质询挡下，也没有任何绕过或回退。
- **媒体字节零请求**：所有 `path` / `thumbs` / `avatar` 主机一个都没请求过，可下载性与许可未验证。
- **搜索参数的边界值未穷举**：`colors` 的 29 个取值只测了 `660000`；`resolutions` / `ratios` 的单个值与上限、`topRange` 的七个取值、`categories` / `purity` 的其它组合、`seed` 的非法值都未实测。
- **官方页面与站点会不一致**：官方页面示例编号 `94x38z` 现在实测 `404`；官方 `#search` 示例里的 `path` 不带 `/full/` 段，而本轮 `pom5lj` 的 `path` 带 `/full/` 段。照实记录，不推断新旧格式、不修补。

更细的维护者依据与排除项见[契约附注](wallhaven-contract-notes.md)；逐条命令、URL 与状态码见[验证记录](verification.md#wallhaven匿名只读实测2026-10-03)。

继续阅读：[方法参考](wallhaven-api.md) · [能力入口](wallhaven-capabilities.md) · [契约附注](wallhaven-contract-notes.md) · [验证记录](verification.md#wallhaven匿名只读实测2026-10-03)。
