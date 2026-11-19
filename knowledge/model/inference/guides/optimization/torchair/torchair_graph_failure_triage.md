---
type: Guide
title: TorchAir 入图失败：按 Eager、FX、Converter 与执行阶段定界
description: 区分断图、Meta、函数化与缺少 Converter 的失败，按阶段选择日志和下一步检查。
tags:
- task.debugging
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/graph_failed_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T03:19:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 入图失败：按 Eager、FX、Converter 与执行阶段定界

## 版本与任务

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`，本卡限定 A2/A3 推理。该提交属于 ascend_26_0_pt28 的固定来源组合；其他版本须核对实际接口。


## 先确认失败在哪一层

1. 在同一软件环境、输入和设备上运行未编译的 NPU Eager。若失败，先定位算子、参数或交付件；此时图配置不能修复基础执行问题。
2. 用 torch.compile 的 Eager 后端对照前端产生的 FX 图。这里的 Eager 后端仍经过 Dynamo/FX，与第一步不同；失败时先查脚本、Meta 和符号推导。
3. 进入目标 NPU 后端时检查 FX 是否成图、是否 graph break，再区分原生 GE Converter 转换、GE 编译和执行失败。断图后的局部成功不能当作整图接入成功。

来源流程图的“NPU 后端失败”只是定界线索，不足以唯一证明断图；需以堆栈和图产物确定具体阶段。npugraph_ex 不使用 GE Converter，不能把 GE 的修复路径直接套给捕获后端。

## 报错与应查交付件

|报错线索|优先检查|处理边界|
|--|--|--|
|unsupported operator 或 dispatch TLS exclude set 相关断言|准确 namespace/overload 是否有 Meta/符号推导，加载模块是否执行|来源将缺 Meta 列为案例原因，不能只凭通用错误字符串断言根因|
|tensor's device must be 'meta', got cpu instead|Meta 函数是否错误返回普通 CPU Tensor|来源示例改为 device="meta"；仍需验证输出 shape、dtype 和符号关系|
|Found a custom (non-ATen) operator，且指出 mutation|Schema 的别名/mutation、非原地变体与函数化实现|补齐保留原地语义的转换，不通过删 mutation 标记绕过|
|ge_converter is not implemented|原生 GE 路线对应 overload 的 Converter|补齐或加载匹配实现；主线零交付件路线另有前提，不能推定发布版自动提供|

## 收集足够的证据

TorchAir Python DEBUG 与 TNG_LOG_LEVEL=0 用于前后端日志；config.debug.graph_dump.type="pbtxt" 保存 TorchAir 图，DUMP_GE_GRAPH 用于 GE 图；ASCEND_GLOBAL_LOG_LEVEL=0 与 ASCEND_SLOG_PRINT_TO_STDOUT=1 用于 CANN 日志。后两组环境变量和 GE Dump 的完整取值、路径、安装限制依赖实际 CANN 版本，本卡不扩展未审阅的 CANN 手册。

记录第一个失败阶段、准确报错节点及其上游、Meta 输出、图转换结果和真实输出，避免把下游报错节点等同于最初发生偏差的位置。

- [Schema、Meta、函数化与后端交付](../../integration/torchair/custom_operator_graph_contract.md)
- [shape/dtype 与输出内存的偏差](ge_shape_dtype_failure_diagnosis.md)
- [图结构和 Eager 定界](../torch_npu/torchair_graph_dump_and_run_eagerly.md)


## 验证边界

保留相同输入、rank、软件栈和变更前后的证据，先检查输出及存储语义，再关闭调试配置复测。来源案例是定位参考，不能把单条报错视作根因证明。本文仅静态审阅，未执行上游代码或 NPU 实验。

- [软件栈版本与来源身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线案例与函数化边界

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的失败案例仍将原生NPU Eager、Dynamo/FX、目标后端转换与GE编译/执行分阶段定位；主线总览列A2/A3/950推理。Meta返回CPU Tensor、缺少Converter、mutation缺少函数化和dispatch断言是不同案例，不能仅凭“入图失败”选择一个通用修复。

主线页面仍用手写函数化作为自定义原地算子的示例。实际是否可由框架自动函数化，还取决于PyTorch版本与Schema，按[自定义算子入图契约](../../integration/torchair/custom_operator_graph_contract.md)核对；不据旧案例要求所有算子必须手工补同一种kernel，也不通过删别名标记掩盖mutation。

主线环境变量表把GE Dump和CANN日志的细节交给独立CANN手册。此处只保留页面已列出的日志入口，不能从引用master链接推断所有CANN版本的值域与安装路径相同。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/graph_failed_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
