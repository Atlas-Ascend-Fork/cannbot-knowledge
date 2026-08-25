---
type: API
title: Relu
description: 根据mask对源操作数srcReg进行Relu（线性整流）操作，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Relu

该接口根据mask对输入数据srcReg进行Relu（线性整流）操作，将结果写入dstReg。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_unary_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数中元素有效性的指示，详细说明请参考MaskReg。

支持数据类型：half、int32_t、float、int64_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [DAV_2201 element-wise unary kernel 骨架 多核](../../../../../runbooks/compilation/dav2201_elementwise_unary_kernel_skeleton_relu.md)（`exemplifies`）：焦点处理Reg Relu 的负值清零及跨 API 实现；DAV_2201 element-wise unary kernel 骨架 多核正文界定“在 DAV_2201（Ascend 910B3）上用 ops-direct-invoke 实现单入单出 element-wise unary 算子（以 ReLU fp16 为例）的完整 kernel 骨架：运行时取核数→尾核 tailing”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
- [AscRelu](../../../c_api/reg/arithmetic_compute/asc_relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；AscRelu正文界定“根据mask对源操作数src按元素进行relu操作，将结果写入目的操作数dst”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
- [AscRelu](../../../c_api/vector_compute/asc_relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；AscRelu正文界定“按元素做线性整流Relu，”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
- [LeakyRelu](../../memory_vector_compute/basic_arithmetic/leaky_relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；LeakyRelu正文界定“矢量元素执行Leaky ReLU操作：非负值原样输出，负值乘以标量系数后输出”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
- [LeakyRelu](leaky_relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；LeakyRelu正文界定“按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量scalarValue后写入”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
- [Prelu](prelu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；Prelu正文界定“实现PReLU激活函数，源操作数srcReg0大于0的元素直接写入目的操作数，否则与srcReg1对应元素相乘后写入”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
- [Relu](../../memory_vector_compute/basic_arithmetic/relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；Relu正文界定“单目矢量计算接口，对输入tensor按元素做ReLU计算，负值置零，非负值原样输出”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
<!-- cannbot:related:end -->
