# e621ng 能力入口：我想做什么，该用哪个接口？

**不知道有哪些接口，先看这页。** 18 个方法的参数与返回见 [方法参考](e621-api.md)，
上游依据、权限分支与排除项见 [契约审计附注](e621-contract-notes.md)，实跑覆盖见
[verification.md](verification.md)。

- **e621ng 是第四类站点**：e621.net 与 e926.net 是同一引擎的两套部署，站点名或 URL 决定连哪一套；
  它与 Danbooru 同样是 Rails 引擎、同样用 HTTP Basic，但帖子负载、评级词表与计数路由都不同，
  不能套用 Danbooru 的字段或 `rating:g`。
- **本库封的是 18 个原生只读 GET 方法**：帖子、标签、画师、评论、合集、笔记、wiki 页面，以及两个相关标签方法。
  它们全部是 `request()` 的薄封装，请求与响应按上游分支原样传递。
- **没有原生写方法**：上游的写路由（发帖、编辑、评论、收藏、投票、上传、审核等）需要登录与更高权限，
  本库不把上游全部路由都封成方法，也不替调用者发写请求；需要时用通用 `request()` 显式调用。
- **库负责 API 调用**，不是下载器或自动采集器：不自动翻页、不自动保存媒体、不自动重试、不做引擎识别。
- **能匿名读列表不等于全部可见**：评论、帖子与用户字段都受服务端可见性过滤，逐条见下文与附注。

## 按目的找入口

下表的 `client` 是已按配置创建的 `E621` 客户端；`query`、`post_id`、`tag_name` 等代表你从配置或前一次
响应取得的值，不是库的默认输入。初始化见 [客户端用法](e621.md)。

| 我想做什么 | 能力与方法 | 最简调用形态 | 是否需要成员 |
| :--- | :--- | :--- | :--- |
| 按标签、评级、排序找图 | `post_list`：过滤写在顶层 `tags` 元标签（`rating:s`、`score:>10`、`order:score`） | `client.post_list(tags=query, limit=example['post_query']['limit'])` | 匿名可查 |
| 看一张帖子的详情 | `post_show` | `client.post_show(post_id)` | 匿名可查 |
| 随机取一帖 | `post_random` | `client.post_random(**example['random_query'])` | 匿名可查 |
| 数一下查询命中多少帖 | `post_count`：返回 `count` 与 `capped` | `client.post_count(tags=query)` | 匿名可查 |
| 按 md5 反查一张帖子 | `post_list(md5=...)`：返回单个帖子 | `client.post_list(md5=md5_hex)` | 匿名可查 |
| 换用新版负载结构 | `post_list` / `post_show` / `post_random` 的 `v2` 与 `mode`：`files`、`stats`，`tags` 为数组或分类字典 | `client.post_list(**dict(client.config['verification']['e621']['post_query'], **client.config['verification']['e621']['v2_query']))` | 匿名可查 |
| 查标签、使用计数与分类 | `tag_list` / `tag_show` | `client.tag_list(search={'name_matches': tag_name})`；`client.tag_show(tag_name)` | 匿名可查 |
| 查画师与主页 URL | `artist_list` / `artist_show`：带 `urls`（详情另带 `domains`） | `client.artist_list(search={'url_matches': url})` | 匿名可查 |
| 看某个帖子的评论 | `comment_list(search={'post_id': post_id})` / `comment_show` | `client.comment_list(search={'post_id': post_id})` | 匿名可读可见评论 |
| 看评论怎么按帖子组织 | `comment_list(group_by='post')`：返回带该页帖子的裸帖子对象（不含评论正文） | `client.comment_list(group_by='post', tags=query)` | 匿名可读 |
| 按合集看系列作品 | `pool_list` / `pool_show`：`post_ids` 顺序即合集顺序 | `client.pool_show(pool_id)` | 匿名可读 |
| 读图上笔记的坐标与正文 | `note_list` / `note_show` | `client.note_list(search={'post_id': post_id})`；`client.note_show(note_id)` | 匿名可读 |
| 查站点说明与 wiki 页面 | `wiki_page_list` / `wiki_page_show`（按标题，含 `help:api` 这类带冒号的标题） | `client.wiki_page_show(example['wiki_title'])` | 匿名可读 |
| 求与某标签相关的标签 | `related_tag`（单个查询）/ `related_tag_bulk`（最多 25 个标签一次） | `client.related_tag(search=client.config['verification']['e621']['related_search'])` | **需要成员**，匿名 `403` |
| 用 18 个方法之外的上游只读路由 | 通用入口 `request()`，自己给方法与路径 | `client.request('GET', 'post_versions.json', params={'search': {'post_id': post_id}})` | 看该路由自身 |

**三个容易选错的地方**：① 帖子三个查询方法**不吃 `search` 字典**，过滤条件全写在顶层 `tags`；
② `only=` 非空时只是让上游去掉 `posts`/`post` 信封，**不做字段裁剪**，想换结构要用 `v2=True`；
③ 两个相关标签方法的参数层级不同（`search[...]` 对顶层），而且都要求成员身份，匿名一律 `403`。

## 匿名和成员，能力差在哪里？

“可匿名”只表示上游源码允许匿名进入该读接口，不保证有结果、能看到全部记录或拿到全部字段。

| 身份 / 条件 | 可以期待的能力 | 主要边界 |
| :--- | :--- | :--- |
| 匿名 | 16 个原生方法：帖子列表/详情/随机/计数、标签、画师、评论、合集、笔记、wiki | `related_tag` 与 `related_tag_bulk` 为 `member_only`，`403`；评论列表另受隐藏与评分阈值过滤；不可见帖子的媒体 URL 为空 |
| 已登录成员（有效 API key） | 额外可用两个相关标签方法与评论/笔记搜索里的 `post_tags_match` | 其余写动作仍要对应权限；这些成功路径未实测 |
| staff / admin | 评论的 `is_hidden` 搜索（staff）、`ip_addr` 搜索（admin）等 | 这些属于身份相关过滤，客户端不预判 |
| 站点部署配置 | e926 一类站点的安全过滤、`safe_mode` | 不在上游仓库默认值内，本库不替站点补 `rating` 过滤 |

返回字段只需记住这几条：

- **帖子**：`file` / `preview` / `sample` / `score` / `tags` 是嵌套对象，没有 `tag_string`、`file_url`、
  `media_asset` 这些 Danbooru 字段；不可见时 `file.url`、`preview.url`、`sample.url` 等是 `null`，
  模型的默认序列化还会隐藏 `md5` / `file_ext`，见[附注](e621-contract-notes.md#sec-post-shapes)。
- **评论**：匿名看不到隐藏评论与评论被关闭帖子的评论，未给 `search={'id': ...}` 时还有评分阈值；
  `group_by='post'` 换的是分页与对象类型（裸帖子），不是评论内容。
- **wiki / 画师 / 合集 / 笔记**：字段是各自表的列加少量附加字段（`creator_name`、`post_count`、
  `category_id`、`urls`、`domains`），逐字段见 [方法参考](e621-api.md)。

以上是上游权限过滤器与查询对象的概括，逐条规则与出处见
[附注的权限与可见性](e621-contract-notes.md#sec-permissions)。

## 完整原生方法索引

以下是 `api_e621.py` 的 **18 个原生只读方法**，每项只解释“干什么”。签名、参数与返回形态见
[方法参考](e621-api.md)，路由与上游行号见[附注的逐方法清单](e621-contract-notes.md#sec-methods)。

### 帖子

- `post_list` — 搜索或列出帖子；给 `md5` 时返回该 md5 对应的单个帖子。
- `post_show` — 读一个帖子的详情。
- `post_random` — 在查询范围内随机取一帖，无匹配时 `404`。
- `post_count` — 统计匹配帖子数，返回 `count` 与封顶标记 `capped`。

### 标签

- `tag_list` — 搜索标签，可按名称、分类、是否有关联 wiki/画师与排序过滤。
- `tag_show` — 按数字 id 或标签名读一个标签。

### 画师

- `artist_list` — 搜索画师，支持名称、组名、别名、主页 URL、关联用户等条件。
- `artist_show` — 按数字 id 或画师名读一个画师，含主页 `urls` 与 `domains`。

### 评论

- `comment_list` — 搜索可见评论；`group_by='post'` 切换成按帖子的裸帖子对象列表。
- `comment_show` — 读一条可见评论。

### 合集

- `pool_list` — 搜索合集，可按类别、名称、说明、创建者与排序过滤。
- `pool_show` — 读一个合集及其帖子 id 顺序。

### 笔记

- `note_list` — 搜索笔记，可按帖子、正文、创建者与更新者过滤。
- `note_show` — 读一个笔记的坐标、尺寸与正文。

### wiki 页面

- `wiki_page_list` — 搜索 wiki 页面，可按标题、正文、别名、父页面与创建者过滤。
- `wiki_page_show` — 按数字 id 或标题读一个页面。

### 相关标签（成员权限）

- `related_tag` — 求与一个查询相关的标签；`*` 通配查询按计数取前 50 个匹配标签（输出再按名称排序）。
- `related_tag_bulk` — 一次为最多 25 个标签求相关标签，返回以标签名为键的计数对象。

## 本库不提供的能力

- **原生写动作**：`posts#update`、评论/合集/笔记/wiki/画师/标签的创建、修改、删除与回滚，收藏、投票、
  待删标记、上传、站内信、API key 管理、批量变更请求、举报与审核等，都没有方法；客户端不做自动重试、
  不替调用者补参数，也不发写请求验证。
- **封装上游全部路由**：只读面只封了上面 18 个。其它匿名可读的 JSON 路由（帖子/笔记/画师/wiki 版本历史、
  用户、热门、论坛主题与帖子、标签别名与蕴含、画师主页记录、帖子集合、站点统计、帮助索引、日志等）
  用通用 `request()` 显式调用，不逐个包方法，见[附注的可用只读扩展](e621-contract-notes.md#sec-readonly-extensions)。
- **不存在或不给 JSON 的路径**：Danbooru 的 `/counts/posts.json` 在 e621ng 没有对应路由（计数用
  `post_count`）；`deleted_posts`、`comments/search`、`notes/search`、`wiki_pages/search`、
  `artists/show_or_new` 等端点只提供 HTML，`.json` 会得到 `406`；登记了但没有动作的动词（如
  `PUT /related_tag`）会落进错误页。
- **管理面与浏览器会话**：`/staff/**` 命名空间、后台任务、审核队列、OAuth/Doorkeeper 路由与所有
  浏览器 HTML 页面都不封。
- **自动采集**：不自动翻页、不自动下载媒体、不自动重试、不做引擎自动识别，也不把单数 `/post.json`
  当作兼容入口（该路径在 e621 部署上是反脚本拦截页，源码里是 `302` 到复数路由，不可依赖）。

## 边界与未实测

- 18 个方法里 16 个有匿名成功响应（15 个来自示例脚本、两个站点各跑一遍，外加两个站点的 `post_count`），
  命令与摘要见 [verification.md](verification.md)；`related_tag` 另有匿名 `403` 记录，`related_tag_bulk`
  没有任何线上调用。两者的成员成功路径**未实测**，只做源码对齐。
- 返回形态复核覆盖了 `post_count`、原始 `posts` 信封、`md5` 单帖、`only` 拆信封与 `v2=true` 新蓝图；
  其它参数组合、身份差异、写路径、管理面与浏览器页面均未实测。
- e926 的实际安全过滤与上游仓库默认值无关，属于站点部署配置；不要从本库推断该站的可见范围。
