# Moebooru 面现状

Moebooru 引擎系站点（如 yande.re、konachan）由 `Moebooru` 类访问。

> **状态说明**：Moebooru 面的 API 方法本轮**未重写**，只把配置加载、会话、参数编码、错误处理
> 换成与 Danbooru 面共享的核心实现。方法签名保持原样，**线上可用性未经验证**。
> 需要严格对齐现役站点的行为时，请以对应站点的 `help/api` 页面与上游
> `moebooru/config/routes.rb`、`app/controllers/` 为准。

## 构造

```python
from pybooru import Moebooru

client = Moebooru('konachan', config_file='pybooru.json')
```

| 参数 | 说明 |
| :--- | :--- |
| `site_name` | `sites` 段的键名，如 `'konachan'`、`'yandere'`；站点条目里的 `url` / `username` / `password` / `hash_string` / `api_version` 按同名字段读入 |
| `site_url` | 显式覆盖站点地址；**自定义地址时必须同时给出 `api_version`**，否则无法确定该用哪种 API 路径 |
| `username` / `password` | 显式覆盖登录凭据（匿名只读时不必填） |
| `hash_string` | 显式覆盖站点加盐模板；匿名访问不必填 |
| `api_version` | 显式覆盖 API 版本 |
| `proxies` | 显式覆盖代理 |
| `config_file` | 配置文件路径，默认当前工作目录的 `pybooru.json` |
| `timeout` / `user_agent` | 显式覆盖超时与 `User-Agent` |

配置结构见 [configuration.md](configuration.md)。

```python
# 只读、匿名
client = Moebooru('yandere')

# 自定义站点：地址与 API 版本都要显式给出
client = Moebooru(site_url='https://example.org', api_version='1.13.0+update.3')
```

## 认证

Moebooru 用 `login` + `password_hash` 放在写请求的表单体里，不用 HTTP Basic：

```
password_hash = SHA1(hash_string.format(password))
```

`hash_string` 与 `username` / `password` 由站点条目提供，客户端在第一次需要登录的请求时计算
`password_hash`。匿名只读请求不带登录字段。细节见 [authentication.md](authentication.md)。

## 与 Danbooru 面的差异

| 项目 | Danbooru 面 | Moebooru 面 |
| :--- | :--- | :--- |
| 通用请求入口 | `request(method, path, *, params, data, files)` | **不提供**；只能调用既有原生方法 |
| 列表方法参数风格 | `xxx_list(search={...}, **params)`，搜索字典编码成 `search[...]` | 保持旧签名，参数按方法自己的 `**params` 或显式参数传递 |
| 认证方式 | HTTP Basic | `login` + `password_hash` 表单字段 |
| API 版本 | 不需要 | `api_version` 决定路径形态（如 `/post/index.json` 与 `/post.json`） |
| 本轮改动 | 按上游路由全面对齐 | **仅共享配置/会话/编码/错误处理** |

## 现有方法

以下方法与当前源码一致，签名未变，**均未做线上验证**：

| 资源 | 方法 |
| :--- | :--- |
| 帖子 | `post_list(**params)`、`post_create(tags, file_=, rating=, source=, rating_locked=, note_locked=, parent_id=, md5=)`、`post_update(post_id, ...)`、`post_destroy(post_id)`、`post_revert_tags(post_id, history_id)`、`post_vote(post_id, score)` |
| 标签 | `tag_list(**params)`、`tag_update(name=, tag_type=, is_ambiguous=)`、`tag_related(**params)` |
| 画师 | `artist_list(**params)`、`artist_create(name, urls=, alias=, group=)`、`artist_update(artist_id, ...)`、`artist_destroy(artist_id)` |
| 评论 | `comment_show(comment_id)`、`comment_create(post_id, comment_body, anonymous=)`、`comment_destroy(comment_id)` |
| Wiki | `wiki_list(**params)`、`wiki_show(**params)`、`wiki_create(title, body)`、`wiki_update(title, new_title=, page_body=)`、`wiki_destroy(title)`、`wiki_lock(title)`、`wiki_unlock(title)`、`wiki_revert(title, version)`、`wiki_history(title)` |
| 笔记 | `note_list(**params)`、`note_search(query)`、`note_history(**params)`、`note_revert(note_id, version)`、`note_create_update(post_id=, coor_x=, coor_y=, width=, height=, is_active=, body=, note_id=)` |
| 用户 / 论坛 | `user_search(**params)`、`forum_list(**params)` |
| 合集 | `pool_list(**params)`、`pool_posts(**params)`、`pool_create(name, description, is_public)`、`pool_update(pool_id, ...)`、`pool_destroy(pool_id)`、`pool_add_post(**params)`、`pool_remove_post(**params)` |
| 收藏 | `favorite_list_users(post_id)` |

写操作（`*_create` / `*_update` / `*_destroy` / `*_delete` / `*_vote` / `*_lock`）需要登录，
权限由站点判断。

## 用法示例

示例脚本从根配置的 `examples.moebooru` 段读取参数：

```python
from pybooru import Moebooru

client = Moebooru('konachan', config_file='pybooru.json')
example = client.config['examples']['moebooru']

posts = client.post_list(tags=example['tags'], page=1, limit=example['limit'])
for post in posts:
    print(post['file_url'])

tags = client.tag_list()
print(tags[0]['name'])
```

可运行脚本见 [../examples/moebooru/](../examples/moebooru/)。

## 后续工作

要把 Moebooru 面也修到与 Danbooru 面同等程度，需要逐步完成：

1. 按 `moebooru/config/routes.rb` 与 `app/controllers/` 逐端点核对现有方法的路由与参数；
2. 为 `post_list` 之类的列表方法统一 `search` 字典语义（Moebooru 的搜索参数是**顶层**参数，
   与 Danbooru 的 `search[...]` 不同，不能照搬）；
3. 补上 Moebooru 独有的端点（如 `post/popular_by_day`、`tag/popular_by_day` 等仅有路由、
   本库尚无对应方法的接口）并去除确认无路由的方法；
4. 用真实站点做匿名只读验证。
