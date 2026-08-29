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

- [ListTensorDesc](../../../../apis/simd_api/basic_api/aux_data_structures/list_tensor_desc.md)（`explains`）：“核函数的入参采用ListTensorDesc的结构存储输入数据信息”指出动态输入 kernel 的 ABI 容器；“提供构造函数创建空列表，通过AppendTensorDesc添加Tensor描述符，通过GetTensorDesc获取指定位置的描述符，通过GetNum获取列表大小。”给出构造、访问和计数该容器的接口操作。
<!-- cannbot:related:end -->
