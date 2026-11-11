---
type: Optimization
title: "X27: transpose-on-load 分形加载 + 全 shape 手动 mmad 二维 tile 网格（免 host 预转置）"
description: "在手动 mmad + host B 预转置 + MatmulImpl fallback 方案基础上做两个关键替代，把手动 mmad 的可覆盖范围从单 tile 微小 shape 扩展到全 shape 覆盖、不依赖 fallback。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.layout_transform
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X27: transpose-on-load 分形加载 + 全 shape 手动 mmad 二维 tile 网格（免 host 预转置）

**Operator type**: matmul（微小/中 shape，固定开销主导），C[M,N]=A[M,K]@B[N,K]^T（B 转置存储）
**Hardware**: Ascend910B2C (DAV_2201)

## 核心思路

在「手动 mmad + host B 预转置 + MatmulImpl fallback」方案基础上做两个关键替代，把手动 mmad 的可覆盖范围从单 tile 微小 shape 扩展到**全 shape 覆盖、不依赖 fallback**：

1. **transpose-on-load 替代 host B 预转置**：B 的 transB 由 `LoadToL0B<LOAD2D>` 的 `isBTranspose=true` 在 L1→L0B 分形加载时完成，**不需要额外的 host workspace 转置 pass**。关键区别：这不是仅支持 16x16 的 LoadData3D，也不是存在缺陷的 LoadData2D ifTranspose，而是 **L1→L0B 的 LoadToL0B LOAD2D isBTranspose=true 形态，910B2C 上对任意 M/N/K 正确**。免去 host 转置的内存 pass 和 workspace 管理。
2. **全 shape 二维 tile 网格**：输出 C 按 gridM×gridN 切 16 对齐 tile，每 tile 保留 FULL K（cube MMAD 内部吞 K），单条 Mmad 完成整 tile；按 `tid=blockIdx+i*blockDim` 走 tile 网格。原本会落入 MatmulImpl fallback 的中大 shape 也走手动路径，避免 fallback 开销。配合「并行度扩展」启发式：per-tile 操作数 >96KB 且 grid<24 时拆分大维摊到更多 core。
3. 叠加已有手段：AIC_ONLY 去 AIV 空转、紧凑 tiling 只读少量 int32、单 tile 整块装入 L0、fp32 Fixpipe NoQuant。

## Key code change
```cpp
// device 侧：
// 1) B 分形加载时完成转置（免 host 预转置 pass）
LocalTensor<half> l0b = l0bQue.AllocTensor<TPosition::B1>();
LoadToL0B<LOAD2D>(l0b, l1B, l0bLoad, isBTranspose=true);  // L1→L0B, transB 在读入时完成
// 2) 单条 Mmad（FULL K，cube 内部吞 K）
Mmad(l0c, l0a, l0b, mmadParams);   // unpadded m/n/k
// 3) fp32 Fixpipe NoQuant
FixpipeParamsV220 fp; fp.quantMode = QuantMode_t::NoQuant;
Fixpipe(l0c, cGm, ..., fp);
// 4) AIC_ONLY
KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY);
```

## 适用场景
- transB 类 matmul（B 转置存储）微小→中 shape：transpose-on-load 免 host 预转置 workspace pass，比 host 预转置方案少一次内存往返
- 需要「全 shape 手动覆盖」（不依赖 MatmulImpl fallback）时：二维 tile 网格 + 并行度扩展启发式，中大 shape 也手动化
- 前提：910B2C 上 LoadToL0B LOAD2D isBTranspose=true 对任意 M/N/K 正确（区别于仅 16x16 的 LoadData3D 陷阱、LoadData2D ifTranspose 坏路径）
- 上限：1x1 等极微 shape 受设备启动地板限制（物理不可达）；K 超大的 shape 需 K-slicing，收益有限

## 关联策略
X24（AIC_ONLY 任务类型）、手动 mmad 分形加载、LoadData3D 陷阱规避。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带；布局变换类改动需同时覆盖转置视图与原布局、多种 M/N/K 边界。
