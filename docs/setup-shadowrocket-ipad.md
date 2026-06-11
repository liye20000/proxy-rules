# iPad Shadowrocket 配置指南

适用于 **iPad 上的 Shadowrocket(小火箭)**。配置逻辑与 iPhone 完全一致,本文重点说明 iPad 上的安装与两种配置方式。

> 前提:你已在 Shadowrocket 里配好机场节点(本项目不管节点)。

---

## 安装:用同一个 Apple ID

iPad 上的 Shadowrocket 是付费 App,但**与 iPhone 共享购买**:用与 iPhone **相同的 Apple ID** 登录 App Store,在「已购买」列表里直接免费下载即可,无需二次付费。

![iPad 已购列表](images/sr-ipad-purchased.png)

---

## 你需要的订阅 URL

把 `YOUR_USERNAME` 换成你的 GitHub 用户名:

```
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/shadowrocket.conf
```

> 同 iPhone:这是一个**只含规则、不含节点**的 Shadowrocket 配置;`PROXY` 表示走你在首页选中的机场节点。

---

## 配置方法 1:直接添加远程配置(推荐,与 iPhone 相同)

1. 打开 Shadowrocket → **「配置」→「远程文件」**(**不是**「设置」)。
2. 右上角 **「+」** → 在 URL 处粘贴上面的 `shadowrocket.conf` raw URL → **下载**。
3. 选中 `proxy-rules 白名单分流` 配置 → 首页选好节点 → 首页顶部 **「全局路由」设为「配置」**。

详细每一步见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md)。

---

## 配置方法 2:用 iCloud Sync 自动同步(最省事)

如果 iPhone 已经配好,且三端用同一 Apple ID,可让配置自动同步过来:

1. 在 **iPhone 和 iPad** 上都:Shadowrocket → **设置(Settings)** → 打开 **iCloud Sync / iCloud 同步**。
2. 稍等片刻,iPhone 上的配置(含 `proxy-rules` 远程配置)会同步到 iPad。
3. iPad 上选中该配置 → 选好节点 → 路由设为「配置」即可。

> 提示:iCloud Sync 同步的是**配置与规则**,节点订阅也会一并同步;你只需在每台设备各自选一次要用的节点。

---

## 验证

用 Safari 访问白名单网站(如 `claude.ai`)能打开即生效。问题见 [troubleshooting.md](troubleshooting.md)。
