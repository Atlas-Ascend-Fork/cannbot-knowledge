---
type: Optimization
title: 昇腾多模态 M-RoPE 优先走 triton-ascend triton_mrope，decode 吞吐优于原生 npu_mrope
description: 昇腾（vLLM 昇腾后端 vllm-ascend）上多模态 M-RoPE（multimodal rotary position embedding，position 为二维 [3,seq]，如 Qwen3-VL 系列）的 rotary embedding 算子选型规则：有两条可选实现——triton-ascend 的 triton_mrope kernel 与原生 torch_npu.npu_mrope 算子。分派门为 HAS_TRITON and positions.ndim == 2：Triton 可用且二维 M-RoPE position 时优先走 triton_mrope（forward_triton 路径），否则回退原生 npu_mrope（rotary_mode='half'，注明待 CANN 8.5.0 更新）。triton_mrope 在 decode 逐 token 阶段吞吐明显更优，收益集中在 TPOT/TPS（约 2×），精度基本持平——仓自报 benchmark：Qwen3-VL-235B-A22B-Instruct-W8A8 TP=8 TPS 49→105、TPOT 0.1472→0.0615；Qwen3-VL-8B-Instruct TPS 125→227。门控要点：triton_mrope import 须收在 HAS_TRITON 保护下，否则无 Triton 构建 import 期即失败；门用 positions.ndim==2 泛化而非绑定具体 mrope_section（早期写死 [24,20,20] 仅对 Qwen3-VL 特定 mrope_section 生效，过窄）。参考实现 vllm_ascend/ops/rotary_embedding.py 的 AscendMRotaryEmbedding.forward_oot/forward_triton，依赖 triton-ascend；Ascend 310P 不支持 Triton 须自动回退。适用 Atlas A3/A2 昇腾平台的 decode_slow 优化场景。
tags:
- task.optimization
- topic.attention
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/6009
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a3
- 310p
---

# 昇腾多模态 M-RoPE 优先走 triton-ascend triton_mrope，decode 吞吐优于原生 npu_mrope

## 适用场景

在昇腾（vLLM 昇腾后端 vllm-ascend）上部署**多模态大模型**、需要做 **M-RoPE（multimodal rotary position embedding，position 为二维 `[3, seq]` 结构，如 Qwen3-VL 系列）** 的 rotary embedding，且观测 decode 吞吐（TPOT/TPS）不理想时，本页给出算子选型的优先级判断。

前提与边界：

- 仅针对**多模态 M-RoPE**（二维 position），不针对普通一维 RoPE。
- 依赖 `triton-ascend`（[Atlas A3](../../concepts/platforms/atlas_a3.md) / A2 支持 Triton；Ascend 310P 不支持 Triton，须自动回退）。
- 通向的判断：M-RoPE 在昇腾上有**两条可选实现**——triton-ascend 的 `triton_mrope` kernel 与原生 `torch_npu.npu_mrope` 算子。前者在 decode 吞吐上明显更优，故应以「Triton 可用 + 二维 position」为门优先走 `triton_mrope`，把原生算子留作回退。

## 条件 → 优先尝试什么

**规则**：昇腾多模态 M-RoPE 的 rotary embedding：

- 若 `HAS_TRITON`（triton-ascend 构建可用）**且** `positions.ndim == 2`（二维 M-RoPE position）→ **优先走 `triton_mrope` kernel**（`forward_triton` 路径）。
- 否则（无 Triton 环境 / 非二维 position）→ 回退到原生 `torch_npu.npu_mrope`（`rotary_mode='half'`）。原生路径当前仍是待 CANN 8.5.0 更新完善的回退分支（源码注 `# todo: need cann update in 8.5.0`），不应作为 Triton 可用时的首选。

**为何有效**：`npu_mrope` 是通用原生算子；`triton_mrope` 是针对 M-RoPE 数据布局手写的 Triton kernel，在昇腾上 decode（逐 token）阶段的 rotary 计算更省，收益集中在 TPOT/TPS，精度基本持平（见 Outcome）。分派门用 `positions.ndim == 2` 而非绑定某个具体 `mrope_section`，使该优化对所有二维 M-RoPE 模型生效，而不只对某一模型的 mrope_section 生效。

**门控写法要点**（可迁移）：`triton_mrope` 的顶层 import 必须收在 `HAS_TRITON` 保护下，否则无 Triton 的构建会在 import 期因缺库直接失败：

```python
from vllm.triton_utils import HAS_TRITON
if HAS_TRITON:
    from vllm.model_executor.layers.rotary_embedding.mrope import triton_mrope

# forward 分派：Triton 可用且二维 position 才走 kernel，否则回退原生
if HAS_TRITON and positions.ndim == 2:
    return self.forward_triton(positions, query, key)
# ... 回退：torch_npu.npu_mrope(..., mrope_section=mrope_section, rotary_mode='half')
```

`forward_triton` 内部形态：`_match_cos_sin_cache_dtype(query)` → 从 `cos_sin_cache[positions]` 取 cos/sin，`chunk(2, dim=-1)` 后 `contiguous()`，再调 `triton_mrope(query, key, cos, sin, mrope_section, head_size, rotary_dim, mrope_interleaved)`，最后 reshape 回原 query/key 形状。

## 依据（支撑的 case）

**benchmark（仓自报、无独立复测）** — 引入该 triton 路径的前置改动 body 给出 triton_mrope vs 原生 npu_mrope baseline：

| 模型（配置） | metric | baseline(npu_mrope) | triton_mrope |
|---|---|---|---|
| Qwen3-VL-235B-A22B-Instruct-W8A8（TP=8） | accuracy | 83.76 | 83.59 |
| | TTFT (s) | 4.8771 | 4.3273 |
| | TPOT | 0.1472 | 0.0615 |
| | TPS | 49 | 105 |
| Qwen3-VL-8B-Instruct | accuracy | 80.65 | 80.86 |
| | TTFT (s) | 4.1744 | 3.1858 |
| | TPOT | 0.0499 | 0.0245 |
| | TPS | 125 | 227 |

收益集中在 **TPOT/TPS（decode 吞吐约 2×）**，精度基本持平（两配置 acc 一升一降，变动幅度小）。数字为仓自报 benchmark、无独立复测，取向作方向性依据而非精确 SLA。

## 反例 / 何时不走 triton_mrope

以下场景该规则不适用，不应优先走 `triton_mrope`：

- **无 Triton 环境**：`HAS_TRITON` 为假的构建（如 Ascend 310P 不支持 Triton）不适用本规则，须回退原生 `torch_npu.npu_mrope`；门控本身以 `HAS_TRITON` 收口保证此回退。
- **非二维 position**：普通一维 RoPE（`positions.ndim != 2`）不适用，只有多模态二维 M-RoPE position 才走 kernel。
- **反面教训——过窄的精确匹配门**：不要按具体 `mrope_section` 精确匹配来开门（早期写法把门写死为 `mrope_section == [24, 20, 20]`，仅对某一模型的 mrope_section 生效），这是过窄的门；应按二维 position 泛化，使优化覆盖所有二维 M-RoPE 模型。

## 参考实现及其约束

- **参考实现**：vllm-ascend 文件 `vllm_ascend/ops/rotary_embedding.py`，类 `AscendMRotaryEmbedding(MRotaryEmbedding)`，`forward_oot` 分派 + `forward_triton`。`triton_mrope` 从 `vllm.model_executor.layers.rotary_embedding.mrope` 导入。triton 侧依赖 `triton-ascend`（记录版本 3.2.0.dev20260105）。
- **该实现的约束（非技术本身的约束）**：
  - 原生回退分支还带一层判定——`mrope_section != [16, 24, 24]` 或设备为 950（`AscendDeviceType.A5`）时走父类 `super().forward_oot`；这是该仓当下的硬编码分派边界，迁移到别处不必照搬。
  - 早期版本曾把 triton 门写死为 `mrope_section == [24, 20, 20]`（仅 Qwen3-VL 特定 mrope_section），后泛化为 `positions.ndim == 2`；说明「按具体 mrope_section 精确匹配」是过窄的门，应按二维 position 泛化。
  - 原生 `npu_mrope` 路径注明待 CANN 8.5.0 更新，属阶段性回退实现。

## Evidence

- 源页（可下探）：[vllm-ascend-pr-6009-0-13-0-cherry-pick-bugfix-fix-bug-of-triton-mrope](https://github.com/vllm-project/vllm-ascend/pull/6009)
- 溯源 sha：`vllm-project/vllm-ascend@18eec9d515ca2eb81e1b0b96711a80c1b900b2b2`，文件 `vllm_ascend/ops/rotary_embedding.py`；合并态分派门为 `if HAS_TRITON and positions.ndim == 2`，回退分支为 `torch_npu.npu_mrope(..., rotary_mode='half')`。
- 层级：核心断言（triton_mrope 优先、`HAS_TRITON and positions.ndim==2` 门控、原生回退 + CANN 8.5.0 caveat）为合并态 diff 事实；benchmark 数字为仓自报披露、无独立复测。
- 施动者为 vllm-ascend 仓侧，非 Qwen 上游。

## 相关

- 框架页：[vllm-ascend](../../../training/concepts/frameworks/vllm_ascend.md)（vLLM 昇腾后端，本 M-RoPE 算子分派所在插件；注意语境差异——该页记的 RL rollout patch 把 M-RoPE 换成 `torch_npu.npu_mrope` 融合算子，是 train 侧 rollout 现状；本页 infer decode 经验是 Triton 可用时 `triton_mrope` 吞吐更优）
- 平台页：[atlas-a3](../../concepts/platforms/atlas_a3.md)（支持 Triton 的昇腾平台；310P 无 Triton 须回退原生）
- 同族 RoPE 算子选型经验：[interleaved-rope-npu-op-selection](../../runbooks/precision/interleaved_rope_npu_op_selection.md)（交错 RoPE 必须用专用算子、通用 RoPE 融合算子会破精度）
- Triton 不可用时的回退判断：[ascend-310p-no-triton-kernel-eager-fallback](../../runbooks/runtime/ascend_310p_no_triton_kernel_eager_fallback.md)（310P 不支持 Triton kernel，须补 host/eager 等价路径）