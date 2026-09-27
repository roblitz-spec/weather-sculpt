# Weather-Sculpt

**用真实的 ERA5 气象场"雕刻"出视频、GIF 和声音。**

不是动画模拟——是 ECMWF 第五代再分析（ERA5, CC-BY 4.0）的真实大气状态，  
经 4 个预调"雕刻"预设渲染成可发布的媒体，并附一条独有的**天气声化**通道。

> 不想装任何东西？浏览器 demo：[weather-sculpt demo](https://roblitz-spec.github.io/weather-sculpt/)

## 预设 · Presets

| 预设                  | 画面               |
| ------------------- | ---------------- |
| `temperature_waves` | 2 m 温度波场         |
| `wind_streamlines`  | 10 m 风场流线（按风速着色） |
| `rain_curtain`      | 6 小时滚动降水雨幕       |
| `pressure_vortex`   | 相对涡旋 + 等压线       |

## 快速开始 · Quickstart

```bash
pip install weather-sculpt
```

```python
from weather_sculpt import render_video, sonify

# 内置迷你样本场（pip 免费层自带, 全 5 变量 / 1° / 7 天）
import os, weather_sculpt
DATA = os.path.join(os.path.dirname(weather_sculpt.__file__), "data", "era5_sample.zarr")

# 一段 60 帧的温度波场 GIF
render_video(DATA, "temperature_waves", "temperature.gif", frames=60, fps=3)

# 把降水"听"出来
sonify(DATA, "tp", "rain.wav", mode="sweep", frames=120)
```

用你自己的 ERA5 数据（任意 0.25° zarr/netCDF 同构数据集）：

```python
from weather_sculpt import open_weather, render_video
ds = open_weather("your/era5.zarr")
render_video(ds, "wind_streamlines", "wind.mp4", frames=120, fps=2)
```

## 免费层 vs 完整包 · Free tier vs Ready-to-Run

|    | 免费层（pip / 本仓库 / demo） | Ready-to-Run 完整包（Gumroad）                     |
| -- | --------------------- | --------------------------------------------- |
| 代码 | ✅ MIT                 | ✅ MIT + 商业授权书                                 |
| 数据 | 迷你样本场                 | **全球 0.25° × 7 天 + 中国区域 × 30 天**（下好、校验过，zstd） |
| 预设 | ✅ 全部                  | ✅ 全部（预调参数）                                    |
| 声化 | ✅                     | ✅                                             |
| 商用 | 需自行遵循 CC-BY 署名并承担取数成本 | **商业授权 + 署名合规 + manifest 校验**                 |

完整包购买：[Weather-Sculpt on Gumroad](https://robloxer31.gumroad.com/l/Weather-Sculpt)

## 数据与署名 · Data & Attribution

ERA5 数据遵循 **CC-BY 4.0**（ECMWF）。任何再分发须保留署名：

> Weather data: **ECMWF ERA5** (CC-BY 4.0). Engine: **weather-sculpt** (roblitz).

## 文件结构

```
weather-sculpt/
├── weather_sculpt/
│   ├── fields.py      # 场加载 + 涡度/散度/归一化
│   ├── presets.py     # 4 个雕刻预设
│   ├── render.py      # PNG 序列 / GIF / MP4
│   ├── sonify.py      # 天气声化 (WAV)
│   └── data/          # 内置迷你样本场（全 5 变量, 1°, 7 天）
├── examples/
├── scripts/
│   ├── download_era5.py    # ERA5 开放数据下载脚本（匿名 S3，免费）
│   ├── make_sample.py      # 生成包内样本
│   ├── make_manifest.py    # 生成校验和 manifest
│   ├── verify_manifest.py  # 买家复算校验
│   └── make_showcase.py    # 渲染展示 GIF
├── QUICKSTART.md
├── README.md / MODEL.md
└── LICENSE.md / LICENSE_COMMERCIAL.md
```
