# Moebooru 客户端

`Moebooru` 访问 Moebooru 引擎系站点（yande.re、konachan、sakugabooru 等）：读根配置、构造请求、
附加 `password_hash`、把服务端 JSON 原样返回。契约以只读参考的上游源码 `moebooru/` 为准，
逐条上游坐标、权限与排除项见[契约审计附注](moebooru-contract-notes.md)。

```python
from pybooru import Moebooru
with Moebooru('yandere', config_file='pybooru.json') as client:
    print(len(client.comment_search(query=client.config['examples']['moebooru']['comment_query'])))
```

```text
0
```

这里展示 2026-09-15 匿名运行 `examples/moebooru/list_comments.py` 记录的真实条数（`comments: 0`）；空列表是正常结果。帖子分页示例也有两页各 3 条的记录，命令、ID 与文件 URL 摘要见 [verification.md](verification.md#当前示例的执行记录)。

## 构造

`Moebooru(site_name=None, site_url=None, username=None, password=None, hash_string=None, api_version=None, proxies=None, *, config_file='pybooru.json', timeout=None, user_agent=None)`

| 参数 | 说明 |
| :--- | :--- |
| `site_name` | 根配置 `sites` 段的键名（如 `'yandere'`）；条目里的 `url` / `username` / `password` / `hash_string` / `api_version` 按同名字段读入 |
| `site_url` | 显式覆盖地址；不用命名站点时必须同时给 `api_version`，否则构造失败 |
| `username` / `password` | 显式覆盖登录凭据；匿名只读不必填 |
| `hash_string` | 站点加盐模板（含 `{0}`）；站点条目里是 `null` 又需要登录时必须显式给 |
| `api_version` | 决定**列表路径形态**（见下方「坑」）：旧版本把裸集合路径补成 `/index`，`1.13.0+update.3` 不补 |
| `proxies` / `timeout` / `user_agent` | 覆盖根配置 `request` 段的同名项；会话关闭 `trust_env`，不读环境变量 |
| `config_file` | 配置文件路径，默认当前工作目录的 `pybooru.json`；不去安装目录搜索 |

显式参数优先于配置文件中的同名值；自定义站点写法 `Moebooru(site_url='https://example.org', api_version='1.13.0+update.3', username='me', password='secret', hash_string='salt--{0}--')`。
解析后的配置挂在 `c.config`，派生字段可读 `c.api_version` / `c.password_hash`（匿名时为 `None`）；每次请求后 `c.last_call` 是最新一次的 `API` 相对路径、最终 `url`（含查询串）、状态与响应头。
配置结构见 [configuration.md](configuration.md)。

## 站点

清单是**样例，不是支持边界**：任何跑 Moebooru 引擎的站点都能用 `site_url=` + `api_version=` 接入；反过来，在清单里也不保证每个能力都启用。清单语义见 [configuration.md](configuration.md#sites-段)。

| 键 | 地址 | 站点自述 API 版本 | 备注 |
| :--- | :--- | :--- | :--- |
| `yandere` | `https://yande.re` | `1.13.0+update.3` | 上游项目的参考部署 |
| `konachan` | `https://konachan.com` | `1.13.0+update.3` | `.net` 是同站的**过滤镜像**（会少掉部分帖子），要完整内容用 `.com` |
| `sakugabooru` | `https://sakugabooru.com` | `1.13.0+update.3` | 动画作画片段站（视频向 fork），标签体系与图片站不同 |

正常返回 JSON——这是网络侧限制，不代表引擎缺少对应路由。

## 认证

不用 HTTP Basic：`password_hash = SHA1(hash_string.format(password))`，构造时算好、之后不再重算。`username` 与 `password` 都为空才是匿名；`GET` / `HEAD` 把 `login` 与 `password_hash` 放进查询串，其他动词放进表单体。
`hash_string` 就是站点自己的 `CONFIG["password_salt"]` 加固定前后缀 `--`（上游
`user.rb:95-96` 的 `SHA1("#{salt}--#{pass}--")`，帮助页 `help/api.en.html.erb:95` 会把它原文列出来），
属于站点固定常量、不随版本变；取值与来源见 [configuration.md](configuration.md#sites-段)。
服务端还接受 `username` + `api_key`、会话 Cookie、明文 `user[name]` 等方式，本库只实现密码哈希一种；细节见 [authentication.md](authentication.md)。

## 通用入口与返回值

没有原生方法的端点直接用它：`request(method, path, *, params=None, data=None, files=None)`。
`params` 是查询串，`data` **恒为 Rails 表单**（嵌套 dict → `a[b]`，列表 → 重复键 `a[]`，
`None` 不发送），`files` 非空时改为 multipart；传入的文件对象由调用者关闭。

```python
from pybooru import Moebooru

with Moebooru('yandere', config_file='pybooru.json') as c:
    example = c.config['examples']['moebooru']
    posts = c.request('GET', 'post', params={'tags': example['tags'], 'limit': example['limit']})
    print([post['id'] for post in posts])
```

| 服务端响应 | 返回值 |
| :--- | :--- |
| JSON 正文 | 原样返回的 Python 对象（列表是数组，详情是单个对象），不改字段、不包装 |
| `204` / 空正文 | `None` |
| HTTP 错误 | `PybooruHTTPError`（`http_code` / `url` / `body` / `data`；正文不是 JSON 时 `.data` 为 `None`） |
| 2xx 但正文不是 JSON | `PybooruAPIError` |

各族的具体形态（顶层数组、`{success:true}`、被触及帖子的批量负载、重定向目标页的 JSON）见 [方法参考的响应形态](moebooru-api.md#响应形态)；异常类型见 [errors.md](errors.md)。

## 容易踩的坑

1. **没有 `post_show` / `wiki_show`**：两者只渲染 HTML；单帖用 `post_list(tags='id:<id>')`（md5 用 `tags='md5:<hash>'`，空数组＝不存在或当前身份不可见），wiki 正文用 `wiki_list` / `wiki_history`。
2. **两个 `api_version` 不是一回事**：构造参数选择列表**路径形态**，`post_list` 的查询参数 `api_version='2'` 选择响应**信封**（`{posts, pool_posts, pools, tags, votes}`）。
3. **`note_list` 按帖子分页**：不带 `post_id` 时服务端先按帖子分页（每页 16 个有笔记的帖子）再展平笔记，`limit` 不生效、也不代表每页 16 条笔记。
4. **`wiki_update` 的 `new_title`**：顶层 `title` 选中页面、`new_title` 才是改名，两个参数可同时传；必须至少给一个 `wiki_page[...]` 属性，否则 400。
5. **重定向后的 200 不是写入确认**：校验失败只 flash 提示时也会重定向到同一目标页；别名/蕴含审批还会跳到 HTML-only 的任务页，可能拿到 500 或非 JSON；判定写入要对目标资源再查一次，不要盲目重试。
6. **`comment_list` 必须带 `post_id`**：不传时查询恒为 `post_id=0` 并返回空数组；要按分页读评论流用 `comment_search(query='')`（空列表是正常结果）。

与 Danbooru 面的差异：Moebooru 没有 `search[...]` 字典（过滤条件在顶层）；`data` 恒为表单，没有 JSON 请求体；认证是 `login` + `password_hash` 而非 HTTP Basic；`api_version` 只在 Moebooru 面存在。

## 示例命令

五个脚本都匿名只读，参数全部来自根配置 `examples.moebooru`（站点、标签、页码、条数等），不硬编码站点与代理；`--config` 指定配置，`--site` 覆盖站点名：

```bash
.venv/Scripts/python.exe examples/moebooru/list_posts.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/list_tags.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/wiki_list.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/list_comments.py --config pybooru.json
.venv/Scripts/python.exe examples/moebooru/related_tags.py --config pybooru.json
```

| 脚本 | 用途 |
| :--- | :--- |
| `list_posts.py` | 按标签分页列出帖子（打印 ID 与文件 URL） |
| `list_tags.py` | 按 `order` 列出标签及计数 |
| `wiki_list.py` | 搜索 wiki 页面标题 |
| `list_comments.py` | 用 `comment_search` 读评论流并打印真实条数（当前观察到 `comments: 0`） |
| `related_tags.py` | 查询相关标签，保留按查询标签分组的原始形态 |

## 边界与未实测

- 本页的调用只覆盖**匿名只读**；**写路径（上传、编辑、投票、删除、审核、账号动作）没有线上实测**，只按上游源码对齐。逐条状态与上游坐标见[契约审计附注](moebooru-contract-notes.md)，真实执行记录见 [verification.md](verification.md)。
- 示例命令那五个脚本已实际运行并退出 0；`sakugabooru` 的加盐模板取自站点自述，**没有发登录请求验证服务端是否接受**。
- 方法存在不等于站点启用了该能力：相似图服务、异步任务后端与站点自行关闭的功能都可能缺失，结果由服务端决定。

继续阅读：[方法参考](moebooru-api.md) · [能力总览](moebooru-capabilities.md) · [契约审计附注](moebooru-contract-notes.md) · [分页](pagination.md)。
