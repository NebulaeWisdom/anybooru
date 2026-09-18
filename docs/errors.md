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

## 不重试

本库不自动重试，也不做指数退避：

* `429` 与 `5xx` 由调用者自己决定等待多久、重试几次；
* Danbooru 在被限流的请求上会返回 `X-Rate-Limit` 响应头（JSON，含 `action`、`rate`、`burst`、`limits`
  等字段），通过 `AnybooruHTTPError.response.headers` 读取。

## 边界与未实测

已执行的 JSON、HTML、空正文和网络异常场景见[验证记录](verification.md)。写类重定向只有源码依据，
没有线上实测；最终 2xx 或 JSON 不等于资源已修改，也不要因最终解析失败而盲目重试写操作。

## 相关文档

* [danbooru.md](danbooru.md)：`request()` 的返回值约定
* [authentication.md](authentication.md)：`401` / `403` 的认证背景
* [pagination.md](pagination.md)：`page` 参数与 `410`
