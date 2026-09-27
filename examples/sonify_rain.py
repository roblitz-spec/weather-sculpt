"""降水声化: 内置样本场的 tp 场 -> 五声音阶"天气和声" WAV。

用法:  python examples/sonify_rain.py [输出路径]
"""
import os
import sys

from weather_sculpt import sonify

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "weather_sculpt", "data", "era5_sample.zarr")
out = sys.argv[1] if len(sys.argv) > 1 else "rain.wav"

if not os.path.exists(DATA):
    raise SystemExit("样本场不存在: %s (pip 安装后自带)" % DATA)

sonify(DATA, "tp", out, mode="sweep", frames=120, seconds_per_step=0.4)
