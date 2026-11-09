---
type: Guide
title: vLLM Ascend FLA 分块线性注意力与门控数据契约
description: 定位 FLA chunk KKT、三角求逆、WY 重建、递归状态更新与输出链；记录有效 varlen、K/V tile、FP32 状态、GQA 重排和归一化边界，供新 GDN 模型适配与误差诊断。
aliases:
- FLA chunk_delta_h chunk_o solve_tril wy_fast
- fused_qkvzba_split_reshape fused_gdn_gating
- GDN packed state transition
tags:
- task.implementation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/cumsum.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/chunk_scaled_dot_kkt.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/fused_qkvzba_split_reshape.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/l2norm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/layernorm_guard.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/wy_fast.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/chunk_delta_h.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/chunk_delta_hupdate.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/chunk_o.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/solve_tril.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/fused_qkvzba_split_reshape.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/fused_gdn_gating.md
  role: constraint
created_at: '2026-11-03T06:08:49Z'
updated_at: '2026-11-03T06:08:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend FLA 分块线性注意力与门控数据契约

## 证据范围

固定 vLLM Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`。本卡聚合 FLA 执行程序与门控/重排文档，不代表已安装的 Triton、DeviceOperator 二进制或全部硬件均通过验证。Python 读取为完整 AST 程序投影，文档为原文；未导入上游代码、编译 JIT 或运行 NPU。

## 分块链与数值语义

1. `cumsum.py` 对三维 scalar gate 按 power-of-two chunk 做局部前缀和，可 reverse、scale。head-first 与 token-first 布局、packed `cu_seqlens/chunk_indices` 必须一致；varlen 要求 B=1。BLOCK_T 根据 `2^18/(H*chunk_size)` 派生，一个 program 可覆盖多个相互独立 chunk。虽然 wrapper 的 `output_dtype` 默认 float，kernel store 前使用输入 `s.dtype` 转换，不能据参数名宣称全程 FP32 输出。head-first load 只检查 H 方向，T 尾部/padding 要由实际输入布局和测试保证。
2. `chunk_scaled_dot_kkt.py` 构造 `beta_i * exp(g_i-g_j) * K_i·K_j` 的**严格下三角**，对角为零；K 的 Hg 通过 `i_h // (H//Hg)` 复用到 H。wrapper 无条件 permute `g_cumsum`，因此 Python 默认 None 不等于这一路支持缺省 gate。实际入口调用 `DeviceOperator`，不能以同文件 kernel 代替已安装实现的派发证据。
3. `solve_tril.py` 仅支持 BT=16/32/64：先求 16×16 下三角块逆并加单位阵，再用 32/64 merge 组合，关键乘法指定 IEEE precision、写回 RTNE。第一阶段 wrapper 走 `DeviceOperator.solve_tril_16x16`。验证时保留严格下三角与单位阵约定，不能换成对角也带 KKT 值的参考。
4. `wy_fast.py` 由 A 重建 `U=A@(V*beta)`、`W=A@(K*beta*exp(g))`。kernel 只遍历 H，未用 grid 的 batch program id 定位另一 batch；部署 packed B=1 是重要边界，不能将 wrapper 形状直接推广为任意 B>1。K/V 分块与不同 dot 的 precision 也应分别记录。
5. `chunk_delta_h.py` 保存每个 chunk **进入前**的 FP32 H，计算 `V_new=U-WH`，再做门控衰减与 `K^T@V_new` 更新，返回 `(h, v_new, final_state)`。实际 state tile 为 K 的 128 与 V 的两段 64；wrapper 的 `K<=256` 断言不证明 K>128 或 V>128 完整覆盖。代码对 g 有无条件 load，不能依 optional 注解传 None。`h_update` 的分配也不等于返回了 transition。
6. `chunk_delta_hupdate.py` 构建局部 transition 并组合 prefix，使用 64×64 子块处理 K=128。wrapper 在 varlen 分支外切 `update_chunk_offsets`，kernel 也先读 `cu_seqlens/chunk_offsets`；有效调用需提供这些 packed 元数据。FP32 `[NT+N]` transition 与 decode 初始化清零范围应按 caller 的 `num_decodes` 对齐，不能凭 `K<=256` 扩大覆盖。
7. `chunk_o.py` 合成 `scale*(QH*exp(g) + causal(QK*exp(g_i-g_j))@V)`；这里是**包含对角**的下三角，与 KKT 不同。scale 默认 `K^-0.5`，BK/BV=128，最终 dtype 跟 V；wrapper 的 g transpose 同样要求实参。

## 模型入口、归一化与布局

`fused_qkvzba_split_reshape.py` 把每个 QK head 的 interleaved `[Q,K,V-group,Z-group]` 与 `[B-group,A-group]` 重排成连续 Q|K|V、Z、b/a。输入地址按给定 heads/dims 的平坦行宽计算，不能传任意 stride view；V heads/QK heads 的正整数整除由 caller 保证。文档的 Qwen3 GDN 形状是既有实例，纯 load/store 比较应按相同 dtype 位值检查。85KiB 的 rows-per-iter 估计经过 next-power-of-two 与其他上限修正，不能当严格资源证明；空行也需独立验证。

`fused_gdn_gating.md` 描述 `g=-exp(A_log)*softplus(a+dt_bias, beta, threshold)`、`beta_out=sigmoid(b)`，g 为 FP32，beta 保留 b dtype。平坦 contiguous 输入、64×8 tile、do-not-specialize 属性和 DeviceOperator 的具体平台分支分别核对。文档列出的平台与参考测试是来源证据，不扩展为本卡新执行结果。

`l2norm.py` 计算 `x*rsqrt(sum(x²)+eps)`，不是 RMS 的 mean；flatten 后默认行连续，FP32 归约、可指定输出 dtype，64KiB feature 上限。`layernorm_guard.py` 则为分组 LayerNorm/RMSNorm，可带 bias 与 Z 的 swish gate；要求末轴 stride=1 和组大小预算。其 activation 参数没有选择其他 activation 的分支，`autograd.Function` 也只实现 forward。不要与另一路 64-row `layernorm_gated.py` 合并成同一个 kernel 契约。

## Agent 的适配和诊断步骤

先锁定实际模型入口及 DeviceOperator 注册，再固定 B、Hg/H、K/V、BT、`cu_seqlens`、chunk offsets 与 state 布局。逐段对比 KKT、A、W/U、chunk 前 H、V_new、最终 H、O，区分严格/含对角、FP32 累积与低精度存储。重点测 packed 多请求、短尾、chunk 边界、已有/新 state、head 复用，以及 K/V 超过实际 tile 的拒绝或替代路径。纯重排使用精确比较；数学归约与门控按 dtype 设置误差并检查 NaN/Inf。图模式还需保持元数据 buffer 地址、生命周期与编译期属性。任何性能结论都需用目标环境的算子及端到端测量补证。
