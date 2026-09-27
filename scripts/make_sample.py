"""Build the free-tier sample dataset (era5_sample.zarr) from the downloaded global zarr.

Default: t2m only, 24 timesteps, full global 0.25 deg, zstd(level 5) — small enough
to ship inside the pip wheel. Re-run after the full download to expand to all 5 vars.
"""
import os, sys, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import zarr

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "era5_global_7d.zarr")
OUT = os.path.join(BASE, "weather_sculpt", "data", "era5_sample.zarr")

# 变量 -> 是否纳入 (下载完成后可全开)
VARS = ["t2m", "u10", "v10", "tp", "msl"]
N_STEPS = 24           # 24 时次 (7 天里每 ~14h 一帧, 动画更顺)
MIN_COMPLETE = 0.95    # 变量须 >=95% 采样时次有数据才纳入 (避免半空变量)
RES_FACTOR = 4         # 每隔 N 个像素取样 (4 = 1°, 像素量 1/N^2; 控制 wheel 体积)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    src = zarr.open(SRC, mode="r")
    n_lat, n_lon = 721, 1440
    # 空间降采样 (控制体积)
    slat, slon = slice(None, None, RES_FACTOR), slice(None, None, RES_FACTOR)
    lat_s = np.linspace(90.0, -90.0, n_lat)[slat]
    lon_s = np.arange(0.0, 360.0, 0.25)[:n_lon][slon]
    n_lat_s, n_lon_s = len(lat_s), len(lon_s)
    ti_src = np.asarray(src["time_index"])
    # 均匀取 N_STEPS 个时次
    idx = np.linspace(0, len(ti_src) - 1, N_STEPS, dtype=int)

    # 决定纳入哪些变量 (源中实际有数据才纳入)
    present = []
    for v in VARS:
        if v in src:
            present.append(v)
    print("vars available in source:", present)
    # 只纳入有有限值数据的变量
    keep = []
    for v in present:
        ok = 0
        for i in idx:
            if np.isfinite(np.asarray(src[v][i])).any():
                ok += 1
        if ok / len(idx) >= MIN_COMPLETE:
            keep.append(v)
    print("vars with data (in sample):", keep)

    zroot = zarr.open(OUT, mode="w")
    times = ti_src[idx]
    for v in keep:
        a = np.asarray(src[v][idx][:, slat, slon], dtype="float32")  # (N, lat_s, lon_s)
        arr = zroot.require_array(
            v, shape=a.shape, dtype="float32",
            chunks=(1, n_lat_s, n_lon_s),
            compressors=[zarr.codecs.ZstdCodec(level=6)],
            fill_value=np.nan,
            dimension_names=["time_index", "latitude", "longitude"],
        )
        arr[...] = a
        arr.attrs["units"] = src[v].attrs.get("units", "")
        arr.attrs["long_name"] = src[v].attrs.get("long_name", v)
        arr.attrs["grid"] = f"{0.25*RES_FACTOR:g} deg regular lat/lon (subsampled {RES_FACTOR}x)"
        print(f"  wrote {v} {a.shape}")

    zroot.require_array("time_index", shape=(len(idx),), dtype="int64",
                        compressors=[zarr.codecs.ZstdCodec(level=6)],
                        dimension_names=["time_index"])[...] = times.astype("int64")
    zroot.require_array("latitude", shape=(n_lat_s,), dtype="float64",
                        compressors=[zarr.codecs.ZstdCodec(level=6)],
                        dimension_names=["latitude"])[...] = lat_s
    zroot.require_array("longitude", shape=(n_lon_s,), dtype="float64",
                        compressors=[zarr.codecs.ZstdCodec(level=6)],
                        dimension_names=["longitude"])[...] = lon_s
    zroot.attrs.update({
        "title": f"Weather-Sculpt sample — ERA5 global {0.25*RES_FACTOR:g} deg, 7 days, 5 vars",
        "source": "s3://earthmover-icechunk-era5 (CC-BY 4.0, ECMWF)",
        "time_units": "hours since 1940-01-01 00:00 (proleptic_gregorian)",
    })

    # 大小
    total = 0
    for r, _d, names in os.walk(OUT):
        for nm in names:
            total += os.path.getsize(os.path.join(r, nm))
    print(f"sample written: {OUT}  ({total/1e6:.1f} MB)")
    with open(os.path.join(OUT, "sample_info.json"), "w") as f:
        json.dump({"vars": keep, "timesteps": len(idx),
                   "time_range": [str(times[0]), str(times[-1])]}, f, indent=2)


if __name__ == "__main__":
    main()
