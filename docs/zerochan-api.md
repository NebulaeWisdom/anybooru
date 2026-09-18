# Zerochan 方法参考

`Zerochan` 的 **2 个原生方法**都是 `request()` 的薄封装，对应 API 页面记录的 5 条 `GET` 路径形态
（`entry_list` 覆盖全部条目、单标签、多标签、strict，`entry_show` 覆盖详情）；
Zerochan 的公开 API 目前只读，所以本页没有写方法。构造、User-Agent、参数编码与 `last_call`
见[客户端用法](zerochan.md)，按目的找入口见[能力入口](zerochan-capabilities.md)，
页面原文、观察到的字段、排除项与逐条状态见[契约审计附注](zerochan-contract-notes.md)。

## 共用前置

本页片段都接着这段前置写：`client` 已构造好，`example` 是配置里的样例输入，
`verified` 是复核输入（含 `verification.zerochan.optional_queries` 这份可选参数清单）。
片段里的 `entry_id`、标签与所有查询参数都来自配置，不是库的默认值、也不由库代取；
结束后调用 `client.close()`，也可以把整段放进 `with Zerochan(...) as client:`。

```python
from anybooru import Zerochan

client = Zerochan('zerochan')                              # 读包内默认 anybooru.json
example = client.config['examples']['zerochan']            # 站点、查询、条目 id、调用间隔
verified = client.config['verification']['zerochan']       # 同形状的复核输入与可选参数清单
```

## 全页通用契约

* **只发 `GET`，不实现认证**：`request()` 的签名没有 `method` / `data` / `files`，客户端也不发
  认证头或提供凭据字段。页面要求 User-Agent 带项目名与使用者的
  Zerochan 用户名，默认值不满足，详见[客户端用法](zerochan.md)。
* **JSON 由查询串选择**：客户端每次都给查询串补 `json=`（空值），路径**不自动添加 `.json` 后缀**
  （通用入口也不校验后缀，调用者给什么就发什么）。
  `/3793685` 不带 `json` 时已观察到 HTML；页面的 JSON 例子写的是裸 `json`（`/?p=1&json`），
  已观察到的响应里 `json` 与 `json=` 都能取到 `application/json`。
* **路径即过滤**：`''` 是全部条目，`<Tag>` 是单标签，`<TagA>,<TagB>` 是多标签，
  `<Tag>?…&strict=` 是 strict 模式，`<id>` 是单条目详情。标签名按**字面名称**使用，没有搜索语法。
* **路径段转义**：每个标签名用 `quote_plus(name, safe='')` 整体转义（空格变 `+`，`,` `/` `&` `#` `%` `+`
  等进 `%XX`），多标签各自转义后用字面逗号连接；不拆空格或逗号、不小写化。条目 id 走 `str(entry_id)`，
  不做额外转义（它应当是数字）。
* **参数透传**：`p` / `l` / `s` / `t` / `d` / `c` 原样发送，`None` 省略；**库不设默认值、不钳位、不校验**，
  页面没有写明的默认（例如不传 `l` 时的页大小）由服务端决定；本次观察到不传 `l` 时返回 48 条，
  这属于服务端当时的取值，不是页面承诺的默认值。
* **信封只有两种**：列表端点返回 `{"items": [...]}`，本库拆 `items`；详情端点返回裸对象，不拆。
  `envelope` 找不到键直接 `KeyError`，不做形状猜测。
* **列表没有分页元数据**：已观察到的列表响应里只有 `items`，没有 `total` / `page` / `pages` 之类的字段，
  所以“还有没有下一页”只能由调用者根据本次条数与自己的 `p` / `l` 判断。
* **失败**：非 2xx 抛 `AnybooruHTTPError`（保留状态码、URL、正文与 `data`）；2xx 但正文不是合法 JSON
  抛 `AnybooruAPIError`；网络异常保持 requests 原异常。页面没有描述错误正文形状；已有的一条错误记录是
  `s=fav&t=0` 的 `500`，其正文**不是合法 JSON**，因此 `error.data` 为 `None`、原始正文在 `error.body`，
  库不重试也不改写（见 [verification.md](verification.md#zerochan匿名只读实测2026-09-18) 与
  [错误处理](errors.md)）。
* **限流**：页面写明 60 请求/分钟、长期超限可能封禁；客户端**不节流、不重试、不做退避**。

## 条目（2 个方法）

### `entry_list(tags=None, strict=False, **params)`

读条目列表并返回 `items` 数组。

| 传入参数 | 路由 | 对应页面原文 |
| :--- | :--- | :--- |
| `tags=None` | `/?…&json=` | `/?p=1&json`：End point for retrieving all entries |
| `tags='Genshin Impact'` | `/Genshin+Impact?…&json=` | `/<Tag>?json`：filtered by one single tag |
| `tags=['Lumine', 'Flower']` | `/Lumine,Flower?…&json=` | `/<TagA>,<TagB>?json`：Filter by multiple tags |
| `tags='Genshin Impact', strict=True` | `/Genshin+Impact?…&strict=&json=` | `/<Tag>?json&strict`：strict mode…primary tag |

```python
entries = client.entry_list(**example['entry_query'])          # {"p": 1, "l": 2, "s": "id"}
second_page = client.entry_list(**verified['optional_queries'][0]['params'])   # {"p": 2, "l": 2, "s": "id"}
by_one_tag = client.entry_list(**example['tag_query'])         # {"tags": "Genshin Impact", "l": 2}
by_tags = client.entry_list(**example['multi_tag_query'])      # {"tags": ["Lumine", "Flower"], "l": 2}
strict = client.entry_list(**example['strict_query'])          # {"tags": "Genshin Impact", "strict": True, "l": 2}
```

参数：

* `tags`：`None` 列全部条目；`str` 是**一个**标签；`list` / `tuple` 是多个标签。字符串里带空格或逗号时
  仍是一个标签（逗号会被转义成 `%2C`），多标签必须用序列。
* `strict`：布尔。`True` 时发送 `strict=` 这个**存在标记**（空值），只保留 primary 标签等于所查标签的条目；
  `False` 时不发送该参数。页面把 strict 记在单标签端点上。
* `**params`：页面定义的查询参数原样透传。

| 参数 | 页面取值 | 页面原文要点 |
| :--- | :--- | :--- |
| `p` | 整数 | `Page. Use in combination with limit to paginate results.` |
| `l` | 1–250 | `Limit, or entries per page.`；不传时页大小由服务端决定，页面未写默认值（本次观察到 48 条） |
| `s` | `id` \| `fav` | `Sorting order. Sort by either recency ( id ) or popularity ( fav ).` |
| `t` | `0` \| `1` \| `2` | `0` 全部时间、`1` 最近 7000 条、`2` 最近 15000 条；页面注明 `might be changed soon`。**`s=fav&t=0` 本次返回 `500`**（正文无效 JSON），`t=1` / `t=2` 返回 `200` |
| `d` | `large` \| `huge` \| `landscape` \| `portrait` \| `square` | `Picture dimensions`，按图片尺寸过滤。**`square` 不是精确的正方形**（本次首项 1006×966），`large` / `huge` 的阈值页面未给 |
| `c` | `red` \| `blue` \| `green` \| … | `Color. Filter entries by certain overall color.` |

返回 `items` 数组，每个条目是这些键（**已观察到的响应字段**，页面本身没有描述响应结构）：
`id`（数字）、`width`、`height`、`md5`（字符串）、`thumbnail`（URL）、`source`（URL 字符串）、
`tag`（primary 标签名字符串）、`tags`（标签名字符串数组）。

注意：

* **meta 标签**：页面在单标签与 strict 两条端点上写明
  “This endpoint is not available for meta tags.”；哪些标签算 meta 标签页面没有定义。
* **`l` 与 `p` 是页面建议的组合**，不是客户端强制要求。本批多次只传 `l=2` 而不传 `p` 也成功返回 2 条；
  `p=2&l=2` 返回另一批条目。不传 `l`、只给特定 `p`，以及 `l` 超范围或 `p` 越界时的响应未实测。
* `md5` 是返回字段，不是本库计算的校验和；库不做去重或比对。
* 本次记录的 `entry_list` 调用：示例列表、单标签、多标签、strict、`p=2`、`t=1`、`t=2`、
  `d` 的五个值与 `c=red` 均为 `200`；`s=fav&t=0` 为 `500`。值样例：不传 `l` 的 `/?json=` 返回
  48 条（首项 `id` 4725815、`tag` `Sin Mal`）；`p=1&l=2&s=id` 返回 2 条；单标签、多标签、strict 各返回
  2 条，首项都是 `id` 4034550；该样本的 `tags` 同时有 `Flower` 与 `Lumine`，
  而 `tag`/primary 是 `Genshin Impact`，说明这次多标签查询不要求 primary 等于所查标签
  （strict 才是这个条件）。逐条 URL 与状态码见
  [verification.md](verification.md#zerochan匿名只读实测2026-09-18)。

### `entry_show(entry_id)`

读单个条目的详情，返回裸对象（无信封）。

```python
entry = client.entry_show(example['entry_id'])       # 3793685
print(entry['primary'], entry['width'], entry['height'], entry['size'])
```

参数 `entry_id` 是条目 id（数字）：示例里取自配置 `examples.zerochan.entry_id`，通常来自 `entry_list`
返回的 `id`；它直接拼进路径 `/3793685?json=`。
返回值是条目对象本身，已观察到的字段：`id`、`small`、`medium`、`large`、`full`（四种尺寸的图片 URL）、
`width`、`height`、`size`（数值；**单位没有页面依据，已有记录里也没有确认**）、`hash`（字符串）、
`source`（URL 字符串）、`primary`（primary 标签名字符串）、`tags`（标签名字符串数组）。

注意：

* **`hash` 与列表里的 `md5` 是两条端点各自的返回字段**，这里只报告字段名与观察到的字符串值，
  本库不比较两者。
* 本次记录：`entry_show(3793685)` 返回 `200`，`primary` 是 `Yukihana Lamy`、`width` 2976、
  `height` 4055、`size` 5706752，`full` / `large` / `small` 等是不同尺寸的图片 URL；
  不存在或非法的 id 没有响应记录。

## 方法索引与路由对照

| 方法 | 路由（`GET`） | 返回 |
| :--- | :--- | :--- |
| `entry_list(tags=None, strict=False, **params)` | `/?json=`、`/<Tag>?json=`、`/<Tag>?json=&strict=`、`/<A>,<B>?json=` | `items` 数组（8 键条目） |
| `entry_show(entry_id)` | `/<id>?json=` | 裸详情对象（12 键） |
| `request(path, *, params=None, envelope=None)` | 任意相对路径 + 客户端补的 `json=` | 原始 JSON；显式 `envelope` 才拆键 |

页面写的是“**Most** endpoints can be accessed by appending the `json` or `xml` query string”，
即并非所有地址都保证有 JSON 形式；本库只封上面这 5 条路径，`xml` 不做。

继续阅读：[客户端用法](zerochan.md) · [能力入口](zerochan-capabilities.md) ·
[契约审计附注](zerochan-contract-notes.md) · [错误处理](errors.md)。
