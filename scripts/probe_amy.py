#!/usr/bin/env python3
"""Probe the real AMY (TulipCC) python module for offline rendering."""
import amy

print("module file:", amy.__file__)
print("public names:", [n for n in dir(amy) if not n.startswith("_")][:60])
for n in ("render_to_list", "start", "stop", "config", "live"):
    print(f"  has {n}:", hasattr(amy, n))
if hasattr(amy, "config"):
    try:
        print("config:", amy.config())
    except Exception as e:
        print("config err:", e)
