---
type: Guide
title: TorchNPU FSDP2 增强入口：通信缓冲复用与重计算钩子
description: 区分增强 fully_shard 入口、私有缓存标志、两版通信分配接口及 post-forward 状态，解释缓存释放为何不等于显存归还。
tags:
- task.optimization
- topic.memory
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/fsdp/_add_fsdp_patch.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/fsdp/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/fsdp/_add_fsdp_patch.py
  role: implementation
created_at: '2026-11-10T11:34:13Z'
updated_at: '2026-11-10T11:34:13Z'
platforms: []
---

# TorchNPU FSDP2 增强入口：通信缓冲复用与重计算钩子

## 固定范围与入口

本卡定向审阅 PyTorch/TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的 FSDP2 增强 patch。未导入、训练、建域或运行设备；未核实整套硬件支持，保持 `draft`、空平台。基础 FSDP2、dtype 和文档支持表继续按[DDP/FSDP 接入指南](torch_npu_ddp_fsdp_adaptation.md)核对，不由内部实现扩大产品范围。

`torch_npu.distributed.fsdp` 导出的 `fully_shard` 来自 `_add_fsdp_patch.py`。该包装先调用 `_apply_fsdp_enhance_patch()`，再调用原生 `torch.distributed.fsdp.fully_shard`；全局标志防止重复安装。patch 会修改进程中的 FSDP 私有类和函数，作用范围并非只包含这次传入的一个 module。

这里的明确入口是 TorchNPU 增强包装；不能仅凭调用原生同名函数，便假定已经安装此 patch 或开启通信缓存。缓存标志和重计算钩子也分别判断，不是同一个默认开关。

## 私有缓存标志与缓存对象

主线 `FSDPParamGroup.__init__` 的包装读取 `modules[0]._use_mem_cache`，默认假；随后将该值放到 `_all_gather_comm`、`_reduce_scatter_comm` 对象。发布版则把同一 module 属性复制到每个 `fsdp_param`，通信包装再从首个参数读取。**入口被安装不表示缓存默认启用；两版内部属性落点也不相同。** 本卡记录实现，不把私有属性改写为通用公共配置配方。

两版 `FSDPMemCache` 都用 dtype 索引 buffer 列表与 used 标志。分配时寻找第一个空闲槽；容量不足则新建更大缓冲，足够时返回所需大小的 view。`free(tensor)` 比较底层 storage 指针，只把匹配槽标为空闲，缓存仍持有 Tensor。

因此这里的 free 是“允许后续通信再次取用”，不是把显存归还驱动。调用完成后显存仍常驻不独自证明泄漏；需结合缓存容量、峰值、稳定输入后的分配行为与对象引用检查。`clear()` 才清空该缓存的引用，但这也不等于底层 caching allocator 必定立刻归还驱动。

缓存键只有 dtype，没有在该层按 device 或进程组分区，也未在这些方法中加锁。不能据这个实现宣称支持任意同进程多设备、跨域并发或任意动态布局；大小变化、原生调用的 size 约定及通信顺序仍需按实际软件栈验证。

## 主线按通信对象分配，发布版按进程组临时标志分配

主线替换 `DefaultAllGather.allocate`、`DefaultReduceScatter.allocate`，并同步 `_fsdp_collectives` 和已提前导入它们的 `_fsdp_param_group` 引用。

- AllGather 的分配在 `_use_mem_cache` 为真时进入缓存，否则正常创建 Tensor。
- ReduceScatter 只缓存首次分配；`_mem_cache_flag` 防止同次 foreach reduce 的下一次分配也复用缓存。这是为了缓存通信输入，输出仍正常分配。
- `foreach_reduce` 成功返回后，对 `out[0]` 执行缓存 free，并重置标志。该代码没有包裹异常恢复的 `finally`，不能据正常返回路径证明任何异常后状态都自动恢复。

发布版替换的是 `_fsdp_collectives.allocate_memory`，并在 foreach AllGather/Reduce 包装中设置与清除进程组的临时标志；由于 ProcessGroup 不接受自定义属性，状态保存在 `WeakKeyDictionary`。`from_process_group` 且 backend 支持 tensor 分配时优先使用 backend 分配；不能把发布版描述成与主线相同的通信对象分配接口。

复用路径与 AllGather 释放顺序还依赖原生等待：两版 `_wait_all_gather_streams_on_event` 包装均先调用原函数，再将已延迟释放的上一层输出或当前结果标为空闲。这里没有证明 CPU 已同步全部设备工作；它依赖原生事件与流的顺序，不能为节省等待而单独提前调用缓存 free。

## 重计算期间的 post-forward 状态

两版此组钩子的关键表达式一致：`FSDPParamGroup.post_forward` 首次调用原函数后设 `_skip_post_forward=True`，再次进入时直接返回输出；`post_backward` 在调用原函数之前把它重置为假。源码注释将其用于避免反向重计算时冗余的 AllGather，不能从这一局部逻辑推导任意 checkpoint 组合都恰好少一次通信。

`FSDPState._post_forward` 的包装另维护 forward prefetch 列表的备份/恢复：首次正常路径先把 `_states_to_forward_prefetch` 移到备份，再调用原函数；skip 或 `PRE_BACKWARD` 状态可恢复备份后调用原函数。状态包装仍会调用原 post-forward，不能和 ParamGroup 的直接跳过混为一层。

`hasattr(module, "skip_custom_post_forward")` 会跳过 State 包装的定制分支；这里检查属性是否存在，不检查属性值真假，而且不会在此卸载 ParamGroup 的 patch。不要据字段名自行推导 `False` 等同于未设置，或推导该属性关闭所有增强逻辑。

验证时分别记录实际入口、私有标志传播、分配复用、重计算前反向顺序和 prefetch 列表，再比较数值、通信次数及峰值/稳态显存。缓存命中、钩子安装和模型训练正确是三个不同的验收点，本卡没有收益数据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/fsdp/_add_fsdp_patch.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/fsdp/__init__.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/fsdp/_add_fsdp_patch.py)（implementation）
