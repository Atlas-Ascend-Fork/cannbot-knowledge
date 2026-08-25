---
type: Guide
title: 高级编程基本流程
description: 本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global
  Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/kernel_operator_implementation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 基本流程

本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。
## Kernel函数格式
### 命名规则
Kernel入口函数名需要和算子类型对应。算子类型采用大驼峰命名，Kernel入口函数采用小写下划线命名，框架在编译和运行时根据命名规则完成匹配。
算子类型：Kernel入口函数名
AddCustom：add_custom
MatmulCustom：matmul_custom
ReduceMaxCustom：reduce_max_custom
Conv2DCustom：conv2_d_custom
GatherV2Custom：gather_v2_custom
完整转换规则和更多示例会在命名转换规则对照表中展开。
### 函数形式
Kernel入口函数可以使用非模板入口或模板化入口。
非模板入口使用extern "C"指定C语言链接规则，msOpGen生成的基础模板通常采用这种形式。
模板化入口通过模板参数承载dtype、Tile数量和分支选择信息。下面示例对应的算子类型是AddCustomTemplate，因此Kernel入口名为add_custom_template。在aclnn工程化算子开发方式中，需要先声明模板参数及其可用组合，再由Host侧Tiling通过ASCENDC_TPL_SEL_PARAM选择组合，编译工具根据配置实例化对应的Kernel。
上述代码使用REGISTER_TILING_DEFAULT注册默认TilingData结构体，并通过GET_TILING_DATA_WITH_STRUCT按指定类型解析Tiling数据。模板参数声明、Host侧选择和编译配置请参考多分支策略的Tiling模板编程章节。
### 参数顺序
Kernel入口函数参数需要按照“输入、输出、workspace、tiling”的顺序排列。框架调用Kernel时，会先按照算子原型定义中的输入输出顺序传入Tensor地址，再追加workspace和tiling两个参数。
参数含义如下：
x、y：算子原型中的输入：指向输入Tensor的Global Memory地址
z：算子原型中的输出：指向输出Tensor的Global Memory地址
workspace：框架追加：指向workspace内存地址
tiling：框架追加：指向Host侧Tiling写入的数据
> 说明：输入输出同名场景
>
> 如果算子原型中的输入和输出同名，msOpGen生成Kernel入口参数时会给输出参数增加ref后缀，用于区分输入和输出地址。
>
>
Kernel实现类的内部组织方式由算子计算逻辑和Ascend C编程模式决定。

<!-- cannbot:related:start -->
## 相关

- [Kernel Tiling](../../../../../apis/simd_api/basic_api/kernel_tiling/kernel_tiling.md)（`explains`）：高级编程基本流程说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。
- [AI Core编译基本用法](../../../compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《AI Core编译基本用法》说明当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [Aclnn算子工程化开发快速入门](../aclnn_quick_start.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《Aclnn算子工程化开发快速入门》说明本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [使用高阶API时配套的Tiling实现](tiling_with_advanced_api.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《使用高阶API时配套的Tiling实现》说明本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [多分支策略](multi_branch_strategy.md)（`related`）：多分支策略 与《高级编程基本流程》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [如何开发动态输入算子](../../../appendix/common_operations/develop_dynamic_input_operator.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《如何开发动态输入算子》说明动态输入算子是指算子的输入个数是动态的，例如AddN，将N个输入tensor累加到一起，输出一个tensor，输入tensor的个数是不固定的。动态输入算子的开发在构造和解析输入数据方面有差异：核函数的入参采用ListTensorDesc的结构存储输入数据信息，对应的，调用时需构造TensorList结构保存参数信息。下面基于kernel直调和工程化算子开发两种开发方式分别介绍具体开发流程。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [算子功能设计](operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [算子原型定义](operator_prototype_definition.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《算子原型定义》说明本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [算子实现](../../../../operator_practice/simd_operator_impl/matrix_advanced_api/operator_impl.md)（`related`）：算子实现 与《高级编程基本流程》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [编译与部署基本流程](../compilation_and_deployment/basic_process.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《编译与部署基本流程》说明本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [输出shape依赖计算](kernel_output_shape_computation.md)（`related`）：动态 shape 地址仍遵循 Kernel 普通输出、shape 输出、workspace、tiling 的入口顺序，需要结合 Kernel 实现规则落地。
- [通过TilingData传递属性信息](tiling_data_attributes.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《通过TilingData传递属性信息》说明本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [高级编程基本流程](host_tiling_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《高级编程基本流程》说明本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [算子适配说明](../../super_kernel/operator_adaptation.md)（`same_topic`）：算子适配说明 与《高级编程基本流程》的实质衔接是：SuperKernel 适配要求算子 block 数、SK_BIND、核间 flag 与缓存可见性匹配；原理、流程和 mix-mode 失败案例给出可执行约束。
<!-- cannbot:related:end -->
