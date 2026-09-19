# 接入一个新图站（新家族）

把一个新图站接进 Anybooru 的维护者清单：做哪些事、产物放哪、哪些结论必须有真实证据。
照着现有代码抄比照本文写更快——可运行的完整样板是 `anybooru/gelbooru02.py` + `anybooru/api_gelbooru02.py`
+ `test/tbib.py` + `examples/gelbooru02/` + `docs/gelbooru02*.md` 这一套。

## 0. 先判断：已有家族，还是要新家族

- 判据是**契约**，不是站点名字或外观：路由形状、参数名、返回格式（JSON / XML）、认证方式、分页语义。
- **已有家族**：只加站点条目 + 冒烟脚本 + 该家族文档里的站点差异段落，不要复制第二个类。已有站点看
  `anybooru/anybooru.json` 的 `sites` 段；家族与站点对照看 [index.md](index.md)。
- **新家族**：先定三个名字，后面所有产物都用它——类名与模块名（`Gelbooru02` → `anybooru/gelbooru02.py`、
  `anybooru/api_gelbooru02.py`）、配置里的站点键（`tbib`）、文档前缀（`docs/gelbooru02*.md`）。
- 有上游引擎源码的家族（`danbooru/`、`moebooru/`、`Serika.art/`、`e621ng/`）：以路由与控制器的**文件 + 行号**
  为第一依据。没有源码的（Zerochan / Gelbooru / Gelbooru02 / Shuushuu）：以站点官方 API 页面、自带 OpenAPI、
  帮助页加**真实响应**为依据。依据等级图例见 [gelbooru-api.md](gelbooru-api.md) 开头。
- Sakuria 连官方 API 页面与 OpenAPI 都没有，证据等级更弱：只把本轮匿名响应支持的结论写成契约，
  输入文档作为候选；未复测项集中标明，矛盾见 [sakuria-contract-notes.md](sakuria-contract-notes.md)。
- 不要 clone 与本次无关的仓库，不要修改只读参考源码。

## 1. 摸契约（只读、匿名、串行）

- 每条只发一次请求、相邻请求间隔 ≥1.2 秒、不重试、不并发；不登录、不发写请求、不下载图片。
- 每条记录四样东西：**真实 URL、HTTP 状态码、`Content-Type`（哪怕它与正文格式不符）、正文首层结构与字段名**。
- 必查：列表、详情、分页参数与语义（页码还是游标）、每页上限、匿名可用性、需要凭据的端点、错误路径
  （不存在的 id、越界页码）。
- 站点自述的上限与实测冲突时写“未证实”，**不要**在客户端里做钳位。
- 302 / 500 / 空正文 / `Content-Type` 与正文不一致这类怪行为照实写进 `docs/<family>-api.md` 与
  `docs/<family>-contract-notes.md`；代码不特判、不重试、不降级。
- 探测脚本与原始响应是一次性产物：放仓库忽略的临时目录，不要提交。

## 2. 客户端

两个文件，照抄最接近的家族：

- `anybooru/<family>.py`：薄壳。构造函数（`site_name` / `site_url` / 该引擎真正需要的凭据 / `config_file` /
  `timeout` / `user_agent`）、认证怎么带、通用入口 `request(...)`。样板：`anybooru/danbooru.py`（HTTP Basic）、
  `anybooru/moebooru.py`（`password_hash`）、`anybooru/shuushuu.py`（默认匿名、显式登录换 Bearer token）、
  `anybooru/gelbooru02.py`（JSON 与 XML 原文两种形态）。
- `anybooru/api_<family>.py`：Mixin，每个原生方法一个小函数——拼路由、带参数、返回响应。样板
  `anybooru/api_gelbooru02.py`。
- 返回**原样**：JSON 完整解析后返回；XML 等非 JSON 返回 `response.text` 原文，连声明、根、属性和空白一起给。
  不猜外层键、不拆层、不改字段名、不做格式嗅探、不自动回退格式。
- 导出写进 `anybooru/__init__.py`。
- 参数不进代码：站点、凭据字段、冒烟查询值写进包内 `anybooru/anybooru.json`（`sites` 段与 `smoke` 段）。

## 3. 冒烟脚本 `test/<站点>.py`

- 一站点一文件，**最多 10 次匿名只读请求**；不引入测试框架、mock、额外依赖或 CI。
- 在十次预算内选代表性的列表、详情、分页与一条预期错误路径（越界页码、不存在的 id）。账号与写操作一律不测；
  方法较多时不要为全覆盖突破预算，实际覆盖与未实测方法写进验证记录。
- 每行一条：`PASS/FAIL <检查名> | <真实 URL> | HTTP <状态码> | <关键字段>`，末尾
  `SUMMARY <site> | requests=N | passed=… failed=…`；有失败就退出 1。样板 `test/tbib.py`。
- 查询参数从 `smoke` 段读，不要硬编码在脚本里。

## 4. 示例 `examples/<family>/`

- 至少两个：一个列表 / 搜索（分页、过滤），一个按资源浏览（详情、标签、评论之类）。样板
  `examples/gelbooru02/list_posts.py` 与 `examples/gelbooru02/browse_resources.py`。
- 查询值来自 `examples` 段，`--config` / `--site` 用法与其它家族一致；教学代码块要能直接抄，
  写法见 [CONTRIBUTING.md](../CONTRIBUTING.md#文档风格)。

## 5. 四份家族文档

- `docs/<family>.md`：这个类怎么用（构造、认证、`request()`、返回值、`last_call`、常见坑），不列全量方法。
- `docs/<family>-api.md`：每个方法的参数、路由、真实返回字段或 XML 属性、可直接抄的示例。
- `docs/<family>-capabilities.md`：「我要做什么 → 用哪个方法」，加一行式完整方法索引。
- `docs/<family>-contract-notes.md`：依据出处（上游文件 + 行号，或 API 页面 / 帮助页 / OpenAPI 条目）、
  权限分支、排除项、文档与实现的矛盾。

## 6. 导航与元数据

- `docs/index.md`：家族选型表加一行，必要时补家族对照。
- `README.md`（家族清单、快速上手、目录）、`changelog.md`、`setup.cfg` 里列支持面的地方。
- 跨家族文档中与该家族相关的段落：`docs/configuration.md`（配置样例、怎么判断站点用哪个类）、
  `docs/installation.md`（模块清单）、`docs/migration.md`（迁移表）、`docs/pagination.md`（分页语义）、
  `docs/authentication.md`（认证方式）、`docs/errors.md`（该引擎特有的状态码含义）。
- `CONTRIBUTING.md`：契约依据里的家族清单与依据路径、示例数量。

## 7. 真跑与记录

- 用项目解释器跑冒烟与示例（匿名、只读、无凭据），记录命令、真实 URL、状态码与关键返回字段。
- 公开记录写进 `docs/verification.md` 的新小节，标题带家族 / 站点与日期；跑不了的（要账号、要写权限）
  照实标「未实测」，不要伪称跑过。
- 「只对过源码或文档、没真跑」的结论与「真跑过」的分开列，边界与未实测项集中写在该节里。
- 对外内容不得出现本机信息：代理地址与出口 IP、绝对路径、临时目录与证据文件名、维护者解释器路径、
  本机网络过程细节，一律写成中性表述。

## 8. 分支与提交边界

- **每次改动都开一条新分支**：从 `master` 切出按目的命名的分支（`feat/<family>-family`、`docs/<topic>`、
  `fix/<what>`），所有提交都落在分支上；等冒烟与示例真跑过、结果记进 `docs/verification.md` 之后，
  再普通合并回 `master`（不改写已推送的历史，功能分支保留）。不要直接在 `master` 上累积提交。
- 一个目的一条提交：客户端、配置、冒烟、示例、每份文档、导航与元数据、实测记录各自成条；每条都能单独
  审查、回退和挑选。
- 只读参考源码与内部文件不进提交。
