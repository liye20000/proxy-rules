# 如何添加 / 删除规则

本文教你增删代理规则。配合 [daily-ops.md](daily-ops.md) 一起看。

---

## 1. 核心原则

> **只改 `proxy-list.txt`,永远不要手动碰 `v2rayn-rules.json` 和 `shadowrocket.conf`。**

`v2rayn-rules.json`(V2RayN 用)和 `shadowrocket.conf`(Shadowrocket 用)都是 GitHub Actions 根据 `proxy-list.txt` **自动生成**的。你手动改它们会在下次 Actions 运行时被覆盖。

---

## 2. 操作步骤(网页编辑,最常用)

1. 浏览器打开 `https://github.com/<USERNAME>/proxy-rules`。
2. 点击 `proxy-list.txt` 进入文件。
3. 点右上角铅笔图标 ✏️ 进入编辑模式。
4. 在合适的分组下加一行域名(或删一行)。
5. 滚到底部填写 commit 信息(如 `add reddit.com`)→ **Commit changes**。
6. 切到 **Actions** 标签,等约 30 秒看到绿色对勾 ✅。

---

## 3. 域名书写规范

- ✅ 写**根域名**:`reddit.com`,而不是子域 `old.reddit.com`——工具会自动匹配所有子域。
- ✅ **不带**协议前缀:写 `reddit.com`,不要写 `https://reddit.com`。
- ✅ **不带** `domain:` 前缀:脚本会自动加。
- ❌ 不要写通配符:`*.reddit.com` 不允许。
- 注释:`#` 开头整行为注释;行内 `#` 之后也是注释。空行会被忽略。

示例:

```text
# ===== Reddit =====
reddit.com
redd.it
redditstatic.com    # 静态资源 CDN
```

---

## 4. 多分组管理建议

加新域名时,**归到合适的现有分组**(如把 `googlevideo.com` 放到 `# ===== Google =====` 下)。如果是全新服务,新建一个分组标题:

```text
# ===== 新服务名 =====
```

保持分组清晰,方便日后审计与维护。

---

## 5. 验证生效

1. **查看 Actions**:仓库 Actions 标签下,最新一次运行应为绿色 ✅(约 30 秒)。
2. **等待订阅周期**:各客户端按设置的更新间隔自动拉取;想立刻生效就手动刷新该客户端的订阅。
3. **实测**:
   - V2RayN:查看实时连接列表,看目标域名走的是 proxy。
   - Shadowrocket:首页看全局路由 / 连接详情,确认命中 PROXY。

---

## 6. 如何删除规则

同样编辑 `proxy-list.txt`,**删除对应那一行**,Commit 即可。Actions 会重新生成不含该域名的 JSON。

---

## 7. 如何回滚

改错了想恢复旧版本:

1. 仓库页面打开 `proxy-list.txt` → 点 **History**(历史)。
2. 找到改动前的那次 commit。
3. 用 **Revert** 撤销某次提交,或直接复制旧内容重新 Commit。
4. Actions 会基于回滚后的内容重新生成 JSON。

> 因为一切都走 git 版本控制,任何改动都可追溯、可回滚。
