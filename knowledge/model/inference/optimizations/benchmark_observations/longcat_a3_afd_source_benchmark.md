---
type: Optimization
title: LongCat A3 AFD与控核的来源性能观测
description: 集中固定 LongCat 文档的核数耗时与整网 benchmark；区分可比较配置、perfect EPLB 和测量环境缺口。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-10-21T09:02:44Z'
updated_at: '2026-10-29T13:46:35Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# LongCat A3 AFD与控核的来源性能观测

## Workload

来源自报的 LongCat-Flash W8A8 Decode；整网表序列长度为 4608，GBS 与 Chips 分行给出，配置叠加 MTP2 与 perfect EPLB。输入/输出长度拆分、请求并发与实际接受率未完整给出。

## Hardware

Atlas A3；Chips 沿用来源的物理卡数标签。算子表核数组合为每个测量点的 Cube/Vector 分配，不作为任意芯片的分核推荐。

## Software

来源固定到上述提交，但没有为这些数字给出完整的实际软件 build、测量脚本和运行日志。安装章节中的示例环境不自动等于 benchmark 环境。

## Metric Definition

TPOT 与 Throughput 沿用源表字段和单位；来源未完整说明计时起止、分母、是否含首 token，以及全部预热/统计处理。不要从标签自行补充计算公式或作为服务端到端指标。

## Repetition and Variance

来源未给 warmup、重复次数、方差/置信区间，也未公开可绑定每行数据的运行记录。本仓没有独立复测，不创建 verified。

## Baseline 与 Variant

[AFD 规则](../rules/afd_attn_ffn_disaggregation.md)维护取舍、拓扑与回退。下面 64 Chips/GBS 256 的两行具有相同的已披露卡数和负载参数，但没有完整配置快照来独立证明只有 AFD 变化；其他行卡数或 GBS 不同。精度风险见[perfect EPLB 边界](../rules/perfect_eplb_profiling_upper_bound.md)。

## Result

| AFD | 量化 | GBS | Seq Length | Chips | TPOT(ms) | Throughput(tokens/p/s) |
| --- | --- | --- | --- | --- | --- | --- |
| N | W8A8 | 512 | 4608 | 64 | 10.37 | 771.46 |
| N | W8A8 | 256 | 4608 | 32 | 10.64 | 751.88 |
| N | W8A8 | 256 | 4608 | 64 | 9.95 | 402.01 |
| Y | W8A8 | 256 | 4608 | 64 | 9.5 | 421.05 |

源优化文档另报告“其他配置相同、整网采集拆解、只改变核数”的算子对比，没有独立测量记录支持进一步因果归因：

| Cube_Vector | MLAProlog(us) | FA(us) | MM(us) | TBMM(us) | QBMM1(us) | QBMM2(us) |
| --- | --- | --- | --- | --- | --- | --- |
| 12C_24V | 68.1 | 118 | 18 | 19.6 | 18.7 | 20.1 |
| 24C_48V | 45.2 | 91.8 | 14.2 | 12.5 | 14.6 | 16.3 |

## Limitations 与验证

这里集中维护旧模型卡和 AFD 规则中的两组数字，不保证新配置可达相同时延。perfect EPLB 的性能配置不能替代真实路由的精度验收。先补实际版本、完整配置、输入、测量脚本和重复记录，再分别核对输出和性能；本次只回源核对文档。Send/Recv 1:1 和历史 KVP 限制见对应规则/机制入口，不从本表推导跨版本支持。

## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md)（supporting）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
