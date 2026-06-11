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


def test_parse_skips_invalid_domains():
    """非法域名(无点、含空格)→ 被跳过。"""
    text = "valid.com\nnodot\nhas space.com\nok.org\n"
    assert generate.parse_domain_list(text) == ["valid.com", "ok.org"]


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


def test_generate_block_and_direct_rules_have_geosite():
    """block / direct 规则包含预期的 geosite / geoip 条目。"""
    rules = generate.generate_v2rayn_rules(["a.com"])
    assert rules[1]["domain"] == ["geosite:category-ads-all"]
    assert rules[2]["domain"] == ["geosite:private", "geosite:cn"]
    assert rules[2]["ip"] == ["geoip:private", "geoip:cn"]


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


# ---------- 端到端 ----------

def test_end_to_end_matches_expected_fixture():
    """端到端:读 fixtures/sample-input.txt → 输出与 expected-output.json 一致。"""
    sample = (FIXTURES / "sample-input.txt").read_text(encoding="utf-8")
    expected = json.loads((FIXTURES / "expected-output.json").read_text(encoding="utf-8"))

    domains = generate.parse_domain_list(sample)
    assert domains == ["example.com", "foo.com", "duplicate.com", "another.com"]

    rules = generate.generate_v2rayn_rules(domains)
    assert rules == expected
