---
type: API
title: 接口变更说明（附录）
description: 为了优化API命名，使其更加清晰和易于理解，当前版本相比于CANN8.5.0及前序版本，部分API命名有变更，具体变更情况请参考以下表格：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/interface_change_description.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 接口变更说明（附录）

为了优化API命名，使其更加清晰和易于理解，当前版本相比于CANN8.5.0及前序版本，部分API命名有变更，具体变更情况请参考以下表格：

| 原接口名 | 新接口名 | 备注 |
|---|---|---|
| ScalarGetCountOfValue | [GetBitCount](../simd_api/basic_api/scalar_compute/get_bit_count.md) | 无 |
| ScalarCountLeadingZero | [CountLeadingZero](../simd_api/basic_api/scalar_compute/count_leading_zero.md) | 无 |
| ScalarGetSFFValue | [GetSFFValue](../simd_api/basic_api/scalar_compute/get_sff_value.md) | 无 |
| ScalarCast | [Cast（float转half、int32_t）](../simd_api/basic_api/scalar_compute/cast_float_to_half_int32.md) | 无 |
| ToBfloat16 | [Cast（float转bfloat16_t）](../simd_api/basic_api/scalar_compute/cast_float_to_bfloat16.md) | 无 |
| ToFloat | [Cast（多类型转float）](../simd_api/basic_api/scalar_compute/cast_multi_type_to_float.md) | 其中一个重载版本的返回值类型由 `float` 改为模板 `U`，`U = float`。 |
| FusedMulAddRelu | [MulAddRelu](../simd_api/basic_api/memory_vector_compute/composite_compute/mul_add_relu.md) | 无 |
| CastDeq | [CastDequant](../simd_api/basic_api/memory_vector_compute/composite_compute/cast_dequant.md) | 无 |
| CompareScalar | [Compares](../simd_api/basic_api/memory_vector_compute/compare_and_select/compares.md) | 无 |
| GetAccVal | [GetReduceRepeatSumSpr](../simd_api/basic_api/memory_vector_compute/reduction_compute_aux_config/get_reduce_repeat_sum_spr_isasi.md) | 无 |
| GetReduceMaxMinCount | [GetReduceRepeatMaxMinSpr](../simd_api/basic_api/memory_vector_compute/reduction_compute_aux_config/get_reduce_repeat_max_min_spr_isasi.md) | 无 |
| SetAtomicNone | [DisableDmaAtomic](../simd_api/basic_api/atomic_operations/disable_dma_atomic.md) | 无 |
| InitConstValue | [Fill](../simd_api/basic_api/cube_compute/cube_load_aux_config/fill.md) | 无 |
| SetMMLayoutTransform | [SetMMRowMajor / SetMMColumnMajor](../simd_api/basic_api/cube_compute/mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md) | `SetMMLayoutTransform(true)` 对应 `SetMMRowMajor()`；`SetMMLayoutTransform(false)` 对应 `SetMMColumnMajor()`。 |
| SetHF32Mode | [SetHF32Mode](../simd_api/basic_api/cube_compute/mmad_compute_aux_config/set_hf32_mode.md) | 接口名不变，参数类型由 `bool` 修改为枚举 `HF32Mode`。 |
| SetHF32TransMode | [SetHF32TransMode](../simd_api/basic_api/cube_compute/mmad_compute_aux_config/set_hf32_trans_mode.md) | 接口名不变，参数类型由 `bool` 修改为枚举 `HF32TransMode`。 |
| CalcTschBlockDim | [CalcTschNumBlocks](../utils_api/platform_info/platform_ascend_c/calc_tsch_num_blocks.md) | 无 |

以下接口于 9.1.0 修改，相比于 CANN 9.0.0 及前序版本，命名和参数约定有如下变更：

| 原接口名 | 新接口名 | 备注 |
|---|---|---|
| BlockReduceSum / BlockReduceMax / BlockReduceMin | [ReduceDataBlock](../simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_data_block.md) | 通过模板参数区分 DataBlock 归约操作，并调整 `mask` 与 `repeatTime` 的参数顺序。 |
| WholeReduceSum / WholeReduceMax / WholeReduceMin | [ReduceRepeat](../simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_repeat.md) | 通过模板参数区分 Repeat 归约操作。 |
| RepeatReduceSum | [ReduceRepeat](../simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_repeat.md) | 通过模板参数区分操作，调整 `mask` 与 `repeatTime` 的参数顺序，并删除无效参数 `dstBlkStride`。 |
| PairReduceSum | [ReducePairElem](../simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_pair_elem.md) | 通过模板参数区分 Pair 元素归约操作，并调整 `mask` 与 `repeatTime` 的参数顺序。 |
