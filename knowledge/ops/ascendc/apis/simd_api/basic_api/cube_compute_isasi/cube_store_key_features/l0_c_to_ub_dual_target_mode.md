---
type: API
title: L0C Buffer到UB双目标模式
description: 同一AI Core内有一个Cube Core和两个Vector Core，当启用双目标模式控制时，L0C Buffer中的M×N矩阵将被分成两半，并同时分别写入两个Vector
  Core各自的UB中，其中前半部分写入SUB BLOCK0，后半部分写入SUB BLOCK1。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/L0C_to_UB_dual_target_mode.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# L0C Buffer到UB双目标模式

## 特性说明

同一AI Core内有一个Cube Core和两个Vector Core，当启用双目标模式控制时，L0C Buffer中的M×N矩阵将被分成两半，并同时分别写入两个Vector Core各自的Unified Buffer（UB）中，其中前半部分写入SUB BLOCK0，后半部分写入SUB BLOCK1。

- 双目标模式（M维度）：按M维度拆分成形状为M / 2 \* N的两个矩阵，分别写入两个UB。
- 双目标模式（N维度）：按N维度拆分成形状为M \* N / 2的两个矩阵，分别写入两个UB。

## 特性约束

- 双目标模式仅支持在L0C Buffer到UB通路，普通搬运模式（NZ2NZ）或NZ2ND搬运场景下使用，不支持随路功能场景。
- 按M维度拆分时M必须为2的倍数。
- 按N维度拆分时N须为32的倍数。

## 使用示例

在普通搬运模式模式下启用双目标模式如下图所示，分为按M维度拆分和按N维度拆分，按M维度拆分M必须为2的倍数，按N维度拆分N必须为32的倍数：

N方向切分：

- nSize = 32，表示源NZ矩阵中待搬运矩阵在N方向上的大小为32个元素。
- mSize = 48，表示源NZ矩阵中待搬运矩阵在M方向上的大小48个元素。
- srcStride = 64，表示源NZ矩阵中待搬运矩阵相邻Z排布的起始地址偏移，即下图中第一个块Z排布矩阵的起始地址与第二个Z排布矩阵的起始地址之间的间隔为64 \* C0\_Size。
- dstStride = 64 \* C0，表示目的NZ矩阵中相邻Z排布的起始地址偏移，即下图中UB0中Z排布的起始地址与UB1中Z排布的起始地址之间的间隔为64 \* 16个元素。

M方向切分：

- nSize = 32，表示源NZ矩阵中待搬运矩阵在N方向上的大小为32个元素。
- mSize = 24，表示源NZ矩阵中待搬运矩阵在M方向上的大小为24个元素。
- srcStride = 64，表示源NZ矩阵中待搬运矩阵相邻Z排布的起始地址偏移，即下图中第一个块Z排布矩阵的起始地址与第二个Z排布矩阵的起始地址之间的间隔为64 \* C0\_Size。
- dstStride = 40 \* C0，表示目的NZ矩阵中相邻Z排布的起始地址偏移，即下图中UB0（或UB1）中第一个Z排布的起始地址与第二个Z排布的起始地址之间的间隔为40 \* 16个元素。

**图1** NZ2NZ双目标搬运模式设置示意图<a name="fig1386816164556"></a>  

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/nz2nz_l0c2ub_dual_dst.png)

在NZ2ND模式下启用双目标模式如下图所示，分为按M维度拆分和按N维度拆分，按M维度拆分M必须为2的倍数，按N维度拆分N必须为2的倍数：

- ndNum = 2，表示源NZ矩阵的数目为2。图中红框区域为矩阵1，蓝框区域为矩阵2。
- nSize = 32，表示源NZ矩阵（图中红框区域或蓝框区域）在N方向上的大小为32个元素。
- mSize = 48，表示源NZ矩阵在M方向上的大小为48个元素。
- srcStride = 64，表示源NZ矩阵中相邻Z排布的起始地址偏移，即下图红框区域中左侧浅色Z排布矩阵的起始地址与右侧深色Z排布矩阵的起始地址之间的间隔为64 \* C0\_Size。
- dstStride = 64，表示目的ND矩阵每一行中的元素个数为64。
- ndNum = 2, 表示源NZ矩阵的数目。
- srcNdStride = 240 ,  表示不同NZ矩阵起始地址之间的间隔为240 \* C0\_Size。
- dstNdStride  = 4096，表示目的相邻ND矩阵起始地址之间的偏移为4096个元素。

**图2** NZ2ND参数双搬入模式设置示意图<a name="fig715654093716"></a>  

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/nz2nd_l0c2ub_dual_dst.png)

完整样例可参考[fixpipe\_l0c2ub](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/03_matrix_compute/fixpipe_l0c2ub)。


<!-- cannbot:related:start -->
## 相关

- [NZ2ND](nz2_nd.md)（`related`）：双目标模式仅支持在L0C Buffer到UB通路，普通搬运模式（NZ2NZ）或NZ2ND搬运场景下使用，不支持随路功能场景。；矩阵搬出时将 NZ 格式矩阵转换为 ND 格式矩阵。通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。。双目标卡明确允许 NZ2ND 场景并规定 M/N 切分约束，NZ2ND 卡补齐行主序开关、stride 与目标不重叠合同。
- [L0C Buffer到Unified Buffer双目标模式](../../../tensor_api/matrix_compute/cube_store_key_features/l0c_to_ub_dual_dst.md)（`same_topic`）：双目标模式仅支持L0C Buffer到Unified Buffer通路；双目标模式仅支持在L0C Buffer到UB通路。两卡描述 Tensor API 与基础 Cube API 中同一 L0C→双 UB 拆分能力，并给出相同的通路与 M/N 切分约束；对照可核验两种编程入口的双目标行为。
<!-- cannbot:related:end -->
