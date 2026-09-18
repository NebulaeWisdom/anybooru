# Zerochan：我要做什么，用哪个方法？

按条件找图片用 `entry_list`；已经知道图片编号、要图片地址和完整信息，用 `entry_show`。
下面的 `client` 是 `Zerochan('zerochan')`。每个调用都直接写出了参数，完整可复制代码见[方法参考](zerochan-api.md)。

## 按目的找调用

| 我要做什么 | 直接调用 | 返回什么 / 实际请求地址 |
| :--- | :--- | :--- |
| 第一页，每页两张，按新到旧 | `client.entry_list(p=1, l=2, s='id')` | 图片列表，含 `id`、`tag`、宽高；`https://www.zerochan.net/?p=1&l=2&s=id&json=` |
| 同样条件翻到第二页 | `client.entry_list(p=2, l=2, s='id')` | 第二页图片列表；`https://www.zerochan.net/?p=2&l=2&s=id&json=` |
| 找 Genshin Impact 标签的图片 | `client.entry_list(tags='Genshin Impact', l=2)` | 图片列表；每张的主标签 `tag` 可能不同；`https://www.zerochan.net/Genshin+Impact?l=2&json=` |
| 同时按 Lumine、Flower 两个标签筛选 | `client.entry_list(tags=['Lumine', 'Flower'], l=2)` | 图片列表，可从 `tags` 查看每张的全部标签；`https://www.zerochan.net/Lumine,Flower?l=2&json=` |
| 只找主标签就是 Genshin Impact 的图片 | `client.entry_list(tags='Genshin Impact', strict=True, l=2)` | 图片列表，每张的 `tag` 是 Genshin Impact；`https://www.zerochan.net/Genshin+Impact?l=2&strict=&json=` |
| 在最近 7000 张图中按人气排序 | `client.entry_list(l=2, s='fav', t=1)` | 图片列表，含 `id`、`tag`；`https://www.zerochan.net/?l=2&s=fav&t=1&json=` |
| 把人气排序窗口扩到最近 15000 张 | `client.entry_list(l=2, s='fav', t=2)` | 相同字段的图片列表；`https://www.zerochan.net/?l=2&s=fav&t=2&json=` |
| 找站点归为 square 的图片 | `client.entry_list(l=2, d='square')` | 图片列表，从 `width`、`height` 看实际宽高；`https://www.zerochan.net/?l=2&d=square&json=` |
| 按整体红色筛选 | `client.entry_list(l=2, c='red')` | 图片列表，含 `id`、`tag`、`thumbnail`；`https://www.zerochan.net/?l=2&c=red&json=` |
| 根据图片编号查地址、尺寸和标签 | `client.entry_show(3793685)` | 图片地址 `small/medium/large/full`、宽高、文件大小、来源、主标签和全部标签；`https://www.zerochan.net/3793685?json=` |
| 看到服务器原样返回的 JSON | `client.request('/', params={'l': 2})` | 整个 `{"items": [...]}` 字典；`https://www.zerochan.net/?l=2&json=` |

`strict=True` 只用于单标签查询：要求图片的**主标签**等于你输入的标签。实际 URL 是 `strict=`，
等号后没有值。多个标签应传列表，不要把它们拼成一个字符串。完整参数取值和不传时的行为见[参数表](zerochan-api.md#参数逐项说明)。

## 全部方法索引

* `entry_list`：给页码、每页数量或标签等条件，返回图片列表；每张含编号 `id`、宽高、缩略图地址、来源、主标签 `tag` 和全部标签 `tags`。
* `entry_show`：给一张图的编号（pid），返回它的四种尺寸图片地址、宽高、文件大小 `size`、来源 `source`、主标签 `primary`、标签数组 `tags` 和 `hash`。
* `request`：给相对地址和 URL 参数，返回服务器整个 JSON；例如保留外面的 `items`，而不是只返回里面的图片列表。

## 边界与未实测

* 单标签与 strict **不支持 meta 标签**，这是 API 页面的规定；未实测具体错误响应。
* `t=0` 的全部时间人气查询已返回 **500**，正文不是合法 JSON；捕获和查看错误的方法见[错误例子](zerochan-api.md#出错时查看状态码与正文)。
* 不传 `l` 曾返回 **48 张图**，页面没有规定这个默认数量；列表只有 `items`，没有图片总数、页码和下一页地址。
* `d=square` 已返回过 `1006×966`，不保证宽高相等；large/huge 的尺寸门槛尚未确认。
* API 页面提到 XML，但本库只做 JSON；不实现写操作、账号登录或 HTML 抓取。图片详情地址不带 `json` 时已返回过 HTML。
* 页面要求 User-Agent 有项目名和自己的 Zerochan 用户名；默认值缺用户名，匿名成功仍有封禁风险。
* 每分钟最多 **60 次请求**，长期超限可能封禁；客户端不替你限速或重试。
* 合规用户名 UA、特殊字符标签、strict 多标签、其余颜色与组合、空结果、分页边界、缺失图片、限流封禁和其它部署未实测。

[客户端用法](zerochan.md) · [方法参考](zerochan-api.md) · [接口依据与实测差异](zerochan-contract-notes.md) · [验证记录](verification.md)
