---
type: API
title: npu_chunk_gated_delta_rule：分块线性注意力与状态约束
description: 说明 chunk GDR 的 TND 输入、必填 scale/状态、950 FP32 状态边界及序列长度文档冲突。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_chunk_gated_delta_rule.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ChunkGatedDeltaRuleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_chunk_gated_delta_rule.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_chunk_gated_delta_rule.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_chunk_gated_delta_rule.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T01:58:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_chunk_gated_delta_rule：分块线性注意力与状态约束

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_chunk_gated_delta_rule(query, key, value, *, beta=None, initial_state=None, actual_seq_lengths=None, scale=None, g=None) -> tuple(Tensor, Tensor)
```

分块计算 Gated Delta Rule，返回所有 token 的 out=(T,Nv,Dv) 与 final_state=(B,Nv,Dv,Dk)。query/key 为 (T,Nk,Dk)，value=(T,Nv,Dv)，dtype BF16；输出 out 为 BF16，状态 dtype 随 initial_state。它常用于 Prefill 的并行块计算，不是 Softmax Attention。

## 参数与组合限制

- 此主线提交确认 A2/A3/950，FP32 initial/final_state 仅在 950 支持；其他平台使用 BF16 状态。
- 尽管签名带默认 None，TND 必须提供 beta、initial_state、actual_seq_lengths。同提交实现还明确检查 scale.has_value()，所以必须显式传 scale，不能沿用文档“None 表示 1”的说法；常见选择为 Dk**-0.5，仍以模型定义为准。
- beta=(T,Nv)、BF16；g=(T,Nv)、FP32，alpha=exp(g)，None 表示 g 为 0。0<Nv,Nk≤64 且 Nv 整除分组关系为 Nv%Nk=0，0<Dv,Dk≤128，B/T 均大于 0，不支持空输入。
- q/k 必须归一化且各元素在 [-1,1]；g∈[-1,0]，beta∈(0,1)，超出可导致溢出。
- actual_seq_lengths 为 INT32(B,)；同页 Eager 示例传独立长度、图示例却传累计边界。本文保留此冲突，多 batch 调用须核对实际底层算子契约；B=1 时两种表示一致。图示例还用相等 Dk/Dv 掩盖状态轴顺序，状态应按参数/实现给出的 (B,Nv,Dv,Dk) 核对。

## 验证与模型关联

先以 B=1 的逐 token 递推参考比对输出与最终状态，再核对 B>1 的分段语义；用 Dk≠Dv 检查状态轴顺序，显式验证 scale 和数值域。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py#L1264)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## GE与文档图示例分别核对

TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的同名GE转换器直接抛出“不支持GE graph mode”的RuntimeError，没有生成算子节点。文档图示例使用config.mode=reduce-overhead的aclgraph配置；不能因为有这段示例便称该固定GE路径可用，也不能据GE拒绝推断所有aclgraph路径均不可用。具体后端仍需按配套核验，没有执行图捕获。

C++明确要求value非空且三维、beta/initial_state/actual_seq_lengths/scale全部提供，最终状态另分配为initial_state.clone并保留其dtype；Meta只检查value，随后直接读取initial_state四轴，未完整核对长度、尺度和分组。构造Meta成功不免除显式scale与其余必填项，也不能用它验证任意输入值域。

双语Eager例传每序列长度，图例传cumsum边界；图例还注释掉q/k归一化，且状态后两轴写成Dk,Dv而示例两者都128。这些示例都不能独立证明多batch长度、非方形状态轴和数值稳定性正确。950PR/DT的FP32状态扩展仍按主线产品条款处理，未取得其他产品FP32状态或已登记发布组合支持的证据。

## 分块参考不是设备验收或公开调参入口

722行测试有网络式和三阶段PyTorch参考，唯一测试方法却被无条件skip（A2/A3）。实际保留的配置仅B=1、T=2048、Nk=Nv=32、Dk=Dv=128、BF16且有g，不覆盖GQA、多batch不同长度、g=None、FP32状态或非整块尾部。

参考中的chunk_size=64是其内部实现参数，公开API没有该调优选项。get_chunk的非整块填充路径引用未定义scale，而测试2048恰为64倍数；get_rmse虽计算误差却返回常量CV_RMSE，使该比较项不能判定真实RMSE。use_float64参数也没有构成实际FP64参考。

这些参考使用NPU Tensor，打印的主机计时没有完整设备同步，不称独立CPU数值参考或融合吞吐结果。本文未运行测试，仍应同时比较每token输出、最终状态、输入状态是否保留，以及实际长度分段。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_chunk_gated_delta_rule.md)（primary）
- [补充版本或约束](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ChunkGatedDeltaRuleKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_chunk_gated_delta_rule.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_chunk_gated_delta_rule.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_chunk_gated_delta_rule.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
