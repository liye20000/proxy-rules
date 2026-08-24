"""generate.py 的单元测试与端到端回归测试。

运行方式:

    pytest tests/

仅依赖标准库 + pytest。
"""

import json
import sys
from pathlib import Path

# 把仓库根目录加入 import 路径,使测试能 import generate
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import generate  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ---------- parse_domain_list ----------

def test_parse_normal_input_returns_correct_count():
    """解析正常输入 → 返回正确数量的域名。"""
    text = "a.com\nb.com\nc.com\n"
    assert generate.parse_domain_list(text) == ["a.com", "b.com", "c.com"]


def test_parse_skips_comment_lines():
    """解析含注释 → 注释行被忽略。"""
    text = "# 这是注释\na.com\n# 又一个注释\nb.com\n"
    assert generate.parse_domain_list(text) == ["a.com", "b.com"]


def test_parse_skips_blank_lines():
    """解析含空行 → 空行被忽略。"""
    text = "a.com\n\n\nb.com\n   \n"
    assert generate.parse_domain_list(text) == ["a.com", "b.com"]


def test_parse_strips_inline_comments():
    """解析含行内注释 → 行内注释被去除。"""
    text = "a.com   # 行内注释\nb.com# 紧贴的注释\n"
    assert generate.parse_domain_list(text) == ["a.com", "b.com"]


def test_parse_empty_file_returns_empty_list():
    """解析空文件 → 返回空列表。"""
    assert generate.parse_domain_list("") == []
    assert generate.parse_domain_list("# 只有注释\n\n") == []


def test_parse_deduplicates():
    """重复域名 → 自动去重(保持顺序)。"""
    text = "a.com\nb.com\na.com\nc.com\nb.com\n"
    assert generate.parse_domain_list(text) == ["a.com", "b.com", "c.com"]


def test_parse_case_insensitive_dedup():
    """大小写不同的同域名 → 视为相同(自动小写化)。"""
    text = "Example.com\nEXAMPLE.COM\nexample.com\n"
    assert generate.parse_domain_list(text) == ["example.com"]


def test_parse_exact_rules_normalizes_and_deduplicates():
    """exact: 主机规则会小写化、校验并独立去重。"""
    text = "exact:API.Example.com\nexact:api.example.com\nexample.com\n"
    assert generate.parse_domain_list(text) == ["exact:api.example.com", "example.com"]


def test_parse_skips_invalid_exact_rules():
    """exact: 后必须是合法主机名。"""
    text = "exact:\nexact:nodot\nexact:has space.example.com\nexact:ok.example.com\n"
    assert generate.parse_domain_list(text) == ["exact:ok.example.com"]


def test_parse_skips_invalid_domains():
    """非法域名(无点、含空格)→ 被跳过。"""
    text = "valid.com\nnodot\nhas space.com\nok.org\n"
    assert generate.parse_domain_list(text) == ["valid.com", "ok.org"]


# ---------- parse_ip_list ----------

def test_parse_ip_list_normal():
    """解析正常 CIDR(IPv4 / IPv6)→ 规范化输出。"""
    text = "91.108.4.0/22\n2001:67c:4e8::/48\n"
    assert generate.parse_ip_list(text) == ["91.108.4.0/22", "2001:67c:4e8::/48"]


def test_parse_ip_list_skips_comments_and_blanks():
    """跳过注释行、空行与行内注释。"""
    text = "# 注释\n\n10.0.0.0/8   # 行内注释\n"
    assert generate.parse_ip_list(text) == ["10.0.0.0/8"]


def test_parse_ip_list_normalizes_host_bits():
    """主机位被置位 → 规范化为网段写法。"""
    assert generate.parse_ip_list("1.2.3.4/24\n") == ["1.2.3.0/24"]


def test_parse_ip_list_skips_invalid():
    """非法 CIDR(非 IP、错误前缀)→ 被跳过。"""
    text = "1.2.3.0/24\nnotanip\n999.0.0.0/8\nok: \n"
    assert generate.parse_ip_list(text) == ["1.2.3.0/24"]


def test_parse_ip_list_dedup():
    """重复(含规范化后重复)→ 去重并保持顺序。"""
    text = "1.2.3.0/24\n1.2.3.4/24\n10.0.0.0/8\n"
    assert generate.parse_ip_list(text) == ["1.2.3.0/24", "10.0.0.0/8"]


# ---------- generate_v2rayn_rules ----------

def test_generate_produces_four_rules_in_order():
    """生成 JSON 结构 → 4 条规则,outboundTag 顺序正确。"""
    rules = generate.generate_v2rayn_rules(["a.com"])
    assert len(rules) == 4
    assert [r["outboundTag"] for r in rules] == ["proxy", "block", "direct", "direct"]
    # 兜底规则使用全端口
    assert rules[3]["port"] == "0-65535"


def test_generate_proxy_rule_contains_all_domains_with_prefix():
    """proxy 规则 → 包含所有输入域名并带 domain: 前缀。"""
    domains = ["a.com", "b.com", "c.com"]
    rules = generate.generate_v2rayn_rules(domains)
    assert rules[0]["outboundTag"] == "proxy"
    assert rules[0]["domain"] == ["domain:a.com", "domain:b.com", "domain:c.com"]


def test_generate_v2rayn_exact_rule_uses_full_prefix():
    """V2RayN 的 exact: 规则生成 full:,不会扩大到整个根域名。"""
    rules = generate.generate_v2rayn_rules(["example.com", "exact:api.vendor.com"])
    assert rules[0]["domain"] == ["domain:example.com", "full:api.vendor.com"]


def test_generate_block_and_direct_rules_have_geosite():
    """block / direct 规则包含预期的 geosite / geoip 条目。"""
    rules = generate.generate_v2rayn_rules(["a.com"])
    assert rules[1]["domain"] == ["geosite:category-ads-all"]
    assert rules[2]["domain"] == ["geosite:private", "geosite:cn"]
    assert rules[2]["ip"] == ["geoip:private", "geoip:cn"]


def test_generate_without_cidrs_keeps_four_rules():
    """不传 cidrs(或为空)→ 仍是原来的 4 条规则,索引不变。"""
    assert len(generate.generate_v2rayn_rules(["a.com"])) == 4
    assert len(generate.generate_v2rayn_rules(["a.com"], [])) == 4


def test_generate_with_cidrs_inserts_proxy_ip_rule_before_cn_direct():
    """传入 cidrs → 新增一条 proxy-IP 规则,排在 CN 直连之前。"""
    rules = generate.generate_v2rayn_rules(["a.com"], ["91.108.4.0/22", "2a0a:f280::/32"])
    assert [r["outboundTag"] for r in rules] == ["proxy", "proxy", "block", "direct", "direct"]
    # 第 2 条是 IP 代理规则:只含 ip、不含 domain
    assert rules[1]["ip"] == ["91.108.4.0/22", "2a0a:f280::/32"]
    assert rules[1]["domain"] == []
    # 必须排在 CN 直连(含 geoip:cn)之前
    cn_idx = next(i for i, r in enumerate(rules) if "geoip:cn" in r["ip"])
    assert 1 < cn_idx


# ---------- generate_shadowrocket_conf ----------

def test_shadowrocket_conf_has_general_and_rule_sections():
    """Shadowrocket 配置 → 含 [General] 与 [Rule] 段落,以及名称头。"""
    conf = generate.generate_shadowrocket_conf(["a.com"])
    assert "#!name=" in conf
    assert "[General]" in conf
    assert "[Rule]" in conf


def test_shadowrocket_conf_routes_each_domain_to_proxy():
    """每个白名单域名 → 生成一条 DOMAIN-SUFFIX,xxx,PROXY。"""
    conf = generate.generate_shadowrocket_conf(["a.com", "b.com"])
    assert "DOMAIN-SUFFIX,a.com,PROXY" in conf
    assert "DOMAIN-SUFFIX,b.com,PROXY" in conf


def test_shadowrocket_exact_rule_uses_domain_not_suffix():
    """Shadowrocket 的 exact: 规则只生成 DOMAIN 精确匹配。"""
    conf = generate.generate_shadowrocket_conf(["exact:api.vendor.com"])
    assert "DOMAIN,api.vendor.com,PROXY" in conf
    assert "DOMAIN-SUFFIX,api.vendor.com,PROXY" not in conf


def test_shadowrocket_conf_has_cn_direct_and_final_fallback():
    """含国内直连(GEOIP,CN,DIRECT)与兜底(FINAL,DIRECT),且 FINAL 在最后。"""
    conf = generate.generate_shadowrocket_conf(["a.com"])
    assert "GEOIP,CN,DIRECT" in conf
    assert "FINAL,DIRECT" in conf
    assert conf.strip().splitlines()[-1] == "FINAL,DIRECT"


def test_shadowrocket_conf_contains_no_node_info():
    """安全:配置中不得出现任何节点 / 代理服务器段落。"""
    conf = generate.generate_shadowrocket_conf(["a.com"])
    assert "[Proxy]" not in conf
    assert "[Proxy Group]" not in conf


# ---------- generate_shadowrocket_module(纯叠加) ----------

def test_shadowrocket_module_is_rule_only_overlay():
    """模块为叠加式:只含 [Rule],不含 [General](不改动底层通用设置)。"""
    mod = generate.generate_shadowrocket_module(["a.com"])
    assert "#!name=" in mod
    assert "[Rule]" in mod
    assert "[General]" not in mod
    assert "[Proxy]" not in mod


def test_shadowrocket_module_routes_domains_to_proxy():
    """模块把白名单域名指向 PROXY。"""
    mod = generate.generate_shadowrocket_module(["a.com", "b.com"])
    assert "DOMAIN-SUFFIX,a.com,PROXY" in mod
    assert "DOMAIN-SUFFIX,b.com,PROXY" in mod


def test_shadowrocket_module_is_strict_whitelist_with_final():
    """模块为严格白名单:含 CN 直连,并以 FINAL,DIRECT 收尾(主导全部路由)。"""
    mod = generate.generate_shadowrocket_module(["a.com"])
    assert "GEOIP,CN,DIRECT" in mod
    assert mod.strip().splitlines()[-1] == "FINAL,DIRECT"


def test_shadowrocket_conf_is_complete_whitelist_with_final():
    """替换式 conf 同为完整白名单:含 CN 直连与 FINAL,DIRECT 兜底。"""
    conf = generate.generate_shadowrocket_conf(["a.com"])
    assert "GEOIP,CN,DIRECT" in conf
    assert conf.strip().splitlines()[-1] == "FINAL,DIRECT"


def test_shadowrocket_conf_and_module_share_proxy_whitelist():
    """conf 与 module 的「白名单 → PROXY」主体一致(共用同一套生成逻辑)。"""
    domains = ["a.com", "b.com"]
    proxy_lines = generate._proxy_whitelist_lines(domains)
    conf = generate.generate_shadowrocket_conf(domains)
    mod = generate.generate_shadowrocket_module(domains)
    for line in proxy_lines:
        assert line in conf
        assert line in mod


# ---------- IP 段 → PROXY(conf 与 module 共用)----------

def test_proxy_ip_lines_empty_returns_empty():
    """cidrs 为空 → 不输出任何 IP 行。"""
    assert generate._proxy_ip_lines([]) == []


def test_proxy_ip_lines_uses_cidr6_for_ipv6_and_no_resolve():
    """IPv4 用 IP-CIDR、IPv6 用 IP-CIDR6,均带 no-resolve、指向 PROXY。"""
    lines = generate._proxy_ip_lines(["91.108.4.0/22", "2a0a:f280::/32"])
    assert "IP-CIDR,91.108.4.0/22,PROXY,no-resolve" in lines
    assert "IP-CIDR6,2a0a:f280::/32,PROXY,no-resolve" in lines


def test_shadowrocket_ip_rules_precede_cn_direct_and_final():
    """IP 段 PROXY 规则排在 GEOIP,CN,DIRECT 与 FINAL,DIRECT 之前。"""
    for text in (
        generate.generate_shadowrocket_conf(["a.com"], ["91.108.4.0/22"]),
        generate.generate_shadowrocket_module(["a.com"], ["91.108.4.0/22"]),
    ):
        lines = text.splitlines()
        ip_idx = lines.index("IP-CIDR,91.108.4.0/22,PROXY,no-resolve")
        cn_idx = lines.index("GEOIP,CN,DIRECT")
        assert ip_idx < cn_idx
        assert lines[-1] == "FINAL,DIRECT"


def test_shadowrocket_without_cidrs_has_no_proxy_ip_lines():
    """不传 cidrs → 不出现任何指向 PROXY 的 IP-CIDR 行。"""
    mod = generate.generate_shadowrocket_module(["a.com"])
    assert "PROXY,no-resolve" not in mod


# ---------- 端到端 ----------

def test_end_to_end_matches_expected_fixture():
    """端到端:读 fixtures/sample-input.txt → 输出与 expected-output.json 一致。"""
    sample = (FIXTURES / "sample-input.txt").read_text(encoding="utf-8")
    expected = json.loads((FIXTURES / "expected-output.json").read_text(encoding="utf-8"))

    domains = generate.parse_domain_list(sample)
    assert domains == ["example.com", "foo.com", "duplicate.com", "another.com"]

    rules = generate.generate_v2rayn_rules(domains)
    assert rules == expected


# ---------- 仓库白名单策略 ----------

def test_repository_covers_required_openai_and_google_ai_domains():
    """接管基线必须覆盖已核对的 OpenAI 与 Google AI 核心域名。"""
    rules = set(generate.parse_domain_list((ROOT / "proxy-list.txt").read_text(encoding="utf-8")))
    assert {
        "openai.com",
        "chatgpt.com",
        "oaistatsig.com",
        "exact:cdn.openaimerge.com",
        "exact:challenges.cloudflare.com",
        "exact:humb.apple.com",
        "ai.google",
        "exact:google.ai",
        "labs.google",
        "deepmind.google",
        "research.google",
        "flow.google",
        "jules.google",
        "opal.google",
        "antigravity.google",
        "codeassist.google",
        "quantumai.google",
        "google.dev",
        "flowmusic.app",
        "notebooklm.google",
    } <= rules


def test_repository_does_not_expand_large_shared_roots_or_optional_endpoints():
    """精确依赖不得扩成共享根域,可选客服/支付/遥测端点保持排除。"""
    rules = set(generate.parse_domain_list((ROOT / "proxy-list.txt").read_text(encoding="utf-8")))
    assert "apple.com" not in rules
    assert "cloudflare.com" not in rules
    assert not ({"intercom.io", "stripe.com", "sentry.io", "datadoghq.com", "workos.com"} & rules)
