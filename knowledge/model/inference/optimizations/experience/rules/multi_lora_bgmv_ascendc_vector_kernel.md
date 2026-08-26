---
type: Optimization
title: 昇腾多-LoRA BGMV 走自研 AscendC 向量核（非-310p 启用，rank/dtype 硬约束）
description: 多 LoRA decode 中，BGMV 按 token 的 adapter index 选择权重，依次执行 shrink x·A 和 expand ·B；通用 gather、matmul、reduce 组合易受多次下发与访存限制。vLLM-Ascend 以两个 AscendC 向量核融合索引取权和归约，并让 SGMV 展开段级 index 后复用同一路径。自研核仅在非 310P 平台启用，310P 回退 torch_ops；dtype 只支持 fp16/bf16，bf16 还要求 AICore 版本不低于 220，LoRA rank 仅支持 8、16、32、64。shrink 要求输入 hidden 大于 rank，expand 受 slice size/offset 边界约束，indices 必须是一维 int64。来源自报 Qwen2.5-7B 吞吐约提升 70%，尚无独立复测。
tags:
- task.optimization
- topic.precision
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/1884
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- 310p
---

# 昇腾多-LoRA BGMV 走自研 AscendC 向量核（非-310p 启用，rank/dtype 硬约束）

## 适用场景

昇腾 NPU 上做**多-LoRA 在线推理**、且发现 LoRA 应用（BGMV / punica 路径）是 decode 热点、拖慢逐 token 生成时，优先把 BGMV 的 shrink/expand 从「通用 PyTorch 组合算子」换成**自研 AscendC 向量核**。

判断这条规则是否命中你的处境：

- 你在做**多适配器同批服务**（一个 batch 里不同 token 属于不同 LoRA），走的是 **BGMV = Batched Gather Matrix-Vector** 语义：multi-LoRA 每 token 按一份 `indices` 选各自的 LoRA 权重，先 **shrink**（`x·A` → 中间 rank 维）再 **expand**（`·B` → 输出维）。
- 基线实现是**上游通用路径**：把 BGMV 由一串原生小算子（gather + 多个 matmul / reduce）拼出。这条路径在昇腾上是该场景的性能瓶颈——多个小算子的下发与访存开销在逐 token decode 上被放大。
- 你的芯片**不是 Ascend 310P**（下述参考实现只在非-310p 启用；310P 仍走通用 torch 回退）。
- 你的 LoRA **rank 落在 {8,16,32,64}**，权重 **dtype 是 fp16 或 bf16**（这两条是参考实现的硬门控，不满足就选不了这条路径，见「参考实现及其约束」）。

若命中，规则是：**用一个「gather + 单核内 reduce」的定制向量核承载整条 shrink/expand，替代多算子拼装**；这在昇腾多-LoRA decode 上是已合入的正向抓手。

## 条件 → 优先尝试什么

| 条件 | 动作 |
|---|---|
| 多-LoRA 在线服务 + BGMV 是 decode 热点 + 非-310p + rank∈{8,16,32,64} + fp16/bf16 | 优先切自研 AscendC `bgmv_shrink` / `bgmv_expand` 向量核，替掉通用 torch_ops 组合路径 |
| 同上但芯片是 **310P** | 不切；继续走通用 `torch_ops` 回退（310P 无该向量核路径，尤其无 bf16 变体） |
| rank > 64，或 dtype 非 fp16/bf16 | 不在参考实现支持面内；要么退回通用路径，要么先扩核（新增 rank 分支 / dtype 门控） |
| 走 SGMV（段级、per-sequence 而非 per-token indices） | 可复用同一对 bgmv 核：先把 `lora_indices` 按 `seq_len` 展开成 per-token indices 再喂给 bgmv |

## 技术：为何一个定制向量核能承载整条 BGMV

BGMV 的本质是「按 token 各选一份权重做两次窄矩阵-向量乘」。通用框架把它拆成 gather（选权重）+ 若干 matmul/reduce，每步都是一次独立算子下发、一次中间张量落存再读回。逐 token decode 时 batch 小、算子多、访存占比高，拆装开销主导。

定制向量核把「按 `indices` 取权重 + 沿 rank/hidden 维做 reduce」**融进一个核**：

- **shrink**（`x·A`，hidden_in → rank）：输入宽（hidden）、输出窄（rank），一次核内点乘+归约得到中间 rank 维。
- **expand**（`·B`，rank → 输出 slice）：输入窄（rank）、输出宽，写回到输出张量的一段 slice。
- **按向量核数切 batch**：`blockDim = ceil(batchSize / numTokensPerCore)`，其中 `numTokensPerCore` 由 host 端按设备**向量核数**（AIV 数）均分 batch 得到——即每个向量核负责若干 token，充分占满 AIV。

好处：省掉多算子下发与中间张量往返，把 BGMV 从「一串小算子」收敛为「一个受控向量核」，在 decode 热点上直接减时延。

**rank 决定归约结构**：不同 rank 走不同 reduce 组合——rank=8 一次 BlockReduceSum；rank=16/32/64 叠加 PairReduceSum + BlockReduceSum。这是把 rank 维归约映射到向量核归约原语的结果，也是「只支持这几个 rank」的来源（每个支持的 rank 都要显式排一条归约路径）。

## 参考实现及其约束

参考实现：vllm-ascend（昇腾推理后端）的自研 BGMV 向量核，见 [AscendC](../../../concepts/frameworks/ascendc.md) 手写算子 + 平台分派。以下约束**是该参考实现的边界，不是 BGMV 技术本身的极限**——扩核即可放宽，但未扩之前是消费者选路的硬门。

**算子与注册**
- 两个 AscendC 向量核 `bgmv_shrink.cpp` / `bgmv_expand.cpp`；host 侧声明 `bgmv_shrink_impl` / `bgmv_expand_impl`，经 torch binding 注册为 `torch.ops._C.bgmv_shrink` / `bgmv_expand`（`torch::kPrivateUse1` device）。
- Python 封装把 `bgmv_shrink / bgmv_expand / bgmv_expand_slice / sgmv_shrink / sgmv_expand / sgmv_expand_slice` 全部落到这两个核上。SGMV 复用 BGMV 的做法：`torch.repeat_interleave(lora_indices_tensor, seq_len_tensor)` 把段级 indices 展开成 per-token indices，再喂 bgmv。

**平台门控（关键选路边界）**
- punica 分派按平台切：`if is_310p(): from vllm.lora.ops.torch_ops import ...`（310P 仍走上游通用 torch 组合算子）`else:` 用自研核封装。即**自研核仅在非-310p 芯片启用**。
- bf16 变体以 `#if (__CCE_AICORE__ >= 220)` 条件编译——旧 AICore（含 310P）没有 bf16 核。平台能力差异（AICore 版本、bf16 原生支持）见 [Atlas A3](../../../concepts/platforms/atlas_a3.md) 与其代际对照。

**dtype 门控**
- 两个 kernel 的 torch binding 均 `TORCH_CHECK(scalar_type == kHalf || scalar_type == kBFloat16, "only support half and bf16")`：**只支持 fp16 / bf16**，其它 dtype 直接报错。

**rank 门控**
- `bgmv_expand.cpp` 定义 `SUPPORTED_RANKS = {8,16,32,64}`，按 rank 走不同 reduce 组合（rank8=单次 BlockReduceSum；rank16/32/64 叠加 PairReduceSum/BlockReduceSum）；**rank > 64 不支持**。

**形状约束**
- shrink 要求 `x.size(1) > y.size(1)`（hidden_in > rank）。
- expand 要求 `x.size(1) <= slice_size` 且 `slice_size + slice_offset <= y.size(1)`。
- x / y / indices 首维需一致；`indices` 为 **int64 一维**。

**并行**
- `blockDim = ceil(batchSize / numTokensPerCore)`，`numTokensPerCore` 由 host 端按 `aiv_num`（`aclGetDeviceCapability(..., ACL_DEVICE_INFO_VECTOR_CORE_NUM)`）均分 batch 得到——按向量核数切 batch，每核处理若干 token。

## 依据（支撑的 case）

- 自研 AscendC BGMV 向量核存在、仅非-310p 启用、受 rank/dtype/平台门控——这些是合入 diff 携带的事实边界，覆盖两个 AscendC kernel、torch binding 的注册与 `TORCH_CHECK`、Python 封装、punica 分派的 `is_310p` 门控。
- 仓自报（PR 描述，无独立复测、无 baseline 命令明细）：QWen2.5-7B、vllm-ascend v0.9.2.rc1 上 TTFT / TPOT / 吞吐约 **+70%**。此为文档披露、**不并入既定事实面**，仅作方向性收益参考。
- vllm-ascend 的 punica 路径在非-310p 上已全量落到自研 BGMV 核，无通用 torch BGMV 残留。

## 反例 / 何时不适用

- **310P**：不启用自研核；强行走会因为无 bf16 核（AICore < 220）与分派门控落空。310P 继续用通用 torch 回退是当前正确路径。
- **rank ∉ {8,16,32,64} 或 dtype ∉ {fp16, bf16}**：不在支持面，torch binding 会直接 `TORCH_CHECK` 失败或无对应 rank 分支——此时该退回通用路径或先扩核。
- 该经验的可迁移面是「昇腾多-LoRA 的 BGMV 该走定制向量核 + 其平台/rank/dtype 边界」，不外推为「所有 LoRA 应用都必然更快」——收益系于 decode 小-batch 下多算子拆装开销被消除这一前提。

## Evidence

- 事件源（可下探）：[vllm-ascend-pr-1884-add-custom-kernels-for-lora-performance](https://github.com/vllm-project/vllm-ascend/pull/1884)
- 合并态 commit：`vllm-project/vllm-ascend@540336edc9db09072a9aaa486fbf7ce625da5b9e`
- 关键文件：`csrc/kernels/bgmv_shrink.cpp`、`csrc/kernels/bgmv_expand.cpp`、`csrc/torch_binding.cpp:199-311`、`vllm_ascend/lora/punica_wrapper/lora_ops.py`、`vllm_ascend/lora/punica_wrapper/punica_npu.py`

## 相关页面

- [ascendc](../../../concepts/frameworks/ascendc.md) —— 自研 BGMV 向量核用 AscendC 手写，直接调度 Vector（AIV）计算单元；本页是其在多-LoRA BGMV 场景下的应用与约束。
- [atlas-a3](../../../concepts/platforms/atlas_a3.md) —— 平台能力差异（AICore 版本 / bf16 原生支持）决定 bf16 核能否编译、以及 310P 与其它昇腾芯片的分派分野。
