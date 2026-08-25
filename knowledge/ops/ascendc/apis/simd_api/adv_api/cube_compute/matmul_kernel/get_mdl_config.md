---
type: API
title: GetMDLConfig
description: 用于配置MDL模板的参数，获取自定义MDL模板。MDL模板的介绍请参考表模板特性。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetMDLConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetMDLConfig

用于配置MDL模板的参数，获取自定义MDL模板。MDL模板的介绍请参考表模板特性。

函数原型：__aicore__ constexpr MatmulConfig GetMDLConfig(const bool intrinsicsLimit = false, const bool batchLoop = false, const uint32_t doMTE2Preload = 0, const bool isVecND2NZ = false, bool isPerTensor = false, bool hasAntiQuantOffset = false, const bool enUnitFlag = false, const bool isMsgReuse = true, const bool enableUBReuse = true, const bool enableL1CacheUB = false, const bool enableMixDualMaster = false, const bool enableKdimReorderLoad = false)

参数：
- intrinsicsLimit（输入）：用于设置参数intrinsicsCheck。 当左矩阵或右矩阵在单核上内轴（即尾轴）大于等于65535（元素个数）时，是否开启循环执行数据从Global Memory到L1 Buffer的搬入。
- batchLoop（输入）：用于设置参数isNBatch。 是否多Batch输入多Batch输出。仅对BatchMatmul有效，开启多Batch后，仅支持Norm模板，且需调用IterateNBatch实现多Batch输入多Batch输出。
- doMTE2Preload（输入）：用于设置参数doMTE2Preload。 在MTE2流水间隙较大，且M/N数值较大时可通过该参数开启对应M/N方向的预加载功能，开启后能减小MTE2间隙，提升性能。预加载功能仅在MDL模板有效（不支持SpecialMDL模板）。
- isVecND2NZ（输入）：用于设置参数enVecND2NZ。 开启通过vector指令进行ND2NZ。开启时需要设置SetLocalWorkspace。参数取值如下：false：不开启通过vector指令进行ND2NZ（默认值）。
- isPerTensor（输入）：用于设置参数isPerTensor。 A矩阵half类型输入且B矩阵int8_t类型输入场景，开启B矩阵量化时是否为per tensor。/true：per tensor量化。/false：per channel量化。

返回值：MatmulConfig结构体。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启MDL模板](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md)（`explains`）：指南给出 MDL 适用于 MTE2 搬运次数多的大 shape，并通过 preload/L1 复用减少流水空隙；GetMDLConfig 提供 `doMTE2Preload`、L1/UB 复用等 MDL 专用参数和返回 MatmulConfig 的调用入口，是该优化机制的可执行配置衔接。
- [GetBasicConfig](get_basic_config.md)（`same_topic`）：GetMDLConfig 与《GetBasicConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetIBShareNormConfig](get_ib_share_norm_config.md)（`same_topic`）：GetMDLConfig 与《GetIBShareNormConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetMMConfig](get_mm_config.md)（`same_topic`）：GetMDLConfig 与《GetMMConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`same_topic`）：GetMDLConfig 与《GetMatmulApiTiling》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetNormalConfig](get_normal_config.md)（`same_topic`）：GetNormalConfig 与《GetMDLConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetSpecialMDLConfig](get_special_mdl_config.md)（`same_topic`）：GetMDLConfig 与《GetSpecialMDLConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：GetMDLConfig 与《IterateNBatch》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [MatmulConfig](matmul_config.md)（`same_topic`）：GetMDLConfig 与《MatmulConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [MatmulTemplateParams](matmul_template_params.md)（`same_topic`）：GetMDLConfig 与《MatmulTemplateParams》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [SetLocalWorkspace](set_local_workspace.md)（`same_topic`）：GetMDLConfig 与《SetLocalWorkspace》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [SetMatmulConfigParams](../matmul_tiling/set_matmul_config_params.md)（`same_topic`）：GetMDLConfig 与《SetMatmulConfigParams》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
<!-- cannbot:related:end -->
