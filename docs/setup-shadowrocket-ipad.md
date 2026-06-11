# iPad Shadowrocket 配置指南

适用于 **iPad 上的 Shadowrocket(小火箭)**。配置逻辑与 iPhone 完全一致,本文重点说明 iPad 上的安装与两种配置方式。

> 前提:你已在 Shadowrocket 里配好机场节点(本项目不管节点)。

---

## 安装:用同一个 Apple ID

iPad 上的 Shadowrocket 是付费 App,但**与 iPhone 共享购买**:用与 iPhone **相同的 Apple ID** 登录 App Store,在「已购买」列表里直接免费下载即可,无需二次付费。

![iPad 已购列表](images/sr-ipad-purchased.png)

---

## 你需要的订阅 URL(模块)

把 `YOUR_USERNAME` 换成你的 GitHub 用户名:

```
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/shadowrocket.module
```

> 同 iPhone:这是一个**只含规则、不含节点**的 Shadowrocket **模块**,叠加在你机场配置之上、不动节点;`PROXY` 表示走你在首页选中的机场节点。

---

## 配置方法 1:添加远程模块(推荐,与 iPhone 相同)

1. 打开 Shadowrocket → **「配置」→「模块」**(**不是**「设置」)。
2. 右上角 **「+」** → 在 URL 处粘贴上面的 `shadowrocket.module` raw URL → **下载** → 启用该模块。
3. 回首页选好节点 → 首页顶部 **「全局路由」设为「配置」**。

详细每一步(含「为什么用模块而不是替换配置」)见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md)。

---

## 配置方法 2:用 iCloud Sync 自动同步(最省事)

如果 iPhone 已经配好,且三端用同一 Apple ID,可让配置自动同步过来:

1. 在 **iPhone 和 iPad** 上都:Shadowrocket → **设置(Settings)** → 打开 **iCloud Sync / iCloud 同步**。
2. 稍等片刻,iPhone 上的模块与配置(含 `proxy-rules` 模块)会同步到 iPad。
3. iPad 上确认 `proxy-rules` 模块已启用 → 选好节点 → 路由设为「配置」即可。

> 提示:iCloud Sync 同步的是**模块与配置**,节点也会一并同步;你只需在每台设备各自选一次要用的节点。

---

## 验证

用 Safari 访问白名单网站(如 `claude.ai`)能打开即生效。想精确查看某域名走代理还是直连,用 **「配置 → 测试规则」**(输入域名看 PROXY/DIRECT)或 **「数据」** 标签看实时连接——详见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md#步骤-5验证)。问题见 [troubleshooting.md](troubleshooting.md)。
