---
type: Guide
title: TorchNPU ShardedTensor.npu的拷贝、元数据与版本边界
description: 区分ShardedTensor本地拷贝和全局元数据更新，保留device未消费与版本门控差异。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_sharded_tensor_patch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_sharded_tensor_patch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compat/distributed.py
  role: constraint
created_at: '2026-11-11T06:29:26Z'
updated_at: '2026-11-11T06:29:26Z'
platforms: []
---

# TorchNPU ShardedTensor.npu的拷贝、元数据与版本边界

## 固定来源与对象范围

依据PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的_sharded_tensor_patch.py，以及主线_compat/distributed.py中570–586行的附加方法门控。ShardedTensor与DTensor是不同对象；此方法不能直接作为DTensor.redistribute或FSDP2分片切换的合同。没有执行补丁、拷贝、进程组或设备测试。

## 本地数据与两层元数据分别处理

_patched_sharded_tensor_npu只允许torch.preserve_format或torch.contiguous_format，其余memory_format直接报RuntimeError。实现用torch.npu.current_device构造current_device，逐个本地shard调用tensor.npu(device=current_device, non_blocking=..., memory_format=...)，深拷贝各shard.metadata并把placement._device改为current_device，随后构造新的Shard列表。

全局metadata也深拷贝，但仅把原placement.device().type不是npu的条目改为current_device；已是npu的全局条目不会在此逐项重写索引。旧对象元数据不会因这些deepcopy赋值而就地更改。新ShardedTensor由外部_init_from_local_shards_and_global_metadata建立，process_group省略时沿用旧组，否则使用传入组，并保留_init_rrefs。

不能从“本地tensor已在目标设备时可能没有数据移动”推出整个方法没有跨rank协作；构建函数的通信与一致性行为属于外部实现。进程组需要与NPU兼容，这个函数不自动创建或转换通信后端。

## device形参与源码docstring的差别

两版方法签名都接收device，但函数体并未消费它，也没有实现docstring中对device无索引格式的ValueError校验；实际拷贝目标来自当前设备。调用者不能据传入npu:索引保证这个补丁会选中指定卡，应先核对当前设备与本地shard放置。non_blocking只是向底层Tensor.npu透传，不代表数据拷贝或后续通信在返回时已经完成。

只有memory_format有这里显式的入口校验；没有在本函数补出dtype、容量、跨设备复制、所有rank全局元数据一致的完整证明。验收时比较拷贝前后本地数据、global/local placement、process_group以及对象/存储别名，分别验证同步和异步消费顺序。

## 发布导入补丁与主线兼容门控

发布模块定义_apply_sharded_tensor_npu_patch并在导入末尾调用，仅当ShardedTensor没有npu属性时附加本方法，不覆盖已有属性。主线把附加逻辑移到_compat/distributed.py：compat_impl的lt=(2,14)门控函数同样只在缺少npu属性时附加，再由兼容容器apply。源码注释把上游2.14硬件无关化作为原因；本文仅对照这个本地门控，不据注释替代对外部版本实现的验证。

两版方法主体相同，注册入口和适用条件仍应分别核对。高层分片场景见[FSDP/DDP适配](torch_npu_ddp_fsdp_adaptation.md)；[DTensor重分布](torch_npu_dtensor_redistribution_and_registration.md)另处理算子策略，不由本对象的npu方法继承其布局规则。
