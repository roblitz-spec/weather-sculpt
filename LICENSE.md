# 许可与署名 · License & Attribution

## 代码 · Code

**MIT License**（署名 roblitz）

Copyright (c) 2026 roblitz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 数据 · Data

本包（pip 免费层 / 浏览器 demo 内嵌样本）包含 **ECMWF ERA5** 再分析数据的子集。
ERA5 遵循 **CC-BY 4.0**，使用与分发须保留以下署名：

> **ERA5 single-level data. Source: ECMWF.**
> Reference: Hersbach, H., Samuelevics, K., Burrows, W., et al. (2023):
> *ERA5: Fifth generation of ECMWF atmospheric reanalyses of the global
> climate*, ECMWF Copernicus Atmosphere Data Store / ECMWF Technical
> Memoranda. DOI: 10.24381/c010a562
>
> 数据获取自公开开放仓库 s3://earthmover-icechunk-era5（CC-BY 4.0 转码分发）。

任何再分发（包括本 pip 包内嵌的样本场）必须随附本署名。

## 边界 · Boundary

- pip 包 / GitHub 仓库 / 浏览器 demo = **免费层**（MIT 代码 + CC-BY 样本数据，
  研究/演示/学习用途，商用需遵循 CC-BY 署名且自行承担数据获取成本）。
- 完整即用数据集（全球 7 天 + 中国 30 天、下好校验过的 zarr、预调预设、商用授权）
  见 **Ready-to-Run 完整包**，其商业使用条款见 `LICENSE_COMMERCIAL.md`。

---

# License & Attribution (English)

**Code**: MIT (roblitz) — see above.

**Data**: ERA5 subsets are **CC-BY 4.0** (ECMWF). All redistribution must keep
the attribution block above. Free tier = pip package + GitHub + browser demo
(research / demo / learning; commercial use subject to CC-BY attribution and
your own data-acquisition responsibility). The ready-to-run full dataset with
commercial license is described in `LICENSE_COMMERCIAL.md`.
