# Pybooru - Danbooru / Moebooru / Serika 图站 API 客户端

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/LuqueDaniel/pybooru/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/Pybooru.svg?style=flat-square)](https://pypi.python.org/pypi/Pybooru/)

**Pybooru** 是用 Python 访问 Danbooru、Moebooru 与 Serika 三类引擎图站 API 的客户端库。

本库按对应引擎的路由与控制器对齐契约，适用于运行相同引擎的实例，不只支持几个固定站点。
Serika 是独立的 Next.js 引擎；其官方 v1 与前端私有的非版本化 API 分开标注，不混同 Rails 两家。

- 版本：**5.0.0.dev1**（开发版，尚未发布到 PyPI）
- 许可：**MIT License**

## 运行要求

- Python >= 3.6
- [requests](https://requests.readthedocs.io/) >= 2.26

## 安装

### 从源码安装（当前开发版）

```bash
git clone https://github.com/LuqueDaniel/pybooru.git
cd pybooru
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .        # Windows
.venv/bin/python -m pip install -e .                # Linux / macOS
```

### 从 PyPI 安装

```bash
pip install --user Pybooru
```

> 本次重构尚未发布；普通 PyPI 安装不保证包含这里的新接口。要使用本轮实现，请从包含这些提交的源码安装。

安装后不需要额外准备配置文件：包内自带一份可用的 `pybooru.json`，构造函数默认就读它。

## 快速开始

### 1. 配置文件

所有站点、凭据、代理、超时等参数集中放在一份 JSON 文件里，不在调用处硬编码，也不用环境变量注入。
这份文件**随包安装**，`Danbooru('danbooru')` 这类调用默认读它：

```json
{
  "request": {
    "timeout": 30,
    "proxies": { "http": "http://proxy.example:8080", "https": "http://proxy.example:8080" },
    "user_agent": "Pybooru/5.0.0.dev1"
  },
  "sites": {
    "danbooru": { "url": "https://danbooru.donmai.us", "username": "", "api_key": "" }
  },
  "examples": {
    "danbooru": { "site": "danbooru", "tags": "rating:g", "limit": 3, "post_id": 1, "comment_body": "示例评论" }
  }
}
```

要改站点、凭据或代理，复制那份包内文件改一份自己的，再把路径交给 `config_file`；当前工作目录里的
同名文件**不会**被自动读取。

```python
import shutil
from pybooru import Danbooru, DEFAULT_CONFIG_FILE

print(DEFAULT_CONFIG_FILE)                                     # 包内默认配置的绝对路径
shutil.copy(DEFAULT_CONFIG_FILE, 'config/sites.json')          # 拿它当模板

client = Danbooru('danbooru')                                  # 读包内默认配置
client = Danbooru('danbooru', config_file='config/sites.json') # 读自己那份
```

`config_file` 指到的文件不存在时直接抛 `FileNotFoundError`，不会退回到默认文件。`sites` 段是
**样例 / 起始清单，不是支持边界**：名单外的同引擎站点可以直接用 `site_url`（Moebooru 另需
`api_version`）接入，见
[docs/configuration.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/configuration.md#sites-段)。

完整的默认配置样例（含三类引擎站点、`examples`、`verification` 段）见
[docs/configuration.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/configuration.md)。

### 2. Danbooru 系站点

```python
from pybooru import Danbooru

# 'danbooru' 是 pybooru.json 中 sites 段的键名；URL、代理、超时、凭据都来自配置。
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

画师查询的参数与上游匹配语义见
[Danbooru API 契约](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru-api.md#artists)。

### 3. Moebooru 系站点（如 yande.re / konachan）

```python
from pybooru import Moebooru

# 'yandere' 是 pybooru.json 中 sites 段的键名；Moebooru 面没有 search 字典，
# 过滤条件（tags、limit、page 等）就是顶层参数。
client = Moebooru('yandere')
example = client.config['examples']['moebooru']

for post in client.post_list(tags=example['tags'], limit=example['limit']):
    print(post['file_url'])

client.close()
```

Moebooru 面已按上游 `moebooru/` 的路由与控制器对齐（90 个原生方法，覆盖帖子、合集、笔记、标签、
画师、评论、wiki、论坛与账号端点）；匿名只读端点的执行记录见
[docs/verification.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/verification.md)，
需要登录的写接口只做源码对齐、未做线上实测。完整清单见
[docs/moebooru-api.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/moebooru-api.md)。

### 4. Serika 系站点（serika.art 及自托管实例）

```python
from pybooru import Serika

with Serika('serika') as client:
    example = client.config['examples']['serika']
    print(client.stats())  # 官方 v1，匿名可达；返回 data，meta 留在 last_call
    result = client.internal_image_list(**example['image_query'])
    for image in result['images']:  # 站内非版本化私有契约，原始 JSON 信封
        print(image['id'], image['post_id'], image['url'])
```

模块 `pybooru.serika` 的 `Serika` 类与 `api_serika` 的方法集覆盖 **16 个官方 v1 方法**及
**14 个站内匿名读方法**。官方需 key 的 12 个方法仅源码对齐，未实测；配置 key 留空，
不实现站内 cookie 登录。随机图片方法返回原始 `bytes`，不会按 JSON 解析。
v1 图片路径用内部 `id`，站内详情用顺序号 `post_id`，两者不能互换。
使用方式见 [docs/serika.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/serika.md)。

## 文档

文档全部为 `docs/` 下的中文 Markdown：

| 文档 | 内容 |
| :--- | :--- |
| [docs/index.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/index.md) | 文档索引与设计立场 |
| [docs/danbooru-capabilities.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru-capabilities.md) | 能做什么、匿名能做什么、想做某件事该用哪个方法 |
| [docs/installation.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/installation.md) | 安装、环境要求、配置文件放哪 |
| [docs/configuration.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/configuration.md) | 默认配置来源、`config_file` 覆盖与 `pybooru.json` 完整样例 |
| [docs/authentication.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/authentication.md) | 认证与权限 |
| [docs/pagination.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/pagination.md) | 分页与游标 |
| [docs/errors.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/errors.md) | 异常与状态码 |
| [docs/danbooru.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru.md) | Danbooru 客户端与 `request()` 通用入口 |
| [docs/danbooru-api.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru-api.md) | Danbooru 各 API 面与端点清单 |
| [docs/moebooru.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/moebooru.md) | Moebooru 客户端与 `request()` 通用入口 |
| [docs/moebooru-api.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/moebooru-api.md) | Moebooru 各 API 面与端点清单 |
| [docs/moebooru-capabilities.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/moebooru-capabilities.md) | Moebooru 能做什么、想做某件事该用哪个方法 |
| [docs/serika.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/serika.md) | Serika 客户端、信封拆封与二进制响应 |
| [docs/serika-api.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/serika-api.md) | 官方 v1 路由、参数、权限与文档矛盾 |
| [docs/serika-capabilities.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/serika-capabilities.md) | 两层能力、站内私有匿名读取与未实测边界 |
| [docs/migration.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/migration.md) | 从 Pybooru 4.x 迁移 |
| [docs/verification.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/verification.md) | 线上验证状态：已实测与未实测清单 |

可运行示例见 [examples/](https://github.com/LuqueDaniel/pybooru/tree/master/examples)：

- `examples/danbooru/`：Danbooru 系站点的列表、详情、分页、相关标签、评论等示例；
- `examples/moebooru/`：Moebooru 系站点的五个匿名只读示例（`list_posts.py`、`list_tags.py`、
  `wiki_list.py`、`list_comments.py`、`related_tags.py`），默认站点取自 `examples.moebooru.site`（当前为
  yande.re），不发写请求。
- `examples/serika/`：`service_info.py`（官方匿名信息）、`browse.py`（站内匿名浏览）、
  `random_image.py`（官方匿名图片字节），参数从 `examples.serika` 读取，不调用需 key 路由。

示例中的关键词、ID 等参数一律从配置文件的 `examples` 段读取，不在示例里硬编码站点、代理、
分页。脚本默认读包内那份 `pybooru.json`，用 `--config` 可指向别处。

## 贡献

请在动手前阅读
**[CONTRIBUTING.md](https://github.com/LuqueDaniel/pybooru/blob/master/CONTRIBUTING.md)**。

## 许可

- **[MIT License](https://github.com/LuqueDaniel/pybooru/blob/master/LICENSE)**
