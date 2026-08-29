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

- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`same_topic`）：mmCFG（输入）：获取的MatmulConfig模板；返回值：MatmulConfig结构体。GetMDLConfig 生成 MatmulConfig，而 GetMatmulApiTiling 把该结构作为 mmCFG 输入生成编译期静态 Tiling；这是直接的生产者到消费者接口契约。
- [GetNormalConfig](get_normal_config.md)（`same_topic`）：用于配置Norm模板的参数，获取自定义Norm模板；用于配置MDL模板的参数，获取自定义MDL模板。两端是同一 Matmul Kernel 模板工厂中的 Norm 与 MDL 配置入口，对照可在普通模板和 MDL 模板之间选择正确的 config 构造函数，避免把模板参数交给错误入口。
<!-- cannbot:related:end -->
