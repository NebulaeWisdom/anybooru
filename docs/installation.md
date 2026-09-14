# 安装

## 运行要求

| 项目 | 要求 |
| :--- | :--- |
| Python | >= 3.6 |
| 运行时依赖 | [requests](https://requests.readthedocs.io/) >= 2.26（安装时自动拉取） |
| 标准库依赖 | `json`（读取根配置文件），无其他第三方依赖 |

本库不依赖环境变量，也不读取任何隐藏位置的配置文件；所有可调参数都在项目根目录的
`pybooru.json` 里显式声明，见 [configuration.md](configuration.md)。

## 从源码安装（当前开发版）

```bash
git clone https://github.com/LuqueDaniel/pybooru.git
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
.venv/Scripts/python.exe -m pip install -e . --proxy http://proxy-host:port
```

运行期的代理写在根配置文件的 `request.proxies` 中。

## 从 PyPI 安装

```bash
pip install --user Pybooru
```

> 本次重构尚未发布；普通 PyPI 安装不保证包含新契约。本文方法针对包含本轮提交的源码开发版（**5.0.0.dev1**）。
>
> 无论哪种安装方式，都要自己准备配置文件，见下节。

## 验证安装

```bash
.venv/Scripts/python.exe -c "import pybooru; print(pybooru.__version__)"
```

输出当前源码版本号即安装成功。

## 配置文件放在哪

安装不会自动创建配置文件。Pybooru 只读取**显式给出**的那一份（默认是当前工作目录的
`pybooru.json`），不会搜索 site-packages、包目录或用户目录。

```bash
# 把根样例复制到你的应用工作目录
cp pybooru.json /path/to/your-project/pybooru.json
```

或者不改工作目录，用 `config_file` 指向它：

```python
client = Danbooru('danbooru', config_file='/path/to/your-project/pybooru.json')
```

sdist 中带有一份完整的根样例 `pybooru.json`；完整内容与逐键说明见
[configuration.md](configuration.md)。缺文件时构造函数直接抛 `FileNotFoundError`。

## 目录结构

| 路径 | 说明 |
| :--- | :--- |
| `pybooru/` | 包源码（`danbooru.py` / `api_danbooru.py` 为 Danbooru 面，`moebooru.py` / `api_moebooru.py` 为 Moebooru 面，`pybooru.py` 为共享核心） |
| `pybooru.json` | 根配置文件：站点、凭据、代理、超时、示例参数 |
| `docs/` | 中文 Markdown 文档（本文件所在处） |
| `examples/` | 可运行示例脚本 |
| `danbooru/`、`moebooru/` | 上游引擎源码，只读参考，不属于发布包 |

## 上游引擎源码（可选）

要核对某个端点的路由与参数，可以本地克隆上游引擎仓库作为只读参考：

```bash
git clone https://github.com/danbooru/danbooru.git
git clone https://github.com/moebooru/moebooru.git
```

路由权威来源是 `danbooru/config/routes.rb` 与 `moebooru/config/routes.rb`，参数与权限见对应
`app/controllers/` 下的控制器。这两个目录不随本包发布，也不参与提交。
