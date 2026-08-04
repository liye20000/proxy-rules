# proxy-rules · 代理规则自动同步系统

> 一处修改,四台设备(Windows PC / iMac / iPhone / iPad)自动同步代理路由规则。

![GitHub Actions](https://github.com/liye20000/proxy-rules/actions/workflows/generate.yml/badge.svg)

在 GitHub 上托管一份代理白名单数据源(`proxy-list.txt`),通过 GitHub Actions 自动转换成各客户端需要的规则格式。你只维护一份纯文本主源,所有平台自动同步。

> 本项目**只管路由规则,不管代理节点**。节点由你的第三方机场(订阅 URL)提供。

---

## ✨ 核心特性

- **一处维护**:域名主源是 `proxy-list.txt`;普通域名匹配子域,`exact:` 可精确到单一主机。
- **自动转换**:GitHub Actions 监听改动,自动生成 V2RayN 用的 `v2rayn-rules.json`。
- **多端同步**:Windows(V2RayN)+ Apple 三端(Shadowrocket)统一订阅,自动拉取。
- **零依赖**:转换脚本仅用 Python 标准库,无第三方包。
- **受控自动发布**:安全的纯新增域名 PR 在 CI 全绿后自动合并；高风险改动仍停下报告。

---

## 🚀 快速开始

三步上手(完整流程见 [docs/quickstart.md](docs/quickstart.md)):

1. **创建仓库**:Fork 或用本项目作为模板创建你自己的 `proxy-rules` 仓库。
2. **拼订阅 URL**:用你的用户名替换占位符,得到两个 raw URL(见下方「订阅 URL 模板」)。
3. **配置客户端**:在 V2RayN / Shadowrocket 里填入订阅 URL(见 `docs/` 下各平台指南)。

---

## ⭐ 日常使用

默认直接把目标告诉 Codex Cloud，由它调查依赖、生成产物、运行测试并发布结果:

| 场景 | 工具 | 耗时 |
|---|---|---|
| 已知单个域名 | Codex Cloud → 自动验证与合并 | 约 2 分钟 |
| 完整服务 / AI 域名审计 | Codex Cloud → 自动验证与安全门禁 | 约 5–15 分钟 |
| 紧急备用 | GitHub 网页创建 PR | 约 2 分钟 |

→ **日常运维的核心参考,详细操作流程见 [docs/daily-ops.md](docs/daily-ops.md)。**

---

## 🏗️ 架构图

```
Codex Cloud 从最新 main 创建分支 → 修改主源、生成、pytest → PR
                ↓ generate CI 全绿 + 安全分类器
                ↓
   安全纯新增自动合并；高风险变更暂停报告
                ↓
   GitHub Actions 监听到 main push
                ↓
   启动 Ubuntu 虚拟机 → 安装 Python → 执行 generate.py
                ↓
   git diff 检查 v2rayn-rules.json 是否变化
                ↓
   有变化 → 以 bot 身份自动 commit + push
                ↓
   各客户端按订阅间隔(1~24 小时)自动拉取
                ↓
   四台设备规则更新完成(从 push 到 Actions 完成 ≈ 30 秒)
```

数据流:

```
                    proxy-list.txt (主源)
                          │ generate.py
            ┌─────────────┴─────────────┐
            ↓                           ↓
   v2rayn-rules.json (派生)      shadowrocket.module (派生)
            │ V2RayN 订阅                │ Shadowrocket 模块订阅
            ↓                           ↓
       Windows PC                iPhone / iPad / iMac
```

> 另有 `shadowrocket.conf`(整份配置,替换式)作为备选;Apple 端**默认推荐用 `.module`**(叠加式,不动机场节点)。

---

## 📁 目录结构

```
proxy-rules/
├── README.md                 # 项目主页(本文件)
├── LICENSE                   # MIT 协议
├── .gitignore                # Python 标准 gitignore
├── AGENTS.md                 # 代理维护的唯一权威规范
├── proxy-list.txt            # 主源:代理白名单(你唯一需要手动改的文件)
├── v2rayn-rules.json         # 派生:V2RayN 规则(Actions 自动生成,勿手动改)
├── shadowrocket.module       # 派生:Shadowrocket 模块(推荐,叠加式;Actions 生成)
├── shadowrocket.conf         # 派生:Shadowrocket 配置(备选,替换式;Actions 生成)
├── generate.py               # 转换脚本(txt → json + module + conf)
├── classify_safe_domain_pr.py # 受控自动合并分类器
├── .github/workflows/
│   ├── generate.yml          # PR 验证与主源生成
│   ├── safe-domain-automerge.yml # 安全域名 PR 自动合并
│   └── update-telegram-ips.yml # 每周 Telegram ASN 更新
├── tests/                    # generate.py 的单元测试
└── docs/                     # 用户文档(见下方导航)
```

---

## 📚 使用文档导航

- [docs/quickstart.md](docs/quickstart.md) — 5 分钟快速上手
- [docs/daily-ops.md](docs/daily-ops.md) — ⭐ Codex + PR 日常运维(必看)
- [docs/cloud-maintenance.md](docs/cloud-maintenance.md) — Codex Cloud 与每周巡检
- [docs/setup-v2rayn.md](docs/setup-v2rayn.md) — Windows V2RayN 配置
- [docs/setup-shadowrocket-iphone.md](docs/setup-shadowrocket-iphone.md) — iPhone 配置
- [docs/setup-shadowrocket-ipad.md](docs/setup-shadowrocket-ipad.md) — iPad 配置
- [docs/setup-shadowrocket-mac.md](docs/setup-shadowrocket-mac.md) — iMac(Apple Silicon)配置
- [docs/adding-rules.md](docs/adding-rules.md) — 如何添加 / 删除规则
- [docs/troubleshooting.md](docs/troubleshooting.md) — 故障排查
- [docs/architecture.md](docs/architecture.md) — 架构与原理(技术深入)

---

## ➕ 如何添加新规则

最常见的动作是告诉 Codex Cloud“把 example.com 加入代理白名单”。
整个站点及子域使用 `example.com`；只代理一个主机使用 `exact:host.example.com`。
不要手改三个派生产物。安全的纯新增规则会在真实生成与完整 pytest 通过后自动合并；
高风险范围才会暂停询问。各设备在下一次订阅刷新时同步。

详见 [docs/adding-rules.md](docs/adding-rules.md) 与 [docs/daily-ops.md](docs/daily-ops.md)。

---

## 🔗 订阅 URL 模板

以下订阅 URL 已填好你的用户名 `liye20000`,可直接复制使用:

```
# V2RayN 专用(Windows)
https://raw.githubusercontent.com/liye20000/proxy-rules/main/v2rayn-rules.json

# Shadowrocket 专用(iPhone / iPad / iMac)— 推荐「模块」方式
https://raw.githubusercontent.com/liye20000/proxy-rules/main/shadowrocket.module

# Shadowrocket 备选「整份配置」方式(仅当节点来自独立的服务器订阅时)
https://raw.githubusercontent.com/liye20000/proxy-rules/main/shadowrocket.conf
```

> `proxy-list.txt` 是给你**手动编辑的主源**,不直接作为客户端订阅;客户端订阅上面**自动生成**的派生文件。Shadowrocket 默认用 `.module`(叠加在机场配置上、不动节点),详见 [docs/setup-shadowrocket-iphone.md](docs/setup-shadowrocket-iphone.md)。

---

## 📄 License

本项目使用 [MIT License](LICENSE)。请把 `LICENSE` 文件里的 `<YEAR>` 与 `<COPYRIGHT HOLDER>` 替换为你自己的信息。
