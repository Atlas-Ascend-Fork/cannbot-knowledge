---
type: Optimization
title: "原生 fp32 Cube 单 pass 投影/attention 替代 fp16 hi/lo 3-mmad（对齐 PyTorch fp32 参考路径）"
description: "融合 GQA prefill 的 fp32 投影 GEMM 若用 fp16 hi/lo 3-mmad（3 次 fp16 mmad/k-step + split 双平面 GM 往返），计算量和数据通路都高于原生 fp32 matmul；改为原生 fp32 cube 单 pass（1 mmad/k-step）后 mmad 次数从 3 降为 1，并省去 split GM 往返。手动 Mmad 已是全精度，不要调用全局 SetHF32Mode(false)（per-core 持久寄存器会跨 kernel launch 污染后续 MIX kernel）。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X46: 原生 fp32 Cube 单 pass 替代 fp16 hi/lo 3-mmad

## 核心思路
PyTorch fp32 matmul 在目标平台默认 HF32 关闭即**单 pass 全精度 fp32**。若融合 GQA 的
fp32 路径用 fp16 hi/lo 3-mmad（3 次 fp16 mmad/k-step + split 双平面 GM 往返），
mmad 次数与 split 数据通路都多于参考，是性能差距的主要来源。

改为**原生 fp32 cube 单 pass**（Matmul 模板的 SPLIT3=false, IS_FP32=true,
1 mmad/k-step），可同时消除 xHi/xLo 的 GM 往返与权重 hi/lo 双平面。

## 关键工程发现
1. **SetHF32Mode(false) 不可调用**：它是 per-core 标量控制寄存器，**跨 kernel launch
   持久**，会破坏后续 MIX attention kernel（表现为特定 head 输出错乱）。**手动 Mmad
   已是全精度**，无需 HF32 开关。
   - **补充**：危险的是**全局** `SetHF32Mode(false)`；**Matmul 对象级**
     `mm.SetHF32(false, 0)` 是 per-matmul 实例配置，随对象析构失效、不跨 launch
     污染，**安全可用**。两条经验不冲突：手动 Mmad 路线不要碰全局开关，Matmul 高阶
     API 路线用对象级开关。
2. **native attention 单 pass**：QK^T 3-mmad→1-mmad, PV 2-mmad→1-mmad, 单 fp32 P 平面
   （ws2 槽减半）。
3. **小 fp32 M=1 回归**：mNum==1 时原生单 mmad 无 M 并行 → 强制 by=1 得最大 N 列拆分；
   极小 shape 路由回 fp16-hi/lo attention 路径避开 host K^T transpose 的 launch 开销。

## 适用场景
- fp32 输入的 GEMM（matmul/conv/attention 投影），当前用 fp16 hi/lo 3-mmad 且投影 MTE2-bound。
- 对齐 PyTorch/CANN 的 fp32 matmul 参考路径（torch_npu 默认 HF32 关闭）。
- 融合管线中 split GM 往返可消除的算子。

## 实现要点
- 复用 Matmul kernel 模板的 SPLIT3=false + IS_FP32=true 分支（1 mmad/k-step）。
- 手动 Mmad 已是全精度，**不要**调 SetHF32Mode(false)。
- host 直喂 fp32 平面（x2d/attn2d），删除 split hi/lo 与权重 hi/lo 双平面。
- M=1 小 shape 强制 by=1（N 列拆分）或路由回 fp16-hi/lo 路径。
- fp32 cube B-operand 必须 nZ L0B（zZ L1→nZ L0B LoadDataWithTranspose），nN→zN 是坏路径
  （Mmad 按错误格式解释）。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖 fp32 投影、QK^T/PV 与 M=1/小 shape，满足 fp32 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与单/双平面权重、ws2 槽需求，确认 SPLIT3=false 路径在容量内；检查 nZ L0B 格式、32B 对齐与 16×16 fractal。
