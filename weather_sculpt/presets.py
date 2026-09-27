"""
Tuned "sculpt" presets: each one turns an ERA5 field set into an animated frame.

  temperature_waves  2 m 温度波场 (标量场, RdYlBu_r)
  wind_streamlines   10 m 风场流线 (streamplot, 按风速着色)
  rain_curtain       降水雨幕 (6h 滚动累积, Wistia)
  pressure_vortex    气压涡旋 (等压线 + 相对涡度着色)
"""
from __future__ import annotations

import numpy as np
import xarray as xr

from .fields import normalize, to_celsius, vorticity

PRESETS: dict[str, dict] = {
    "temperature_waves": {
        "kind": "scalar",
        "var": "t2m",
        "cmap": "RdYlBu_r",
        "title": "2 m temperature — ERA5",
        "unit": "°C",
    },
    "wind_streamlines": {
        "kind": "streamline",
        "var": "u10",
        "cmap": "viridis",
        "title": "10 m wind — ERA5",
        "unit": "m/s",
    },
    "rain_curtain": {
        "kind": "rain",
        "var": "tp",
        "cmap": "Wistia",
        "title": "Precipitation (6 h rolling) — ERA5",
        "unit": "mm",
        "window": 6,
    },
    "pressure_vortex": {
        "kind": "vortex",
        "var": "msl",
        "cmap": "RdBu",
        "title": "MSLP + relative vorticity — ERA5",
        "unit": "hPa",
    },
}


def list_presets() -> list[str]:
    return list(PRESETS)


# ---------------------------------------------------------------- frames

def _setup_ax(ax, ds):
    lat = ds["latitude"].values
    lon = ds["longitude"].values
    ax.set_xlim(lon[0], lon[-1])
    ax.set_ylim(lat[-1], lat[0])
    ax.set_xlabel("lon")
    ax.set_ylabel("lat")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_facecolor("#0d1117")
    ax.tick_params(colors="white")
    for s in ax.spines.values():
        s.set_color("#555")
    return lat, lon


def _scalar_frame(ax, ds, cfg, t):
    lat, lon = _setup_ax(ax, ds)
    a = to_celsius(ds[cfg["var"]][t].values) if cfg["var"] == "t2m" else ds[cfg["var"]][t].values
    norm = normalize(a)
    im = ax.imshow(
        norm, origin="upper",
        extent=(lon[0], lon[-1], lat[-1], lat[0]),
        aspect="auto", cmap=cfg["cmap"],
    )
    cb = ax.figure.colorbar(im, ax=ax, pad=0.02)
    cb.ax.tick_params(colors="white", labelsize=7)
    lo, hi = np.nanpercentile(a[np.isfinite(a)], [2, 98])
    ax.set_title(f"{cfg['title']}  [{lo:.1f} … {hi:.1f} {cfg['unit']}]", color="white", fontsize=9)
    return im


def _streamline_frame(ax, ds, cfg, t, step: int = 3):
    lat, lon = _setup_ax(ax, ds)
    # 纬度轴是 90->-90 (递减); streamplot 要求 y 严格递增, 故翻转纬度与对应数据行
    # (v 是北向分量, 物理值不变, 仅让数据行与翻转后的 y 坐标对齐)。
    u = ds["u10"][t].values[::step, ::step][::-1]
    v = ds["v10"][t].values[::step, ::step][::-1]
    ll = lat[::step][::-1]
    lo_ = lon[::step]
    speed = np.hypot(u, v)
    Q = np.meshgrid(lo_, ll)
    sp = normalize(speed)
    sp = 0.15 + 0.85 * sp
    sp[~np.isfinite(sp)] = 0.2
    stream = ax.streamplot(
        Q[0], Q[1], u, v, color=sp, cmap=cfg["cmap"],
        density=1.6, linewidth=0.8, arrowsize=0.7,
    )
    cb = ax.figure.colorbar(stream.lines, ax=ax, pad=0.02)
    cb.set_label("wind speed (rel.)", color="white", fontsize=7)
    cb.ax.tick_params(colors="white", labelsize=7)
    ax.set_title(f"{cfg['title']}  [max {np.nanmax(speed):.1f} {cfg['unit']}]", color="white", fontsize=9)
    return stream


def _rain_frame(ax, ds, cfg, t, window: int | None = None):
    lat, lon = _setup_ax(ax, ds)
    w = window or cfg.get("window", 6)
    tp = ds[cfg["var"]].values[: t + 1]
    acc = tp[-w:].sum(axis=0) * 1000.0  # m -> mm
    norm = normalize(np.log1p(acc))
    im = ax.imshow(
        norm, origin="upper",
        extent=(lon[0], lon[-1], lat[-1], lat[0]),
        aspect="auto", cmap=cfg["cmap"],
    )
    cb = ax.figure.colorbar(im, ax=ax, pad=0.02)
    cb.set_label(f"precip {w}h (log, mm)", color="white", fontsize=7)
    cb.ax.tick_params(colors="white", labelsize=7)
    ax.set_title(f"{cfg['title']}  [Σ {np.nanmax(acc):.1f} mm]", color="white", fontsize=9)
    return im


def _vortex_frame(ax, ds, cfg, t):
    lat, lon = _setup_ax(ax, ds)
    msl = ds["msl"][t].values / 100.0  # Pa -> hPa
    zeta = vorticity(ds["u10"], ds["v10"], t) * 1e5  # 1e-5 /s
    zeta = np.where(np.isfinite(zeta), zeta, 0.0)
    im = ax.imshow(
        normalize(zeta, lo=2, hi=98),
        origin="upper",
        extent=(lon[0], lon[-1], lat[-1], lat[0]),
        aspect="auto", cmap=cfg["cmap"],
    )
    finite = msl[np.isfinite(msl)]
    if finite.size:
        LON, LAT = np.meshgrid(lon, lat)
        levels = np.linspace(np.percentile(finite, 5), np.percentile(finite, 95), 9)
        cs = ax.contour(LON, LAT, msl, levels=levels,
                        colors="white", linewidths=0.5, alpha=0.6)
        ax.clabel(cs, fmt="%.0f", fontsize=6, colors="white")
    cb = ax.figure.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("relative vorticity (1e-5 /s)", color="white", fontsize=7)
    cb.ax.tick_params(colors="white", labelsize=7)
    ax.set_title(cfg["title"], color="white", fontsize=9)
    return im


_DISPATCH = {
    "scalar": _scalar_frame,
    "streamline": _streamline_frame,
    "rain": _rain_frame,
    "vortex": _vortex_frame,
}


def draw_frame(ax, ds: xr.Dataset, preset: str, t: int):
    """Draw one frame of `preset` at time index `t` onto matplotlib axes `ax`."""
    if preset not in PRESETS:
        raise KeyError(f"unknown preset {preset!r}; choose from {list_presets()}")
    cfg = PRESETS[preset]
    fn = _DISPATCH[cfg["kind"]]
    if t < 0 or t >= len(ds["time"]):
        raise IndexError(f"t={t} out of range [0, {len(ds['time']) - 1}]")
    if cfg["kind"] == "rain" and t < cfg.get("window", 6) - 1:
        t = cfg.get("window", 6) - 1
    return fn(ax, ds, cfg, t)
