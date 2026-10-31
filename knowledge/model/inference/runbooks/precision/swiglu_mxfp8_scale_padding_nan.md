---
type: Runbook
title: MXFP8 SwiGLU 后 MatMul 全 NaN：检查奇数 scale 的补齐字节
description: 在 950 MXFP8 融合量化路径中，区分有效 E8M0 scale 与偶数成对存储；未初始化补齐字节可能污染后续 QMM/GMM。
tags:
- task.debugging
- topic.precision
- topic.compute.quantization
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/src/swiglu_group_quant/op_kernel/swiglu_group_quant_base.h
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/src/swiglu_group_quant/op_kernel/swiglu_mx_quant_perf.h
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/examples/test_npu_swiglu_group_quant.py
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/1000
  role: evidence
created_at: '2026-10-29T04:09:05Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- '950'
---

# MXFP8 SwiGLU 后 MatMul 全 NaN：检查奇数 scale 的补齐字节

## 症状与触发

950 MXFP8 路径中，融合 SwiGLU 的量化值看似正常，但下游 QMM/GMM 全 NaN，结果还依赖之前的显存内容。PR 的触发实例为输入尾轴 320、输出宽度 160：每 32 元素一个 scale，产生 5 个有效 scale，但实际 scale 存储为 [T,3,2]。

## 快速检查与根因

检查每行第 6 个 E8M0 字节。旧实现只写前 5 个有效字节；补齐位置若残留 0xFF，会作为 NaN scale 被下游消费。把 shape 改成紧凑 [T,5] 不能修复接口布局；PR 报告 QMM/GMM 以 161002 拒绝该形状。

## 修复与验证

采用修复后的融合算子及匹配绑定：奇数有效 scale 数补零，UB 容量和 GM 搬出按完整 scale pair 计算，并同步对应 tiling。比较旧版、修复版与只清零补齐位置的对照，检查量化值、有效 scale、补齐字节及下游有限性。

来源在 950PR、CANN 9.2.0-beta.2 上报告了污染显存后复用地址的验证、24 个补齐子场景及 1056 组数值回归。报告来自 PR 作者，本批未编译或运行算子，也未测性能。

## 回退与残留风险

回退到已验证的匹配算子/绑定或高精度路径，并复查输出。只在调用方清零输出缓冲不保证 kernel 分配的实际 scale 缓冲被初始化；同时检查奇数宽度、分块尾部和大行分块，不能只测一个小 shape。

## Evidence

PR1000 已合入；固定 kernel、tiling 配套修改及测试文件支持该修复链路。来源测试中的 torch_npu 版本和独立执行方法仍应随原 PR 核对。
