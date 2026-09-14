# 认证与权限

## Danbooru 系站点

Danbooru 引擎的 API 使用 **HTTP Basic** 认证：用户名作为 Basic 用户名，API key 作为 Basic 密码。

凭据来自根配置文件的 `sites` 段（见 [configuration.md](configuration.md)）：

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
两者都来自根配置文件的站点条目：

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

只读接口按匿名 GET 发出，不需要上述字段；站点条目的 `hash_string` 为 `null` 时要登录必须显式传入。
服务端还接受 `username` + `api_key` 查询参数（该身份受 `limit_api` 限制，只有 `json` / `xml` / `zip`
格式被放行）、会话 Cookie 与 `user[name]` + `user[password]` 明文，本库只实现 `password_hash` 一种。

> Moebooru 面的端点已按上游 `moebooru/` HEAD `206455e1` 的路由与控制器对齐（90 个原生方法）；
> 匿名只读端点的执行记录见 [verification.md](verification.md)，需要登录的写接口**未做线上实测**，
> 详见 [moebooru.md](moebooru.md) 与 [moebooru-api.md](moebooru-api.md) 的认证与权限一节。

## 写接口的状态

标注为“需要登录”的写接口（创建评论、投票、上传、编辑 wiki 等）都按其上游引擎控制器的源码实现对齐，
**均未经线上实测**：本地没有可用账号，也没有 API key，因此这些接口只保证“按源码契约把请求发对”，
不保证在某个具体站点上一定有权限。需要提权或站点专用行为的接口，请以目标站点的权限模型为准。

## 相关文档

* [configuration.md](configuration.md)：凭据、代理、超时的配置位置
* [errors.md](errors.md)：`401` / `403` 等状态码与异常
* [pagination.md](pagination.md)：分页参数
