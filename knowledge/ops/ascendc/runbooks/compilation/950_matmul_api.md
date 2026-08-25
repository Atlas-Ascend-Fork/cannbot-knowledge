---
type: "Runbook"
title: "950 Matmul高阶API选型先查内置源"
description: "在 Ascend950 上为反量化+Matmul 融合选 Matmul 高阶 API 的 dtype/TPosition/CubeFormat/执行模式时，先用固定路径读 CANN 内置 weight_quant_batch_matmul_v2 源码确认 950 取值（TSCM/NZ + CFG_MDL + 单核顺序），避免自选 GM/ND half + MIX 致 507015。"
tags: ["task.debugging", "topic.implementation.api_layer.high_level_api", "topic.tiling"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 950 Matmul高阶API选型先查内置源

## 现象

在为自定义算子 BenchNoHarnessWeightQuantBatchMatmul（A16W8 反量化 + Matmul 融合）在 Ascend950PR（DAV_3510 / arch35，CANN 9.1.0，安装路径 cann-9.2.0）上选 Matmul 高阶 API 的 dtype / TPosition / CubeFormat / 执行模式时，自行选择了 MatmulType<TPosition::GM, CubeFormat::ND, half> + KERNEL_TYPE_MIX_AIC_1_1（AIV 反量化 / AIC Matmul / CrossCoreFlag 同步），结果 NPU ST 全部 507015 崩溃。问题不在于某一参数调错，而在于没有先查 CANN 内置同源算子在 950 上实际选了哪组配置，导致在错误的 GM/ND half + MIX 路线里反复调参。

## 适用场景

- 工程形态：Kernel 直调 + aclnn，自定义算子在 950 上需要选 Matmul 高阶 API 的 MatmulType（TPosition / CubeFormat / dtype / isTranspose）、MatmulImpl 配置（CFG_MDL 等）与 kernel 执行模式（KERNEL_TASK_TYPE_DEFAULT 与否 / MIX vs 单核顺序）。
- API 路径：MatmulImpl<...>、REGIST_MATMUL_OBJ、MatmulType<TPosition::*, CubeFormat::*, T, trans>、KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_*)、if ASCEND_IS_AIC/ASCEND_IS_AIV、op.Init()+op.Process()。
- 验证过的平台与 CANN 版本：Ascend950PR / DAV_3510 / arch35；CANN 9.1.0（cann-9.2.0 安装路径）。platforms: [950] 严格对应。
- 适用粒度：operator_family（反量化 + Matmul 融合类，以及任何在 950 上对 Matmul 高阶 API 位置/格式/模式选择拿不准的场景）。
- 路线优先级：recommended_fastpath——动笔写 kernel 前先读内置源确认配置，而非先盲选 GM/ND half + MIX 再调试。
- 不适用或未验证场景：非 950 架构（如 a2/a3）的内置取值不同（custom.h 用 GM/ND、arch35 custom_weight_nz.h 用 GM/ND + GM/NZ 混合且仍 MIX），未验证，不写入 platforms。

## 判别方法

**触发条件**：在 950 上为反量化+Matmul 融合（或任何 Matmul 高阶 API）选 dtype/位置/格式/模式而拿不准，或自选的 GM/ND + MIX 路线已出现 507015。

**可执行探针**（固定路径，CANN 安装目录下的内置算子源码）：

```
BUILTIN_ROOT=/home/g00931184/cann/Ascend/cann-9.2.0/opp/built-in/op_impl/ai_core/tbe/impl/ops_nn/ascendc/weight_quant_batch_matmul_v2

# 1) 确认 950(arch35) 入口 cpp 是否设 KERNEL_TASK_TYPE_DEFAULT、调用哪个 kernel 类
$BUILTIN_ROOT/arch35/weight_quant_batch_matmul_v2.cpp
$BUILTIN_ROOT/weight_quant_batch_matmul_v2.cpp            # 根目录 cpp 的 #if/__NPU_ARCH__==3510 #else 分支

# 2) 确认 950 单核顺序 kernel 的 Matmul 位置/格式/配置
$BUILTIN_ROOT/weight_quant_batch_matmul_v2_weight_nz_performance_base.h
$BUILTIN_ROOT/weight_quant_batch_matmul_v2_weight_nz_performance.h
$BUILTIN_ROOT/weight_quant_batch_matmul_v2_custom_weight_nz.h
```

**原始观测**（逐字取自上述内置源码，CANN cann-9.2.0 安装路径固定 blob 证据）：

`weight_quant_batch_matmul_v2_weight_nz_performance_base.h` 第 97-101 行（950 单核顺序 kernel 的 Matmul 类型定义）：
```cpp
using inputXType = MatmulType<TPosition::TSCM, CubeFormat::NZ, xType, aTrans>;
using inputWType = MatmulType<TPosition::TSCM, CubeFormat::NZ, xType, bTrans>;
using outputYType = MatmulType<TPosition::VECIN, CubeFormat::NZ, yType>;
using inputBiasType = MatmulType<TPosition::VECOUT, CubeFormat::ND, float>;
MatmulImpl<inputXType, inputWType, outputYType, inputBiasType, CFG_MDL> mmObj_;
```

`weight_quant_batch_matmul_v2.cpp` 根目录 cpp 的 3510 分支（第 374-390 行 `#else`）：
```cpp
#else
    if constexpr (BATCH == WQBMMV2_BATCH_ZERO && ...) {
        INVOKE_WEIGHT_QUANT_BMM_OP_NZ_IMPL(WeightQuantBatchMatmulV2WeightNzPerformanceKernel, ...);
    } else if constexpr (BATCH == WQBMMV2_BATCH_ONE && ...) {
        INVOKE_WEIGHT_QUANT_BMM_OP_NZ_IMPL(WeightQuantBatchMatmulV2WeightNzKernel, ...);
    }
#endif
```

`INVOKE_WEIGHT_QUANT_BMM_OP_NZ_IMPL` 宏（同文件第 107-114 行）：
```cpp
#define INVOKE_WEIGHT_QUANT_BMM_OP_NZ_IMPL(templateClass, ...)                                                       \
    do {                                                                                                             \
        GET_TILING_DATA_WITH_STRUCT(WeightQuantBatchMatmulV2NzTilingData, tilingDataIn, tiling);                     \
        templateClass<DTYPE_X, DTYPE_WEIGHT, DTYPE_BIAS, DTYPE_Y, __VA_ARGS__> op;                                   \
        op.Init(x, weight, antiquantScale, antiquantOffset, quantScale, quantOffset, bias, y, userWS, &tilingDataIn, \
                &tPipe);                                                                                             \
        op.Process();                                                                                                \
    } while (0)
```

对照：`weight_quant_batch_matmul_v2_custom.h` 第 70-74 行（**非 3510** 通用分支）：
```cpp
using inputXType = MatmulType<TPosition::GM, CubeFormat::ND, xType, aTrans>;
using inputWType = MatmulType<TPosition::GM, CubeFormat::ND, xType, bTrans>;
using outputYType = MatmulType<TPosition::GM, CubeFormat::ND, yType>;
using inputBiasType = MatmulType<TPosition::GM, CubeFormat::ND, biasType>;
MatmulImpl<inputXType, inputWType, outputYType, inputBiasType, CFG_MDL> mmObj;
```

**解释**：

1. 950（arch35）的 3510 `#else` 分支不设置 `KERNEL_TASK_TYPE_DEFAULT`，直接 `op.Init()`+`op.Process()`，kernel 内部（weight_nz_performance.h）无 `if ASCEND_IS_AIV/AIC` 分支——即 ascend950 默认模式下 AIC 核同时支持 Cube（Matmul）与 Vector（Cast/Mul/DataCopyPad）指令，单核顺序执行反量化+Matmul，不需要 MIX 模式、不需要 CrossCoreFlag 同步。
2. 950 内置的 Matmul 位置/格式是 A/B 用 `TPosition::TSCM`（L1）+ `CubeFormat::NZ`，C 用 `TPosition::VECIN` + NZ，配置 `CFG_MDL`；而非自选的 `TPosition::GM` + `CubeFormat::ND`（GM/ND 是非 3510 的 custom.h 取值）。
3. B 矩阵类型是 `xType`（half/bf16），不是 `int8`——即 weight 先反量化为 xType 再放入 L1，而非把 int8 直接喂给 Matmul。
4. arch35 目录下的 `weight_quant_batch_matmul_v2.cpp`（新版）第 154 行设 `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_MIX_AIC_1_2)`、调用 `custom_weight_nz.h`（A=GM/ND、B=GM/NZ、C=GM/ND，仍 `if ASCEND_IS_AIC` MIX），与根目录 cpp 的 3510 `#else` 分支（单核顺序 + TSCM/NZ）存在版本差异；判别时以与本算子同源的、能跑通的分支为准，不要把 arch35 目录 cpp 的 MIX 取值当作 950 唯一选择。

**结论**：在 950 上做反量化+Matmul 融合，先按内置单核顺序 + TSCM/L1 + NZ + CFG_MDL 选型，再写 kernel；不要从 GM/ND half + MIX 起步。

## 验证信号

- ST 运行自选 GM/ND half + MIX 路线在 950 上返回 ACL error 507015，两用例（M=4,K=16,N=8 与 M=128,K=4096,N=4096）均 FAIL，总计 0 通过 2 失败（来源平台：Ascend950；证据等级: tool_observed）。
- AIC-only 变体 ST 运行同样返回 507015，CPU golden 4/4 PASS（MERE=0, MARE=0），证明崩溃在 NPU kernel 执行阶段而非精度逻辑（来源平台：Ascend950；证据等级: tool_observed）。
- 内置 `weight_nz_performance_base.h` 第 97-101 行：A/B = `MatmulType<TPosition::TSCM, CubeFormat::NZ, xType>`、C = `MatmulType<TPosition::VECIN, CubeFormat::NZ, yType>`、`MatmulImpl<..., CFG_MDL>`（来源平台：Ascend950；证据等级: artifact_verified）。
- 内置根目录 cpp 3510 `#else` 分支（第 374-390 行）+ `INVOKE_WEIGHT_QUANT_BMM_OP_NZ_IMPL` 宏（第 107-114 行）：不设 `KERNEL_TASK_TYPE_DEFAULT`，`op.Init()`+`op.Process()` 单核顺序（来源平台：Ascend950；证据等级: artifact_verified）。
- 内置 arch35 cpp 第 154 行 `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_MIX_AIC_1_2)` 与 `custom_weight_nz.h` 第 70-74/150 行（A=GM/ND、B=GM/NZ、C=GM/ND、`if ASCEND_IS_AIC`）显示版本差异（来源平台：Ascend950；证据等级: artifact_verified）。

> 说明：以上为对 CANN 内置源码的读取观测（artifact_verified），用于判别正确选型。本 trace 内未对按此选型重新实现的 kernel 跑通 ST——即该选型在本算子上能跑通是未验证结论，不得当作 tool_observed 验证信号使用。

## 预防

- 动笔写 kernel 前，先用本卡探针读 CANN 内置同源算子源码，确认本架构下 Matmul 的 TPosition / CubeFormat / 配置 / 执行模式取值，再据此设置自己的 MatmulType 与 KERNEL_TASK_TYPE_DEFAULT。
- 950 上反量化+Matmul 融合，默认选 TSCM/L1 + NZ + CFG_MDL + 单核顺序（不设 `KERNEL_TASK_TYPE_DEFAULT`），把 GM/ND + MIX 当作需要额外证据证明可行的非常规选项。

## 失效边界

- platforms: [950] 只覆盖 Ascend950PR / DAV_3510 / arch35。
- 非 3510 架构（a2 / a3）的内置取值不同（custom.h 用 GM/ND、arch35 custom_weight_nz.h 用 GM/ND + GM/NZ 混合且仍 MIX）；a2/a3 未在本 trace 内验证，未验证，推断可迁移（同 Matmul 高阶 API 语义），不写入 platforms。
- CANN 版本差异：arch35 目录 cpp（新版，MIX_AIC_1_2 + custom_weight_nz.h）与根目录 cpp 的 3510 `#else`（单核顺序 + weight_nz_performance.h）并存；判别时以与本算子同源且能跑通的分支为准，版本升级时需重跑探针。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启纯Cube模式](../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_pure_cube.md)（`related`）：Runbook 的核心选择是 950 上不盲用 MIX、优先同核顺序执行；纯 Cube 指南给出 Matmul 高阶 API 的执行模式配置与适用边界，可核对是否真的需要 Vector/Cube 分核。
- [TSCM输入的矩阵乘](../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md)（`related`）：Runbook 从内置源确认 950 A/B 使用 TSCM+NZ，目标指南说明 TSCM 输入 Matmul 的 L1 驻留、类型配置和数据准备，是该选型的直接实现参考。
<!-- cannbot:related:end -->
