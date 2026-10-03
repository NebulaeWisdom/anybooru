# Wallhaven：我要做什么，用哪个方法？

Wallhaven（站点根 `https://wallhaven.cc`）自带 **API v1**，官方页面是 <https://wallhaven.cc/help/api>，路由都在 `api/v1/` 下。本库按该页面实现 **7 个原生方法，全部是只读 `GET`**：

* `wallpaper_search()`、`wallpaper_show()` —— 壁纸搜索与详情
* `tag_show()` —— 标签
* `user_settings()`、`collection_list()`、`user_collections()`、`collection_wallpapers()` —— 账号设置与集合

**为什么算新家族**：判据是契约而不是站名。列表返回 `{"data": [...], "meta": {...}}`、详情返回 `{"data": {...}}`、账号 key 走 `apikey` 查询值（官方页面 `#auth` 还允许 `X-API-Key` 头）、每页固定 24 条、分类与纯度是三位 `0`/`1` 掩码——这些跟现有十三个家族（Danbooru / Moebooru / Serika / e621ng / Zerochan / Gelbooru / Gelbooru02 / Shuushuu / Sakuria / Anime-Pictures / Cosine / Nhentai / ArtStation）的契约都不同。官方页面锚点：`#wallpapers`、`#search`、`#tags`、`#user-settings`（“User Collections”一节复用了这个锚点）、`#limits`、`#auth`。

**相似与用户上传不是方法**：官方 `#search` 给出的相似壁纸写法是 `q='like:<壁纸编号>'`，用户上传写法是 `q='@<用户名>'`，两者都走 `wallpaper_search()`；候选 URL `/api/v1/w/<编号>/similar`、`/api/v1/user` 与 `/api/v1/user/<用户名>` 本轮实测都是 `404 {"error": "Not Found"}`，本类不替它们虚构方法。

**证据范围**：本轮匿名只读直接 HTTP 请求覆盖了 7 条路由（壁纸搜索、壁纸详情、标签详情、设置、集合列表、某用户公开集合、集合里的壁纸）与主要的搜索参数、分页、错误路径；每个路由的真实 URL、状态码与响应摘要见[验证记录](verification.md#wallhaven匿名只读实测2026-10-03)。原生 Python 方法与随仓库脚本的实际执行范围同样以那份记录为准；**方法存在不等于成功路径测过**，带 key 的成功响应一轮都没有样本。

本页只做「目的 → 方法」对照与 7 方法一行索引。构造、认证、`request()`、返回值与错误语义在[客户端用法](wallhaven.md)；每个方法的完整参数、取值、真实 URL 与逐字段返回在[方法参考](wallhaven-api.md)；依据与排除项在[契约附注](wallhaven-contract-notes.md)。

## 按目的找调用

`client` 由 `Wallhaven('wallhaven')` 创建；下表调用里的编号、用户名、查询串都是可直接运行的字面值（`apikey` 除外，见客户端用法）。

| 我要做什么 | 调用 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| 浏览最新壁纸 / 翻页 | `client.wallpaper_search(page=1)` / `client.wallpaper_search(page=2)` | 页码（从 1 起，每页 24 条）→ `{"data": [壁纸摘要], "meta": {…}}`；翻页自己把 `page` 加一，客户端不翻页、不合并 |
| 关键词、过滤、排序搜索 | `client.wallpaper_search(q='nature', categories='100', purity='100', atleast='1920x1080')` | 搜索串与过滤键 → 列表信封。12 个查询键的取值与默认值见[方法参考](wallhaven-api.md) |
| 榜单 / 按种子随机 | `client.wallpaper_search(sorting='toplist', topRange='1w')` / `client.wallpaper_search(sorting='random', seed='abc123')` | 排序名、榜单窗口、6 位种子 → 列表信封；随机的 `meta.seed` 以实际返回为准 |
| 找相似壁纸 | `client.wallpaper_search(q='like:pom5lj')` | 壁纸编号写进 `q`——**官方 `#search` 给出的方式**；候选 `/w/<编号>/similar` 实测 `404`。本轮该查询被 `403` HTML 质询挡下，没有成功样本 |
| 列某个用户的上传 | `client.wallpaper_search(q='@LewisMweir13')` | 用户名写进 `q`——**官方 `#search` 给出的方式**；候选 `/user`、`/user/<用户名>` 实测 `404` |
| 精确标签搜索 | `client.wallpaper_search(q='id:1')` | 标签编号 → 列表信封，`meta.query` 变成对象 `{"id": 1, "tag": "anime"}`。官方页面写它 **"can not be combined"**：不能和别的 `q` 表达式拼在一起；`purity` / `categories` 这类独立查询参数不受此限 |
| 取一张壁纸的详情 | `client.wallpaper_show('pom5lj')` | 六位壁纸编号 → `{"data": {…}}`：壁纸摘要的全部字段，**外加** `uploader` 与 `tags` |
| 读一个标签 | `client.tag_show(1)` | 数字标签编号（`1` 是 `anime`）→ `{"data": {…}}` |
| 读自己的账号设置（**需 key**） | `client.user_settings()` | 无参数 → `{"data": {…}}`（缩略图尺寸、每页条数、纯度、分类等）。匿名或 key 无效是 `401 {"error": "Unauthorized"}` |
| 列自己的集合，含私有（**需 key**） | `client.collection_list()` | 无参数 → `{"data": [{id, label, views, public, count}]}`。匿名是 `404 {"error": "Nothing here"}`，**不是 401** |
| 列某个用户的公开集合 | `client.user_collections('ThorRagnarok')` | 用户名 → `{"data": [{id, label, views, public, count}]}`；空 `data` 是正常成功。私有集合只有本人带 key 能看 |
| 读一个集合里的壁纸 | `client.collection_wallpapers('ThorRagnarok', 274175, purity='100', page=1)` | 用户名 + 数字集合编号 → `{"data": [...], "meta": {current_page, last_page, per_page, total}}`；**这个 `meta` 没有 `query` / `seed`**。官方 `#user-settings` 说只有 `purity` 一个过滤参数可用；私有集合需 key。不存在的编号是 `404 {"error": "Nothing here"}` |
| 预期错误路径 | `client.wallpaper_show('000000')` → `404`；`client.user_settings()` 匿名 → `401`；`client.collection_list()` 匿名 → `404`；`client.wallpaper_search(page=1000000)` → `400 {"error": "Bad Request"}` | 都抛 `AnybooruHTTPError`，读 `error.http_code` / `error.data` / `error.body` |
| 换路径、换动词或加请求头 | `client.request('GET', 'api/v1/settings', headers={'X-API-Key': apikey})` | 动词 + 站点相对路径 + `params` / `headers` → 同一条通路。前导 `/` 去掉，`X-API-Key` 走 `headers` |

分页、随机种子、空 `data` 与短页的坑见[客户端用法](wallhaven.md#翻页随机种子与常见坑)；两者 `meta` 的键不同，别照抄搜索的分页解析。

## 完整方法索引：7 个 `GET`

每个方法一行；参数范围、缺省行为与逐字段返回只放在[方法参考](wallhaven-api.md)。路径都接在站点根 `https://wallhaven.cc` 后面，都在 `api/v1/` 下。带「**需 key**」的行需要你自己的账号 key；其成功路径一轮都没有样本。

### 壁纸（2 个 `GET`，匿名可读）

* `wallpaper_search(**params)` → `GET api/v1/search`，返回 `{"data": [...], "meta": {...}}`；`params` 是站点自己的 12 个查询键。
* `wallpaper_show(wallpaper_id, **params)` → `GET api/v1/w/{wallpaper_id}`，返回 `{"data": {…}}`；`wallpaper_id` 是六位站点编号（如 `pom5lj`），逐段编码；详情比列表摘要多 `uploader` 与 `tags`。没有相似路由方法。

### 标签（1 个 `GET`，匿名可读）

* `tag_show(tag_id, **params)` → `GET api/v1/tag/{tag_id}`，返回 `{"data": {…}}`；`tag_id` 是数字编号（`1` 是 `anime`），逐段编码。

### 账号设置与集合（4 个 `GET`）

* `user_settings(**params)` → `GET api/v1/settings`，返回 `{"data": {…}}`；**需 key**，匿名 `401`。
* `collection_list(**params)` → `GET api/v1/collections`，返回 `{"data": [...]}`（没有 `meta`）；**需 key**，列出当前 key 所属账号的集合（含私有）；匿名 `404 {"error": "Nothing here"}`。
* `user_collections(username, **params)` → `GET api/v1/collections/{username}`，返回 `{"data": [...]}`；只列该用户的公开集合；`username` 逐段编码。
* `collection_wallpapers(username, collection_id, **params)` → `GET api/v1/collections/{username}/{collection_id}`，返回 `{"data": [...], "meta": {current_page, last_page, per_page, total}}`（**没有 `query` / `seed`**，条目没有 `uploader` / `tags`）；两个路径段逐段编码；本人带 key 可读私有集合。匿名有 `200` 样本，带 key 与私有集合未实测。

另有通用入口 `request(method, path, *, params=None, headers=None)`：动词、站点相对路径、查询与额外请求头由你给全。前导 `/` 去掉后拼站点根；`params` 按共享编码发送（`None` 丢弃、布尔小写、数组编成 `key[]=`）；`X-API-Key` 等头走 `headers`。API v1 的原生路由都是 `GET`，这个入口没有 `data` / `form` 正文参数。

## 本库不封装的能力

下面这些要么官方页面没有，要么不属于 API v1 的公开读取面。需要时用 `client.request(method, path, params=…, headers=…)` 自己发；本库不绕过任何访问控制。

| 类别 | 情况 | 为什么不封装 |
| :--- | :--- | :--- |
| 相似壁纸、用户资料 | 候选 `/api/v1/w/<编号>/similar`、`/api/v1/user`、`/api/v1/user/<用户名>` | 官方页面没有把它们列为路由，本轮实测都是 `404 {"error": "Not Found"}`。相似用 `q='like:<编号>'`、上传用 `q='@<用户名>'`，都走 `wallpaper_search()`；**不伪造路由** |
| 集合与设置的写入 | 改设置、改集合、收藏 | API v1 的 7 条路由都是只读 `GET`；本库无登录、无写方法、无 CSRF / Cookie 处理 |
| NSFW 解锁 | 匿名加 NSFW 纯度位 | 客户端不补纯度位、不改写 `purity`；没有 key 就拿不到 NSFW（匿名 `purity='001'` 本轮是 `200` + `total 0`），也不会绕过 `401` |
| 登录、注册、key 管理 | 账号页与设置页 | 只有网页；本库只接受你已有的 key |
| 反自动化质询与 HTML 页面 | Cloudflare 质询页、帮助页 | 本库不解析 HTML、不求解质询、不做失败回退 |
| 媒体下载 | `w.wallhaven.cc` / `th.wallhaven.cc` 上的图片 | `path` 与 `thumbs` 只是地址字符串，本库不下载、不改写 |
| OpenAPI / 服务端源码 | — | 本轮没有取得；公开结论只以官方页面与匿名响应为准，不编造 schema 或行号 |

## 边界与未实测

* **带 key 的成功路径没有样本**：`apikey` 查询值与 `X-API-Key` 头都只有官方 `#auth` 依据；`user_settings()`、`collection_list()`、私有集合与集合壁纸的带 key 响应未实测，无效 key 的形态也只有 `#limits` 的说明。
* **相似搜索没有成功样本**：本轮唯一的 `q='like:<编号>'` 被 `403` HTML 质询挡下，没有绕过或回退。
* **限流、随机种子、末页语义**：官方 `#limits` 写每分钟 45 次并回 `429`，本轮只观察到限流响应头，阈值未触发；官方 `#search` 说 `sorting='random'` 的 seed 可在页间传递以避免重复，本轮两次样本回报的 seed 不同，不能据此断定之后也会变，也不能当成去重保证；空 `data` 不是末页判据，`page=1000000` 才是 `400`。细节见[客户端用法](wallhaven.md#翻页随机种子与常见坑)。
* **搜索参数边界未穷举**：`colors` 的 29 个取值只测了一个，`topRange` 的七个窗口、`resolutions` / `ratios` 的上限、其它 `categories` / `purity` 组合、非法 `seed` 都没有样本。
* **媒体与许可**：所有图片主机零请求；匿名可读不等于可以使用，站点条款与版权归各自原始权利人。

更细的未实测清单见[客户端用法](wallhaven.md#边界与未实测)；逐条 URL、状态码与响应摘要见[验证记录](verification.md#wallhaven匿名只读实测2026-10-03)；依据出处与排除项见[契约附注](wallhaven-contract-notes.md)。

继续阅读：[客户端用法](wallhaven.md) · [方法参考](wallhaven-api.md) · [验证记录](verification.md#wallhaven匿名只读实测2026-10-03)。
