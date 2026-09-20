# Anime-Pictures：我要做什么，用哪个方法？

`anime-pictures.net` 是自研 JSON API 的动漫图站，不是 Danbooru / Moebooru 模板站点。本库包装 API 主机 `https://api.anime-pictures.net`：13 个原生方法 = 12 个读取 + 1 个需要登录的写方法。

读取分三类：

- JSON 读取 11 条：主机根 1 个；帖子 4 个（`posts_list` / `post_show` / `post_comments` / `post_tags`，其中 `post_tags` 需要权限）；标签 2 个；用户 2 个；评论 2 个。
- 字节读取 1 条：`image_get()` 走同一条 HTTP 通路，只回原始字节。需登录，本轮没有成功样本。
- 写 1 个：`post_create()` 只把你给的 dict 原样作为 JSON 发出。本轮没有发出任何写请求。

除 `service_info()` 不收参数外，10 条 JSON 读取路由都接 `**params`，原样拼进查询串；`post_create()` 接的是正文 `data`。两者都不接 `headers`；需要额外请求头时用 `client.request(…)` 或 `client.image_get(…, headers=…)`。每个方法的完整参数范围、缺省行为与返回字段见[方法参考](anime-pictures-api.md)；本页只做“目的 → 方法”的对照。

表里的数字与编号来自 2026-09-19 的一批匿名只读请求，不是每个 Python 方法逐个运行过的记录；逐条 URL 与状态见[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。站点数据实时变动，编号、条数、计数只作形态示例。输入资料里本轮没复测的候选说法不写进本页，集中列在[边界清单](anime-pictures-contract-notes.md#未实测集中清单)。

通用约定：

- `client` 由 `AnimePictures('anime_pictures')` 创建，包内配置默认匿名；构造、凭据与路径规则见[客户端用法](anime-pictures.md)。
- 路径都接在 `https://api.anime-pictures.net/api/v3` 后面，两个例外：`service_info()` 请求主机根 `/`，`image_get()` 请求主机根下的 `/pictures/get_image/{file_url}`。
- 信封指响应最外层的包装对象。列表信封不统一：帖子是 `posts_per_page` / `response_posts_count` / `page_number` / `posts_count` / `max_pages`；标签、用户、评论是 `offset` / `limit` / `count`。单资源分别是 `{success, tag}` / `{success, user, errormsg}` / `{success, comment, user}`。帖子详情以 `post` 为核心，本轮样本 929452 另有 `source` / `user` / `moderator` / `tags` / `file_url` / `star_it` / `favorites_users` / `tied`；另一张图真跑时没有 `source`，别当固定键集。
- 一层都不拆：`request()` 与 11 条 JSON 读取路由原样返回 JSON（列表就是列表对象、详情就是详情对象），不做字段改名、不合并分页、不重试、不钳位、不本地校验；`image_get()` 不解析字节。
- 媒体只给地址：`small_preview` / `medium_preview` / `big_preview` 只在详情里，列表里没有；CDN 地址公式来自输入资料、本轮未实测（见[客户端用法](anime-pictures.md#媒体地址只有详情给三档-url公式未实测)）。

## 按目的找调用

| 我要做什么 | 调用 | 给什么 → 返回什么（本轮实测） |
| :--- | :--- | :--- |
| 看服务标识 | `client.service_info()` | 无参数 → `GET https://api.anime-pictures.net/`（主机根）`200 {"message": "Hello, World!"}` |
| 浏览最新帖子 | `client.posts_list(page=0, posts_per_page=2)` | 0 起步页码 + 每页条数 → `200`，信封 `posts_per_page` 2、`response_posts_count` 2、`page_number` 0、`posts_count` 667906、`max_pages` 333952，`posts` 是帖子对象数组（id 929492、929491） |
| 翻下一页 | `client.posts_list(page=1, posts_per_page=2)` | 手动把 `page` 加一 → 本轮是 id 929490、929489；`page` 从 0 开始，必填（不传 / 非整数 `400`，`-1` `500`） |
| 按标签搜帖子 | `client.posts_list(page=0, search_tag='hatsune miku')` | 标签名（带空格，由 requests 编码）→ 同一个信封，本轮 `posts_count` 21008，并且这一次响应顶层多出一个 `exclusive_tag` 键（命中的那个标签对象；其它 `search_tag` 取值没有这个键，出现条件未实测）；两个词用空格分隔的组合查询本轮有结果（`'long hair blue eyes'` → 146065，是否每帖都带这两个标签本轮未逐帖核实），没有这个标签时 `posts_count` 0（`max_pages` 也是 0） |
| 排除某标签 | `client.posts_list(page=0, denied_tags='long hair')` | 单个标签名 → 本轮 `posts_count` 269346；把两个标签写进同一个值（`'long hair blue eyes'`）没有排除效果（667906），重复同名参数时本轮是后者生效（510020） |
| 换排序 | `client.posts_list(page=0, posts_per_page=3, order_by='rating')` | 排序字段名 → 本轮 `date` 首条 929492、`date_r` 首条 2、`rating` 首条 301063（`score_number` 629，同一帖 `score` 是 1446.0）、`views` 首条 88793、`size` 首条 34056、`tag_num` 首条 581823、`id` 首条 1；`order_by=random` 与 `date` 结果相同；本轮 `order=asc` 与 `order=desc` 的结果都与不传 `order` 相同（只证这一组取值，别推广到所有 `order` 取值） |
| 只看某段时间 | `client.posts_list(page=0, posts_per_page=1, order_by='date_r', ldate=1)` | 预置区间枚举（不是天数）→ 本轮 `ldate=1` / `3` / `6` 的 `posts_count` 分别是 411 / 57 / 61654，`0` 与 `8` 都是 667906；每个取值命中的最旧 `pubtime` 与推断的区间名见[方法参考](anime-pictures-api.md) |
| 按画幅 / 主色 / 格式 / 上传者过滤 | `client.posts_list(page=0, aspect='16:9')`、`color='FF0000'`、`ext_png='png'`、`ext_jpg='jpg'`、`user=204183`、`stars_by=13734` | 各自的过滤键 → 本轮 `posts_count` 分别是 37502、1645、196121、470199、30757、41519；`ext_*` 本轮只发过 `ext_jpg` / `ext_png` / `ext_gif`，取值为 `jpg` / `png` / `gif` / `yes` 时都生效（`ext_jpg=yes&ext_png=yes` 是 OR，666320）→ 值本身似乎不参与比较，但“任意非空值都启用”未穷举；`aspect` 不要求严格等比（本轮 `16:9` 命中的首条是 7017×3947，容差未测） |
| 取一张帖子详情 | `client.post_show(929452)` | 帖子编号 → 详情对象：本轮这张图的顶层键是 `post`（比列表对象多 `small_preview` / `medium_preview` / `big_preview` 三档 opreviews 地址）、`source`（`kind` / `url` / `verification`）、`user`、`moderator`、`tags`（每项 `{tag, user, relation}`）、`file_url`（含空格的文件名）、`star_it`（匿名 `false`）、`favorites_users`、`tied`（本轮 `[]`）；这不是固定键集，本轮真跑另一张图时响应没有 `source`，取键前先判断 |
| 取不存在的帖子 | `client.post_show(999999999)` | `410 {"errormsg": "Post not found", "success": false}`——是 410 不是 404 |
| 把编号写错成非数字 | `client.post_show('top')` | `400`，`Content-Type: text/plain; charset=utf-8`，正文 ``Invalid URL: Cannot parse `top` to a `i32` ``；异常的 `data` 是 `None`、原文在 `body` 里 |
| 读某帖的评论 | `client.post_comments(382872)` | 帖子编号 → `200 {"success": true, "comments": [ … ]}`，每项 `{comment, user}`，`comment` 的键是 `id` / `datetime` / `language` / `text` / `html`；本轮 1 条，没有分页信封（不返回 `offset` / `limit` / `count`） |
| 读某帖的标签（需权限） | `client.post_tags(929452)` | 帖子编号 → 本轮匿名 `403 {"errormsg": "You not have rights", "success": false}`；成功形态未实测。标签一般已经在详情的 `tags` 里 |
| 发帖 | `client.post_create(data)`（可选 `idempotency_key=…`） | `data` 由你自己准备，原样作为 JSON 正文（可选 `Idempotency-Key` 头）→ 需要登录；本轮没有发出写请求，成功与被拒的响应都没有本轮样本（输入资料称匿名 `401`，本轮未复测）；正文字段名未实测，本库不替你猜——怎么组织 `data` 见[方法参考](anime-pictures-api.md) |
| 精确取一个标签 | `client.tags_list(tag='hatsune miku')` | 标签全名 → `200 {"success": true, "offset": 0, "limit": 20, "count": 1, "tags": [ … ]}`，标签对象键为 `id` / `tag` / `tag_ru` / `tag_jp` / `num` / `num_pub` / `type` / `description_en` / `description_ru` / `description_jp` / `alias` / `parent` / `views`（本轮命中 id 407） |
| 用前缀找标签 | `client.tags_list(tag='hatsune')` | 同一个接口的精确匹配 → `count` 0（没有叫 `hatsune` 的标签）；`tag` 不是搜索 |
| 列标签 / 翻页 | `client.tags_list(limit=2, offset=0)` | 每页条数 + 跳过条数 → 同一个信封；本轮不带参数时 `limit` 20、`count` 156541，`limit=1000` 回 `limit` 100 |
| 传一个该接口不认识的参数 | `client.tags_list(search='hatsune')` | 本轮 `200`，与不带任何参数的结果相同（`count` 156541）→ 在这个取值下 `search` 没有效果；别把它当搜索，也别由此推断所有未知参数都被忽略 |
| 取一个标签详情 | `client.tag_show(407)` | 标签编号 → `200 {"success": true, "tag": { … }}`，`tag` 就是标签对象 |
| 取不存在的标签 | `client.tag_show(999999999)` | `404 {"errormsg": "Tag not found", "success": false}` |
| 列用户 | `client.users_list(limit=2, offset=0)` | 每页条数 + 跳过条数 → `200 {"success": true, "offset": 0, "limit": 2, "count": 225284, "users": [ … ]}`，用户对象键为 `id` / `name` / `login` / `avatar_version` / `isavatar` / `site_score` / `groups` / `gender` / `register_date`（没有头像地址）；不带参数时 `limit` 20，`limit=101` 回 100 |
| 看一个用户 | `client.user_show(294066)` | 用户编号 → `200 {"success": true, "user": { … }, "errormsg": null}`；本轮该 `user` 没有 `login` 键，别假设字段处处齐全 |
| 取不存在的用户 | `client.user_show(999999999)` | `404 {"errormsg": "User not found", "success": false}` |
| 看全站最新评论 | `client.comments_list(limit=2, offset=0)` | 每页条数 + 跳过条数 → `200 {"success": true, "offset": 0, "limit": 2, "count": 14988, "comments": [ … ]}`，每项 `{comment, user, post}`（`post` 同样不含预览字段）；不带参数时 `limit` 20，`limit=101` 回 100 |
| 看单条评论 | `client.comment_show(174693)` | 评论编号 → `200 {"success": true, "comment": { … }, "user": { … }}`（与输入资料“只有 comment”的说法不同，以实测为准） |
| 取不存在的评论 | `client.comment_show(999999999)` | `404 {"errormsg": "Have no comment", "success": false}` |
| 拿原图字节（需登录） | `client.image_get(detail['file_url'])` | 详情响应的 `file_url`（含空格的文件名，客户端整段编码）→ `GET https://api.anime-pictures.net/pictures/get_image/{编码后的 file_url}`；成功返回原始 `bytes`（不解析、不嗅探、不落盘），本轮匿名 `403` 空正文、无 `Content-Type`，成功形态未实测 |
| 用别的路径或自定义头 | `client.request('GET', 'posts', params={'page': 0})` | 动词 + 路径 + `params` / `data` / `headers` → 与原生方法同一条通路，JSON 原样返回；前导 `/` 表示主机根（见[通用入口](anime-pictures.md#通用入口-request)） |

## 完整方法索引（12 读取 + 1 写 = 13）

除 `service_info()` 与 `image_get()` 走主机根外，以下路径都接在 `https://api.anime-pictures.net/api/v3` 后面。

### 站点与图片入口（2）

- `service_info()` → `GET /`（主机根），服务标识：本轮 `200 {"message": "Hello, World!"}`。
- `image_get(file_url, *, headers=None)` → `GET /pictures/get_image/{quote(file_url, safe='')}`（主机根），成功返回原始 `bytes`；需登录，本轮匿名 `403` 空正文。

### 帖子（5）

- `posts_list(**params)` → `GET posts`，帖子列表，信封是 `posts_per_page` / `response_posts_count` / `page_number` / `posts` / `posts_count` / `max_pages`。
- `post_show(post_id, **params)` → `GET posts/{post_id}`，详情对象（以 `post` 为核心，样本 929452 另有 8 个顶层键，另一张图没有 `source`），只有它给三档预览地址；不存在回 `410`。
- `post_comments(post_id, **params)` → `GET posts/{post_id}/comments`，`{success, comments:[{comment, user}]}`，没有分页信封。
- `post_tags(post_id, **params)` → `GET posts/{post_id}/tags`，需权限，本轮匿名 `403`。
- `post_create(data, *, idempotency_key=None)` → `POST posts`，`data` 原样作 JSON 正文、可选 `Idempotency-Key` 头，需登录，本轮未发出写请求。

### 标签（2）

- `tags_list(**params)` → `GET tags`，标签列表信封 `{success, offset, limit, count, tags}`；`tag=` 是精确匹配。
- `tag_show(tag_id, **params)` → `GET tags/{tag_id}`，`{success, tag}`；不存在回 `404`。

### 用户（2）

- `users_list(**params)` → `GET users`，用户列表信封 `{success, offset, limit, count, users}`。
- `user_show(user_id, **params)` → `GET users/{user_id}`，`{success, user, errormsg}`；不存在回 `404`。

### 评论（2）

- `comments_list(**params)` → `GET comments`，全站评论信封 `{success, offset, limit, count, comments}`，每项 `{comment, user, post}`。
- `comment_show(comment_id, **params)` → `GET comments/{comment_id}`，`{success, comment, user}`；不存在回 `404`。

通用入口 `request(method, path, *, params=None, data=None, headers=None)`：路径、动词与正文自己给全，不补前缀、不拆信封、不改字段名。

## 本库不封装的能力

这些路由/主机不在本库范围内；需要时用 `client.request(method, path, params=…, data=…, headers=…)` 自己发（只有 JSON 会被解析）。

| 类别 | 例子 | 为什么不封装 |
| :--- | :--- | :--- |
| 媒体 CDN 与地址公式 | `https://opreviews.anime-pictures.net/…`、`https://oimages.anime-pictures.net/…` | 本库不按公式下载媒体；公式来自输入资料、本轮未实测，详情里原文给出的三档地址够用（见[客户端用法](anime-pictures.md#媒体地址只有详情给三档-url公式未实测)） |
| 旧版路由与旧版参数 | 输入资料列的 web 主机 `/pictures/view_posts/{page}?type=json`、`/pictures/view_post/{id}?type=json`、`/login/submit`、`/pictures/vote`，以及旧版参数 `type=json` | API 主机上的 `/api/v2/comments` 与 `/pictures/view_posts/0?type=json` 本轮实测 `404` 空正文、`type=json` 实测 `400`；web 主机本轮未请求。本库不包装这些路径，也不把 `404` 变成空结果 |
| 其它动词的写接口 | `PUT` / `PATCH` / `DELETE /api/v3/posts/{id}` | 只有 CORS 预检提到这些动词；本库没有账号、不探测写路由 |
| 登录 / 注册 / 换凭据 | 输入资料提到的 web 主机登录流程 | 本库不登录、不刷新令牌；凭据由调用方通过 `authorization` / `cookie` 原样传入 |
| Web 前端 HTML | `https://anime-pictures.net` 的页面 | 输入资料称被 Cloudflare 质询挡下；本库只对 API 主机说话，不抓 HTML |
| 标签联想 / 前缀搜索 | 输入资料称 v3 里没有补全端点 | 本轮只证 `tags?search=…` 在这一个取值下没有效果；不凭别家引擎的惯例造方法 |

## 边界与未实测

- 本轮已证的读路径：主机根、帖子列表（`page=0` / `page=1`、`search_tag` / `denied_tags` 的取值样本）、帖子详情、某帖评论、某帖标签的匿名 `403`、标签列表（精确 `tag=`、无参数、`search=` 对照、`type` 0–8）、标签详情、用户列表、用户详情、评论列表、评论详情、三类列表的 `limit` / `offset`，以及四类“不存在”错误、非法路径段的 `400 text/plain`、旧版路径 `/api/v2/comments` 与 `/pictures/view_posts/0?type=json` 的 `404` 空正文、旧版参数 `type=json` 的 `400`。逐条见[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。
- 没有样本：`post_tags()` / `image_get()` 的成功响应、`post_create()` 的全部行为、`Authorization` / `Cookie` 的成功路径、登录与换凭据、`PUT` / `PATCH` / `DELETE`、任何媒体 CDN 地址与字节。
- 参数语义未穷尽：上面那些参数只有单次取值样本，完整取值枚举、未知值回落规则、缺省与边界以[方法参考](anime-pictures-api.md)与[依据与差异](anime-pictures-contract-notes.md#未实测集中清单)的标注为准；没有取过的取值不要按样本外推。
- 三个脚本（轻量冒烟与两个示例）的实跑命令、请求数与退出码见[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)；它们覆盖用法路径，不等于 13 个方法逐一验证。

继续阅读：[客户端用法](anime-pictures.md) · [方法参考](anime-pictures-api.md) · [依据与差异](anime-pictures-contract-notes.md) · [验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。
