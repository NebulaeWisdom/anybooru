# Pixiv 方法参考

`Pixiv` 提供 **140 个原生方法**：Web 面 81 个（65 GET、16 POST），App 面 59 个（53 GET、6 POST），合计 118 GET 与 22 POST。方法名前缀 `web_` / `app_` 明确选择域名；同名资源在两面的参数、认证与 JSON 字段并不相同。

构造、凭据、通用 `request()` 和 `last_call` 见 [客户端用法](pixiv.md)；按目的找方法见 [能力入口](pixiv-capabilities.md)；来源分歧与排除理由见 [契约附注](pixiv-contract-notes.md)；真实命令及逐请求结果见 [实测记录](verification.md#pixiv匿名只读实测2026-10-08)。

本页区分第三方源码提供的成功结构与匿名 HTTP 观察。所有写方法仅源码对齐，未执行；需要登录的成功路径没有凭据实测。完整返回值保留，不把 HTTP 200 的 `error:true` 改写成异常。

## Web API（`www.pixiv.net`，81 个方法）

本面方法名带 `web_` 前缀，由 `PixivApi_Mixin` 提供，内部都走 `Pixiv.request(..., api='web')`（web 是默认面）。
本面共 **81 个原生方法**（65 个 `GET` + 16 个 `POST`）。所有方法原样返回完整 JSON，**不剥 `body` 层**；app 面的方法见另一节。

## 依据与分级

| 标记 | 来源 | 等级与说明 |
| :--- | :--- | :--- |
| **W** | 社区客户端 [YieldRay/pixiv-web-api](https://github.com/YieldRay/pixiv-web-api/tree/main/packages/pixiv-web-api/src/api) 的单个 `.ts` 文件 | **社区客户端源码，不是官方服务端规范**。逐方法给出具体文件链接；它自己的 `request.ts` 会剥 `body`、带重试与 CSRF 抓取，**这些都没照抄**。 |
| **N** | [FreeNowOrg/PixivNow 文档](https://raw.githubusercontent.com/FreeNowOrg/PixivNow/master/docs/pixiv-web-api.md) | 社区文档。 |
| **D** | [daydreamer-json/pixiv-ajax-api-docs](https://raw.githubusercontent.com/daydreamer-json/pixiv-ajax-api-docs/main/README.md) | 社区文档，作者自述已过时。 |
| **S** | [pixivsource.pages.dev/PixivWebApi](https://pixivsource.pages.dev/PixivWebApi) | 社区小说资源参考。 |
| **P** | pixivpy3 `aapi.py` 的 `showcase_article` | 第三方客户端源码。 |
| **实测** | 本仓库匿名只读样本（真实 URL、状态码、字段） | 比来源更强，但只证明样本本身。 |

**没有任何来源是官方服务端规范**；本轮未取得完整的官方 web API 文档。来源之间冲突时以实测为准；
来源未声明的返回键一律写“源码未声明”，不编造成功结构。

> **证据粒度**：方法条里标“实测”的是**路由级证据** —— 直接向该 URL 发过匿名只读请求，看到的是站点侧的
> 路径、状态码与字段；它**不等于**对应的 Python 方法被执行过。Python 方法级的执行记录单独写在
> `docs/verification.md`，两者不要混称。来源未给、也没实测到的写“未实测”。

## 客户端约定（web 面）

- 通用入口：`request(method, path, *, api='web', params=None, data=None, form=None, headers=None, response_format='json')`。
  原生方法只是把路由与参数拼好后调它；能传什么、有没有权限全由服务端决定。
- 路径：相对 `https://www.pixiv.net` 拼；`path` 里每个资源段都按 `quote(str(value), safe='')` 转义（`web_search_*` 的
  `word` 与 `web_search_tags` 的 `tag` 也在路径段里）。
- 查询参数：原样交给共享编码器 —— 字典编成 `a[b]`、列表/元组编成**重复键** `key[]`、`None` 丢弃、布尔发小写。
  `web_illust_recommend_illusts(illust_ids, ...)` 的 `illust_ids` 也走同一编码器（编成 `illust_ids[]=149021929&illust_ids[]=135613111`）：
  **实测带方括号的重复键是 `200`，来源 W 声明的“不带方括号”写法实测是 `400`**；以实测为准，客户端不做任何特例。
- 没有本地校验、没有默认分页、没有自动翻页、不重试、不猜格式；来源里出现的“建议默认值”只在参数表里注明，**不代填**。
- 返回：完整 JSON。**HTTP 200 而正文 `error` 为 `true` 时也当数据返回，不转成异常**；HTTP 非 2xx 由共享传输抛
  `AnybooruHTTPError`，`.data` 是解析后的正文（解不出 JSON 时为 `None`）。
- 实测到的信封不止一种，别当成一种：
  - 多数读取：`{"error": false, "message": "", "body": {…}}`（如 `ajax/illust/{id}`、`ajax/user/{id}`）。
  - 搜索面：`{"error": false, "body": {…}}`，**没有 `message` 键**（实测 `ajax/search/artworks/cat`、`/search/tags/cat`、
    `/ranking/novel`、`/search/suggestion`）。
  - 排行榜错误：`{"error": "ランキング集計の範囲外です"}`，`error` 是**字符串**（实测 `ranking.php?p=10000`，HTTP `404`）。
  - 一般 `400`：`{"error": true, "message": "不正なリクエストです。", "body": []}`（实测多条）。
  - `404` 且 `message` 为空：`{"error": true, "message": "", "body": []}`（实测 `ajax/illust/59580629`）。
  - **`HTTP 200` 也可能是失败**：`ajax/illusts/comments/replies?comment_id=233757844` 返回 `200`，正文却是
    `{"error": true, "message": "", "body": []}`，读不到 `hasNext`。所以“HTTP 200”不等于这条路由给你有效数据。

## 共享参数表

下表被多个方法引用，**每个方法只列它自己特有的参数**，并在这里指回本表。

### 表 A：`lang`

| 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `lang` | 查询 | 语言标记（如 `ja`、`en`） | 请求返回文案/标签翻译的语言 | 未规定（由站点按会话与 Accept-Language 决定） | `lang='en'` |

### 表 B：`work_type`（多路由方法共用的**路径段**）

`work_type` 是**字面路径段**，客户端不做同义词映射，也不猜别名；传别的值就是拼出别的路径，由服务端判定。

| 值 | 出现在哪些路由 | 含义 |
| :--- | :--- | :--- |
| `illusts` | `ajax/user/{user_id}/{work_type}/tag`、`/tags`、`/bookmarks`、`/bookmark/tags`；`ajax/{work_type}/bookmarks/*`；`ajax/{work_type}/like` | 插画 |
| `manga` | 同上 `tag`、`tags` | 漫画 |
| `illustmanga` | 同上 `tag`、`tags` | 插画 + 漫画 |
| `novels` | 同上 `tag`、`tags`、`bookmarks`、`bookmark/tags`；`ajax/{work_type}/bookmarks/*`；`ajax/{work_type}/like` | 小说 |
| `illust` | `ajax/follow_latest/{work_type}`、`ajax/tags/frequent/{work_type}`、`ajax/{work_type}/series/{id}/*` | 插画（单数，另一套路由） |
| `novel` | 同上 | 小说（单数） |

### 表 C：搜索过滤参数（`web_search_artworks` / `web_search_illustrations` / `web_search_manga` / `web_search_novels` 共用）

| 名称 | 取值 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `order` | 实测用过 `date_d`；其余未规定 | 结果排序 | 未规定 | `order='date_d'` |
| `mode` | 实测用过 `all`；其余未规定 | 年龄分级/模式 | 未规定 | `mode='all'` |
| `p` | 页码（整数，实测从 `1` 起） | 第几页 | 未规定（服务端默认页） | `p=1` |
| `s_mode` | 实测用过 `s_tag`；其余未规定 | 标签匹配方式 | 未规定 | `s_mode='s_tag'` |
| `type` | 各路由不同，见方法条 | 作品类型筛选 | 未规定 | `type='all'` |
| `ai_type`、`dgw`、`wlt`、`wgt`、`hlt`、`hgt`、`ratio`、`tool`、`scd`、`ecd`、`blt`、`bgt` | 来源只给参数名，未给取值 | 搜索过滤字段（关键词、宽高/宽高比、工具、日期、书签数等） | 未规定 | 见各方法示例 |
| `work_lang` | 来源只给名字 | 作品语言（`search_manga` / `search_novels` 有） | 未规定 | `work_lang='ja'` |

> 本库不校验这些取值，原样转发；表里标“未规定”的枚举**不是**客户端限制，而是来源与样本都没写。

### 表 D：`offset` + `limit` 分页

多个列表方法（插画/小说评论、用户关注/粉丝等）用 `offset`（跳过条数）+ `limit`（本页条数）。具体默认值见各方法条，
未在来源或实测中出现的默认值一律写“未规定”，**客户端不代填**。

---

## 插画 illust

### `web_illust_show(illust_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/illust/{illust_id}`（W [`illust.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/illust.ts) + 实测）。
- 给什么 → 返回什么：给一张插画的编号（如 `149040133`），返回完整信封 `{"error": false, "message": "", "body": {…}}`；
  `body` 里是这张插画：`illustId` / `illustTitle` / `illustComment` / `id` / `title` / `description`、`illustType`、
  `createDate` / `uploadDate`、`restrict` / `xRestrict` / `sl`、`urls`（`mini` / `thumb` / `small` / `regular` / `original`）、
  `tags`（`tags` 是标签对象数组，每项含 `tag` / `locked` / `deletable`，**`userId` / `userName` 是可选的**：实测作者自带的
  初始标签带这两个键、后续标签只有 `tag` / `locked` / `deletable`；这是观察到的相关性，不是“某类标签必有或必无”的规则，
  取用时先判键存在）、`userId` / `userName` / `userAccount`、
  `width` / `height` / `pageCount`、计数 `bookmarkCount` / `likeCount` / `commentCount` / `responseCount` / `viewCount`、
  `bookMarkData` / `likeData` / `isBookmarkable` / `seriesNavData` / `alt` / `aiType` / `userIllusts` / `pollData` /
  `titleCaptionTranslation` / `zoneConfig` / `extraData` 等（实测 `body` 键共 60+ 个，按原样返回）。
- 参数：

  | 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `illust_id` | 路径（必填） | 数字或数字串 | 插画编号 | — | `149040133` |
  | `full` | 查询 | 来源只给名字 | 返回更完整的作品数据 | 未规定 | `full=1` |
  | `lang` | 查询 | 见表 A | 语言 | 未规定 | `lang='en'` |

- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illust/149040133
      detail = client.web_illust_show(149040133)
      print(detail['error'], detail['body']['illustId'], detail['body']['title'])
      print(detail['body']['urls']['original'], detail['body']['width'], detail['body']['height'])
      print([tag['tag'] for tag in detail['body']['tags']['tags']])
  ```

- 实测：`149040133` → `200`，`application/json; charset=utf-8`；已不存在的 `59580629` → `404`，正文
  `{"error": true, "message": "", "body": []}`；`illust/0` → `400`，正文 `{"error": true, "message": "不正なリクエストです。", "body": []}`。

### `web_illust_pages(illust_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/illust/{illust_id}/pages`（W `illust.ts` + 实测）。
- 给什么 → 返回什么：给插画编号，返回完整信封，`body` 是**每页一张的数组**；每项有 `urls`（`thumb_mini` / `small` / `regular` / `original`）
  与 `width` / `height`。多页插画用它拿全部原图地址。
- 参数：`illust_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illust/149040133/pages
      pages = client.web_illust_pages(149040133)
      for page in pages['body']:
          print(page['urls']['original'], page['width'], page['height'])
  ```

- 实测：`200`；`149040133` 的 `body` 是长度 1 的数组，`body[0].urls.original` 是 `i.pximg.net/img-original/...png`。

### `web_ugoira_metadata(illust_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/illust/{illust_id}/ugoira_meta`（W `illust.ts`）。
- 给什么 → 返回什么：给动图（ugoira）插画编号，返回完整信封，`body` 有 `src` / `originalSrc`（动图 zip 地址）、
  `mime_type`、`frames`（每帧 `file` / `delay`）。**只返回地址，不下载媒体**。
- 参数：`illust_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illust/<动图编号>/ugoira_meta
      meta = client.web_ugoira_metadata(1234567)
      print(meta['body']['originalSrc'], meta['body']['mime_type'], len(meta['body']['frames']))
  ```

- 实测：`illust/150572937/ugoira_meta` → `200`；`body` 键 `['src', 'originalSrc', 'mime_type', 'frames']`，
  `frames` 是 `{file, delay}` 数组（样本 9 帧，`delay` 200，`mime_type` `image/jpeg`）。

### `web_illust_new(**params)`

- 路由：`GET https://www.pixiv.net/ajax/illust/new`（W `illust.ts`；D 同）。
- 给什么 → 返回什么：返回完整信封，`body` 是新投稿作品数据（W 未声明逐字段；来源只写“new-work data”）。
- 参数：

  | 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `lastId` | 查询 | 上一批最后一条的 id | 游标式翻页 | 未规定 | `lastId='149040133'` |
  | `limit` | 查询 | 整数 | 本批条数 | 未规定 | `limit=20` |
  | `type` | 查询 | 来源只给名字 | 作品类型 | 未规定 | `type='illust'` |
  | `r18` | 查询 | 来源只给名字 | 是否含 R18 | 未规定 | `r18='true'` |

- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illust/new?limit=20
      latest = client.web_illust_new(limit=20)
      print(latest['error'], latest['message'])
  ```

- 实测：`lastId=0&limit=2&type=illust&r18=False` 与 `r18=0` 都是 `400`（正文通用错误信封）；**没有成功样本**。

### `web_illust_recommend_init(illust_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/illust/{illust_id}/recommend/init`（W [`illustRecommend.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/illustRecommend.ts) + 实测）。
- 给什么 → 返回什么：给插画编号，返回完整信封，`body` 有 `illusts`（相关插画，**数组**，每项与搜索列表的插画条目同形：
  `id` / `title` / `url` / `tags` / `userId` / `userName` / `width` / `height` / `pageCount` 等）、`nextIds`（继续查询用的 id 数组）、`details`。
  客户端**不自动**拿 `nextIds` 去调 `web_illust_recommend_illusts`。
- 参数：`illust_id`（路径，必填）、`limit`（查询，整数，条数）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illust/149040133/recommend/init?limit=2
      init = client.web_illust_recommend_init(149040133, limit=2)
      print(len(init['body']['illusts']), len(init['body']['nextIds']))
  ```

- 实测：`200`；`limit=2` 时 `body.illusts` 长度 2、`body.nextIds` 长度 178。

### `web_illust_recommend_illusts(illust_ids, **params)`

- 路由：`GET https://www.pixiv.net/ajax/illust/recommend/illusts`（W `illustRecommend.ts` + 实测）。
- 给什么 → 返回什么：给一串插画编号，返回完整信封，`body.illusts` 是插画数组（每项有 `id` / `title` / `url` / `tags` /
  `userId` / `userName` / `width` / `height` / `pageCount` / `illustType`，并多一个 `type`（实测 `'illust'`））。
- 参数：

  | 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `illust_ids` | 查询（必填） | 编号列表 | 要查的相关插画编号 | — | `[149021929, 135613111]` |
  | `lang` | 查询 | 见表 A | 语言 | 未规定 | `lang='en'` |

  **编码**：走共享编码器，编成**带方括号**的重复键 `illust_ids[]=149021929&illust_ids[]=135613111`（实测 `200`）；
  来源 W 声明的**不带方括号**写法（`illust_ids=149021929&illust_ids=135613111`）**实测是 `400`**，不采用。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illust/recommend/illusts?illust_ids[]=149021929&illust_ids[]=135613111
      recommended = client.web_illust_recommend_illusts([149021929, 135613111])
      for illust in recommended['body']['illusts']:
          print(illust['id'], illust['title'], illust['type'])
  ```

- 实测：带方括号 → `200`，`body` 顶层键只有 `['illusts']`；不带方括号 → `400`（正文通用错误信封）。

### `web_illust_discovery(**params)`

- 路由：`GET https://www.pixiv.net/ajax/illust/discovery`（N + 实测）。
- 给什么 → 返回什么：返回完整信封，`body.illusts` 是发现页插画数组。
- 参数：`mode`（查询，实测用过 `safe`；`all` 未测）、`max`（查询，条数；**实测上限 18**）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illust/discovery?mode=safe&max=18
      discovery = client.web_illust_discovery(mode='safe', max=18)
      print(len(discovery['body']['illusts']))
  ```

- 实测：`mode=safe&max=2` → `200`（`illusts` 2 条）；`mode=safe&max=18` → `200`（18 条）；**`max=19` 与 `max=100` → `400`**。

### `web_illust_series(series_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/series/{series_id}`（W [`illustSeries.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/illustSeries.ts)）。
- 给什么 → 返回什么：给系列编号，返回完整信封，`body` 有 `tagTranslation` / `thumbnails` / `illustSeries` / `requests` /
  `users` / `page` / `extraData` / `zoneConfig`（`page` 是系列内分页信息）。
- 参数：`series_id`（路径，必填）、`p`（查询，页码）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/series/336340?p=1
      series = client.web_illust_series(336340, p=1)
      print(series['body']['page'])
  ```

- 实测：`ajax/series/257832?p=1` → `200`；`body` 顶层键 `['tagTranslation', 'thumbnails', 'illustSeries', 'requests',
  'users', 'page', 'extraData', 'zoneConfig']`。

### `web_illust_comments(illust_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/illusts/comments/roots`（W [`illustsComments.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/illustsComments.ts) + 实测）。
- 给什么 → 返回什么：给插画编号，返回完整信封，`body` 有 `comments`（评论数组，每项含 `id` / `comment` / `userId` /
  `userName` / `isDeletedUser` / `img` / `stampId` / `commentDate` / `commentParentId` / `commentUserId` / `editable` / `hasReplies`）
  与 `hasNext`（是否还有下一页）。
- 参数：

  | 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `illust_id` | 查询（必填） | 插画编号 | 取哪张插画的评论 | — | `149040133` |
  | `offset` | 查询 | 整数 | 跳过条数 | 未规定（W 注释写首次 `0`，之后 `3`，**这是注释不是默认值**） | `offset=0` |
  | `limit` | 查询 | 整数 | 本页条数 | 未规定（W 注释写首次 `3`，之后 `50`） | `limit=3` |
  | `lang` | 查询 | 见表 A | 语言 | 未规定 | `lang='en'` |

- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illusts/comments/roots?illust_id=149040133&offset=0&limit=2
      comments = client.web_illust_comments(149040133, offset=0, limit=2)
      print(len(comments['body']['comments']), comments['body']['hasNext'])
  ```

- 实测：`200`；`offset=0&limit=2` 时 `body.comments` 2 条，`body.hasNext` 可读。

### `web_illust_comment_replies(comment_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/illusts/comments/replies`（W `illustsComments.ts`）。
- 给什么 → 返回什么：给一条评论的编号，返回完整信封，`body` 有 `comments`（回复数组）与 `hasNext`。
- 参数：`comment_id`（查询，必填，评论编号）、`page`（查询，整数页码）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illusts/comments/replies?comment_id=<评论编号>&page=1
      replies = client.web_illust_comment_replies(123456, page=1)
      print(len(replies['body']['comments']), replies['body']['hasNext'])
  ```

- 实测：`comment_id=233757844&page=1` → **HTTP `200` 但正文 `{"error": true, "message": "", "body": []}`**，
  `body` 是空数组、**读不到 `hasNext`**。这条不能当成功样本；有效 `comment_id` 与返回结构仍**未实测**。

---

## 小说 novel

### `web_novel_show(novel_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/{novel_id}`（W [`novels.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/novels.ts) + 实测）。
- 给什么 → 返回什么：给小说编号，返回完整信封，`body` 有 `id` / `title` / `content`（正文）/ `userId` / `userName` /
  `coverUrl` / `pageCount` / `characterCount` / `wordCount` / `readingTime` / `useWordCount` / `language` /
  `description` / `tags` / `seriesNavData` / `userNovels`、计数 `bookmarkCount` / `likeCount` / `commentCount` /
  `markerCount` / `viewCount`、`xRestrict` / `restrict` / `isOriginal` / `isBungei` / `hasGlossary` / `textEmbeddedImages` 等。
- 参数：`novel_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/11165421
      novel = client.web_novel_show(11165421)
      print(novel['body']['id'], novel['body']['title'], novel['body']['wordCount'])
  ```

- 实测：`11165421` → `200`，`body` 键含上述字段。

### `web_user_novels(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/novels`（W [`userNovels.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/userNovels.ts) + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 是**以小说编号为顶层键**的小说数据对象。
- 参数：`user_id`（路径，必填）、`ids`（查询，列表，只要这些小说编号）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/38475999/novels?ids[]=11165421&ids[]=11165886
      novels = client.web_user_novels(38475999, ids=[11165421, 11165886])
      print(list(novels['body']))
  ```

- 实测：`200`；`body` 顶层键就是 `11165421` / `11165886`（小说编号本身）。

### `web_novel_discovery(**params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/discovery`（N + 实测）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `novels`（数组）与 `details`。
- 参数：`mode`（查询，实测用过 `safe`）、`limit`（查询，条数）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/discovery?mode=safe
      discovery = client.web_novel_discovery(mode='safe')
      print(len(discovery['body']['novels']))
  ```

- 实测：`mode=safe`（不传 `limit`）→ `200`，`body.novels` 59 条（**这是本次样本条数，不是固定每页数**）。

### `web_novel_new(**params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/new`（S）。
- 给什么 → 返回什么：返回完整信封，`body` 是新小说数据（**S 未声明逐字段**）。
- 参数：`lastId`（查询，游标）、`limit`（查询，条数）、`r18`（查询，是否含 R18）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/new?limit=20
      latest = client.web_novel_new(limit=20)
      print(latest['error'], latest['message'])
  ```

- 实测：`lastId=0&limit=2&r18=false` → `400`（正文通用错误信封）；**没有成功样本**。

### `web_novel_recommend_init(novel_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/{novel_id}/recommend/init`（W [`novelRecommend.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/novelRecommend.ts) + 实测）。
- 给什么 → 返回什么：给小说编号，返回完整信封，`body` 有 `novels`（数组）、`nextIds`（数组）、`details`。
- 参数：`novel_id`（路径，必填）、`limit`（查询，条数）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/11165421/recommend/init?limit=2
      init = client.web_novel_recommend_init(11165421, limit=2)
      print(len(init['body']['novels']), len(init['body']['nextIds']))
  ```

- 实测：`200`；`limit=2` 时 `body.novels` 2 条、`body.nextIds` 长度 178。

### `web_novel_recommend_novels(**params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/recommend/novels`（N + 实测）。
- 给什么 → 返回什么：返回完整信封，`body.novels` 是小说数组。
- 参数：`novelIds`（查询，列表；实测用 `novelIds[]=` 重复键）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/recommend/novels?novelIds[]=16448475&novelIds[]=18112696
      recommended = client.web_novel_recommend_novels(novelIds=[16448475, 18112696])
      print(len(recommended['body']['novels']))
  ```

- 实测：`200`；`novelIds[]=…` 两条返回 `body.novels` 2 条。

### `web_novel_editors_picks(**params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/editors_picks`（S）。
- 给什么 → 返回什么：返回完整信封，`body` 是编辑精选（S 未声明逐字段）。
- 参数：`limit`（查询，条数）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/editors_picks?limit=10
      picks = client.web_novel_editors_picks(limit=10)
      print(picks['error'], picks['message'])
  ```

- 实测：`limit=2&lang=ja` → `200`；`body` 顶层键 `['tagTranslation', 'thumbnails', 'illustSeries', 'requests', 'users',
  'page', 'zoneConfig']`。

### `web_top_novel(**params)`

- 路由：`GET https://www.pixiv.net/ajax/top/novel`（S）。
- 给什么 → 返回什么：返回完整信封，`body` 是小说首页数据（S 未声明逐字段）。
- 参数：`mode`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/top/novel
      top = client.web_top_novel()
      print(top['error'], top['message'])
  ```

- 实测：`mode=all&lang=ja` → `200`；`body` 顶层键 `['page', 'thumbnails', 'users', 'tagTranslation', 'novelSeries',
  'requests', 'zoneConfig']`。

### `web_novel_genre(genre, **params)`

- 路由：`GET https://www.pixiv.net/ajax/genre/novel/{genre}`（S）。
- 给什么 → 返回什么：给题材（`genre`，路径段），返回完整信封，`body` 是该题材的小说列表（S 未声明逐字段）。
- 参数：`genre`（路径，必填，题材标识）、`mode`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/genre/novel/<题材>
      listing = client.web_novel_genre('fantasy')
      print(listing['error'], listing['message'])
  ```

- 实测：`genre=romance&mode=safe&lang=ja` → `200`；`body` 顶层键 `['page', 'zoneConfig', 'extraData', 'tagTranslation',
  'thumbnails', 'illustSeries', 'requests', 'users']`。

### `web_novel_bookmark_data(novel_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/{novel_id}/bookmarkData`（S + 实测）。
- 给什么 → 返回什么：给小说编号，返回完整信封，`body` 有 `id`（**数字**）/ `isBookmarkable` / `bookmarkData`（当前登录态的收藏状态）。
- 参数：`novel_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/11165421/bookmarkData
      bookmark_data = client.web_novel_bookmark_data(11165421)
      print(bookmark_data['body']['isBookmarkable'], bookmark_data['body']['bookmarkData'])
  ```

- 实测：`11165421` → `200`，`body` = `{"id": 11165421, "isBookmarkable": false, "bookmarkData": null}`
  （匿名时 `isBookmarkable` 为 `false`、`bookmarkData` 为 `null`，这是**该样本**的值）。

### `web_novel_comments(novel_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novels/comments/roots`（W [`novelsComments.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/novelsComments.ts) + 实测）。
- 给什么 → 返回什么：给小说编号，返回完整信封，`body` 有 `comments`（每项含 `id` / `comment` / `userId` / `userName` /
  `img` / `stampId` / `stampLink` / `commentDate` / `commentRootId` / `commentParentId` / `replyToUserId` / `replyToUserName` /
  `editable` / `hasReplies`）与 `hasNext`。
- 参数：`novel_id`（查询，必填）、`offset`（查询，跳过条数）、`limit`（查询，本页条数）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novels/comments/roots?novel_id=11165421&offset=0&limit=2
      comments = client.web_novel_comments(11165421, offset=0, limit=2)
      print(len(comments['body']['comments']), comments['body']['hasNext'])
  ```

- 实测：`200`；`offset=0&limit=2` 时 `body.comments` 2 条、`body.hasNext` 可读。

### `web_novel_comment_replies(comment_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novels/comments/replies`（W `novelsComments.ts` + 实测）。
- 给什么 → 返回什么：给评论编号，返回完整信封，`body` 有 `comments` 与 `hasNext`。
- 参数：`comment_id`（查询，必填）、`page`（查询，页码）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novels/comments/replies?comment_id=33074564&page=1
      replies = client.web_novel_comment_replies(33074564, page=1)
      print(len(replies['body']['comments']), replies['body']['hasNext'])
  ```

- 实测：`200`；`comment_id=33074564&page=1` 时 `body.comments` 1 条、`body.hasNext` = `false`。

### `web_novel_series(series_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/series/{series_id}`（W [`novelSeries.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/novelSeries.ts) + 实测）。
- 给什么 → 返回什么：给系列编号，返回完整信封，`body` 有 `id` / `userId` / `userName` / `title` / `caption` / `language` /
  `tags` / `publishedContentCount` / `publishedTotalCharacterCount` / `publishedTotalWordCount` / `publishedReadingTime` /
  `firstNovelId` / `latestNovelId` / `displaySeriesContentCount` / `total` / `firstEpisode` / `watchCount` / `maxXRestrict` /
  `cover` / `isWatched` / `isNotifying` / `xRestrict` / `isOriginal` / `isConcluded` / `aiType` / `hasGlossary` 等。
- 参数：`series_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/series/1122424
      series = client.web_novel_series(1122424)
      print(series['body']['title'], series['body']['publishedContentCount'])
  ```

- 实测：`1122424` → `200`，`body` 键含上述字段。

### `web_novel_series_content(series_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/series_content/{series_id}`（W `novelSeries.ts` + 实测）。
- 给什么 → 返回什么：给系列编号，返回完整信封，`body` 有 `tagTranslation`、`thumbnails`（含 `illust` / `novel` / `novelSeries` /
  `novelDraft` / `collection`）、`illustSeries`、`requests`、`users`，以及 `page`：**实测 `page` 里是 `seriesContents`（不是只有
  `novels`）**，另有 `seriesId` / `isSetCover` / `isFirstPage` / `isLastPage` / `titleCaptionTranslation` 等。
- 参数：

  | 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `series_id` | 路径（必填） | 系列编号 | 取哪个系列 | — | `1122424` |
  | `limit` | 查询 | 整数 | 本页条数 | 未规定 | `limit=2` |
  | `last_order` | 查询 | 整数 | 从哪个 order 之后取 | 未规定 | `last_order=0` |
  | `order_by` | 查询 | 源码字面 `asc` / `dsc` / 字符串 | 排序方向（源码字面就是 `dsc`，**不是笔误，不要擅自改成 `desc`**） | 未规定 | `order_by='asc'` |
  | `page` | 查询 | 整数 | 页码 | 未规定 | `page=1` |
  | `size` | 查询 | 整数 | 每页条数 | 未规定 | `size=30` |
  | `lang` | 查询 | 见表 A | 语言 | 未规定 | `lang='en'` |

- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/series_content/1122424?limit=2&last_order=0&order_by=asc
      content = client.web_novel_series_content(1122424, limit=2, last_order=0, order_by='asc')
      print(content['body']['page']['isLastPage'], len(content['body']['page']['seriesContents']))
  ```

- 实测：`200`；`body` 顶层键 `['tagTranslation', 'thumbnails', 'illustSeries', 'requests', 'users', 'page']`。

### `web_novel_series_titles(series_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/novel/series/{series_id}/content_titles`（W `novelSeries.ts` + 实测）。
- 给什么 → 返回什么：给系列编号，返回完整信封，`body` 是 `[{"id", "title", "available"}]` 数组 —— **实测没有 `order` 字段**
  （W 曾声明过 `order`，以实测为准，不要给读者 `order`）。
- 参数：`series_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/novel/series/1122424/content_titles
      titles = client.web_novel_series_titles(1122424)
      print([(item['id'], item['available']) for item in titles['body']])
  ```

- 实测：`200`；`body` 长度 8，`body[0]` = `{"id": "11165421", "title": "その距離でふれたい。", "available": true}`。

---

## 搜索 search

四个 `web_search_*`（artworks / illustrations / manga / novels）都走 `ajax/search/{kind}/{word}`，`word` **同时进路径段与查询串**，
共用表 C 的过滤参数；各自 `type` 取值不同。

> **列表里可能混有广告占位行**：`search/artworks`、`search/illustrations`、`search/manga` 的样本都是 60 个槽位
> = 59 个作品 + 1 个 `{"isAdContainer": true}`；但 `search/novels` 的样本是 30 条作品、**没有**占位行，
> `search/top` 聚合结果里 `illust` 24 / `manga` 24 / `novel` 8 也没有。**不要把“60 槽位 1 占位”套到所有搜索面**：
> 条数与占位行都只属于各自路由的样本。稳妥做法是遍历前先判 `item.get('isAdContainer')`，不要对每一项直接取 `item['id']`
> （占位行没有 `id`，会 `KeyError`）。占位行照原样返回，客户端**不过滤、不改写**。

### `web_search_artworks(word, **params)`

- 路由：`GET https://www.pixiv.net/ajax/search/artworks/{word}`（W [`search.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/search.ts) / N + 实测）。
- 给什么 → 返回什么：给关键词（如 `'cat'`），返回完整信封 `{"error": false, "body": {…}}`（**实测没有 `message` 键**）；
  `body.illustManga.data` 是插画/漫画数组，**每项不一定都是作品**：实测 60 个槽位 = 59 个作品 + 1 个
  `{"isAdContainer": true}` 占位行（占位行没有 `id`）；作品项有 `id` / `title` / `url` / `tags`（标签名数组）/ `userId` /
  `userName` / `width` / `height` / `pageCount` / `illustType` / `xRestrict` / `aiType` / `isBookmarkable` / `profileImageUrl` /
  `createDate` 等；`body.illustManga` 还有 `total` 与 `lastPage`。`body` 顶层另有 `suggestChips` / `popular` /
  `relatedTags` / `tagTranslation` / `zoneConfig` / `extraData`。
- 参数：`word`（路径 + 查询，必填）+ 表 C 的 `order` / `mode` / `p` / `s_mode` / `type`（实测用过 `type='all'`）/ `ai_type` /
  `dgw` / `wlt` / `wgt` / `hlt` / `hgt` / `ratio` / `tool` / `scd` / `ecd` / `blt` / `bgt` / `lang`。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/artworks/cat?word=cat&order=date_d&mode=all&p=1&s_mode=s_tag&type=all
      result = client.web_search_artworks('cat', p=1, order='date_d', mode='all', s_mode='s_tag', type='all')
      # 先剔掉广告占位行，再按作品取字段
      works = [item for item in result['body']['illustManga']['data'] if not item.get('isAdContainer')]
      for artwork in works[:3]:
          print(artwork['id'], artwork['title'], artwork['userName'])
      print(len(works), result['body']['illustManga']['lastPage'])
  ```

- 实测：`p=1` / `p=2` / `p=10` 都是 `200`；`p=10000` 仍 `200`（**越界不等于报错**，也不保证是有效页）；`limit=1` 也是 `200`。
  匿名可读。**每个样本的 `data` 都含 1 个广告占位行**（初测的 `p=1`/`p=2`/`p=10000`/`limit=1` 四份原始样本各 1 行）。

### `web_search_illustrations(word, **params)`

- 路由：`GET https://www.pixiv.net/ajax/search/illustrations/{word}`（W / N + 实测）。
- 给什么 → 返回什么：返回完整信封，`body.illust.data` 是插画数组，另有 `body.illust.total` 与 `lastPage`。
- 参数：`word`（路径 + 查询，必填）+ 表 C 的过滤参数；`type` 取 `illust_and_ugoira` / `illust` / `ugoira`（实测 `illust` 与 `ugoira`
  都是 `200`）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/illustrations/cat?word=cat&order=date_d&mode=all&p=1&s_mode=s_tag&type=illust
      result = client.web_search_illustrations('cat', order='date_d', mode='all', p=1, s_mode='s_tag', type='illust')
      works = [item for item in result['body']['illust']['data'] if not item.get('isAdContainer')]
      print(len(works))
  ```

- 实测：`type=illust` 与 `type=ugoira` 都 `200`；`body` 顶层键 `['illust', 'suggestChips', 'popular', 'relatedTags',
  'tagTranslation', 'zoneConfig', 'extraData']`。本次样本 `body.illust.data` 是 60 槽位、含 1 个 `{"isAdContainer": true}`
  占位行；`len(data)` 会把占位行算进去，按作品数统计要先判别。

### `web_search_manga(word, **params)`

- 路由：`GET https://www.pixiv.net/ajax/search/manga/{word}`（W / N + 实测）。
- 给什么 → 返回什么：返回完整信封，`body.manga.data` 是漫画数组，另有 `body.manga.total` 与 `lastPage`。
- 参数：`word`（路径 + 查询，必填）+ 表 C 的过滤参数；`type` 取 `manga`，另有 `work_lang`。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/manga/cat?word=cat&order=date_d&mode=all&p=1&s_mode=s_tag&type=manga
      result = client.web_search_manga('cat', order='date_d', mode='all', p=1, s_mode='s_tag', type='manga')
      works = [item for item in result['body']['manga']['data'] if not item.get('isAdContainer')]
      print(len(works))
  ```

- 实测：`200`；`body` 顶层键 `['manga', 'suggestChips', 'popular', 'relatedTags', 'tagTranslation', 'zoneConfig', 'extraData']`。
  本次样本 `body.manga.data` 是 60 槽位、含 1 个 `{"isAdContainer": true}` 占位行，按作品数统计要先判别。

### `web_search_novels(word, **params)`

- 路由：`GET https://www.pixiv.net/ajax/search/novels/{word}`（W / N / S + 实测）。
- 给什么 → 返回什么：返回完整信封，`body.novel.data` 是小说数组，每项有 `id` / `title` / `genre` / `url` / `tags` / `userId` /
  `userName` / `profileImageUrl` / `textCount` / `wordCount` / `readingTime` / `useWordCount` / `description`；另有 `body.novel.total`
  与 `lastPage`。
- 参数：`word`（路径 + 查询，必填）+ `order` / `mode` / `p` / `s_mode` / `work_lang` / `gs` / `tlt` / `tgt` / `wlt` / `wgt` /
  `original_only` / `genre` / `csw` / `lang`。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/novels/cat?word=cat&order=date_d&mode=all&p=1&s_mode=s_tag
      result = client.web_search_novels('cat', order='date_d', mode='all', p=1, s_mode='s_tag')
      works = [item for item in result['body']['novel']['data'] if not item.get('isAdContainer')]
      print(len(works))
  ```

- 实测：`200`；`body` 顶层键 `['novel', 'suggestChips', 'popular', 'relatedTags', 'tagTranslation', 'zoneConfig', 'extraData']`。
  本次样本是 30 条作品、**没有** `{"isAdContainer": true}` 占位行（与 `artworks` / `illustrations` / `manga` 的 60 槽位 1 占位不同）；
  示例里仍保留判别写法，遍历别人样本时更稳。

### `web_search_top(word, **params)`

- 路由：`GET https://www.pixiv.net/ajax/search/top/{word}`（W `search.ts` + 实测）。
- 给什么 → 返回什么：给关键词，返回完整信封，`body` 有 `novel` / `illust` / `manga` / `popular` / `relatedTags` /
  `tagTranslation` / `zoneConfig` / `extraData` / `collection`。
- 参数：`word`（路径 + 查询，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/top/cat?word=cat&lang=en
      top = client.web_search_top('cat', lang='en')
      print(sorted(top['body']))
  ```

- 实测：`word=cat&lang=en` → `200`，`body` 顶层键 `['novel', 'popular', 'relatedTags', 'tagTranslation', 'zoneConfig',
  'extraData', 'illust', 'manga', 'collection']`（**没有 `suggestChips`**，与别的搜索面不同）；聚合结果本次样本
  `illust` 24 条 / `manga` 24 条 / `novel` 8 条，没有 `isAdContainer` 占位行。

### `web_search_tags(tag, **params)`

- 路由：`GET https://www.pixiv.net/ajax/search/tags/{tag}`（W `search.ts` + 实测）。
- 给什么 → 返回什么：给标签（路径段），返回完整信封，`body` 有 `tag` / `word` / `pixpedia`（`abstract` / `image` / `id` /
  `yomigana` / `parentTag` / `siblingsTags` / `tag`）/ `breadcrumbs`（`successor` / `current`）/ `myFavoriteTags` / `tagTranslation`。
- 参数：`tag`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/tags/cat?lang=en
      tag = client.web_search_tags('cat', lang='en')
      print(tag['body']['tag'], tag['body']['pixpedia']['abstract'])
  ```

- 实测：`200`；`body` 顶层键 `['tag', 'word', 'pixpedia', 'breadcrumbs', 'myFavoriteTags', 'tagTranslation']`。

### `web_search_users(**params)`

- 路由：`GET https://www.pixiv.net/ajax/search/users`（S）。
- 给什么 → 返回什么：返回完整信封，`body` 是用户搜索结果（S 未声明逐字段）。
- 参数：`nick`（查询，昵称）、`s_mode`（查询，匹配方式，实测用过 `s_usr`）、`i`（查询，来源只给名字）、`p`（查询，页码）、
  `lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/users?nick=fuzichoco&s_mode=s_usr&i=1&p=1
      users = client.web_search_users(nick='fuzichoco', s_mode='s_usr', i=1, p=1)
      print(users['error'], users['message'])
  ```

- 实测：`nick=fuzichoco&s_mode=s_usr&i=1&p=1` → `400`（正文通用错误信封）；**没有成功样本**。

### `web_search_suggestion(**params)`

- 路由：`GET https://www.pixiv.net/ajax/search/suggestion`（W `search.ts` + 实测）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `popularTags` / `recommendTags` / `recommendByTags` / `recommendedIllusts` /
  `myFavoriteTags` / `tagTranslation` / `thumbnails`。
- 参数：`mode`（查询，实测用过 `all`）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/search/suggestion?mode=all
      suggestion = client.web_search_suggestion(mode='all')
      print(sorted(suggestion['body']))
  ```

- 实测：`200`；`body` 顶层键 `['popularTags', 'recommendTags', 'recommendByTags', 'recommendedIllusts',
  'myFavoriteTags', 'tagTranslation', 'thumbnails']`（`thumbnails` 样本 192 条）。

---

## 用户 user

### `web_user_show(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}`（W [`user.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/user.ts) + 实测）。
- 给什么 → 返回什么：给用户编号（如 `27517`），返回完整信封，`body` 有 `userId` / `name` / `image` / `imageBig` /
  `premium` / `isFollowed` / `isMypixiv` / `isBlocking` / `background` / `sketchLiveId` / `partial` / `sketchLives` /
  `commission` / `publisher` / `following` / `mypixivCount` / `followedBack` / `comment` / `commentHtml` / `webpage` /
  `social` / `canSendMessage` / `region` / `age` / `birthDay` / `gender` / `job` / `workspace` / `official` / `group`。
- 参数：

  | 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `user_id` | 路径（必填） | 用户编号 | 取哪个用户 | — | `27517` |
  | `full` | 查询 | `1`（实测） | 返回更完整的用户资料 | 未规定 | `full=1` |
  | `lang` | 查询 | 见表 A | 语言 | 未规定 | `lang='en'` |

- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517?full=1
      user = client.web_user_show(27517, full=1)
      print(user['body']['userId'], user['body']['name'], user['body']['following'])
  ```

- 实测：`200`；`body` 键含上述全部字段。

### `web_user_profile_all(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/profile/all`（W `user.ts` + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 有 `illusts` / `manga` / `novels` / `mangaSeries` / `novelSeries` /
  `collections` / `collectionIds` / `pickup` / `bookmarkCount` / `externalSiteWorksStatus` / `request` /
  `shouldShowSensitiveNotice`。实测 `body.illusts` 是 `{插画编号: null}` 的映射（只给编号，内容要另取）。
- 参数：`user_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/profile/all
      profile = client.web_user_profile_all(27517)
      print(len(profile['body']['illusts']), profile['body']['bookmarkCount'])
  ```

- 实测：`200`；`body.pickup` 样本 3 条。

### `web_user_profile_top(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/profile/top`（W `user.ts` + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 有 `illusts` / `manga` / `novels` / `collections` / `requestPostWorks` /
  `requestPlans` / `zoneConfig` / `extraData`。**W 也提示实际键可能与声明不同**，按实测原样返回，不假设固定形状。
- 参数：`user_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/profile/top
      top = client.web_user_profile_top(27517)
      print(sorted(top['body']))
  ```

- 实测：`200`；`body` 顶层键 `['illusts', 'manga', 'novels', 'collections', 'requestPostWorks', 'requestPlans',
  'zoneConfig', 'extraData']`。

### `web_user_profile_illusts(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/profile/illusts`（W `user.ts` + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body.works` 是**以作品编号为键**的作品数据（另有 `zoneConfig` / `extraData`）。
- 参数：`user_id`（路径，必填）、`ids`（查询，列表，只要这些编号）、`work_category`（查询，作品类别，实测用过 `illustManga`）、
  `is_first_page`（查询，是否首页）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/profile/illusts?ids[]=149040133&ids[]=147208254&work_category=illustManga&is_first_page=1
      works = client.web_user_profile_illusts(27517, ids=[149040133, 147208254], work_category='illustManga', is_first_page=1)
      print(list(works['body']['works']))
  ```

- 实测：`200`；`body` 顶层键 `['works', 'zoneConfig', 'extraData']`。

### `web_user_profile_novels(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/profile/novels`（W `user.ts` + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，**`body.works`（不是 `body.novels`）**是以小说编号为键的小说数据，
  另有 `zoneConfig` / `extraData`。
- 参数：`user_id`（路径，必填）、`ids`（查询，列表）、`is_first_page`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/38475999/profile/novels?ids[]=11165421&ids[]=11165886&is_first_page=1
      novels = client.web_user_profile_novels(38475999, ids=[11165421, 11165886], is_first_page=1)
      print(list(novels['body']['works']))
  ```

- 实测：`200`；`body` 顶层键 `['works', 'zoneConfig', 'extraData']`（**没有 `novels` 键**）。

### `web_user_illusts(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/illusts`（W `user.ts` + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 是**以插画编号为顶层键**的插画数据对象。
- 参数：`user_id`（路径，必填）、`ids`（查询，列表）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/illusts?ids[]=149040133&ids[]=147208254
      illusts = client.web_user_illusts(27517, ids=[149040133, 147208254])
      print(list(illusts['body']))
  ```

- 实测：`200`；`body` 顶层键就是 `149040133` / `147208254`（插画编号本身）。

### `web_user_meta(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/meta`（W `user.ts` + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 是**页面 meta**（不是用户资料本体）：`description` / `title` /
  `canonical` / `ogp` / `twitter` / `alternateLanguages` / `descriptionHeader`。
- 参数：`user_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/meta
      meta = client.web_user_meta(27517)
      print(meta['body']['title'], meta['body']['canonical'])
  ```

- 实测：`200`；`body` 顶层键 `['description', 'title', 'canonical', 'ogp', 'twitter', 'alternateLanguages',
  'descriptionHeader']`。

### `web_user_works_latest(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/works/latest`（W `user.ts` + 实测）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 有 `illusts` / `novels`（都是以编号为键的对象）。
- 参数：`user_id`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/works/latest
      latest = client.web_user_works_latest(27517)
      print(sorted(latest['body']))
  ```

- 实测：`200`；`body` 顶层键 `['illusts', 'novels']`。

### `web_user_following(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/following`（W `user.ts`；匿名实测 `400`）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 有 `users` / `total` / `followUserTags`。
- 参数：`user_id`（路径，必填）、`offset`（查询，跳过条数）、`limit`（查询，本页条数）、`rest`（查询，范围，如 `show`）、
  `lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/following?offset=0&limit=2&rest=show
      following = client.web_user_following(27517, offset=0, limit=2, rest='show')
      print(len(following['body']['users']), following['body']['total'])
  ```

- 实测：匿名 `offset=0&limit=2&rest=show` → `400`（正文通用错误信封，**不是 401**）；**没有成功样本**（需要登录态）。

### `web_user_followers(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/followers`（D）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 是粉丝列表（D 未声明逐字段）。
- 参数：`user_id`（路径，必填）、`offset`（查询）、`limit`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/followers?offset=0&limit=2
      followers = client.web_user_followers(27517, offset=0, limit=2)
      print(followers['error'], followers['message'])
  ```

- 实测：`offset=0&limit=2` → `400`（正文通用错误信封）；**没有成功样本**。来源 D 自述已过时。

### `web_user_recommends(user_id, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/recommends`（W `user.ts`）。
- 给什么 → 返回什么：给用户编号，返回完整信封，`body` 有 `recommendUsers` / `thumbnails`。
- 参数：`user_id`（路径，必填）、`userNum`（查询，用户数）、`workNum`（查询，作品数）、`isR18`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/recommends?userNum=10&workNum=3
      recommends = client.web_user_recommends(27517, userNum=10, workNum=3)
      print(len(recommends['body']['recommendUsers']))
  ```

- 实测：`userNum=2&workNum=1&isR18=false` → `400`（正文通用错误信封）；**没有成功样本**。

### `web_user_tagged(user_id, work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/{work_type}/tag`（W `user.ts` / `userNovels.ts` + 实测）。
- 给什么 → 返回什么：给用户编号与 `work_type`（见表 B），返回完整信封，`body` 有 `works`（**数组**）/ `total` /
  `zoneConfig` / `extraData`。
- 参数：`user_id`（路径，必填）、`work_type`（路径，必填，`illusts` / `manga` / `illustmanga` / `novels`）、
  `tag`（查询，标签）、`offset`（查询）、`limit`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/illusts/tag?tag=%E5%88%9D%E9%9F%B3%E3%83%9F%E3%82%AF&offset=0&limit=2
      tagged = client.web_user_tagged(27517, 'illusts', tag='初音ミク', offset=0, limit=2)
      print(len(tagged['body']['works']), tagged['body']['total'])
  ```

- 实测：`illusts` + `tag=初音ミク` → `200`，`body.works` 2 条；`novels` + `tag=創作BL` → `200`，`body.works` 2 条。

### `web_user_tags(user_id, work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/{work_type}/tags`（W [`userTags.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/userTags.ts) + 实测）。
- 给什么 → 返回什么：给用户编号与 `work_type`，返回完整信封，`body` 是标签条目数组，每项 `tag` / `tag_translation` /
  `tag_yomigana` / **`cnt`**（计数键是 `cnt`，不是 `count`）。
- 参数：`user_id`（路径，必填）、`work_type`（路径，必填，见表 B）、`all`（查询，是否取全部，实测用过 `1`）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/illusts/tags?all=1
      tags = client.web_user_tags(27517, 'illusts', all=1)
      print([(item['tag'], item['cnt']) for item in tags['body']][:3])
  ```

- 实测：`illusts` + `all=1` → `200`，`body` 921 条；`novels` + `all=1` → `200`，`body` 31 条。

### `web_user_bookmarks(user_id, work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/{work_type}/bookmarks`（W `user.ts` / `userNovels.ts`；匿名实测 `400`）。
- 给什么 → 返回什么：给用户编号与 `work_type`（`illusts` / `novels`），返回完整信封，`body` 有 `works` / `total`。
- 参数：`user_id`（路径，必填）、`work_type`（路径，必填，`illusts` / `novels`）、`tag`（查询）、`offset`（查询）、
  `limit`（查询）、`rest`（查询，如 `show`）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/illusts/bookmarks?tag=&offset=0&limit=2&rest=show
      bookmarks = client.web_user_bookmarks(27517, 'illusts', tag='', offset=0, limit=2, rest='show')
      print(bookmarks['body']['total'])
  ```

- 实测：`illusts` 与 `novels` 匿名都 → `400`（正文通用错误信封，**不是 401**）；**没有成功样本**（收藏需要登录态）。

### `web_user_bookmark_tags(user_id, work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/user/{user_id}/{work_type}/bookmark/tags`（W `user.ts`）。
- 给什么 → 返回什么：给用户编号与 `work_type`（`illusts` / `novels`），返回完整信封，`body` 有 `public` / `private` /
  `tooManyBookmark` / `tooManyBookmarkTags`。
- 参数：`user_id`（路径，必填）、`work_type`（路径，必填）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/27517/illusts/bookmark/tags
      bookmark_tags = client.web_user_bookmark_tags(27517, 'illusts')
      print(sorted(bookmark_tags['body']))
  ```

- 实测：`illusts` 与 `novels` 匿名都 → `400`（正文通用错误信封）；**没有成功样本**。

### `web_user_extra(**params)`

- 路由：`GET https://www.pixiv.net/ajax/user/extra`（W `user.ts`）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `background` / `followers` / `following` / `mypixivCount`。
- 参数：`is_smartphone`（查询）、`version`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/user/extra
      extra = client.web_user_extra()
      print(sorted(extra['body']))
  ```

- 实测：`is_smartphone=false&version=20261008` → `400`（正文通用错误信封）；**没有成功样本**。

---

## 关注 / 首页 / 发现

### `web_follow_latest(work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/follow_latest/{work_type}`（D / S；匿名实测 `400`）。
- 给什么 → 返回什么：给 `work_type`（`illust` / `novel`），返回完整信封，`body` 有 `page` / `thumbnails`。
- 参数：`work_type`（路径，必填，`illust` / `novel`）、`mode`（查询）、`p`（查询，页码）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/follow_latest/illust?mode=all&p=1
      latest = client.web_follow_latest('illust', mode='all', p=1)
      print(latest['error'], latest['message'])
  ```

- 实测：`illust` 与 `novel` 匿名都 → `400`（正文通用错误信封）；**没有成功样本**（关注流需要登录态）。

### `web_mypixiv_latest(**params)`

- 路由：`GET https://www.pixiv.net/ajax/mypixiv_latest/illust`（D）。
- 给什么 → 返回什么：返回完整信封，`body` 是 mypixiv 动态流（D 未声明逐字段）。
- 参数：`p`（查询，页码）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/mypixiv_latest/illust?p=1
      feed = client.web_mypixiv_latest(p=1)
      print(feed['error'], feed['message'])
  ```

- 实测：`p=1` → `400`（正文通用错误信封）；**没有成功样本**（需要登录态）。

### `web_watch_list(work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/watch_list/{work_type}`（D / S）。
- 给什么 → 返回什么：给 `work_type`（`manga` / `novel`），返回完整信封，`body` 是追更系列列表（D 未声明逐字段）。
- 参数：`work_type`（路径，必填，`manga` / `novel`）、`p`（查询，页码）、`new`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/watch_list/manga?p=1
      watch = client.web_watch_list('manga', p=1)
      print(watch['error'], watch['message'])
  ```

- 实测：`manga?p=1` 与 `novel?p=1&new=1` 都 → `400`（正文通用错误信封）；**没有成功样本**（需要登录态）。

### `web_street(section, **params)`

- 路由：`GET https://www.pixiv.net/ajax/street/{section}`（S）。
- 给什么 → 返回什么：给版块（`section`），返回完整信封，`body` 是该版块首页内容（S 未声明逐字段）。
- 参数：`section`（路径，必填，`recommend_tags` / `latest` / `sub` / `for_you`）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/street/latest
      street = client.web_street('latest')
      print(street['error'], street['message'])
  ```

- 实测：`recommend_tags` / `latest` / `sub` / `for_you` 四个 section 匿名都 → `400`（正文通用错误信封）；**没有成功样本**。
  **没有 `/ajax/trending` 这类路由**，趋势由 `web_search_suggestion` / `web_street(section='recommend_tags')` 覆盖。

### `web_top_illust(**params)`

- 路由：`GET https://www.pixiv.net/ajax/top/illust`（D；匿名实测 `400`）。
- 给什么 → 返回什么：返回完整信封，`body` 是插画首页内容（D 未声明逐字段）。
- 参数：`mode`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/top/illust?mode=all
      top = client.web_top_illust(mode='all')
      print(top['error'], top['message'])
  ```

- 实测：匿名 `mode=all` → `400`；**没有成功样本**。

### `web_discovery_artworks(**params)`

- 路由：`GET https://www.pixiv.net/ajax/discovery/artworks`（N + 实测）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `thumbnails` / `recommendations`。
- 参数：`mode`（查询）、`limit`（查询，条数）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/discovery/artworks?mode=all&limit=2
      discovery = client.web_discovery_artworks(mode='all', limit=2)
      print(discovery['error'], discovery['message'])
  ```

- 实测：匿名 `mode=all&limit=2` → `400`（**不是 401**）；**没有成功样本**。
  （注意别与 `web_illust_discovery` 搞混：那是 `ajax/illust/discovery`，用 `max`，匿名可读。）

### `web_discovery_novels(**params)`

- 路由：`GET https://www.pixiv.net/ajax/discovery/novels`（N）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `thumbnails` / `recommendedNovelIds` / `recommendNovelDetails`。
- 参数：`mode`（查询）、`limit`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/discovery/novels?mode=all&limit=2
      discovery = client.web_discovery_novels(mode='all', limit=2)
      print(discovery['error'], discovery['message'])
  ```

- 实测：`mode=all&limit=2` → `400`（**不是 401**）；**没有成功样本**。

### `web_discovery_users(**params)`

- 路由：`GET https://www.pixiv.net/ajax/discovery/users`（N / W）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `users` / `thumbnails`。
- 参数：`limit`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/discovery/users?limit=2
      discovery = client.web_discovery_users(limit=2)
      print(discovery['error'], discovery['message'])
  ```

- 实测：`limit=2` → `400`（正文通用错误信封）；**没有成功样本**。

---

## 排行榜

### `web_ranking(**params)`

- 路由：`GET https://www.pixiv.net/ranking.php`（N / D / W + 实测）。
- 给什么 → 返回什么：返回**根级 JSON**（不是 `ajax/*` 的信封）：顶层有 `contents`（榜单数组）、`mode` / `content` / `page` /
  `prev` / `next` / `date` / `prev_date` / `next_date` / `rank_total` / `meta` / `date_range_text` / `zoneConfig`；
  `contents` 每项有 `title` / `date` / `tags`（标签名数组）/ `url` / `illust_type` / `illust_page_count` / `user_name` /
  `profile_img` / `illust_content_type`（含 `sexual` 等标记）/ `illust_series` / `illust_id` / `width` / `height` /
  `user_id` / `rank` / `yes_rank` / `rating_count` / `view_count` / `illust_upload_timestamp` / `attr` / `is_masked`。
  **`illust_series` 不是布尔**：实测是 `false` **或**一个对象（含 `illust_series_id` / `user_id` / `title` / `caption` /
  `content_count` / `create_datetime` / `content_illust_id` / `content_order` / `page_url`）；取系列字段前先判真假，
  别把 `false` 当字典用。
- 参数：

  | 名称 | 位置 | 取值 | 含义 | 不传时 | 示例 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `mode` | 查询 | 实测 `daily`；其余未规定 | 榜单周期 | 未规定 | `mode='daily'` |
  | `content` | 查询 | 来源只给名字 | 榜单内容分类 | 未规定 | `content='illust'` |
  | `date` | 查询 | `YYYYMMDD` | 指定日期榜单 | 未规定 | `date='20261006'` |
  | `p` | 查询 | 页码（整数） | 第几页 | 未规定 | `p=1` |
  | `format` | 查询 | `json` | 返回 JSON（本家族**唯一一处客户端补的协议默认值**；不补会拿到 HTML） | 由客户端补 `json` | `format='json'` |

- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ranking.php?mode=daily&p=1&format=json
      ranking = client.web_ranking(mode='daily', p=1)
      for entry in ranking['contents'][:3]:
          print(entry['rank'], entry['illust_id'], entry['title'], entry['view_count'])
  ```

- 实测：`p=1` / `p=2` → `200`；`p=10000` → `404`，正文 `{"error": "ランキング集計の範囲外です"}`（`error` 是字符串）。

### `web_novel_ranking(**params)`

- 路由：`GET https://www.pixiv.net/ajax/ranking/novel`（N / S + 实测）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `display_a`（含 `rank_a` 数组，每项 `rank` / `id` / `title` / `create_date` /
  `user_id` / `user_name` / `profile_img` / `comment`）、`start` / `end` / `date` / `h_title` / `zoneConfig`。
- 参数：`mode`（查询，实测用过 `daily`）、`date`（查询）、`p`（查询，页码）、`content`（查询）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/ranking/novel?mode=daily&p=1
      ranking = client.web_novel_ranking(mode='daily', p=1)
      print(ranking['body']['display_a']['rank_a'][0]['title'])
  ```

- 实测：`200`；`body` 顶层键 `['display_a', 'start', 'end', 'date', 'h_title', 'zoneConfig']`（信封是 `{"error": false, "body": …}`，
  **没有 `message`**）。

---

## 标签 / showcase

### `web_showcase_article(**params)`

- 路由：`GET https://www.pixiv.net/ajax/showcase/article`（P）。
- 给什么 → 返回什么：返回完整信封，`body` 是 showcase 文章详情（P 未声明逐字段）。
- 参数：`article_id`（查询，必填，文章编号）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/showcase/article?article_id=<文章编号>
      article = client.web_showcase_article(article_id=12345)
      print(article['error'], article['message'])
  ```

- 实测：API `ajax/showcase/article?article_id=0` → `404`，正文 `{"error": true, "message": "リクエストされたページが見つかりませんでした",
  "body": []}`（**只测到错误路径**）。**别与网页混淆**：网页 `/showcase` 页面是 `302`、`Location: /showcase/`（不是 pixivision 文章页），
  与这个 API 不是一回事。已读来源里没有有效的 `article_id`，**成功路径 source-only、没有样本**；示例里的 `12345` 只是占位，
  不是有效文章编号（也别与 pixivision 的文章编号混用）。

### `web_tag_info(**params)`

- 路由：`GET https://www.pixiv.net/ajax/tag/info`（W [`tags.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/tags.ts) + 实测）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `tag` / `abstract` / `thumbnail` / `en` / `en_new` / `ja` / `ja_new` /
  `is_view_lead_wire`（`ja` 里是 `tag` / `abstract` / `url`）。
- 参数：`tag`（查询，必填，标签名）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/tag/info?tag=cat
      info = client.web_tag_info(tag='cat')
      print(info['body']['tag'], info['body']['abstract'])
  ```

- 实测：`200`；`body` 顶层键 `['tag', 'abstract', 'thumbnail', 'en', 'en_new', 'ja', 'ja_new', 'is_view_lead_wire']`。

### `web_frequent_tags(work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/tags/frequent/{work_type}`（W `tags.ts` + 实测）。
- 给什么 → 返回什么：给 `work_type`（`illust` / `novel`），返回完整信封，`body` 是标签条目数组，每项 `tag` / `tag_translation`。
- 参数：`work_type`（路径，必填，`illust` / `novel`）、`ids`（查询，列表）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/tags/frequent/illust?ids[]=149040133&ids[]=147208254
      tags = client.web_frequent_tags('illust', ids=[149040133, 147208254])
      print([item['tag'] for item in tags['body']])
  ```

- 实测：`illust` + 两个 id → `200`，`body` 5 条。

### `web_suggest_tags(**params)`

- 路由：`GET https://www.pixiv.net/ajax/tags/suggest_by_word`（W `tags.ts`）。
- 给什么 → 返回什么：返回完整信封，`body` 有 `illust_count` / `tag_name` / `total_count`。
- 参数：`word`（查询，必填，关键词）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/tags/suggest_by_word?word=cat
      suggestion = client.web_suggest_tags(word='cat')
      print(suggestion['error'], suggestion['message'])
  ```

- 实测：`word=cat` → `400`（正文通用错误信封）；**没有成功样本**。

### `web_search_autocomplete(**params)`

- 路由：`GET https://www.pixiv.net/rpc/cps.php`（W [`cps.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/cps.ts) + 实测）。
- 给什么 → 返回什么：返回**根级 JSON**，顶层只有 `candidates`，其每项有 `access_count` / `tag_name` / `tag_translation` / `type`。
- 参数：`keyword`（查询，必填，前缀关键词）、`lang`（查询，见表 A）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/rpc/cps.php?keyword=cat
      candidates = client.web_search_autocomplete(keyword='cat')
      print([(item['tag_name'], item['access_count']) for item in candidates['candidates'][:3]])
  ```

- 实测：`keyword=cat` → `200`，根键只有 `['candidates']`。

---

## 写入方法（全部 `POST`，本仓库**绝不执行**）

> 下面每个方法都需要登录态 Cookie；网页端写请求还要站点 CSRF token（`X-CSRF-Token`）。本库不抓取、不自动获取 token，
> `csrf_token` 由调用方从配置/参数显式传入。**所有写入方法均未执行、未实测**；返回结构只写来源声明的键，来源没写的写“源码未声明”，
> **不编造 `success`**。示例一律标注“未执行、未实测”。
>
> `work_type` 是**字面路径段**（见表 B），客户端不做同义词映射。

### `web_bookmark_add(work_type, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/bookmarks/add`，正文 **JSON**（W [`illustsBookmarks.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/illustsBookmarks.ts) / [`novelsBookmarks.ts`](https://github.com/YieldRay/pixiv-web-api/blob/main/packages/pixiv-web-api/src/api/novelsBookmarks.ts)）。
- 给什么 → 返回什么：`work_type` 为 `illusts` 时给 `illust_id`（返回 `body` 有 `last_bookmark_id` / `stacc_status_id`）；
  为 `novels` 时给 `novel_id`（源码声明返回的是新收藏 id 的字符串）。
- 属性（`**attributes` 原样作为 JSON 正文，来源没要求的字段不代填）：`illust_id` **或** `novel_id`（整数）、
  `restrict`（`0` 公开 / `1` 非公开）、`comment`（字符串）、`tags`（字符串数组）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测：需要登录态 Cookie 与站点 CSRF token
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<页面里的 32 位 token>') as client:
      result = client.web_bookmark_add('illusts', illust_id=149040133, restrict=0, tags=['测试'])
      print(result['body']['last_bookmark_id'])
  ```

### `web_bookmark_delete(work_type, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/bookmarks/delete`，正文 **表单**（`form=`，W 同文件）。
- 给什么 → 返回什么：`work_type='illusts'` 给 `bookmark_id`（即 `web_bookmark_add` 返回的 `last_bookmark_id`）；
  `work_type='novels'` 给 `book_id` 与 `del='1'`。返回键**源码未声明**。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_bookmark_delete('illusts', bookmark_id=123456789)
      print(result)
  ```

### `web_bookmark_add_tags(work_type, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/bookmarks/add_tags`，正文 **JSON**（W 同文件）。
- 给什么 → 返回什么：给要打标签的收藏记录编号与标签数组。返回键**源码未声明**。
- 属性：`bookmark_ids`（整数数组）、`tags`（字符串数组）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_bookmark_add_tags('illusts', bookmark_ids=[123456789], tags=['测试'])
      print(result)
  ```

### `web_bookmark_edit_restrict(work_type, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/bookmarks/edit_restrict`，正文 **JSON**（W 同文件）。
- 给什么 → 返回什么：改收藏的公开/非公开。返回键**源码未声明**。
- 属性：`bookmarkIds`（字符串数组）、`bookmarkRestrict`（`'private'` / `'public'`）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_bookmark_edit_restrict('illusts', bookmarkIds=['123456789'], bookmarkRestrict='private')
      print(result)
  ```

### `web_bookmark_remove(work_type, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/bookmarks/remove`，正文 **JSON**（W 同文件）。
- 给什么 → 返回什么：批量移除收藏。返回键**源码未声明**。
- 属性：`bookmarkIds`（字符串数组）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_bookmark_remove('illusts', bookmarkIds=['123456789'])
      print(result)
  ```

### `web_bookmark_rename_progress(work_type, **params)`

- 路由：`GET https://www.pixiv.net/ajax/{work_type}/bookmarks/rename_tag_progress`（W 同文件）——**这是读取，不是 POST**。
- 给什么 → 返回什么：返回完整信封，`body` 有 `isInProgress`（布尔，是否正在重命名标签）。
- 参数：`work_type`（路径，必填，`illusts` / `novels`）。
- 示例：

  ```python
  from anybooru import Pixiv

  with Pixiv('pixiv', cookie='', access_token='', csrf_token='') as client:
      # GET https://www.pixiv.net/ajax/illusts/bookmarks/rename_tag_progress
      progress = client.web_bookmark_rename_progress('illusts')
      print(progress['body']['isInProgress'])
  ```

- 实测：`illusts` 与 `novels` 匿名都 → `400`（正文通用错误信封）；**没有成功样本**（需要登录态）。

### `web_like(work_type, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/like`，正文 **JSON**（W `illusts.ts` / `novels.ts`）。
- 给什么 → 返回什么：点赞/取消点赞。返回 `body` 有 `is_liked`。**源码没有声明“撤销”入口**，本库也不声称有 undo。
- 属性：`illust_id` **或** `novel_id`（整数）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_like('illusts', illust_id=149040133)
      print(result['body']['is_liked'])
  ```

### `web_comment_post(work_type, **attributes)`

- 路由：`work_type='illust'` → `POST https://www.pixiv.net/rpc/post_comment.php`；`work_type='novel'` →
  `POST https://www.pixiv.net/novel/rpc/post_comment.php`，正文 **表单**（W `illustsComments.ts` / `novelsComments.ts`）。
- 给什么 → 返回什么：发评论或贴表情。返回**根级 JSON**，有 `comment_id` / `comment` / `user_id` / `user_name` / `stamp_id` / `parent_id`。
- 属性：`type`（`'comment'` 或 `'stamp'`）、`illust_id` **或** `novel_id`、`author_user_id`、`comment`（`type='comment'` 时）、
  `stamp_id`（`type='stamp'` 时，源码只声明在 illust 侧）、`parent_id`（可选，回复某条评论）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_comment_post('illust', type='comment', illust_id=149040133,
                                       author_user_id=27517, comment='测试')
      print(result['comment_id'])
  ```

- 说明：源码里**没有** `ajax/illusts/comments/post` 这类实现；不要在方法参考里给它造一个并列原生方法，确需时可自己用通用 `request()`。

### `web_comment_delete(work_type, **attributes)`

- 路由：`work_type='illust'` → `POST https://www.pixiv.net/rpc_delete_comment.php`；`work_type='novel'` →
  `POST https://www.pixiv.net/novel/rpc_delete_comment.php`，正文 **表单**（W 同文件）。
- 给什么 → 返回什么：删除一条评论。返回键**源码未声明**。
- 属性：`i_id`（作品编号）、`del_id`（要删的评论编号）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_comment_delete('illust', i_id=149040133, del_id=123456)
      print(result)
  ```

### `web_user_follow_add(user_id, **attributes)`

- 路由：`POST https://www.pixiv.net/bookmark_add.php`，正文 **表单**（N / S）。方法固定发 `mode='add'` / `type='user'` /
  `format='json'` / `user_id=<user_id>`（**协议常量，不是来源查询默认值**），其余 `**attributes` 照发。
- 给什么 → 返回什么：关注用户。返回键**来源未声明**。
- 属性：`restrict`（`0` 公开 / `1` 非公开）、`tag`（字符串）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_user_follow_add(27517, restrict=0)
      print(result)
  ```

### `web_user_follow_delete(user_id, **attributes)`

- 路由：`POST https://www.pixiv.net/rpc_group_setting.php`，正文 **表单**（N / S）。方法固定发 `mode='del'` /
  `type='bookuser'` / `id=<user_id>`，其余 `**attributes` 照发。
- 给什么 → 返回什么：取关用户。返回键**来源未声明**。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_user_follow_delete(27517)
      print(result)
  ```

### `web_user_block(user_id, action, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/block/save`，正文 **JSON**（S）。
- 给什么 → 返回什么：拉黑/取消拉黑。返回键**来源未声明**。
- 属性：`user_id`（整数，方法也把它当参数）、`action`（`'block'` / `'unblock'`）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_user_block(27517, 'block')
      print(result)
  ```

### `web_series_watch(work_type, series_id, **attributes)` / `web_series_unwatch(...)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/series/{series_id}/watch`（W `illustSeries.ts` / `novelSeries.ts`）。
  `work_type` 为 `illust` / `novel`（**单数**）。
- 给什么 → 返回什么：追更系列。正文 **JSON**（可传 `{}`）。返回键**源码未声明**。
- 参数：`work_type`（路径，必填，`illust` / `novel`）、`series_id`（路径，必填）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      print(client.web_series_watch('illust', 336340))
      print(client.web_series_unwatch('illust', 336340))
  ```

### `web_series_notify_on(work_type, series_id, **attributes)` / `web_series_notify_off(...)`

- 路由：`POST https://www.pixiv.net/ajax/{work_type}/series/{series_id}/watchlist/notification/turn_on`（与 `turn_off`），
  正文 **JSON**（W 同文件）。
- 给什么 → 返回什么：开/关该系列的更新通知。返回键**源码未声明**。
- 参数：`work_type`（路径，必填，`illust` / `novel`）、`series_id`（路径，必填）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      print(client.web_series_notify_on('illust', 336340))
      print(client.web_series_notify_off('illust', 336340))
  ```

### `web_illust_tag_add(illust_id, tag, **attributes)`

- 路由：`POST https://www.pixiv.net/ajax/tags/illust/{illust_id}/add`，正文 **JSON**（W `tags.ts`）。
- 给什么 → 返回什么：给插画加标签。返回键**源码未声明**。
- 属性：`tag`（字符串，方法也把它当参数）。
- 示例（**未执行、未实测**）：

  ```python
  from anybooru import Pixiv

  # 未执行、未实测
  with Pixiv('pixiv', cookie='<登录后的 Cookie>', csrf_token='<32 位 token>') as client:
      result = client.web_illust_tag_add(149040133, '测试')
      print(result)
  ```

---

## 本段排除的 web 面范围

以下是**外围平台服务**，不是作品浏览/交互契约，本库不封装；**不说它们“不存在”或“必须匿名”**：

- OAuth / 登录 / 注册 / 资料编辑 / 账号控制。
- 通知 / webpush / dashboard / tumeng / Sketch。
- 约稿与 request 的创建与完成、创作者市场、用户活动门户、stories。
- 作品的上传 / 编辑 / 删除（没有选定到可核实的源码契约）。
- HTML 抓取、CSS/JS/静态资源/CDN 下载。
- 旧版不受支持的别名（通用 `request()` 仍可自行拼）。
- **没有** `/ajax/trending` 这类路由；趋势由 `web_search_suggestion` / `web_street(section='recommend_tags')` 覆盖。

逐条依据与排除理由见 `docs/pixiv-contract-notes.md` 的 web 面小节。


## App API（`app-api.pixiv.net`，59 个方法）

pixiv 的 App API 是官方移动客户端用的那套接口，和站点前端的 Web API 是**两台主机、两套返回外壳**：App API 在 `https://app-api.pixiv.net`，路由都挂在 `v1/`、`v2/`、`webview/` 下，成功时直接返回一段 JSON（没有 Web 面那种 `{"error", "message", "body"}` 信封），唯一例外是 `app_webview_novel()`，它返回 HTML 文本。本页列出 `Pixiv` 全部 **59 个 `app_` 前缀方法**，每个都是对 [`Pixiv.request()`](pixiv.md) 的一次薄调用，`api='app'` 选中这台主机。Web 面方法见本页前面的 Web 章节。

App 面**绝大多数方法需要调用者自己的 `access_token`**：它作为 `Authorization: Bearer <token>` 发出，本库不登录、不换 token、不刷新 token，也不索要凭据。本轮仅 `app_application_info()`、`app_emoji()` 这两个拿到匿名成功，不外推成其余所有端点都不可匿名。每个方法标注它是否要 token；需要 token 的示例用占位串 `'<你的 access token>'` 表示，集中说明见[边界与未实测（App 面）](#边界与未实测app-面)。

### 依据与阅读方式

本页每条结论标注来源，五个标记：

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **P** | pixivpy 客户端源码 `pixivpy3/aapi.py`（`AppPixivAPI` 同名函数）与 `pixivpy3/models.py`（返回模型），取自 <https://raw.githubusercontent.com/upbit/pixivpy/master/pixivpy3/aapi.py> 与 <https://raw.githubusercontent.com/upbit/pixivpy/master/pixivpy3/models.py> | 路由、必需参数、已知可选参数、返回模型的字段形状。它是**第三方客户端**，不是 pixiv 官方服务端规范；成功响应字段只来自它的模型，本页不把它当官方契约 |
| **Z** | ZipFile 抓包《Unofficial API specification extracted from Pixiv Android App v5.0.17》，<https://gist.github.com/ZipFile/3ba99b47162c23f8aea5d5942bb557b1> | pixivpy 没封装的 App 路由（如 `v1/application-info/android`、`v1/emoji`、`v1/spotlight/articles`，以及本页标注 Z 的其它路由）的路径与参数。它是 **2016 年抓包**，不是官方 OpenAPI |
| **H** | hanshsieh 第三方 OpenAPI，<https://raw.githubusercontent.com/hanshsieh/pixiv-api-doc/master/api.yaml> | pixivpy 与 ZipFile 都没给的那几条路由（`v1/illust/comment/replies`、`v2/user/browsing-history/illust/add`）的路径与参数。它是**第三方 OpenAPI**，不是 pixiv 官方规范 |
| **G** | gallery-dl 客户端源码 `gallery_dl/extractor/pixiv.py`（`PixivAPI.illust_series`、`PixivAPI.illust_comments`），<https://raw.githubusercontent.com/mikf/gallery-dl/master/gallery_dl/extractor/pixiv.py> | `v1/illust/series`、`v3/illust/comments` 的路径、参数与消费字段。它是**第三方下载器**，不是 pixiv 官方规范 |
| **L** | 本轮对 `app-api.pixiv.net` 发起的匿名只读 `GET`（不重试、不跟随跳转、不带任何凭据） | （本列用原生方法名指代其对应路由；L 是对该路由直接发 HTTP，不是运行这些 Python 方法。）对应路由当次的状态码、`Content-Type`、错误体、信封键、字段是否出现。**只有 `app_application_info()` 与 `app_emoji()` 拿到匿名 200 成功**；`app_illust_detail()`、`app_novel_detail()`、`app_spotlight_articles()`、`app_novel_ranking()`、`app_illust_comment_replies()`、`app_user_state()`、`app_illust_series()`、`app_illust_comments_v3()` 的匿名 400 是**拒绝证据**，证明“无 token 会被拒”，不是成功；`v1/novel/markers` 与 `v2/illust/comments` 的匿名 404 是**排除证据**，见边界一节 |

规矩：

* **参数表**的名称、枚举以 **P/Z/H** 为准；**状态码、错误体、字段是否出现**以 **L** 为准；两者都没有的写“未规定”。本页不引用输入研究文档，也不编造 pixiv 官方源码行号。
* **本库不注入源码默认值**：`filter`、`search_target`、`sort`、`include_ranking_label` 等在 pixivpy 里带默认值，那只是**该客户端自己的行为**。本库省略哪个参数就不发哪个参数，服务端行为即“该参数未出现”。表中“源码自带值”一列只作示例，**不宣称是本库默认**。
* **数字（`latest_version`、`id`、计数）都是当次快照**，站点随时会变，只作例子。
* 未实测、需凭据、写操作、排除项集中写在[边界与未实测（App 面）](#边界与未实测app-面)。

### 客户端与通用约定（App 面）

* **类**：`Pixiv`，App 方法全部以 `app_` 前缀，和 `web_` 方法共存于同一个实例：

```python
from anybooru import Pixiv

client = Pixiv('pixiv')                                   # 匿名；读包内 sites.pixiv
client = Pixiv('pixiv', access_token='<你的 access token>')  # app 面大多数方法要 token
```

* **站点根**：App 根是 `https://app-api.pixiv.net`（包内配置键 `sites.pixiv.app_url`，构造参数 `app_url`）。它和 Web 根 `https://www.pixiv.net`（`site_url`）是两个值，`app_` 方法拼在 App 根后。路由里**不带前导斜杠**（如 `v1/user/detail`），真实 URL = `https://app-api.pixiv.net` + `/` + 路由。
* **认证**：`access_token` 非空时，每个 `app_` 请求带 `Authorization: Bearer <access_token>`；显式传 `access_token=''` 保持匿名（即使配置里有值也不用）。**不发** `x-client-time` / `x-client-hash`（pixivpy 的普通 API 函数未注入这两个头；凭据成功路径与头的实际需求未实测），**不伪造** `app-os` / `app-os-version` / `PixivAndroidApp` 之类 User-Agent（用的是本包统一配置的 User-Agent）。单次调用可用 `headers={'Authorization': 'Bearer <另一个 token>'}` 覆盖。
* **GET 标识参数进查询串**：App 主机的 GET 路由把作品号、用户号放在查询里，不放路径。GET 方法签名里的必填 id（`user_id`、`illust_id`、`novel_id`、`series_id`、`word`、`seed_user_id`）会以路由自己的键名并进查询串；`app_webview_novel()` 的 `novel_id` 键名是 `id`。
* **POST 标识参数进表单正文**：6 个 POST 方法（写操作）的必填值（`illust_id`、`user_id`、`show_ai`、`illust_ids`）与 `**attributes` 一起进 `form` 表单正文，**不进查询串**。
* **其余参数原样转发**：`**params` 不改名、不校验、不补默认、不排序。共享编码器把 `None` 值丢弃、布尔写成小写 `true` / `false`、列表写成重复的 `key[]=`。因此**列表值写字面 Python 列表**：`seed_illust_ids=['149040133']` 编码成 `seed_illust_ids[]=149040133`；**逗号串**（如 `already_recommended`）写字面字符串 `'12345,67890'`，不要写列表。
* **分页**：App 列表返回**绝对** `next_url`（形如 `https://app-api.pixiv.net/v1/user/illusts?filter=for_ios&user_id=7140895&type=illust&offset=30`）。翻页把它原样交回：`client.request('GET', next_url, api='app')`。本库不解析、不递增、不自动跟随 `next_url`。
* **返回**：成功 JSON 完整解析后原样返回，不拆信封、不改字段名、不转类型。**App 面没有 `{"error", "message", "body"}` 信封**，列表就是 `{"illusts": [...], "next_url": "..."}` 这个字典本身。
* **错误**：非 2xx 抛 `AnybooruHTTPError`（带 `http_code` / `url` / `body` / `data`）。App 面错误体是 `{"error": {"user_message": ..., "message": ..., "reason": ..., "user_message_details": {...}}}` 这种裸对象，原样保留。
* **`app_webview_novel()` 是唯一返回 HTML 的方法**：`response_format='text'` 把正文当纯文本返回，本库**不解析、不抽小说**；要小说正文/元数据，自己从那段 HTML 里取。
* **`last_call`**：最近一次请求的 `API`（路径原文）、`url`、`status_code`、`status`、`headers`。调试真实 URL 先看 `client.last_call['url']`。

### 59 个方法索引

「路由」列省略共同主机 `https://app-api.pixiv.net/`；「必填」是签名里必须给的值；「已知可选参数」只列 P/Z/H/G 依据里出现的名字，**不表示服务端仅接受这些名字**（其余名字经 `**params` 原样发出）。

| 方法 | HTTP | 路由 | 必填 | 已知可选参数 | 返回外层 | 来源 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`app_user_detail()`](#app_user_detail) | GET | `v1/user/detail` | `user_id` | `filter` | `{user, profile, profile_publicity, workspace}` | P |
| [`app_user_illusts()`](#app_user_illusts) | GET | `v1/user/illusts` | `user_id` | `type`, `filter`, `offset` | `{user, illusts, next_url}` | P |
| [`app_user_bookmarks_illust()`](#app_user_bookmarks_illust) | GET | `v1/user/bookmarks/illust` | `user_id` | `restrict`, `filter`, `max_bookmark_id`, `tag` | `{illusts, next_url}` | P |
| [`app_user_bookmarks_novel()`](#app_user_bookmarks_novel) | GET | `v1/user/bookmarks/novel` | `user_id` | `restrict`, `filter`, `max_bookmark_id`, `tag` | `{novels, next_url}` | P |
| [`app_user_related()`](#app_user_related) | GET | `v1/user/related` | `seed_user_id` | `filter`, `offset` | `{user_previews, next_url}` | P |
| [`app_user_recommended()`](#app_user_recommended) | GET | `v1/user/recommended` | — | `filter`, `offset` | `{user_previews, next_url}` | P |
| [`app_user_following()`](#app_user_following) | GET | `v1/user/following` | `user_id` | `restrict`, `offset` | `{user_previews, next_url}` | P |
| [`app_user_follower()`](#app_user_follower) | GET | `v1/user/follower` | `user_id` | `filter`, `offset` | `{user_previews, next_url}` | P |
| [`app_user_mypixiv()`](#app_user_mypixiv) | GET | `v1/user/mypixiv` | `user_id` | `offset` | `{user_previews, next_url}` | P |
| [`app_user_list()`](#app_user_list) | GET | `v2/user/list` | `user_id` | `filter`, `offset` | `{user_previews, next_url}` | P |
| [`app_user_bookmark_tags_illust()`](#app_user_bookmark_tags_illust) | GET | `v1/user/bookmark-tags/illust` | `user_id` | `restrict`, `offset` | `{bookmark_tags, next_url}` | P |
| [`app_illust_detail()`](#app_illust_detail) | GET | `v1/illust/detail` | `illust_id` | — | `{illust}` | P + L(匿名 400 拒绝) |
| [`app_illust_follow()`](#app_illust_follow) | GET | `v2/illust/follow` | — | `restrict`, `offset` | `{illusts, next_url}` | P |
| [`app_illust_comments()`](#app_illust_comments) | GET | `v1/illust/comments` | `illust_id` | `offset`, `include_total_comments` | `{comments, next_url, total_comments?}` | P |
| [`app_illust_series()`](#app_illust_series) | GET | `v1/illust/series` | `illust_series_id` | `offset` | `{illusts, next_url, illust_series_detail}` | G + L(匿名 400 拒绝) |
| [`app_illust_comments_v3()`](#app_illust_comments_v3) | GET | `v3/illust/comments` | `illust_id` | — | `{comments, next_url}` | G + L(匿名 400 拒绝) |
| [`app_illust_related()`](#app_illust_related) | GET | `v2/illust/related` | `illust_id` | `filter`, `seed_illust_ids[]`, `offset`, `viewed[]` | `{illusts, next_url}` | P |
| [`app_illust_recommended()`](#app_illust_recommended) | GET | `v1/illust/recommended` | — | `content_type`, `include_ranking_label`, `filter`, `max_bookmark_id_for_recommend`, `min_bookmark_id_for_recent_illust`, `offset`, `include_ranking_illusts`, `include_privacy_policy`, `viewed[]` | `{illusts, ranking_illusts, next_url, contest_exists?, privacy_policy?}` | P |
| [`app_illust_ranking()`](#app_illust_ranking) | GET | `v1/illust/ranking` | — | `mode`, `filter`, `date`, `offset` | `{illusts, next_url}` | P |
| [`app_illust_new()`](#app_illust_new) | GET | `v1/illust/new` | — | `content_type`, `filter`, `max_illust_id` | `{illusts, next_url}` | P |
| [`app_ugoira_metadata()`](#app_ugoira_metadata) | GET | `v1/ugoira/metadata` | `illust_id` | — | `{ugoira_metadata: {zip_urls, frames}}` | P |
| [`app_trending_tags_illust()`](#app_trending_tags_illust) | GET | `v1/trending-tags/illust` | — | `filter` | `{trend_tags}` | P |
| [`app_search_illust()`](#app_search_illust) | GET | `v1/search/illust` | `word` | `search_target`, `sort`, `duration`, `start_date`, `end_date`, `filter`, `search_ai_type`, `offset` | `{illusts, next_url, search_span_limit, show_ai}` | P |
| [`app_search_novel()`](#app_search_novel) | GET | `v1/search/novel` | `word` | `search_target`, `sort`, `merge_plain_keyword_results`, `include_translated_tag_results`, `start_date`, `end_date`, `filter`, `search_ai_type`, `offset` | `{novels, next_url, search_span_limit, show_ai}` | P |
| [`app_search_user()`](#app_search_user) | GET | `v1/search/user` | `word` | `sort`, `duration`, `filter`, `offset` | `{user_previews, next_url}` | P |
| [`app_novel_detail()`](#app_novel_detail) | GET | `v2/novel/detail` | `novel_id` | — | `{novel}` | P + L(匿名 400 拒绝) |
| [`app_novel_series()`](#app_novel_series) | GET | `v2/novel/series` | `series_id` | `filter`, `last_order` | `{novel_series_detail, novels, next_url}` | P |
| [`app_novel_comments()`](#app_novel_comments) | GET | `v1/novel/comments` | `novel_id` | `offset`, `include_total_comments` | `{comments, next_url, total_comments?, comment_access_control}` | P |
| [`app_novel_recommended()`](#app_novel_recommended) | GET | `v1/novel/recommended` | — | `include_ranking_label`, `filter`, `offset`, `include_ranking_novels`, `already_recommended`, `max_bookmark_id_for_recommend`, `include_privacy_policy` | `{novels, ranking_novels, next_url, privacy_policy?}` | P |
| [`app_novel_new()`](#app_novel_new) | GET | `v1/novel/new` | — | `filter`, `max_novel_id` | `{novels, next_url}` | P |
| [`app_novel_follow()`](#app_novel_follow) | GET | `v1/novel/follow` | — | `restrict`, `offset` | `{novels, next_url}` | P |
| [`app_user_novels()`](#app_user_novels) | GET | `v1/user/novels` | `user_id` | `filter`, `offset` | `{user, novels, next_url}` | P |
| [`app_webview_novel()`](#app_webview_novel) | GET | `webview/v2/novel` | `novel_id`（键名 `id`） | `viewer_version` | **HTML 文本** | P |
| [`app_illust_bookmark_detail()`](#app_illust_bookmark_detail) | GET | `v2/illust/bookmark/detail` | `illust_id` | — | `{bookmark_detail: {is_bookmarked, tags}}` | P |
| [`app_illust_bookmark_add()`](#app_illust_bookmark_add) | POST | `v2/illust/bookmark/add` | `illust_id` | `restrict`, `tags[]` | 站点 JSON（源码未声明成功键） | P |
| [`app_illust_bookmark_delete()`](#app_illust_bookmark_delete) | POST | `v1/illust/bookmark/delete` | `illust_id` | — | 站点 JSON（源码未声明成功键） | P |
| [`app_user_follow_add()`](#app_user_follow_add) | POST | `v1/user/follow/add` | `user_id` | `restrict` | 站点 JSON（源码未声明成功键） | P |
| [`app_user_follow_delete()`](#app_user_follow_delete) | POST | `v1/user/follow/delete` | `user_id` | — | 站点 JSON（源码未声明成功键） | P |
| [`app_user_edit_ai_show_settings()`](#app_user_edit_ai_show_settings) | POST | `v1/user/ai-show-settings/edit` | `show_ai` | — | 站点 JSON（源码未声明成功键） | P |
| [`app_application_info()`](#app_application_info) | GET | `v1/application-info/android` | — | — | `{application_info}` | Z + L(匿名 200 成功) |
| [`app_emoji()`](#app_emoji) | GET | `v1/emoji` | — | — | `{emoji_definitions}` | Z + L(匿名 200 成功) |
| [`app_spotlight_articles()`](#app_spotlight_articles) | GET | `v1/spotlight/articles` | — | `category`, `offset` | `{spotlight_articles, next_url}` | Z + L(匿名 400 拒绝) |
| [`app_user_bookmark_tags_novel()`](#app_user_bookmark_tags_novel) | GET | `v1/user/bookmark-tags/novel` | `user_id` | `restrict`, `offset` | `{bookmark_tags, next_url}` | Z |
| [`app_user_follow_detail()`](#app_user_follow_detail) | GET | `v1/user/follow/detail` | `user_id` | — | `{follow_detail: {is_followed, restrict}}` | Z |
| [`app_user_browsing_history_illusts()`](#app_user_browsing_history_illusts) | GET | `v1/user/browsing-history/illusts` | — | `offset` | `{illusts, next_url}` | Z |
| [`app_user_browsing_history_novels()`](#app_user_browsing_history_novels) | GET | `v1/user/browsing-history/novels` | — | `offset` | `{novels, next_url}` | Z |
| [`app_user_state()`](#app_user_state) | GET | `v1/user/me/state` | — | — | `{user_state: {is_mail_authorized}}` | Z |
| [`app_illust_comment_replies()`](#app_illust_comment_replies) | GET | `v1/illust/comment/replies` | `comment_id` | — | `{comments, next_url}` | H |
| [`app_illust_mypixiv()`](#app_illust_mypixiv) | GET | `v2/illust/mypixiv` | — | `offset` | `{illusts, next_url}` | Z |
| [`app_illust_popular()`](#app_illust_popular) | GET | `v1/illust/popular` | — | `**params` | Z 未声明成功结构 | Z |
| [`app_manga_recommended()`](#app_manga_recommended) | GET | `v1/manga/recommended` | — | `filter`, `include_ranking_illusts`, `max_bookmark_id`, `offset` | `{illusts, ranking_illusts, next_url}` | Z |
| [`app_trending_tags_manga()`](#app_trending_tags_manga) | GET | `v1/trending-tags/manga` | — | `filter` | Z 未声明成功结构 | Z |
| [`app_search_autocomplete()`](#app_search_autocomplete) | GET | `v1/search/autocomplete` | `word` | — | `{search_auto_complete_keywords}` | Z |
| [`app_novel_ranking()`](#app_novel_ranking) | GET | `v1/novel/ranking` | — | `mode`, `date`, `offset` | `{novels, next_url}` | Z |
| [`app_novel_mypixiv()`](#app_novel_mypixiv) | GET | `v1/novel/mypixiv` | — | `offset` | `{novels, next_url}` | Z |
| [`app_novel_popular()`](#app_novel_popular) | GET | `v1/novel/popular` | — | `**params` | Z 未声明成功结构 | Z |
| [`app_trending_tags_novel()`](#app_trending_tags_novel) | GET | `v1/trending-tags/novel` | — | `filter` | Z 未声明成功结构 | Z |
| [`app_novel_bookmark_detail()`](#app_novel_bookmark_detail) | GET | `v2/novel/bookmark/detail` | `novel_id` | — | `{bookmark_detail: {is_bookmarked, restrict, tags}}` | Z |
| [`app_illust_browsing_history_add()`](#app_illust_browsing_history_add) | POST | `v2/user/browsing-history/illust/add` | `illust_ids[]` | `**attributes` | H 声明 JSON `{}`（未执行） | H |

### 枚举与共用参数速查

下表是本页反复出现的取值，方法表里直接引用；`不传时` 一律指**服务端在该参数未出现时**的行为（本库不补）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `filter` | `for_ios`（P 源码自用值；其它取值 P/Z 未给） | 按客户端平台过滤作品元数据 | 未规定（不加该参数） | `filter='for_ios'` |
| `restrict` | P 源码自用 `public`；P 依据另给 `private`（`app_user_bookmarks_*`）与 `all`（`app_novel_follow`） | 收藏或关注列表的可见范围 | 未规定（P 源码常自带 `public`，本库不注入） | `restrict='public'` |
| `offset` | 整数，从 `0` 起 | 列表偏移量（页码游标之一） | 未规定 | `offset=30` |
| `max_bookmark_id` / `max_illust_id` / `max_novel_id` / `last_order` | 整数或数字串 | 各端点自己的游标；`next_url` 里给出 | 未规定 | `max_illust_id='150000000'` |
| `start_date` / `end_date` / `date` | `YYYY-MM-DD` | 日期过滤 / 排行榜日期 | 未规定 | `start_date='2026-01-01'` |
| `search_target` | `partial_match_for_tags` / `exact_match_for_tags` / `title_and_caption` / `keyword`（`app_search_novel` 另有 `text`） | 关键词匹配方式 | 未规定（P 源码自用 `partial_match_for_tags`） | `search_target='partial_match_for_tags'` |
| `sort` | `date_desc` / `date_asc` / `popular_desc`（`popular_desc` 需会员） | 结果排序 | 未规定（P 源码自用 `date_desc`） | `sort='date_desc'` |
| `duration` | `within_last_day` / `within_last_week` / `within_last_month` | 时间范围过滤 | 未规定 | `duration='within_last_week'` |
| `search_ai_type` | `0` / `1` | AI 作品过滤开关 | 未规定 | `search_ai_type=1` |
| `include_total_comments` / `include_ranking_label` / `include_ranking_illusts` / `include_ranking_novels` / `include_privacy_policy` / `merge_plain_keyword_results` / `include_translated_tag_results` | 布尔 | 是否要求响应带对应块 | 未规定（P 源码对部分自带 `true`） | `include_total_comments=True` |
| `viewed` / `seed_illust_ids` | 列表 | 已看/种子作品号；编码成重复的 `viewed[]=` / `seed_illust_ids[]=` | 未规定 | `viewed=['149040133']` |
| `already_recommended` | 逗号串 | 已推荐过的作品号，避免重复 | 未规定 | `already_recommended='12345,67890'` |

`app_illust_ranking()` 的 `mode` 取值（P 源码所列）：`day`、`day_male`、`day_female`、`week_original`、`week_rookie`、`week`、`month`、`day_r18`、`day_male_r18`、`day_female_r18`、`week_r18`、`week_r18g`，以及 manga 变体；本库不注入任何默认。

`app_novel_ranking()` 的 `mode` 取值（Z 所列）：`day`、`day_male`、`day_female`、`week_rookie`、`week`、`day_r18`、`week_r18`；本库不注入任何默认。

---

### 用户（15 个方法）

用户列表类返回的 `user_previews`，每项包一个 `user` 对象（`id`、`name`、`account`、`profile_image_urls.medium`、`is_followed` 等）和它的若干 `illusts`。

#### app_user_detail

给什么：`app_user_detail(user_id, **params)`。给一个用户编号，返回这个用户的资料、公开性设置与工作环境。

* 路由：`GET v1/user/detail` → `https://app-api.pixiv.net/v1/user/detail`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_detail`；返回模型 `pixivpy3/models.py::UserInfoDetailed`
* 认证：需 `access_token`

返回裸 JSON `{"user", "profile", "profile_publicity", "workspace"}`：`user` 含 `id`、`name`、`account`、`profile_image_urls`、`comment`、`is_followed`；`profile` 含 `total_follow_users`、`total_illusts`、`total_manga`、`total_novels`、`total_illust_bookmarks_public`、`total_illust_series`、`total_novel_series` 等计数；`profile_publicity` 与 `workspace` 是公开性/工作环境块。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串，如 `'27517'` | 用户编号，取自 `https://www.pixiv.net/users/27517` 或作品里的 `user.id` | 必填（缺参数 Python 直接报 `TypeError`） | `client.app_user_detail('27517')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定（本库不注入源码的 `for_ios`） | `client.app_user_detail('27517', filter='for_ios')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
detail = client.app_user_detail('27517', filter='for_ios')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/detail?user_id=27517&filter=for_ios
print(detail['user']['name'], detail['user']['account'])
print(detail['profile']['total_illusts'], detail['profile']['total_novels'])
```

#### app_user_illusts

给什么：`app_user_illusts(user_id, **params)`。给一个用户编号，返回他发布的插画或漫画列表。

* 路由：`GET v1/user/illusts` → `https://app-api.pixiv.net/v1/user/illusts`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_illusts`；返回模型 `pixivpy3/models.py::UserIllustrations`
* 认证：需 `access_token`

返回 `{"user": {...}, "illusts": [...], "next_url": "..."}`。`illusts` 每项是插画对象（字段见 [`app_illust_detail`](#app_illust_detail)）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_illusts('27517')` |
| `type` | `illust` / `manga` | 只要插画还是只要漫画 | 未规定（P 源码自用 `illust`） | `client.app_user_illusts('27517', type='manga')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_illusts('27517', filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_illusts('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_illusts('27517', type='illust')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/illusts?user_id=27517&type=illust
for illust in page['illusts']:
    print(illust['id'], illust['title'], illust['page_count'])
print(page['next_url'])
```

#### app_user_bookmarks_illust

给什么：`app_user_bookmarks_illust(user_id, **params)`。给一个用户编号，返回他收藏的插画列表。

* 路由：`GET v1/user/bookmarks/illust` → `https://app-api.pixiv.net/v1/user/bookmarks/illust`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_bookmarks_illust`；返回模型 `pixivpy3/models.py::UserBookmarksIllustrations`
* 认证：需 `access_token`

返回 `{"illusts": [...], "next_url": "..."}`。读**别人**的私密收藏需要那个人的授权；裸 token 只能读公开的。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_bookmarks_illust('27517')` |
| `restrict` | `public` / `private` | 收藏可见范围 | 未规定（P 源码常自带 `public`，本库不注入） | `client.app_user_bookmarks_illust('27517', restrict='public')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_bookmarks_illust('27517', filter='for_ios')` |
| `max_bookmark_id` | 整数或数字串 | 翻页游标 | 未规定 | `client.app_user_bookmarks_illust('27517', max_bookmark_id='150000000')` |
| `tag` | 字符串 | 只看带该收藏标签的作品 | 未规定 | `client.app_user_bookmarks_illust('27517', tag='cat')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_bookmarks_illust('27517', restrict='public', tag='cat')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/bookmarks/illust?user_id=27517&restrict=public&tag=cat
print(len(page['illusts']), page['next_url'])
```

#### app_user_bookmarks_novel

给什么：`app_user_bookmarks_novel(user_id, **params)`。给一个用户编号，返回他收藏的小说列表。

* 路由：`GET v1/user/bookmarks/novel` → `https://app-api.pixiv.net/v1/user/bookmarks/novel`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_bookmarks_novel`；返回模型 `pixivpy3/models.py::UserBookmarksNovel`
* 认证：需 `access_token`

返回 `{"novels": [...], "next_url": "..."}`；`novels` 每项是小说对象（字段见 [`app_novel_detail`](#app_novel_detail)）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_bookmarks_novel('27517')` |
| `restrict` | `public` / `private` | 收藏可见范围 | 未规定 | `client.app_user_bookmarks_novel('27517', restrict='public')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_bookmarks_novel('27517', filter='for_ios')` |
| `max_bookmark_id` | 整数或数字串 | 翻页游标 | 未规定 | `client.app_user_bookmarks_novel('27517', max_bookmark_id='150000000')` |
| `tag` | 字符串 | 只看带该收藏标签的小说 | 未规定 | `client.app_user_bookmarks_novel('27517', tag='cat')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_bookmarks_novel('27517', restrict='public')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/bookmarks/novel?user_id=27517&restrict=public
print(len(page['novels']), page['next_url'])
```

#### app_user_related

给什么：`app_user_related(seed_user_id, **params)`。给一个种子用户编号，返回和他相关的用户。

* 路由：`GET v1/user/related` → `https://app-api.pixiv.net/v1/user/related`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_related`
* 认证：需 `access_token`

返回 `{"user_previews": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `seed_user_id` | 数字串 | 作为基准的用户编号（P 源码要求它在查询串最后） | 必填 | `client.app_user_related('27517')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_related('27517', filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定（P 源码恒发，缺省 `0`） | `client.app_user_related('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_related('27517')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/related?seed_user_id=27517
for preview in page['user_previews']:
    print(preview['user']['id'], preview['user']['name'])
print(page['next_url'])
```

#### app_user_recommended

给什么：`app_user_recommended(**params)`。返回**当前登录账号**的推荐用户列表（无必填值）。

* 路由：`GET v1/user/recommended` → `https://app-api.pixiv.net/v1/user/recommended`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_recommended`
* 认证：需 `access_token`

返回 `{"user_previews": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_recommended(filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_recommended(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_recommended()
# 真实 URL：GET https://app-api.pixiv.net/v1/user/recommended
print(len(page['user_previews']), page['next_url'])
```

#### app_user_following

给什么：`app_user_following(user_id, **params)`。给一个用户编号，返回他关注的人。

* 路由：`GET v1/user/following` → `https://app-api.pixiv.net/v1/user/following`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_following`；返回模型 `pixivpy3/models.py::UserFollowing`
* 认证：需 `access_token`

返回 `{"user_previews": [...], "next_url": "..."}`。读**别人**的私密关注列表需要那个人的授权。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_following('27517')` |
| `restrict` | `public`（P 源码自用值；其它取值 P/Z 未给） | 关注列表可见范围 | 未规定（P 源码常自带 `public`） | `client.app_user_following('27517', restrict='public')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_following('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_following('27517', restrict='public')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/following?user_id=27517&restrict=public
print(len(page['user_previews']), page['next_url'])
```

#### app_user_follower

给什么：`app_user_follower(user_id, **params)`。给一个用户编号，返回关注他的人。

* 路由：`GET v1/user/follower` → `https://app-api.pixiv.net/v1/user/follower`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_follower`
* 认证：需 `access_token`

返回 `{"user_previews": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_follower('27517')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_follower('27517', filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_follower('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_follower('27517')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/follower?user_id=27517
print(len(page['user_previews']), page['next_url'])
```

#### app_user_mypixiv

给什么：`app_user_mypixiv(user_id, **params)`。给一个用户编号，返回他的 MyPixiv（好 P 友）列表。

* 路由：`GET v1/user/mypixiv` → `https://app-api.pixiv.net/v1/user/mypixiv`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_mypixiv`
* 认证：需 `access_token`

返回 `{"user_previews": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_mypixiv('27517')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_mypixiv('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_mypixiv('27517')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/mypixiv?user_id=27517
print(len(page['user_previews']), page['next_url'])
```

#### app_user_list

给什么：`app_user_list(user_id, **params)`。给一个用户编号，返回他的公开用户分组（`v2` 路由）。

* 路由：`GET v2/user/list` → `https://app-api.pixiv.net/v2/user/list`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_list`
* 认证：需 `access_token`

返回 `{"user_previews": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_list('27517')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_list('27517', filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_list('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_list('27517')
# 真实 URL：GET https://app-api.pixiv.net/v2/user/list?user_id=27517
print(len(page['user_previews']), page['next_url'])
```

#### app_user_bookmark_tags_illust

给什么：`app_user_bookmark_tags_illust(user_id, **params)`。给一个用户编号，返回他插画收藏用过的标签及数量。

* 路由：`GET v1/user/bookmark-tags/illust` → `https://app-api.pixiv.net/v1/user/bookmark-tags/illust`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_bookmark_tags_illust`
* 认证：需 `access_token`

返回 `{"bookmark_tags": [...], "next_url": "..."}`；每个标签含 `tag`、`count` 和 `name` 映射。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_bookmark_tags_illust('27517')` |
| `restrict` | `public`（P 源码自用值；其它取值 P/Z 未给） | 收藏可见范围 | 未规定（P 源码常自带 `public`） | `client.app_user_bookmark_tags_illust('27517', restrict='public')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_bookmark_tags_illust('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_bookmark_tags_illust('27517', restrict='public')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/bookmark-tags/illust?user_id=27517&restrict=public
for tag in page['bookmark_tags']:
    print(tag['tag'], tag['count'])
print(page['next_url'])
```

#### app_user_bookmark_tags_novel

给什么：`app_user_bookmark_tags_novel(user_id, **params)`。给一个用户编号，返回他小说收藏用过的标签。

* 路由：`GET v1/user/bookmark-tags/novel` → `https://app-api.pixiv.net/v1/user/bookmark-tags/novel`
* 来源：**Z**（ZipFile 抓包 `/v1/user/bookmark-tags/novel`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"bookmark_tags": [...], "next_url": "..."}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_bookmark_tags_novel('27517')` |
| `restrict` | `public`（Z 自用值；其它取值 Z 未给） | 收藏可见范围 | 未规定 | `client.app_user_bookmark_tags_novel('27517', restrict='public')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_bookmark_tags_novel('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_bookmark_tags_novel('27517', restrict='public')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/bookmark-tags/novel?user_id=27517&restrict=public
# 来源：Z；未实测
print(page['bookmark_tags'], page['next_url'])
```

#### app_user_browsing_history_illusts

给什么：`app_user_browsing_history_illusts(**params)`。返回当前账号的插画浏览历史（无必填值）。

* 路由：`GET v1/user/browsing-history/illusts` → `https://app-api.pixiv.net/v1/user/browsing-history/illusts`
* 来源：**Z**（ZipFile 抓包 `/v1/user/browsing-history/illusts`）
* 认证：来源声称需 `access_token`（未实测）
* 注：Z 依据里这条路由**没有** `user_id` 必填参数，本库不臆造一个。

返回 `{"illusts": [...], "next_url": "..."}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_browsing_history_illusts(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_browsing_history_illusts(offset=30)
# 真实 URL：GET https://app-api.pixiv.net/v1/user/browsing-history/illusts?offset=30
# 来源：Z；未实测
print(len(page['illusts']), page['next_url'])
```

#### app_user_browsing_history_novels

给什么：`app_user_browsing_history_novels(**params)`。返回当前账号的小说浏览历史（无必填值）。

* 路由：`GET v1/user/browsing-history/novels` → `https://app-api.pixiv.net/v1/user/browsing-history/novels`
* 来源：**Z**（ZipFile 抓包 `/v1/user/browsing-history/novels`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"novels": [...], "next_url": "..."}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_browsing_history_novels(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_browsing_history_novels(offset=30)
# 真实 URL：GET https://app-api.pixiv.net/v1/user/browsing-history/novels?offset=30
# 来源：Z；未实测
print(len(page['novels']), page['next_url'])
```

#### app_user_state

给什么：`app_user_state(**params)`。返回当前登录账号的状态（无参数）。

* 路由：`GET v1/user/me/state` → `https://app-api.pixiv.net/v1/user/me/state`
* 来源：**Z**（ZipFile 抓包 `/v1/user/me/state`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"user_state": {"is_mail_authorized": <bool>}}`（Z 依据）。

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
state = client.app_user_state()
# 真实 URL：GET https://app-api.pixiv.net/v1/user/me/state
# 来源：Z；未实测
print(state['user_state']['is_mail_authorized'])
```

---

### 插画（16 个方法）

列表里的插画对象（P `models.py::IllustrationInfo`）字段：`id`、`title`、`type`（`illust`/`manga`/`ugoira`）、`image_urls{square_medium, medium, large}`、`caption`、`restrict`、`user`、`tags[{name, translated_name}]`、`tools`、`create_date`、`page_count`、`width`、`height`、`sanity_level`、`x_restrict`、`series{id, title}`、`meta_single_page{original_image_url}`、`meta_pages[{image_urls{...}}]`、`total_view`、`total_bookmarks`、`is_bookmarked`、`visible`、`is_muted`、`illust_ai_type`、`illust_book_style`、`total_comments`、`restriction_attributes[]`。`image_urls` / `meta_pages` 的地址都指向 `i.pximg.net`，本库原样返回、不下载。

#### app_illust_detail

给什么：`app_illust_detail(illust_id, **params)`。给一个作品编号，返回这一张插画/漫画的详情。

* 路由：`GET v1/illust/detail` → `https://app-api.pixiv.net/v1/illust/detail`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_detail`；返回模型 `pixivpy3/models.py::IllustrationInfo`
* 认证：需 `access_token`。**L（拒绝证据，非成功）**：匿名 `GET https://app-api.pixiv.net/v1/illust/detail?illust_id=59580629` → `400 application/json`，正文 `{"error": {"user_message": "", "message": "Error occurred at the OAuth process. Please check your Access Token to fix this. Error Message: invalid_request", "reason": "", "user_message_details": {}}}`

返回裸 JSON `{"illust": {...}}`，`illust` 的字段即上面那套 `IllustrationInfo` 字段。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串，如 `'149040133'` | 作品编号，取自作品页 URL `https://www.pixiv.net/artworks/149040133` | 必填 | `client.app_illust_detail('149040133')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
result = client.app_illust_detail('149040133')
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/detail?illust_id=149040133
illust = result['illust']
print(illust['title'], illust['type'], illust['page_count'])
print(illust['image_urls']['large'], illust['total_view'], illust['total_bookmarks'])
print([tag['name'] for tag in illust['tags']])
```

#### app_illust_follow

给什么：`app_illust_follow(**params)`。返回**当前登录账号**关注的画师的新作列表（无必填值）。

* 路由：`GET v2/illust/follow` → `https://app-api.pixiv.net/v2/illust/follow`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_follow`
* 认证：需 `access_token`

返回 `{"illusts": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `restrict` | `public` / `private` | 关注来源可见范围 | 未规定（P 源码常自带 `public`） | `client.app_illust_follow(restrict='public')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_illust_follow(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_follow(restrict='public')
# 真实 URL：GET https://app-api.pixiv.net/v2/illust/follow?restrict=public
print(len(page['illusts']), page['next_url'])
```

#### app_illust_comments

给什么：`app_illust_comments(illust_id, **params)`。给一个作品编号，返回它的评论。

* 路由：`GET v1/illust/comments` → `https://app-api.pixiv.net/v1/illust/comments`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_comments`
* 认证：需 `access_token`

返回 `{"comments": [...], "next_url": "..."}`，并在要求时带 `total_comments`。每条评论含 `id`、`comment`、`date`、`user`、`parent_comment`、`has_replies`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串 | 作品编号 | 必填 | `client.app_illust_comments('149040133')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_illust_comments('149040133', offset=20)` |
| `include_total_comments` | 布尔 | 响应是否带评论总数 | 未规定（P 源码该参数为 bool） | `client.app_illust_comments('149040133', include_total_comments=True)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_comments('149040133', include_total_comments=True)
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/comments?illust_id=149040133&include_total_comments=true
print(page.get('total_comments'), len(page['comments']), page['next_url'])
```

#### app_illust_related

给什么：`app_illust_related(illust_id, **params)`。给一个作品编号，返回与它相关的插画。

* 路由：`GET v2/illust/related` → `https://app-api.pixiv.net/v2/illust/related`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_related`
* 认证：需 `access_token`

返回 `{"illusts": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串 | 作品编号 | 必填 | `client.app_illust_related('149040133')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_illust_related('149040133', filter='for_ios')` |
| `seed_illust_ids` | 列表 | 追加的种子作品号；编码成重复的 `seed_illust_ids[]=` | 未规定 | `client.app_illust_related('149040133', seed_illust_ids=['149040133'])` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定（P 源码恒发） | `client.app_illust_related('149040133', offset=30)` |
| `viewed` | 列表 | 已看作品号；编码成重复的 `viewed[]=` | 未规定 | `client.app_illust_related('149040133', viewed=['149040133'])` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_related('149040133', viewed=['149040133'])
# 真实 URL：GET https://app-api.pixiv.net/v2/illust/related?illust_id=149040133&viewed[]=149040133
print([illust['id'] for illust in page['illusts']], page['next_url'])
```

#### app_illust_recommended

给什么：`app_illust_recommended(**params)`。返回推荐插画（无必填值）。

* 路由：`GET v1/illust/recommended` → `https://app-api.pixiv.net/v1/illust/recommended`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_recommended`
* 认证：需 `access_token`

返回 `{"illusts": [...], "ranking_illusts": [...], "next_url": "..."}`，并按所请求选项带 `contest_exists`、`privacy_policy`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `content_type` | `illust` / `manga` | 推荐插画还是漫画 | 未规定（P 源码自用 `illust`） | `client.app_illust_recommended(content_type='illust')` |
| `include_ranking_label` | 布尔 | 是否带榜单标签 | 未规定（P 源码自带 `true`） | `client.app_illust_recommended(include_ranking_label=True)` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_illust_recommended(filter='for_ios')` |
| `max_bookmark_id_for_recommend` | 整数或数字串 | 推荐用收藏游标 | 未规定 | `client.app_illust_recommended(max_bookmark_id_for_recommend='150000000')` |
| `min_bookmark_id_for_recent_illust` | 整数或数字串 | 近期作品收藏下限 | 未规定 | `client.app_illust_recommended(min_bookmark_id_for_recent_illust='1000')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_illust_recommended(offset=30)` |
| `include_ranking_illusts` | 布尔 | 是否带 `ranking_illusts` | 未规定 | `client.app_illust_recommended(include_ranking_illusts=True)` |
| `include_privacy_policy` | 布尔 | 是否带隐私政策块 | 未规定 | `client.app_illust_recommended(include_privacy_policy=True)` |
| `viewed` | 列表 | 已看作品号；编码成重复的 `viewed[]=` | 未规定 | `client.app_illust_recommended(viewed=['149040133'])` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_recommended(content_type='illust', include_ranking_illusts=True)
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/recommended?content_type=illust&include_ranking_illusts=true
print(len(page['illusts']), len(page['ranking_illusts']), page['next_url'])
```

#### app_illust_ranking

给什么：`app_illust_ranking(**params)`。返回插画排行榜的一页（无必填值）。

* 路由：`GET v1/illust/ranking` → `https://app-api.pixiv.net/v1/illust/ranking`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_ranking`
* 认证：需 `access_token`

返回 `{"illusts": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `mode` | 见[枚举速查](#枚举与共用参数速查)的榜单 mode 列表 | 榜单类型（日榜、周榜、R18 等） | 未规定（P 源码自用 `day`） | `client.app_illust_ranking(mode='day')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_illust_ranking(mode='day', filter='for_ios')` |
| `date` | `YYYY-MM-DD` | 指定榜单日期 | 未规定 | `client.app_illust_ranking(mode='day', date='2026-01-01')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_illust_ranking(mode='day', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_ranking(mode='day')
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/ranking?mode=day
for illust in page['illusts']:
    print(illust['id'], illust['title'])
print(page['next_url'])
```

#### app_illust_new

给什么：`app_illust_new(**params)`。返回最新投稿插画的一页（无必填值）。

* 路由：`GET v1/illust/new` → `https://app-api.pixiv.net/v1/illust/new`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_new`
* 认证：需 `access_token`

返回 `{"illusts": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `content_type` | `illust` / `manga` | 新作是插画还是漫画 | 未规定（P 源码自用 `illust`） | `client.app_illust_new(content_type='illust')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_illust_new(filter='for_ios')` |
| `max_illust_id` | 整数或数字串 | 翻页游标 | 未规定 | `client.app_illust_new(max_illust_id='150000000')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_new(content_type='illust')
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/new?content_type=illust
print(len(page['illusts']), page['next_url'])
```

#### app_ugoira_metadata

给什么：`app_ugoira_metadata(illust_id, **params)`。给一个动图（ugoira）作品编号，返回它的帧数据与压缩包地址。

* 路由：`GET v1/ugoira/metadata` → `https://app-api.pixiv.net/v1/ugoira/metadata`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.ugoira_metadata`
* 认证：需 `access_token`

返回 `{"ugoira_metadata": {"zip_urls": {"medium": "...", "original": "..."}, "frames": [{"file": "...", "delay": <毫秒>}, ...]}}`。`zip_urls` 指向 `i.pximg.net`，本库原样返回、不下载。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串 | ugoira 作品编号 | 必填 | `client.app_ugoira_metadata('149040133')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
meta = client.app_ugoira_metadata('149040133')
# 真实 URL：GET https://app-api.pixiv.net/v1/ugoira/metadata?illust_id=149040133
ugoira = meta['ugoira_metadata']
print(ugoira['zip_urls']['original'], len(ugoira['frames']))
```

#### app_trending_tags_illust

给什么：`app_trending_tags_illust(**params)`。返回插画趋势标签（无必填值）。

* 路由：`GET v1/trending-tags/illust` → `https://app-api.pixiv.net/v1/trending-tags/illust`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.trending_tags_illust`
* 认证：需 `access_token`

返回 `{"trend_tags": [...]}`；每项含 `tag`、`translated_name` 与 `illust`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_trending_tags_illust(filter='for_ios')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
result = client.app_trending_tags_illust()
# 真实 URL：GET https://app-api.pixiv.net/v1/trending-tags/illust
for trend in result['trend_tags']:
    print(trend['tag'], trend['translated_name'])
```

#### app_illust_comment_replies

给什么：`app_illust_comment_replies(comment_id, **params)`。给一条评论的编号，返回它的回复。

* 路由：`GET v1/illust/comment/replies` → `https://app-api.pixiv.net/v1/illust/comment/replies`
* 来源：**H**（hanshsieh 第三方 OpenAPI `/v1/illust/comment/replies`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"comments": [...], "next_url": "..."}`（H 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `comment_id` | 数字串 | 评论编号 | 必填 | `client.app_illust_comment_replies('123456')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_comment_replies('123456')
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/comment/replies?comment_id=123456
# 来源：H；未实测
print(len(page['comments']), page['next_url'])
```

#### app_illust_mypixiv

给什么：`app_illust_mypixiv(**params)`。返回好 P 友（MyPixiv）的插画（无必填值）。

* 路由：`GET v2/illust/mypixiv` → `https://app-api.pixiv.net/v2/illust/mypixiv`
* 来源：**Z**（ZipFile 抓包 `/v2/illust/mypixiv`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"illusts": [...], "next_url": "..."}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_illust_mypixiv(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_mypixiv(offset=30)
# 真实 URL：GET https://app-api.pixiv.net/v2/illust/mypixiv?offset=30
# 来源：Z；未实测
print(len(page['illusts']), page['next_url'])
```

#### app_illust_popular

给什么：`app_illust_popular(**params)`。返回热门插画（无必填值）。

* 路由：`GET v1/illust/popular` → `https://app-api.pixiv.net/v1/illust/popular`
* 来源：**Z**（ZipFile 抓包只给路由，未声明成功响应结构）
* 认证：来源声称需 `access_token`（未实测）
* 返回：**Z 只给路由，没有声明成功响应里有哪些键**；本库不臆造字段，也不把 `illust_id` 之类当必填。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `**params` | 任意名字 | 原样进查询串；Z 未记录这条路由的已知输入 | 不传即不加 | — |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_popular()
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/popular
# 来源：Z 只给路由，未声明成功字段；未实测
print(page)
```

#### app_manga_recommended

给什么：`app_manga_recommended(**params)`。返回推荐漫画（无必填值）。

* 路由：`GET v1/manga/recommended` → `https://app-api.pixiv.net/v1/manga/recommended`
* 来源：**Z**（ZipFile 抓包 `/v1/manga/recommended`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"illusts": [...], "ranking_illusts": [...], "next_url": "..."}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_manga_recommended(filter='for_ios')` |
| `include_ranking_illusts` | 布尔 | 是否带 `ranking_illusts` | 未规定 | `client.app_manga_recommended(include_ranking_illusts=True)` |
| `max_bookmark_id` | 整数或数字串 | 翻页游标 | 未规定 | `client.app_manga_recommended(max_bookmark_id='150000000')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_manga_recommended(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_manga_recommended(include_ranking_illusts=True)
# 真实 URL：GET https://app-api.pixiv.net/v1/manga/recommended?include_ranking_illusts=true
# 来源：Z；未实测
print(len(page['illusts']), len(page['ranking_illusts']), page['next_url'])
```

#### app_trending_tags_manga

给什么：`app_trending_tags_manga(**params)`。返回漫画趋势标签（无必填值）。

* 路由：`GET v1/trending-tags/manga` → `https://app-api.pixiv.net/v1/trending-tags/manga`
* 来源：**Z**（ZipFile 抓包只给路由，未声明成功响应结构）
* 认证：来源声称需 `access_token`（未实测）
* 返回：Z 只给路由，未声明成功字段；预期是 JSON，但本库不断言 `trend_tags` 键存在。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_trending_tags_manga(filter='for_ios')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
result = client.app_trending_tags_manga(filter='for_ios')
# 真实 URL：GET https://app-api.pixiv.net/v1/trending-tags/manga?filter=for_ios
# 来源：Z 只给路由，未声明成功字段；未实测
print(result)
```

#### app_illust_series

给什么：`app_illust_series(illust_series_id, **params)`。给一个插画系列编号，返回系列信息与该系列内的插画。

* 路由：`GET v1/illust/series` → `https://app-api.pixiv.net/v1/illust/series`
* 来源：**G**（gallery-dl `PixivAPI.illust_series`，<https://raw.githubusercontent.com/mikf/gallery-dl/master/gallery_dl/extractor/pixiv.py>；它用的 wire 键是 `illust_series_id`）
* 认证：来源声称需 `access_token`。**L（拒绝证据，非成功）**：匿名 `GET https://app-api.pixiv.net/v1/illust/series?illust_series_id=257832&offset=0` → `400 application/json`，正文 `{"error": {"user_message": "", "message": "Error occurred at the OAuth process. ... invalid_request", "reason": "", "user_message_details": {}}}`

返回 `{"illusts": [...], "next_url": "...", "illust_series_detail": {"title": ..., "caption": ..., "series_work_count": ...}}`（G 依据；`illust_series_detail` 这三个字段是 gallery-dl 的 `PixivSeriesExtractor` 实际取用的）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_series_id` | 数字串，如 `'257832'` | 插画系列编号 | 必填 | `client.app_illust_series('257832')` |
| `offset` | 整数，从 `0` 起 | 翻页游标 | 未规定（G 源码自带 `0`，本库不注入） | `client.app_illust_series('257832', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_series('257832')
# 真实 URL：GET https://app-api.pixiv.net/v1/illust/series?illust_series_id=257832
# 来源：G；匿名实测 400（拒绝），带 token 成功未实测
detail = page['illust_series_detail']
print(detail['title'], detail['series_work_count'])
print(len(page['illusts']), page['next_url'])
```

#### app_illust_comments_v3

给什么：`app_illust_comments_v3(illust_id, **params)`。给一个作品编号，返回它的评论——**这是 `v3/illust/comments`，和 `app_illust_comments()` 的 `v1/illust/comments` 是两条不同路由，不是别名**。

* 路由：`GET v3/illust/comments` → `https://app-api.pixiv.net/v3/illust/comments`
* 来源：**G**（gallery-dl `PixivAPI.illust_comments`，`_pagination` 以 `comments` 为列表键）
* 认证：来源声称需 `access_token`。**L（拒绝证据，非成功）**：匿名 `GET https://app-api.pixiv.net/v3/illust/comments?illust_id=149040133` → `400 application/json`，正文 `{"error": {"user_message": "", "message": "Error occurred at the OAuth process. ... invalid_request", "reason": "", "user_message_details": {}}}`
* 注：v1 与 v3 各封装一个方法，本库不加兼容别名；v2 候选已因匿名 404 排除（见边界）。

返回 `{"comments": [...], "next_url": "..."}`（G 依据；首次调用源码只给 `illust_id`，后续游标从 `next_url` 回传，本库不注入默认）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串 | 作品编号 | 必填 | `client.app_illust_comments_v3('149040133')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_illust_comments_v3('149040133')
# 真实 URL：GET https://app-api.pixiv.net/v3/illust/comments?illust_id=149040133
# 来源：G；匿名实测 400（拒绝），带 token 成功未实测
print(len(page['comments']), page['next_url'])
```

---

### 搜索（4 个方法）

#### app_search_illust

给什么：`app_search_illust(word, **params)`。给关键词，搜插画。

* 路由：`GET v1/search/illust` → `https://app-api.pixiv.net/v1/search/illust`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.search_illust`；返回模型 `pixivpy3/models.py::SearchIllustrations`
* 认证：需 `access_token`

返回 `{"illusts": [...], "next_url": "...", "search_span_limit": ..., "show_ai": ...}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `word` | 字符串，如 `'cat'` | 搜索关键词 | 必填 | `client.app_search_illust('cat')` |
| `search_target` | 见[枚举速查](#枚举与共用参数速查) | 匹配方式 | 未规定（P 源码自用 `partial_match_for_tags`） | `client.app_search_illust('cat', search_target='partial_match_for_tags')` |
| `sort` | `date_desc` / `date_asc` / `popular_desc` | 排序 | 未规定（P 源码自用 `date_desc`） | `client.app_search_illust('cat', sort='date_desc')` |
| `duration` | `within_last_day` / `within_last_week` / `within_last_month` | 时间范围 | 未规定 | `client.app_search_illust('cat', duration='within_last_week')` |
| `start_date` / `end_date` | `YYYY-MM-DD` | 起止日期 | 未规定 | `client.app_search_illust('cat', start_date='2026-01-01')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_search_illust('cat', filter='for_ios')` |
| `search_ai_type` | `0` / `1` | AI 作品过滤 | 未规定 | `client.app_search_illust('cat', search_ai_type=1)` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_search_illust('cat', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_search_illust('cat', search_target='partial_match_for_tags',
                                sort='date_desc', filter='for_ios')
# 真实 URL：GET https://app-api.pixiv.net/v1/search/illust?
#   word=cat&search_target=partial_match_for_tags&sort=date_desc&filter=for_ios
print(page['illusts'][0]['id'], page['illusts'][0]['title'], page['next_url'])
```

#### app_search_novel

给什么：`app_search_novel(word, **params)`。给关键词，搜小说。

* 路由：`GET v1/search/novel` → `https://app-api.pixiv.net/v1/search/novel`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.search_novel`；返回模型 `pixivpy3/models.py::SearchNovel`
* 认证：需 `access_token`

返回 `{"novels": [...], "next_url": "...", "search_span_limit": ..., "show_ai": ...}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `word` | 字符串 | 搜索关键词 | 必填 | `client.app_search_novel('cat')` |
| `search_target` | `partial_match_for_tags` / `exact_match_for_tags` / `title_and_caption` / `keyword` / `text` | 匹配方式（小说另有正文 `text`） | 未规定（P 源码自用 `partial_match_for_tags`） | `client.app_search_novel('cat', search_target='text')` |
| `sort` | `date_desc` / `date_asc` / `popular_desc` | 排序 | 未规定（P 源码自用 `date_desc`） | `client.app_search_novel('cat', sort='date_desc')` |
| `merge_plain_keyword_results` | 布尔 | 合并纯关键词结果 | 未规定（P 源码自带 `true`） | `client.app_search_novel('cat', merge_plain_keyword_results=True)` |
| `include_translated_tag_results` | 布尔 | 是否含翻译标签命中 | 未规定（P 源码自带 `true`） | `client.app_search_novel('cat', include_translated_tag_results=True)` |
| `start_date` / `end_date` | `YYYY-MM-DD` | 起止日期 | 未规定 | `client.app_search_novel('cat', end_date='2026-01-01')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_search_novel('cat', filter='for_ios')` |
| `search_ai_type` | `0` / `1` | AI 作品过滤 | 未规定 | `client.app_search_novel('cat', search_ai_type=1)` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_search_novel('cat', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_search_novel('cat', sort='date_desc')
# 真实 URL：GET https://app-api.pixiv.net/v1/search/novel?word=cat&sort=date_desc
print(page['novels'][0]['id'], page['novels'][0]['title'], page['next_url'])
```

#### app_search_user

给什么：`app_search_user(word, **params)`。给关键词，搜用户。

* 路由：`GET v1/search/user` → `https://app-api.pixiv.net/v1/search/user`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.search_user`
* 认证：需 `access_token`

返回 `{"user_previews": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `word` | 字符串 | 搜索关键词 | 必填 | `client.app_search_user('cat')` |
| `sort` | `date_desc` / `date_asc` / `popular_desc` | 排序 | 未规定（P 源码自用 `date_desc`） | `client.app_search_user('cat', sort='date_desc')` |
| `duration` | `within_last_day` / `within_last_week` / `within_last_month` | 时间范围 | 未规定 | `client.app_search_user('cat', duration='within_last_month')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_search_user('cat', filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_search_user('cat', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_search_user('cat')
# 真实 URL：GET https://app-api.pixiv.net/v1/search/user?word=cat
for preview in page['user_previews']:
    print(preview['user']['id'], preview['user']['name'])
print(page['next_url'])
```

#### app_search_autocomplete

给什么：`app_search_autocomplete(word, **params)`。给关键词前缀，返回搜索自动补全词。

* 路由：`GET v1/search/autocomplete` → `https://app-api.pixiv.net/v1/search/autocomplete`
* 来源：**Z**（ZipFile 抓包 `/v1/search/autocomplete`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"search_auto_complete_keywords": [...]}`（Z 依据；数组元素结构 Z 未声明）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `word` | 字符串，如 `'ca'` | 关键词前缀 | 必填 | `client.app_search_autocomplete('ca')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
result = client.app_search_autocomplete('ca')
# 真实 URL：GET https://app-api.pixiv.net/v1/search/autocomplete?word=ca
# 来源：Z；未实测
print(result['search_auto_complete_keywords'])
```

---

### 小说（12 个方法）

小说对象（P `models.py::NovelInfo`）字段：`id`、`title`、`caption`、`restrict`、`x_restrict`、`is_original`、`image_urls`、`create_date`、`tags[{name, translated_name, added_by_uploaded_user}]`、`page_count`、`text_length`、`user`、`series`、`is_bookmarked`、`total_bookmarks`、`total_view`、`visible`、`total_comments`、`is_muted`、`is_mypixiv_only`、`is_x_restricted`、`novel_ai_type`、`comment_access_control`。

#### app_novel_detail

给什么：`app_novel_detail(novel_id, **params)`。给一个小说编号，返回这篇小说的详情。

* 路由：`GET v2/novel/detail` → `https://app-api.pixiv.net/v2/novel/detail`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.novel_detail`；返回模型 `pixivpy3/models.py::NovelInfo`
* 认证：需 `access_token`。**L（拒绝证据，非成功）**：匿名 `GET https://app-api.pixiv.net/v2/novel/detail?novel_id=11165421` → `400 application/json`，正文同为 `{"error": {"user_message": "", "message": "Error occurred at the OAuth process. ... invalid_request", "reason": "", "user_message_details": {}}}`

返回裸 JSON `{"novel": {...}}`，`novel` 的字段即上面那套 `NovelInfo` 字段。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `novel_id` | 数字串 | 小说编号 | 必填 | `client.app_novel_detail('12345678')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
result = client.app_novel_detail('12345678')
# 真实 URL：GET https://app-api.pixiv.net/v2/novel/detail?novel_id=12345678
novel = result['novel']
print(novel['title'], novel['text_length'], novel['page_count'])
print([tag['name'] for tag in novel['tags']])
```

#### app_novel_series

给什么：`app_novel_series(series_id, **params)`。给一个小说系列编号，返回系列信息与系列内小说。

* 路由：`GET v2/novel/series` → `https://app-api.pixiv.net/v2/novel/series`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.novel_series`
* 认证：需 `access_token`

返回 `{"novel_series_detail": {...}, "novels": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `series_id` | 数字串 | 小说系列编号 | 必填 | `client.app_novel_series('12345')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_novel_series('12345', filter='for_ios')` |
| `last_order` | 整数或数字串 | 系列内翻页游标 | 未规定 | `client.app_novel_series('12345', last_order='10')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
series = client.app_novel_series('12345')
# 真实 URL：GET https://app-api.pixiv.net/v2/novel/series?series_id=12345
print(series['novel_series_detail']['title'], len(series['novels']), series['next_url'])
```

#### app_novel_comments

给什么：`app_novel_comments(novel_id, **params)`。给一个小说编号，返回它的评论。

* 路由：`GET v1/novel/comments` → `https://app-api.pixiv.net/v1/novel/comments`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.novel_comments`；返回模型 `pixivpy3/models.py::NovelComments`
* 认证：需 `access_token`

返回 `{"comments": [...], "next_url": "...", "comment_access_control": ...}`，并在要求时带 `total_comments`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `novel_id` | 数字串 | 小说编号 | 必填 | `client.app_novel_comments('12345678')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_novel_comments('12345678', offset=20)` |
| `include_total_comments` | 布尔 | 响应是否带评论总数 | 未规定 | `client.app_novel_comments('12345678', include_total_comments=True)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_novel_comments('12345678', include_total_comments=True)
# 真实 URL：GET https://app-api.pixiv.net/v1/novel/comments?novel_id=12345678&include_total_comments=true
print(page.get('total_comments'), len(page['comments']), page['next_url'])
```

#### app_novel_recommended

给什么：`app_novel_recommended(**params)`。返回推荐小说（无必填值）。

* 路由：`GET v1/novel/recommended` → `https://app-api.pixiv.net/v1/novel/recommended`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.novel_recommended`
* 认证：需 `access_token`

返回 `{"novels": [...], "ranking_novels": [...], "next_url": "..."}`，并按选项带 `privacy_policy`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `include_ranking_label` | 布尔 | 是否带榜单标签 | 未规定（P 源码自带 `true`） | `client.app_novel_recommended(include_ranking_label=True)` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_novel_recommended(filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_novel_recommended(offset=30)` |
| `include_ranking_novels` | 布尔 | 是否带 `ranking_novels` | 未规定 | `client.app_novel_recommended(include_ranking_novels=True)` |
| `already_recommended` | 逗号串 | 已推荐过的小说号，避免重复 | 未规定 | `client.app_novel_recommended(already_recommended='12345,67890')` |
| `max_bookmark_id_for_recommend` | 整数或数字串 | 推荐用收藏游标 | 未规定 | `client.app_novel_recommended(max_bookmark_id_for_recommend='150000000')` |
| `include_privacy_policy` | 布尔 | 是否带隐私政策块 | 未规定 | `client.app_novel_recommended(include_privacy_policy=True)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_novel_recommended(include_ranking_novels=True)
# 真实 URL：GET https://app-api.pixiv.net/v1/novel/recommended?include_ranking_novels=true
print(len(page['novels']), len(page['ranking_novels']), page['next_url'])
```

#### app_novel_new

给什么：`app_novel_new(**params)`。返回最新投稿小说的一页（无必填值）。

* 路由：`GET v1/novel/new` → `https://app-api.pixiv.net/v1/novel/new`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.novel_new`
* 认证：需 `access_token`

返回 `{"novels": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_novel_new(filter='for_ios')` |
| `max_novel_id` | 整数或数字串 | 翻页游标 | 未规定 | `client.app_novel_new(max_novel_id='150000000')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_novel_new()
# 真实 URL：GET https://app-api.pixiv.net/v1/novel/new
print(len(page['novels']), page['next_url'])
```

#### app_novel_follow

给什么：`app_novel_follow(**params)`。返回**当前登录账号**关注的小说（无必填值）。

* 路由：`GET v1/novel/follow` → `https://app-api.pixiv.net/v1/novel/follow`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.novel_follow`
* 认证：需 `access_token`

返回 `{"novels": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `restrict` | `public` / `private` / `all` | 关注来源可见范围 | 未规定（P 源码常自带 `public`） | `client.app_novel_follow(restrict='public')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_novel_follow(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_novel_follow(restrict='public')
# 真实 URL：GET https://app-api.pixiv.net/v1/novel/follow?restrict=public
print(len(page['novels']), page['next_url'])
```

#### app_user_novels

给什么：`app_user_novels(user_id, **params)`。给一个用户编号，返回他写的小说。

* 路由：`GET v1/user/novels` → `https://app-api.pixiv.net/v1/user/novels`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_novels`；返回模型 `pixivpy3/models.py::UserNovels`
* 认证：需 `access_token`

返回 `{"user": {...}, "novels": [...], "next_url": "..."}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_novels('27517')` |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_user_novels('27517', filter='for_ios')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_user_novels('27517', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_user_novels('27517')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/novels?user_id=27517
print(page['user']['name'], len(page['novels']), page['next_url'])
```

#### app_webview_novel

给什么：`app_webview_novel(novel_id, **params)`。给一个小说编号，返回该小说的 webview 页面——**这是 HTML，不是 JSON**。

* 路由：`GET webview/v2/novel` → `https://app-api.pixiv.net/webview/v2/novel`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.webview_novel`
* 认证：需 `access_token`
* 返回：页面 HTML 原文（经 `response_format='text'` 原样返回），本库**不解析、不抽小说正文或元数据**。小说正文与 `WebviewNovel` 元数据内嵌在那段 HTML 里，要取就自己从文本里解析。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `novel_id` | 数字串 | 小说编号；**查询键名是 `id`，不是 `novel_id`** | 必填 | `client.app_webview_novel('12345678')` |
| `viewer_version` | 日期编码的构建串，如 `'20221031_ai'` | 站点要求的查看器版本号 | 未规定（P 源码恒发 `20221031_ai`，本库不注入，按需显式传） | `client.app_webview_novel('12345678', viewer_version='20221031_ai')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
html = client.app_webview_novel('12345678', viewer_version='20221031_ai')
# 真实 URL：GET https://app-api.pixiv.net/webview/v2/novel?id=12345678&viewer_version=20221031_ai
# 返回：HTML 文本（不是 JSON）；本库不抽小说
print(type(html), len(html))
```

#### app_novel_ranking

给什么：`app_novel_ranking(**params)`。返回小说排行榜的一页（无必填值）。

* 路由：`GET v1/novel/ranking` → `https://app-api.pixiv.net/v1/novel/ranking`
* 来源：**Z**（ZipFile 抓包 `/v1/novel/ranking`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"novels": [...], "next_url": "..."}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `mode` | 见[枚举速查](#枚举与共用参数速查)的小说 mode 列表 | 榜单类型 | 未规定 | `client.app_novel_ranking(mode='day')` |
| `date` | `YYYY-MM-DD` | 指定榜单日期 | 未规定 | `client.app_novel_ranking(mode='day', date='2026-01-01')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_novel_ranking(mode='day', offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_novel_ranking(mode='day')
# 真实 URL：GET https://app-api.pixiv.net/v1/novel/ranking?mode=day
# 来源：Z；未实测
print([novel['id'] for novel in page['novels']], page['next_url'])
```

#### app_novel_mypixiv

给什么：`app_novel_mypixiv(**params)`。返回好 P 友（MyPixiv）的小说（无必填值）。

* 路由：`GET v1/novel/mypixiv` → `https://app-api.pixiv.net/v1/novel/mypixiv`
* 来源：**Z**（ZipFile 抓包 `/v1/novel/mypixiv`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"novels": [...], "next_url": "..."}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_novel_mypixiv(offset=30)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_novel_mypixiv(offset=30)
# 真实 URL：GET https://app-api.pixiv.net/v1/novel/mypixiv?offset=30
# 来源：Z；未实测
print(len(page['novels']), page['next_url'])
```

#### app_novel_popular

给什么：`app_novel_popular(**params)`。返回热门小说（无必填值）。

* 路由：`GET v1/novel/popular` → `https://app-api.pixiv.net/v1/novel/popular`
* 来源：**Z**（ZipFile 抓包只给路由，未声明成功响应结构）
* 认证：来源声称需 `access_token`（未实测）
* 返回：**Z 只给路由，没有声明成功响应里有哪些键**；本库不臆造字段，也不把 `novel_id` 之类当必填。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `**params` | 任意名字 | 原样进查询串；Z 未记录这条路由的已知输入 | 不传即不加 | — |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_novel_popular()
# 真实 URL：GET https://app-api.pixiv.net/v1/novel/popular
# 来源：Z 只给路由，未声明成功字段；未实测
print(page)
```

#### app_trending_tags_novel

给什么：`app_trending_tags_novel(**params)`。返回小说趋势标签（无必填值）。

* 路由：`GET v1/trending-tags/novel` → `https://app-api.pixiv.net/v1/trending-tags/novel`
* 来源：**Z**（ZipFile 抓包只给路由，未声明成功响应结构）
* 认证：来源声称需 `access_token`（未实测）
* 返回：Z 只给路由，未声明成功字段；预期是 JSON，但本库不断言 `trend_tags` 键存在。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `filter` | `for_ios` | 见[枚举速查](#枚举与共用参数速查) | 未规定 | `client.app_trending_tags_novel(filter='for_ios')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
result = client.app_trending_tags_novel(filter='for_ios')
# 真实 URL：GET https://app-api.pixiv.net/v1/trending-tags/novel?filter=for_ios
# 来源：Z 只给路由，未声明成功字段；未实测
print(result)
```

---

### 收藏与关注状态（读，3 个方法）

#### app_illust_bookmark_detail

给什么：`app_illust_bookmark_detail(illust_id, **params)`。给一个作品编号，返回**当前登录账号**对该作品的收藏状态。

* 路由：`GET v2/illust/bookmark/detail` → `https://app-api.pixiv.net/v2/illust/bookmark/detail`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_bookmark_detail`
* 认证：需 `access_token`

返回 `{"bookmark_detail": {"is_bookmarked": <bool>, "tags": [...]}}`。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串 | 作品编号 | 必填 | `client.app_illust_bookmark_detail('149040133')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
state = client.app_illust_bookmark_detail('149040133')
# 真实 URL：GET https://app-api.pixiv.net/v2/illust/bookmark/detail?illust_id=149040133
print(state['bookmark_detail']['is_bookmarked'], state['bookmark_detail']['tags'])
```

#### app_novel_bookmark_detail

给什么：`app_novel_bookmark_detail(novel_id, **params)`。给一个小说编号，返回当前账号对该小说的收藏状态。

* 路由：`GET v2/novel/bookmark/detail` → `https://app-api.pixiv.net/v2/novel/bookmark/detail`
* 来源：**Z**（ZipFile 抓包 `/v2/novel/bookmark/detail`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"bookmark_detail": {"is_bookmarked": <bool>, "restrict": ..., "tags": [{"name": ..., "count": ..., "is_registered": ...}]}}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `novel_id` | 数字串 | 小说编号 | 必填 | `client.app_novel_bookmark_detail('12345678')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
state = client.app_novel_bookmark_detail('12345678')
# 真实 URL：GET https://app-api.pixiv.net/v2/novel/bookmark/detail?novel_id=12345678
# 来源：Z；未实测
print(state['bookmark_detail']['is_bookmarked'], state['bookmark_detail']['tags'])
```

#### app_user_follow_detail

给什么：`app_user_follow_detail(user_id, **params)`。给一个用户编号，返回当前账号对他的关注状态。

* 路由：`GET v1/user/follow/detail` → `https://app-api.pixiv.net/v1/user/follow/detail`
* 来源：**Z**（ZipFile 抓包 `/v1/user/follow/detail`）
* 认证：来源声称需 `access_token`（未实测）

返回 `{"follow_detail": {"is_followed": <bool>, "restrict": ...}}`（Z 依据）。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号 | 必填 | `client.app_user_follow_detail('27517')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
detail = client.app_user_follow_detail('27517')
# 真实 URL：GET https://app-api.pixiv.net/v1/user/follow/detail?user_id=27517
# 来源：Z；未实测
print(detail['follow_detail']['is_followed'], detail['follow_detail']['restrict'])
```

---

### 账号写操作（6 个方法，**本库一次都不会调用**）

下面 6 个是 POST，会改变登录账号的状态。它们在这里只作为契约记录，参数形态与其它方法一致：必填值 + `**attributes` 全部写进**表单正文**（`form`，不是 JSON）。**响应是站点返回的 JSON；来源没有声明成功响应里有哪些键**（唯一例外是 `app_illust_browsing_history_add()`，H 来源只声明一个空对象 `{}`），所以本页不写 `success: true` 之类的“成功字段”。

#### app_illust_bookmark_add

给什么：`app_illust_bookmark_add(illust_id, **attributes)`。收藏一个作品。

* 路由：`POST v2/illust/bookmark/add` → `https://app-api.pixiv.net/v2/illust/bookmark/add`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_bookmark_add`
* 认证：需 `access_token`
* 返回：站点 JSON（P 源码未声明成功键）

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串 | 作品编号（进表单正文） | 必填 | `client.app_illust_bookmark_add('149040133')` |
| `restrict` | `public`（P 源码自用值；其它取值 P/Z 未给） | 收藏可见范围 | 未规定（P 源码常自带 `public`） | `client.app_illust_bookmark_add('149040133', restrict='public')` |
| `tags` | 列表 | 收藏标签；编码成重复的 `tags[]=` 表单字段 | 未规定 | `client.app_illust_bookmark_add('149040133', tags=['cat'])` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
# 本库不调用写方法；下面是它的调用形态，仅为记录契约
client.app_illust_bookmark_add('149040133', restrict='public', tags=['cat'])
# 真实 URL：POST https://app-api.pixiv.net/v2/illust/bookmark/add
# 表单正文：illust_id=149040133&restrict=public&tags[]=cat
```

#### app_illust_bookmark_delete

给什么：`app_illust_bookmark_delete(illust_id, **attributes)`。取消收藏一个作品。

* 路由：`POST v1/illust/bookmark/delete` → `https://app-api.pixiv.net/v1/illust/bookmark/delete`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.illust_bookmark_delete`
* 认证：需 `access_token`
* 返回：站点 JSON（P 源码未声明成功键）

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_id` | 数字串 | 作品编号（进表单正文） | 必填 | `client.app_illust_bookmark_delete('149040133')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
# 本库不调用写方法
client.app_illust_bookmark_delete('149040133')
# 真实 URL：POST https://app-api.pixiv.net/v1/illust/bookmark/delete
# 表单正文：illust_id=149040133
```

#### app_user_follow_add

给什么：`app_user_follow_add(user_id, **attributes)`。关注一个用户。

* 路由：`POST v1/user/follow/add` → `https://app-api.pixiv.net/v1/user/follow/add`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_follow_add`
* 认证：需 `access_token`
* 返回：站点 JSON（P 源码未声明成功键）

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号（进表单正文） | 必填 | `client.app_user_follow_add('27517')` |
| `restrict` | `public`（P 源码自用值；其它取值 P/Z 未给） | 关注可见范围 | 未规定（P 源码常自带 `public`） | `client.app_user_follow_add('27517', restrict='public')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
# 本库不调用写方法
client.app_user_follow_add('27517', restrict='public')
# 真实 URL：POST https://app-api.pixiv.net/v1/user/follow/add
# 表单正文：user_id=27517&restrict=public
```

#### app_user_follow_delete

给什么：`app_user_follow_delete(user_id, **attributes)`。取关一个用户。

* 路由：`POST v1/user/follow/delete` → `https://app-api.pixiv.net/v1/user/follow/delete`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_follow_delete`
* 认证：需 `access_token`
* 返回：站点 JSON（P 源码未声明成功键）

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 数字串 | 用户编号（进表单正文） | 必填 | `client.app_user_follow_delete('27517')` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
# 本库不调用写方法
client.app_user_follow_delete('27517')
# 真实 URL：POST https://app-api.pixiv.net/v1/user/follow/delete
# 表单正文：user_id=27517
```

#### app_user_edit_ai_show_settings

给什么：`app_user_edit_ai_show_settings(show_ai, **attributes)`。开关是否显示 AI 生成作品。

* 路由：`POST v1/user/ai-show-settings/edit` → `https://app-api.pixiv.net/v1/user/ai-show-settings/edit`
* 来源：**P** `pixivpy3/aapi.py::AppPixivAPI.user_edit_ai_show_settings`
* 认证：需 `access_token`
* 返回：站点 JSON（P 源码未声明成功键）

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `show_ai` | 布尔 | 是否显示 AI 作品；表单键名 `show_ai`，编码成小写 `true` / `false` | 必填 | `client.app_user_edit_ai_show_settings(True)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
# 本库不调用写方法
client.app_user_edit_ai_show_settings(True)
# 真实 URL：POST https://app-api.pixiv.net/v1/user/ai-show-settings/edit
# 表单正文：show_ai=true
```

#### app_illust_browsing_history_add

给什么：`app_illust_browsing_history_add(illust_ids, **attributes)`。把若干作品加入浏览历史。

* 路由：`POST v2/user/browsing-history/illust/add` → `https://app-api.pixiv.net/v2/user/browsing-history/illust/add`
* 来源：**H**（hanshsieh 第三方 OpenAPI `/v2/user/browsing-history/illust/add`）
* 认证：来源声称需 `access_token`（未实测）
* 返回：**H 声明响应是 JSON `{}`（空对象）**；本库不执行、不臆造别的成功键。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `illust_ids` | 列表 | 作品编号列表；表单编码成重复的 `illust_ids[]=` | 必填 | `client.app_illust_browsing_history_add(['149040133'])` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
# 本库不调用写方法
client.app_illust_browsing_history_add(['149040133'])
# 真实 URL：POST https://app-api.pixiv.net/v2/user/browsing-history/illust/add
# 表单正文：illust_ids[]=149040133
```

---

### 应用信息与其它（3 个方法）

#### app_application_info

给什么：`app_application_info(**params)`。无参数，返回 Android 客户端自身的最新版本与更新信息。**这是匿名可读的成功路由。**

* 路由：`GET v1/application-info/android` → `https://app-api.pixiv.net/v1/application-info/android`
* 来源：**Z**（ZipFile 抓包 `/v1/application-info/android`，标注 no auth needed）+ **L**（本轮匿名 200 成功）
* 认证：**不需要 token**

返回 `{"application_info": {...}}`。**L** 实测 `GET https://app-api.pixiv.net/v1/application-info/android` → `200 application/json`，键 `application_info`，其中含 `latest_version`（实测 `"6.66.1"`）、`update_required`（`true`）、`update_available`（`true`）、`update_message`（一段日文）、`store_url`（`"http://play.google.com/store/apps/details?id=jp.pxv.android"`），以及 `notice_exists`、`notice_id`、`notice_important`、`notice_message`。取值都是当次快照。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `**params` | 任意名字 | 原样进查询串；Z 未给这条路由任何查询参数 | 不传即不加 | — |

```python
from anybooru import Pixiv

client = Pixiv('pixiv')                       # 匿名即可，不需要 token
info = client.app_application_info()
# 真实 URL：GET https://app-api.pixiv.net/v1/application-info/android
# 实测：200 application/json，键 application_info
print(info['application_info']['latest_version'], info['application_info']['update_required'])
print(info['application_info']['store_url'])
```

#### app_emoji

给什么：`app_emoji(**params)`。无参数，返回站点表情列表。**这是匿名可读的成功路由。**

* 路由：`GET v1/emoji` → `https://app-api.pixiv.net/v1/emoji`
* 来源：**Z**（ZipFile 抓包 `/v1/emoji`，标注 no auth needed）+ **L**（本轮匿名 200 成功）
* 认证：**不需要 token**

返回 `{"emoji_definitions": [...]}`；每项含 `id`、`slug`、`image_url_medium`。**L** 实测 `GET https://app-api.pixiv.net/v1/emoji` → `200 application/json`，键 `emoji_definitions`，首项 `id` `101`、`slug` `"normal"`、`image_url_medium` `"https://s.pximg.net/common/images/emoji/128x128/101_128x128.png"`；地址是原样字符串，本库不下载。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `**params` | 任意名字 | 原样进查询串；Z 未给这条路由任何查询参数 | 不传即不加 | — |

```python
from anybooru import Pixiv

client = Pixiv('pixiv')                       # 匿名即可，不需要 token
result = client.app_emoji()
# 真实 URL：GET https://app-api.pixiv.net/v1/emoji
# 实测：200 application/json，键 emoji_definitions
for emoji in result['emoji_definitions']:
    print(emoji['id'], emoji['slug'], emoji['image_url_medium'])
```

#### app_spotlight_articles

给什么：`app_spotlight_articles(**params)`。返回特辑（spotlight）文章列表（无必填值）。

* 路由：`GET v1/spotlight/articles` → `https://app-api.pixiv.net/v1/spotlight/articles`
* 来源：**Z**（ZipFile 抓包 `/v1/spotlight/articles`，需 auth）+ **L（拒绝证据，非成功）**：匿名 `GET https://app-api.pixiv.net/v1/spotlight/articles?category=all&offset=0` → `400 application/json`，正文同为 `{"error": {"user_message": "", "message": "Error occurred at the OAuth process. ... invalid_request", "reason": "", "user_message_details": {}}}`
* 认证：需 `access_token`

返回 `{"spotlight_articles": [...], "next_url": "..."}`。成功响应字段只有 Z 依据，**未实测**。

| 参数 | 取值 | 含义 | 不传时 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `category` | `all` / `manga` | 特辑分类 | 未规定 | `client.app_spotlight_articles(category='all')` |
| `offset` | 整数，从 `0` 起 | 偏移量 | 未规定 | `client.app_spotlight_articles(category='all', offset=20)` |

```python
from anybooru import Pixiv

client = Pixiv('pixiv', access_token='<你的 access token>')
page = client.app_spotlight_articles(category='all')
# 真实 URL：GET https://app-api.pixiv.net/v1/spotlight/articles?category=all
# 匿名实测：400（拒绝）；带 token 的成功响应未实测
print(page['spotlight_articles'], page['next_url'])
```

---

### 边界与未实测（App 面）

本节把 App 面的权限边界、未实测项与排除项集中在这里，方法小节不再重复。

**凭据与权限边界**

* App 面**来源声称**需要 `access_token` 的方法共 **57 个**（全部除匿名的 `app_application_info()`、`app_emoji()` 之外）；这是各来源的声明，不是逐条实测结论。`access_token` 是调用者**已经持有**的值，通过构造参数 `access_token=` 或包内配置 `sites.pixiv.access_token` 传入；非空时每个 App 请求带 `Authorization: Bearer <access_token>`。
* 本类**没有登录、没有 OAuth2 / PKCE 换 token、没有 refresh token、没有自动获取 Cookie**。它只保存你给的值：token 被拒或过期，得到的是站点自己的响应。**本页不引导你去注册或申请任何凭据**——需要 token 的方法只说明它要什么头，值从哪来由调用者自行决定。
* 示例里的 `'<你的 access token>'` 是占位串，换成你已有的 token 才能跑通；`Pixiv('pixiv')` 不带 token 时是匿名，只有 `app_application_info()` / `app_emoji()` 会成功，其它 App 方法会被站点拒绝。
* **不发** `x-client-time` / `x-client-hash`（pixivpy 的普通 API 函数未注入这两个头；凭据成功路径与头的实际需求未实测），**不伪造** App 专用 User-Agent / `app-os` 头，**不注入**任何 pixivpy 默认参数。

**实测覆盖（L）**

* 成功：只有两条匿名 200——`app_application_info()`（`v1/application-info/android`）与 `app_emoji()`（`v1/emoji`）。上面已给状态码与字段。
* 拒绝（**不是成功**）：`app_illust_detail()`（`v1/illust/detail?illust_id=59580629`）、`app_novel_detail()`（`v2/novel/detail?novel_id=11165421`）、`app_spotlight_articles()`（`v1/spotlight/articles?category=all&offset=0`）、`app_novel_ranking()`（`v1/novel/ranking?mode=day`）、`app_illust_comment_replies()`（`v1/illust/comment/replies?comment_id=233757844`）、`app_user_state()`（`v1/user/me/state`）、`app_illust_series()`（`v1/illust/series?illust_series_id=257832&offset=0`）、`app_illust_comments_v3()`（`v3/illust/comments?illust_id=149040133`）八条匿名调用都返回 `400 application/json`，错误体是 `{"error": {"message": "Error occurred at the OAuth process. ... invalid_request", ...}}`。它只证明“无 token 被拒”，不证明成功时返回什么。
* 来源声称需要 `access_token` 的方法共 **57 个**（59 总数减 2 个匿名可读的 `app_application_info()`、`app_emoji()`）。这 57 个里，本轮发起过请求的有 8 个——`app_illust_detail()`、`app_novel_detail()`、`app_spotlight_articles()`、`app_novel_ranking()`、`app_illust_comment_replies()`、`app_user_state()`、`app_illust_series()`、`app_illust_comments_v3()`，各得一次匿名 400 拒绝；**其余 49 个方法本轮没有发起过任何请求**。这 49 个方法的路由、参数与返回字段来自 **P/Z/H/G 混合**第三方来源（P = 当前 pixivpy 源码，Z = 2016 年抓包，H = 第三方 OpenAPI，G = gallery-dl 源码），**不是 pixiv 官方服务端规范**；成功响应里字段是否真的出现，本页不保证，标什么来源即“该来源这么写”。

**已排除的 App 路由**

* `v1/illust/recommended-nologin` 与 `v1/novel/recommended-nologin`：本轮在无 token、配置的 User-Agent 下实测都返回 **404**，错误体 `{"error": {"user_message": "指定されたエンドポイントは存在しません", ...}}`。这是**该次请求下**的观察，不推广成“服务端永远没有这条路由”，所以本库不封装它们。
* `v1/novel/markers`（曾考虑为 `app_novel_markers`）与 `v2/illust/comments`（曾考虑为 `app_illust_comments_v2`）：本轮匿名实测分别返回 **404**——`v1/novel/markers` 是 `{"error": {"user_message": "指定されたエンドポイントは存在しません", ...}}`，`v2/illust/comments?illust_id=149040133` 是 `{}`（`application/json`，无 `charset`）。因此这两条**不作为原生方法封装**。同样是**该次请求下**的观察，不推广成“服务端永远没有这两条路由”。
* `v1/novel/text`（以及旧的 `novel_text` 包装）：pixivpy 把它标注为已不存在、正文改走 `app_webview_novel()` 的 webview 页面；但 gallery-dl 源码里仍保留 `v1/novel/text`，本库不据此断言服务端绝对下线，只跟随 pixivpy 的选择不封装。
* `v1/novel/series`：本库随当前 pixivpy 选用 `v2/novel/series`（`app_novel_series()`）；旧第三方文档与 gallery-dl 里给的 `v1/novel/series` 本库未选、未实测，也不断言服务端已迁移。
* 旧 public-api / works API、OAuth 登录流程、上传、媒体下载与 CDN（`i.pximg.net`）、Fanbox / Sketch / 约稿 / 账号后台：都不在 App 作品 API 范围内，本库不封装。
* `v1/walkthrough/illusts` 与 `v1/walkthrough/renewal-description`：引导页 / 更新说明用途，不在作品 API 范围，本库不封装。
* 来源里**没有**可依据路由的 App 写操作（小说收藏增删、评论写、小说正文/标记写）不臆造对称 API；对应的收藏/评论交互由 Web 面方法承接。
* `app_webview_novel()` 返回 HTML，本库不解析；从页面里抽 `WebviewNovel` 元数据与小说正文是调用者的事。

**清单外的方法**

* 上述 59 条之外没有原生方法。要调别的站点相对路径，用通用入口 `client.request('GET', path, api='app', params=...)`，行为与原生方法一致（不改名、不补默认、不跟随 `next_url`）。

