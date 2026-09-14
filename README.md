# Pybooru - Danbooru / Moebooru 图站 API 客户端

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/LuqueDaniel/pybooru/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/Pybooru.svg?style=flat-square)](https://pypi.python.org/pypi/Pybooru/)

**Pybooru** 是用 Python 访问 Danbooru 系与 Moebooru 系图站 API 的客户端库。

Danbooru 与 Moebooru 是被大量图站采用的引擎模板，因此本库对齐的是这两套引擎的公共契约，而不是某两个
具体站点的私有行为。

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

安装不会自动创建配置文件；无论哪种方式，都要自己准备一份 `pybooru.json`。

## 快速开始

### 1. 准备根配置文件

所有站点、凭据、代理、超时等参数集中放在一份 JSON 文件里，不在调用处硬编码，也不用环境变量注入：

```json
{
  "request": {
    "timeout": 30,
    "proxies": { "http": "http://proxy-host:port", "https": "http://proxy-host:port" },
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

`config_file` 默认为**当前工作目录**下的 `pybooru.json`：把它复制到你的应用工作目录，或用
`config_file` 显式指向别处。库不会去安装目录里找它，文件不存在时直接抛 `FileNotFoundError`，
也没有内置站点作为后备。

完整的根样例（含 Moebooru 站点、`examples`、`verification` 段）见
[docs/configuration.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/configuration.md)。

### 2. Danbooru 系站点

```python
from pybooru import Danbooru

# 'danbooru' 是 pybooru.json 中 sites 段的键名；URL、代理、超时、凭据都来自根配置。
client = Danbooru('danbooru', config_file='pybooru.json')
example = client.config['examples']['danbooru']

posts = client.post_list(tags=example['tags'], limit=example['limit'])
for post in posts:
    print(post['id'], post['rating'], post['tag_string'])

client.close()
```

需要登录的写接口在配置了 `username` / `api_key` 后自动使用 HTTP Basic 认证：

```python
client = Danbooru('danbooru', config_file='pybooru.json')
example = client.config['examples']['danbooru']
client.comment_create(post_id=example['post_id'], body=example['comment_body'])
```

按 URL 查画师、pixiv 作者 ID 转 tag 的完整流程见
[docs/danbooru-artists.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru-artists.md)。

### 3. Moebooru 系站点（如 yande.re / konachan）

```python
from pybooru import Moebooru

client = Moebooru('konachan', config_file='pybooru.json')
example = client.config['examples']['moebooru']

posts = client.post_list(tags=example['tags'], limit=example['limit'])
for post in posts:
    print(post['file_url'])
```

Moebooru 面的 API 文件本轮未重写，只同步了共享配置用法；其线上可用性尚未验证，详见
[docs/moebooru.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/moebooru.md)。

## 文档

文档全部为 `docs/` 下的中文 Markdown：

| 文档 | 内容 |
| :--- | :--- |
| [docs/index.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/index.md) | 文档索引与设计立场 |
| [docs/installation.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/installation.md) | 安装、环境要求、配置文件放哪 |
| [docs/configuration.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/configuration.md) | 根配置文件 `pybooru.json` 完整样例 |
| [docs/authentication.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/authentication.md) | 认证与权限 |
| [docs/pagination.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/pagination.md) | 分页与游标 |
| [docs/errors.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/errors.md) | 异常与状态码 |
| [docs/danbooru.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru.md) | Danbooru 客户端与 `request()` 通用入口 |
| [docs/danbooru-api.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru-api.md) | Danbooru 各 API 面与端点清单 |
| [docs/danbooru-artists.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/danbooru-artists.md) | 按 URL 查画师、pixiv id → tag |
| [docs/moebooru.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/moebooru.md) | Moebooru 面现状与用法 |
| [docs/migration.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/migration.md) | 从 Pybooru 4.x 迁移 |
| [docs/verification.md](https://github.com/LuqueDaniel/pybooru/blob/master/docs/verification.md) | 线上验证状态：已实测与未实测清单 |

可运行示例见 [examples/](https://github.com/LuqueDaniel/pybooru/tree/master/examples)：

- `examples/danbooru/`：Danbooru 系站点的列表、详情、画师、相关标签、评论等示例；
- `examples/moebooru/`：Moebooru 系站点的对应示例。

示例中的关键词、ID 等参数一律从根配置文件的 `examples` 段读取，不在示例里硬编码站点、代理、
分页或作者 ID。

## 贡献

请在动手前阅读
**[CONTRIBUTING.md](https://github.com/LuqueDaniel/pybooru/blob/master/CONTRIBUTING.md)**。

## 许可

- **[MIT License](https://github.com/LuqueDaniel/pybooru/blob/master/LICENSE)**
