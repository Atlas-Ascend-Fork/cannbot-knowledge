# 辅助数据结构

- [辅助数据结构](aux_data_structures.md)：AscendC 矢量计算基础 API 的辅助数据结构总览，涵盖 Coordinate、Layout、TensorTrait、TensorDesc 等类型与参数结构。
- [BinaryRepeatParams](binary_repeat_params.md)：BinaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
- [complex32/complex64](complex32_complex64.md)：复数类型定义，complex32 实部虚部为 half、位宽 32 位，complex64 实部虚部为 float、位宽 64 位，仅 Ascend 950PR/950DT 支持。
- [Coordinate](coordinate/index.md)：Coordinate 辅助数据结构用于描述张量坐标，提供 MakeCoord 构造与 Crd2Idx 坐标到索引转换接口。
- [Layout（辅助数据结构）](layout/index.md)：返回描述张量形状的Shape对象。
- [ListTensorDesc](list_tensor_desc.md)：ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !
- [ShapeInfo（辅助数据结构）](shape_info.md)：ShapeInfo用来存放LocalTensor或GlobalTensor的shape信息。
- [TPosition](t_position.md)：Ascend C管理不同层级物理内存的抽象逻辑位置，代替片上物理存储概念，包括矢量编程和矩阵编程所需的各类存储位置。
- [TensorDesc](tensor_desc/index.md)：创建与释放TensorDesc对象。
- [TensorTrait](tensor_trait/index.md)：获取Layout实例化对象。
- [UnaryRepeatParams](unary_repeat_params.md)：UnaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
