---
type: API
title: integer_sequence
description: index_sequence是Ascend C提供的一个类模板，用于生成一个编译时的整数序列，适用于模板元编程。 make_index_sequence是Ascend
  C提供的一个模板，通常使用make_index_sequence创建一个index_sequence类型的对象，用于生成一个从0到N-1的整数序列。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/general_utils/integer_sequence.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# integer_sequence

index_sequence是Ascend C提供的一个类模板，用于生成一个编译时的整数序列，适用于模板元编程。

make_index_sequence是Ascend C提供的一个模板，通常使用make_index_sequence创建一个index_sequence类型的对象，用于生成一个从0到N-1的整数序列。

函数原型：template<size_t... Idx>；using index_sequence = IntegerSequence<size_t, Idx...>;；template<size_t N> 等4种重载

参数：...Idx：表示序列的形参包。<br><br>size_t，在64位系统中为long unsigned int，非64位系统中为unsigned int。；N：生成的整数序列的大小。<br><br>size_t，在64位系统中为long unsigned int，非64位系统中为unsigned int。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   N的范围为[0, 64]。
-   index_sequence作为序列，长度最大为64。
