---
type: Guide
title: Profiler事件重建：Python栈重放、参数解析与跨线程父子关系
description: 核对Python tracer重放和EventTree完整本地定义，区分缺失return、线程作用域、参数字符串错误与内存身份关联。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_python_trace_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_python_trace_parser.py
  role: implementation
created_at: '2026-11-11T04:51:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler事件重建：Python栈重放、参数解析与跨线程父子关系

## 固定版本与两个重建阶段

本卡完整审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的PythonTraceParser与EventTree模块。两对整个AST相同，全部原始差异仅行尾空白，已逐行核对，保留注释/docstring；不推广到其他Profiler模块。平台未知，保持draft，没有导入上游、反序列化模型、解析真实采集或设备实验。

第一阶段按Python tracer记录重放栈，生成带开始/结束和分析ID的PyTraceEvent；第二阶段EventTree将TorchOp、内存与PyCall合在一起恢复父子关系，再分配内存身份，最后做局部验证。TraceEventManager、ID编码器、采集器及内存分类消费者仍独立，现有[Tensor/Storage身份](torch_npu_profiler_tensor_storage_identity.md)继续解释allocation_id与tensor_id，本卡给出重放、参数schema和建树条件。

## Python栈按TID分桶，return只弹栈顶

TraceTag仅0 Py_Call、1 Py_Return、2 C_Call、3 C_Return；CallType仅0普通Py、1模块Py、2 C调用，没有注释中提到的独立OptimizerCall枚举。构造Parser保留三类输入引用，hash/param字典初始为空；生成时字典推导式对重复key保留最后值。找不到hash时显示str(key)，不直接丢事件。

_group_trace_data_by_tid只以TID分组，没有PID。每桶按start_ns排序，稳定同时间顺序取决于原记录；各桶独立重放，不做跨桶时间归并。ID用该桶每条记录的enumerate下标，包括return/未知tag造成的空档，不能当跨进程或全局唯一调用ID。

Py_Call与C_Call分别压ReplayFrame；任一种Return只在非空栈时关闭当前栈顶，不核对Py/C类型、key或调用名是否对应。空栈Return被忽略；其他tag不压/弹，但仍推进event_idx和最大时间。没有真实return的栈帧在末尾统一用该线程**最后观察到的记录时间**补结束，逐个弹出，不能将该补值当作实际函数返回或真实持续到采集窗口终点。

ReplayFrame先用end=-1、parent=None、return_idx=0占位，暂存父frame ID。结果按弹栈/完成次序输出，之后通过本桶id_map写parent_id；找不到父事件用0。0同时可作为首条call的self_id，不能据单个0区分所有身份语义。PyTraceEvent的时间/名称/PID/TID/params和self_id getter直接返回内部值，end、return_idx、parent_id setter直接赋值，没有校验非负时长、线程一致或重建完整性。

## 模块与参数不是Tensor恢复

名称含`######`就按分隔符拆成module_name和module_uid，exact解包两段，多分隔符会失败。每线程重放内按模块名计数、按UID查重，重复UID复用其编号；不是跨线程/窗口的模型模块全局ID。模块显示名为`nn.Module: <name>_<id>`，args给Python id/parent id并额外给module id；普通Py/C名字保持原样。

get_python_trace_data把重放事件交TraceEventManager生成python_function X事件，顺手为tid_dict不存在的TID记False；get_python_trace_api_data构造11槽API记录，开始/结束均用Py事件ns，PID/TID交contact_2num、名字交字符串ID，最后为PYTHON_TRACE，其余槽None。两入口都未调用_gen_param_map；只有get_pycall_data先加载参数字典，再重放并返回对象。是否有采集参数文件和此入口的选择共同影响后续EventTree参数，不应把文本/API导出成功当已恢复模型参数。

ParamTensorBean先按`}`拆外层列表；本模块再按以下字符串schema解析，没有执行真实Tensor构造、地址解引用或设备复制：

|解析入口|本地规则与缺失处理|
|---|---|
|parse_tensor_metadata|`;`拆成恰好8项：TensorImpl十六进制、storage ptr十六进制或None、dtype字符串、dtype_size整数、逗号分隔sizes、逗号分隔strides、device_type整数、device_index整数。空sizes/strides为空列表；项数不符None；整数错误直接传播，没有storage_offset字段或sizes/strides等长检查。|
|parse_input_from_string|types按`;`加CRLF切，Tensor片段按`)`、TensorList按`}`、Scalar按`;`。除None/Scalar/ScalarList/TensorList标记外均按Tensor元数据解；Scalar保存字符串，None与ScalarList保存该类型标记，不解出数值列表。独立下标越界get_str_from_list给空字符串，可能继续得到None；TensorList内项也可能None。|
|parse_module_param|按`)`恰好3项：name、Tensor元数据、可选grad；项数不符None。|
|parse_optimizer_param|按`)`恰好3项：Tensor、可选grad、可选state；无state为空列表。|
|parse_state_param|按`]`拆非空状态，再以`>`恰好2项拆name/Tensor；坏项数整函数None，不校验内部Tensor结果非空。|

_TensorMetadata保存字段与可变_IDReference；id getter委托这个共享引用。_ModuleParam/_OptimizerParam只是相应字段容器。_ExtraFields_PyCall保存name/end/key及参数：有module_params时优先解析module，只有其为假才考虑optimizer_params，二者不会在该分支同时装填；空字段保持None。错误结构不一定被后面的validate捕获，见下文。

## EventTree对齐线程与结束边界

_ProfilerEvent按Bean类型选择TorchOp/Allocation/PyCall，保存TID和开始ns、可变parent/children以及finished=False，不另存PID作树键。Torch额外字段为name/end/scope/forward_tid/sequence及解析后的inputs；内存额外字段含原始字节alloc_size、active/allocated/reserved、ptr/设备和共享id；内存结束等于开始，名称固定[Memory]。PyCall用重放end和参数。对象小于比较只看end_time_ns，供结束优先队列使用，不定义更强的同刻事件优先级。

EventTree依次取Torch、内存、PyCall并合并，按start_time_ns排序；Torch数据还检查原数组相邻项：当前scope=FUNCTION、下一项=BACKWARD_FUNCTION且当前名以autograd::engine::evaluate_function:开头，才把下一项sequence/forward_tid复制到当前。这里不是按全局sequence搜索任意最近反向事件。RecordScope其余枚举只登记编号，不在这一步自动分类；设备编号CPU0/CUDA1/NPU20也不是本模块新增硬件支持证明。

内存只排除data_type=BLOCK_FREE（2），不是只取NPU、只取内部allocator或只按alloc_size正负过滤。Python参数入口使用get_pycall_data，hash/函数/参数分别从对应framework tag读取；这一层即使缺hash也可由key名字回退，与FwkFileParser文本要求hash+函数同时存在不同。

build_event_tree维护TID当前事件和按end排序的PriorityQueue。新事件前，仅弹出`old.end < new.start`的结束事件，**相等时仍留在当前父链**；不能默认它是所有区间都end-exclusive的标准树。push_event优先同TID当前事件，没有时对Torch取truthy forward_tid对应线程作parent（缺省-1也不是自动被当False），其他事件不做前向线程回退。parent存在就append child。

正时长事件更新当前TID并入结束队列，零或负时长立即mark_finished；起止合法性要到构造末尾才检查。push若已有parent、未完成child或重复finished就打印错误并返回False；pop沿当前parent链依次mark_finished直至目标，找不到当前事件或链断也打印False，再恢复目标parent为该TID当前。build遇False直接return，没有统一抛错、回滚或返回完整性标志；随后EventTree构造仍继续calculate_unique_id与validate_events。get_root_nodes只是从已排序事件中选parent=None，并不证明树成功覆盖全部事件。

## 身份分配与验证的先后顺序

get_tensor_info扁平化Torch直接Tensor/列表、内存分配/释放、首次见key的PyCall参数/grad/state；内存free以原字节alloc_size<0判断。storage键为(ptr,device_type,index)，free写回allocation_id后移除键；出现过TensorImpl的周期才派生tensor_id，ID共享写回事件和元数据。该算法没有把PID、dtype或shape加入storage键，也没有按TensorImpl建立跨分配周期身份；详细失效边界见原[身份指南](torch_npu_profiler_tensor_storage_identity.md)。ptr=None也没有在这里先过滤，不能把缺地址的关联当已证真实共享存储。

validate_events最后才检查start>end、Torch inputs顶层None、PyCall的模块/优化器参数冲突、空模块参数对象以及空optimizer对象/state。它不逐项保证TensorList内部、p.tensor、grad/state Tensor有效；get_tensor_info更早就会访问这些内部对象，可能先AttributeError/TypeError。只看到某些错误分支print后return，不能推广成所有坏元数据都容错继续。

分析内存类别或Python调用耗时时，先保留完整记录、每线程边界、缺失return补齐、同刻次序、是否进入参数入口和原始schema，再解释父子关系与ID。静态可恢复字段不等于模型对象数、真实线程执行时间、采集无丢失或设备性能收益；下游[内存类别](../../../../training/guides/torch_npu_profiler_memory_category_inference.md)和[时间线累计](torch_npu_profiler_memory_timeline_event_accounting.md)仍受各自条件约束。

## Evidence

- [ac0e156 _python_trace_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_python_trace_parser.py)：完整本地模块1–240。
- [ac0e156 _event_tree_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py)：完整本地模块1–615。
- [f3ecfe4 _event_tree_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_event_tree_parser.py)：完整本地模块1–615。
- [f3ecfe4 _python_trace_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_python_trace_parser.py)：完整本地模块1–240。
