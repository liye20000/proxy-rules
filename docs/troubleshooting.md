# 故障排查

按症状查找。本项目只管规则,**节点 / 网络相关的问题请找你的机场**。

---

## 速查表

| 症状 | 可能原因 | 解决 |
|---|---|---|
| Actions 跑失败,红色 ❌ | 权限不够 / 脚本异常 | 检查 **Settings → Actions → General → Workflow permissions** 设为 **Read and write**;再看运行日志定位脚本错误 |
| Actions 跑成功但没有新 commit | 派生文件没变化(预期行为) | 不是问题。只有 `proxy-list.txt` 实际改动导致派生文件变化时才会自动提交 |
| 订阅 URL 拉不到内容 | URL 拼错 / 网络问题 | 浏览器直接打开该 raw URL,确认能看到内容;检查用户名 / 仓库名 / 分支名 |
| 在 Shadowrocket「设置」里找不到规则 | 找错地方了 | 规则**不在「设置」**;在 **「配置 → 模块」** 添加 `shadowrocket.module`,见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md) |
| 导入后看不到「proxy-rules 白名单分流」 | 看的是配置列表 | 配置按**文件名**显示(如 `shadowrocket.conf`);`#!name=` 的名字只在**模块**列表显示。推荐用「模块」方式 |
| 换成本项目配置后**节点消失了** | 用了「替换配置」而非「模块」 | 你的节点在机场那份配置里。改用 **「模块」** 叠加(不动节点);见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md) |
| Shadowrocket 加了模块但所有网站都直连 | 模块没启用 / 路由模式不对 | 启用 `proxy-rules` 模块,并把首页「全局路由」设为 **「配置」**(不是「直连」) |
| Shadowrocket 白名单网站连不上 | 没选节点 / 节点失效 | 首页选中一个机场节点(规则里的 `PROXY` = 选中的节点);节点失效就换一个 |
| 开了小火箭后国内 App(银行 / 网上国网等)打不开 | 代理类型干扰 | Shadowrocket → 设置 → 代理,把代理类型从 `http` 改为 `none`(tun 模式) |
| 某网站没走代理 | 域名不在白名单 / 规则未刷新 | 在 `proxy-list.txt` 添加该域名;手动刷新客户端订阅 |
| Claude Code / curl 报 `ECONNRESET` | 代理节点不稳定 | 换节点,与本项目无关 |
| Cloudflare 返回 `403` | 代理节点 IP 被风控 | 换节点,与本项目无关 |

---

## 详解

### Actions 失败(红色 ❌)

1. 进入仓库 **Actions** 标签 → 点开失败的运行 → 看红色步骤日志。
2. 最常见原因是**工作流权限**:**Settings → Actions → General → Workflow permissions** 必须是 **Read and write permissions**,否则 bot 无法 commit。
3. 如果是 `generate.py` 报错,日志会显示 Python traceback;通常是 `proxy-list.txt` 内容异常(如整个文件被清空)。

### 订阅 URL 拉不到内容

确认 URL 结构(把占位符换成你的真实值):

```
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/v2rayn-rules.json
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/shadowrocket.module
```

- 用户名 / 仓库名拼写正确?
- 分支是 `main`(不是 `master`)?
- 仓库是 **Public**?Private 仓库的 raw URL 需要鉴权,客户端拉不到。

### 改了规则但客户端没更新

- **V2RayN 默认手动更新订阅**——需要你手动点一次「更新订阅」。
- Shadowrocket 在「配置 → 模块」里对 `proxy-rules` 做一次更新 / 刷新,再断开重连一次。
- 确认 Actions 已经跑完并生成了新派生文件(绿色 ✅)。

### 多设备同时改冲突

如果两台设备几乎同时 push,GitHub 会 reject 第二次 push。解决:先 `pull`(或网页上以最新版本为基础重新编辑)→ 合并 → 再提交。日常尽量**一处改**,避免并发编辑。

---

更多日常运维问题见 [daily-ops.md](daily-ops.md) 的「常见问题」章节。
