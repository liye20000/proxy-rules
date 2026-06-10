# iPhone Shadowrocket 配置指南

适用于 **iPhone 上的 Shadowrocket(小火箭)**。本指南教你把本项目的 `proxy-list.txt` 配成规则集订阅。

> 前提:你已在 Shadowrocket 里配好机场节点(本项目不管节点)。

---

## 你需要的订阅 URL

把 `YOUR_USERNAME` 换成你的 GitHub 用户名:

```
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/proxy-list.txt
```

---

## 步骤 1:打开配置标签

打开 Shadowrocket → 底部 **配置(Config)** 标签。

![配置标签](images/sr-iphone-config-tab.png)

---

## 步骤 2:添加规则集

在「配置」页里找到规则相关区域,**添加一个规则集(Add Rule Set / 远程规则)**,填写:

| 字段 | 填写内容 |
|---|---|
| 类型(Type) | 规则集 / DOMAIN-SET(纯域名列表) |
| 链接(URL) | 上面那条 `proxy-list.txt` 的 raw URL |
| 目标(Policy / Outbound) | **PROXY**(走代理) |
| 更新间隔(Update Interval) | `86400`(秒,即 24 小时;可按需调小) |

![添加规则集](images/sr-iphone-add-ruleset.png)

---

## 步骤 3:规则集排序(重要)

⚠️ **排序决定优先级。** 本规则集(白名单 → PROXY)**必须排在** `GEOIP,CN` / `DIRECT` / `FINAL` 这类直连兜底规则**之前**,否则白名单域名可能被提前判为直连。

在规则列表里把 `proxy-list.txt` 规则集拖到靠前位置,确保:

```
1. proxy-list.txt 规则集 → PROXY      ← 本项目,放前面
2. GEOIP,CN → DIRECT
3. FINAL → DIRECT(或 PROXY,看你习惯)
```

---

## 步骤 4:启用代理 + iOS VPN 授权

1. 回到首页,选好你的机场节点。
2. 顶部开关打开「连接 / 启动」。
3. 首次启用时 iOS 会弹出 **VPN 配置授权**,点「允许」并用 Face ID / 密码确认。

---

## 步骤 5:验证

用 Safari 访问一个白名单网站(如 `claude.ai` 或 `youtube.com`),能正常打开即生效。

如需确认走的策略:Shadowrocket 首页 → 点开连接详情 / 全局路由,看目标域名命中的是不是 PROXY。

问题排查见 [troubleshooting.md](troubleshooting.md)。
