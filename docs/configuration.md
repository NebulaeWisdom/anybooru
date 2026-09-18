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

要改站点、凭据或代理，把那份文件复制成自己的，再把路径交给 `config_file`。下面这段可以直接执行，
它先看一眼包内那份的位置，再复制一份到当前目录并改成自己的名字（复制出来的文件不包含任何凭据，
默认就是匿名配置）：

```python
import shutil
from anybooru import Danbooru, DEFAULT_CONFIG_FILE

print(DEFAULT_CONFIG_FILE)                              # 包内默认配置的绝对路径

shutil.copy(DEFAULT_CONFIG_FILE, 'my-anybooru.json')    # 复制一份到当前目录改

with Danbooru('danbooru') as client:                    # 读包内默认配置
    print(client.site_url)                              # https://danbooru.donmai.us

with Danbooru('danbooru', config_file='my-anybooru.json') as client:  # 读自己那份，相对路径按当前工作目录解析
    print(client.timeout)                               # 30
```

包内默认文件的绝对路径也可以直接从 `anybooru.DEFAULT_CONFIG_FILE` 读（editable 安装时它就是仓库里的
`anybooru/anybooru.json`，改动立即生效）。`config_file` 指到的文件不存在时构造函数直接抛出
`FileNotFoundError`，**不会**退回到包内那份，也不会退回到内置站点。

构造函数的第一个参数是 `sites` 段里的键名（例如 `Danbooru('danbooru')` 里的 `'danbooru'`），
不是 URL；要用配置里没有的站点，传 `site_url`。

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
    "e926": { "url": "https://e926.net", "username": "", "api_key": "" },
    "zerochan": { "url": "https://www.zerochan.net" },
    "gelbooru": { "url": "https://gelbooru.com", "api_key": "", "user_id": "" }
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
    },
    "zerochan": {
      "site": "zerochan",
      "entry_query": {"p": 1, "l": 2, "s": "id"},
      "tag_query": {"tags": "Genshin Impact", "l": 2},
      "multi_tag_query": {"tags": ["Lumine", "Flower"], "l": 2},
      "strict_query": {"tags": "Genshin Impact", "strict": true, "l": 2},
      "entry_id": 3793685,
      "pause_seconds": 1.2
    },
    "gelbooru": {
      "site": "gelbooru",
      "autocomplete_query": {"term": "blue", "type": "tag", "limit": 3}
    }
  }
}
```

四类“查询整块放进字典”的家族（Serika / e621ng / Zerochan / Gelbooru）各有几个容易踩的点，键与对应调用见下文
[`examples` 段](#examples-段)的总表：

* **Serika**：查询值是逗号分隔的字符串（`ratings='safe'`），不是 Rails 数组；站内详情示例从列表响应里取
  `post_id` 再查，不硬编码图片 ID。三个匿名示例的命令见 [serika.md](serika.md#可运行示例)。
* **e621ng**：查询参数是 Rails 顶层参数与 `search[...]`；`wiki_title` 是 `wiki_page_show` 的标题或 ID，
  像 `help:api` 这样含冒号的标题由客户端转义。三个匿名示例的命令见 [e621.md](e621.md)。
* **Zerochan**：`tags` 进 URL 路径（传字符串是单标签，传数组把各标签名转义后逗号连接），
  其余单字母参数进查询串；`d`（尺寸）、`t`（人气取样窗口）、`c`（颜色）等可选值同样放在字典里
  原样发给服务端，配置里没有默认值。两个匿名示例的命令见 [zerochan.md](zerochan.md#可运行示例)。
* **Gelbooru**：只有 `autocomplete` 能匿名跑（已实测 `200`，返回建议数组，`limit` 不决定条数）；
  配置键 `autocomplete_query` 里的 `term` / `type` / `limit` 就是字面实参；dapi 的 5 个方法需要该站账号的
  `api_key` 与 `user_id`，本仓库没有凭据，没有对应示例。
  一个匿名示例的命令见 [gelbooru.md](gelbooru.md)。

`examples.*` 只服务示例脚本；`verification.*` 是维护者验证脚本的输入，两者互不替代（见下节）。

## `request` 段

这三个键对所有家族生效；构造函数同名参数（`timeout=` / `proxies=` / `user_agent=`）会给单个客户端覆盖它们。

| 键 | 类型 | 取值 | 含义 | 包内那份的值 | 抄得走的例子 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `timeout` | number 或 number 数组 | 正数秒数；写成两元素数组时是 `[连接超时, 读取超时]` | 单次请求最多等多久，超时抛 `requests.Timeout`（本库不包装网络异常） | `30` | `10` 或 `[5, 30]` |
| `proxies` | object | 键为 `http` / `https`，值是代理地址 | 传给 requests 的代理；会话设了 `trust_env=False`，所以只认这里的值，不读 `HTTP_PROXY` 之类的环境变量 | `{}`（直连） | `{"http": "http://proxy.example:8080", "https": "http://proxy.example:8080"}` |
| `user_agent` | string | 任意字符串 | 每个请求的 `User-Agent` 头 | `Anybooru/0.1.0.dev1` | `"MyProject - MyZerochanUsername"` |

这三个键都被直接读取：自己那份配置里删掉任何一个键，构造客户端时会抛 `KeyError`，不会回落到别的值。
请求头里的 `Accept` 固定是 `application/json`，配置里改不了。

## `sites` 段

`sites` 段的键就是构造客户端时传的第一个参数：`Danbooru('danbooru')` 读的是 `sites.danbooru` 这个条目，
`Moebooru('yandere')` 读 `sites.yandere`，以此类推。

这一段是**样例 / 起始清单，不是支持边界**：

* 库不读任何内置站点表，也不对站点名做白名单校验——`site_name` 在 `sites` 里查不到就
  直接 `KeyError`，不会回落到别的地址（`resources.py` 只做 `json.load`，`anybooru.py` 只做一次字典取值）；
* 名单外的站点只要跑同一套引擎，就能直接用：构造时传 `site_url`（Moebooru 还必须同时传
  `api_version`），完全绕开本段；
* 反过来，名单里的站点**不保证每个能力都可用**：站点自己会关闭部分功能、按权限裁剪返回内容，
  网络侧也可能只挡住你这条线路（例如 `konachan.com` 在某些网络上得到 Cloudflare 挑战页）。

支持范围由**各引擎自己的接口规则**决定，而不是由这份清单决定：Danbooru 引擎看
[danbooru-api.md](danbooru-api.md)，Moebooru 引擎看 [moebooru-api.md](moebooru-api.md)，
Serika 引擎看 [serika-api.md](serika-api.md)，e621ng 引擎看 [e621-api.md](e621-api.md)，
Zerochan 看 [zerochan-api.md](zerochan-api.md)，Gelbooru 看 [gelbooru-api.md](gelbooru-api.md)。
比对基线固定在本地的上游快照（`danbooru/` HEAD `d4cdddd44`、`moebooru/` HEAD `206455e1`、
`Serika.art/` HEAD `ef11dd12`、`e621ng/` HEAD `7a9c98851`），
所以**同引擎也可能漂移**：站点跑的是更老或改过的分支时，个别端点的参数、权限与响应形态可能不同，
本库实现的是那份上游规则，而不是某个站点的私有行为。按需增删站点键是正常用法，把清单当成“只支持这些站”会误判。

Zerochan 与 Gelbooru 是这条规则的**例外**：前者没有可引用的公开引擎源码；后者本轮没有找到能核对当前部署的
官方 PHP 快照，也未对比其它部署。Zerochan 依据是**官方 API 页面快照加实测**，Gelbooru 是**官方 wiki/帮助页与站点脚本
加真实响应**；逐条出处与排除项分别见 [zerochan-contract-notes.md](zerochan-contract-notes.md) 与
[gelbooru-contract-notes.md](gelbooru-contract-notes.md)。

Danbooru 系站点（Danbooru 引擎）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 请求都拼在这个地址后面；结尾多余的 `/` 会被去掉。例子 `"https://danbooru.donmai.us"` |
| `username` | string，登录名 | 只读匿名访问时留 `""`。例子 `"your-username"` |
| `api_key` | string | 站点个人设置页生成的 API key；没有就留 `""`。例子 `"your-api-key"` |

条目里这三个键都要在：客户端直接按名字取，缺哪个都会在构造时抛 `KeyError`。

> `username` 与 `api_key` **任一非空**就会给每个请求带上 HTTP Basic（用户名 + API key 作为密码）；
> 两项都为空才是匿名请求。只填一项不等同于匿名，服务端会返回 `401`。
> 见 [authentication.md](authentication.md#danbooru-系站点)。

Moebooru 系站点（Moebooru 引擎）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 例子 `"https://konachan.com"`；结尾多余的 `/` 会被去掉 |
| `username` | string，登录名 | 只读匿名访问时留 `""`。例子 `"your-username"` |
| `password` | string，明文密码 | 客户端自己算 `password_hash`，不会把明文发出去。例子 `"your-password"` |
| `hash_string` | string 或 `null` | 该站 `help/api` 页给出的加盐模板，含 `{0}` 占位符；例子 `"choujin-steiner--{0}--"`（yande.re）。写 `null` 表示条目没给，登录时必须在构造函数里显式传 |
| `api_version` | string，形如 `1.13.0+update.3` | 站点 `help/api` 标题里自述的版本，只用来决定列表路径形态（见下）。例子 `"1.13.0+update.3"` |

条目里这五个键也都要在（`hash_string` 可以是 `null`），缺键同样在构造时抛 `KeyError`。

> `username` 与 `password` 都留空即可用于**只读**接口；填了之后读请求也会带上认证字段。
> 请把填好的 `anybooru.json` 留在本地，不要提交真实账号与 key。

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
  现役三站都自述 `1.13.0+update.3`，因此用新形态；旧别名路由在新部署里仍然存在，但不再是上游列出的路径。

> 注意同名不同物：请求参数里的 `api_version='2'` 是**让帖子接口换成 v2 版返回结构**的开关
> （上游 `moebooru/app/controllers/post_controller.rb:338-362` 按它选另一套序列化），与上面这个站点
> 版本字符串无关，详见 [moebooru-api.md](moebooru-api.md)。

Serika 系站点（六家族中的独立 Next.js 引擎）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | `serika.art` 或同引擎的自托管实例。例子 `"https://serika.art"` |
| `api_key` | string | 以 `sk_serika_` 开头的官方 key；留 `""` 时不发 `Authorization` 头，只走匿名可达路由 |

Serika 条目只用这两个键：没有 `username`、`password`、`hash_string`、`api_version`。
自托管实例在 `sites` 里加一个同结构条目，把 `url` 换掉即可；没有内置站点后备，缺键同样抛 `KeyError`。
官方 v1 的大多数只读路由也要求 key，留空不会被替换成占位符；本轮不申请凭据，这些路由只对过源码。
浏览器 cookie 登录不实现，详见 [authentication.md](authentication.md#serika-系站点)。

e621ng 系站点（e621ng 引擎，e621.net 与 e926.net 是同一引擎的两套部署）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 例子 `"https://e621.net"`；安全内容站写 `"https://e926.net"` |
| `username` | string，登录名 | 只读匿名访问时留 `""`。例子 `"your-username"` |
| `api_key` | string | 账号设置页生成的 key，作为 HTTP Basic 的密码发送。例子 `"your-api-key"` |

与 Danbooru 条目同构（`username` 与 `api_key` 任一非空即带 Basic 头），但这是另一套引擎：
条目里没有 `password` / `hash_string` / `api_version`，客户端也没有路径版本开关。
是否只显示安全内容由站点部署配置决定（`safe_mode` 不在上游仓库默认值里），本库不替你补评级过滤。

Zerochan 系站点（Zerochan 站点自有的只读 JSON API，**没有上游引擎源码**）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 例子 `"https://www.zerochan.net"`；结尾多余的 `/` 会被去掉 |

**只有 `url` 一个字段**：`Zerochan` 构造时把共享传输的 `username` 置空，站点条目里没有 `username` /
`api_key` / `password` / `hash_string` / `api_version`，本库不读也不要求这些键。
API 页面要求请求头 `User-Agent` 含项目名与使用者自己的 Zerochan 用户名，这是**请求头约定而不是认证**：
它取自共享的 `request.user_agent`（默认 `Anybooru/0.1.0.dev1`），本库不校验、不代替使用者填写；
不满足时请求仍可能成功，但官方文档写明匿名项目有被封的风险。API 目前只读，条目里没有可用的凭据字段。
官方文档写明限流 60 请求/分钟，本库不做客户端限速，示例两次调用之间的间隔由 `examples.zerochan.pause_seconds` 给出。

Gelbooru 系站点（`index.php` 接口，本轮没有取得当前部署的官方 PHP 源码）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 所有请求都拼成 `<url>/index.php?page=…`。例子 `"https://gelbooru.com"` |
| `api_key` | string | 该站账号的 API key；**只加在 dapi 请求上**，留 `""` 表示没有。例子 `"your-api-key"` |
| `user_id` | string | 该站账号的编号，与 `api_key` 一起使用；同样只加在 dapi 请求上。例子 `"123456"` |

条目里这三个键都要在：客户端直接按名字取，缺哪个都会在构造时抛 `KeyError`。
`api_key` 与 `user_id` 都为空时请求就是匿名的：此时只有 `autocomplete` 这类页面脚本接口可用，
`page=dapi` 的五个方法已逐个实测匿名401、空正文，账号成功返回仍未实测。这两项与 Danbooru 的 `username` + `api_key`
不是同一套东西，不要照抄。

同一个站点名在所有客户端里都表示 `sites` 段的键（`Danbooru`、`Moebooru`、`Serika`、`E621`、`Zerochan`、
`Gelbooru`），选择哪个类由调用者决定。

### 样例清单里各条的实际状态

清单是**样例**：每条的状态如下，别把「在清单里」等同于「支持」或「已测」。
支持范围由各引擎自己的接口规则决定（[danbooru-api.md](danbooru-api.md)、[moebooru-api.md](moebooru-api.md)、
[serika-api.md](serika-api.md)、[e621-api.md](e621-api.md)、[zerochan-api.md](zerochan-api.md)、
[gelbooru-api.md](gelbooru-api.md)）。

| 键 | 引擎 | 本轮线上状态 |
| :--- | :--- | :--- |
| `danbooru` | Danbooru | 匿名只读已实测（12 成功 + 3 预期错误） |
| `safebooru` | Danbooru | 匿名只读已实测：先是 6 个列表端点 `200`、`/post.json` 为 `404`，随后用客户端复测 16 个方法全 `200` 且形态与 `danbooru.donmai.us` 一致；它与 `danbooru` 同属 donmai 部署 |
| `konachan` | Moebooru | 匿名只读已实测（12 个列表端点 `200`；该站对部分网络会给 Cloudflare `403`，见 [verification.md](verification.md)） |
| `yandere` | Moebooru | 匿名只读已实测（同上） |
| `sakugabooru` | Moebooru | 匿名只读已实测（同上）；`api_version` 与 `hash_string` 取该站 `help/api` 自述 |
| `serika` | Serika | 官方 v1 的 4 个匿名可达方法与部分站内读方法已实测；需 key 的 12 个 v1 方法未实测，见 [serika.md](serika.md) 与 [verification.md](verification.md) |
| `e621` | e621ng | 匿名只读已实测：三个示例逐方法 `200`，另有 `post_count`、原始 `posts` 结构、`md5`、`only`、`v2` 五类返回形态复核；`related_tag` 匿名 `403` |
| `e926` | e621ng | 匿名只读已实测：同一批示例在 e926 上同样 `200`，`post_count` 与 e621 同为 `240001` / `capped=true` |
| `zerochan` | Zerochan | 见 [zerochan.md](zerochan.md) 与 [verification.md](verification.md)；本家族没有上游源码，状态按官方 API 页面快照与真实请求记录，不按源码对齐 |
| `gelbooru` | Gelbooru | 补全九种type的非空结果全部为tag建议，limit=3可回10条；五个dapi方法匿名均401空正文、账号成功返回未实测；HTML14项200、CDN三项初始302。逐条见[扩展记录](verification.md#gelbooru有界匿名扩展实测2026-09-18)，来源见[契约附注](gelbooru-contract-notes.md) |

### 怎么判断一个站点该用哪个类

**库不做自动识别**：`Danbooru`、`Moebooru`、`Serika`、`E621`、`Zerochan`、`Gelbooru` 是六个并列的类，各自的
传输方式、认证形态与参数拼法按各自引擎写死；选错类不会自动降级，也不会失败后换成另一个类重试。
判断依据只能是你自己手里的信息：**站点自述**（页脚、帮助页、API 页面、上游仓库）加上**发一次请求看响应**
（Zerochan 这类没有上游源码的站点，只能靠官方 API 页面与实测响应）。

**光看路径形态不足以判断引擎**：

* e621ng 与 Danbooru 都提供复数 `GET /posts.json`，两者都用 HTTP Basic（用户名 + API key）；
* 单数 `GET /post.json` 也不能证否：e621 上返回的 `403` 是**部署侧反脚本拦截页**（HTML，
  不是 JSON；上游源码里 `/post` 其实是一条旧的 `302` 重定向），把它当成 `404` 会得出错误的结论；
* 反过来，e621ng **没有** Danbooru 的 `/counts/posts.json` 路由（该请求在 e621 上是站点自己的 HTML
  `404`），计数走 `/posts/count.json`。所以「某个路径不存在」只能说明这一条路径，不能证明整个引擎。

判断时需要同时看站点自述与响应内容，实测对照：

| 观察 | Danbooru 引擎（`safebooru.donmai.us` / `danbooru.donmai.us`） | e621ng 引擎（`e621.net`） | Moebooru 引擎（`yande.re`） |
| :--- | :--- | :--- | :--- |
| `GET /posts.json?limit=1` | `200`，正文直接是数组 `[{"id": …}]`，没有外层对象 | `200`，正文是对象 `{"posts": [{"id": …}]}` | `404` |
| 帖子字段 | `tag_string` / `file_url` / `media_asset` 等扁平字段 | 嵌套 `file` / `preview` / `sample` / `score` / `tags`，没有上述扁平字段 | 自有扁平字段 |
| 评级词表 | `rating:g` / `s` / `q` / `e` | 只有 `rating:s` / `q` / `e`，其余值（如 `rating:g`）被**静默丢弃**、不报错 | `rating:s` / `q` / `e`（全称在站点 `help/ratings` 页） |
| `GET /post.json?limit=1` | `404` | 部署侧反脚本页 `403`（HTML） | `200` |
| `GET /counts/posts.json` | `200`，正文是 `{"counts": …}` | 站点自己的 HTML `404`（上游没有 `/counts` 路由，计数走 `/posts/count.json`） | 未测 |
| 认证 | username + api_key 走 HTTP Basic | username + api_key 走 HTTP Basic | 表单字段 `login` + `password_hash` |

站点的页脚与帮助页会自述引擎，这是最快的判据：本轮的探测里 e621 页脚写 `Running e621ng v.<版本>`，
三个 Moebooru 站写 `Running Moebooru 6.0.0`，`/help/api` 还给出该站自述的 API 版本与加盐模板。
不是每个站点都写全，所以仍要配合响应内容，不能只看一处。

Serika 又是另一套路径：没有 Rails 的 `posts`，只有官方 `/api/v1/...` 与前端自用的 `/api/...`，
见 [serika.md](serika.md)。

Zerochan 的路径也是站点自己的：根路径 `/?p=1&json`（全部条目）、`/<标签>?json`（单标签）、
`/<标签A>,<标签B>?json`（多标签）与 `/<id>?json`（单条目详情）。要 JSON 必须在查询串里带 `json` 标记——
同一个 `/<id>` 不带 `json` 时返回的是 **HTML 页面**，所以「路径存在」不能说明拿到了 JSON。
它也没有 Rails 的 `posts` 路径，更没有上游源码可对照，只能看官方 API 页面与实测响应，
见 [zerochan.md](zerochan.md)。

Gelbooru 的路径固定是 `index.php`，接口由 `page` 参数选择：`page=dapi`（再加 `json=1`）是站点的 dapi，
需要账号；`page=autocomplete2` 是站点页面脚本用的自动补全接口，**返回 JSON 且匿名即可用**；
`page=tags/post/wiki` 等浏览路由返回给人看的 **HTML**。本库只包装上述两个 JSON
入口，不把 HTML 页面当 JSON 使用，也没有抓取页面的方法：`post_list` / `tag_list` / `user_list` /
`comment_list` / `post_deleted` 属于 dapi，需要该站账号；`autocomplete` 匿名可达，见 [gelbooru.md](gelbooru.md)。

选错类的表现是普通的 HTTP 错误或字段对不上的返回，不会被库掩盖：拿 Danbooru 客户端请求 Moebooru 站点会得到
`404`（路径不存在）；拿 Danbooru 客户端请求 e621 站点能拿到 `200`，但正文是 `{"posts": [ … ]}` 这种外面包了
一层的对象、帖子字段也是 e621 自己的嵌套结构，客户端不转换结构、不补字段；凭据形态不匹配时是 `401`。这些都在
[errors.md](errors.md) 的异常模型里。

## `examples` 段

`examples` 段只服务于 `examples/` 目录下的示例脚本：把关键词、数量、ID 这类调用参数放回配置，
脚本自己不硬编码站点、代理和分页。脚本把键读出来之后，发出的调用就是下表的最后一列——照抄那一列即可，
不需要配置文件，也不需要先读示例源码：

| 家族 | 配置键（包内样例值） | 脚本最终发出的字面调用 |
| :--- | :--- | :--- |
| Danbooru | `site` = `"danbooru"` | `Danbooru('danbooru')` |
| Danbooru | `tags` = `"rating:g"`、`limit` = `3` | `client.post_list(tags='rating:g', limit=3)`，打印每帖的 `id` / `rating` / `tag_string` |
| Danbooru | `pages` = `[1, 2]` | `client.post_list(tags='rating:g', page=1, limit=3)`，第二页把 `page` 换成 `2`；再取当前页末项的 id 用 `page='b<id>'` 往旧帖翻 |
| Danbooru | `tag_search` = `{"order": "count"}`、`limit` = `3` | `client.tag_list(search={'order': 'count'}, limit=3)`，打印 `name` / `post_count` |
| Danbooru | `wiki_title` = `"help:api"`、`preview_chars` = `200` | `client.wiki_page_show('help:api')`，打印 `title` 与截断到 200 字的 `body` |
| Danbooru | `related_query` = `"touhou"`、`related_category` = `0`、`related_order` = `"frequency"`、`search_sample_size` = `1000`、`tag_sample_size` = `100` | `client.related_tag(search={'query': 'touhou', 'category': 0, 'order': 'frequency', 'search_sample_size': 1000, 'tag_sample_size': 100}, limit=3)` |
| Danbooru | `post_id` = `1`、`comment_body` = `"示例评论"` | `client.comment_create(post_id=1, body='示例评论')`——**真实的 POST 写操作**，需要账号与 API key，本仓库不带凭据、**未执行、未实测** |
| Moebooru | `site` = `"yandere"` | `Moebooru('yandere')` |
| Moebooru | `tags` = `"rating:s"`、`limit` = `3`、`pages` = `[1, 2]` | `client.post_list(tags='rating:s', page=1, limit=3)`（GET `/post.json?tags=rating%3As&page=1&limit=3`），打印 `id` / `file_url` |
| Moebooru | `limit` = `3`、`tag_order` = `"count"` | `client.tag_list(limit=3, order='count')`（GET `/tag.json?limit=3&order=count`），打印 `name` / `count` |
| Moebooru | `wiki_query` = `"touhou"`、`limit` = `3` | `client.wiki_list(query='touhou', limit=3)`，打印命中页面的 `title` |
| Moebooru | `comment_query` = `""`、`limit` = `3`、`preview_chars` = `120` | `client.comment_search('')`（空词表示不做全文过滤），先打印真实条数，再打印前 3 条评论的 `id` / `post_id` 与正文前 120 字 |
| Moebooru | `related_tags` = `"touhou"`、`related_type` = `"general"` | `client.tag_related(tags='touhou', type='general')`，返回 `{"touhou": [["标签名", 共现次数], …]}` |
| Serika | `site` = `"serika"` | `Serika('serika')` |
| Serika | `image_query` = `{"page":1,"limit":3,"ratings":"safe","sort":"newest"}` | `client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')`（GET `/api/images?page=1&limit=3&ratings=safe&sort=newest`） |
| Serika | `user_query` = `{"page":1,"limit":1,"sort":"newest"}` | `client.user_list(page=1, limit=1, sort='newest')`（官方 v1，匿名可达） |
| Serika | `tag_query` = `{"limit":3}` | `client.internal_tag_list(limit=3)`（GET `/api/tags?limit=3`） |
| Serika | `artist_query` = `{"page":1,"limit":3}` | `client.internal_artist_list(page=1, limit=3)`（GET `/api/artists?page=1&limit=3`） |
| Serika | `random_size` = `{"width":400,"height":400}`、`random_query` = `{"ratings":"safe","format":"png","fit":"cover"}` | `client.random_image(width=400, height=400, ratings='safe', format='png', fit='cover')`，返回 `bytes`，脚本只打印字节数与响应头 |
| e621ng | `site` = `"e621"` | `E621('e621')`；把站点名换成 `'e926'` 即安全内容镜像站 |
| e621ng | `post_query` = `{"tags":"rating:s","limit":2}` | `client.post_list(tags='rating:s', limit=2)` |
| e621ng | `random_query` = `{"tags":"rating:s"}` | `client.post_random(tags='rating:s')` |
| e621ng | `tag_query` / `artist_query` / `pool_query` / `note_query` / `wiki_query` = 各自的 `{"limit": 2}`；`comment_query` = `{"group_by":"comment","limit":2}` | `client.tag_list(limit=2)`、`client.artist_list(limit=2)`、`client.pool_list(limit=2)`、`client.note_list(limit=2)`、`client.wiki_page_list(limit=2)`、`client.comment_list(group_by='comment', limit=2)`；每类再取首项详情（`tag_show` / `artist_show` / …） |
| e621ng | `wiki_title` = `"help:api"` | `client.wiki_page_show('help:api')`，标题里的冒号由客户端转义 |
| e621ng | `pause_seconds` = `1` | `time.sleep(1)`，脚本自己等，库不做限速 |
| Zerochan | `site` = `"zerochan"` | `Zerochan('zerochan')` |
| Zerochan | `entry_query` = `{"p":1,"l":2,"s":"id"}` | `client.entry_list(p=1, l=2, s='id')`，打印每条的 `id` / `tag` / `width` / `height` |
| Zerochan | `tag_query` = `{"tags":"Genshin Impact","l":2}` | `client.entry_list(tags='Genshin Impact', l=2)`（路径编码成 `Genshin+Impact`） |
| Zerochan | `multi_tag_query` = `{"tags":["Lumine","Flower"],"l":2}` | `client.entry_list(tags=['Lumine', 'Flower'], l=2)`（路径编码成 `Lumine,Flower`） |
| Zerochan | `strict_query` = `{"tags":"Genshin Impact","strict":true,"l":2}` | `client.entry_list(tags='Genshin Impact', strict=True, l=2)`（只匹配 primary 标签） |
| Zerochan | `entry_id` = `3793685` | `client.entry_show(3793685)`，打印 `id` / `primary` / `width` / `height` / `size` / `full` / `source` |
| Zerochan | `pause_seconds` = `1.2` | `time.sleep(1.2)`，脚本自己等，库不做限速 |
| Gelbooru | `site` = `"gelbooru"` | `Gelbooru('gelbooru')`（包内条目的 `api_key` / `user_id` 都为空，即匿名） |
| Gelbooru | `autocomplete_query` = `{"term":"blue","type":"tag","limit":3}` | `client.autocomplete('blue', type='tag', limit=3)`（GET `https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2`，实测 `200`），返回建议数组，每条含 `type` / `label` / `value` / `post_count` / `category`；脚本打印建议条数与每一条建议、`last_call` 的真实 URL 与状态码。**`limit` 不决定本次返回几条**：实测 `limit=3` 返回 10 条 |

两个约定：Danbooru 与 Moebooru 的示例读顶层散键（`tags` / `limit` / `pages`），
Serika、e621ng、Zerochan 与 Gelbooru 把查询整块放进 `*_query` 字典再展开；`comment_body` 只服务上面那条写操作，
只读示例用的是列表返回的第一个帖子 id。这些键都可以按自己的脚本增删。

示例脚本的用法：

```bash
.venv/Scripts/python.exe examples/danbooru/list_posts.py
.venv/Scripts/python.exe examples/danbooru/list_posts.py --config my-anybooru.json --site safebooru
.venv/Scripts/python.exe examples/e621/list_posts.py --site e926
.venv/Scripts/python.exe examples/zerochan/list_entries.py
.venv/Scripts/python.exe examples/zerochan/filter_entries.py
.venv/Scripts/python.exe examples/gelbooru/autocomplete.py
```

`--config` 指定配置文件路径，省略即读包内默认的那份（上面第一条就用包内那份；第二条换成自己复制出来的
`my-anybooru.json`，文件名与前文一致，你也可以取别的名字）；`--site` 显式覆盖站点名，省略时取
`examples.<段>.site`。两者都只用命令行参数，不使用环境变量。

## 显式覆盖

构造函数参数优先于配置文件里的同名值，所以不改配置文件也能临时换站点或换超时。每个构造参数覆盖什么：

| 构造参数 | 覆盖配置里的 | 字面例子 |
| :--- | :--- | :--- |
| `site_name` | 选 `sites` 段的哪个键 | `Danbooru('danbooru')` |
| `site_url` | `sites.<键>.url` | `Danbooru('danbooru', site_url='https://safebooru.donmai.us')` |
| `config_file` | 换成另一份 JSON | `Danbooru('danbooru', config_file='my-anybooru.json')` |
| `username` / `api_key` | `sites.<键>.username` / `.api_key`（Danbooru、E621） | `Danbooru('danbooru', username='your-username', api_key='your-api-key')` |
| `username` / `password` / `hash_string` / `api_version` | 同名的站点条目字段（Moebooru） | `Moebooru('yandere', api_version='1.13.0+update.3')` |
| `api_key` | `sites.<键>.api_key`（Serika） | `Serika('serika', api_key='sk_serika_…')` |
| `api_key` / `user_id` | `sites.<键>.api_key` / `.user_id`（Gelbooru；只随 dapi 请求发送） | `Gelbooru('gelbooru', api_key='your-api-key', user_id='123456')` |
| `timeout` / `proxies` / `user_agent` | `request` 段同名键（所有家族，含 Zerochan 的 `user_agent`） | `Zerochan('zerochan', user_agent='MyProject - MyZerochanUsername')` |

```python
from anybooru import Danbooru

with Danbooru(
        'danbooru',                                  # 站点名：取 sites.danbooru
        site_url='https://safebooru.donmai.us',      # 覆盖 url：换成另一套 Danbooru 部署
        timeout=10,                                  # 覆盖 request.timeout
        user_agent='MyProject/1.0',                  # 覆盖 request.user_agent
        proxies={'http': 'http://proxy.example:8080',
                 'https': 'http://proxy.example:8080'}) as client:
    print(client.site_url)                           # https://safebooru.donmai.us
    print(client.timeout)                            # 10
```

**注意**：只要传了站点名，客户端就会去 `sites` 段查一次，所以 `'danbooru'` 这样的键必须存在，否则构造时抛
`KeyError`——`site_url` 只是覆盖查到的地址，不会跳过这次查找。完全不用站点条目就省略第一个参数：
`Danbooru(site_url='https://safebooru.donmai.us')`（Moebooru 还必须同时传 `api_version`）。

## 加载后的配置

解析结果保存在公开属性 `config` 上（就是那份 JSON 的字典），可以随时查看实际生效的值：

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    print(client.timeout)   # 30：实际使用的超时秒数
    print(client.site_url)  # https://danbooru.donmai.us：实际访问的站点地址
    print(client.last_call)                               # {}，还没发过请求；发过之后是最近一次的 URL 与状态码
```

## `verification` 段

维护者做线上验证时用的一段输入，**不属于公开 API**，普通使用者可以整段删掉。它按家族分组，记录的是
“这次跑哪些脚本、发哪些请求、两次之间等多久”：

| 子段 / 键 | 内容 |
| :--- | :--- |
| `verification.serika` | `scripts` 是要跑的示例脚本，`pause_seconds` 是间隔；请求输入仍取 `examples.serika` |
| `verification.e621` | `sites` 决定在 `e621.net` 与 `e926.net` 各跑一遍，`scripts` 是要跑的示例，`pause_seconds` 是间隔；`post_query` / `count_query` / `v2_query` / `only_query` / `related_search` 是复核返回结构与权限分支用的输入 |
| `verification.zerochan` | `scripts` 是要跑的两个示例，`pause_seconds` 是间隔，`default_query` 是不带过滤的根路径查询，`entry_query` / `tag_query` / `multi_tag_query` / `strict_query` / `entry_id` 与 `examples.zerochan` 相同，`optional_queries` 逐条列出页码、排序窗口（`t`）、尺寸（`d`）与颜色（`c`）等可选参数 |
| Danbooru / Moebooru 的顶层与 `moebooru` 子段 | 正常查询（`post_tags` / `tag_search` / `artist_search` / `related_search` / `wiki_search`）、故意不存在的 id 与超界页码（`missing_post_id` / `invalid_page` / `invalid_tags` / `invalid_date`）等，用来核对错误路径 |

命令与真实结果一律记在 [verification.md](verification.md)，本文不重复。
