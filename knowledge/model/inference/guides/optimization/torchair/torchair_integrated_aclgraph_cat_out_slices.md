---
type: Guide
title: 集成 AclGraph 的 Cat 消除：out 切片写入与改写边界
description: 解释集成Cat消除的实际开关、schema准入、共享输出分段写入、普通用户迁移和动态shape失败后的图状态。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/cat_optimization.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/cat_optimization.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py
  role: implementation
created_at: '2026-11-11T10:23:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成 AclGraph 的 Cat 消除：out 切片写入与改写边界

本卡审阅固定主线 `92e1e967`、固定发布 `7c6c754b` 中 `python/torchair/_acl_concrete_graph/cat_optimization.py` 的完整本地模块，以及集成转换器的实际开关调用。两版模块完整 AST 相同，原始差异为格式与检查注释；没有导入上游、执行 FX 改写、shape 表达式、算子或设备测试。本机制与[Inductor AscendC 的 Cat/View 融合](torchair_inductor_ascendc_cat_view_fusion.md)属于不同路径。

## 开关与目标图形

集成转换器在 `self.config.debug.aclgraph.remove_cat_ops` 条件成立时，调用 `optimize_cat_with_out_tensor(self.fx_graph)`。配置默认 True；这是实际 Python 图优化调用，而非依靠序列化出的编译字符串触发，配置包装器协议见[配置与模式消费者](torchair_grouped_config_serialization_and_mode_consumers.md)。该 pass 的 `config` 形参在本地函数体没有被消费。

pass 只收集 `call_function` 且 target 精确等于 `torch.ops.aten.cat.default` 的节点，没有对所有名称含 cat 的操作统一改写。没有 Cat 时直接返回；有 Cat 时先调用外部 `add_stream_label_to_node_meta`，再逐个验证。

| 本地准入检查 | 准确边界 |
| --- | --- |
| 输入张量集合 | `cat_node.args[0]` 必须为至少两个元素的 list/tuple；没有仅靠关键字 `tensors` 的读取分支 |
| 拼接轴 | 从第二位置参数或 `kwargs['dim']` 取得，必须通过 `isinstance(dim, int)` 且等于 0；不把其他等价轴归一化为 0 |
| 输入与输出元数据 | Cat 必须有 `meta['val']`；每个输入必须为有 `val` 的 `call_function` FX Node |
| 生产者 | 必须找到匹配的 out 重载；输入若还被集合内另一个 Cat 使用，则拒绝本 Cat |
| 输入 shape | 相邻输入 rank 一致，除第 0 维外逐维相等；没有在这里独立验证所有输入 dtype/device、有效 rank、输出 shape 总和或重载的运行时适用条件 |

“被共享”检查仅针对本轮仍在 `cat_node_set` 中的其他 Cat，不禁止普通非 Cat 用户，也不专门去重同一 Cat 中重复出现的生产者。不要将它简化为“只有单用户纯算子才会入选”。

## out 重载按参数名和类型匹配

`_get_out_variant` 要求目标有 `_overloadpacket`，从原 schema 中去掉名称为 `out` 的参数，保留其余参数的 `(name, str(type))` 有序列表。随后枚举 packet 的重载，候选必须包含名为 `out` 的参数，且去掉它后的列表与原列表完全相同，取第一个匹配者。这可以区分维度名称与整数维度等不同类型的重载；不是简单地假定 `packet.out` 总正确。

原目标没有 schema 时，局部 fallback 才直接取 packet 的 `out` 属性。比较没有另外覆盖参数默认值、keyword-only 标志、返回结构、alias/可变性合同或具体设备实现；找到 schema 候选不等于这些语义已经验证。创建节点时再次查询重载，复制原 kwargs、写入 `out=slice_node`，保留原 args，并把原节点的 meta 更新到新节点；如果再次查询得到 None，代码仍以原 target 配合这个 out 关键字建节点，没有在此统一改走别的算法。

## 一块输出与每个生产者的切片

pass 按原图顺序找到最早的输入生产者，把一次 `aten.empty.memory_format` 分配插在它之前。分配使用 Cat 输出 meta 的 shape、dtype、device，显式 `pin_memory=False`、`memory_format=None`，不是无条件对原有输出 Tensor 做原地重用。

静态首维尺寸转换为 int；若输出 meta 含符号，则先从图的标量符号 placeholder 建立表达式到输入节点的映射，并调用外部 `construct_fx_node_shape` 构造输出 shape 或各输入首维尺寸。这个局部映射不主动从每个 Tensor placeholder 的所有维度建立任意符号来源。外部 shape 构造器、全局表达式缓存及其运行行为未由本卡重新资格化。

解析完各输入首维大小后，按 Cat 输入顺序累加 offset。常量直接相加，动态情况插入 `operator.add`；为每个生产者创建第 0 维 `[offset, offset+size)` 的 `aten.slice.Tensor`，再让对应 out 重载写入该 slice。整体意图是用共享输出的分段写入替换中间结果再拼接；这里没有实测内存峰值、算子次数或延迟收益，也不证明任意 out 实现都避免额外分配。

若 Cat 有 `stream_label`，代码只在这次 empty 分配两侧插入 `air.scope_enter/exit`；新输出节点记录该 label，新的 out 节点复制各自原生产者的 meta。这段代码本身不证明所有生产者同流、没有跨流依赖，或其他 pass 的 Event 同步已经验证。

## 全部 uses 迁移与失败后的图状态

每个输入生产者与新 out 节点记录在以旧 Node 为键的 `replacement_map` 中；之后对旧生产者调用 `replace_all_uses_with(new_node)`，并把 Cat 的全部 uses 改成共享输出。这包括准入时没有排除的普通非 Cat 用户。新节点复制旧 meta，没有在这里重算所有下游 alias、stride 或外部观察关系，因此不能仅凭 shape 检查断言普通用户的存储关系均保持不变。重复输入还会覆盖该字典同键的前一次映射，源码没有独立的重复生产者去重或成本保证。

旧 Cat 和旧生产者只在已经没有 users 时清理 meta 并 erase；不会据此删除所有新建的无用节点。只要 `optimized_count > 0`，尾部才执行 `gm.graph.lint()` 与 `gm.recompile()`。这些是上游 pass 将执行的调用，本次摄取没有运行它们，也不将 lint 当成数值、alias 或设备合法性证明。

本函数没有围绕全部改写建立 try/rollback。动态输出 shape 的辅助节点可能已经插入，随后某个输入首维尺寸无法解析，才以 `continue` 放弃该 Cat；这里没有撤销前面插入的辅助节点。如果最终没有成功优化任何 Cat，尾部也不会因此自动 lint/recompile。其他 schema、meta、形状比较或构图异常同样不能从本地代码推成“总是保留原图并安全回退”。外部调试装饰器只按已存在的调用记录，不由本卡扩大为事务保证。

诊断时对照开关、精确 target、out schema、非 Cat 用户、重复输入、符号来源、生成的 empty/slice/out 节点及 pass 结束状态，再核对实际结果和内存变化。不要仅以 Cat 节点消失推断所有中间内存被消除，或把这里的局部准入作为全产品支持矩阵。

## Evidence

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/cat_optimization.py)（primary）：1–240；完整本地模块与全部局部定义，外部被调实现另计。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/cat_optimization.py)（implementation）：1–253；完整本地模块与全部局部定义，外部被调实现另计。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：251–256；实际开关或默认声明的有界证据，不提升其整模块资格。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：239–243；实际开关或默认声明的有界证据，不提升其整模块资格。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py)（implementation）：88–88；实际开关或默认声明的有界证据，不提升其整模块资格。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py)（implementation）：88–88；实际开关或默认声明的有界证据，不提升其整模块资格。
