---
type: Guide
title: Inductor 并行调度消费者：分组回退、事件汇合与缓冲作用域
description: 核对固定主线的 Python wrapper 门控、CV 分组阈值、环境字符串缺陷及完整的主从流事件和缓冲生成路径。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallel_scheduler_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_framework.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_cv.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/schedule_node_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.md
  role: constraint
created_at: '2026-11-10T11:18:21Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor 并行调度消费者：分组回退、事件汇合与缓冲作用域

## 版本与适用边界

定向审阅 PyTorch/TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中并行调度的关键门控、默认 CV 策略及 Python wrapper 的相关分配/释放片段。未执行、导入或修改上游，也未验证设备；整卡 `draft`、空平台。发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 不含主源 `torch_npu/_inductor/fx_passes/parallel_scheduler_pass.py` 这一路径，以下不作为发布版行为保证。

固定说明仍限定推理、图下沉、950DT 和 PyTorch 2.9 示例，详见[文档层并行调度指南](torch_npu_inductor_parallel_schedule.md)。源码某个局部门控没有再次检查这些条件，不能据此扩展训练或产品支持范围。本卡补充文档片段未展示的回退、事件汇合与缓冲生成，不重写支持表。

## 开关通过后仍有多次回退

初始化中只有 `ENABLE_PARALLEL_SCHEDULER` 转小写后等于 `true` 才安装 `Scheduler._codegen` patch。真正生成时，`is_multi_stream()` 还要求 wrapper 是 `NPUPythonWrapperCodeGen`；否则调用原始 codegen。因此 `1` 不启用，也不能用相同配置推导 C++ wrapper 会走此实现。

`ParallelGroupingStrategy.execute_strategy()` 在默认情况下，节点总数不大于 20 时返回空组。CV 策略还会挑选连续的 Cube/Vector 段，并检查选定段端点的依赖；任一组按展开 fused node 后的计数少于 `20 // 5 = 4`，则清空并行两组。最终生成器要求至少三个组，且每组非空；否则继续调用原始 codegen。

因此不止 Cube/Vector 需要非空：如果 MAIN 为空，也会回退。`cv parallel group len: 3` 表示返回字典含三个键，后面仍须看每组节点列表和生成物，不能单凭这个数字断言多流已生效。

节点计数也分层：总体阈值比较传入的 `len(nodes)`；组内最小值使用 `calculate_group_len()` 展开 fused node 的 `snodes` 数。不要将两个阈值都解释为原始 FX 算子数量。

## 固定版本的阈值环境字符串缺陷

两个消费者分别使用：

```python
parallel_scheduler_nodes_min = os.environ.get("PARALLEL_SCHEDULER_NODES_MIN", 20)
if len(nodes) <= parallel_scheduler_nodes_min:
    ...

sub_nodes_min = os.environ.get("PARALLEL_SCHEDULER_NODES_MIN", 20) // 5
```

默认值 `20` 是整数；显式环境变量值则是字符串，这里没有 `int()` 转换。根据这两段表达式，显式设置包括 `"20"` 在内的字符串，会在走到相应比较或整除时产生类型不匹配。这是静态源码判断，未运行上游复现，也未在本任务修复上游。

因此本 revision 的这个内部环境项不能当作已验证可用的阈值调优接口。仅调低阈值就尝试加速的建议还会忽略分组、同步与缓冲开销；先按实际版本确认该解析是否已修复。

## 从主流分叉，并在结束前汇合

生成器先取 `torch_npu.npu.current_stream()`，在该流记录 `main_event`，为每个非 MAIN 组建立 Stream 和 Event。进入组流 context 时等待这个 `main_event`。离开当前组流时记录其完成 event；切回主流时等待尚未等待的组 event；若最后一个节点仍在组流，结束时也记录完成 event。

尾部遍历非 MAIN 的 event，使主流等待所有尚未等待的并行组完成，然后才结束设备 guard 并 flush。等待逻辑表明生成器包含结束汇合，不能把文档只展示开头的片段当成完整流生命周期。

这些 event 是固定生成代码的依赖结构，不是任意自定义分组正确性的证明。初始 `main_event` 在生成的分流序列前记录；若修改策略或插入额外主流生产者，必须重新核对生产到消费的真实先后，不能只看“有 wait_event”。实际并行重叠仍需设备时间线证明。

## 缓冲分配、释放和工作区也携带流作用域

`pre_node_multi_stream_flag()` 将对应的 `*.npu_stream` 写入节点及组成子节点。`build_buffer_producer_group()` 追踪输出所属组，生成器可在进入组 context 前预分配其缓冲；wrapper 的 `pre_define_buffer` 防止重复分配。Concat 的输入/输出还存在专门的归组处理，不能只按某个 Kernel 的名字推导整个缓冲生命周期。

`build_multi_stream_buf_intent()` 为输出定义、外部节点参数和 `last_usage` 记录缩进位置；`make_buffer_free()` 根据这些信息生成相应作用域的 `del`。workspace 的 allocation/deallocation 也从 origin node 传递作用域；最终 wrapper 还扫描子流 context 调整释放相关映射。这些是代码生成和内存规划的配套路径，不等同于本卡已核验所有 allocator 与 record-stream 行为。

定位性能或数值问题时应连同实际 wrapper 一起检查：各组内容、首次等待、生产者所在流、完成 event、消费前汇合、分配和 `del` 的位置。只有分组日志，没有实际产物和时间线，无法判断是否减少串行或增加了同步成本。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallel_scheduler_pass.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_framework.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_cv.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/schedule_node_utils.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.md)（constraint）
