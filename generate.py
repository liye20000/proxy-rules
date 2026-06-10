#!/usr/bin/env python3
"""代理规则转换脚本。

读取主源文件 proxy-list.txt(纯文本,每行一个域名),
生成 V2RayN(Xray-core)格式的路由规则文件 v2rayn-rules.json。

只使用 Python 标准库,可独立运行:

    python generate.py

退出码:成功 0,失败 1。
"""

import json
import re
import sys
from pathlib import Path

# 主源文件与派生文件的路径(相对脚本所在目录,避免硬编码绝对路径)
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "proxy-list.txt"
OUTPUT_FILE = BASE_DIR / "v2rayn-rules.json"

# 域名基本格式校验:由字母/数字/连字符组成的标签,用点分隔,至少含一个点。
DOMAIN_PATTERN = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")


def parse_domain_list(text: str) -> list[str]:
    """解析文本,返回干净的域名列表。

    - 跳过空行和注释行(以 # 开头)
    - 处理行内注释(# 之后的内容)
    - 自动小写化
    - 自动去重(保持首次出现的顺序)
    - 校验:基本域名格式(包含点,不含空格/特殊字符);非法行打印警告并跳过

    :param text: proxy-list.txt 的完整文本内容
    :return: 去重后的小写域名列表
    """
    domains: list[str] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        # 去掉行内注释:取第一个 # 之前的部分
        line = raw_line.split("#", 1)[0].strip().lower()
        if not line:
            continue

        if not DOMAIN_PATTERN.match(line):
            # 非法域名格式:警告到 stderr,但不中断整体处理
            print(f"警告:跳过非法域名行:{raw_line!r}", file=sys.stderr)
            continue

        if line in seen:
            continue

        seen.add(line)
        domains.append(line)

    return domains


def generate_v2rayn_rules(domains: list[str]) -> list[dict]:
    """根据域名列表生成 V2RayN 路由规则数组。

    生成 4 条规则,顺序固定:

    1. 代理白名单(每个域名加 ``domain:`` 前缀)
    2. 拦截广告(``geosite:category-ads-all``)
    3. 直连 CN + 局域网(``geosite:private`` / ``geosite:cn`` 与 ``geoip:private`` / ``geoip:cn``)
    4. 兜底 direct(``port: 0-65535``,全部直连)

    :param domains: 已清洗的域名列表
    :return: 规则字典数组,可直接序列化为 JSON
    """
    proxy_domains = [f"domain:{d}" for d in domains]

    return [
        {
            "outboundTag": "proxy",
            "port": "",
            "protocol": [],
            "inboundTag": [],
            "domain": proxy_domains,
            "ip": [],
            "enabled": True,
        },
        {
            "outboundTag": "block",
            "port": "",
            "protocol": [],
            "inboundTag": [],
            "domain": ["geosite:category-ads-all"],
            "ip": [],
            "enabled": True,
        },
        {
            "outboundTag": "direct",
            "port": "",
            "protocol": [],
            "inboundTag": [],
            "domain": ["geosite:private", "geosite:cn"],
            "ip": ["geoip:private", "geoip:cn"],
            "enabled": True,
        },
        {
            "outboundTag": "direct",
            "port": "0-65535",
            "protocol": [],
            "inboundTag": [],
            "domain": [],
            "ip": [],
            "enabled": True,
        },
    ]


def main() -> int:
    """主入口。读取主源、生成规则、写出 JSON。

    :return: 成功返回 0,失败返回 1
    """
    if not INPUT_FILE.exists():
        print(f"错误:找不到主源文件 {INPUT_FILE.name}", file=sys.stderr)
        return 1

    text = INPUT_FILE.read_text(encoding="utf-8")
    domains = parse_domain_list(text)

    if not domains:
        print("错误:解析后没有任何有效域名,请检查 proxy-list.txt", file=sys.stderr)
        return 1

    rules = generate_v2rayn_rules(domains)

    # JSON 输出:2 空格缩进,允许 UTF-8 字符,文件末尾保留一个换行符
    OUTPUT_FILE.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"成功:从 {len(domains)} 个域名生成 {OUTPUT_FILE.name}(共 {len(rules)} 条规则)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
