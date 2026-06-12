# CLAUDE.md — 给本地 Claude Code 的项目说明

本文件会在本地 Claude Code 启动时被自动读取。

## 项目一句话

代理规则自动同步系统:维护唯一主源 `proxy-list.txt`,GitHub Actions 自动生成各客户端规则文件。
仓库:https://github.com/liye20000/proxy-rules

## ⚠️ 开工前必做:先同步远程最新

`proxy-list.txt` 经常通过 **GitHub 网页**编辑,且 Actions 的 bot 会**自动提交**重新生成的派生文件。
因此本地仓库常常落后于远程。**每次在本地开始工作前,先拉取最新,避免基于旧代码改动或产生冲突:**

```bash
git pull --ff-only origin main
```

- 若提示有本地未提交改动导致无法快进:先 `git stash`(或提交/丢弃)再 `git pull`,然后视情况 `git stash pop`。
- 若出现分叉(本地也有提交):`git pull --rebase origin main` 后处理冲突。
- 公开仓库,`git pull` 无需鉴权;只有 `push` 才需要 PAT。

## 核心规则

- **只手动编辑两个主源**:`proxy-list.txt`(每行一个根域名)与 `proxy-ip-list.txt`(每行一个 CIDR,按 IP 段走代理的**手动**补充)。两者 `#` 均为注释。
- **`proxy-ip-auto.txt` 切勿手动改**:它由 `fetch_telegram_ips.py` 每天抓取 Telegram 各 ASN 的 BGP 网段(RIPEstat),`update-telegram-ips` 工作流会覆盖它。Telegram 的 IP 段无需人工维护。
- **绝不手动改派生文件**:`v2rayn-rules.json` / `shadowrocket.module` / `shadowrocket.conf` 都由 `generate.py` 生成,手改会被 Actions 覆盖。
- 改完务必本地自测:
  ```bash
  python generate.py      # 重新生成三个派生文件
  python -m pytest tests/ -q
  ```
- 改了 `proxy-list.txt` / `generate.py` / 工作流后 push 到 `main`,Actions 会自动重新生成并提交派生文件(约 30 秒)。

## 客户端订阅(派生文件)

- V2RayN(Windows):`v2rayn-rules.json`
- Shadowrocket(iPhone/iPad/iMac):`shadowrocket.module`(推荐,严格白名单、叠加不动节点);`shadowrocket.conf` 为替换式备选。

## 安全

- PAT 仅通过环境变量 `GH_TOKEN` 传给 `gh`;**绝不**写入任何文件 / commit / 日志。
- 日常运维(网页加删域名)不需要 PAT;只有本地创建仓库 / push 才需要。

## 更多

详见 `docs/`(`daily-ops.md` 为运维核心)与 `proxy-rules-design-doc.md`(设计规范)。
