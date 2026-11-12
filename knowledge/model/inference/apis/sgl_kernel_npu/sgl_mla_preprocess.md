---
type: API
title: SGLang MLA预处理的量化、缓存模式与原地输出
description: 说明arch22的MLA融合预处理、FRACTAL_NZ权重、四个预分配输出及cache_mode精度和布局限制。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/mla_preprocess.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/mla_preprocess/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/mla_preprocess/op_host/mla_preprocess_tiling.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/mla_preprocess/op_kernel/mla_preprocess.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/operators/attention/test_mla_preprocess.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/mla_preprocess/op_kernel/mla_preprocess_mix_fp16.hpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/mla_preprocess/op_kernel/mla_preprocess_mix_bf16.hpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mla_preprocess/op_host/mla_preprocess.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mla_preprocess/op_kernel/mla_preprocess_kernel.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mla_preprocess/op_host/tiling/mla_preprocess_tiling.h
  role: header
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T18:01:44Z'
platforms:
- a2
- a3
---

# SGLang MLA预处理的量化、缓存模式与原地输出

## 接口原型

```python
from sgl_kernel_npu.operators.attention import mla_preprocess

def mla_preprocess(
    hidden_state,
    gamma0,
    beta0,
    wdqkv,
    descale0,
    gamma1,
    beta1,
    wuq,
    descale1,
    gamma2,
    cos,
    sin,
    wuk,
    kv_cache,
    kv_cache_rope,
    slotmapping,
    *,
    quant_scale0,
    quant_offset0,
    bias0,
    quant_scale1,
    quant_offset1,
    bias1,
    ctkv_scale=None,
    q_nope_scale=None,
    cache_mode="krope_ctkv",
    quant_mode="per_tensor_quant_asymm",
    q_out0,
    kv_cache_out0,
    q_out1,
    kv_cache_out1,
    impl="auto",
):
    ...
```

## 数据流与入口

`mla_preprocess` 融合MLA前处理：静态非对称量化、INT8矩阵乘和反量化、latent/query拆分、RMSNorm、Query吸收权重、half旋转RoPE与分页缓存写入。原生仅arch22；auto固定选择Ascend C，不自动切换参考。它不是attention计算入口。

hidden_state为FP16/BF16 `[N,H]`，N=1..1024、H=2048..8192。第一次INT8权重逻辑 `[2112,H]`，拆分latent576和query1536；latent又分512 NoPE和64 RoPE。第二次INT8权重逻辑 `[headNum*192,1536]`，每头拆128 NoPE和64 RoPE；NoPE再乘 `[headNum,128,512]` wuk。两份INT8权重在NPU须FRACTAL_NZ，使用format_cast(29)而非手工reshape，并启用internal_format。

量化scale/offset与INT32 bias两组均需提供。FP16输入的descale为int64，BF16输入的descale为FP32。RMSNorm epsilon为1e-6；RoPE按前后两半旋转，不是KDA/Compressor的交错配对。slotmapping为int32 `[N]`，调用方保证合法槽位，全部tensor同NPU。

## 四个输出与cache_mode

调用方预分配并传入 `q_out0,kv_cache_out0,q_out1,kv_cache_out1`，函数原地写入后按此顺序返回。按接口合同，调用方应让kv_cache_out0与kv_cache、kv_cache_out1与kv_cache_rope分别使用同一storage；adapter检查同设备和相关dtype等条件，但未检查storage相等。两套Device Init把实际写目标绑定到cache输出指针，不能保证传入不同storage时输入cache也被更新。比较后端须使用独立的cache/输出组，并在每组内满足别名前提。

| 模式 | Q与缓存形态及边界 |
| --- | --- |
| kvcache | ND，NoPE512+RoPE64合并，q_out0为 `[N,heads,576]`，q_out1不用。 |
| krope_ctkv | ND，两份Q分别512/64，缓存分开。 |
| int8_nzcache | BF16输入，NoPE缓存与q_out0为INT8，NZ的C0=32；须非空ctkv_scale和每头q_nope_scale，blockSize=128。 |
| nzcache | BF16输入，NZ按C0=16分组，blockSize=128。 |

API 文档只将 FP16 列为 krope_ctkv，但固定 adapter/Host 允许 cache_mode 0/1，即 kvcache 与 krope_ctkv；Device 也有 FP16 kvcache 分发，测试定义了两种 FP16 模式。保留此文档与实现差异，这些测试本次未运行，不能写成真机验证结果。

NZ物理布局为 `[blocks,groups,blockSize,C0]`。quant_mode仅实现per_tensor_quant_asymm（qmode0）。adapter也接受per_token_quant_symm并映射为1，显式None同样默认到1；但固定Device仅有六个qmode0分支，没有qmode1匹配，不能把adapter接受等同实现支持。未知字符串由adapter拒绝。参考使用FP32并保留规定取整边界，仅用于数值对比。验证同时检查Q两分量、slot对应cache写入、未写槽保持，以及FRACTAL_NZ和各精度模式限制。

## 旧legacy Direct入口与静态上传区

旧`torch.ops.npu.mla_preprocess`由`csrc/mla_preprocess/op_host/mla_preprocess.cpp`直接tiling/launch；前文新adapter的维度、dtype、设备与别名检查不能移作其Host保证。它原样使用四个caller输出并返回四个Tensor引用；未分配或重新绑定输出storage。独立输入kv_cache_rope在这个Host签名中出现，但没有进入launch参数序列；实际cache写目标仍须按Device输出指针解释。

旧cache_mode map仅含krope_ctkv=1、int8_nzcache=2、nzcache=3，不含新入口的kvcache=0；None默认krope_ctkv。旧quant_mode只有per_tensor_quant_asymm=0/per_token_quant_symm=1，None默认**1**。Host据是否BF16、cache与quant生成key：`(isBF16<<8)|cacheMode|(quantMode<<3)`。已读旧Device switch仅有六个qmode0 key：FP16 cache0/1、BF16 cache0/1/2/3；因此旧Host正常字符串能产生有效body的交集仅FP16 c1或BF16 c1/2/3且qmode0。None默认qmode1会落default无body，不能由Host接收字符串推成计算支持；cache0虽有Device模板，也没有这个旧map的公开producer。

缺省ctkv_scale/q_nope_scale各分配同hiddenState设备的FP16 `empty([1])`，内容未初始化，既不是null指针也不是有效scale=1。是否读取由对应cache/dtype分支决定，不能当作任意INT8缓存的有效默认。Host直接用hiddenState第0/末维、wuk第0维取N/H/head，N及head先窄化I32，再转入U32参数；本函数没有先做新adapter那套完整shape/dtype/同设备/contiguous检查。计算RopeConcatTiling、EinSumQuantTiling等发生在N范围检查之前，零N/head/core及超范围值可能先进入除模/下溢，不能靠最后bIndex检查兜底。

Host向Device依次传hiddenState、两组gamma/beta/quant/bias、gamma2，然后sin/cos两次、kv_cache、slotmapping、两投影权重和descale、两optional scale、四输出、workspace与tiling。sin/cos共四槽是旧kernel ABI的一部分，不能按Python形参只有一对就删掉后两槽。blockDim固定平台AIC数，query/latent处理核数另写POD。

令每token最大stage片大小F=max(s1Factor,2*head*192,2*2112,4*max(head*192,2112))，其中cache2的s1Factor=max(H,2*head*512)，其它为H；Q=N*F。BF16或qmode1时userWorkspace=4Q+8N，其它=3Q；Host再加libAPI系统workspace一次，用hiddenState设备Byte tensor分配。POD s1..s5 offset依次0/Q/2Q/3Q/4Q，Device直接从传入workspace基址加offset，不另外跳过libAPI前缀。s4/s5是否读取依所选body，不能把声明offset当所有route都已实际分配/消费。

静态tiling allocation为`sizeof(MlaTilingData)*1024*3`，设备只在首次调用时选定。偏移为`sizeof(POD)*(1024*(cacheMode−1)+(N−1))`；每次重做Host tiling并同步H2D memcpy，N−1必须在0..1023，否则抛错。缓存槽只按cacheMode和N区分，**不按dtype、H、head、quantMode或stream区分**；同槽配置变化会覆盖，跨设备仍指向首设备allocation，不能当成并发安全的内容缓存。

局部写法虽为`MlaTilingData tilingData;`，该旧header具有默认成员初始化：大多数字段初值0，hiddenStateDim初值7168并由Init覆盖；不能仅因没有{}就把这些字段说成未初始化。Init逐子过程赋值，天然padding字节不具有同样的零值保证；旧Device entry还按字段手工复制到本地结构，并非整份Host POD逐字节搬入。NPU槽经没有owner的from_blob Byte view传入；宏只捕获裸data_ptr与标量，并使用当前NPU stream。static tiling、每调用workspace、optional占位、输入/输出的异步生命周期职责不同，没有在此Host建立完整隔离或完成同步。这里保留旧Direct的入口、默认、POD上传与失败边界；完整数学实现仍分别见两张新ACLNN源码卡，不将它们的ABI/guard整体移给旧入口。本次未执行编译、真机或数值验证。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [另一个五输出的MLA Prolog V4接口](sgl_mlaprolog_v4.md)
- [浮点缓存路径的完整源码与静态边界](../../operators/aclnn/transformer/attention/sgl_mla_preprocess_float_cache.md)
- [INT8缓存路径的量化、布局与资源](../../operators/aclnn/transformer/attention/sgl_mla_preprocess_int8_cache.md)
