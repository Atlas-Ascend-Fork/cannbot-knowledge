---
type: Optimization
title: PyPTO V4 单 die 算子数据与 VF 观测（平台待核验）
description: PyPTO V4 单 die 算子数据与 VF 观测（平台待核验）；按固定来源保留条件、差异和待验证边界，不提供通用性能保证。
tags:
- task.testing
- topic.performance.analysis
status: draft
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_pypto_operator_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto/README.md
  role: supporting
created_at: '2026-10-22T01:37:01Z'
updated_at: '2026-10-29T14:38:30Z'
platforms: []
---

# PyPTO V4 单 die 算子数据与 VF 观测（平台待核验）

## Workload

固定指南的单 die、B=64、MTP1、序列 8K；各行按原表 B/S1/S2/D/压缩参数分别读取。

## Hardware

来源说明兼容多代硬件，但未把测量行绑定到具体型号。保持 draft、空平台，不把框架兼容性当作测量平台。

## Software

固定来源版本见 Evidence；未与各行数据绑定的软件 build 不自行补齐。

## Baseline 与 Variant

Duration 表没有未优化对照；hc_post VF 对照未使能 VF，但未给完整 shape/计时资料。

## Metric Definition

沿用源表单位；算子、非 Hcom Kernel 总和与端到端耗时分别报告，不混用。

## Repetition and Variance

来源未给足够逐轮样本、warmup、重复次数、方差或置信区间；没有本仓独立复测。

## Result

| 算子 | 代码行数(KLOC) | B | S1 | S2 | D | cmp_ratio | coff | start pos | Duration(us) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sliding_window_attention | 0.3 | 64 | 2 | 8192 | 512 | N/A | N/A | N/A | 65 |
| compressed_flash_attention | 0.2 | 64 | 2 | 8192 | 512 | 128 | N/A | N/A | 90 |
| sparse_compressed_flash_attention | 0.2 | 64 | 2 | 8192 | 512 | 4 | N/A | N/A | 160 |
| compressor_c4li | 0.9 | 64 | 2 | N/A | 128 | 4 | 2 | 8192 | 55 |
| compressor_c4a | 0.9（源表跨行） | 64 | 2 | N/A | 512 | 4 | 2 | 8192 | 80 |
| compressor_c128a | 0.9（源表跨行） | 64 | 2 | N/A | 512 | 128 | 1 | 8192 | 55 |
| compressor_c4li | 0.9（源表跨行） | 64 | 2 | N/A | 128 | 4 | 2 | 8191 | 75 |
| compressor_c4a | 0.9（源表跨行） | 64 | 2 | N/A | 512 | 4 | 2 | 8191 | 95 |
| compressor_c128a | 0.9（源表跨行） | 64 | 2 | N/A | 512 | 128 | 1 | 8191 | 125 |
| mla_prolog | 0.5 | 64 | 2 | N/A | N/A | N/A | N/A | N/A | 130 |
| hc_pre | 0.4 | 64 | 2 | N/A | N/A | N/A | N/A | N/A | 70 |
| lightning_indexer_prolog | 0.3 | 64 | 2 | N/A | N/A | N/A | N/A | N/A | 101 |

### 独立的 hc_post VF 披露

同一指南另报告已做其他优化后的 Vector Fusion 相对提升 22.7%；缺完整 shape、绝对时延和独立复测，不能和上述 Duration 表拼成同一次实验。

## Limitations 与验证

不推导所有 A2/A3/950 的算子耗时；没有硬件绑定时不补平台或 Scope。转稳定前需定位原始测量环境、输入、命令和计时记录。

本卡记录来源自报，不是普遍性能保证，不新增 verified。

## Evidence

- [deepseek_v4_pypto_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_pypto_operator_guide.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md)（supporting）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto/README.md)（supporting）

## 本轮来源核对与剩余缺口

V4 模型 README 声明 A3 Pod 与 950PR/DT 两类部署；V4 PyPTO 指南只在表前写单 die、64 batch、MTP1、8K，没有具体卡型。相同仓库的 `ops/pypto/README.md` 仍介绍 V3.2 的 A3 三算子库，不能将其支持范围移植为 V4 测量平台。

已核对模型与算子两层来源，仍缺这些 V4 行及独立 22.7% VF 披露的测量硬件、完整输入/环境与原始记录。保留 draft，不把“新代际”措辞解释成 950 实测。
