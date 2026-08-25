---
type: API
title: L0C Buffer到UB双目标模式
description: 同一AI Core内有一个Cube Core和两个Vector Core，当启用双目标模式控制时，L0C Buffer中的M×N矩阵将被分成两半，并同时分别写入两个Vector
  Core各自的UB中，其中前半部分写入SUB BLOCK0，后半部分写入SUB BLOCK1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/L0C_to_UB_dual_target_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L0C Buffer到UB双目标模式

## 特性说明

同一AI Core内有一个Cube Core和两个Vector Core，当启用双目标模式控制时，L0C Buffer中的M×N矩阵将被分成两半，并同时分别写入两个Vector Core各自的UB中，其中前半部分写入SUB BLOCK0，后半部分写入SUB BLOCK1。

- 双目标模式（M维度）：按M维度拆分成形状为M / 2 * N的两个矩阵，分别写入两个UB。
- 双目标模式（N维度）：按N维度拆分成形状为M * N / 2的两个矩阵，分别写入两个UB。

## 特性约束

- 双目标模式仅支持在L0C Buffer到UB通路，普通搬运模式（NZ2NZ）或NZ2ND搬运场景下使用，不支持随路功能场景。
- 按M维度拆分时M必须为2的倍数。
- 按N维度拆分时N须为32的倍数。

## 使用示例

在普通搬运模式模式下启用双目标模式如下图所示，分为按M维度拆分和按N维度拆分，按M维度拆分M必须为2的倍数，按N维度拆分N必须为32的倍数：

N方向切分：

- nSize = 32，表示源NZ矩阵中待搬运矩阵在N方向上的大小为32个元素。
- mSize = 48，表示源NZ矩阵中待搬运矩阵在M方向上的大小48个元素。
- srcStride = 64，表示源NZ矩阵中待搬运矩阵相邻Z排布的起始地址偏移，即下图中第一个块Z排布矩阵的起始地址与第二个Z排布矩阵的起始地址之间的间隔为64 * C0_Size。
- dstStride = 64 * C0，表示目的NZ矩阵中相邻Z排布的起始地址偏移，即下图中UB0中Z排布的起始地址与UB1中Z排布的起始地址之间的间隔为64 * 16个元素。

M方向切分：

- nSize = 32，表示源NZ矩阵中待搬运矩阵在N方向上的大小为32个元素。
- mSize = 24，表示源NZ矩阵中待搬运矩阵在M方向上的大小为24个元素。
- srcStride = 64，表示源NZ矩阵中待搬运矩阵相邻Z排布的起始地址偏移，即下图中第一个块Z排布矩阵的起始地址与第二个Z排布矩阵的起始地址之间的间隔为64 * C0_Size。
- dstStride = 40 * C0，表示目的NZ矩阵中相邻Z排布的起始地址偏移，即下图中UB0（或UB1）中第一个Z排布的起始地址与第二个Z排布的起始地址之间的间隔为40 * 16个元素。

**图1** NZ2NZ双目标搬运模式设置示意图

在NZ2ND模式下启用双目标模式如下图所示，分为按M维度拆分和按N维度拆分，按M维度拆分M必须为2的倍数，按N维度拆分N必须为2的倍数：

- ndNum = 2，表示源NZ矩阵的数目为2。图中红框区域为矩阵1，蓝框区域为矩阵2。
- nSize = 32，表示源NZ矩阵（图中红框区域或蓝框区域）在N方向上的大小为32个元素。
- mSize = 48，表示源NZ矩阵在M方向上的大小为48个元素。
- srcStride = 64，表示源NZ矩阵中相邻Z排布的起始地址偏移，即下图红框区域中左侧浅色Z排布矩阵的起始地址与右侧深色Z排布矩阵的起始地址之间的间隔为64 * C0_Size。
- dstStride = 64，表示目的ND矩阵每一行中的元素个数为64。
- ndNum = 2, 表示源NZ矩阵的数目。
- srcNdStride = 240 ,  表示不同NZ矩阵起始地址之间的间隔为240 * C0_Size。
- dstNdStride  = 4096，表示目的相邻ND矩阵起始地址之间的偏移为4096个元素。

**图2** NZ2ND参数双搬入模式设置示意图

完整样例可参考fixpipe_l0c2ub。

<!-- cannbot:related:start -->
## 相关

- [L0C Buffer到Unified Buffer双目标模式](../../cube_compute_tensor_api/cube_store_key_features/l0c_to_ub_dual_dst.md)（`related`）：TensorAPI 卡描述相同 L0C→双 UB 拆分能力，可对照 ISASI 与 TensorAPI 的配置入口。
- [DataCopy（L0C Buffer到UB数据搬运）](../cube_compute_store/data_copy_l0_c_to_ub.md)（`same_topic`）：DataCopy（L0C Buffer到UB数据搬运） 与《L0C Buffer到UB双目标模式》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
- [FixpipeL0CToUB](../cube_compute_store/fixpipe_l0_c_to_ub.md)（`same_topic`）：FixpipeL0CToUB 与《L0C Buffer到UB双目标模式》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
<!-- cannbot:related:end -->
