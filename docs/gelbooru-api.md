# Gelbooru 方法参考

六个原生方法都发 GET：五个官方 dapi 读取方法，加一个站内 JSON 补全方法。通用 `request(page, *, params=None)` 的完整参数见[客户端用法](gelbooru.md#通用-request按-page-选择-json-入口)。

依据标记：**W（官方 wiki）**、**H（官方旧 help）**、**J（站点 JavaScript）**、**T（外部综合资料）**、**L（本轮真实响应）**、**[推断]（没有响应或序列化源码证明的候选字段）**。出处见[契约附注](gelbooru-contract-notes.md#资料来源与等级)。

dapi 例子假定 `my-anybooru.json` 已从包内模板复制，并填入账号自己的 `api_key` / `user_id`。所有 dapi URL 只展示路由和查询，实际有凭据时末尾追加 `&api_key=<你的API_KEY>&user_id=<你的数字账号ID>`。它们不是成功响应示例；逐方法状态见各返回说明及文末[边界与未实测](#边界与未实测)。

## autocomplete：把输入片段变成可搜索的名字

签名：`autocomplete(term, **params)`。

给前缀 `blue`，返回建议数组。`label` 用于展示，`value` 可作为搜索标签，`post_count` 是站点给出的**字符串**计数，`category` 可区分普通标签与版权名等。

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `term` | 必填字符串，输入片段；多词标签通常用下划线 | Python 报缺参；允许显式传 `''`，服务器行为见边界 | `client.autocomplete('blue', type='tag', limit=3)` |
| `type` | 字符串；J 中有 `tag`、`tag_query`、`artist`、`pool`、`user`、`wiki_page`、`favorite_group`、`saved_search_label`、`mention` | T 记为 `tag`，J 没规定服务器默认值；客户端不补 | `client.autocomplete('blue', type='tag', limit=3)` |
| `limit` | 整数，请求希望返回的条数；J 固定传 10，没有给范围 | T 记为 10，J 只证明前端发 10；客户端不补 | `client.autocomplete('blue', type='tag', limit=3)` |

扩展实测把上面九个 `type` 各请求一次，**所有非空结果的 `type` 都是 `'tag'`**。例如 `client.autocomplete('lozertuser', type='user', limit=3)` 返回的是 `category='character'` 的标签，不是带 `name/level` 的用户对象；`type='artist', term='fuzichoco'` 返回三项，包含 artist、character 和普通 tag 分类。`pool/favorite_group/saved_search_label` 配 `touhou` 得到标签建议；`wiki_page` 配 `howto` 也不是 wiki 条目。所以 `type` 表列的是脚本传参名，**不承诺服务端按它筛选资源种类**。每项 URL、数量和首项见[扩展实测 G4](verification.md#g4补全种类与空值边界)。

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru') as client:
    suggestions = client.autocomplete('blue', type='tag', limit=3)
    # GET https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2
    for suggestion in suggestions:
        print(suggestion['value'], suggestion['post_count'], suggestion['category'])
    print(client.last_call['status_code'], client.last_call['url'])
```

**返回依据 L + J**：本次 HTTP 200，返回 10 项。首项如下，不把请求里的 3 当成实际条数：

```json
{"type":"tag","label":"blue eyes","value":"blue_eyes","post_count":"2817483","category":"tag"}
```

| 字段 | 含义与依据 |
| :--- | :--- |
| `type` | 本次全部为 `'tag'`；J 按它选择展示方式 |
| `label` / `value` | 本次 `blue eyes` / `blue_eyes`，分别用于展示与插入查询 |
| `post_count` | 本次为 `'2817483'` 等数字字符串；库不转整数 |
| `category` | 本次普通项为 `'tag'`，`blue_archive` 项为 `'copyright'`；不是 dapi 标签类型的整数 |
| `antecedent` | J 将它作为额外的别名文字显示并替换下划线；本次没有此字段，方向含义不由渲染代码保证 |
| `name` / `level` | J 使用的附加属性 / 用户等级；本次 tag 结果没有这两个字段 |

## post_list：组合搜索、翻页或按图片编号查询

签名：`post_list(**params)`；路由 `page=dapi&s=post&q=index&json=1`。

给标签串、页码与每页数量，查询图片；给 `id=1`，走同一个接口选编号为 1 的帖子，没有单独的 `post_show` 路由。

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `limit` | 整数，每页图片数；W 称默认 100，H 称硬上限 100 | W：100；客户端不补 | `client.post_list(limit=2)` |
| `pid` | 整数页码；T 从 0 开始，W 只写 page number | T：0；W 未规定，客户端不补 | `client.post_list(pid=1, limit=2)` |
| `tags` | 空格分隔的站点搜索串；普通标签取交集，`-标签` 排除；站点支持的元标签也放这里 | T：最新帖子；W 未规定默认排序 | `client.post_list(tags='blue_hair solo rating:general', limit=2)` |
| `cid` | 整数，change ID 的 Unix 时间值，按修改筛选；多个帖子可能同值 | W 未规定；客户端不发此过滤项 | `client.post_list(cid=1704067200, limit=2)` |
| `id` | 整数，帖子编号，来自网页 `page=post&s=view&id=1` 的 `id` | 不按单个编号筛选 | `client.post_list(id=1)` |

**返回依据：参数 W；字段为候选 [推断]，未实测（需账号）。** W 确认可按 `id` 查询，但没有任何响应字段表。T 的帖子网页记录有 ID、Posted、Uploader、宽高、Rating、Score、Source、标签和图片地址这些**数据**；把它们写成 JSON 键 `id`、`created_at`、`owner`、`width`、`height`、`rating`、`score`、`source`、`tags`、`file_url`、`sample_url`、`preview_url` 则全是候选命名，不是官方承诺。即使数据存在，键名、类型及嵌套也可能不同。

方法返回完整解析后的 JSON；例子打印整个响应，**不**以猜测的 `post` / `@attributes` 键取值。

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru', config_file='my-anybooru.json') as client:
    first_page_response = client.post_list(tags='blue_hair solo rating:general', pid=0, limit=2)
    # GET https://gelbooru.com/index.php?tags=blue_hair+solo+rating%3Ageneral&pid=0&limit=2&s=post&q=index&page=dapi&json=1
    print(first_page_response)

    second_page_response = client.post_list(tags='blue_hair solo rating:general', pid=1, limit=2)
    # 同路由，pid=1；客户端不自动请求下一页。
    print(second_page_response)

    post_response = client.post_list(id=1)
    # GET https://gelbooru.com/index.php?id=1&s=post&q=index&page=dapi&json=1
    print(post_response)
```

搜索和排序写在 `tags` 中，而非 `order=`；T 转述的写法包括 `score:>=10`、`width:>=1000`、`source:ab*`、`sort:updated:desc`、`sort:random`。不要照搬 Danbooru 的 `order:` 或 Zerochan 的 `s='fav'`。例如：

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru', config_file='my-anybooru.json') as client:
    sorted_posts_response = client.post_list(tags='rating:general score:>=10 sort:updated:desc', limit=2)
    # GET https://gelbooru.com/index.php?tags=rating%3Ageneral+score%3A%3E%3D10+sort%3Aupdated%3Adesc&limit=2&s=post&q=index&page=dapi&json=1
    print(sorted_posts_response)
```

## post_deleted：从记录编号之后读删除流

签名：`post_deleted(**params)`；路由 `page=dapi&s=post&q=index&deleted=show&json=1`。这里的游标是 `last_id`，不是帖子分页的 `pid`。

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `last_id` | 整数；W/H 说返回大于该编号的记录，不能由此确认它等于原帖子编号 | W/H 未规定；客户端不补 0 | `client.post_deleted(last_id=0)` |
| `limit` | 整数；T 示例出现过，但 W/H 的删除流章节没有列出它 | 未规定是否生效、默认值与上限；客户端不补 | `client.post_deleted(last_id=0, limit=2)` |

**返回依据：路由和游标 W/H；字段为候选 [推断]，未实测（需账号）。** 页面只确认存在删除记录和数值游标，没有列返回键。候选 `id` 表示记录编号；是否另有原帖子编号或删除时间无法确认，不把 `deleted_at` 等键当保证。客户端保留完整 JSON，也不会自动提取下一次 `last_id`。

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru', config_file='my-anybooru.json') as client:
    deleted_posts_response = client.post_deleted(last_id=0)
    # GET https://gelbooru.com/index.php?last_id=0&s=post&q=index&deleted=show&page=dapi&json=1
    print(deleted_posts_response)
```

## tag_list：精确标签、多个标签、通配符和排序

签名：`tag_list(**params)`；路由 `page=dapi&s=tag&q=index&json=1`。给 `name` 查一个名字，给 `names` 一次查多个，给 `name_pattern` 按字符模式筛选。

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `id` | 整数，标签在库中的编号 | 不按此编号筛选 | `client.tag_list(id=1)` |
| `limit` | 整数，返回标签数；W 未给取值上限 | W：100；客户端不补 | `client.tag_list(limit=2)` |
| `after_id` | 整数，只查标签编号大于此值的记录 | 不附加此条件；起点 W 未规定 | `client.tag_list(after_id=100, limit=2)` |
| `name` | 字符串，按标签名查 | 不附加此条件 | `client.tag_list(name='blue_eyes')` |
| `names` | 一个空格分隔的字符串，查多个指定标签；不是数组 | 不附加此条件 | `client.tag_list(names='schoolgirl moon cat')` |
| `name_pattern` | LIKE 模式；`_` 代表一个任意字符，`%` 代表任意长字符串，不是站点网页的 `*` | 不附加此条件 | `client.tag_list(name_pattern='%choolgirl%')` |
| `orderby` | `date` / `count` / `name`，按时间 / 数量 / 名称排序 | W 未规定；客户端不补 | `client.tag_list(name_pattern='blue%', orderby='count', order='DESC', limit=2)` |
| `order` | `ASC` / `DESC`，升序 / 降序 | W 未规定；客户端不补 | `client.tag_list(orderby='name', order='ASC', limit=2)` |

**返回依据：参数 W；字段为候选 [推断]，未实测（需账号）。** W 确认标签具有可查询的数据库编号和名字、支持按数量排序；本轮 HTML 标签页确有类型、计数和名字。候选 JSON 键为 `id`、`name`、`count`、`type`，但该网页不是 dapi，不能证明这四个键实际存在。J 的类别映射 `general=0`、`artist=1`、`copyright=3`、`character=4`、`meta=5` 也不能证明 dapi 一定使用整数 `type`。返回值是完整 JSON，不转成以标签名为键的字典。

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru', config_file='my-anybooru.json') as client:
    tags_response = client.tag_list(name_pattern='blue%', orderby='count', order='DESC', limit=2)
    # GET https://gelbooru.com/index.php?name_pattern=blue%25&orderby=count&order=DESC&limit=2&s=tag&q=index&page=dapi&json=1
    print(tags_response)
```

## user_list：按用户名或模式查账号

签名：`user_list(**params)`；路由 `page=dapi&s=user&q=index&json=1`。

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `limit` | 整数，返回用户数；W 文本误称 posts，位于 User List 章节 | W：100；客户端不补 | `client.user_list(limit=2)` |
| `pid` | 整数页码，T 从 0 开始 | T：0；W 未规定 | `client.user_list(pid=0, limit=2)` |
| `name` | 字符串，要查的用户名 | 不按此名字筛选 | `client.user_list(name='lozertuser')` |
| `name_pattern` | 字符串，用户名通配查询；T 例子用 `%`，W 未给通配符细则 | 不附加此条件 | `client.user_list(name_pattern='lozer%', limit=2)` |

**返回依据：参数 W；字段为候选 [推断]，未实测（需账号）。** W 确认站点账号有数字 user ID 和可检索用户名，但未说明此列表是否返回它们；候选 `id`、`name` 分别表示账号编号和用户名。不能从 autocomplete 的 `level` 推出本接口也有等级字段。返回完整 JSON，不拆 `user` 键。

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru', config_file='my-anybooru.json') as client:
    users_response = client.user_list(name_pattern='lozer%', pid=0, limit=2)
    # GET https://gelbooru.com/index.php?name_pattern=lozer%25&pid=0&limit=2&s=user&q=index&page=dapi&json=1
    print(users_response)
```

## comment_list：按 post_id 请求评论

签名：`comment_list(post_id, **params)`；路由 `page=dapi&s=comment&q=index&json=1`。

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `post_id` | 必填整数；T 解释为帖子编号，用于该帖评论；W/H 却写 comment id，详见边界与附注 | Python 报缺参；不把缺参猜成全站最新评论 | `client.comment_list(1)` |
| `**params` | 其它显式查询参数；W/H 没列评论的 `limit`、`pid` 或排序参数 | 不发额外参数；不沿用 post/user 的默认值 | `client.comment_list(1)` |

**返回依据：路由与参数名 W/H，参数含义 T / [推断]；字段为候选 [推断]，未实测（需账号）。** 官方只列评论读取入口与 `post_id`，没列响应数据；候选 `id`（评论编号）、`post_id`（关联帖子）、`body`（评论正文）、`creator`（作者）都是推断，不能当成实际键或完整字段表。库返回整个 JSON，不按候选键读取。

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru', config_file='my-anybooru.json') as client:
    comments_response = client.comment_list(1)
    # GET https://gelbooru.com/index.php?post_id=1&s=comment&q=index&page=dapi&json=1
    print(comments_response)
```

## 出错时保留状态码与正文

下面调用的匿名拒绝路径已实测：`post_list(limit=1)` 返回 401、空正文，抛 `AnybooruHTTPError`；其余四个 dapi 方法也各取得同样结果。捕获后查看实际结果，不把错误改成空列表。需要账号的成功响应仍未实测。

```python
from anybooru import AnybooruHTTPError, Gelbooru

with Gelbooru('gelbooru', api_key='', user_id='') as client:
    try:
        posts_response = client.post_list(limit=1)
        print(posts_response)
    except AnybooruHTTPError as error:
        print(error.http_code, error.url, repr(error.body))
        print(client.last_call['status_code'])
```

## 边界与未实测

| 方法 | 本轮执行边界 |
| :--- | :--- |
| `autocomplete` | 九个脚本 type、空 term、空格写法、taq/wiki 两个未知值均已跑；13 次都是 200，非空项全部为 type=tag |
| `post_list` | 匿名已实测 401、空正文；需账号的成功返回未实测，含列表、详情、过滤排序和分页 |
| `post_deleted` | 匿名已实测 401、空正文；成功返回未实测，记录编号含义、last_id 缺省及 limit 支持未确认 |
| `tag_list` | 匿名已实测 401、空正文；成功返回字段未实测，HTML 和 J 不能代替字段证明 |
| `user_list` | 匿名已实测 401、空正文；成功返回未实测，用户名模式细则与分页未确认 |
| `comment_list` | 匿名已实测 401、空正文；成功返回未实测，post_id 含义矛盾和非空正文尚待核对 |

* 五个 dapi 方法均只负责拼出文档给出的查询参数。**没有任何经本站响应验证的 dapi JSON 字段表**；上面的候选键仅供未来对照，不参与客户端解析。不保证数组、资源名外层键、`@attributes`、总数或下一页字段。
* W 仅在 post/tag/user 章节明确写 `json=1`；客户端也对删除流、评论发送它，这是统一 JSON 请求的选择，不证明这两条分支已经返回过 JSON。
* `type='taq'` 和 `'wiki'` 配 `term='blue'` 实测都返回 10 个标签建议，不是 T 声称的未知值空数组；显式空 term 和 `'hatsune miku'` 则实测为 `[]`。这不证明任意未知 type 的行为，也没有证明专用用户/池/wiki 补全或别名字段；缺省 type 与其它 limit 未实测。
* W 的默认 100 与 H 的硬上限 100 不同；客户端不钳位。错误里的 `success` 和消息来自 H 的文字说明，JSON 编码形式未实测。
* `s=artist/pool/wiki` 没出现在官方 dapi 清单，本库无原生方法；HTML 的标签、别名、wiki、池、画师等入口见[能力页](gelbooru-capabilities.md#网页入口本库不封装)。

[客户端用法](gelbooru.md) · [能力入口](gelbooru-capabilities.md) · [逐条依据与矛盾](gelbooru-contract-notes.md) · [实测记录](verification.md#gelbooru匿名只读实测2026-09-18)
