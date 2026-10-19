---
type: Optimization
title: 'R5: 非对齐访问优化'
description: 使用 UnalignRegForLoad/Store 优化非 32B 对齐地址的数据访问。
tags:
- task.optimization
- topic.compute.composite
status: deprecated
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/R5_unalign_opt.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- '950'
---

# R5: 非对齐访问优化

> ⚠️ **已废弃**：使用虚构 UnalignRegForLoad API，与 P7（DataCopyPad）/ P11（尾块处理）重叠，零引用，仅作方向留档。**去向**：无直接继任卡，仅留档参考。


## 核心思想
使用 UnalignRegForLoad/Store 优化非 32B 对齐地址的数据访问。

## 代码骨架

// === 改造后（优化实现）===
```cpp
// Baseline: 对齐加载 + 手动拼接
// (需要两次 LoadAlign + Shift 操作)

// Evolved: 使用 UnalignReg
UnalignRegForLoad ureg;
LoadUnAlignPre<float>(ureg, srcAddr);  // 预初始化（循环外）

for (uint16_t i = 0; i < repTimes; ++i) {
    LoadUnAlign<float, POST_MODE_UPDATE>(srcReg, ureg, srcAddr, stride);
    // srcAddr 自动更新
    Adds(dstReg, srcReg, scalar, mask);
    StoreAlign(dstAddr + i * repSize, dstReg, mask);
}
```

## 常见陷阱

⚠️ 收益**: 减少非对齐场景的访问次数
⚠️ 风险**: UnalignReg 资源有限（每 VF 最多 4 Load + 4 Store）
⚠️ 复杂度**: 需要 Pre/Post 配对调用
