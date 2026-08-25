---
type: API
title: Layout（辅助数据结构）
description: Layout 辅助数据结构用于描述张量数据排布，提供构造函数、Shape/Stride 操作与 MakeLayout 等接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/Layout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# Layout（辅助数据结构）

Layout 用于描述张量数据在内存中的排布方式，包含 Shape、Stride 等核心属性。
提供构造函数创建 Layout 对象，GetShape/GetStride 查询排布信息，MakeShape/MakeStride/MakeLayout 构建排布对象，以及 is_layout 进行类型判断。
支持运算符重载，便于排布对象的比较与赋值操作。

<!-- cannbot:related:start -->
## 相关

- [GetShape](get_shape.md)（`related`）：GetShape 提取 Layout 的逻辑维度，与 GetStride 联合才能完整解释布局。
- [GetStride](get_stride.md)（`related`）：GetStride 提取每个维度的内存步长，是 Layout 从坐标计算偏移所需的另一半信息。
- [Coordinate](../coordinate/coordinate.md)（`same_topic`）：Coordinate 与《Layout（辅助数据结构）》的实质衔接是：Coordinate 由 MakeCoord 构造，并由 Crd2Idx 结合 Layout 的 shape/stride 转成线性索引。
- [Layout构造函数](layout_constructor.md)（`same_topic`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《Layout（辅助数据结构）》说明Layout 辅助数据结构用于描述张量数据排布，提供构造函数、Shape/Stride 操作与 MakeLayout 等接口。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout简介](layout_intro.md)（`same_topic`）：简介解释 Layout 通过编译期 Shape 与 Stride 完成坐标到线性地址映射，补足对象总览背后的内存语义。
- [is_layout](is_layout.md)（`same_topic`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《Layout（辅助数据结构）》说明Layout 辅助数据结构用于描述张量数据排布，提供构造函数、Shape/Stride 操作与 MakeLayout 等接口。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
<!-- cannbot:related:end -->
