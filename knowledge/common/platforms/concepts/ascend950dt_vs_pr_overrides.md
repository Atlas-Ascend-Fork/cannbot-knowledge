---
type: Concept
title: "Ascend950DT vs 950PR 差异与 SKU 表"
description: "950DT 相对 950PR 的全部差异字段：片上高速内存容量/带宽（headline）、AI 子系统 SKU 核数、分格式算力（MXFP4/FP8/BF16/TF32/INT）、L2、AI CPU；SKU 必须按设备实证不可按型号推。"
tags: [task.lookup, topic.architecture, topic.memory]
status: draft
sources:
- resource: https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf
  role: primary
created_at: "2026-09-22T04:15:00Z"
updated_at: "2026-10-16T00:00:00Z"
platforms: ["950"]
aliases: [hw/ascend950dt-overrides]
---

> **来源说明（2026-10-16）**：本卡 SPEC 差异表已指向官方公开白皮书（见 sources，可直接复核）；「设备级回读」与「闭合枚举」两节为车队私有实测/配置枚举，无公开复核途径，按社区评审要求整卡暂维持 draft，待该部分补可复核来源后回升。

# 950DT ↔ 950PR 差异（只列不同字段；共架构部分见各专项卡）

> **[SPEC 引用说明]** 本卡中 `[SPEC pN §x 图y]` 标注指向[《昇腾 950 NPU 架构白皮书》官方公开版](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)（SHA-256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`；页码按 PDF 文件页序、从 1 开始）。该标注表示该字段属"厂商主张"证据层（非实测、非承诺）；可实测核对的内容以各卡 `[MEASURED]` 标注与正文数据为准。


证据标注约定见 [主卡](target_ascend950dt.md)。

## 片上高速内存（headline 差异）

| 字段 | 950DT | 950PR（对照） | 来源 |
|---|---|---|---|
| 片上内存容量 | **Up to 144 GB（SKU 档 96 GB）** | Up to 128 GB（SKU 档 112 GB） | [SPEC p13 表3-1; p25 表4-2] |
| 片上内存带宽 | **4 TB/s** | 1.6 TB/s（SKU 档 1.4 TB/s） | [SPEC p13 表3-1; p26 §4.3.1] |
| 片上内存模块数/片 | **4** | 8 | [SPEC p12 §3 架构示意图说明] |
| 产品定位 | 全生命周期 LLM 训练 + 复杂推理（"突破内存墙瓶颈"） | 高性能推荐 + Prefill（"极致吞吐与低延迟"） | [SPEC p8 §2 引言] |

两侧的高速内存 RAS 相同：Online ECC、巡检刷写弱行重写/隔离、备用行动态 failover [SPEC p26 §4.3.1]。

## AI 子系统 SKU 配置

整片 36 个 AI 子系统（每子系统 1 Cube Core + 2 Vector Core）[SPEC p13]，SKU 从满配熔断：

| 字段 | 950DT SKU | 950PR SKU | 来源 |
|---|---|---|---|
| Cube Core 数 | **36 / 32 / 28** | 32 / 28 | [SPEC p13 表3-1] |
| Vector Core 数 | **72 / 64 / 56** | 64 / 56 | [SPEC p13 表3-1] |

⚠️ **任何具体主机的 SKU 是按设备实证，不是按型号假设。** 不要把 "950DT" 读成 "36/72"：用每 SKU 数字前先查实际熔断配置。

### 设备级回读（本节取代先前未绑定的 SKU 判定）

**唯一正确的取值机制：读该 SKU 自己的 `platform_config` ini，键用 run 绑定的完整 `soc_version`，不要硬编码核数。**

`Ascend950DT_9582`，CANN 9.1.0，2026-09-27 容器内实测 [MEASURED]：

| 字段 | 值 |
|---|---|
| `ai_core_cnt` | 32 |
| `cube_core_cnt` | 32 |
| `vector_core_cnt` | 64 |
| `l1_size` | 524288（512 KB） |
| `l2_size` | 134217728（128 MB） |
| `ub_size` | 253952（248 KB） |

来源 `/usr/local/Ascend/cann-9.1.0/aarch64-linux/data/platform_config/Ascend950DT_9582.ini`，
sha256 `43883e3c7224b940bbc04bd7289f78ce01fa5500916d3656ae8ae84910a41e3b`。

⇒ **该主机是 32 子系统档 SKU**（上表中间列）。`vector_core_cnt` 64 = 2 x `cube_core_cnt` 32，
与本卡「每子系统 1 Cube Core + 2 Vector Core」的 SPEC 断言在**设备级独立吻合**；`l2_size`
128 MB 亦与本卡 SPEC 来源的 L2 值吻合。两个字段的 SPEC 与设备交叉验证同时成立。

⛔ **不要用 `Short_SoC_version` 当键。** 该 ini 里它是 `Ascend950`——family 级、各 SKU 相同，
按它取值必然丢掉 SKU 差异。键必须是完整 `SoC_version`（此处 `Ascend950DT_9582`）。

**闭合枚举（CANN 9.1.0 实测）**：`data/platform_config` 下共 **68** 个 `.ini`，其中 950 族
**34** 个 = **25 个 `Ascend950DT_*` + 9 个 `Ascend950PR_*`**。34/34 全部同时带 `ai_core_cnt`
与 `ub_size`，所以这两个字段可以无条件按 `soc_version` 取到，**不需要 fallback 分支**。
注意 34 是 950 族的计数，不是 `platform_config` 的总数（68）——把 34 当成总数会在别的
平台族上静默取空。`ub_size=253952` 在该 ini 中出现两次且值相同，故「取首个匹配」与
「取末个匹配」在此恰好一致，但消费者不应依赖这一点。

## 分格式算力（Cube+Vector 合计）[SPEC p13 表3-1]

| 格式 | 950DT（36/32/28 核） | 950PR（32/28 核） |
|---|---|---|
| MXFP4 | 2007 / 1784 / 1561 | 1784 / 1561 |
| HiF8/MXFP8/FP8 | 1034 / 919 / 804 | 919 / 804 |
| INT8 | 1034 / 919 / 804 | 919 / 804 |
| BF16/FP16 | 547 / 486 / 425 | 486 / 425 |
| TF32 | 273 / 243 / 212 | 243 / 212 |

Cube-only [SPEC p13–14]：MXFP4 1946/1730/1513；FP8 973/865/756；BF16/FP16 486/432/378；TF32 243/216/189。
Vector-only [SPEC p14]：FP16/BF16 60/54/47；FP32 30/27/23；INT8 60/54/47；INT16 30/27/23；INT32 15/13/11；INT64 7/6/5。

## L2 Cache 与 AI CPU

| 字段 | 950DT | 950PR | 来源 |
|---|---|---|---|
| L2 Cache | **128 MB** | 128 MB（SKU 档 112 MB） | [SPEC p15 表3-1; p25 表4-2] |
| AI CPU | Linx816, 8C16T / 6C12T | Linx816, 8C16T / 6C12T / 4C8T | [SPEC p14 表3-1] |

实测对照见 [950DT 实测观测](ascend950dt_measured_observations.md)；PR 侧全量规格见 [950PR 平台卡](target_ascend950pr.md)。
