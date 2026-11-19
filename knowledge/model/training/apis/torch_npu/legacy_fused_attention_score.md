---
type: API
title: 旧fused_attention_score：NZ、保留概率与固定自注意力shape
description: 保留旧产品平台未知及真实二维输出，不用文档宽松描述推导任意交叉注意力。
tags:
- task.lookup
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_fused_attention_score.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_fused_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_fused_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FusedAttentionScoreKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FusedAttentionScoreKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:42:31Z'
updated_at: '2026-11-09T20:42:31Z'
platforms: []
---

# 旧fused_attention_score：NZ、保留概率与固定自注意力shape

## 固定版本与产品边界

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文、独立主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文及各自实现。发布归ascend_26_0_pt28，main不是与其他仓main自动配套的发行。

平台只按实际产品页；950新增项严格另列主线PR/DT，旧Atlas不自动映射新型号。计划废弃、不维护、schema注册及实际运行能力分别判断；stable不表示推荐新模型采用或运行verified。这里只静态阅读，未导入上游、运行设备、反向、数值或性能实验，底层Kernel算法不由框架包装引用视为全覆盖。


## 平台和维护

两版页面只列旧Atlas训练910、推理310p，未确认A2/A3或950，故draft且platforms为空；其他融合接口支持表不补齐这里。计划废弃、底层不维护，中文建议npu_fusion_attention，主线英文Notice省略了替代建议；替换前仍需核对新接口合同。

## 文档输入协议

Q/K/V和attention_mask均FP16、格式29(NZ)。无转置时Q(B,H,Sq,Dq)、K(B,H,Sk,Dq)、V(B,H,Sv,Dv)，mask(B,H,Sq,Sk)；head数一致、QK的D一致。scale为Scalar，keep_prob表示保留概率0..1，与MHA的dropout_prob含义相反。query/key transpose、两个bmm transpose、value/dx transpose共六bool默认False，后两个主要供反向消费，不能视作同一个排列开关。

## 实际分配比文档窄

两固定实现逐字节相同：首输出分配(B*Sq,H*Dq)，不是文档“同Q形状”的四维；softmax辅助分配(B,H,Sq,Sq)，不按Sk。反向Q/K/V都按Q的尺寸重建，不能由文档允许Dv不同就承诺任意交叉注意力或不同V head_dim正确。value_transpose/dx_transpose没有在前向AttentionScore命令中消费。

fwd内部还保存softmax及一维UINT8 mask（长度softmax.numel），mask使用默认生成器current_seed、seed2=0并跨secondary stream记录原流；没有这里所读私有Dropout的Philox偏移协议，不推导相同随机消耗或可互换掩码。公开入口只返回首Tensor，内部三元组与反向辅助结果不能按普通SDPA协议解包。[BERT旧包装](contrib_bert_fused_attention.md)还有投影、固定head_dim与首次检查边界。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_fused_attention_score.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_fused_attention_score.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_fused_attention_score.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FusedAttentionScoreKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FusedAttentionScoreKernelNpu.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
