---
type: API
title: is_same
description: is_same是定义在头文件里的一个类型特征工具，它能够在程序编译时判断两个类型是否完全相同。本接口可应用在模板元编程、类型检查、条件编译等场景，用于在编译阶段确定类型信息，避免运行时可能出现的类型不匹配问题。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_same.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_same

is_same是定义在头文件里的一个类型特征工具，它能够在程序编译时判断两个类型是否完全相同。本接口可应用在模板元编程、类型检查、条件编译等场景，用于在编译阶段确定类型信息，避免运行时可能出现的类型不匹配问题。

函数原型：template <typename Tp, typename Up>；struct is_same;

参数：Tp：需要比较两个类型是否完全相同的第一个类型。；Up：需要比较两个类型是否完全相同的第二个类型。

返回值：is_same的静态常量成员value用于获取返回的布尔值，is_same::value取值如下：

-   true：Tp和Up是完全相同的类型。
-   false：Tp和Up不是相同的类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Conditional](conditional.md)（`related`）：conditional 可据 is_same 结果选择返回类型或实现类型。
- [EnableIf](enable_if.md)（`related`）：enable_if 可消费 is_same 结果选择特化路径，连接类型等同性判定与编译期分派。
- [is_convertible](is_convertible.md)（`related`）：is_same 要求完全相同，is_convertible 只要求可转换；API 约束强度不同。
- [is_pointer](is_pointer.md)（`related`）：is_pointer 与《is_same》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [remove_cv](remove_cv.md)（`related`）：配合 IsSame 可在编译期验证 remove_cv_t<T> 是否为预期基础类型。
- [remove_volatile](remove_volatile.md)（`related`）：配合 IsSame 验证移除后类型。
- [IntegralConstant](integral_constant.md)（`same_topic`）：is_same 的布尔结果通过 integral_constant 形式暴露，供模板条件消费。
- [is_void](is_void.md)（`same_topic`）：is_void 与《is_same》的实质衔接是：is_void 常与 integral_constant/is_same 表达编译期结果，并通过 Conditional/EnableIf 选择仅对 void 或非 void 有效的模板实现。
- [remove_pointer](remove_pointer.md)（`same_topic`）：remove_pointer 与《is_same》的实质衔接是：remove_pointer 与 add_pointer/is_pointer 构成指针类型归一化，随后常用 is_same、Conditional 或 EnableIf 约束模板分支。
<!-- cannbot:related:end -->
