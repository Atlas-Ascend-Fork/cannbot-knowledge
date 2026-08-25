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
