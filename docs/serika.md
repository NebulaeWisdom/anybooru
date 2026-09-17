# Serika 客户端用法

`Serika` 与 `Danbooru` / `Moebooru` / `E621` 并列，是四个引擎客户端之一，访问 `serika.art` 及同引擎的
自托管实例。它有两面：官方版本化 `/api/v1` 与站内未版本化 `/api/*` 的匿名只读；选哪面看
[能力总览](serika-capabilities.md)，逐条签名看 [方法参考](serika-api.md)。

```python
from anybooru import Serika
with Serika('serika') as client:
    print(client.api_index()['name'])
```

```text
SerikaART API
```

这三行代码就是完整可跑的最小用法；展示的是 2026-09-15 匿名调用已记录的真实服务名，命令与响应摘要见
[verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。

## 构造与自托管实例

```python
Serika(site_name=None, site_url=None, api_key=None, proxies=None,
       *, config_file=None, timeout=None, user_agent=None)
```

| 参数 | 说明 |
| :--- | :--- |
| `site_name` | 配置 `sites` 下的键，条目包含 `url` 与 `api_key`；不表示仅支持预置清单 |
| `site_url` | 显式覆盖地址；不用命名站点时由调用方提供，库没有地址后备 |
| `api_key` | 覆盖配置的 key；空字符串不附认证头，非空附 `Authorization: Bearer <key>` |
| `proxies` / `timeout` / `user_agent` | 覆盖配置 `request` 对应项；会话关闭 `trust_env`，不读环境变量 |
| `config_file` | 配置文件路径；默认 `None`，即读随包安装的 `anybooru/anybooru.json`，传路径才读别的文件 |

自托管实例：在配置的 `sites` 新增与 `sites.serika` 相同的两字段条目，把 `url` 改为实例根地址，再把这个键传给 `Serika`；没有自动探测、没有引擎自动切换，也不需要复制代码。配置是应用输入，示例里的分页、评级与图片尺寸都来自 [anybooru.json](../anybooru/anybooru.json)。
`username`、密码哈希、浏览器 cookie 登录都不是本家族的构造参数；官方 API key 与站内会话 token 是两种不同凭据，本库只实现前者的发送。用完记得 `client.close()`，或用 `with` 语句块。

## 通用请求入口

```python
request(method, path, *, params=None, data=None, files=None,
        binary=False, envelope=None)
```

* `path` 是相对路径（例如 `api/v1/stats`），不自动补 `.json` 或 API 版本；原生方法会转义动态路径段，
  通用入口里的完整路径由调用方转义。
* `params` 是扁平查询字典：布尔落成小写 `true` / `false`，`None` 不发送。
  `tags`、`ratings`、`exclude_tags` 是逗号分隔**字符串**，不接受列表，也不接受 Danbooru 搜索表达式。
* `data` 在没有 `files` 时作为 JSON 体发送并保留显式空数组；有 `files` 时改为 multipart 表单。
  `image_batch` 的 `ids` 是 JSON 数组，`upload` 的 `tags` 是表单里的文本，两者别混。
* `upload` 的单文件参数用 requests 的 `(filename, fileobj, content_type)` 三元组并明确 part MIME；库不猜扩展名，文件对象由调用方关闭。
* 不检查 key 权限、不钳位参数、不自动重试、不自动翻页，也不会把官方错误改走站内路由。

## 返回值与信封

| 路径或模式 | Python 返回值 | 元数据 |
| :--- | :--- | :--- |
| 官方标准 JSON 方法 | `data` 字段 | 整个服务端 `meta` 放进 `last_call['meta']` |
| 两个信封例外 | `api_index()` 是裸 dict；`user_list()` 是 `users` 数组 | 两者服务端都没有 `data`/`meta`，`user_list` 的分页在 `last_call['meta']['pagination']` |
| `internal_*` | 原始 JSON，例如 `{success, images, pagination}` | 不拆站内信封，分页仍在返回体 |
| `random_image()` | 原始 `bytes` | `Content-Type`、`X-Image-Id`/`X-Post-Id` 等在 `last_call['headers']` |
| 空成功 | JSON 通路 `None`、二进制通路 `b''` | 不尝试 JSON 解码，保留 `last_call` |

`request()` 默认 `envelope=None` 返回原始 JSON；`envelope='data'` / `'users'` 是两个明确的官方响应模式，不做形状猜测或后备字段搜索。`last_call` 记录 `API`、`url`、`status_code`、`status`、`headers`，并总是只表示**最近一次**请求——下一次请求会清掉旧的 `meta`，跨请求保留分页要自己先存；可复制用例见[可运行示例](#可运行示例)与[方法参考](serika-api.md)的常用方法片段。

## 五个要记住的坑

1. **图片 ID 不互换**：官方 `image_show` / `image_delete` / `image_similar` / `image_batch` 用**内部图片 id**（响应里的 `id`/`dbid`），站内 `internal_image_show` / `internal_image_comments` 用**公开序号**（响应里的 `post_id`）；
   实测同图 `id=7323837`、`post_id=4237836`——官方文档对 v1 详情写顺序号，实现用的是内部 id。
2. **safe 默认只是局部的**：使用评级过滤的列表、随机、搜索图片与热门接口，不给 `ratings` 时只看 safe；详情、similar 等按各自规则，不做全家族统一。
3. **未知标签不总是 404**：图片列表与随机元数据只在**部分**标签不存在时回 `404 TAG_NOT_FOUND`，全部不存在时回空数组；站内列表还受标签缓存影响，PNG 随机图在无交集时可能返回**不含**这些标签的图。
4. **二进制 200 不一定是选中图片**：服务端无结果可返回灰色占位 PNG、内部出错可返回红色占位 PNG，都还是 HTTP 200；只有命中才带 `X-*` 元数据头。客户端照原样返回字节，不伪造替代图片。
5. **非法数字文本不保证回默认值**：不传的参数不会被补上，传了非数字文本时也不能假定服务端会回落默认；限值、排序枚举与过滤细节一律以服务端行为为准。

更细的对照与实现细节见[契约审计附注](serika-contract-notes.md#官方文档矛盾逐条)，本页只保留使用时要记住的结论。

## 错误处理

非 2xx 在 JSON 与二进制通路里都抛 `AnybooruHTTPError`，有 `http_code`、`url`、`body`、`data`、
`response`；服务端给了 JSON `code` 时用 `error.data['code']` 读取，非 JSON 错误正文的 `data` 为 `None`。
JSON 通路收到非空但不可解析的 2xx 正文抛 `AnybooruAPIError`；网络异常保持 requests 的原异常。
官方 v1 的缺 key / 缺权限 / 限流 HTTP 分别是 `401` / `403` / `429`，但**三者的正文 `code` 都可能等于
`UNAUTHORIZED`**，要连 HTTP 状态码与原始正文一起判断。详见 [errors.md](errors.md)。

## 可运行示例

三个脚本都支持 `--config` 与 `--site`，`--config` 省略即读包内默认配置，默认站点取自 `examples.serika.site`，只调用匿名可达路径：

```bash
.venv/Scripts/python.exe examples/serika/service_info.py
.venv/Scripts/python.exe examples/serika/browse.py
.venv/Scripts/python.exe examples/serika/random_image.py
```

* `service_info.py`：官方索引、统计、用户目录；展示裸 JSON、标准信封、users 例外三种返回形状。
* `browse.py`：站内图片列表 → 取首图 `post_id` 查详情，再读标签与画师；不拿内部 id 误查站内详情。
* `random_image.py`：读图片字节，打印字节数、真实 `Content-Type` 与响应头，不自动保存图片。

三条命令均已实际运行、退出 `0`，合计 **8 个 HTTP 200**（4 个官方 v1 + 4 个站内）；命令与逐调用输出见 [verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。

## 边界与未实测

* 已实测的只有上面那 8 次匿名调用；**官方 12 个需 key 的方法成功路径全部未实测**——本轮 `api_key` 保持空值，不申请、不索要凭据；站内另外 10 个方法仅源码对齐。
* 自托管部署（换 `site_url` 指到别的实例）未实测；认证成功路径、权限/限流、上传/删除、PNG 占位错误分支与参数组合均未实测；本页的源码级结论来自站点控制器，没有为它们额外发探测请求。
* 逐条状态与排除项见[契约审计附注](serika-contract-notes.md#路由清单与逐条状态)；能力与不提供的范围见[能力总览](serika-capabilities.md#本库不提供的能力)。
