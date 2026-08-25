---
type: API
title: is_pointer
description: 在程序编译时，判断一个类型是否为指针类型，可以用于在编译时进行类型检查和条件处理。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_pointer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_pointer

在程序编译时，判断一个类型是否为指针类型，可以用于在编译时进行类型检查和条件处理。

函数原型：template <typename Tp>；struct is_pointer;

参数：Tp：需要检测的类型，包括基本类型（如int、float等）、复合类型（如数组、函数类型）、用户自定义类型（如类、结构体等），以及指针类型本身。

返回值：is_pointer的静态常量成员value用于获取返回的布尔值，is_pointer::value取值如下：

-   true：Tp是指针类型。
-   false：Tp不是指针类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Conditional](conditional.md)（`related`）：is_pointer 与《Conditional》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [EnableIf](enable_if.md)（`related`）：is_pointer 与《EnableIf》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [is_convertible](is_convertible.md)（`related`）：is_pointer 与《is_convertible》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [is_same](is_same.md)（`related`）：is_pointer 与《is_same》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [add_pointer](add_pointer.md)（`same_topic`）：add_pointer：add_pointer与remove_pointer构成互逆类型变换，is_pointer可在模板分支中验证变换结果；其他不相关 trait不连接。 目标卡《is_pointer》补充：在程序编译时，判断一个类型是否为指针类型，可以用于在编译时进行类型检查和条件处理。
- [remove_pointer](remove_pointer.md)（`same_topic`）：is_pointer 与《remove_pointer》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
<!-- cannbot:related:end -->
