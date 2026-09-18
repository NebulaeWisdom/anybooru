# Anybooru 文档

Anybooru 是访问 Danbooru、Moebooru、Serika、e621ng、Zerochan 与 Gelbooru 六类引擎图站 API 的 Python 客户端。先选与你的站点匹配的客户端，再按任务查方法；本库不自动识别引擎。

不知道自己的站点属于哪一类？先看[怎么判断一个站点该用哪个类](configuration.md#怎么判断一个站点该用哪个类)（看路径与响应形状），
再进对应家族的「三行上手」跑通第一个请求。

## 先选阅读层

| 你要解决的问题 | 看哪类文档 | 会读到什么 |
| :--- | :--- | :--- |
| 第一次调用，怎么配、怎么跑？ | **客户端用法** `<family>.md` | 构造签名每个参数的作用、三行可复制代码、认证怎么配、请求发到哪个 URL、返回值里能取哪些字段、常见坑 |
| 已知道任务，具体调哪个方法？ | **方法参考** `<family>-api.md` | 按资源分组：每个方法的参数取值范围、不传时服务端怎么做、拼出的真实 URL、返回 JSON 的字段与类型、可直接抄的示例 |
| 知道要做什么、不知道方法叫什么？ | **能力入口** `<family>-capabilities.md` | 「我要做什么 → 用哪个方法」对照表，加该家族全部方法的一行式索引 |
| 要维护客户端、核对依据？ | **契约审计附注** `<family>-contract-notes.md` | 每个方法的出处（上游文件与行号，或 API 页面原文）、权限分支、写动作边界、明确排除的路由、已知的文档与实现差异 |
| 想确认哪些场景真的跑过？ | **验证记录** [verification.md](verification.md) | 实际执行的命令、请求 URL、状态码与响应摘要；哪些只对过源码、哪些没测，分开列 |

## 按家族选文档

| 家族（站点示例） | 客户端怎么用 | 每个方法的参数与返回 | 按任务找方法 | 依据与排除（维护者用） |
| :--- | :--- | :--- | :--- | :--- |
| Danbooru（danbooru.donmai.us、safebooru.donmai.us） | [三行上手](danbooru.md) | [方法参考](danbooru-api.md) | [按任务找方法](danbooru-capabilities.md) | [上游契约与依据](danbooru-contract-notes.md) |
| Moebooru（yande.re、konachan.com、sakugabooru.com） | [三行上手](moebooru.md) | [方法参考](moebooru-api.md) | [按任务找方法](moebooru-capabilities.md) | [上游契约与依据](moebooru-contract-notes.md) |
| Serika（serika.art 与自托管实例） | [三行上手](serika.md) | [官方与站内方法](serika-api.md) | [按任务找方法](serika-capabilities.md) | [版本、权限与说明差异](serika-contract-notes.md) |
| e621ng（e621.net / e926.net） | [三行上手](e621.md) | [方法参考](e621-api.md) | [按任务找方法](e621-capabilities.md) | [上游契约与依据](e621-contract-notes.md) |
| Zerochan（zerochan.net） | [三行上手](zerochan.md) | [两个原生方法](zerochan-api.md) | [按任务找方法](zerochan-capabilities.md) | [API 页面与实测依据](zerochan-contract-notes.md) |
| Gelbooru（gelbooru.com） | [三行上手](gelbooru.md) | [六个原生方法](gelbooru-api.md) | [按任务找方法](gelbooru-capabilities.md) | [来源层级与未实测项](gelbooru-contract-notes.md) |

Danbooru / Moebooru / e621ng 是三个互不相同的 Rails 引擎；Serika 是独立的 Next.js 引擎，提供官方 `/api/v1`
与前端自用、没有公共兼容保证的 `/api/*`；Zerochan 是站点自有的只读 JSON API，**没有公开的引擎源码**，
只能拿官方 API 页面原文和真实响应当依据，所以它的附注引用的是页面文字与实测响应，而不是源码行号；
Gelbooru 使用 `index.php`：`page=dapi&json=1` 请求官方 JSON，`page=autocomplete2` 返回站内补全 JSON；
`page=tags/post/wiki` 等浏览路由返回 HTML。依据是官方 wiki/帮助页、站点 JavaScript 和真实匿名响应，
没有当前 PHP 服务端快照可引用，不能由前端字段推出 dapi 字段。
不能按“Danbooru-style”这类血缘名称选客户端：e621ng 与 Danbooru 都提供复数 `posts` 路径、都用 HTTP Basic，
但返回的 JSON 结构完全不同。判断方法见
[配置：怎么选类](configuration.md#怎么判断一个站点该用哪个类)。

## 六个家族共用的用法

| 文档 | 什么时候看 |
| :--- | :--- |
| [安装](installation.md) | Python 与依赖要求、源码安装步骤、装完怎么验证、包内文件都在哪 |
| [配置](configuration.md) | 默认读哪份 JSON、怎么换一份自己的、`sites` 每个字段什么意思、`examples` 各键对应哪个调用、代理与超时写在哪 |
| [认证](authentication.md) | Danbooru 用 username + API key 走 HTTP Basic、Moebooru 用 password_hash、Serika 用 Bearer key、e621ng 同 Danbooru 但另一套引擎、Gelbooru 的 dapi 要账号的 api_key + user_id、Zerochan 没有认证只有 User-Agent 要求 |
| [分页](pagination.md) | 六个家族各自的页码参数与每页上限、游标形式、超过上限报什么错 |
| [错误处理](errors.md) | 三个异常类各自什么时候抛、HTTP 错误带哪些字段、各引擎的状态码含义、为什么不自动重试 |
| [迁移](migration.md) | 从 Pybooru 4.x 改名/换参数/换返回值的逐方法对照表 |

## 客户端共同约定

1. **显式配置**：默认读随包安装的 `anybooru/anybooru.json`，`config_file` 指向别的文件时读那一份；
   不读环境变量、不搜索当前工作目录、没有内置站点后备。构造函数的站点名就是配置 `sites` 段里的键名。
2. **通用入口与原生方法**：六个客户端都有 `request()`，原生方法只是把参数拼好再调它。能传什么参数、
   有没有权限，全由服务端决定；客户端不预判能力，也不拦下你不认识的搜索字段。
3. **返回什么就给你什么**：不自动翻页、不重试、不换别的接口重来；HTTP 非 2xx 时抛异常并保留状态码和正文。
   有些方法会替你剥掉一层外层对象：Serika 官方 v1 返回 `{"success":true,"data":{…},"meta":{…}}` 时返回 `data` 里的内容、
   把 `meta` 放进 `client.last_call['meta']`；e621ng 的列表返回 `{"posts":[… ]}` 时给你数组、详情返回 `{"post":{…}}` 时给你对象，
   而 `v2=true` 或带 `only=` 的请求服务端本来就不套这层，客户端也不拆；Zerochan 的列表返回 `{"items":[… ]}` 时给你数组，
   详情路径直接是条目对象；Gelbooru 一个外层都不拆，服务端给什么就返回什么。返回 JSON 的完整原貌、
   以及哪些方法不拆，见各家族方法参考。
4. **参数按各引擎的写法发**：Rails 引擎把嵌套字典编成 `a[b]`、列表编成重复键 `a[]`，布尔发成 `true` / `false`，
   值为 `None` 的键不发送；Danbooru 不带文件的 `data` 用 JSON 请求体，Moebooru 一律用 Rails 表单。
   Serika 的标签与评级是逗号分隔的字符串（不是数组），批量查询用 JSON，上传用 multipart。
   e621ng 与 Danbooru 同为 Basic 认证，但评级的取值和帖子字段都不同，查询不能互相照抄。
   Zerochan 用站点自己的单字母查询键（`p` 页码、`l` 每页条数、`s` 排序、`t` 人气窗口、`d` 尺寸、`c` 颜色），
   标签写在路径上，要 JSON 得在查询串里带 `json` 标记，而不是给路径加 `.json`。
   Gelbooru 的路径固定是 `index.php`，用 `page` 选择入口，dapi 补 `json=1`，autocomplete2 本身返回 JSON；
   凭据只在 dapi 请求上发送。

## 边界与未实测

- 依据分两条路：Danbooru / Moebooru / Serika / e621ng 对齐各自固定版本的上游源码（文件与行号见对应附注），
  Zerochan 与 Gelbooru 没有可引用的上游源码，只有站点页面/脚本原文与真实响应。两条路都不是对每个下游
  站点的保证：站点可以自己关掉某个功能、按权限裁剪返回内容，也可能用反爬挡住你所在的网络。
- 已经真实执行过的匿名读取：Danbooru 的 12 次成功与 3 次预期错误、Moebooru 的指定匿名读取、Serika 的
  官方公开入口与部分站内读取、e621ng 三个示例在 e621.net 与 e926.net 各跑一遍、Zerochan 的
  `entry_list` 与 `entry_show`、Gelbooru 的 `autocomplete`（`200`，返回建议数组；实测 `limit=3` 仍返回
  10 条）。逐条命令、请求 URL 与结果见[验证记录](verification.md)。
- 只有源码或站点文档依据、没有成功响应记录的部分：所有需要登录或 API key 的写路径、e621ng 需要成员权限的
  `related_tag` / `related_tag_bulk`、Serika 全部需 key 的 v1 方法、Gelbooru 全部 5 个 dapi 方法
  （需要账号，未实测）。方法存在不等于测过。
- 只读范围并不相同：e621ng 面没有原生写方法，写路由要用通用 `request()` 自己拼方法与路径；
  Zerochan 的 API 本身只读，且只提供 JSON（不实现 `xml`），文档要求的 User-Agent 里含项目名与
  Zerochan 用户名是站点约定，本库照配置原样发送、不校验、不代填。Gelbooru 面同样没有写方法，
  使用 `page=dapi` 与 `page=autocomplete2` 两个 JSON 入口；`page=tags/post/wiki` 等 HTML 浏览页面
  不封装为 JSON 方法，也不抓取解析。

## 许可

MIT License，见仓库根目录 [LICENSE](../LICENSE)。
