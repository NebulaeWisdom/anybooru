# Cosine：我要做什么，用哪个方法？

Cosine Gallery（`https://pic.cosine.ren`）是 Telegram 频道 `@CosineGallery` 的配套图站，自研 JSON API
（Next.js + Prisma + Meilisearch），**不是 booru 引擎**：没有 `post` 对象、没有 `rating` 字符串、没有点号参数，
标签是字符串数组、站内编号 `id` 与上游编号 `pid` 是两个字段。
本库包装站点根 `https://pic.cosine.ren`：**13 个原生方法 = 11 个读取 + 2 个 `POST`**。

* **JSON 读取 10 条**：图片列表、作品详情、随机、搜索（含建议与索引进度）3 条、标签 2 条、画师 2 条。
* **XML 读取 1 条**：`feed()` 取 `/feed.xml` 的 RSS 原文（返回字符串，不解析）。
* **`POST` 2 条**：`search_index_admin()`（**会改站点搜索索引，本轮零请求**）与
  `artwork_revalidate()`（站点内部刷新入口，需要密钥，**本轮零请求**）。

**除 `feed()`（请求 `/feed.xml`）外，其余 12 个方法都接在站点根后面的 `/api/*` 上**；
每个方法都原样返回站点给的那一层，参数由你给全、客户端不钳位、不重试、不合并分页、**不下载媒体**。
每个方法的完整参数范围与逐字段说明放在[方法参考](cosine-api.md)；
本页只做「目的 → 方法」的对照与一行索引，不重复参数表。

**表里的数字与编号来自 2026-09-20 的一批匿名只读请求**，不是每个 Python 方法逐个运行过的记录；
逐条 URL 与状态见[验证记录](verification.md#cosine匿名只读实测2026-09-20)。
站点数据实时变动，编号、条数、计数只作形态示例。

用法面的共同约定：

* 下面的 `client` 由 `Cosine('cosine')` 创建，包内配置默认匿名（`revalidate_secret` 是空串）；
  构造、空密钥语义与路径规则见[客户端用法](cosine.md)。
* **四种返回外壳**（客户端一层都不拆）：A `{"json", "meta"}`（`/api/artwork/{id}`、`/api/random`）、
  B `{"images", "total"}`（`/api/list`、`/api/artist` 列表分支）与 `{"artists", "total", "hasNextPage"}`
  （`/api/artists`）、C `{"success", "data"}`（`/api/search`、`/api/search/suggestions`、`/api/search/admin`）、
  D 裸数组（`/api/tag`、`/api/tags`）。**失败形态也不统一**：A/B/D 是 `{"error": …}`，
  C 是 `{"success": false, "error": …, "message": …}`。
* **`artist_images(infoOnly=True)` 的裸资料对象不在四种外壳内**（只有 `author` / `authorid` /
  `platform` / `artworkCount` 四个键）。
* 媒体只给地址：`rawurl` / `thumburl` / `latestImageThumb` 都是字符串，本库不请求、不落盘；
  地址规则与取图要求见[媒体地址](cosine.md#媒体地址只返回字符串本库不下载)。

## 按目的找调用

| 我要做什么 | 调用 | 给什么 → 返回什么（**实测**＝本轮匿名响应样本；**源码**＝站点公开仓库只读单文件；**输入**＝输入资料的语义候选；**未实测**＝没有样本） |
| :--- | :--- | :--- |
| 浏览最新图片 | `client.image_list(page=1, pageSize=2)` | 页码（**从 1 起**）+ 每页条数 → `200 {"images": […], "total": 4953}`，本轮 `id` 5003、5002（对象 21 个键，含 `platform` / `author` / `authorid` / `pid` / `rawurl` / `thumburl` / `tags`） |
| 翻下一页 | `client.image_list(page=2, pageSize=2)` | 手动把 `page` 加一 → 本轮 `id` 5001、5000；`page` 从 1 起，`page=0` / `page=-1` 是 `500`，超末页是空数组 |
| 一次多取几张 | `client.image_list(pageSize=100)` | 每页条数 → 本轮 100 项（不带参数时回 10 项）；`pageSize=0` 回空数组、`pageSize=-1` 回最旧 1 条 |
| 取一张作品的详情 | `client.artwork_show(1)` | 站内编号 → **A 信封** `{"json": {…}, "meta": {"values": …}}`；`json` 与列表项同为 21 键；`page` 的起点按输入资料是 Pixiv 0 / Twitter 1（本轮样本各一个，**不承诺恒定**）；`/api/artwork/3840` 是 Pixiv 样本（`rawurl` 在 `i.pximg.net`），详情**不补** `originUrl` / `authorUrl` |
| 取不存在的作品 | `client.artwork_show(999999999)` | `404 {"error": "未找到该作品"}`——**没有 `json` 键** |
| 把编号写成非数字 | `client.artwork_show('abc')` | `500 {"error": "服务器错误"}`——**是 500 不是 400** |
| 随机抽图 | `client.image_random(count=1)` | 张数 → A 信封，**1 张时 `json` 是对象**（本轮 `id` 1666），并且只有它会补 `originUrl` / `authorUrl`、把 `i.pximg.net` 换成 `piv.cosine.ren` |
| 随机抽多张 | `client.image_random(count=3)` | → 同信封，**`json` 是数组**（3 项，`id` 2042…），`meta.values` 的键带下标（`0.userid`、`1.userid`…） |
| 抽很多张 | `client.image_random(count=100)` | → 本轮回 **20 项**（数组）；`count` 不传 / `0` / `-5` 都只回 1 张，`count=abc` 是 `404 {"error": "未找到图片"}` |
| 关键词搜索 | `client.search(q='初音', limit=2)` | C 信封：`data` 是 `{"hits", "query", "total", "limit", "offset", "processingTimeMs"}`，本轮 `query` 初音、`total` 255、`limit` 2；`hits[0]['id']` 是**字符串**（`'2760'`），`tags` 是字符串数组，另有 `searchable_content` / `_formatted`，**没有** `userid` / `username` / `page` / `size` / `guest` / `extension` |
| 不传关键词 = 搜整个索引 | `client.search(limit=2)` | → `query` 是 `""`、`total` 1000（`total` 是**索引进度里的估算上限**，只反映索引：同一时刻 `indexedImages` 3353、库里 `totalImages` 4953，所以 **1000 ≠ 全库**），不带 `limit` 时回 `limit` 20 |
| 翻搜索结果 | `client.search(q='初音', limit=2, offset=2)` | 跳过条数 → 同一个 C 信封；`offset=100000` 会回 `offset` 1000 且 `hits` 为空，`offset=-5` 是 `500` |
| 按标签搜 | `client.search(tags='GenshinImpact', limit=2)` | **忽略大小写全等**：`GenshinImpact` 与 `genshinimpact` 都是 166；中文标签 `原神` 是 510；多个标签用**逗号**写在一个值里是 **AND**（`原神,GenshinImpact` 是 160）；标签名要写完整标签，不能带 `#`（`tag_images` 上带 `#` 本轮回空数组，`search` 的这一取值未单独测） |
| 只看 R18 或非 R18 | `client.search(r18='true', limit=100)` | `'true'` 的 7 条命中全为 R18；`'false'` 与 `'1'` 的样本均为非 R18，源码也按这个条件过滤。不传才不过滤；相同的截断计数 1000 不代表相同结果 |
| 按来源过滤 | `client.search(platform='pixiv', limit=2)`、`platform='twitter'`、`platform='unknown'` | 前两个本轮 `total` 都是 1000，未知平台回 `total` 0 |
| 换排序 | `client.search(sort='width:asc', limit=2)` | 合法排序表达式有效；非法值（`bogus`）是 `500 {"success": false, "error": "Internal search error", "message": "Invalid syntax for the sort parameter: …"}` |
| 搜索建议 | `client.search_suggestions(q='miku')` | C 信封，`data` 是 `{"suggestions": [{"text", "type"}], "query"}`：本轮 10 条（`limit=50` 回 15 条）；单字符 `q='a'` 回空数组 |
| 看索引进度 | `client.search_index_status()` | 无参数 → C 信封：`{"totalImages": 4953, "indexedImages": 3353, "indexHealth": "partial", "lastSyncTime": …}`（实测）；`lastSyncTime` 是**假值**（源码：`src/lib/search/indexing-service.ts` 里写的是 `new Date()`，即请求时刻） |
| **重建/校验索引（危险）** | `client.search_index_admin('rebuild')` | **会修改站点搜索索引；站点该路由无鉴权；本轮零请求**（**未实测**）。源码只读形态：`validate` 回 `{success, data}`、其余回 `{success, message}`、非法 `action` 400——见[客户端用法](cosine.md#search_index_admin危险会改站点数据绝不要手滑) |
| 请站点刷新某作品缓存 | `client.artwork_revalidate(1)` | JSON `{"artworkId": 1, "secret": …}`；密钥来自构造参数或配置，**空密钥也照发**；**本轮零请求**（**未实测**）。源码只读：站点把 `secret` 与环境变量比较，**不相等**才回 `401 {"message": "无效的密钥"}`，所以空密钥**不一定**被拒 |
| 按标签列作品 | `client.tag_images('GenshinImpact', start=0, limit=2)` | **D 裸数组**、没有 `total`：本轮 `id` 4971、4970；`start` 是跳过条数（`start=2` 是 4967、4964）；`tag` 必填，不传是 `400 {"error": "标签参数缺失"}` |
| 判某个标签的末尾 | `len(client.tag_images('RuanMei', limit=100)) == 0` | 靠**空数组**判末尾：本轮 `RuanMei` 有 10 张（8 个不同 `pid`；`tag_list` 给它的 `count` 是 9、`search` 的 `total` 也是 9，口径不同，见[客户端用法](cosine.md#标签d-裸数组count-不是作品数)）；不存在的标签（`zzzznotexist`）与带 `#` 的写法都回 `[]`（`200`） |
| 列全部标签 | `client.tag_list()` | 无参数 → **D 裸数组**，本轮 2128 项 `{"tag", "count"}`（`甜妹` 1309、`原神` 450、`GenshinImpact` 137、`RuanMei` 9）；`count` **不是作品数**，有静态缓存（`X-Nextjs-Cache: HIT`） |
| 看某画师的作品 | `client.artist_images('pixiv', '54390221', page=1, pageSize=2)` | 平台 + 画师编号 → **B 信封** `{"images": […], "total": 78}`，本轮 `id` 4869、4827；缺参数是 `400 {"error": "缺少必要参数 platform 或 authorid"}`，编号非数字是 `500` |
| 看某画师的资料 | `client.artist_images('pixiv', '54390221', infoOnly=True)` | **只有字面量 `'true'` 走资料分支**（`infoOnly=1` 仍回列表）→ **裸资料对象** `{'author': 'makoron117', 'authorid': '54390221', 'platform': 'pixiv', 'artworkCount': 78}`；资料里的 `author` 可能与作品列表的 `author`（本轮 `まころん夏コミC48土お52日`）不同；没有作品是 `404 {"error": "未找到该画师"}` |
| 列画师 | `client.artist_list(page=1, pageSize=2, sortBy='artworks')` | **B 信封** `{"artists": […], "total": 1708, "hasNextPage": true}`，每项有 `platform` / `authorid` / `author` / `artworkCount` / `latestImageThumb` / `latestImageFilename` / `lastUpdateTime` / `latestImageWidth` / `latestImageHeight`；不带参数回 20 项 |
| 换画师排序 | `client.artist_list(sortBy=…)` | `artworks`（首个 `authorid` 54390221）、`random`（首个 `夏炉`）、`lastUpdate`（首个 `torino`）都有效；**未知值静默回落 `artworks`**（本轮 `sortBy=unknown` 与不传一致） |
| 读站点 RSS | `client.feed()` | 无参数 → **字符串**（`GET /feed.xml` 的 `response.text` 原文，不是 JSON、不解析）：本轮 RSS 2.0、20 个 `<item>`、`<guid>` 3290/3288/3289…、`lastBuildDate` `Sun, 10 Aug 2025 13:07:22 GMT`；**不是当前最新 20 张**，响应带缓存 |
| 用别的路径、动词或格式 | `client.request('GET', 'feed.xml', response_format='xml')` | 动词 + 路径 + `params` / `data` / `headers` / `response_format` → 与原生方法同一条通路；前导 `/` 会被去掉（`'/api/list'` 与 `'api/list'` 等价），`response_format='xml'` 回 `response.text` |

## 完整方法索引（11 读取 + 2 个 `POST` = 13）

每个原生方法一行；参数范围、缺省行为与逐字段说明只放在[方法参考](cosine-api.md)。
以下路径都接在 `https://pic.cosine.ren` 后面，**只有 `feed()` 不在 `/api` 下**。

### 图片与作品（3，都是 `/api` 下的 JSON 读取）

* `image_list(**params)` → `GET /api/list`，B 信封 `{"images", "total"}`；`page` / `pageSize`。
* `artwork_show(artwork_id)` → `GET /api/artwork/{quote(str(artwork_id), safe='')}`，A 信封
  `{"json", "meta"}`；不存在 `404`，非数字 `500`。
* `image_random(**params)` → `GET /api/random`，A 信封；1 张时 `json` 是对象、多张是数组，
  并且只有它补 `originUrl` / `authorUrl`、把 `i.pximg.net` 换成 `piv.cosine.ren`。

### 搜索与索引（3 JSON 读取 + 1 危险 `POST`）

* `search(**params)` → `GET /api/search`，C 信封；`q` / `limit` / `offset` / `platform` / `tags` / `r18` / `sort`。
* `search_suggestions(**params)` → `GET /api/search/suggestions`，C 信封；`q` / `limit`。
* `search_index_status()` → `GET /api/search/admin`（只读分支），C 信封的索引进度报告。
* `search_index_admin(action, **params)` → `POST /api/search/admin`，正文 `{"action": …, **params}`；
  **会重建/删除站点搜索索引、该路由无鉴权、本轮零请求**，见[危险说明](cosine.md#search_index_admin危险会改站点数据绝不要手滑)。

### 标签（2 条 JSON 读取，都是裸数组）

* `tag_images(tag, **params)` → `GET /api/tag`，**D 裸数组**、无 `total`；`tag` 必填（不带 `#`），`start` / `limit`。
* `tag_list()` → `GET /api/tags`，**D 裸数组** `[{"tag", "count"}]`；`count` 不是作品数，有静态缓存。

### 画师（2 条 JSON 读取）

* `artist_images(platform, authorid, **params)` → `GET /api/artist`，B 信封 `{"images", "total"}`；
  `infoOnly` **只有字面量 `'true'`** 改走裸资料对象分支。
* `artist_list(**params)` → `GET /api/artists`，B 信封 `{"artists", "total", "hasNextPage"}`；`page` / `pageSize` / `sortBy`。

### RSS 与站点内部入口（1 读取 + 1 `POST`）

* `feed()` → `GET /feed.xml`，**返回完整 XML 字符串**（`response_format='xml'` 走 `response.text`，无嗅探）。
* `artwork_revalidate(artwork_id, *, secret=None)` → `POST /api/artwork/revalidate`，正文
  `{"artworkId": …, "secret": …}`；`secret=None` 取构造时的 `revalidate_secret`，**空密钥也照发**，
  由站点决定 `401` 或成功；**本轮零请求**。

另外有一个通用入口 `request(method, path, *, params=None, data=None, headers=None, response_format='json')`：
路径（去掉前导 `/` 后拼站点根）、动词、正文与返回格式自己给全，不补前缀、不拆信封、不改字段名。

## 本库不封装的能力

这些路由 / 主机不在本库范围内；需要时用
`client.request(method, path, params=…, data=…, headers=…, response_format=…)` 自己发
（**只有 `'json'` 会被解析，`'xml'` 回文本**）。

| 类别 | 例子 | 为什么不封装 |
| :--- | :--- | :--- |
| 媒体下载与地址公式 | `pbs.twimg.com`、`i.pximg.net`、`piv.cosine.ren`、`backblaze.cosine.ren` 上的图 | 本库不下载媒体；`rawurl` / `thumburl` / `latestImageThumb` 已把地址给你，取图要求（`Referer`、镜像域名）见[客户端用法](cosine.md#媒体地址只返回字符串本库不下载)；`backblaze.cosine.ren` 的样本全是 `404` |
| 站点页面路由 | `/`、`/search`、`/tag/{标签}`、`/artists`、`/artist/{platform}/{uid}`、`/artwork/{id}`、`/about`、`/friends` | 它们不是 API；本库不抓 HTML，也不把页面当接口解析 |
| 登录 / 注册 / 换令牌 | 站点没有公开的账号体系 | 本库不登录、不索要账号；读取方法一律匿名可调 |
| 其它动词 | `PUT` / `PATCH` / `DELETE` | 本轮没有探测过站点的写路由，也不把未知动词变成方法 |

## 边界与未实测

* **没跑过的方法**：`search_index_admin()` 与 `artwork_revalidate()` 两个 `POST` 本轮**零请求**；
  `search_index_status()` 的 `GET` 分支已请求过。
* **已证的读取路径**：`image_list`（两页外加 `pageSize` 的 0 / 负值 / 100 / 缺省与 `page` 的越界）、
  `artwork_show`（命中、`404`、非数字 `500`）、`image_random`（缺省 / 1 / 3 / 0 / 负值 / 100 / 非数字）、
  `search`（`q` / 空 `q` / `limit` / `offset` / `platform` / `tags` / `r18` / `sort` 的取值样本）、
  `search_suggestions`、`search_index_status`、`tag_images`（命中 / 带 `#` / 不存在 / 大小写）、
  `tag_list`、`artist_images`（列表两页 / 资料 / `infoOnly=1` 对照 / 缺参数 / 非数字 / `404`）、
  `artist_list`（缺省 / 翻页 / 三种 `sortBy` / 未知值）、`feed`。
  逐条 URL 与状态见[验证记录](verification.md#cosine匿名只读实测2026-09-20)。
* **参数语义未穷尽**：上面那些参数只有**单次取值样本**，完整取值枚举、未知值回落规则、缺省与夹取边界以
  [方法参考](cosine-api.md)与[依据与差异](cosine-contract-notes.md#未实测集中清单)的标注为准；
  没有取过的取值不要按样本外推。
* **没有样本**：两个 `POST` 的全部行为、密钥的成功路径、任何媒体主机的字节与 `Content-Type`、
  `search_index_status` 里 `lastSyncTime` 之外的索引内部状态。三个脚本（轻量冒烟与两个示例）的实跑记录见
  [验证记录](verification.md#cosine匿名只读实测2026-09-20)；它们覆盖用法路径，
  不等于 13 个方法逐一验证。
* **纯源码、没有响应样本的说法**：两个 `POST` 的响应形状与密钥比较（含 `validate` 回 `{success, data}`、
  其余回 `{success, message}`、非法 `action` 400、`index_all` 的 `batchSize` 缺省 100、`sync_recent` 的
  `hours` 缺省 24、不相等才 `401`）；这些来自公开仓库的单个文件（只读，不 clone、不编行号），
  **不是线上部署版本与响应样本的证明**。
* **实测与源码互相印证的**：`/api/random` 的 `count` 夹取（`0` / 负值 → 1 张、`100` → 20 张）与标签
  `#` 收敛，`/api/search` 的缺省值与 `total` 取 Meilisearch 估算、`limit` / `offset` 夹取，
  `/api/tags` 的计数口径，`lastSyncTime` 不是真实同步时间——这些既有本轮样本，也有源码依据；
  但完整取值仍**没有穷举**。
* **没有排序或随机性保证**：`/api/random` 的返回顺序只有「样本升序」这一点观察，源码查询没有 `orderBy`；
  `artist_list(sortBy='random')` 只取过一次，未证明随机。
* **别名与写路由未探测**：输入资料称 `/rss`、`/rss.xml`、`/feed` 重写到 `feed.xml`，本轮只请求过 `/feed.xml`；
  除 `GET /api/search/admin` 外没有探测任何写路由。

继续阅读：[客户端用法](cosine.md) · [方法参考](cosine-api.md) ·
[依据与差异](cosine-contract-notes.md) · [验证记录](verification.md#cosine匿名只读实测2026-09-20)。
