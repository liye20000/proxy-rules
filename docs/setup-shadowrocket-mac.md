# iMac Shadowrocket 配置指南(Apple Silicon)

适用于 **Apple Silicon Mac(M1 / M2 / M3 / M4)**,如本项目用户的 M2 iMac。Shadowrocket 本是 iOS App,在 Apple Silicon Mac 上可直接安装运行。

> 前提:你已在 Shadowrocket 里配好机场节点(本项目不管节点)。

---

## Apple Silicon Mac 专属安装方法

1. 打开 **Mac App Store**,搜索 **Shadowrocket**。
2. 搜索结果默认可能只显示 Mac App。点筛选 / 切换到 **「iPhone 与 iPad App」** 标签。
3. 用与 iPhone **同款 Apple ID** 登录。由于已在 iPhone 端购买,这里可**已购免费安装**。
4. 安装后在「启动台」里像普通 Mac App 一样打开。

![Mac App Store iPhone/iPad App 筛选](images/sr-mac-appstore-filter.png)

---

## Intel Mac 的替代方案(简短)

Intel(x86)Mac **无法**直接安装 iOS 版 Shadowrocket。建议:

- 改用 **Stash**(Mac 原生,规则语法兼容)或 ClashX 等客户端;
- 或考虑升级到 Apple Silicon 机型。

本指南后续步骤以 Apple Silicon 为准。

---

## iOS App 在 Mac 上的交互特点

iOS App 跑在 Mac 上时,**原本的触屏手势会映射成鼠标操作**:

- 「点按」= 鼠标左键单击。
- 「长按」= 按住鼠标左键不放。
- 列表拖动排序 = 按住后拖拽。

界面与 iPhone 版几乎一致,只是窗口化显示。

---

## 配置订阅

本项目为 Shadowrocket 生成了专用**模块** `shadowrocket.module`(**只含规则,不含节点**,叠加在你机场配置上、不动节点)。你的订阅 URL(可直接复制使用):

```
https://raw.githubusercontent.com/liye20000/proxy-rules/main/shadowrocket.module
```

配置步骤与 iPhone 相同(注意:在 **「配置 → 模块」**,不是「设置」):

1. **「配置」→「模块」** → 右上角 **「+」** → 粘贴上面的 raw URL → **下载** → 启用模块。
2. 首页选好节点 → 首页顶部 **「全局路由」设为「配置」**。

详见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md)(含「为什么用模块而不是替换配置」)。

---

## VPN 配置弹窗授权

首次启用时,macOS 会弹出**「Shadowrocket 想要添加 VPN 配置」**的系统弹窗,点 **允许**,并用密码 / Touch ID 确认。

---

## 与 iPhone / iPad 通过 iCloud Sync 同步

1. Shadowrocket → 设置 → **iCloud Sync** 打开。
2. 三台设备用同一 Apple ID。

之后任一端改配置,三端自动同步;每台设备各自选一次要用的节点即可。

---

## 验证

Safari 访问白名单网站(如 `claude.ai`)能打开即生效。想精确查看某域名走代理还是直连,用 **「配置 → 测试规则」**(输入域名看 PROXY/DIRECT)或 **「数据」** 标签看实时连接——详见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md#步骤-5验证)。问题见 [troubleshooting.md](troubleshooting.md)。
