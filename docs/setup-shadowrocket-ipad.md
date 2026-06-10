# iPad Shadowrocket 配置指南

适用于 **iPad 上的 Shadowrocket(小火箭)**。配置逻辑与 iPhone 完全一致,本文重点说明 iPad 上的两种配置方式。

> 前提:你已在 Shadowrocket 里配好机场节点(本项目不管节点)。

---

## 安装:用同一个 Apple ID

iPad 上的 Shadowrocket 是付费 App,但**与 iPhone 共享购买**:用与 iPhone **相同的 Apple ID** 登录 App Store,在「已购买」列表里直接免费下载即可,无需二次付费。

![iPad 已购列表](images/sr-ipad-purchased.png)

---

## 你需要的订阅 URL

把 `YOUR_USERNAME` 换成你的 GitHub 用户名:

```
https://raw.githubusercontent.com/YOUR_USERNAME/proxy-rules/main/proxy-list.txt
```

---

## 配置方法 1:AirDrop 从 iPhone 传配置(最快)

如果 iPhone 已经配好:

1. iPhone Shadowrocket → 配置页 → 把当前 `.conf` 配置文件**分享 / 导出**。
2. 通过 **AirDrop** 发送到 iPad。
3. iPad 上接收后选择「用 Shadowrocket 打开」,配置(含规则集订阅)即导入完成。

---

## 配置方法 2:重复 iPhone 流程

如果不想用 AirDrop,直接在 iPad 上重复 iPhone 的配置步骤即可:

1. 打开配置标签 → 添加规则集。
2. 链接填上面的 `proxy-list.txt` raw URL。
3. 目标设为 **PROXY**,更新间隔 `86400`。
4. **排序**:规则集放在 `GEOIP,CN` / `DIRECT` / `FINAL` 之前(同 iPhone 指南的强调)。

详细字段说明见 [setup-shadowrocket-iphone.md](setup-shadowrocket-iphone.md)。

---

## 启用 iCloud Sync(推荐)

让 iPhone / iPad / iMac 三端配置自动同步:

1. Shadowrocket → **设置(Settings)** → 找到 **iCloud Sync / iCloud 同步**。
2. 打开开关。
3. 确保三台设备用**同一个 Apple ID** 且 iCloud 已登录。

启用后,在任一设备改了配置,其余设备会自动同步,无需逐台重配。

---

## 验证

用 Safari 访问白名单网站(如 `claude.ai`)能打开即生效。问题见 [troubleshooting.md](troubleshooting.md)。
