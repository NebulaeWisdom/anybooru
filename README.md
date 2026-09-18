# Anybooru - Danbooru / Moebooru / Serika / e621ng / Zerochan / Gelbooru 图站 API 客户端

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/NebulaeWisdom/anybooru/master/LICENSE)

**Anybooru** 是访问六类图站引擎的 Python API 客户端：Danbooru 系（`danbooru.donmai.us`、
`safebooru.donmai.us`）、Moebooru 系（`yande.re`、`konachan.com`、`sakugabooru.com`）、
Serika（`serika.art` 与同引擎自托管实例）、e621ng（`e621.net`、`e926.net`）、Zerochan（`zerochan.net`）
与 Gelbooru（`gelbooru.com`）。
它不做跨引擎的统一图库模型：每个家族的方法只包装**该引擎自己**的路由，参数按该引擎的规则编码，
服务端返回的字段原样交给你，字段差异不隐藏。

同名方法在不同引擎上返回的字段不同。下表的 `client` 由对应家族创建，完整代码在后面的六个例子里：

| 调用 | 真实请求 | 你拿到什么 |
| :--- | :--- | :--- |
| Danbooru：`client.post_list(tags='rating:g', limit=3)` | `GET https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=3` | 帖子列表；标签是空格分隔字符串 `post['tag_string']`，文件地址是 `post['file_url']` |
| e621ng：`client.post_list(tags='rating:s', limit=2)` | `GET https://e621.net/posts.json?tags=rating%3As&limit=2` | 帖子列表；普通标签在 `post['tags']['general']` 数组里，文件地址在 `post['file']['url']`，总分在 `post['score']['total']` |
| Moebooru：`client.post_list(tags='rating:s', limit=3)` | `GET https://yande.re/post.json?tags=rating%3As&limit=3` | 帖子列表；文件地址是 `post['file_url']`，标签是空格分隔字符串 `post['tags']` |
| Serika：`client.internal_image_list(page=1, limit=3, ratings='safe', sort='newest')` | `GET https://serika.art/api/images?page=1&limit=3&ratings=safe&sort=newest` | 字典的 `images` 是图片列表，`pagination` 有页码和总数；每张图同时有内部编号 `id` 与网页上使用的编号 `post_id` |
| Zerochan：`client.entry_list(tags='Genshin Impact', l=2)` | `GET https://www.zerochan.net/Genshin+Impact?l=2&json=` | 返回 `{"items": [...]}` 里的图片列表；每张有编号 `id`、宽高、`thumbnail` 缩略图地址、`source` 来源、`tag` 主标签、`tags` 全部标签，以及 `md5` |
| Gelbooru：`client.autocomplete('blue', type='tag', limit=3)` | `GET https://gelbooru.com/index.php?type=tag&limit=3&term=blue&page=autocomplete2` | 建议数组，每条含 `type` / `label`（如 `blue eyes`）/ `value`（如 `blue_eyes`）/ `post_count` / `category`（如 `tag`、`copyright`）。**`limit` 不决定本次返回几条**：实测 `limit=3` 仍返回 10 条 |

六类引擎的来路不同：Danbooru、Moebooru、e621ng 是三个**互不相同**的 Rails 引擎，同名路由与相同的
认证头不代表同一套契约；Serika 是独立的 Next.js 应用，官方版本化 `/api/v1` 与站内未版本化 `/api/*`
两面分开标注；Zerochan 是站点自有的只读 JSON API，**没有公开的引擎源码**，契约依据是官方 API 页面快照
加真实请求实测——见
[docs/zerochan-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/zerochan-contract-notes.md)；
Gelbooru 走站点自己的 `index.php`：`page=dapi`（加 `json=1`）与页面脚本用的 `page=autocomplete2` 返回
JSON；`page=tags/post/wiki` 等浏览路由返回 HTML。依据是官方 wiki/帮助页与站点脚本
加真实响应，见
[docs/gelbooru-contract-notes.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/gelbooru-contract-notes.md)。
前四个家族按上游引擎源码对齐，Zerochan 与 Gelbooru 按站点文档与真实响应核对，不存在“六个家族都有源码依据”。

- 版本：**0.1.0.dev1**（开发版，尚未发布到 PyPI）
- 许可：**MIT License**
- 上游：[LuqueDaniel/pybooru](https://github.com/LuqueDaniel/pybooru)（最后一次发版是 2020 年的 4.2.2）。
  本仓库重写了客户端（Danbooru 面 227 个方法、Moebooru 面 90 个方法）并新增 Serika、e621ng、Zerochan
  与 Gelbooru 四个家族，重构了配置、传输与错误处理；仓库原名 `pybooru`，现名 `anybooru`，版本号从 `0.1.0.dev1`
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

包内文件的开头长这样（`sites` 段一共 10 个条目，这里是四种典型形态）：

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
    "gelbooru": { "url": "https://gelbooru.com", "api_key": "", "user_id": "" }
  }
}
```

- 用命名站点：`site_name` 是 `sites` 段的键，例如 `Danbooru('danbooru')`、`Moebooru('yandere')`、
  `Zerochan('zerochan')`、`Gelbooru('gelbooru')`；条目里的 `url`、凭据与 `api_version` 按同名字段读入，
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

## 六个家族的第一次调用

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

## 文档

文档全部是 `docs/` 下的中文 Markdown，每份只回答一类问题：

| 文档 | 内容 |
| :--- | :--- |
| [docs/index.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/index.md) | 导航：想做什么 → 读哪份；六个家族怎么选 |
| [docs/installation.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/installation.md) | 安装、Python 与 requests 版本、配置文件放在哪 |
| [docs/configuration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/configuration.md) | `anybooru.json` 完整样例、`config_file` 覆盖、`sites` 段语义与引擎判别 |
| [docs/authentication.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/authentication.md) | 各家族的认证形态：HTTP Basic、Moebooru 密码哈希、Serika Bearer、Gelbooru 的 `api_key` + `user_id`、Zerochan 匿名 |
| [docs/pagination.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/pagination.md) | 各引擎的页码、`limit` 与游标写法 |
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
| [docs/migration.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/migration.md) | 从上游 4.x 迁移到 0.1.x 的逐项对照 |
| [docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md) | 哪些端点真的跑过（含状态码与返回摘要）、哪些没有 |

## 可运行示例

`examples/` 下 21 个脚本都按家族分目录，全部支持 `--config` 与 `--site`；省略 `--config` 就读包内默认配置，
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

```bash
.venv/Scripts/python.exe examples/danbooru/list_posts.py
.venv/Scripts/python.exe examples/moebooru/list_posts.py
.venv/Scripts/python.exe examples/serika/service_info.py
.venv/Scripts/python.exe examples/e621/list_posts.py
.venv/Scripts/python.exe examples/zerochan/list_entries.py
.venv/Scripts/python.exe examples/gelbooru/autocomplete.py
```

哪些脚本真的跑过、每条命令的状态码与返回摘要，见
[docs/verification.md](https://github.com/NebulaeWisdom/anybooru/blob/master/docs/verification.md)。

## 轻量匿名冒烟检查

安装本包后，可单独运行 `test/<站点>.py`，快速检查导入、配置与客户端构造，以及少量 API 的字段类型、
列表条数、分页、详情编号和预期错误。文件名对应 `sites`：`serika`、`danbooru`、`safebooru`、
`konachan`、`yandere`、`sakugabooru`、`e621`、`e926`、`zerochan`、`gelbooru`。

```bash
python test/danbooru.py
python test/zerochan.py --config <你的配置文件>
python test/gelbooru.py --config <你的配置文件>
```

全部匿名、只发 GET，不需要账号，脚本显式禁用配置中的凭据；不登录、不写入、不下载媒体、
不重试、不跟随重定向、不切换站点。每站严格少于 10 次请求：Serika 最多 5 次、Gelbooru 最多 6 次、
其余各最多 4 次；前置列表失败时跳过依赖的详情/翻页，不补发请求。两次请求之间按
`smoke.pause_seconds` 暂停（默认 1.2 秒）。不依赖测试框架，不在 CI 自动运行。

每条检查输出 `PASS` / `FAIL`、真实 URL、HTTP 状态或异常及关键字段/条数，最后汇总实际尝试次数；
退出码 `0` 表示本次全部符合预期，`1` 表示失败或漂移。Gelbooru 五个 dapi 的匿名 `401` 空正文是
**预期拒绝**，不是失败；网络失败也不会伪装成站点变化。这里不是全 API 覆盖或长期可用性保证。

省略 `--config` 时读包内默认配置（不含代理）；若所在网络需要代理，必须用 `--config` 指向自己的
完整配置。复制最新版 `anybooru/anybooru.json`，保留其中的 `smoke` 段，仅调整自己的 `request` 设置；
不会合并旧配置或读取环境变量。参数说明见[配置文档](docs/configuration.md#smoke-段)，
一次完整执行的结果见[验证记录](docs/verification.md)。脚本随仓库与源码分发包提供，不放入 wheel。

## 贡献

请在动手前阅读 **[CONTRIBUTING.md](https://github.com/NebulaeWisdom/anybooru/blob/master/CONTRIBUTING.md)**。

## 许可

- **[MIT License](https://github.com/NebulaeWisdom/anybooru/blob/master/LICENSE)**
