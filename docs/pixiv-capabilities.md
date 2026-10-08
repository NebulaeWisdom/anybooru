# Pixiv：我要做什么，用哪个方法？

Pixiv（网页端 `https://www.pixiv.net`、App 面 `https://app-api.pixiv.net`）不是 booru 引擎，两个域名不同的面放在同一个 `Pixiv` 类里，由 `request(..., api='web'|'app')` 选根。本库按公开前端来源与匿名实测（网页端）、公开客户端源码（App 面）实现 **140 个原生方法**：

- **81 个 `web_`**：网页端，65 个 `GET`（64 个只读 + 写查询 `web_bookmark_rename_progress`）+ 16 个 `POST`。
- **59 个 `app_`**：App 面，53 个只读 `GET` + 6 个 `POST`。

**为什么算新家族**：判据是契约而不是站名。网页端返回 `{"error": false, "message": "", "body": {...}}` 信封（搜索/排行榜/评论那几条没有 `message`），`ranking.php?format=json` 更是裸根对象；App 面直接返回 `{"illusts": [...], "next_url": "..."}` 这样的裸 JSON。跟现有十四个家族（Danbooru / Moebooru / Serika / e621ng / Zerochan / Gelbooru / Gelbooru02 / Shuushuu / Sakuria / Anime-Pictures / Cosine / Nhentai / ArtStation / Wallhaven）的契约都不同。

**证据范围**：网页端依据匿名只读响应加社区前端逆向来源，App 面依据公开客户端源码（第二依据，不是服务端契约）与两条匿名成功/拒绝探测；App 面**成功路径未实测**。逐条 URL、状态码与未实测项见[验证记录](verification.md)与[契约附注](pixiv-contract-notes.md)。**方法存在不等于成功路径测过。**

本页只做「目的 → 方法」对照与 140 方法一行索引。构造、认证、`request()`、返回与错误语义在[客户端用法](pixiv.md)；每个方法的完整参数、取值、真实 URL 与逐字段返回在[方法参考](pixiv-api.md)。

## 按目的找调用

`client` 由 `Pixiv('pixiv', cookie='', access_token='', csrf_token='')` 创建；下表调用里的编号、词、查询值都是可直接运行的字面值。带「**需 Cookie**」的网页端方法匿名会被站点拒（`400`/`401`）；带「**需 token**」的 App 方法需要 `access_token`（`Pixiv('pixiv', access_token='<你的 token>')`）。

| 我要做什么 | 调用 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| 浏览最新插画 / 翻页 | `client.web_search_artworks('cat', p=1, order='date_d', mode='all', s_mode='s_tag', type='all')` / `p=2` | 关键词、页码（从 1 起）→ `{"error", "body"}`，作品数组在 `body.illustManga.data`，`body.illustManga.total` / `lastPage` 是总数与最大页。**每页 `data` 60 个槽位，可能含 1 个 `{"isAdContainer": true}` 广告槽，遍历时自行区分、单独报数** |
| 关键词过滤搜索 | `client.web_search_artworks('cat', order='popular_d', mode='safe', s_mode='s_tag_full', type='illust', ai_type=0)` | 站点自己的查询键（`order`/`mode`/`s_mode`/`type`/`ai_type`/`wlt`/`wgt`…）→ 同上；逐键范围见[方法参考](pixiv-api.md) |
| 只搜插画 / 只搜漫画 / 搜小说 | `client.web_search_illustrations('cat', type='illust')` / `client.web_search_manga('cat')` / `client.web_search_novels('cat')` | 关键词 → 数组分别在 `body.illust.data` / `body.manga.data` / `body.novel.data` |
| 搜索聚合页 / 标签页 / 用户 | `client.web_search_top('cat')` / `client.web_search_tags('初音ミク')` / `client.web_search_users(nick='cat')` | 关键词或标签 → 聚合/标签/用户结果信封 |
| 搜索联想词 | `client.web_suggest_tags('初音')` / `client.web_search_autocomplete('初音')` | 词或关键词 → 标签建议 / `candidates` 裸对象 |
| 取一张插画的详情 | `client.web_illust_show('149040133')` | 插画编号 → `{"error", "message", "body"}`，`body` 有 `illustId`/`illustTitle`/`userId`/`urls`（五个地址）/`width`/`height`/`pageCount`/`tags.tags`/计数 |
| 取多页图的每一页地址 | `client.web_illust_pages('149040133')` | 插画编号 → `body` 数组，每页 `urls`（`thumb_mini`/`small`/`regular`/`original`）与宽高；一次给全、没有页码参数 |
| 取 ugoira 动图帧数据 | `client.web_ugoira_metadata('149040133')` | ugoira 编号 → `body.src`/`originalSrc`/`mime_type`/`frames`（`file` + `delay`） |
| 按 id 批量取作品/小说 | `client.web_user_profile_illusts('27517', ids=['149040133'])` / `client.web_user_illusts('27517', ids=[...])` / `client.web_user_novels('27517', ids=[...])` | 编号列表（编成 `ids[]=`）→ `body` 以作品编号为键 |
| 列某用户的作品编号索引 | `client.web_user_profile_all('27517')` | 用户编号 → `body.illusts`/`body.manga` 是「编号→null」字典、`body.novels` 是数组，要详情再逐条 `web_illust_show`；不分页 |
| 取用户资料 / 置顶 / 最新 / meta | `client.web_user_show('27517', full=1)` / `client.web_user_profile_top('27517')` / `client.web_user_works_latest('27517')` / `client.web_user_meta('27517')` | 用户编号 → 资料/置顶/最新/元数据信封 |
| 列用户的关注 / 粉丝 / 相关推荐（**需 Cookie**） | `client.web_user_following('27517', offset=0, limit=24)` / `client.web_user_followers('27517')` / `client.web_user_recommends('27517', userNum=10)` | 用户编号 → 用户列表信封；匿名实测 `400` |
| 列用户的书签 / 书签标签 / 资源标签 | `client.web_user_bookmarks('27517', 'illusts', offset=0, rest='show')` / `client.web_user_bookmark_tags('27517', 'illusts')` / `client.web_user_tags('27517', 'illusts')` / `client.web_user_tagged('27517', 'illusts', tag='cat')` | 用户编号 + `work_type`（范围见索引）→ 书签/标签信封；书签匿名实测 `400` |
| 看某条的时间线（关注 / MyPixiv，**需 Cookie**） | `client.web_follow_latest('illust', mode='all', p=1)` / `client.web_mypixiv_latest(p=1)` | `work_type` 或页码 → 时间线信封；`follow_latest` 匿名实测 `400` |
| 看首页/发现流 | `client.web_street('recommend_tags')` / `client.web_discovery_artworks(mode='all', limit=18)` / `client.web_discovery_novels(mode='all')` / `client.web_discovery_users(limit=18)` | `section`/`mode` → 区块信封。首页「趋势标签」走 `web_street('recommend_tags')`，**没有**独立 trending 路由 |
| 读插画/漫画排行榜 | `client.web_ranking(mode='daily', p=1)` | `mode`/`p`/可选 `date`/`content` → **裸根对象**：`contents`（每页 50 条）、`rank_total`、`page`、`prev`/`next`、`date`；方法自动补 `format=json` |
| 读小说排行榜 | `client.web_novel_ranking(mode='daily', p=1)` | `mode`/`p` → `{"error", "body"}`，排行在 `body.display_a.rank_a` |
| 读某插画/小说的评论与回复 | `client.web_illust_comments('149040133', offset=0, limit=2)` / `client.web_illust_comment_replies('comment_id')` / `client.web_novel_comments('novel_id', offset=0, limit=2)` / `client.web_novel_comment_replies('comment_id')` | 作品或评论编号 → `body.comments` + `body.hasNext` |
| 读插画的推荐/相关 | `client.web_illust_recommend_init('149040133', limit=2)` → `client.web_illust_recommend_illusts(nextIds)` | 首屏 `body.illusts`/`nextIds`/`details`；续页传 `nextIds` 列表（重复 `illust_ids=` 键） |
| 读小说的推荐/首页/编辑精选/题材 | `client.web_novel_recommend_init('novel_id')` / `client.web_novel_recommend_novels(novelIds=[...])` / `client.web_top_novel(mode='all')` / `client.web_novel_editors_picks(limit=10)` / `client.web_novel_genre('original')` | 小说编号或题材 → 小说列表信封 |
| 读小说详情 / 系列 / 目录 | `client.web_novel_show('12345678')` / `client.web_novel_series('12345')` / `client.web_novel_series_content('12345', limit=10)` / `client.web_novel_series_titles('12345')` | 小说或系列编号 → 详情（`body.content` 是正文）/ 系列信息 / 系列内小说 / 目录 |
| 读某插画系列 / 特辑文章 / 标签信息 | `client.web_illust_series('12345')` / `client.web_showcase_article('123')` / `client.web_tag_info('初音ミク')` | 系列/文章/标签编号 → 对应信封 |
| 取一起出现的高频标签 | `client.web_frequent_tags('illust', ids=['149040133'])` | `work_type` + 编号列表 → 共同标签数组 |
| 读最新作品流 | `client.web_illust_new(limit=10, type='illust')` / `client.web_novel_new(limit=10)` | `limit`/`type` 等 → 新作列表；`illust_new` 参数敏感（探测 `400`），字段按来源 |
| App 面：用户资料 / 作品 / 关注等（**需 token**） | `client.app_user_detail('27517')` / `client.app_user_illusts('27517', type='illust')` / `client.app_user_following('27517', restrict='public')` … | 用户编号 → 裸 JSON（`user` / `illusts` / `user_previews` + `next_url`） |
| App 面：插画详情 / 相关 / 推荐 / 排行（**需 token**） | `client.app_illust_detail('149040133')` / `client.app_illust_related('149040133')` / `client.app_illust_recommended(content_type='illust')` / `client.app_illust_ranking(mode='day')` | 插画编号或选项 → `{"illust": {...}}` / `illusts` + `next_url` |
| App 面：搜索（**需 token**） | `client.app_search_illust('cat', sort='date_desc')` / `client.app_search_novel('cat')` / `client.app_search_user('cat')` | 关键词 → `illusts`/`novels`/`user_previews` + `next_url` |
| App 面：插画系列 / v3 评论（**需 token**） | `client.app_illust_series('257832', offset=0)` / `client.app_illust_comments_v3('149040133')` | 系列编号（查询键 `illust_series_id`）或插画编号 → `{illusts, next_url, illust_series_detail}` 或 `{comments, next_url}`；来源为 gallery-dl，成功未实测 |
| App 面：小说详情 / 系列 / 正文网页（**需 token**） | `client.app_novel_detail('12345678')` / `client.app_novel_series('12345')` / `client.app_webview_novel('12345678', viewer_version='20221031_ai')` | 小说/系列编号 → 裸 JSON；`app_webview_novel` 返回 **HTML 原文**（`response_format='text'`，不解析） |
| App 面：阅读历史 / MyPixiv / 热门（**需 token**） | `client.app_user_browsing_history_illusts()` / `client.app_illust_mypixiv()` / `client.app_illust_popular()` / `client.app_novel_mypixiv()` / `client.app_novel_popular()` | 无必填（或 `offset`）→ `{illusts/novels, next_url}`；`*_popular` 来源只给路径、不给 schema |
| App 面：漫画推荐 / 小说排行（**需 token**） | `client.app_manga_recommended()` / `client.app_novel_ranking(mode='day')` | 选项 → `illusts`/`novels` + `next_url` |
| App 面：某评论的回复 / 关注详情 / 账号状态（**需 token**） | `client.app_illust_comment_replies('123456789')` / `client.app_user_follow_detail('27517')` / `client.app_user_state()` | 评论或用户编号、或无参 → 回复、关注状态、账号状态 |
| App 面：关键词自动补全（**需 token**） | `client.app_search_autocomplete('初音')` | 关键词 → `{search_auto_complete_keywords: [...]}`（元素字段来源未声明） |
| App 面：翻页 | `client.request('GET', next_url, api='app')` | 上一条 App 列表返回的绝对 `next_url` → 下一页；**必须同时传 `api='app'`** |
| App 面：匿名可读的两条 | `client.app_application_info()` / `client.app_emoji()` | 无参数 → 应用信息 / emoji 列表；本轮匿名实测 `200`（其余 App 路由匿名被拒） |
| 预期错误路径 | `client.web_illust_show('59580629')` → `404`；`client.web_illust_show('0')` → `400`；`client.web_ranking(mode='daily', p=10000)` → `404`；`client.app_illust_detail('149040133')` 匿名 → `400` | 都抛 `AnybooruHTTPError`，读 `error.http_code` / `error.data` / `error.body` |
| 换路径、换动词或加请求头 | `client.request('GET', 'v1/emoji', api='app', headers={'Accept-Language': 'ja'})` | 动词 + 路由（相对或绝对）+ `api` + `params`/`data`/`form`/`headers`/`response_format` → 同一条通路 |

翻页、越界页码与列表编码的坑见[客户端用法](pixiv.md#翻页与常见坑)。

## 完整方法索引

「路由」列省略共同主机：`web_` 方法省略 `https://www.pixiv.net/`，`app_` 方法省略 `https://app-api.pixiv.net/`。带 `**params` 的方法其余查询键原样转发，带 `**attributes` 的方法把属性作为请求体（JSON 或表单，见每条标注）。返回的完整信封与逐字段在[方法参考](pixiv-api.md)。**带 `work_type` 的方法每个模板只列一次，`work_type` 的取值就是该行给的集合。**

### 网页端（81 个 `web_` 方法）

#### 插画（10 个只读 `GET`）

* `web_illust_show(illust_id, **params)` → `GET ajax/illust/{illust_id}`；插画编号 → `body` 详情（`illustTitle`/`urls`/`pageCount`/`tags.tags`…）；`tags.tags` 每项至少有 `tag`/`locked`/`deletable`，`userId`/`userName` 只在作者自己加的标签上出现、其它标签可能没有。
* `web_illust_pages(illust_id, **params)` → `GET ajax/illust/{illust_id}/pages`；→ `body` 数组，每页 `urls`/`width`/`height`。
* `web_ugoira_metadata(illust_id, **params)` → `GET ajax/illust/{illust_id}/ugoira_meta`；→ `body.src`/`originalSrc`/`mime_type`/`frames`。
* `web_illust_new(**params)` → `GET ajax/illust/new`；`lastId`/`limit`/`type`/`r18` → 新作列表。
* `web_illust_recommend_init(illust_id, **params)` → `GET ajax/illust/{illust_id}/recommend/init`；→ `body.illusts`/`nextIds`/`details`。
* `web_illust_recommend_illusts(illust_ids, **params)` → `GET ajax/illust/recommend/illusts`；`illust_ids`（列表，编成重复 `illust_ids[]=`）→ 续页推荐。
* `web_illust_discovery(**params)` → `GET ajax/illust/discovery`；`mode`/`max` → 发现流。
* `web_illust_series(series_id, **params)` → `GET ajax/series/{series_id}`；→ 插画系列信息。
* `web_illust_comments(illust_id, **params)` → `GET ajax/illusts/comments/roots`；`offset`/`limit` → `body.comments`/`hasNext`。
* `web_illust_comment_replies(comment_id, **params)` → `GET ajax/illusts/comments/replies`；`page` → 回复。

#### 小说（15 个只读 `GET`）

* `web_novel_show(novel_id, **params)` → `GET ajax/novel/{novel_id}`；→ 小说详情（`body.content` 是正文、`seriesNavData` 是系列导航）。
* `web_user_novels(user_id, **params)` → `GET ajax/user/{user_id}/novels`；`ids`（列表）→ `body` 以小说编号为键。
* `web_novel_discovery(**params)` → `GET ajax/novel/discovery`；`mode`/`limit` → 小说发现流。
* `web_novel_new(**params)` → `GET ajax/novel/new`；`lastId`/`limit`/`r18` → 新小说。
* `web_novel_recommend_init(novel_id, **params)` → `GET ajax/novel/{novel_id}/recommend/init`；→ `novels`/`nextIds`/`details`。
* `web_novel_recommend_novels(**params)` → `GET ajax/novel/recommend/novels`；`novelIds`（列表）→ 续页小说推荐。
* `web_novel_editors_picks(**params)` → `GET ajax/novel/editors_picks`；`limit` → 编辑精选。
* `web_top_novel(**params)` → `GET ajax/top/novel`；`mode` → 小说首页区块。
* `web_novel_genre(genre, **params)` → `GET ajax/genre/novel/{genre}`；`mode` → 题材列表。
* `web_novel_bookmark_data(novel_id, **params)` → `GET ajax/novel/{novel_id}/bookmarkData`；→ `body.id`/`isBookmarkable`/`bookmarkData`。
* `web_novel_comments(novel_id, **params)` → `GET ajax/novels/comments/roots`；`offset`/`limit` → `body.comments`/`hasNext`。
* `web_novel_comment_replies(comment_id, **params)` → `GET ajax/novels/comments/replies`；`page` → 回复。
* `web_novel_series(series_id, **params)` → `GET ajax/novel/series/{series_id}`；→ 系列信息。
* `web_novel_series_content(series_id, **params)` → `GET ajax/novel/series_content/{series_id}`；`limit`/`last_order`/`order_by`/`page`/`size` → `body.thumbnails` + `body.page`（`body.page.seriesContents` 是内容数组、`isFirstPage`/`isLastPage` 也在这里；键名不是 `novels`）；`order_by` 来源写作 `asc`/`dsc`（原拼写，不改）。
* `web_novel_series_titles(series_id, **params)` → `GET ajax/novel/series/{series_id}/content_titles`；→ `body` 数组 `{id, title, available}`（**没有 `order`**）。

#### 搜索（9 个只读 `GET`）

**广告槽只出现在 `web_search_artworks` / `web_search_illustrations` / `web_search_manga` 三类**（各 60 槽、含 1 个 `{"isAdContainer": true}`）；**`web_search_novels` 本轮样本是 30 条、没有广告槽**，`web_search_top` 的聚合数组另有自己的条数。本类原样返回、不过滤，遍历时按该路由实际返回的行用 `if 'isAdContainer' in row` 区分，并单独报广告数。

* `web_search_artworks(word, **params)` → `GET ajax/search/artworks/{word}`；`word` 同时进路径与查询 → `body.illustManga.data`/`total`/`lastPage`。
* `web_search_illustrations(word, **params)` → `GET ajax/search/illustrations/{word}`；`type` 限 `illust_and_ugoira`/`illust`/`ugoira` → `body.illust.data`。
* `web_search_manga(word, **params)` → `GET ajax/search/manga/{word}`；另有 `work_lang`、`type='manga'` → `body.manga.data`。
* `web_search_novels(word, **params)` → `GET ajax/search/novels/{word}`；另有 `work_lang`/`gs`/`tlt`/`tgt`/`original_only`/`genre`/`csw` → `body.novel.data`。
* `web_search_top(word, **params)` → `GET ajax/search/top/{word}`；→ `body.novel`/`illust`/`manga`/`popular`/`relatedTags`。
* `web_search_tags(tag, **params)` → `GET ajax/search/tags/{tag}`；→ `body.tag`/`word`/`pixpedia`/`breadcrumbs`/`tagTranslation`。
* `web_search_users(**params)` → `GET ajax/search/users`；`nick`/`s_mode`/`i` → 用户搜索信封。
* `web_search_suggestion(**params)` → `GET ajax/search/suggestion`；`mode` → `popularTags`/`recommendTags`/`recommendByTags`/`myFavoriteTags`/`tagTranslation`/`thumbnails`。
* `web_search_autocomplete(keyword, **params)` → `GET rpc/cps.php`；`keyword` → 裸对象 `candidates[]`（`access_count`/`tag_name`/`tag_translation`/`type`）。

#### 用户（16 个只读 `GET`）

* `web_user_show(user_id, **params)` → `GET ajax/user/{user_id}`；`full` → 用户资料（`name`/`image`/`premium`/`isFollowed`/私密区块…）。
* `web_user_profile_all(user_id, **params)` → `GET ajax/user/{user_id}/profile/all`；→ `body.illusts`/`manga`（编号→null 字典）、`novels`、`bookmarkCount`、`pickup` 等。
* `web_user_profile_top(user_id, **params)` → `GET ajax/user/{user_id}/profile/top`；→ `illusts`/`manga`/`novels`/`pickup`（顶层键按来源）。
* `web_user_profile_illusts(user_id, **params)` → `GET ajax/user/{user_id}/profile/illusts`；`ids`（列表）/`work_category`/`is_first_page` → `body.works` 以编号为键。
* `web_user_profile_novels(user_id, **params)` → `GET ajax/user/{user_id}/profile/novels`；`ids`（列表）/`is_first_page` → `body.works` 以编号为键（键名是 `works`，不是 `novels`）。
* `web_user_illusts(user_id, **params)` → `GET ajax/user/{user_id}/illusts`；`ids`（列表）→ `body` 以插画编号为键。
* `web_user_meta(user_id, **params)` → `GET ajax/user/{user_id}/meta`；→ 用户 meta 块。
* `web_user_works_latest(user_id, **params)` → `GET ajax/user/{user_id}/works/latest`；→ `illusts`/`novels`。
* `web_user_following(user_id, **params)` → `GET ajax/user/{user_id}/following`；`offset`/`limit`/`rest` → `users`/`total`/`followUserTags`；匿名实测 `400`（需 Cookie）。
* `web_user_followers(user_id, **params)` → `GET ajax/user/{user_id}/followers`；`offset`/`limit` → 粉丝列表。
* `web_user_recommends(user_id, **params)` → `GET ajax/user/{user_id}/recommends`；`userNum`/`workNum`/`isR18` → `recommendUsers`/`thumbnails`。
* `web_user_tagged(user_id, work_type, **params)` → `GET ajax/user/{user_id}/{work_type}/tag`；`work_type ∈ {illusts, manga, illustmanga, novels}`；`tag`/`offset`/`limit` → 作品 + `total`。
* `web_user_tags(user_id, work_type, **params)` → `GET ajax/user/{user_id}/{work_type}/tags`；`work_type ∈ {illusts, manga, illustmanga, novels}`；`all` → `body` 数组 `tag`/`count`。
* `web_user_bookmarks(user_id, work_type, **params)` → `GET ajax/user/{user_id}/{work_type}/bookmarks`；`work_type ∈ {illusts, novels}`；`tag`/`offset`/`limit`/`rest` → 作品 + `total`；匿名实测 `400`（需 Cookie）。
* `web_user_bookmark_tags(user_id, work_type, **params)` → `GET ajax/user/{user_id}/{work_type}/bookmark/tags`；`work_type ∈ {illusts, novels}` → `public`/`private`/`tooManyBookmark`/`tooManyBookmarkTags`。
* `web_user_extra(**params)` → `GET ajax/user/extra`；`is_smartphone`/`version` → `background`/`followers`/`following`/`mypixivCount`。

#### 关注、发现与首页（8 个只读 `GET`）

* `web_follow_latest(work_type, **params)` → `GET ajax/follow_latest/{work_type}`；`work_type ∈ {illust, novel}`；`mode`/`p` → `page`/`thumbnails`；`illust` 匿名实测 `400`（需 Cookie）。
* `web_mypixiv_latest(**params)` → `GET ajax/mypixiv_latest/illust`；`p` → MyPixiv 流（需 Cookie）。
* `web_watch_list(work_type, **params)` → `GET ajax/watch_list/{work_type}`；`work_type ∈ {manga, novel}`；`p`/`new` → 追更系列列表。
* `web_street(section, **params)` → `GET ajax/street/{section}`；`section ∈ {recommend_tags, latest, sub, for_you}` → 首页区块（趋势标签在这里）。
* `web_top_illust(**params)` → `GET ajax/top/illust`；`mode` → 首页插画区块；匿名实测 `400`（需 Cookie）。
* `web_discovery_artworks(**params)` → `GET ajax/discovery/artworks`；`mode`/`limit` → `thumbnails`/`recommendations`；匿名实测 `400`（需 Cookie）。
* `web_discovery_novels(**params)` → `GET ajax/discovery/novels`；`mode`/`limit` → `thumbnails`/`recommendedNovelIds`/`recommendNovelDetails`。
* `web_discovery_users(**params)` → `GET ajax/discovery/users`；`limit` → `users`/`thumbnails`。

#### 排行榜（2 个只读 `GET`）

* `web_ranking(**params)` → `GET ranking.php`；方法先补 `format='json'`；`mode`/`content`/`date`/`p` → **裸根对象**（`contents`/`rank_total`/`page`/`prev`/`next`/`date`）；每条 `contents` 的 `illust_series` 可能是布尔 `false` 或带 `illust_series_id`/`title`/`page_url` 等键的对象。
* `web_novel_ranking(**params)` → `GET ajax/ranking/novel`；`mode`/`date`/`p`/`content` → `{"error", "body"}`，排行在 `body.display_a.rank_a`。

#### 特辑与标签（4 个只读 `GET`）

* `web_showcase_article(article_id, **params)` → `GET ajax/showcase/article`；`article_id`（查询键）→ 文章元数据 + `illusts`/`novels`；来源只有前端逆向，`/showcase/` 页面本轮重定向 `302` 且不跟随，读取来源里没有有效 `article_id`，因此真实编号未实测。
* `web_tag_info(tag, **params)` → `GET ajax/tag/info`；`tag` → `tag`/`abstract`/`thumbnail`/`en`/`ja`。
* `web_frequent_tags(work_type, **params)` → `GET ajax/tags/frequent/{work_type}`；`work_type ∈ {illust, novel}`；`ids`（列表）→ 共同标签数组。
* `web_suggest_tags(word, **params)` → `GET ajax/tags/suggest_by_word`；`word` → `illust_count`/`tag_name`/`total_count`。

#### 交互与写入（17 个：16 个 `POST` + 1 个 `GET`；**本项目从不调用**，全部需会话 Cookie 与配套 CSRF token）

带 `work_type` 的每个模板只列一次；正文形态与来源字段名写在[方法参考](pixiv-api.md)。带「需 Cookie」的网页端路由没有会话时站点自行拒绝。

* `web_bookmark_add(work_type, **attributes)` → `POST ajax/{work_type}/bookmarks/add`（**JSON**）；`work_type ∈ {illusts, novels}`；体含 `illust_id`/`novel_id`/`restrict`/`comment`/`tags`。
* `web_bookmark_delete(work_type, **attributes)` → `POST ajax/{work_type}/bookmarks/delete`（**表单**）；`work_type ∈ {illusts, novels}`；体含 `bookmark_id`，小说用 `book_id` + `del='1'`。
* `web_bookmark_add_tags(work_type, **attributes)` → `POST ajax/{work_type}/bookmarks/add_tags`（JSON）；`{illusts, novels}`；`bookmark_ids`/`tags`。
* `web_bookmark_edit_restrict(work_type, **attributes)` → `POST ajax/{work_type}/bookmarks/edit_restrict`（JSON）；`{illusts, novels}`；`bookmarkIds`/`bookmarkRestrict`（`private`/`public`）。
* `web_bookmark_remove(work_type, **attributes)` → `POST ajax/{work_type}/bookmarks/remove`（JSON）；`{illusts, novels}`；`bookmarkIds`。
* `web_bookmark_rename_progress(work_type, **params)` → `GET ajax/{work_type}/bookmarks/rename_tag_progress`；`{illusts, novels}` → `body.isInProgress`。**这一条是 `GET`**。
* `web_like(work_type, **attributes)` → `POST ajax/{work_type}/like`（JSON）；`{illusts, novels}`；体含 `illust_id`/`novel_id`；来源称返回 `is_liked`、无撤销。
* `web_comment_post(work_type, **attributes)` → `POST rpc/post_comment.php`（`illust`）或 `POST novel/rpc/post_comment.php`（`novel`）（**表单**）；`work_type ∈ {illust, novel}`；体含 `type`/`illust_id`/`novel_id`/`author_user_id`/`comment`/`parent_id`/`stamp_id`。
* `web_comment_delete(work_type, **attributes)` → `POST rpc_delete_comment.php` / `novel/rpc_delete_comment.php`（**表单**）；`work_type ∈ {illust, novel}`；体含 `i_id`/`del_id`。
* `web_user_follow_add(user_id, **attributes)` → `POST bookmark_add.php`（**表单**）；固定 `mode='add'`/`type='user'`/`format='json'` + `user_id`，属性含 `restrict`/`tag`。
* `web_user_follow_delete(user_id, **attributes)` → `POST rpc_group_setting.php`（**表单**）；固定 `mode='del'`/`type='bookuser'`/`id=user_id`。
* `web_user_block(user_id, action, **attributes)` → `POST ajax/block/save`（JSON）；`action ∈ {block, unblock}`。
* `web_series_watch(work_type, series_id, **attributes)` → `POST ajax/{work_type}/series/{series_id}/watch`（JSON，体可空）；`work_type ∈ {illust, novel}`。
* `web_series_unwatch(work_type, series_id, **attributes)` → 同路径 `/unwatch`（JSON）；`{illust, novel}`。
* `web_series_notify_on(work_type, series_id, **attributes)` → 同路径 `/watchlist/notification/turn_on`（JSON）；`{illust, novel}`。
* `web_series_notify_off(work_type, series_id, **attributes)` → 同路径 `/watchlist/notification/turn_off`（JSON）；`{illust, novel}`。
* `web_illust_tag_add(illust_id, tag, **attributes)` → `POST ajax/tags/illust/{illust_id}/add`（JSON）；体含 `tag`。

### App 面（59 个 `app_` 方法）

App 面返回**裸 JSON、没有 `{"error","message","body"}` 信封**，列表就是 `{"…": [...], "next_url": "..."}` 这个对象。带 **需 token** 的方法用 `Pixiv('pixiv', access_token='<你的 token>')`；匿名调用返回站点自己的 `400`。**App 面成功路径未实测**：来源是公开客户端 `pixivpy`、一份第三方 OpenAPI、一份 **2016 年** Android 客户端抓包（旧版本，**不是当前服务端规范，也不保证路由仍可用**）与 gallery-dl 的显式函数。来源只给路径、未声明返回 schema 的行已如实标注「来源未声明」，本库**不编造字段**。

#### 用户（13 个只读 `GET`，均需 token）

* `app_user_detail(user_id, **params)` → `GET v1/user/detail`；`filter` → `{user, profile, profile_publicity, workspace}`。
* `app_user_illusts(user_id, **params)` → `GET v1/user/illusts`；`type`（`illust`/`manga`）/`filter`/`offset` → `{user, illusts, next_url}`。
* `app_user_bookmarks_illust(user_id, **params)` → `GET v1/user/bookmarks/illust`；`restrict`/`filter`/`max_bookmark_id`/`tag` → `{illusts, next_url}`。
* `app_user_bookmarks_novel(user_id, **params)` → `GET v1/user/bookmarks/novel`；同上 → `{novels, next_url}`。
* `app_user_related(seed_user_id, **params)` → `GET v1/user/related`；`filter`/`offset` → `{user_previews, next_url}`。
* `app_user_recommended(**params)` → `GET v1/user/recommended`；`filter`/`offset` → `{user_previews, next_url}`。
* `app_user_following(user_id, **params)` → `GET v1/user/following`；`restrict`/`offset` → `{user_previews, next_url}`。
* `app_user_follower(user_id, **params)` → `GET v1/user/follower`；`filter`/`offset` → `{user_previews, next_url}`。
* `app_user_mypixiv(user_id, **params)` → `GET v1/user/mypixiv`；`offset` → `{user_previews, next_url}`。
* `app_user_list(user_id, **params)` → `GET v2/user/list`；`filter`/`offset` → `{user_previews, next_url}`。
* `app_user_bookmark_tags_illust(user_id, **params)` → `GET v1/user/bookmark-tags/illust`；`restrict`/`offset` → `{bookmark_tags, next_url}`。
* `app_user_bookmark_tags_novel(user_id, **params)` → `GET v1/user/bookmark-tags/novel`；`restrict`/`offset` → `{bookmark_tags, next_url}`（来源只有抓包）。
* `app_user_follow_detail(user_id, **params)` → `GET v1/user/follow/detail`；→ `{follow_detail: {is_followed, restrict}}`（来源只有抓包）。

#### 插画（14 个只读 `GET`）

* `app_illust_detail(illust_id, **params)` → `GET v1/illust/detail`（**需 token**；匿名实测 `400`）；→ `{illust}`（`type`/`image_urls`/`meta_pages`/`tags`…）。
* `app_illust_follow(**params)` → `GET v2/illust/follow`（**需 token**）；`restrict`/`offset` → `{illusts, next_url}`。
* `app_illust_mypixiv(**params)` → `GET v2/illust/mypixiv`（**需 token**）；`offset` → `{illusts, next_url}`（来源只有抓包）。
* `app_illust_popular(**params)` → `GET v1/illust/popular`（**需 token**）；**来源只给路径、未声明 schema，也不要求 `illust_id`**，本库不声称任何返回字段。
* `app_illust_comments(illust_id, **params)` → `GET v1/illust/comments`（**需 token**）；`offset`/`include_total_comments` → `{comments, next_url, total_comments?}`。
* `app_illust_series(illust_series_id, **params)` → `GET v1/illust/series`（**需 token**）；`illust_series_id`（查询键）/`offset` → `{illusts, next_url, illust_series_detail: {title, caption, series_work_count}}`（来源为 gallery-dl；匿名实测 `400`，成功未实测）。
* `app_illust_comments_v3(illust_id, **params)` → `GET v3/illust/comments`（**需 token**）；`illust_id` → `{comments, next_url}`（来源为 gallery-dl；独立的 v3 路由，不是 v1 的别名；成功未实测）。
* `app_illust_comment_replies(comment_id, **params)` → `GET v1/illust/comment/replies`（**需 token**）；→ `{comments, next_url}`（来源为第三方 OpenAPI）。
* `app_illust_related(illust_id, **params)` → `GET v2/illust/related`（**需 token**）；`filter`/`seed_illust_ids`（列表）/`offset`/`viewed`（列表）→ `{illusts, next_url}`。
* `app_illust_recommended(**params)` → `GET v1/illust/recommended`（**需 token**）；`content_type`/`include_ranking_label`/`offset`/`viewed` 等 → `{illusts, ranking_illusts, next_url}`。
* `app_illust_ranking(**params)` → `GET v1/illust/ranking`（**需 token**）；`mode`/`filter`/`date`/`offset` → `{illusts, next_url}`；`mode` 取值（来源）：`day`/`day_male`/`day_female`/`week_original`/`week_rookie`/`week`/`month`/`day_r18`/`day_male_r18`/`day_female_r18`/`week_r18`/`week_r18g` 及 manga 变体。
* `app_illust_new(**params)` → `GET v1/illust/new`（**需 token**）；`content_type`/`filter`/`max_illust_id` → `{illusts, next_url}`。
* `app_manga_recommended(**params)` → `GET v1/manga/recommended`（**需 token**）；`filter`/`include_ranking_illusts`/`max_bookmark_id`/`offset` → `{illusts, ranking_illusts, next_url}`（来源只有抓包）。
* `app_ugoira_metadata(illust_id, **params)` → `GET v1/ugoira/metadata`（**需 token**）；→ `{ugoira_metadata: {zip_urls, frames}}`。

#### 搜索（4 个只读 `GET`，均需 token）

* `app_search_illust(word, **params)` → `GET v1/search/illust`；`search_target`/`sort`/`duration`/`start_date`/`end_date`/`filter`/`search_ai_type`/`offset` → `{illusts, next_url, search_span_limit, show_ai}`。
* `app_search_novel(word, **params)` → `GET v1/search/novel`；同 `app_search_illust` 另加 `merge_plain_keyword_results`/`include_translated_tag_results`/`search_target='text'` → `{novels, next_url, …}`。
* `app_search_user(word, **params)` → `GET v1/search/user`；`sort`/`duration`/`filter`/`offset` → `{user_previews, next_url}`。
* `app_search_autocomplete(word, **params)` → `GET v1/search/autocomplete`；→ `{search_auto_complete_keywords: [...]}`（来源只有抓包，**数组元素字段来源未声明**）。

#### 小说（11 个只读 `GET`，均需 token）

* `app_novel_detail(novel_id, **params)` → `GET v2/novel/detail`；→ `{novel}`。
* `app_novel_series(series_id, **params)` → `GET v2/novel/series`；`filter`/`last_order` → `{novel_series_detail, novels, next_url}`。
* `app_novel_comments(novel_id, **params)` → `GET v1/novel/comments`；`offset`/`include_total_comments` → `{comments, next_url, total_comments?, comment_access_control}`。
* `app_novel_recommended(**params)` → `GET v1/novel/recommended`；`include_ranking_label`/`filter`/`offset`/`include_ranking_novels`/`already_recommended`（逗号串）/`max_bookmark_id_for_recommend` → `{novels, ranking_novels, next_url}`。
* `app_novel_new(**params)` → `GET v1/novel/new`；`filter`/`max_novel_id` → `{novels, next_url}`。
* `app_novel_follow(**params)` → `GET v1/novel/follow`；`restrict`（`public`/`private`/`all`）/`offset` → `{novels, next_url}`。
* `app_novel_ranking(**params)` → `GET v1/novel/ranking`；`mode`/`date`/`offset` → `{novels, next_url}`（来源只有抓包）；`mode` 取值：`day`/`day_male`/`day_female`/`week_rookie`/`week`/`day_r18`/`week_r18`。
* `app_novel_mypixiv(**params)` → `GET v1/novel/mypixiv`；`offset` → `{novels, next_url}`（来源只有抓包）。
* `app_novel_popular(**params)` → `GET v1/novel/popular`；**来源只给路径、未声明 schema，也不要求 `novel_id`**，本库不声称任何返回字段。
* `app_user_novels(user_id, **params)` → `GET v1/user/novels`；`filter`/`offset` → `{user, novels, next_url}`。
* `app_webview_novel(novel_id, **params)` → `GET webview/v2/novel`；`novel_id` 作为 `id`；`viewer_version` → **HTML 文本**（`response_format='text'`，不解析、不抽正文）。

#### 趋势标签（3 个只读 `GET`，均需 token）

* `app_trending_tags_illust(**params)` → `GET v1/trending-tags/illust`；`filter` → `{trend_tags}`。
* `app_trending_tags_manga(**params)` → `GET v1/trending-tags/manga`；`filter` → **来源只给路径、未声明成功 schema**，本库不声称返回字段。
* `app_trending_tags_novel(**params)` → `GET v1/trending-tags/novel`；`filter` → 同上，不声称返回字段。

#### 收藏、浏览历史、账号状态与匿名（8 个只读 `GET`）

* `app_illust_bookmark_detail(illust_id, **params)` → `GET v2/illust/bookmark/detail`（**需 token**）；→ `{bookmark_detail: {is_bookmarked, tags}}`。
* `app_novel_bookmark_detail(novel_id, **params)` → `GET v2/novel/bookmark/detail`（**需 token**）；→ `{bookmark_detail: {is_bookmarked, restrict, tags}}`。
* `app_user_browsing_history_illusts(**params)` → `GET v1/user/browsing-history/illusts`（**需 token**）；`offset` → `{illusts, next_url}`（来源只有抓包；来源**未要求** `user_id`）。
* `app_user_browsing_history_novels(**params)` → `GET v1/user/browsing-history/novels`（**需 token**）；`offset` → `{novels, next_url}`（来源只有抓包）。
* `app_user_state(**params)` → `GET v1/user/me/state`（**需 token**）；→ `{user_state: {is_mail_authorized}}`（来源只有抓包）。
* `app_application_info(**params)` → `GET v1/application-info/android`；**匿名实测 `200`**；→ `{application_info}`。
* `app_emoji(**params)` → `GET v1/emoji`；**匿名实测 `200`**；→ `{emoji_definitions}`。
* `app_spotlight_articles(**params)` → `GET v1/spotlight/articles`（**需 token**；匿名实测 `400`）；`category`/`offset` → `{spotlight_articles, next_url}`。

#### App 写入（6 个 `POST`，**表单**正文，均需 token；**本项目从不调用**）

* `app_illust_bookmark_add(illust_id, **attributes)` → `POST v2/illust/bookmark/add`；体含 `illust_id`/`restrict`/`tags`（列表）。
* `app_illust_bookmark_delete(illust_id, **attributes)` → `POST v1/illust/bookmark/delete`；体含 `illust_id`。
* `app_illust_browsing_history_add(illust_ids, **attributes)` → `POST v2/user/browsing-history/illust/add`；体含 `illust_ids[]`；来源声明响应是空 JSON 对象。
* `app_user_follow_add(user_id, **attributes)` → `POST v1/user/follow/add`；体含 `user_id`/`restrict`。
* `app_user_follow_delete(user_id, **attributes)` → `POST v1/user/follow/delete`；体含 `user_id`。
* `app_user_edit_ai_show_settings(show_ai, **attributes)` → `POST v1/user/ai-show-settings/edit`；体含 `show_ai`（布尔，编码成 `true`/`false`）。

## 本库不封装的能力

下面这些要么不属于公开读取面，要么不是美术作品契约，要么本库按仓库一贯规则不做。需要时用 `client.request(method, path, api=..., params=…, data=…, form=…, headers=…)` 自己发；本库不绕过任何访问控制。

| 类别 | 情况 | 为什么不封装 |
| :--- | :--- | :--- |
| OAuth2 登录 / PKCE / 令牌刷新 | `app-api.pixiv.net/web/v1/login`、`oauth.secure.pixiv.net/auth/token` | 本库不登录、不换令牌、不刷新，只接收你已有的 `access_token`；也不自动取 `PHPSESSID`（网页端 `Cookie`） |
| 注册、资料编辑、账号管理 | 账号设置、profile 修改、邮箱/密码 | 需要登录态的账号服务，不是作品浏览/交互契约 |
| 网页端写路由的 CSRF 自动获取 | 从首页 HTML 的 `__NEXT_DATA__` 抓 `X-CSRF-TOKEN` | 本库不解析 HTML、不自取 token；`csrf_token` 由调用方传入 |
| 上传 / 编辑 / 删除作品 | 投稿、改图、删图 | 没有取得可依赖的契约来源；且属写操作 |
| 通知 / webpush / dashboard / tumeng | `ajax/notification`、`ajax/webpush`、`ajax/dashboard/*`、`ajax/linked_service/tumeng` | 账号服务，超出公开读取面 |
| Sketch / FANBOX / 约稿市场 | `ajax/sketch/*`、commission/request 的创建、完成、创作者市场、story 门户 | 平台型周边服务，不是插画 API 契约 |
| 旧版 Public API / Works API | 已废弃的 `public-api.pixiv.net` | 上游客户端已退役，不沿用 |
| App 面 `*-nologin` 与废弃路由 | `v1/illust/recommended-nologin`、`v1/novel/recommended-nologin` 实测 `404`；`v1/novel/text`（`novel_text`）已废弃；旧的 `v1/novel/series` | 路由已不存在或已被替代；小说系列用选定的 `v2/novel/series`（不声称服务端迁移已验证） |
| App 面实测 `404` 的两条候选 | `v1/novel/markers`、`v2/illust/comments`（v2 评论）本轮带配置 UA、无 token 实测 `404` | 探测当下返 `404`，本库从原生移除、归入排除；**不绝对断言路由已消失**，需要时用通用 `request()` 显式调用 |
| App 面无契约来源的写路由 | 小说收藏 add/delete、评论写入、小说正文/标记写入 | 这些没有取得可依赖的来源，本库**不发明对称 API**；对应的网页端收藏/评论交互已封装 |
| App 面引导与账号周边 | `v1/walkthrough/illusts`、`v1/walkthrough/renewal-description` 等 onboarding、应用设置、注册 | 引导/账号服务，不属于美术作品读取面 |
| 首页「趋势」独立路由 | 没有 `/ajax/trending` | 趋势标签在 `web_street('recommend_tags')` 或 `web_search_suggestion()` 里，不为它虚构路由 |
| HTML 抓取 / 静态资源 / CDN 下载 | 网页 HTML、CSS/JS/图片字节 | 本库只发 JSON API 请求；`urls`/`zip_urls` 只是字符串地址，不下载、不解析 |
| 换宿主绕过（`app-api.pixivlite.com` 等） | 第三方镜像宿主 | 只换域名不是独立契约面；通用 `request()` 可显式调用任意路由 |

## 边界与未实测

* **App 面成功路径全部未实测**：59 个 `app_` 方法里，只有 `app_application_info()` 与 `app_emoji()` 拿到匿名 `200`；`app_illust_detail` / `app_novel_detail` / `app_spotlight_articles` 的匿名 `400` 是**拒绝证据**，不是成功，也**不代表这些需要登录的路由仍可用**。其余路由、参数、返回字段来自公开客户端 `pixivpy`、一份第三方 OpenAPI、一份 **2016 年** Android 抓包与 gallery-dl（第二依据；旧抓包**不是当前服务端规范，不保证路由仍可用**）。生产前用你自己的 token 自测。
* **App 面若干路由只给路径、未声明返回 schema**：`app_trending_tags_manga()`、`app_trending_tags_novel()`、`app_illust_popular()`、`app_novel_popular()`、`app_search_autocomplete()`（`search_auto_complete_keywords` 的元素）、`app_user_state()`（`user_state` 内字段）都只按来源给出路由与已见键，本库**不声称返回字段**。
* **两条 App 候选路由本轮实测 `404`**：`v1/novel/markers` 与 `v2/illust/comments` 在带配置 UA、无 token 的探测下都返 `404`，因此没有作为原生方法；这只是当次观测，**不绝对推断路由已消失**，需要时用通用 `request()` 显式调用。
* **网页端账号范围方法无成功样本**：`web_user_following`、`web_user_bookmarks`、`web_follow_latest`、`web_top_illust`、`web_discovery_artworks` 匿名实测 `400`，需要会话 `Cookie`；本库已提供方法但没有带 Cookie 的成功响应。
* **所有写方法一次都没执行**：16 个网页端 `POST` + 6 个 App `POST` + 1 个网页端写查询（`web_bookmark_rename_progress`，`GET`）都只做源码对齐。JSON 还是表单正文、成功返回字段，来源未声明的地方本库不编造。项目从不调用它们。
* **参数枚举未穷尽**：搜索的 `ai_type`/`dgw`/`wlt`/`wgt`/`hlt`/`hgt`/`ratio`/`tool`/`scd`/`ecd`/`blt`/`bgt`，小说搜索的 `gs`/`tlt`/`tgt`/`original_only`/`genre`/`csw`，榜单 `mode` 的全部取值，`web_novel_series_content` 的 `order_by`（来源写作 `asc`/`dsc`）等，都只有来源枚举，未逐值实测；参数名不在已知集合里也会原样发出。
* **`work_type` 取值不校验**：索引里给的集合是来源与实测见过的取值，本库不做本地校验，未知值会直奔站点自己的路由。
* **`web_illust_new` 的匿名契约未定**：本轮一次探测 `lastId=0&limit=2&type=illust&r18=False` 回 `400`，该路由参数敏感，字段与成功形态按来源。
* **媒体字节零请求**：所有 `i.pximg.net` / `s.pximg.net` / `pixon.ads-pixiv.net` 地址一个都没请求过；可下载性、Referer 要求与许可未验证。
* **网页端反爬现实**：缺 Referer / 非日 IP / 数据中心 IP 的请求可能得到 `403` 挑战或 `{"error": true, ...}`，某些路由跳到登录页；本库不伪造头、不绕行，头缺失下的现象不作站点结论。
* **依据分级**：网页端 = 匿名只读响应 + 社区前端逆向（第二依据）；App 面 = 公开客户端源码（第二依据）。**没有**官方 OpenAPI 或服务端源码，也没有一份完整官方规范；来源冲突（如评论路由 `v1`/`v2`）以上市实现为准并在[契约附注](pixiv-contract-notes.md)记录。

更细的未实测清单见[客户端用法](pixiv.md#边界与未实测)；逐条 URL、状态码与响应摘要见[验证记录](verification.md)；依据出处与排除项见[契约附注](pixiv-contract-notes.md)。

继续阅读：[客户端用法](pixiv.md) · [方法参考](pixiv-api.md) · [契约附注](pixiv-contract-notes.md) · [验证记录](verification.md)。
