# ArtStation 客户端用法

`ArtStation` 访问 `https://www.artstation.com` 的公开作品集资源与 RSS，**不套用 booru 的帖子模型**。
作品有数字 `id` 和短码 `hash_id`：例如作品 `22900098` 的短码是 `1LxzVq`，网页地址为
`https://www.artstation.com/artwork/1LxzVq`；评论路径用数字 ID，两者不能互换。

本类有 **15 个原生 GET：14 个 JSON 读取与 1 个 RSS 读取**，没有凭据字段、登录或原生写方法。
完整方法与参数只放在 [方法参考](artstation-api.md)，按任务查 [能力入口](artstation-capabilities.md)。

## 三行上手

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    projects = client.project_list(page=1, per_page=2)
    print(projects['total_count'], [item['hash_id'] for item in projects['data']])
    print(client.last_call['status_code'], client.last_call['url'])
```

真实请求：`GET https://www.artstation.com/projects.json?page=1&per_page=2`。
本轮 200，返回完整 `{"data":[…],"total_count":14522955}`；首条 `id=22900098`、
`hash_id='1LxzVq'`、`title='Field Journal'`。这些数字是快照，不是客户端常量。

## 构造与配置

```python
ArtStation(site_name=None, site_url=None, proxies=None, *,
           config_file=None, timeout=None, user_agent=None)
```

| 参数 | 含义与取值 | 不传时 | 可抄示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | `sites` 中的站点键 | 不选命名站点，需显式给 `site_url` | `ArtStation('artstation')` |
| `site_url` | 站点基地址字符串 | 读所选站点的 `url` | `ArtStation(site_url='https://www.artstation.com')` |
| `proxies` | requests 的代理字典，`{}` 表示直连 | 读 `request.proxies` | `ArtStation('artstation', proxies={})` |
| `config_file` | 完整 JSON 配置文件路径；`None` 用包内配置 | 读随包安装的 `anybooru.json` | `ArtStation('artstation', config_file='my-anybooru.json')` |
| `timeout` | 秒数或连接/读取超时二元组 | 读 `request.timeout` | `ArtStation('artstation', timeout=30)` |
| `user_agent` | 应用自己的 User-Agent 字符串 | 读 `request.user_agent` | `ArtStation('artstation', user_agent='MyArtClient/1.0')` |

包内 `sites` 的新增条目只有地址：

```json
{"artstation": {"url": "https://www.artstation.com"}}
```

构造不联网；默认匿名，不从配置读取用户名、密码、API key 或 Cookie，也不生成认证头。
通用请求可显式传 `headers`，但这不代表本库提供了认证方案或保证账号能力可用。
配置文件不存在就抛错，不搜索当前目录、不回落另一份配置、不读环境变量。
用 `with` 自动释放会话，或结束时调用 `client.close()`。

## 搜索、过滤与分页

搜索必须明确给 `page` 和 `per_page`，不是默认第 1 页、默认 50 条。
每页 3 与 75 条都有成功样本，2 和 76 都被站点以 400 拒绝。客户端不替你补值或钳位。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    search_results = client.project_search(
        query='cat', page=1, per_page=3, sorting='relevance')
    print(search_results['total_count'], search_results['data'][0]['title'])
```

真实 URL：`https://www.artstation.com/api/v2/search/projects.json?query=cat&page=1&per_page=3&sorting=relevance`。
本轮 200，`total_count=118784`，首条 `id=10122141,title='Cat Cat Cat'`；作品地址键为 `url`，
缩略图键为 `smaller_square_cover_url`，不是全站列表的 `permalink/cover`。

**GET 的 `filters` 要传 JSON 字符串。** 不要直接传 Python 列表让共享编码器把它变成
`filters[][field]` 之类的查询键；该形态本轮收到 400 `{"data":"filters should be a string"}`。

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    for page in (1, 2):
        projects = client.project_search(
            query='', page=page, per_page=3, sorting='relevance',
            filters='[{"field":"title","method":"contain","value":"dragon"}]')
        print(page, [item['title'] for item in projects['data']])
```

第 1 页真实 URL：
`https://www.artstation.com/api/v2/search/projects.json?query=&page=1&per_page=3&sorting=relevance&filters=%5B%7B%22field%22%3A%22title%22%2C%22method%22%3A%22contain%22%2C%22value%22%3A%22dragon%22%7D%5D`。
两页均有 200 样本；第 1 页标题为 `Dragon and mouse`、`Omakase! Dragonslayer :: 屠龍`、
`Dragon's Breath`。使用者应按站点要求控制请求频率；配置示例脚本会在每次请求前暂停。

其它列表也用 `page/per_page`，但边界不同：全站每页 50 成功、51 报 400；专辑 4 成功、3 报 400；
Explore 10 成功、9 报 400。全站超深页报 400 空正文，用户作品超深页则为 200 空 `data`。
不要给所有路由套一套默认值或终止规则；本库不自动翻页。更多见 [分页](pagination.md#artstation-的分页)。

## 返回值：完整对象，不拆 data

| 调用种类 | 实际拿到什么 |
| :--- | :--- |
| 大部分列表与搜索 | `{"data":[…],"total_count":N}`，键序不保证 |
| `explore_latest` | `{"data":[…]}`，**没有 total_count** |
| `project_random` | 一个作品对象，含 `id/hash_id/assets/tags/user`，没有 data 外层 |
| 用户资料三条路由 | 用户对象，字段集各自不同，不合并 |
| `search_filter_fields` | 数组，条目有 `name/type`，部分另有 `select_options` |
| `feed` | 完整 RSS 字符串，声明、根节点、空白一并保留 |

全站作品条目含 `user/views_count`，用户作品条目本轮没有这两个键；专辑条目直接含 `assets`，
搜索条目不含完整资产。**相同列表结构不表示条目字段相同。** 每条路由的真实字段见方法参考。

例如随机作品是详情对象，但不能指定作品编号：

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    project = client.project_random()
    print(project['id'], project['hash_id'], len(project['assets']))
    feed_xml = client.feed(sorting='latest')
    print(feed_xml[:60])
```

真实请求分别为 `https://www.artstation.com/random_project.json`（200 JSON）与
`https://www.artstation.com/artwork.rss?sorting=latest`（200 `application/rss+xml; charset=utf-8`）。
随机样本各次不同；RSS 本轮为 RSS 2.0、50 个 item。本库不解析 RSS、不访问其中链接。

## 通用入口 `request()`

```python
request(method, path, *, params=None, data=None, headers=None,
        response_format='json')
```

| 参数 | 含义 | 不传时 | 示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词，显式发送；原生方法都是 GET | 必填 | `'GET'` |
| `path` | 相对配置基址的路径；去掉前导 `/`，不自动补 `.json` | 必填 | `'projects.json'` |
| `params` | 查询字典，走共享 Rails 编码 | 不加查询参数 | `{'page': 1, 'per_page': 2}` |
| `data` | JSON 正文，值原样发送，包括内部 `None` | 不发 JSON 正文 | 原生读取不需要正文；非 GET 未实测 |
| `headers` | 本次请求头字典，合并到会话默认头 | 默认 Accept 为 application/json | `{'Accept': 'application/rss+xml'}` |
| `response_format` | `json` 解析完整 JSON；`xml/html` 返回 `.text` 原文 | `json` | `'html'` |

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    projects = client.request('GET', '/projects.json', params={'page': 1, 'per_page': 2})
    print(projects['total_count'])
    html = client.request('GET', '/openapi.json', response_format='html')
    print(html[:60])
```

`/projects.json` 与 `projects.json` 同义；不是绝对 URL 转发器。
`/openapi.json` 的匿名直接响应实际是 **200 HTML Explore 页**，不是 OpenAPI。
默认 JSON 入口不会自动改读 HTML，而是抛 `AnybooruAPIError`；选择 `html` 才返回原文。
返回格式不是 `json/xml/html` 时由映射抛 `KeyError`，不会猜格式。

查询值为 `None` 时省略；布尔编码为小写 `true/false`；字典/序列使用 `key[child]` / 重复 `key[]`。
原生路径中的用户名、评论作品 ID 逐段百分号编码；`album_id/channel_id` 是查询参数，不是路径段。
`filters` 的 JSON 字符串由调用者准备，客户端不特殊处理它。
默认保留 requests 的重定向行为；仓库冒烟与示例明确关闭重定向，避免把一次调用变成隐含多次请求。

## last_call 与错误

`client.last_call` 保留最后响应的 `API`（去前导斜杠的路径）、`url`（编码后的完整 URL）、
`status_code`、`status`（原因文本）和 `headers`。请求发生传输异常、尚无响应时可能为空。

```python
from anybooru import ArtStation, AnybooruHTTPError

with ArtStation('artstation') as client:
    try:
        client.project_search(query='cat', page=1, per_page=2)
    except AnybooruHTTPError as error:
        print(error.http_code, error.data, error.body)
        print(client.last_call['url'], client.last_call['headers']['Content-Type'])
```

真实 URL：`https://www.artstation.com/api/v2/search/projects.json?query=cat&page=1&per_page=2`；
本轮 400、JSON `{"message":"per_page should be >= 3","code":"per_page"}`。
其它 400 也可能是 `{"data":"…"}` 或空正文，不要总读 `message`。
`AnybooruHTTPError` 保留 `http_code/url/body/data/response`；正文不是 JSON 时 `data=None`。
2xx 非 JSON 在默认 JSON 通路中抛 `AnybooruAPIError`，空的成功正文沿共享传输返回 `None`。
没有失败回退、重试或空结果伪装；通用异常说明见 [错误处理](errors.md)。

## 媒体地址：只返回字符串，本库不下载

`cover`、`assets[].image_url/small_image_url/large_image_url` 和搜索缩略图键里的 URL 都原样保留。
不推导文件名、不换 CDN 分片、不把尺寸改成 4k/8k、不删缓存查询串。
本轮没有请求任何媒体；返回一个地址不能证明它当前可下载或获准使用。

## 可运行示例与冒烟脚本

```bash
python -X utf8 examples/artstation/list_projects.py --config my-anybooru.json
python -X utf8 examples/artstation/browse_resources.py --config my-anybooru.json
python -X utf8 test/artstation.py --config my-anybooru.json
```

不传 `--config` 使用包内配置。示例还有 `--site`，缺省来自 `examples.artstation.site`；查询值来自
`examples.artstation`，对应上文 `project_list(page=1,per_page=2)`、按标题 dragon 的搜索以及
`user_show('timwarnock')`、`album_projects(104104,page=1,per_page=4)` 等字面调用。
冒烟使用 `smoke.artstation`。本轮两个示例各 4 请求、冒烟 10 请求，全部退出 0；
冒烟包括预期 404/400，汇总为 `SUMMARY artstation | requests=10 | passed=10 failed=0`。
逐条命令、UTC、URL 与响应摘要只放在 [验证记录](verification.md#artstation匿名只读实测2026-09-20)。

## 边界与未实测

- 两条指定作品样本 `/projects/G1ew2N.json` 和 `/api/v2/community/projects/22897630.json` 分别为
  403 HTML 挑战与 401 `{"data":null}`，没有 `project_show`；随机/搜索/专辑不是失败后的自动备用路径。
- POST 搜索、CSRF、所有写请求与凭据成功未测；不根据 401 猜认证方式，不解挑战。
- 只有少量分页、`sorting=relevance`、`title contain dragon` 与 RSS `latest` 样本；缺省值、其它排序、
  过滤组合、全部每页上限与精确末页未穷举。非空评论、随机分布和非空 tags 元素类型也未测。
- 未取得官方 API 规范或服务端源码，不把输入资料当本轮证据；未知路径 200 不等于全站没有 404。
- [服务条款](https://www.artstation.com/tos) 对采集与规避访问控制有限制，匿名可读不等于许可。
  本库不提供批量遍历器或媒体下载器。

完整依据、输入矛盾及未实测清单见 [契约附注](artstation-contract-notes.md#6-边界与未实测)。
