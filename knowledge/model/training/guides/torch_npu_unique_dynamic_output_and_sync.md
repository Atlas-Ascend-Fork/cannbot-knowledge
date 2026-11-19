---
type: Guide
title: Unique动态输出：上界申请、同步与ViewShape回读
description: 说明Unique2、UniqueDim和UniqueConsecutive的输出上界、inverse/counts准备、同步查询及版本守卫。
tags:
- task.optimization
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/Unique2KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UniqueDimKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UniqueConsecutiveKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/Unique2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UniqueDimKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UniqueConsecutiveKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-12T02:29:43Z'
updated_at: '2026-11-12T02:29:43Z'
platforms: []
---

# Unique动态输出：上界申请、同步与ViewShape回读

三个Unique包装都先按输入规模申请输出，再进入显式同步执行路径，随后读取SDK返回的view shape并resize。关闭inverse/counts并不总能省掉对应的准备或查询；应把辅助输出与同步计入整段去重开销。

| 包装 | 执行前申请 | 执行后调整 |
| --- | --- | --- |
| `_unique2`，两版本守卫 | y上界为self.numel；`return_inverse || return_counts`时申请self形状Long inverse，否则空Long；counts按return_counts申请numel或空Long | aclnnUnique2同步后查询Get<4>的y形状、resize y；请求counts才按同形状resize counts，最后delete[]查询指针 |
| `_unique2`，V2R2及之后 | 申请规则相同 | 即使只请求counts、未请求inverse，也先申请并传入inverse；执行后再把inverse替换成空Long。V2R1分支没有这个末尾替换 |
| `unique_dim` | y按self规模申请；inverse和counts都按self.size(dim)申请Long，没有用两个返回标志跳过这些申请 | 同步调用参数为self、sorted、return_inverse、dim和三个输出；本地调用列表没有return_counts参数。分别查询Get<4>和Get<6>，resize y与counts |
| `unique_consecutive` | 有dim时y按self规模，否则按numel；inverse按return_inverse申请选中轴长度或self形状，否则空Long；counts同理按轴长度或numel/空Long | 无dim传入整数哨兵1000；同步后仍分别查询并resize y及counts，没有用return_counts包住第二次查询 |

`unique_dim`的空尺寸分支在输出申请和SDK调用前：选中轴size为0时，只允许全shape恰有一个零尺寸，返回同shape空y及两个空Long；选中轴非零但其他轴为0则报错。它和`unique_consecutive`本地只显式检查dim小于rank，不能把这条检查描述为完整负轴/rank校验。

两次查询的包装复用同一个`view_dims`变量，在第二次查询前没有本地delete[]，仅最后释放最终指针。错误检查或resize抛错的路径也没有局部RAII清理；因此这里只确认源码写出的释放位置，不保证每个查询缓冲都独立释放，也不在未展开SDK所有权语义时宣称已复现泄漏。

每个函数静态缓存aclGetViewShape地址，缺符号会检查失败；SDK返回非零也会检查失败。两版Unique2/Dim/Consecutive完整活动代码与非namespace注释相同，差异为排版和namespace尾注释；V2R1与V2R2差异是各快照内部的版本守卫，不能写成只有主线的修复。

## 固定证据与成本边界

来源固定为OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`；同步宏复用此前固定来源审阅，见[动态选择同步](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)。先进入DO_COMPATIBILITY的旧ACL分支不由这里推断其同步次数。本文没有执行算子或设备实验，不把resize后的逻辑shape当作最初只申请这么少内存，也不保证底层分配器立即归还上界空间。公共产品/类型表见[torch索引与统计](torch_npu_native_torch_index_reduce_scope.md)。

## Evidence

- [Unique2KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/Unique2KernelNpuOpApi.cpp)（primary）：1–105。
- [UniqueDimKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UniqueDimKernelNpuOpApi.cpp)（primary）：1–85。
- [UniqueConsecutiveKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UniqueConsecutiveKernelNpuOpApi.cpp)（primary）：1–87。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：768–770、5230–5236。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：744–812。
- [Unique2KernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/Unique2KernelNpuOpApi.cpp)（implementation）：1–111。
- [UniqueDimKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UniqueDimKernelNpuOpApi.cpp)（implementation）：1–79。
- [UniqueConsecutiveKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UniqueConsecutiveKernelNpuOpApi.cpp)（implementation）：1–77。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：743–745、5063–5069。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：677–736。
