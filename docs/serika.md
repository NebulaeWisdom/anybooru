# Serika 客户端

`Serika` 是与 `Danbooru` / `Moebooru` 并列的第三个引擎客户端，支持 `serika.art` 及运行相同引擎的自托管实例。
权威是本地只读 `Serika.art/app/api/**/route.ts`；官方说明与控制器冲突时以控制器为准，不模仿 Rails 搜索或认证。

## 两个契约面

| 面 | 方法命名 | 稳定性与实测范围 |
| :--- | :--- | :--- |
| 官方 `/api/v1` | `image_list` / `stats` 等 16 个方法 | 有版本号，官方文档只收录其中 10 个动词，其余按控制器补齐；12 个需 key 方法仅源码对齐，成功路径未实测 |
| 站内 `/api/*` | `internal_*`，14 个方法 | 非版本化私有契约，前端自用，可能随时改；本轮仅封匿名公开读取，不含会话写操作 |

逐条官方参数与权限见 [serika-api.md](serika-api.md)，站内逐路由、未实测项与排除理由见
[serika-capabilities.md](serika-capabilities.md)。**有版本号、已被官方文档收录、已实测是三个不同的事实**。

## 构造与自托管实例

```python
from pybooru import Serika

with Serika('serika', config_file='pybooru.json') as client:
    print(client.stats())
```

```python
Serika(site_name=None, site_url=None, api_key=None, proxies=None,
       *, config_file='pybooru.json', timeout=None, user_agent=None)
```

| 参数 | 说明 |
| :--- | :--- |
| `site_name` | 根配置 `sites` 下的键，条目包含 `url` 与 `api_key`；不表示仅支持预置清单 |
| `site_url` | 显式覆盖地址；不用命名站点时由调用方提供，库没有地址后备 |
| `api_key` | 覆盖配置的 key；空字符串不附认证头，非空附 `Authorization: Bearer <key>` |
| `proxies` / `timeout` / `user_agent` | 覆盖根 `request` 对应项；requests 会话关闭 `trust_env`，不读环境变量 |
| `config_file` | 显式配置路径，默认当前工作目录下 `pybooru.json`，不搜索安装目录 |

自托管实例：在根 `sites` 新增与 `sites.serika` 相同的两字段条目，把 `url` 改为实例根地址，
再把该键传给 `Serika`。无须复制代码，也没有自动探测/自动切换引擎；其他部署**尚未实测**。
配置是应用输入，示例中的代理、分页、评级与图片尺寸全部来自 [pybooru.json](../pybooru.json)。

本轮 `api_key` 保持空值，不申请凭据。`username`、密码哈希、浏览器 cookie 登录都不是本家族的构造参数。
站内 API 的会话 token 与官方 API key 是不同凭据；本库只实现后者的发送，且本轮未实测其认证成功路径。

## 通用请求入口

```python
request(method, path, *, params=None, data=None, files=None,
        binary=False, envelope=None)
```

* `path` 是相对路径，例如 `api/v1/stats`；不自动补 `.json` 或 API 版本。原生方法会对每个动态路径段转义，
  通用入口中的完整路径由调用方转义。
* `params` 是扁平查询字典。布尔变为小写 `true` / `false`，`None` 不发送。
  `tags`、`ratings`、`exclude_tags` 是逗号分隔字符串，不是 Python 列表，不接受 Danbooru 搜索表达式。
* `data` 在没有 `files` 时作为 JSON 体发送，保留显式空数组；有 `files` 时改为 multipart 表单。
  `image_batch` 的 `ids` 是 JSON 数组；`upload` 的 `tags` 是表单中的 JSON 文本或 CSV 文本，两者别混。
* `upload` 的单文件参数需传 requests 三元组 `(filename, fileobj, content_type)`，明确 part MIME。
  裸文件对象不带正确的 part Content-Type 会被服务端的文件类型校验拒绝；库不猜扩展名，文件由调用者关闭。
* 不检查 key 权限、不钳位参数、不自动重试、不自动翻页，也不会把官方错误改走站内路由。

## 返回值与信封

| 路径或模式 | Python 返回值 | 元数据 |
| :--- | :--- | :--- |
| 官方标准 JSON 方法 | `data` 字段 | 整个服务端 `meta` 放入 `last_call['meta']` |
| `api_index()` | 原始裸 dict，无 `success` / `data` 信封 | 响应头、URL、状态在 `last_call` |
| `user_list()` | `users` 数组 | 服务端无 `data` / `meta`；把 `pagination` 放入 `last_call['meta']['pagination']`，不编造 timestamp |
| `internal_*` | 原始 JSON，例如 `{success, images, pagination}` | 不拆站内信封，分页仍在返回体 |
| `random_image()` | 原始 `bytes` | `Content-Type` 与可选的 `X-Image-Id` / `X-Post-Id` 等在 `last_call['headers']` |
| JSON 通路的空成功 | `None` | 保留 `last_call` |
| 二进制通路的空成功 | `b''` | 不尝试 JSON 解码 |

`request()` 默认 `envelope=None`，返回原始 JSON；`envelope='data'` / `'users'` 是两个明确的
官方响应模式，不做形状猜测或后备字段搜索。原生方法会选择对应模式，`binary=True` 使用独立的二进制通路。
`last_call` 总是只表示**最近一次**请求；下一次请求会清除旧的 `meta`，要跨请求保留分页请先自行保存。

```python
with Serika('serika', config_file='pybooru.json') as client:
    example = client.config['examples']['serika']
    users = client.user_list(**example['user_query'])
    print(users, client.last_call['meta']['pagination'])
    picture = client.random_image(**example['random_size'], **example['random_query'])
    print(len(picture), client.last_call['headers']['Content-Type'])
```

## ID、过滤与站点侧差异

1. **图片 ID 不互换**：`image_show` / `image_delete` / `image_similar` / `image_batch` 用内部 `images.id`
   （响应中 `id` / `dbid`）；`internal_image_show` / `internal_image_comments` 用 `sequential_id`，即 `post_id`。
   本轮实际列表→详情链拿到 `id=7323837`、`post_id=4237836`。官方文档对 v1 详情写 sequential ID，代码却用内部 ID。
2. **safe 默认来自服务端**：使用 `ratingFilter` 的列表、随机、搜索图片与热门接口，不给 `ratings` 时只看 safe。
   详情、similar 等按各自控制器规则，不对全家族做统一评级过滤。
3. **未知标签不总是 404**：v1 图片列表和随机元数据在全部标签不存在时返回空数组，部分不存在才 `404 TAG_NOT_FOUND`；
   站内图片列表还受标签缓存影响。PNG 路由的代码在标签不存在或无交集时可能**直接丢弃标签过滤**，并非返回空结果。
4. **二进制 200 不一定是选中图片**：服务端无结果可返回灰色占位 PNG，内部异常可返回红色占位 PNG，仍是 HTTP 200；
   元数据头可用于区分。客户端照原样返回 bytes，不把服务端占位图当成异常，也不伪造本地替代图片。
5. **数字默认与非法文本不同**：有些站内路由先对缺省值应用默认，再调用 `parseInt`；不能声称非法文本一定回默认。
   限值、排序枚举、过滤细节全部由对应控制器决定。

更多差异在 [官方参考的矛盾表](serika-api.md#文档与源码矛盾)。这些源码发现没有额外发请求探测。

## 错误处理

非 2xx 在 JSON 和二进制通路里都抛 `PybooruHTTPError`，有 `http_code`、`url`、`body`、`data`、
`response`；服务端提供 JSON `code` 时直接通过 `error.data['code']` 读取。非 JSON 错误正文的 `data` 为 `None`。
JSON 通路收到非空但不可解析的 2xx 正文抛 `PybooruAPIError`；网络异常保持 requests 的原异常。

当前 v1 控制器缺 key / 缺权限 / 限流分别是 HTTP 401 / 403 / 429，但均可带 `code: UNAUTHORIZED`。
`RATE_LIMITED` 只出现在它们未使用的辅助包装器与官方文字中；依 HTTP 状态与原始正文共同判断，不能只看 code。
本轮没有新跑错误请求或 key 请求；这里只记录源码与既有错误类的行为，不宣称这些成功/失败分支已实测。

## 可运行示例

三个脚本均支持 `--config` 与 `--site`，默认站点取自 `examples.serika.site`；只调用匿名可达路径：

```bash
.venv/Scripts/python.exe examples/serika/service_info.py --config pybooru.json
.venv/Scripts/python.exe examples/serika/browse.py --config pybooru.json
.venv/Scripts/python.exe examples/serika/random_image.py --config pybooru.json
```

* `service_info.py`：官方索引、统计、用户目录；展示裸 JSON、标准信封、users 例外三种返回形状。
* `browse.py`：站内图片列表→取首图 `post_id` 查详情，再读取标签和画师；不拿内部 id 误查站内详情。
* `random_image.py`：读图片 bytes，打印字节数、真实 Content-Type 与响应头，不自动保存图片。

**三个脚本已实际运行，均退出 0，共 8 个 HTTP 200**；完整参数与输出摘要见
[verification.md](verification.md#serika2026-09-15-实现后的匿名调用)。这不代表其余 22 个方法已线上验证，
更不代表自托管部署、认证/权限/限流、上传/删除或全部参数组合已验证。
