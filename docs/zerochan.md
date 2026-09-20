# Zerochan 客户端用法

`entry_list` 传入页码、标签等条件，返回**图片列表**。`entry_show` 传入图片编号，返回这张图的地址、宽高、文件大小、来源、标签。全部参数和例子见[方法参考](zerochan-api.md)。

## 第一次调用

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:  # 站点地址和请求设置来自包内 anybooru.json
    entries = client.entry_list(p=1, l=2, s='id')
    # GET https://www.zerochan.net/?p=1&l=2&s=id&json=
    # 返回图片列表；每项有 id（图片编号）、tag（主标签）、tags（全部标签）、width、height 等字段。
    print([(entry['id'], entry['tag']) for entry in entries])
    print(client.last_call['status_code'], client.last_call['url'])
```

意思是：**第一页，每页两张图，按新到旧排序**。`entries` 是 Python 列表，不是带 `items` 的字典；库已从服务端的 `{"items": [...]}` 中取出数组。

## 构造与配置

签名：`Zerochan(site_name=None, site_url=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。

| 参数 | 类型与含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置里的站点名 | 不选站点，必须提供 `site_url` | `Zerochan('zerochan')` |
| `site_url` | 字符串，站点根地址 | 使用所选站点的地址 | `Zerochan(site_url='https://www.zerochan.net')` |
| `config_file` | 配置文件路径 | 默认读包内 `anybooru.json`；给路径才读别的文件；文件不存在抛 `FileNotFoundError` | `Zerochan('zerochan', config_file=None)` |
| `proxies` | 字典，代理设置；`{}` 表示不使用代理 | 使用 `request.proxies`，包内为 `{}`；不读环境变量 | `Zerochan('zerochan', proxies={})` |
| `timeout` | 超时秒数，也可给连接/读取超时二元组 | 使用 `request.timeout`，包内为 `30` | `Zerochan('zerochan', timeout=10)` |
| `user_agent` | 字符串，请求的 User-Agent 标识 | 使用 `request.user_agent`，默认 `Anybooru/0.1.0.dev1` | `Zerochan('zerochan', user_agent='Anybooru/0.1.0.dev1')` |

User-Agent 必须包含项目名和你自己的 Zerochan 用户名。包内默认 `Anybooru/0.1.0.dev1` 只有项目标识，没有用户名；请在自己的配置中补入。匿名请求可能成功，但官方提示匿名项目可能被封禁。这不是账号登录：客户端没有 `username`、`password` 或 `api_key` 参数，也不实现登录会话。

`with` 结束关闭网络连接；不用 `with` 时，调用完执行 `client.close()`。

## 通用 request()：保留外层 items

`request` 返回服务器发来的整个 JSON 字典。下面仍请求两张图片，但返回值保留了外层 `items`，要用 `body['items']` 才能拿到图片列表：

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    body = client.request('/', params={'l': 2})
    # GET https://www.zerochan.net/?l=2&json=
    # 返回字典 {"items": [...]}；每项含 id、tag、tags、width、height 等字段。
    print(list(body))  # ['items']
    print([(entry['id'], entry['tag']) for entry in body['items']])
```

* `path` 是相对路径，开头的 `/` 会去掉；根列表用 `/` 或空字符串。
* 客户端在 URL 后加 `json=` 告诉站点返回 JSON，**不是**在路径后加 `.json`。
* `params` 是要放进 URL 的参数：`{'l': 2}` 就是 `l=2`；值为 `None` 时不发送该参数。用 `request` 手写标签路径时需要自己处理空格等字符，`entry_list` 会替你处理。
* `envelope` 控制是否拆开外层字典：默认不拆，填 `'items'` 就只返回 `items` 对应的列表。`entry_list` 本来就返回这个列表；`entry_show` 返回的是那张图片的信息，没有再套一层。

## 标签与参数编码

标签放在 URL 路径里，不是 Danbooru 风格的搜索字符串：

| 传入的 `tags` | 发出的路径 | 含义 |
| :--- | :--- | :--- |
| 不传 | `/` | 不按标签筛选图片 |
| `'Genshin Impact'` | `/Genshin+Impact` | 一个标签，空格编码为 `+` |
| `['Lumine', 'Flower']` | `/Lumine,Flower` | 两个标签，逐个编码后用逗号连接 |

字符串不按空格或逗号拆分，大小写保持原样。名字中的特殊字符由客户端转义；不要把 `rating:`、`order:` 等其它家族的搜索语法套进来。

`p` / `l` / `s` / `t` / `d` / `c` 是普通查询参数。`strict=True` 是 Python 开关，实际发送 `strict=`（等号后没有值）；它要求图片的**主标签**就是你输入的那个标签。单标签、多标签和 strict 的完整调用见[方法参考](zerochan-api.md#按标签过滤)。

## 返回值与 last_call

| 你给什么 | 它返回什么 |
| :--- | :--- |
| `entry_list`：页码、每页数量、标签或其它筛选条件 | 图片列表；每项有图片编号 `id`、宽高、缩略图地址 `thumbnail`、来源 `source`、主标签 `tag`、标签数组 `tags` |
| `entry_show`：一张图的编号（也常叫 pid） | 这张图的四种尺寸地址 `small` / `medium` / `large` / `full`、宽高、文件大小 `size`、来源 `source`、主标签 `primary`、标签数组 `tags` |
| `request`：相对路径和查询参数 | 服务器返回的整个 JSON；例如图片列表仍包在 `{"items": [...]}` 里面 |

`last_call` 的 `url` 是实际请求 URL，`status_code` 是 HTTP 状态码；还有 `API`（相对路径）、`status`（状态文字）和 `headers`（响应头）。第一个例子已演示如何打印它们。非 2xx 抛 `AnybooruHTTPError` 并保留正文；2xx 非 JSON 抛 `AnybooruAPIError`；网络异常由 requests 原样抛出。详见[错误处理](errors.md)。

## 可运行示例

仓库里的 `list_entries.py` 演示列表和详情，`filter_entries.py` 演示单标签、多标签与 strict。`examples.zerochan` 这组配置键给脚本提供站点、参数、图片编号和请求间隔，例如 strict 那组参数就是 `client.entry_list(tags='Genshin Impact', strict=True, l=2)`。脚本支持 `--config` / `--site`；已执行的命令和输出见[验证记录](verification.md#zerochan匿名只读实测2026-09-18)。

## 边界与未实测

* 不传 `l` 时曾观察到 **48 张图**；API 页面没有规定默认数量。服务器只返回 `{"items": [...]}`，没有图片总数、当前页码或下一页地址；翻页要自己传 `p` / `l`，客户端不会替你发下一次请求。
* `s='fav', t=0` 已返回 **500**，正文是不完整 JSON；`t=1` / `t=2` 有成功响应。库不修复正文、不重试。
* 官方说明单标签和 strict 端点**不适用于 meta 标签**；本轮未实测其具体拒绝响应。
* API 页面还提到 XML，但本库**只实现 JSON**；不实现写操作、登录会话或 HTML 抓取。已观察到 `/3793685` 不带 `json` 返回 HTML，加 `json` 后才是 JSON。
* 官方限流 **60 请求/分钟**，长期超限可能封禁；这里只说明要求，客户端没有内置限速，调用者自行安排请求节奏。
* `d=square` 的样本包含 `1006×966`，不能理解成宽高严格相等；large/huge 的阈值没有页面依据。
* 缺失条目已实测：`/999999999?json=` 返回 **404**，抛 `AnybooruHTTPError`，正文 6 字符、`data` 是字典（见[验证记录](verification.md#轻量匿名冒烟脚本十站单轮执行2026-09-18)）。
* 尚未实测：合规用户名 UA、特殊字符标签的服务端匹配、strict 多标签组合、其余参数组合、非法参数、分页边界、空结果、限流/封禁响应、XML 和其它部署。

[方法参考](zerochan-api.md) · [能力入口](zerochan-capabilities.md) · [接口依据](zerochan-contract-notes.md)
