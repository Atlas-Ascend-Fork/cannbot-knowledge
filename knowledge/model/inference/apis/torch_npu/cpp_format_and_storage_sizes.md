---
type: API
title: TorchNPU C++格式API：分配、格式号与底层存储维度
description: 区分empty_with_format的keep_format、格式编号与get_npu_storage_sizes的各维大小。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-empty_with_format.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-empty_with_format.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-empty_with_format.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_format.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_format.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-get_npu_format.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_storage_sizes.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_storage_sizes.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-get_npu_storage_sizes.md
  role: constraint
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU C++格式API：分配、格式号与底层存储维度

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 接口原型与头文件

定义于`torch_npu/csrc/core/npu/NPUFormat.h`，文档声明如下：

```cpp
at::Tensor empty_with_format(c10::IntArrayRef sizes,
    const c10::TensorOptions& options, int64_t acl_format, bool keep_format = false);
int64_t get_npu_format(const at::Tensor& self);
std::vector<int64_t> get_npu_storage_sizes(const at::Tensor& self);
```

以上属于`at_npu::native`命名空间。sizes是请求形状，options指定Tensor属性，acl_format是NPU格式编号。keep_format=true要求保持所给格式，false允许实现按条件调整；这不保证任意shape、dtype、格式组合均有效，也不提供初始化数值保证。

## 逻辑shape、物理存储与字节数

get_npu_format返回格式编号，不返回dtype或转置排列。get_npu_storage_sizes返回int64维度向量：主线中文明确为Tensor底层存储每一维的大小；发布中文和主线英文泛称“内存大小”。因此不能直接把返回向量当已分配字节数，也不能总认为它等于逻辑`self.sizes()`。

模型布局优化需要同时保存逻辑shape、实际dtype、格式号和底层维度，按消费者验证，而非仅比较其中一个值。格式转换及主线950DT限制见[C++ npu_format_cast](cpp_npu_format_cast.md)；其新增产品范围不扩大本卡其余接口范围。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-empty_with_format.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-empty_with_format.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-empty_with_format.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_format.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_format.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-get_npu_format.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_storage_sizes.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-get_npu_storage_sizes.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-get_npu_storage_sizes.md)（constraint）
