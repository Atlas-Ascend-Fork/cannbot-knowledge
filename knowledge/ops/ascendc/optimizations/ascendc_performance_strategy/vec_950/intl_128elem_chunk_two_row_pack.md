---
type: Optimization
title: 交错模式按 128 元素 chunk 打包两行
description: 把交错模式“一行一个窗口”改成按 128 元素 chunk（64 pair）切块，DeInterleave 后一行一 lane，D=64 时一块吃两行
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/intl-128elem-chunk-two-row-pack.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：交错模式按 128 元素 chunk 打包两行

交错（interleaved）模式的自然块长是 **64 pair = 128 元素**，不是“1 行”。按 chunk 切块后，D=64（32 pair/行）的形状一个 64-lane 块吃两行，向量 lane 不再浪费一半。

## 1. 原理

逐行窗口写法（每行 128 元素窗口）：

```cpp
for (r...) for (w in wins) {                       // D=64 -> wins=1，只用 32/64 lane
    LoadAlign(ra, x + r*pitch + w*128);            // 64 元素
    LoadAlign(rb, x + r*pitch + w*128 + 64);       // 下一行的数据
    ...
    StoreAlign(y + r*pitch + w*128, ba, mask1);    // 只写 64 元素 = 1 行
}
```

chunk 写法（每块 64 pair）：

```cpp
for (c in chunks) {                                 // D=64 -> 每 chunk 2 行
    LoadAlign(ra, x + c*128); LoadAlign(rb, x + c*128 + 64);
    Cast(fa, ra); Cast(fb, rb);          // 全 lane
    DeInterleave(xe, xo, fa, fb);        // 64 lane = 两行的 even/odd 平面
    ... 6 条算术 ...
    Interleave(r0, r1, ye, yo);
    StoreAlign(y + c*128, b0); StoreAlign(y + c*128 + 64, b1);
}
```

D=128 时 chunk = 1 行；D=64 时 chunk = 2 行。cos/sin 按行序、pitch = H 排列，D=64 时两个相邻条目正好 64 个 float，一条 64-lane load 覆盖两行。

## 2. 性能问题模式

- 优化目标：提高 lane 利用率 + 消掉 per-row 窗口下标/掩码。
- 适用数据流：交错/成对重组类 elementwise（交错模式旋转编码、复数乘、twiddle 旋转）。

## 3. 正确性红线

- D=64 时两行分别对应 `c(r)`、`c(r+1)`；错位表现为“隔行错”。
- 尾行（奇数行 tile）用 32-pair 掩码、只写 1 行。
- b16 的 `DeInterleave` 前必须全 lane 宽化。

## 4. 泛化条件

- 策略作用域：common。
- 适用：`D % 64 == 0 && D <= 128`；行 pitch = D；cos/sin 行序、pitch = H。
- 不适用：D 非 64 倍数；相邻行不连续；行数 < 2。
- 与 `int64-narrow-int32-lane-packing` 的分工：那张卡压的是 dtype 窄域视图里的结构性死 lane（数据表示问题），本卡压的是“块长按行而不是按 lane 取”造成的 lane 浪费（切块粒度问题）。
- 与 `d2-pair-dintlv-row-per-lane` 的分工：那张卡把 D=2 的行-通道反交错做行并，本卡把 D∈{64,128} 的 128 元素 chunk 做两行打包；两者共用 DeInterleave/Interleave 原语，但块长推导完全不同。

## 5. 实施步骤

1. 块 = 128 元素 / 64 pair。
2. 行/chunk = 128 / D。
3. 两次 64-lane load + DeInterleave。
4. 算术 + Interleave + 两次 store。
5. cos/sin 取址 = chunk*64 个 float。
6. 奇数行尾行剥出。

## 6. LLM 前置问题

- 交错模式的块长是按 lane 定的还是按行定的？
- D 是多少？一个 64-lane 块能装几行？
- cos/sin 在 UB 里是按行序还是 dup 布局？相邻两行条目连续吗？
- tile 高度会是奇数吗？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`common`
- 相关策略：`d2-pair-dintlv-row-per-lane`（同为交错/反交错打包）、`int64-narrow-int32-lane-packing`（lane 压缩的另一路径）

## 检索卡（短卡）

动作：把交错模式“一行一个窗口”改成按 128 元素 chunk（64 pair）切块，DeInterleave 后一行一 lane，D=64 时一块吃两行
适用：D%64==0 且 D≤128；行 pitch=D；表项按行序排列、pitch=H
限制：D=64 时两行须对应相邻表项，错位即隔行错；奇数行尾行用 32-pair 掩码只写 1 行；b16 DeInterleave 前须全 lane 宽化
范围：交错/成对重组类 elementwise（旋转编码、复数乘、twiddle）
检索词：128-element-chunk、DeInterleave、Interleave、两行打包、pair-mask、lane 利用率
机会：按行切块时 D=64 只用一半 lane，且 per-row 窗口下标与掩码每行重算
代价：要求相邻两行表项在 UB 连续，与表项 dup 布局冲突
