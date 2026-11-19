---
type: API
title: op_never_timeout：GE 算子标签与融合后的失效边界
description: 说明不超时 scope 的 True/False 嵌套、禁止断图以及融合不继承属性。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/op_never_timeout.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/op_never_timeout.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/op_never_timeout.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/op_never_timeout.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_scope_attr.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/_scope_attr.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# op_never_timeout：GE 算子标签与融合后的失效边界

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取 A2/A3；主线 A2/A3 与950的限定范围见下节，不回推发布版。

## 接口

`torchair.scope.op_never_timeout(enable: bool=True)` 在 with 范围给 GE 节点添加 _op_exec_never_timeout 属性；无返回值，scope 内不支持 graph break。嵌套 enable=False 可取消对应内层节点的该标记。

## 适用与核验

仅 GE 图模式，面向已确认确需较长执行的算子。它不是修复死锁、HCCL 超时或通信域 timeout 的接口。子算子标记不会继承到融合后的新节点，必须检查最终编译图属性，不能只看 Python 范围或融合前日志。

标记排除了对应算子的超时检测，不保证异常时自动恢复，也不保证来源演示中的所有融合策略保持该效果。先定位耗时原因，再以最终节点、scope 日志和业务进展验证。

- [融合控制和统计](../../guides/optimization/torchair/torchair_fx_pass_and_fusion_controls.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线对应scope与最终节点

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节对应文档已与发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 逐页对照；主线总览声明A2/A3与950PR/950DT，未在这些接口页另列产品排除。950仅属于主线证据，不回推发布配套，也不证明两仓主线组合已兼容。

主线API及特性页仍是enable=True默认、True/False嵌套，GE范围、禁止断图和融合节点不继承的同一约束；未增加捕获后端、HCCL故障恢复或任意长任务均可安全放行的承诺。源页示例日志只是融合前节点属性示范，最终图与执行进度仍须核对。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/op_never_timeout.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/op_never_timeout.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/op_never_timeout.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/op_never_timeout.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
## op_never_timeout 的实现配对

本节把本卡两页（特性页与 scope API 页）的承诺与 TorchAir Python 实现配对；scope 属性栈、`@guard_scope_attr`/`apply_scope_attr` 的应用机制与多流 scope 标签已由[scope 属性与多流控制边](../../guides/optimization/torchair/torchair_ge_multistream_control_edges_and_scope_labels.md)承载，此处只补本接口的门槛、值链路与新差异，不重述。

- enable 类型门是硬拒绝：`op_never_timeout(enable)` 在进入 scope 前检查 `isinstance(enable, bool)`，非 bool 直接抛 `TypeError`（scope/__init__.py:74–75 主线/64–66 发布，两版一致）。int 0/1 同样被拒，不是「truthy 即可」；文档与 API 页只写「bool类型」，未提该异常。
- 属性值链路：`str(enable)` 作为 `_op_exec_never_timeout` 的栈值进入 `_Scope`（主线 77/发布 69–70）；`ScopeAttrs.apply` 把该键写为 GE 布尔属性 `op.attr[key].b = (value == "True")`（_scope_attr.py:40–41 两版——布尔属性仅在字符串精确等于 "True" 时为真，与多流卡结论一致，此处只锚定行段）。属性经 `@guard_scope_attr` 装饰的 `_parse_node_internal`（fx2ge_converter.py:1723）作用于 scope 块内新增 GE 节点；嵌套时逐层 apply，内层 enable=False 以字符串 "False" 写出布尔假，与文档「嵌套取消」语义一致。
- 与 View 优化的交互（新增配对）：通用 scope 门对纯 super_kernel scope 有例外——`has_scope_attr()` 为真且非「仅 super_kernel」时才在该 scope 块内禁用 View 跳过（_scope_attr.py:79–92 主线）；本接口写入的 `_op_exec_never_timeout` 使含它的 scope 不是纯 super_kernel，进入本接口即阻断该 scope 块内的 view 跳过，见[GE 编译调优](../../guides/optimization/torchair/ge_compile_optimization_controls.md)的源码配对节——view_optimize 页把本功能列入「不生效」清单的机制根源即此通用 scope 门，四项清单之外的其他非 super_kernel scope 同样阻断，纯 super_kernel scope 不触发该阻断。
- 日志锚点：文档示例 DEBUG 行「Set attribute _op_exec_never_timeout: True on op: Mul」来自 `ScopeAttrs.apply` 的日志（两版 _scope_attr.py:44）；文档样本标注的 `[_scope_attr.py:38]` 是旧构建行号，消息格式与当前两 pin 实现一致——样本行号不应用作版本判别。
- 版本边界：发布版 `npu_stream_switch` 无 `enable_inner_parallel` 参数（主线 scope/__init__.py:22 三参数/发布 22 两参数），故发布 `apply` 的布尔写分支只列 `_op_exec_never_timeout`（_scope_attr.py:40），主线把 `_enable_inner_parallel` 一并按布尔写（40–41）；`deterministic` scope 构造器为主线独有（发布 rg 零命中）。
- 约束「融合后不继承」「with 内不支持断图」在已读的 scope/_scope_attr.py、scope/__init__.py 与 fx2ge 装饰器路径中没有 Python 层强制点（两 pin scope 树 rg 零命中）：融合继承性由 GE 融合过程决定，断图约束属 Dynamo 捕获语义，本仓静态读数不能证明其下游裁决方式；「必须检查最终编译图属性」的核验路径不变。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/__init__.py)（implementation）：1–81 全文读取（op_never_timeout 56–77、deterministic 43–53、npu_stream_switch 22–29、data_dump 80–81）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/__init__.py)（implementation）：39–77 窗口读取（op_never_timeout 46–70、data_dump 74–77）；1–38 未复读，npu_stream_switch 参数差异以 rg 行级证据记录。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_scope_attr.py)（implementation）：1–131 全文读取（apply 32–44、guard_scope_attr 67–76、has_scope_attr 79–80、has_only_super_kernel_scope_attr 83–92）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/_scope_attr.py)（implementation）：28–50 窗口读取（apply 布尔写 40–41、日志 44）；其余段未复读。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：1716–1726 窗口读取（@guard_view_input 1722 与 @guard_scope_attr 1723 挂 `_parse_node_internal`）。
- 同时复读主线 API 页 api/scope/op_never_timeout.md（1–30，融合不继承与禁止断图约束在 25–26）与特性页 features/advanced/op_never_timeout.md（全文含示例日志段）；发布两页未复读，以上文既有两版对照结论为准。全部为静态读取，未运行上游代码或 NPU 实验。
