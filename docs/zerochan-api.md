# Zerochan 方法参考

`entry_list` 按筛选条件返回图片列表；`entry_show` 根据图片编号返回这张图的尺寸、图片地址、来源和标签。
下面每个 Python 代码块都能独立运行；构造器默认读包内配置，User-Agent 要求与覆盖配置见[客户端用法](zerochan.md)。

## entry_list：列表、过滤与分页

签名：`entry_list(tags=None, strict=False, **params)`。

你给出页码、每页张数、标签或其它筛选条件，方法返回符合条件的**图片列表**。
服务器返回 `{"items": [...]}`，你拿到的是其中那个数组。每张图包含图片编号 `id`、宽 `width`、高 `height`、
缩略图地址 `thumbnail`、来源链接 `source`、主标签名 `tag`、全部标签 `tags`，另有字符串字段 `md5`。

### 参数逐项说明

下表的调用都假定已有 `client = Zerochan('zerochan')`；完整可运行代码紧接在表后。

| 参数 | 类型与取值 | 不传时怎样 | 字面调用示例 |
| :--- | :--- | :--- | :--- |
| `tags` | `str`：一个标签；`list` / `tuple`：多个标签 | 客户端默认 `None`，请求根列表 | `client.entry_list(tags='Genshin Impact', l=2)` |
| `strict` | `bool`；`True` 要求图片的主标签就是输入的单个标签 | 客户端默认 `False`，不发送这个开关 | `client.entry_list(tags='Genshin Impact', strict=True, l=2)` |
| `p` | `int`，页码；与 `l` 配合翻页 | 页面未规定默认页码；客户端不补 | `client.entry_list(p=2, l=2, s='id')` |
| `l` | `int`，每页 **1–250** 条 | 页面未规定默认条数；曾观察到 48 条，客户端不补 | `client.entry_list(p=1, l=2, s='id')` |
| `s` | `str`：`'id'` 按新到旧，`'fav'` 按人气 | 页面未规定默认排序；客户端不补 | `client.entry_list(p=1, l=2, s='id')` |
| `t` | `int`：`0` 全部时间，`1` 最近 7000 条，`2` 最近 15000 条；用于人气排序 | 页面未规定默认窗口；客户端不补 | `client.entry_list(l=2, s='fav', t=1)` |
| `d` | `str`：`'large'`、`'huge'`、`'landscape'`、`'portrait'`、`'square'` | 页面未规定默认尺寸条件；客户端不补 | `client.entry_list(l=2, d='square')` |
| `c` | `str`，整体颜色名，如 `'red'`、`'blue'`、`'green'`；页面没有给完整词表 | 页面未规定默认颜色条件；客户端不补 | `client.entry_list(l=2, c='red')` |

### 列表、分页与按新到旧排序

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    first_page_entries = client.entry_list(p=1, l=2, s='id')
    # GET https://www.zerochan.net/?p=1&l=2&s=id&json=
    # 返回列表；每项有 id、tag、width、height 等字段。
    print([entry['id'] for entry in first_page_entries])

    second_page_entries = client.entry_list(p=2, l=2, s='id')
    # GET https://www.zerochan.net/?p=2&l=2&s=id&json=
    # 返回第二页图片列表，仍有 id、tag 等字段；响应不提供图片总数或当前页码。
    print([entry['id'] for entry in second_page_entries])
```

### 按标签过滤

**单标签**：传原始标签名，空格由客户端编码为 `+`。

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    tagged_entries = client.entry_list(tags='Genshin Impact', l=2)
    # GET https://www.zerochan.net/Genshin+Impact?l=2&json=
    # 返回图片列表；tag 是每张图的主标签，不必等于 Genshin Impact。
    print([(entry['id'], entry['tag']) for entry in tagged_entries])
```

**多标签**：传列表，而不是把多个名字塞进一个字符串。

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    matching_entries = client.entry_list(tags=['Lumine', 'Flower'], l=2)
    # GET https://www.zerochan.net/Lumine,Flower?l=2&json=
    # 返回图片列表；样本 tags 同时包含 Lumine、Flower，主标签仍可能是其它名称。
    print([(entry['id'], entry['tag'], entry['tags']) for entry in matching_entries])
```

**strict**：单标签查询上的开关，意思是“只保留主标签就是这个标签的图片”。
Python 写 `strict=True`，实际 URL 是 **`strict=`（等号后没有值）**，不是 `strict=true`。
单标签与 strict 端点均不适用于 **meta 标签**。

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    primary_tag_entries = client.entry_list(tags='Genshin Impact', strict=True, l=2)
    # GET https://www.zerochan.net/Genshin+Impact?l=2&strict=&json=
    # 返回列表；这次每条的 tag 都是 Genshin Impact。
    print([(entry['id'], entry['tag']) for entry in primary_tag_entries])
```

### 按人气排序与时间窗口

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    recent_popular_entries = client.entry_list(l=2, s='fav', t=1)
    # GET https://www.zerochan.net/?l=2&s=fav&t=1&json=
    # 返回图片列表；页面规定在最近 7000 张图中按人气排序，每张图有 id、tag、tags。
    print([(entry['id'], entry['tag']) for entry in recent_popular_entries])

    wider_popular_entries = client.entry_list(l=2, s='fav', t=2)
    # GET https://www.zerochan.net/?l=2&s=fav&t=2&json=
    # 返回相同结构的列表；页面将此窗口定义为最近 15000 条。
    print([(entry['id'], entry['tag']) for entry in wider_popular_entries])
```

### 尺寸过滤

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    square_entries = client.entry_list(l=2, d='square')
    # GET https://www.zerochan.net/?l=2&d=square&json=
    # 返回列表；width、height 是实际尺寸，square 不保证两者严格相等。
    print([(entry['id'], entry['width'], entry['height']) for entry in square_entries])
```

### 颜色过滤

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    red_entries = client.entry_list(l=2, c='red')
    # GET https://www.zerochan.net/?l=2&c=red&json=
    # 返回列表；含 id、tag、thumbnail 等字段，没有额外的颜色分类字段。
    print([(entry['id'], entry['tag'], entry['thumbnail']) for entry in red_entries])
```

## entry_show：根据图片编号查询图片信息

给一张图的编号（常叫 **pid**，例如 `3793685`），返回这张图的四种尺寸图片地址、宽高、文件大小、
来源链接、主标签名和全部标签。这个编号能在列表项的 `id` 字段中找到，也是图片网页地址末尾的数字：
`https://www.zerochan.net/3793685` 的图片编号就是 `3793685`。

方法实际参数名是 `entry_id`：`entry_show(entry_id)`，必填整数，没有默认值。

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    entry = client.entry_show(3793685)
    # GET https://www.zerochan.net/3793685?json=
    # 返回这张图的信息，没有再套一层；primary=Yukihana Lamy，width=2976，height=4055。
    print(entry['id'], entry['primary'], entry['width'], entry['height'])
    print(entry['full'])  # https://static.zerochan.net/Yukihana.Lamy.full.3793685.jpg
```

| 返回字段 | 你能拿来做什么 |
| :--- | :--- |
| `id` | 这张图的编号 |
| `small` / `medium` / `large` / `full` | 四种尺寸的图片地址；例如 `entry['full']` 是完整尺寸图片地址 |
| `width` / `height` | 图片宽度和高度 |
| `size` | 文件大小的数值，客户端不换算单位 |
| `source` | 来源链接，例如原始 Pixiv 作品地址 |
| `primary` | 图片的主标签名，示例中为 `Yukihana Lamy` |
| `tags` | 这张图的全部标签名组成的列表 |
| `hash` | 服务器给出的字符串字段；列表里的对应字段名称是 `md5`，不要混用键名 |

## request：查看服务器返回的整个 JSON

`request` 接受相对路径和查询参数，始终发送 GET。请求列表时，它返回 `{"items": [...]}` 整个字典；
`entry_list` 则只返回里面的图片数组。完整例子见[客户端用法](zerochan.md#通用-request保留外层-items)。
客户端自动把 `json=` 放进 URL，不会在路径后面加 `.json`。

## 出错时查看状态码与正文

下面请求全部时间的人气排行；已知这组参数返回 HTTP 500。可以捕获 `AnybooruHTTPError`，
打印实际地址与服务器原文，不要把错误当作“没有图片”。

```python
from anybooru import Zerochan, AnybooruHTTPError

with Zerochan('zerochan') as client:
    try:
        popular_entries = client.entry_list(l=2, s='fav', t=0)
        # GET https://www.zerochan.net/?l=2&s=fav&t=0&json=
    except AnybooruHTTPError as error:
        print(error.http_code)  # 500
        print(error.url)  # https://www.zerochan.net/?l=2&s=fav&t=0&json=
        print(repr(error.body))  # '{\r\n  "items": [\r\n}\r\n'：不是合法 JSON
```

## 边界与未实测

* `t=0` 虽然在页面中定义为全部时间，实测 `/?l=2&s=fav&t=0&json=` 返回 **500**，
  正文为不完整 JSON；`AnybooruHTTPError` 保留该正文。其成功路径未实测。页面也提示 `t` 的行为可能调整。
* 不传 `l` 观察到 **48 张图**，不是页面承诺；服务器只返回 `{"items": [...]}`，没有图片总数、页码或下一页地址。
* API 页面说明单标签与 strict **不支持 meta 标签**；本库只实现 JSON，不做 XML、写操作或登录。
  `/<id>` 不带 `json` 的详情地址已观察到 HTML，不能当 API 读取。
* 官方限流 **60 请求/分钟**，长期超限可能封禁；客户端没有限速逻辑或自动重试。
* 尺寸分类阈值、颜色算法、详情 `size` 单位没有得到完整确认；square 已有不等宽高样本。
* 合规用户名 UA、特殊字符标签、strict 多标签、其余组合、空结果、分页边界、缺失条目、限流响应和其它部署未实测。

[客户端用法](zerochan.md) · [能力入口](zerochan-capabilities.md) · [出处与差异](zerochan-contract-notes.md) · [实测记录](verification.md)
