# Sakuria 方法参考

Sakuria（`sakuria-api.syarolia.com`）是 Pixiv 的第三方镜像站：作品、用户、系列编号沿用 Pixiv 体系，接口是站点自己的一套。站点没有官方文档、OpenAPI、可引用的服务端源码。本页结论只来自本库本轮的匿名只读执行（**L**）。用户提供的输入文档只作候选，没有被 L 支持的部分集中在[边界与未实测](#边界与未实测)，不当契约写。

本页列出 44 个原生方法：27 个匿名只读 `GET`（服务与配置 5、插画 5、用户 8、小说 4、系列 1、特辑 2、标签 2）和 17 个 `/me/*` 账号方法，另有通用入口 `request(method, path, *, params=None, headers=None)`。

客户端怎么构造、`last_call` 与异常见[客户端用法](sakuria.md)；「想做什么 → 用哪个方法」见[能力入口](sakuria-capabilities.md)；依据出处与排除项见[依据与差异](sakuria-contract-notes.md)；执行记录见[验证记录](verification.md#sakuria匿名只读实测2026-09-19)。

## 依据标注与阅读方式

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **L** | 本轮 54 次直接 HTTP 观察（每组请求发一次、不重试、不跟随跳转、不下载媒体） | 对应路由和参数的状态、Content-Type 与字段；不等于每个 Python 方法都执行过 |
| **未实测** | 输入文档声称、本轮没有请求或没有复现 | 参数取值、默认值、枚举、错误码与媒体行为的候选；**不作为契约** |

本轮 54 个响应全部是 `Content-Type: application/json`，状态分布 `200`×41、`400`×7、`401`×3、`404`×1、`503`×1、`426`×1——`403` 没有样本。

本页只写 L 支持的事实；未知项与输入文档的矛盾分别集中在[实测与输入文档的矛盾](#实测与输入文档的矛盾)与[边界与未实测](#边界与未实测)。

## 通用约定

- **基地址**：`https://sakuria-api.syarolia.com`，来自包内配置 `sites.sakuria`。本页路由都补在它之后。
- **方法**：44 个原生方法全部发 `GET`；参数放查询串，`tag_illusts` 的标签放路径段。
- **认证**：默认匿名。构造时 `access_token` 非空才发 `Authorization: Bearer <token>`；显式传空字符串按不配置凭据处理，不发认证头。构造函数没有 `username`。显式传入的 `headers` 在认证头之后合并。
- **自定义头**：客户端不加隐式头。L：`/me/likes` 不带 `x-sakuria-data-contract` 返回 `426 {"error":"upgrade_required","requiredDataContract":2}`；显式带 `x-sakuria-data-contract: 2` 后返回 `401 {"error":"sakuria_session_required"}`。包装方法签名只有位置参数和 `**params`，不接 `headers`；要带这个头请用通用入口。
- **参数编码**：`params` 走共享编码——`None` 值不发送、布尔转小写 `true`/`false`、嵌套字典写成 `key[child]`、序列写成重复 `key[]` 键。库不做本地校验、不钳位、不补默认值。
- **返回**：JSON 原样返回，不拆信封、不改字段名、不转换类型。2xx 空正文返回 `None`；2xx 但正文不是 JSON 抛 `AnybooruAPIError`；非 2xx 抛 `AnybooruHTTPError`（带 `http_code` / `url` / `body` / `data`）。库不重试、不降级、不对 503 自动重发。`client.last_call` 保留 `API`、`url`、`status_code`、`status`、`headers`。
- **信封**：服务端返回的列表外层结构。L 实测不统一：搜索与用户作品列表返回 `{items, page, pageSize, total, totalPages, hasMore, nextPage?, hiddenCount?}`（`nextPage`、`hiddenCount` 是否出现按路由）；用户收藏是 `{items, pageSize, hasMore, nextCursor, hiddenCount}`；评论是 `{items, hasMore}`；回复与相关插画、相关用户只有 `{items}`；`/users/{id}/followers`、`/users/{id}/series` 是 `{items, page, pageSize, hasMore}`。详情路由（`/`、`/illust/{id}`、`/users/{id}`、`/novels/{id}`、`/series/{id}`、`/spotlight/{id}`）是裸对象。
- **分页字段是假值（L）**：`search/illust?q=blue` 的 `page=1/2/3` 给出 `total` 48/72/96、`totalPages` 4/4/6、`nextPage` 4/4/6，page1∩page2 有 24 项、page2∩page3 有 10 项。数值 `nextPage` 不能当相邻页码；翻页要手动 `page + 1`，判末尾只看 `hasMore=false`（本轮没有跑到末页，末页标志未实测）。
- **`pageSize` 与条数不符（L）**：`search/illust` 写 `pageSize:24` 的三页分别返回 29/24/33 项，`size=48` 那页返回 39 项；`spotlight` 写 `pageSize:12` 返回 20 项。不要用信封字段推算 `items` 长度。
- **参数校验（L）**：被识别的参数会校验，非法值返回 `400 {"error":"筛选参数无效","code":"invalid_search_filter","field":"<参数名>"}`；已复现 `page=0`、`size=0`、`size=49`、`sort=__invalid__`、`mode=text` 各一次。哪些参数名之外还会被识别、哪些参数会被忽略，见[边界与未实测](#边界与未实测)。
- **媒体**：本库不下载任何图片字节，也不提供图片字节方法。L 本轮没有对 `/img/` 或任何图片主机发请求；`urls.*`、`thumb`、`avatar`、`cover` 给的都是地址字符串，怎么拼完整 URL 见[边界与未实测](#边界与未实测)。

## 通用入口 `request()`

签名：`request(method, path, *, params=None, headers=None)`

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串，大写；本页 44 个原生方法都发 `'GET'` | 必填（Python 报缺参） | `client.request('GET', '/stats')` |
| `path` | 站点相对路径，如 `'/search/illust'`；前导 `/` 可有可无 | 必填 | `client.request('GET', '/tags/blue', params={'size': 2})` |
| `params` | 查询参数字典，经共享编码后拼进查询串 | `None`，不发查询参数 | 见上一行 |
| `headers` | 额外请求头字典，在认证头之后合并 | `None`，只带默认头与认证头 | `client.request('GET', '/me/likes', headers={'x-sakuria-data-contract': '2'})` |

`last_call['API']` 是去掉前导 `/` 的路径；例如 `'/stats'` 对应 `'stats'`，根路径对应空字符串。

```python
from anybooru import AnybooruHTTPError, Sakuria

with Sakuria('sakuria') as client:
    body = client.request('GET', '/stats')
    # GET https://sakuria-api.syarolia.com/stats
    # L：200，{"newToday": 30, "totalIllusts": 85, "totalCreators": 197, "totalUsers": 113}
    print(sorted(body))

with Sakuria('sakuria', access_token='') as client:
    try:
        me_likes = client.request('GET', '/me/likes',
                                  headers={'x-sakuria-data-contract': '2'})
        # GET https://sakuria-api.syarolia.com/me/likes
        # L 匿名观察：没有这个头时 426 upgrade_required；带上后 401 sakuria_session_required。
        print(me_likes)
    except AnybooruHTTPError as error:
        print(error.http_code, error.url, repr(error.body))
```

## 服务与配置（5 个方法）

这 5 个方法只接 `**params`，没有位置参数；本轮 5 次请求都成功，参数是否被识别未实测（见边界）。

### index

`index(**params)` → 路由 `GET /`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `client.index()` |

L：200，正文恰 3 个键 `{"name":"sakuria-api","ok":true,"docs":"https://github.com/your-org/sakuria"}`（`str` / `bool` / `str`）。`docs` 指向占位仓库，不是真实源码或文档。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    body = client.index()
    # GET https://sakuria-api.syarolia.com/
    # L：{"name": "sakuria-api", "ok": true, "docs": "https://github.com/your-org/sakuria"}
    print(body['name'], body['ok'], body['docs'])
```

### stats

`stats(**params)` → 路由 `GET /stats`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `client.stats()` |

L：200，4 个整数键 `newToday`、`totalIllusts`、`totalCreators`、`totalUsers`（本轮值 30 / 85 / 197 / 113）。这些是站点自报计数，`totalIllusts` 只有两位数，不能当作镜像站可搜到的作品规模。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    stats = client.stats()
    # GET https://sakuria-api.syarolia.com/stats
    # L：{"newToday": 30, "totalIllusts": 85, "totalCreators": 197, "totalUsers": 113}
    print(stats['newToday'], stats['totalIllusts'], stats['totalCreators'], stats['totalUsers'])
```

### health

`health(**params)` → 路由 `GET /healthz`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `client.health()` |

L：200。顶层 `ok`（bool）、`releaseSha`、`releaseVersionId`（str），`checks` 是 12 键对象：`db`、`jwt`、`pxve`、`aiProviderCredentials`、`aiProviderCredentialKekVersion`、`giftSchemaReady`、`giftRuntimeReady`、`aiProviderCredentialDecryptable`、`aiProviderRuntimeReady`、`cache` 为 bool，`cacheBackend`、`databaseDriver` 为 str（本轮样本分别是 `"d1-fallback"`、`"d1"`）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    health = client.health()
    # GET https://sakuria-api.syarolia.com/healthz
    # L：{"ok": true, "releaseSha": "…", "releaseVersionId": "…", "checks": {…12 键…}}
    print(health['ok'], health['checks']['databaseDriver'], health['checks']['cacheBackend'])
```

### app_config

`app_config(**params)` → 路由 `GET /app/config`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `client.app_config()` |

L：200。本轮读到的键与类型：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `latestVersion` | str | 本轮 `"1.0.0"` |
| `latestBuild` | int | 本轮 `1` |
| `updateUrl` / `releaseNotes` | str | 本轮都是空串 |
| `updateAvailable` / `updateRequired` | bool | 本轮 `true` / `false` |
| `maintenance.enabled` | bool | 维护模式开关 |
| `announcement` | null | 本轮为 `null` |
| `flags` | object | `directMode`、`proxyMode`、`inAppRegister` 三个 bool |
| `servers` | array | 本轮 2 条，每项 `{id, name, baseUrl, memberOnly, region, enabled, note}`；`id` 本轮为 `cloudflare` 与 `backbone`，后者 `memberOnly:true` |
| `imageProxy` | object | `{enabled, turboBase}`，`turboBase` 是图片代理主机 |
| `imageProxyPro` | object | `{enabled}` |
| `iap` | object | `plus{enabled, notice, promo{badge, originalPrice, endsAt}}`、`credits{enabled, notice, dailyLimit}`、`tips{enabled}`；本轮样本在此处截断，是否还有其它子键未读到 |

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    config = client.app_config()
    # GET https://sakuria-api.syarolia.com/app/config
    # L：servers[] 2 条；imageProxy.turboBase 是图片代理主机；maintenance.enabled 为 bool
    print([server['id'] for server in config['servers']], config['maintenance']['enabled'])
    print(config['imageProxy']['turboBase'], config['flags'])
```

### ai_config

`ai_config(**params)` → 路由 `GET /ai/config`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `client.ai_config()` |

L：200。顶层 bool：`enabled`、`metaEnabled`、`novelEnabled`、`mangaEnabled`、`commentEnabled`、`ratesEstimated`；str：`mangaInputMode`（本轮 `"client_ocr_v1"`）、`billingMode`（本轮 `"static_token_price"`）；int：`cacheTtlDays`（本轮 `7`）。`models[]` 本轮 2 条，每项含 `id`、`name`、`providerName`、`rateRangeState`、`ratePer1mInRange{min,max}`、`ratePer1mOutRange{min,max}`、`ratePer1mIn`、`ratePer1mOut`、`billingMode`、`ratesEstimated`、`contextLength`、`maxOutputTokens`、`inputModalities[]`、`outputModalities[]`、`reasoningByScene{meta, novel, …}`；本轮样本在 `reasoningByScene` 处截断，`defaults`、`reasoningDefaults`、`languages[]` 等键是否存在于本页未实测。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    ai = client.ai_config()
    # GET https://sakuria-api.syarolia.com/ai/config
    # L：enabled 为 true；models[] 2 条，每项含 id/name/providerName/contextLength 等键
    print(ai['enabled'], ai['billingMode'], len(ai['models']))
    print(ai['models'][0]['id'], ai['models'][0]['contextLength'])
```

## 插画（5 个方法）

### illust_search

`illust_search(**params)` → 路由 `GET /search/illust`。返回列表信封，`items` 每项是[插画对象](#插画对象)。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `q` | 查询词；本轮只证 `q=blue` 被接受（匹配语义未实测） | 未实测 | `q='blue'` |
| `page` | 页码；`page=0` → 400 `invalid_search_filter`，`field` 为 `page`；`page=1/2/3` → 200 | 本轮两条不带 `page` 的请求都返回 `page:1` | `page=2` |
| `size` | 每页条数，写进信封 `pageSize`；`size=1`、`size=48` → 200，`size=0`、`size=49` → 400，`field` 为 `size` | 未实测（输入文档说 24） | `size=2` |
| `sort` | 排序；`sort=popular` → 200，`sort=__invalid__` → 400，`field` 为 `sort` | 未实测 | `sort='popular'` |
| `mode` | 本轮 `mode=text` → 400，`field` 为 `mode`；其它值未实测 | 未实测 | `mode='text'`（预期抛 HTTP 错误） |
| `type` | `type=illust` → 401 `{"code":"auth_required","feature":"advanced_search"}` | 未实测 | `type='illust'`（匿名抛 HTTP 错误） |
| `limit` | `limit=__invalid__` 在 `size=24` 基线上仍 200，ID 顺序与分页字段不变 | 未实测 | `limit='__invalid__'` |

L：200 的信封是 `{items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}`，`items` 条数与 `pageSize` 不相等（本轮 `size=24` 的三页分别 29/24/33 项，`size=1` 是 5 项、`size=48` 是 39 项）。`total` / `totalPages` / `nextPage` 是假值，见[通用约定](#通用约定)的分页条目。其余参数名是否被识别见[边界与未实测](#边界与未实测)。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    first_page = client.illust_search(q='blue', size=2, sort='new', page=1)
    # GET https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=1
    # L：200；信封 {items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}
    print(first_page['page'], first_page['pageSize'], first_page['hasMore'])
    for illust in first_page['items']:
        print(illust['id'], illust['title'], illust['urls']['thumb'], illust['author']['id'])
    second_page = client.illust_search(q='blue', size=2, sort='new', page=2)
    # GET https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=2
    # 这组 size=2 示例本轮两页没有重叠；另一次 size=24 对照有 24 个重复 ID。取多页仍应按 id 去重。
    print([illust['id'] for illust in second_page['items']])
```

### illust_show

`illust_show(illust_id, **params)` → 路由 `GET /illust/{illust_id}`。返回**裸对象**[插画对象](#插画对象)，没有信封。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `illust_id` | 作品编号，进 URL 路径 | 必填 | `illust_show(70937229)` |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `illust_show(70937229)` |

L：`/illust/70937229` → 200；`/illust/0` → 404 `{"error":"illust not found"}`；`/illust/abc` → 400 `{"error":"invalid id"}`（本轮只证这两个取值）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    illust = client.illust_show(70937229)
    # GET https://sakuria-api.syarolia.com/illust/70937229
    # L：200；id/title/type/pages/urls/author/tags/stats/publishedAt/publishedDays/
    #    isAi/isR18/xRestrict/sl（本样本 pages=1、isR18=false、xRestrict=0、sl=2）
    print(illust['id'], illust['title'], illust['pages'], illust['type'])
    print(illust['urls']['regular'], illust['author']['name'], illust['stats'])
    print([tag['name'] for tag in illust['tags']])
```

### illust_comments

`illust_comments(illust_id, **params)` → 路由 `GET /illust/{illust_id}/comments`。返回 `{items, hasMore}`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `illust_id` | 作品编号，进 URL 路径 | 必填 | `illust_comments(70937229)` |
| `page` / `size` | 本轮只用 `page=1&size=2` 发过一次，两个取值都被接受 | 未实测 | `page=1, size=2` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：200，`{"items":[2 条评论],"hasMore":true}`。评论对象本轮观察到的键：`id`、`author{id,name,handle,accent,avatar}`（**没有 `stats`**）、`text`、`repliesCount`、`likes`、`createdAt`、`timeLabel`。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    comments = client.illust_comments(70937229, page=1, size=2)
    # GET https://sakuria-api.syarolia.com/illust/70937229/comments?page=1&size=2
    # L：200，{"items": [2 条], "hasMore": true}；每项含 id/author/text/repliesCount/likes/
    #    createdAt/timeLabel
    print(comments['hasMore'])
    for comment in comments['items']:
        print(comment['id'], comment['author']['name'], comment['timeLabel'], comment['repliesCount'])
```

### illust_comment_replies

`illust_comment_replies(illust_id, comment_id, **params)` → 路由 `GET /illust/{illust_id}/comments/{comment_id}/replies`。返回 `{"items":[…]}`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `illust_id` / `comment_id` | 作品编号与父评论编号，进 URL 路径 | 必填 | `illust_comment_replies(70937229, 183991501)` |
| `**params` | 本轮没有可识别参数（`page`/`size` 在别处用过，这里没试） | 不发查询参数 | 同上 |

L：`/illust/70937229/comments/183991501/replies` → 200，`{"items":[1 条回复]}`，**没有 `hasMore`**；回复对象与插画评论同构（同样的 8 个键）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    replies = client.illust_comment_replies(70937229, 183991501)
    # GET https://sakuria-api.syarolia.com/illust/70937229/comments/183991501/replies
    # L：200，{"items": [1 条]}；回复对象字段与插画评论同构，没有 hasMore。
    print(len(replies['items']))
    for reply in replies['items']:
        print(reply['id'], reply['author']['name'], reply['text'])
```

### illust_related

`illust_related(illust_id, **params)` → 路由 `GET /illust/{illust_id}/related`。返回 `{"items":[Illust]}`，**没有分页字段**。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `illust_id` | 作品编号，进 URL 路径 | 必填 | `illust_related(128641898)` |
| `size` | 返回条数；本轮 `size=2` → 200 返回 2 条 | 未实测 | `size=2` |
| `**params` | 本轮没有其它可识别参数（`page`/`limit`/`offset` 是否被忽略未实测） | 不发查询参数 | 同上 |

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    related = client.illust_related(128641898, size=2)
    # GET https://sakuria-api.syarolia.com/illust/128641898/related?size=2
    # L：200，{"items": [2 张 Illust]}；没有 page/total/hasMore 等分页键。
    print([illust['id'] for illust in related['items']])
```

## 用户（8 个方法）

### user_search

`user_search(**params)` → 路由 `GET /search/user`。返回 `{items, total}`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `q` | 查询词；本轮 `q=mika` 被接受 | 未实测 | `q='mika'` |
| `page` | 页码；本轮 `page=1/2/3` → 200，`total` 分别为 6/12/21，与各页 `items` 条数相等、各页 ID 无交集 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数（非法值行为未实测） | 不发查询参数 | 同上 |

L：200，信封只有 `items` 与 `total` 两个键——**`total` 是本页条数，不是累计总数**。`items[]` 每项是 `{user, previews}`：`user` 是[用户对象](#用户对象)（没有 `social`/`bio`/`banner`/`location`）；`previews` 本轮 1–3 条，每项 `{id, title, thumb, isR18, xRestrict, isAi, sl}`，`thumb` 是地址字符串。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    found = client.user_search(q='mika', page=1)
    # GET https://sakuria-api.syarolia.com/search/user?q=mika&page=1
    # L：200，{"items": [6 条], "total": 6}；total 等于本页 items 条数。
    print(found['total'], len(found['items']))
    for item in found['items']:
        print(item['user']['id'], item['user']['name'], item['user']['handle'],
              [preview['id'] for preview in item['previews']])
```

### user_show

`user_show(user_id, **params)` → 路由 `GET /users/{user_id}`。返回**裸对象**[用户对象](#用户对象)，没有信封。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `user_id` | Pixiv 用户编号，进 URL 路径 | 必填 | `user_show(129030276)` |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `user_show(129030276)` |

L：`/users/129030276` → 200，键 `id`、`name`、`handle`、`accent`、`avatar`、`banner`、`stats`、`social`；`stats` 本轮不是全 0（`following:11`、`works:8`、`totalBookmarks:13`），`social` 一条 `{kind, url, label}`；`banner` 是地址字符串（`/img/c/1200x600_90_a2_g5/background/…`）。其它 id 取值（0、超大编号、非数字）本轮没有请求。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    user = client.user_show(129030276)
    # GET https://sakuria-api.syarolia.com/users/129030276
    # L：200；id/name/handle/accent/avatar/banner/stats/social（social 1 条）
    print(user['id'], user['name'], user['handle'], user['banner'])
    print(user['stats'], user['social'][0]['url'])
```

### user_illusts

`user_illusts(user_id, **params)` → 路由 `GET /users/{user_id}/illusts`。返回列表信封，`items` 每项是[插画对象](#插画对象)。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `user_id` | 用户编号，进 URL 路径 | 必填 | `user_illusts(1039353)` |
| `page` | 页码；本轮 `page=1/2` → 200，各 45 项、交集 23 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数（`pageSize`/`limit`/`offset`/`sort` 是否被忽略未实测） | 不发查询参数 | 同上 |

L：200 的信封 `{items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}`：`pageSize` 都 24，`hiddenCount` 都 3，`nextPage` 分别 3 与 4，`total` 48/72，`totalPages` 2/3，`hasMore` 都 `true`——与搜索一样，**这些字段不能当真实页码或总数**。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    works = client.user_illusts(1039353, page=1)
    # GET https://sakuria-api.syarolia.com/users/1039353/illusts?page=1
    # L：200；信封 {items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}
    #    （pageSize=24、hiddenCount=3、nextPage=3，items 本轮 45 项）
    print(works['page'], works['hasMore'], works['total'], len(works['items']))
    for illust in works['items']:
        print(illust['id'], illust['title'], illust['stats']['likes'])
```

### user_novels

`user_novels(user_id, **params)` → 路由 `GET /users/{user_id}/novels`。返回列表信封，`items` 每项是[列表 Novel-lite](#小说对象)。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `user_id` | 用户编号，进 URL 路径 | 必填 | `user_novels(3182410)` |
| `page` | 页码；本轮 `page=1` → 200 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：200 的信封 `{items, page, pageSize, total, totalPages, hasMore, nextCursor}`：本轮 24 项、`pageSize` 24、`total` 48、`totalPages` 2、`hasMore:true`，`nextCursor` 是**上游 Pixiv 地址**（`https://app-api.pixiv.net/v1/user/novels?user_id=3182410&offset=30`），不能拿去请求本站。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    novels = client.user_novels(3182410, page=1)
    # GET https://sakuria-api.syarolia.com/users/3182410/novels?page=1
    # L：200；items 24 项，hasMore=true，nextCursor 指向上游 Pixiv 地址
    print(novels['page'], novels['hasMore'], novels['nextCursor'])
    for novel in novels['items']:
        print(novel['id'], novel['title'], novel['textLength'])
```

### user_bookmarks

`user_bookmarks(user_id, **params)` → 路由 `GET /users/{user_id}/bookmarks`。返回信封 `{items, pageSize, hasMore, nextCursor, hiddenCount}`，`items` 每项是[插画对象](#插画对象)。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `user_id` | 用户编号，进 URL 路径 | 必填 | `user_bookmarks(1554775)` |
| `page` | 本轮 `page=1` 与 `page=2` 返回**完全相同**的 JSON（19 项、`nextCursor` 都是 `"9175901406"`）：这两个取值没有推进分页 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：200，`pageSize` 24、`hiddenCount` 5、`hasMore:true`。**只有 `page=1/2` 这两个值被证过**，`cursor` / `nextCursor` / `limit` / `offset` 等是否有效见[边界与未实测](#边界与未实测)。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    bookmarks = client.user_bookmarks(1554775, page=1)
    # GET https://sakuria-api.syarolia.com/users/1554775/bookmarks?page=1
    # L：200；items 19 项，pageSize=24、hiddenCount=5、hasMore=true、nextCursor="9175901406"
    print(bookmarks['pageSize'], bookmarks['hasMore'], bookmarks['nextCursor'])
    for illust in bookmarks['items']:
        print(illust['id'], illust['title'])
```

### user_followers

`user_followers(user_id, **params)` → 路由 `GET /users/{user_id}/followers`。返回信封 `{items, page, pageSize, hasMore}`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `user_id` | 用户编号，进 URL 路径 | 必填 | `user_followers(1039353)` |
| `page` | 本轮 `page=1`、`page=2` → 200，`page` 原样回显 1 与 2 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：两次都返回 `{"items":[],"pageSize":12,"hasMore":false}`。**只能说明这两个 page 取值为空，不能据此说 `page` 无效，也不能说该功能未实现**；非空时 item 的字段结构见[边界与未实测](#边界与未实测)（未实测）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    followers = client.user_followers(1039353, page=1)
    # GET https://sakuria-api.syarolia.com/users/1039353/followers?page=1
    # L：200，{"items": [], "page": 1, "pageSize": 12, "hasMore": false}；page=2 同样为空。
    print(followers['page'], followers['pageSize'], followers['hasMore'], len(followers['items']))
```

### user_series

`user_series(user_id, **params)` → 路由 `GET /users/{user_id}/series`。返回信封 `{items, page, pageSize, hasMore}`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `user_id` | 用户编号，进 URL 路径 | 必填 | `user_series(3182410)` |
| `page` | 本轮 `page=1` → 200 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：`/users/3182410/series?page=1` → 200，`{"items":[],"page":1,"pageSize":24,"hasMore":false}`：**本轮没有取得非空样本，item 字段未实测**（见边界）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    series = client.user_series(3182410, page=1)
    # GET https://sakuria-api.syarolia.com/users/3182410/series?page=1
    # L：200，{"items": [], "page": 1, "pageSize": 24, "hasMore": false}
    print(series['page'], series['pageSize'], series['hasMore'], len(series['items']))
```

### user_related

`user_related(user_id, **params)` → 路由 `GET /users/{user_id}/related`。返回 `{"items":[…]}`，item 与 `user_search` 的 `{user, previews}` 同构。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `user_id` | 用户编号，进 URL 路径 | 必填 | `user_related(1039353)` |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `user_related(1039353)` |

L：`/users/1039353/related` → 200，`{"items":[12 条 {user, previews}]}`，**没有分页键**。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    related = client.user_related(1039353)
    # GET https://sakuria-api.syarolia.com/users/1039353/related
    # L：200，{"items": [12 条 {user, previews}]}；没有分页键。
    for item in related['items']:
        print(item['user']['id'], item['user']['name'], len(item['previews']))
```

## 小说（4 个方法）

### novel_search

`novel_search(**params)` → 路由 `GET /search/novel`。返回列表信封，`items` 每项是[列表 Novel-lite](#小说对象)（**不含正文 `text`**）。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `q` | 查询词；本轮 `q=blue` 被接受 | 未实测 | `q='blue'` |
| `page` | 页码；本轮 `page=1/2` → 200 | 未实测 | `page=1` |
| `sort` | 排序字段；完整枚举与行为未实测，见边界 | 未实测 | 本轮省略 |
| `type` | `type=illust` → 400 `{"error":"小说不支持该作品筛选条件","code":"unsupported_filter_for_scope","field":"type"}` | 未实测 | `type='illust'`（抛 HTTP 错误） |
| `ai` | `ai=exclude` → 401 `{"code":"auth_required","feature":"advanced_search"}`（不是 403） | 未实测 | `ai='exclude'`（匿名抛 HTTP 错误） |
| `mode` | 取值与行为未实测，见边界 | 未实测 | 本轮省略 |

L：200 的信封 `{items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}`：本轮 page1 24 项、`total` 48、`totalPages` 2、`nextPage` 2、`hiddenCount` 6；page2 26 项、`total` 72、`totalPages` 3、`nextPage` 3、`hiddenCount` 4。总数随页码变化，不当固定全局总数；这两次 nextPage 恰为下一相邻页，不能推广其它查询。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    found = client.novel_search(q='blue', page=1)
    # GET https://sakuria-api.syarolia.com/search/novel?q=blue&page=1
    # L：200；items 24 项，total=48、totalPages=2、nextPage=2、hiddenCount=6
    print(found['page'], found['hasMore'], found['total'], len(found['items']))
    for novel in found['items']:
        print(novel['id'], novel['title'], novel['textLength'], 'text' in novel)
```

### novel_show

`novel_show(novel_id, **params)` → 路由 `GET /novels/{novel_id}`。返回**裸对象**。注意 `/novel/{id}`（单数）没有请求过，不要假设它存在。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `novel_id` | 小说编号，进 URL 路径 | 必填 | `novel_show(29167620)` |
| `**params` | 本轮没有可识别参数 | 不发查询参数 | `novel_show(29167620)` |

L：`/novels/29167620` → 200，键包括 `id`、`title`、`author`、`caption`、`captionHtml`、`tags`、`textLength`、`coverSvg`、`cover{thumb, small, regular, original, w, h}`、`text`、`document{text, uploadedImages, pixivImages}`、`publishedAt`、`publishedDays`、`isAi`、`isR18`、`xRestrict`、`sl`。该样本 `textLength` 是 99，但顶层 `text` 是**空串**：正文只出现在 `document.text`（4 行 `[uploadedimage:<id>]`），对应 `document.uploadedImages` 的 4 个对象（每个含 `{id, urls{thumb, small, regular, original}, visible, isR18, xRestrict, sl}`），而 `document.pixivImages` 是空对象；对该样本只读顶层 `text` 会丢失文档里的插图标记。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    novel = client.novel_show(29167620)
    # GET https://sakuria-api.syarolia.com/novels/29167620
    # L：200；textLength=99，但顶层 text 是空串；正文在 document.text（4 行 [uploadedimage:…]），
    #    document.uploadedImages 有 4 个对象，document.pixivImages 是空对象。
    print(novel['id'], novel['title'], novel['textLength'], repr(novel['text']))
    print(novel['document']['text'])
    print(sorted(novel['document']['uploadedImages']))
```

### novel_comments

`novel_comments(novel_id, **params)` → 路由 `GET /novels/{novel_id}/comments`。返回 `{items, hasMore}`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `novel_id` | 小说编号，进 URL 路径 | 必填 | `novel_comments(29167620)` |
| `page` | 页码；本轮 `page=1` → 200 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：`/novels/29167620/comments?page=1` → 200，`{"items":[],"hasMore":false}`。本轮没有非空样本，评论对象的 `stampUrl` / `stampId` 等字段见[边界与未实测](#边界与未实测)（未实测）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    comments = client.novel_comments(29167620, page=1)
    # GET https://sakuria-api.syarolia.com/novels/29167620/comments?page=1
    # L：200，{"items": [], "hasMore": false}
    print(comments['hasMore'], len(comments['items']))
```

### novel_related

`novel_related(novel_id, **params)` → 路由 `GET /novels/{novel_id}/related`。返回带 `items` 与分页字段的对象；本轮 `items` 为空，非空元素结构未实测。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `novel_id` | 小说编号，进 URL 路径 | 必填 | `novel_related(29167620)` |
| `**params` | 本轮没有可识别参数（`page` 是否生效未实测） | 不发查询参数 | `novel_related(29167620)` |

L：`/novels/29167620/related` → 200，`{"items":[],"page":1,"pageSize":12,"total":0,"totalPages":1,"hasMore":false}`。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    related = client.novel_related(29167620)
    # GET https://sakuria-api.syarolia.com/novels/29167620/related
    # L：200，{"items": [], "page": 1, "pageSize": 12, "total": 0, "totalPages": 1, "hasMore": false}
    print(related['page'], related['hasMore'], related['pageSize'], len(related['items']))
```

## 系列（1 个方法）

### series_show

`series_show(series_id, **params)` → 路由 `GET /series/{series_id}`。返回**裸对象**，键包含 `id`、`title`、`caption`、`total`、`author`、`items`、`hasMore`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `series_id` | 系列编号，进 URL 路径 | 必填 | `series_show(198059)` |
| `page` | 页码；本轮 `page=1` → 200 | 未实测 | `page=1` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：`/series/198059?page=1` → 200，`total` 219、`items` 30 项、`hasMore:true`；`/series/12064` → 200，`items:[]`、`total:7`、`hasMore:false`。两个都不是同一套编号时行为不同的原因未实测（见边界）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    series = client.series_show(198059, page=1)
    # GET https://sakuria-api.syarolia.com/series/198059?page=1
    # L：200；{id, title, caption, total=219, author, items(30 项), hasMore=true}，没有 page/pageSize 键。
    print(series['id'], series['title'], series['total'], series['hasMore'], len(series['items']))
    for illust in series['items']:
        print(illust['id'], illust['pages'], len(illust.get('pageUrls', [])))
```

## 特辑（2 个方法）

### spotlight_list

`spotlight_list(**params)` → 路由 `GET /spotlight`。返回信封 `{items, page, pageSize, hasMore}`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `page` | 页码；本轮 `page=1` → 200 | 未实测 | `page=1` |
| `lang` | 语言；本轮 `lang=zh-cn` → 200（其它取值未请求） | 未实测 | `lang='zh-cn'` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：`?page=1&lang=zh-cn` → 200，20 项、`pageSize:12`、`hasMore:true`。**只请求了一页，不能说 `hasMore` 恒 `true`**。item 本轮观察到的键：`id`、`title`、`caption`、`tag`、`coverSvg`、`cover`、`tags[{id,name}]`、`date`、`articleUrl`、`works`；`cover` 是字符串地址，`works` 本轮是空数组。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    spotlight = client.spotlight_list(page=1, lang='zh-cn')
    # GET https://sakuria-api.syarolia.com/spotlight?page=1&lang=zh-cn
    # L：200；items 20 项、pageSize=12、hasMore=true；每项含 id/title/cover/tags/articleUrl 等键。
    print(spotlight['pageSize'], spotlight['hasMore'], len(spotlight['items']))
    for item in spotlight['items']:
        print(item['id'], item['title'], item['cover'], item['articleUrl'])
```

### spotlight_show

`spotlight_show(spotlight_id, **params)` → 路由 `GET /spotlight/{spotlight_id}`。返回**裸对象**。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `spotlight_id` | 特辑编号，进 URL 路径 | 必填 | `spotlight_show(11971)` |
| `lang` | 语言；本轮 `lang=zh-cn` → 200 | 未实测 | `lang='zh-cn'` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：`/spotlight/11971?lang=zh-cn` → 200，键 `id`、`title`、`date`、`description`、`cover`、`tags`、`works`、`articles`、`relatedLatest{tag_name,tag_id,items}`、`relatedRecommend{…}`、`articleUrl`；`articles` 本轮 19 条（每项 `{id, title, thumbnail}`），`works` 与两个 related 的 `items` 本轮都是空数组；本轮 `cover` 是 `/p/embed.pixiv.net/pixivision/zh/a/11971/ogimage.jpg`——**不在 `/img/` 前缀下**。`/spotlight/0` → **503** `{"error":"upstream temporarily unavailable","retryable":true}`（不是 404）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    article = client.spotlight_show(11971, lang='zh-cn')
    # GET https://sakuria-api.syarolia.com/spotlight/11971?lang=zh-cn
    # L：200；articles 19 条，works 为空数组，relatedLatest/relatedRecommend 的 items 都为空。
    print(article['id'], article['title'], article['articleUrl'], len(article['articles']))
    print([illust['id'] for illust in article['works']])
```

## 标签（2 个方法）

### tag_illusts

`tag_illusts(tag, **params)` → 路由 `GET /tags/{tag}`，标签作为路径段（客户端按路径段规则编码，`safe=''`，所以 `初音ミク` 会写成 `%E5%88%9D%E9%9F%B3%E3%83%9F%E3%82%AF`）。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `tag` | 标签名，进 URL 路径 | 必填 | `tag_illusts('blue')` |
| `page` / `size` | 本轮 `page=1&size=24` → 200 | 未实测 | `page=1, size=24` |
| `**params` | 本轮没有其它可识别参数（搜索类参数是否仍被识别未实测） | 不发查询参数 | 同上 |

L：`/tags/blue?page=1&size=24` → 200，信封 `{items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}`（本轮 `total` 48、`totalPages` 4、`nextPage` 4、`hiddenCount` 65）25 项；同参数 `search/illust` 本轮 29 项、与它交集 25 项——**两次请求不在同一时刻，不能称两者完全等价**。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    tagged = client.tag_illusts('blue', page=1, size=24)
    # GET https://sakuria-api.syarolia.com/tags/blue?page=1&size=24
    # L：200；items 25 项，信封与 search/illust 同键。
    print(tagged['pageSize'], tagged['hasMore'], len(tagged['items']))
    print([illust['id'] for illust in tagged['items']])
```

### tag_search

`tag_search(**params)` → 路由 `GET /tags/search`。

| 参数 | 取值与含义（L） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `q` | 本轮 `?q=blue&size=2` 与 `?size=2` 返回**完全相同**的 JSON（各 11 项）：这两个请求里 `q` 没有影响 | 未实测 | `q='blue'`（本轮无影响） |
| `size` | 每页条数；本轮 `size=2` → 200 | 未实测 | `size=2` |
| `**params` | 本轮没有其它可识别参数 | 不发查询参数 | 同上 |

L：`?size=2` → 200，信封 `{items, page, pageSize, total, totalPages, hasMore, nextPage, hiddenCount}`，11 项。本轮**没有**请求标签补全/联想类路由，因此不能断言站点没有这类接口（见边界）。

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    listing = client.tag_search(size=2)
    # GET https://sakuria-api.syarolia.com/tags/search?size=2
    # L：200；items 11 项；带上 q=blue 时完整 JSON 与本请求相同。
    print(listing['pageSize'], listing['hasMore'], len(listing['items']))
```

## 账号方法（17 个，全部需登录，返回结构未实测）

这 17 个方法只拼 `/me/*` 路由并把 `**params` 原样作为查询串发送，不做任何额外处理。**每条都需要可用的 `access_token`；本库没有账号，除 `me_likes` 外其余 16 条本轮都没有请求过，返回结构、字段名、参数是否生效全部未知。** 涉及 `x-sakuria-data-contract` 的路径（L：`/me/likes` 不带头 426、带头 401）用通用入口显式带头——包装方法不接 `headers`。

| 方法 | 路由 | 参数 | 返回 |
| :--- | :--- | :--- | :--- |
| `me(**params)` | `GET /me` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_capabilities(**params)` | `GET /me/capabilities` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_bookmarks(**params)` | `GET /me/bookmarks` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_likes(**params)` | `GET /me/likes` | 需登录；只接 `**params`；**L：不带 `x-sakuria-data-contract` → 426 `upgrade_required`（`requiredDataContract:2`），带上头 → 401 `sakuria_session_required`** | 未知（未取得认证后样本） |
| `me_following(**params)` | `GET /me/following` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_notifications(**params)` | `GET /me/notifications` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_history(**params)` | `GET /me/history` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_settings(**params)` | `GET /me/settings` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_illusts(**params)` | `GET /me/illusts` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_novels(**params)` | `GET /me/novels` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_series(**params)` | `GET /me/series` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_credits(**params)` | `GET /me/credits` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_plus(**params)` | `GET /me/plus` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_subscription(**params)` | `GET /me/subscription` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_favorites(**params)` | `GET /me/favorites` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_search_history(**params)` | `GET /me/search-history` | 需登录；只接 `**params`，未实测 | 未知 |
| `me_recommend(**params)` | `GET /me/recommend` | 需登录；只接 `**params`，未实测 | 未知 |

登录/注册端点没有封装，本轮也没有请求：输入文档说它们在 API 主机上全部 404，注册入口在 Cloudflare 挑战保护的 Web 主机上（见边界）。本库不提供登录方法，也不索要账号。

```python
from anybooru import AnybooruHTTPError, Sakuria

with Sakuria('sakuria', access_token='<token>') as client:
    try:
        me = client.me()
        # GET https://sakuria-api.syarolia.com/me
        # 需登录；返回结构未实测。没有有效 token 时（输入文档）401 {"error": "Unauthorized"}。
        print(me)
    except AnybooruHTTPError as error:
        print(error.http_code, error.url, repr(error.body))

# 需要数据契约头的路径走通用入口（包装方法不接 headers）
with Sakuria('sakuria', access_token='') as client:
    try:
        likes = client.request('GET', '/me/likes', headers={'x-sakuria-data-contract': '2'})
        # GET https://sakuria-api.syarolia.com/me/likes
        # L 匿名观察：不带头 426 upgrade_required；带头后 401 sakuria_session_required。
        print(likes)
    except AnybooruHTTPError as error:
        print(error.http_code, repr(error.body))
```

## 公共对象

下面只写本轮 L 实际观察到的键；`?` 表示该键在本轮样本里出现过也缺过（缺键不等于空值）。输入文档里的其它字段候选见[边界与未实测](#边界与未实测)。

### 插画对象

出现在 `/illust/{id}`、`/search/illust.items`、`/tags/{tag}.items`、`/users/{id}/illusts.items`、`/users/{id}/bookmarks.items`、`/series/{id}.items`。L 观察到的键：

| 字段 | 类型 | L 说明 |
| :--- | :--- | :--- |
| `id` | str | 作品编号 |
| `title` | str | 标题 |
| `type` | str | 本轮样本值 `illust`、`manga` |
| `pages` | int | 图片张数 |
| `description` | str? | 本轮部分样本出现（用户作品列表、收藏） |
| `urls` | object | `{thumb, small, regular, original, w, h}`，前四个是地址字符串 |
| `pageUrls` | array? | 本轮多页样本出现，元素与 `urls` 同构、按页序 |
| `author` | object | [用户对象](#用户对象)（列表里没有 `banner`） |
| `tags` | array | `{name, translated?, alt}`；本轮有只有 `{name, alt}` 的样本 |
| `stats` | object | `{likes, bookmarks, views, comments}`，4 个 int |
| `publishedAt` | str | ISO8601，带 `+09:00` |
| `publishedDays` | int | 距发布天数 |
| `isAi` / `isR18` | bool | 本轮 `isAi` 同时有 `true/false`；`isR18` 样本为 `false` |
| `xRestrict` | int | 本轮样本 `0` |
| `sl` | int | 本轮样本 `2`；语义未实测 |

### 用户对象

`/users/{id}` 与各处 `author` 共用；L 观察到 `id`、`name`、`handle`、`accent`、`avatar`（str）、`stats{followers, following, works, totalLikes, totalBookmarks}`（int）；`/users/{id}` 另有 `banner`（地址字符串）与 `social[]`（每项 `{kind, url, label}`，本轮 1 条）。`stats` 的计数本轮不是 0（`following:11`、`works:8`、`totalBookmarks:13`）。

### 小说对象

**列表小说对象**（本轮非空样本来自 `/search/novel.items` 与 `/users/{id}/novels.items`）：L 观察到的键：`id`、`title`、`author`、`tags`、`textLength`、`coverSvg`、`cover{thumb, small, regular, original, w, h}`、`stats{likes, bookmarks, views, comments}`、`publishedAt`、`publishedDays`、`isAi`、`isR18`、`xRestrict`、`sl`、`series{id, title}`，另有 `caption?`。**没有正文 `text`。**

**详情对象**（`/novels/{id}`）在 Novel-lite 之外还有 `text`、`document{text, uploadedImages, pixivImages}`、`caption`、`captionHtml`。本轮样本：`textLength` 99、顶层 `text` 是空串、`document.text` 是 4 行 `[uploadedimage:<id>]`、`uploadedImages` 有 4 个对象（`{id, urls{thumb, small, regular, original}, visible, isR18, xRestrict, sl}`）、`pixivImages` 是空对象；Novel-lite 的字段在本样本里照常出现。

### 特辑对象

列表项见 [spotlight_list](#spotlight_list)，详情见 [spotlight_show](#spotlight_show)：本轮观察到 `cover` 是地址字符串、`tags` 是 `{id, name}` 数组、`articles` 是 `{id, title, thumbnail}` 数组；详情样本的 `cover` 是 `/p/embed.pixiv.net/…`，与 `urls` / `avatar` 那类 `/img/` 路径不同形。

## 实测与输入文档的矛盾

集中见[契约附注的矛盾表](sakuria-contract-notes.md#实测与输入文档的矛盾)：小说 `type` 的忽略说法、`ai=exclude` 的状态码、`text/document.text` 等同说法被本轮响应否定；标签路由完全等价未复现。`user_search.total` 则与输入“本页条数”一致，不应误改成累计值。

## 边界与未实测

以下全部是**未实测**：输入文档的候选、本轮没有请求的取值、或本轮没有复现的结论。不当作契约。

* **默认值**：除 `search/illust` 不带 `page` 时返回 `page:1` 外，各路由的默认页码、默认页大小、默认排序都没有实测（输入文档说插画搜索 `size` 默认 24、`sort` 默认 `new`，未复现）。
* **枚举与上限**：`size` 只证 `1` 与 `48` 被接受、`0` 与 `49` 被拒；`sort` 只证 `popular` 被接受；`type` 只证 `illust` → 401；`mode` 只证 `text` → 400；`lang` 只用过 `zh-cn`；`hiddenCount` 的含义、`sl` 的语义、`xRestrict` 的取值集合都没有实测。
* **参数忽略**：只证过 `search/illust` 的 `limit=__invalid__` 一次仍返回 200。输入文档列的「其余参数静默忽略」（`pageSize`/`per_page`/`offset`/`tags`/`r18`/`isAi`/`userId` 等）本轮没有复现；`user_bookmarks` 的 `cursor`/`limit`/`offset`、`user_illusts` 的 `pageSize`/`sort`/`order` 同理。
* **末页标志**：本轮没有跑到任何列表的末页，`hasMore=false` 与 `nextPage=null` 作为终止标志未实测。
* **错误码与错误措辞**：本轮只观察到 `invalid_search_filter`（`field` 为 `page`/`size`/`sort`/`mode`）、`unsupported_filter_for_scope`、`auth_required`、`upgrade_required`、`sakuria_session_required`、`illust not found`、`invalid id`、`upstream temporarily unavailable`。输入文档里的其它措辞（`invalid user id` / `invalid novel id` / `invalid series id` / `invalid spotlight id` / `bad path` / `{"error":"Not Found","path":…}` / 403 付费 / 其它 404 与 401 正文）本轮没有请求到，`/illust/abc` 之外的非法 id 都没试。
* **`/me/*`**：除 `me_likes` 的 426 → 401 外，17 个方法里的另外 16 个本轮一条也没有请求，返回结构、参数与错误行为全部未知；登录、注册、JWT 的获取与刷新也没有实测。
* **登录/注册端点**：输入文档说 API 主机上 `/auth/*`、`/login`、`/register`、`/session`、`/token`、`/oauth/token` 全部 404，注册入口在 Cloudflare 挑战保护的 Web 主机上——本轮没有复测。
* **媒体**：本库不下载媒体。输入文档说 `/img/` 是匿名可用的图片代理、`urls.*` 等是 `/img/` 开头的相对路径、拼上基地址才是完整 URL、只应用响应里给的尺寸、找不到文件返回 200 + SVG 占位图、另两个图床主机需要 token——本轮**没有对任何图片地址发过请求**，这些行为未实测。L 只在 JSON 里见到地址字符串：多数以 `/img/` 开头，但 `/spotlight/{id}` 的 `cover` 是 `/p/embed.pixiv.net/…`，所以「地址一律在 `/img/` 下」不成立。
* **写接口与付费面**：输入文档说 CORS 声明允许写动词、插画搜索的 `type=illust|manga|ugoira`、`ai=exclude`、`sort=popular&page>=2`、`ratio` 与小说搜索的 `mode` 属 Sakuria+、另有一条会员主机；本轮只证了插画 `type=illust` 401 与小说 `ai=exclude` 401，其余没有样本，也没有探测过写路由。
* **非空样本缺失的结构**：`/users/{id}/followers` 的非空 item、`/users/{id}/series` 的 item、`/novels/{id}/comments` 的评论对象（含 `stampUrl`/`stampId`）、`/novels/{id}/related` 的 item、`/spotlight/{id}` 的 `works` item 都没有非空样本。
* **其它未定**：`/spotlight/{id}` 顶层 `caption`/`coverSvg`/`tag` 是否存在、`/novels/{id}/series` 等子路径是否存在、限流与配额（输入文档说没有任何 `RateLimit-*`/`Retry-After` 头）、`lang` 与 `Accept-Language` 对正文的影响、特辑 id 不存在返回 503 而非 404 的原因，都没有实测。

[客户端用法](sakuria.md) · [能力入口](sakuria-capabilities.md) ·
[依据与差异](sakuria-contract-notes.md) · [验证记录](verification.md#sakuria匿名只读实测2026-09-19)
