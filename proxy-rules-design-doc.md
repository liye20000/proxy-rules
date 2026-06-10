# 代理规则自动同步系统 - 项目设计文档

> **文档类型**：工程设计规范(Design Spec)
> **目标读者**:Claude Code(自动化实施)
> **项目代号**:`proxy-rules`
> **版本**:1.0

---

## 1. 项目概述

### 1.1 一句话定义

在 GitHub 上托管一份代理白名单数据源,通过 GitHub Actions 自动适配多个客户端,让用户**一处修改、四台设备(Windows PC / iMac / iPhone / iPad)自动同步**。

### 1.2 用户场景

用户有以下设备和工具:

| 平台 | 客户端 | 备注 |
|---|---|---|
| Windows | V2RayN v6.45 | 主力开发机 |
| iMac | Shadowrocket(iOS 版) | M2 Apple Silicon,与 iPhone 共享购买 |
| iPhone | Shadowrocket | 已付费 |
| iPad | Shadowrocket | 与 iPhone 共享购买 |

代理节点由第三方机场提供(订阅 URL 方式),**本项目不管节点,只管路由规则**。

### 1.3 解决的问题

不同平台的客户端使用不同的规则配置格式:

- V2RayN:Xray-core JSON
- Shadowrocket:纯文本 / Clash 系语法

无法直接共用同一份规则文件。**本项目通过 GitHub Actions 自动化转换**,让用户只维护一份纯文本主源,所有平台自动同步。

### 1.4 不在范围内的功能

- ❌ 代理服务器节点的管理(机场已处理)
- ❌ 客户端软件的开发或修改
- ❌ 用户系统层面的 VPN 配置

### 1.5 项目生命周期与运维模式

本项目采用**三层混合运维模式**,明确每个动作用什么工具:

| 阶段 | 工具 | 频率 | 触发条件 |
|---|---|---|---|
| **一次性建设** | PC 本地 Claude Code | 仅 1 次 | 项目初始化、重大重构 |
| **日常增删规则** | GitHub 网页(手机/电脑浏览器) | 高频 | 加 / 删 1~2 个域名 |
| **复杂智能任务** | Claude.ai 网页/手机 App 的 Code 功能 | 低频 | 批量整理、查漏补缺、规则审计 |

**设计意图**:简单的事用最简单的工具,复杂的事才动用 AI。避免"每改一个域名都得打开 Claude Code"的过度工程化。

**对 Claude Code 的要求**:本次实施(一次性建设阶段)结束后,Claude Code 必须把这三层运维流程写进交付文档,让用户清楚日常该用哪种方式操作。详见第 5 节 `docs/daily-ops.md`。

### 1.6 鉴权方式:双 PAT 设计

本项目**全程使用 GitHub Personal Access Token (PAT) 进行鉴权**,不使用密码,不使用浏览器 OAuth(避免人工干预)。

为安全和职责分离,设计两个独立的 PAT:

| Token | 用途 | 期限 | 权限范围 | 生命周期 |
|---|---|---|---|---|
| **PAT-Deploy** | 一次性建设阶段使用 | 30 天(或更短) | All repos(因仓库尚未创建)+ Contents/Actions/Workflows/Administration: Read/Write | 部署完成后**立即撤销** |
| **PAT-DailyOps** | 长期日常运维 | 1 年 | Only `proxy-rules` 仓库 + Contents (Read/Write) + Actions (Read) | 长期保留,过期后续期 |

**核心安全原则**:
- ❌ Claude Code **永远不接受用户名/密码**(GitHub 2021 年已废除密码鉴权)
- ❌ Claude Code **永远不把 PAT 写入文件、commit message、日志输出**
- ✅ PAT 仅通过环境变量 `GH_TOKEN` 传递给 `gh` CLI
- ✅ 部署完成后,Claude Code 必须**显式提示用户撤销 PAT-Deploy**

完整鉴权流程见第 11 节"安全与鉴权规范"。

---

## 2. 总体架构

### 2.1 数据流

```
                  ┌──────────────────────────────┐
                  │     GitHub Repository         │
                  │                              │
                  │   proxy-list.txt (主源)       │
                  │       ↓ generate.py          │
                  │   v2rayn-rules.json (派生)    │
                  └──────────────┬───────────────┘
                                 │ HTTP 订阅
            ┌────────────────────┼────────────────────┐
            ↓                    ↓                    ↓
   ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐
   │ Windows V2RayN │  │  Apple 三端       │  │  (未来扩展)      │
   │                │  │  Shadowrocket     │  │                 │
   │ 订阅:          │  │                  │  │                 │
   │ v2rayn-rules   │  │  订阅:           │  │                 │
   │ .json          │  │  proxy-list.txt  │  │                 │
   └────────────────┘  └──────────────────┘  └─────────────────┘
```

### 2.2 自动化流水线

```
用户编辑 proxy-list.txt → git push
                ↓
   GitHub Actions 监听到 push
                ↓
   启动 Ubuntu 虚拟机 → 安装 Python
                ↓
   执行 generate.py(读 txt 转 json)
                ↓
   git diff 检查 v2rayn-rules.json 是否变化
                ↓
   有变化 → 自动 commit + push
                ↓
   各客户端按订阅间隔(1~24 小时)自动拉取
                ↓
   四台设备规则更新完成
```

整个过程从 push 到 Actions 完成 ≈ 30 秒。

---

## 3. 技术选型(已确定,不需要重新评估)

| 项 | 选择 | 理由 |
|---|---|---|
| 代码托管 | GitHub | 免费、Actions 强大、raw URL 适合订阅 |
| CI/CD | GitHub Actions | 免费、配置简单、原生集成 |
| 转换脚本语言 | Python 3 | 跨平台、生态成熟、JSON 处理简单 |
| 主源格式 | 纯文本(每行一域名) | 极简、人类可读、对 git diff 友好 |
| V2RayN 规则格式 | Xray-core JSON | V2RayN v6.x 的订阅功能要求此格式 |
| 仓库可见性 | Public | 内容无敏感信息,简化订阅 URL |
| License | MIT | 开源宽松,允许他人使用 |

---

## 4. 仓库目录结构

Claude Code 需要在仓库根目录创建以下完整结构:

```
proxy-rules/
├── README.md                          # 项目主页
├── LICENSE                            # MIT 协议
├── .gitignore                         # Python 标准 gitignore
│
├── proxy-list.txt                     # 主源:代理白名单
├── v2rayn-rules.json                  # 派生:V2RayN 规则(由 Actions 生成)
├── generate.py                        # 转换脚本
│
├── .github/
│   └── workflows/
│       └── generate.yml               # GitHub Actions 配置
│
├── tests/
│   ├── test_generate.py               # 转换脚本单元测试
│   └── fixtures/
│       ├── sample-input.txt
│       └── expected-output.json
│
└── docs/                              # 用户文档
    ├── quickstart.md                  # 5 分钟快速上手
    ├── daily-ops.md                   # ⭐ 日常运维三层模式
    ├── setup-v2rayn.md                # Windows 配置指南
    ├── setup-shadowrocket-iphone.md   # iPhone 配置指南
    ├── setup-shadowrocket-ipad.md     # iPad 配置指南
    ├── setup-shadowrocket-mac.md      # Mac 配置指南
    ├── adding-rules.md                # 如何添加新规则
    ├── troubleshooting.md             # 故障排查
    └── architecture.md                # 架构说明(技术深入)
```

---

## 5. 各文件详细规范

### 5.1 `proxy-list.txt` (主源文件)

**作用**:用户唯一手动维护的文件,定义所有走代理的域名。

**格式规则**:
- UTF-8 编码,无 BOM
- 每行一个域名
- 不带协议前缀(不要写 `https://`)
- 不带 `domain:` 等前缀
- 不要写通配符(`*.example.com` 不允许)
- `#` 开头的行为注释,忽略
- 行内 `#` 后的内容视为行内注释
- 空行允许且会被忽略
- 域名应是根域名形式(`example.com`,工具会自动匹配子域)

**初始内容要求**:

按服务分组,每组用注释标题分隔,顺序如下:

```text
# 代理白名单 - 主源文件
# 每行一个域名,以 # 开头的行为注释
# 修改后 GitHub Actions 会自动重新生成 v2rayn-rules.json
# 最后更新:[YYYY-MM-DD]

# ===== Anthropic / Claude =====
anthropic.com
claude.ai
claude.com

# ===== OpenAI / ChatGPT =====
openai.com
chatgpt.com
oaistatic.com
oaiusercontent.com
sora.com

# ===== GitHub =====
github.com
githubusercontent.com
githubassets.com
github.io
githubapp.com
git.io

# ===== Google =====
google.com
googleapis.com
googleusercontent.com
gstatic.com
ggpht.com
gmail.com
googlevideo.com
goo.gl
android.com
withgoogle.com

# ===== YouTube =====
youtube.com
youtu.be
ytimg.com
youtube-nocookie.com

# ===== Twitter / X =====
twitter.com
x.com
twimg.com
t.co

# ===== TradingView =====
tradingview.com
tradingview-widget.com

# ===== Binance(币安)=====
binance.com
bnbstatic.com
binancezh.com
bn-files.com

# ===== Bitget =====
bitget.com
bgstatic.com
```

---

### 5.2 `generate.py` (转换脚本)

**作用**:读 `proxy-list.txt`,生成 `v2rayn-rules.json`。

**技术要求**:
- Python 3.9+
- 仅使用标准库(`json`, `re`, `pathlib`, `sys`)
- 入口可独立运行: `python generate.py`
- 退出码:成功 0,失败 1
- 输出日志到 stdout,错误信息到 stderr

**函数设计**:

```python
def parse_domain_list(text: str) -> list[str]:
    """解析文本,返回干净的域名列表。
    - 跳过空行和注释行
    - 处理行内注释
    - 自动去重(保持顺序)
    - 自动小写化
    - 校验:基本域名格式(包含点,不含空格/特殊字符)
    """

def generate_v2rayn_rules(domains: list[str]) -> list[dict]:
    """根据域名列表生成 V2RayN 路由规则数组。
    生成 4 条规则:
    1. 代理白名单(domain:前缀)
    2. 拦截广告(geosite:category-ads-all)
    3. 直连 CN + 局域网(geosite:cn / geosite:private / geoip:cn / geoip:private)
    4. 兜底 direct(port: 0-65535)
    """

def main() -> int:
    """主入口。"""
```

**生成的 JSON 结构**:

```json
[
  {
    "outboundTag": "proxy",
    "port": "",
    "protocol": [],
    "inboundTag": [],
    "domain": [
      "domain:anthropic.com",
      "domain:claude.ai",
      "..."
    ],
    "ip": [],
    "enabled": true
  },
  {
    "outboundTag": "block",
    "port": "",
    "protocol": [],
    "inboundTag": [],
    "domain": ["geosite:category-ads-all"],
    "ip": [],
    "enabled": true
  },
  {
    "outboundTag": "direct",
    "port": "",
    "protocol": [],
    "inboundTag": [],
    "domain": ["geosite:private", "geosite:cn"],
    "ip": ["geoip:private", "geoip:cn"],
    "enabled": true
  },
  {
    "outboundTag": "direct",
    "port": "0-65535",
    "protocol": [],
    "inboundTag": [],
    "domain": [],
    "ip": [],
    "enabled": true
  }
]
```

**JSON 输出格式要求**:
- 2 空格缩进
- `ensure_ascii=False`(允许 UTF-8 字符)
- 文件末尾保留一个换行符
- 数组元素之间无多余空行

**错误处理**:
- `proxy-list.txt` 不存在 → 打印错误退出 1
- 解析后 domains 为空 → 打印错误退出 1
- 任何 IO 错误 → 抛出原始异常,退出 1

---

### 5.3 `.github/workflows/generate.yml`

**作用**:监听 `proxy-list.txt` 改动,自动重新生成 `v2rayn-rules.json` 并提交。

**触发条件**:
- 推送到 `main` 分支,且改动包含 `proxy-list.txt` / `generate.py` / 工作流自身
- 手动触发(`workflow_dispatch`)

**权限**:`contents: write`(允许 Actions 提交到仓库)

**Job 步骤**:
1. checkout(`actions/checkout@v4`)
2. 安装 Python 3(`actions/setup-python@v5`)
3. 运行 `python generate.py`
4. `git diff --quiet v2rayn-rules.json` 检查变化
5. 有变化 → commit with bot identity → push

**提交 commit 的作者**:

```
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
```

**Commit message**:`auto: 重新生成 v2rayn-rules.json`

**重要**:必须避免 Actions 触发自己造成死循环。通过仅在 paths 监听 `proxy-list.txt` 而非 `v2rayn-rules.json` 实现。

---

### 5.4 `README.md` (项目主页)

**作用**:项目的入口文档,放在仓库根目录。

**必须包含的章节(按顺序)**:

1. **项目标题 + 一句话描述**
2. **徽章区**:GitHub Actions 状态徽章
3. **核心特性**:5 条 bullet,说明本项目的卖点
4. **快速开始**:3 步上手概览,指向 `docs/quickstart.md`
5. **⭐ 日常使用**:**显著位置**展示 `docs/daily-ops.md` 的链接,说明这是日常运维的核心参考
6. **架构图**:文字版的数据流图(类似第 2 节)
7. **目录结构**:简化版的文件树 + 每个文件作用
8. **使用文档导航**:链接到 `docs/` 下各文档
9. **如何添加新规则**:核心操作,1 段简介 + 链接到 `docs/adding-rules.md` 和 `docs/daily-ops.md`
10. **订阅 URL 模板**:占位符形式(用户替换 username)
11. **License**

**语言**:中文为主,代码块和命令保留英文。

**徽章示例**:
```
![GitHub Actions](https://github.com/USERNAME/proxy-rules/actions/workflows/generate.yml/badge.svg)
```

**README 中"日常使用"章节的内容要点**(突出三层运维模式):

```markdown
## 日常使用

这个项目的运维分为三层,按场景选用工具:

| 场景 | 工具 | 耗时 |
|---|---|---|
| 加 / 删 1~2 个域名 | GitHub 网页直接编辑 | 2 分钟 |
| 加新服务 / 智能整理 | Claude.ai 网页 Code 功能 | 5 分钟 |
| 改架构 / 排查 bug | PC 本地 Claude Code | 按需 |

→ 详细操作流程见 [docs/daily-ops.md](docs/daily-ops.md)
```

---

### 5.5 `docs/quickstart.md`

**作用**:让新用户 10 分钟内完成端到端配置。

**结构**:
1. **前置条件**:已有 GitHub 账号 / 已有代理机场订阅 / 已装基础客户端
2. **第一阶段**:Fork 或 Use Template(假设用户从模板创建)
3. **第二阶段**:获取订阅 URL(展示 raw URL 的拼接方式)
4. **第三阶段**:在每个客户端配置订阅(指向各平台详细指南)
5. **第四阶段**:验证(测试访问 Claude.ai 或其他白名单网站)

格式:用编号步骤 + 截图占位符(`![截图](images/xxx.png)`),Claude Code 可以创建 images 目录但放占位文字)。

---

### 5.6 `docs/setup-v2rayn.md`

**详细描述**:
- V2RayN v6.x 路由设置入口(菜单 → 设置 → 路由设置)
- 添加规则集 → 别名 / 域名解析策略 / **可选地址(URL)** 字段
- URL 填什么(用占位符)
- 手动触发更新订阅的方法
- 设置环境变量给 CLI 工具使用代理(`HTTPS_PROXY`/`HTTP_PROXY`)
- 启用系统代理
- 验证步骤(`curl` 命令测试 CF-RAY)

---

### 5.7 `docs/setup-shadowrocket-iphone.md`

**详细描述**:
- Shadowrocket 打开 → 配置标签
- 添加规则集:类型 / 链接 / 目标 / 更新间隔
- URL 填什么
- 规则集排序的重要性(必须在 GEOIP,CN,DIRECT 之前)
- 启用代理 + iOS VPN 授权
- 验证步骤

---

### 5.8 `docs/setup-shadowrocket-ipad.md`

**主要内容**:
- 与 iPhone 相同的 Apple ID 在 App Store 已购列表中下载
- 配置方法 1:AirDrop 从 iPhone 传 .conf
- 配置方法 2:重复 iPhone 流程
- iCloud Sync 启用方法

---

### 5.9 `docs/setup-shadowrocket-mac.md`

**关键内容**:
- **Apple Silicon Mac(M1/M2/M3/M4)专属安装方法**:
  - Mac App Store 搜索 Shadowrocket
  - 筛选切换到"iPhone 与 iPad App"
  - 用 iPhone 同款 Apple ID 登录,已购免费安装
- Intel Mac 的替代方案(简短提及,建议升级或换 Stash)
- iOS App 在 Mac 上的交互特点(触屏交互转鼠标的注意事项)
- VPN 配置弹窗授权
- 与 iPhone/iPad 通过 iCloud Sync 同步配置的方法

---

### 5.10 `docs/adding-rules.md`

**作用**:教用户如何添加/删除规则。

**结构**:
1. **核心原则**:只改 `proxy-list.txt`,不要碰 `v2rayn-rules.json`
2. **操作步骤(网页编辑)**:
   - 进入仓库 → 找到文件 → 铅笔图标 → 编辑 → 加一行 → Commit
3. **域名书写规范**:
   - 写根域名(`reddit.com`)而非子域(`old.reddit.com`)
   - 不要写协议前缀
   - 注释如何写
4. **多分组管理建议**:加新域名时归到合适分组
5. **验证生效**:
   - 查看 Actions 是否跑完(30 秒)
   - 等待客户端订阅周期(或手动刷新)
   - 用 V2RayN 实时连接列表 / Shadowrocket 全局路由查看
6. **如何删除规则**:同样编辑 txt 文件,删除对应行
7. **如何回滚**:GitHub history 找到旧版本,revert

---

### 5.10.1 `docs/daily-ops.md` (日常运维核心文档)

**作用**:告诉用户**什么时候用什么工具**,避免过度工程化。

**结构**:

#### 章节 1:三层运维模式概览

用一张表/图说明三种场景对应的工具:

| 场景 | 推荐工具 | 频率 | 耗时 |
|---|---|---|---|
| 加 1 个域名(我已知道域名) | GitHub 网页直接编辑 | 高频 | 2 分钟 |
| 删 1 个域名 | GitHub 网页直接编辑 | 中频 | 1 分钟 |
| 加一个新服务(可能涉及多个域名) | Claude.ai 网页 Code 功能 | 低频 | 3-5 分钟 |
| 整理/重构规则 | Claude.ai 网页 Code 功能 | 极少 | 5-15 分钟 |
| 项目重大改动(改架构) | PC 本地 Claude Code | 几乎不发生 | 30 分钟+ |

#### 章节 2:场景 A - 加 / 删 1 个域名(GitHub 网页)

**这是 90% 的场景,记住这一个流程就够了。**

完整步骤:
1. 任何浏览器(手机/电脑均可)打开 `https://github.com/<USERNAME>/<REPO>`
2. 点击 `proxy-list.txt`
3. 右上角铅笔图标 ✏️ → 编辑模式
4. 滚到合适的分组(如 `# ===== Google =====`),加一行 / 删一行
5. 滚到底部 → 写 commit 信息(如:`add reddit.com`)→ `Commit changes`
6. 切到 Actions 标签 → 等 30 秒,看到绿色对勾
7. 等待客户端订阅周期(或手动刷新单个客户端)

**手机操作小贴士**:
- iPhone Safari / Chrome 都能编辑,但建议横屏
- 推荐用 GitHub Mobile App,编辑体验比网页好

#### 章节 3:场景 B - 复杂任务(Claude.ai 网页 Code)

**何时用 Claude.ai 网页版的 Code 功能**:
- 想加一个新服务,但不确定它有几个相关域名(让 AI 帮你查)
- 想批量整理(比如"把所有 Google 相关合并到一个分组")
- 想检查现有规则是否完整(比如"我的 Binance 规则有没有遗漏 CDN?")
- 想做规则审计("分析一下哪些域名没必要代理")

**使用前的一次性准备**:

a. 生成 GitHub Personal Access Token (PAT-DailyOps):
   - 详细步骤见 [附录 D.2](../proxy-rules-design-doc.md#d2-pat-dailyops) 或本仓库 README 中的 PAT 章节
   - 关键配置:Token name `proxy-rules-daily-ops`,1 年期限,**仅授权本仓库**,权限 Contents(Read/Write)+ Actions(Read)
   - ⚠️ 注意区分:此 token 与初次部署用的 PAT-Deploy 不同,权限更小、期限更长
   - 复制 token(只显示一次,丢失需重新生成)

b. 在 Claude.ai 创建一个项目(Project):
   - 项目名:`proxy-rules 运维`
   - 在 Project 的"项目说明 / 自定义指令"中粘贴一段标准 prompt(见下方模板)

c. 把 PAT 保存到密码管理器(1Password / Apple Keychain / Windows Credential Manager),Claude.ai 不要存

**标准 prompt 模板**(用户在每次新对话开头粘贴一次):

```
我有一个 GitHub 仓库:https://github.com/<USERNAME>/proxy-rules

这是一个代理规则同步项目,主源是 proxy-list.txt(纯文本,
每行一个域名),GitHub Actions 会自动生成 v2rayn-rules.json。

请帮我完成以下任务:[在这里描述你要做什么]

操作规则:
1. 用 git clone 拉取仓库
2. 修改 proxy-list.txt(只改这个文件,不要碰自动生成的 json)
3. 域名书写规范:根域名(reddit.com),不带协议前缀,不带 domain: 前缀
4. 加入合适的分组下,保持原有的注释结构和分组顺序
5. commit message 使用语义化:add xxx / remove xxx / refactor xxx
6. push 到 main 分支
7. 验证 Actions 是否成功触发并完成
8. 最后告诉我:改了什么、commit hash、Actions 状态

GitHub 鉴权(我开新会话时会粘贴):
GitHub PAT: <你的 token>
GitHub Username: <你的 username>
```

**典型对话示例**:

```
👤 用户:[粘贴标准 prompt]
        在这里描述你要做什么:
        帮我加入 Reddit 访问需要的全部域名,
        包括 Reddit 自己和它依赖的所有 CDN。

🤖 Claude Code:
   - clone 仓库
   - 分析 Reddit 域名结构,确认需要:
     reddit.com / redd.it / redditstatic.com / redditmedia.com
   - 在 proxy-list.txt 添加新分组 "# ===== Reddit ====="
   - commit + push
   - 验证 Actions 跑成功
   - 报告:已添加 4 个域名,Actions 已成功生成新 JSON
```

#### 章节 4:场景 C - 项目重大改动(PC 本地 Claude Code)

**何时需要 PC 本地版**:
- 改架构(比如增加 Clash YAML 输出格式)
- 改自动化流水线
- 排查复杂 bug

这种场景很少见,如果遇到,直接 cd 到本地仓库目录跑 `claude` 即可。

#### 章节 5:三层模式的边界守则

**永远不要**:
- ❌ 同一时刻在多个客户端编辑 proxy-list.txt(可能产生 git 冲突)
- ❌ 把 GitHub PAT 写在公开仓库的任何文件里
- ❌ 用 Claude.ai 网页版做简单的"加一个域名"(浪费 token,网页直接改更快)

**始终要**:
- ✅ 任何修改都通过 git commit,不要绕过版本控制
- ✅ commit message 写清楚改了什么
- ✅ 改完后看一眼 Actions 是否成功

#### 章节 6:常见问题

| 问题 | 答案 |
|---|---|
| Claude.ai 网页 Code 改了规则,V2RayN 没更新? | V2RayN 是手动更新订阅的,不是自动 |
| 多设备同时改了规则冲突? | GitHub 会 reject 第二次 push,改用 pull → 合并 → push |
| PAT 不小心泄露了? | 立即去 GitHub Settings revoke,重新生成 |
| 手机上不方便复制 PAT? | 用密码管理器(1Password 等)的自动填充 |

---

### 5.11 `docs/troubleshooting.md`

**覆盖问题**:

| 症状 | 可能原因 | 解决 |
|---|---|---|
| Actions 跑失败,red ❌ | 权限不够 / 脚本异常 | 检查 Settings → Actions → Workflow permissions 为 Read and write |
| Actions 跑成功但没有 commit | json 没变化(预期行为) | 不是问题 |
| V2RayN 订阅 URL 拉不到内容 | URL 错误 / 网络问题 | 浏览器直接打开 URL 检查是否能看到 json |
| Shadowrocket 规则集订阅后规则数为 0 | URL 错误 / 文件为空 | 浏览器直接打开 URL 检查 |
| 某网站没走代理 | 域名不在白名单 / 规则未刷新 | 添加规则 / 手动刷新订阅 |
| Claude Code 报 ECONNRESET | 代理节点不稳定 | 换节点,与本项目无关 |
| Cloudflare 返回 403 | 代理节点 IP 被风控 | 换节点,与本项目无关 |

---

### 5.12 `docs/architecture.md`

**作用**:深度技术说明,给想理解原理的用户。

**内容**:
- 完整的数据流图
- 为什么需要两种格式(各客户端的格式差异)
- Python 脚本的工作原理
- GitHub Actions 工作流原理
- 安全性说明(为什么仓库可以 Public)
- 性能考虑(订阅频率 / GitHub raw URL 缓存)

---

### 5.13 `tests/test_generate.py`

**作用**:确保 `generate.py` 的正确性,后续修改有回归测试。

**测试框架**:`pytest`(或 `unittest`,标准库即可)

**最少测试用例**:
1. 解析正常输入 → 返回正确数量的域名
2. 解析含注释 → 注释被忽略
3. 解析含空行 → 空行被忽略
4. 解析含行内注释 → 行内注释被去除
5. 解析空文件 → 返回空列表
6. 重复域名 → 自动去重
7. 大小写不同的同域名 → 视为相同(自动小写化)
8. 生成 JSON 结构 → 4 条规则,顺序正确
9. 生成 JSON 的 proxy 规则 → 包含所有输入域名带 `domain:` 前缀
10. 端到端:读 fixtures → 输出 → 与 expected-output.json 一致

**fixtures**:
- `tests/fixtures/sample-input.txt`:包含各种边界情况的示例输入
- `tests/fixtures/expected-output.json`:对应的预期输出

---

### 5.14 `.gitignore`

**最小内容**(Python 项目):

```
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
*.swp
.idea/
.vscode/
*.egg-info/
```

---

### 5.15 `LICENSE`

**内容**:标准 MIT License,版权人填占位符(`<YEAR> <COPYRIGHT HOLDER>`),由用户后续替换。

---

## 6. 实施步骤(Claude Code 执行顺序)

按以下顺序构建,**每完成一步都打印状态**:

### Phase 1:项目骨架(优先级最高)
1. 创建目录结构(`mkdir -p .github/workflows docs tests/fixtures`)
2. 创建 `.gitignore`
3. 创建 `LICENSE`(MIT,版权人 placeholder)

### Phase 2:核心功能
4. 创建 `proxy-list.txt`(初始内容如 5.1 节)
5. 创建 `generate.py`(按 5.2 节规范)
6. 本地运行 `python generate.py` 测试,生成 `v2rayn-rules.json`
7. 创建 `.github/workflows/generate.yml`(按 5.3 节)

### Phase 3:测试
8. 创建 `tests/fixtures/sample-input.txt`
9. 创建 `tests/fixtures/expected-output.json`
10. 创建 `tests/test_generate.py`
11. 本地运行 `pytest tests/` 验证全部通过

### Phase 4:文档
12. 创建 `README.md`(主页)
13. 创建 `docs/quickstart.md`
14. 创建 `docs/daily-ops.md` ⭐(运维核心文档,务必详细)
15. 创建 `docs/setup-v2rayn.md`
16. 创建 `docs/setup-shadowrocket-iphone.md`
17. 创建 `docs/setup-shadowrocket-ipad.md`
18. 创建 `docs/setup-shadowrocket-mac.md`
19. 创建 `docs/adding-rules.md`
20. 创建 `docs/troubleshooting.md`
21. 创建 `docs/architecture.md`

### Phase 5:本地验证
21. 检查所有文件存在且非空
22. 验证 `generate.py` 能跑通
23. 验证 `pytest tests/` 通过
24. 检查 README.md 中的链接是否有效(指向存在的文件)

### Phase 6:Git 本地准备
25. 初始化 git 仓库(如尚未初始化): `git init`
26. 配置本地 git user(如尚未配置,询问用户):
    - `git config user.name "..."`
    - `git config user.email "..."`
27. 创建初次 commit: `feat: 初始化代理规则同步系统`

### Phase 7:GitHub 自动部署(全程自动,只在必要时询问用户)

**前置依赖检查**:

28. 检查 `gh` 命令是否可用: `gh --version`
    - 不可用 → 提示用户安装(`winget install --id GitHub.cli`),停在此步等待

**PAT 鉴权(不使用密码,不使用浏览器登录)**:

29. **强制使用 PAT 鉴权**。Claude Code 必须严格按以下流程:
    
    a. **检查是否已有 PAT-Deploy**:询问用户是否已生成 PAT-Deploy
       - 已生成 → 让用户粘贴(Claude Code 必须明确告知用户:PAT 仅用于本次会话,不会写入任何文件)
       - 未生成 → 输出生成步骤(见附录 D),停在此步等待用户完成
    
    b. **设置环境变量**(必须使用环境变量,严禁写入文件):
       ```powershell
       # PowerShell (Windows)
       $env:GH_TOKEN = "<用户粘贴的 PAT>"
       ```
       ```bash
       # bash (Linux/macOS)
       export GH_TOKEN="<用户粘贴的 PAT>"
       ```
    
    c. **验证鉴权生效**:
       ```bash
       gh auth status
       ```
       期望输出包含 `Logged in to github.com as <username>`
    
    d. **拒绝条件**:
       - 如果用户提供的是"用户名 + 密码",**必须明确拒绝**,告知用户:
         > GitHub 自 2021 年起不再接受密码鉴权。请按附录 D 生成 Personal Access Token (PAT)。
       - 如果用户坚持给密码,继续拒绝,**不可尝试任何其他登录方式**
    
    e. **拒绝把 PAT 持久化**:
       - 不要执行 `gh auth login --with-token` 后选择保存
       - 不要写入 `.netrc`、`.git-credentials`、`.env` 等任何文件
       - 仅依赖 `GH_TOKEN` 环境变量,会话结束自然失效

**创建远程仓库**:

30. 询问用户仓库名(默认 `proxy-rules`,允许用户改名)
31. 询问用户仓库可见性(默认 Public,因为订阅 URL 需要无鉴权访问)
32. 使用 gh CLI 创建仓库并 push:
    ```bash
    gh repo create <REPO_NAME> --public --source=. --remote=origin --push
    ```
    此命令会一次性完成:创建远程仓库 + 设置 origin + push main 分支

**配置 Actions 权限**:

33. 给仓库的 Actions 配置 Read/Write 权限(必须,否则 workflow 无法 commit):
    ```bash
    gh api -X PUT /repos/<OWNER>/<REPO>/actions/permissions/workflow \
      -f default_workflow_permissions=write \
      -F can_approve_pull_request_reviews=false
    ```

**触发并监控首次 Actions 运行**:

34. 手动触发一次 workflow(确保即使无文件变化也能跑一遍):
    ```bash
    gh workflow run generate.yml
    ```
35. 监控本次运行状态(最多等待 90 秒):
    ```bash
    gh run list --workflow=generate.yml --limit=1
    gh run watch  # 实时监控最新运行
    ```
36. 检查结果:
    - 成功 ✅ → 继续 Phase 8
    - 失败 ❌ → 拉取日志 `gh run view --log-failed` 输出给用户,停下来排错

**验证订阅 URL 可用**:

37. 构造两个 raw URL 并验证可访问:
    ```bash
    USERNAME=$(gh api user --jq .login)
    REPO=<REPO_NAME>
    
    curl -fsSL "https://raw.githubusercontent.com/$USERNAME/$REPO/main/proxy-list.txt" \
      | head -5
    
    curl -fsSL "https://raw.githubusercontent.com/$USERNAME/$REPO/main/v2rayn-rules.json" \
      | head -10
    ```
38. 两个 URL 都能拉到内容 → 部署成功

### Phase 8:输出最终交付总结

完成全部 7 个 Phase 后,向用户输出:

1. 仓库 URL: `https://github.com/<USERNAME>/<REPO>`
2. 两个订阅 URL(替换为真实 username/repo)
3. Actions 状态徽章 markdown(可粘贴到 README)
4. 下一步操作清单:
   - V2RayN 端:配置订阅(指向 `docs/setup-v2rayn.md`)
   - iPhone 端:配置订阅(指向 `docs/setup-shadowrocket-iphone.md`)
   - 等等

### Phase 9:鉴权善后(必须执行,不可跳过)

部署成功后,Claude Code **必须**主动引导用户完成以下安全善后:

39. **明确提醒用户撤销 PAT-Deploy**:
    
    输出原文(必须使用这样的措辞,不可省略):
    
    ```
    🔒 安全善后:请立即撤销刚刚使用的 PAT-Deploy
    
    PAT-Deploy 是为本次部署生成的高权限 token,已完成使命。
    强烈建议你立即撤销,避免 token 泄露风险。
    
    撤销步骤(只需 30 秒):
    1. 打开 https://github.com/settings/personal-access-tokens
    2. 找到名为 `proxy-rules-deploy` 的 token
    3. 点击右侧 `Revoke` 按钮 → 确认
    
    完成后告诉我"已撤销",我会清理本次会话中残留的 token 引用。
    ```
    
40. **建议生成 PAT-DailyOps**(用于未来 Claude.ai 网页 Code 日常运维):
    
    ```
    📝 可选:生成长期运维 PAT-DailyOps
    
    如果你计划未来用 Claude.ai 网页版的 Code 功能做日常运维
    (加复杂域名、智能整理规则),建议现在生成一个权限更小的
    长期 token。
    
    建议配置:
    - 名字:proxy-rules-daily-ops
    - 期限:1 年
    - Repository access: Only select repositories → 仅选 proxy-rules
    - Permissions:
      - Contents: Read and write
      - Actions: Read
      - Metadata: Read(自动)
    
    生成后存入密码管理器(1Password / Bitwarden / Apple Keychain),
    Claude.ai 网页版每次新会话开始时粘贴使用。
    
    详细使用方式见仓库内 docs/daily-ops.md。
    ```

41. **清理环境变量**(在用户确认撤销后):
    ```powershell
    Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue
    ```

### Phase 7 / 8 / 9 中遇到失败的处理原则

- **gh 未安装**:暂停,告诉用户准确的安装命令
- **gh 未登录**:暂停,告诉用户运行 `gh auth login`,等用户做完报告再继续
- **仓库名已存在**:询问用户是 (a) 换名字 (b) 删除旧仓库 (c) 用旧仓库的 origin
- **push 失败**:可能是网络问题(GitHub 在中国偶尔不稳定),提示用户检查代理后重试
- **Workflow 跑失败**:拉取错误日志显示给用户,根据错误类型给出修复建议

---

## 7. 验收标准(Definition of Done)

### 7.1 功能性
- [ ] `python generate.py` 能从 `proxy-list.txt` 生成正确的 `v2rayn-rules.json`
- [ ] `pytest tests/` 全部通过(至少 10 个测试用例)
- [ ] `proxy-list.txt` 含至少 9 个分组、40 个域名(按 5.1 节)
- [ ] `v2rayn-rules.json` 含 4 条规则,顺序正确

### 7.2 自动化
- [ ] `.github/workflows/generate.yml` 语法正确
- [ ] 工作流权限设为 `contents: write`
- [ ] 仅在 `proxy-list.txt` 等关键文件改动时触发
- [ ] 不会触发自循环(改 `v2rayn-rules.json` 不会再触发)

### 7.3 文档完整性
- [ ] `README.md` 是中文,含 11 个必要章节(包含"日常使用"章节)
- [ ] `docs/` 下所有指定文档存在且非空(包含 `daily-ops.md`)
- [ ] `docs/daily-ops.md` 完整覆盖三层运维模式 + PAT 生成步骤 + Claude.ai 标准 prompt 模板
- [ ] 每个 setup-*.md 文档包含完整的步骤、关键截图占位符、验证方法
- [ ] `docs/troubleshooting.md` 至少覆盖 7 种症状
- [ ] README 中显眼位置链接到 `daily-ops.md`

### 7.4 代码质量
- [ ] `generate.py` 使用类型注解
- [ ] 函数有 docstring
- [ ] 没有硬编码绝对路径
- [ ] 错误处理完整(IO / 解析 / 空输入)

### 7.5 Git 整洁度
- [ ] `.gitignore` 工作正常
- [ ] commit message 语义清晰
- [ ] 没有提交临时文件 / `__pycache__/` / `.DS_Store`

### 7.6 GitHub 部署
- [ ] 远程仓库已成功创建(Public)
- [ ] main 分支已 push
- [ ] Actions Workflow permissions 已设为 Read and write
- [ ] 首次 Actions 运行成功(可通过 `gh run list` 验证)
- [ ] 两个 raw URL 都能 curl 拉到正确内容
- [ ] 仓库页面顶部 Actions 徽章显示绿色(passing)

---

## 8. 关键约束与禁忌

### 8.1 不要做的事

- ❌ **不要修改 `proxy-list.txt` 的格式**:用户已熟悉纯文本格式,改成 yaml/json 会破坏体验
- ❌ **不要在脚本里硬编码代理服务器信息**:本项目只管规则,节点由用户机场处理
- ❌ **不要引入除 Python 标准库 + pytest 外的依赖**:保持简单
- ❌ **不要让 Actions 在每次 commit 都触发**:必须配置 paths 过滤
- ❌ **不要把仓库设为 Private**:订阅 URL 需要无鉴权访问
- ❌ **不要在文档里用真实的 GitHub username 写订阅 URL**:用占位符 `YOUR_USERNAME`

### 8.2 必须做的事

- ✅ **所有用户文档必须是中文**:用户的母语习惯
- ✅ **`generate.py` 必须本地可独立运行**:不依赖 Actions 环境
- ✅ **每个 docs 文件必须能独立阅读**:不依赖读者已读其他文档
- ✅ **代码注释用中文**:与文档风格一致

---

## 9. 用户最终交付清单(Claude Code 完成全部 Phase 后输出)

**所有 8 个 Phase 完成后,Claude Code 向用户输出以下信息**:

```
✅ 项目已部署完毕!

📦 仓库地址
   https://github.com/<USERNAME>/<REPO>

🔗 订阅 URL(配置客户端时使用)
   规则主源(Shadowrocket 用):
   https://raw.githubusercontent.com/<USERNAME>/<REPO>/main/proxy-list.txt
   
   V2RayN 专用:
   https://raw.githubusercontent.com/<USERNAME>/<REPO>/main/v2rayn-rules.json

⚙️ Actions 已自动运行,初次构建状态:
   [✅ 成功 / ❌ 失败 + 错误简述]

📚 接下来怎么配置各设备
   Windows V2RayN  → 见 docs/setup-v2rayn.md
   iPhone 小火箭   → 见 docs/setup-shadowrocket-iphone.md
   iPad 小火箭     → 见 docs/setup-shadowrocket-ipad.md
   iMac 小火箭     → 见 docs/setup-shadowrocket-mac.md

⭐ 日常如何使用(必看)
   → docs/daily-ops.md
   - 90% 的场景:用 GitHub 网页直接编辑 proxy-list.txt
   - 10% 的场景:用 Claude.ai 网页 Code 功能做复杂运维
   - 极少:用 PC 本地 Claude Code 做架构改动

📝 以后加新规则(最常见动作)
   1. 任何浏览器打开仓库 → proxy-list.txt → 铅笔图标
   2. 加一行域名 → Commit
   3. 等约 30 秒 Actions 自动重新生成 JSON
   4. 各设备下次拉取订阅时自动同步

🔒 安全善后(部署后必做)
   1. 立即撤销 PAT-Deploy
      https://github.com/settings/personal-access-tokens
      找到 proxy-rules-deploy → Revoke
   2. (可选)生成 PAT-DailyOps 用于未来日常运维
      详见 docs/daily-ops.md 中的 PAT 设置章节

可以打开仓库地址确认一下页面,Actions 标签下应该能看到 1 次成功的运行记录。
```

### 用户的前置准备

**在让 Claude Code 跑这个项目前**,用户需要先完成以下三件事(用户在 README 或对话开始时被告知):

1. **安装 GitHub CLI**:
   ```
   winget install --id GitHub.cli
   ```
2. **安装 Git**(如尚未安装):
   ```
   git --version       # 检查
   winget install --id Git.Git   # 没装就装
   ```
3. **生成 GitHub Personal Access Token (PAT-Deploy)**:
   - 详细步骤见附录 D
   - 建议提前生成好,Claude Code 跑到 Phase 7 时直接粘贴
   - **不需要** `gh auth login`(Claude Code 会用 PAT 通过环境变量鉴权)

Claude Code 在 Phase 7 第 28-29 步会检查这些前置条件,缺失则暂停等待用户准备。

**⚠️ 安全提醒**:
- Claude Code 不接受 GitHub 用户名/密码,仅接受 PAT
- 用户提供的 PAT **仅在当前会话有效**(通过环境变量),不会持久化
- 部署完成后,Claude Code 会主动提醒用户撤销 PAT-Deploy

---

## 10. 后续可能的扩展(本次不实现,只在文档中预留方向)

未来如果用户需要,可扩展的方向:

1. **多 client format 输出**:除了 V2RayN JSON,可扩展 generate.py 生成 Clash YAML / Surge .conf / Sing-box JSON
2. **GitHub Pages**:把 docs/ 部署为静态网站
3. **预提交钩子**:`pre-commit` 自动跑 pytest
4. **dependabot**:自动升级 Actions 版本
5. **多分组导出**:为不同设备生成不同子集的规则

这些**本次实施不要做**,但可以在 `docs/architecture.md` 末尾留一个 "未来扩展" 章节简单提一下。

---

## 11. 安全与鉴权规范(Claude Code 必须严格遵守)

### 11.1 鉴权信息分类与处置规则

| 信息类型 | 来源 | Claude Code 处置 |
|---|---|---|
| GitHub 用户名 | 用户提供 | 可记录、可使用、可在 commit 中显示 |
| GitHub 密码 | 用户可能误提供 | **必须立即拒绝**,告知用户密码无效,引导生成 PAT |
| GitHub PAT | 用户提供 | **仅写入环境变量 `GH_TOKEN`**,**严禁**写入任何文件 |
| SSH 私钥 | 用户可能提供 | 本项目不需要,如用户主动提供,礼貌告知不需要 |
| 2FA 验证码 | 用户可能误提供 | **必须立即拒绝**,告知用户不应该把 2FA 码给任何工具 |

### 11.2 PAT 处置七条铁律

Claude Code 在收到 PAT 后,必须严格遵守:

1. **永远不写入文件** — 不写 `.env`、`.netrc`、`.git-credentials`、`.gitconfig`、`config.json` 或任何其他配置文件
2. **永远不写入 commit message** — 即使是测试性 commit 也不行
3. **永远不写入日志输出** — `echo $GH_TOKEN`、`print(token)` 都禁止;调试时用 `echo ${GH_TOKEN:0:4}***` 这样的脱敏方式
4. **永远不通过命令行参数传递** — 不要用 `gh auth login --token <PAT>`(这会被 shell history 记录),必须用 `GH_TOKEN` 环境变量
5. **永远不在屏幕上完整显示** — 用户粘贴后,后续引用只说"已收到 PAT"或显示 `ghp_xxxx...xxxx` 脱敏
6. **永远不传递给第三方服务** — 不发给 webhook、不发给任何 HTTP API(`gh` 本地工具除外)
7. **会话结束前必须清理** — 显式 `Remove-Item Env:GH_TOKEN` / `unset GH_TOKEN`

### 11.3 错误鉴权方式的拒绝清单

如果用户尝试以下方式,Claude Code 必须拒绝并解释:

| 用户行为 | Claude Code 响应 |
|---|---|
| "我把密码告诉你" | 拒绝。GitHub 2021 年起不接受密码鉴权。引导生成 PAT(指向附录 D) |
| "我把 2FA 码告诉你" | 拒绝。2FA 码不应该给任何工具,只用于浏览器登录时输入 |
| "把 PAT 存到一个文件里方便下次用" | 拒绝。PAT 应该存在密码管理器,而不是项目文件里 |
| "用我的 SSH 私钥" | 婉拒。本项目用 HTTPS+PAT 已经够用,SSH 私钥应该留在 `~/.ssh/` 不暴露 |
| "用 OAuth 浏览器登录" | 可接受,但提醒:本项目设计为 PAT 鉴权以支持完全自动化;OAuth 方式在自动化场景需要手工 device code 步骤 |

### 11.4 Claude Code 工作时的安全自检

每次 Claude Code 即将执行涉及 token 的操作前,**先在心里(或思考中)过一遍**:

- 这个命令会把 token 输出到屏幕吗?
- 这个命令会把 token 写入文件吗?
- 这个命令会被 shell history 记录吗?
- 这个 commit / push 会包含敏感信息吗?

任何一项是"是",停下,改用安全方式。

### 11.5 用户主动询问 PAT 处置时的标准回答

用户可能问:"你拿我的 PAT 干啥了?"

Claude Code 的标准回答模板:

```
你的 PAT 仅用于以下用途:
1. 设置环境变量 GH_TOKEN(本次终端会话内有效)
2. 让 gh CLI 调用 GitHub API:创建仓库、push、配置 Actions 权限、触发 workflow
3. 完成所有任务后,提示你撤销该 PAT

我没有:
- 把 PAT 写入任何文件
- 把 PAT 发到任何第三方服务
- 把 PAT 显示在终端输出里(只在你刚粘贴时短暂可见)
- 在 commit message 或代码里引用 PAT

你可以在 GitHub 的 Token 使用历史(https://github.com/settings/tokens 
→ 找到该 token → 看 "Last used" 时间)核对最近的调用记录。
```

---

## 附录 A:V2RayN 规则的字段语义(供 Claude Code 参考)

V2RayN v6.x 的路由规则使用 Xray-core 的格式,字段语义:

- `outboundTag`:出站标签
  - `proxy`:走代理
  - `direct`:走直连
  - `block`:拦截(不发出)
- `port`:端口范围,`""` 表示不限,`"0-65535"` 显式表示所有端口(常用于兜底规则)
- `domain`:域名规则数组,支持的前缀:
  - `domain:xxx.com`:匹配 xxx.com 及所有子域
  - `full:xxx.com`:精确匹配
  - `keyword:xxx`:关键字匹配
  - `regexp:^xxx`:正则匹配
  - `geosite:xxx`:内置规则集(如 `geosite:cn`)
- `ip`:IP 规则数组,支持 CIDR / `geoip:xxx`
- `protocol`:协议过滤,`[]` 表示不限
- `inboundTag`:入站标签过滤,`[]` 表示不限
- `enabled`:是否启用,`true` 或 `false`

附录 A 是给 Claude Code 在写 generate.py 时参考的,不需要写到用户文档里(用户没必要懂底层格式)。

---

## 附录 B:测试数据准备(给 Claude Code 用)

`tests/fixtures/sample-input.txt` 应包含以下边界情况:

```
# 这是顶部注释
# 用于测试

# ===== 分组 1 =====
example.com
foo.com   # 这是行内注释

# 空行测试

duplicate.com
DUPLICATE.com    # 测试大小写去重

# ===== 分组 2 =====
another.com
```

期望解析结果:`["example.com", "foo.com", "duplicate.com", "another.com"]`

期望生成的 `v2rayn-rules.json` 的 proxy 规则的 domain 数组:`["domain:example.com", "domain:foo.com", "domain:duplicate.com", "domain:another.com"]`

---

## 附录 C:Claude Code 工作模式建议

建议你(Claude Code)按以下模式工作:

1. **先全文阅读本文档**,理解整体目标
2. **按 Phase 1~8 顺序逐步实施**,每完成一个 Phase 简短总结(1-2 句话即可)
3. **遇到歧义时**:遵循"附录 B 中的具体示例" > "正文规范" > "你的合理判断" 这个优先级
4. **本地测试通过(Phase 1-5)后再进入 Git 操作(Phase 6+)**
5. **Phase 7 GitHub 部署阶段允许自动执行命令**,但:
   - 涉及不可逆操作时(如删除仓库、覆盖已有 origin)必须先问用户
   - `gh` 命令报权限错误时,不要重试不同方案,直接告诉用户具体什么错
   - 出现网络错误时,告诉用户"可能 GitHub 连接不稳定,等会再试",不要循环重试
6. **完成所有工作后,输出第 9 节的最终交付清单**(已自动部署后的版本)

### 关键禁令

- ❌ **不要替用户做不可逆决策**:删除仓库、force push、覆盖远程内容
- ❌ **不要尝试绕过 gh 鉴权**:如果 `gh auth status` 显示未登录,**不要尝试用其他方式登录**(如生成 PAT、写入 .netrc 等),停下来要求用户跑 `gh auth login`
- ❌ **不要把任何 token / 密码记录到任何文件**:即使临时调试也不行
- ❌ **不要在 commit message 里夹带与本任务无关的内容**

如果有任何技术细节确实无法决定,**明确询问用户**,而不是自行猜测做错。

---

## 附录 D:GitHub Personal Access Token (PAT) 生成步骤

本项目设计了**两个 PAT**,职责分离,生成步骤如下。

### D.1 PAT-Deploy(一次性,用于初次部署)

**用途**:让 Claude Code 创建仓库、push 代码、配置 Actions 权限。
**期限**:30 天(部署完成后立即撤销,所以期限可以短)
**生成步骤**:

1. 浏览器登录 GitHub,访问:
   `https://github.com/settings/personal-access-tokens/new`
2. 填写以下字段:
   
   | 字段 | 填写内容 |
   |---|---|
   | Token name | `proxy-rules-deploy` |
   | Description | `临时部署 token,用完即撤销` |
   | Resource owner | 选你自己的用户 |
   | Expiration | `30 days`(或更短) |
   | Repository access | **All repositories**(因为目标仓库还未创建,无法限定) |

3. **Repository permissions** 展开后,逐项设置:
   
   | 权限项 | 值 |
   |---|---|
   | Administration | **Read and write** |
   | Actions | **Read and write** |
   | Contents | **Read and write** |
   | Metadata | Read (自动勾选,无需手动) |
   | Workflows | **Read and write** |
   | (其他所有项) | No access |

4. 滚到最底部 → **Generate token**
5. **立即复制完整 token**(格式形如 `github_pat_xxxxx...`),只显示一次
6. 把 token 临时粘贴到一个 secure note(密码管理器中),不要写到 .txt 文件
7. 回到 Claude Code,告诉它"PAT-Deploy 已准备好",粘贴

### D.2 PAT-DailyOps(长期,用于 Claude.ai 网页 Code 日常运维)

**用途**:让 Claude.ai 网页版的 Code 功能能修改 `proxy-list.txt` 并 push。
**期限**:1 年(平衡安全和便捷)
**生成时机**:部署完成、撤销 PAT-Deploy 之后

**生成步骤**:

1. 浏览器访问:
   `https://github.com/settings/personal-access-tokens/new`
2. 填写以下字段:
   
   | 字段 | 填写内容 |
   |---|---|
   | Token name | `proxy-rules-daily-ops` |
   | Description | `Claude.ai 网页版日常运维 proxy-rules 仓库专用` |
   | Resource owner | 你自己 |
   | Expiration | `1 year` |
   | Repository access | **Only select repositories** → 仅勾选 `proxy-rules` |

3. **Repository permissions**:
   
   | 权限项 | 值 |
   |---|---|
   | Contents | **Read and write** |
   | Actions | **Read** |
   | Metadata | Read (自动) |
   | (其他所有项) | No access |

4. Generate token → 复制 → **存入密码管理器**(1Password / Bitwarden / Apple Keychain)
5. 每次在 Claude.ai 开新会话做日常运维时,从密码管理器复制一次粘贴给它即可

### D.3 PAT 撤销步骤

无论哪个 PAT 想撤销:

1. 浏览器访问:`https://github.com/settings/personal-access-tokens`
2. 找到对应名字(`proxy-rules-deploy` 或 `proxy-rules-daily-ops`)
3. 点击右侧 **Revoke** 按钮 → 确认

撤销立即生效,后续任何带该 token 的请求会被 GitHub 拒绝。

### D.4 PAT 泄露应急流程

如果你怀疑 PAT 已泄露(比如不小心截图发了别人):

1. **立即撤销该 PAT**(同 D.3)
2. 检查仓库的近期 commit:`git log --oneline -20`,确认没有可疑的 commit
3. 检查 Actions 运行历史:`gh run list --limit=20`,确认没有可疑运行
4. 如果发现异常,可以从 GitHub UI 删除可疑 commit 或回滚分支
5. 生成新 PAT,继续使用

由于 PAT 范围有限,泄露的影响仅限于 `proxy-rules` 仓库,**不会影响你的 GitHub 账号其他部分**。这就是为什么我们用 fine-grained PAT 而不是密码或全局 PAT。

---

**文档结束(v1.3 - 完整版)**

---

**文档结束(v1.3 - 完整版)**

如有任何不清楚的地方,Claude Code 应当在开始实施前提出疑问,不要带着误解动手。
