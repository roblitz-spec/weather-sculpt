# Weather-Sculpt — 5 分钟上手

> Ready-to-Run 完整包：预置真实 ERA5 气象场（全球 7 天 + 中国 30 天，5 变量），
> 解压即用，不用再自己下载 20 小时。
>
> 🌐 浏览器 demo（无需安装）：https://roblitz-spec.github.io/weather-sculpt/

## 这是什么

Weather-Sculpt 用**真实的 ERA5 再分析场**雕刻出视频、GIF 和声音：
2 m 温度波场、10 m 风场流线、降水雨幕、气压涡旋 + 声化（sonification）彩蛋。
数据源 ECMWF ERA5（CC-BY 4.0），0.25° 网格，逐小时。

## 安装

```bash
pip install numpy xarray zarr matplotlib pillow
# 进入本目录
pip install -e .          # 或直接把本目录加进 PYTHONPATH
```

## 第一张图（10 行）

```python
from weather_sculpt import open_weather, render_video

ds = open_weather("data/era5_global_7d.zarr")     # 全球 7 天
render_video(ds, "temperature_waves", "out.gif", frames=28, fps=3)
```

打开 `out.gif` —— 7 天全球 2 m 温度演变动画。

## 四个预设

```python
from weather_sculpt import open_weather, render_video

ds = open_weather("data/era5_global_7d.zarr")
for p in ["temperature_waves", "wind_streamlines", "rain_curtain", "pressure_vortex"]:
    render_video(ds, p, f"{p}.gif", frames=28, fps=3)
```

| 预设 | 内容 |
|---|---|
| `temperature_waves` | 2 m 温度波场（°C，RdYlBu） |
| `wind_streamlines` | 10 m 风场流线（按风速着色） |
| `rain_curtain` | 降水 6h 滚动累积（mm，log） |
| `pressure_vortex` | 海平面气压等压线 + 相对涡度 |

## 中国 30 天

```python
ds = open_weather("data/era5_china_30d.zarr")     # 73-135E, 18-53N
render_video(ds, "wind_streamlines", "china_wind.gif", frames=60, fps=2)
```

## 声化（音频彩蛋）

```python
from weather_sculpt import sonify
sonify("data/era5_global_7d.zarr", "t2m", "temp.wav", mode="zonal", frames=64)
sonify("data/era5_global_7d.zarr", "tp", "rain.wav", mode="sweep", frames=64)
```

- `zonal`：纬向平均 → 音高，场强 → 响度
- `sweep`：纬度剖面 → 五声音阶琶音

## 数据校验（溯源）

`data/manifest.json` 含两个 zarr 的**目录级 SHA-256 指纹**、时间范围与数据来源署名。
买家可复算校验：

```bash
python scripts/verify_manifest.py     # 逐文件复算并比对 manifest
```

## 文件结构

```
weather-sculpt/
├── weather_sculpt/          # 引擎（MIT）
│   ├── fields.py            #   场读取 + 涡度/散度/归一化
│   ├── presets.py           #   4 个雕刻预设
│   ├── render.py            #   GIF/MP4/PNG 渲染
│   ├── sonify.py            #   声化
│   └── data/era5_sample.zarr#   免费小样本（0.5° 全 5 变量，试跑用）
├── data/
│   ├── era5_global_7d.zarr  #   全球 7 天 × 5 变量 × 0.25°（1.7 GB）
│   ├── era5_china_30d.zarr  #   中国 30 天 × 5 变量（262 MB）
│   └── manifest.json        #   校验和 + 署名
├── examples/                #   可运行示例
├── demo/                    #   展示成品（GIF/WAV）
├── scripts/                 #   下载/打包/校验工具
├── LICENSE.md               #   代码 MIT + 数据 CC-BY 4.0
└── LICENSE_COMMERCIAL.md    #   商业授权（两区域一价）
```

## 授权边界

- **代码**：MIT（随便用）。
- **数据**：ECMWF ERA5，CC-BY 4.0 —— 署名即可。
- **本包**：商业授权见 `LICENSE_COMMERCIAL.md`（全球 7d + 中国 30d，一个价格一份授权，
  含商用 + 再分发权，要求保留署名行）。
