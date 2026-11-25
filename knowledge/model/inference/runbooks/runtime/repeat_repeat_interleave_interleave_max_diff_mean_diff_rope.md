---
{
  "type": "Runbook",
  "title": "RoPE cos/sin 展开模式错误（TILE 被写成 INTERLEAVE）：部分旋转优化激活潜伏 bug 致 8 视频全毁",
  "description": "DiT 类模型把 eager RoPE（einops `repeat(cos, \"... d -> ... 1 (2 d)\")` + `rotate_half`）替换为 `torch_npu.npu_rotary_mul`（rotary_mode='half'），并放宽启用条件到部分旋转",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# RoPE cos/sin 展开模式错误（TILE 被写成 INTERLEAVE）：部分旋转优化激活潜伏 bug 致 8 视频全毁

## 适用场景

- DiT 类模型把 eager RoPE（einops `repeat(cos, "... d -> ... 1 (2 d)")` + `rotate_half`）替换为 `torch_npu.npu_rotary_mul`（rotary_mode='half'），并放宽启用条件到部分旋转（`ro_dim <= head_dim`，本例 ro_dim=96、head_dim=128）。
- 症状：推理无报错、日志无 NaN/warning，但生成视频画面完全错误（本例 daVinci-MagiHuman 8/8 模式全毁，base/distill/sr/TI2V 无一幸免）。

## 触发与观测

- 触发（source 0 seq 1/134，user_reported）：apply_rotary_emb_torch 部分旋转优化（`ro_dim == x.shape[-1]` 放宽为 `<=` 并对 `x[..., :ro_dim]` 走 `npu_rotary_mul`+cat）后输出视频画面全错；日志检索 error/warning/nan 零命中（source 0 seq 183，tool_observed）。
- 设备 micro-test（source 0 seq 195/209，tool_observed）：fp32 下 npu_rotary_mul 路径 vs 原始实现 Max diff 6.955590 / Mean 0.609720——排除 bf16 精度问题；同时单元素（[0,0,0,0]、[0,0,0,48]）与未旋转部分（96-127 维）完全一致，说明公式正确而 cos/sin 排布错位。

## 探针与操作

- 探针 1（source 0 seq 219，tool_observed，einops 语义对照）：

```text
repeat 'd -> (2 d)':  [1, 2, 3, 4, 1, 2, 3, 4]
repeat 'd -> (d 2)':  [1, 1, 2, 2, 3, 3, 4, 4]
repeat_interleave(2): [1, 1, 2, 2, 3, 3, 4, 4]
```

即原始 `"... 1 (2 d)"` 是 TILE `[c0..c47,c0..c47]`，优化代码的 `repeat_interleave(2, dim=-1)` 是 INTERLEAVE `[c0,c0,c1,c1,...]`——两者不可互换。
- 探针 2（source 0 seq 235，tool_observed）：with/without `.contiguous()` 结果完全相同（max_diff 均 0.017566），排除非连续内存问题；`npu_rotary_mul` 对非连续切片输入本身正确。
- 修复：三处 `repeat_interleave(2, dim=-1)` → `torch.cat([cos, cos], dim=-1)`（TILE）——`apply_rotary_emb_torch` r1/r2 与 `DiTModel.forward` 预展开 rope_cos/rope_sin（source 0 seq 244-248 edits）。

## 机制与判别

- 机制：half 模式 RoPE 的 `x_new = cat(-x2, x1)` 按前后半配对，要求 cos/sin 同为 TILE 排布；INTERLEAVE 展开使每个频率分量的 cos/sin 与错误维度相乘，元素级公式仍"局部正确"（个别下标吻合）但整体旋转矩阵错位，且不产生任何运行时错误——典型的静默语义破坏。
- 潜伏激活路径：错误写法早在三项融合算子 commit（175e123，6 月 27 日）已引入，但被 `ro_dim == x.shape[-1]`（96≠128）守卫死锁；部分旋转优化把条件放宽为 `<=` 才激活。放宽 dormant 分支的条件时，该分支内的历史 bug 会一并引爆。
- 判别：bf16 噪声基线（FIX 后 max_diff=0.017566）vs 语义错误（BUG max_diff=8.008636）相差 ~450×；fp32 下修复后逐位相等。

## 验证信号

- BUG/FIX 对照（source 0 seq 229，tool_observed，逐字）：

```text
BUG (repeat_interleave/INTERLEAVE): max_diff=8.008636, mean_diff=0.572396
FIX (cat/TILE):                     max_diff=0.017566, mean_diff=0.001058
```

- 端到端算子级复验（source 0 seq 269，tool_observed）：`apply_rotary_emb_torch` 与 `apply_rotary_emb_npu` 两路径 bf16 max_diff=0.017566（精度噪声），float32 `max_diff=0.00000000` 完全一致。
- 修复后未重跑整网视频生成——画质验收（视频画面正常）仍待端到端复验。

## 适用与失效边界

- 适用：任何 einops `(2 d)` TILE 语义 RoPE 迁移到 npu_rotary_mul 的替换审查；含部分旋转（ro_dim < head_dim）路径启用前的等价性测试（fp32 逐位比对是最小充分探针）。
- 失效/停止：若原始实现本来就是 `(d 2)`/interleaved 语义，则 `repeat_interleave` 才是正确展开——必须先核对原始模式再选展开；本卡结论限定 non-interleaved (half) 语义。附带观察：x 与 cos 最后一维不匹配时 npu_rotary_mul 报 561002（aclnnRotaryPositionEmbedding），可用于 shape 探针但与本案根因无关。

## 附：断言存档

- RoPE 优化画质全毁根因：原始 einops repeat "... d -> ... 1 (2 d)" 是 TILE 展开 [c0..c47,c0..c47]，优化代码误用 repeat_interleave(2)（INTERLEAVE [c0,c0,c1,c1,...]），half 模式旋转矩阵维度错位且无任何运行时报错；fp32 下 npu_rotary_mul 路径 Max diff 6.96，修复后 bf16 仅 0.0176（噪声）、fp32 逐位相等
