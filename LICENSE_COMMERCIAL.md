# 商业使用授权书 · Commercial License

**Weather-Sculpt「即用完整包」商业授权**

本授权书随 **weather-sculpt「即用完整包」**（下称"本包"）一并提供。购买/获得本包即视为接受本授权。
本包 = 下好并校验过的 **ERA5 完整即用数据集**（全球 0.25° × 7 天逐时 + 中国区域 0.25° × 30 天逐时，
5 变量：2m 气温 / 10m 风 U·V / 降水 / 海平面气压）+ **预调"雕刻"预设** + **渲染与声化工具、文档** + 本商业授权。
**两个区域，一个价格，一份授权。**

## 授权范围（You may）

1. **商业使用**：将本包数据与引擎产出（视频/GIF/图像/音频）用于商业产品、服务、内容创作、
   客户项目、付费课程、艺术品销售等。
2. **再分发**：可随你的产品分发本包数据（须随附本授权书与 ERA5 CC-BY 署名）。
3. **修改**：可修改引擎代码与预设（代码本身 MIT，署名 roblitz）。
4. **无抽成**：基于本包产出的商业收入，无需向 roblitz 分成。

## 署名要求（Attribution）

任何对外发布（产品、视频、论文、社交内容）须包含：

> Weather data: **ECMWF ERA5** (CC-BY 4.0). Engine: **weather-sculpt** (roblitz).

## 不授予（Not granted）

- 不得声称本包数据为 ECMWF/Copernicus 官方发布渠道（官方渠道见 data.ecmwf.int）。
- 不得去除本授权书或 ERA5 署名后分发。

## 代码许可说明

本包中的 `weather_sculpt` 引擎代码本身遵循 **MIT**（署名 roblitz）——MIT 本就允许闭源商用。
本商业授权的价值在于：**下好、接好、调好的完整 ERA5 数据集 + 预调配置 + 商业授权与署名合规 + 支持**，
而不是代码本身的稀缺。

## 数据出处

- 来源仓库：`s3://earthmover-icechunk-era5`（CC-BY 4.0 转码分发，Icechunk V2）
- 原始数据：ECMWF ERA5（Copernicus）
- 校验：本包 `data/manifest.json` 含每数据集 SHA-256 指纹与时间范围，可复核。

---

# Commercial License (English)

By purchasing or receiving this package (the ready-to-run **ERA5 dataset**: global
0.25° × 7 days hourly + China region 0.25° × 30 days hourly, 5 variables — 2 m
temperature, 10 m wind U/V, total precipitation, mean sea level pressure — plus
tuned "sculpt" presets, rendering & sonification tooling, docs, and this license;
**two regions, one price, one license**), you may:

1. **Use commercially**: products, services, content, client work, paid courses,
   art sales — video, GIF, images and audio generated from this package.
2. **Redistribute** the packaged data with your product (keep this license and the
   ERA5 CC-BY attribution).
3. **Modify** the engine and presets (code is MIT, roblitz).
4. **No revenue share** on commercial income derived from this package.

**Attribution required** in any public release:

> Weather data: **ECMWF ERA5** (CC-BY 4.0). Engine: **weather-sculpt** (roblitz).

**Not granted**: presenting this package as an official ECMWF/Copernicus channel;
redistribution with attribution or this license removed.

The `weather_sculpt` engine is **MIT** (roblitz), which already permits closed-source
commercial use. The value here is the **ready, verified, integrated ERA5 dataset +
tuned presets + commercial license/attribution compliance + support** — not the
scarcity of the code.

**Provenance**: source repo `s3://earthmover-icechunk-era5` (CC-BY 4.0 mirror,
Icechunk V2); original data ECMWF ERA5 (Copernicus). `data/manifest.json` carries
SHA-256 fingerprints and time ranges for verification.
