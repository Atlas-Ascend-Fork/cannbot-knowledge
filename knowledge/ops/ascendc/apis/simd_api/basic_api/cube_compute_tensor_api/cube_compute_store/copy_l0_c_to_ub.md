---
type: API
title: Copy
description: 将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_store/Copy_L0CToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# Copy（L0C到UB数据搬运）

通过统一Copy接口将L0C Buffer数据搬运到Unified Buffer，用于矩阵计算结果在Vector侧进一步处理。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

支持场景：连续数据搬出、随路格式转换、双目的搬出（L0CToUBDualDst，同时搬出到两个UB地址）。函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [BatchCopy](../cube_store_key_features/batch_copy.md)（`related`）：当目的在 UB 时，BatchCopy 对应 L0C→UB Copy 的批量外层循环，复用该搬出路径的格式和对齐合同。
- [Copy](copy_l0_c_to_gm.md)（`related`）：《Copy》明确“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。”；它与《Copy》的“将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopy（L0C Buffer到UB数据搬运）](../../cube_compute/cube_compute_store/data_copy_l0_c_to_ub.md)（`related`）：DataCopy（L0C Buffer到UB数据搬运） 与《Copy》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
- [FixpipeL0CToUB](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_ub.md)（`related`）：FixpipeL0CToUB 与《Copy》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [L0C Buffer到Unified Buffer双目标模式](../cube_store_key_features/l0c_to_ub_dual_dst.md)（`related`）：The tensor Copy call is the concrete L0C-to-UB transfer that can enable the dual-destination mode described by the focal page.
- [UnitFlag](../mmad_compute_key_features/unit_flag.md)（`related`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Copy》提供“将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [L1OrL0CUbDataMove](../../data_move_guide/l1_or_l0_c_ub_data_move.md)（`same_topic`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《Copy》说明将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [矩阵计算的搬出](cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》明确“矩阵计算 TensorAPI 搬出接口集，涵盖 L0C 到 GM、L0C 到 UB 的 Copy 接口及 L0C Buffer 内存结构。”；它与《Copy》的“将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
