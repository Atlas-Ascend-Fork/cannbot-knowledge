---
type: Guide
title: Eager DVM融合提交与输出分配重入
description: 连接kernel池、流切换、输出分配保护及TaskQueue两条codegen/workspace/launch顺序，说明正常清理与待验证失败路径。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_control.h
  role: implementation
created_at: '2026-11-11T02:59:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Eager DVM融合提交与输出分配重入

## 固定来源

仅覆盖OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的Eager融合管理器与kernel本地实现。平台及发布配套待核，保持draft和空平台。本次只读源码。开关与线程使用条件沿用[Eager DVM融合](torch_npu_eager_lazy_fusion.md)。

## 管理器和流

Manager::Get对当前stream相同的待提交kernel直接复用，stream变化先Flush，再从池或new取得kernel，赋予递增id、当前stream与本次dump标志。构造时使用kEager、kUnifyWS并预留输入/输出容器。正常结束后FreeKernel用锁将对象放回池，管理器析构删除池内对象。Get/当前图状态采用进程级对象，池上的锁只覆盖所读池操作。

SetLazyFusionDisabled通过原子exchange取得旧值，状态发生变化才调用Flush。Manager::SetDumpEnabled在状态变化时先Flush，再保存新dump状态。Manager::Flush先清空current_再调用kernel Flush，输出分配保护生效时先返回并保留current_。

## 输出分配如何防止半成图被回收

返回新Tensor的Output重载先用AllocationGuard增加output_allocation_depth_，保存graph id，再调用apply_tensor_without_format。申请完成后CheckOutputAllocationState要求id相同、flushed_为False且管理器current_仍为本kernel，然后登记输出。RAII在离开该重载时减少深度。

内存申请触发GC或重试同步、再进入Manager::Flush时，IsAllocatingOutput会使当前图留待输出登记完成。所读检查还会拒绝申请期间已经变化的图状态。实际allocator重入、并发和异常组合仍需在具体软件栈运行验证。

## 工作区与提交阶段

Alloc在TaskQueue模式等于2时使用allocate_workspace(size, stream_)，其他分支使用unsafe_empty_workspace。Tensor暂存在workspace_，地址交给DVM CodeGen。工作区分配器和输入引用释放必须结合下表的实际先后理解。

| 阶段 | TaskQueue等于2 | 其他所读分支 |
| --- | --- | --- |
| Store生成 | 标记flushed_并生成未skip且Storage存活的Store | 相同 |
| codegen前 | 调用线程ClearGraphRefs | 调用线程先CodeGenAndDump，输入强引用此时仍在 |
| codegen与Launch | RunOpApiV2回调依次CodeGenAndDump、Launch | codegen后ClearGraphRefs、workspace_.clear，再由回调Launch |
| 正常回调尾部 | workspace_.clear后ClearRuntimeState | ClearRuntimeState |

源码说明其他分支先codegen的动机是避免释放短生命周期输入后，工作区申请立即复用同一块内存。这里记录已实现顺序，工作区释放后的实际设备生命周期依赖相应分配器和执行队列。

## 清理和返回

ClearGraphRefs清空输入Storage上的lazy_fusion_data_、释放Load的强引用，清空仍存活输出Storage的登记，复位输出、dump及缓存使用计数。Load、DvmOp和shape对象保存在kernel容器中供后续复用，kernel析构再删除相应对象。ShapeWithRef使用op_infer::SIZE固定数组，本地Update循环没有附加容量检查，尺寸准入需沿具体handler核对。

LazyFusionKernel::Flush在flushed_已为True时直接返回。无输出的Flush直接Clear。正常Launch返回后，ClearRuntimeState清理DVM内部状态和dump缓冲，复位flushed_并归池。所读CodeGen和Launch周围没有为所有异常建立统一回滚结构，失败后的对象回收和重试条件保留为外层执行器待核问题。

Launch按需调用UseStreamResInCurrentThread并把stream_传给DVM。synchronize调试选项额外调用带超时的stream同步，同步失败记录日志，最终返回值仍取自DVM Launch。正常提交与调试同步应分别观察。

采用时核对输出申请期间的重入、queue模式、stream切换、对象归池及非零工作区的真实生命周期，先比较数值，再统计Host提交、codegen和设备执行开销。图内别名复用见[Tensor复用与别名](torch_npu_eager_dvm_metadata_alias_and_view_lifetime.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp)（primary），读取范围 1–792。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h)（implementation），读取范围 1–451。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_control.h)（implementation），读取范围 1–24。
