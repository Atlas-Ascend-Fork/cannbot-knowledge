---
type: Guide
title: GE多流依赖：延迟控制边与scope归属
description: 解释GE record/wait控制边的暂存与首次附加、scope嵌套标签选择，以及空Tensor快捷路径的实际版本差异。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_scope_attr.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/_scope_attr.py
  role: implementation
created_at: '2026-11-11T10:53:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE 多流依赖：延迟控制边与 scope 归属

GE 转换路径把 `air.record/wait` 表达成图内控制边：record 返回当前流已记录的最后一个 GE 算子的 controller，wait 暂存这些依赖，到当前流下一次产生 GE 算子时才附加。它与[独立 npugraph_ex 的 Event 生成与回放](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)属于不同执行路径。

本卡静态对照固定主线 `92e1e967`、固定发布 `7c6c754b` 的局部转换、四个控制边消费者与 scope 属性栈；没有执行图改写、生成器、Event/Stream 或设备实验。

## 分派顺序与控制边生命周期

| 阶段与条件 | 本地行为 | 成本与正确性核对 |
| --- | --- | --- |
| target 字符串精确为 `air.scope_enter.default` / `scope_exit.default` | 先以 `need_execute=True` 调用 target 并返回 | 这条特殊分派先于后面的空 Tensor 优化 |
| `air.record.default` | 查当前流的 GE op 顺序表；非空返回最后一个 op 的 `ControlTensor(...).controller`，为空返回 `no_op_before_record` | 本地分支没有创建设备 Event；记录的是已纳入顺序表的 op |
| `air.wait.default` | 遍历 args[0]，收集非哨兵字符串；GeTensor 则取其生产者的 controller；追加到当前流的待用列表并返回 None | 其他类型不加入；不在这里去重或把控制字符串变成设备同步调用 |
| 普通转换成功且产生新 GE ops | 将 `graph.op[num_ops:]` 全部登记到当前流顺序表 | 记录范围是这个转换切片，外部装饰器产生的辅助节点另计 |
| 当前流有待用控制边且本次 ops 非空 | 只把整批依赖追加到 ops[0].input，随后清空该流待用列表 | 不是给本次每个 op 都重复加边 |
| 本次 ops 为空 | `_handle_wait_control_edge` 直接返回 | 待用依赖保留，继续等待后面的有 op 转换 |

两版构造函数都在图对象上建立按流键索引的 defaultdict(list)，分别存 op 顺序和待用边。所列消费者没有对“wait 后再无 GE op”的情况另做尾部 flush；不能把 Python wait 调用返回等同于依赖已经附到了最终输出，也不能只看 FX 节点数量推导新增 GE 控制边数量。图中其他引用复制与副作用排序规则见[GE 引用与排序](torchair_ge_reference_copy_and_ordering.md)。

主线通常由 `parse_node` 在 record_asc_ir=False 时进入 `_parse_node_internal`，发布由 parse_node 本体处理同样的 record/wait 分派。本卡没有展开主线 IR 诊断 mock 路径或外部 guard_view_input 实现。

## scope 标签的两种取法

`guard_scope_attr` 在进入转换时，将线程局部 ScopeAttrs 的列表交给图对象的 scope_attr_ctx；转换后对新增 GE ops 调用属性应用。ScopeAttrs.push 向列表末尾追加，pop 弹出末尾，scope_attr_info 返回该列表引用。图对象的 scope_attr_ctx 退出时将其线程局部字段置为 None，没有在这里恢复进入前的字段值。

| 用途 | 标签/属性选择规则 |
| --- | --- |
| `_get_current_stream` 给 op 顺序和待用边选键 | 按列表正向查找，返回首个带 `_user_stream_label` 的字典中的值；没有则返回 None |
| ScopeAttrs.apply 写入 GE op 属性 | 按栈顺序逐层写同名属性，后层写入可以覆盖前层 |
| 普通属性 | 将值转成字符串，再经 compat_as_bytes 写入字符串字段 |
| `_op_exec_never_timeout` | 两版都按值是否精确等于字符串 `True` 写 bool |
| `_enable_inner_parallel` | 主线也按上述规则写 bool；发布这个分支只特殊处理前一键，所以该键走普通字符串写入 |

当栈中嵌套两个不同的 `_user_stream_label` 时，控制边记账可以使用外层首个标签，而最终 op 属性采用后写覆盖的内层标签。这里两种选择规则确实不同，应同时检查记账键与落到 op 上的标签；尚未执行设备复现。空 `_super_kernel_scope` 另触发本地属性移除 helper，helper 本身不在本组新增审阅范围内。

## 空 Tensor 快捷返回的版本差异

record/wait 的特殊分派先于空 Tensor 判断。普通节点会先 flatten meta；满足“每个输出均为无符号的零元素 Tensor”且 target 不在本地例外集合时，调用 make_real_tensor_like 后提前返回，不走后面的 converter 与控制边附加。

| 条件 | 主线 | 发布 |
| --- | --- | --- |
| flatten 结果为空 | 额外要求 bool(flat_meta_outputs)，因此该快捷条件为假 | 直接 all(...)，空集合的结果为真 |
| 禁止该快捷处理的精确 target | reduce_scatter_tensor_uneven、all_to_all_single_npu、allgather_in_tensor_uneven，以及 `_recv`，均在 `npu_define.*.default` 下 | 同前三项，没有此处的 `_recv` 项 |
| 未提前返回且原标志为 False 时的 `_has_empty_tensor` 判断 | 同样要求 flatten 结果非空才判全零 | 对空 flatten 使用 all(...) |

这限定了本地优化准入，不代表所有无 Tensor 输出或通信操作都走同一条路。快捷返回或零 op 转换不会在上述消费者里消耗待用边；分析重叠执行时，应把原 FX 节点、实际生成的 GE ops、流标签及控制输入一起核对。

排查顺序：先确认精确 target 与快捷分支，再检查 record 对应的末 GE op、wait 缓存键、下一批 ops[0] 收到的控制输入，以及最终 op 的 scope 属性。源码中的这些列表与属性写入没有给出实际设备耗时或并发收益。

## Evidence

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（primary）：118–118、258–263、1158–1160、1722–1786、1788–1797、1940–1946、2116–2158。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：64–64、163–167、933–935、1390–1450、1550–1556、1716–1756。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_scope_attr.py)（implementation）：1–76。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/scope/_scope_attr.py)（implementation）：1–76。
