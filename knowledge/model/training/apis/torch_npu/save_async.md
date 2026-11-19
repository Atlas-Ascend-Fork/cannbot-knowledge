---
type: API
title: save_async：后台线程、模型Hook与保存完成边界
description: 保存序列化参数、无返回完成句柄及每设备流复用限制，不把异步返回当检查点落盘。
tags:
- task.lookup
- topic.checkpointing
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-save_async.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-save_async.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-save_async.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/serialization.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/serialization.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# save_async：后台线程、模型Hook与保存完成边界

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 接口

```text
torch_npu.utils.save_async(obj, f, pickle_module=pickle,
    pickle_protocol=DEFAULT_PROTOCOL, _use_new_zipfile_serialization=True,
    _disable_byteorder_record=False, model=None)
```

obj为保存对象，f为路径或二进制文件句柄，pickle_module/protocol指定序列化，model可为需注册反向hook的Module。此处只静态阅读，没有保存、加载或反序列化对象。

## 发布实现与独立主线函数差异

发布465–602行及主线316–482行的相应函数：禁止_use_new_zipfile_serialization=False；调用先检查pickle模块版本，捕获当前device，然后新起线程执行保存，返回None，**不返回Thread/Future或完成句柄**。函数返回不是文件已经完整可读、错误已传回主线程或已持久化的证明。

worker按设备缓存保存流。仅首次创建该设备流时，若model是Module则注册full_backward_hook；后续复用流的调用不会在这段逻辑为新的model重新注册。hook让当时当前流等待保存流，不代表磁盘写入已经完成；首次调用model=None后再传model也不能假定补上hook。并发调用的map/流复用无此处可见的锁或任务排序保证。

worker在保存流中pickle元数据、把非CPU storage转CPU，再写data.pkl及data记录；obj直接作为引用传给线程，不是调用时已深拷贝的原子训练状态。Module pickle期间暂清root的_backward_hooks，成功后恢复，没有在该局部用finally保护异常恢复；不能无条件与参数更新/Hook修改并发。

同data_ptr但不同dtype的storage会被拒绝；主线_save函数还增加删除persistent_id闭包以减小保留，不能用这一注释宣称所有保存路径无内存增长。接收的_disable_byteorder_record在所覆盖的worker实现中没有形成完整与torch.save等价的格式合同。

## 业务验收

保存对象的稳定性、完成与异常收集、文件句柄寿命、I/O和恢复后的多步状态需有明确协议；不以轮询文件存在当完整检查点保证。它与[原生DCP保存/Planner/Stager](../../guides/torch_npu_native_distributed_checkpoint_scope.md)的接口和完成合同分别处理，文档简单训练样例没有完成/恢复断言，本卡不补造未提供的join API。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-save_async.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-save_async.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-save_async.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/serialization.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/serialization.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py)（implementation）
