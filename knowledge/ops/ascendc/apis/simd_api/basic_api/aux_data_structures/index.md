# 辅助数据结构

- [BinaryRepeatParams](binary_repeat_params.md)：BinaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
- [Coordinate](coordinate/index.md)：Coordinate本质上是一个元组（tuple），用于表示张量在不同维度的位置信息，即坐标值。Coordinate（坐标）和Layout（布局）、Index（内存位置索引）之间存在紧密的关联：
- [Layout](layout/index.md)：返回描述张量形状的Shape对象。
- [ListTensorDesc](list_tensor_desc.md)：ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !
- [ShapeInfo（辅助数据结构）](shape_info.md)：ShapeInfo用来存放LocalTensor或GlobalTensor的shape信息。
- [TPosition](t_position.md)：Ascend C管理不同层级物理内存的抽象逻辑位置，代替片上物理存储概念，包括矢量编程和矩阵编程所需的各类存储位置。
- [TensorDesc](tensor_desc/index.md)：创建与释放TensorDesc对象。
- [TensorTrait](tensor_trait/index.md)：获取Layout实例化对象。
- [UnaryRepeatParams](unary_repeat_params.md)：UnaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
