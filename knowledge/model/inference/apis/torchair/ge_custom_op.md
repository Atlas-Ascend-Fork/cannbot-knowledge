---
type: API
title: ge.custom_op：原生 Converter 的 IR 输入、属性与动态输出
description: 说明 REG_OP 映射、args 优先级、显式属性类型和动态输出结构，不混同自动适配路线。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/custom_op.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/custom_op.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/ge_custom.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-09T02:51:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# ge.custom_op：原生 Converter 的 IR 输入、属性与动态输出

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取 A2/A3；主线 A2/A3 与950的限定范围见下节，不回推发布版。

## 接口职责

`torchair.ge.custom_op(op_type,*args,inputs=None,outputs=None,attrs=None,node_name=None)` 在原生 Converter 内构造 Ascend IR 节点，op_type、输入/输出名称和顺序需与 REG_OP 一致。它不负责安装 Eager Kernel 或自动补齐 Meta。

## 参数方式与返回

args 顺序方式与 inputs/outputs/attrs 字典方式不要混用，同时提供时以 args 解析结果为准。动态输入用 Tensor 列表，可选未传输入为 None；动态输出必须用显式 outputs=["m",("n",数量)]，不能依赖 args 自动推导。

返回结构随输出定义：普通输出是 GE Tensor，动态输出是一组 Tensor；不要因签名简写 `->Tensor` 就把所有多输出当单 Tensor。attrs 用 ge.attr.Bool/Int/Float/Str/DataType 及对应列表类明确类型，不能混用普通整数和类型枚举；显式方式的属性按原型填写，不因等于默认值就省略示例要求的属性。node_name 在一张图内唯一。

## 适配路线

本卡为发布版原生 Converter 接口。主线的零交付件自动 GE 适配有独立前提，不能据它跳过此发布路线的 Converter、GE IR 或 OPP 交付。对可选输入、零动态输入、动态多输出和符号维度分别检查 Meta 与 GE 输出结构。

- [完整交付与两种适配路线](../../guides/integration/torchair/custom_operator_graph_contract.md)
- [GE 类型、常量和拷贝节点](../../guides/optimization/torchair/ge_converter_tensor_and_control_edges.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线注册查询与args校验

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节对应文档已与发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 逐页对照；主线总览声明A2/A3与950PR/950DT，未在这些接口页另列产品排除。950仅属于主线证据，不回推发布配套，也不证明两仓主线组合已兼容。

主线custom_op先查询已注册GE IR；动态库加载状态缺失或IR未注册时报错，再选择显式字典或args解析路线。这个入口不会自动生成IR、加载任意业务Kernel或绕过缺失交付。API页与发布页的接口/约束一致，变化的图开发文档链接不是软件兼容证明。

args解析要求数量严格等于IR输入数加属性数，不能因为某项可选就直接少传位置；必选输入需GE Tensor，可选输入可Tensor/None，动态输入为list/tuple，属性按原型类型构造。用None跳过属性解析不保证必选属性可缺省。混用显式inputs/outputs/attrs仍被args路线覆盖，node_name单独继续传递。

支持的显式属性类型为Bool、DataType、Float、Int、Str，以及ListBool、ListDataType、ListFloat、ListInt、ListStr、ListListFloat、ListListInt。列表属性类型不能靠元素个数暗推；动态输出数量需显式outputs中的(name,count)，不把args导出的固定输出名列表当作动态数量推断。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/custom_op.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/custom_op.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/ge_custom.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
