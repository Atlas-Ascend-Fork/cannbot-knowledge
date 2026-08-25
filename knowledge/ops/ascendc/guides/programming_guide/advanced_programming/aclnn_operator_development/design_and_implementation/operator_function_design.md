---
type: Guide
title: 算子功能设计
description: 本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_function_design.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子功能设计

本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。
本文以AddCustom算子作为示例。AddCustom的计算语义如下：
本文只给出功能设计阶段需要明确的内容。具体接口和代码写法会在后续章节展开。
## 前置理解：aclnn工程化算子开发方式由哪几部分组成
一个aclnn自定义算子工程通常需要完成三类代码。
第一类代码：算子原型定义，声明算子的接口信息，包括输入、输出和属性，以及支持的dtype、format。
第二类代码：Host侧Tiling实现，在Kernel执行前准备运行参数。Kernel在AI Core上运行前，需要知道本次输入一共有多少数据、如何切核并启动多少个Block、每个Block内部如何继续切分、是否需要额外workspace，以及是否需要设置调度模式等launch配置。
第三类代码：Kernel侧算子实现，在AI Core上执行的实际计算。Kernel侧根据Tiling传入的参数，从GM搬运数据到UB，在UB上完成计算，再把结果写回GM。
本文的功能设计，就是在写这三类代码前，先确定每一类代码需要表达什么。
## 围绕算子原型做功能设计
算子原型设计从算子语义开始。算子语义描述算子接收什么数据、执行什么计算、输出什么结果。这个步骤决定OpDef中的输入输出声明，也决定Tiling和Kernel需要围绕哪些数据设计。
AddCustom是逐元素加法算子。输入x和y在相同位置上的元素相加，结果写入输出z。每个元素的计算互相独立，适合按连续数据段切分到多个Block上并行处理。
根据这条语义，可以先确定算子对外暴露的原型边界。AddCustom对外暴露两个输入x、y和一个输出z。这三个Tensor已经可以完整表达z = x + y的计算语义，每次调用都需要提供，因此在原型边界上都属于必选参数。AddCustom没有额外属性，调用方只需要准备两个输入Tensor和一个输出Tensor。
如果算子带有标量、维度、阈值、开关等配置项，需要在功能设计阶段确定它们的承载方式。值较小且用于描述算子行为的配置项适合作为属性；需要按Tensor传入、参与动态图数据依赖或数据量较大的内容适合作为输入。属性识别和传递的完整示例请参考通过TilingData传递属性信息。
除此之外，还需要确定算子支持什么场景：
- 数据类型和数据格式。
- 确定性：算子在相同输入下是否产生相同输出。
将前两步确定的输入输出、dtype/format列表等合并，即得到完整的算子原型定义。完整的算子原型定义编写方法和API说明请参考算子原型定义。
完成算子原型设计后，功能设计可以继续拆解Host侧Tiling需要准备的运行参数，以及Kernel侧如何完成实际计算。
## 围绕Host侧Tiling做功能设计
Host侧Tiling设计的重点，是确定Kernel启动前需要准备哪些运行参数。Host侧Tiling负责把输入shape、属性等信息转换成Kernel运行时需要的参数，包括切核策略、Block内切分、workspace大小、TilingKey和必要的调度模式等。

<!-- cannbot:related:start -->
## 相关

- [Aclnn算子工程化开发快速入门](../aclnn_quick_start.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《Aclnn算子工程化开发快速入门》说明本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [使用高阶API时配套的Tiling实现](tiling_with_advanced_api.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《使用高阶API时配套的Tiling实现》说明本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [多分支策略](multi_branch_strategy.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《多分支策略》说明本文属于扩展内容，介绍同一个算子需要根据dtype、shape或属性执行不同计算流程时，如何使用TilingKey或Kernel模板组织多个Kernel分支。TilingKey使用数字标识分支，适合分支数量较少、含义稳定的场景；Kernel模板使用具名参数描述分支，适合由多个维度共同决定分支的场景。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [算子原型定义](operator_prototype_definition.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《算子原型定义》说明本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [算子基本概念](../../../../technical_appendix/concepts_and_terms/neural_networks_and_operators/operator_basics.md)（`related`）：算子基本概念：算子名称/类型/Tensor/Shape/Layout概念是原型定义和功能设计的输入语言；数据排布卡进一步解释Tensor layout，帮助把概念落到注册与实现。 目标卡《算子功能设计》补充：本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。
- [编译与部署基本流程](../compilation_and_deployment/basic_process.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《编译与部署基本流程》说明本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [输出shape依赖计算](kernel_output_shape_computation.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《输出shape依赖计算》说明本文属于扩展内容，介绍输出shape依赖Kernel计算结果时的实现方法。NonZero等算子在Kernel计算完成前无法确定实际输出shape。此类输出需要在原型定义中调用OutputShapeDependOnCompute()标记，并由Kernel按照固定格式把实际shape写入框架追加的shape输出地址。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [通过TilingData传递属性信息](tiling_data_attributes.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《通过TilingData传递属性信息》说明本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [高级编程基本流程](host_tiling_implementation.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《高级编程基本流程》说明本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [高级编程基本流程](kernel_operator_implementation.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [高级编程概述](../overview.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《高级编程概述》说明本文是基础内容，说明Aclnn算子工程化开发这组文档的范围、阅读顺序和前置条件。建议先确认环境满足要求，再按快速入门跑通AddCustom示例，跑通后回到对应章节逐步补齐细节。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
<!-- cannbot:related:end -->
