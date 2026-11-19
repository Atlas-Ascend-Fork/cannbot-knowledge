---
type: API
title: RMSNorm 与 RoPE 及 KVCache 写入融合（torch_npu.npu_kv_rmsnorm_rope_cache）
description: torch_npu.npu_kv_rmsnorm_rope_cache：RMSNorm 与 RoPE 及 KVCache 写入融合。融合了MLA（Multi-head Latent Attention）结构中RMSNorm归一化计算与RoPE（Rotary Position Embedding）位置编码以及更新KVCache的ScatterUpdate操作。 区分发布576维和主线950可变尺寸，说明量化冲突、原地缓存、索引与底层V2选择。
tags:
- task.lookup
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_kv_rmsnorm_rope_cache.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_kv_rmsnorm_rope_cache
---


# npu_kv_rmsnorm_rope_cache：四返回、950范围与底层选择

## 版本与范围

发布A2/A3的576维契约依据ascend_26_0_pt28；主线同名四返回接口新增950PR及DT的范围，按独立固定快照记录，主线配套尚未确认。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_kv_rmsnorm_rope_cache(kv, gamma, cos, sin, index, k_cache, ckv_cache, *, k_rope_scale=None, c_kv_scale=None, k_rope_offset=None, c_kv_offset=None, v=None, epsilon=1e-5, cache_mode='Norm', is_output_kv=False) -> (Tensor, Tensor, Tensor, Tensor)
```

发布A2/A3普通路线对kv的512维压缩分量做RMSNorm、64维位置分量做RoPE，并原地写入两份Cache；主线950可变尺寸和v分支分别见下文。返回顺序为 (k_cache,ckv_cache,k_embed_out,y_out)，前两项对应已更新 Cache；is_output_kv=True 才请求有效的非量化中间结果。此四返回入口与Python v2的双返回不同；两固定提交已存在的实现不等于公开产品范围相同。

## 参数与组合限制

- kv=(B,1,T,576)、FP16/BF16；gamma=(512,)，cos/sin=(B,1,T,64)。这些维度在该发布文档固定，不能从主线 v2 的可变尺寸扩展。
- 非量化 Cache 为 FP16/BF16。Norm 模式下为 (B,1,cache_length,64/512)，index 为 INT64(B,T)，按 batch 内偏移且 cache_length≥T。
- PA/PA_BNSD/PA_NZ 为全局 token 偏移，index=(B*T,)；PA_BLK_* 为页起始全局偏移，index=(B*ceil(T/block_size),)，只支持连续更新。页数至少 B*ceil(T/block_size)。所有模式索引不得重复，重复行为未定义。
- INT8 Cache 路径要求两份 FP32 scale 同时提供，形状分别为 (64,) 与 (512,)；offset 同时 None 或同时提供。来源参数段将 offset 写为量化必填，但组合约束允许同时 None，本卡保留该差异、按实际量化路线复核。
- NZ Cache 的物理尾块非量化为 16、量化为 32，不能按逻辑 ND shape 直接解释。is_output_kv 只在分页相关模式生效，默认 False 不保证中间输出有效。

## 验证与模型关联

同时检查 Cache 写入位置、原地副作用、四返回次序和请求的中间结果；用不同 token/page 索引验证单位，图模式保留输入 mutation。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L871)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [主线 v2 双返回及实现证据](npu_kv_rmsnorm_rope_cache_v2.md)

## 主线950范围与完整公式

主线中英文增加950PR及DT：hidden_size/rms_size/rope_size可以按业务设置，须rms_size+rope_size=hidden_size、rope_size为偶数。A2/A3仍固定576=512+64。这个扩展属于旧四返回接口自己的主线产品契约，不只是Python v2的功能，也不回推发布A2/A3。kv/gamma/cos/sin仍FP16/BF16、kv为(B,1,T,H)，index为INT64，缓存模式、唯一索引和页数要求继续生效。

发布页五张公式图片已逐张核对：拆分RMS与RoPE分支，RMS为gamma*rms_in/sqrt(mean(rms_in²)+epsilon)；RoPE先把64维尾轴reshape为(32,2)，交换最后两轴再展回64，才做k*cos+RotateHalf(k)*sin。RotateHalf是(-后半,前半)，不能跳过奇偶重排。主线512/64的公式属于示例，不能据此撤销950参数段的可变维度。主线中文中间输出shape采用rope_size/rms_size，英文仍写64/512，两种文字分别限定。

Norm缓存逻辑shape为(B,1,cache_length,D)；分页缓存逻辑shape为(pages,block_size,1,D)。NZ公开物理排布为(pages,D/16,block_size,1,16)，量化为(pages,D/32,block_size,1,32)，不通过改cache_mode字符串自动完成格式转换。PA_BLK_*的索引按页起点，要求更新连续；它不是逐token任意scatter。is_output_kv只在分页模式有效，返回的两份中间结果是量化前值。

## 缓存量化说明中的冲突

主线产品参数列出950的INT8、HiFloat8和两种FP8缓存，A2/A3明确排除三种8位浮点；但同页组合约束仍把量化缓存限定INT8。offset参数段又写A2/A3对称量化必填、950支持非对称且非对称必填，约束段却写两个offset暂不支持配置。中英文都保留这些冲突，不能由总类型名单推定FP8、偏移和所有cache模式的任意组合可用；需要准确运行包契约，普通路线保持原版本限定。

主线量化示例只将k_cache改为INT8，ckv_cache仍用input_dtype，与双INT8约束不符。Norm示例仅改mode和index、未完整重建缓存；BLK示例只改index_shape变量，未生成匹配的新index，且batch*(T+block_size-1)//block_size不总等于batch*ceil(T/block_size)。这些片段是需要补齐的说明，不是可直接运行的正确性证据。

## 包装中的v和别名

两固定schema/C++都另含公开原型遗漏的v=None，上方声明已补齐；它不是自动启用新路径的布尔开关。只有底层V2符号可用、v四维且尾维128时才取固定192/128中间输出，其他情况走V1并忽略v；详细分支、Meta差异与Python v2的区分见[npu_kv_rmsnorm_rope_cache_v2](npu_kv_rmsnorm_rope_cache_v2.md)。C++没有把所有无效v都转为明确拒绝。

旧四返回C++直接返回输入两份缓存的引用，schema却未标注可写别名，Meta为缓存返回empty_like占位；因此不能按schema外观当作无副作用函数。两固定GE旧接口转换器直接下传两份缓存和v，不在Converter里重现ACLNN的V1/V2选择。公开图示例设置keep_inference_input_mutations=True，但未在本仓执行。

## 已有 OpPlugin 7.3.0 文档与版本边界

### RMSNorm 与 RoPE 及 KVCache 写入融合：torch_npu.npu_kv_rmsnorm_rope_cache

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

融合了MLA（Multi-head Latent Attention）结构中RMSNorm归一化计算与RoPE（Rotary Position Embedding）位置编码以及更新KVCache的ScatterUpdate操作。

### 文档签名

```text
torch_npu.npu_kv_rmsnorm_rope_cache(kv, gamma, cos, sin, index, k_cache, ckv_cache, *, k_rope_scale=None, c_kv_scale=None, k_rope_offset=None, c_kv_offset=None, epsilon=1e-5, cache_mode='Norm', is_output_kv=False) -> (Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_kv_rmsnorm_rope_cache.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
