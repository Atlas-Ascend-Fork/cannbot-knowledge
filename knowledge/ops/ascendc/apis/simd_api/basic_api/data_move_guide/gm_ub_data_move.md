---
type: API
title: GmUbDataMove
description: 提供Global Memory与Unified Buffer间数据搬运接口概述，支持连续搬运、高维切分、切片搬运、格式转换及非对齐搬运等场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/GM_UB_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GmUbDataMove

Global Memory 与 Unified Buffer 间数据搬运接口概述。GM→UB 支持 DataCopy（连续/高维切分/切片/ND2NZ/NDDMA 多维搬运）、DataCopyPad（非对齐）。UB→GM 支持 DataCopy（连续/高维切分/切片/NZ2ND）、DataCopyPad。UB→GM 的 CO2→GM 通路仅 Atlas 推理 AI Core 支持。切片搬运和部分随路转换为软仿接口。DataBlock（32B）为基本寻址粒度。

<!-- cannbot:related:start -->
## 相关

- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：GmUbDataMove 与《InitOutput GM 专用，UB 清零用 Duplicate》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [NDDMA 快速路径 C=1 中间轴漏维判别](../../../../runbooks/precision/nddma_c_1.md)（`exemplifies`）：GmUbDataMove 与《NDDMA 快速路径 C=1 中间轴漏维判别》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [NDDMA 最内层 srcStride=0 广播读越界](../../../../runbooks/precision/nddma_srcstride_0.md)（`exemplifies`）：GmUbDataMove 与《NDDMA 最内层 srcStride=0 广播读越界》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [NDDMA多维dstStride致data搬运偏移的判别](../../../../runbooks/precision/nddma_dststride_data.md)（`exemplifies`）：GmUbDataMove 与《NDDMA多维dstStride致data搬运偏移的判别》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../../../../runbooks/compilation/nddma_nddmaconfig_datacopypad.md)（`exemplifies`）：GmUbDataMove 与《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [RANK大于5时NDDMA漏维只解释accum错误](../../../../runbooks/precision/rank_5_nddma_accum_var.md)（`exemplifies`）：GmUbDataMove 与《RANK大于5时NDDMA漏维只解释accum错误》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [AIV核上的ND2NZ格式转换](../../../../guides/operator_practice/best_practices/matmul_tuning_cases/aiv_nd2nz_conversion.md)（`explains`）：GmUbDataMove 与《AIV核上的ND2NZ格式转换》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [NZ2ND](../cube_compute/cube_store_key_features/nz2_nd.md)（`related`）：GmUbDataMove 与《NZ2ND》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [总体约束说明（概述）](overview/overall_constraints.md)（`related`）：GmUbDataMove 与《总体约束说明（概述）》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [数据搬运](../memory_vector_compute/data_move/data_move.md)（`related`）：GmUbDataMove 与《数据搬运》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [数据搬运导览](data_move_guide.md)（`related`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《GmUbDataMove》说明提供Global Memory与Unified Buffer间数据搬运接口概述，支持连续搬运、高维切分、切片搬运、格式转换及非对齐搬运等场景。。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
- [数据搬运概念（概述）](overview/data_move_concept.md)（`related`）：GmUbDataMove 与《数据搬运概念（概述）》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [数据通路（概述）](overview/data_path.md)（`related`）：GmUbDataMove 与《数据通路（概述）》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [概览](overview/overview.md)（`related`）：GmUbDataMove 与《概览》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [矢量数据搬运](../../c_api/vector_data_move/vector_data_move.md)（`related`）：GmUbDataMove 与《矢量数据搬运》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
<!-- cannbot:related:end -->
