---
type: API
title: SetBatchNum
description: 在不改变Tiling的情况下，重新设置多Batch计算的Batch数。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetBatchNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
---

# SetBatchNum

## 功能说明

在不改变Tiling的情况下，重新设置多Batch计算的Batch数。

## 函数原型

```
__aicore__ inline void SetBatchNum(int32_t batchA, int32_t batchB)
```

## 参数说明

**表1**  参数说明
<a name="table9646134355611"></a>

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| batchA | 输入 | 设置的一次计算的A矩阵Batch数。 |
| batchB | 输入 | 设置的一次计算的B矩阵Batch数。 |

## 返回值说明

无

## 约束说明

-   当开启MixDualMaster（双主模式）场景时，即模板参数[enableMixDualMaster](matmul_config.md#matmulconfig-params)设置为true，不支持使用该接口。
-   本接口仅支持在纯Cube模式（只有矩阵计算）下调用。

## 调用示例

```
//  纯cube模式
#define ASCENDC_CUBE_ONLY
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, AType, false, LayoutMode::NORMAL> aType;
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BType, false, LayoutMode::NORMAL> bType;
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, CType, false, LayoutMode::NORMAL> cType;
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BiasType> biasType;
AscendC::Matmul<aType, bType, cType, biasType> mm1;
mm1.SetTensorA(gm_a, isTransposeAIn);
mm1.SetTensorB(gm_b, isTransposeBIn);
if (tiling.isBias) {
    mm1.SetBias(gm_bias);
}
mm1.SetBatchNum(batchA, batchB);
// 多batch Matmul计算
mm1.IterateBatch(gm_c, false, 0, false);
```


<!-- cannbot:related:start -->
## 相关

- [IterateBatch](iterate_batch.md)（`related`）：在不改变Tiling的情况下，重新设置多Batch计算的Batch数。；调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。；SetBatchNum 调整当前 Matmul 对象的 batchA/batchB，随后 IterateBatch 按该多 Batch 状态一次产出多个 C 矩阵，形成运行期批数设置到批量执行的调用链。
- [SetBatchNum](../matmul_tiling/set_batch_num.md)（`related`）：在不改变Tiling的情况下，重新设置多Batch计算的Batch数。；设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。；Host 侧先把最大 Batch 写入 Tiling，Kernel 侧再在不重做 Tiling 时改当前 batchA/batchB，二者是同一 Matmul 多 Batch 配置在静态上限与运行期覆盖两个阶段的合同。
<!-- cannbot:related:end -->
