# Tensor数据结构

- [MakeMemPtr](make_mem_ptr.md)：需要包含的头文件为：#include "tensor_api/tensor.h"。 MakeMemPtr用于构造带物理存储位置标记和数据类型信息的内存指针适配器HardwareMemPtr，支持的物理位置如下表所示。
- [MakeTensor](make_tensor.md)：将内存指针与布局对象绑定生成带完整类型信息的Tensor对象，根据物理位置自动推导返回GlobalTensor或LocalTensor。
- [Pointer（基础API）](pointer.md)：Pointer定义指针迭代器，用于遍历和访问张量数据。
- [Slice（基础API）](slice.md)：需要包含的头文件为：#include "tensor_api/tensor.h"。 Slice用于从张量指定坐标处切出一个子张量。根据输入的起始坐标coord和切片描述信息info，计算新的起始存储位置，并构造对应的子张量，子张量保持与原张量相同的存储位置类型。
- [Tensor](tensor.md)：将内存访问引擎Engine与布局Layout绑定，分为GlobalTensor和LocalTensor两种，公共接口由BaseTensor提供。
- [Tensor数据结构](tensor_structure.md)：TensorAPI Tensor 数据结构集，包含 Tensor、Pointer、ViewEngine 及 MakeTensor、Slice 等相关接口。
- [ViewEngine](view_engine.md)：ViewEngine是Tensor API中的视图引擎，负责持有一个指针对象Iterator，通过Begin()返回这段视图的起始位置。在LocalTensor中，ViewEngine和Layout一起组成一个Tensor的视图。
