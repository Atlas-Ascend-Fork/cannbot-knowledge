---
type: API
title: DataCopy（L0C Buffer到UB数据搬运）
description: 对数据搬运能力进行增强，相比于基础数据搬运接口，增加了L0C Buffer-\>Unified Buffer（UB）通路的随路计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DataCopy（L0C Buffer到UB数据搬运）

对 L0C Buffer→Unified Buffer（CO1→CO2）通路的数据搬运进行增强，增加随路反量化和 ReLU 计算。仅 Atlas 推理系列产品 AI Core 支持增强搬运功能，其他型号接口可调用但功能等同基础搬运。

参数：dst、src 为 LocalTensor；intriParams 为 DataCopyParams；enhancedParams 为 DataCopyEnhancedParams。关键字段：blockMode（BLOCK_MODE_MATRIX 为 16×16 分形 / BLOCK_MODE_VECTOR 为 1×16 分形）、deqScale（DEQ/DEQ8/DEQ16/VDEQ/VDEQ8/VDEQ16 量化模式）、deqValue（量化系数，含 M/N/MCB/Offset/Sign/ReLU 标志位）、deqTensorAddr（VDEQ 系列反量化参数向量地址，32 字节对齐）、sidStoreMode（DEQ8/VDEQ8 存储模式 0/1/2）、isRelu(bool)。

blockMode 与数据类型决定 blockLen/srcStride/dstStride 单位：MATRIX 模式 half/int16 为 512B、float/int32 为 1024B；VECTOR 模式 half/int16 为 32B、float/int32 为 64B。仅 Atlas 推理 AI Core 支持增强功能。

<!-- cannbot:related:start -->
## 相关

- [Copy](../../cube_compute_tensor_api/cube_compute_store/copy_l0_c_to_ub.md)（`related`）：DataCopy（L0C Buffer到UB数据搬运） 与《Copy》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
- [L0C Buffer内存结构介绍](l0_c_memory_structure_intro.md)（`related`）：DataCopy（L0C Buffer到UB数据搬运） 与《L0C Buffer内存结构介绍》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
- [L1OrL0CUbDataMove](../../data_move_guide/l1_or_l0_c_ub_data_move.md)（`related`）：DataCopy（L0C Buffer到UB数据搬运） 与《L1OrL0CUbDataMove》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
- [FixpipeL0CToUB](fixpipe_l0_c_to_ub.md)（`same_topic`）：FixpipeL0CToUB 与《DataCopy（L0C Buffer到UB数据搬运）》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [L0C Buffer到UB双目标模式](../cube_store_key_features/l0_c_to_ub_dual_target_mode.md)（`same_topic`）：DataCopy（L0C Buffer到UB数据搬运） 与《L0C Buffer到UB双目标模式》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
<!-- cannbot:related:end -->
