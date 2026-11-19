---
type: API
title: Python主机存储Tensor：empty_with_swapped_memory与生命周期
description: 保留NPU身份、有限消费者及版本打印条件，说明注册Host内存和释放同步成本。
tags:
- task.lookup
- topic.model_serving
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-empty_with_swapped_memory.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:39Z'
updated_at: '2026-11-14T08:44:18Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.empty_with_swapped_memory
---

# Python主机存储Tensor：empty_with_swapped_memory与生命周期

## 固定版本与复核边界

文档为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda各自收录页；发布对应ascend_26_0_pt28。实现分别为TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b和独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把独立main当已配套发行。

产品逐接口/版本限定；950条目如仅DT便不扩PR，旧Atlas不自动映射新型号。静态阅读不表示已调用设备、图捕获、回调、文件解析或性能验证；stable不表示运行verified。未执行上游或加载任何模型、检查点和dump数据。


## Python声明和存储

empty_with_swapped_memory(size,*,dtype=None,device=None)创建NPU设备身份、实际Host内存的特殊Tensor。size是非负形状整数序列；dtype未给采用全局默认，device未给取当前默认NPU。实际注册两个可选项是关键字参数，不按旧文本省略星号构造位置参数调用。Tensor不是普通CPU张量，也不是所有NPU算子可自动透明使用的统一内存。

两固定TensorFactories均检查NPU设备、非负尺寸，用Host交换分配器并设置连续逻辑shape/存储描述；complex在未禁JIT时拒绝，这个局部检查不扩大消费者dtype支持。main在deterministic空分配策略生效时额外填充，不能承诺所有empty分配都已初始化有效数值。

## 消费者和打印

明确不支持图模式，仅列fill_、zero_、mul_、npu_apply_adam_w、npu_hans_encode、npu_hans_decode六类操作。文档的torch.fill_等文字在Tensor代码中应核对实际方法，不作为额外顶层Python接口导出证明。

同时满足CANN>=8.5.0与Ascend HDK>=26.0.rc1才支持直接打印；任一较旧先mul_转普通Tensor再查看。不能把文档NPU设备信息当Host直接解引用普遍可用。发布产品A2/A3训练，主线Python页增加950DT，未确认950PR；[C++同名入口](cpp_swapped_memory.md)的独立产品页仍仅A2/A3，不互相补产品表。

## 资源生命周期

两固定分配器按系统页大小对齐，申请Host内存后HostRegister为映射内存；有VA一致性能力时使用相应配置，否则回退旧Host申请并处理对齐。返回指针和Host指针可能不同，设备身份并不改变实际Host资源消耗。

deleter会先同步设备，再注销Host注册、释放Host内存和映射记录；不能把“卸载到Host”宣传为没有同步或带宽成本。允许操作、初始化、实际消费者、Host峰值和释放时延分别验收，不根据样例数值推断优化收益。

## 已有 OpPlugin 7.3.0 文档与版本边界

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### NPU 设备标记与 Host 内存张量分配：torch_npu.empty_with_swapped_memory

### 用途与语义

申请一个device信息为NPU且实际内存在host侧的`Tensor`。

### 文档签名

```text
torch_npu.empty_with_swapped_memory(size, dtype=None, device=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-empty_with_swapped_memory.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）
