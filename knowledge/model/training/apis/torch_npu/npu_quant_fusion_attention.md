---
type: API
title: npu_quant_fusion_attention：量化QKV训练打分与前反向的950入口
description: 保存固定无dropout/全窗语义、dequant scale门槛、950前向query_dtype必传的发布/主线差异、BF16输出分配、pre-950分派边界与Meta静态缺陷。
tags:
- task.lookup
- topic.attention
- topic.compute.quantization
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionV2KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_flash_attention_grad.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_flash_attention_grad.py
  role: example
created_at: '2026-11-12T05:36:44Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# npu_quant_fusion_attention：量化QKV训练打分与前反向的950入口

## 版本与范围

本卡依据 OpPlugin 主线候选 d84e9b1d6a558e5f27973cd4329f62968e46fdda 与发布 dedc316708372c9a8bfde4527abd2a94b74840f5。两个 schema 在主线与发布两版本 的 yaml 登记原文相同（`op_api: [v2.1, newest]`）；实现文件主线与发布两版本 存在 5 个 diff hunk，其中一处是对本入口的直接语义变更（见「版本边界」）。OpPlugin 仓库没有该接口的官方 API 文档页，codegen 模板也没有 docstring；`derivatives.yaml` 无自动微分接线，反向是显式 schema，由调用方自行衔接。两份官方用例均标注 `SupportedDevices(['Ascend950'])`。本文为静态源码/用例审阅，未执行任何上游或设备测试。

## 调用与固定语义

```python
attention_out, softmax_max, softmax_sum, softmax_out, seed, offset, numels = torch_npu.npu_quant_fusion_attention(
    query, key, value, head_num, input_layout,
    d_scale_q=..., d_scale_k=..., d_scale_v=..., p_scale=None, scale=1., query_dtype=None)

dq, dk, dv, dpse, dq_rope, dk_rope, dsink = torch_npu.npu_quant_fusion_attention_backward(
    query, key, value, dy, head_num, input_layout,
    d_scale_q, d_scale_k, d_scale_v, d_scale_dy,
    p_scale=None, ds_scale=None, softmax_max=None, softmax_sum=None, attention_in=None,
    scale_value=1., query_dtype=None)
```

前向 wrapper 在共用 common 前固定一批参数，调用方无法覆盖：`keep_prob=1.0`（无 dropout）、`pre_tokens=next_tokens=2147483647`（全窗）、`inner_precise=0`、`sparse_mode=0`、`pse_type=1`、`softmax_layout=""`、`out_dtype=0`、`gen_mask_parallel=false`、`sync=false`、`seed=offset=0`；pse/padding_mask/atten_mask/query_rope/key_rope/sink/dropout_mask 全部为未定义 `at::Tensor()`，prefix 与 actual_seq 列表为空。即这是一个无掩码、无 PSE、无 RoPE、无变长的"干净"量化打分入口，与 [npu_fusion_attention_v2](npu_fusion_attention_v2.md) 的完整参数面互补。

返回七元组结构与 v2 相同：`attention_out` 随 Q 布局、尾维为 Dv；`softmax_max/softmax_sum` 为 FP32 统计（供反向）；`softmax_out` 为 `{0}` 形状占位；`seed/offset` 保持 wrapper 初始 0（keep_prob 固定 1.0，不触发 philox 获取），但 `numels` 由 mask helper 按布局形状计算——BSH/SBH/BNSD/BSND 都是各维乘积，不是固定 0，不要对返回的 numels 做 0 假设。

## host 检查分层

| 检查 | 层级 | 行为 |
|--|--|--|
| 每个已定义输入经 `format_trans` | 运行时 C++ host | `TORCH_CHECK is_npu`（TYPE 错误）后转 `ACL_FORMAT_ND` |
| query/key/value（反向另加 dy）3/4 维 | 运行时 C++ host | PARAM 错误 |
| `input_layout` 非空 | 运行时 C++ host（主线新增，发布无此检查） | PARAM 错误 |
| 布局枚举 BSH/SBH/BNSD/BSND/TND | 运行时 C++ host | 转大写后校验，大小写不敏感；前向 common 中精确匹配的大写 `TND` 在转大写前另受 actual_seq 两列表非空守卫（前向 quant wrapper 列表固定为空，见「输出分配」TND 可达性（前向）） |
| is_fp8 门槛：前向 d_scale_q/k/v/p_scale 至少一个有值；反向 d_scale_q/k/v/dy 至少一个 | 运行时 C++ host | PARAM 错误（"No fp8-related ... inputs"） |
| 950 前向 `query_dtype` 必传（主线） | 运行时 C++ host | PARAM 错误；host 仅检查 `has_value`，不校验取值等于 hifloat8，错误文案 "shall only be set to hifloat8" 是提示而非枚举强制 |
| `make_wrapper` itemsize 一致性 | 运行时 C++ host | 按声明 dtype 解析 aclDataType 后仅检查 itemsize 相等，无 hifloat8 专属守卫（uint8 存储+hifloat8 因 1==1 通过；FP16 存储对 hifloat8 因 2≠1 拒绝）；不据此承诺 hifloat8 之外 dtype 可用 |

schema 前向把三个 d_scale 声明在 `*` 之后：必选但仅限关键字传参；反向的 d_scale_q/k/v/dy 为位置参数，`*` 之后才是 p_scale/ds_scale 等可选关键字项。因此 is_fp8 门槛实际保护的是共用 common 的其他内部调用方。反向 host 不强制 `query_dtype`（主线与发布两版本 相同）：省略时 `make_wrapper` 退回张量自身 scalar_type（uint8 存储会按 UINT8 语义包装），与主线前向的强制检查不对称，混用时需自查。

## 输出分配

- 前向 `attention_out` 固定 BF16（`is_fp8` 分支不看 out_dtype 参数），形状按布局：BSH/SBH 为 `(B/S维, S/B维, query.size(2)*value.size(2)/key.size(2))`，BNSD `(B,N,S,Dv)`，BSND `(B,S,N,Dv)`；common 中另有 TND `(T,N,Dv)` 分配分支（可达性见下条）。
- `softmax_max/softmax_sum`：非 TND 为 `[B, head_num, S0, 1]` FP32——`is_fp8` 路径末维是 1，同文件非量化路径是 8，不要按 v2 卡的 8 宽统计套用；common 的 TND 分支为 `[T, N_local, 8]`（可达性见下条）。
- TND 可达性（前向）：前向 quant wrapper 固定 actual_seq 列表为空；前向 common 的非空守卫按精确字符串 `"TND"` 匹配且先于大小写转换，大写 `TND` 直接被该守卫拒绝。小写 `tnd` 绕过精确匹配，转大写后仍进入 TND 分支，并以空列表访问 `ac_seq_qlen[0]`——静态读码为无检查访问，失败形态未验证。上两行的 TND 形状是与 v2 共用的 common 分配分支，不要据此宣称本入口支持正常 TND 调用或可达的 TND 输出。
- 反向 wrapper 固定 `out_dtype=1`，dq/dk/dv 分配 BF16（`out_dtype==0` 才是 FP16，本入口不取该值）。返回元组中 `dpse/dq_rope/dk_rope` 因 pse/rope 未传，在函数尾部被重置为默认构造的 `at::Tensor()`——未定义张量，不是空张量，不要对其做形状假设；`dsink` 为 `{0}` 形状 FP32 有定义占位。

## 设备入口分派

- **≥Ascend950 前向**：q/k/v 经 `make_wrapper(·, query_dtype)` 包装后下发 `aclnnQuantFlashAttentionScore(q_w, k_w, v_w, atten_mask, d_scale_q, d_scale_k, d_scale_v, p_scale, scale, pre_tokens, next_tokens, head_num, layout, sparse_mode, softmax_max, softmax_sum, softmax_out, attention_out)`。掩码只保留 atten_mask 一类；drop/padding/pse/rope/prefix/变长列表/inner_precise/out_dtype/pse_type/seed/offset 均不透传。
- **≥950 反向**：q/k/v/dy 四个 wrapper，下发 `aclnnQuantFlashAttentionScoreGrad(..., softmax_max, softmax_sum, attention_in, d_scale_q/k/v/dy, ds_scale, p_scale, scale_value, pre_tokens, next_tokens, head_num, layout, sparse_mode, out_dtype, dq, dk, dv)`，只产出三梯度。
- **<950（A2/A3 等）**：common 无 is_fp8 门控，量化 wrapper 会落入通用 `aclnnFlashAttentionScoreV2`/`aclnnFlashAttentionScoreGradV2` 分支，这些调用的参数表中不携带 d_scale 与 query_dtype/wrapper。这是静态读码结论；这些 aclnn 收到量化 dtype 输入的真实行为（支持、报错或错算）未知，不能据本文件推定 A2/A3 可用或失败形态，也不能推定量化语义在 pre-950 由其他入口承载。

## 版本边界（发布 → 主线）

1. **950 前向 query_dtype**：发布是可选双路径——有 query_dtype 时走 wrapper、无则把原始张量直传 `aclnnQuantFlashAttentionScore`（对应 FP8 e4m3 输入）；主线改为强制必传且仅 wrapper 路径，错误文案写明 "shall only be set to hifloat8"。官方 FP8(e4m3) 前向用例在主线与发布两版本 均不传 query_dtype，与主线检查静态不一致（未运行验证何方实际生效；跨版本脚本应显式传 query_dtype 并按版本核对）。
2. **input_layout 空串检查**：主线在前向 common 与 grad common 两处新增；发布传空串会在更晚阶段失败。
3. dropout helper 的 philox seed/offset 获取被移入 `<950` 条件。对本入口无 dropout 行为影响（keep_prob 固定 1.0，不生成 mask；返回统计口径见「调用与固定语义」），但影响同文件 v2 入口的 950 随机数行为，以 [v2 卡](npu_fusion_attention_v2.md)为准。
4. 用例演进：主线新增 hifp8 前向用例（uint8 存储 + `query_dtype=torch_npu.hifloat8`，BSND `(1,57600,5,128)`），并把反向 golden 重写为 512 块 block-quant 参考 + `en_dtypes` hifloat8 转换。读码可见 hifp8 用例 golden 形状 `(2,1,1,128)` 与 BSND 输出 `(1,57600,5,128)` 不一致，`equal` 判定按形状语义应为 False，断言写法可疑（静态观察，未运行）。

## Meta 静态缺陷（主线与发布两版本 相同）

前向 meta（`npu_quant_fusion_attention_forward`）引用未定义名 `out_dtype`（非参数、非模块全局），被调用即 NameError（静态读码，未执行）；softmax 统计按 `[B, head_num, S1, 8]` 分配，与 C++ 非 TND is_fp8 的 `[B, head_num, S0, 1]` 不一致；`S1` 默认按 `query.size(2)`（BNSD）推导，仅 BSH/SBH 有覆写，BSND/TND 布局推导错误。反向 meta 引用未定义名 `out_dtype` 与 `sink`，且 `torch.empty_like([0], ...)` 以列表为参数（与 v2 卡记录的同类静态类型风险）。不能据 Meta 输出推断真实输出形状、dtype 或训练显存。

## 与相邻入口的关系

- [npu_fusion_attention_v2](npu_fusion_attention_v2.md)（及其 [V1](npu_fusion_attention.md)/[V3](npu_fusion_attention_v3.md)）：同文件共用 common 与校验；v2 卡已声明其 `is_fp8=False`，量化尺度与参数不可混用。
- hifloat8 Tensor 包装与 cast 链见[训练指南](../../guides/torch_npu_hifloat8_tensor_wrapper_and_cast_chain.md)；本入口是 hifloat8 存储进入 attention 计算的直接消费者之一。
- 推理侧量化注意力是 [npu_fused_infer_attention_score](../../../inference/apis/torch_npu/npu_fused_infer_attention_score.md) 家族（FIA），与本训练入口不互替。
- `aclnnQuantFlashAttentionScore(ScoreGrad)` 的设备侧语义（scale 应用位置、p_scale/ds_scale 含义）不在来源覆盖（ops/ascendc 无对应设备文档）；p_scale/ds_scale 目前只能由用例 golden 推断（概率量化 scale、dsoftmax 量化 scale，512 块），无官方文档。

## 失效边界

- 未运行任何用例；官方用例仅覆盖 Ascend950，无 A2/A3/950DT 矩阵，无 dropout/PSE/RoPE 组合（本入口也不支持）。
- pre-950 行为未知（见「设备入口分派」）。
- 主线候选的软件配套未确认；`op_api: [v2.1, newest]` 只是本固定源的注册证据，不据此推断所有 torch_npu 二进制的可用性。
- d_scale 的方向约定（乘或除）在用例中为 `d_scale = 1/scale`（先 block-quant 再求逆），未经运行复核，不要照抄为通用契约。
