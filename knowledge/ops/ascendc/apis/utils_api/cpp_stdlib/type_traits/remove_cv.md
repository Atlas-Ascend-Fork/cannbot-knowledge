---
type: API
title: remove_cv
description: 在程序编译时，对传入的模板参数类型移除const限定符或volatile限定符，或同时移除这两种限定符，可以用于在编译时进行类型转换。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/remove_cv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# remove_cv

在程序编译时，对传入的模板参数类型移除const限定符或volatile限定符，或同时移除这两种限定符，可以用于在编译时进行类型转换。

函数原型：template <typename Tp>；struct remove_cv;

参数：Tp：需要处理的类型，包括基本类型（如int、float等）、复合类型（如数组、指针、引用）、用户自定义类型（如类、结构体等），以及const限定、volatile限定或两者都限定的类型。

返回值：remove_cv是一个结构体，其提供一个嵌套类型type，表示移除const和volatile限定符后的类型。通过remove_cv::type来访问该类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [is_same](is_same.md)（`related`）：配合 IsSame 可在编译期验证 remove_cv_t<T> 是否为预期基础类型。
- [add_cv](add_cv.md)（`same_topic`）：AddCV 是逆向变换，可用于构造后验证恢复基础类型。
- [add_volatile](add_volatile.md)（`same_topic`）：remove_cv说明在程序编译时，对传入的模板参数类型移除const限定符或volatile限定符，或同时移除这两种限定符，可以用于在编译时进行类型转换。
- [remove_const](remove_const.md)（`same_topic`）：remove_const 只去掉 const，remove_cv 同时去掉 const 与 volatile；后者是组合变换，适合需要完全规范化 cv 限定的模板。
- [remove_volatile](remove_volatile.md)（`same_topic`）：RemoveCV 同时移除 const/volatile；只需去 volatile 时本接口更窄。
<!-- cannbot:related:end -->
