---
type: Guide
title: Host扩展段保活与清缓存：事件队列和整段回收
description: 解释Host expandable的记录流、延后复用与host_empty_cache消费者，保留查询异常、部分段和版本统计字段差异。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/CachingHostAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.h
  role: implementation
created_at: '2026-11-10T14:30:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Host扩展段保活与清缓存：事件队列和整段回收

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`本地NPUExpandableHostAllocatorImpl的事件、空闲块和清缓存消费者，并对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的选定段。record_event、block_free、release_cached_blocks三组选定方法非注释token相同；统计字段及基类接口有变化，不扩展为整Host allocator等价。平台未知，保持draft、空平台；未执行上游、设备或Host内存实验。

## 真实入口与独立Host实现

PrivateUse1 Host allocator首次setAllocator用call_once选择普通或expandable实现。选中expandable后，allocate/free/record_event/empty_cache进入本地override；它不是Device缓存分配器，也不是[copy_指针分类](torch_npu_host_device_copy_execution.md)本身。

本地allocate对零大小返回空，否则先process_events，再按size+32并向512字节对齐准备请求，寻找可用块或映射；失败时尝试release_cached_blocks再申请。成功后标allocated_、保存requested_size与ptr→block映射，返回ptr和block context。这里描述本地准备/复用，不保证全部映射/失败恢复或任意输入规模可用。

## 记录使用不等于已经完成搬运

record_event尝试核对context/ptr对应的已知块，要求命中块仍allocated，把stream加入集合后返回True；未命中返回False，不取得任意外部指针的所有权。这一步记录使用流，事件是在随后free时处理；它不建立数据生产者与消费者之间所需的依赖。

free先标块未allocated。没有记录流则直接free_expandable_block；有记录流时逐流record事件、增加event_count_并清流集合，把(event,block)放入队列。free_expandable_block要求未allocated且event_count_=0，合并可用邻块后放入缓存空闲集合；这里没有把每次Tensor析构都直接退还物理Host页。

## 查询队列与异常清理

process_events从队列后端取当前事件查询：未完成则放回并立即返回，本轮不越过它继续查后续项。事件完成后降低块event_count_，最后一个完成且块未allocated才归入空闲缓存。allocate与release_cached_blocks都调用这一处理，所以对象释放后可复用时间还取决于实际事件进展。

所读process_events捕获query异常后记日志并按completed=True继续清理；query_event override也有类似处理。它们是异常处理代码，不是设备使用已经正确完成的证明；不能据事件被移出或empty_cache返回认证传输数值正确。真实错误和异步使用仍需在对应运行上下文处理，未执行这些路径。

## host_empty_cache并非无条件等待所有使用

主线公开host_empty_cache→_npu_hostEmptyCache→Host allocator.empty_cache→本地release_cached_blocks。所读Python/C++入口未额外加入npuSynchronizeDevice；release_cached_blocks仅先process_events，再release_blocks并返回True，没有在此循环等待全部未完成事件。

源码注释写调用release_cached_blocks前应同步设备，但这句不等于所查公开调用链已经执行同步。也不能据这里没有显式DeviceSync推导底层Unmap/FreePhysical必定无等待；ACL内部开销未测量。与[Device缓存回收](torch_npu_allocator_stream_reclaim_and_lazy_order.md)的显式同步事件路径区分。

release_blocks只遍历已经可用的缓存块；unmap只归还该空闲区间内部完整的segment_size物理段，边缘不足整段可以保留，实际unmap size为0时直接返回。当前segment_size常量为20971520字节；逻辑释放小块不等于立刻退还同等物理字节。

Unmap成功后调用AclrtUnmapMem/FreePhysical；整个虚拟segment都未映射且可归并成完整块时，才删除segment并释放地址保留。不能把host_empty_cache解释成释放活跃、仍等待事件或任意部分页；返回True只表这段函数到达返回，不证明Host占用降为零。

## 统计字段按版本和阶段消费

主线alloc_found_block/free_expandable_block增加/减少active_bytes，物理映射/unmap增加/减少allocated_bytes。发布所读对应逻辑块申请/空闲段则增加/减少allocated_bytes；本卡未审完其全部物理统计。因此不能把两版同名Host统计字段一律当成同一逻辑活跃量或套用Device allocated/reserved口径。

缓存/舍入阈值的配置文档已说明Host expandable路径有独立逻辑；这里的size+32及512对齐来自本地实现，不把普通ATen缓存阈值getter当成这一allocate的实际消费。背景线程getter或类继承也不证明这套本地process_events自动由同样线程调度。

诊断时先固定实际Host实现和版本，记录申请跨度、已记录流、事件完成、逻辑空闲与物理段归还，再比较host_empty_cache前后；只看最终CPU Tensor消失、is_pinned或单个统计不能替代这条寿命链。

本卡未完整审阅所有split/merge合法性、地址预留/扩展映射回滚、上游ATen Host pool或图捕获组合；没有新增支持矩阵、异常安全认证、性能数字或verified。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.cpp)（primary）：定向范围 39–41, 475–511, 575–639, 664–693, 717–751, 762–843, 877–961, 964–998, 1083–1092, 1133–1179, 1190–1217, 1246–1274。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/CachingHostAllocator.cpp)（implementation）：定向范围 411–449, 613–643, 667–702, 829–899, 1097–1144。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py)（implementation）：定向范围 184–189。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）：定向范围 1141–1145。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.h)（implementation）：定向范围 40–50。
