# 错误处理

## 异常层次

```
PybooruError
├── PybooruHTTPError     HTTP 状态码不是 2xx
└── PybooruAPIError      状态码是 2xx，但响应体不是合法 JSON
```

网络层错误（连不上、超时、TLS 失败等）**不包装**，直接抛出 requests 自己的异常
（`requests.ConnectionError`、`requests.Timeout` 等）。

## `PybooruHTTPError`

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

用法：

```python
from pybooru import Danbooru, PybooruHTTPError

client = Danbooru('danbooru')
try:
    client.post_show(0)
except PybooruHTTPError as error:
    print(error.http_code)                  # 404
    print(error.url)                        # https://danbooru.donmai.us/posts/0.json
    if error.data:                          # 站点返回的 JSON 错误体
        print(error.data['message'])
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

## `PybooruAPIError`

状态码是 2xx，但响应体无法按 JSON 解析时抛出。常见于两种情况：

1. 请求被中间层（代理、登录页、站点维护页）换成了 HTML；
2. 调用了服务端会 `redirect_to` 的端点：客户端跟随重定向，**最终格式以目标端点为准**。
   因为客户端始终发送 `Accept: application/json`，重定向目标通常仍返回 JSON
   （`artist_show_or_new` 已实测如此）；只有当最终响应不是 JSON 时才抛本异常。
   写类重定向端点未实测，请用 `last_call['status_code']` / `last_call['url']` 判断结果，
   详见 [danbooru-api.md](danbooru-api.md)。

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `args[0]` | str | 出错信息，含 URL 与解码错误 |
| `response` | `requests.Response` \| None | 原始响应对象 |

## 状态码

本库不对状态码做任何预判或翻译：服务端返回什么就抛什么。下面是两个引擎实际会返回的状态码，
可用作排查参考。

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
| `501` | 功能不可用：例如站点未配置 archive 服务时的 `post_versions` / `pool_versions`，未配置 IQDB 时的以图搜图 |
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
  等字段），通过 `PybooruHTTPError.response.headers` 读取。

## 相关文档

* [danbooru.md](danbooru.md)：`request()` 的返回值约定
* [authentication.md](authentication.md)：`401` / `403` 的认证背景
* [pagination.md](pagination.md)：`page` 参数与 `410`
