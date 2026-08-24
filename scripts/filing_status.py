#!/usr/bin/env python3
"""Filing system status checker.

Scans the business filing folders and reports:
  - what is waiting in LPT/under-review (pending Zerric's approval)
  - what is approved and filed in each LPT subfolder
  - Z-Dot folder contents
  - violations (e.g. [DRAFT] files outside under-review)

Usage: python scripts/filing_status.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Z_DOT_DIRS = ["clients", "marketing", "landing-pages", "proposals", "resources", "archive"]
LPT_DIRS = ["marketing", "landing-pages", "property-management", "resources", "archive"]
UNDER_REVIEW = os.path.join(ROOT, "LPT", "under-review")


def list_files(path):
    out = []
    for dirpath, _dirnames, filenames in os.walk(path):
        for f in filenames:
            if f == "README.md":
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
            out.append(rel)
    return sorted(out)


def main():
    print("Filing system status")
    print("=" * 40)

    pending = list_files(UNDER_REVIEW)
    print(f"\nLPT/under-review (WAITING on Zerric): {len(pending)}")
    for f in pending:
        print(f"  [PENDING] {f}")
    if not pending:
        print("  (nothing pending - all clear)")

    for d in LPT_DIRS:
        files = list_files(os.path.join(ROOT, "LPT", d))
        print(f"\nLPT/{d} (approved/filed): {len(files)}")
        for f in files[:10]:
            print(f"  {f}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")

    for d in Z_DOT_DIRS:
        files = list_files(os.path.join(ROOT, d))
        print(f"\n{d}/ (Z-Dot): {len(files)} file(s)")

    violations = []
    for d in LPT_DIRS:
        for f in list_files(os.path.join(ROOT, "LPT", d)):
            if "[DRAFT]" in os.path.basename(f):
                violations.append(f)
    print("\nViolations:")
    if violations:
        for f in violations:
            print(f"  [DRAFT] file outside under-review: {f}")
    else:
        print("  none - all drafts are correctly in under-review")

    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
