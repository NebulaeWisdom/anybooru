# Gelbooru02：我要做什么，用哪个方法？

`Gelbooru02` 只覆盖 TBIB（`https://tbib.org`）上**有真实证据**的 dapi 读接口：帖子、删除流、标签、评论。默认返回 **XML 文本**，只有 `post_list` 默认返回 JSON。完整参数、返回字段与失败样本见[方法参考](gelbooru02-api.md)；帮助页原文与本轮响应对照见[依据与差异](gelbooru02-contract-notes.md)。

## 按目的找调用

下表 `client` 由 `Gelbooru02('tbib')` 创建（构造见[客户端用法](gelbooru02.md)）。

| 我要做什么 | 调用 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| 按标签读帖子（JSON） | `client.post_list(tags='rating:safe', pid=0, limit=2)` | `tags` 标签串 + `pid` 页码 + `limit` 条数 → **数组**，每项 15 个键（`id`、`directory`、`image`、`hash`、`width`、`height`、`change`、`owner`、`parent_id`、`rating`、`sample`、`score`、`tags`…），**无图片地址** |
| 翻页 | `client.post_list(tags='rating:safe', pid=1, limit=2)` | `pid` 页码 → 下一页数组；实测 `pid` 生效，客户端不自动翻页 |
| 按编号取一张帖 | `client.post_list(id=28627153)` | `id` 帖子编号 → 同一路由数组（**无 `post_show`**） |
| 按 change ID 筛 | `client.post_list(tags='rating:safe', cid=1789760741, limit=2)` | `cid`（Unix 时间形式的 change ID）→ 同一路由数组；同一时间被改的帖子可能同值 |
| 拿帖子的 XML（要图片地址） | `client.post_list(tags='rating:safe', limit=1, response_format='xml')` | 同一路由，**不加** `json=1` → 原始 XML 文本：根 `<posts count=… offset=…>`，每条 `<post …/>` 带 `file_url`、`sample_url`、`preview_url`、`md5`、`created_at`、`source`、`rating="s"` 等 |
| 自己解析 XML | `xml.etree.ElementTree.fromstring(xml_text)`（调用者侧） | XML 文本 → 元素树；库不解析、不修剪、不改名 |
| 读删除流 | `client.post_deleted(last_id=0, limit=1)` | `last_id`（帮助页：返回大于该编号的记录）→ **目前只有失败样本**：`500` + 半段 `<posts>`，抛 `AnybooruHTTPError` |
| 读标签（XML） | `client.tag_list(limit=2)` | `limit` 条数 → XML 文本：根 `<tags type="array">`，子元素 `<tag id= name= count= type= ambiguous= />`，值全是字符串；加 `json=1` 不改变格式 |
| 读某帖评论（XML） | `client.comment_list(1, limit=1)` | 帖子编号（帮助页写作 post_id，描述却说 comment id）→ XML 文本；实测 `post_id=1` 返回空 `<comments type="array"/>` |
| 用别的 dapi 分发页/参数 | `client.request('dapi', params={…})` / `client.request('dapi', params={…}, response_format='json')` | 自定 `s`、`q` 与查询参数 → 默认原文 XML 文本；`response_format='json'` 时加 `json=1` 并解析 JSON |

## 完整方法索引

原生方法 4 个，全部匿名、只读、GET；另有 1 个通用入口。

### 原生方法

* `post_list(*, response_format='json', **params)` → `GET /index.php?page=dapi&s=post&q=index`（`json=1` 仅在 JSON 模式）。
  入参 `limit`（帮助页称硬上限 100，实测 101 也返回 101）、`pid`（页码）、`tags`（站点搜索串）、
  `cid`（Unix 时间形式的 change ID）、`id`（帖子编号）。返回 JSON 数组（15 键，**无媒体地址**）；
  或 XML `<posts count offset>` + `<post …>` 文本属性。
* `post_deleted(**params)` → `GET /index.php?page=dapi&s=post&q=index&deleted=show`。
  入参 `last_id`（帮助页有）；`limit` 未被帮助页列出。返回 XML 文本，**目前只有 `500` 失败样本**。
* `tag_list(**params)` → `GET /index.php?page=dapi&s=tag&q=index`。实测参数只有 `limit`；
  帮助页没有标签分节，其它过滤/排序参数未验证。返回 `<tags type="array">` XML 文本。
* `comment_list(post_id, **params)` → `GET /index.php?page=dapi&s=comment&q=index&post_id=<值>`。
  返回 `<comments type="array"/>` XML 文本；非空评论结构未验证。

### 通用入口

* `request(page, *, params=None, response_format='xml')` → `GET /index.php?page=<page>`。
  `response_format='xml'`（默认）返回 `response.text` 原文；`'json'` 自动加 `json=1` 并解析 JSON；
  其它值直接 `KeyError`。非 2xx 一律先抛 `AnybooruHTTPError`。

## 本库不封装的路由

| 路由 / 页面 | 观察到的行为 | 为什么不封装 |
| :--- | :--- | :--- |
| `page=autocomplete&q=blue&limit=1`、`page=autocomplete2&term=blue&limit=1` | `302`，`Location: //tbib.org/`，正文为空（探测不跟随跳转） | 无 JSON/XML 数据；共享传输不关闭跳转，行为与探测时不同，且未实测 |
| `page=dapi&s=deleted&q=index` | `200`、`text/html`、**正文为空** | 帮助页无此路由，空正文不可作删除流 |
| `page=dapi&s=artist` / `s=pool` / `s=wiki` 等 | 未请求 | TBIB 上无帮助页依据、无实测；不凭别的站点文档造方法 |
| `page=dapi&s=user&q=index` | 未请求 | 属账号面；本类无凭据、不做登录 |
| `page=post&s=list&tags=…` 等网页 | `200 text/html` | 网页不是数据接口，本库不做 HTML 解析 |
| 图片地址（`file_url` / `sample_url` / `preview_url` 指向的文件） | 未请求 | 不下载媒体、不构造媒体地址；XML 已给完整 URL，用不用由调用者决定 |
| 其它 Gelbooru 0.2 部署 | 未检查 | 本家族只在 TBIB 上核实，不把 TBIB 行为说成引擎通例 |

## 边界与未实测

* **真实执行情况**：冒烟脚本 6 次请求全部 `200`（passed 6 / failed 0，退出码 0）；两个示例各 2 次 `200`，退出码 0，stderr 为空。覆盖 `post_list` 的 JSON 与 XML、`tag_list`、`comment_list`；**`post_deleted` 仍只有 `500` 失败样本**，无成功样本。
* **XML 一律原样返回**：本库不解析、不补全、不转类型、不去空格；用 `xml.etree.ElementTree` 解析是调用者的事。
* **`json=1` 只在 `post_list` 上有效**：标签与评论加不加都一样返回 XML。
* **参数只承诺帮助页写过的**：标签与删除流的其它参数无本站依据；`limit` 的 100 上限未兑现。
* **分页与计数无稳定保证**：`pid` 实测生效（`pid=1&limit=2` 的 XML 根 `offset="2"`，编号与首页不同），但站点数据在动，不保证两次请求的条数与顺序。
* **未实测/未验证项**：`page=autocomplete` / `page=autocomplete2` 的跳转行为未实测；非空评论结构未验证；`page=dapi&s=artist` / `s=pool` / `s=wiki` / `s=user` 与其它 Gelbooru 0.2 部署均未请求、未检查。
* **功能边界**：无认证、写操作、账号接口、媒体下载、重试或限流逻辑；不做 HTML 解析；不把 TBIB 行为说成引擎通例。

继续阅读：[客户端用法](gelbooru02.md) · [方法参考](gelbooru02-api.md) ·
[依据与差异](gelbooru02-contract-notes.md) · [验证记录](verification.md#gelbooru02tbib匿名只读实测2026-09-19)。
