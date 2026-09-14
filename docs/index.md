# Pybooru 文档

Pybooru 是访问 Danbooru 系与 Moebooru 系图站 API 的 Python 客户端。
Danbooru 与 Moebooru 是被大量图站采用的引擎模板，所以本库对齐的是这两套引擎的**公共契约**
（上游 `config/routes.rb` 与对应控制器），而不是某个具体站点的私有行为。

## 文档索引

| 文档 | 内容 |
| :--- | :--- |
| [installation.md](installation.md) | 环境要求、源码/PyPI 安装、目录结构 |
| [configuration.md](configuration.md) | 根配置文件 `pybooru.json` 的完整结构与加载规则 |
| [authentication.md](authentication.md) | HTTP Basic（Danbooru）与 `password_hash`（Moebooru） |
| [pagination.md](pagination.md) | `page` / `limit` 的透传规则与游标分页 |
| [errors.md](errors.md) | 异常层次、`PybooruHTTPError` 字段、引擎状态码 |
| [danbooru.md](danbooru.md) | Danbooru 客户端构造、`request()` 通用入口、参数编码 |
| [danbooru-api.md](danbooru-api.md) | Danbooru 各 API 面：端点、参数、认证要求、路由来源 |
| [danbooru-artists.md](danbooru-artists.md) | 按 URL 查画师、pixiv 作者 ID → tag |
| [moebooru.md](moebooru.md) | Moebooru 面现状、构造与用法、未验证说明 |
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
   不在客户端做权限判断——服务端返回什么就原样交给调用者。
3. **通用入口 + 原生方法**：每个原生方法都是 `request(method, path, *, params, data, files)` 的
   薄封装；缺少原生方法的端点可以直接用 `request()` 访问，见 [danbooru.md](danbooru.md)。
4. **参数语义跟随引擎**：嵌套字典编码成 Rails 的 `a[b]` 形式，列表编码成 `a[]`，布尔编码成
   `true` / `false`，`None` 直接不发送。

## 验证状态

接口以本地上游引擎源码为契约依据（`danbooru/`、`moebooru/`，只读参考）。

* Danbooru 只读端点的匿名线上验证已在 `danbooru.donmai.us` 执行（12 次成功 + 3 次预期错误），
  逐条结果见 [verification.md](verification.md)；
* 所有需要登录的写接口都只做了**源码对齐**，**未做线上实测**；
* Moebooru 面本轮未重写，只同步了共享配置用法，**未做线上验证**，见 [moebooru.md](moebooru.md)。

## 许可

MIT License，见仓库根目录的 [LICENSE](../LICENSE)。
