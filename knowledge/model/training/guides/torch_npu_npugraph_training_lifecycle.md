---
type: Guide
title: NPUGraph Tree 训练代际：待反向传播、输出克隆与梯度累加边界
description: 对照固定主线和发布版实现，解释训练中何时允许结束 Tree 路径、存活输出如何跨代迁移，以及梯度缓冲为何需要独立处理。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree_state.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_graph_tree.py
  role: implementation
created_at: '2026-11-10T11:14:37Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# NPUGraph Tree 训练代际：待反向传播、输出克隆与梯度累加边界

## 版本与审阅范围

定向审阅 PyTorch 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Tree manager、用户可见输出迁移和标记状态，并对照发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 对应训练代际路径。没有读取完整 Tree、运行模型或验证软硬件组合，整卡保留 `draft`、空平台。两个 revision 分开描述，不能将主线新增的输出保护当成发布版能力。

[Tree 与静态地址总览](../../inference/guides/optimization/torchair/torchair_inductor_ascendc_graph_tree.md)已解释分区、地址与输出寿命；本卡补充它明确未覆盖的训练状态转换。

## pending backward 是布尔保护，不是未完成反向的计数器

两版 `run()` 都先执行 `_run()`，成功返回后才根据编译模式更新状态：`FORWARD` 将 `running_forwards_with_pending_backwards` 置为真，`BACKWARD` 将其置为假；`set_to_running_backward()` 也会清除该状态。**一次 backward 调用即可清除这个布尔保护，不代表所有 forward 都逐一完成 backward。** 源码注释明确选择此近似，因为部分 forward 可能永远不执行 backward。

它保护 `mod2(mod1(x)).sum().backward()` 这类多个 compiled forward 相连的情况：中间的 Dynamo generation 变化不能单独证明上一训练轮已结束。它也不是 autograd 就绪检测器或梯度累加完成证明。

`can_start_new_generation()` 的实际判断顺序为：

1. 当前 generation 与 manager 记录值不同，否则返回假。
2. 若显式使用过 step 标记，则允许新代。
3. 否则要求没有 pending backward。

主线从独立 `_graph_tree_state.py` 读取 `MarkStepBox`；发布版将相同的计数状态和标记函数定义在 `_graph_tree.py` 内。计数非零时取显式负数标记，否则取 `GenerationTracker.generation`。上游 Dynamo generation 增量实现不在本卡范围，因此不把 generation 等同于每次模型调用次数。

## step 标记具有强制边界含义

`torch.compiler.npugraph_mark_step_begin()` 对应标记函数每次把负计数减一。由于显式标记在 `can_start_new_generation()` 中优先于 pending backward，**不能把它当成无副作用的提速提示**。尚有依赖的 forward、backward 或相连 compiled 子图，应按真实逻辑训练轮组织边界；随意在子图之间插入标记可能让旧路径进入回收/迁移流程。

在没有新代时，recording、execution 和 warmup 路径仍可在所有输出死亡后结束。旧输出长期存活、旧 forward 需要 backward 或用户持有跨轮引用时，可能无法命中快速路径；源码警告建议检查 backward 或输出 detach，并提到显式标记。这里的 `detach()` 只改变 autograd 关系，不能推导为获得独立存储。需要跨代保存数值时，应在旧存储被覆盖前于 compiled 函数之外复制，并核对后续用途。

## 主线新增的用户可见输出跨代迁移

在主线 `add_function()` 中，调用方传入的 `user_visible_output_idxs` 被转为集合；`BACKWARD` 模式被强制清空，其他模式有非空集合时打开 manager 的克隆分支。该保护依赖上游正确标记输出，不等于任意存活 Tensor 自动受保护。

主线在 execution 匹配旧 children 之前，若发现 generation 变化且启用了上述机制，先尝试结束旧执行，避免先沿用旧代子节点。结束新代路径时会请求 `_clone_current_path_live_user_visible_outputs()`：

- 从路径中按用户可见输出的 storage group 收集仍存活的存储。
- 按存储字节数分配新的 `uint8` Tensor，并用 `_foreach_copy_` 复制整个存储，而非只复制某个 Tensor 的逻辑元素。
- 交换 storage 的 data pointer，再更新对应 weakref、Tensor 引用和缓存；旧 graph-pool 存储另行处理 deleter/访问错误标记。

这是源码的存储迁移机制，不能简化成“每次 replay 所有输出都 clone”。复制只在这些边界和已标记且存活的组上发生；长时间保留大存储或小 view 指向大存储时，迁移成本与保留的底层字节数有关，需结合真实时间线和内存观测评估。

主线诊断文本提到 `torch._inductor.config.triton.cudagraph_trees_generation_cloning = 'user_visible'`；本卡没有追完该上游配置到所有索引的生产路径，因此不承诺仅设置该值就覆盖任意返回对象、别名或梯度。

## 发布版不具备相同的跨代克隆流程

在已对照的发布版 `try_end_curr_recording/execution/warmup` 中，新代仍使用 pending-backward/显式标记判断，但直接清理路径或 weakref，没有主线上述用户可见输出迁移调用。发布版中仅持有 Python 引用，不足以得到“跨代旧值会自动保留”的保证。不要把主线的安全性或内存成本结论反向套用到发布版。

## 梯度累加需单独处理

主线 `add_function()` 明确排除 backward 输出的用户可见克隆索引；普通返回值的保护不能代替 `.grad` 缓冲的生命周期管理。主线 `format_dealloc_msg(..., is_grad_output=True)` 专门指出：`reduce-overhead` 配合梯度累加，若 `.grad` 在 capture 中分配，后续运行可能覆盖其存储。

该诊断建议在 compiled backward 捕获前于捕获范围外建立稳定 `.grad` 缓冲，例如 eager warmup 或预分配零梯度；不需要累加时则在每次 backward 前将 `.grad` 设为 `None`。这些是固定源码给出的处理方向，不是本卡实际运行过的配方；是否仍被优化器、清零方式或别名重置，需在具体训练流程中检查。

定位时同时保留编译模式、generation、标记位置、输出是否跨轮存活、`.grad` 的分配/置空时机。仅看到捕获成功，不能证明后续累加结果和跨代输出数值正确。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree_state.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_graph_tree.py)（implementation）
