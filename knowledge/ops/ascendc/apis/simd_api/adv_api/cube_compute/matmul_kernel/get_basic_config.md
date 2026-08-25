---
type: API
title: GetBasicConfig
description: 用于配置BasicBlock模板的参数，获取自定义BasicBlock模板。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetBasicConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetBasicConfig

用于配置BasicBlock模板的参数，获取自定义BasicBlock模板。BasicBlock模板的介绍请参考表模板特性。 使用该接口时可以优先考虑使用模板常量化。相比BasicBlock模板仅实现baseM、baseN、baseK常量化，模板常量化可以在此基础上实现singleCoreM、singleCoreN、singleCoreK、baseM、baseN、baseK的常量化，模板常量化的具体使用方式请参考Matmul Tiling常量化。

函数原型：__aicore__ constexpr MatmulConfig GetBasicConfig(const uint32_t basicM, const uint32_t basicN, const uint32_t basicK, const bool intrinsicsLimit = false, const bool batchLoop = false, const BatchMode bmmMode = BatchMode::BATCH_LESS_THAN_L1)

参数：
- basicM（输入）：用于设置参数basicM。 与TCubeTiling结构体中的baseM参数含义相同，Matmul计算时base块M轴长度，以元素为单位。
- basicN（输入）：用于设置参数basicN。 与TCubeTiling结构体中的baseN参数含义相同，Matmul计算时base块N轴长度，以元素为单位。
- basicK（输入）：用于设置参数basicK。 与TCubeTiling结构体中的baseK参数含义相同，Matmul计算时base块K轴长度，以元素为单位。
- intrinsicsLimit（输入）：用于设置参数intrinsicsCheck。 当左矩阵或右矩阵在单核上内轴（即尾轴）大于等于65535（元素个数）时，是否开启循环执行数据从Global Memory到L1 Buffer的搬入。
- batchLoop（输入）：用于设置参数isNBatch。 是否多Batch输入多Batch输出。仅对BatchMatmul有效，开启多Batch后，仅支持Norm模板，且需调用IterateNBatch实现多Batch输入多Batch输出。

返回值：MatmulConfig结构体。

约束：
- 使用本接口时，基本块大小baseM、baseN需满足：singleCoreM能被baseM整除，singleCoreN能被baseN整除。
- 本接口的参数basicM、basicN、basicK应与TCubeTiling结构体的baseM、baseN、baseK设置保持一致。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`related`）：GetMatmulApiTiling 生成 GetBasicConfig 所要求一致的 TCubeTiling；两者共同约束 baseM/baseN/baseK 与单核切分的匹配。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《GetBasicConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetNormalConfig](get_normal_config.md)（`same_topic`）：GetNormalConfig 与《GetBasicConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [MatmulConfig](matmul_config.md)（`same_topic`）：MatmulConfig 定义 GetBasicConfig 返回对象的字段和模板常量化语义，补足 base 参数及调度开关的契约。
<!-- cannbot:related:end -->
