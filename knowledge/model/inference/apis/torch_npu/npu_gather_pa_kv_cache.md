---
type: API
title: PA KV缓存读取：原地目标、功能化拷贝与格式分派
description: 补齐PA KV gather原地无返回、functional复制目标缓冲、key_cache格式分派及Meta/测试边界。
tags:
- task.implementation
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherPaKvCacheKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherPaKvCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_gather_pa_kv_cache.py
  role: example
created_at: '2026-11-10T11:46:19Z'
updated_at: '2026-11-10T11:46:19Z'
platforms: []
---

# PA KV缓存读取：原地目标、功能化拷贝与格式分派

## 固定版本与范围

本卡依据OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的GatherPaKvCache包装、Schema及功能化Meta；所述分派、复制与返回合同两版一致。发布来源组合为ascend_26_0_pt28，主线配套未知；未取得覆盖整接口的产品和缓存ABI支持表，保持draft与空平台。

此入口从分页缓存读取到调用方准备的key/value目标缓冲，与[npu_scatter_pa_kv_cache](npu_scatter_pa_kv_cache.md)的写入方向分开。本文只审阅前端合同，没有验证设备kernel、并发更新或分页数值。

## 两个入口消费不同的结果对象

```text
npu_gather_pa_kv_cache(key_cache, value_cache, block_tables, seq_lens,
  key, value, *, seq_offset=None, is_seq_lens_cumsum=False) -> ()

npu_gather_pa_kv_cache_functional(key_cache, value_cache, block_tables,
  seq_lens, key, value, *, seq_offset=None,
  is_seq_lens_cumsum=False) -> (key_out, value_out)
```

原地Schema把key/value分别标为Tensor(a!)/Tensor(b!)，C++直接把两个目标交给`aclnnGatherPaKvCache`，不返回新的K/V二元组。应在调用后消费传入目标，不按functional协议解包。

功能化C++先完整clone **key和value目标缓冲**，在副本上调用同一ACLNN，再返回副本；复制的不是key_cache/value_cache。输入目标的既有内容参与这次clone，不是只用shape创建未初始化结果。优化评估应按目标缓冲的`numel*element_size`计算可见逻辑拷贝体积，另计实际写入、allocator和临时开销。不能把成本误算为复制整个KV cache，也不能为减少复制而擅自改变调用方要求的输入隔离语义。

## PA_NZ选择只检查key_cache真实格式

两个入口都通过get_npu_format(key_cache)读取NPU格式；只有精确等于ACL_FORMAT_FRACTAL_NZ时传cacheMode="PA_NZ"，其他值传"Norm"。这个判定没有同时校验value_cache，也没有显式将数据转NZ或从任意C0变体恢复布局。

包装使用EXEC_NPU_NO_FORMAT_CHECK_CMD，并将block_tables、seq_lens、seq_offset和is_seq_lens_cumsum原样传入。这里没有完整的cache/目标shape、dtype、块ID域、长度前缀、offset或有效token数量检查。连续性、reshape成功或Meta返回shape不能证明物理缓存ABI已匹配；必须先确认两份缓存及目标布局一致，再核对真实分页、offset和有效区协议。

## Meta只提供目标输出规格

两版功能化Meta各用key/value的shape和dtype创建meta设备empty，返回两个规格；不根据block_tables或seq_lens推导实际写入token数量，也不模拟真实clone内容、缓存读写及别名。目标容量和Meta形状不能当作每行均有效的证明，未写入区和并发cache更新需单独验收。

is_seq_lens_cumsum是透传的解释开关，不在此包装自动把逐batch长度改为累计边界。调用方不得只切换布尔值而沿用未经确认的同一数组；本卡没有从薄层定义所有长度/offset及NZ的数学合同。

## 测试参考与接入验收

定向阅读的主线测试入口只有两个FP16方法，装饰器为Ascend950，分别原地和功能化；调用torch.compile的backend="eager"，不构成GE/TorchAir运行记录。示例golden按Norm路径读取，不能证明NZ分派已验证。

参考和驱动还有静态缺陷：Norm参考条件中使用未定义acc_seq_len；驱动计算了cumsum却在is_seq_lens_cumsum=True时仍传seq_lens_list而非cumsum，长度表示不一致；NZ参考在seq_offset=None时把block_table设成0而没有建立block_start。测试还调用torch.npu_gard。这些均未在本次运行复现，不能把测试文件存在当作精度通过。

实际接入应使用独立的小型分页参考，区分长度与累计边界、offset非整块、跨页、尾页和目标未写区；分别核对原地目标变化和functional副本、cache输入及返回对象。先验证非均匀数值和实际物理格式，再比较连续读取、分页gather、目标拷贝及完整注意力阶段的耗时和峰值内存。本次未执行上游、图、设备或性能测试，无新增verified。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherPaKvCacheKernelNpuOpApi.cpp)（primary）

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherPaKvCacheKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定实现来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定实现来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_gather_pa_kv_cache.py)（example）
