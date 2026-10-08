"""FinAgentRank · 步骤4 演示：接入标准 / Conformance 校验。

运行：cd FinAgentRank && python src/finagentrank/run_step4.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finagentrank.conformance import (
    conformance_check, check_declared_vs_measured, validate_manifest,
)


def good_transport(endpoint: str, _payload: dict) -> tuple[int, dict]:
    # 模拟一个健康的金融 Agent：握手 200，声明擅长 Factor
    return 200, {"capabilities": ["Factor", "Data"], "name": "AlphaFactor-Quant"}


def main() -> None:
    # 1) 合规 manifest（通过）
    good = {
        "name": "AlphaFactor-Quant", "name_for_model": "alpha_factor",
        "endpoint": "https://alpha.example.com", "auth": "bearer",
        "capabilities": ["Factor", "Data"], "output_type": "factor",
        "egress_hosts": ["yfinance", "edgar"], "schema_version": "0.1",
    }
    r1 = conformance_check(good, good_transport)
    print("===== 1) 合规 manifest → 通过 =====")
    print(f"  passed={r1['passed']} errors={r1['errors']} 握手={r1['handshake']['status']}")

    # 2) 缺字段 + 非法输出类型 + 握手超时 → 拦截 + 修复建议
    bad = {
        "name": "ShadyAgent",
        "endpoint": "ftp://bad.example.com",   # 非 http(s)
        "auth": "bearer",
        "capabilities": ["Factor", "Hack"],   # 非法族
        "output_type": "advisory",            # 非法输出类型（投顾类，超出边界）
        # 缺 egress_hosts / name_for_model / schema_version
    }
    r2 = conformance_check(bad, lambda e, p: (500, {}))
    print("\n===== 2) 缺陷 manifest → 拦截 + 修复建议 =====")
    print(f"  passed={r2['passed']}")
    print(f"  errors={r2['errors']}")
    print(f"  suggestions={r2['suggestions']}")

    # 3) manifest 通过但握手失败 → 拦截
    ok_manifest_but_no_hs = dict(good, endpoint="https://down.example.com")
    r3 = conformance_check(ok_manifest_but_no_hs, lambda e, p: (504, {}))
    print("\n===== 3) manifest 合规但握手超时 → 拦截 =====")
    print(f"  passed={r3['passed']} 握手note={r3['handshake']['note']}")

    # 4) 声明 vs 实测自动分类对照（§9.1 枢纽）
    print("\n===== 4) 声明 vs 实测自动分类 =====")
    print(f"  声明[Factor] vs 实测Risk → {check_declared_vs_measured(['Factor'], 'Risk')}")
    print(f"  声明[Factor] vs 实测Factor → {check_declared_vs_measured(['Factor'], 'Factor') or '一致(以实测为准)'}")


if __name__ == "__main__":
    main()
