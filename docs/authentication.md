# 认证与权限

## Danbooru 系站点

Danbooru 引擎的 API 使用 **HTTP Basic** 认证：用户名作为 Basic 用户名，API key 作为 Basic 密码。

凭据来自配置文件的 `sites` 段（见 [configuration.md](configuration.md)）：

```json
{
  "sites": {
    "danbooru": {
      "url": "https://danbooru.donmai.us",
      "username": "your-username",
      "api_key": "your-api-key"
    }
  }
}
```

规则很简单：

* `username` 与 `api_key` **任一非空**，每个请求就会带上 HTTP Basic 认证头（缺的那一项发空串）；
* **两项都为空**才是纯匿名请求；
* 不会静默降级：凭据填错时服务端返回 `401`，客户端不会退回匿名；
* 权限判断完全由服务端完成——本库不做客户端权限检查，也不会因为接口“需要登录”就提前报错。

匿名状态下可以正常调用公开只读接口，例如：

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:          # 配置里 username 与 api_key 都为空 = 匿名
    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=1
    posts = client.post_list(tags='rating:g', limit=1)
    print(posts[0]['id'], posts[0]['rating'], posts[0]['tag_string'])
```

写接口会因为服务端返回 `401` / `403` 而失败，错误里保留状态码与响应正文，见 [errors.md](errors.md)。

也可以在构造函数里显式覆盖配置文件的凭据。下面这段是**写操作**（发表评论），需要账号与 API key，
本仓库不带凭据、**未执行、未实测**，只示范参数怎么传：

```python
from anybooru import Danbooru

# 未执行：凭据是占位符；真实调用会 POST https://danbooru.donmai.us/comments.json
with Danbooru('danbooru', username='your-username', api_key='your-api-key') as client:
    comment = client.comment_create(post_id=1, body='示例评论')
    print(comment['id'], comment['post_id'])   # 返回新建评论对象里的这两个字段
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
{
  "sites": {
    "konachan": {
      "url": "https://konachan.com",
      "username": "your-username",
      "password": "your-password",
      "hash_string": "So-I-Heard-You-Like-Mupkids-?--{0}--",
      "api_version": "1.13.0+update.3"
    }
  }
}
```

`username` 与 `password` 都留空即可匿名读取；配置凭据后，读请求也带认证字段。
站点条目的 `hash_string` 为 `null` 时，登录需要显式提供模板。
服务端还接受 `username` + `api_key`（仅 `json` / `xml` / `zip` 格式）、会话 Cookie 与
`user[name]` + `user[password]` 明文；本库只实现 `password_hash` 一种。
逐方法权限及上游依据见 [Moebooru 契约审计附注](moebooru-contract-notes.md)。

## Serika 系站点

Serika 是独立引擎。`Serika` 从 `sites.<站点>.api_key` 读取凭据，非空时发送
`Authorization: Bearer <key>`；默认配置样例的 `sites.serika.api_key` 为 **空字符串**，不发送认证头，
不制造占位 key。URL、代理、超时仍来自同一份 `anybooru.json`。

| API 面 | 认证与可用范围 |
| :--- | :--- |
| 官方 `/api/v1`：`api_index` / `stats` / `user_list` / `random_image` | 服务端允许匿名访问，示例只走这四个 |
| 官方 `/api/v1` 其余 12 个方法 | 需要 API key 加对应权限，清单见附注 |
| 站内 `/api/*`（方法名带 `internal_` 前缀） | 前端自用、没有版本保证的接口，本库只封匿名可读的那些；不实现浏览器 cookie 登录 |
| 站内评论/投票/收藏/上传/管理/账号写操作 | 依赖 Serika Accounts 的账号会话或属于写路径，本库不提供；API key 不能当会话用 |

客户端不预判权限、不自动换成站内接口、不在认证失败后退回匿名。服务端按 API key 限流。
当前 v1 的缺 key、缺权限、超限都返回 `code: UNAUTHORIZED`，HTTP 分别为 `401` / `403` / `429`；
请结合 `AnybooruHTTPError.http_code`、`.data['code']` 与 `.body` 判断原因。
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
{
  "sites": {
    "e621": { "url": "https://e621.net", "username": "your-username", "api_key": "your-api-key" },
    "e926": { "url": "https://e926.net", "username": "", "api_key": "" }
  }
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

## Zerochan：User-Agent 身份标识

`Zerochan` 只提供 GET JSON 读取，不实现 Basic、API key 或账号/cookie 登录。
站点配置只有 `url`；身份标识来自 `request.user_agent`，也可用构造参数 `user_agent` 显式覆盖。
Zerochan API 文档要求这个头同时包含**项目名和使用者自己的 Zerochan 用户名**，写成配置就是：

```json
{
  "request": {
    "timeout": 30,
    "proxies": {},
    "user_agent": "MyProject - MyZerochanUsername"
  }
}
```

包内默认 `Anybooru/0.1.0.dev1` 只有项目标识，**不满足完整要求**；请在自己的配置中补入用户名，
或对单个客户端覆盖：`Zerochan('zerochan', user_agent='MyProject - MyZerochanUsername')`。
这不是登录认证，也不意味着获得额外权限；匿名请求可能成功，仍有被封禁的风险。
没有用户名时库不会编造一个，也不会自动申请账号。来源和实测边界见
[Zerochan 契约审计附注](zerochan-contract-notes.md)与[验证记录](verification.md#zerochan匿名只读实测2026-09-18)。

## Gelbooru 系站点

Gelbooru 用该站自己的 `index.php` 接口，凭据形态与前面几家都不同：

| 字段 | 值 |
| :--- | :--- |
| `api_key` | `sites.<站点>.api_key` |
| `user_id` | `sites.<站点>.user_id`（该站账号的编号） |

```json
{
  "sites": {
    "gelbooru": {
      "url": "https://gelbooru.com",
      "api_key": "your-api-key",
      "user_id": "123456"
    }
  }
}
```

规则：

* 这两项**只加在 dapi 请求上**（`page=dapi`，也就是 `post_list` / `post_deleted` / `tag_list` /
  `user_list` / `comment_list`），其他请求不带；留空就是匿名；
* **匿名只能用 `autocomplete`**（已用匿名请求实测 `200`，返回建议数组；`limit` 不决定条数）：站点的 dapi
  需要账号，5 个方法已逐个实测匿名401、空正文；**账号成功路径仍未实测**；
* 客户端不预判权限、不做参数校验、不拆返回的 JSON，服务端给什么就返回什么。

来源层级（官方 wiki/帮助页与页面脚本，外加真实匿名响应）与未实测项见
[Gelbooru 契约审计附注](gelbooru-contract-notes.md)；可调用能力见
[Gelbooru 能力入口](gelbooru-capabilities.md)。

## Gelbooru02（TBIB）：没有凭据

`Gelbooru02` 的构造参数没有 `username/api_key/user_id`，不提供内置认证功能；
站点条目只有 `url`。本轮帖子 JSON/XML、标签与空评论、分页请求
均为匿名，没有发送凭据。站点账号功能是否有其它认证方式未实测。

它和 `gelbooru.com` 那套需要账号的 dapi 凭据不是一回事：不要把
`Gelbooru('gelbooru', api_key=…, user_id=…)` 的写法搬过来。见 [Gelbooru02 用法](gelbooru02.md) 与
[Gelbooru02 契约审计附注](gelbooru02-contract-notes.md)。

## Shuushuu：默认匿名，显式登录才建立会话

公开图片、标签、评论、用户资料等读取不需要登录。`Shuushuu('shuushuu')` 只创建客户端，不发送任何登录请求。
`sites.shuushuu` 的 `username/password/access_token` 默认都为 `""`；即使填了用户名和密码也不会自动登录。

| 主动选择 | 客户端行为 |
| :--- | :--- |
| 留空凭据 | 普通匿名读取，无认证头 |
| 提供非空 `access_token` | 请求发送 `Authorization: Bearer <token>`，到期不自动续期 |
| 显式 `auth_login(username, password)` | JSON body 发到 `/api/v1/auth/login`，保存响应 token 与同会话 Cookie |
| 显式 `auth_refresh()` | 使用会话的 `refresh_token` Cookie，保存新的 access token；不在 JSON 里传 refresh token |
| 显式 `auth_logout()` / `auth_logout_all()` | 请求服务器吊销当前 / 所有 refresh token；成功后清空客户端 token 与 Cookie |

OpenAPI 描述 access token 有效 30 分钟，refresh token 30 天；服务端登出不立即撤销已经签发的 access token。
登录、个人数据和写权限不是公共读取的前置步骤；`user_ratings` 只允许本人或具有 `USER_EDIT_PROFILE` 的版主，
不能把“GET”当成匿名权限保证。参数与字面调用见 [Shuushuu 方法参考](shuushuu-api.md)。

## Sakuria：`access_token` 与需要登录的 `/me/*`

`Sakuria` 只有一种凭据：站点条目的 `access_token`（默认 `""`）。非空时给每个请求加
`Authorization: Bearer <token>`；留空即匿名，不发送任何认证头。没有 `username` / `password` / `api_key` /
`user_id` 字段，构造签名里也没有用户名。

```python
from anybooru import Sakuria

with Sakuria('sakuria', access_token='') as client:   # 显式空串：即使配置里填了 token 也不发认证头
    # GET https://sakuria-api.syarolia.com/stats
    print(client.stats())                             # 匿名公开路由，原样返回 JSON

with Sakuria('sakuria') as client:                    # 不传 access_token：读取 sites.sakuria.access_token
    # 构造不发请求；包内 token 为空，last_call 此时也是空字典。
    print(client.last_call)
```

规则：

* `access_token=''`（显式空串）表示本次客户端匿名，**不读取**配置里的 token；`None`（或不传）才读配置；
* 非空才加 `Authorization: Bearer <token>`；库不做本地权限判断，也不会在 `401` 后退回匿名；
* **没有**登录、注册、换取或刷新 token 的方法；这些路由的位置与可达性本轮未复核。
  token 由使用者自己准备，库不代替获取或续期，也不索要账号密码；
* `me*` 系列 17 个方法（`me` / `me_capabilities` / `me_bookmarks` / `me_likes` / `me_following` /
  `me_notifications` / `me_history` / `me_settings` / `me_illusts` / `me_novels` / `me_series` / `me_credits` /
  `me_plus` / `me_subscription` / `me_favorites` / `me_search_history` / `me_recommend`）**都需要登录**：
  没有 token 时由服务端拒绝，返回结构**未实测、未知**——库只拼路由、原样返回 JSON，不拆信封。
  其中只有 `/me/likes` 本轮被请求过（匿名先 426，显式带契约头后 401），其余 16 个连拒绝形态都没有样本。

本轮实测：`/me/likes` 不带 `x-sakuria-data-contract: 2` 时回 `426`（正文 `{"error":"upgrade_required","requiredDataContract":2}`），
显式补上该头后变成 `401`（正文 `{"error":"sakuria_session_required"}`）——服务端先看数据契约版本，再查登录。
本客户端**不隐式发送**这个头：需要时用通用入口显式传，例如
`client.request('GET', '/me/likes', headers={'x-sakuria-data-contract': '2'})`；`headers` 是 `request()` 的
关键字参数，原生方法不带隐式头。逐条依据与未实测边界见
[Sakuria 契约审计附注](sakuria-contract-notes.md)。

## 边界与未实测

已提供的需要登录的写方法只有源码对齐，没有线上实测。Serika 用户没有且不申请 API key，
12 个需 key 方法的成功响应也未实测；匿名公开方法与部分站内读取已有真实执行。
Moebooru 的 90 个原生方法按上游 HEAD `206455e1` 对齐，e621ng 的 18 个原生只读方法按上游 HEAD
`7a9c98851` 对齐，两者的匿名执行范围见[验证记录](verification.md)。Gelbooru 的 5 个 dapi 方法需要
该站账号，已实测匿名拒绝为401、空正文，账号成功路径仍只有站点文档依据。源码或文档对齐不保证站点授予权限。
Shuushuu 的五个认证方法、`user_ratings` 以及全部账号写操作未调用、未实测；公开读方法也只执行了验证记录列出的子集。
Gelbooru02（TBIB）的账号路径未调用；新客户端默认匿名，不提供登录或内置凭据字段。
其 `post_deleted` 方法没有单独实跑，直接请求对应删除流路由得到 `500`，没有成功样本。
Sakuria 的 17 个 `me*` 方法按账号读取封装；本轮只请求过 `/me/likes`（匿名无契约头为 426，
带 `x-sakuria-data-contract: 2` 后为 401 `sakuria_session_required`），17 个成功返回结构一律未知；
带 token 的路径从未执行，也没有任何登录、换取或刷新 token 的方法可用。匿名只读侧的执行（54 次串行探测、
10 次上限的冒烟与两个示例）也都是有界样本，不泛化到 44 个方法；依据是本仓库最弱的一档（无官方页面 / OpenAPI / 源码）。逐条见
[验证记录](verification.md#sakuria匿名只读实测2026-09-19)与
[Sakuria 契约审计附注](sakuria-contract-notes.md)。

## 相关文档

* [configuration.md](configuration.md)：凭据、代理、超时的配置位置
* [errors.md](errors.md)：`401` / `403` 等状态码与异常
* [pagination.md](pagination.md)：分页参数
