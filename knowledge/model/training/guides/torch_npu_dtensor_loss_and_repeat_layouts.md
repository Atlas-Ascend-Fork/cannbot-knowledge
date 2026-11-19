---
type: Guide
title: TorchNPU DTensor损失归约与repeat分片边界
description: 区分CrossEntropy及KLDiv归约候选、均匀分片检查和repeat的维度及变量边界。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_math_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_math_ops.py
  role: implementation
created_at: '2026-11-11T06:35:50Z'
updated_at: '2026-11-11T06:35:50Z'
platforms: []
---

# TorchNPU DTensor损失归约与repeat分片边界

## 固定实现范围

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的_math_ops.py，相关函数完整AST相同。记录的是本地候选生成，不是运行过的数值、通信或编译验证；外部expand_to_full_mesh_op_strategy及注册兼容实现需要按包版本核对。

## 均匀分片检查的实际强度

is_tensor_evenly_shardable要求spec是DTensorSpec、shape非空、placements非空。对每个Shard placement，将对应mesh维size乘到其张量维的shards_map；只有累计份数大于1且该shape维无法整除时返回False，其余返回True。非Shard的Partial/Replicate不参与乘积。

它检查整除，不检查全部shape取值、负dim规范化、placement维越界或mesh/shape一致；也不保证策略一定最优。调用位置有时只取第一条候选spec，不等于对未来选择的所有候选逐一校验。

## CrossEntropy前向与反向的mean并不对称

前向以四个输出槽loss/log_prob/zloss/lse_for_zloss和x/target输入展开策略，存在weight时补复制weight，input_index=4。除全部复制外：reduction='none'时loss与log_prob沿0分片，zloss/lse复制，x/target沿0分片；mean仅在weight缺省且target第一条策略spec通过均匀分片检查时增加loss=Partial('avg')，log_prob沿0分片。其他reduction分支直接产生loss=Partial('sum')及log_prob沿0分片，存在的weight复制；这个else并非对任意reduction字符串的合法性验证。

反向input_index=1，存在weight或lse_for_zloss时将其保持复制；none给梯度与对应输入的0维分片候选，sum让grad_loss复制而输出及其他主要输入沿0分片。mean没有额外分片候选。不能由前向mean存在Partial(avg)推定反向也有同样的batch候选，也不能用算术平均替代带weight或不均匀分片的全局损失合同。

## KLDiv逐维生成与提前返回

KLDiv前向逐个x维生成候选：none保留该维Shard，mean只有x.shape[dim]可被x.mesh.size(0)整除才输出Partial('avg')，sum输出Partial('sum')。源码注释说batchmean与sum枚举值相同，本函数不单独实现完整batchmean归一逻辑；log_target也不在这里分支。

前向某维不满足mean整除会进入warning并立即返回已累计候选，不是跳过这个维继续枚举，因此后续维可能未生成。它使用mesh.size(0)，不是前述多mesh累计分片检查。反向none让grad_out/x/target与输出同Shard，sum让grad_out复制、其余同Shard；mean直接保留已累计的复制候选，不新增分片。不要从单维整除扩展为所有mesh维或全部loss梯度都已可均匀归约。

## repeat_interleave的负维与候选变量边界

前向先给复制。输入通过均匀检查时，dim=None只加Shard(0)，指定dim则对每个输入维都加Shard候选。未通过均匀检查且指定dim时，只有i!=dim才给局部变量sharding_strategy赋值，但append位于if外：第一次i==dim且变量尚无值时存在静态UnboundLocalError路径，之后等于dim也可能追加上一次候选。没有执行该路径，不据此声称所有真实不均匀输入都会报错。

这两个repeat策略没有normalize_dim；负dim不能直接按其他算子已规范化的规则解释。反向只有dim非None且x均匀时才枚举候选；若grad首placement沿dim分片且grad不均匀，则循环各轮直接continue，否则输出、grad和x均沿当前i分片。dim=None或x不均匀只保留复制，repeats/output_size不在本地做完整合法性检查。

## 集成验收

覆盖none/mean/sum、weight和可选统计、均匀/非均匀分片、多维mesh、正/负/缺省dim，分别比较loss、梯度和实际归约。出现Partial时记录消费前的重分布，不能只用本地loss与单卡全局loss比较。接口支持条件见[原生TP约束](torch_npu_native_tensor_parallel_constraints.md)，策略展开版本差异见[DTensor重分布与注册](torch_npu_dtensor_redistribution_and_registration.md)。
