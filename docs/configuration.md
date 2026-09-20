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
都带这份文件），`sites` 段共 16 个条目。它的结构如下（`sites` 段可以按需要增删站点；`verification` 段是
维护者验证脚本专用的，普通使用者可以省略）：

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
    "gelbooru": { "url": "https://gelbooru.com", "api_key": "", "user_id": "" },
    "tbib": { "url": "https://tbib.org" },
    "shuushuu": { "url": "https://e-shuushuu.net", "username": "", "password": "", "access_token": "" },
    "sakuria": { "url": "https://sakuria-api.syarolia.com", "access_token": "" },
    "anime_pictures": { "url": "https://api.anime-pictures.net/api/v3", "authorization": "", "cookie": "" },
    "cosine": { "url": "https://pic.cosine.ren", "revalidate_secret": "" },
    "nhentai": { "url": "https://nhentai.net", "api_key": "" }
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
    },
    "gelbooru02": {
      "site": "tbib",
      "post_query": {"tags": "rating:safe", "pid": 0, "limit": 2},
      "tag_query": {"limit": 2},
      "comment_post_id": 1,
      "pause_seconds": 1.2
    },
    "shuushuu": {
      "site": "shuushuu",
      "search_query": {"q": "long hair", "limit": 5},
      "tag_title": "long hair",
      "image_query": {"tags_mode": "all", "tag_depth": 0, "per_page": 2, "sort_by": "favorites", "sort_order": "DESC"},
      "pages": [1, 2],
      "tag_id": 46,
      "comment_query": {"image_id": 1118862, "per_page": 2},
      "user_query": {"search": "whitekitten", "per_page": 2},
      "news_query": {"per_page": 1},
      "pause_seconds": 2.1
    },
    "sakuria": {
      "site": "sakuria",
      "illust_query": {"q": "blue", "size": 2, "sort": "new"},
      "pages": [1, 2],
      "illust_id": 70937229,
      "comment_query": {"page": 1, "size": 2},
      "pause_seconds": 1.2
    },
    "anime_pictures": {
      "site": "anime_pictures",
      "post_query": {"search_tag": "hatsune miku", "posts_per_page": 2, "order_by": "rating"},
      "pages": [0, 1],
      "post_id": 382872,
      "pause_seconds": 1.3
    },
    "cosine": {
      "site": "cosine",
      "list_query": {"pageSize": 2},
      "pages": [1, 2],
      "search_query": {"q": "初音", "limit": 2, "platform": "twitter", "r18": false, "sort": "create_time:desc"},
      "offsets": [0, 2],
      "artwork_id": 1,
      "tag": "GenshinImpact",
      "tag_query": {"start": 0, "limit": 2},
      "artist_query": {"platform": "pixiv", "authorid": "54390221", "page": 1, "pageSize": 2},
      "pause_seconds": 1.3
    },
    "nhentai": {
      "site": "nhentai",
      "pause_seconds": 1.3,
      "pages": [1, 2],
      "list_query": {"per_page": 2},
      "search_query": {"query": "language:english", "sort": "date", "page": 1},
      "gallery_id": 658856,
      "tag_type": "language",
      "tag_slug": "english",
      "tag_ids": "12227,6346",
      "comments_query": {"page": 1, "per_page": 2}
    }
  }
}
```

十类“查询整块放进字典”的家族（Serika / e621ng / Zerochan / Gelbooru / Gelbooru02 / Shuushuu / Sakuria / Anime-Pictures / Cosine / nhentai）各有几个容易踩的点，键与对应调用见下文
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
* **Gelbooru02（TBIB）**：`post_list` 默认返回 JSON 列表，`tags` / `pid` / `limit` 原样转发；
  想看 XML 原文要显式传 `response_format='xml'`（例如 `post_list(response_format='xml', id=28627190)`）。
  `tag_list` / `comment_list` 在成功时返回原文文本；删除流路由在 TBIB 上观测到 `500`，
  两个示例（`list_posts.py`、`browse_resources.py`）不调用删除流，只演示匿名成功路径，
  是否已执行以[验证记录](verification.md)为准。
* **Shuushuu**：公开读取默认匿名；`search(q='long hair')` 返回标签，`image_list(tags='46', per_page=2)` 才筛图。
  `tags` 用数字 ID 的英文逗号串，`+` 不是组合运算符；`tag_list` 每页数用 `per_page`，不使用 `limit`。
  两个示例都显式清空凭据，参数见下表与[客户端用法](shuushuu.md)。
* **Sakuria**：列表方法用 `page` / `size`；查询键与字面实参一一对应（`illust_query` 的 `q` / `size` / `sort`
  就是 `illust_search(q='blue', size=2, sort='new')` 的实参）。示例显式传 `access_token=''` 表示匿名：
  空串**不读**配置里的 token。这里的封面/头像地址是站内相对路径，示例只打印，不下载媒体；
  信封里的 `total` / `nextPage` 不是真页码（本轮实测），翻页只能手动递增 `page` 并按 `id` 去重，
  详见[分页](pagination.md#sakuria-的分页)。
* **Anime-Pictures**：`url` 是 **API 基址**（`https://api.anime-pictures.net/api/v3`），不是网页主机；
  `post_query` 的键就是 `posts_list(**post_query)` 的实参，`pages` 是 **0 起步**的页码数组（`[0, 1]`），
  示例用 `post_id` 调详情并以同一帖的 `user.id` / 首条评论 `comment.id` 继续查用户与评论。
  两个匿名示例的命令见 [anime-pictures.md](anime-pictures.md)；分页语义与实测出的取值边界见
  [分页](pagination.md#anime-pictures-的分页)。
* **Cosine**：`list_query` 是 `image_list(**list_query)` 的实参（`pageSize` 是驼峰），因此页码另放在
  `pages`；`search_query` 直接展开成 `search(**search_query)`，`offsets` 是给 `search(offset=…)` 的两个取值；
  `tag` / `tag_query` 对应 `tag_images(tag, **tag_query)`（标签必须完整、不带 `#`），`artist_query` 对应
  `artist_images(**artist_query)`；`artwork_id` 供 `artwork_show(1)`。示例显式传 `revalidate_secret=''`，
  即使配置里填了密钥也只发空串，且只有 `artwork_revalidate` 会用到它。命令见
  [cosine.md](cosine.md)。
* **nhentai**：`list_query` 就是 `gallery_list(**list_query)` 的实参（`{"per_page": 2}` → `gallery_list(per_page=2)`），
  页码另放在 `pages`；`search_query` 展开成 `search(**search_query)`（`query` 是站点的搜索表达式，必填，
  `sort` 只收 `date` / `popular` 与三个人气窗口），`gallery_id` 供 `gallery_show(658856)`，
  `tag_type` + `tag_slug` 供 `tag_show('language', 'english')`，`tag_ids` 是**英文逗号串**（`'12227,6346'`，
  客户端不做拼接、不改写），`comments_query` 展开成 `gallery_comments(**comments_query)`。
  站点的 `page` / `per_page` 由服务端规定取值范围与默认值（OpenAPI 里逐端点写明），客户端不钳位；
  每个端点各有匿名请求预算（例如 `GET /api/v2/galleries` 匿名 `15/1min per IP`），示例用
  `pause_seconds` 自己等，库不做限速也不重试。命令与参数表见 [nhentai.md](nhentai.md) 与
  [分页](pagination.md#nhentai-的分页)。

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
Zerochan 看 [zerochan-api.md](zerochan-api.md)，Gelbooru 看 [gelbooru-api.md](gelbooru-api.md)，
Gelbooru02（TBIB）看 [gelbooru02-api.md](gelbooru02-api.md)，Shuushuu 看 [shuushuu-api.md](shuushuu-api.md)，
Sakuria（站点自有 JSON API）看 [sakuria-api.md](sakuria-api.md)，
Anime-Pictures（站点自有的 `api/v3` JSON 接口）看 [anime-pictures-api.md](anime-pictures-api.md)，
Cosine（站点自有的 Next.js + Prisma + Meilisearch JSON API 与 `feed.xml`）看 [cosine-api.md](cosine-api.md)，
nhentai（站点自有的 `api/v2` JSON API）看 [nhentai-api.md](nhentai-api.md)。
比对基线固定在本地的上游快照（`danbooru/` HEAD `d4cdddd44`、`moebooru/` HEAD `206455e1`、
`Serika.art/` HEAD `ef11dd12`、`e621ng/` HEAD `7a9c98851`），
所以**同引擎也可能漂移**：站点跑的是更老或改过的分支时，个别端点的参数、权限与响应形态可能不同，
本库实现的是那份上游规则，而不是某个站点的私有行为。按需增删站点键是正常用法，把清单当成“只支持这些站”会误判。

Zerochan、Gelbooru 与 Gelbooru02 是这条规则的**例外**：Zerochan 没有可引用的公开引擎源码；Gelbooru 本轮没有
找到能核对当前部署的官方 PHP 快照，也未对比其它部署；Gelbooru02 有 TBIB 首页和 `index.php?page=help&topic=dapi`
帮助页与真实响应，没有服务端源码快照；版本只确认到站点自述 0.2。Zerochan 依据是**官方 API 页面
快照加实测**，Gelbooru 是**官方 wiki/帮助页与站点脚本加真实响应**，Gelbooru02 是**帮助页加匿名实测**；
逐条出处与排除项分别见 [zerochan-contract-notes.md](zerochan-contract-notes.md)、
[gelbooru-contract-notes.md](gelbooru-contract-notes.md) 与
[gelbooru02-contract-notes.md](gelbooru02-contract-notes.md)。
Shuushuu 同样没有本地上游服务端源码；依据是站点的 [OpenAPI](https://e-shuushuu.net/api/openapi.json)
与真实响应，不是 Danbooru/Moebooru 模板，详见[契约附注](shuushuu-contract-notes.md)。
Sakuria 比它们更弱一档：**既没有官方 API 页面，也没有 OpenAPI，也没有上游源码**，
依据只有匿名响应观察加随后的有界实测；样本之外的行为仍是候选，推断不构成返回值承诺，
出处与未实测边界见 [Sakuria 契约附注](sakuria-contract-notes.md)。
Anime-Pictures 同样没有任何**可读到的**正式来源：官方 API 手册页存在但整站受 Cloudflare 质询，命令行读不到；
没有 OpenAPI，也没有服务端源码。依据是匿名只读响应实测加候选输入资料（其中的外部客户端源码链接本轮没有
独立读过），未实测的参数边界与输入矛盾见 [Anime-Pictures 契约附注](anime-pictures-contract-notes.md)。
Cosine 也没有本地上游服务端源码：站点前端代码在公开仓库里，本轮只按需只读了个别文件当线索（不 clone、
不写行号），公开结论以匿名只读响应为准，未实测项见 [Cosine 契约附注](cosine-contract-notes.md)。
nhentai 同样没有本地上游服务端源码：依据是站点自己发布的 OpenAPI 文档
（`GET https://nhentai.net/api/v2/openapi.json`，OpenAPI 3.1.0，`info.version` 为 `2.0.0+14bccf7`，
98 条路径 / 114 个操作）与真实响应，不是 Danbooru/Moebooru 模板；出处与排除项见
[nhentai 契约附注](nhentai-contract-notes.md)。

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

Serika 系站点（独立 Next.js 引擎）：

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

Gelbooru02（TBIB）站点（站点自述 `Running Gelbooru 0.2`，**没有服务端源码快照**）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 所有请求都拼成 `<url>/index.php?page=…`。例子 `"https://tbib.org"` |

**只有 `url` 一个字段**：`Gelbooru02` 没有内置认证功能，默认匿名请求；
站点条目没有 `api_key` / `user_id` / `username` / `password`。账号路径不在本轮实测范围。
它与 `gelbooru`（`gelbooru.com`）不是同一套接口：TBIB 上帖子可选 JSON，标签与评论只返回 XML 文本，
详见 [gelbooru02.md](gelbooru02.md) 与
[gelbooru02-contract-notes.md](gelbooru02-contract-notes.md)。

Shuushuu 站点（独立 REST API，公开读取默认匿名）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | `"https://e-shuushuu.net"`，原生方法自行带 `/api/v1` |
| `username` | string，默认 `""` | 仅显式 `auth_login()` 时读取；例如 `"your-username"`，构造不登录 |
| `password` | string，默认 `""` | 同上，仅显式登录时作为 JSON 密码发送；不进 URL |
| `access_token` | string，默认 `""` | 非空时发送 `Authorization: Bearer <token>`；不是永久 API key |

调用方显式给出的构造参数优先，`None` 读取对应配置。填写用户名/密码不会自动换取 token；
refresh token 只保存在同一个客户端会话的 Cookie 中，不存在配置字段或自动刷新任务。
公开图片、标签、评论与用户资料不需要这些凭据，个人数据与写操作才需要登录。认证方法的调用方式及边界见
[Shuushuu 用法](shuushuu.md)。

Sakuria 站点（Pixiv 第三方镜像站，站点自有的只读 JSON API，**没有官方页面、OpenAPI 或上游源码**）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 填 **API 主机**，不是网页主机；例子 `"https://sakuria-api.syarolia.com"` |
| `access_token` | string，默认 `""` | 非空时给每个请求加 `Authorization: Bearer <token>`；留空即匿名 |

条目只用这两个键：没有 `username`、`password`、`api_key`、`user_id`，构造签名里也没有用户名。
是否带认证头由这一项决定，客户端不做本地权限判断、不在 `401` 后退回匿名。
所有方法原样返回站点给的**完整 JSON**（不剥信封、不改字段名、不做格式嗅探），非 2xx 走共享异常，
`last_call` 记录最近一次请求的真实 URL 与状态码；`request(method, path, ...)` 是同一套出口。
包内 `access_token` 为空；本类不提供登录、注册、换取或刷新 token 的方法，也不索要账号密码。
17 个 `me*` 方法按账号读取封装，成功返回结构未实测（本轮只请求过 `/me/likes`）；差异与边界见
[authentication.md](authentication.md) 与
[Sakuria 契约附注](sakuria-contract-notes.md)。
响应里的图片地址按原样返回：本轮看到的用户头像、横幅是站内相对路径（形如 `/img/...`），
要完整地址就自己拼上 `site_url`；本库只返回路径文本，**不下载媒体**。候选输入提到「缺图会回 `200`
加 `image/svg+xml` 占位图而不是 `404`」，本轮没有请求任何媒体，这条未复测。

Anime-Pictures 站点（自研 `api/v3` JSON 接口，**没有可读到的官方手册页、OpenAPI 或上游源码**）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，**API 基址** | 不是网页主机；例子 `"https://api.anime-pictures.net/api/v3"` |
| `authorization` | string，默认 `""` | 非空时按**原值**作为 `Authorization` 头发送；库不加 `Bearer`、不改写，scheme 未实测 |
| `cookie` | string，默认 `""` | 非空时按**原值**作为 `Cookie` 头发送；库不猜 cookie 名、不拼接，也不替你登录 |

条目只用这三个键：没有 `username`、`password`、`api_key`、`user_id`。是否发送凭据由这两项决定，
显式传空串（`authorization=''` / `cookie=''`）表示本次客户端匿名、**不读**配置里的值；`None`（或不传）才读配置。
客户端不做本地权限判断、不在 `401` / `403` 后退回匿名，也不提供登录、注册或刷新方法。
本轮 10 个 GET 有匿名成功样本；`post_tags` 与 `image_get` 匿名被拒，二者与 `post_create` 的成功路径未实测。差异见
[authentication.md](authentication.md)、[anime-pictures.md](anime-pictures.md) 与
[Anime-Pictures 契约附注](anime-pictures-contract-notes.md)。

Cosine 站点（Next.js + Prisma + Meilisearch 自研 API，**没有本地上游服务端源码**）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 请求都拼在这个地址后面；例子 `"https://pic.cosine.ren"` |
| `revalidate_secret` | string，默认 `""` | 只供 `POST /api/artwork/revalidate` 使用；留空即匿名，客户端照发空串、由站点判定。显式传空串表示本次不读配置，`None`（或不传）才从条目里读这个名字 |

客户端按名字取 `url`（没传 `site_url` 时）与 `revalidate_secret`（没传该参数时），条目里缺哪个都会在构造时抛
`KeyError`；条目里没有 `username` / `password` / `api_key` / `access_token` 一类字段，公开读取默认匿名。不调用 `artwork_revalidate` 时，任何请求都不会带上这个密钥，
也不会带别的认证头。公开读取（`image_list` / `artwork_show` / `image_random` / `search` / `search_suggestions` /
`tag_images` / `tag_list` / `artist_images` / `artist_list` / `search_index_status` / `feed`）都取过匿名 `200` 样本，
两个 POST（`artwork_revalidate` 与 `search_index_admin`）本轮没有调用，成功与拒绝形态都未实测。
证据与未实测项见[验证记录](verification.md#cosine匿名只读实测2026-09-20)与
[Cosine 契约附注](cosine-contract-notes.md)。

nhentai 站点（站点自有的 `api/v2` JSON API，站点自己发布 OpenAPI，**没有上游引擎源码**）：

| 键 | 类型与取值 | 含义与例子 |
| :--- | :--- | :--- |
| `url` | string，站点根地址 | 填**网页主机**，不是 `/api/v2`；原生方法自己带 `api/v2` 前缀，例如 `GET https://nhentai.net/api/v2/galleries`。例子 `"https://nhentai.net"` |
| `api_key` | string，默认 `""` | 账号设置页生成的 key；留 `""` 时不发 `Authorization` 头，即匿名。例子 `"your-api-key"` |

条目只用这两个键：没有 `username` / `password` / `user_id` / `access_token`。是否发送凭据只看 `api_key`：
显式传空串（`api_key=''`）表示本次客户端匿名、**不读**配置里的值；`None`（或不传）才读配置。非空时每个请求
带上 `Authorization: Key <api_key>`——scheme 就是字面量 `Key`，不是 `Basic` 也不是 `Bearer`，key 在
`https://nhentai.net/user/settings#apikeys` 生成。客户端不做本地权限判断、不在 `401` 后退回匿名，也不提供登录、
注册或刷新方法。
站点另有一套 `Authorization: User <token>` 的用户凭据；本类**不实现**它（构造签名里没有这个参数），
`user_me()` 是公开契约里唯一相关的读取方法（OpenAPI 把 `user` / `auth` 两个分组标为 First-party and internal
only，只有 `GET /api/v2/user` 例外），细节见 [authentication.md](authentication.md#nhentai-站点)。
站点 OpenAPI 要求带描述性的 `User-Agent`（`AppName/version (联系人或项目 URL)`）：它取自共享的
`request.user_agent`（默认 `Anybooru/0.1.0.dev1`），本库不校验、也不代替使用者填写，需要就改
`request.user_agent` 或用构造参数 `user_agent`——这是**请求头约定而不是认证**，不满足时请求仍可能成功。
限流按端点分别给预算（OpenAPI 里逐条写明，例如匿名 `GET /api/v2/galleries` 是 `15/1min per IP`），
本库不做客户端限速，示例的调用间隔由 `examples.nhentai.pause_seconds` 给出；逐条出处见
[nhentai 契约附注](nhentai-contract-notes.md)。

同一个站点名在所有客户端里都表示 `sites` 段的键（`Danbooru`、`Moebooru`、`Serika`、`E621`、`Zerochan`、
`Gelbooru`、`Gelbooru02`、`Shuushuu`、`Sakuria`、`AnimePictures`、`Cosine`、`Nhentai`），选择哪个类由调用者决定。

### 样例清单里各条的实际状态

清单是**样例**：每条的状态如下，别把「在清单里」等同于「支持」或「已测」。
支持范围由各引擎自己的接口规则决定（[danbooru-api.md](danbooru-api.md)、[moebooru-api.md](moebooru-api.md)、
[serika-api.md](serika-api.md)、[e621-api.md](e621-api.md)、[zerochan-api.md](zerochan-api.md)、
[gelbooru-api.md](gelbooru-api.md)、[gelbooru02-api.md](gelbooru02-api.md)、[shuushuu-api.md](shuushuu-api.md)、
[sakuria-api.md](sakuria-api.md)、[anime-pictures-api.md](anime-pictures-api.md)、
[cosine-api.md](cosine-api.md)、[nhentai-api.md](nhentai-api.md)）。

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
| `shuushuu` | e-shuushuu 自有 REST API | 公开读接口按 OpenAPI 封装；本次匿名冒烟与两个示例的逐请求结果见[验证记录](verification.md#shuushuu-匿名只读实测2026-09-19)，认证及写路径未实测 |
| `tbib` | Gelbooru02（站点自述 `Running Gelbooru 0.2`） | 匿名冒烟与两个示例共 10 次请求全部 `200`，三个脚本退出 `0`（`post_list` 的 JSON 与 XML、`tag_list`、`comment_list`、分页 `pid=1&limit=2`）；`post_deleted` 未跑（TBIB 上实测 `500` 加不完整 XML）；逐条见[验证记录](verification.md#gelbooru02tbib匿名只读实测2026-09-19)，来源见[契约附注](gelbooru02-contract-notes.md) |
| `sakuria` | Sakuria（Pixiv 第三方镜像站，站点自有 JSON API，**无官方页面 / OpenAPI / 源码**） | 本轮串行 54 次匿名 GET（每个请求只发一次、不重试、不跟随跳转、不下载媒体）：`200`×41、`400`×7、`401`×3、`404`/`426`/`503` 各一；另有 10 次上限的匿名冒烟（`10/10` 通过、退出 `0`）与两个示例（全部 `200`、退出 `0`）。**只证样本、不泛化枚举与上限**（例如 `size` 只证实 1 与 48 被接受、0 与 49 被拒绝，响应条数不等于 `size`）。44 个方法全部接入（27 个匿名只读 + 17 个需登录的 `me*`，后者只请求过 `/me/likes`）。逐条见[验证记录](verification.md#sakuria匿名只读实测2026-09-19)与[契约附注](sakuria-contract-notes.md) |
| `cosine` | Cosine（Next.js + Prisma + Meilisearch 自研 API，**没有本地上游服务端源码**） | 两批匿名串行探测共 69 次（`200`×57、`500`×7、`404`×3、`400`×2）：第一批 18 次全部 `200`，覆盖列表、正常作品详情、`image_random` 的 1 条与 3 条、搜索与建议、标签筛图与标签列表、画师作品与画师资料、只读索引进度与 `feed.xml`；第二批 51 次补齐页码 / `offset` / 标签 / 画师 / 搜索的边界，含 `400` / `404` / `500` 样本。10 次上限的冒烟与两个示例的执行结果同样列在[验证记录](verification.md#cosine匿名只读实测2026-09-20)。两个 POST 未调用，成功与拒绝形态未实测 |
| `anime_pictures` | Anime-Pictures（自研 `api/v3` JSON 接口，**无可读到的官方手册页 / OpenAPI / 服务端源码**） | 本轮串行 90 次匿名 GET（`200`×76、`400`×4、`403`×2、`404`×6、`410`×1、`500`×1）：API 主机根、帖子列表两页与分页 / 排序参数、帖子详情、帖评论、标签列表与详情、用户列表与详情、评论列表与详情、标签 `type` 0–7、缺失资源的 `410` / `404`、非法路径段的纯文本 `400` 与缺 `page` 的 JSON `400`、`page=-1` 的 `500`、`get_image` 的 `403` 空正文。`post_create`、带 Cookie 的成功路径与媒体成功返回均未实测。逐条见[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)与[契约附注](anime-pictures-contract-notes.md) |
| `nhentai` | nhentai API v2（站点自有 REST API，站点自己发布 OpenAPI，**无上游引擎源码**） | 36 个原生方法按站点 OpenAPI（`info.version` 为 `2.0.0+14bccf7`，98 条路径 / 114 个操作 / 129 个 schema）封装；本轮串行 61 次匿名 GET（每请求只发一次、不跟随跳转、不重试、不下载媒体）把 31 个 GET 路由逐个直接打过一遍：25 个 `200`，6 个匿名必拒的 `401`（`/api/v2/user`、`/api/v2/favorites`、`/api/v2/favorites/random`、`/api/v2/blacklist`、`/api/v2/blacklist/ids`、`/api/v2/galleries/{id}/favorite`，正文统一是 `{"error": "Authentication required"}`）。4 个写方法（3 个 `POST` + 1 个 `DELETE`）与 `POST /api/v2/tags/search` 未调用；带 key 的成功路径、PoW/CAPTCHA、账号与内部路由（`auth` / `user` / `moderation` 分组）与所有媒体请求从未执行，`.to` 克隆站不接入。脚本侧另有匿名冒烟 10 请求 10 通过（`8×200` 加预期的 `404` / `400`，退出 `0`）与两个示例（3 次与 5 次 GET 全 `200`，退出 `0`）。逐条见[验证记录](verification.md#nhentai匿名只读实测2026-09-20)，出处与排除项见[nhentai 契约附注](nhentai-contract-notes.md) |

### 怎么判断一个站点该用哪个类

**库不做自动识别**：`Danbooru`、`Moebooru`、`Serika`、`E621`、`Zerochan`、`Gelbooru`、`Gelbooru02`、`Shuushuu`、
`Sakuria`、`AnimePictures`、`Cosine`、`Nhentai` 是十二个并列的类，各自的传输方式、认证形态与参数拼法按各自引擎写死；选错类不会自动降级，也不会失败后换成
另一个类重试。判断依据只能是你自己手里的信息：**站点自述**（页脚、帮助页、API 页面、上游仓库）加上
**发一次请求看响应**（Zerochan、Gelbooru02、Sakuria、Anime-Pictures、Cosine、nhentai 这类没有可读到的上游服务端源码的站点，
只能靠站点页面、可读到的公开前端文件与实测响应）。

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

e-shuushuu 的 OpenAPI 自称 `Shuushuu API 2.0.0`，路径如 `/api/v1/images` 和 `/api/v1/tags`，
列表保留 `total/page/per_page/images` 等字段。`/api/v1/search` 搜的是标签；不能因 Serika 也用
`/api/v1` 就混用客户端，二者的标签输入、认证、返回对象都不同。

TBIB（Gelbooru02）和 gelbooru.com 长得像、其实不是一套：两者都请求 `index.php`、都用 `page` 选入口，
但 TBIB 的**帖子**用 `page=dapi&s=post&q=index` 时默认给 XML、加 `json=1` 才给 JSON（一个数组，没有
`count` / `offset` 这类根信息），而**标签与评论**加不加 `json=1` 都只给 XML 文本；XML 的帖子根元素形如
`<posts count="…" offset="…">`，`pid` 翻页时 `offset` 跟着走（实测 `pid=1&limit=2` 时 `offset="2"`）。
不能把 `gelbooru.com` 的 dapi JSON 客户端整体复用到 TBIB；用户目录未调用，补全路径取得 `302` 而非建议数据。
二者的匿名边界与格式差异见 [gelbooru02.md](gelbooru02.md)。

Sakuria 的路径也是站点自己的：站点元信息是 `/`、`/stats`、`/healthz`、`/app/config`、`/ai/config`；
列表走 `/search/illust`、`/search/user`、`/search/novel`、`/spotlight`、`/tags/search`；
详情走 `/illust/<id>`、`/users/<id>`、`/novels/<id>`、`/series/<id>`、`/spotlight/<id>`、`/tags/<标签>`；
子资源挂在详情路径下（`/illust/<id>/comments`、`/illust/<id>/comments/<comment_id>/replies`、
`/illust/<id>/related`，用户侧则有 `/users/<id>/illusts` 等）；个人面是 `/me` 与 `/me/<能力>` 一类路径。
本轮实测：`/illust/<id>`、`/users/<id>`、`/novels/<id>`、`/series/<id>`、`/spotlight/<id>` 回的是**裸对象**，
不是 `{items: …}`；只有列表路由带信封，而 `/series/<id>` 虽是裸对象，自己仍带一个 `items` 作品数组。
它同样没有 Rails 的 `posts`，也没有官方页面与上游源码可对照，是本仓库依据最弱的一档，
见 [sakuria.md](sakuria.md)。

Anime-Pictures 的路径也在自己的 API 主机上：**根**是 `https://api.anime-pictures.net/`，
JSON 资源路由挂在 `/api/v3` 下：`/api/v3/posts`（列表）、`/api/v3/posts/{id}`（详情）、
`/api/v3/posts/{id}/comments`、`/api/v3/posts/{id}/tags`（需权限）、`/api/v3/tags`、`/api/v3/tags/{id}`、
`/api/v3/users`、`/api/v3/users/{id}`、`/api/v3/comments`、`/api/v3/comments/{id}`；
原图下载入口是根下的 `/pictures/get_image/{file_url}`（需权限）。它与 Rails 家族的区别很直接：
路径里不用 `posts.json`；帖子列表采用 0 起步的 `page` 与 `posts_per_page`，不是其它家族的 `tags/limit` 搜索方式，
标签、用户与评论列表仍使用 `limit/offset`。本轮实测：帖子不存在**不是 `404` 而是 `410`**；不存在的标签 / 用户 / 评论才是
`404`；非法路径段（如 `/api/v3/posts/top`）返回 `400` 加 `text/plain`，正文不是 JSON；
API 主机上的 `/api/v2/comments` 与 `/pictures/view_posts/0?type=json` 已测为 `404` 空正文，其它旧路径未测。
输入资料记录网页主机被 Cloudflare 质询挡下、`/api/v3/*` 会 302 到 API 主机；本轮未请求网页主机，也不依赖其跳转。
Cosine 的路径也在自己的站点根上：作品列表是 `/api/list?page=1&pageSize=2`，详情是 `/api/artwork/{id}`，
随机是 `/api/random?count=…`，搜索与建议是 `/api/search`、`/api/search/suggestions`，标签是 `/api/tag` 与 `/api/tags`，
画师是 `/api/artist` 与 `/api/artists`，索引进度与索引管理共用 `/api/search/admin`（GET 读、POST 改），
订阅源是 `/feed.xml`。它不是 booru：路由里没有 `posts.json`，列表的外壳是 `{"images":…,"total":…}`，
参数用 `pageSize` / `start` / `offset` / `r18` 这些站点自己的名字；作品编号 `id` 是站内自增主键，
上游编号在 `pid` 里，两者不能互换。它同样没有可对照的上游服务端源码：站点前端仓库公开，本轮只按需
只读了个别文件（不 clone、不写行号），公开结论来自匿名只读响应。见 [cosine.md](cosine.md) 与
[契约附注](cosine-contract-notes.md)。

nhentai 的路径挂在站点的 `/api/v2` 下，与 booru 家族不同：根是 `/api/v2`（`GET https://nhentai.net/api/v2`，
回 `{"version": …, "message": …}`），列表是 `/api/v2/galleries`、搜索是 `/api/v2/search?query=…`、
详情是 `/api/v2/galleries/{id}`（可加 `include=comments,related,favorite,suggestions`）、
标签是 `/api/v2/tags/{tag_type}` 与 `/api/v2/tags/{tag_type}/{slug}`（`language/english` 这种
**类型 + slug** 两段，不是单个字符串），评论是 `/api/v2/galleries/{id}/comments`。
列表的回包是对象 `{"result": [ … ], "num_pages": …}`，条目数组在 `result` 里，不是裸数组；
参数用 `page` / `per_page` / `sort` / `include` / `limit` 这些站点自己的名字，搜索表达式写在 `query` 里
（`language:english`、`tag:"big breasts"`、`pages:>10`）。认证是单个 `Authorization: Key <api_key>` 头，
既不是 Basic 也不是查询串字段。它同样没有上游服务端源码可对照，但站点自己发布了 OpenAPI
（`https://nhentai.net/api/v2/openapi.json`）；见 [nhentai.md](nhentai.md)、
[nhentai-api.md](nhentai-api.md) 与[契约附注](nhentai-contract-notes.md)。

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
| Gelbooru02 | `site` = `"tbib"` | `Gelbooru02('tbib')`，站点条目只有 `url`，没有凭据可填 |
| Gelbooru02 | `post_query` = `{"tags":"rating:safe","pid":0,"limit":2}` | `client.post_list(tags='rating:safe', pid=0, limit=2)`（默认 JSON：`https://tbib.org/index.php?tags=rating%3Asafe&pid=0&limit=2&s=post&q=index&page=dapi&json=1`，实测 `200`，返回帖子数组）；`list_posts.py` 再拿首帖 `id` 调 `client.post_list(id=<该 id>, response_format='xml')` 取同一帖的 XML 原文 |
| Gelbooru02 | `tag_query` = `{"limit":2}`、`comment_post_id` = `1` | `client.tag_list(limit=2)`（`https://tbib.org/index.php?limit=2&s=tag&q=index&page=dapi`）与 `client.comment_list(1)`（`…&post_id=1&s=comment&q=index&page=dapi`）——两者都返回 XML 文本、不带 `json=1`，实测 `200`；`browse_resources.py` 打印根元素与子元素属性 |
| Gelbooru02 | `pause_seconds` = `1.2` | `time.sleep(1.2)`，示例在请求之间等，不代表服务端限流阈值 |
| Shuushuu | `site` = `"shuushuu"` | `Shuushuu('shuushuu', username='', password='', access_token='')`，示例明确匿名 |
| Shuushuu | `search_query` = `{"q":"long hair","limit":5}`、`tag_title` = `"long hair"` | `client.search(q='long hair', limit=5)`，从 `hits` 中选 `title == 'long hair'` 的 `tag_id`，没有命中就结束，不猜 ID |
| Shuushuu | `image_query`、`pages` = `[1,2]` | 对查到的 46 调 `client.image_list(tags='46', page=1, tags_mode='all', tag_depth=0, per_page=2, sort_by='favorites', sort_order='DESC')`；第二页用 `page=2`，再从非空第一页取 `image_id` 读详情 |
| Shuushuu | `tag_id` = `46`、`comment_query` = `{"image_id":1118862,"per_page":2}` | `client.tag_show(46)`、`client.comment_list(image_id=1118862, per_page=2)`，读取标签关系与该图评论 |
| Shuushuu | `user_query` = `{"search":"whitekitten","per_page":2}`、`news_query` = `{"per_page":1}` | `client.user_list(search='whitekitten', per_page=2)`、`client.news_list(per_page=1)` |
| Shuushuu | `pause_seconds` = `2.1` | `time.sleep(2.1)`，示例在请求之间等，不代表服务端限流阈值 |
| Sakuria | `site` = `"sakuria"` | `Sakuria('sakuria', access_token='')`，示例明确匿名（空串不读配置里的 token） |
| Sakuria | `illust_query` = `{"q":"blue","size":2,"sort":"new"}`、`pages` = `[1,2]` | `client.illust_search(q='blue', size=2, sort='new', page=1)`（GET `https://sakuria-api.syarolia.com/search/illust?q=blue&size=2&sort=new&page=1`），打印每条的 `id` / `title`；第二页手动把 `page` 换成 `2`，翻页判定只看 `hasMore` 为 `false` 或 `nextPage` 为 `null`（不用数值 `nextPage` 跳页），并对重复 `id` 去重后再打印 |
| Sakuria | `illust_id` = `70937229`、`comment_query` = `{"page":1,"size":2}` | `client.illust_show(70937229)`、`client.illust_comments(70937229, page=1, size=2)`；`browse_resources.py` 再用详情里的 `author.id` 调 `client.user_show(<该 id>)` |
| Sakuria | `pause_seconds` = `1.2` | `time.sleep(1.2)`，示例在请求之间等，不代表服务端限流阈值 |
| Anime-Pictures | `site` = `"anime_pictures"` | `AnimePictures('anime_pictures')`，条目 `url` 是 API 基址，凭据都为空即匿名 |
| Anime-Pictures | `post_query` = `{"search_tag":"hatsune miku","posts_per_page":2,"order_by":"rating"}`、`pages` = `[0,1]` | `client.posts_list(page=0, search_tag='hatsune miku', posts_per_page=2, order_by='rating')`（GET `https://api.anime-pictures.net/api/v3/posts?page=0&search_tag=hatsune+miku&posts_per_page=2&order_by=rating`），第二页把 `page` 换成 `1`；打印真实 `last_call` URL 与状态、`page_number` / `posts_count` / `max_pages`，以及每帖 `id` / `score_number` |
| Anime-Pictures | `post_id` = `382872` | `client.post_show(382872)`；`browse_resources.py` 再用 `client.post_comments(382872)` 取评论、用详情里的 `user.id` 调 `client.user_show(<该 id>)`、用非空评论首条的 `comment.id` 调 `client.comment_show(<该 id>)`（评论为空时跳过该步并说明），只打印字段不打印评论正文 |
| Anime-Pictures | `pause_seconds` = `1.3` | `time.sleep(1.3)`，示例在请求之间等，不代表服务端限流阈值 |
| Cosine | `site` = `"cosine"` | `Cosine('cosine', revalidate_secret='')`，示例显式空串＝本次不读配置里的密钥（它只服务 `artwork_revalidate`，示例不调用） |
| Cosine | `list_query` = `{"pageSize":2}`、`pages` = `[1,2]` | `client.image_list(page=1, pageSize=2)`（GET `https://pic.cosine.ren/api/list?page=1&pageSize=2`），第二页把 `page` 换成 `2`；返回 `{"images":…,"total":…}`，脚本打印 `total` 与每项 `id` / `pid` / `platform` / `rawurl` |
| Cosine | `search_query` = `{"q":"初音","limit":2,"platform":"twitter","r18":false,"sort":"create_time:desc"}`、`offsets` = `[0,2]` | `client.search(q='初音', limit=2, platform='twitter', r18=False, sort='create_time:desc', offset=0)`，第二个 `offset` 用 `2`；布尔编成小写（`r18=False` → `r18=false`），脚本只打印 `data['total']` 与 `hits` 里的 `id`。注意 `total` 被夹到 1000、`offset` 也被夹到 1000 |
| Cosine | `artwork_id` = `1`、`tag` = `"GenshinImpact"`、`tag_query` = `{"start":0,"limit":2}` | `client.artwork_show(1)['json']`（superjson 外壳）与 `client.tag_images('GenshinImpact', start=0, limit=2)`（裸数组、没有 `total`） |
| Cosine | `artist_query` = `{"platform":"pixiv","authorid":"54390221","page":1,"pageSize":2}` | `client.artist_images(platform='pixiv', authorid='54390221', page=1, pageSize=2)`（`{"artists":…,"total":…,"hasNextPage":…}`），再用同一组参数加 `infoOnly=True` 取该画师的资料对象；布尔编成小写正好命中站点只认字面量 `"true"` 的分支 |
| Cosine | `pause_seconds` = `1.3` | `time.sleep(1.3)`，示例在请求之间等，不代表服务端限流阈值 |
| nhentai | `site` = `"nhentai"` | `Nhentai('nhentai', api_key='')`，示例显式空串＝匿名：不读配置里的 key，也不发 `Authorization` 头。两个示例是 `examples/nhentai/list_galleries.py`（列表两页 + 搜索，共 3 次 GET）与 `examples/nhentai/browse_resources.py`（详情 + 标签详情 + 标签批量 + 评论 + 站点配置，共 5 次 GET） |
| nhentai | `list_query` = `{"per_page":2}`、`pages` = `[1,2]` | `client.gallery_list(page=1, per_page=2)`（GET `https://nhentai.net/api/v2/galleries?page=1&per_page=2`），第二页把 `page` 换成 `2`；回包是对象，脚本打印 `result` 的条数与每条的 `id` |
| nhentai | `search_query` = `{"query":"language:english","sort":"date","page":1}` | `client.search(query='language:english', sort='date', page=1)`（GET `https://nhentai.net/api/v2/search?query=language%3Aenglish&sort=date&page=1`），打印 `result` 条数、`num_pages` 与首条的 `id` |
| nhentai | `gallery_id` = `658856`、`tag_type` = `"language"`、`tag_slug` = `"english"` | `client.gallery_show(658856)`（GET `https://nhentai.net/api/v2/galleries/658856`）与 `client.tag_show('language', 'english')`（GET `https://nhentai.net/api/v2/tags/language/english`） |
| nhentai | `tag_ids` = `"12227,6346"`、`comments_query` = `{"page":1,"per_page":2}` | `client.tag_ids('12227,6346')`（英文逗号串，客户端不拼接、不改写）与 `client.gallery_comments(658856, page=1, per_page=2)`；`browse_resources.py` 另调 `site_config()`（GET `https://nhentai.net/api/v2/config`）打印配置里的 CDN 服务器列表 |
| nhentai | `pause_seconds` = `1.3` | `time.sleep(1.3)`，示例在请求之间等，不代表服务端限流阈值（各端点自己的预算是文档值，见 [errors.md](errors.md#nhentai)） |

两个约定：Danbooru 与 Moebooru 的示例读顶层散键（`tags` / `limit` / `pages`），
Serika、e621ng、Zerochan、Gelbooru、Gelbooru02、Shuushuu、Sakuria、Anime-Pictures、Cosine 与 nhentai 把查询整块放进 `*_query` 字典再展开（nhentai 另把页码放在 `pages`）；
`comment_body` 只服务上面那条写操作，只读示例用的是列表返回的第一个帖子 id。这些键都可以按自己的脚本增删。

示例脚本的用法：

```bash
.venv/Scripts/python.exe examples/danbooru/list_posts.py
.venv/Scripts/python.exe examples/danbooru/list_posts.py --config my-anybooru.json --site safebooru
.venv/Scripts/python.exe examples/e621/list_posts.py --site e926
.venv/Scripts/python.exe examples/zerochan/list_entries.py
.venv/Scripts/python.exe examples/zerochan/filter_entries.py
.venv/Scripts/python.exe examples/gelbooru/autocomplete.py
python examples/gelbooru02/list_posts.py
python examples/gelbooru02/browse_resources.py
.venv/Scripts/python.exe examples/shuushuu/search_images.py
.venv/Scripts/python.exe examples/shuushuu/browse_resources.py
.venv/Scripts/python.exe examples/sakuria/search_illusts.py
.venv/Scripts/python.exe examples/sakuria/browse_resources.py
.venv/Scripts/python.exe examples/anime_pictures/list_posts.py
.venv/Scripts/python.exe examples/anime_pictures/browse_resources.py
.venv/Scripts/python.exe examples/cosine/list_images.py
.venv/Scripts/python.exe examples/cosine/browse_resources.py
.venv/Scripts/python.exe examples/nhentai/list_galleries.py
.venv/Scripts/python.exe examples/nhentai/browse_resources.py
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
| `site_url` | `sites.<键>.url`（Gelbooru02/TBIB 的条目只有这一个字段） | `Gelbooru02('tbib', site_url='https://tbib.org')` |
| `username` / `password` / `access_token` | 同名站点字段（Shuushuu） | `Shuushuu('shuushuu', username='', password='', access_token='')`，明确匿名，不自动登录 |
| `access_token` | `sites.<键>.access_token`（Sakuria） | `Sakuria('sakuria', access_token='')`，显式空串=匿名、不读配置里的 token；非空才发 `Authorization: Bearer <token>` |
| `authorization` / `cookie` | `sites.<键>.authorization` / `.cookie`（Anime-Pictures） | `AnimePictures('anime_pictures', authorization='', cookie='')`，显式空串=匿名、不读配置里的值；非空时按原值发送，不加 `Bearer`、不猜 cookie 名 |
| `revalidate_secret` | `sites.<键>.revalidate_secret`（Cosine） | `Cosine('cosine', revalidate_secret='')`，显式空串=本次不读配置里的密钥；`None`（或不传）才读配置，只有 `artwork_revalidate` 会用到它 |
| `api_key` | `sites.<键>.api_key`（nhentai） | `Nhentai('nhentai', api_key='')`，显式空串=匿名、不读配置里的 key；非空时头是 `Authorization: Key <api_key>`，库只加 `Key ` 这个 scheme 前缀，不改写 key 本身 |
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

## `smoke` 段

只供仓库 `test/<站点>.py` 的匿名冒烟脚本使用，不改变库的请求行为；普通 API 调用不读取这段。
脚本与完整默认参数都随源码分发，完整内容见 [`anybooru/anybooru.json`](../anybooru/anybooru.json)。
自备覆盖配置必须保留这段；`--config` 读取整份文件，不和包内默认值合并。

| 键 | 默认值与用途 |
| :--- | :--- |
| `pause_seconds` | `1.2`；上次请求结束后等待这些秒数，再发下一次 |
| `limit` / `pages` | `2` / `[1, 2]`；每页只取两条，页码检查只使用这两个页码；Danbooru/e621 改用首批末项的 `b<id>` 游标 |
| `missing_id` | `0`；Danbooru/e621 的缺失帖子、Moebooru 的缺失评论、Serika 的缺失图片 |
| `danbooru.tags` / `moebooru.tags` / `e621.tags` | `rating:g` / `rating:s` / `rating:s`；正常读取的安全评级过滤 |
| `moebooru.api_version` | `2`；检查带 `posts` 数组的返回对象，不误要求未请求的 tags/pools/votes |
| `serika.ratings` / `serika.sort` | `safe` / `newest`；站内图片列表的评级与排序 |
| `zerochan.sort` / `zerochan.missing_id` | `id` / `999999999`；编号倒序与缺失条目边界 |
| `gelbooru` | `term='blue'`、`type='tag'`、`limit=3`；只检查标签建议结构，不把 limit 当返回条数上限；`post_id=1` / `last_id=0` 供两个匿名拒绝调用 |
| `tbib` | `post_query={tags:'rating:safe'}`、`pages=[0, 1]`、`comment_post_id=1`；本轮 6 个请求覆盖 post 的 JSON 与 XML、`pid` 翻页（实测 `pid=1&limit=2` 时 XML 根 `offset="2"`）、tags 与 comments 的 XML |
| `shuushuu.pause_seconds` | `2.1`，仅此站冒烟请求间隔，不取全局 `1.2` |
| `shuushuu.search_query` / `tag_query` | `q='long hair', limit=2` / `search='long hair', per_page=2`；两个按名字查标签的入口 |
| `shuushuu.image_query` / `required_tag_ids` | `tags='46,169', tags_mode='all', tag_depth=0, per_page=2, sort_by='favorites', sort_order='DESC', status=[1,2], include_comments=False` / `[46,169]`；检查实际图片包含指定标签，状态数组用重复键 |
| `shuushuu.tag_id` / `comment_query` | `46` / `image_id=1118862, per_page=2`；标签详情及指定图片评论 |
| `shuushuu.invalid_per_page` / `per_page_maximum` / `missing_image_id` | `101` / `100` / `999999999`；读取上限越界的422和不存在图片的404，不把错误改为空列表 |
| `sakuria` | `pause_seconds=1.2`、`illust_query={q:'blue',size:2,sort:'new'}`、`pages=[1,2]`、`novel_query={q:'blue',page:1}`、`spotlight_query={page:1,lang:'zh-cn'}`、`comment_illust_id=70937229`、`comment_query={page:1,size:2}`、`missing_id=0`、`invalid_size=49`；**最多 10 次**匿名请求：站点统计、插画搜索两页、首批首条的详情、小说搜索、`spotlight` 列表、指定插画评论、详情作者、缺失 id 与越界 `size` 两个预期错误；不发 `me*` 请求 |
| `cosine` | `pause_seconds=1.3`、`list_query={pageSize:2}`、`pages=[1,2]`、`artwork_id=1`、`random_counts=[1,3]`、`search_query={q:'初音',limit:2}`、`tag='GenshinImpact'`、`tag_query={start:0,limit:2}`、`missing_id=999999999`；**最多 10 次**匿名 GET：`image_list` 两页、`artwork_show(1)`、`image_random(count=1)` 与 `image_random(count=3)`、`search`、`tag_images`、`tag_list`、`feed`、缺失作品（预期 `404`）；构造 `revalidate_secret=''`、不跟随跳转、不重试、不发 `POST`、不调用 `search_index_admin`、不下载媒体 |
| `anime_pictures` | `pause_seconds=1.3`、`post_query={posts_per_page:2}`、`pages=[0,1]`、`comment_post_id=382872`、`tag_query={tag:'hatsune miku'}`、`tag_id=407`、`user_query={limit:2,offset:0}`、`comment_query={limit:2,offset:0}`、`missing_id=999999999`、`invalid_post_id='top'`；**最多 10 次**匿名 GET：帖子两页、从首批取首条的详情（列表失败就跳过，不补发）、指定帖评论、精确标签查询与标签详情、用户列表、评论列表、缺失帖子（预期 `410`）与非法路径段（预期 `400` 纯文本，`error.data is None`、正文留在 `.body`、`last_call` 记下状态与 URL）；显式清空双凭据、禁跳转、不发 `POST`、不访问媒体 |
| `nhentai` | `gallery_id=658856`、`list_query={per_page:2}`、`search_query={query:'language:english',sort:'date',page:1}`、`tag_type='language'`、`tag_slug='english'`、`missing_id=999999999`、`invalid_query={page:0,per_page:2}`；**最多 10 次**匿名 GET（间隔取全局 `pause_seconds`，页码取全局 `pages`）：画廊列表两页、指定画廊详情、搜索、今日热门、标签详情、评论计数、指定画廊评论（`per_page` 取自 `list_query`）、缺失画廊与非法页码的列表调用两个预期错误路径；构造显式 `api_key=''`、不跟随跳转、不重试、不发 `POST`/`DELETE`、不请求账号路由、不下载媒体 |

这些参数改变查询输入，不改变固定请求数量。运行方法、每站预算、退出码及匿名边界见
[README](../README.md#轻量匿名冒烟检查)；真实结果只记在 [verification.md](verification.md)。

## `verification` 段

维护者做线上验证时用的一段输入，**不属于公开 API**，普通使用者可以整段删掉。它按家族分组，记录的是
“这次跑哪些脚本、发哪些请求、两次之间等多久”：

| 子段 / 键 | 内容 |
| :--- | :--- |
| `verification.serika` | `scripts` 是要跑的示例脚本，`pause_seconds` 是间隔；请求输入仍取 `examples.serika` |
| `verification.e621` | `sites` 决定在 `e621.net` 与 `e926.net` 各跑一遍，`scripts` 是要跑的示例，`pause_seconds` 是间隔；`post_query` / `count_query` / `v2_query` / `only_query` / `related_search` 是复核返回结构与权限分支用的输入 |
| `verification.zerochan` | `scripts` 是要跑的两个示例，`pause_seconds` 是间隔，`default_query` 是不带过滤的根路径查询，`entry_query` / `tag_query` / `multi_tag_query` / `strict_query` / `entry_id` 与 `examples.zerochan` 相同，`optional_queries` 逐条列出页码、排序窗口（`t`）、尺寸（`d`）与颜色（`c`）等可选参数 |
| `verification.shuushuu` | `site='shuushuu'`，`scripts` 列出两个示例，`smoke_script='test/shuushuu.py'`，`pause_seconds=2.1`；调用参数分别取 `examples.shuushuu` 和 `smoke.shuushuu` |
| Danbooru / Moebooru 的顶层与 `moebooru` 子段 | 正常查询（`post_tags` / `tag_search` / `artist_search` / `related_search` / `wiki_search`）、故意不存在的 id 与超界页码（`missing_post_id` / `invalid_page` / `invalid_tags` / `invalid_date`）等，用来核对错误路径 |

命令与真实结果一律记在 [verification.md](verification.md)，本文不重复。
