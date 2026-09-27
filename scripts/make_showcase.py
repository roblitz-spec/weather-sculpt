"""渲染 4 个预设的展示 GIF (营销/README 用) — 从完整数据出, 每 6 小时一帧, 28 帧。

    python scripts/make_showcase.py            # 全部 4 个
    python scripts/make_showcase.py wind rain  # 只渲染指定预设
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather_sculpt import list_presets, render_video  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "era5_global_7d.zarr")
OUT_DIR = os.path.join(BASE, "demo")

# preset -> 输出文件名
NAMES = {
    "temperature_waves": "temperature_7d.gif",
    "wind_streamlines": "wind_streamlines_7d.gif",
    "rain_curtain": "rain_curtain_7d.gif",
    "pressure_vortex": "pressure_vortex_7d.gif",
}


def main():
    want = sys.argv[1:] or list_presets()
    os.makedirs(OUT_DIR, exist_ok=True)
    for p in want:
        out = os.path.join(OUT_DIR, NAMES[p])
        print(f"=== {p} -> {NAMES[p]} ===", flush=True)
        render_video(SRC, p, out, frames=28, fps=3, progress=True)
        print(f"  done: {out}", flush=True)
    print("ALL SHOWCASE GIFS DONE", flush=True)


if __name__ == "__main__":
    main()
