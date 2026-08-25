---
type: API
title: 卷积格式转换
description: 在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过NZ2ND能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/convolution_format_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 卷积格式转换

在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过NZ2ND能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：

**图1** NC1HWC0转换为NHWC格式

特别的，针对Ascend 950PR/Ascend 950DT产品，还支持Fixpipe指令通过NZ2DN能力，将L0C Buffer上数据转为NCHW格式输出。转换示意图如下所示：

**图2**  NC1HWC0转换为NCHW格式

<!-- cannbot:related:start -->
## 相关

- [AIV核上的ND2NZ格式转换](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/aiv_nd2nz_conversion.md)（`explains`）：焦点处理Cube 搬出阶段的 NZ/ND 格式转换；AIV核上的ND2NZ格式转换正文界定“矩阵乘算子中输入矩阵内轴非256字节对齐时，在AIV核上完成ND到NZ格式转换以提升随路搬运效率”。候选给出 ND2NZ 实现、Fixpipe 开关与 NZ 分形布局，能执行并验证焦点所述格式转换。
- [NZ2ND](nz2_nd.md)（`related`）：“NZ2ND”定义：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。；“卷积格式转换”定义：在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过NZ2ND能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：。实质衔接：NZ2ND 是 L0C 搬出的格式转换能力；卷积 NHWC 输出复用该能力，实际 DataCopy 前需通过 Fixpipe NZ2ND 标志配置。
- [关键分形格式详解](../cube_compute_fractal_intro/key_fractal_format_details.md)（`related`）：焦点处理Cube 搬出阶段的 NZ/ND 格式转换；关键分形格式详解正文界定“矩阵分形存储格式是对多维Tensor在内存中数据排布格式的描述”。候选给出 ND2NZ 实现、Fixpipe 开关与 NZ 分形布局，能执行并验证焦点所述格式转换。
- [辅助矩阵分形格式详解](../cube_compute_fractal_intro/aux_cube_fractal_format_details.md)（`related`）：焦点处理Cube 搬出阶段的 NZ/ND 格式转换；辅助矩阵分形格式详解正文界定“针对Ascend 950PR/Ascend 950DT产品：”。候选给出 ND2NZ 实现、Fixpipe 开关与 NZ 分形布局，能执行并验证焦点所述格式转换。
- [SetFixpipeNz2ndFlag](../cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`same_topic`）：焦点处理Cube 搬出阶段的 NZ/ND 格式转换；SetFixpipeNz2ndFlag正文界定“DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置”。候选给出 ND2NZ 实现、Fixpipe 开关与 NZ 分形布局，能执行并验证焦点所述格式转换。
<!-- cannbot:related:end -->
