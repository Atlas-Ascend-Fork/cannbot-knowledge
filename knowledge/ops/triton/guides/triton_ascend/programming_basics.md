---
type: Guide
title: 编程基础：核心概念与标准 Kernel 结构
description: Triton Ascend 编程基础（核心概念 / 标准 Kernel 五步 / 边界 Mask / 编程模式 / Autotune）提炼摘要；完整正文见同目录 programming_basics_full.md。
tags: [task.implementation, topic.tiling, topic.implementation.masking, topic.compilation, topic.data_movement.memory_access]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/tree/c22984baa55e1506eadd7c72955d9bf669b1c959/
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/README.md
  role: supporting
created_at: '2026-08-13T00:00:00Z'
updated_at: '2026-10-14T00:00:00Z'
platforms: [a2, a3]
---
# 编程基础：核心概念与标准 Kernel 结构

> **canonical 正文见 [programming_basics_full.md](programming_basics_full.md)**（`Triton Ascend 基础知识参考手册`）；
> 本卡仅为该卡 §1 编程基础的提炼摘要与导航入口，正文以 full 卡为准，避免同一段正式知识独立维护两份。

## 摘要

- **核心概念**：Kernel（`@triton.jit`）、Grid（`kernel[grid](args)`）、Block（`tl.program_id`）、内存层次（全局/共享/寄存器）。
- **标准 Kernel 五步**：① 核间切分（`pid * BLOCK`）→ ② 核内循环 → ③ 构造索引 → ④ 边界 mask → ⑤ load → 计算 → store。
- **边界处理**：`mask = idx < numel`，`tl.load(..., other=0.0)`。
- **编程模式**：向量（逐元素）、归约（`tl.sum` + `tl.atomic_add`）、矩阵乘（`tl.make_block_ptr` + `tl.dot`）。
- **Autotune**：Ascend 不支持 CUDA 专用 `num_warps/num_ctas/num_stages`，主要调 `BLOCK_SIZE` 与 `grid`。

> 以上各小节的完整代码与说明见 [programming_basics_full.md §1 编程基础](programming_basics_full.md)。