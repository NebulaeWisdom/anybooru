# nhentai：契约审计附注

本文供维护者核对依据与范围；调用入门见 [客户端用法](nhentai.md)，参数与返回字段见
[方法参考](nhentai-api.md)，任务选型见 [能力入口](nhentai-capabilities.md)，命令与逐请求结果见
[实测记录](verification.md#nhentai匿名只读实测2026-09-20)。

## 1. 依据与家族判定

本家族没有本地服务端源码。依据分为：

- **S（规范）**：[官方 OpenAPI](https://nhentai.net/api/v2/openapi.json)，本轮匿名 GET 为
  `200 application/json`；OpenAPI `3.1.0`，`info.title="nhentai API"`，版本
  `2.0.0+14bccf7`。实际包含 **98 个路径、114 个 HTTP 操作、129 个 schema**。
- **C（官方变更记录）**：[changelog](https://nhentai.net/api/v2/changelog)，本轮
  `200 text/html; charset=utf-8`。它记录变更时间，不能代替当前规范或当前响应。
- **L（本轮响应）**：匿名 GET 的真实 URL、HTTP 状态、Content-Type、完整正文；公开摘要集中于实测记录。
- **T（候选资料）**：接入前的综合调查，不当作已经完成的本轮验证。下面逐项区分复现、修正与尚未证明。

规范引用用 JSON Pointer（例如 `#/paths/~1api~1v2~1galleries/get`）和 schema 名，
不是服务端源码行号。`paths` 的每个 HTTP 动词各算一次 operation。

**这是新家族，不是给现有类添一个站点 URL。** 它的 `/api/v2/galleries`、`/search?query=`、
标签类型/slug 路径、`Authorization: Key …`、画廊列表与详情的不同字段结构，以及多种分页结构，
合在一起不符合现有 Danbooru、Moebooru、Serika、e621ng、Zerochan、Gelbooru、Gelbooru02、
Shuushuu、Sakuria、Anime-Pictures 或 Cosine 的契约。仅有 `result` 键或 JSON 格式相同不构成同族。
命名统一为 `Nhentai`、`nhentai.py` / `api_nhentai.py`、站点键 `nhentai`、`docs/nhentai*.md`。

## 2. 接入范围与排除项

原生面为 **36 个方法：31 GET、4 POST、1 DELETE**。覆盖：

| 资源 | 纳入内容 | 规范入口 |
| --- | --- | --- |
| 服务 | 版本、CDN 列表、含公告的配置 | `/api/v2`、`/cdn`、`/config` |
| 画廊 | 最新、按标签、热门、随机 ID、详情、相关、评论、评论数、标签建议 | `/galleries*` 的公共读取 |
| 搜索与标签 | 画廊搜索、标签列表/单项/ID 批量解析、标签补全 | `/search`、`/tags*` |
| 社区整理 | taxonomy 列表/统计/已解决/单项/评论/编辑历史，GTS 积压与新标签 | `/taxonomy*`、`/gts/backlog`、`/gts/new-tags` 的读取 |
| 账号关联资源 | 自己的资料、收藏列表/随机/状态、黑名单列表/ID，公开用户资料 | `/user`、`/favorites*`、`/blacklist*`、`/users/{user_id}/{slug}` |
| 显式需权限操作 | 添加/移除收藏、更新黑名单、取得整卷短期下载地址 | favorite 的 POST/DELETE、`POST /blacklist`、`POST /galleries/{gallery_id}/download` |

`POST /tags/search` 是查询，但本轮没有执行任何 POST。`gallery_download()` 仅返回站点 JSON
中的 `url` 与 `expires_at`，不访问这个 URL、不下载整卷，也不逐页抓媒体。

以下不做原生封装：

- `auth` 登录/注册/刷新/注销/密码恢复、API key 创建管理、其余 `user` 管理。
  规范 `tags[name=user].description` 写的是 **“First-party and internal only, bar GET /api/v2/user”**，
  因而 `user_me()` 是明确例外，不应把它与账号管理一起排除。
- 只接受 User Token 的评论写入、举报、画廊编辑、标签建议写入/投票、taxonomy 写入与全部 moderation。
- PoW、CAPTCHA 与广告 `zones`：不是图库资源获取所需的第三方面，也不实现挑战求解。
- 旧 `/api/gallery` 系列与 `nhentai.to` HTML：不是 v2 的替代路径；失败不自动回退。

这不是“114 个操作全部支持”的宣称。通用 `request()` 只提供显式 JSON 请求能力，不提供登录、
自动续期、内容解析器、权限提升或成功保证。

## 3. 认证与传输判断

规范 `#/components/securitySchemes` 定义了同一个 `Authorization` 头的两种形式：
`Key <api_key>` 与 `User <token>`；`info.description` 指定第三方使用 Key。构造器只提供 `api_key`，
默认包内配置为空。`None` 读站点配置，显式 `''` 保持匿名；构造不联网。

不能仅看 operation 的 `security` 数组判定匿名不可用：画廊列表等列出了两种方案，
但 description 明写可选认证，本轮确为匿名 200。相反，下列六个纳入方法的路径匿名均为
`401 application/json`，正文 `{"error":"Authentication required"}`：
`/user`、`/favorites`、`/favorites/random`、`/blacklist`、`/blacklist/ids`、
`/galleries/658856/favorite`。排除的 `/user/keys` 同样观察到 401。

实现复用共享 HTTP 层，保留全部 JSON：字典不拆 `result`，数组不包装，整数不转成字典。
非 2xx 保留状态和正文；不把 400 改成规范列出的 422，也不把 HTML 错误当作空 JSON。
可选查询参数不在客户端填默认值、钳位、重试或修正；JSON 正文的空数组和 null 原样交给服务端。

## 4. 返回形态与分页的证据

| 项目 | S | L 与实现取舍 |
| --- | --- | --- |
| 画廊列表 | `PaginatedResponse_GalleryListItem_` | 保留 `result,num_pages,per_page,total`；列表标题是扁平字段，标签是 `tag_ids` |
| 画廊详情 | `GalleryDetailResponse` | `title` 为对象，`tags` 为完整标签数组，`pages` 为逐页地址与尺寸；与列表不是同一结构 |
| 热门 | 200 schema 为 `GalleryListItem[]` | 本轮 5 项；schema 没有 `minItems/maxItems`，不把 5 写成固定返回条数 |
| 单标签 | `TagResponse` | `tag_show('language','english')` 返回单个对象，不是数组或 `result` |
| 评论数 | 200 schema 为 integer | `/comments/count` 返回裸整数 0；这只是该画廊的观察值 |
| 相关与默认画廊建议 | `RelatedGalleriesResponse` / `SuggestionListResponse` | 本轮分别为 `{"result":[…]}` / `{"result":[]}`；建议 schema 还允许 `has_more,num_pages,total`，不能从默认空样本断言任何参数下都仅有 result |
| 标签索引 | `TagPaginatedResponse` | `per_page=1` 仍回显 120；默认 popular 无 alphabet，`sort=name` 实际包含 alphabet |
| taxonomy / GTS | 各自的 ListResponse | 常见 `result,has_more,num_pages,total`，没有公共的 per_page 回显；新标签与编辑历史本轮只有 result |
| 已解决 taxonomy | 查询 schema 声明 per_page 1–100、默认 25 | `per_page=2` 实回 50 项；请求条数与实际条数不一致，不在本地截断 |

`GalleryDetailResponse` 中附加字段并非全都必填。`include=comments,related,favorite,suggestions`
本轮追加了 `comments,comment_count,related,suggestions`，没有 `is_favorited`。
单传 `include=favorite` 也没有这个键；只确认匿名响应结构，不把浮动计数的字节相等当作契约。
C 的 2026-05-21 条目说明 include comments 只取前 50 条，继续读取应走分页评论接口。

列表 `/galleries?page=1&per_page=2` 的一次快照为 `total=646010,num_pages=323037`，
而 `ceil(total/per_page)=323005`，两者不同。`page=100000&per_page=25` 返回尾部 24 项、HTTP 200，
不是空页。这里既不能保证总数除法是准确末页，也不能把空页或不足一页当成所有端点统一终止条件。
本库不提供自动遍历器，调用者明确指定需要的页数；更多差异见 [分页](pagination.md)。

## 5. 候选资料的逐项校正

| 候选说法 | 本轮结论与依据 |
| --- | --- |
| 98 paths / 114 operations / 129 schemas，版本 `2.0.0+14bccf7` | **复现**。实际取回规范计数一致，不是把原资料数字抄作实测 |
| `/api/v2` 可用，旧 API 403 | **复现并限定路径**。版本根 200；`/api/gallery/658856` 403 text/plain，正文正是 `Use new API https://nhentai.net/api/v2/docs`。不是 v2 根 403，也未遍历所有旧路由 |
| “API 全部 200” | **错误泛化**。已列六个资源读取与 `/user/keys` 实为匿名 401；成功与拒绝要按路由区分 |
| 热门“固定 5 条” | **只复现样本 5 条**。数组形状被规范与响应支持，恒定长度没有规范保证 |
| 单标签对象、评论数整数、tags IDs 数组 | **复现**。不能套统一 result 解析 |
| `POST /tags/search` 裸数组 | **S 确认，未运行**。规范仅列 POST，200 为 TagResponse 数组；不能把本轮 GET 调查写成该 POST 的 200 证据 |
| 标签列表 alphabet “响应里没有” | **不成立的泛化**。默认 popular 样本没有；`sort=name` 样本实际包含 |
| tag_list 与单标签固定同一组字段 | **需补充**。本轮列表项只有 `id,type,name,slug,url,count,description`；详情另含 nullable 的 `is_community,pending_describe_id`；schema 非必填字段不能假定始终出现 |
| user/auth 全部只给第一方 | **遗漏 GET /user 例外**。规范 tags 描述和 2026-04-02 changelog 均明确允许 Key 读取自己的资料（隐藏 email） |
| `num_pages` 不一致，所以自己用 total/per_page 算末页 | **前半复现，建议不可靠**。计数/页数可能漂移，越界 galleries 返回尾部；客户端保留两者，不另造保证 |
| 搜索 per_page 不存在、传了无效 | **复现样本**。规范仅 query/sort/page；传 per_page=2 仍回 25 条且回显 25 |
| 标签 per_page 实际固定 120 | **复现已测类型的回显**。tag 类型实回 120 条；language 共 14 条，回显仍 120；不泛称每次恰有 120 项 |
| tagged total 恒 null | **本轮样本为 null，不能保证恒值**。schema 接受 integer 或 null；不在本地改成 0 |
| 参数校验 400 | **复现，并与 S 的 422 条目有差异**。page=0、per_page=101、缺 query、非法 sort 均 400 error/details；非法 tag type 为 400 error |
| taxonomy/GTS 的返回只需列清单 | **原资料细节不足**。补齐 UUID 路径、has_more 与分页字段；resolved 的 per_page=2 实际 50 项是额外发现 |
| 所有记录均为只读 GET，又列 POST 搜索/下载 200/401 | **证据口径自相矛盾**。保留为历史候选叙述，不冒称本轮执行过这些 POST，也不推断原调查到底执行了什么 |
| taxonomy/GTS/zones “全部实测”，结尾又说仅清单枚举 | **证据分级不一致**。本轮只把自己收到的响应计为 L；广告未测 |
| count、num_favorites、总页数与旧快照不同 | **数据变化，不是契约错误**。不写断言锁定旧计数；旧尾页 12 项与本轮 24 项也不是固定长度规则 |

## 6. `.to` 与 `.net` 的区别

本轮只取页面 HTML，不执行页面 JavaScript、不请求其中图片或广告。
`https://nhentai.to/g/658856/` 是 `200 text/html; charset=UTF-8`，包含
`var gallery = new N.gallery({...})`，`num_pages: 51,` 后直接闭对象：**尾逗号使这段不是合法 JSON**。
这不是 v2 GalleryDetailResponse，且本库没有清洗或解析该对象的代码。

同一 URL 数字 `658856`：`.to` 内嵌 `id=642949,media_id="3994845"`，而 `.net` 详情为
`id=658856,media_id="4006343"`。不能把站点根从 `.net` 换成 `.to` 继续调用 Nhentai，
也不能把 URL id 或 clone 内部 book id 自动当成 `.net` id。

**“标签 id 通用”必须拆成三个字段。** `.to` 本地 `tags[].id=22`，其 `nh_id="2937"` 对应
`.net` 单标签 `id=2937`；两个 `id` 本身并不通用。该 clone 同一页还包含 `nh_id="-2"`
与 `nh_id="-289"`，所以连 `nh_id` 也不能无条件承诺总有可解析的 `.net` 对应项。
负值的业务含义与全部映射覆盖率未确认。

七个已测 `.to` API 样本均为 404：旧 gallery、v2 gallery、任意不存在路径、v2 openapi、
gallery/1、旧搜索、v1 gallery。带 `Accept: application/json` 的样本返回
`{"message":""}`；`/api/gallery/1` 带 `Accept: text/html` 返回完整 HTML。
**有限 GET 的 404 不能证明服务器没有任何 `/api/**` 路由，更不能证明任何动词都无效。**
站点另有 `GET /trending-searches`，本轮 200 application/json、数组 10 项，
因此“完全不提供 JSON”也不准确。以上不足以建立与 `.net` 同族的可用契约，故不纳入默认站点与封装。

## 7. 边界与未实测

- 规范对齐不等于成功认证：未申请、索要或使用任何 Key/User Token；未验证有效 key、伪造 key、权限等级。
- 全部 POST/DELETE 均未执行，包括只读的 tag_search；收藏、黑名单更新、下载地址申请的成功形态只按 S。
- 未调用登录、刷新、用户管理、moderation、广告、PoW/CAPTCHA，也未求解挑战。
- 所有媒体主机、媒体字节、Range、双后缀 URL 的成功与 Referer 条件均未验证；客户端不猜媒体路径、不修后缀。
- 未触发限流去验证配额，不重试 429；极端搜索页码 503、完整排序/过滤组合、全站末页与其它部署未实测。
- 公告本轮 null、选定画廊评论为空、taxonomy 编辑历史为空；非空内容不能宣称已覆盖。
- `.to` 阅读页、列表、搜索、UA 对照与其它 clone 域名未验证；不从几个 404 推断完整路由表或法律条款。
- 31 个原生 GET 路径的直接 HTTP 观察与 Python 方法真跑分开记账，后者以实测记录中的脚本输出为准。
