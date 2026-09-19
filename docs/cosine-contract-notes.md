# Cosine：接口依据、权限与排除项

本页供核对依据，不代替[客户端用法](cosine.md)或[方法参考](cosine-api.md)。
`Cosine` 一共 **13 个原生方法**：**11 个匿名只读 `GET`** 加 **2 个 `POST`**
（`artwork_revalidate`、`search_index_admin`，本项目**一次都没有发过**）。全部方法只拼路由、带参数、
原样返回响应；没有媒体下载、没有登录、没有自动重试。

依据是**匿名响应为先**，外加**上游前端公开仓库里六个文件的只读阅读**：

* **L**：本轮 69 次匿名只读 `GET`（串行、相邻 ≥1.3 秒、各发一次、不重试、不跟随跳转、不下载媒体），
  逐条 URL、状态与字段见[验证记录](verification.md#cosine匿名只读实测2026-09-20)；
* **S**：上游 `SomeACG/SomeACG-Next` 的 6 个文件（`src/app/api/tags/route.ts`、
  `src/app/api/random/route.ts`、`src/app/api/search/route.ts`、`src/app/api/search/admin/route.ts`、
  `src/app/api/artwork/revalidate/route.ts`、`src/lib/search/indexing-service.ts`）的只读阅读；
  仓库**没有 clone**，每个文件只读一次，因此只写文件路径、**不写行号**；源码也不是站点当前部署版本的证明；
* **T**：接入时收到的《Cosine Gallery 接口文档（综合版）》，它自称内容来自对同一主机的匿名实测并
  交叉核对了站点前端源码，但**没有可公开核对的发布链接**。

本轮未取得官方 API 页面或 OpenAPI，也未确认线上部署的源码版本；公开仓库的 Next.js 路由仍是可引用的源码证据。
T 的部分只用于选择请求与描述字段语义，**没有 L 或 S 支持的一律集中在
[未实测集中清单](#未实测集中清单)，不进正文结论**。

## 资料来源与等级

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **L：本轮匿名只读实测** | 69 次直接 HTTP 观察（首轮 18 次路由与字段、第二批 51 次参数与边界，都串行、相邻 ≥1.3 秒、不重试、不跟随跳转、不下载媒体，每次都带 `Origin`） | 11 条读路由各有 `200` 样本；`400`/`404`/`500` 的错误路径、部分默认值与站点夹取后的回显也在其中。**直接路由证据不等于运行过对应的 Python 方法**，方法实际执行范围另见验证记录 |
| **S：上游单文件源码（只读 6 个文件）** | `src/app/api/tags/route.ts`、`src/app/api/random/route.ts`、`src/app/api/search/route.ts`、`src/app/api/search/admin/route.ts`、`src/app/api/artwork/revalidate/route.ts`、`src/lib/search/indexing-service.ts`（文件位置见[依据文件与出处](#依据文件与出处)；只写文件、不写行号） | 这些路由里的参数解析、默认值、夹取、查询与分支，以及响应形状：`/api/tags` 的 `count` 算法、`/api/random` 的 `count` 夹取与查询、`/api/search` 的 `q`/`limit`/`offset`/`sort`/`tags`/`r18` 处理、`/api/search/admin` 的 action 分支与响应体、`/api/artwork/revalidate` 的密钥比较、索引报告里 `lastSyncTime` 的实现。**源码依据不等于跑过**：两个 `POST` 零请求 |
| **T：输入文档（候选）** | 《Cosine Gallery 接口文档（综合版）》，自称站点前端源码交叉核对 + 匿名实测，无公开链接 | 未复测的参数默认值与上限、枚举、媒体取图要求、字段的上游语义、表名与表结构。这些一律只列在[未实测集中清单](#未实测集中清单)与[矛盾表](#实测与输入文档的矛盾与需要更正的说法) |
| **没有官方手册 / 部署版本证据** | 未取得 API 手册或 OpenAPI；公开仓库里的 Next.js 路由与服务文件不能证明线上部署版本 | `prisma/schema.prisma`、`src/lib/type.ts`、`src/lib/search/meilisearch-client.ts` 与第三方 Go 消费者本轮没有独立读取 |

三点必须记住：

1. **L 覆盖 11 条读路由**，两条 `POST` 是零样本：`search_index_admin` 与 `artwork_revalidate`
   的响应与错误文案只有 **S** 依据，**没有任何实测**。
2. **样本不是固定数据集**：搜索的 `total`、`hits` 条数与索引计数都在动（索引落后于库），
   数字只作当时读数的例子。
3. **四套信封 + 一个裸资料对象是站点现状**，不是本库造的：`/api/artist` 的 `infoOnly='true'`
   返回的是一个独立对象，既不是 `{"images": …}` 也不是数组。

## 13 个方法的逐条依据

「本轮 L」列只统计 69 次直接 HTTP 路由观察，不包含随后的冒烟与示例执行。路径都接在
`https://pic.cosine.ren` 后面。

| 方法 | 路由 | 本轮 L | 实测要点（另列 S 依据） |
| :--- | :--- | :--- | :--- |
| `image_list(**params)` | `GET /api/list` | 9 | 信封 `{"images": […], "total": 4953}`；不带参数 10 条（`pageSize` 默认 10）、`pageSize=100` 100 条、`pageSize=0` 空数组、`pageSize=-1` 只回最旧 1 条、`page=0`/`page=-1` → `500 {"error": "获取图片列表失败"}`、`page=100000` → 空数组 200 |
| `artwork_show(artwork_id)` | `GET /api/artwork/{id}` | 4 | superjson `{"json": …, "meta": {"values": {userid, create_time, authorid}}}`；`1`、`3840` 各一条；`999999999` → `404 {"error": "未找到该作品"}`；`abc` → `500 {"error": "服务器错误"}`（不是 400）；详情不带 `originUrl`/`authorUrl` |
| `image_random(**params)` | `GET /api/random` | 7 | 不带 `count`、`count=1`、`count=0`、`count=-5` → `json` 是**对象**；`count=3` → 数组 3 条（`id` `2042`/`2741`/`3927`）；`count=100` → 数组 **20** 条；`count=abc` → `404 {"error": "未找到图片"}`；对象比详情多 `originUrl`/`authorUrl`，Pixiv 行换 `piv.cosine.ren`。**S**：`count` 缺省 1、`Math.min(Math.max(count,1),20)`；查询 `findMany({where:{id:{in:randomIds}}})` **没有 `orderBy`**；`tags` 做 `replace(/#+/g,'#')` |
| `search(**params)` | `GET /api/search` | 21 | `{"success": true, "data": {hits, query, total, limit, offset, processingTimeMs}}`；`q=初音&limit=2` → `total` 255；不带参数 → `limit` 20、`total` 1000；`limit=500` → `limit` 回显 100 且 100 条；`offset=100000` → `offset` 回显 1000、`hits` 空；`limit=-1`/`offset=-5`/`sort=bogus` → 500 带 Meilisearch 英文 `message`；`platform=unknown` → 空命中；`tags` 大小写不敏感（`GenshinImpact` 与 `genshinimpact` 都是 166）、逗号＝AND（`原神,GenshinImpact` → 160、`原神` → 510）；`r18=true` → `total` 7 且 7 条命中 `r18` 全 `true`，`r18=false`/`r18=1` 的命中 `r18` 全 `false`；**命中字段集合不固定**（`tags=RuanMei` 有一条没有 `title`）。**S**：`q` 缺省 `''`、`limit` 缺省 20 且 `Math.min(…,100)`、`offset` 缺省 0、`sort` 缺省 `create_time:desc`、`tags.split(',')` 逐条 AND、`r18 !== null` 时按 `r18 === 'true'`、`data.total = estimatedTotalHits` |
| `search_suggestions(**params)` | `GET /api/search/suggestions` | 4 | `{"success": true, "data": {suggestions, query}}`，建议项是 `{"text", "type"}`；`q=miku&limit=2` → 2 条、`q=miku` → 10 条、`q=miku&limit=50` → 15 条；`q=a` → 空数组 200。**本轮没有读这条路由的源码**：默认 10 与「上限 20」都只算候选 |
| `tag_images(tag, **params)` | `GET /api/tag` | 8 | 裸数组、无 `total`；`GenshinImpact&start=0&limit=2` → 2 条、`start=2` 确实偏移到 `id` 4967；`genshinimpact` 同命中；`#GenshinImpact`、`原神,GenshinImpact`、`zzzznotexist` 都 → `[]` 200；缺 `tag` → `400 {"error": "标签参数缺失"}`；`RuanMei&limit=100` → 10 张图（8 个 `pid`，其 `tags` 里该标签共出现 14 次） |
| `tag_list()` | `GET /api/tags` | 1 | 裸数组 2128 项 `{"tag", "count"}`，按 `count` 倒序（`甜妹` 1309 … `脚镣` 1），表头 `X-Nextjs-Cache: HIT`。**S**：`count` 来自 `imageTag.groupBy(by: ['tag'], _count: {tag: true})`，清前导 `#` 合并后降序；表名（输入文档称 `imagetags`）本轮没读 schema，不当契约 |
| `artist_images(platform, authorid, **params)` | `GET /api/artist` | 7 | 列表分支 `{"images": […], "total": 78}`（`page=1`/`page=2` 各 2 条）；`infoOnly='true'` → **裸资料对象** `{"author": …}`，其中 `author` 与列表里的画师名不同；`infoOnly=1` 仍是列表分支；缺 `platform` → 400、`authorid=abc` → `500 {"error": "获取画师数据失败"}`、`infoOnly=true` 且无作品 → `404 {"error": "未找到该画师"}`。该路由本轮**没有读源码**，默认 `page`/`pageSize` 未测 |
| `artist_list(**params)` | `GET /api/artists` | 6 | `{"artists": […], "total": 1708, "hasNextPage": true}`；不带参数 20 条（`pageSize` 默认 20）；`page=1`/`page=2` 配 `pageSize=2&sortBy=artworks` 是第 1–2 名与第 3–4 名；`sortBy=lastUpdate` 按最新入库倒序；`sortBy=random` 与 `artworks` 不同；`sortBy=unknown` 与 `artworks` 同页一致（回落）。也没有读源码 |
| `search_index_status()` | `GET /api/search/admin` | 1 | 匿名 `200 {"success": true, "data": {"totalImages": 4953, "indexedImages": 3353, "indexHealth": "partial", "lastSyncTime": …}}`；`lastSyncTime` 与响应 `Date` 头同秒。**S**：报告由 `src/lib/search/indexing-service.ts` 的 `getIndexReport` 生成（`prisma.image.count()` 与索引文档数），`lastSyncTime` 写成 `new Date()` |
| `search_index_admin(action, **params)` | `POST /api/search/admin` | **0** | **本轮一次都没发**。**S**：路由按 `action` 分支、无鉴权检查，`initialize`/`index_all`/`sync_recent`/`rebuild` 回 `{success: true, message}`、`validate` 回 `{success: true, data}`、其它 `400 {success: false, error: 'Invalid action'}`，`index_all` 读 `batchSize`（缺省 100）、`sync_recent` 读 `hours`（缺省 24）——全部只有源码依据，**没有任何实测** |
| `artwork_revalidate(artwork_id, *, secret=None)` | `POST /api/artwork/revalidate` | **0** | **本轮一次都没发**（连空密钥的 401 都没试）。**S**：`secret` 与 `process.env.REVALIDATE_SECRET` 不等回 `401 {"message": "无效的密钥"}`、缺 `artworkId` 回 400、成功回 `{revalidated: true, now: Date.now()}`——只有源码依据 |
| `feed()` | `GET feed.xml` | 1 | `200 application/xml; charset=utf-8`，`X-Nextjs-Cache: HIT`；RSS 2.0，20 条 `<item>`，`guid` 前三 `3290`/`3288`/`3289`，`lastBuildDate` `Sun, 10 Aug 2025 13:07:22 GMT` |

合计 9+4+7+21+4+8+1+7+6+1+0+0+1 = **69** 次，状态分布 `200`×**57**、`400`×2、`404`×3、`500`×**7**；
格式分布 68 个 `application/json` 加 1 个 `application/xml; charset=utf-8`。
7 个 `500` 是：`/api/list?page=0`、`/api/list?page=-1`、`/api/artwork/abc`、
`/api/artist?platform=pixiv&authorid=abc`、`/api/search?limit=-1`、`/api/search?limit=2&offset=-5`、
`/api/search?sort=bogus&limit=2`。

## 权限与访问面

* **11 条读路由匿名可用**：本轮没有带任何凭据，全部拿到过 `200`（含 `GET /api/search/admin`）。
  站点没有本库能用的登录面，本库也不发明登录方法。
* **两条 `POST` 零样本**：
  * `artwork_revalidate` 需要站点服务端的 `REVALIDATE_SECRET`（**S**：路由把它与请求体里的 `secret` 比较）。
    本库的凭据字段是 `sites.cosine.revalidate_secret`，包内默认**空字符串**；构造时
    `revalidate_secret=None` 读配置，显式传空串也保持空。**空密钥照样发送**，由站点决定是否 `401`，
    本库不做本地校验、不报错、不重试；这个值只进这一个 JSON 正文，不会变成请求头，也不发给任何其它路由。
  * `search_index_admin` 按 `action` 改动站点搜索索引（**S**：`initialize`/`index_all`/`sync_recent`/`rebuild`
    会重建或删除索引，其中 `rebuild` 是删索引重建），**源码里这条 POST 没有任何鉴权检查**，
    所以匿名调用者也能触发。本库把它做成方法是为了接口完整，**不会自动调用、不检查权限、
    不提供 dry run、不重试、不回滚**。
* **媒体**：本库不下载图片字节，也没有取字节的方法；本轮对 `pbs.twimg.com`、`i.pximg.net`、
  `piv.cosine.ren`、`backblaze.cosine.ren` **一次请求都没有发**，`rawurl` / `thumburl` /
  `latestImageThumb` 只作为文本返回。取图要求（`Referer`、域名替换、`.webp` 兜底）见
  [方法参考的媒体一节](cosine-api.md#媒体地址只文档未下载)，全部是 T。
* **CORS 与限流**：本轮 69 个响应都带 `Origin` 请求头，回包里**没有** `Access-Control-Allow-Origin`，
  也**没有任何** `RateLimit-*` / `Retry-After`。只能说本轮样本没有这些头；
  输入文档记的 `OPTIONS /api/search` → `204` 本轮没有复测。**不要假设有配额**，
  本库也不做节流与退避。
* **写入面**：站点没有本库可用的上传、投稿、删除接口（输入文档称这些在 Telegram 机器人侧，T）；
  本库封装的两个 `POST` 一个刷新作品页缓存、一个管理索引，都不是用户内容接口，
  但**确实存在两个匿名可达的写入口**。

## 已被 L 或 S 支持的关键说法

这些说法本轮有 L 或 S 支持，可以当契约用（样本与细节见[方法参考](cosine-api.md)）：

* 四套外壳与归属：A `{"json", "meta"}`（`artwork_show`、`image_random`）、
  B `{"images", "total"}`（`image_list`、`artist_images` 列表分支）、
  B′ `{"artists", "total", "hasNextPage"}`（`artist_list`）、C `{"success", "data"}`
  （`search`、`search_suggestions`、`search_index_status`）、D 裸数组（`tag_images`、`tag_list`）；
  另加 `/api/artist` 的 `infoOnly='true'` 裸资料对象与 XML 的 `feed.xml`。
* `tags` 数组**可能含重复项**，且各路由对前导 `#` 的处理不一致：`artwork_show` 保留库内原样
  （`id=1` 的 8 项只有 4 个不同值、全带 `#`），`image_list` 与 `tag_images` 的样本去掉了 `#`；
  **S**：`image_random` 只把连续的 `#` 收成一个（`replace(/#+/g,'#')`），不补也不去。
* 本轮最新 100 行的 `size` 都是 `null`、`guest` 都是 `false`，老行 `id=1` 则是 `675622` / `true`；
  不由此推断两个字段描述入库年代，也不把输入文档的「新数据恒如此」当成保证。
* 站内 `id`（`1`、`5003`）与上游 `pid`（字符串 `1740331347254948074`、`2100902205171937298`）是两套编号；
  同一 `pid` 的多张图是多行（`RuanMei` 的 10 张图覆盖 8 个 `pid`）。
* 页数与条数的边界：`page=0`/`page=-1` → 500，超末页 → 空数组 200，`pageSize=0` → 空数组，
  `pageSize=-1` → 最旧 1 条；`search` 的 `limit` 被夹到 100、`offset` 被夹到 1000；
  `image_random` 的 `count` 被夹到 1–20。
* 搜索的 `total` 是索引的估算命中数（**S**：`estimatedTotalHits`）且会被截到 1000；
  索引落后于库（**L**：`indexedImages` 3353 / `totalImages` 4953），库里有 10 张的标签搜出来 9 条。
* 错误路径：缺参数 400、不存在的作品 404、非数字作品 id **500**、非数字 `authorid` **500**、
  `/api/search` 的非法 `limit`/`offset`/`sort` 是 500 且带 Meilisearch 英文 `message`。
* 搜索参数的缺省与比较（`q` 空串、`limit` 20/≤100、`offset` 0、`sort` `create_time:desc`、
  `tags` 逗号 AND、`r18` 用 `=== 'true'`）由 **S** 给出，并有 L 样本佐证（`r18=true` 的 7 条命中全 `true`，
  `r18=false`/`r18=1` 的命中全 `false`）。
* **搜索命中的字段集合不固定**：L 见到一条没有 `title` 的命中（`tags=RuanMei` 的 `id` `38`），
  `_formatted` 也一样，所以调用方要按「可能缺」取值；`id` 是字符串、`tags` 是字符串数组、
  `width`/`height` 是数字这些是稳定观察。
* `/api/artists` 的 `sortBy` 未知值静默回落 `artworks`（`unknown` 与 `artworks` 同页一致）。
* `search_index_status()` 的 `lastSyncTime` 在样本里等于响应时刻（**S**：实现在
  `src/lib/search/indexing-service.ts`，写成 `new Date()`），所以**不是可信的上次同步时间**。
* `/api/tags` 的 `count` 是标签记录行数而不是作品数（**S** + L），与 `search` 的 `total` 口径不同；
  `RuanMei` 的三个数字是 `count` 9、图片 10、标签出现 14 次。
* `/api/tags` 与 `/feed.xml` 的样本带 `X-Nextjs-Cache: HIT`（`/api/list` 的样本没有这个头），
  说明这些读响应可能是缓存过的；缓存时长与失效条件未测。
* RSS 是 RSS 2.0、20 条 item、`lastBuildDate` 来自缓存，且 `guid`（`3290`…）与当时
  `/api/list` 的最新行（`5003`…）不是同一代。

## 实测与输入文档的矛盾与需要更正的说法

逐项对照输入文档与 L/S。**「类型」列**说明这条该怎么处理：**矛盾**＝按 L/S 写，输入说法不成立；
**不完整/遗漏**＝输入说法本身不错但会误导或漏项；**未证实**＝本轮既没证实也没否证；
**不外推**＝L 样本与 S 实现都不支持把它写成契约。

| # | 输入文档说法 | 本轮 L/S | 类型 | 处理 |
| :--- | :--- | :--- | :--- | :--- |
| A | 导语说「作品编号沿用原站（Pixiv illust id、Tweet id）」 | L：站内 `id` 是自增行号（`1`、`5003`），上游编号是字符串 `pid`（`1740331347254948074`、`2100902205171937298`）；详情与页面用 `id` | 矛盾（措辞不精确） | 两套编号要分开写；输入文档自己的字段表已有正确区分 |
| B | 「全部接口 `GET`（只有两个写接口）、返回 `application/json`、路径都在 `/api/` 下」 | L：`GET /feed.xml` 返回 `application/xml; charset=utf-8` 的 RSS，不在 `/api/` 下，也不属于那两个写接口 | 不完整/遗漏 | 总述要带上 `feed.xml` 这条 XML 路由（输入文档第 6 节自己列了 RSS） |
| C | superjson `meta.values`「**恒为** `userid`/`authorid`/`create_time` 三个键」 | L：单对象样本是这三个裸键；`image_random(count=3)/(count=100)` 的**数组**样本里键带下标（`0.userid`、`14.authorid` …，20 条时是 60 个键），并且 `meta` 还多出 `referentialEqualities` | 矛盾 | 不能假定 `meta` 的键集合或子键；Python 调用方忽略 `meta` 即可 |
| D | 「`hits` 里 `id`、`authorid`、`pid`、`filename`、`create_time`、`tags` 都是**字符串**」 | L：前五个字段的值是字符串，但 `tags` 是**字符串数组**（元素为字符串）；`width`/`height` 仍是数字 | 矛盾（措辞） | 按「值是字符串」读；不要理解成 `tags` 本身是字符串 |
| E | 「不传 `q` / 空串命中**全库**」「`tags` 过滤结果小于 1000 时 `total` 就是全库精确数」 | L/S：`total` 取 `estimatedTotalHits`，只反映**索引**命中；同一时刻索引 3353 / 库 4953，`RuanMei` 库里有 10 张而搜索回 9 条；`total` 被截到 1000（不会先给大于 1000 的值） | 矛盾 | 只能写「索引里的估算命中数」；「大于 1000 时不可信」应改成「最多就是 1000，被截断了」 |
| F | 联想 `limit=50`「也只给 20 条」，并把 20 当精确数量 | L：`limit=50` 回 **15** 条；这**不推翻**「上限 20」，因为 15 ≤ 20，无法区分是上限还是候选只有 15 个 | 未证实（不是反例） | 上限 20 留未实测；不要写「一定给 20 条」 |
| G | `tag_images` 示例里 Pixiv 图片地址的时间路径写成 `/19:31:38/`（冒号） | L：同一行是 `https://i.pximg.net/img-original/img/2026/08/22/19/31/38/148746199_p0.jpg`，时间是**斜杠**分段 | 矛盾 | 按 L 写；不能照示例拼 `piv.cosine.ren` 地址 |
| H | `/feed.xml`「只含**最新** 20 条」 | L：确实 20 条，但 `guid` 是 `3290`/`3288`/`3289`，与当时 `/api/list` 的最新行 `5003`/`5002`… 不是同一代，`lastBuildDate` 是 `Sun, 10 Aug 2025 13:07:22 GMT`（缓存时间） | 矛盾（若「最新」指当前库） | 写「缓存中的 20 条」，**不要**当当前最新 20 张 |
| I | 「站点没有写接口（上传、投稿、删除都在 Telegram 机器人侧），API 侧不存在可测的写路径」 | 与它自己写的两个 `POST` 冲突，也与本轮读到的源码冲突：`POST /api/search/admin`（无鉴权、会重建/删除索引）与 `POST /api/artwork/revalidate` 都存在 | 矛盾 | 两个写入口要写出来并标「本轮绝不执行」；不要把「没有用户内容写接口」说成「没有写路径」 |
| J | 四类外壳的总括没有提 `/api/artist?infoOnly=true` 的裸资料对象；另有说法把 `POST /api/search/admin` 的成功体写成 `{success, data}` | L：资料分支是独立的裸对象，塞不进四类；**S**：`initialize`/`index_all`/`sync_recent`/`rebuild` 回 `{success: true, message}`，只有 `validate` 回 `{success: true, data}` | 不完整/遗漏 | 四类之外单列资料对象；`POST` 的响应形状按 S 分 action 写，且标明**未实测** |
| K | 「`/api/random` 的结果顺序按主键（不是随机）」 | L 的 3 条与 20 条样本确实是升序 `id`；但 **S** 的查询没有 `orderBy`，所以顺序**没有保证** | 不外推 | 写成「无排序保证」；样本升序只是样本，不是契约 |
| L | 把 `hits` 的字段当**统一集合**（`title`、`author`… 每条都有） | `tags=RuanMei` 的 `id='38'` 没有 `title`；实际分页示例又因 `id='2721'` 缺标题而首次退出1，移除标题必有假设后重跑退出0 | 矛盾 | 展示实际字段，保留缺失，不补默认标题；执行经过见[验证记录](verification.md#cosine匿名只读实测2026-09-20) |

另外几处按 L/S 收口、不算输入文档错误的地方：

* `meta` 之外，输入文档对 A 型信封（`json` 里是数据、`meta` 是类型表）的描述是对的；
* `tags` 数组可能重复、各路由 `#` 前缀不一致成立（`image_random` 的确切规则见 **S**）；
* `search` 命中不是完整作品对象（少 `userid`/`username`/`page`/`size`/`guest`/`extension`）成立，
  这是输入文档已有的删减说明，不算新错误；
* `RuanMei` 的 `count` 9 / 图片 10 / 标签出现 14 三个数字要一起写，避免有人把 `count` 当图片数。

## 未实测集中清单

以下**没有 L 或 S 支持**（或只有 S 依据但从未执行），一律不当契约：

* **两条 `POST`**：`search_index_admin()` 与 `artwork_revalidate()` 本轮零请求。
  成功状态码与响应、错误文案、耗时、能否中断与副作用全部未知；S 给出的 action 分支、
  `batchSize`/`hours` 缺省、`{success, message}` / `{success, data}` 形状与密钥比较
  **只是源码阅读结果**。公开文档不得把这些写成「已验证」。
* **默认值**：`artist_images` 的 `page`/`pageSize`（输入文档称 1 / 24）、`tag_images` 的 `limit`
  （称 32）、`artist_list` 的 `page`、`search_suggestions` 的 `limit`（称 10，L 与之一致但没读源码）
  都未实测；这些路由本轮没有读上游源码。
* **上限**：`search_suggestions` 的 `limit` 上限（称 20）未证实；列表路由的 `pageSize` 上限
  （`pageSize=100` 正常返回 100 条，更大的值没试）、`tag_images` 的 `limit` 上限都没有样本。
* **页码与条数的其它越界**：只证了 `page=0`、`page=-1`、`page=100000`、`pageSize=0`、`pageSize=-1`；
  其它负数、小数、空串、非数字、极大值都没试。输入文档给的解释（Prisma 的 `skip` 为负、
  `take:-1` 反向语义）是 T。
* **枚举**：`platform` 只证 `pixiv`/`twitter`/`unknown`；`indexHealth` 只见过 `partial`；
  `search_suggestions` 的 `type` 只见过 `general`；`sortBy` 只试过 4 个值；`sort` 只证
  `create_time:desc`（S 缺省）与 `width:asc` 被接受。S 给的是路由里的分支，
  不是这些取值的全集保证，也不是部署版本的保证。
* **排序与随机性的复测**：`artist_list` 的 `sortBy=random` 只发过一次，没有复测是否每次不同；
  `/api/random` 的返回顺序没有多次样本，也没有 `orderBy`，只能说无保证。
* **索引面**：索引落后库、同步策略、`initialize`/`index_all`/`sync_recent`/`rebuild`/`validate`
  各做什么、`lastSyncTime` 是否恒等于响应时刻，都未实测；只有一次 `GET` 样本与 S 的源码阅读。
* **RSS**：只证了 `200`、`Content-Type`、RSS 2.0、20 条 item、前三条 `guid` 与 `lastBuildDate`；
  item 内部字段清单、`/rss`、`/rss.xml`、`/feed` 是否都能到达同一份（输入文档称都 200）、
  缓存时长与失效条件都没复测。
* **字段集合的完整性**：搜索命中已经有一条缺 `title` 的样本，**哪些字段会缺、什么时候缺没有穷举**；
  作品对象、画师对象、`{"tag", "count"}` 是否也会有缺项，同样没有穷举（样本里它们都完整）。
* **媒体**：零请求。`Referer` 要求、`piv.cosine.ren` 免 `Referer`、Twitter 两种 URL 形态的实际行为、
  `backblaze.cosine.ren` 兜底是否可用（输入文档记 4 个样本全 404）全部未实测；
  本库也不提供任何下载方法。
* **跨域与配额**：`OPTIONS` 行为、正式 CORS 策略、是否有速率限制与配额都没有实测；
  本库不做节流、不退避、不自动重试。
* **缓存**：只有 `/api/tags` 与 `/feed.xml` 观察到 `X-Nextjs-Cache: HIT`；
  其它路由是否有静态缓存、缓存时长、失效条件都未知。
* **字段语义与表结构**：`title` 对 Twitter 是推文正文、`page` 的平台起点差异、
  `userid`/`username` 是投稿人、`create_time` 是入库时间、`size`/`guest` 的历史原因，
  还有表名与表结构（输入文档称 `images`/`imagetags`），都是 T；本轮没有读 schema 或投稿代码。
* **其它上游细节**：`src/lib/type.ts` 的平台枚举、`prisma/schema.prisma`、
  `src/lib/search/meilisearch-client.ts` 的可排序字段与索引名、第三方消费者
  （`TyrEamon/MtcACG-GO` 的 `internal/crawler/cosine_tag.go`）的做法，本轮都没有独立读。

## 排除项

* **不封装站点页面路由**：`/`、`/search`、`/tag/{标签}`、`/artists`、`/artist/{platform}/{uid}`、
  `/artwork/{id}`、`/about`、`/friends` 都是页面，不是 API。
* **不把 `backblaze.cosine.ren` 写进代码**，也不把它当主链路：输入文档自己记的 4 个样本都是 404，
  本轮零请求。
* **不加媒体下载方法**：预览与原图地址公式只写在[方法参考](cosine-api.md#媒体地址只文档未下载)里。
* **不发明登录或凭据获取方法**：站点没有本库能用的登录面；唯一的凭据是
  `sites.cosine.revalidate_secret`，只进一个 `POST` 正文。
* **不封装 `/rss`、`/rss.xml`、`/feed`**：只封装 `feed.xml` 这一条（输入文档称其余都是重写，未复测）。
* **不封装上游的其它端点或第三方客户端的私有路径**，也不把输入文档里的表名、枚举、上限搬进代码。
* **不在客户端做兜底**：不校验、不钳位、不补默认值、不拆信封、不嗅探格式、不重试、不改错误文案；
  站点返回什么就交给调用方什么。
* **两个 `POST` 只作为方法存在**：本项目不会自动调用它们，冒烟与示例里也不包含写请求。

## 依据文件与出处

| 依据 | 位置 | 等级 |
| :--- | :--- | :--- |
| 本轮匿名只读请求 | 69 次直接 HTTP 观察（`200`×57、`400`×2、`404`×3、`500`×7），逐条 URL、状态、表头与字段记在[验证记录](verification.md#cosine匿名只读实测2026-09-20) | L |
| 标签 `count` 算法 | [src/app/api/tags/route.ts](https://github.com/SomeACG/SomeACG-Next/blob/main/src/app/api/tags/route.ts) | S |
| `/api/random` 的 `count`、查询与 `tags` 处理 | [src/app/api/random/route.ts](https://github.com/SomeACG/SomeACG-Next/blob/main/src/app/api/random/route.ts) | S |
| `/api/search` 的参数解析、缺省与 `total` 来源 | [src/app/api/search/route.ts](https://github.com/SomeACG/SomeACG-Next/blob/main/src/app/api/search/route.ts) | S |
| `/api/search/admin` 的 GET 报告与 POST action 分支 | [src/app/api/search/admin/route.ts](https://github.com/SomeACG/SomeACG-Next/blob/main/src/app/api/search/admin/route.ts) | S |
| `/api/artwork/revalidate` 的密钥比较与响应 | [src/app/api/artwork/revalidate/route.ts](https://github.com/SomeACG/SomeACG-Next/blob/main/src/app/api/artwork/revalidate/route.ts) | S |
| 索引报告与 `lastSyncTime` 的实现 | [src/lib/search/indexing-service.ts](https://github.com/SomeACG/SomeACG-Next/blob/main/src/lib/search/indexing-service.ts) | S |
| 输入文档 | 接入时收到的《Cosine Gallery 接口文档（综合版）》，无公开核对链接 | T |
| 输入文档引用的其它上游文件与第三方项目 | `prisma/schema.prisma`、`src/lib/type.ts`、`src/lib/search/meilisearch-client.ts`、`TyrEamon/MtcACG-GO` 等，本轮没有独立读过 | T（未独立核实） |

上游文件本轮**没有 clone 仓库**，只按需只读单个文件，因此上表只给文件路径、不给行号；
这些源码也不是站点当前部署版本的证明。

客户端怎么构造、`last_call` 与 `revalidate_secret` 见[客户端用法](cosine.md)；
全部方法的参数、字段与示例见[方法参考](cosine-api.md)；
「想做什么 → 用哪个方法」见[能力入口](cosine-capabilities.md)。

[客户端用法](cosine.md) · [能力入口](cosine-capabilities.md) ·
[方法参考](cosine-api.md) · [验证记录](verification.md#cosine匿名只读实测2026-09-20)
