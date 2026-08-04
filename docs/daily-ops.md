# 日常运维：Codex Cloud 受控全自动

默认入口是在连接本仓库的 Codex Cloud 中直接描述目标。云端调查依赖、修改主源、生成产物、
运行测试并创建 PR；满足安全门禁的纯新增域名会在 CI 全绿后自动合并。用户只需提出需求，
不需要保持本地电脑开机、手动运行 Actions 或审核常规域名 PR。GitHub 网页编辑仅作应急备用。
Codex Cloud 会继续跟踪到自动合并和 `main` 复验成功后再报告结果；门禁未通过时只报告原因，
不会把仍停在 PR 中的变化当作已经发布。

## 新增域名

单个已知域名可以直接说：

```text
把 example.com 加入代理白名单。
```

服务级请求建议说明功能边界：

```text
把某某服务加入白名单，检查网页、登录、API 和核心 CDN，
排除广告和遥测域名，完成验证后发布安全结果。
```

Codex 会先判断已有后缀规则是否已经覆盖，再选择语法：

- `example.com`：整个站点与所有子域名。
- `exact:host.example.com`：只有一个主机，避免扩大代理范围。

涉及 `apple.com`、`cloudflare.com` 等共享根域的扩大匹配，必须由用户决定。

## 自动发布门禁

每个域名 PR 仍需写明：

- 新增的规则，以及普通/精确匹配方式。
- 官方来源或可复现的实际依赖依据。
- 明确排除的广告、统计、客服、遥测、支付或企业 SSO 端点。
- `python generate.py` 和完整 pytest 结果。
- `v2rayn-rules.json`、`shadowrocket.module`、`shadowrocket.conf` 的变化。

`safe-domain-automerge` 只自动合并来自本仓库所有者、命名符合规范、CI 对当前 head 成功，
且只新增域名主源与三个派生产物的 PR。删除规则、共享根域、IP、脚本、测试、文档、工作流
或安全配置变更都会保留为草稿 PR 或报告，等待用户决定。合并后 Actions 会再次生成和验证。

## 应急网页编辑

无法使用 Codex 时，可在 GitHub 编辑 `proxy-list.txt` 或 `proxy-ip-list.txt` 并创建 PR。
不得直接编辑 `proxy-ip-auto.txt` 或三个派生产物。PR 检查会执行真实生成和完整 pytest。

## Telegram 自动维护

每周一北京时间 11:00，工作流从 RIPEstat 查询五个 Telegram ASN。任一 ASN 为空、CIDR 非法或响应异常时，
本次工作流失败且保留上一份文件。两个写入工作流使用同一 concurrency group，避免并发推送。
紧急需要刷新时，Codex 可通过 `gh workflow run update-telegram-ips.yml --ref main` 补跑，
用户无需进入 GitHub Actions 页面操作。

## 每周维护

每周一 09:00（Asia/Shanghai）的 Codex 云端任务检查最近七天 Actions、raw 订阅、Telegram
数据和 OpenAI/Google 官方域名清单。健康且无变化时不创建内容；安全新增通过门禁自动合并；
删除、冲突或大范围扩张只报告。详情见 [`cloud-maintenance.md`](cloud-maintenance.md)。

## 凭据

日常流程不需要向对话粘贴 PAT。GitHub 连接应限制到本仓库；仓库和云端环境不保存 PAT、
GitHub Secret 或 `OPENAI_API_KEY`。如果旧 PAT 曾出现在本地文件中，必须到 GitHub 设置撤销，
删除本地文件本身不能使已签发令牌失效。
