# Gelbooru：我要做什么，用哪个方法？

匿名想把输入前缀变成标签名，用 `autocomplete`；需要帖子、删除流、标签库、用户或评论的官方 JSON，用 dapi 五个方法。下面的 `client` 由 `Gelbooru('gelbooru')` 创建；完整可复制片段见[方法参考](gelbooru-api.md)。

## 按目的找调用

| 我要做什么 | 调用 | 给什么 → 返回什么 |
| :--- | :--- | :--- |
| 把 blue 补成可搜索的标签名 | `client.autocomplete('blue', type='tag', limit=3)` | 输入前缀 → 建议数组，`label` 是展示文字、`value` 是标签名、`post_count` 是字符串计数；本次 200、10 条 |
| 同时按多个标签过滤图片 | `client.post_list(tags='blue_hair solo rating:general', limit=2)` | 站点搜索串 → 完整 JSON；图片数据与候选字段见方法参考，不在客户端映射成统一图片模型 |
| 第二页图片 | `client.post_list(pid=1, limit=2)` | 页码和每页数量 → 该次响应；不自动请求下一页 |
| 已知图片编号，读它的信息 | `client.post_list(id=1)` | 编号 1 → 同一列表路由的 JSON，不是独立的详情路由 |
| 按分数筛选、按更新时间排序 | `client.post_list(tags='score:>=10 sort:updated:desc', limit=2)` | 条件写在 `tags` → 完整响应，排序不是 `order=` 参数 |
| 从某个编号之后继续读删除记录 | `client.post_deleted(last_id=100)` | 删除记录游标 → 完整 JSON，不替调用者提取下个游标 |
| 精确查一个标签 | `client.tag_list(name='blue_eyes')` | 名字 → 该标签的 JSON，候选 `id/name/count/type` 仅为推断 |
| 同时查几个标签 | `client.tag_list(names='schoolgirl moon cat')` | 空格分隔字符串 → 完整 JSON，不能用 Python 列表代替 |
| 模糊查名字，并按数量倒序 | `client.tag_list(name_pattern='blue%', orderby='count', order='DESC', limit=2)` | LIKE 模式、排序 → 完整 JSON；`%` 是任意长通配符 |
| 查用户名前缀 | `client.user_list(name_pattern='lozer%', pid=0, limit=2)` | 名字模式 → 完整 JSON，候选 `id/name` 仅为推断 |
| 请求某图片的评论 | `client.comment_list(1)` | `post_id=1` → 完整 JSON；官方文字对参数含义存在矛盾，见附注 |
| 自己指定 page 和查询参数 | `client.request('autocomplete2', params={'term': 'blue', 'type': 'tag', 'limit': 3})` | JSON 入口与参数 → 原样解析后的 JSON；HTML 不能用此入口读成字符串 |

## 全部方法索引

### 官方 dapi

* `post_list(**params)` → `page=dapi&s=post&q=index&json=1`，搜索、分页或 `id` 查单帖。
* `post_deleted(**params)` → `page=dapi&s=post&q=index&deleted=show&json=1`，按 `last_id` 查删除流。
* `tag_list(**params)` → `page=dapi&s=tag&q=index&json=1`，按编号、名字、多个名字或 LIKE 模式查标签。
* `user_list(**params)` → `page=dapi&s=user&q=index&json=1`，按用户名或模式查用户。
* `comment_list(post_id, **params)` → `page=dapi&s=comment&q=index&json=1`，带指定 `post_id` 查评论。

### 站内 JSON

* `autocomplete(term, **params)` → `page=autocomplete2`，返回输入建议；本次 tag 建议的字段为 `type/label/value/post_count/category`。
* `request(page, *, params=None)` 是上述方法共用的 GET 入口，不拆任何响应外层。

## 网页入口：本库不封装

这些是 **HTML 网页而非官方 JSON API**，用浏览器查看。这里给出实际路由，便于找到 JSON 清单之外的功能；不是让调用者用 `request()` 把 HTML 当 JSON。路由来源为外部综合资料及站点页面链接，本轮实际读取的范围单列在文末。

| 目的 | 网页地址 | 可以查看什么 |
| :--- | :--- | :--- |
| 浏览标签与计数 | [标签列表](https://gelbooru.com/index.php?page=tags&s=list) | 名字、分类、帖子数；过滤例子：`https://gelbooru.com/index.php?page=tags&s=list&tags=blue_*&sort=desc&order_by=index_count` |
| 查某标签会自动带上哪些标签 | [标签蕴含](https://gelbooru.com/index.php?page=tags&s=implications) | 蕴含关系两端，例如前置标签与它蕴含的标签；可用 `tags=crossover_*` 过滤 |
| 查旧标签名与正式名字 | [标签别名](https://gelbooru.com/index.php?page=alias&s=list) | 别名关系，不等于 `s=tag` 的 dapi 返回字段 |
| 浏览图片搜索结果 | [帖子列表](https://gelbooru.com/index.php?page=post&s=list&tags=blue_sky) | 图片网页列表；网页分页 `pid` 不在客户端解释 |
| 已知编号查看图片详情 | [编号 1 的帖子](https://gelbooru.com/index.php?page=post&s=view&id=1) | 图片、上传信息、尺寸、评级、来源和分类标签，不是 JSON 字段表 |
| 找标签说明或帮助条目 | [wiki 搜索 howto](https://gelbooru.com/index.php?page=wiki&s=list&search=howto) | 条目名与可点开的编号 |
| 阅读官方 API 文档 | [howto:api](https://gelbooru.com/index.php?page=wiki&s=view&id=18780) | dapi 资源、参数和认证格式；未提供 JSON 字段表 |
| 阅读旧 API 帮助 | [旧 dapi 帮助](https://gelbooru.com/index.php?page=help&topic=dapi) | 删除流等路由；页首明确标注过时，不以它覆盖新 wiki |
| 浏览池、画师或评论 | [池](https://gelbooru.com/index.php?page=pool&s=list) · [画师](https://gelbooru.com/index.php?page=artist&s=list) · [评论](https://gelbooru.com/index.php?page=comment&s=list) | HTML 列表；不是已确认的 `s=pool/artist` dapi |
| 浏览讨论或来源追踪 | [论坛](https://gelbooru.com/index.php?page=forum&s=list) · [追踪列表](https://gelbooru.com/index.php?page=tracker&s=list) | 站内网页，不属于本客户端方法清单 |

## 边界与未实测

* `post_list`、`post_deleted`、`tag_list`、`user_list`、`comment_list` **逐个均未执行 / 未实测（需账号）**。参数来自官方页面；返回 JSON 的键名、类型和外层结构均未证实，方法参考明确区分确认的数据、候选字段 [推断] 和无依据项。
* 本次唯一匿名原生方法调用是 `autocomplete('blue', type='tag', limit=3)`，200 且 10 项。其它 `type` 在前端脚本中出现，不等于服务端成功路径已跑过。
* 网页表中本轮读取的是标签列表、标签蕴含、官方 wiki、旧 help，均为 200 HTML；没有重跑其余网页、写表单、登录或账号选项。
* 不提供 XML、HTML 解析、CDN 地址推导、写接口或自动翻页；不为 `artist/pool/wiki` 编造 dapi 方法。不用其它站的响应替代 gelbooru.com 证据。

[客户端用法](gelbooru.md) · [参数和返回值](gelbooru-api.md) · [出处与差异](gelbooru-contract-notes.md) · [真实执行记录](verification.md#gelbooru匿名只读实测2026-09-18)
