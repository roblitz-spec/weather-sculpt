"""打包付费 zip (Gumroad) — weather-sculpt-full-0.1.0.zip

内容: 完整数据 (全球 7d + 中国 30d, 5 变量) + manifest + 代码 + 预设 + examples
      + demo 展示 + LICENSE_COMMERCIAL + QUICKSTART + 文档。

优化: zarr 分块已是 zstd 压缩 → 用 ZIP_STORED 直存 (不重复压缩, 省 CPU/时间),
      其余小文件 (代码/文本/图片) 用 ZIP_DEFLATED。

    python scripts/build_paid_zip.py
"""
from __future__ import annotations

import os
import sys
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(BASE, "dist")
OUT = os.path.join(DIST, "weather-sculpt-full-0.1.0.zip")
ROOT_NAME = "weather-sculpt-full"

# 整目录跳过
SKIP_DIRS = {".git", "dist", "web", "weather_sculpt.egg-info", "__pycache__", "node_modules"}
# 具体文件跳过 (相对 BASE 的路径)
SKIP_FILES = {
    "GUMROAD_PUBLISH_GUIDE.md",
    ".gitignore",
    os.path.join("data", "progress.json"),
    os.path.join("data", "download.log"),
    os.path.join("data", "chunk_sample.bin"),
}


def is_zarr(rel: str) -> bool:
    return ".zarr" in rel.split(os.sep)


def main():
    os.makedirs(DIST, exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)

    n_files = 0
    n_stored = 0
    n_deflated = 0
    with zipfile.ZipFile(OUT, "w", allowZip64=True) as z:
        for root, dirs, files in os.walk(BASE):
            rel_root = os.path.relpath(root, BASE)
            # 就地剪枝
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != "__pycache__"]
            for name in files:
                if name.endswith(".pyc"):
                    continue
                rel = os.path.relpath(os.path.join(root, name), BASE)
                if rel in SKIP_FILES:
                    continue
                arcname = os.path.join(ROOT_NAME, rel)
                full = os.path.join(root, name)
                if is_zarr(rel):
                    z.write(full, arcname, compress_type=zipfile.ZIP_STORED)
                    n_stored += 1
                else:
                    z.write(full, arcname, compress_type=zipfile.ZIP_DEFLATED)
                    n_deflated += 1
                n_files += 1
                if n_files % 500 == 0:
                    print(f"  ...{n_files} files", flush=True)

    size = os.path.getsize(OUT)
    print(f"\nwrote {OUT}")
    print(f"  files: {n_files}  (stored={n_stored}, deflated={n_deflated})")
    print(f"  size : {size/1e9:.3f} GB ({size/1e6:.1f} MB)")
    if size > 2 * 1024**3:
        print("  ⚠️  OVER 2GB — Gumroad 单文件上限, 需拆包")
    else:
        print(f"  OK: under 2GB limit (headroom {(2*1024**3 - size)/1e9:.3f} GB)")


if __name__ == "__main__":
    main()
