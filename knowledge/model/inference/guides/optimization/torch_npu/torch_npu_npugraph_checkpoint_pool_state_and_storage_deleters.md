---
type: Guide
title: NPUGraph私有池checkpoint：块状态恢复与Storage deleter迁移
description: 解释Tree新录制前的allocator恢复消费者、原地址segment重建、Storage所有权迁移及校验发生在状态变更之后的边界。
tags:
- task.implementation
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py
  role: implementation
created_at: '2026-11-10T14:49:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# NPUGraph私有池checkpoint：块状态恢复与Storage deleter迁移

## 固定版本与实际消费者

定向核对PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b的默认缓存分配器checkpoint/恢复及C++ Python绑定；另读主线Tree的保存与调用点。未导入上游、执行capture/replay、读取采集数据或验证任何设备组合，整卡保留draft与空平台。

主线Tree在记录输出存活信息后调用_npu_getCheckpointState。进入某些warmup且当前处于EXECUTION时、或需要新record且仍有current_node时，调用apply_checkpoint_execution_state_in_allocator；该方法再调用_npu_setCheckpointPoolState。因此这里是新录制前修正allocator账本的真实消费者，不是每次replay都完整恢复一次的保证。训练代际见[Tree生命周期](../../../../training/guides/torch_npu_npugraph_training_lifecycle.md)，池引用见[原生私有池生命周期](torch_npu_npugraph_private_pool_routing_and_lifetime.md)。

## checkpoint保存块元数据，不保存设备数值

PrivatePoolState保存owner_id和segment列表；每个segment沿块链记录device、stream、stream_uses、size、地址、allocated和gc_count_base等字段。它明确省略use_count及底层分配计数；不是模型权重、Tensor值、RNG或跨进程可移植的文件检查点。

get_private_pool_head_blocks从active_blocks及池内small/large缓存收集segment头，再沿next取BlockState。BlockState构造要求event_count==0；getCheckpointState先调用插入捕获期延迟事件的helper，并不在这个函数中无条件同步所有事件。不能把错误文本“Events should have synchronized”当成已经替调用方完成全设备同步。

## 恢复复用现有segment并重建分配状态

两版setCheckpointPoolState先拒绝freeable池、要求owner_id仍存在，然后执行：

1. 遍历该私有池当前已分配块，要求event_count==0，记录旧地址并调用内部free；再次确认池内块均处于未分配状态。
2. 从缓存small/large建立地址到块的映射；checkpoint中每个segment的首地址必须仍可找到。该过程没有为丢失的旧segment申请一个任意新地址来代替。
3. 按保存的块尺寸调用alloc_found_block拆分并核对地址和size；这里使用当前块重建账本，不按当前max_split_size重新决定checkpoint的切分。
4. 对checkpoint里未分配的块再free，对应已分配块交回allocations_created。扩展段末尾块及合并后size另有放宽检查，不能把普通segment的每个尺寸断言机械套到扩展段。

这份算法只恢复allocator所有权/切分状态，没有从checkpoint读回设备数据。旧地址上的值若被后续replay或新录制覆盖，恢复账本不能还原它；值快照仍要通过[输出重建与clone](../torchair/npugraph_ex_output_reconstruction_and_storage_lifetime.md)所述策略独立处理。

## Storage deleter是恢复合同的一部分

外层NpuCachingAllocator先把旧释放地址从allocated映射移除，再把恢复为allocated的块登记回去，并为其生成带local_raw_delete的DataPtr。_npu_setCheckpointPoolState接收的stale_storages_ptr及待补deleter项是**StorageImpl地址**；helper随后读取Storage的数据地址做匹配，不能直接把任意Tensor.data_ptr整数当成StorageImpl传入。

绑定对stale StorageImpl去重，计算“已释放但未在新状态分配”的地址数量并做数量检查；随后逐个验证stale项的数据地址属于本次freed集合，将标准raw deleter交换为deleteNothing。数量检查及逐项membership检查不等于完整别名、悬空指针或所有Tensor生命周期分析。

待补deleter项按数据地址形成映射；对恢复DataPtr能匹配到的Storage要求当前context为空，再移入DataPtr。没匹配到的DataPtr执行release_context，避免这个临时对象析构时直接删除恢复后的块。同址多Storage会在这个局部map覆盖，不能据此认证任意多个独立StorageImpl自动获得正确共同所有权。

关键顺序是**allocator恢复先发生，数量/旧deleter/新context校验在后**。后续校验失败不代表恢复未发生，也没有在所读绑定中看到自动回滚步骤；这不是可随意试错的事务式公共内存快照接口。此结论限定所列调用链，未推导所有调用都会失败或发生数据错误。

## Tree与版本差异

主线Tree先移除path cached tensors，收集path_live_weakrefs，传空stale列表和存活StorageImpl列表恢复，再按去重后的dead data_ptr调用raw_delete；可选slow-path检查核对池与deleter。空stale是这个已读Tree消费者的选择，不等于底层接口从不需要stale参数，也不代表其他npugraph_ex输出重建可以省略它。

两版所读块恢复核心步骤与Storage deleter迁移结构一致。主线绑定在调用allocator恢复前显式拒绝force-uncached配置；发布版对应绑定没有这一显式检查，不能由缺少guard认证其可用。主线增加恢复日志；本卡不把选定方法的静态一致扩大成整个allocator、全部Tree策略或两版运行兼容相同。

排查新分支录制的内存问题，应同时保留pool/owner id、保存时和恢复时的输出存活集合、已死地址、事件条件、deleter标准状态及恢复后的新分配。只看到checkpoint对象存在，不能证明segment仍存活、输出数值保留、显存已归还或每次replay无Host成本。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（primary）：650–686、821–850、1877–2133、2458–2477、4036–4072。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）：675–711、825–857、1720–1871、1918–1967、2176–2197、3453–3458、3472–3498。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）：344–382、519–580。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Module.cpp)（implementation）：299–335、534–589。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py)（implementation）：1617–1636、2405–2424、2506–2519、3084–3140。
