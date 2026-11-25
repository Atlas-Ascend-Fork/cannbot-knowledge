---
type: Optimization
title: "已验证方案：权重流 GEMM 的天花板是「字节数」不是「带宽」——用实测 achieved 带宽而非 MTE2 占用率判定"
description: "MTE2 占用率接近饱和、cube 利用率很高，并不等于带宽已打满；权重流 GEMM 的天花板是每核搬运的字节数，应按实测 achieved 带宽而不是 MTE2 占用率判定。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_optimization_overview.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/transfer_larger_data_blocks.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/weight_stream_gemm_byte_ceiling.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 weight-stream-gemm-byte-ceiling）。
>
> 原始元数据：
>
> ```yaml
> id: weight-stream-gemm-byte-ceiling
> confidence: single_op
> op_families: [matmul, cv-mix]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/weight_stream_gemm_byte_ceiling.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/weight_stream_gemm_byte_ceiling.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 已验证方案：权重流 GEMM 的天花板是「字节数」不是「带宽」

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象
`aic_mte2_ratio` 0.95-1.00、`cube_utilization` 0.98、`aic_mac_ratio` 仅 0.028-0.119。
（短 burst、L2 未命中、有效核不足都会让 MTE2 空转）。

## 方案（度量口径）
把 **achieved 权重流带宽** 作为唯一判定量：

```
achieved_GBps = weight_bytes / gemm_segment_time
weight_bytes = (C^2 + (H*S)^2 + (W*S)^2 + C*C/4 + 3*C*C/4 + C^2) * 4
```

实测（大 14 例几何均值）：

结论：**已接近 PyTorch 参考的同口径带宽，带宽侧没有成倍空间**。剩余差距只能来自**减少搬运字节**，
而不是提高带宽或继续切分核。

## 有效范围
- 任何"权重远大于 L2（192 MB）且被反复流式读取"的 GEMM 型算子；
- 判据：`aic_mte2_ratio` 高但 `cube_utilization`/`mac_ratio` 低，且 achieved BW 已接近参考实现；
- 非目标：权重能常驻 L2 的中小 shape（那里瓶颈是固定开销/核数，见 X124）。

## 关键推论（本轮实测）
 但 672 B→128 B 会让大 case 桶从 1.0537 掉到 0.7663（见 F: baseN-upshift-collapses-burst）。
2. **减少字节必须不牺牲 burst/重叠**：按字节模型降低 A 重读次数与每核字节，
 因为连带把 baseK 168→32（burst 672 B→128 B）而净亏。
3. **尚待验证的唯一安全旋钮**：realize 的 `(baseM=48, baseN=32, baseK=168)` 只用 L0B 的
 21.5 KB / 32 KB；请求 `baseN=48`（48×168×4 = 32.3 KB ≤ 半 L0B）可让 A 重读 12→8 次、
 每核字节进一步下降，**burst 保持不变**。该点未实测，属下一轮候选，勿当已验证结论引用。

## 测量纪律（本轮踩到的坑）
 跨变体比较前必须把参考时间统一到同一份 canonical 集合。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/weight_stream_gemm_byte_ceiling.json`；引用时请结合上文适用条件与失效边界判断适用范围。

