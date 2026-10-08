# pixiv：契约依据、排除项与实测修正

本页供维护者核对依据与接入范围；调用入门见 [客户端用法](pixiv.md)，每个方法的参数与返回字段见
[方法参考](pixiv-api.md)，按目的选方法见 [能力入口](pixiv-capabilities.md)，真实 URL、状态码与
`Content-Type` 见 [验证记录](verification.md)。

pixiv **没有本地服务端源码，也没有官方公开的 API 规范或 OpenAPI 文档**，因此本页不引“服务端
源文件行号”，只引社区源码文件名、真实 URL 与本轮匿名只读观察。凭据相关结论一律来自第三方
客户端源码与站点自身的拒绝响应，不是登录成功后的响应。

## 1. 依据分级

**这是新家族，不是给现有类加一个站点 URL。** pixiv 有两个不同主机、两套不同信封、两套不同
分页模型：web 面（`www.pixiv.net`）的 `/ajax`、`ranking.php` 与 `rpc` 脚本，app 面
（`app-api.pixiv.net`）的 `/v1`、`/v2`、`/webview`。它不符合 Danbooru、Moebooru、Serika、
e621ng、Zerochan、Gelbooru、Gelbooru02、Shuushuu、Sakuria、Anime-Pictures、Cosine、
nhentai、ArtStation、Wallhaven 中任何一个的契约；仅“返回 JSON”不构成同族。

依据等级与出处：

| 标记 | 出处 | 能说明什么 |
| :--- | :--- | :--- |
| **L（本轮实测）** | 本轮对 `www.pixiv.net` 与 `app-api.pixiv.net` 的匿名只读 `GET`（串行、不重试、不跟随跳转、不下载媒体、不带凭据） | 路由的匿名状态码、`Content-Type`、错误体、信封键、字段是否出现、参数是否被采纳 |
| **W** | 前端 TS 源码 `YieldRay/pixiv-web-api` 的 `src/api/*.ts`（如 `illust.ts`、`search.ts`、`user.ts`、`novels.ts`、`illustRecommend.ts`、`illustsComments.ts`、`tags.ts` 及写方法各文件） | web 路由字符串、请求体是 JSON 还是 form、参数名、query 数组的序列化方式 |
| **P** | `upbit/pixivpy` 的 `pixivpy3/aapi.py` 与 `models.py` | app 路由、参数名、`next_url` 分页、返回体键；是现役第三方客户端源码，不是服务端规范 |
| **Z** | ZipFile《Unofficial API specification extracted from Pixiv Android App v5.0.17》（gist 抓包） | 一批 app 路由和部分枚举（`application-info`、`emoji`、novel 系、browsing-history 等）；2016 年抓包，部分已过时 |
| **H** | `hanshsieh/pixiv-api-doc` 的 `api.yaml`（第三方 OpenAPI，非官方） | `v1/illust/comment/replies`、`POST v2/user/browsing-history/illust/add` 等补充路由 |
| **A** | `azuline/pixiv-api` 的 `client.py`、`models.py`、`commons.py` | 较旧的第三方客户端源码；其中 17 个方法是 pixivpy 的**严格子集**，没有 pixivpy 之外的路由，因此不构成额外扩展 |
| **G** | `mikf/gallery-dl` 的 `gallery_dl/extractor/pixiv.py`（`PixivAPI`） | 补齐两条 app 路由（`v1/illust/series`、`v3/illust/comments`）；函数名级引用，不编造服务端行号 |
| **N / D / S** | N=`FreeNowOrg/PixivNow` 的 `docs/pixiv-web-api.md`；D=`daydreamer-json/pixiv-ajax-api-docs`（作者自述已过时）；S=社区小说端点参考 `pixivsource.pages.dev/PixivWebApi` | web/novel 路由的第三方逆向文档，用于交叉核对外围路由 |

**Z、H、G 补出的路由按“已纳入覆盖”处理，不是排除项**：它们进原生方法表（`app_*`），成功响应一律
标注“仅源码、未实测”，并在第 3、8 节写出 Live 是否可达。唯一的例外是 Z/H 中本轮匿名 **404**
的两条（`/v1/novel/markers`、`/v2/illust/comments`），与 `*-nologin` 同一标准、不封装已知不可达
的包装，列入第 7 节排除；通用 `Pixiv.request()` 仍允许调用方显式复核。W 的 `request.ts` 自带
重试、CSRF 抓取与错误重试，**这些行为没有被复制**；本项目只采纳它的路由、参数名与请求体形态。
项目里存在本地 `danbooru/`、`moebooru/` 引擎源码，而 pixiv 没有对应的本地源码，因此本页的行号依据为空。

## 2. 范围总览

原生方法共 **140 个**，命名统一为 `web_*`（web 主机）与 `app_*`（app 主机）：

| 面 | 只读（GET） | 写（POST） | 小计 |
| :--- | ---: | ---: | ---: |
| web（`www.pixiv.net`） | 65 | 16 | 81 |
| app（`app-api.pixiv.net`） | 53 | 6 | 59 |
| 合计 | 118 | 22 | 140 |

app 的 59 = pixivpy 基线 40 + 存活的 Z/H 扩展 17 + gallery-dl 补齐 2。web 的 65 个 `GET` 里含收藏
标签改名进度 `web_bookmark_rename_progress`；它是只读查询、HTTP 动词是 **`GET`**，只是按“收藏写族”
归类时与 16 个 `POST` 放在一起（写族共 17 条 = 16 个 `POST` + 这 1 个 `GET`）。按 HTTP 动词点算
就是 **GET 118、POST 22**（= 140）。方法总数以 `anybooru/api_pixiv.py` 的冻结清单为准；逐方法的
参数细节在 [方法参考](pixiv-api.md)，不与本页重复。

按资源分组（每个方法的完整路由见第 3、6 节）：

| 资源 | web 方法 | app 方法 | 主要依据 |
| :--- | :--- | :--- | :--- |
| 插画/作品 | 详情、逐页图、ugoira 帧、新作、相关推荐、系列、评论、评论回复 | 详情、相关、推荐、排行、新作、ugoira、关注动态、trending 标签、评论、mypixiv、popular、评论回复、插画系列、v3 评论 | W、P、Z、H、G |
| 小说 | 详情、新作、发现、推荐、编辑精选、首页、分类、收藏状态、系列信息/内容/标题、评论、评论回复 | 详情、系列、评论、推荐、新作、关注动态、webview 正文、排行、收藏详情、mypixiv、popular | W、P、Z、N、S |
| 搜索与标签 | artworks/illustrations/manga/novels/top/tags/users/suggestion/autocomplete | illust/novel/user、autocomplete | W、P、Z、N、S |
| 用户 | 资料、作品列表、关注/粉丝、推荐、标签、收藏、收藏标签、附加资料 | 资料、作品、收藏、相关、推荐、关注/粉丝、mypixiv、列表、收藏标签、关注详情、浏览历史、账号状态 | W、P、Z、D |
| 榜单 | 插画榜（`ranking.php`）、小说榜 | 插画榜、小说榜 | N、P、Z |
| 特辑/其它 | `showcase_article`、street/top、discovery、mypixiv、watch_list、follow_latest、tag info/frequent/suggest | spotlight、application-info、emoji | P、Z、W、N、D |
| 写 | 收藏增删/标签/可见性、点赞、评论、关注/取关、拉黑、系列追更、加标签、收藏进度查询 | 收藏增删、关注/取关、AI 显示开关、浏览历史上报 | W、P、N、S、H |

## 3. 逐方法路由与依据

**Live 列是本轮对该路由的匿名直接 HTTP 观察，说明的是路由与响应，不等于对应的 Python 方法被
真跑过**；Python 方法真跑范围以 [验证记录](verification.md) 为准。`—` 表示该路由本轮没有请求。

### 3.1 web 只读（65，全 `GET`）

| 方法 | 路由（`www.pixiv.net`） | 依据 | Live |
| :--- | :--- | :--- | :--- |
| `web_illust_show` | `ajax/illust/{illust_id}` | W | 200；`illust/59580629` 404、`illust/0` 400 |
| `web_illust_pages` | `ajax/illust/{illust_id}/pages` | W | 200 |
| `web_ugoira_metadata` | `ajax/illust/{illust_id}/ugoira_meta` | W | 200 |
| `web_illust_new` | `ajax/illust/new` | W、D | 400（`lastId=0&limit=2&type=illust&r18=False`、`r18=0` 均 400） |
| `web_illust_recommend_init` | `ajax/illust/{illust_id}/recommend/init` | W | 200（`limit=2`） |
| `web_illust_recommend_illusts` | `ajax/illust/recommend/illusts` | W | 200（`illust_ids[]`）；无括号形式 400（W 来源 bug，见 5.5） |
| `web_illust_discovery` | `ajax/illust/discovery` | N | 200（`mode=safe&max=2`、`max=18`）；400（`mode=all&limit=2`、`max=19`、`max=100`） |
| `web_illust_series` | `ajax/series/{series_id}` | W | 200（`257832`、`p=1`；body `thumbnails`/`illustSeries`/`page`/`users`/`requests`/`extraData`/`zoneConfig`） |
| `web_illust_comments` | `ajax/illusts/comments/roots` | W | 200 |
| `web_illust_comment_replies` | `ajax/illusts/comments/replies` | W | 200（`comment_id=233757844` 另一次 200 但 `error:true` 空数组） |
| `web_novel_show` | `ajax/novel/{novel_id}` | W | 200 |
| `web_user_novels` | `ajax/user/{user_id}/novels` | W | 200（`ids[]`） |
| `web_novel_discovery` | `ajax/novel/discovery` | N | 200（`mode=safe`） |
| `web_novel_new` | `ajax/novel/new` | S | 400（`lastId=0&limit=2&r18=false`） |
| `web_novel_recommend_init` | `ajax/novel/{novel_id}/recommend/init` | W | 200（`limit=2`） |
| `web_novel_recommend_novels` | `ajax/novel/recommend/novels` | N | 200（`novelIds[]`） |
| `web_novel_editors_picks` | `ajax/novel/editors_picks` | S | 200（`limit=2&lang=ja`） |
| `web_top_novel` | `ajax/top/novel` | S | 200（`mode=all&lang=ja`） |
| `web_novel_genre` | `ajax/genre/novel/{genre}` | S | 200（`romance`、`mode=safe`） |
| `web_novel_bookmark_data` | `ajax/novel/{novel_id}/bookmarkData` | S | 200 |
| `web_novel_comments` | `ajax/novels/comments/roots` | W | 200 |
| `web_novel_comment_replies` | `ajax/novels/comments/replies` | W | 200 |
| `web_novel_series` | `ajax/novel/series/{series_id}` | W | 200 |
| `web_novel_series_content` | `ajax/novel/series_content/{series_id}` | W | 200（`limit=2&last_order=0&order_by=asc`） |
| `web_novel_series_titles` | `ajax/novel/series/{series_id}/content_titles` | W | 200 |
| `web_search_artworks` | `ajax/search/artworks/{word}` | W、N | 200（`p` 1/2/10/10000、`limit=1` 均 200） |
| `web_search_illustrations` | `ajax/search/illustrations/{word}` | W、N | 200（`type=illust`、`type=ugoira`） |
| `web_search_manga` | `ajax/search/manga/{word}` | W、N | 200 |
| `web_search_novels` | `ajax/search/novels/{word}` | W、N、S | 200 |
| `web_search_top` | `ajax/search/top/{word}` | W | 200 |
| `web_search_tags` | `ajax/search/tags/{tag}` | W | 200 |
| `web_search_users` | `ajax/search/users` | S | **400**（`nick=fuzichoco&s_mode=s_usr&i=1&p=1`） |
| `web_search_suggestion` | `ajax/search/suggestion` | W | 200（`mode=all`） |
| `web_search_autocomplete` | `rpc/cps.php` | W | 200（`keyword=cat`） |
| `web_user_show` | `ajax/user/{user_id}` | W | 200（`full=1`） |
| `web_user_profile_all` | `ajax/user/{user_id}/profile/all` | W | 200 |
| `web_user_profile_top` | `ajax/user/{user_id}/profile/top` | W | 200 |
| `web_user_profile_illusts` | `ajax/user/{user_id}/profile/illusts` | W | 200 |
| `web_user_profile_novels` | `ajax/user/{user_id}/profile/novels` | W | 200（`ids[]`；body 键是 `works`，见 8 节） |
| `web_user_illusts` | `ajax/user/{user_id}/illusts` | W | 200（`ids[]`） |
| `web_user_meta` | `ajax/user/{user_id}/meta` | W | 200 |
| `web_user_works_latest` | `ajax/user/{user_id}/works/latest` | W | 200 |
| `web_user_following` | `ajax/user/{user_id}/following` | W | 400 |
| `web_user_followers` | `ajax/user/{user_id}/followers` | D | 400（`offset=0&limit=2`） |
| `web_user_recommends` | `ajax/user/{user_id}/recommends` | W | 400（`userNum=2&workNum=1&isR18=false`） |
| `web_user_tagged` | `ajax/user/{user_id}/{work_type}/tag` | W | 200（`illusts`；`novels`） |
| `web_user_tags` | `ajax/user/{user_id}/{work_type}/tags` | W | 200（`illusts`；`novels`） |
| `web_user_bookmarks` | `ajax/user/{user_id}/{work_type}/bookmarks` | W | 400（`illusts`；`novels`） |
| `web_user_bookmark_tags` | `ajax/user/{user_id}/{work_type}/bookmark/tags` | W | 400（`illusts`；`novels`） |
| `web_user_extra` | `ajax/user/extra` | W | 400（`is_smartphone=false&version=20261008`） |
| `web_follow_latest` | `ajax/follow_latest/{work_type}` | D、S | 400（`illust`；`novel`） |
| `web_mypixiv_latest` | `ajax/mypixiv_latest/illust` | D | 400（`p=1`） |
| `web_watch_list` | `ajax/watch_list/{work_type}` | D、S | 400（`manga`；`novel`） |
| `web_street` | `ajax/street/{section}` | S | 400（`recommend_tags`、`latest`、`sub`、`for_you`） |
| `web_top_illust` | `ajax/top/illust` | D | 400 |
| `web_discovery_artworks` | `ajax/discovery/artworks` | N | 400（`mode=all&limit=2`） |
| `web_discovery_novels` | `ajax/discovery/novels` | N | 200（`mode=safe`）；400（`mode=all&limit=2`） |
| `web_discovery_users` | `ajax/discovery/users` | N、W | 400（`limit=2`） |
| `web_ranking` | `ranking.php` | N、D、W | 200（`mode=daily`、`p=1`/`p=2`）；404（`p=10000`） |
| `web_novel_ranking` | `ajax/ranking/novel` | N、S | 200（`mode=daily&p=1`） |
| `web_showcase_article` | `ajax/showcase/article` | P | `article_id=0` → 404 `{error,message,body}`；页面 `/showcase` 302 `Location: /showcase/` 未跟转；无有效 `article_id`，source-only |
| `web_tag_info` | `ajax/tag/info` | W | 200（`tag=cat`） |
| `web_frequent_tags` | `ajax/tags/frequent/{work_type}` | W | 200（`ids[]`） |
| `web_suggest_tags` | `ajax/tags/suggest_by_word` | W | **400**（`word=cat`） |
| `web_bookmark_rename_progress` | `ajax/{work_type}/bookmarks/rename_tag_progress` | W | 400（`illusts`；`novels`） |

### 3.2 app 只读（53，全 `GET`）

| 方法 | 路由（`app-api.pixiv.net`） | 依据 | Live |
| :--- | :--- | :--- | :--- |
| `app_user_detail` | `v1/user/detail` | P | — |
| `app_user_illusts` | `v1/user/illusts` | P | — |
| `app_user_bookmarks_illust` | `v1/user/bookmarks/illust` | P | — |
| `app_user_bookmarks_novel` | `v1/user/bookmarks/novel` | P | — |
| `app_user_related` | `v1/user/related` | P | — |
| `app_user_recommended` | `v1/user/recommended` | P | — |
| `app_user_following` | `v1/user/following` | P | — |
| `app_user_follower` | `v1/user/follower` | P | — |
| `app_user_mypixiv` | `v1/user/mypixiv` | P | — |
| `app_user_list` | `v2/user/list` | P | — |
| `app_user_bookmark_tags_illust` | `v1/user/bookmark-tags/illust` | P | — |
| `app_user_bookmark_tags_novel` | `v1/user/bookmark-tags/novel` | Z | — |
| `app_user_follow_detail` | `v1/user/follow/detail` | Z | — |
| `app_user_browsing_history_illusts` | `v1/user/browsing-history/illusts` | Z | — |
| `app_user_browsing_history_novels` | `v1/user/browsing-history/novels` | Z | — |
| `app_user_state` | `v1/user/me/state` | Z | 400（匿名，OAuth `invalid_request`） |
| `app_illust_detail` | `v1/illust/detail` | P | 400（匿名，OAuth `invalid_request`） |
| `app_illust_follow` | `v2/illust/follow` | P | — |
| `app_illust_mypixiv` | `v2/illust/mypixiv` | Z | — |
| `app_illust_popular` | `v1/illust/popular` | Z | — |
| `app_illust_comments` | `v1/illust/comments` | P | — |
| `app_illust_comment_replies` | `v1/illust/comment/replies` | H | 400（匿名，OAuth `invalid_request`） |
| `app_illust_comments_v3` | `v3/illust/comments` | G | 400（匿名，OAuth `invalid_request`） |
| `app_illust_related` | `v2/illust/related` | P | — |
| `app_illust_recommended` | `v1/illust/recommended` | P | — |
| `app_illust_ranking` | `v1/illust/ranking` | P | — |
| `app_illust_new` | `v1/illust/new` | P | — |
| `app_illust_series` | `v1/illust/series` | G | 400（匿名，OAuth `invalid_request`；`illust_series_id=257832&offset=0`） |
| `app_ugoira_metadata` | `v1/ugoira/metadata` | P | — |
| `app_trending_tags_illust` | `v1/trending-tags/illust` | P | — |
| `app_trending_tags_manga` | `v1/trending-tags/manga` | Z | — |
| `app_trending_tags_novel` | `v1/trending-tags/novel` | Z | — |
| `app_manga_recommended` | `v1/manga/recommended` | Z | — |
| `app_search_illust` | `v1/search/illust` | P | — |
| `app_search_novel` | `v1/search/novel` | P | — |
| `app_search_user` | `v1/search/user` | P | — |
| `app_search_autocomplete` | `v1/search/autocomplete` | Z | — |
| `app_novel_detail` | `v2/novel/detail` | P | 400（匿名，OAuth `invalid_request`） |
| `app_novel_series` | `v2/novel/series` | P | — |
| `app_novel_comments` | `v1/novel/comments` | P | — |
| `app_novel_recommended` | `v1/novel/recommended` | P | — |
| `app_novel_new` | `v1/novel/new` | P | — |
| `app_novel_follow` | `v1/novel/follow` | P | — |
| `app_novel_ranking` | `v1/novel/ranking` | Z | 400（匿名，OAuth `invalid_request`） |
| `app_novel_bookmark_detail` | `v2/novel/bookmark/detail` | Z | — |
| `app_novel_mypixiv` | `v1/novel/mypixiv` | Z | — |
| `app_novel_popular` | `v1/novel/popular` | Z | — |
| `app_user_novels` | `v1/user/novels` | P | — |
| `app_webview_novel` | `webview/v2/novel` | P | —（返回 HTML，见 5.1） |
| `app_illust_bookmark_detail` | `v2/illust/bookmark/detail` | P | — |
| `app_application_info` | `v1/application-info/android` | Z | 200（匿名） |
| `app_emoji` | `v1/emoji` | Z | 200（匿名） |
| `app_spotlight_articles` | `v1/spotlight/articles` | Z | 400（匿名，OAuth `invalid_request`） |

Z/H 补出的路由（`app_user_bookmark_tags_novel`、`app_user_follow_detail`、
`app_user_browsing_history_*`、`app_user_state`、`app_illust_mypixiv`、`app_illust_popular`、
`app_illust_comment_replies`、`app_trending_tags_manga/novel`、`app_manga_recommended`、
`app_search_autocomplete`、`app_novel_ranking`、`app_novel_bookmark_detail`、`app_novel_mypixiv`、
`app_novel_popular`）与 G 补齐的两条（`app_illust_series`、`app_illust_comments_v3`）虽然只有第三方
抓包/OpenAPI/客户端源码依据，仍作为覆盖纳入。`app_illust_popular`/`app_novel_popular`/
`app_trending_tags_manga`/`app_trending_tags_novel` 的来源没有给出成功字段，客户端只提供路由、不编造
字段。Z/H 另有两条本轮匿名 404（`/v1/novel/markers`、`/v2/illust/comments`），与 `*-nologin`
同标准、不封装已知不可达的包装，见第 7 节排除；gallery-dl 选的 `v3/illust/comments` 是**另一条
现役路由、不是 v1/v2 的别名**，与 v1 的 `app_illust_comments` 并存。

## 4. 认证与权限分支

**两个主机各带一种凭据，且只按调用方选择的 `api` 值决定，绝不看 URL。** 构造函数不联网、
不登录、不换 token、不刷新 token、不自动取 Cookie；拒绝或过期的凭据会得到站点自己的响应。

| 主机 | 头 | 何时带 | 实测分支 |
| :--- | :--- | :--- | :--- |
| web `api='web'` | `Referer: <web 根>/` | 每个 web 调用默认带 | 多数 `/ajax` 只读路由无 Cookie 即可 200 |
| web | `Cookie: <登录会话>` | 配置的 `cookie` 非空时 | 账号态路由（关注列表、关注动态、dashboard）匿名被拒 |
| web | `X-CSRF-Token: <token>` | 配置的 `csrf_token` 非空时 | 写方法需要；本客户端不对任何路由自动抓取 token |
| app `api='app'` | `Authorization: Bearer <access_token>` | 配置的 `access_token` 非空时 | 无 token 时 app 业务路由 400 |
| app | `app-os` 头 / 伪造 UA / `x-client-time` / `x-client-hash` | **从不伪造** | 业务路由不需要 time/hash；只按站点默认 UA 发送 |

匿名只读的实测分支：

| 场景 | 结果 | 依据 |
| :--- | :--- | :--- |
| web 公开插画/用户/搜索/榜单 | `200`，`{error:false,...,body}` | L |
| web `ajax/illust/59580629`（不存在的 id） | `404` `{"error":true,"message":"","body":[]}` | L |
| web `ajax/illust/0`（非法 id） | `400` `{"error":true,"message":"不正なリクエストです。","body":[]}` | L |
| web 账号态路由匿名（`following`、`followers`、`recommends`、`top/illust`、`follow_latest/*`、`mypixiv_latest`、`watch_list/*`、`street/*`、`user/extra`、`discovery/*`、`user/*/bookmarks`、`bookmark/tags`） | `400`，正文同“非法请求” | L。**不是 403**：这些 400 是请求校验失败，不能当成“认证失败”或“匿名不可用”的证据 |
| app `v1/illust/detail`、`v2/novel/detail`、`v1/spotlight/articles`、`v1/user/me/state`、`v1/novel/ranking`、`v1/illust/comment/replies`、`v1/illust/series`、`v3/illust/comments` 匿名 | `400` `{"error":{"user_message":"","message":"Error occurred at the OAuth process. Please check your Access Token to fix this. Error Message: invalid_request","reason":"","user_message_details":{}}}` | L；共 8 条 app 业务路由。**不是 401** |
| app `v1/application-info/android`、`v1/emoji` 匿名 | `200` 裸 JSON | L。所以“所有 app 路由都要 token”是错的 |
| app `v1/illust/recommended-nologin`、`v1/novel/recommended-nologin` 匿名 | `404` `{"error":{"user_message":"指定されたエンドポイントは存在しません",...}}` | L（在配置 UA、无 token 下）。这两条是“端点不存在”，不是认证分支 |

带凭据的成功路径**一律未实测**：本仓库没有 pixiv 凭据，也**没有向站点或用户索要**。任何
需要 session Cookie、CSRF token 或 `access_token` 的 200 响应，本文与其它三份文档都只作源码/
文档对齐，不伪称跑过。

## 5. 数据壳与分页：样本差异

### 5.1 返回外壳

- **web `/ajax`**：多数为 `{"error": <bool>, "message": <str>, "body": ...}`。
- **web 搜索与小说榜**：观察到 `{"error": ..., "body": ...}`，**没有 `message` 键**（`ajax/search/*`、
  `ajax/ranking/novel`）。`message` 并非每个响应都有，不要写成“统一 message”。
- **web `ranking.php`**：**没有信封**，直接返回 `{contents, mode, content, page, prev, next, date,
  prev_date, next_date, rank_total, meta, date_range_text, zoneConfig}`；`rpc/cps.php` 也是裸
  `{"candidates": [...]}`。
- **web 错误体**：命中的 `400` 观察为 `{"error":true,"message":"不正なリクエストです。","body":[]}`；
  `ranking.php` 越界是裸 `{"error":"ランキング集計の範囲外です"}`；不存在的插画是 `404` 空 `message`。
  这些是样本，不推广为“所有错误的 message 恒为某值”。
- **app**：裸 JSON，**无 web 那种信封**；错误体通常是 `{"error":{...}}`。
- **app `webview/v2/novel`**：返回 **HTML 文本**，客户端用 `response_format='text'` 原样返回、不解析、
  不正则抽取。它是唯一非 JSON 的方法。
- **app `v2/illust/comments` 的 404 例外**：body 是空的 `{}`，不是上表那种 `{"error":{...}}`；
  本类原样返回，不做归一。

### 5.2 web 搜索分页（样本）

同一次 `ajax/search/artworks/cat`（`order=date_d&mode=all&s_mode=s_tag&type=all`）：

| 请求 | 结果 |
| :--- | :--- |
| `p=1` | 200，`illustManga.data` **60 个槽位**（59 个作品 + 1 个广告占位） |
| `p=1&limit=1` | 200，仍是 **60 个槽位**；首条 id 与不带 `limit` 的 `p=1` 相同 → **`limit` 被忽略** |
| `p=10` | 200，60 个槽位 |
| `p=10000` | 200，60 个槽位，**前三个 id 与 `p=10` 完全相同** → 越界页回落到末页样本，不是空页 |
| 任意页 | `illustManga.total=107077`、`lastPage=10` |

**60 是槽位数、不是作品数**：`ajax/search/artworks`（`illustrations`、`manga` 同形）每页混有 1 行广告
占位 `{"isAdContainer": true}`（本轮四个 artworks 样本各 1 行，分别在第 24、45、25、53 个槽位），
其余才是作品行；客户端原样返回整个 `data`，**不过滤、不补位、不改写**，由调用方按 `isAdContainer`
自行判别。**这个 60/1 广告的样本只属于 artworks 系，不要套到全部四条搜索路由**：本轮
`ajax/search/novels` 是 **30 个小说、无广告占位**；`ajax/search/top` 的聚合是 **illust 24 / manga 24 /
novel 8**。`total`/`lastPage` 与每页槽数也对不上（`107077/60` 远大于 10），且 artworks 越界页返回的
是末页数据。因此**不能把 `lastPage`、`total` 或“空/短页”当作通用终止条件**，也不要把 `len(data)`
当成作品条数；这只描述 `artworks` 这一个查询词的样本，不推广为所有搜索路由的页数规律。

### 5.3 web 榜单分页（样本）

`ranking.php?mode=daily&format=json`：每页 **50** 条，`rank_total=500`，`p=1`、`p=2` 均 200，
`p=2` 的 `next=3`；`p=10000` 返回 **404** 裸 `{"error":"ランキング集計の範囲外です"}`。`format=json`
是本路由取 JSON 的协议步骤，由 `web_ranking` 在查询串首位补上，调用者传自己的 `format` 会覆盖它。
`ajax/ranking/novel` 则本身已是 JSON（`{error,body}`，含 `display_a`）。

榜单条目的 `illust_series` **不是恒为布尔**：本轮前两页同时出现 `false` 与对象两种值。对象形态带
`illust_series_id`、`user_id`、`title`、`caption`、`content_count`、`create_datetime`、
`content_illust_id`、`content_order`、`page_url`。按布尔解析会出错，调用方要按判别字段分支；客户端
原样返回，不做归一。

### 5.4 discovery 的 `max` 上限（样本上界 18）

`ajax/illust/discovery`：`mode=safe&max=2` → 200；`mode=safe&max=18` → **200，`body.illusts` 18 条**；
`mode=safe&max=19` → **400**；`mode=safe&max=100` → 400；`mode=all&limit=2` → 400。这批样本说明
`max` 的上界是 **18**（18 成功、19 失败），且这条路由不吃 `limit`。客户端只原样转发、不钳位。
`ajax/discovery/novels` 另一条路由是 `mode=safe` 200、`mode=all&limit=2` 400。

### 5.5 参数编码：`illust_ids` 的来源 bug（已由 Live 定案）

- 列表值默认走共享编码器，即重复的 `name[]` 键。实测 `ids[]`（user 作品）、`novelIds[]`
  （`ajax/novel/recommend/novels`）均为 **200**。
- `ajax/illust/recommend/illusts` 有两种写法：
  - 重复 `illust_ids[]=<id>`（带方括号，与其它列表参数一致）→ **200**；
  - 重复 `illust_ids=<id>`（**不带**方括号，W 的写法）→ **400** `不正なリクエストです。`。
  **结论：W 的无括号序列化是来源 bug，正确契约与其它列表一致是 `illust_ids[]`。** 这条路由不是
  特例，不应保留任何自拼查询串或 `urlencode` 旁路；客户端必须走共享编码器，与 `novelIds[]` 一致。
- app 侧的 `app_webview_novel` 把 id 放在查询键 `id`（不是路径段）；app 列表返回绝对 `next_url`，
  调用方把它原样回传给 `Pixiv.request(api='app')` 继续翻页。

## 6. 写请求来源表与 FORM/JSON 差异

**以下 22 个 `POST` 写方法只登记契约、本项目零执行（未发任何请求）。** 请求体形态是源码的字面
事实：`data=` 走 JSON 体，`form=` 走 `application/x-www-form-urlencoded`。本表 20 行另有 1 个
`GET` 只读 `web_bookmark_rename_progress`（它已计入 3.1 的 65 个只读，本轮对它作过匿名 HTTP 探测，
此处按收藏写族并列以便对照）。

| 方法 | HTTP | 路由 | 体 | 来源 |
| :--- | :--- | :--- | :--- | :--- |
| `web_bookmark_add(work_type)` | POST | `ajax/{work_type}/bookmarks/add`（`www.pixiv.net`） | JSON | W |
| `web_bookmark_delete(work_type)` | POST | `ajax/{work_type}/bookmarks/delete` | **form** | W |
| `web_bookmark_add_tags(work_type)` | POST | `ajax/{work_type}/bookmarks/add_tags` | JSON | W |
| `web_bookmark_edit_restrict(work_type)` | POST | `ajax/{work_type}/bookmarks/edit_restrict` | JSON | W |
| `web_bookmark_remove(work_type)` | POST | `ajax/{work_type}/bookmarks/remove` | JSON | W |
| `web_bookmark_rename_progress(work_type)` | **GET** | `ajax/{work_type}/bookmarks/rename_tag_progress` | — | W |
| `web_like(work_type)` | POST | `ajax/{work_type}/like` | JSON | W |
| `web_comment_post(work_type)` | POST | `rpc/post_comment.php`（illust）/ `novel/rpc/post_comment.php`（novel） | **form** | W |
| `web_comment_delete(work_type)` | POST | `rpc_delete_comment.php`（illust）/ `novel/rpc_delete_comment.php`（novel） | **form** | W |
| `web_user_follow_add(user_id)` | POST | `bookmark_add.php` | **form** | N、S |
| `web_user_follow_delete(user_id)` | POST | `rpc_group_setting.php` | **form** | N、S |
| `web_user_block(user_id, action)` | POST | `ajax/block/save` | JSON | S |
| `web_series_watch` / `web_series_unwatch` / `web_series_notify_on` / `web_series_notify_off` | POST | `ajax/{work_type}/series/{series_id}/watch`、`/unwatch`、`/watchlist/notification/turn_on`、`/watchlist/notification/turn_off` | JSON（可为 `{}`） | W |
| `web_illust_tag_add(illust_id, tag)` | POST | `ajax/tags/illust/{illust_id}/add` | JSON | W |
| `app_illust_bookmark_add(illust_id)` | POST | `v2/illust/bookmark/add`（`app-api.pixiv.net`） | **form** | P |
| `app_illust_bookmark_delete(illust_id)` | POST | `v1/illust/bookmark/delete` | **form** | P |
| `app_illust_browsing_history_add(illust_ids)` | POST | `v2/user/browsing-history/illust/add` | **form**（`illust_ids[]`） | H |
| `app_user_follow_add(user_id)` | POST | `v1/user/follow/add` | **form** | P |
| `app_user_follow_delete(user_id)` | POST | `v1/user/follow/delete` | **form** | P |
| `app_user_edit_ai_show_settings(show_ai)` | POST | `v1/user/ai-show-settings/edit` | **form** | P |

要点：

- **FORM 与 JSON 并存，且不按“web=JSON、app=form”一刀切**：web 的收藏删除、评论、关注/取关是
  form，其余收藏与系列、拉黑、加标签是 JSON；app 的六个写全是 form。
- `web_user_follow_add`/`web_user_follow_delete` 的主体里带协议常量
  （`mode='add'`、`type='user'`、`format='json'`；以及 `mode='del'`、`type='bookuser'`、`id=<user_id>`），
  调用者的 `attributes` 覆盖它们。这是 N/S 记的协议动作名，不是源码查询默认值。
- `web_comment_post`/`web_comment_delete` 走 `rpc/*.php`；社区文档 S 另列过一个
  `/ajax/illusts/comments/post`，但 W 的 `illustsComments.ts` 实现的是 `rpc/post_comment.php`。**本
  项目按 W 实现，不再并列包一层不确定的 ajax 变体**。
- 收藏/评论/关注/系列/加标签等需要 **session Cookie 与 CSRF token**；`web_bookmark_delete` 的
  `illusts` 用 `bookmark_id`、`novels` 用 `book_id` 与 `del='1'`，两者体形态一致但键名不同（W）。
- `web_like` 的源声称无撤销；`web_bookmark_rename_progress` 是 `GET` 状态查询，不是写；本轮对
  `illusts`/`novels` 的匿名调用都是 400，说明它同样需要正确的账号态参数。

## 7. 排除项（逐条理由）

以下**不是“不存在”**，而是超出插画浏览/交互契约、或依据不足、或属于本项目明确不做的一类：

1. **外围平台服务**：OAuth/登录/注册/资料编辑/账号控制；通知、webpush、dashboard、tumeng、Sketch；
   委托（commission）创建/完成、创作者市场；用户活动门户与 stories。理由：它们是站点自用或账号
   管理面，不是作品浏览与互动接口，逐项在此登记。
2. **作品上传/编辑/删除**：没有选定的、可核验的源码契约，故不封装。理由：依据不足，不是“站点
   没有”。
3. **旧 public API**：`public-api.pixiv.net` 已被 pixiv 下线，pixivpy 于 2022-02-04 的提交中移除
   了 `PUBLIC_API` 支持。理由：已弃用，不属于现役契约。
4. **`bapi` / `ByPassSni` / `app-api.pixivlite.com` 之类主机覆盖**：只改 host，不是独立契约面，
   而且与“包内不写代理/不绕行”冲突。理由：非契约、且属绕行。
5. **app 已知不可达的路由（本轮匿名 404）**：`v1/illust/recommended-nologin`、
   `v1/novel/recommended-nologin`（端点不存在）、`v1/novel/markers`（端点不存在）、
   `v2/illust/comments`（body 空对象 `{}`）。理由：在配置 UA、无 token 下不可达，与
   `*-nologin` 同一标准、**不封装已知不可达的包装**。**只记录这些路径与配置下的 404，不断言服务端
   全局没有**；通用 `Pixiv.request()` 仍允许调用方显式复核。
6. **app `/v1/novel/text`（`novel_text` 别名）**：现役 pixivpy 明确标注它已不存在，改用
   `webview_novel` 取正文。理由：已退役；本项目只提供 `app_webview_novel`。
7. **app `/v1/novel/series`（旧版本）**：与现役客户端冲突，本项目选 `v2/novel/series`（P）；抓包里
   的 v1 仅作候选。理由：以现役源码为准，**不断言服务端已迁移**。
8. **app 入门引导**：`/v1/walkthrough/illusts`、`/v1/walkthrough/renewal-description` 属于首次启动
   引导，不是作品浏览契约。理由：非作品资源。
9. **无源可依的小说写操作**：`POST /v2/novel/bookmark/add`、`/v1/novel/bookmark/delete`、小说评论写、
   小说正文/marker 写没有任何已读源（Z 是纯 GET 抓包、H 只覆盖 illust 收藏与浏览历史、A 无小说）。
   理由：**不凭对称性发明接口**；对应的小说阅读用只读方法，收藏/评论互动的写只提供 web 面已核实
   的 `web_bookmark_*` / `web_comment_*`。
10. **OAuth 与媒体**：不做 OAuth/PKCE/密码授权/refresh token 交换，不下载任何媒体字节
    （`i.pximg.net` 的 `url`/`urls`/`image`/`profile_img`/`zip_urls` 一律原样返回），不请求 CDN，
    不做 host 绕过。理由：需要账号与交互，且媒体下载在本项目的测试边界之外。
11. **网页 HTML 抓取与前端资产**：不解析 `www.pixiv.net` 的 HTML、不取 CSS/JS/图片，唯一例外是
    `app_webview_novel` 原样返回站点自己给的 HTML 文本（不解析）。理由：契约面是 JSON API。
12. **旧式别名/未知变体**：不提供未核实的同义路由；通用 `Pixiv.request()` 仍允许调用方显式发
    任意路由。理由：不猜测、不兜底。

## 8. 与来源初稿 / 社区资料的偏差（以 Live 为准）

| 社区资料/源码的说法 | Live 与本文的修正 |
| :--- | :--- |
| 匿名访问某些 web 路由会 `401`/认证失败 | 本轮账号态 web 路由匿名是 **400 非法请求**，不是 401；不能把 web 400 等同认证 403 |
| “所有 app 路由都要 token” | `v1/application-info/android`、`v1/emoji` 匿名 **200**；不是所有 app 路由都要 |
| 匿名 app 请求返回 401 | 实测是 **400** 加 OAuth `invalid_request` 错误体 |
| 业务请求需要 `x-client-time`/`x-client-hash` | 业务路由不需要，客户端**不伪造**这两个头，也不伪造 app UA |
| web 错误 message 统一 | web 响应并非都有 `message`：搜索、小说榜无该键，`ranking.php`/`cps.php` 无信封 |
| W：`ajax/illust/recommend/illusts` 用不带括号的重复 `illust_ids` | **来源 bug**：无括号实测 **400**；带括号 `illust_ids[]` 实测 **200**。正确形式与其它列表一致 |
| `ajax/illust/discovery` 的 `max` 硬上限 18 | 与 Live 一致：`max=18` 200（18 条）、`max=19` 400、`max=100` 400 |
| `ajax/discovery/novels` 匿名可用 | 分参数：`mode=safe` 200、`mode=all&limit=2` 400；不能把某一次 400 当成整条路由不可用，也不能把 200 推广到所有 mode |
| `ajax/search/users`、`ajax/tags/suggest_by_word` 属匿名可用 | 本轮这两条按公开参数实测 **400**（非法请求）；不假设匿名可用 |
| `ajax/user/{id}/profile/novels` 的 body 键是 `novels` | 实测 body 是 `works`（与 `profile/illusts` 同形），不是 `novels` |
| `ajax/novel/series/{id}/content_titles` 条目有 `order` | 实测条目只有 `id`/`title`/`available`，**没有 `order`** |
| `ajax/novel/series_content/{id}` 的 `page` 用 `novels` | 实测 `page` 用 **`seriesContents`**，不是 `novels` |
| `ajax/illusts/comments/replies` 成功即含评论 | 实测 `comment_id=233757844` 为 **200 但 `error:true`、`body` 为空数组**；本类原样返回，不把 HTTP 200 当有数据 |
| 搜索 `data` 每页都是 60 个作品行 | 只对 `artworks`/`illustrations`/`manga` 成立且为 **60 槽位 = 59 作品 + 1 广告占位 `{"isAdContainer": true}`**；`novels` 是 **30 个小说无广告**，`top` 聚合是 **illust 24 / manga 24 / novel 8**。`len(data)` 不是作品数，客户端不过滤、由调用方判别 |
| v1/v2/v3 插画评论 | `v1/illust/comments`（P）与 `v3/illust/comments`（gallery-dl，匿名 400 OAuth）各自是独立现役路由、并存；`v2/illust/comments` 本轮 404、不封装。三条**不是别名** |
| `ajax/showcase/article` 可直接按 article_id 读 | 文章接口无有效 id 可用：`article_id=0` 本轮 **404** `{error,message,body}`；页面 `/showcase` 是另一对象、**302 `Location: /showcase/`** 且未跟转。没有成功样本，保持 source-only，不拿页面重定向当文章接口结果 |
| gallery-dl 仍含 `v1/novel/series`、`v1/novel/text`，而 pixivpy 选 `v2/novel/series` 且标注 `v1/novel/text` 不存在 | 第三方源互相冲突，**照录不裁**：本客户端选 v2 系列 + `webview_v2/novel` 取正文，但不断言服务端已迁移或旧路由全局不存在 |
| 榜单条目的 `illust_series` 是布尔 | 实测 `false` 与对象两种值并存；对象带 `illust_series_id` 等一串字段，按布尔解析会出错 |
| 插画 `tags.tags` 每条都带 `userId`/`userName` | 实测**可选**：作者自加标签有，其它标签没有（样本 `149040133` 第 3、4 个标签只有 `tag`/`locked`/`deletable`） |
| H：`GET /v2/illust/comments` 现役 | 本轮匿名 **404**，body 是空对象 `{}`；不与 P 的 v1 并列封装，列入第 7 节排除 |
| Z：`GET /v1/novel/markers` 现役 | 本轮匿名 **404**（`指定されたエンドポイントは存在しません`）；列入第 7 节排除，不断言全局不存在 |
| “空页/短页即到底” | 搜索越界页返回末页 60 条样本、`lastPage` 与 `total` 对不上，不能作终止条件；榜单越界页是 404 |

## 9. 边界与未实测（集中）

- **全部带凭据的成功路径未实测**：web 的 Cookie/CSRF 写与账号态只读、app 的全部 53 个业务只读
  方法。本仓库没有 pixiv 凭据，也没有向站点或用户索要；也不打算用匿名请求反推登录后的字段。
- **全部 22 个 `POST` 写方法零执行**：未发出任何 HTTP 请求，状态码、成功体、副作用一律未观测；
  表中形态来自 W/P/H 源码。
- **`web_bookmark_rename_progress` 是 `GET` 只读、不是写**：本轮对它做过直接 HTTP 探测（`illusts`、
  `novels` 均 400），但它的 Python 方法没有跑。**不要把 HTTP 探测与 Python 方法实跑混为一谈，也不
  要把 GET 与 POST 混为一谈**；本节其它“未实测”只针对 Python 方法调用。
- **初次脚本运行（历史证据，失败记录照存）**：smoke 的 10 次 GET 执行到 8×200 + 1×404 + 1×400，
  进程 exit 1、5 通过 5 失败；失败原因是返回行形状混杂（搜索 `data` 里的 `isAdContainer` 行、
  榜单 `illust_series` 的布尔/对象两种值、插画标签缺 `userId`/`userName`），**不是端点失效，也没有
  重试**。一次 list 示例在打印前先抛 `KeyError: id`，该次响应状态没被记录，**不据其它请求重建它的
  200**。**修好后的最终真跑是 smoke 10/10 通过、list 3 成功，browse 的 4 次原本即 200 未重跑。**
- **app 面只测到代表路由**：8 条匿名 400（`illust/detail`、`novel/detail`、`spotlight/articles`、
  `user/me/state`、`novel/ranking`、`illust/comment/replies`、`illust/series`、`v3/illust/comments`）、
  2 条匿名 200（`application-info`、`emoji`）、4 条匿名 404（`illust/recommended-nologin`、
  `novel/recommended-nologin`、`novel/markers`、`v2/illust/comments`）。其余 app 只读方法只有源码
  依据（P、Z、H、A、G），没有本轮的账号态响应。
- **被排除的 4 条 app 路由（见第 7 节第 5 条）不能用匿名 404 断言全局不存在**；它们只是不封装为
  原生方法，通用 `Pixiv.request()` 仍可显式复核。
- **web 未请求的方法**（第 3 节 Live 为 `—` 的行）：`web_showcase_article` 的路由与参数只有 P 依据，
  未得有效 `article_id`，保持 source-only。
- **未定的字段说明**：`app_illust_popular`、`app_novel_popular`、`app_trending_tags_manga`、
  `app_trending_tags_novel` 的来源没有给出成功字段；各 app 路由每页条数与 `offset` 语义、
  `web_illust_new` 的合法参数组合，均未实测。
- **字段的浮动值**：作品 id、计数、时间、图片地址都是采样值，客户端不缓存、不查询、不校验。
- **参数取值枚举**（榜单 `mode`、搜索 `order`/`s_mode`/`type`、`work_type` 各端点允许值）在
  [方法参考](pixiv-api.md) 按端点列出；本页只标依据，不重复展开。
