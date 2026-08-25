---
type: Guide
title: 如何开发动态输入算子
description: 动态输入算子是指算子的输入个数是动态的，例如AddN，将N个输入tensor累加到一起，输出一个tensor，输入tensor的个数是不固定的。动态输入算子的开发在构造和解析输入数据方面有差异：核函数的入参采用ListTensorDesc的结构存储输入数据信息，对应的，调用时需构造TensorList结构保存参数信息。下面基于kernel直调和工程化算子开发两种开发方式分别介绍具体开发流程。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/common_operations/develop_dynamic_input_operator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 如何开发动态输入算子

动态输入算子是指算子的输入个数是动态的，例如AddN，将N个输入tensor累加到一起，输出一个tensor，输入tensor的个数是不固定的。动态输入算子的开发在构造和解析输入数据方面有差异：核函数的入参采用ListTensorDesc的结构存储输入数据信息，对应的，调用时需构造TensorList结构保存参数信息。下面基于kernel直调和工程化算子开发两种开发方式分别介绍具体开发流程。
-   kernel直调
-   参考ListTensorDesc数据结构自行定义ListTensorDesc和TensorDesc结构体，并将实际的输入数据保存至ListTensorDesc结构中。示例如下:
ptrOffset传入为ListTensorDesc首地址和数据指针首地址dataPtr之间的偏移量，tensorDesc中保存两个输入的tensor描述信息， dataPtr传入为保存输入数据的地址指针。
-   kernel侧调用时，直接传入ListTensorDesc表达的输入信息。示例如下：
-   kernel侧算子实现，入参需传入动态结构的数据（srcList），并使用AscendC::ListTensorDesc结构做解析。示例如下：
-   工程化算子开发
-   单算子调用时，构造List类型tensor并传入。
使用aclCreateTensor创建tensor后，需调用aclCreateTensorList，将创建好的tensor组成List形式，如下所示。
获取算子使用的workspace空间大小接口的入参，也需使用aclTensorList结构参数，用来计算workspace的大小，调用示例如下。
-   算子原型定义中，输入数据的参数类型设置为动态，示例如下。
-   host侧算子实现，获取动态输入信息的接口，需使用对应的动态接口。
例如，Tiling函数和InferShape函数中，GetDynamicInputShape接口用于获取动态输入的shape信息，InferDataType函数中，GetDynamicInputDataType接口用于获取动态输入的数据类型，示例如下。
-   kernel侧算子实现，入参需传入动态结构的数据，并使用AscendC::ListTensorDesc结构做解析。
核函数入参需传入动态结构的数据，例如GM_ADDR srcList，示例如下。
对传入的参数srcList，需使用AscendC::ListTensorDesc结构做解析，得到每个tensor的具体信息，示例如下。

<!-- cannbot:related:start -->
## 相关

- [ListTensorDesc](../../../../apis/simd_api/basic_api/aux_data_structures/list_tensor_desc.md)（`explains`）：如何开发动态输入算子 与《ListTensorDesc》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [TensorDesc](../../../../apis/simd_api/basic_api/aux_data_structures/tensor_desc/tensor_desc.md)（`explains`）：如何开发动态输入算子 与《TensorDesc》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [TensorDesc简介](../../../../apis/simd_api/basic_api/aux_data_structures/tensor_desc/tensor_desc_intro.md)（`explains`）：如何开发动态输入算子 与《TensorDesc简介》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](../../../../runbooks/compilation/gm_addr_tiling.md)（`related`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《如何开发动态输入算子》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [bisheng 动态 shape 编译段错误 — extern C + DTYPE](../../../../runbooks/compilation/bisheng_extern_c_dtype_dynamic_shape_segfault.md)（`related`）：如何开发动态输入算子 与《bisheng 动态 shape 编译段错误 — extern C + DTYPE》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`related`）：如何开发动态输入算子 与《optional input 未连接触发 InferShape 失败》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`related`）：如何开发动态输入算子 与《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [高级编程基本流程](../../advanced_programming/aclnn_operator_development/design_and_implementation/kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《如何开发动态输入算子》说明动态输入算子是指算子的输入个数是动态的，例如AddN，将N个输入tensor累加到一起，输出一个tensor，输入tensor的个数是不固定的。动态输入算子的开发在构造和解析输入数据方面有差异：核函数的入参采用ListTensorDesc的结构存储输入数据信息，对应的，调用时需构造TensorList结构保存参数信息。下面基于kernel直调和工程化算子开发两种开发方式分别介绍具体开发流程。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [基本开发流程](../../advanced_programming/operator_graph_development/basic_development_flow.md)（`same_topic`）：如何开发动态输入算子 与《基本开发流程》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [算子动态库和静态库编译](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/dynamic_static_lib_compilation.md)（`same_topic`）：如何开发动态输入算子 与《算子动态库和静态库编译》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [算子原型定义](../../advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`same_topic`）：如何开发动态输入算子 与《算子原型定义》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [适配插件开发](../../advanced_programming/ai_framework_adaptation/onnx_framework/adaptation_plugin_development.md)（`same_topic`）：如何开发动态输入算子 与《适配插件开发》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
<!-- cannbot:related:end -->
