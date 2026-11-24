---
type: Optimization
title: 车道跨距对齐 + 列打包（VL/cal 列进一次向量 op）
description: 把 UB 行距改成 VL 的整除因子 cal，P=VL/cal 个连续输出列一次向量 op 算完，filter 预复制 P 份，32B gap 用 stride 桥接
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/lane-stride-packing-32b-gap-alignment.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：车道跨距对齐 + 列打包（VL/cal 列进一次向量 op）

把 UB 行距从 `CeilAlign(C,16)` 改成 VL 的整除因子 `cal`，使 `P = VL/cal` 个连续输出列在 UB 里连续覆盖一个 VL，filter 预复制 P 份，一次 `LoadAlign+Add+Max` 同时算出 P 列；两侧 stride 用 `gap32 = (cal*2 − AlignUp(C*2,32))/32` 桥接 Normal 模式的 32B 块推进。

## 1. 原理

lane 占用率是「每列一次 op」形态下的隐性成本：C 远小于 VL 时，一次 op 只搬 C/VL 的数据，指令数却按整 op 计。因为**窗口行距是实现自己定的**（padded 行布局），把它改成 VL 的整除因子不花任何额外代价，却让 P 列共享一次 op。

```
未打包（cal = CeilAlign(C,16)）:  每列 1 op，lane 占用 C/128
打包（cal | VL，P = VL/cal）  :  每 P 列 1 op，lane 占用 P*C/128 ≈ 100%
```

三个必须同时满足的细节（库内既有卡没写全的部分）：

1. **cal 必须整除 VL**：fp16 VL=128，候选只有 16/32/64/128。C=97 → cal 只能 112（不整除）⇒ P=1，无收益。
2. **32B gap 桥接**：`DataCopyPad` Normal 模式在 UB 侧按 `AlignUp(blockLen,32)` 推进块，而真实行距是 `cal*2B`，差值必须以 `srcStride/dstStride` 补上：
   ```
   gap32 = (cal*2 - AlignUp(C*2, 32)) / 32      # C=63/cal=64 → 0；C=43/cal=64 → 1
   ```
   漏了这一步的表现是**整列错位**，不是局部误差。
3. **垃圾 lane 不能写回**：`[C, cal)` 是填充通道（不填 -inf、不参与 store），store 的 `blockLen` 必须是 `C*dtypeSize` 而不是 `cal*dtypeSize`。

## 2. 性能问题模式

- 优化目标：把 C ≪ VL 的算子的 lane 占用从 C/128 提到 ~100%
- 判定入口：`aiv_vec_time / Duration` 高，且 `C ≤ 64`（此时每列一个 op 的 lane 浪费 ≥50%）

## 3. 正确性红线

- `gap32` 算错 → 整列错位
- `P>1` 时窗口要留 `pack` 列 slack，否则末组 `LoadAlign` 读越界（那几列不填 -inf，被掩码即可）
- `[C, cal)` 的垃圾 lane 绝不能写回（store `blockLen = C*dtypeSize`）
- 只有 `sw == 1` 才能打包；`sw>1` 时列间距被 stride 打散
- `C>128` 且不做通道分块时 P=1，不要强上

## 4. 泛化条件

适用：

- 逐输出列做向量计算、lane 数由通道维决定、`C ≪ VL`
- UB 行距由实现自选（padded 行布局）
- filter 可预复制（一次 op 的 filter 操作数是 VL 个 lane）
- V 管是绑定/次绑定管

不适用：

- `sw > 1`
- `C > 128` 且未做通道分块（cal 只能 > VL）
- `C ∈ (64,128]`：cal=128、P=1，无余量（C=127 已是 99% 占用）
- 与“通道 tile 列打包”类思路的差别：本卡补齐三点——`cal` 必须整除 VL（否则 lane 仍填不满）、UB 块推进按 `AlignUp(blockLen,32)` 而非 `blockLen` 造成的 32B gap 必须显式用 stride 桥接、`C > VL` 必须先做通道分块。
- 与 `int64-narrow-int32-lane-packing` 的分工：那张卡压的是 dtype 视图里的结构性死 lane，本卡把“小通道维的多个输出列”打进同一个 VL——前者改数据表示，后者改 tiling 粒度。

## 5. 实施步骤

1. UB 行距改为 `cal = C<=16?16 : C<=32?32 : C<=64?64 : CeilAlign(C,16)`
2. `P = VL/cal`（`cal<VL && sw==1 && tap 集合有特化体`），否则 1
3. filter 预复制 P 份（复用 tile-filter VF：`rows=taps, cp=cal, iBlk=P`）
4. VF 按列组循环：列步长 `P*cal = VL`、tap 步长 `cal`、filter 步长 `VL`、掩码 `ncol*cal`
5. 搬入/搬出/预载的 UB 侧 stride 用 `gap32`；GM 侧 stride 保持 0
6. 窗口为末组多分配 `pack` 列
7. 验收：边界/越界形状逐元素一致，且逐例时间不劣于打包前

## 6. LLM 前置问题

- 目标形状的 C 是多少、是否 `≪ VL`？
- `cal` 能否整除 VL？
- `sw == 1`？
- 是否已确认 store 只写 C 个 lane、且 stride 用 gap32 桥接？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`op_class`
- 相关策略：`wide-descriptor-store-collapse`（同一实现里的写回侧合并，两者必须共用 32B 对齐口径）、`int64-narrow-int32-lane-packing`（lane 压缩的另一路径）

## 检索卡（短卡）

动作：把 UB 行距改成 VL 的整除因子 cal，P=VL/cal 个连续输出列一次向量 op 算完，filter 预复制 P 份，32B gap 用 stride 桥接
适用：逐输出列做向量计算、lane 数由通道维决定、C 明显小于 VL；UB 行距可自选
限制：cal 必须整除 VL；只有 sw==1 才能打包；C>128 须先做通道分块；store 只写每列前 C 个 lane
范围：小通道卷积/池化/形态学/逐通道 elementwise
检索词：cal 整除 VL、列打包、filter 预复制、32B gap、Normal 模式、前缀掩码末组
机会：C 远小于 VL 时一次向量 op 只用 C/VL 的 lane，V 管绑定而 lane 大量闲置
代价：末组不足 P 列要前缀掩码收窄，窗口需多留 P-1 列
