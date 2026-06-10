# ⭐ 日常运维:三层模式

本文档是 proxy-rules 项目的**日常运维核心参考**。一句话原则:**简单的事用最简单的工具,复杂的事才动用 AI。** 避免「每改一个域名都得打开 Claude Code」的过度工程化。

---

## 章节 1:三层运维模式概览

| 场景 | 推荐工具 | 频率 | 耗时 |
|---|---|---|---|
| 加 1 个域名(我已知道域名) | GitHub 网页直接编辑 | 高频 | 2 分钟 |
| 删 1 个域名 | GitHub 网页直接编辑 | 中频 | 1 分钟 |
| 加一个新服务(可能涉及多个域名) | Claude.ai 网页 Code 功能 | 低频 | 3–5 分钟 |
| 整理 / 重构规则 | Claude.ai 网页 Code 功能 | 极少 | 5–15 分钟 |
| 项目重大改动(改架构) | PC 本地 Claude Code | 几乎不发生 | 30 分钟+ |

**记住这张表**:绝大多数时候你只需要第一行——打开 GitHub 网页改一行字。

---

## 章节 2:场景 A — 加 / 删 1 个域名(GitHub 网页)

**这是 90% 的场景,记住这一个流程就够了。**

完整步骤:

1. 任何浏览器(手机 / 电脑均可)打开 `https://github.com/<USERNAME>/proxy-rules`
2. 点击 `proxy-list.txt`
3. 右上角铅笔图标 ✏️ → 进入编辑模式
4. 滚到合适的分组(如 `# ===== Google =====`),加一行 / 删一行
5. 滚到底部 → 写 commit 信息(如:`add reddit.com`)→ 点 **Commit changes**
6. 切到 **Actions** 标签 → 等约 30 秒,看到绿色对勾 ✅
7. 等待客户端订阅周期(或手动刷新单个客户端)即可同步

![网页编辑截图](images/daily-ops-web-edit.png)

**手机操作小贴士**:

- iPhone Safari / Chrome 都能编辑,但建议横屏。
- 推荐用 **GitHub Mobile App**,编辑体验比网页好。

**域名书写规范**(无论用哪种工具都适用):

- 写**根域名**(`reddit.com`),不要写子域(`old.reddit.com`)——工具会自动匹配子域。
- **不带**协议前缀(不要写 `https://`)。
- **不带** `domain:` 等前缀(脚本会自动加)。
- 不要写通配符(`*.example.com` 不允许)。
- 加到合适的分组下,保持原有的注释结构。

---

## 章节 3:场景 B — 复杂任务(Claude.ai 网页 Code)

**何时用 Claude.ai 网页版的 Code 功能**:

- 想加一个新服务,但不确定它有几个相关域名(让 AI 帮你查)。
- 想批量整理(比如「把所有 Google 相关合并到一个分组」)。
- 想检查现有规则是否完整(比如「我的 Binance 规则有没有遗漏 CDN?」)。
- 想做规则审计(「分析一下哪些域名没必要代理」)。

### 使用前的一次性准备

**a. 生成 GitHub Personal Access Token(PAT-DailyOps)**

- 关键配置:Token name `proxy-rules-daily-ops`,**1 年**期限,**仅授权本仓库**,权限 **Contents(Read/Write)+ Actions(Read)**。
- ⚠️ 注意区分:此 token 与初次部署用的 **PAT-Deploy 不同**——权限更小、期限更长、只能动这一个仓库。
- 详细生成步骤见本仓库根目录的 `proxy-rules-design-doc.md` 附录 D.2,或下方「PAT-DailyOps 生成速查」。
- 复制 token(**只显示一次**,丢失需重新生成)。

**b. 在 Claude.ai 创建一个项目(Project)**

- 项目名:`proxy-rules 运维`
- 在 Project 的「项目说明 / 自定义指令」中粘贴下方标准 prompt 模板。

**c. 把 PAT 存到密码管理器**(1Password / Apple Keychain / Windows Credential Manager / Bitwarden),**Claude.ai 里不要长期存**。

### 标准 prompt 模板(每次新对话开头粘贴一次)

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

### 典型对话示例

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

### PAT-DailyOps 生成速查

1. 浏览器访问 `https://github.com/settings/personal-access-tokens/new`
2. 填写:

   | 字段 | 值 |
   |---|---|
   | Token name | `proxy-rules-daily-ops` |
   | Expiration | `1 year` |
   | Repository access | **Only select repositories** → 仅勾选 `proxy-rules` |

3. Repository permissions:

   | 权限项 | 值 |
   |---|---|
   | Contents | Read and write |
   | Actions | Read |
   | Metadata | Read(自动) |
   | 其他所有项 | No access |

4. **Generate token** → 复制 → 存入密码管理器。

---

## 章节 4:场景 C — 项目重大改动(PC 本地 Claude Code)

**何时需要 PC 本地版**:

- 改架构(比如增加 Clash YAML 输出格式)。
- 改自动化流水线(改 `generate.py` / `generate.yml`)。
- 排查复杂 bug。

这种场景很少见。如果遇到,直接在本地 `cd` 到仓库目录,运行 `claude` 即可。

---

## 章节 5:三层模式的边界守则

**永远不要**:

- ❌ 同一时刻在多个客户端编辑 `proxy-list.txt`(可能产生 git 冲突)。
- ❌ 把 GitHub PAT 写在公开仓库的任何文件里。
- ❌ 用 Claude.ai 网页版做简单的「加一个域名」(浪费 token,网页直接改更快)。

**始终要**:

- ✅ 任何修改都通过 git commit,不要绕过版本控制。
- ✅ commit message 写清楚改了什么。
- ✅ 改完后看一眼 Actions 是否成功。

---

## 章节 6:常见问题

| 问题 | 答案 |
|---|---|
| Claude.ai 网页 Code 改了规则,V2RayN 没更新? | V2RayN 默认手动更新订阅,不是自动。手动刷新一次订阅即可。 |
| 多设备同时改了规则冲突? | GitHub 会 reject 第二次 push,改用 pull → 合并 → push。 |
| PAT 不小心泄露了? | 立即去 GitHub Settings → Personal access tokens **Revoke**,再重新生成。 |
| 手机上不方便复制 PAT? | 用密码管理器(1Password 等)的自动填充功能。 |
