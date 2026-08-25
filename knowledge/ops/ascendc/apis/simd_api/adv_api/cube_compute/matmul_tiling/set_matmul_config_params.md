---
type: API
title: SetMatmulConfigParams
description: 在计算Tiling时，用于自定义设置表1中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetMatmulConfigParams.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetMatmulConfigParams

在计算Tiling时，用于自定义设置[表1](#table9646134355611)中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。

函数原型：
void SetMatmulConfigParams(int32_t mmConfigTypeIn = 1, bool enableL1CacheUBIn = false, ScheduleType scheduleTypeIn = ScheduleType::INNER_PRODUCT, MatrixTraverse traverseIn = MatrixTraverse::NOSET, bool enVecND2NZIn = false)
void SetMatmulConfigParams(const MatmulConfigParams& configParams)

参数：
- mmConfigTypeIn（输入）：设置Matmul的模板类型，需要与Matmul对象创建的模板一致，当前只支持配置为0或1。/0：代表Norm模板 1：代表MDL模板，默认值为1
- enableL1CacheUBIn（输入）：配置是否开启L1缓存UB计算块；推荐开启场景：MTE3和MTE2流水串行较多的场景。/false：不开启L1缓存UB计算块，默认值为false/true：开启L1缓存UB计算块
- scheduleTypeIn（输入）：配置Matmul数据搬运模式。参数取值如下：ScheduleType::INNER_PRODUCT：默认模式，在K方向上做MTE1的循环搬运 ScheduleType::OUTER_PRODUCT：在M或N方向上做MTE1的循环搬运ScheduleType::N_BUFFER_33：NBuffer33模板的数据搬运模式，MTE2每次搬运A矩阵的1x3个基本块，直至A矩阵所有3x3个基本块全载在L1 Buffer中
- traverseIn（输入）：Matmul做矩阵运算的循环迭代顺序，即一次迭代计算出[baseM, baseN]大小的C矩阵分片后，自动偏移到下一次迭代输出的C矩阵位置的偏移顺序。参数取值如下： NOSET：0，当前无效。。
- enVecND2NZIn（输入）：是否开启ND2NZ。

约束：
- 本接口必须在GetTiling接口前调用。
- 若Matmul对象使用NBuffer33模板策略，即MatmulPolicy为NBuffer33MatmulPolicy，则在调用GetTiling接口生成Tiling参数前，必须通过本接口将scheduleTypeIn参数设置为ScheduleType::N_BUFFER_33，以启用NBuffer33模板策略的Tiling生成逻辑。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《SetMatmulConfigParams》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [Matmul高阶API开启UnitFlag](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`explains`）：《SetMatmulConfigParams》明确“在计算Tiling时，用于自定义设置表1中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。”；它与《Matmul高阶API开启UnitFlag》的“开启UnitFlag为MMAD与FIXPIPE提供512B细粒度同步，实现计算与搬出流水并行，提升算子性能。”在实际调用参数、数据流或结果校验上直接衔接。
- [EnableL1BankConflictOptimise](enable_l1_bank_conflict_optimise.md)（`related`）：EnableL1BankConflictOptimise 与《SetMatmulConfigParams》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [GetMMConfig](../matmul_kernel/get_mm_config.md)（`related`）：Host 侧设置的模板、调度与遍历参数必须与 Kernel 的 MatmulConfig 一致，连接 GetMMConfig 的设备配置和 tiling 生成。
- [GetNormalConfig](../matmul_kernel/get_normal_config.md)（`related`）：GetNormalConfig 与《SetMatmulConfigParams》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetSpecialMDLConfig](../matmul_kernel/get_special_mdl_config.md)（`related`）：Host tiling 的 MatmulConfig 参数必须与 Kernel 侧 SpecialMDL 配置保持一致，连接模板选择与 tiling 生成。
- [GetMDLConfig](../matmul_kernel/get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《SetMatmulConfigParams》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetMatmulApiTiling](../matmul_kernel/get_matmul_api_tiling.md)（`same_topic`）：GetMatmulApiTiling 与《SetMatmulConfigParams》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [MatmulConfig](../matmul_kernel/matmul_config.md)（`same_topic`）：Host 侧 SetMatmulConfigParams 的取值必须与 Kernel 模板的 MatmulConfig 一致，否则两侧采用不同模板策略。
- [SetMadType](set_mad_type.md)（`same_topic`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《SetMatmulConfigParams》明确提供“在计算Tiling时，用于自定义设置表1中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《SetMatmulConfigParams》提供“在计算Tiling时，用于自定义设置表1中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
