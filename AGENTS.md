# proxy-rules 维护规范（唯一权威）

本仓库维护严格代理白名单。所有代理、自动化代理和人工贡献者均以本文件为准；
`CLAUDE.md` 仅是兼容入口，不另行定义规则。

## 开工与交付

1. 从最新 `main` 建立 `codex/<主题>` 分支，不直接向 `main` 写入人工改动。
2. 自动维护只创建草稿 PR，绝不自动合并。
3. 修改后必须运行真实生成和完整测试：

   ```text
   python generate.py
   python -m pytest tests/ -q
   ```

4. PR 必须列出新增规则及匹配类型、依据、明确排除项、测试结果和三个派生产物变化。

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
- PR 运行生成与完整测试；bot 仅在非 PR 运行中、有实际变化时提交。
- Codex Cloud 使用 Python 3.13，Setup script 为 `python -m pip install pytest`。
- Agent 网络默认关闭；只有实时 Telegram 抓取任务需要访问 `stat.ripe.net`。
- 不引入 Codex GitHub Action，不保存 PAT、GitHub Secret 或 `OPENAI_API_KEY`。
- GitHub 连接失效时，仓库 Actions 和公开订阅必须仍能独立工作。

## 安全

任何令牌、Cookie、账号凭据和本地工具设置都不得进入仓库、日志、Issue 或 PR。
`.claude/settings.local.json` 被显式忽略；发现历史令牌时只报告位置并要求在提供方撤销，绝不复述值。
