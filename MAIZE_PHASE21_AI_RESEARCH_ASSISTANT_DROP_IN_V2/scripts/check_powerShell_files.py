from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
files = list(ROOT.glob('*.ps1'))
failures = []
for p in files:
    data = p.read_bytes()
    if any(b >= 128 for b in data):
        failures.append(f"NON_ASCII:{p.name}")
    text = data.decode('ascii', errors='strict')
    # Simple structural sanity checks for runner scripts.
    if p.name.startswith('RUN_'):
        if text.count('{') != text.count('}'):
            failures.append(f"BRACE_MISMATCH:{p.name}")
        if text.count('(') != text.count(')'):
            failures.append(f"PAREN_MISMATCH:{p.name}")
        if text.count("'") % 2 != 0:
            failures.append(f"SINGLE_QUOTE_ODD:{p.name}")
        if text.count('"') % 2 != 0:
            failures.append(f"DOUBLE_QUOTE_ODD:{p.name}")
if failures:
    for x in failures:
        print('[FAIL]', x)
    raise SystemExit(1)
print(f'[PASS] PowerShell ASCII/structure check: {len(files)} files')
