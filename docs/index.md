# Pybooru 文档

Pybooru 是访问 Danbooru、Moebooru 与 Serika 三类引擎图站 API 的 Python 客户端。
契约以对应上游路由与控制器为准：前两者是 Rails 引擎，Serika 是独立的 Next.js 引擎，
同时提供官方 `/api/v1` 和前端自用的非版本化 `/api/*`。后者没有公共兼容保证，文档单独标明。

## 文档索引

| 文档 | 内容 |
| :--- | :--- |
| [danbooru-capabilities.md](danbooru-capabilities.md) | 不知道有哪些 API？按目的找入口、区分匿名/登录能力、浏览全部原生方法 |
| [installation.md](installation.md) | 环境要求、源码/PyPI 安装、目录结构 |
| [configuration.md](configuration.md) | 根配置文件 `pybooru.json` 的完整结构与加载规则 |
| [authentication.md](authentication.md) | HTTP Basic（Danbooru）、`password_hash`（Moebooru）、Bearer（Serika） |
| [pagination.md](pagination.md) | `page` / `limit` 的透传规则与游标分页 |
| [errors.md](errors.md) | 异常层次、`PybooruHTTPError` 字段、引擎状态码 |
| [danbooru.md](danbooru.md) | Danbooru 客户端构造、`request()` 通用入口、参数编码 |
| [danbooru-api.md](danbooru-api.md) | Danbooru 各 API 面：端点、参数、认证要求、路由来源 |
| [moebooru.md](moebooru.md) | Moebooru 客户端构造、`request()` 通用入口、认证与版本路径 |
| [moebooru-api.md](moebooru-api.md) | Moebooru 各 API 面：端点、参数、权限过滤器、路由来源 |
| [moebooru-capabilities.md](moebooru-capabilities.md) | 不知道有哪些 Moebooru API？按目的找入口、区分匿名/登录能力、浏览全部原生方法 |
| [serika.md](serika.md) | Serika 客户端、信封拆封、二进制字节与匿名示例 |
| [serika-api.md](serika-api.md) | Serika 官方 v1 全路由、认证与源码/官方文档差异 |
| [serika-capabilities.md](serika-capabilities.md) | Serika 两层能力、站内非版本化匿名路由与不支持的会话写操作 |
| [migration.md](migration.md) | 从 Pybooru 4.x 迁移到 5.x 的逐项对照 |
| [verification.md](verification.md) | 线上验证状态：已实测与未实测清单 |

## 三行上手

```python
from pybooru import Danbooru

with Danbooru('danbooru') as client:            # 读取当前目录的 pybooru.json
    example = client.config['examples']['danbooru']
    posts = client.post_list(tags=example['tags'], limit=example['limit'])
    print(posts[0]['id'], posts[0]['tag_string'])
```

`'danbooru'` 是根配置文件 `sites` 段的键名；站点地址、凭据、代理、超时都在那里。
调用参数一律不硬编码在代码里，完整约定见 [configuration.md](configuration.md)。

## 设计立场

理解这几点，基本就理解了本库的行为边界：

1. **一份显式配置**：`pybooru.json` 是唯一的参数来源，没有环境变量、没有隐藏搜索路径、
   没有内置站点后备。
2. **不做隐式兜底**：不猜站点能力、不限制未知的 `search[...]` 参数、不自动翻页、不自动重试、
   不在客户端做权限判断——HTTP 错误保留服务端状态与正文。
3. **通用入口 + 原生方法**：三个家族都有 `request()` 通用入口，原生方法是它的薄封装；
   见 [danbooru.md](danbooru.md)、[moebooru.md](moebooru.md)、[serika.md](serika.md)。
   Serika 官方信封拆成数据与 `last_call['meta']`；其站内 JSON 原样返回，图片方法返回 `bytes`。
4. **参数语义跟随引擎**：Rails 面的嵌套参数编码成 `a[b]` / `a[]`，布尔编码成 `true` / `false`，
   `None` 不发送；Danbooru 无文件时使用 JSON，Moebooru 恒用表单。Serika 的标签/评级查询是
   逗号分隔字符串，不识别 Danbooru 搜索语法；批量查询用 JSON，上传用 multipart。

## 验证状态

接口以本地上游引擎源码为契约依据（`danbooru/`、`moebooru/`、`Serika.art/`，只读参考）。

* Danbooru 只读端点的匿名线上验证已在 `danbooru.donmai.us` 执行（12 次成功 + 3 次预期错误），
  逐条结果见 [verification.md](verification.md)；
* Moebooru 面已按上游 `moebooru/` HEAD `206455e1` 的路由与控制器重写（90 个原生方法），
  匿名只读端点的执行记录同样记在 [verification.md](verification.md)；
* Serika 支持官方 v1 和站内非版本化匿名读取；实际匿名调用记录见 [verification.md](verification.md)，
  所有需 API key 的路由仅源码对齐，未实测成功响应，不因有版本号就视为已验证；
* 所有需要登录的写接口都只做了**源码对齐**，**未做线上实测**。

## 许可

MIT License，见仓库根目录的 [LICENSE](../LICENSE)。
