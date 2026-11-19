---
type: Guide
title: TorchNPU Profiler的Attention、GEMM FLOPs估算与吞吐解释
description: 说明GEMM、GMM、Attention和BlockSparse理论计数与吞吐/MFU解释的边界。
tags:
- task.optimization
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_hook.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_registry.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_formulas.py
  role: primary
created_at: '2026-11-11T07:41:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler的Attention、GEMM FLOPs估算与吞吐解释

## 计的是选定算术项

固定PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的_flops_formulas.py完整545行及Hook/registry直接消费者。平台未知、未执行公式或设备测试；固定发布三条同名路径缺失只作精确路径记录。注册和计数失败仍执行原算子的规则见[FLOPs Hook](torch_npu_profiler_flops_hooks_registry_and_measurement_scope.md)。这些Python形状估算不等于硬件PMU实测或全部训练FLOPs。

## GEMM公式族与融合项的排除

| 目标族 | 当前计数 |
|---|---|
| mm / bmm | 2MNK；bmm再乘输入batch数 |
| matmul | 向量点积2K；一侧向量取对应batch；矩阵两侧先广播batch，再2×batch乘积×MNK |
| linear | 2×input除末维外尺寸乘积×weight的N×K |
| addmm | 仅mat1/mat2的2MNK，beta/alpha/self不改变当前公式 |
| all_gather_base_mm | 2×x1本地M×传入world_size×K×x2末维N |
| transpose_batchmatmul | 按perm_x1/perm_x2先置换shape，再通用矩阵公式；perm_y/batch_split_factor未计额外工作 |
| quant_matmul_gelu / grouped_matmul_swiglu_quant_v2 | 通用_matrix_tensor_flops，仅所给x/weight的矩阵项，不额外计GELU/SwiGLU/量化/scale/bias等 |
| alltoallv_gmm / gmm_alltoallv | 先算gmm_x/gmm_weight矩阵项，mm_x和mm_weight都非None才另加普通MM，按对应trans权重标志选N |

通用_matmul_shape_flops要求两侧rank>=2，取M=prod(left_shape[:-1])、K=left_shape[-1]、N=right_shape[-1]或转置时[-2]；它不是全部高维广播和group语义的完整验证器。许多函数不检查K或batch一致，依据原算子合法输入来估算；公式能给数不证明原调用合法。all-gather的world_size来自参数，不核对实际通信组；all-to-all的send/recv counts、ep_world_size没有进入该算术式，不能据此认证本rank实际收发后的工作量或通信开销。

广播helper按尾对齐检查尺寸相等或任一为1，再取max；_permute_shape检查排列长度，却未另验所有索引唯一/合法，_shape直接int每个dim。它们不是动态shape无开销或完整归一化的保证。

## GMM分组长度是局部启发式

npu_grouped_matmul将list/tuple视多Tensor，否则包成单项。x与weight数量相等时直接逐pair求和，group_list等参数不参与；只有单x/多weight才用group_list拆M，其它数量不匹配抛ValueError。split_item/group_type/group_list_type/act_type及量化相关flag没有在公式里切换一套完整算子语义。

单组直接使用total_m。多组需group_list长度等于weight数；若末项等于total_m且各项和大于total_m，才当累计端点做相邻差，否则当长度。最终只要求sum等于total_m，没有独立验证每个组长度非负或累计单调，因此不能拿这条启发式替代实际API的group_list_type合同。空值、错误shape等公式失败会使Hook跳过该次标记，原算子仍可运行。

## 普通Attention的分数面积

BNSD直接取维度，BSND换成B/N/S/D，BSH/SBH靠head数整除隐藏维；_head_dim要求heads>0且可整除。fusion_attention会从K的布局或隐藏维推KV heads，infer_attention_score用num_key_value_heads或回退num_heads；这些不是完整GQA、device或Q/K/V兼容检查。

共同布局计数为`int(2*B*query_heads*score_area*(Dq+Dv))`，只包括QK和PV两项。K解析出的head维等值不在这里逐项核验；softmax、bias/pse、mask生成、dropout和数据搬运未加到此式。

score_area的固定分支：sparse_mode=0取Sq×Sk；mode2在Sq>=Sk时取SqSk−Sk²/2，否则Sq²/2；mode3在Sq>=Sk时取Sk²/2，否则SqSk−Sq²/2；其他mode抛ValueError。这里的半平方面积没有逐行对角项、实际atten_mask、padding_mask、pre/next_tockens窗口核算，不应当作任意稀疏模式的精确有效元素数。

TND走另一分支，要求actual_seq_qlen与actual_seq_kvlen，先int转换、去末尾0，再把累计端点做差；两列数目必须一致且差值非负。面积是各序列q_len×kv_len之和，再乘2×query_heads×(Dq+Dv)。该分支不使用sparse_mode或实际mask，也不完整验证累计末项与Tensor总token数一致；空累计列表可得0，不能由0认证真实计算量为0。

## BlockSparse按块真值累计，但仍有输入前提

npu_block_sparse_attention把block_sparse_mask转序列，batch取mask外层长度，query heads参考mask[0]长度；query/value按各自layout取长度和D，key没有用于该计数式。seq长度缺省按shape给每batch一份，提供时去末尾0、要求条目数等于mask batch，TND再按累计端点做差且不得负。

按mask[batch][head][q_block][kv_block]遍历，真值块才累计：q_tokens=min(block_x,max(q_len−q_start,0))、kv_tokens同理，末块裁剪到序列边界，最后`int(2*有效score元素*(Dq+Dv))`。不是只用非零块数乘固定完整面积；但也没有完整验证正block尺寸、mask嵌套rank/矩形一致性、head/batch对应或所有序列边界，不能把局部循环当整算子输入验证。

_to_sequence接受list/tuple或tolist返回的list/tuple，_to_nested_list只是转发，不逐层认证所有值；任何非零真值都可被循环当有效块，未强制mask元素为BOOL。实际shape/layout/掩码合同仍需按固定算子API单独满足。

## 吞吐和MFU需要同一分母与覆盖口径

用于比较时保存实际命中的Python目标、公式版本、输入全局/局部shape、GMM分组、Attention长度与稀疏参数，再核丢失/失败标记。观察到MSTX消息只说明本地公式给出非负值并尝试标记，不能认证设备执行了同样数量的浮点指令。

如果自行以FLOPs/时间计算吞吐，应使用与这些计数对应的同一批工作和时间窗，说明是否包含前反向、通信、量化、重计算和并行rank重复计数；TFLOP/s还要按10^12作单位换算。MFU另需适配真实产品、dtype和执行模式的峰值口径，不能将Host标记耗时、PMU占比、理论公式或不同rank的数字直接互换。本卡没有提供峰值数值或测得性能，指标选择和观测成本见[Profiler指标选择](torch_npu_profiler_metrics_selection.md)。

## Evidence

- [固定主线源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_hook.py)（1–153行，完整本地模块）
- [固定主线源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_registry.py)（1–56行，完整本地模块）
- [固定主线源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_formulas.py)（1–545行，完整本地模块）
