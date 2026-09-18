# Gelbooru02：接口依据与差异

本页供核对依据，不代替[客户端用法](gelbooru02.md)或[方法参考](gelbooru02-api.md)。
本类提供基于 TBIB（`https://tbib.org`）帮助页与真实响应的 4 个只读方法与 1 个通用入口，
不包含认证、写操作、媒体下载或 HTML 解析。

## 资料来源与等级

| 标记 | 来源 | 证明范围 |
| :--- | :--- | :--- |
| **H：TBIB 自带帮助页** | `https://tbib.org/index.php?page=help&topic=dapi`（HTTP 200、`text/html`） | 帖子列表、删除流、评论列表三条路由，以及 `limit` / `pid` / `tags` / `cid` / `id` / `last_id` / `post_id` 的文字说明 |
| **L：本轮真实响应** | 对 `tbib.org` 的实际请求（含用现有 `Gelbooru` 客户端访问 TBIB 的记录） | 状态码、Content-Type、正文形状与字段名、失败正文 |

三件必须记住的边界：

1. **没有服务端源码快照**：本轮没有找到可证明属于 TBIB 的 Gelbooru 0.2 源码，因此本页不做任何
   “源码第几行”的断言，一切以帮助页原文与真实响应为准。
2. **版本只能说到 “0.2”**：首页页脚原文是 `Running Gelbooru 0.2`，页面里**没有 generator 元信息**，
   所以不能推断 0.2.x 的具体补丁号，也不能由静态脚本路径推断实现版本
   （`script/application.js.php?1`、`script/awesomplete.min.js?v5` 只说明站点引用了这些脚本，
   `tbib.js` 是横幅/广告脚本，不是引擎版本）。
3. **gelbooru.com 的文档不是 TBIB 的依据**：官方 wiki 与旧 help 描述的是另一套部署；
   它们写过的标签参数（`name`、`names`、`name_pattern`、`orderby`、`order`、`after_id`）
   在 TBIB 上**既没有帮助页依据也没有实测**，本家族不把它们写成依据。

## 帮助页原文（H）

`help&topic=dapi` 只有三节：Posts（List、Deleted Images）与 Comments（List）。
**没有 Tags 分节，也全文没有出现 `json` 这个词**。

| 帮助页原文 | 落点 |
| :--- | :--- |
| `Url for API access: /index.php?page=dapi&s=post&q=index` | `post_list` 的路由 |
| `limit` How many posts you want to retrieve. There is a hard limit of 100 posts per request. | `limit` 参数；硬上限声称 100（L 里未兑现） |
| `pid` The page number. | `pid` 是页码 |
| `tags` The tags to search for. Any tag combination that works on the web site will work here. This includes all the meta-tags. See cheatsheet for more information. | `tags` 直接发站点搜索串 |
| `cid` Change ID of the post. This is in Unix time so there are likely others with the same value if updated at the same time. | `cid` 是 Unix 时间值，同一时间可能多个帖子同值 |
| `id` The post id. | `id` 是帖子编号（同一条路由，没有独立详情页） |
| `Url for API access: /index.php?page=dapi&s=post&q=index&deleted=show` | `post_deleted` 的路由 |
| `last_id` A numerical value. Will return everything above this number. | `last_id` 的语义 |
| `Url for API access: /index.php?page=dapi&s=comment&q=index` | `comment_list` 的路由 |
| `post_id` The id number of the comment to retrieve. | 参数名是帖子、描述说是评论编号：**文档内部矛盾**，L 的空结果无法澄清 |

帮助页没有写：`json`、`s=tag`、`s=deleted`、`page=autocomplete*`、评论的 `limit`、标签的任何过滤/排序。

## 本轮真实响应（L）

| 请求 | 状态 | Content-Type | 正文要点 |
| :--- | :--- | :--- | :--- |
| `GET https://tbib.org/` | 200 | `text/html; charset=UTF-8` | 页脚含 `Running Gelbooru 0.2`；无 generator 元信息 |
| `GET …?page=help` 与 `…?page=help&topic=dapi` | 200 | `text/html; charset=UTF-8` | 帮助页正文（见上节） |
| `GET …?page=post&s=list&tags=rating%3Asafe&pid=0` | 200 | `text/html; charset=UTF-8` | 网页列表可用（本库不解析 HTML） |
| `…?page=dapi&s=post&q=index&limit=1&tags=rating%3Asafe` | 200 | `text/xml;charset=UTF-8` | `<posts count="7928673" offset="0"><post …/></posts>`，`post` 属性含 `file_url`、`sample_url`、`preview_url`、`rating="s"`、`md5`、`created_at`、`source`、`has_comments` 等，全部为字符串 |
| 同一地址加 `&json=1` | 200 | **`text/html; charset=UTF-8`** | 裸 JSON 数组 1 项，15 个键（`directory`、`hash`、`height`、`id`、`image`、`change`、`owner`、`parent_id`、`rating`、`sample`、`sample_height`、`sample_width`、`score`、`tags`、`width`），`rating` 为 `"safe"`，`sample` 为布尔 `true`，**没有媒体地址** |
| `…?page=dapi&s=tag&q=index&limit=1`（加/不加 `json=1`） | 200 | `text/xml;charset=UTF-8` | 两次正文**完全相同**：`<tags type="array"><tag type="0" count="2" name="aphinity" ambiguous="false" id="3145728"/></tags>` |
| `…?page=dapi&s=comment&q=index&post_id=1&limit=1`（加/不加 `json=1`） | 200 | `text/xml;charset=UTF-8` | 两次正文**完全相同**：`<comments type="array"/>`（空集合） |
| `…?page=dapi&s=post&q=index&limit=101&tags=rating:safe&json=1` | 200 | `text/html; charset=UTF-8` | 真的返回 **101 项**，`rating` 全为 `safe` |
| `…?page=dapi&s=post&q=index&limit=1&tags=rating:safe&pid=1&json=1` | 200 | `text/html; charset=UTF-8` | 1 项 `id=28627160`；JSON 没有分页元数据，动态数据的不同编号单独不足以证明页码语义 |
| `…?page=dapi&s=deleted&q=index&limit=1`（加/不加 `json=1`） | 200 | `text/html; charset=UTF-8` | **正文为空** |
| `…?page=dapi&s=post&q=index&deleted=show&last_id=0&limit=1`（加/不加 `json=1`） | **500** | `text/xml;charset=UTF-8` | 正文只有没写完的 `<?xml version="1.0" encoding="UTF-8"?><posts>` |
| `…?page=autocomplete&q=blue&limit=1` 与 `…?page=autocomplete2&term=blue&limit=1` | **302** | `text/html` | `Location: //tbib.org/`，正文为空（探测不跟随跳转） |
| `GET https://tbib.org/tbib.js?v4=` | 200 | `application/javascript` | 横幅/广告脚本，与引擎版本无关 |
| 用现有 `Gelbooru(site_url='https://tbib.org')` 调 `post_list(limit=1, tags='rating:safe')` | 200 | `text/html; charset=UTF-8` | 返回 JSON 数组（该客户端能解析） |
| 同一客户端调 `tag_list(limit=1)` / `comment_list(1, limit=1)` | 200 | `text/xml;charset=UTF-8` | 拿到 XML，客户端按 JSON 解析失败 → `AnybooruAPIError` |

命令与逐条摘要见[验证记录](verification.md#gelbooru02tbib匿名只读实测2026-09-19)。

本轮完整跑通的补充样本（冒烟 6 次 + 示例各 2 次，全部 `200`）：

* `post_list` JSON 与 XML 用同一个编号互相校验通过：JSON 一侧 `id=28627190`、`rating="safe"`、
  `1200×1600`；XML 一侧同编号，根元素 `count="1"`、`offset="0"`，`rating="s"`，
  XML 的 `file_url` 与 `sample_url` 相同，`preview_url` 是另一个缩略图地址；JSON 没有这些 URL 字段。
* `pid=1&limit=2` 的 XML：根 `offset="2"`、`count="7928682"`，两个帖子编号 `28627185` / `28627184`，
  与第一页不重复（分页实证）。
* `tag_list(limit=2)`：两个标签 `aphinity`、`algol_(words_worth)`。
* `comment_list(post_id=1, limit=2)` 及不传 `limit` 的示例：仍是空集合 `<comments type="array"/>`。

## 文档化 vs 实测

| 参数 / 路由 | H 是否文档化 | L 到哪一步 | 本库的处理 |
| :--- | :--- | :--- | :--- |
| `limit` | 是（称硬上限 100） | `limit=1`、`limit=101` 都按数返回 | 原样发送，**不钳位**；上限未继续探测 |
| `pid` | 是 | `pid=0`、`pid=1` 各取到不同帖子 | 原样发送，不设默认页 |
| `tags` | 是 | 只用过 `rating:safe` | 原样发送，不解析、不改写 |
| `cid` | 是 | **未请求** | 原样发送（帮助页有，行为细节未验证） |
| `id` | 是 | 用 `id=28627190` 取得同编号的 JSON 与 XML | 走同一条列表路由，没有 `post_show` |
| `last_id` | 是（删除流） | 只触发过 `500` | 原样发送；**成功路径没有任何样本** |
| `post_id` | 是（描述与参数名矛盾） | `post_id=1` 只得到空集合 | 原样发送；不推断语义，也不推断子元素结构 |
| `json` | **完全没提** | `post` 有效；`tag`/`comment` 无效 | 通过 `response_format='json'` 暴露；XML 模式绝不自动加它 |
| `s=tag` 路由 | **没有 Tags 分节** | 实测可用（`limit=1`） | `tag_list` 的依据是 L，不是 H |
| 标签的其它参数 | 无 | 未请求 | **不承诺**（别站文档里的写法不算 TBIB 的依据） |
| `s=deleted` | 无 | `200` 空正文 | 不封装，也不当成删除流 |
| `deleted=show` | 是 | `500` 半段 XML | `post_deleted` 使用；错误原样抛出 |
| `page=autocomplete*` | 无 | `302`（不跟随） | 不封装 |
| 评论的 `limit` | 无 | 传过 `limit=1/2`，也省略过；均为空 | 原样发送，是否生效未验证 |

## JSON 与 XML 的数据差别（要点）

逐字段对照表见[方法参考](gelbooru02-api.md#json-与-xml-的字段差别)。核对方便，这里只记两条最关键的：

* **媒体地址只在 XML 里**：JSON 没有 `file_url` / `sample_url` / `preview_url`，只有
  `directory` + `image` + `hash`；本库**不拼地址**、不猜目录规则。
* **同名数据不同写法**：JSON `rating: "safe"` ↔ XML `rating="s"`；JSON `hash` ↔ XML `md5`；
  JSON `parent_id: 0` ↔ XML `parent_id=""`；XML 的值全是字符串，JSON 用真类型。

另外，`post_list` 的 **JSON 响应 Content-Type 是 `text/html`**，XML 响应才是 `text/xml`；
本库因此**不做 Content-Type 嗅探**——用哪种格式由调用者的 `response_format` 决定，不由响应头决定。

## 失败与矛盾

| 项目 | 事实 | 处理 |
| :--- | :--- | :--- |
| 删除流 | H 文档写 `deleted=show` + `last_id`；L 里 `last_id=0&limit=1` 返回 `500` 与**未闭合**的 `<posts>` | 客户端抛 `AnybooruHTTPError` 并保留正文；不重试、不换路由、不修补 XML |
| `s=deleted` | 不在 H；L 返回 `200` 但**空正文** | 不封装；文档明确它不是删除流 |
| `limit` 上限 | H 称 hard limit 100；L 的 `limit=101` 返回 101 条 | 不钳位；上限写“未确认”，不扩大探测 |
| `json=1` | H 完全没提；L 对 tag/comment 完全无效 | 不做“JSON 失败了再试 XML”的自动回退；格式由调用者选 |
| `post_id` 含义 | H：参数名 post_id，描述却是 “comment id” | 保留矛盾，不用空结果反推语义 |
| 自动补全 | H 没有；L 的 `autocomplete` / `autocomplete2` 都是 `302` 到站点根 | 不封装；也不声称通过本库调用时会怎样（共享传输不关闭跳转，路径未实测） |
| 首页版本 | 只有页脚 `Running Gelbooru 0.2`，无 generator 元信息 | 只说 0.2；不推断补丁版本与实现 |
| 输出格式 | 同一批数据在 JSON 与 XML 里字段集不同 | 文档逐项列出差异，客户端不做转换 |

## 客户端取舍

1. **独立类、独立接口约定**：`Gelbooru02` 不复用也不改动现有 `Gelbooru`；两者的 JSON 假设不同，
   混用会把 TBIB 的 XML 当 JSON 解析（现有客户端对 `tag_list` / `comment_list` 正是如此失败）。
2. **XML 是默认返回**：`request(..., response_format='xml')` 原样返回 `response.text`，
   不解析、不去空白、不改名；只有显式 JSON 模式才加 `json=1` 并解析。
3. **不嗅探、不回退**：不看 Content-Type 选格式，不因为解析失败换另一种格式，不重试。
4. **错误优先于解析**：非 2xx 在返回前抛 `AnybooruHTTPError`，`body` 保留原文（`500` 的删除流就是例子）。
5. **不造数据**：不拼媒体地址、不把 `s` 补成 `safe`、不把字符串 `"false"` 变布尔、不编造评论字段。
6. **不添加能力**：没有认证属性、没有账号方法、没有写操作、没有自动翻页、没有本地限流；
   构造时给共享传输传空用户名，所以站点条目只需要 `url`。

## 排除项

分类清单与理由见[能力入口的排除表](gelbooru02-capabilities.md#本库不封装的路由)。一句话概括：
`autocomplete` / `autocomplete2`（302）、`s=deleted`（空正文）、未验证的 `s=artist|pool|wiki`、
账号面 `s=user`、网页列表页、媒体文件、其它 Gelbooru 0.2 部署，都不在本库内。

## 未解决与未实测

* **`post_deleted` 没有成功样本**：删除流的正常返回结构、`last_id` 的生效方式、`limit` 是否被读，全部未知。
* **评论没有非空样本**：`<comments type="array"/>` 之外的结构、`post_id` 的真实语义、评论的 `limit`，
  都未验证；本库不编造评论字段。
* **标签只验证到 `limit=1/2` 与两个样本名**（`aphinity`、`algol_(words_worth)`）：其它过滤/排序参数
  在 TBIB 上没有依据；属性保留 XML 字符串，标签分类枚举没有验证。
* **`cid` 未请求**，`limit` 的真实上限未确认（`limit=101` 返回 101 条，未再往上探）；
  `offset` 只观察到“`pid=1&limit=2` 时为 2、按 `id` 查时为 0”这一个样本，换算公式不作保证。
* **媒体与账号未涉及**：不下载图片、不拼媒体地址、不读账号接口、不登录。
* **其它部署未检查**：本页结论只对 TBIB 成立；不要把 TBIB 的 JSON/XML 差异推广到所有 Gelbooru 0.2 站点。

[客户端用法](gelbooru02.md) · [方法参考](gelbooru02-api.md) · [能力入口](gelbooru02-capabilities.md)
