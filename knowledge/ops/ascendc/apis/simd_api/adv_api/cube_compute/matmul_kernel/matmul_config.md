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
