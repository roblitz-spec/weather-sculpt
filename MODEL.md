# MODEL · 数据源与方法

## 数据：ECMWF ERA5 单层级（地表）场

- **产品**：ERA5 single-level（surface）
- **变量**（5 个）：
  | 键 | 量 | 单位 |
  |---|---|---|
  | `t2m` | 2 米气温 | K |
  | `u10` / `v10` | 10 米风 U / V 分量 | m s⁻¹ |
  | `tp` | 总降水（1 小时） | m |
  | `msl` | 海平面气压 | Pa |
- **网格**：0.25° 规则经纬网格，全球 721 × 1440（lat 90…-90，lon 0…359.75）
- **时间**：逐小时；时间索引 = `hours since 1940-01-01 00:00`（proleptic_gregorian）
- **许可**：CC-BY 4.0（ECMWF），引用见 `LICENSE.md`

## 本包数据集

| 数据集 | 范围 | 时次 |
|---|---|---|
| `era5_global_7d.zarr` | 全球 0.25° | 168（7 天逐时） |
| `era5_china_30d.zarr` | 73–135°E, 18–53°N（141×249） | 720（30 天逐时） |

- 格式：zarr v3，float32，zstd 压缩；`manifest.json` 提供 SHA-256 与时间范围。
- 缺失值：NaN（`_FillValue`）。
- 获取通道：`s3://earthmover-icechunk-era5`（Icechunk V2，匿名，CC-BY 4.0 转码分发）。

## 引擎方法（`weather_sculpt`）

- **场操作**（`fields.py`）：
  - 相对涡度 ζ = ∂v/∂x − ∂u/∂y，x 向间距按 cos(φ) 缩放（球面近似）；
  - 散度 ∂u/∂x + ∂v/∂y；
  - `normalize`：百分位截断（默认 1–99）→ [0,1]，保证色标稳定。
- **预设**（`presets.py`）：
  | 预设 | 输入 | 画面 |
  |---|---|---|
  | `temperature_waves` | t2m | 温度波场（RdYlBu_r 标量场） |
  | `wind_streamlines` | u10, v10 | 流线（streamplot，按风速着色，降采样绘制） |
  | `rain_curtain` | tp | 6 小时滚动累积雨幕（log 尺度，Wistia） |
  | `pressure_vortex` | msl, u10, v10 | 相对涡度着色 + 等压线 |
- **渲染**（`render.py`）：matplotlib (Agg) → PNG 序列 → GIF（Pillow）或 MP4（ffmpeg，缺省回退 GIF）。
- **声化**（`sonify.py`）：
  - `zonal`：纬向均值 → 音高（110–880 Hz），空间离散度 → 响度；
  - `sweep`：纬向剖面切 12 带 → 五声音阶和弦，随时间演变为"天气和声"。
  - 纯 numpy 加法合成，16-bit PCM WAV。

## 已知限制

- ERA5 有约 5 天产品延迟（以 `manifest.json` 时间范围为准）。
- 0.25° 分辨率下小尺度对流系统为再分析估计值，非观测。
- 涡度/散度为网格微分近似，边界处精度下降。
- 全球窗口与时间范围固定于构建日；需要其他范围请用 `scripts/download_era5.py` 重取（匿名通道，免费）。
