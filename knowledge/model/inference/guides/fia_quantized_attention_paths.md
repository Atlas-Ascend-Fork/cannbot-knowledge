---
type: Guide
title: FIA 全量化：INT8、MXFP8 与 GQA FP8 的执行边界
description: 区分主线量化参数组、950模式三元组、scale物理形状和Eager限定，记录文档冲突与不可推断项。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py
  role: implementation
created_at: '2026-11-09T09:42:58Z'
updated_at: '2026-11-14T01:59:28Z'
platforms:
- a2
- a3
- '950'
---

# FIA 全量化：INT8、MXFP8 与 GQA FP8 的执行边界

## 固定来源与模式选择

仅依据 OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda`。主线文档的产品支持、具体模式约束、Meta、C++分派与GE Converter分别提供不同证据；这里没有运行、精度或性能验证，也不声明与TorchAir另一主线提交兼容。发布基线的接口卡保留独立版本范围。

浮点Q+低比特KV是[KV伪量化](fia_kv_antiquant_modes.md)，Q/K/V均低比特才是本页全量化；输出量化又是单独一层，不能只见quant_scale便当成同一数值链。

## v1 INT8 参数组与未解决的产品冲突

| 主线文档中的输入/输出路线 | 必需参数 | 不应携带 |
| --- | --- | --- |
| QKV INT8→INT8 | dequant_scale1、quant_scale1、dequant_scale2、quant_scale2 | quant_offset2可选 |
| QKV INT8→FP16 | 前三项 | quant_scale2、quant_offset2 |
| FP16/BF16→INT8后量化 | quant_scale2 | 前三项；quant_offset2可选 |

dequant_scale1/2为FP32或UINT64，quant_scale1为FP32。上述旧INT8路线限定BSH/BNSD/BSND/BNSD_BSND，INT8 D需32对齐；普通decode QKV全INT8仍在文档中禁止。

主线v1 Query类型段只列FP16/BF16，量化表与示例6却列QKV全INT8；C++/Meta存在INT8输出分配，不能据此消除产品支持表冲突或认定950所有INT8全量化均可用。本表保存文档参数契约，具体全INT8产品组合仍待对应CANN确认。示例5中“禁用前三项”只适用于浮点输入后量化，不能推广到示例6。

## v2 MLA INT8 的额外条件与冲突

A2/A3 D=512 MLA段明确列QKV INT8、RoPE BF16、输出BF16；三路dequant_scale_query/key/value均为FP32且同时存在，Query mode3、KV per-tensor mode0，不带输出量化及K/V offset，可用NZ。它不是v1的pertensor全量化四参数链。

同页Query类型段未列A2/A3 INT8，TND D512综合限制又写不支持全量化。因此本页不将这个特化声明扩展为所有layout可用，尤其不据Recipes的TND_NTD调用把相互矛盾的条目合并成已确认支持表。950的INT8 MLA段要求PA NZ，并列自己的layout与Q head集合；仍需同时核对MLA尺寸、稀疏及实际CANN支持，不能跨产品复用。

## 950 v2 MXFP8 全量化

该小节覆盖950PR/950DT的文档路径，Q/K/V为E4M3，Query/Key/Value模式分别6/6/8，三路scale为E8M0。D仅64或128，逻辑layout仅TND，可分页或不分页；分页block_size固定512，KV为BnNBsD或NZ。

| scale | 非PA | PA BnNBsD | PA NZ |
| --- | --- | --- | --- |
| Query | 推荐(Q_T,Q_N,D/64,2)；Q_S×G≤80时推荐(KV_N,Q_T,G,D/64,2) | 同左 | 同左 |
| Key | (KV_T,KV_N,D/64,2) | (Bn,KV_N,Bs,D/64,2) | (Bn,KV_N,Bs/16,D/64,16,2) |
| Value | (KV_T/64,KV_N,D,2) | (Bn,KV_N,Bs/64,D,2) | (Bn,KV_N,D/16,Bs/64,16,2) |

G=Q_N/KV_N，Bn为页块数，Bs为块大小；Query推荐形状的切换点不是Token总数通用阈值。表中的除法是物理scale轴定义，不能在非整除输入上自行截断。需要配套真实长度与相应对齐/填充策略。

只列sparse0无mask或sparse3配mask，inner_precise为0/1，允许请求LSE。单算子直调的PA路径特许KV、KV scale及key_rope的0/1轴非连续；不外推为任意stride或图模式也能非连续。

## 950 v2 GQA FP8 全量化：只走 Eager

Q/K/V为E4M3，模式3/3/2，三路scale为FP32；只列NTD_TND+PA，Q形状(Q_N,Q_T,D)，KV为(blocknum,KV_N,blocksize,D)，D=128、block_size=128。Query scale为(Q_N,Q_T)，Key scale为(blocknum,KV_N,blocksize)，Value scale为(KV_N,)；与MXFP8的E8M0、scale轴和512页大小均不同。

支持sparse0无mask或3配mask，inner_precise0/1，可请求LSE。可选PScale对应quant_scale_p，FP32 shape(1,)，不传默认1.0；禁止RoPE、左padding、TensorList、prefix、PSE。单算子直调只对KV及Key scale的0/1轴非连续给出例外。

**主线Meta显式拒绝Q/K/V为E4M3且模式3/3/2的组合，错误信息注明“only supports eager mode”。** 因而通用“支持图模式”及GE Converter存在都不能证明该组合可torch.compile/GE/捕获；本次没有尝试绕过Meta。

## 后量化与输出 dtype

v1 quant_scale2、v2 quant_scale_out存在时通常选择INT8输出；offset可选但必须与scale同dtype/shape。浮点Query BF16允许FP32/BF16输出scale，其余普通路径仅FP32。per-channel输出scale元素乘积对应输出Q_N×D（BSH为H），不按KV头数分配。

带per-channel后量化时不支持Ring Attention或D非32Byte对齐；负band窗口及带offset的无效行还可能被拦截，不能靠inner_precise修复所有组合。v2主线新增out_dtype，C++/Meta在输出量化或INT8/E4M3/指定HIFLOAT8输入分支读取它；这仅证明分配/类型转发，不表示任意输出枚举都满足底层Kernel。返回值章节只列FP16/BF16/INT8，与out_dtype参数中FP8示例并不构成完整一致矩阵。

## 保留未决的路径

模式7在参数页称FP8 per-block全量化，D列1..128，但没有像MXFP8/GQA FP8一样完整列出scale物理shape与产品组合；不从“模式编号存在”生成可运行配方。query_dtype文档称预留，C++/Meta/Converter却存在HIFLOAT8输入分支，亦保留差异。上述冲突与缺项是明确的待确认项，不能作为已验证的支持路线。

950 C++分派使用aclnnFusedInferAttentionScoreV5；非950的v2使用V4，v1按CANN门槛选择V2/V3。Python的v1/v2命名与底层aclnn版本号不是同一编号体系。

- [v2接口与主线增量](../apis/torch_npu/npu_fused_infer_attention_score_v2.md)
- [MLA与packed布局](fia_mla_and_packed_layouts.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py)（implementation）
