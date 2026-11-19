---
type: Guide
title: 词表并行融合损失：局部参考点、通信和反向交付
description: 串联三个显式接口，推导局部最大值不同为何不能直接相加 exp 和，并保留词表边界与产品交集。
tags:
- task.implementation
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_cross_entropy_loss_with_max_sum.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_online_max_sum.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_cross_entropy_loss_with_max_sum_backward.py
  role: example
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 词表并行融合损失：局部参考点、通信和反向交付

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 任务与入口

将LM-Head的局部MatMul、统计与交叉熵分阶段处理，选择保存logits/softmax的性能路线，或反向重算的省显存路线。三个接口的产品交集按损失阶段仅取A2/A3；前后阶段的950支持不足以证明整条流水在950有完整支持。

## 来源公式推导出的通信检查

online_max_sum返回每个分片的局部最大值m_i，以及s_i=sum(exp(z-m_i))。**依据这些公式推导**：先求M=max_i(m_i)，全局分母应为S=sum_i(s_i*exp(m_i-M))；直接SUM各s_i会混合不同参考点，通常不正确。例如两分片各只有logit 0与10，局部s均为1，直接SUM得到2，正确全局参考点的分母是1+exp(-10)。

目标logit也需在同一M参考点下合并，并用target_mask排除目标不属于该词表片的项；不能把域外masked_target=0的占位当作真实目标。此处给出数值一致性检查，不声称三个Python调用自动完成正确的HCCL通信、mask与autograd集成。

## 保存与重算的联合约束

return_logits=False使前向最后一槽为空；损失阶段不提供vocab_parallel_logits时softmax为空，反向必须同时提供修正后的全局M/S。保存logits并生成softmax可进入反向高性能分支，代价是保留(B,V_local)中间量。两种路径分别测峰值、耗时与梯度，不把缺省空槽解释为零概率。

target_mask按bit打包，不能转换为普通长度B字节数组后盲传；masked_target、输入和权重分片必须保持一致。反向weight的本地词表行数至少128，label_smoothing仅0。区间端点文档存在易混淆表述，应结合实际映射核实后再组装多卡流程。

显式反向输出本地input_grad/weight_grad，不代表全局归约、状态保存和训练框架hook已经交付。先与小规模全词表参考比较每token损失与两个梯度，再验证跨rank及存储生命周期。仅核对了上述公式的CPU标量算术，未执行上游算子、HCCL或训练。

- [通信前MatMul与局部统计](../apis/torch_npu/npu_fused_linear_online_max_sum.md)
- [损失与可选Softmax](../apis/torch_npu/npu_fused_cross_entropy_loss_with_max_sum.md)
- [两条反向路线](../apis/torch_npu/npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md)
- [分块LM-Head是另一种显存策略](../concepts/techniques/chunk_loss.md)

## 目标logit修正与可交付的验证范围

按来源公式进一步推导：若分片r拥有目标，局部p_r=z_target-m_r应修正为p_r+(m_r-M)，域外分片贡献仍为0，再求和得到以M为参考的目标量。不能把所有域外的0也加上m_r-M。此前的S修正与此目标修正必须使用同一批数据、同一全局M及准确的目标所有权；这是公式推导，未作为多卡可运行实现发布。

三接口共用的主线C++只分配输出和调用本地aclnn，未执行跨rank通信。前向不保存logits、损失不生成softmax时，对应Python槽都为None，而非零概率矩阵。不要把None丢进后续分支，也不凭公式中的赋值形式推定缓存原地修改。

现有三个测试分别只检查shape/dtype/None；随机统计与softmax没有组成同一份可追踪的真实交叉熵参考，未证明数值损失、局部梯度、通信校正或训练框架自动求导。后续实现验收需先用一致的全词表参考核对前向及两份梯度，再覆盖分片所有权、packed mask尾部、通信及缓存生命周期。

online和显式反向公开950PR/DT，损失阶段950尚未确认，所以本指南的公开产品交集仍为A2/A3；“未列”不是明确No。固定Meta和derivatives文件未找到三个同名条目，只记录检索范围，不扩大为所有图后端不可用的结论。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_cross_entropy_loss_with_max_sum.py)（example）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_online_max_sum.py)（example）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_cross_entropy_loss_with_max_sum_backward.py)（example）
