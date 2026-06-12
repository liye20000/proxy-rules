#!/usr/bin/env python3
"""自动抓取 Telegram 各 ASN 实际宣告的 IP 段,写入 proxy-ip-auto.txt。

数据源:RIPEstat announced-prefixes API(免费、免鉴权、稳定)。查询 Telegram
名下的多个 ASN 实际对外宣告的 BGP 前缀,汇总去重后写出。这是事实上最权威的
Telegram IP 段来源——Telegram 没有公开的官方 IP 列表接口。

安全兜底:任一 ASN 抓取失败、或汇总结果为空,直接报错退出(返回 1)且**不写文件**,
避免把规则清空。只用标准库,可独立运行:

    python fetch_telegram_ips.py

退出码:成功 0,失败 1。
"""

import json
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "proxy-ip-auto.txt"

# Telegram 官方 ASN(Telegram Messenger Inc / Network / Amsterdam 等)
TELEGRAM_ASNS = [62041, 62014, 59930, 44907, 211157]
RIPESTAT_URL = "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}"
TIMEOUT = 30


def parse_ripestat_prefixes(payload: dict) -> list[str]:
    """从 RIPEstat announced-prefixes 响应里提取 prefix 列表。

    :param payload: 已解析的 JSON 字典
    :return: CIDR 字符串列表
    """
    return [p["prefix"] for p in payload["data"]["prefixes"]]


def fetch_asn_prefixes(asn: int) -> list[str]:
    """抓取单个 ASN 的宣告前缀(出错会抛异常,由 main 统一处理)。"""
    url = RIPESTAT_URL.format(asn=asn)
    req = urllib.request.Request(url, headers={"User-Agent": "proxy-rules-bot"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return parse_ripestat_prefixes(payload)


def collect_telegram_cidrs() -> list[str]:
    """汇总所有 Telegram ASN 的前缀,去重(保持首次出现顺序)。"""
    seen: set[str] = set()
    cidrs: list[str] = []
    for asn in TELEGRAM_ASNS:
        for prefix in fetch_asn_prefixes(asn):
            if prefix not in seen:
                seen.add(prefix)
                cidrs.append(prefix)
    return cidrs


def render(cidrs: list[str]) -> str:
    """渲染为 proxy-ip-auto.txt 文本。

    IPv4 / IPv6 分组并各自排序,保证输出稳定(便于「有变化才提交」)。
    """
    v4 = sorted(c for c in cidrs if ":" not in c)
    v6 = sorted(c for c in cidrs if ":" in c)
    lines = [
        "# 自动生成,切勿手动编辑!",
        "# 由 fetch_telegram_ips.py 抓取 Telegram 各 ASN 的 BGP 宣告网段(数据源:RIPEstat)。",
        "# 手动维护的 IP 段请写到 proxy-ip-list.txt;本文件每天由 GitHub Actions 覆盖更新。",
        "",
        "# ===== Telegram(自动 · IPv4)=====",
        *v4,
        "",
        "# ===== Telegram(自动 · IPv6)=====",
        *v6,
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    """主入口:抓取 → 校验非空 → 写出。失败/为空均不写文件。"""
    try:
        cidrs = collect_telegram_cidrs()
    except Exception as exc:  # 网络/解析任何异常都视为失败,绝不写文件
        print(f"错误:抓取 Telegram IP 段失败:{exc}", file=sys.stderr)
        return 1

    if not cidrs:
        print("错误:抓取结果为空,放弃写入(避免清空规则)", file=sys.stderr)
        return 1

    OUTPUT_FILE.write_text(render(cidrs), encoding="utf-8")
    print(f"成功:抓取到 {len(cidrs)} 个 Telegram IP 段 → {OUTPUT_FILE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
