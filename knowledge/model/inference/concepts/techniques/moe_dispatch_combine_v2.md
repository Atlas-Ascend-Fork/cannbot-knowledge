---
type: Concept
title: MoE Dispatch/Combine V2（一体化融合算子）
description: torch_npu.npu_moe_distribute_dispatch_v2 / npu_moe_distribute_combine_v2（仓内文档亦称 MC2 路由）把 MoE 专家并行的 All-to-All dispatch / combine 路由通信收敛为两个一体化融合算子（专家 GroupedMatmul 仍位于两者之间独立执行）：dispatch_v2 按路由分发 token 到专家所在 rank 并按专家重排，combine_v2 按逆映射退还并加权融合。相比手写 init_routing_v2 重排 + all_to_all_single + finalize_routing（即 double-routing），把发送/状态同步/重排封装在单算子内，减少 host 下发与 kernel 启动，适合纯 EP Decode（moe_ep_size>1 且 moe_tp_size==1）小 batch 低时延场景。主要使用方（grep 实证、非穷举）：R1 / Kimi-K2 / Qwen3-MoE / Qwen3.5-MoE / DeepSeek-V3.2-Exp / LongCat-Flash(-Lite) / DeepSeek-V4 / Gemma-4 / Hy3-preview；A2 受 experts_per_rank≤24 限制、A3 无此限。配套 HCCL_BUFFSIZE / HCCL_OP_EXPANSION_MODE=AIV 调优。MC2 使用独立 HCCL 通信域 moe_ep_group_mc2（与 EP 的 moe_ep_group 解耦）+ 独立 buffer（calc_moe_hccl_buffer_size is_full_mesh_v2=True）+ fullmesh_v2 模式（dispatch_kwargs comm_alg=fullmesh_v2，见 R1/Kimi/V3.2/glm-5/qwen3_moe/V4）；fullmesh_v2 不支持零专家，故带 copy_expert_num 的 LongCat-Flash 仍切独立域但不置 comm_alg=fullmesh_v2。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md
  role: primary
created_at: '2026-05-31T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MoE Dispatch/Combine V2（一体化融合算子）

## Summary

`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（[expert-parallel](../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**：

- **dispatch_v2**：把每个 token 按路由结果（`expert_ids`/`topk_idx`）分发到所选专家所在 rank（All-to-All 分发），并在算子内部完成按专家重排，输出 `expand_x`（按专家重排的接收 token）、`assist_info_for_combine`（combine 逆映射所需三元组）、`expert_token_num`（每专家收到 token 数）、`ep_recv_counts` / `tp_recv_counts`。
- **combine_v2**：专家计算后按 dispatch 的逆映射把结果退还回 token 原属 rank（All-to-All 收集 + 加权融合），入参 `assist_info_for_combine` 复用 dispatch 输出、`expert_scales` 为 routing 权重；`ep_send_counts` 取 dispatch 的 `ep_recv_counts`。

相比手写"`npu_moe_init_routing_v2` 重排 + `dist.all_to_all_single` + `npu_moe_finalize_routing`"的多算子组合（即 [double-routing](double_routing.md) 路径），一体化算子把发送 / 状态同步 / 重排封装在单算子内部，减少 host 下发与 kernel 启动次数，适合 Decode 单 token 小 batch、host bound 的低时延场景。中间专家计算仍走 `npu_grouped_matmul`（A8 路径传 `pertoken_scale`）。

## Trigger Conditions

纯 EP Decode：`moe_ep_size>1` 且 `moe_tp_size==1`，由各模型的开关使能：

- **Qwen3.5-MoE**：`custom_params.enable_decode_moe_dispatch_combine_v2`（默认 False），且 `forward_metadata.is_prefill==False`、`moe_ep_size>1`、`moe_tp_size==1` 四条同时满足（`_can_use_decode_dispatch_combine_v2`，`modeling_qwen3_5_moe.py:1815-1823`）。
- **LongCat-Flash-Lite**：`custom_params.enable_moe_mc2_dispatch`（缺省时由 `exe_mode=="ge_graph"` 推断），且 `moe_tp_size==1`、非 Prefill 时走 MC2，否则回退 double-routing（`modeling_longcat_flash_lite.py:1630-1633`、`:827`）。
- **DeepSeek-R1 / Kimi-K2-Thinking**：Decode 走 `moe_infer_dispatch_combine`（`modeling_deepseek.py:721`），dispatch/combine 入参经 `set_mc2_kwargs`（`:427`）填充，`group_ep`/`group_tp` 取 `moe_ep_group_mc2` 通信域；Prefill 走 double-routing。
- **Gemma-4-26B-A4B**：MoE EP decode 在 `mc2`（本算子）与 `local_experts` 两路径间按 `experts_per_rank ≤ 24` 自动切换（见下"平台约束"），默认 `mc2`。

Prefill 大序列更适合 double-routing：`dispatch_v2` 单层 token 数受 BS 上限（longcat-flash-lite 报告约 512）约束，无法直接用于 Prefill（`optimization_report_ep.md:127`）。

## Platform Constraints

- **A2 上 `experts_per_rank ≤ 24` 限制**：`npu_moe_distribute_dispatch_v2` 在 A2 受每 rank 专家数 ≤24 约束，A3 无该限制（`gemma4_26b_a4b/agentic/optimization_report.md:137`）。Gemma-4 EP=8 下 16 experts/rank 两平台都满足；longcat-flash-lite EP=8 下 32/rank 在 A2 不满足，A2 部署需 `custom_params.enable_moe_mc2_dispatch: false` 走 double-routing，或 `exe_mode: eager`（`optimization_report_ep.md:126`）。
- **零专家支持**：dispatch_v2/combine_v2 通过入参 `copy_expert_num` 支持零（identity）专家处理，计算公式 `MoE(ori_x)=ori_x`；LongCat 系列借此暴露其 zero expert（`modeling_longcat_flash_lite.py:914/929`、longcat-flash `docs` 路由小节）。
- **SuperKernel 兼容性（hy3-preview，CANN 8.5.0 实测）**：`npu_moe_distribute_combine_v2` 的 `shared_expert_x` 参数与 [superkernel](superkernel.md) 不兼容（融合链涉及 >2 real stream，编译报 "super kernel do not support more than 2 real stream"），该融合已回退待 CANN 更新；API 文档未记录此限制（`hy3_preview/optimization_report.md:273/305`）。

## Tuning Env

- `HCCL_BUFFSIZE`：dispatch/combine 通信缓冲区大小，报错 "HCCL_BUFFSIZE is too SMALL" 时按提示增大，所有 Rank 须一致（多个模型 README 一致说明）。R1 部署经 `calc_moe_hccl_buffer_size` 为 `moe_ep_group_mc2` 计算缓冲（`modeling_deepseek.py:2379`）。
- `HCCL_OP_EXPANSION_MODE=AIV`：用 Device Vector Core 加速集合通信，进一步压缩通信时延（R1 decode 文档、`kimi-k2-thinking/function.sh:101`）。

> ⚠️ 约束（与 Prefill micro-batch 互斥）：[expert-parallel](../parallelism/expert_parallel.md) R1 Decode 条目记 `HCCL_OP_EXPANSION_MODE=AIV` 与 Prefill micro-batch 互斥；另 `qwen3_5/README.md:158` 提示该项可能引入不确定计算导致评测波动，精度评测时建议关闭。

## 独立通信域 + fullmesh_v2

MC2（dispatch_v2/combine_v2）使用**独立的 HCCL 通信域** `moe_ep_group_mc2`，与 EP 的 `moe_ep_group` 集合通信解耦：各模型在 `set_mc2_kwargs` 内把 dispatch/combine 的 `group_ep` / `group_tp` 取自 `moe_ep_group_mc2` 的 HCCL 名（而非 `moe_ep_group`），让 MC2 路由通信与 EP 其它集合通信用各自的 comm group 与 buffer。

- **独立 buffer**：`moe_ep_group_mc2` 的 HCCL buffer 由 `calc_moe_hccl_buffer_size(..., is_full_mesh_v2=True)` 单独计算（fullmesh_v2 分支下 dispatch token 占用按 `ceil(2*hidden_size/FULL_MESH_DATA_ALIGN)*WIN_ADDR_ALIGN` 取，区别于非 fullmesh_v2 的对齐公式），由 R1 在 `moe_ep_size>1 且 moe_tp_size==1` 时注册该独立 group（`modeling_deepseek.py:2378-2390`，`hccl_utils.py:194/244`）。
- **fullmesh_v2 通信模式**：独立域下 dispatch_kwargs 显式传 `comm_alg: "fullmesh_v2"`。grep@2c45117 全仓 `comm_alg="fullmesh_v2"` **仅** 6 处：deepseek-r1（`modeling_deepseek.py:444`）、kimi-k2-thinking（`:387`）、deepseek-v3.2-exp（`:393`）、glm-5（`modeling_glm.py:381`）、qwen3_moe（`modeling_qwen3_moe.py:218`）、deepseek-v4（`:318`）。前 5 个属 893d72e 改造清单；deepseek-v4 系 0day 适配自带，且**仅 `platform_version != "950"` 分支置 fullmesh_v2，950 平台改置 `combine_kwargs["comm_quant_mode"]=4`(MXFP8) 不置**（`:317-321`）。**Qwen3.5-MoE / Gemma-4 / Hy3-preview 等其余 MC2 使用方 grep 无 `comm_alg`，未启用 fullmesh_v2。** fullmesh_v2 的通信拓扑细节详见 torch_npu / HCCL 文档。
- **零专家约束（fullmesh_v2 不支持零专家）**：**fullmesh_v2 不支持零（identity）专家计算**。带零专家（`copy_expert_num = num_zero_experts`）的 [longcat-flash](../models/longcat_flash.md) 因此**仍切到独立域 `moe_ep_group_mc2` 但不启用 fullmesh_v2**——其 `set_mc2_kwargs` 把 `group_ep`/`group_tp` 取自 `moe_ep_group_mc2_name`、保留 `copy_expert_num`，但 dispatch_kwargs 中**无 `comm_alg` 项**（`modeling_longcat_flash.py:447/453/469/1609`，与上列模型形成对照）。

> ⚠️ 代码 vs 提交描述（grep@2c45117）：提交描述把 longcat-flash 表述为"未使能"。**代码字面**为：longcat-flash 仍使用独立通信域 `moe_ep_group_mc2`（`modeling_longcat_flash.py:1609/447`），仅**未设置 `comm_alg: "fullmesh_v2"`**（无该 kwarg，与其余模型显式置 fullmesh_v2 相反）。即"未使能"指**未启用 fullmesh_v2 模式**，而非未切独立域。

## Distinction From Adjacent Pages

- **vs [expert-parallel](../parallelism/expert_parallel.md)**：那是 EP 并行策略 / 部署总页（专家分卡、AllToAll 通信、负载均衡）；dispatch/combine_v2 是其 Decode 路径所用的**具体融合算子实现**。
- **vs [double-routing](double_routing.md)**：那是 **Prefill** 阶段基于 `init_routing_v2` + `dist.all_to_all_single` 的 HCCL AllToAll **多算子集合通信路由**；dispatch/combine_v2 是 **Decode** 阶段的一体化融合算子，二者互为场景对照（Prefill 大序列 vs Decode 小 batch）。
- **vs [shmem-dispatch-combine](shmem_dispatch_combine.md)**：那是 DeepSeek-V4 shmem_guide 给出的、用 CANN SHMEM 对称内存**单边通信手写重写** dispatch&combine 的文档级指南（put/signal/wait）；dispatch/combine_v2 是 torch_npu **标准一体化融合算子**（HCCL/MC2 底层），把发/等/拷贝封装在算子内部、不暴露 win 区。V4 生产路径实调 dispatch/combine_v2 算子（`modeling_deepseek.py:578/616`），非 SHMEM 重写路径。

## Shared Usage（主要使用方，grep@2c45117 实证；非穷举）

| 模型 | 路径 | 触发/开关 | 代码证据 |
|---|---|---|---|
| DeepSeek-R1 | Decode 大 EP | `moe_infer_dispatch_combine` + `set_mc2_kwargs` | `modeling_deepseek.py:721/427/734/773` |
| Kimi-K2-Thinking | Decode（与 R1 同构、独立副本） | 同 R1 `moe_infer_dispatch_combine` | `models/kimi-k2-thinking/models/modeling_deepseek.py:617/643` |
| Qwen3-MoE | Decode（`moe_infer_dispatch_combine`，"support ep for decode stage"） | 纯 EP Decode（`moe_ep_size>1`、`moe_tp_size==1`） | `modeling_qwen3_moe.py:358/380` |
| Qwen3.5-MoE | 纯 EP Decode | `enable_decode_moe_dispatch_combine_v2` | `modeling_qwen3_5_moe.py:1851/1884` |
| DeepSeek-V3.2-Exp | Decode（`moe_infer_dispatch_combine`，tp+ep mix、`is_prefill` 恒 False） | Decode（与 V3.1 一致 Attention DP + MoE EP） | `models/deepseek-v3.2-exp/models/modeling_deepseek.py:636/667` |
| LongCat-Flash | Decode MoE EP + 零专家（独立域，不启用 fullmesh_v2 ⚑） | `copy_expert_num` | `longcat_flash_optimization.md:140`、`modeling_longcat_flash.py:447/453/469/1609` |
| LongCat-Flash-Lite | Decode（MC2）/ Prefill double-routing | `enable_moe_mc2_dispatch` | `modeling_longcat_flash_lite.py:764/1633` |
| DeepSeek-V4 | Decode MoE EP（生产路径） | — | `models/deepseek-v4/.../modeling_deepseek.py:578/616` |
| Gemma-4-26B-A4B | Decode `mc2`/`local_experts` 双路径自动切换 | `experts_per_rank ≤ 24` | `gemma4_26b_a4b/.../optimization_report.md:130-137` |
| Hy3-preview | Decode（含 SuperKernel 兼容性回退） | — | `hy3_preview/optimization_report.md:173/273/305` |

> ⚑ fullmesh_v2 使能（grep@2c45117 精确集，**非全表**）：仅 R1 / Kimi / V3.2-Exp / glm-5 / qwen3_moe（893d72e 改造）+ V4（非 950 分支，0day 自带）在独立域下置 `comm_alg: "fullmesh_v2"`；上表 **Qwen3.5-MoE / Gemma-4 / Hy3-preview / LongCat(-Lite) 用 MC2 但未置 fullmesh_v2**（不在 893d72e 清单、grep 无 `comm_alg`）；LongCat-Flash 另因零专家不支持 fullmesh_v2，仍切独立域但不置该项。
>
> [glm-5](../models/glm_5.md)（`modeling_glm.py:624/655`，独立域 + fullmesh_v2 `:381`）也调用本融合算子；另有 `pangu-7b`（`modeling_openpangu_dense.py:740/775`，其 `comm_alg` 为 `"MTE"` 非 fullmesh_v2）调用本算子但尚无独立 wiki 页，暂不前向链。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-r1/deepseek_r1_decode_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md)（L22 dispatch_v2/combine_v2 多卡路由 + L39 `HCCL_OP_EXPANSION_MODE`）；[`models/deepseek_r1/models/modeling_deepseek.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek_r1/models/modeling_deepseek.py)（`moe_infer_dispatch_combine` L721 / `set_mc2_kwargs` L427 / `dispatch_args`+`combine_args` L729-771 / `npu_grouped_matmul` `pertoken_scale` L549）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/qwen3_5/models/modeling_qwen3_5_moe.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/models/modeling_qwen3_5_moe.py)（`enable_decode_moe_dispatch_combine_v2` L1695 / `_can_use_decode_dispatch_combine_v2` L1815-1823 / `_run_experts_dispatch_combine_v2` L1824-1884）；提交 `feat: support qwen3.5`（2825444，MR!402）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — Gemma-4：[`models/gemma4_26b_a4b/agentic/optimization_report.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md)（§6.3 mc2 vs local_experts + `experts_per_rank ≤ 24`）+ `README.md:122/135`；提交 `feat: add gemma-4 model optimized by agent skills`（16e3806）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — Hy3-preview：[`models/hy3_preview/optimization_report.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/optimization_report.md)（L273/305 combine_v2 `shared_expert_x` × SuperKernel 兼容性回退）；提交 `[feat] Adapt and optimize hy3-preview`（71ce39f）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — LongCat-Flash-Lite：[`models/longcat_flash_lite/agentic/optimization_report_ep.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md)（L121-127 Decode MC2 / Prefill double-routing + A2 约束）；`models/longcat_flash_lite/models/modeling_longcat_flash_lite.py:764/914/1630`。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 独立通信域 + fullmesh_v2（commit 893d72e，MR!421 `mc2 use independent communication group`）：[`models/deepseek_r1/models/modeling_deepseek.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek_r1/models/modeling_deepseek.py)（`set_mc2_kwargs` 取 `moe_ep_group_mc2` L429 / `comm_alg: "fullmesh_v2"` L444 / 注册 `moe_ep_group_mc2` + `calc_moe_hccl_buffer_size(is_full_mesh_v2=True)` L2378-2390）；[`models/longcat-flash/models/modeling_longcat_flash.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat-flash/models/modeling_longcat_flash.py)（独立域 L1609 + `copy_expert_num` L453/469、无 `comm_alg`）；fullmesh_v2 旁证 [`modeling_glm.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/models/modeling_glm.py)`:381` / [`modeling_qwen3_moe.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_moe/models/modeling_qwen3_moe.py)`:218` / [`hccl_utils.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/utils/hccl_utils.py)（`calc_moe_hccl_buffer_size` `is_full_mesh_v2` 分支 L194/244，buffer 公式后经 MR!485 微调）。涉及模型清单以 commit 893d72e 描述为准（deepseek-v3.2 / deepseek_r1 / glm-5 / kimi-k2-thinking / longcat-flash / qwen3_moe）。
- 外部 torch_npu API 文档：[`npu_moe_distribute_dispatch_v2`](https://www.hiascend.com/document/detail/zh/Pytorch/720/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_distribute_dispatch_v2.md) / [`npu_moe_distribute_combine_v2`](https://www.hiascend.com/document/detail/zh/Pytorch/720/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_distribute_combine_v2.md)。

## Links

- [expert-parallel](../parallelism/expert_parallel.md)
- [double-routing](double_routing.md)
- [shmem-dispatch-combine](shmem_dispatch_combine.md)
- [moe-multi-stream](moe_multi_stream.md)（shared expert 计算与 dispatch/combine AllToAll 重叠）
- [superkernel](superkernel.md)（combine_v2 `shared_expert_x` 在 CANN 8.5.0 与 >2 stream SuperKernel 不兼容）
- [deepseek-r1](../models/deepseek_r1.md)
- [qwen3-moe](../models/qwen3_moe.md)
- [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [kimi-k2-thinking](../models/kimi_k2_thinking.md)
- [longcat-flash](../models/longcat_flash.md)
- [longcat-flash-lite](../models/longcat_flash_lite.md)
- [deepseek-v4](../models/deepseek_v4.md)
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（Decode mc2 / local_experts 双路径，按 `experts_per_rank ≤ 24` 自动切换）
- [hy3-preview](../models/hy3_preview.md)（Decode MC2 dispatch/combine；`combine_v2` `shared_expert_x` × SuperKernel 在 CANN 8.5.0 不兼容已回退）
- [moe-comm-overlap](../../../training/concepts/techniques/moe_comm_overlap.md)（跨域对照：训练侧 MindSpeed 不走一体化融合算子，而靠异步通信 + 跨 microbatch 前反向排布把 dispatch/combine All2All 与计算重叠，与本页推理侧融合算子互为对照）

<!-- cannbot:related:start -->
## 相关

- [950(Ascend950) MXFP8 fused-MoE：进分组 matmul 前激活量化 scale 必须打包成 [M, N//2, 2] 并中心化收口](../../optimizations/experience/rules/950_mxfp8_moe_activation_scale_packed_layout.md)（`related`）：《950 MXFP8 MoE scale 布局》要求“这条 MoE 路径与 ［moe-dispatch-combine-v2］(../../../concepts/techniques/moe_dispatch_combine_v2.md) 的 dispatch/combine + 分组 gmm 消费顺序衔接，scale 归一化必须发生在 scale 抵达 gmm 之前。”；《MoE Dispatch/Combine V2》说明“中间专家计算仍走 `npu_grouped_matmul`（A8 路径传 `pertoken_scale`）。”，两端共同锁定 dispatch 后、GMM 前的 scale 交接位置。
- [GLM-5](../models/glm_5.md)（`related`）：“Decode 调 `npu_moe_distribute_dispatch_v2`（`:624`）/ `npu_moe_distribute_combine_v2`（`:655`），`a8` 量化时 `quant_mode=2`。”与“`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（［expert-parallel］(../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**：”提供双方正文证据。GLM-5 的 decode 路线实际调用 dispatch_v2/combine_v2，技术页解释这对算子如何封装 EP 的发送、重排与回收，构成模型调用到通信机制的直接边。
- [Gemma-4-26B-A4B](../models/gemma4_26b_a4b.md)（`related`）：“**`mc2`**：`npu_moe_distribute_dispatch_v2` + `npu_moe_distribute_combine_v2`（［moe-dispatch-combine-v2］(../techniques/moe_dispatch_combine_v2.md)），与仓内其他 MoE 模型一致。”；“**Gemma-4-26B-A4B**：MoE EP decode 在 `mc2`（本算子）与 `local_experts` 两路径间按 `experts_per_rank ≤ 24` 自动切换（见下"平台约束"），默认 `mc2`。”。目标卡给出焦点模型 mc2 分支所调用的 dispatch/combine 数据流与平台约束。
- [MoE Double-Routing](double_routing.md)（`related`）：`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（［expert-parallel］(../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**：；DeepSeek-R1 / Kimi-K2 等大 EP MoE 模型在 Prefill 阶段使用的专家路由方案。每张卡完成 **2 次 init-routing + 2 次 finalize-routing**：第一次做本卡内按专家排序 + 通过 AllToAll+ReduceSum 推导 `input_splits` / `output_splits`；token AllToAll 之后再做一次 re-routing 让本卡 token 按本地专家再次排序。相较 AllGather 全量方案，Double-Routing 在负载较均衡时**峰值显存更低**（无数据冗余）且**通信量更小**。。一体化 V2 卡明确把 Double-Routing 作为多算子替代路径，后者补齐 Prefill 大序列的两次重排与 AllToAll 任务图。
- [MoE dispatch/combine 算子报错或大 batch 失败：HCCL 通信 buffer 不足，须按模型显式放大 HCCL_BUFFSIZE](../../runbooks/runtime/moe_dispatch_combine_hccl_buffsize.md)（`related`）：`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（［expert-parallel］(../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**：；MoE EP dispatch/combine 走 HCCL all-to-all，通信 buffer（RDMA 窗口）大小由 `HCCL_BUFFSIZE` 控制，默认 **200MB**。当一步 dispatch 的流量超过该 buffer（专家数多、batch 大时更易），算子报错。。概念卡定义两个融合算子的 EP All-to-All，Runbook给出其 HCCL buffer 不足时的启动期信号、容量公式和调参动作。
- [MoE dispatch/combine 通信侧量化：dispatch 量化模式随激活 dtype、combine 通信可开 MXFP8（昇腾 950）](../../optimizations/experience/rules/moe_dispatch_combine_comm_quant.md)（`related`）：`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（［expert-parallel］(../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**：；MoE token 派发（dispatch/combine）的量化模式由**激活 dtype** 决定、**不随权重位宽变**：`w4a8int4` 与 `w8a8int8` 同用 `dispatch_quant_mode = 2`（int8 派发）。int4 只作用于专家 grouped_matmul 的权重，激活侧仍走 a8（int8）per-token 动态量化（进 GMM 前 `npu_dynamic_quant`）。映射规律：`*a8int8 → 2`、`*a8mxfloat* → 4`，即 W4A8 与对应 W8A8 共用同一 dispatch 量化路径。。概念卡定义 dispatch/combine V2 调用链，规则卡补齐该链的 dispatch_quant_mode 与 950 combine 通信量化选项。
- [MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置](../../runbooks/performance/moe_prefill_oom_peak_memory.md)（`related`）：**dispatch 展开中间量随 token 数线性放大**。MoE 专家 dispatch 把每 token 复制到其 top_k 个专家上，产生 `expanded_x` / `gathered_tokens` 中间张量，规模约 `num_tokens × top_k × hidden`；token 越多峰值越高。；- **dispatch_v2**：把每个 token 按路由结果（`expert_ids`/`topk_idx`）分发到所选专家所在 rank（All-to-All 分发），并在算子内部完成按专家重排，输出 `expand_x`（按专家重排的接收 token）、`assist_info_for_combine`（combine 逆映射所需三元组）、`expert_token_num`（每专家收到 token 数）、`ep_recv_counts` / `tp_recv_counts`。；OOM 卡中的展开中间量对应融合 dispatch 的输出，目标补齐其生产参数与 combine 交接。
- [MoeDistributeCombineAddRmsNorm 950 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/transformer/mc2/moe_distribute_combine_add_rms_norm_950.md)（`related`）：950 公开路线把 `expandX` 按 `assistInfoForCombine` 写入 EP 目标 window；`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（［expert-parallel］(../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**：。算子卡给出 950 CombineAddRmsNorm 的 window 写入与专家聚合实现，概念页把它放回 MC2 dispatch/combine 的端到端 All-to-All 路由链。
- [MoeDistributeCombineSetup 950 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/transformer/mc2/moe_distribute_combine_setup_950.md)（`related`）：根据 `assistInfoForCombine` 的专家累计 token 数，把 `expandX` 分段写入各 EP rank 的 HCCL window，并写通知状态；Setup 提交 URMA 后立即返回，完成确认与后处理交给 CombineTeardown；`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（［expert-parallel］(../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**。950 Setup 算子卡展开 MC2 combine 链的窗口写入、通知和 Teardown 交接，概念页给出其在 dispatch/combine V2 All-to-All 路由中的上层位置。
- [NPU fused_topk 默认先归一化再按 routed_scaling_factor 缩放：保留 norm_topk_prob=True 会二次归一化破坏路由缩放语义](../../runbooks/precision/moe_router_norm_topk_prob_fused_topk_npu.md)（`related`）：精度卡给出“**这些环节里，同一份归一化或同一份路由权重只能被应用一次**”；Dispatch/Combine 卡则明确“**combine_v2**：专家计算后按 dispatch 的逆映射把结果退还回 token 原属 rank（All-to-All 收集 + 加权融合），入参 `assist_info_for_combine` 复用 dispatch 输出、`expert_scales` 为 routing 权重；`ep_send_counts` 取 dispatch 的 `ep_recv_counts`。”，由此可定位 routing 权重在 combine 端的实际消费点并避免重复加权。
- [Qwen3-MoE](../models/qwen3_moe.md)（`related`）：从“后者使用一体化融合算子 `npu_moe_distribute_dispatch_v2`/`combine_v2`（`:365/:387`），两条 EP 路径的中间专家计算均走 `npu_grouped_matmul`；见 ［moe-dispatch-combine-v2］(../techniques/moe_dispatch_combine_v2.md)。”进入 Qwen3-MoE 的 decode 路线后，按“**dispatch_v2**：把每个 token 按路由结果（`expert_ids`/`topk_idx`）分发到所选专家所在 rank（All-to-All 分发），并在算子内部完成按专家重排”检查 expand_x、assist_info_for_combine 和 recv counts，即可闭合模型分支到融合算子参数的调用链。
- [Qwen3.5-MoE](../models/qwen3_5_moe.md)（`related`）：“- **MoE dispatch/combine 融合**：纯 EP Decode（`enable_decode_moe_dispatch_combine_v2` 开 + Decode + `moe_ep_size>1` + `moe_tp_size==1`）下，用 `torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2` 替代手写重排 + `all_to_all` + finalize routing，适合小 batch 低时延 Decode。见 ［moe-dispatch-combine-v2］(../techniques/moe_dispatch_combine_v2.md)。”；“- **Qwen3.5-MoE**：`custom_params.enable_decode_moe_dispatch_combine_v2`（默认 False），且 `forward_metadata.is_prefill==False`、`moe_ep_size>1`、`moe_tp_size==1` 四条同时满足（`_can_use_decode_dispatch_combine_v2`，`modeling_qwen3_5_moe.py:1815-1823`）。”。模型优化条目与技术卡给出相同的四项触发条件，后者还能定位到具体门控函数。
- [基于 SHMEM 重写的 MoE Dispatch&Combine](shmem_dispatch_combine.md)（`related`）：SHMEM 手写重写（显式发/等状态 + win 拷贝机制）与 `npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（torch_npu **一体化融合算子**，［moe-dispatch-combine-v2］(moe_dispatch_combine_v2.md)，Qwen3-MoE/Qwen3.5/Gemma-4 及 V4 生产路径普遍调用）是不同机制——融合算子把发/等/拷贝封装在算子内部，不暴露 win 区。；- **vs ［shmem-dispatch-combine］(shmem_dispatch_combine.md)**：那是 DeepSeek-V4 shmem_guide 给出的、用 CANN SHMEM 对称内存**单边通信手写重写** dispatch&combine 的文档级指南（put/signal/wait）；dispatch/combine_v2 是 torch_npu **标准一体化融合算子**（HCCL/MC2 底层），把发/等/拷贝封装在算子内部、不暴露 win 区。V4 生产路径实调 dispatch/combine_v2 算子（`modeling_deepseek.py:578/616`），非 SHMEM 重写路径。；双方明确给出生产融合算子与 SHMEM 文档级重写的替代机制和验证边界。
- [昇腾融合 MoE 路由的整数契约：npu_moe_init_routing(_v2) 的 active_expert_range 只吃 int、topk_ids 须 int32](../../runbooks/runtime/npu_moe_init_routing_integer_contract.md)（`related`）：`npu_moe_init_routing(_v2)` 对若干标量入参有整数 dtype 契约：`active_expert_range` 只吃 Python int、`topk_ids` 须 int32。；相比手写"`npu_moe_init_routing_v2` 重排 + `dist.all_to_all_single` + `npu_moe_finalize_routing`"的多算子组合（即 ［double-routing］(double_routing.md) 路径），一体化算子把发送 / 状态同步 / 重排封装在单算子内部，减少 host 下发与 kernel 启动次数；整数契约卡用于修复多算子 init-routing 入口，dispatch/combine_v2 卡给出 Decode 场景下可绕开该组合的一体化替代路线和适用条件。
<!-- cannbot:related:end -->
