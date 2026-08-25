---
type: API
title: Utils APIget
description: get的作用是从tuple容器中提取指定位置的元素。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/container_functions/get.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# get

get的作用是从tuple容器中提取指定位置的元素。

函数原型：template <size_t N, typename ...Tps>；__aicore__ inline typename tuple_element<N, tuple<Tps...> >::type& get(tuple<Tps...>& t) noexcept；template <size_t N, typename ...Tps> 等8种重载

参数：N：N是一个编译时常量，代表要提取元素的索引。索引从0开始，取值范围为[0, 64)。；Tps...：Tps...为传入tuple的模板参数包，tuple参数个数范围为(0, 64]。<br><br>Ascend 950PR/Ascend 950DT，支持的数据类型为：bool、int4b_t、int8_t、uint8_t、fp8_e8m0_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、LocalTensor、GlobalTensor。<br><br>Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：bool、int4b_t、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、LocalTensor、GlobalTensor。<br><br>Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为：bool、int4b_t、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、LocalTensor、GlobalTensor。；t：t是tuple对象，可以是左值引用、常量左值引用或右值引用。

返回值：tuple对象中对应位置的元素。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：get函数仅支持const和constexpr常量索引，索引的取值范围为[0, 64)。

<!-- cannbot:related:start -->
## 相关

- [Tuple](tuple.md)（`related`）：get 以编译期常量索引读取 tuple 元素，是 tuple 创建后的直接访问操作。
- [make_tuple](make_tuple.md)（`same_topic`）：“make_tuple”处理make_tuple是一个实用的函数模板，其作用在于便捷地创建tuple对象。它可以自动推断元素的类型，使代码更简洁，也可以构造元素列表。；“Utils APIget”明确get的作用是从tuple容器中提取指定位置的元素。。实质衔接：make_tuple 构造 Tuple，get 按位置读取元素，二者构成同一容器对象的直接生产/消费关系。
<!-- cannbot:related:end -->
