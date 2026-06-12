# 架构与原理

面向想理解项目内部机制的读者。日常使用不需要读本文。

---

## 1. 完整数据流

```
                  ┌──────────────────────────────────┐
                  │     GitHub Repository             │
                  │                                  │
                  │   proxy-list.txt    (主源:按域名)  │
                  │   proxy-ip-list.txt (主源:按 IP 段)│
                  │            ↓ generate.py         │
                  │   ┌────────────┴────────────┐    │
                  │   ↓                         ↓    │
                  │ v2rayn-rules.json   shadowrocket.module │
                  │   (派生)              (派生,另有 .conf) │
                  └─────┬──────────────────────┬─────┘
                        │ HTTP 订阅(raw URL)   │
                        ↓                      ↓
              ┌────────────────┐    ┌──────────────────────┐
              │ Windows V2RayN │    │  Apple 三端 Shadowrocket │
              │ 订阅:          │    │  订阅:               │
              │ v2rayn-rules   │    │  shadowrocket.module  │
              │ .json          │    │  (模块,叠加不动节点)   │
              └────────────────┘    └──────────────────────┘
```

核心思路:**单一数据源(Single Source of Truth)+ 自动派生**。主源有三份纯文本(均可选,缺失按空处理):

- `proxy-list.txt` —— 按域名走代理(手动)。
- `proxy-ip-list.txt` —— 按 IP 段走代理的**手动**补充。
- `proxy-ip-auto.txt` —— 按 IP 段走代理的**自动**部分,由 `fetch_telegram_ips.py` 每天抓取 Telegram 各 ASN 的 BGP 网段(数据源 RIPEstat),**切勿手动编辑**。

生成时两份 IP 主源合并去重。各客户端需要的格式由 CI 自动生成。

---

## 2. 为什么需要派生出两种格式

不同客户端的规则配置格式不兼容,且**都无法直接消费裸域名列表**:

| 客户端 | 格式 | 订阅的文件 |
|---|---|---|
| V2RayN v6.x | Xray-core JSON(路由规则数组) | `v2rayn-rules.json` |
| Shadowrocket | 模块(`[Rule]`,叠加式,推荐) | `shadowrocket.module` |
| Shadowrocket | 完整配置(`[General]` + `[Rule]`,替换式,备选) | `shadowrocket.conf` |

- **V2RayN** 需要结构化的 JSON 路由规则。
- **Shadowrocket** 需要含 `[Rule]` 段落的配置或模块;它**不能**直接订阅一个「每行一个域名」的纯文本(那只能作为某条规则引用的 `DOMAIN-SET`,无法单独成为订阅)。因此必须由 `generate.py` 生成。

**为什么 Shadowrocket 优先用「模块」而非「配置」**:用户的节点通常存在机场给的整份配置(如 `default.conf`)里,而且那份配置自带很多规则(如 `apple-relay`→PROXY、`baidu`→DIRECT)。若用我们「只含规则、不含节点」的 `.conf` 去**替换**生效配置,节点会丢失、原有规则也被换掉。而**模块(module)会叠加**在当前配置之上、规则优先级更高,只改路由、不动节点——因此推荐 `shadowrocket.module`。

**模块是一套「严格白名单,主导全部路由」**:`shadowrocket.module` 含完整规则(白名单 → PROXY、局域网/国内 → DIRECT、`FINAL,DIRECT` 兜底)。由于模块优先级高于配置,这套规则会**接管全部路由**——白名单域名走代理、其余一律直连;用户机场配置里原有的路由规则被**覆盖**(若仍想代理某域名,加进 `proxy-list.txt` 即可)。节点不受影响,仍由机场配置提供。`shadowrocket.conf` 是等价的**完整配置**(多了 `[General]`),用于「整份替换」、且仅当节点来自独立服务器订阅时使用。

> 设计取舍:这里默认让模块**主导路由**(严格白名单),而非"在原配置上只追加几个 PROXY 域名"的纯叠加——因为本项目的目标就是一套统一、可预期的白名单。若需纯叠加模式,改 `generate_shadowrocket_module` 去掉 `FINAL` 兜底即可。

> 两者都**只含路由规则,不含任何节点 / 密码**。策略关键字 `PROXY` 表示「走用户在 Shadowrocket 首页选中的节点」,节点来自用户自己的机场。这也是仓库可以保持 Public 的原因之一。

所以主源 `proxy-list.txt` 本身不直接给客户端订阅,而是作为人类编辑的单一来源,派生出客户端可消费的文件。

---

## 3. Python 脚本的工作原理

`generate.py` 只用标准库(`json` / `re` / `ipaddress` / `pathlib` / `sys`),核心函数:

- `parse_domain_list(text)`:把纯文本解析成干净的域名列表——去注释、去空行、去行内注释、小写化、去重(保持顺序)、正则校验基本域名格式。
- `parse_ip_list(text)`:解析 `proxy-ip-list.txt`,用 `ipaddress` 校验并规范化为 CIDR 网段(IPv4 / IPv6),去注释、去重;非法行警告跳过。
- `generate_v2rayn_rules(domains, cidrs)`:生成 V2RayN(Xray-core)路由规则:
  1. **proxy(域名)**:所有白名单域名加 `domain:` 前缀 → 走代理。
  2. **proxy(IP 段)**:`cidrs` 非空时新增一条,`ip` 数组放 CIDR → 走代理;**排在 CN 直连之前**(Telegram 等数据中心 IP 不属于 CN,否则会落到兜底被直连)。
  3. **block**:`geosite:category-ads-all` → 拦截广告。
  4. **direct**:`geosite:private` / `geosite:cn` + `geoip:private` / `geoip:cn` → 国内与局域网直连。
  5. **direct 兜底**:`port: 0-65535` → 其余全部直连。
- `_proxy_whitelist_lines(domains)`:构造共用的「白名单 `DOMAIN-SUFFIX,xxx,PROXY`」规则行。
- `_proxy_ip_lines(cidrs)`:构造共用的「IP 段 → PROXY」规则行(IPv4 用 `IP-CIDR`、IPv6 用 `IP-CIDR6`,均带 `no-resolve`)。
- `_shadowrocket_full_rule_lines(domains, cidrs)`:白名单域名 + IP 段(在国内直连之前)+ 私有网段/`GEOIP,CN,DIRECT` + `FINAL,DIRECT`,构成完整白名单(供 .conf 用)。
- `generate_shadowrocket_module(domains, cidrs)`:生成 Shadowrocket **模块**(仅 `[Rule]`,完整严格白名单——含 `FINAL,DIRECT`,主导全部路由,推荐)。
- `generate_shadowrocket_conf(domains, cidrs)`:生成 Shadowrocket **完整配置**(`[General]` + 完整 `[Rule]`,替换式,备选)。
- `main()`:读三份主源(`proxy-list.txt` + 合并 `proxy-ip-list.txt` / `proxy-ip-auto.txt`)→ 解析 → 同时写出 `v2rayn-rules.json`(2 空格缩进、`ensure_ascii=False`、末尾换行)、`shadowrocket.module` 与 `shadowrocket.conf`。IP 主源缺失时按空列表处理。

`fetch_telegram_ips.py`(独立脚本,只用标准库):查询 Telegram 各 ASN(`62041 / 62014 / 59930 / 44907 / 211157`)在 RIPEstat 的 `announced-prefixes`,汇总去重、按 v4/v6 排序后写出 `proxy-ip-auto.txt`。**任一 ASN 抓取失败或结果为空 → 非零退出且不写文件**,避免清空规则。

错误处理:域名主源不存在、解析后域名为空都会打印错误并返回退出码 1。

规则顺序很重要:两种格式都按自上而下 / 数组顺序匹配,白名单(PROXY)在最前,兜底(DIRECT)在最后。

---

## 4. GitHub Actions 工作流原理

**`.github/workflows/generate.yml`**(主源改动 → 重新生成):

- **触发**:push 到 `main` 且改动命中 `proxy-list.txt` / `proxy-ip-list.txt` / `generate.py` / 工作流自身;或手动 `workflow_dispatch`。
- **权限**:`contents: write`,允许 bot 提交回仓库。
- **步骤**:checkout → 装 Python → 跑 `generate.py` → `git add` 三个派生文件后用 `git diff --cached --quiet` 判断是否有变化 → 有变化才以 `github-actions[bot]` 身份 commit & push。

**`.github/workflows/update-telegram-ips.yml`**(每天自动更新 Telegram IP 段):

- **触发**:`schedule` 每天 03:00 UTC;或手动 `workflow_dispatch`。
- **步骤**:跑 `fetch_telegram_ips.py` 抓取并写 `proxy-ip-auto.txt` → 跑 `generate.py` 重新生成 → 有变化才提交 `proxy-ip-auto.txt` 与三个派生文件。自身在一个 job 内完成「抓取 + 生成 + 提交」,不依赖 `generate.yml`(bot 用默认 token 的 push 默认不会触发别的工作流)。

**防死循环**:`generate.yml` 的 `paths` 过滤器**只监听 `proxy-list.txt` / `proxy-ip-list.txt` / `generate.py` / 工作流自身,不监听派生文件**。所以 bot 提交生成结果不会再次触发自己。

---

## 5. 安全性说明(为什么仓库可以 Public)

- 仓库内容只是**公开域名的白名单**和转换脚本,**不含任何节点信息、密钥、账号**。
- 公开反而简化订阅:raw URL 无需鉴权即可被客户端拉取。
- 鉴权用 fine-grained PAT 且范围仅限本仓库;即便泄露,影响也被限制在这一个仓库内(详见根目录设计文档第 11 节与附录 D)。

---

## 6. 性能考虑

- **订阅频率**:客户端按 1~24 小时的间隔拉取。raw URL 由 GitHub / CDN 缓存,通常有几分钟的缓存延迟,属正常现象。
- **Actions 时长**:从 push 到生成完成约 30 秒。
- **文件体积**:纯文本与 JSON 都很小(KB 级),拉取开销可忽略。

---

## 7. 未来扩展(本次未实现)

留作方向参考,当前不实现:

1. **多 client format 输出**:扩展 `generate.py` 生成 Clash YAML / Surge `.conf` / Sing-box JSON。
2. **GitHub Pages**:把 `docs/` 部署为静态网站。
3. **pre-commit 钩子**:提交前自动跑 `pytest`。
4. **dependabot**:自动升级 Actions 版本。
5. **多分组导出**:为不同设备生成不同子集的规则。
