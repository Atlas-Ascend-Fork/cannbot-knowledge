---
type: Optimization
title: A2 多 LoRA BGMV 自研向量核：FP32 中间缓冲与 rank 边界
description: 固定 A2 CI 目标的自研 BGMV shrink/expand 实现；shrink 输出及 expand 输入使用 FP32 中间缓冲，外侧
  fp16/bf16，expand 仅有 rank 8/16/32/64 分支。310P 回退通用实现，不保证其他平台或通用性能收益。
tags:
- task.optimization
- topic.precision
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/1884
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/vllm_ascend/lora/punica_wrapper/punica_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/csrc/kernels/bgmv_shrink.cpp
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/csrc/kernels/bgmv_expand.cpp
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/csrc/torch_binding.cpp
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/vllm_ascend/lora/punica_wrapper/lora_ops.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/tests/e2e/singlecard/ops/test_bgmv_shrink.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/tests/e2e/singlecard/ops/test_bgmv_expand.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/540336edc9db09072a9aaa486fbf7ce625da5b9e/.github/workflows/vllm_ascend_test.yaml
  role: supporting
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-10-22T10:41:21Z'
platforms:
- a2
---

# A2 多 LoRA BGMV 自研向量核：FP32 中间缓冲与 rank 边界

## 平台证据与生命周期

固定 PR1884 提交 `540336edc9db09072a9aaa486fbf7ce625da5b9e` 的 `punica_npu.py` 确认：310P 导入 `vllm.lora.ops.torch_ops`，其他平台导入自研 `lora_ops`。原卡仅标 310P 与自研核主结论相反，现撤下该标注。同提交 CI 的单卡端到端任务明确使用 `linux-aarch64-a2-1` 和 910b 镜像，递归执行包含两份 BGMV 直接调用测试的单卡目录，因此主结论仅声明 A2 的实现与测试配置范围。没有读取实际 CI 运行结果或执行硬件测试，也不从“非 310P”推导所有 A3/950 均适用。

## 适用场景

在本卡固定版本支持的 A2 上做**多-LoRA 在线推理**、且发现 LoRA 应用（BGMV / punica 路径）是 decode 热点、拖慢逐 token 生成时，优先把 BGMV 的 shrink/expand 从「通用 PyTorch 组合算子」换成**自研 AscendC 向量核**。

判断这条规则是否命中你的处境：

- 你在做**多适配器同批服务**（一个 batch 里不同 token 属于不同 LoRA），走的是 **BGMV = Batched Gather Matrix-Vector** 语义：multi-LoRA 每 token 按一份 `indices` 选各自的 LoRA 权重，先 **shrink**（`x·A` → 中间 rank 维）再 **expand**（`·B` → 输出维）。
- 基线实现是**上游通用路径**：把 BGMV 由一串原生小算子（gather + 多个 matmul / reduce）拼出。若时间线显示这条组合路径占据热点，可进一步验证下发与访存开销；不能仅凭算子组合形式认定瓶颈。
- 你的目标为本卡有配置依据的 **A2**。源码按非 310P 分派自研路径，但分派条件本身不能证明其他平台已支持。
- 你的 LoRA **rank 落在 {8,16,32,64}**，权重 **dtype 是 fp16 或 bf16**（这是调用方必须满足的边界，Host 没有完整校验，见「参考实现及其约束」）。

若命中，规则是：**分别用 shrink 与 expand 两个定制向量核承载取权和归约，比较其与通用组合路径的正确性及端到端收益**。固定实现已经合入，目标负载是否获益仍需测量。

## 条件 → 优先尝试什么

| 条件 | 动作 |
|---|---|
| A2 多-LoRA 在线服务 + BGMV 是 decode 热点 + rank∈{8,16,32,64} + 外侧 fp16/bf16、中间 FP32 | 优先切自研 AscendC `bgmv_shrink` / `bgmv_expand` 向量核，替掉通用 torch_ops 组合路径 |
| 同上但芯片是 **310P** | 不切；继续走通用 `torch_ops` 回退（310P 无该向量核路径，尤其无 bf16 变体） |
| rank∉{8,16,32,64}，或外侧 dtype 非 fp16/bf16，或中间缓冲非 FP32 | 调用前拒绝，或明确选兼容实现；Host 不保证安全拒绝所有异常输入 |
| 走 SGMV（段级、per-sequence 而非 per-token indices） | 可复用同一对 bgmv 核：先把 `lora_indices` 按 `seq_len` 展开成 per-token indices 再喂给 bgmv |

## 技术：为何一个定制向量核能承载整条 BGMV

BGMV 的本质是「按 token 各选一份权重做两次窄矩阵-向量乘」。通用框架把它拆成 gather（选权重）+ 若干 matmul/reduce，每步都是一次独立算子下发、一次中间张量落存再读回。小 batch 下可能受到拆装开销影响，是否主导仍需真实时间线判断。

定制向量核把「按 `indices` 取权重 + 沿 rank/hidden 维做 reduce」**融进一个核**：

- **shrink**（`x·A`，hidden_in → rank）：输入宽（hidden）、输出窄（rank），一次核内点乘+归约得到中间 rank 维。
- **expand**（`·B`，rank → 输出 slice）：输入窄（rank）、输出宽，写回到输出张量的一段 slice。
- **按向量核数切 batch**：`blockDim = ceil(batchSize / numTokensPerCore)`，其中 `numTokensPerCore` 由 host 端按设备**向量核数**（AIV 数）均分 batch 得到——按可用向量核数分配 token；小 batch 下实际启动核数可少于 AIV 总数，例如 batch=1 仅一个 block。

这对核减少组合路径中的算子下发和部分中间张量，但 shrink→expand 的 FP32 缓冲仍需写回和读取。是否降低 decode 时延需在同负载下比较。

**rank 决定归约结构**：不同 rank 走不同 reduce 组合——rank=8 一次 BlockReduceSum；rank=16/32 使用 PairReduceSum 与 BlockReduceSum 组合；rank=64 连续执行两次 BlockReduceSum。这是把 rank 维归约映射到向量核归约原语的结果，也是「只支持这几个 rank」的来源（每个支持的 rank 都要显式排一条归约路径）。

## 参考实现及其约束

参考实现：vllm-ascend（昇腾推理后端）的自研 BGMV 向量核，见 [AscendC](../../concepts/frameworks/ascendc.md) 手写算子 + 平台分派。以下约束**是该参考实现的边界，不是 BGMV 技术本身的极限**——扩核即可放宽，但未扩之前是调用方选路时必须主动检查的条件。

**算子与注册**
- 两个 AscendC 向量核 `bgmv_shrink.cpp` / `bgmv_expand.cpp`；host 侧声明 `bgmv_shrink_impl` / `bgmv_expand_impl`，经 torch binding 注册为 `torch.ops._C.bgmv_shrink` / `bgmv_expand`（`torch::kPrivateUse1` device）。
- Python 封装把 `bgmv_shrink / bgmv_expand / bgmv_expand_slice / sgmv_shrink / sgmv_expand / sgmv_expand_slice` 全部落到这两个核上。SGMV 复用 BGMV 的做法：`torch.repeat_interleave(lora_indices_tensor, seq_len_tensor)` 把段级 indices 展开成 per-token indices，再喂 bgmv。

**平台门控（关键选路边界）**
- punica 分派按平台切：`if is_310p(): from vllm.lora.ops.torch_ops import ...`（310P 仍走上游通用 torch 组合算子）`else:` 用自研核封装。即固定代码在非 310P 分支导入自研封装；本卡仅确认 A2 配置范围。
- bf16 变体以 `#if (__CCE_AICORE__ >= 220)` 条件编译——旧 AICore（含 310P）没有 bf16 核。平台能力差异（AICore 版本、bf16 原生支持）见 [Atlas A3](../../concepts/platforms/atlas_a3.md) 与其代际对照。

**dtype 门控**
- 两个 kernel 的 torch binding 均 `TORCH_CHECK(scalar_type == kHalf || scalar_type == kBFloat16, "only support half and bf16")`：shrink 检查输入 `x` 为 fp16/bf16，expand 检查最终 `y` 为 fp16/bf16。中间张量不是半精度：shrink 内核的 `Y_T=float`，expand 内核的 `X_T=float`，Punica 按 FP32 申请中间 buffer。权重需与对应半精度输入/输出匹配，不能把这些检查理解为全部张量 dtype 已验证。

**rank 分支与调用方检查**

本卡的 rank 指实际中间张量的维度：shrink 从 `y.size(1)` 取值，expand 从 `x.size(1)` 取值，并传给 `maxLoRARank`。调用方必须让缓冲与堆叠权重的该维一致；不能只检查某个 adapter 声明的原始 rank，就忽略实际 padding 后的维度。
- `bgmv_expand.cpp` 定义 `SUPPORTED_RANKS = {8,16,32,64}`，按 rank 走不同 reduce 组合（rank8=单次 BlockReduceSum；rank=16/32 走 PairReduceSum + BlockReduceSum，rank=64 走两次 BlockReduceSum）；仅这四个 rank 有归约分支；其他值（包括小于 64 的未列值）也不能视为受支持。Host 没有显式 rank 白名单检查。

**形状约束**
- shrink 要求 `x.size(1) > y.size(1)`（hidden_in > rank）。
- expand 要求 `x.size(1) <= slice_size` 且 `slice_size + slice_offset <= y.size(1)`。
- x / y / indices 首维需一致；`indices` 为 **int64 一维**；Host 只检查一维形状，Device 将其按 `int64_t*` 读取，不能期待错误 dtype 一定先被安全拒绝。

**并行**
- `blockDim = ceil(batchSize / numTokensPerCore)`，`numTokensPerCore` 由 host 端按 `aiv_num`（`aclGetDeviceCapability(..., ACL_DEVICE_INFO_VECTOR_CORE_NUM)`）均分 batch 得到——按向量核数切 batch，每核处理若干 token。

## 依据（支撑的 case）

- 自研 AscendC BGMV 向量核存在、仅非-310p 启用、受 rank/dtype/平台门控——这些是合入 diff 携带的事实边界，覆盖两个 AscendC kernel、torch binding 的注册与 `TORCH_CHECK`、Python 封装、punica 分派的 `is_310p` 门控。
- PR 作者概括 Qwen2.5-7B 的改善约 70%，但配图中 TTFT、TPOT、吞吐的相对变化并不相同，且未标明具体硬件和完整命令。本卡不将该概括改写为“三项都提升 70%”，也不作为 A2 性能结论。
- 固定提交的 `punica_npu.py` 在非 310P 分支导入自研封装，310P 分支保留通用实现；不将这一文件的静态分派外推为所有版本和模型的运行路径。

## 反例 / 何时不适用

- **310P**：不启用自研核；强行走会绕过固定平台分派，且 BF16 编译还受 AICore 条件约束。310P 继续用通用 torch 回退是当前正确路径。
- **rank ∉ {8,16,32,64}、外侧 dtype ∉ {fp16, bf16} 或中间缓冲非 FP32**：不在支持面，外侧半精度检查可能报错，但 rank 由 Device 分支限制，Host 没有显式 rank 白名单检查——调用前应主动拒绝这些输入或选兼容实现；不能期待内核替调用方做安全回退。
- 该经验的可迁移面是「昇腾多-LoRA 的 BGMV 该走定制向量核 + 其平台/rank/dtype 边界」，不外推为「所有 LoRA 应用都必然更快」——收益系于 decode 小-batch 下多算子拆装开销被消除这一前提。

## Evidence

- 事件源（可下探）：[vllm-ascend-pr-1884-add-custom-kernels-for-lora-performance](https://github.com/vllm-project/vllm-ascend/pull/1884)
- 合并态 commit：`vllm-project/vllm-ascend@540336edc9db09072a9aaa486fbf7ce625da5b9e`
- 关键文件：`csrc/kernels/bgmv_shrink.cpp`、`csrc/kernels/bgmv_expand.cpp`、`csrc/torch_binding.cpp:199-311`、`vllm_ascend/lora/punica_wrapper/lora_ops.py`、`vllm_ascend/lora/punica_wrapper/punica_npu.py`

## 相关页面

- [ascendc](../../concepts/frameworks/ascendc.md) —— 自研 BGMV 向量核用 AscendC 手写，直接调度 Vector（AIV）计算单元；本页是其在多-LoRA BGMV 场景下的应用与约束。
- [atlas-a3](../../concepts/platforms/atlas_a3.md) —— 平台能力差异（AICore 版本 / bf16 原生支持）决定 bf16 核能否编译、以及 310P 与其它昇腾芯片的分派分野。

## 本轮来源核对与剩余缺口

两份直接算子测试与 A2 CI 调度是平台支持配置的依据，不是本仓取得的测试结果；A3 与 950 的适用性仍未由本卡确认。shrink 的 FP32 输出接入 expand 的 FP32 输入，不能把中间 buffer 改成 fp16/bf16。

`SUPPORTED_RANKS` 常量和归约分支覆盖 8/16/32/64，但 Host 没有显式 rank 白名单保护；未支持的 rank 不保证安全失败。Host 对空 batch 的检查还使用字符串条件，不能据此认为零 token 已安全处理。验证时先审查 dtype、indices、非空 batch、rank 和 slice 边界，再按固定测试的参考计算逐项比较；异常时恢复兼容实现。性能必须另做同负载对照，不新增 verified。
