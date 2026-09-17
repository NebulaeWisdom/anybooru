# 向 Anybooru 贡献

感谢你有兴趣参与贡献！

## 资源

* [**项目文档**](docs/index.md)：`docs/` 下的中文 Markdown 文档。
* [源码仓库](https://github.com/NebulaeWisdom/anybooru)：源码安装入口；本库暂不发布到 PyPI。
* [代码示例](examples/)：Danbooru / Moebooru / Serika / e621ng 四个家族的可运行示例。
* [问题追踪](https://github.com/NebulaeWisdom/anybooru/issues)：Bug 与功能请求。

上游引擎源码是本项目的接口契约依据，本地只读参考，**不要修改、不要提交**：

* `danbooru/`：Danbooru 引擎（Ruby on Rails），路由见 `danbooru/config/routes.rb`。
* `moebooru/`：Moebooru 引擎，路由见 `moebooru/config/routes.rb`。
* `Serika.art/`：Serika 引擎，官方 v1 与站内路由见 `app/api/v1/**/route.ts` 与 `app/api/**/route.ts`。
* `e621ng/`：e621ng 引擎，路由见 `e621ng/config/routes.rb`。

## 行为准则

**互相尊重，保持愉快！**

## 我能做什么？

### 报告 Bug

报告前请先搜索 [已有 issue](https://github.com/NebulaeWisdom/anybooru/issues)，确认尚未被提交。Bug 使用
**Bug report** 模板创建：

* 描述性的标题
* 期望行为
* 实际行为
* 复现步骤（含代码）
* 环境信息（Anybooru 版本、Python 版本、站点、操作系统）

> 请勿在 issue、示例或提交中粘贴真实账号、API key、密码或代理凭据。

### 功能请求

请先搜索 [已有 issue](https://github.com/NebulaeWisdom/anybooru/issues)，确认尚未被请求。功能请求使用
**Feature request** 模板创建：

* 描述性的标题
* 功能的详细说明
* 为什么需要该功能、你会如何使用它、它能带来什么收益

新增站点级用法时，请说明对应家族的上游引擎路由与控制器，而不是某个站点的私有行为；四家族的
源码入口与依据见[契约审计附注导航](docs/index.md#按家族选文档)。

### 提交 Pull Request

1. 先按独立目的规划提交边界：每个 commit 只承担一个明确目的，便于单独审查、回退和挑选；
   存在依赖时按依赖顺序拆成多个小提交，不要把多个可分离的改动攒成一个大提交。
2. 填写 [Pull Request 模板](.github/pull_request_template.md)。
3. 遵循下方[代码风格](#代码风格)。
4. 提交前在本地准备环境并冒烟验证：

   ```bash
   python -m venv .venv
   .venv/Scripts/python.exe -m pip install -e .        # Windows
   .venv/bin/python -m pip install -e .                # Linux / macOS
   ```

   示例脚本从配置文件读取参数（默认是包内 `anybooru/anybooru.json`，见 [docs/configuration.md](docs/configuration.md)）。

## 代码风格

* **[PEP-8](https://peps.python.org/pep-0008/)**（不严格要求），
* **[Google Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)**。

其他约定：

* 站点地址、凭据、代理、超时、示例参数一律放在配置文件 `anybooru/anybooru.json`，禁止硬编码在代码里，
  也禁止用环境变量注入。
* 不做隐式兜底、不自动重试、不猜站点上限；服务端返回什么就原样暴露什么。
* 文档改动请同时更新 `docs/` 下对应的中文 Markdown。
