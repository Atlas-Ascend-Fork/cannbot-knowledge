---
type: API
title: MLA 推理前处理（torch_npu.npu_mla_prolog）
description: torch_npu.npu_mla_prolog：MLA 推理前处理。推理场景下，Multi-Head Latent Attention（MLA）前处理的计算。 记录A2/A3旧MLA前处理、量化与Cache合同，明确空输入及别名冲突、跳过测试与迁移核验边界。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mla_prolog.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mla_prolog.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MlaPrologKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mla_prolog.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MlaPrologKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mla_prolog.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:45Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_mla_prolog
---


# npu_mla_prolog：计划废弃的V1前处理入口

## 维护状态、固定版本与用途

OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5和主线d84e9b1d6a558e5f27973cd4329f62968e46fdda两版都明确：本接口计划废弃，底层kernel不再维护、不保证性能和精度，不推荐使用。本文保留既有模型维护的查询入口；卡片stable表示知识生命周期，不构成推荐或运行认证。公开产品仅A2/A3，没有950。配套TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013、主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c；发布属于ascend_26_0_pt28，主线混配未知。

用于推理MLA前处理，融合Q下采样、RMSNorm、Q上采样与WUK映射、Q RoPE，以及KV下采样/RMSNorm、K RoPE和Cache写入。公式为cQ=RMSNorm(x@WDQ)，qN=(cQ@WUQ)@WUK，qR=RoPE(cQ@WQR)，kC=Cache(RMSNorm(x@WDKV))，kR=Cache(RoPE(x@WKR))。两组RMSNorm epsilon分别可设、默认1e-5；归一化沿各自末轴，不把公式中的N与attention head数混为一维。

## 输入组合与四输出

必传位置参数依次为token_x、weight_dq、weight_uq_qr、weight_uk、weight_dkv_kr、rmsnorm_gamma_cq、rmsnorm_gamma_ckv、rope_sin、rope_cos、cache_index、kv_cache、kr_cache；其后可选scale、epsilon及cache_mode为关键字。

|参数|公开shape与dtype/布局|
|--|--|
|token_x|BF16 ND[T,He]或[B,S,He]|
|weight_dq|BF16 FRACTAL_NZ[He,Hcq]|
|weight_uq_qr|BF16或INT8 FRACTAL_NZ[Hcq,N*(D+Dr)]，将UQ与QR合并|
|weight_uk|BF16 ND[N,D,Hckv]|
|weight_dkv_kr|BF16 FRACTAL_NZ[He,Hckv+Dr]|
|gamma_cq / gamma_ckv|BF16 ND[Hcq] / [Hckv]|
|rope_sin / rope_cos|BF16 ND[T,Dr]或[B,S,Dr]，与token前缀配套|
|cache_index|INT64 ND[T]或[B,S]，值在[0,BlockNum*BlockSize)|
|kv_cache / kr_cache|BF16或INT8 ND四维[BlockNum,BlockSize,Nkv,Hckv或Dr]|

三个NZ权重可用npu_format_cast转换，不能只改view或把ND权重地址解释成NZ。weight_uk仍为ND。cache_mode支持PA_BSND（默认）和PA_NZ，但本页只给上述逻辑四维shape，没有完整列PA_NZ物理重排，不能直接套用V3或特定模型的打包布局。

返回(query,query_rope,kv_cache_out,kr_cache_out)：前两者为BF16 ND[T,N,Hckv/Dr]或[B,S,N,Hckv/Dr]，后两者与输入Cache的shape/dtype对应。qN不是未经过WUK的qC，也不是普通attention的最终context。

固定维度He=7168、Hcq=1536、Hckv=512、D=128、Dr=64、Nkv=1；N在1/2/4/8/16/32/64/128。B在0..65536、S在0..16、T=B*S在0..1048576；BlockSize仅16或128，BlockNum=ceil(B*Skv/BlockSize)。不能把这些固定低秩维数外推为任意MLA模型可用。

## 部分量化与尺度位置

weight_uq_qr为INT8时是部分权重量化；其余主权重和token仍BF16。若两Cache为BF16，必须给dequant_scale_w_uq_qr，smooth_scales_cq可选；若两Cache为INT8，还必须给quant_scale_ckv和quant_scale_ckr。weight_uq_qr为BF16非量化时，这四项均None，不按Cache参数单独列INT8就推导无尺度量化组合成立。

|尺度|公开合同与计算位置|
|--|--|
|dequant_scale_w_uq_qr|FP32 ND[1,N*(D+Dr)]，MatmulQcQr后perchannel反量化|
|smooth_scales_cq|FP32 ND[1,Hcq]，RMSNormCq输出的动态量化平滑尺度|
|quant_scale_ckv|FP32 ND[1,Hckv]，写入KV Cache前量化|
|quant_scale_ckr|FP32 ND[1,Dr]，写入RoPE Cache前量化|

文档称INT8 weight_uq_qr是pertensor量化输入，随后却把其反量化scale定义为perchannel形状；保留两处表述差异，不自造单标量广播配方。dequant_scale_x、dequant_scale_w_dq、dequant_scale_w_dkv_kr在本V1均为预留None，不能因IR或V3接受全权重量化就启用。这里没有V3的query_quant_mode或额外dequant_scale_q_nope输出。

## 文档与包装实现的冲突

文档允许B/S/T/Skv为0：B/S/T0时两个query为空且不更新Cache；Skv0时query仍计算、Cache为空不更新。但两版Eager包装逐一检查全部12个必传Tensor numel>0，任一为空都会在ACLOP前拒绝。Meta仅检查不为None及部分rank，不验证numel，因此Meta成功也不证明公开空输入在Eager可用。

两版实现走ACLOP OpCommand("MlaProlog")，在入口与内部都拒绝IsAclnnOnly平台并提示使用npu_mla_prolog_v3；Meta拒绝soc_version≥260。不要以生成GE的宽dtype列表推导950或其他ACLNN-only设备支持。三个公开预留scale虽可由包装透传也不构成公开能力。

文档把两个Cache输出称in-place更新，但Schema没有别名/突变标签，Eager为cache_out另行apply_tensor_without_format，未显式把结果copy回Cache输入；Meta也独立empty_like。生成GE建四个输出节点，没有在该转换器显式绑定Cache别名。因此不能仅凭文档省略返回Cache、或把V3“仅从输入cache读取”的模型改法直接用于V1。底层是否另有原地语义需真实核验，静态包装不能证明输入完全未改变，也不能证明一定共享存储。

非连续输出分支构造contiguous_query/Cache变量，但调用nocheck仍传原输出，再format_fresh_view；这是静态分支疑点。新分配输出是否实际进入该分支未验证，不能写成必现精度故障或把它当通用连续性修复配方。

Eager query dtype取token_x，Meta却取rope_sin；公开均BF16时一致，宽输入分支不据此认证混合dtype。eps在Eager转float传给ACLOP，图写float attr；均只描述传参，不替代数值精度核验。

## 图、Cache索引与测试边界

两版TorchAir转换器仅将全部输入、可选项和attrs映射为ge.MlaProlog，生成函数保留可选空槽并返回四输出，没有本地验证Cache索引值、维护状态或Eager平台门禁。公开说明内部不校验cache_index取值，调用方需确保容量边界和真实槽位对应；不能用随机float转int64的全0索引证明分页路由正确。

两版测试文件字节相同，只有两个A2方法，分别3D[B,S,He]和合轴2D[T,He]，都因CANN过旧而无条件skip。参考覆盖四输出0.005容差、包含分段BF16截断、交错RoPE重排及Cache逐槽写入，但输入和参考多数仍在NPU，不是独立CPU精度证据；仅非量化PA_BSND、BlockSize128、N32，索引全部0，没有量化、PA_NZ、空输入、A3或图性能验收。重复槽位的覆盖/竞争行为也未被独立隔离验证。

文档图样例先graph后Eager复用同一Cache，只有打印且没有assert；发布示例还把TORCHDYNAMO_VERBOSE/TORCH_LOGS写为普通Python变量，主线改为环境变量。样例输出文字不构成两模式独立、可复现实测。

迁移到[V3入口](npu_mla_prolog_v3.md)应重新核对位置/关键字、返回次序、量化模式、索引与Cache别名、空输入及软件配套，不只替换函数名。[MLA模型概念](../../concepts/kernels/mla_prolog.md)描述的是具体模型V2/V3及PyPTO分派，不作为本V1的额外支持合同。本次只做固定来源静态审查，无上游执行、设备/图/性能实验，无新增verified。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MLA 推理前处理：torch_npu.npu_mla_prolog

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

推理场景下，Multi-Head Latent Attention（MLA）前处理的计算。

### 文档签名

```text
torch_npu.npu_mla_prolog(token_x, weight_dq, weight_uq_qr, weight_uk, weight_dkv_kr, rmsnorm_gamma_cq, rmsnorm_gamma_ckv, rope_sin, rope_cos, cache_index, kv_cache, kr_cache, *, dequant_scale_x=None, dequant_scale_w_dq=None, dequant_scale_w_uq_qr=None, dequant_scale_w_dkv_kr=None, quant_scale_ckv=None, quant_scale_ckr=None, smooth_scales_cq=None, rmsnorm_epsilon_cq=1e-05, rmsnorm_epsilon_ckv=1e-05, cache_mode="PA_BSND") -> (Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mla_prolog.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mla_prolog.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MlaPrologKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mla_prolog.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MlaPrologKernelNpu.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mla_prolog.py)（example）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
