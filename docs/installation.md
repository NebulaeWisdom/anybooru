# 安装

## 运行要求

| 项目 | 要求 |
| :--- | :--- |
| Python | >= 3.6 |
| 运行时依赖 | [requests](https://requests.readthedocs.io/) >= 2.26（安装时自动拉取） |
| 标准库依赖 | `json`、`os`（读取默认配置文件），无其他第三方依赖 |

本库不依赖环境变量，也不会去当前工作目录或用户目录搜索配置文件；所有可调参数都在配置文件里显式
声明，默认读随包安装的 `pybooru/pybooru.json`，见 [configuration.md](configuration.md)。

## 从源码安装（当前开发版）

```bash
git clone https://github.com/NebulaeWisdom/pybooru.git
cd pybooru

# 创建并激活虚拟环境
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .        # Windows
.venv/bin/python -m pip install -e .                # Linux / macOS
```

`-e`（editable）安装后，`import pybooru` 直接指向仓库里的源码，改动立即生效。

### 需要代理时

pip 支持显式指定代理，请不要用环境变量注入：

```bash
.venv/Scripts/python.exe -m pip install -e . --proxy http://proxy.example:8080
```

运行期的代理写在配置文件的 `request.proxies` 中。

## 从 PyPI 安装

```bash
pip install --user Pybooru
```

> 本次重构尚未发布；普通 PyPI 安装不保证包含新契约。本文方法针对包含本轮提交的源码开发版（**5.0.0.dev1**）。
>
> 任何安装方式都自带可用配置，见下节。

## 验证安装

```bash
.venv/Scripts/python.exe -c "import pybooru; print(pybooru.__version__)"
```

输出当前源码版本号即安装成功。

## 配置文件放在哪

安装包里自带一份 `pybooru/pybooru.json`，`Danbooru('danbooru')` 这类调用默认读它，**不需要**把它复制
到工作目录。它的绝对路径是 `pybooru.DEFAULT_CONFIG_FILE`，可直接当模板来源：

```bash
# 源码安装：复制仓库里那份
cp pybooru/pybooru.json /path/to/your-project/sites.json
```

```python
import shutil, pybooru

shutil.copy(pybooru.DEFAULT_CONFIG_FILE, 'config/sites.json')  # pip 安装后用这个
client = Danbooru('danbooru', config_file='config/sites.json')  # 再显式指向自己那份
```

库不会搜索当前工作目录、用户目录或其他隐藏位置，只读 `config_file` 指到的那份（默认即包内那份）。
完整内容与逐键说明见 [configuration.md](configuration.md)。文件缺失时构造函数直接抛
`FileNotFoundError`。

## 目录结构

| 路径 | 说明 |
| :--- | :--- |
| `pybooru/` | 包源码：`danbooru` / `moebooru` / `serika` / `e621` 各有客户端模块与 `api_<family>.py` 方法模块，`pybooru.py` 为共享核心 |
| `pybooru/pybooru.json` | 随包默认配置：站点、凭据、代理、超时、示例参数 |
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
