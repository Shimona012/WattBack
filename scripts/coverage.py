"""Which states have rates, how confident, and where to look for the rest.   python scripts/coverage.py"""
import sys; sys.path.insert(0, ".")
from app.tariffs import STATES, TARIFFS
for code, (name, *_, reg) in sorted(STATES.items(), key=lambda x: x[1][0]):
    t = TARIFFS.get(code)
    print(f"{code}  {name:38} {(t.get('status') if t else 'ESTIMATE ONLY'):16} {reg}")
print(f"\n{len(TARIFFS)} of {len(STATES)} states/UTs have a record.")
