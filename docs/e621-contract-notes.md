# e621ng 契约审计附注

面向维护者与契约核对者。使用者页面（[客户端用法](e621.md)、[方法参考](e621-api.md)、
[能力入口](e621-capabilities.md)）只保留可操作的事实；上游行号、权限过滤器、源码与部署的差异、
排除项与逐条状态记在这里。

**审计依据**：上游仓库 <https://github.com/e621ng/e621ng>，固定快照
[`7a9c98851`](https://github.com/e621ng/e621ng/tree/7a9c98851)。本文所有 `路径:行号` 都相对该 commit，
上游更新后需重新核对。权威顺序是 `config/routes.rb`（路由）→ `app/controllers/*`（动作、过滤器与强参数）
→ `app/blueprints/*.rb` 与 `app/models/*`（序列化、搜索、校验）→ `config/danbooru_default_config.rb`（默认值）。
客户端侧依据是 `pybooru/api_e621.py`（`E621Api_Mixin`，18 个原生方法）与 `pybooru/e621.py`（客户端与
`request()`）。

**目录形态与 Danbooru 不同**：e621ng **没有** `app/policies/` 与 `app/serializers/`。权限过滤器定义在
`app/controllers/application_controller.rb`（`define_method`），帖子序列化在 `app/blueprints/*.rb`。
`/help/api` 这条路径属于 `help_pages` 路由而不是 wiki（下文单列）。

## 状态口径与总量

* 客户端原生方法 **18 个**，全部是 `GET` 只读，方法体内各调用一次 `E621.request(...)`。
* **已实测（匿名只读，2026-09-15，`e621.net` 与 `e926.net`）**：
  * 三个示例脚本逐站运行 **6 次、30 次调用全部 `200` 且退出码 `0`**：`post_list`、`post_show`、
    `post_random`、`tag_list`、`tag_show`、`artist_list`、`artist_show`、`comment_list`、`comment_show`、
    `pool_list`、`pool_show`、`note_list`、`note_show`、`wiki_page_list`、`wiki_page_show`（15 个方法 × 2 站）；
  * 返回形态复核 **7 次调用**：两个站点的 `post_count`（`200`，`{"count": 240001, "capped": true}`）、
    原始 `posts` 信封（`200`）、`md5` 单帖分支（`200`）、`only` 拆信封分支（`200`）、
    `v2=true` 新蓝图分支（`200`）、`related_tag` 匿名（`403`）；
  * 命令、URL、状态码与响应摘要在 [verification.md](verification.md)。
* **源码对齐、未实测**：`related_tag` 与 `related_tag_bulk` 的**成员成功路径**（未配置认证凭据）；
  `v2=true` 的 `mode=extended` / `mode=thumbnail` 两个视图；全部写路径、staff 面与只读扩展
  路由。`related_tag_bulk` 没有任何线上调用（连失败响应也没有）。
* 「已实测」只覆盖当时那次调用用到的参数组合；同一方法换参数、换身份、换站点都不算已验证。
  匿名 `403` 只是权限边界的证据，不是成功路径。

<a id="sec-methods"></a>

## 逐方法：路由与状态（18 个原生方法）

路由行号取自 `config/routes.rb`；控制器行号指该动作与其 JSON 分支。

| 方法 | 路由（`GET`） | routes.rb | 控制器 | 匿名 | 返回形态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `post_list(**params)` | `posts.json` | 339（集合 344-347） | `posts#index` 11-62 | 是（过滤器例外清单在 6、8） | 默认 `{"posts": [...]}` 拆成数组；`md5` 命中拆 `post`；`only` / `v2=true` 不拆 |
| `post_show(post_id, **params)` | `posts/<id>.json` | 339 | `posts#show` 77-104 | 是 | `{"post": {...}}` 拆成对象；`only` / `v2=true` 不拆 |
| `post_random(**params)` | `posts/random.json` | 344-347 | `posts#random` 171-181 | 是 | 同 `post_show`；无匹配 `404` |
| `post_count(**params)` | `posts/count.json` | 344-347 | `posts#count` 64-75 | 是 | `{"count": N, "capped": bool}`（内联，无信封） |
| `tag_list(search=None, **params)` | `tags.json` | 392 | `tags#index` 8-12 | 是 | tag 对象数组 |
| `tag_show(tag_id, **params)` | `tags/<id>.json` | 392 | `tags#show` 14-21 | 是 | tag 对象；数字按 id、否则按名称，未命中 `404` |
| `artist_list(search=None, **params)` | `artists.json` | 209 | `artists#index` 11-30（JSON 分支 23-29） | 是（7） | artist 对象数组，含 `urls` |
| `artist_show(artist_id, **params)` | `artists/<id>.json` | 209 | `artists#show` 32-56 | 是（7） | artist 对象，含 `urls` 与 `domains` |
| `comment_list(search=None, **params)` | `comments.json` | 229 | `comments#index` 13-19 → 105-113 / 115-141 | 是（7，`skip_before_action :api_check` 在 11） | `CommentBlueprint` 数组；`group_by=post` 时是裸帖子对象数组 |
| `comment_show(comment_id, **params)` | `comments/<id>.json` | 229 | `comments#show` 21-26 | 是（7） | 单个 `CommentBlueprint`，无信封；不可见 `403` |
| `pool_list(search=None, **params)` | `pools.json` | 311 | `pools#index` 9-17 | 是（5） | pool 对象数组（含 `creator_name`、`post_count`） |
| `pool_show(pool_id, **params)` | `pools/<id>.json` | 311 | `pools#show` 19-26 | 是（5） | pool 对象 |
| `note_list(search=None, **params)` | `notes.json` | 302 | `notes#index` 10-15 | 是（5） | note 对象数组（含 `creator_name`） |
| `note_show(note_id, **params)` | `notes/<id>.json` | 302 | `notes#show` 17-22 | 是（5） | note 对象 |
| `wiki_page_list(search=None, **params)` | `wiki_pages.json` | 451 | `wiki_pages#index` 9-26 | 是（5） | wiki 页面数组（含 `creator_name`、`category_id`） |
| `wiki_page_show(title_or_id, **params)` | `wiki_pages/<id>.json` | 451 | `wiki_pages#show` 28-45 | 是（5） | wiki 页面对象；数字按 id、否则 `WikiPage.titled`（56-58），未命中 `404` |
| `related_tag(search=None, **params)` | `related_tag.json` | 382 | `related_tags#show` 8-16 | **否** | 成员：`[{"name", "category_id"}]`；匿名 `403` |
| `related_tag_bulk(query, category_id=None)` | `related_tag/bulk.json` | 383 | `related_tags#bulk` 18-24 | **否** | 成员：`{tag => [{"name", "count", "category_id"}]}`；匿名 `403` |

两条相关标签路径的 `member_only` 是控制器级全局过滤器（`related_tags_controller.rb:6`），所以失败先于参数
解析。`routes.rb:382` 的 `resource :related_tag, only: %i[show update]` 另外登记了 `PUT /related_tag`，
但控制器没有 `update` 动作，该动词只会落进错误页，属应排除的动词。`related_tag` 的动作直接索引
`params[:search][:query]`（9 行），不带 `search` 会触发未捕获异常；`bulk` 读顶层 `query` / `category_id`（18-19）。

<a id="sec-post-shapes"></a>

## 帖子形状：唯一权威分支

形状由**请求参数**决定，不能写死 `v2=false`：

| 输入 | 生效处 | 结果 |
| :--- | :--- | :--- |
| 无 `md5`，且 `only` 为空、未给 `v2=true` | `posts_controller.rb:56-58` → `json_response_helper.rb:39-42` | `PostLegacyBlueprint` + `{"posts": [...]}` |
| 同上但带 `only=`（任意非空值） | `json_response_helper.rb:13-15` | 同一份 legacy 哈希**直接输出**，无信封，且**不裁剪字段** |
| `md5=<非空字符串>` | `posts_controller.rb:12-21`（`pick_json_format(..., collection: false)` 在 18） | `Post.find_by!(md5:)`；未命中 `404`；默认 `{"post": {...}}` |
| `v2=true` | `json_response_helper.rb:44-56` | 新蓝图**永不包信封**（集合=数组） |
| `v2=true&mode=extended` | `json_response_helper.rb:49-50` | `PostBlueprint` `view: :extended`，`tags` 是九类字典 |
| `v2=true&mode=thumbnail` / `thumbnails` | `json_response_helper.rb:47-48` | `PostThumbnailBlueprint` |
| `v2=true&mode=<其它>` | `json_response_helper.rb:51-52` | `PostBlueprint` `view: :basic`，`tags` 是标签名数组 |

配套事实：`v2` 只有精确字符串 `"true"` 才走新格式；`mode` 在 legacy 分支完全被忽略；`only` 在新格式分支
被忽略；该帖子的 JSON 分支使用 `only` 时只去掉信封，不做字段筛选（`json_response_helper.rb:13-20`）。
本仓库自带的请求规格也锚定了这些分支：`spec/requests/posts_controller_spec.rb`（`v2` 断言从 33 行起、
`md5` 从 70 行起、`count` 从 113 行起）。

蓝图字段（可对照实测负载）：

* `PostLegacyBlueprint`（`app/blueprints/post_legacy_blueprint.rb:6-134`，实测 25 键）：`id`、`created_at`、
  `updated_at`、`file`（14-27：`width`、`height`、`ext`、`size`、`md5`、`url`）、`preview`（29-41）、
  `sample`（43-57）、`score`（59-65：`up`、`down`、`total`）、`tags`（67-73：按 `TagCategory::REVERSE_MAPPING`
  输出九类）、`locked_tags`（75-77）、`change_seq`（79）、`flags`（81-90）、`rating`、`fav_count`（92）、
  `sources`（94-96）、`pools`（98-100）、`relationships`（102-109）、`approver_id`、`uploader_id`、
  `uploader_name`、`description`（111）、`comment_count`（113-115）、`is_favorited`（117-119）、
  `vote`（121-123）、`has_notes`（125-127）、`duration`（129-131）。
* `PostBlueprint`（`app/blueprints/post_blueprint.rb:6-154`，实测 v2 basic 18 键）：`files`（16-67）、
  `stats`（73-83）、`flags`（85-94）、`has`（96-104）、`relationships`（106-111）、`pools`、`rating`、
  `locked_tags`、`sources`、`description`，以及 `view :basic` 的 `tags`（136-140，标签名字符串数组）与
  `view :extended` 的 `tags`（143-149，九类字典）。
* `PostThumbnailBlueprint`（`app/blueprints/post_thumbnail_blueprint.rb:5-63`）：扁平字段，
  `flags`/`pools`/`tags` 都是字符串。
* `CommentBlueprint`（`app/blueprints/comment_blueprint.rb:6-26`，16 键）由控制器显式渲染
  （`comments_controller.rb:139` 列表、`145` 单条）。
* 其它资源走模型默认 `as_json`：`ApplicationRecord::ApiMethods`（`app/models/application_record.rb:188-212`）
  统一剔除 IP 列（`hidden_attributes` 在 206）并追加 `method_attributes`（210）。各资源附加字段：
  `Pool` 加 `creator_name`、`post_count`（`app/models/pool.rb:357-359`），`Note` 加 `creator_name`
  （`app/models/note.rb:58-60`），`WikiPage` 加 `creator_name`、`category_id`
  （`app/models/wiki_page.rb:133-135`），`Comment` 加 `creator_name`、`updater_name`（`comment.rb:337-339`），
  `Artist` 的 JSON 由控制器 `include: [:urls]`（`artists_controller.rb:23-29`，该键在 26 行）与
  `methods: [:domains]`（55）补足。列集见 `db/structure.sql`（`tags` 9 列、`artists` 10 列、`comments` 15 列、
  `pools` 9 列、`notes` 13 列、`wiki_pages` 12 列、`help_pages` 7 列）。

帖子负载与可见性强相关，而且要区分两条序列化路径：

* **模型序列化**（`as_json`）：`Post#hidden_attributes`（`app/models/post.rb:1894-1900`）在帖子不可见时
  额外隐藏 `md5`、`file_ext` 与 `pool_ids` 三个键，`method_attributes`（1902-1908）只在可见时补
  `file_url`、`sample_url`、`preview_file_url`。
* **`/posts.json` 的 legacy 蓝图**：不复用上面那层，`file.md5` / `file.ext` 仍取自模型；只有 `file.url`、
  `preview.url` / `preview.alt`、`sample.url` / `sample.alt` 在 `post.visible?` 为假时保持初始的 `null`
  （键始终存在，`app/blueprints/post_legacy_blueprint.rb:14-57`）。

所以「不可见」在 posts 负载里的表现是**键在、值为空**，而不是键被删掉；v2 蓝图同理，只在
`post.visible?` 为真时填 `files.original.url` 等 URL（`app/blueprints/post_blueprint.rb:16-67`）。

<a id="sec-client"></a>

## 客户端侧实现契约

`pybooru/e621.py` 与 `pybooru/api_e621.py` 只做三件与上游一一对应的事，其余原样透传：

* **分支判定**：`_unwrapped(params)` 对应两处上游条件——`params[:only].present?`（`json_response_helper.rb:14`）
  与控制器传入的 `legacy: params[:v2] != "true"`（`posts_controller.rb:18`、`57`、`101`、`180`，取值后再由
  `pick_json_format` 在 39-42 / 44-56 分流）；其中「present」按 Rails 的 `blank?` 语义实现（`None`、空白
  字符串、空集合都算不 present）。`_md5_lookup(params)` 对应 `posts_controller.rb:12-13`（非字符串 `md5`
  被置 `nil`，再按 `present?` 分支）。判定结果只决定 `envelope` 传哪个键，本身不改请求。
* **信封拆封**：`envelope` 只接受一个键名，方法内按上面的判定写死 `posts` / `post` / 不拆；缺键直接
  `KeyError`，不做形状搜索或后备键——上游分支与返回值一一对应，不引入第二套猜测规则。
* **参数组装**：`_search(search, params)` 把搜索字典整包放进 `search`（对应 `search_params` 的
  `params.fetch(:search, {})`）；`_segment(value)` 用 `quote(str(value), safe="")` 转义单个路径段
  （对应 `tags` / `artists` / `wiki_pages` 上的 `id_name_constraint`，`config/routes.rb:3`，id 段不允许含
  `/`）；`request()` 负责补 `.json`、
  去掉开头 `/`、把布尔落成小写字符串、省略 `None`，并在 `username` 或 `api_key` 非空时才加 Basic 头。

<a id="sec-search"></a>

## 搜索字段（逐资源）

列表方法的搜索键都在 `search[...]` 里；帖子三个查询方法用顶层 `tags`（`posts_controller.rb:57`、
`posts#count` 的 `tag_query` 在 198-202）。**未知键被静默忽略**，表现为返回全集。

| 资源 | 允许的搜索键 | 源码 |
| :--- | :--- | :--- |
| tags | `id`、`created_at`、`updated_at`（基类）、`fuzzy_name_matches`、`name_matches`、`name`、`category`、`hide_empty`、`has_wiki`、`has_artist`、`is_locked`、`order` | `app/models/tag.rb:345-397`（`hide_empty` 默认行为在 365-367，order 分支 383-394） |
| artists | `id`、`created_at`、`updated_at`、`name`、`group_name`、`any_name_matches`、`any_other_name_like`、`any_other_name_matches`、`any_name_or_url_matches`、`url_matches`、`creator_id` / `creator_name`、`linked_user_id` / `linked_user_name`、`has_tag`、`is_linked`、`order` | `app/models/artist.rb:455-514`（order 分支 502-511）；顶层 `name` 由控制器并进 `search[name]`（`artists_controller.rb:120-124`） |
| comments | `id`、`created_at`、`updated_at`、`body_matches`、`post_id`、`creator_id` / `creator_name`、`poster_id` / `poster_name`、`post_note_updater_id` / `post_note_updater_name`、`is_sticky`、`do_not_bump_post`、`order`、`advanced_search`；成员另可 `post_tags_match`，staff 另可 `is_hidden`，admin 另可 `ip_addr` | 控制器白名单 `comments_controller.rb:162-168`；过滤实现 `app/models/comment.rb:103-182`（order 分支 161-175，`poster_*` 过滤在 177-181） |
| pools | `id`、`created_at`、`updated_at`、`name_matches`、`description_matches`、`creator_id` / `creator_name`、`category`、`is_active`、`order` | `app/models/pool.rb:63-94`（order 分支 82-91） |
| notes | `id`、`created_at`、`updated_at`、`body_matches`、`is_active`、`post_id`、`creator_id` / `creator_name`、`post_note_updater_id` / `post_note_updater_name`、`order`；成员另可 `post_tags_match` | 控制器白名单 `notes_controller.rb:66-72`；过滤实现 `app/models/note.rb:33-55` |
| wiki_pages | `id`、`created_at`、`updated_at`、`title`、`body_matches`、`other_names_match`、`other_names_present`、`parent`、`creator_id` / `creator_name`、`is_locked`、`is_deleted`、`hide_deleted`、`order` | `app/models/wiki_page.rb:89-129`（order 分支 119-126）；顶层 `title` 由控制器搬进 `search[title]`（`wiki_pages_controller.rb:121-126`） |

键的取值语义集中在 `ApplicationRecord` 的 `attribute_matches`（`app/models/application_record.rb:35-49`）：
数值/时间收 `5`、`>5`、`5..10`、`5,6,7`，布尔按 truthy/falsy 字符串，文本含 `*` 走 `LIKE`、否则走
`to_tsvector` 全文；用户类字段由 `with_resolved_user_ids`（111-130）与 `where_user`（134-141）处理，
`*_id` 收逗号列表并按 `max_per_page` 截断。

**白名单机制不一致**：`tags#index`、`pools#index`、`wiki_pages#index` 直接用
`ApplicationController#search_params`（`application_controller.rb:379-381`，`permit!`，不校验键），
`artists#index` 自己覆写也是 `permit!`（`artists_controller.rb:120-124`）；
而 `comments#index`（`comments_controller.rb:162-168`）与 `notes#index`（`notes_controller.rb:66-72`）走
`permit_search_params`（383-386，白名单加「只留标量」）。评论白名单里的 `poster_id` / `poster_name` 不是
评论者，而是**帖子上传者**：`Comment.search` 用 `where_user(:"posts.uploader_id", :poster, params)`
（`app/models/comment.rb:177-181`）把它接到帖子的 `uploader_id` 上。

**空值会被重定向**：`normalize_search`（346-377）对所有 `GET`/`HEAD` 请求剔除空白 `search` 项（含嵌套），
只要有东西被剔掉就 `302` 到清理后的地址（`wiki_pages#index` 另有 `normalize_search_params` 把顶层 `title`
搬进 `search[title]`，`wiki_pages_controller.rb:121-126`）。

<a id="sec-permissions"></a>

## 权限与可见性

* **认证**（`app/logical/session_loader.rb`）：无凭据即 `User.anonymous`（`load` 22-48）；`Basic` 头经
  `authenticate_basic_auth`（170-185）按第一个 `:` 切出 `login` / `api_key`；也接受参数式
  `login` + `api_key`（160-168），但那条路径要同源请求才跳过 CSRF（`application_controller.rb:23-27`），
  本库不使用；`Bearer` 是 OAuth（84-118），需要部署启用 provider。
* **过滤器**：`member_only`、`staff_only`、`admin_only` 等由 `UserLevel::ROLES` 循环 `define_method`
  生成（`application_controller.rb:289-305`），实际是「该等级及以上」；匿名不满足 `is_member?`，
  失败统一走 `access_denied`（219-240）。
* **两条相关标签路径**整体 `member_only`（`related_tags_controller.rb:6`），所以 18 个方法里有 2 个匿名不可达；
  上游规格也断言匿名 `403`（`spec/requests/related_tags_controller_spec.rb`，27 与 102 行附近）。
* **评论可见性**（`app/models/comment.rb`）：`accessible`（51-74）对匿名只保留 `is_hidden = false` 且
  帖子未被关闭评论的记录；`is_accessible?`（205-219）是同一规则的单条版本；列表在未给 `search[id]` 时再套
  `above_threshold`（80-82）：`is_sticky = true OR score >= 用户阈值`。匿名账号的 `comment_threshold`
  默认是 `-2`（`db/structure.sql` 的 `users.comment_threshold`），所以这是真实过滤，不是装饰。
* **帖子可见性**（`app/models/post.rb`）：`visible?`（2258-2263）依次排除
  `loginblocked?`（2254：匿名且帖子要求登录）、`safeblocked?`（2245-2248：安全模式与非 `s` 评级、
  或命中站点屏蔽标签）、`deleteblocked?`（2250-2252）。不可见会影响下发的字段，见上一节。
* **字段级**：IP 列在所有资源上被 `hidden_attributes` 剔除（`application_record.rb:206-208`），
  帖子在不可见时另加 `md5`、`file_ext`（`post.rb:1894-1900`）。

<a id="sec-errors"></a>

## 错误与状态码

权限与错误体由 `ApplicationController` 决定（`app/controllers/application_controller.rb`）：

| 情形 | 状态 | 正文 | 出处 |
| :--- | :--- | :--- | :--- |
| 权限不足（含相关标签匿名、不可见评论） | `403` | `{"success": false, "reason": "Access Denied..."}` | `access_denied` 219-240（JSON 分支 236-238） |
| 记录不存在 | `404` | `{"success": false, "reason": "not found"}` | `render_404` 178-190（内联 JSON 在 183-185），不是模板 |
| 认证失败（凭据无效/不完整） | `401` | `error.json.erb` 的 `{"success": false, "message": ..., "code": ...}` | `rescue_exception` 139-142 |
| 其它预期错误（分页、标签、格式） | 见下 | 同上模板 | `render_expected_error` 196-200 |
| `posts` 的 `tags` 参数不是字符串 | `400` | 同上 | `posts_controller.rb:23-27`、`66-69` |
| `page` / `limit` 非法或越界 | `410` | 同上 | `rescue_exception` 151-152 |
| 标签过多/深度/非法、post 数超限、全文查询超时 | `422` | 同上 | 153-158 |
| 该端点没有 JSON 视图 | `406` | HTML 错误页 | `render_unsupported_format` 192-194 |
| 未匹配的动词/路由 | `405` | 错误页 | 147-148 |
| 已登录的非 `GET`/`HEAD` 写请求被限流 | `429` | 同上 | `api_check` 107-116（响应头 `X-Api-Limit`） |
| 数据库不可用 | `503` | 错误页 | 161-162 |

客户端侧：非 2xx 一律抛 `PybooruHTTPError`（`http_code`、`url`、`body`、`data`、`response`），
2xx 但非 JSON 抛 `PybooruAPIError`；`403` 的 JSON 正文实测为
`{"success": false, "reason": "Access Denied"}`。见 [errors.md](errors.md)。

## 分页与计数

* 入口 `Danbooru::Paginator::BaseExtension`（`app/logical/danbooru/paginator/base_extension.rb`）：
  `paginate` 8-20 按 `parse_page`（87-100）选编号页或游标模式；`paginate_posts`（24-27）只给帖子用账号的
  `per_page`；`parse_limit`（67-85）要求数字并在 `0..Danbooru.config.max_per_page` 之间，否则
  `PaginationError` → `410`。
* 游标：`b<id>` → `:sequential_before` → `id < N` 且按 id 降序；`a<id>` → `:sequential_after` →
  `id > N` 且按 id 升序后再反转（两者对外都是新→旧）。SQL 实现见
  `app/logical/danbooru/paginator/active_record_extension.rb:12-22`，OpenSearch 实现见
  `app/logical/danbooru/paginator/document_store_extensions.rb:26-37`（`range: { id: { lt/gt } }`）。
  编号页上限 `max_numbered_pages`，超过即 `410`（`validate_numbered_page!` 102-108）。
* 默认值来自 `config/danbooru_default_config.rb`：`records_per_page` 75（698）、`max_per_page` 320（704）、
  `max_numbered_pages` 750（392）、`tag_query_limit` 40（382，`rating:s`、`status:deleted`、`limit:` 不计入，
  见 `is_unlimited_tag?` 387-389）。
* 计数：`posts#count`（`posts_controller.rb:64-75`）用
  `max_count = max_numbered_pages * max_per_page + 1`（71），再取 `count_only(max_count:)` 与
  `count_capped?`（`document_store_extensions.rb:61-74`）。所以 `capped` 表示 OpenSearch 返回的是下限；
  实测两个站点都是 `{"count": 240001, "capped": true}`，即查询撞上了计数上限，不能当成精确总数。
  e621ng**没有** Danbooru 的 `/counts/posts.json` 路由。
* 全部请求都过 `validate_pagination_param_types`（`application_controller.rb:330-340`）：`page` / `limit`
  只能是标量，传哈希或数组会被拒。

## 评级

* 词表只有 `s` / `q` / `e`：元标签解析处 `app/logical/tag_query.rb:1454`
  （`if %w[s q e].include?(g2 = g2[0]&.downcase)`）——首字母不在表内的 `rating:` 元标签被**整条丢弃**，
  既不报错也不过滤，所以 `rating:g` 与不传标签同义；`rating:safe` / `questionable` / `explicit` 因取首字母而合法。
  实测与之相符（`rating:g` 与不带标签返回同一条最新帖）。
* 排序表 `ORDER_TABLE`（`app/logical/elastic_post_query_builder.rb:103-140`）与 `rating` 条件
  （218，`add_array_relation(:rating, :rating)`）都在全文检索构建器里；`status:`、`md5:`、`width:` 等元标签
  同文件 142-243。
* 安全模式：`SessionLoader#set_safe_mode`（`session_loader.rb:250-253`）取
  `Danbooru.config.safe_mode? || params[:safe_mode].truthy? || 账号设置`；上游仓库默认关闭
  （`danbooru_default_config.rb:27-30`），可用 `DANBOORU_SAFE_MODE` 环境变量或部署自己的
  `config/danbooru_local_config.rb`（`config/application.rb:24` 引入，上游 `.gitignore:5` 忽略该文件）覆盖。
  **e926 的实际过滤属于部署配置，不在上游仓库默认值内**，本库不替站点补 `rating` 过滤。
* 帖子更新侧的评级校验在 `app/models/post.rb:43`（只接受 `s`/`q`/`e`），与本库只读面无关。


<a id="sec-help-page"></a>

## `/help/api` 与 `/wiki_pages/<title>` 是两种记录

* `/help/<name>` 走 `resources :help_pages, controller: "help", path: "help"`（`config/routes.rb:282-286`），
  动作是 `HelpController#show`（`app/controllers/help_controller.rb:21-34`），实体是 `HelpPage`
  （`app/models/help_page.rb:3-18`，列 `id`、`name`、`wiki_page`、`related`、`title`、时间戳，
  并 `belongs_to :wiki`，按 `wiki_pages.title` 关联）。
* `/wiki_pages/<title>` 走 `wiki_pages#show`（`wiki_pages_controller.rb:28-45`），实体是 `WikiPage`，
  标题先经 `WikiPage.normalize_name`（小写、空格转下划线，`app/models/wiki_page.rb:267-269`）与
  `normalize_title`（241-251，会剥掉形如 `类别:` 的标签类别前缀），再 `titled`（56-58）。
* 实测区分：`/help/api` 返回 HelpPage（`name` 为 `api`，`wiki_page` 指向 `e621:api`）；
  `/wiki_pages/help%3Aapi.json` 返回 WikiPage（标题 `help:api`，`is_locked` 为 true）。
  本库只封了后者（`wiki_page_show`）。前者可用通用 `request()`，不能仅凭缺少 `.json` 就断言它返回 HTML：
  之前的匿名探测给 `/help/api` 发送 `Accept: application/json` 时取得了 HelpPage JSON。

<a id="sec-readonly-extensions"></a>

## 可用但未封方法的上游只读路由

这些路由源码上匿名可读、能返回 JSON，但没有原生方法（避免为未被使用的路由增加维护面），需要时用
`E621.request()` 显式调用：版本历史类 `/post_versions.json`、`/note_versions.json`、
`/artist_versions.json`、`/wiki_page_versions.json`；账号与站点类 `/users.json`、`/users/<id>.json`、
`/stats.json`、`/popular.json`、`/news_updates.json`、`/mod_actions.json`；社区类 `/forum_topics.json`、
`/forum_posts.json`、`/favorites.json`、`/blips.json`、`/user_feedbacks.json`、`/upload_karma_events.json`；
元数据类 `/tag_aliases.json`、`/tag_implications.json`、`/artist_urls.json`、`/post_sets.json`、
`/post_sets/<id>.json`、`/search_trends.json`、`/help.json`、`/help/list.json`、`/p/:id.json`（会 `302` 到
`/posts/<id>.json`）。逐路由的权限过滤器与可用性以 `app/controllers/*` 为准，本轮没有为它们发过请求。

<a id="sec-exclusions"></a>

## 排除项

* **写动词**：`posts#update`、`comments#create/update/destroy/hide/unhide/warning`、
  `pools#create/update/destroy/revert`、`notes#create/update/destroy/revert`、
  `wiki_pages#create/update/destroy/revert`、`artists#create/update/destroy/revert`、
  `tags#update/destroy/preview`、投票、收藏、待删标记、上传、批量变更请求、举报与审核、站内信、API key、
  OAuth、登录会话。它们都需要登录与对应权限，本库不封方法、不做自动重试，也不替调用者补参数。
* **没有动作或被登记错的动作**：`PUT /related_tag`（`routes.rb:382` 登记、控制器无 `update`）。
* **没有相应 JSON 实现或视图**：`deleted_posts`（`deleted_posts_controller.rb:4` 只 `respond_to :html`）、
  `comments/search`、`notes/search`、`wiki_pages/search` 等不作为 JSON 原生方法；具体格式失败由控制器响应
  分支与 Rails 视图协商决定。
* **可以匿名读、但没有原生方法的 JSON 路由**：`artists/show_or_new` 走
  `resources :artists` 的 collection（`config/routes.rb:211-215`），控制器 `respond_to :html, :json`
  （`artists_controller.rb:6`）且 `member_only` 例外含 `show_or_new`（`:7`）；未知名称返回未保存的
  `Artist` 对象（`artists_controller.rb:97-107` 的 `respond_with(@artist)`），名称已存在则 `redirect_to
  artist_path`（`:101`，`302`，目标不带 `.json`）。它与 `artists#show` 的"未知名称 JSON 404"不同，也不在
  18 个原生方法里；需要时用 `request()`，本路线**仅源码对齐、未实测**。
* **不存在的路由**：`/counts/*`（Danbooru 的形状）在上游没有对应路由；`/post` 系列单数路径在源码里是 `302`
  重定向（`routes.rb:569`、`578-583`），目标多数不带 `.json`，不可当作契约入口。
* **管理面**：`namespace :staff`（`routes.rb:22-`）下的文件、wiki、automod、用户清理、封锁等动作，以及
  OAuth/Doorkeeper 路由（仅当部署启用 provider，`routes.rb:3-14`）。

<a id="sec-deploy"></a>

## 源码与部署的差异


* `/post.json` 返回 `403` HTML「Access Denied - Oh no!」反脚本页：该页面在上游仓库里不存在，源码侧这条路径是
  `302` 重定向。因此任何「复数/单数」判别式在 e621 都不成立——须以站点自述与一次真实 JSON 响应判断引擎。
* `/counts/posts.json` 返回站点自己的 HTML `404`：说明的只是「没有 Danbooru 的计数路由」，**不代表**没有计数能力
  （真实计数是 `/posts/count.json`）。
* `rating:g` 与不传 `tags` 返回同一帖，与源码的静默丢弃一致。
* `/help/api` 的实体是 HelpPage，`/wiki_pages/help%3Aapi.json` 是 WikiPage（见上一节）。
* e926 的安全过滤来自部署配置，上游仓库默认关闭安全模式；两站相同的 `240001` / `capped=true`
  只说明两次查询都触到计数上限，不能据此认定两站真实帖子总数或内容范围相等。
* 站点身份的源码出处是 `app/views/static/_footer.html.erb:15-22`：普通用户看到 `Running e621ng`，
  版本来自 `GitHelper.version`。部署自述的版本号不是客户端对全部路由的兼容保证。
* 客户端沿用配置中的描述性 `User-Agent`。此快照未检出入站 User-Agent 的强制校验；
  `config/danbooru_default_config.rb:735-741` 定义的是站点**出站** HTTP 头，
  `app/logical/session_loader.rb:246` 只记录 API key 使用时的 User-Agent，不能混作入站要求的实现依据。
  本轮匿名请求使用配置中的 `Pybooru/5.0.0.dev1`；边缘访问策略不属于这份 Rails 源码的保证。

## 未实测

* `related_tag` / `related_tag_bulk` 的成员成功路径（含 `category_id` 分支与 `bulk` 的 `POST` 变体）——
  成员身份需要凭据；两者成功路径只做源码对齐，未实测。
* `v2=true` 的 `mode=extended` 与 `mode=thumbnail` 两个视图、不可见身份下帖子负载的置空与隐藏分支、
  `search` 白名单的成员/staff/admin 分支。
* 全部写路径、staff 面、OAuth 面、上面列出的只读扩展路由、以及自托管实例的差异。
* 本轮没有运行 formatter / lint / 测试套件；上游自带的 specs 只作为源码契约的第二份证据被引用。
