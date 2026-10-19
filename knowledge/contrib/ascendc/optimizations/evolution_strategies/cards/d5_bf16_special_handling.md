---
type: Optimization
title: 'D5: BF16 & Platform-Specific Handling (BF16/多平台处理)'
description: 参考实现针对不同的Ascend芯片（910B, 910_93, 910_95, 310P, kirinx90等）提供了特定的配置支持。
tags:
- task.optimization
- topic.compute.composite
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/D5_bf16_special_handling.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- a2
---

# D5: BF16 & Platform-Specific Handling (BF16/多平台处理)

## 核心思想
参考实现针对不同的Ascend芯片（910B, 910_93, 910_95, 310P, kirinx90等）提供了特定的配置支持。这种多平台适配策略不仅体现在编译配置上，还深入到了Shape校验和平台特性检测层面。例如，在Ascend910_95上，算子支持2D shape (g, n)用于分组矩阵乘法场景，而在其他平台上只支持(1, n)或(n,)。这种差异化支持允许算子在不同的硬件能力和使用场景下都能获得最优性能。平台特性检测通过GetChipFeature函数实现，动态检测芯片是否支持特定功能（如Intrinsic_data_move_l12bt的bf16支持），从而实现运行时适配。

> 注：本卡实测平台为 a2（910B 系）；910_95/310P/kirinx90 等其他平台支持描述源自参考实现，为可迁移推断，未实测。

## 代码骨架

// === 改造前（基线）===
```cpp
this->AICore().AddConfig("ascend910b");
```

// === 改造后（优化实现）===
```cpp
this->AICore().AddConfig("ascend910_95");
this->AICore().AddConfig("ascend910_93");
this->AICore().AddConfig("ascend910b");
OpAICoreConfig config_kirin = GetKirinCoreConfig();
this->AICore().AddConfig("kirinx90", config_kirin);
```

## 关键修改点

1. 预期收益: 算子可移植性强，适配多种硬件; 算子可移植性强，支持多种华为Ascend芯片; 提升算子的可移植性和适用范围

## 常见陷阱

⚠️ 需要维护多个平台配置
⚠️ 需要额外的FP32 workspace内存和cast操作的开销
⚠️ 需要维护多套配置，增加测试负担

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
