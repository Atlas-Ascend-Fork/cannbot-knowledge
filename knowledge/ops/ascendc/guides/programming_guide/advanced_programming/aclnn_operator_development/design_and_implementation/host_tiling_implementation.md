---
type: Guide
title: 高级编程基本流程
description: 本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/host_tiling_implementation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基本流程

本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。
## Tiling概念回顾
Tiling是在Kernel启动前，根据数据规模、平台资源和Kernel实现确定数据切分方式及运行配置的过程。Tiling本身不执行算子的张量计算，而是为Kernel准备运行所需的参数。
对于常见的数据并行算子，数据通常按以下两个层次切分：
- Block：Kernel的逻辑并行单元。整体数据分配给多个Block并行处理，Block数量通过numBlocks指定。
- Tile：单个Block内分批处理的数据单元。当一个Block负责的数据无法一次放入片上存储（例如UB）时，Kernel按Tile循环完成数据搬入、计算和写回。
TilingFunc运行在Host侧。框架在Kernel启动前调用TilingFunc，并通过TilingContext提供输入输出shape、属性信息。TilingFunc读取并校验这些信息，计算切分参数、选择Kernel分支，最后写回两类结果：
- TilingData：Kernel执行时需要读取的参数，例如总元素数、单次处理的数据量、循环次数、尾块长度和分支参数。
- Kernel启动配置：例如numBlocks、workspace大小、TilingKey和调度模式。
Host侧Tiling的输入和输出如下图所示：
图中，TilingContext是TilingFunc与框架之间的数据载体：TilingFunc从中读取输入输出shape、属性信息，并将TilingData、numBlocks、TilingKey和workspace大小等结果写回其中。
## 核心概念
Host侧Tiling的输出主要包括TilingData、numBlocks、workspace大小和TilingKey；不同运行场景还可能涉及调度模式（schedule mode）等Kernel launch配置。写代码前先理解这些输出，后面的流程会更容易对应。
### TilingData
TilingData用于承载Host侧传给Kernel侧的切分结果，只需定义Kernel实际使用的字段。常见字段包括总元素数、单次处理的数据量、循环次数、尾块长度和分支参数，具体字段由Kernel实现决定。
AddCustom基础样例只定义totalLength和tileNum。其中，totalLength表示总元素数；tileNum表示样例中总数据的分块数量。Kernel通过totalLength / tileNum计算单次处理的数据量，并与numBlocks共同确定每个Block的循环次数。
AscendC推荐使用标准C++语法定义Tiling结构体。这种方式便于组织固定大小、可直接复制的字段，且允许不同算子使用同名结构体。字段类型、数组写法和Host/Kernel侧一致性约束见使用约束。
本文档以标准C++语法为主线介绍Tiling实现的基本流程。

<!-- cannbot:related:start -->
## 相关

- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](../../../../../runbooks/compilation/561103_isgroup_1_tilingkey.md)（`related`）：高级编程基本流程 与《561103: isGroup=-1 哨兵致 tilingKey 路由失配》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`related`）：高级编程基本流程 与《ACLNN 361001 — tilingKey 与 funcEntry 映射失》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [CMake函数参考（附录）](../appendix/cmake_function_reference.md)（`related`）：高级编程基本流程 与《CMake函数参考（附录）》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [TilingFunc 未声明依赖读 axes 致 segfault](../../../../../runbooks/compilation/tilingfunc_axes_segfault.md)（`related`）：高级编程基本流程 与《TilingFunc 未声明依赖读 axes 致 segfault》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`related`）：高级编程基本流程 与《TilingKey 缓存 correction 致 tilingdata 复用》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [blockLength 对齐 slice 致 numBlocks 塌缩单核](../../../../../runbooks/performance/blocklength_slice_numblocks.md)（`related`）：高级编程基本流程 与《blockLength 对齐 slice 致 numBlocks 塌缩单核》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`related`）：高级编程基本流程 与《sub-kernel 后缀 _N 是 tilingKey 位编码非序号》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`related`）：高级编程基本流程 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [使用高阶API时配套的Tiling实现](tiling_with_advanced_api.md)（`related`）：Host Tiling 基本流程定义从 shape、平台资源到 TilingData/workspace/numBlocks 的通用输出，本卡在其上接入 MultiCoreMatmulTiling 与 TCubeTiling。
- [算子功能设计](operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《高级编程基本流程》说明本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [高级编程基本流程](kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《高级编程基本流程》说明本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [多分支策略](multi_branch_strategy.md)（`same_topic`）：高级编程基本流程 与《多分支策略》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [算子原型定义](operator_prototype_definition.md)（`same_topic`）：高级编程基本流程 与《算子原型定义》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [算子适配说明](../../super_kernel/operator_adaptation.md)（`same_topic`）：算子适配说明 与《高级编程基本流程》的实质衔接是：SuperKernel 适配要求算子 block 数、SK_BIND、核间 flag 与缓存可见性匹配；原理、流程和 mix-mode 失败案例给出可执行约束。
- [编译与部署基本流程](../compilation_and_deployment/basic_process.md)（`same_topic`）：高级编程基本流程 与《编译与部署基本流程》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [编译过程调试](../compilation_and_deployment/compilation_debug.md)（`same_topic`）：高级编程基本流程 与《编译过程调试》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [输出shape依赖计算](kernel_output_shape_computation.md)（`same_topic`）：高级编程基本流程 与《输出shape依赖计算》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [通过TilingData传递属性信息](tiling_data_attributes.md)（`same_topic`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“高级编程基本流程”明确本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
<!-- cannbot:related:end -->
