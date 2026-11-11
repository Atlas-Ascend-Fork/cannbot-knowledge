---
type: Optimization
title: "X21: 910B2C Cube 化平台纪律 + 数据驱动 Kahan 精度路由"
description: "在 910B2C（DAV_2201）上把 AIV 算子 Cube 化时，正确性杀手往往不是算法而是平台纪律：若干平台陷阱会静默产出垃圾或 hang，且 CANN 不报错。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X21: 910B2C Cube 化平台纪律 + 数据驱动 Kahan 精度路由

## 核心思路
在 910B2C（DAV_2201）上把 AIV 算子 Cube 化时，正确性杀手往往不是算法而是**平台纪律**：
四条平台纪律陷阱会静默产出垃圾或 hang，且 CANN 不报错。逐一避坑后，Cube 路线
才能真正落地；对 fp32 L0C 累加必然超差的相消重元素 case，用**数据驱动预扫描**（非 shape
硬编码）按一般性能量规则分流到 Kahan 兜底，保住全量精度。

四条平台纪律（文档未载）：
1. **AIC_ONLY 内核必须显式声明**：`__global__ __aicore__`（无 `__vector__`）的内核被编译为
   MIX 双入口（mix_aic+mix_aiv），AIV 入口执行 cube 指令会产垃圾甚至 hang。修复：内核首行
   `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY)`。
2. **跨 pipe 同步只用 SetFlag/WaitFlag HardEvent**：`PipeBarrier<PIPE_MTE2>` 不建立
   MTE2→V 顺序（DMA 未落地即被读取，输出恒 0）；`MTE2_S` 事件在本平台不存在，GetValue
   标量读前用 `MTE2_MTE3 + V_S` 链替代。
3. **TransDataTo5HD（scatter_vnchwconv_b16）在本平台静默杀死内核**：保留该指令时整个
   内核 no-op（rc=0 无日志，魔数写入都不落地）。替代：标量 UB gather
   （`dst[hw*16+lane]=src[lane*HW+hw]`）→ S_V → 精确 cast round-trip → V_MTE3 → DataCopyPad。
4. **vendor fractal N 序必须用探针判定**：3D conv backprop-filter 的 dw 分形序为
   **(kd, ci1, kh, kw, ci0)**（kd 在 ci1 之外），与 2D forward k 序 (ci1,kh,kw,ci0)
   不同；ci1G=1 或 kd=1 时两序重合会掩盖差异。判别探针：固定 ci1G=2，分别构造 kd=1
   与 kd=3 的输入比较结果即可定序。

## 适用场景
- **算子类型**: 任何在 910B2C 上新增的 Cube（AIC）内核；conv3d/conv2d backward-filter
  及一切 vendor fractal 布局读写的算子
- **瓶颈类型**: Cube 化移植阶段的正确性失败（垃圾值/hang/静默 no-op）；fp32 累加精度
  上限导致的边界 case 超差
- **前提条件**: 无（纪律类）；精度路由需要一次 AIV 预扫描（每 block 统计 max|v|/sum|v|，
  加一次 D2H 同步）

## 实现要点
1. **崩溃 salvage 的数据判读陷阱**：精度对比脚本在 NaN 掩码不匹配时可能提前返回，
   MERE/MARE 停留默认 0.0——"MERE=0 但 FAIL"**不代表**有限值精确。先用全 1 输入探针
   （任何布局排列下结果不变量）确认基本正确性，再信 compare 数值
2. **探针方法**：全 1（布局不变量）→ ramp（k 序）→ one-hot（落点）；单 tile → 多 unit
   → 多 ci1 逐级放大；host 侧分级 dump 工作区定位故障 stage
3. **精度路由规则**（数据驱动，禁止 shape 硬编码）：输入含 inf/NaN → Kahan；
   max|x|·max|g|·S > 5e10（相消误差超 fp32 能力）→ Kahan；fp16 且任一 stride>1
   （边界 tap 累加拓扑 + 紧容差）→ Kahan。fp32 L0C 树序/原子加随机序在强相消元素上
   必然超过 bf16 容差，这是精度上限不是 bug
4. **Kahan 兜底必须移植带补偿的完整实现**（TwoSum/逐行 Kahan/inf-guard），plain-fp32
   重写在紧容差 case 上会显著超差
5. 排查纪律：对每个嫌疑留排除证据（毒药测试预填魔数、将 AIC 核数设为 1 的单核调试、
   相位间 host 全同步等），避免误修

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加
  逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C/workspace 预算审计；诊断类改动先做同码 A/A 噪声带；正确性
  异常时先跑布局不变量探针（全 1/ramp/one-hot），再分级 dump 定位故障 stage。
