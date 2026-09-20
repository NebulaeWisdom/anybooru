# Gelbooru02 客户端用法

`Gelbooru02` 访问自述为 **Gelbooru 0.2** 的图站。本家族只在 **TBIB（`https://tbib.org`）** 上核实过：首页页脚原文是 `Running Gelbooru 0.2`，页面没有 generator 元信息，不能推断具体的 0.2.x 补丁版本，也没有服务端源码快照可对照。其它 Gelbooru 0.2 部署没有检查过，不要拿 TBIB 的响应当它们的保证。

它和已有的 `Gelbooru` 客户端不是同一套接口约定：

- `Gelbooru` 假设 dapi 返回 JSON：`json=1` 后按 JSON 解析。
- TBIB 的 dapi 默认返回 XML。对**标签**与**评论**两条路由，`json=1` 也不改变输出。用 `Gelbooru(site_url='https://tbib.org')` 调 `tag_list` / `comment_list` 会拿到 XML 文本，接着抛 `AnybooruAPIError`（解析 JSON 失败）。`post_list` 才是 JSON 数组。

所以本类把 XML 文本原样交给调用者，由调用者自己用 `xml.etree.ElementTree` 解析。它不嗅探 Content-Type、不做 XML 转 JSON、不做失败回退。

原生方法有 4 个：`post_list`、`post_deleted`、`tag_list`、`comment_list`，外加通用入口 `request(page, params=…, response_format=…)`。逐条参数、返回字段与失败证据见[方法参考](gelbooru02-api.md)、[能力入口](gelbooru02-capabilities.md)、[依据与差异](gelbooru02-contract-notes.md)。

## 第一次调用：读一页安全评级的帖子（JSON）

```python
from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    posts = client.post_list(tags='rating:safe', pid=0, limit=2)
    # GET https://tbib.org/index.php?tags=rating%3Asafe&pid=0&limit=2&s=post&q=index&page=dapi&json=1
    # 返回一个数组（没有外层键，也没有总数/页码字段），每项形如：
    # {"directory": 4905, "hash": "…", "height": 2955, "id": 28627153, "image": "…jpg",
    #  "change": 1789760741, "owner": "danbooru", "parent_id": 0, "rating": "safe",
    #  "sample": True, "sample_height": 791, "sample_width": 850, "score": 0,
    #  "tags": "1girl absurdres …", "width": 3176}
    for post in posts:
        print(post['id'], post['rating'], post['width'], post['height'], post['tags'][:40])
    print(client.last_call['status_code'], client.last_call['url'])
```

给什么：`tags='rating:safe'`、`pid=0`、`limit=2`。  
返回什么：JSON 数组。数组项含 `directory`、`hash`、`height`、`id`、`image`、`change`、`owner`、`parent_id`、`rating`、`sample`、`sample_height`、`sample_width`、`score`、`tags`、`width`。没有外层键，也没有总数/页码字段。

`post_list` 默认就是 JSON。JSON 里没有 `file_url` / `sample_url` / `preview_url`，只有 `directory`、`image`、`hash`。本库不会用它们拼媒体地址（见[常见坑](#六个必须记住的差别)）。

## 第二次调用：同一张帖子的 XML 形态

```python
import xml.etree.ElementTree as ElementTree

from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    xml_text = client.post_list(id=28627190, response_format='xml')
    # GET https://tbib.org/index.php?id=28627190&s=post&q=index&page=dapi
    # 本次返回完整 XML 字符串；根 posts 的 count="1"、offset="0"。
    # post 属性含 id="28627190"、rating="s"、width="1200"、height="1600"、
    # file_url="https://tbib.org/images/4905/7693b5d7bdff535e8c47ebcc32338235d24bedf9.jpg"。
    root = ElementTree.fromstring(xml_text)          # 解析是调用者的事，库不做
    print(root.tag, root.attrib['count'], root.attrib['offset'])
    for post in root.findall('post'):
        print(post.get('id'), post.get('rating'), post.get('file_url'))
```

给什么：`id=28627190`、`response_format='xml'`。  
返回什么：完整 XML 字符串。根元素是 `posts`，属性有 `count="1"`、`offset="0"`。`post` 属性含 `id`、`rating`、`width`、`height`、`file_url` 等。

同一个编号在两种格式下的字段不完全一样：XML 有 `file_url` / `sample_url` / `preview_url`、`md5`、`created_at`、`source`、`has_comments` 等，JSON 没有这些。`rating` 也不一样：JSON 是 `safe`，XML 是 `s`。逐项对照见[方法参考](gelbooru02-api.md#json-与-xml-的字段差别)。

## 构造与配置

签名：`Gelbooru02(site_name=None, site_url=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 中的键名 | 不选命名站点，需显式给 `site_url` | `Gelbooru02('tbib')` |
| `site_url` | 字符串，站点根地址，不带 `/index.php` | 读取所选站点的 `url` | `Gelbooru02(site_url='https://tbib.org')` |
| `proxies` | 字典，按 `http` / `https` 指定代理，`{}` 表示直连 | 使用 `request.proxies`，包内为 `{}`；不读环境变量 | `Gelbooru02('tbib', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json`；指定文件不存在直接抛错 | `Gelbooru02('tbib', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout`，包内为 `30` | `Gelbooru02('tbib', timeout=10)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent`，包内为 `Anybooru/0.1.0.dev1` | `Gelbooru02('tbib', user_agent='MyBooruApp/1.0')` |

包内站点条目只有一个字段：

```json
{"tbib": {"url": "https://tbib.org"}}
```

没有 `api_key` / `user_id` / 用户名密码。本类不读凭据、不发 `Authorization`、不做登录，也没有账号相关方法。复制完整配置的方法见[配置指南](configuration.md)。用完记得 `client.close()`，或用 `with` 语句块。

## 通用入口 `request()`

签名：`request(page, *, params=None, response_format='xml')`。

它每次 GET `<site_url>/index.php`。`page` 决定分发页，本类只用 `'dapi'`。`response_format` 决定怎么处理响应：

| `response_format` | 行为 | 返回 |
| :--- | :--- | :--- |
| `'xml'`（默认） | 原样请求，**不**加 `json=1`，不做任何解析 | `response.text`，内容一字不改，含 XML 声明、根元素、属性和空白 |
| `'json'` | 自动加 `json=1`，走共享的 JSON 通路 | 解析后的 Python 对象；正文不是合法 JSON 时抛 `AnybooruAPIError` |
| 其它值 | 客户端没有这个分支 | `KeyError`，不静默降级成 XML 或 JSON |

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `page` | 必填字符串，分发页；本类只用 `'dapi'` | Python 报缺参 | `client.request('dapi', params={'s': 'post', 'q': 'index', 'limit': 1, 'tags': 'rating:safe'})` |
| `params` | 字典，原样发送的查询参数；`None` 值不发送，布尔写成小写 | 只留 `page`，以及 JSON 模式的 `json=1` | 同上 |

```python
from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    xml_text = client.request('dapi', params={'s': 'post', 'q': 'index', 'id': 28627153})
    # GET https://tbib.org/index.php?s=post&q=index&id=28627153&page=dapi
    # 返回 XML 文本；调用者自己解析
    print(xml_text[:120])
    print(client.last_call['status_code'], client.last_call['API'], client.last_call['url'])
```

`last_call` 记录最近一次请求：`API`（这里是 `page` 的值，即 `'dapi'`）、`url`（含查询串）、`status_code`、`status`、`headers`。

非 2xx 一律抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`、`data`。它在解析之前就抛出，不会把错误正文当数据返回。网络错误保持 requests 的原异常。详见 [errors.md](errors.md)。

## 六个必须记住的差别

1. **XML 是默认，不是异常。** `tag_list`、`comment_list`、`post_deleted` 在成功时返回原文字符串；只有 `post_list` 默认给 JSON，还能用 `response_format='xml'` 换回来。删除流本次返回 HTTP 错误。
2. **`json=1` 在标签与评论上无效。** 同一地址加不加 `json=1`，返回体完全一样，都是 `text/xml`。本库不替它们“再试一次 JSON”，也不因为看到 XML 就改写结果。
3. **JSON 没有媒体地址。** JSON 帖子只有 `directory` / `image` / `hash`；`file_url`、`sample_url`、`preview_url` 只出现在 XML 里。本库不拼 `images/{directory}/{image}` 这类地址，也不猜 CDN 规则。
4. **同一个字段在两种格式下叫法/取值不同。** XML 的 `rating="s"`、`md5`、`created_at`、`source`、`has_comments` 在 JSON 里分别对应 `rating="safe"`、`hash`，其余没有。`parent_id` 在 XML 里是空字符串，在 JSON 里是整数 `0`。要跨格式用，先自己归一化。
5. **删除流要看清楚是哪条路由：**
   - 帮助页写的 `s=post&q=index&deleted=show`，即 `post_deleted`，在 TBIB 上对 `last_id=0` 返回 **HTTP 500**。正文是一段没写完的 `<?xml version="1.0" encoding="UTF-8"?><posts>`。本库保留这个错误，抛 `AnybooruHTTPError`，不重试、不修补。
   - `s=deleted&q=index` 是另一条没有帮助页依据的地址，实测返回 `200` 但正文为空。它不是可用的删除流，本库不封装。
6. **`limit` 的“硬上限 100”没有兑现。** 帮助页原文写 “There is a hard limit of 100 posts per request.”，但实测 `limit=101` 真的返回了 101 条。客户端不钳位。

## 可运行示例

两个脚本都只读、匿名，参数取自配置的 `examples.gelbooru02` 段：`site='tbib'`、`post_query={'tags': 'rating:safe', 'pid': 0, 'limit': 2}`、`tag_query={'limit': 2}`、`comment_post_id=1`、`pause_seconds=1.2`。脚本里没有硬编码站点或查询值。

```bash
python examples/gelbooru02/list_posts.py
python examples/gelbooru02/browse_resources.py
```

- `list_posts.py`：`post_list(**post_query)` 读 JSON 帖子，再用同一个编号读 XML。打印方法、状态码、真实 URL、Content-Type 摘要与两侧的关键字段，不打印整段大响应。
- `browse_resources.py`：`tag_list(limit=2)` 读标签 XML，`comment_list(1)` 读评论 XML。只打印状态码、URL 与解析出来的少量字段。

两个脚本都不使用凭据，请求之间按 `pause_seconds` 停顿，不跟随跳转，不重试。已实际运行：冒烟脚本 6 次请求全部 `200`，即 `passed 6 / failed 0`，退出码 `0`；两个示例各 2 次 `200`，退出码 `0`，stderr 为空。逐条命令、URL 与 stdout 摘要见[验证记录](verification.md#gelbooru02tbib匿名只读实测2026-09-19)。

## 边界与未实测

- **只有 4 个原生方法**：`post_list`、`post_deleted`、`tag_list`、`comment_list`，加通用 `request()`。站点的其它 dapi 分发页，如 `s=artist`、`s=pool`、`s=wiki` 等，在 TBIB 上既没有帮助页依据，也没有实测，本库不为它们造方法。
- **`page=autocomplete` / `page=autocomplete2` 没有封装。** 探测时这两个地址返回 `302`、`Location: //tbib.org/`、正文为空；该记录未跟随跳转。共享传输默认跟随跳转，但通过通用 `request()` 调用这两个入口的最终结果未实测。
- **`post_deleted` 没有任何成功样本。** 唯一记录是 `500` 与不完整 XML；`last_id` 的语义、成功返回的字段都没有验证。`s=deleted&q=index` 那个 200 空正文地址不是它的替代品。
- **评论只有空结果样本。** `post_id=1` 返回 `<comments type="array"/>`。非空评论的子元素结构，以及 `post_id` 到底指评论编号还是帖子编号，帮助页文字自相矛盾，都未确认。
- **标签只实测过 `limit=1/2`。** `id`、`name`、`count`、`type`、`ambiguous` 是实测到的属性名，保留为 XML 字符串。标签分类枚举、排序、过滤与分页行为未验证。
- **`limit` 上限没有继续探测。** 实测 `limit=101` 返回 101 条；服务端真实上限未验证。
- **媒体与账号不涉及。** 不下载图片、不拼媒体地址、不读账号接口，`user_list` 属账号面，未调用。也没有登录、写操作、限流与重试逻辑。
- **其它 Gelbooru 0.2 部署未检查。** 本页每条结论都只来自 TBIB 的响应，不要说成“Gelbooru 0.2 都这样”。

继续阅读：[方法参考](gelbooru02-api.md) · [能力入口](gelbooru02-capabilities.md) · [依据与差异](gelbooru02-contract-notes.md) · [错误处理](errors.md)。
