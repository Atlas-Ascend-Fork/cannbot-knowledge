---
type: API
title: Relu
description: 单目矢量计算接口，对输入tensor按元素做ReLU计算，负值置零，非负值原样输出。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Relu

单目矢量计算接口，按元素计算 ReLU 激活。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = max(0, src_i)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [DAV_2201 element-wise unary kernel 骨架 多核](../../../../../runbooks/compilation/dav2201_elementwise_unary_kernel_skeleton_relu.md)（`exemplifies`）：该 kernel 骨架的 Compute 阶段直接按元素调用 Relu；API 卡明确 dst=max(0,src) 和支持数据类型，是功能语义的最小合同。
- [AddRelu](../composite_compute/add_relu.md)（`related`）：AddRelu 等价于先逐元素求和再对中间结果执行 Relu；拆分为 Add+Relu 可用于不满足复合接口 dtype/mask 契约的路径。
- [AscRelu](../../../c_api/vector_compute/asc_relu.md)（`related`）：Basic Memory Relu 是 LocalTensor 风格的对应接口，可用于从 C Vector API 迁移。
- [Maxs](maxs.md)（`related`）：Maxs 与《Relu》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Mins](mins.md)（`related`）：Mins 与《Relu》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [ReGlu](../../../adv_api/activation_functions/re_glu_interface/re_glu.md)（`related`）：ReGlu 的门控分支使用 ReLU 激活；基础 Relu 明确 dst=max(0,src)，可用于拆解和验证 ReGlu 的激活部分。
- [LeakyRelu](leaky_relu.md)（`same_topic`）：LeakyRelu 与《Relu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Relu](../../reg_vector_compute/basic_arithmetic/relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；Relu正文界定“单目矢量计算接口，对输入tensor按元素做ReLU计算，负值置零，非负值原样输出”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
<!-- cannbot:related:end -->
