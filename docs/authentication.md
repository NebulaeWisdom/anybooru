# 认证与权限

## Danbooru 系站点

Danbooru 引擎的 API 使用 **HTTP Basic** 认证：用户名作为 Basic 用户名，API key 作为 Basic 密码。

凭据来自配置文件的 `sites` 段（见 [configuration.md](configuration.md)）：

```json
"sites": {
  "danbooru": {
    "url": "https://danbooru.donmai.us",
    "username": "your-username",
    "api_key": "your-api-key"
  }
}
```

规则很简单：

* `username` 与 `api_key` **任一非空**，每个请求就会带上 HTTP Basic 认证头（缺的那一项发空串）；
* **两项都为空**才是纯匿名请求；
* 不会静默降级：凭据填错时服务端返回 `401`，客户端不会退回匿名；
* 权限判断完全由服务端完成——本库不做客户端权限检查，也不会因为接口“需要登录”就提前报错。

匿名状态下可以正常调用公开只读接口；写接口会因为服务端返回 `401` / `403` 而失败，
错误里保留状态码与响应正文，见 [errors.md](errors.md)。

也可以在构造函数里显式覆盖配置文件的凭据：

```python
from pybooru import Danbooru

client = Danbooru('danbooru', username='your-username', api_key='your-api-key')
```

> Danbooru 的 API key 在站点个人设置页生成。请勿把填好的配置文件提交到仓库。

## Moebooru 系站点

Moebooru 引擎不用 HTTP Basic：登录信息随请求一起提交，字段是：

| 字段 | 值 |
| :--- | :--- |
| `login` | 用户名 |
| `password_hash` | `SHA1(hash_string.format(password))` 的十六进制摘要 |

`GET` / `HEAD` 请求把这两个字段放进**查询串**，其他动词放进**表单体**（客户端按方法自动选择）。
`hash_string` 是该站点 `help/api` 页面约定的加盐模板（含 `{0}` 占位符），`password` 是明文密码。
两者都来自配置文件的站点条目：

```json
"sites": {
  "konachan": {
    "url": "https://konachan.com",
    "username": "your-username",
    "password": "your-password",
    "hash_string": "So-I-Heard-You-Like-Mupkids-?--{0}--",
    "api_version": "1.13.0+update.3"
  }
}
```

`username` 与 `password` 都留空即可匿名读取；配置凭据后，读请求也带认证字段。
站点条目的 `hash_string` 为 `null` 时，登录需要显式提供模板。
服务端还接受 `username` + `api_key`（仅 `json` / `xml` / `zip` 格式）、会话 Cookie 与
`user[name]` + `user[password]` 明文；本库只实现 `password_hash` 一种。
逐方法权限及上游依据见 [Moebooru 契约审计附注](moebooru-contract-notes.md)。

## Serika 系站点

Serika 是独立第三类引擎。`Serika` 从 `sites.<站点>.api_key` 读取凭据，非空时发送
`Authorization: Bearer <key>`；默认配置样例的 `sites.serika.api_key` 为 **空字符串**，不发送认证头，
不制造占位 key。URL、代理、超时仍来自同一份 `pybooru.json`。

| 契约面 | 认证与交付边界 |
| :--- | :--- |
| 官方 v1：`api_index` / `stats` / `user_list` / `random_image` | 控制器允许匿名，示例只走这些公开方法 |
| 官方 v1：其他 12 个方法 | API key + 对应权限；具体权限见契约审计附注 |
| 站内非版本化 `internal_*` | 前端自用私有契约，只封装匿名公开读取；不实现浏览器 cookie 登录 |
| 站内评论/投票/收藏/上传/管理/账号写操作 | 依赖 Serika Accounts 会话或属于写路径，不在本轮能力范围；API key 不是会话 token |

客户端不预判权限、不自动换成站内接口、不在认证失败后退回匿名。服务端按 API key 限流。
当前 v1 的缺 key、缺权限、超限都返回 `code: UNAUTHORIZED`，HTTP 分别为 `401` / `403` / `429`；
请结合 `PybooruHTTPError.http_code`、`.data['code']` 与 `.body` 判断原因。
逐条权限、限流实现和官方说明差异见 [Serika 契约审计附注](serika-contract-notes.md)，
可调用能力见 [Serika 能力入口](serika-capabilities.md)。

## e621ng 系站点

e621ng 是 e621.net 与 e926.net 共用的 Rails 引擎，认证形态与 Danbooru 相同（HTTP Basic），
但属于另一套引擎：Basic 用户名是登录名，密码是 **API key**。

| 字段 | 值 |
| :--- | :--- |
| Basic 用户名 | `sites.<站点>.username` |
| Basic 密码 | `sites.<站点>.api_key` |

```json
"sites": {
  "e621": { "url": "https://e621.net", "username": "your-username", "api_key": "your-api-key" },
  "e926": { "url": "https://e926.net", "username": "", "api_key": "" }
}
```

规则：

* `username` 与 `api_key` **任一非空**，每个请求就带上 Basic 头（缺的那项发空串）；两项都为空才是匿名请求；
* 上游把 Basic 凭据按第一个 `:` 切出 `login` 与 `api_key` 再校验；
* 客户端**只走 Basic 头**：上游另外接受 `login` + `api_key` 请求参数，那条路径额外要求同源请求才能跳过
  CSRF，本库不使用；
* 权限判断完全由服务端完成，客户端不预判、不在认证失败后退回匿名。

本客户端的 16 个常规只读方法允许匿名进入；`related_tag` 与 `related_tag_bulk` 在上游控制器级是
`member_only`，匿名请求以 `403` 失败，且不会因此降级到别的端点。两个方法的成员成功响应
仅源码对齐、未实测；`related_tag` 的匿名拒绝已记录在[验证记录](verification.md)。

写请求：e621ng 面**没有原生写方法**。写路由的身份要求由各自控制器决定，不能概括为全部必须登录
（例如注册只允许未登录用户）。启用 `api_check` 的控制器才对已登录的非 `GET` / `HEAD` 请求做令牌桶
限流（超限回 `429`，响应头带 `X-Api-Limit`）；用户控制器显式跳过该检查。这些分支仅源码对齐、未实测，
出处见附注的[写动作边界](e621-contract-notes.md#sec-exclusions)与[限流错误](e621-contract-notes.md#sec-errors)。需要时用通用 `request()` 显式指定方法与路径，
本库不做自动重试、不替调用者补参数。

`safe_mode` 由服务端决定（请求参数 `safe_mode`、账号设置或站点自己的部署配置），上游仓库默认值是关闭。
本库不替站点补 `rating` 过滤，e926 那类安全内容站点的实际可见范围以该站配置为准。

## 边界与未实测

已提供的需要登录的写方法只有源码对齐，没有线上实测。Serika 用户没有且不申请 API key，
12 个需 key 方法的成功响应也未实测；匿名公开方法与部分站内读取已有真实执行。
Moebooru 的 90 个原生方法按上游 HEAD `206455e1` 对齐，e621ng 的 18 个原生只读方法按上游 HEAD
`7a9c98851` 对齐，两者的匿名执行范围见[验证记录](verification.md)。源码对齐不保证具体站点授予权限，
目标站点的权限模型为准。

## 相关文档

* [configuration.md](configuration.md)：凭据、代理、超时的配置位置
* [errors.md](errors.md)：`401` / `403` 等状态码与异常
* [pagination.md](pagination.md)：分页参数
