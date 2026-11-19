---
type: Guide
title: 发布快照训练清单：通信、FSDP、优化器与重计算
description: 区分类/方法级Y与空白，保留FP16与BF16通信钩子差异及未验证弹性、TP和DCP表。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md
  role: constraint
created_at: '2026-11-09T17:27:10Z'
updated_at: '2026-11-09T17:27:10Z'
platforms: []
---

# 发布快照训练清单：通信、FSDP、优化器与重计算

## 来源与版本缺口

依据PyTorch/TorchNPU发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内docs/api/torch_npu_apis.md。它位于锁定发布源码内，但页面没有逐项的PyTorch小版本、CANN/包post、产品或参数支持矩阵，不能仅由父提交推为26.0/PT2.8所有组合的运行保证；本卡保留draft、platforms为空，待独立版本/硬件证据消解。

原表Y表示该文件声称兼容，仍须看限制；兼容性留空明确表示尚未验证。空白不是显式不支持，Y也不是本知识库新增verified或完整模型验收。类、方法、原地形式和同名函数逐行消费，不按父类、别名、相邻项或主线其他版本补全；这里没有执行/导入上游、编译、启动进程或设备实验。

## 通信入口与组件分层

init_process_group、Store/TCPStore/HashStore/FileStore/PrefixStore与已列Store方法、分组/rank查询、send/recv、broadcast/all_reduce/all_gather/reduce_scatter/all_to_all及部分对象通信列Y。isend/irecv/batch_isend_irecv、reduce/gather/scatter、scatter_object_list/monitored_barrier和旧*_multigpu条目留空；Y没有给完整dtype、async完成、后端/拓扑或对象序列化合同。

DDP GradBucket列出的属性/方法、allreduce_hook、FP16压缩及wrapper、PowerSGD及batched形式、noop_hook列Y；BF16压缩及wrapper留空。不能由FP16支持推定BF16压缩已验证，性能/收敛也须另验。

Join/Joinable/JoinHook及main_hook/post_hook列Y，notify_join_context、join_device/join_hook/join_process_group留空。整张Elastic表105项、TP表15项、DCP表40项、Pipeline表6项和RPC表39项均留空，不由其他组件Y补全启动、弹性重启、分片保存或远程Autograd的完整执行流程。

## FSDP与优化器不能按父对象继承

FSDP类本身、no_sync、状态字典转换/聚合、MixedPrecision和state dict配置多留空；apply/clip_grad_norm_/forward/named_buffers/named_parameters/register_comm_hook，以及BackwardPrefetch/ShardingStrategy/CPUOffload列Y。这不是完整FSDP生命周期已验证，也不能把MixedPrecision留空改成绝对不支持。

ZeroRedundancyOptimizer类、add_param_group/state_dict列Y，step/load_state_dict/consolidate_state_dict/join_hook留空；PostLocalSGDOptimizer及其列出的step/状态方法有Y。分布式优化器与常规优化器、构造/更新/保存/恢复四阶段分别验收。

常规Optimizer的基础方法、Adadelta/Adagrad/Adam的部分参数组与状态方法列Y，但Adam/AdamW/SGD等类及step并没有因此都被标Y。Adadelta、Rprop及若干scheduler行带接口级四类型泛化文字，调度器没有给Tensor参数表，不能把它解释成学习率只能是四种Tensor或任意优化器状态都支持这些类型。SequentialLR类有Y，其get_last_lr/load_state_dict/print_lr/state_dict留空，保留方法差异。

## Autograd与重计算的窄证据

Function、grad、forward_ad的dual_level/make_dual/unpack_dual、functional Jacobian/Hessian/JVP/VJP、saved_tensors hooks、save_on_cpu、异常检测、gradcheck/gradgradcheck及部分Profiler方法列Y。autograd.backward、Function.forward/backward/jvp/vmap及部分Node方法留空，不从父类Y补齐。

checkpoint与checkpoint_sequential均Y但这份表没有FP32专属说明、随机/上下文/反向或图后端条件；主线其他版本的sequential限制不回填为本页原文，也不由本页无说明反向消除当前部署版本的限制。

## 所属表的证据范围

| 表 | Y条目 | 留空条目 | 有限制条目 |
| --- | --- | --- | --- |
| torch.autograd | 28 | 14 | 0 |
| torch.distributed | 45 | 15 | 0 |
| torch.distributed.algorithms.join | 5 | 4 | 0 |
| torch.distributed.elastic | 0 | 105 | 0 |
| torch.distributed.fsdp | 9 | 26 | 0 |
| torch.distributed.optim | 7 | 6 | 0 |
| torch.distributed.tensor.parallel | 0 | 15 | 0 |
| torch.distributed.checkpoint | 0 | 40 | 0 |
| torch.optim | 61 | 172 | 42 |
| DDP Communication Hooks | 14 | 4 | 0 |
| Pipeline Parallelism | 0 | 6 | 0 |
| Distributed RPC Framework | 0 | 39 | 0 |
| torch.utils.checkpoint | 2 | 0 | 0 |

计数是该页目录记录数量，不是运行通过率；未给局部参数/默认值/组合条件时保持未知。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）
