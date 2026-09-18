# Zerochan：接口依据与实测差异

本页供维护者核对来源。参数和调用例子见[方法参考](zerochan-api.md)，第一次使用看[客户端用法](zerochan.md)。

## 资料来源

没有可供核对的 Zerochan 引擎源码。本次依据是站点 [API 页面](https://www.zerochan.net/api)的
[2024 年快照](https://web.archive.org/web/2024/https://www.zerochan.net/api)，以及[实际请求记录](verification.md#zerochan匿名只读实测2026-09-18)。
直接访问帮助页曾得到浏览器检查页面，所以这里没有声称拿到了最新版说明。

API 页面解释了 URL、参数、只读限制、User-Agent 和请求频率，但没有给返回字段表、错误正文或默认每页数量。
下面将“页面怎么说”和“实际拿到什么”分开记录。

## API 页面逐项依据

引号内是快照原文片段。

| 页面位置 / 原文 | 对应的具体行为 |
| :--- | :--- |
| “a simple read-only API”；“all requests are done using GET” | 本库只发 GET，不提供上传、编辑、删除、收藏等写操作 |
| “the name of your project and your Zerochan username is required”；“your project may be banned for being anonymous” | User-Agent 应带项目名和自己的 Zerochan 用户名；仅用默认 `Anybooru/0.1.0.dev1` 缺用户名 |
| “60 requests per minute”；“Chronically exceeding this limit may result in a ban” | 每分钟最多 60 次；长期超限可能封禁。客户端不内置限速或重试 |
| “appending the json or xml query string to the 'normal' url” | 在 URL 后加 `json` 或 `xml` 选择格式；本库只实现 JSON，实际加的是 `json=` |
| `/?p=1&json`：“End point for retrieving all entries”；“All of these are optional” | 根地址查询图片列表；`p/l/s/t/d/c` 都是可选参数 |
| `p`：“Page. Use in combination with limit to paginate results.” | 页码，与每页数量 `l` 配合使用；没有写默认页码 |
| `l`：“(1-250) Limit, or entries per page.” | 每页 1–250 张；没有写不传时的数量 |
| `s`：“Sort by either recency ( id ) or popularity ( fav )” | `id` 按新到旧，`fav` 按人气；没有写默认排序 |
| `t`：“0 indicates all time, 1 indicates the last 7000 entries, 2 indicates the last 15000 entries” | 人气排序的窗口为全部时间、最近 7000 张或最近 15000 张；页面另说行为 “might be changed soon”，没有默认窗口 |
| `d`：“(large\|huge\|landscape\|portrait\|square) Picture dimensions” | 五个尺寸分类；页面没有给具体宽高门槛或默认值 |
| `c`：“(red\|blue\|green\|...) Color. Filter entries by certain overall color.” | 按整体颜色筛选；词表未列全，没有写默认颜色 |
| `/Genshin+Impact?json`：“filtered by one single tag”；“not available for meta tags” | 按一个标签找图片；meta 标签不适用于这个接口 |
| `/Genshin+Impact?json&strict`：“entries where the primary tag is the tag being matched”；“not available for meta tags” | strict 要求主标签就是输入的单个标签；meta 标签同样不可用 |
| `/Lumine,Flower?json`：“Filter by multiple tags.” | 多个标签放进同一段路径，用逗号分隔 |
| `/3793685?json`：“Detailed information about a single entry.” | 给图片编号，返回这张图的信息 |

## 返回 JSON 的依据

来源：[验证记录 Z2](verification.md#z2逐端点与可选参数)保存了各次实际 URL、HTTP 状态和响应片段。

| 实际请求 | 实际返回什么 | 客户端怎么交给调用者 |
| :--- | :--- | :--- |
| 根列表、单标签、多标签、strict | `{"items": [...]}`；顶层只看到 `items` | `entry_list` 返回 `items` 里的图片列表；`request` 默认返回整个字典 |
| `/3793685?json=` | 一张图片的 JSON 字典，没有外层 `items` | `entry_show` 返回这张图的信息，字段不改名 |
| `/3793685`，没有 `json` | HTTP 200，但内容是 HTML 图片网页 | 不拿网页内容冒充 API 响应 |

列表每张图的字段是 `id, width, height, md5, thumbnail, source, tag, tags`：
编号、宽高、缩略图地址、来源、主标签和标签数组；`md5` 是服务器附带的字符串。
详情字段是 `id, small, medium, large, full, width, height, size, hash, source, primary, tags`：
四种尺寸图片地址、宽高、文件大小、来源、主标签和标签数组；附带字符串键叫 `hash`，不是 `md5`。
客户端不把这两个键互换，也不把详情的 `primary` 改成列表的 `tag`。

## 页面与实际响应的差别

| 项目 | 页面说明 | 实际观察与处理 |
| :--- | :--- | :--- |
| JSON 的写法 | 例子用裸 `json`、`strict` | `json` 和 `json=` 都返回过 JSON；Python `strict=True` 发成 `strict=`，有 HTTP 200 记录，不是 `strict=true` |
| 默认每页数量 | 只规定 `l` 为 1–250，没有默认值 | 不传 `l` 的 `/?json=` 返回过 **48 张图**；这是当次观察，不写成固定保证 |
| 页数与总数 | 没有说明返回总数或页码 | 已观察到列表只有 `items`，没有 `total`、`page` 或下一页链接 |
| 全部时间人气排行 | `t=0` 表示 all time | `/?l=2&s=fav&t=0&json=` 返回 **500**；正文是 `{\r\n  "items": [\r\n}\r\n`，数组没闭合，不是合法 JSON |
| square 尺寸 | 只给分类名称 | 返回过 `1006×966` 和 `1024×1024`，不能按名称推断宽高严格相等 |
| large / huge | 没有阈值说明 | 本批两种条件的前两张相同，不能据此推导分类门槛 |

HTTP 500 先变成 `AnybooruHTTPError`，原始正文保留在 `body`；正文无法解析成 JSON，`data` 为 `None`。
库没有重试、换参数或把错误变成空列表。

## 边界与未实测

* **页面声明不适用**：单标签和 strict 的 meta 标签过滤；具体拒绝状态和正文未实测。
* **本库不实现**：XML、写操作、账号登录、HTML 抓取、自动翻页与自动限速。XML 在 API 页面里出现过，不等于站点不支持。
* **页面没给接口**：标签目录、画师、评论、wiki、合集和按 md5/hash 反查；本库没有替它们编造方法，不宣称站点内部不存在这些功能。
* **仍未实测**：`t=0` 成功返回图片、合规用户名 UA、特殊字符标签的服务端匹配、strict 多标签组合、其它颜色及参数组合、
  空结果、分页边界、缺失图片、限流/封禁响应、其它部署。详情 `size` 的单位也未独立确认。
* 带项目名的匿名请求曾成功，但不能推翻页面要求用户名的规定；封禁条件和限流错误状态没有页面说明。
* 实际执行次数、返回值和新旧批次分别保留在[验证记录](verification.md)，不把页面说明当作已经运行过的证据。

[客户端用法](zerochan.md) · [方法参考](zerochan-api.md) · [能力入口](zerochan-capabilities.md)
