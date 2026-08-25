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
