# Sakuria 客户端用法

`Sakuria` 访问 Pixiv 第三方镜像站 Sakuria 的 JSON API，不是 booru 客户端的别名。
本类使用 `illust_search(q=...)` 等独立方法，不把 booru 的 `tags`、`rating:` 或帖子字段转换过来。

站点有多个主机，客户端只对**公开 API 主机** `https://sakuria-api.syarolia.com` 说话
（包内 `sites.sakuria` 的 `url` 就是它）：

| 主机 | 角色 | 本轮是否请求 |
| :--- | :--- | :--- |
| `https://sakuria-api.syarolia.com` | 公开 API（国际加速线路） | **是**，本客户端全部路由都在这里 |
| `https://sakuria.syarolia.com` | Web 前端 | 未请求（输入文档称被 Cloudflare 挑战挡住） |
| `https://sakuria-app-api.syarolia.com` | Sakuria+ 会员线路 | 未请求（输入文档称无会员态返回 `401`） |
| `https://sakuria-pximg.syarolia.com`、`https://sakuria-pximg-pro.syarolia.com` | 图片 turbo / pro 代理 | 未请求（输入文档称缺图片 token 返回 `401`） |

**依据只有匿名响应**：没有可引用的上游引擎源码、官方 API 页面或 OpenAPI。
本轮直接 HTTP 观察覆盖 27 个公共 JSON 路由及 `/me/likes` 的匿名拒绝分支；
这不等于 44 个 Python 包装方法逐个运行过。实际脚本、请求 URL 与范围见
[验证记录](verification.md#sakuria匿名只读实测2026-09-19)。

客户端一共 **44 个原生方法**：**27 个匿名只读方法**（站点与配置、插画、用户、小说、系列、
特辑、标签）加 **17 个 `/me/*` 账号路由透传**（需要登录），另有一个通用入口 `request()`。
逐条参数与返回字段见[方法参考](sakuria-api.md)，「我要做什么 → 用哪个方法」与 44 方法完整索引见
[能力入口](sakuria-capabilities.md)。**输入文档里那些本轮没测到的候选说法**（参数取值枚举、
默认值、上限、错误码全集、媒体占位图等）不写进本页正文，集中列在
[依据与差异的边界清单](sakuria-contract-notes.md#边界与未实测)。

## 第一次调用：站点计数与一页插画搜索

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    stats = client.stats()
    # GET https://sakuria-api.syarolia.com/stats
    # 200 application/json：
    # {"newToday": 30, "totalIllusts": 85, "totalCreators": 197, "totalUsers": 113}
    print(stats['totalIllusts'], stats['totalCreators'], stats['totalUsers'])

    page = client.illust_search(q='blue', page=1, size=24)
    # GET https://sakuria-api.syarolia.com/search/illust?q=blue&page=1&size=24
    # 200 application/json，信封键是 items/page/pageSize/total/totalPages/hasMore/nextPage/hiddenCount：
    # 本轮实测值是 items 29 条、page 1、pageSize 24、total 48、totalPages 4、
    # hasMore true、nextPage 4、hiddenCount 61
    for illust in page['items']:
        print(illust['id'], illust['title'], illust['urls']['regular'])
    print(client.last_call['status_code'], client.last_call['url'])
```

`stats` 的计数是站点自述、随实时数据变动；`search/illust` 的 `page=2/3` 本轮分别返回
`items` 24 条与 33 条，`total` 变成 72/96、`totalPages` 与 `nextPage` 变成 4/6——
**三页并非都恰好 24 条**，所以不要用 `size` 或 `totalPages` 推算条数与页数（见文末“实测下定的行为”）。

## 第二次调用：详情是裸对象，评论与回复各自一条路由

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    illust = client.illust_show(70937229)
    # GET https://sakuria-api.syarolia.com/illust/70937229
    # 200 application/json，**裸对象、没有信封**，键为 id/title/type/pages/description/urls/
    # author/tags/stats/publishedAt/publishedDays/isAi/isR18/xRestrict/sl；
    # 本轮实测：title "翔鶴"、type "illust"、pages 1、isAi false、isR18 false、
    # xRestrict 0、sl 2、tags 9 条、urls.w/h 为 1200/675，pages=1 因此没有 pageUrls 键
    print(illust['author']['id'], illust['stats']['views'], len(illust['tags']))

    comments = client.illust_comments(70937229, page=1, size=2)
    # GET https://sakuria-api.syarolia.com/illust/70937229/comments?page=1&size=2
    # 200，信封只有 {"items": [评论, …], "hasMore": true}；本轮 2 条，
    # 评论键为 id/author/text/repliesCount/likes/createdAt/timeLabel，
    # author 是 {id, name, handle, accent, avatar}（没有 stats）
    for comment in comments['items']:
        print(comment['id'], comment['author']['handle'], comment['repliesCount'])
        if comment['repliesCount']:
            replies = client.illust_comment_replies(70937229, comment['id'])
            # GET https://sakuria-api.syarolia.com/illust/70937229/comments/<该评论 id>/replies
            # 200，信封只有 {"items": [回复, …]}，没有 hasMore
            for reply in replies['items']:
                print('  reply', reply['id'], reply['text'][:20])
```

`/illust/{id}`、`/novels/{id}`、`/series/{id}`、`/users/{id}`、`/spotlight/{id}` 都直接返回资源对象，
不把该资源再包进一个外层键；其中系列对象自身仍有 `items` 作品数组。
回复与相关插画、相关用户返回 `{"items": [...]}`；`comment_id` 用评论对象的 `id`，不是回复数。

## 构造与配置

签名：`Sakuria(site_name=None, site_url=None, access_token=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 中的键名 | 不选命名站点，需显式给 `site_url` | `Sakuria('sakuria')` |
| `site_url` | 字符串，站点根地址，必须是 API 主机 | 读取所选站点的 `url` | `Sakuria(site_url='https://sakuria-api.syarolia.com')` |
| `access_token` | 字符串，令牌；**非空**才随请求发送 `Authorization: Bearer <token>`，`''` 表示明确不带凭据 | 有站点名时读取其 `access_token`（包内为空），否则为 `None` | `Sakuria('sakuria', access_token='')` |
| `proxies` | 字典，按 `http` / `https` 指定代理，`{}` 表示直连 | 使用 `request.proxies`，包内为 `{}`；不读环境变量 | `Sakuria('sakuria', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json`；指定文件不存在直接抛错 | `Sakuria('sakuria', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout`，包内为 `30` | `Sakuria('sakuria', timeout=10)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent`，包内为 `Anybooru/0.1.0.dev1` | `Sakuria('sakuria', user_agent='MyBooruApp/1.0')` |

**没有 `username` / `password`**：本类不做登录，也没有登录、注册、刷新令牌的方法。
包内站点条目只有两个字段：

```json
{"sakuria": {"url": "https://sakuria-api.syarolia.com", "access_token": ""}}
```

`access_token` 的三种写法要分清楚：不传（`None`）**回落**到站点条目的值；显式传 `''`
是“明确不带凭据”，不看配置里的令牌；只有非空字符串才会加上 `Authorization: Bearer` 头。
复制完整配置的方法见[配置指南](configuration.md)。用完记得 `client.close()`，或用 `with` 语句块。

## 认证：匿名读 27 条，其余靠你自带的令牌

* **27 个公共 JSON 路由的样本均匿名成功**，没有带 `Authorization` 头；
  这不包含付费搜索参数的成功路径，也不意味着每个包装方法都真跑过。
* **17 个 `/me/*` 方法需要登录态**，本轮只请求过其中一个：`GET /me/likes` 不带
  `x-sakuria-data-contract` 时返回 `426 {"error":"upgrade_required","requiredDataContract":2}`，
  加上 `x-sakuria-data-contract: 2` 之后变成
  `401 {"error":"sakuria_session_required"}`。其余 16 条的请求、响应与返回结构**本轮没有样本**，
  逐条状态见[账号方法与访问面](sakuria-contract-notes.md#账号方法与访问面)，不要把它们当匿名探针。
* **客户端不发任何隐式头**（除共享的 User-Agent / Accept 与非空令牌时的 `Authorization`）：
  要带 `x-sakuria-data-contract` 这类头就自己写进 `headers`。
* 本库**不提供**登录、刷新、登出方法，也不索要账号；自己拿到令牌后可以直接构造
  `Sakuria('sakuria', access_token='…')`（这里省略真实令牌）。登录/注册端点的位置、
  令牌的获取与失效行为都属未实测项（见文末边界）。

## 通用入口 `request()`

签名：`request(method, path, *, params=None, headers=None)`。

它与 44 个原生方法走同一条通路，只是路径与动词由你给全：

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串；本轮 44 个原生方法与探测全部用 `'GET'` | 必填 | `client.request('GET', 'stats')` |
| `path` | 站点相对路径，不带主机；前导 `/` 会去掉，尾部 `/` 保留，不补版本前缀 | 必填 | `client.request('GET', 'illust/70937229/comments', params={'page': 1, 'size': 2})` |
| `params` | 查询参数字典；`None` 值不发送，布尔写成小写 | `None`，不发查询参数 | `client.request('GET', 'search/illust', params={'q': 'blue', 'size': 24})` |
| `headers` | 额外请求头字典，只作用于本次请求 | `None`，不附加 | `client.request('GET', 'me/likes', headers={'x-sakuria-data-contract': '2'})` |

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    page = client.request('GET', 'search/illust', params={'q': 'blue', 'page': 2, 'size': 24})
    # GET https://sakuria-api.syarolia.com/search/illust?q=blue&page=2&size=24
    print(page['page'], len(page['items']), page['total'])
    print(client.last_call['status_code'], client.last_call['url'])
```

`path` 里的资源编号不做本地校验，标签名照原样送（`tag_illusts` 会把整个标签段做 URL 编码）。
客户端**不**加 `/api` 或版本前缀、不补 `.json`、不拆信封、不改字段名、不合并分页、
不重试、不钳位任何参数、不做本地参数校验，也不加隐式 Sakuria 头。共享 requests 会话默认跟随重定向；本轮冒烟、示例和直接探测显式关闭了跟随。

## 返回值与 last_call

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | 解析后的 Python 对象，一层都不拆：列表接口是 `{"items", "page", "pageSize", …}`，详情接口是裸对象 |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`、`data`；本轮的样本是 `400 {"error":"invalid id"}`、`400 {"error":"筛选参数无效","code":"invalid_search_filter","field":"size"}`、`401 {"error":"sakuria_session_required"}`、`401 {"error":"高级筛选需要 Sakuria+","code":"auth_required","feature":"advanced_search"}`、`404 {"error":"illust not found"}`、`426 {"error":"upgrade_required","requiredDataContract":2}`、`503 {"error":"upstream temporarily unavailable","retryable":true}` |
| 2xx 但正文为空 | 返回 `None`（空响应不当错误处理） |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError` |
| 网络错误 | requests 自己的异常原样抛出，没有重试 |

每次收到响应后 `client.last_call` 是最近一次的情况：`API`（本次调用的路由）、`url`（含查询串的最终地址）、
`status_code`、`status`、`headers`。核对“参数发成什么样”看它：

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    client.illust_related(128641898, size=2)
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://sakuria-api.syarolia.com/illust/128641898/related?size=2
```

响应头里每个响应都带 `x-sakuria-request-id`，`Access-Control-Expose-Headers` 列出
`ETag,X-Sakuria-App-Attest-Policy,X-Sakuria-Request-ID`。详见 [errors.md](errors.md)。

## 媒体地址：只给地址，拼接是你的事

**本库不下载媒体**，不提供 `image_bytes` 之类的下载方法，也不替你拼地址。
下面的插画样本中 `urls.*` 是以 `/` 开头的相对路径，拼上 `client.site_url` 即为完整 URL：

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    illust = client.illust_show(70937229)
    base = client.site_url
    for size_name in ('thumb', 'small', 'regular', 'original'):
        print(size_name, base + illust['urls'][size_name])
    if 'pageUrls' in illust:                      # 只有 pages > 1 才有这个键
        for page in illust['pageUrls']:
            print(page['w'], page['h'], base + page['original'])
```

三条使用规则：

1. **先看是不是以 `/` 开头再拼主机**。本轮见到的相对路径不全是 `/img/`：插画与小说封面是
   `/img/c/…`、`/img/img-original/…`、`/img/c/240x480_80/novel-cover-master/…`，
   而特辑详情的 `cover` 是 `/p/embed.pixiv.net/pixivision/zh/a/11971/ogimage.jpg`；
   同一次响应里 `articleUrl` 则是绝对地址。**绝对地址不要再拼主机**。
2. **地址里的尺寸档位照抄，不要自己拼**。`urls` 与 `pageUrls[]` 是同一套键
   （`thumb`/`small`/`regular`/`original` 加 `w`/`h`），`pages=1` 时没有 `pageUrls`；
   本轮没有比较过不同 `w`/`h` 的地址模板，也没有请求过任何图片字节。
3. **输入文档说 `/img/…` 缺文件时返回 HTTP 200 的占位 SVG（`Content-Type: image/svg+xml`）
   而不是 `404`**；按用户要求把这条写在这里提醒，但**本轮没有复测、也没有下载任何媒体**，
   真要用图时请自己检查 `Content-Type`。

## 实测下定的行为

下面每一条都有本轮 54 次匿名请求里的具体样本支撑；其它没有样本的说法都推到文末边界。

1. **列表信封**：本轮出现过的键是 `items`、`page`、`pageSize`、`total`、`totalPages`、`hasMore`、
   `nextPage`、`hiddenCount`；评论是 `{items, hasMore}`，回复、相关插画、相关用户只有 `{items}`，
   用户搜索只有 `{items, total}`，用户收藏是 `{items, pageSize, hasMore, nextCursor, hiddenCount}`。
2. **`total` / `totalPages` / `nextPage` 不能用来导航**：`/search/illust?q=blue&size=24` 的
   page1/2/3 分别给出 `total` 48/72/96、`totalPages` 4/4/6、`nextPage` 4/4/6，而 `page` 自己
   是 1/2/3——`nextPage` 既不等于相邻页码，也不是总数；`total` 也不等于累计条数。
3. **相邻页会重叠**：同一批请求里 page1 与 page2 有 24 个相同 `id`（page1 共 29 条）、
   page2 与 page3 有 10 个相同 `id`（page2 共 24 条）。翻页要自己按 `id` 去重。
4. **`items` 条数不等于请求的 `size`**：`size=1` 回 5 条、`size=24` 回 29/24/33 条、`size=48` 回 39 条；
   `size=1` 与 `size=48` 被接受，`size=0` 与 `size=49` 得到
   `400 {"error":"筛选参数无效","code":"invalid_search_filter","field":"size"}`。
   不要用 `len(items)` 反推 `size`，也不要把 48 当成实际上限。
5. **只有部分参数会被校验**：`page=0`、`sort=__invalid__`、`mode=text` 各得到 `400` 且带 `field`；
   而 `limit=__invalid__` 仍返回 `200`，ID 顺序与分页字段与不带该参数的基线相同——
   本轮**只证了 `limit` 这一个取值被忽略**，不要推广到其它参数名。
6. **详情是裸对象**（`/illust/{id}`、`/novels/{id}`、`/series/{id}`、`/users/{id}`、`/spotlight/{id}`），
   而 `/series/{id}` 自身仍带 `items` 作品数组。
7. **用户搜索的 `total` 是「本页条数」**：`q=mika` 的 page1/2/3 分别是 6/12/21 条，
   `total` 与 `items` 条数逐页相等，且各页 `id` 互不重叠。它的信封没有 `hasMore`/`nextPage`，
   所以这个端点**没有可用的翻页判据**。
8. **用户收藏的 `page=1` 与 `page=2` 返回完全相同的 JSON**（19 项、`nextCursor` 同为
   `"9175901406"`、`hasMore` 为 true）；本轮只证明这两个取值没有推进，其它分页写法没有样本。
9. **用户关注者两页都是空 `items`**，`page` 分别回显 1 与 2、`hasMore` 为 false；
   本轮**不能**据此说分页无效或功能未实现，非空 item 的结构也没有样本。
10. **`/tags/{tag}` 与 `/search/illust` 不是同一批结果**：`/tags/blue` 与
    `/search/illust?q=blue` 在同 `page=1&size=24` 下分别是 25 与 29 条、交集 25，两次请求不是同一时刻，
   本轮没有定性差异原因；而 `/tags/search?q=blue&size=2` 与不带 `q` 的完整 JSON 相同（各 11 项），
    在这个取值下 `q` 确实没影响。
11. **系列编号不要混用**：`series_show(198059)` 返回 30 项、`total=219`；
    输入资料中另一个编号 `12064` 返回空 `items`、`total=7`，不能仅看 `total` 推断本页内容。
12. **特辑**：列表一页 20 项而信封写 `pageSize` 12、`hasMore` true；详情 `11971` 有 19 篇
    `articles`、`works` 为空、`relatedLatest`/`relatedRecommend` 的 `items` 也为空；
    `/spotlight/0` 得到 `503 {"error":"upstream temporarily unavailable","retryable":true}`。
13. **`nextCursor` 会泄漏上游地址**：`/users/3182410/novels` 的 `nextCursor` 是
    `https://app-api.pixiv.net/v1/user/novels?user_id=3182410&offset=30`，它**不是本站的游标**。
14. **计数类字段不必为 0**：`/users/129030276` 的 `stats` 本轮是
    `{"followers": 0, "following": 11, "works": 8, "totalLikes": 0, "totalBookmarks": 13}`。
15. **会员面**：插画搜索 `type=illust` 与小说搜索 `ai=exclude` 本轮都得到
    `401 {"error":"高级筛选需要 Sakuria+","code":"auth_required","feature":"advanced_search"}`。
16. **小说详情里 `text` 与 `document.text` 不一致**：本轮 `novel_show(29167620)` 顶层 `text` 是**空串**，
    而 `document.text` 是 4 行 `[uploadedimage:25719695]` 这样的上传图标记；`document.uploadedImages`
    有 4 条、`pixivImages` 为空。输入文档说两者“内容相同”**被本轮推翻**，不要按那个假设取正文。

## 可运行示例

两个脚本都匿名只读，参数全部来自配置的 `examples.sakuria` 段
（`site='sakuria'`、`illust_query={'q': 'blue', 'size': 2, 'sort': 'new'}`、`pages=[1, 2]`、
`illust_id=70937229`、`comment_query={'page': 1, 'size': 2}`、`pause_seconds=1.2`），
脚本里没有硬编码站点或查询值，也不发任何 `/me/*` 请求：

```bash
python examples/sakuria/search_illusts.py
python examples/sakuria/browse_resources.py
```

* `search_illusts.py`：`illust_search(**illust_query, page=…)` 最多走两页，**手动递增 `page`**，
  遇 `hasMore=false` 或 `nextPage=null` 就停（不用数值 `nextPage` 跳页），按 `id` 去重展示。
* `browse_resources.py`：三次调用——`illust_show(配置的 id)`、`illust_comments(配置的 id, **comment_query)`、
  再用详情里的 `author['id']` 调 `user_show`；打印每次的真实 URL、状态码、`Content-Type` 与关键字段。

两个脚本都不下载媒体、不跟随跳转、不重试、请求之间按 `pause_seconds` 停顿。
轻量冒烟 `test/sakuria.py`（匿名、只读、最多 10 次请求、不 mock、不进 CI）用
`python test/sakuria.py --config <你的配置文件>` 运行，参数取自 `smoke.sakuria`。

三者的执行情况（逐条 URL、状态码与输出摘要见
[验证记录](verification.md#sakuria匿名只读实测2026-09-19)）：

* 冒烟：**10 次请求、`passed 10 / failed 0`、退出码 0**，其中 8 次 `200`，
  另有 `illust_show(0)` 的 `404` 与 `size=49` 的 `400` 两条预期错误路径。
* `search_illusts.py`：**2 次请求（`page=1`、`page=2`）全部 `200`、退出码 0**。
* `browse_resources.py`：**3 次请求（`illust_show`、`illust_comments`、详情作者的 `user_show`）
  全部 `200`、退出码 0**。

这三个脚本覆盖的是用法路径，不是本站全部 44 个方法；端点级的实测范围见
[依据与差异](sakuria-contract-notes.md#本轮请求覆盖)。

## 边界与未实测

输入文档（T）里**本轮没有测到**的说法集中在这里，不要当契约用：

* **未请求的面**：媒体字节（一次都没下载）、`sakuria-app-api`/`sakuria-pximg*` 三个其它主机、
  Web 前端与登录/注册端点、任何写接口、以及 `/me/*` 里除 `me_likes` 之外的 16 条。
* **`/me/*` 返回结构**：17 条全部未知；`me_likes` 只有 `426`（无契约头）与 `401`（带契约头）两个样本。
* **媒体占位图**：输入文档称 `/img/…` 缺文件返回 `200` + `image/svg+xml` 占位图、查询参数被忽略、
  两个 pximg 主机需要图片 token——**均未复测**。
* **参数取值与默认值**：`size` 的可用范围与默认值、`sort`/`type`/`ai`/`mode`/`ratio` 的完整枚举、
  搜索与列表的其它默认页大小、`lang` 与未知值的回退、`page` 的实际上界，都只有输入文档说法；
  本轮只测了 `size` 的 0/1/24/48/49、`page` 的 0、`sort` 的 `popular`/非法值、`mode=text`、
  `limit=__invalid__` 这几个点。
* **错误码全集**：本轮见到的只有 `400`/`401`/`404`/`426`/`503` 几种形态；
  输入文档列的 `403`、`invalid user id`/`invalid novel id` 之类的逐资源措辞、`Not Found` 路由错误体
  本轮都没有样本。
* **末页判据**：`hasMore=false` 只在空集合样本上出现过（关注者、用户系列、小说评论、小说相关、
  小说系列 id 的系列）；**翻到有数据的末页**、`nextPage=null` 本轮都没跑到，
  所以“据此判末尾”仍是输入文档的候选说法。
* **字段语义**：`sl`（本轮样本恒 2）的含义、`hiddenCount` 的过滤规则、标签 `alt` 的取余规律、
  `translated` 缺失时整键省略、`stats` 常为 0、ugoira 没有帧信息、`pageUrls` 与 `urls` 的关系，
  都只有输入文档依据。小说正文：本轮详情顶层 `text` 是空串、`document.text` 是上传图标记
  （两者**不相同**，输入文档的说法被推翻），**其它小说的正文形态与插图映射规则仍未实测**。
* **媒体与参数的外推**：不要根据本轮样本推断未测尺寸档位、绝对外链头像形态、`r18`/`safe` 等参数的
  忽略清单、或“同类对象字段一致”。
* **限流**：本轮没有观察到任何 `RateLimit-*` / `Retry-After` 响应头，也没有公开配额说明；
  不要假设有配额，客户端也不做节流与退避。

继续阅读：[方法参考](sakuria-api.md) · [能力入口](sakuria-capabilities.md) ·
[依据与差异](sakuria-contract-notes.md) · [错误处理](errors.md)。
