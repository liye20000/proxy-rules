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
OUTPUT_FILE = BASE_DIR / "v2rayn-rules.json"            # 派生:V2RayN(Xray-core)规则
OUTPUT_SR_CONF = BASE_DIR / "shadowrocket.conf"         # 派生:Shadowrocket 完整配置(替换式,仅规则)
OUTPUT_SR_MODULE = BASE_DIR / "shadowrocket.module"     # 派生:Shadowrocket 模块(叠加式,推荐)

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


def _proxy_whitelist_lines(domains: list[str]) -> list[str]:
    """构造「白名单域名 → PROXY」的规则行(被 conf 与 module 共用)。

    每个域名一条 ``DOMAIN-SUFFIX,xxx,PROXY``。``PROXY`` 是 Shadowrocket 的特殊策略,
    表示「走当前选中的节点」。
    """
    lines = ["# ===== 代理白名单(PROXY = 你在首页选中的节点)====="]
    lines += [f"DOMAIN-SUFFIX,{d},PROXY" for d in domains]
    return lines


def _shadowrocket_full_rule_lines(domains: list[str]) -> list[str]:
    """构造一套**完整的**白名单路由 ``[Rule]`` 内容(用于替换式 .conf)。

    = 白名单 PROXY + 局域网/国内 DIRECT + ``FINAL,DIRECT`` 兜底。
    规则自上而下匹配、首条命中即生效,白名单在最前、兜底在最后。
    """
    lines = list(_proxy_whitelist_lines(domains))
    lines += [
        "# ===== 局域网与国内直连 =====",
        "IP-CIDR,192.168.0.0/16,DIRECT",
        "IP-CIDR,10.0.0.0/8,DIRECT",
        "IP-CIDR,172.16.0.0/12,DIRECT",
        "GEOIP,CN,DIRECT",
        "# ===== 兜底:其余全部直连(严格白名单)=====",
        "FINAL,DIRECT",
    ]
    return lines


def generate_shadowrocket_conf(domains: list[str]) -> str:
    """生成 Shadowrocket 完整配置(``[General]`` + ``[Rule]``,不含任何节点)。

    用于「替换整份配置」的场景——仅当用户的节点来自独立的「服务器订阅」、
    而非机场给的整份配置时使用。它是一套**完整**白名单路由(含 ``FINAL,DIRECT`` 兜底)。
    配置中**不含**任何节点 / 密码 / 机场信息;``PROXY`` 指向用户在首页选中的节点。

    :param domains: 已清洗的域名列表
    :return: 完整的 .conf 文本(以换行符结尾)
    """
    lines: list[str] = [
        "#!name=proxy-rules 白名单分流(完整配置)",
        "#!desc=完整白名单路由:只把白名单域名走代理,其余直连;不含任何节点信息。",
        "",
        "[General]",
        "bypass-system = true",
        "skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local",
        "dns-server = system",
        "",
        "[Rule]",
    ]
    lines += _shadowrocket_full_rule_lines(domains)
    return "\n".join(lines) + "\n"


def generate_shadowrocket_module(domains: list[str]) -> str:
    """生成 Shadowrocket 模块(仅 ``[Rule]``,**严格白名单,主导全部路由**,不含任何节点)。

    **推荐方式**:模块会**叠加**在用户当前生效的配置(通常是机场给的整份配置)之上,
    优先级高于配置中的规则,但**只覆盖路由、不动节点**——节点原样保留在机场配置里。

    本模块是一套**完整**白名单路由:白名单 → PROXY、局域网/国内 → DIRECT、其余
    ``FINAL,DIRECT``。由于模块优先级高于配置,这套规则会**主导全部路由**:
    白名单域名走代理,其余一切直连;用户机场配置里原有的路由规则(如 apple-relay /
    copilot 走代理)将被**覆盖**(若仍想代理,把对应域名加进 proxy-list.txt 即可)。

    本文件同样不含任何节点 / 密码 / 机场信息;``PROXY`` 指向用户在首页选中的节点。

    :param domains: 已清洗的域名列表
    :return: 完整的 .module 文本(以换行符结尾)
    """
    lines: list[str] = [
        "#!name=proxy-rules 白名单分流",
        "#!desc=严格白名单:只把白名单域名走代理、其余全部直连;叠加在你的配置之上、主导全部路由,但不动节点。",
        "",
        "[Rule]",
    ]
    lines += _shadowrocket_full_rule_lines(domains)
    return "\n".join(lines) + "\n"


def main() -> int:
    """主入口。读取主源、生成规则、写出派生文件。

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

    # 1) V2RayN JSON:2 空格缩进,允许 UTF-8 字符,文件末尾保留一个换行符
    rules = generate_v2rayn_rules(domains)
    OUTPUT_FILE.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 2) Shadowrocket 模块(推荐:叠加式,不动节点)与完整配置(替换式备选),均不含节点
    OUTPUT_SR_MODULE.write_text(generate_shadowrocket_module(domains), encoding="utf-8")
    OUTPUT_SR_CONF.write_text(generate_shadowrocket_conf(domains), encoding="utf-8")

    print(
        f"成功:从 {len(domains)} 个域名生成 "
        f"{OUTPUT_FILE.name}(共 {len(rules)} 条规则)、"
        f"{OUTPUT_SR_MODULE.name} 与 {OUTPUT_SR_CONF.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
