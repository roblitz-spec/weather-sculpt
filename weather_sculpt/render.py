"""
Render a preset over time into frames, then export.

Outputs (by extension of `out`):
  .gif   animated GIF (needs Pillow)
  .mp4   H.264 (needs ffmpeg on PATH; falls back to GIF if missing)
  .png   single frame
  dir/   PNG sequence (no extra deps)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import xarray as xr  # noqa: E402

from .fields import open_weather  # noqa: E402
from .presets import PRESETS, draw_frame  # noqa: E402

_DPI = 100
_BG = "#0d1117"


def _ensure_ds(ds_or_path) -> xr.Dataset:
    if isinstance(ds_or_path, xr.Dataset):
        return ds_or_path
    return open_weather(str(ds_or_path))


def render_video(
    ds_or_path,
    preset: str,
    out: str,
    frames: int | None = None,
    start: int = 0,
    fps: int = 2,
    width: int = 1280,
    height: int = 720,
    progress: bool = True,
):
    """Render `preset` from `ds_or_path` (zarr path or Dataset) to `out`.

    frames: how many timesteps to animate (default: all, sampled evenly
            from `start`). Returns the written file path.
    """
    ds = _ensure_ds(ds_or_path)
    cfg = PRESETS[preset]
    n_total = len(ds["time"])
    need = cfg.get("window", 1)
    lo = max(start, need - 1)
    if frames is None:
        idx = list(range(lo, n_total))
    else:
        idx = np.linspace(lo, n_total - 1, frames, dtype=int).tolist()
        if len(set(idx)) < len(idx):
            idx = list(range(lo, min(lo + frames, n_total)))

    out = os.path.abspath(out)
    ext = os.path.splitext(out)[1].lower()
    if ext == ".png":
        return _render_single(ds, preset, out, idx[0])

    png_dir = tempfile.mkdtemp(prefix="wsculpt_")
    for i, t in enumerate(idx):
        fig = plt.figure(figsize=(width / _DPI, height / _DPI), dpi=_DPI)
        fig.patch.set_facecolor(_BG)
        ax = fig.add_subplot(111)
        draw_frame(ax, ds, preset, t)
        ts = ds["time"].values[t]
        ax.text(
            0.02, 0.02, str(ts)[:16], transform=ax.transAxes,
            color="white", fontsize=8, family="monospace",
        )
        p = os.path.join(png_dir, f"frame_{i:04d}.png")
        fig.savefig(p, facecolor=_BG)
        plt.close(fig)
        if progress and (i % 5 == 0 or i == len(idx) - 1):
            print(f"  frame {i + 1}/{len(idx)}  t={ts}", flush=True)

    try:
        if ext == ".gif":
            _to_gif(png_dir, out, fps)
        elif ext == ".mp4":
            _to_mp4(png_dir, out, fps)
        elif ext in ("", os.sep):
            os.makedirs(out, exist_ok=True)
            for f in sorted(os.listdir(png_dir)):
                shutil.copy(os.path.join(png_dir, f), os.path.join(out, f))
            print(f"PNG sequence -> {out}", flush=True)
            return out
        else:
            raise ValueError(f"unsupported output extension {ext!r} (use .gif/.mp4/.png/dir)")
    finally:
        shutil.rmtree(png_dir, ignore_errors=True)
    print(f"wrote {out}", flush=True)
    return out


def _render_single(ds, preset, out, t):
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=_DPI)
    fig.patch.set_facecolor(_BG)
    draw_frame(ax, ds, preset, t)
    ts = ds["time"].values[t]
    ax.text(0.02, 0.02, str(ts)[:16], transform=ax.transAxes,
            color="white", fontsize=8, family="monospace")
    fig.savefig(out, facecolor=_BG)
    plt.close(fig)
    print(f"wrote {out}", flush=True)
    return out


def _frames(png_dir):
    return sorted(
        os.path.join(png_dir, f) for f in os.listdir(png_dir) if f.endswith(".png")
    )


def _to_gif(png_dir, out, fps):
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("Pillow required for GIF export: pip install pillow") from e
    imgs = _frames(png_dir)
    frames = [Image.open(p) for p in imgs]
    duration = int(1000 / fps)
    frames[0].save(
        out, save_all=True, append_images=frames[1:],
        duration=duration, loop=0, optimize=False,
    )


def _to_mp4(png_dir, out, fps):
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found on PATH — falling back to GIF", flush=True)
        gif = os.path.splitext(out)[0] + ".gif"
        _to_gif(png_dir, gif, fps)
        return
    cmd = [
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(png_dir, "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "veryfast", out,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
