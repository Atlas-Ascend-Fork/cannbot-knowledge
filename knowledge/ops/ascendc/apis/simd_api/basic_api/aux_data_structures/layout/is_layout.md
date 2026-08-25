---
type: API
title: is_layout
description: 判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/is_layout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# IsLayout

判断两个Layout是否相等。比较shape、stride和format等属性。函数原型：bool IsLayout(const Layout& layout1, const Layout& layout2)。参数为两个待比较的Layout。返回true表示相等，false表示不等。用于验证Layout一致性。

<!-- cannbot:related:start -->
## 相关

- [Layout构造函数](layout_constructor.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout简介](layout_intro.md)（`related`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《Layout简介》说明Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
- [MakeLayout](make_layout.md)（`related`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《MakeLayout》说明将传入的Shape和Stride数据打包成Layout数据结构。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Layout（辅助数据结构）](layout.md)（`same_topic`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《Layout（辅助数据结构）》说明Layout 辅助数据结构用于描述张量数据排布，提供构造函数、Shape/Stride 操作与 MakeLayout 等接口。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
- [SetLayout](../tensor_trait/set_layout.md)（`same_topic`）：is_layout说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。
- [layout](layout1.md)（`same_topic`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《layout》说明获取Layout实例化对象。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
<!-- cannbot:related:end -->
