---
{
  "type": "Runbook",
  "title": "npu_apply_rotary_pos_emb 原地更新 q/k 导致的逐模块等价测试假阳性",
  "description": "reviewer 独立逐模块等价测试中 A3 RoPE 出现 max_abs=4.26562 / mean_rel=0.3165 的巨大偏差，而同会话端到端 golden 对齐（cosine 0.99989、贪心 token 全匹配）通过——模块级与整体级结果矛盾。最小约定探针显示 'half' 模式对 rotate_half 参考 maxerr 仅 0.0078125，但 q/ref/out 样本逐值相同，暴露根因：该算子原地更新 q/k 输入，参考是在调用算子之后用被改写的输入算的。判别：样本逐值相同 = 测试顺序伪影（先算参考/克隆输入后偏差回落到 0.015625）；偏差随 rotary_mode 换挡持续（interleave 对 rotate_half maxerr 1.3046875）= 真实语义不匹配。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# npu_apply_rotary_pos_emb 原地更新 q/k 导致的逐模块等价测试假阳性

## 适用场景

- 场景：在 Ascend NPU 上为融合算子（本例 `npu_apply_rotary_pos_emb`，TND layout、rotary_mode='half'）编写独立逐模块等价测试（fused vs eager 参考）时的测试方法与排障。
- 平台/版本：Ascend950PR_9589，torch_npu 2.12.0，CANN 9.1.0；模型为 Hunyuan-A13B-Instruct-FP8（GQA、head_dim=128、RoPE 先于 per-head QK RMSNorm）。
- 目标：区分「融合算子数值真的不等价」与「测试自身因原地更新产生假阳性」两类情况。
- 缺失信息：该行为未在官方文档中显式声明（文档仅说「原地更新」体现在接口描述中时不易被注意到）；其他 RoPE 类算子（npu_rotary_mul、npu_interleave_rope）未逐一验证是否同样原地更新。

## 触发与观测

- 触发（矛盾信号）：reviewer 独立逐模块等价测试 `tools/reviewer_module_check.py` 首跑，A3 RoPE 出现巨大偏差（逐字）：

```
[A3_rope_q] max_abs=4.26562 mean_rel=0.3165 shape=(7, 4, 16) ref_mean=0.773438
[A3_rope_k] max_abs=4.3125 mean_rel=0.3042 shape=(7, 2, 16) ref_mean=0.785156
```

  而同会话端到端 golden 对齐通过（cosine 0.99989、贪心 token 全匹配），且其余模块（A1/A2/A4/A5/M3/M1–M3）均在 BF16 舍入容差内——模块级与整体级结果矛盾。
- 探针观测（最小 RoPE 约定测试，D=8、T=3、N=2、固定种子，先调用算子再算参考）：'half' 对 rotate_half 参考 maxerr 仅 0.0078125、'interleave' 1.3046875、minus-sign 变体 1.875；且 q/ref/out 样本逐值相同。

## 探针与操作

判别探针（输出逐字，来源记录#141）：

```
half maxerr vs rotate_half= 0.0078125
interleave maxerr vs rotate_half= 1.3046875
vs minus-sign ref maxerr= 1.875
q sample [-0.92578125, -0.42578125, -2.640625, 0.1455078125]
ref sample [-0.92578125, -0.42578125, -2.640625, 0.1455078125]
out sample [-0.92578125, -0.42578125, -2.640625, 0.1455078125]
```

测试修复：把 eager 参考计算移到算子调用之前、并对 q/k 克隆输入（`q_save, k_save = q.clone(), k.clone()`），再跑同一测试。

## 机制与判别

- 根因：`npu_apply_rotary_pos_emb` 原地（in-place）更新 q/k 输入张量；原测试在调用算子之后才用同一 q/k 计算 eager 参考，参考值即来自已被算子改写的输入——`q sample`/`ref sample`/`out sample` 三者逐值相同即为此伪影的直接证据。
- 可区分解释分支：
  1. 测试顺序伪影（参考在算子之后计算、未克隆）→ 样本逐值相同、修复顺序后偏差消失（回落到 BF16 舍入量级）。
  2. 真实语义不匹配（如 rotary_mode 选错：interleave 对 rotate_half 参考 maxerr 1.3046875 持续存在，与样本对照无关）。
- 旁证判别：端到端 golden 通过而模块级大偏差，本身即提示测试工件问题优先于算子问题；固定种子 + 样本逐值对照是把两者区分开的最小探针。
- 未验证推断：文档对「原地更新」的表述位于接口描述（「在旋转位置编码计算中直接对结果执行原地更新」），是否所有 layout/mode 均原地未逐一验证。

## 验证信号

（平台：Ascend950PR_9589 / torch_npu 2.12.0 / CANN 9.1.0；tiny 随机张量单次运行）

- c1：npu_apply_rotary_pos_emb(TND, rotary_mode='half') 会原地更新 q/k 输入张量；等价性测试若在调用算子之后才计算 eager 参考（未克隆输入），参考值即来自被改写的输入，产生 max_abs=4.26562 / mean_rel=0.3165 量级的假阳性偏差。〔signals：来源记录#137（假阳性观测）、#141（探针确认样本逐值相同）〕
- c2：判别方法：固定种子下若 q/ref/out 样本逐值相同即为原地更新伪影（参考被算子改写）；偏差随 rotary_mode 换挡持续（interleave 对 rotate_half 参考 maxerr=1.3046875，half 仅 0.0078125）则为真实语义不匹配；先算参考/克隆输入后，A3 偏差回落至 max_abs=0.015625、mean_rel=0.0005286（BF16 舍入容差内）。〔signals：来源记录#141（探针）、#149（修复后逐模块复测）〕

修复后逐模块复核（逐字，来源记录#149）：

```
[A3_rope_q] max_abs=0.015625 mean_rel=0.0005286 shape=(7, 4, 16) ref_mean=0.773438
[A3_rope_k] max_abs=0.015625 mean_rel=0.0006105 shape=(7, 2, 16) ref_mean=0.785156
```

## 适用与失效边界

- 适用：所有对可能原地更新的 NPU 融合算子做等价/回归测试的场景；判定顺序：先固定种子做样本逐值对照，再下「不等价」结论。
- 边界：探针只能区分「测试伪影」与「真实不匹配」两类；真实不匹配时仍需按模式/布局/约束（TND 的 [T,1,D]、D=128 或 64 等）逐项排查。
- 失效/停止条件：若克隆输入 + 先算参考后偏差仍显著（超出 BF16 舍入量级），则为真实语义不匹配，应转向算子参数/版本排查而非继续怀疑测试；端到端 golden 与模块级测试结论冲突时，两者都不可直接采信，须以最小探针仲裁。
