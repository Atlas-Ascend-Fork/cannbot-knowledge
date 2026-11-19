---
type: Guide
title: FIA KV 伪量化：版本、阶段与 scale 布局矩阵
description: 对照主线 v1/v2 的 KV 分离模式、打包 INT4/FP4、PagedAttention 与 GQA NZ 条件，保留产品差异。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.precision
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
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: primary
created_at: '2026-11-09T09:42:58Z'
updated_at: '2026-11-10T05:26:41Z'
platforms:
- a2
- a3
- '950'
---

# FIA KV 伪量化：版本、阶段与 scale 布局矩阵

## 适用版本与选择顺序

正文主体依据 OpPlugin 主线固定提交 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`；A2/A3 与 Ascend 950PR/950DT 逐项区分，不回推 `ascend_26_0_pt28` 发布组合。TorchAir 主线 Converter 只作转换证据，不代表两仓主线已经配套验证。发布v1增补另见文末，分别固定来源。先确定实际 Q_S、Q/KV dtype、逻辑 layout、KV 物理分页格式，再选 scale 模式；不能仅按“W4/C8”配置名选择。

v1 的分离参数为 key/value_antiquant_scale、key/value_antiquant_offset、key/value_antiquant_mode；v2 对应 dequant_scale_key/value、dequant_offset_key/value、key/value_quant_mode。scale 成对有或无，offset 也成对；对称量化省略 offset，不必人为添加零张量。

## 模式与 scale/offset 的物理形状

下表 N 为 KV_N，H=N×逻辑 D；shape 必须按阶段匹配。mode0 包含 per-channel 和 per-tensor，不能只看 mode 编号区分。

| 模式 | Q_S>1 的 scale/offset | Q_S=1 的 scale/offset | dtype |
| --- | --- | --- | --- |
| 0 per-channel | (N,1,D)、(N,D)、(H)、(1,N,1,D)、(1,N,D)、(1,H) | (1,N,1,D)、(1,N,D)、(1,H) | 与浮点 Query 相同 |
| 0 per-tensor | (1,) | (1,) | 与 Query 相同 |
| 1 per-token | (B,S) | (1,B,S) | FP32 |
| 2 per-tensor+head | (N,) | (N,) | 与 Query 相同 |
| 3 per-token+head | (B,N,S) | (B,N,S) | FP32 |
| 4 per-token+PA | (blocknum,blocksize) | 同左 | FP32 |
| 5 per-token+head+PA | (blocknum,N,blocksize) | 同左 | FP32 |

此表是形状入口，不是所有产品/dtype 的组合支持表：A2/A3 的 Q_S>1 仅模式0/1，Q_S=1 才列0..5。950 的普通 INT8/打包INT4路径列0..5，但 per-tensor 与 per-tensor+head 在 Q_S=1 只列 KV INT8；模式4/5在 v1 只列 KV INT8。v2 的 Q_S>1 模式4还列 E4M3，模式5仍仅INT8，不能把新增类型并到 v1 或 decode 表。

一般要求 K/V 模式及 scale/offset shape 一致；明确例外 K=mode0、V=mode1，各自使用表中形状和不同 dtype。A2/A3 v2 对该 INT8 混合模式的 decode 另限定 Query/输出 FP16；不能将“成对存在”读作所有 shape 必须一致。

A2/A3 v2 普通 Q_S>1 分离路径进一步要求 Query/输出 BF16、KV INT8、Q_S≤16，不支持 TensorList/普通 PA；per-channel scale 为BF16，per-token为FP32。GQA NZ 是下述独立特化例外。v1 的 combined antiquant_scale/offset 路径另有 INT8→FP16 等条件，不能把 v2 的分离限制倒灌到 v1。

## 950 新类型与打包边界

v2 的 per-channel 支持 INT8、打包INT4、HIFLOAT8、E4M3；后两种不支持 dequant_offset。Q_S>1 的 per-token 还列 E4M3，但 Q_S=1 的 per-token 表只列 INT8/打包INT4，不能合并两表。模式6的 FP4 E2M1 per-token-group 使用 E8M0 scale，形状 (1,B,N,S,D/32)，无 offset；不把 FP8 全量化的6/6/8配置当成 KV FP4 伪量化。

打包INT4使用INT32容器，每个元素存8个逻辑INT4；逻辑D要求64对齐，物理INT32末维对应8对齐。FP4容器的末维是两个逻辑4bit元素；v2 Meta与Converter分别按2扩展逻辑D并Bitcast/Reshape，INT4按8扩展。需要重解释位模式，普通 to(dtype) 数值转换不等价。形状推导代码中有 E1M2 分支，不表示公开页面已授权全部 E1M2 产品组合。

950 v2 的 FP4/打包INT4 decode 要求 Query与逻辑KV D均64对齐，打包INT4不支持后量化。key_dtype/value_dtype 在 HIFLOAT8、FP4时需按接口要求填写，E8M0 scale使用相应dequant_scale_*_dtype；query_dtype和多个其他提示仍存在“文档预留、实现有分支”的差异，不能仅由实现分支宣称全部开放。

## 普通 PagedAttention 与 scale 管理

PA需要有效 INT32 二维块表、实际KV长度、正 block_size，并保证容量、物理KV布局与块ID一致；框架不代为检查每个 block ID。mask、PSE及按序列存的 per-token scale 轴需覆盖页表列数×block_size容量，不能仅按当前有效长度分配。

Q_S>1 普通浮点 PA 的 block_size 为128/256/384/512。A2/A3普通prefill不支持KV伪量化；950 v2明确增加INT8、INT4、HIFLOAT8、E4M3、FP4伪量化PA，不能外推到v1。950 v2的五维PA KV布局为(blocknum,N,D/16,blocksize,16)，打包INT32对应(blocknum,N,D/2,blocksize,2)，其中D/物理容器应按上游逻辑轴核对。

decode 的 block_size 对齐：浮点16，INT8/E4M3/HIFLOAT8为32，FP4/INT4为64；A2/A3不支持浮点Q+INT4 KV的PA。v1 decode仅A2/A3栏明确block_size≤512，950栏只列对齐要求；v2主线decode段也未给统一512上限，不跨产品/版本复用。KV每个Tensor元素总数仍受INT32范围限制。

Q布局BNSD/TND可选BnBsH或BnNBsD，BSH/BSND的普通路径仅BnBsH；950 v2还列五维PA格式。BnBsH的KV_N×D超过65535会受硬件指令约束，可核对GQA减小KV头或受支持的BnNBsD布局。来源建议后者优先，但不是本地性能测量。

## GQA 伪量化 + NZ 的专用矩阵

共同要求 Query BF16、KV INT8、D=128、Q_S为1..16、分离scale、高性能模式，head组合仅(10,1)/(64,8)/(80,8)/(128,16)，逻辑layout仅BSH/BSND/BNSD。NZ KV为(blocknum,KV_N,D/32,blocksize,32)，不是把普通四维KV直接改名。

A2/A3要求PA且block_size仅128/512；per-channel scale按layout为(H)/(N,1,D)/(N,D)，BF16；per-token为(B,S)，FP32，S覆盖页容量。无offset、RoPE、左padding、TensorList、PSE、prefix、后量化。MTP=0用mode0无mask，0<MTP<16用mode3压缩mask。v2的该段还写mode9 tree mask，但与同页“mode9仅MLA、此路径禁止RoPE”相冲突，不能据此组合GQA NZ与tree mask。

950 v2反而要求非PA，仅per-channel；同样只列上述head组合、D与Q_S，并限制TensorList/PSE/后量化。不能把A2/A3的paged-NZ配方平移到950。

## 合并参数与验证边界

v1的combined antiquant_scale/offset在950不支持，A2/A3按mode0通道/张量或mode1 Token管理，合并shape含前导2用于K/V；分离参数同时存在时以分离为准。v2没有combined数据参数。减少KV存储或拷贝是优化目标，仍应比较完整链路的反量化成本、容量、数值和吞吐；本次仅静态审阅，未执行NPU。

- [v1接口](../apis/torch_npu/npu_fused_infer_attention_score.md)
- [v2接口](../apis/torch_npu/npu_fused_infer_attention_score_v2.md)
- [全量化路径](fia_quantized_attention_paths.md)

## 发布v1的独立限制与文档变化

以下增补仅依据发布OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5的v1全文，不将上文主线v2扩展倒推发布。发布A2/A3 v1在普通Q_S>1 KV分离段也明确要求Q/输出BF16、KV INT8、Q_S≤16，仅perchannel/pertoken，scale分别BF16/FP32；不支持TensorList、左padding、普通PA或prefix。perchannel段列(KV_N,D)/(H)等形状，GQA NZ专节再按layout给(H)/(N,1,D)/(N,D)，不能用一个通用shape覆盖全部路线。

发布decode分离模式0..5与形状表分别保留，K=mode0/V=mode1为例外，其余模式及非空scale/offset shape匹配。发布的混合INT8模式还明确Q/输出仅FP16，不能把950主线表对类型的宽泛列举套回A2/A3。per-token decode shape为(1,B,S)，普通prefill则(B,S)；mode2为(N,)，mode3为(B,N,S)，mode4/5为物理页尺度，不能互换。

combined antiquant_scale/offset有前导2管理K/V，发布参数概述声称decode只perchannel，但同页综合约束又列pertensor/pertoken及对应shape，主线随后补齐概述。这是文档内部差异，不能据其中一行单独认证或否定所有组合。普通prefill combined路径仅INT8→FP16；高性能模式要求KV数值范围与scale范围乘积在(-1,1)，超出应核高精度路径；不是所有量化方式的误差保证。

发布普通PA段写可提高吞吐但可能降低性能，主线改成缓存布局建议；吞吐、单次时延和总链路成本应分别测量。发布decode每个KV Tensor元素总数不得超过INT32表示范围，页表列数×block_size容量也需被mask/PSE/per-token scale覆盖；这些限制不能因为主线概述省略而推定已经取消。两版K/V和prefix的INT32→INT4图转换只重解释位模式，不生成校准scale。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）
