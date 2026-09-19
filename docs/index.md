# Anybooru 文档

Anybooru 是访问 Danbooru、Moebooru、Serika、e621ng、Zerochan、Gelbooru、Gelbooru02（TBIB）、Shuushuu、Sakuria、Anime-Pictures 与 Cosine 十一类图站 API 的 Python 客户端。先选与你的站点匹配的客户端，再按任务查方法；本库不自动识别引擎。

不知道自己的站点属于哪一类？先看[怎么判断一个站点该用哪个类](configuration.md#怎么判断一个站点该用哪个类)（看路径与响应形状），
再进对应家族的「三行上手」跑通第一个请求。

## 先选阅读层

| 你要解决的问题 | 看哪类文档 | 会读到什么 |
| :--- | :--- | :--- |
| 第一次调用，怎么配、怎么跑？ | **客户端用法** `<family>.md` | 构造签名每个参数的作用、三行可复制代码、认证怎么配、请求发到哪个 URL、返回值里能取哪些字段、常见坑 |
| 已知道任务，具体调哪个方法？ | **方法参考** `<family>-api.md` | 按资源分组：每个方法的参数取值范围、不传时服务端怎么做、拼出的真实 URL、返回 JSON 字段或 XML 属性、可直接抄的示例 |
| 知道要做什么、不知道方法叫什么？ | **能力入口** `<family>-capabilities.md` | 「我要做什么 → 用哪个方法」对照表，加该家族全部方法的一行式索引 |
| 要维护客户端、核对依据？ | **契约审计附注** `<family>-contract-notes.md` | 每个方法的出处（上游文件与行号，或 API 页面原文）、权限分支、写动作边界、明确排除的路由、已知的文档与实现差异 |
| 想确认哪些场景真的跑过？ | **验证记录** [verification.md](verification.md) | 实际执行的命令、请求 URL、状态码与响应摘要；哪些只对过源码、哪些没测，分开列 |
| 要接一个新站或新引擎？ | **新增图站流程** [adding-a-site.md](adding-a-site.md) | 从陌生站点到能用的家族：怎么定引擎、怎么摸契约、客户端与冒烟写在哪、四份文档和导航补什么、提交怎么拆 |

## 按家族选文档

| 家族（站点示例） | 客户端怎么用 | 每个方法的参数与返回 | 按任务找方法 | 依据与排除（维护者用） |
| :--- | :--- | :--- | :--- | :--- |
| Danbooru（danbooru.donmai.us、safebooru.donmai.us） | [三行上手](danbooru.md) | [方法参考](danbooru-api.md) | [按任务找方法](danbooru-capabilities.md) | [上游契约与依据](danbooru-contract-notes.md) |
| Moebooru（yande.re、konachan.com、sakugabooru.com） | [三行上手](moebooru.md) | [方法参考](moebooru-api.md) | [按任务找方法](moebooru-capabilities.md) | [上游契约与依据](moebooru-contract-notes.md) |
| Serika（serika.art 与自托管实例） | [三行上手](serika.md) | [官方与站内方法](serika-api.md) | [按任务找方法](serika-capabilities.md) | [版本、权限与说明差异](serika-contract-notes.md) |
| e621ng（e621.net / e926.net） | [三行上手](e621.md) | [方法参考](e621-api.md) | [按任务找方法](e621-capabilities.md) | [上游契约与依据](e621-contract-notes.md) |
| Zerochan（zerochan.net） | [三行上手](zerochan.md) | [两个原生方法](zerochan-api.md) | [按任务找方法](zerochan-capabilities.md) | [API 页面与实测依据](zerochan-contract-notes.md) |
| Gelbooru（gelbooru.com） | [三行上手](gelbooru.md) | [六个原生方法](gelbooru-api.md) | [按任务找方法](gelbooru-capabilities.md) | [来源层级与未实测项](gelbooru-contract-notes.md) |
| Gelbooru02（TBIB，tbib.org） | [三行上手](gelbooru02.md) | [四个原生方法](gelbooru02-api.md) | [按任务找方法](gelbooru02-capabilities.md) | [帮助页与实测证据](gelbooru02-contract-notes.md) |
| Shuushuu（e-shuushuu.net） | [三行上手](shuushuu.md) | [方法参考](shuushuu-api.md) | [按任务找方法](shuushuu-capabilities.md) | [OpenAPI 与实测依据](shuushuu-contract-notes.md) |
| Sakuria（Pixiv 第三方镜像，sakuria-api.syarolia.com） | [三行上手](sakuria.md) | [44 个读取方法](sakuria-api.md) | [按任务找方法](sakuria-capabilities.md) | [匿名响应与资料矛盾](sakuria-contract-notes.md) |
| Anime-Pictures（anime-pictures.net，自研 `api/v3`） | [三行上手](anime-pictures.md) | [13 个原生方法](anime-pictures-api.md) | [按任务找方法](anime-pictures-capabilities.md) | [匿名响应与输入矛盾](anime-pictures-contract-notes.md) |
| Cosine（pic.cosine.ren，自研 API、非 booru 引擎） | [三行上手](cosine.md) | [13 个原生方法](cosine-api.md) | [按任务找方法](cosine-capabilities.md) | [匿名响应与上游文件](cosine-contract-notes.md) |

**两家 Gelbooru 不是同一套接口**，选类前先看清是哪一家：

| | Gelbooru（`gelbooru.com`） | Gelbooru02（TBIB，`tbib.org`） |
| :--- | :--- | :--- |
| 站点依据 | 站点自己的 `index.php` 接口与官方 wiki/help | 首页页脚写 `Running Gelbooru 0.2`，`index.php?page=help&topic=dapi` 有 dapi 文档 |
| 返回格式 | `page=dapi` 请求 JSON（需账号）、`page=autocomplete2` 返回 JSON（匿名） | `post_list` 默认 JSON、可选 XML 原文；标签与评论加 `json=1` 的实测仍为 XML |
| 客户端认证 | `api_key` + `user_id`（留空即匿名） | 没有凭据字段，配置只有 `url`；本站匿名读取已验证，账号未实测 |
| 原生方法 | 6 个：`post_list` / `post_deleted` / `tag_list` / `user_list` / `comment_list` / `autocomplete` | 4 个：`post_list` / `post_deleted` / `tag_list` / `comment_list` |
| 文档入口 | [gelbooru.md](gelbooru.md) | [gelbooru02.md](gelbooru02.md) |

Danbooru / Moebooru / e621ng 是三个互不相同的 Rails 引擎；Serika 是独立的 Next.js 引擎，提供官方 `/api/v1`
与前端自用、没有公共兼容保证的 `/api/*`；Zerochan 是站点自有的只读 JSON API，**没有公开的引擎源码**，
只能拿官方 API 页面原文和真实响应当依据，所以它的附注引用的是页面文字与实测响应，而不是源码行号；
Gelbooru 使用 `index.php`：`page=dapi&json=1` 请求官方 JSON，`page=autocomplete2` 返回站内补全 JSON；
`page=tags/post/wiki` 等浏览路由返回 HTML。依据是官方 wiki/帮助页、站点 JavaScript 和真实匿名响应，
没有当前 PHP 服务端快照可引用，不能由前端字段推出 dapi 字段。
Gelbooru02 是另一套东西：TBIB（`tbib.org`）自述 `Running Gelbooru 0.2`，同一个 `index.php` 上**帖子可选 JSON**、
**标签与评论实测返回 XML 文本**（加 `json=1` 也一样）；依据是该站 `index.php?page=help&topic=dapi` 帮助页与
真实匿名响应，没有服务端源码快照，也不能由帮助页推出未观察到的字段。
e-shuushuu 是独立 FastAPI REST API，所有原生方法在 `/api/v1`，依据是站点自带 OpenAPI 和真实响应；
没有本地上游服务端源码，不套用 Danbooru 或 Moebooru 的路由、标签字符串规则。
Sakuria 是 Pixiv 第三方镜像而非 booru：插画、小说、用户、系列和特辑各有独立路由，完整 JSON 不拆层。
没有可引用的服务端源码、官方 API 页面或 OpenAPI；依据只有匿名响应与待核实的用户观察，证据等级最弱。
Anime-Pictures 也是非 booru 的一类：站点自研 `api/v3` JSON 接口，**API 主机** `api.anime-pictures.net`
与网页主机 `anime-pictures.net` 分开（网页主机被 Cloudflare 质询挡下，`/api/v3/*` 的 302 不依赖），
根、帖子、标签、用户与评论各走自己的路径与参数名。官方 API 手册页同样读不到，也没有 OpenAPI 与服务端源码；
依据只是匿名响应实测与候选输入资料（其中的外部客户端源码链接本轮没有独立读过），未实测项单独标明，
见[契约附注](anime-pictures-contract-notes.md)。
Cosine（`pic.cosine.ren`）也不是 booru 引擎：它是 Telegram 频道 `@CosineGallery` 的配套图站，Next.js +
Prisma + Meilisearch 自研 API，`api/list`、`api/artwork/{id}`、`api/random`、`api/search`、`api/tag` 与
`api/tags`、`api/artist` 与 `api/artists`、`api/search/admin` 以及 `feed.xml` 各走自己的路由，参数名
（`pageSize` / `start` / `offset` / `r18`）与返回外壳都属于站点自己，四种外壳本库一个都不拆。
没有 OpenAPI 与服务端源码快照，站点前端源码在公开仓库里、本轮只按需只读了个别文件当线索，
公开结论以匿名只读响应为准，见[契约附注](cosine-contract-notes.md)。
不能按“Danbooru-style”这类血缘名称选客户端：e621ng 与 Danbooru 都提供复数 `posts` 路径、都用 HTTP Basic，
但返回的 JSON 结构完全不同。判断方法见
[配置：怎么选类](configuration.md#怎么判断一个站点该用哪个类)。

## 十一个家族共用的用法

| 文档 | 什么时候看 |
| :--- | :--- |
| [安装](installation.md) | Python 与依赖要求、源码安装步骤、装完怎么验证、包内文件都在哪 |
| [配置](configuration.md) | 默认读哪份 JSON、怎么换一份自己的、`sites` 每个字段什么意思、`examples` 各键对应哪个调用、代理与超时写在哪 |
| [认证](authentication.md) | Danbooru/e621ng 用 HTTP Basic、Moebooru 用 password_hash、Serika 用 Bearer key、Gelbooru dapi 用 api_key + user_id、Gelbooru02 无凭据、Zerochan 无认证、Shuushuu 显式登录、Sakuria 只接收已有 Bearer token、Anime-Pictures 原样转发 `Authorization` / `Cookie`、Cosine 默认匿名且 `revalidate_secret` 留空 |
| [分页](pagination.md) | 十一个家族各自的页码参数、每页条数、游标形式，以及 Sakuria 的重复结果与不可靠总数、Anime-Pictures 的 0 起步 `page`、Cosine 的 `pageSize` / `limit`+`offset` 与搜索 `total` 被夹到 1000 |
| [错误处理](errors.md) | 三个异常类各自什么时候抛、HTTP 错误带哪些字段、各引擎的状态码含义、为什么不自动重试 |
| [迁移](migration.md) | 从 Pybooru 4.x 改名/换参数/换返回值的逐方法对照表 |

## 客户端共同约定

1. **显式配置**：默认读随包安装的 `anybooru/anybooru.json`，`config_file` 指向别的文件时读那一份；
   不读环境变量、不搜索当前工作目录、没有内置站点后备。构造函数的站点名就是配置 `sites` 段里的键名。
2. **通用入口与原生方法**：十一个客户端都有 `request()`，原生方法只是把参数拼好再调它。能传什么参数、
   有没有权限，全由服务端决定；客户端不预判能力，也不拦下你不认识的搜索字段。
3. **返回什么就给你什么**：不自动翻页、不重试、不换别的接口重来；HTTP 非 2xx 时抛异常并保留状态码和正文。
   有些方法会替你剥掉一层外层对象：Serika 官方 v1 返回 `{"success":true,"data":{…},"meta":{…}}` 时返回 `data` 里的内容、
   把 `meta` 放进 `client.last_call['meta']`；e621ng 的列表返回 `{"posts":[… ]}` 时给你数组、详情返回 `{"post":{…}}` 时给你对象，
   而 `v2=true` 或带 `only=` 的请求服务端本来就不套这层，客户端也不拆；Zerochan 的列表返回 `{"items":[… ]}` 时给你数组，
   详情路径直接是条目对象；Gelbooru、Shuushuu、Sakuria、Anime-Pictures 与 Cosine 一个外层都不拆，服务端给什么就返回什么
   （Cosine 的四种外壳原样返回：superjson 的 `{"json":…,"meta":…}`、`{"images":…,"total":…}`、
   `{"success":true,"data":…}` 与裸数组；`image_random` 在 `count=1` 时 superjson 里的 `json` 是**对象**、
   `count≥2` 时才是数组）；
   Gelbooru02 的 XML 方法给你**服务端原文**（含 XML 声明、根元素属性与全部空白，不解析、不转换、不裁剪）。
   返回内容的完整原貌、以及哪些方法不拆，见各家族方法参考。
4. **参数按各引擎的写法发**：Rails 引擎把嵌套字典编成 `a[b]`、列表编成重复键 `a[]`，布尔发成 `true` / `false`，
   值为 `None` 的键不发送；Danbooru 不带文件的 `data` 用 JSON 请求体，Moebooru 一律用 Rails 表单。
   Serika 的标签与评级是逗号分隔的字符串（不是数组），批量查询用 JSON，上传用 multipart。
   e621ng 与 Danbooru 同为 Basic 认证，但评级的取值和帖子字段都不同，查询不能互相照抄。
   Zerochan 用站点自己的单字母查询键（`p` 页码、`l` 每页条数、`s` 排序、`t` 人气窗口、`d` 尺寸、`c` 颜色），
   标签写在路径上，要 JSON 得在查询串里带 `json` 标记，而不是给路径加 `.json`。
   Gelbooru 的路径固定是 `index.php`，用 `page` 选择入口，dapi 补 `json=1`，autocomplete2 本身返回 JSON；
   凭据只在 dapi 请求上发送。
   Gelbooru02 也走 `index.php`，用 `page` 选入口、`response_format` 选 JSON 还是 XML 原文；
   查询键（`limit` / `pid` / `tags` / `id` / `post_id`）原样转发，`s` 与 `q` 由客户端补。
   Shuushuu 的 `tags='46,169'` 是数字 ID 逗号串，`status=[1, 2]` 是重复同名键；分页用 `page/per_page`，
   标签搜索方法 `search` 用 `limit/offset`。构造从不登录；`user_ratings` 是显式私有读取，其余资源读取的实测范围见家族文档。
   Sakuria 的插画搜索使用 `q/page/size`，标签路径逐段 URL 编码；不把 booru 的 `tags/limit` 换算成这些参数。
   Anime-Pictures 用站点自己的查询键（`page` 0 起步、`posts_per_page`、`search_tag`、`order_by` 等），
   资源 id 与文件名都在路径段上逐段编码；`'posts'` 这类相对路径拼在 **API 基址** `/api/v3` 后面，
   而带前导 `/` 的路径（`'/api/v3/posts'`、`'/'`）落在主机根——这是与其它家族最直观的差别。
   Cosine 的参数走共享编码：`None` 丢弃、布尔发成小写、数组按 Rails 重复键；`path` 去掉前导 `/` 后拼在
   站点根上，`data` 按 JSON 原样发送。它的分页用站点自己的键（`page`/`pageSize`、`limit`/`offset`、
   `start`/`limit`），`response_format='xml'` 时 `feed()` 走 `.text` 返回完整 RSS 原文，不做 JSON 嗅探。

## 边界与未实测

- 源码家族 Danbooru / Moebooru / Serika / e621ng 对齐各自固定版本的上游源码（文件与行号见对应附注）。
  Zerochan、Gelbooru、Gelbooru02 与 Shuushuu 依据站点页面、脚本、帮助页或 OpenAPI 加真实响应。
  Cosine 没有本地上游服务端源码，站点前端源码在公开仓库里，本轮只按需只读了个别文件当线索
  （不 clone、不写行号），公开结论以匿名只读响应为准。
  Sakuria 没有上述正式来源，仅有匿名实测；Anime-Pictures 同样没有可读到的官方手册页、OpenAPI 或服务端源码，
  依据只是匿名响应加候选输入资料。未复核的资料说法集中标明。任何一种依据都不是对下游站点的保证。
- 已经真实执行过的匿名读取：Danbooru 的 12 次成功与 3 次预期错误、Moebooru 的指定匿名读取、Serika 的
  官方公开入口与部分站内读取、e621ng 三个示例在 e621.net 与 e926.net 各跑一遍、Zerochan 的
  `entry_list` 与 `entry_show`、Gelbooru 的 `autocomplete`（`200`，返回建议数组；实测 `limit=3` 仍返回
  10 条）、Gelbooru02（TBIB）的匿名冒烟与两个示例（`post` 的 JSON 与 XML、`tag`、`comment`、`pid` 分页，
  共 10 次请求全部 `200`，三个脚本退出 `0`）、Anime-Pictures 的 90 次串行匿名 GET（`200`×76、
  `400`×4、`403`×2、`404`×6、`410`×1、`500`×1：API 主机根、两页帖子、帖子详情、帖评论、标签列表与详情、
  用户列表与详情、评论列表与详情、分页与排序参数、缺失资源的四种状态码、非法路径段的纯文本 `400`、
  `get_image` 的空正文 `403`）及 Cosine 的匿名读取路径与边界；
  各家族示例脚本的实跑情况见[验证记录](verification.md)。
- 只有源码或站点文档依据、没有成功响应记录的部分：所有需要登录或 API key 的写路径、e621ng 需要成员权限的
  `related_tag` / `related_tag_bulk`、Serika 全部需 key 的 v1 方法、Gelbooru 全部 5 个 dapi 方法
  （账号成功返回未实测，匿名已各取得401空正文）、Gelbooru02 未观察到的部分（评论非空结构、`post_deleted`
  的成功流、`limit` 的真实上限）、Anime-Pictures 的 `post_create`（没发过 POST）、带 Cookie 的
  `post_tags` 与 `image_get`、媒体地址的成功返回、Cosine 的两个 POST（`artwork_revalidate` 需要站点密钥、
  `search_index_admin` 会改站点索引，本轮都没有调用）、旧版 web 路由与 `PUT` / `PATCH` / `DELETE`。
  方法存在不等于成功路径测过。
- 只读范围并不相同：e621ng 面没有原生写方法，写路由要用通用 `request()` 自己拼方法与路径；
  Zerochan 的 API 本身只读，且只提供 JSON（不实现 `xml`），文档要求的 User-Agent 里含项目名与
  Zerochan 用户名是站点约定，本库照配置原样发送、不校验、不代填。Gelbooru 面同样没有写方法，
  使用 `page=dapi` 与 `page=autocomplete2` 两个 JSON 入口；`page=tags/post/wiki` 等 HTML 浏览页面
  不封装为 JSON 方法，也不抓取解析。Gelbooru02（TBIB）只有 4 个只读方法、没有写方法也没有账号接口：
  帖子的 JSON 与 XML 字段并不一致（JSON 没有 `file_url` / `sample_url` / `preview_url`，XML 有且 `rating` 用
  单字母 `s`），它不替你构造媒体地址；`post_deleted` 在 TBIB 上是 `500` 加不完整 XML，客户端照原样抛
  `AnybooruHTTPError`，不降级、不重试；`tag` / `comment` 只会返回 XML 文本（`json=1` 也一样），
  XML 也不解析成字典。
- Shuushuu 默认匿名；公开图片、标签、评论、用户资料等读取不要求账号，但个人资料和管理 GET 不在此列。
  登录、刷新、登出及账号写操作未实测；本次匿名冒烟与示例的实际范围见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)。
- Sakuria 提供 27 个公共资源 GET 与 17 个账号 GET。账号方法只接收已有 token，成功返回结构未实测；
  不实现登录、刷新或媒体下载。匿名执行范围与资料矛盾见[验证记录](verification.md#sakuria匿名只读实测2026-09-19)。
- Anime-Pictures 的 13 个原生方法里有 12 个只读 GET 和 1 个 POST（`post_create`）；`post_tags` 与
  `image_get`（`/pictures/get_image/{file_url}`，原样返回 `bytes`）也是读请求但需要身份，匿名实测 `403`。
  本类不提供登录、注册或刷新方法，也不索要账号密码；本家族唯一的字节读取方法是
  `image_get`，其余 CDN 地址只写在文档里。匿名执行范围、输入资料矛盾与未实测项见
  [验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)与
  [契约附注](anime-pictures-contract-notes.md)。
- Cosine 的 13 个原生方法里 11 个是只读 GET（`search_index_status` 也是只读 GET），另有两个 POST：
  `artwork_revalidate` 把 `{"artworkId":…,"secret":…}` 作为 JSON 原文发出，密钥留空就照发空串、由站点判定；
  `search_index_admin` **会重建或删除站点搜索索引**，公开路由源码没有鉴权检查，本库不做自动重试与兜底，
  示例和冒烟都不调用它。两个 POST 本轮都未执行，成功与拒绝形态都未实测；`feed()` 用 `response_format='xml'`
  返回 RSS 原文。匿名可读范围、状态码样本与未实测项见
  [验证记录](verification.md#cosine匿名只读实测2026-09-20)与[契约附注](cosine-contract-notes.md)。

## 许可

MIT License，见仓库根目录 [LICENSE](../LICENSE)。
