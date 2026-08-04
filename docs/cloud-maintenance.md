# Codex Cloud 环境与每周巡检

## 环境基线

- 仓库：`liye20000/proxy-rules`，默认分支 `main`。
- 工作目录：仓库根目录；项目规范来自根目录 `AGENTS.md`。
- Python：3.13。
- Setup script：`python -m pip install pytest`。
- Secrets：空；不添加 PAT、GitHub Secret 或 `OPENAI_API_KEY`。
- Agent 网络：开启，域名列表选择 `All`，HTTP 方法只允许 `GET`、`HEAD`、`OPTIONS`；仅用于读取
  任意新服务的官方资料，不允许登录、上传或远端写入。
- 交付：从最新 `main` 建立 `codex/domain-<service>-<YYYYMMDD>` 分支。满足根目录 `AGENTS.md`
  自动门禁的纯新增域名创建 ready PR；其他变化创建草稿 PR 或报告。

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
