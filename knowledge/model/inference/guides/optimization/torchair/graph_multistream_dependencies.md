---
type: Guide
title: 图内多流依赖：GE record/wait 与 npugraph_ex Event
description: 按后端表达跨流顺序，区分执行同步和 record_stream 内存寿命，说明 Event 不能跨 graph break。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/multi_stream.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/multi_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/record.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/wait.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/npu_wait_tensor.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/multi_stream.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/multi_stream_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/feature/多流并发.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/multi_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/multi_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/replace_stream_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/replace_stream_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_tagged_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_tagged_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 图内多流执行与内存依赖

## 先分析可并行区间

从真实数据依赖和 profiling 确认独立分支，再评估计算与计算、计算与通信的重叠。Cube 已饱和时增加流可能引入调度开销；不能仅依据流数量判断收益。

## GE 表达

使用 `torchair.scope.npu_stream_switch` 标记流。`npu_wait_tensor(self, dependency)` 使消费 self 的后续算子等待 dependency 对应生产节点；返回 self 本身。没有自然输出作为依赖时，可用 `torchair.ops.record()` 产生依赖 Tensor，再由当前流 `torchair.ops.wait([tensor])` 等待。

GE 静态图多流与 enable_single_stream 冲突；动态 shape 的多流设置需要另外核对。固定主线新增的 enable_inner_parallel 属性在配套 CANN 大于 9.0.0 时才生效，不能套用到本仓 9.0.0 发布基线。

## npugraph_ex 表达

使用原生 `torch.npu.stream`、Event.record 和 Event.wait。固定来源要求一个 Event 留在同一整图/编译段内，不能跨 graph break。`tensor.record_stream` 延迟内存复用，解决生命周期问题；它不能代替生产者到消费者的执行依赖。

## 验证与回退

分别验证生产完成后读取、跨流 Tensor 提前析构、图内原地更新及多次重放。结合图结构和时间线检查同步是否存在、是否造成额外串行。记录同输入下的精度、峰值显存和稳态时延，无收益或出现死锁时回退单流并保留证据。本文为固定主线说明，未做设备实验。

## 版本入口

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## feature示例的流标签和资源前提

两快照feature页允许重复stream_tag表示同一逻辑流及嵌套context；stream_priority在签名中默认为0且标为预留参数，不能宣传设定它就能获得某种硬件优先级。npu_wait_tensor所等的是dependency的生产完成对self后续消费者的顺序，不因self的数值未改变就删掉依赖。

旧例以A3的Cube/Vector分离和计算/通信资源重叠说明用途，FP16、1000×1000、dynamic=False/fullgraph=True仅为示例，不证明任意产品/动态shape/规模有收益；本卡已有主线范围不由该例扩大。AI Core饱和时更多流可能只增调度成本。独立npugraph_ex的scope闭环、融合检查和捕获流设计另见[实现差异草稿](npugraph_ex_standalone_design_contracts.md)，不能与GE路径互换为同一执行协议。

## 捕获闭环与业务同步的图示区别

发布npugraph_ex多流图只展示从流末尾record3/record4与默认流wait3/wait4；主线重绘后明确区分实线的用户event1/event2和虚线的框架头尾record/wait闭环。后者使从流任务进入同一次捕获，不证明业务数据依赖自动成立。Event不能跨graph break，record_stream也不能代替event同步。

GE的动态shape多流默认关闭，ENABLE_DYNAMIC_SHAPE_MULTI_STREAM=1用于开启底层自动分流；用户显式npu_stream_switch表达的优先级更高。静态shape的enable_single_stream冲突、SuperKernel中优先使用其stream-fusion配置等条件独立核对，不能把两类后端的流标签和原生Stream对象互换。

## Evidence

- [docs/zh/ascend_ir/features/advanced/multi_stream.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/multi_stream.md)（primary）
- [docs/zh/npugraph_ex/advanced/multi_stream.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/multi_stream.md)（constraint）
- [docs/zh/ascend_ir/api/ops/record.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/record.md)（supporting）
- [docs/zh/ascend_ir/api/ops/wait.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/wait.md)（supporting）
- [docs/zh/ascend_ir/api/scope/npu_wait_tensor.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/npu_wait_tensor.md)（supporting）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/multi_stream.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/multi_stream_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/feature/多流并发.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/multi_stream.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/multi_stream.md)（constraint）
## npugraph_ex 流/Event 改写的源码配对

本节把本卡「npugraph_ex 表达」与「捕获闭环」两节跟两固定 pin 的集成包 python/torchair ACL 实现配对。GE 路径的 record/wait 控制边机制配对见[GE 跨流接口](../../../apis/torchair/ge_stream_dependencies.md)；独立 npugraph_ex 包（npugraph_ex/ 目录）不在本卡读取范围，其 scope 闭环与捕获流设计以[独立包设计契约](npugraph_ex_standalone_design_contracts.md)为准。

- 模式门：`replace_stream_event_pass` 只在 mode ∈ {reduce-overhead, npugraph_ex} 时运行（npu_fx_compiler.py:1098–1100 主线/935–937 发布，AOT 编译入口 1.1 步骤）。max-autotune（GE）不运行该 pass；torch 无 npu 或 fake_record_stream 属性时跳过并打 warning（replace_stream_event.py:26–29 主线/27–30 发布）。
- 原生 API 改写（replace_stream_event.py 主线 25–238/发布 26–189）：Event 节点出现即按名注册 tagged event（主线 52–56/发布 51–55）；`torch.ops.streams.record_event/wait_event`、`event.record/wait`、`stream.wait_event/wait_stream/record_event` 方法调用改写为 `air.tagged_event_*`，带流参数生成 `*_on_stream`（stream_id/device_index/device_type）；`torch.npu.fake_record_stream` 改写为 `air.record_tagged_stream_`（主线 93–98/发布 72–73）；`torch.npu.Stream`/`current_stream` 节点从 node.meta.example_value 提取 stream_id/device_index/device_type，缺失即 RuntimeError（主线 264–301/发布 226–263）。等于捕获起点默认流的参数以 DEFAULT_*_MARKER 字符串标记（主线 324–330、354–358/发布 273–278、303–316），由 resolve_default_stream_markers pass 解析（_tagged_event.py:183–197 主线注释，发布同构 178–192）。
- 版本差异一处：主线对 `torch.ops.streams.record_event/wait_event` 带流参数时先比对捕获起点默认流，相等则改写为无流 tagged_event_record/wait（主线 57–92）；发布版同路径直接生成 `*_on_stream` 形式（发布 55–74），无默认流比对分支。不能把主线该改写行为套用到发布版。
- set_stream 栈纪律：set_stream 在栈外则入栈并改写为 `air.scope_enter`（键 `_user_stream_label/_user_stream_priority`，另按可用性附 `_user_stream_id/_user_stream_device_index/_user_stream_device_type`，priority 固定 0——主线 352/发布 299）；目标流已在栈内时只弹出其上方条目并逐个插入 `air.scope_exit`（主线 206–212：while 栈顶不等于目标才 pop，目标本身保留、不重插 scope_enter，目标已是栈顶则零弹出）；切回默认流则整栈弹出（主线 213–219）；图末栈非空直接 RuntimeError「you must make sure at the end of your code set stream to the same stream as the begin of your code」，报错文本推荐 with torch.npu.stream()（主线 226–234/发布 181–189）。该门是流 scope 配平的编译期硬拒绝：不平衡的原生 set_stream 序列被拒绝编译，不是静默兜底；它证明的是流切换必须配平，文档「Event 不能跨 graph break」的约束是文档层表述，已读实现没有把两者画等号。`_user_stream_priority` 键表还被控核 pass 用作流切换 scope 的识别标记（主线 graph_pass.py:748 仅用键名集合、值不读；发布版同常量 rg 命中 graph_pass.py:737，该区块未读）——与接口卡「priority 为预留参数」一致。
- wait 自动补 record：`apply_event_record`（graph_pass.py:690–698 主线/684–692 发布）对 wait 参数里非 record 节点，在生产节点之后自动插入 `air.record` 节点（wait_record_dic 按生产者去重）——ACL 路径不要求用户手写 record。
- 头尾事件闭环：`apply_event_closure_with_multi_stream`（主线 610–686/发布 613–681）先过存在门：无 qualifying 用户流 scope_enter 即早退返回 False（主线 650–652/发布 645–647），不插任何事件、也不做末节点 output 检查；仅存在用户流 scope_enter 的剩余分支在首个节点前 record enter 事件、在每个流 scope_enter 之后 wait，在每个流 scope_exit 之前 record exit 事件、在 output 节点之前 wait，且该分支内末节点非 output 即 RuntimeError（主线 669–671/发布 663–665）。本卡「框架头尾 record/wait 闭环」的插入位置即此。两个 pass 均由 fx2acl 转换器调用（fx2acl_converter.py:261–274 主线/248–258 发布）。
- tagged event 的 eager 实现与边界：record/wait 在 `torch.npu.current_stream()`（或按 stream_id/device_index/device_type 构造的显式 Stream）上执行；tag 缺失抛 AssertionError（提示用 npu_create_tagged_event 创建或报 issue）；created_inside=True 时事件取自 `_GLOBAL_SCOPE_TAG_TO_EVENT`（_tagged_event.py 主线 21–56、200–233/发布 21–52、200–232）。GE 转换器对 tagged_event_record/wait、record_tagged_stream 一律 raise NotImplementedError（主线 81–98、124–126/发布 78–96、122–125）——这组算子是 ACL 路径专用，GE(max-autotune) 路径不支持。
- `torchair.ops.npu_record_tagged_stream(input, tag)` 的 eager 实现经 `_npu_get_or_create_stream_with_tag` 按标签懒建 `torch_npu.npu.Stream()`（全局锁+字典缓存，_scope_attr.py:99–109 两版）后调 `input.record_stream(stream)`；源码注释明确 record_stream 不修改输入、只按 data_ptr 增加流使用计数，先 clone 会让记录的 data_ptr 变成 clone 的（_tagged_event.py:59–68 两版）——不能用先 clone 的方式“保护”跨流 Tensor。
- `guard_with_user_stream_scope`（_scope_attr.py:112–125 主线/111–123 发布：按 scope 顶层 `_user_stream_label` 把执行切到标签流上下文）在两 pin 的 python/torchair 内都只有定义和 acl_graph.py 的导入（主线 25/发布 24），没有任何应用点（rg 全树各恰 2 行）——存在不等于消费：不能据此宣称当前版本有经该装饰器的流路由；其依赖的标签流工厂 `_npu_get_or_create_stream_with_tag` 的真实消费者是 npu_record_tagged_stream。本断言限定在两 pin 的 python/torchair 集成包树。
- 本节全部为集成包静态读数；tagged event 的运行时语义、graph break 处的行为未运行验证。

### 配对差异归组

| 文档/本卡承诺 | 实际门槛与动作（静态读到） | 失败/版本边界 |
| --- | --- | --- |
| 「使用原生 torch.npu.stream、Event.record/wait」 | ACL 路径先经 replace_stream_event_pass 全量改写为 air.tagged_event_*/record_tagged_stream_/scope_enter/exit | 仅 reduce-overhead/npugraph_ex 运行；GE 模式不改写 |
| 「原生流切换 scope 必须配平」 | set_stream 栈必须配平，否则编译期 RuntimeError | 硬拒绝不是静默兜底；报错文本推荐 with torch.npu.stream() |
| 「Event 留在同一整图/编译段内，不能跨 graph break」 | 文档层约束；静态读数未读到对应实现门（implementation unclosed） | 不能把 set_stream 栈配平门当作该约束的实现证明 |
| 「没有自然输出的生产节点可用 record 产生依赖标记」 | ACL 路径 wait 参数非 record 时自动补插 record（两版） | ACL 路径手写 record 非必需；GE 路径仍按接口卡控制边机制 |
| 「框架头尾 record/wait 闭环使从流任务进入同一次捕获」 | enter/exit 事件四点插入（两版同构），仅当存在用户流 scope_enter 才执行（存在门 650–652/645–647） | 插入路径中末节点非 output 即 RuntimeError；无流 scope 的图整段跳过；闭环不证明业务数据依赖 |
| tensor.record_stream 延迟内存复用 | fake_record_stream→record_tagged_stream_→input.record_stream(标签流) | 先 clone 会让记录的 data_ptr 变成 clone 的（源码注释，两版） |
| npugraph_ex 独立包同名行为 | 未读独立包，以既有契约卡为准 | 不得把集成包行号/结构反推独立包 |

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：窗口 1085–1110（replace_stream_event_pass 的模式门 1098–1100）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：窗口 925–945（模式门 935–937，与主线同构）。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/replace_stream_event.py)（implementation）：1–385 全文读取（改写主循环 25–238、set_stream 纪律 191–234、默认流标记 304–377、_get_stream_info 264–301）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/replace_stream_event.py)（implementation）：1–330 全文读取（与主线同构；发布版无 torch.ops.streams.* 默认流比对分支 55–74；set_stream 纪律 147–189；标记逻辑 251–326；priority 固定 0 在 299）。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py)（implementation）：窗口 575–780（_create_event_by_name 580、_extract_user_stream_info 588–604、closure 610–686、apply_event_record 690–698、_insert_record_nodes 700–715、控核 pass 键名标记 748）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/graph_pass.py)（implementation）：窗口 575–712（closure 613–681、apply_event_record 684–692，与主线同构）。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：窗口 255–278（closure/apply_event_record 调用点 261–274）。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：窗口 240–260（调用点 248–258，与主线同构）。
- [新增来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_tagged_event.py)（implementation）：1–292 全文读取（record/wait eager 31–56、record_tagged_stream 59–68、GE 转换器 NotImplementedError 81–98/124–126、标签字典 130–151、on_stream 变体 200–292）。
- [新增来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_tagged_event.py)（implementation）：1–272 全文读取（与主线同构；发布 GE 转换器 NotImplementedError 78–96/122–125、on_stream 变体 240–272）。
- [新增来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：窗口 22–28（guard_with_user_stream_scope 仅导入 25）。
- [新增来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：窗口 22–26（仅导入 24）。
- 本节引用的 _scope_attr.py 两版全文读取登记在[GE 跨流接口](../../../apis/torchair/ge_stream_dependencies.md)新增来源 9/10（同次阅读，不重复登记）。负向扫描（rg 全 python/torchair，两 pin）：`guard_with_user_stream_scope` 各恰 2 行（定义+导入，无应用点）。全部为静态读取，未运行上游。
