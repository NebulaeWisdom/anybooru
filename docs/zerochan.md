# Zerochan 客户端用法

`Zerochan` 是继 `Danbooru` / `Moebooru` / `Serika` / `E621` 之后的第五个客户端，访问 Zerochan
（`https://www.zerochan.net`）的**只读 JSON API**。本次没有可供核对的 Zerochan 引擎源码，
因此只依据站点自己的 [API 页面](https://www.zerochan.net/api)、
[2024 年快照](https://web.archive.org/web/2024/https://www.zerochan.net/api)与真实响应；
两者的逐条出处、排除项与未实测边界记在[契约审计附注](zerochan-contract-notes.md)。
本页只讲“这个类怎么用”；两个方法的签名、路由与返回形态见[方法参考](zerochan-api.md)，
按目的找入口见[能力入口](zerochan-capabilities.md)。

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:                                  # 读包内默认 anybooru.json
    example = client.config['examples']['zerochan']
    entries = client.entry_list(**example['entry_query'])             # {"p": 1, "l": 2, "s": "id"}
    print(entries[0]['id'], entries[0]['tag'])
    entry = client.entry_show(example['entry_id'])                    # 3793685
    print(entry['primary'], entry['width'], entry['height'])
```

条数、URL 与状态码以 [verification.md](verification.md#zerochan匿名只读实测2026-09-18) 的 Zerochan 小节为准；
本页只保留结论性事实：不传 `l` 时**观察到**服务端返回 48 条（`/?json=`），页面并没有写明这个默认值，
客户端也不设默认、不推断条数。

## 构造

```python
Zerochan(site_name=None, site_url=None, proxies=None,
         *, config_file=None, timeout=None, user_agent=None)
```

| 参数 | 说明 |
| :--- | :--- |
| `site_name` | 配置 `sites` 段的键名；包内默认配置的 `sites.zerochan` 只有 `url` 一项 |
| `site_url` | 显式覆盖地址；只给 `site_url` 也可以构造，**库没有地址后备**，两者都不给会直接报错 |
| `proxies` / `timeout` / `user_agent` | 显式覆盖配置 `request` 段的同名值；会话 `trust_env=False`，不读环境变量 |
| `config_file` | 配置文件路径；默认 `None`，即读随包安装的 `anybooru/anybooru.json`（`anybooru.DEFAULT_CONFIG_FILE`），显式传路径才读别的文件，指到的文件不存在会抛 `FileNotFoundError` |

**没有 `username` / `api_key` / `password` 参数**：API 页面没有描述登录认证步骤；客户端不发
认证头，也不提供凭据配置。构造时给共享传输传的是空用户名，因此站点条目只需要一个 `url`。
配置总览与自定义站点写法见 [configuration.md](configuration.md)；解析后的配置挂在公开属性 `config` 上
（`config['sites']['zerochan']['url']`、`config['examples']['zerochan']`、`config['request']['timeout']`）。
示例脚本从 `config['examples']['zerochan']` 取站点、查询、条目 ID 与调用间隔，没有硬编码参数。

用完记得 `client.close()`，或者像上面那样用 `with` 语句块。

## 认证与 User-Agent

* **不实现认证**：本库既不发送凭据，也不做登录、cookie 会话或 key 管理；
  已有匿名只读成功响应，页面未定义凭据类参数。
* **User-Agent 是页面要求的身份标识**。请求头须带上项目名与使用者自己的 Zerochan 用户名，
  并且说明不带这个自定义头请求**仍可能成功**，但匿名项目**可能被封**：
  “the name of your project and your Zerochan username is required … your project may be banned
  for being anonymous.”。包内默认是 `Anybooru/0.1.0.dev1`，它只是库的默认值，**不满足页面的要求**。
* 请把 `request.user_agent` 配置项（或构造参数 `user_agent=`）改成
  “项目名 + 你的 Zerochan 用户名”的形式，例如 `<项目名> - <你的 Zerochan 用户名>`。
  这不是登录认证，不代表获取账号权限，也不能保证请求一定被接受。
* 本库不校验或补齐用户名，调用者负责提供自己的标识。

## 通用请求入口

```python
request(path, *, params=None, envelope=None)
```

这是两个原生方法的底座，也是拿上游原始信封（不拆 `items`）或访问原生方法之外的相对路径时的入口。
与其它家族不同，它**没有 `method` / `data` / `files`**：Zerochan 公开 API 目前只有 `GET`，
所以这个入口天然只发 `GET`，也不接受请求体或文件。

```python
from anybooru import Zerochan

with Zerochan('zerochan') as client:
    example = client.config['examples']['zerochan']
    # 原生方法用的同一条路由，通用入口不拆信封，返回上游原样的 {"items": [...]}
    body = client.request('', params=example['entry_query'])
    print(list(body), body['items'][0]['id'], client.last_call['status_code'])
```

* `path` 是**相对路径，开头的 `/` 会去掉**：空字符串或 `/` 是全部条目，
  一个标签名（或多个标签名用逗号连起来）是标签过滤，一个条目 id 是详情。
  路径按原样拼接：库**既不补 `.json` 后缀，也不会替调用者去掉后缀**——JSON 由查询串选择（见下一条）；
  动态路径段由原生方法转义，裸路径要调用者自己保证已经是合法的 URL 段。
* **`json` 查询值由客户端补上**，调用者永远不写它：每次请求都会带上 `json=`（空值）。
  API 页面写的是把 `json` 追加到“正常 URL”上，例如 `/?p=1&json`；实际观察到的响应里
  `json` 与 `json=` 两种写法都能拿到 `application/json`（见 [verification.md](verification.md)）。
  已观察到 `/3793685` 返回 HTML，而 `/3793685?json` 返回 JSON；不要把正常页面当 API。
* `params` 放查询参数（页面定义了 `p` / `l` / `s` / `t` / `d` / `c`），不做白名单筛选，
  `None` 不发送；**没有客户端默认值**。
* `envelope` 是显式契约，只接受一个键名；列表端点用 `items` 拆封，详情端点没有信封所以不传。
  键不存在时直接 `KeyError`，不会去找别的形状或后备字段。
* 不自动重试、不自动翻页、不解析 HTML、不做引擎识别；网络错误、限流、5xx 全抛给调用者。
* 文档里的 60 请求/分钟限流**只在文档里说明，不在客户端强制执行**：翻页要由调用者自己安排节奏
  （`examples.zerochan.pause_seconds` 就是给示例脚本用的间隔，不是库的限速）。

## 参数编码

查询参数走与其它家族相同的编码器：布尔落成小写 `true` / `false`，`None` 不发送，
嵌套 dict 变 `a[b]`、列表变重复键 `a[]`。Zerochan 的过滤参数都是标量，通常直接透传：

```python
with Zerochan('zerochan') as client:
    example = client.config['examples']['zerochan']
    entries = client.entry_list(**example['entry_query'])              # {"p": 1, "l": 2, "s": "id"}
    second_page = client.entry_list(
        **client.config['verification']['zerochan']['optional_queries'][0]['params'])  # {"p": 2, "l": 2, "s": "id"}
```

**标签不是搜索表达式，而是字面标签名**，只出现在路径里：`/Genshin+Impact?json` 里的 `+` 就是空格，
`/Lumine,Flower?json` 里逗号是分隔符。客户端的规则是：

| 传入 | 发送的路径 | 说明 |
| :--- | :--- | :--- |
| `tags=None` | `/?…&json=` | 不按标签过滤，列全部条目 |
| `tags='Genshin Impact'` | `/Genshin+Impact?…` | **一个**标签；名称整体按路径段转义，空格变 `+` |
| `tags=['Lumine', 'Flower']` | `/Lumine,Flower?…` | 两个标签；每个名字**各自**转义后再用逗号连接 |
| `tags=('Lumine', 'Flower')` | 同上 | 元组与列表等价 |
| `tags='Lumine,Flower'` | `/Lumine%2CFlower?…` | 字符串**不按逗号拆**，这是一个名字里含逗号的标签 |

* 每个标签名都用 `quote_plus(name, safe='')` 整体转义，所以名字里的 `/`、`&`、`#`、`%`、`+`、`,` 都进 `%XX`，
  空格变 `+`。**这只保证编码结果**：名字带特殊字符时服务端怎么把编码后的路径段匹配回标签没有实测，
  已有记录里的单/多/strict 查询用的是普通名字（`Genshin Impact`、`Lumine`、`Flower`）。
* **大小写原样保留**，不做小写化，也不替换空格与下划线；标签名怎么写就怎么发。
* 不解析或生成图站搜索语法。API 页面没有定义 `order:`、`rating:`、`score:` 或通配符语法，
  不要套用别的家族的搜索表达式。原生方法通过 `tags` 参数组装路径，不发送 `tags` 查询键。
* 客户端不预判非法路径或参数的结果；非 2xx 抛 HTTP 异常，成功响应走 JSON 解析。

## 返回值与信封

| 调用 | 返回 |
| :--- | :--- |
| `entry_list(...)` | 条目数组（上游 `{"items": [...]}` 的 `items`） |
| `entry_show(entry_id)` | 详情对象本身（该端点没有信封，原样返回） |
| `request(path)` 不传 `envelope` | 上游原始 JSON：列表是 `{"items": [...]}`，详情是裸对象 |
| 空成功正文，且未指定 `envelope` | `None`；这个分支未向 Zerochan 实测，`entry_list` 仍要求有 `items` 的对象，不把空正文当空列表 |

两个返回形状的字段（均为**已观察到的响应字段**）：

* 列表条目 8 键：`id`、`width`、`height`、`md5`、`thumbnail`、`source`、`tag`、`tags`；
  其中 `tag` 是 primary 标签名的字符串，`tags` 是标签名字符串数组。
* 详情对象 12 键：`id`、`small`、`medium`、`large`、`full`、`width`、`height`、`size`、`hash`、
  `source`、`primary`、`tags`；四种尺寸是不同大小的图片 URL，`primary` 是 primary 标签名字符串。
* `md5`（列表）与 `hash`（详情）都是服务端**返回的字段**，库只把它们当普通数据，不做校验、比对或去重。

`last_call` 记录每次请求的实际情况：`API`（相对路径，根路径调用时是空字符串）、
`url`（含查询串的最终地址）、`status_code`、`status`、`headers`。它可以直接核对“标签到底发成了什么样”：

```python
with Zerochan('zerochan') as client:
    example = client.config['examples']['zerochan']
    client.entry_list(**example['tag_query'])
    print(client.last_call['status_code'], client.last_call['url'])
# 路径里的空格被编码成 '+'，json 由客户端补在查询串里
```

## 常见坑

1. **JSON 与正常页面的区别只在查询串**：`/<id>` 是给人看的 HTML 页面，`/<id>?json`（本库发的
   `/<id>?json=`）才是 JSON；不带 `json` 的地址不会被客户端救回，因为它根本不生成那种请求。
2. **字符串不会按空格或逗号拆**：`entry_list(tags='Genshin Impact')` 编码为 `Genshin+Impact`，
   `entry_list(tags='Lumine,Flower')` 编码为 `Lumine%2CFlower`。多标签请给列表或元组；
   名字含逗号时服务端如何匹配未实测，不能推断一定是空结果或交集。
3. **meta 标签端点不可用**：API 页面在单标签与 strict 两条端点上都写了
   “This endpoint is not available for meta tags.”；这是服务端限制，不是客户端漏做，页面也没有说明
   哪些标签算 meta 标签。
4. **列表没有分页元数据**：已观察到的列表信封只有 `items` 一个键，没有 `total` / `page` / `pages`
   这类字段。要翻页只能自己传 `p` 与 `l`，并记住本次返回了多少条（`len(entries)`）；
   库不推断是否还有下一页。
5. **`l` 的默认值没有页面依据**：页面只写了 `l` 的范围是 1–250 与“配合 `p` 翻页”，没有写不传时的默认页大小；
   库不设默认、不钳位、不补值。本次观察到不传 `l` 时返回 48 条，这是当时的服务端行为，不是承诺的默认值；
   需要固定条数就显式给 `l`。
6. **`s=fav` 的人气窗口由 `t` 决定，而 `t` 没有客户端默认值**：页面写 `t` 取 `0` / `1` / `2`，
   分别对应全部时间、最近 7000 条、最近 15000 条，并注明该参数行为**可能即将调整**；
   不传 `t` 时由服务端决定，库不替调用者补 `0`。**`t=0` 当前返回 `500`**：本次记录里
   `s=fav&t=0` 的正文是**无效 JSON**（`"items": [` 打开数组后直接以 `}` 结束），
   由 `AnybooruHTTPError` 原样保留，库不重试、不改写；`t=1` / `t=2` 当时正常返回 `200`。
   因此 `t=0` 的“成功路径”属未实测，不能写成“只是没测过”。
7. **`/3793685` 这类数字路径就是详情**：一个纯数字段会被服务端当成条目 id；本库按这个路径形态拼
   （`entry_show`），标签名与 id 是否会互相回退没有页面依据，也没有响应记录。
8. **`d` 与 `c` 是枚举字符串**：`d` 取 `large` / `huge` / `landscape` / `portrait` / `square`，
   `c` 是颜色名（页面写 `red|blue|green|...`）；非法值由服务端处理，客户端不校验。
   **`square` 不是精确的正方形**：本次记录里 `d=square` 的首项是 1006×966，第二项才是 1024×1024，
   所以只能把它理解成服务端的归类，不能断言宽高必须相等；`large` 与 `huge` 那次的返回相同，
   页面也没有给阈值，两者的边界未知。
9. **`xml` 不在本库内**：页面写的是 “appending the `json` or `xml` query string”，但本客户端只做 JSON；
   需要 XML 只能自己用通用 HTTP 取，别指望这里的参数能切换格式。
10. **限流 60 请求/分钟不是摆设**：页面写明长期超限可能导致封禁，而客户端不做任何节流；
    批量跑请自己按配置的间隔逐条发。
11. **User-Agent 默认值不符合页面要求**：`Anybooru/0.1.0.dev1` 有项目标识，但没有你的 Zerochan 用户名，
    匿名请求仍可能成功，但页面提示匿名项目可能被封；要合规就改配置里的 `request.user_agent`。

## 可运行示例

两个脚本都支持 `--config` 与 `--site`，`--config` 省略即读包内默认配置，站点名默认取
`examples.zerochan.site`；查询、条目 ID 与调用间隔全部来自配置文件，脚本只调用匿名只读路径。

```bash
.venv/Scripts/python.exe examples/zerochan/list_entries.py
.venv/Scripts/python.exe examples/zerochan/filter_entries.py

# 换成自己的配置文件或站点键
.venv/Scripts/python.exe examples/zerochan/list_entries.py --config <配置文件>
```

* `list_entries.py`：用 `examples.zerochan.entry_query`（`p=1`、`l=2`、`s=id`）调 `entry_list`，
  打印状态码、最终 URL、条数与前两条的 `id` / `tag` / 宽高；间隔 `pause_seconds` 后再用
  `entry_id` 调 `entry_show`，打印该条目的 `id` / `primary` / 宽高 / `size` / `full` / `source`。
* `filter_entries.py`：依次用 `tag_query`（单标签）、`multi_tag_query`（两个标签）、
  `strict_query`（单标签 + strict）调 `entry_list`，每条之间按 `pause_seconds` 暂停，
  打印每次的状态码、最终 URL、条数与 `id` / `tag`。

示例脚本会让 User-Agent 保持配置里的值；要让请求符合页面的要求，先按上一节把
`request.user_agent` 改成你自己的项目名与 Zerochan 用户名。

两条命令均已实际运行：**退出码 `0`、stderr 为空、合计 5 次 `HTTP 200`**（`list_entries.py` 2 次，
`filter_entries.py` 3 次；脚本自己打印状态码）。逐条命令、URL 与输出摘要见
[verification.md](verification.md#zerochan匿名只读实测2026-09-18)。

## 边界与未实测

* 客户端只封 **2 个原生方法**（`entry_list` / `entry_show`）与通用 `request()`；其它路径没有方法。
* 已有记录合计 **21 次请求：20×200 + 1×500**——契约复核 16 次（15×200 + 1×500），
  两个示例脚本 5 次（5×200）。覆盖根列表（默认 48 条）、配置里的示例列表、单标签、多标签、strict、
  单条目详情、`p=2`、`t=1` / `t=2`、`d` 的五个值与 `c=red`；唯一的 `500` 是 `s=fav&t=0`，
  正文不是合法 JSON。逐条 URL、状态码与条数见
  [verification.md](verification.md#zerochan匿名只读实测2026-09-18)。
* **未实测**：`t=0` 的成功路径（本次 `500`）、加入自己用户名后的合规 UA、特殊字符标签、
  `p` / `l` 的越界与非法值、上述之外的参数组合、超限流后的响应、网络错误与别的 5xx，
  以及 XML 格式。页面未提供完整行为细节，本轮也没有取得这些分支的响应。
* **不可用**：单标签与 strict 端点的 meta 标签过滤（服务端声明不可用）、写操作（API 只读）、
  XML 输出（本库刻意不做）。可用性判断的依据见[契约审计附注](zerochan-contract-notes.md)。
* 本库不做引擎识别，也不会在失败后换客户端重试；选 `Zerochan` 由调用者决定，判断方法见
  [configuration.md](configuration.md)。

继续阅读：[方法参考](zerochan-api.md) · [能力入口](zerochan-capabilities.md) ·
[契约审计附注](zerochan-contract-notes.md) · [错误处理](errors.md) · [配置](configuration.md)。
