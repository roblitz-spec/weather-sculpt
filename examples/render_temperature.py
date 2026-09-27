"""温度波场: 内置样本场 -> 60 帧 GIF (3 fps ≈ 20 秒)。

用法:  python examples/render_temperature.py [输出路径]
"""
import os
import sys

from weather_sculpt import render_video

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "weather_sculpt", "data", "era5_sample.zarr")
out = sys.argv[1] if len(sys.argv) > 1 else "temperature.gif"

if not os.path.exists(DATA):
    raise SystemExit("样本场不存在: %s (pip 安装后自带)" % DATA)

render_video(DATA, "temperature_waves", out, frames=60, fps=3, width=1280, height=720)
