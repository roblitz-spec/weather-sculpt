"""
Weather sonification — the Weather-Sculpt signature channel.

Two modes:
  zonal  每时次一个音: 纬向均值 -> 音高, 空间离散度 -> 响度。
         听感: 天气系统的"心跳"。
  sweep  每时次一个和弦: 纬向剖面切成 12 个纬度带, 各带值 -> 五声音阶音高,
         强度 -> 分量幅度。听感: 南北方向的"天气和声"缓慢演变。

输出 16-bit PCM WAV (纯 numpy, 无额外依赖)。
"""
from __future__ import annotations

import os
import wave

import numpy as np

from .fields import open_weather

_SR_DEFAULT = 22050
# 五声音阶 (C 大调五声): C D E G A 跨两个八度
_SCALE = [261.63, 293.66, 329.63, 392.00, 440.00,
          523.25, 587.33, 659.25, 783.99, 880.00,
          1046.50, 1174.66]


def _env(n: int, attack: float = 0.08, release: float = 0.25) -> np.ndarray:
    """Simple attack/hold/release envelope."""
    e = np.ones(n)
    na = max(1, int(n * attack))
    nr = max(1, int(n * release))
    e[:na] *= np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def _tone(freq: float, n: int, amp: float, sr: int) -> np.ndarray:
    if freq <= 0 or amp <= 0 or n <= 0:
        return np.zeros(n)
    t = np.arange(n) / sr
    body = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t)
    return amp * body * _env(n)


def sonify(
    ds_or_path,
    var: str = "t2m",
    out: str = "weather.wav",
    mode: str = "zonal",
    sr: int = _SR_DEFAULT,
    seconds_per_step: float = 0.5,
    frames: int | None = None,
    gain: float = 0.5,
) -> str:
    """Sonify `var` from a Weather-Sculpt zarr dataset. Returns the WAV path."""
    ds = ds_or_path if hasattr(ds_or_path, "data_vars") else open_weather(str(ds_or_path))
    a = ds[var].values.astype("float64")
    a = np.where(np.isfinite(a), a, np.nan)
    n_t = a.shape[0]
    if frames is None:
        idx = list(range(n_t))
    else:
        idx = np.linspace(0, n_t - 1, frames, dtype=int).tolist()

    n = int(sr * seconds_per_step)
    out_path = np.zeros((len(idx), n))

    # 预计算整段序列统计 (O(n) 次全场归约, 避免 O(n^2)); 空帧产生 NaN, 忽略告警
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        means = np.array([np.nanmean(a[t]) for t in idx])
        stds = np.array([np.nanstd(a[t]) for t in idx])

    def rank_of(v, arr):
        if not np.isfinite(v):
            return 0.5
        return float(np.nanmean(arr <= v))

    for i, t in enumerate(idx):
        # 空帧 (该时次尚未下载, 全 NaN) -> 静音, 跳过
        if not np.isfinite(a[t]).any():
            continue
        if mode == "zonal":
            if not np.isfinite(means[i]):
                continue
            f = 110.0 + 770.0 * rank_of(means[i], means)
            amp = 0.15 + 0.85 * rank_of(stds[i], stds)
            out_path[i] = _tone(f, n, amp, sr)
        elif mode == "sweep":
            profile = np.nanmean(a[t], axis=1)  # (lat,)
            if not np.isfinite(profile).any():
                continue
            nb = 12
            bands = np.array_split(profile, nb)
            vals = [np.nanmean(b) for b in bands]
            vals = np.array([v if np.isfinite(v) else np.nan for v in vals])
            finite = vals[np.isfinite(vals)]
            if finite.size == 0:
                continue
            lo, hi = float(finite.min()), float(finite.max())
            rng = (hi - lo) or 1.0
            for b_i, v in enumerate(vals):
                if not np.isfinite(v):
                    continue
                pos = float(np.clip((v - lo) / rng, 0.0, 1.0))
                note = _SCALE[min(nb - 1, int(pos * nb))]
                amp = 0.02 + 0.10 * (1.0 - abs(2 * pos - 1))  # 中段更响
                out_path[i] += _tone(note, n, amp, sr)
        else:
            raise ValueError(f"unknown mode {mode!r} (use 'zonal' or 'sweep')")

    pcm = out_path * gain
    pcm = np.clip(pcm, -1.0, 1.0)
    pcm16 = (pcm * 32767).astype("<i2")

    out = os.path.abspath(out)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm16.tobytes())
    print(f"wrote {out} ({len(idx) * seconds_per_step:.1f}s @ {sr}Hz, mode={mode})", flush=True)
    return out
