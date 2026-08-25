---
type: Guide
title: 输出shape依赖计算
description: 本文属于扩展内容，介绍输出shape依赖Kernel计算结果时的实现方法。NonZero等算子在Kernel计算完成前无法确定实际输出shape。此类输出需要在原型定义中调用OutputShapeDependOnCompute()标记，并由Kernel按照固定格式把实际shape写入框架追加的shape输出地址。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/kernel_output_shape_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 输出shape依赖计算

本文属于扩展内容，介绍输出shape依赖Kernel计算结果时的实现方法。NonZero等算子在Kernel计算完成前无法确定实际输出shape。此类输出需要在原型定义中调用OutputShapeDependOnCompute()标记，并由Kernel按照固定格式把实际shape写入框架追加的shape输出地址。
## 在算子原型中标记输出
OutputShapeDependOnCompute()只能用于输出。以下示例表示输出y的shape需要等待Kernel计算结果：
算子有多个输出时，只在实际依赖计算的输出上增加该标记。输入输出声明方法见算子原型定义。
## Kernel入口增加shape输出参数
框架会在所有普通输出之后、workspace和tiling之前追加一个GM_ADDR参数，用于保存依赖计算的输出shape。Kernel入口保持以下顺序：
示例：
即使有多个输出依赖计算，也只增加一个shape输出地址。各输出的shape信息在该地址中按原型输出顺序连续排列。
## shape信息排布格式
shape输出按uint64_t数组组织。每个待刷新输出固定占9个uint64_t元素：
偏移：内容
0：rank，即实际维度数
1至8：各维度大小，最多8维
如果有n个输出依赖计算，总空间为n * 9个uint64_t元素。第i个输出从i * 9开始，顺序与算子原型中的输出声明顺序一致。
对于输出Tensor数据类型为uint64_t的场景，需要把rank值的第31位设置为1，表示后续维度按uint64_t解析：
输出Tensor为uint32_t时不设置该标记，直接写入rank。
## 写入单个输出shape
假设输出y的数据类型为uint32_t，Kernel计算后得到实际shape为[32, 64]：
索引3至8是该输出的保留槽位，不会保存其他输出的数据。
输出Tensor的数据类型为uint64_t，实际shape为[1, 64, 128, 128]时，需要设置类型标记：
## 写入多个输出shape
假设两个输出都依赖计算，数据类型均为uint64_t，实际shape分别为[16, 32]和[1, 16, 16, 32]：
当算子还包含不依赖计算的普通输出时，shape输出区域只为调用了OutputShapeDependOnCompute()的输出分配槽位，但槽位顺序仍按这些输出在原型中的先后顺序排列。
## 相关文档
- Kernel侧算子实现：Kernel入口格式和参数顺序。
- 算子原型定义：输入输出声明和shape推导关系。
- OutputShapeDependOnCompute：接口定义和工程版本约束。

<!-- cannbot:related:start -->
## 相关

- [OutputShapeDependOnCompute](../../../../../apis/utils_api/prototype_register_management/op_param_def/output_shape_depend_on_compute.md)（`explains`）：OutputShapeDependOnCompute 只完成原型标记，目标指南给出 kernel 写实际 shape、框架读取并管理输出内存的完整实现合同。
- [InferShape 返回 identity 致空 kernel 假通过](../../../../../runbooks/precision/infershape_identity_kernel.md)（`related`）：该案例涉及 Kernel 计算后回写实际输出 shape，可作为动态 shape 槽位格式和运行结果的排障参照。
- [低 rank 零填充致 count=0 用 td_->rank 非 RANK](../../../../../runbooks/precision/rank_count_0_td_rank_rank.md)（`related`）：低 rank 零填充致 count=0 用 td_->rank 非 RANK 与《输出shape依赖计算》的实质衔接是：实际 rank 必须来自 tiling 而非模板容量；低 rank padding、NDDMA维度、shape/axes 和 blockDim 卡共同验证零填充维被误纳入循环后 count=0 的机制。
- [基本开发流程](../../operator_graph_development/basic_development_flow.md)（`related`）：基本开发流程 与《输出shape依赖计算》的实质衔接是：算子图基本流程把 OpDef 原型、InferShape/InferDataType、图编译执行和 tiling 下沉串成同一生命周期；三个失败案例分别验证原型加载、可选输入和 shape 推导不能被绕过。
- [算子功能设计](operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《输出shape依赖计算》说明本文属于扩展内容，介绍输出shape依赖Kernel计算结果时的实现方法。NonZero等算子在Kernel计算完成前无法确定实际输出shape。此类输出需要在原型定义中调用OutputShapeDependOnCompute()标记，并由Kernel按照固定格式把实际shape写入框架追加的shape输出地址。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [高级编程基本流程](kernel_operator_implementation.md)（`related`）：动态 shape 地址仍遵循 Kernel 普通输出、shape 输出、workspace、tiling 的入口顺序，需要结合 Kernel 实现规则落地。
- [高级编程基本流程](host_tiling_implementation.md)（`same_topic`）：高级编程基本流程 与《输出shape依赖计算》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
<!-- cannbot:related:end -->
