# Gelbooru02 方法参考

本类提供 4 个原生方法与通用入口 `request(page, *, params=None, response_format='xml')`。所有请求都是 `GET <site_url>/index.php`，参数位于顶层查询串；没有认证参数、请求体或文件。

证据标记：

| 标记 | 来源 | 证明范围 |
| :--- | :--- | :--- |
| **H** | TBIB 自带帮助页 `https://tbib.org/index.php?page=help&topic=dapi`（HTTP 200） | 删除流与评论的路由、以及 `limit` / `pid` / `tags` / `cid` / `id` / `last_id` / `post_id` 的文字说明 |
| **L** | 本轮对 `tbib.org` 的真实响应 | 状态码、Content-Type、正文形状与字段名 |

## 通用入口 `request()`

签名：`request(page, *, params=None, response_format='xml')`

给什么：`page` 字符串，`params` 字典或 `None`，`response_format` 字符串。返回：XML 原文或解析后的 Python 对象。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `page` | 必填字符串，`index.php?page=` 的分发页；本类只使用 `'dapi'` | Python 报缺参 | `client.request('dapi', params={'s': 'post', 'q': 'index', 'limit': 1, 'tags': 'rating:safe'})` |
| `params` | 字典，原样作为查询参数；`None` 值不发送，布尔写成小写 `true`/`false` | 只留 `page`（JSON 模式再加 `json=1`） | 同上 |
| `response_format` | `'xml'`（默认）或 `'json'` | 默认 `'xml'` | `client.request('dapi', params={'s': 'tag', 'q': 'index', 'limit': 1}, response_format='json')` |

| `response_format` | 实际行为 | 返回 |
| :--- | :--- | :--- |
| `'xml'` | 原样请求，不加 `json=1`，不嗅探 Content-Type、不解析、不去空白 | `response.text`：XML 声明、根元素、属性、空白全部保留 |
| `'json'` | 自动加 `json=1`，用共享 JSON 通路解析 | 解析后的 Python 对象；正文不是合法 JSON 时抛 `AnybooruAPIError` |
| 其它字符串 | 没有这个分支 | `KeyError`（不会退化成 XML 或 JSON） |

```python
from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    posts_json = client.request('dapi', params={'s': 'post', 'q': 'index', 'limit': 1,
                                                'tags': 'rating:safe'}, response_format='json')
    # GET https://tbib.org/index.php?s=post&q=index&limit=1&tags=rating%3Asafe&page=dapi&json=1
    # -> [{"directory": 4905, "hash": "…", "height": 2955, "id": 28627153, …}]
    posts_xml = client.request('dapi', params={'s': 'post', 'q': 'index', 'limit': 1,
                                               'tags': 'rating:safe'})
    # GET https://tbib.org/index.php?s=post&q=index&limit=1&tags=rating%3Asafe&page=dapi
    # -> "<?xml version=\"1.0\" encoding=\"UTF-8\"?><posts count=\"7928673\" offset=\"0\">…"（字符串）
    print(type(posts_json).__name__, type(posts_xml).__name__, len(posts_json), posts_xml[:60])
```

非 2xx 在返回前抛 `AnybooruHTTPError`（带 `http_code`、`url`、`body`、`data`）；`response_format='xml'` 也不会把 `500` 页面当作文本返回。`last_call['API']` 是 `page` 的值。

## post_list

签名：`post_list(*, response_format='json', **params)`

路由：`page=dapi&s=post&q=index`，`response_format='json'` 时加 `json=1`。没有单独的 `post_show`：按编号取一张帖用 `id=<帖子编号>` 走同一入口。

| 参数 | 取值、含义（H） | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `limit` | 请求条数；H 写 “There is a hard limit of 100 posts per request.”，但 L 里 `limit=101` 返回了 101 条 | 站点默认值未验证；客户端不补 | `client.post_list(tags='rating:safe', limit=2)` |
| `pid` | 页码 | 未验证；客户端不补 0 | `client.post_list(tags='rating:safe', pid=1, limit=2)` |
| `tags` | 站点搜索串，H 说网页能用的标签组合与元标签都能用 | 未验证；客户端不补排序或过滤 | `client.post_list(tags='rating:safe', limit=2)` |
| `cid` | change ID（Unix 时间值），同一时间被改的帖子可能有相同值 | 未请求过 | `client.post_list(tags='rating:safe', cid=1789760741, limit=2)` |
| `id` | 帖子编号 | 不按单个编号筛选 | `client.post_list(id=28627153)` |
| `response_format` | `'json'`（默认）或 `'xml'` | 默认 JSON | `client.post_list(id=28627153, response_format='xml')` |

**JSON 返回**：一个数组，没有外层键（没有 `posts`、`count`、页码），每项 15 个键：

| 键 | 观测到的类型 | 含义 |
| :--- | :--- | :--- |
| `id` | int | 帖子编号 |
| `directory` | int | 站点内部目录号 |
| `image` | str | 存储文件名（不是 URL） |
| `hash` | str | 文件哈希 |
| `width` / `height` | int | 原图宽高 |
| `change` | int | change ID（Unix 时间值） |
| `owner` | str | 返回的 owner 名称，样本为 `danbooru`；对应账号未验证 |
| `parent_id` | int | 父帖编号字段；所取 JSON 样本为 `0` |
| `rating` | str | 观测值为 `"safe"` |
| `sample` | bool | 是否有样例图 |
| `sample_width` / `sample_height` | int | 样例图尺寸 |
| `score` | int | 分数 |
| `tags` | str | 空格分隔的标签串 |

```python
from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    posts = client.post_list(tags='rating:safe', pid=0, limit=2)
    # GET https://tbib.org/index.php?tags=rating%3Asafe&pid=0&limit=2&s=post&q=index&page=dapi&json=1
    # -> [{"directory": …, "hash": …, "height": …, "id": …, "image": …, "change": …,
    #      "owner": …, "parent_id": …, "rating": "safe", "sample": true, "score": …, "tags": …, "width": …}, …]
    first_page_ids = [post['id'] for post in posts]
    second_page = client.post_list(tags='rating:safe', pid=1, limit=2)
    # GET https://tbib.org/index.php?tags=rating%3Asafe&pid=1&limit=2&s=post&q=index&page=dapi&json=1
    # 这是 JSON 翻页用法；本轮 limit=2 的第二页实测走的是 XML，offset="2"（见边界与未实测）。
    print(first_page_ids, [post['id'] for post in second_page])
```

**XML 返回**：整段文本。根元素 `<posts count="…" offset="…">`，每条帖子是 `<post …/>`，属性直接写在元素上且全部是字符串。实测属性名：

`height`、`score`、`file_url`、`parent_id`、`sample_url`、`sample_width`、`sample_height`、
`preview_url`、`rating`、`tags`、`id`、`width`、`change`、`md5`、`creator_id`、`has_children`、
`created_at`、`status`、`source`、`has_notes`、`has_comments`、`preview_width`、`preview_height`。

```python
import xml.etree.ElementTree as ElementTree

from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    xml_text = client.post_list(tags='rating:safe', limit=1, response_format='xml')
    # GET https://tbib.org/index.php?tags=rating%3Asafe&limit=1&s=post&q=index&page=dapi
    # <?xml version="1.0" encoding="UTF-8"?><posts count="7928673" offset="0"><post height="2955"
    #   score="" file_url="https://tbib.org/images/4905/….jpg" sample_url="…" preview_url="…"
    #   rating="s" tags=" 1girl … " id="28627153" width="3176" md5="…" created_at="Fri Sep 18 … 2026"
    #   status="active" source="https://x.com/…" has_comments="false" …/></posts>
    root = ElementTree.fromstring(xml_text)
    print(root.tag, root.attrib['count'], root.attrib['offset'])
    for post in root.findall('post'):
        print(post.get('id'), post.get('rating'), post.get('file_url'), post.get('md5'))
```

注意：XML 的 `tags` 值带首尾空格；`score`、`parent_id` 这类没有值的属性是空字符串。客户端不修剪、不转类型。

实测根元素行为：按 `id` 查单帖时 `count="1"`、`offset="0"`（`count` 是本次匹配数）；`pid=1&limit=2` 时 `offset="2"`，返回的两个帖子编号与第一页不同。

## post_deleted

签名：`post_deleted(**params)`

路由：`page=dapi&s=post&q=index&deleted=show`（H 的 “Deleted Images” 一节：`last_id` 是 “A numerical value. Will return everything above this number.”）。返回 XML 文本。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `last_id` | 整数，H 说返回所有大于该编号的记录 | 未验证；客户端不补 0 | `client.post_deleted(last_id=0, limit=1)` |
| `limit` | 整数；H 的删除流一节没有列它 | 未验证删除流是否读它 | 同上 |

本轮没有成功样本：`last_id=0&limit=1`（加不加 `json=1` 都一样）返回 **HTTP 500**、Content-Type `text/xml`，正文是没写完的一段：

```text
<?xml version="1.0" encoding="UTF-8"?><posts>
```

```python
from anybooru import AnybooruHTTPError, Gelbooru02

with Gelbooru02('tbib') as client:
    try:
        deleted_xml = client.post_deleted(last_id=0, limit=1)
        # GET https://tbib.org/index.php?last_id=0&limit=1&s=post&q=index&deleted=show&page=dapi
        print(deleted_xml)
    except AnybooruHTTPError as error:
        print(error.http_code, repr(error.body))   # 500 '<?xml version="1.0" encoding="UTF-8"?><posts>\n'
        print(client.last_call['url'])
```

客户端保留这个错误：不重试、不降级成另一条路由、不把残缺 XML 补成合法结构。

## tag_list

签名：`tag_list(**params)`

路由：`page=dapi&s=tag&q=index`。返回 XML 文本；`json=1` 无效（加不加都一样是 `text/xml`）。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `limit` | 整数，实测 `limit=1` 返回 1 个标签 | 默认值与上限未验证；客户端不补 | `client.tag_list(limit=2)` |

```python
import xml.etree.ElementTree as ElementTree

from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    xml_text = client.tag_list(limit=1)
    # GET https://tbib.org/index.php?limit=1&s=tag&q=index&page=dapi
    # <?xml version="1.0" encoding="UTF-8"?><tags type="array"><tag type="0" count="2"
    #   name="aphinity" ambiguous="false" id="3145728"/></tags>
    root = ElementTree.fromstring(xml_text)
    for tag in root.findall('tag'):
        print(tag.get('id'), tag.get('name'), tag.get('count'), tag.get('type'), tag.get('ambiguous'))
```

实测子元素属性：`id`、`name`、`count`、`type`、`ambiguous`，全部是字符串（`count="2"`、`ambiguous="false"`、`id="3145728"`）。根元素带 `type="array"`。

## comment_list

签名：`comment_list(post_id, **params)`

路由：`page=dapi&s=comment&q=index&post_id=<值>`。返回 XML 文本；`json=1` 同样无效。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `post_id` | 必填；H 原文 “The id number of the comment to retrieve.”，但参数名是 `post_id`（含义矛盾，见边界与未实测） | Python 报缺参 | `client.comment_list(1, limit=1)` |
| `limit` | 整数，可传；H 的评论一节没有列它 | 未验证是否生效、默认值未知 | 同上 |

本轮只有空结果：`post_id=1&limit=1` 返回 `200 text/xml`：

```text
<?xml version="1.0" encoding="UTF-8"?><comments type="array"/>
```

```python
import xml.etree.ElementTree as ElementTree

from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    xml_text = client.comment_list(1, limit=1)
    # GET https://tbib.org/index.php?limit=1&post_id=1&s=comment&q=index&page=dapi
    # <?xml version="1.0" encoding="UTF-8"?><comments type="array"/>
    root = ElementTree.fromstring(xml_text)
    print(root.tag, root.attrib, len(list(root)))     # comments {'type': 'array'} 0
```

## JSON 与 XML 的字段差别

同一次查询（`tags=rating:safe`）在两种格式下给出的字段不一致：

| 数据 | JSON（`response_format='json'`，post_list 默认） | XML（`response_format='xml'`） |
| :--- | :--- | :--- |
| 外层 | 裸数组，无总数/偏移 | `<posts count="…" offset="…">` 根元素 |
| 图片地址 | **没有** `file_url` / `sample_url` / `preview_url` | 三个都有 |
| 哈希 | `hash` | `md5` |
| 评级 | `rating: "safe"` | `rating="s"` |
| 父帖 | `parent_id: 0`（整数） | `parent_id=""`（无值时是空字符串） |
| 时间 | 只有 `change`（Unix 时间值） | 另有 `created_at="Fri Sep 18 21:45:40 +0200 2026"` |
| 其它 XML 独有 | — | `creator_id`、`status`、`source`、`has_children`、`has_notes`、`has_comments`、`preview_width`、`preview_height` |
| 相邻/统计字段 | 没有 | 没有（两边都没有上一张/下一张编号） |
| 类型 | 数值与布尔是真类型 | 全部是字符串（`"false"`、`"2"`、空串） |

本库不做转换：不把 `s` 补成 `safe`、不把 `hash` 改名成 `md5`、不拼媒体 URL、不把空字符串转成 `None`。要跨格式使用，调用者自己归一化。

## 出错时保留状态码与正文

```python
from anybooru import AnybooruHTTPError, Gelbooru02

with Gelbooru02('tbib') as client:
    try:
        posts_xml = client.post_list(tags='rating:safe', limit=1, response_format='xml')
        print(posts_xml[:60])
    except AnybooruHTTPError as error:
        print(error.http_code, error.url, repr(error.body))
```

* 非 2xx → `AnybooruHTTPError`，`body` 是原文（`500` 的删除流就是那半段 XML）。
* 2xx 但 JSON 模式解析失败 → `AnybooruAPIError`（例如对标签/评论误用 JSON 模式）。
* 网络错误 → requests 的原异常，不包装、不重试。

## 边界与未实测

- 没有服务端源码快照，也没有 0.2.x 的具体补丁版本信息（首页页脚只写 `Running Gelbooru 0.2`）。
- gelbooru.com 自己的 wiki 与旧 help 不是本页依据：那些参数（如标签的 `name_pattern`、`orderby`）在 TBIB 上未经验证，不作为本家族依据。逐条原文、差异与排除项见[依据与差异](gelbooru02-contract-notes.md)。
- post_list XML 翻页：`pid=1&limit=2` 时 `offset="2"`，返回编号与第一页不同；观测上 `offset` 等于 `pid × limit`，但只有一个样本，本站数据在动，不要当成稳定公式。
- post_list JSON 本轮还逐字段核对过另一个样本：`id=28627190`、`rating="safe"`、1200×1600（见依据与差异的 L 小节）。
- tag_list 的过滤、排序、分页参数：帮助页没有标签分节，也没有写这些参数；本库不承诺 `name`、`names`、`name_pattern`、`orderby`、`order`、`after_id` 在 TBIB 上可用。
- comment_list 的子元素结构：本轮只有空结果，没有非空评论样本，本库不编造评论字段名，也不拿帮助页那句矛盾描述（“comment id” vs 参数名 `post_id`）当作已澄清的事实。

[客户端用法](gelbooru02.md) · [能力入口](gelbooru02-capabilities.md) ·
[依据与差异](gelbooru02-contract-notes.md) · [验证记录](verification.md#gelbooru02tbib匿名只读实测2026-09-19)
