---
type: API
title: GetIBShareNormConfig
description: 用于配置IBShare模板的参数，获取自定义IBShare模板。IBShare模板的介绍请参考表模板特性。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetIBShareNormConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetIBShareNormConfig

用于配置IBShare模板的参数，获取自定义IBShare模板。IBShare模板的介绍请参考表模板特性。

函数原型：__aicore__ constexpr MatmulConfig GetIBShareNormConfig(const bool intrinsicsLimit = false, const bool batchLoop = false, const bool isVecND2NZ = false, const BatchMode bmmMode = BatchMode::BATCH_LESS_THAN_L1, const bool isDoubleCache = false, const bool enUnitFlag = true)

参数：
- intrinsicsLimit（输入）：用于设置参数intrinsicsCheck。 当左矩阵或右矩阵在单核上内轴（即尾轴）大于等于65535（元素个数）时，是否开启循环执行数据从Global Memory到L1 Buffer的搬入。
- batchLoop（输入）：用于设置参数isNBatch。 是否多Batch输入多Batch输出。仅对BatchMatmul有效，开启多Batch后，仅支持Norm模板，且需调用IterateNBatch实现多Batch输入多Batch输出。
- isVecND2NZ（输入）：用于设置参数enVecND2NZ。 开启通过vector指令进行ND2NZ。开启时需要设置SetLocalWorkspace。参数取值如下：false：不开启通过vector指令进行ND2NZ（默认值）。
- bmmMode（输入）：用于设置参数batchMode。该参数用于BatchMatmul场景。 BatchMatmul场景中Layout类型为NORMAL时，设置BatchMatmul输入A/B矩阵的多batch数据总和与L1 Buffer的大小关系。
- isDoubleCache（输入）：用于设置参数enableDoubleCache。 开启IBShare模板后，在L1 Buffer上是否同时缓存两块数据。参数取值如下：false：L1 Buffer上同时缓存一块数据（默认值）。

返回值：MatmulConfig结构体。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启IBShare模板共享A和B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_ab.md)（`explains`）：用于配置IBShare模板的参数，获取自定义IBShare模板；通过设置A和B矩阵MatmulType的IBShare均为true，开启该优化。接口提供 IBShare 模板配置入口，指南展示 A/B 同时共享时的 MatmulType 设置、Cube 分核与 27.11us 到 22.44us 的验证路径。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：开启IBShare模板后，在L1 Buffer上是否同时缓存两块数据；IBShare功能通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。接口的 isDoubleCache 参数控制 L1 缓存块数，指南说明 B 共享的 MTE2 复用机制、适用 shape 与 IterateAll 输出约束。
<!-- cannbot:related:end -->
