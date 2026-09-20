# Anime-Pictures 客户端用法

`AnimePictures` 访问 Anime-Pictures（`anime-pictures.net`）自研 JSON API。它不是 Danbooru / Moebooru 模板站点：帖子没有标题，没有 `rating` 字符串；评分看整数票数 `score_number`，`score` 是另一个浮点字段，不要混用；标签对象里 `tag` / `tag_ru` / `tag_jp` 并列返回。别把别的家族的路由、参数名或返回结构搬过来。

客户端共 **13 个原生方法**：**12 个读取**（11 条 JSON 读取加 `image_get()` 的字节入口）加 **1 个写方法** `post_create()`（发帖，需要登录）。逐条参数与返回字段见[方法参考](anime-pictures-api.md)；「我要做什么 → 用哪个方法」与 13 方法完整索引见[能力入口](anime-pictures-capabilities.md)。本轮匿名只读的请求与响应摘要见[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)；**输入资料里本轮没复测的候选说法**（参数取值枚举、缺省值、上限、图片地址公式、写接口与登录流程）集中在[依据与差异的边界清单](anime-pictures-contract-notes.md#未实测集中清单)，本页不把它们写成承诺。

## 主机与路径：客户端只对 API 主机说话

包内 `sites.anime_pictures` 的 `url` 就是 API 基址 `https://api.anime-pictures.net/api/v3`；除主机根（`service_info()`）与图片下载入口（`image_get()`）之外，其余 11 个方法都接在它后面。

| 主机 / 路径 | 角色 | 本轮是否请求 |
| :--- | :--- | :--- |
| `https://api.anime-pictures.net/api/v3` | JSON API 基址（包内配置的值） | **是**，本轮 API 基址上的 10 条公开 `GET` 都请求过（其中 `post_tags` 匿名被拒 `403`）；`post_create()` 的 `POST` 本轮没有发 |
| `https://api.anime-pictures.net/` | 主机根，`service_info()` 用它 | **是** |
| `https://api.anime-pictures.net/pictures/get_image/{file_url}` | 原图下载入口（需登录），`image_get()` 用它 | **是**，匿名 `403` |
| `https://anime-pictures.net` | Web 前端与旧版 `/pictures/*` 路由（输入资料说法） | 未请求；本库不抓 HTML |
| `https://opreviews.anime-pictures.net`、`https://oimages.anime-pictures.net` | 预览图与原图 CDN | 未请求；本库不按公式下载媒体（见[媒体地址](#媒体地址只有详情给三档-url公式未实测)） |
| `https://anime-pictures.net/api/v3/*` | 输入资料称会 `302` 到 API 主机 | 未请求；客户端直接用 API 主机，不依赖这个跳转 |

## 第一次调用：主机根与一页帖子

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    greeting = client.service_info()
    # GET https://api.anime-pictures.net/          ← 主机根，不是 API 基址
    # 200 application/json：{"message": "Hello, World!"}
    print(greeting['message'])

    page = client.posts_list(page=0, posts_per_page=2)
    # GET https://api.anime-pictures.net/api/v3/posts?page=0&posts_per_page=2
    # 200 application/json，信封键是 posts_per_page / response_posts_count /
    # page_number / posts / posts_count / max_pages：
    # 本轮 page=0 是 2 条（id 929492、929491），posts_count 667906、max_pages 333952；
    # page=1 是 id 929490、929489 —— 页码从 0 开始，page=1 是第二页
    for post in page['posts']:
        print(post['id'], post['md5'], post['ext'], post['score_number'])
    print(client.last_call['status_code'], client.last_call['url'])

    # 列表里的帖子对象**不含预览地址**，字段以标量为主（`color` 是 RGB 数组）；
    # 要预览地址得取详情（见下）
```

`service_info()` 给无参，返回含 `message` 的 JSON。`posts_list(page=0, posts_per_page=2)` 给页码和每页条数，返回含 `posts` 的信封；`posts` 里是帖子对象，字段以标量为主。

`posts_count` 是当前过滤条件下的总帖子数，`response_posts_count` 只是本次真正返回的条数，两者不要混用。

`page` 是**必填的 0 起步整数**：本轮不带 `page` 与 `page=abc` 都得到 `400 {"errormsg": "Missing or invalid \`page\` parameter", "success": false}`（JSON），`page=-1` 得到 `500 {"errormsg": "Internal server error", "success": false}`。

`posts_per_page` 的本轮单次样本是：不传回 `80`，`1` 与 `100` 按值生效，`101` / `150` / `1000` / `0` 都回 `60`，`-1` 回 `80`（负数只测了 `-1` 这一个值）——**这是具体样本，不是完整的取值规则或上限**，逐条见[方法参考](anime-pictures-api.md)。

## 第二次调用：详情对象与预览地址

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    detail = client.post_show(929452)
    # GET https://api.anime-pictures.net/api/v3/posts/929452
    # 200 application/json；本轮这张图的顶层键是 post / source / user / moderator / tags /
    # file_url / star_it / favorites_users / tied（star_it false、tied []）。
    # 这不是固定九键：帖子 382872 没有 source；这里展示的是 929452 的已观察字段
    post = detail['post']
    print(post['id'], post['width'], post['height'], post['tags_count'])
    print(post['small_preview'], post['medium_preview'], post['big_preview'])
    # post 比列表里的帖子对象多出 small_preview / medium_preview / big_preview 三档
    # opreviews 预览地址；本轮已实测的原文是
    # https://opreviews.anime-pictures.net/7ae/7aed675fc799255bcf7af042314206b2_sp.avif
    # https://opreviews.anime-pictures.net/7ae/7aed675fc799255bcf7af042314206b2_cp.avif
    # https://opreviews.anime-pictures.net/7ae/7aed675fc799255bcf7af042314206b2_bp.avif
    print(detail['source']['kind'], detail['source']['url'])  # 929452 的样本含 source
    for authored in detail['tags']:
        print(authored['tag']['tag'], authored['relation']['addtime'])
        # 每项是 {tag, user, relation}：标签对象、关联该标签的人、关联记录
    print(detail['file_url'])
    # "929452-3550x2344-azur lane-illustrious (azur lane)-…-looking at viewer.png"
    # file_url 是**下载用的文件名，不是地址**，含空格；它是 image_get() 的入参（客户端负责编码）

    comments = client.post_comments(382872)
    # GET https://api.anime-pictures.net/api/v3/posts/382872/comments
    # 200 application/json：{"success": true, "comments": [ … ]}
    # 每项是 {comment, user}；comment 的键是 id / datetime / language / text / html，
    # 本轮该帖 1 条评论（id 174693）；**没有 offset / limit / count 分页信封**
    for item in comments['comments']:
        print(item['comment']['id'], item['comment']['language'])
```

`post_show(929452)` 给帖子 id，返回详情对象；`post` 比列表里的帖子对象多出 `small_preview` / `medium_preview` / `big_preview` 三档 `opreviews` 预览地址。

`post_comments(382872)` 给帖子 id，返回 `comments` 数组；每项是 `{comment, user}`，`comment` 的键是 `id` / `datetime` / `language` / `text` / `html`。本轮该帖只有 1 条评论（id `174693`）。

帖子不存在时返回的是 **`410`（不是 `404`）**：`{"errormsg": "Post not found", "success": false}`；标签 / 用户 / 评论不存在才是 `404`（`Tag not found` / `User not found` / `Have no comment`）。`post_comments()` 没有分页信封，但这**不代表**任意分页参数一定无效——本轮只证了响应里没有这些字段。

## 构造与配置

签名：`AnimePictures(site_name=None, site_url=None, authorization=None, cookie=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`。

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 中的键名 | 不选命名站点，需显式给 `site_url` | `AnimePictures('anime_pictures')` |
| `site_url` | 字符串，站点基地址；本类必须是 API 基址 | 读取所选站点的 `url`（包内是 `https://api.anime-pictures.net/api/v3`） | `AnimePictures(site_url='https://api.anime-pictures.net/api/v3')` |
| `authorization` | 字符串，**非空**才按原值发送 `Authorization: <原值>` | `None` 时有站点名就读站点条目的 `authorization`（包内为空串）；显式 `''` 表示明确不带凭据 | `AnimePictures('anime_pictures', authorization='…')` |
| `cookie` | 字符串，**非空**才按原值发送 `Cookie: <原值>`（整条 Cookie 头的值） | 同 `authorization`：`None` 回落站点条目，显式 `''` 强制匿名 | `AnimePictures('anime_pictures', cookie='…')` |
| `proxies` | 字典，按 `http` / `https` 指定代理，`{}` 表示直连 | 使用 `request.proxies`；不读环境变量 | `AnimePictures('anime_pictures', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json` | `AnimePictures('anime_pictures', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接/读取超时二元组 | 使用 `request.timeout` | `AnimePictures('anime_pictures', timeout=10)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent` | `AnimePictures('anime_pictures', user_agent='MyBooruApp/1.0')` |

**构造不发任何请求**，也不校验凭据；用完记得 `client.close()`，或用 `with` 语句块。

包内站点条目只有三个字段：

```json
{"anime_pictures": {
  "url": "https://api.anime-pictures.net/api/v3",
  "authorization": "",
  "cookie": ""
}}
```

复制完整配置的方法见[配置指南](configuration.md)。

## 凭据：原样透传，不做 scheme，也没有登录方法

* **两个字段都只是请求头原文**。非空 `authorization` 直接写进 `Authorization` 头、非空 `cookie` 直接写进 `Cookie` 头，客户端**不加** `Bearer` 前缀、不解析、不刷新、不猜 cookie 名。整条 Cookie 头的值（含 `名字=`）要自己给全。
* **本库不提供**登录、注册、刷新令牌的方法，也不索要账号；请把已有凭据填进 `authorization` / `cookie`，或留在 `''` 上做匿名请求。
* **凭据的确切形式未实测**：本轮全部请求都是在两个字段为空串时发出的，`Authorization` 与 `Cookie` 的成功路径没有样本。输入资料称浏览器登录 Cookie 名是 `anime_pictures_jwt`、v3 写操作按 CORS 用 `authorization` 头——这些是**候选说法，不是本库的承诺**，别拿匿名 `403` 反推“Cookie 一定对/一定唯一”。

需要带凭据的调用形态如下（**未执行、未实测**，仅示意字面写法）：

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures', authorization='<凭据原值>', cookie='<整条 Cookie 头的值>') as client:
    detail = client.post_show(929452)              # 公开读取，这里只是为了拿 file_url
    labeled = client.post_tags(929452)             # 需要权限的读取：本轮匿名 403
    blobs = client.image_get(detail['file_url'])   # 需要登录的原图入口：成功返回 bytes（见下）
```

## 通用入口 `request()`

签名：`request(method, path, *, params=None, data=None, headers=None)`。

它与 13 个原生方法走同一条通路，只是路径、动词和正文由你给全。`path` **用 `urljoin` 接到基址上**，所以**前导 `/` 会换成主机根**，这与本库多数家族「去掉前导斜线」的行为不同：

| `path` 写法 | 实际请求的地址 | 说明 |
| :--- | :--- | :--- |
| `'posts'` | `https://api.anime-pictures.net/api/v3/posts` | 相对 API 基址，最常用 |
| `'posts/929452/comments'` | `https://api.anime-pictures.net/api/v3/posts/929452/comments` | 拼接在基址后面 |
| `'/api/v3/posts'` | `https://api.anime-pictures.net/api/v3/posts` | **前导 `/` 是主机根路径**，不是基址相对路径 |
| `'/'` | `https://api.anime-pictures.net/` | `service_info()` 走的就是这个主机根 |
| `'/pictures/get_image/…'` | `https://api.anime-pictures.net/pictures/get_image/…` | `image_get()` 的入口在主机根下，不在 `/api/v3` 下 |

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串 | 必填 | `client.request('GET', 'posts', params={'page': 0})` |
| `path` | 上面那张表的路径写法 | 必填 | `client.request('GET', '/api/v3/tags/407')` |
| `params` | 查询参数字典；值为 `None` 的键不发送，布尔发成小写 `true` / `false` | `None`，不发查询参数 | `client.request('GET', 'tags', params={'tag': 'hatsune miku'})` |
| `data` | **JSON 请求体**：字典原样交给 requests 的 `json` 参数，**含 `None`（会发成 `null`），不清理、不改名**；正文里是什么字段由你自备（字段名未实测，见[方法参考](anime-pictures-api.md)） | `None`，不带请求体 | `client.request('POST', 'posts', data=data)` |
| `headers` | 额外请求头字典，只作用于本次请求；**同名时覆盖实例的凭据头** | `None`，不附加 | `client.request('GET', 'posts', headers={'Accept-Language': 'zh-cn'})` |

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    page = client.request('GET', 'posts', params={'page': 1, 'posts_per_page': 2})
    # GET https://api.anime-pictures.net/api/v3/posts?page=1&posts_per_page=2
    print(page['page_number'], len(page['posts']))

    same_page = client.request('GET', '/api/v3/posts', params={'page': 1, 'posts_per_page': 2})
    # 前导斜线写法：同样是 /api/v3/posts；主机根下的路由（如 '/pictures/get_image/…'）只能这样写
    print(same_page['page_number'], client.last_call['url'])
```

客户端**不**补版本前缀、不补 `.json`、不拆信封、不改字段名、不合并分页、不重试、不钳位任何参数、不做本地参数校验，也不加隐式的 Anime-Pictures 专属头。`POST` 正文的字段名**未知**，所以 `post_create()` 只把你给的 dict 原样作为 JSON 发出，本库不替你猜字段。

## 返回值：JSON 与 bytes

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | 解析后的 Python 对象，一层都不拆：列表是 `{posts, posts_count, max_pages, …}`、`{tags, count, offset, limit, success}`、`{users, …}`、`{comments, …}`，详情是 `{post, …}`（本轮样本 929452 另有 `source`/`user`/`moderator`/`tags`/`file_url`/`star_it`/`favorites_users`/`tied`，**不是固定键集**），单资源是 `{tag: …}` / `{user: …}` / `{comment: …}` |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`、`data`。本轮的样本是 `403 {"errormsg": "You not have rights", "success": false}`、`404 {"errormsg": "Tag not found", "success": false}`、`410 {"errormsg": "Post not found", "success": false}`，以及 `400` 的**纯文本**正文 |
| 2xx 但正文为空 | 返回 `None`（空响应不当错误处理） |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError` |
| 网络错误 | requests 自己的异常原样抛出，没有重试 |
| `image_get()` 成功 | **原始 `bytes`**，不解析、不嗅探、不写磁盘、不落缓存 |

`image_get(file_url, *, headers=None)` 给 `file_url` 和可选请求头，成功时返回原始 `bytes`——它是本库唯一的字节出口。它请求 `GET https://api.anime-pictures.net/pictures/get_image/{quote(file_url, safe='')}`，入参用详情响应的 `file_url`（**含空格的文件名**，客户端会把它整段做 URL 编码，**你不要自己先编码**）。本轮匿名请求得到 **`403` + 空正文、响应里没有 `Content-Type`**，成功时的字节数与格式**未实测**。

每次收到响应后 `client.last_call` 是最近一次的情况：`API`（这次调用的路由路径，如 `posts`、`/pictures/get_image/…`）、`url`（含查询串的最终地址）、`status_code`、`status`、`headers`。`image_get()` 与其它方法共用同一条传输层，所以它也会更新 `last_call`。核对“参数发成什么样”看它：

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    client.tags_list(tag='hatsune miku')
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://api.anime-pictures.net/api/v3/tags?tag=hatsune+miku
```

**非法路径段返回的是 `text/plain` 而不是 JSON**：本轮 `posts/top` 得到 `400`、`Content-Type: text/plain; charset=utf-8`、正文 ``Invalid URL: Cannot parse `top` to a `i32` ``。此时 `AnybooruHTTPError.data` 是 `None`，原文在 `.body` 里，`last_call` 仍记录 URL 与状态码。详见 [errors.md](errors.md)。

## 媒体地址：只有详情给三档 URL，公式未实测

**本库不按公式下载媒体**，也不替你拼地址；唯一的例外是上面那个需要登录的 `image_get()`。本轮**已经实测**的只有详情响应里原文给出的三档 `opreviews` 地址（`small_preview` / `medium_preview` / `big_preview`，`post` 对象的一部分，样本见上文）。其余地址公式来自输入资料，**本轮没有请求过任何 CDN 地址**，候选公式集中到[边界与未实测](#边界与未实测)。

用法的三条提醒：**绝对地址不要再拼主机**；**地址里的尺寸档位与后缀照抄，不要自己替换**；**要用 CDN 时自己检查 `Content-Type` 与实际字节**——本轮没测过它们，本库也不为它们做兜底。

## 容易踩的坑（本轮都有样本）

1. **帖子不存在是 `410`，标签 / 用户 / 评论不存在才是 `404`**，四者的正文都是 `{"errormsg": "…", "success": false}`。
2. **非法路径段是 `400 text/plain`**（``Invalid URL: Cannot parse `top` to a `i32` ``），不是 JSON。按条件取“第一张”要走列表接口，别把非数字塞进 `posts/{id}`。
3. **`page` 必填且 0 起步**：不传 / 非整数 `400`，`-1` `500`；`page=1` 是第二页。
4. **列表不带预览地址**，`small_preview` / `medium_preview` / `big_preview` 只在详情里。
5. **`score` 与 `score_number` 是两个字段**：`score_number` 是整数票数（实测过 `6`、`9`、`70`、`629`），`score` 是浮点字段，本轮取值覆盖 `0.0`–`1446.0`（例如 `id 301063` 是 `score` 1446.0 / `score_number` 629、`id 2` 是 73.0 / 70，多数帖子是 0.0）——输入资料称 `score` 恒为 `0.0`，本轮数据**明确不支持**；它自己的含义站点未说明，排序/比较请用 `score_number`。
6. **`ext` 自带点**、**`file_url` 是文件名不是地址且含空格**（要自己做路径段时别漏编码）。
7. **`tags?tag=` 是精确匹配**：`tag=hatsune miku` 回 `count 1`（`id 407`），`tag=hatsune` 回 `count 0`；本轮的 `tags?search=hatsune` 与不带任何参数**返回相同结果**（`count` 都是 156541），所以在这些取值下 `search` 没有效果——别把它当搜索用，也别由此推断其它参数全部无效。
8. **`post_comments` 没有分页信封**（没有 `offset` / `limit` / `count`）；本轮该帖只有 1 条评论。
9. **同一类资源在不同路由里的包装层不同**：`tag_show` 是 `{success, tag}`、`user_show` 是 `{success, user, errormsg}`、`comment_show` 是 `{success, comment, user}`；`comments_list` 的每项是 `{comment, user, post}`，其中 `post` 同样不含预览字段。
10. **`post_tags` 匿名被拒**：本轮 `403 {"errormsg": "You not have rights", "success": false}`，成功形态未实测；标签通常已经在详情响应的 `tags` 里。
11. **字段不是处处齐全**：本轮抽样里有帖子对象**没有 `status_type`**（列表样本里就出现过）；同一个 `user_show` 的 `user` 对象没有 `login` 键，而详情里的 `user` 有。别假设字段处处存在、处处同构。
12. **帖子搜索的标签串**：`search_tag` 的值是标签名，多个标签用**空格分隔**写成一个值（本轮 `'long hair blue eyes'` 有结果，`posts_count` 146065——是否每帖都带这两个标签未逐帖核实），整串不存在时 `posts_count` 0（`max_pages` 也是 0，不是 `-1`）；本轮 `'hatsune miku'` 那一次响应顶层还**多出一个 `exclusive_tag` 键**（命中的那个标签对象），其它 `search_tag` 取值没有这个键——它何时出现未实测。输入资料称未编码的空格会让服务端静默忽略该参数——**本轮未复测**；用本库的 `params` 传值时由 requests 负责编码，但你自己拼 URL 或路径段时要编码。
13. **旧版写法不会再被接受**：旧版参数 `type=json` 本轮实测 `400 {"errormsg": "Only json_v3, json1, and xml response types are supported", "success": false}`（响应里提到的 `json_v3` / `json1` / `xml` 三种格式本轮都没有请求过，本库也不提供对应方法）；API 主机上的旧版路径（`/api/v2/comments`、`/pictures/view_posts/0?type=json`）与不存在的 v3 路由本轮都是 `404` **空正文**。新代码请用 `/api/v3`。

## 可运行示例

两个脚本都匿名只读，参数来自配置的 `examples.anime_pictures` 段，脚本里没有硬编码站点或查询值：

```bash
python examples/anime_pictures/list_posts.py
python examples/anime_pictures/browse_resources.py
```

* `list_posts.py`：按配置的 `post_query`（`search_tag` / `posts_per_page` / `order_by`）走配置的 `pages`，打印每次真实的 `last_call` URL 与状态码、`page_number`、`posts_count`、`max_pages` 与帖子的 `id`、`score_number`。
* `browse_resources.py`：`post_show(配置的 post_id)` → `post_comments(同一个 id)` → 用详情里的 `user['id']` 调 `user_show` → 用第一条非空评论的 `comment['id']` 调 `comment_show`；评论为空时不发那条请求并说明。它只打印字段，不打印评论正文，也不访问任何媒体地址。

两个脚本都显式使用空凭据（匿名）、不跟随跳转、请求之间按配置的 `pause_seconds` 停顿。轻量冒烟 `test/anime_pictures.py`（匿名、只读、最多 10 次请求、不 mock、不进 CI，参数取自 `smoke.anime_pictures`）用下面的命令运行，每行 `PASS/FAIL`，末尾 `SUMMARY`，失败退出 1：

```bash
python test/anime_pictures.py --config <你的配置文件>
```

三个脚本的实际执行命令、请求数、状态码与退出码记录在[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)；**它们覆盖的是用法路径，不等于 13 个方法逐一验证过。**

## 边界与未实测

本页出现的“本轮实测”都只指 2026-09-19 那批匿名只读请求；下面这些**没有样本**，不要当契约：

* **参数样本已覆盖，语义未穷尽**：本轮匿名探测取过 `page` / `posts_per_page`、`order_by` 的七个值、有无 `order` 的对照、`search_tag` / `denied_tags`、`ldate` 0–8、标签 `type` 0–8、`tags?search=`、`aspect` / `color` / `ext_*` / `user` / `stars_by`，以及三类列表的 `limit` / `offset` 与缺省值，都是**单次样本**（逐条见[验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)）。这些参数的完整规则、缺省与边界以[方法参考](anime-pictures-api.md)与[依据与差异](anime-pictures-contract-notes.md)的标注为准，没有取过的取值不要按样本外推。
* **没有样本的参数与语义**：标签 `type` 整数到类别名的映射（站点不返回名称）、`lang` 的效果、被静默忽略的参数清单、`datetime` / `tied` / `artefacts_degree` / `smooth_degree` 的确切含义、用户头像地址（API 只给 `avatar_version` 与 `isavatar`）、`ldate` 各区间长度的官方定义。
* **凭据与写操作**：`Authorization` / `Cookie` 的成功路径、发帖 `POST /api/v3/posts` 的请求体与返回、`PUT` / `PATCH` / `DELETE`、登录或换取凭据的端点——全部未实测（`post_create()` 只原样发送你给的 dict）。
* **媒体**：`opreviews` / `oimages` 的地址公式与格式变体、`image_get()` 成功时的字节与 `Content-Type`——本轮没有请求过 CDN 媒体；`image_get` 仅观察到匿名 403 空正文，详情里的预览 URL 只读作字符串。

  | 候选公式（输入资料，**未实测**） | 说明 |
  | :--- | :--- |
  | `https://opreviews.anime-pictures.net/{md5前3位}/{md5}_{sp\|cp\|bp\|lp}.avif` | `{md5}` 取帖子对象的 `md5`，`{md5前3位}` 是它的前三个字符；`_lp` 详情不返回 |
  | `…_sp.png` | 输入资料称 `_sp` 有 `.png` 变体，`_cp` / `_bp` / `_lp` 只有 `.avif` |
  | `https://oimages.anime-pictures.net/{md5前3位}/{md5}{ext}` | `ext` 自带点，所以正确拼法是 `{md5}.png`；再自己加点会拼成 `{md5}..png`（两个点）。输入资料称匿名拿不到（`302` 回首页） |
* **旧版路由**：API 主机上的 `/api/v2/comments` 与 `/pictures/view_posts/0?type=json` 两个旧版路径本轮实测是 `404` 空正文，旧版参数 `type=json` 实测 `400`（见上面的坑 13，其它旧版路径与响应里提到的 `json_v3` / `json1` / `xml` 格式本轮都没有请求）；web 主机（`anime-pictures.net`）本轮未请求，本库也不包装这些路由，需要时用 `request()` 自己试。
* **未实测不等于不存在**：站点数据实时变动，本页的编号、条数、计数都只是那一天的快照。

继续阅读：[方法参考](anime-pictures-api.md) · [能力入口](anime-pictures-capabilities.md) · [依据与差异](anime-pictures-contract-notes.md) · [验证记录](verification.md#anime-pictures匿名只读实测2026-09-19)。
