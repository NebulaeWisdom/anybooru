# 配置文件 `anybooru.json`

Anybooru 的所有可调参数——站点地址、凭据、代理、超时、User-Agent、示例参数——集中放在一份
JSON 文件里。

设计上只有两个来源，都用**显式参数**决定：

* 默认：`config_file=None`，读**随包安装**的 `anybooru/anybooru.json`；
* 覆盖：`config_file='<路径>'`，读指定的那一份（相对路径相对当前工作目录解析）。

此外没有别的入口：没有环境变量输入、不去当前工作目录或用户目录猜一份同名文件、没有内置站点后备，
也不会因为站点名未知就悄悄换一个地址。

## 文件放在哪里

`config_file` 默认 `None`，读的是安装包里那份 `anybooru.json`，所以安装之后直接写
`Danbooru('danbooru')` 就能用，不需要把任何东西复制到工作目录。

要改站点、凭据或代理，把那份文件复制成自己的，再把路径交给 `config_file`：

```python
from anybooru import Danbooru, DEFAULT_CONFIG_FILE

print(DEFAULT_CONFIG_FILE)  # 包内默认配置的绝对路径
client = Danbooru('danbooru')  # 读包内默认配置
client = Danbooru('danbooru', config_file='config/sites.json')  # 读自己那份
client = Danbooru('danbooru', config_file=r'D:\app\sites.json')  # 绝对路径亦可
```

包内默认文件的绝对路径从 `anybooru.DEFAULT_CONFIG_FILE` 读（editable 安装时它就是仓库里的
`anybooru/anybooru.json`，改动立即生效）。`config_file` 指到的文件不存在时构造函数直接抛出
`FileNotFoundError`，**不会**退回到默认文件，也不会退回到内置站点。

`Danbooru('danbooru')` 的第一个参数是 `sites` 段里的键名，不是 URL。

## 完整样例

完整、可直接复制的内容见包内的 [`anybooru/anybooru.json`](../anybooru/anybooru.json)（wheel 与 sdist
都带这份文件）。它的结构如下（`sites` 段可以按需要增删站点；`verification` 段是维护者验证脚本
专用的，普通使用者可以省略）：

```json
{
  "request": {
    "timeout": 30,
    "proxies": {},
    "user_agent": "Anybooru/0.1.0.dev1"
  },
  "sites": {
    "serika": { "url": "https://serika.art", "api_key": "" },
    "danbooru": { "url": "https://danbooru.donmai.us", "username": "", "api_key": "" },
    "safebooru": { "url": "https://safebooru.donmai.us", "username": "", "api_key": "" },
    "konachan": {
      "url": "https://konachan.com",
      "username": "",
      "password": "",
      "api_version": "1.13.0+update.3",
      "hash_string": "So-I-Heard-You-Like-Mupkids-?--{0}--"
    },
    "yandere": {
      "url": "https://yande.re",
      "username": "",
      "password": "",
      "api_version": "1.13.0+update.3",
      "hash_string": "choujin-steiner--{0}--"
    },
    "sakugabooru": {
      "url": "https://sakugabooru.com",
      "username": "",
      "password": "",
      "api_version": "1.13.0+update.3",
      "hash_string": "er@!$rjiajd0$!dkaopc350!Y%)--{0}--"
    },
    "e621": { "url": "https://e621.net", "username": "", "api_key": "" },
    "e926": { "url": "https://e926.net", "username": "", "api_key": "" }
  },
  "examples": {
    "serika": {
      "site": "serika",
      "image_query": {"page": 1, "limit": 3, "ratings": "safe", "sort": "newest"},
      "user_query": {"page": 1, "limit": 1, "sort": "newest"},
      "tag_query": {"limit": 3},
      "artist_query": {"page": 1, "limit": 3},
      "random_size": {"width": 400, "height": 400},
      "random_query": {"ratings": "safe", "format": "png", "fit": "cover"}
    },
    "danbooru": {
      "site": "danbooru",
      "tags": "rating:g",
      "limit": 3,
      "pages": [1, 2],
      "tag_search": {"order": "count"},
      "preview_chars": 200,
      "post_id": 1,
      "wiki_query": "help:api",
      "wiki_title": "help:api",
      "related_query": "touhou",
      "related_category": 0,
      "related_order": "frequency",
      "search_sample_size": 1000,
      "tag_sample_size": 100,
      "comment_body": "示例评论"
    },
    "moebooru": {
      "site": "yandere",
      "tags": "rating:s",
      "limit": 3,
      "pages": [1, 2],
      "tag_order": "count",
      "comment_query": "",
      "wiki_query": "touhou",
      "related_tags": "touhou",
      "related_type": "general",
      "preview_chars": 120
    },
    "e621": {
      "site": "e621",
      "post_query": {"tags": "rating:s", "limit": 2},
      "random_query": {"tags": "rating:s"},
      "tag_query": {"limit": 2},
      "artist_query": {"limit": 2},
      "comment_query": {"group_by": "comment", "limit": 2},
      "pool_query": {"limit": 2},
      "note_query": {"limit": 2},
      "wiki_query": {"limit": 2},
      "wiki_title": "help:api",
      "pause_seconds": 1
    }
  }
}
```

Serika 示例使用默认配置中的 `examples.serika`，不与 Danbooru、Moebooru、e621ng 三个 Rails 家族的搜索语法混用：

| 键 | 用途 |
| :--- | :--- |
| `site` | 对应 `sites.serika`，也可改为自托管实例的站点键 |
| `image_query` | 站内图片列表查询，含 `page` / `limit` / CSV `ratings` / `sort` |
| `user_query` | 官方 v1 匿名用户目录查询，含 `page` / `limit` / `sort` |
| `tag_query` / `artist_query` | 站内标签、画师列表查询 |
| `random_size` | 匿名二进制图片路径的 `width` / `height` |
| `random_query` | 二进制图片的 `ratings` / `format` / `fit` 等查询值 |

站内详情示例从实际列表响应取得 `post_id`，不硬编码图片 ID。三个匿名示例的命令见
[serika.md](serika.md#可运行示例)。`verification.serika` 的 `scripts` 与 `pause_seconds` 指定本轮逐一运行哪些示例与调用间隔；
请求输入仍来自 `examples.serika`。证据文件由维护者留在本机，不入库。

e621ng 示例使用 `examples.e621`，查询参数是 Rails 顶层参数与 `search[...]`，不是 Serika 的 CSV 风格：

| 键 | 用途 |
| :--- | :--- |
| `site` | 对应 `sites.e621`，改成 `e926` 即换到安全内容站 |
| `post_query` | `post_list` 的查询（`tags`、`limit` 等顶层参数） |
| `random_query` | `post_random` 的查询（`tags`） |
| `tag_query` / `artist_query` / `comment_query` / `pool_query` / `note_query` / `wiki_query` | 各资源 `*_list` 的字典参数（评论带 `group_by`） |
| `wiki_title` | `wiki_page_show` 的标题或 ID（`help:api` 这类含冒号的标题由客户端转义） |
| `pause_seconds` | 示例脚本两次调用之间的等待秒数，脚本自己 sleep，库不做限速 |

三个匿名示例的命令见 [e621.md](e621.md)。`verification.e621` 的 `sites` 决定逐站运行哪些站点、`scripts`
列出要跑的示例、`pause_seconds` 是间隔；`post_query` / `count_query` / `v2_query` / `only_query` /
`related_search` 是返回形态与权限分支的复核输入；可运行示例的请求输入来自 `examples.e621`。

## `request` 段

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `timeout` | number | 单次请求超时秒数，默认 `30`；写成数组时按 requests 的 (连接超时, 读取超时) 处理 |
| `proxies` | object | 传给 requests 的代理字典，键为 `http` / `https`；默认 `{}`，即不使用代理 |
| `user_agent` | string | 请求头 `User-Agent` |

## `sites` 段

每个键是一个站点名，值是**同一个名称**在客户端构造函数中引用到的配置。

这一段是**样例 / 起始清单，不是支持边界**：

* 库不读任何内置站点表，也不对站点名做白名单校验——`site_name` 在 `sites` 里查不到就
  直接 `KeyError`，不会回落到别的地址（`resources.py` 只做 `json.load`，`anybooru.py` 只做一次字典取值）；
* 名单外的站点只要跑同一套引擎，就能直接用：构造时传 `site_url`（Moebooru 还必须同时传
  `api_version`），完全绕开本段；
* 反过来，名单里的站点**不保证每个能力都可用**：站点自己会关闭部分功能、按权限裁剪返回内容，
  网络侧也可能只挡住你这条线路（例如 `konachan.com` 在某些网络上得到 Cloudflare 挑战页）。

支持范围由**引擎契约**决定，而不是由这份清单决定：Danbooru 引擎看
[danbooru-api.md](danbooru-api.md)，Moebooru 引擎看 [moebooru-api.md](moebooru-api.md)，
Serika 引擎看 [serika-api.md](serika-api.md)，e621ng 引擎看 [e621-api.md](e621-api.md)。
契约基线固定在本地的上游快照（`danbooru/` HEAD `d4cdddd44`、`moebooru/` HEAD `206455e1`、
`Serika.art/` HEAD `ef11dd12`、`e621ng/` HEAD `7a9c98851`），
所以**同引擎也可能漂移**：站点跑的是更老或改过的分支时，个别端点的参数、权限与响应形态可能不同，
本库实现的是那份契约而不是某个站点的私有行为。按需增删站点键是正常用法，把清单当成“只支持这些站”会误判。

Danbooru 系站点（Danbooru 引擎）：

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `url` | string | 站点根地址，如 `https://danbooru.donmai.us` |
| `username` | string | 用户名 |
| `api_key` | string | API key |

> `username` 与 `api_key` **任一非空**就会给请求带上 HTTP Basic；两项都为空才是匿名请求。
> 只填一项不等同于匿名，服务端会返回 `401`。见 [authentication.md](authentication.md)。

Moebooru 系站点（Moebooru 引擎）：

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `url` | string | 站点根地址，如 `https://konachan.com` |
| `username` | string | 用户名 |
| `password` | string | 明文密码，客户端自行计算 `password_hash` |
| `hash_string` | string \| null | 站点自己的加盐模板，含 `{0}` 占位符（等价上游 `CONFIG["password_salt"]` + 固定前后缀 `--`）；为 `null` 表示条目没给，登录时必须显式传 |
| `api_version` | string | 站点 `help/api` 标题里自述的 API 版本，如 `1.13.0+update.3`；只影响列表路径形态，见下 |

> 凭据留空即可用于**只读**接口。请把填好的 `anybooru.json` 留在本地，不要提交真实账号与 key。

这两个键都是**站点自述值，抄自该站 `help/api`**（需要 `Accept: text/html`，见
[moebooru-api.md](moebooru-api.md)），不是本库定义、也没有“最新版本”可升级：

* `hash_string`：上游把它渲染进帮助页
  （`moebooru/app/views/help/api.en.html.erb:95` 的 “The actual string that is hashed is
  `<%= CONFIG["password_salt"] %>--your-password--`”），仓库默认值是 `choujin-steiner`
  （`moebooru/config/init_config.rb:9`，即 yande.re 用的那个）。各站自己改盐：本仓库样本里
  `konachan` 是 `So-I-Heard-You-Like-Mupkids-?--{0}--`、`sakugabooru` 是
  `er@!$rjiajd0$!dkaopc350!Y%)--{0}--`。本库做 `SHA1(hash_string.format(password))`，
  与上游 `User.sha1`（`moebooru/app/models/user.rb:95-96`，盐来自 `user.rb:615` 的
  `@salt = CONFIG["password_salt"]`）等价。它是**固定常量**：站点不换盐就不用动，
  与引擎版本无关；本轮实测三站 `help/api` 报的仍是上面这些值。
* `api_version`：本库只拿它决定**列表路径形态**。`help/api` 的变更日志写着 `1.13.0+update.3`
  的改动是 “Removed /index from API URLs”，所以只有 `1.13.0` / `1.13.0+update.1` / `1.13.0+update.2`
  这三个旧值会被补成 `/post/index.json`，其余走 `/post.json`（`anybooru/moebooru.py` 的 `request`）。
  现役三站都自述 `1.13.0+update.3`，因此用新形态；旧别名路由在新部署里仍然存在，但不再是契约路径。

> 注意同名不同物：请求参数里的 `api_version='2'` 是**引擎的 v2 响应信封开关**
> （`moebooru/app/controllers/post_controller.rb:338-362`），与这里的站点版本字符串无关，
> 详见 [moebooru-api.md](moebooru-api.md)。

Serika 系站点（四家族中的独立 Next.js 引擎）：

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `url` | string | `serika.art` 或相同引擎的自托管根地址；无内置站点后备 |
| `api_key` | string | 非空时发送 `Authorization: Bearer <key>`；默认配置样例为空，仅匿名访问 |

Serika 不使用 `username`、`password`、`hash_string` 或客户端路径版本开关。
`Serika('serika')` 读取上述两项；自托管实例在 `sites` 中新增同结构条目。
官方 v1 的多数只读路由也需 key，空 key 不会被替换成占位符；本轮不申请凭据、不实测这些路由。
站内 cookie 登录不实现，详见 [authentication.md](authentication.md#serika-系站点)。

e621ng 系站点（e621ng 引擎，e621.net 与 e926.net 同引擎两站）：

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `url` | string | 站点根地址，如 `https://e621.net` / `https://e926.net` |
| `username` | string | 登录名 |
| `api_key` | string | API key |

与 Danbooru 条目同构（HTTP Basic，`username` 与 `api_key` 任一非空即带认证头），但这是另一套引擎：
站点条目里没有 `password` / `hash_string` / `api_version`，客户端也没有路径版本开关。
`safe_mode` 属于站点部署配置，不在上游仓库默认值内，本库不替站点补评级过滤。

同一个站点名在所有客户端里都表示 `sites` 段的键（`Danbooru`、`Moebooru`、`Serika`、`E621`），
选择哪个类由调用者决定。

### 样例清单里各条的实际状态

清单是**样例**：每条的状态如下，别把「在清单里」等同于「支持」或「已测」。
支持范围由引擎契约决定（[danbooru-api.md](danbooru-api.md)、[moebooru-api.md](moebooru-api.md)、
[serika-api.md](serika-api.md)、[e621-api.md](e621-api.md)）。

| 键 | 引擎 | 本轮线上状态 |
| :--- | :--- | :--- |
| `danbooru` | Danbooru | 匿名只读已实测（12 成功 + 3 预期错误） |
| `safebooru` | Danbooru | 匿名只读已实测：先是 6 个列表端点 `200`、`/post.json` 为 `404`，随后用客户端复测 16 个方法全 `200` 且形态与 `danbooru.donmai.us` 一致；它与 `danbooru` 同属 donmai 部署 |
| `konachan` | Moebooru | 匿名只读已实测（12 个列表端点 `200`；该站对部分网络会给 Cloudflare `403`，见 [verification.md](verification.md)） |
| `yandere` | Moebooru | 匿名只读已实测（同上） |
| `sakugabooru` | Moebooru | 匿名只读已实测（同上）；`api_version` 与 `hash_string` 取该站 `help/api` 自述 |
| `serika` | Serika | 见 [serika.md](serika.md) 与 [verification.md](verification.md) |
| `e621` | e621ng | 匿名只读已实测：三个示例逐方法 `200`，另有 `post_count`、原始 `posts` 信封、`md5`、`only`、`v2` 五类返回形态复核；`related_tag` 匿名 `403` |
| `e926` | e621ng | 匿名只读已实测：同一批示例在 e926 上同样 `200`，`post_count` 与 e621 同为 `240001` / `capped=true` |

### 怎么判断一个站点该用哪个类

**库不做自动识别**，也没有探测引擎的代码路径，更不会失败后自动换类重试：`Danbooru`、`Moebooru`、
`Serika`、`E621` 是四个并列的类，各自的传输、认证与参数编码按引擎写死，选错类不会有降级或回退。
判断依据是你自己持有的信息：**站点自述**（页脚、仓库、上游路由）加上**一次真实响应契约**。

**路径形态不足以判定引擎**：

* e621ng 与 Danbooru 都提供复数 `GET /posts.json`，两者都用 HTTP Basic（用户名 + API key）；
* 单数 `GET /post.json` 也不能证否：e621 上返回的 `403` 是**部署侧反脚本拦截页**（HTML，
  不是 JSON，上游源码里 `/post` 其实是一条旧的 `302` 重定向），把它当成 `404` 会得出错误的结论；
* 反过来，e621ng **没有** Danbooru 的 `/counts/posts.json` 路由（该请求在 e621 上是站点自己的 HTML
  `404`），计数走 `/posts/count.json`。所以「某个路径不存在」只能说明这一条路径，不能证明整个引擎。

判断时需要同时看站点自述与响应契约，实测对照：

| 观察 | Danbooru 引擎（`safebooru.donmai.us` / `danbooru.donmai.us`） | e621ng 引擎（`e621.net`） | Moebooru 引擎（`yande.re`） |
| :--- | :--- | :--- | :--- |
| `GET /posts.json?limit=1` | `200`，**裸数组** | `200`，`{"posts": [...]}` 信封 | `404` |
| 帖子字段 | `tag_string` / `file_url` / `media_asset` 等扁平字段 | 嵌套 `file` / `preview` / `sample` / `score` / `tags`，没有上述扁平字段 | 自有扁平字段 |
| 评级词表 | `rating:g` / `s` / `q` / `e` | 只有 `rating:s` / `q` / `e`，其余值（如 `rating:g`）被**静默丢弃**、不报错 | `rating:s` / `q` / `e`（全称在站点 `help/ratings` 页） |
| `GET /post.json?limit=1` | `404` | 部署侧反脚本页 `403`（HTML） | `200` |
| `GET /counts/posts.json` | `200`，`{"counts": ...}` | 站点自己的 HTML `404`（上游没有 `/counts` 路由，计数走 `/posts/count.json`） | 未测 |
| 认证 | username + api_key Basic | username + api_key Basic | `login` + `password_hash` 表单字段 |

站点的页脚与帮助页会自述引擎，这是最快的判据：本轮的探测里 e621 页脚写 `Running e621ng v.<版本>`，
三个 Moebooru 站写 `Running Moebooru 6.0.0`，`/help/api` 还给出该站自述的 API 版本与加盐模板。
不是每个站点都写全，所以仍要配合响应契约，不能只看一处。

Serika 是另一个独立引擎，没有 Rails 的 `posts` 路径，只有自己的 `/api/v1` 与站内 `/api/*`，
见 [serika.md](serika.md)。

选错类的表现是普通的 HTTP 错误或形状不对的返回，不会被库掩盖：拿 Danbooru 客户端请求 Moebooru 站点会得到
`404`（路径不存在）；拿 Danbooru 客户端请求 e621 站点能拿到 `200`，但正文是带 `posts` 信封的对象、
帖子字段也是 e621 自己的嵌套结构，客户端不做任何形状转换或补字段；凭据形态不匹配时是 `401`。这些都在
[errors.md](errors.md) 的异常模型里。

## `examples` 段

`examples` 段只服务于 `examples/` 目录下的可运行示例与文档片段：把**关键词、数量、ID**这类
调用参数放回配置文件，示例脚本本身不硬编码站点、代理和分页。

| 键 | 所属 | 说明 |
| :--- | :--- | :--- |
| `site` | 各家族 | 传给客户端构造函数的站点名，对应 `sites` 段的键 |
| `tags` | Danbooru / Moebooru | 搜索关键词（Moebooru 面作为顶层 `tags` 参数发送） |
| `limit` | Danbooru / Moebooru | 单页数量（服务端可能按端点自行限制或忽略，见 [moebooru-api.md](moebooru-api.md#分页与实际上限)） |
| `pages` | Danbooru / Moebooru | 编号分页示例的页码数组 |
| `preview_chars` | Danbooru / Moebooru | 正文显示长度（Danbooru 的 wiki 示例、Moebooru 的评论示例） |
| `tag_search` | Danbooru | 标签查询字典（Moebooru 面没有 `search[...]` 字典） |
| `tag_order` | Moebooru | `tag_list` 的 `order` 值，如 `count` |
| `comment_query` | Moebooru | 评论流查询词；空字符串表示不启用全文过滤 |
| `post_id` | Danbooru | 帖子 ID；只读示例改用列表返回的首个 ID（见 [danbooru.md](danbooru.md)），该键本身只服务写示例 `examples/danbooru/comment_create.py` |
| `comment_body` | Danbooru | 评论正文，同样只服务写示例 `examples/danbooru/comment_create.py`——它是**真实的 POST 写示例**，需要账号与 API key，本仓库不带凭据、**未执行、未实测** |
| `wiki_query` | Danbooru / Moebooru | wiki 页面查询词 |
| `wiki_title` | Danbooru / e621ng | wiki 页面标题（Moebooru 没有 JSON 的单页读取方法） |
| `related_query` / `related_category` / `related_order` | Danbooru | 相关标签查询参数 |
| `related_tags` / `related_type` | Moebooru | 相关标签查询的 `tags` 与 `type` 参数 |
| `search_sample_size` / `tag_sample_size` | Danbooru | 相关标签查询的样本规模 |
| `post_query` / `random_query` | e621ng | `post_list` / `post_random` 的顶层查询参数（`tags`、`limit`） |
| `tag_query` / `artist_query` / `comment_query` / `pool_query` / `note_query` / `wiki_query` | e621ng | 各资源 `*_list` 的字典参数；评论的 `group_by` 也在字典里 |
| `pause_seconds` | e621ng | 示例脚本两次调用之间的等待秒数，脚本自己 sleep |

e621ng 段没有 `tags` / `limit` / `pages` 这些散键：查询一律放在 `*_query` 字典里，示例脚本用 `**` 展开。
表中“Danbooru / Moebooru”项仅指这两个家族，Serika 与 e621ng 各自使用自己的查询字典配置。

Moebooru 示例读 `comment_query`（评论流查询词，空串表示不做全文过滤）与 `preview_chars`（正文截断长度）；
Danbooru 示例读 `comment_body`。两者都可以按自己的脚本增删。

示例脚本的用法：

```bash
.venv/Scripts/python.exe examples/danbooru/list_posts.py
.venv/Scripts/python.exe examples/danbooru/list_posts.py --config config/sites.json --site safebooru
.venv/Scripts/python.exe examples/e621/list_posts.py --site e926
```

`--config` 指定配置文件路径，省略即读包内默认的那份；`--site` 显式覆盖站点名（省略该选项则取
`examples.<段>.site`，e621 示例默认取 `examples.e621.site`）。
两者都只用命令行参数，不使用环境变量。

## 显式覆盖

构造函数参数优先于配置文件中的同名值，方便在不改配置文件的前提下临时切换：

```python
from anybooru import Danbooru

client = Danbooru(
    'danbooru',
    config_file='config/sites.json',
    site_url='https://safebooru.donmai.us',
    username='your-username',
    api_key='your-api-key',
    proxies={'http': 'http://proxy.example:8080', 'https': 'http://proxy.example:8080'},
    timeout=10,
    user_agent='MyApp/1.0',
)
```

## 加载后的配置

客户端把解析结果保存在公开属性 `config` 上，可以随时查看实际生效的配置：

```python
client = Danbooru('danbooru')

client.config['request']['timeout']              # 30
client.config['sites']['danbooru']['url']        # https://danbooru.donmai.us
client.config['examples']['danbooru']['tags']    # rating:g
```

## `verification` 段

维护者做线上接口验证的脚本会在配置中额外使用一个 `verification` 段，它不是公开 API 的一部分，
普通使用者不需要配置，文档也不对其逐键说明；Serika 与 e621ng 两个子段分别给这两轮验证列出要跑的
示例、站点与调用间隔，具体命令见 [verification.md](verification.md)。
