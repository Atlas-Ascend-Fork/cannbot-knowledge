---
type: Optimization
title: MoE 专家 GMM 权重加载后处理与低比特量化调用约定：NZ 布局 / W4A8 bias 辅助矩阵 / W4A16 N-dim 重打包 / clip
description: MoE 专家 GMM 权重加载后处理与低比特量化调用约定：NZ 布局 / W4A8 bias 辅助矩阵 / W4A16 N-dim 重打包 / clip。在昇腾上让 MoE 专家走 npu_grouped_matmul（GMM），要么换低比特权重（W8A8→W4A8、或纯权重 int4 W4A16），要么想让 GMM 读权重更快时。这些改动的坑几乎都落在 process_weights_after_loading（加载后一次性处理，不进热路径）：布局/打包/辅助矩阵没按 GMM kernel 的调用约定准备好，就会精度错、布局不匹配、甚至新分支静默不生效。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/12
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/93
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/205
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/13
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# MoE 专家 GMM 权重加载后处理与低比特量化调用约定：NZ 布局 / W4A8 bias 辅助矩阵 / W4A16 N-dim 重打包 / clip

## 适用场景

在昇腾上让 MoE 专家走 `npu_grouped_matmul`（GMM），要么换低比特权重（W8A8→W4A8、或纯权重 int4 W4A16），要么想让 GMM 读权重更快时。这些改动的坑几乎都落在 **`process_weights_after_loading`（加载后一次性处理，不进热路径）**：布局/打包/辅助矩阵没按 GMM kernel 的调用约定准备好，就会精度错、布局不匹配、甚至新分支静默不生效。

## 规则一：加载后把专家权重转 NZ 供 GMM 高效读取

GMM 从 NZ（`format=29`）内部格式读权重更高效，故专家权重（`w13`/`w2`）驻留前一次性 `torch_npu.npu_format_cast(..., 29)`，转换放在加载后、不进热路径。量化路径的**调用约定差异**：W8A8 GMM 分支的专家权重先 `transpose(1,2).contiguous()` 再 cast；未量化分支直接 cast。转换后释放原缓存指针（`caching_allocator_delete`）避免驻留双份。见 [weight-nz](../../../concepts/techniques/weight_nz.md)。

## 规则二：W4A8 相对 W8A8 的 grouped-matmul 调用约定（核心 gotcha）

从 [W8A8](../../../concepts/quantization/w8a8c8.md) 迁到 [W4A8](../../../concepts/quantization/w4a8c8.md)（权重 4-bit 对称静态、激活 8-bit per-token 动态）时，直接照搬 W8A8 的 MoE GMM 方法会漏掉 W4A8 特有约定：

1. **scheme 判据**：权重 4-bit 对称静态、激活 8-bit per-token 动态 → 分发到 W4A8 专用 MoE GMM 方法（而非 W8A8/W4A16 分支）。
2. **grouped-matmul 调用差异**：W4A8 路径的 `npu_grouped_matmul` 需传入**每专家一个 float 的 bias 辅助矩阵** + weight_scale + per_token_scale，`output_dtype` 直接给 bf16；W8A8 路径首段 mm 输出 int32、mm 内不带 bias/scale、之后再 dequant。建模侧据量化模式给融合 MoE GMM 传 `bias=True`（源码注释：W4A8 时 gmm kernel 需一个辅助矩阵、以 bias 传入）。
3. **权重打包**：4-bit 权重 2-per-int8 打包（`pack_factor = 8//4 = 2`）以 int8 存储；per-channel weight scale 每专家分别存、对本 rank 所需专家拼接。
4. **精度**：需每专家 `alpha` clip 因子（`dynamic_quant` 前先 clip 提升 W4A8 精度）。
5. **EP 复用非新增**：`moe_ep_size>1` 时每设备仅存其映射专家的 smooth_scale，首段 GMM 的动态量化需完整 smooth_scale、故 all-gather 补齐——这是 W4A8 **复用** W8A8 既有逻辑（分支从仅 W8A8 扩为 W8A8||W4A8），非 W4A8 新引入。

## 规则三：W4A16（纯权重 int4）走 antiquant + 必须 N-dim 重打包

跑「原生 compressed-tensors int4 QAT 权重（weight-only）+ BF16 激活」的 W4A16 混合精度（MoE 专家 int4、注意力/dense 保 BF16）时：

1. **识别 W4A16**：`input_quant is None and weight_quant.symmetric and strategy∈{CHANNEL,GROUP} and not weight_quant.dynamic and num_bits==4` → 选 W4A16 MoE GMM 方法、否则回落 W8A8 动态 token 量化。
2. **antiquant 前向**：两段 `npu_grouped_matmul` 均传 `antiquant_scale/antiquant_offset`、`output_dtype` 取激活 dtype（BF16），中间接 `npu_swiglu`——int4 权重在 kernel 内 antiquant 回 BF16、激活全程 BF16、无需量化激活。
3. **重打包坑**：GMM int4 antiquant kernel **只吃 N-dim packed** 权重，而 compressed-tensors 通常给 **K-dim packed**（`pack_factor=32//4=8`）。加载后须 `unpack_from_int32(...,4)` → `transpose(1,2)` → `pack_to_int32`/`npu_convert_weight_to_int4pack` 转成 N-dim，并对应 transpose per-group 的 scale/offset。**漏这一步权重布局与 kernel 不匹配**（源码注释直证：`GMM kernel only support Ndim packed, repack is necessary when Kdim packed`）。
4. **混合精度装配**：MoE 专家以量化 config 构造走 W4A16；q_a_proj/kv_b_proj/o_proj/dense/lm_head 以 `quant_config=None` 构造 → BF16。

## 收益（W4A8 MoE decode，仓自报 benchmark）

Atlas A3、DeepSeek-V3.2-Exp、MoE 改 W4A8（注意力仍 W8A8C8）、序列长 65536、MTP 同 W8A8C8 口径。动机：权重大、搬运 bound 的场景 W4A8 减内存占用、降权重搬运耗时。

| MoE Quant | Global Batch | Chips | TPOT(ms) | Throughput(tokens/p/s) |
|---|---|---|---|---|
| W8A8 | 64 | 32 | 20.81 | 96 |
| W4A8 | 64 | 32 | 20.18 | 99 |
| W8A8 | 32 | 16 | 24.39 | 82 |
| W4A8 | 32 | 16 | 22.51 | 89 |

**在报告的这两组配置中**：32-chip 约 +3%，16-chip（每卡权重更大）约 +8.5%——16-chip 相对增益更大，与「每卡权重越大、W4A8 搬运收益越大」方向一致，但**仅两点、不外推单调规律**。精度另评（W4A8 需 learned-clamp / clip，见规则二第 4 点）。

## 边界

各调用约定按证据限定到 compressed-tensors MoE GMM 链路（W4A8 证据取 DeepSeek-V3.2-Exp、W4A16 取 Kimi-K2-Thinking QAT 权重、NZ 取 Qwen3-MoE SGLang），可迁移到同结构（MoE + GMM 量化）的其它模型，不外推为整栈通用律；QAT int4 权重由上游模型自带、本仓不产权重。MoE dispatch/combine 的**通信侧**量化是另一回事，见 [moe-dispatch-combine-comm-quant](moe_dispatch_combine_comm_quant.md)。

## Evidence

- W4A8 scheme 判据、grouped-matmul bias/output_dtype 对照、2-per-int8 打包、建模 `bias=True`、EP 分支扩展：diff 事实（含源码注释）@47228911d04d。溯源下探 [cann-recipes-infer-pr-12-feat-support-moe-gmm-w4a8](https://gitcode.com/cann/cann-recipes-infer/merge_requests/12)。
- W4A16 识别谓词、antiquant grouped_matmul、unpack→transpose→convert_weight_to_int4pack 重打包、混合精度落点：diff 事实（注释直证重打包动机）@da13d66。溯源下探 [cann-recipes-infer-pr-93-feat-support-kimi-k2-thinking](https://gitcode.com/cann/cann-recipes-infer/merge_requests/93)。
- 加载后 `npu_format_cast(...,29)` 转 NZ、W8A8 分支 transpose 前置：diff 事实 @50e41b5b8220。溯源下探 [cann-recipes-infer-pr-205-feat-support-qwen3-moe-sglang](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)。
- W4A8 vs W8A8 decode benchmark 表（含 seq 65536、chips、TPOT、吞吐）：doc 披露（仓自报、非独立复跑结果）@8c6c58b36bac。溯源下探 [cann-recipes-infer-pr-13-feat-add-deepseek-v3-2-exp-w4a8c8-quantization-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/13)。

<!-- cannbot:related:start -->
## 相关

- [Kimi-K2-Thinking](../../../concepts/models/kimi_k2_thinking.md)（`related`）：“**MoE** GroupedMatmul 采用 W4A16（权重 Int4 静态 Per-Channel，激活 BF16）”确定 Kimi 的模型级量化入口；“GMM int4 antiquant kernel **只吃 N-dim packed** 权重”给出该入口加载后的强制重打包合同，能够直接指导权重转换和精度排障。
- [MoE dispatch/combine 通信侧量化：dispatch 量化模式随激活 dtype、combine 通信可开 MXFP8（昇腾 950）](moe_dispatch_combine_comm_quant.md)（`related`）：“MoE token 派发（dispatch/combine）的量化模式由**激活 dtype** 决定、**不随权重位宽变**：`w4a8int4` 与 `w8a8int8` 同用 `dispatch_quant_mode = 2`（int8 派发）。int4 只作用于专家 grouped_matmul 的权重，激活侧仍走 a8（int8）per-token 动态量化（进 GMM 前 `npu_dynamic_quant`）。”与“从 ［W8A8］(../../../concepts/quantization/w8a8c8.md) 迁到 ［W4A8］(../../../concepts/quantization/w4a8c8.md)（权重 4-bit 对称静态、激活 8-bit per-token 动态）时，直接照搬 W8A8 的 MoE GMM 方法会漏掉 W4A8 特有约定：”分别限定通信量化模式与专家权重约定。通信规则把 dispatch 模式绑定到激活 dtype，并明确 int4 仅属于专家 GMM 权重；GMM 规则进一步给出 W4A8 权重、scale、bias 与打包约定，二者共同划清同一低比特 MoE 任务链的通信侧和专家计算侧责任。
- [大 MoE 量化按模块角色分配精度：路由专家最激进、共享专家 / 注意力保守](moe_role_based_precision_allocation.md)（`related`）：“从 ［W8A8］(../../../concepts/quantization/w8a8c8.md) 迁到 ［W4A8］(../../../concepts/quantization/w4a8c8.md)（权重 4-bit 对称静态、激活 8-bit per-token 动态）时，直接照搬 W8A8 的 MoE GMM 方法会漏掉 W4A8 特有约定：”落实低比特 GMM 的迁移合同；“**MoE 路由专家（routing experts）的 Linear / GroupedMatmul → 最激进**：降到 W4A8（4bit 权重、8bit 激活）或 W4A16。它们冗余度高、且每 token 只激活一小部分，是量化的主战场。”给出何时选择该合同的模块角色策略，两卡连成选型到实现准备链。
- [昇腾量化权重的加载期布局/命名处理：W4A8 MoEGMM 三件套、剔除零 offset、scale 改名门控、NZ 按 dtype 门控](quant_weight_load_layout_and_naming.md)（`related`）：“## 一、W4A8 MoEGMM 的 int4 专家权重三件套布局”明确给出左端事实；“## 规则二：W4A8 相对 W8A8 的 grouped-matmul 调用约定（核心 gotcha）”明确给出右端事实。加载规则定义 int4 打包、UINT64 scale 与 assistance_bias 三件套；GMM 页把它们接到 npu_grouped_matmul 的 bias/scale/pertoken_scale 调用和加载后 NZ/W4A16 重打包。
<!-- cannbot:related:end -->
