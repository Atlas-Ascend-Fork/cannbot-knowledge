---
type: API
title: GE 跨流接口：record、wait、npu_wait_tensor 与流标签
description: 区分无输出节点标记、当前流等待与返回原 Tensor 的依赖注入，并说明流内并行参数的版本门槛。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/record.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/wait.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/npu_wait_tensor.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/npu_stream_switch.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/npu_stream_switch.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/multi_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/multi_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/record.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/wait.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/npu_wait_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_record_wait.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_record_wait.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_wait_tensor.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/_wait_tensor.py
  role: implementation
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
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_pre_scan.py
  role: implementation
created_at: '2026-11-09T04:38:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# GE 跨流接口：record、wait、npu_wait_tensor 与流标签

## 版本与范围

依据 TorchAir 主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的 GE 接口文档，选择 A2/A3 推理。发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的流切换签名只有前两个参数；主线参数不回推到发布基线。

## 输入、返回值和作用对象

|接口|契约与用途|
|--|--|
|`torchair.ops.record()`|无参数，在当前流显式下发任务，返回可供 wait 等待的 Tensor；没有自然输出的生产节点可用它产生依赖标记。|
|`torchair.ops.wait(tensors: List[torch.Tensor])`|当前流等待列表中 Tensor 对应的生产节点完成，无返回值；可一次指定多个依赖。|
|`torchair.scope.npu_wait_tensor(self, dependency)`|为消费 self 的后续节点建立对 dependency 生产节点的等待，返回 self 本身；不要据此假定分配了新存储。|
|`torchair.scope.npu_stream_switch(stream_tag, stream_priority=0, enable_inner_parallel=True)`|with 块内给算子标注目标流；相同字符串标签表示同一流。stream_priority 当前为预留参数，使用默认 0，不能据它承诺调度优先级收益。|

流切换块内不允许 graph break。主线 enable_inner_parallel 为布尔值，控制 GE 是否按原有并发策略继续在标签流内分流，默认 True；它写入 `_enable_inner_parallel`，仅支持 max-autotune 模式且配套 CANN **大于** 9.0.0 才生效。发布基线 CANN 9.0.0 不满足此门槛。

## 正确性边界

依赖对象应对应真实生产者和消费者；wait 是当前流的执行顺序约束，不是 Python 值拷贝。它们也不能替代 tensor.record_stream 对内存复用时机的管理。先验证跨流读写与多次执行，再用时间线评估并行收益。本文仅静态审阅，未执行 NPU 编译。

- [多流依赖的场景设计](../../guides/optimization/torchair/graph_multistream_dependencies.md)

## API页旧签名与功能页增量

两固定快照的npu_stream_switch API页仍列两个参数stream_tag、stream_priority；主线多流功能页才列第三个enable_inner_parallel=True及CANN>9.0.0条件。表中三参数形式据该主线功能页消费，不能反推发布接口已有此参数，也不能因旧API页漏列而宣称主线功能不存在。

record和wait API页的“无约束”只表示未另列专门条目，仍须遵守后端可成图、scope不允许断图以及真实跨流依赖。record可用于已有自然输出的节点以表达清晰依赖，不只是无输出节点的替代物。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/record.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/wait.md)（supporting）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/npu_wait_tensor.md)（supporting）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/npu_stream_switch.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/npu_stream_switch.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/multi_stream.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/multi_stream.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/record.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/wait.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/npu_wait_tensor.md)（constraint）
## record/wait/npu_wait_tensor/npu_stream_switch 的源码链与执行边界

本节把本卡四接口（record/wait/npu_wait_tensor/npu_stream_switch）的契约与两固定 pin 的 TorchAir Python 实现配对。scope 属性栈机制与 op_never_timeout 的布尔写入路径已由[编译调优配对](../../guides/optimization/torchair/ge_compile_optimization_controls.md)与[不超时接口](op_never_timeout.md)承载，此处只补本组实现锚点与新差异，不重述；独立 npugraph_ex 包不在本节范围。

- `torchair.ops.record()`（主线 ops/__init__.py:53–54/发布 46–47）落地为自定义算子 `torch.ops.air.record`：eager BackendSelect 实现只返回 `torch.empty(0, device=device)`（_record_wait.py 主线 8–17/发布 7–17，Meta 同为空 Tensor）。「返回可供 wait 等待的 Tensor」在实现上是 0 元素占位 Tensor，不承载设备数据；图模式下该节点被 GE 转换器吞掉，不产生任何数据算子。
- `torchair.ops.wait(tensors)`（主线 49–50/发布 42–43）先经 `_wait` 包装校验：None 或空列表抛 ValueError，任一元素非 torch.Tensor 抛 ValueError（主线 _record_wait.py:34–40/发布 40–46）。`torch.ops.air.wait` 标记 has_side_effect 且 eager 实现返回 None——图外调用无任何动作，顺序约束只在图转换时生成。
- `torchair.scope.npu_wait_tensor`（scope/__init__.py:5–8 两版）落地为 `torch.ops.air.wait_tensor`：CPU/PrivateUse1 的真实执行内核直接 raise NotImplementedError（主线 _wait_tensor.py:19–26/发布 19–27），即真实执行在这两个后端不可用；Meta 内核返回 self（两版 14–16），Meta/Fake 推断路径不抛该错。不能概括为「无 eager 内核/eager 必抛错」——抛错限定 CPU/PrivateUse1 真实执行，构图走注册的 GE 转换器。发布版报错文本明确把 reduce-overhead 场景指向 npu_create_tagged_event/npu_tagged_event_record/npu_tagged_event_wait 替代（发布 20–23），主线文本没有该指引（主线 20–22），两版报错内容不同。GE 转换器把 `ControlTensor(dependency.node).controller` 追加到 `ge.Identity(self)` 的输入并返回该 Identity（主线 33–38/发布 33–42）：「返回 self 本身」在 GE 图里是 Identity 节点经控制输入原样传递。
- `torchair.scope.npu_stream_switch` 写 scope 属性 `(_user_stream_label, _user_stream_priority)`，主线另有 `_enable_inner_parallel`（主线 scope/__init__.py:22–29/发布 22–26，发布无该参数与既有结论一致不重述）。ScopeAttrs.apply 把前两项写 `op.attr[key].s` 字符串、`_enable_inner_parallel`（仅主线）与 `_op_exec_never_timeout` 写 `op.attr[key].b = (value == "True")`（主线 _scope_attr.py:32–44/发布 32–43）。npu_stream_switch 对参数不做任何类型校验（对比 op_never_timeout 的 isinstance bool TypeError），布尔判定是字符串字面比较：`str(enable_inner_parallel)` 后精确等于 "True" 才写 True——非 bool 值不必然取 False，字面字符串 "True" 同样写 True，其余任意取值（含大小写不同的 "true"）写 False。
- `_user_stream_priority` 的值在已读路径中没有任何消费者把它读作优先级：两 pin python/torchair 全树 rg 各恰 4 处命中——scope 构造写入（scope/__init__.py:26/25，本卡来源 7/8 实读）、ACL 原生 set_stream 改写的键表（priority 固定 0）、流信息提取键表（只提取 stream_id/device_index/device_type）与控核 pass 的键名识别标记（主线仅用键名集合）；后三处的行号锚点与阅读登记在[多流依赖](../../guides/optimization/torchair/graph_multistream_dependencies.md)的新节及其来源内。与「stream_priority 为预留参数」一致，不能承诺调度收益；该键写上 GE 算子（op.attr 字符串）之后的下游消费不在静态读数内。
- GE 转换器的 record/wait 落地（fx2ge_converter.py:1743–1745 主线/1409–1412 发布分派）：record 经 `_build_record_control_edge`（主线 2123–2130/发布 1723–1729）返回当前流在 `_muti_stream_op_order` 中最后一个 op 的 ControlTensor controller；该流尚无算子时返回哨兵字符串 'no_op_before_record'。wait 经 `_build_wait_control_edge`（主线 2131–2143/发布 1731–1741）把 GeTensor 参数转 controller、跳过哨兵，压入 `_wait_control_edges[当前流]`；每次节点转换后 `_handle_wait_control_edge`（主线 2145–2160/发布 1743–1758，挂接点主线 1780/发布 1440）把新增 GE 算子记入所属流，并把待接控制边接到同流 wait 之后第一个算子的 input。当前流由 scope 栈的 `_user_stream_label` 决定（`_get_current_stream` 主线 2116–2122/发布 1716–1722）；未开 npu_stream_switch 时为 None，record/wait 仍以 None 键工作——scope 标签是分桶键而非开关。
- 由此的执行边界：「当前流等待」实现为 GE 控制边，作用对象是 wait 之后的同流算子，不是设备端等待算子；record 时流上无前序算子则哨兵被 wait 过滤、不产生控制边；wait 之后同流无算子时控制边留在桶内没有附着点（GE 下游是否另行消费剩余边，静态读数未见，不下断言）。
- 主线 `_SPECIAL_TARGETS`（fx2ge_converter.py:265–270：air.scope_enter/scope_exit/record/wait.default 四项）有两个消费者：can_convert 对这四个 target 直接返回 True（主线 1696–1697），max-autotune 的自定义算子预扫描跳过它们（custom_op_pre_scan.py:83/138）。发布版 python/torchair 内该集合 rg 零命中；发布版 can_convert/预扫描对应区块未读，不对其下断言。

### 配对差异归组

| 文档承诺 | 实际门槛与动作（静态读到） | 失败/版本边界 |
| --- | --- | --- |
| record「显式下发任务，返回可供 wait 等待的 Tensor」 | eager= torch.empty(0)（两版 8–17）；图内取当前流最后 op 的 controller 或哨兵 | 占位 Tensor 不承载设备数据；流上无前序 op→无控制边 |
| wait「当前流等待生产节点完成」 | `_wait` 先校验非空/全 Tensor（两类 ValueError）；控制边接到 wait 后同流第一个 op 的 input | 图外调用无动作（eager return None）；wait 后同流无 op→边无附着点 |
| npu_wait_tensor「使消费 self 的后续算子等待」 | CPU/PrivateUse1 真实执行 raise NotImplementedError；Meta 内核返回 self；GE=Identity+控制输入 | 真实执行仅 CPU/PrivateUse1 抛错（Meta/Fake 推断不抛）；发布报错文本指向 tagged event 替代、主线无此指引 |
| npu_stream_switch「标注目标流」 | label/priority→op.attr 字符串；_enable_inner_parallel→bool 且 str 化后字面 "True" 才为 True | 无参数类型校验；非 bool 值不必然 False（字面字符串 "True" 也为 True）；发布版无第三参数 |
| stream_priority「预留参数」 | 值无消费者（固定写 0/只取键名标记，两版一致） | 不能承诺调度优先级收益 |

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/__init__.py)（implementation）：1–54 全文读取（wait/record 导出 49–54）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/__init__.py)（implementation）：1–47 全文读取（wait/record 导出 42–47；末行 47 为 `return _record()`，文件无结尾换行符，`wc -l` 计 46，逻辑行数为 47）。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_record_wait.py)（implementation）：1–44 全文读取（record eager 8–17、wait has_side_effect 22、_wait 校验 34–40、_record 43–44）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_record_wait.py)（implementation）：1–49 全文读取（与主线仅排版差异；_wait 校验 40–46、_record 49）。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_wait_tensor.py)（implementation）：1–38 全文读取（kernel_impl raise 19–22、impl 注册 25–26、GE 转换器 33–38）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/_wait_tensor.py)（implementation）：1–42 全文读取（raise 文本指向 tagged event 替代 20–23、GE 转换器 33–42；其余与主线同构）。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/__init__.py)（implementation）：1–81 全文读取（npu_wait_tensor 5–8、npu_stream_switch 22–29、op_never_timeout TypeError 74–75）。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/__init__.py)（implementation）：1–77 全文读取（npu_stream_switch 22–26 无第三参数；op_never_timeout TypeError 62–65）。
- [新增来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_scope_attr.py)（implementation）：1–131 全文读取（apply 32–44、has_scope_attr 79–80、_npu_get_or_create_stream_with_tag 99–109、guard_with_user_stream_scope 112–125）。
- [新增来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/_scope_attr.py)（implementation）：1–128 全文读取（apply 32–43 仅 _op_exec_never_timeout 走 bool；与主线同构仅少 _enable_inner_parallel 分支）。
- [新增来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 265–270、1159–1160、1690–1700、1743–1745、1780、2116–2160（record/wait 分派、控制边三函数与 can_convert 特判；_SPECIAL_TARGETS 定义 265–270）。
- [新增来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 934–935、1409–1412、1440、1716–1758（发布版对应分派与控制边三函数，与主线同语义仅行号不同；_SPECIAL_TARGETS rg 零命中）。
- [新增来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_pre_scan.py)（implementation）：窗口 80–142（预扫描对 _SPECIAL_TARGETS 的跳过 138–139）。
- 负向扫描（rg 全 python/torchair，两 pin）：`_enable_inner_parallel` 主线恰 2 行（写+apply）、发布 0 行；`_SPECIAL_TARGETS` 发布 0 行；`_user_stream_priority` 两 pin 各恰 4 行（scope 写入、set_stream 键表、提取键表、控核键名标记）。全部为静态读取，未运行上游；「消费者不存在」限定在 rg 树（python/torchair）与已读窗口，后两处键表的行号锚点由[多流依赖](../../guides/optimization/torchair/graph_multistream_dependencies.md)来源承载。
