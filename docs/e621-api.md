# e621ng 方法参考

`E621` 有 **18 个原生方法**，全部发 `GET`、全部只读，一个方法对应一条 `/xxx.json` 路由。
下面每个 Python 代码块都能单独复制运行：自带 import 与 `with E621('e621') as client:`，
参数是字面值，注释里给出真实请求地址与真实返回到的字段（条目编号会随站点更新变化，注释中的编号来自
记录在[验证记录](verification.md#anybooru-改名后的复跑2026-09-18)的真实响应）。

客户端怎么构造、认证怎么配、`request()` 与 `last_call` 见[客户端用法](e621.md)；
“我要做某事 → 用哪个方法”见[能力入口](e621-capabilities.md)；上游文件与行号依据见
[契约审计附注](e621-contract-notes.md)。

## 全页通用规则

* **认证**：`username` 或 `api_key` 任一非空就带 HTTP Basic；两项都空是匿名。权限由服务端判定，
  客户端不预判。`related_tag` 与 `related_tag_bulk` 要成员身份，匿名得到 `403`。
* **搜索条件的位置**：列表方法的过滤条件放 `search` 字典，客户端整包编码成 `search[键]=值`；
  帖子三个查询方法（`post_list` / `post_count` / `post_random`）没有 `search`，过滤条件写在顶层 `tags`。
* **搜索键的写法**（上游 `attribute_matches`）：数值与时间收 `5`、`>5`、`5..10`、`5,6,7`；
  布尔收 `true` / `false` / `1` / `0` / `yes` / `no`；文本含 `*` 时按 `LIKE` 通配，否则按 Postgres 全文匹配；
  用户类字段成对出现（`creator_id` / `creator_name`、`linked_user_id` / `linked_user_name`），
  `*_id` 收逗号分隔的多个值。**不在该资源支持范围内的键被服务端静默忽略**，表现为“返回全集”，
  客户端不拦截也不报错。
* **分页**：`page=2` 是页号；`page='b6715096'` 取 id 小于 6715096 的记录，`page='a6715096'` 取 id 大于它的记录，
  两种游标都按 id 从新到旧返回。`limit` 收 `0..320`，不传时每页 75 条（帖子用账号的每页设置）；
  页码越界或 `limit` 非法回 `410`。见 [pagination.md](pagination.md)。
* **评级**：`rating:` 只认首字母 `s` / `q` / `e`（`rating:safe` 等全称也生效）；首字母不在词表里的值被丢弃。
* **失败**：非 2xx 抛 `AnybooruHTTPError`，`http_code` / `url` / `body` / `data` / `response` 都在异常上。
  `404` 正文是 `{"success": false, "reason": "not found"}`；权限不足 `403` 是
  `{"success": false, "reason": "Access Denied"}`；其它预期错误是
  `{"success": false, "message": ..., "code": ...}`。状态码与源码位置见
  [附注](e621-contract-notes.md#sec-errors) 与 [errors.md](errors.md)。

## 帖子（4 个方法）

帖子接口有几种返回结构，由请求参数决定，不是调用者随便挑的开关：

| 你发的请求 | 你拿到什么 | 服务端 JSON |
| :--- | :--- | :--- |
| `post_list(tags='rating:s', limit=2)` | 帖子列表 | `{"posts": [...]}` 里的数组 |
| `post_list(md5='...')` | 一个帖子字典 | `{"post": {...}}` 里的对象 |
| 带 `only='id,rating'` | 帖子列表（或单帖），字段**没有被裁** | 数组/对象本体，没有外层字典 |
| 带 `v2=True` | 帖子列表（或单帖），元素是新结构 | 数组/对象本体 |
| `v2=True, mode='extended'` | 同上，`tags` 变成按类别分组的字典 | 数组/对象本体 |
| `v2=True, mode='thumbnail'` | 同上，换成缩略图用的扁平字段 | 数组/对象本体 |
| `v2=True, mode='basic'`（或其它值） | 同上，`tags` 是标签名字符串数组 | 数组/对象本体 |

默认（旧结构）每条帖子的 25 个键：`id`、`created_at`、`updated_at`、`file`、`preview`、`sample`、
`score`、`tags`、`locked_tags`、`change_seq`、`flags`、`rating`、`fav_count`、`sources`、`pools`、
`relationships`、`approver_id`、`uploader_id`、`uploader_name`、`description`、`comment_count`、
`is_favorited`、`vote`、`has_notes`、`duration`。其中 `file` 是
`{width, height, ext, size, md5, url}`；`preview` 是 `{width, height, url, alt}`；
`sample` 是 `{has, width, height, url, alt, alternates}`；`score` 是 `{up, down, total}`；
`tags` 是九个类别（`general`、`artist`、`contributor`、`copyright`、`character`、`species`、`invalid`、
`meta`、`lore`）到标签名列表的字典；`flags` 是
`{pending, flagged, note_locked, status_locked, rating_locked, deleted}`；`sources` 是链接列表；
`pools` 是合集编号列表；`relationships` 是 `{parent_id, has_children, has_active_children, children}`。

`v2=True` 的 18 个键：`id`、`created_at`、`updated_at`、`change_seq`、`files`、`uploader_id`、
`uploader_name`、`approver_id`、`stats`、`flags`、`has`、`relationships`、`pools`、`rating`、
`locked_tags`、`sources`、`description`、`tags`。其中 `files` 是
`{meta, original, preview, sample[, video]}`；`stats` 是
`{score: {up, down, total}, fav_count, is_favorited, vote, comment_count, hotness}`；
`has` 是 `{parent, children, active_children, notes, sample}`。

### post_list

签名：`post_list(**params)`。路由：`GET /posts.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | `str`，标签与元标签用空格分隔 | 过滤条件；`rating:s`、`wolf`、`order:score`、`score:>10`、`date:2026-09-01..` 都写在这里 | 客户端不发；服务端按最新排序返回全部可见帖子 | `tags='rating:s wolf order:score'` |
| `limit` | `int`，`0..320` | 每页条数 | 客户端不发；服务端用账号每页设置（默认 75） | `limit=2` |
| `page` | `int` 页号，或 `str` 游标 `'a<id>'` / `'b<id>'` | 翻页 | 客户端不发；服务端按第 1 页 | `page=2`、`page='b6715096'` |
| `md5` | `str`，32 位 md5 | 反查单个帖子 | 客户端不发；走普通列表分支 | `md5='b37f8af2b4508efb57cfeb08ef2ef5a1'` |
| `v2` | `bool` 或 `str`；只有字符串 `'true'`（Python `True` 会编码成它）走新结构 | 换成 18 键新结构 | 客户端不发；返回 25 键旧结构 | `v2=True` |
| `mode` | `str`：`'basic'` / `'extended'` / `'thumbnail'`（`'thumbnails'` 同义） | 只对 `v2=True` 生效，选新结构的视图 | 不传或传其它值时走 `basic` 分支（`tags` 是标签名数组） | `v2=True, mode='extended'` |
| `only` | `str`，任意非空值 | 让上游去掉外层字典 | 客户端不发；保留外层字典 | `only='id,rating'` |
| `random` | `bool` | 只影响上游 `PostSets::Post` 的随机状态与页面呈现，**不改查询排序** | 客户端不发 | `random=True` |
| `post` | `dict`，例如 `{'tags': 'rating:s'}` | 嵌套的 `post[tags]`，仅在顶层 `tags` 缺席时被上游读取 | 客户端不发 | `post={'tags': 'rating:s'}` |

```python
from anybooru import E621

with E621('e621') as client:
    posts = client.post_list(tags='rating:s', limit=2)
    # GET https://e621.net/posts.json?tags=rating%3As&limit=2
    # 本轮得到 6715278 与 6715276，都为 rating=s；每项是一个帖子的字段字典。
    # 每条含 file(md5/ext/size/宽高)、score.total、九类 tags。
    for post in posts:
        print(post['id'], post['rating'], post['file']['md5'], post['score']['total'])
        print({name: len(tags) for name, tags in post['tags'].items()})
```

```python
from anybooru import E621

with E621('e621') as client:
    post = client.post_list(md5='b37f8af2b4508efb57cfeb08ef2ef5a1')
    # GET https://e621.net/posts.json?md5=b37f8af2b4508efb57cfeb08ef2ef5a1
    # 2026-09-15 实测：返回单个帖子字典（md5 命中走单帖分支），字段与列表元素同组。
    print(post['id'], post['file']['md5'])
```

```python
from anybooru import E621

with E621('e621') as client:
    posts = client.post_list(tags='rating:s', limit=1, only='id,rating')
    # GET https://e621.net/posts.json?tags=rating%3As&limit=1&only=id%2Crating
    # 2026-09-15 实测：返回列表、没有外层字典，但元素仍是完整 25 键；
    # only 只去掉外层，不是只留 id 和 rating。
    print(len(posts), sorted(posts[0]))
```

```python
from anybooru import E621

with E621('e621') as client:
    posts = client.post_list(tags='rating:s', limit=1, v2=True)
    # GET https://e621.net/posts.json?tags=rating%3As&limit=1&v2=true
    # 2026-09-15 实测：返回列表，元素是 18 键新结构；
    # files 与 stats 是字典，tags 是标签名字符串数组。
    print(sorted(posts[0]))
    print(posts[0]['files']['original']['url'], posts[0]['stats']['score']['total'])
```

```python
from anybooru import E621

with E621('e621') as client:
    second_page = client.post_list(tags='rating:s', limit=2, page=2)
    # GET https://e621.net/posts.json?tags=rating%3As&limit=2&page=2
    # 返回第 2 页列表；结构与第 1 页相同。翻页到更旧的编号用 page='b<id>'，
    # 回到更新的编号用 page='a<id>'（例如 page='b6715093'）。
    print([post['id'] for post in second_page])
```

### post_show

签名：`post_show(post_id, **params)`。路由：`GET /posts/<post_id>.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `post_id` | `int` 帖子编号 | 要读的帖子 | 必填 | `post_show(6715096)` |
| `v2` | `bool` | 换成 18 键新结构 | 客户端不发；返回 25 键旧结构 | `v2=True` |
| `mode` | `str`：`'basic'` / `'extended'` / `'thumbnail'` | 只对 `v2=True` 生效 | 不传或传其它值时走 `basic` 分支 | `v2=True, mode='extended'` |
| `only` | `str`，任意非空值 | 去掉外层字典 | 客户端不发；保留外层字典 | `only='id,rating'` |
| `post_set_id` | `int` | HTML 页面里“当前帖子集合”的上下文 | 客户端不发 | `post_set_id=1` |
| `pool_id` | `int` | HTML 页面里“当前合集”的上下文 | 客户端不发 | `pool_id=54791` |

```python
from anybooru import E621

with E621('e621') as client:
    post = client.post_show(6715096)
    # GET https://e621.net/posts/6715096.json
    # 2026-09-18 实测：返回单个帖子字典（6715096，rating=s），
    # file 含 md5/ext/size/宽高，score.total 为整数。
    print(post['id'], post['rating'], post['file']['ext'], post['score']['total'])
```

`post_set_id` / `pool_id` 会被接受，但只影响 HTML 页面里的上下文，不改变 JSON 返回的字段。

### post_random

签名：`post_random(**params)`。路由：`GET /posts/random.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | `str` | 与 `post_list` 相同的标签/元标签查询 | 客户端不发；服务端在全部可见帖里随机 | `tags='rating:s'` |
| `v2` / `mode` / `only` | 同 `post_show` | 同 `post_show` | 同 `post_show` | `v2=True` |

上游在 `tags` 之后附加 `order:random` 取一条；查询没有匹配时回 `404`。

```python
from anybooru import E621

with E621('e621') as client:
    post = client.post_random(tags='rating:s')
    # GET https://e621.net/posts/random.json?tags=rating%3As
    # 返回一张符合 rating:s 的随机图；本轮编号为 1080816，file.ext 为 jpg。
    print(post['id'], post['rating'], post['file']['ext'])
```

### post_count

签名：`post_count(**params)`。路由：`GET /posts/count.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | `str` | 同 `post_list` 的查询 | 客户端不发；统计全部可见帖子 | `tags='rating:s'` |
| `post` | `dict` | 嵌套 `post[tags]`，顶层 `tags` 缺席时才读 | 客户端不发 | `post={'tags': 'rating:s'}` |

返回 `{'count': ..., 'capped': ...}`：`count` 是命中数，`capped=True` 表示查询撞上了服务端的分页上限，
这时 `count` 只是下限，不是精确总数。

```python
from anybooru import E621

with E621('e621') as client:
    result = client.post_count(tags='rating:s')
    # GET https://e621.net/posts/count.json?tags=rating%3As
    # 2026-09-15 实测：{'count': 240001, 'capped': True}；e621 与 e926 同值。
    print(result['count'], result['capped'])
```

## 标签（2 个方法）

### tag_list

签名：`tag_list(search=None, **params)`。路由：`GET /tags.json`。
返回标签对象列表，每项键为 `id`、`name`、`post_count`、`category`、`related_tags`、
`related_tags_updated_at`、`created_at`、`updated_at`、`is_locked`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['name']` | `str`，逗号分隔的多个标签名 | 精确匹配（先小写化、去首尾空白、空格转下划线） | 客户端不发 | `search={'name': 'anthro,wolf'}` |
| `search['name_matches']` | `str` | 名称模糊匹配；不给 `*` 时按通配处理 | 客户端不发 | `search={'name_matches': 'anthro'}` |
| `search['fuzzy_name_matches']` | `str` | 名称相似度匹配（原样传值，不做归一化） | 客户端不发 | `search={'fuzzy_name_matches': 'anthor'}` |
| `search['category']` | `str`，逗号分隔的数字：`0` general、`1` artist、`2` contributor、`3` copyright、`4` character、`5` species、`6` invalid、`7` meta、`8` lore | 按分类过滤 | 客户端不发 | `search={'category': '1'}` |
| `search['hide_empty']` | 布尔 | 是否隐藏 `post_count` 为 0 的标签 | 服务端**默认隐藏**（`post_count > 0`）；显式传 `false` 才看得到空标签 | `search={'hide_empty': 'false'}` |
| `search['has_wiki']` | 布尔 | 是否要求存在同名 wiki 页面 | 客户端不发 | `search={'has_wiki': 'true'}` |
| `search['has_artist']` | 布尔 | 是否要求存在同名画师记录 | 客户端不发 | `search={'has_artist': 'true'}` |
| `search['is_locked']` | 布尔 | 是否只看被锁定的标签 | 客户端不发 | `search={'is_locked': 'true'}` |
| `search['order']` | `str`：`name` / `similarity` / `id_asc` / `id_desc` / `date` | 排序；`similarity` 需要同时给 `fuzzy_name_matches` | 未规定默认排序；上游按 `post_count` 从多到少 | `search={'order': 'name'}` |
| `limit` / `page` | `int` | 每页条数 / 页号 | 客户端不发；服务端每页 75 条、第 1 页 | `limit=2` |

```python
from anybooru import E621

with E621('e621') as client:
    tags = client.tag_list(limit=2)
    # GET https://e621.net/tags.json?limit=2
    # 本轮得到 anthro(7115) 与 mammal(12054)；每项有 id、name、category、post_count。
    print([(tag['id'], tag['name'], tag['post_count']) for tag in tags])
```

```python
from anybooru import E621

with E621('e621') as client:
    tags = client.tag_list(search={'name_matches': 'anthro', 'category': '0'}, limit=2)
    # GET https://e621.net/tags.json?limit=2&search%5Bname_matches%5D=anthro&search%5Bcategory%5D=0
    # 返回同结构标签列表；category 收字符串或数字，列表里是逗号分隔的多个值。
    print([(tag['name'], tag['category']) for tag in tags])
```

### tag_show

签名：`tag_show(tag_id, **params)`。路由：`GET /tags/<tag_id>.json`。
返回单个标签对象，字段与 `tag_list` 的列表元素相同。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `tag_id` | `int` 标签编号，或 `str` 标签名 | 全数字时按编号查；否则按名称**精确**匹配（大小写、空格不归一化） | 必填 | `tag_show(7115)`、`tag_show('anthro')` |

```python
from anybooru import E621

with E621('e621') as client:
    tag = client.tag_show(7115)
    # GET https://e621.net/tags/7115.json
    # 2026-09-18 实测：7115 anthro（名称分支未实测）。
    print(tag['id'], tag['name'], tag['category'], tag['post_count'])
```

未命中时服务端回 `404`，正文 `{"success": false, "reason": "not found"}`。

## 画师（2 个方法）

### artist_list

签名：`artist_list(search=None, **params)`。路由：`GET /artists.json`。
返回画师对象列表；每项键为 `id`、`name`、`creator_id`、`is_active`、`group_name`、`created_at`、
`updated_at`、`other_names`、`linked_user_id`、`is_locked`、`notes`，并且总是带 `urls` 数组
（元素是画师主页记录，含 `url`）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['name']` | `str` | 名称精确匹配（小写化、空格转下划线） | 客户端不发 | `search={'name': 'panzer_(p.z)'}` |
| `search['group_name']` | `str` | 组名匹配 | 客户端不发 | `search={'group_name': 'studio'}` |
| `search['any_name_matches']` | `str` | 名称或别名匹配（不给 `*` 时按通配处理） | 客户端不发 | `search={'any_name_matches': 'panzer'}` |
| `search['any_other_name_like']` | `str` | 只匹配别名，`LIKE` 写法 | 客户端不发 | `search={'any_other_name_like': '%panzer%'}` |
| `search['any_other_name_matches']` | `str` | 只匹配别名，正则写法 | 客户端不发 | `search={'any_other_name_matches': '^panzer'}` |
| `search['any_name_or_url_matches']` | `str` | 名称或主页地址匹配 | 客户端不发 | `search={'any_name_or_url_matches': 'x.com/panzer'}` |
| `search['url_matches']` | `str` | 主页地址匹配 | 客户端不发 | `search={'url_matches': 'https://x.com/panzer'}` |
| `search['creator_id']` / `search['creator_name']` | `int` / `str` | 创建者 | 客户端不发 | `search={'creator_id': '1'}` |
| `search['linked_user_id']` / `search['linked_user_name']` | `int` / `str` | 关联的站内账号 | 客户端不发 | `search={'is_linked': 'true'}` |
| `search['has_tag']` | 布尔 | 名称是否有对应标签 | 客户端不发 | `search={'has_tag': 'true'}` |
| `search['is_linked']` | 布尔 | 是否已关联站内账号 | 客户端不发 | `search={'is_linked': 'false'}` |
| `search['order']` | `str`：`name` / `updated_at` / `post_count` | 排序 | 未规定默认排序；上游按 `updated_at` 从新到旧 | `search={'order': 'name'}` |
| `name` | `str` | 单个名称；上游把它并进 `search[name]` | 客户端不发 | `name='panzer_(p.z)'` |
| `expiry` | `int`（天） | 允许中间层缓存该响应多久 | 客户端不发 | `expiry=1` |
| `limit` / `page` | `int` | 每页条数 / 页号 | 客户端不发；服务端每页 75 条、第 1 页 | `limit=2` |

```python
from anybooru import E621

with E621('e621') as client:
    artists = client.artist_list(limit=2)
    # GET https://e621.net/artists.json?limit=2
    # 本轮返回 flashyscloset(126813)、scruffasus(126812)，urls 列出各自的主页地址。
    for artist in artists:
        print(artist['id'], artist['name'], [url['url'] for url in artist['urls']])
```

```python
from anybooru import E621

with E621('e621') as client:
    artists = client.artist_list(search={'url_matches': 'https://x.com/miindfang'}, limit=2)
    # GET https://e621.net/artists.json?limit=2&search%5Burl_matches%5D=https%3A%2F%2Fx.com%2Fmiindfang
    # 返回匹配该主页地址的画师列表；url_matches 也接受不以 http 开头的子串。
    print([(artist['id'], artist['name']) for artist in artists])
```

### artist_show

签名：`artist_show(artist_id, **params)`。路由：`GET /artists/<artist_id>.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `artist_id` | `int` 画师编号，或 `str` 画师名 | 全数字按编号查；否则按名称查（小写化、空格转下划线） | 必填 | `artist_show(126799)`、`artist_show('panzer_(p.z)')` |

返回该画师对象，字段同 `artist_list` 的元素，并额外带 `domains`（从作品来源统计出的域名）。

```python
from anybooru import E621

with E621('e621') as client:
    artist = client.artist_show(126799)
    # GET https://e621.net/artists/126799.json
    # 2026-09-18 实测：126799 panzer_(p.z)，带 urls 与 domains。
    print(artist['id'], artist['name'], artist['is_active'], len(artist['urls']))
```

JSON 请求下未知名称回 `404`；同一个未知名称用浏览器访问时会被重定向到新建入口，这是页面行为，与 JSON 无关。

## 评论（2 个方法）

### comment_list

签名：`comment_list(search=None, **params)`。路由：`GET /comments.json`。
默认返回评论对象列表，每项键为 `id`、`created_at`、`updated_at`、`post_id`、`creator_id`、`body`、
`score`、`updater_id`、`do_not_bump_post`、`is_hidden`、`is_sticky`、`warning_type`、`warning_user_id`、
`creator_name`、`updater_name`、`vote`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['id']` | `int` | 按评论编号查 | 客户端不发；会套评分阈值过滤（见下） | `search={'id': '10075334'}` |
| `search['body_matches']` | `str` | 正文匹配；不给 `*` 时按全文检索 | 客户端不发 | `search={'body_matches': 'cute'}` |
| `search['post_id']` | `str`，逗号分隔的帖子编号 | 按帖子过滤 | 客户端不发 | `search={'post_id': '6715096'}` |
| `search['creator_id']` / `search['creator_name']` | `int` / `str` | 评论作者 | 客户端不发 | `search={'creator_name': 'ksharbaugh'}` |
| `search['poster_id']` / `search['poster_name']` | `int` / `str` | **帖子上传者**（不是评论作者） | 客户端不发 | `search={'poster_id': '1'}` |
| `search['post_note_updater_id']` / `search['post_note_updater_name']` | `int` / `str` | 该帖笔记的更新者 | 客户端不发 | `search={'post_note_updater_id': '1'}` |
| `search['is_sticky']` | 布尔 | 是否只看置顶评论 | 客户端不发 | `search={'is_sticky': 'true'}` |
| `search['do_not_bump_post']` | 布尔 | 是否只看“不顶帖”的评论 | 客户端不发 | `search={'do_not_bump_post': 'true'}` |
| `search['order']` | `str`：`post_id` / `score` / `updated_at` 及其 `_desc` 形式 | 排序 | 未规定默认排序；上游按 `created_at` 从新到旧 | `search={'order': 'score'}` |
| `search['advanced_search']` | 布尔 | 正文搜索改用 websearch 语法 | 客户端不发 | `search={'body_matches': 'cute -ugly', 'advanced_search': 'true'}` |
| `search['post_tags_match']` | `str` | 按帖子标签过滤；**需要成员身份** | 客户端不发 | `search={'post_tags_match': 'wolf'}` |
| `search['is_hidden']` | 布尔 | 是否包含隐藏评论；**需要 staff** | 客户端不发 | `search={'is_hidden': 'true'}` |
| `search['ip_addr']` | `str` | 按发表 IP 过滤；**需要 admin** | 客户端不发 | `search={'ip_addr': '1.2.3.4'}` |
| `group_by` | `str`；`'post'` 切换视图，其它值保持评论列表 | `'post'` 时返回帖子对象列表（见下） | 客户端不发；返回评论列表 | `group_by='post'` |
| `tags` | `str` | `group_by='post'` 时的帖子标签查询 | 客户端不发 | `group_by='post', tags='rating:s'` |
| `limit` / `page` | `int` | 每页条数 / 页号；帖子视图固定每页 5 帖 | 客户端不发 | `limit=2` |

可见性：匿名看不到 `is_hidden` 评论与“评论被关闭”帖子的评论；没有 `search={'id': ...}` 时会再套
“置顶或评分不低于账号阈值”的过滤，所以这里拿到的不是全站最新评论，而是达到阈值的可见评论。

```python
from anybooru import E621

with E621('e621') as client:
    comments = client.comment_list(group_by='comment', limit=2)
    # GET https://e621.net/comments.json?group_by=comment&limit=2
    # 本轮得到评论 10075464 / 10075463；每项含 post_id、creator_name、score、body。
    # group_by 传 'comment' 或其它非 'post' 值都返回这个评论列表。
    print([(comment['id'], comment['post_id'], comment['creator_name']) for comment in comments])
```

```python
from anybooru import E621

with E621('e621') as client:
    posts = client.comment_list(group_by='post', tags='rating:s', limit=2)
    # GET https://e621.net/comments.json?group_by=post&tags=rating%3As&limit=2
    # 这条分支返回的是帖子对象列表（帖子表的列，例如 id、rating、tag_string、score），
    # 不包含评论内容，也不是帖子接口的 25 键结构；每页 5 帖。
    print([(post['id'], post['rating'], post['comment_count']) for post in posts])
```

```python
from anybooru import E621

with E621('e621') as client:
    comments = client.comment_list(search={'post_id': '6715096'}, limit=2)
    # GET https://e621.net/comments.json?limit=2&search%5Bpost_id%5D=6715096
    # 返回该帖的评论列表（匿名只含可见评论）；search['post_id'] 也收 '1,2,3' 这样的多个编号。
    print([(comment['id'], comment['score']) for comment in comments])
```

### comment_show

签名：`comment_show(comment_id, **params)`。路由：`GET /comments/<comment_id>.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `comment_id` | `int` 评论编号 | 要读的评论 | 必填 | `comment_show(10075334)` |

```python
from anybooru import E621

with E621('e621') as client:
    comment = client.comment_show(10075334)
    # GET https://e621.net/comments/10075334.json
    # 2026-09-18 实测：返回单个评论字典（10075334），字段与列表元素相同，没有外层字典。
    print(comment['id'], comment['post_id'], comment['creator_name'], len(comment['body']))
```

目标评论对当前身份不可见时回 `403`，编号不存在时回 `404`。

## 合集（2 个方法）

### pool_list

签名：`pool_list(search=None, **params)`。路由：`GET /pools.json`。
返回合集对象列表，每项键为 `id`、`name`、`creator_id`、`description`、`is_active`、`post_ids`（帖子编号列表，
顺序就是合集顺序）、`created_at`、`updated_at`、`category`，外加 `creator_name` 与 `post_count`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['name_matches']` | `str` | 名称匹配；不给 `*` 时按通配处理 | 客户端不发 | `search={'name_matches': 'honeymoon'}` |
| `search['description_matches']` | `str` | 说明匹配 | 客户端不发 | `search={'description_matches': 'september'}` |
| `search['creator_id']` / `search['creator_name']` | `int` / `str` | 创建者 | 客户端不发 | `search={'creator_name': 'example'}` |
| `search['category']` | `str`：`'series'` 或 `'collection'` | 只按类别过滤 | 客户端不发；两类都返回 | `search={'category': 'series'}` |
| `search['is_active']` | 布尔 | 是否只看启用中的合集 | 客户端不发 | `search={'is_active': 'true'}` |
| `search['order']` | `str`：`name` / `created_at` / `post_count` | 排序 | 未规定默认排序；上游按 `updated_at` 从新到旧 | `search={'order': 'post_count'}` |
| `expiry` | `int`（天） | 允许中间层缓存该响应多久 | 客户端不发 | `expiry=1` |
| `limit` / `page` | `int` | 每页条数 / 页号 | 客户端不发 | `limit=2` |

```python
from anybooru import E621

with E621('e621') as client:
    pools = client.pool_list(limit=2)
    # GET https://e621.net/pools.json?limit=2
    # 本轮得到合集 47696 / 59192，category 均为 series，post_count 分别为 20 / 4。
    print([(pool['id'], pool['category'], pool['post_count']) for pool in pools])
```

```python
from anybooru import E621

with E621('e621') as client:
    series_pools = client.pool_list(search={'category': 'series', 'is_active': 'true'}, limit=2)
    # GET https://e621.net/pools.json?limit=2&search%5Bcategory%5D=series&search%5Bis_active%5D=true
    # 返回类别为 series 且启用中的合集列表，字段同上。
    print([(pool['id'], pool['name']) for pool in series_pools])
```

### pool_show

签名：`pool_show(pool_id, **params)`。路由：`GET /pools/<pool_id>.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `pool_id` | `int` 合集编号 | 要读的合集 | 必填 | `pool_show(54791)` |
| `page` / `limit` | `int` | 只影响 HTML 页面的帖子分页，不改变 JSON 返回 | 客户端不发 | `pool_show(54791, limit=2)` |

```python
from anybooru import E621

with E621('e621') as client:
    pool = client.pool_show(54791)
    # GET https://e621.net/pools/54791.json
    # 2026-09-18 实测：返回单个合集字典；post_ids 是帖子编号列表，顺序即合集顺序。
    print(pool['id'], pool['name'], len(pool['post_ids']), pool['post_ids'][:3])
```

## 笔记（2 个方法）

### note_list

签名：`note_list(search=None, **params)`。路由：`GET /notes.json`。
返回笔记对象列表，每项键为 `id`、`creator_id`、`post_id`、`x`、`y`、`width`、`height`、`is_active`、
`body`、`created_at`、`updated_at`、`version`，外加 `creator_name`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['id']` | `int` | 按笔记编号查 | 客户端不发 | `search={'id': '506654'}` |
| `search['body_matches']` | `str` | 正文匹配 | 客户端不发 | `search={'body_matches': 'translation'}` |
| `search['is_active']` | 布尔 | 是否只看启用中的笔记 | 客户端不发 | `search={'is_active': 'true'}` |
| `search['post_id']` | `str`，逗号分隔的帖子编号 | 按帖子过滤 | 客户端不发 | `search={'post_id': '6715096'}` |
| `search['creator_id']` / `search['creator_name']` | `int` / `str` | 创建者 | 客户端不发 | `search={'creator_name': 'example'}` |
| `search['post_note_updater_id']` / `search['post_note_updater_name']` | `int` / `str` | 该帖笔记的更新者 | 客户端不发 | `search={'post_note_updater_id': '1'}` |
| `search['order']` | `str`：`id_asc` / `id_desc` | 排序 | 未规定默认排序；上游按 `id` 从大到小 | `search={'order': 'id_asc'}` |
| `search['post_tags_match']` | `str` | 按帖子标签过滤；**需要成员身份** | 客户端不发 | `search={'post_tags_match': 'wolf'}` |
| `limit` / `page` | `int` | 每页条数 / 页号 | 客户端不发 | `limit=2` |

```python
from anybooru import E621

with E621('e621') as client:
    notes = client.note_list(limit=2)
    # GET https://e621.net/notes.json?limit=2
    # 本轮返回笔记 506657 / 506656，分别属于帖子 6714984 / 6714983；x、y、width、height 是图上的位置与大小。
    for note in notes:
        print(note['id'], note['post_id'], note['x'], note['y'], note['width'], note['height'])
```

### note_show

签名：`note_show(note_id, **params)`。路由：`GET /notes/<note_id>.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `note_id` | `int` 笔记编号 | 要读的笔记 | 必填 | `note_show(506654)` |

```python
from anybooru import E621

with E621('e621') as client:
    note = client.note_show(506654)
    # GET https://e621.net/notes/506654.json
    # 2026-09-18 实测：返回单个笔记字典；body 是笔记正文，坐标为像素值。
    print(note['id'], note['post_id'], note['is_active'], len(note['body']))
```

## wiki 页面（2 个方法）

### wiki_page_list

签名：`wiki_page_list(search=None, **params)`。路由：`GET /wiki_pages.json`。
返回页面对象列表，每项键为 `id`、`creator_id`、`title`、`body`、`is_locked`、`created_at`、`updated_at`、
`updater_id`、`other_names`、`is_deleted`、`parent`、`featured_posts`，外加 `creator_name` 与
`category_id`（页面标题对应不到标签时为 `null`）。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['title']` | `str` | 标题匹配（`*` 通配；上游会小写化并把空格转下划线） | 客户端不发 | `search={'title': 'toriel'}` |
| `title` | `str` | 单个标题，上游把它并进 `search[title]` | 客户端不发 | `title='toriel'` |
| `search['body_matches']` | `str` | 正文匹配 | 客户端不发 | `search={'body_matches': 'translation'}` |
| `search['other_names_match']` | `str` | 别名匹配 | 客户端不发 | `search={'other_names_match': 'undertale'}` |
| `search['other_names_present']` | 布尔 | 是否只看有别名或没有别名的页面 | 客户端不发 | `search={'other_names_present': 'true'}` |
| `search['parent']` | `str` | 父页面标题（重定向页用） | 客户端不发 | `search={'parent': 'undertale'}` |
| `search['creator_id']` / `search['creator_name']` | `int` / `str` | 创建者 | 客户端不发 | `search={'creator_name': 'example'}` |
| `search['is_locked']` / `search['is_deleted']` | 布尔 | 是否只看锁定 / 已删除页面 | 客户端不发 | `search={'is_locked': 'true'}` |
| `search['hide_deleted']` | 布尔 | 是否隐藏已删除页面 | 客户端不发 | `search={'hide_deleted': 'true'}` |
| `search['order']` | `str`：`title` / `post_count` | 排序 | 未规定默认排序；上游按 `updated_at` 从新到旧 | `search={'order': 'title'}` |
| `expiry` | `int`（天） | 允许中间层缓存该响应多久 | 客户端不发 | `expiry=1` |
| `limit` / `page` | `int` | 每页条数 / 页号 | 客户端不发 | `limit=2` |

```python
from anybooru import E621

with E621('e621') as client:
    pages = client.wiki_page_list(limit=2)
    # GET https://e621.net/wiki_pages.json?limit=2
    # 本轮返回页面 110139 foxxsnow 与 112153 uzula_(pelleelle)，category_id 均为 4。
    print([(page['id'], page['title'], page['category_id']) for page in pages])
```

### wiki_page_show

签名：`wiki_page_show(title_or_id, **params)`。路由：`GET /wiki_pages/<title_or_id>.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `title_or_id` | `int` 页面编号，或 `str` 标题 | 全数字按编号查；否则按标题查（小写化、空格转下划线） | 必填 | `wiki_page_show('help:api')`、`wiki_page_show(11224)` |

标题里的冒号等字符由客户端转义，所以 `'help:api'` 直接传即可，发出的地址是
`/wiki_pages/help%3Aapi.json`；未命中回 `404`。

```python
from anybooru import E621

with E621('e621') as client:
    page = client.wiki_page_show('help:api')
    # GET https://e621.net/wiki_pages/help%3Aapi.json
    # 2026-09-18 实测：返回页面 11224 help:api，is_locked=true，category_id 为 null
    # （该标题没有对应标签）。
    print(page['id'], page['title'], page['is_locked'], page['category_id'])
```

站点上的 `/help/api` 是另一个资源（`help_pages` 路由下的 HelpPage，字段是 `name`、`wiki_page`、
`title`、`related`），本库没有为它封方法；需要时用 `request('GET', 'help/api')` 自己取。

## 相关标签（2 个方法，需要成员身份）

两个方法在上游控制器级就要求成员身份，匿名请求回 `403`（实测正文
`{"success": false, "reason": "Access Denied"}`）。成员身份需要凭据，本轮**没有成功响应记录**，
下面的返回结构来自上游查询对象源码。

### related_tag

签名：`related_tag(search=None, **params)`。路由：`GET /related_tag.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `search['query']` | `str` | 一个标签名，或含 `*` 的通配查询 | 上游把空查询当作“无相关标签” | `search={'query': 'wolf'}` |
| `search['category_id']` | `int` 或 `str` | 把计算限制到某个标签分类（`0` general、`1` artist、`3` copyright、`4` character、`5` species） | 不传时按全部标签计算 | `search={'query': 'wolf', 'category_id': 0}` |
| `limit` | `int` | 路由接受该参数，但控制器总是返回自己的结果集 | 客户端不发 | `limit=10` |

返回 `[{"name": ..., "category_id": ...}]`；通配查询走另一分支，按 post_count 取前 50 个匹配标签，
输出再按名称排序。

```python
from anybooru import E621

with E621('e621') as client:
    related = client.related_tag(search={'query': 'wolf', 'category_id': 0})
    # GET https://e621.net/related_tag.json?search%5Bquery%5D=wolf&search%5Bcategory_id%5D=0
    # 2026-09-15 匿名实测：403，AnybooruHTTPError，data 为
    # {"success": false, "reason": "Access Denied"}。成员成功路径未实测。
    print([(item['name'], item['category_id']) for item in related])
```

### related_tag_bulk

签名：`related_tag_bulk(query, category_id=None)`。路由：`GET /related_tag/bulk.json`。

| 参数 | 类型与取值 | 含义 | 不传时怎样 | 字面例子 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | `str`，空格分隔的标签名 | 每个标签各算一组相关标签；上游最多取前 25 个 | 必传；空白查询返回 `{}` | `related_tag_bulk('wolf canine')` |
| `category_id` | `int` 或 `str` | 把计算限制到某个标签分类 | 不传时按全部标签计算 | `related_tag_bulk('wolf', category_id=0)` |

返回以标签名为键的字典，值是 `[{"name": ..., "count": ..., "category_id": ...}]` 列表。

```python
from anybooru import E621

with E621('e621') as client:
    related = client.related_tag_bulk('wolf', category_id=0)
    # GET https://e621.net/related_tag/bulk.json?query=wolf&category_id=0
    # 匿名请求回 403（与 related_tag 同一成员门槛）；成员成功路径未实测，
    # 返回结构取自上游查询对象源码。
    print({name: len(items) for name, items in related.items()})
```

## 边界与未实测

* 已记录的调用覆盖：`post_list`（默认列表、`md5`、`only`、`v2`）、`post_show`、`post_random`、
  `post_count`、`tag_list`、`tag_show`、`artist_list`、`artist_show`、`comment_list`、`comment_show`、
  `pool_list`、`pool_show`、`note_list`、`note_show`、`wiki_page_list`、`wiki_page_show`（以上匿名 `200`），
  以及 `related_tag` 的匿名 `403`。逐条命令、URL 与状态码见
  [验证记录](verification.md#anybooru-改名后的复跑2026-09-18)。
* 本轮按字面执行了所有匿名代码块，包括第二页、标签/画师过滤、评论按帖子分组、合集过滤和不存在图片的 404；
  两个相关标签方法仍需成员权限，**未执行成员成功示例**。
* **未实测**：`related_tag_bulk`、两种成员成功响应、v2 的 extended/thumbnail、按名称查标签/画师、
  `safe_mode`、旧式单数路径与本页未演示的参数组合。没有写请求，也没有申请或使用凭据登录。
* 表格与索引里的其它单行调用没有全部执行；只有验证记录中点名的调用属于已实测。
* `limit` 的 `0..320`、编号页 `750` 上限与游标边界只有源码与 `410` 分支依据，没有逐值探测。

继续阅读：[客户端用法](e621.md) · [能力入口](e621-capabilities.md) ·
[契约审计附注](e621-contract-notes.md) · [错误处理](errors.md) · [分页](pagination.md)。
