"""Field loading and differential operators for 2-D lat/lon weather fields."""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import xarray as xr

_T0 = datetime(1940, 1, 1)
_EARTH_R = 6371000.0


def open_weather(path: str, var: str | None = None) -> xr.Dataset:
    """Open a Weather-Sculpt zarr dataset (era5_global_7d.zarr / era5_china_30d.zarr).

    Adds a decoded `time` coordinate (ERA5 index = hours since 1940-01-01).
    Pass `var` to keep only one variable (plus coordinates).
    """
    ds = xr.open_zarr(path, decode_times=False, decode_cf=False, consolidated=False, chunks=None)
    ti = ds["time_index"].values
    ds = ds.assign_coords(
        time=[_T0 + timedelta(hours=int(t)) for t in ti]
    )
    if var is not None:
        keep = [var] + [c for c in ds.coords if c not in ("time_index",)]
        ds = ds[keep] if var in ds.data_vars else ds[[var]]
    return ds


def _grid_spacing(lat: np.ndarray, lon: np.ndarray):
    # 用带符号的间距: ERA5 纬度轴是 90->-90 (递减), 故 dy 为负,
    # 使 np.gradient(f, axis=0)/dy 给出正确的北向 ∂f/∂y (递增布局下自动为正)。
    dlat = float(np.median(np.diff(lat)))
    dlon = float(np.median(np.diff(lon)))
    dy = dlat * np.pi / 180.0 * _EARTH_R
    # per-latitude x-spacing (m per lon step), 用 |lon 步长|, 恒正
    lat0 = lat[:, 0] if lat.ndim == 2 else lat
    dx_row = abs(dlon) * np.pi / 180.0 * _EARTH_R * np.cos(np.deg2rad(lat0))
    return dy, dx_row


def _d_dx(f2d: np.ndarray, dx_row: np.ndarray) -> np.ndarray:
    """Partial derivative along longitude with per-row spacing."""
    g = np.gradient(f2d, axis=1)
    return g / dx_row[:, None]


def _d_dy(f2d: np.ndarray, dy: float) -> np.ndarray:
    return np.gradient(f2d, axis=0) / dy


def vorticity(u: xr.DataArray, v: xr.DataArray, t: int) -> np.ndarray:
    """Relative vorticity (1/s) at time index `t` from u/v components.

    Spherical approximation: zeta = dv/dx - du/dy, x-spacing scaled by cos(lat).
    """
    u2 = u[t].values.astype("float64")
    v2 = v[t].values.astype("float64")
    lat = u[t].coords["latitude"].values
    lon = u[t].coords["longitude"].values
    dy, dx_row = _grid_spacing(lat, lon)
    return _d_dx(v2, dx_row) - _d_dy(u2, dy)


def divergence(u: xr.DataArray, v: xr.DataArray, t: int) -> np.ndarray:
    """Horizontal divergence (1/s) at time index `t`."""
    u2 = u[t].values.astype("float64")
    v2 = v[t].values.astype("float64")
    lat = u[t].coords["latitude"].values
    lon = u[t].coords["longitude"].values
    dy, dx_row = _grid_spacing(lat, lon)
    return _d_dx(u2, dx_row) + _d_dy(v2, dy)


def normalize(a: np.ndarray, lo: float = 1.0, hi: float = 99.0) -> np.ndarray:
    """Percentile-clip a field to [0, 1] for colormap stability."""
    a = np.asarray(a, dtype="float64")
    finite = a[np.isfinite(a)]
    if finite.size == 0:
        return np.zeros_like(a)
    p_lo, p_hi = np.percentile(finite, [lo, hi])
    if p_hi <= p_lo:
        p_hi = p_lo + 1.0
    return np.clip((a - p_lo) / (p_hi - p_lo), 0.0, 1.0)


def to_celsius(t2m_k: np.ndarray) -> np.ndarray:
    """K -> deg C."""
    return np.asarray(t2m_k, dtype="float64") - 273.15
