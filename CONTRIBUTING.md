# 向 Anybooru 贡献

感谢你有兴趣参与贡献！本文件说明这个仓库的代码约定、文档约定和验收方式；动手前请先读完。

## 资源

* [**项目文档**](docs/index.md)：`docs/` 下的中文 Markdown，十二个家族各四份（客户端用法 / 方法参考 /
  能力入口 / 契约审计附注），另有安装、配置、认证、分页、错误、迁移与验证记录。
* [源码仓库](https://github.com/NebulaeWisdom/anybooru)：源码安装入口；本库暂不发布到 PyPI。
* [新增图站流程](docs/adding-a-site.md)：把一个新站点接进本库的维护者清单（判引擎、摸契约、写客户端、
  冒烟与示例、四份家族文档、导航与元数据、实测记录、提交边界）。
* [代码示例](examples/)：Danbooru / Moebooru / Serika / e621ng / Zerochan / Gelbooru / Gelbooru02 / Shuushuu / Sakuria / Anime-Pictures / Cosine / Nhentai 十二个家族共 33 个可运行脚本。
* [问题追踪](https://github.com/NebulaeWisdom/anybooru/issues)：Bug 与功能请求。

## 契约依据（只读参考，不要修改、不要提交）

前四个家族的上游引擎源码是本项目的接口契约依据，它们各自是独立仓库，本地只读：

* `danbooru/`：Danbooru 引擎（Ruby on Rails），路由见 `danbooru/config/routes.rb`，控制器在
  `danbooru/app/controllers/`，默认配置在 `danbooru/config/danbooru_default_config.rb`。
* `moebooru/`：Moebooru 引擎，路由见 `moebooru/config/routes.rb`，帮助文字在
  `moebooru/app/views/help/api.en.html.erb`（帮助页有历史遗留的错误说法，以路由与控制器为准）。
* `Serika.art/`：Serika 引擎，官方 v1 在 `app/api/v1/**/route.ts`，站内面在 `app/api/**/route.ts`。
* `e621ng/`：e621ng 引擎，路由见 `e621ng/config/routes.rb`，帖子序列化在 `app/blueprints/`。

**Zerochan、Gelbooru、Gelbooru02（TBIB）、e-shuushuu、Sakuria 与 Anime-Pictures 没有可引用的本地上游服务端源码**：

* `zerochan.net` 只在站内 API 页面写契约，没有公开的引擎仓库，本仓库拿不到可引用的源码或行号。依据是
  **官方 API 页面快照 + 真实请求实测**，逐条出处、与实现的差异以及排除项（`xml` 格式、meta 标签、限流语义）
  记在 [`docs/zerochan-contract-notes.md`](docs/zerochan-contract-notes.md)。
* `gelbooru.com` 使用 `index.php`：dapi 用 `json=1` 请求 JSON，`autocomplete2` 本身返回 JSON，
  标签页、帖子页和 wiki 是 HTML。本轮没有找到可核对当前部署的官方 PHP 源码；依据是**官方 wiki/帮助页与站点脚本
  + 真实匿名响应**，来源层级、未实测项与排除项记在
  [`docs/gelbooru-contract-notes.md`](docs/gelbooru-contract-notes.md)。不要拿旧版本的 PHP 代码当现役契约，
  也不要从别家引擎的返回结构推断它的字段。
* `tbib.org` 自述 `Running Gelbooru 0.2`，接口同样是站点的 `index.php`：帖子加 `json=1` 返回 JSON，
  标签与评论在加/不加 `json=1` 的实测中均返回 XML。依据是站点 `index.php?page=help&topic=dapi` 帮助页与
  **真实匿名响应**；没有服务端源码快照，不要推测补丁版本、实现语言或未观察到的字段，也不要把
  `gelbooru.com` 的 dapi 字段套过来。来源层级与排除项记在
  [`docs/gelbooru02-contract-notes.md`](docs/gelbooru02-contract-notes.md)。
* `e-shuushuu.net` 是独立 REST API，依据是站点自带 [OpenAPI](https://e-shuushuu.net/api/openapi.json)
  的路径、参数和响应 schema 加真实响应；不是 Danbooru/Moebooru 模板。详见
  [`docs/shuushuu-contract-notes.md`](docs/shuushuu-contract-notes.md)。
* `sakuria-api.syarolia.com`（Pixiv 第三方镜像站）**没有官方 API 页面、没有 OpenAPI、没有上游源码**，
  是本仓库依据最弱的一档：只有匿名响应观察加随后的一次有界实测（每个请求只发一次），本轮只证样本、
  不泛化任何枚举与上限。样本之外的候选字段、未复测的错误码与分页语义一律不得当成返回值承诺，
  `/me/*` 更是需要登录且未实测。逐条记在
  [`docs/sakuria-contract-notes.md`](docs/sakuria-contract-notes.md)。
* `api.anime-pictures.net`（Anime-Pictures，站点自研的 `api/v3` JSON 接口）**没有可读到的官方 API 手册页**
  （手册页存在但整站受 Cloudflare 质询）、**没有 OpenAPI、没有服务端源码**。依据是**匿名只读响应实测**
  加候选输入资料（输入引用的外部客户端源码链接本轮没有独立读过）。API 主机 `api.anime-pictures.net`
  与网页主机 `anime-pictures.net` 分开，不要依赖网页主机上的 `/api/v3/*` 302；旧版 `/api/v2/*` 与
  `/pictures/view_posts/*` 在 API 主机上实测 `404` 空正文，不包装。帖子不存在是 `410` 而不是 `404`，
  非法路径段是 `400` 加 `text/plain`（不是 JSON）；`post_tags` 与 `image_get` 匿名 `403`，
  POST 与带凭据的成功路径未实测。来源层级、未实测项与输入矛盾记在
  [`docs/anime-pictures-contract-notes.md`](docs/anime-pictures-contract-notes.md)。

* `pic.cosine.ren`（Cosine，Telegram 频道 `@CosineGallery` 的配套图站，Next.js + Prisma + Meilisearch
  自研 API）**没有本地上游服务端源码**：站点前端代码在公开仓库里，但本轮只按需只读了个别文件当线索
  （不 clone、不写行号），公开结论以匿名只读响应为准。它不是 booru：`/api/list`、`/api/artwork/{id}`、
  `/api/random`、`/api/search`、`/api/tag` 与 `/api/tags`、`/api/artist` 与 `/api/artists`、`/api/search/admin`
  与 `/feed.xml` 各走自己的路由与参数名，四种返回外壳（superjson、`images`+`total`、`success`+`data`、裸数组）
  本库一个都不拆；`POST /api/search/admin` 会重建或删除**站点**搜索索引，`POST /api/artwork/revalidate`
  需要站点服务端密钥，两者本轮都未执行。来源层级、与输入资料的矛盾与未实测项记在
  [`docs/cosine-contract-notes.md`](docs/cosine-contract-notes.md)。

* `nhentai.net`（Nhentai，站点自带的 `.net` API v2）**没有本地上游服务端源码**：依据是站点自带的
  [OpenAPI](https://nhentai.net/api/v2/openapi.json)（OpenAPI 3.1.0，98 paths / 114 operations /
  129 schemas）加匿名只读响应。引用 OpenAPI 条目时写 JSON Pointer 与 `operationId`（例如
  `#/paths/~1api~1v2~1galleries/get`、`get_all_galleries_api_v2_galleries_get`），没有服务端行号可写，
  不要编。它的返回形状与任何现有家族都不同：作品列表是 `{"result": […], "num_pages": …, "per_page": …,
  "total": …}`、`gallery_popular` 是裸数组、`tag_show` 是裸对象、`gallery_random` 是 `{"id": …}`，
  分页是 `page` + `per_page`，认证是 `Authorization: Key`。已实测的契约与实现的矛盾：OpenAPI 把非法 `page`
  与超上限的 `per_page` 记作 `422`，实测是 `400`。`nhentai.to` 一类克隆站被排除，不当作 `.net` 的替代基址。
  来源层级、排除项与未实测项记在 [`docs/nhentai-contract-notes.md`](docs/nhentai-contract-notes.md)。

改动这八个家族请区分站点说明、公开前端文件、帮助页/OpenAPI、脚本行为与真实响应；候选字段的推断必须显式标明，
不能当成返回值承诺。四个源码家族与它们是两条不同的依据路径，不存在“十二个家族都有源码依据”。

## 我能做什么？

### 报告 Bug

报告前请先搜索 [已有 issue](https://github.com/NebulaeWisdom/anybooru/issues)，确认尚未被提交；
Bug 使用 **Bug report** 模板创建。一份能直接定位问题的报告包含：

* 标题里写明家族或类名（例如 `Zerochan.entry_list`、`E621.post_list`）；
* 期望行为与实际行为：贴出**完整调用**（类名、字面实参、`--config` / `--site` 取值）与它返回的东西；
* 真实请求地址：`client.last_call['url']` 是含查询串的最终 URL，例如
  `https://danbooru.donmai.us/posts.json?tags=rating%3Ag&limit=3`——它比“请求失败”有用得多；
* HTTP 状态码与正文：`AnybooruHTTPError` 带 `http_code` / `url` / `body` / `data`，`AnybooruAPIError`
  表示 2xx 但正文不是 JSON；
* 环境：Anybooru 版本（`anybooru.__version__`）、Python 版本、站点与操作系统。

> 请勿在 issue、示例或提交中粘贴真实账号、API key、密码、cookie 或代理凭据；也不要粘贴整份私有配置文件，
> 只保留出问题的 `sites` / `examples` 片段。

### 功能请求

请先搜索 [已有 issue](https://github.com/NebulaeWisdom/anybooru/issues)，确认尚未被请求；功能请求使用
**Feature request** 模板创建，写明：

* 属于哪个家族与哪个引擎，以及你期望的调用形态（方法名、参数、返回值里你要用到的字段）；
* 依据：Danbooru / Moebooru / e621ng / Serika 请给出上游路由与控制器位置（文件与行号更好）；
  Zerochan 请给出 API 页面出处与实测响应；Gelbooru 请给出官方 wiki/帮助页或页面脚本的出处与实测响应；
  Gelbooru02（TBIB）请给出 `index.php?page=help&topic=dapi` 的条目或真实匿名响应（注明是 XML 还是 JSON）；
  Shuushuu 请给出官方 OpenAPI 路径、参数或 schema 名，以及实际执行范围；
  Sakuria 请给出可复现的匿名响应（请求 URL、状态码、正文关键字段）与执行范围——它没有官方页面、OpenAPI 与源码，
  本站候选输入不是契约；
  Anime-Pictures 请给出可复现的匿名响应（API 主机 `api.anime-pictures.net` 上的请求 URL、状态码与正文关键字段）
  以及执行范围——它同样没有可读到的官方手册页、OpenAPI 与源码，外部客户端源码链接只能当线索，不能当契约；
  Cosine 请给出可复现的匿名响应（请求 URL、状态码与正文关键字段）与执行范围，并注明结论有没有公开前端文件
  支撑（只写文件、不编行号）——它没有本地上游服务端源码、OpenAPI，也没有可读到的官方手册页；
  Nhentai 请给出站点自带 [OpenAPI](https://nhentai.net/api/v2/openapi.json) 的条目（JSON Pointer 或
  `operationId`，例如 `#/paths/~1api~1v2~1galleries/get`）以及可复现的匿名响应（请求 URL、状态码与正文关键字段）
  与执行范围——它同样没有本地上游服务端源码，也没有别的契约来源；`.to` 一类克隆站的行为不算 `.net` 的契约。
  **不要以某个站点的私有行为当契约**。

### 提交 Pull Request

1. **每次改动都开一条新分支**：从 `master` 切出按目的命名的分支（例如 `feat/gelbooru02-family`、
   `docs/adding-a-site`、`fix/moebooru-password-hash`），所有提交都落在这条分支上；等改动做完、
   冒烟与示例真跑过、结果记进 `docs/verification.md` 之后，再普通合并回 `master`（不改写已推送的历史，
   功能分支保留）。不要直接在 `master` 上累积提交。
2. 先按独立目的规划提交边界：每个 commit 只承担一个明确目的（例如“修正 Moebooru 合集写操作的动词”、
   “补齐 e621 标签的搜索字段”），便于单独审查、回退和挑选；存在依赖时按依赖顺序拆成多个小提交，
   不要把多个可分离的改动攒成一个大提交。
3. 填写 [Pull Request 模板](.github/pull_request_template.md)，在“如何验证”里写清你实际执行的命令与输出。
4. 遵循下方[代码风格](#代码风格)与[文档风格](#文档风格)。
5. 在本地准备环境并真跑一次改动涉及的路径：

   ```bash
   python -m venv .venv
   .venv/Scripts/python.exe -m pip install -e .        # Windows
   .venv/bin/python -m pip install -e .                # Linux / macOS

   .venv/Scripts/python.exe examples/danbooru/list_posts.py
   .venv/Scripts/python.exe examples/zerochan/list_entries.py
   .venv/Scripts/python.exe examples/gelbooru/autocomplete.py
   python examples/gelbooru02/list_posts.py
   .venv/Scripts/python.exe examples/shuushuu/search_images.py
   .venv/Scripts/python.exe examples/sakuria/search_illusts.py
   .venv/Scripts/python.exe examples/anime_pictures/list_posts.py
   .venv/Scripts/python.exe examples/anime_pictures/browse_resources.py
   .venv/Scripts/python.exe examples/cosine/list_images.py
   .venv/Scripts/python.exe examples/cosine/browse_resources.py
   .venv/Scripts/python.exe examples/nhentai/list_galleries.py
   .venv/Scripts/python.exe examples/nhentai/browse_resources.py
   ```

   示例脚本默认读包内 `anybooru/anybooru.json`，用 `--config` 指向自己的配置、用 `--site` 换站点。
   代理等请求设置来自 `request`，凭据来自 `sites`，示例查询值来自 `examples`。
   示例按需真跑：运行过的记录命令、URL、状态与返回；没有运行的照实标“未实测”，不要求为补齐数量逐一请求。
6. 需要凭据或会产生写入的路径（例如 `examples/danbooru/comment_create.py`）在提交说明里明确标注
   “未执行、未实测”，并写清依据的源码位置与请求体形状；不要为了凑验证去发写请求。

### 轻量匿名冒烟

`test/` 是唯一保留测试脚本的目录：一站点一文件，每文件最多 10 次匿名只读 HTTP 请求，
不引入测试框架、mock、依赖或 CI 检查。例如 `python test/danbooru.py --config <你的配置文件>`；
具体预算、输出与配置用法见 [README](README.md#轻量匿名冒烟检查)。按改动涉及的站点运行，
不要为凑覆盖率重复请求；真实 URL、状态/异常、请求次数和退出码追加进 `docs/verification.md`。

## 代码风格

* [**PEP-8**](https://peps.python.org/pep-0008/)（不严格要求）与
  [**Google Python Docstrings**](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)。
* 库实现与仓库可运行示例的站点、凭据、代理、超时、User-Agent 和查询输入来自配置，不用环境变量注入。
  **教学文档不同**：要直接写字面参数，不能让读者再查配置键才能知道这行代码做什么。
* 不做隐式兜底、不自动重试、不猜站点上限、不写本地参数校验；服务端返回什么就原样暴露什么，
  错误保持原状态码与正文。
* 一个家族的客户端只包装**该引擎自己**的路由：不把别的引擎的参数名、默认值或返回结构搬过来，
  也不为旧行为保留别名或垫片。
  新增方法要给出依据（路由与控制器的文件位置；Zerochan 为 API 页面出处 + 实测响应，Gelbooru 为官方
  wiki/帮助页或页面脚本出处 + 实测响应，Gelbooru02 为 TBIB 帮助页条目与真实响应，
  Shuushuu 为 OpenAPI 路径/schema + 实测响应，Sakuria 与 Anime-Pictures 为可复现的匿名响应与执行范围，
  Nhentai 为站点自带 OpenAPI 的路径/schema（JSON Pointer 或 `operationId`）+ 实测响应），
  并在对应家族的 `docs/<家族>-api.md` 里补参数与返回字段。

## 文档风格

* **第一标准是使用者看得懂、抄得走**：只复述方法名的句子（`post_list` → “获取帖子列表”）不合格；
  每段要给出读者从方法名猜不到的信息——具体参数与取值、真实 URL、返回字段、状态码、数量或边界。
* 每个方法写清“给什么 → 返回什么”，并且用**真实字段名**说。例子：`entry_show(3793685)` 给一张图的编号，
  返回这张图的 `small` / `medium` / `large` / `full` 四种尺寸地址、`width` / `height`、`size`、
  `source`、`primary`（primary 标签名）与 `tags`。
* **参数表必须写全**：名称、类型与取值枚举、含义、不传时的行为（上游没写就写“未规定”）、一个可以直接
  复制的例子。不要用抽象的 `**params` 描述代替已知参数表。
* **教学代码块必须自足**：自己 `import`，用 `with Class('site') as client:`，参数写字面值，例如
  `client.entry_list(tags='Genshin Impact', strict=True, l=2)`；不要写 `client.config['examples'][...]`
  这类间接查找，也不要在代码里加默认值提取或模拟请求来制造成功。变量名要等于它装的内容
  （`primary_tag_entries = ...`，不是 `strict = ...`）。
* 需要凭据、写操作或无法匿名执行的代码单独列出并标注**未执行 / 未实测**，参数、请求体与源码依据仍要写全；
  不能因为跑不了就把方法删掉，也不能伪称验证过。
* 文档按文件分工，同一件事不写四遍：`docs/<家族>.md` 客户端怎么用、`docs/<家族>-api.md` 全部方法的参数与
  返回字段、`docs/<家族>-capabilities.md` 想做什么 → 用哪个方法、`docs/<家族>-contract-notes.md` 出处与
  排除项；真实执行记录集中写在 `docs/verification.md`。
* 对外发布的文档与产物不得出现本机信息：代理地址、出口 IP、绝对路径、临时目录与本地证据文件名一律写成
  中性表述或占位符。
