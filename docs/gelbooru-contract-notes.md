# Gelbooru：接口依据、取舍与实测差异

本页供核对接口依据，不代替[客户端用法](gelbooru.md)或[方法参考](gelbooru-api.md)。本客户端有五个官方 dapi 读取方法和一个站内 JSON 补全方法；没有 HTML 抓取或写方法。

## 资料来源与等级

以下字母表示**来源类型**，不是把低等级推断包装成高等级保证；线上响应只证明被调用的那组参数。

| 标记 | 可核对的来源 | 证明范围 |
| :--- | :--- | :--- |
| W：官方 wiki | [howto:api，id=18780](https://gelbooru.com/index.php?page=wiki&s=view&id=18780)，本次读取为 200 HTML，页上最后更新 `02/22/22 4:17 PM` | dapi 的四种资源与删除流、参数名称、认证查询格式；**没有响应字段表** |
| H：官方旧 help | [help&topic=dapi](https://gelbooru.com/index.php?page=help&topic=dapi)，本次 200 HTML | post/comment/deleted 路由、旧版 limit 与错误说明；页首自称过时并指向 W |
| J：站点 JavaScript | [autocomplete3.js](https://gelbooru.com/script/autocomplete3.js)，本次 200，响应 Last-Modified 为 `Wed, 03 Mar 2021 23:11:06 GMT` | 浏览器如何请求补全、读取哪些属性、绑定哪些补全种类；不是 dapi 服务端源码 |
| T：外部综合参考 | 本次接入收到的《Gelbooru 接口文档（综合版）》，没有可公开核对的发布链接；其引用入口主要是 W、H、J | 匿名 dapi 401、其它网页、搜索写法等是该资料的既有记录；没有原始响应可供本轮独立确认的部分不升级为 L |
| L：真实响应 | [首批记录](verification.md#gelbooru匿名只读实测2026-09-18)与[有界扩展](verification.md#gelbooru有界匿名扩展实测2026-09-18)，包含命令、URL、状态和关键内容 | 首批 6 次；扩展 35 次：13 个补全、5 个 dapi 匿名401、14 个 HTML 状态、3 个 CDN 初始302；无账号成功响应 |
| [推断]：候选字段 | [方法参考](gelbooru-api.md)各方法返回说明，明确写出可确认的数据与推测的键名 | 为未来比对提供名字；不是字段承诺，不用于解析、拆层、类型转换或模型映射 |

### 为什么没有 PHP 服务端行号

本轮没有找到可证明属于当前 gelbooru.com 的官方 PHP 0.2.x 仓库。[Gelbooru GitHub 账号的公开仓库接口](https://api.github.com/users/gelbooru/repos)当时返回空数组；按 `gelbooru language:PHP`、`gelbooru 0.2` 查找得到的是旧 fork 或消费者客户端，不据此断言源码永久不存在。

例如 [zixaphir/gelbooru-fork](https://github.com/zixaphir/gelbooru-fork) 的 README 明说 “A continuation of Gelbooru 0.1 beta”。它不是已确认的现役 0.2.x 服务端，不能拿它的序列化代码当本站字段契约，因此没有复制它作为上游快照，也没有把旧源码的字段写成已确认字段。

没有去兄弟站获取匿名 dapi 来填空：即使另一个站返回某种数组，也不能证明 gelbooru.com 相同。本轮字段处理选择 **官方参数文档 + 明示候选推断 + 原始 JSON 返回**，而非跨部署猜测后强制拆层。

## 官方参数的逐项依据

W 页面正文按小节定位；HTML 压缩在长行上，下面使用标题和原文片段，比部署后会漂移的 HTML 行号更易核对。

| 页面位置与原文 | 实现选择 |
| :--- | :--- |
| W Authentication：`&api_key=API_KEY_HERE&user_id=USER_ID_HERE`；key 来自 account options，ID 来自 options/profile | `sites.gelbooru` 含两个空字符串；仅 dapi 附加非空配置值，不用用户名、Basic 或 Bearer |
| W Posts List：`/index.php?page=dapi&s=post&q=index`；参数 `limit/pid/tags/cid/id/json` | `post_list(**params)`；`id` 仍走 index，没有另建 show 方法 |
| W Posts List：tags “Any tag combination that works on the web site will work here” | 标签搜索串直接发，不解析或改写元标签；页面另外链接站内 howto:search / howto:cheatsheet |
| W Posts List：cid “This is in Unix time so there are likely others with the same value” | 文档说明同一时间值可对应多帖，不把 cid 当唯一记录 ID |
| W Tag List：`id/limit/after_id/name/names/name_pattern/json/order/orderby`；names “Separated by spaces” | `tag_list` 接受一个字符串形式的 names；不把 Python 列表编码成它 |
| W Tag List：LIKE 的 `_` 为 single character、`%` 为 multi-character；orderby 为 date/count/name | 原样发送通配符字符串，由 requests 做 URL 编码；不替换为网页 `*` |
| W User List：`limit/pid/name/name_pattern/json` | `user_list`，不推定 Danbooru 的 `search[name_matches]` 等结构 |
| W/H Comments List：`post_id The id number of the comment to retrieve.` | 参数名保留 `post_id`；按 T 的解释作为关联帖子编号，但参数含义仍有文字矛盾，见下表 |
| W/H Deleted Images：`deleted=show`；last_id “Will return everything above this number.” | `post_deleted` 固定该开关；不把缺省游标偷偷设为 0，也不自动使用 pid |
| W post/tag/user：`json Set to 1 for JSON formatted response.` | 所有 dapi 请求固定发送 `json=1`；删除流和评论的 JSON 分支仍待账号响应确认 |

## 站点脚本的逐项依据

以下行号对应本次读取的 [autocomplete3.js](https://gelbooru.com/script/autocomplete3.js) 文件。它只有前端逻辑，不提供 dapi 序列化代码。

| 行号 | 内容与边界 |
| :--- | :--- |
| 34 | `TAG_CATEGORIES` 含 `general:0`、`artist:1`、`copyright:3`、`character:4`、`meta:5` 等别写；没有 `metadata:5` 这个完整键名 |
| 42 | `MAX_RESULTS = 10`，只证明前端请求值，不证明服务器默认数量或硬上限 |
| 69–75 | 绑定 `tag/artist/pool/user/wiki_page/favorite_group/saved_search_label`；对应输入控件存在不等于服务端每个 type 都成功 |
| 88–115、136–138 | 提及 `mention` 和 `tag_query` |
| 187–190 | 渲染 `item.label`；把 `item.value` 编码到帖子网页的 tags 参数 |
| 195–213 | 条件读取 `antecedent` 与 `post_count`，不能把这两个键声明为每项必有 |
| 216–230 | 读取 type/category；用户分支读取 level；另保存 name 属性。这里的值不证明 dapi tag/user 字段 |
| 236–241 | `$.getJSON('/index.php?page=autocomplete2', {term: query, type: type, limit: ...})`，没有 `json=1` 或账号参数 |

L 本次 tag 响应实际含 `type/label/value/post_count/category`；`post_count` 为字符串，普通项 `category='tag'`、版权项为 `'copyright'`。没有本轮 `antecedent/name/level` 样本。

## dapi 字段：确认的数据不等于确认的键

| 方法 | 文档或网页能支持的数据判断 | 候选字段 [推断] 与执行状态 |
| :--- | :--- | :--- |
| `post_list` | W 确认可按帖子 id 查询；T 转述网页含 ID、Posted、Uploader、宽高、评级、分数、来源、标签、图片地址。扩展只复核网页 HTTP 状态，没有解析正文 | `id/created_at/owner/width/height/rating/score/source/tags/file_url/sample_url/preview_url` 是候选命名，**成功返回未实测（需账号）** |
| `post_deleted` | W/H 确认删除记录入口与数值 last_id，不确认它是否是原帖子编号 | `id` 仅为候选记录键；是否有时间、原帖编号及其名字未知，**未实测（需账号）** |
| `tag_list` | W 有标签 id、name 查询和 count 排序；L 的标签 HTML 实际有名字、类型、帖子数 | `id/name/count/type` 是候选，不从 HTML 或 J 映射强行推出字段与类型，**未实测（需账号）** |
| `user_list` | W 提到数字账号 ID 与用户名查询，不给列表响应列 | `id/name` 是候选，不承诺 level 等附加列，**未实测（需账号）** |
| `comment_list` | W/H 只给评论路由与 post_id 参数；T 解释为读取某帖评论 | `id/post_id/body/creator` 是候选，连参数含义都有待核对，**未实测（需账号）** |

`json=1` 是否返回 `{"post": [...]}`、`@attributes`、数组或其它结构，均没有本轮依据。客户端对此不作选择；得到什么 JSON 就返回什么 JSON。代码例子打印整份响应，不用候选键做下标访问。

五个 dapi 方法的**匿名拒绝已分别实测为 401、0 字节正文**，异常为 `AnybooruHTTPError`，`data=None`；
`last_call` 保存 `API='dapi'`、真实 URL、`status_code=401`、`status='Unauthorized'` 和响应头。
上表的“未实测”仅指需账号的成功返回字段，不再表示方法从未发过请求。

## 文档、脚本与实际结果的矛盾

| 项目 | 原文 / 既有说法 | 本轮处理 |
| :--- | :--- | :--- |
| dapi 匿名权限 | W：“We will occasionally require authentication”；T：匿名一律 401、空正文 | L 扩展分别调用五个原生 dapi 方法，全部401、空正文；异常与last_call保留响应。账号成功分支仍未执行 |
| post limit | W：“default limit of 100”；H：“hard limit of 100” | 默认值与上限分开描述，不做客户端钳位；实际边界未验证 |
| comment post_id | W/H：“id number of the comment”；参数名却是 post_id，T 写该帖下评论 | 倾向解释为帖子 ID，但明确为 T / 推断；不把文字矛盾当已由线上响应纠正 |
| user limit | W 的 User List 下仍写 “How many posts” | 按章节解释为用户数量，同时记录原文笔误，不借此推导返回字段 |
| autocomplete limit | T 称返回条数上限，J 每次发 10 | L 的 `limit=3` 返回 10 条；否定“这一请求至多三条”，不推断所有 limit 都被忽略或上限一定是 10 |
| 未知 autocomplete type | T 参数说明说未知值返回 `[]`，其记录却说 `type=wiki` 回退标签 | L：taq/wiki 配 blue 均200、10个tag建议；不能维持未知值必为空的说法，客户端没有做回退 |
| TAG_CATEGORIES | T 写完整名称 `metadata:5` | J 实际键是 `meta:5`；不把脚本 key、页面显示类型、JSON 字段名混为一谈 |
| 错误结构 | H：response success of “false”，附 “search down” 或类似消息 | 没规定 JSON 键类型、包装及 HTTP 状态；不预设 `{success:false,message:...}`，不把认证空正文解释成此业务错误 |
| 文档新旧 | H 页首 “This section is out of date”；W 仅显示 2022 更新时间和 locked | 可以说 H 自称过时，不能据更新时间和锁定状态声称 W 自己也标了过时 |
| 搜索词集合 | J 的 METATAGS 有继承自其它站的名称；T 提醒并非都由 Gelbooru 支持 | 不把 J 的全部枚举变成服务端搜索保证，原样发送调用者的字符串 |
| 脚本 type 不等于响应对象种类 | J 绑定九种输入；T 称可做用户、池等补全 | L 的九种请求非空结果全部type=tag；user=lozertuser回character标签，pool=touhou回copyright标签，不能称已拿到用户或池对象 |
| 空输入和空格 | T：无 term / 空格写法返回空数组 | L 对显式空字符串和 hatsune miku 各一次均200、空数组；没有探测省略term或下划线对照 |
| CDN 跳转 | T：三个 img4 地址可返回302、需跟随跳转 | L 三个地址初始响应均302，Location为gelbooru.com/hotlink.php；未跟随，不能把“跟随即可取得图片”当已证实 |

## 客户端取舍与权限分支

1. **站点根地址 + 固定脚本**：配置 url 为 `https://gelbooru.com`；`request(page, params=...)` 拼 `/index.php`。这样与已有家族的站点根配置同构，但不会套用 `.json` REST 路径或版本号。
2. **五个 dapi 方法均保留**：凭据缺失不删除方法、不编造成功数据；这里只完成文档给定路由与参数的封装。不会主动拦下匿名调用，也不会借 HTML 替代它。
3. **JSON 原样交付**：没有 `envelope` 参数，没有 `post/tag/user/comment` 键猜测、字段映射或 CDN 拼接。空成功正文、HTTP 错误及 JSON 解析错误沿用共享传输。
4. **站内补全单独标注**：`autocomplete2` 的依据是站点脚本与匿名响应，不写成官方 dapi 子资源；不附加 dapi 凭据，不补 `json=1`。
5. **HTML 不纳入客户端**：标签含义、别名和蕴含等网页确实存在，地址见[网页入口表](gelbooru-capabilities.md#网页入口本库不封装)。解析这些页面需要另立 HTML 契约；本轮没有把它们包装成返回 JSON 的方法。
6. **认证不等于写能力**：非空 api_key/user_id 各自附加到 dapi URL，空值不发送；类没有 POST、登录或写方法。错误原样抛出，没有重试、限流器、失败后切换端点或代理。

## 边界与未实测

* 首批6次与扩展35次分开记录，完整命令、URL及状态见[验证记录](verification.md#gelbooru有界匿名扩展实测2026-09-18)。扩展14条HTML均200，只读响应头、不解析内容。
* 五个 dapi 方法均实测匿名401、空正文；认证成功、JSON字段与包装、排序分页、非认证错误体、配额和限流仍无本站证据。
* 九种脚本type及两种未知值均已请求，不能把返回的tag建议升级为用户/池/wiki专用对象。别名方向、antecedent/name/level样本、缺省type及其它limit仍未实测。
* 不实现XML、HTML解析、账号登录、写请求或官方未列出的dapi资源；三个CDN地址只验证初始302，未读取媒体或跟随Location，地址规律及其它部署未验证。

[客户端用法](gelbooru.md) · [方法参考](gelbooru-api.md) · [能力入口](gelbooru-capabilities.md)
