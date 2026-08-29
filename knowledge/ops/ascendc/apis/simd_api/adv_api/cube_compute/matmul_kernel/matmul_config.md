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

- [Matmul高阶API开启MDL模板](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md)（`explains`）：本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启MDL模板对算子性能的提升效果。在MDL模板中，MTE2流水从Global Memory到L1 Buffer（A1/B1）的数据搬运为一次性大包搬运，即一次MTE2能搬入多个Matmul计算的基本块，提升带宽利用率，使后续的MTE1流水尽可能复用A1/B1内基本块的缓存数据，减少MTE2的搬运次数。MDL模板的详细介绍请参考MatmulConfig。；模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。MatmulConfig的参数说明见表2。MatmulConfig的定义方式有： - 该模板参数可选取提供的模板之一，当前提供的MatmulConfig模板取值范围为【CFG_NORM、CFG_MDL、CFG_IBSHARE_NORM、MM_CFG_BB】，分别对应默认的Norm、MDL、IBShare、BasicBlock模板。各模板的介绍请参考表1。 - 该模板参数可以基于各类获取模板的接口，自定义模板参数配置，获取自定义模板。；案例要求开启 MDL，目标给出选择 CFG_MDL 的实际模板参数入口及默认 Norm 行为。
- [Matmul高阶API开启UnitFlag](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`explains`）：开启UnitFlag功能的方式为将MatmulConfig中的enUnitFlag参数设置为true。；模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。。调优指南把 MMAD 与 FIXPIPE 流水并行的开关落到 MatmulConfig.enUnitFlag，API 页定义承载该模板配置的 MatmulConfig 参数对象。
- [GetMMConfig](get_mm_config.md)（`related`）：返回值：MatmulConfig结构体。；模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。；前者是自定义配置的构造入口，后者定义其返回对象及模板语义。
- [GetSpecialMDLConfig](get_special_mdl_config.md)（`related`）：返回值：MatmulConfig结构体。；模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。；GetSpecialMDLConfig 是 MatmulConfig 自定义实例的生产接口。
- [SetMatmulConfigParams](../matmul_tiling/set_matmul_config_params.md)（`related`）：模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。；在计算Tiling时，用于自定义设置［表1］(#table9646134355611)中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。；MatmulConfig 定义 kernel 模板配置，SetMatmulConfigParams 在 Tiling 侧写入同一组参数并要求两侧取值一致。
<!-- cannbot:related:end -->
