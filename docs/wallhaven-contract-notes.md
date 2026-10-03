# Wallhaven：契约依据、排除项与实测矛盾

本页供维护者核对依据与接入范围；调用入门见[客户端用法](wallhaven.md)，参数与返回字段见[方法参考](wallhaven-api.md)，任务选型见[能力入口](wallhaven-capabilities.md)，真实 URL、状态码与 `Content-Type` 见[验证记录](verification.md#wallhaven匿名只读实测2026-10-03)。

## 1. 依据与家族判定

| 标记 | 出处 | 能说明什么 |
| :--- | :--- | :--- |
| **官方** | 官方 API 页面 <https://wallhaven.cc/help/api>，本轮匿名 `GET` 为 `200 text/html`，标题 *API v1 Documentation* | 路径、查询参数名与取值、默认值、认证方式、限流与错误状态、响应示例的字段形状 |
| **实测** | 本轮对站点发起的匿名只读 `GET`（串行、不重试、不跟随跳转、不下载媒体、不带任何凭据） | 路由的状态码、`Content-Type`、错误体、信封键、字段是否出现、参数是否被采纳 |
| **未实测** | 官方声称、本轮没有请求或没有复现的分支 | 带密钥成功、私有收藏、NSFW、`X-API-Key` 头、`429` 触发 |

官方页面的小节锚点：`#wallpapers`（Accessing Wallpaper information）、`#search`（Searching and listings）、`#tags`（Tag info）、`#user-settings`（User Settings）、**User Collections 小节复用了 `#user-settings`**（页面里第二个 `id="user-settings"`，标题是 User Collections）、`#limits`（Rate Limiting and Errors）、`#auth`（Authentication）、`#changes`（Changes to the API）。本页与[方法参考](wallhaven-api.md)按标题引用，不按这个重复锚点。

**本轮只取到这一个帮助页作为公开契约，未取得服务端源码，也没有 OpenAPI 规范**。因此本页与方法参考都不引“源文件行号”或“OpenAPI schema”，只引官方页面标题/锚点与本轮真实 URL/状态/字段。网页里是站点自己的示例 JSON，不是机器可读规范；示例编号会失效（见第 5 节）。

**这是独立家族，不是给现有类加一个站点 URL。** 挂在站点根 `/api/v1` 下的路由、`apikey` 查询值、`{"data": ...}` / `{"data": [...], "meta": {...}}` 信封、三位 0/1 的 `categories` / `purity` 掩码、`topRange` 榜单范围、`q` 里的 `@`、`id:`、`type:`、`like:` 语法，都与现有 Danbooru、Moebooru、Serika、e621ng、Zerochan、Gelbooru、Gelbooru02、Shuushuu、Sakuria、Anime-Pictures、Cosine、nhentai、ArtStation 契约不同。仅“返回 JSON”或“参数是字符串”不构成同族。

## 2. 原生范围：7 个方法，全部 GET

| 方法 | 路由（主机均为 `wallhaven.cc`） | 官方小节 | 实测结果 |
| :--- | :--- | :--- | :--- |
| `wallpaper_search(**params)` | `/api/v1/search` | Searching and listings | `200`；`data` 24 条 + `meta`；参数与边界见第 5 节 |
| `wallpaper_show(wallpaper_id, **params)` | `/api/v1/w/{wallpaper_id}` | Accessing Wallpaper information | `pom5lj`、`9mjoy1` 为 `200`（含 `uploader` + `tags`）；官方示例 `94x38z` 与 `000000` 为 `404 {"error": "Nothing here"}` |
| `tag_show(tag_id, **params)` | `/api/v1/tag/{tag_id}` | Tag info | `tag/1` 为 `200`（`anime`）；`tag/0` 为 `404 {"error": "Nothing here"}` |
| `user_settings(**params)` | `/api/v1/settings` | User Settings | 匿名 `401 {"error": "Unauthorized"}`；带密钥成功**未实测** |
| `collection_list(**params)` | `/api/v1/collections` | User Collections | 匿名 **`404 {"error": "Nothing here"}`**（不是 401）；带密钥成功**未实测** |
| `user_collections(username, **params)` | `/api/v1/collections/{username}` | User Collections | `ThorRagnarok` `200`、`data` 3 项（274175/400286/384565）；`EstlinLuna` `200`、10 项；`LewisMweir13`、`rootkit` `200 {"data": []}`（无公开收藏） |
| `collection_wallpapers(username, collection_id, **params)` | `/api/v1/collections/{username}/{collection_id}` | User Collections | `ThorRagnarok/274175` `200`、`data` 24、`meta` 仅 `current_page,last_page,per_page,total`；第 2 页 `200`；`/0` 为 `404 {"error": "Nothing here"}` |

另有通用入口 `request(method, path, *, params=None, headers=None)`；它不增加权限或成功保证。7 个原生方法都是 `GET`，客户端不发明写请求、正文或其它动词。

## 3. 相似与用户入口：官方 7 条路径里没有独立路由

官方页面列出的 7 条路径里没有单独的“相似壁纸”或“用户资料/上传”路由；两者都放在搜索语法里。本节只说明官方未列独立路径、候选写法本轮 404，不排除站点另有未公开或本轮未请求到的路径：

| 想要 | 候选写法（本轮实测 404） | 官方做法 | 实测 |
| :--- | :--- | :--- | :--- |
| 相似壁纸 | `GET /api/v1/w/<id>/similar` | 搜索 `q='like:<wallpaper_id>'`，官方原文 *Find wallpapers with similar tags* | `/w/94x38z/similar`、`/w/pom5lj/similar` 都是 `404 {"error": "Not Found"}`；`q='like:94x38z'`、`q='like:pom5lj'` 本轮都是 `403 text/html`（Cloudflare 质询，`Cf-Mitigated: challenge`） |
| 用户资料 / 上传 | `GET /api/v1/user`、`GET /api/v1/user/<name>` | 用户上传用搜索 `q='@<username>'`；收藏用 `/api/v1/collections/<username>` | `/user`、`/user/LewisMweir13` 都是 `404 {"error": "Not Found"}`；`q='@LewisMweir13'` 为 `200`（`meta.total=46`） |

所以客户端**不设** `similar` 方法，也**不设** `user_show` / `profile` 方法：官方没有为它们列路径，客户端也不凭候选路径去猜。要看相似或上传，直接调 `wallpaper_search(q='like:<id>')` 或 `wallpaper_search(q='@<name>')`（见[方法参考](wallhaven-api.md#q-搜索语法)）。这两个候选路径的 404 只说明本轮的写法不对，不构成“站点绝无其它相似/资料入口”的结论。

`q='like:<id>'` 的 `403` 只是本轮观察：这是 Cloudflare 对那两次请求的质询，不能推广成“`like:` 永远不可用”，也不能仅凭它断言相似能力已移除。客户端不解挑战、不换 UA、不重试、不静默改用别的路径。

## 4. 认证与权限分支

官方 `#auth` 原文：密钥可以放在 URL 查询值 `?apikey=<API KEY>`，也可以放在请求头 `X-API-Key: <API KEY>`。客户端只自动发**配置的**查询值一种；请求头形式由调用方在单次 `headers` 里显式传（见[方法参考](wallhaven-api.md#客户端与通用约定客户端)）。构造：`apikey=None` 读包内配置，显式 `''` 匿名，非空即作为查询值发送；没有登录、没有凭据续期、构造不联网。

权限分支（**实测**与**未实测**分开）：

| 场景 | 结果 | 依据 |
| :--- | :--- | :--- |
| 匿名读 `/api/v1/settings` | `401 {"error": "Unauthorized"}` | 实测 |
| 匿名读 `/api/v1/collections`（自己的收藏） | **`404 {"error": "Nothing here"}`** | 实测。这条**不是** 401：路由按密钥归属取“自己的”收藏，匿名时没有归属对象 |
| 匿名读 `/api/v1/collections/<username>` | `200`，只含该用户的**公开**收藏；`ThorRagnarok` 3 项、`EstlinLuna` 10 项、`LewisMweir13`/`rootkit` 空数组 | 实测；官方原文 *Only collections that are public will be accessible to other users* |
| 带密钥读 `/api/v1/settings`、`/api/v1/collections`（含私有）、私有 `collection_wallpapers` | **未实测** | 本轮无凭据，未索要 |
| 匿名读 NSFW 壁纸 / 搜索含 `nsfw` 位 | 官方说无有效密钥是 `401`；实测 `purity=001` 搜索是 **`200` + `data=[]` + `meta.total=0`**（没有 401，也没有 NSFW 结果） | 两者并列记录，冲突照实保留 |

**匿名收藏范围**：`user_collections()` 只给公开收藏（他人视角）；**密钥持有者自己的全部收藏（含私有）走 `collection_list()`**；`collection_wallpapers()` 对他人只读公开收藏，密钥持有者可读自己的私有收藏。这三种可见性来自官方页面文字；其中公开收藏（空与非空）已有匿名实测样本，私有与本人的收藏没有样本。

## 5. 文档与实测的矛盾 / 参数语义

### 5.1 官方示例编号已失效

官方 `#wallpapers` 和 `#search` 的示例都用 `94x38z`。本轮实测 `GET https://wallhaven.cc/api/v1/w/94x38z` 是 `404 {"error": "Nothing here"}`，`GET https://wallhaven.cc/api/v1/w/94x38z/similar` 是 `404 {"error": "Not Found"}`。当前可用样本是 `pom5lj`（`200`，上传者 `LewisMweir13`）与 `9mjoy1`（`200`，`views=856409`、8 个标签）。**不要把官方示例里的编号、计数、字段值当稳定契约**。

### 5.2 “随机种子保证不重复”没有复现

官方 `#search` 原文：*Sorting by 'random' will produce a seed that can be passed between pages to ensure there are no repeats when getting a new page.* 实测：

* `sorting='random'&seed='abc123'&page=1` → `meta.seed="wPpR1H"`；
* `sorting='random'&seed='abc123'&page=2` → `meta.seed="vMFVjx"`（与第 1 页不同）；
* 把第 1 页返回的 `wPpR1H` 传回 `page=2` → `meta.seed="Ec2tSv"`。

**本轮样本两页返回的种子并不一致，跨页无重复没有被复现**；这只是抽样观察，不推广为站点普遍行为。客户端不固定、不改写、不缓存 seed，也不承诺去重；调用方若需要确定性分页，要自己保存并比较实际条目。

### 5.3 非法 `page` / `sorting` / `categories` 的服务器行为

| 请求 | 状态与正文 | 说明 |
| :--- | :--- | :--- |
| `search?page=1000000` | `400 application/json` `{"error": "Bad Request"}` | 页码过界 |
| `search?page=0` | `500 text/html`（HTML 错误页，标题 *It broke*） | 不是 JSON |
| `search?page=abc` | `200`，`meta.current_page=1` | 非数字被当成第一页 |
| `search?sorting=not-a-sort` | `200`，`data=[]`，但 `meta.total=501359,last_page=20890` | **空数组 ≠ 结果耗尽** |
| `search?categories=abc` | `200`，`data` 24 条，`meta.total=626058` | 非掩码值不报错 |
| `search?sorting=views&order=asc` | `200`，只回 2 条，但 `meta.per_page=24,total=501359` | **短页也 ≠ 结果耗尽** |

客户端原样透传这些参数，不钳位、不纠正、不因 `data=[]` 判终止。

### 5.4 404 的两种正文

命中路由但资源不存在 / 匿名无权 → `{"error": "Nothing here"}`：`/w/000000`、`/w/94x38z`、`/tag/0`、`/collections/ThorRagnarok/0`、匿名 `/collections`。
官方 7 条路径之外的候选路径 → `{"error": "Not Found"}`：`/w/{id}/similar`、`/user`、`/user/{name}`。
两种都是 `404 application/json`。

### 5.5 `403` 质询不是 JSON

`q='like:*'` 两次都是 `403`，`Content-Type: text/html; charset=UTF-8`，响应头 `Cf-Mitigated: challenge`，正文是 Cloudflare 的 *Just a moment...* 页。客户端把它当普通非 2xx 抛出（保留 `http_code` / `body`），不解析、不放行、不重试、不伪装 UA。其它 `q`（`nature`、`id:1`、`type:png`、`+nature -anime`、`@LewisMweir13`）都是 `200 application/json`。

### 5.6 返回形状的实测差异

* `meta.query`：`q='nature'` 回显 `"nature"`；无关键词为 `null`；`q='type:png'` 与 `q='@LewisMweir13'` 回显 **空串 `""`**；`q='id:1'` 回显对象 `{"id": 1, "tag": "anime"}`。三种类型（string / null / object）都要有分支处理，别假设恒为字符串。
* `meta.per_page` 实测恒为 `24`；官方页面也写死 24，参数表没有 `per_page`。
* **`collection_wallpapers` 的 `meta` 更窄**：实测 `ThorRagnarok/274175` 的 `meta` 只有 `current_page` / `last_page` / `per_page` / `total`，没有搜索 `meta` 的 `query` / `seed`。官方原文说它 *similar listing as the search results*，但信封并不完全相同，两处不能共用一套分页解析。
* `short_url` 官方示例是 `http://whvn.cc/...`，实测是 `https://whvn.cc/...`；按原样交付，不要改写协议。
* 搜索摘要**没有** `uploader` / `tags`，只有详情才有；把摘要当详情用会缺键。
* `source` 常为空串，也可能是一条 URL（样本 `https://www.artstation.com/artwork/EaDPkK`）。

## 6. 限流

官方 `#limits` 原文：*API calls are currently limited to 45 per minute*，超限回 `429`。本轮实测响应头带 `X-RateLimit-Limit: 45` 与递减的 `X-RateLimit-Remaining`，但**没有触发过 429**，滚动窗口与超限正文均未验证。客户端不内置节流、不重试、不指数退避；包内示例在每次调用前停顿控制节奏。

## 7. 未实测清单（不算契约）

* 带有效密钥的**任何成功路径**：`user_settings()`、`collection_list()`、私有 `collection_wallpapers()`、NSFW 图片与含 `nsfw` 位的搜索。本轮没有凭据，也没有向站点申请或伪造密钥。
* `X-API-Key` 请求头形式（只按官方 `#auth` 记录，未发请求）。
* 私有/本人的 `collection_wallpapers()` 响应（公开收藏已实测）。
* `429` 触发路径。
* `page` 的实际上界、`topRange` 各取值的含义差异、`sorting='hot'`（不在官方 API 参数表里）。
* 媒体地址：`path`、`thumbs`、`avatar` 一律原样交付，不请求、不校验、不下载。
