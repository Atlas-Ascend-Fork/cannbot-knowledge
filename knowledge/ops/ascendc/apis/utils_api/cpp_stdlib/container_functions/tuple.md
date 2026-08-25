---
type: API
title: Tuple
description: 允许存储多个不同类型元素的容器，支持函数多返回值、异构数据存储、参数分组和模板元编程等场景，实例化深度最大64。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/container_functions/tuple.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# tuple

在C++中，tuple是一个功能强大的容器，它允许存储多个不同类型的元素。具体使用场景如下：

-   当一个函数需要返回多个不同类型的值时，使用tuple是一个很好的选择。它避免了创建结构体或类来封装多个返回值，尤其是在不需要为这些返回值创建单独的类型时。
-   当需要存储不同类型的数据，可以使用tuple来存储异构元素。例如，存储数据的查询结果，其中包含不同类型的字段。
-   在函数调用中，当需要传递多个不同类型的参数，但又不想为它们创建结构体时，可以使用tuple对这些参数分组。
-   在模板元编程中，tuple可以作为类型列表，存储多个类型信息。
-   当程序需要在不同阶段存储和传递多个状态信息时，可以使用tuple将这些状态统一存储，便于管理。
-   在一些泛型算法中，可以使用tuple存储计算结果或中间结果。
-   在模板元编程中，可以使用tuple存储和展开参数包。

以下是tuple的构造函数说明：

-   默认构造函数：创建一个空的元组。
-   初始化列表构造函数：直接在创建对象时提供元素的值。
-   复制构造函数：用来复制一个已有的元组。

函数原型：template <typename Tp, typename ...Tps>；class tuple<Tp, Tps...> : public tuple<Tps...>；{ 等10种重载

参数：Tps...：表示输入类型的形参包，参数个数范围为[0，64]。<br><br>Ascend 950PR/Ascend 950DT，支持的数据类型为：bool、int4b_t、int8_t、uint8_t、fp8_e8m0_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、LocalTensor、GlobalTensor。<br><br>Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：bool、int4b_t、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、LocalTensor、GlobalTensor。<br><br>Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为：bool、int4b_t、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、LocalTensor、GlobalTensor。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   tuple实例化深度为64，即支持64个元素以内的数据类型的聚合。
-   构造函数为初始化列表时，列表中的数据应同为左值或右值，不可混用，初始化列表中的元素个数和类型，必须与tuple定义的元素个数和类型严格匹配。
-   不支持数组等可变长度的数据类型。
-   不支持隐式转换构造函数。

<!-- cannbot:related:start -->
## 相关

- [Utils APIget](get.md)（`related`）：get 以编译期常量索引读取 tuple 元素，是 tuple 创建后的直接访问操作。
- [容器函数](container_functions.md)（`related`）：容器函数总览定义 tuple 的异构聚合、64 元素上限和限制，并导航到构造与访问接口。
- [make_tuple](make_tuple.md)（`same_topic`）：“make_tuple”处理make_tuple是一个实用的函数模板，其作用在于便捷地创建tuple对象。它可以自动推断元素的类型，使代码更简洁，也可以构造元素列表。；“Tuple”明确允许存储多个不同类型元素的容器，支持函数多返回值、异构数据存储、参数分组和模板元编程等场景，实例化深度最大64。。实质衔接：make_tuple 构造 Tuple，get 按位置读取元素，二者构成同一容器对象的直接生产/消费关系。
<!-- cannbot:related:end -->
