# 数据结构(TensorAPI，试验特性)

- [数据结构(TensorAPI，试验特性)](data_structure_tensor_api.md)：TensorAPI（试验特性）数据结构总览，涵盖内置数据类型、Layout 与 Tensor 相关数据结构及工具接口。
- [Layout数据结构](layout_structure/index.md)：需要包含的头文件为：#include "tensor_api/tensor.h"。 Capacity用于计算Layout所需的实际内存容量。 与Size（有效元素个数）不同，Capacity包含了因非连续步长导致的无效数据区域。对于连...
- [Tensor数据结构](tensor_structure/index.md)：需要包含的头文件为：#include "tensor_api/tensor.h"。 MakeMemPtr用于构造带物理存储位置标记和数据类型信息的内存指针适配器HardwareMemPtr，支持的物理位置如下表所示。
- [utils](utils/index.md)：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetLayoutPattern用于从Layout类型中提取其LayoutPattern类型信息。
