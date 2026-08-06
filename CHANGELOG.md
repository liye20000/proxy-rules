# 变更记录

本文件记录对规则系统的重要改动(主源结构、生成逻辑、自动化等)。日常加删单个域名不在此列出。

## 2026-08-04 — 自动维护触发策略

- Telegram ASN 更新由每日改为每周一 03:00 UTC（北京时间 11:00），保留手动紧急补跑入口。
- 域名变更默认由 Codex Cloud 完成；安全纯新增 PR 经 `generate` 和可信分类器后自动合并，
  删除、共享根域、代码、测试、文档、工作流与安全配置变更仍需人工决定。
- PR 验证降为只读仓库权限；自动合并工作流只从可信 `main` 运行且不执行 PR 代码。
- 补充 Codex Cloud 首次运行验收、手机端任务入口及 Cloud 与本地工作区的同步边界。

## 2026-08-03 — Codex Cloud 接管、精确主机与 AI 白名单

- 新增根目录 `AGENTS.md` 作为唯一维护规范，`CLAUDE.md` 缩减为兼容指针；旧设计文档标记为历史资料。
- `proxy-list.txt` 支持 `exact:`：V2RayN 生成 `full:`，Shadowrocket 生成 `DOMAIN`，普通规则完全兼容。
- 补齐 OpenAI/ChatGPT/Codex 的精确共享端点，以及 Google AI、Labs、DeepMind、Flow、Jules、Opal 等域名；不扩大到整个 `apple.com` 或 `cloudflare.com`。
- Telegram 任一 ASN 为空、响应含非法 CIDR或请求异常时整次失败并保留旧文件。
- Actions 升级到 checkout/setup-python v7、固定 Python 3.13、完整 pytest、PR 验证和共享写入 concurrency group。
- 日常流程改为 Codex 创建草稿 PR、用户审核合并；不使用 PAT 对话粘贴、`OPENAI_API_KEY` 或 Codex GitHub Action。

## 2026-06-12 — Telegram IP 段自动化 + 按 IP 段走代理

新增「按 IP 段走代理」能力,并让 Telegram 的 IP 段全自动维护。

**主源现在有三份(均可选,生成时合并去重):**

| 文件 | 谁维护 | 用途 |
|---|---|---|
| `proxy-list.txt` | 手动 | 按**域名**走代理 |
| `proxy-ip-list.txt` | 手动 | 按 **IP 段**(CIDR)走代理的额外补充 |
| `proxy-ip-auto.txt` | **机器人每天**(切勿手改) | Telegram 各 ASN 的 BGP 网段,由 `fetch_telegram_ips.py` 抓取 |

**自动化:**
- `fetch_telegram_ips.py` 查 Telegram 5 个 ASN(`62041 / 62014 / 59930 / 44907 / 211157`)在 RIPEstat 的宣告前缀,写入 `proxy-ip-auto.txt`;抓取失败或为空时**非零退出且不写文件**,绝不清空规则。
- 工作流 `update-telegram-ips.yml` 每天 03:00 UTC(也可手动 Run workflow)执行:抓取 → `generate.py` 重新生成 → 有变化才提交。
- 所以 **Telegram 的 IP 段无需人工维护**,改动最多一天内自动跟上。

**生成结果:**
- V2RayN(`v2rayn-rules.json`):新增一条独立 `proxy` 路由,`ip` 数组放 CIDR,**排在 CN 直连之前**(Telegram 等数据中心 IP 不属于 CN,否则会被兜底直连)。
- Shadowrocket(`.module` / `.conf`):`IP-CIDR / IP-CIDR6 ...,PROXY,no-resolve`,同样排在 `GEOIP,CN,DIRECT` 之前。

**客户端无需任何改动**:订阅的派生文件 URL 不变,刷新订阅即可拿到含 IP 段的新规则。

> 注:Telegram 的网页/登录/`t.me`/下载仍走域名(`telegram.org`、`t.me` 等在 `proxy-list.txt`);IP 段负责 App 的 MTProto 消息收发。两者配合才完整。
