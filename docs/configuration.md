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
    "lolibooru": {
      "url": "https://lolibooru.moe",
      "username": "",
      "password": "",
      "api_version": "1.13.0+update.3",
      "hash_string": null
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
      "site": "konachan",
      "tags": "rating:s",
      "limit": 3,
      "post_id": 1,
      "comment_body": "示例评论"
    }
  }
}
```

## `request` 段

| 键 | 类型 | 说明 |
| :--- | :--- | :--- |
| `timeout` | number | 单次请求超时秒数，默认 `30`；写成数组时按 requests 的 (连接超时, 读取超时) 处理 |
| `proxies` | object | 传给 requests 的代理字典，键为 `http` / `https` |
| `user_agent` | string | 请求头 `User-Agent` |

## `sites` 段

每个键是一个站点名，值是**同一个名称**在客户端构造函数中引用到的配置。

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

同一个站点名在 Danbooru 与 Moebooru 两个客户端里含义一致：都是 `sites` 段的键。

## `examples` 段

`examples` 段只服务于 `examples/` 目录下的可运行示例与文档片段：把**关键词、数量、ID**这类
调用参数放回配置文件，示例脚本本身不硬编码站点、代理和分页。

| 键 | 所属 | 说明 |
| :--- | :--- | :--- |
| `site` | 两者 | 传给客户端构造函数的站点名，对应 `sites` 段的键 |
| `tags` | 两者 | 搜索关键词 |
| `limit` | 两者 | 单页数量 |
| `pages` / `tag_search` / `preview_chars` | Danbooru | 编号分页示例的页码数组、标签查询字典、wiki 正文显示长度 |
| `post_id` | 两者 | 帖子 ID（示例优先改用列表返回的首个 ID，见 [danbooru.md](danbooru.md)） |
| `comment_body` | 两者 | 评论正文示例 |
| `wiki_query` / `wiki_title` | Danbooru | wiki 页面查询词与标题 |
| `related_query` / `related_category` / `related_order` | Danbooru | 相关标签查询参数 |
| `search_sample_size` / `tag_sample_size` | Danbooru | 相关标签查询的样本规模 |

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
