# Anime-Pictures 方法参考

Anime-Pictures（`anime-pictures.net`）是自研后端的插画站：路由与返回形状都不是 Danbooru / Moebooru 那一套。
非法路径段会返回含 `i32` 的纯文本错误；仅凭文案不能验证后端实现语言。
**没有可读到的官方 API 页面**（手册页 `/pages/api` 存在，但整站被 Cloudflare 质询挡下）、**没有 OpenAPI、
也没有可引用的服务端源码**：本页的公开结论只来自本轮对 `https://api.anime-pictures.net/api/v3` 的
**90 次匿名只读 `GET`**（首轮路由与字段 21 次，参数取值 69 次，都标 **L**）以及随后真跑的用法路径。
接入时收到的《Anime-Pictures 接口文档（综合版）》
只作候选，未被 L 支持的参数默认值、枚举与上限集中在[边界与未实测](#边界与未实测)，不当契约写。

本页列出 `AnimePictures` 的全部 **13 个原生方法**：**12 个 `GET`**（服务信息 1、帖子 4、标签 2、用户 2、
评论 2，这 11 条读路由，加原图入口 `image_get()`）与 **1 个 `POST`**（`post_create`，本轮**没有发过任何 POST**），
另有通用入口 `request(method, path, *, params=None, data=None, headers=None)`；**只有 `image_get()` 返回字节**，
其余方法的地址字段都是文本。客户端怎么构造、`last_call` 怎么看、媒体地址怎么拼见
[客户端用法](anime-pictures.md)；「想做什么 → 用哪个方法」见[能力入口](anime-pictures-capabilities.md)；
依据出处、权限与排除项见[依据与差异](anime-pictures-contract-notes.md)；执行记录见
[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。

## 依据标注与阅读方式

| 标记 | 来源 | 能说明什么 |
| :--- | :--- | :--- |
| **L** | 本轮 90 次直接 HTTP 观察（首轮 21 次 + 参数轮 69 次；串行、相邻 ≥1.2 秒、不重试、不跟随跳转、不下载媒体） | 对应路由的状态、`Content-Type`、信封与字段，以及参数取值与默认值；**不等于每个 Python 方法都执行过** |
| **未实测** | 输入文档声称、本轮没有请求或没有复现 | 参数取值、默认值、上限、枚举、POST 与凭据、媒体行为；**不作为契约** |

90 个响应的格式分布：**85 个 `application/json`**、1 个 `text/plain; charset=utf-8`
（`GET /api/v3/posts/top` 的 400）、4 个**没有任何 `Content-Type`**（`GET /pictures/get_image/…` 的 403 空正文，
以及 3 条路由不存在的 404 空正文）。状态分布 `200`×76、`400`×4、`403`×2、`404`×6、`410`×1、`500`×1。
本页只写 L 支持的事实；未知项与输入文档的矛盾分别集中在
[实测与输入文档的矛盾](anime-pictures-contract-notes.md#实测与输入文档的矛盾)与本文末尾的
[边界与未实测](#边界与未实测)。

## 通用约定

* **基地址**：`https://api.anime-pictures.net/api/v3`，来自包内配置 `sites.anime_pictures.url`。
  除 `service_info()` 与 `image_get()` 之外，本页路由都接在它后面。
* **路径语义（与其它家族有意不同，务必看清）**：`request()` 用 `urljoin(self.site_url + '/', path)` 拼地址——
  **不带前导 `/`** 的路径是相对 API 基址（`'posts'` → `…/api/v3/posts`），
  **带前导 `/`** 的路径按**主机根**解析（`'/api/v3/posts'` 与 `'posts'` 落到同一个地址；
  `'/'` → `https://api.anime-pictures.net/`；`'/pictures/get_image/…'` → 主机根下的 `/pictures/…`）。
  所以 `service_info()` 用 `'/'`、`image_get()` 用 `'/pictures/get_image/{…}'`，其余方法用不带前导斜杠的路由。
* **方法**：12 个原生方法发 `GET`，只有 `post_create` 发 `POST`。
* **认证**：包内配置的 `authorization` / `cookie` 为空串；构造参数 `None` 读配置，显式空串保持匿名。非空时**按原值**送
  `Authorization` / `Cookie` 头：不添加 `Bearer`、不猜 Cookie 名、不登录、不刷新令牌、不发明登录接口。
  本轮 90 次请求全部匿名，**没有任何带凭据的成功样本**。
* **参数编码**：`params` 走共享层（Rails 风格）——`None` 值不发送、布尔写成小写 `true`/`false`、
  嵌套字典写成 `key[child]`、序列写成重复 `key[]`。库**不做本地校验、不钳位、不补默认值、不猜上限**；
  没在下面参数表里的参数名也会原样进查询串。
* **返回**：JSON 原样返回，不拆信封、不改字段名、不转换类型。2xx 正文为空 → `None`；
  2xx 但正文不是 JSON → `AnybooruAPIError`；非 2xx → `AnybooruHTTPError`（带
  `http_code` / `url` / `body` / `data`，正文不是 JSON 时 `data` 为 `None`）。
  库不重试、不降级；共享 requests 会话默认跟随跳转，本轮探测、冒烟与示例都显式关闭了跳转。
  `client.last_call` 保留 `API`、`url`、`status_code`、`status`、`headers`。
* **响应头**：`post_show` 样本带 `vary: Cookie, Authorization`；登录后内容是否不同未实测。
  JSON 响应都带 `access-control-allow-origin: https://anime-pictures.net` 与
  `access-control-allow-credentials: true`。本轮没观察到任何限流响应头。
* **资源编号**：进路径的编号用 `quote(str(id), safe='')` 编码；库不校验合法性，
  服务端怎么回就怎么抛（非整数路径段是 `text/plain` 的 400，见下）。
* **媒体**：本库只有 `image_get()` 返回字节；`small_preview` / `medium_preview` / `big_preview`
  与 `file_url` 都只是文本。CDN（`opreviews` / `oimages`）本轮**一次都没请求**。

## 通用入口 `request()`

签名：`request(method, path, *, params=None, data=None, headers=None)`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串，大写；13 个原生方法发 `'GET'` 或 `'POST'` | 必填（Python 报缺参） | `client.request('GET', 'posts')` |
| `path` | 路径，语义见上：`'posts'` 相对 API 基址，`'/'` 是主机根 | 必填 | `client.request('GET', 'tags/407')` |
| `params` | 查询参数字典，经共享层编码后拼进查询串 | `None`，不发查询参数 | `client.request('GET', 'posts', params={'page': 0, 'posts_per_page': 2})` |
| `data` | 调用方给的 dict 原样写进 requests 的 `json` 参数；其中 `None` 序列化成 JSON `null`，不清理、不改名、不补字段 | `None`，不发请求体 | `client.request('POST', 'posts', data=data)`；自备正文见下方未执行的 `post_create` 示例 |
| `headers` | 额外请求头字典，**覆盖**同名实例凭据头，只作用于本次请求 | `None`，只带默认头与凭据头 | `client.request('GET', 'posts', headers={'Cookie': '调用方自己的凭据'})` |

`last_call['API']` 保留交给共享层的路径原文，不去掉前导 `/`；根路径对应 `'/'`。

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    root = client.request('GET', '/')
    # GET https://api.anime-pictures.net/
    # L：200 application/json，{"message": "Hello, World!"}
    print(root['message'])

    page = client.request('GET', 'posts', params={'page': 0, 'posts_per_page': 2})
    # GET https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2
    # L：200，信封 posts_per_page 2 / response_posts_count 2 / page_number 0 /
    #     posts_count 667906 / max_pages 333952
    print(client.last_call['status_code'], client.last_call['url'])
    print(page['page_number'], [post['id'] for post in page['posts']])
```

`'/'` 与 `'/api/v3/posts'` 这两种写法都要记住：前者是主机根，后者与相对写法 `'posts'` 等价。
下面 13 个方法把常用路由各自包好，需要别的路径时再用这个入口。

## 服务信息（1 个方法）

### service_info

签名：`service_info()`。路由：`GET /`（**主机根**，不在 API 基址下）。

无参数。

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    hello = client.service_info()
    # GET https://api.anime-pictures.net/
    # L：200 application/json，{"message": "Hello, World!"}（唯一键，str）
    print(hello['message'])
```

L：正文只有 `message` 一个键，值 `"Hello, World!"`；不含版本号、配额或站点统计。

## 帖子（4 个 `GET` + 1 个 `POST`）

### posts_list

签名：`posts_list(**params)`。路由：`GET /api/v3/posts`。返回**列表信封**（键见下）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | 0 起步的整数 | 页码 | **L：必填**。不传、或传非整数（`page=abc`）→ 400 `{"errormsg":"Missing or invalid \`page\` parameter","success":false}`；`page=-1` → 500 `{"errormsg":"Internal server error","success":false}`；越界（`page=999999&posts_per_page=100`）→ 200，`response_posts_count` 0、`posts` 空数组，`posts_count` 与 `max_pages` 仍是全量值 | `page=0` |
| `posts_per_page` | 整数；输入建议 1～100，本轮只抽测部分值 | 请求每页条数，**不是返回条数的硬保证** | **L：缺省 80**。`1`/`2`/`3`/`100` 回显对应值；`101`/`150`/`1000`/`0` 回 60；`-1` 回 80。区间内其它值与其它负数未实测 | `posts_per_page=2` |
| `search_tag` | 标签名；多个标签用空格分隔，整段要 URL 编码（`+` 或 `%20`） | 输入文档称是 AND（要同时带这些标签）；本轮只证「组合查询能返回结果」（`long hair blue eyes` → 146065），**没有逐帖验标签**，AND 语义仍算候选 | **L：不传不过滤**。`hatsune miku` → `posts_count` 21008、`zzzznotexist` → 0；命中时信封可能多出 `exclusive_tag`（见下）。本轮**没有**故意发未编码的空格，输入文档「未编码就被静默丢弃」未复测 | `search_tag='hatsune miku'` |
| `denied_tags` | 单个标签名 | 排除带该标签的帖子 | **L：不传不过滤**。`long hair` → 269346、`blue eyes` → 510020；空格连接两个标签的整串 `long hair blue eyes` → 667906（**没排除**，被当成一个不存在的标签名）；重复同名参数 `denied_tags=long hair&denied_tags=blue eyes` → 510020（**后者生效**）。注意：共享层把 Python 列表编码成 `denied_tags[]=…`，**与重复同名参数不是一回事**，服务端对 `denied_tags[]` 的行为未实测——要发重复同名参数请自己拼查询串走 `request()` | `denied_tags='long hair'` |
| `order_by` | `date` / `date_r` / `rating` / `views` / `size` / `tag_num` / `id` | 排序字段，见下表 | **L：不传时前三 ID 与 `date` 相同**；`random` 这一个未知值也得到同样前三 ID，不能外推所有未知值 | `order_by='rating'` |
| `ldate` | `0`～`7` 的区间枚举；另测了 `8` | 时间过滤，不按天数直接解释，见下表 | **L：不传与 `0` 的总数一致**；`8` 与 `0` 最旧 ID 和总数相同 | `ldate=1` |
| `aspect` | `宽:高`，如 `16:9`、`1:1` | 只返回该画幅的帖子 | **L：不传不过滤**。`16:9` → 37502、`1:1` → 18296。注意 `16:9` 的样本里出现 7017×3947、5500×3094 → **不是严格有理等比**，匹配容差未实测 | `aspect='16:9'` |
| `color` | 6 位十六进制，带不带 `#` 都行 | 只返回主色调相近的帖子 | **L：不传不过滤**。`FF0000` 与 `%23FF0000` 都是 1645 | `color='FF0000'` |
| `ext_jpg` / `ext_png` / `ext_gif` | 字符串；本轮取值为 `jpg` / `png` / `gif` / `yes` | 扩展名过滤，可组合 | **L：不传不过滤**。`ext_jpg=jpg` → 470199、`ext_png=png` → 196121、`ext_gif=gif` → 1586；`ext_jpg=yes&ext_png=yes` → 666320。未证明所有非空值都启用 | `ext_png='png'` |
| `user` | 用户 id | 只返回该用户上传的帖子 | **L：不传不过滤**。`user=204183` → 30757 | `user=204183` |
| `stars_by` | 用户 id | 只返回该用户收藏的帖子 | **L：不传不过滤**。`stars_by=13734` → 41519 | `stars_by=13734` |
| `order` | — | **L：对 `order_by=rating` 没有影响**：`order_by=rating&order=asc` 与 `order_by=rating&order=desc` 的前三 id 跟不带 `order` 完全相同。本轮只测了这一组组合，**不要断言所有 `order` 取值都不存在** | — | `order='asc'`（在这一组里不生效） |
| `lang` | `en` / `ru` / `ja` / `zh-cn` 等 | 输入文档称对读接口没有观察到的效果 | **未实测**（本轮没发过这个参数） | `lang='en'` |
| `type` | — | 旧版 web 路由的参数 | **L：`type=json` → 400** `{"errormsg":"Only json_v3, json1, and xml response types are supported","success":false}`（服务端提到 `json_v3`/`json1`/`xml`，本轮**只发了 `json` 这一个值**，那三种没有请求） | `type='json'`（预期 400） |
| `**params` | 其它名字原样进查询串 | 客户端不识别参数名 | 未列出的参数行为未实测；`lang` 也未请求 | — |

**信封字段**（L）：

| 字段 | 类型 | 含义与本轮值 |
| :--- | :--- | :--- |
| `posts` | array | 帖子对象数组。**列表项不含预览图地址**（本轮所有列表样本都没有 `small_preview` / `medium_preview` / `big_preview`） |
| `posts_per_page` | int | 服务端实际使用的每页条数（可能与请求值不同，见参数表） |
| `response_posts_count` | int | 本次真正返回的条数（末页会小于 `posts_per_page`；`page=999999` 时是 0） |
| `page_number` | int | 回显请求的页码（本轮 0 / 1 / 999999） |
| `posts_count` | int | 当前条件下的**总帖子数**（不带过滤时 667906；带过滤时变小） |
| `max_pages` | int | 最后一个可用页码（0 起步；`posts_per_page=2` 时 333952、`100` 时 6679、`1` 时 667905）。**空结果时是 0**：`search_tag=zzzznotexist` → `posts_count` 0、`posts` `[]`、`max_pages` **0**（不是 `-1`）。输入文档的 `ceil(posts_count / posts_per_page) - 1` 在有结果时吻合，但**不能无条件用**；本库不替调用方重算 |
| `exclusive_tag` | object | **只在 `search_tag` 命中的那一次出现过**：`search_tag=hatsune miku` 的响应顶层多出一个完整标签对象（id 407），其余 `search_tag` 取值都没有这个键。该对象的 `description_en` 是 HTML（`<b>Hatsune Miku</b>`），而 `tags_list` 里同一标签的 `description_en` 是站点 BBcode（`[b]…[/b]`）——**同一个字段两种渲染形态**。何时出现、是否只在单标签精确命中时出现，未实测 |

L：`page=0` 返回 id `929492`、`929491`；`page=1` 返回 id `929490`、`929489`。

#### 排序（`order_by`，L）

`page=0&posts_per_page=3` 的实测前三名：

| `order_by` | 排序依据（由本轮字段值看出） | 本轮前三 id |
| :--- | :--- | :--- |
| `date`（默认） | `pubtime` 倒序 | `929492`、`929491`、`929490` |
| `date_r` | `pubtime` 正序 | `2`、`3`、`5`（`pubtime` 2009-10-11） |
| `rating` | `score_number` 倒序（629 / 525 / 442） | `301063`、`423454`、`602864` |
| `views` | `download_count` 倒序（706939 / 421712 / 117589） | `88793`、`304173`、`45264` |
| `size` | `size` 倒序（127208144 / 91388385 / 79005698） | `34056`、`43659`、`45028` |
| `tag_num` | `tags_count` 倒序（766 / 664 / 662） | `581823`、`266625`、`264140` |
| `id` | `id` 正序（**不是时间序**：id `1` 的 `pubtime` 是 2011-11，id `2` 是 2009-10） | `1`、`2`、`3` |
| `random`（仅此未知值已测） | 与 `date` 的前三 ID 相同 | `929492`、`929491`、`929490` |

本轮只证 `date_r` 一个反序取值；`rating_r` 之类的其它 `_r` 后缀**没有样本**，不要照名字推断它们存在。

#### 时间区间（`ldate`，L）

`page=0&posts_per_page=1&order_by=date_r&ldate=…`，取区间内**最旧**一条的 `pubtime`：

| `ldate` | 本轮最旧 `pubtime` | 本轮 `posts_count` | 输入文档给的区间名（**推断**，站点不返回名称） |
| :--- | :--- | :--- | :--- |
| `0`（默认） | `2009-10-11T02:01:54` | 667906 | 不限 |
| `1` | `2026-09-12T19:20:29` | 411 | 最近一周 |
| `2` | `2026-08-20T19:18:12` | 1879 | 最近一月 |
| `3` | `2026-09-18T14:00:06` | 57 | 最近一天 |
| `4` | `2026-03-20T16:19:51` | 11286 | 半年 |
| `5` | `2025-09-19T13:46:45` | 28743 | 一年 |
| `6` | `2024-09-19T21:35:09` | 61654 | 两年 |
| `7` | `2023-09-20T20:10:45` | 84306 | 三年 |
| `8` | `2009-10-11T02:01:54` | 667906 | 与 `0` 相同（回落） |

区间名是输入文档的推断（站点只返回整数）；上表里**可当契约的**是「`ldate` 是预置区间枚举、`8` 回落到 `0`
的行为、以及各取值命中的最旧 `pubtime`」，具体日期与计数每天都在变。

**帖子对象**（字段与类型来自 L；未由响应直接说明的业务含义仍是输入资料解释，不能当服务端定义）：

| 字段 | 类型与本轮示例 | 含义 |
| :--- | :--- | :--- |
| `id` | int `929492` | 帖子编号 |
| `md5` | str `"0f04fddedd428aae0e3c25c2e62a2812"` | 文件 md5（拼媒体地址用） |
| `md5_pixels` | str `"25e48d820fdad25fd8b27bef13726e92"` | 像素数据 md5，与文件 md5 不同 |
| `juser_id` | int `257203` | 上传者用户 id |
| `width` / `height` | int `5760` / `2400` | 原图像素尺寸 |
| `pubtime` | str `"2026-09-19T11:32:13.156038"` | 入库 / 上架时间 |
| `datetime` | str `"2026-09-08T20:05:34.082710"` | 另一个时间字段，站点没有说明，含义未实测 |
| `score` | float `0.0`、`73.0`、`1446.0` | L：id 2 的 `score=73.0`、`score_number=70`；id 301063 是 `1446.0` / `629`。输入「恒为 0.0」被推翻；两字段不同，`score` 的计算方式未实测 |
| `score_number` | int `8` | 得分 / 票数 |
| `size` | int `8828082` | 文件字节数 |
| `download_count` | int `30` | 下载次数 |
| `erotics` | int `1` | 是否 R18（本轮样本 `0` / `1`） |
| `color` | array `[152, 128, 124]` | 主色 RGB，三个整数 |
| `ext` | str `".png"` | 扩展名，**带点**；样本还含 `.jpg`、`.jpeg`、`.gif`，不是穷尽枚举 |
| `status` | int `1` | 本轮样本是 1，不构成恒定保证；其它值含义未实测 |
| `status_type` | int `0`，也可能不出现 | 反序列表中的 id 2、3、5 均无此键；不要假设一定存在 |
| `spoiler` | bool `false` | 剧透标记 |
| `have_alpha` | bool `true` | 原图是否带透明通道 |
| `tags_count` | int `61` | 标签数 |
| `artefacts_degree` | float `7.662280773497636` | 压缩伪影指标，站点没有说明 |
| `smooth_degree` | float `30.38158800281947` | 平滑度指标，站点没有说明 |

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    first_page = client.posts_list(page=0, posts_per_page=2)
    # GET https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2
    # L：200，posts_count 667906、max_pages 333952、page_number 0，posts 2 条
    print(first_page['posts_count'], first_page['max_pages'])
    for post in first_page['posts']:
        print(post['id'], post['ext'], post['score_number'], post['tags_count'], post['md5'])

    second_page = client.posts_list(page=1, posts_per_page=2)
    # GET https://api.anime-pictures.net/api/v3/posts?page=1&posts_per_page=2
    # L：200，page_number 1，posts 的 id 是 929490、929489（与第一页不重叠）
    print([post['id'] for post in second_page['posts']])

    tagged = client.posts_list(page=0, posts_per_page=2, search_tag='hatsune miku')
    # GET https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2&search_tag=hatsune+miku
    # L：200，posts_count 21008、max_pages 10503；这一条响应顶层还多出 exclusive_tag（标签 407）
    print(tagged['posts_count'], tagged['max_pages'], tagged['exclusive_tag']['id'])

    top_rated = client.posts_list(page=0, posts_per_page=3, order_by='rating')
    # GET https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=3&order_by=rating
    # L：200，前三 id 是 301063、423454、602864，score_number 依次 629、525、442
    print([(post['id'], post['score_number']) for post in top_rated['posts']])
```

`posts_list` 的 `page` 必填（缺了直接 400），`posts_per_page=101` 之类会被服务端改写成 60，
所以**别用请求值反推返回条数**；翻页看 `page_number` 与 `response_posts_count`。
列表项**不带**预览地址，要出图得自己按 [媒体地址](#媒体地址只是文本未实测) 拼。

### post_show

签名：`post_show(post_id, **params)`。路由：`GET /api/v3/posts/{post_id}`。返回一个**多段对象**，不是信封。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | 整数（或可转成整数的值） | 帖子编号，进 URL 路径 | 必填；非整数路径段得到 400 纯文本 | `post_show(929452)` |
| `**params` | 本轮没有可识别参数 | — | 本轮探测的 `post_show` 请求都没带查询参数 | `post_show(929452)` |

顶层键（L：**本轮 `929452` 这一个样本**有下面 9 个；**不是每个帖子的详情都同形**）：

| 字段 | 类型与本轮值 | 含义 |
| :--- | :--- | :--- |
| `post` | object | 帖子对象，字段与列表项同，**额外多出** `small_preview` / `medium_preview` / `big_preview` 三个地址（本轮分别是 `…_sp.avif` / `…_cp.avif` / `…_bp.avif`） |
| `source` | object `{"kind": "external", "url": "https://danbooru.donmai.us/posts/12151917", "verification": "moderator_confirmed"}` | 来源：`kind`、原作者链接、`verification` |
| `user` | object | 上传者，用户对象（本轮 `id` 294066、`name`/`login` `"Nekomina"`、`gender` `null`） |
| `moderator` | object | 审核者，用户对象（本轮 `id` 204183、`login` `"cold_crime"`、`groups` `["user", "moderator"]`）；输入文档称可能为 `null`，本轮没有 `null` 样本 |
| `tags` | array | 每项 `{tag, user, relation}`：`tag` 是标签对象，`user` 是把标签关联到本帖的人，`relation` 是 `{id, addtime, user_id}`（本轮 `id` 28258758、`addtime` `"2026-09-08T12:51:02.674949"`） |
| `file_url` | str | 原图下载用的**文件名**（不是地址），含空格，给 `image_get()` 当路径段；本轮 `"929452-3550x2344-azur lane-illustrious (azur lane)-illustrious (wandering glow of midnight) (azur lane)-single-long hair-looking at viewer.png"` |
| `star_it` | bool | 当前登录用户是否已收藏；匿名样本 `false` |
| `favorites_users` | array | 每项 `{favorite, user}`；本轮 `favorite` 是 `{post, juser_id, addtime, folder}`（`folder` 值 `"Azur Lane"`），`user` 是用户对象 |
| `tied` | array | 本轮样本是空数组 `[]`，站点没有说明 |

**顶层键集合不固定**：另一个帖子 `post_show(382872)` 的响应里**没有 `source` 键**（真实执行时读
`detail['source']` 直接 `KeyError`），所以输入文档说的「顶层键固定为这 9 个」不成立；
取 `moderator` / `source` / `favorites_users` / `tied` 这些键之前先判断它在不在，
不要用默认值或兜底逻辑掩盖缺失。

错误路径（L）：`post_show(999999999)` → **410** `{"errormsg":"Post not found","success":false}`；
`post_show('top')` → **400 `text/plain; charset=utf-8`**，正文 `` Invalid URL: Cannot parse `top` to a `i32` ``，
此时 `AnybooruHTTPError.data` 是 `None`、`.body` 是这段纯文本，`last_call` 记的是这个 URL 与状态。

```python
from anybooru import AnybooruHTTPError, AnimePictures

with AnimePictures('anime_pictures') as client:
    detail = client.post_show(929452)
    # GET https://api.anime-pictures.net/api/v3/posts/929452
    # L：200，这个样本顶层 9 键；post.tags_count 38、post.ext ".png"、source.kind "external"、
    #     user.login "Nekomina"、tags 38 项、star_it false、tied []
    print(detail['post']['id'], detail['user']['id'], detail['source']['url'])
    # 929452 这个样本有 source；别的帖子不一定有（382872 就没有，直接读会 KeyError）
    print(detail['post']['small_preview'], detail['file_url'])
    for item in detail['tags'][:2]:
        print(item['tag']['tag'], item['relation']['addtime'])

    try:
        client.post_show(999999999)
    except AnybooruHTTPError as error:
        print(error.http_code, error.data)
        # L：410 {'errormsg': 'Post not found', 'success': False}

    try:
        client.post_show('top')
    except AnybooruHTTPError as error:
        print(error.http_code, repr(error.body), error.data)
        # L：400 'Invalid URL: Cannot parse `top` to a `i32`' None
        print(client.last_call['status_code'], client.last_call['url'])
```

### post_comments

签名：`post_comments(post_id, **params)`。路由：`GET /api/v3/posts/{post_id}/comments`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | 整数 | 帖子编号，进 URL 路径 | 必填 | `post_comments(382872)` |
| `**params` | 本轮没有可识别参数 | — | L 只发过不带额外参数的请求 | `post_comments(382872)` |

L：200，信封只有两个键：`{"success": true, "comments": […]}`，**没有 `offset` / `limit` / `count`**。
本轮该帖返回 1 条评论，每条是 `{comment, user}`（**没有 `post` 段**）：

| 字段 | 类型与本轮值 |
| :--- | :--- |
| `comments[].comment` | object，评论对象（`id` 174693、`datetime` `"2026-09-19T09:13:46.230319"`、`language` `"en"`、`text`、`html`） |
| `comments[].user` | object，评论者，用户对象（`id` 290656、`login` `"FikriHarjantoKesumo"`） |

**不能**由「没有分页信封」推断分页参数一定无效：本轮没有测过给这个路由传 `limit` / `offset` / `page`。

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    comments = client.post_comments(382872)
    # GET https://api.anime-pictures.net/api/v3/posts/382872/comments
    # L：200 {"success": true, "comments": [{"comment": {...}, "user": {...}}]}，1 条
    print(comments['success'], len(comments['comments']))
    for item in comments['comments']:
        print(item['comment']['id'], item['comment']['language'], item['user']['id'])
```

### post_tags

签名：`post_tags(post_id, **params)`。路由：`GET /api/v3/posts/{post_id}/tags`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | 整数 | 帖子编号，进 URL 路径 | 必填 | `post_tags(929452)` |
| `**params` | 本轮没有可识别参数 | — | L 只发过不带额外参数的请求 | `post_tags(929452)` |

L：**匿名 403** `{"errormsg":"You not have rights","success":false}`（`application/json`）。
**成功形态本轮没有任何样本**；带非空凭据后是否可用也未实测。帖子的标签已经包含在 `post_show()` 的 `tags` 里，
一般不需要这个路由。

```python
from anybooru import AnybooruHTTPError, AnimePictures

with AnimePictures('anime_pictures') as client:
    try:
        client.post_tags(929452)
    except AnybooruHTTPError as error:
        print(error.http_code, error.data)
        # L 匿名：403 {'errormsg': 'You not have rights', 'success': False}
```

### post_create

签名：`post_create(data, *, idempotency_key=None)`。路由：`POST /api/v3/posts`。
**本方法本轮没有执行过**：本轮只授权匿名读取，没有发任何写请求。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `data` | 调用方自己的 dict | 原样作为 JSON 正文；未知字段不补全、不清理，`None` 序列化成 `null` | 必填 | 从你自行准备的 JSON 文件读出 dict，见下方示例 |
| `idempotency_key` | 字符串，或 `None` | 非 `None` 时作为 `Idempotency-Key` 请求头发送 | `None`，不发这个头 | `idempotency_key='…'` |

**未实测**：请求体结构、成功状态码与返回体、凭据怎么带（输入文档只提到 CORS 允许 `authorization` 头，
没有验证过 `Bearer` 还是裸 token）。输入文档候选：匿名 `POST /api/v3/posts` → `401`
`{"errormsg":"You have no rights","success":false}`。下面片段**没有执行**，只示范形状：

下面需要先自行准备符合站点要求的 `post-payload.json` 与凭据；该文件不是本库提供的正文模板。
无法给出可工作的字段字面示例，因为请求体结构未实测。以下只展示如何传入已有 dict，**不要作为匿名冒烟运行**。

```python
import json
from anybooru import AnimePictures

with open('post-payload.json', encoding='utf-8') as payload_file:
    data = json.load(payload_file)

with AnimePictures('anime_pictures', authorization='<调用方已有的完整凭据>') as client:
    created = client.post_create(data, idempotency_key='my-post-submission-001')
    # POST https://api.anime-pictures.net/api/v3/posts；未执行、成功响应未知
    print(created)
```

## 标签（2 个方法）

### tags_list

签名：`tags_list(**params)`。路由：`GET /api/v3/tags`。返回列表信封。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | 正整数；仅抽测 2、1000 与缺省 | 每页条数 | **L：默认 20**；`1000` 回显 100 并给 100 项。其它越界值未实测，不由单例保证硬上限 | `limit=2` |
| `offset` | ≥0 的整数 | 跳过条数 | **L：默认 0**；`offset=2` 回显 2 并跳过前 2 项 | `offset=0` |
| `type` | 整数（本轮 `0`～`7` 命中非空，`8` 返回空集合） | 标签类别整数（API 不返回类别名，含义见下表） | **L：不传不过滤**（`count` 156541） | `type=1` |
| `tag` | 标签全名 | **精确匹配**一个标签 | **L：不传不过滤**。`hatsune miku` → `count` 1、命中 id 407；`hatsune` → `count` 0 | `tag='hatsune miku'` |
| `search` | — | **L：被忽略**——`search='hatsune'` 与不带该参数的响应计数、前几项 id 完全一致（`count` 都是 156541、前 3 个 id 都是 226296 / 226295 / 226294） | — | `search='hatsune'`（不生效） |
| `**params` | 其它名字原样进查询串 | — | 本轮发过上表这些名字 | — |

`type` 的实测 `count`（`limit=2&offset=0`，2026-09-19 快照；**类别名是推断，站点只返回整数**）：

| `type` | 本轮 `count` | 本轮首项名称 | 输入资料的候选类别名（推断，非官方定义） |
| :--- | ---: | :--- | :--- |
| `0` | 4303 | `editor (kankin jk)` | 其它 / 未分类 |
| `1` | 56435 | `nakumura tamaki` | 角色 |
| `2` | 4474 | `hasshaku-sama (cosplay)` | 通用属性 |
| `3` | 5510 | `buta thunder (vocaloid)` | 动画 / 剧集；该名称不能覆盖所有已见样本 |
| `4` | 76532 | `giao giao` | 作者 / 画师 |
| `5` | 4606 | `ai the somnium files` | 游戏 |
| `6` | 1909 | `knight a` | 品牌 / 公司 / 企划 |
| `7` | 2772 | `anima (honkai: nexus anima)` | 物品；仅凭样本不能确认这个类别名 |
| `8` | 0 | 无，`tags=[]`、HTTP 200 | 未确定，不能据此推断所有更大值 |

信封字段（L）：`success`（bool）、`offset`、`limit`、`count`（**过滤条件下的总标签数**，与 `limit` 无关）、
`tags`（数组）。本轮：不带参数和带 `search` 时 `limit` 20、`offset` 0、`count` 156541、`tags` 20 项；
`tag='hatsune miku'` 时 `count` 1、`tags` 1 项（id 407）；`tag='hatsune'` 时 `count` 0、`tags` `[]`。

**标签对象**（L）：

| 字段 | 类型与本轮示例 | 含义 |
| :--- | :--- | :--- |
| `id` | int `407` | 标签编号 |
| `tag` | str `"hatsune miku"` | 主名称 |
| `tag_ru` | str 或 `null` | 俄文名（本轮 `"хацунэ мику"`；默认列表里多为 `null`） |
| `tag_jp` | str 或 `null` | 日文名（本轮 `"初音ミク"`） |
| `num` | int `22686` | 关联帖子总数 |
| `num_pub` | int `21988` | 已发布帖子数 |
| `type` | int `1` | 类别整数，站点不返回名称 |
| `description_en` / `description_ru` / `description_jp` | str 或 `null` | 三种语言的说明（本轮 `description_en` 是含 `\r\n` 的长文本、`_ru`/`_jp` 为 `null`） |
| `alias` | `null` | 别名；本轮所有样本都是 `null` |
| `parent` | int 或 `null` | 父标签 id（本轮子标签 `illustrious (azur lane)` 的 `parent` 是 152814，即 `azur lane`）；默认列表里的样本为 `null` |
| `views` | int `93150` | 标签页浏览量；该值是标签 407 的本轮快照 |

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    exact = client.tags_list(tag='hatsune miku')
    # GET https://api.anime-pictures.net/api/v3/tags?tag=hatsune+miku
    # L：200，count 1，tags[0].id 407，tag_ru "хацунэ мику"、num 22686、num_pub 21988
    print(exact['count'], exact['tags'][0]['id'], exact['tags'][0]['tag_jp'])

    missing = client.tags_list(tag='hatsune')
    # GET https://api.anime-pictures.net/api/v3/tags?tag=hatsune
    # L：200，count 0、tags 空数组 —— tag 是精确匹配，不能当前缀搜索
    print(missing['count'], missing['tags'])

    next_tags = client.tags_list(limit=2, offset=2)
    # GET https://api.anime-pictures.net/api/v3/tags?limit=2&offset=2
    # L：200，offset 2、limit 2、count 156541；两项 id 为 226294、226293
    print(next_tags['limit'], next_tags['count'])
```

### tag_show

签名：`tag_show(tag_id, **params)`。路由：`GET /api/v3/tags/{tag_id}`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | 整数 | 标签编号，进 URL 路径 | 必填 | `tag_show(407)` |
| `**params` | 本轮没有可识别参数 | — | L 只发过不带额外参数的请求 | `tag_show(407)` |

L：200 `{"success": true, "tag": {…}}`，`tag` 就是一个[标签对象](#tags_list)（本轮 id 407）；
不存在的 id → **404** `{"errormsg":"Tag not found","success":false}`。

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    tag = client.tag_show(407)
    # GET https://api.anime-pictures.net/api/v3/tags/407
    # L：200 {"success": true, "tag": {...}}，tag.tag "hatsune miku"、tag.views 93150
    print(tag['success'], tag['tag']['id'], tag['tag']['tag'], tag['tag']['views'])
```

## 用户（2 个方法）

### users_list

签名：`users_list(**params)`。路由：`GET /api/v3/users`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | 正整数；仅抽测 2、101 与缺省 | 每页条数 | **L：默认 20**；`101` 回显 100、回 100 项。其余越界值未实测 | `limit=2` |
| `offset` | ≥0 的整数 | 跳过条数 | **L：默认 0**；`offset=2` 回显 2 并跳过前 2 项 | `offset=0` |
| `**params` | 其它名字原样进查询串 | — | 本轮发过 `limit` / `offset` | — |

L：不带参数 → 200 `{"success": true, "offset": 0, "limit": 20, "count": 225284, "users": […20 条…]}`；
`?limit=2&offset=0` → `limit` 2、`users` 2 条。`count` 是总用户数，与 `limit` 无关。用户对象见下。

### user_show

签名：`user_show(user_id, **params)`。路由：`GET /api/v3/users/{user_id}`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | 整数 | 用户编号，进 URL 路径 | 必填 | `user_show(294066)` |
| `**params` | 本轮没有可识别参数 | — | L 只发过不带额外参数的请求 | `user_show(294066)` |

**顶层是三个键**（L）：`success`（bool）、`user`（对象）、**`errormsg`（成功时是 `null`）**。
不存在的 id → **404** `{"errormsg":"User not found","success":false}`。

**用户对象**（L）：本轮见过的键有 `id`、`name`、`login`、`avatar_version`、`isavatar`、`site_score`、
`groups`、`gender`、`register_date`，但**不是每个路由都同形**——`user_show` 的样本就没有 `login`。
本轮样本对照：

| 字段 | `users_list` 的项（id 294066） | `user_show(294066)` |
| :--- | :--- | :--- |
| `id` | 294066 | 294066 |
| `name` | `"Nekomina"` | `"Nekomina"` |
| `login` | `"Nekomina"` | **没有这个键** |
| `avatar_version` | 3 | 3 |
| `isavatar` | true | true |
| `site_score` | 21638 | 21638 |
| `groups` | `["user"]` | `["user"]` |
| `gender` | `null` | `null` |
| `register_date` | `"2026-02-28T15:59:00.140189"` | 同左 |

也就是说**用户对象的键不固定**：`users_list` 的项有 `login`，本轮 `user_show` 的样本没有 `login`
（`gender` 本轮还见过 `1` / `2`，含义未实测）。**没有头像地址字段**——只有 `avatar_version` + `isavatar`；
输入文档里旧客户端的 `avatars/…` 路径本轮没有请求过，不要当契约。

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    listing = client.users_list(limit=2, offset=0)
    # GET https://api.anime-pictures.net/api/v3/users?limit=2&offset=0
    # L：200，count 225284，users 2 条，id 257203 与 294066
    print(listing['count'], [user['id'] for user in listing['users']])

    profile = client.user_show(294066)
    # GET https://api.anime-pictures.net/api/v3/users/294066
    # L：200 {"success": true, "user": {...}, "errormsg": null}
    #    user.name "Nekomina"、site_score 21638、register_date "2026-02-28T15:59:00.140189"
    print(profile['success'], profile['errormsg'], profile['user']['name'])
    print(profile['user']['groups'], profile['user']['isavatar'])
```

## 评论（2 个方法）

### comments_list

签名：`comments_list(**params)`。路由：`GET /api/v3/comments`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | 正整数；仅抽测 2、101 与缺省 | 每页条数 | **L：默认 20**；`101` 回显 100、回 100 项。其余越界值未实测 | `limit=2` |
| `offset` | ≥0 的整数 | 跳过条数 | **L：默认 0**；`offset=2` 回显 2 并跳过前 2 项 | `offset=0` |
| `**params` | 其它名字原样进查询串 | — | 本轮发过 `limit` / `offset` | — |

L：不带参数 → 200 `{"success": true, "offset": 0, "limit": 20, "count": 14988, "comments": […20 条…]}`；
`?limit=2&offset=0` → `limit` 2、`comments` 2 条。
每条是 `{comment, user, post}` 三段：`post` 是帖子对象（**不含预览图字段**，与 `posts_list` 一致）。
输入文档称 `post_id` / `user_id` / `post` 等参数会被忽略；本轮**没有测过**这些参数名。

### comment_show

签名：`comment_show(comment_id, **params)`。路由：`GET /api/v3/comments/{comment_id}`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `comment_id` | 整数 | 评论编号，进 URL 路径 | 必填 | `comment_show(174693)` |
| `**params` | 本轮没有可识别参数 | — | L 只发过不带额外参数的请求 | `comment_show(174693)` |

**顶层是三个键**（L）：`success`（bool）、`comment`（对象）、`user`（评论者用户对象）——
**顶层确实带 `user` 段**（输入文档说没有 `user`，是错的）。不存在的 id → **404**
`{"errormsg":"Have no comment","success":false}`。

**评论对象**（L）：

| 字段 | 类型与本轮值 | 含义 |
| :--- | :--- | :--- |
| `id` | int `174693` | 评论编号 |
| `datetime` | str `"2026-09-19T09:13:46.230319"` | 发表时间 |
| `language` | str `"en"` | 评论语言 |
| `text` | str `"Twitter: https://twitter.com/usa_mitha"` | 站点 BBcode 原文 |
| `html` | str | 渲染后的 HTML，`/` 会写成 `&#x2F;`，链接带 `rel="nofollow" target="_blank"` |

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    listing = client.comments_list(limit=2, offset=0)
    # GET https://api.anime-pictures.net/api/v3/comments?limit=2&offset=0
    # L：200，count 14988，每条是 {comment, user, post}；post 段没有预览图字段
    print(listing['count'], [item['comment']['id'] for item in listing['comments']])
    print(listing['comments'][0]['post']['id'], listing['comments'][0]['post']['ext'])

    one = client.comment_show(174693)
    # GET https://api.anime-pictures.net/api/v3/comments/174693
    # L：200 {"success": true, "comment": {...}, "user": {...}}
    print(one['comment']['id'], one['comment']['language'], one['user']['id'])
    print(one['comment']['text'])
```

## 原图入口（1 个方法，成功形态未实测）

### image_get

签名：`image_get(file_url, *, headers=None)`。路由：
`GET /pictures/get_image/{quote(file_url, safe='')}`——**主机根**下，不在 API 基址下。
这是**唯一返回 `bytes` 的方法**：共享层拿到成功响应后直接把正文原样给你，不解析、不嗅探 `Content-Type`、
不写磁盘。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- | :--- |
| `file_url` | 字符串 | 详情响应 `file_url` 原值（含空格的文件名，不是地址），整段按 `quote(…, safe='')` 编码 | 必填 | `client.image_get(detail['file_url'])`，`detail` 来自 `post_show` |
| `headers` | 字典，或 `None` | 额外请求头，**覆盖**同名实例凭据头，只作用于本次请求 | `None`，只带默认头与凭据头 | `headers={'Cookie': '调用方自己的凭据'}` |

L：**匿名 403，正文为空、没有任何 `Content-Type`**（`Content-Length: 0`）→ 抛 `AnybooruHTTPError`，
`error.data` 是 `None`、`error.body` 是 `''`。**成功返回什么字节、需要什么凭据都没有实测**：
只知道输入文档说这条路要登录，且本轮 403 无法说明 Cookie 名或头部方案是否正确、是否唯一。
不要把 403 当成「填上 Cookie 就一定能成功」。

```python
from anybooru import AnybooruHTTPError, AnimePictures

with AnimePictures('anime_pictures') as client:
    detail = client.post_show(929452)
    try:
        content = client.image_get(detail['file_url'])
        # GET https://api.anime-pictures.net/pictures/get_image/<quote(file_url, safe='')>
        # 未实测：匿名 L 是 403 空正文；成功时返回 bytes，本库不做嗅探
        print(len(content))
    except AnybooruHTTPError as error:
        print(error.http_code, repr(error.body), error.data)
        # L 匿名：403 '' None
```

## 媒体地址（只是文本，未实测）

本轮只观察了 `post_show()` 返回的三档预览 URL 字符串，没有向这些 CDN 地址发请求：

```
small_preview  = https://opreviews.anime-pictures.net/7ae/7aed675fc799255bcf7af042314206b2_sp.avif
medium_preview = https://opreviews.anime-pictures.net/7ae/7aed675fc799255bcf7af042314206b2_cp.avif
big_preview    = https://opreviews.anime-pictures.net/7ae/7aed675fc799255bcf7af042314206b2_bp.avif
```

**其余地址公式都是未实测的输入文档候选**（本轮没有对 `opreviews` / `oimages` 发过任何请求）：

* 预览：`https://opreviews.anime-pictures.net/{md5 前三位}/{md5}_{sp|cp|bp|lp}.avif`——
  输入文档称详情不给的 `_lp` 档也存在。
* 格式：输入文档称 `_sp` 同时有 `.png` 变体，`_cp` / `_bp` / `_lp` **只有 `.avif`**，且与帖子的 `ext` 无关。
  本轮**没有验证**这些变体（一次 CDN 请求都没有发）。
* 原图：`https://oimages.anime-pictures.net/{md5 前三位}/{md5}{ext}`（`ext` **自带点**）；
  输入文档称匿名会 `302` 回首页、需要登录 Cookie。本轮未实测。
* 原图另一条入口就是 `image_get()`（`GET /pictures/get_image/{file_url}`），见上。

**不要**把「匿名 403 / 未实测」推成「带上某个 Cookie 就一定能拿到图」；凭据方案、Cookie 名与必要性
本轮都没有验证。要下载字节请自己判断 `Content-Type` 与状态码。

## 错误与状态码（L）

| 状态 | 本轮触发 | 正文与类型 |
| :--- | :--- | :--- |
| `200` | 11 条读路由里的 10 条（`posts_list`、`post_show`、`post_comments`、`tags_list`、`tag_show`、`users_list`、`user_show`、`comments_list`、`comment_show`、`service_info`） | JSON，原样返回 |
| `400` | 缺 `page` 或 `page=abc` | `{"errormsg": "Missing or invalid `page` parameter", "success": false}`，JSON |
| `400` | 路径段不是整数：`GET /api/v3/posts/top` | `` Invalid URL: Cannot parse `top` to a `i32` ``，`text/plain; charset=utf-8`，`data` 为 `None` |
| `400` | `posts_list(page=0, posts_per_page=2, type='json')` | `{"errormsg": "Only json_v3, json1, and xml response types are supported", "success": false}`，JSON |
| `403` | `GET /api/v3/posts/929452/tags` | `{"errormsg": "You not have rights", "success": false}` |
| `403` | `GET /pictures/get_image/{file_url}` | **空正文、无 `Content-Type`** |
| `404` | `tags/{id}` | `{"errormsg": "Tag not found", "success": false}` |
| `404` | `users/{id}` | `{"errormsg": "User not found", "success": false}` |
| `404` | `comments/{id}` | `{"errormsg": "Have no comment", "success": false}` |
| `404` | 路由不存在：`/api/v3/not_a_route`、`/api/v2/comments`、`/pictures/view_posts/0?type=json` | **空正文、无 `Content-Type`**（`Content-Length: 0`），`data` 为 `None` |
| `410` | `posts/{id}` 不存在 | `{"errormsg": "Post not found", "success": false}` |
| `500` | `posts_list(page=-1)` | `{"errormsg": "Internal server error", "success": false}` |
| `401` | 未登录 `POST /api/v3/posts` | 输入文档候选 `{"errormsg": "You have no rights", "success": false}`；**本轮没有样本** |

三个容易踩的点：**帖子不存在是 `410` 不是 `404`**；**非法路径段返回 `text/plain` 纯文本**，
想按 `errormsg` 解析前先看 `Content-Type`（`AnybooruHTTPError.data` 此时是 `None`）；
**路由不存在的 `404` 是空正文且不带 `Content-Type`**，`error.body` 是 `''`、`error.data` 是 `None`。

## 边界与未实测

下面都是输入文档（候选）或本轮没有测到的面，**不要当契约**；逐条依据与矛盾清单见
[依据与差异](anime-pictures-contract-notes.md)。

* **仍未实测的参数**：`posts_list(lang=…)` 的效果（输入文档称无效）、
  「含空格的标签不编码时参数被静默丢弃、返回全库且不报错」（本轮两次带空格搜索都用了 `+` 编码，
  **没有**故意送未编码空格）、输入文档列的其它「被忽略参数名」（`min_width`、`min_height`、`min_size`、
  `min_score`、`keyword`、`tags`、`tag`、`author`、`date`、`rating`、`erotics`、`ids`、`user_id`、
  `juser_id`、`token`、`ltext`、`no_previews` …）——本轮只证了 `tags_list` 的 `search`
  与 `posts_list` 的 `order=asc`/`order=desc`（都配 `order_by=rating`）这两组不生效，
  **不要推广到其它名字与其它组合**。
* **`ldate` 的其它越界值**：本轮只证 `8` 与 `0` 结果相同；`9`、更大的值、负数都没有样本，
  不能把「`≥8` 一律回落到 `0`」写成已测。
* **`post_comments` 的分页**：本轮只证该信封没有 `offset`/`limit`/`count`，没有测过给这个路由传分页参数。
* **`post_tags` 的成功形态**：匿名 403 是唯一样本；凭据正确时返回什么、是否可用，未实测。
* **`post_create` 与凭据**：POST 一次都没发。请求体结构、`Idempotency-Key` 的效果、
  `Authorization` 的方案（`Bearer` 还是裸 token）、Cookie 名与登录换取凭据的端点，全部未实测。
* **媒体**：三个 CDN 地址公式与 `_sp` 的 `.png` 变体、`oimages` 的 302、详情不给的 `_lp` 档，
  本轮零请求；`image_get` 的成功字节形态也未实测。
* **`exclusive_tag` 的出现条件**：只有 `search_tag=hatsune miku` 一个样本带这个键，
  多标签搜索与不存在的标签都没有；什么条件下出现、是否只在精确命中时出现，未实测。
* **`post_show` 的顶层键集合**：本轮取得 `929452`、`929492` 与 `382872` 的详情，其中 `382872` 没有 `source`；
  字段是否出现与什么条件有关，未实测。
* **字段语义**：`datetime` 与 `pubtime` 的区别、`tied`、`artefacts_degree`、`smooth_degree`、
  `gender` 的 `1`/`2`、`type` 的类别名（站点只返回整数，本页的类别名都是推断）、
  `description_en` 为什么在 `exclusive_tag` 里是 HTML、`alias` 恒 `null` 的原因，都未知。
  `status_type` 的缺失已在反序列表中复现，但原因与触发条件未确定。
* **头像地址**：API 只给 `avatar_version` + `isavatar`，没有头像 URL 字段；输入文档里旧客户端拼的
  `avatars/…` 路径本轮没有请求过。
* **旧版路由**：本轮复测了 3 条——`/api/v2/comments`、`/pictures/view_posts/0?type=json`、
  `/api/v3/not_a_route` 都是 **404 空正文**；`/login/submit`、`/pictures/vote`、
  `/pictures/autocomplete_tag`、`/pictures/add_comment/{id}` 本轮没有请求。这些遗留路径不封装、不建议使用。
* **写接口与其它动词**：`PUT` / `PATCH` / `DELETE /api/v3/posts/{id}` 只有输入文档提到的 CORS 通用
  `access-control-allow-methods` 提到过，该路由自己的 `OPTIONS` 输入文档记录为 `Allow: GET,HEAD,POST`；
  本轮没有发过 `OPTIONS`，也不封装这些动词。
* **限流**：本轮未观察到 429 或显式限流响应，未取得官方配额；本库不做节流与退避。

继续阅读：[客户端用法](anime-pictures.md) · [能力入口](anime-pictures-capabilities.md) ·
[依据与差异](anime-pictures-contract-notes.md) · [验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。
