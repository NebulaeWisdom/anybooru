# Gelbooru 客户端用法

`Gelbooru` 从同一个 `index.php` 入口读取两种 JSON：官方 `page=dapi` 的帖子、标签、用户、评论和删除记录，以及站内 `page=autocomplete2` 的输入建议。后者可以匿名调用；前者使用账号的 `api_key` 与数字 `user_id`。

## 第一次调用：把 blue 补成可搜索的标签

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru') as client:
    suggestions = client.autocomplete('blue', type='tag', limit=3)
    # GET https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2
    # 返回数组；每项 label 是展示文字，value 是可放进标签搜索的名字。
    for suggestion in suggestions:
        print(suggestion['label'], suggestion['value'], suggestion['post_count'])
    print(client.last_call['status_code'], client.last_call['url'])
```

本次该请求返回 HTTP 200、**10 条**建议，不是请求中写的 3 条；首项 `label='blue eyes'`、`value='blue_eyes'`、`post_count='2817483'`。库没有截断数组；`limit` 是发送给服务器的参数，不是客户端切片。完整命令与响应摘要见[实测记录](verification.md#gelbooru匿名只读实测2026-09-18)。

## 构造与配置

签名：`Gelbooru(site_name=None, site_url=None, api_key=None, user_id=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 中的键名 | 不选命名站点，需显式给 `site_url` | `Gelbooru('gelbooru')` |
| `site_url` | 字符串，站点根地址，不带 `/index.php` 或查询串 | 读取所选站点的 `url` | `Gelbooru(site_url='https://gelbooru.com')` |
| `api_key` | 字符串，账号选项中的 API key；`''` 表示不附加 | 命名站点读取其 `api_key`；不选站点则为 `None` | `Gelbooru('gelbooru', api_key='')` |
| `user_id` | 数字账号 ID 或它的字符串形式，不是用户名；`''` 表示不附加 | 命名站点读取其 `user_id`；不选站点则为 `None` | `Gelbooru('gelbooru', user_id='')` |
| `proxies` | 字典，按 `http` / `https` 指定代理，`{}` 表示直连 | 使用 `request.proxies`，包内为 `{}`；不读环境变量 | `Gelbooru('gelbooru', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json`；指定文件不存在直接抛错 | `Gelbooru('gelbooru', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout`，包内为 `30` | `Gelbooru('gelbooru', timeout=10)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent`，包内为 `Anybooru/0.1.0.dev1` | `Gelbooru('gelbooru', user_agent='MyBooruApp/1.0')` |

包内站点条目为：

```json
{"gelbooru": {"url": "https://gelbooru.com", "api_key": "", "user_id": ""}}
```

这只是 `sites` 中的一个条目；复制完整配置的方法见[配置指南](configuration.md)。显式构造参数优先于配置，`None` 表示按上述规则读取，空字符串则是明确留空。`with` 退出时关闭连接，不使用 `with` 时调用 `client.close()`。

## 认证只随 dapi 请求发送

官方页面指定 URL 查询参数 `api_key` 和 `user_id`，不是 HTTP Basic 或 Bearer。两个值的来源是[账号选项](https://gelbooru.com/index.php?page=account&s=options)里的 API Access Credentials；本库不实现登录、申请 key 或账号会话。

填好自己的配置后，`post_list(limit=2)` 发到：

```text
https://gelbooru.com/index.php?limit=2&s=post&q=index&page=dapi&json=1&api_key=<你的API_KEY>&user_id=<你的数字账号ID>
```

这里只展示 URL 格式，不是已执行的请求。配置中的非空值各自附加到 dapi 查询串；空值不发送，不会在本地替服务器判断权限。`autocomplete` 不附加这两个配置值。`last_call['url']` 会保留实际查询串，分享账号请求记录前应去掉凭据。

## 通用 request：按 page 选择 JSON 入口

签名：`request(page, *, params=None)`。它没有 REST 相对路径、版本号、HTTP 方法或请求体参数，每次都发 GET 到 `<site_url>/index.php`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `page` | 必填字符串；官方 JSON 用 `'dapi'`，站内补全用 `'autocomplete2'` | Python 报缺参 | `client.request('autocomplete2', params={'term': 'blue', 'type': 'tag', 'limit': 3})` |
| `params` | 字典；dapi 用 `s` 选择资源、`q='index'` 选择读取动作，并带筛选条件 | 不附加调用方参数 | `client.request('dapi', params={'s': 'post', 'q': 'index', 'id': 1})` |

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru') as client:
    suggestions = client.request('autocomplete2',
                                 params={'term': 'blue', 'type': 'tag', 'limit': 3})
    # 与 autocomplete 一样返回建议数组，不改 label/value/post_count/category。
    print(suggestions)
```

`page` 由第一个参数确定；dapi 的 `json=1` 由客户端固定补入。原生方法另固定 `s`、`q` 和删除流的 `deleted=show`。客户端不为 `limit`、页码、排序补默认值。它也不设置 `envelope` 或按响应形状拆外层对象：若服务器返回字典，你拿到整个字典；若返回数组，你拿到整个数组。

## 参数编码与返回值

* 帖子搜索用字符串，例如 `tags='blue_hair solo rating:general'`。空格表示组合条件，编码到 URL 后为 `+`，冒号为 `%3A`；不要预先写 `%20` 或 `%25`，否则会再次编码。
* 标签名里的空格通常写成下划线，例如补全用 `'hatsune_miku'`。库不会把空格替换为下划线，也不会改变大小写。
* `tag_list(names='schoolgirl moon cat')` 的多个名字放在一个空格分隔字符串里，**不是** Python 列表；`name_pattern='%choolgirl%'` 的百分号由 requests 编码为 `%25`。
* 参数值为 `None` 不发送；整数直接编码成数值字符串。库不转换 dapi 与站内 HTML 的分页含义。
* dapi 返回结构尚无本站账号响应作为依据，原生方法也保留完整 JSON，具体候选字段与来源区分见[方法参考](gelbooru-api.md)。不会用 HTML 抓取或猜测字段填补响应。

`last_call` 在收到响应后保存 `API`（`page` 值）、`url`（最终 URL）、`status_code`、`status` 和 `headers`。非 2xx 抛 `AnybooruHTTPError`，保留真实状态、正文和能解析的 JSON；2xx 非 JSON 抛 `AnybooruAPIError`；空的成功正文按共享传输返回 `None`。requests 网络异常原样抛出，没有重试或换接口。

## 可运行示例

`examples/gelbooru/autocomplete.py` 只调用一次匿名补全，打印完整建议、数量及 `last_call` 中的状态码和 URL。`examples.gelbooru` 为脚本提供站点和查询参数，对应字面调用就是 `client.autocomplete('blue', type='tag', limit=3)`。支持 `--config` 和 `--site`，已执行命令集中在[验证记录](verification.md#gelbooru匿名只读实测2026-09-18)。

## 边界与未实测

* `post_list`、`post_deleted`、`tag_list`、`user_list`、`comment_list` 均为**未执行 / 未实测（需账号）**；包括认证成功、字段类型、外层结构、分页、上限和错误正文。已有外部资料报告匿名 dapi 为 401 空正文，本轮没有重发这些请求。
* 只有 `autocomplete('blue', type='tag', limit=3)` 的一组参数经本库实跑。其它补全种类、空查询、未知 `type`、空格名称、别名项及分页边界没有本轮响应证据。站点脚本出现的种类不等于每个服务端分支都已确认。
* `limit=3` 本次收到 10 条；脚本固定发 10，也不能由此推导服务器的默认值或最大值。
* 本库不封装 HTML 页面、不解析图片网页、不构造 CDN 地址，不做 XML、写操作、登录、自动翻页、限流或重试。标签列表、蕴含、别名、wiki 等网页的实际地址与用途见[网页入口表](gelbooru-capabilities.md#网页入口本库不封装)。
* 没有能作为当前服务端契约的官方 PHP 源码快照，也没有其它部署的旁证。官方页面、站点 JavaScript、外部记录与推断分开列在[契约附注](gelbooru-contract-notes.md)。

[方法参考](gelbooru-api.md) · [按目的找方法](gelbooru-capabilities.md) · [契约附注](gelbooru-contract-notes.md)
