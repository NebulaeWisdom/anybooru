# Zerochan 能力入口：我想做什么，该用哪个接口？

**不知道有哪些接口，先看这页。** 2 个方法的参数、路由与返回见[方法参考](zerochan-api.md)，
页面原文、字段出处、排除项与逐条状态见[契约审计附注](zerochan-contract-notes.md)，
实际调用记录见 [verification.md](verification.md#zerochan匿名只读实测2026-09-18)。

* **Zerochan 是第五个家族**：公开契约的路径和响应与现有四家族不同；没有可供核对的引擎源码，
  只依据 API 页面与真实响应。官方使用 **entries**（不是 posts），因此方法名为 `entry_list` / `entry_show`。
* **本库封 2 个原生方法 + 1 个通用入口**：`entry_list`（列表 / 单标签 / 多标签 / strict）、
  `entry_show`（单条目详情），以及只发 `GET` 的 `request()`。
* **不实现认证**：不发送凭据，也没有凭据配置项；User-Agent 是页面要求的身份标识，
  页面要求它带项目名与使用者自己的 Zerochan 用户名，默认值不满足要求（见[客户端用法](zerochan.md)）。
* **API 是只读的**：页面第一句就是 read-only、所有请求都是 GET；本库不提供写方法，也不发写请求。
* **能匿名读不等于全部可见**：Zerochan 自己的内容范围、meta 标签限制与封禁策略由站点决定，
  本库不预判、不绕过、不抓 HTML 页面当 API。
* **库负责 API 调用，不是下载器**：不自动翻页、不自动保存图片、不自动重试、不做引擎识别。

## 按目的找入口

下表只定位方法与参数所在配置，完整签名、参数值与返回形态见[方法参考](zerochan-api.md)。
`example` 指配置的 `examples.zerochan`，`verified` 指 `verification.zerochan`；初始化见[客户端用法](zerochan.md)。

| 我想做什么 | 方法与配置入口 |
| :--- | :--- |
| 按新到旧浏览条目 | `entry_list(**example['entry_query'])` |
| 按一个标签找图 | `entry_list(**example['tag_query'])` |
| 按多个标签找图 | `entry_list(**example['multi_tag_query'])` |
| 只匹配 primary 标签 | `entry_list(**example['strict_query'])` |
| 翻页 | `entry_list`，更改 `p` / `l`；配置示例见 `verified['optional_queries']` 的 `page` 项 |
| 按人气排序 | `entry_list`，配置 `s` / `t`；`t=0` 本次返回 500，成功路径未实测 |
| 按尺寸或整体颜色过滤 | `entry_list`，配置 `d` / `c` |
| 看一条详情与图片 URL | `entry_show(example['entry_id'])` |
| 拿未拆信封的原始 JSON | `request('/', params=example['entry_query'])` |

标签以原始名称传入，多个名字用列表或元组；不要借用其它家族的搜索表达式。
客户端只负责 URL 编码，特殊字符名字的服务端匹配尚未实测。
列表没有观察到分页元数据，库不推断下一页；JSON 由查询标记选择，不是 `.json` 后缀。
页面没有提供按 `md5` / `hash` 反查的接口，本库也没有相应方法。

## 完整原生方法索引

以下是 `anybooru/api_zerochan.py` 的**全部 2 个原生只读方法**与通用入口，每项只解释“干什么”；
签名、参数表与返回字段见[方法参考](zerochan-api.md)。

### 条目

* `entry_list` — 列条目：不给 `tags` 时列出全部条目，给字符串时按单标签过滤，给列表/元组时按多标签过滤，
  `strict=True` 时只保留 primary 标签匹配的条目；`p` / `l` / `s` / `t` / `d` / `c` 原样透传。
* `entry_show` — 按条目 id 读详情，返回该条目对象本身（无信封）。

### 通用入口

* `request` — 发一次 `GET` 到任意相对路径并返回原始 JSON；`json=` 由客户端补，
  只有显式给 `envelope` 才拆键（列表用 `items`）。它是上面两个方法的底座，也是未被封成方法的路径的出口。

## 本库不提供的能力

* **原生写动作**：API 页面明确写着 read-only，所有请求都是 `GET`；因此没有上传、编辑、删除、收藏、
  投票、评论这类方法，`request()` 也没有 `method` / `data` / `files` 参数，不给写请求留入口。
* **登录、cookie 会话与 API key**：API 页面没有描述登录步骤，本库也没有凭据参数；
  需要账号身份的站内动作不在本库范围。
* **`xml` 输出**：页面提到可以追加 `json` 或 `xml` 查询串，本客户端**只做 JSON**；
  需要 XML 请自行用通用 HTTP 客户端取，库不会因为换个参数就切格式。
* **meta 标签过滤**：页面在单标签与 strict 两条端点上写明不可用，这是服务端限制；
  库不绕过、也不替调用者把 meta 标签转成别的查询。
* **分页元数据与自动翻页**：已观察到的列表响应没有 `total` / `page` 这类字段；
  库不合成它们，也不自动续页。
* **列表之外的资源端点**：页面只记录了上面那 5 条路径（全部条目、单标签、strict、多标签、详情）。
  标签目录、画师、评论、wiki、合集这类端点页面没有提供，本库不为它们造方法，也不拿站点 HTML 页面当 API。
* **HTML 页面抓取与引擎识别**：已有不带 `json` 的详情地址返回 HTML 的记录；
  库不解析 HTML，也不根据站点特征自动选择客户端。

## 边界与未实测

* 已有记录合计 **21 次请求：20×200 + 1×500**——契约复核 16 次（15×200，`s=fav&t=0` 为 `500`），
  两个示例脚本 5 次（5×200，退出码 `0`、stderr 为空）。只覆盖根列表、示例列表、单标签、多标签、
  strict、详情、`p=2`、`t=1` / `t=2`、`d` 五个值与 `c=red`；命令、URL、状态码与条数见
  [verification.md](verification.md#zerochan匿名只读实测2026-09-18)，本页不预先宣称覆盖范围。
* **未实测**：`t=0` 的成功路径、非法或极端参数、末页、空结果、特殊字符标签、strict 多标签组合、
  其它颜色与过滤组合、超限流响应、其它错误路径，以及加入自己用户名后的合规 UA。
* **服务端声明不可用**的是单标签与 strict 的 meta 标签过滤；**API 不提供写能力**；
  **本库未实现** XML、登录与 HTML 抓取；**页面未描述**的资源不等于站点不存在。
  这些类别与“未实测”分开列出，见[附注的排除项](zerochan-contract-notes.md)。
* User-Agent 要求与匿名风险是站点策略，不是库能验证或规避的行为；默认 UA 不合规这一点逐条写在
  [客户端用法](zerochan.md)。

继续阅读：[方法参考](zerochan-api.md) · [客户端用法](zerochan.md) ·
[契约审计附注](zerochan-contract-notes.md) · [配置](configuration.md)。
