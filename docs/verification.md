# 验证记录

这里记录真实执行的命令、请求和结果；方法怎么调用见[方法参考](index.md#按家族选文档)，上游依据见各家族的契约审计附注。
所有数据都是当时的快照，不保证再次请求得到相同 ID、计数或排名。证据文件当时保存在维护者本机临时目录，不随仓库分发；已删除的脚本只在[历史记录](#历史记录)中列出。

改名前的实测记录保留当时的 `pybooru` / `pybooru.json` / `Pybooru*` 包名、配置名与异常名；
改名后对应 `anybooru` / `anybooru.json` / `Anybooru*`。原命令和观测结果不回写，改名后的复跑结果另列于文末。

## 执行环境与批次

| 批次 | 时间、站点与身份 | 方式 / 证据 | 执行结果 |
| :--- | :--- | :--- | :--- |
| D1：Danbooru 匿名读取 | 2026-09-14T16:14:23Z–16:14:44Z；`https://danbooru.donmai.us`，`sites.danbooru`，username/api_key 均空 | 维护者本机一次性脚本；证据保存请求与响应原文 | 15 次：12×200、404/410/422 各一次；间隔 1 秒 |
| D2：画师重定向 | 同站、匿名 | 同一脚本；结果见[Danbooru 表](#danbooru匿名只读验证) | 跟随 302，最终 200 JSON |
| M1：Moebooru 首次读取 | 2026-09-15；`https://yande.re`，`sites.yandere`，username/password 均空 | 维护者本机一次性脚本 | 15×200 后一次断连，退出 1；证据仅为实际终端输出摘要，不是完整原始响应 |
| M2：Moebooru 续跑 | 2026-09-14T17:48:23Z–17:48:27Z，同站 | 同一脚本的续跑部分 | 200/404/400 各一次，退出 0；逐次保存 URL、状态、头、JSON/正文和异常类型 |
| M3：突发与中断复查 | 2026-09-15，同站匿名 | 见[突发与中断复查](#突发与中断复查) | 完整序列 17 次调用退出 0；连续 10 次 `GET /post.json?limit=1` 全部 200，无中断 |
| M4：候选站点复核 | 2026-09-15，全部匿名 GET | 维护者本机脚本；证据文件 | 四域名各 12 个只读端点全部 200 JSON，差异见[站点复核](#站点复核) |
| S1：Serika 客户端示例 | 2026-09-15；`https://serika.art`，`sites.serika.api_key` 为空 | 维护者本机 runner 依次运行三个现有示例 | 8×200；三进程均退出 0、stderr 为空；临时 runner、片段、stdout/stderr/returncode 证据转录后已删除 |
| D3：Danbooru 候选读路径复核 | 2026-09-15，匿名 GET | 维护者本机脚本；证据文件 | `danbooru.donmai.us` 的 9 个 REST 读路径（含 `users.json` / `autocomplete.json`）全 `200` |
| D4：Safebooru 客户端复测 | 2026-09-15，匿名 GET | 维护者本机脚本；证据文件 | 16 个客户端方法全 `200`，返回形态与 `danbooru.donmai.us` 一致 |
| E1：e621ng 示例与形态复核 | 2026-09-15；`https://e621.net` 与 `https://e926.net`，`sites.e621` / `sites.e926`，username/api_key 均空 | 三个现有示例各站跑一遍 + 一轮返回形态复核；两者都保存逐调用记录 | 37 次匿名 GET：36×200、1×403（`related_tag` 匿名拒绝）；6 条示例命令均退出 0 |

| 共享设置 | 实际值 |
| :--- | :--- |
| D1 参数 | 根 `verification` 段：站点、关键词、样本规模、间隔，以及 `missing_post_id` / `invalid_page` / `invalid_tags` |
| M1/M2 参数 | 根 `verification.moebooru`，间隔 1 秒，无客户端自动重试；续跑没有重跑已成功的 15 次 |
| S1 参数 | 根 `examples.serika`、`verification.serika.scripts`、`verification.serika.pause_seconds=1`；只在示例之间等待，示例内部不额外 sleep / 重试 |
| E1 参数 | 根 `examples.e621`（示例输入）、`verification.e621`（站点列表、脚本、间隔、形态复核输入）；示例之间 sleep 1 秒，库不重试、不做本地分页 |
| 本地导入（Moebooru） | `.venv/Scripts/python.exe -c "import pybooru; from pybooru import Moebooru"`，退出 0 |
| 本地导入（三家族） | `.venv/Scripts/python.exe -c "import pybooru; from pybooru import Serika, Danbooru, Moebooru"`，退出 0，输出 `Serika Danbooru Moebooru` |

## Danbooru：匿名只读验证

D1 的 URL 均以 `https://danbooru.donmai.us` 为基址；具体 ID 来自配置或前一次真实响应。

| 场景与调用 | 请求路径 | HTTP | 真实摘要 |
| :--- | :--- | :--- | :--- |
| `post_list(limit=2)` | `/posts.json?limit=2` | 200 | 2 条 |
| `post_list(tags='rating:g', limit=2)` | `/posts.json?tags=rating%3Ag&limit=2` | 200 | 2 条 |
| `post_show(post_id=...)` | `/posts/<id>.json` | 200 | 单对象，含 `id` / `rating` / `md5` 等 |
| `post_list(page='b12192570', limit=2)` | `/posts.json?page=b12192570&limit=2` | 200 | 2 条，更早的 ID |
| `tag_list(search={'name_matches': 'touhou'}, limit=2)` | `/tags.json?limit=2&search[name_matches]=touhou` | 200 | `touhou`，tag id `29` |
| `artist_list(search={'url_matches': 'https://www.pixiv.net/users/27517', 'is_deleted': False, 'is_banned': False, 'has_tag': True, 'order': 'name'}, limit=2)` | `/artists.json?limit=2&search[url_matches]=...&search[is_deleted]=false&search[is_banned]=false&search[has_tag]=true&search[order]=name` | 200 | 1 条，artist id `8704`，name `fuzichoco` |
| 同一 artist 查询增加 `search['any_name_matches']='fuzichoco'` | 同前路径，加 `search[any_name_matches]=fuzichoco` | 200 | 同一 artist |
| `related_tag(search={'query': 'touhou', 'category': 0, 'order': 'frequency', 'search_sample_size': 1000, 'tag_sample_size': 100}, limit=2)` | `/related_tag.json?limit=2&search[query]=touhou&search[category]=0&...` | 200 | `query` / `post_count` / `tag` / `related_tags`（2 项）/ `wiki_page_tags` |
| `wiki_page_list(search={'title': 'help:api'}, limit=2)` | `/wiki_pages.json?limit=2&search[title]=help%3Aapi` | 200 | 1 条，page id `43568` |
| `wiki_page_show('help:api')` | `/wiki_pages/help%3Aapi.json` | 200 | title `help:api` |
| `comment_list(group_by='comment', limit=2)` | `/comments.json?group_by=comment&limit=2` | 200 | 2 条 |
| `pool_list(limit=2)` | `/pools.json?limit=2` | 200 | 2 条 |
| D2：`artist_show_or_new(name='fuzichoco')` | 重定向终点 `https://danbooru.donmai.us/artists/8704`（无 `.json`） | 302 → 200 | `Content-Type: application/json`，artist `8704`；客户端保留 `Accept: application/json` |

重定向后的格式由目标端点决定；这次已取得 JSON，不把重定向一概视为解析失败。

### Danbooru 错误响应

| 请求 | HTTP | 服务端消息 / 类型 | 客户端结果 |
| :--- | :--- | :--- | :--- |
| `/posts/0.json` | 404 | `That record was not found.` / `ActiveRecord::RecordNotFound` | `PybooruHTTPError` |
| `/posts.json?page=1001&limit=2` | 410 | `You cannot go beyond page 1000.` / `PaginationExtension::PaginationError` | `PybooruHTTPError` |
| `/posts.json?tags=touhou 1girl solo&limit=2` | 422 | `You cannot search for more than 2 tags at a time.` / `PostQuery::TagLimitError` | `PybooruHTTPError` |

三次都保留 `{success: false, error, message, backtrace}` JSON；状态、URL、正文分别由 `.http_code` / `.url` / `.data` 读取，见[错误处理](errors.md)。

## Moebooru：2026-09-15 追加记录

M1 + M2 合计 **19 次尝试：16×200、1×404、1×400、1 次无 HTTP 响应**。基址为 `https://yande.re`。

| 场景与实际调用 | HTTP | 真实摘要 |
| :--- | :--- | :--- |
| `post_list(limit=2)` | 200 | 2 条，首条 ID `1268798` |
| `post_list(tags='rating:s', page=1, limit=2)` | 200 | 2 条，首条 ID `1268790` |
| 同一搜索 `page=2` | 200 | 2 条，首条 ID `1268785`，与第一页不同 |
| `tag_list(name='touhou', limit=2)` | 200 | `elis_(touhou)`、`gouki_(touhou)`；名称查询非精确相等 |
| `tag_related(tags='touhou', type='general')` | 200 | 按 `touhou` 分组，25 个名称/计数对，首项 `thighhighs / 5286` |
| `artist_list(name='fuzichoco')` | 200 | 1 条，ID `50315`，name `fuzichoco` |
| `comment_list()` | 200 | `[]`；缺失 `post_id` 按 0 查询，不是全站最新评论 |
| `comment_search(query='')`（M2） | 200 | `[]`；未取得非空评论正文 |
| `wiki_list(query='touhou', limit=2)` | 200 | 2 条，首条 `alphes`，ID `833` |
| `wiki_history(title='alphes')` | 200 | 2 条，版本 `2`、`1` |
| `note_list()` | 200 | 22 条，首条 ID `7781`；不作为 `limit=2` 生效的证据 |
| `note_history()` | 200 | 25 条 |
| `pool_list()` | 200 | 20 条，首条 ID `99411` |
| `pool_show(99411)` | 200 | 单个合集对象，`posts` 内 2 帖，不是顶层帖子数组 |
| `user_list(name='admin')` | 200 | 20 条，首条 `adminale / 546937`；用户 JSON 为 name/id |
| `forum_list()` | 200 | 30 条，首条主题 ID `10470` |
| M1：`comment_show(0)` | 无 HTTP 响应 | `requests.exceptions.ProxyError`，底层 `RemoteDisconnected: Remote end closed connection without response`；退出 1，非法日期尚未执行 |
| M2：`GET https://yande.re/comment/show.json?id=0` | 404 | `PybooruHTTPError`；550 字节 HTML，含 `Requested page does not exist`；`.data is None`，`.body` 保留原文 |
| M2：`GET https://yande.re/post/popular_by_day.json?year=2026&month=13&day=1` | 400 | `PybooruHTTPError`；空正文，`.data is None`，`.body == ''` |

HTML/空正文 HTTP 错误与 Danbooru 的 JSON 错误体不同；网络异常原样抛出，没有被转换成状态码或 JSON 解码错误。

### 突发与中断复查

| 项目 | 方式 | 结果 |
| :--- | :--- | :--- |
| 单发原失败端点 | `GET /comment/show.json?id=0` | 404 text/html、550 字节 |
| 完整序列重跑 | 同一脚本、同站点、1 秒间隔 | 17 次完成、退出 0，`comment_show(0)` 为 404 |
| 无间隔突发 | 连续 10 次 `GET /post.json?limit=1`，无 sleep | 10/10×200，无中断 |

原第 16 次请求的一次断连记录为**无法复现的瞬时中断**：不是该端点的固有行为，也没有观测到突发限流阈值。站点侧反爬/限流仍是可能原因；重跑时留间隔，不能把无响应写成 HTTP 404 或断言限流阈值。

## 当前示例的执行记录

以下是既有真实执行记录，本次文档重排没有重新发请求。数值和排名会随线上数据变化。

| 家族 | 实际命令 | 输出摘要 / 执行结果 |
| :--- | :--- | :--- |
| Danbooru | `.venv/Scripts/python.exe examples/danbooru/related_tag.py --config pybooru.json` | 移除个人示例后的独立执行：`query: touhou posts: 1096795`；`1girl`、`solo`、`hat`；匿名 |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/list_posts.py --config pybooru.json` | page 1：`1268790 / 1268789 / 1268785`；page 2：`1268781 / 1268779 / 1268755`，各附文件 URL |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/list_tags.py --config pybooru.json` | 3 标签及计数，首项 `thighhighs 264282` |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/wiki_list.py --config pybooru.json` | `alphes`、`alstroemeria_records`、`azur_lane` |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/list_comments.py --config pybooru.json` | `comments: 0`，未填充示例评论 |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/related_tags.py --config pybooru.json` | `tag: touhou`，前 3 个名称/计数对，首项 `thighhighs 5286` |
| Serika | `.venv/Scripts/python.exe examples/serika/service_info.py --config pybooru.json` | API `SerikaART API` / `1.0.0`，统计及用户 `Giru`，详见 S1 表 |
| Serika | `.venv/Scripts/python.exe examples/serika/browse.py --config pybooru.json` | 3 张 safe 图、详情、标签、画师，详见 S1 表 |
| Serika | `.venv/Scripts/python.exe examples/serika/random_image.py --config pybooru.json` | bytes，81224 字节，`Content-Type: image/png`，详见 S1 表 |

Moebooru 五命令按上述顺序以 `&&` 连接执行，整体退出 0；输入来自 `examples.moebooru`，匿名，输出摘要当时保存在维护者本机。Serika 三命令各退出 0、stderr 为空，合计 8 请求。

## 站点复核

来源：用户提供的站点架构调查报告（本机文件，未入库；调查日期 2026-09-14）。报告中的引擎血缘归类与 API 兼容性分开核对；未探测报告中“都不属于”的站点。

### Moebooru 身份与只读覆盖

| 域名 | `GET /` 页脚证据 | `GET /help/api` 自述 | 只读结果 |
| :--- | :--- | :--- | :--- |
| `konachan.com` | `Running Moebooru 6.0.0` | `Help: API 1.13.0+update.3`，自述 Moebooru | 12/12×200 JSON |
| `konachan.net` | `Running Moebooru 6.0.0` | `Help: API 1.13.0+update.3` | 12/12×200 JSON |
| `sakugabooru.com` | `Running Moebooru 6.0.0` | `Help: API 1.13.0+update.3` | 12/12×200 JSON |
| `yande.re` | 此批根路径按 Accept 返回 JSON，没有页脚记录 | `Help: API 1.13.0+update.3`，自述 Moebooru | 12/12×200 JSON；本轮主契约判据站 |

12 条路径：`/post.json`、`/post/index.json`、`/tag.json`、`/artist.json`、`/comment.json`、`/wiki.json`、`/note.json`、`/pool.json`、`/forum.json`、`/user.json`、`/tag/related.json?tags=touhou`、`/post/popular_by_day.json`。
条数反映站点数据差异，例如 `note.json`：Konachan 114、Sakugabooru 82、yande.re 22。Sakugabooru 的报告中高置信度判断已落实为页脚证据，但不取代 yande.re 作为本轮主契约判据。

| 站点 | 帮助页自述 `hash_string` | 配置结论 |
| :--- | :--- | :--- |
| `yande.re` | `choujin-steiner--{0}--` | 与原配置一致，条目不变 |
| `konachan.com` / `.net` | `So-I-Heard-You-Like-Mupkids-?--{0}--` | 与原配置一致，保留 `.com` |
| `sakugabooru.com` | `er@!$rjiajd0$!dkaopc350!Y%)--{0}--` | 新增 `sakugabooru` → `https://sakugabooru.com`，版本同为 `1.13.0+update.3` |

自述原文为 `The actual string that is hashed is "<盐>--<em>your-password</em>--"`，`{0}` 是密码位。模板仅用于构造 password_hash；没有发登录请求证明服务端接受。配置说明见[sites 段](configuration.md#sites-段)。

### Konachan 域名与过滤镜像

| 同时段对照 | 观察结果 | 结论 |
| :--- | :--- | :--- |
| `konachan.com`，同域名、同一时段 | 一次 `403`（`Server: cloudflare`、`Just a moment...`），一次 `200`（含首页、帮助页与 12 端点） | `403` 是网络侧的 Cloudflare 挑战，不是域名或引擎没有 API |
| `.com` 的 `/post.json?limit=5` | `408456, 408455, 408454, 408453, 408452` | 默认保留 `.com` |
| `.net` 的同一请求 | `408453, 408452, 408451, 408450, 408449` | 同站过滤镜像，少最新 3 帖，不是等价备份 |

两域名同引擎、同 API 版本、同加盐模板，但内容不等价。`.net` 与 `.com` 内容不等价，不能用 `.net` 代替完整站点或 yande.re 的契约判据。

### HTML 帮助页的 Accept 差异

| 请求头 | `yande.re` | `konachan.com` | `sakugabooru.com` |
| :--- | :--- | :--- | :--- |
| `Accept: application/json` | 404 HTML（550 B） | 404 空正文 | 404 空正文 |
| `Accept: text/html,application/xhtml+xml` | 200（42930 B） | 200（44403 B） | 200（44166 B） |

本库固定发送 JSON Accept，帮助页只提供 HTML；其 404 不能证明页面或路由不存在。上游模板与路由依据见 [Moebooru 契约审计附注](moebooru-contract-notes.md)。

### Safebooru 与 Rails 路径判别

匿名 GET；Safebooru 此前仅继承旧清单登记，本批才补齐验证。

| 请求 | `safebooru.donmai.us` | `yande.re` |
| :--- | :--- | :--- |
| `/posts.json?limit=1` | 200，list[1] | 404，`Server: freenginx` |
| `/post.json?limit=1` | 404 | 200，list[1] |
| `/tags.json?limit=1` | 200 | — |
| `/artists.json?limit=1` | 200 | — |
| `/comments.json?limit=1` | 200 | — |
| `/wiki_pages.json?limit=1` | 200 | — |
| `/pools.json?limit=1` | 200 | — |
| 库调用 `Danbooru('safebooru').post_list(limit=2)` | 200，`[12194055, 12194053]` | — |

Safebooru 与 Danbooru 同属 donmai 部署，使用 Danbooru 引擎。路径形态、页脚/帮助页自述及认证方式共同用于判断；本库不自动识别，调用者选择类，见[如何选类](configuration.md#怎么判断一个站点该用哪个类)。

### Safebooru：D4 用客户端复测的 16 个方法

上面那一批是裸路径探测；D4 改用线上客户端（`Danbooru(site_url='https://safebooru.donmai.us')`）逐方法复测，
匿名、间隔 1 秒。ID 取自同一轮的列表响应：
post `12195666`、tag `2730264`、artist `683106`、comment `2630682`、pool `23200`。

| 客户端方法 | 实际路径 | HTTP | 返回形态 |
| :--- | :--- | :--- | :--- |
| `post_list(limit=1)` | `/posts.json?limit=1` | 200 | `list[1]`，46 个 Danbooru post 字段（含 `tag_string` / `file_url` / `media_asset`） |
| `post_show(12195666)` | `/posts/12195666.json` | 200 | `dict`，同一组字段 |
| `post_random()` | `/posts/random.json` | 200 | `dict`，同一组字段 |
| `tag_list(limit=1)` | `/tags.json?limit=1` | 200 | `list[1]` |
| `tag_show(2730264)` | `/tags/2730264.json` | 200 | `dict` |
| `artist_list(limit=1)` | `/artists.json?limit=1` | 200 | `list[1]` |
| `artist_show(683106)` | `/artists/683106.json` | 200 | `dict` |
| `comment_list(group_by='comment', limit=1)` | `/comments.json?group_by=comment&limit=1` | 200 | `list[1]` |
| `comment_show(2630682)` | `/comments/2630682.json` | 200 | `dict` |
| `pool_list(limit=1)` | `/pools.json?limit=1` | 200 | `list[1]` |
| `pool_show(23200)` | `/pools/23200.json` | 200 | `dict` |
| `wiki_page_list(limit=1)` | `/wiki_pages.json?limit=1` | 200 | `list[1]` |
| `wiki_page_show('help:api')` | `/wiki_pages/help%3Aapi.json` | 200 | `dict` |
| `related_tag(search={'query': 'rating:g'})` | `/related_tag.json?search%5Bquery%5D=rating%3Ag` | 200 | `dict`，含 `post_count` / `related_tags` / `wiki_page_tags` |
| `counts_posts()` | `/counts/posts.json` | 200 | `dict`，键 `counts` |
| `note_list(limit=1)` | `/notes.json?limit=1` | 200 | `list[1]` |

16 次全 `200`，形态与 `danbooru.donmai.us` 相同；`sites.safebooru` 条目本轮没有改动。
不带 `group_by` 时 `/comments.json` 返回的是帖子对象（本轮首测因此把 post id 当成 comment id，得到 404），
这一层是服务端分组行为，不是站点差异。另有同一轮的首版探测用不存在的 ID 调用 `tag_show(1)` / `artist_show(1)`，
Safebooru 得到 404 `ActiveRecord::RecordNotFound`，与 D1 记录的 `danbooru.donmai.us` `/posts/0.json` 同类。

## Serika：2026-09-15 实现后的匿名调用

S1 只计新增客户端的 **8×200**，不混入旧评估中的匿名 401。基址为 `https://serika.art`。

### 官方 v1：实际匿名成功

| 客户端方法 | 实际 GET 路径 | HTTP | 真实响应 / 消费结果 |
| :--- | :--- | :--- | :--- |
| `api_index()` | `/api/v1` | 200 | 裸对象 name `SerikaART API`，version `1.0.0` |
| `stats()` | `/api/v1/stats` | 200 | 拆封后 totals：images **4237843**、tags **730851**、users **3058**；meta.timestamp `2026-09-14T22:18:21.628Z` |
| `user_list(...)` | `/api/v1/users?page=1&limit=1&sort=newest` | 200 | 返回 1 用户 `Giru`；users 特殊信封拆为数组，last_call.meta.pagination：page=1、limit=1、total=3058、pages=3058 |
| `random_image(...)` | `/api/v1/random/400/400/image.png?fit=cover&format=png&ratings=safe` | 200 | Python bytes，**81224 字节**，Content-Type `image/png`，未进行 JSON 解码 |

| S1 附加证据 | 真实值 |
| :--- | :--- |
| stats 评级分组 | safe **3499663**、questionable **324774**、explicit **413406** |
| stats AI 与上传 | AI **14195**、非 AI **4223648**、最近 24h 上传 **0** |
| 用户计数关系 | 用户目录与 stats 本次均 3058；不能由占位账号排除规则断言每次必然不同 |
| 图片标识头 | x-image-id / x-dbid 均 **2796776**，x-post-id **1416106** |
| 图片规格头 | x-original-width `1168`，x-original-height `2057`，x-rating `safe` |
| 图片传输头 | Date `Mon, 14 Sep 2026 22:18:36 GMT`；cf-cache-status `MISS` |
| 图片验证范围 | 有实际选图元数据头；未另做图片解码、视觉检查或错误占位探测；再次随机调用不保证相同值 |

### 站内非版本化私有面：实际匿名成功

| 客户端方法 | 实际 GET 路径 | HTTP | 真实响应 / 消费结果 |
| :--- | :--- | :--- | :--- |
| `internal_image_list(...)` | `/api/images?page=1&limit=3&ratings=safe&sort=newest` | 200 | 3 张 safe 图；内部 id **7323837 / 7323836 / 7323835**，post_id **4237836 / 4237835 / 4237834**；pagination.total=3499663、pages=1166555、has_next=true |
| `internal_image_show(...)` | `/api/images/4237836` | 200 | 用前一响应的 **post_id** 查询；返回内部 id **7323837**、post_id **4237836**、rating=safe |
| `internal_tag_list(...)` | `/api/tags?limit=3` | 200 | `highres: 3402288`、`1girl: 3223922`、`solo: 2597729` |
| `internal_artist_list(...)` | `/api/artists?page=1&limit=3` | 200 | `dairi: 17186`、`inoino: 4265`、`nyantcha: 2785`（tagName/postCount） |

列表首图与详情 URL 相同：`https://cdn.serika.art/uploads/1788013605888-1788013605888-1q2b2g-danbooru-12074741.png`。
这验证站内详情的顺序号语义；没有用需 key 的 v1 详情做 ID 对照。控制器、官方文档与实际字段的差异见 [Serika 契约审计附注](serika-contract-notes.md)。

## e621ng：2026-09-15 实现后的匿名调用

E1 是本轮新增客户端后的真实执行：**37 次匿名 GET**，其中 30 次来自三个示例在 e621.net 与 e926.net
各跑一遍（6 条命令，每条分别为 3、10 或 2 次调用），7 次是返回形态与权限分支的单独复核。除下表标明的 `403`
外全部 `200`。基址为 `https://e621.net` 与 `https://e926.net`，`sites.e621` / `sites.e926` 的
`username` 与 `api_key` 都是空串。示例输出只保留摘要：文件走尺寸/大小/md5，标签走计数，评论与笔记
正文只报长度，不打印媒体 URL 与正文。

### 三个匿名示例

六条命令都不带 `--config`（读包内默认配置），用 `--site` 显式指定站点；六条都退出 0、stderr 为空。

| 站 | 实际命令 | 输出摘要 |
| :--- | :--- | :--- |
| e621 | `.venv/Scripts/python.exe examples/e621/list_posts.py --site e621` | `post_list` `/posts.json?tags=rating%3As&limit=2`：2 帖，`6709455`（jpg 2370×2423，score 0）与 `6709449`（png 1817×2832，score 2），均 `rating=s`，各含 `file` 的 ext/size/宽高/md5 与 9 类 `tags` 计数；`post_show(6709455)` 同帖；`post_random` 命中 `1434546`（png 1275×1650，score 32） |
| e621 | `.venv/Scripts/python.exe examples/e621/browse_resources.py --site e621` | 10 次调用全 `200`：`tag_list(limit=2)` → `anthro`(`7115`,4464327) / `mammal`(`12054`,4398445)；`tag_show(7115)`；`artist_list(limit=2)` → `miindfang`(`126653`) / `weirdmichelle69`(`126652`)，各带 `urls`；`artist_show(126653)`；`comment_list(group_by=comment,limit=2)` → `10071234` / `10071233`；`comment_show(10071234)`；`pool_list(limit=2)` → `58878`(collection) / `59177`(series)；`pool_show(58878)`；`note_list(limit=2)` → `506555` / `506554`；`note_show(506555)` |
| e621 | `.venv/Scripts/python.exe examples/e621/wiki_pages.py --site e621` | `wiki_page_list(limit=2)` → `rusty_seas`(`112045`) / `buckteeth`(`8473`)；`wiki_page_show('help:api')` 命中 `/wiki_pages/help%3Aapi.json`，返回 `11224`、`is_locked=true` |
| e926 | `.venv/Scripts/python.exe examples/e621/list_posts.py --site e926` | 3 次调用全 `200`；`post_list` 首帖与 `post_show` 同为 `6709455`；`post_random` 命中 `3065213`（webm 1280×720，score 614） |
| e926 | `.venv/Scripts/python.exe examples/e621/browse_resources.py --site e926` | 10 次调用全 `200`；标签 `7115`、画师 `126653`、评论 `10071234`、合集 `58878`、笔记 `506555` 的列表首项与详情相符，各列表同样返回 2 条 |
| e926 | `.venv/Scripts/python.exe examples/e621/wiki_pages.py --site e926` | 2 次调用全 `200`；列表 `112045` / `8473`，`wiki_page_show('help:api')` 返回 `11224` |

### 返回形态与权限分支

| 调用 | 实际请求路径 | HTTP | 真实摘要 |
| :--- | :--- | :--- | :--- |
| `post_count(tags='rating:s')` | `/posts/count.json?tags=rating%3As` | 200 | `{"count": 240001, "capped": true}`；e621 与 e926 同值，说明该批次搜索触到分页上限，`count` 是下限 |
| `request('GET', 'posts', params={'tags': 'rating:s', 'limit': 1})` | `/posts.json?tags=rating%3As&limit=1` | 200 | 原始正文是 `{"posts": [...]}` 信封；首帖是 25 键 legacy 形态（`file` / `preview` / `sample` / `score` / `tags` / `flags` / `pools` / `sources` / `relationships` 等），无 `tag_string` / `file_url` / `media_asset` |
| `post_list(md5='b37f8af2b4508efb57cfeb08ef2ef5a1')` | `/posts.json?md5=b37f8af2b4508efb57cfeb08ef2ef5a1` | 200 | 线上正文是 `{"post": {...}}`；方法按该分支拆封，返回**单个帖子对象**，字段与上一行同组 |
| `post_list(tags='rating:s', limit=1, only='id,rating')` | `/posts.json?tags=rating%3As&limit=1&only=id%2Crating` | 200 | 返回数组、没有信封，但元素仍是完整 25 键 legacy 对象：`only` 只去掉信封，**不做字段筛选** |
| `post_list(tags='rating:s', limit=1, v2=True)` | `/posts.json?tags=rating%3As&limit=1&v2=true` | 200 | 返回数组、没有信封，元素是 18 键 v2 形态：`files` 与 `stats` 为对象、`tags` 为字符串数组 |
| `related_tag(search={'query': 'wolf', 'category_id': 0})` | `/related_tag.json?search%5Bquery%5D=wolf&search%5Bcategory_id%5D=0` | 403 | `PybooruHTTPError`，`.data` 为 `{"success": false, "reason": "Access Denied"}`，`.http_code` 为 `403` |

这批复核的响应 `Date` 头落在 `Tue, 15 Sep 2026 16:27:20`–`16:27:32 GMT`；三个示例的执行记录同为
2026-09-15，未记录到秒级时刻。`related_tag_bulk` 没有请求；`related_tag` 仅执行匿名拒绝，两个方法的
成员成功路径均未实测。已实现只读方法的上游依据见 [e621ng 契约审计附注](e621-contract-notes.md)。

交付中未增加或保留测试文件，未运行项目测试套件、formatter、lint 或构建；上面的数字全部来自真实 HTTP 响应。

## 文档修正后的示例复核（2026-09-16）

### Danbooru 只读示例与写边界

为核对 README 的示例清单，六个只读脚本各执行一次，均退出 `0`、stderr 为空。命令格式为
`.venv/Scripts/python.exe examples/danbooru/<脚本> --config <配置文件>`；尖括号表示脚本名与覆盖配置路径，
请求输入来自配置中的 `examples.danbooru`，站点为 `https://danbooru.donmai.us`。

| 脚本 | 本次真实输出摘要 |
| :--- | :--- |
| `list_posts.py` | 三帖 `12198589` / `12198583` / `12198582`，均 `rating=g`，各打印标签串 |
| `list_tags.py` | `1girl 8420422`、`highres 8166550`、`solo 7070952` |
| `show_post.py` | 从列表取得首帖 `12198589`，打印评级与标签串 |
| `paginate_posts.py` | page 1：`12198589 / 12198583 / 12198582`；page 2 与 before `12198582` 均为 `12198581 / 12198578 / 12198577` |
| `related_tag.py` | `query: touhou posts: 1097086`；`1girl`、`solo`、`hat` |
| `wiki_page.py` | `help:api`，正文摘要以 `Danbooru offers a REST-like API` 开始 |

这些脚本不打印 HTTP 状态码，因此不把进程退出 `0` 记作逐请求的 `200` 证据。
`comment_create.py` 是需凭据的真实 POST 写示例，保持未执行、未实测；本次没有发写请求。

### e621 示例的默认站点

命令 `.venv/Scripts/python.exe examples/e621/list_posts.py --config <配置文件>` 中的配置路径为占位表示；
执行时**没有传 `--site`**，站点取 `examples.e621.site`。进程退出 `0`、stderr 为空，并打印三次真实 HTTP `200`：

| 方法 | 实际请求 / 结果 |
| :--- | :--- |
| `post_list` | `https://e621.net/posts.json?tags=rating%3As&limit=2`，返回 `6709653` / `6709650`，均 `rating=s` |
| `post_show` | `https://e621.net/posts/6709653.json`，返回首帖 `6709653` |
| `post_random` | `https://e621.net/posts/random.json?tags=rating%3As`，返回 `6573362`，`rating=s` |

本次只确认该脚本省略 `--site` 的路径，不将它扩展为全部站点、空字符串选项或其它参数组合的实测。

## 边界与未实测

| 范围 | 没有执行 / 不能据现有证据声称 |
| :--- | :--- |
| 全家族写路径 | 所有需登录的发帖、上传、评论、投票、编辑、删除、审核均只有源码依据；本轮所有线上执行为匿名读取 |
| Danbooru 权限与可选能力 | 高权限/重新认证（API keys、jobs 写、site credentials）、archive 版本历史、IQDB、上传/媒体链路；写重定向 `artist_delete` / `artist_ban` / `artist_unban` / `forum_topics_mark_all_as_read` |
| Danbooru 部署 | 除本页明确列出的站点与路径外，没有下游兼容矩阵 |
| Moebooru 认证与写操作 | 账号/password_hash、source-only/文件上传、权限等级、审核删除；包括源码允许匿名进入的修改型动作，均未执行 |
| Moebooru 其余读路径 | 相似图、未列明热门查询、补全/标签摘要/别名/蕴含、论坛详情/搜索、指定帖子的非空评论等；已执行的笔记/Wiki 历史不等于存在通用 archive API |
| Moebooru 部署与后端 | 旧路径版本真实部署、未列明 fork 差异、写重定向最终结果、异步任务后端；路由存在不等于 JSON 或已启用能力 |
| Serika 官方需 key 的 12 方法 | `image_list`、`image_show`、`image_delete`、`image_similar`、`image_batch`、`random_list`、`tag_list`、`tag_show`、`user_show`、`search`、`trending`、`upload`；用户无 key 且不申请，S1 没有请求这些路径；成功响应/认证/权限/限流/批量 JSON/multipart/删除/参数边界没有实测 |
| Serika 站内另外 10 方法 | `internal_image_comments`、`internal_tag_show`、`internal_tag_autocomplete`、`internal_tag_complementary`、`internal_artist_show`、`internal_artist_wiki`、`internal_artist_reviews`、`internal_user_list`、`internal_user_show`、`internal_user_activity`：只核对匿名可读源码 |
| Serika 错误及部署 | S1 未发错误请求，不声称覆盖 401/403/404/429、PNG 占位或二进制错误；`.data['code']` 可读仅由源码确认；无其他自托管部署验证 |
| e621ng 成员与写路径 | `related_tag` / `related_tag_bulk` 的成员成功响应、Basic 认证成功均仅源码对齐、未实测；没有实现原生写方法，没有请求上游写动作与 staff 路径 |
| e621ng 其余返回分支 | `v2` 的 `mode=extended` / `thumbnail(s)`、`comment_list(group_by=post)`、`artist_show` 名字形式、请求级 `safe_mode`、旧式单数重定向没有本轮客户端实测；此前 `/help/api` 的 HelpPage 200 与 `/static/site_map` 的 406 属改造前探测，不计入 E1 |
| e621ng 部署与返回上限 | 仅覆盖 e621.net 与 e926.net 两个站点；e926 的 HTML 路由被 Cloudflare 挑战，本轮只走 JSON；`limit` 的 320 上限与编号页 750 上限只在源码与 `410` 分支上核对，没有逐值探测边界 |
| 非能力范围 | 未实现 Serika cookie 登录、私有交互/资源写操作；未申请或实测需要 key 的候选站调用；e621ng 面未包写方法与邻接只读路由 |
| 工程流程 | 交付中未新增或保留测试文件；未运行项目测试套件、formatter、lint、发布 workflow、分发包构建；旧 workflow 不代表已在当前 GitHub runner/PyPI 验证；上游源码只读且未提交 |

## 历史记录

本节保留阶段性判断与已删除入口，不把它们当作当前用法或当前覆盖范围。

| 历史阶段 / 入口 | 当时事实 | 后续落点 |
| :--- | :--- | :--- |
| 最初共享传输脚本 | 匿名 `/posts.json?limit=2` 为 200；仅本地构造 Konachan/yande.re 客户端，观察 API 版本与鉴权模板保留 | 当时没有 Moebooru 线上验证；后续执行单列为 M1–M4 |
| Danbooru 阶段的未验证清单 | 当时 Moebooru 全部端点、除 danbooru.donmai.us 外站点均未验证 | 后来 Moebooru 与 Safebooru/候选站记录各自独立，不将新结果计入 D1 |
| 已删除个人示例 | `.venv/Scripts/python.exe examples/danbooru/pixiv_id_to_tag.py --config pybooru.json`：`artist: 8704 fuzichoco`，帖子 `12090564`、`12070768`、`12064514` | 脚本在 `20cea4b` 删除，根配置三个个人输入也删除；不能作为可运行入口或库特性 |
| 原生 Artist 查询历史 | pixiv 作者 `27517` → artist `8704` → name/tag `fuzichoco` | 保留真实 URL 与查询证据；通用 Artist 契约见 [Danbooru 方法参考](danbooru-api.md) |
| 与个人示例同批的相关标签 | `.venv/Scripts/python.exe examples/danbooru/related_tag.py --config pybooru.json`：query `touhou`，post_count `1096790`，`1girl` / `solo` / `hat`；两示例均同配置、代理、匿名 | 删除个人输入后另一次输出为 `1096795`，两个计数是独立快照 |
| Moebooru 评论示例替换 | 原 `comment_create.py` 会真实写入且需账号 | 已改用只读 `list_comments.py`，未加模拟成功或护栏；写方法仍在参考页 |
| M1 中断的最初判断 | 用户指出站点侧反爬/限流（yande.re 较重）可造成无 HTTP 响应，是环境预期现象，不是本库缺陷 | M3 未复现、未观测阈值；保留一次瞬时中断事实，不写成 404 或确定限流机制 |
| Konachan 早期探测 | 早期探测脚本：`.com` 24/24 为 Cloudflare 403 / `Just a moment...` | 限制随网络环境变化，不是域名永久不可用 |
| 帮助页早期 404 | 当时仅发 `Accept: application/json` | HTML Accept 返回 200，页面并未缺失；详见 Accept 差异表 |
| Serika 改造前匿名 200 | `/api/v1`、`/api/v1/stats`、`/api/v1/users?limit=1`、`/api/v1/random/400/400/image.png`；站内 `/api/images`、`/api/images/:id`、`/api/tags`、`/api/artists` | 来源：改造前的 Serika.art 评估记录；不计入 S1 的 8 次新增客户端请求 |
| Serika 改造前匿名 401 | v1 images 列表/详情、tags 列表/详情、trending、search、random、users 详情，共 8 个 GET | 仅证明无 key 被拒绝，不证明成功字段；S1 没有重跑 |
| Serika 说明矛盾纠正 | ID、未知标签、限流错误码、PNG 标签过滤等旧评估泛化 | 仅按源码纠正，见 [Serika 契约审计附注](serika-contract-notes.md)，没有另发探测 |

## Anybooru 改名后的复跑（2026-09-18）

本节为 `anybooru==0.1.0.dev1` 的新执行，不回写前面的 Pybooru 历史证据。
首条示例的开始时间为 `2026-09-17T23:22:05Z`（UTC）。以下命令中的 `<配置文件>` 是占位符：
实际使用的是从包内配置复制出来的覆写配置；凭据为空，User-Agent 为 `Anybooru/0.1.0.dev1`。
包内默认 `request.proxies` 仍是 `{}`，分发配置里不放任何网络设置。

### 导入与默认配置

```bash
.venv/Scripts/python.exe -c "from anybooru import Danbooru, Moebooru, Serika, E621"
```

退出 `0`，stdout/stderr 均为空。另一次真实导入读取的元数据为 `name: anybooru`、
`version: 0.1.0.dev1`、`Home-page: https://github.com/NebulaeWisdom/anybooru`；
`anybooru.DEFAULT_CONFIG_FILE` 指向已安装包目录内的 `anybooru/anybooru.json`。
用同一内部配置构造 `E621` 后，会话的 `User-Agent` 实际为 `Anybooru/0.1.0.dev1`。

### 四家族现有只读示例

每行均以 `.venv/Scripts/python.exe <脚本路径> --config <配置文件>` 执行，未传 `--site`，
站点来自配置。共 **17 条命令全部退出 `0`，stderr 均为空**；没有运行需凭据的 `comment_create.py`。

| 脚本路径 | 真实输出片段 / 摘要 |
| :--- | :--- |
| `examples/danbooru/list_posts.py` | `12211425 g`、`12211421 g`、`12211420 g` 及各自标签 |
| `examples/danbooru/list_tags.py` | `1girl 8429162`、`highres 8177132`、`solo 7077918` |
| `examples/danbooru/show_post.py` | `12211425 g` 及标签 |
| `examples/danbooru/paginate_posts.py` | `page 1 [12211425, 12211421, 12211420]`；`page 2` 与 `before 12211420` 均为 `[12211416, 12211415, 12211410]` |
| `examples/danbooru/related_tag.py` | `query: touhou posts: 1097796`，随后为 `1girl` / `solo` / `hat` |
| `examples/danbooru/wiki_page.py` | `help:api`，正文以 `Danbooru offers a REST-like API to make scripting easy.` 开头 |
| `examples/moebooru/list_posts.py` | 两页各 3 帖及文件 URL：第一页 `1269034` / `1269023` / `1269022`；第二页 `1269019` / `1269016` / `1269015` |
| `examples/moebooru/list_tags.py` | `thighhighs 264342`、`no_bra 208004`、`nipples 203288` |
| `examples/moebooru/wiki_list.py` | `alphes`、`alstroemeria_records`、`azur_lane` |
| `examples/moebooru/list_comments.py` | `comments: 0`，未验证非空评论正文 |
| `examples/moebooru/related_tags.py` | `tag: touhou`，`thighhighs 5286` / `nipples 4630` / `wings 4491` |
| `examples/serika/service_info.py` | 3×200；`SerikaART API` / `1.0.0`，图片 `4237843`、标签 `730851`、用户 `3059`，用户目录返回 1 项 |
| `examples/serika/browse.py` | 4×200；列表 3 图，首图与详情 `id=7323837` / `post_id=4237836`；标签首项 `highres 3402288`，画师首项 `dairi 17186` |
| `examples/serika/random_image.py` | 200，`python_type: bytes`、`bytes: 66729`、`Content-Type: image/png`，`x-image-id: 1811154` |
| `examples/e621/list_posts.py` | 3×200；列表 `6715096` / `6715093`，详情 `6715096`，随机 `502758`，均 `rating=s` |
| `examples/e621/browse_resources.py` | 10×200；标签 `7115 anthro`，画师 `126799 panzer_(p.z)`，评论 `10075334`（正文 229 字符），合集 `54791`，笔记 `506654` |
| `examples/e621/wiki_pages.py` | 2×200；列表标题 `toriel` / `vodyanoy5`，详情 `11224 help:api` |

Danbooru 与 Moebooru 的脚本不打印状态码，本节只报告真实 stdout 和进程退出码，
不据此编造逐请求 HTTP 状态。Serika 明确打印 **8×200**，e621.net 明确打印 **15×200**；
后者证明新 User-Agent 在这些匿名路由上被接受，没有遇到 403。
Serika 本轮三个示例均成功，但不抹去此前批次出现过的连接失败。
本轮没有重测 e926、账号认证、写路径、Serika 需 key 的方法或其余部署与参数组合。

### 分发包与文档锚点

真实执行 `.venv/Scripts/python.exe -m pip wheel . --no-deps --no-build-isolation --wheel-dir <输出目录>`
（输出目录为占位表示），退出 `0`，生成 `anybooru-0.1.0.dev1-py3-none-any.whl`。
用项目解释器读取 wheel 后确认包含 `anybooru/anybooru.json`，没有旧包名的归档成员；
元数据实际为 `Name: anybooru`、`Version: 0.1.0.dev1`、
`Home-page: https://github.com/NebulaeWisdom/anybooru`。配置中的 User-Agent 为 `Anybooru/0.1.0.dev1`、`proxies` 是空对象。

项目解释器检查了全部 **30 份受跟踪 Markdown** 中的 **84 个相对锚点链接**，结果为 **0 悬空**、退出 `0`。
没有新增测试套件，也没有用上述结果代替 GitHub runner 或 PyPI 发布验证。

### 只构建工作流的本地执行

真实执行 `.venv/Scripts/python.exe -m build --no-isolation --outdir <输出目录>`（目录为占位表示），
退出 `0`，末行输出：

```text
Successfully built anybooru-0.1.0.dev1.tar.gz and anybooru-0.1.0.dev1-py3-none-any.whl
```

该过程先构建 sdist，再从 sdist 构建 wheel；日志包含 `anybooru/anybooru.json`。
本地复跑使用已装好依赖的项目虚拟环境，因此加了 `--no-isolation`；CI 保持 `python -m build` 的默认隔离构建。
这不是 GitHub Actions runner 实跑，也未触发或验证任何 PyPI 发布。临时分发产物检查后删除。

[文档入口](index.md) · [Danbooru 审计](danbooru-contract-notes.md) · [Moebooru 审计](moebooru-contract-notes.md) · [Serika 审计](serika-contract-notes.md) · [e621ng 审计](e621-contract-notes.md)

## Zerochan：匿名只读实测（2026-09-18）

本节是 `anybooru==0.1.0.dev1` 新增 Zerochan 客户端后的真实执行，不计入上面的四家族历史批次。
契约来自 [API 页面](https://www.zerochan.net/api)的
[2024 年快照](https://web.archive.org/web/2024/https://www.zerochan.net/api)与实际响应；没有上游引擎源码。
以下命令中的 `<配置文件>`、`<只读编排脚本>`、`<记录文件>`、`<输出目录>` 均为占位表示：
实际配置从包内配置复制而来；没有使用环境变量，没有用户名、认证头或登录动作。
User-Agent 为 `Anybooru/0.1.0.dev1`，**没有用户名，不满足页面的完整身份要求**；匿名成功不排除被封禁风险。

### Z1：导入与包内配置

使用项目虚拟环境实际导入 `Zerochan`，以 `Zerochan('zerochan')` 构造并读取 URL 与 UA，输出：

```text
Zerochan https://www.zerochan.net Anybooru/0.1.0.dev1 {}
```

退出 `0`、stderr 为空。此构造使用默认的包内配置（`proxies` 为空），线上请求则使用覆写配置。
证明默认配置可构造，不把它记成连网成功。

### Z2：逐端点与可选参数

真实执行的命令形态：

```bash
.venv/Scripts/python.exe <只读编排脚本> --config <配置文件> --output <记录文件>
```

一次性编排调用真实的 `request` / `entry_list` / `entry_show`，输入全部来自 `verification.zerochan`。
相邻请求完成后暂停配置的 `1.2` 秒，不并发、不重试；没有把客户端限速写进库。
开始时间为 `2026-09-18T00:08:47.466210+00:00`，首个响应 `Date` 为 `Fri, 18 Sep 2026 00:08:48 GMT`。
共 **16 次 GET：15×200、1×500**，全部收到 HTTP 响应，Content-Type 均为
`application/json; charset=utf-8`。编排记录错误后继续其余请求，最终退出 `1`（不是全部通过）。

下表 URL 均以 `https://www.zerochan.net` 为根；每行只有一次实际调用。

| 配置项 / 调用 | 实际路径与查询串 | HTTP | 真实响应摘要 |
| :--- | :--- | :--- | :--- |
| `default_query` / `request('/')` | `/?json=` | 200 | 顶层只有 `items`，数组 **48 条**；首项 `4725815`，`tag: Sin Mal` |
| `entry_query` / `entry_list` | `/?p=1&l=2&s=id&json=` | 200 | 2 条，`4725815` / `4725814` |
| `tag_query` / `entry_list` | `/Genshin+Impact?l=2&json=` | 200 | `4034550`（`tag: Genshin Impact`）、`3793080`（`tag: Yae Miko`） |
| `multi_tag_query` / `entry_list` | `/Lumine,Flower?l=2&json=` | 200 | `4034550` / `4110668`，两条 `tag` 均为 `Genshin Impact` |
| `strict_query` / `entry_list` | `/Genshin+Impact?l=2&strict=&json=` | 200 | `4034550` / `4110668`，两条 `tag` 均为所查的 `Genshin Impact` |
| `entry_id` / `entry_show` | `/3793685?json=` | 200 | 裸对象；`primary: Yukihana Lamy`，`2976×4055`，`size: 5706752` |
| `optional_queries.page` | `/?p=2&l=2&s=id&json=` | 200 | 2 条，`4725810` / `4725809`，与上一页不同 |
| `optional_queries.popularity_all` | `/?l=2&s=fav&t=0&json=` | **500** | `AnybooruHTTPError`；正文为不完整 JSON，见下文原文 |
| `optional_queries.popularity_recent` | `/?l=2&s=fav&t=1&json=` | 200 | 2 条，`4723740` / `4722756` |
| `optional_queries.popularity_extended` | `/?l=2&s=fav&t=2&json=` | 200 | 2 条，`4680768` / `4694831` |
| `optional_queries.large` | `/?l=2&d=large&json=` | 200 | `4725814`（`3570×2008`）、`4725810`（`3010×4858`） |
| `optional_queries.huge` | `/?l=2&d=huge&json=` | 200 | `4725814` / `4725810`，本次样本与 large 相同 |
| `optional_queries.landscape` | `/?l=2&d=landscape&json=` | 200 | `4725814`（`3570×2008`）、`4725800`（`4131×2160`） |
| `optional_queries.portrait` | `/?l=2&d=portrait&json=` | 200 | `4725815`（`1153×1684`）、`4725810`（`3010×4858`） |
| `optional_queries.square` | `/?l=2&d=square&json=` | 200 | `4725807`（**`1006×966`**）、`4725804`（`1024×1024`） |
| `optional_queries.color` | `/?l=2&c=red&json=` | 200 | 2 条，`4725810` / `4725807` |

`optional_queries` 实际是按 `name` 命名的数组，上表点号表示其中一项，不是 JSON 对象的访问表达式。

列表响应首项摘录（只选列以下字段，未展示完整 tags 数组）：

```json
{"items":[{"id":4725815,"width":1153,"height":1684,"md5":"00602349a494ad03942f1148208ca34a","thumbnail":"https://s3.zerochan.net/240/15/16/4725815.avif","tag":"Sin Mal"}]}
```

本批列表项观察到的完整键集为 `id, width, height, md5, thumbnail, source, tag, tags`；
列表顶层没有 `total` / `page` / 下一页链接。默认 **48 条**只是本次不传 `l` 的观察，不是页面承诺或库默认。
详情观察到 `id, small, medium, large, full, width, height, size, hash, source, primary, tags`，选列摘录：

```json
{"id":3793685,"width":2976,"height":4055,"size":5706752,"hash":"5ba73b33f6f045f62f938f63158704e0","primary":"Yukihana Lamy","full":"https://static.zerochan.net/Yukihana.Lamy.full.3793685.jpg","source":"https://www.pixiv.net/en/artworks/87283595"}
```

`s=fav&t=0` 的 **完整响应正文**为以下文本（原始换行是 CRLF）：

```text
{
  "items": [
}
```

HTTP 为 `500 Internal Server Error`，虽然 Content-Type 声明 JSON，但正文没有闭合数组，不能解析成 JSON。
客户端先按 HTTP 状态抛 `AnybooruHTTPError`，保留 URL 与正文，没有把它转成成功空列表。
API 快照把 `t=0` 列为 all time；**本次只有失败响应，成功行为未实测**，不删参数、不特判或换端点。
同样不能把 `d=square` 解释成严格的宽高相等，或据两条样本推导 large/huge 的阈值。
`c=red` 的成功响应不等于已审计服务端颜色分类算法。

### Z3：两个可运行示例

以下两条命令均真实执行，站点由配置选择（未传 `--site`），分别在 `00:09:50` 与 `00:09:54` UTC 开始：

```bash
.venv/Scripts/python.exe examples/zerochan/list_entries.py --config <配置文件>
.venv/Scripts/python.exe examples/zerochan/filter_entries.py --config <配置文件>
```

两条命令均退出 **`0`**，stderr 为空；共 **5×HTTP 200**，每次调用都打印真实状态码和 URL。

| 示例 | 真实输出片段 |
| :--- | :--- |
| `list_entries.py` | `entry_list`：`count: 2`，`4725815 Sin Mal` / `4725814 Sin Mal`；`entry_show`：`3793685 Yukihana Lamy`，`2976×4055`、`size: 5706752` |
| `filter_entries.py` | 单标签 `4034550` / `3793080`；多标签 `4034550` / `4110668`；strict `4034550` / `4110668`，两条 primary 标签均为 `Genshin Impact` |

Z2 与 Z3 合计 **21 次匿名 GET：20×200、1×500**。没有写请求、没有下载图片、没有触发登录。

### Z4：wheel 入包

实际构建一次：

```bash
.venv/Scripts/python.exe -m pip wheel . --no-deps --no-build-isolation --wheel-dir <输出目录>
```

退出 **`0`**，输出 `Successfully built anybooru`，生成 `anybooru-0.1.0.dev1-py3-none-any.whl`。
读取归档确认含 `anybooru/zerochan.py`、`anybooru/api_zerochan.py`、`anybooru/anybooru.json`；
包内 `sites.zerochan` 为 `{"url":"https://www.zerochan.net"}`。元数据 `Name: anybooru`、
`Version: 0.1.0.dev1`，description/keywords 均包含 Zerochan。检查后删除分发产物与本轮构建目录。
没有从 wheel 独立安装再运行，也没有执行 sdist、GitHub runner 或 PyPI 发布验证。

### 既有探测、未解决与未实测

* 实现前已取得的独立响应：裸 `json` 与空值 `json=` 均为 `200 application/json`；
  `/3793685` 不带 json 时为 `200 text/html`。它们不计入 Z2/Z3，也没有把 HTML 当 API 解析。
* live API 帮助页的直接抓取曾遇浏览器挑战，当前契约文字使用 2024 快照；没有声称取到了最新版正文。
* `s=fav&t=0` 的成功响应仍未拿到；不把 500 原因推断成限流或其它外部因素。
* 尚未验证合规用户名 UA、特殊字符标签在服务端的匹配、meta 标签拒绝、strict 多标签组合、其它颜色、
  所有排序/过滤组合、空结果、末页、非法参数、缺失条目、限流/封禁响应与其它部署。
* `xml` 是页面列出的格式，但本库只实现 JSON，XML 未实现也未实测；写操作、登录会话与 HTML 页面不在 API 能力内。
* 没有新增测试、护栏或客户端限速，没有执行格式化、lint 或项目测试套件。原始证据留作本次交接，
  一次性编排脚本使用后删除。

[Zerochan 客户端](zerochan.md) · [方法参考](zerochan-api.md) · [能力入口](zerochan-capabilities.md) · [契约审计附注](zerochan-contract-notes.md)
