---
type: Guide
title: 缓存分配器跨流回收：事件完成、捕获延后与选块顺序
description: 解释FREE_REQUESTED到可复用缓存的事件链，区分lazy回收时机及主线/发布选块次序，避免把释放对象等同设备归还。
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

# 缓存分配器跨流回收：事件完成、捕获延后与选块顺序

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`默认缓存分配器的stream记录、free、事件回收与malloc选块，并对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的对应选定段。两版insert_events/process_events所比函数非注释token相同；malloc/free的捕获门控与lazy顺序有变化，不推定整分配器相同。平台未知，保持draft、空平台；没有执行设备或并发实验。

## 入口和生命周期记录的范围

主线默认allocator经allocate→DeviceCachingAllocator::malloc产生带local_raw_delete的DataPtr；释放时该deleter调用caching_allocator.free，再进入设备free。recordStream的公开包装只处理非空、deleter等于local_raw_delete的地址，找到块后记录stream；其他来源直接返回。不能因此推定IPC或外部allocator没有保护，它们只不在本段默认块记录合同内。

Device recordStream把流加入block.stream_uses，捕获上下文还另记捕获期间流集合。它记录使用事实，不执行这里未出现的流间等待，也不替调用方建立数据生产/消费依赖。已有通信Work保护沿用[训练通信内存复用](../../../../training/guides/torch_npu_collective_memory_reuse.md)。

## free先降低allocated，块未必可复用

Device free先将allocated=False，降低allocation/allocated_bytes并记FREE_REQUESTED；如果还有记录流且NPU系统已初始化，非捕获时insert_events，捕获时把块放入deferred列表。上述条件不成立时直接free_block。

insert_events把stream_uses移出，为每条流record事件、增加event_count并排到按流分组的队列。process_events先处理捕获后延期项，再从每条流队首查询：未完成就停止该流队列，继续其他流；完成则减event_count，直到该块所有事件都完成才free_block。后面的事件可能因同流队首未完成而延后，不是全局按最早时间完成顺序。

free_block要求未allocated且event_count=0，记录FREE_COMPLETED、尝试合并相邻可合并块，将块放入pool空闲集合，并降低active/requested统计。这个函数不直接aclrtFree，因此“可在缓存中复用”仍不是“还给驱动”。allocated_bytes已经下降而active/reserved仍高，可以来自等待事件或缓存，不单独证明泄漏；字段见[内存计数](torch_npu_memory_counters.md)。

## 捕获门控按固定版本解释

主线在相关路径调用is_capture_context：设备活动捕获计数为0时快速false，否则查询当前流capture状态，查询出错也返回false。它区分当前调用流状态，而非单凭存在私有分配池就认定捕获；这仍是静态分支，不认证底层查询失败后的任意组合安全。

发布所读malloc/free/recordStream使用captures_underway是否为空作门控，不能将主线判断机械回写发布。延期处理会移除捕获期间记下的流使用，再给剩余流插事件；其正确性仍依赖真实捕获依赖合同，本卡没有运行重放、参数/KV变更或异常恢复。

普通process_events查询完成状态；另有synchronize_and_free_events显式同步事件再回收，不能把所有“回收事件”都理解为只查询、无等待。捕获池和对象生命周期前提需与[图池指南](../torchair/npugraph_ex_memory_pool_and_clone.md)分别核对。

## lazy回收阈值不放宽完成条件

两固定快照的kLazyQuerySize为512。未开lazy时，在所选非捕获条件下malloc先process_events再选块；开启lazy后，命中缓存且队列积压不大可以省去该次查询。该开关改变回收时机，不把未完成事件直接判完成，也不保证所有负载都降低显存或时延。

| 版本 | lazy路径关键顺序 |
| --- | --- |
| 发布 | 先get_free_block/回调搜索，再在未命中或队列事件总数>512时process_events；原先未命中才再查块。 |
| 主线 | 积压>512时先process_events再选块；未命中且本次尚未reap时再process_events并重查。reaped标志避免同次malloc重复事件处理。 |

主线get_free_block选中后把块从pool中移出，真正allocated=True在后续alloc_found_block才设置。free_block又可能合并并删除相邻未allocated、无事件/流使用的块。因此不能认为“从pool拿到指针”就已完成其分配生命周期；主线注释解释先回收再选块是为了避免这段未完成标记窗口与邻块合并相遇。

这里直接确认两版顺序及相关标记/合并条件，不把源码注释写成已在本机复现的发布崩溃、所有并发都安全或性能收益证明。size、stream、split与capture池限制仍影响最终是否能复用，不能只看空闲字节总和。

## 验证与边界

对内存延迟回收问题，固定真正的allocator、DataPtr来源、设备和流，区分FREE_REQUESTED、事件插入/查询、FREE_COMPLETED和segment释放；再看lazy阈值和捕获状态。stream记录是寿命追踪，与流间计算依赖分开；不要靠删除记录或提前归还来掩盖未完成使用。

本卡只闭合所列默认缓存块事件/选块消费者，未完整审阅所有eraseStream、IPC/外部分配器、跨线程并发、split策略或扩展段物理回收。配置开关说明复用[分配器选项](../torch_npu_allocator_options.md)，没有新增verified或运行性能结论。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（primary）：定向范围 119–119, 1203–1283, 1468–1488, 1528–1543, 1592–1635, 1712–1717, 2374–2406, 2628–2683, 2703–2727, 2828–2841, 2882–2891, 3404–3445, 3459–3551, 3657–3710, 3907–3926, 4126–4155, 4370–4372, 4412–4419。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）：定向范围 109–109, 1156–1214, 1445–1483, 1557–1563, 2984–3063。
