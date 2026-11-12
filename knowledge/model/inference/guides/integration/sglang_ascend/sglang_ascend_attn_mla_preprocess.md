---
type: Guide
title: SGLang Ascend MLA预处理：MLAPO、MLAProlog与权重生命周期
description: 按投影kernel类型选择MLA预处理模式，说明INT8/MXFP8量化布局、RoPE重排、NZ缓存和PD释放原始权重的前提。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/mla_preprocess.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/deepseek_v2_attention_mla_npu.py
  role: implementation
created_at: '2026-11-08T12:07:53Z'
updated_at: '2026-11-09T04:31:35Z'
platforms: []
aliases:
- NPUFusedMLAPreprocess
- MLAPO
- MLAProlog
---

# SGLang Ascend MLA预处理：MLAPO、MLAProlog与权重生命周期

## 触发与模式选择

`SGLANG_NPU_USE_MLAPO`控制融合预处理，`SGLANG_USE_FIA_NZ`独立控制缓存布局；NZ不要求MLAPO开启。`NPUFusedMLAPreprocess`根据q/kv两组投影的实际kernel类选择模式：浮点为0，legacy部分INT8为1，dynamic W8A8为2，MXFP8为3。仅查看weight dtype为INT8不足以选择模式。

先由uses_mlaprolog选择路线，进入forward_mlaprolog后才按无rotary选MLAProlog v4、有rotary选torch_npu v3。arch35直接选择MLAProlog；非arch35只有无RoPE且模式0或2时凭此条件直接启用，模式1或3还须满足其他选择条件（例如适用的kv_b_proj ignore分支），不能仅由无RoPE推导必经v4。其他路线是否继续legacy MLAPO还受DSA、是否extend、kv_b_proj和量化kernel条件影响，不能把所有阶段都融合。

## 权重和精度约束

legacy MLAPO将融合q+kv投影次序重排为kv+q，并同步RoPE偶奇重排、dequant scale和bias，缓存为NZ 16×32布局。动态INT8路径要求预期的[K,N]权重、正确的逐通道scale数，拒绝NeoX RoPE和非零RMSNorm bias。它保留原投影权重给extend和indexer使用；某些其他PD decode模式在拷入融合helper后会resize原storage为0，不能再引用原投影存储。

MXFP8权重要求ND矩阵及[K/64,N,2]配对E8M0 scale；还原为[N,K/32]时使用独立视图处理，避免修改仍存活的scale。模式3量化hidden使用block32 MX scale；模式2要求hidden_states、k_cache、v_cache和w_kc已经是BF16，否则直接抛RuntimeError；随后仅对hidden_states做逐token动态INT8量化，不替调用方转换输入或缓存。weightUk保留非量化形式。

packed FP8缓存只允许相应模式3路线。缓存为PA_BSND（packed或非NZ）或PA_NZ（普通NZ）；packed字段按tile128和repo模式传给接口。ModelSlim KV scheme开启kv/query量化参数及静态inverse K scale，Q的RoPE补偿与Q动态scale必须成对传递，不能只改cache dtype。

## 接入步骤、代价和验收

在加载后核对投影kernel类、矩阵方向、RoPE风格、norm bias与scale尺寸，再进行一次性权重重排；随后确认prefill/indexer还需要的原始权重没有被释放。融合helper返回兼容旧7/8元组，新增query descale通过包装维持调用契约。融合写缓存后由上层传save_kv_cache=False，防止第二次写入。

融合可减少投影、norm、RoPE和cache写的调用，但增加权重预排布与额外副本；不满足前提时保留分步路径。建议比较开关前后的prefill、decode、DSA indexer、量化Q/K scale与PD加载后首轮输出，同时检查原storage是否仍被读取。本次未编译或实测；本卡只描述固定源码的模型调用与数据生命周期。

## 配套知识

[MLA预处理接口](../../../apis/sgl_kernel_npu/sgl_mla_preprocess.md)；[MLAProlog v4接口](../../../apis/sgl_kernel_npu/sgl_mlaprolog_v4.md)。
