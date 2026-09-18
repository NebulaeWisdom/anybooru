# Moebooru 客户端用法

`Moebooru` 访问用 Moebooru 引擎搭的图站：yande.re、konachan.com、sakugabooru.com 等。
它做的事情只有三件：按站点条目读配置、把参数发成 Rails 的表单/查询串、把服务端返回的 JSON 原样交给你。
哪些接口存在、每个接口要什么参数、什么等级能调用，全部以只读参考的上游源码 `moebooru/` 为准；
逐条出处、权限过滤器和被排除的浏览器页面见[契约审计附注](moebooru-contract-notes.md)。

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    posts = client.post_list(tags='rating:s', limit=3)   # GET https://yande.re/post.json?tags=rating%3As&limit=3
    print(posts[0]['id'], posts[0]['file_url'])
```

`post_list` 返回的是一个数组，每项是帖子字典，含 `id`、`tags`、`score`、`md5`、`file_url`、
`preview_url`、`sample_url`、`width`、`height`、`rating`、`status` 等字段；上面两行会打印第一条的编号与原图地址。
本轮在 yande.re 上真实读到的编号、文件地址与条数见 [verification.md](verification.md) 的 Moebooru 章节；
本页只写“怎么调、拿到什么”，不重复那些数字。

Moebooru 面和 Danbooru 面有三个必须分清的区别：**过滤条件直接写在顶层**（没有 `search[...]` 字典）、
**请求体永远是 Rails 表单**（没有 JSON 请求体）、**认证是 `login` + `password_hash`**（不是 HTTP Basic）。

## 构造

```text
Moebooru(site_name=None, site_url=None, username=None, password=None, hash_string=None,
         api_version=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)
```

| 参数 | 类型 | 说明 | 不给时的行为 |
| :--- | :--- | :--- | :--- |
| `site_name` | str | 配置 `sites` 段的键名，例如 `'yandere'`；条目里的 `url`、`username`、`password`、`hash_string`、`api_version` 按同名字段读入 | 与 `site_url` 都不给会直接报错，库没有地址后备 |
| `site_url` | str | 显式地址，例如 `'https://yande.re'`；用于不在清单里的自建站 | 不给就取 `site_name` 条目的 `url` |
| `username` | str | 登录用户名 | 取站点条目的 `username`；与 `password` 都空 = 匿名 |
| `password` | str | 登录密码明文，只用于在构造时算出 `password_hash` | 取站点条目的 `password` |
| `hash_string` | str | 站点加盐模板，形如 `'choujin-steiner--{0}--'`，`{0}` 会被密码替换 | 取站点条目的 `hash_string`；匿名不需要它 |
| `api_version` | str | 站点自述版本，决定**列表路径形态**（见下节）；大小写不敏感 | 取站点条目的 `api_version` |
| `proxies` / `timeout` / `user_agent` | 同 `request` 配置段 | 显式覆盖配置里的同名项；会话不读环境变量（`trust_env=False`） | 用配置 `request` 段的值 |
| `config_file` | str | 要读的配置路径 | `None` = 读随包安装的 `anybooru/anybooru.json`；指到的文件不存在会抛 `FileNotFoundError`，不会退回包内默认 |

用自建站时两个字段必须一起给：`Moebooru(site_url='https://example.org', api_version='1.13.0+update.3',
username='me', password='secret', hash_string='salt--{0}--')`——只给 `site_url` 不给 `api_version` 会报错，
因为列表路径形态没有默认值。

构造完成后可以读这几个属性：`client.site_url`、`client.api_version`、`client.password_hash`
（匿名时为 `None`）、`client.config`（整份配置）。

## 站点清单

清单是**样例，不是支持边界**：任何跑 Moebooru 引擎的站点都能用 `site_url=` + `api_version=` 接入；
反过来，在清单里也不代表该站每个能力都开着。

| 配置键 | 地址 | 站点自述版本 | 备注 |
| :--- | :--- | :--- | :--- |
| `yandere` | `https://yande.re` | `1.13.0+update.3` | 上游项目的参考部署 |
| `konachan` | `https://konachan.com` | `1.13.0+update.3` | `konachan.net` 是同站的过滤镜像，会少掉部分帖子 |
| `sakugabooru` | `https://sakugabooru.com` | `1.13.0+update.3` | 动画作画片段的视频站，标签体系与图片站不同 |

可达性取决于网络环境：`konachan.com` 对某些网络会返回 Cloudflare 的 “Just a moment…” 挑战页，
换一条线路后同一域名同样路径正常返回 JSON。这是网络侧限制，不代表引擎没有这条路由。

## 认证

不登录时什么认证字段都不发：只要 `username` 与 `password` 都为空，请求里就没有 `login` 与 `password_hash`。

登录在构造时算好密码哈希，之后不再重算：

```text
password_hash = SHA1(hash_string.format(password))
```

`hash_string` 是站点自己的 `CONFIG["password_salt"]` 加上固定前后缀 `--`，例如 yande.re 的
`choujin-steiner--{0}--`，上游 `user.rb:95-96` 的 `SHA1("#{salt}--#{pass}--")` 就是这个格式；
站点帮助页 `app/views/help/api.en.html.erb:95` 会把它原文列出来，因此它是站点固定常量、不随版本变。
各站取值见 [configuration.md](configuration.md#sites-段)。

发送位置：`GET` / `HEAD` 把 `login` 与 `password_hash` 放进查询串，其它动词放进表单体。
服务端还接受 `username` + `api_key`、会话 Cookie、`user[name]` + `user[password]` 明文等几种方式，
本库只实现 `password_hash` 这一种；细节见 [authentication.md](authentication.md)。

## 通用入口 `request()`

没有原生方法的端点直接用它：

```text
request(method, path, *, params=None, data=None, files=None)
```

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    posts = client.request('GET', 'post', params={'tags': 'rating:s', 'limit': 1})
    # GET https://yande.re/post.json?tags=rating%3As&limit=1
    print(posts[0]['id'], posts[0]['md5'], posts[0]['jpeg_url'])
```

| 参数 | 说明 |
| :--- | :--- |
| `method` | `'GET'` / `'POST'` / `'PUT'` / `'DELETE'` 等；本库不判断服务端允许哪个动词，传什么发什么 |
| `path` | 相对路径，例如 `'post'`、`'post/similar'`、`'wiki/history'`；开头写不写 `/` 都行，写 `.json` 也会被去掉再重新补上 |
| `params` | 查询串参数；嵌套字典变 `a[b]`，列表变重复键 `a[]`，布尔变小写 `true`/`false`，`None` 直接不发送 |
| `data` | 请求体，**恒为 Rails 表单**（同一套编码）；不带文件时也是表单，没有 JSON 请求体这条路径 |
| `files` | requests 的文件映射或 `(字段名, 文件)` 列表；给出后请求体变成 multipart，文件对象由调用者关闭 |

路径形态有一条版本规则：`api_version` 是 `1.13.0`、`1.13.0+update.1`、`1.13.0+update.2` 时，
**裸的集合路径**（如 `'post'`、`'tag'`）会被补成 `post/index.json`；现役站点自述
`1.13.0+update.3`，走非 `/index` 形态，也就是 `post.json`。带动作段的路径（如 `'pool/show'`）不受影响。

返回值：

| 服务端给了什么 | 你会拿到什么 |
| :--- | :--- |
| JSON 正文 | Python 对象：列表接口是数组（每项一个帖子/标签/评论…），详情接口是单个字典 |
| `204` 或空正文 | `None`（例如 `forum_mark_all_read()`） |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`、`data`（正文不是 JSON 时 `data` 为 `None`） |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError` |
| 连不上/超时/TLS 失败 | 原样抛 requests 的异常，本库不包装也不重试 |

每次请求后 `client.last_call` 是最新一次的情况：`API`（相对路径）、`url`（最终完整地址，含查询串）、
`status_code`、`status`、`headers`。核对“参数到底发成什么样”看它：

```python
from anybooru import Moebooru

with Moebooru('yandere') as client:
    client.post_list(tags='id:1269034')
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://yande.re/post.json?tags=id%3A1269034
```

## 六个容易踩的坑

1. **没有 `post_show`，也没有 `wiki_show`**：这两个动作只渲染 HTML 页面。单帖用
   `post_list(tags='id:<帖子编号>')`（按 md5 用 `tags='md5:<哈希>'`），返回空数组表示不存在或当前身份看不见；
   wiki 正文用 `wiki_list(query='title:<标题>')`，历史用 `wiki_history(title='<标题>')`。
   对这两个路径请求 `.json` 会得到 404 空正文（`post/show` 写了 `format: false`）或 406，不是本库漏封。
2. **两个 `api_version` 不是一回事**：构造参数那个决定列表路径要不要补 `/index`；
   `post_list` 的查询参数 `api_version='2'` 决定返回结构——不带时是图片列表，带 `'2'` 时是 `{"posts": [...]}`。
   想同时拿到标签、自己的投票或合集，分别加 `include_tags='1'`、`include_votes='1'`、`include_pools='1'`。
3. **`note_list` 的页码是帖子页，不是笔记页**：不带 `post_id` 时服务端先按“有笔记的帖子”分页
   （每页 16 个帖子），再把这些帖子的全部笔记铺平返回，所以一页拿到的笔记数不是 16，`limit` 也不生效。
4. **`wiki_update` 的改名参数是 `new_title`**：顶层 `title` 用来选中页面，`new_title` 才是写进
   `wiki_page[title]` 的新标题，两个可以同时传。另外必须至少给一个 `wiki_page[...]` 属性，否则服务端回 400。
5. **跟随重定向拿到的 200 不是“写成功”**：只有 flash 提示的校验失败也会重定向到同一个目标页；
   别名/蕴含的审批还会跳到只有 HTML 的任务页，可能拿到 500 或非 JSON。要确认写没写进去，写完后自己再查一次，
   不要盲目重试。
6. **`comment_list` 不带 `post_id` 只会查到空列表**：服务端把缺失的帖子编号当成 0，
   所以它不是“全站最新评论”接口。要按页读评论流用 `comment_search(query='')`（空数组是正常结果，不是失败）。

和 Danbooru 面的差别再列一次：Moebooru 没有 `search[...]` 字典（过滤条件在顶层）；`data` 恒为表单；
认证是 `login` + `password_hash`；`api_version` 只在 Moebooru 面存在。

## 可运行示例

五个脚本全部匿名只读，`--config` 指定配置文件（省略即读包内默认那份），`--site` 覆盖站点名；
站点与参数来自配置的 `examples.moebooru` 段，脚本没有硬编码站点或代理。例如配置里是
`tags='rating:s'`、`limit=3`、`pages=[1, 2]`，脚本对应的调用就是
`client.post_list(tags='rating:s', page=page, limit=3)`：

```bash
.venv/Scripts/python.exe examples/moebooru/list_posts.py
.venv/Scripts/python.exe examples/moebooru/list_tags.py
.venv/Scripts/python.exe examples/moebooru/wiki_list.py
.venv/Scripts/python.exe examples/moebooru/list_comments.py
.venv/Scripts/python.exe examples/moebooru/related_tags.py
```

| 脚本 | 它调用什么、打印什么 |
| :--- | :--- |
| `list_posts.py` | 按标签分页 `post_list`，每页打印帖子编号与 `file_url` |
| `list_tags.py` | `tag_list(limit=3, order='count')`，打印标签名与使用计数 |
| `wiki_list.py` | `wiki_list(query='touhou', limit=3)`，打印页面标题 |
| `list_comments.py` | `comment_search(query='')`，打印条数（与 0 条也是正常结果）；有正文时再打印前若干字符 |
| `related_tags.py` | `tag_related(tags='touhou', type='general')`，打印查询标签与共现标签、次数 |

五个脚本的真实运行记录（退出码、真实打印）在 [verification.md](verification.md) 的 Moebooru 章节。

## 边界与未实测

* 本页只覆盖**匿名只读**。**写路径（上传、编辑、投票、删除、审核、账号动作）没有线上实测**，
  只按上游源码对齐；逐条状态与上游坐标见[契约审计附注](moebooru-contract-notes.md)。
* 示例里那五个脚本确实跑过并退出 0；`sakugabooru` 的加盐模板取自站点自述，**没有发登录请求**验证服务端是否接受。
* 方法存在不等于站点开了该能力：相似图服务、异步任务后端、站点自己关掉的功能都可能缺失，
  结果由服务端决定，本库不补默认值也不伪造替代响应。

继续阅读：[方法参考](moebooru-api.md) · [能力总览](moebooru-capabilities.md) ·
[契约审计附注](moebooru-contract-notes.md) · [分页](pagination.md)。
