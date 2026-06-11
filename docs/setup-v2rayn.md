# Windows V2RayN 配置指南

适用于 **V2RayN v6.x**(Windows)。本指南教你把本项目生成的 `v2rayn-rules.json` 配成订阅,让 V2RayN 按白名单路由。

> 前提:你已在 V2RayN 里配好机场节点(本项目不管节点)。

---

## 你需要的订阅 URL

你的订阅 URL(可直接复制使用):

```
https://raw.githubusercontent.com/liye20000/proxy-rules/main/v2rayn-rules.json
```

---

## 步骤 1:打开路由设置

V2RayN 主菜单 → **设置(Settings)** → **路由设置(Routing Setting)**。

![路由设置入口](images/v2rayn-routing-entry.png)

---

## 步骤 2:添加规则集订阅

在路由设置窗口里找到「规则集 / 自定义规则集」相关区域,**添加一个规则集**,填写:

| 字段 | 填写内容 |
|---|---|
| 别名(Remarks) | `proxy-rules`(任意,便于识别) |
| 域名解析策略(domainStrategy) | `IPIfNonMatch`(推荐默认即可) |
| **可选地址(URL)** | 上面那条 `v2rayn-rules.json` 的 raw URL |

填好「可选地址(URL)」后,V2RayN 会从该 URL 拉取规则内容。

![添加规则集](images/v2rayn-add-ruleset.png)

---

## 步骤 3:手动触发更新订阅

第一次添加后,需要让 V2RayN 拉一次规则:

- 在规则集列表上右键 → **更新订阅 / 重新加载**,或
- 主界面菜单 → **订阅(Subscription)** → **更新订阅(无需代理 / 通过代理)**。

更新后,规则集里应能看到 4 条规则(proxy / block / direct / direct 兜底)。

---

## 步骤 4:启用系统代理

主界面右下角(或菜单)把系统代理模式设为 **自动配置系统代理(PAC)** 或 **全局**,根据你的习惯选择。本项目的规则已经做了白名单分流,推荐配合 V2RayN 的路由模式使用。

---

## 步骤 5:给命令行工具配置代理(可选)

如果你要让 `curl` / `git` / `claude` 等 CLI 工具走代理,在 PowerShell 里设置环境变量(端口换成你 V2RayN 实际的 HTTP 端口,默认常见为 `10809`):

```powershell
$env:HTTPS_PROXY = "http://127.0.0.1:10809"
$env:HTTP_PROXY  = "http://127.0.0.1:10809"
```

> 这只在当前终端会话有效。需要永久生效请在「系统环境变量」里设置。

---

## 步骤 6:验证

访问一个白名单网站(如 `claude.ai`)能正常打开即可。进阶验证用 `curl` 检查是否命中 Cloudflare(说明走了代理):

```powershell
curl -I https://claude.ai
```

返回头里出现 `cf-ray:` 字段,说明请求经由 Cloudflare(通常即走了代理)。如果访问超时或被重置,检查:

- 节点是否连通(与本项目无关,属于机场问题);
- 该域名是否在 `proxy-list.txt` 白名单里;
- 订阅是否已更新到最新。

---

## 步骤 7:查看哪些地址走代理 / 哪些走直连

V2RayN 没有像 Shadowrocket「测试规则」那样的单域名测试界面,看路由用以下两种方式:

**方式 A:实时连接列表(推荐)**

1. V2RayN 主界面菜单 → 打开 **「连接」/ 实时连接** 视图(部分版本在底部标签或「查看 → 连接」)。
2. 列表里每条连接会显示目标地址和命中的**出站(outbound)**:
   - `proxy` → 走代理;
   - `direct` → 直连;
   - `block` → 被拦截(广告)。
3. 在浏览器访问某网站,再回来看对应连接走的是 `proxy` 还是 `direct`。

**方式 B:看日志**

1. **设置 → 参数设置**,把 **日志级别(loglevel)** 设为 `info`(或 `debug`)。
2. 主界面下方的日志区 / **「查看日志」** 会打印每个请求命中的路由,据此判断走向。
3. 排查完建议把日志级别调回 `warning`,减少刷屏。

> 对照预期:白名单域名(`claude.ai` 等)应为 `proxy`;国内/其余域名应为 `direct`。

更多问题见 [troubleshooting.md](troubleshooting.md)。
