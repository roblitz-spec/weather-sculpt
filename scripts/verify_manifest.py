"""校验数据完整性 — 逐文件复算两个 zarr 的目录级 SHA-256 指纹并比对 manifest.json。

买家开箱后跑一下即可确认数据未被篡改 / 完整:
    python scripts/verify_manifest.py
退出码 0 = 全部匹配, 1 = 有失配。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
MANIFEST = os.path.join(DATA, "manifest.json")


def dir_sha256(d: str) -> str:
    h = hashlib.sha256()
    files = []
    for root, _dirs, names in os.walk(d):
        for n in names:
            p = os.path.join(root, n)
            files.append(os.path.relpath(p, d))
    for rel in sorted(files):
        h.update(rel.encode())
        with open(os.path.join(d, rel), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


def main():
    if not os.path.exists(MANIFEST):
        print("manifest.json not found at", MANIFEST)
        return 1
    with open(MANIFEST) as f:
        m = json.load(f)

    ok = True
    for key in ("global_7d", "china_30d"):
        entry = m[key]
        path = os.path.join(DATA, entry["file"])
        if not os.path.exists(path):
            print(f"[MISSING] {entry['file']}")
            ok = False
            continue
        got = dir_sha256(path)
        match = got == entry["sha256"]
        ok = ok and match
        print(f"[{'OK ' if match else 'FAIL'}] {entry['file']}\n"
              f"       expected {entry['sha256'][:16]}…\n"
              f"       got      {got[:16]}…")

    print("\nVERIFY " + ("PASSED" if ok else "FAILED"))
    print(f"source: {m['source']['bucket']} ({m['source']['license']})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
