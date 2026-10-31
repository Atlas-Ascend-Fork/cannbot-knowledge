---
type: Runbook
title: 3DGS build mask 向量核异常：TileSum 的元素数被当成字节数
description: 在 A2 大 tile 数的 flash_gaussian_build_mask 中，按 int32 元素宽度检查 UB 分配、SetValue 和 DataCopyPad 的一致性。
tags:
- task.debugging
- topic.rendering
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/ops/ascendc/kernels/op_kernel/flash_gaussian_build_mask.cpp
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/merge_requests/142
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/merge_requests/58
  role: evidence
created_at: '2026-10-29T04:09:08Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a2
---

# 3DGS build mask 向量核异常：TileSum 的元素数被当成字节数

## 症状与触发

3DGS 调用 flash_gaussian_build_mask，在较大的 tile 数下报向量核硬件异常，来源实例包含 CCU instruction address check error、retCode=0x31。该错误文本本身不能唯一确定根因。

## 快速检查与根因

检查 LocalBufferInit 中 TileSumTensorBuffer 的 InitBuffer 字节数。旧实现只分配 tileNumPerCore 字节，实际 TileSumTensor 为 int32、按 tileNumPerCore 个元素写入和拷贝，所需容量为四倍；SetValue 和 DataCopyPad 因而越界。

## 修复、验证与回退

成套使用修复实现，让 InitBuffer 使用 tileNumPerCore × sizeof(int32_t)，并核对读写和搬出边界。PR 作者在 A2/CANN 8.5 上报告 numTile=10609（1024×1024、tile_size=10）修前异常、修后正常；numTile=32761 的 tile_sum 与 golden 逐元素一致，原有测试通过。

在实际模型路径中复测触发 shape、每核 tile 数和 tail，比较 tile_sum 与 golden，再跑原有 build mask 回归。本批仅核对修复源码和 PR，未编译或执行 NPU 算子。

若回退旧版，只在已验证安全的配置运行；缩小图片或 tile 数只是绕过触发，不能证明容量问题已经修好。先保留原始错误与 tiling 参数，再继续排查其他导致同类硬件错误的原因。

## Evidence

- [flash_gaussian_build_mask.cpp](../../../../../cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/ops/ascendc/kernels/op_kernel/flash_gaussian_build_mask.cpp)（primary）
- [远程来源](https://gitcode.com/cann/cann-recipes-embodied-ai/merge_requests/142)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-spatial-intelligence/merge_requests/58)（evidence）
