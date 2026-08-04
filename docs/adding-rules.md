# 添加、删除与审核规则

默认让 Codex Cloud 从最新 `main` 创建分支并完成调查、生成、测试和发布。普通安全新增只修改
域名主源与三个派生产物并创建 ready PR；需要修改测试、文档或代码时改建草稿 PR。
`v2rayn-rules.json`、`shadowrocket.module`、`shadowrocket.conf` 必须由生成器更新。

## 域名语法

```text
example.com
exact:api.vendor.example
```

- 普通规则匹配自身及所有子域；生成 V2RayN `domain:` 和 Shadowrocket `DOMAIN-SUFFIX`。
- `exact:` 只匹配指定主机；生成 V2RayN `full:` 和 Shadowrocket `DOMAIN`。
- 不写协议、路径、端口或通配符，域名会被小写化并去重。

新增前先检查现有普通规则是否已覆盖。例如存在 `google.com` 时，不要重复加入
`accounts.google.com`。如果依赖位于共享基础设施，应加入精确主机，不要扩大到整个
`apple.com` 或 `cloudflare.com`。

## 服务级请求

Codex 应优先查官方文档，并核对网页、登录、API、静态资源、文件和实时连接。广告、统计、
客服、遥测、支付和企业 SSO 默认排除。PR 要列出依据和排除项。

## CIDR

- `proxy-ip-list.txt`：人工维护，每行一个 IPv4/IPv6 CIDR。
- `proxy-ip-auto.txt`：Telegram 自动数据，不得手改。

Telegram 每周任务查询 RIPEstat。任一 ASN 为空、包含非法 CIDR 或请求异常时整次失败并保留
上一份文件。

## 验证与发布

```text
python generate.py
python -m pytest tests/ -q
```

检查三种产物的规则顺序和匹配类型。安全纯新增 PR 在 CI 与可信自动门禁通过后自动合并；
客户端在下一次订阅更新时生效，紧急时可手动刷新。

删除现有规则、代理范围明显扩大、修改 IP/代码/测试/文档/工作流，或官方来源冲突时，
创建草稿 PR 或只报告，不自动合并。
