---
type: API
title: MatmulConfig
description: 模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。MatmulConfig的参数说明见表2。MatmulConfig的定义方式有：
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/MatmulConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# MatmulConfig

模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。MatmulConfig的参数说明见表2。MatmulConfig的定义方式有： - 该模板参数可选取提供的模板之一，当前提供的MatmulConfig模板取值范围为【CFG_NORM、CFG_MDL、CFG_IBSHARE_NORM、MM_CFG_BB】，分别对应默认的Norm、MDL、IBShare、BasicBlock模板。各模板的介绍请参考表1。 - 该模板参数可以基于各类获取模板的接口，自定义模板参数配置，获取自定义模板。

<!-- cannbot:related:start -->
## 相关

- [AIC和AIV独立运行机制](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/aic_aiv_independent_execution.md)（`explains`）：双主模式由 MatmulConfig::enableMixDualMaster 开启，配置必须在同一算子所有 Matmul 对象间一致。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《MatmulConfig》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [Matmul高阶API开启MDL模板](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md)（`explains`）：指南解释大 shape、MTE2 循环搬运占比高时为何选择 MDL，并给出通过 L1 缓存多个基本块减少搬运的机制；MatmulConfig 卡则把该选择落到 `CFG_MDL` 模板参数合同，二者构成选型理由到配置入口的直接链路。
- [Matmul高阶API开启MTE2 Preload](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_mte2_preload.md)（`explains`）：MTE2 Preload 案例通过 MatmulConfig::doMTE2Preload 开关启用预加载，并受 MDL、K 全载和 DoubleBuffer 约束；目标卡定义该配置入口。
- [Matmul高阶API开启多核K轴错峰访问内存](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_multi_core_k_stagger.md)（`explains`）：K 轴错峰的实际开关 enableKdimReorderLoad 属于 MatmulConfig，且案例要求 MDL 模板；配置卡是将性能诊断落实到模板参数的直接接口桥梁。
- [EnableL1BankConflictOptimise](../matmul_tiling/enable_l1_bank_conflict_optimise.md)（`related`）：EnableL1BankConflictOptimise 与《MatmulConfig》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [IterateNBatch](iterate_n_batch.md)（`related`）：IterateNBatch 与《MatmulConfig》的实质衔接是：IterateNBatch 必须先开启 MatmulConfig::isNBatch、配置 Host 侧 batch 信息并申请 workspace；同步/异步结果分别经 WaitIterateBatch 或 GetBatchTensorC/GetBatchC 获取，使用说明给出完整调用顺序。
- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：《MatmulCallBackFunc》说明模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。；《MatmulConfig》说明模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。MatmulConfig的参数说明见表2。MatmulConfig的定义方式有：。二者在回调类型由Matmul模板参数、配置与Policy实例化，并经注册宏和用户自定义信息进入Kernel侧Matmul对象上存在可执行的直接衔接。
- [MatmulPolicy](matmul_policy.md)（`related`）：MatmulPolicy 选择扩展策略，MatmulConfig 选择模板配置；二者共同确定 Matmul 对象的编译期行为但职责不同。
- [GetBasicConfig](get_basic_config.md)（`same_topic`）：MatmulConfig 定义 GetBasicConfig 返回对象的字段和模板常量化语义，补足 base 参数及调度开关的契约。
- [GetIBShareNormConfig](get_ib_share_norm_config.md)（`same_topic`）：MatmulConfig 定义 GetIBShareNormConfig 返回对象中的 intrinsicsCheck、batchMode、double-cache 与 UnitFlag 等字段。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《MatmulConfig》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetMMConfig](get_mm_config.md)（`same_topic`）：GetMMConfig 返回的正是 MatmulConfig；该卡定义预置模板及字段，是解释工厂函数结果不可缺的对象契约。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`same_topic`）：GetMatmulApiTiling 与《MatmulConfig》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [GetNormalConfig](get_normal_config.md)（`same_topic`）：GetNormalConfig 返回 Matmul 当前 Normal 配置，MatmulConfig 卡定义该配置对象及字段；前者是后者在 Matmul 对象上的读取入口。
- [GetSpecialMDLConfig](get_special_mdl_config.md)（`same_topic`）：GetSpecialMDLConfig 返回 MatmulConfig，该对象定义 intrinsicsCheck、batch、预加载与量化等字段的统一配置语义。
- [MatmulTemplateParams](matmul_template_params.md)（`same_topic`）：MatmulConfig 是 MatmulTemplateParams 的核心配置参数，决定 Norm、MDL、IBShare、BasicBlock 等执行模板。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；MatmulConfig正文界定“模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。MatmulConfig的参数说明见表2。MatmulConfig的定义方式有：”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [SetMatmulConfigParams](../matmul_tiling/set_matmul_config_params.md)（`same_topic`）：Host 侧 SetMatmulConfigParams 的取值必须与 Kernel 模板的 MatmulConfig 一致，否则两侧采用不同模板策略。
<!-- cannbot:related:end -->
