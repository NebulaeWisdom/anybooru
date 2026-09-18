<!--- 标题写成一句话改动摘要，例如 fix(moebooru): 合集写操作改用 POST -->

## Description
<!--- 改了什么、为什么这样改：涉及的方法、文件、配置键，以及行为上的前后差别 -->

## Motivation and Context
<!--- 解决什么问题；若修复 issue，请链接。若涉及契约，请写明上游路由与控制器位置
     （Zerochan 为 API 页面出处 + 实测响应） -->

## How Has This Been Tested?
<!--- 写清实际执行的命令与结果，不要只写“已测试”。没有跑过的路径直接写“未执行” -->
* 执行的命令：
* 关键输出 / HTTP 状态码：
* 未执行、未实测的路径（需要凭据、会写入，或依赖特定站点）：它的源码依据是什么：

## Code Examples (if appropriate):

## Types of changes
<!--- 在适用的方框里填 `x` -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)

## Checklist:
<!--- 逐项确认；不确定就照实写，不要默认勾选 -->
- [ ] 我的改动符合项目的代码风格（PEP-8）。
- [ ] 新增或修改的方法给出了契约依据（上游路由与控制器位置；Zerochan 为 API 页面出处 + 实测响应）。
- [ ] 我的提交按独立目的拆分，每个 commit 只承担一个明确目的。
- [ ] 我已同步更新 `docs/` 下受影响的内容：`<家族>.md`（客户端用法）、`<家族>-api.md`（方法参考）、
      `<家族>-capabilities.md`（能力入口）、`<家族>-contract-notes.md`（出处与排除项），实测记录写进
      `docs/verification.md`。
- [ ] 我没有在对外文档里写入本机代理地址、绝对路径或临时目录。
- [ ] 我已阅读 CONTRIBUTING.md。
