---
type: Guide
title: TorchNPU 连续化：目标缓冲门控与描述符缓存
description: 沿基础格式设备拷贝解释连续化选择、描述符缓存与实际搬运的区别，区分缓存命中、容量上限和 StrideCopy 回退；含 npu_stride_copy
  / npu_view_copy 实现层（≥256 stride 转置优化、<32B view_copy 回退与 pin 差、AclnnOnly 物化路径）。
tags:
- task.optimization
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ContiguousOpt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/ContiguousOpt.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ContiguousOpt.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/ContiguousOpt.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/contiguous_register.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/contiguous_register.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/permute_opt.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/permute_opt.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/CopyKernel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/CopyKernel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AsStridedKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AsStridedKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AsStridedKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ViewcopyKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ViewcopyKernelNpu.cpp
  role: implementation
created_at: '2026-11-10T14:50:25Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# TorchNPU 连续化：目标缓冲门控与描述符缓存

## 固定版本与适用边界

静态审阅 PyTorch/TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与发布线 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的所列调用链。连续化调度、缓存比较、Transpose 消费和基础格式拷贝的选定实现一致；选项函数两版均以函数内静态值保存首次读取结果，发布版在函数内构造允许值表。未确认产品范围，因此保持 `draft` 和空平台；未执行上游、设备、正确性或性能实验。

## 先确认实际拷贝分支

在 `copy_d2d_dtype_baseformat` 的同 dtype、基础格式路径，目标 `self` 非连续时直接走通用拷贝；只有目标连续、源非连续时才尝试 `ContiguousOptimizeWithBaseFormat`。尝试失败后调用 `npu_stride_copy_out`，记录 `contiguous_d_AsStrided`；源与目标都连续且元素数相同时另走 `d2dCopyAsync`。这些是该具体入口的分支，不能据此概括每个 ACLNN 算子或所有设备拷贝。

连续化还要通过 `CheckClone`：目标存储偏移需满足 `OffsetAreMatch`，目标自身连续，源目标 sizes 相等，目标 sizes 还须等于其存储描述的 base_sizes。仅看到源是某种 view，或两者形状相等，不能判定该优化可用。

## 哪些入口使用缓存

|入口|实际行为|
|---|---|
|已有目标的 `ContiguousOptimizeWithAnyFormat(self, src, ...)`|尝试普通 `Run`；该重载本身不查描述符缓存。|
|只传源的 `ContiguousOptimizeWithAnyFormat(src, ...)`|先检查 NPU 类型并按源格式申请目标，再进入缓存调度；失败返回 `nullopt`。|
|`ContiguousOptimizeWithBaseFormat(self, src, ...)`|先要求源为基础格式，再进入缓存调度。`OpenCombined` 与选项判断同时成立时追加 `combined` 候选。|

`OpenCombined` 为 False 时，短路表达式尚不调用选项 getter；`CheckCombinedOptimizerEnable` 在首次实际调用时初始化函数内静态变量。两版先由 `GetBoolTypeOption` 使用 `strtol` 解析，再把非零归一为 1、零归一为 0，随后检查允许值表并保存布尔结果；这不构成对原始环境字符串严格只能为 0/1 的校验。不要把运行后改 `COMBINED_ENABLE` 当作该静态值的刷新方式，部署仍按文档支持值配置。组合 view 的文档条件另见[编译缓存与组合连续化](torch_npu_aclop_cache_and_contiguous_views.md)。

## 缓存复用的是描述符分析

`cached_contiguous_opt` 是静态容器，键哈希来自 sizes、base_sizes、strides、base_strides、storage offset 和 NPU format；命中哈希后，`equalDesc` 还逐项比较这六组描述信息。哈希相同但描述不同会回到普通优化尝试，不能把哈希碰撞直接说成错误复用。

描述匹配时将 `cached_contiguous` 置真，并调用已存 pattern 的 `CachedRun`。未找到哈希项时遍历候选；容器大小达到 `CachedMaxSize=1000000` 后，走普通 `Run` 而不进入该处的新缓存尝试。这个数量门槛约束该调度分支的入缓存方式，不能当作总内存容量、LRU 策略或设备缓存大小。

注册器的默认 `CachedOptimizer` 直接调用普通 `Optimizer`；因此进入 `CachedRun` 不证明每种 pattern 都保存了独立分析结果。以 Permute 实现为例，首次通过识别时保存 perm 与 sizes；再次匹配时复用这些参数，但仍调用 `permute_to_contiguous`，后者仍执行 `npu_transpose_out`。这不是张量数值缓存，也不免除目标分配或必要的数据搬运。

## 用于优化判断

先确认业务走到上述拷贝入口，再观察 view 描述是否重复、目标是否满足完整克隆门控，以及是否转入 `contiguous_d_AsStrided`。Permute 实现提供 `contiguous_d_Transpose` 与 `cached_contiguous_d_Transpose` 标记，可作为所选分支的观测线索；标记出现仍不等于零拷贝或获得性能收益。

将首次形状分析、重复描述分析和实际搬运分别计时，并单独核对数值、别名与分配开销。Host 与设备间拷贝的非阻塞和转换位置另见[Host 与设备拷贝执行](torch_npu_host_device_copy_execution.md)。本卡未审阅全部 pattern 的识别算法、缓存并发安全或底层算子执行结果。

## npu_stride_copy / npu_view_copy 实现层

本卡上文记录了 copy 失败路径落 `npu_stride_copy_out`；本节覆盖 op-plugin 侧三个文件。消费面：torch_npu 两 pin `CopyKernel.cpp`/`TensorShape.cpp`/`TensorFactories.cpp` 调用 `npu_stride_copy(_out)`；`AsStridedKernelNpu.cpp`（133 行主线 / 114 行发布，**pin 有实差**）的 `stride_copy_out_npu_nocheck`：`result.nbytes()<32` 且 storage desc 不 match 时委托 `acl_op::npu_view_copy`（源注释：小于一个 block 的搬运 AsStrided 暂不支持）；**主线新增 `prefer_as_strided_over_view_copy`**（element_size≤1 的整型/bool 输出绕过 view_copy，防其归一化非标准 bool 字节；发布无此分支，1 字节输出发布仍走 view_copy）；`stride.back()>=256` 时按 stride 降序构造 AsStrided+Transpose 组合（源注释：性能优于直接 AsStrided，输出 ND 分配 + `NpuStorageOffsetGuard`）；否则直接 ACE `AsStrided`（`InputWithoutContiguous` + shape/stride 输入）。opapi `AsStridedKernelNpuOpApi.cpp`（主线独有文件，发布无）：`IsAclnnOnly()` 为真时不走 GE AsStrided，改 `self.as_strided` 构造纯元数据视图 + `apply_tensor_without_format` 输出 + `EXEC aclnnInplaceCopy` 物化；源注释明示 A2/A3 等老 SOC 保持 acl_op 行为不变；`DO_COMPATIBILITY(aclnnInplaceCopy→acl_op)`。`ViewcopyKernelNpu.cpp`（121 行，两 pin 去空白等价）：`npu_view_copy` 的 `AicoreValid` 要求 storage_sizes 与 sizes 至多一维差、base_strides 除差维外一致、非 Double、src/dst 尺寸相同；命中时 src 先 `check_match`/`format_contiguous` 再单条 ACE `ViewCopy`（self 与 src 的 size/stride 以 `MEMORY_HOST_COMPILE_INDEPENDENT` 输入、offset 传标量 0），未命中时仍发 ViewCopy 但走全量参数形态。三条路径的性能取舍未测；AclnnOnly 行为为静态推导。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ContiguousOpt.cpp)（primary）：8–10,13–205。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/ContiguousOpt.cpp)（implementation）：8–10,13–205。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ContiguousOpt.h)（implementation）：11–31,33–57。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/ContiguousOpt.h)（implementation）：11–31,33–57。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/contiguous_register.h)（implementation）：18–33,48–73。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/contiguous_register.h)（implementation）：18–33,48–73。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/permute_opt.cpp)（implementation）：10–75。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/permute_opt.cpp)（implementation）：10–75。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/CopyKernel.cpp)（implementation）：410–450。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/CopyKernel.cpp)（implementation）：392–432。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：189–198,213–217。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：125–137,152–158。

- [AsStridedKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AsStridedKernelNpu.cpp)（implementation）：全文 133 行；[发布版](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AsStridedKernelNpu.cpp) 114 行，**缺 prefer_as_strided_over_view_copy 分支**（diff 实差）。
- [AsStridedKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AsStridedKernelNpuOpApi.cpp)（implementation）：全文；发布无同路径文件（负向）。
- [ViewcopyKernelNpu.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ViewcopyKernelNpu.cpp)（implementation）：全文 121 行；发布去空白等价。
