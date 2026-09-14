# 根配置文件 `pybooru.json`

Pybooru 的所有可调参数——站点地址、凭据、代理、超时、User-Agent、示例参数——集中放在一份
JSON 文件里。

设计上只认这一份**显式文件**：

* 没有环境变量输入；
* 没有隐藏的搜索路径：库**不会**去包安装目录、site-packages、用户目录或任何其他位置找它；
* 没有内置站点后备，也不会因为站点名未知就悄悄换一个地址。

## 文件放在哪里

`config_file` 参数的默认值是**当前工作目录**下的 `pybooru.json`。因此有两种用法：

1. **把 `pybooru.json` 复制到你自己的应用工作目录**（推荐，与脚本同级或在其启动目录下）；
2. 或者用 `config_file` 显式指向任意路径。

```python
from pybooru import Danbooru

client = Danbooru('danbooru')                                  # 读取当前工作目录的 pybooru.json
client = Danbooru('danbooru', config_file='pybooru.json')      # 等价，显式写全
client = Danbooru('danbooru', config_file='config/sites.json') # 指向别处
```

`pip install` 之后**不会**自动出现配置文件：sdist 里带了一份根样例 `pybooru.json`，你需要把它
放到工作目录，或把它所在路径交给 `config_file`。文件不存在时构造函数直接抛出 `FileNotFoundError`。

`Danbooru('danbooru')` 的第一个参数是 `sites` 段里的键名，不是 URL。

## 完整样例

完整、可直接复制的内容见仓库根的 [`pybooru.json`](../pybooru.json)（sdist 里也会带这份样例）。
它的结构如下（`sites` 段可以按需要增删站点；`verification` 段是维护者验证脚本专用的，普通使用者
可以省略）：

```json
{
  "request": {
    "timeout": 30,
    "proxies": { "http": "http://proxy-host:port", "https": "http://proxy-host:port" },
    "user_agent": "Pybooru/5.0.0.dev1"
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
    }
  },
  "examples": {
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
    }
  }
}
```

Serika 示例使用根样例中的 `examples.serika`，不与 Rails 两家的搜索语法混用：

| 键 | 用途 |
| :--- | :--- |
| `site` | 对应 `sites.serika`，也可改为自托管实例的站点键 |
| `image_query` | 站内图片列表查询，含 `page` / `limit` / CSV `ratings` / `sort` |
| `user_query` | 官方 v1 匿名用户目录查询，含 `page` / `limit` / `sort` |
| `tag_query` / `artist_query` | 站内标签、画师列表查询 |
| `random_size` | 匿名二进制图片路径的 `width` / `height` |
| `random_query` | 二进制图片的 `ratings` / `format` / `fit` 等查询值 |

站内详情示例从实际列表响应取得 `post_id`，不硬编码图片 ID。三个匿名示例的命令见
[serika.md](serika.md#可运行示例)。`verification.serika` 的 `scripts`、`pause_seconds`、
`evidence_file` 指定本轮逐一运行哪些示例、调用间隔与临时证据位置；请求输入仍来自 `examples.serika`。

## `request` 段

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `timeout` | number | 单次请求超时秒数，默认 `30`；写成数组时按 requests 的 (连接超时, 读取超时) 处理 |
| `proxies` | object | 传给 requests 的代理字典，键为 `http` / `https` |
| `user_agent` | string | 请求头 `User-Agent` |

## `sites` 段

每个键是一个站点名，值是**同一个名称**在客户端构造函数中引用到的配置。

这一段是**样例 / 起始清单，不是支持边界**：

* 库不读任何内置站点表，也不对站点名做白名单校验——`site_name` 在 `sites` 里查不到就
  直接 `KeyError`，不会回落到别的地址（`resources.py` 只做 `json.load`，`pybooru.py` 只做一次字典取值）；
* 名单外的站点只要跑同一套引擎，就能直接用：构造时传 `site_url`（Moebooru 还必须同时传
  `api_version`），完全绕开本段；
* 反过来，名单里的站点**不保证每个能力都可用**：站点自己会关闭部分功能、按权限裁剪返回内容，
  网络侧也可能只挡住你这条线路（例如 `konachan.com` 在某些网络上得到 Cloudflare 挑战页）。

支持范围由**引擎契约**决定，而不是由这份清单决定：Danbooru 引擎看
[danbooru-api.md](danbooru-api.md)，Moebooru 引擎看 [moebooru-api.md](moebooru-api.md)。
契约基线固定在本地的上游快照（`danbooru/` HEAD `d4cdddd44`、`moebooru/` HEAD `206455e1`），
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
| `hash_string` | string \| null | 该站点 `help/api` 页面约定的加盐模板，含 `{0}` 占位符；为 `null` 表示没有内置值，登录时需要显式提供 |
| `api_version` | string | 该站点声明的 API 版本，如 `1.13.0+update.3` |

> 凭据留空即可用于**只读**接口。请把填好的 `pybooru.json` 留在本地，不要提交真实账号与 key。

Serika 系站点（独立第三类引擎）：

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `url` | string | `serika.art` 或相同引擎的自托管根地址；无内置站点后备 |
| `api_key` | string | 非空时发送 `Authorization: Bearer <key>`；根样例为空，仅匿名访问 |

Serika 不使用 `username`、`password`、`hash_string` 或客户端路径版本开关。
`Serika('serika', config_file='pybooru.json')` 读取上述两项；自托管实例在 `sites` 中新增同结构条目。
官方 v1 的多数只读路由也需 key，空 key 不会被替换成占位符；本轮不申请凭据、不实测这些路由。
站内 cookie 登录不实现，详见 [authentication.md](authentication.md#serika-系站点)。

同一个站点名在 Danbooru、Moebooru、Serika 客户端中都表示 `sites` 段的键，选择哪个类由调用者决定。

### 样例清单里各条的实际状态

清单是**样例**：每条的状态如下，别把「在清单里」等同于「支持」或「已测」。
支持范围由引擎契约决定（[danbooru-api.md](danbooru-api.md)、[moebooru-api.md](moebooru-api.md)）。

| 键 | 引擎 | 本轮线上状态 |
| :--- | :--- | :--- |
| `danbooru` | Danbooru | 匿名只读已实测（12 成功 + 3 预期错误） |
| `safebooru` | Danbooru | 匿名只读已实测（`posts` / `tags` / `artists` / `comments` / `wiki_pages` / `pools` 均 `200`）；它与 `danbooru` 同属 donmai 部署，`safebooru.donmai.us/post.json` 为 `404`，路径形态确认是 Danbooru 引擎而非 Moebooru |
| `konachan` | Moebooru | 匿名只读已实测（12 个列表端点 `200`；该站对部分网络会给 Cloudflare `403`，见 [verification.md](verification.md)） |
| `yandere` | Moebooru | 匿名只读已实测（同上） |
| `sakugabooru` | Moebooru | 匿名只读已实测（同上）；`api_version` 与 `hash_string` 取该站 `help/api` 自述 |
| `serika` | Serika | 见 [serika.md](serika.md) 与 [verification.md](verification.md) |

原样例里的 `lolibooru`（`https://lolibooru.moe`）在本次复核中经两个出口都拿不到 HTTP 响应
（隧道 `502` 与 SSL 层 `UNEXPECTED_EOF_WHILE_READING`），已从清单移除。

### 怎么判断一个站点该用哪个类

**库不做自动识别**，也没有探测引擎的代码路径：`Danbooru`、`Moebooru`、`Serika` 是三个并列的类，
各自的传输、认证与参数编码按引擎写死，选错类不会有降级或回退。判断依据是你自己持有的信息——
引擎来源（站点页脚、仓库、上游路由）或一次探测。

两个 Rails 引擎的路径形态可以直接区分，实测结果：

| 探测 | Danbooru 引擎（`safebooru.donmai.us`） | Moebooru 引擎（`yande.re`） |
| :--- | :--- | :--- |
| `GET /posts.json?limit=1` | `200` | `404` |
| `GET /post.json?limit=1` | `404` | `200` |

即：复数 `posts` 是 Danbooru，单数 `post` 是 Moebooru。另外 Moebooru 站点通常能在
页脚看到 `Running Moebooru <版本>`、在 `/help/api`（需要 `Accept: text/html`）读到自述 API 版本与
加盐模板；Danbooru 用 `username` + `api_key` 走 HTTP Basic，Moebooru 用 `login` + `password_hash`
表单字段，从认证方式上也能反推。

选错类的表现是普通的 HTTP 错误，不会被库掩盖：拿 Danbooru 客户端请求 Moebooru 站点会得到
`404`（路径不存在），拿 Moebooru 客户端请求 Danbooru 站点同样 `404`；凭据形态不匹配时是
`401`。这些都在 [errors.md](errors.md) 的异常模型里。

## `examples` 段

`examples` 段只服务于 `examples/` 目录下的可运行示例与文档片段：把**关键词、数量、ID**这类
调用参数放回配置文件，示例脚本本身不硬编码站点、代理和分页。

| 键 | 所属 | 说明 |
| :--- | :--- | :--- |
| `site` | 三家 | 传给客户端构造函数的站点名，对应 `sites` 段的键 |
| `tags` | 两者 | 搜索关键词（Moebooru 面作为顶层 `tags` 参数发送） |
| `limit` | 两者 | 单页数量（服务端可能按端点自行限制或忽略，见 [moebooru-api.md](moebooru-api.md#分页与实际上限)） |
| `pages` | 两者 | 编号分页示例的页码数组 |
| `preview_chars` | 两者 | 正文显示长度（Danbooru 的 wiki 示例、Moebooru 的评论示例） |
| `tag_search` | Danbooru | 标签查询字典（Moebooru 面没有 `search[...]` 字典） |
| `tag_order` | Moebooru | `tag_list` 的 `order` 值，如 `count` |
| `comment_query` | Moebooru | 评论流查询词；空字符串表示不启用全文过滤 |
| `post_id` | Danbooru | 帖子 ID（示例优先改用列表返回的首个 ID，见 [danbooru.md](danbooru.md)） |
| `comment_body` | Danbooru | 评论正文示例 |
| `wiki_query` | 两者 | wiki 页面查询词 |
| `wiki_title` | Danbooru | wiki 页面标题（Moebooru 没有 JSON 的单页读取方法） |
| `related_query` / `related_category` / `related_order` | Danbooru | 相关标签查询参数 |
| `related_tags` / `related_type` | Moebooru | 相关标签查询的 `tags` 与 `type` 参数 |
| `search_sample_size` / `tag_sample_size` | Danbooru | 相关标签查询的样本规模 |

表中其余“两个/两者”项仅指 Danbooru 与 Moebooru；Serika 使用上面的查询字典配置。

Moebooru 示例读 `comment_query`（评论流查询词，空串表示不做全文过滤）与 `preview_chars`（正文截断长度）；
Danbooru 示例读 `comment_body`。两者都可以按自己的脚本增删。

示例脚本的用法：

```bash
.venv/Scripts/python.exe examples/danbooru/list_posts.py
.venv/Scripts/python.exe examples/danbooru/list_posts.py --config pybooru.json --site danbooru
```

`--config` 指定配置文件路径，`--site` 显式覆盖站点名（留空则取 `examples.<段>.site`）。两者都只用
命令行参数，不使用环境变量。

## 显式覆盖

构造函数参数优先于配置文件中的同名值，方便在不改配置文件的前提下临时切换：

```python
from pybooru import Danbooru

client = Danbooru(
    'danbooru',
    config_file='pybooru.json',
    site_url='https://safebooru.donmai.us',
    username='your-username',
    api_key='your-api-key',
    proxies={'http': 'http://proxy-host:port', 'https': 'http://proxy-host:port'},
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
普通使用者不需要配置，文档也不对其逐键说明。
