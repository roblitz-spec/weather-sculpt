"""
Weather-Sculpt — ERA5 数据下载与打包脚本
================================================
数据源: earthmover-icechunk-era5 (S3, 匿名, CC-BY 4.0)
        Icechunk V2 仓库, zarr v3, pcodec(level 8), chunk = 1 时次全球 (721x1440)

产物:
  data/era5_global_7d.zarr   5 变量 x 168 时次, 0.25° 全球, float32, zstd
  data/era5_china_30d.zarr   5 变量 x 720 时次, 中国区域 (73-135E, 18-53N), zstd
  data/manifest.json         校验和 + 数据来源 + 时间范围 (署名合规用)

策略:
  - pcodec 为纯 Python 解码 (~40s/块), 用 4 进程并行
  - 断点续传: progress.json 记录已完成 (var|t)
  - 中国窗口与全球窗口重叠的时次直接从全球 zarr 切片, 不重复解码
  - 必须绕过系统代理运行:  env -u http_proxy -u https_proxy ... python download_era5.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np
import zarr
import zarr.storage

# ---------- 配置 ----------
BUCKET = "earthmover-icechunk-era5"
PREFIX = "icechunkV2"
REGION = "us-east-1"
BRANCH = "main"
GROUP = "single/spatial"

VARS = ["t2m", "u10", "v10", "tp", "msl"]
VAR_META = {
    "t2m": {"long_name": "2 metre temperature", "units": "K", "short": "2t"},
    "u10": {"long_name": "10 metre U wind component", "units": "m s**-1", "short": "10u"},
    "v10": {"long_name": "10 metre V wind component", "units": "m s**-1", "short": "10v"},
    "tp": {"long_name": "Total precipitation", "units": "m", "short": "tp"},
    "msl": {"long_name": "Mean sea level pressure", "units": "Pa", "short": "msl"},
}

N_LAT, N_LON = 721, 1440
T_END = 756047                      # 最新时次索引 (hours since 1940-01-01)
GLOBAL_DAYS = 7                     # 168 时次
CHINA_DAYS = 30                     # 720 时次
CHINA = {"lat_min": 18.0, "lat_max": 53.0, "lon_min": 73.0, "lon_max": 135.0}
# 瓶颈在单连接 (~20KB/s), 不是 CPU (pcodec 为 C 实现, 解码 <0.2s)。
# 并行连接可线性叠加 (实测 4 路 ≈ 69KB/s); 但 16 路会触发 AWS 连接重置 (os 10054),
# 故取 8 路 + worker 内退避重试。
WORKERS = 8
MAX_TRIES = 5

T0 = datetime(1940, 1, 1)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")
GLOBAL_ZARR = os.path.join(DATA_DIR, "era5_global_7d.zarr")
CHINA_ZARR = os.path.join(DATA_DIR, "era5_china_30d.zarr")

GLOBAL_TIMES = list(range(T_END - 24 * GLOBAL_DAYS + 1, T_END + 1))
CHINA_TIMES = list(range(T_END - 24 * CHINA_DAYS + 1, T_END + 1))
CHINA_NEW_TIMES = [t for t in CHINA_TIMES if t not in set(GLOBAL_TIMES)]

# 中国区域在 0.25° 网格上的行列 (lat 从 90N 向下, lon 从 0E 向右)
LAT_SLICE = (slice(int((90 - CHINA["lat_max"]) / 0.25), int((90 - CHINA["lat_min"]) / 0.25) + 1),)
LON_SLICE = slice(int(CHINA["lon_min"] / 0.25), int(CHINA["lon_max"] / 0.25) + 1)
LAT_LEN = (90 - CHINA["lat_min"]) / 0.25 - (90 - CHINA["lat_max"]) / 0.25 + 1   # 141
LON_LEN = (CHINA["lon_max"] - CHINA["lon_min"]) / 0.25 + 1                     # 248


def t_to_time(t: int) -> datetime:
    return T0 + timedelta(hours=int(t))


_STORE = None


def get_store():
    """每个 worker 进程缓存一个只读会话 (不可跨进程共享, 进程内复用)。"""
    global _STORE
    if _STORE is None:
        import icechunk
        storage = icechunk.s3_storage(bucket=BUCKET, prefix=PREFIX, region=REGION, anonymous=True)
        repo = icechunk.Repository.open(storage)
        _STORE = repo.readonly_session(BRANCH).store
    return _STORE


def pick_codec():
    """zarr v3 原生 codec (venv 为 zarr>=3)。"""
    try:
        return lambda: zarr.codecs.ZstdCodec(level=3)
    except Exception:
        return lambda: zarr.codecs.GzipCodec(level=4)


CODEC = pick_codec()


def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(p: dict):
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(p, f)
    os.replace(tmp, PROGRESS_FILE)


# ---------- worker (模块顶层, 供 Windows spawn 用) ----------
def fetch_chunk(task: tuple[str, int]) -> tuple[str, int, np.ndarray]:
    """解码一个 (var, t) 全球时次, 返回 (var, t, 2D array)。带退避重试。"""
    var, t = task
    last_err: Exception | None = None
    for attempt in range(MAX_TRIES):
        try:
            store = get_store()
            a = zarr.open_array(store, path=f"{GROUP}/{var}", mode="r")
            arr = np.asarray(a[t, :, :])
            return var, t, arr
        except Exception as e:
            last_err = e
            time.sleep(5 * (attempt + 1))  # 5s, 10s, 15s, 20s, 25s
    raise last_err  # type: ignore[misc]


def build_global_zarr():
    zroot = zarr.open(GLOBAL_ZARR, mode="a")
    for var in VARS:
        arr = zroot.require_array(
            var, shape=(len(GLOBAL_TIMES), N_LAT, N_LON), dtype="float32",
            chunks=(1, N_LAT, N_LON), compressors=[CODEC()],
            fill_value=np.nan,
            dimension_names=["time_index", "latitude", "longitude"],
        )
        arr.attrs.update(VAR_META[var])
        arr.attrs["grid"] = "0.25 deg regular lat/lon, lat 90..-90, lon 0..359.75"
    # 坐标 (zarr v3 维度名写进 metadata.dimension_names, xarray 据此确定维度)
    zroot.require_array("time_index", shape=(len(GLOBAL_TIMES),), dtype="int64",
                        compressors=[CODEC()],
                        dimension_names=["time_index"])[...] = np.array(GLOBAL_TIMES, dtype="int64")
    zroot.require_array("latitude", shape=(N_LAT,), dtype="float64",
                        compressors=[CODEC()],
                        dimension_names=["latitude"])[...] = np.linspace(90.0, -90.0, N_LAT)
    zroot.require_array("longitude", shape=(N_LON,), dtype="float64",
                        compressors=[CODEC()],
                        dimension_names=["longitude"])[...] = np.arange(0.0, 360.0, 0.25)[:N_LON]
    zroot.attrs.update({
        "title": "ERA5 surface fields, global 0.25 deg, 7 days hourly",
        "source": f"s3://{BUCKET}/{PREFIX} (CC-BY 4.0, ECMWF/ECMWF+Copernicus)",
        "time_units": "hours since 1940-01-01 00:00:00 (proleptic_gregorian)",
        "created": datetime.now().isoformat(timespec="seconds"),
    })
    return zroot


def build_china_zarr():
    zroot = zarr.open(CHINA_ZARR, mode="a")
    for var in VARS:
        arr = zroot.require_array(
            var, shape=(len(CHINA_TIMES), int(LAT_LEN), int(LON_LEN)), dtype="float32",
            chunks=(1, int(LAT_LEN), int(LON_LEN)), compressors=[CODEC()],
            fill_value=np.nan,
            dimension_names=["time_index", "latitude", "longitude"],
        )
        arr.attrs.update(VAR_META[var])
        arr.attrs["region"] = f"{CHINA['lon_min']}-{CHINA['lon_max']}E, {CHINA['lat_min']}-{CHINA['lat_max']}N"
    zroot.require_array("time_index", shape=(len(CHINA_TIMES),), dtype="int64",
                        compressors=[CODEC()],
                        dimension_names=["time_index"])[...] = np.array(CHINA_TIMES, dtype="int64")
    zroot.require_array("latitude", shape=(int(LAT_LEN),), dtype="float64",
                        compressors=[CODEC()],
                        dimension_names=["latitude"])[...] = np.linspace(CHINA["lat_max"], CHINA["lat_min"], int(LAT_LEN))
    zroot.require_array("longitude", shape=(int(LON_LEN),), dtype="float64",
                        compressors=[CODEC()],
                        dimension_names=["longitude"])[...] = np.arange(CHINA["lon_min"], CHINA["lon_max"] + 0.25, 0.25)[:int(LON_LEN)]
    zroot.attrs.update({
        "title": "ERA5 surface fields, China region 0.25 deg, 30 days hourly",
        "source": f"s3://{BUCKET}/{PREFIX} (CC-BY 4.0, ECMWF/ECMWF+Copernicus)",
        "time_units": "hours since 1940-01-01 00:00:00 (proleptic_gregorian)",
        "created": datetime.now().isoformat(timespec="seconds"),
    })
    return zroot


def download_phase(tasks: list[tuple[str, int]], progress: dict,
                   store_write: callable, label: str) -> None:
    """并行解码 tasks, 每完成一个写入目标 zarr 并更新进度。"""
    pending = [t for t in tasks if f"{t[0]}|{t[1]}" not in progress]
    print(f"[{label}] total={len(tasks)} pending={len(pending)} workers={WORKERS}", flush=True)
    if not pending:
        return
    done = 0
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(fetch_chunk, task): task for task in pending}
        for fut in as_completed(futures):
            var, t = futures[fut]
            try:
                v, t, arr = fut.result()
            except Exception as e:
                print(f"  !! {var}|{t} FAILED after {MAX_TRIES} tries: {type(e).__name__}: {e} — 跳过, 重跑脚本会补上", flush=True)
                continue
            store_write(v, t, arr)
            progress[f"{var}|{t}"] = t_to_time(t).isoformat(timespec="hours")
            done += 1
            if done % 10 == 0 or done == len(pending):
                el = time.time() - t_start
                eta = el / done * (len(pending) - done)
                print(f"  [{label}] {done}/{len(pending)} elapsed={el/60:.0f}m eta={eta/60:.0f}m", flush=True)
                save_progress(progress)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    # 绕过代理 (双保险)
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        os.environ.pop(k, None)

    progress = load_progress()
    zglobal = build_global_zarr()
    zchina = build_china_zarr()

    def g_write(v, t, a):
        zglobal[v][GLOBAL_TIMES.index(t)] = a

    def c_write(v, t, a):
        zchina[v][CHINA_TIMES.index(t)] = a

    t_start = time.time()
    print(f"=== Phase 1: global {GLOBAL_DAYS}d ({len(VARS)*len(GLOBAL_TIMES)} chunks) ===", flush=True)
    download_phase([(v, t) for v in VARS for t in GLOBAL_TIMES], progress, g_write, "global")

    print(f"=== Phase 2: China {CHINA_DAYS}d, new-only {len(VARS)*len(CHINA_NEW_TIMES)} chunks ===", flush=True)
    download_phase([(v, t) for v in VARS for t in CHINA_NEW_TIMES], progress, c_write, "china")

    # 重叠时次: 从全球 zarr 切片进中国 zarr
    print("=== Phase 3: slice overlap (global -> china) ===", flush=True)
    for var in VARS:
        src = zglobal[var]
        dst = zchina[var]
        for i, t in enumerate(CHINA_TIMES):
            if t in set(GLOBAL_TIMES):
                gi = GLOBAL_TIMES.index(t)
                dst[i] = src[gi][LAT_SLICE[0], LON_SLICE]
        print(f"  {var} overlap sliced", flush=True)

    save_progress(progress)
    print(f"DONE in {(time.time()-t_start)/3600:.2f}h", flush=True)

    # manifest
    import hashlib

    def dir_sha256(d):
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
    with open(os.path.join(DATA_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest.json written", flush=True)


if __name__ == "__main__":
    main()
