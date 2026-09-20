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

## 文档字面代码复核（2026-09-18）

本轮直接提取各 Markdown 的 Python 代码块执行，不重新手写一套“等价调用”。每块独立运行，
保留原文代码、stdout、异常和真实响应；API 的字面参数没有替换。为使用同一份覆写配置，仅在临时执行进程
把 `resources.DEFAULT_CONFIG_FILE` 指向内部覆盖配置，包内配置和源文件不改；不使用环境变量，也不加入凭据。
每次请求前按配置等待 `1.2` 秒。需账号、会写入数据或旧 4.x 的代码不执行。

命令形态（路径用占位符表示）：

```bash
.venv/Scripts/python.exe <片段执行脚本> --config <配置文件> --manifest <片段清单> --output <执行记录>
```

### Zerochan：重写后的全部教学片段

`zerochan.md` 的 2 块、`zerochan-api.md` 的 9 块全部执行，合计 **13 次 GET：12×200、1×500**。
11 块代码均正常结束；错误示例捕获了 `AnybooruHTTPError`，并不是把 500 当成成功响应。
首个请求开始于 `2026-09-18T01:11:20.451200+00:00`。

| 字面例子 | 实际 URL（根地址为 `https://www.zerochan.net`） | 真实输出摘要 |
| :--- | :--- | :--- |
| 第一页，`p=1, l=2, s='id'`（用法页及方法页各一次） | `/?p=1&l=2&s=id&json=` | 两次均 200；`4725815 Sin Mal`、`4725814 Sin Mal` |
| 第二页，`p=2, l=2, s='id'` | `/?p=2&l=2&s=id&json=` | 200；`4725810`、`4725809` |
| 原样 JSON，`request('/', params={'l': 2})` | `/?l=2&json=` | 200；顶层键 `['items']`，其中是两张图片的列表 |
| 单标签，`tags='Genshin Impact', l=2` | `/Genshin+Impact?l=2&json=` | 200；`4034550 Genshin Impact`、`3793080 Yae Miko` |
| 多标签，`tags=['Lumine', 'Flower'], l=2` | `/Lumine,Flower?l=2&json=` | 200；`4034550`、`4110668`，返回的 `tags` 包含所查标签 |
| 主标签，`tags='Genshin Impact', strict=True, l=2` | `/Genshin+Impact?l=2&strict=&json=` | 200；两张图的 `tag` 都是 `Genshin Impact`；实际是 `strict=`，不是 `strict=true` |
| 人气窗口，`l=2, s='fav', t=1` | `/?l=2&s=fav&t=1&json=` | 200；`4723740`、`4722756` |
| 人气窗口，`l=2, s='fav', t=2` | `/?l=2&s=fav&t=2&json=` | 200；`4680768`、`4694831` |
| 尺寸，`l=2, d='square'` | `/?l=2&d=square&json=` | 200；`4725807 1006×966`、`4725804 1024×1024` |
| 颜色，`l=2, c='red'` | `/?l=2&c=red&json=` | 200；`4725810`、`4725807`，含 `thumbnail` 图片地址 |
| 图片编号，`entry_show(3793685)` | `/3793685?json=` | 200；`3793685 Yukihana Lamy 2976 4055`，`full` 为该图的完整尺寸地址 |
| 错误，`l=2, s='fav', t=0` | `/?l=2&s=fav&t=0&json=` | 500；打印 `error.http_code`、`error.url` 和 `repr(error.body)` |

错误正文的实际输出仍是 `'{\r\n  "items": [\r\n}\r\n'`，不是合法 JSON。
本轮没有重测不传 `l` 的默认条数；上次观察到的 48 条保留为历史事实，不写成页面保证。

四份 Zerochan 文档的相对链接审计：**28 个相对链接、其中 7 个片段锚点、0 个缺失**。
实际执行 `.venv/Scripts/python.exe <链接审计脚本> --output <记录文件> docs/zerochan.md docs/zerochan-api.md docs/zerochan-capabilities.md docs/zerochan-contract-notes.md`，退出 `0`。

### 其余文档：已执行范围与停止点

下列记录均在用户要求停止新增执行前完成；随后停止所有后续请求和核对，没有补跑行内示例。
命令均为 `.venv/Scripts/python.exe <片段执行脚本> --config <配置文件> --manifest <片段清单> --output <记录文件>`。

| 批次 | 已记录的实际结果 |
| :--- | :--- |
| 首批（Zerochan、e621ng、Moebooru、Serika） | 102 次调用收到 HTTP：97×200、1×400、3×404、1×500。Moebooru v2 例子另有一次 Python `KeyError: pools`，原因是例子误以为未请求的字段也会返回；不是 HTTP 失败 |
| 续批（修正例子、共享指南、README、Danbooru） | 33×200、1×404 |
| 补跑未取得响应的块 | 38×200、1×403、1×404、2×500；27 块正常结束。其余为两组排序查询 500、笔记预览 403，以及用户搜索 200 空列表后旧例子下标越界 |

关键响应与修正：

* e621ng 的31个匿名代码块全部正常结束，HTTP为30×200和1×404。
  `/posts.json?tags=rating%3As&limit=2` 返回6715278/6715276；`/posts/0.json` 返回404和
  `{"success":false,"reason":"not found"}`。按帖子分组的评论即使给 `limit=2` 也返回5个帖子。
* Moebooru：`/post.json?tags=rating%3As&limit=3&api_version=2` 实际只返回 `{"posts": [...]}`，3张图。
  加上 `include_tags=1&include_votes=1&include_pools=1` 后，实际键才是
  `['pool_posts','pools','posts','tags','votes']`。例子修正后已重新执行，正常结束。
  `/post/similar.json?id=1269034` 返回200、`success: true`、0个匹配；指定图片的笔记和评论查询返回空列表。
* Serika：已执行的匿名例子取得正常响应；不存在图片的例子返回404 JSON，8×8随机图例子返回400纯文本。
  普通 `request('GET', 'api/v1/stats')` 的键为 `data/meta/success`；选择 `data` 后才是统计字段。
  补全与搭配标签使用的是只读查询POST，不是写操作；没有使用任何账号或API key。
* Danbooru：两次 `rating:g order:score`（limit 分别为 10 和 2）返回 500，
  `error: ActiveRecord::QueryCanceled`、`message: The database timed out running your query.`。
  `POST /notes/preview.json` 只预览、不保存，但实际返回403、`ActionController::InvalidAuthenticityToken`，
  不能写成成功预览。`/users.json?limit=1&search%5Bname_matches%5D=fuzichoco` 返回200空列表；
  旧例子访问首项时越界，已改为直接显示列表，修改后未重跑。

需要账号或会修改数据的代码均未执行；旧4.x对照块未执行。表格、索引与其它行内用例没有逐条实跑，
未在记录中点名的组合仍为**未实测**。停止后没有再发请求或补做全项目核对。
除Zerochan与e621两组已有相对链接审计外，其余组没有完成本轮全量锚点检查，不宣称全部链接已验证。

## Gelbooru：匿名只读实测（2026-09-18）

本轮没有账号、API key 或登录操作，没有发写请求。Gelbooru 站点上的执行合计 **6 次 GET，6×HTTP 200**：
一个通过新客户端执行的补全请求，以及为核对资料和网页路由读取的四份 HTML、一个 JavaScript 文件。
这不是六个原生方法都成功；五个 dapi 方法均未发送请求。

以下命令中的 `python` 代表实际使用的项目虚拟环境解释器，配置和一次性读取工具的路径以占位符呈现；
URL 和调用参数则按真实请求记录，不把占位符命令冒充另一轮执行。

### G1：新客户端的匿名补全示例

实际执行的脚本和参数：

```bash
python examples/gelbooru/autocomplete.py --config <配置文件>
```

开始时间为 `2026-09-18T05:35:23.029Z`，进程退出 `0`，stderr 为空。
脚本真实导入 `from anybooru import Gelbooru`，站点条目里的 `api_key` / `user_id` 都为空；
这次参数对应 `client.autocomplete('blue', type='tag', limit=3)`。

| 实际 URL（GET） | `last_call['status_code']` | 实际结果 |
| :--- | :--- | :--- |
| `https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2` | 200 | JSON 数组，10 项；脚本从 `last_call['url']` 打印此 URL，未附加 `json` 或账号参数 |

脚本输出的前三项如下，其余七项依次为 `blue_sky`、`blue_skirt`、`blue_background`、`blue_dress`、
`blue_bow`、`blue_shirt`、`blue_jacket`：

```json
[
  {"type":"tag","label":"blue eyes","value":"blue_eyes","post_count":"2817483","category":"tag"},
  {"type":"tag","label":"blue hair","value":"blue_hair","post_count":"1362688","category":"tag"},
  {"type":"tag","label":"blue archive","value":"blue_archive","post_count":"454986","category":"copyright"}
]
```

关键差异：**请求 `limit=3`，实际返回 10 项**。所以“limit 是硬性的返回条数上限”不适用于这个响应。
客户端不截断结果；也没有用更多请求推导服务器默认值、最大值或全部 limit 的行为。
`post_count` 保留字符串，`type` 与 `category` 是不同的字段，版权项的 type 仍为 tag。

### G2：资料与 HTML 路由复核

实际执行的读取命令形态：

```bash
python <只读资料抓取脚本> --config <配置文件> --input <来源请求清单> --output <执行记录>
```

进程退出 `0`；按下表顺序各 GET 一次，无重试。下面时间是各响应的 HTTP `Date`（UTC），
字节数是 requests 解码传输压缩后 `response.content` 的长度，不是压缩后的网络流量。

| 实际 URL | HTTP / Content-Type | Date / 正文字节数 | 可核对的内容 |
| :--- | :--- | :--- | :--- |
| `https://gelbooru.com/index.php?page=wiki&s=view&id=18780` | 200 / `text/html; charset=UTF-8` | 05:32:28 / 10388 | 标题 `howto:api`；有认证、Posts/Tag/User/Comments List、Deleted Images；显示更新时间 `02/22/22 4:17 PM`；没有 dapi 响应字段表 |
| `https://gelbooru.com/index.php?page=help&topic=dapi` | 200 / `text/html; charset=UTF-8` | 05:32:30 / 4563 | 页首 `This section is out of date`；post 的 hard limit 100，与 wiki 的 default limit 100 不同 |
| `https://gelbooru.com/script/autocomplete3.js` | 200 / `application/javascript` | 05:32:31 / 11599 | 调用 `/index.php?page=autocomplete2`，发送 term/type/limit；`MAX_RESULTS=10`，读取 label/value/post_count/category 等属性 |
| `https://gelbooru.com/index.php?page=tags&s=list` | 200 / `text/html; charset=UTF-8` | 05:32:32 / 21150 | `Tag Listing` HTML 表格；示例 `1girl`、`general`、计数 `9713939`；翻页链接第二页为 `pid=50`，不能当作 dapi 页码 |
| `https://gelbooru.com/index.php?page=tags&s=implications` | 200 / `text/html; charset=UTF-8` | 05:32:34 / 13336 | 标题 `Tag Implication Listing`；关系含 `crossover_pairing → crossover`、`mechanical_magical_girl → magical_girl` |

这些 HTML 读取只是页面状态与资料复核，不是新增的客户端方法，也没有把 HTML 解析结果当作 dapi JSON。
其它网页的用途与地址列在[能力入口](gelbooru-capabilities.md#网页入口本库不封装)。

### G3：边界与未实测

* `post_list`、`post_deleted`、`tag_list`、`user_list`、`comment_list` **分别均未执行 / 未实测（需账号）**。
  接口路由和参数取自官方页面；JSON 字段名、类型、包装、总数、分页、错误体和认证成功路径没有本轮响应证据。
* 外部综合资料已有“匿名 dapi 401 空正文”的记录，本轮没有重发 dapi，也没有把该记录算入六次请求。
  候选返回字段按 `[推断]` 标明，具体哪项来自文档、哪项仅是推断，见[方法参考](gelbooru-api.md)和[契约附注](gelbooru-contract-notes.md)。
* 其它补全种类、空值、未知 type、空格输入、别名项、limit 边界和其它站点未实测；没有为了补齐数量遍历端点或换网络重跑。
* 没有下载图片、抓取登录态、读取账号凭据或执行任何写操作。没有新增测试、checksum、护栏、重试，
  未运行 formatter、lint、项目测试套件、分发包构建或发布；这轮证据仅限上述真实读取。

[Gelbooru 客户端](gelbooru.md) · [方法参考](gelbooru-api.md) · [能力入口](gelbooru-capabilities.md) · [契约附注](gelbooru-contract-notes.md)


## Gelbooru：有界匿名扩展实测（2026-09-18）

在上一批基础上按明确清单再执行 **35 次 GET：27×200、5×401、3×302**，每项一次。
清单展开为 13 个补全查询、5 个 dapi 读取、14 个 HTML 路由和 3 个图片 CDN 地址；无额外探测、无重试、无网络切换。
请求结束后等待配置的 **1.2 秒**再开始下一项；记录中的最小结束至下次开始间隔为 **1.201 秒**。
所有请求匿名，只使用 gelbooru.com 及指定的 img4.gelbooru.com，没有登录、凭据或写请求。

执行命令形态（python 代表项目虚拟环境解释器，内部路径以占位符表示）：

```bash
python <匿名只读执行脚本> --config <配置文件> --input <请求清单> --output <执行记录>
```

开始 `2026-09-18T06:38:45.036377+00:00`，结束 `2026-09-18T06:39:50.260422+00:00`，进程退出 0。
异常被逐项记录后继续清单，不代表把 401 当成功；没有网络异常或无 HTTP 响应的项。
下面与上一批独立记账，历史数字与历史“未执行”状态没有改写。

### G4：补全种类与空值边界

13 次均为 200、`application/json`，均发 `limit=3`。下表的首项字段来自真实响应，而非按请求 type 构造。

| 实际 URL（GET） | HTTP | 返回条数 | 首项关键字段 |
| :--- | :--- | :--- | :--- |
| `https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2` | 200 | 10 | `{"type":"tag","label":"blue eyes","value":"blue_eyes","post_count":"2817587","category":"tag"}` |
| `https://gelbooru.com/index.php?type=tag_query&limit=3&term=blue&page=autocomplete2` | 200 | 10 | `{"type":"tag","label":"blue eyes","value":"blue_eyes","post_count":"2817587","category":"tag"}` |
| `https://gelbooru.com/index.php?type=artist&limit=3&term=fuzichoco&page=autocomplete2` | 200 | 3 | `{"type":"tag","label":"fuzichoco","value":"fuzichoco","post_count":"1017","category":"artist"}` |
| `https://gelbooru.com/index.php?type=pool&limit=3&term=touhou&page=autocomplete2` | 200 | 10 | `{"type":"tag","label":"touhou","value":"touhou","post_count":"1021798","category":"copyright"}` |
| `https://gelbooru.com/index.php?type=user&limit=3&term=lozertuser&page=autocomplete2` | 200 | 1 | `{"type":"tag","label":"lozertuser","value":"lozertuser","post_count":"1","category":"character"}` |
| `https://gelbooru.com/index.php?type=wiki_page&limit=3&term=howto&page=autocomplete2` | 200 | 5 | `{"type":"tag","label":"howtodriveacar","value":"howtodriveacar","post_count":"2","category":"artist"}` |
| `https://gelbooru.com/index.php?type=favorite_group&limit=3&term=touhou&page=autocomplete2` | 200 | 10 | `{"type":"tag","label":"touhou","value":"touhou","post_count":"1021798","category":"copyright"}` |
| `https://gelbooru.com/index.php?type=saved_search_label&limit=3&term=touhou&page=autocomplete2` | 200 | 10 | `{"type":"tag","label":"touhou","value":"touhou","post_count":"1021798","category":"copyright"}` |
| `https://gelbooru.com/index.php?type=mention&limit=3&term=lozertuser&page=autocomplete2` | 200 | 1 | `{"type":"tag","label":"lozertuser","value":"lozertuser","post_count":"1","category":"character"}` |
| `https://gelbooru.com/index.php?type=tag&limit=3&term=&page=autocomplete2` | 200 | 0 | `[]`，没有首项 |
| `https://gelbooru.com/index.php?type=tag&limit=3&term=hatsune+miku&page=autocomplete2` | 200 | 0 | `[]`，没有首项 |
| `https://gelbooru.com/index.php?type=taq&limit=3&term=blue&page=autocomplete2` | 200 | 10 | `{"type":"tag","label":"blue eyes","value":"blue_eyes","post_count":"2817587","category":"tag"}` |
| `https://gelbooru.com/index.php?type=wiki&limit=3&term=blue&page=autocomplete2` | 200 | 10 | `{"type":"tag","label":"blue eyes","value":"blue_eyes","post_count":"2817587","category":"tag"}` |

* 九个脚本枚举值均已请求，但**所有非空项的返回 type 都是 tag**。artist=fuzichoco 甚至包含 character 与普通 tag 分类项；user=lozertuser 返回的是 category=character 的标签，不是用户对象。
* pool/favorite_group/saved_search_label 配 touhou 得到标签建议，wiki_page 配 howto 得到 howtodriveacar 等标签，不是池、收藏组、保存搜索或 wiki 条目。只能证明这些输入取得上述响应，不能宣称那些独立资源的补全成功。
* 拼错的 taq 与未列入脚本枚举的 wiki 配 blue 都返回 10 个标签建议，不是外部资料所说的空数组；这是服务器的响应，客户端没有替换 type 或切换接口。
* 空 term 和空格写法 hatsune miku 均返回空数组，与外部资料一致；没有再补发下划线写法作对照。
* 请求 limit=3 可得到 10、5、3、1、0 项，不能保证最多三项，也不能由此断言服务端对全部 limit 的算法。

### G5：五个 dapi 方法的匿名拒绝

通过原生方法实际执行；构造器显式给 `api_key=''`、`user_id=''`，URL 不含凭据。

| 调用 | 实际 URL（GET） | HTTP / 异常 / 正文 |
| :--- | :--- | :--- |
| `post_list(limit=1)` | `https://gelbooru.com/index.php?limit=1&s=post&q=index&page=dapi&json=1` | 401 / `AnybooruHTTPError` / 0 字节 |
| `tag_list(limit=1)` | `https://gelbooru.com/index.php?limit=1&s=tag&q=index&page=dapi&json=1` | 401 / `AnybooruHTTPError` / 0 字节 |
| `user_list(limit=1)` | `https://gelbooru.com/index.php?limit=1&s=user&q=index&page=dapi&json=1` | 401 / `AnybooruHTTPError` / 0 字节 |
| `comment_list(post_id=1)` | `https://gelbooru.com/index.php?post_id=1&s=comment&q=index&page=dapi&json=1` | 401 / `AnybooruHTTPError` / 0 字节 |
| `post_deleted(last_id=0)` | `https://gelbooru.com/index.php?last_id=0&s=post&q=index&deleted=show&page=dapi&json=1` | 401 / `AnybooruHTTPError` / 0 字节 |

五次均为 `Content-Type: text/html; charset=UTF-8`；异常的 `http_code=401`、`body=''`、`data=None`，
响应体为空，不是错误 JSON。每次 `last_call` 都含 `API='dapi'`、表内 URL、`status_code=401`、
`status='Unauthorized'` 和真实响应头；没有误抛 JSON 解析异常，也没有返回成功空数组。
这确认了外部资料的匿名 401 边界，**没有验证任何 dapi 成功响应字段或认证成功路径**。

### G6：HTML 路由可访问性

只读状态与响应头，不解析页面内容；GET 使用 `Accept: text/html`、不跟随跳转。
14 项均为 200，Content-Type 均为 `text/html; charset=UTF-8`。这里的“可达”只指收到 HTTP 200，
不是对页面内容完整性或各表单功能的验证。

| 实际 URL（GET） | HTTP | 结果 |
| :--- | :--- | :--- |
| `https://gelbooru.com/index.php?page=tags&s=list` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=tags&s=implications` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=alias&s=list` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=post&s=list&tags=1girl` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=post&s=view&id=1` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=wiki&s=list&search=howto` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=wiki&s=view&id=18780` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=pool&s=list` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=artist&s=list` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=comment&s=list` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=forum&s=list` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=tracker&s=list` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=extras&s=artists` | 200 | HTML 响应可达；未解析内容 |
| `https://gelbooru.com/index.php?page=help&topic=dapi` | 200 | HTML 响应可达；未解析内容 |

### G7：图片 CDN 初始响应

对给定三个地址各 GET 一次，`allow_redirects=False`；使用流式响应只记录头，不读取或保存媒体正文。
没有请求 Location 目标，不能声称跟随后取得图片。

| 实际 URL（GET） | HTTP | Location |
| :--- | :--- | :--- |
| `https://img4.gelbooru.com/images/f3/82/f3824ad985f121187065c4eaeae22875.jpg` | 302 | `https://gelbooru.com/hotlink.php?hash=/images/f3/82/f3824ad985f121187065c4eaeae22875.jpg` |
| `https://img4.gelbooru.com/thumbnails/f3/82/thumbnail_f3824ad985f121187065c4eaeae22875.jpg` | 302 | `https://gelbooru.com/hotlink.php?hash=/thumbnails/f3/82/thumbnail_f3824ad985f121187065c4eaeae22875.jpg` |
| `https://img4.gelbooru.com/samples/f3/82/sample_f3824ad985f121187065c4eaeae22875.jpg` | 302 | `https://gelbooru.com/hotlink.php?hash=/samples/f3/82/sample_f3824ad985f121187065c4eaeae22875.jpg` |

三项均为 302，目标是 gelbooru.com 的 hotlink.php，符合资料的初始跳转状态。
原图与样例响应另带 `Retry-After: 10`、`X-RateLimit-Limit: 100`；本轮不重试，不能仅凭这两个头
把 302 断定为限流或推出配额周期。

### G8：本轮后仍未实测

* dapi 的认证成功、JSON 字段/类型/外层、分页、排序、过滤、非认证错误体和配额仍未实测；候选字段仍是推断。
* 补全返回中没有经确认的 user/pool/wiki 等专用对象、antecedent 别名样本或 name/level 样本；其它 term、缺省 type、limit 边界未覆盖。
* HTML 只记录 HTTP 状态和类型，未解析网页或执行表单；CDN 未跟随跳转、未确认目标响应或图片内容，也未验证普遍地址规律。
* 没有账号、写操作、其它部署、网络切换或重试；没有新增测试/checksum、运行格式化/lint/项目套件/构建。

[客户端用法](gelbooru.md) · [方法参考](gelbooru-api.md) · [网页可达性](gelbooru-capabilities.md#网页入口本库不封装) · [依据与差异](gelbooru-contract-notes.md)


## 轻量匿名冒烟脚本：十站单轮执行（2026-09-18）

新增的 `test/<站点>.py` 各执行一次，没有为了让结果变绿而重跑。全部使用项目虚拟环境，按
`smoke.pause_seconds=1.2` 在请求之间暂停；命令里的 `<配置文件>` 是本机覆盖配置的公开占位。
所有构造器显式匿名（Zerochan 本来就没有凭据参数），十条命令均成功导入、读取配置和构造客户端。

**合计 39 次 GET，全部收到 HTTP 响应：23×200、7×预期404、5×预期401、2×403、2×301。**
8 个脚本退出 0，2 个退出 1；所有 stderr 均为空。脚本不重试、不跟随重定向、不登录、不写入、
不下载媒体，实际请求数全部低于每文件 10 次上限。

### 命令、次数与退出码

| 实际脚本命令（配置路径以占位符表示） | 请求数 | 退出码 | 本轮结果 |
| :--- | ---: | ---: | :--- |
| `.venv/Scripts/python.exe test/gelbooru.py --config <配置文件>` | 6 | 0 | 1×200、5×401 |
| `.venv/Scripts/python.exe test/serika.py --config <配置文件>` | 5 | 0 | 4×200、1×404 |
| `.venv/Scripts/python.exe test/zerochan.py --config <配置文件>` | 4 | 0 | 3×200、1×404 |
| `.venv/Scripts/python.exe test/danbooru.py --config <配置文件>` | 4 | 0 | 3×200、1×404 |
| `.venv/Scripts/python.exe test/safebooru.py --config <配置文件>` | 4 | 0 | 3×200、1×404 |
| `.venv/Scripts/python.exe test/e621.py --config <配置文件>` | 4 | 0 | 3×200、1×404 |
| `.venv/Scripts/python.exe test/e926.py --config <配置文件>` | 4 | 0 | 3×200、1×404 |
| `.venv/Scripts/python.exe test/konachan.py --config <配置文件>` | 2 | 1 | 2×403 |
| `.venv/Scripts/python.exe test/yandere.py --config <配置文件>` | 4 | 0 | 3×200、1×404 |
| `.venv/Scripts/python.exe test/sakugabooru.py --config <配置文件>` | 2 | 1 | 2×301 |

### 逐检查的真实 URL 与输出

下列摘要来自脚本 stdout；动态 ID、计数和文件大小只是此次快照。`setup` 不发 HTTP，未计入次数。
Konachan 与 Sakugabooru 的列表失败后，各自跳过了详情与第二页，四个 SKIP 均没有发请求。

| 站点 / 检查 | 真实 URL | HTTP / 判定 | 观察到的字段或条数 |
| :--- | :--- | :--- | :--- |
| gelbooru / `autocomplete` | `https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2` | HTTP 200 / PASS | `count=10 requested_limit=3 first=blue_eyes post_count='2817625'; type:str,label:str,value:str,post_count:str,category:str` |
| gelbooru / `posts.anonymous_denied` | `https://gelbooru.com/index.php?limit=2&s=post&q=index&page=dapi&json=1` | HTTP 401 AnybooruHTTPError (expected) / PASS | `anonymous access denied as expected; body_chars=0 data=None` |
| gelbooru / `tags.anonymous_denied` | `https://gelbooru.com/index.php?limit=2&s=tag&q=index&page=dapi&json=1` | HTTP 401 AnybooruHTTPError (expected) / PASS | `anonymous access denied as expected; body_chars=0 data=None` |
| gelbooru / `users.anonymous_denied` | `https://gelbooru.com/index.php?limit=2&s=user&q=index&page=dapi&json=1` | HTTP 401 AnybooruHTTPError (expected) / PASS | `anonymous access denied as expected; body_chars=0 data=None` |
| gelbooru / `comments.anonymous_denied` | `https://gelbooru.com/index.php?post_id=1&s=comment&q=index&page=dapi&json=1` | HTTP 401 AnybooruHTTPError (expected) / PASS | `anonymous access denied as expected; body_chars=0 data=None` |
| gelbooru / `deleted.anonymous_denied` | `https://gelbooru.com/index.php?last_id=0&s=post&q=index&deleted=show&page=dapi&json=1` | HTTP 401 AnybooruHTTPError (expected) / PASS | `anonymous access denied as expected; body_chars=0 data=None` |
| serika / `api_index` | `https://serika.art/api/v1` | HTTP 200 / PASS | `name:str,version:str; name=SerikaART API version=1.0.0` |
| serika / `internal_image_list page 1` | `https://serika.art/api/images?page=1&limit=2&ratings=safe&sort=newest` | HTTP 200 / PASS | `success:bool,images:list,pagination:dict; images=2 post_ids=[4237836, 4237835] pagination:page:int,limit:int,total:int,pages:int,has_next:bool total=3499663 pages=1749832 has_next=True` |
| serika / `internal_image_show first post_id` | `https://serika.art/api/images/4237836` | HTTP 200 / PASS | `id:int,post_id:int,rating:str,url:str; id=7323837 post_id=4237836 rating=safe url=https://cdn.serika.art/uploads/1788013605888-1788013605888-1q2b2g-danbooru-12074741.png` |
| serika / `internal_image_list page 2` | `https://serika.art/api/images?page=2&limit=2&ratings=safe&sort=newest` | HTTP 200 / PASS | `success:bool,images:list,pagination:dict; images=2 post_ids=[4237834, 4237833] pagination:page:int,limit:int,total:int,pages:int,has_next:bool total=3499663 pages=1749832 has_next=True` |
| serika / `internal_image_show missing id` | `https://serika.art/api/images/0` | HTTP 404 AnybooruHTTPError (expected) / PASS | `AnybooruHTTPError; body_chars=43 data=dict` |
| zerochan / `entry_list page 1` | `https://www.zerochan.net/?p=1&l=2&s=id&json=` | HTTP 200 / PASS | `entries=2 page=1 ids=[4725835, 4725833]` |
| zerochan / `entry_show first id` | `https://www.zerochan.net/4725835?json=` | HTTP 200 / PASS | `id:int,primary:str,full:str,width:int,height:int,size:int,tags:list; id=4725835 primary=Phoenix (Zenless Zone Zero) size=3299328 full=https://static.zerochan.net/Phoenix.%28Zenless.Zone.Zero%29.full.4725835.png` |
| zerochan / `entry_list page 2` | `https://www.zerochan.net/?p=2&l=2&s=id&json=` | HTTP 200 / PASS | `entries=2 page=2 ids=[4725832, 4725829]` |
| zerochan / `entry_show missing id` | `https://www.zerochan.net/999999999?json=` | HTTP 404 AnybooruHTTPError (expected) / PASS | `AnybooruHTTPError; body_chars=6 data=dict` |
| danbooru / `post_list` | `https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=2` | HTTP 200 / PASS | `ids=[12213214, 12213213] rating=g` |
| danbooru / `post_show` | `https://danbooru.donmai.us/posts/12213214.json` | HTTP 200 / PASS | `id:int,rating:str,tag_string:str tags=28` |
| danbooru / `post_list_cursor` | `https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=2&page=b12213213` | HTTP 200 / PASS | `cursor=12213213 ids=[12213212, 12213209]` |
| danbooru / `post_show_missing` | `https://danbooru.donmai.us/posts/0.json` | HTTP 404 AnybooruHTTPError (expected) / PASS | `success=false error=ActiveRecord::RecordNotFound` |
| safebooru / `post_list` | `https://safebooru.donmai.us/posts.json?tags=rating%3Ag&limit=2` | HTTP 200 / PASS | `ids=[12213214, 12213213] rating=g` |
| safebooru / `post_show` | `https://safebooru.donmai.us/posts/12213214.json` | HTTP 200 / PASS | `id:int,rating:str,tag_string:str tags=28` |
| safebooru / `post_list_cursor` | `https://safebooru.donmai.us/posts.json?tags=rating%3Ag&limit=2&page=b12213213` | HTTP 200 / PASS | `cursor=12213213 ids=[12213212, 12213209]` |
| safebooru / `post_show_missing` | `https://safebooru.donmai.us/posts/0.json` | HTTP 404 AnybooruHTTPError (expected) / PASS | `success=false error=ActiveRecord::RecordNotFound` |
| e621 / `post_list` | `https://e621.net/posts.json?tags=rating%3As&limit=2` | HTTP 200 / PASS | `ids=[6715854, 6715833] rating=s` |
| e621 / `post_show` | `https://e621.net/posts/6715854.json` | HTTP 200 / PASS | `id:int,rating:str file=png 2048x2048 size=2452927 url=set tags=9 categories, general=33` |
| e621 / `post_list_cursor` | `https://e621.net/posts.json?tags=rating%3As&limit=2&page=b6715833` | HTTP 200 / PASS | `cursor=6715833 ids=[6715826, 6715823]` |
| e621 / `post_show_missing` | `https://e621.net/posts/0.json` | HTTP 404 AnybooruHTTPError (expected) / PASS | `success=false reason=not found` |
| e926 / `post_list` | `https://e926.net/posts.json?tags=rating%3As&limit=2` | HTTP 200 / PASS | `ids=[6715854, 6715833] rating=s` |
| e926 / `post_show` | `https://e926.net/posts/6715854.json` | HTTP 200 / PASS | `id:int,rating:str file=png 2048x2048 size=2452927 url=set tags=9 categories, general=33` |
| e926 / `post_list_cursor` | `https://e926.net/posts.json?tags=rating%3As&limit=2&page=b6715833` | HTTP 200 / PASS | `cursor=6715833 ids=[6715826, 6715823]` |
| e926 / `post_show_missing` | `https://e926.net/posts/0.json` | HTTP 404 AnybooruHTTPError (expected) / PASS | `success=false reason=not found` |
| konachan / `post_list page 1` | `https://konachan.com/post.json?tags=rating%3As&page=1&limit=2&api_version=2` | HTTP 403 / FAIL | `ValueError: expected HTTP 200; AnybooruHTTPError; body_chars=5689` |
| konachan / `comment_show 0` | `https://konachan.com/comment/show.json?id=0` | HTTP 403 / FAIL | `ValueError: expected HTTP 404; AnybooruHTTPError; body_chars=5505` |
| yandere / `post_list page 1` | `https://yande.re/post.json?tags=rating%3As&page=1&limit=2&api_version=2` | HTTP 200 / PASS | `posts=2 ids=[1269052, 1269049] id:int,rating:str,tags:str,width:int,height:int` |
| yandere / `post_list id:1269052` | `https://yande.re/post.json?tags=id%3A1269052&limit=2&api_version=2` | HTTP 200 / PASS | `posts=1 selected_id=1269052 id:int,rating:str,tags:str,width:int,height:int` |
| yandere / `post_list page 2` | `https://yande.re/post.json?tags=rating%3As&page=2&limit=2&api_version=2` | HTTP 200 / PASS | `posts=2 ids=[1269048, 1269047] earlier_than=1269049` |
| yandere / `comment_show 0` | `https://yande.re/comment/show.json?id=0` | HTTP 404 AnybooruHTTPError (expected) / PASS | `AnybooruHTTPError; data=None; body_chars=550` |
| sakugabooru / `post_list page 1` | `https://sakugabooru.com/post.json?tags=rating%3As&page=1&limit=2&api_version=2` | HTTP 301 / FAIL | `ValueError: expected HTTP 200; AnybooruHTTPError; body_chars=162` |
| sakugabooru / `comment_show 0` | `https://sakugabooru.com/comment/show.json?id=0` | HTTP 301 / FAIL | `ValueError: expected HTTP 404; AnybooruHTTPError; body_chars=162` |

### 失败的含义与本轮边界

* **Konachan**：列表与缺失评论均为 `403`，所以退出 1，详情与分页因此未发。该站的拒绝随网络环境变化，
  不能据此断言 API 改版、客户端 bug 或站点不可用。
* **Sakugabooru**：两个初始响应均为 `301`。脚本为控制请求数不跟随任何重定向，所以 200/404 检查失败、
  详情与分页未发。历史 `200` 记录没有逐一列出初始跳转，**不足以证明最近发生站点改版或 API 不可用**；
  也没有请求跳转目标或把 301 改判为通过。
* **Zerochan**：新增缺失条目基线 `/999999999?json=` 实际 `404`，`AnybooruHTTPError.data` 为字典、
  正文 6 字符。此前仅是脚本假设，这次取得真实响应。列表/详情/分页的字段类型与已有记录相符。
* **其余成功项**：Danbooru 的 `tag_string` 仍是字符串；e621 的 `tags` 仍是分类对象、`file` 是嵌套对象；
  yande.re 的 v2 返回含 `posts`，不误要求未请求的 tags/pools/votes；Serika 详情继续使用公开 `post_id`；
  Gelbooru `post_count` 仍为字符串，`limit=3` 仍返回 10 个建议，五个 dapi 均为 401 空正文的预期匿名拒绝。
  未在这些小样本中发现字段漂移或真实库 bug。

没有测试框架、mock、CI 请求、格式化、lint、项目套件、构建或发布。`MANIFEST.in` 已声明把 `test/*.py`
带入源码分发包；`setup.cfg` 的包清单不变，脚本不作为 wheel 包模块。本轮未构建归档核验入包结果。
未再执行默认配置的联网、账号成功/写路径、媒体读取、Sakugabooru 跳转后行为、完整 API / 参数矩阵或
其它解释器版本。上述 39 次即本轮全部请求。

### Konachan 与 Sakugabooru 的实际响应（2026-09-18）

`konachan.com` 四项检查全部取得预期响应；`sakugabooru.com` 的列表与缺失评论初始响应都是 `301`。

| 检查 | 真实 URL | HTTP | 真实摘要 |
| :--- | :--- | :--- | :--- |
| `post_list page 1` | `https://konachan.com/post.json?tags=rating%3As&page=1&limit=2&api_version=2` | 200 | `posts=2 ids=[408602, 408601] id:int,rating:str,tags:str,width:int,height:int` |
| `post_list id:408602` | `https://konachan.com/post.json?tags=id%3A408602&limit=2&api_version=2` | 200 | `posts=1 selected_id=408602 id:int,rating:str,tags:str,width:int,height:int` |
| `post_list page 2` | `https://konachan.com/post.json?tags=rating%3As&page=2&limit=2&api_version=2` | 200 | `posts=2 ids=[408600, 408599] earlier_than=408601` |
| `comment_show 0` | `https://konachan.com/comment/show.json?id=0` | 404 | `AnybooruHTTPError; error={'status': 404, 'error': 'Not Found'}` |
| `post_list page 1` | `https://sakugabooru.com/post.json?tags=rating%3As&page=1&limit=2&api_version=2` | 301 | 未跟随重定向，判定失败 |
| `comment_show 0` | `https://sakugabooru.com/comment/show.json?id=0` | 301 | 未跟随重定向，判定失败 |

**Konachan 的错误体判据已更正**：早期脚本把 yande.re 的“404 正文是 HTML、`data` 为 `None`”要求套到了
Konachan，所以那条检查一直失败。Konachan 的真实响应是 `404` 加一个 JSON 对象，判据现为：**HTTP `404`、
正文是 JSON 对象、含 `status`（int 且等于 404）与 `error`（str）**；不锁死英文文案，也不接受 HTML、
空正文或错误状态值。字段来自一次真实观测的响应体，固定字段后**未再联网复跑**，只用保存的响应做过
离线核对（真样本通过、把 `status` 改成 `200` 的样本被拒）。

**Sakugabooru 仍是失败**：`301` 不满足脚本要求的 `200`/`404`，为控制请求数不跟随任何重定向，所以详情与
第二页没有执行，跳转目标后的 API 是否正常仍未验证。`test/yandere.py` 与 `test/sakugabooru.py` 的判据
都没有改。

## Shuushuu 匿名只读实测（2026-09-19）

e-shuushuu 接入后的真实客户端调用，不是把收到的旧接口记录改名为本轮结果。执行时间为
**UTC 2026-09-18 18:14:29–18:15:18**；本节标题用执行者当地日期，保留原始UTC时间。
站点自带 `GET https://e-shuushuu.net/api/openapi.json` 另取到 **200、application/json**，
自称 `Shuushuu API 2.0.0`、OpenAPI `3.1.0`；它是接口依据，不计入下面18次资源请求。

### 命令与总结果

命令中的 `my-anybooru.json` 是实际覆盖配置路径的中性写法：从当前包内配置复制，仅使用自己的网络设置，
没有凭据；公开记录不刊登维护者的配置路径或网络出口。`-X utf8` 固定终端输出编码。

```bash
.venv/Scripts/python.exe -c "import anybooru; print(anybooru.Shuushuu); c = anybooru.Shuushuu('shuushuu'); print(c.site_url, repr(c.username), repr(c.password), repr(c.access_token), c.last_call); c.close()"
.venv/Scripts/python.exe -X utf8 test/shuushuu.py --config my-anybooru.json
.venv/Scripts/python.exe -X utf8 examples/shuushuu/search_images.py --config my-anybooru.json
.venv/Scripts/python.exe -X utf8 examples/shuushuu/browse_resources.py --config my-anybooru.json
```

| 命令 | 退出码 | HTTP尝试 | 结果 |
| :--- | ---: | ---: | :--- |
| 导入与默认构造 | 0 | 0 | `<class 'anybooru.shuushuu.Shuushuu'>`；站点 `https://e-shuushuu.net`，用户名/密码/token都是空字符串，`last_call={}` |
| `test/shuushuu.py` | 0 | 10 | 8×200、预期422一次、预期404一次；`SUMMARY shuushuu \| requests=10 \| passed=10 failed=0` |
| `search_images.py` | 0 | 4 | 4×200；标签名换ID、两页筛图、第一张详情 |
| `browse_resources.py` | 0 | 4 | 4×200；标签详情、指定图片评论、用户搜索、新闻 |

四条命令的stderr均为空。资源请求合计 **18次：16×200 + 1×422 + 1×404**；两个错误是预期边界，
没有意外失败或SKIP。冒烟每次输出 `PASS`、URL、状态和字段摘要；末行如上。没有登录或账号相关调用。

### 十次冒烟请求

| 检查 | 实际URL | HTTP | 实际返回与判定 |
| :--- | :--- | ---: | :--- |
| 标签搜索 | `https://e-shuushuu.net/api/v1/search?q=long+hair&limit=2` | 200 | `entity='tags'`、`hits=2`、`total=4`，首项 `tag_id=46, title='long hair'`；有 `query/limit/offset` |
| 标签列表 | `https://e-shuushuu.net/api/v1/tags?search=long+hair&per_page=2` | 200 | `total=2, per_page=2`，标题 `long hair` / `Somali Longhaired`，每项有编号、类型、使用次数和别名标记 |
| 逗号串筛图与重复状态 | `https://e-shuushuu.net/api/v1/images?tags=46%2C169&tags_mode=all&tag_depth=0&per_page=2&sort_by=favorites&sort_order=DESC&status=1&status=2&include_comments=false` | 200 | `total=189767, page=1, per_page=2`，图片 `[186447,235604]`；两项的 `tags` 均含46和169 |
| 列表首张详情 | `https://e-shuushuu.net/api/v1/images/186447` | 200 | `image_id=186447` 与所选编号一致，`favorites=306`、31个标签，仍含46和169；MD5 `07301ff8a4dd743ce2d2f60f12fed188` |
| 标签详情 | `https://e-shuushuu.net/api/v1/tags/46` | 200 | `title='long hair', usage_count=729799, total_image_count=722909`，有 `child_count/aliases/links/sources/characters` |
| 图片评论 | `https://e-shuushuu.net/api/v1/comments?image_id=1118862&per_page=2` | 200 | `total=1`，评论 `post_id=629189`，`image_id` 与过滤条件一致；`post_text/post_text_html` 均为字符串 |
| 图片统计 | `https://e-shuushuu.net/api/v1/images/stats/summary` | 200 | `total_images=1102275, total_favorites=5757425, average_rating=3.76` |
| 站点限制 | `https://e-shuushuu.net/api/v1/meta/config` | 200 | `max_search_tags=5, max_image_size=33554432, search_delay_seconds=2`，`tag_types` 有5项，尺寸/冷却/ML开关字段类型符合检查 |
| 每页上限越界 | `https://e-shuushuu.net/api/v1/images?per_page=101` | 422 | 抛 `AnybooruHTTPError`，JSON的 `detail[].loc=['query','per_page']`，`type='less_than_equal'`、`ctx.le=100`；正文147字符 |
| 不存在的图片 | `https://e-shuushuu.net/api/v1/images/999999999` | 404 | 抛 `AnybooruHTTPError`，JSON的 `detail` 是15字符字符串，正文28字符；没有改成空列表 |

这轮证明 `%2C` 逗号串、`status=1&status=2` 重复键与小写布尔值被实际发送；不证明状态组合所有可见性规则。
没有再发 `tags=1+2` 对照请求；该错误写法会静默丢过滤的依据仍是收到的既有记录（T）。

### 两个匿名示例

`search_images.py` 按名称查到46再分页，不把46硬编码在脚本里：

| 方法 | 实际URL | HTTP | 实际摘要 |
| :--- | :--- | ---: | :--- |
| `search` | `https://e-shuushuu.net/api/v1/search?q=long+hair&limit=5` | 200 | `hits=4,total=4,entity='tags'`；精确标题 `long hair` 的编号46、使用次数729799 |
| `image_list` 页1 | `https://e-shuushuu.net/api/v1/images?tags=46&page=1&tags_mode=all&tag_depth=0&per_page=2&sort_by=favorites&sort_order=DESC` | 200 | `total=722909`，图片 `[186447,1101184]` |
| `image_list` 页2 | `https://e-shuushuu.net/api/v1/images?tags=46&page=2&tags_mode=all&tag_depth=0&per_page=2&sort_by=favorites&sort_order=DESC` | 200 | `total=722909,page=2`，图片 `[341978,186949]` |
| `image_show` | `https://e-shuushuu.net/api/v1/images/186447` | 200 | 2459×2504，收藏306，标签31；原图字段 `https://cdn.e-shuushuu.net/fullsize/2009-08-09-186447.png`，缩略图字段 `https://cdn.e-shuushuu.net/thumbs/2009-08-09-186447.webp` |

`browse_resources.py` 的四个请求：

| 方法 | 实际URL | HTTP | 实际摘要 |
| :--- | :--- | ---: | :--- |
| `tag_show` | `https://e-shuushuu.net/api/v1/tags/46` | 200 | `type=1,title='long hair',usage_count=729799,total_image_count=722909`；`aliases/links/sources/characters` 都是空数组 |
| `comment_list` | `https://e-shuushuu.net/api/v1/comments?image_id=1118862&per_page=2` | 200 | `post_id=629189`，作者 `whitekitten`，`date='2026-09-11T03:20:03Z'`，正文487字符 |
| `user_list` | `https://e-shuushuu.net/api/v1/users?search=whitekitten&per_page=2` | 200 | `total=1`，用户59006，上传22533、收藏8728、`active=true` |
| `news_list` | `https://e-shuushuu.net/api/v1/news?per_page=1` | 200 | `total=32`，新闻41，标题 `Tag suggestions`，作者 `anonymous_object`，`date='2026-07-09T01:08:13Z'`，正文404字符 |

### 边界与未实测

- 成功覆盖10个公开资源方法，不等于35个公开读取入口逐一跑过。其余历史、关联资源、相似图、hash查重、权限表等只有OpenAPI及明确标出的既有记录依据。
- 五个 `auth_*` 方法和私有 `user_ratings` 完全未调用；登录、refresh Cookie轮换、Bearer成功路径、账号写操作、上传、收藏、评论写入、私信和admin均未实测。
- 媒体URL只从JSON字段读出，没有请求CDN、没有下载图像，没有复测受保护媒体路由的302或跳转目标。
- 没有复测 `tag_images(46)` 与另两个计数入口的差异，没有用本轮暂时相同的722909否定T记录的不同统计口径。
- 只读请求成功不代表冷却参数被API强制执行、没有Cloudflare限制或长期可用；没有探测限流、重试、其它身份或部署。
- 没有运行格式化、lint、项目级测试套件、构建、安装归档或CI。只证明本节命令与请求，不扩写为发布验证。

## Gelbooru02/TBIB：匿名只读实测（2026-09-19）

### 引擎身份与格式证据

`https://tbib.org/` 的 HTML 正文明写 **`Running Gelbooru 0.2`**，没有 generator meta 或更细的补丁版本号。
这是站点自述，不是从页面外观或第三方资料猜测。帮助页列出旧式 `index.php?page=dapi` 路由；
静态路径包括 `script/application.js.php?1`、`script/awesomplete.min.js?v5`，这些资源参数不是引擎版本号。
没有取得服务端源码，不能确定具体提交或全部同族部署的契约。

以下均为匿名 GET 的真实响应；`Content-Type` 按响应头保留，即使它与正文格式不一致。

| 实际 URL | HTTP | Content-Type | 正文结构与关键事实 |
| :--- | ---: | :--- | :--- |
| `https://tbib.org/` | 200 | `text/html; charset=UTF-8` | HTML；页脚自述 `Running Gelbooru 0.2` |
| `https://tbib.org/index.php?page=help` | 200 | `text/html; charset=UTF-8` | 站点帮助 HTML |
| `https://tbib.org/index.php?page=post&s=list&tags=rating%3Asafe&pid=0` | 200 | `text/html; charset=UTF-8` | 帖子列表 DOM、`class="preview"`；不是 dapi JSON |
| `https://tbib.org/index.php?page=help&topic=dapi` | 200 | `text/html; charset=UTF-8` | API Basics；列 `limit/pid/tags/cid/id`，删除流 `last_id`，评论 `post_id` |
| `https://tbib.org/index.php?page=dapi&s=post&q=index&limit=1&tags=rating%3Asafe` | 200 | `text/xml;charset=UTF-8` | `<posts count="7928673" offset="0">`，一个 `<post>`；`id=28627153`、`rating=s`，媒体地址在 XML 属性里 |
| `https://tbib.org/index.php?page=dapi&s=post&q=index&limit=1&tags=rating%3Asafe&json=1` | 200 | `text/html; charset=UTF-8` | JSON 数组一项，`id=28627153`、`rating=safe`；没有根计数和媒体 URL |
| `https://tbib.org/index.php?page=dapi&s=tag&q=index&limit=1` | 200 | `text/xml;charset=UTF-8` | `<tags type="array">`，一条 `<tag id="3145728" name="aphinity" count="2" type="0" ambiguous="false"/>` |
| `https://tbib.org/index.php?page=dapi&s=tag&q=index&limit=1&json=1` | 200 | `text/xml;charset=UTF-8` | 仍是相同 XML 根与标签属性，不是 JSON |
| `https://tbib.org/index.php?page=dapi&s=comment&q=index&post_id=1&limit=1` | 200 | `text/xml;charset=UTF-8` | `<comments type="array"/>`，零子元素 |
| `https://tbib.org/index.php?page=dapi&s=comment&q=index&post_id=1&limit=1&json=1` | 200 | `text/xml;charset=UTF-8` | 仍是空评论 XML，不能据此列非空评论字段 |
| `https://tbib.org/index.php?page=dapi&s=deleted&q=index&limit=1` | 200 | `text/html; charset=UTF-8` | 空正文，不证明存在可用的删除流 |
| `https://tbib.org/index.php?page=dapi&s=deleted&q=index&limit=1&json=1` | 200 | `text/html; charset=UTF-8` | 空正文，不是 JSON 数组 |
| `https://tbib.org/index.php?page=dapi&s=post&q=index&deleted=show&last_id=0&limit=1` | 500 | `text/xml;charset=UTF-8` | 正文仅 `<?xml version="1.0" encoding="UTF-8"?><posts>` 加换行，没有闭合根 |
| `https://tbib.org/index.php?page=dapi&s=post&q=index&deleted=show&last_id=0&limit=1&json=1` | 500 | `text/xml;charset=UTF-8` | 同样是不完整 XML，不改判为空列表 |
| `https://tbib.org/index.php?page=autocomplete&q=blue&limit=1` | 302 | `text/html; charset=UTF-8` | 空正文；`Location: //tbib.org/`，没有取得补全数据 |
| `https://tbib.org/index.php?page=autocomplete&q=blue&limit=1&json=1` | 302 | `text/html; charset=UTF-8` | 空正文；`Location: //tbib.org/` |
| `https://tbib.org/index.php?page=autocomplete2&term=blue&limit=1` | 302 | `text/html; charset=UTF-8` | 空正文；`Location: //tbib.org/` |
| `https://tbib.org/index.php?page=dapi&s=post&q=index&limit=101&tags=rating%3Asafe&json=1` | 200 | `text/html; charset=UTF-8` | JSON 数组 **101 项**；帮助页称 hard limit 100，但该请求没有按 100 截断，真正上限未证实 |
| `https://tbib.org/index.php?page=dapi&s=post&q=index&limit=1&tags=rating%3Asafe&pid=1&json=1` | 200 | `text/html; charset=UTF-8` | JSON 数组一项 `id=28627160`；没有分页元数据 |
| `https://tbib.org/tbib.js?v4=` | 200 | `application/javascript` | 脚本自述 NeverBlock Version 3.2，是广告脚本版本，不是 TBIB 的引擎版本 |

帖子 JSON 实际键为 `directory/hash/height/id/image/change/owner/parent_id/rating/sample/sample_height/sample_width/score/tags/width`。
其中 `sample` 为布尔值，`id/directory/height/width/change/parent_id/sample_height/sample_width/score` 为整数，
其它上述字段为字符串。XML 则保留 `posts` 根的 `count/offset` 和 `post` 的全部属性，包括
`file_url/sample_url/preview_url/md5`；`score`、`parent_id` 在所取 XML 样本里可为空字符串。
客户端不把 XML 属性强转为 JSON 字段、不将 `rating=s` 改成 `safe`、不按 `directory/image/hash` 拼媒体地址。

### 与 gelbooru.com 的差异及既有客户端实测

gelbooru.com 一列沿用其已有实测与官方页面结论，没有为本节调用该站或改写原有家族文档。

| 对比项 | gelbooru.com / `Gelbooru` | TBIB / `Gelbooru02` |
| :--- | :--- | :--- |
| 路由与搜索 | `index.php?page=dapi&s=post&q=index`；帖子 `tags/pid`，删除流 `deleted=show/last_id` | 同形路由；不是 REST `/posts.json`；`q=index` 是动作，不是标签串 |
| 匿名 dapi | 五个原生方法均已观测 401 空正文；账号成功未实测 | 帖子、标签和评论样本 200，无 `api_key/user_id`；删除流 500 |
| JSON 与 XML | 客户端一律请求 dapi `json=1` 并解 JSON；账号成功字段未观测 | 只有帖子取得 JSON 数组；标签与评论带 `json=1` 仍是 XML |
| 补全参数 | `autocomplete2&term=blue` 取得 JSON 建议；`limit=3` 可回 10 条 | `autocomplete&q=blue` 和 `autocomplete2&term=blue` 均 302 到首页 |
| 分页与上限 | 文档列 `pid`；default 100 与旧 help hard 100 的说法未由账号请求验证 | `pid=1,limit=2` 的 XML `offset=2`；JSON 无页码/总数；`limit=101` 回 101，真正上限未知 |

直接把现有 `Gelbooru` 的 `site_url` 指向 TBIB，得到以下结果：

| 方法与真实 URL | HTTP / Content-Type | 现有客户端结果 |
| :--- | :--- | :--- |
| `post_list(limit=1, tags='rating:safe')` → `https://tbib.org/index.php?limit=1&tags=rating%3Asafe&s=post&q=index&page=dapi&json=1` | 200 / `text/html; charset=UTF-8` | 成功返回 JSON 列表 |
| `tag_list(limit=1)` → `https://tbib.org/index.php?limit=1&s=tag&q=index&page=dapi&json=1` | 200 / `text/xml;charset=UTF-8` | 抛 `AnybooruAPIError`，因为正文是 XML |
| `comment_list(1, limit=1)` → `https://tbib.org/index.php?limit=1&post_id=1&s=comment&q=index&page=dapi&json=1` | 200 / `text/xml;charset=UTF-8` | 抛 `AnybooruAPIError`，因为正文是 XML |

因此不是只加一个 `sites` 条目就能复用全部方法。独立 `Gelbooru02` 让帖子默认走 JSON，标签、评论及
显式 XML 帖子返回 `response.text` 原文；不按响应猜格式，也不修复站点返回。用户/账号接口没有调用。

### 已执行命令与客户端结果

以下命令的 `my-anybooru.json` 是用户自己的完整配置文件占位写法；参数与站点条目来自新版包内模板，
没有账号凭据。三份脚本的真实执行时间为 **UTC 2026-09-18 19:58:59–19:59:17**。

```bash
python -X utf8 test/tbib.py --config my-anybooru.json
python -X utf8 examples/gelbooru02/list_posts.py --config my-anybooru.json
python -X utf8 examples/gelbooru02/browse_resources.py --config my-anybooru.json
```

| 脚本 | 退出码 | 实际请求 | 结果 |
| :--- | ---: | ---: | :--- |
| `test/tbib.py` | 0 | 6 | 全部 200；`SUMMARY tbib \| requests=6 \| passed=6 failed=0`，无 SKIP |
| `examples/gelbooru02/list_posts.py` | 0 | 2 | JSON 列表与同帖 XML 均 200 |
| `examples/gelbooru02/browse_resources.py` | 0 | 2 | 标签与空评论 XML 均 200 |

三条命令 stderr 均为空；这十条客户端请求如下，不用 HTTP 200 代替字段检查。

| 调用 | 实际 URL | HTTP / Content-Type | 返回字段与结果 |
| :--- | :--- | :--- | :--- |
| 冒烟 JSON 列表 | `https://tbib.org/index.php?pid=0&limit=2&tags=rating%3Asafe&s=post&q=index&page=dapi&json=1` | 200 / `text/html; charset=UTF-8` | 两项 `28627190/28627188`，`rating=safe`，上述 15 个 JSON 键及类型检查通过 |
| 冒烟 JSON 单帖 | `https://tbib.org/index.php?id=28627190&limit=2&s=post&q=index&page=dapi&json=1` | 200 / `text/html; charset=UTF-8` | 一项，编号与列表选择相同，1200×1600、30 个标签 |
| 冒烟 XML 单帖 | `https://tbib.org/index.php?id=28627190&s=post&q=index&page=dapi` | 200 / `text/xml;charset=UTF-8` | 原文 `str`；调用方解析后 `posts count=1 offset=0`、`post id=28627190 rating=s`，三个媒体 URL 属性存在 |
| 冒烟 XML 第二页 | `https://tbib.org/index.php?pid=1&limit=2&tags=rating%3Asafe&s=post&q=index&page=dapi` | 200 / `text/xml;charset=UTF-8` | `offset=2,count=7928682`；两帖 `28627185/28627184`，均 `rating=s` |
| 冒烟标签 | `https://tbib.org/index.php?limit=2&s=tag&q=index&page=dapi` | 200 / `text/xml;charset=UTF-8` | 两个 tag：`aphinity`、`algol_(words_worth)`；`id/name/count/type/ambiguous` 属性检查通过 |
| 冒烟评论 | `https://tbib.org/index.php?limit=2&post_id=1&s=comment&q=index&page=dapi` | 200 / `text/xml;charset=UTF-8` | `<comments type="array"/>`，没有子元素 |
| 示例 JSON 列表 | `https://tbib.org/index.php?tags=rating%3Asafe&pid=0&limit=2&s=post&q=index&page=dapi&json=1` | 200 / `text/html; charset=UTF-8` | 两帖 `28627190/28627188`，尺寸 1200×1600 / 3000×2250，标签数 30 / 27 |
| 示例 XML 单帖 | `https://tbib.org/index.php?id=28627190&s=post&q=index&page=dapi` | 200 / `text/xml;charset=UTF-8` | `md5=9304a0568bb9ddc0a57d8a23eea8c2f4`；`file_url` 与 `sample_url` 均为 `https://tbib.org/images/4905/7693b5d7bdff535e8c47ebcc32338235d24bedf9.jpg`；`preview_url=https://tbib.org/thumbnails/4905/thumbnail_7693b5d7bdff535e8c47ebcc32338235d24bedf9.jpg` |
| 示例标签 | `https://tbib.org/index.php?limit=2&s=tag&q=index&page=dapi` | 200 / `text/xml;charset=UTF-8` | tag `3145728/aphinity/count=2` 与 `78839808/algol_(words_worth)/count=1`；两者 `type=0,ambiguous=false` |
| 示例评论 | `https://tbib.org/index.php?post_id=1&s=comment&q=index&page=dapi` | 200 / `text/xml;charset=UTF-8` | 空 `comments` 根，`type=array` |

### 边界与未实测

- 只确认站点自述 Gelbooru 0.2，没有更细版本或服务端源码证据；没有登记或实测其它同族站点。
- 非空评论的子元素字段、`post_id` 的确切含义、标签过滤/排序/分页、帖子 `cid` 和更多元标签/排序组合均未实测。
- 帮助页的 100 上限被一次 `limit=101` 的响应否定，但实际硬上限仍未知。没有客户端钳位或自动翻页。
- 删除流只取得 500，不完整 XML 保留为站点错误；没有取得成功删除记录，`last_id` 游标推进未实测。
  上表错误来自直接路由请求，六请求冒烟不重复调用已知失败的删除流。
- 账号、凭据、用户接口、登录、写操作、私有数据均未调用；没有媒体下载或跟随补全的 302。
- 新增客户端不解析 HTML，不包装补全或用户目录；原始 XML 即使不完整也不由客户端补齐。
- 只执行了本节列出的匿名场景，没有构建、安装归档、CI、格式化、lint 或项目级套件验证。


## Sakuria：匿名只读实测（2026-09-19）

Sakuria 是 Pixiv 第三方镜像，不是 booru 家族的另一站点。本节没有服务端源码、官方 API 页面或 OpenAPI
可作交叉依据；用户提供的观察资料只用于选择请求，不能替代本次响应。资料矛盾见
[契约附注](sakuria-contract-notes.md#实测与输入文档的矛盾)。

### 路由观察与客户端执行的区别

先对 27 个公共 JSON 路由及少量参数、错误分支发出 **54 次匿名 GET**：41×200、7×400、3×401，
404、426、503 各一次。它们是直接 HTTP 观察，不是声称 44 个 Python 包装方法全部运行过。
随后运行客户端冒烟与两个示例，另有 **15 次 GET**；本节共 69 次，状态合计
54×200、8×400、3×401、2×404、1×426、1×503。
所有请求串行、相邻至少间隔 1.2 秒，不重试、不跟随重定向、不登录、不发写请求、不下载媒体；
54 次直接观察与脚本成功响应记录的 Content-Type 均为 `application/json`；冒烟的两个错误也解析到了 JSON 对象。

### 54 次直接路由观察

下表 URL 都是实际请求；数字是当时样本，不是未来总量或每页条数保证。

| 观察项 | 真实 URL | HTTP | 返回摘要 |
| :--- | :--- | ---: | :--- |
| index | `https://sakuria-api.syarolia.com/` | 200 | 键 name,ok,docs |
| stats | `https://sakuria-api.syarolia.com/stats` | 200 | 键 newToday,totalIllusts,totalCreators,totalUsers; {'newToday': 30, 'totalIllusts': 85, 'totalCreators': 197, 'totalUsers': 113} |
| health | `https://sakuria-api.syarolia.com/healthz` | 200 | 键 ok,releaseSha,releaseVersionId,checks |
| app_config | `https://sakuria-api.syarolia.com/app/config` | 200 | 键 latestVersion,latestBuild,updateUrl,releaseNotes,updateAvailable,updateRequired,maintenance,announcement,flags,servers,imageProxy,imageProxyPro,iap,appAttest |
| ai_config | `https://sakuria-api.syarolia.com/ai/config` | 200 | 键 enabled,metaEnabled,novelEnabled,mangaEnabled,mangaInputMode,commentEnabled,cacheTtlDays,billingMode,ratesEstimated,models,defaults,reasoningDefaults,routingPresets,languages |
| illust_page1 | `https://sakuria-api.syarolia.com/search/illust?q=blue&page=1&size=24` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=24; total=48; totalPages=4; hasMore=true; nextPage=4; hiddenCount=61; items=29 |
| illust_page2 | `https://sakuria-api.syarolia.com/search/illust?q=blue&page=2&size=24` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=2; pageSize=24; total=72; totalPages=4; hasMore=true; nextPage=4; hiddenCount=36; items=24 |
| illust_page3 | `https://sakuria-api.syarolia.com/search/illust?q=blue&page=3&size=24` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=3; pageSize=24; total=96; totalPages=6; hasMore=true; nextPage=6; hiddenCount=57; items=33 |
| illust_size1 | `https://sakuria-api.syarolia.com/search/illust?q=blue&size=1` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=1; total=2; totalPages=2; hasMore=true; nextPage=2; hiddenCount=25; items=5 |
| illust_size48 | `https://sakuria-api.syarolia.com/search/illust?q=blue&size=48` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=48; total=96; totalPages=5; hasMore=true; nextPage=5; hiddenCount=81; items=39 |
| illust_size49 | `https://sakuria-api.syarolia.com/search/illust?q=blue&size=49` | 400 | error="筛选参数无效"; code="invalid_search_filter"; field="size" |
| illust_size0 | `https://sakuria-api.syarolia.com/search/illust?q=blue&size=0` | 400 | error="筛选参数无效"; code="invalid_search_filter"; field="size" |
| illust_page0 | `https://sakuria-api.syarolia.com/search/illust?q=blue&page=0` | 400 | error="筛选参数无效"; code="invalid_search_filter"; field="page" |
| illust_ignored_limit | `https://sakuria-api.syarolia.com/search/illust?q=blue&page=1&size=24&limit=__invalid__` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=24; total=48; totalPages=4; hasMore=true; nextPage=4; hiddenCount=61; items=29 |
| illust_sort_popular | `https://sakuria-api.syarolia.com/search/illust?q=blue&page=1&size=2&sort=popular` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=2; total=4; totalPages=2; hasMore=true; nextPage=2; hiddenCount=21; items=6 |
| illust_sort_invalid | `https://sakuria-api.syarolia.com/search/illust?q=blue&sort=__invalid__` | 400 | error="筛选参数无效"; code="invalid_search_filter"; field="sort" |
| illust_mode | `https://sakuria-api.syarolia.com/search/illust?q=blue&mode=text` | 400 | error="筛选参数无效"; code="invalid_search_filter"; field="mode" |
| illust_type | `https://sakuria-api.syarolia.com/search/illust?q=blue&type=illust` | 401 | error="高级筛选需要 Sakuria+"; code="auth_required"; feature="advanced_search" |
| illust_show | `https://sakuria-api.syarolia.com/illust/70937229` | 200 | 键 id,title,type,pages,description,urls,author,tags,stats,publishedAt,publishedDays,isAi,isR18,xRestrict,sl; id=70937229；urls.w/h=1200/675；author.id=27517；tags=9 |
| illust_comments | `https://sakuria-api.syarolia.com/illust/70937229/comments?page=1&size=2` | 200 | 键 items,hasMore; hasMore=true; items=2 |
| illust_replies | `https://sakuria-api.syarolia.com/illust/70937229/comments/183991501/replies` | 200 | 键 items; items=1 |
| illust_related | `https://sakuria-api.syarolia.com/illust/128641898/related?size=2` | 200 | 键 items; items=2 |
| illust_missing | `https://sakuria-api.syarolia.com/illust/0` | 404 | error="illust not found" |
| illust_invalid | `https://sakuria-api.syarolia.com/illust/abc` | 400 | error="invalid id" |
| user_search1 | `https://sakuria-api.syarolia.com/search/user?q=mika&page=1` | 200 | 键 items,total; total=6; items=6 |
| user_search2 | `https://sakuria-api.syarolia.com/search/user?q=mika&page=2` | 200 | 键 items,total; total=12; items=12 |
| user_search3 | `https://sakuria-api.syarolia.com/search/user?q=mika&page=3` | 200 | 键 items,total; total=21; items=21 |
| user_show | `https://sakuria-api.syarolia.com/users/129030276` | 200 | 键 id,name,handle,accent,avatar,banner,stats,social; id=129030276；following=11；works=8；totalBookmarks=13 |
| user_illusts1 | `https://sakuria-api.syarolia.com/users/1039353/illusts?page=1` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=24; total=48; totalPages=2; hasMore=true; nextPage=3; hiddenCount=3; items=45 |
| user_illusts2 | `https://sakuria-api.syarolia.com/users/1039353/illusts?page=2` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=2; pageSize=24; total=72; totalPages=3; hasMore=true; nextPage=4; hiddenCount=3; items=45 |
| user_novels | `https://sakuria-api.syarolia.com/users/3182410/novels?page=1` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextCursor; page=1; pageSize=24; total=48; totalPages=2; hasMore=true; nextCursor="https://app-api.pixiv.net/v1/user/novels?user_id=3182410&offset=30"; items=24 |
| user_bookmarks1 | `https://sakuria-api.syarolia.com/users/1554775/bookmarks?page=1` | 200 | 键 items,pageSize,hasMore,nextCursor,hiddenCount; pageSize=24; hasMore=true; nextCursor="9175901406"; hiddenCount=5; items=19 |
| user_bookmarks2 | `https://sakuria-api.syarolia.com/users/1554775/bookmarks?page=2` | 200 | 键 items,pageSize,hasMore,nextCursor,hiddenCount; pageSize=24; hasMore=true; nextCursor="9175901406"; hiddenCount=5; items=19 |
| user_followers1 | `https://sakuria-api.syarolia.com/users/1039353/followers?page=1` | 200 | 键 items,page,pageSize,hasMore; page=1; pageSize=12; hasMore=false; items=0 |
| user_followers2 | `https://sakuria-api.syarolia.com/users/1039353/followers?page=2` | 200 | 键 items,page,pageSize,hasMore; page=2; pageSize=12; hasMore=false; items=0 |
| user_series | `https://sakuria-api.syarolia.com/users/3182410/series?page=1` | 200 | 键 items,page,pageSize,hasMore; page=1; pageSize=24; hasMore=false; items=0 |
| user_related | `https://sakuria-api.syarolia.com/users/1039353/related` | 200 | 键 items; items=12 |
| novel_search | `https://sakuria-api.syarolia.com/search/novel?q=blue&page=1` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=24; total=48; totalPages=2; hasMore=true; nextPage=2; hiddenCount=6; items=24 |
| novel_search2 | `https://sakuria-api.syarolia.com/search/novel?q=blue&page=2` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=2; pageSize=24; total=72; totalPages=3; hasMore=true; nextPage=3; hiddenCount=4; items=26 |
| novel_type | `https://sakuria-api.syarolia.com/search/novel?q=blue&type=illust` | 400 | error="小说不支持该作品筛选条件"; code="unsupported_filter_for_scope"; field="type" |
| novel_ai | `https://sakuria-api.syarolia.com/search/novel?q=blue&ai=exclude` | 401 | error="高级筛选需要 Sakuria+"; code="auth_required"; feature="advanced_search" |
| novel_show | `https://sakuria-api.syarolia.com/novels/29167620` | 200 | 键 id,title,author,caption,captionHtml,tags,textLength,text,document,coverSvg,cover,stats,publishedAt,publishedDays,isAi,isR18,xRestrict,sl; text空串；textLength=99；document.text含4行uploadedimage标记；uploadedImages=4；pixivImages={}；两处text不相等 |
| novel_comments | `https://sakuria-api.syarolia.com/novels/29167620/comments?page=1` | 200 | 键 items,hasMore; hasMore=false; items=0 |
| novel_related | `https://sakuria-api.syarolia.com/novels/29167620/related` | 200 | 键 items,page,pageSize,total,totalPages,hasMore; page=1; pageSize=12; total=0; totalPages=1; hasMore=false; items=0 |
| series_show | `https://sakuria-api.syarolia.com/series/198059?page=1` | 200 | 键 id,title,caption,total,author,items,hasMore; total=219; hasMore=true; items=30 |
| series_novel_id | `https://sakuria-api.syarolia.com/series/12064` | 200 | 键 id,title,caption,total,author,items,hasMore; total=7; hasMore=false; items=0 |
| spotlight_list | `https://sakuria-api.syarolia.com/spotlight?page=1&lang=zh-cn` | 200 | 键 items,page,pageSize,hasMore; page=1; pageSize=12; hasMore=true; items=20 |
| spotlight_show | `https://sakuria-api.syarolia.com/spotlight/11971?lang=zh-cn` | 200 | 键 id,title,date,description,cover,tags,works,articles,relatedLatest,relatedRecommend,articleUrl; articles=19；works=0；cover=/p/embed.pixiv.net/pixivision/zh/a/11971/ogimage.jpg |
| spotlight_missing | `https://sakuria-api.syarolia.com/spotlight/0` | 503 | error="upstream temporarily unavailable"; retryable=true |
| tag_illusts | `https://sakuria-api.syarolia.com/tags/blue?page=1&size=24` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=24; total=48; totalPages=4; hasMore=true; nextPage=4; hiddenCount=65; items=25 |
| tag_search_q | `https://sakuria-api.syarolia.com/tags/search?q=blue&size=2` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=2; total=4; totalPages=2; hasMore=true; nextPage=2; hiddenCount=19; items=11 |
| tag_search_noq | `https://sakuria-api.syarolia.com/tags/search?size=2` | 200 | 键 items,page,pageSize,total,totalPages,hasMore,nextPage,hiddenCount; page=1; pageSize=2; total=4; totalPages=2; hasMore=true; nextPage=2; hiddenCount=19; items=11 |
| me_likes_contract | `https://sakuria-api.syarolia.com/me/likes` | 426 | error="upgrade_required"; requiredDataContract=2 |
| me_likes_auth | `https://sakuria-api.syarolia.com/me/likes` | 401 | error="sakuria_session_required" |

对这些响应作字段比较（不追加 HTTP 请求）：

- 插画搜索 `size=24,page=1/2/3` 的 `total=48/72/96`，`totalPages=4/4/6`，`nextPage=4/4/6`；
  条数为 29/24/33，相邻页 ID 交集 24/10。数值 `nextPage` 不是下一相邻页；总数不是固定全局总量。
- `size=1/48` 被接受，实际给 5/39 条；`size=0/49` 返回 400 `field=size`。
  这证明边界样本，不证明区间内所有值，更不能把 48 当作实际返回条数的硬上限。
- 加 `limit=__invalid__` 后 ID 顺序与分页字段和基线相同；完整作品对象有动态差异。
  只确认这一个参数取值没改变所比较结果，不能据此宣布所有未知参数都被忽略。
- `user_search(q='mika',page=1/2/3)` 分别返回 6/12/21 项，`total` 恰等于各页条数，各页 ID 无交集。
  因此“累计值”的怀疑没有被支持，不把它当全局总数；也没有 `hasMore` 可判断末页。
- `user_illusts(1039353,page=1/2)` 各有 45 项，ID 交集 23；两页有 `nextPage=3/4`。
- `user_bookmarks(1554775,page=1/2)` 完整 JSON 相同（19 项、相同 `nextCursor`）；只证这两个页值。
  `user_followers(1039353,page=1/2)` 都为空，但 `page` 分别回显 1/2，不能称页码无效或功能未实现。
- `/tags/blue?page=1&size=24` 有 25 项，与 `/search/illust?q=blue&page=1&size=24` 的 29 项交集 25。
  不能承诺完全等价；请求不同时，差异原因未确定。`/tags/search?size=2` 带 `q=blue` 与不带的
  完整 JSON 相同，均 11 项。
- `/illust/70937229` 的标签有 `translated` 缺省项，`alt` 依数组顺序为 0/1/2/3/4/0/1/2/3；
  不把这一观察当服务端分类语义。头像、图片地址仅观察 JSON 字符串，没有请求其正文。

### 已执行命令与客户端结果

以下 `my-anybooru.json` 是使用者自己的完整配置文件的中性占位名；实际参数来自包内模板的
`smoke.sakuria` / `examples.sakuria`，显式 `access_token=''` 保持匿名。
三个脚本实际执行时间为 **UTC 2026-09-19 13:08:07–13:08:48**。

```bash
python -X utf8 test/sakuria.py --config my-anybooru.json
python -X utf8 examples/sakuria/search_illusts.py --config my-anybooru.json
python -X utf8 examples/sakuria/browse_resources.py --config my-anybooru.json
```

| 脚本 | 请求数 | 状态 | 退出码 |
| :--- | ---: | :--- | ---: |
| `test/sakuria.py` | 10 | 8×200，预期 404、400 各一次；`SUMMARY sakuria \| requests=10 \| passed=10 failed=0`，无 SKIP | 0 |
| `examples/sakuria/search_illusts.py` | 2 | 两次 200 | 0 |
| `examples/sakuria/browse_resources.py` | 3 | 三次 200 | 0 |

三个脚本 stderr 均为空。冒烟实际检查了导入、配置、构造、完整 JSON 字段与类型、详情 ID 等于列表选择值、
作者 ID、错误状态/JSON 正文；`last_call` 提供以下真实 URL 与状态，未把任意 200 当作通过。

| 调用 | 真实 URL | HTTP | 关键返回字段 |
| :--- | :--- | ---: | :--- |
| 冒烟 stats | `https://sakuria-api.syarolia.com/stats` | 200 | newToday:int,totalIllusts:int,totalCreators:int,totalUsers:int \| newToday=30 totalIllusts=85 totalCreators=197 totalUsers=113 |
| 冒烟 illust_search page 1 | `https://sakuria-api.syarolia.com/search/illust?page=1&q=blue&size=2&sort=new` | 200 | items:list,page:int,pageSize:int,total:int,totalPages:int,hasMore:bool \| page=1 items=2 pageSize=2 total=4 totalPages=2 hasMore=True hiddenCount=28 ids=['149856440', '149856385'] first=149856440 title='青の世界に君を探して SNS公開版\u3000７' urls.original=/img/img-original/img/2026/09/19/22/00/06/149856440_p0.jpg |
| 冒烟 illust_show first id | `https://sakuria-api.syarolia.com/illust/149856440` | 200 | id:str,title:str,type:str,pages:int,urls:dict,author:dict,tags:list,stats:dict,publishedAt:str,publishedDays:int,isAi:bool,isR18:bool,xRestrict:int,sl:int \| id=149856440 title='青の世界に君を探して SNS公開版\u3000７' type=illust pages=2 author=70836035 tags=3 stats={'likes': 1, 'bookmarks': 1, 'views': 4, 'comments': 0} urls.original=/img/img-original/img/2026/09/19/22/00/06/149856440_p0.jpg |
| 冒烟 illust_search page 2 | `https://sakuria-api.syarolia.com/search/illust?page=2&q=blue&size=2&sort=new` | 200 | items:list,page:int,pageSize:int,total:int,totalPages:int,hasMore:bool \| page=2 items=8 pageSize=2 total=6 totalPages=3 hasMore=True hiddenCount=22 ids=['149856181', '149856117', '149855928', '149855832', '149855736', '149855696', '149855689', '149855621'] first=149856181 title='9/27ガタケット185お品書き' urls.original=/img/img-original/img/2026/09/19/21/54/43/149856181_p0.png |
| 冒烟 novel_search | `https://sakuria-api.syarolia.com/search/novel?q=blue&page=1` | 200 | items:list,page:int,pageSize:int,total:int,totalPages:int,hasMore:bool \| page=1 items=27 pageSize=24 total=48 hasMore=True hiddenCount=3 ids=['29170046', '29170024', '29170009', '29170001', '29169999', '29169990', '29169911', '29169840', '29169729', '29169686', '29169672', '29169606', '29169592', '29169546', '29169519', '29169513', '29169476', '29169465', '29169331', '29169304', '29169269', '29169223', '29169217', '29169116', '29169065', '29169060', '29169048'] first=29170046 title='名探偵コナン＆ブルーアーカイブ\u300014番目の標的(前編)' textLength=32396 cover.regular=/img/c/240x480_80/novel-cover-master/img/2026/09/19/22/07/08/ci29170046_3df6b93266caf418cb1ffd1d44024e95_master1200.jpg |
| 冒烟 spotlight_list | `https://sakuria-api.syarolia.com/spotlight?page=1&lang=zh-cn` | 200 | items:list,page:int,pageSize:int,hasMore:bool \| page=1 items=20 pageSize=12 hasMore=True ids=['12064', '11903', '11731', '11737', '11661', '11665', '11728', '12078', '11708', '11772', '12047', '11971', '12050', '11681', '11927', '11683', '11975', '11993', '11815', '11642'] first=12064 title='【宝可梦】谜拟丘同人作品特辑 ' cover=/img/c/1200x630_q80_a2_g1_u1_icr0.086:0.082:0.929:0.902/img-original/img/2025/12/18/11/11/56/138736355_p0.jpg articleUrl=https://www.pixivision.net/zh/a/12064 tags=2 works=0 |
| 冒烟 illust_comments | `https://sakuria-api.syarolia.com/illust/70937229/comments?page=1&size=2` | 200 | items:list,hasMore:bool \| items=2 hasMore=True ids=['225695134', '222800878'] likes=[0, 0] first=225695134 timeLabel='4 个月前' text_chars=4 |
| 冒烟 user_show detail author | `https://sakuria-api.syarolia.com/users/70836035` | 200 | id:str,name:str,handle:str,accent:str,avatar:str,stats:dict,social:list \| id=70836035 name='Teraichi十代目てらいち' handle=10thteraichi stats={'followers': 0, 'following': 76, 'works': 174, 'totalLikes': 0, 'totalBookmarks': 2882} social=1 avatar=/img/user-profile/img/2024/08/09/21/14/07/26215650_13b44c8974f1e79c152a35350d6e6142_170.jpg |
| 冒烟 illust_show missing id | `https://sakuria-api.syarolia.com/illust/0` | 404 | error='illust not found' body_chars=28 |
| 冒烟 illust_search size over maximum | `https://sakuria-api.syarolia.com/search/illust?q=blue&size=49` | 400 | error='筛选参数无效' code='invalid_search_filter' field='size' body_chars=64 |
| 示例 illust_search | `https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=1` | 200 | {"count": 2, "ids": ["149856440", "149856385"], "new_ids": ["149856440", "149856385"], "page_size": 2, "total": 4, "next_page": 2, "has_more": true} |
| 示例 illust_search | `https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=2` | 200 | {"count": 8, "ids": ["149856181", "149856117", "149855928", "149855832", "149855736", "149855696", "149855689", "149855621"], "new_ids": ["149856181", "149856117", "149855928", "149855832", "149855736", "149855696", "149855689", "149855621"], "page_size": 2, "total": 6, "next_page": 3, "has_more": true} |
| 示例 illust_show | `https://sakuria-api.syarolia.com/illust/70937229` | 200 | {"illust_id": "70937229", "pages": 1, "tag_count": 9, "author_id": "27517", "stats": {"likes": 243793, "bookmarks": 243793, "views": 1200449, "comments": 442}} |
| 示例 illust_comments | `https://sakuria-api.syarolia.com/illust/70937229/comments?page=1&size=2` | 200 | {"count": 2, "has_more": true, "first": {"id": "225695134", "author_id": "122643822", "author_name": "ayuayu", "likes": 0, "replies_count": 0, "chars": 4, "created_at": "2026-05-21T07:17:53+09:00", "time_label": "4 个月前"}} |
| 示例 user_show | `https://sakuria-api.syarolia.com/users/27517` | 200 | {"user_id": "27517", "handle": "fuzichoco", "stats": {"followers": 0, "following": 288, "works": 274, "totalLikes": 0, "totalBookmarks": 4195}} |

搜索示例合并得到 10 个唯一 ID，`duplicate_count=0`；这一轮没有触发去重删除分支，不能把先前
`size=24` 的重叠说成这次 `size=2` 也有。第二页实际 8 项但 `pageSize=2`，没有被客户端截断。

### 边界与未实测

- 已制作的接口面为 44 个原生 GET；直接 HTTP 核实公共路由不等于每个 Python 包装方法都运行过。
  本节只执行了上表列出的客户端方法。
- 17 个账号方法均未用 token 登录调用，成功返回结构未知；仅匿名 `/me/likes` 验证了
  426 与显式契约头后的 401。其余账号路由本轮未请求，没有发明登录或刷新方法。
- 未遍历所有页、参数枚举、区间内取值、排序/筛选组合、实际最大条数或末页停止条件；
  `followers`、用户小说系列、小说评论与关联小说的非空元素、特辑详情 `works` 本轮无成功非空样本。
- 小说详情取得上传图标记及 4 个图片描述对象，但顶层 `text` 为空；未取得通常意义上的非空小说文字正文，
  也未读取任何插图字节。`document.text` 与 `text` 不相同，不应相互替代。
- 403、429、会员成功、token 生命周期、写路由、其它主机、登录/注册路径、图片占位响应均未请求。
  “缺图为 200 + image/svg+xml”的输入提醒按原授权只写在媒体注意事项，不冒称本轮复测。
- 没有运行 formatter、lint、构建、安装归档、CI 或项目测试套件；唯一保留的测试是十请求以内的匿名冒烟。


## Anime-Pictures：匿名只读实测（2026-09-19）

本次接入第十家族 `AnimePictures`，基地址是 `https://api.anime-pictures.net/api/v3`。
接口面为 13 个原生方法（12 GET、1 POST）；**方法存在不代表权限成功路径已验证**。
以下分开记录直接 HTTP 观察与通过新客户端执行的脚本。所有请求匿名、串行，相邻请求至少间隔 1.3 秒；
未登录、未发写请求、不跟随重定向、不下载 CDN 媒体、无请求级重试。`get_image` 仅取得匿名 403 空正文。

### 90 次直接路由观察

覆盖主机根、帖子/标签/用户/评论读取、两项受限 GET 的匿名拒绝、分页/过滤/排序样本与错误路径。
共 **90 GET：76×200、4×400、2×403、6×404、1×410、1×500**。
响应格式为 `application/json` 85 次、`text/plain; charset=utf-8` 1 次、未带 `Content-Type` 的空正文 4 次。
这些是路由观察，不冒称相应 Python 方法均已执行；参数值未穷举，计数都是当时快照。

| 观察项 | 真实 URL | HTTP | Content-Type | 关键字段 |
| :--- | :--- | ---: | :--- | :--- |
| root | `https://api.anime-pictures.net/` | 200 | application/json | {"message": "Hello, World!"} |
| posts0 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=667906; max_pages=333952; ids=[929492, 929491] |
| posts1 | `https://api.anime-pictures.net/api/v3/posts?page=1&posts_per_page=2` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=1; posts_count=667906; max_pages=333952; ids=[929490, 929489] |
| detail | `https://api.anime-pictures.net/api/v3/posts/929452` | 200 | application/json | keys=post,source,user,moderator,tags,file_url,star_it,favorites_users,tied; post.id=929452; ext=.png; tags=38; 三档preview URL仅观察字符串 |
| post_comments | `https://api.anime-pictures.net/api/v3/posts/382872/comments` | 200 | application/json | keys=success,comments; comments=1; ids=[174693] |
| post_tags | `https://api.anime-pictures.net/api/v3/posts/929452/tags` | 403 | application/json | {"errormsg": "You not have rights", "success": false} |
| tags_exact | `https://api.anime-pictures.net/api/v3/tags?tag=hatsune+miku` | 200 | application/json | offset=0; limit=20; count=1; tags=[(407, 'hatsune miku')] |
| tags_partial | `https://api.anime-pictures.net/api/v3/tags?tag=hatsune` | 200 | application/json | offset=0; limit=20; count=0; tags=[] |
| tags_default | `https://api.anime-pictures.net/api/v3/tags` | 200 | application/json | offset=0; limit=20; count=156541; tags=[(226296, 'giao giao'), (226295, 'hasshaku-sama (cosplay)')] |
| tags_search | `https://api.anime-pictures.net/api/v3/tags?search=hatsune` | 200 | application/json | offset=0; limit=20; count=156541; tags=[(226296, 'giao giao'), (226295, 'hasshaku-sama (cosplay)')] |
| tag_show | `https://api.anime-pictures.net/api/v3/tags/407` | 200 | application/json | success=true; tag.id=407; tag=hatsune miku; views=93150 |
| users_list | `https://api.anime-pictures.net/api/v3/users?limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=225284; ids=[257203, 294066] |
| user_show | `https://api.anime-pictures.net/api/v3/users/294066` | 200 | application/json | keys=success,user,errormsg; user.id=294066; user键=id,name,avatar_version,isavatar,site_score,groups,gender,register_date |
| comments_list | `https://api.anime-pictures.net/api/v3/comments?limit=2&offset=0` | 200 | application/json | keys=success,offset,limit,count,comments; comments=2; ids=[174693, 174688] |
| comment_show | `https://api.anime-pictures.net/api/v3/comments/174693` | 200 | application/json | keys=success,comment,user; comment.id=174693; user.id=290656 |
| missing_post | `https://api.anime-pictures.net/api/v3/posts/999999999` | 410 | application/json | {"errormsg": "Post not found", "success": false} |
| missing_tag | `https://api.anime-pictures.net/api/v3/tags/999999999` | 404 | application/json | {"errormsg": "Tag not found", "success": false} |
| missing_user | `https://api.anime-pictures.net/api/v3/users/999999999` | 404 | application/json | {"errormsg": "User not found", "success": false} |
| missing_comment | `https://api.anime-pictures.net/api/v3/comments/999999999` | 404 | application/json | {"errormsg": "Have no comment", "success": false} |
| invalid_post_path | `https://api.anime-pictures.net/api/v3/posts/top` | 400 | text/plain; charset=utf-8 | 正文 'Invalid URL: Cannot parse `top` to a `i32`' |
| image_get | `https://api.anime-pictures.net/pictures/get_image/929452-3550x2344-azur%20lane-illustrious%20%28azur%20lane%29-illustrious%20%28wandering%20glow%20of%20midnight%29%20%28azur%20lane%29-single-long%20hair-looking%20at%20viewer.png` | 403 | 无 | 正文 '' |
| page_missing | `https://api.anime-pictures.net/api/v3/posts` | 400 | application/json | {"errormsg": "Missing or invalid `page` parameter", "success": false} |
| page_text | `https://api.anime-pictures.net/api/v3/posts?page=abc` | 400 | application/json | {"errormsg": "Missing or invalid `page` parameter", "success": false} |
| page_negative | `https://api.anime-pictures.net/api/v3/posts?page=-1` | 500 | application/json | {"errormsg": "Internal server error", "success": false} |
| page_past_end | `https://api.anime-pictures.net/api/v3/posts?page=999999&posts_per_page=100` | 200 | application/json | posts_per_page=100; response_posts_count=0; page_number=999999; posts_count=667906; max_pages=6679; ids=[] |
| ppp_default | `https://api.anime-pictures.net/api/v3/posts?page=0` | 200 | application/json | posts_per_page=80; response_posts_count=80; page_number=0; posts_count=667906; max_pages=8348; ids=[929492, 929491, 929490] |
| ppp_1 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=667906; max_pages=667905; ids=[929492] |
| ppp_100 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=100` | 200 | application/json | posts_per_page=100; response_posts_count=100; page_number=0; posts_count=667906; max_pages=6679; ids=[929492, 929491, 929490] |
| ppp_101 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=101` | 200 | application/json | posts_per_page=60; response_posts_count=60; page_number=0; posts_count=667906; max_pages=11131; ids=[929492, 929491, 929490] |
| ppp_150 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=150` | 200 | application/json | posts_per_page=60; response_posts_count=60; page_number=0; posts_count=667906; max_pages=11131; ids=[929492, 929491, 929490] |
| ppp_1000 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1000` | 200 | application/json | posts_per_page=60; response_posts_count=60; page_number=0; posts_count=667906; max_pages=11131; ids=[929492, 929491, 929490] |
| ppp_0 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=0` | 200 | application/json | posts_per_page=60; response_posts_count=60; page_number=0; posts_count=667906; max_pages=11131; ids=[929492, 929491, 929490] |
| ppp_-1 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=-1` | 200 | application/json | posts_per_page=80; response_posts_count=80; page_number=0; posts_count=667906; max_pages=8348; ids=[929492, 929491, 929490] |
| sort_date | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=date` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[929492, 929491, 929490]; score/score_number=[(0.0, 8), (0.0, 9), (0.0, 5)] |
| sort_date_r | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=date_r` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[2, 3, 5]; score/score_number=[(73.0, 70), (31.0, 25), (67.0, 42)] |
| sort_rating | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=rating` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[301063, 423454, 602864]; score/score_number=[(1446.0, 629), (0.0, 525), (0.0, 442)] |
| sort_views | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=views` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[88793, 304173, 45264]; score/score_number=[(117.0, 27), (144.0, 60), (72.0, 66)] |
| sort_size | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=size` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[34056, 43659, 45028]; score/score_number=[(81.0, 34), (31.0, 6), (36.0, 9)] |
| sort_tag_num | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=tag_num` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[581823, 266625, 264140]; score/score_number=[(0.0, 15), (36.0, 9), (72.0, 16)] |
| sort_id | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=id` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[1, 2, 3]; score/score_number=[(16.0, 11), (73.0, 70), (31.0, 25)] |
| sort_random | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=random` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[929492, 929491, 929490]; score/score_number=[(0.0, 8), (0.0, 9), (0.0, 5)] |
| order_asc | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=rating&order=asc` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[301063, 423454, 602864] |
| order_desc | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=rating&order=desc` | 200 | application/json | posts_per_page=3; response_posts_count=3; page_number=0; posts_count=667906; max_pages=222635; ids=[301063, 423454, 602864] |
| search_0 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&search_tag=hatsune+miku` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=21008; max_pages=10503; ids=[929980, 929880]; exclusive_tag.id=407 |
| search_1 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&search_tag=long+hair+blue+eyes` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=146065; max_pages=73032; ids=[929489, 929484] |
| search_2 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&search_tag=zzzznotexist` | 200 | application/json | posts_per_page=2; response_posts_count=0; page_number=0; posts_count=0; max_pages=0; ids=[] |
| denied_0 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&denied_tags=long+hair` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=269346; max_pages=134672; ids=[929491, 929490] |
| denied_1 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&denied_tags=blue+eyes` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=510020; max_pages=255009; ids=[929492, 929491] |
| denied_2 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&denied_tags=long+hair+blue+eyes` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=667906; max_pages=333952; ids=[929492, 929491] |
| denied_repeated | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&denied_tags=long+hair&denied_tags=blue+eyes` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=510020; max_pages=255009; ids=[929492, 929491] |
| ldate_0 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=0` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=667906; max_pages=667905; ids=[2]; 最早pubtime=2009-10-11T02:01:54.188977 |
| ldate_1 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=1` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=411; max_pages=410; ids=[929698]; 最早pubtime=2026-09-12T19:20:29.314077 |
| ldate_2 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=2` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=1879; max_pages=1878; ids=[926488]; 最早pubtime=2026-08-20T19:18:12.277337 |
| ldate_3 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=3` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=57; max_pages=56; ids=[930137]; 最早pubtime=2026-09-18T14:00:06.818648 |
| ldate_4 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=4` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=11286; max_pages=11285; ids=[912892]; 最早pubtime=2026-03-20T16:19:51.852357 |
| ldate_5 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=5` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=28743; max_pages=28742; ids=[887334]; 最早pubtime=2025-09-19T13:46:45.276579 |
| ldate_6 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=6` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=61654; max_pages=61653; ids=[841331]; 最早pubtime=2024-09-19T21:35:09.887326 |
| ldate_7 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=7` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=84306; max_pages=84305; ids=[810433]; 最早pubtime=2023-09-20T20:10:45.566003 |
| ldate_8 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=1&order_by=date_r&ldate=8` | 200 | application/json | posts_per_page=1; response_posts_count=1; page_number=0; posts_count=667906; max_pages=667905; ids=[2]; 最早pubtime=2009-10-11T02:01:54.188977 |
| filter_0 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&aspect=16%3A9` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=37502; max_pages=18750; ids=[929491, 929490] |
| filter_1 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&aspect=1%3A1` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=18296; max_pages=9147; ids=[930027, 929882] |
| filter_2 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&color=FF0000` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=1645; max_pages=822; ids=[802077, 639511] |
| filter_3 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&color=%23FF0000` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=1645; max_pages=822; ids=[802077, 639511] |
| filter_4 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&ext_jpg=jpg` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=470199; max_pages=235099; ids=[929491, 929456] |
| filter_5 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&ext_png=png` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=196121; max_pages=98060; ids=[929492, 929490] |
| filter_6 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&ext_gif=gif` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=1586; max_pages=792; ids=[926946, 922910] |
| filter_7 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&ext_jpg=yes&ext_png=yes` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=666320; max_pages=333159; ids=[929492, 929491] |
| filter_8 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&user=204183` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=30757; max_pages=15378; ids=[930131, 930153] |
| filter_9 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&stars_by=13734` | 200 | application/json | posts_per_page=2; response_posts_count=2; page_number=0; posts_count=41519; max_pages=20759; ids=[929366, 929364] |
| tag_type_0 | `https://api.anime-pictures.net/api/v3/tags?type=0&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=4303; tags=[(226287, 'editor (kankin jk)'), (221353, 'jien (nikke)')] |
| tag_type_1 | `https://api.anime-pictures.net/api/v3/tags?type=1&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=56435; tags=[(226294, 'nakumura tamaki'), (226293, 'reiha (real bout high school)')] |
| tag_type_2 | `https://api.anime-pictures.net/api/v3/tags?type=2&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=4474; tags=[(226295, 'hasshaku-sama (cosplay)'), (226207, 'miyamoto musashi (onimusha) (cosplay)')] |
| tag_type_3 | `https://api.anime-pictures.net/api/v3/tags?type=3&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=5510; tags=[(226288, 'buta thunder (vocaloid)'), (226273, 'mashiro no oto')] |
| tag_type_4 | `https://api.anime-pictures.net/api/v3/tags?type=4&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=76532; tags=[(226296, 'giao giao'), (226278, 'partita')] |
| tag_type_5 | `https://api.anime-pictures.net/api/v3/tags?type=5&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=4606; tags=[(226279, 'ai the somnium files'), (226229, 'stellar blade: blood rain')] |
| tag_type_6 | `https://api.anime-pictures.net/api/v3/tags?type=6&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=1909; tags=[(226276, 'knight a'), (226173, 'akutagawa vtuber project')] |
| tag_type_7 | `https://api.anime-pictures.net/api/v3/tags?type=7&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=2772; tags=[(225975, 'anima (honkai: nexus anima)'), (225968, 'dragon bubble (arknights)')] |
| tag_type_8 | `https://api.anime-pictures.net/api/v3/tags?type=8&limit=2&offset=0` | 200 | application/json | offset=0; limit=2; count=0; tags=[] |
| tags_limit_1000 | `https://api.anime-pictures.net/api/v3/tags?limit=1000` | 200 | application/json | offset=0; limit=100; count=156541; tags=[(226296, 'giao giao'), (226295, 'hasshaku-sama (cosplay)')] |
| tags_offset | `https://api.anime-pictures.net/api/v3/tags?limit=2&offset=2` | 200 | application/json | offset=2; limit=2; count=156541; tags=[(226294, 'nakumura tamaki'), (226293, 'reiha (real bout high school)')] |
| users_default | `https://api.anime-pictures.net/api/v3/users` | 200 | application/json | offset=0; limit=20; count=225284; ids=[257203, 294066, 182163] |
| users_offset | `https://api.anime-pictures.net/api/v3/users?limit=2&offset=2` | 200 | application/json | offset=2; limit=2; count=225284; ids=[182163, 290656] |
| users_limit101 | `https://api.anime-pictures.net/api/v3/users?limit=101` | 200 | application/json | offset=0; limit=100; count=225284; ids=[257203, 294066, 182163] |
| comments_default | `https://api.anime-pictures.net/api/v3/comments` | 200 | application/json | keys=success,offset,limit,count,comments; comments=20; ids=[174693, 174688, 174678] |
| comments_offset | `https://api.anime-pictures.net/api/v3/comments?limit=2&offset=2` | 200 | application/json | keys=success,offset,limit,count,comments; comments=2; ids=[174678, 174677] |
| comments_limit101 | `https://api.anime-pictures.net/api/v3/comments?limit=101` | 200 | application/json | keys=success,offset,limit,count,comments; comments=100; ids=[174693, 174688, 174678] |
| legacy_v2 | `https://api.anime-pictures.net/api/v2/comments` | 404 | 无 | 正文 '' |
| legacy_posts | `https://api.anime-pictures.net/pictures/view_posts/0?type=json` | 404 | 无 | 正文 '' |
| unknown_route | `https://api.anime-pictures.net/api/v3/not_a_route` | 404 | 无 | 正文 '' |
| post_type_json | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&type=json` | 400 | application/json | {"errormsg": "Only json_v3, json1, and xml response types are supported", "success": false} |

主要校对结果：`score` 并非恒 0（id 2 为 73.0，id 301063 为 1446.0）；单条评论带 `user`；
单用户顶层带 `errormsg:null`、内层无 `login`；`max_pages` 在空搜索时是 0；
单标签帖子搜索样本带额外 `exclusive_tag`；部分收藏记录带 `folder`。详情的 `source` 也可能不存在，见下文。
完整输入错误、字段清单遗漏、数据漂移及未实测推断见[契约附注](anime-pictures-contract-notes.md#实测与输入文档的矛盾)。

### 实际命令与最终脚本结果

下列命令使用 `my-anybooru.json` 作为使用者配置文件的中性名称；参数取自包内模板的
`smoke.anime_pictures` / `examples.anime_pictures`。三个脚本都显式设置 `authorization=''`、`cookie=''`。

```bash
python -X utf8 test/anime_pictures.py --config my-anybooru.json
python -X utf8 examples/anime_pictures/list_posts.py --config my-anybooru.json
python -X utf8 examples/anime_pictures/browse_resources.py --config my-anybooru.json
```

| 脚本（最终版本） | UTC 执行时间 | 请求数 | HTTP 与结果 | 退出码 |
| :--- | :--- | ---: | :--- | ---: |
| `test/anime_pictures.py` | 13:53:51–13:54:10 | 10 | 8×200 + 预期 410、400；`SUMMARY anime_pictures \| requests=10 \| passed=10 failed=0`，无 SKIP | 0 |
| `examples/anime_pictures/list_posts.py` | 13:51:00–13:51:03 | 2 | 两次 200，页码 0/1，hatsune miku 按 rating 排序 | 0 |
| `examples/anime_pictures/browse_resources.py` | 13:54:11–13:54:18 | 4 | 四次 200，详情 → 帖评论 → 上传者 → 评论详情 | 0 |

最终三个脚本的 stderr 均为空，共 **16 GET：14×200、预期 410 与 400 各一次**。
冒烟验证导入、配置与构造，观察完整 JSON、资源 ID、页码，以及 HTTP 错误与 `last_call`；
`posts/top` 确实抛 `AnybooruHTTPError`（不是 `AnybooruAPIError`），`data=None`、`body` 保留 42 字符纯文本，
`last_call` 保留 HTTP 400 与真实 URL。客户端未自行修正任何分页字段。

| 调用 | 真实 URL | HTTP | 关键字段 |
| :--- | :--- | ---: | :--- |
| 冒烟 posts_list page 0 | `https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2` | 200 | posts:list,posts_per_page:int,response_posts_count:int,page_number:int,posts_count:int,max_pages:int \| page_number=0 posts=2 response_posts_count=2 posts_per_page=2 posts_count=667906 max_pages=333952 ids=[929492, 929491] first=929492 md5=0f04fddedd428aae0e3c25c2e62a2812 size=5760x2400 score_number=8 ext='.png' |
| 冒烟 post_show first id | `https://api.anime-pictures.net/api/v3/posts/929492` | 200 | id:int,md5:str,width:int,height:int,score:float,score_number:int,ext:str,tags_count:int \| id=929492 file_url='929492-5760x2400-wuthering waves-augusta (wuthering waves)-giao giao-single-long hair-looking at viewer.png' small_preview=https://opreviews.anime-pictures.net/0f0/0f04fddedd428aae0e3c25c2e62a2812_sp.avif tags=62 user=257203 detail_keys=post,source,user,moderator,tags,file_url,star_it,favorites_users,tied |
| 冒烟 posts_list page 1 | `https://api.anime-pictures.net/api/v3/posts?page=1&posts_per_page=2` | 200 | posts:list,posts_per_page:int,response_posts_count:int,page_number:int,posts_count:int,max_pages:int \| page_number=1 posts=2 response_posts_count=2 posts_per_page=2 posts_count=667906 max_pages=333952 ids=[929490, 929489] first=929490 md5=b1593fc95c0e38ff1e2f0266fc0f011b size=5500x3094 score_number=6 ext='.png' |
| 冒烟 post_comments configured post | `https://api.anime-pictures.net/api/v3/posts/382872/comments` | 200 | success:bool,comments:list \| comments=1 first=174693 text_chars=38 user=290656 |
| 冒烟 tags_list exact tag | `https://api.anime-pictures.net/api/v3/tags?tag=hatsune+miku` | 200 | tags:list,success:bool,offset:int,limit:int,count:int \| offset=0 limit=20 count=1 ids=[407] names=['hatsune miku'] first=407/'hatsune miku' num=22686 |
| 冒烟 tag_show configured id | `https://api.anime-pictures.net/api/v3/tags/407` | 200 | success:bool,tag:dict \| id=407 tag='hatsune miku' num=22686 type=1 |
| 冒烟 users_list | `https://api.anime-pictures.net/api/v3/users?limit=2&offset=0` | 200 | users:list,success:bool,offset:int,limit:int,count:int \| offset=0 limit=2 count=225284 user_ids=[257203, 294066] |
| 冒烟 comments_list | `https://api.anime-pictures.net/api/v3/comments?limit=2&offset=0` | 200 | comments:list,success:bool,offset:int,limit:int,count:int \| offset=0 limit=2 count=14988 comment_ids=[174693, 174688] post_ids=[382872, 887422] |
| 冒烟 post_show missing id | `https://api.anime-pictures.net/api/v3/posts/999999999` | 410 | data=['errormsg', 'success'] errormsg='Post not found' body_chars=45 last_call=HTTP 410 https://api.anime-pictures.net/api/v3/posts/999999999 |
| 冒烟 post_show invalid path | `https://api.anime-pictures.net/api/v3/posts/top` | 400 | data=None body_chars=42 content_type='text/plain; charset=utf-8' last_call=HTTP 400 https://api.anime-pictures.net/api/v3/posts/top |
| 示例 posts_list | `https://api.anime-pictures.net/api/v3/posts?page=0&search_tag=hatsune+miku&posts_per_page=2&order_by=rating` | 200 | {"requested_page": 0, "page_number": 0, "posts_per_page": 2, "response_posts_count": 2, "posts_count": 21008, "max_pages": 10503, "count": 2, "ids": [423454, 476183]} |
| 示例 posts_list | `https://api.anime-pictures.net/api/v3/posts?page=1&search_tag=hatsune+miku&posts_per_page=2&order_by=rating` | 200 | {"requested_page": 1, "page_number": 1, "posts_per_page": 2, "response_posts_count": 2, "posts_count": 21008, "max_pages": 10503, "count": 2, "ids": [662233, 496255]} |
| 示例 post_show | `https://api.anime-pictures.net/api/v3/posts/382872` | 200 | {"post_id": 382872, "width": 2864, "height": 5159, "score": 0.0, "score_number": 35, "tags_count": 26, "ext": ".png", "detail_keys": ["post", "user", "moderator", "tags", "file_url", "star_it", "favorites_users", "tied"], "user_id": 18830, "user_name": "卂丂口レ尺工乂", "tag_count": 26} |
| 示例 post_comments | `https://api.anime-pictures.net/api/v3/posts/382872/comments` | 200 | {"success": true, "count": 1, "first": {"id": 174693, "datetime": "2026-09-19T09:13:46.230319", "language": "en", "chars": 38, "user_id": 290656, "user_name": "FikriHarjantoKesumo"}} |
| 示例 user_show | `https://api.anime-pictures.net/api/v3/users/18830` | 200 | {"user_id": 18830, "name": "卂丂口レ尺工乂", "avatar_version": 27, "isavatar": true, "site_score": 0, "groups": ["user", "commiter"], "gender": 1, "register_date": "2012-11-01T19:57:11.566739"} |
| 示例 comment_show | `https://api.anime-pictures.net/api/v3/comments/174693` | 200 | {"id": 174693, "datetime": "2026-09-19T09:13:46.230319", "language": "en", "chars": 38, "user_id": 290656, "user_name": "FikriHarjantoKesumo"} |

### 初版示例发现的真实字段差异

`browse_resources.py` 初次运行于 UTC 13:51:04，完成一次 `post_show(382872)` 后，
按输入文档“详情顶层固定九键”的假设读取 `detail['source']`，触发 `KeyError: 'source'`，退出 1。
该次响应已成功解析 JSON，但脚本在打印前失败，**未记录 HTTP 状态码，不补写成 200**。
修正后的示例打印实际 `detail_keys`，不再无条件读取 `source`，也没有补默认值或返回空来源；
后续真实响应为 HTTP 200，顶层恰有八键：`post/user/moderator/tags/file_url/star_it/favorites_users/tied`。
最终示例四次 GET 全部通过，证明这个真实数据差异不再导致脚本失败。

初版冒烟也曾在 UTC 13:50:40–13:50:59 完成 10 次请求，8×200 + 预期 410/400、退出 0。
发现详情字段可缺失后，同步移除了冒烟对 `source/moderator/favorites_users/tied` 的固定键集假设，
再运行的最终版本结果如上；详情 ID、预览字段、用户与标签检查仍保留。
因此整个接入过程累计 **117 GET**（90 直接观察 + 两次各 10 的冒烟 + 列表示例 2 + 初版浏览 1 + 修正版浏览 4）；
其中 116 次明确记录状态（98×200、6×400、2×403、6×404、3×410、1×500），另 1 次只知成功 JSON 而未打印状态。
没有网络失败后的重试，也没有为了掩盖初版错误而覆盖其执行记录。

### 边界与未实测

- 新客户端实际执行的方法是 `posts_list/post_show/post_comments/tags_list/tag_show/users_list/user_show/comments_list/comment_show`；
  `service_info/post_tags/image_get` 只有直接路由观察，不把它们标成 Python 方法已执行。
- `post_create` 没有执行；请求体结构、成功状态码、Authorization scheme、Cookie 登录成功与权限分支均未知。
  输入中的 POST 401、OPTIONS/CORS 动词说明没有在本轮复测；不据此发明 PUT/PATCH/DELETE 或登录接口。
- `image_get` 的成功字节未实测；媒体 CDN、头像路径、预览格式变体与原图公式均未请求。
  三档预览仅观察了 JSON 中的地址字符串。
- 未编码原始空格、`lang`、全部忽略参数、完整分页边界、其它排序/过滤组合、`ldate` 负数或大于 8、
  成功认证、写入、其它主机/部署未测。`ldate` 区间长度与标签类别名称仍属推断。
- 没有运行 formatter、lint、构建、安装归档、CI 或项目测试套件；保留的测试仅为每次最多十请求的匿名冒烟。


## Cosine：匿名只读实测（2026-09-20）

Cosine Gallery（`https://pic.cosine.ren`）的接入依据是匿名响应，以及公开仓库
[SomeACG/SomeACG-Next](https://github.com/SomeACG/SomeACG-Next) 六个单文件的只读源码。
源码出处、两条未执行的 POST 与输入资料纠错见[契约附注](cosine-contract-notes.md)。
以下区分直接 HTTP 观察与实际运行 Python 客户端；字段和计数都是本次快照，不承诺固定值。

### 直接路由校对：69 次 GET

第一批 18 次、第二批 51 次，共 **69 次匿名 GET：200×57、400×2、404×3、500×7**。
每次串行，前一次结束后至少等 1.3 秒；无重试、无跳转、无登录、无 POST、无媒体下载。
68 个响应的 `Content-Type` 为 `application/json`，`feed.xml` 为 `application/xml; charset=utf-8`。
请求都带 `Origin: https://example.com`；这些响应中没有 `Access-Control-Allow-Origin` 或 `RateLimit-*`，
但这不证明本站永久没有 CORS 配置或限流。两批覆盖全部 11 条读取路由。

| # | 真实 URL | HTTP | 正文关键字段 |
| :--- | :--- | :--- | :--- |
| 1 | `https://pic.cosine.ren/api/list?page=1&pageSize=2` | 200 | {images,total}；images=2；total=4953；ids=[5003, 5002] |
| 2 | `https://pic.cosine.ren/api/list?page=2&pageSize=2` | 200 | {images,total}；images=2；total=4953；ids=[5001, 5000] |
| 3 | `https://pic.cosine.ren/api/artwork/1` | 200 | {json,meta}；json=object；条数=1；ids=[1]；meta.values=3 键 |
| 4 | `https://pic.cosine.ren/api/random?count=1` | 200 | {json,meta}；json=object；条数=1；ids=[1666]；meta.values=3 键 |
| 5 | `https://pic.cosine.ren/api/random?count=3` | 200 | {json,meta}；json=array；条数=3；ids=[2042, 2741, 3927]；meta.values=9 键 |
| 6 | `https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2` | 200 | {success,data}；hits=2；{'query': '初音', 'total': 255, 'limit': 2, 'offset': 0}；ids=['2760', '1689'] |
| 7 | `https://pic.cosine.ren/api/search?limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 1000, 'limit': 2, 'offset': 0}；ids=['3363', '3362'] |
| 8 | `https://pic.cosine.ren/api/search?limit=2&offset=100000` | 200 | {success,data}；hits=0；{'query': '', 'total': 1000, 'limit': 2, 'offset': 1000}；ids=[] |
| 9 | `https://pic.cosine.ren/api/search/suggestions?q=miku&limit=2` | 200 | {success,data}；suggestions=2；query=miku；项字段 text/type |
| 10 | `https://pic.cosine.ren/api/tag?tag=GenshinImpact&start=0&limit=2` | 200 | 裸作品数组 2 项；ids=[4971, 4970]；无 total |
| 11 | `https://pic.cosine.ren/api/tags` | 200 | 裸数组 2128 项；首项 {'tag': '甜妹', 'count': 1309}；RuanMei count=9 |
| 12 | `https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&page=1&pageSize=2` | 200 | {images,total}；images=2；total=78；ids=[4869, 4827] |
| 13 | `https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&infoOnly=true` | 200 | 裸资料对象；{'author': 'makoron117', 'authorid': '54390221', 'platform': 'pixiv', 'artworkCount': 78} |
| 14 | `https://pic.cosine.ren/api/artists?page=1&pageSize=2&sortBy=artworks` | 200 | {artists,total,hasNextPage}；artists=2；total=1708；hasNextPage=True；authorid=['54390221', '6662895'] |
| 15 | `https://pic.cosine.ren/api/search/admin` | 200 | {success,data}；{'totalImages': 4953, 'indexedImages': 3353, 'indexHealth': 'partial', 'lastSyncTime': '2026-09-19T16:42:34.383Z'} |
| 16 | `https://pic.cosine.ren/feed.xml` | 200 | RSS 2.0；items=20；lastBuildDate=Sun, 10 Aug 2025 13:07:22 GMT |
| 17 | `https://pic.cosine.ren/api/tag?tag=RuanMei&start=0&limit=100` | 200 | 裸作品数组 10 项；ids=[4203, 282, 103, 87]；无 total |
| 18 | `https://pic.cosine.ren/api/search?tags=RuanMei&limit=100` | 200 | {success,data}；hits=9；{'query': '', 'total': 9, 'limit': 100, 'offset': 0}；ids=['282', '103'] |
| 19 | `https://pic.cosine.ren/api/list` | 200 | {images,total}；images=10；total=4953；ids=[5003, 5002, 5001, 5000] |
| 20 | `https://pic.cosine.ren/api/list?pageSize=100` | 200 | {images,total}；images=100；total=4953；ids=[5003, 5002, 5001, 5000] |
| 21 | `https://pic.cosine.ren/api/list?pageSize=0` | 200 | {images,total}；images=0；total=4953；ids=[] |
| 22 | `https://pic.cosine.ren/api/list?pageSize=-1` | 200 | {images,total}；images=1；total=4953；ids=[1] |
| 23 | `https://pic.cosine.ren/api/list?page=0&pageSize=2` | 500 | {"error": "获取图片列表失败"} |
| 24 | `https://pic.cosine.ren/api/list?page=-1&pageSize=2` | 500 | {"error": "获取图片列表失败"} |
| 25 | `https://pic.cosine.ren/api/list?page=100000&pageSize=2` | 200 | {images,total}；images=0；total=4953；ids=[] |
| 26 | `https://pic.cosine.ren/api/artwork/999999999` | 404 | {"error": "未找到该作品"} |
| 27 | `https://pic.cosine.ren/api/artwork/abc` | 500 | {"error": "服务器错误"} |
| 28 | `https://pic.cosine.ren/api/artwork/3840` | 200 | {json,meta}；json=object；条数=1；ids=[3840]；meta.values=3 键 |
| 29 | `https://pic.cosine.ren/api/random` | 200 | {json,meta}；json=object；条数=1；ids=[3408]；meta.values=3 键 |
| 30 | `https://pic.cosine.ren/api/random?count=0` | 200 | {json,meta}；json=object；条数=1；ids=[423]；meta.values=3 键 |
| 31 | `https://pic.cosine.ren/api/random?count=-5` | 200 | {json,meta}；json=object；条数=1；ids=[3037]；meta.values=3 键 |
| 32 | `https://pic.cosine.ren/api/random?count=100` | 200 | {json,meta}；json=array；条数=20；ids=[101, 221, 258, 313, 385, 392, 417, 840, 1001, 1326, 1786, 2033, 2083, 2138, 2627, 2674, 2702, 2888, 2897, 3096]；meta.values=60 键 |
| 33 | `https://pic.cosine.ren/api/random?count=abc` | 404 | {"error": "未找到图片"} |
| 34 | `https://pic.cosine.ren/api/search` | 200 | {success,data}；hits=20；{'query': '', 'total': 1000, 'limit': 20, 'offset': 0}；ids=['3363', '3362'] |
| 35 | `https://pic.cosine.ren/api/search?q=&limit=2&offset=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 1000, 'limit': 2, 'offset': 2}；ids=['3361', '3360'] |
| 36 | `https://pic.cosine.ren/api/search?limit=500` | 200 | {success,data}；hits=100；{'query': '', 'total': 1000, 'limit': 100, 'offset': 0}；ids=['3363', '3362'] |
| 37 | `https://pic.cosine.ren/api/search?sort=bogus&limit=2` | 500 | {"success": false, "error": "Internal search error", "message": "Invalid syntax for the sort parameter: expected expression ending by `:asc` or `:desc`, found `bogus`."} |
| 38 | `https://pic.cosine.ren/api/search?limit=-1` | 500 | {"success": false, "error": "Internal search error", "message": "Invalid value type at `.limit`: expected a positive integer, but found a negative integer: `-1`"} |
| 39 | `https://pic.cosine.ren/api/search?limit=2&offset=-5` | 500 | {"success": false, "error": "Internal search error", "message": "Invalid value type at `.offset`: expected a positive integer, but found a negative integer: `-5`"} |
| 40 | `https://pic.cosine.ren/api/search?platform=pixiv&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 1000, 'limit': 2, 'offset': 0}；ids=['3363', '3362'] |
| 41 | `https://pic.cosine.ren/api/search?platform=twitter&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 1000, 'limit': 2, 'offset': 0}；ids=['3360', '3355'] |
| 42 | `https://pic.cosine.ren/api/search?platform=unknown&limit=2` | 200 | {success,data}；hits=0；{'query': '', 'total': 0, 'limit': 2, 'offset': 0}；ids=[] |
| 43 | `https://pic.cosine.ren/api/search?tags=GenshinImpact&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 166, 'limit': 2, 'offset': 0}；ids=['3342', '3337'] |
| 44 | `https://pic.cosine.ren/api/search?tags=genshinimpact&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 166, 'limit': 2, 'offset': 0}；ids=['3342', '3337'] |
| 45 | `https://pic.cosine.ren/api/search?tags=%E5%8E%9F%E7%A5%9E&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 510, 'limit': 2, 'offset': 0}；ids=['3358', '3342'] |
| 46 | `https://pic.cosine.ren/api/search?tags=%E5%8E%9F%E7%A5%9E,GenshinImpact&limit=100` | 200 | {success,data}；hits=100；{'query': '', 'total': 160, 'limit': 100, 'offset': 0}；ids=['3342', '3337'] |
| 47 | `https://pic.cosine.ren/api/search?r18=true&limit=100` | 200 | {success,data}；hits=7；{'query': '', 'total': 7, 'limit': 100, 'offset': 0}；ids=['2822', '734'] |
| 48 | `https://pic.cosine.ren/api/search?r18=false&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 1000, 'limit': 2, 'offset': 0}；ids=['3363', '3362'] |
| 49 | `https://pic.cosine.ren/api/search?r18=1&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 1000, 'limit': 2, 'offset': 0}；ids=['3363', '3362'] |
| 50 | `https://pic.cosine.ren/api/search?sort=width:asc&limit=2` | 200 | {success,data}；hits=2；{'query': '', 'total': 1000, 'limit': 2, 'offset': 0}；ids=['1421', '429'] |
| 51 | `https://pic.cosine.ren/api/search/suggestions?q=miku` | 200 | {success,data}；suggestions=10；query=miku；项字段 text/type |
| 52 | `https://pic.cosine.ren/api/search/suggestions?q=miku&limit=50` | 200 | {success,data}；suggestions=15；query=miku；项字段 text/type |
| 53 | `https://pic.cosine.ren/api/search/suggestions?q=a` | 200 | {success,data}；suggestions=0；query=a；项字段 text/type |
| 54 | `https://pic.cosine.ren/api/tag` | 400 | {"error": "标签参数缺失"} |
| 55 | `https://pic.cosine.ren/api/tag?tag=GenshinImpact&start=2&limit=2` | 200 | 裸作品数组 2 项；ids=[4967, 4964]；无 total |
| 56 | `https://pic.cosine.ren/api/tag?tag=%23GenshinImpact&limit=2` | 200 | 裸作品数组 0 项；ids=[]；无 total |
| 57 | `https://pic.cosine.ren/api/tag?tag=zzzznotexist&limit=2` | 200 | 裸作品数组 0 项；ids=[]；无 total |
| 58 | `https://pic.cosine.ren/api/tag?tag=genshinimpact&limit=2` | 200 | 裸作品数组 2 项；ids=[4971, 4970]；无 total |
| 59 | `https://pic.cosine.ren/api/tag?tag=%E5%8E%9F%E7%A5%9E,GenshinImpact&limit=2` | 200 | 裸作品数组 0 项；ids=[]；无 total |
| 60 | `https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&page=2&pageSize=2` | 200 | {images,total}；images=2；total=78；ids=[4823, 4796] |
| 61 | `https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&infoOnly=1&pageSize=2` | 200 | {images,total}；images=2；total=78；ids=[4869, 4827] |
| 62 | `https://pic.cosine.ren/api/artist?authorid=54390221` | 400 | {"error": "缺少必要参数 platform 或 authorid"} |
| 63 | `https://pic.cosine.ren/api/artist?platform=pixiv&authorid=abc` | 500 | {"error": "获取画师数据失败"} |
| 64 | `https://pic.cosine.ren/api/artist?platform=pixiv&authorid=999999999&infoOnly=true` | 404 | {"error": "未找到该画师"} |
| 65 | `https://pic.cosine.ren/api/artists` | 200 | {artists,total,hasNextPage}；artists=20；total=1708；hasNextPage=True；authorid=['54390221', '6662895'] |
| 66 | `https://pic.cosine.ren/api/artists?page=2&pageSize=2&sortBy=artworks` | 200 | {artists,total,hasNextPage}；artists=2；total=1708；hasNextPage=True；authorid=['15034125', '22298878'] |
| 67 | `https://pic.cosine.ren/api/artists?page=1&pageSize=2&sortBy=random` | 200 | {artists,total,hasNextPage}；artists=2；total=1708；hasNextPage=True；authorid=['1294719251849199616', '1081773718962024448'] |
| 68 | `https://pic.cosine.ren/api/artists?page=1&pageSize=2&sortBy=lastUpdate` | 200 | {artists,total,hasNextPage}；artists=2；total=1708；hasNextPage=True；authorid=['162416678', '1269027794'] |
| 69 | `https://pic.cosine.ren/api/artists?page=1&pageSize=2&sortBy=unknown` | 200 | {artists,total,hasNextPage}；artists=2；total=1708；hasNextPage=True；authorid=['54390221', '6662895'] |

关键对照：

- 四类 JSON 已逐条确认：详情/随机 `{json,meta}`；图片/画师列表 `{images,total}`、画师榜
  `{artists,total,hasNextPage}`；搜索/建议/索引状态 `{success,data}`；标签两条路由是裸数组。
  `artist_images(infoOnly=True)` 另返回裸资料对象，不属于四种列表结构；RSS 返回 XML 原文。
- 随机 `count=1` 是对象，`count=3` 是数组；多条的 `meta.values` 是 `0.userid` 等带下标的键。
- 搜索空关键词 `total=1000`，但索引状态是 `indexedImages=3353`、`totalImages=4953`；
  `offset=100000` 被站点回显为 1000 并给空 `hits`，客户端没有钳位。
- `RuanMei` 的标签 `count=9`，数据库标签路径回 10 张图（8 个 `pid`、标签出现 14 次），搜索回 9 条。
  结合标签路由源码的 `imageTag.groupBy` / `_count.tag`，确认 `count` 是标签记录行数，不能换算成图片数。
- RSS 有 20 条，但前三 `guid=3290/3288/3289`、缓存 `lastBuildDate` 为 2025-08-10；
  当前列表的首两条却是 `5003/5002`，不能称它为当前最新 20 张。

### 实际命令与最终脚本结果

复制完整包内配置为自己的文件后可这样运行（下面使用中性配置文件名）：

```bash
python -X utf8 test/cosine.py --config my-anybooru.json
python -X utf8 examples/cosine/list_images.py --config my-anybooru.json
python -X utf8 examples/cosine/browse_resources.py --config my-anybooru.json
```

| 脚本 | 最终请求数 | HTTP | 退出码 | 结果 |
| :--- | :--- | :--- | :--- | :--- |
| `test/cosine.py` | 10 | 200×9、预期404×1 | 0 | `SUMMARY cosine &#124; requests=10 &#124; passed=10 failed=0` |
| `examples/cosine/list_images.py` | 4 | 200×4 | 0 | 两页列表；带 platform/r18/sort 的搜索按 offset=0/2 翻页 |
| `examples/cosine/browse_resources.py` | 4 | 200×4 | 0 | 详情、标签数组、画师作品与画师资料对象 |

最终三者标准错误均为空；各次请求间隔至少 1.3 秒。冒烟和列表最终运行的 UTC 时间分别为
2026-09-19 17:03:07–17:03:23、17:03:25–17:03:30，浏览示例是 17:01:18–17:01:25。
冒烟检查了实际 URL/状态、四种外壳、详情 ID、分页无重复、随机单/多形状、RSS 原文和缺失资源的
`AnybooruHTTPError`；错误保留 `data`、`body` 与 `last_call`。没有执行写方法。

| 调用 | 真实 URL | HTTP | 关键字段 |
| :--- | :--- | :--- | :--- |
| 冒烟 image_list page 1 | `https://pic.cosine.ren/api/list?page=1&pageSize=2` | 200 | images:list,total:int；page=1 total=4953 images=2 ids=[5003, 5002] first=5003 pid=2100902205171937298 platform=twitter page=1 rawurl=https://pbs.twimg.com/media/HSfnUtFakAAhHtG.jpg?name=orig；no earlier page to compare |
| 冒烟 image_list page 2 | `https://pic.cosine.ren/api/list?page=2&pageSize=2` | 200 | images:list,total:int；page=2 total=4953 images=2 ids=[5001, 5000] first=5001 pid=2098778224214024600 platform=twitter page=1 rawurl=https://pbs.twimg.com/media/HSBbOj2a0AASMiB.jpg?name=orig；no id shared with page 1 |
| 冒烟 artwork_show configured id | `https://pic.cosine.ren/api/artwork/1` | 200 | json:dict,meta:dict；meta_keys=['values'] values=3 id=1 pid=1740331347254948074 platform=twitter page=1 tags=8 |
| 冒烟 image_random count 1 | `https://pic.cosine.ren/api/random?count=1` | 200 | json:dict,meta:dict；count=1 json=dict artworks=1 ids=[428] hosts=['piv.cosine.ren'] |
| 冒烟 image_random count 3 | `https://pic.cosine.ren/api/random?count=3` | 200 | json:list,meta:dict；count=3 json=list artworks=3 ids=[102, 998, 3909] hosts=['pbs.twimg.com'] |
| 冒烟 search configured query | `https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2` | 200 | success:bool,data:dict；hits:list,query:str,total:int,limit:int,offset:int,processingTimeMs:int；query='初音' total=255 limit=2 offset=0 processingTimeMs=4 hits=2 hit_ids=['2760', '1689'] |
| 冒烟 tag_images configured tag | `https://pic.cosine.ren/api/tag?start=0&limit=2&tag=GenshinImpact` | 200 | items=2 ids=[4971, 4970] tag='GenshinImpact' start=0 limit=2 |
| 冒烟 tag_list | `https://pic.cosine.ren/api/tags` | 200 | items=2128 first='甜妹'/1309 names=['甜妹', '女孩子', '崩坏星穹铁道', '原神', '精选'] |
| 冒烟 feed | `https://pic.cosine.ren/feed.xml` | 200 | chars=16593 items=20 content_type='application/xml; charset=utf-8' |
| 冒烟 artwork_show missing id | `https://pic.cosine.ren/api/artwork/999999999` | 404 | data=dict body_chars=18 content_type='application/json' last_call=HTTP 404 https://pic.cosine.ren/api/artwork/999999999 |
| 示例 image_list | `https://pic.cosine.ren/api/list?page=1&pageSize=2` | 200 | {"requested_page": 1, "total": 4953, "count": 2, "ids": [5003, 5002]} |
| 示例 image_list | `https://pic.cosine.ren/api/list?page=2&pageSize=2` | 200 | {"requested_page": 2, "total": 4953, "count": 2, "ids": [5001, 5000]} |
| 示例 search | `https://pic.cosine.ren/api/search?offset=0&q=%E5%88%9D%E9%9F%B3&limit=2&platform=twitter&r18=false&sort=create_time%3Adesc` | 200 | {"requested_offset": 0, "success": true, "query": "初音", "total": 125, "limit": 2, "offset": 0, "processing_time_ms": 9, "count": 2, "ids": ["2760", "1689"], "hits": [{"id": "2760", "field_keys": ["_formatted", "ai", "author", "authorid", "create_time", "filename", "height", "id", "pid", "platform", "r18", "rawurl", "searchable_content", "tags", "thumburl", "title", "width"]}, {"id": "1689", "field_keys": ["_formatted", "ai", "author", "authorid", "create_time", "filename", "height", "id", "pid", "platform", "r18", "rawurl", "searchable_content", "tags", "thumburl", "title", "width"]}]} |
| 示例 search | `https://pic.cosine.ren/api/search?offset=2&q=%E5%88%9D%E9%9F%B3&limit=2&platform=twitter&r18=false&sort=create_time%3Adesc` | 200 | {"requested_offset": 2, "success": true, "query": "初音", "total": 125, "limit": 2, "offset": 2, "processing_time_ms": 72, "count": 2, "ids": ["3041", "2721"], "hits": [{"id": "3041", "field_keys": ["_formatted", "ai", "author", "authorid", "create_time", "filename", "height", "id", "pid", "platform", "r18", "rawurl", "searchable_content", "tags", "thumburl", "title", "width"]}, {"id": "2721", "field_keys": ["_formatted", "ai", "author", "authorid", "create_time", "filename", "height", "id", "pid", "platform", "r18", "rawurl", "searchable_content", "tags", "thumburl", "width"]}]} |
| 示例 artwork_show | `https://pic.cosine.ren/api/artwork/1` | 200 | {"artwork_id": 1, "meta_value_keys": ["authorid", "create_time", "userid"], "meta_value_count": 3, "id": 1, "pid": "1740331347254948074", "platform": "twitter", "page": 1, "userid": "6030777595", "author": "bshi_edayo", "authorid": "1456997233363419136", "width": 1620, "height": 2880, "filename": "1740331347254948074_1.jpg", "extension": "jpg", "size": 675622, "guest": true, "r18": false, "ai": false, "tag_count": 8, "distinct_tag_count": 4} |
| 示例 tag_images | `https://pic.cosine.ren/api/tag?start=0&limit=2&tag=GenshinImpact` | 200 | {"tag": "GenshinImpact", "start": 0, "limit": 2, "count": 2, "ids": [4971, 4970]} |
| 示例 artist_images | `https://pic.cosine.ren/api/artist?page=1&pageSize=2&platform=pixiv&authorid=54390221` | 200 | {"platform": "pixiv", "authorid": "54390221", "page": 1, "total": 78, "count": 2, "ids": [4869, 4827]} |
| 示例 artist_images infoOnly | `https://pic.cosine.ren/api/artist?infoOnly=true&platform=pixiv&authorid=54390221` | 200 | {"platform": "pixiv", "authorid": "54390221", "author": "makoron117", "artwork_count": 78} |

### 初版示例发现的字段差异与修正

初版 `list_images.py` 已打印三次 200，第四次搜索（同过滤条件、`offset=2`）取得 JSON 后，
对 `hit['title']` 的读取触发 `KeyError: 'title'`，退出 1。该请求在打印状态之前失败，
**没有记录状态码，不能事后补写成 200**。修正只删除示例对标题必有的假设，改为打印实际 `field_keys`，
没有补默认标题、没有换路由、没有改服务端数据；冒烟也移除了 `title` 必有断言。
只重新运行这两个受影响脚本：最终均退出 0。新样本明确显示 `id='2721'` 没有 `title`，
同一页 `id='3041'` 有 `title`；更早的直接观察中，`RuanMei` 命中 `id='38'` 也缺该字段。
客户端一直返回完整原始 JSON，未填补缺项。

初版冒烟同样是 10 次请求、9×200+预期404、退出 0（UTC 17:00:50–17:01:09）。
本轮 API/RSS 累计 **101 次 GET**＝69 直接观察 + 两轮各10的冒烟 + 初版列表4 + 修正版列表4 + 浏览4；
其中 **100 次状态明确：200×86、400×2、404×5、500×7**，另一次只知成功解析 JSON 而未打印状态。
初版失败记录没有被最终成功覆盖；未为了增加覆盖而复跑其它脚本。

### 边界与未实测

- 实际运行的原生方法是 `image_list/artwork_show/image_random/search/tag_images/tag_list/artist_images/feed`
  共 8 个；`search_suggestions/artist_list/search_index_status` 只有直接 HTTP 观察，不说包装方法已执行。
- **两个 POST 均零请求**：尤其 `POST /api/search/admin` 会重建/删除站点索引，公开路由源码没有鉴权检查，
  本轮绝未执行；`artwork_revalidate` 连空密钥401都没有请求。成功、失败、密钥和真实权限分支均未实测。
- 媒体主机、原图备份、Referer要求、RSS别名、页面路由、其它部署、完整参数取值与资源上限均未请求或穷举。
  源码里 `lastSyncTime: new Date()` 不是可信同步记录，公开仓库代码也不证明线上部署版本。
- 未运行 formatter、lint、构建、安装归档、CI 或项目测试套件；保留的测试仅为每次最多十请求的匿名冒烟。


## nhentai：匿名只读实测（2026-09-20）

实现范围是 `nhentai.net` API v2；`nhentai.to` 只作契约对照，不加入客户端。
权威来源是站点自带的 [OpenAPI](https://nhentai.net/api/v2/openapi.json) 与
[changelog](https://nhentai.net/api/v2/changelog)，不是本地服务端源码。
规范与候选资料的逐项差异见 [契约附注](nhentai-contract-notes.md)。

### 运行命令与结果

以下使用中性配置文件名；文件内容沿用包内配置，只填使用者自己的网络设置。

```bash
.venv/Scripts/python.exe -c "import anybooru; from anybooru import Nhentai"
.venv/Scripts/python.exe -X utf8 test/nhentai.py --config my-anybooru.json
.venv/Scripts/python.exe -X utf8 examples/nhentai/list_galleries.py --config my-anybooru.json
.venv/Scripts/python.exe -X utf8 examples/nhentai/browse_resources.py --config my-anybooru.json
```

| 项目 | UTC 起止（2026-09-20） | HTTP | stdout 摘要 | stderr / 退出码 |
| --- | --- | --- | --- | --- |
| 导入 | 10:32:21.712660–10:32:21.899330 | 无请求 | 无输出，Nhentai 可导入 | 空 / 0 |
| 冒烟 | 10:32:21.909839–10:32:51.241830 | 8×200、预期404、预期400 | `SUMMARY nhentai \| requests=10 \| passed=10 failed=0` | 空 / 0 |
| 列表/搜索示例 | 10:32:51.244961–10:32:56.309175 | 3×200 | 两页各2项，搜索25项；先打印 HTTP 行，再打印结构摘要 | 空 / 0 |
| 资源示例 | 10:32:56.313173–10:33:04.796956 | 5×200 | 画廊18页、标签12227、批量标签2项、评论0项、配置主机列表各4项 | 空 / 0 |

脚本均显式传 `api_key=''`、不跟随重定向、不重试、不请求媒体；脚本内部按配置串行暂停。
本次没有冒烟/示例初版失败。契约抓取的准备阶段曾因把整数超时值当作序列而抛 `TypeError`，
当时尚未发出 HTTP；改用配置中的整数后完成抓取，不计为站点错误或额外请求。

### 冒烟的十个请求

这十次均是 Python 原生方法调用；所有响应的 Content-Type 都是 `application/json`。

| # | 方法 / 真实 URL | 状态 | 输出观察 |
| --- | --- | --- | --- |
| 1 | `gallery_list` → `https://nhentai.net/api/v2/galleries?page=1&per_page=2` | 200 | IDs 682610、682609；per_page=2；total=646010、num_pages=323039 |
| 2 | `gallery_list` → `https://nhentai.net/api/v2/galleries?page=2&per_page=2` | 200 | IDs 682608、682607；per_page=2 |
| 3 | `gallery_show` → `https://nhentai.net/api/v2/galleries/658856` | 200 | id=658856、media_id=4006343；18个pages对象、15个标签；title对象3键 |
| 4 | `search` → `https://nhentai.net/api/v2/search?sort=date&page=1&query=language%3Aenglish` | 200 | result25项、total=147499、num_pages=5900 |
| 5 | `gallery_popular` → `https://nhentai.net/api/v2/galleries/popular` | 200 | 直接数组5项；不把5设为断言 |
| 6 | `tag_show` → `https://nhentai.net/api/v2/tags/language/english` | 200 | 单个对象、id=12227；type/slug对应请求 |
| 7 | `gallery_comment_count` → `https://nhentai.net/api/v2/galleries/658856/comments/count` | 200 | 裸整数0 |
| 8 | `gallery_comments` → `https://nhentai.net/api/v2/galleries/658856/comments?per_page=2` | 200 | result=[]、num_pages=0、total=0 |
| 9 | `gallery_show` → `https://nhentai.net/api/v2/galleries/999999999` | 404 | AnybooruHTTPError；data为dict、body29字符、last_call保留状态与URL |
| 10 | `gallery_list` → `https://nhentai.net/api/v2/galleries?page=0&per_page=2` | 400 | AnybooruHTTPError；data为dict、body100字符、last_call保留状态与URL |

页间不要求 ID 互斥：新作品可能在两次请求之间移动页边界。检查响应结构与资源编号，
不锁定动态总数、收藏数、热门条数，也不把空评论当成失败。

### 两个示例的八个请求

所有响应均为 **200 application/json**。

| 脚本 | 方法 / 真实 URL | 实际摘要 |
| --- | --- | --- |
| list_galleries | `gallery_list` → `https://nhentai.net/api/v2/galleries?page=1&per_page=2` | 2项；682610、682609 |
| list_galleries | `gallery_list` → `https://nhentai.net/api/v2/galleries?page=2&per_page=2` | 2项；682608、682607 |
| list_galleries | `search` → `https://nhentai.net/api/v2/search?sort=date&page=1&query=language%3Aenglish` | 25项，打印实际字段名、编号与尺寸，不打印标题 |
| browse_resources | `gallery_show` → `https://nhentai.net/api/v2/galleries/658856` | cover350×496、18页、15标签；未出现附加块 |
| browse_resources | `tag_show` → `https://nhentai.net/api/v2/tags/language/english` | id12227；对象含is_community与pending_describe_id键 |
| browse_resources | `tag_ids` → `https://nhentai.net/api/v2/tags/ids?ids=12227%2C6346` | 2个language类型标签、ID12227和6346 |
| browse_resources | `gallery_comments` → `https://nhentai.net/api/v2/galleries/658856/comments?page=1&per_page=2` | 评论数组为空；没有非空正文的成功样本 |
| browse_resources | `site_config` → `https://nhentai.net/api/v2/config` | image_servers4项、thumb_servers4项、announcement=null |

### 规范与候选资料核对：直接 HTTP 观察

以下 **61 个 GET** 的 UTC 为 **10:17:50.836350–10:24:35.156212**：
**39×200、5×400、7×401、1×403、9×404**。
每个探测项只请求一次、串行间隔1.3秒，不跟随跳转、不重试；HTTP错误也保留完整正文，
抓取程序退出0表示记录完成，不表示每个端点都200。
这是直接 HTTP 请求的证据，不冒称对应的 Python 原生方法都执行过。
表内的计数是当次样本，不是固定契约；对象一栏列的是正文首层字段。

| # | 真实 URL（GET） | HTTP | Content-Type | 正文首层 |
| --- | --- | --- | --- | --- |
| 1 | `https://nhentai.net/api/v2/openapi.json` | 200 | `application/json` | 对象：`openapi, info, paths, components, tags` |
| 2 | `https://nhentai.net/api/v2/config` | 200 | `application/json` | 对象：`image_servers, thumb_servers, announcement` |
| 3 | `https://nhentai.net/api/v2/cdn` | 200 | `application/json` | 对象：`image_servers, thumb_servers` |
| 4 | `https://nhentai.net/api/v2` | 200 | `application/json` | 对象：`version, message` |
| 5 | `https://nhentai.net/api/v2/changelog` | 200 | `text/html; charset=utf-8` | 文本：10464 UTF-8 字节 |
| 6 | `https://nhentai.net/api/v2/galleries?page=1&per_page=2` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 2 项 |
| 7 | `https://nhentai.net/api/v2/galleries?page=2&per_page=2` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 2 项 |
| 8 | `https://nhentai.net/api/v2/galleries/popular` | 200 | `application/json` | 数组：5 项 |
| 9 | `https://nhentai.net/api/v2/galleries/random` | 200 | `application/json` | 对象：`id` |
| 10 | `https://nhentai.net/api/v2/galleries/658856` | 200 | `application/json` | 对象：`id, media_id, title, cover, thumbnail, scanlator, upload_date, tags, num_pages, num_favorites, pages` |
| 11 | `https://nhentai.net/api/v2/galleries/658856?include=comments%2Crelated%2Cfavorite%2Csuggestions` | 200 | `application/json` | 对象：`id, media_id, title, cover, thumbnail, scanlator, upload_date, tags, num_pages, num_favorites, pages, comments, comment_count, related, suggestions` |
| 12 | `https://nhentai.net/api/v2/galleries/658856/related` | 200 | `application/json` | 对象：`result`；result 5 项 |
| 13 | `https://nhentai.net/api/v2/galleries/658856/comments?page=1&per_page=2` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 0 项 |
| 14 | `https://nhentai.net/api/v2/galleries/658856/comments/count` | 200 | `application/json` | 整数：0 |
| 15 | `https://nhentai.net/api/v2/galleries/658856/suggestions` | 200 | `application/json` | 对象：`result`；result 0 项 |
| 16 | `https://nhentai.net/api/v2/galleries/tagged?tag_id=12227&page=1&per_page=2` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 2 项 |
| 17 | `https://nhentai.net/api/v2/search?query=language%3Aenglish&page=1` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 25 项 |
| 18 | `https://nhentai.net/api/v2/tags/language/english` | 200 | `application/json` | 对象：`id, type, name, slug, url, count, description, is_community, pending_describe_id` |
| 19 | `https://nhentai.net/api/v2/tags/ids?ids=12227%2C6346` | 200 | `application/json` | 数组：2 项 |
| 20 | `https://nhentai.net/api/v2/tags/tag?per_page=1` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 120 项 |
| 21 | `https://nhentai.net/api/v2/taxonomy?per_page=2` | 200 | `application/json` | 对象：`result, has_more, num_pages, total`；result 2 项 |
| 22 | `https://nhentai.net/api/v2/taxonomy/resolved?per_page=2` | 200 | `application/json` | 对象：`result, has_more, num_pages, total`；result 50 项 |
| 23 | `https://nhentai.net/api/v2/taxonomy/stats` | 200 | `application/json` | 对象：`pending, accepted_total, rejected_total, accepted_30d, accepted_7d, created_30d, renamed_30d, merged_30d, described_30d, trending_count, active_count, declined_count, recent_accepted` |
| 24 | `https://nhentai.net/api/v2/gts/backlog?per_page=2` | 200 | `application/json` | 对象：`result, has_more, num_pages, total`；result 2 项 |
| 25 | `https://nhentai.net/api/v2/gts/new-tags?limit=2` | 200 | `application/json` | 对象：`result`；result 2 项 |
| 26 | `https://nhentai.net/api/v2/user` | 401 | `application/json` | 对象：`error`；Authentication required |
| 27 | `https://nhentai.net/api/v2/favorites` | 401 | `application/json` | 对象：`error`；Authentication required |
| 28 | `https://nhentai.net/api/v2/favorites/random` | 401 | `application/json` | 对象：`error`；Authentication required |
| 29 | `https://nhentai.net/api/v2/blacklist` | 401 | `application/json` | 对象：`error`；Authentication required |
| 30 | `https://nhentai.net/api/v2/blacklist/ids` | 401 | `application/json` | 对象：`error`；Authentication required |
| 31 | `https://nhentai.net/api/v2/galleries/658856/favorite` | 401 | `application/json` | 对象：`error`；Authentication required |
| 32 | `https://nhentai.net/api/v2/user/keys` | 401 | `application/json` | 对象：`error`；Authentication required |
| 33 | `https://nhentai.net/api/gallery/658856` | 403 | `text/plain` | 文本：43 UTF-8 字节 |
| 34 | `https://nhentai.to/api/gallery/658856` | 404 | `application/json` | 对象：`message` |
| 35 | `https://nhentai.to/api/v2/galleries/658856` | 404 | `application/json` | 对象：`message` |
| 36 | `https://nhentai.to/api/definitely-not-a-route-xyz` | 404 | `application/json` | 对象：`message` |
| 37 | `https://nhentai.to/api/v2/openapi.json` | 404 | `application/json` | 对象：`message` |
| 38 | `https://nhentai.to/g/658856/` | 200 | `text/html; charset=UTF-8` | 文本：151693 UTF-8 字节 |
| 39 | `https://nhentai.to/trending-searches` | 200 | `application/json` | 数组：10 项 |
| 40 | `https://nhentai.net/api/v2/taxonomy/9d1099af-1f2e-4a22-ab73-3f935f4a6b54` | 200 | `application/json` | 对象：`id, action, status, score, voter_count, proposer, proposer_note, created_at, target_tag, new_description, comment_count, recent_comments` |
| 41 | `https://nhentai.net/api/v2/taxonomy/9d1099af-1f2e-4a22-ab73-3f935f4a6b54/comments?page=1&per_page=2` | 200 | `application/json` | 对象：`result, has_more, num_pages, total`；result 2 项 |
| 42 | `https://nhentai.net/api/v2/taxonomy/9d1099af-1f2e-4a22-ab73-3f935f4a6b54/edits` | 200 | `application/json` | 对象：`result`；result 0 项 |
| 43 | `https://nhentai.net/api/v2/users/981330/jegutimantion` | 200 | `application/json` | 对象：`id, username, slug, avatar_url, is_superuser, is_staff, date_joined, about, favorite_tags, recent_favorites, recent_comments` |
| 44 | `https://nhentai.net/api/v2/galleries/999999999` | 404 | `application/json` | 对象：`error`；Gallery not found |
| 45 | `https://nhentai.net/api/v2/galleries?page=0&per_page=2` | 400 | `application/json` | 对象：`error, details`；Validation error |
| 46 | `https://nhentai.net/api/v2/galleries?per_page=100` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 100 项 |
| 47 | `https://nhentai.net/api/v2/galleries?per_page=101` | 400 | `application/json` | 对象：`error, details`；Validation error |
| 48 | `https://nhentai.net/api/v2/galleries?page=100000&per_page=25` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 24 项 |
| 49 | `https://nhentai.net/api/v2/search?query=language%3Aenglish&page=1&per_page=2` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 25 项 |
| 50 | `https://nhentai.net/api/v2/search?query=zzanybooruunlikelymatchzz&page=2` | 200 | `application/json` | 对象：`result, num_pages, per_page, total`；result 0 项 |
| 51 | `https://nhentai.net/api/v2/search?query=language%3Aenglish&sort=bogus` | 400 | `application/json` | 对象：`error, details`；Validation error |
| 52 | `https://nhentai.net/api/v2/search` | 400 | `application/json` | 对象：`error, details`；Validation error |
| 53 | `https://nhentai.net/api/v2/tags/language?sort=name&per_page=1` | 200 | `application/json` | 对象：`result, num_pages, per_page, total, alphabet`；result 14 项 |
| 54 | `https://nhentai.net/api/v2/tags/bogus` | 400 | `application/json` | 对象：`error`；Invalid tag type. Must be one of: artist, category, character, group, language, parody, tag |
| 55 | `https://nhentai.net/api/v2/galleries/tagged?tag_id=999999999` | 404 | `application/json` | 对象：`error`；Tag not found |
| 56 | `https://nhentai.net/api/v2/galleries/658856?include=favorite` | 200 | `application/json` | 对象：`id, media_id, title, cover, thumbnail, scanlator, upload_date, tags, num_pages, num_favorites, pages` |
| 57 | `https://nhentai.net/api/v2/taxonomy/resolved?limit=2` | 200 | `application/json` | 对象：`result, has_more, num_pages, total`；result 50 项 |
| 58 | `https://nhentai.net/api/v2/tags/tag/big-breasts` | 200 | `application/json` | 对象：`id, type, name, slug, url, count, description, is_community, pending_describe_id` |
| 59 | `https://nhentai.to/api/gallery/1` | 404 | `text/html; charset=UTF-8` | 文本：63404 UTF-8 字节 |
| 60 | `https://nhentai.to/api/galleries/search?query=test` | 404 | `application/json` | 对象：`message` |
| 61 | `https://nhentai.to/api/v1/gallery/658856` | 404 | `application/json` | 对象：`message` |

关键结论：规范确为98 paths /114 operations /129 schemas；认证格式是 `Authorization: Key <api_key>`。
六个纳入的账号读取路径匿名401，其它25个纳入的GET路径取得200。
热门数组本次5项但规范不保证固定5；单标签是对象、评论数是整数。
`sort=name` 标签列表实际带 alphabet；`taxonomy/resolved?per_page=2` 实回50项。
`.to` 七个API样本404不能推出所有方法/路径都不存在，且它的 trending-searches实际返回JSON。
同一画廊编号跨站的media_id不同；clone标签本地id与nh_id要区分，负nh_id的含义未确认。

### 边界与未实测

- Python实际调用了9个原生方法：gallery_list、gallery_show、search、gallery_popular、tag_show、
  gallery_comment_count、gallery_comments、tag_ids、site_config。其它22个GET方法只有直接HTTP观察；
  另外5个非GET方法只对齐规范。
- **所有4个POST和1个DELETE均零请求**，包括查询型tag_search；Key/User Token成功、写权限、
  下载地址的真实目标/时效、账号管理/挑战/审核/广告均未验证，也未申请凭据。
- 媒体CDN和字节零请求，未验证Range、Referer、双后缀地址、旧媒体主机；返回路径原样保留。
- 没有触发429去验证配额，极端搜索页503、完整参数边界与枚举组合、其它部署、clone阅读页等未验证。
- 评论与编辑历史的选定样本为空；非空公告、其它错误/权限分支不能写成已测。
- 本轮合计 **79 GET：55×200、6×400、7×401、1×403、10×404**；没有模糊状态的请求。
  未运行formatter、lint、项目测试套件、构建、发布或额外离线检查。
