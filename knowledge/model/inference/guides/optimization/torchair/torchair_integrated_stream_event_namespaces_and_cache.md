---
type: Guide
title: 集成 TorchAir 的流事件改写：命名空间、缓存与版本边界
description: 对照集成流事件改写的高接口分支、npugraph_ex与air目标差异、实际事件缓存及默认流解析白名单，限定注册与运行证明。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/replace_stream_event.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/replace_stream_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
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
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_lib.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_lib.py
  role: implementation
created_at: '2026-11-11T10:31:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成 TorchAir 的流事件改写：命名空间、缓存与版本边界

本卡只描述固定主线 `92e1e967`、固定发布 `7c6c754b` 的 `python/torchair` 集成实现。两版 `replace_stream_event.py` 的完整本地定义及所列真实入口、注册与缓存消费者已静态对照，没有导入模块、取得外部对象、改写 FX 图、创建 Event/Stream 或执行设备同步。

已有[独立包事件与作用域闭环](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)绑定另一个命名空间；本卡不从独立包较新的 cond 遍历、入口流复用或错误提示，推导集成实现具有同样机制。集成任务更新的另一组 Event 与共享列表见[更新规则与捕获交接](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)。

## 实际入口与接口探测

集成 `npu_fx_compiler` 在 mode 值属于 `reduce-overhead`、`npugraph_ex` 时，将当前传入的 gm 交给本模块的 `replace_stream_event_pass`。pass 本体若缺 `torch.npu` 或 `torch.npu.fake_record_stream` 就告警并返回；这不是所有多流能力的版本认证。

`_torch_high_version` 只检测 Dynamo 是否提供 `graph_bytecode_inputs.get_external_object_by_index`，没有与某个 PyTorch 版本号比较。普通 Event/Stream 构造器与外部对象路径另由本地 helper 识别；legacy `get_user_object_from_id` 目标会被 `_is_event` 直接认作事件，不能把这份判断当成任意用户对象的类型验证。

每次 pass 使用递增的类级 `GraphCounter` 构造 `graph_N_` 前缀，事件索引表、流栈和流信息表则在本次调用中新建。`set_graph_id` 可以直接覆盖计数，所读计数方法没有锁；前缀机制不是任意复位、并发或多进程下的唯一性证明。本函数只遍历当前 gm 的节点，没有在这里递归扫描所有子图。

## 显式流路径有真实的命名空间与参数差异

下表中的“高接口路径”指上述外部对象接口探测成立且节点 target 为 `torch.ops.streams.record_event/wait_event`；不是所有 record/wait 写法都进入这一分支。

| 输入分支 | 固定主线集成实现 | 固定发布集成实现 |
| --- | --- | --- |
| 高接口、显式 stream 对象，且入口流 ID 非 None、stream_id 与它相同 | 改为 `torch.ops.npugraph_ex.tagged_event_record/wait`，只传事件 tag 与 True | 改为 `torch.ops.air.tagged_event_record_on_stream/wait_on_stream`，显式传三项身份 |
| 高接口、其他显式 stream 对象 | 改为 `npugraph_ex.*_on_stream`，将 stream_id/device_index/device_type 各自转成 str | 改为 `air.*_on_stream`，直接传对象字段的原值 |
| 高接口、没有显式 stream | 两版均改为 `air.tagged_event_record/wait`，传 tag 与 True | 同主线 |
| `call_method` 形式的 event.record/wait、stream.wait_event/record_event/wait_stream | 两版相应改为 `air` tagged 操作；显式身份经过本地 helper，可能成为默认流标记字符串 | 同一命名空间，不能以此覆盖上面的高接口差异 |

高接口通过 `event_index_to_node_name[index]` 直接索引事件名，所读分支没有独立包后来增加的“索引缺失时给出分支闭环提示”判断。缺失键存在 KeyError 路径，不应承诺所有不匹配都转成统一的友好诊断。显式流对象的属性读取也没有在这些分支建立通用异常回退。

这里的本地 `torchair.ops._lib` 是 `Library('air', 'FRAGMENT')`；所引 on-stream 注册检查/定义的目标也都是 `air`，schema 将三项身份声明为 str。发布高接口直接传对象原值的行为与这份本地 schema 需要在真实 dispatcher 环境下核对，不能写成它已经在改写时完成与主线相同的字符串归一化。

主线部分分支实际写成 `npugraph_ex`，是需要单独检查的接线边界。本地所读 `air` 注册点并不证明整个进程没有其他包注册 `npugraph_ex`，更不证明已复现算子查找或设备执行失败。也不能因为另一命名空间存在同名操作，就自动视为使用相同事件缓存、schema、实现或默认流策略。

## 事件名必须对应实际缓存

本模块创建事件时调用导入的 `torchair._acl_concrete_graph.graph_pass._create_event_by_name`。两版该 helper 都在全局锁下按名字向其 `_GLOBAL_SCOPE_TAG_TO_EVENT` 字典创建一次 Event。所读局部创建函数没有为每个 gm 另建私有字典或自动删除缓存项。

集成 `ops._tagged_event._get_event_by_tag` 在 `created_inside=True` 时，明确从这个集成 `graph_pass` 模块导入并查找 `_GLOBAL_SCOPE_TAG_TO_EVENT`。因此事件 tag、created_inside 标志及实际执行操作所属模块要一起核对；不能将“同名 tag 已创建”脱离其缓存所属模块理解为任意 namespace 都能读到同一对象。本卡没有展开另一个 namespace 的实现、其他注册包或完整 Event 执行合同。

所引 on-stream 注册还以 `hasattr(torch.ops.air, name)` 为条件；操作已经存在时不会由这些块重新安装实现。Meta 函数返回 None、声明 side effect、绑定 Composite 实现，分别是不同动作，不是 Meta 调用已经完成设备同步的证据。

## 流栈与默认流解析只到本地实际范围

本 pass 从 `example_value` 读取流的三项身份；缺 meta 对象或相应属性会报错，priority 固定为 0。显式 helper 对“表中没有流信息”的情况报错，scope 参数构造 helper 则只追加当前可得身份；不能把它们统称为完全相同的身份验证。`fake_record_stream` 改为 `air.record_tagged_stream_`，传 Tensor 与流节点名，没有在这里复制 Tensor。

`current_stream` 节点记录当时的逻辑流；切入新流时改为带图前缀 label 的 `air.scope_enter`。目标在栈中时只弹出它上方的项，并为这些项插入 `scope_exit`；目标已经在栈顶则不插入，切回逻辑 `default_stream` 哨兵才清空整个栈。这些退出分支没有在此统一删除原 set_stream 节点；结束栈仍非空则报错并要求用户恢复入口流。成功尾部调用 gm.recompile，不构成任意嵌套、异常退出或设备时序均正确的保证。

转换器后续实际调用本地 `resolve_default_stream_markers`。两版所读完整函数只处理 `air` 的 record_on_stream、wait_on_stream、stream_wait_stream、scope_enter 四个白名单目标及其直接位置参数中的标记字符串；不递归列表或 kwargs，也没有将 `npugraph_ex` 目标加入白名单。需要解析时，两版都在图入口新插 current_stream/getattr/str 节点，不采用独立主线后来的标记节点复用机制。

因此不能只因 scope 参数列表中出现默认流标记，就断言这里已经递归替换了它；也不能把主线高接口换 namespace 的分支自动纳入该白名单。改写时多处赋值为没有 `.default` 后缀的 OpOverloadPacket，而白名单元素使用 `.default`；中间转换是否将 target 归一化也需核对，不能以同名自动保证命中。默认流机制的通用概念可参照[独立包卡](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)，本段仅绑定集成两版的实际函数与调用，未重新审计其余 scope 消费者。

诊断应保存实际 mode、接口分支、改写前后 target 的 namespace、三项参数的实际类型、tag 与缓存所属模块、流栈结束状态和标记解析结果。分别检查“图是否改成预期操作”“操作是否由期望实现注册”“缓存是否为同一对象”，再评价多流执行结果或性能；本卡没有运行验证、支持矩阵或收益数字。

## Evidence

- [固定集成实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/replace_stream_event.py)（primary）：1–385；完整本地改写模块，外部被调实现独立。
- [固定集成实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/replace_stream_event.py)（implementation）：1–331；完整本地改写模块，外部被调实现独立。
- [固定集成实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：57–57、1098–1100；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：58–58、935–937；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py)（implementation）：576–586、1331–1427；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/graph_pass.py)（implementation）：579–589、1359–1447；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：320–324；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：298–301；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_tagged_event.py)（implementation）：10–10、21–28、253–277；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_tagged_event.py)（implementation）：10–10、21–28、240–260；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_lib.py)（implementation）：1–3；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
- [固定集成实现 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_lib.py)（implementation）：1–3；仅准确入口、解析器、注册或缓存边界，不提升所在模块或外部执行体资格。
