# Zerochan 契约审计附注

面向维护者与契约核对者。使用者页面（[客户端用法](zerochan.md)、[方法参考](zerochan-api.md)、
[能力入口](zerochan-capabilities.md)）只保留可操作的事实；本文记页面原文出处、证据等级、
排除项、客户端实现契约与逐条状态。

## 契约来源与证据立场

* **Zerochan 没有公开引擎源码**，也没有可对照的上游仓库；本家族**不引用任何上游文件或行号**。
  契约只有两个来源，按权威顺序排列：
  1. **站点自己的 API 页面原文**：`https://www.zerochan.net/api`
     （归档快照 <https://web.archive.org/web/2024/https://www.zerochan.net/api>）。页面没有版本号，
     快照取自 2024 年；本文所有带引号的英文都是该快照正文的**逐字片段**。
  2. **真实响应**：已观察到的 JSON 结构（字段名、类型、信封）。它与页面原文一起决定实现，
     但不能替代页面——页面没写的东西一律记为“已观察”，不写成“服务端承诺”。
  `Checking browser...`），所以引用的是归档快照；这只看文档页面，**不代表 JSON API 端点不可用**
  （端点连通的记录见 [verification.md](verification.md)）。这类边缘访问策略不属于 Zerochan 的 API 契约。
* 客户端侧依据是 `anybooru/zerochan.py`（客户端与 `request()`）与 `anybooru/api_zerochan.py`
  （`ZerochanApi_Mixin`，2 个原生方法）。
* **页面本身不描述响应结构**（没有字段表、没有信封说明、没有错误形状、没有默认页大小）。
  所以本库的字段清单与信封拆解全部基于**已观察到的响应**；页面对应的原文只覆盖 URL 形态、
  查询参数、UA 要求、限流与只读性质。凡是“页面没写、只是观察到”的结论，本文都显式标注。
* 客户端只做页面允许的事：不加页面之外的端点、不实现页面之外的行为、不为页面未定义的默认值兜底。
  逐条落点见下一节。

## 页面原文与落点（逐条引用）

以下按快照正文逐条摘录；行内代码标记仅便于阅读。

| 页面原文（快照） | 落点 |
| :--- | :--- |
| “For the time being, Zerochan has a simple read-only API to programmatically request data from its data set.” | 只读定位：本库没有写方法，`request()` 也不接受 `method` / `data` / `files` |
| “Since the API is read-only at this time, all requests are done using `GET` .” | `request()` 恒发 `GET`；README 与配置说明按只读客户端描述 |
| “To access the API, a user-agent header containing the name of your project and your Zerochan username is required. For example: "My AI learning app - MyUsername". The request may still be completed successfully without this custom header, but your project may be banned for being anonymous.” | User-Agent 要求与匿名风险：默认 `Anybooru/0.1.0.dev1` **不满足**，需使用者改配置（不是认证） |
| “There is a rate limit of 60 requests per minute. Chronically exceeding this limit may result in a ban.” | 限流只在文档说明；客户端不节流、不重试；示例的 `pause_seconds` 是脚本级间隔 |
| “Most endpoints can be accessed by appending the `json` or `xml` query string to the 'normal' url.” | JSON 由查询串选择；本库补 `json=`；`xml` 明确排除；“Most”说明并非所有地址都有 JSON 形式 |
| “For example: `/?p=1&json`”——“End point for retrieving all entries. You may use the following query string parameters for filtering. All of these are optional:” | 根路径 `entry_list(tags=None)`；参数全部可选且原样透传 |
| “`p` (int) Page. Use in combination with limit to paginate results.” | `p` 透传；库不设页码默认 |
| “`l` (1-250) Limit, or entries per page. Use in combination with page to paginate results.” | `l` 透传；**页面没写不传时的页大小**，库不猜、不钳位 |
| “`s` (id\|fav) Sorting order. Sort by either recency ( id ) or popularity ( fav ).” | `s` 透传；recency / popularity 两种排序 |
| “`t` (0\|1\|2) Time used for sorting by popularity. 0 indicates all time, 1 indicates the last 7000 entries, 2 indicates the last 15000 entries. This parameters' behavior might be changed soon.” | `t` 透传；页面自带“可能调整”的免责，文档不把它当稳定语义 |
| “`d` (large\|huge\|landscape\|portrait\|square) Picture dimensions, you may use this to filter by certain picture dimensions .” | `d` 透传；枚举值不校验 |
| “`c` (red\|blue\|green\|...) Color. Filter entries by certain overall color.” | `c` 透传；页面用省略号，词表不完整，库不补全 |
| “`/Genshin+Impact?json`”——“Endpoint for retrieving all entries, filtered by one single tag. This endpoint is not available for meta tags.” | 单标签 `entry_list(tags=<str>)`；示例里的 `+` 就是空格；meta 标签**服务端不可用** |
| “`/Genshin+Impact?json&strict`”——“Endpoint for retrieving entries in a tag using strict mode, that is, entries where the primary tag is the tag being matched. This endpoint is not available for meta tags.” | `strict=True` 发 `strict=` 存在标记；strict 只记在单标签端点上；meta 标签同样不可用 |
| “`/Lumine,Flower?json`”——“Filter by multiple tags.” | 多标签 `entry_list(tags=[...])`；逗号是分隔符，名字各自转义 |
| “`/3793685?json`”——“Detailed information about a single entry.” | `entry_show(entry_id)`；纯数字路径段是条目 id |

**页面没有提供的资料**：响应字段表、信封键名、错误状态码与正文、`l` 的默认值、
meta 标签的定义、`p` / `l` 越界后的行为、超限流后的响应、限流是否带响应头、各端点的内容范围。

## 路由清单与状态

`GET`，路径相对 `https://www.zerochan.net`；所有请求都带客户端补的 `json=`。
下表的“已记录”表示已有对应的响应事实，逐条 URL、状态码与响应摘要见
[verification.md](verification.md#zerochan匿名只读实测2026-09-18)；“页面已声明”只表示页面有原文，不等于跑过。

| # | 路径 | 客户端 | 页面依据 | 已有响应记录 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `/?json`（可带 `p` / `l` / `s` / `t` / `d` / `c`） | `entry_list()` / `request('')` | `/?p=1&json` 段 | 已记录：`200` 且 `Content-Type: application/json`；不传 `l` 时 `items` 有 48 条，`p=2&l=2` 也 `200` |
| 2 | `/<Tag>?json` | `entry_list(tags=<str>)` | `/<Tag>?json` 段 | 已记录：带 `l=2` 时 `200` 且 JSON；其它过滤组合未实测 |
| 3 | `/<Tag>?json&strict=` | `entry_list(tags=..., strict=True)` | `/<Tag>?json&strict` 段 | 已记录：`200` 且 JSON |
| 4 | `/<TagA>,<TagB>?json` | `entry_list(tags=<list/tuple>)` | `/Lumine,Flower?json` 段 | 已记录：`200` 且 JSON |
| 5 | `/<id>?json` | `entry_show(entry_id)` | `/3793685?json` 段 | 已记录：`200` 且 JSON |
| 6 | `/<id>`（不带 `json`） | 无（本库不生成） | “appending the json … to the 'normal' url” 的反面 | 已记录：同 id 的不带 `json` 地址返回 `200` **HTML** |
| 7 | `/?l=2&s=fav&t=0&json`（人气窗口 `t=0`） | `entry_list(l=2, s='fav', t=0)` | `t` 参数原文含 `0 indicates all time` | 已记录：`500`，正文不是合法 JSON（见下节） |

第 6 行是“JSON 与正常页面是两种输出”的直接证据：同一个 `<id>`，带 `json` 得 JSON、不带得 HTML。
第 7 行是**唯一**的错误记录，说明页面写了 `t` 可以取 `0`，但当前站点对 `t=0` 返回 `500`；
`t=1` 与 `t=2` 都在同一批记录里返回 `200`。这几行的“已记录”只覆盖当时那组参数，
换参数、换时间都不算已验证。

## 本次已记录调用（汇总）

* **契约复核 16 次：15×200 + 1×500**，时间为 2026-09-18（UTC），User-Agent 为配置默认的
  `Anybooru/0.1.0.dev1`。覆盖：`/?json=`（不传 `l`，48 条）、示例列表 `p=1&l=2&s=id`、
  单标签、多标签、strict、详情 `3793685`、`p=2&l=2&s=id`、`s=fav&t=1`、`s=fav&t=2`、
  `d` 的五个值、`c=red`；唯一的 `500` 来自 `s=fav&t=0`，正文不是合法 JSON，
  `AnybooruHTTPError` 原样保留、没有重试。
* **两个示例脚本 5 次：5×200**，退出码 `0`、stderr 为空（`list_entries.py` 2 次、
  `filter_entries.py` 3 次）。
* 合计 **21 次请求**。逐条 URL、状态码、条数与字段摘要见
  [verification.md](verification.md#zerochan匿名只读实测2026-09-18)；本文只保留结论与出处，不复制响应正文。

## 响应形状与已观察字段

**信封**：列表端点返回 `{"items": [...]}`，已观察到的顶层键**只有 `items`**，
没有 `total` / `page` / `pages` / `next` 这类分页元数据；`entry_list` 只拆 `items`。
详情端点返回裸对象，没有信封，所以 `entry_show` 不传 `envelope`。

| 端点 | 已观察到的字段 | 类型要点 |
| :--- | :--- | :--- |
| 列表条目（8 键） | `id`、`width`、`height`、`md5`、`thumbnail`、`source`、`tag`、`tags` | `id` / `width` / `height` 是数字；`md5`、`thumbnail`、`source`、`tag` 是字符串；`tags` 是字符串数组 |
| 详情对象（12 键） | `id`、`small`、`medium`、`large`、`full`、`width`、`height`、`size`、`hash`、`source`、`primary`、`tags` | `small` / `medium` / `large` / `full` 是不同尺寸的图片 URL；`size` 是数字（**单位未确认**）；`hash`、`source`、`primary` 是字符串；`tags` 是字符串数组 |

四个容易被当作同一件事的字段：

* **`md5`（列表）与 `hash`（详情）**：两条端点各自返回的字符串字段，观察到的值都是 32 位十六进制样式，
  但**库不比较、不校验、不互转**；它们只是响应数据，不是本库的 checksum 机制，也不能当作“同一个值”的保证。
* **`tag`（列表）与 `primary`（详情）**：都是 primary 标签名（字符串）。页面用 primary tag 描述 strict 语义，
  列表里对应的键名是 `tag`，键名不同、含义对应，文档如实分成两个字段。
* **`tags`（两条端点）**：标签名字符串数组，顺序与内容由服务端给出，库不平铺、不去重、不排序。
* **没有观察到** `tag_string`、`file_url`、`media_asset`、`rating`、`score`、`fav_count`、`created_at`
  这些别的家族的字段；按它们的名字取值会 `KeyError`。

**默认页大小**：页面只写 `l` 的范围是 1–250 与 “Use in combination with page to paginate results.”
（是建议组合，不是硬性要求），没有写不传 `l` 时的条数。已有的一次观察是不传 `l` 的 `/?json=` 返回
`items` 48 条；这是当时的服务端取值，**不是默认值保证**，客户端也不设默认、不钳位。
其它查询的组合、页大小与页面-条数对应关系仍以
[verification.md](verification.md#zerochan匿名只读实测2026-09-18) 的记录为准。

**尺寸过滤的观察**：`d=square` 的首项是 1006×966、第二项才是 1024×1024，所以不能把 `square`
解释成“宽高精确相等”；`d=large` 与 `d=huge` 那一批返回的首两项相同（3570×2008、3010×4858），
页面又没有给阈值，**两者边界未知**；`d=landscape` 的两项宽大于高、`d=portrait` 的两项高大于宽，
与名字相符，但样本只有各 2 条，不构成对全站的断言。

**标签的匹配**：客户端只保证把标签名编码成一个路径段（`quote_plus`，空格变 `+`）。
已有记录里的标签查询（单标签、多标签、strict）用的都是普通名字；名字里含 `/`、`,`、`&` 等字符时
**服务端如何把编码后的路径段匹配回标签没有实测**。`tags` 数组与 `tag` / `primary` 都是服务端给的
标签名原文（大小写原样），库不归一化。

## 客户端侧实现契约

`anybooru/zerochan.py` 与 `anybooru/api_zerochan.py` 只做页面允许的事：

* **路径组装**（`entry_list`）：
  * `tags=None` → 空路径，拼成 `https://www.zerochan.net/` 后再接查询串（根列表）；
  * `tags` 是 `str` → `quote_plus(tags, safe='')`，**整体**当作一个路径段（空格变 `+`）；
  * `tags` 是 `list` / `tuple` → 每个名字各自 `quote_plus(name, safe='')`，再用**字面逗号**连接；
  * 不 `str()` 强转标签名、不按空格或逗号拆分、不做小写化、不替换空格与下划线。
* **路径组装**（`entry_show`）：`str(entry_id)` 直接作为路径段，不做转义（id 应当是数字）。
* **JSON 选择**：`request()` 把调用者给的 `params` 复制一份并**强制**写入 `json=""`，
  因此查询串里出现的是 `json=`（空值），不是裸 `json`；调用者传的 `json` 会被覆盖。
  路径**不自动添加 `.json` 后缀**，通用入口也不校验后缀：调用者给什么就发什么，库不追加也不剥离。
* **strict**：`entry_list(strict=True)` 往 `params` 里写 `strict=""`（存在标记），查询串里是 `strict=`；
  `strict=False` 时完全不发送该参数。
* **返回值**：`entry_list` 传 `envelope='items'`；`entry_show` 不传 `envelope`；
  通用 `request(path)` 默认返回原始 JSON，只有显式给 `envelope` 才按键拆，缺键直接 `KeyError`。
* **错误路径**：非 2xx 一律抛 `AnybooruHTTPError`，不重试、不改写。已有的一条记录是 `s=fav&t=0` 的
  `500`：正文按 JSON 解析失败，所以 `error.data` 是 `None`、原始正文留在 `error.body`；
  客户端没有为这种断开的 JSON 做任何修复或后备。
* **传输**：`request()` 签名没有 `method` / `data` / `files`，底层 `_request` 的默认方法就是 `GET`；
  不发认证头（构造时给共享传输的是空用户名，站点条目只需要 `url`）；
  `None` 参数不发送，其余参数原样编码（布尔落成小写 `true` / `false`，嵌套 dict 成 `a[b]`）。
* **`last_call`** 记录 `API`（相对路径，根路径调用时是空字符串）、`url`（含查询串的最终地址）、
  `status_code`、`status`、`headers`。

客户端**不做**的事：不设任何参数默认值、不钳位 `l` / `p`、不重试、不节流、不做超限退避、
不自动翻页、不合成分页元数据、不把 `md5` 与 `hash` 互转、不解析 HTML、不实现 `xml`、不识别引擎、
不在失败后改用别的地址。

## 排除项

* **`xml`**：页面写的是 “appending the `json` or `xml` query string”，本客户端**刻意只做 JSON**。
  需要 XML 的调用者要自己用通用 HTTP 客户端；本库不会因为参数变化而切换格式。
* **meta 标签过滤**：单标签与 strict 两条端点的页面原文都写了 “not available for meta tags”，
  属服务端不可用；页面也没有定义哪些标签是 meta 标签，库不猜、不绕过。
* **写操作与账号动作**：页面第一句即 read-only、全部 `GET`；本库没有上传、编辑、删除、收藏、投票、
  评论、登录、cookie 会话、API key 管理这类方法，也不为它们留入口（`request()` 连 `method` 参数都没有）。
* **其余资源端点**：页面只记录了 5 条路径形态（全部条目、单标签、strict、多标签、详情），
  本站额外记录的 `t=0` 只是根路径换了参数。标签目录、画师、评论、wiki、合集这类端点页面**没有提供**；
  本库不为未文档化的端点造方法，也不把站点 HTML 页面当 API 用。
* **限流**：页面写明 60 请求/分钟、长期超限可能封禁，但**没有描述超限后的响应**；
  客户端不执行限流，也不把限流错误翻译成别的异常。超限后的真实行为属未实测。
* **浏览器页面**：`/3793685` 不带 `json` 已记录为 HTML，本库不抓取或解析 HTML 页面，
  也不从这一条记录推断站点每个地址的输出格式。

## “不可用”与“未实测”的分界

两类结论不能混写：

| 结论 | 适用项 | 依据 |
| :--- | :--- | :--- |
| **服务端声明不可用** | 单标签与 strict 端点的 meta 标签过滤 | 页面原文 “not available for meta tags” |
| **API 设计使然** | 写操作、账号动作（API 只读） | 页面原文 “read-only … all requests are done using GET” |
| **本库刻意不做** | `xml` 输出、HTML 抓取、自动翻页、引擎识别 | 本库取舍，不是站点限制 |
| **页面未提供** | 标签目录 / 画师 / 评论 / wiki / 合集等端点 | 页面只记录 5 条路径，未提供即未定义；不宣称“站点没有” |
| **已观察但行为异常** | `s=fav&t=0`：页面写了可取 `0`，当前却返回 `500` 且正文非 JSON | 一次记录，不足以归纳成因；不写成“已下线”，也不写成“可用” |
| **未实测** | `t=0` 的成功路径、`p` / `l` 越界与极端值、其它参数组合、超限流响应、网络错误与别的 5xx | 页面未描述，也没有对应的响应记录 |

User-Agent 属第三种口径之外的策略项：页面说“required”，同时说“may still be completed successfully
without this custom header”，并提示匿名项目可能被封。已有记录里默认 UA 的匿名请求成功过（见
[verification.md](verification.md)），这**只说明当时没有被拒绝**，不能推翻页面的风险提示，
也不能证明某个 UA 安全。

## 未实测

* 单标签与 strict 端点遇到 meta 标签时的具体响应（页面已声明不可用，但没有响应记录）。
* `t=0` 的成功路径（当前只有一条 `500` 记录）；`l` / `p` 的边界与非法值；
  `t` 取 `0` / `1` / `2` 之外的语义变化；`d` / `c` 的非法取值；两条端点换其它取值的组合。
* 超限流后的状态码与正文；是否带限流相关响应头；封禁触发条件。
* 其它错误路径：不存在的条目 id、非法 id、网络错误、别的 5xx；已有错误记录只有 `t=0` 那条，
  其正文不是合法 JSON。
* 名字含 `/`、`,`、`&` 等特殊字符的标签在服务端的匹配结果（只确认了客户端的编码）。
* 站点内容范围、地区/出口差异、加入用户名后的合规 UA 对响应的影响；页面没有给出完整可见性契约。
* 为这些分支没有发出过探测请求；已发出的调用逐条记录在
  [verification.md](verification.md#zerochan匿名只读实测2026-09-18)，
  本文不把“页面有原文”当作“已实测”。
