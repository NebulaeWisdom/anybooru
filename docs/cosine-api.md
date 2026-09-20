# Cosine 方法参考

Cosine Gallery（`https://pic.cosine.ren`）是 Telegram 频道的配套图站，不是本包已有的任何 booru 引擎。它是 Next.js + Prisma + Meilisearch 的自研应用，路由、信封、编号与错误文案都是自己的一套。没有官方 API 文档、没有 OpenAPI。

公开结论来自两类依据：

* 本轮 69 次匿名只读 `GET`（串行、相邻 ≥1.3 秒、各发一次、不重试、不跟随跳转、不下载媒体），标 **L**。
* 上游前端公开仓库（`SomeACG/SomeACG-Next`）六个文件的只读阅读，标 **S**：`src/app/api/tags/route.ts`、`src/app/api/random/route.ts`、`src/app/api/search/route.ts`、`src/app/api/search/admin/route.ts`、`src/app/api/artwork/revalidate/route.ts` 与 `src/lib/search/indexing-service.ts`。本轮没有 clone 仓库，每个文件只读一次，只写文件路径、不编行号；源码也不是站点当前部署版本的证明。

接入时收到的《Cosine Gallery 接口文档（综合版）》只作候选，标 **T**。未被 L 或 S 支持的参数默认值、枚举、上限、媒体规则与源码实现细节一律集中在[边界与未实测](#边界与未实测)，不当契约写。

本页列出 `Cosine` 的全部 **13 个原生方法**：**11 个匿名只读 `GET`** 加 **2 个 `POST`**（`artwork_revalidate`、`search_index_admin`，本轮一次都没有发过），另有通用入口 `request(method, path, *, params=None, data=None, headers=None, response_format="json")`。客户端怎么构造、`last_call` 怎么看、`revalidate_secret` 从哪来见[客户端用法](cosine.md)；「想做什么 → 用哪个方法」见[能力入口](cosine-capabilities.md)；依据出处、矛盾与排除项见[依据与差异](cosine-contract-notes.md)；真实请求记录见[验证记录](verification.md#cosine匿名只读实测2026-09-20)。

## 依据标注与阅读方式

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **L** | 本轮 69 次直接 HTTP 观察（串行、相邻 ≥1.3 秒、不重试、不跟随跳转、不下载媒体；每次都带 `Origin`） | 对应路由的状态、`Content-Type`、信封、字段名与类型，以及部分参数的默认值、上限与被夹后的回显。不等于每个 Python 方法都执行过 |
| **S** | 上游前端公开仓库的 6 个文件只读阅读（路径同上） | 这些文件里的默认值、夹取、参数解析、分支与响应形状：`/api/tags` 的 `count` 算法、`/api/random` 的 `count` 夹取与分页查询、`/api/search` 的 `q`/`limit`/`offset`/`sort`/`tags`/`r18` 处理、`/api/search/admin` 的 action 分支、`/api/artwork/revalidate` 的密钥比较、索引报告里 `lastSyncTime` 的实现。只写文件路径、不编行号；源码不是部署版本的证明，也不等于对应 `POST` 被执行过 |
| **T** | 输入文档《Cosine Gallery 接口文档（综合版）》（自称来自对同一主机的匿名实测并交叉核对了站点前端源码） | 参数默认值全集、枚举与上限、媒体取图要求、字段的上游语义、数据表名与表结构。没有 L 或 S 支持的都不是契约 |

本轮 69 个响应的状态分布是 `200`×57、`400`×2、`404`×3、`500`×7；格式分布是 68 个 `application/json` 加 1 个 `application/xml; charset=utf-8`（`GET /feed.xml`）。样本里没有 `403`，也没有任何 `Access-Control-Allow-Origin` 或 `RateLimit-*` 头——只能说本轮样本没有这些头，不能承诺站点没有配额或允许跨域。

样本里的数字（`total` 4953、标签 2128 个、某项 `count`、`processingTimeMs` 等）都只是当时的读数，不保证稳定；本页把它们当例子写，不当常量。

## 通用约定

* **基地址**：`https://pic.cosine.ren`，来自包内配置 `sites.cosine.url`。本页路由都补在它之后，JSON 路由在 `/api` 下，另有 `feed.xml` 这一条非 JSON 路由。
* **方法**：11 个原生方法发 `GET`，2 个发 `POST`。查询参数放查询串；作品编号作为一个路径段。
* **认证**：所有读路由本轮匿名可直接拿到 `200`，客户端默认不带任何凭据头，也不做登录。**S**：`src/app/api/search/admin/route.ts` 的 `POST` 分支也没有任何鉴权检查，只按 `action` 分支执行。唯一的凭据是 `revalidate_secret`，它只出现在 `artwork_revalidate` 的 JSON 正文里，不会变成请求头，其它路由也收不到它；**S**：该路由把 `secret` 与服务端的 `process.env.REVALIDATE_SECRET` 比较，不等就 `401`。包内配置该字段默认为空字符串，空值照发不误，由站点决定是否拒绝。
* **参数编码**：`params` 走共享编码——`None` 值不发送、布尔写成小写 `true`/`false`、嵌套映射写成 `key[child]`、序列写成重复的 `key[]` 键。库不钳位、不补默认值、不校验取值、不改参数名，站点拒绝什么就返回什么。
* **正文**：`data` 原样作为 JSON 正文（走 requests 的 `json` 参数），`None` 会序列化成 JSON `null`，不清理、不改名、不经过查询编码。
* **返回**：JSON 原样返回，不拆信封、不改字段名、不转换类型。2xx 空正文返回 `None`；2xx 但正文不是 JSON 抛 `AnybooruAPIError`；非 2xx 抛 `AnybooruHTTPError`（带 `http_code` / `url` / `body` / `data`）。库不重试、不降级、不做格式嗅探。`client.last_call` 保留 `API`、`url`、`status_code`、`status`、`headers`。
* **`response_format`**：显式给出，`'json'`（默认）解析 JSON，`'xml'` 返回 `response.text` 原文；传其它值直接 `KeyError`，不看 `Content-Type` 猜格式。13 个方法里只有 `feed()` 用 `'xml'`。
* **图片**：本库不下载任何图片字节，也没有取字节的方法；`rawurl` / `thumburl` / `latestImageThumb` 都是原样返回的地址字符串，怎么取见[媒体地址](#媒体地址只文档未下载)。
* **首次请求即真请求**：构造只读配置、不联网；任何方法被调用就真的发出去，没有预检、没有 dry run。

## 通用入口 `request()`

签名：`request(method, path, *, params=None, data=None, headers=None, response_format="json")`

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串，如 `'GET'` / `'POST'` | 必填（Python 报缺参） | `client.request('GET', 'api/tags')` |
| `path` | 站点相对路径，前导 `/` 会被去掉后拼在站点根之后 | 必填 | `client.request('GET', '/api/list', params={'page': 1, 'pageSize': 2})` |
| `params` | 查询参数字典，经共享编码后拼进查询串 | `None`，不发查询参数 | 见上一行 |
| `data` | JSON 正文字典，原样发送 | `None`，不发请求体 | `client.request('POST', 'api/artwork/revalidate', data={'artworkId': 1, 'secret': ''})`（**未执行过**） |
| `headers` | 本次请求的额外请求头字典，原样发送、不与任何东西合并 | `None`，只带客户端默认头 | `client.request('GET', 'api/tags', headers={'Accept-Language': 'zh-CN'})` |
| `response_format` | `'json'` 或 `'xml'`；`'xml'` 返回 `response.text` 原文 | `'json'` | `client.request('GET', 'feed.xml', response_format='xml')` |

`last_call['API']` 是去掉前导 `/` 后的路径原文；`'api/list'` 对应 `'api/list'`，`feed.xml` 对应 `'feed.xml'`。

```python
from anybooru import AnybooruHTTPError, Cosine

with Cosine('cosine') as client:
    body = client.request('GET', '/api/tags')
    # GET https://pic.cosine.ren/api/tags
    # L：200，裸数组 [{"tag": "甜妹", "count": 1309}, …]（本轮 2128 项，表头 X-Nextjs-Cache: HIT）
    print(len(body), body[0])

with Cosine('cosine') as client:
    try:
        client.request('GET', '/api/tag')
        # L：400 {"error": "标签参数缺失"}——缺 tag 时站点自己报错，库不会本地拦下
    except AnybooruHTTPError as error:
        print(error.http_code, error.url, error.data)
        # 400 https://pic.cosine.ren/api/tag {'error': '标签参数缺失'}
```

## 四种信封（外加画师资料一个裸对象）

同一个站点混用了四套外壳，外加 `/api/artist` 的一个分支；看错外壳会以为拿到了空结果。本库一个都不拆，下面写的是你拿到的原文形状。

| 外壳 | 哪些路由 | 形状 |
| :--- | :--- | :--- |
| **A** superjson | `artwork_show()`、`image_random()` | `{"json": …, "meta": {"values": {…}}}` |
| **B** 列表 | `image_list()`、`artist_images()` 的列表分支 | `{"images": […], "total": N}` |
| **B′** 画师榜 | `artist_list()` | `{"artists": […], "total": N, "hasNextPage": bool}` |
| **C** 结果 | `search()`、`search_suggestions()`、`search_index_status()` | `{"success": true, "data": {…}}` |
| **D** 裸数组 | `tag_images()`、`tag_list()` | `[{…}, …]` |
| **E** 裸资料对象 | `artist_images(..., infoOnly='true')` | `{"author": …, "authorid": …, "platform": …, "artworkCount": N}` |

* **A（superjson）**：真正的数据在 `json` 里。`json` 可能是对象，也可能是数组——只有 `image_random()` 会给出数组。`meta.values` 是 superjson 的类型表：单对象时本轮键是 `userid`、`authorid`（`bigint`，正文里已是字符串）与 `create_time`（`Date`，正文里已是 ISO 串）；数组时键带下标（如 `"14.authorid"`），且 `image_random(count=100)` 的样本里还多出一个 `meta.referentialEqualities`（如 `"9.authorid": ["18.authorid"]`），所以不要假定 `meta` 里只有三个键。Python 调用方读 `body["json"]` 即可，`meta` 可以忽略。
* **B / B′**：只有 `images`（或 `artists`）与 `total`，没有 `success`、没有 `meta`。`artist_list()` 多一个 `hasNextPage` 布尔。
* **C**：`data` 里才是结果。出错时是 `{"success": false, "error": …, "message": …}` 加 HTTP `500`。
* **D**：既没有信封也没有 `total`，空结果就是 `[]`。
* **E**：`artist_images(platform, authorid, infoOnly='true')` 返回的是一个裸资料对象，不是 B、不是 D、也不是只含一条的列表。

错误体是另一套形状，与信封无关：A/B/B′/D 路由用 `{"error": "中文说明"}`，`/api/search` 系用 `{"success": false, "error": …}`（见[错误与状态码](#错误与状态码l)）。

## 作品对象（`images[]` / `json` / 裸数组的元素）

这是 A、B、B′ 之外的三种列表与详情共用的对象；`search()` 的命中是它的瘦身子集，见下一节。字段名、类型与样本取值都来自 L；「上游语义」一列是 T（输入文档对数据来源的解释，本轮没有逐条复核）。

```json
{
  "id": 5003,
  "userid": "6030777595",
  "username": "@cosine_yu",
  "create_time": "2026-09-18T11:49:24.590Z",
  "platform": "twitter",
  "title": "ヴォジャニャーツァ\n#原神",
  "page": 1,
  "size": null,
  "filename": "2100902205171937298_1.jpg",
  "author": "torino",
  "authorid": "162416678",
  "pid": "2100902205171937298",
  "extension": "jpg",
  "rawurl": "https://pbs.twimg.com/media/HSfnUtFakAAhHtG.jpg?name=orig",
  "thumburl": "https://pbs.twimg.com/media/HSfnUtFakAAhHtG.jpg?name=medium",
  "width": 1600,
  "height": 2429,
  "guest": false,
  "r18": false,
  "ai": false,
  "tags": ["原神", "精选", "壁纸"]
}
```

| 字段 | 类型 | 观测到的取值 | 含义（上游语义为 T） |
| :--- | :--- | :--- | :--- |
| `id` | number | 5003、1、3840 | 站内自增行号，`/artwork/{id}` 页面用的就是它；不是上游编号 |
| `userid` | string | 本轮样本都是 `"6030777595"` | 投稿人（Telegram 侧）id，不是画师 |
| `username` | string | `"@cosine_yu"` | 投稿人用户名，带 `@` |
| `create_time` | string | `"2026-09-18T11:49:24.590Z"` | 入库时间（ISO 8601 UTC），不是作品发布时间 |
| `platform` | string | `"twitter"`、`"pixiv"` | 来源平台；本轮只见过这两个值 |
| `title` | string | 可含换行、可为 `""` | Pixiv 是作品标题；Twitter 是推文正文 |
| `page` | number | Twitter `1`、Pixiv `0` | 同一作品里的第几张；`file` 名里的 `_p0`/`_1` 与它对应 |
| `size` | number \| null | 本轮新行样本都是 `null`，`id=1` 是 `675622` | 原图字节数；只有 2023 年的老行样本有值 |
| `filename` | string | `"148746199_p0.jpg"` | 落盘文件名 |
| `author` | string | `"torino"`、`"まころん夏コミC48土お52日"` | 画师名（与 `username` 不是一个人） |
| `authorid` | string | `"162416678"` | 画师 id（bigint 转字符串） |
| `pid` | string | `"2100902205171937298"` | 上游作品编号（Pixiv illust id / Tweet id），字符串 |
| `extension` | string | `"jpg"`、`"png"` | 不带点的后缀 |
| `rawurl` | string | 见[媒体地址](#媒体地址只文档未下载) | 原图地址，原样返回 |
| `thumburl` | string | 见[媒体地址](#媒体地址只文档未下载) | 缩略图地址，原样返回 |
| `width` / `height` | number | `1600` / `2429` | 原图宽高（像素） |
| `guest` | boolean | 新行 `false`，`id=1` 是 `true` | 老数据的游客投稿标记 |
| `r18` | boolean | `false`、`true` | 是否 R18 |
| `ai` | boolean | `false` | 是否 AI 生成 |
| `tags` | string[] | `["原神", "精选", "壁纸"]`、`["#RuanMei", "…"]` | 标签数组；`#` 前缀各路由不一致、可能含重复项 |

三个必须记住的点：

1. **同一 `pid` 会有多行**（`page` 不同），例如 `pid` `1740597132367909104` 的 `id=2`、`id=3` 是两条独立记录。
2. **`tags` 可能重复、`#` 前缀按路由不同**。`artwork_show()` 保留库内原样——`id=1` 的 8 项只有 `#RuanMei`、`#ルアン・メェイ`、`#スターレイル`、`#HonkaiStarRail` 4 个不同值，`id=3840` 的 16 项只有 8 个不同值（4 项带 `#`、4 项不带）；`image_list()` 与 `tag_images()` 的样本去掉了 `#`，`image_random()` 则只是不补 `#`（存什么发什么，见该节）。做匹配、计数、展示前请自己 `lstrip('#')` 再去重。
3. **`size` 与 `guest` 描述的是入库年代，不是图片本身**；用它们判断图片质量会翻车。

## 计数字段的三个口径（不要互相换算）

| 来源 | 字段 | 口径 | 本轮样本 |
| :--- | :--- | :--- | :--- |
| `image_list()` / `artist_images()` | `total` | 该查询在库里的行数 | 全库 `4953` |
| `search()` | `data.total` | 索引的估算命中数（**S**：`estimatedTotalHits`），被夹过 | 大面积命中一律 `1000`；`q=初音` 是 `255` |
| `tag_list()` | `count` | 标签记录行数（**S**：按 tag 分组数行，先去掉前导 `#` 再合并，再降序） | `GenshinImpact` 137、`RuanMei` 9 |
| `tag_images()` | 无 | 裸数组长度 = 本页条数，不是命中总数 | `GenshinImpact` 一页 2 条 |

同一个标签的数字各不相同。以 `GenshinImpact` 为例：`tag_list()` 的 `count` 是 `137`，`search(tags='GenshinImpact')` 的 `total` 是 `166`，`tag_images('GenshinImpact')` 只有数组长度。再以 `RuanMei` 为例（同一轮样本）：`tag_list()` 的 `count` 是 **9**，`tag_images('RuanMei')` 返回 **10 张图**（覆盖 8 个 `pid`），这 10 张图的 `tags` 里该标签一共出现 **14 次**；搜索那边只回 **9 条 hits**。也就是：`count` 既不是图片数、也不是标签出现次数，三者不能互相换算。`search()` 还比库落后：`search_index_status()` 自报 `indexedImages` 3353 / `totalImages` 4953。要数库里的行数用 `image_list()` 的 `total` 或 `tag_images()` 翻页累计，不要用 `search()` 的 `total`。

## 作品列表与详情（3 个方法）

### image_list

签名：`image_list(**params)`。路由：`GET /api/list`。返回 **B** 信封。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | 整数，从 `1` 起 | 页码 | **L**：不带参数返回的是第一页（`id` `5003` 起） | `page=2` |
| `pageSize` | 整数 | 每页条数 | **L**：不带参数返回 10 条 | `pageSize=2` |
| `**params` | 其它名字原样进查询串 | — | 本轮只发过上表这两个名字 | — |

L：

* `GET /api/list?page=1&pageSize=2` → `200 {"images": [200-09-18/09-14 两条], "total": 4953}`；`page=2&pageSize=2` → `id` `5001`、`5000`（继续按 `create_time` 倒序）。
* 不带参数 → 10 条，`id` 从 `5003` 递减到 `4994`；`pageSize=100` → 100 条。
* `pageSize=0` → `200 {"images": [], "total": 4953}`。
* `pageSize=-1` → `200`，但只返回 **1 条**（`id=1`，最旧那条）。不要用负数。
* `page=0` / `page=-1` → `500 {"error": "获取图片列表失败"}`。
* `page=100000&pageSize=2` → `200 {"images": [], "total": 4953}`（超末页是空数组，不是错误）。
* `tags` 已去 `#`；`rawurl` / `thumburl` 是数据库原值（Pixiv 行是 `i.pximg.net`，不做 `piv.cosine.ren` 替换）。

排序、`pageSize` 上限、`page` 与 `pageSize` 的其它越界值见[边界与未实测](#边界与未实测)。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    page = client.image_list(page=1, pageSize=2)
    # GET https://pic.cosine.ren/api/list?page=1&pageSize=2
    # L：200 {"images": [2 条], "total": 4953}
    for image in page['images']:
        print(image['id'], image['platform'], image['author'], image['filename'])
    print(page['total'])

with Cosine('cosine') as client:
    beyond_last = client.image_list(page=100000, pageSize=2)
    # L：200 {"images": [], "total": 4953}——末尾用空数组判断，没有错误码
    print(beyond_last['images'], beyond_last['total'])
```

### artwork_show

签名：`artwork_show(artwork_id)`。路由：`GET /api/artwork/{artwork_id}`。返回 **A** 信封。`artwork_id` 被 `quote(str(artwork_id), safe='')` 编成一个路径段，不做数字校验。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `artwork_id` | 站内行号；传字符串会先 `str()` 再编码 | 要取的作品 | 必填 | `artwork_show(1)`、`artwork_show(3840)` |

L：

* `GET /api/artwork/1` → `200 {"json": {作品对象}, "meta": {"values": {"userid": ["bigint"], "create_time": ["Date"], "authorid": ["bigint"]}}}`。该样本 `size` 是 `675622`、`guest` 是 `true`（2023 年的老行），`tags` 8 项含重复且带 `#`，`rawurl` 是 `…?format=jpg&name=orig`、`thumburl` 是 `…?format=jpg&name=large`。
* `GET /api/artwork/3840` → `200`，`size` `null`、`guest` `false`、`extension` `png`，`tags` 16 项（8 个不同值，其中 4 项带 `#`）。
* `GET /api/artwork/999999999` → `404 {"error": "未找到该作品"}`。
* `GET /api/artwork/abc` → `500 {"error": "服务器错误"}`——非数字是 500 不是 400。
* 详情不带 `originUrl` / `authorUrl`（只有 `image_random()` 带），也不做 `piv.cosine.ren` 替换。

```python
from anybooru import AnybooruHTTPError, Cosine

with Cosine('cosine') as client:
    artwork = client.artwork_show(3840)['json']
    # GET https://pic.cosine.ren/api/artwork/3840
    # L：200 {"json": {…}, "meta": {"values": {…}}}
    print(artwork['id'], artwork['pid'], artwork['page'], artwork['size'])
    print(sorted(set(tag.lstrip('#') for tag in artwork['tags'])))

with Cosine('cosine') as client:
    try:
        client.artwork_show('abc')
    except AnybooruHTTPError as error:
        # L：500 {"error": "服务器错误"}
        print(error.http_code, error.data)
```

### image_random

签名：`image_random(**params)`。路由：`GET /api/random`。返回 **A** 信封，1 条时 `json` 是对象、≥2 条时是数组（本库不替你统一）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `count` | 整数 | 要几张 | **S**：`parseInt` 后 `Math.min(Math.max(count,1),20)`；**L**：不带参数、`count=0`、`count=-5` 都回 1 条（`json` 是对象） | `count=3` |
| `**params` | 其它名字原样进查询串 | — | 本轮只发过 `count` | — |

L：

* `GET /api/random` → `200`，`json` 是对象（`id=3408` 的 Twitter 行）；`count=1` → 对象（`id=1666`，Pixiv）；`count=3` → 数组 3 条（`id` `2042`、`2741`、`3927`，升序）；`count=100` → 数组 20 条（S 的夹取，不是 100）。
* 顺序没有保证：S 的实现是 `findMany({where:{id:{in:randomIds}}})`，没有 `orderBy`；本轮 3 条与 20 条的样本 `id` 都是升序，那只是样本，不要据此承诺「按主键排序」。
* `count=0`、`count=-5` → 都是单对象；`count=abc` → `404 {"error": "未找到图片"}`。
* 比其它路由多两个字段：`originUrl`（Twitter 样本 `https://x.com/_/status/1961772823841738792`、Pixiv 样本 `https://www.pixiv.net/artworks/129597145`）与 `authorUrl`（`https://x.com/i/user/1502621932717424640`、`https://www.pixiv.net/users/33844486`）。
* Pixiv 行的 `rawurl` / `thumburl` 被站点换成 `piv.cosine.ren` 同路径（`https://piv.cosine.ren/img-original/img/2025/04/23/00/00/13/129597145_p0.jpg`）。
* `tags` 最多保留单个前导 `#`，但不是统一加 `#`：S 的处理是 `tag.replace(/#+/g, '#')`，也就是把连续的 `#` 收成一个（不限于行首）；本轮 Twitter 样本是 `["#Furina", "#GenshinImpact", …]`；两个 Pixiv 样本一个 6 项全带 `#`（`["#初音未来", "#VOCALOID", "#插画", …]`），另一个既有不带 `#` 的（`"原创"`、`"女孩子"`、`"teatime"`）也有带 `#` 的（`"#大"`、`"#甜妹"`、`"#蓝色系"`）。也就是「存的是什么就发什么，只把连续 `#` 收成一个」，不要断言这条路由一定会给标签补 `#` 或去 `#`；连续 `#`（如 `##甜妹`）本轮没有样本。重复项同样不去。

```python
from anybooru import AnybooruHTTPError, Cosine

with Cosine('cosine') as client:
    one = client.image_random(count=1)['json']
    # GET https://pic.cosine.ren/api/random?count=1
    # L：200，"json" 是对象：{"id": 1666, "rawurl": "https://piv.cosine.ren/img-original/…", "originUrl": …}
    print(one['id'], one['originUrl'], one['authorUrl'])

with Cosine('cosine') as client:
    many = client.image_random(count=3)['json']
    # L：200，"json" 是数组 3 条；按主键返回，不要当随机顺序
    print([image['id'] for image in many])

with Cosine('cosine') as client:
    try:
        client.image_random(count='abc')
    except AnybooruHTTPError as error:
        # L：404 {"error": "未找到图片"}（不是 400）
        print(error.http_code, error.data)
```

## 搜索（2 个方法）

### search

签名：`search(**params)`。路由：`GET /api/search`。返回 **C** 信封，结果在 `data` 里。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `q` | 字符串 | 关键词 | **S**：缺省 `''`（空串会命中整个索引）；**L**：`data.query` 原样回显 | `q='初音'` |
| `limit` | 整数 | 每页条数 | **S**：缺省 `20`，且 `Math.min(parseInt(limit), 100)` 夹取；**L**：不带时 `data.limit` 回显 `20`，`limit=500` 回显 `100` | `limit=2` |
| `offset` | 整数 | 跳过条数 | **S**：缺省 `0`；**L**：不带时回显 `0`，`offset=100000` 回显 `1000` 且 `hits` 为空 | `offset=2` |
| `platform` | `pixiv` / `twitter` | 精确匹配平台 | 不过滤；**L**：`platform=unknown` 是 200 且 `hits` 为空、`total` 0 | `platform='twitter'` |
| `tags` | 逗号分隔的标签串 | 多标签 **AND** | 不过滤 | `tags='原神,GenshinImpact'` |
| `r18` | 字符串或 Python 布尔值 | `'true'` / `True` 选择 R18，其它已给值按非 R18 过滤（S；L 已测 `'false'` 与 `'1'`） | 不过滤；不能把同样被截到 1000 的计数当作过滤无效 | `r18=False` |
| `sort` | 排序表达式，如 `create_time:desc`、`width:asc` | 排序 | **S**：缺省 `create_time:desc`；**L**：`width:asc` 被接受、`bogus` 直接 500 | `sort='create_time:desc'` |
| `**params` | 其它名字原样进查询串 | — | 本轮只发过上表这些名字 | — |

`data` 字段（L）：`hits`、`query`、`total`、`limit`、`offset`、`processingTimeMs`；**S**：`total` 取的是 Meilisearch 的 `estimatedTotalHits`，所以它是索引里的估算命中数，既不是全库行数、也不保证精确。

`hits[]` 的每条不是上一节的作品对象，而是索引里的瘦身版：

| 在 `hits[]` 里 | 观测 |
| :--- | :--- |
| `id`、`pid`、`authorid`、`filename` | 都是字符串（`"2760"`） |
| `width`、`height` | 仍是数字（`1280`、`1810`） |
| `tags` | 字符串数组、本轮样本里都没有 `#`，可能含重复项 |
| `title`、`author`、`platform`、`thumburl`、`rawurl`、`create_time`、`r18`、`ai` | 字段集合不固定：`tags=RuanMei` 的 `id='38'` 没有 `title`，随后分页示例的 `id='2721'` 也缺这个键；不要补造标题或把一条命中的字段当成全部结果的固定结构 |
| `searchable_content` | 站点拼的检索文本（标题、作者、标签、平台等空格相连） |
| `_formatted` | 命中高亮的副本：字符串字段一致，但数字变成字符串（`"width": "1280"`），命中片段被包上 `<em>…</em>`（如 `_formatted.title` 里的 `給<em>初</em><em>音</em>未來`）；直接当纯文本渲染会把 `<em>` 显示出来 |
| **没有** | `userid`、`username`、`page`、`size`、`guest`、`extension` |

L：

* `GET /api/search?q=%E5%88%9D%E9%9F%B3&limit=2` → `200`，`hits` 2 条，`query` `"初音"`、`total` `255`、`limit` `2`、`offset` `0`、`processingTimeMs` `65`。
* `GET /api/search`（什么都不传）→ `200`，`hits` 20 条，`limit` 回显 `20`、`offset` `0`、`query` `""`、`total` `1000`。
* `limit=500` → `data.limit` 回显 **`100`**，`hits` 100 条，可见 `data.limit` 不是调用方传进去的值。
* `limit=2&offset=100000` → `data.offset` 回显 **`1000`**、`hits` `[]`、`total` `1000`。
* `limit=-1` → `500 {"success": false, "error": "Internal search error", "message": "Invalid value type at `.limit`: expected a positive integer, but found a negative integer: `-1`"}`；`offset=-5` 同形，`message` 换成 `.offset`。
* `sort=bogus` → `500 {"success": false, "error": "Internal search error", "message": "Invalid syntax for the sort parameter: expected expression ending by `:asc` or `:desc`, found `bogus`."}`——错误信息里带 Meilisearch 的英文原文，本库原样抛出。
* `sort=width:asc&limit=2` → `200`（该写法被接受，返回两条的 `width` 是 `471` 与 `480`）。
* `platform=pixiv` / `platform=twitter` → `200`、`total` 都是被夹的 `1000`；`platform=unknown` → `200`、`hits` `[]`、`total` `0`。
* `tags=GenshinImpact&limit=2` 与 `tags=genshinimpact&limit=2` → 都是 `total` `166`（S 是逐条 `tags.split(',')` 的比较，本轮证明它对大小写不敏感）；`tags=原神&limit=2` → `total` `510`；`tags=原神,GenshinImpact&limit=100` → `total` `160`，这 100 条逐条都同时带这两个标签（忽略大小写）——多标签是 AND。
* `r18=true&limit=100` → `total` **`7`**，且这 7 条命中的 `r18` 都是 `true`；`r18=false&limit=2` 与 `r18=1&limit=2` → 这四条命中的 `r18` 都是 `false`，但 `total` 与不传时一样是 `1000`，被上限盖住、分不出过滤差异。S：路由里 `r18` 不是 `null` 时按 `r18 === 'true'` 取值，所以「非 `'true'` 就是非 R18 过滤」。
* `tags=RuanMei&limit=100` → `hits` 9 条、`total` `9`，同一个 `pid` 会出现两行（索引一行 = 一张图）；其中一条命中（`id` `38`）连 `title` 键都没有——命中对象的字段集合不是固定的，不要假定每条都有标题。同一时刻 `tag_images('RuanMei')` 是 10 行（覆盖 8 个 `pid`）、那些行的 `tags` 里该标签一共出现 14 次。三个数字口径不同，不能互相换算。
* 因此不要把 `total` 当全库条数：本轮索引自报 3353 / 库 4953，`total` 只会被截到 1000（不会先给大于 1000 的数），库里有 10 张的标签搜索只回 9 条。

```python
from anybooru import AnybooruHTTPError, Cosine

with Cosine('cosine') as client:
    payload = client.search(q='初音', limit=2, platform='twitter', r18=False,
                            sort='create_time:desc')['data']
    # GET https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2&platform=twitter&r18=false&sort=create_time%3Adesc
    # 同组过滤参数实测：200，total=125；不带平台/r18过滤的初音搜索才是255。
    print(payload['query'], payload['total'], payload['processingTimeMs'])
    for hit in payload['hits']:
        print(hit['id'], sorted(hit), len(hit['tags']))

with Cosine('cosine') as client:
    try:
        client.search(limit=-1)
    except AnybooruHTTPError as error:
        # L：500 {"success": false, "error": "Internal search error", "message": "Invalid value type at `.limit`: …"}
        print(error.http_code, error.data['message'])
```

### search_suggestions

签名：`search_suggestions(**params)`。路由：`GET /api/search/suggestions`。返回 **C** 信封，`data` 是 `{"suggestions": [{"text": …, "type": …}, …], "query": …}`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `q` | 字符串 | 半截关键词 | **L**：不传等于空串 | `q='miku'` |
| `limit` | 整数 | 最多几条 | **L**：不带时回 10 条；上限未实测，见[边界与未实测](#边界与未实测) | `limit=2` |
| `**params` | 其它名字原样进查询串 | — | 本轮只发过 `q`、`limit` | — |

L：

* `q=miku&limit=2` → `200`，`suggestions` 2 条（`miku`、`MIKU`），两条 `type` 都是 `"general"`；`q=miku`（不带 `limit`）→ 10 条；`q=miku&limit=50` → **15 条**。
* `q=a`（1 个字符）→ `200 {"success": true, "data": {"suggestions": [], "query": "a"}}`。
* 联想词不是独立词库：`limit=50` 的样本里出现的是带 `#`、带换行的标题/标签串（如 `"Bottle Miku🫧\n#初音ミク"`），所以 `text` 可以直接展示，但别当纯标签用。
* `type` 在所有样本里都是 `"general"`；输入文档称它写死为这个值（T）。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    suggestions = client.search_suggestions(q='miku', limit=2)['data']['suggestions']
    # GET https://pic.cosine.ren/api/search/suggestions?q=miku&limit=2
    # L：200 {"success": true, "data": {"suggestions": [{"text": "miku", "type": "general"}, …], "query": "miku"}}
    print([item['text'] for item in suggestions])

with Cosine('cosine') as client:
    short = client.search_suggestions(q='a')['data']['suggestions']
    # L：200，suggestions 为空数组——太短的 q 不是错误
    print(short)
```

## 标签（2 个方法）

### tag_images

签名：`tag_images(tag, **params)`。路由：`GET /api/tag`。返回 **D** 裸数组，没有 `total`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag` | 字符串，完整标签、不带 `#` | 要查的标签，作为查询名 `tag` 发送 | 必填；缺了站点回 `400 {"error": "标签参数缺失"}` | `tag_images('GenshinImpact')` |
| `start` | 整数 | 跳过条数（是 offset，不是页码） | 未实测，见[边界与未实测](#边界与未实测) | `start=2` |
| `limit` | 整数 | 每页条数 | 未实测，见[边界与未实测](#边界与未实测) | `limit=2` |
| `**params` | 其它名字原样进查询串 | — | 本轮只发过 `start`、`limit` | — |

L：

* `tag=GenshinImpact&start=0&limit=2` → `200`，裸数组 2 条（`id` `4971`、`4970`，按 `create_time` 倒序）。
* `tag=GenshinImpact&start=2&limit=2` → 第一条是 `id` `4967`，`start` 确实当偏移用。
* `tag=genshinimpact&limit=2` → 前两条与 `GenshinImpact` 相同（忽略大小写）。
* `tag=RuanMei&start=0&limit=100` → `200`，10 条（该标签只有 10 张图，`limit` 没吃满）；这 10 条覆盖 8 个 `pid`（同一 `pid` 的多张图是两行），它们的 `tags` 里该标签一共出现 14 次——`tag_list()` 的 `count` 9 与这三个数都不同，别换算。
* `tag=%23GenshinImpact`（带 `#`）→ `200 []`；`tag=原神,GenshinImpact`（逗号串）→ `200 []`；`tag=zzzznotexist` → `200 []`。空数组既表示没有命中，也是翻页到底的信号。
* 缺 `tag` → `400 {"error": "标签参数缺失"}`。
* 元素就是作品对象，`tags` 已去 `#`；`rawurl` 是 `i.pximg.net`（不做域名替换），形如 `https://i.pximg.net/img-original/img/2026/08/22/19/31/38/148746199_p0.jpg`。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    page = client.tag_images('GenshinImpact', start=0, limit=2)
    # GET https://pic.cosine.ren/api/tag?tag=GenshinImpact&start=0&limit=2
    # L：200，裸数组 2 条（id 4971、4970），没有 total
    print([image['id'] for image in page])

with Cosine('cosine') as client:
    missing = client.tag_images('zzzznotexist', limit=2)
    # L：200 []——没有的标签不是错误；翻页也就靠这个空数组收尾
    print(missing)

with Cosine('cosine') as client:
    # 翻页：start 按已取条数递增，取到空数组为止（本库不会自动翻页）
    start = 0
    while True:
        batch = client.tag_images('RuanMei', start=start, limit=2)
        if not batch:
            break
        print(start, [image['id'] for image in batch])
        start += len(batch)
```

### tag_list

签名：`tag_list()`。路由：`GET /api/tags`。无参数。返回 **D** 裸数组，元素是 `{"tag": …, "count": …}`。没有 `total`，一次全量返回（本轮约 70 KB）。

L：

* `GET /api/tags` → `200`，2128 项；样本顺序与 `count` 倒序一致：`甜妹` 1309、`女孩子` 634、`崩坏星穹铁道` 465、`原神` 450、`GenshinImpact` 137、`RuanMei` 9，最后一项是 `脚镣` 1。
* `tag` 字段不带 `#`；响应头带 `X-Nextjs-Cache: HIT`（本轮唯一在 API 路由上见到的缓存标记，`/feed.xml` 也带）。
* `count` 是标签记录行数，不是作品数：S（`src/app/api/tags/route.ts`）按 tag 分组（`groupBy(by: ['tag'], _count: {tag: true})`）、先去掉前导 `#` 再合并，然后降序返回；与 `search(tags=…)` 的 `total` 口径不同，见[计数字段的三个口径](#计数字段的三个口径不要互相换算)。输入文档给的表名（`imagetags`）本轮没有读 schema 核对，不当契约。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    tags = client.tag_list()
    # GET https://pic.cosine.ren/api/tags
    # L：200，裸数组 2128 项；表头 X-Nextjs-Cache: HIT
    print(len(tags), tags[0])
    print({row['tag']: row['count'] for row in tags if row['tag'] in ('甜妹', 'RuanMei')})
    # 一次全量返回，要分页请自己对这个列表切片
```

## 画师（2 个方法）

### artist_images

签名：`artist_images(platform, authorid, **params)`。路由：`GET /api/artist`。一条路由两种形状：默认返回 **B** 信封，只有 `infoOnly='true'` 走 **E** 裸资料对象分支。`platform` 与 `authorid` 都是必填位置参数，作为查询名 `platform` / `authorid` 发送。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `platform` | `pixiv` / `twitter` | 平台 | 必填；缺了回 `400 {"error": "缺少必要参数 platform 或 authorid"}` | `artist_images('pixiv', '54390221')` |
| `authorid` | 字符串（画师 id） | 画师 id | 必填；传 `abc` 回 `500 {"error": "获取画师数据失败"}` | 见上一行 |
| `infoOnly` | 字符串，只有字面量 `'true'` 走资料分支 | 只要资料不要作品 | 走列表分支；`infoOnly=1` 也是列表分支（L） | `artist_images('pixiv', '54390221', infoOnly='true')` |
| `page` | 整数 | 页码（列表分支） | 未实测，见[边界与未实测](#边界与未实测) | `page=2` |
| `pageSize` | 整数 | 每页条数（列表分支） | 未实测，见[边界与未实测](#边界与未实测) | `pageSize=2` |
| `**params` | 其它名字原样进查询串 | — | 本轮只发过上表这些名字 | — |

L：

* `platform=pixiv&authorid=54390221&page=1&pageSize=2` → `200 {"images": [2 条], "total": 78}`；`page=2&pageSize=2` → 另外 2 条（`total` 仍 `78`），`page` 按 `pageSize` 起跳。
* `platform=pixiv&authorid=54390221&infoOnly=true` → `200`，裸资料对象 `{"author": "makoron117", "authorid": "54390221", "platform": "pixiv", "artworkCount": 78}`——没有 `images`、没有信封。
* `infoOnly=1&pageSize=2` → 走列表分支（`{"images": [2 条], "total": 78}`），所以非字面量 `'true'` 不是资料分支。
* 资料里的 `author`（`makoron117`）与本页作品列表里同一画师的 `author`（`まころん夏コミC48土お52日`）可以不一致；展示名字请用列表里的，或自己选一个并写清来源。
* `infoOnly=true` 但该画师没有作品 → `404 {"error": "未找到该画师"}`（样本 `authorid=999999999`）。
* 缺 `platform` → `400 {"error": "缺少必要参数 platform 或 authorid"}`；`authorid=abc` → `500 {"error": "获取画师数据失败"}`。
* 列表分支的 `tags` 已去 `#`（本轮样本没有重复项，但同一套字段在 `image_list`、`tag_images`、`artwork_show` 的样本里出现过重复，不要假定去重）。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    listing = client.artist_images('pixiv', '54390221', page=1, pageSize=2)
    # GET https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&page=1&pageSize=2
    # L：200 {"images": [2 条], "total": 78}
    print(listing['total'], [image['id'] for image in listing['images']])

with Cosine('cosine') as client:
    record = client.artist_images('pixiv', '54390221', infoOnly='true')
    # GET https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&infoOnly=true
    # L：200 裸对象 {"author": "makoron117", "authorid": "54390221", "platform": "pixiv", "artworkCount": 78}
    # 注意：这不是 {"images": …}；record['author'] 可能与列表里的画师名不同
    print(record['author'], record['artworkCount'])
```

### artist_list

签名：`artist_list(**params)`。路由：`GET /api/artists`。返回 **B′** 信封 `{"artists": […], "total": N, "hasNextPage": bool}`——只有这条路由用 `artists` 这个键。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | 整数 | 页码 | 未实测，见[边界与未实测](#边界与未实测) | `page=2` |
| `pageSize` | 整数 | 每页条数 | **L**：不带参数返回 20 条 | `pageSize=2` |
| `sortBy` | `artworks` / `random` / `lastUpdate`，未知值静默回落 | 排序方式 | **L**：不带参数的头两条与 `sortBy=artworks` 相同 | `sortBy='lastUpdate'` |
| `**params` | 其它名字原样进查询串 | — | 本轮只发过上表这些名字 | — |

`artists[]` 每项字段（L）：`platform`、`authorid`、`author`、`artworkCount`、`latestImageThumb`、`latestImageFilename`、`lastUpdateTime`、`latestImageWidth`、`latestImageHeight`。`latestImageThumb` 是数据库原值：Pixiv 画师是 `i.pximg.net`（取图要 Referer），Twitter 画师是 `pbs.twimg.com`（本轮 `美和野らぐ`、`pong`、`鸦居` 三条都是）。

L：

* `GET /api/artists`（不带参数）→ `200`，`artists` 20 条，`total` `1708`、`hasNextPage` `true`。
* `page=1&pageSize=2&sortBy=artworks` → `54390221`（78 件）、`6662895`（57 件）；`page=2&pageSize=2&sortBy=artworks` → `15034125`（54 件）、`22298878`（46 件），两页拼起来是件数递减的 4 行，分页按 `(page-1)*pageSize` 起跳（一次样本）。
* `page=1&pageSize=2&sortBy=lastUpdate` → `torino`（`lastUpdateTime` `2026-09-18`）、`ぺんたごん…`（`2026-09-14`），这两行的顺序与最新作品入库时间倒序一致（一次样本）。
* `page=1&pageSize=2&sortBy=random` → 与 `artworks` 完全不同的两行（`夏炉` 3 件、`ばん` 2 件），只发过一次，没有复测它是否每次都不同。
* `page=1&pageSize=2&sortBy=unknown` → 与 `sortBy=artworks` 的同一页完全一致（回落已证一例）。
* `hasNextPage` 在本轮每个样本里都是 `true`，没有跑到末页。
* 这条路由本轮没有读源码，所以 `artworks` / `lastUpdate` 分别按什么排序、行序是否稳定都只有样本，不要写成排序保证。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    top = client.artist_list(page=1, pageSize=2, sortBy='artworks')
    # GET https://pic.cosine.ren/api/artists?page=1&pageSize=2&sortBy=artworks
    # L：200 {"artists": [2 条], "total": 1708, "hasNextPage": true}
    for artist in top['artists']:
        print(artist['authorid'], artist['author'], artist['artworkCount'])

with Cosine('cosine') as client:
    recent = client.artist_list(page=1, pageSize=2, sortBy='lastUpdate')
    # L：200；最新作品入库时间倒序（torino 2026-09-18、ぺんたごん… 2026-09-14）
    print([artist['lastUpdateTime'] for artist in recent['artists']])
```

## 索引与缓存（3 个方法，其中 2 个是 `POST`）

### search_index_status

签名：`search_index_status()`。路由：`GET /api/search/admin`。无参数。返回 **C** 信封。这条是只读的，它和下面的写方法共用同一个路由，但本库把它单独包成一个方法。

L：

* `GET /api/search/admin` → `200 {"success": true, "data": {"totalImages": 4953, "indexedImages": 3353, "indexHealth": "partial", "lastSyncTime": "2026-09-19T16:42:34.383Z"}}`。
* 本轮匿名就能拿到，不需要任何凭据。
* `lastSyncTime` 与同时刻响应的 `Date` 头落在同一秒（`16:42:34`）。S：报告由 `src/lib/search/indexing-service.ts` 里的 `getIndexReport` 生成，`dbCount` 取 `prisma.image.count()`、`indexCount` 取索引文档数，而 `lastSyncTime` 明确写成 `new Date()`（源码注释也说明本应记录真实同步时间）——所以它不是可信的上次同步时间；出处是那个服务文件，不是 `src/app/api/search/admin/route.ts`。
* `indexHealth` 本轮只见过 `"partial"`；输入文档列了 `healthy` / `partial` / `empty` 三个取值（T），本轮没有 `healthy` 或 `empty` 的样本。
* 索引比库少：同一天 `totalImages` `4953`、`indexedImages` `3353`，与 `search()` 落后于 `tag_images()` 的观察一致。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    status = client.search_index_status()['data']
    # GET https://pic.cosine.ren/api/search/admin
    # L：200 {"success": true, "data": {"totalImages": 4953, "indexedImages": 3353, "indexHealth": "partial", …}}
    print(status['totalImages'], status['indexedImages'], status['indexHealth'])
    # 不要用这些数字推算搜索结果条数：搜索那边的 total 另有 1000 的上限
```

### search_index_admin

签名：`search_index_admin(action, **params)`。路由：`POST /api/search/admin`。正文是 `dict(params, action=action)`，原样作为 JSON 发出。

> **危险：这个请求会改站点数据，而且本轮一次都没有发过。**
> S（`src/app/api/search/admin/route.ts`）：`POST` 直接按 `action` 分支执行，没有任何鉴权检查，取值是 `initialize`、`index_all`、`sync_recent`、`rebuild`（这四个回 `{"success": true, "message": …}`）与 `validate`（回 `{"success": true, "data": …}`），其它值 `400 {"success": false, "error": "Invalid action"}`；`index_all` 取 `batchSize`（缺省 100）、`sync_recent` 取 `hours`（缺省 24）。也就是说匿名调用者也能触发重建。本库不会替你确认、不会检查权限、不提供 dry run、也不会在事后回滚；`search_index_admin()` 一被调用就真的发出去了。本项目从未执行过它，所以上面这些响应形状只有源码依据、没有任何实测；也不要说「每个 action 都返回 `{success, data}`」——四个 action 的是 `{success, message}`。读进度请用 `search_index_status()`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `action` | `initialize` / `index_all` / `sync_recent` / `rebuild` / `validate`（S：路由的 switch 分支） | 要执行的索引操作 | 必填 | `search_index_admin('index_all')`——不要执行 |
| `**params` | 其它键值，如 `batchSize`、`hours` | 与 `action` 合并进同一个 JSON 正文，原样发送（S：`index_all` 读 `batchSize` 缺省 100、`sync_recent` 读 `hours` 缺省 24） | 只发 `{"action": …}` | `search_index_admin('sync_recent', hours=24)`——不要执行 |

* request 正文就这样构造：`{"action": "index_all", "batchSize": 100}`。
* 未知 action 的响应（S：`400 {"success": false, "error": "Invalid action"}`）与四个 action 的 `{"success": true, "message": …}`、`validate` 的 `{"success": true, "data": …}` 都只有源码依据，本轮没有执行过，不要把它们当实测结果。
* 以下仅说明调用形态，未执行，不是匿名只读示例；不要为了验证接口发出任何 action：

```text
调用：client.search_index_admin('index_all', batchSize=100)
请求：POST https://pic.cosine.ren/api/search/admin
JSON：{"action": "index_all", "batchSize": 100}
```

### artwork_revalidate

签名：`artwork_revalidate(artwork_id, *, secret=None)`。路由：`POST /api/artwork/revalidate`。正文是 `{"artworkId": artwork_id, "secret": secret}`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `artwork_id` | 站内行号；在正文里原样发送，不做路径编码、不做数字校验 | 要刷新的作品 | 必填 | `artwork_revalidate(3840)`——不要执行 |
| `secret` | 字符串或 `None` | 站点服务端环境变量里的密钥 | `None` 时用客户端的 `revalidate_secret`（构造参数或 `sites.cosine.revalidate_secret`，包内默认空串） | `artwork_revalidate(3840, secret='<调用方自己的密钥>')`——不要执行 |

* 空密钥也照发：`secret` 是空串时正文就是 `{"artworkId": 3840, "secret": ""}`；S 说只有与站点 `process.env.REVALIDATE_SECRET` 不相等时才回 401，所以空串到底被接受还是被拒，取决于站点那个环境变量的值——本库不承诺空密钥一定会被拒，也不做本地检查、不报错、不重试。
* 这个密钥只进这一个正文，不会变成请求头，也不发给任何其它路由。
* 本轮没有发过这个 `POST`（连空密钥的 401 都没试），所以成功响应、未知 `artwork_id` 的状态全部未实测。S（`src/app/api/artwork/revalidate/route.ts`）：`secret` 与服务端的 `process.env.REVALIDATE_SECRET` 不等时回 `401 {"message": "无效的密钥"}`；缺 `artworkId` 回 `400`；两者都对回 `{"revalidated": true, "now": Date.now()}`。这些只有源码依据。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    # POST https://pic.cosine.ren/api/artwork/revalidate
    # 未执行：需要站点服务端的 REVALIDATE_SECRET，本项目没有该凭据。
    # secret 原样写入正文；只有服务端能决定接受还是拒绝，客户端不猜状态码。
    response = client.artwork_revalidate(3840, secret='<调用方自己的密钥>')
    print(response)
```

## RSS（1 个方法）

### feed

签名：`feed()`。路由：`GET /feed.xml`。无参数。返回 XML 原文（`response_format='xml'`），不解析、不校验、不转成 JSON；这是本家族唯一一条非 JSON 路由。

L：

* `GET /feed.xml` → `200`，`Content-Type: application/xml; charset=utf-8`，带 `X-Nextjs-Cache: HIT`。
* 正文是 RSS 2.0：`<?xml version="1.0" encoding="utf-8"?>` 加 `<rss version="2.0">`；`<channel>` 里有 `title`（站点名称）、`link`（站点根）、`description`、`lastBuildDate`（样本 `Sun, 10 Aug 2025 13:07:22 GMT`）、`docs`、`generator`、`language`（`zh-CN`）、一个 `<image>`（含 favicon）与 `copyright`，然后是 `<item>` 块。
* 样本有 20 条 `<item>`；其中 `guid` 是站内作品 id，前三条是 `3290`、`3288`、`3289`——与同一天 `image_list()` 的最新行（`5003`、`5002`、…）不是同一代。不要把这个 feed 当作「当前最新 20 张」，`lastBuildDate` 也来自缓存。
* item 内部的字段名与样例见输入文档（T）；本轮只核对了它仍是 RSS 2.0 且只含 20 条，没有逐条核对每个 item 的字段。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    xml = client.feed()
    # GET https://pic.cosine.ren/feed.xml
    # L：200 application/xml; charset=utf-8，正文以 <?xml version="1.0" encoding="utf-8"?> 开头
    print(xml[:60])
    print(xml.count('<item>'))
    # 20 条；guid 不是当前最新作品 id，本库不会替你解析或翻页
```

## 媒体地址（只文档，未下载）

本库不下载任何图片字节，也没有取字节的方法；下面全部是字段里读到的地址形态与取图要求。本轮对任何图片主机（`pbs.twimg.com`、`i.pximg.net`、`piv.cosine.ren`、`backblaze.cosine.ren`）一次请求都没有发，所以除了「字段里出现过这些形态」之外都属未实测。

L（地址形态，来自 JSON 字段）：

| 形态 | 出现在 | 样本 |
| :--- | :--- | :--- |
| `https://pbs.twimg.com/media/{id}.jpg?name=orig` / `?name=medium` | Twitter 行，`rawurl` / `thumburl` | `image_list()`、`tag_images()` |
| `https://pbs.twimg.com/media/{id}?format=jpg&name=orig` / `&name=large` | Twitter 行，同上 | `artwork_show(1)` |
| `https://i.pximg.net/img-original/img/YYYY/MM/DD/HH/MM/SS/{filename}` | Pixiv 行，除 `image_random()` 外 | `tag_images()`、`artwork_show(3840)` |
| `https://i.pximg.net/img-master/…_{filename}_master1200.jpg`、`https://i.pximg.net/c/600x1200_90/img-master/…` | Pixiv 行，`thumburl` | `tag_images('RuanMei')` 的两条样本 |
| `https://piv.cosine.ren/img-original/…`、`https://piv.cosine.ren/img-master/…_master1200.jpg` | 只有 `image_random()` 的 Pixiv 行 | `count=1`、`count=-5` |

T（取图要求，未实测）：

* `i.pximg.net` 的地址一般需要 `Referer: https://www.pixiv.net/`（输入文档称不带是 `403`、带上 `200`）。
* `piv.cosine.ren` 是 `i.pximg.net` 的域名替换：路径原样保留，任何 `i.pximg.net` 路径都可以这样换，不用等 `image_random()` 给你，且输入文档称它免 `Referer`。
* Twitter 的 `pbs.twimg.com` 地址输入文档称直连可用；`name=orig` 是原图档，`name=medium` / `name=large` 与 `?format=` 的具体档位由站点给什么就是什么，不要假定只有一种。
* 输入文档还提到一个原图兜底主机 `backblaze.cosine.ren`（`/pic/origin/{platform}/{文件名改 .webp}`，第三方项目还会先试原始文件名），但它不在本库代码里、本轮也没有请求过，输入文档自己记的 4 个样本是 `404`：不要把它当主链路。
* 站点页面路由（`/`、`/search`、`/tag/{标签}`、`/artists`、`/artist/{platform}/{uid}`、`/artwork/{id}`、`/about`、`/friends`）不是 API，本库不封装。

## 错误与状态码（L）

| 状态 | 本轮触发的请求 | 正文 |
| :--- | :--- | :--- |
| `200` | 其余 58 次（正常读、空数组、超末页、`pageSize=0` / `pageSize=-1`、`count=0` / `count=-5`、`sort=width:asc` 等） | 四种信封 / 裸数组 / 裸资料对象 / RSS 原文 |
| `400` | `GET /api/tag`（缺 `tag`）、`GET /api/artist`（缺 `platform`） | `{"error": "标签参数缺失"}`、`{"error": "缺少必要参数 platform 或 authorid"}` |
| `404` | `GET /api/artwork/999999999`、`GET /api/random?count=abc`、`GET /api/artist?…&infoOnly=true`（该画师无作品） | `{"error": "未找到该作品"}`、`{"error": "未找到图片"}`、`{"error": "未找到该画师"}` |
| `500` | `GET /api/list?page=0`、`page=-1`；`GET /api/artwork/abc`；`GET /api/artist?platform=pixiv&authorid=abc`；`GET /api/search?limit=-1`、`offset=-5`、`sort=bogus` | `{"error": "获取图片列表失败"}`、`{"error": "服务器错误"}`、`{"error": "获取画师数据失败"}`、`{"success": false, "error": "Internal search error", "message": "…Meilisearch 英文…"}` |

要点：

* A/B/B′/D 路由的错误体是 `{"error": "中文说明"}`；`/api/search` 系是 `{"success": false, "error": …, "message": …}`，只有它带 `message`。
* 同一类错误的状态码不统一：作品 id 非数字是 `500`（不是 `400`），`random` 的非法 `count` 是 `404`（不是 `400`），标签缺失是 `400`。
* 非 2xx 一律抛 `AnybooruHTTPError`（`http_code` / `url` / `body` / `data`），库不重试、不改写正文。
* `200` + 空数组是正常结果：`tag_images()` 没有命中、`image_list()` 超末页、`search_suggestions()` 的短 `q` 都是 `200`。

## 边界与未实测

下面是没有 L 或 S 支持的部分（输入文档候选、本轮没请求到的取值、或本轮没有复现的结论），不要当契约；逐条出处与矛盾见[依据与差异](cosine-contract-notes.md)。

* **两个 `POST`**：`search_index_admin()` 与 `artwork_revalidate()` 本轮一次都没有发。成功响应、错误文案、耗时与副作用全部未实测；S 给出的 action 分支、`batchSize`/`hours` 缺省、`{success, message}` / `{success, data}` 形状与密钥比较都只有源码依据，没有任何实测。
* **默认值**：有 L 支持的：`image_list` 的 10 条与第一页、`artist_list` 的 20 条、`search_suggestions` 的 10 条；有 S 且与 L 一致的：`search` 的 `limit` 20、`offset` 0、`sort` `create_time:desc`、`r18` 比较用 `=== 'true'`，以及 `image_random` 的 `count` 1 与 1–20 夹取。`artist_images` 的 `page`/`pageSize` 默认（输入文档称 1 / 24）、`tag_images` 的 `start`/`limit` 默认（称 0 / 32）、`artist_list` 的 `page` 默认、`search_suggestions` 的 `limit` 上限（称 20）都未实测，也没有读过对应路由源码。
* **上限与被夹**：`search` 的 `limit` 100（S + L：`500` 回 100 且 100 条）、`offset` 夹到 1000（L：`100000` 回 1000）、`image_random` 的 `count` 20（S + L：`100` 回 20 条）已证；`search_suggestions` 的 `limit` 上限（输入文档称 20）未证实——`limit=50` 只回 15 条，无法区分是上限还是只有 15 个候选；`pageSize` 与 `limit` 在列表路由上的服务端上限未测（`pageSize=100` 正常返回 100 条）。
* **页码与条数的其它越界**：只证了 `page=0` / `page=-1` → 500、`pageSize=0` → 空数组、`pageSize=-1` → 1 条、`page=100000` → 空数组；其它负数、小数、非数字、极大值都没有样本。输入文档给的解释（Prisma 的 `skip` 为负、`take:-1` 反向语义）是 T。
* **排序**：`sort` 的缺省值是 S 的 `create_time:desc`；L 证 `width:asc` 被接受、`bogus` → 500；`height` 与其它字段没试。`artist_list` 的 `sortBy` 只证 `artworks`、`random`、`lastUpdate`、`unknown`（回落）各一次，`random` 每次是否真的不同没有复测；该路由没有源码依据，所以行序与「按件数 / 按更新时间」都只是样本。
* **不外推的一条**：`image_random()` 的返回顺序在 L 样本里是升序，但 S 的查询没有 `orderBy`，所以只能说「无排序保证」，不要写成「按主键排序」。
* **命中字段集合**：L 见到一条没有 `title` 的搜索命中（`tags=RuanMei` 的 `id` `38`），所以「每条命中都有某字段」不成立；其它字段是否也会缺，本轮没有穷举。
* **过滤语义**：`tags` 的 AND 只证了两个标签一次（`原神,GenshinImpact` → 160，前 100 条逐条都同时带两个标签）；大小写只证了 `GenshinImpact` / `genshinimpact` 这一对；`r18` 的「非 `'true'` 即非 R18 过滤」由 S 给出，L 的 `r18=false` / `r18=1` 样本里每条命中的 `r18` 都是 `false`（与语义一致），只是 `total` 与不传时一样被 1000 的上限盖住、分不出过滤差异；`platform` 只证 `pixiv` / `twitter` / `unknown`，"只有这两种平台"是输入文档的说法。
* **`total` 与 `count` 的口径**：`search().total` 被夹到 1000（L），夹点与 Meilisearch `maxTotalHits` 的关系是 T；`tag_list().count` 是行数（S 支持算法，含义解释部分是 T）；三者不能互相换算。
* **索引落后**：`indexHealth` 的三个取值（`healthy`/`partial`/`empty`）是输入文档说法，本轮只见过 `partial`；`lastSyncTime` 的实现（`new Date()`）由 S 的 `src/lib/search/indexing-service.ts` 支持，但那条路径本身只被请求过一次。
* **RSS 的 item 字段**：只证了它仍是 RSS 2.0、20 条 item、`guid` 前三条 `3290`/`3288`/`3289`、`lastBuildDate` `Sun, 10 Aug 2025 13:07:22 GMT`（缓存时间，不是当年当天）；item 内部字段清单与 `/rss`、`/rss.xml`、`/feed` 是否都能到达同一份（输入文档称都 200）未复测，缓存时长与失效条件也未测。
* **媒体**：0 请求。`Referer`、`piv.cosine.ren` 免 Referer、`backblaze.cosine.ren` 兜底、Twitter 两种 URL 形态的实际取图行为全部是 T；本库也不提供下载方法。
* **跨域与配额**：本轮 69 个响应都没有 `Access-Control-Allow-Origin`、也没有 `RateLimit-*`，但只能说本轮样本没有这些头；输入文档记的 `OPTIONS /api/search` → `204` 本轮没有复测，有没有配额、限流怎么触发都未知，本库不做节流与退避。
* **缓存头**：只有 `/api/tags` 与 `/feed.xml` 的样本带 `X-Nextjs-Cache: HIT`，其它路由是否也有静态缓存、缓存多久都未测。
* **数据库层面的语义**（历史遗留）：`title` 对 Twitter 是推文正文、`page` 两平台起点不同、`size` 与 `guest` 描述入库年代、`create_time` 是入库时间、`userid`/`username` 是投稿人而非画师——这些来自输入文档（T），本轮只支持其中「字段值确实长这样」的观察；「新数据恒 `null` / 恒 `false`」本轮没有逐条核对。

继续阅读：[客户端用法](cosine.md) · [能力入口](cosine-capabilities.md) · [依据与差异](cosine-contract-notes.md) · [验证记录](verification.md#cosine匿名只读实测2026-09-20)
