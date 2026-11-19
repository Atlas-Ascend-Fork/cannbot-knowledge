---
type: API
title: MLA Prolog v2 五路前处理（torch_npu.npu_mla_prolog_v2）
description: torch_npu.npu_mla_prolog_v2：推理场景下，Multi-Head Latent Attention（MLA）前处理的计算。 文档按五路描述：Query 非 RoPE 分量、Query RoPE 分量、压缩 KV cache、RoPE key cache，以及 qN 经 DynamicQuant 得到的量化参数。 明确A2/A3旧V2的量化尺度、五输出次序及Cache突变声明缺口，限定迁移V3和数值验证范围。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mla_prolog_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MlaPrologV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mla_prolog_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MlaPrologV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mla_prolog_v2.py
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
- torch_npu.npu_mla_prolog_v2
- MLA Prolog v2
---


# npu_mla_prolog_v2：五种量化组合与非标准原地Cache

## 版本、维护建议与五路计算

固定OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013与主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c。发布属于ascend_26_0_pt28，主线配套未知。两版公开仅A2/A3，均说明两个Cache原地更新却未按标准in-place算子实现，建议以[V3](npu_mla_prolog_v3.md)替换；不能从V3推导本V2支持950，也不把V1的kernel不再维护声明自动移给V2。

V2在[V1四路前处理](npu_mla_prolog.md)基础上增加query的动态量化路径：cQ=RMSNorm(x@WDQ)，qN=(cQ@WUQ)@WUK，qR=RoPE(cQ@WQR)，kC=Cache(RMSNorm(x@WDKV))，kR=Cache(RoPE(x@WKR))；全量C8组合再对qN按token/head动态量化。两组RMSNorm eps分别可设，默认1e-5。

公开动态量化公式为scale=max(abs(qN),末轴)/127，qN_int8=round(qN/scale)。文档没有描述全零行scale0的保护策略，未测试时不补造epsilon或clip规则。量化后的Q必须与对应反量化尺度一起消费，不能只把query cast回BF16。

## 参数、固定维度与返回顺序

必传位置参数为token_x、weight_dq、weight_uq_qr、weight_uk、weight_dkv_kr、gamma_cq、gamma_ckv、rope_sin、rope_cos、cache_index、kv_cache、kr_cache；scale、epsilon、cache_mode为关键字。输入名称中的gamma在API中完整写作rmsnorm_gamma_cq/rmsnorm_gamma_ckv。

|输入|shape、dtype与布局|
|--|--|
|token_x|ND[T,He]或[B,S,He]，BF16/INT8按组合|
|weight_dq|FRACTAL_NZ[He,Hcq]，BF16/INT8按组合|
|weight_uq_qr|FRACTAL_NZ[Hcq,N*(D+Dr)]，BF16/INT8按组合|
|weight_uk|BF16 ND[N,D,Hckv]|
|weight_dkv_kr|FRACTAL_NZ[He,Hckv+Dr]，BF16/INT8按组合|
|gamma_cq / gamma_ckv|BF16 ND[Hcq] / [Hckv]|
|rope_sin / rope_cos|BF16 ND[T,Dr]或[B,S,Dr]|
|cache_index|INT64 ND[T]或[B,S]，与同次token对应的线性页槽位|
|kv_cache / kr_cache|ND[BlockNum,BlockSize,Nkv,Hckv或Dr]，dtype见组合表|

He7168、Hcq1536、Hckv512、D128、Dr64、Nkv1固定；N仅1/2/4/8/16/32/64/128。B0..65536、S0..16、T0..1048576；BlockSize16或128。NZ权重须真正做格式转换，不用reshape代替。

返回顺序为(query,query_rope,kv_cache_out,kr_cache_out,dequant_scale_q_nope)：尺度是第五项，不按V3次序解包。query为[T,N,Hckv]或[B,S,N,Hckv]；query_rope为[T,N,Dr]或[B,S,N,Dr]且BF16；两个Cache shape/dtype对应输入。尺度FP32，在全量C8组合为[T,N,1]或[B*S,N,1]，其他组合仅[1]。三维token的尺度仍将B*S合轴，不能当[B,S,N,1]。

## 五种组合必须整体选择

所有组合的weight_uk、gamma和RoPE输入仍BF16；DQ/UQ/QR/DKV缩写对应上表的三个NZ权重。这里的“全量化”描述INT8激活与权重，和模型prefill/decode阶段不是同一分类。

|组合|token / DQ / UQ-QR / DKV-KR|KV / KR Cache|query / query_rope|必需量化尺度|
|--|--|--|--|--|
|非量化|全部BF16|BF16 / BF16|BF16 / BF16|无|
|部分量化、Cache不量化|BF16 / BF16 / INT8 / BF16|BF16 / BF16|BF16 / BF16|UQ-QR反量化|
|部分量化、Cache量化|BF16 / BF16 / INT8 / BF16|INT8 / INT8|BF16 / BF16|UQ-QR反量化、CKV与CKR量化|
|全量化、Cache不量化|全部INT8|BF16 / BF16|BF16 / BF16|x、DQ、UQ-QR、DKV-KR反量化|
|全量化、Cache量化|全部INT8|INT8 / BF16|INT8 / BF16|x、三权重反量化及CKV量化；CKR不量化|

只有最后一组合给出per-token-head Q尺度，其余[1]为占位描述，不承诺数值为1、更不应用于一般Q反量化。全部组合不能按单参数dtype支持集合做笛卡尔积，尤其不能把全量C8的KR也改INT8。

|尺度|FP32 ND形状与位置|
|--|--|
|dequant_scale_x|[T,1]或[B*S,1]，激活pertoken，输入INT8时下采样后反量化|
|dequant_scale_w_dq|[1,Hcq]，DQ perchannel反量化|
|dequant_scale_w_uq_qr|[1,N*(D+Dr)]，合并投影后perchannel反量化|
|dequant_scale_w_dkv_kr|[1,Hckv+Dr]，DKV/KR投影后perchannel反量化|
|quant_scale_ckv|[1,Hckv]，KV写回量化|
|quant_scale_ckr|[1,Dr]，仅部分量化C8的KR写回量化|
|smooth_scales_cq|[1,Hcq]，量化组合中RMSNormCq后的动态量化平滑|

表把smooth_scales_cq列入量化组合，非量化列无需赋值；它的必传性不能仅从可选Schema判断。部分量化场景说明称UQ-QR是pertoken量化，但参数定义为perchannel反量化；全量C8的CKV又称pertensor，却给[1,Hckv]形状，需核对实际数值是否按通道重复，不自行推导任意通道尺度。主线英文全量C8输入描述还漏列KV量化，中文和完整dtype表均列INT8，应保留这一语言差异。

发布dequant_scale_w_dq文案错误指向token_x的perchannel、DKV尺度错误写成MatmulQcQr后处理；主线已改为各自权重投影。不能把这些发布文字误当两份激活尺度，或把query尺度与Cache写回量化系数交换。

## 槽位、空输入与Cache突变

主线cache_index要求每项在[0,L)，L为KV前两轴乘积且等于KR前两轴乘积；发布按[0,BlockNum*BlockSize)描述且明确内部不校验值。主线BlockNum至少ceil(B*Skv/BlockSize)，发布写等于。槽位需对应真实分页管理，不能用随机索引证明token身份正确。

cache_mode支持PA_BSND（默认）/PA_NZ；文档主要给逻辑四维shape，不能按名称自行外推PA_NZ物理打包或直接复制V3空KR Cache约定。

公开允许B/S/T/Skv0；前三者0时query、query_rope及Q尺度为空且Cache不更新，Skv0时Q与尺度正常计算、Cache空且不更新。V2包装没有V1的全部必传输入numel>0检查，但实际空输入仍需后端验收。非量化等分支无论token是否为空都分配尺度[1]，与“前三者0时尺度为空”文字存在shape冲突；Meta同样保留[1]。不能仅凭文档或Meta推出所有空分支已一致。

两版Eager调用aclnnMlaPrologV2WeightNz，直接把输入kv_cache/kr_cache返回为第三/四项，没有另分配Cache输出；Schema却没有(a!)/(b!)别名突变标签，Meta返回独立empty_like，TorchAir转换器只返回生成GE的五输出。标准编译器可能据Schema理解成无副作用，不能忽略文档迁移提示；真实验收要检查输入存储变化、返回别名、图依赖与重复回放，不以输出内容碰巧相同代替别名合同。

## 实现分支、参考与验证缺口

两版包装拒绝IsAclnnOnly，Meta拒绝soc_version≥260，均提示V3。只有token_x为INT8且quant_scale_ckv非None时，包装/Meta将query设INT8并分配逐token/head尺度；其他分支query dtype取rope_sin、尺度[1]。该条件本身没有检查Cache dtype或所有必需尺度，不能把一次输出分配成功当完整组合已合法。query_rope固定BF16。

生成GE IR比公开表宽，可包含FP16等dtype，但转换器没有逐组合/索引值校验或Eager平台拒绝逻辑，不认证额外产品或混合dtype。两版后端调用没有提供“新符号缺少自动回退旧版本”的路径。

唯一A2测试方法无条件skip，测试主线366行与发布仅末尾换行不同。它仅覆盖3D token、全量C8、PA_BSND、BlockSize128/N32；query以INT8允许误差1，其余及尺度0.005，未覆盖其他四组合、PA_NZ、空输入、A3、图或性能。

参考在算子执行后才把Cache转CPU，会以已更新的输入Cache为基线，不能独立检查未写槽位是否被破坏；quant_scale_ckv还只取第一列。参考对query_rope额外乘CKV量化系数/Q反量化尺度比，而通用公式只写RoPE，说明全量C8分支数值合同不能靠通用公式和dtype推断。该未运行参考不是可以直接移植的全模式精度标杆。

主线样例将全0 cache_index改为范围内randint，修正了线性槽位说明；仍只打印结果，graph后Eager复用同Cache、不比较完整五输出和副作用。迁移V3应按其Schema重核位置/关键字、返回次序、量化模式和别名，保留独立初始Cache做Eager/图对照。本次仅静态审查，无上游、NPU/分布式/图/性能实验，无新增verified。

- [模型MLA概念](../../concepts/kernels/mla_prolog.md)
- [图Cache适配边界](../../optimizations/rules/graph_mode_kvcache_inplace_mla_prolog_adaptation.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### MLA Prolog v2 五路前处理：torch_npu.npu_mla_prolog_v2

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

推理场景下，Multi-Head Latent Attention（MLA）前处理的计算。

### 输入、输出与行为

文档按五路描述：Query 非 RoPE 分量、Query RoPE 分量、压缩 KV cache、RoPE key cache，以及 qN 经 DynamicQuant 得到的量化参数。前四路与第五路的输出协议不能混用。

### 文档签名

```text
torch_npu.npu_mla_prolog_v2(token_x, weight_dq, weight_uq_qr, weight_uk, weight_dkv_kr, rmsnorm_gamma_cq, rmsnorm_gamma_ckv, rope_sin, rope_cos, cache_index, kv_cache, kr_cache, *, dequant_scale_x=None, dequant_scale_w_dq=None, dequant_scale_w_uq_qr=None, dequant_scale_w_dkv_kr=None, quant_scale_ckv=None, quant_scale_ckr=None, smooth_scales_cq=None, rmsnorm_epsilon_cq=1e-05, rmsnorm_epsilon_ckv=1e-05, cache_mode="PA_BSND") -> (Tensor, Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mla_prolog_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v2.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v2.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v2.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MlaPrologV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mla_prolog_v2.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MlaPrologV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mla_prolog_v2.py)（example）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
