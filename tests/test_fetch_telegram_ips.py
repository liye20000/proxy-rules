"""fetch_telegram_ips.py 的单元测试(纯解析/渲染逻辑,不联网)。

运行方式:

    pytest tests/

仅依赖标准库 + pytest。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fetch_telegram_ips as f  # noqa: E402


# ---------- parse_ripestat_prefixes ----------

def test_parse_ripestat_prefixes_extracts_prefix_field():
    """从 RIPEstat 响应结构里提取 prefix 列表。"""
    payload = {
        "data": {
            "prefixes": [
                {"prefix": "91.108.4.0/22", "timelines": []},
                {"prefix": "2001:67c:4e8::/48", "timelines": []},
            ]
        }
    }
    assert f.parse_ripestat_prefixes(payload) == ["91.108.4.0/22", "2001:67c:4e8::/48"]


def test_parse_ripestat_prefixes_empty():
    """无前缀 → 返回空列表。"""
    assert f.parse_ripestat_prefixes({"data": {"prefixes": []}}) == []


# ---------- render ----------

def test_render_splits_v4_v6_and_sorts():
    """渲染:IPv4 / IPv6 分组并各自排序,输出稳定。"""
    out = f.render(["91.108.8.0/22", "2a0a:f280::/32", "91.108.4.0/22", "2001:67c:4e8::/48"])
    lines = [l for l in out.splitlines() if l and not l.startswith("#")]
    assert lines == [
        "91.108.4.0/22",
        "91.108.8.0/22",
        "2001:67c:4e8::/48",
        "2a0a:f280::/32",
    ]


def test_render_has_do_not_edit_header():
    """输出含「切勿手动编辑」提示头。"""
    out = f.render(["91.108.4.0/22"])
    assert out.startswith("#")
    assert "切勿手动编辑" in out


def test_render_output_is_deterministic():
    """同一组输入(顺序不同)→ 渲染结果一致(便于「有变化才提交」)。"""
    a = f.render(["91.108.8.0/22", "91.108.4.0/22"])
    b = f.render(["91.108.4.0/22", "91.108.8.0/22"])
    assert a == b


def test_constants_cover_known_telegram_asns():
    """ASN 列表包含已知的 Telegram 主 ASN。"""
    assert 62041 in f.TELEGRAM_ASNS
    assert set(f.TELEGRAM_ASNS) >= {62041, 62014, 59930, 44907, 211157}
