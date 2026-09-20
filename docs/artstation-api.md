# ArtStation 方法参考

`ArtStation` 访问 ArtStation（`https://www.artstation.com`）的站点自研接口，不套用 booru 模型。booru 模型指图片站常用的一套接口约定（标签、评分、pools 等），本站不用这套。

作品在站点里叫 project，标识同时有数字 `id` 与短码 `hash_id`，两者用途不同，见[编号：`id` 与 `hash_id`](#编号id-与-hash_id)。

本类一共 **17 个原生方法**：**15 个匿名只读 `GET`**（**14 个返回 JSON**，`feed()` 返回 **RSS 原文**字符串）加 **2 个 `POST`**——准备匿名 CSRF 令牌的 `csrf_token()` 与只读搜索 `project_search_post()`。CSRF 指跨站请求伪造，令牌用来确认请求来自真人页面而非第三方网站。

两个 `POST` **不是内容写入**：一个只取会话令牌，一个只读搜索结果。站点里发作品、改资料、评论、收藏、关注、上传、删除这类**内容与账号写操作一个都没有包装**。

**没有凭据字段、没有媒体下载方法**，构造函数不读取账号配置。覆盖范围是**公开作品集资源与 RSS 订阅源**——全站作品流、搜索、用户与作品集、社区（相册 / 频道 / 评论 / 探索）加一个订阅源；**不是 ArtStation 的完整封装**：站点的打印、市集、学习、招聘、博客、公告、词典、合集等路由与站点页面 HTML 都不在这里，也没有对应的包装方法。

构造、代理、超时、`last_call`、参数编码这类"类怎么用"的问题见[客户端用法](artstation.md)；「我要做什么 → 用哪个方法」见[能力入口](artstation-capabilities.md)；依据出处、排除项与候选输入的错误见[契约附注](artstation-contract-notes.md)。

本页结论来自**本轮 37 次直接匿名只读 `GET`**（31 次路由与边界 + 6 次取值边界补充；串行、相邻至少 1.3 秒、各发一次、不重试、不跟随跳转、不下载媒体；冒烟与示例脚本自己发起的调用另按脚本统计），真实请求记录见[验证记录](verification.md#artstation匿名只读实测2026-09-20)。这 37 个响应的状态分布是 `200`×25、`400`×9、`401`×1、`403`×1、`404`×1；格式分布是 `application/json`×28、`application/rss+xml`×1、`text/html`×4、`text/plain`×4。**两个 `POST` 另有单独一组匿名样本（CSRF 令牌与只读搜索）**，观测值单列在[匿名 CSRF 令牌与只读搜索 POST](#匿名-csrf-令牌与只读搜索-post)，不并入上面的 GET 统计。样本里的 `total_count`、作品编号、频道编号都只是那次请求的读数，**不保证稳定**；以下字段清单描述选定样本，不是字段全集或必填 schema。

接入时收到的候选输入资料只用来选请求，**算契约的只有下面的 L 与 P 证据**：文中每个参数、字段、边界要么有 L 或 P 支持，要么当场标成"未实测"。

## 方法索引

| 方法 | HTTP | 路由（拼在站点根后） | 外层 | 每项键数 / 条目 |
| :--- | :--- | :--- | :--- | :--- |
| [`project_list`](#全站作品流-project_list) | `GET` | `/projects.json` | `{"data": […], "total_count": N}` | 21 |
| [`project_random`](#随机作品-project_random) | `GET` | `/random_project.json` | 裸作品对象 | 30（对象自身） |
| [`user_show`](#用户资料三条路由) | `GET` | `/users/{username}.json` | 裸用户对象 | 70（对象自身） |
| [`user_quick`](#用户资料三条路由) | `GET` | `/users/{username}/quick.json` | 裸用户对象 | 59（对象自身） |
| [`user_profile`](#用户资料三条路由) | `GET` | `/api/v2/user_profiles/{username}.json` | 裸用户对象 | 63（对象自身） |
| [`user_projects`](#user_projects) | `GET` | `/users/{username}/projects.json` | `{"data": […], "total_count": N}` | 19 |
| [`user_following`](#user_following) | `GET` | `/users/{username}/following.json` | `{"data": […], "total_count": N}` | 30 |
| [`project_search`](#project_search) | `GET` | `/api/v2/search/projects.json` | `{"data": […], "total_count": N}` | 9 |
| [`search_filter_fields`](#search_filter_fields) | `GET` | `/api/v2/search/projects/filter_fields.json` | 裸数组 | 12 项（每项 2 键，`select_multiple` 3 键） |
| [`album_projects`](#album_projects) | `GET` | `/api/v2/community/projects/by_album.json` | `{"data": […], "total_count": N}` | 13 |
| [`channel_list`](#channel_list) | `GET` | `/api/v2/community/channels/channels.json` | `{"data": […], "total_count": N}` | 24 |
| [`channel_projects`](#channel_projects) | `GET` | `/api/v2/community/channels/projects.json` | `{"data": […], "total_count": N}` | 10 |
| [`project_comments`](#project_comments) | `GET` | `/api/v2/community/projects/{project_id}/comments.json` | `{"data": […], "total_count": N}` | 本轮为空 |
| [`explore_latest`](#explore_latest) | `GET` | `/api/v2/community/explore/projects/latest.json` | `{"data": […]}`（**没有** `total_count`） | 10 |
| [`feed`](#feedrss-订阅源) | `GET` | `/artwork.rss` | **XML 文本**（字符串） | RSS 2.0，50 个 `<item>` |
| [`csrf_token`](#匿名-csrf-令牌与只读搜索-post) | `POST` | `/api/v2/csrf_protection/token.json` | 裸对象（唯一键 `public_csrf_token`，str，本轮 88 字符） | 1 |
| [`project_search_post`](#匿名-csrf-令牌与只读搜索-post) | `POST` | `/api/v2/search/projects.json` | `{"data": […], "total_count": N}` | 11（搜索 9 键 + `assets` + `description`） |

另有通用入口 [`request()`](#通用入口-request)，用于调用17个原生方法之外的路径或动词。

## 依据标注与阅读方式

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **L** | 本轮 37 次完整直接 HTTP 观察，另引用前期缺 per_page 的匿名 400；随后脚本另计 | 路由的状态码、Content-Type、形状、字段与部分边界；**不等于每个 Python 方法都执行过** |
| **P** | 另一组匿名 `POST` 样本（CSRF 令牌与只读搜索；同样串行、不下载媒体） | 只有这两条 `POST` 的状态码、Content-Type、外层与字段；**账户写操作、令牌续期与其它 `POST` 不在其中** |
| **未实测** | 候选输入资料声称、本轮没有请求或没有复现 | 参数缺省值、枚举全集、上限、账号认证成功路径、账户写入、媒体规则；**不作为契约** |

* **本轮没有取到官方契约文本**：官方契约文本指站点发布的接口规范文档。`/openapi.json` 返回的是站点自己的 `200 text/html` 兜底页，不是 OpenAPI 文档，也没有可读到的官方 API 文档页或服务端源码。这只说明**本轮的依据只有匿名响应**，不构成"站点没有其它接口或文档"的结论。
* **未知路径不一定 404**：`/openapi.json` 与一条随便编的路径本轮都返回 `200 text/html` 兜底页，所以"某个路径返回 200"**不能**当作该路由存在的证据。
* 本文不写"全站不可用""没有详情接口"这类整站结论：被挑战或要登录的只是本轮请求过的那几条路径。

## 通用约定

* **基地址**：`https://www.artstation.com`，来自包内配置 `sites.artstation.url`。原生方法的路径都拼在它后面；路径可以带前导 `/`，客户端先去掉它再拼接。
* **方法**：15 个原生方法发 `GET`（查询参数放查询串），2 个 `POST` 发 JSON 正文或表单正文（见[匿名 CSRF 令牌与只读搜索 POST](#匿名-csrf-令牌与只读搜索-post)）。只有用户名与评论所属的作品编号各作为一个路径段（见下一条），`album_id` / `channel_id` 仍是查询参数。
* **认证**：`sites.artstation` 只有一个 `url` 字段，构造函数**没有凭据参数**，共享传输层的 `username` 传空串。15 条 GET 路由本轮全部匿名拿到响应，客户端不自动生成认证头，也不做登录。POST 搜索显式使用 `PUBLIC-CSRF-TOKEN` 头，它的值由调用方传参（客户端既不去取、也不缓存、不续期），见[匿名 CSRF 令牌与只读搜索 POST](#匿名-csrf-令牌与只读搜索-post)。401/403 的样本见[固定作品详情路径](#固定作品详情路径403401与没有-project_show)。
* **参数编码**：`params`（查询串）与 `form`（表单正文）都走共享的 Rails 风格编码——Rails 是 Ruby 的 Web 框架，它规定 `None` 值不发送、布尔写成小写 `true`/`false`、嵌套字典写成 `key[child]`、序列写成重复的 `key[]` 键。库**不做本地校验、不钳位、不补默认值、不猜上限**；没写进下面参数表的参数名也会原样进查询串或正文，站点拒绝什么就报什么。`data` 是 JSON 正文，不走这套编码。
* **路径标识符**：只有**用户名**（三条用户资料、用户作品、关注）与**评论所属作品编号**是路径段，按 `quote(str(value), safe='')` 逐段编码后拼进路径；库不校验合法性，服务端怎么回就怎么抛。`album_id` 与 `channel_id` 不是路径段，它们是**查询参数**（`album_projects` / `channel_projects` 内部把它们并进 `params` 一起走查询编码）。
* **返回**：JSON 原样返回，**不拆外层、不改字段名、不转换类型**。`response_format='json'`（16 个 JSON 方法固定用它：14 个 GET 加 2 个 POST）走共享 JSON 通路解析；`'xml'` / `'html'` 只把 `response.text` 原样给你（`feed()` 用 `'xml'`）；其它取值直接抛 `KeyError`，**客户端不看 Content-Type 嗅探格式**（不根据服务器声明猜响应体）。在 JSON 通路中，2xx 空正文返回 `None`，2xx 非空但不是 JSON 则抛 `AnybooruAPIError`；文本通路仍返回字符串。
* **错误**：非 2xx 抛 `AnybooruHTTPError`，带 `http_code` / `url` / `body` / `data` 与 `response`；正文是合法 JSON 时 `data` 是解析结果，正文为空或不是 JSON 时 `data` 为 `None`。库**不重试、不降级、不自动换路、不把错误正文补成正常结构**。
* **`last_call`**：保留 `API`（去前导斜杠的路由）、`url`、`status_code`、`status`、`headers`。
* **媒体**：`cover` 的 `*_url`、`assets[].image_url`、搜索结果的 `smaller_square_cover_url` 都只是**原样字符串**；本库不请求、不拼接、不改写、不删掉 URL 问号后面的缓存戳，也没有任何下载方法。

## 通用入口 request()

`request(method, path, *, params=None, data=None, form=None, headers=None, response_format='json')`

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串，如 `'GET'` / `'POST'` | 必填（Python 报缺参） | `client.request('GET', '/projects.json')` |
| `path` | 站点相对路径；前导 `/` 会被去掉后拼在站点根后 | 必填 | `client.request('GET', '/api/v2/community/channels/channels.json')` |
| `params` | 查询参数字典，经共享编码后拼进查询串 | `None`，不发查询参数 | `client.request('GET', '/projects.json', params={'page': 1, 'per_page': 1})` |
| `data` | JSON 正文，原样作为 requests 的 `json` 发送 | `None`，不发 JSON 正文 | `client.request('POST', '/api/v2/csrf_protection/token.json', data={'create_csrf_token_request': 'true'})` |
| `form` | 表单正文：经共享的 `encode_params` 编码后作为请求体发送（Rails 风格，序列写成重复 `key[]`） | `None`，不发表单正文 | `client.request('POST', '/api/v2/search/projects.json', form={'query': 'cat', 'page': 1, 'per_page': 3})` |
| `headers` | 本次请求的额外请求头字典，原样发送 | `None`，只带客户端默认头 | `client.request('POST', '/api/v2/search/projects.json', headers={'PUBLIC-CSRF-TOKEN': '…'})` |
| `response_format` | `'json'`（默认）、`'xml'`、`'html'`；后两者返回 `response.text` 原文 | `'json'` | `client.request('GET', '/artwork.rss', response_format='xml')` |

`form` 与 `data` 是**两条不同的正文通路**，调用方按方法选一条：`csrf_token()` 用 `data`（JSON），`project_search_post()` 用 `form`（表单）。两者都不传时不发正文；客户端不校验正文形状、不互相兜底。

`last_call['API']` 是去掉前导 `/` 后的路径原文（`'projects.json'`、`'artwork.rss'` …）。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    page = client.request('GET', '/api/v2/community/explore/projects/latest.json',
                          params={'page': 1, 'per_page': 10})
    # GET https://www.artstation.com/api/v2/community/explore/projects/latest.json?page=1&per_page=10
    # L：200，{"data": [… 10 个作品 …]}——这条路由没有 total_count
    print(client.last_call['API'], len(page['data']))

    rss = client.request('GET', '/artwork.rss', params={'sorting': 'latest'},
                         response_format='xml')
    # GET https://www.artstation.com/artwork.rss?sorting=latest
    # L：200 application/rss+xml; charset=utf-8 -> 字符串，<?xml …?> 开头
    print(type(rss).__name__, rss[:38])
```

## 全站作品流 project_list

`project_list(**params)`。路由：`GET /projects.json`。返回全站最新作品的分页列表，`total_count` 是全站作品总数。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `int` 页码，本轮取过 `1`；`999999` 是 `400` | 第几页 | **未实测**（本轮没有不传参数的样本） | `client.project_list(page=1, per_page=1)` |
| `per_page` | `int`，1、2、50 有成功样本；51 是 400，上限观察为50 | 每页条数 | **未实测** | `client.project_list(page=1, per_page=50)` |

外层是 `{"data": [...], "total_count": N}`；`total_count` 是全站作品数（本轮 `14522955`），`data` 是这一页的作品。每个作品项 **21 个键**：

| 键 | 观测类型 | 含义 / 本轮样本 |
| :--- | :--- | :--- |
| `id` | int | 作品数字编号，`22900098` |
| `hash_id` | str | 作品短码，`1LxzVq`；`permalink` 与固定详情路径都用它 |
| `user_id` | int | 作者数字编号，`41` |
| `title` | str | 标题，`"Field Journal"` |
| `description` | str | 作品说明（可能很长，含换行） |
| `created_at` / `updated_at` / `published_at` | str | ISO 8601 带时区，如 `"2026-09-20T01:35:15.014-05:00"` |
| `views_count` | int | 浏览量，`222`（**用户作品列表没有这个键**） |
| `likes_count` | int | 点赞数，`63` |
| `adult_content` | bool | 作品是否被标记为成人内容 |
| `admin_adult_content` | bool | 站方成人标记，与上者独立 |
| `hide_as_adult` | bool | 是否在成人过滤下隐藏 |
| `cover_asset_id` | int | 封面资产编号，`102562779` |
| `tag_list` | `null` 或数组 | 本轮样本是 `null`；**非 null 的元素形态未实测** |
| `permalink` | str | 作品页地址，`"https://www.artstation.com/artwork/1LxzVq"` |
| `user` | dict | 作者卡片，21 键：`id`、`username`、`first_name`、`last_name`、`headline`、`avatar_file_name`、`subdomain`、`city`、`country`、`pro_member`、`availability`、`is_staff`、`is_plus_member`、`is_studio_account`、`is_school_account`、`medium_avatar_url`、`large_avatar_url`、`full_name`、`permalink`、`artstation_profile_url`、`location` |
| `cover` | dict | 封面 4 键：`id`、`small_square_url`、`micro_square_image_url`、`thumb_url` |
| `icons` | dict | 6 个布尔：`image`、`video`、`video_clip`、`model3d`、`marmoset`、`pano`（**没有** `multiple_images`） |
| `assets_count` | int | 作品内资产数，`8` |

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    first = client.project_list(page=1, per_page=1)
    # GET https://www.artstation.com/projects.json?page=1&per_page=1
    # L：200 application/json; charset=utf-8
    #    {"data": [ …1 项… ], "total_count": 14522955}
    project = first['data'][0]
    print(first['total_count'])
    print(project['id'], project['hash_id'], project['title'], project['assets_count'])
    # 22900098 1LxzVq Field Journal 8
    print(project['permalink'], project['cover']['small_square_url'])
    print(project['user']['username'], project['user']['full_name'])
```

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    page = client.project_list(page=1, per_page=50)
    # GET https://www.artstation.com/projects.json?page=1&per_page=50
    # L：200，data 正好 50 项，total_count 与上面同值（同一时刻读数）
    print(len(page['data']), [item['id'] for item in page['data'][:3]])
```

`per_page=51` 与 `page=999999&per_page=1` 都是 **`400 text/plain; charset=utf-8`、正文为空字符串**——站点不解释原因，客户端也不猜，照原样抛 `AnybooruHTTPError`（`error.body == ''`）。

```python
from anybooru import AnybooruHTTPError, ArtStation

with ArtStation('artstation') as client:
    try:
        client.project_list(page=1, per_page=51)
        # GET https://www.artstation.com/projects.json?page=1&per_page=51
    except AnybooruHTTPError as error:
        # L：400 text/plain; charset=utf-8，error.body == ''，error.data 为 None
        print(error.http_code, repr(error.body), error.data)
```

## 随机作品 project_random

`project_random()`。路由：`GET /random_project.json`。**不收任何参数**。返回**裸作品对象**（没有 `data` 外层），比列表项详细得多，本轮样本 **30 个键**。

| 键 | 观测类型 | 含义 / 本轮样本 |
| :--- | :--- | :--- |
| `id` / `hash_id` / `slug` | int / str / str | `3260777`、`"OnxxK"`、`"red-short-hair-and-two-swords"` |
| `permalink` / `shortlink` | str | `"https://www.artstation.com/artwork/OnxxK"`、`"https://artstn.co/p/OnxxK"` |
| `title` / `description` | str | 标题、说明 |
| `user_id` | int | 作者编号，`28863` |
| `views_count` / `likes_count` / `comments_count` | int | `39675` / `1655` / `7` |
| `created_at` / `updated_at` / `published_at` | str | ISO 8601 带时区 |
| `adult_content` / `hide_as_adult` / `liked` | bool | 本轮都是 `false` |
| `editor_pick` / `is_promotional` | bool | `true` / `false` |
| `medium` / `mediums` | dict / 数组 | `{"name": "Digital 2D"}` / `[{"name": "Digital 2D", "id": 1}]` |
| `categories` | 数组 | `[{"name": "Concept Art"}, {"name": "Illustration"}, {"name": "Character Design"}]`（元素只有 `name`） |
| `software_items` | 数组 | `[{"icon_url": …, "id": 32, "name": "Photoshop"}]` |
| `tags` | 数组 | 本轮样本是空数组 `[]`；**元素形态未实测** |
| `collection_ids` | 数组 | 本轮样本是 `[]` |
| `visibilities` | 数组 | `["artstation", "website"]` |
| `cover_url` | str | 单张封面地址（与 `cover` 字典里的不同尺寸并列） |
| `cover` | dict | 11 键：`id`、`thumb_url`、`medium_image_url`、`large_image_url`、`micro_square_image_url`、`smaller_square_image_url`、`small_square_image_url`、`crop_x`、`crop_y`、`crop_w`、`crop_h` |
| `user` | dict | 12 键：`followed`、`followees_count`、`followers_count`、`full_name`、`headline`、`id`、`is_plus_member`、`large_avatar_url`、`medium_avatar_url`、`permalink`、`pro_member`、`username` |
| `assets` | 数组 | 作品内资产，本轮 2 项、每项 21 键（见下） |

`assets[]` 每项的 21 个键：`id`、`title`、`asset_type`（本轮 `"image"`）、`image_url`、`small_image_url`、`original_url`（本轮 `null`）、`width`、`height`、`position`、`is_image`、`is_video`、`is_model_3d`、`has_image`、`has_embedded_player`、`player_embedded`、`oembed`、`viewport_constraint_type`、`crop_x`、`crop_y`、`crop_w`、`crop_h`。本轮样本：`id=11299788`、`image_url` 指到 `https://cdna.artstation.com/p/assets/images/images/011/299/788/large/inhyuk-lee-.jpg?1528872924`、`width=1200`、`height=1724`、`original_url=null`。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    project = client.project_random()
    # GET https://www.artstation.com/random_project.json
    # L：200，裸对象 {"hide_as_adult": false, "adult_content": false, "assets": [ …2 项… ], …}
    print(project['id'], project['hash_id'], project['title'])
    # 3260777 OnxxK Red, Short hair and Two Swords
    print(project['user']['username'], project['likes_count'], project['views_count'])
    print([asset['asset_type'] for asset in project['assets']])
    print(len(project['tags']), project['medium']['name'])
```

随机接口本轮只取到一张，`tags` 又是空数组，所以**随机性、返回顺序、`tags` 元素形态都没有证据**；不要把它当"每次必定不同"或"`tags` 一定是数组"的依据。

## 用户资料（三条路由）

用户资料有三条独立路由，各给一份**不同的对象**；本轮串行取同一用户时，部分数值也不同。三条都不拆外层。

| 方法 | 路由 | 本轮对象键数 | 与另外两条的差异（都是本节样本） |
| :--- | :--- | :--- | :--- |
| `user_show(username)` | `/users/{username}.json` | 70 | 比 `user_quick` 多 14 个键：`badges`、`collections_count`、`community_projects_count`、`experience_items`、`first_name`、`has_public_email`、`last_name`、`portfolio`、`projects_count`、`show_all_projects_album`、`skills`、`social_profiles`、`software_items`、`user_productions`；比两者少 `is_artist`、`is_beta`、`has_recruiter_badge` |
| `user_quick(username)` | `/users/{username}/quick.json` | 59 | 比 `user_show` 少上面那 14 个键，多 `is_artist`、`is_beta`、`has_recruiter_badge` |
| `user_profile(username)` | `/api/v2/user_profiles/{username}.json` | 63 | 比 `user_show` 少 14 条社交主页 `*_url`，多 `artstation_website_url`、`freelance_profiles`、`subdomain`、`website_default_album`、`is_artist`、`is_beta`、`has_recruiter_badge` |

三条共有的字段（本轮都是这 42 个）：`albums_with_community_projects`、`artstation_subdomain_url`、`artstation_url`、`artstation_website`、`availability`、`available_full_time`、`available_contract`、`available_freelance`、`blocked`、`city`、`country`、`cover_file_name`、`cover_width` / `cover_height`、`default_cover_url`、`display_portfolio_as_albums`、`followed`、`followees_count`、`followers_count`、`following_back`、`full_name`、`has_pro_permissions` / `has_premium_permissions`、`headline`、`id`、`is_plus_member`、`is_staff`、`is_studio_account`、`is_school_account`、`large_avatar_url` / `medium_avatar_url`、`liked_projects_count`、`memorialized`、`permalink`、`portfolio_display_settings`、`portfolio_display_settings_albums`、`pro_member`、`profile_artstation_website` / `profile_artstation_website_url`、`profile_default_album`、`username`、`website_url`。`user_show` 与 `user_quick` **还都带**这 14 条社交主页字段：`behance_url`、`deviantart_url`、`facebook_url`、`imdb_url`、`instagram_url`、`linkedin_url`、`pinterest_url`、`sketchfab_url`、`steam_url`、`tumblr_url`、`twitch_url`、`twitter_url`、`vimeo_url`、`youtube_url`；`user_profile` **不**返回它们。

三条路由的差异在本轮样本里具体表现为：

| 字段 | `user_show` | `user_quick` | `user_profile` |
| :--- | :--- | :--- | :--- |
| `projects_count` | `40` | **没有这个键** | `40` |
| `community_projects_count` | `40` | **没有** | `40` |
| `collections_count` | `15` | **没有** | `2` |
| `followees_count` | `409` | `409` | `408` |
| `albums_with_community_projects[0].title` | `"All"` | `"All"` | `"All projects"` |
| `profile_default_album` | `{"id": 95733, "album_type": "all_projects"}` | 同左 | 同左 |

`albums_with_community_projects` 是本轮三条路由都有的一个数组，元素是本人在社区里的相册：`id`（`95733`）、`title`、`user_id`、`created_at` / `updated_at`、`position`（`-1`）、`community_projects_count`、`total_projects`、`website_projects_count`、`public_projects_count`、`profile_visibility`、`website_visibility`、`album_type`（`"all_projects"`）。候选输入把 `albums_with_community_projects[].id` 作为专辑编号来源；本轮 timwarnock 响应为 `95733`，专辑成功样本另选 `104104`。没有请求 `95733` 的专辑列表，不从两个样本编号不同推断它们是不同编号体系。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `username` | `str` 用户名（路径段，按 `quote(str(v), safe='')` 编码） | 要读的用户 | 必填（Python 报缺参） | `client.user_show('timwarnock')` |

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    user = client.user_show('timwarnock')
    # GET https://www.artstation.com/users/timwarnock.json
    # L：200，裸对象 70 键；id=1、username="timwarnock"、projects_count=40
    print(user['id'], user['username'], user['projects_count'], user['followers_count'])
    print(user['albums_with_community_projects'][0]['title'])
    print([skill['name'] for skill in user['skills']])

    quick = client.user_quick('timwarnock')
    # GET https://www.artstation.com/users/timwarnock/quick.json
    # L：200，裸对象 59 键；没有 projects_count，但 followers_count=4744 与前一条一致
    print('projects_count' in quick, quick['has_recruiter_badge'])

    profile = client.user_profile('timwarnock')
    # GET https://www.artstation.com/api/v2/user_profiles/timwarnock.json
    # L：200，裸对象 63 键；collections_count=2、albums_with_community_projects[0].title="All projects"
    print(profile['id'], profile['collections_count'],
          profile['albums_with_community_projects'][0]['title'])
```

不存在的用户名是 **`404 text/plain; charset=utf-8`、正文为空字符串**：

```python
from anybooru import AnybooruHTTPError, ArtStation

with ArtStation('artstation') as client:
    try:
        client.user_show('zzzz_no_such_user_99')
        # GET https://www.artstation.com/users/zzzz_no_such_user_99.json
    except AnybooruHTTPError as error:
        # L：404 text/plain; charset=utf-8，error.body == ''，error.data 为 None
        print(error.http_code, repr(error.body))
```

三条资料路由本轮只测过存在的用户与一个不存在的用户名，**其它用户名形态（大小写、URL 编码、带斜杠或空格）的编码行为都没有样本**。

## user_projects

`user_projects(username, **params)`。路由：`GET /users/{username}/projects.json`。返回该用户的社区作品分页列表（**全局列表与用户列表的条目键集不同**，见下）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `username` | `str` 用户名（路径段） | 要读的用户 | 必填 | `client.user_projects('timwarnock', page=1, per_page=2)` |
| `page` | `int` 页码，本轮取过 `1`、`2`、`9999` | 第几页 | **未实测** | 同上 |
| `per_page` | `int`，本轮取过 `2`；上下限未穷举 | 每页条数 | **未实测** | 同上 |
| `album_id` | 候选专辑编号，输入还列出字符串 `all`；均未实测 | 选择用户的专辑 | 未规定，未实测 | `client.user_projects('timwarnock', page=1, per_page=2, album_id=95733)`（未实测） |

外层 `{"data": [...], "total_count": N}`，本轮三个页码样本 `total_count=40`，不保证跨请求恒定。每个作品项 **19 个键**：与 [`project_list`](#全站作品流-project_list) 的 21 键相比，**少了 `user` 与 `views_count`**，其余键名与含义一致（`id`、`slug`、`user_id`、`title`、`description`、`created_at`、`updated_at`、`published_at`、`likes_count`、`adult_content`、`admin_adult_content`、`cover_asset_id`、`tag_list`、`hash_id`、`permalink`、`hide_as_adult`、`cover`、`icons`、`assets_count`）。`cover` 同样是 4 键，`icons` 同样是 6 键。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    page1 = client.user_projects('timwarnock', page=1, per_page=2)
    # GET https://www.artstation.com/users/timwarnock/projects.json?page=1&per_page=2
    # L：200，{"data": [ …2 项… ], "total_count": 40}
    page2 = client.user_projects('timwarnock', page=2, per_page=2)
    # GET https://www.artstation.com/users/timwarnock/projects.json?page=2&per_page=2
    # L：200，另外 2 项，total_count 仍是 40
    print([item['id'] for item in page1['data']])   # [17792515, 13201269]
    print([item['id'] for item in page2['data']])   # [13207332, 13201229]
    print('views_count' in page1['data'][0], 'user' in page1['data'][0])   # False False
```

**超深页不是错误**（与全局列表相反）：`page=9999&per_page=2` 返回 **`200 {"data": [], "total_count": 40}`**——空数组照常给你，页面越界由你按 `data` 是否为空判断。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    empty = client.user_projects('timwarnock', page=9999, per_page=2)
    # GET https://www.artstation.com/users/timwarnock/projects.json?page=9999&per_page=2
    # L：200，{"data": [], "total_count": 40}
    print(empty['data'], empty['total_count'])
```

## user_following

`user_following(username, **params)`。路由：`GET /users/{username}/following.json`。返回该用户关注的人（**用户卡片**，不是作品）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `username` | `str` 用户名（路径段） | 要读的用户 | 必填 | `client.user_following('timwarnock', page=1, per_page=2)` |
| `page` | `int` 页码，本轮取过 `1` | 第几页 | **未实测** | 同上 |
| `per_page` | `int`，本轮取过 `2`；上下限未穷举 | 每页条数 | **未实测** | 同上 |

外层 `{"data": [...], "total_count": N}`，本轮 `total_count=409`。每个用户卡片 **30 个键**：`id`、`username`、`headline`、`avatar_file_name`、`subdomain`、`city`、`country`、`available_full_time` / `available_contract` / `available_freelance`、`followers_count`、`pro_member`、`cover_file_name`、`availability`、`artist_role`、`followed`、`full_name`、`medium_avatar_url`、`large_avatar_url`、`is_staff`、`is_plus_member`、`is_studio_account`、`is_school_account`、`default_cover_url`、`location`、`sample_projects`、`skills`、`software_items`、`following_back`、`has_recruiter_badge`。注意卡片**没有** `projects_count`、没有 `permalink`、没有作品总数。

* `sample_projects` 是**缩略图地址字符串数组**（本轮 6 个 URL），不是作品对象。
* `skills` 是 `[{"name": "Character Design"}, …]`。
* `software_items` 是 `[{"name": "Photoshop", "icon_url": …}, …]`。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    following = client.user_following('timwarnock', page=1, per_page=2)
    # GET https://www.artstation.com/users/timwarnock/following.json?page=1&per_page=2
    # L：200，{"data": [ …2 张用户卡片… ], "total_count": 409}
    print(following['total_count'])
    for card in following['data']:
        print(card['id'], card['username'], card['followers_count'], len(card['sample_projects']))
        # 3669 eventrue 40541 6
        # 20302 ionic 47963 …
```

## project_search

`project_search(**params)`。路由：`GET /api/v2/search/projects.json`。站内搜索接口；返回 `{"data": [...], "total_count": N}`，每个结果项 **9 个键**（比其它列表项短很多，并且**没有** `slug` / `permalink`——作品地址在 `url` 里）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | `str` 关键词，本轮取过 `"cat"` 与 `""`（空串） | 搜索词 | **未实测**（本轮每次都给了，包括空串） | `client.project_search(query='cat', page=1, per_page=3, sorting='relevance')` |
| `page` | `int` ≥ 1；`0` 是 `400` | 第几页 | **缺它直接 `400 {"data": "page should be given"}`，站点不给默认页** | 同上 |
| `per_page` | `int`，实测区间 `3..75`；`2` 是 `400 {"message": "per_page should be >= 3", "code": "per_page"}`，`76` 是 `400 {"message": "per_page should be <= 75", "code": "per_page"}` | 每页条数 | **缺它直接 `400 {"data": "per_page should be given"}`** | 同上 |
| `sorting` | `str`，实测 `relevance`；候选 `likes/date/rank` 未测 | 排序方式，实际排序规则未核定 | 未规定；省略它的 75 条搜索样本为200 | `client.project_search(query='cat', page=1, per_page=3, sorting='relevance')` |
| `filters` | `str`：JSON 字符串，不是 Python 列表 | 结构化条件，见[筛选字符串](#筛选字符串filters-必须是-json-字符串) | 不带 filters 的 cat 搜索已有200；不推测隐式过滤规则 | `filters='[{"field":"title","method":"contain","value":"dragon"}]'` |
| `pro_first` | 候选字符串 `'1'` / `'0'`，未实测 | 输入称是否优先展示 Pro 会员作品 | 未规定，未实测 | `client.project_search(query='cat', page=1, per_page=3, pro_first='1')`（未实测） |
| `additional_fields` | 序列，候选值 assets/description；共享编码为重复 additional_fields[] | 请求补充字段；GET样本两值同传仍无这两字段 | 未传时已测搜索项没有 assets/description | `client.project_search(query='cat', page=1, per_page=3, additional_fields=['assets', 'description'])` |

结果项 9 键：`id`、`hash_id`、`url`（作品页地址，`"https://www.artstation.com/artwork/aY5nBq"`）、`smaller_square_cover_url`、`hide_as_adult`、`is_adult_content`、`title`、`icons`、`user`。其中 `icons` 是 **7 个布尔**（比 `project_list` 的 6 键多 `multiple_images`）；`user` 只有 9 键：`id`、`username`、`full_name`、`medium_avatar_url`、`is_staff`、`pro_member`、`is_plus_member`、`is_studio_account`、`is_school_account`（**没有** `first_name` / `city` / `location` 等）。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    result = client.project_search(query='cat', page=1, per_page=3, sorting='relevance')
    # GET https://www.artstation.com/api/v2/search/projects.json?query=cat&page=1&per_page=3&sorting=relevance
    # L：200，{"data": [ …3 项… ], "total_count": 118784}
    print(result['total_count'])
    for item in result['data']:
        print(item['id'], item['hash_id'], item['title'], item['user']['username'])
    # 10122141 aY5nBq Cat Cat Cat dajeong_park
    # 17985153 lDmGo5 YT ver.cat loull_aroll
    # 3049628  vGG46 Lion anatomy maryia_panfilova
```

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    wide = client.project_search(query='cat', page=1, per_page=75)
    # GET https://www.artstation.com/api/v2/search/projects.json?query=cat&page=1&per_page=75
    # L：200，data 正好 75 项（搜索的上限就是这个数）
    print(len(wide['data']))
```

分页示例：`page` 与 `per_page` 都必须显式给。下一行换 `page=2` 即可，其它参数不动。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    page2 = client.project_search(query='cat', page=2, per_page=3, sorting='relevance')
    # GET https://www.artstation.com/api/v2/search/projects.json?query=cat&page=2&per_page=3&sorting=relevance
    print([item['id'] for item in page2['data']])
```

搜索的两种错误外壳都要认（按 `http_code` 分支，别按文案或键名）：

```python
from anybooru import AnybooruHTTPError, ArtStation

with ArtStation('artstation') as client:
    try:
        client.project_search(query='cat', page=1, per_page=2)
        # GET https://www.artstation.com/api/v2/search/projects.json?query=cat&page=1&per_page=2
    except AnybooruHTTPError as error:
        # L：400 application/json，{"message": "per_page should be >= 3", "code": "per_page"}
        print(error.http_code, error.data['code'], error.data['message'])

    try:
        client.project_search(query='cat', per_page=3)
        # GET https://www.artstation.com/api/v2/search/projects.json?query=cat&per_page=3
    except AnybooruHTTPError as error:
        # L：400 application/json，{"data": "page should be given"}（data 里是字符串，没有 code/message）
        print(error.http_code, error.data)
```

## search_filter_fields

`search_filter_fields()`。路由：`GET /api/v2/search/projects/filter_fields.json`。**不收任何参数**，返回**裸数组**（没有 `data` 外层），本轮 **12 项**。每一项至少 `{"name": ..., "type": ...}`；`type` 是 `select_multiple` 的项**另有** `select_options` 数组（元素形如 `{"id": 35, "name": "Abstract"}` 或 `{"id": "pano", "name": "360 Panos"}`，**`id` 有时是数字、有时是字符串**）。

| `name` | `type` | `select_options` 本轮条数 |
| :--- | :--- | :--- |
| `title` | `text` | — |
| `artist_name` | `text` | — |
| `tags` | `tags` | — |
| `category_ids` | `select_multiple` | 59 |
| `asset_types` | `select_multiple` | 6（`360 Panos`、`Marmoset Viewer`、`Sketchfab`、`Twinmotion`、`Video`、`Video Clip`） |
| `medium_ids` | `select_multiple` | 11 |
| `medium_id` | `select_multiple` | 11 |
| `software_ids` | `select_multiple` | 410 |
| `comments_count` | `number` | — |
| `artist_followers_count` | `number` | — |
| `following` | `boolean` | — |
| `editor_pick` | `boolean` | — |

**不要假设每项都有 `select_options`**：`text` / `number` / `boolean` / `tags` 类型的项本轮只有 `name` 与 `type` 两个键。这份清单说的是"搜索接口认得哪些字段名与取值域"，**不等于**这些字段在 `filters` 里一定都生效；`filters` 的实际行为只测过下节那一组。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    fields = client.search_filter_fields()
    # GET https://www.artstation.com/api/v2/search/projects/filter_fields.json
    # L：200，裸数组 12 项，第一项 {"name": "title", "type": "text"}
    print(len(fields), [(f['name'], f['type']) for f in fields[:3]])
    asset_types = next(f for f in fields if f['name'] == 'asset_types')
    print([opt['id'] for opt in asset_types['select_options']])
```

## 匿名 CSRF 令牌与只读搜索 POST

15 个 GET 之外还有 2 个 POST。它们不写入作品或账号：一个向站点索取匿名 CSRF 令牌，另一个是同一搜索接口的 `POST` 形式、结果只读。改数据、改关系、改账号的请求本类一个都没有包装。

两条路由要**配成一对**用：先 `csrf_token()` 取令牌——响应会带会话 Cookie，共享的 requests 会话按常规自动保存它；再在**同一个 `ArtStation` 实例**上调用 `project_search_post(token, ...)`，客户端把令牌原样放进请求头 `PUBLIC-CSRF-TOKEN`。客户端**不会**自己去取令牌、不会缓存、不会续期、不会重试、不会伪造 Cookie，也不会替你调用搜索——两步都由调用方显式发起。

### csrf_token

`csrf_token(**attributes)`。路由：`POST /api/v2/csrf_protection/token.json`。正文是 **JSON**：`attributes` 原样作为 JSON 对象发送（内部走 `request(..., data=attributes)`）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `create_csrf_token_request` | 字符串 `'true'` | 让站点生成一个公开 CSRF 令牌；本轮只用过这一个键 | 不传就不发这个键；省略时是否仍发令牌**未实测** | `client.csrf_token(create_csrf_token_request='true')` |

**返回**：`200 application/json; charset=utf-8`，**裸对象，本轮只有唯一一个键**：`public_csrf_token`（str，本轮 88 字符，值不复述；有效期与可复用次数未测）。令牌响应同时下发 `Set-Cookie`（本轮记录到的 Cookie 名字是 `PRIVATE-CSRF-TOKEN` 与 Cloudflare 的 `__cf_bm`），由共享 requests 会话按常规保存。客户端**不把令牌存成实例属性**、不写磁盘、不重试：它只出现在这次调用的返回值里，要留着自己留。

### project_search_post

`project_search_post(public_csrf_token, **params)`。路由：`POST /api/v2/search/projects.json`。正文是**表单**（`application/x-www-form-urlencoded`，`params` 经共享 `encode_params` 编码后走 `request(..., form=params)`）；请求头 `PUBLIC-CSRF-TOKEN` 的值就是第一个参数 `public_csrf_token` 的**原值**（不由客户端生成、修改或补齐）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `public_csrf_token` | `str`，`csrf_token()` 响应里的 `public_csrf_token` 原值 | 放进 `PUBLIC-CSRF-TOKEN` 请求头的令牌；**必填位置参数**，且要与取令牌时**同一个 `ArtStation` 实例**（Cookie 配对） | Python 报缺参 | `client.project_search_post(token, query='cat', page=1, per_page=3, sorting='relevance')` |
| `query` | `str` 关键词，与 GET 搜索同名 | 搜索词 | 未实测 | 同上 |
| `page` | `int`，本轮1成功；其它边界未测 | 第几页 | 未实测 | 同上 |
| `per_page` | `int`，本轮3成功；POST上下限未测，不沿用GET的3..75结论 | 每页条数 | 未实测 | 同上 |
| `sorting` | `str`，本轮只跑过 `'relevance'` | 排序方式 | 未实测 | 同上 |
| `pro_first` | 候选（GET 侧未测） | 输入称是否优先展示 Pro 会员作品 | 未规定，未实测 | `client.project_search_post(token, query='cat', page=1, per_page=3, pro_first='1')`（未实测） |
| `filters` | 候选对象数组，form编码为filters[][field/method/value]，本轮POST未实测 | 结构化条件 | 未规定，未实测 | `filters=[{'field':'title','method':'contain','value':'dragon'}]`（未实测） |
| `additional_fields` | 序列，本轮用 `['assets', 'description']` | 让结果项追加这两个字段 | POST 不传它的样本**未测**；GET 搜索不带它时结果项是 9 键 | `client.project_search_post(token, query='cat', page=1, per_page=3, sorting='relevance', additional_fields=['assets', 'description'])` |

**返回**：`200 application/json; charset=utf-8`，外层与 GET 搜索**同形**：`{"total_count": N, "data": [...]}`（本轮样本 `total_count` 为 `118783`）。带 `additional_fields=['assets', 'description']` 时每个结果项是 **11 个键**：GET 搜索的 9 键（`id`、`hash_id`、`url`、`smaller_square_cover_url`、`hide_as_adult`、`is_adult_content`、`title`、`icons`、`user`）再加这两个字段——

* `description`：**字符串**（本轮样本是带 `<p>` 的 HTML 片段，不是纯文本）。
* `assets`：数组；图片资产样本有 11 键：`id`/`title`/`asset_type`/`width`/`height`/`position`/`viewport_constraint_type`/`small_image_url`/`large_image_url`/`has_image`/`has_embedded_player`。video/video_clip 项另有 `player_embedded`/`oembed`，不能把 11 键当所有类型的全集。三个结果分别有 6/11/17 个资产；地址只是字符串，本库不下载。

本轮命中的三个作品编号与同名 GET 搜索一致（`10122141`、`17985153`、`3049628`）。**不带 `additional_fields` 的 POST 样本未测**；GET 搜索不带它时结果项是 9 键（见 [project_search](#project_search) 的字段表），`additional_fields` 的**其它取值**也没有样本。

### 两步调用（同一个客户端）

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    token_body = client.csrf_token(create_csrf_token_request='true')
    # POST https://www.artstation.com/api/v2/csrf_protection/token.json
    # 请求 Content-Type application/json，正文 {"create_csrf_token_request": "true"}
    # P：200 application/json; charset=utf-8，{"public_csrf_token":"<公开token>"}（样本88字符）
    token = token_body['public_csrf_token']

    result = client.project_search_post(
        token, query='cat', page=1, per_page=3, sorting='relevance',
        additional_fields=['assets', 'description'])
    # POST https://www.artstation.com/api/v2/search/projects.json
    # 请求 Content-Type application/x-www-form-urlencoded，正文
    #   query=cat&page=1&per_page=3&sorting=relevance&additional_fields%5B%5D=assets&additional_fields%5B%5D=description
    # 请求头 PUBLIC-CSRF-TOKEN 就是上面 token 的原值；同一个实例，会话 Cookie 来自上一步
    # P：200 application/json; charset=utf-8，{"total_count": 118783, "data": [ …3 项… ]}
    print(result['total_count'])
    for item in result['data']:
        print(item['id'], item['title'], len(item['assets']), len(item['description']))
        # 10122141 Cat Cat Cat 6 89
        # 17985153 YT ver.cat 11 …
        # 3049628  Lion anatomy 17 …
    print(result['data'][0]['assets'][0]['asset_type'],
          result['data'][0]['assets'][0]['large_image_url'])
```

`additional_fields` 只对**选定的搜索结果**追加字段，不是"按编号取任意作品"的通用入口：相册（`album_projects`）与随机（`project_random`）本来就有各自的 `assets`；这条 `POST` 给的是搜索命中的作品外加 `assets` / `description`，**不是唯一的资产入口**。

## album_projects

`album_projects(album_id, **params)`。路由：`GET /api/v2/community/projects/by_album.json`。方法把 `album_id` 作为查询参数拼进去（不是路径段），返回该相册里的作品。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `album_id` | `int` 相册编号；本轮样本 `104104` | 要读的相册 | 必填（Python 报缺参） | `client.album_projects(104104, page=1, per_page=4)` |
| `page` | `int` 页码，本轮取过 `1` | 第几页 | **未实测** | 同上 |
| `per_page` | `int`，实测下限 `4`（`3` 是 `400 {"message": "per_page should be >= 4", "code": "per_page"}`）；上限未穷举 | 每页条数 | **未实测** | 同上 |

外层 `{"data": [...], "total_count": N}`，本轮 `total_count=49`。每个作品项 **13 个键**，与其它列表不同——它**自带 `assets` 数组**，并且多出相册自己的字段：`album_id`（`104104`）、`album_title`（`"All projects"`）、`position`（负数，样本 `-56` / `-33` / `-30` / `-27`）。其它键：`id`、`slug`、`created_at`、`updated_at`、`hash_id`、`title`、`description`、`permalink`、`cover`、`assets`。注意这些项**没有** `user`、`views_count`、`likes_count`、`adult_content`、`icons`。

`assets[]` 每项本轮是 8 键：`id`、`asset_type`、`width`、`height`、`title`、`has_embedded_player`、`small_image_url`、`large_image_url`。**这与 `project_random()` 的 21 键资产不同**（少了 `original_url` / `is_image` / `crop_*` / `oembed` 等）；`cover` 也不同（7 键，含 `small_image_url` / `medium_image_url` / `large_image_url` / `small_square_image_url` / `smaller_square_image_url` / `micro_square_image_url`）。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    album = client.album_projects(104104, page=1, per_page=4)
    # GET https://www.artstation.com/api/v2/community/projects/by_album.json?album_id=104104&page=1&per_page=4
    # L：200，{"data": [ …4 项… ], "total_count": 49}
    print(album['total_count'])
    for item in album['data']:
        print(item['id'], item['hash_id'], item['title'], item['album_title'], item['position'])
        # 21341650 XJLVv0 North African Witch All projects -56
    first = album['data'][0]
    print(first['assets'][0]['asset_type'], first['assets'][0]['width'], first['assets'][0]['large_image_url'])
```

`album_id` 与用户资料里的 `albums_with_community_projects[].id`（如 `95733`）**不是同一套编号**：本轮相册路由用的是 `104104`，而 `95733` 只出现在用户对象里，两者没有互相验证过。

## channel_list

`channel_list()`。路由：`GET /api/v2/community/channels/channels.json`。**不收任何参数**。返回 `{"data": [...], "total_count": N}`，本轮 `total_count` 与 `data` 条数都是 64。这条路由没有公开的分页参数，本轮也没有分页样本，所以**不能断言 64 就是全部频道**。

每个频道项 **24 个键**：`id`、`name`、`image_url`、`uri`（短名，如 `"abstract"`）、`state`（`"published"`）、`featured`、`type`（`"global"`）、`icon_image_url`、`is_ad`、`advertiser`、`advertisement_paid_by`、`block_image_url`、`promo_text`、`promo_link`、`intro_link`、`logo_image_url`、`bg_image_url`、`artworks_only`、`intro_button`、`intro_title`、`show_intro`、`show_logo_on_intro`、`intro_content_position`、`learning_sources`（本轮是 `{}`）。频道编号与短名都能当 `channel_projects()` 的 `channel_id` 吗？**没有测过短名**：本轮只用了数字 `70`。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    channels = client.channel_list()
    # GET https://www.artstation.com/api/v2/community/channels/channels.json
    # L：200，{"data": [ …64 项… ], "total_count": 64}
    print(len(channels['data']), channels['data'][0]['id'], channels['data'][0]['name'])
    # 64 70 Abstract
    print([(c['id'], c['name']) for c in channels['data'][:3]])
```

## channel_projects

`channel_projects(channel_id, **params)`。路由：`GET /api/v2/community/channels/projects.json`。方法把 `channel_id` 作为查询参数拼进去，返回频道里的作品。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `channel_id` | `int` 频道编号；本轮样本 `70`（`channel_list()` 里的 `id`） | 要读的频道 | 必填（Python 报缺参） | `client.channel_projects(70, page=1, per_page=5)` |
| `page` | `int` 页码，本轮取过 `1` | 第几页 | **未实测** | 同上 |
| `per_page` | `int`，本轮取过 `5`；上下限未穷举 | 每页条数 | **未实测** | 同上 |
| `sorting` | `str`（候选参数） | 排序方式 | **未实测**（一次都没测过） | `client.channel_projects(70, page=1, per_page=5, sorting='latest')`（未实测） |
| `dimension` | 字符串或数值（候选参数） | 维度筛选 | **未实测** | `client.channel_projects(70, page=1, per_page=5, dimension='2d')`（未实测） |

外层 `{"data": [...], "total_count": N}`，本轮 `total_count=10000`（只出现一次，不能判断是不是站点上限）。每个作品项 **10 个键**：与 [搜索结果](#project_search) 的 9 键相比，**少了 `is_adult_content`**，**多了 `is_highlighted` 与 `small_square_cover_url`**；`icons` 同样含 `multiple_images`，而样本 `user` 比搜索卡片多 `has_recruiter_badge`，共 10 键。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    projects = client.channel_projects(70, page=1, per_page=5)
    # GET https://www.artstation.com/api/v2/community/channels/projects.json?channel_id=70&page=1&per_page=5
    # L：200，{"data": [ …5 项… ], "total_count": 10000}
    for item in projects['data']:
        print(item['id'], item['hash_id'], item['title'], item['is_highlighted'])
        # 22900098 1LxzVq Field Journal False
```

## project_comments

`project_comments(project_id, **params)`。路由：`GET /api/v2/community/projects/{project_id}/comments.json`（编号是**路径段**，要用数字作品 `id`，不是 `hash_id`）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `project_id` | `int` 数字作品编号，本轮 `22897630` | 评论所属作品 | 必填（Python 报缺参） | `client.project_comments(22897630)` |
| `page` | `int` 页码（候选参数） | 第几页 | **未实测**（一次都没测过） | `client.project_comments(22897630, page=1)`（未实测） |
| `per_page` | `int` 条数（候选参数） | 每页条数 | **未实测** | `client.project_comments(22897630, per_page=10)`（未实测） |

外层是 `{"data": [...], "total_count": N}`；本轮那个作品**没有评论**，返回 `{"total_count": 0, "data": []}`。**非空评论对象的结构本轮没有样本**，所以本文不写评论字段名，也不推断 `data` 元素的键。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    comments = client.project_comments(22897630)
    # GET https://www.artstation.com/api/v2/community/projects/22897630/comments.json
    # L：200，{"total_count": 0, "data": []}
    print(comments['total_count'], comments['data'])
```

## explore_latest

`explore_latest(**params)`。路由：`GET /api/v2/community/explore/projects/latest.json`。站点"探索"页的最新作品流。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `int` 页码，本轮取过 `1` | 第几页 | **未实测** | `client.explore_latest(page=1, per_page=10)` |
| `per_page` | `int`，实测下限 `10`（`9` 是 `400 {"message": "per_page should be >= 10", "code": "per_page"}`）；上限未穷举 | 每页条数 | **未实测** | 同上 |

**这条路由的外层只有 `{"data": [...]}`，没有 `total_count`**（本轮确认）。每个作品项 **10 个键**，与 [`channel_projects`](#channel_projects) 完全相同：`id`、`hash_id`、`url`、`smaller_square_cover_url`、`hide_as_adult`、`title`、`is_highlighted`、`small_square_cover_url`、`icons`、`user`。判断有没有下一页只能用 `len(data)` 是否为 0（或是否小于你请求的 `per_page`），别去取 `total_count`。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    latest = client.explore_latest(page=1, per_page=10)
    # GET https://www.artstation.com/api/v2/community/explore/projects/latest.json?page=1&per_page=10
    # L：200，{"data": [ …10 项… ]}——没有 total_count
    print('total_count' in latest, len(latest['data']))
    for item in latest['data'][:3]:
        print(item['id'], item['hash_id'], item['title'])
        # 22900842 Aol8Ae Lauda acrylic portrait
```

## feed()：RSS 订阅源

`feed(**params)`。路由：`GET /artwork.rss`。**返回字符串**（RSS 原文），`response_format` 在方法内部固定为 `'xml'`，走 `.text`，不解析、不嗅探。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `sorting` | `str`；本轮只跑过 `'latest'` | 订阅源排序 | **未实测**；其它取值**没有证据** | `client.feed(sorting='latest')` |

响应 `200 application/rss+xml; charset=utf-8`。本轮正文是 RSS 2.0：根 `<rss version="2.0">`，带 `atom` 与 `content` 两个命名空间；`<channel>` 里有 `<title>ArtStation - Latest Artwork</title>`、`<description>Showcase. Discover. Connect.</description>`、`<link>https://www.artstation.com/</link>`、`<language>en-us</language>` 与一个 `<atom:link rel="self" … href="https://www.artstation.com/artwork.rss"/>`（**self 链接里没有 `sorting` 参数**，即使请求带了 `?sorting=latest`）。本轮共 **50 个 `<item>`**。每个 `<item>` 的子元素顺序与内容：`<title>`（`Lauda acrylic portrait by Firmin "Fiire" DESPREZ`）、`<description>`（CDATA 纯文本说明）、`<content:encoded>`（CDATA 里是带 `<p>` / `<a>` / `<img>` 的 HTML，图片地址指向 `cdn*.artstation.com`）、`<pubDate>`（RFC 822，如 `Sun, 20 Sep 2026 05:56:51 -0500`）、`<link>`、`<guid>`（与 `<link>` 同值，就是作品页地址）。CDATA 是 XML 里的一段"原文照录"区域，里面的尖括号不当标记解析；RFC 822 是一种老式邮件/新闻组日期格式。

```python
import xml.etree.ElementTree as ElementTree

from anybooru import ArtStation

with ArtStation('artstation') as client:
    rss = client.feed(sorting='latest')
    # GET https://www.artstation.com/artwork.rss?sorting=latest
    # L：200 application/rss+xml; charset=utf-8 -> 字符串，以 <?xml version="1.0" encoding="UTF-8"?> 开头
    print(type(rss).__name__, rss[:38])
    root = ElementTree.fromstring(rss)          # 解析发生在调用方一侧
    channel = root.find('channel')
    items = channel.findall('item')
    print(channel.find('title').text, len(items))     # ArtStation - Latest Artwork 50
    first = items[0]
    print(first.find('title').text)
    print(first.find('guid').text, first.find('pubDate').text)
```

**返回的是原文**：客户端不做 XML 解析、不剥 CDATA、不去空白、不把 `<item>` 转成 dict，也不把 RSS 当作 `artwork.rss` 之外的任何格式。`sorting` 本轮只验证过 `latest`。

## 外壳与字段差异（同一站点，多条路线）

站点每条路由给的外层不同，**客户端一层都不拆**；下表是你真正拿到的形状：

| 外层 | 哪些方法 | 取数据的方式 |
| :--- | :--- | :--- |
| `{"data": [...], "total_count": N}` | `project_list`、`user_projects`、`user_following`、`project_search`、`album_projects`、`channel_list`、`channel_projects`、`project_comments` | `body['data']` 是列表，`body['total_count']` 是那次请求的计数 |
| `{"data": [...]}` | `explore_latest` | **没有 `total_count`**，只能数 `len(body['data'])` |
| 裸作品对象 | `project_random` | 直接 `body['id']` / `body['assets']`，没有 `data` 键 |
| 裸用户对象 | `user_show`、`user_quick`、`user_profile` | 直接 `body['id']`，三份对象键集不同（70 / 59 / 63） |
| 裸数组 | `search_filter_fields` | `body` 就是 12 项字段清单 |
| `{"data": [...], "total_count": N}`（与 GET 搜索同形） | `project_search_post` | 同上；带 `additional_fields` 时每个结果项会加宽 |
| 裸对象（本轮仅 `public_csrf_token`） | `csrf_token` | 返回公开 token 字符串；有效期与复用次数未测 |
| XML 字符串 | `feed` | `body` 是 RSS 原文，要自己解析 |

上表的 `{"data": …, "total_count": …}` 里**两个键的先后顺序只是样本细节**：站点有的路由先给 `data`、有的先给 `total_count`，按字典键取值即可，不要依赖顺序，也不要假定只有这两个键。

同一个"列表外壳"里的条目键集也不一样，照抄别人的取值路径会 `KeyError`：

| 列表 | 每项键数 | 与相邻列表的差异 |
| :--- | :--- | :--- |
| `project_list` | 21 | 有 `user`、`views_count`；`icons` 6 键；`cover` 4 键 |
| `user_projects` | 19 | **无 `user`、无 `views_count`**，其余同全局列表 |
| `user_following` | 30 | 用户卡片：有 `sample_projects`、`skills`、`software_items`、`artist_role`；无 `projects_count`、无 `permalink` |
| `project_search` | 9 | **无 `slug` / `permalink`**（地址在 `url`）；有 `is_adult_content`；`icons` 7 键含 `multiple_images`；`user` 9 键 |
| `channel_projects` | 10 | 无 `is_adult_content`；有 `is_highlighted`、`small_square_cover_url` |
| `explore_latest` | 10 | 同 `channel_projects` |
| `album_projects` | 13 | 有 `album_id`、`album_title`、`position` 与**自带的 `assets`**；无 `user` / `views_count` / `likes_count` / `icons` |
| `channel_list` | 24 | 是频道对象，不是作品 |
| `search_filter_fields` | 2（`select_multiple` 为 3） | `{name, type}`，可能多一个 `select_options` |
| `project_search_post` | 11 | GET 搜索的 9 键再加 `assets`（数组，元素 11 键）与 `description`（HTML 字符串）；只在带 `additional_fields` 的样本里观测到 |

封面与资产也不是一套结构：`project_list` / `user_projects` 的 `cover` 是 4 键（`id`、`small_square_url`、`micro_square_image_url`、`thumb_url`）；`project_random` 的 `cover` 是 11 键（`thumb_url`、`medium_image_url`、`large_image_url`、`*_square_*`、四个 `crop_*`）；`album_projects` 的 `cover` 是 7 键（含 `small_image_url` / `large_image_url`，没有 `crop_*`）。`project_random` 的 `assets[]` 是 21 键，`album_projects` 的 `assets[]` 是 8 键，`project_search_post` 的 `assets[]` 是 11 键（`id`、`title`、`asset_type`、`width`、`height`、`position`、`viewport_constraint_type`、`small_image_url`、`large_image_url`、`has_image`、`has_embedded_player`）——三套都只是字符串地址，本库不下载、不改写。

## 筛选字符串：`filters` 必须是 JSON 字符串

`project_search` 的 `filters` 收的是**一段 JSON 字符串**，不是 Python 列表。写成列表会被共享编码展开成 `filters[][field]=...` 等查询键，站点不接受，回 `400 {"data": "filters should be a string"}`。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    filters = '[{"field":"title","method":"contain","value":"dragon"}]'
    result = client.project_search(query='', page=1, per_page=3,
                                   sorting='relevance', filters=filters)
    # GET https://www.artstation.com/api/v2/search/projects.json?query=&page=1&per_page=3&sorting=relevance
    #     &filters=%5B%7B%22field%22%3A%22title%22%2C%22method%22%3A%22contain%22%2C%22value%22%3A%22dragon%22%7D%5D
    # L：200，{"data": [ …3 项… ], "total_count": 111156}
    for item in result['data']:
        print(item['title'])
    # Dragon and mouse
    # Omakase! Dragonslayer :: 屠龍
    # Dragon's Breath
```

对照组：把同一组条件写成 Python 列表，会变成重复键并被拒绝。

```python
from anybooru import AnybooruHTTPError, ArtStation

with ArtStation('artstation') as client:
    try:
        client.project_search(query='', page=1, per_page=3, filters=[
            {'field': 'title', 'method': 'contain', 'value': 'dragon'},
        ])
        # GET …?filters%5B%5D%5Bfield%5D=title&filters%5B%5D%5Bmethod%5D=contain&filters%5B%5D%5Bvalue%5D=dragon
    except AnybooruHTTPError as error:
        # L：400 application/json，{"data": "filters should be a string"}
        print(error.http_code, error.data)
```

一个筛选元素本轮的形状是 `{"field": ..., "method": ..., "value": ...}`（`field=title`、`method=contain`、`value=dragon` 有效）。**还有哪些 `field` / `method` / `value` 组合可用没有系统测过**；`search_filter_fields()` 给的是字段名与可选值清单，不能当成"所有组合都成立"的证明。以上都针对 GET 的 `project_search`；[`project_search_post`](#匿名-csrf-令牌与只读搜索-post) 把 `params` 编成**表单正文**，**`filters` 在表单编码下的形态本轮没有样本**。

## 编号：`id` 与 `hash_id`

作品在响应里同时有数字 `id` 与短码 `hash_id`，两者用途不同：

* **`id`（数字）**：`22900098`。用在 `/api/v2/community/projects/{project_id}/comments.json` 这类**数字路径段**接口（`project_comments(22897630)`），也是各列表项之间的稳定对照键。
* **`hash_id`（短码）**：`1LxzVq`。出现在 `permalink`（`https://www.artstation.com/artwork/1LxzVq`）里，也是站点页面路由与固定详情路径的用法（`/projects/{hash}.json`，本轮被挑战，见下）。
* 搜索结果项给的是完整地址 `url`，**没有** `slug` / `permalink`；相册项给 `slug` 但也给 `hash_id`。
* 两者都不是连续的，也不保证不重复出现在别的路由里；库不校验、不转换、不互相推导（不会拿 `hash_id` 去自动搜索，也不会拿 `id` 去拼详情路径）。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    project = client.project_random()
    print(project['id'], project['hash_id'], project['permalink'], project['shortlink'])
    # 3260777 OnxxK https://www.artstation.com/artwork/OnxxK https://artstn.co/p/OnxxK
    comments = client.project_comments(project['id'])   # 评论路由要数字 id
    # GET https://www.artstation.com/api/v2/community/projects/3260777/comments.json
    # （这条编号未实测，只演示 id 的来源；本轮测过的评论编号是 22897630）
    print(comments['total_count'])
```

## 固定作品详情路径：403/401，与没有 `project_show`

本类**没有 `project_show()`**：本轮两条"按固定标识取单个作品"的路径都拿不到数据，客户端也**不会**自动改走别的路径（比如拿 `hash_id` 去搜索）。

| 路径 | 本轮结果 | 正文 |
| :--- | :--- | :--- |
| `/projects/{hash}.json`（站点根下的固定详情） | `403 text/html; charset=UTF-8`，响应头带 `Cf-Mitigated: challenge` | Cloudflare 质询页 HTML（约 24 KB），不是作品 JSON |
| `/api/v2/community/projects/{数字 id}.json` | `401 application/json; charset=utf-8` | `{"data": null}` |

```python
from anybooru import AnybooruHTTPError, ArtStation

with ArtStation('artstation') as client:
    try:
        client.request('GET', '/projects/G1ew2N.json')
        # GET https://www.artstation.com/projects/G1ew2N.json
    except AnybooruHTTPError as error:
        # L：403 text/html; charset=UTF-8，响应头 Cf-Mitigated: challenge；error.data 为 None（HTML 不是 JSON）
        print(error.http_code, error.response.headers.get('Cf-Mitigated'), len(error.body))

    try:
        client.request('GET', '/api/v2/community/projects/22897630.json')
        # GET https://www.artstation.com/api/v2/community/projects/22897630.json
    except AnybooruHTTPError as error:
        # L：401 application/json; charset=utf-8，error.data == {'data': None}
        print(error.http_code, error.data)
```

这两个样本只说明**这两条路径在本轮匿名请求里拿不到数据**，不是"站点没有详情接口"的结论：想按编号取作品时，用列表 / 搜索 / 相册 / 频道结果里已有的条目，或用通用入口自己发别的路径（库不替你换路、不加参数、不改写响应）。

## 边界与未实测

前面每节已经就事论事地标了未实测；这里只集中列**没有样本或没有穷举**的部分，不要当契约：

* **缺省行为没有样本**：`project_list`、`user_projects`、`user_following`、`album_projects`、`channel_projects`、`explore_latest` 的**不传 `page` / `per_page`** 本轮一次都没测过；候选资料声称的"默认第 1 页 / 默认每页条数"没有 L 支持。唯一有缺省证据的是 `project_search`：缺 `page` 是 `400 {"data": "page should be given"}`、缺 `per_page` 是 `400 {"data": "per_page should be given"}`（都是直接报错，不是默认值）。
* **边界只取了单点**：可以用的点有全局列表 `per_page` `1` / `50`、搜索 `3` / `75`、相册 `4`、探索 `10`；报错的点有全局列表 `51` 与 `page=999999`、搜索 `2` / `76` / `page=0`、相册 `3`、探索 `9`。这些点之间的精确上下限**没有二分**；`user_projects` / `user_following` / `channel_projects` / `project_comments` 的每页条数上限**完全没测**。客户端**不钳位**，越界一律由站点报错。
* **排序与筛选枚举未实测**：`sorting` 只跑过搜索的 `'relevance'` 与 RSS 的 `'latest'`；`pro_first` 未测；GET additional_fields 有一次 200，结果未追加 assets/description，POST 侧另见下节；频道 `sorting` / `dimension`、`project_comments` 的 `page` / `per_page`、`user_projects` 的 `album_id` **一次都没有测过**；`filters` 只测过 `title` + `contain` + `dragon` 一组。
* **账号与内容写入未测**：登录、发 / 改 / 删作品、评论、收藏、关注、上传、admin，以及任何带账号凭据的请求**一个都没有测过**。本轮新增的 `POST` 只有这两条路由（CSRF 令牌与只读搜索），它们不改数据；其未测项见下一条与[匿名 CSRF 令牌与只读搜索 POST](#匿名-csrf-令牌与只读搜索-post)。无凭据的 `401` / `403` 也不能证明站点用的是哪种认证。
* **`POST` 侧未测**：令牌的省略参数行为、有效期、复用 / 续期 / 失效、同一令牌跨实例或跨进程的表现，缺令牌 / 过期令牌 / 被拒（例如 `412` 之类）的响应，其它 `POST` 路由，`filters` 在表单编码下的形态，`POST` 搜索自己的 `page` / `per_page` 边界，以及 `additional_fields` 的其它取值，**都没有单独样本**。
* **两条固定详情路径**只有 `403` 挑战页与 `401 {"data": null}` 两个样本，它们的成功结构、其它固定详情写法、匿名受限内容**都没有样本**。
* **未知路径没有穷举**：只有 `/openapi.json` 与一条随便编的路径返回 `200 text/html` 兜底页；"所有未知路径都 200"与"所有 `/api/v2/**` 都不被挑战"都**没有证据**。
* **随机详情样本有限**：直接观察一条，冒烟与示例另各一条，tags 都是空数组；直接样本 original_url 为 null。随机分布、tags 元素形态与 assets 的稳定键集未验证，不能称均匀随机或任意字段恒有。
* **列表项的键集只是当时的快照**：21 / 19 / 13 / 10 / 11 / 9 / 30 / 24 这些数字不保证恒定（`11` 是带 `additional_fields` 的 `POST` 搜索项）；`tag_list` 本轮全是 `null`，非空内容未测；`total_count` 都是当天读数（全局 `14522955`、搜索 `cat` `118784`、过滤 `dragon` `111156`、关注 `409`、用户作品 `40`、频道 `10000`、频道数 `64`、相册 `49`、`POST` 搜索 `118783`），**不保证稳定，也不代表站点上限**；同名 GET 与 POST 搜索的 `118784` / `118783` 是两次不同请求的读数，不要当成同一个常量。
* **评论非空结构未测**：直接观察与浏览示例都只有 `{"total_count":0,"data":[]}`，所以本文不写评论字段名。
* **用户对象的三份差异没有定论**：70 / 59 / 63 键只是样本；三条路由为什么在 `followees_count` / `collections_count` / 相册标题上不一样（`408` vs `409`、`2` vs `15`、`"All"` vs `"All projects"`），本轮如实返回、不做合并与纠正。
* **媒体与法律**：所有 `cdn*.artstation.com` 主机本轮**零请求**，地址规则只来自字段本身；本站的条款与 robots 本轮读过（都是 `200`），**匿名能拿到响应不等于站点许可抓取或聚合**。
* **本库不做任何绕过或兜底**：没有 UA 伪装、Cookie 伪造、出口轮换、重试、退避、响应改写、自动换路、参数钳位。

继续阅读：[客户端用法](artstation.md) · [能力入口](artstation-capabilities.md) · [依据与差异](artstation-contract-notes.md) · [验证记录](verification.md#artstation匿名只读实测2026-09-20)。
