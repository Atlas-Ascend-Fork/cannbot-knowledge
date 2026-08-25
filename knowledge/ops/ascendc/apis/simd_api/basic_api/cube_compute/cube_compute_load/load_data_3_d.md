---
type: API
title: LoadData
description: 将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_3D.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LoadData 3D

将数据从L1 Buffer搬运到L0A或L0B Buffer的3D模式搬运接口。支持高维数据的分块搬运，通过LoadData3DParams配置各维度切分参数。3D模式适用于卷积等高维数据场景。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界](../../../../../runbooks/compilation/cube_retcode_0x26_aiv_cube_api.md)（`exemplifies`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界》具体提供“Cube 核直调 kernel 入口 extern "C" __global__ __aicore__ 未标记核类型时 bisheng 按 MIX 模式编译，kernel 被派发到 AIV 核执行 Cube 专属 API（LoadData/Mmad/Fixpipe），AIV 核无 L0A/L0B/L0C 硬件单元，访问 AIC 内部 buffer 越界，触发 aicore exception retCode=0x26 / ErrCode=507015，plog 表现为 aivector error 而非 Cube 侧错误。判别要点：代码用 Cube API、报错却是 aivector error + fixp_error 非零 + scalar access internal buffer of AICore is out of bounds。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [L1/L0 tensor 须用 TPosition 构造非 SetAddr](../../../../../runbooks/compilation/l1_l0_tensor_tposition_setaddr.md)（`exemplifies`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《L1/L0 tensor 须用 TPosition 构造非 SetAddr》具体提供“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [AscL13dFmatrixConfig](../../../c_api/struct/asc_l13d_fmatrix_config.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《AscL13dFmatrixConfig》具体提供“用于设置3D格式搬运接口的Feature map属性参数，包括宽高和四周填充大小。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍](l1_l0_a_b_memory_structure_intro.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》具体提供“为提升数据访问效率和吞吐量，Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [SetFmatrix](../cube_load_aux_config/set_fmatrix.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetFmatrix》具体提供“调用LoadData（卷积数据搬运）时设置FeatureMap的属性描述，包括l1H、l1W、padList和fmatrixMode，需在LoadData接口前调用。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [SetFmatrixBitMode](../cube_load_aux_config/set_fmatrix_bit_mode.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetFmatrixBitMode》具体提供“调用LoadData（卷积数据搬运）时以位域方式设置FeatureMap的属性描述，包括l1H、l1W和padList，需在LoadData接口前调用。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [SetLoadDataBoundary](../cube_load_aux_config/set_load_data_boundary.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetLoadDataBoundary》具体提供“设置LoadData（卷积数据搬运）接口所需的L1 Buffer（A1/B1）边界值，源操作数地址超出边界时从起始地址开始读取。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [SetLoadDataPaddingValue](../cube_load_aux_config/set_load_data_padding_value.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetLoadDataPaddingValue》具体提供“调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [矩阵计算的搬入](cube_compute_load.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《矩阵计算的搬入》具体提供“矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《矩阵计算输入搬运约束》具体提供“具体可见表数据通路和存储层级。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadDataWithStride](load_data_with_stride.md)（`same_topic`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《LoadDataWithStride》具体提供“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入对应内存，支持配置输出矩阵K轴方向偏移量dstStride。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData（BitMode卷积数据搬运）](load_data_3_d_bit_mode.md)（`same_topic`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《LoadData（BitMode卷积数据搬运）》具体提供“LoadData（BitMode卷积数据搬运）用于完成image to column操作，将多维feature map转为二维矩阵。支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（卷积数据搬运）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load3DBitModeParam。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [SetLoadDataRepeat](../cube_load_aux_config/set_load_data_repeat.md)（`same_topic`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadData》说明将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
<!-- cannbot:related:end -->
