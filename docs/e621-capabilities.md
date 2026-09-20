# e621ng 能力入口：我想做什么，该用哪个接口？

先看这页选接口。每个方法的参数表、返回字段与可运行片段见[方法参考](e621-api.md)；上游文件与行号依据、权限分支、排除项见[契约审计附注](e621-contract-notes.md)；真实调用记录见[验证记录](verification.md#anybooru-改名后的复跑2026-09-18)。

**先认清四件事：**

* **e621ng 和 Danbooru 不是一套字段**：`e621.net` 与 `e926.net` 共用同一套程序与路由，是两个部署。它和 Danbooru 一样有复数 `GET /posts.json`、一样用 HTTP Basic，但帖子字段、评级词表与计数路由都不同。不要把 Danbooru 的字段或 `rating:g` 套过来。
* **本库封 18 个原生方法**：帖子 4、标签 2、画师 2、评论 2、合集 2、笔记 2、wiki 页面 2、相关标签 2。全部 `GET` 只读，全部是 `request()` 的薄封装。
* **没有原生写方法**：发帖、编辑、评论、收藏、投票、上传、审核等上游写路由，要自己用 `request()` 显式调用。本库不替调用者发写请求，也不把上游每条路由都封成方法。
* **库负责 API 调用，不是下载器**：不自动翻页、不自动保存媒体、不自动重试、不做引擎识别。能匿名读列表也不等于全部可见，评论与帖子字段受服务端可见性过滤，逐条见下文与附注。

## 按目的找入口

下表的 `client` 是已构造好的 `E621('e621')` 实例；编号、名称等值取自前一次响应或你已知的数据。初始化与认证见[客户端用法](e621.md)。

| 我想做什么 | 用哪个方法 | 直接抄的调用 | 匿名能读吗 |
| :--- | :--- | :--- | :--- |
| 按标签、评级、排序找图 | `post_list`：过滤写在顶层 `tags`，支持 `rating:s`、`wolf`、`order:score`、`score:>10` | `client.post_list(tags='rating:s order:score', limit=2)` | 能 |
| 看一张帖子的详情 | `post_show`：返回 `file`、`preview`、`sample`、`score`、九类 `tags` 等 25 个键 | `client.post_show(6715096)` | 能 |
| 随机取一帖 | `post_random`：上游在查询后加 `order:random` 取一条，没命中回 `404` | `client.post_random(tags='rating:s')` | 能 |
| 数一下查询命中多少帖 | `post_count`：返回 `count` 与 `capped`，`capped=True` 时计数只是下限 | `client.post_count(tags='rating:s')` | 能 |
| 按 md5 反查一张帖子 | `post_list(md5=...)`：命中时返回**单个**帖子字典 | `client.post_list(md5='b37f8af2b4508efb57cfeb08ef2ef5a1')` | 能 |
| 换成 18 键的新版字段结构 | `post_list` / `post_show` / `post_random` 的 `v2=True`：`files`、`stats` 是对象，`tags` 是标签名数组 | `client.post_list(tags='rating:s', limit=1, v2=True)` | 能 |
| 按类别分组的标签结构 | 同上再加 `mode='extended'`：`tags` 变成九类到标签名列表的字典 | `client.post_list(tags='rating:s', limit=1, v2=True, mode='extended')` | 能（视图未实测） |
| 只要表层不要外层字典 | 帖子方法加 `only='id,rating'`：去掉外层，**字段不裁** | `client.post_list(tags='rating:s', limit=1, only='id,rating')` | 能 |
| 翻页 | 加 `page=2`；更旧的编号用 `page='b6715096'`，更新的编号用 `page='a6715096'` | `client.post_list(tags='rating:s', limit=2, page=2)` | 能 |
| 查标签与使用计数 | `tag_list`：可按名称、分类（`0` general…`8` lore）、是否有 wiki/画师、排序过滤 | `client.tag_list(search={'name_matches': 'anthro'}, limit=2)` | 能 |
| 按编号或名称读一个标签 | `tag_show`：名称是精确匹配，不做大小写归一化（名称分支只有源码依据） | `client.tag_show(7115)`、`client.tag_show('anthro')` | 能 |
| 查画师与主页 URL | `artist_list`：可按名称、别名、主页地址、关联账号过滤，每项带 `urls` | `client.artist_list(search={'url_matches': 'https://x.com/miindfang'}, limit=2)` | 能 |
| 读一个画师的资料 | `artist_show`：额外带 `domains`（作品来源域名） | `client.artist_show(126799)` | 能 |
| 看某个帖子的评论 | `comment_list(search={'post_id': ...})`：匿名只含可见评论，另套评分阈值 | `client.comment_list(search={'post_id': '6715096'}, limit=2)` | 能（可见范围受限） |
| 看评论按帖子分组 | `comment_list(group_by='post')`：返回该页**帖子对象**列表，每页 5 帖，不含评论正文 | `client.comment_list(group_by='post', tags='rating:s', limit=2)` | 能 |
| 读一条评论的正文与评分 | `comment_show`：返回 `body`、`score`、`creator_name` 等 16 个键 | `client.comment_show(10075334)` | 能（不可见评论 `403`） |
| 按合集看系列作品 | `pool_list` / `pool_show`：`post_ids` 的顺序就是合集顺序 | `client.pool_list(search={'category': 'series'}, limit=2)`；`client.pool_show(54791)` | 能 |
| 读图上笔记的坐标与正文 | `note_list` / `note_show`：返回 `x`、`y`、`width`、`height`、`body` | `client.note_list(search={'post_id': '6715096'}, limit=2)`；`client.note_show(506654)` | 能 |
| 查站点说明与 wiki 页面 | `wiki_page_list` / `wiki_page_show`：按标题查，`help:api` 这类带冒号的标题直接传 | `client.wiki_page_list(limit=2)`；`client.wiki_page_show('help:api')` | 能 |
| 求与某标签相关的标签 | `related_tag`（单个查询）/ `related_tag_bulk`（一次最多 25 个标签） | `client.related_tag(search={'query': 'wolf', 'category_id': 0})`；`client.related_tag_bulk('wolf', category_id=0)` | **不能**：匿名 `403` |
| 用 18 个方法之外的只读路由 | 通用入口 `request()`：自己给方法与路径 | `client.request('GET', 'post_versions.json', params={'limit': '2'})` | 看该路由自身 |

**三处容易选错**：

1. 帖子三个查询方法不吃 `search` 字典，过滤条件写在顶层 `tags`。
2. `only=` 只去掉外层字典，不裁字段；想换结构用 `v2=True`。
3. 两个相关标签方法的参数层级不同：`related_tag` 用 `search[...]`，`related_tag_bulk` 用顶层 `query`。两者都要求成员身份，匿名一律 `403`。

## 匿名和成员，能力差在哪里？

“可匿名”只表示上游允许匿名进入这条读路由，不保证有结果、能看到全部记录或拿到全部字段。

| 身份 / 条件 | 可以做什么 | 主要边界 |
| :--- | :--- | :--- |
| 匿名 | 16 个方法：帖子列表/详情/随机/计数、标签、画师、评论、合集、笔记、wiki 页面 | 两个相关标签方法回 `403`；评论列表只含可见评论并套评分阈值；不可见帖子的媒体地址是 `null` |
| 已登录成员（有效 API key） | 额外可用两个相关标签方法，以及评论/笔记搜索里的 `post_tags_match` | 成员成功路径未实测；其余写动作还要各自权限 |
| staff / admin | 评论搜索的 `is_hidden`（staff）、`ip_addr`（admin） | 属于身份相关过滤，客户端不预判 |

返回字段只需记住这几条：

* **帖子**：`file`、`preview`、`sample`、`score`、`tags` 都是嵌套对象。没有 `tag_string`、`file_url`、`media_asset` 这些 Danbooru 字段。不可见时 `file.url`、`preview.url`、`sample.url` 等是 `null`，模型自身的序列化还会省掉 `md5`、`file_ext` 两个键。
* **评论**：匿名看不到隐藏评论与评论被关闭帖子的评论。`group_by='post'` 换的是分页与对象类型（帖子对象），不是评论内容。
* **标签 / 画师 / 合集 / 笔记 / wiki**：字段是各自表的列，加上少量附加字段（`creator_name`、`post_count`、`category_id`、`urls`、`domains`，以及画师模型上声明的 `notes`）。逐字段见[方法参考](e621-api.md)。

逐条规则与源码出处见[附注的权限与可见性](e621-contract-notes.md#sec-permissions)。

## 完整原生方法索引

以下是 `anybooru/api_e621.py` 的 **18 个原生只读方法**。签名、参数表与可运行片段见[方法参考](e621-api.md)，路由与上游行号见[附注的逐方法清单](e621-contract-notes.md#sec-methods)。

### 帖子

* `post_list`：给 `tags`（标签与元标签）与 `limit`/`page` 取帖子列表。给 `md5` 时改取单个帖子。给 `only` 或 `v2=True` 时返回不带外层字典的列表，`v2=True` 的元素换成 18 键新结构。
* `post_show`：给帖子编号取一张帖子。`post_set_id` / `pool_id` 只影响 HTML 页面上下文，不改 JSON 字段。
* `post_random`：给 `tags` 在范围内随机取一条。上游在查询后附加 `order:random`，没命中回 `404`。
* `post_count`：给 `tags` 统计命中数，返回 `count` 与 `capped`。`capped=True` 表示 `count` 只是下限。

### 标签

* `tag_list`：给 `search` 过滤条件搜索标签。`hide_empty` 不传时服务端默认只返回使用计数大于 0 的标签。`order` 支持 `name` / `similarity` / `id_asc` / `id_desc` / `date`，否则按使用计数从多到少。
* `tag_show`：给标签编号或**精确**标签名读一个标签。名称不做大小写/空格归一化，未命中 `404`。

### 画师

* `artist_list`：给 `search` 过滤条件搜索画师。可按名称、组名、别名、主页地址、关联账号、是否有同名标签过滤。每项带 `urls`，`order` 支持 `name` / `updated_at` / `post_count`。
* `artist_show`：给编号或画师名读一个画师，名称会归一化。额外返回 `domains` 与其非表列属性 `notes`。

### 评论

* `comment_list`：给 `search` 过滤条件搜索可见评论。`poster_id`/`poster_name` 指的是**帖子上传者**。`group_by='post'` 切换成帖子对象列表，每页 5 帖，不含评论正文。
* `comment_show`：给评论编号读一条评论。目标不可见时 `403`，不存在时 `404`。

### 合集

* `pool_list`：给 `search` 过滤条件搜索合集。`category` 收 `series` / `collection`，`is_active` 收布尔。每项带 `post_ids`（顺序即合集顺序）与 `post_count`。
* `pool_show`：给合集编号读一个合集。`page`/`limit` 只影响 HTML 页面。

### 笔记

* `note_list`：给 `search` 过滤条件搜索笔记。可按帖子、正文、启用状态、创建者与该帖笔记更新者过滤。返回 `x`、`y`、`width`、`height` 与 `body`。
* `note_show`：给笔记编号读一条笔记，字段同上。

### wiki 页面

* `wiki_page_list`：给 `search` 过滤条件搜索页面。`title` 支持 `*` 通配，`other_names_match` 查别名，`parent` 查重定向页。返回 `creator_name` 与 `category_id`（无对应标签时为 `null`）。
* `wiki_page_show`：给页面编号或标题读一个页面。标题会归一化并把冒号等字符转义，未命中 `404`。

### 相关标签（需要成员身份）

* `related_tag`：在 `search` 里给 `query`（可含 `*` 通配）与 `category_id`，返回 `[{"name": ..., "category_id": ...}]`。通配时按使用计数取前 50 个再按名称排序。
* `related_tag_bulk`：给空格分隔的多个标签名，上游最多取前 25 个，可选 `category_id`，返回以标签名为键、`[{"name", "count", "category_id"}]` 为值的字典。空白查询返回 `{}`。

### 通用入口

* `request`：给方法与相对 JSON 路径，发一次任意方法的请求并返回原始 JSON。不指定 `envelope` 时不拆任何键。它是上面 18 个方法的底座，也是未封方法的只读路由与写路由的出口。

## 本库不提供的能力

* **原生写动作**：`posts#update`、评论/合集/笔记/wiki/画师/标签的创建、修改、删除与回滚，收藏、投票、待删标记、上传、站内信、API key 管理、批量变更请求、举报与审核等都没有方法。上游这些动作的身份要求由各自控制器决定（多数需要登录，注册反而是未登录专用）。本库不替调用者发写请求。
* **封装上游全部路由**：只读面只封了上面 18 个。其它匿名可读的 JSON 路由（帖子/笔记/画师/wiki 版本历史、用户、热门、论坛主题与帖子、标签别名与蕴含、画师主页记录、帖子集合、站点统计、帮助索引、日志等）用 `request()` 显式调用，清单见[附注](e621-contract-notes.md#sec-readonly-extensions)。
* **不存在或不给 JSON 的路径**：Danbooru 的 `/counts/posts.json` 在 e621ng 没有对应路由，计数用 `post_count`。`deleted_posts`、`comments/search`、`notes/search`、`wiki_pages/search` 没有 JSON 实现或视图，请求 `.json` 得到 `406`。登记了却没有动作的动词（如 `PUT /related_tag`）会落进错误页。
* **可以匿名读、但没有原生方法的 JSON 路由**：`artists/show_or_new` 提供 HTML 与 JSON 两种格式且匿名可进；未知名称返回一个**未保存**的画师对象，名称已存在则 `302` 到 `/artists/<id>`。需要时用 `request()`。
* **管理面与浏览器会话**：`/staff/**` 命名空间、后台任务、审核队列、OAuth 路由与所有 HTML 页面都不封。
* **自动采集**：不自动翻页、不自动下载媒体、不自动重试、不做引擎识别。也不把单数 `/post.json` 当入口——该地址在 e621 部署上是反脚本拦截页，源码里是 `302` 跳到复数路由，不能依赖。

## 边界与未实测

* **方法实测覆盖**：18 个方法里 16 个有匿名成功记录（15 个来自示例脚本、两个站点各跑一遍，外加两个站点的 `post_count`）。`related_tag` 只有匿名 `403` 记录，`related_tag_bulk` 一次请求都没发过。两个相关标签方法的成员成功路径**未实测**，只做源码对齐。
* **已执行**：默认列表、md5 查单帖、only 保留全部字段、v2 新结构、计数。本轮还执行了页 2、标签/画师筛选、按帖子分组的评论和合集筛选。具体 URL 与输出见[文档代码复核](verification.md#文档字面代码复核2026-09-18)。
* **未实测**：v2 的 extended/thumbnail、按名称查询标签（名称分支只有源码依据）/画师、其它身份和全部写操作。`artists/show_or_new` 仅源码对齐，未实测。
* **站点部署配置**：e926 一类站点的内容过滤与 `safe_mode` 不在上游仓库默认值内，属于站点部署配置。本库不替站点补 `rating` 过滤，也不要从本库推断该站的可见范围。

继续阅读：[方法参考](e621-api.md) · [客户端用法](e621.md) ·
[契约审计附注](e621-contract-notes.md) · [配置](configuration.md)。
