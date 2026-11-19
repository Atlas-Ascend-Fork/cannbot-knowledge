---
type: API
title: C++ npu_format_cast：版本参数与950DT私有格式限制
description: 区分发布双参数接口、主线customize_dtype门槛，以及950DT NZ格式的形状和后续操作限制。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_format_cast.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_format_cast.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-npu_format_cast.md
  role: constraint
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# C++ npu_format_cast：版本参数与950DT私有格式限制

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 发布与主线声明

定义于`torch_npu/csrc/core/npu/NPUFormat.h`、命名空间`at_npu::native`。发布文档为`at::Tensor npu_format_cast(const at::Tensor& self, int64_t acl_format)`；主线新增`c10::optional<int64_t> customize_dtype = c10::nullopt`。self为待转换Tensor，返回转换后的Tensor；本卡是C++接口，不能拿[发布版Python双参数接口](npu_format_cast.md)代替其主线签名或产品约束。

主线本接口明确新增950DT；本卡metadata中的950仅对这一主线条目成立，发布来源仍没有该确认，不扩到950PR。A2/A3仍限训练系列。

## customize_dtype与C0

默认FP32/INT32的C0=16、INT8的C0=32。文档示例传3（torch.int32对应值）使NZ的C0=8；参数控制该布局选择，不是任意公开dtype转换承诺。整数枚举应和固定版本对应，不把所有整数都视为有效值。

**该参数仅支持A2/A3训练系列且CANN>=9.1.0**；其他产品或更旧CANN传该参数会报错。主线整体列950DT不能消去这一参数门槛，也不能以新参数回推26.0/PyTorch2.8。

## 950DT的独立限制

主线明确950DT私有格式转换不受`torch_npu.npu.config.allow_internal_format=False`限制。转NZ后的Tensor不支持文档所列会修改Tensor的操作，包括contiguous、pad、view、slice；应按这个私有格式合同处理，不能照搬普通Tensor中“view不修改值”的直觉来放宽允许操作。

最后两维任一为1的NZ Tensor不支持transpose。文档另称当self.dtype与customize_dtype一致且为FP16/BF16时，二维[k,n]的k=1不支持；这与customize_dtype本身仅A2/A3支持的限定同时保留，不能由该条件反推950可显式传该参数。

格式号、C0、dtype与逻辑维度变换分别核对。先确认目标算子能消费转换结果及数值、别名/后续操作符合业务，再衡量转换开销和模型收益；未执行转换或性能测试。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_format_cast.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_format_cast.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-npu_format_cast.md)（constraint）
