# proxy-rules · 代理规则自动同步系统

> 一处修改,四台设备(Windows PC / iMac / iPhone / iPad)自动同步代理路由规则。

![GitHub Actions](https://github.com/YOUR_USERNAME/proxy-rules/actions/workflows/generate.yml/badge.svg)

在 GitHub 上托管一份代理白名单数据源(`proxy-list.txt`),通过 GitHub Actions 自动转换成各客户端需要的规则格式。你只维护一份纯文本主源,所有平台自动同步。

> 本项目**只管路由规则,不管代理节点**。节点由你的第三方机场(订阅 URL)提供。

---

## ✨ 核心特性

- **一处维护**:只编辑一份纯文本 `proxy-list.txt`,每行一个域名。
- **自动转换**:GitHub Actions 监听改动,自动生成 V2RayN 用的 `v2rayn-rules.json`。
- **多端同步**:Windows(V2RayN)+ Apple 三端(Shadowrocket)统一订阅,自动拉取。
- **零依赖**:转换脚本仅用 Python 标准库,无第三方包。
- **轻量运维**:90% 的日常操作只需在 GitHub 网页点几下,2 分钟搞定。

---

## 🚀 快速开始

三步上手(完整流程见 [docs/quickstart.md](docs/quickstart.md)):

1. **创建仓库**:Fork 或用本项目作为模板创建你自己的 `proxy-rules` 仓库。
2. **拼订阅 URL**:用你的用户名替换占位符,得到两个 raw URL(见下方「订阅 URL 模板」)。
3. **配置客户端**:在 V2RayN / Shadowrocket 里填入订阅 URL(见 `docs/` 下各平台指南)。

---

## ⭐ 日常使用

这个项目的运维分为三层,按场景选用工具:

| 场景 | 工具 | 耗时 |
|---|---|---|
| 加 / 删 1~2 个域名 | GitHub 网页直接编辑 | 2 分钟 |
| 加新服务 / 智能整理 | Claude.ai 网页 Code 功能 | 5 分钟 |
| 改架构 / 排查 bug | PC 本地 Claude Code | 按需 |

→ **日常运维的核心参考,详细操作流程见 [docs/daily-ops.md](docs/daily-ops.md)。**

---

## 🏗️ 架构图

```
用户编辑 proxy-list.txt → git push(或网页 Commit)
                ↓
   GitHub Actions 监听到 push
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
├── proxy-list.txt            # 主源:代理白名单(你唯一需要手动改的文件)
├── v2rayn-rules.json         # 派生:V2RayN 规则(Actions 自动生成,勿手动改)
├── shadowrocket.module       # 派生:Shadowrocket 模块(推荐,叠加式;Actions 生成)
├── shadowrocket.conf         # 派生:Shadowrocket 配置(备选,替换式;Actions 生成)
├── generate.py               # 转换脚本(txt → json + module + conf)
├── .github/workflows/
│   └── generate.yml          # GitHub Actions 配置
├── tests/                    # generate.py 的单元测试
└── docs/                     # 用户文档(见下方导航)
```

---

## 📚 使用文档导航

- [docs/quickstart.md](docs/quickstart.md) — 5 分钟快速上手
- [docs/daily-ops.md](docs/daily-ops.md) — ⭐ 日常运维三层模式(必看)
- [docs/setup-v2rayn.md](docs/setup-v2rayn.md) — Windows V2RayN 配置
- [docs/setup-shadowrocket-iphone.md](docs/setup-shadowrocket-iphone.md) — iPhone 配置
- [docs/setup-shadowrocket-ipad.md](docs/setup-shadowrocket-ipad.md) — iPad 配置
- [docs/setup-shadowrocket-mac.md](docs/setup-shadowrocket-mac.md) — iMac(Apple Silicon)配置
- [docs/adding-rules.md](docs/adding-rules.md) — 如何添加 / 删除规则
- [docs/troubleshooting.md](docs/troubleshooting.md) — 故障排查
- [docs/architecture.md](docs/architecture.md) — 架构与原理(技术深入)

---

## ➕ 如何添加新规则

最常见的动作:只改 `proxy-list.txt`,**不要碰自动生成的 `v2rayn-rules.json` / `shadowrocket.module` / `shadowrocket.conf`**。在 GitHub 网页打开 `proxy-list.txt` → 铅笔图标编辑 → 在合适的分组加一行域名 → Commit。约 30 秒后 Actions 自动重新生成派生文件,各设备下次拉取订阅时同步。

详见 [docs/adding-rules.md](docs/adding-rules.md) 与 [docs/daily-ops.md](docs/daily-ops.md)。

---

## 🔗 订阅 URL 模板

把 `YOUR_USERNAME` 替换成你的 GitHub 用户名:

```
# V2RayN 专用(Windows)
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/v2rayn-rules.json

# Shadowrocket 专用(iPhone / iPad / iMac)— 推荐「模块」方式
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/shadowrocket.module

# Shadowrocket 备选「整份配置」方式(仅当节点来自独立的服务器订阅时)
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/shadowrocket.conf
```

> `proxy-list.txt` 是给你**手动编辑的主源**,不直接作为客户端订阅;客户端订阅上面**自动生成**的派生文件。Shadowrocket 默认用 `.module`(叠加在机场配置上、不动节点),详见 [docs/setup-shadowrocket-iphone.md](docs/setup-shadowrocket-iphone.md)。

---

## 📄 License

本项目使用 [MIT License](LICENSE)。请把 `LICENSE` 文件里的 `<YEAR>` 与 `<COPYRIGHT HOLDER>` 替换为你自己的信息。
