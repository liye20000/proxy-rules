# 快速上手(10 分钟)

本指南帮你在约 10 分钟内完成端到端配置:从拥有自己的 `proxy-rules` 仓库,到四台设备开始自动同步代理规则。

> 本项目只管**路由规则**,不管代理节点。开始前请确保你已有一个第三方机场的订阅(节点来源)。

---

## 前置条件

- ✅ 已有 GitHub 账号
- ✅ 已有代理机场订阅(节点 URL,本项目不提供节点)
- ✅ 已在各设备装好基础客户端:
  - Windows:V2RayN v6.x
  - iPhone / iPad / iMac:Shadowrocket

---

## 第一阶段:创建你自己的仓库

如果你是从模板创建:

1. 打开本项目仓库页面。
2. 点右上角 **Use this template**(或 **Fork**)。
3. 仓库名建议保持 `proxy-rules`,可见性选 **Public**(订阅 URL 需要无鉴权访问)。
4. 创建完成后,你就有了自己的 `https://github.com/<你的用户名>/proxy-rules`。

![创建仓库截图](images/quickstart-create-repo.png)

---

## 第二阶段:获取订阅 URL

raw URL 的拼接方式(把 `YOUR_USERNAME` 换成你的 GitHub 用户名):

```
# V2RayN 专用(Windows 用)
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/v2rayn-rules.json

# Shadowrocket 专用(iPhone / iPad / iMac 用)— 推荐「模块」
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/shadowrocket.module
```

> 注:`proxy-list.txt` 是你手动维护的**主源**,不直接给客户端订阅;客户端订阅上面由 Actions **自动生成**的派生文件。Shadowrocket 用 `.module`(叠加在机场配置上、不动节点);另有 `shadowrocket.conf` 备选,见各平台指南。

**验证 URL 可用**:把上面两个 URL 直接粘到浏览器打开,应该能看到 JSON / 配置文本内容。看不到内容请见 [troubleshooting.md](troubleshooting.md)。

---

## 第三阶段:在各客户端配置订阅

按你的设备查看对应详细指南:

| 设备 | 指南 |
|---|---|
| Windows V2RayN | [setup-v2rayn.md](setup-v2rayn.md) |
| iPhone Shadowrocket | [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md) |
| iPad Shadowrocket | [setup-shadowrocket-ipad.md](setup-shadowrocket-ipad.md) |
| iMac Shadowrocket | [setup-shadowrocket-mac.md](setup-shadowrocket-mac.md) |

![客户端配置截图](images/quickstart-client-config.png)

---

## 第四阶段:验证

1. 确保代理客户端已连接你的机场节点。
2. 访问一个在白名单里的网站(如 `claude.ai` 或 `youtube.com`)。
3. 能正常打开 → 规则生效。
4. 进阶验证(Windows):用 `curl` 检查是否走了代理,详见 [setup-v2rayn.md](setup-v2rayn.md) 的验证章节。

---

## 接下来

- 想加 / 删域名?→ 90% 的场景看 [daily-ops.md](daily-ops.md)(必看)。
- 想了解原理?→ [architecture.md](architecture.md)。
- 遇到问题?→ [troubleshooting.md](troubleshooting.md)。
