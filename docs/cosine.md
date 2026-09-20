# Cosine 客户端用法

`Cosine` 访问 Cosine Gallery（`https://pic.cosine.ren`，Telegram 频道 `@CosineGallery` 的配套图站）的自研 JSON API。  
它不是 Danbooru / Moebooru / Gelbooru 系的 booru 引擎：没有 `rating` 字符串、没有 `post` 对象、没有点号参数，标签是字符串数组，站点编号 `id` 与上游编号 `pid` 是两个不同数字。别把别的家族的路由、参数名或返回结构搬过来。

客户端一共 **13 个原生方法**：**11 个读取**（10 条 JSON 读取加 `feed()` 的 XML 原文入口）和 **2 个 `POST`**。  
`search_index_admin()` 会改站点搜索索引；`artwork_revalidate()` 是站点内部刷新入口；两者本轮都没有发出。

逐条参数与返回字段见[方法参考](cosine-api.md)；「我要做什么 → 用哪个方法」与 13 方法索引见[能力入口](cosine-capabilities.md)。本轮匿名只读请求与响应摘要见[验证记录](verification.md#cosine匿名只读实测2026-09-20)；**没有样本的说法**（参数取值边界、索引源码细节、两个 `POST` 的成功路径、媒体取图要求）集中在[依据与差异的边界清单](cosine-contract-notes.md#未实测集中清单)，本页不把它们写成承诺。

**没有任何方法会下载媒体**：`rawurl` / `thumburl` 只是响应里的字符串，客户端不解析、不拼接、不落盘；地址规则只写在[媒体地址](#媒体地址只返回字符串本库不下载)一节。

## 返回外壳：先认清四种，再取字段

站点每个路由给的外壳不同，客户端一层都不拆：你拿到的就是站点发的那一层。每条路由属于哪类是固定的。

| 外壳 | 形状 | 哪些路由 | 失败时的形状 |
| :--- | :--- | :--- | :--- |
| **A 信封** | `{"json": …, "meta": {"values": …}}` | `GET /api/artwork/{id}`、`GET /api/random` | `{"error": "…"}` |
| **B 列表** | `{"images": […], "total": N}`；`/api/artists` 是 `{"artists": […], "total": N, "hasNextPage": true/false}` | `GET /api/list`、`GET /api/artist` 的列表分支、`GET /api/artists` | `{"error": "…"}` |
| **C 结果** | `{"success": true, "data": {…}}` | `GET /api/search`、`GET /api/search/suggestions`、`GET /api/search/admin` | `{"success": false, "error": "…", "message": "…"}` |
| **D 裸数组** | `[…]`；`/api/tag` 是作品对象数组，`/api/tags` 是 `{tag, count}` 数组，都没有 `total` | `GET /api/tag`、`GET /api/tags` | `{"error": "…"}` |

A 的 `meta.values` 是 superjson 对 `BigInt` / `Date` 字段的说明，键随数据变化：

- `/api/artwork/1` 本轮是 `{"userid": ["bigint"], "create_time": ["Date"], "authorid": ["bigint"]}`。
- `/api/random?count=3` 返回数组时，键带下标：`0.userid`、`0.create_time`、`0.authorid`、`1.userid`…，不是恒定三个键。
- 数组形态的 `meta` 还可能多出 `referentialEqualities`；本轮 `/api/random?count=3` 是 `{"0.userid": ["1.userid", "2.userid"]}`。  
  所以 `meta` 的键也随请求变化，别按固定键集去取。

`feed()` 是第五种形态：不是 JSON，见[feed()](#feed站点-rss-原文)。

## 主机与路径：客户端只对 API 主机说话

包内 `sites.cosine` 的 `url` 是站点根 `https://pic.cosine.ren`。13 个方法都接在它后面：`feed()` 走 `/feed.xml`，其余走 `/api/…`。站点页面路由不包装，`rawurl` 指向的图片主机也不会被请求。

| 主机 / 路径 | 角色 | 本轮是否请求 |
| :--- | :--- | :--- |
| `https://pic.cosine.ren/api/*` | JSON API：包内配置值 + `/api` 路径 | **是**，本轮全部匿名 `GET` 都在这里；两条 `POST` 没有发出 |
| `https://pic.cosine.ren/feed.xml` | RSS 2.0 原文，`feed()` 用它 | **是**，`200 application/xml; charset=utf-8` |
| `https://pbs.twimg.com` | Twitter 图源，出现在 `rawurl` / `thumburl` | 未请求；本库不下载媒体 |
| `https://i.pximg.net` | Pixiv 图源，出现在 `rawurl` / `thumburl` | 未请求；本库不下载媒体 |
| `https://piv.cosine.ren` | 站点的 Pixiv 镜像域名，只有 `/api/random` 会把 `i.pximg.net` 换成它 | 未请求；本库不下载媒体 |
| `https://backblaze.cosine.ren` | 输入资料提到的原图兜底域名 | 未请求；输入资料 4 个样本全是 `404`，不把它当主链路 |
| `/`、`/search`、`/tag/{标签}`、`/artists`、`/artist/{platform}/{uid}`、`/artwork/{id}` | 站点页面，不是 API | 未请求；本库不抓 HTML，需要时用 `request()` 自己试 |

## 第一次调用：分页列表

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    page = client.image_list(page=1, pageSize=2)
    # GET https://pic.cosine.ren/api/list?page=1&pageSize=2
    # 200 application/json：{"images": [...], "total": 4953}
    print(page['total'], [image['id'] for image in page['images']])  # 4953 [5003, 5002]

    second = client.image_list(page=2, pageSize=2)
    # GET https://pic.cosine.ren/api/list?page=2&pageSize=2 → 同信封，本轮 id 5001、5000
    print([image['id'] for image in second['images']])
    print(client.last_call['status_code'], client.last_call['url'])
```

`image_list(**params)`：给分页参数，返回 B 列表外壳 `{"images": [...], "total": N}`。

- `page`：页码，**从 1 开始**。`page=1` 第一页，`page=2` 第二页。  
  本轮：`page=0`、`page=-1` 都是 `500 {"error": "获取图片列表失败"}`；`page=100000` 超末页返回空数组，`total` 不变，不报错。
- `pageSize`：每页条数。  
  本轮：不传返回 **10 条**，`total` 仍是 4953；`pageSize=100` 返回 100 条；`pageSize=0` 返回 `{"images": [], "total": 4953}`；`pageSize=-1` 只返回最旧 1 条，`id` 为 1。

这些都是单次取值样本，不是完整取值规则。

列表里每张图是扁平对象，本轮 21 个键：

`id`、`userid`、`username`、`create_time`、`platform`、`title`、`page`、`size`、`filename`、`author`、`authorid`、`pid`、`extension`、`rawurl`、`thumburl`、`width`、`height`、`guest`、`r18`、`ai`、`tags`。

容易看错的语义：

- `id` 是站内自增编号，本轮列表样本是 5003、5002；`pid` 是上游编号，即 Pixiv illust id / Twitter 推文 id。两者都是标识，但不是同一个东西。`pid` 相同的多张图是同一帖的多页。
- `userid` / `username` 按输入资料是投稿人，不是画师。本轮作品样本里都是 `"6030777595"` / `"@cosine_yu"`，即频道搬运账号；样本没有第二条投稿人。`author` / `authorid` 按输入资料是画师。这两个语义本轮没有从上游投稿代码独立验证，样本也不能证明恒定。
- `title` 在本轮 Twitter 样本里是推文正文，可含换行、emoji、`#标签`，例如 `"「先輩、彼女さんいたんですね。あ、ご注文は？」"`。这是样本观察，字段语义没有独立核对。
- `page` 起点按输入资料是 Pixiv 从 0 起、Twitter 从 1 起。本轮样本正好一个 0、一个 1，但这是语义候选加单点样本，同一 `pid` 的多页编号规则本轮未核。
- `size` 与 `guest` 在本轮新数据样本里是 `null` / `false`；最老样本 `id 1` 是 `size` 675622 / `guest` true。只有这两个样本层面观察，别按它们判断图片是否可用或新旧。
- `tags` 是字符串数组，可能重复：`/api/artwork/1` 的 8 项里只有 4 个不同值。前缀不统一：`/api/artwork/1` 与 `/api/random` 本轮样本带 `#`；`/api/list` 本轮样本是 `["原神", "精选", "壁纸"]`、`["甜妹"]`。客户端不做归一化，要比较就自己 `lstrip('#')`。
- `rawurl` / `thumburl` 是图源地址字符串，`platform` 不同主机也不同，详见[媒体地址](#媒体地址只返回字符串本库不下载)。

## 作品详情：A 信封

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    detail = client.artwork_show(1)
    # GET https://pic.cosine.ren/api/artwork/1
    # 200 application/json：{"json": {...}, "meta": {"values": {...}}}
    artwork = detail['json']          # 真实对象在 json 里，客户端不替你取出来
    print(artwork['id'], artwork['platform'], artwork['author'])
    # 1 twitter bshi_edayo
    print(artwork['rawurl'])          # .../GCbmIUma8AAQ6ok?format=jpg&name=orig
    print(artwork['thumburl'])        # .../GCbmIUma8AAQ6ok?format=jpg&name=large
    print(detail['meta']['values'])   # {'userid': ['bigint'], 'create_time': ['Date'], 'authorid': ['bigint']}
```

`artwork_show(artwork_id)`：给作品 `id`，返回 A 信封 `{"json": {...}, "meta": {"values": {...}}}`。

- 详情对象与列表项字段集相同，本轮 `/api/artwork/3840` 与列表项都是那 21 个键。
- 详情不补 `originUrl` / `authorUrl`，只有 `/api/random` 补。
- `platform` 是 `pixiv` 时，`rawurl` / `thumburl` 是 `i.pximg.net` 原样地址。本轮 `/api/artwork/3840` 是 `https://i.pximg.net/img-original/img/2025/09/26/18/12/27/135557027_p0.png`。
- Twitter 来源地址可能没有扩展名。本轮 `/api/artwork/1` 是 `https://pbs.twimg.com/media/GCbmIUma8AAQ6ok?format=jpg&name=orig`，扩展名靠 `format=jpg` 给出。

错误样本都是 `{"error": "…"}`，没有 `json` 键：

- `artwork_show(999999999)`：`404 {"error": "未找到该作品"}`
- `artwork_show('abc')`：`500 {"error": "服务器错误"}`。非数字编号是 500 不是 400；客户端不做本地校验，编号会按路径段编码后发出。

## 随机图：1 张是对象、多张是数组

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    one = client.image_random(count=1)
    # GET https://pic.cosine.ren/api/random?count=1
    artwork = one['json']             # 只有 1 张时 json 是对象，不是只含一个元素的数组
    print(artwork['id'], artwork['originUrl'], artwork['authorUrl'])
    # 1666 https://www.pixiv.net/artworks/124508716 https://www.pixiv.net/users/51689952
    print(one['meta']['values'].keys())   # dict_keys(['userid', 'create_time', 'authorid'])  ← 不带下标

    many = client.image_random(count=3)
    # 200：json 是数组（本轮 3 项），meta.values 的键带下标：0.userid、1.userid、2.userid…
    print([item['id'] for item in many['json']], len(many['json']))
    print(list(many['meta']['values'])[:3])
```

`image_random(**params)`：给 `count`，返回 A 信封。`json` 的类型随数量变化：

- 不传与 `count=1`：`json` 是一个对象。
- `count=3`：`json` 是 3 项数组。
- `count=0` 与 `count=-5`：仍是 1 张，`json` 是对象。
- `count=100`：回 20 项数组。
- `count=abc`：`404 {"error": "未找到图片"}`。

所以「取多少张」先看 `json` 类型，再决定怎么遍历，别写死 `json[0]` 或写死遍历。

顺序没有保证。输入资料称「结果顺序按主键」；本轮 `count=3` 样本 `id` 是 2042、2741、3927，`count=100` 的 20 条也是升序。但站点公开源码 `src/app/api/random/route.ts` 只读单文件里的查询没有 `orderBy`，所以既不能承诺升序，也不代表它按随机序号排；本轮样本不足以外推。

`/api/random` 是本轮 JSON 读取路由里唯一给图源做加工的路由：补 `originUrl`、`authorUrl`，并把 Pixiv 的 `i.pximg.net` 换成 `piv.cosine.ren`。`/api/list`、`/api/artwork/{id}`、`/api/tag`、`/api/search`、`/api/artist`、`/api/artists` 本轮都把 `i.pximg.net` 原样返回。

```python
# count=1 的样本（Pixiv 来源）
#   rawurl    https://piv.cosine.ren/img-original/img/2024/11/21/22/26/20/124508716_p0.jpg
#   thumburl  https://piv.cosine.ren/img-master/img/2024/11/21/22/26/20/124508716_p0_master1200.jpg
#   originUrl https://www.pixiv.net/artworks/124508716
#   authorUrl https://www.pixiv.net/users/51689952
# 缺省 count（不传参数）的样本（Twitter 来源，主机不变）
#   rawurl    https://pbs.twimg.com/media/GzmdyBfbEAA0ww_.jpg?name=orig
#   originUrl https://x.com/_/status/1961772823841738792
#   authorUrl https://x.com/i/user/1502621932717424640
```

`/api/random` 的标签前缀不统一，同一张图里也可能混着：

- `count=1` 的 Pixiv 样本：`["#初音未来", "#VOCALOID", "#插画", "#vocaloid", "#Vocaloid", "#miku"]`
- `count=-5` 的 Pixiv 样本，`id 3037`：`["原创", "女孩子", "双胞胎", "商业绘图", "吊袜带", … "#大", "#甜妹", "#蓝色系"]`
- `count=3` 的第二个元素：`["插画", "女孩子", "萝莉"]`

所以既不能写「`/api/random` 一定带 `#`」，也不能写「一定不带」。输入资料与站点公开源码 `src/app/api/random/route.ts` 只读单文件说这里是 `replace(/#+/g, '#')`，即把连续 `#` 收敛成一个，不是补 `#`；本轮没有对照输入，这条规则本身未实测。客户端原样返回，不增删。

## 搜索：C 信封，`hits` 是另一套字段

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    result = client.search(q='初音', limit=2)
    # GET https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2
    data = result['data']             # {'success': true, 'data': {...}}
    print(data['query'], data['total'], data['limit'], data['offset'], data['processingTimeMs'])
    # 初音 255 2 0 65
    hit = data['hits'][0]
    print(type(hit['id']).__name__, hit['tags'])   # str ['甜妹', '樱', 'miku', '粉色系', '樱未来']
    print(hit['searchable_content'][:20], type(hit['_formatted']).__name__)
```

`search(**params)`：给搜索参数，返回 C 结果外壳 `{"success": true, "data": {...}}`。`data` 里有 `query`、`total`、`limit`、`offset`、`processingTimeMs`、`hits`。

`hits` 每一项不是列表 / 详情里的图片对象：

- `id` 是字符串。
- `tags` 是字符串数组。
- 另有 `searchable_content` 与 `_formatted`。
- 字段集合不固定：真实分页搜索的 `id='2721'` 缺少 `title`，不要把某条命中的键当成全部结果必有的字段。
- 列表里的 `userid` / `username` / `page` / `size` / `guest` / `extension` 不在本轮搜索样本中。

详细字段表见[方法参考](cosine-api.md#search)。

本轮搜索参数样本，都是单次取值：

| 参数 | 本轮观察 |
| :--- | :--- |
| 不传 `q` / `q=''` | `query` 是 `""`、`total` 1000。它不是全库：同一时刻索引进度 `indexedImages` 3353、库里 `totalImages` 4953，空 `q` 最多只给 1000 条 |
| `limit` | 不传时 `limit` 20；`limit=500` 回 `limit` 100 |
| `offset` | `offset=100000` 回 `offset` 1000 且 `hits` 为空；`limit=-1`、`offset=-5` 是 `500`，Meilisearch 英文报错 |
| `total` | 是估算值，源码直接取 Meilisearch 的 `estimatedTotalHits`。它只反映索引，而且是上限：被夹到 1000，不会先给出大于 1000 的值，也不等于库里真实条数 |
| `platform` | `pixiv` / `twitter` 有结果，本轮 `total` 都是 1000；`unknown` 回 `total` 0 |
| `tags` | 忽略大小写全等：`GenshinImpact` 与 `genshinimpact` 都是 166。标签要写完整标签名。多个标签用逗号写在一个值里是 AND：`原神,GenshinImpact` 是 160，小于单个 `原神` 的 510。带 `#` 的取值本轮只在 `tag_images` 上测过，回空数组；`search` 没有单独测 |
| `r18` | 字面量 `'true'` 选择 R18，本轮 7 条全为 `true`；`'false'` 与 `'1'` 选择非 R18，本轮命中均为 `false`。不传才不过滤。各自 `total=1000` 不能证明过滤没有生效 |
| `sort` | `width:asc` 有效；非法值 `bogus` 是 `500 {"success": false, "error": "Internal search error", "message": "Invalid syntax for the sort parameter: …"}` |

本轮样本里 `limit` / `offset` / `total` 都被站点改成 100 / 1000 量级的值，输入资料也说是站点端夹取。这不是本库的钳位：客户端把值原样发出。`sort` 与 `total` 的完整取值规则没有穷举，未知值别按样本外推。

### search_suggestions()

`search_suggestions(**params)`：给 `q`，返回 C 信封。`data` 是 `{"suggestions": [{"text": …, "type": …}, …], "query": …}`。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    print(client.search_suggestions(q='miku')['data']['suggestions'][:2])
    # [{'text': 'miku', 'type': 'general'}, {'text': 'MIKU', 'type': 'general'}]
    print(client.search_suggestions(q='a')['data'])   # {'suggestions': [], 'query': 'a'}  ← 单字符回空
```

本轮 `q='miku'` 不带 `limit` 得到 10 条，`limit=50` 得到 15 条，即该查询的候选数量。「`limit` 上限 20、小于 2 个字符回空」来自输入资料与本轮单字符样本（`q='a'` 回空），上限没有逐值实测。本轮样本 `type` 都是 `"general"`，不保证恒定。

### search_index_status()

`search_index_status()`：无参数，读 `GET /api/search/admin` 的只读分支，返回 C 信封。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    status = client.search_index_status()['data']
    # {'totalImages': 4953, 'indexedImages': 3353, 'indexHealth': 'partial',
    #  'lastSyncTime': '2026-09-19T16:42:34.383Z'}
    print(status['totalImages'], status['indexedImages'], status['indexHealth'])
```

`lastSyncTime` 是不可信值：站点公开源码 `src/lib/search/indexing-service.ts` 的 `getIndexReport()` 把它写成 `new Date()`，源码注释也说明这里本应存真实同步时间，所以它是请求那一刻，不是真正的同步时间。本库原样返回，不修正。`indexHealth` 与两个计数只作进度参考：本轮 `totalImages` 4953 是库里的图片数，`indexedImages` 3353 是索引里的文档数。

## 标签：D 裸数组，`count` 不是作品数

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    works = client.tag_images('GenshinImpact', start=0, limit=2)
    # GET https://pic.cosine.ren/api/tag?tag=GenshinImpact&start=0&limit=2
    # 200 application/json：裸数组，没有信封、没有 total
    print([item['id'] for item in works])          # [4971, 4970]
    print(works[0]['tags'])                        # ['原神', 'GenshinImpact', '桑多涅原神', '甜妹']

    next_page = client.tag_images('GenshinImpact', start=2, limit=2)
    print([item['id'] for item in next_page])      # [4967, 4964]   ← start 是跳过条数，不是页码
```

`tag_images(tag, **params)`：

- `tag` 是位置参数，也是必填项。不传时站点回 `400 {"error": "标签参数缺失"}`。
- 标签要完整且不带 `#`。本轮 `tag='#GenshinImpact'` 回 `[]`。
- 大小写不敏感：`genshinimpact` 与 `GenshinImpact` 同结果。
- 逗号不是分隔符：`tag='原神,GenshinImpact'` 本轮回 `[]`，它被当成一个完整标签名精确匹配。
- `start` 是跳过条数，不是页码。
- 返回裸数组。结果为空数组就是没有更多了，用 `len(...) == 0` 判末尾，不要找 `total`。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    tags = client.tag_list()
    # GET https://pic.cosine.ren/api/tags
    # 200 application/json：裸数组，本轮 2128 项
    print(len(tags), tags[0])                      # 2128 {'tag': '甜妹', 'count': 1309}
    counts = {item['tag']: item['count'] for item in tags}
    print(counts['原神'], counts['GenshinImpact'], counts['RuanMei'])   # 450 137 9
```

`tag_list()`：不要参数，返回 `{"tag": …, "count": …}` 裸数组。

`count` 是标签关联表的行数，不是用了该标签的作品数。站点公开源码 `src/app/api/tags/route.ts` 按 `tag` 做 `groupBy`、取 `_count.tag`，清掉前导 `#` 后合并同名，再按 `count` 降序输出。所以它不能和 `search(tags='RuanMei')` 的 `total`、也不能和 `tag_images()` 的返回条数互相换算。本轮同一时刻：

- `tag_list()` 的 `RuanMei` 是 9。
- `search(tags='RuanMei')` 的 `total` 是 9，即索引里的 9 条。
- `tag_images('RuanMei', limit=100)` 返回 10 张、8 个不同 `pid`。
- 把每张图的 `tags` 逐项数一遍，`RuanMei` 出现 14 次。

三个数字口径完全不同：9 / 10 / 14。别把作品数组的 `tags` 累加当计数。这个路由带静态缓存，本轮响应有 `X-Nextjs-Cache: HIT`，数据不是实时刷新。

## 画师

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    works = client.artist_images('pixiv', '54390221', page=1, pageSize=2)
    # GET https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&page=1&pageSize=2
    # 200 application/json：{"images": [...], "total": 78}   ← B 外壳
    print(works['total'], [item['id'] for item in works['images']])   # 78 [4869, 4827]

    profile = client.artist_images('pixiv', '54390221', infoOnly=True)
    # GET https://pic.cosine.ren/api/artist?platform=pixiv&authorid=54390221&infoOnly=true
    # 200 application/json：裸资料对象，不是列表外壳
    print(profile)   # {'author': 'makoron117', 'authorid': '54390221', 'platform': 'pixiv', 'artworkCount': 78}
```

`artist_images(platform, authorid, **params)`：两个位置参数都必填，漏传会先触发 Python `TypeError`。

- 列表分支返回 B 外壳 `{"images": [...], "total": N}`。
- `infoOnly` 只有字面量 `'true'` 走资料分支。本轮 `infoOnly=1` 仍返回 `{"images": [...], "total": ...}`。
- 直接请求 `/api/artist` 缺 `platform` 的样本是站点 `400`。
- `authorid='abc'` 得到 `500 {"error": "获取画师数据失败"}`。
- 资料分支没有作品时是 `404 {"error": "未找到该画师"}`。

资料对象不在四种外壳里，只有 `author`、`authorid`、`platform`、`artworkCount` 四个键。资料里的 `author` 可能与作品列表里的 `author` 不同：本轮资料给 `makoron117`，同一画师的作品列表给 `まころん夏コミC48土お52日`。输入资料称站点源码里资料来自不带排序的 `findFirst`，本轮未做源码核对，所以别把资料名当唯一真名，也不要拿它和列表里的 `author` 做等值匹配。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    first = client.artist_list(page=1, pageSize=2, sortBy='artworks')
    # GET https://pic.cosine.ren/api/artists?page=1&pageSize=2&sortBy=artworks
    # 200 {"artists": [...], "total": 1708, "hasNextPage": true}
    print(first['total'], first['hasNextPage'], first['artists'][0]['authorid'])   # 1708 True 54390221
    for artist in first['artists']:
        print(artist['platform'], artist['authorid'], artist['author'], artist['artworkCount'])
        print(artist['latestImageThumb'], artist['lastUpdateTime'])
```

`artist_list(**params)`：给分页与排序参数，返回 `{"artists": [...], "total": N, "hasNextPage": true/false}`。

本轮样本：

- 不带参数返回 20 项、`total` 1708、`hasNextPage` true。
- `sortBy='artworks'`：本轮首个 `authorid` 是 54390221。
- `sortBy='random'`：本轮首个是 `夏炉`。
- `sortBy='lastUpdate'`：本轮首个是 `torino`，其 `lastUpdateTime` 与列表最新一条时间相同。
- 未知值静默回落成 `artworks`：本轮 `sortBy=unknown` 与不传结果一致。

每项字段是 `platform` / `authorid` / `author` / `artworkCount` / `latestImageThumb` / `latestImageFilename` / `lastUpdateTime` / `latestImageWidth` / `latestImageHeight`。`latestImageThumb` 是站内原始图源地址，Pixiv 画师是 `i.pximg.net`；`/api/random` 的域名替换不作用在这里。本库同样不下载它。

## feed()：站点 RSS 原文

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    feed = client.feed()
    # GET https://pic.cosine.ren/feed.xml
    # 200 application/xml; charset=utf-8
    print(type(feed).__name__, feed[:38])          # str <?xml version="1.0" encoding="utf-8"?>
    print('RSS 条目数:', feed.count('<item>'))     # 20
```

`feed()`：无参数，请求 `GET feed.xml`，按 `response.text` 原样返回完整 XML 原文字符串，不解析、不嗅探、不把 `Content-Type` 当依据。它是该客户端唯一返回字符串的方法。

本轮样本是 RSS 2.0、20 个 `<item>`，`<guid>` 是站内编号 3290、3288、3289…，`<lastBuildDate>` 是 `Sun, 10 Aug 2025 13:07:22 GMT`，响应带 `X-Nextjs-Cache: HIT`。所以它既不是「当前最新 20 张」（`/api/list` 的最新编号早已是 5003 一带），也不是实时源。`<item>` 的 `<description>` 里嵌了 `piv.cosine.ren` 的缩略图 HTML；本库只把字符串给你，不解析 HTML，也不下载其中的图片。

## 构造与配置

签名：

`Cosine(site_name=None, site_url=None, revalidate_secret=None, proxies=None, *, config_file=None, timeout=None, user_agent=None)`

| 参数 | 取值、含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `site_name` | 字符串，配置 `sites` 中的键名 | 不选命名站点，需显式给 `site_url` | `Cosine('cosine')` |
| `site_url` | 字符串，站点基地址 | 读取所选站点的 `url`，包内是 `https://pic.cosine.ren` | `Cosine(site_url='https://pic.cosine.ren')` |
| `revalidate_secret` | 字符串，只用于 `artwork_revalidate()` 的请求体 | `None` 且有站点名时读站点条目的 `revalidate_secret`，包内是空串 | `Cosine('cosine', revalidate_secret='…')` |
| `proxies` | 字典，按 `http` / `https` 指定代理，`{}` 表示直连 | 使用 `request.proxies`；不读环境变量 | `Cosine('cosine', proxies={})` |
| `config_file` | JSON 配置文件路径，或 `None` | 读随包安装的 `anybooru.json` | `Cosine('cosine', config_file='my-anybooru.json')` |
| `timeout` | 秒数，或连接 / 读取超时二元组 | 使用 `request.timeout` | `Cosine('cosine', timeout=10)` |
| `user_agent` | 请求的 User-Agent 字符串 | 使用 `request.user_agent` | `Cosine('cosine', user_agent='MyBooruApp/1.0')` |

构造不发任何请求，也不校验密钥。用完记得 `client.close()`，或用 `with` 语句块。包内站点条目只有两个字段：

```json
{"cosine": {
  "url": "https://pic.cosine.ren",
  "revalidate_secret": ""
}}
```

复制完整配置的方法见[配置指南](configuration.md)。

## 空密钥语义：只有 `artwork_revalidate()` 会用到它

- 本库没有登录、注册、换令牌的方法，也不索要账号。11 条读取路由本轮都有匿名 `200` 样本。
- `revalidate_secret` 是站点自己的 `REVALIDATE_SECRET`，只出现在 `POST /api/artwork/revalidate` 的 JSON 正文里：`{"artworkId": …, "secret": …}`。
- `None` 表示「没给」：有站点名时从配置读，包内是空串。显式空串 `''` 就是空串本身，仍会被放进正文。也就是说这个方法从不省略 `secret` 字段，空密钥照发，由站点决定结果（源码只读显示站点拿它与环境变量比较，不相等才回 `401`，本轮未实测，见[两个 `POST`](#search_index_admin危险会改站点数据绝不要手滑)）。
- 其它 12 个方法不会带这个密钥：不在查询串、不在请求头、不在正文。匿名调用不会因为配置里有密钥而变成带密钥请求。

## 两个 `POST`：先看清楚再决定

### `search_index_admin()`：危险，会改站点数据，绝不要手滑

这是本轮唯一会修改站点搜索索引的方法。`action` 是 `initialize` / `index_all` / `sync_recent` / `rebuild` / `validate`，其中重建类动作会重建或删除站点的搜索索引数据。站点公开源码里这个路由没有鉴权检查，任何人都能触发。因此本库与本轮所有脚本都没有调用它，本轮对 `POST /api/search/admin` 零请求，它的成功与失败响应都没有样本。下面片段不是可运行示例，只是把请求形态写清楚。

```text
请求形态（不要照抄执行）
  POST https://pic.cosine.ren/api/search/admin
  正文：{"action": "rebuild"}            # action 必填
  可选参数与 action 一起进正文，例如 batchSize / hours；值由你给，客户端不钳位、不校验、不重试
```

调用方式例如 `client.search_index_admin('index_all', batchSize=100)`，本轮未执行。位置参数是 `action`，其余参数合并进正文，得到 `{"action": "index_all", "batchSize": 100}`。只读索引状态请用 `search_index_status()`，即 `GET` 同一路由，不要为了「看看状态」去点这个 `POST`。

源码只读、本轮没有样本的响应形状，来自站点公开源码 `src/app/api/search/admin/route.ts` 只读单文件，不是本轮响应证据：

- `POST` 直接按 `action` 分支。
- `validate` 回 `{"success": true, "data": …}`。
- `initialize` / `index_all` / `sync_recent` / `rebuild` 回 `{"success": true, "message": …}`。
- 非法 `action` 回 `400 {"success": false, "error": "Invalid action"}`。
- `index_all` 的 `batchSize` 缺省 100；`sync_recent` 的 `hours` 缺省 24。

这些都没有本轮样本，别当契约用。

### `artwork_revalidate()`：需要站点密钥，本轮同样没有调用

它请求 `POST /api/artwork/revalidate`，正文是 `{"artworkId": <编号>, "secret": <密钥>}`，用来请站点刷新某个作品的缓存。`secret` 规则见上一节：不传就取构造时的 `revalidate_secret`，显式空串就是空串，字段总会出现。本轮没有发这条请求，所以成功、`401`、错误体全部没有样本，客户端也不做重试或兜底。

源码只读、本轮没有样本的行为，来自站点公开源码 `src/app/api/artwork/revalidate/route.ts` 只读单文件：

- 站点把正文里的 `secret` 与 `process.env.REVALIDATE_SECRET` 比较，不相等就回 `401 {"message": "无效的密钥"}`。
- 缺 `artworkId` 回 `400`。
- 成功回 `{"revalidated": true, "now": …}`。
- 所以空密钥不一定被拒：如果站点环境变量恰好也是空串，两边就相等。本轮一次都没有请求过，连空密钥结果也没有实测。

```python
from anybooru import Cosine

# 未执行、未实测：下面只是把调用形态写全，需要站点密钥才可能成功
with Cosine('cosine', revalidate_secret='<站点 REVALIDATE_SECRET>') as client:
    result = client.artwork_revalidate(1)          # 等价于 secret='<站点 REVALIDATE_SECRET>'
    print(result)
```

## 通用入口 `request()`

签名：

`request(method, path, *, params=None, data=None, headers=None, response_format='json')`

它与 13 个原生方法走同一条通路，只是路径、动词、正文和返回格式由你给全。`path` 会去掉前导 `/` 后拼在站点根后面，与 Anime-Pictures 家族的 `urljoin` 语义不同。

| `path` 写法 | 实际请求的地址 | 说明 |
| :--- | :--- | :--- |
| `'api/list'` | `https://pic.cosine.ren/api/list` | 相对站点根，最常用 |
| `'/api/list'` | `https://pic.cosine.ren/api/list` | 前导 `/` 被去掉，与上一条等价 |
| `'feed.xml'` / `'/feed.xml'` | `https://pic.cosine.ren/feed.xml` | 站点根下的文件 |
| `'api/artwork/1'` | `https://pic.cosine.ren/api/artwork/1` | 路径段不会被自动编码，编号要自己拼 |

| 参数 | 取值与含义 | 不传时怎样 | 字面示例 |
| :--- | :--- | :--- | :--- |
| `method` | HTTP 动词字符串 | 必填 | `client.request('GET', 'api/list', params={'page': 1})` |
| `path` | 上面那张表的路径写法 | 必填 | `client.request('GET', 'api/artwork/1')` |
| `params` | 查询参数字典，按下面的编码规则发出 | `None`，不发查询参数 | `client.request('GET', 'api/list', params={'page': 1, 'pageSize': 2})` |
| `data` | JSON 请求体：字典原样写进正文，`None` 值也写，成为 `null`，不清理、不改名、不走查询编码 | `None`，不带请求体 | `client.request('POST', 'api/artwork/revalidate', data={'artworkId': 1, 'secret': ''})` |
| `headers` | 额外请求头字典，只作用于本次请求 | `None`，不附加 | `client.request('GET', 'feed.xml', headers={'Accept': 'application/xml'})` |
| `response_format` | `'json'` 解析 JSON；`'xml'` 返回 `response.text` 原文 | `'json'` | `client.request('GET', 'feed.xml', response_format='xml')` |

参数编码用本库共享的 Rails 风格编码，规则三条：

| 你传的值 | 发出去的样子 | 例子 |
| :--- | :--- | :--- |
| `None` | 整个键丢弃；查询串与正文的 `data` 不动 | `params={'q': None, 'limit': 2}` 只发 `limit=2` |
| 布尔 | 小写 `true` / `false` | `params={'r18': True}` 发 `r18=true` |
| 列表 / 元组 / 嵌套字典 | 键带方括号：列表 `key[]=值` 重复；字典 `key[子键]=值` | `params={'tags': ['原神', 'GenshinImpact']}` 发 `tags%5B%5D=原神&tags%5B%5D=GenshinImpact` |

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    same = client.request('GET', '/api/list', params={'page': 1, 'pageSize': 2})
    # 前导斜线等价写法：GET https://pic.cosine.ren/api/list?page=1&pageSize=2
    print(same['total'], client.last_call['url'])

    raw_feed = client.request('GET', 'feed.xml', response_format='xml')
    print(type(raw_feed).__name__, raw_feed[:38])   # str <?xml version="1.0" encoding="utf-8"?>
```

客户端不补 `/api` 前缀、不补 `.json`、不拆信封、不改字段名、不合并分页、不重试、不钳位任何参数、不做本地参数校验、不变换 `response_format`。

注意站点多标签参数用逗号串而不是数组，即 `search(tags='原神,GenshinImpact')`。用 `request()` 传 `tags=['原神', 'GenshinImpact']` 会发成 `tags[]=…`，站点是否接受这种写法本轮没有样本。需要多标签时优先用原生 `search()` 的逗号串写法。

## 返回值与 `last_call`

| 服务端给了什么 | 你拿到什么 |
| :--- | :--- |
| JSON 正文 | 解析后的 Python 对象，一层都不拆：A 是 `{"json", "meta"}`；B 是 `{"images"/"artists", "total"(, "hasNextPage")}`；C 是 `{"success", "data"}`；D 是数组 |
| `response_format='xml'` | `str`，即 `response.text` 原文，见 `feed()` 与 `request(..., response_format='xml')` |
| HTTP 非 2xx | 抛 `AnybooruHTTPError`，带 `http_code`、`url`、`body`、`data`。本轮样本：`400 {"error": "标签参数缺失"}`、`404 {"error": "未找到该作品"}`、`500 {"error": "获取图片列表失败"}`、`500 {"success": false, "error": "Internal search error", "message": "…"}` |
| 2xx 但正文为空 | 返回 `None`，空响应不当错误处理 |
| 2xx 但正文不是 JSON | 抛 `AnybooruAPIError` |
| 网络错误 | requests 自己的异常原样抛出，没有重试 |

每次收到响应后，`client.last_call` 是最近一次的情况：

- `API`：这次调用的路由路径，如 `api/list`、`feed.xml`
- `url`：含查询串的最终地址
- `status_code`
- `status`
- `headers`

它在每次请求前会被清空，所以一次请求失败时，它记录的仍是那次失败请求的 URL 与状态码。

```python
from anybooru import Cosine

with Cosine('cosine') as client:
    client.search(q='初音', limit=2)
    print(client.last_call['status_code'], client.last_call['url'])
    # 200 https://pic.cosine.ren/api/search?q=%E5%88%9D%E9%9F%B3&limit=2
    print(client.last_call['headers']['Content-Type'])   # application/json
```

本轮带 `Origin` 头的样本响应都没有 `Access-Control-Allow-Origin`，也都没有 `RateLimit-*`。这只说明本轮这些样本没有这些头，不承诺站点没有配额，也不代表浏览器里能用。

## 媒体地址：只返回字符串，本库不下载

本库没有任何下载媒体的方法，也不替你拼地址。`rawurl` / `thumburl` / `latestImageThumb` 都是响应里原文的字符串，照抄使用。需要字节时用别的工具或你自己的下载代码，并自己检查 `Content-Type` 与实际字节。

已验证的取图形态只有下面这些，都是地址字符串层面的观察：

| 来源 | 本轮样本地址 | 说明 |
| :--- | :--- | :--- |
| Twitter 原图 | `https://pbs.twimg.com/media/HSfnUtFakAAhHtG.jpg?name=orig` | `?name=orig` 是原图，`?name=medium` 是中等图，即 `thumburl` |
| Twitter 无扩展名 | `https://pbs.twimg.com/media/GCbmIUma8AAQ6ok?format=jpg&name=orig` | 路径没有后缀，格式由 `format=jpg` 给出；`thumburl` 是 `format=jpg&name=large` |
| Pixiv 图源直出 | `https://i.pximg.net/img-original/img/2025/09/26/18/12/27/135557027_p0.png` | `/api/list`、`/api/artwork/{id}`、`/api/tag`、`/api/search`、`/api/artist`、`/api/artists` 本轮都给这个主机。路径里的日期时间用 `/` 分段，如 `/2026/08/22/19/31/38/`，不是 `19:31:38` |
| Pixiv 图源，`/api/random` 加工过 | `https://piv.cosine.ren/img-original/img/2024/11/21/22/26/20/124508716_p0.jpg` | 只有 `/api/random` 把主机换掉，并额外给 `originUrl` / `authorUrl` |

两条取图要求来自输入资料与站点前端惯例，本库不实现，本轮也未实测：

- `i.pximg.net` 直接取图通常需要带 `Referer: https://www.pixiv.net/`，否则会被图源拒绝。
- `piv.cosine.ren` 是站点镜像域名，按站点说明免 Referer；`/api/random` 给的就是这个形态。

`https://backblaze.cosine.ren` 只在输入资料里作为原图兜底出现，本轮 4 个样本全是 `404`。本库既不用它，也不用它做兜底。

## 容易踩的坑（本轮都有样本）

1. **四种外壳不统一，失败形态也不统一**：A/B/D 失败是 `{"error": "…"}`，没有 `json` / `success` 键；C 失败是 `{"success": false, "error": "…", "message": "…"}`。取字段前先确认这次是哪一类。
2. **`/api/random` 只有 1 张时 `json` 是对象**，`count=3` 才是数组；数组形态下 `meta.values` 的键带下标。
3. **编号类型不一致**：列表、详情、`tag_images` 里的 `id` 是整数；搜索的 `hits[].id` 是字符串。反查详情前先确认类型，本库不做转换。
4. **非数字编号 / 画师号是 `500`**，如 `artwork_show('abc')`、`artist_images('pixiv', 'abc')`；不存在是 `404`；`page=0` 也是 `500`。
5. **`page` 从 1 开始**：`page=1` 是第一页；`pageSize=0` 回空数组，`pageSize=-1` 回最旧 1 条；超末页是空数组，不是错误。
6. **`search` 的 `total` 被夹到 1000 且是估算**：空 `q`、`platform=` 过滤样本都是 1000。别拿它当真总数或做分页上限；`offset` 超过 1000 会被夹到 1000 并回空 `hits`。
7. **`r18='true'` 选择 R18，`r18='1'` / `'false'` 选择非 R18**：不传才不过滤；被截到 1000 的计数不能用来判断是否过滤。
8. **搜索的 `tags` 用逗号串表达多标签 AND**；`tag_images()` 只接一个完整 `tag`，本轮带 `#` 回空数组。不要把后者的样本外推成搜索 `tags` 带 `#` 的实测结果。
9. **`/api/tags` 的 `count` 不是作品数**，它是对标签关联表计数，且有静态缓存；和 `search(tags=…)` 的 `total`、`tag_images()` 的条数都不等价。
10. **`artist_images(infoOnly=…)` 只有字面量 `'true'` 走资料分支**，`infoOnly=1` 仍返回列表。资料对象的 `author` 可能与作品列表里的 `author` 不同，资料对象也不在四种外壳内。
11. **`search_index_status()` 的 `lastSyncTime` 是假值**，源码给 `new Date()`，即请求时刻。
12. **`feed()` 不是「最新 20 张」，也不是 XML 解析结果**：它是带缓存的 RSS 原文，`lastBuildDate` 与当前数据可能差很久（本轮样本的条目编号与 `/api/list` 最新编号相差一年多）。
13. **站点错误正文是中文短句**，如 `{"error": "未找到该作品"}`。不要按文案分支，按 `http_code`（`e.http_code`）判断更稳；文案本身没有文档承诺。
14. **本库不下载媒体**：`rawurl` / `thumburl` 只是字符串，取图要求由你自己满足。

## 可运行示例

两个脚本都匿名只读，参数来自配置的 `examples.cosine` 段，脚本里没有硬编码站点或查询值：

```bash
python examples/cosine/list_images.py
python examples/cosine/browse_resources.py
```

- `list_images.py`：按配置的 `list_query`，即 `pageSize`，走配置的 `pages` 两页 `image_list()`；再用配置的 `search_query`，即 `q` / `limit` / `platform` / `r18` / `sort`，走两个 `offsets` 的 `search()`；打印每行真实的 `last_call` URL、状态码、`Content-Type` 与关键字段。
- `browse_resources.py`：`artwork_show(配置的 artwork_id)` → `tag_images(配置的 tag, **tag_query)` → `artist_images(**artist_query)` 列表分支 → 同一个画师的 `infoOnly=True` 资料对象；只打印字段，不打印标签正文，不访问任何媒体地址。

两个脚本都显式使用空密钥、不跟随跳转、不重试，请求之间按配置的 `pause_seconds` 停顿。

轻量冒烟 `test/cosine.py` 匿名、只读、最多 10 次请求、不 mock、不进 CI，参数取自 `smoke.cosine`：

```bash
python test/cosine.py --config <你的配置文件>
```

每行输出 `PASS/FAIL`，末尾 `SUMMARY`，失败退出 1。它覆盖 `image_list()` 两页、`artwork_show()` 命中与 `404`、`image_random()` 的 1 张与 3 张、`search()`、`tag_images()`、`tag_list()`、`feed()`，共 10 次匿名 `GET`，不含任何 `POST`。三个脚本的实跑命令、请求数、状态码与退出码写在[验证记录](verification.md#cosine匿名只读实测2026-09-20)，本页不复制。它们覆盖的是用法路径，不等于 13 个方法逐一验证过。

## 边界与未实测

本页的「本轮实测」都只指 2026-09-20 那批匿名只读请求。下面这些没有样本，不要当契约：

- **两个 `POST` 完全没有发过**：`search_index_admin()` 的全部行为，包括它是否真的重建 / 删除索引、未知 `action` 的反应；`artwork_revalidate()` 的成功体、`401`、密钥形态。本轮对 `POST /api/search/admin` 和 `POST /api/artwork/revalidate` 都是零请求。相关形状只有源码只读依据。
- **源码依据的边界**：本页提到的上游代码都是公开仓库里的单个文件，只读，不 clone、不编行号。它不是站点线上部署版本的证明。`POST` 响应形状与密钥校验只有源码依据。画师资料使用 `findFirst` 的说法只来自输入资料，本轮未读该路由源码。
- **顺序与「随机」**：`/api/random` 返回顺序没有保证，样本升序、源码查询无 `orderBy`；`artist_list(sortBy='random')` 本轮只取过一次，没有证明随机性。
- **别名路由没测**：输入资料称 `/rss`、`/rss.xml`、`/feed` 会重写到 `feed.xml`，本轮只请求了 `/feed.xml`，这些别名未实测。`GET /api/search/admin` 以外也没有探测过任何写路由。
- **参数取值没有穷举**：`pageSize` 的正负与 0、`page` 的越界、`count` 的边界、`limit` / `offset` / `total` 的夹取规则、`sort` 的合法取值、`search_suggestions` 的 `limit` 上限、`sortBy` 的未知值回落，都只有单次取值样本（逐条见[验证记录](verification.md#cosine匿名只读实测2026-09-20)）。没有取过的取值不要按样本外推。
- **字段语义未穷尽**：`size` / `guest` / `ai` / `r18` 的写入规则、`title` 对各类来源的确切含义、`create_time` 是入库时间还是发布时间、`searchable_content` / `_formatted` 的生成方式，只有本轮样本层面的观察。
- **媒体**：所有图源主机，包括 `pbs.twimg.com`、`i.pximg.net`、`piv.cosine.ren`、`backblaze.cosine.ren`，本轮一个都没有请求。取图所需的 `Referer` 等要求来自输入资料与站点说明，不是本库的承诺。
- **未实测不等于不存在**：站点数据实时变动。本页的编号、计数、条数，如 4953 / 1708 / 2128 / 255，都只是那一天快照。

继续阅读：[方法参考](cosine-api.md) · [能力入口](cosine-capabilities.md) · [依据与差异](cosine-contract-notes.md) · [验证记录](verification.md#cosine匿名只读实测2026-09-20)。
