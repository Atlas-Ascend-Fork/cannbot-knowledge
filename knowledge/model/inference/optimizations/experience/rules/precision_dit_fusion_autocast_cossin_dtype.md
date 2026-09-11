---
type: Optimization
title: 生成模型 (DiT) 接融合算子 / autocast 时的 dtype·混精·RoPE cos-sin 布局精度对齐
description: 生成模型 (DiT) 接融合算子 / autocast 时的 dtype·混精·RoPE cos-sin 布局精度对齐。把 dit / 扩散式生成模型的原生小算子（MoE gate 打分、RoPE）换成 NPU 融合算子，或对整块前向开 torch.autocast(dtype=bfloat16) 后，出现下面任一现象，先怀疑融合算子与 autocast 的 dtype·混精·广播布局边界没对齐，而非模型逻辑本身： 输出与小算子基线对不上（cos_sim 明显偏离）； 计算图里多出成片冗余 cast 算子； 某个本应 fp32 的分支被自动混精静默降到 bf16、数值敏感处掉分。
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/218
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/233
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 生成模型 (DiT) 接融合算子 / autocast 时的 dtype·混精·RoPE cos-sin 布局精度对齐

## 适用场景

把 [dit](../../../concepts/modules/dit.md) / 扩散式生成模型的原生小算子（MoE gate 打分、[RoPE](../../../concepts/modules/mla.md)）换成 NPU 融合算子，或对整块前向开 `torch.autocast(dtype=bfloat16)` 后，出现下面任一现象，先怀疑**融合算子与 autocast 的 dtype·混精·广播布局边界没对齐**，而非模型逻辑本身：

- 输出与小算子基线对不上（cos_sim 明显偏离）；
- 计算图里多出成片冗余 cast 算子；
- 某个本应 fp32 的分支被自动混精静默降到 bf16、数值敏感处掉分。

## 三条可迁移的边界对齐规则

### 1. 必须保 fp32 的分支要显式关 autocast

外层开 `torch.autocast(dtype=bfloat16)` 后，即便分支内显式 `.float()` 或权重本身是 fp32，计算仍会被自动转 bf16——要么损伤本应 fp32 的精度（如 gate 打分对数值敏感），要么徒增 cast。对必须 fp32 的分支包一层显式关闭：

```python
with torch.npu.amp.autocast(enabled=False):
    if self.wg.weight.dtype == torch.float32:
        hidden_states = hidden_states.float()
    logits = self.wg(hidden_states)   # gate 打分保 fp32
```

### 2. 跨到 bf16 计算的混精边界常量预转目标 dtype

参与 bf16 计算的常量（RoPE 的 cos/sin）若停在 fp32，会在每次进入 bf16 计算时被运行时反复插入 `float32→bf16` cast。预先一次性 `.to(bfloat16)`，消掉这批冗余 cast 算子：

```python
cos = real_batched_index_select(cos, dim=1, idx=position_ids).to(torch.bfloat16)
sin = real_batched_index_select(sin, dim=1, idx=position_ids).to(torch.bfloat16)
```

### 3. 交错 (interleaved) RoPE 的融合算子要显式选交错模式 + cos/sin 4D 广播布局

用通用 RoPE 融合算子 `torch_npu.npu_rotary_mul(x, cos, sin)` 不指定 `rotary_mode` 去替换交错式 RoPE，旋转配对会错位、输出偏离 `rotate_half` 风格的小算子参考实现。修法两步：

```python
# 显式选交错模式；cos/sin 直接从已备好的 4D 布局解包，不再函数内 reshape/搬运
cos, sin = freqs_cis
xq_out = torch_npu.npu_rotary_mul(xq, cos, sin, rotary_mode="interleave")
xk_out = torch_npu.npu_rotary_mul(xk, cos, sin, rotary_mode="interleave")
```

并把 cos/sin 从 2D `[S, D]` 预整形为 4D `[1, S, 1, D]` 广播布局、在上游（序列并行分片路径与采样路径两处）**一次性完成**，替代每个 transformer block 调用时的逐块 reshape + host→device 搬运：

```python
freqs_cos = freqs_cos.reshape(1, -1, 1, dim_thw)   # 分片路径：2D → 4D
freqs_cos = freqs_cos.to(self.device).unsqueeze(-2).unsqueeze(0)   # 采样路径：一次性上移+整形
```

交错 RoPE 的算子选型本身（专用 `npu_interleave_rope` vs 通用算子的 interleave 模式，通用算子选错模式会使 cos_sim≈0）见 [interleaved-rope-npu-op-selection](../../../runbooks/precision/interleaved_rope_npu_op_selection.md)；本页补的是「选对模式后 + cos/sin 4D 布局上移」的精度与冗余消除。

## 参考实现及其约束

- autocast fp32 gate + cos/sin 预转 bf16 的参考实现：cann-recipes-infer 的 HunyuanImage-3.0 适配（`adaptor_patches/hunyuan.py`，外层 bf16 autocast 下的 NPU 推理）。
- rotary_mode 交错 + cos/sin 4D 布局上移的参考实现：cann-recipes-infer 的 [HunyuanVideo](../../../concepts/models/hunyuan_video.md)（`posemb_layers.py` / `inference.py`，序列并行分片路径 + 采样路径两处都收敛到 `[1, S, 1, D]`）。
- 迁移边界：上述分支名、开关、`dim_thw` 布局是这两个参考实现的具体形态；换到别的 DiT 生成模型时，「保 fp32 分支关 autocast / 边界常量预转 dtype / 交错 RoPE 选交错模式」的对齐思想不变，具体分支与布局须按模型重定，`rotary_mode` 以该模型小算子的旋转语义为准。

## 风险 / 回退

- `autocast(enabled=False)` 只对包起来的分支生效，勿误关掉需要 bf16 加速的主干。
- `rotary_mode` 选错（交错模型用默认模式、或非交错模型用 interleave）都会破精度——迁移时用小算子参考实现逐 token 对齐验收，不要只看不 crash。

## Evidence

- diff 事实（@fdb79bf65a8b）：gate 处 `torch.npu.amp.autocast(enabled=False)`、cos/sin `.to(torch.bfloat16)` 预转，与优化文档「消除冗余算子」两小节一致。收益（消冗余 cast / 保 fp32）为定性、无 before→after 数字。溯源下探 [cann-recipes-infer-pr-218-feat-support-hunyuanimage-3-0-model-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/218)
- diff 事实（@cec5c22b8960）：`npu_rotary_mul(..., rotary_mode="interleave")` 新增、cos/sin 4D `[1,S,1,D]` 整形上移、移除逐块 reshape/搬运。「默认旋转模式与交错约定不匹配致精度偏离」为对 diff 的机制推断（未取到算子规格独立核实），修复前后精度数值源未披露。溯源下探 [cann-recipes-infer-pr-233-fix-hunyuanvideo-rope-debug](https://gitcode.com/cann/cann-recipes-infer/merge_requests/233)