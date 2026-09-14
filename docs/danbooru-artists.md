# 按 URL 查画师与 pixiv 作者 ID → tag

Danbooru 的 `Artist` 记录里，`name` 字段就是画师在其作品上使用的 tag；`urls` 是画师的各平台主页
地址。因此“pixiv 作者 ID → tag”的本质是：**用主页 URL 反查 artist，取出它的 `name`**。

## 按 URL 查画师

```python
from pybooru import Danbooru

client = Danbooru('danbooru')
example = client.config['examples']['danbooru']

artists = client.artist_list(search={'url_matches': example['artist_url']})
for artist in artists:
    print(artist['id'], artist['name'])
```

`search[url_matches]` 走的是 `ArtistURL.url_matches`（上游 `app/models/artist.rb`、
`app/models/artist_url.rb`）：传入完整的 `http(s)://` 地址时，站点会把 URL 归一化成规范主页地址
再做匹配，因此 `https://www.pixiv.net/users/27517` 这类 pixiv 主页链接可以直接用；
传普通字符串时则按子串模糊匹配 `artist_urls.url`。

## pixiv 作者 ID → tag

`examples` 段里准备了拼 URL 用的模板与一个作者 ID：

```json
"pixiv_id": 27517,
"pixiv_url_template": "https://www.pixiv.net/users/{pixiv_id}",
"artist_url": "https://www.pixiv.net/users/27517"
```

```python
url = example['pixiv_url_template'].format(pixiv_id=example['pixiv_id'])

artists = client.artist_list(search={'url_matches': url})
tag = artists[0]['name']       # 这个 name 就是帖子上的画师 tag
```

完整可运行脚本：`examples/danbooru/pixiv_id_to_tag.py`。

pixiv 主页链接的几种写法（`/users/<id>`、`/u/<id>`、`/en/users/<id>`、`member.php?id=<id>`）都会被
上游的 URL 解析器归一化成 `https://www.pixiv.net/users/<id>`，见
`danbooru/app/logical/source/url/pixiv.rb`。

## 画师搜索的其他参数

`artist_list(search={...})` 里可用的搜索键（上游 `Artist::SearchMethods#search`）：

| 键 | 说明 |
| :--- | :--- |
| `url_matches` | 按主页 URL 匹配（字符串形式做模糊匹配） |
| `any_name_or_url_matches` | 一个词同时尝试名字与 URL 匹配 |
| `any_name_matches` | 在当前名、其他名、团体名里匹配；支持 `*` 通配与 `/正则/` |
| `name_matches` | 只匹配当前名 |
| `id` | 按 artist ID |
| `is_deleted` / `is_banned` | 是否已删除 / 已封禁 |
| `has_tag` | 是否存在同名 tag |
| `order` | `name`、`updated_at`、`post_count` |

分页参数 `limit` / `page` 走顶层：`client.artist_list(search={...}, limit=20, page=1)`。

## 相关的其他方法

| 方法 | 说明 |
| :--- | :--- |
| `artist_show(artist_id)` | 取单个画师（`GET /artists/<id>.json`） |
| `artist_show_or_new(name='...')` | 按名字查画师：名称已存在时该端点会 302 重定向到画师页面（跟随重定向后仍得到 JSON，已实测），不存在时返回一个尚未保存的 artist 对象 |
| `artist_urls_list(search={'artist_id': ...})` | 列出画师主页地址（`GET /artist_urls.json`），适合反查一个画师有哪些平台账号 |
| `related_tag(search={'query': ...}, ...)` | 相关标签查询（见下） |

## 相关标签

```python
related = client.related_tag(search={
    'query': example['related_query'],
    'category': example['related_category'],
    'order': example['related_order'],
    'search_sample_size': example['search_sample_size'],
    'tag_sample_size': example['tag_sample_size'],
})
```

对应 `GET /related_tag.json`，参数含义（上游 `app/controllers/related_tags_controller.rb`）：

| 搜索键 | 说明 |
| :--- | :--- |
| `query` | 查询用的标签/标签组合（必需） |
| `category` / `categories` | 限定结果标签的分类（数字或名称，`,`/空格分隔多值；`0` 为通用标签） |
| `order` | 排序方式：`frequency`（默认）、`cosine`、`jaccard`、`overlap` |
| `search_sample_size` | 取样帖子数（默认 5000） |
| `tag_sample_size` | 取样标签数（默认 500） |

顶层参数 `limit`（默认 100，上限 1000）与 `media_asset_id` 走 `**params` 传入。

结果是一个**对象**而不是裸列表（上游 `RelatedTagQuery#serializable_hash`）：

| 字段 | 说明 |
| :--- | :--- |
| `query` | 归一化后的查询字符串 |
| `post_count` | 该查询的帖子数 |
| `tag` | 查询命中的标签对象 |
| `related_tags` | 相关标签数组 |
| `wiki_page_tags` | 该标签 wiki 页面里提到的标签数组 |

`related_tags` 里每个元素的字段由站点序列化决定，本库原样返回。

## 完整流程示例

```python
from pybooru import Danbooru

client = Danbooru('danbooru')
example = client.config['examples']['danbooru']

url = example['pixiv_url_template'].format(pixiv_id=example['pixiv_id'])
artists = client.artist_list(search={'url_matches': url, 'is_deleted': False})


artist = artists[0]
print('tag:', artist['name'])

# 用这个 tag 去搜作品
posts = client.post_list(tags=artist['name'], limit=example['limit'])
for post in posts:
    print(post['id'], post['rating'], post['tag_string'])

# 再看与这个 tag 相关的标签
related = client.related_tag(search={'query': artist['name'],
                                    'order': example['related_order']},
                             limit=example['limit'])
for item in related['related_tags']:
    print(item['tag']['name'])
```

## 相关文档

* [danbooru-api.md](danbooru-api.md)：全端点清单
* [danbooru.md](danbooru.md)：`request()` 与参数编码
