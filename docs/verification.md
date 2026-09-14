# 验证状态

本文记录对真实线上站点的验证执行情况，区分**已实测**与**仅源码对齐**。

这里保留的是当时真实执行的历史记录，不是产品能力清单。下文使用特定主页 URL 的请求与输出不变；当时执行过的个人工作流示例现已删除，其历史命令仅供追溯，不能作为当前仓库的可运行入口。该个人补丁不再被包装为库特性，通用 Artist 查询契约仍见 [API 文档](danbooru-api.md#artists)。

## 已执行：匿名只读验证

| 项目 | 内容 |
| :--- | :--- |
| 时间 | 2026-09-14T16:14:23Z 至 16:14:44Z（本地 2026-09-15 00:14–00:14） |
| 站点 | `https://danbooru.donmai.us`（根配置 `sites.danbooru`） |
| 身份 | **匿名**，未配置 `username` / `api_key` |
| 传输 | 项目 venv `.venv/Scripts/python.exe`，代理 `http://proxy-host:port`，会话 `trust_env=False` |
| 方式 | 每次请求间隔 1 秒；请求与响应原文保存在本地 `temp/danbooru-live-evidence.json`（临时产物，不入库） |
| 脚本 | `temp/verify_danbooru.py`（临时产物，不入库；参数取自根配置 `verification` 段） |

共 15 次请求：12 次成功（`200`），3 次为**预期失败**（`404` / `410` / `422`）。

### 成功请求

| 场景 | 方法 | 请求 URL | 结果 |
| :--- | :--- | :--- | :--- |
| 帖子列表 | `post_list(limit=2)` | `/posts.json?limit=2` | 2 条 |
| 帖子搜索 | `post_list(tags='rating:g', limit=2)` | `/posts.json?tags=rating%3Ag&limit=2` | 2 条 |
| 帖子详情 | `post_show(post_id=...)` | `/posts/<id>.json` | 单对象，含 `id/rating/md5/...` |
| 游标分页 | `post_list(page='b<id>', limit=2)` | `/posts.json?page=b12192570&limit=2` | 2 条，返回更早的 ID |
| 标签搜索 | `tag_list(search={'name_matches': 'touhou'}, limit=2)` | `/tags.json?limit=2&search[name_matches]=touhou` | `touhou`，tag id `29` |
| 画师按 URL（含布尔过滤与 order） | `artist_list(search={'url_matches': 'https://www.pixiv.net/users/27517', 'is_deleted': False, 'is_banned': False, 'has_tag': True, 'order': 'name'}, limit=2)` | `/artists.json?limit=2&search[url_matches]=...&search[is_deleted]=false&search[is_banned]=false&search[has_tag]=true&search[order]=name` | 1 条，artist id `8704` |
| 画师按名字+URL | 同上再加 `search={'any_name_matches': 'fuzichoco'}` | 同上 + `search[any_name_matches]=fuzichoco` | 同一 artist |
| 相关标签 | `related_tag(search={'query': 'touhou', 'category': 0, 'order': 'frequency', 'search_sample_size': 1000, 'tag_sample_size': 100}, limit=2)` | `/related_tag.json?limit=2&search[query]=touhou&search[category]=0&...` | 返回对象含 `query` / `post_count` / `tag` / `related_tags`（2 项） / `wiki_page_tags` |
| wiki 搜索 | `wiki_page_list(search={'title': 'help:api'}, limit=2)` | `/wiki_pages.json?limit=2&search[title]=help%3Aapi` | 1 条，page id `43568` |
| wiki 按标题取页 | `wiki_page_show('help:api')` | `/wiki_pages/help%3Aapi.json` | `title` 为 `help:api` |
| 评论列表 | `comment_list(group_by='comment', limit=2)` | `/comments.json?group_by=comment&limit=2` | 2 条 |
| 合集列表 | `pool_list(limit=2)` | `/pools.json?limit=2` | 2 条 |

其中“pixiv 作者 ID → tag”这一条链路也已实测跑通：`pixiv_id 27517` → artist `8704`，
其 `name`（即作品上的画师 tag）为 `fuzichoco`。

### 重定向端点

| 场景 | 方法 | 结果 |
| :--- | :--- | :--- |
| 按名字取画师（名字已存在，服务端 302） | `artist_show_or_new(name='fuzichoco')` | 跟随重定向到 `https://danbooru.donmai.us/artists/8704`（无 `.json`），最终 `200`、`Content-Type: application/json`，拿到 artist `8704` |

这说明**重定向并不等于失去 JSON**：客户端固定发送 `Accept: application/json`，重定向目标通常仍按
JSON 响应。因此对重定向类端点只能说“跟随重定向，最终格式以目标端点为准”，不能断言必定抛
`PybooruAPIError`。写类重定向端点（`artist_delete` / `artist_ban` / `artist_unban` /
`forum_topics_mark_all_as_read`）仍未实测。

### 可运行示例

另执行了两个仓库内原生示例，均通过同一根配置使用代理、匿名访问。其中
`examples/danbooru/pixiv_id_to_tag.py` 是个人猴子补丁示例，已在 `20cea4b` 中删除，
下面的命令与输出仅作历史记录，不是当前可运行入口：

```bash
.venv/Scripts/python.exe examples/danbooru/pixiv_id_to_tag.py --config pybooru.json  # 该脚本已删除
.venv/Scripts/python.exe examples/danbooru/related_tag.py --config pybooru.json
```

第一条输出 `artist: 8704 fuzichoco`，并检索到帖子 `12090564`、`12070768`、`12064514`；第二条输出查询 `touhou`、`post_count=1096790`，相关标签依次为 `1girl`、`solo`、`hat`。数量与排名会随线上数据变化。

最初共享传输调用 `temp/verify_transport.py` 也已执行：匿名 `/posts.json?limit=2` 返回 `200`，同时仅在本地构造了 Konachan / yande.re 客户端并观察到配置中的 API 版本与鉴权模板得到保留；这不代表 Moebooru 线上接口经过验证。

### 移除个人示例后的执行记录

删除个人工作流示例及其三个根配置输入后，再次执行：

```bash
.venv/Scripts/python.exe examples/danbooru/related_tag.py --config pybooru.json
```

该保留示例通过根配置中的 `http://proxy-host:port` 代理匿名请求，正常输出 `query: touhou posts: 1096795`，以及 `1girl`、`solo`、`hat`。这次输出是独立的新记录；上文历史 URL、响应与命令未替换。

### 预期失败（验证错误处理）

| 场景 | 请求 | 状态码 | 服务端消息 | 异常 |
| :--- | :--- | :--- | :--- | :--- |
| 不存在的帖子 | `/posts/0.json` | `404` | `That record was not found.`（`ActiveRecord::RecordNotFound`） | `PybooruHTTPError` |
| 页码超限 | `/posts.json?page=1001&limit=2` | `410` | `You cannot go beyond page 1000.`（`PaginationExtension::PaginationError`） | `PybooruHTTPError` |
| 标签数超限 | `/posts.json?tags=touhou 1girl solo&limit=2` | `422` | `You cannot search for more than 2 tags at a time.`（`PostQuery::TagLimitError`） | `PybooruHTTPError` |

三次都拿到了 `{success: false, error, message, backtrace}` 形式的 JSON 错误体，
并可通过 `PybooruHTTPError.http_code` / `.url` / `.data` 读取——与 [errors.md](errors.md) 描述一致。

## 尚未验证

以下内容**只做了源码对齐，没有任何线上实测**，不要当作已验证行为：

* **全部需要登录的写接口**（发帖、上传、评论、投票、编辑、删除、审核类动作等）；
* 需要更高权限或重新认证的端点（API keys、jobs 写动作、site credentials 等）；
* 存在重定向的端点（`artist_delete` / `artist_ban` / `artist_unban` / `forum_topics_mark_all_as_read`）；
* **Moebooru 面**（`Moebooru` 的全部端点）；
* 除 `danbooru.donmai.us` 之外的其他 Danbooru 系站点；
* 需要站点开启可选能力的端点（archive 服务提供的版本历史、IQDB 以图搜图、上传与媒体资源链路）。
* 没有执行发布工作流、分发包构建、全项目 lint/格式化/测试；没有新增测试；旧发布工作流保留，但不宣称已在当前 GitHub runner 或 PyPI 上验证。

## 复现方式

验证只用根配置文件里的参数，不在脚本里硬编码站点：

```bash
.venv/Scripts/python.exe temp/verify_danbooru.py
```

参数来自 `pybooru.json` 的 `verification` 段（站点、关键词、样本规模、间隔秒数，
以及用于触发错误的 `missing_post_id`、`invalid_page`、`invalid_tags`）。

## Moebooru：2026-09-15 追加记录

本节是独立的新记录。上方“Moebooru 全部未验证”属于此前 Danbooru 阶段的历史快照，
保留原文；**当前 Moebooru 的已执行范围以本节为准**，不把源码实现当成线上通过。

### 环境、命令与一次中断

- 主站：根配置 `sites.yandere` 的 `https://yande.re`，用户名与密码均为空，匿名只读。
- 解释器：项目 `.venv/Scripts/python.exe`；代理取根配置 `http://proxy-host:port`；未发送任何写请求。
- 参数：`pybooru.json` 的 `verification.moebooru`；每次请求间隔 1 秒，没有客户端自动重试。
- 先执行以下命令；导入成功、退出码 0。验证脚本在 15 个 `200` 后被对端关闭连接，退出码 1：

```bash
.venv/Scripts/python.exe -c "import pybooru; from pybooru import Moebooru"
.venv/Scripts/python.exe temp/verify_moebooru.py --config pybooru.json
```

连接被对端关闭发生于 `comment_show(0)`：`requests.exceptions.ProxyError`，底层
`RemoteDisconnected: Remote end closed connection without response`，**没有 HTTP 状态码**。
因此不能把它记成 `404`，当时的非法日期场景也还没有执行。
首次脚本原本在结束时才保存完整响应，断连使该保存语句未到达；
`temp/moebooru-live-first-pass.json` 是根据实际终端输出保留的**摘要**，不是完整原始响应。
没有重跑此前已经成功的 15 个请求。

用户已指出：这类「请求中途被对端关闭、根本没有 HTTP 响应」的现象属**站点侧反爬/限流**
（yande.re 的限流偏重），是本环境的预期行为，不是本库缺陷。它不改变上面的事实记录——
该次仍然**没有** HTTP 状态码，所以既不能记成 `404`，也不能当成库吞异常的证据。

#### 复查：该次中断不可复现（同轮追加）


| 复查项 | 命令 / 方式 | 观察结果 |
| :--- | :--- | :--- |
| 完整序列（原代理） | `.venv/Scripts/python.exe temp/verify_moebooru.py --config pybooru.json`（代理 `http://proxy-host:port`） | 退出码 `0`，17 次调用全部完成，同样含 `comment_show(0)` → `404` |

同一脚本、同一站点、同样的 1 秒间隔；原代理这次也把之前断在第 16 次的那一步跑完了。
所以那次无 HTTP 响应的中断**既不是该端点固有行为，也不是某一个代理特有**，
且无法通过「重复同一序列」或「短时突发」触发。**不能**据此推出限流阈值，
只能如实记为一次瞬时中断；限流仍是站点侧可能原因，但没有观测到阈值证据。
两次复查的完整记录在 `temp/moebooru-proxy-alt.json` 与 `temp/moebooru-proxy-default.json`，
突发结果是 `temp/moebooru-burst-probe.json`（均为临时产物，不提交）。

随后仅继续评论查询及未完成的两个错误场景，命令退出码 0：

```bash
.venv/Scripts/python.exe temp/verify_moebooru_remaining.py --config pybooru.json
```

这三次请求逐次保存到 `temp/moebooru-live-continuation.json`，包含实际 URL、状态、响应头、
JSON/正文与异常类型。客户端时间为 `2026-09-14T17:48:23Z` 至 `17:48:27Z`
（本地 2026-09-15 01:48）。临时脚本和响应均不提交。

两段合计 **19 次请求尝试：16 次 `200`、1 次 `404`、1 次 `400`，另 1 次连接被对端关闭、未收到 HTTP 响应**。
以下调用中的具体值来自本次根配置或前一个响应，不是库内置默认值。

### 已执行：匿名读取

| 场景 | 实际调用 | 观察结果 |
| :--- | :--- | :--- |
| 帖子列表 | `post_list(limit=2)` | `200`，2 条，首条 ID `1268798` |
| 帖子搜索 | `post_list(tags='rating:s', page=1, limit=2)` | `200`，2 条，首条 ID `1268790` |
| 编号翻页 | 同搜索，`page=2` | `200`，2 条，首条 ID `1268785`，与第一页不同 |
| 标签搜索 | `tag_list(name='touhou', limit=2)` | `200`，`elis_(touhou)`、`gouki_(touhou)`；名称查询不是精确相等 |
| 相关标签 | `tag_related(tags='touhou', type='general')` | `200`，按 `touhou` 分组的 25 个名称/计数对；首项 `thighhighs / 5286` |
| 画师 | `artist_list(name='fuzichoco')` | `200`，1 条，ID `50315`、名称 `fuzichoco` |
| 评论列表（未指定帖子） | `comment_list()` | `200`，`[]`。源码将缺失 `post_id` 转为 `0`；这不是全站最新评论接口 |
| 评论搜索 | `comment_search(query='')` | 续跑 `200`，实际 `[]`；**没有取得非空评论正文，不宣称已验证非空评论结果** |
| Wiki 搜索 | `wiki_list(query='touhou', limit=2)` | `200`，2 条，首条 `alphes`，ID `833` |
| Wiki 历史 | `wiki_history(title='alphes')` | `200`，2 条，版本 `2`、`1` |
| 笔记 | `note_list()` | `200`，22 条，首条 ID `7781`；这里没有声称 `limit=2` 生效 |
| 笔记历史 | `note_history()` | `200`，25 条 |
| 合集列表 | `pool_list()` | `200`，20 条，首条 ID `99411` |
| 合集及帖子 | `pool_show(99411)` | `200`，一个合集对象，内含 2 个帖子，不是顶层帖子数组 |
| 用户搜索 | `user_list(name='admin')` | `200`，20 条，首条 `adminale / 546937`；用户 JSON 为名称与 ID |
| 论坛 | `forum_list()` | `200`，30 条，首条主题 ID `10470` |

### 已执行：错误响应

| 场景 | 实际 URL | 状态与异常 | 保留的响应 |
| :--- | :--- | :--- | :--- |
| 不存在的评论（续跑） | `https://yande.re/comment/show.json?id=0` | `404`，`PybooruHTTPError` | 550 字节 HTML，含 `Requested page does not exist`；`.data is None`，`.body` 保留原文 |
| 非法日期参数 | `https://yande.re/post/popular_by_day.json?year=2026&month=13&day=1` | `400`，`PybooruHTTPError` | 空正文；`.data is None`，`.body == ''` |

这次错误响应**不是 JSON**，与上方 Danbooru 的 JSON 错误体证据不同。
库没有吞掉代理异常、没有把空正文伪造成 JSON，也没有把 HTML `404` 判成 JSON 解码错误。

### 已执行：全部 Moebooru 示例

以下五个命令按顺序以 `&&` 连接执行，整体退出码 0；每个脚本都有真实终端输出。
输入取 `examples.moebooru`，均匿名、同一代理；`temp/moebooru-examples-evidence.json` 保存输出摘要。

```bash
.venv/Scripts/python.exe examples/moebooru/list_posts.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/list_tags.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/wiki_list.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/list_comments.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/related_tags.py --config pybooru.json
```

| 脚本 | 实际输出摘要 |
| :--- | :--- |
| `list_posts.py` | page 1：`1268790 / 1268789 / 1268785`；page 2：`1268781 / 1268779 / 1268755`，各自附文件 URL |
| `list_tags.py` | 3 个标签与计数，首项 `thighhighs 264282` |
| `wiki_list.py` | `alphes`、`alstroemeria_records`、`azur_lane` |
| `list_comments.py` | `comments: 0`；空结果如实输出，不填充示例评论 |
| `related_tags.py` | `tag: touhou`，输出前 3 个相关名称/计数对，首项 `thighhighs 5286` |

原 `comment_create.py` 会真实写入且需要账号，已替换为只读 `list_comments.py`，
不是对写操作加一个模拟成功或安全护栏。写接口用法仍在 API 文档中，标注未实测。

### 站点选择与未验证项

- 沿用本轮已有站点探测结果（`temp/moebooru-site-probe.json`，本次未重跑）：
  `konachan.com` 的 24/24 请求被 Cloudflare JS 挑战拦截，`403`、`Just a moment...`。
  正常返回 JSON（见下方「架构报告驱动的候选站点复核」）。无论哪种情况都不能推断引擎没有对应路由。
- Main 另行实测 `https://konachan.net/post.json?limit=1` 同代理匿名 `200`、Moebooru 风格 JSON；
  后续复核确认 `.net` 是**同站的过滤镜像**（会少掉部分帖子），因此不作为完整内容站点，
  也没有用它代替主站 yande.re 的契约判据（见下方复核小节）。
  Sakugabooru 已由复核补齐引擎证据与只读端点覆盖，但它**不是**本轮契约判据的主站。
- **全部写动作、账号/密码认证、上传文件及 source-only 上传、权限等级、审核与删除均未实测**；
  包括源码允许匿名进入的修改型动作，也没有执行。实现依据是上游路由/控制器/模型。
- 未运行的具名读接口仍仅源码对齐：例如相似图、其余热门查询、补全/标签摘要/别名/蕴含、
  论坛详情/搜索、指定帖子的非空评论等。笔记与 Wiki 历史这两个已列明场景例外，确已运行；
  它们不代表验证了不存在的通用 archive API。
- 旧路径版本的真实部署、下游站点差异、写操作重定向后的结果、异步任务后端没有实测。
  方法存在不等于目标站点启用了相应能力；路由存在也不意味着提供 JSON。
- 现役 Moebooru 站点普遍有反爬与限流（yande.re 偏重）：中途被关闭连接、拿不到 HTTP 响应可能发生，
  且**不得**把这种中断记成 HTTP 错误码或库的行为，也不要预先断言限流阈值。
- 未新增或执行测试、格式化、lint、发布 workflow 或分发包构建；没有修改或提交两份上游仓库。

### 架构报告驱动的候选站点复核（2026-09-15 追加）

用户提供 `temp/image-sites-architecture-report.md`（调查日期 2026-09-14），其中归属 Moebooru 的
只有 Konachan、Sakugabooru、Yande.re 三站。本节按「先证明引擎身份，再证明可用」复核这三站，
把确认可用者加入根配置 `sites`；脚本 `temp/probe_moebooru_candidates.py`（临时，不入库），
原始输出 `temp/moebooru-candidates.json`，全部匿名 GET。

#### 引擎身份：站点自述

| 站点 | `GET /` 页脚 | `GET /help/api` |
| :--- | :--- | :--- |
| `konachan.com` | `Running Moebooru 6.0.0` | `Help: API 1.13.0+update.3`，正文自述 Moebooru |
| `konachan.net` | `Running Moebooru 6.0.0` | `Help: API 1.13.0+update.3` |
| `sakugabooru.com` | `Running Moebooru 6.0.0` | `Help: API 1.13.0+update.3` |
| `yande.re` | —（根路径按 `Accept` 返 JSON） | `Help: API 1.13.0+update.3`，正文自述 Moebooru |

报告对 Konachan 的「页脚直接显示运行 Moebooru 6.0.0」在本环境复现成功。
报告对 Sakugabooru 的中高置信度判断也落实为页脚级证据：`Running Moebooru 6.0.0`。

#### 加盐模板：站点自述值

`help/api` 原文形如 `The actual string that is hashed is "<盐>--<em>your-password</em>--"`，
`{0}` 即密码位；三站都自述 API 版本 `1.13.0+update.3`：

| 站点 | `hash_string` |
| :--- | :--- |
| `yande.re` | `choujin-steiner--{0}--` |
| `konachan.com` / `konachan.net` | `So-I-Heard-You-Like-Mupkids-?--{0}--` |
| `sakugabooru.com` | `er@!$rjiajd0$!dkaopc350!Y%)--{0}--` |

前两项与原配置一致；`sakugabooru` 的模板来自其站点自述，仅用于构造 `password_hash`，
**没有发登录请求、未验证服务端是否接受**。

#### 匿名只读端点覆盖（12/12 通过）

`/post.json`、`/post/index.json`、`/tag.json`、`/artist.json`、`/comment.json`、`/wiki.json`、
`/note.json`、`/pool.json`、`/forum.json`、`/user.json`、`/tag/related.json`（`tags=touhou`）、
`/post/popular_by_day.json` 在 `konachan.com`（经 `proxy-host:port`）、`konachan.net`、
`sakugabooru.com`、`yande.re` 上均返回 `200` 与 JSON。每站返回条数随站点数据不同
（如 `note.json`：konachan `list[114]`、sakugabooru `list[82]`、yande.re `list[22]`），这是数据差异。



| 出口 | 结果 |
| :--- | :--- |
| `http://proxy-host:port` | 13/13 请求 `403`、`Server: cloudflare`、`Just a moment...` |
| `http://proxy-host:port` | 14/14 请求 `200`（含 `/`、`/help/api` 与上表全部端点） |

域名与站点本身正常；这也解释了后来 `konachan.net` 反而是先能用上的那个域名。

#### `konachan.net` 是同站的过滤镜像

同一时刻取两域名的最新 5 帖：

| 域名 | `/post.json?limit=5` 的 ID |
| :--- | :--- |
| `konachan.com` | `408456, 408455, 408454, 408453, 408452` |
| `konachan.net` | `408453, 408452, 408451, 408450, 408449` |

两域名同引擎、同 API 版本、同一加盐模板，但可见帖子不一致（`.net` 少掉最新的 3 条）。
结论：`.net` **不能**当作 `.com` 的等价备份，配置里保留 `.com`。

#### `help/api` 的 `Accept` 伪影

| 请求头 | `yande.re` | `konachan.com` | `sakugabooru.com` |
| :--- | :--- | :--- | :--- |
| `Accept: application/json` | `404` HTML 404 页（550 B） | `404` 空正文 | `404` 空正文 |
| `Accept: text/html,application/xhtml+xml` | `200`（42930 B） | `200`（44403 B） | `200`（44166 B） |

本轮早先一次把 `/help/api` 记为 `404` 就是只发了 `Accept: application/json`：
本库固定发这个头，帮助页只有 HTML 模板，于是落到兜底路由。**这不是站点缺页面，也不是路由不存在**；
该行为已补进 [moebooru-api.md](moebooru-api.md) 的 HTML-only 清单。

#### 清单变更与未采用的站

- 新增 `sakugabooru` → `https://sakugabooru.com`，`api_version` 与 `hash_string` 取站点自述值；
  样例配置与 [configuration.md](configuration.md)、[moebooru.md](moebooru.md) 已同步。
- `lolibooru`（样例中既有的历史条目）**不可达**：经 `proxy-host:port` 得到
  `ProxyError: Tunnel connection failed: 502 Bad Gateway`，经 `proxy-host:port` 得到
  未做 DNS 层面确认。**用户确认后已从样例清单移除**（`pybooru.json`、`configuration.md`、
  `moebooru.md` 同步删除），本节保留上面那次探测的事实，不改成「站点已关闭」这类未验证结论。
- 报告中归入「Danbooru 系」的 Gelbooru、TBIB 实际运行 Gelbooru 引擎，不在本库两个引擎契约内，
  未做探测；「都不属于」的站点同理。

#### Safebooru 与引擎判别式（同轮追加）

用户追问「清单里的站点是否都测过」后补测了此前只被登记、未被验证的 `safebooru`，并顺手取得
两个 Rails 引擎的判别式（同一台机器、同一代理 `http://proxy-host:port`、匿名 `GET`）：

| 探测 | `safebooru.donmai.us` | `yande.re` |
| :--- | :--- | :--- |
| `/posts.json?limit=1` | `200`，`list[1]` | `404`（`Server: freenginx`） |
| `/post.json?limit=1` | `404` | `200`，`list[1]` |
| `/tags.json?limit=1` | `200` | — |
| `/artists.json?limit=1` | `200` | — |
| `/comments.json?limit=1` | `200` | — |
| `/wiki_pages.json?limit=1` | `200` | — |
| `/pools.json?limit=1` | `200` | — |

结论：`safebooru` 是 Danbooru 引擎（复数 `posts` 存在、单数 `post` 不存在），与 `danbooru`
同属 donmai 部署，匿名只读可用。同一组探测也说明**库不自动识别引擎**：判别依据是路径形态、
页脚/`help/api` 自述或认证方式，选哪个类由调用者决定；
这一节已写进 [configuration.md](configuration.md#怎么判断一个站点该用哪个类)。
