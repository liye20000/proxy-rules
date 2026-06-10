# 架构与原理

面向想理解项目内部机制的读者。日常使用不需要读本文。

---

## 1. 完整数据流

```
                  ┌──────────────────────────────┐
                  │     GitHub Repository         │
                  │                              │
                  │   proxy-list.txt (主源)       │
                  │       ↓ generate.py          │
                  │   v2rayn-rules.json (派生)    │
                  └──────────────┬───────────────┘
                                 │ HTTP 订阅(raw URL)
            ┌────────────────────┼────────────────────┐
            ↓                    ↓                    ↓
   ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐
   │ Windows V2RayN │  │  Apple 三端       │  │  (未来扩展)      │
   │ 订阅:          │  │  Shadowrocket     │  │                 │
   │ v2rayn-rules   │  │  订阅:           │  │                 │
   │ .json          │  │  proxy-list.txt  │  │                 │
   └────────────────┘  └──────────────────┘  └─────────────────┘
```

核心思路:**单一数据源(Single Source of Truth)+ 自动派生**。用户只维护 `proxy-list.txt`,其余格式由 CI 自动生成。

---

## 2. 为什么需要两种格式

不同客户端的规则配置格式不兼容:

| 客户端 | 格式 | 订阅的文件 |
|---|---|---|
| V2RayN v6.x | Xray-core JSON(路由规则数组) | `v2rayn-rules.json` |
| Shadowrocket | 纯文本域名列表 / Clash 系语法 | `proxy-list.txt` |

Shadowrocket 能直接消费纯文本域名列表,所以它**直接订阅主源** `proxy-list.txt`。V2RayN 需要结构化的 JSON 路由规则,所以需要 `generate.py` 转换。

---

## 3. Python 脚本的工作原理

`generate.py` 只用标准库(`json` / `re` / `pathlib` / `sys`),三个核心函数:

- `parse_domain_list(text)`:把纯文本解析成干净的域名列表——去注释、去空行、去行内注释、小写化、去重(保持顺序)、正则校验基本域名格式。
- `generate_v2rayn_rules(domains)`:生成固定 4 条路由规则:
  1. **proxy**:所有白名单域名加 `domain:` 前缀 → 走代理。
  2. **block**:`geosite:category-ads-all` → 拦截广告。
  3. **direct**:`geosite:private` / `geosite:cn` + `geoip:private` / `geoip:cn` → 国内与局域网直连。
  4. **direct 兜底**:`port: 0-65535` → 其余全部直连。
- `main()`:读文件 → 解析 → 生成 → 以 2 空格缩进、`ensure_ascii=False`、末尾换行写出 JSON。

错误处理:主源不存在、解析后域名为空都会打印错误并返回退出码 1。

规则顺序很重要:Xray-core 按数组顺序匹配,白名单 proxy 在最前,兜底 direct 在最后。

---

## 4. GitHub Actions 工作流原理

`.github/workflows/generate.yml`:

- **触发**:push 到 `main` 且改动命中 `proxy-list.txt` / `generate.py` / 工作流自身;或手动 `workflow_dispatch`。
- **权限**:`contents: write`,允许 bot 提交回仓库。
- **步骤**:checkout → 装 Python → 跑 `generate.py` → `git diff --quiet v2rayn-rules.json` 判断是否有变化 → 有变化才以 `github-actions[bot]` 身份 commit & push。

**防死循环**:工作流的 `paths` 过滤器**只监听 `proxy-list.txt` 等输入文件,不监听 `v2rayn-rules.json`**。所以 bot 提交生成结果不会再次触发自己。

---

## 5. 安全性说明(为什么仓库可以 Public)

- 仓库内容只是**公开域名的白名单**和转换脚本,**不含任何节点信息、密钥、账号**。
- 公开反而简化订阅:raw URL 无需鉴权即可被客户端拉取。
- 鉴权用 fine-grained PAT 且范围仅限本仓库;即便泄露,影响也被限制在这一个仓库内(详见根目录设计文档第 11 节与附录 D)。

---

## 6. 性能考虑

- **订阅频率**:客户端按 1~24 小时的间隔拉取。raw URL 由 GitHub / CDN 缓存,通常有几分钟的缓存延迟,属正常现象。
- **Actions 时长**:从 push 到生成完成约 30 秒。
- **文件体积**:纯文本与 JSON 都很小(KB 级),拉取开销可忽略。

---

## 7. 未来扩展(本次未实现)

留作方向参考,当前不实现:

1. **多 client format 输出**:扩展 `generate.py` 生成 Clash YAML / Surge `.conf` / Sing-box JSON。
2. **GitHub Pages**:把 `docs/` 部署为静态网站。
3. **pre-commit 钩子**:提交前自动跑 `pytest`。
4. **dependabot**:自动升级 Actions 版本。
5. **多分组导出**:为不同设备生成不同子集的规则。
