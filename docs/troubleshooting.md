# 故障排查

按症状查找。本项目只管规则,**节点 / 网络相关的问题请找你的机场**。

---

## 速查表

| 症状 | 可能原因 | 解决 |
|---|---|---|
| Actions 跑失败,红色 ❌ | 权限不够 / 脚本异常 | 检查 **Settings → Actions → General → Workflow permissions** 设为 **Read and write**;再看运行日志定位脚本错误 |
| Actions 跑成功但没有新 commit | JSON 没变化(预期行为) | 不是问题。只有 `proxy-list.txt` 实际改动导致 JSON 变化时才会自动提交 |
| V2RayN 订阅 URL 拉不到内容 | URL 拼错 / 网络问题 | 浏览器直接打开该 raw URL,确认能看到 JSON;检查用户名 / 仓库名 / 分支名 |
| Shadowrocket 规则集订阅后规则数为 0 | URL 错误 / 文件为空 | 浏览器直接打开 `proxy-list.txt` raw URL 检查是否有内容 |
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
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/proxy-list.txt
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/v2rayn-rules.json
```

- 用户名 / 仓库名拼写正确?
- 分支是 `main`(不是 `master`)?
- 仓库是 **Public**?Private 仓库的 raw URL 需要鉴权,客户端拉不到。

### 改了规则但客户端没更新

- **V2RayN 默认手动更新订阅**——需要你手动点一次「更新订阅」。
- Shadowrocket 按更新间隔自动拉,等待周期或手动刷新。
- 确认 Actions 已经跑完并生成了新 JSON(绿色 ✅)。

### 多设备同时改冲突

如果两台设备几乎同时 push,GitHub 会 reject 第二次 push。解决:先 `pull`(或网页上以最新版本为基础重新编辑)→ 合并 → 再提交。日常尽量**一处改**,避免并发编辑。

---

更多日常运维问题见 [daily-ops.md](daily-ops.md) 的「常见问题」章节。
