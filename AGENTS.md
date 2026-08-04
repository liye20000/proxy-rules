# proxy-rules 维护规范（唯一权威）

本仓库维护严格代理白名单。所有代理、自动化代理和人工贡献者均以本文件为准；
`CLAUDE.md` 仅是兼容入口，不另行定义规则。

## 开工与交付

1. 默认在 Codex Cloud 从最新 `main` 建立分支，不依赖用户本地电脑。普通域名新增使用
   `codex/domain-<service>-<YYYYMMDD>`；其他维护使用 `codex/<主题>`。
2. 用户只需描述域名或服务需求；Codex 负责调查、修改、验证、推送分支和创建 PR。
3. 满足“受控全自动”门禁的纯新增域名 PR 创建为 ready 状态，CI 全绿后自动 squash 合并；
   其他改动只创建草稿 PR，不得自动合并。
4. 修改后必须运行真实生成和完整测试：

   ```text
   python generate.py
   python -m pytest tests/ -q
   ```

5. PR 必须列出新增规则及匹配类型、依据、明确排除项、测试结果和三个派生产物变化。
6. 对 ready 的安全域名 PR，Codex 必须继续跟踪到自动合并与 `main` 上的 `generate` 复验成功，
   再向用户报告可用结果；若门禁未合并或复验失败，报告具体原因，不把半成品当作完成。

### 受控全自动门禁

只有同时满足以下条件才允许无人审核自动合并：

- PR 来自本仓库所有者、目标为 `main`，分支符合 `codex/domain-<service>-<YYYYMMDD>`，且不是草稿。
- `generate` 对当前 PR head 的真实生成、派生产物校验和完整 pytest 全部成功。
- 只改动 `proxy-list.txt` 与三个派生产物，且至少新增一个有效规则、不删除任何旧规则。
- 不新增 `apple.com`、`cloudflare.com` 等分类器列出的高影响共享根域；其精确主机 `exact:` 仍可自动合并。

删除规则、修改 IP 主源、脚本、测试、文档、工作流或安全配置，以及来源冲突和大范围扩张，
一律创建草稿 PR 或报告并等待用户决定。自动合并分类器必须从可信 `main` 执行，绝不检出或
运行 PR 中的分类器/工作流代码。

## 单一数据源

- `proxy-list.txt`：人工维护的域名主源。
- `proxy-ip-list.txt`：人工维护的 CIDR 主源。
- `proxy-ip-auto.txt`：Telegram 自动数据，不得手改。
- `v2rayn-rules.json`、`shadowrocket.module`、`shadowrocket.conf`：由 `generate.py` 派生，不得手改。

域名语法：

- `example.com`：匹配该域名和所有子域名；生成 V2RayN `domain:` 与 Shadowrocket `DOMAIN-SUFFIX`。
- `exact:host.example.com`：只匹配该主机；生成 V2RayN `full:` 与 Shadowrocket `DOMAIN`。

加入规则前先检查是否已经被普通后缀规则覆盖。共享面很大的根域（例如 `apple.com`、
`cloudflare.com`）不得为解决单一依赖而加入；应优先使用 `exact:`，无法避免扩大范围时由用户决定。

## 服务级域名调查

优先使用官方文档，核对网页、登录、API、静态资源、文件上传下载和实时连接。
广告、统计、客服、遥测、支付和企业 SSO 默认排除，除非它们是用户要求的核心功能。

当前 AI 基线来源：

- OpenAI：<https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps>
- Gemini：<https://knowledge.workspace.google.com/admin/generative-ai/gemini-app/gemini-app-firewall-settings>
- Google AI：<https://ai.google/>
- Google Labs：<https://labs.google/>

## Telegram 安全门禁

`fetch_telegram_ips.py` 必须把每个 ASN 都视为必需数据源。任一 ASN 请求异常、返回空列表，
或包含非法 CIDR 时整次失败，不得覆盖旧文件。抓取与生成完成后必须通过完整 pytest 才能提交。

## GitHub Actions 与云端代理

- 两个写入工作流共用 `proxy-rules-writer` concurrency group。
- `generate` 在相关 PR 上以只读权限自动运行生成与完整测试，合并到 `main` 后自动复验；用户无需手动触发。
- `safe-domain-automerge` 只消费成功的 `generate` 结果，并按上述门禁自动 squash 合并安全 PR。
- Telegram ASN 更新每周一 03:00 UTC（北京时间 11:00）自动运行；`workflow_dispatch` 仅作紧急补跑。
- bot 仅在非 PR 运行中、有实际变化时提交。
- Codex Cloud 使用 Python 3.13，Setup script 为 `python -m pip install pytest`。
- Cloud Agent 网络开启为全域只读，只允许 `GET`、`HEAD`、`OPTIONS`，用于查询任意新服务的官方资料；
  禁止登录、上传和远端写请求。Telegram 抓取仍由 GitHub Actions 访问 `stat.ripe.net`。
- 不引入 Codex GitHub Action，不保存 PAT、GitHub Secret 或 `OPENAI_API_KEY`。
- GitHub 连接失效时，仓库 Actions 和公开订阅必须仍能独立工作。

## 安全

任何令牌、Cookie、账号凭据和本地工具设置都不得进入仓库、日志、Issue 或 PR。
`.claude/settings.local.json` 被显式忽略；发现历史令牌时只报告位置并要求在提供方撤销，绝不复述值。
