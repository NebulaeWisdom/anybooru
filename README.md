# Anybooru - Danbooru / Moebooru / Serika / e621ng / Zerochan 图站 API 客户端

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/NebulaeWisdom/anybooru/master/LICENSE)

**Anybooru** 是访问 Danbooru、Moebooru、Serika、e621ng 与 Zerochan 五类引擎的普通 Python API 客户端，
不是某个站点的私有 SDK：原生方法封装该家族的 API 路由，参数按该引擎的规则编码，
服务端返回的数据字段原样给出，不拼装跨引擎的统一图库模型。

部分原生方法按文档明确的契约拆开响应信封；需要保留完整 JSON 时可使用各家族的通用 `request()` 入口。
信封与元数据的处理方式见对应家族文档，不把不同引擎的响应差异隐藏起来。

本库按对应引擎的路由与控制器对齐契约，适用于运行相同引擎的实例，不只支持几个固定站点。
Serika 是独立的 Next.js 引擎，其官方 v1 与前端私有的非版本化 API 分开标注；Danbooru、Moebooru、
e621ng 是三个互不相同的 Rails 引擎，同名路由与相同的认证头不代表同一套契约。Zerochan 是**第五类**：
站点自有的只读 JSON API，没有公开的引擎源码，契约依据是官方 API 页面快照加真实请求实测，
与另外四类的对齐方式不同，见
[docs/zerochan-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-contract-notes.md)。

- 版本：**0.1.0.dev1**（开发版，尚未发布到 PyPI）
- 许可：**MIT License**

本项目源自 [LuqueDaniel/pybooru](https://github.com/LuqueDaniel/pybooru)（上游最后一次发版是 2020 年的 4.2.2），
现已重写客户端并新增 Serika、e621ng 与 Zerochan 三个家族，重构配置、文档、传输与错误处理。
前四个家族按上游引擎源码对齐，Zerochan 则依据 API 页面快照与真实响应。
本仓库原名 `pybooru`，现名 `anybooru`；新的版本序列从 `0.1.0.dev1` 开始。
除 changelog 里保留的历史记录外，**行为与上游不再一致**，用法以本仓库文档为准；原项目的 MIT 许可与
版权声明保留在 [LICENSE](https://github.com/NebulaeWisdom/anybooru/blob/master/LICENSE)。

## 运行要求

- Python >= 3.6
- [requests](https://requests.readthedocs.io/) >= 2.26

## 安装

### 从源码安装（当前开发版）

```bash
git clone https://github.com/NebulaeWisdom/anybooru.git
cd anybooru
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .        # Windows
.venv/bin/python -m pip install -e .                # Linux / macOS
```

安装后不需要额外准备配置文件：包内自带一份可用的 `anybooru.json`，构造函数默认就读它。

## 快速开始

### 1. 配置文件

所有站点、凭据、代理、超时等参数集中放在一份 JSON 文件里，不在调用处硬编码，也不用环境变量注入。
这份文件**随包安装**，`Danbooru('danbooru')` 这类调用默认读它：

```json
{
  "request": {
    "timeout": 30,
    "proxies": {},
    "user_agent": "Anybooru/0.1.0.dev1"
  },
  "sites": {
    "danbooru": { "url": "https://danbooru.donmai.us", "username": "", "api_key": "" },
    "e621": { "url": "https://e621.net", "username": "", "api_key": "" },
    "e926": { "url": "https://e926.net", "username": "", "api_key": "" },
    "zerochan": { "url": "https://www.zerochan.net" }
  },
  "examples": {
    "danbooru": { "site": "danbooru", "tags": "rating:g", "limit": 3, "post_id": 1, "comment_body": "示例评论" },
    "e621": { "site": "e621", "post_query": { "tags": "rating:s", "limit": 2 }, "pause_seconds": 1 },
    "zerochan": {
      "site": "zerochan",
      "entry_query": { "p": 1, "l": 2, "s": "id" },
      "tag_query": { "tags": "Genshin Impact", "l": 2 },
      "multi_tag_query": { "tags": ["Lumine", "Flower"], "l": 2 },
      "strict_query": { "tags": "Genshin Impact", "strict": true, "l": 2 },
      "entry_id": 3793685,
      "pause_seconds": 1.2
    }
  }
}
```

要改站点、凭据或代理，复制那份包内文件改一份自己的，再把路径交给 `config_file`；当前工作目录里的
同名文件**不会**被自动读取。包内默认 `request.proxies` 是空对象，即不使用代理；需要代理时把它填成
`{"http": "http://proxy-host:port", "https": "http://proxy-host:port"}`。

```python
import shutil
from anybooru import Danbooru, DEFAULT_CONFIG_FILE

print(DEFAULT_CONFIG_FILE)                                     # 包内默认配置的绝对路径
shutil.copy(DEFAULT_CONFIG_FILE, 'config/sites.json')          # 拿它当模板

client = Danbooru('danbooru')                                  # 读包内默认配置
client = Danbooru('danbooru', config_file='config/sites.json') # 读自己那份
```

`config_file` 指到的文件不存在时直接抛 `FileNotFoundError`，不会退回到默认文件。`sites` 段是
**样例 / 起始清单，不是支持边界**：名单外的同引擎站点可以直接用 `site_url`（Moebooru 另需
`api_version`）接入，见
[docs/configuration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/configuration.md#sites-段)。

完整的默认配置样例（含五类引擎站点、`examples`、`verification` 段）见
[docs/configuration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/configuration.md)。

### 2. Danbooru 系站点

```python
from anybooru import Danbooru

# 'danbooru' 是 anybooru.json 中 sites 段的键名；URL、代理、超时、凭据都来自配置。
client = Danbooru('danbooru')
example = client.config['examples']['danbooru']

posts = client.post_list(tags=example['tags'], limit=example['limit'])
for post in posts:
    print(post['id'], post['rating'], post['tag_string'])

client.close()
```

需要登录的写接口在配置了 `username` / `api_key` 后自动使用 HTTP Basic 认证：

```python
client = Danbooru('danbooru')
example = client.config['examples']['danbooru']
client.comment_create(post_id=example['post_id'], body=example['comment_body'])
```

这条写路径**未实测**：`comment_create` 只按上游源码对齐（评论接口要求登录），本仓库不带凭据，
对应脚本 `examples/danbooru/comment_create.py` 未执行、未实测；要真正写入得自己填 `username` / `api_key`。

画师查询的参数与上游匹配语义见
[Danbooru API 契约](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru-api.md#artists)。

### 3. Moebooru 系站点（如 yande.re / konachan）

```python
from anybooru import Moebooru

# 'yandere' 是 anybooru.json 中 sites 段的键名；Moebooru 面没有 search 字典，
# 过滤条件（tags、limit、page 等）就是顶层参数。
client = Moebooru('yandere')
example = client.config['examples']['moebooru']

for post in client.post_list(tags=example['tags'], limit=example['limit']):
    print(post['file_url'])

client.close()
```

Moebooru 面已按上游 `moebooru/` 的路由与控制器对齐（90 个原生方法，覆盖帖子、合集、笔记、标签、
画师、评论、wiki、论坛与账号端点）；匿名只读端点的执行记录见
[docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md)，
需要登录的写接口只做源码对齐、未做线上实测。完整清单见
[docs/moebooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru-api.md)。

### 4. Serika 系站点（serika.art 及自托管实例）

```python
from anybooru import Serika

with Serika('serika') as client:
    example = client.config['examples']['serika']
    print(client.stats())  # 官方 v1，匿名可达；返回 data，meta 留在 last_call
    result = client.internal_image_list(**example['image_query'])
    for image in result['images']:  # 站内非版本化私有契约，原始 JSON 信封
        print(image['id'], image['post_id'], image['url'])
```

模块 `anybooru.serika` 的 `Serika` 类与 `api_serika` 的方法集覆盖 **16 个官方 v1 方法**及
**14 个站内匿名读方法**。官方需 key 的 12 个方法仅源码对齐，未实测；配置 key 留空，
不实现站内 cookie 登录。随机图片方法返回原始 `bytes`，不会按 JSON 解析。
v1 图片路径用内部 `id`，站内详情用顺序号 `post_id`，两者不能互换。
使用方式见 [docs/serika.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika.md)。

### 5. e621ng 系站点（e621.net / e926.net）

```python
from anybooru import E621

# 'e621' 与 'e926' 是 anybooru.json 中 sites 段的键名；两者是同一引擎的两套站点，
# e926 只提供安全内容。URL、代理、超时、凭据同样来自配置。
with E621('e621') as client:
    example = client.config['examples']['e621']

    for post in client.post_list(**example['post_query']):
        print(post['id'], post['rating'], post['file']['url'])
```

e621ng 面按上游路由与控制器对齐，提供 **18 个原生只读方法**：帖子、标签、画师、评论、
合集、笔记、wiki 各一对列表/详情，另有随机帖、帖子计数和两个相关标签方法。默认帖子负载是嵌套结构
（`file` / `preview` / `sample` / `score` / `tags`），**没有** Danbooru 的 `tag_string` / `file_url` /
`media_asset`；评级词表也是 e621 自己的 `rating:s` / `rating:q` / `rating:e`，首字母不是 `s` / `q` / `e`
的取值（例如 Danbooru 的 `rating:g`）会被服务端静默丢弃，不报错。
本面不提供原生写方法：需要写操作时用通用 `request()` 显式指定方法与路径。
需要成员权限的 `related_tag` / `related_tag_bulk` 只有源码依据，未取得成功响应。
完整方法、参数与返回形态见
[docs/e621-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621-api.md)。

### 6. Zerochan 系站点（zerochan.net）

```python
from anybooru import Zerochan

# 'zerochan' 是 anybooru.json 中 sites 段的键名；该站点条目只有 url 一个字段。
with Zerochan('zerochan') as client:
    example = client.config['examples']['zerochan']

    for entry in client.entry_list(**example['entry_query']):  # 返回 items 信封里的列表
        print(entry['id'], entry['tag'], entry['md5'])

    detail = client.entry_show(example['entry_id'])            # 原样返回详情对象
    print(detail['id'], detail['primary'], detail['full'])
```

Zerochan 面只有 **2 个原生只读方法**：`entry_list(tags=None, strict=False, **params)` 与
`entry_show(entry_id)`。`tags` 省略走根路径、传字符串走单标签、传列表/元组把各标签名分别转义后
用逗号连接；`strict=True` 附加 `strict` 空标记（只匹配 primary 标签）。`p` / `l` / `s` / `t` / `d` / `c`
等查询值原样透传，客户端不补默认值。`request(path, *, params=None, envelope=None)` **恒为 `GET`**，
只发 JSON：自动附加 `json` 查询标记，而不是加 `.json` 路径后缀（`xml` 不在本库覆盖范围内）；
API 目前只读，本面没有任何写方法。实测列表项字段为 `id` / `width` / `height` / `md5` / `thumbnail` /
`source` / `tag` / `tags`，详情含 `small` / `medium` / `large` / `full` 等尺寸 URL——`md5` 与 `hash`
都是服务端返回的字段，本库不计算校验值。

按官方 API 页面，请求头 `User-Agent` **必须含项目名与自己的 Zerochan 用户名**；它来自
`request.user_agent` 配置项，而不是认证凭据，`Zerochan` 构造参数没有 `username` / `api_key`。
默认 `Anybooru/0.1.0.dev1` **未包含用户名，不满足完整要求**；请在自己的配置中补入。
匿名请求即使成功，仍有被封禁的风险。文档限流为 60 请求/分钟，客户端不做限速，
示例两次调用之间按 `examples.zerochan.pause_seconds` 暂停。

本家族**没有公开的引擎源码**，契约依据是官方 API 页面快照加真实请求实测：逐条出处、文档与实现的
差异和排除项见
[docs/zerochan-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-contract-notes.md)，
方法参考见 [docs/zerochan-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-api.md)，
客户端用法见 [docs/zerochan.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan.md)。

## 文档

文档全部为 `docs/` 下的中文 Markdown：

| 文档 | 内容 |
| :--- | :--- |
| [docs/index.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/index.md) | 文档索引与设计立场 |
| [docs/danbooru-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru-capabilities.md) | 能做什么、匿名能做什么、想做某件事该用哪个方法 |
| [docs/installation.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/installation.md) | 安装、环境要求、配置文件放哪 |
| [docs/configuration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/configuration.md) | 默认配置来源、`config_file` 覆盖与 `anybooru.json` 完整样例 |
| [docs/authentication.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/authentication.md) | 认证与权限 |
| [docs/pagination.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/pagination.md) | 分页与游标 |
| [docs/errors.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/errors.md) | 异常与状态码 |
| [docs/danbooru.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru.md) | Danbooru 客户端与 `request()` 通用入口 |
| [docs/danbooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru-api.md) | Danbooru 各 API 面与端点清单 |
| [docs/moebooru.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru.md) | Moebooru 客户端与 `request()` 通用入口 |
| [docs/moebooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru-api.md) | Moebooru 各 API 面与端点清单 |
| [docs/moebooru-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru-capabilities.md) | Moebooru 能做什么、想做某件事该用哪个方法 |
| [docs/serika.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika.md) | Serika 客户端、信封拆封与二进制响应 |
| [docs/serika-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika-api.md) | 官方 v1 路由、参数、权限与文档矛盾 |
| [docs/serika-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika-capabilities.md) | 两层能力、站内私有匿名读取与未实测边界 |
| [docs/e621.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621.md) | e621ng 客户端、`request()` 通用入口与信封规则 |
| [docs/e621-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621-api.md) | e621ng 18 个原生只读方法、参数与返回形态 |
| [docs/e621-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621-capabilities.md) | e621ng 能做什么、想做某件事该用哪个方法 |
| [docs/zerochan.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan.md) | Zerochan 客户端、参数编码与 `request()` 通用入口 |
| [docs/zerochan-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-api.md) | Zerochan 两个原生方法、路由与返回形态 |
| [docs/zerochan-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-capabilities.md) | Zerochan 能做什么、想做某件事该用哪个方法 |
| [docs/migration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/migration.md) | 从上游 4.x 迁移 |
| [docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md) | 线上验证状态：已实测与未实测清单 |

可运行示例见 [examples/](https://github.com/NebulaeWisdom/anybooru/tree/master/examples)：

- `examples/danbooru/`：六个匿名只读示例（`list_posts.py`、`list_tags.py`、`show_post.py`、
  `paginate_posts.py`、`related_tag.py`、`wiki_page.py`），默认站点取自 `examples.danbooru.site`；
  另有 `comment_create.py`，它是**真实的 POST 写示例**（发表评论）：需要账号与 API key，本仓库不带
  凭据，**未执行、未实测**，写路径只做了源码层面的上游对齐；
- `examples/moebooru/`：Moebooru 系站点的五个匿名只读示例（`list_posts.py`、`list_tags.py`、
  `wiki_list.py`、`list_comments.py`、`related_tags.py`），默认站点取自 `examples.moebooru.site`（当前为
  yande.re），不发写请求。
- `examples/serika/`：`service_info.py`（官方匿名信息）、`browse.py`（站内匿名浏览）、
  `random_image.py`（官方匿名图片字节），参数从 `examples.serika` 读取，不调用需 key 路由。
- `examples/e621/`：`list_posts.py`（帖子列表、详情与随机帖）、`browse_resources.py`（标签、画师、
  评论、合集、笔记）、`wiki_pages.py`（wiki 列表与单个标题），匿名只读，参数从 `examples.e621` 读取。
- `examples/zerochan/`：`list_entries.py`（条目列表与配置里的单条目详情）、`filter_entries.py`
  （单标签、多标签与 `strict` 三种过滤），匿名只读，参数从 `examples.zerochan` 读取，两次调用之间按
  `pause_seconds` 暂停。

示例中的关键词、ID 等参数一律从配置文件的 `examples` 段读取，不在示例里硬编码站点、代理、
分页。脚本默认读包内那份 `anybooru.json`，用 `--config` 可指向别处。

## 贡献

请在动手前阅读
**[CONTRIBUTING.md](https://github.com/NebulaeWisdom/anybooru/blob/master/CONTRIBUTING.md)**。

## 许可

- **[MIT License](https://github.com/NebulaeWisdom/anybooru/blob/master/LICENSE)**
