<!--- 标题请写明家族或类名，例如 `Zerochan.entry_list` 返回的 tags 缺失、`E621.post_list` 超时 -->

## Description
<!--- 这个 bug 是什么，影响了哪次调用（方法名 + 参数） -->

## Expected Behavior
<!--- 你认为应该发生什么，依据是什么：文档段落、上游路由/控制器位置，还是它以前的行为 -->

## Actual Behavior
<!--- 实际发生什么：抛出的异常与正文，或者返回里哪个字段/哪条记录不对 -->

## Steps to Reproduce
<!--- 贴出完整调用（类名、字面实参、--config / --site 取值），不要只写“请求失败” -->
1. `from anybooru import Danbooru`
2.
3.
4.

## Request Details
<!--- 这一段最有助于定位问题 -->
* 最终请求地址（`client.last_call['url']`，含查询串）：
* HTTP 状态码：
* 响应正文或异常：   <!--- AnybooruHTTPError 带 http_code / url / body / data；AnybooruAPIError 表示 2xx 但不是 JSON --->

## Your Environment
<!--- 尽量给全，缺项会让问题无法复现 -->
* Anybooru Version:   <!--- python -c "import anybooru; print(anybooru.__version__)" -->
* Python Version:
* Engines / site:     <!--- Danbooru / Moebooru / Serika / e621ng / Zerochan，以及具体站点 URL -->
* Operating System and version:
* Link to your project:

## More Information

## Possible Fix
<!--- 可选：你猜测的原因或修法 -->

<!--- 请勿粘贴真实账号、API key、密码、cookie 或代理凭据；修改过的 sites / examples 片段只贴相关的几行 -->
