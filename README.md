# Anybooru - Danbooru / Moebooru / Serika / e621ng / Zerochan / Gelbooru / e-shuushuu / Gelbooru 0.2 / Sakuria / Anime-Pictures / Cosine / Nhentai / ArtStation 图站 API 客户端

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/NebulaeWisdom/anybooru/master/LICENSE)

**Anybooru** 是访问十三类图站 API 的 Python 客户端：Danbooru 系（`danbooru.donmai.us`、
`safebooru.donmai.us`）、Moebooru 系（`yande.re`、`konachan.com`、`sakugabooru.com`）、
Serika（`serika.art` 与同引擎自托管实例）、e621ng（`e621.net`、`e926.net`）、Zerochan（`zerochan.net`）
、Gelbooru（`gelbooru.com`）、e-shuushuu（`e-shuushuu.net`）、Gelbooru 0.2（TBIB，`tbib.org`）、
Sakuria（Pixiv 第三方镜像）、Anime-Pictures（`anime-pictures.net`，自研 `api/v3` 接口）、
Cosine（`pic.cosine.ren`，自研 API 的 Next.js 图站）、Nhentai（`nhentai.net`，站点自带的 `.net` API v2）
与 ArtStation（`artstation.com`，公开作品集、只读搜索与 RSS 订阅源）。

它不做跨引擎的统一图库模型：每个家族的方法只包装**该引擎自己**的路由，参数按该引擎的规则编码，
服务端返回的字段原样交给你，字段差异不隐藏。使用时**先选与你的站点匹配的客户端，再按任务查方法**；
本库不自动识别引擎——不确定站点属于哪一类，先看
[怎么判断一个站点该用哪个类](docs/configuration.md#怎么判断一个站点该用哪个类)。

- 版本：**0.1.0.dev1**（开发版；本仓库当前不发布到 PyPI，按源码安装，见[安装](#安装)）
- 许可：**MIT License**，见 [LICENSE](LICENSE)
- 上游：[LuqueDaniel/pybooru](https://github.com/LuqueDaniel/pybooru)（最后一次发版是 2020 年的 4.2.2）。
  本仓库重写了客户端（Danbooru 面 227 个方法、Moebooru 面 90 个方法）并新增 Serika、e621ng、Zerochan、
  Gelbooru、e-shuushuu、Gelbooru 0.2、Sakuria、Anime-Pictures、Cosine、Nhentai 与 ArtStation 十一个家族，
  重构了配置、传输与错误处理；仓库原名 `pybooru`，现名 `anybooru`，版本号从 `0.1.0.dev1` 重新起算。
  除 changelog 保留的历史记录外，**行为与上游不再一致**，用法以本仓库文档为准。

## 同名方法，不同字段

同名方法在不同引擎上返回的字段不同。下表的 `client` 由对应家族创建，完整代码在后面的例子里：

| 调用 | 真实请求 | 你拿到什么 |
| :--- | :--- | :--- |
| Danbooru：`client.post_list(tags='rating:g', limit=3)` | `GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=3` | 帖子列表；标签是空格分隔字符串 `post['tag_string']`，文件地址是 `post['file_url']` |
| e621ng：`client.post_list(tags='rating:s', limit=2)` | `GET https://e621.net/posts.json?tags=rating%3As&limit=2` | 帖子列表；普通标签在 `post['tags']['general']` 数组里，文件地址在 `post['file']['url']`，总分在 `post['score']['total']` |
| Moebooru：`client.post_list(tags='rating:s', limit=3)` | `GET https://yande.re/post.json?tags=rating%3As&limit=3` | 帖子列表；文件地址是 `post['file_url']`，标签是空格分隔字符串 `post['tags']` |
| Serika：`client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')` | `GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest` | 字典的 `images` 是图片列表，`pagination` 有页码和总数；每张图同时有内部编号 `id` 与网页上使用的编号 `post_id` |
| Zerochan：`client.entry_list(tags='Genshin Impact', l=2)` | `GET https://www.zerochan.net/Genshin+Impact?l=2&json=` | 返回 `{"items": [...]}` 里的图片列表；每张有编号 `id`、宽高、`thumbnail` 缩略图地址、`source` 来源、`tag` 主标签、`tags` 全部标签，以及 `md5` |
| Gelbooru：`client.autocomplete('blue', type='tag', limit=3)` | `GET https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2` | 建议数组，每条含 `type` / `label`（如 `blue eyes`）/ `value`（如 `blue_eyes`）/ `post_count` / `category`（如 `tag`、`copyright`）。**`limit` 不决定本次返回几条**：既有实测记录里 `limit=3` 仍返回 10 条 |
| e-shuushuu：`client.image_list(tags='46', per_page=2)` | `GET https://e-shuushuu.net/api/v1/images?tags=46&per_page=2` | 完整对象中的 `images` 是图片数组，`total/page/per_page` 是本次查询的分页数据；图片带 `image_id`、`tags`、`url` 和 `thumbnail_url`。`tags` 收数字标签 ID，不收名字 |
| Gelbooru 0.2：`client.post_list(tags='rating:safe', limit=2)` | `GET https://tbib.org/index.php?tags=rating%3Asafe&limit=2&s=post&q=index&page=dapi&json=1` | JSON 数组含 `id/width/height/rating/tags`，没有媒体 URL；显式 `response_format='xml'` 返回完整 XML 字符串，帖子属性才含 `file_url/preview_url` |
| Sakuria：`client.illust_search(q='blue', page=1, size=2)` | `GET https://sakuria-api.syarolia.com/search/illust?q=blue&page=1&size=2` | 完整字典中的 `items` 是插画数组；每项含 `id/title/urls/author/tags`，图片尺寸在 `urls.w/urls.h`，不是顶层 |
| Anime-Pictures：`client.posts_list(search_tag='hatsune miku', posts_per_page=2, page=0)` | `GET https://api.anime-pictures.net/api/v3/posts?search_tag=hatsune+miku&posts_per_page=2&page=0` | 完整信封：`posts` 是帖子数组，另有 `page_number` / `posts_per_page` / `response_posts_count` / `posts_count` / `max_pages`；每帖含 `id`、`md5`、`ext`（如 `.png`，**带点**）与 `score_number`（评分看它；`score` 原样保留，样本里既有 `0.0` 也有非零值）。列表**不给**预览地址 |
| Cosine：`client.image_list(page=1, pageSize=2)` | `GET https://pic.cosine.ren/api/list?page=1&pageSize=2` | 站内作品列表；方法原样返回 `{"images": [...], "total": N}`，不剥层。每项 `id` 是站内自增编号，上游编号在 `pid`；`rawurl` / `thumburl` 是地址。列表样本里 `size` 是 `null`、`guest` 是 `false`（只代表这批样本，不推广成恒值） |
| Nhentai：`client.gallery_list(per_page=2)` | `GET https://nhentai.net/api/v2/galleries?per_page=2` | 完整信封：`result` 是作品数组，另有 `num_pages` / `per_page` / `total`；每项有 `id`、`media_id`、`num_pages`、`num_favorites`、`thumbnail` 与 `thumbnail_width` / `thumbnail_height`、`tag_ids`（标签编号数组）、`blacklisted`。`gallery_show(id, include='related')` 是另一套详情对象（`cover` / `thumbnail` 带宽高、`pages`、`tags`、`scanlator`、`upload_date`）；方法不拆层 |
| ArtStation：`client.project_list(page=1, per_page=2)` | `GET https://www.artstation.com/projects.json?page=1&per_page=2` | 公开作品列表；方法原样返回 `{"data": [...], "total_count": N}`，不剥 `data` 层。条目样本含 `id`、`hash_id`、`title`、`permalink`、`cover`、`assets_count` 与 `tag_list`。**用户作品列表是另一套条目字段**：`user_projects` 的条目没有 `user` / `views_count`，不要跨路由照抄字段清单 |

表中标注的实测结果来自 [docs/verification.md](docs/verification.md) 的既有记录，不是对站点当前状态的保证。
十三个家族的引擎来路、契约依据与未实测边界见 [docs/index.md](docs/index.md) 与各家族的契约附注。

## 运行要求

- Python >= 3.6（`python_requires`；打包元数据的 classifiers 列到 3.10，构建工作流只用 3.11 跑构建，
  并非对所有受支持版本逐一验证）
- [requests](https://requests.readthedocs.io/) >= 2.26（唯一的第三方依赖；其余用到的是标准库）

## 安装

```bash
git clone https://github.com/NebulaeWisdom/anybooru.git
cd anybooru
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .        # Windows
.venv/bin/python -m pip install -e .                # Linux / macOS
```

装完不需要另外准备配置文件：包内自带一份可用的 `anybooru.json`。安装细节、验证安装、代理写法与
目录结构见 [docs/installation.md](docs/installation.md)。

## 第一次调用

下面两段都可以整字复制执行（匿名只读，默认站点来自包内配置）。其余十一个家族的第一次调用
（XML 原文、Bearer token、四种返回外壳等）见对应家族的 `docs/<family>.md`。

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
才是匿名，权限由服务端判定，凭据无效返回 `401` 而不是静默降级。

### Nhentai（nhentai.net）

```python
from anybooru import Nhentai

with Nhentai('nhentai') as client:                 # 包内 nhentai 条目的 api_key 留空即匿名
    # GET https://nhentai.net/api/v2/galleries?per_page=2
    # 方法原样返回整个信封：result 是作品数组，另有 num_pages / per_page / total。
    # 每项有 id（作品编号，详情路由与收藏都用它）、media_id（拼图片地址的字符串）、
    # num_pages、num_favorites、thumbnail 与 tag_ids（标签编号数组）
    page = client.gallery_list(per_page=2)
    for gallery in page['result']:
        print(gallery['id'], gallery['media_id'], gallery['num_pages'])
    print(page['num_pages'], page['per_page'], page['total'])

    # GET https://nhentai.net/api/v2/galleries/658856?include=related
    # 详情是另一套对象：cover / thumbnail 各含地址与宽高，pages 是每页对象数组，
    # tags 是标签对象数组；include= 用逗号串追加附加块，不传就不请求
    detail = client.gallery_show(658856, include='related')
    print(detail['id'], detail['num_pages'], len(detail['pages']), len(detail['tags']))
```

每个方法「给什么 → 返回什么」、真实 URL 与返回字段，见各家族的[方法参考](#文档)。

## 配置

站点地址、凭据、代理、超时、User-Agent 与示例参数都在一份 JSON 里。这份文件**随包安装**，
`Danbooru('danbooru')` 这类调用默认读它；`anybooru.DEFAULT_CONFIG_FILE` 是它的路径。
`config_file` 指到的文件不存在时直接抛 `FileNotFoundError`，不会回落到默认文件或内置站点；
当前工作目录里的同名文件**不会**被自动读取；没有任何环境变量注入。

包内文件的开头长这样（`sites` 段一共 17 个条目，下面列出部分站点；完整文件与逐键说明见
[docs/configuration.md](docs/configuration.md)）：

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
  `Zerochan('zerochan')`、`Gelbooru('gelbooru')`、`Gelbooru02('tbib')`、`Shuushuu('shuushuu')`、
  `Sakuria('sakuria')`、`AnimePictures('anime_pictures')`、`Cosine('cosine')`、`Nhentai('nhentai')`、
  `ArtStation('artstation')`；条目里的 `url`、凭据与 `api_version` 按同名字段读入，显式构造参数优先。
- 用清单外的站点：直接给 `site_url=`，例如 `Moebooru(site_url='https://example.org',
  api_version='1.13.0+update.3')`、`E621(site_url='https://e926.net')`。`sites` 段是**样例 / 起始清单，
  不是支持边界**。
- 改自己的配置：把包内那份复制成一份自己的，再把路径交给 `config_file=`，例如
  `Danbooru('danbooru', config_file='config/sites.json')`。默认 `request.proxies` 是 `{}`（不使用代理），
  需要时代理写成 `{"http": "http://proxy-host:port", "https": "http://proxy-host:port"}`。
- 各站点的凭据字段、默认值与认证形态（HTTP Basic、password_hash、Bearer、查询凭据、按次传入的
  CSRF token）见 [docs/authentication.md](docs/authentication.md)。两处容易踩的：Anime-Pictures 的 `url`
  是 **API 基址** `https://api.anime-pictures.net/api/v3`，不是网页主机；Zerochan 的 `user_agent` 按官方
  页面要求应含项目名与自己的用户名，默认值不含用户名，见[客户端用法](docs/zerochan.md)。

## 文档

文档全部是 `docs/` 下的中文 Markdown，每份只回答一类问题。先读 [docs/index.md](docs/index.md)
选家族与阅读层；跨家族通用的文档：

| 文档 | 内容 |
| :--- | :--- |
| [docs/index.md](docs/index.md) | 导航：想做什么 → 读哪份；十三个家族怎么选 |
| [docs/installation.md](docs/installation.md) | 安装、Python 与 requests 版本、配置文件放在哪、发行状态 |
| [docs/configuration.md](docs/configuration.md) | `anybooru.json` 完整样例、`config_file` 覆盖、`sites` 段语义与引擎判别 |
| [docs/authentication.md](docs/authentication.md) | 各家族的认证形态：HTTP Basic、密码哈希、Bearer、查询凭据、按次传入的 CSRF token |
| [docs/pagination.md](docs/pagination.md) | 各引擎的页码、`limit` 与游标写法 |
| [docs/errors.md](docs/errors.md) | 三个异常类、HTTP 错误字段、各引擎状态码含义、为什么不自动重试 |
| [docs/migration.md](docs/migration.md) | 从 Pybooru 4.x 改名 / 换参数 / 换返回值的逐方法对照表 |
| [docs/verification.md](docs/verification.md) | 哪些端点真的跑过（既有记录：状态码与返回摘要）、哪些没有 |
| [docs/adding-a-site.md](docs/adding-a-site.md) | 维护者向：把新图站 / 新引擎接成本仓库家族要做什么 |

每个家族有四份文档，入口见 [docs/index.md 的按家族选文档](docs/index.md#按家族选文档)：

| 家族 | 客户端怎么用 | 每个方法的参数与返回 | 按任务找方法 | 依据与排除（维护者用） |
| :--- | :--- | :--- | :--- | :--- |
| Danbooru | [danbooru.md](docs/danbooru.md) | [danbooru-api.md](docs/danbooru-api.md) | [danbooru-capabilities.md](docs/danbooru-capabilities.md) | [danbooru-contract-notes.md](docs/danbooru-contract-notes.md) |
| Moebooru | [moebooru.md](docs/moebooru.md) | [moebooru-api.md](docs/moebooru-api.md) | [moebooru-capabilities.md](docs/moebooru-capabilities.md) | [moebooru-contract-notes.md](docs/moebooru-contract-notes.md) |
| Serika | [serika.md](docs/serika.md) | [serika-api.md](docs/serika-api.md) | [serika-capabilities.md](docs/serika-capabilities.md) | [serika-contract-notes.md](docs/serika-contract-notes.md) |
| e621ng | [e621.md](docs/e621.md) | [e621-api.md](docs/e621-api.md) | [e621-capabilities.md](docs/e621-capabilities.md) | [e621-contract-notes.md](docs/e621-contract-notes.md) |
| Zerochan | [zerochan.md](docs/zerochan.md) | [zerochan-api.md](docs/zerochan-api.md) | [zerochan-capabilities.md](docs/zerochan-capabilities.md) | [zerochan-contract-notes.md](docs/zerochan-contract-notes.md) |
| Gelbooru | [gelbooru.md](docs/gelbooru.md) | [gelbooru-api.md](docs/gelbooru-api.md) | [gelbooru-capabilities.md](docs/gelbooru-capabilities.md) | [gelbooru-contract-notes.md](docs/gelbooru-contract-notes.md) |
| Gelbooru 0.2（TBIB） | [gelbooru02.md](docs/gelbooru02.md) | [gelbooru02-api.md](docs/gelbooru02-api.md) | [gelbooru02-capabilities.md](docs/gelbooru02-capabilities.md) | [gelbooru02-contract-notes.md](docs/gelbooru02-contract-notes.md) |
| e-shuushuu | [shuushuu.md](docs/shuushuu.md) | [shuushuu-api.md](docs/shuushuu-api.md) | [shuushuu-capabilities.md](docs/shuushuu-capabilities.md) | [shuushuu-contract-notes.md](docs/shuushuu-contract-notes.md) |
| Sakuria | [sakuria.md](docs/sakuria.md) | [sakuria-api.md](docs/sakuria-api.md) | [sakuria-capabilities.md](docs/sakuria-capabilities.md) | [sakuria-contract-notes.md](docs/sakuria-contract-notes.md) |
| Anime-Pictures | [anime-pictures.md](docs/anime-pictures.md) | [anime-pictures-api.md](docs/anime-pictures-api.md) | [anime-pictures-capabilities.md](docs/anime-pictures-capabilities.md) | [anime-pictures-contract-notes.md](docs/anime-pictures-contract-notes.md) |
| Cosine | [cosine.md](docs/cosine.md) | [cosine-api.md](docs/cosine-api.md) | [cosine-capabilities.md](docs/cosine-capabilities.md) | [cosine-contract-notes.md](docs/cosine-contract-notes.md) |
| Nhentai | [nhentai.md](docs/nhentai.md) | [nhentai-api.md](docs/nhentai-api.md) | [nhentai-capabilities.md](docs/nhentai-capabilities.md) | [nhentai-contract-notes.md](docs/nhentai-contract-notes.md) |
| ArtStation | [artstation.md](docs/artstation.md) | [artstation-api.md](docs/artstation-api.md) | [artstation-capabilities.md](docs/artstation-capabilities.md) | [artstation-contract-notes.md](docs/artstation-contract-notes.md) |

## 可运行示例

`examples/` 下共 35 个脚本，按家族分目录，全部支持 `--config` 与 `--site`；省略 `--config` 就读包内默认
配置，站点名与参数（标签、页码、条数、间隔）取自配置的 `examples.<家族>` 段，脚本里不硬编码站点与分页。

| 目录 | 脚本 |
| :--- | :--- |
| `examples/danbooru/` | `list_posts.py`（帖子列表）、`show_post.py`（单帖详情）、`list_tags.py`（标签搜索）、`paginate_posts.py`（数字 `page` 翻页与 `page='b<id>'` 取更旧帖子）、`related_tag.py`（相关标签）、`wiki_page.py`（按标题读 wiki 正文）——六个匿名只读脚本；另有 `comment_create.py` 是**真实的 POST 写示例**，需要账号与 API key，本仓库不带凭据，未执行、未实测 |
| `examples/moebooru/` | `list_posts.py`（两页帖子与文件地址）、`list_tags.py`（标签与计数）、`wiki_list.py`（wiki 标题搜索）、`list_comments.py`（评论流条数，当前观察到 0 条）、`related_tags.py`（相关标签）——五个匿名只读脚本 |
| `examples/serika/` | `service_info.py`（官方索引、统计、用户目录）、`browse.py`（站内图片列表与详情、标签、画师）、`random_image.py`（读官方随机图片字节并打印 Content-Type，不落盘）——三个匿名只读脚本 |
| `examples/e621/` | `list_posts.py`（帖子列表、单帖、随机帖）、`browse_resources.py`（标签、画师、评论、合集、笔记）、`wiki_pages.py`（wiki 列表与按标题取页）——三个匿名只读脚本 |
| `examples/zerochan/` | `list_entries.py`（条目列表与单条目详情）、`filter_entries.py`（单标签、多标签、`strict` 三种过滤）——两个匿名只读脚本，调用之间按 `pause_seconds` 暂停 |
| `examples/gelbooru/` | `autocomplete.py`（标签自动补全）——一个匿名只读脚本；dapi 的 5 个方法需要账号，没有成功调用示例，匿名拒绝见验证记录 |
| `examples/gelbooru02/` | `list_posts.py`（JSON 列表与同帖 XML）、`browse_resources.py`（XML 标签与评论）——两个匿名脚本，各最多两次 GET |
| `examples/shuushuu/` | `search_images.py`（标签名换 ID、两页筛图、详情）、`browse_resources.py`（标签详情、评论、用户、新闻）——两个匿名只读脚本 |
| `examples/sakuria/` | `search_illusts.py`（两页搜索与 ID 去重）、`browse_resources.py`（插画详情、评论与作者）——两个匿名脚本 |
| `examples/anime_pictures/` | `list_posts.py`（配置的两页帖子列表，打印真实 URL、状态与分页字段）、`browse_resources.py`（帖子详情、该帖评论、用户资料、评论详情）——两个匿名只读脚本，不访问媒体 |
| `examples/cosine/` | `list_images.py`（配置的两页 `image_list` 与两个 `offset` 的搜索）、`browse_resources.py`（作品详情、标签筛图、画师作品与 `infoOnly=True` 的画师资料）——两个匿名只读脚本，不下载媒体 |
| `examples/nhentai/` | `list_galleries.py`（配置的两页 `gallery_list` 与一次 `search`）、`browse_resources.py`（作品详情、标签详情、多标签编号查询、作品评论与站点配置）——两个匿名只读脚本，不下载媒体 |
| `examples/artstation/` | `list_projects.py`（配置的两页全站作品列表与两页过滤搜索）、`browse_resources.py`（用户资料、专辑作品、随机作品与作品评论）——两个匿名只读脚本，不调用被站点挡下的详情路由 |

```bash
.venv/Scripts/python.exe examples/danbooru/list_posts.py
.venv/Scripts/python.exe examples/moebooru/list_posts.py
.venv/Scripts/python.exe examples/serika/service_info.py
.venv/Scripts/python.exe examples/e621/list_posts.py
.venv/Scripts/python.exe examples/zerochan/list_entries.py
.venv/Scripts/python.exe examples/gelbooru/autocomplete.py
.venv/Scripts/python.exe examples/shuushuu/search_images.py
.venv/Scripts/python.exe examples/gelbooru02/list_posts.py
.venv/Scripts/python.exe examples/sakuria/search_illusts.py
.venv/Scripts/python.exe examples/anime_pictures/list_posts.py
.venv/Scripts/python.exe examples/cosine/list_images.py
.venv/Scripts/python.exe examples/nhentai/list_galleries.py
.venv/Scripts/python.exe examples/artstation/list_projects.py
```

其余目录与脚本同理：`.venv/Scripts/python.exe examples/<family>/<script>.py`（Linux / macOS 用
`.venv/bin/python`）。哪些脚本真的跑过、逐条状态码与返回摘要，见
[docs/verification.md](docs/verification.md) 的既有记录。

## 轻量匿名冒烟检查

安装本包后，可单独运行 `test/<站点>.py`，快速检查导入、配置与客户端构造，以及少量 API 的字段类型、
列表条数、分页、详情编号和预期错误。文件名对应 `sites` 段 17 个条目：`serika`、`danbooru`、`safebooru`、
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
不重试、不跟随重定向、不切换站点。每站最多 10 次请求：Shuushuu、Sakuria、Cosine、Anime-Pictures、
Nhentai 与 ArtStation 最多 10 次、Serika 最多 5 次、Gelbooru 与 TBIB 最多 6 次，其余各最多 4 次；
前置列表失败时跳过依赖的详情 / 翻页，不补发请求。两次请求之间按配置暂停：通用 `smoke.pause_seconds=1.2`，
Shuushuu 用 `smoke.shuushuu.pause_seconds=2.1`，Sakuria 用 `smoke.sakuria.pause_seconds=1.2`，
Anime-Pictures 用 `smoke.anime_pictures.pause_seconds=1.3`，Cosine 用 `smoke.cosine.pause_seconds=1.3`；
Nhentai 没有自己的 `pause_seconds`，用通用的 `smoke.pause_seconds=1.2`，
ArtStation 用 `smoke.artstation.pause_seconds=1.3`。不依赖测试框架，不在 CI 自动运行。

每条检查输出 `PASS` / `FAIL`、真实 URL、HTTP 状态或异常及关键字段 / 条数，最后汇总实际尝试次数；
退出码 `0` 表示本次全部符合预期，`1` 表示失败或漂移。Gelbooru 五个 dapi 的匿名 `401` 空正文是
**预期拒绝**，不是失败；Anime-Pictures 的缺失帖子 `410` 与非法路径段 `400`（正文是 `text/plain`、
`AnybooruHTTPError.data` 为 `None`）、Cosine 查缺失作品的 `404`、Nhentai 查缺失作品的 `404` 与非法
`page`（例如 `page=0`）的 `400`、ArtStation 的缺失用户名 `404`（`text/plain` 空正文）与非法搜索参数的
`400` 同样是**预期拒绝**，不是失败；网络失败也不会伪装成站点变化。这里不是全 API 覆盖或长期可用性保证。

省略 `--config` 时读包内默认配置（不含代理）；若所在网络需要代理，必须用 `--config` 指向自己的完整
配置。复制最新版 `anybooru/anybooru.json`，保留其中的 `smoke` 段，仅调整自己的 `request` 设置；
不会合并旧配置或读取环境变量。参数说明见[配置文档](docs/configuration.md#smoke-段)，
一次完整执行的结果见[验证记录](docs/verification.md)。脚本随仓库与源码分发包提供，不放入 wheel。

## 贡献

请在动手前阅读 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

## 许可

- **[MIT License](LICENSE)**
