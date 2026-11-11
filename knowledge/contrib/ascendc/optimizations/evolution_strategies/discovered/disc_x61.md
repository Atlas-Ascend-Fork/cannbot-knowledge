---
type: Optimization
title: "X61: 硬件转置指令替代 vgather 通路（v4dtrans + strided UB copy 交织）"
description: "当数据重排的 vgather 吞吐被每 repeat 元素数上限钉在发射率墙上时，检查芯片 platform_config 的 Intrinsic 清单寻找专用转置指令；将 gather 源布局重排为 [C,HW] tile 形态后，用 Transpose 与 strided UB->UB DataCopy 交织替代 vgather 微指令，实现无逐元素 gather 的布局变换。"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X61: 硬件转置指令替代 vgather 通路（v4dtrans + strided UB copy 交织）

## 核心思路
当数据重排的 vgather 吞吐被"每 repeat 上限元素数"钉死在发射率墙（如 m200 Gather
128 half/repeat，32 条微指令/窗口不可再压）时，检查芯片 platform_config 的
**Intrinsic 清单**寻找专用转置指令：310P3 无 v4trans 但**有 v4dtrans/vtranspose**。
`Transpose(dst, src, tmp, TransposeParamsExt{NCHW2NHWC})` 每次完成一个
[C,HW] 行主序 tile 的 [HW,C] 转置（其几何为 dst[hw*C+c]=src[c*HW+hw]）。把 gather
源布局重排为 [C,HW] tile 形态后，每窗（或每 tile）用 **2 次 Transpose（两路分量）+
2 次 strided UB->UB DataCopy（行交织到目标布局）** 替代全部 vgather 微指令——每窗
4 个发射单元替换 32 条微指令。UB->UB DataCopy 走 V-pipe copy_ubuf_to_ubuf
（dav_m200 支持，blockCount≤4095），同样不是 MTE 事务。

## 适用场景
- gather/转置主导的布局重排（ND→NZ/fractal、量化 nibble 分离转置、解交织）在
  "Gatherb NOT_SUPPORT + Gather 元素率上限"双卡死的老架构（m200/310P 等）
- 症状：Vector busy 高、每窗口固定数量的 gather 微指令、发射率受限
- 前置动作：grep platform_config ini 的 Intrinsic_v*trans 清单——v4dtrans/
  vtranspose 支持则此路通；v4trans 不支持不代表没有替代指令

## 实现要点
1. **几何验证**：v4dtrans 在 310P 官方文档无几何记录。可由已有 Transpose 参考实现
   与 Brcb 内 8x8 v4dtrans 调用交叉推导，上板首测做 bit-exact 验证
2. **双路交织**：lo/hi（或奇/偶行）两路分量各做一次 Transpose 到临时 tile（E/H），
   再用 2 次 strided DataCopy{32 块, 4 单位=128B, srcStride=0, dstStride=4} 交织到
   目标行布局——纯 bit 搬运，无数值变换
3. **暂存复用**：E/H 覆盖流水线上"此刻已死"的 buffer（如抽取完成后、下次装载前的
   临时槽），不新增 UB；offset 表随 gather 一并删除，进一步减少 UB 占用
4. **同步**：Transpose 与 copy 都在 V-pipe，用 PIPE_V 屏障序；无新跨引擎边

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），对比父变体与变体；用全量精度
  门禁与逐 bit/逐元素对比确认布局变换语义未变。
- 首版先用已知几何的输入验证转置地址映射；容量类改动先做 UB/L1/L0C 预算审计，
  确认临时 tile 复用与流水线驻留不越界。
