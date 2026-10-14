from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
xml_path = OUT / "API_TEST_RESULTS.xml"
report_path = OUT / "API_TEST_REPORT.md"
csv_path = OUT / "API_TEST_CASES.csv"

print("=" * 72)
print("PHASE 19 — COMPLETE FASTAPI API TEST SUITE")
print("Testing every OpenAPI endpoint + valid/invalid/boundary/error cases")
print("No manual endpoint testing required")
print("=" * 72)

cmd = [sys.executable, "-m", "pytest", "tests", "-vv", "-ra", "--tb=short", f"--junitxml={xml_path}"]
env = os.environ.copy()
env.setdefault("MAIZE_PROJECT_ROOT", str(BASE.parent))
result = subprocess.run(cmd, cwd=BASE, env=env, text=True)

if xml_path.exists():
    root = ET.parse(xml_path).getroot()
    cases = []
    for tc in root.iter("testcase"):
        node = next(iter(tc), None)
        if node is None:
            status = "PASS"
        elif node.tag == "skipped":
            status = "SKIPPED"
        elif node.tag in {"failure", "error"}:
            status = "FAIL"
        else:
            status = "PASS"
        cases.append({
            "test": f"{tc.attrib.get('classname', '')}::{tc.attrib.get('name', '')}".lstrip(":") ,
            "status": status,
            "duration_seconds": tc.attrib.get("time", "0"),
        })
    import csv
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["test", "status", "duration_seconds"])
        w.writeheader(); w.writerows(cases)

    counts = {s: sum(1 for c in cases if c["status"] == s) for s in ["PASS", "FAIL", "SKIPPED"]}
    print("\n" + "=" * 72)
    print("TEST CASE RESULT SUMMARY")
    print("=" * 72)
    for c in cases:
        print(f"[{c['status']:<7}] {c['test']}")
    print("-" * 72)
    print(f"PASS={counts['PASS']}  FAIL={counts['FAIL']}  SKIPPED={counts['SKIPPED']}")
    print("=" * 72)

    report_path.write_text(
        "# Phase 19 API Test Report\n\n"
        f"PASS: {counts['PASS']}\n\nFAIL: {counts['FAIL']}\n\nSKIPPED: {counts['SKIPPED']}\n\n"
        "Every OpenAPI route is protected by `test_61_every_openapi_route_has_explicit_coverage`.\n",
        encoding="utf-8",
    )

print(f"JUnit results: {xml_path}")
print(f"Case results : {csv_path}")
print(f"Report       : {report_path}")
if result.returncode == 0:
    print("ALL API TESTS PASSED")
else:
    print(f"API TEST SUITE FAILED (pytest exit code {result.returncode})")
raise SystemExit(result.returncode)
