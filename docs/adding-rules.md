# 如何添加 / 删除规则

本文教你增删代理规则。配合 [daily-ops.md](daily-ops.md) 一起看。

---

## 1. 核心原则

> **只改 `proxy-list.txt`,永远不要手动碰 `v2rayn-rules.json` / `shadowrocket.module` / `shadowrocket.conf`。**

`v2rayn-rules.json`(V2RayN 用)、`shadowrocket.module` 和 `shadowrocket.conf`(Shadowrocket 用)都是 GitHub Actions 根据 `proxy-list.txt` **自动生成**的。你手动改它们会在下次 Actions 运行时被覆盖。

---

## 2. 操作步骤(网页编辑,最常用)

1. 浏览器打开 `https://github.com/liye20000/proxy-rules`。
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

## 4.5 按 IP 段走代理(IP 主源)

有些服务的核心连接**不经域名/DNS,直接连 IP**(最典型的是 **Telegram**:App 用 MTProto 直连数据中心 IP)。这类服务只加域名是不够的,必须按 **IP 段(CIDR)** 走代理。共有两个 IP 主源,生成时**合并去重**:

| 文件 | 谁维护 | 内容 |
|---|---|---|
| `proxy-ip-auto.txt` | **机器人自动**(每天) | Telegram 各 ASN 的实时 BGP 网段,由 `fetch_telegram_ips.py` 抓取(数据源 RIPEstat)。**切勿手动编辑**,每天会被覆盖。 |
| `proxy-ip-list.txt` | 你手动 | 除 Telegram 外、你想按 IP 走代理的额外网段。 |

**Telegram 不用你管**——`update-telegram-ips` 工作流每天自动更新 `proxy-ip-auto.txt` 并重新生成规则。若 Telegram 临时改了 IP 段,最多一天内自动跟上(也可在 Actions 页手动 **Run workflow** 立即更新)。

**手动加别的 IP 段**:编辑 `proxy-ip-list.txt`,每行一个 CIDR(IPv4 或 IPv6),`#` 注释规则同上。写法用标准网段:`203.0.113.0/24`、`2a0a:f280::/32`;脚本会用 `ipaddress` 校验并规范化,主机位写错也会自动归一(如 `1.2.3.4/24` → `1.2.3.0/24`)。

这些 IP 段会被生成为:V2RayN 里一条独立的 `proxy` 路由(`ip` 数组);Shadowrocket 里 `IP-CIDR / IP-CIDR6 ... ,PROXY,no-resolve`,且**排在国内直连之前**,所以非 CN 的 IP 也能正确走代理。两个文件都为空/不存在时,只生成域名白名单规则(行为与以前一致)。

> 提示:Telegram 的网页/登录/`t.me`/下载仍走域名,所以 `telegram.org`、`t.me` 等域名留在 `proxy-list.txt` 里;IP 段负责 App 的消息收发。两者配合才完整。

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
