# Anime-Pictures：接口依据、权限与排除项

本页供核对依据，不代替[客户端用法](anime-pictures.md)或[方法参考](anime-pictures-api.md)。
Anime-Pictures（`anime-pictures.net`）是自研后端的插画站，本类一共 **13 个原生方法**：
**11 条 JSON 读取路由**（其中 `post_tags` 匿名被拒）、**原图入口 `image_get()`**（也是 `GET`，成功形态未实测）
加 **1 个 `POST`**（`post_create`，需权限），外加通用入口 `request()`；**只有 `image_get()` 返回字节**。
本库不提供登录 / 注册 / 刷新令牌的方法，也不替调用方猜凭据方案。

依据**只有匿名响应**：没有可读到的官方 API 页面（手册页 `/pages/api` 被 Cloudflare 质询挡下）、
没有 OpenAPI、没有服务端源码。本页把「本轮真实请求过的」（L）与「输入文档候选、本轮没测到的」（T）
分开写，**T 的部分集中在[未实测集中清单](#未实测集中清单)，不进正文结论**。

## 资料来源与等级

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **L：本轮匿名只读实测** | 90 次直接 HTTP 观察（首轮路由与字段 21 次、参数取值 69 次；串行、相邻 ≥1.3 秒、不重试、不跟随跳转、不下载媒体），逐条 URL、状态与字段见[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19) | 12 条 `GET` 路由里 10 条有 `200` 样本、`post_tags` 有 `403`、`image_get` 有 `403` 空正文；非 `200` 共 14 次（`400`×4、`403`×2、`404`×6、`410`×1、`500`×1）。直接路由证据**不等于**运行过对应 Python 方法 |
| **T：输入文档（候选）** | 接入时收到的《Anime-Pictures 接口文档（综合版）》，自称内容来自对 API 主机的匿名实测（2026-09-19）并交叉核对公开客户端源码；**没有可公开核对的发布链接** | 尚未复测的参数取值、默认值、上限、枚举、错误码全集、媒体地址公式与字段语义。这些一律只列在[未实测集中清单](#未实测集中清单) |
| **没有可用官方 / 服务端来源** | 官方手册页 [pages/api](https://anime-pictures.net/pages/api) 存在但被 Cloudflare 质询挡下，没有可读到的内容；未取得 OpenAPI 或服务端源码 | 错误文案包含 `i32` 不能单独验证实现语言；本页不声称已核实 Rust / SvelteKit 实现细节 |
| **外部客户端源码（未独立读过）** | 输入文档附了几个公开客户端仓库的链接作为参数名与地址公式的交叉依据 | 本轮**没有独立读过这些仓库**，输入文档里引自它们的说法只算候选，不能写成「已核对源码」 |

输入列出的外部客户端入口为 [flexbooru-ap](https://github.com/onlymash/flexbooru-ap)、
[MoeLoaderP](https://github.com/xplusky/MoeLoaderP)、[yandere-masonry](https://github.com/asadahimeka/yandere-masonry)
和 [danbooru_downloader](https://github.com/ANewPassword/danbooru_downloader)。这里只保留来源线索，
不提供未独立核对的源码行号，也不把旧客户端路由视作现役 API 契约。

三点必须记住：

1. **L 覆盖 12 条 `GET` 路由**：10 条匿名 `200`、`post_tags` 匿名 `403`、`image_get` 匿名 `403` 空正文；
   **`POST` 一次都没发**，也没有任何带凭据的成功样本。参数默认值与取值（`page`/`posts_per_page`/
   `order_by`/`ldate`/`search_tag`/`denied_tags`/`aspect`/`color`/`ext_*`/`user`/`stars_by`、
   各列表的 `limit`/`offset`/`type`）在参数轮里已实测，见[参数实测](#参数实测第二轮-69-次)。
2. **没有 L 的说法不当契约**：默认值、取值枚举、上限、错误码全集、字段语义、媒体公式都只算候选，
   集中在[未实测集中清单](#未实测集中清单)，不要用它们推断未测参数的行为。
3. **样本不是固定数据集**：编号、计数、排名每天都在变；同一条标签在两个时间点也可能返回不同的计数与浏览量，
   本页的数字只作当时响应的例子。

## 13 个方法的逐条依据

「本轮 L」列统计 90 次直接 HTTP 路由观察（首轮 21 + 参数轮 69）；不包含随后冒烟与示例的客户端请求。
路径里除 `service_info()` 的 `GET /` 与 `image_get()` 的 `GET /pictures/get_image/{file_url}` 之外，
都接在 `https://api.anime-pictures.net/api/v3` 后面。

### 服务信息（1）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `service_info()` | `GET /` | 1 | `200 application/json`，正文只有一个键 `message`，值 `"Hello, World!"` |

### 帖子（5：4 个 `GET` + 1 个 `POST`）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `posts_list(**params)` | `GET /posts` | **51** | 首轮 2 次（`page=0`/`page=1`）+ 参数轮 49 次：`page` 缺失/`abc` 的 400、`page=-1` 的 500、越界页 200 空数组、`posts_per_page` 8 个取值、7 个 `order_by` 取值 + `random` 回落、`order=asc/desc` 无影响、3 个 `search_tag`、4 个 `denied_tags`、`ldate` 0～8、10 组过滤参数（`aspect`×2、`color`×2、`ext_*`×4、`user`、`stars_by`）、`type=json` 的 400；信封键见[方法参考](anime-pictures-api.md#posts_list) |
| `post_show(post_id, **params)` | `GET /posts/{post_id}` | **3** | `929452` → `200`，**该样本**顶层 9 键 `post`/`source`/`user`/`moderator`/`tags`/`file_url`/`star_it`/`favorites_users`/`tied`；`post` 比列表项多 `small_preview`/`medium_preview`/`big_preview`；响应头带 `vary: Cookie, Authorization`。**用法路径真跑发现 `382872` 没有 `source` 键**（读 `detail['source']` 触发 `KeyError`）→ 顶层键集合**不固定**，见[矛盾表](#实测与输入文档的矛盾)。另两次是错误路径：`999999999` → 410、`top` → 400 纯文本 |
| `post_comments(post_id, **params)` | `GET /posts/{post_id}/comments` | 1 | `382872` → `200`，顶层只有 `success`/`comments`，**没有 `offset`/`limit`/`count`**；每条是 `{comment, user}`（**没有 `post` 段**） |
| `post_tags(post_id, **params)` | `GET /posts/{post_id}/tags` | 1 | `929452` → 匿名 `403` `{"errormsg":"You not have rights","success":false}`；**成功形态没有样本** |
| `post_create(data, *, idempotency_key=None)` | `POST /posts` | **0** | **一次都没发**；请求体、成功状态码、凭据方案全未知 |

### 标签（2）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `tags_list(**params)` | `GET /tags` | **15** | 首轮 4 次：`tag=hatsune miku` → `200`、`count` 1、命中 id 407；`tag=hatsune` → `count` 0；不带参数与 `search=hatsune` 的响应计数与前几项 id 完全一致（`limit` 20、`count` 156541、前 3 个 id 226296/226295/226294）→ **`search` 被忽略**。参数轮 11 次：`type` 0～8 的计数（8 → `count` 0、`tags` 空）、`limit=1000` 回落 100、`offset=2` 生效 |
| `tag_show(tag_id, **params)` | `GET /tags/{tag_id}` | **2** | `407` → `200 {"success":true,"tag":{…}}`；`999999999` → `404 {"errormsg":"Tag not found","success":false}` |

### 用户（2）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `users_list(**params)` | `GET /users` | **4** | 首轮 `limit=2&offset=0` → `200`，`count` 225284，`users` 2 条（id 257203、294066）；参数轮：不带参数 `limit` 20 / `offset` 0、`offset=2` 生效、`limit=101` 回落 100。用户对象带 `login` |
| `user_show(user_id, **params)` | `GET /users/{user_id}` | **2** | `294066` → `200`，**顶层三键** `success`/`user`/`errormsg`（`errormsg` 为 `null`）；本样本 `user` **没有 `login` 键**；`999999999` → `404 {"errormsg":"User not found","success":false}` |

### 评论（2）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `comments_list(**params)` | `GET /comments` | **4** | 首轮 `limit=2&offset=0` → `200`，`count` 14988，每条 `{comment, user, post}`；`post` 段**没有预览图字段**。参数轮：不带参数 `limit` 20 / `offset` 0、`offset=2` 生效、`limit=101` 回落 100 |
| `comment_show(comment_id, **params)` | `GET /comments/{comment_id}` | **2** | `174693` → `200`，**顶层三键** `success`/`comment`/`user`（**带 `user` 段**）；`999999999` → `404 {"errormsg":"Have no comment","success":false}` |

### 原图入口（1，成功形态未实测）

| 方法 | 路由 | 本轮 L | 实测要点 |
| :--- | :--- | :--- | :--- |
| `image_get(file_url, *, headers=None)` | `GET /pictures/get_image/{quote(file_url, safe='')}` | 1 | 真实文件名的匿名请求得到 **403 空正文、无 `Content-Type`**（`Content-Length: 0`）；成功字节形态未知 |

### 错误路径（已计入上表与总数）

| 探测 | HTTP | 正文与类型 |
| :--- | :--- | :--- |
| `GET /posts/999999999` | `410` | `{"errormsg":"Post not found","success":false}`，JSON |
| `GET /tags/999999999` | `404` | `{"errormsg":"Tag not found","success":false}`，JSON |
| `GET /users/999999999` | `404` | `{"errormsg":"User not found","success":false}`，JSON |
| `GET /comments/999999999` | `404` | `{"errormsg":"Have no comment","success":false}`，JSON |
| `GET /posts/top` | `400` | `` Invalid URL: Cannot parse `top` to a `i32` ``，`text/plain; charset=utf-8` |
| `GET /posts`（缺 `page`）、`GET /posts?page=abc` | `400`（各 1 次） | `{"errormsg":"Missing or invalid \`page\` parameter","success":false}`，JSON |
| `GET /posts?page=-1` | `500` | `{"errormsg":"Internal server error","success":false}`，JSON |
| `GET /posts?page=0&posts_per_page=2&type=json` | `400` | `{"errormsg":"Only json_v3, json1, and xml response types are supported","success":false}`，JSON |
| `GET /api/v3/not_a_route`、`GET /api/v2/comments`、`GET /pictures/view_posts/0?type=json` | `404`（3 次） | **空正文、无 `Content-Type`**（`Content-Length: 0`） |

## 参数实测（第二轮 69 次）

这一节只放第二轮直接请求能定性的参数行为；逐条 URL 与字段见
[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)，参数表（含「不传时怎样」与字面示例）在
[方法参考](anime-pictures-api.md#posts_list)。

| 参数 | 本轮实测（L） |
| :--- | :--- |
| `posts_list(page=…)` | **必填**；不传或 `abc` → 400；`-1` → 500；`999999&posts_per_page=100` → 200、`response_posts_count` 0、`posts` 空，`posts_count`/`max_pages` 仍是 667906/6679 |
| `posts_list(posts_per_page=…)` | 缺省 80；`1`/`2`/`3`/`100` 回显对应值；`101`/`150`/`1000`/`0` → 60；`-1` → 80。**没有穷举 1～100**，也不保证实际条数（越界页回 0 条） |
| `posts_list(order_by=…)` | `date` → `929492,929491,929490`；`date_r` → `2,3,5`；`rating` → `301063,423454,602864`（`score_number` 629/525/442）；`views` → `88793,304173,45264`；`size` → `34056,43659,45028`；`tag_num` → `581823,266625,264140`；`id` → `1,2,3`；`random` 与 `date` 同 ID |
| `posts_list(order=…)` | `order_by=rating&order=asc` 与 `...&order=desc` 的前三 id 都跟不带 `order` 相同 → **不能宣布所有 `order` 取值都不存在** |
| `posts_list(search_tag=…)` | `hatsune+miku` → `posts_count` 21008，且信封多出 `exclusive_tag`（完整标签对象 407）；`long+hair+blue+eyes` → 146065（没有逐帖验 AND）；`zzzznotexist` → `posts_count` 0、`max_pages` **0** |
| `posts_list(denied_tags=…)` | `long+hair` → 269346；`blue+eyes` → 510020；`long+hair+blue+eyes` → 667906（整串不匹配、等于全库）；重复同名参数 `denied_tags=long+hair&denied_tags=blue+eyes` → 510020（后者生效）。**没有**故意发未编码空格，输入文档的「静默丢参」未复测 |
| `posts_list(ldate=…)` | `0`→667906（最旧 2009-10-11）、`1`→411、`2`→1879、`3`→57、`4`→11286、`5`→28743、`6`→61654、`7`→84306、`8`→667906（与 `0` 相同）。区间名（周/月/日/半年/年/两年/三年）是**推断** |
| `posts_list(aspect/color/ext_*/user/stars_by)` | `aspect=16:9` → 37502（样本尺寸 7017×3947、5500×3094，**不是严格 16:9**，容差未测）、`aspect=1:1` → 18296；`color=FF0000` 与 `%23FF0000` 都是 1645；`ext_jpg=jpg` → 470199、`ext_png=png` → 196121、`ext_gif=gif` → 1586、`ext_jpg=yes&ext_png=yes` → 666320（值不参与比较）；`user=204183` → 30757；`stars_by=13734` → 41519 |
| `posts_list(type=json)` | 400，正文说只支持 `json_v3`/`json1`/`xml`；**本轮没有请求那三种格式**，不承诺默认 JSON 客户端能解析 XML，也不为新格式加方法 |
| `tags_list(limit/offset/type/tag/search)` | 缺省 `offset` 0、`limit` 20；`limit=1000` → `limit` 100（回 100 项）；`offset=2` 跳过基线前两项；`type` 0～7 都非空（4303/56435/4474/5510/76532/4606/1909/2772），`type=8` → `count` 0、`tags` 空（不是错误）；`tag` 精确（1 / 0）；`search` 与默认的完整 JSON 相同 |
| `users_list` / `comments_list` | 缺省 `offset` 0、`limit` 20（各回 20 条）；`offset=2` 生效；`limit=101` → `limit` 100（各回 100 条） |
| 旧路由与未知路由 | `/api/v2/comments`、`/pictures/view_posts/0?type=json`、`/api/v3/not_a_route` 都是 404 空正文；其它旧版路径本轮没有请求 |

## 权限与访问面

* **12 条 `GET` 路由**：10 条匿名 `200`；`post_tags` 匿名 `403`；`image_get` 匿名 `403`（空正文）。
* **`post_create`**：一次都没发；输入文档称匿名 `401`，本轮没有样本。
* **凭据怎么带未实测**：本库只做「调用方传值、原样送头」——构造函数 `authorization` / `cookie` 空默认，
  非空时按原值送 `Authorization` / `Cookie`，**不添加 `Bearer`、不猜 Cookie 名、不登录、不刷新、不发明 token 接口**。
  输入文档提到 CORS 预检允许 `authorization` 与 `idempotency-key` 两个头、浏览器登录态 Cookie 名是
  `anime_pictures_jwt`：**本轮没有复测 OPTIONS，也没有验证过任何登录态**，这些只作候选。
* **不能由匿名 `403` 推断凭据方案**：`post_tags` 与 `image_get` 的 403 只说明「匿名被拒」，
  既不能证明「填上某个 Cookie 就一定成功」，也不能证明 Cookie 是唯一认证方式。
* **限流**：本轮未取得 429 或显式限流响应，未获得官方配额；这不证明无限流。
  本库不做节流、不做退避、不重试。

## 排除路由与不封装的能力

| 类别 | 例子 | 为什么不封装 |
| :--- | :--- | :--- |
| 其它写动词 | `PUT` / `PATCH` / `DELETE /api/v3/posts/{id}` | 只有输入文档提到的 CORS 通用 `access-control-allow-methods` 列过这些动词，该路由自己的 `OPTIONS` 输入文档记录为 `Allow: GET,HEAD,POST`；**本库不封装，也没有实测路由** |
| 登录 / 令牌 | 旧 web 主机的 `POST /login/submit`（表单 `login`/`password`/`time_zone`）与 `/login/logout` | 输入文档说这些属于 web 主机且未实测；本库不做登录，凭据由调用方提供 |
| 旧版 web 路由 | `/pictures/view_posts/{page}?type=json`、`/pictures/view_post/{id}?type=json`、`/pictures/vote`、`/pictures/autocomplete_tag`、`/pictures/add_comment/{id}`、`/api/v2/comments`、`/api/v2/posts/{id}/comments` | 本轮复测了 3 条：`/api/v2/comments`、`/pictures/view_posts/0?type=json`、未知路由 `/api/v3/not_a_route` 都是 **404 空正文**；其余旧路径没有请求。新代码请用 v3 接口，**不要依赖这些遗留路径** |
| 媒体 CDN | `https://opreviews.anime-pictures.net/{...}`、`https://oimages.anime-pictures.net/{...}` | 本库不下载媒体；**本轮一次 CDN 请求都没发**，公式只作候选写在[方法参考](anime-pictures-api.md#媒体地址只是文本未实测) |
| 标签联想 | v3 里的 `search` 等参数（本轮证 `search` 被忽略）；旧版 `POST /pictures/autocomplete_tag` | v3 没有找到联想 / 前缀搜索；本轮没有寻找补全端点，也不凭别家引擎的惯例造方法 |
| 头像地址 | 输入文档里旧客户端拼的 `avatars/{id}_{version}.jpg` | API 只给 `avatar_version` + `isavatar`，本轮没有请求过头像地址，**不当契约、不写进代码** |
| Web 前端 | `https://anime-pictures.net` 的 HTML 页面、`/api/v3/*` 到 API 主机的 `302` | 输入文档记录页面被 Cloudflare 质询、`302` 只是反代；本库只对 API 主机说话，不做 HTML 解析，也不依赖那个 `302` |

## 实测与输入文档的矛盾

下面分别列出确定反例与字段清单补充；依据为 90 次直接路由观察及随后实际运行的客户端请求。
数据快照变化不是契约错误，单独列在表后。未被证实或推翻的候选见[未实测集中清单](#未实测集中清单)。

| 项目 | 输入文档的说法 | 本轮实测（L）与处理 |
| :--- | :--- | :--- |
| `user_show` 的顶层字段 | 示例响应只有 `success` 与 `user` 两个键 | **L 是三键**：`{"success": true, "user": {…}, "errormsg": null}`。成功时顶层**确实带 `errormsg`**（值为 `null`），字段清单需要补上 |
| `comment_show` 的顶层字段 | 8.2 节写「只返回 `comment`，没有 `user` / `post`」 | **L 是 `{"success": true, "comment": {…}, "user": {…}}`**：单条评论**带评论者的 `user` 段**，只有 `post` 段确实没有。输入文档那句「没有 `user`」是错的 |
| `favorites_users[].favorite` 的键 | 字段说明仅列 `{post,juser_id,addtime}` | `929452` 的一项还带 `folder="Azur Lane"`，另一项没有 `folder`；字段清单有遗漏，但该键不是必有 |
| `status_type` 偶发缺失 | 15.15 与 5.1 节说部分帖子对象没有这个键 | 本轮复现：反序列表 id 2、3、5 没有此键。此项与输入一致，记录在这里提醒不要当必有字段 |
| 帖子详情的顶层键「固定」 | 5.2 节称固定 9 个顶层键 | `929452` 有 9 键，但 `382872` 没有 `source`；初版示例因此 `KeyError`。修正示例不无条件读取该键后，4 次 GET 全部 200、退出 0；完整记录见验证页。客户端始终保留真实缺失，不补默认值 |
| `score` 恒为 `0.0` | 5.1 字段表与 15.5 都写恒为 0.0 | 反例：id 2 的 `score=73.0`、`score_number=70`；id 301063 为 `1446.0` / `629`。本轮 `order_by=rating` 仍与 `score_number` 倒序吻合，但不能覆盖或丢掉非零 `score` |
| `max_pages` 公式 | 5.1 说 `max_pages = ceil(posts_count / posts_per_page) - 1` | **L 只对非空结果吻合**：`search_tag=zzzznotexist` → `posts_count` 0、`posts` `[]`、`max_pages` **0**（不是 `-1`）。本库不重算这个字段，翻页判断请用响应里的原值 |
| `search_tag` 的示例 URL | 12 节的能力速查写 `GET /api/v3/posts?search_tag=hatsune%20miku`，**没有带 `page`** | **L：缺 `page` 直接 400**（`{"errormsg":"Missing or invalid \`page\` parameter","success":false}`），照抄那条 URL 拿不到数据；调用时 `page` 必填 |
| 「所有读接口匿名可用」 | 3.1 节写「第 5～8 节所有 `GET` 读接口匿名可用，实测 `200`」 | **L 与它自己的 3.2/5.4 矛盾**：`GET /posts/{id}/tags` 匿名是 **`403`**（`image_get` 也是 403）。读接口要分「匿名可用」与「需要权限」两类 |
| 用户对象的 `login` | 7.2 通用字段表列出 `login`，但单用户示例没写它，未明确区分不同路由的字段集合 | `users_list` 与详情里的嵌套用户有 `login`，`user_show` 的样本没有；这是需要补充的路由差异，不应把通用字段表当必有字段表 |
| 原图地址的扩展名描述 | 15.7 写「`ext` 带点，再自己加点会拼出 `.png.png`」 | **描述错误**：`ext` 已经带点（`.png`），再补一个点得到的是 `md5..png`，不是重复扩展名。公式照 `{md5}{ext}` 拼即可，本轮**没有**请求过 `oimages` 验证 |
| 帖子列表字段清单 | 5.1 未列 `exclusive_tag` | `search_tag=hatsune miku` 的响应多出完整标签对象 `exclusive_tag`（id 407），其中 `description_en` 是 HTML；`tags_list` 同一标签的该字段是 BBcode。出现条件与渲染规则未实测，不把这两种形态强行统一 |

数据快照差异（**不是契约错误**）：标签 407 的 `tag_ru` 本轮是小写 `хацунэ мику`，
`num_pub=21988`、`views=93150`（输入为 22686、0）；帖子 929452 的 `score_number/download_count`
本轮为 6/40（输入为 5/31），929492 的 `download_count` 为 30（输入为 22）。
时间区间 `ldate=5` 的计数为 28743，而输入为 28760。它们只是不同时间的样本，不能据此断定规则变化。

## 未实测集中清单

**这一节集中放输入文档（T）候选、本轮 90 个请求没有测到的说法**；正文结论不依赖它们。
已经被参数轮覆盖的默认值与取值不在这里，见[参数实测](#参数实测第二轮-69-次)。

* **仍未发的参数**：`posts_list(lang=…)` 的效果（输入文档称无效）、
  「含空格的标签不编码时参数被静默丢弃、返回全库且不报错」（本轮两次带空格搜索都用了 `+` 编码，
  **没有**故意送未编码空格）、输入文档列的其它「被忽略参数名」（`min_width`、`min_height`、
  `min_size`、`min_score`、`keyword`、`tags`、`tag`、`author`、`date`、`rating`、`erotics`、`ids`、
  `user_id`、`juser_id`、`token`、`ltext`、`no_previews` …）——本轮只证 `tags_list` 的 `search`
  与 `posts_list` 的 `order=asc/desc` 这两组不生效，**不要推广**。
* **越界枚举值**：`ldate` 只测到 `0`～`8`（`8` 与 `0` 相同），`9`、更大值与负数没有样本；
  `posts_per_page` 只抽测了 `1`/`2`/`3`/`100`/`101`/`150`/`1000`/`0`/`-1`，没有穷举 1～100。
* **`search_tag` 的语义**：多标签是 AND 只是输入文档说法，本轮只证组合查询能返回结果；
  `type` 类别的 0～7 名称（站点只返回整数，样本里 `type=7` 的标签名与输入文档的「物品」例子不同）、
  `aspect` 匹配的容差（`16:9` 的样本不是严格等比）都未定性。
* **`post_comments` 的分页**：本轮只证该信封没有 `offset`/`limit`/`count`，也**没有**测过给它传
  `limit`/`offset`/`page`，所以不能断言分页参数无效。
* **`post_tags` 的成功形态**：只有匿名 `403` 一个样本。
* **`post_create` 与凭据**：POST 一次都没发；请求体结构、`Idempotency-Key` 的效果、
  `Authorization` 的方案（`Bearer` 还是裸 token）、Cookie 名与登录换取凭据的端点全部未知；
  输入文档候选只有「匿名 `401 {"errormsg":"You have no rights","success":false}`」。
  所有写动词（`PUT`/`PATCH`/`DELETE`）与任何带凭据的成功响应也没有样本。
* **媒体**：`opreviews` / `oimages` 地址公式、`_sp` 的 `.png` 变体、`_cp`/`_bp`/`_lp` 只有 `.avif`、
  详情不给的 `_lp` 档、`oimages` 匿名 `302`、`image_get` 成功返回的字节——**本轮零 CDN 请求**；
  实测过的媒体地址只有 `post_show` 返回的三个预览 URL 字符串本身。
* **`type` 的其它取值**：服务端在 `type=json` 的 400 里提到 `json_v3`/`json1`/`xml`，
  本轮**没有请求**那三种格式，不承诺默认（JSON）客户端能解析 XML，也不加新格式方法。
* **`exclusive_tag` 的出现条件**：只有 `search_tag=hatsune miku` 一个样本带这个键，
  多标签搜索与不存在的标签都没有；什么条件下出现未实测。
* **字段语义**：`datetime` 与 `pubtime` 的区别、`tied`、`artefacts_degree`、`smooth_degree`、
  `alias` 恒 `null`、`gender` 的 `1`/`2`、`description_en` 在 `exclusive_tag` 里是 HTML、
  `source.verification` 的取值集合——都未知。
* **头像 URL**：输入文档里旧客户端的 `avatars/…` 路径**未实测**，本库不拼。
* **旧版 web 路由与 302**：`/login/submit`、`/pictures/vote`、`/pictures/autocomplete_tag`、
  `/pictures/add_comment/{id}`、`/pictures/view_post/{id}?type=json`、`/api/v2/posts/{id}/comments`
  在 API 主机上的行为、web 主机 `/api/v3/*` 的 `302`：本轮没有请求，按「不封装、不建议用」处理。
* **`OPTIONS` 预检与限流**：CORS 允许的头 / 动词都只有输入文档说法（本轮没有发 `OPTIONS`）；
  没有观察到限流响应头，也不排除密集请求被前置层断连（输入文档的说法），本轮未复现。

## 本轮请求覆盖

| 面 | 覆盖情况 |
| :--- | :--- |
| `service_info`（`GET /`） | 1 次，`200` |
| `posts_list`（`GET /posts`） | **51 次**（首轮 2 + 参数轮 49）：`200`×47（含越界页空数组）、`400`×3（缺 `page`、`page=abc`、`type=json`）、`500`×1（`page=-1`） |
| `post_show`（`GET /posts/{id}`） | 3 次：`929452` → `200`；`999999999` → `410`；`top` → `400` 纯文本 |
| `post_comments` | 1 次（`382872`），`200` |
| `post_tags` | 1 次（`929452`），**`403`** |
| `tags_list`（`GET /tags`） | **15 次**（首轮 4 + 参数轮 11），全部 `200` |
| `tag_show` | 2 次：`407` → `200`；`999999999` → `404` |
| `users_list` | **4 次**（首轮 1 + 参数轮 3），全部 `200` |
| `user_show` | 2 次：`294066` → `200`；`999999999` → `404` |
| `comments_list` | **4 次**（首轮 1 + 参数轮 3），全部 `200` |
| `comment_show` | 2 次：`174693` → `200`；`999999999` → `404` |
| `image_get` | 1 次（真实 `file_url`），**`403` 空正文** |
| 旧版 / 未知路由 | 3 次（`/api/v2/comments`、`/pictures/view_posts/0?type=json`、`/api/v3/not_a_route`），都是 **`404` 空正文** |
| `POST` | **0 次** |
| 媒体 CDN（`opreviews` / `oimages`） | **0 次** |
| Web 主机与其它旧版路由 | **0 次** |

合计 **90 次匿名 `GET`**：状态 `200`×76、`400`×4、`403`×2、`404`×6、`410`×1、`500`×1；
正文格式 `application/json`×85、`text/plain; charset=utf-8`×1、无 `Content-Type`×4（`image_get` 的 403
与 3 条空正文 404）。随后真跑的用法路径（轻量冒烟与两个示例）的请求数、命令与输出摘要记录在
[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)，本页不重复列；它们覆盖的是用法路径，
不等于 13 个方法逐一验证。

本轮**没有**跑到：任何 `POST`、任何带凭据的成功响应、`post_tags` 的成功形态、
`image_get` 的成功字节、任何 CDN 请求、`OPTIONS` 预检、任何媒体字节。

## 客户端取舍

1. **13 条路由一条不多一条不少**：11 条读路由沿用站点路由，加 `image_get()` 与 `post_create()`；
   `post_create` 保留为最小写入口，请求体完全由调用方给 dict，库不编字段名。
2. **JSON 原样交付**：不拆信封、不改字段名、不转换类型、不合并分页，`post_show` 的多段对象也不套壳；
   `max_pages`、`posts_count`、`score` 这些字段照服务端原值给，**不本地重算、不覆盖**。
3. **凭据显式、原样**：`authorization` / `cookie` 空默认；非空时按原值送头，不添加 `Bearer`、
   不猜 Cookie 名、不登录、不刷新，也不提供登录 / 注册方法。
4. **路径语义固定**：`urljoin(site_url + '/', path)`——不带前导 `/` 是相对 API 基址，
   带前导 `/` 是主机根；这跟其它家族不一样，文档写清，代码里也不替调用方补斜杠。
5. **媒体只给地址**：唯一的字节例外是 `image_get()`，它按 URL 原样取回正文（不解析、不嗅探、不写磁盘）；
   CDN 地址只当文本，本库不拼、不下载。
6. **不做客户端兜底**：不重试、不钳位、不做本地参数校验、不猜上限、不为空结果换路由，
   错误保持原状态码与正文（含 `text/plain` 与空正文的那种）。
7. **`POST` 只接调用方 dict**：`data` 原样作为 JSON 正文、`idempotency_key` 原样作为
   `Idempotency-Key` 头；未知字段一律不造。

继续阅读：[客户端用法](anime-pictures.md) · [方法参考](anime-pictures-api.md) ·
[能力入口](anime-pictures-capabilities.md) · [验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。
