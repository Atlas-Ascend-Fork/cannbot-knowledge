---
type: Guide
title: 成员判断与分桶：广播、排序和SearchSorted准备成本
description: 核对isin数量启发式、unique与排序临时，Bucketize的950及类型门控，以及SearchSorted固定版本的校验、标量物化和输出格式准备。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IsInKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BucketizeKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SearchsortedKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IsInKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BucketizeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SearchsortedKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/SearchsortedSideUtil.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/SearchsortedWarnUtil.h
  role: implementation
created_at: '2026-11-12T02:14:38Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 成员判断与分桶：广播、排序和SearchSorted准备成本

`isin(Tensor, Tensor)` 在两个固定版本都由一组ATen操作组成；`bucketize` 主线另有950及之后SoC的直接ACLNN路线。优化时先确认实际入口和分支，再判断排序、广播、标量物化及输出格式整理的成本。

## IsIn的两条算法

| 条件 | 本地行为 | 可见准备成本 |
| --- | --- | --- |
| `elements.numel()==0` | 内部实现直接返回 | functional仍先申请与elements同形状的Bool结果；out仍先执行Bool/shape检查 |
| `test_elements.numel() < int64_t(10.0f * pow(double(elements.numel()), 0.145))` | 先`out.fill_(invert)`，将elements尾部扩一维，与按广播形状view的test逐项比较；普通模式`eq().any(-1)`，invert为`ne().all(-1)`，最后copy到out | 比较与归约的中间结果；不是单个本地`aclnnIsIn`调用。阈值只按元素数量估算，没有dtype、可用内存或形状布局门控 |
| 其余 | 进入排序算法 | `assume_unique=false`分别做unique，保留elements逆映射；true只ravel。两者都cat、稳定排序、申请Bool重复掩码和重排掩码、相邻比较，再通过index_copy恢复顺序并copy到out |

稳定排序用于让拼接时在前的elements在相等值中保持先于test。`invert`改变相邻比较和尾元素填充值；`assume_unique`只省去排序路线的unique，不改变小集合广播路线。非unique路线最后按逆映射恢复；unique路线切取前`elements.numel()`项并view为out形状。这些入口受`VERSION_BETWEEN(V2R1, VERSION_NEWEST)`和对应Schema门控，不扩展到Scalar重载。

## Bucketize的直接路线与版本差异

三种本地重载都先要求boundaries为一维。主线Tensor functional/out在**SoC枚举≥Ascend950、self和boundaries都不是Double、aclnnBucketize及其GetWorkspaceSize符号可见**时调用aclnnBucketize；functional按`out_int32`申请Int或Long，out检查使用out自身dtype再把`out_int32`交SDK，没有在这段代码中显式强制二者对应。

主线条件不满足时，以及发布版全部Tensor调用，均转入`op_api::searchsorted`或其out重载；Scalar两版始终转该路线，并传入空side/sorter。符号探测是静态结果，不证明任意shape/dtype执行成功。直接Bucketize和SearchSorted是不同的调用链，不能用其中一条路线的临时张量行为替另一条背书。

## SearchSorted生成配置与旧ACL消费者

| 路线 | 固定源码中的准备与差异 |
| --- | --- |
| 主线生成OpAPI | Scalar/Tensor/Tensor_out都在`new_params`逗号链中先调用对应validate，再调用非连续告警helper，最后解析`right_eff`；functional输出Int/Long，Scalar输出标量，Tensor输出self形状。Scalar执行aclnnSearchSorteds，Tensor执行aclnnSearchSorted，并传sorter |
| 发布生成OpAPI | Scalar和Tensor_out直接把right及sorter交SDK；Tensor使用`structured_inherit: searchsorted.Tensor_out`。配置没有主线上述validate/warn/side解析逗号链 |
| 旧ACL Tensor/out，两版共有 | `SearchSorted`命令只接sorted_sequence/self，属性为dtype和right。out经CheckOut；若输出格式不匹配，先format_contiguous临时输出，执行后format_fresh_view；functional申请结果再执行 |
| 旧ACL Scalar，两版共有 | 用sorted_sequence dtype将Scalar复制到设备，unsqueeze为一维输入；另申请标量形状结果，再执行命令 |
| 主线旧ACL新增 | validate和warn调用；side存在时由`side=="right"`得到有效right，否则沿用right。发布旧ACL函数虽然接收side/sorter形参，本地没有消费它们；主线旧ACL也未把sorter作为命令输入，不能仅凭签名认定已按sorter重排 |

告警helper检查行主序stride，空/未定义/零维视为连续；非Strided布局委托`is_contiguous()`。Tensor重载检查值、边界和已定义sorter，Scalar只检查边界与sorter，分别WARN_ONCE。**helper只检查并告警，没有在这里实际contiguous复制**；输入复制及完整validate语义需由相应实现另核，不能把告警当成本卡测得的复制次数。这里明确可见的输出临时和Scalar设备物化来自旧ACL消费者，与生成OpAPI分开。

## 固定证据与使用边界

来源是OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布固定点`dedc316708372c9a8bfde4527abd2a94b74840f5`的只读文本；未运行算子、复制或设备实验。SDK内部、完整validate头及公开接口全部参数支持不在本卡推断范围。相关路线可对照[排序与TopK](torch_npu_sort_topk_routing_and_legacy_output_costs.md)，Scalar和兼容分支见[动态选择与Where](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)。

## Evidence

- [IsInKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IsInKernelNpuOpApi.cpp)（primary）：1–132。
- [BucketizeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BucketizeKernelNpuOpApi.cpp)（primary）：1–75。
- [SearchsortedKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SearchsortedKernelNpu.cpp)（primary）：1–107。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1552–1560、4531–4566、5540–5545。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773。
- [IsInKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IsInKernelNpuOpApi.cpp)（implementation）：1–130。
- [BucketizeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BucketizeKernelNpuOpApi.cpp)（implementation）：1–47。
- [SearchsortedKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SearchsortedKernelNpu.cpp)（implementation）：1–100。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1493–1501、4394–4416、5371–5376。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792。
- [SearchsortedSideUtil.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/SearchsortedSideUtil.h)（implementation）：18–25。
- [SearchsortedWarnUtil.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/SearchsortedWarnUtil.h)（implementation）：24–100。
