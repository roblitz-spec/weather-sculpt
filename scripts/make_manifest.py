"""
生成 data/manifest.json — 校验和 + 数据来源 + 时间范围 (署名合规用)。

独立于下载: 数据下载完成后单独运行, 失败可反复重试, 不重跑下载。
    python scripts/make_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime

# 复用下载脚本里的常量 (import 不触发 main, 仅取配置)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from download_era5 import (  # noqa: E402
    BUCKET, PREFIX, VARS, VAR_META,
    GLOBAL_ZARR, CHINA_ZARR, DATA_DIR,
    GLOBAL_TIMES, CHINA_TIMES, CHINA, t_to_time,
)


def dir_sha256(d: str) -> str:
    """目录级指纹: 按相对路径排序, 逐文件哈希后汇总。"""
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
    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "source": {
            "bucket": f"s3://{BUCKET}",
            "prefix": PREFIX,
            "repo": "icechunk V2, branch main",
            "license": "CC-BY 4.0 — ECMWF (Copernicus Atmosphere Data Store / reanalysis v5)",
            "attribution": "ERA5 single-level data. Source: ECMWF. "
                           "Reference: Hersbach, H. et al. (2020), ERA5: Fifth Generation of "
                           "ECMWF Atmospheric Reanalyses, ECMWF Technical Memoranda.",
        },
        "grid": "0.25 deg regular lat/lon; time = hours since 1940-01-01 00:00 (hourly)",
        "variables": {v: VAR_META[v] for v in VARS},
        "global_7d": {
            "file": "era5_global_7d.zarr",
            "time_range": [t_to_time(GLOBAL_TIMES[0]).isoformat(), t_to_time(GLOBAL_TIMES[-1]).isoformat()],
            "timesteps": len(GLOBAL_TIMES),
            "sha256": dir_sha256(GLOBAL_ZARR),
        },
        "china_30d": {
            "file": "era5_china_30d.zarr",
            "region": f"{CHINA['lon_min']}-{CHINA['lon_max']}E, {CHINA['lat_min']}-{CHINA['lat_max']}N",
            "time_range": [t_to_time(CHINA_TIMES[0]).isoformat(), t_to_time(CHINA_TIMES[-1]).isoformat()],
            "timesteps": len(CHINA_TIMES),
            "sha256": dir_sha256(CHINA_ZARR),
        },
    }
    out = os.path.join(DATA_DIR, "manifest.json")
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest.json written:")
    print("  global_7d  sha256 =", manifest["global_7d"]["sha256"][:16], "…",
          f"({manifest['global_7d']['timesteps']} steps)")
    print("  china_30d  sha256 =", manifest["china_30d"]["sha256"][:16], "…",
          f"({manifest['china_30d']['timesteps']} steps)")


if __name__ == "__main__":
    main()
