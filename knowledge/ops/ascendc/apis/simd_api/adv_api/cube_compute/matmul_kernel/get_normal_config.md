---
type: API
title: GetNormalConfig
description: 用于配置Norm模板的参数，获取自定义Norm模板。Norm模板的介绍请参考表模板特性。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetNormalConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetNormalConfig

用于配置Norm模板的参数，获取自定义Norm模板。Norm模板的介绍请参考表模板特性。

函数原型：__aicore__ constexpr MatmulConfig GetNormalConfig(const bool intrinsicsLimit = false, const bool batchLoop = false, const bool isVecND2NZ = false, const BatchMode bmmMode = BatchMode::BATCH_LESS_THAN_L1, const bool isMsgReuse = true, const IterateOrder iterateOrder = IterateOrder::UNDEF, const ScheduleType scheduleType = ScheduleType::INNER_PRODUCT, const bool enUnitFlag = true, const bool enableMixDualMaster = false, const BatchOutMode bmmOutMode = BatchOutMode::SINGLE_BATCH)

参数：
- intrinsicsLimit（输入）：用于设置参数intrinsicsCheck。 当左矩阵或右矩阵在单核上内轴（即尾轴）大于等于65535（元素个数）时，是否开启循环执行数据从Global Memory到L1 Buffer的搬入。
- batchLoop（输入）：用于设置参数isNBatch。 是否多Batch输入多Batch输出。仅对BatchMatmul有效，开启多Batch后，仅支持Norm模板，且需调用IterateNBatch实现多Batch输入多Batch输出。
- isVecND2NZ（输入）：用于设置参数enVecND2NZ。 开启通过vector指令进行ND2NZ。开启时需要设置SetLocalWorkspace。参数取值如下：false：不开启通过vector指令进行ND2NZ（默认值）。
- bmmMode（输入）：用于设置参数batchMode。该参数用于BatchMatmul场景。 BatchMatmul场景中Layout类型为NORMAL时，设置BatchMatmul输入A/B矩阵的多batch数据总和与L1 Buffer的大小关系。
- isMsgReuse（输入）：用于设置参数enableReuse。 SetSelfDefineData函数设置的回调函数中的dataPtr是否直接传递计算数据。若未调用SetSelfDefineData设置dataPtr，，该参数仅支持默认值true。

返回值：MatmulConfig结构体。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [AIV核上的ND2NZ格式转换](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/aiv_nd2nz_conversion.md)（`explains`）：GetNormalConfig 与《AIV核上的ND2NZ格式转换》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`related`）：GetNormalConfig 与《GetMatmulApiTiling》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [MatmulTemplateParams](matmul_template_params.md)（`related`）：GetNormalConfig 与《MatmulTemplateParams》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [Matmul使用说明](matmul_usage.md)（`related`）：GetNormalConfig 与《Matmul使用说明》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`related`）：GetNormalConfig 与《REGIST_MATMUL_OBJ》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [SetLocalWorkspace](set_local_workspace.md)（`related`）：GetNormalConfig 与《SetLocalWorkspace》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [SetMatmulConfigParams](../matmul_tiling/set_matmul_config_params.md)（`related`）：GetNormalConfig 与《SetMatmulConfigParams》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetBasicConfig](get_basic_config.md)（`same_topic`）：GetNormalConfig 与《GetBasicConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetIBShareNormConfig](get_ib_share_norm_config.md)（`same_topic`）：GetNormalConfig 与《GetIBShareNormConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetNormalConfig 与《GetMDLConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetMMConfig](get_mm_config.md)（`same_topic`）：GetNormalConfig 与《GetMMConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetSpecialMDLConfig](get_special_mdl_config.md)（`same_topic`）：GetNormalConfig 与《GetSpecialMDLConfig》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：GetNormalConfig 与《IterateNBatch》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [MatmulConfig](matmul_config.md)（`same_topic`）：GetNormalConfig 返回 Matmul 当前 Normal 配置，MatmulConfig 卡定义该配置对象及字段；前者是后者在 Matmul 对象上的读取入口。
<!-- cannbot:related:end -->
