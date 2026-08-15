#!/usr/bin/env python3
"""
[RIGOR] Pre-Push Guard - تتلى قبل كل git push
================================================
تضمن هذه الأداة:
1. اختبارات الميزات القديمة (Existing Features Guard)
2. فحص الـ JS Syntax
3. فحص عدم وجود ملفات سرية في الـ commit
4. عرض إحصائيات التغييرات

الاستخدام:
    python pre_push.py
"""
import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd, cwd=ROOT):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def step(num, name):
    print(f"\n[{num}/4] {name}")
    print("-" * 50)

print("=" * 60)
print("  [RIGOR] PRE-PUSH GUARD")
print("=" * 60)

# [1/4] - JS Syntax Check
step("1", "JS Syntax Check")
rc, out, err = run(["node", "-e", "const fs=require('fs'); const code=fs.readFileSync('static/pos/pos.js','utf8'); new Function(code); console.log('OK')"])
if "OK" in out:
    print("  [PASS] pos.js syntax OK")
else:
    print(f"  [FAIL] JS Syntax Error: {err}")
    print("  [ABORT] Push cancelled!")
    sys.exit(1)

# [2/4] - Python Imports Check
step("2", "Python Import Check")
rc, out, err = run([sys.executable, "-c", "from database.db import get_db; from routes.store import store_bp; print('OK')"])
if "OK" in out:
    print("  [PASS] Python imports OK")
else:
    print(f"  [FAIL] Python import error: {err}")
    print("  [ABORT] Push cancelled!")
    sys.exit(1)

# [3/4] - Existing Features Tests
step("3", "Existing Features Tests (Guard)")
rc, out, err = run([sys.executable, "tests/test_existing_features.py"])
if rc == 0:
    print("  [PASS] All existing features OK")
else:
    print(f"  [FAIL] Some tests failed (rc={rc})")
    print("  [ABORT] Push cancelled!")
    sys.exit(1)

# [4/4] - Git Status Review
step("4", "Git Status Review")
rc, out, err = run(["git", "diff", "--stat", "--cached"])
print(out if out else "  (no staged changes)")
# Check for secrets
rc2, out2, err2 = run(["git", "diff", "--cached", "--name-only"])
sensitive = [".env", "cookie", "USER.md", "TOOLS.md", "*.db"]
for f in out2.split("\n"):
    for s in sensitive:
        if s in f and "*" not in s:
            print(f"  [ALERT] Sensitive file detected: {f}")
            print("  [ABORT] Push cancelled!")
            sys.exit(1)

print("\n" + "=" * 60)
print("  [RIGOR] All checks passed! Push safe!")
print("=" * 60)
print()
print("Continue with: git push origin main")
sys.exit(0)
