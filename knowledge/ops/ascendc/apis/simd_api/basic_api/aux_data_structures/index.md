# 辅助数据结构

- [BinaryRepeatParams](binary_repeat_params.md)：BinaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
- [Coordinate](coordinate/index.md)：共 3 张知识卡（如 Coordinate简介、Crd2Idx、MakeCoord）。
- [Layout](layout/index.md)：共 10 张知识卡（如 GetShape、GetStride、is_layout 等）。
- [ListTensorDesc](list_tensor_desc.md)：ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !
- [ShapeInfo（辅助数据结构）](shape_info.md)：ShapeInfo用来存放LocalTensor或GlobalTensor的shape信息。
- [TPosition](t_position.md)：Ascend C管理不同层级物理内存的抽象逻辑位置，代替片上物理存储概念，包括矢量编程和矩阵编程所需的各类存储位置。
- [TensorDesc](tensor_desc/index.md)：共 8 张知识卡（如 构造和析构函数、GetDataObj、GetDataPtr 等）。
- [TensorTrait](tensor_trait/index.md)：共 7 张知识卡（如 GetLayout、is_tensorTrait、MakeTensorTrait 等）。
- [UnaryRepeatParams](unary_repeat_params.md)：UnaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。

- [DataCopyEnhancedParams](data_copy_enhanced_params.md)：DataCopyEnhancedParams 是 L0C→UB 搬运的增强参数结构体，配置搬运分形模式 blockMode、随路量化 deqScale/deqValue/deqTensorAddr、随路 ReLU 与 padding 模式。
- [DataCopyExtParams](data_copy_ext_params.md)：DataCopyExtParams 是 DataCopyPad 等扩展搬运的参数结构体，单位按搬运方向不对称：GM→UB 时 blockLen/srcStride 以字节计、dstStride 以 32B DataBlock 计；UB→GM 时 srcStride 以 32B DataBlock 计、dstStride 以字节计；blockLen 两个方向都以字节计。
- [DataCopyParams](data_copy_params.md)：DataCopyParams 是高维切分搬运的参数结构体，用 blockCount/blockLen 描述搬运块数与每块长度（单位 32B DataBlock），用 srcGap/dstGap 描述相邻数据块间隔，覆盖连续与非连续搬运。
- [FixpipeParams](fixpipe_params.md)：FixpipeParams 是 Cube 结果搬出指令 Fixpipe 的参数族，包含 V220、Arch3510/C310 与模板三种形态，字段单位与量化配置随形态和产品不同。
- [LoadData2DParams](load_data_2_d_params.md)：LoadData2DParams 是 LoadData 2D（L1→L0A/L0B）的参数结构体，以 512 字节分形为单位配置起始分形、迭代次数、源/目的分形间隔、转置与地址更新方向。
- [LoadData3DParamsV2Pro](load_data_3_d_params_v2_pro.md)：LoadData3DParamsV2Pro 是 LoadData 卷积搬运 v2 Pro 的参数结构体，用 extConfig/filterConfig 两个位打包参数表达窗口起点、扩展量、filter 尺寸、步长与膨胀。
- [MmadParams](mmad_params.md)：MmadParams 是 Cube 矩阵乘加指令 Mmad 的参数结构体，给出 m/n/k 几何尺寸，并配置 unitFlag 指令并行、kDirectionAlign 对齐方式与 C 矩阵初值来源。
- [Nd2NzParams](nd2_nz_params.md)：Nd2NzParams 是 ND→NZ 布局转换搬运的参数结构体，描述源 ND 矩阵个数/行数/列数、相邻矩阵间隔，以及目的 NZ 矩阵在 C0、N、矩阵三个方向的步长。
