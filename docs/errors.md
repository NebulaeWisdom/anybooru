# 错误处理

## 异常层次

```
AnybooruError
├── AnybooruHTTPError     HTTP 状态码不是 2xx
└── AnybooruAPIError      状态码是 2xx，但响应体不是合法 JSON
```

网络层错误（连不上、超时、TLS 失败等）**不包装**，直接抛出 requests 自己的异常
（`requests.ConnectionError`、`requests.Timeout` 等）。

对着现象找异常：

| 你看到的情况 | 抛出的异常 | 从哪里读原因 |
| :--- | :--- | :--- |
| 服务端返回 `400` / `401` / `403` / `404` / `410` / `429` / `5xx` 等非 2xx | `AnybooruHTTPError` | `.http_code` 是状态码，`.url` 是实际请求地址，`.body` 是正文原文，`.data` 是正文按 JSON 解析的结果（不是 JSON 时是 `None`；Serika 的错误码在 `.data['code']`） |
| 连不上、DNS 失败、连接或读取超时、TLS 握手失败 | requests 的异常，不被本库包装 | 异常类型与消息（例如 `requests.Timeout`） |
| HTTP 是 2xx，但正文不是 JSON（被中间层换成 HTML 等） | `AnybooruAPIError` | `str(error)` 里含 URL 与解码错误，`.response` 是原始响应 |

## `AnybooruHTTPError`

HTTP 状态码不在 `200..299` 时抛出，保留完整响应：

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `http_code` | int | HTTP 状态码 |
| `url` | str | 出错请求的完整 URL（含查询串） |
| `response` | `requests.Response` | 原始响应对象，可读任意响应头与内容 |
| `body` | str | 响应正文原文 |
| `data` | object \| None | 把正文按 JSON 解析的结果；正文不是 JSON 时为 `None` |

`str(error)` 的形式是：

```
404 Not Found: {"success":false,"error":"...","message":"That record was not found."} - URL: https://danbooru.donmai.us/posts/0.json
```

用法（`post_show(0)` 请求的是不存在的帖子，所以必然走异常分支）：

```python
from anybooru import Danbooru, AnybooruHTTPError

with Danbooru('danbooru') as client:
    try:
        # GET https://danbooru.donmai.us/posts/0.json
        client.post_show(0)
    except AnybooruHTTPError as error:
        print(error.http_code)          # 404
        print(error.url)                # https://danbooru.donmai.us/posts/0.json
        print(error.body)               # 服务端返回的正文原文
        if error.data:                  # 正文能按 JSON 解析时才是字典，否则是 None
            print(error.data['message'])   # That record was not found.
```

Danbooru 引擎的 JSON 错误体形如：

```json
{
  "success": false,
  "error": "ActiveRecord::RecordNotFound",
  "message": "That record was not found.",
  "backtrace": null
}
```

（模板见上游 `app/views/static/error.json.erb`，正文结构由 `ApplicationController#render_error_page`
组装。）

## `AnybooruAPIError`

状态码是 2xx，但响应体无法按 JSON 解析时抛出。常见于两种情况：

1. 请求被中间层（代理、登录页、站点维护页）换成了 HTML；
2. 调用了服务端会 `redirect_to` 的端点：客户端跟随重定向，**最终格式以目标端点为准**。
   因为客户端始终发送 `Accept: application/json`，重定向目标通常仍返回 JSON
   （`artist_show_or_new` 已实测如此）；只有当最终响应不是 JSON 时才抛本异常。
   通过 `last_call['status_code']` / `last_call['url']` 可以观察最终响应；状态码本身不确认写入生效。
   重定向分支与权限依据见 [Danbooru 审计](danbooru-contract-notes.md)、[Moebooru 审计](moebooru-contract-notes.md)。

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `args[0]` | str | 出错信息，含 URL 与解码错误 |
| `response` | `requests.Response` \| None | 原始响应对象 |

## 状态码

本库不对状态码做任何预判或翻译：服务端返回什么就抛什么。下面保留 Danbooru 与 Moebooru 的速查；
Serika 的 HTTP/code 对照见 [Serika 契约审计附注](serika-contract-notes.md)，e621ng 的权限与错误边界见
[e621ng 契约审计附注](e621-contract-notes.md)。Zerochan 未实测非法参数、缺失条目或限流错误，
不能套用其他家族的状态码；其文档与响应依据见 [Zerochan 契约审计附注](zerochan-contract-notes.md)。
Sakuria 的错误码只有本轮试过的那几个样本（含 `426` 与「缺失 `/spotlight/{id}` 回 `503`」）列在下文，
不是全集，见 [Sakuria 契约审计附注](sakuria-contract-notes.md)。
Anime-Pictures 的错误码样本同样只覆盖本轮试过的路径（缺失帖子 `410`、缺失标签 / 用户 / 评论 `404`、
非法路径段的纯文本 `400`、需要身份的 `403`），且**帖子不存在用 `410` 而不是 `404`**，
见 [Anime-Pictures 契约审计附注](anime-pictures-contract-notes.md)。
Cosine 的错误样本同样只覆盖本轮试过的路径，三者不要互相套用；它的错误正文不统一：有的是纯文本、
`AnybooruHTTPError.data` 为 `None`，有的才是 JSON 对象，见下节。

### Danbooru 引擎

| 状态码 | 触发场景（上游 `ApplicationController#rescue_exception`） |
| :--- | :--- |
| `400` | 请求体不被该 HTTP 方法接受、请求格式非法 |
| `401` | 认证失败（会话/凭据无效、验证码服务异常） |
| `403` | 权限不足：Pundit 拒绝、用户权限不够、CSRF/跨域请求被拒 |
| `404` | 记录不存在 |
| `405` | 控制器捕获 `ActionController::RoutingError`；未匹配的路径还可能走静态 404 路由 |
| `406` | 该端点不支持请求的响应格式（例如对 HTML-only 动作请求 `.json`） |
| `410` | **分页错误**：页码超过账号上限（一般非数字文本可能被归一为第一页，不保证触发错误） |
| `422` | 查询非法：标签数量超过账号上限、搜索表达式错误、升级码无效 |
| `429` | 触发限流（`You're doing that too fast`） |
| `451` | 内容因下架请求被移除 |
| `500` | 服务端异常、数据库查询超时 |
| `501` | 功能不可用：例如站点未配置 archive 服务时的 `post_versions` / `pool_versions`；IQDB 未配置走空数组分支，区别见 [Danbooru 审计](danbooru-contract-notes.md#失败与能力依赖) |
| `503` | 数据库不可用 |

### Moebooru 引擎

Moebooru 用一组自定义状态码表达业务失败（上游 `ApplicationController`）：

| 状态码 | 含义 |
| :--- | :--- |
| `420` | Invalid Record：模型校验失败 |
| `421` | User Throttled：触发小时/每日限额 |
| `422` | Locked：目标资源被锁定 |
| `423` | Already Exists：资源已存在 |
| `424` | Invalid Parameters：参数非法 |

### Sakuria

本轮 54 次匿名 GET（各 1 次、不重试、不跟随跳转、不下载媒体）里，错误体都是 JSON，且**字段随路由不同**：
`error` 一定在，`code` / `field` / `feature` / `retryable` / `requiredDataContract` 只在对应路由出现。

| 状态码 | 本轮观察（样本，不是全集） |
| :--- | :--- |
| `400` | 参数或路径非法。筛选参数越界或取值不认识：`{"error":"筛选参数无效","code":"invalid_search_filter","field":"size"}`（`size=0`、`size=49`），`field` 换成 `page` / `sort` / `mode` 出现在 `page=0`、`sort=__invalid__`、`mode=text` 上；非数字 id：`{"error":"invalid id"}`（`/illust/abc`，没有 `code`）；在小说上请求插画筛选：`{"error":"小说不支持该作品筛选条件","code":"unsupported_filter_for_scope","field":"type"}`（`/search/novel?type=illust`） |
| `401` | 需要登录或更高等级。高级筛选：`{"error":"高级筛选需要 Sakuria+","code":"auth_required","feature":"advanced_search"}`（`/search/illust?type=illust`、`/search/novel?ai=exclude`）；补齐契约头后的 `/me/likes`：`{"error":"sakuria_session_required"}` |
| `403` | **本轮没有样本**，含义未实测 |
| `404` | 资源不存在：`/illust/0` 回 `{"error":"illust not found"}`（没有 `code`） |
| `426` | 数据契约版本不满足：`/me/likes` 不带 `x-sakuria-data-contract: 2` 时回 `{"error":"upgrade_required","requiredDataContract":2}` |
| `503` | 上游暂不可用：`/spotlight/0` 回 `{"error":"upstream temporarily unavailable","retryable":true}`，**不是 `404`** |

这些只是本轮试过的路由：`401` 的两种正文、`400` 的几种 `field`、`503` 的 `retryable`
都不会自动推广到别的端点，`403` 未实测。`200` 也不代表参数生效——`/search/illust?…&limit=__invalid__`
仍回 `200`（这只证 `limit` 这一个取值被忽略，**不能推广成「所有未知参数都被忽略」**）。
`/me/*` 的其余路由、登录后的状态码、限流与 `429` 都没有样本。

### Anime-Pictures

本轮 90 次匿名 GET（串行、每个请求只发一次、不重试、不跟随跳转、不下载媒体）里的错误样本。
站点 API 位于 `https://api.anime-pictures.net`，原生方法里的相对路径拼在 `/api/v3` 后，`'/pictures/…'` 这种前导 `/` 路径落在主机根：

| 状态码 | 本轮观察（样本，不是全集） |
| :--- | :--- |
| `400` | **非法路径段**：`GET /api/v3/posts/top` 回 `Content-Type: text/plain; charset=utf-8`，正文是 ``Invalid URL: Cannot parse `top` to a `i32` ``。这不是 JSON——`AnybooruHTTPError.data` 是 `None`，正文在 `.body` 里 |
| `400` | **帖子列表缺页码或页码非整数**：`GET /api/v3/posts` 与 `GET /api/v3/posts?page=abc` 都回 JSON，``{"errormsg":"Missing or invalid `page` parameter","success":false}``；`page` 是必填项 |
| `400` | **不认识的响应格式**：`GET /api/v3/posts?page=0&…&type=json` 回 `{"errormsg":"Only json_v3, json1, and xml response types are supported","success":false}`——这些其它格式本轮没有请求，客户端也不提供 |
| `403` | 需要身份：`GET /api/v3/posts/{id}/tags` 回 `{"errormsg":"You not have rights","success":false}`（`post_tags`）；`GET /pictures/get_image/{file_url}` 回 **`403` 空正文、没有 `Content-Type`**（`image_get`） |
| `404` | 标签 / 用户 / 评论不存在：正文分别是 `{"errormsg":"Tag not found","success":false}`、`{"errormsg":"User not found","success":false}`、`{"errormsg":"Have no comment","success":false}`。API 主机上不存在的路由也是 `404` 空正文（旧版 `/api/v2/comments`、`/pictures/view_posts/0?type=json` 与任意的 `/api/v3/not_a_route` 实测如此） |
| `410` | **帖子不存在**：`GET /api/v3/posts/{id}` 回 `{"errormsg":"Post not found","success":false}`。这一条与其它家族的 `404` 相反，是本家族最容易记混的状态码 |
| `500` | `GET /api/v3/posts?page=-1` 回 `{"errormsg":"Internal server error","success":false}`——负页码不是 `400` |

`401` 与 `429` 在本轮**都没有样本**（没有发过 POST，也没有触发限流）。候选输入称 `POST /api/v3/posts`
未登录回 `401`（`{"errormsg":"You have no rights","success":false}`），本轮没有执行，只能当候选。
站点也**没有观察到任何限流响应头**。

```python
from anybooru import AnimePictures, AnybooruHTTPError

with AnimePictures('anime_pictures') as client:
    try:
        client.post_show(999999999)          # 不存在的帖子：410，不是 404
    except AnybooruHTTPError as error:
        print(error.http_code)               # 410
        print(error.data['errormsg'])        # Post not found

    try:
        client.post_show('top')              # 路径段不是整数：400，正文不是 JSON
    except AnybooruHTTPError as error:
        print(error.http_code)               # 400
        print(error.data)                    # None：正文按 JSON 解析失败
        print(error.body)                    # Invalid URL: Cannot parse `top` to a `i32`

    try:
        client.posts_list()                  # 缺 page：400，但正文是 JSON
    except AnybooruHTTPError as error:
        print(error.data['errormsg'])        # Missing or invalid `page` parameter
```

同一条 `AnybooruHTTPError` 模型下，`.data` 只能对「正文是 JSON 的错误」用：Anime-Pictures 的正常错误体
（`410` / `404` / `403` / `400` 页码 / `400` 格式 / `500` 的 JSON 形态）都有 `errormsg` 与 `success`
两个字段，可以直接读；纯文本的 `400`（非法路径段）只能读 `.body`。逐条 URL 与正文见
[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)与
[Anime-Pictures 契约审计附注](anime-pictures-contract-notes.md)。

### Cosine

本轮匿名只读探测（两次串行批次，每个请求只发一次、不重试、不跟随跳转、不下载媒体）里的错误样本。
Cosine 的错误正文形状**不统一**：有的是站点自己的 JSON（例如 `{"error": "标签参数缺失"}`），有的是它自己的
其它文本，所以不要假定错误体一定有某个字段；`AnybooruHTTPError.data` 只在正文能按 JSON 解析时才是对象。

| 状态码 | 本轮观察（样本，不是全集） |
| :--- | :--- |
| `400` | **缺必填的查询参数**：`GET /api/tag` 完全不带 `tag` 回 `{"error": "标签参数缺失"}`；`GET /api/artist` 不带 `platform` 也是 `400` |
| `404` | **作品不存在**：`GET /api/artwork/999999999` 回 `404`；`GET /api/random?count=abc`（`count` 不是数字）同样回 `404`；`GET /api/artist` 的 `infoOnly='true'` 分支上查一个没有作品的画师也回 `404` |
| `500` | **路径段或参数非法**：`GET /api/artwork/abc`（路径段不是数字）是 `500` 而不是 `400`；`GET /api/list?page=0` 与 `page=-1` 都是 `500`；`GET /api/artist` 的 `authorid` 不能转成数字也是 `500`；`GET /api/search` 的 `limit=-1`、`offset=-5` 与 `sort=bogus` 都是 `500`（`sort` 收的是 Meilisearch 表达式，非法值由 Meilisearch 报错） |

对照样本：`/api/list` 翻到末页之后是 `200` 加空 `images`（不是 `404`）；`/api/tag` 查一个没有作品的标签、
`/api/search/suggestions` 只传一个字符的 `q` 也都是 `200` 加空数组 / 空列表——**空结果不是错误**，
本库不把它换成异常，也不据此判定“资源不存在”。未知取值同样不会在本地被拦下：`platform=unknown` 与
`sortBy=unknown` 都回了 `200`，由站点自己解释——所以“没报错”不等于“参数生效”。

```python
from anybooru import Cosine, AnybooruHTTPError

with Cosine('cosine') as client:
    try:
        client.artwork_show(999999999)          # 不存在的作品
    except AnybooruHTTPError as error:
        print(error.http_code)                  # 404
        print(error.body)                       # 站点自己的正文原文

    try:
        client.artwork_show('abc')              # 路径段不是数字
    except AnybooruHTTPError as error:
        print(error.http_code)                  # 500，不是 400
        print(error.url)                        # https://pic.cosine.ren/api/artwork/abc

    try:
        client.request('GET', 'api/tag')        # 完全不传 tag
    except AnybooruHTTPError as error:
        print(error.http_code, error.data['error'])   # 400 标签参数缺失
```

`response_format='xml'` 的 `feed()` 不在上表里：它要的是 RSS 原文，客户端直接把 `.text` 给你，
**不做 JSON 解析、不做格式嗅探**，所以正文不是 JSON 也不会变成 `AnybooruAPIError`；反过来，
JSON 路由拿到 2xx 却不是 JSON 时，仍按共享规则抛 `AnybooruAPIError`。
本轮带 `Origin` 的样本里**没有** `Access-Control-Allow-Origin`，也没有任何 `RateLimit-*` 响应头——
只能说本轮样本没有这些头，不能当成“站点没有配额”或“浏览器跨域一定可用”的保证。
客户端不做任何自动重试：`search_index_admin` 这类写入口更没有兜底或回滚，见[不重试](#不重试)。

## 不重试

本库不自动重试，也不做指数退避：

* `429` 与 `5xx` 由调用者自己决定等待多久、重试几次；
* Danbooru 在被限流的请求上会返回 `X-Rate-Limit` 响应头（JSON，含 `action`、`rate`、`burst`、`limits`
  等字段），通过 `AnybooruHTTPError.response.headers` 读取。

## 边界与未实测

已执行的 JSON、HTML、空正文和网络异常场景见[验证记录](verification.md)。写类重定向只有源码依据，
没有线上实测；最终 2xx 或 JSON 不等于资源已修改，也不要因最终解析失败而盲目重试写操作。
Sakuria 的错误路径本轮只跑过有界样本：探测的 54 次匿名 GET 里非 2xx 共 13 个（`400` 七个、`401` 三个、
`404` / `426` / `503` 各一），其余 41 个是 `200`；10 次上限的冒烟另含一次 `404` 与一次 `400`。
`403`、`429`、登录后的状态码、媒体与占位图分支都没有样本，上表不是全集。
Anime-Pictures 的错误路径同样只跑了有界样本：90 次匿名 GET 里非 2xx 共 14 个（`400` 四个、`403` 两个、
`404` 六个、`410` 与 `500` 各一），其余 76 个是 `200`；`401`、`429`、带 Cookie 的成功路径与媒体成功返回
都没有样本。异常字段本身与其它家族共用同一套，不受影响。逐条见
[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。
Cosine 的错误路径同样只跑了有界样本：本轮两次匿名串行探测只在缺失作品、参数非法与页码越界上取得
`400` / `404` / `500` 样本；两个 POST（`artwork_revalidate`、`search_index_admin`）从未调用，
`401` / `403` / `429` 都没有样本，未知参数是否被忽略也没有证据。逐条见
[验证记录](verification.md#cosine匿名只读实测2026-09-20)与[Cosine 契约审计附注](cosine-contract-notes.md)。

## 相关文档

* [danbooru.md](danbooru.md)：`request()` 的返回值约定
* [authentication.md](authentication.md)：`401` / `403` 的认证背景
* [pagination.md](pagination.md)：`page` 参数与 `410`
