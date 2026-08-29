---
type: API
title: NZ2ND
description: 矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/NZ2ND.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NZ2ND

矩阵搬出时将 NZ 格式矩阵转换为 ND 格式矩阵。通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。

参数：ndNum 为 ND 矩阵个数、mSize/nSize 为矩阵 M/N 方向维度、srcStride 为源 NZ 矩阵不同 Z 分形列间隔（单位 C0_Size）、dstStride 为目的 ND 矩阵不同行间隔（单位 element）、srcNdStride 为不同 NZ 矩阵间隔（单位 16×C0_Size）、dstNdStride 为不同 ND 矩阵间隔（单位 element）。约束：不能与 Channel Split/Merge 同时开启；目标操作数地址不能重叠。

<!-- cannbot:related:start -->
## 相关

- [L0C Buffer到UB双目标模式](l0_c_to_ub_dual_target_mode.md)（`related`）：双目标模式仅支持在L0C Buffer到UB通路，普通搬运模式（NZ2NZ）或NZ2ND搬运场景下使用，不支持随路功能场景。；矩阵搬出时将 NZ 格式矩阵转换为 ND 格式矩阵。通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。。双目标卡明确允许 NZ2ND 场景并规定 M/N 切分约束，NZ2ND 卡补齐行主序开关、stride 与目标不重叠合同。
- [SetFixpipeNz2ndFlag](../cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`related`）：焦点卡通过“DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路 NZ2ND 格式转换时，设置格式转换配置。”定义配置入口，候选卡说明“通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。”；两卡直接闭合 NZ2ND 功能的使能与步幅参数合同。
- [卷积格式转换](convolution_format_conversion.md)（`related`）：在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过NZ2ND能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：；矩阵搬出时将 NZ 格式矩阵转换为 ND 格式矩阵。通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。。格式转换卡指定 Fixpipe 的 NZ2ND 能力输出 NHWC，API 卡补齐行主序开关、stride 和目标不重叠合同。
<!-- cannbot:related:end -->
