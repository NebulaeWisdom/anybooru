# Anybooru 文档

Anybooru 是访问 Danbooru、Moebooru、Serika 与 e621ng 四类引擎图站 API 的 Python 客户端。先选与你的站点匹配的客户端，再按任务查方法；本库不自动识别引擎。

## 先选阅读层

| 你要解决的问题 | 看哪类文档 | 会读到什么 |
| :--- | :--- | :--- |
| 第一次调用，怎么配、怎么跑？ | **客户端用法** `<family>.md` | 三行上手、真实输出、构造参数、认证、返回值 |
| 已知道任务，具体调哪个方法？ | **方法参考** `<family>-api.md` | 按资源分组的常用示例；长尾方法的 Python 签名、用途与返回要点 |
| 要维护客户端、核对上游契约？ | **契约审计附注** `<family>-contract-notes.md` | 上游文件与行号、权限分支、实现细节、排除项、说明矛盾 |
| 想确认哪些场景真的跑过？ | **验证记录** [verification.md](verification.md) | 命令、URL、状态码、真实摘要与证据指针；历史与未实测分列 |

不知道有什么能力？先看各家族的“能力入口”，用“我要做什么 → 方法”表定位资源，再进入方法参考。

## 按家族选文档

| 家族 | 客户端用法 | 方法参考 | 能力入口与完整索引 | 契约审计附注 |
| :--- | :--- | :--- | :--- | :--- |
| Danbooru | [三行上手](danbooru.md) | [常用示例与长尾方法](danbooru-api.md) | [按任务找方法](danbooru-capabilities.md) | [上游契约与依据](danbooru-contract-notes.md) |
| Moebooru | [三行上手](moebooru.md) | [常用示例与长尾方法](moebooru-api.md) | [按任务找方法](moebooru-capabilities.md) | [上游契约与依据](moebooru-contract-notes.md) |
| Serika | [三行上手](serika.md) | [官方与站内方法](serika-api.md) | [按任务找方法](serika-capabilities.md) | [版本、权限与说明差异](serika-contract-notes.md) |
| e621ng（e621.net / e926.net） | [三行上手](e621.md) | [常用示例与长尾方法](e621-api.md) | [按任务找方法](e621-capabilities.md) | [上游契约与依据](e621-contract-notes.md) |

Danbooru / Moebooru / e621ng 是 Rails 引擎；Serika 是独立的 Next.js 引擎，提供官方 `/api/v1` 与前端自用、
没有公共兼容保证的 `/api/*`。不能根据“Danbooru-style”血缘名称选客户端：e621ng 与 Danbooru 同样是复数
`posts` 路径、同样用 HTTP Basic，但响应契约不同。判断方法见
[配置：怎么选类](configuration.md#怎么判断一个站点该用哪个类)。

## 四个家族共用的用法

| 文档 | 什么时候看 |
| :--- | :--- |
| [安装](installation.md) | 环境要求、源码安装与目录结构 |
| [配置](configuration.md) | 默认配置来源、`config_file` 覆盖、站点、代理、超时和示例参数 |
| [认证](authentication.md) | Danbooru Basic、Moebooru password_hash、Serika Bearer、e621ng Basic |
| [分页](pagination.md) | page/limit 透传、编号页与 Danbooru/e621ng 游标 |
| [错误处理](errors.md) | HTTP 错误字段、网络异常、状态码与重定向 |
| [迁移](migration.md) | 从 4.x 到 Anybooru 的方法与参数替换 |

## 客户端共同约定

1. **显式配置**：默认读随包安装的 `anybooru/anybooru.json`，`config_file` 指向其他文件时读那份；没有
   环境变量注入、没有工作目录搜索、没有内置站点后备。站点键指向配置里的 `sites` 条目。
2. **通用入口与原生方法**：四个客户端都有 `request()`；原生方法是其薄封装。服务端决定权限与参数含义，客户端不猜能力、不拦截未知搜索字段。
3. **保留原响应语义**：不自动翻页、重试或降级；HTTP 错误保留状态和正文。Serika 官方信封拆为返回数据与 `last_call['meta']`，站内 JSON 原样返回，图片方法返回 bytes；e621ng 的信封拆封按上游请求分支决定（不同分支拆 `posts` / `post` 或不拆），不做形状猜测。
4. **参数跟随引擎**：Rails 查询嵌套编码为 `a[b]` / `a[]`，布尔为 `true` / `false`，None 不发送；Danbooru 无文件写请求用 JSON，Moebooru 恒用表单。Serika 标签/评级为逗号分隔字符串，批量查询用 JSON，上传用 multipart。e621ng 与 Danbooru 同为 Basic 认证，但评级词表与帖子负载不同，不能共用过滤条件。

## 边界与未实测

- 四家族契约分别依据各自固定版本的上游源码，出处见上表的契约审计附注，不是对每个下游站点的保证。
- Danbooru 早期匿名验证为 12 次成功与 3 次预期错误；Moebooru 已重写 90 个原生方法并执行指定匿名读取；Serika 已执行官方公开入口与部分站内匿名读取；e621ng 提供 18 个原生只读方法，其示例执行记录见[验证记录](verification.md)。不把方法存在当作实测。
- e621ng 面**没有原生写方法**；上游的写路由要用通用 `request()` 显式调用。需要成员权限的 `related_tag` / `related_tag_bulk` 只有源码依据，成功路径未实测。
- 有版本号或能匿名读列表，都不等于该路径已验证；需要登录/API key 的写路径没有线上实测，Serika 全部需 key 方法的成功路径也没有实测。

## 许可

MIT License，见仓库根目录 [LICENSE](../LICENSE)。
