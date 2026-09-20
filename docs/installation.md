# 安装

## 运行要求

| 项目 | 要求 |
| :--- | :--- |
| Python | >= 3.6 |
| 运行时依赖 | [requests](https://requests.readthedocs.io/) >= 2.26（安装时自动拉取） |
| 标准库依赖 | `json`、`os`（读取默认配置文件），无其他第三方依赖 |

本库不读环境变量，也不会去当前工作目录或用户目录搜索配置文件：所有可调参数都在一份 JSON 里显式声明，
默认读随包安装的 `anybooru/anybooru.json`（里面有 16 个站点条目 `serika`、`danbooru`、`safebooru`、
`konachan`、`yandere`、`sakugabooru`、`e621`、`e926`、`zerochan`、`gelbooru`、`tbib`、`shuushuu`、`sakuria`、
`anime_pictures`、`cosine`、`artstation`，
以及 `request` / `sites` / `examples` / `smoke` / `verification` 五段），怎么改见 [configuration.md](configuration.md)。

## 从源码安装（当前开发版）

```bash
git clone https://github.com/NebulaeWisdom/anybooru.git
cd anybooru

# 创建并激活虚拟环境
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .        # Windows
.venv/bin/python -m pip install -e .                # Linux / macOS
```

`-e`（editable）安装后，`import anybooru` 直接指向仓库里的源码，改动立即生效。

### 需要代理时

pip 支持显式指定代理，请不要用环境变量注入：

```bash
.venv/Scripts/python.exe -m pip install -e . --proxy http://proxy.example:8080
```

运行期的代理写在配置文件的 `request.proxies` 中。

## 打包与发布状态

本库目前**不发布到 PyPI**：请按上面的源码安装方式使用，不要依赖 `pip install Anybooru` 这类指令。
将来是否发包由维护者决定，届时本文再补对应的安装方式。

[构建工作流](../.github/workflows/build.yml) 在推送、PR 或手动触发时构建 sdist 与 wheel，
不包含上传步骤、不读取 PyPI secret，也不监听 release 事件。当前构建使用 Python 3.11，
并非对所有受支持 Python 版本逐一验证。
以后若决定发布，需先确认 PyPI 项目名及其归属、配置对应项目的 token secret，并明确发布触发方式；
当前工作流不会代替这些决策自动发包。

## 验证安装

```bash
.venv/Scripts/python.exe -c "import anybooru; print(anybooru.__version__)"
```

当前源码的版本号是 `0.1.0.dev1`，打印出这一行即安装成功。再用构造器确认包内配置能被解析
（这段不发网络请求）：

```python
from anybooru import Danbooru

with Danbooru('danbooru') as client:      # 'danbooru' 是包内配置 sites 段的键名
    print(client.site_url)                # https://danbooru.donmai.us
    print(client.timeout)                 # 30，来自 request.timeout
```

## 配置文件放在哪

安装包里自带一份 `anybooru/anybooru.json`，`Danbooru('danbooru')` 这类调用默认读它，**不需要**把它复制
到工作目录。要改站点或凭据时，可以拿包内那份当模板另存一份（`anybooru.DEFAULT_CONFIG_FILE` 就是它的
绝对路径）：

```python
import shutil
from anybooru import DEFAULT_CONFIG_FILE, Danbooru

print(DEFAULT_CONFIG_FILE)                             # 包内默认配置的绝对路径

shutil.copy(DEFAULT_CONFIG_FILE, 'my-anybooru.json')   # 复制一份到当前目录，改这个副本

with Danbooru('danbooru', config_file='my-anybooru.json') as client:
    print(client.site_url)                             # https://danbooru.donmai.us
```

库不会搜索当前工作目录、用户目录或其他隐藏位置，只读 `config_file` 指到的那份（默认即包内那份）；
`my-anybooru.json` 不存在时构造函数立刻抛 `FileNotFoundError`，不会退回包内那份。
逐键说明见 [configuration.md](configuration.md)。

## 目录结构

| 路径 | 说明 |
| :--- | :--- |
| `anybooru/` | 包源码：`danbooru` / `moebooru` / `serika` / `e621` / `zerochan` / `gelbooru` / `gelbooru02` / `shuushuu` / `sakuria` / `anime_pictures` / `cosine` / `artstation` 各有客户端模块与 `api_<family>.py` 方法模块，`anybooru.py` 为共享核心 |
| `anybooru/resources.py` | 包内默认配置的路径 `DEFAULT_CONFIG_FILE`，以及把 Python 参数编成 Rails 查询串的 `encode_params` |
| `anybooru/exceptions.py` | 三个公开异常 `AnybooruError` / `AnybooruHTTPError` / `AnybooruAPIError`，见 [errors.md](errors.md) |
| `anybooru/anybooru.json` | 随包默认配置：`request`（超时、代理、User-Agent）、`sites`（16 个站点条目）、`examples`、`smoke`、`verification` |
| `docs/` | 中文 Markdown 文档（本文件所在处） |
| `examples/` | 各家族的匿名只读示例脚本，参数取自配置的 `examples` 段 |
| 上游引擎仓库 | 可选的只读参考，不属于发布包；版本与源码入口见各家族的契约审计附注 |

## 上游引擎源码（可选）

要核对某个端点的路由与参数，可以本地克隆上游引擎仓库作为只读参考：

```bash
git clone https://github.com/danbooru/danbooru.git
git clone https://github.com/moebooru/moebooru.git
git clone https://github.com/e621ng/e621ng.git
```

三个 Rails 引擎的路径规则以各自的 `config/routes.rb` 为准；参数、权限与响应形状看对应仓库的
`app/controllers/`（Danbooru 另有 `app/policies/` 与 `app/logical/`，e621ng 的帖子序列化在
`app/blueprints/`）。Serika 是自研 Next.js 站点，路由分散在 `app/api/v1/**/route.ts` 与 `app/api/**/route.ts`，
入口见 [Serika 契约审计附注](serika-contract-notes.md)。所有上游参考都不随本包发布，也不参与提交。

Zerochan、Gelbooru、Gelbooru02（TBIB）、Shuushuu、Sakuria、Anime-Pictures、Cosine 与 ArtStation 都没有可供核对的
本地上游**服务端**源码：Zerochan 的依据是
官方 API 页面快照与实际响应；Gelbooru 是官方 wiki/帮助页、站点脚本与实际响应；Gelbooru02 是该站
`index.php?page=help&topic=dapi` 帮助页、首页的 `Running Gelbooru 0.2` 与实际响应，不能由帮助页或前端字段
推出未观察到的结构；Shuushuu 使用站点自带的 OpenAPI 与匿名响应。Sakuria 还要再弱一档：连官方页面与
OpenAPI 都没有，依据只是匿名响应观察加随后的一次有界实测（每个请求只发一次），样本之外的候选字段
不得当成返回值承诺。Anime-Pictures 与 Sakuria 同档：官方 API 手册页存在但整站被 Cloudflare 质询、
命令行读不到，也没有 OpenAPI 与服务端源码，依据只是匿名只读响应加候选输入资料
（输入引用的外部客户端源码链接本轮没有独立读过）。Cosine 的站点前端代码在公开仓库里，本轮只按需只读了个别
文件当线索（不 clone、不写行号），公开结论以匿名只读响应与 [Cosine 契约附注](cosine-contract-notes.md) 为准。
ArtStation 本轮未取得官方 API 文档页或 OpenAPI，依据同样只有匿名只读响应；本类只覆盖公开作品集路由
与一个 RSS 订阅源，成功字段按探测响应写，样本之外的取值不得当成返回值承诺。
八者都不从其他引擎推断。
出处与未实测边界见 [Zerochan 契约审计附注](zerochan-contract-notes.md)、
[Gelbooru 契约审计附注](gelbooru-contract-notes.md)、
[Gelbooru02 契约审计附注](gelbooru02-contract-notes.md)、
[Shuushuu 契约审计附注](shuushuu-contract-notes.md)、
[Sakuria 契约审计附注](sakuria-contract-notes.md)、
[Anime-Pictures 契约审计附注](anime-pictures-contract-notes.md)、
[Cosine 契约审计附注](cosine-contract-notes.md) 与
[ArtStation 契约审计附注](artstation-contract-notes.md)。
