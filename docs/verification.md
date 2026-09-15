# 验证记录

这里记录真实执行的命令、请求和结果；方法怎么调用见[方法参考](index.md#按家族选文档)，上游依据见各家族的契约审计附注。
所有数据都是当时的快照，不保证再次请求得到相同 ID、计数或排名。`temp/` 路径是当时的本地证据指针，不随仓库分发；已删除的脚本只在[历史记录](#历史记录)中列出。

## 执行环境与批次

| 批次 | 时间、站点与身份 | 命令 / 证据指针 | 执行结果 |
| :--- | :--- | :--- | :--- |
| D1：Danbooru 匿名读取 | 2026-09-14T16:14:23Z–16:14:44Z（本地 2026-09-15 00:14）；`https://danbooru.donmai.us`，`sites.danbooru`，username/api_key 均空 | `.venv/Scripts/python.exe temp/verify_danbooru.py`；`temp/danbooru-live-evidence.json` 保存请求与响应原文 | 15 次：12×200、404/410/422 各一次；间隔 1 秒 |
| D2：画师重定向 | 同站、同代理、匿名 | `temp/verify_artist_redirect.py`；结果见[Danbooru 表](#danbooru匿名只读验证) | 跟随 302，最终 200 JSON |
| M1：Moebooru 首次读取 | 2026-09-15；`https://yande.re`，`sites.yandere`，username/password 均空 | `.venv/Scripts/python.exe temp/verify_moebooru.py --config pybooru.json`；`temp/moebooru-live-first-pass.json` | 15×200 后一次断连，退出 1；证据仅为实际终端输出摘要，不是完整原始响应 |
| M2：Moebooru 续跑 | 2026-09-14T17:48:23Z–17:48:27Z（本地 2026-09-15 01:48），同站同代理 | `.venv/Scripts/python.exe temp/verify_moebooru_remaining.py --config pybooru.json`；`temp/moebooru-live-continuation.json` | 200/404/400 各一次，退出 0；逐次保存 URL、状态、头、JSON/正文和异常类型 |
| M4：候选站点复核 | 2026-09-15，全部匿名 GET | `temp/probe_moebooru_candidates.py`；`temp/moebooru-candidates.json` | 四域名各 12 个只读端点全部 200 JSON，差异见[站点复核](#站点复核) |
| S1：Serika 客户端示例 | 2026-09-15；`https://serika.art`，`sites.serika.api_key` 为空 | `.venv/Scripts/python.exe temp/run_serika_examples.py --config pybooru.json` 编排三个现有示例 | 8×200；三进程均退出 0、stderr 为空；临时 runner、片段、stdout/stderr/returncode 证据转录后已删除 |
| D3：Danbooru 血缘站点复核 | 2026-09-15，匿名 GET | `temp/probe_danbooru_family.py`；`temp/danbooru-family-probe.json` | Danbooru 9 个 REST 路径全 200；Gelbooru/TBIB 对应路径全 404 |

| 共享设置 | 实际值 |
| :--- | :--- |
| 解释器 | 项目 `.venv/Scripts/python.exe` |
| D1 参数 | 根 `verification` 段：站点、关键词、样本规模、间隔，以及 `missing_post_id` / `invalid_page` / `invalid_tags` |
| M1/M2 参数 | 根 `verification.moebooru`，间隔 1 秒，无客户端自动重试；续跑没有重跑已成功的 15 次 |
| 本地导入（Moebooru） | `.venv/Scripts/python.exe -c "import pybooru; from pybooru import Moebooru"`，退出 0 |
| 本地导入（三家族） | `.venv/Scripts/python.exe -c "import pybooru; from pybooru import Serika, Danbooru, Moebooru; print(Serika.__name__, Danbooru.__name__, Moebooru.__name__)"`，退出 0，输出 `Serika Danbooru Moebooru` |

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


| 项目 | 命令 / 方式 | 结果与证据 |
| :--- | :--- | :--- |


## 当前示例的执行记录

以下是既有真实执行记录，本次文档重排没有重新发请求。数值和排名会随线上数据变化。

| 家族 | 实际命令 | 输出摘要 / 执行结果 |
| :--- | :--- | :--- |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/list_posts.py --config pybooru.json` | page 1：`1268790 / 1268789 / 1268785`；page 2：`1268781 / 1268779 / 1268755`，各附文件 URL |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/list_tags.py --config pybooru.json` | 3 标签及计数，首项 `thighhighs 264282` |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/wiki_list.py --config pybooru.json` | `alphes`、`alstroemeria_records`、`azur_lane` |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/list_comments.py --config pybooru.json` | `comments: 0`，未填充示例评论 |
| Moebooru | `.venv/Scripts/python.exe examples/moebooru/related_tags.py --config pybooru.json` | `tag: touhou`，前 3 个名称/计数对，首项 `thighhighs 5286` |
| Serika | `.venv/Scripts/python.exe examples/serika/service_info.py --config pybooru.json` | API `SerikaART API` / `1.0.0`，统计及用户 `Giru`，详见 S1 表 |
| Serika | `.venv/Scripts/python.exe examples/serika/browse.py --config pybooru.json` | 3 张 safe 图、详情、标签、画师，详见 S1 表 |
| Serika | `.venv/Scripts/python.exe examples/serika/random_image.py --config pybooru.json` | bytes，81224 字节，`Content-Type: image/png`，详见 S1 表 |

Moebooru 五命令按上述顺序以 `&&` 连接执行，整体退出 0；输入来自 `examples.moebooru`，同代理匿名，输出摘要在 `temp/moebooru-examples-evidence.json`。Serika 三命令各退出 0、stderr 为空，合计 8 请求。

## 站点复核

来源：用户提供的 `temp/image-sites-architecture-report.md`（调查日期 2026-09-14）。报告中的引擎血缘归类与 API 兼容性分开核对；未探测报告中“都不属于”的站点。

### Moebooru 身份与只读覆盖

| 域名 | `GET /` 页脚证据 | `GET /help/api` 自述 | 只读结果 |
| :--- | :--- | :--- | :--- |
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
| `.com` 的 `/post.json?limit=5` | `408456, 408455, 408454, 408453, 408452` | 默认保留 `.com` |
| `.net` 的同一请求 | `408453, 408452, 408451, 408450, 408449` | 同站过滤镜像，少最新 3 帖，不是等价备份 |


### HTML 帮助页的 Accept 差异

| 请求头 | `yande.re` | `konachan.com` | `sakugabooru.com` |
| :--- | :--- | :--- | :--- |
| `Accept: application/json` | 404 HTML（550 B） | 404 空正文 | 404 空正文 |
| `Accept: text/html,application/xhtml+xml` | 200（42930 B） | 200（44403 B） | 200（44166 B） |

本库固定发送 JSON Accept，帮助页只提供 HTML；其 404 不能证明页面或路由不存在。上游模板与路由依据见 [Moebooru 契约审计附注](moebooru-contract-notes.md)。

### Safebooru 与 Rails 路径判别


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

### Gelbooru 与 TBIB：血缘不等于 API 兼容

D3 的原始证据为 `temp/danbooru-family-probe.json`。

| 路径 | `danbooru.donmai.us` | `gelbooru.com` | `tbib.org` |
| :--- | :--- | :--- | :--- |
| `/posts.json?limit=1` | 200，list[1] | 404，Gelbooru HTML 页 | 404，nginx 页 |
| `/tags.json?limit=1` | 200 | 404 | 404 |
| `/artists.json?limit=1` | 200 | 404 | 404 |
| `/comments.json?limit=1` | 200 | 404 | 404 |
| `/wiki_pages.json?limit=1` | 200 | 404 | 404 |
| `/pools.json?limit=1` | 200 | 404 | 404 |
| `/users.json?limit=1` | 200 | 404 | 404 |
| `/related_tag.json?query=touhou` | 200，含 related_tags 等键 | 404 | 404 |
| `/autocomplete.json?search[query]=touhou` | 200，list[0] | 404 | 404 |
| `/index.php?page=dapi&s=post&q=index&json=1&limit=1` | 404 | 401，空正文 | 200 |
| `Danbooru(site_url='https://gelbooru.com').post_list(limit=1)` | — | `PybooruHTTPError` 404，body 为 HTML 404 页 | — |
| `Danbooru(site_url='https://tbib.org').post_list(limit=1)` | — | — | `PybooruHTTPError` 404，body 为 nginx 404 页 |

Gelbooru/TBIB 页脚或关于页自述 `Running Gelbooru 0.2`，把 Danbooru 标为原始概念来源；报告的“Danbooru 系”是血缘归类，不是 REST 兼容。
TBIB 的 dapi 返回字段为 `id`、`tags`、`rating`、`parent_id`、`width`、`height`、`sample`、`sample_height`、`sample_width`、`score`、`hash`、`directory`、`image`、`owner`、`change`，与 Danbooru post 不同。Gelbooru dapi 要 key，匿名只取得 401 空正文。
两个候选站均未加入 `sites`，本库不提供 Gelbooru dapi 客户端；Danbooru 原有条目保留，其 9 个 REST 成功请求独立于 D1 的 15 次记录。

### 已移除的历史清单项

| :--- | :--- | :--- | :--- |
| `lolibooru` / `https://lolibooru.moe` | `ProxyError: Tunnel connection failed: 502 Bad Gateway` | `SSLError: UNEXPECTED_EOF_WHILE_READING` | 两边均未得到源站 HTTP 响应；未做 DNS 确认，不能断言关闭。用户确认后已从 `pybooru.json`、configuration/moebooru 样例清单移除 |

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
| 非能力范围 | 未实现 Serika cookie 登录、私有交互/资源写操作，未实现 Gelbooru dapi；未申请或实测需要 key 的候选站调用 |
| 工程流程 | 未新增测试，未运行测试、formatter、lint、项目套件、发布 workflow、分发包构建；旧 workflow 不代表已在当前 GitHub runner/PyPI 验证；上游 clone 只读且未提交 |

## 历史记录

本节保留阶段性判断与已删除入口，不把它们当作当前用法或当前覆盖范围。

| 历史阶段 / 入口 | 当时事实 | 后续落点 |
| :--- | :--- | :--- |
| 最初共享传输 `temp/verify_transport.py` | 匿名 `/posts.json?limit=2` 为 200；仅本地构造 Konachan/yande.re 客户端，观察 API 版本与鉴权模板保留 | 当时没有 Moebooru 线上验证；后续执行单列为 M1–M4 |
| Danbooru 阶段的未验证清单 | 当时 Moebooru 全部端点、除 danbooru.donmai.us 外站点均未验证 | 后来 Moebooru 与 Safebooru/候选站记录各自独立，不将新结果计入 D1 |
| 已删除个人示例 | `.venv/Scripts/python.exe examples/danbooru/pixiv_id_to_tag.py --config pybooru.json`：`artist: 8704 fuzichoco`，帖子 `12090564`、`12070768`、`12064514` | 脚本在 `20cea4b` 删除，根配置三个个人输入也删除；不能作为可运行入口或库特性 |
| 原生 Artist 查询历史 | pixiv 作者 `27517` → artist `8704` → name/tag `fuzichoco` | 保留真实 URL 与查询证据；通用 Artist 契约见 [Danbooru 方法参考](danbooru-api.md) |
| 与个人示例同批的相关标签 | `.venv/Scripts/python.exe examples/danbooru/related_tag.py --config pybooru.json`：query `touhou`，post_count `1096790`，`1girl` / `solo` / `hat`；两示例均同配置、代理、匿名 | 删除个人输入后另一次输出为 `1096795`，两个计数是独立快照 |
| Moebooru 评论示例替换 | 原 `comment_create.py` 会真实写入且需账号 | 已改用只读 `list_comments.py`，未加模拟成功或护栏；写方法仍在参考页 |
| M1 中断的最初判断 | 用户指出站点侧反爬/限流（yande.re 较重）可造成无 HTTP 响应，是环境预期现象，不是本库缺陷 | M3 未复现、未观测阈值；保留一次瞬时中断事实，不写成 404 或确定限流机制 |
| Konachan 早期探测 | `temp/moebooru-site-probe.json`：`.com` 24/24 为 Cloudflare 403 / `Just a moment...` | 限制随网络环境变化，不是域名永久不可用 |
| 帮助页早期 404 | 当时仅发 `Accept: application/json` | HTML Accept 返回 200，页面并未缺失；详见 Accept 差异表 |
| Serika 改造前匿名 200 | `/api/v1`、`/api/v1/stats`、`/api/v1/users?limit=1`、`/api/v1/random/400/400/image.png`；站内 `/api/images`、`/api/images/:id`、`/api/tags`、`/api/artists` | 来源 `HANDOFF.md` 的“Serika.art 评估”；不计入 S1 的 8 次新增客户端请求 |
| Serika 改造前匿名 401 | v1 images 列表/详情、tags 列表/详情、trending、search、random、users 详情，共 8 个 GET | 仅证明无 key 被拒绝，不证明成功字段；S1 没有重跑 |
| Serika 说明矛盾纠正 | ID、未知标签、限流错误码、PNG 标签过滤等旧评估泛化 | 仅按源码纠正，见 [Serika 契约审计附注](serika-contract-notes.md)，没有另发探测 |

[文档入口](index.md) · [Danbooru 审计](danbooru-contract-notes.md) · [Moebooru 审计](moebooru-contract-notes.md) · [Serika 审计](serika-contract-notes.md)
