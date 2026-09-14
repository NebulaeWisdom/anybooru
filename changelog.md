# Pybooru - Changelog

## Pybooru 5.0.0.dev1 - (2026-09-15)

以本地上游引擎源码（`danbooru/` HEAD `d4cdddd44`、`moebooru/` HEAD `206455e1`）为依据的整体重构。
**破坏性变更**，迁移步骤见 [docs/migration.md](docs/migration.md)。

### 配置与认证

- 站点、凭据、代理、超时、User-Agent、示例参数集中到根配置文件 `pybooru.json`；
  `config_file` 默认为当前工作目录下的该文件，缺失时抛 `FileNotFoundError`；
  不搜索安装目录、不读环境变量、没有内置站点后备。
- 删除 `resources.SITE_LIST` 与 `HTTP_STATUS_CODE`（站点清单改由配置提供）。
- 新增 `client.config`（解析后的配置）、`last_call` 记录每次请求的最终 URL 与状态。
- 认证改为按 “`username` 或 `api_key` 任一非空” 自动附加 HTTP Basic，缺项为空串；
  两项都空才匿名，凭据不完整由服务端返回 `401`，不再静默降级。

### 传输层

- 新增通用入口 `Danbooru.request(method, path, *, params=None, data=None, files=None)`；
  `path` 自动补 `.json`；`params` 用 Rails 括号编码；`data` 无文件时以 **JSON 请求体**发送
  （保留显式空数组等结构），带文件时改用 Rails 表单 / multipart。
- 会话复用连接并关闭 `trust_env`（代理只来自配置）；固定 `Accept: application/json`。
- 不做本地校验、不做本地分页上限、不自动重试、不做客户端鉴权。
- 空成功体（204 等）返回 `None`；HTTP 错误抛 `PybooruHTTPError(response)`，携带
  `http_code` / `url` / `response` / `body` / `data`；2xx 非 JSON 抛 `PybooruAPIError`。
- `Danbooru.close()` 与上下文管理器支持；Danbooru 面移除内部 `_get`。

### Danbooru API 面

- 全面重写为 227 个方法，逐条对齐 `config/routes.rb` 与各控制器/模型/策略；
  列表方法统一 `xxx_list(search=None, **params)`（帖子列表例外：过滤走 `tags` 元标签）。
- 补齐此前面向现役站点缺失的能力：`post_create`、`post_random`、post events/replacements/
  approvals/disapprovals/regenerations、投票列表、uploads 与 media assets、AI 标签、autocomplete、
  `source`、`related_tag` 全参数、favorite groups、forum 投票与访问记录、saved searches、
  site credentials、bans / ip bans / ip addresses / ip geolocations、mod actions、modqueue、
  moderation reports、news updates、reports、jobs、dtext links、reactions、user actions/events/
  feedbacks/name change requests、API keys、rate limits、`status`、bulk update requests、
  tag/note/wiki 版本、`artist_show_or_new`、`wiki_page_show_or_new`、dmail/forum 全标记已读。
- 修正旧实现的错误：`post_update` 的 `ost[source]`、`post_flag_show` 打到 appeals 表、
  `tag_update` 打到 `pools/<id>`、`note_update` 路由拼错、`wiki_versions_list` 键名拼错、
  `artist_create`/`artist_update` 调用不存在的 `self.get`、`upload_create` 的失效字段等。
- `post_replacement_create` 的本地文件使用 `post_replacement[replacement_file]` multipart 字段，文件句柄由调用者管理；此管理员写路径未实测。
- 删除无上游路由的方法：`post_versions_show`、`post_unvote`、`comment_unvote`、`artist_undelete`、
  `artist_banned`、`dmail_delete`（均给出替代调用）。

### Moebooru 面

- API 方法签名**保持原样**，只迁移共享配置加载、会话、编码与错误处理；
  构造器按 `sites` 段读取 `url` / `username` / `password` / `hash_string` / `api_version`。
- 线上可用性**未验证**。

### 文档

- 删除 Sphinx 文档树（`docs/source/`、`docs/Makefile`、`docs/make.bat`）、预览脚本与 `setup.cfg`
  的 `docs` / `all` extras；文档改为 `docs/` 下的中文 Markdown（安装、根配置、认证、分页、错误、
  各 Danbooru API 面、画师与 pixiv、Moebooru 现状、迁移）。
- README、CONTRIBUTING 更新为中文并与 5.x 契约一致；`docs` 链接不再指向已失效的 Read the Docs。
- 示例重写为从根配置 `examples` 段取参数，不再硬编码站点、代理、分页与作者 ID；
  删除引用旧接口的历史示例脚本。

### 工程整理

- 删除历史 CI 配置（`.travis.yml`、`appveyor.yml`）与临时入口脚本 `provisional_test.py`；
  保留与旧流程无关的发布工作流。PyPI 发布工作流见 `.github/workflows/publish_to_pypi.yml`。
- 删除只服务旧流程的工具脚本（`tools/`）。
- 新增 `MANIFEST.in`，把根样例 `pybooru.json` 与 `docs/`、`examples/` 带入 sdist。
- `setup.cfg` 移除过时的 Python 3.5 分类器与 `docs`/`all` extras（运行下限仍为 Python >= 3.6）。

### 验证

- 已在 `danbooru.donmai.us` 完成匿名只读验证（15 次请求：12 次 `200`，3 次预期错误
  `404`/`410`/`422`，另验证了重定向端点 `artist_show_or_new` 在 302 后仍返回 JSON），覆盖
  `post_list`（含搜索与游标分页）、`post_show`、`tag_list`、`artist_list`（按 pixiv URL + 布尔过滤）、
  `related_tag`、`wiki_page_list`、`wiki_page_show`、`comment_list`、`pool_list`；
  逐条记录见 [docs/verification.md](docs/verification.md)。
- 所有需要登录的写接口仅做到源码对齐，**未做线上实测**；
- Moebooru 面未做线上验证；
- 其他 Danbooru 系站点、站点可选能力（archive 版本历史、IQDB、上传链路）未验证。

## Pybooru 4.2.2 - (2020-10-17)

- Added 504 error to HTTP_STATUS_CODE [#52](https://github.com/LuqueDaniel/pybooru/pull/52) by [@chlorofomduck](https://github.com/chlorofomduck)
- Fixed Danbooru client.favorite_remove() [#51](https://github.com/LuqueDaniel/pybooru/issues/51) and all 204 responses.

## Pybooru 4.2.0 - (2020-06-06)

**Note**: Pybooru 4.2.0 Is the last version that support Python 2.7

- Add support for Lolibooru [#44](https://github.com/LuqueDaniel/pybooru/pull/44) by [@Nachtalb](https://github.com/Nachtalb)
- Add support for safebooru.donmai.us to default sites [#37](https://github.com/LuqueDaniel/pybooru/pull/37) by [@mirukana](https://github.com/mirukana)
- Add `count_posts()` function to Danbooru API [#35](https://github.com/LuqueDaniel/pybooru/pull/35) by [@mirukana](https://github.com/mirukana)
- Replaced all `http` URLs for `https` [#36](https://github.com/LuqueDaniel/pybooru/pull/36) by [@mirukana](https://github.com/mirukana)
- Fixes the file url in the download example [#39](https://github.com/LuqueDaniel/pybooru/pull/39) by [@Luk3M](https://github.com/Luk3M)
- Fixes `Moebooru._build_hash_string`
- Small refactors
- Small fixes

## Pybooru 4.1.0 - (2017-02-08)

- Pybooru: refactored `_get_status()`
- Python 3.6 support
- Fixed `PybooruHTTPError`
- Pybooru: now `site_name` and `site_url` are `@property`
- Remove Pylint references
- End of Python 2.6 support
- Danbooru: added `post_mark_translated()`
- Danbooru: added `post_unvote()`
- Danbooru: added `post_flag_show()`
- Danbooru: added `post_appeals_show()`
- Danbooru: added `post_versions_show()`
- Danbooru: added `post_versions_undo()`
- Danbooru: added `comment_undelete()`
- Danbooru: added `comment_vote()`
- Danbooru: added `comment_unvote()`
- Danbooru: added `artist_undelete()`
- Danbooru: added `tag_show()`
- Danbooru: added `tag_udpate()`
- Danbooru: added `wiki_delete()`
- New docstring format
- Added support for Danbooru accounts levels.
- Refactored api_moebooru.py
- Code improvements
- Documentation improvement

## Pybooru 4.0.1 - (2016/12/09)

- Fix problems with Pypi

## Pybooru 4.0.0 - (2016/12/09)

- Added support to Danbooru
- Now Danbooru and Moebooru are two separed classes
- Pybooru has been refactored
- Moebooru (only): added support for API versioning
- Added PybooruAPIError exception
- Added **last_call** attribute to Danbooru and Moebooru to store last request information
- Examples has been updated
- Added generated documentation to Pybooru (subsequently replaced by the Markdown documentation in this repository).
- Added some tools for Pybooru (tools folder)
- Refactored setup.py
- End of Python 3.2.x support
- Fixed parameter comparison (python 2.X only)
- In this version there's a nice amount of improvements

## Pybooru 3.0.1 - (2015/01/13)

- Minors changes

## Pybooru 3.0 - (2014/12/06)

- In this version there's a nice amount of code improvements
- Added compatibility with Python 3
- Pybooru now use requests
- Replace `"%s" % (foo)` for `"{0}".format(foo)`
- Improvement code style
- Added Travis CI to the project

## Pybooru 2.1.1 - (2013/12/26)

- Improve documentation style

## Pybooru 2.1 - (2013/10/14)

- Added login suppport for any Moebooru based site
- Fixed a bug: #c4b3435
- Added new information to setup.py
- Small changes
