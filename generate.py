#!/usr/bin/env python3
"""代理规则转换脚本。

读取主源文件 proxy-list.txt(纯文本,每行一个域名或 exact:精确主机),
生成 V2RayN(Xray-core)格式的路由规则文件 v2rayn-rules.json。

只使用 Python 标准库,可独立运行:

    python generate.py

退出码:成功 0,失败 1。
"""

import ipaddress
import json
import re
import sys
from pathlib import Path

# 主源文件与派生文件的路径(相对脚本所在目录,避免硬编码绝对路径)
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "proxy-list.txt"
INPUT_IP_FILE = BASE_DIR / "proxy-ip-list.txt"         # 主源:按 IP 段走代理(手动维护)
INPUT_IP_AUTO_FILE = BASE_DIR / "proxy-ip-auto.txt"    # 主源:自动抓取的 IP 段(fetch_telegram_ips.py)
OUTPUT_FILE = BASE_DIR / "v2rayn-rules.json"            # 派生:V2RayN(Xray-core)规则
OUTPUT_SR_CONF = BASE_DIR / "shadowrocket.conf"         # 派生:Shadowrocket 完整配置(替换式,仅规则)
OUTPUT_SR_MODULE = BASE_DIR / "shadowrocket.module"     # 派生:Shadowrocket 模块(叠加式,推荐)

# 域名基本格式校验:由字母/数字/连字符组成的标签,用点分隔,至少含一个点。
DOMAIN_PATTERN = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")


def parse_domain_list(text: str) -> list[str]:
    """解析文本,返回干净的域名规则列表。

    - 跳过空行和注释行(以 # 开头)
    - 处理行内注释(# 之后的内容)
    - 自动小写化
    - 自动去重(保持首次出现的顺序)
    - 普通域名匹配自身与所有子域名;``exact:host.example.com`` 只匹配该主机
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

        prefix = "exact:" if line.startswith("exact:") else ""
        host = line.removeprefix(prefix)

        if not DOMAIN_PATTERN.match(host):
            # 非法域名格式:警告到 stderr,但不中断整体处理
            print(f"警告:跳过非法域名行:{raw_line!r}", file=sys.stderr)
            continue

        if line in seen:
            continue

        seen.add(line)
        domains.append(line)

    return domains


def _domain_rule_parts(rule: str) -> tuple[bool, str]:
    """把已清洗规则拆为 ``(是否精确匹配, 主机名)``。"""
    if rule.startswith("exact:"):
        return True, rule.removeprefix("exact:")
    return False, rule


def parse_ip_list(text: str) -> list[str]:
    """解析文本,返回干净的 CIDR 列表(IPv4 / IPv6)。

    - 跳过空行和注释行(以 # 开头)
    - 处理行内注释(# 之后的内容)
    - 用标准库 ``ipaddress`` 校验并规范化为网段写法;非法行打印警告并跳过
    - 自动去重(保持首次出现的顺序)

    :param text: proxy-ip-list.txt 的完整文本内容
    :return: 去重后的规范化 CIDR 列表
    """
    cidrs: list[str] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        try:
            # strict=False 容忍主机位被置位,统一规范化为网段写法(如 1.2.3.4/24 → 1.2.3.0/24)
            network = ipaddress.ip_network(line, strict=False)
        except ValueError:
            print(f"警告:跳过非法 CIDR 行:{raw_line!r}", file=sys.stderr)
            continue

        normalized = network.with_prefixlen
        if normalized in seen:
            continue

        seen.add(normalized)
        cidrs.append(normalized)

    return cidrs


def generate_v2rayn_rules(domains: list[str], cidrs: list[str] | None = None) -> list[dict]:
    """根据域名列表生成 V2RayN 路由规则数组。

    生成的规则顺序固定:

    1. 代理白名单域名(每个域名加 ``domain:`` 前缀)
    2. 代理白名单 IP 段(``cidrs`` 非空时才生成;按 IP 走代理,如 Telegram)
    3. 拦截广告(``geosite:category-ads-all``)
    4. 直连 CN + 局域网(``geosite:private`` / ``geosite:cn`` 与 ``geoip:private`` / ``geoip:cn``)
    5. 兜底 direct(``port: 0-65535``,全部直连)

    代理 IP 规则排在「CN 直连」之前:Telegram 等数据中心 IP 不属于 CN,
    若无此规则会落到兜底而被直连。

    :param domains: 已清洗的域名列表
    :param cidrs: 已清洗的 CIDR 列表(可为 None / 空,此时不生成 IP 代理规则)
    :return: 规则字典数组,可直接序列化为 JSON
    """
    proxy_domains = [
        f"full:{host}" if is_exact else f"domain:{host}"
        for is_exact, host in map(_domain_rule_parts, domains)
    ]
    cidrs = cidrs or []

    rules: list[dict] = [
        {
            "outboundTag": "proxy",
            "port": "",
            "protocol": [],
            "inboundTag": [],
            "domain": proxy_domains,
            "ip": [],
            "enabled": True,
        },
    ]

    if cidrs:
        rules.append(
            {
                "outboundTag": "proxy",
                "port": "",
                "protocol": [],
                "inboundTag": [],
                "domain": [],
                "ip": list(cidrs),
                "enabled": True,
            }
        )

    rules += [
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

    return rules


def _proxy_whitelist_lines(domains: list[str]) -> list[str]:
    """构造「白名单域名 → PROXY」的规则行(被 conf 与 module 共用)。

    普通域名生成 ``DOMAIN-SUFFIX,xxx,PROXY``;``exact:`` 规则生成
    ``DOMAIN,host,PROXY``。``PROXY`` 表示「走当前选中的节点」。
    """
    lines = ["# ===== 代理白名单(PROXY = 你在首页选中的节点)====="]
    for rule in domains:
        is_exact, host = _domain_rule_parts(rule)
        keyword = "DOMAIN" if is_exact else "DOMAIN-SUFFIX"
        lines.append(f"{keyword},{host},PROXY")
    return lines


def _proxy_ip_lines(cidrs: list[str]) -> list[str]:
    """构造「白名单 IP 段 → PROXY」的规则行(被 conf 与 module 共用)。

    IPv4 用 ``IP-CIDR``、IPv6 用 ``IP-CIDR6``;均带 ``no-resolve``,避免对 IP
    规则触发 DNS 解析。``cidrs`` 为空时返回空列表(不输出该段)。
    """
    if not cidrs:
        return []
    lines = ["# ===== 代理白名单 IP 段(如 Telegram,no-resolve 避免解析)====="]
    for cidr in cidrs:
        keyword = "IP-CIDR6" if ":" in cidr else "IP-CIDR"
        lines.append(f"{keyword},{cidr},PROXY,no-resolve")
    return lines


def _shadowrocket_full_rule_lines(domains: list[str], cidrs: list[str] | None = None) -> list[str]:
    """构造一套**完整的**白名单路由 ``[Rule]`` 内容(用于替换式 .conf)。

    = 白名单域名 PROXY + 白名单 IP 段 PROXY + 局域网/国内 DIRECT + ``FINAL,DIRECT`` 兜底。
    规则自上而下匹配、首条命中即生效;IP 段排在国内直连之前,白名单在最前、兜底在最后。
    """
    lines = list(_proxy_whitelist_lines(domains))
    lines += _proxy_ip_lines(cidrs or [])
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


def generate_shadowrocket_conf(domains: list[str], cidrs: list[str] | None = None) -> str:
    """生成 Shadowrocket 完整配置(``[General]`` + ``[Rule]``,不含任何节点)。

    用于「替换整份配置」的场景——仅当用户的节点来自独立的「服务器订阅」、
    而非机场给的整份配置时使用。它是一套**完整**白名单路由(含 ``FINAL,DIRECT`` 兜底)。
    配置中**不含**任何节点 / 密码 / 机场信息;``PROXY`` 指向用户在首页选中的节点。

    :param domains: 已清洗的域名列表
    :param cidrs: 已清洗的 CIDR 列表(可为 None / 空,此时不生成 IP 代理规则)
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
    lines += _shadowrocket_full_rule_lines(domains, cidrs)
    return "\n".join(lines) + "\n"


def generate_shadowrocket_module(domains: list[str], cidrs: list[str] | None = None) -> str:
    """生成 Shadowrocket 模块(仅 ``[Rule]``,**严格白名单,主导全部路由**,不含任何节点)。

    **推荐方式**:模块会**叠加**在用户当前生效的配置(通常是机场给的整份配置)之上,
    优先级高于配置中的规则,但**只覆盖路由、不动节点**——节点原样保留在机场配置里。

    本模块是一套**完整**白名单路由:白名单 → PROXY、局域网/国内 → DIRECT、其余
    ``FINAL,DIRECT``。由于模块优先级高于配置,这套规则会**主导全部路由**:
    白名单域名走代理,其余一切直连;用户机场配置里原有的路由规则(如 apple-relay /
    copilot 走代理)将被**覆盖**(若仍想代理,把对应域名加进 proxy-list.txt 即可)。

    本文件同样不含任何节点 / 密码 / 机场信息;``PROXY`` 指向用户在首页选中的节点。

    :param domains: 已清洗的域名列表
    :param cidrs: 已清洗的 CIDR 列表(可为 None / 空,此时不生成 IP 代理规则)
    :return: 完整的 .module 文本(以换行符结尾)
    """
    lines: list[str] = [
        "#!name=proxy-rules 白名单分流",
        "#!desc=严格白名单:只把白名单域名走代理、其余全部直连;叠加在你的配置之上、主导全部路由,但不动节点。",
        "",
        "[Rule]",
    ]
    lines += _shadowrocket_full_rule_lines(domains, cidrs)
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

    # IP 段主源均为可选:合并「手动」(proxy-ip-list.txt)与「自动抓取」
    # (proxy-ip-auto.txt)两份,parse_ip_list 会统一规范化并去重。文件缺失按空处理。
    ip_text = ""
    for ip_file in (INPUT_IP_FILE, INPUT_IP_AUTO_FILE):
        if ip_file.exists():
            ip_text += ip_file.read_text(encoding="utf-8") + "\n"
    cidrs = parse_ip_list(ip_text)

    # 1) V2RayN JSON:2 空格缩进,允许 UTF-8 字符,文件末尾保留一个换行符
    rules = generate_v2rayn_rules(domains, cidrs)
    OUTPUT_FILE.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 2) Shadowrocket 模块(推荐:叠加式,不动节点)与完整配置(替换式备选),均不含节点
    OUTPUT_SR_MODULE.write_text(generate_shadowrocket_module(domains, cidrs), encoding="utf-8")
    OUTPUT_SR_CONF.write_text(generate_shadowrocket_conf(domains, cidrs), encoding="utf-8")

    print(
        f"成功:从 {len(domains)} 个域名 + {len(cidrs)} 个 IP 段生成 "
        f"{OUTPUT_FILE.name}(共 {len(rules)} 条规则)、"
        f"{OUTPUT_SR_MODULE.name} 与 {OUTPUT_SR_CONF.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
