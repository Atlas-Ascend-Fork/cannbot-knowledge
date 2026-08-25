---
type: API
title: GetSpecialMDLConfig
description: 用于配置SpecialMDL模板的参数，获取自定义SpecialMDL模板。SpecialMDL模板的介绍请参考表模板特性。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetSpecialMDLConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetSpecialMDLConfig

用于配置SpecialMDL模板的参数，获取自定义SpecialMDL模板。SpecialMDL模板的介绍请参考表模板特性。

函数原型：__aicore__ constexpr MatmulConfig GetSpecialMDLConfig(const bool intrinsicsLimit = false, const bool batchLoop = false, const uint32_t doMTE2Preload = 0, const bool isVecND2NZ = false, bool isPerTensor = false, bool hasAntiQuantOffset = false)

参数：
- intrinsicsLimit（输入）：用于设置参数intrinsicsCheck。 当左矩阵或右矩阵在单核上内轴（即尾轴）大于等于65535（元素个数）时，是否开启循环执行数据从Global Memory到L1 Buffer的搬入。
- batchLoop（输入）：用于设置参数isNBatch。 是否多Batch输入多Batch输出。仅对BatchMatmul有效，开启多Batch后，仅支持Norm模板，且需调用IterateNBatch实现多Batch输入多Batch输出。
- doMTE2Preload（输入）：用于设置参数doMTE2Preload。 在MTE2流水间隙较大，且M/N数值较大时可通过该参数开启对应M/N方向的预加载功能，开启后能减小MTE2间隙，提升性能。预加载功能仅在MDL模板有效（不支持SpecialMDL模板）。
- isVecND2NZ（输入）：预留参数，保持默认值false即可。
- isPerTensor（输入）：用于设置参数isPerTensor。 A矩阵half类型输入且B矩阵int8_t类型输入场景，开启B矩阵量化时是否为per tensor。/true：per tensor量化。/false：per channel量化。

返回值：MatmulConfig结构体。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`related`）：GetMatmulApiTiling 与《GetSpecialMDLConfig》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [SetMatmulConfigParams](../matmul_tiling/set_matmul_config_params.md)（`related`）：Host tiling 的 MatmulConfig 参数必须与 Kernel 侧 SpecialMDL 配置保持一致，连接模板选择与 tiling 生成。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《GetSpecialMDLConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetNormalConfig](get_normal_config.md)（`same_topic`）：GetNormalConfig 与《GetSpecialMDLConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [MatmulConfig](matmul_config.md)（`same_topic`）：GetSpecialMDLConfig 返回 MatmulConfig，该对象定义 intrinsicsCheck、batch、预加载与量化等字段的统一配置语义。
<!-- cannbot:related:end -->
