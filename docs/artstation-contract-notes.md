# ArtStation：契约依据、权限与输入校正

本页供维护者核对证据与接入范围；使用方法见 [客户端用法](artstation.md)，完整参数见
[方法参考](artstation-api.md)，按目的查入口见 [能力入口](artstation-capabilities.md)。
真实 URL、状态码、Content-Type 与脚本结果集中在
[验证记录](verification.md#artstation匿名只读实测2026-09-20)。

## 1. 依据等级与家族判定

| 标记 | 出处 | 本轮取得的证据 |
| :--- | :--- | :--- |
| L：匿名响应 | `https://www.artstation.com` 的根级 JSON、`/api/v2`、RSS 及少量边界路径 | 37 次定点 GET，25×200、9×400、401/403/404 各一次；每次保存完整响应，逐项摘要见验证记录 |
| P：站点公开政策 | [服务条款](https://www.artstation.com/tos)、[robots.txt](https://www.artstation.com/robots.txt) | 都为 200；属于上述 37 次，不另外重复计数 |
| T：候选输入 | 接入时收到的《artstation.com（ArtStation）接口文档（综合版）》 | 提供待核验的路径与字段，不作为本轮已经请求的证据；其中引用的前端 bundle 与第三方项目本轮没有独立读取 |
| L-POST：匿名两步跟进 | POST csrf_protection/token.json 与 POST search/projects.json | 两个原生方法在同一会话完整执行200；初次记录器失败的一条token请求另计，状态未记录，详见验证记录 |

本轮没有取得官方 API 手册、OpenAPI 或服务端源码快照，不编造路由控制器与行号。
`GET /openapi.json` 返回的是 `200 text/html; charset=utf-8`、标题为 `ArtStation - Explore`
的 HTML，而不是 OpenAPI。**这不能证明别处不存在官方规范、GraphQL 或合作接口。**

这是独立家族而非某个 booru 模板的新部署：作品同时有数字 `id` 与短码 `hash_id`，用户以
`username` 进入路径；根级列表、v2 搜索、专辑、频道和 RSS 的参数与响应均有各自结构。
只有 JSON 或 Rails 风格参数相同，不足以复用 Danbooru/Moebooru 类。
客户端统一命名 `ArtStation`，站点键 `artstation`，不制造跨站统一作品模型。

## 2. 原生范围：17 个方法

原生方法为 **15 GET + 2 POST，16个JSON响应 + 1个RSS响应**。新增POST是匿名CSRF准备与form搜索，不修改内容。
下表是直接 HTTP 路由证据，不代表全部 Python 包装方法都运行过；方法真跑范围在验证记录单列。

| 方法 | 路由（主机均为 `www.artstation.com`） | L 的返回与关键区别 |
| :--- | :--- | :--- |
| `project_list(**params)` | `/projects.json` | `{data,total_count}`；作品含 `id/hash_id/title/permalink/cover/assets_count/user/views_count`，没有完整 `assets` |
| `project_random()` | `/random_project.json` | 单个作品对象；样本 `id=3260777,hash_id=OnxxK`，含 `assets/tags/categories/mediums/software_items/comments_count/user`；不是指定作品查询 |
| `user_show(username)` | `/users/{username}.json` | 单个用户对象；`timwarnock` 的 `id=1,projects_count=40`，含 `albums_with_community_projects`、技能和软件资料 |
| `user_quick(username)` | `/users/{username}/quick.json` | 单个用户对象；样本 59 键，含相册摘要、社交链接与 `is_artist/is_beta`；不是全量档案的简单子集 |
| `user_profile(username)` | `/api/v2/user_profiles/{username}.json` | 单个用户对象；样本 63 键，含 `username/headline/projects_count/portfolio/social_profiles` |
| `user_projects(username, **params)` | `/users/{username}/projects.json` | `{data,total_count}`；本轮条目 19 键，**缺少全站列表的 `user/views_count`** |
| `user_following(username, **params)` | `/users/{username}/following.json` | `{data,total_count}`；条目是用户卡片，含 `id/username/full_name/sample_projects/skills/software_items` |
| `project_search(**params)` | `/api/v2/search/projects.json` | `{total_count,data}`；条目用 `url/smaller_square_cover_url/is_adult_content`，不是全站列表的 `permalink/cover/adult_content` |
| `search_filter_fields()` | `/api/v2/search/projects/filter_fields.json` | 裸数组，样本 12 项；每项 `name/type`，部分另有 `select_options` |
| `album_projects(album_id, **params)` | `/api/v2/community/projects/by_album.json` | `{total_count,data}`；条目带 `album_id/album_title/position/assets/description`，无需附加字段参数即可读资产摘要 |
| `channel_list()` | `/api/v2/community/channels/channels.json` | `{total_count,data}`；样本 64 项，`id=70,name=Abstract,uri=abstract` |
| `channel_projects(channel_id, **params)` | `/api/v2/community/channels/projects.json` | `{total_count,data}`；条目有 `is_highlighted/small_square_cover_url`，样本不含搜索的 `is_adult_content` |
| `project_comments(project_id, **params)` | `/api/v2/community/projects/{数字id}/comments.json` | 本轮 `22897630` 为 `{total_count:0,data:[]}`；非空评论字段没有证据 |
| `explore_latest(**params)` | `/api/v2/community/explore/projects/latest.json` | **仅 `{data}`，没有 `total_count`**；条目与本轮频道作品相近 |
| `feed(**params)` | `/artwork.rss` | `application/rss+xml; charset=utf-8`；RSS 2.0、样本 50 个 item，完整字符串返回，不解析或下载其中媒体 |
| `csrf_token(**attributes)` | **POST** `/api/v2/csrf_protection/token.json` | JSON请求；200单键public_csrf_token对象，配对Cookie由会话保存 |
| `project_search_post(public_csrf_token, **params)` | **POST** `/api/v2/search/projects.json` | form请求；200完整搜索对象，三个命中追加assets/description；见第7节 |

资产也不能统一成同一种字段集：专辑资产样本有
`id/asset_type/width/height/title/has_embedded_player/small_image_url/large_image_url`；
随机作品资产另有 `image_url/original_url/position`、布尔类型标记与裁剪字段。
`original_url=null`、`tag_list=null` 都只是观察值，客户端不将其改成其它字段或空数组。

## 3. 分页、过滤与错误

- 全站列表 `page=1&per_page=1` 返回 1 条，`per_page=50` 返回 50 条，`per_page=51` 是
  **400、text/plain、空正文**。`page=999999&per_page=1` 同样 400 空正文；没有二分精确最大页码。
- 用户作品 `page=1/2&per_page=2` 各 2 条；样本第一页面 ID 为 `17792515/13201269`，
  第二页为 `13207332/13201229`。`page=9999&per_page=2` 是 **200、data=[]、total_count=40**。
  这是页码分页，不是游标；浮动列表不保证跨次请求无重复，也不保证总数不变。
- 搜索 `per_page=3/75` 分别返回 3/75 条；2 和 76 都是 **400 `{message,code}`**，
  `code='per_page'`，消息分别说明 `>= 3` 与 `<= 75`。
- 搜索**没有证实任何可省略的 page/per_page 默认值**。缺 `page` 为 400
  `{"data":"page should be given"}`；前期独立匿名响应也已记录缺 `per_page` 为 400
  `{"data":"per_page should be given"}`。`page=0` 则是 400
  `{"data":"page should be a positive integer"}`。
- GET `filters` 要给序列化后的 **JSON 字符串**。本轮
  `[{"field":"title","method":"contain","value":"dragon"}]` 返回三个含 Dragon 的标题；
  用 `filters[][field]` 等嵌套查询键则为 400 `{"data":"filters should be a string"}`。
  客户端没有特殊转换：共享编码器会将 Python 列表编码成 Rails 数组，因此调用者应明确传字符串。
- GET 附带 `additional_fields[]=assets&additional_fields[]=description` 仍为 200，但本轮
  三个搜索命中都没有 assets/description。随后同会话POST搜索成功追加两字段，
  两者按HTTP动词区分，不让GET方法暗中切换POST。
- 专辑每页 4 条成功、3 条为 400，错误说明 `>= 4`；Explore 每页 10 条成功、9 条为 400，
  错误说明 `>= 10`。它们的上限、其余列表上限与缺省行为未测。
- 不存在的 `/users/zzzz_no_such_user_99.json` 为 **404 text/plain; charset=utf-8，空正文**。
  非 2xx 由共享 `AnybooruHTTPError` 保留 `http_code/url/body/data`，不改写成统一 JSON 错误。
- `/openapi.json` 与 `/no-such-route-xyz-123` 均为 **200 HTML Explore 页**。不能用 200 或
  `.json` 后缀判断 API 是否存在，更不能推广成“所有根级路径绝无 404”。默认 JSON 入口遇到这种
  成功 HTML 会产生 `AnybooruAPIError`；只有显式 `response_format='html'` 才按原文返回。

上述约束均由站点决定。客户端不填查询默认值、不钳位、不自动翻页、不重试、不拆 `data`。
XML/HTML 使用显式返回格式并走 `response.text`，不根据 Content-Type 猜格式或降级。

## 4. 权限、挑战与排除项

两个已知的指定作品入口单独判断：

| 匿名请求 | 实际结果 | 接入决定 |
| :--- | :--- | :--- |
| `/projects/G1ew2N.json` | 403 HTML，`Cf-Mitigated: challenge` | 不封装为可用的 `project_show`，不解挑战，不自动改用另一入口 |
| `/api/v2/community/projects/22897630.json` | 401 JSON，`{"data":null}` | 不猜 API key、Bearer 或 Cookie 契约，不承诺带凭据即可成功 |
| `/api/v2/community/projects/22897630/comments.json` | 200 JSON、空评论列表 | 评论子路由仍纳入；父路由 401 不能外推到子路由 |

原生方法不读取账号凭据，配置只含站点URL，构造不联网。匿名CSRF需要调用者显式取用，不是账号登录。
共享 HTTP 会话的正常连接行为不是挑战绕过；本轮没有登录、没有 Cookie 伪造、没有 UA 伪装或
任何挑战求解。少量路径的不同响应只能说明这些样本有访问差异，不能反推出完整 WAF 规则或因果。

**不纳入原生封装：**

- 所有上传、点赞、收藏、评论写入、关注、购买、消息与账号操作。HTTP POST本身不等同内容写入；
  仅匿名CSRF准备与查询型POST纳入，且绝不自动执行。
- HTML 页面解析、Angular 内嵌 JSON 提取、开发者入口枚举、移动端和用户子域。
- sitemap 遍历、印品目录、商城、学习、招聘、博客、组织、字典、公告、收藏集及只出现于 bundle
  清单的其它路径；它们超出本次公开作品集读取范围，不声称不存在。
- 媒体字节和地址改写：CDN 主机、尺寸档、缓存查询串、Referer/Range 不做请求或转换。
  `assets/cover` 中的 URL 只作为接口返回的字符串交付；不实现更大尺寸猜测或失败回退链。

随机详情和专辑资产是不同资源入口，**不是**按任意已知 `id/hash_id` 精确读取完整作品的替身。
通用 `request()` 可以显式调用站点相对路径，但不增加成功保证、权限或自动备用路径。

政策方面，本轮 `/tos` 确含 §24(d) 的内容采集限制、§24(j) 的禁止规避访问控制、§24(n) 的
使用范围限制，以及 “Don't scrape content from the site.”；§46(a) 写明 NoAI 默认标记、需主动取消。
`robots.txt` 有 `/*/likes`、`/*/following`、`/*/followers` 等 Disallow 与 sitemap 条目。
**路径匿名可读不等于获准采集、再分发或用于生成式 AI。** 本次只做定点接口核验，不提供批量抓取器。

## 5. 候选输入的错误、缺口与过度外推

| 候选说法 | 本轮判断与修正 |
| :--- | :--- |
| 搜索缺 `per_page` 默认返回 50，缺 `page` 默认为 1 | **明确矛盾**：两种缺参均已有匿名 400，错误信息分别要求 per_page/page；不要把输入中的另一处“缺参必报”与默认值同时当真 |
| 用户作品条目与 `/projects.json` “完全相同” | **明确矛盾**：全站样本 21 键，用户样本 19 键，缺 `user/views_count`；冒烟与示例不按全站字段集消费用户列表 |
| 用户档案“字段全集”清单 | **不完整**：列出的清单遗漏 `albums_with_community_projects`，而输入自身后文又使用它；本轮 user_show/quick 都实有该数组，不能从旧清单封死字段集 |
| 频道/Explore 与搜索 item 同构 | **需细分**：本轮前两者多 `is_highlighted/small_square_cover_url`、缺 `is_adult_content`，搜索则相反；共同 id/hash 不等于全字段同构 |
| 搜索 filter_fields 没有 id/hash_id，所以不可能精确定位 | **前半复现，后半未证实**：12 项确实未列这两个名字；不能据此证明服务端拒绝所有未列出的过滤器。本库没有发明按 id 搜索方法 |
| `random_project` 是唯一匿名完整详情入口、tags 必为对象数组 | **未证明唯一性与元素类型**：直接观察一条、冒烟与示例另各一条，tags 都为空；不从空数组推断元素，也不把有限路径调查写成穷尽性结论 |
| 用户作品不传 per_page 就“必然一次全部给完” | **未证实**：本轮明确传每页条数；原资料 40/49 条样本不足以区分默认上限与全部返回，不在正文写为保证 |
| 整片 `/api/v2/**` 不挑战，路径规则与 UA/出口/Cookie 都无关 | **不外推**：本轮只观察指定路径，不做对照或绕过；没有证据证明全路径或恒定 WAF 规则 |
| 根级路径“没有 404”、只存在两种 404 | **过度概括**：本轮两个未知路径为 200 Explore，缺失用户 JSON 却是空正文 404；有限样本不能定义全站路由与全部错误形态 |
| “不存在官方 API/GraphQL/API 子域可用路径” | **未证明全称否定**：仅确认本轮未取得规范以及 `/openapi.json` 不是规范；其它入口未逐项核验 |
| 标称全为只读 GET/HEAD，却列 POST token、POST search 与 Range GET 的结果，并说“全部写操作未测” | **证据口径不一致**：POST 搜索可以是只读查询，但它仍不是 GET/HEAD；本轮不推断原调查到底执行了什么，更不借用其结果冒充本轮执行 |
| 尺寸档/缓存参数/Referer 的少数样本意味着所有媒体恒可用、无鉴权、可随意改 URL | **未实测且不可泛化**：本轮零媒体请求；保留响应 URL，不改变尺寸或查询串 |
| 单个 sitemap 分片的条数可以乘分片数得到全站规模 | **证据不足**：不同分片可能不同长度；本轮不枚举 sitemap、不发布该估算为准确总数 |
| `tag_list` 恒 null、original_url 恒 null、没有缓存或限流 | **样本不是恒值**：本轮列表 tag_list 与随机资产 original_url 为 null，不建立全站恒值/缓存/配额保证，不做速率实验 |
| RSS 与主列表“最新”含义、两个 total_count 不一致的原因 | **仍有缺口**：RSS 本轮 50 item；不证明缓存刷新规律或计数口径，也不把时间变化后的总数差当契约错误 |
| ToS/robots 与旧帮助文章的 NoAI 解释冲突 | **仅政策正文复核**：本轮读了 ToS/robots，没有读取帮助文章或新条款 PDF 的全文，不声称已解决文档版本冲突 |
| §3.3 称 robots 没禁 likes | **与原文矛盾**：输入自己列出的 robots 与本轮200原文都含 `Disallow: /*/likes`；该模式未用 `$` 限定结尾，不能说它只管 HTML、不管同前缀 JSON |
| §17.3 称没有一个资产四档都探过，§10.3 却列同一资产八档200 | **输入内部口径冲突**：不把任一表格当本轮证据；本轮零媒体请求，尺寸适用范围仍未验证 |

## 6. 边界与未实测

- 所有内容写入、PUT/PATCH/DELETE、登录与账号权限；CSRF缺失/失效/跨会话、POST错误分支未测，401不证明认证方案。
- 被挑战详情的成功结构、按数字或短码读取其它固定详情路径、匿名受限内容与非空评论。
- 搜索 `likes/date/rank` 的排序语义、非法 sorting、`pro_first`、非 title 的 filters、隐藏过滤字段、
  query匹配范围/权重、POST filters/其它additional_fields组合、POST分页边界。
- 全站/用户/关注列表缺省条数与最大页码，用户/关注/专辑/频道/Explore 的完整每页上限，
  `album_id=all` 或其它专辑选择、频道 sorting/dimension、评论 page/per_page 与 RSS 其它排序。
- 随机分布、随机 username 参数效果、非空 tags 元素形态，以及资源所有可能缺失字段。
- 全部媒体/CDN 请求与尺寸、Range、Referer、缓存戳、NoAI 响应头；没有访问返回的图片 URL。
- robots 之外的 sitemap 内容、其它主机、其它 API 模块、官方手册/源码部署版本、CORS、配额与挑战触发机制。

以上未实测项不影响已封装调用原样发送，但不能写成已验证能力。所有页面数字仅为当次快照，
不是客户端常量；本轮的 Python 方法执行范围与原始路由观察范围分开记账。

## 7. POST 搜索与 CSRF 的纳入决定（2026-09-20 跟进）

初版把没有实测的POST两步整体排除，混淆了“未验证”与“不应提供方法”。复核后纳入
`csrf_token(**attributes)` 与 `project_search_post(public_csrf_token, **params)`，
符合本库显式包装、逐项标注证据的口径：调用者主动发起，库不获取账号、不自动取token或续期、不重放请求。
候选输入只用作选点；以下成功结论由本次新样本支撑。

1. `csrf_token(create_csrf_token_request='true')` 发JSON到
   `POST /api/v2/csrf_protection/token.json`，200 application/json；返回单键对象
   `public_csrf_token`（样本88字符），响应Cookie名为PRIVATE-CSRF-TOKEN与__cf_bm。
   requests会话自然保存Cookie，公开token仅保留在调用者本次变量，不新增持久凭据字段。
2. 同一个client把公开token写入PUBLIC-CSRF-TOKEN头，发
   `query=cat&page=1&per_page=3&sorting=relevance&additional_fields[]=assets&additional_fields[]=description`
   的form-urlencoded到 `POST /api/v2/search/projects.json`，200 application/json，
   返回 `{total_count:118783,data:[…]}`。三个命中id为10122141/17985153/3049628，
   均有description字符串和assets数组，资产条数6/11/17。

`request()` 新增显式 `form` 参数，沿共享Rails编码器发送表单；原 `data` 仍然是完整JSON，
GET project_search不变。两个POST方法各只发一次请求，不自动读取或拆除返回信封。
搜索资产的宽高、位置、small/large_image_url按站点返回；没有访问任何媒体URL。

**POST的实际增量是给搜索结果补充assets/description，不是“唯一资产入口”。**
既有album_projects与project_random已经可返回资产；新方法也不是任意id/hash的详情查询，
不自动绕过固定详情路径的403或401。

本次补充共3次POST尝试：初次token响应进入记录钩子后，临时记录器把请求正文bytes写JSON失败、
退出1；状态和UTC未保存，不补称200，搜索也未发送。修正记录器后只重跑受影响的两步，两个200、退出0。
不是HTTP失败重试或token自动续期；原GET冒烟与两个示例未再跑，仍分别10/4/4次GET。
公开token与Cookie值不落盘或写入公开材料。

缺/坏/过期token、412错误、POST JSON搜索、POST filters与其它排序/边界/媒体类型覆盖仍未实测；
输入关于这些分支的说法只作候选。不能把GET的分页错误与限制未经核验直接推广到POST。
