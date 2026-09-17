# 安装

## 运行要求

| 项目 | 要求 |
| :--- | :--- |
| Python | >= 3.6 |
| 运行时依赖 | [requests](https://requests.readthedocs.io/) >= 2.26（安装时自动拉取） |
| 标准库依赖 | `json`、`os`（读取默认配置文件），无其他第三方依赖 |

本库不依赖环境变量，也不会去当前工作目录或用户目录搜索配置文件；所有可调参数都在配置文件里显式
声明，默认读随包安装的 `anybooru/anybooru.json`，见 [configuration.md](configuration.md)。

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

输出当前源码版本号即安装成功。

## 配置文件放在哪

安装包里自带一份 `anybooru/anybooru.json`，`Danbooru('danbooru')` 这类调用默认读它，**不需要**把它复制
到工作目录。它的绝对路径是 `anybooru.DEFAULT_CONFIG_FILE`，可直接当模板来源：

```bash
# 源码安装：复制仓库里那份
cp anybooru/anybooru.json /path/to/your-project/sites.json
```

```python
import shutil, anybooru

shutil.copy(anybooru.DEFAULT_CONFIG_FILE, 'config/sites.json')  # 用包内默认配置当模板
client = Danbooru('danbooru', config_file='config/sites.json')  # 再显式指向自己那份
```

库不会搜索当前工作目录、用户目录或其他隐藏位置，只读 `config_file` 指到的那份（默认即包内那份）。
完整内容与逐键说明见 [configuration.md](configuration.md)。文件缺失时构造函数直接抛
`FileNotFoundError`。

## 目录结构

| 路径 | 说明 |
| :--- | :--- |
| `anybooru/` | 包源码：`danbooru` / `moebooru` / `serika` / `e621` 各有客户端模块与 `api_<family>.py` 方法模块，`anybooru.py` 为共享核心 |
| `anybooru/anybooru.json` | 随包默认配置：站点、凭据、代理、超时、示例参数 |
| `docs/` | 中文 Markdown 文档（本文件所在处） |
| `examples/` | 可运行示例脚本 |
| 上游引擎仓库 | 可选的只读契约参考，不属于发布包；版本与源码入口见各家族契约审计附注 |

## 上游引擎源码（可选）

要核对某个端点的路由与参数，可以本地克隆上游引擎仓库作为只读参考：

```bash
git clone https://github.com/danbooru/danbooru.git
git clone https://github.com/moebooru/moebooru.git
git clone https://github.com/e621ng/e621ng.git
```

Rails 三家的路由权威来源是各上游的 `config/routes.rb`，参数与权限见对应 `app/controllers/`
及模型；e621ng 的帖子序列化位于 `app/blueprints/`。Serika 的独立路由结构与源码入口见
[Serika 契约审计附注](serika-contract-notes.md)。所有上游参考都不随本包发布，也不参与提交。
