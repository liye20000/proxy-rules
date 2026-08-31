# Codex Cloud 环境与每周巡检

## 环境基线

- 仓库：`liye20000/proxy-rules`，默认分支 `main`。
- 工作目录：仓库根目录；项目规范来自根目录 `AGENTS.md`。
- Python：3.13。
- Setup script：`python -m pip install pytest`。
- Secrets：空；不添加 PAT、GitHub Secret 或 `OPENAI_API_KEY`。
- Description 使用以下文本，使环境摘要与当前自动合并门禁一致：

  ```text
  Strict proxy whitelist maintenance. Follow AGENTS.md, run real generation and the full pytest suite.
  Safe additive domain PRs may auto-merge after CI; risky or broad changes remain draft or report-only.
  ```
- Agent 网络：开启，域名列表选择 `All`，HTTP 方法只允许 `GET`、`HEAD`、`OPTIONS`；仅用于读取
  任意新服务的官方资料，不允许登录、上传或远端写入。
- 交付：从最新 `main` 建立 `codex/domain-<service>-<YYYYMMDD>` 分支。满足根目录 `AGENTS.md`
  自动门禁的纯新增域名创建 ready PR；其他变化创建草稿 PR 或报告。
- Google AI 官方产品页的 AI Mode 入口使用 `google.ai` 跳转到 `google.com`；白名单以
  `exact:google.ai` 只覆盖该入口，不扩大到其他 `.ai` 域名。
- Google AI 官方产品页的 Lens 入口使用 `search.google`；白名单以
  `exact:search.google` 只覆盖该入口，实际搜索与应用深链继续由既有 Google 规则覆盖。

环境页面显示 `Use this` 只能证明仓库和配置已经保存。首次使用还应提交一次只读健康检查，确认
Cloud 容器能够实际检出仓库、执行生成器和完整测试：

```text
只做环境健康检查，不修改文件、不提交、不创建 PR。
读取 AGENTS.md，输出 Python 版本，运行 python generate.py 和
python -m pytest tests/ -q，最后输出 git status --short 并报告测试数量。
```

## 手机启动云端任务

最稳定的入口是手机浏览器打开 <https://chatgpt.com/codex/cloud>，选择
`liye20000/proxy-rules` 环境并点击 `Use this`。ChatGPT iOS App 已出现 `Codex`、`Code` 或
`Remote` 入口的账号也可以直接使用；选择同一仓库、`main` 和本环境后提交需求。如果 App
没有仓库或环境选择器，应改用手机浏览器，避免在未绑定仓库的普通聊天中提交维护任务。

日常只需描述目标，例如：

```text
把 example.com 加入代理白名单，遵循 AGENTS.md 全自动处理。
安全的纯新增域名通过 CI 后自动合并；风险或大范围变更只报告并创建草稿 PR。
完成后继续跟踪到 main 复验成功，再告诉我最终结果。
```

任务运行在 Cloud 独立容器中，不需要本地电脑保持开机。Cloud 合并到 GitHub 后，本地工程仍然
独立有效；本地执行 `git switch main` 和 `git pull --ff-only origin main` 才会取得云端的新提交。
不要让本地与 Cloud 同时修改同一个工作分支。

## 周期任务提示词

```text
维护 liye20000/proxy-rules。遵循根目录 AGENTS.md。每周检查最近七天 GitHub Actions、
三个 raw 订阅产物、Telegram 五个 ASN 的空值/非法 CIDR/数量异常，并对比 OpenAI、Gemini、
Google AI、Google Labs 的官方域名清单。先搜索已有 codex-maintenance Issue/PR，避免重复。

健康且无变化时不创建 Issue 或 PR。官方新增且确定是核心功能时，只允许新增：从最新 main
创建 codex/domain-<service>-<YYYYMMDD>，更新主源并生成三个派生产物，运行真实生成和完整
pytest 后创建 ready PR，由 safe-domain-automerge 在 CI 全绿且门禁通过后自动合并。若需要修改
测试、文档、脚本或工作流，改建草稿 PR。若无法运行完整验证，则创建 Issue，附证据、建议差异
和可直接交给 Codex Cloud 的修复提示。涉及删除、来源冲突或大范围代理扩张时只报告，不修改。
```

计划时间：每周一 09:00，时区 `Asia/Shanghai`。连接器或云端任务失效不影响定时 Actions 与
客户端公开订阅。
