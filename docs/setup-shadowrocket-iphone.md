# iPhone Shadowrocket 配置指南

适用于 **iPhone 上的 Shadowrocket(小火箭)**,本指南基于 **2.2.x** 版本界面。

> 前提:你已在 Shadowrocket 里配好机场节点(本项目不管节点)。

> ⚠️ **重要更正**:规则**不在「设置」里**。早期版本的本文档让你去「设置」找规则区域,这是错的——「设置」底部只有「**服务器订阅**」(那是给机场节点用的)。本项目的规则要在 **「配置 / 远程文件」** 里添加。下面是正确流程。

---

## 你需要的订阅 URL

本项目为 Shadowrocket 生成了一个专用配置文件 `shadowrocket.conf`(**只含路由规则,不含任何节点信息**)。把 `YOUR_USERNAME` 换成你的 GitHub 用户名:

```
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/shadowrocket.conf
```

> 这个文件只决定「哪些域名走代理、哪些直连」。规则里的 **`PROXY`** 表示**走你在首页选中的那个节点**——节点仍然来自你的机场订阅,这个配置里没有也不需要任何节点 / 密码。

---

## 步骤 1:进入「配置 → 远程文件」

1. 打开 Shadowrocket。
2. 进入 **「配置」(Configuration)** 管理界面 → 选 **「远程文件」(Remote File)** 这一类。

> 注:不同小版本里,「配置」可能在底部标签,也可能在首页内的配置区。认准 **「远程文件 / Remote File」** 这个入口即可,**不要**去「设置」。

![配置-远程文件入口](images/sr-iphone-config-tab.png)

---

## 步骤 2:添加远程配置(粘贴 URL)

1. 点右上角 **「+」**(加号)。
2. 在 **URL / 链接** 处粘贴上面那条 `shadowrocket.conf` 的 raw URL。
3. 备注(可选)填 `proxy-rules`。
4. 点 **「下载」/ 保存**。下载成功后,配置列表里会出现 `proxy-rules 白名单分流`。

![添加远程配置](images/sr-iphone-add-ruleset.png)

---

## 步骤 3:选中该配置 + 选好节点 + 路由设为「配置」

要让规则真正生效,三件事都要到位:

1. **选中配置**:在配置列表里点一下 `proxy-rules 白名单分流`,把它设为当前生效的配置(左侧出现勾选标记)。
2. **选好节点**:回到 **首页**,在你的机场节点列表里选中一个要使用的节点。
3. **路由模式设为「配置」**:首页顶部的 **「全局路由」(Global Routing)** 设为 **「配置」(Configuration)** —— 只有这个模式才会按本规则分流(另两个选项「代理 / 直连」会忽略规则,全部走代理或全部直连)。

> 规则里的 `PROXY` 就会指向你刚选中的那个节点。

---

## 步骤 4:启用代理 + iOS VPN 授权

1. 回到首页,把顶部连接开关打开。
2. 首次启用时 iOS 会弹出 **VPN 配置授权**,点「允许」并用 Face ID / 密码确认。

---

## 步骤 5:验证

用 Safari 访问一个白名单网站(如 `claude.ai` 或 `youtube.com`),能正常打开即生效。

确认走的策略:Shadowrocket 首页 → 点开 **「连接 / 全局路由」** 详情,看目标域名命中的是不是 `PROXY`;访问一个国内网站(如 `baidu.com`)应命中 `DIRECT`。

---

## 更新规则

之后你在 GitHub 改了 `proxy-list.txt`,Actions 会自动重新生成 `shadowrocket.conf`。Shadowrocket 端让配置生效最新版:在「配置 / 远程文件」里对 `proxy-rules` 这条做一次 **更新 / 刷新**(下拉或点更新按钮),再断开重连一次即可。

遇到问题见 [troubleshooting.md](troubleshooting.md)。
