---
type: Guide
title: SGLang Ascend 注意力：GQA、MLA、DSA与阶段路由
description: 固定版本Ascend后端如何按prefill、decode、verify、CP和KV量化选择FIA、FA、稀疏或原生回退，并区分各路线的Host长度参与和DCP verify设备因果mask。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/mla_cache.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dcp.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dsa_dcp.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/base_attn_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_npu_prefill_cp_backend.py
  role: implementation
created_at: '2026-11-08T12:07:52Z'
updated_at: '2026-11-09T04:31:34Z'
platforms: []
aliases:
- AscendAttnBackend
- ASCEND_USE_FIA
- ASCEND_USE_FA
---

# SGLang Ascend 注意力：GQA、MLA、DSA与阶段路由

## 场景与入口

本卡是 `AscendAttnBackend` 的模型推理适配 reference。排查“同一 attention-backend 在不同阶段调用不同算子”时，先检查模型是否启用 MLA、是否传入 `topk_indices`、当前 ForwardMode、FIA/FA 开关、KV dtype、SWA和DCP；不能仅凭后端名称判断实际路线。源码没有为所有组合给出芯片支持矩阵，平台保持未知。

| 触发 | 执行路线与限制 |
| --- | --- |
| 传入TopK | 优先稀疏offload（若启用），否则 `forward_sparse`；不会落到普通dense MTP |
| target verify或draft extend v2 | `forward_mtp`；可选DSpark专用FlashMLA/页式MTP优先于普通FIA |
| 普通GQA/MHA prefill | 先写KV；FIA支持的head维度走TND，不满足时逐请求BSND；开FA时使用flash_attn_npu_v3 |
| 无FIA/FA的dense prefill | 合适的因果、小head、无encoder/logit cap走内部flash-qlens；cross attention、精度特例或logit cap走原生SDPA |
| 普通decode | 图且未compile、且非dense MLA DCP时走graph专用FIA；eager可选FIA、FA、paged attention或原生SDPA |
| dense MLA decode | FIA且Q/K head比至少8时返回attention并可请求LSE；非FIA MLA只返回输出且不支持graph/LSE |
| mixed chunk | 作为变长extend复用；无DSA TopK的dense MLA明确拒绝 |

## 长度、布局和缓存契约

dense MLA DCP target verify 用Host镜像限定本地页表读取上界，用设备seq_lens加query长度构造逐query因果mask，overlap期间两者可能不同。这个分工不适用于所有FIA路线：普通GQA FIA直接以seq_lens_cpu_int作为actual_seq_lengths_kv，dense MLA decode以seq_lens_cpu_list作为该参数，Host长度在这些分支也参与实际KV可见范围。没有CPU镜像时可用调度器发布的 `max_seq_len_host`（已分配页上界）限定页表；再没有则读取完整可用表宽，不能把捕获时的短长度固化为重放上界。DSpark/DFlash的verify host长度已扩张，普通Eagle/Ngram则需要加draft宽度，重复加宽会使读写越界。

GQA的SWA层读取SWA页表，写入使用 `KVWriteLoc(full,swa)`；cross attention写 `encoder_out_cache_loc`，不得套用由decoder full地址换算的SWA地址。DP填充时，TND eager先裁掉无效Q、匹配页表与长度行数，最后补零恢复物理输出形状。图使用固定页表、掩码和SWA地址缓冲，重放原地更新。

MLA缓存分为latent NoPE与RoPE。普通verify可为非2次幂head补齐、计算后截回；ModelSlim还须为补齐head提供query dequant scale=1。FIA v2使用动态Q scale和静态K/V scale；普通FIA通过workspace查询和out重载固定输出。DSA的FP8缓存走quant sparse算子，BF16 Q拼接NoPE/RoPE，tile128和rope维度必须匹配池布局；非FP8走普通sparse attention。

## 前缀、CP与回退

dense MLA prefill有prefix时，先加载并去量化latent历史，再经kv_b投影：QK/V维度相等的分支逐请求拼接历史和当前KV；另一路分别计算当前因果attention和全历史attention，再按LSE用 `npu_attention_update` 合并。零长度prefix必须把历史输出置0、LSE置负无穷，避免空历史影响归一化。无prefix时可用TND，某些value维度走原生SDPA。

GQA CP先按策略还原并all-gather完整K/V写池，FIA计算由CP策略提供prev/next分块；非FIA的GQA CP明确未实现。DSA CP以本地Q、全量已聚合KV和逐token页表做一次稀疏attention。dense MLA DCP保持rank-local页表和每query因果mask，要求LSE供跨rank合并；不能用无LSE的内部paged MLA替代。dLLM分支使用无因果mask的FIA，与普通自回归路线区分。

## 使用步骤与验收

1. 记录解析后的开关、模型head维度、cache格式和ForwardMode，定位上述实际分支。
2. 对同批请求分别核对host表宽上界、device有效长度、Q累计边界、full/SWA地址和DP padding行；verify核对长度只扩张一次。
3. 选择短/长prefix、混合请求长度、空DP rank、跨页和head补齐案例，与关闭图的同版本输出对比；这是建议验证方法，本次未执行。

回退到逐请求BSND或原生SDPA会增加主机同步、拼接与kernel开销；关闭图只能绕开捕获条件，不能补足缺失的CP或LSE实现。此处不声明完整Host/Device算子闭包，也不以路由存在证明所有硬件可运行。

## 补充调用与验证边界

CP manual全部在CPU张量和mock NPU模块下运行，验证CPv2 materialize_full_kv拥有完整KV写入、FIA闭包实际Q行数与cu长度一致、物理padding输出补回；历史错误561002只出现在说明，不是本次观测。示例物理4行、逻辑prev2+next1分别向FIA传Q2/Q1及累计长度[2]/[1]，最终恢复4行；它是控制流回归定义，不能证明真实NPU tiling或通信成功。
