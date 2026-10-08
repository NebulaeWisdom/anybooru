# Pixiv 客户端用法

`Pixiv` 访问 pixiv 的 **两个 JSON 面**：站点前端自用的网页端 API（`https://www.pixiv.net`，路由是 `ajax/...`、`ranking.php`、`rpc/*.php`）与官方移动客户端的 App API（`https://app-api.pixiv.net`，路由是 `v1/...`、`v2/...`、`webview/...`）。它不是任何一套已有 booru 引擎的站点：网页端多数路由返回 `{"error": false, "message": "", "body": {...}}` 信封、搜索/排行榜/评论那几条没有 `message`、`ranking.php` 更是裸根对象；App 面直接返回裸 JSON（列表就是 `{"illusts": [...], "next_url": "..."}` 这个对象本身），所以是**独立家族**。

本类一共 **140 个原生方法**：**81 个 `web_`**（网页端，65 个 `GET` + 16 个 `POST`；`GET` 里 64 个只读，另一个是写查询 `web_bookmark_rename_progress`）与 **59 个 `app_`**（App 面，53 个只读 `GET` + 6 个 `POST`）。方法名一律带 `web_` / `app_` 前缀区分两台主机。没有登录方法、不换令牌、不下载图片：`urls` / `url` / `image` / `zip_urls` 里的地址原样给你，是否取字节由你自己决定。

**每方法的路由、全部参数与逐字段返回在[方法参考](pixiv-api.md)**；「我要做什么 → 用哪个方法」与 140 方法一行索引见[能力入口](pixiv-capabilities.md)；两面依据分级、权限分支与排除项见[契约附注](pixiv-contract-notes.md)。本页只讲**这个类怎么用**：构造、认证、`request()`、JSON 与表单与纯文本正文、返回值与 `last_call`、错误、能直接抄的调用、翻页、两个脚本、边界。

## 依据

pixiv **没有一份完整的官方公开 API 规范**，也没有可引用的本地服务端源码。本页结论分两档：

- **网页端**：依据是本轮对 `https://www.pixiv.net` 的**匿名只读**直接请求（真实 URL、状态码与字段见[验证记录](verification.md)），辅以四个社区前端逆向来源（`YieldRay/pixiv-web-api`、`PixivNow` 的 web 文档、`daydreamer-json/pixiv-ajax-api-docs`（作者自述已过时）、一份社区小说端点参考）。这些都是**第三方**，不是服务端契约；有实测状态与字段的按实测写，只有来源的按来源写并标注。
- **App 面**：依据是公开客户端 `pixivpy` 的 `pixivpy3/aapi.py` 与 `models.py`、`gallery-dl` 的 Pixiv 提取器、一份第三方 OpenAPI（`hanshsieh/pixiv-api-doc`）与一份 **2016 年**的 Android 客户端抓包（`ZipFile`，Android 5.0.17）。这些都是第三方来源，不是 pixiv 官方规范；旧抓包不保证当前路由仍可用。本轮仅应用信息与表情定义两条路由匿名成功，带凭据的成功路径没有实测。

本轮真跑的范围以[验证记录](verification.md)为准，不是对站点当前状态的保证。

## 三行上手

```python
from anybooru import Pixiv

with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
    illust = client.web_illust_show('149040133')
    print(illust['error'], illust['body']['illustTitle'],
          illust['body']['userId'], illust['body']['pageCount'])
    print(client.last_call['status_code'], client.last_call['url'])
```

真实请求 `GET https://www.pixiv.net/ajax/illust/149040133`，本轮 `200 application/json; charset=utf-8`：返回 `{"error": false, "message": "", "body": {...}}`，`body.illustTitle` 是作品标题、`body.userId` 是作者编号、`body.pageCount` 是页数，图片地址在 `body.urls` 的 `mini` / `thumb` / `small` / `regular` / `original` 五个键里。这些字段值都是当时的快照，不是客户端常量。

## 构造与配置

```python
Pixiv(site_name=None, site_url=None, cookie=None, access_token=None,
      proxies=None, *, app_url=None, csrf_token=None, config_file=None,
      timeout=None, user_agent=None)
```

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 段里的键名 | 不选命名站点，需显式给 `site_url`（App 面还需 `app_url`） | `Pixiv('pixiv')` |
| `site_url` | 字符串，**网页端**根地址 `https://www.pixiv.net` | 读取所选站点的 `url`（包内即 `https://www.pixiv.net`）；末尾 `/` 被去掉 | `Pixiv(site_url='https://www.pixiv.net')` |
| `cookie` | 字符串，网页端登录会话，作为 `Cookie` 请求头发给网页端 | `None` 且有站点名就读 `sites.<站点名>.cookie`（包内为空串） | `Pixiv('pixiv', cookie='')` |
| `access_token` | 字符串，App 面令牌，非空时发 `Authorization: Bearer <token>` | `None` 且有站点名就读 `sites.<站点名>.access_token`（包内为空串） | `Pixiv('pixiv', access_token='')` |
| `proxies` | 字典，按 `http` / `https` 指定代理；`{}` 表示直连 | 使用 `request.proxies`；**不读环境变量** | `Pixiv('pixiv', proxies={})` |
| `app_url` | 字符串，**App 面**根地址 `https://app-api.pixiv.net`；仅关键字参数 | 读取所选站点的 `app_url`；末尾 `/` 被去掉 | `Pixiv('pixiv', app_url='https://app-api.pixiv.net')` |
| `csrf_token` | 字符串，网页端写路由的 `X-CSRF-Token` 头 | `None` 且有站点名就读 `sites.<站点名>.csrf_token`（包内为空串） | `Pixiv('pixiv', csrf_token='')` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json` | `Pixiv('pixiv', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout` | `Pixiv('pixiv', timeout=30)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent` | `Pixiv('pixiv', user_agent='MyPixClient/1.0')` |

包内站点条目（两个根都放同一个站点键，`request(..., api=...)` 显式选根）：

```json
{"pixiv": {"url": "https://www.pixiv.net", "app_url": "https://app-api.pixiv.net",
           "cookie": "", "csrf_token": "", "access_token": ""}}
```

**构造不发任何请求**，也不校验凭据，所以没有 token 也能构造出可用客户端（网页端匿名可用）。App 面若既没给 `site_name` 也没给 `app_url`，调用 `api='app'` 的方法时会因根地址为 `None` 直接报错——要用 App 面就显式给 `app_url` 或 `site_name`。用完 `client.close()`，或用 `with` 语句块自动释放会话。换一份自己的完整配置、往 `sites.pixiv` 各字段填值的写法见[配置指南](configuration.md)。

## 认证：三个凭据与两台主机

pixiv 的两台主机用**不同**的凭据，本类把这一点写死：

- **网页端**（`api='web'`，默认）：每次请求都带 `Referer: https://www.pixiv.net/`；`cookie` 非空时带 `Cookie` 头、`csrf_token` 非空时带 `X-CSRF-Token` 头。三者各自三态：`None`（且有 `site_name`）读包内配置、显式 `''` **固定匿名**且不读配置、非空使用。
- **App 面**（`api='app'`）：`access_token` 非空时带 `Authorization: Bearer <access_token>`；显式 `''` 固定匿名。**不伪造** `app-os` / `app-os-version` / `PixivAndroidApp` 之类 User-Agent，也不加 `x-client-time` / `x-client-hash`（那是换 token 端点的东西，普通业务路由不需要）；用的是本包统一配置的 User-Agent。
- **哪个头只由 `api` 决定**：绝不看 URL 猜。传 App 列表返回的绝对 `next_url` 回填时，**同时**要传 `api='app'`，否则它会被当成网页端调用而又不发 Bearer。

本类**不实现** OAuth2 登录 / PKCE 授权码 / 令牌刷新 / 自动取 Cookie：你给什么就用什么，被拒或过期的凭据产生的是站点自己的答复。**不要把 token 写进源码或提交进仓库**。

单次调用可用 `headers` 覆盖任一默认头：

```python
from anybooru import Pixiv

token = input('pixiv access token: ')          # 你自己的 token；不要提交
with Pixiv('pixiv', access_token='') as client:  # 不自动带配置里的 token
    detail = client.request('GET', 'v1/illust/detail', api='app',
                            params={'illust_id': '149040133'},
                            headers={'Authorization': 'Bearer ' + token})
    print(detail['illust']['title'])
```

配置里有 token、只想让某一次匿名，就在构造时传 `access_token=''`（App 面即不带 `Authorization`）；反过来，实例上没配 token 也能靠这一次的 `headers` 临时带上。

**匿名能得到什么、得不到什么**：本轮插画详情/页列表、用户资料与作品索引、搜索、排行榜、小说与部分评论/标签/发现路由取得匿名成功；用户关注、时间线和新版发现等选定请求返回 `400`。App 面应用信息与表情定义两条路由返回 `200`，8 条业务路由返回 OAuth `invalid_request` 的 `400`。未请求的路由不能据此断言匿名可用或必拒，Cookie/token 权限说明与成功字段按各方法的第三方来源列出。

## 通用入口 `request()`

```python
request(method, path, *, api='web', params=None, data=None, form=None,
        headers=None, response_format='json')
```

原生方法只是把参数拼好再调它。`path` 用 `urljoin(选中根 + '/', path)` 拼接，所以相对路由、前导 `/` 的路由与**绝对 URL** 三种写法都到达它们命名的地址：

| `path` 写法 | `api` | 实际请求的地址 |
| :--- | :--- | :--- |
| `'ajax/illust/149040133'` | `'web'`（默认） | `https://www.pixiv.net/ajax/illust/149040133` |
| `'/ranking.php'` | `'web'` | 同上：前导 `/` 与不带等价 |
| `'v1/user/detail'` | `'app'` | `https://app-api.pixiv.net/v1/user/detail` |
| App 列表返回的 `next_url`（绝对地址） | `'app'` | 原样回填的那条地址（**必须同时传 `api='app'`**） |

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词，如 `'GET'`、`'POST'` | 必填 | `client.request('GET', 'ajax/illust/149040133')` |
| `path` | 上表的写法（相对路由或绝对地址） | 必填 | `client.request('GET', 'v1/user/detail', api='app', params={'user_id': '27517'})` |
| `api` | `'web'`（默认）或 `'app'`，显式选根**并决定发哪套凭据头** | 默认 `'web'` | `client.request('GET', 'v1/emoji', api='app')` |
| `params` | 查询参数字典，按下面的编码规则发送 | `None`，不发查询参数 | `client.request('GET', 'ajax/illust/149040133', params={'full': 1})` |
| `data` | **JSON 正文**，原样作为请求体发送（`None` 值也保留），仅 `POST` 写路由用 | `None`，不发 JSON 正文 | `client.web_bookmark_add('illusts', illust_id='149040133', restrict='0')` |
| `form` | **表单正文**，用与 `params` 相同的编码器编码，仅部分 `POST` 路由用 | `None`，不发表单正文 | `client.web_bookmark_delete('illusts', bookmark_id='123')` |
| `headers` | 额外请求头，合并并**覆盖**本节上面的默认头 | `None`，不附加 | `client.request('GET', 'v1/emoji', api='app', headers={'Accept-Language': 'ja'})` |
| `response_format` | `'json'`（默认）解析 JSON；`'text'` 返回正文原文 | 默认 `'json'` | `client.app_webview_novel('12345678')`（内部用 `'text'`） |

**JSON / 表单 / 纯文本正文怎么区分**（三件事互不混淆）：

- 网页端的写路由分两种正文：`ajax/<work_type>/bookmarks/add`、`.../add_tags`、`.../edit_restrict`、`.../remove`、`ajax/<work_type>/like`、`ajax/block/save`、`ajax/<work_type>/series/<id>/watch` 等收 **JSON**（走 `data`）；`ajax/<work_type>/bookmarks/delete`、`rpc/post_comment.php`、`rpc_delete_comment.php`、`bookmark_add.php`、`rpc_group_setting.php` 收 **表单**（走 `form`）。App 面的 6 个 `POST` 全部走**表单**。同一次调用最多用其中一种正文，原生方法已经把该路由要的那种选好。
- 原生方法名里带 `**attributes` 的方法传的是**请求体**（JSON 或表单取决于路由），带 `**params` 的方法传的是**查询参数**。别把 JSON 体塞进 `params`。（上表 `data` / `form` 两行用的是写路由举例，只为说明正文形态；写路由本项目从不调用。）
- `response_format='text'` 是**显式**的、不嗅探 `Content-Type`：只有 `app_webview_novel()` 用它，因为那条路由返回的是网页 HTML 而不是 JSON。给它别的值抛 `KeyError`。

**查询参数编码**用本库共享编码，规则四条：

| 你传的值 | 发出去的样子 | 例子 |
| :--- | :--- | :--- |
| `None` | 整个键**丢弃** | `params={'p': 1, 'lang': None}` → 只发 `p=1` |
| 布尔 | 小写 `true` / `false` | `params={'include_total_comments': True}` → `include_total_comments=true` |
| 列表 / 元组 | 键带方括号重复：`key[]=值` | `params={'ids': ['149040133']}` → `ids%5B%5D=149040133` |
| 嵌套字典 | `key[子键]=值` | `params={'range': {'start': 1}}` → `range%5Bstart%5D=1` |

因此**逗号串参数要写字面字符串**（App 面 `already_recommended='12345,67890'`），不要写 Python 列表；列表一律编成重复的 `key[]=`，插画推荐的续页 `web_illust_recommend_illusts(illust_ids, **params)` 也一样（`illust_ids[]=`）。

客户端不补前缀、不补尾斜杠、不拆外层、不改字段名、不重试、不钳位页码或取值，也不做本地校验。

## 返回值、`last_call` 与错误

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | 解析后的对象，**一层都不拆**：网页端给你完整的 `{"error": ..., "message": ..., "body": ...}`（有的路由没有 `message`）；搜索/排行榜/`ranking.php` 各是它们自己的外壳（`{"error", "body"}` 或裸根对象）；App 面给你 `{"illusts": [...], "next_url": "..."}` 这样的对象本身 |
| HTTP 非 2xx（含 `3xx`） | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`（原始文本）、`data`（能解析成 JSON 时是解析结果，否则 `None`）、`response` |
| 2xx 但正文为空 | 返回 `None` |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError`（App 面 `webview/v2/novel` 用 `response_format='text'`，不会走这条） |
| 网络错误 | requests 自己的异常原样抛出，没有重试与退避 |

**HTTP 200 而正文 `error` 为 `true` 时也当数据返回**，不会转成本地异常；只有非 2xx 才会抛错。重定向**从不跟随**（`allow_redirects=False`）：`3xx` 直接抛 `AnybooruHTTPError`，`Location` 保留在 `error.response` / `error.headers` 里。

`client.last_call` 是最近一次请求的 `API`（去掉前导 `/` 的路由原文）、`url`（含查询串的真实地址）、`status_code`、`status`（原因文本）、`headers`；**它在每次请求前清空**，所以失败时记录的就是那次失败请求。

```python
from anybooru import AnybooruHTTPError, Pixiv

with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
    client.web_illust_show('149040133')
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://www.pixiv.net/ajax/illust/149040133

    try:
        client.web_illust_show('59580629')
    except AnybooruHTTPError as error:
        print(error.http_code, error.data)
        # 404 {'error': True, 'message': '', 'body': []}
```

本轮实测到的真实状态与正文（都是快照）：

| 请求 | HTTP | 正文 | 说明 |
| :--- | :--- | :--- | :--- |
| `GET ajax/illust/149040133` | `200` | `{"error": false, "message": "", "body": {...}}` | 生效中的插画编号 |
| `GET ajax/illust/59580629` | `404` | `{"error": true, "message": "", "body": []}` | 不存在的插画编号（`body` 是空数组，不是对象） |
| `GET ajax/illust/0` | `400` | `{"error": true, "message": "不正なリクエストです。", "body": []}` | 非法编号 |
| `GET ranking.php?mode=daily&p=1&format=json` | `200` | 裸根对象（含 `contents` / `rank_total` / `next`） | 排行榜 |
| `GET ranking.php?mode=daily&p=10000&format=json` | `404` | `{"error": "ランキング集計の範囲外です"}` | 越界页码，正文是另一种裸对象 |
| `GET ajax/search/artworks/cat?...&p=10000` | `200` | 仍是第 1 页样式的内容 | 搜索越界**不报错**，`HTTP 200` 不是页码有效的证明 |
| `GET v1/illust/detail?illust_id=59580629`（匿名） | `400` | `{"error": {"user_message": "", "message": "...invalid_request", "reason": "", "user_message_details": {}}}` | App 面缺 token，裸 `error` 对象、不是网页端信封 |

`404` / `400` / `401` 的正文分几种：网页端不存在的资源是带 `error: true` 的信封，`ranking.php` 越界是裸 `{"error": "..."}`，App 面是裸 `{"error": {...}}`。错误正文非 JSON（例如 Cloudflare 质询 HTML）时 `error.data` 是 `None`、`error.body` 是 HTML。错误分类与共享异常的完整说明见[错误处理](errors.md)。

## 搜索：代表用法

网页端搜索把站点自己的查询键原样发出，作品数组在 `body.illustManga.data`（插画/漫画）或 `body.novel.data`（小说）里，`body` 里同时有 `total` 与 `lastPage`：

```python
from anybooru import Pixiv

with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
    first = client.web_search_artworks(
        'cat', order='date_d', mode='all', p=1, s_mode='s_tag', type='all')
    # GET https://www.pixiv.net/ajax/search/artworks/cat?word=cat&order=date_d&mode=all&p=1&s_mode=s_tag&type=all
    manga = first['body']['illustManga']
    works = [row for row in manga['data'] if 'isAdContainer' not in row]
    print(manga['total'], manga['lastPage'],
          len(works), len(manga['data']) - len(works),
          [row['id'] for row in works[:3]])

    second = client.web_search_artworks(
        'cat', order='date_d', mode='all', p=2, s_mode='s_tag', type='all')
    # GET .../artworks/cat?word=cat&order=date_d&mode=all&p=2&s_mode=s_tag&type=all
    rows = second['body']['illustManga']['data']
    print([row['id'] for row in rows if 'isAdContainer' not in row])
```

本轮 `word='cat'` 样本的 `illustManga.total=107077`、`lastPage=10`；`data` 有 **60 个槽位**（59 个作品和 1 个 `{"isAdContainer": true}` 广告槽）。客户端原样返回，例子按实际行类型区分作品和广告并报数。`p=10000` 仍是 `200`，前三个作品 ID 与 `p=10` 相同；这不能证明深页有效。`lastPage` 记录站点这次给出的页界，但它和 `total`/每页槽数不能组成精确总页数公式。常用查询有 `order='date_d'`、`mode='all'`、`s_mode='s_tag'`、`type='all'`、`p=1`；其它排序和尺寸/日期/收藏数筛选的来源枚举与省略行为见[方法参考](pixiv-api.md)，不保证所有组合都已验证。

只搜插画用 `web_search_illustrations(word, ...)`（`body.illust.data`），只搜漫画用 `web_search_manga(word, ...)`（`body.manga.data`），搜小说用 `web_search_novels(word, ...)`（`body.novel.data`）。本轮前三种作品搜索各有 60 槽、1 个广告；小说搜索样本为 30 条且没有广告。数字仅属于这次请求，不能据此保证每页数量或其它路由永远没有广告。

## 详情、插画页与榜单

```python
from anybooru import Pixiv

with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
    illust = client.web_illust_show('149040133')['body']
    # GET https://www.pixiv.net/ajax/illust/149040133 → 200
    print(illust['illustId'], illust['illustTitle'], illust['pageCount'],
          illust['width'], illust['height'])
    print(sorted(illust['urls']))          # mini/thumb/small/regular/original
    print([tag['tag'] for tag in illust['tags']['tags']])
    # tags.tags 每项至少有 tag/locked/deletable；作者自己加的标签还带
    # userId/userName，其它标签可能没有这两个键。

    pages = client.web_illust_pages('149040133')['body']
    # GET https://www.pixiv.net/ajax/illust/149040133/pages → 200
    print(len(pages), pages[0]['width'], pages[0]['height'],
          sorted(pages[0]['urls']))        # thumb_mini/small/regular/original

    ranking = client.web_ranking(mode='daily', p=1)
    # GET https://www.pixiv.net/ranking.php?mode=daily&p=1&format=json → 200
    print(ranking['rank_total'], ranking['content'], ranking['page'],
          ranking['next'], ranking['date'])
    print(ranking['contents'][0]['rank'], ranking['contents'][0]['illust_id'])
```

要点：

- `web_illust_show('149040133')` 本轮 `200`：`body.pageCount=1`，`body.urls` 五个地址；`web_illust_pages('149040133')` 本轮 `200`，`body` 是数组、每张图一项（`urls` 只有 `thumb_mini`/`small`/`regular`/`original`），一次给全所有分页地址、**没有页码参数**。多页图的单独地址看这里，客户端一张都不下载。
- `web_ranking(mode='daily', p=1)` 返回**裸根对象**（没有 `error`/`body` 外壳）：`contents` 每页 50 条、`rank_total` 是榜单总名额（日榜 500）、`prev`/`next` 是上一/下一页（`false` 表示没有）。每条 `contents` 里的 `illust_series` **可能是布尔 `false`，也可能是对象**（带 `illust_series_id`/`title`/`caption`/`content_count`/`page_url` 等键，作品属于某个系列时才出现）——别假定它一定是布尔。客户端方法会自动补 `format=json`，否则该路由返回整个 HTML 排行榜页；自己传 `format` 会覆盖它。
- 只想要 `web_illust_show` 的 `full=1` 更全的字段，就自己在调用里传 `full=1`（站点自己的页面会带，本类不替你补）。

## 用户、小说与评论

```python
from anybooru import Pixiv

with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
    user = client.web_user_show('27517', full=1)['body']
    # GET https://www.pixiv.net/ajax/user/27517?full=1 → 200
    print(user['userId'], user['name'], user['premium'], user['following'])

    profile = client.web_user_profile_all('27517')['body']
    # GET https://www.pixiv.net/ajax/user/27517/profile/all → 200
    print(len(profile['illusts']), len(profile['manga']),
          profile['bookmarkCount'])

    comments = client.web_illust_comments('149040133', offset=0, limit=2)['body']
    # GET https://www.pixiv.net/ajax/illusts/comments/roots?illust_id=149040133&offset=0&limit=2 → 200
    print(comments['hasNext'], [c['id'] for c in comments['comments']])
```

- `web_user_profile_all(user_id)` 的 `body.illusts` / `body.manga` 是 `{"作品编号": null}` 的字典（编号有序、值一律 `null`，只给编号清单），要详情再逐条调 `web_illust_show`；`body.novels` 是数组，另有 `mangaSeries`/`novelSeries`/`collections`/`pickup`/`bookmarkCount` 等。这条路由不分页。
- 一次取多个作品/多篇小说的公开信息：`web_user_profile_illusts(user_id, ids=[...])`、`web_user_illusts(user_id, ids=[...])`、`web_user_novels(user_id, ids=[...])`；批量检索标签用 `web_frequent_tags(work_type, ids=[...])`。`ids` 是列表，编成重复的 `ids[]=`。
- 小说详情看 `web_novel_show(novel_id)`（`body.content` 是正文、`body.seriesNavData` 是系列导航）；`web_novel_series(series_id)` 与 `web_novel_series_content(series_id, ...)` / `web_novel_series_titles(series_id)` 读系列与目录，`web_novel_series_content` 的 `order_by` 来源写作 `asc` / `dsc`（来源的原拼写，本类不悄悄改成 `desc`）。
- 评论分「顶层」与「回复」两组：`web_illust_comments(w)` / `web_illust_comment_replies(comment_id)` 与 `web_novel_comments(w)` / `web_novel_comment_replies(comment_id)`，返回 `body.comments` 与 `body.hasNext`。
- 需要会话 Cookie 的路由（`web_user_following`、`web_user_bookmarks`、`web_follow_latest`、`web_top_illust`、`web_discovery_artworks` 等）匿名会被站点拒；本类照实抛出站点状态，不做回退。

## 翻页与常见坑

- **网页端页码从 1 起**（搜索 `p`、排行榜 `p`），列表用站点自己的页计数（`lastPage` / `total` / `page` / `next`），客户端不自动翻页、不合并、不钳位。
- **HTTP 200 ≠ 页码有效**：搜索 `p=10000` 本轮仍 `200` 且内容像第 1 页；排行榜越界 `p=10000` 才是 `404`。别用「短页/空页/200」当终止判据，按 `illustManga.lastPage` 或 `rank_total` 与站点自己的状态判断。
- **App 面用绝对 `next_url` 游标**：列表返回的 `next_url` 原样交回 `client.request('GET', next_url, api='app')`；本类不解析、不递增、不自动跟随。**回填绝对地址时必须传 `api='app'`**。
- **列表值写字面 Python 列表**（编成重复 `key[]=`），逗号串写字面字符串；`web_illust_recommend_illusts` 的 `illust_ids` 也走同一编码（`illust_ids[]=`）。
- **`web_search_artworks` 的路径段与查询键都叫 `word`**：路径是 `/artworks/<词>`、查询是 `?word=<词>`，方法自己各拼一份，调用方只传一次 `word`。
- 账号范围网页路由的 Cookie 权限来自第三方来源；本轮选定匿名请求只观察到 `400`，没有带会话的成功样本。

## 媒体地址

`body.urls`（`mini`/`thumb`/`small`/`regular`/`original` 或页列表的 `thumb_mini`/`small`/`regular`/`original`）、用户 `image`/`imageBig`、ugoira 的 `src`/`originalSrc`/`zip_urls`、App 面的 `image_urls`、`coverUrl`、`zip_urls` 都是 **`i.pximg.net` / `s.pximg.net` 上的完整地址字符串**，原样返回。本库不下载、不推导、不改扩展名、不换分片、不删查询串；返回一个地址不代表它当前可下载或获准使用（pixiv 的图片主机通常还要求 `Referer: https://www.pixiv.net/`，那是图片 CDN 的事，不在本 API 面内）。

## 可运行示例与冒烟脚本

```bash
.venv/Scripts/python.exe examples/pixiv/list_artworks.py --config my-anybooru.json
.venv/Scripts/python.exe examples/pixiv/browse_resources.py --config my-anybooru.json
.venv/Scripts/python.exe test/pixiv.py --config my-anybooru.json
```

不传 `--config` 使用包内配置；示例还有 `--site`，缺省取 `examples.pixiv.site`。两个示例都是**匿名只读、只走网页端**，调用来自 `examples.pixiv`：

- `list_artworks.py`：按 `search_query`（`order='date_d'`、`mode='all'`、`s_mode='s_tag'`、`type='all'`）取 `pages` 里的第 1、2 页 `web_search_artworks`，再按 `ranking_query`（`mode='daily'`、`p=1`）取一次 `web_ranking`——共 3 次 `GET`。
- `browse_resources.py`：依次读 `illust_id='149040133'` 的 `web_illust_show`、`web_illust_pages`，`user_id='27517'` 的 `web_user_show`（配 `user_query` 的 `full=1`）与 `web_user_profile_all`——共 4 次 `GET`。

冒烟用 `smoke.pixiv`（同样含 `pages` 两页、`search_query`、`ranking_query`、`illust_id`、`user_id`、`user_query`，另有 `missing_illust_id='59580629'` 的预期 `404` 与一次匿名 `app_illust_detail` 的预期 `400`，共 10 次请求），**脚本里没有硬编码的站点或查询值**。实测范围以[验证记录](verification.md)为准；方法存在不等于每条参数组合都跑过。

## 边界与未实测

- **App 面带凭据的成功路径未测**：`app_application_info()` 与 `app_emoji()` 对应路由由直接 HTTP 请求取得匿名 `200`；8 条业务路由匿名返回 `400` OAuth 错误，其余仅源码对齐。这里不是说这些 Python 方法全部执行过；实际运行的方法见验证记录。路由、参数与成功字段来自 P/Z/H/G 第三方来源，旧抓包不保证当前可用性。
- **App 面有若干路由只给路径、不给返回 schema**：`app_trending_tags_manga()`、`app_trending_tags_novel()`、`app_illust_popular()`、`app_novel_popular()`、`app_search_autocomplete()`（`search_auto_complete_keywords` 的数组元素）、`app_user_state()`（`user_state` 内的字段）等都只按来源给出路由与已见键，本库**不编造字段**。
- **网页端账号范围路由没有成功样本**：`web_user_following`、`web_user_bookmarks`、`web_follow_latest`、`web_top_illust`、`web_discovery_artworks` 对应请求本轮均为匿名 `400`，不是 `401`。需要会话的说明来自第三方源码；单次“非法请求”正文不能独自证明失败只由未登录造成，带 Cookie 的成功路径未测。
- **22 个 POST 一次都没有执行**：16 个网页端 POST 与 6 个 App POST 仅源码对齐。`web_bookmark_rename_progress` 则是读取进度的 GET，其两条资源路由已直接匿名探测并返回 `400`，但该 Python 方法未运行。源码未声明的写响应字段不作补造。
- **参数枚举未穷尽**：搜索的高级过滤键、榜单 `mode` 的全部取值、`web_novel_series_content` 的 `order_by` 全部取值等只有来源枚举，未逐值实测。参数名不在已知集合里也会原样发出，站点可能自行忽略或报错。
- **媒体字节零请求**：所有 `i.pximg.net` / `s.pximg.net` 地址一个都没请求过，可下载性、Referer 要求与许可未验证。
- **风控触发条件未测**：本轮未对缺 Referer、客户端标识或来源网络做对照，不能据这些样本归因挑战或限流。本类不自动重试、不更换主机、不跟随重定向。
- **App 面协议常量**：本类只发调用方给的 `Authorization: Bearer`，不注入 `app-os` / `app-os-version` / `app-version` 之类头；若某路由在真实客户端里依赖这些头，缺头下的结果是站点自己的答复。
- **没有 OAuth / 登录 / 刷新**：本类不实现 PKCE、`/auth/token`、令牌刷新与自动取 Cookie；token 与 cookie 由你自己取得并传入。

更细的依据出处、权限分支与排除项见[契约附注](pixiv-contract-notes.md)；逐条 URL、状态码与响应摘要见[验证记录](verification.md)。

继续阅读：[方法参考](pixiv-api.md) · [能力入口](pixiv-capabilities.md) · [契约附注](pixiv-contract-notes.md) · [验证记录](verification.md)。
