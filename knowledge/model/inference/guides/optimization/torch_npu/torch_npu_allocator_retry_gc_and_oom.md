---
type: Guide
title: 缓存分配器申请重试：GC同步、回收层次与OOM计数
description: 追踪默认缓存分配器的缓存查找、GC、分级重试和预拒绝，区分实际同步及num_alloc_retries统计口径。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
created_at: '2026-11-10T14:11:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 缓存分配器申请重试：GC同步、回收层次与OOM计数

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的默认缓存分配器申请与GC/重试消费者，并对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的选定申请/GC段。两版实现有差异，不宣称整分配器等价。平台未知，保持draft、空平台；未执行上游、设备、OOM触发或性能实验。

## 实际入口和三种“已分配”

主线静态初始化把allocator指向caching_allocator；其allocate在非零大小、未走强制uncached分支时调用NpuCachingAllocator::malloc，后者进入对应DeviceCachingAllocator::malloc。raw_alloc/raw_alloc_with_stream也有同类入口，但本卡不覆盖自定义替换分配器或所有私有池实现。

Device malloc先按请求舍入和选pool再找块；底层申请使用alloc_size，可能大于原始orig_size。total_allocated_memory在取得设备segment时增加、release_block时减少，不是只统计当前活跃Tensor的memory_allocated。缓存池持有量、活跃分配和设备总可用量分别解释，不能把同名“allocated”串成一项。

## 先复用，再逐级尝试申请

主线的选定调用顺序是：

1. 处理符合条件的跨流事件，查现有pool；未命中时调用free-memory callbacks，回调报告释放后再查一次。
2. 仍未命中，且allowed_memory_maximum有值、GC阈值大于0时，尝试GC；随后alloc_block(...,isRetry=False)。
3. 普通失败先尝试已选择use-on-OOM的池回退，再尝试释放足够可用缓存块并以isRetry=False申请；预防拒绝则跳过这些重试。
4. 仍失败、未预拒绝且当前非捕获上下文时，释放锁调用npuSynchronizeDevice(true)，清workspace池，release_cached_blocks后以isRetry=True最后尝试。

释放足够块的分支在max_split_size为默认无限值时直接返回false；进入其非默认候选搜索后会显式npuSynchronizeDevice，不能把它只看成无等待的容器操作。该路径选同流候选大块，不表示能清理任意活跃Tensor或全部私有池。

发布所读段同样有缓存查找、按条件GC、释放可用缓存后再申请、非捕获时同步设备/清workspace/释放缓存的最后重试；没有主线这一处use-on-OOM池尝试及预拒绝分支。不能据主线的新选项回推旧发布行为。

## GC有真实同步，年龄不是经过的秒数

GC目标按`total_allocated_memory - threshold*allowed_memory_maximum`计算；未超过阈值或large pool没有非split候选便返回。主线构造时调用setMemoryFraction；fraction=1会使allowed_memory_maximum为空，fraction<1才写额度。这里记录实际调用门控，不把设置了GC阈值解释成每次分配必定GC；配置产品/版本仍见[分配器选项](../torch_npu_allocator_options.md)。

候选存在后，两版所读GC函数都释放锁并调用`npuSynchronizeDevice(true)`，然后按平均gc_count选择非split大块回收。函数注释称不强制同步，不能据该注释宣称当前实现无同步或必定低延迟。

主线get_free_block在GC条件生效时给所查pool内空闲块gc_count加1，被选中者归零；因此年龄反映查找/复用间隔，不是墙钟时间。GC每轮选择gc_count>=平均值的块，内层不在刚达到目标时立即停止，可以超出目标。它回收缓存候选，不会把仍活跃或等待事件的任意分配直接变成可释放内存。

## 回缓存、还驱动与捕获池分开

主线release_cached_blocks在默认池且非捕获时先同步未完成事件，再释放large/small池的可释放块；私有池仅按该函数的freeable/use_count与指定pool分支处理。release_blocks对普通segment只释放没有前后切分邻居的块；扩展段走unmap/物理handle分支，不能把这层概括成任何Tensor都立即aclrtFree。

普通release_block最终调用所属私有allocator.raw_delete或aclrtFree，并降低total_allocated_memory及reserved统计。Python对象结束、块回到缓存池、segment还驱动是不同时间点。empty_cache与OOM错误文本不能独自证明所有活跃/捕获/通信内存已经释放；OOM观察范围见[内存快照](torch_npu_oom_memory_snapshot.md)。

## 计数和预拒绝不是同一次事件

| 计数/分支 | 所选主线消费者 |
| --- | --- |
| num_alloc_retries | 仅alloc_block的isRetry=True分支加1；前面的首次申请和释放部分缓存后的isRetry=False再申请不加，因此不是全部driver malloc调用数或全部失败次数。 |
| num_ooms | 最终普通内存申请错误路径加1并记录OOM/调用观察者；成功重试不必形成最终OOM。 |
| num_oom_rejections | throw_on_npumalloc_oom条件下的预防额度拒绝加1，设置rejected，Device malloc返回nullptr；外层malloc再抛OutOfMemoryError。它跳过普通重试和普通OOM观察者分支。 |

显式allowed_memory_maximum额度检查发生在预防拒绝检查之前，失败仍属普通申请错误；配置是否生效及快照限制沿用[预防OOM文档](torch_npu_memory_debug_and_rejection.md)。预拒绝还可异步通知rejection observers，不把通知提交当成回调已完成。本卡没有运行注册回调或断言所有分配器都服从这些计数。

分析显存抖动或时延尖峰时，联合看原始/舍入/segment大小、空闲块复用、事件积压、GC与最后重试同步，再按准确计数判断。一次申请最终成功也可能支付同步和回收成本；计数为0不排除早期额外申请。

本卡未完整审阅use-on-OOM池选择、全部扩展段映射、配额配置解析或OOM快照写入。没有给出调参收益、跨流安全或硬件支持的新运行保证。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（primary）：定向范围 1052–1057, 1203–1397, 1416–1429, 1753–1761, 2828–2903, 2906–3116, 3120–3169, 3182–3227, 3248–3288, 3366–3395, 3650–3684, 4126–4155, 4225–4244, 4412–4419。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）：定向范围 1156–1270, 2563–2629, 2631–2678, 2752–2776。
