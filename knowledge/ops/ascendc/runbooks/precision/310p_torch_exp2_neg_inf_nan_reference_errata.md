---
type: "Runbook"
title: "310P torch.exp2(-inf) 返回 NaN 的参考缺陷"
description: "310P 上 torch.exp2(-inf) 返回 NaN（torch.exp(-inf) 返回 0）；冻结 golden 在 masked_fill(-inf)+exp2 的 attention/MLA 参考里会产出 NaN/垃圾（归约前先清 pad 位可避免；先算 den 再清已无法恢复）。实现侧改用有限大负数 + 自然 exp，参考侧用 dtype-faithful compose + CPU 裁决。"
tags: [task.debugging, topic.precision, topic.activation]
status: stable
sources: []
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-11T09:46:56Z'
platforms: ["310p"]
---

# 310P torch.exp2(-inf) 返回 NaN 的参考缺陷

## 现象

在一个 dense block-table MLA decode 算子的迁移里，device golden 在**异构 `kv_len`**（同一 batch 内请求长度不同）的 case 上失败，失败形状很有辨识度：

- score 逐位正确；`e = exp2(s2 - m)` 的有限位置 maxabs ≈ 6e-8，但 `den = sum(e)` 变成 NaN，`out` 随之 NaN/垃圾；
- fp16 输出饱和成 ±65504，bf16 输出到 1e7 量级；`matched_ratio ≈ 0.125`（恰好是“无 padding 的那部分请求”）；
- 同一 case 的 CPU golden 完全正常，`ours vs CPU` PASS、`device golden vs CPU` FAIL——失败方向是“参考坏了”，不是实现坏了。

## 适用场景

- **工程形态**：310P 上的 torch 参考实现/冻结 golden（npubench、kernelbench 风格），以及任何“mask 位置置 `-inf` → `exp2` → 求和/归一化”的 attention/MLA/softmax/gating 算子。
- **API 路径**：`torch.exp2` / `torch.exp`（torch_npu eager）；实现侧的 `Exp`（自然 exp）+ 有限大负数掩码。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0 + torch_npu 2.9。
- **适用粒度**：`platform_wide` —— 310P 上任何用 `torch.exp2` 且输入可能含 `-inf` 的参考实现；不限于 MLA。
- **路线优先级**：`recommended_fastpath` —— 实现侧永远不要对 `-inf` 调 `exp2`；参考侧用“精确长度、无 padding”的 compose + CPU 裁决。
- **明确不适用 / 未验证场景**：其它 torch_npu/CANN 版本是否仍返回 NaN 未验证；`torch.tanh(-inf)=NaN` 是同族线索但本卡未在可核验 trace 中复现（见失效边界）；其它平台未验证。

## 根因

310P 的 torch_npu `exp2` 对 `-inf` 没有按 IEEE 返回 0，而是返回 **NaN**；同一输入下 `torch.exp(-inf)` 正常返回 0。最小探针（逐字）：

```python
import torch, torch_npu
d=torch.device('npu')
x=torch.tensor([-float('inf'), float('-inf'), -1e30, 0.0, 1.0], device=d)
print('exp2(-inf) ->', torch.exp2(x).cpu().tolist())
print('exp(-inf) ->', torch.exp(x).cpu().tolist())
# masked_fill then exp2
s=torch.zeros(2,4,8,device=d)
mask=torch.zeros(2,4,8,dtype=torch.bool,device=d); mask[:,:,4:]=True
s=s.masked_fill(mask, float('-inf'))
print('after fill sample', s[0,0].cpu().tolist())
m=s.amax(-1,keepdim=True)
print('m', m.flatten().cpu().tolist())
e=torch.exp2(s-m)
print('e sample', e[0,0].cpu().tolist())
print('sum', e.sum(-1).flatten().cpu().tolist())
```

输出（逐字）：

```text
.exp2(-inf) -> [nan, nan, 0.0, 1.0, 2.0]
exp(-inf) -> [0.0, 0.0, 0.0, 1.0, 2.7182817459106445]
after fill sample [0.0, 0.0, 0.0, 0.0, -inf, -inf, -inf, -inf]
m [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
e sample [1.0, 1.0, 1.0, 1.0, nan, nan, nan, nan]
sum [nan, nan, nan, nan, nan, nan, nan, nan]
```

冻结 golden 在异构 `kv_len` 的 padding 位置执行 `masked_fill(-inf)` 后统一 `exp2(s - m)`；这些位置变成 NaN。失败的关键是**顺序**：golden 先做 `den = sum(e)`（此时 pad 位的 NaN 已进入分母），之后才 `e.masked_fill(pad, 0)`；清零只改 e 自身，已经算出的 `den` 不会恢复，NaN 经 PV matmul 放大成 ±65504/1e7 的垃圾。若在 `sum` **之前**先把 pad 位清 0，`den` 可以正常——不要把“归约前清零”本身当成坏实践。**这与 subnormal/FTZ 无关**，是 `exp2(-inf)` 的 NaN 语义。

## 判别方法

1. **微探针**：`torch.exp2([-inf])` 是否 NaN、`torch.exp([-inf])` 是否 0。两条一对比即可定性。
2. **组合路径与清零顺序**：`s.masked_fill(mask, -inf)` → `e = exp2(s - m)`；先打印 `e` 的 mask 位置，若 NaN 即为本缺陷。再分别跑两种顺序：① `den = e.sum(-1)` 之后才 `e.masked_fill(pad, 0)`——`den` 保持 NaN；② **先** `e.masked_fill(pad, 0)` 再 `sum`——`den` 正常。两者对照可把“`exp2(-inf)` 产生 NaN”与“清零顺序错”分开。
3. **参考裁决**：同一 case 跑 `device golden vs CPU` 与 `device golden vs dtype-faithful compose`；若 CPU 正常、compose 正常、device golden 坏，则归类为 reference 问题，不是实现问题。
4. **排除 subnormal/FTZ**：`exp2(-1e30)` 返回 0（探针第 3 个元素），只有 `-inf` 触发 NaN；不要用 FTZ 解释。

## 解决配方

### 实现侧：不要对 -inf 调 exp2

用自然 exp + 有限大负数掩码。修复后的 MLA kernel causal unit：

```cpp
            Muls(sUb_, sUb_, bmm1Scale_, static_cast<int32_t>(rows * kTile));
            Muls(sUb_, sUb_, log2e_, static_cast<int32_t>(rows * kTile));
            if (tt < kTile) {
                Duplicate(maskUb_, 1.0f, static_cast<int32_t>(kTile));
                Duplicate(colBiasUb_, 0.0f, static_cast<int32_t>(kTile));
                Duplicate(maskUb_[tt], 0.0f, static_cast<int32_t>(kTile - tt));
                Duplicate(colBiasUb_[tt], kNegBig, static_cast<int32_t>(kTile - tt));
                ApplyColMask64(sUb_, maskUb_, colBiasUb_, rows);
            }
            // ...
            SubRowsBcast64(eUb_, sUb_, brcbUb_, rows);
            Muls(eUb_, eUb_, kLn2, static_cast<int32_t>(rows * kTile));
            Exp(eUb_, eUb_, static_cast<int32_t>(rows * kTile));
```

要点：

- `kNegBig` 是**有限大负数**（如 -1e30），不是 `-inf`；`s2 - m` 仍是有限负数，`exp((s2-m)·ln2)` 下溢到 0。
- `Muls(eUb_, eUb_, kLn2)` 把 base-2 指数转成自然 exp：`exp(x·ln2) = 2^x`；这样完全避开 `exp2`。
- 掩码用“乘 mask + 加 bias”的列掩码，而不是 `masked_fill(-inf)`；尾块位置直接得到 `kNegBig`。
- 若必须在实现里保留 `-inf` 语义，至少在调用 `Exp` 前把 `-inf` 替换成有限大负数，或显式 `Duplicate(0)` 清零。

### 参考侧：dtype-faithful compose + CPU 裁决

- 用“按精确 `kv_len` 分组、无 padding”的 compose 做绑定参考；padding 位置不存在，就不会把 `-inf` 送进 `exp2`。
- fp32 参考要复刻 golden 的两次 einsum（nope K=R + rope K=Dr），不要用单 GEMM；fp16/bf16 用单 GEMM。
- 对冻结 golden 的受影响 case，用 CPU literal golden 裁决；报告里归类为 **reference 问题**，记录受影响 case、证据与裁决结果。

compose 的核心（逐字）：

```python
            if query.dtype == torch.float32:
                # match the golden's two einsums exactly (nope K=R + rope K=Dr)
                s = (torch.bmm(qg[..., :R], kf[:, :, :R].transpose(1, 2))
                     + torch.bmm(qg[..., R:], kf[:, :, R:].transpose(1, 2)))
            else:
                s = torch.bmm(qg, kf.transpose(1, 2))             # [n, qH, L] fp32
            s = s * bmm1_scale * LOG2E
            m = s.amax(dim=-1, keepdim=True)
            e = torch.exp2(s - m)
            den = e.sum(dim=-1, keepdim=True)
            p = (e / den).to(torch.float16).float()               # golden P rounding
            o = torch.bmm(p, kf[:, :, :R]) * bmm2_scale           # [n, qH, R]
            out[bs] = o.reshape(n, q_len, H, R)
            l2 = m.squeeze(-1) + torch.log2(den.squeeze(-1))
```

注意 compose 的 `s` 已经按精确 `kv_len` 截断，没有 padding 位置；这是它不会触发 `exp2(-inf)` 的原因。

## 设计决策

- **为什么用 `Exp(x·ln2)` 而不是 `exp2`**：`Exp` 是自然 exp，对有限负数正常下溢到 0；`exp2` 在 310P 上对 `-inf` 返回 NaN。数学上 `2^x = e^{x·ln2}`，常数乘一次即可。
- **为什么用 -1e30 而不是 -inf**：-1e30 是有限值，`exp(-1e30)` 下溢到 0；同时它足够负，softmax 的 max 不会选中它。若用 -inf，就会再次踩 `exp2`/NaN 的坑。
- **为什么参考侧不直接改 golden**：冻结 golden 是评测契约的一部分，不能改；正确做法是用 dtype-faithful compose + CPU 裁决，并在报告中标注 reference 缺陷。
- **当前方案路线档位**：`recommended_fastpath`（实现侧）；参考侧 `safety_fallback`（CPU 裁决）。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0，torch_npu 2.9；device 3。
- 相关文件：`op_kernel/trtllm_mla_decode.cpp`（`Exp`/掩码）；`precision/ref_compose.py`（dtype-faithful compose）；`scripts/check_impls_multi.py`（三路对照）；`precision/precision_multi.json`。
- 复现探针：一条 `python3 -c` 即可（见“根因”）。

## 完整代码

微探针与实现/compose 的 causal unit 已在上文逐字内联。微探针是自包含的，可直接在 310P 上复跑；实现片段来自修复后的 MLA kernel（开发轨迹中该片段之后的编辑只改了相邻变量名）；compose 片段来自 `ref_compose.py` 的精确长度循环。

## 性能影响

本卡是参考缺陷/正确性修复，不改变实现性能。实现侧把 `exp2` 换成 `Exp(x·ln2)` 的代价是一次额外的 `Muls`（每元素一次乘），相对整个 softmax/PV 链可忽略；没有单独测量。

## 预防

- 在 310P 上写 masked softmax 参考/实现时，禁止对可能为 `-inf` 的位置调用 `exp2`；用自然 `exp` 或有限大负数。
- 异构 `kv_len` / padding mask 的 case 必须单独跑 device golden vs CPU；同构 case 全过不代表参考没问题。
- 看到“score 对、den 错、out 垃圾”且输出饱和到 ±65504/1e7，先查 `exp2(-inf)`，不要先怀疑 matmul。
- 报告里把 reference 缺陷与实现缺陷分开；受影响 case 用 CPU literal golden 裁决，并记录裁决矩阵。

## 验证信号

来源：TRT-LLM MLA decode 310P 战役的同一条开发轨迹（单条轨迹、单次上板；证据等级 `tool_observed`/`artifact_verified`）。

- 微探针逐字输出：`exp2(-inf) -> [nan, nan, 0.0, 1.0, 2.0]`，`exp(-inf) -> [0.0, 0.0, 0.0, 1.0, 2.718...]`，masked `e` 的 4 个 mask 位为 NaN，`sum` 全 NaN。（来源平台：310P；证据等级：tool_observed）
- 受影响 case 的指纹：`e` 的有限位置 maxabs ≈ 6e-8，`den` NaN，fp16 输出 ±65504、bf16 1e7、matched ≈ 0.125。（来源平台：310P；证据等级：tool_observed）
- 绑定参考：device golden 45/50；5 个异构 case 用 dtype-faithful compose 后 5/5 PASS，绑定参考 50/50；CPU literal golden 与 compose 一致。（来源平台：310P；证据等级：artifact_verified）

## 失效边界

- **版本依赖**：其它 torch_npu/CANN 版本是否仍 `exp2(-inf)=NaN` 未验证；升级后应重跑微探针。
- **同族 `tanh(-inf)`**：本地战训记录过 310P 上 `torch.tanh(-inf)=NaN`，但本 trace 的可核验证据里只有 agent 对 CPU 语义（-1）的假设，**没有 device 探针输出**；本卡不把它写成平台结论。若需要，单独补一条 device 探针。
- **不是 subnormal/FTZ**：`exp2(-1e30)=0`，只有 `-inf` 触发 NaN；不要用 FTZ 解释或“修 subnormal”绕过。
- **清零顺序**：本卡不否定“归约前清零 pad 位”的写法；在 `den=sum(e)` 之前把 pad 位清 0，den 正常。坏的是先算 den（已含 NaN）再清 e，此时 den 不会自动恢复。
- **参考侧**：CPU 裁决只适用于冻结 golden 的受影响 case；不要把 CPU 结果直接当作所有 case 的绑定参考（fp32 的 device matmul 是 fp16-internal，CPU 真值不同）。
- **未决项（优先）**：在其它 310P 版本上复现 `exp2(-inf)=NaN` 并定位到 torch_npu 的哪个算子实现；以及 `tanh(-inf)` 是否有同样的 device 行为。

## 坏实践

- 在 masked softmax 里对 `-inf` 调 `exp2`，然后花时间调 matmul/den 的数值。
- 在 `den = sum(e)` **已经算出 NaN 之后**才 `e.masked_fill(pad, 0)`，以为能把分母救回来；清零只影响 e，已算出的 den 不会恢复。若在 `sum` 前清零，den 可以正常——不要把“归约前清零”本身列为坏实践。
- 用“310P subnormal/FTZ”解释这个差异；探针已经证明 `-1e30` 正常、`-inf` 才 NaN。
- 为了匹配坏掉的 device golden 去改实现（例如把实现也弄成 NaN），这是反向的作弊。

## 误诊

- 第一轮看到 `den` 不对，先怀疑 `sum` 的 reduce 实现或 `m` 的 max 取错；逐步对照显示 `s2`、`m` 都与 CPU 逐位一致，只有 `e` 的 mask 位置是 NaN。
- 第二轮怀疑 `masked_fill` 本身在 device 上把 `-inf` 变成了 NaN；微探针显示 `masked_fill` 后的 `s` 仍是 `-inf`，是 `exp2` 把它变成 NaN。
