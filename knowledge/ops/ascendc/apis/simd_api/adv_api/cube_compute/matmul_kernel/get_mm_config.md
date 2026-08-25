---
type: API
title: GetMMConfig
description: 灵活的自定义Matmul模板参数配置，通过设置MatmulConfigMode及可变参数获取自定义的MatmulConfig。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetMMConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetMMConfig

灵活的自定义Matmul模板参数配置。通过设置[MatmulConfigMode](#table17837129144319)、[MatmulShapeParams](#table16317184295116)、[MatmulQuantParams](#table8313111211573)、[MatmulBatchParams](#table15129204644)、[MatmulFuncParams](#table66217141862)，获取自定义的MatmulConfig。 MatmulConfigMode 指定待修改的模板，随后可按任意顺序传入一个或多个 Shape、Quant、Batch 或 Func 参数。

函数原型：
template <MatmulConfigMode configMode, typename... ArgTypes>
__aicore__ inline constexpr MatmulConfig GetMMConfig(ArgTypes&&... args)

参数：
- configMode：获取的MatmulConfig模板。
- ArgTypes：可变模板参数。
- args（输入）：可变参数，任意顺序传入需要设置的MatmulShapeParams、MatmulQuantParams、MatmulBatchParams、MatmulFuncParams中的一个或多个。
- 参数：说明
- CONFIG_NORM：表示设置MatmulConfig默认值为Norm模板
返回值：MatmulConfig结构体。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [MatmulTemplateParams](matmul_template_params.md)（`related`）：GetMMConfig 生成可作为 MatmulTemplateParams 中 MatmulConfig 实参的自定义配置，连接配置选择与对象实例化。
- [SetMatmulConfigParams](../matmul_tiling/set_matmul_config_params.md)（`related`）：Host 侧设置的模板、调度与遍历参数必须与 Kernel 的 MatmulConfig 一致，连接 GetMMConfig 的设备配置和 tiling 生成。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《GetMMConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetNormalConfig](get_normal_config.md)（`same_topic`）：GetNormalConfig 与《GetMMConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [MatmulConfig](matmul_config.md)（`same_topic`）：GetMMConfig 返回的正是 MatmulConfig；该卡定义预置模板及字段，是解释工厂函数结果不可缺的对象契约。
<!-- cannbot:related:end -->
