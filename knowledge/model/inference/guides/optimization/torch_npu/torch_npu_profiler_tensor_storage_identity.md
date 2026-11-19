---
type: Guide
title: Profiler内存身份关联：指针复用、分配周期与Tensor标签
description: 解释EventTree如何从指针/设备和释放事件生成allocation_id及tensor_id，区分TensorImpl、共享存储、Unknown与跨窗口身份。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: implementation
created_at: '2026-11-10T13:42:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler内存身份关联：指针复用、分配周期与Tensor标签

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的EventTree身份恢复及MemoryProfile直接消费者，并对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的选定方法。所比13个方法AST相同，不推定完整事件建树、PythonTraceParser、采集器或两版全部归因相同。平台未知，保持draft、空平台；没有执行上游或解析采集数据。

## 身份恢复位于分类之前

MemoryProfile先构造EventTree，再从其root节点建立DataFlowGraph和分类表。EventTree取TorchOp、内存和PyCall事件，按start_time_ns排序，调用build_event_tree、calculate_unique_id，最后validate_events。这里的id由本次分析生成，不是设备全局对象编号，也不能跨进程、rank、采集窗口或重新解析持久复用。

身份会影响[内存类别推断](../../../../training/guides/torch_npu_profiler_memory_category_inference.md)和[时间线事件累计](torch_npu_profiler_memory_timeline_event_accounting.md)：相同指针字符串、相同算子名字或相同Tensor形状都不足以认定同一生命周期。原生内存快照和OP_MEMORY另有各自观测合同。

## 元数据和进入身份表的事件

所读Tensor字符串schema恰有八项：TensorImpl地址、storage ptr、dtype、dtype_size、sizes、strides、device_type、device_index。项数不符返回None；空ptr字段变成None，整数转换失败不在该函数中自行补默认值。该schema没有独立storage_offset项，不能据此宣称已恢复任意view地址范围。

get_tensor_info按事件顺序扁平化：

- TorchOp：读取直接Tensor输入或Tensor列表输入，不是只取算子输出名字。
- Allocation：取ptr/设备及共享的id引用，不带TensorImpl；是否free以alloc_size<0判断。
- PyCall：从module或optimizer参数、grad及optimizer state元数据提取Tensor。key为None或该key已处理则跳过这一身份表输入步骤；不把它解释成每次调用都会重新关联所有状态，也不据此否定后续分类器还会遍历PyCall。

fetch_allocation_events排除data_type=BLOCK_FREE的内存事件，其余所读记录进入建树；这与[OP内存配组](torch_npu_profiler_op_memory_pairing_and_attribution.md)的NPU/内部分配器生命周期准备层不同，不能混用两层过滤条件或把BLOCK_FREE再算一次Tensor释放。

## allocation_id按指针、设备和free切分

calculate_unique_id先维护`storage_map[(ptr,device_type,device_index)]`。某键首次出现就分配递增allocation_id，写回当前元数据/分配事件持有的id引用；若当前是free，写回后立即从storage_map删除这个键。以后同ptr/设备再次出现会得到新allocation_id。

因此，同一观察周期内相同storage ptr与设备的记录可关联在一起；观察到释放后的同址复用则被切开。算法没有按TensorImpl相等去切换allocation_id，也没有把pid、stream、dtype、shape或stride加入该键。不能只用ptr跨设备合并，也不能把混入多进程的数据交给这张映射后假定已区分进程身份。

如果采集缺少free，后续同址记录可能沿用旧allocation_id；窗口起点只有一次free也会先获得一个id再移除键。这里描述的是所采事件上的关联，不是底层分配器完整历史的证明。时间排序只显式以start_time_ns为键，不增加“同时间总是malloc先于Tensor元数据”等未写出的次序保证。

## tensor_id在此实现中由allocation_id派生

下一步收集至少出现过`impl is not None`元数据的allocation_id，只为这些周期建立tensor_id映射；仅见内存事件而没有对应Tensor元数据的周期仍可有allocation_id，却没有tensor_id。过滤的是局部扁平化列表，已写回原事件的allocation_id不会因此被清掉。

映射具体为`id_map[allocation_id] = counter`，再把tensor_id写回该周期的记录；不是把真实TensorImpl数值当tensor_id，也没有在所读循环中按TensorImpl建立跨分配周期的并查关系。共享同一所见storage周期的不同TensorImpl/shape/stride记录可能获得同一个分析tensor_id；free后重用同址则属于另一周期。不要将“tensor id”这个名字或注释当成已恢复全部Python Tensor对象和别名语义。

TensorKey._make要求tensor_id、allocation_id和ptr都非None，并加入device_type/index。缺任意项则不能构造TensorKey；分类表对只有DeviceKey的项返回None，即Unknown。分配事件缺tensor_id不等于没有内存占用、零字节或已证泄漏，后续事件累计可保留无法归类的分配。

## 完整性检查和诊断边界

validate_events检查事件起止时间、部分TorchOp输入和PyCall参数结构；所读错误分支打印错误并return，没有在这里统一抛异常、修复id或回滚建树。该检查在身份关联之后执行，不能仅凭构造返回或图导出成功认定采集完整；更早的解析/关联函数也可能因不合法元数据抛错，不能把打印分支误解为所有错误都会容错继续。

诊断类别或显存曲线变化时，先固定设备/进程、采集窗口及元数据开关，再检查ptr是否缺失、free是否覆盖、是否具有Tensor元数据、同址是否跨周期复用；保留allocation_id与tensor_id的区别。随后按具体TensorKey版本解释类别迁移，避免把模型对象个数、分配周期数和时间线字节数混为一项。

本卡只覆盖所选身份分配与直接消费链，未完整审阅线程/前向反向父子关系、Python tracer key生产、所有参数字符串解析、schema匹配或运行时别名。未执行正确性、内存或性能实验，也不从静态规则给出新的产品支持。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py)（primary）：主线定向范围 18–59, 84–147, 189–221, 241–318, 434–535, 554–615。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py)（implementation）：发布版选定方法AST对照范围 124–147, 434–481, 487–520, 282–296, 300–318, 524–535, 554–565, 581–608。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)（implementation）：主线定向范围 114–142, 574–591。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)（implementation）：发布版选定方法AST对照范围 124–128, 135–138, 131–132, 574–582, 586–599。
