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

另执行了两个仓库内原生示例，均通过同一根配置使用代理、匿名访问：

```bash
.venv/Scripts/python.exe examples/danbooru/pixiv_id_to_tag.py --config pybooru.json
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
