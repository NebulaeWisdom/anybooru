# ArtStation：我要做什么，用哪个方法？

`ArtStation` 包装 `https://www.artstation.com` 的公开作品集资源与 RSS：**15 个原生 GET，
其中 14 个返回完整 JSON，1 个返回 RSS 原文**。没有原生写方法、登录或凭据配置，不下载媒体。
它不是 booru 家族：作品的数字 `id` 与网页短码 `hash_id` 是两个字段，不能相互推导。

本页只做任务选型与完整方法索引；构造和通用请求见 [客户端用法](artstation.md)，
全部参数、缺省行为、字段与代码见 [方法参考](artstation-api.md)。

## 按目的找调用

以下调用中的 `client` 由 `ArtStation('artstation')` 创建；值都是可直接使用的字面示例。

| 我要做什么 | 调用 | 返回的关键内容 |
| :--- | :--- | :--- |
| 浏览全站作品页 | `client.project_list(page=1, per_page=2)` | 完整 `{data,total_count}`；每项有 `id/hash_id/title/permalink/cover/assets_count/user/views_count` |
| 按关键词找作品 | `client.project_search(query='cat', page=1, per_page=3, sorting='relevance')` | 完整 `{total_count,data}`；作品链接在 `url`，缩略图在 `smaller_square_cover_url` |
| 按标题过滤并翻页 | `client.project_search(query='', page=2, per_page=3, sorting='relevance', filters='[{"field":"title","method":"contain","value":"dragon"}]')` | GET filters 为 JSON **字符串**；第 2 页有 200 样本，返回独立的三条搜索结果 |
| 查看过滤器字段与候选选项 | `client.search_filter_fields()` | 裸数组，项含 `name/type`；多选类型另有 `select_options`，不是每项都有 |
| 读取随机作品及资产信息 | `client.project_random()` | 单个作品对象，含 `id/hash_id/assets/tags/categories/user`；不能指定作品 ID |
| 查看用户资料与专辑摘要 | `client.user_show('timwarnock')` | 用户对象；`id/username/projects_count/skills/software_items/albums_with_community_projects` |
| 读取较小的用户资料卡 | `client.user_quick('timwarnock')` | 另一份用户对象；含社交单列链接和 `is_artist/is_beta`，不是 user_show 的简单子集 |
| 读取 v2 用户资料 | `client.user_profile('timwarnock')` | 用户对象；`projects_count/portfolio/social_profiles/subdomain`，不与其它用户响应合并 |
| 按页看用户作品 | `client.user_projects('timwarnock', page=2, per_page=2)` | `{data,total_count}`；本轮条目没有全站列表的 `user/views_count` |
| 查看该用户关注的人 | `client.user_following('timwarnock', page=1, per_page=2)` | `{data,total_count}`；每项是用户卡，含 `username/full_name/sample_projects` |
| 查看专辑内作品与资产摘要 | `client.album_projects(104104, page=1, per_page=4)` | `{total_count,data}`；条目直接带 `album_id/album_title/position/assets/description` |
| 选择频道 | `client.channel_list()` | `{total_count,data}`；每项有 `id/name/uri/type`，样本 70 为 Abstract |
| 看频道里的作品 | `client.channel_projects(70, page=1, per_page=5)` | `{total_count,data}`；条目含 `is_highlighted/small_square_cover_url` |
| 看 Explore 最新流 | `client.explore_latest(page=1, per_page=10)` | **仅 `{data}`，没有 total_count** |
| 看指定作品评论 | `client.project_comments(22897630)` | 数字作品 ID；本轮 `{total_count:0,data:[]}`，不猜非空评论字段 |
| 读 RSS 订阅 | `client.feed(sorting='latest')` | RSS 完整字符串，样本 50 个 item；不解析、不访问媒体链接 |

例如搜索最短调用不能省掉分页：缺 `page` 或 `per_page` 都有 400 样本，
每页 2 条也会报错。页码、每页限制、错误体与缺省值的细节统一查方法参考，不由本页另定一套规则。

## 完整方法索引（15 GET）

路径都接在 `https://www.artstation.com` 后面；JSON 始终完整返回，不拆 `data`。

| 方法签名 | 路由 | 返回 |
| :--- | :--- | :--- |
| `project_list(**params)` | `/projects.json` | 作品列表对象 `{data,total_count}` |
| `project_random()` | `/random_project.json` | 单个随机作品对象 |
| `user_show(username)` | `/users/{username}.json` | 用户资料对象 |
| `user_quick(username)` | `/users/{username}/quick.json` | 另一种用户资料对象 |
| `user_profile(username)` | `/api/v2/user_profiles/{username}.json` | v2 用户资料对象 |
| `user_projects(username, **params)` | `/users/{username}/projects.json` | 用户作品列表对象 |
| `user_following(username, **params)` | `/users/{username}/following.json` | 关注用户列表对象 |
| `project_search(**params)` | `/api/v2/search/projects.json` | 搜索结果对象 `{total_count,data}` |
| `search_filter_fields()` | `/api/v2/search/projects/filter_fields.json` | 过滤器字段数组 |
| `album_projects(album_id, **params)` | `/api/v2/community/projects/by_album.json` | 专辑作品列表对象，album_id 在查询串 |
| `channel_list()` | `/api/v2/community/channels/channels.json` | 频道列表对象 |
| `channel_projects(channel_id, **params)` | `/api/v2/community/channels/projects.json` | 频道作品列表对象，channel_id 在查询串 |
| `project_comments(project_id, **params)` | `/api/v2/community/projects/{project_id}/comments.json` | 评论列表对象 |
| `explore_latest(**params)` | `/api/v2/community/explore/projects/latest.json` | 只有 data 的列表对象 |
| `feed(**params)` | `/artwork.rss` | XML 原文字符串 |

另有通用入口
`request(method, path, *, params=None, data=None, headers=None, response_format='json')`，
用来显式给路径、参数与返回格式；不自动获取权限或替换失败路由。

## 本库不封装的能力

| 能力 | 范围判断 |
| :--- | :--- |
| 按任意 ID/hash 读取指定作品完整详情 | `/projects/G1ew2N.json` 本轮 403 HTML 挑战，v2 `/community/projects/22897630.json` 是 401 data:null；没有 project_show，也不以随机或搜索替代 |
| POST 搜索与 CSRF 两步流程 | 只有候选输入叙述，没有本轮成功证据；不封装、不执行 |
| 账号、发布、互动写入、购物与消息 | 没有登录或权限管理，所有写入不在原生面 |
| HTML/内嵌 JSON 解析、sitemap、其它栏目枚举 | 不做解析器或遍历器；未逐项核验的路径不当可用接口 |
| 媒体下载与尺寸猜测 | 只交付接口给出的 URL，不改主机/尺寸/查询串，不请求媒体 |

## 边界与未实测

上表是方法能力，不是“所有方法与所有参数组合都真跑过”。15 条原生路由都有直接匿名响应样本，
Python 包装方法的实际执行范围见 [验证记录](verification.md#artstation匿名只读实测2026-09-20)。
其它排序、过滤组合、完整分页上限、认证成功、非空评论、媒体访问均未实测；
所有计数与字段集都只是快照，不是静态 schema。

匿名可达不等于内容使用许可；站点条款、输入资料的错误/缺口与集中未实测清单见
[契约附注](artstation-contract-notes.md#6-边界与未实测)。
