# Anybooru - Danbooru / Moebooru / Serika / e621ng / Zerochan / Gelbooru / e-shuushuu / Gelbooru 0.2 / Sakuria / Anime-Pictures / Cosine / Nhentai / ArtStation 图站 API 客户端

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/NebulaeWisdom/anybooru/master/LICENSE)

**Anybooru** 是访问十二类图站 API 的 Python 客户端：Danbooru 系（`danbooru.donmai.us`、
`safebooru.donmai.us`）、Moebooru 系（`yande.re`、`konachan.com`、`sakugabooru.com`）、
Serika（`serika.art` 与同引擎自托管实例）、e621ng（`e621.net`、`e926.net`）、Zerochan（`zerochan.net`）
、Gelbooru（`gelbooru.com`）、e-shuushuu（`e-shuushuu.net`）、Gelbooru 0.2（TBIB，`tbib.org`）、
Sakuria（Pixiv 第三方镜像）、Anime-Pictures（`anime-pictures.net`，自研 `api/v3` 接口）、
Cosine（`pic.cosine.ren`，自研 API 的 Next.js 图站）、Nhentai（`nhentai.net`，站点自带的 `.net` API v2）
与 ArtStation（`artstation.com`，公开作品集、只读搜索与 RSS 订阅源）。
它不做跨引擎的统一图库模型：每个家族的方法只包装**该引擎自己**的路由，参数按该引擎的规则编码，
服务端返回的字段原样交给你，字段差异不隐藏。

同名方法在不同引擎上返回的字段不同。下表的 `client` 由对应家族创建，完整代码在后面的十二个例子里：

| 调用 | 真实请求 | 你拿到什么 |
| :--- | :--- | :--- |
| Danbooru：`client.post_list(tags='rating:g', limit=3)` | `GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=3` | 帖子列表；标签是空格分隔字符串 `post['tag_string']`，文件地址是 `post['file_url']` |
| e621ng：`client.post_list(tags='rating:s', limit=2)` | `GET https://e621.net/posts.json?tags=rating%3As&limit=2` | 帖子列表；普通标签在 `post['tags']['general']` 数组里，文件地址在 `post['file']['url']`，总分在 `post['score']['total']` |
| Moebooru：`client.post_list(tags='rating:s', limit=3)` | `GET https://yande.re/post.json?tags=rating%3As&limit=3` | 帖子列表；文件地址是 `post['file_url']`，标签是空格分隔字符串 `post['tags']` |
| Serika：`client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')` | `GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest` | 字典的 `images` 是图片列表，`pagination` 有页码和总数；每张图同时有内部编号 `id` 与网页上使用的编号 `post_id` |
| Zerochan：`client.entry_list(tags='Genshin Impact', l=2)` | `GET https://www.zerochan.net/Genshin+Impact?l=2&json=` | 返回 `{"items": [...]}` 里的图片列表；每张有编号 `id`、宽高、`thumbnail` 缩略图地址、`source` 来源、`tag` 主标签、`tags` 全部标签，以及 `md5` |
| Gelbooru：`client.autocomplete('blue', type='tag', limit=3)` | `GET https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2` | 建议数组，每条含 `type` / `label`（如 `blue eyes`）/ `value`（如 `blue_eyes`）/ `post_count` / `category`（如 `tag`、`copyright`）。**`limit` 不决定本次返回几条**：实测 `limit=3` 仍返回 10 条 |
| e-shuushuu：`client.image_list(tags='46', per_page=2)` | `GET https://e-shuushuu.net/api/v1/images?tags=46&per_page=2` | 完整对象中的 `images` 是图片数组，`total/page/per_page` 是本次查询的分页数据；图片带 `image_id`、`tags`、`url` 和 `thumbnail_url`。`tags` 收数字标签 ID，不收名字 |
| Gelbooru 0.2：`client.post_list(tags='rating:safe', limit=2)` | `GET https://tbib.org/index.php?tags=rating%3Asafe&limit=2&s=post&q=index&page=dapi&json=1` | JSON 数组含 `id/width/height/rating/tags`，没有媒体 URL；显式 `response_format='xml'` 返回完整 XML 字符串，帖子属性才含 `file_url/preview_url` |
| Sakuria：`client.illust_search(q='blue', page=1, size=2)` | `GET https://sakuria-api.syarolia.com/search/illust?q=blue&page=1&size=2` | 完整字典中的 `items` 是插画数组；每项含 `id/title/urls/author/tags`，图片尺寸在 `urls.w/urls.h`，不是顶层 |
| Anime-Pictures：`client.posts_list(search_tag='hatsune miku', posts_per_page=2, page=0)` | `GET https://api.anime-pictures.net/api/v3/posts?search_tag=hatsune+miku&posts_per_page=2&page=0` | 完整信封：`posts` 是帖子数组，另有 `page_number` / `posts_per_page` / `response_posts_count` / `posts_count` / `max_pages`；每帖含 `id`、`md5`、`ext`（如 `.png`，**带点**）与 `score_number`（评分看它；`score` 原样保留，样本里既有 `0.0` 也有非零值）。列表**不给**预览地址 |
| Cosine：`client.image_list(page=1, pageSize=2)` | `GET https://pic.cosine.ren/api/list?page=1&pageSize=2` | 站内作品列表；方法原样返回 `{"images": [...], "total": N}`，不剥层。每项 `id` 是站内自增编号，上游编号在 `pid`；`rawurl` / `thumburl` 是地址。列表样本里 `size` 是 `null`、`guest` 是 `false`（只代表这批样本，不推广成恒值） |
| Nhentai：`client.gallery_list(per_page=2)` | `GET https://nhentai.net/api/v2/galleries?per_page=2` | 完整信封：`result` 是作品数组，另有 `num_pages` / `per_page` / `total`；每项有 `id`、`media_id`、`num_pages`、`num_favorites`、`thumbnail` 与 `thumbnail_width` / `thumbnail_height`、`tag_ids`（标签编号数组）、`blacklisted`。`gallery_show(id, include='related')` 是另一套详情对象（`cover` / `thumbnail` 带宽高、`pages`、`tags`、`scanlator`、`upload_date`）；方法不拆层 |
| ArtStation：`client.project_list(page=1, per_page=2)` | `GET https://www.artstation.com/projects.json?page=1&per_page=2` | 公开作品列表；方法原样返回 `{"data": [...], "total_count": N}`，不剥 `data` 层。条目样本含 `id`、`hash_id`、`title`、`permalink`、`cover`、`assets_count` 与 `tag_list`。**用户作品列表是另一套条目字段**：`user_projects` 的条目没有 `user` / `views_count`，不要跨路由照抄字段清单 |

十二个家族的来路不同：Danbooru、Moebooru、e621ng 是三个**互不相同**的 Rails 引擎，同名路由与相同的
认证头不代表同一套契约；Serika 是独立的 Next.js 应用，官方版本化 `/api/v1` 与站内未版本化 `/api/*`
两面分开标注；Zerochan 是站点自有的只读 JSON API，**没有公开的引擎源码**，契约依据是官方 API 页面快照
加真实请求实测——见
[docs/zerochan-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-contract-notes.md)；
Gelbooru 走站点自己的 `index.php`：`page=dapi`（加 `json=1`）与页面脚本用的 `page=autocomplete2` 返回
JSON；`page=tags/post/wiki` 等浏览路由返回 HTML。依据是官方 wiki/帮助页与站点脚本
加真实响应，见
[docs/gelbooru-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru-contract-notes.md)。
e-shuushuu 是独立的 FastAPI REST API，依据是站点自带的 [OpenAPI](https://e-shuushuu.net/api/openapi.json)
与真实响应，不套 Danbooru/Moebooru 路径。前四个家族按上游源码对齐，其余按各站点可获得的依据核对；
没有可引用的本地 e-shuushuu 服务端源码，见[契约附注](docs/shuushuu-contract-notes.md)。
TBIB 首页明确标注 `Running Gelbooru 0.2`，帖子 JSON 可匿名读取，标签与评论在带 `json=1` 的实测中仍返回 XML。
独立的 `Gelbooru02` 保留这些差异，不把它套进当前 `gelbooru.com` 的 JSON 客户端，见[契约附注](docs/gelbooru02-contract-notes.md)。
Sakuria 不是 booru；它使用插画、小说、用户与 Pixivision 特辑模型。没有官方 API 页面、OpenAPI 或上游源码，
只凭匿名响应核对，证据等级最弱；未经本轮请求证实的输入说法单独标明，见[契约附注](docs/sakuria-contract-notes.md)。
Anime-Pictures 也不是 booru 引擎：站点自研一套 `api/v3` JSON 接口，**API 主机 `api.anime-pictures.net`
与网页主机 `anime-pictures.net` 分开**（网页主机被 Cloudflare 质询挡下，`/api/v3/*` 的 302 不要依赖），
根路径、帖子、标签、用户、评论各走自己的路由，不套 Danbooru/Moebooru 的参数名与字段。可读到的官方
API 手册页同样被质询挡下，也没有 OpenAPI 与服务端源码；依据只是匿名只读响应实测与候选输入资料
（输入引用了外部客户端源码链接，本轮没有独立读过），所以未实测项单独标明，见[契约附注](docs/anime-pictures-contract-notes.md)。
Cosine（`pic.cosine.ren`）是 Telegram 频道 `@CosineGallery` 的配套图站，同样不是 booru 引擎：Next.js +
Prisma + Meilisearch 自研 API，`api/list`、`api/artwork/{id}`、`api/random`、`api/search` 与
`api/search/suggestions`、`api/tag` / `api/tags`、`api/artist` / `api/artists`、`api/search/admin` 与
`feed.xml` 各走自己的路由，返回外壳有四种（superjson 的 `{"json":…,"meta":…}`、`{"images":…,"total":…}`、
`{"success":true,"data":…}` 与裸数组），本库一个都不拆。站点前端源码在公开仓库里，本轮只按需只读了个别
文件当线索（不 clone、不写行号），没有 OpenAPI 与服务端源码快照，公开结论以匿名只读响应为准，
未实测项单独标明，见[契约附注](docs/cosine-contract-notes.md)。
Nhentai（`nhentai.net`）是另一类独立契约：站点自带的 `.net` API v2（根路径 `https://nhentai.net/api/v2`）
把作品、搜索、标签与编辑建议分成 `/api/v2/galleries`、`/api/v2/search`、`/api/v2/tags/...`、
`/api/v2/taxonomy/...` 等路径，列表用 `page` + `per_page` 分页（作品每页上限 100、缺省 25），详情用
`include=comments,related,favorite,suggestions` 追加附加块，认证是 `Authorization: Key <key>`（大部分只读路由匿名可用）。
站点自带 OpenAPI（`GET https://nhentai.net/api/v2/openapi.json`，OpenAPI 3.1.0）是路径、参数与响应
schema 的第一依据，公开结论由匿名只读响应核对。`nhentai.to` 的作品编号与 HTML 数据结构不同，
不在本家族覆盖范围内；不做基址替换、ID 转换或回退，见[契约附注](docs/nhentai-contract-notes.md)。

ArtStation（`artstation.com`）是公开作品集站点，本类覆盖它的公开作品集 JSON 路由、只读搜索与一个 RSS 订阅源
（`artwork.rss`）：17 个原生方法 = 15 个 `GET` + 2 个 `POST`，其中 16 个返回 JSON、`feed()` 返回 RSS 原文。
两个 POST 都**不是**内容写入：`csrf_token()` 只是按调用方给的属性取公开 CSRF token，返回体里的
`public_csrf_token` 与站点会话 Cookie（由会话自然保存）配对；`project_search_post()` 是同一个搜索的只读 POST
形态，token由调用方每次传入，本库不自动获取、不续期、不重放、不重试、不落盘。本轮未取得官方API规范
或服务端源码，依据只有匿名响应，所以成功字段、状态码与排除项按实测边界写；固定作品详情
`/projects/{hash}.json` 实测被站点质询挡下（`403`），v2 单作品 `/api/v2/community/projects/{id}.json` 匿名
`401`，因此本类**没有封装** `project_show`。构造器与站点条目都没有凭据字段，不写数据、不下载媒体、
不重写媒体地址，见[契约附注](docs/artstation-contract-notes.md)。

- 版本：**0.1.0.dev1**（开发版，尚未发布到 PyPI）
- 许可：**MIT License**
- 上游：[LuqueDaniel/pybooru](https://github.com/LuqueDaniel/pybooru)（最后一次发版是 2020 年的 4.2.2）。
  本仓库重写了客户端（Danbooru 面 227 个方法、Moebooru 面 90 个方法）并新增 Serika、e621ng、Zerochan
  、Gelbooru、e-shuushuu、Gelbooru 0.2、Sakuria、Anime-Pictures、Cosine、Nhentai 与 ArtStation 十个家族，重构了配置、传输与错误处理；仓库原名 `pybooru`，现名 `anybooru`，版本号从 `0.1.0.dev1`
  重新起算。除 changelog 保留的历史记录外，**行为与上游不再一致**，用法以本仓库文档为准；
  原项目的 MIT 许可与版权声明保留在 [LICENSE](https://github.com/NebulaeWisdom/anybooru/blob/master/LICENSE)。

## 运行要求

- Python >= 3.6
- [requests](https://requests.readthedocs.io/) >= 2.26

## 安装

```bash
git clone https://github.com/NebulaeWisdom/anybooru.git
cd anybooru
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .        # Windows
.venv/bin/python -m pip install -e .                # Linux / macOS
```

装完不需要另外准备配置文件：包内自带一份可用的 `anybooru.json`。

## 配置

站点地址、凭据、代理、超时、User-Agent 与示例参数都在一份 JSON 里。这份文件**随包安装**，
`Danbooru('danbooru')` 这类调用默认读它；`anybooru.DEFAULT_CONFIG_FILE` 是它的路径。
`config_file` 指到的文件不存在时直接抛 `FileNotFoundError`，不会回落到默认文件或内置站点；
当前工作目录里的同名文件**不会**被自动读取；没有任何环境变量注入。

包内文件的开头长这样（`sites` 段一共 16 个条目，下面列出部分站点）：

```json
{
  "request": {
    "timeout": 30,
    "proxies": {},
    "user_agent": "Anybooru/0.1.0.dev1"
  },
  "sites": {
    "danbooru": { "url": "https://danbooru.donmai.us", "username": "", "api_key": "" },
    "yandere": { "url": "https://yande.re", "username": "", "password": "", "api_version": "1.13.0+update.3", "hash_string": "choujin-steiner--{0}--" },
    "zerochan": { "url": "https://www.zerochan.net" },
    "gelbooru": { "url": "https://gelbooru.com", "api_key": "", "user_id": "" },
    "tbib": { "url": "https://tbib.org" },
    "shuushuu": { "url": "https://e-shuushuu.net", "username": "", "password": "", "access_token": "" },
    "sakuria": { "url": "https://sakuria-api.syarolia.com", "access_token": "" },
    "anime_pictures": { "url": "https://api.anime-pictures.net/api/v3", "authorization": "", "cookie": "" },
    "cosine": { "url": "https://pic.cosine.ren", "revalidate_secret": "" },
    "nhentai": { "url": "https://nhentai.net", "api_key": "" },
    "artstation": { "url": "https://www.artstation.com" }
  }
}
```

- 用命名站点：`site_name` 是 `sites` 段的键，例如 `Danbooru('danbooru')`、`Moebooru('yandere')`、
  `Zerochan('zerochan')`、`Gelbooru('gelbooru')`、`Gelbooru02('tbib')`、`Shuushuu('shuushuu')`、`Sakuria('sakuria')`、`AnimePictures('anime_pictures')`、`Cosine('cosine')`、`Nhentai('nhentai')`、`ArtStation('artstation')`；条目里的 `url`、凭据与 `api_version` 按同名字段读入，
  显式构造参数优先。
- 用清单外的站点：直接给 `site_url=`，例如
  `Moebooru(site_url='https://example.org', api_version='1.13.0+update.3')`、`E621(site_url='https://e926.net')`。
  `sites` 段是**样例 / 起始清单，不是支持边界**。
- 改自己的配置：把包内那份复制成一份自己的，再把路径交给 `config_file=`，例如
  `Danbooru('danbooru', config_file='config/sites.json')`。默认 `request.proxies` 是 `{}`（不使用代理），
  需要代理时填成 `{"http": "http://proxy-host:port", "https": "http://proxy-host:port"}`。
- Zerochan 的 `User-Agent`：官方 API 页面要求请求头含**项目名与自己的 Zerochan 用户名**（例如
  `"My AI learning app - MyUsername"`）。它来自 `request.user_agent` 配置项，**不是认证凭据**，
  `Zerochan` 构造参数里没有 `username` / `api_key`。默认值 `Anybooru/0.1.0.dev1` 不含用户名，
  不满足页面的完整要求，请在自己的配置里补上（或给构造函数传 `user_agent=`）；匿名请求即使成功，
  仍有被封禁的风险。
- Gelbooru 的 `api_key` / `user_id`：两者都是**该站账号**的凭据，只加到 dapi 请求上（`page=dapi`），
  留空即匿名（匿名只能用 `autocomplete` 这类页面脚本接口，dapi 需要账号）。填好后本库会随 dapi 查询一起
  发送；这两项与 Danbooru 的 `username` + `api_key` 不是同一套东西，`user_id` 取的是该站的账号编号。
- e-shuushuu 默认匿名：公开图片、标签、评论、用户资料等读取不需要登录。`username/password` 只供显式
  `auth_login()` 使用，构造时即使填了它们也不登录；`access_token` 非空才随请求发 Bearer 头。
  登录、刷新、登出只为主动使用账号的人保留，本次没有调用，详见[客户端用法](docs/shuushuu.md)。
- Gelbooru 0.2 的 TBIB 条目只有 `url`：帖子、标签和空评论响应已取得匿名 200，不需要填账号。
  它与 `gelbooru` 条目分开，认证与其它同族站点未实测。
- Sakuria 使用 API 主机，默认 `access_token=''` 为匿名；非空才发送 `Authorization: Bearer`。
  17 个账号方法已封装，但成功返回结构未实测；不提供登录、注册或 token 刷新方法。
- Anime-Pictures 的条目 `url` 是 **API 基址** `https://api.anime-pictures.net/api/v3`，不是网页主机
  `anime-pictures.net`。凭据是 `authorization` 与 `cookie` 两个字段，默认 `""` 即匿名；非空时分别按原值
  发送 `Authorization` / `Cookie` 头，**不加 `Bearer`、不改写、不猜 cookie 名**。本类不提供登录、注册或
  刷新方法，凭据得自己准备；确切 scheme（`Bearer`、token 还是别的）未实测。
  匿名只读接口足以浏览帖子、标签、用户与评论；`post_tags`、`post_create` 与 `image_get` 需要身份，
  匿名拒绝形态见[错误处理](docs/errors.md)。
- Cosine 默认匿名：作品列表与详情、随机、搜索与建议、标签、画师、索引进度与 `feed.xml` 都不需要凭据。
  `revalidate_secret` 只供 `POST /api/artwork/revalidate` 使用，包内留空；构造时显式传
  `revalidate_secret=''` 表示本次固定发空密钥、**不读**配置里的值，`None`（或不传）才读配置。
  不用这个接口时，任何请求都不会带上它，也不会带别的认证头；该接口本轮从未调用，成功与拒绝形态都未实测。
  `POST /api/search/admin` 会重建或删除站点搜索索引，本轮**绝不会执行**，见[客户端用法](docs/cosine.md)。
- Nhentai 默认匿名：作品列表与详情、搜索、随机、标签与标签分类、编辑建议、CDN 与站点配置都不需要凭据。
  `api_key` 是唯一凭据字段，包内留空；构造时显式传 `api_key=''` 表示本次固定匿名、**不读**配置里的值，
  `None`（或不传）才读配置。非空时随每个请求发 `Authorization: Key <key>`，本类没有用户名/密码或用户令牌入口。
  `favorite_list`、`favorite_random`、`blacklist_list`、`blacklist_update`、`blacklist_ids`、`gallery_favorite`、
  `favorite_add`、`favorite_remove`、`gallery_download` 与 `user_me` 需要账号（API key 或该站用户令牌）：
  6 个只读方法的匿名请求各自得到 `401`，没有带凭据调用；站点第一方账号与用户令牌写操作（评论写入、
  标签分类写入、作品编辑、审核）不在覆盖范围内，见[客户端用法](docs/nhentai.md)。
- ArtStation 的条目**只有 `url`**：公开作品集路由、`artwork.rss` 订阅源与只读搜索 POST 都匿名可达，站点
  条目里没有凭据槽位，本类不自动生成认证头。只读搜索 POST 要的公开 CSRF token 由 `csrf_token()` 取回后
  由调用方每次传入，**不写进配置、不落盘、不自动获取或续期**。通用 `request()` 可显式带头调用未封装路由，
  但本库不代管登录，也不保证认证成功。

## 十二个家族的第一次调用

每段代码都可以直接复制执行（匿名只读），默认站点都来自包内配置。

### Danbooru 系站点

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:
    # GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=3
    # 帖子列表不读 search 字典：过滤条件写在 tags 里当元标签（rating:g、score:>10、order:score……）
    # 返回帖子字典数组，本调用用到 id、rating、tag_string（空格分隔的标签串）
    for post in client.post_list(tags='rating:g', limit=3):
        print(post['id'], post['rating'], post['tag_string'])

    # GET https://danbooru.donmai.us/posts/12211425.json
    # 单个帖子字典：另有 file_url、preview_file_url、md5、source、parent_id、created_at 等字段
    post = client.post_show(12211425)
    print(post['id'], post['file_url'], post['source'])
```

需要登录的写接口（评论、上传、编辑）在配置 `username` / `api_key` 后自动附加 HTTP Basic；凭据两项都空
才是匿名，权限由服务端判定，凭据无效返回 `401` 而不是静默降级。全部 227 个方法与逐条上游出处见
[docs/danbooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru-api.md)。

### Moebooru 系站点

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    # GET https://yande.re/post.json?tags=rating%3As&limit=3
    # 返回帖子字典数组，过滤条件（tags、limit、page）就是顶层参数，没有 search 字典
    # 每帖有 id、file_url、preview_url、sample_url、tags（空格分隔）、md5、width、height、source
    for post in client.post_list(tags='rating:s', limit=3):
        print(post['id'], post['file_url'])

    # Moebooru 没有 post_show（那条路由只有 HTML），单帖查询是 tags='id:1269034'
    # GET https://yande.re/post.json?tags=id%3A1269034
    print(client.post_list(tags='id:1269034')[0]['tags'])
```

认证不是 HTTP Basic：`password_hash = SHA1(hash_string.format(password))`，`username` 与 `password`
都为空才是匿名。90 个原生方法与逐条坑（`note_list` 按帖子分页、`wiki_update` 的 `new_title`、
重定向后的 `200` 不等于写入成功）见
[docs/moebooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru-api.md)。

### Serika（serika.art 及自托管实例）

```python
from anybooru import Serika

with Serika('serika') as client:
    # GET https://serika.art/api/v1/stats
    # 官方标准响应是 {"success": true, "data": {...}, "meta": {...}}，方法直接返回 data；
    # data["totals"] 是 {"images": 4237843, "tags": 730851, "users": 3059}（2026-09-17 实测值，
    # meta 留在 client.last_call['meta']）
    totals = client.stats()['totals']
    print(totals['images'], totals['tags'], totals['users'])

    # GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest
    # 站内私有面原样返回 {"success": true, "images": [...], "pagination": {...}}
    # id 是内部 bigint，post_id 是站内详情要用的公开顺序号，两者不能互换
    page = client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')
    for image in page['images']:
        print(image['id'], image['post_id'], image['rating'], image['url'])
```

官方 `/api/v1` 覆盖 16 个方法、站内匿名只读 14 个；官方需 API key 的 12 个方法只做源码对齐、未实测，
本库也不实现站内 cookie 登录。两者区别、返回形状与 ID 陷阱见
[docs/serika-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika-api.md)。

### e621ng 系站点

```python
from anybooru import E621

with E621('e621') as client:                       # 同一个类也能连 e926.net：E621('e926')
    # GET https://e621.net/posts.json?tags=rating%3As&limit=2
    # 服务端返回 {"posts": [...]}，方法直接把里面的数组给你
    # 每帖有 id、rating、file{url,ext,size,width,height,md5}、score{up,down,total}、
    # tags{general,artist,copyright,character,species,meta,...}（每类是标签名数组）
    for post in client.post_list(tags='rating:s', limit=2):
        print(post['id'], post['rating'], post['file']['url'], post['score']['total'])
```

评级词表是 e621 自己的 `rating:s` / `rating:q` / `rating:e`：写成 Danbooru 的 `rating:g` 时服务端**静默
忽略**该条件、不报错，返回的结果就是没过滤的。18 个原生只读方法的参数与返回形态见
[docs/e621-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621-api.md)。
需要成员权限的 `related_tag` / `related_tag_bulk` 只有源码依据，未取得过成功响应。

### Zerochan（zerochan.net）

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    # GET https://www.zerochan.net/?p=1&l=2&s=id&json=
    # 服务端返回 {"items": [...]}，方法把里面的数组给你：每项 id、width、height、md5、
    # thumbnail、source、tag（primary 标签名）、tags（标签名数组）；列表没有总数或页码字段
    for entry in client.entry_list(p=1, l=2, s='id'):
        print(entry['id'], entry['tag'], entry['width'], entry['height'])

    # GET https://www.zerochan.net/Genshin+Impact?l=2&json=
    # tags 传字符串＝单标签过滤（空格会编码成 +）；传列表＝多标签：entry_list(tags=['Lumine', 'Flower'])
    # strict 只保留 primary 标签就是所查标签的条目：entry_list(tags='Genshin Impact', strict=True)
    print([entry['id'] for entry in client.entry_list(tags='Genshin Impact', l=2)])

    # GET https://www.zerochan.net/3793685?json=
    # 详情返回单个条目字典：id、small/medium/large/full（四种尺寸的图片地址）、width、height、
    # size（字节数）、hash、source、primary（primary 标签名）、tags
    detail = client.entry_show(3793685)
    print(detail['primary'], detail['width'], detail['height'], detail['size'], detail['full'])
```

Zerochan 面只有 2 个原生方法，它们都是 `GET`，并且只收 JSON（`xml` 不在覆盖范围内）：
`entry_list(tags=None, strict=False, **params)` 与 `entry_show(entry_id)`。查询参数 `p` 页码、`l` 每页条数
（页面写的范围是 1–250）、`s` 排序（`id` 最新 / `fav` 最热）、`t` 人气窗口（`0` / `1` / `2`）、`d` 尺寸
（`large` / `huge` / `landscape` / `portrait` / `square`）、`c` 颜色原样传给服务端，客户端不补默认值。
页面写明限流 **60 请求/分钟**，客户端不做限速，示例脚本之间按配置的 `pause_seconds` 暂停。
`md5` 与 `hash` 都是服务端返回的字段，本库不计算校验值。
`l=2` 这类具体取值、每个可选参数的实测结果与那一条 `500` 都记在
[docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md)。

### Gelbooru（gelbooru.com）

```python
from anybooru import Gelbooru

with Gelbooru('gelbooru') as client:               # 包内 gelbooru 条目的 api_key / user_id 都为空
    # GET https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2
    # 匿名可达（不需要账号）：返回建议数组，每条含 type（本次为 tag）、
    # label（如 blue eyes）、value（如 blue_eyes）、post_count、category（如 tag / copyright）。
    # 注意 limit 不决定这次返回几条：实测 limit=3 仍然返回了 10 条；方法把服务端 JSON 原样给你，不拆外层。
    for suggestion in client.autocomplete('blue', type='tag', limit=3):
        print(suggestion['value'], suggestion['label'], suggestion['post_count'])

    # 需要该站账号的 dapi 查询（本仓库不带凭据，下面这行**未执行、未实测**）：
    # GET https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=2
    # client.post_list(limit=2)  要填好 sites.gelbooru 的 api_key 与 user_id 才能用
```

Gelbooru 面固定 **6 个原生只读方法**，全部是 `GET`，返回的 JSON **原样给你、不拆任何外层**（`autocomplete`
实测返回的就是一个建议数组；dapi 的返回结构还没实测）。

| 方法 | 请求 | 说明 |
| :--- | :--- | :--- |
| `autocomplete(term, **params)` | `index.php?term=<词>&…&page=autocomplete2` | 标签自动补全；**匿名可达**，是本家族唯一不需要账号的方法（实测 `limit` 不决定返回条数） |
| `post_list(**params)` | `index.php?page=dapi&s=post&q=index&json=1&…` | 帖子查询。`post_list(id=1)` 就是单帖查询，没有单独的 `post_show` |
| `post_deleted(**params)` | `index.php?page=dapi&s=post&q=index&deleted=show&json=1&…` | 已删除的帖子 |
| `tag_list(**params)` | `index.php?page=dapi&s=tag&q=index&json=1&…` | 标签查询 |
| `user_list(**params)` | `index.php?page=dapi&s=user&q=index&json=1&…` | 用户查询 |
| `comment_list(post_id, **params)` | `index.php?page=dapi&s=comment&q=index&json=1&post_id=<编号>&…` | 某帖的评论 |

只有 `page=dapi` 的请求会带 `json=1`。**本客户端使用两个 JSON 入口**：`page=dapi`（需要账号）与页面脚本用的
`page=autocomplete2`（匿名可达）；`page=tags/post/wiki` 等浏览路由返回 **HTML**，
本库没有抓取 HTML 的方法。dapi 的查询参数原样转发（`s` / `q` / `json`
由客户端补），本库不做参数校验、不补默认值、不拆外层、不猜返回结构。5 个 dapi 方法都需要 gelbooru.com
的账号（`api_key` + `user_id`），**匿名已逐个实测401、空正文；账号成功返回仍未实测**。`autocomplete` 已用匿名请求实测（`200`，
返回建议数组，且 `limit` 不决定条数——实测 `limit=3` 返回 10 条，逐条记录见
[docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md)）。
扩展实测中，九个脚本 `type` 的非空结果全部为 `type='tag'`；`user`、`pool` 等传参不代表返回了用户或池对象。
拼错 `taq` 与未列举的 `wiki` 也返回标签建议；逐项边界见[方法参考](docs/gelbooru-api.md)。
边界与来源见
[docs/gelbooru-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru-contract-notes.md)，
逐方法参数见
[docs/gelbooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru-api.md)。

### e-shuushuu（e-shuushuu.net）

```python
from anybooru import Shuushuu

with Shuushuu('shuushuu') as client:
    tag_results = client.search(q='long hair', limit=5)
    # GET https://e-shuushuu.net/api/v1/search?q=long+hair&limit=5
    for tag in tag_results['hits']:
        print(tag['tag_id'], tag['title'])

    images_response = client.image_list(tags='46', per_page=2)
    # GET https://e-shuushuu.net/api/v1/images?tags=46&per_page=2
    for image in images_response['images']:
        print(image['image_id'], image['url'], image['thumbnail_url'])
    print(images_response['total'], client.last_call['status_code'])
```

`search` 搜的是标签，不是图片；先由 `hits[].tag_id` 找 ID，再用 `image_list` 筛图。
多个 ID 写成 `tags='46,169', tags_mode='all'`，不能写 `46+169`；标签列表用 `per_page` 而非 `limit`。
客户端提供 36 个资源 GET 方法（其中 `user_ratings` 是私有数据）和 5 个显式认证方法，
全部保留完整 JSON，不自动分页或刷新 token；是否实际跑过，按方法参考的边界表与验证记录区分。
公共读接口的参数、返回字段见[方法参考](docs/shuushuu-api.md)，按目的查[能力入口](docs/shuushuu-capabilities.md)。

### Gelbooru 0.2（TBIB）

```python
from xml.etree import ElementTree
from anybooru import Gelbooru02

with Gelbooru02('tbib') as client:
    posts = client.post_list(tags='rating:safe', limit=2)
    # GET https://tbib.org/index.php?tags=rating%3Asafe&limit=2&s=post&q=index&page=dapi&json=1
    for post in posts:
        print(post['id'], post['width'], post['height'], post['rating'])

    tags_xml = client.tag_list(limit=2)
    # GET https://tbib.org/index.php?limit=2&s=tag&q=index&page=dapi
    # 返回的是完整 str；只有下面这行由调用方显式解析 XML。
    tags = ElementTree.fromstring(tags_xml)
    for tag in tags:
        print(tag.attrib['id'], tag.attrib['name'], tag.attrib['count'])
```

帖子默认返回完整 JSON 数组；`post_list(id=28627153, response_format='xml')` 可读取 XML 原文里的
`file_url/sample_url/preview_url`，不要拿 JSON 的 `directory/image/hash` 自行拼媒体地址。
标签与评论保留 XML 原文，不转字典、不拆根节点；HTTP 错误保留正文。
四个读取方法的参数、删除流 500 和补全 302 的边界见[方法参考](docs/gelbooru02-api.md)，
实跑结果见[验证记录](docs/verification.md#gelbooru02tbib匿名只读实测2026-09-19)。

### Sakuria（Pixiv 第三方镜像）

```python
from anybooru import Sakuria

with Sakuria('sakuria') as client:
    illusts = client.illust_search(q='blue', page=1, size=2)
    # GET https://sakuria-api.syarolia.com/search/illust?q=blue&page=1&size=2
    # 返回完整 {items, page, pageSize, total, totalPages, hasMore, nextPage, ...}，不取出 items 代替原对象。
    for illust in illusts['items']:
        print(illust['id'], illust['title'], illust['urls']['w'], illust['urls']['h'])
    print(client.last_call['status_code'], client.last_call['url'])
```

44 个原生 GET 覆盖插画、小说、用户、评论回复、系列、特辑、标签、统计与配置，以及 17 个账号入口。
不要把 `total` 当全库总量，不要按数值 `nextPage` 跳页；分页与字段事实见[方法参考](docs/sakuria-api.md)。
库不请求作品图片正文；相对图片地址的拼接与占位图注意事项见[客户端用法](docs/sakuria.md)。

### Anime-Pictures（anime-pictures.net）

```python
from anybooru import AnimePictures

with AnimePictures('anime_pictures') as client:
    # GET https://api.anime-pictures.net/api/v3/posts?search_tag=hatsune+miku&posts_per_page=2&order_by=rating&page=0
    # page 是必填的 0 起步页码，不传会得到 400；完整信封是 posts 数组加
    # page_number / posts_per_page / response_posts_count / posts_count（当前过滤条件下的总数）/ max_pages
    # 列表里的帖子不带预览地址；color 是数组，不是所有字段都是标量
    page = client.posts_list(search_tag='hatsune miku', posts_per_page=2, order_by='rating', page=0)
    for post in page['posts']:
        print(post['id'], post['score_number'], post['ext'], post['tags_count'])

    # GET https://api.anime-pictures.net/api/v3/posts/929452
    # 多段对象：post（比列表多 small_preview / medium_preview / big_preview 三个预览地址）、source、
    # user、moderator、tags（每项 {tag, user, relation}）、file_url（是文件名不是地址，含空格）、
    # star_it、favorites_users、tied
    detail = client.post_show(929452)
    print(detail['post']['id'], detail['file_url'], detail['user']['name'])
```

Anime-Pictures 面固定 **13 个方法（12 个 GET + 1 个 POST）**：根 `service_info()`（`GET https://api.anime-pictures.net/`
返回 `{"message": "Hello, World!"}`）、帖子 `posts_list` / `post_show` / `post_comments` / `post_tags`、
写入口 `post_create`（正文是调用方给你的 dict，原样作为 JSON 发送，可选 `Idempotency-Key` 头）、
标签 `tags_list` / `tag_show`、用户 `users_list` / `user_show`、评论 `comments_list` / `comment_show`，
以及 `image_get(file_url)`（`GET https://api.anime-pictures.net/pictures/get_image/<编码后的文件名>`，
原样返回 `bytes`，不解析、不嗅探、不落盘）。
有三处与其它家族**有意不同**：`url` 是 API 基址 `https://api.anime-pictures.net/api/v3`（不是网页主机），
所以 `'posts'` 这类相对路径拼在 `/api/v3` 后面，而 `'/api/v3/posts'` 和 `'/'` 是**主机根**路径；
帖子不存在返回 `410` 而不是 `404`；非法路径段返回 `400` 加 `text/plain` 正文而不是 JSON
（`AnybooruHTTPError.data` 此时是 `None`，`.body` 保留原文）。
分页要点：帖子列表的 `page` **0 起步且必填**——不传或非整数回 JSON `400`，`page=-1` 回 `500`；
`posts_per_page` 缺省 `80`，实测 `101` / `150` / `1000` / `0` 回落成 `60`、`-1` 回到 `80`；
标签 / 用户 / 评论列表改用 `limit` / `offset`（缺省 `20` / `0`），标签 `limit=1000` 与用户 / 评论 `limit=101`
都回到 `100`。列表里的 `score_number` 才是评分，`score` **不是恒为 `0.0`**，两个字段都按原值返回。
空结果（例如查一个不存在的标签）会回 `posts_count=0`、`max_pages=0`，别把 `max_pages` 当公式无条件套用。
用户对象也不同形：`users_list` 的条目与帖子详情里的 `user` 带 `login`，而 `user_show` 返回的 `user` 没有
`login`（顶层另有 `errormsg: null`）——跨路由取字段前先看清是哪一种。
`post_tags` 与 `image_get` 本轮匿名实测 `403`，`post_create` 没发过 POST、成功与拒绝形态都未实测；
带身份的成功路径、凭据 scheme 与媒体返回形态均未实测。方法参数见[方法参考](docs/anime-pictures-api.md)，
凭据字段见[认证](docs/authentication.md)，分页与错误见
[分页](docs/pagination.md#anime-pictures-的分页)与[错误处理](docs/errors.md#anime-pictures)。

### Cosine（pic.cosine.ren）

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    # GET https://pic.cosine.ren/api/list?page=1&pageSize=2
    # 外壳是 {"images": [...], "total": N}，方法原样给你这个对象，不剥层。
    # 每项 id 是站内自增编号，上游编号在 pid；size 为 null、guest 为 false 是新数据的样本值；
    # rawurl / thumburl 是图片地址，库不下载媒体。
    page = client.image_list(page=1, pageSize=2)
    for image in page['images']:
        print(image['id'], image['pid'], image['platform'], image['rawurl'])
    print(page['total'])

    # GET https://pic.cosine.ren/api/artwork/1
    # 另一种外壳：superjson 的 {"json": {...}, "meta": {...}}，作品对象在 ["json"] 里；
    # 详情不补 originUrl / authorUrl（只有 /api/random 会补这两个字段，并把 i.pximg.net 换成 piv.cosine.ren）
    artwork = client.artwork_show(1)['json']
    print(artwork['id'], artwork['size'], artwork['guest'], artwork['tags'])

    # GET https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2
    # 第三种外壳：{"success": true, "data": {...}}；hits 里的 id 是字符串、tags 是数组。
    # total 是 Meilisearch 的估计值并被服务端夹到 1000，不能当全库总量。
    result = client.search(q='初音', limit=2)['data']
    print(result['total'], [hit['id'] for hit in result['hits']])
```

Cosine 面固定 **13 个原生方法（11 个 GET + 2 个 POST）**，返回四种外壳**全部原样**给你：`image_list` 的
`{"images":…,"total":…}`、`artist_list` 的 `{"artists":…,"total":…,"hasNextPage":…}`、`artwork_show` 与
`image_random` 的 superjson `{"json":…,"meta":…}`、`search` / `search_suggestions` / `search_index_status`
的 `{"success":true,"data":…}`，以及 `tag_images` 与 `tag_list` 的**裸数组**。
`artist_images(infoOnly=True)` 返回的是第五种形状——不在上面四种列表外壳内的**裸画师资料对象**
（`{author, authorid, platform, artworkCount}`），且资料里的 `author` 可能与作品列表里的名字不同。

分页有三套参数：`image_list` / `artist_list` 用 `page`（1 起）+ `pageSize`，`search` 用 `limit` + `offset`，
`tag_images` 用 `start` + `limit`。`search` 的 `total` 被夹在 1000、`offset` 也被夹到 1000，**不能用来算翻页**；
`tag_images` / `tag_list` 没有 `total`，是否到底只能看返回空数组。`tag_list` 的 `count` 是标签行数，
**不是**用了该标签的作品数，两种口径不能换算。
边界样本同样照实写：`image_list?page=0` 与 `page=-1` 是 `500`（不是 `400`），翻过末页却是 `200` 加空 `images`，
`pageSize=-1` 回的是最旧的 1 条、`pageSize=0` 回空数组（站点自己的语义，客户端不拦）；
`image_random` 的 `count` 由**站点**夹在 1–20（`count=0` 与 `-5` 回的是 1 条那种对象形状、`count=100` 回 20 条），
非数字 `count` 是 `404`；样本里的 id 是升序，但站点这条查询没有排序子句，**不保证任何顺序**；`search` 的 `limit=-1`、`offset=-5` 与 `sort=bogus` 都是 `500`。
逐条参数与样本见[方法参考](docs/cosine-api.md)，分页见[分页](docs/pagination.md#cosine-的分页)。

`feed()` 用 `response_format='xml'` 返回 `feed.xml` 的**完整 XML 原文**（不解析、不转字典；`response_format`
只认 `'json'` 与 `'xml'`，其它值直接抛 `KeyError`，客户端不看 `Content-Type` 猜格式）。样本的 `lastBuildDate`
与首几条 `guid` 都明显早于同一时刻列表里的最新编号，所以**别把 `feed` 当“当前最新 20 条”**，它只是站点缓存里的
那批 RSS；`/rss`、`/rss.xml`、`/feed` 这些别名本轮没有请求。
`artwork_revalidate(artwork_id, secret=None)` 是本站唯一需要密钥的 POST，密钥留空就照发空串、由站点判定
（本轮未调用）。`search_index_admin(action)` 会**重建或删除站点搜索索引**，本轮探测显示该路由没有鉴权门槛，
所以本库不做任何自动重试或兜底，示例与冒烟都不调用它。错误样本（缺失作品 `404`、缺必填参数 `400`、
非数字路径段与 `page=0` 一类 `500`）与状态码含义见[错误处理](docs/errors.md#cosine)，凭据语义见
[认证](docs/authentication.md)，可调用能力见[能力入口](docs/cosine-capabilities.md)。

### Nhentai（nhentai.net）

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:                 # 包内 nhentai 条目的 api_key 留空即匿名
    # GET https://nhentai.net/api/v2/galleries?per_page=2
    # 方法原样返回整个信封：result 是作品数组，另有 num_pages / per_page / total。
    # 每项有 id（作品编号，详情路由与收藏都用它）、media_id（拼图片地址的字符串）、num_pages、
    # num_favorites、thumbnail 与 thumbnail_width / thumbnail_height、tag_ids（标签编号数组）、blacklisted
    page = client.gallery_list(per_page=2)
    for gallery in page['result']:
        print(gallery['id'], gallery['media_id'], gallery['num_pages'], gallery['num_favorites'])
    print(page['num_pages'], page['per_page'], page['total'])

    # GET https://nhentai.net/api/v2/galleries/658856?include=related
    # 详情是另一套对象：cover / thumbnail 各含地址与宽高，pages 是每页对象数组（页码与地址），
    # tags 是标签对象数组（id / type / name / slug / url / count），另有 num_pages、num_favorites、
    # upload_date、scanlator；include= 用逗号串追加 comments / related / favorite / suggestions 附加块，
    # 不传就不请求（这几个附加字段会是 null）
    detail = client.gallery_show(658856, include='related')
    print(detail['id'], detail['num_pages'], detail['num_favorites'], len(detail['pages']), len(detail['tags']))
```

Nhentai 面固定 **36 个原生方法（31 个 GET、4 个 POST、1 个 DELETE）**，返回的 JSON **完整原样**给你、不剥层。
作品列表、搜索结果与作品评论列表都是 `{"result": [...], "num_pages": …, "per_page": …, "total": …}`
（`total` 可以是 `null`）；`gallery_related(gallery_id)` 是只有 `result` 的对象；标签列表在 `sort=name` 时才多一个
`alphabet`（默认排序没有）；`gallery_popular()` 返回**裸作品数组**，`tag_show(tag_type, slug)` 返回裸标签对象，
`tag_ids(ids)` 返回裸标签数组，`blacklist_ids()` 返回整数数组，`gallery_random()` 返回 `{"id": …}` 那样的
随机作品对象，`user_me()` 返回用户对象——形状各不相同，方法都照原样返回，不猜、不拆。

分页不是统一规则：`gallery_list` 使用 `page` 与 `per_page`，而 `search` 只声明
`query`、`sort` 与 `page`，不声明 `per_page`。标签列表和已解决的 taxonomy 列表可能不采纳
请求条数；计数与总页数也可能不一致。请按[分页说明](docs/pagination.md#nhentai-的分页)
选择明确的页码，不用总数除法或短页作为通用终止条件。

`favorite_list`、`favorite_random`、`blacklist_list`、`blacklist_update`、`blacklist_ids`、`gallery_favorite`、
`favorite_add`、`favorite_remove`、`gallery_download` 与 `user_me` 这 10 个方法需要账号（API key 或该站
用户令牌）：其中 6 个只读方法的匿名请求各自得到 `401` 加 `{"error": "Authentication required"}`，
4 个写与下载地址分配动作没有执行。`gallery_download(gallery_id)` 返回的是下载地址与过期时间一类的对象，
库只给这个对象、**不下载媒体**。`tag_search(**attributes)` 是 POST 但**不需要认证**（按前缀查标签，正文是 JSON），
本轮也没有发过 POST。本类唯一的凭据字段是 `api_key`，非空时发送 `Authorization: Key <key>`，
不提供用户名/密码或用户令牌入口；第一方账号与用户令牌写操作、PoW/captcha 与广告位都不封装。

逐方法参数见[方法参考](docs/nhentai-api.md)，按目的查找见[能力入口](docs/nhentai-capabilities.md)，
依据与排除项（含 `.to` 克隆站）见[契约附注](docs/nhentai-contract-notes.md)，逐条请求记录见[验证记录](docs/verification.md)。
冒烟脚本与两个示例已经匿名真跑：`test/nhentai.py` 的 10 次请求 10 项检查全部通过、
`examples/nhentai/list_galleries.py` 三次 `200`、`examples/nhentai/browse_resources.py` 五次 `200`，
三个脚本退出码都是 `0`；经 Python 实际执行到的原生方法共 9 个，另外 22 个只到路由级直接请求。

### ArtStation（artstation.com）

```python
from anybooru import ArtStation

with ArtStation('artstation') as client:
    # GET https://www.artstation.com/projects.json?page=1&per_page=2
    # 服务端返回 {"data": [...], "total_count": N}，方法原样给你这个对象，不剥 data 层。
    # 全站列表的条目样本含 id、hash_id、title、permalink、cover、assets_count 与 tag_list
    #（样本里 tag_list 是 null，不能据此认为它恒为 null 或恒为数组）。
    page = client.project_list(page=1, per_page=2)
    for project in page['data']:
        print(project['id'], project['hash_id'], project['title'], project['permalink'])
    print(page['total_count'])

    # GET https://www.artstation.com/users/timwarnock/projects.json?page=1&per_page=2
    # 用户作品列表是同一族的另一套条目字段：样本里没有 user 与 views_count，
    # 不要拿全站列表的字段清单去要求这个路由。
    user_page = client.user_projects('timwarnock', page=1, per_page=2)
    print([project['id'] for project in user_page['data']], user_page['total_count'])

    # GET https://www.artstation.com/api/v2/search/projects.json?query=&page=1&per_page=3&sorting=relevance
    # 搜索外壳同样是 {"total_count": N, "data": [...]}；filters 是 JSON 字符串，不是嵌套对象。
    hits = client.project_search(query='', page=1, per_page=3, sorting='relevance')
    print(hits['total_count'], [item['hash_id'] for item in hits['data']])

    # GET https://www.artstation.com/artwork.rss?sorting=latest
    # response_format='xml' 走 .text，返回订阅源原文（不解析、不转 JSON、不看 Content-Type 猜格式）
    feed_xml = client.feed(sorting='latest')
    print(len(feed_xml), feed_xml[:60])

    # 只读 POST 形态（不是内容写入），两步由调用方自己串：同一个 client 才有配对的会话 Cookie
    # POST https://www.artstation.com/api/v2/csrf_protection/token.json（JSON 正文是原样的属性）
    public_token = client.csrf_token(create_csrf_token_request='true')['public_csrf_token']
    # POST https://www.artstation.com/api/v2/search/projects.json
    # token 由调用方每次传入，只放本次调用的 PUBLIC-CSRF-TOKEN 头；表单编码走共享编码器。
    # additional_fields 只是让这次搜索的结果多带 assets / description，不是按 id 取某个作品的入口。
    posted = client.project_search_post(
        public_token, query='cat', page=1, per_page=3, sorting='relevance',
        additional_fields=['assets', 'description'],
    )
    print(posted['total_count'], [item['hash_id'] for item in posted['data']])
```

ArtStation 面固定 **17 个原生方法（15 个 `GET` + 2 个 `POST`）**：16 个返回 JSON、`feed()` 返回
`artwork.rss` 的 RSS 原文；原有的 `project_search()` 仍是 `GET`，本次没有改动。范围是**公开作品集资源、
只读搜索与订阅源**：作品列表与随机作品，用户资料三面
（`user_show` / `user_quick` / `user_profile`）、用户作品与关注，搜索（`project_search` 与只读的
`project_search_post`）与可搜索字段（`search_filter_fields`），专辑作品（`album_projects`），频道列表与
频道作品（`channel_list` / `channel_projects`），作品评论（`project_comments`）、探索最新（`explore_latest`）、
`feed()`，以及取公开 CSRF token 的 `csrf_token()`。
**两个 POST 都不是内容写入**：`csrf_token(**attributes)` 把属性原样作为 JSON 正文 POST 到
`api/v2/csrf_protection/token.json`，返回体里的 `public_csrf_token` 由调用方保存，站点会话 Cookie 由会话
自然保存；`project_search_post(public_csrf_token, **params)` 用同一个 `ArtStation` 实例发出表单编码的只读
搜索 POST，token 只放本次调用的 `PUBLIC-CSRF-TOKEN` 头。token **必须由调用方传入**，本库不自动获取、不续期、
不重放、不重试，也不把它存成配置项或对象属性。`request()` 除 `data`（JSON 正文）外新增 `form=`（共享编码器编出的
Rails 表单），选哪个由调用方决定，不做本地校验、不补默认值、不回退。
构造器与站点条目**都没有凭据字段**：不做登录、不写数据、不下载媒体、不拼接或改写媒体地址；固定作品详情
`/projects/{hash}.json` 实测被站点质询挡下（`403`，HTML），v2 的单作品 `/api/v2/community/projects/{id}.json`
匿名返回 `401`，所以本类**没有封装** `project_show`——确需那两条路由时用通用 `request()` 显式调用。
`project_search` 缺 `per_page` 时服务端回 `400`（正文是 `{"data":"per_page should be given"}`），异常原样
抛出。`project_search_post()` 的 `additional_fields=['assets','description']` 只是要求服务端在**这次查询的结果**
里多带这两个字段；专辑作品与随机作品本来就带 `assets`，它**不是**按作品 id 取任意作品的入口。
已跟到的 POST 样本：`csrf_token()` 是 `200` 加 `application/json`，正文顶层只有 `public_csrf_token`
（字符串），响应里出现的 Cookie（`PRIVATE-CSRF-TOKEN`）由会话自然保存、值不落盘；`project_search_post()` 是
200、响应application/json；请求正文为application/x-www-form-urlencoded（additional_fields[]为重复键），外壳是
`{"total_count":…,"data":[…]}`，本次 3 条结果的条目都带 `assets` 与 `description`（`assets` 里有图片与
video 条目，字段含 `asset_type`、`width`、`height`、`small_image_url`、`large_image_url`）。
缺 token、过期 token、其它 `filters` 形状与 `412` 一类 POST 边界**仍未实测**。
本轮**未取得 ArtStation 官方 API 文档页、OpenAPI 或服务端源码**，公开结论以匿名只读响应为准；
`sorting` 只实测过 `relevance`，订阅源只实测过 `latest`，样本之外的取值、以及 POST 表单里 `filters` 的嵌套
形状都按候选处理。逐方法参数见[方法参考](docs/artstation-api.md)，按任务查[能力入口](docs/artstation-capabilities.md)，
依据与排除项见[契约附注](docs/artstation-contract-notes.md)。

## 文档

文档全部是 `docs/` 下的中文 Markdown，每份只回答一类问题：

| 文档 | 内容 |
| :--- | :--- |
| [docs/index.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/index.md) | 导航：想做什么 → 读哪份；十二个家族怎么选 |
| [docs/installation.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/installation.md) | 安装、Python 与 requests 版本、配置文件放在哪 |
| [docs/configuration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/configuration.md) | `anybooru.json` 完整样例、`config_file` 覆盖、`sites` 段语义与引擎判别 |
| [docs/authentication.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/authentication.md) | 各家族的认证形态：HTTP Basic、密码哈希、Bearer、查询凭据；Sakuria 只接收已有 token，Anime-Pictures 原样转发 `Authorization` / `Cookie`，Cosine 默认匿名且 `revalidate_secret` 留空，Nhentai 默认匿名且 `api_key` 非空时发 `Authorization: Key <key>`，ArtStation 站点条目无凭据字段且公开 CSRF token 按次传入 |
| [docs/pagination.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/pagination.md) | 各引擎的页码、`limit` 与游标写法，含 Anime-Pictures 的 0 起步 `page`、Cosine 的 `page`/`pageSize`、`limit`/`offset` 两套，以及 Nhentai 的 `page`/`per_page` 与 ArtStation 的 `page`/`per_page` |
| [docs/errors.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/errors.md) | `AnybooruHTTPError` / `AnybooruAPIError`、状态码与错误正文 |
| [docs/danbooru.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru.md) | Danbooru 客户端：构造、`request()`、参数编码、返回值、坑 |
| [docs/danbooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru-api.md) | Danbooru 227 个方法：参数、路由、返回形态 |
| [docs/danbooru-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru-capabilities.md) | Danbooru：想做的事 → 用哪个方法（含完整方法索引） |
| [docs/danbooru-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/danbooru-contract-notes.md) | Danbooru 契约出处、权限分支与排除项 |
| [docs/moebooru.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru.md) | Moebooru 客户端：构造、认证、`request()`、坑 |
| [docs/moebooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru-api.md) | Moebooru 90 个方法：参数、路由、返回形态 |
| [docs/moebooru-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru-capabilities.md) | Moebooru：想做的事 → 用哪个方法 |
| [docs/moebooru-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/moebooru-contract-notes.md) | Moebooru 上游文件与行号、权限与排除项 |
| [docs/serika.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika.md) | Serika 客户端：两面路由、返回形状、二进制响应 |
| [docs/serika-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika-api.md) | Serika 官方 v1 与站内方法：参数、权限与文档矛盾 |
| [docs/serika-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika-capabilities.md) | Serika：两层能力与匿名可读范围 |
| [docs/serika-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/serika-contract-notes.md) | Serika 路由逐条状态与排除项 |
| [docs/e621.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621.md) | e621ng 客户端：认证、请求信封规则、评级词表 |
| [docs/e621-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621-api.md) | e621ng 18 个原生只读方法：参数与返回形态 |
| [docs/e621-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621-capabilities.md) | e621ng：想做的事 → 用哪个方法 |
| [docs/e621-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/e621-contract-notes.md) | e621ng 上游出处、搜索字段与可见性约束 |
| [docs/zerochan.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan.md) | Zerochan 客户端：URL 形态、参数编码、`request()` |
| [docs/zerochan-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-api.md) | Zerochan 两个原生方法：参数、路由与返回字段 |
| [docs/zerochan-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-capabilities.md) | Zerochan：想做的事 → 用哪个方法 |
| [docs/zerochan-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-contract-notes.md) | Zerochan 页面原文出处、与实现的差异、排除项（`xml`、meta 标签） |
| [docs/gelbooru.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru.md) | Gelbooru 客户端：`index.php` 的 page 参数、凭据与 `request()` |
| [docs/gelbooru-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru-api.md) | Gelbooru 6 个原生方法：参数、URL 与返回形态（dapi 需账号） |
| [docs/gelbooru-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru-capabilities.md) | Gelbooru：想做的事 → 用哪个方法、哪些匿名可用 |
| [docs/gelbooru-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru-contract-notes.md) | Gelbooru 的来源层级、dapi 与 HTML 页面的边界、未实测项 |
| [docs/shuushuu.md](docs/shuushuu.md) | e-shuushuu 客户端：匿名默认、显式认证、逗号串与重复查询键 |
| [docs/shuushuu-api.md](docs/shuushuu-api.md) | 36 个资源读取（含私有 user_ratings）与 5 个认证方法的参数、路由和 JSON 字段 |
| [docs/shuushuu-capabilities.md](docs/shuushuu-capabilities.md) | e-shuushuu：按目的选方法与完整索引 |
| [docs/shuushuu-contract-notes.md](docs/shuushuu-contract-notes.md) | OpenAPI 依据、权限分支、排除项及资料差异 |
| [docs/gelbooru02.md](docs/gelbooru02.md) | Gelbooru 0.2 客户端：匿名 TBIB、JSON 与原样 XML 字符串 |
| [docs/gelbooru02-api.md](docs/gelbooru02-api.md) | 四个读取方法的参数、格式差异与站点异常 |
| [docs/gelbooru02-capabilities.md](docs/gelbooru02-capabilities.md) | Gelbooru 0.2：按目的选方法、未封装入口 |
| [docs/gelbooru02-contract-notes.md](docs/gelbooru02-contract-notes.md) | TBIB 版本证据、帮助页与响应矛盾、同族边界 |
| [docs/sakuria.md](docs/sakuria.md) | Sakuria 客户端：API 主机、已有 token、完整 JSON 与媒体地址 |
| [docs/sakuria-api.md](docs/sakuria-api.md) | 27 个公共读取与 17 个账号方法的参数、路由和字段 |
| [docs/sakuria-capabilities.md](docs/sakuria-capabilities.md) | Sakuria：按目的选方法与完整索引 |
| [docs/sakuria-contract-notes.md](docs/sakuria-contract-notes.md) | 匿名响应依据、输入资料矛盾与未实测范围 |
| [docs/anime-pictures.md](docs/anime-pictures.md) | Anime-Pictures 客户端：API 基址、前缀 `/` 语义、原样凭据头与完整 JSON |
| [docs/anime-pictures-api.md](docs/anime-pictures-api.md) | 13 个原生方法（12 GET + 1 POST）：参数、路由与返回字段 |
| [docs/anime-pictures-capabilities.md](docs/anime-pictures-capabilities.md) | Anime-Pictures：按目的选方法与完整索引 |
| [docs/anime-pictures-contract-notes.md](docs/anime-pictures-contract-notes.md) | 匿名响应依据、输入资料矛盾、未实测项与排除路由 |
| [docs/cosine.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/cosine.md) | Cosine 客户端：四种返回外壳、三套分页参数、`request()` 与危险索引入口 |
| [docs/cosine-api.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/cosine-api.md) | 13 个原生方法：参数、路由与返回字段 |
| [docs/cosine-capabilities.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/cosine-capabilities.md) | Cosine：按目的选方法、匿名可读范围与两个 POST 入口 |
| [docs/cosine-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/cosine-contract-notes.md) | 匿名响应依据、上游前端文件、排除项与未实测项 |
| [docs/nhentai.md](docs/nhentai.md) | Nhentai 客户端：站点根与 `api/v2` 路径、`Key` 认证、`request()`、分页与坑 |
| [docs/nhentai-api.md](docs/nhentai-api.md) | 36 个原生方法（31 GET + 4 POST + 1 DELETE）：参数、路由与返回字段 |
| [docs/nhentai-capabilities.md](docs/nhentai-capabilities.md) | Nhentai：按目的选方法、匿名可读范围与需账号的方法 |
| [docs/nhentai-contract-notes.md](docs/nhentai-contract-notes.md) | OpenAPI 条目依据（JSON Pointer / operationId）、权限分支、排除项与未实测项 |
| [docs/artstation.md](docs/artstation.md) | ArtStation 客户端：路径拼接、`request()` 的 `data` / `form`、RSS 原文与按次传入的 CSRF token |
| [docs/artstation-api.md](docs/artstation-api.md) | 17 个原生方法（15 GET + 2 POST）：参数、路径、请求头与返回字段 |
| [docs/artstation-capabilities.md](docs/artstation-capabilities.md) | ArtStation：按目的选方法、公开作品集、只读搜索与订阅源范围 |
| [docs/artstation-contract-notes.md](docs/artstation-contract-notes.md) | 匿名响应依据、工作范围、排除路由与未实测项 |
| [docs/migration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/migration.md) | 从上游 4.x 迁移到 0.1.x 的逐项对照 |
| [docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md) | 哪些端点真的跑过（含状态码与返回摘要）、哪些没有 |

## 可运行示例

`examples/` 下 33 个脚本都按家族分目录，全部支持 `--config` 与 `--site`；省略 `--config` 就读包内默认配置，
站点名与参数（标签、页码、条数、间隔）取自 `examples.<家族>` 段——例如上面 Zerochan 那段的
`entry_list(p=1, l=2, s='id')` 对应 `examples.zerochan.entry_query`，`entry_show(3793685)` 对应
`examples.zerochan.entry_id`。示例里不硬编码站点、代理与分页。

| 目录 | 脚本 |
| :--- | :--- |
| `examples/danbooru/` | `list_posts.py`（帖子列表）、`show_post.py`（单帖详情）、`list_tags.py`（标签搜索）、`paginate_posts.py`（数字 `page` 翻页与 `page='b<id>'` 取更旧帖子）、`related_tag.py`（相关标签）、`wiki_page.py`（按标题读 wiki 正文）——六个匿名只读脚本 |
| `examples/danbooru/comment_create.py` | **真实的 POST 写示例**：发表评论，需要账号与 API key，本仓库不带凭据，**未执行、未实测** |
| `examples/moebooru/` | `list_posts.py`（两页帖子与文件地址）、`list_tags.py`（标签与计数）、`wiki_list.py`（wiki 标题搜索）、`list_comments.py`（评论流条数，当前观察到 0 条）、`related_tags.py`（相关标签）——五个匿名只读脚本 |
| `examples/serika/` | `service_info.py`（官方索引、统计、用户目录）、`browse.py`（站内图片列表与详情、标签、画师）、`random_image.py`（读官方随机图片字节并打印 Content-Type，不落盘）——三个匿名只读脚本 |
| `examples/e621/` | `list_posts.py`（帖子列表、单帖、随机帖）、`browse_resources.py`（标签、画师、评论、合集、笔记）、`wiki_pages.py`（wiki 列表与按标题取页）——三个匿名只读脚本 |
| `examples/zerochan/` | `list_entries.py`（条目列表与单条目详情）、`filter_entries.py`（单标签、多标签、`strict` 三种过滤）——两个匿名只读脚本，调用之间按 `pause_seconds` 暂停 |
| `examples/gelbooru/` | `autocomplete.py`（标签自动补全，打印建议条数与全部建议、`last_call` 的真实 URL 与状态码）——一个匿名只读脚本；dapi 的 5 个方法需要账号，没有成功调用示例，匿名拒绝见验证记录 |
| `examples/shuushuu/` | `search_images.py`（标签名换 ID、两页筛图、详情）、`browse_resources.py`（标签详情、评论、用户、新闻）——两个匿名只读脚本，各最多四次 GET |
| `examples/gelbooru02/` | `list_posts.py`（JSON 列表与同帖 XML）、`browse_resources.py`（XML 标签与评论）——两个匿名脚本，各最多两次 GET |
| `examples/sakuria/` | `search_illusts.py`（两页搜索与 ID 去重）、`browse_resources.py`（插画详情、评论与作者）——两个匿名脚本，分别最多两次与三次 GET |
| `examples/anime_pictures/` | `list_posts.py`（配置的两页帖子列表，打印真实 URL、状态、`page_number`、`posts_count`、`max_pages` 与每帖 `id` / `score_number`）、`browse_resources.py`（帖子详情、该帖评论、详情里 `user.id` 的用户资料、非空评论首条的评论详情）——两个匿名只读脚本，分别两次与四次 GET，不访问媒体 |
| `examples/cosine/` | `list_images.py`（配置的两页 `image_list` 与两个 `offset` 的搜索）、`browse_resources.py`（作品详情、标签筛图、画师作品与 `infoOnly=True` 的画师资料）——两个匿名只读脚本，各四次 GET，调用之间按 `pause_seconds` 暂停，不下载媒体 |
| `examples/nhentai/` | `list_galleries.py`（配置的两页 `gallery_list` 与一次 `search`，共三次 GET）、`browse_resources.py`（作品详情、标签详情、多标签编号查询、作品评论与站点配置，共五次 GET）——两个匿名只读脚本，先打印真实 URL、状态码与 `Content-Type` 再取字段，调用之间按 `pause_seconds` 暂停，不下载媒体 |
| `examples/artstation/` | `list_projects.py`（配置的两页全站作品列表与两页过滤搜索）、`browse_resources.py`（用户资料、配置专辑的作品、随机作品与配置作品的评论）——两个匿名只读脚本，各四次 GET，调用之间按 `pause_seconds` 暂停，不下载媒体、不调用被站点挡下的详情路由 |

```bash
.venv/Scripts/python.exe examples/danbooru/list_posts.py
.venv/Scripts/python.exe examples/moebooru/list_posts.py
.venv/Scripts/python.exe examples/serika/service_info.py
.venv/Scripts/python.exe examples/e621/list_posts.py
.venv/Scripts/python.exe examples/zerochan/list_entries.py
.venv/Scripts/python.exe examples/gelbooru/autocomplete.py
.venv/Scripts/python.exe examples/shuushuu/search_images.py
python examples/gelbooru02/list_posts.py
python examples/sakuria/search_illusts.py
.venv/Scripts/python.exe examples/anime_pictures/list_posts.py
.venv/Scripts/python.exe examples/anime_pictures/browse_resources.py
.venv/Scripts/python.exe examples/cosine/list_images.py
.venv/Scripts/python.exe examples/cosine/browse_resources.py
.venv/Scripts/python.exe examples/nhentai/list_galleries.py
.venv/Scripts/python.exe examples/nhentai/browse_resources.py
python examples/artstation/list_projects.py
python examples/artstation/browse_resources.py
```

哪些脚本真的跑过、每条命令的状态码与返回摘要，见
[docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md)。

## 轻量匿名冒烟检查

安装本包后，可单独运行 `test/<站点>.py`，快速检查导入、配置与客户端构造，以及少量 API 的字段类型、
列表条数、分页、详情编号和预期错误。文件名对应 `sites`：`serika`、`danbooru`、`safebooru`、
`konachan`、`yandere`、`sakugabooru`、`e621`、`e926`、`zerochan`、`gelbooru`、`shuushuu`、`tbib`、
`sakuria`、`anime_pictures`、`cosine`、`nhentai`、`artstation`。

```bash
python test/danbooru.py
python test/zerochan.py --config <你的配置文件>
python test/gelbooru.py --config <你的配置文件>
python test/tbib.py --config <你的配置文件>
python test/sakuria.py --config <你的配置文件>
python test/anime_pictures.py --config <你的配置文件>
python test/cosine.py --config <你的配置文件>
python test/nhentai.py --config <你的配置文件>
python test/artstation.py --config <你的配置文件>
```

全部匿名、只发 GET，不需要账号，脚本显式禁用配置中的凭据；不登录、不写入、不下载媒体、
不重试、不跟随重定向、不切换站点。每站最多 10 次请求：Shuushuu、Sakuria、Cosine、Anime-Pictures、Nhentai 与 ArtStation 最多 10 次、Serika 最多 5 次、Gelbooru 与 TBIB 最多 6 次，
其余各最多 4 次；前置列表失败时跳过依赖的详情/翻页，不补发请求。两次请求之间按配置暂停：
通用 `smoke.pause_seconds=1.2`，Shuushuu 用 `smoke.shuushuu.pause_seconds=2.1`，Sakuria 用 `smoke.sakuria.pause_seconds=1.2`，
Anime-Pictures 用 `smoke.anime_pictures.pause_seconds=1.3`，Cosine 用 `smoke.cosine.pause_seconds=1.3`；
Nhentai 没有自己的 `pause_seconds`，用通用的 `smoke.pause_seconds=1.2`，ArtStation 用 `smoke.artstation.pause_seconds=1.3`。不依赖测试框架，不在 CI 自动运行。

每条检查输出 `PASS` / `FAIL`、真实 URL、HTTP 状态或异常及关键字段/条数，最后汇总实际尝试次数；
退出码 `0` 表示本次全部符合预期，`1` 表示失败或漂移。Gelbooru 五个 dapi 的匿名 `401` 空正文是
**预期拒绝**，不是失败；Anime-Pictures 的缺失帖子 `410` 与非法路径段 `400`（正文是 `text/plain`、
`AnybooruHTTPError.data` 为 `None`）、Cosine 查缺失作品的 `404`、Nhentai 查缺失作品的 `404` 与非法 `page`
（例如 `page=0`）的 `400`、ArtStation 的缺失用户名 `404`（`text/plain` 空正文）与非法搜索参数的 `400`
同样是**预期拒绝**，不是失败；网络失败也不会伪装成站点变化。
这里不是全 API 覆盖或长期可用性保证。

省略 `--config` 时读包内默认配置（不含代理）；若所在网络需要代理，必须用 `--config` 指向自己的
完整配置。复制最新版 `anybooru/anybooru.json`，保留其中的 `smoke` 段，仅调整自己的 `request` 设置；
不会合并旧配置或读取环境变量。参数说明见[配置文档](docs/configuration.md#smoke-段)，
一次完整执行的结果见[验证记录](docs/verification.md)。脚本随仓库与源码分发包提供，不放入 wheel。

## 贡献

请在动手前阅读 **[CONTRIBUTING.md](https://github.com/NebulaeWisdom/anybooru/blob/master/CONTRIBUTING.md)**。

## 许可

- **[MIT License](https://github.com/NebulaeWisdom/anybooru/blob/master/LICENSE)**
