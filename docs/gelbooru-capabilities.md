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

| 目的 | 网页地址 | 可以查看什么 | 扩展实测 |
| :--- | :--- | :--- | :--- |
| 浏览标签与计数 | [标签列表](https://gelbooru.com/index.php?page=tags&s=list) | 名字、分类、帖子数；可另传 tags/sort/order_by 过滤排序 | 200 HTML |
| 查标签蕴含关系 | [标签蕴含](https://gelbooru.com/index.php?page=tags&s=implications) | 前置标签与它蕴含的标签；可另传 tags 过滤 | 200 HTML |
| 查旧名与正式名字 | [标签别名](https://gelbooru.com/index.php?page=alias&s=list) | 别名关系，不等于 dapi 标签字段 | 200 HTML |
| 浏览图片搜索结果 | [1girl 帖子列表](https://gelbooru.com/index.php?page=post&s=list&tags=1girl) | 图片网页列表；不在客户端解释网页 pid | 200 HTML |
| 已知编号看详情 | [编号 1 的帖子](https://gelbooru.com/index.php?page=post&s=view&id=1) | 图片、上传信息、尺寸、评级、来源、分类标签，不是 JSON 字段表 | 200 HTML |
| 找帮助或标签说明 | [wiki 搜索 howto](https://gelbooru.com/index.php?page=wiki&s=list&search=howto) | 条目名与编号 | 200 HTML |
| 阅读官方 API 文档 | [howto:api](https://gelbooru.com/index.php?page=wiki&s=view&id=18780) | dapi 参数与认证，没有 JSON 字段表 | 200 HTML |
| 浏览池 | [池列表](https://gelbooru.com/index.php?page=pool&s=list) | HTML 池列表，不代表已确认 s=pool dapi | 200 HTML |
| 浏览画师 | [画师列表](https://gelbooru.com/index.php?page=artist&s=list) | HTML 画师列表，不代表已确认 s=artist dapi | 200 HTML |
| 浏览评论 | [评论列表](https://gelbooru.com/index.php?page=comment&s=list) | 网页评论，不是 dapi 响应 | 200 HTML |
| 浏览讨论 | [论坛](https://gelbooru.com/index.php?page=forum&s=list) | 站内讨论列表 | 200 HTML |
| 浏览来源追踪 | [追踪列表](https://gelbooru.com/index.php?page=tracker&s=list) | 站内追踪页面 | 200 HTML |
| 查看画师统计 | [画师统计](https://gelbooru.com/index.php?page=extras&s=artists) | 站内统计页面 | 200 HTML |
| 阅读旧 API 帮助 | [旧 dapi 帮助](https://gelbooru.com/index.php?page=help&topic=dapi) | 页首自称过时，不以它覆盖新 wiki | 200 HTML |

上表每个地址各 GET 一次，只记录状态与 Content-Type，**200 不等于已审查页面内容或表单功能**。
补充过滤参数、其它页码没有随表遍历；客户端没有解析这些网页。

## 图片 CDN：只验证初始跳转

外部资料给定的原图、缩略图、样例图三个 `img4.gelbooru.com` 地址已各做一次不跟随跳转的 GET，
全部返回 **302**，Location 指向 `gelbooru.com/hotlink.php`。完整三个 URL 与 Location 见[实测 G7](verification.md#g7图片-cdn-初始响应)。
没有跟随到目标、没有读取或保存图片正文；不能把初始302写成已成功下载图片。本库不推导 CDN 地址。

## 边界与未实测

* 五个 dapi 方法已分别实测匿名401、空正文，异常为 `AnybooruHTTPError`；**需账号的成功响应仍未实测**，候选字段仍为推断。
* 九种脚本type、空term、空格写法和taq/wiki两个未知值共13次补全请求均200；非空项全部type=tag，不能称为已证实用户/池/wiki专用补全。每条结果见[扩展记录](verification.md#gelbooru有界匿名扩展实测2026-09-18)。
* HTML 14条只确认HTTP可达；未解析内容、未登录、未执行表单。账号选项和其它HTML条件未跑；CDN只看初始302，目标响应与媒体内容未知。
* 不提供XML、HTML解析、CDN地址推导、写接口或自动翻页；不为artist/pool/wiki编造dapi方法。未使用其它站点替代本站证据。

[客户端用法](gelbooru.md) · [参数和返回值](gelbooru-api.md) · [出处与差异](gelbooru-contract-notes.md) · [真实执行记录](verification.md#gelbooru匿名只读实测2026-09-18)
