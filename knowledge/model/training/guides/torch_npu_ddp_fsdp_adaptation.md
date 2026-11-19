---
type: Guide
title: TorchNPU DDP 与 FSDP2：基础接入和配套核验
description: 限定固定主线 PyTorch2.14 清单中的 A2/A3与950DT 基础 DDP/FSDP2 接入，说明输入精度、全局 rank 和复杂组合边界。
tags:
- task.design
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/parallelism_strategy/ddp_introduction.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/parallelism_strategy/fsdp_introduction.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/distributed_overview.md
  role: supporting
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-fsdp-fully_shard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-fsdp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-pipelining.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/distributed_overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/parallelism_strategy/ddp_introduction.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/parallelism_strategy/fsdp_introduction.md
  role: constraint
created_at: '2026-11-09T02:11:09Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# TorchNPU DDP 与 FSDP2：基础接入和配套核验

## 版本与范围

依据固定 TorchNPU 主线 ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf 的 DDP/FSDP2 指南及 PyTorch2.14 逐接口产品清单，覆盖 A2/A3 与950DT的基础接入（950DT逐接口依据见后文）；不是 26.0/PyTorch2.8 的配套声明，也不覆盖任意并行策略或高级参数组合。

## 接入要点

两条路线都以 hccl 为通信后端，import torch_npu 完成相应适配。每进程绑定一张 NPU，设备相关调用仍用 NPU。DDP 保留每进程完整模型，通过反向梯度同步训练，输入分片由数据采样策略保证，不能指望 DDP 自动切分数据。

FSDP2 的 fully_shard 路线以分片参数减少常驻内存，来源示例先逐层 fully_shard，再包装根模型。实际 reshard_after_forward、预取、精度、专家 mesh、checkpoint 和优化器策略必须核对训练框架自身的配置，不能从简介的“计算后释放”推定所有策略都如此。

## 验证与模型关联

先确认实际 PyTorch 接口可用，再比较参数、梯度与优化器更新的跨 rank 一致性，检查数据划分、checkpoint 恢复和分片后内存。TorchNPU 基础接入不代替 TorchTitan/MindSpeed 的模型装配契约。本卡未执行训练或设备验证。

- [现有 FSDP2 策略、mesh 与预取知识](../concepts/parallelism/fsdp.md)


## 分片原语和证据缺口

同提交分布式总述还说明 DTensor 表达 Shard/Replicate 等布局、DeviceMesh 使用 device_type="npu" 管理通信域。高层能力声明不能替代各组合的平台/版本矩阵；基础接入的逐接口证据见下节，TP/PP、checkpoint 和混合策略仍须另核对，不据“用法与社区一致”认定全部已验证。

## 清单限制与多节点身份

同一固定提交的 PyTorch2.14 清单分别明确 DDP 和 fully_shard 的产品范围，覆盖 A2/A3；fully_shard 的 input 仅 BF16/FP16/FP32。平台按下述补充逐接口证据覆盖A2/A3与950DT，仍无本地运行验证。

此清单不证明所有 reshard、预取、checkpoint、TP/PP 组合或特定训练框架的装配均已验证。DDP、FSDP1 的 FullyShardedDataParallel 与 FSDP2 的 fully_shard 也不能按类名近似互换。

来源 FSDP2 示例把 LOCAL_RANK 同时传为通信 rank；多节点中不能照抄：LOCAL_RANK 用于本节点设备选择，通信的全局 rank 应取实际启动器提供的全局身份，并保持 world_size、节点和组成员一致。示例能描述单机流程，不证明所有多节点启动配置正确。

- [AMP 精度上下文](torch_npu_autocast_and_custom_autograd.md)
- [融合优化器的参数类型限制](torch_npu_fused_optimizer_lifecycle.md)

## PyTorch2.14的950DT及FSDP1边界

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.14原生清单还明确列950DT：DDP及join/join_hook/no_sync，FSDP2 fully_shard及FSDPModule.unshard。DDP.register_comm_hook中文列950支持、英文明确950不支持，按[通信钩子指南](torch_npu_ddp_communication_hooks.md)保留该语言分歧。这是逐接口支持证据，不是950PR或任意分片/精度组合的证明。本卡将基础入口范围补齐到950DT；A2/A3原有约束继续适用。

FSDP1的FullyShardedDataParallel同页列A2/A3/950DT、input仅BF16/FP16/FP32，建议显式device_id=torch.device("npu:本地设备号")。不要把示例npu:0固定用于所有rank，也不把FSDP1的MixedPrecision/CPUOffload对象直接替代FSDP2策略对象。

FSDP1的apply、clip_grad_norm_、forward、named_buffers、named_parameters、no_sync、register_comm_hook及BackwardPrefetch/ShardingStrategy/MixedPrecision/CPUOffload均列950DT；check_is_root、fsdp_modules、full_optim_state_dict、optim_state_dict_to_load、state_dict_type及StateDict/OptimStateDict配置类只列A2/A3。中文缺少950不单独证明不可用，英文排除在下节明确保留；保存/恢复方案不能仅凭根类支持就视为全部子接口已经支持。

流水并行清单另列pipeline/Pipe、pipe_split、PipelineStage/build_stage、microbatch拆合，以及GPipe、1F1B、Interleaved1F1B、LoopedBFS、InterleavedZeroBubble等入口的A2/A3/950DT范围。它不证明DDP/FSDP、所有schedule、动态图和checkpoint的任意交叉组合已验证；具体训练框架的装配仍按各自来源。

## 七版本英文的FSDP状态与方法边界

同提交2.7.1、2.9至2.14中英文fully_shard均只列BF16/FP16/FP32 input。FSDPModule.unshard只在中文列三类产品，类没有独立产品表；英文未收录该对象，不据方法表补造其全部生命周期合同。

FSDP1的check_is_root/fsdp_modules/full_optim_state_dict/optim_state_dict_to_load/state_dict_type，以及StateDictConfig、Full/Sharded/LocalStateDictConfig、OptimStateDictConfig、Full/Sharded/LocalOptimStateDictConfig和StateDictSettings中文仅列A2/A3、英文明确950不支持。这比只读中文缺项得到的“未纳入”更明确，保存恢复设计必须保留英文排除。

英文另对flatten_sharded_optim_state_dict、get_state_dict_type、module、optim_state_dict、rekey_optim_state_dict、scatter_full_optim_state_dict、set_state_dict_type、shard_full_optim_state_dict、sharded_optim_state_dict、summon_full_params列三类均不支持，中文未列。不能用父类、普通state_dict或DCP支持补齐这些方法。

流水并行七版本两侧还对SplitPoint、TensorChunkSpec及PipelineScheduleSingle/Multi.step列三类产品；表未给microbatch合法shape、调度前反向次序、阶段所有权或ZeroBubble收益保证，不从名称生成已验证的整套流水方案。

## FSDP私有ReduceScatter族的版本与产品

同提交中英文private_apis对torch.distributed.fsdp._fully_shard._fsdp_api.ReduceScatter，以及_fsdp_collectives.DefaultReduceScatter/ProcessGroupAllocReduceScatter列BF16/FP16/FP32/INT32/INT64，限PyTorch2.9.0及之后；_fsdp_collectives.foreach_reduce列BF16/FP16/FP32，限2.8.0及之后。均为A2/A3支持、950暂不支持。

原文“支持”的类型没有给所有参数位置和归约组合，不将INT64泛化成所有模型参数类型。私有归约实现的表不由公开FSDP类级产品表覆盖，也不单独证明某个具体FSDP实例必调用其中一个实现。

## 完整示例的作用域与策略选择

中英文DDP示例使用device_count决定world_size、mp.spawn分配进程并以127.0.0.1为master，是单机演示。FSDP2示例则读取LOCAL_RANK却将其传给全局rank：多节点应由启动器的全局RANK/实际进程组身份管理通信，以LOCAL_RANK选择本机NPU；两者不能混用。示例先逐层fully_shard、再根模型fully_shard，之后创建Adam，描述了AllGather取回参数及ReduceScatter归约分片梯度的基本流程；其range(5)是五次训练迭代，不证明完成五个数据集epoch。

总览建议模型单卡可放先考虑DDP、放不下考虑FSDP、扩展瓶颈再评估TP/PP，并用DeviceMesh/DTensor表达通信域与布局。这是决策入口，不能据“用法一致”抹去前文逐接口、dtype、版本和950DT差异。DistributedSampler解决数据分片，不自动消除CPU/存储/预处理瓶颈；DDP梯度同步也不能独立保证不同采样、RNG、归一化和优化器设置下与单卡数值逐项一致。

总览的分布式Checkpoint、TP/PP及HCCL/NCCL语义对照只给外部入口，未摄取外部文档，不能当作任意算子、布局和恢复组合的完整合同。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/parallelism_strategy/ddp_introduction.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/parallelism_strategy/fsdp_introduction.md)（constraint）

- [本卡补充来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/distributed_overview.md)（supporting）

- [补充固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（constraint）

- [补充固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-fsdp-fully_shard.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-fsdp.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-fsdp.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-fsdp.md)（constraint）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-pipelining.md)（constraint）

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-pipelining.md)（constraint）

- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-pipelining.md)（constraint）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [固定来源 45](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）

- [固定来源 46](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/distributed_overview.md)（constraint）

- [固定来源 47](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/parallelism_strategy/ddp_introduction.md)（constraint）

- [固定来源 48](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/parallelism_strategy/fsdp_introduction.md)（constraint）
