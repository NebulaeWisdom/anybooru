# Moebooru 契约审计附注

给维护者与契约核对者：每个方法的上游文件行号、权限过滤器、过期帮助页条目、实现层的 SQL 与缓存细节、
被排除的界面路由，以及**逐条**的“已实测 / 只对源码”状态。面向使用者的三页不重复这些内容：
[客户端用法](moebooru.md) · [方法参考](moebooru-api.md) · [能力总览](moebooru-capabilities.md)。

## 证据来源与权威顺序

1. **上游源码**（只读参考，本地 clone `moebooru/` HEAD `206455e1`）：
   `config/routes.rb` 与 `app/controllers/*`（含 `ApplicationController` 的过滤器和 `respond_to_*` 助手）
   是唯一权威；下文行号都相对这个 clone，格式为 `routes.rb:N`（`moebooru/config/routes.rb`）、
   `xxx_controller.rb:N`（`moebooru/app/controllers/xxx_controller.rb`）。
2. **引擎自带帮助页** `app/views/help/api.en.html.erb`（608 行）：部分条目已过期，只当作旁证；
   任务书最初写的 `app/views/static/help/api.en.html.erb` 并不存在，实际路径是这一个。
3. **线上真实响应**：只用于确认现役部署的实际行为，逐条命令与观察见 [verification.md](verification.md)。

判断“哪些行为已被真实请求验证过”看状态列：

* **已实测**＝对线上站点真实发过该请求（项目 venv、匿名只读、代理来自配置）；
* **源码对齐**＝只核对了路由、控制器、模型与允许参数，**没有**向线上发过这个请求；
* **写动作与账号动作全部是源码对齐**。

## 路径、动词与格式

* **格式后缀**：`routes.rb` 里用 `match` / `get` / `post` 声明的路由都隐含一个可选 `(.:format)`；
  唯一例外是 `post/show`，它显式写了 `:format => false`（`routes.rb:153`）。
* **本库始终请求 `.json`**：`Moebooru.request()` 去掉相对路径开头的 `/`、去掉已有的 `.json` 再补回后缀；
  方法把 id 当请求参数发送（例如 `/post/update.json` 带 `id=`），而不是拼进路径——引擎自带的前端脚本也这么发。
  现役站点的列表形如 `GET /post.json`、`/pool.json`、`/note.json`。
* **`post/show` 不是 JSON 端点**：`.json` 匹配不到这条路由，也匹配不到 `post(.:format)`，
  最终落到兜底路由 `match "*path" => "errors#not_found"`（`routes.rb:280`）的 `head :not_found`
  （`errors_controller.rb:5`），得到**空正文 `404`**；对 `/post/show` 发 `Accept: application/json` 则得到 `406`。
  **单帖 JSON 走 `post_list(tags='id:<id>')`**（md5 用 `tags='md5:<哈希>'`），需要外层结构时再带
  `api_version=2`——`id` 查询本身不要求它。
* **旧 `/index` 别名**：`/post/index`、`/pool/index`、`/note/index`、`/wiki/index`、`/forum/index`、
  `/artist/index`、`/comment/index`、`/tag/index`、`/tag_alias/index`、`/tag_implication/index`、
  `/user/index`、`/user_record/index`、`/inline/index`、`/job_task/index`、`/banned/index`、
  `/admin/index`、`/batch/index` 都还在路由表里，但每一行都标着 `# FIXME: remove this`
  （如 `routes.rb:138`、`routes.rb:122`）；帮助页的版本记录也写明 `1.13.0+update.3` 移除了 `/index`。
  客户端只在 `api_version` 为 `1.13.0` / `1.13.0+update.1` / `1.13.0+update.2` 时生成这种路径，新代码不要依赖。
  四站探测里 `/post/index.json` 仍返回 `200`，只能说明别名当前还在。
* **HTML-only 不等于路由不存在**：被排除的端点（见下文排除项）大多有真实路由，只是没有 JSON 分支，
  或只有 JS / 订阅源 / 二进制响应。请求不支持的格式时，带 `respond_to` 的动作用 `UnknownFormat` 回 `406`，
  完全没有 `respond_to` 的动作用 `MissingTemplate` 回 `500`。

## 认证

* 登录字段是 `login` + `password_hash`，其中 `password_hash = SHA1(hash_string.format(password))`
  （`user.rb:87-97`，帮助页 `help/api.en.html.erb:95`）；本库在 `GET` / `HEAD` 放进查询串，
  其他动词放进表单体。
* 服务端还接受：`username` + `api_key`（`user.rb:12-14`，会置 `@from_api`）、会话 Cookie、
  `login` + `password_hash`、`user[name]` + `user[password]` 明文（`application_controller.rb:34-79`）。
  本库只实现 `password_hash` 一种。
* **`api_key` 身份必须请求 `.json`**：`limit_api` 只放行 `xml` / `json` / `zip`，其他格式直接
  `head :not_found`（`application_controller.rb:296-300`）。
* **匿名**＝`username` 与 `password` 都为空。凭据不完整不会降级成匿名，结果由服务端决定。
* **反垃圾参数陷阱**：请求里出现顶层参数 `url1` 时，`filter_spam` 直接 `head :ok`
  （`application_controller.rb:370-372`），也就是 `200` 空响应。不要用这个参数名。

## 权限

* 权限来自控制器的 `before_action` 过滤器，**没有独立的策略层**（这一点与 Danbooru 的 Pundit 不同）：
  `admin_only`、`mod_only`、`janitor_only`、`privileged_only`、`contributor_only`、`member_only`、
  `post_member_only`、`post_privileged_only`、`blocked_only`、`no_anonymous`。
* 拒绝时走 `access_denied`，JSON 是 `403 {"success": false, "reason": "access denied"}`
  （`application_controller.rb:12-30`）。
* `post_member_only` / `post_privileged_only` 在 `ApplicationController` 里有显式定义
  （`application_controller.rb:344-358`，覆盖了动态生成的同名方法），因此**对所有动词都执行成员/权限检查**：
  不要按“只有 POST 需要登录”理解这些动作（例如 `post/update` 的 GET 表单页同样要求成员身份）。
* 有些动作在方法体内判权限：`comment#destroy` / `#update` 的 `has_permission?`、`inline#delete` 的
  `has_permission?`、`post#destroy` 的 `can_user_delete?`（版主、帖子被 hold、或上传未满一天）、
  `inline#delete` 与 `user_record#destroy` 的归属检查，以及别名/蕴含 `commit='Delete'` 时允许待审记录的创建者。

各方法要求的身份（与上文过滤器一一对应；全部只做源码对齐，没有线上实测）：

| 需要的身份 | 方法 |
| :--- | :--- |
| 匿名可调 | `post_list`、`post_acknowledge_new_deleted_posts`、`post_similar`、`post_popular_recent`、`post_popular_by_day`、`post_popular_by_week`、`post_popular_by_month`、`pool_list`、`pool_show`、`note_list`、`note_search`、`note_history`、`favorite_list_users`、`inline_list`、`artist_list`、`tag_list`、`tag_related`、`tag_autocomplete_name`、`tag_summary`、`tag_alias_list`、`tag_implication_list`、`comment_list`、`comment_search`、`comment_show`、`comment_mark_as_spam`、`wiki_list`、`wiki_history`、`wiki_recent_changes`、`forum_list`、`forum_show`、`forum_search`、`user_list`、`user_autocomplete_name`、`user_check`、`user_create`、`user_reset_password` |
| 已登录（成员） | `post_create`、`post_update`、`post_destroy`、`post_revert_tags`、`post_vote`、`post_update_batch`、`post_flag`、`pool_create`、`pool_update`、`pool_destroy`、`pool_add_post`、`pool_remove_post`、`pool_import`、`pool_order`、`note_revert`、`note_update`、`history_undo`、`inline_copy`、`inline_delete`、`dmail_mark_all_read`、`artist_create`、`artist_update`、`tag_update`、`tag_alias_create`、`tag_implication_create`、`comment_create`、`comment_update`、`comment_destroy`、`wiki_create`、`wiki_update`、`wiki_revert`、`forum_create`、`forum_update`、`forum_destroy`、`forum_mark_all_read`、`user_update`、`user_authenticate`、`user_modify_blacklist` |
| 成员，但**只能操作自己的** | `post_activate`（非版主限自己的 hold） |
| 对象归属检查 | `post_destroy`（版主、帖子被 hold、或上传未满一天）、`comment_update` / `comment_destroy` / `forum_update` / `forum_destroy`（创建者或版主）、`inline_delete`（本人或版主） |
| contributor+ | `pool_copy` |
| janitor+ | `post_moderate`、`post_undelete` |
| privileged+ | `artist_destroy`、`user_record_destroy`（且需 mod 或该记录提交者） |
| mod+ | `wiki_destroy`、`wiki_lock`、`wiki_unlock`、`tag_mass_edit`、`tag_alias_update`（删除待审记录时创建者也可以）、`tag_implication_update`（同上）、`forum_lock`、`forum_unlock`、`forum_stick`、`forum_unstick` |

## 参数分层

| 层 | 形式 | 说明 |
| :--- | :--- | :--- |
| 顶层查询参数 | `?tags=...&limit=10&page=2` | 控制器直接读取的字段：搜索词、分页、开关 |
| 嵌套属性 | 查询串 `?post[tags]=...` / 表单 `pool[name]=...` | 写方法的模型属性，键名前缀就是模型名 |

* Moebooru **没有** Danbooru 的 `search[...]` 搜索字典：过滤条件本身就是顶层参数。
* 读方法把 `**params` 原样发出；写方法是“语义必需字段做成形参 + 其余属性收进 `**attributes`”，
  属性嵌套在模型名下：`post[...]`、`pool[...]`、`note[...]`、`tag[...]`、`tag_alias[...]`、
  `tag_implication[...]`、`wiki_page[...]`、`comment[...]`、`forum_post[...]`、`artist[...]`、
  `user[...]`、`user_record[...]`。
* **引擎按字符串比较的开关必须传字面值**，传 Python 布尔不生效：`unflag='1'`（`post_controller.rb:523`）、
  `redo='1'`（`history_controller.rb:186`）、`forcegray='1'`、`anonymous='1'`、
  `commit='Yes' | 'Approve' | 'Delete' | 'Cancel' | 'Post'`、`api_version='2'`、`filter='1'`、
  `include_tags='1'` 等。
* 嵌套哈希用 `params.require(:model)`：**缺少或为空会得到 `400`**（例如 `wiki_update` 必须至少发送一个
  `wiki_page[...]` 键；`post_update` 缺少 `post` 时控制器直接 `head :unprocessable_entity`，即 `422` 空正文）。
* `None` 值由客户端直接省略，不会发送。

## 分页与实际上限

页码从 1 开始，服务端把 `page` 夹在 `1..1000000`（`app/helpers/sessions_helper.rb:2`）。
每页大小按端点各自写死，下表是**服务端的真实行为**，不是客户端的限制：

| 端点 | 每页 / 上限 | 来源 |
| :--- | :--- | :--- |
| `post_list` | 默认 40（`limit:` 元标签可覆盖）；>1000 一律夹到 1000 | `post_controller.rb:273-276` |
| `pool_list` | 每页 20；`query` 里的 `limit:N` 被夹到 ≤100 | `pool_controller.rb:10-13,31-33` |
| `pool_show` | 每页 24 个帖子（账号 `pool_browse_mode == 1` 时 1000） | `pool_controller.rb:111-122` |
| `note_list` | 先按帖子分页（带 `post_id` 时每页最多 100 个帖子，否则 16 个），再铺平这些帖子的全部笔记 | `note_controller.rb:19-33` |
| `note_history` | 25；按 `post_id` / `user_id` 过滤时 50；**`limit` 被忽略** | `note_controller.rb:40-50` |
| `note_search` | 25 | `note_controller.rb:9` |
| `comment_list` | 25；**`limit` 被忽略** | `comment_controller.rb:61-63` |
| `comment_search` | 30 | `comment_controller.rb:109` |
| `forum_list` | 带 `parent_id` 时 100，否则 30；`latest` 固定第一页 10 条 | `forum_controller.rb:119-125`；`forum_post.rb:177-179` |
| `wiki_list` | `limit` 生效，默认 25 | `wiki_controller.rb:43,57` |
| `wiki_recent_changes` | `per_page` 生效，默认 25 | `wiki_controller.rb:158` |
| `artist_list` | 带 `name` / `url` 时 50，否则 25；**`limit` 被忽略** | `artist_controller.rb:81-90` |
| `tag_list` | 默认 50；`limit=0` 返回全部 | `tag_controller.rb:36-43,77-81` |
| `tag_related` | 没有 `limit` 参数，硬上限 25 | `app/models/tag/related_tag_methods.rb:6` |
| `tag_autocomplete_name` / `user_autocomplete_name` | 硬上限 20 | `tag_controller.rb:14`；`user_controller.rb:22` |
| `tag_alias_list` / `tag_implication_list` / `inline_list` / `user_list` | 20 | 各控制器 `paginate per_page: 20` |
| `post_popular_recent` / `_by_day` / `_by_week` / `_by_month` | 最多 40 条，按 `score` 降序 | `post_controller.rb:432-482` |
| `history` 索引（HTML-only） | 20 | `history_controller.rb:165` |

**被忽略的 `limit` 不要在调用侧当作支持**：`comment_list`、`note_history`、`artist_list` 都不读它。
`wiki_history` 例外地完全没有分页：它按版本倒序返回该页面的**全部**版本（`wiki_controller.rb:163-174`）。

## 返回结构

| 服务端用了什么 | 你拿到什么 |
| :--- | :--- |
| `respond_to_list` | 原对象的 JSON：列表是数组，详情是单个字典 |
| `respond_to_success(..., api: X)` | `X` 再合并 `{"success": true}`；没有 `api:` 时就是 `{"success": true}` |
| `respond_to_error(...)` | 状态 `420`（校验）/ `421`（限额）/ `422`（锁定）/ `423`（已存在）/ `424`（参数非法）/ `500`，正文是 `{"success": false, "reason": ...}`（`application_controller.rb:120-152`） |
| `access_denied` | `403 {"success": false, "reason": "access denied"}` |
| `head :no_content` | `204`，本库返回 `None`（`forum_mark_all_read`） |
| `Post.batch_api_data` | `{"posts": [...], "pool_posts": [...], "pools": [...], "tags": {...}, "votes": {...}}`，由 `post_update_batch`、`post_moderate`、`post_vote`、`post_flag`、`pool_remove_post`、`post_undelete` 使用 |

错误响应不一定是 JSON：HTML 错误页（例如对未知编号请求 `comment/show` 得到的 `404`）的原文会放在
`AnybooruHTTPError.body`，此时 `.data` 是 `None`。判定失败请以状态码为准，不要假定 `.data` 一定可解析。

## 写请求的重定向与结果歧义

`requests` 跟随 `302` / `303` 并保留 `Accept`，所以“最终读到 JSON”是可能的，但它**不是写入成功的确认**：
只有 flash 提示的校验失败也会重定向到同一个目标页。以下动作的返回与直觉不同：

| 动作 | 实际发生什么 |
| :--- | :--- |
| `tag_alias_create` / `tag_implication_create` | 成功后 `302` 到 `tag_alias#index` / `tag_implication#index`（两者支持 JSON），跟过去拿到的是**索引数组**，不是 `{"success": true}` |
| `tag_alias_update` / `tag_implication_update` | `Delete` 分支重定向到索引；`Approve` 分支重定向到 `job_task#index`（**只有 HTML**）：即使改动已经生效，也可能拿到 `500` 或非 JSON。**不要据此盲目重试**，写完后用列表接口自己确认 |
| `pool_import` / `pool_order` | POST 恒 `302` 到 `pool/show`（`redirect_to` 在 `respond_to` 之前），最终读到的是该合集 JSON |
| `forum_create` / `forum_update` / `forum_destroy` / `forum_lock` / `forum_unlock` / `forum_stick` / `forum_unstick` | `302` 到 `forum#show` 或 `forum#index`（都支持 JSON），最终读到帖子对象或数组；`forum_lock` 的编号在请求体里（`routes.rb:77`） |
| `artist_destroy` | 只有 `commit='Yes'` 才返回 `{"success": true}`；否则 `302` 回索引页（不是 JSON 错误） |
| `tag_mass_edit` | 只有站点开启 `enable_asynchronous_tasks` 时才同步返回 `{"success": true}`；同步分支没有 JSON 响应，**不要期待统一格式** |

判断写入是否真的生效，最可靠的做法是写完后自己再查一次目标资源。

## 逐方法：状态、路由与参数（90 个）

状态口径见文首。路由列写动词与路径；参数列写控制器实际读取的字段，返回列写客户端最后拿到的东西。

### 帖子（17）

| 方法 | 状态 | 路由（动词） | 参数与返回 |
| :--- | :--- | :--- | :--- |
| `post_list(**params)` | 已实测 | `GET post(.json)`（`routes.rb:137`；别名 `/post/index`） | `tags`、`limit`、`page`、`filter='1'`；不带 `api_version=2` 返回图片列表，带上后默认仅有 `posts`。`include_tags='1'` 添加 `tags`，`include_votes='1'` 添加 `votes`，`include_pools='1'` 添加 `pool_posts` / `pools`（`post_controller.rb:358-370`）。`api_version=2` 配 XML 得到 `424 V2 API is JSON-only` |
| `post_create(tags, *, file=None, source=None, md5=None, anonymous=None, **attributes)` | 源码对齐 | `POST post/create(.json)`（`routes.rb:165`，multipart） | `post[file]` **仅在给了文件时**发送；`post[source]`、`post[parent_id]`、`post[rating]`、`post[tags]`、`post[is_held]`；顶层 `md5` 用于上传后校验（不匹配 → `420` 并销毁帖子）、`anonymous='1'`（contributor+）。`post[is_rating_locked]` / `post[is_note_locked]` **不被创建接口接受**（`post_controller.rb:845-847`）；**只给来源的上传有效**（`post/file_methods.rb:216-218`）；重复 md5 → `423` 带 `post_id` / `location`；超出每日限额 → `421` |
| `post_update(post_id, **attributes)` | 源码对齐 | `POST\|PUT post/update(/:id)(.json)`（`routes.rb:162`） | 允许属性：`post[tags]`、`post[old_tags]`、`post[source]`、`post[parent_id]`、`post[rating]`、`post[is_held]`、`post[is_shown_in_index]`、`post[is_note_locked]`、`post[is_rating_locked]`、`post[frames_pending_string]`（`post_controller.rb:853-854`）。**没有文件替换**：`post[file]` 不被接受；缺少 `post` 哈希 → `422` 空正文；非版主改已删除帖 → `422 Post Locked` |
| `post_destroy(post_id, reason=None, *, destroy=None)` | 源码对齐 | `POST\|DELETE post/destroy(/:id)(.json)`（`routes.rb:164`） | `reason`；对**已被标记删除**的帖子，传 `destroy='1'`（任意非空值）才是永久删除，且仅版主可用（否则 `403`）；`commit='Cancel'` 直接 `302` 回帖子页；权限不足在动作内 `access_denied`（`post_controller.rb:217-244`） |
| `post_revert_tags(post_id, history_id)` | 源码对齐 | `POST\|PUT post/revert_tags(/:id)(.json)`（`routes.rb:161`） | `history_id` 是 `post_tag_histories` 的 id；返回只有 `{"success": true}`，不带帖子数据 |
| `post_vote(post_id, score=None)` | 源码对齐 | `POST\|PUT post/vote(/:id)(.json)`（`routes.rb:163`） | 不传 `score` 是**读自己当前的投票**（`{"success": true, "vote": <int>}`）；写入接受 `0..3`（0 清除投票），非版主负分或 `>3` → `424 Invalid score`；重复投票 → `423 Already voted`（带帖子数据） |
| `post_activate(post_ids)` | 源码对齐 | `GET\|POST post/activate(.json)`（`routes.rb:140`） | `post_ids` **必须是数组**（`post_ids[]=N`），非数组得到空 `204`；作用是**释出被 hold 的帖子**（`is_held = true` 的记录，`post/status_methods.rb:19-43`），非版主只能作用于自己的帖子；返回 `{"success": true, "count": N}` |
| `post_acknowledge_new_deleted_posts()` | 源码对齐 | `GET\|POST post/acknowledge_new_deleted_posts(.json)`（`routes.rb:139`） | 无参数；登录时顺带更新 `last_deleted_post_seen_at`；返回 `{"success": true}` |
| `post_update_batch(post)` | 源码对齐 | `GET\|POST post/update_batch(.json)`（`routes.rb:156`） | `post` 是**以帖子编号为键的映射**：`post[<post_id>][属性]`，属性同 `post_update`；只带编号的条目表示“只订阅回包”；返回恒为 JSON 的 `batch_api_data`（不受格式影响） |
| `post_moderate(ids, commit, reason=None, reason2=None)` | 源码对齐 | `GET\|POST post/moderate(.json)`（`routes.rb:146`） | `ids[<post_id>]=1` 的映射、`commit='Approve'` 或 `'Delete'`、`reason` / `reason2`；返回被触及帖子（含父帖）的 `batch_api_data` |
| `post_flag(post_id, reason=None, *, unflag=None)` | 源码对齐 | `POST\|PUT post/flag(/:id)(.json)`（`routes.rb:160`；**GET 未路由**） | 正常分支 `reason` 必填；`unflag='1'` 取消标记（仅标记者本人或版主）；非 active 的帖子标记 → `500`；非 flagged 的帖子取消标记 → `500`；返回 `batch_api_data` |
| `post_undelete(post_id)` | 源码对齐 | `GET\|POST post/undelete(/:id)(.json)`（`routes.rb:155`） | 返回帖子（及父帖）的 `batch_api_data` |
| `post_similar(*, file=None, **params)` | 源码对齐 | 无文件 `GET post/similar(.json)`；有文件 `POST post/similar(.json)`（`routes.rb:154`） | 查询参数 `id`（对比帖，未知 → `404`）、`url`、`search_id`、`services`（默认 `local`）、`threshold`、`forcegray='1'`、`width` / `height`、`initial='1'`；`file` 走 multipart 的 `file` 字段；没有 id/url/file/search_id → `503 no search supplied`；服务失败 → `503` 带服务报错文本；对比帖已删除 → `500 Post deleted` |
| `post_popular_recent(**params)` | 源码对齐 | `GET\|POST post/popular_recent(.json)`（`routes.rb:151`） | `period` ∈ `1w` / `1m` / `1y`，其他值被强制成 `1d`；返回最多 40 条 |
| `post_popular_by_day(**params)` | 已实测（错误路径） | `GET\|POST post/popular_by_day(.json)`（`routes.rb:148`） | `year`、`month`、`day`（缺省取当前时间）；日期非法 → `400` 空正文。四站探测返回 `200`，非法日期返回 `400` 空正文 |
| `post_popular_by_week(**params)` | 源码对齐 | `GET\|POST post/popular_by_week(.json)`（`routes.rb:149`） | 同上，三个日期参数指该周内任意一天 |
| `post_popular_by_month(**params)` | 源码对齐 | `GET\|POST post/popular_by_month(.json)`（`routes.rb:150`） | 同上，指该月内任意一天 |

### 合集（10）

所有写路由都同时挂着 GET，但 **GET 只是渲染表单页，写入必须 POST**；客户端方法一律发 POST。

| 方法 | 状态 | 路由（动词） | 参数与返回 |
| :--- | :--- | :--- | :--- |
| `pool_list(**params)` | 已实测 | `GET\|POST pool(.json)`（`routes.rb:121`；别名 `/pool/index`） | `query`（`order:X`、`limit:N`、`posts:RANGE`）、`order`（`name` / `date` / `updated` / `id`）、`page`；实测 yande.re 返回 20 条 |
| `pool_show(pool_id, **params)` | 已实测 | `GET/POST pool/show.json`（`routes.rb:131`，编号由查询参数传入） | 返回**一个合集对象**，帖子在 `posts` 里，每页 24 个（浏览模式为 1 时 1000 个）；编号不存在时也会 `302` 到 `/pool`，最终可能是合集列表。实测 yande.re `id=99411` 返回对象且含 `posts` |
| `pool_create(name, **attributes)` | 源码对齐 | `POST pool/create(.json)`（`routes.rb:125`） | `pool[name]`、`pool[description]`、`pool[is_public]`、`pool[is_active]`；返回 `{"success": true}`，**不带新编号** |
| `pool_update(pool_id, **attributes)` | 源码对齐 | `POST pool/update(/:id)(.json)`（`routes.rb:133`；**PUT 未路由**） | 同上四个属性；不是合集所有者且合集非公开 → `403` |
| `pool_destroy(pool_id)` | 源码对齐 | `POST pool/destroy(/:id)(.json)`（`routes.rb:126`；**DELETE 未路由**） | `{"success": true}`；无更新权限 → `403` |
| `pool_add_post(pool_id, post_id, sequence=None)` | 源码对齐 | `POST pool/add_post(.json)`（`routes.rb:123`；**PUT 未路由**） | 顶层 `pool_id` / `post_id`；`pool[sequence]` 可省；帖子已在合集 → `423 Post already exists` |
| `pool_remove_post(pool_id, post_id)` | 源码对齐 | `POST pool/remove_post(.json)`（`routes.rb:129`；**PUT 未路由**） | 返回帖子的 `batch_api_data`，并带 `X-Post-Id` 响应头 |
| `pool_copy(pool_id, name=None)` | 源码对齐 | `POST pool/copy(/:id)`（`routes.rb:124`） | `name` 默认 `<原名> (copy)`；JSON 只有 `{"success": true}`，**新编号只在 HTML 重定向里** |
| `pool_import(pool_id, posts)` | 源码对齐 | `POST pool/import(/:id)`（`routes.rb:127`） | `posts[<post_id>]=<sequence>`（按 sequence 排序）；POST **恒 `302`** 到 `pool/show`，跟随重定向后读到该合集 JSON |
| `pool_order(pool_id, sequences)` | 源码对齐 | `POST pool/order(/:id)`（`routes.rb:128`） | `pool_post_sequence[<pool_post_id>]=<sequence>`；同样恒 `302` |

### 笔记、历史、收藏、内联与站内信（11）

| 方法 | 状态 | 路由（动词） | 参数与返回 |
| :--- | :--- | :--- | :--- |
| `note_list(**params)` | 已实测 | `GET/POST note.json`（`routes.rb:113`；别名 `/note/index`） | `post_id` 限单帖；不传时按每页 16 个有 `last_noted_at` 的帖子分页，再返回这些帖子的全部笔记铺平后的数组；`page` 是帖子页码，`limit` 不生效。实测 yande.re 返回 22 条 |
| `note_search(query, **params)` | 源码对齐 | `GET\|POST note/search(.json)`（`routes.rb:116`） | `query` **必需**：不传会落到 HTML 分支，`.json` 得 `406`；全文检索，每页 25 |
| `note_history(**params)` | 已实测 | `GET\|POST note/history(/:id)(.json)`（`routes.rb:115`） | 取值优先级 `id`（笔记编号）→ `post_id` → `user_id`；每页 25（按 `post_id` / `user_id` 时 50）；**`limit` 被忽略**；实测 yande.re 返回 25 条 |
| `note_revert(note_id, version)` | 源码对齐 | `POST\|PUT note/revert(/:id)(.json)`（`routes.rb:117`） | `version` 是 `note_versions.version`；帖子锁定 → `422 Post is locked`；成功返回 `{"success": true}`（`note_controller.rb:68`） |
| `note_update(note_id=None, **attributes)` | 源码对齐 | `POST\|PUT note/update(/:id)(.json)`（`routes.rb:118`） | 传 `note_id` 走更新，不传走新建（新建必须有 `note[post_id]`）；属性 `note[x]`、`note[y]`、`note[width]`、`note[height]`、`note[body]`、`note[is_active]`（`note_controller.rb:99-100`）；返回 `{"success": true, "new_id", "old_id", "formatted_body"}` |
| `history_undo(change_ids, redo=None)` | 源码对齐 | `POST history/undo(.json)`（`routes.rb:91`） | `id` 是**逗号分隔的 `history_changes` id**（不是 `history` 的 id）；`redo='1'` 表示重做；`change_ids` 跨多条历史且调用者低于 privileged → `403`；返回 `{"success": true, "successful", "failed", "errors"}` |
| `favorite_list_users(post_id)` | 源码对齐 | `GET\|POST favorite/list_users(.json)`（`routes.rb:65`） | **没有过滤器（匿名可达）**；返回 `{"favorited_users": "name1,name2"}`——是逗号连接的字符串，没人收藏时是空串；帖子不存在 → `404` |
| `inline_list(**params)` | 源码对齐 | `GET\|POST inline(.json)`（`routes.rb:94`） | `page`；每页 20；返回 `id`、`description`、`user_id`、`images` |
| `inline_copy(inline_id)` | 源码对齐 | `POST\|PUT inline/copy(/:id)`（`routes.rb:100`） | 顶层 `id`；返回 `{"success": true}`（新内联图编号只在 HTML 重定向里） |
| `inline_delete(inline_id)` | 源码对齐 | `POST\|DELETE inline/delete(/:id)`（`routes.rb:102`） | 无过滤器，动作内判权限；顶层 `id`；不是本人（且非版主）→ `403`；返回 `{"success": true}` |
| `dmail_mark_all_read()` | 源码对齐 | `POST dmail/mark_all_read`（`routes.rb:62`） | 协议常量 `commit='Yes'`（否则 `302` 回收件箱）；返回 `{"success": true}`。`GET` 同路径是确认页（`routes.rb:61`），不是 JSON |

补两点免得找错地方：**历史通过 `note_history` / `wiki_history` 与 `history_undo` 访问**，
没有额外的“归档版本”JSON 端点——`history` 索引只有 HTML（`.json` → `406`）；
笔记与 wiki 的历史数据在 `note_versions` / `wiki_page_versions` 表里，分别由上面两个方法读取。

### 画师与标签（16）

| 方法 | 状态 | 路由（动词） | 参数与返回 |
| :--- | :--- | :--- | :--- |
| `artist_list(**params)` | 已实测 | `GET\|POST artist(.json)`（`routes.rb:19`；别名 `/artist/index`） | `name`、`url`、`order`、`page`；每页 25（带 `name` / `url` 时 50），**`limit` 被忽略**；实测 yande.re 返回 1 条（`fuzichoco`） |
| `artist_create(name, **attributes)` | 源码对齐 | `POST artist/create(.json)`（`routes.rb:21`） | `artist[name]`、`artist[alias_name]`、`artist[alias_names]`、`artist[member_names]`、`artist[urls]`、`artist[notes]`（`artist_controller.rb:111-112`）；**没有 `artist[alias]` / `artist[group]`**（帮助页仍写旧字段） |
| `artist_update(artist_id, **attributes)` | 源码对齐 | `POST artist/update.json`（`routes.rb:25`；**PUT 未路由**） | 同一份允许属性；GET 是编辑表单；`commit='Cancel'` 直接 `302` 回详情页 |
| `artist_destroy(artist_id)` | 源码对齐 | `POST artist/destroy(/:id)(.json)`（`routes.rb:22`） | 必须带 `commit='Yes'` 才是删除并返回 `{"success": true}`（`artist_controller.rb:22-27`） |
| `tag_list(**params)` | 已实测 | `GET\|POST tag(.json)`（`routes.rb:195`；别名 `/tag/index`） | `limit`（默认 50，`0` 为全部）、`order`（`name` / `date` / `count`）、`name`（支持 `*`）、`type`、`id`、`after_id`、`page`；实测 `name='touhou'` 非精确匹配 |
| `tag_related(**params)` | 已实测 | `GET/POST tag/related.json`（`routes.rb:205`） | `tags`（空白分隔，百分号与逗号被剥离并转小写）、`type`（必须是站点 `tag_types` 的键）；返回 `{tag: [[name,count],...]}`，没有 `limit`，每组最多 25 项；实测 yande.re 返回 25 组名称/计数 |
| `tag_update(name, **attributes)` | 源码对齐 | `POST tag/update(.json)`（`routes.rb:208`；**POST-only**） | `tag[name]`（必填）、`tag[tag_type]`、`tag[is_ambiguous]`；顶层的 `name` 不生效 |
| `tag_autocomplete_name(term)` | 源码对齐 | `GET tag/autocomplete_name`（`routes.rb:197`） | 只渲染 JSON 的动作；硬上限 20 个名字 |
| `tag_summary(**params)` | 源码对齐 | `GET tag/summary`（`routes.rb:207`） | `version`；带 `version` 且未变化时返回 `{"version", "unchanged": true}`，否则返回带 `data` 的摘要；版本号来自 `Tag.get_summary_version`（`tag_controller.rb:20-30`） |
| `tag_mass_edit(start, result)` | 源码对齐 | `POST\|GET tag/mass_edit`（`routes.rb:201`） | `start` 缺失 → `424 Start tag missing`；只有站点开启 `enable_asynchronous_tasks` 时才同步返回 `{"success": true}`（异步队列走 `job_task`） |
| `tag_alias_list(**params)` | 源码对齐 | `GET\|POST tag_alias`（`routes.rb:189`；别名 `/tag_alias/index`） | `query`、`page`；每页 20；返回 `[{id,name,alias_id,pending}]` |
| `tag_alias_create(name, alias_name, reason=None)` | 源码对齐 | `POST tag_alias/create`（`routes.rb:192`） | 引擎字段是 `tag_alias[name]`、`tag_alias[alias]`、`tag_alias[reason]`，所以 Python 形参用 `alias_name` 表示目标标签；创建的是待审（`is_pending`）记录，成功后 `302` 到索引（JSON 可用） |
| `tag_alias_update(aliases, commit, reason=None)` | 源码对齐 | `POST\|PUT tag_alias/update`（`routes.rb:191`） | `aliases[<id>]` 映射、`commit='Delete'` / `'Approve'`、`reason`；Approve 分支见“写请求的重定向”一节 |
| `tag_implication_list(**params)` | 源码对齐 | `GET tag_implication`（`routes.rb:211`；别名 `/tag_implication/index`） | `query`、`page`；每页 20；返回 `[{id,consequent_id,predicate_id,pending}]`；`commit='Search Aliases'` 会重定向到别名列表 |
| `tag_implication_create(predicate, consequent, reason=None)` | 源码对齐 | `POST tag_implication/create`（`routes.rb:214`） | `tag_implication[predicate]`、`tag_implication[consequent]`、`tag_implication[reason]`；成功后 `302` 到索引 |
| `tag_implication_update(implications, commit, reason=None)` | 源码对齐 | `POST\|PUT tag_implication/update`（`routes.rb:213`） | `implications[<id>]` 映射、`commit`、`reason` |

### 评论、Wiki 与论坛（27）

| 方法 | 状态 | 路由（动词） | 参数与返回 |
| :--- | :--- | :--- | :--- |
| `comment_list(**params)` | 已实测 | `GET\|POST comment(.json)`（`routes.rb:43`；别名 `/comment/index`） | `post_id`、`page`；**必须带 `post_id`**：模型生成的查询恒带 `post_id = params[:post_id].to_i`（`comment.rb:15-17`），不传就等于 `post_id=0`，得到空数组；**必须走 `.json`**——控制器分支判断的是 `params[:format]`（`comment_controller.rb:61`），只发 `Accept` 会拿到 HTML；每页 25，**`limit` 被忽略** |
| `comment_search(query, **params)` | 已实测 | `GET\|POST comment/search`（`routes.rb:47`） | `query`（支持 `user:<name>`）、`page`；传空字符串则不启用全文过滤，可当作不带 `post_id` 的评论流——这类查询在线上可能返回空列表，**空列表是正常结果，不是失败**；每页 30。首次实测与续跑都返回 `[]`，**没有取得非空评论正文** |
| `comment_show(comment_id)` | 已实测（错误路径） | `GET\|POST comment/show(/:id)(.json)`（`routes.rb:48`） | `id`；返回单条评论对象。实测 `id=0` 返回 `404`、550 字节 HTML，`.data is None` |
| `comment_create(post_id, body)` | 源码对齐 | `POST comment/create(.json)`（`routes.rb:51`） | `comment[post_id]`、`comment[body]`；控制器只在顶层 `commit='Post'` 时才检查成员每小时限额（`comment_controller.rb:34`，本库不发送该值，因此不会进入该分支），`commit='Post without bumping'` 可不顶帖；**`comment[anonymous]` 不被接受**（`comment_controller.rb:141-142`） |
| `comment_update(comment_id, **attributes)` | 源码对齐 | `POST\|PUT comment/update(/:id)`（`routes.rb:50`） | `comment[body]`、`comment[post_id]`；无权 → `403` |
| `comment_destroy(comment_id)` | 源码对齐 | `POST\|DELETE comment/destroy(/:id)(.json)`（`routes.rb:49`） | `{"success": true}`；无权 → `403` |
| `comment_mark_as_spam(comment_id)` | 源码对齐 | `POST comment/mark_as_spam(/:id)`（`routes.rb:52`） | **没有过滤器（匿名可达）**；`{"success": true}`；控制器没有来源过滤，所以不能当作“匿名安全”的读接口 |
| `wiki_list(**params)` | 已实测 | `GET/POST wiki.json`（`routes.rb:260`；别名 `/wiki/index`） | `query`（普通词走全文检索，`title:` 前缀切换为标题匹配）、`order`（`date` / `title`）、`limit`（默认 25）、`page`；实测 yande.re 返回 2 条 |
| `wiki_history(title=None, **params)` | 已实测 | `GET\|POST wiki/history(/:id)(.json)`（`routes.rb:265`） | `title` 或 `id` 指定页面；返回 `wiki_page_versions` 数组（按版本倒序，**不分页**）；实测版本 2/1 |
| `wiki_recent_changes(**params)` | 源码对齐 | `GET\|POST wiki/recent_changes`（`routes.rb:267`） | `user_id`、`per_page`（默认 25）、`page` |
| `wiki_create(title, body)` | 源码对齐 | `POST wiki/create(.json)`（`routes.rb:275` 附近） | `wiki_page[title]`、`wiki_page[body]`；校验失败 → `420`；成功返回 `{"success": true, "location"}` |
| `wiki_update(title, *, new_title=None, **attributes)` | 源码对齐 | `POST/PUT wiki/update.json`（`routes.rb:273`） | 顶层 `title` 选中页面；`new_title` → `wiki_page[title]`，`body` → `wiki_page[body]`，两层标题可以同时传入而不冲突；**必须至少一个嵌套属性**，否则 `400`；锁定页 → `422` |
| `wiki_destroy(title)` | 源码对齐 | `POST\|DELETE wiki/destroy(.:format)`（`routes.rb:270`） | 顶层 `title`；`{"success": true}` |
| `wiki_lock(title)` / `wiki_unlock(title)` | 源码对齐 | `POST\|PUT wiki/lock` / `wiki/unlock`（`routes.rb:272,274`） | 顶层 `title`；`{"success": true}`；不存在的标题在 lock / unlock 上会 `500` |
| `wiki_revert(title, version)` | 源码对齐 | `POST\|PUT wiki/revert(.:format)`（`routes.rb:271`） | 顶层 `title` + `version`；返回 `{"success": true}`；锁定页 → `422` |
| `forum_list(**params)` | 已实测 | `GET\|POST forum(.json)`（`routes.rb:68`；别名 `/forum/index`） | `parent_id`（每页 100）、`latest`（固定第一页 10 条）、`page`（否则每页 30）；实测 yande.re 返回 30 条 |
| `forum_show(forum_id, **params)` | 源码对齐 | `GET\|POST forum/show(/:id)`（`routes.rb:74`） | `id`；返回单个帖子对象 |
| `forum_search(query, **params)` | 源码对齐 | `GET\|POST forum/search`（`routes.rb:75`） | `query`、`page`；每页 30 |
| `forum_create(title, body, **attributes)` | 源码对齐 | `POST forum/create`（`routes.rb:83`） | `forum_post[parent_id]`（`0` / 缺省 = 新主题，否则回复）、`forum_post[title]`、`forum_post[body]`；`302` 到 `forum/show/<根帖 id>` |
| `forum_update(forum_id, **attributes)` | 源码对齐 | `POST\|PUT forum/update(/:id)`（`routes.rb:81`） | `forum_post[title]`、`forum_post[body]`、`forum_post[parent_id]`；`302` |
| `forum_destroy(forum_id)` | 源码对齐 | `POST\|DELETE forum/destroy(/:id)`（`routes.rb:82`） | `302` |
| `forum_lock(forum_id)` / `forum_unlock(forum_id)` / `forum_stick(forum_id)` / `forum_unstick(forum_id)` | 源码对齐 | `POST\|PUT forum/lock`（编号在请求体）/ `forum/unlock(/:id)` / `forum/stick(/:id)` / `forum/unstick(/:id)`（`routes.rb:77-80`） | `302` |
| `forum_mark_all_read()` | 源码对齐 | `GET\|POST forum/mark_all_read`（`routes.rb:76`） | `204` 空响应 → 本库返回 `None` |

### 账号（9）

账号面只做源码对齐，**没有可用的测试账号，一次线上请求都没发**。

| 方法 | 状态 | 路由（动词） | 参数与返回 |
| :--- | :--- | :--- | :--- |
| `user_list(**params)` | 已实测 | `GET\|POST user(.json)`（`routes.rb:225`；别名 `/user/index`） | `name`、`level`、`id`、`order`、`page`；每条只有 `{name, id}`（`user.rb:183-185`），每页 20；实测 yande.re 返回 20 条 |
| `user_autocomplete_name(term)` | 源码对齐 | `GET user/autocomplete_name`（`routes.rb:224`） | 关键词长度 < 2 返回空数组；硬上限 20 个名字 |
| `user_check(username, password)` | 源码对齐 | `POST user/check`（`routes.rb:231`） | **独立端点，按协议要求明文发送** `username` + `password`；返回 `{"response", "exists", "name", "id", "no_email", "pass_hash", "user_info"}`，`response` 为 `success` / `unknown-user` / `wrong-password`（`user_controller.rb:121-147`） |
| `user_create(name, password, password_confirmation, **attributes)` | 源码对齐 | `POST user/create`（`routes.rb:247`） | `user[...]`：`name`、`email`、`password`、`password_confirmation`、`blacklisted_tags`、`always_resize_images`、`receive_dmails`、`show_samples`、`use_browser`、`show_advanced_editing`、`pool_browse_mode`；返回 `{"response": "success"|"error", "errors": [...]}` |
| `user_update(**attributes)` | 源码对齐 | `POST/PUT/PATCH user/update.json`（`routes.rb:246`） | 属性同创建接口但**不接受 `name`**，额外允许 `current_password`；返回 `{"success": true}` 或 `420` |
| `user_authenticate(**params)` | 源码对齐 | `POST\|PUT user/authenticate`（`routes.rb:244`） | `url`；`{"success": true}` |
| `user_modify_blacklist(add=None, remove=None)` | 源码对齐 | `POST\|PUT user/modify_blacklist`（`routes.rb:245`） | `add[]` / `remove[]`；返回 `{"success": true, "result": [tags]}` |
| `user_reset_password(name, email)` | 源码对齐 | `GET\|POST user/reset_password`（`routes.rb:238`） | `user[name]`、`user[email]`；返回 `{"result": "success"}`（另有 `unknown-user` / `no-email` / `wrong-email` 失败结果，SMTP 拒收时为 `invalid-email`）（`user_controller.rb:230-263`） |
| `user_record_destroy(user_record_id)` | 源码对齐 | `POST\|DELETE user_record/destroy(/:id)`（`routes.rb:257`） | `{"success": true}`；否则 `403`（privileged+，且 mod+ 或该记录提交者） |

一次连接被对端关闭的中断发生在既有的评论读取序列中（没有 HTTP 响应），**已复查为不可复现**，
不能记为 404 或限流阈值；事实记录见 [verification.md](verification.md) 的 Moebooru 章节。

## 字段坐标（本库原样返回，不做裁剪）

`as_json` / `api_attributes` 的完整字段集：

* 帖子 `post/api_methods.rb:4-80`（`status == "deleted"` 时删掉 `sample_url` / `jpeg_url` / `file_url`，
  `post_similar` 结果另带 `similarity`，见 67-68 行）；合集 `pool.rb:128-141`；
  **`pool_show` 的 JSON 另有视图** `app/views/pool/show.json.jbuilder`（顶层键是
  `id`、`name`、`created_at`、`updated_at`、`user_id`、`is_public`、`post_count`、`description`、`posts`，
  每个帖子项是 `id`、`tags`、`created_at`、`creator_id`、`author`、`change`、`source`、`score`、`md5`、
  `file_size`、`file_url`、`is_shown_in_index`、`preview_url`、`preview_width`、`preview_height`、
  `actual_preview_width`、`actual_preview_height`、`sample_url`、`sample_width`、`sample_height`、
  `sample_file_size`、`jpeg_url`、`jpeg_width`、`jpeg_height`、`jpeg_file_size`、`rating`、`has_children`、
  `parent_id`、`status`、`width`、`height`、`is_held`、`frames_pending_string`、`frames_pending`、
  `frames_string`、`frames`）；合集成员 `pool_post.rb:39-49`；
  笔记 `note.rb:50-72`；笔记版本 `note_version.rb:6-7`；评论 `comment.rb:73-88`；
  论坛帖 `forum_post.rb:101-115`；画师 `artist.rb:181-198`；标签 `tag/api_methods.rb:6-14`；
  标签别名 `tag_alias.rb:90-104`；标签蕴含 `tag_implication.rb` 的 `as_json`
  （`{id, consequent_id, predicate_id, pending}`）；内联 `inline.rb:70-80`；
  内联图 `inline_image.rb:304-323`；历史变更 `post_tag_history.rb:100-101`；
  被标记帖子详情 `flagged_post_detail.rb:36-52`。

## 帮助页与 `help/api` 的 Accept 伪影

* `help/api` 只有 HTML 模板：本库固定发 `Accept: application/json`，于是落到兜底路由
  `errors#not_found`，yande.re 回它的 HTML 404 页（550 字节）、konachan.com 与 sakugabooru.com 回空正文；
  换 `Accept: text/html` 就是 `200`。**这不是站点缺页面，也不是路由不存在**——各站 `help/api`
  正是站点自述 API 版本与加盐模板的来源。
* 请求不支持的格式时，带 `respond_to` 的动作用 `UnknownFormat` 回 `406`，
  完全没有 `respond_to` 的动作用 `MissingTemplate` 回 `500`。

## 帮助页中已过期的条目

引擎自带帮助页（`app/views/help/api.en.html.erb`，608 行）与当前路由 / 控制器不一致之处：

* 仍写 `post[file]` 可替换文件：`post/update` 的允许字段里没有 `file`，会被丢弃。
* 仍写 `+1` / `-1` 投票与分数语义：当前 `post/vote` 接受 `0..3`（0 清除），非版主负分或 `>3` 得 `424`。
* 仍列 `post/show` 作为可用 JSON 端点：当前路由显式 `format: false`（`routes.rb:153`）；同理不再列 `wiki/show`。
* 仍列 `artist[alias]` / `artist[group]`：当前允许 `alias_name`、`alias_names`、`member_names`、`urls`、`notes`。
* 仍列 `tag[name_pattern]`：当前控制器不实现该参数。
* 帮助页的版本记录确认 `1.13.0+update.3` 移除了 `/index` 形态，与路由表里那些
  `# FIXME: remove this` 的别名一致。
* 帮助页里“评论不再有索引”之类的变更说明不能推翻当前路由与控制器。

## 排除项（都有真实路由，只是没有 JSON）

`Moebooru.request()` 始终请求 `.json`；它既不把 HTML 变成 JSON，也不做订阅源 / ZIP 下载出口。
请求这些地址通常先得到 HTTP 错误（`AnybooruHTTPError`），只有 2xx 非 JSON 正文才抛 `AnybooruAPIError`。

### 只渲染 HTML / JS（`.json` 会 406 或 500）

| 路由 | 说明 |
| :--- | :--- |
| `GET post/show(/:id)(/*tag_title)`（`routes.rb:153`） | `:format => false`，只渲染 HTML；`.json` 落到兜底 404 空正文 |
| `GET post/browse`（`routes.rb:142`） | 浏览器页面，`.json` → `406` |
| `GET\|POST post/deleted_index`（`routes.rb:144`） | 只有 HTML 模板，`.json` → `500`；控制器没有登录过滤器 |
| `GET\|POST post/upload`（`routes.rb:157`）、`post/upload_problem`（`routes.rb:158`） | 上传表单；`upload_problem` 是空动作且没有模板，任何格式都 `500` |
| `GET\|POST post/delete(/:id)`（`routes.rb:143`） | 删除确认页；真正的写是 `post_destroy` |
| `GET post/error`（`routes.rb:145`） | 静态 HTML |
| `GET\|POST tag/cloud`（`routes.rb:198`） | 标签云，只渲染页面 |
| `GET\|POST tag/popular_by_day` / `_week` / `_month`（`routes.rb:202-204`） | 同样只渲染页面；日期非法 → `400` |
| `GET\|POST tag/edit(/:id)`、`tag/edit_preview`（`routes.rb:199-200`） | HTML 编辑页 / 预览片段 |
| `GET wiki/show.json`（`routes.rb:269`） | `respond_to` 只有 `format.html`（`wiki_controller.rb:110-130`），`.json` → `406` |
| `GET\|POST wiki/add`、`wiki/diff`、`wiki/edit`、`wiki/preview`、`wiki/rename`（`routes.rb:262-268`） | 编辑 / 对比 / 预览页面 |
| `GET\|POST history`、`history/index`（`routes.rb:89-90`） | 索引页只有 `format.html`，`.json` → `406`；索引每页 20（`history_controller.rb:165`） |
| `GET\|POST comment/edit(/:id)`、`comment/moderate`（`routes.rb:45-46`） | HTML / 重定向 |
| `GET\|POST forum/preview`、`forum/new`、`forum/add`、`forum/edit(/:id)`（`routes.rb:70-73`） | 预览片段（即使请求 `.json` 也返回 HTML）与表单页 |
| `GET\|POST pool/select`（`routes.rb:130`）、`pool/transfer_metadata`（`routes.rb:132`） | 选择器（`.json` → `406`）与元数据迁移表单（`.json` → `500`） |
| `GET\|POST artist/preview`、`artist/show(/:id)`（`routes.rb:23-24`） | 预览片段与 `302` 到 wiki 页面 |
| `GET\|POST tag/show(/:id)`（`routes.rb:206`） | `302` 到 wiki 页面 |
| `GET\|POST tag_subscription`、`tag_subscription/index`（`routes.rb:217-218`） | 索引只渲染 HTML；`create`（219）与 `destroy(/:id)`（221）只有 JS 分支；`update`（220）`302` 到 `user#edit` |
| `dmail` / `dmail/inbox`、`compose`、`preview`、`show`、`create`、`show_previous_messages`（`routes.rb:55-60`） | 模板或重定向；`show` 会顺带标记邮件已读。只有 `mark_all_read` 的 POST 有 JSON |
| `inline/create`、`add_image`、`update`、`edit`、`crop`、`delete_image`（`routes.rb:96-103`） | 重定向或 HTML / JS |
| `user/show(/:id)`、`edit`、`change_email`、`change_password`、`home`、`login`、`signup`、`invites`、`block(/:id)`、`unblock`、`set_avatar(/:id)`、`remove_avatar/:id`、`show_blocked_users`（`routes.rb:228-243`） | HTML 表单或 `302` |
| `GET\|POST user_record`、`user_record/index`、`user_record/create(/:id)`（`routes.rb:254-256`） | 索引只有 HTML；创建是表单重定向 |
| `GET help(/:page)`（`routes.rb:86`） | 只有 HTML 模板（`app/views/help/`），见上文的 Accept 伪影 |

### 仅重定向

| 路由 | 说明 |
| :--- | :--- |
| `GET\|POST post/view(/:id)`（`routes.rb:159`） | `302` 到 `post/show` |
| `GET\|POST post/random(/:id)`（`routes.rb:152`） | `302` 到 `post/show/<id>` 或 `/post`；路径里的编号会被动作忽略 |

### 依赖站点开关或本身就是死路由

| 路由 | 说明 |
| :--- | :--- |
| `GET\|POST user/activate_user`、`user/resend_confirmation`（`routes.rb:227,237`） | 动作只在 `CONFIG[enable_account_email_activation]` 开启时定义 |
| `GET\|POST user/remove_from_blacklist`（`routes.rb:236`） | 空动作且没有模板，任何格式都 `500` |
| `GET\|POST report/set_dates` 等报表路由（`routes.rb:170-175`） | 控制器里 `set_dates` 是 private 方法（`report_controller.rb:61-69`），报表只渲染 HTML / 投票模板 |
| `resources :advertisements`（`routes.rb:9-16`）、`batch/*`（`routes.rb:32-36`）、`blocks/*`（`routes.rb:39-40`）、`job_task/*`（`routes.rb:106-110`）、`admin/*`（`routes.rb:3-6`）、`settings/api`（`routes.rb:178-180`） | 全部渲染模板或重定向：`advertisements#redirect` 还会累加点击数；`job_task` 的 index/show 是 HTML 或跳转 `post/show`；`admin/reset_password` 只有一个 JSON 异常分支（不是正常成功契约）；`settings/api#show` 的 `ensure_api_key` 会改动账号状态，不是匿名只读接口 |
| `GET\|POST static/*`、`opensearch`、`help(/:page)`、`banned`、`root`（`routes.rb:85,182-186,280`） | 站点页面 / 导航 / 状态码，没有数据包装 |

### 订阅源与二进制

| 路由 | 说明 |
| :--- | :--- |
| `GET post/atom(.:format)`、`GET\|POST atom`（`routes.rb:141,167`） | Atom 订阅源（最新 40 帖），不是 JSON |
| `GET post/piclens`（`routes.rb:147`） | RSS 订阅源，默认格式 `rss` |
| `GET pool/zip/:id`（`routes.rb:134`） | 二进制 ZIP（`send_data` + `X-Archive-Files` 头，未知 hash 时 `404`，否则 `302` 到 `?hash=<md5>`） |

### 弃用的 `/index` 别名

`/post/index`、`/pool/index`、`/note/index`、`/wiki/index`、`/forum/index`、`/artist/index`、
`/comment/index`、`/tag/index`、`/tag_alias/index`、`/tag_implication/index`、`/user/index`、
`/user_record/index`、`/inline/index`、`/job_task/index`、`/banned/index`、`/admin/index`、`/batch/index`
都还在路由表里，但都标着 `# FIXME: remove this`；客户端只在旧 `api_version` 下生成它们，新代码不要依赖。
四站探测里 `/post/index.json` 仍返回 `200`，只能说明别名当前还在。

## 未解决与未实测

* 全部写动作、账号 / 密码认证、上传文件与只给来源的上传、权限等级、审核与删除都没有实测；
  包括源码允许匿名进入的修改型动作（`comment_mark_as_spam`、`post_acknowledge_new_deleted_posts`）。
* 未运行过的具名读接口仍只是源码对齐，逐条见上文状态列；笔记与 wiki 历史是例外，确已运行。
* 旧路径版本的真实部署、下游 fork 差异、写操作重定向后的结果、异步任务后端都没有实测；
  方法存在不等于目标站点启用了相应能力（例如未开启 `enable_asynchronous_tasks` 时 `tag_mass_edit`
  没有同步 JSON 响应）。
* `sakugabooru` 的加盐模板取自站点自述，**没有发登录请求**验证服务端是否接受。
* 现役 Moebooru 站点普遍有反爬与限流：中途被关闭连接、拿不到 HTTP 响应可能发生，
  但本轮未复现、也未观察到突发阈值，不能记成 HTTP 错误码或限流阈值。

相关文档：[客户端用法](moebooru.md) · [方法参考](moebooru-api.md) ·
[能力总览](moebooru-capabilities.md) · [线上证据](verification.md)。
