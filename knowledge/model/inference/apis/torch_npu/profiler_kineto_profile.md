---
type: API
title: _KinetoProfile：手动启停、元数据与导出方法
description: 保留基础采集类与profile控制层的区别，以及JSON元数据限制的发布主线差异。
tags:
- task.lookup
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler_interface.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler_interface.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_utils.py
  role: implementation
created_at: '2026-11-09T20:03:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# _KinetoProfile：手动启停、元数据与导出方法

## 固定版本和支持范围

文档分别来自OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文；实现分别核对TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。发布组合ascend_26_0_pt28有独立配套证据，两个仓库主线提交不自动配套，不能用新参数回推发布版。

本卡平台限定A2/A3。部分OpPlugin主线接口页列950DT，但同一固定PyTorch主线原生Profiler支持页对相关入口另有明确不支持说明，且不同方法产品表并不相同；版本与命名空间冲突见[采集指南](../../guides/optimization/torch_npu/torch_npu_profiler_capture_schedule.md)，不以类级表扩展全部方法。旧Atlas条目不自动映射新型号。这里只做静态来源审阅，未导入上游、运行设备采集、解析或性能实验。


## 类级合同

两实现_KinetoProfile仅接收关键字activities=None、record_shapes/profile_memory/with_stack/with_flops/with_modules=False、experimental_config=None；主线另有custom_trace_id_callback。该参数被文档标为str，但主线实现要求无参Callable返回str。类本身没有profile的schedule/on_trace_ready/step和子线程注册接口，也没有定义trace ID setter/getter，不能因为profile继承它就反向移植方法。

start初始化采集后开始记录，stop停止并finalize；CPU活动下record_shapes记录InputShapes/InputTypes，stack记录框架/CPU算子调用，modules记录框架模块Python层次。文档称with_flops暂不支持解析性能数据；主线实现存在特定MSTX FLOPs hook，不能据此扩大为全部算子解析保证。内存采集的glibc提示见[内存指南](../../guides/optimization/torch_npu/torch_npu_profiler_memory_and_metadata.md)。

## 元数据和版本差异

add_metadata(key,value)要求字符串，两实现检查每串≤4096字符，并用getsizeof字典加本次键值大小估计小于50KiB；这不是递归统计所有既有value的严格总容量保证。同key覆盖。

发布add_metadata_json同样检查字符串长度和容量，再json.loads；主线只检查字符串及合法JSON，不保留该长度/容量判断。两者都把解析后的对象按key覆盖，不能当逐step历史。主线额外preset_metadata_json，先保存预置值、start_trace时再通过JSON添加；发布类无此方法，不能回推。

## 导出与临时数据

export_chrome_trace(output_path)要有效采集路径；发布包装显式要求.json后缀，主线包装这一检查已省略，不等于所有格式都有解析器支持。export_stacks要求with_stack=True，metric仅self_cpu_time_total/self_npu_time_total，非法值回CPU。export_memory_timeline要求record_shapes、profile_memory及stack/modules至少一项，device默认有NPU时npu:0、否则cpu；实际设备必须在所采数据中存在。

两版未配置handler且无ASCEND_WORK_PATH时采用export_only_prof_dir临时目录，析构可删除原始目录；不能保证省略handler后原始数据永久保留。需要离线解析时明确保留目录及生命周期，见[导出回调](profiler_trace_handler.md)。这些方法多由no_exception_func捕获Exception、打印后返回None；没有异常向外抛出不等于操作成功。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler_interface.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler_interface.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_utils.py)（implementation）

## 关键启停链与Event观测恢复的固定实现

以下补充仍限前述两个TorchNPU固定提交，保留本卡A2/A3及公开参数/版本约束，不据内部实现扩展产品支持。只实际审阅profiler_interface中的构造、生命周期与参数检查，公开start/stop和两个analysis工具函数；trace ID生成、metadata dump、GC/FLOPs/native Profiler的完整实现仍另计，没有导入、启动采集或做异常/设备实验。

### 构造与环境gating不是每次重新探测

两版_ProfInterface先把非空activities转set，假值（包括空list/set）则取supported_activities；这个本地函数直接委托原生_supported_npu_activities，不在Python里认证硬件矩阵。_check_params遇一个不支持活动就整组回默认。record_shapes/profile_memory/with_stack/with_flops/with_modules逐项要求bool，非bool回False，不把字符串'false'解析成False；experimental_config类型不匹配则换默认对象。set转换本身发生在这些检查前，并非所有非法Iterable都已规范化。

没有NPU活动时“experimental config不用”的提示只是警告，该方法没有把对象清空；没有CPU活动而with_gc为真也只警告，真正GC启动还受CPU成员检查。不能仅靠warning文字推断全部配置字段被移除。

主线构造首先保存check_msprof_env的缓存布尔，随后仍做上述参数检查；只有有效时_lazy_init。init/warmup/start/stop/finalize/delete/analyse也都按这个已保存值提前返回。PROFILER_SAMPLECONFIG或PROFILING_MODE非空时helper警告并缓存False（'0'/'false'仍为非空）；环境后来变化不在这里重新探测。发布没有这套Python局部gating，构造会到_lazy_init；这不证明发布的原生层没有自己的检查。辅助缓存/环境字段见[解析与环境工具](../../guides/optimization/torch_npu/torch_npu_profiler_analysis_pool_parser_plan_and_done_marker.md)。

### warmup、start、stop顺序影响观测窗口

init_trace先创建/读取目录，再_init_profiler；主线随后才创建trace_id。warmup和start都按prof_path、record_shapes、profile_memory、with_stack、with_flops、with_modules、experimental_config()七项构造NpuProfilerConfig，分别调用原生warmup/start，不能将warmup等同start。

start在原生_start_profiler前读取syscnt_enable；启用时再读freq/start_cnt，并总读start_monotonic。主线随后逐项把preset_metadata交给可调用的metadata_json_adder，再包装Event方法，然后_start_profiler；with_flops且experimental_config.tx_enabled时安装FlopsHookManager，最后尝试启动CPU GC检测。发布同样先包装Event再_start_profiler/GC，但没有本段预置metadata/FLOPs hook调用。时间字段是启动阶段顺序取得的，不据这里证明与全部设备事件同时采样或已完成校准。

主线stop在含NPU活动时先torch.npu.synchronize，再按相同FLOPs条件uninstall，然后_stop_profiler、stop_gc_detect、解除Event包装。发布Python方法直接_stop_profiler、GC、解除包装，没有相同的显式同步/hook段；不由此推断原生_stop_profiler完全不等待。同步及观测开销不能与不含Profiler的正常负载混成同一计时窗口。

GC helper仅在CPU活动且with_gc时建检测器并start；stop还要求gc_detector非None，调用stop后才把引用清空。这里只审调用与条件，不重复认证阈值算法或所有回调异常行为。

### Event包装是进程内类方法修改

_enable_event_record逐个替换Event.record/wait/query/elapsed_time/synchronize，用torch.profiler.record_function('Event::方法名')包住原调用并保留返回值，wrapper.origin_func保存被包装函数。修改的是Event类方法，没有按某一个Event对象、某个线程或单个profile实例隔离；也不改变本卡对设备完成、event等待及数据寿命的外部合同。

_disable_event_record对当前每个方法只取一层origin_func，缺该属性就保留当前方法。若再次到达enable而尚未解除上一层，会再包装当前函数；一次disable不保证回到最初原方法。这里没有锁、实例拥有者或本地重入计数，不因已有profile状态机就宣称任意手动/嵌套路径都安全重入。

启停实现没有用统一try/finally恢复这些全局修改。例如包装之后_start_profiler抛错会跳过后续hook/GC，stop里较早同步、hook或原生stop抛错也可跳过后面的GC停止和Event恢复；不是说所有异常发生位置都会留下同一状态。没有运行这些条件故障来声称已观察到泄漏或错误。

### 吞掉异常不等于完成清理

公开_KinetoProfile.start先ProfPathCreator.init(export_only_mode=True)，再init_trace/start_trace；stop按stop_trace/finalize_trace顺序。两者都有no_exception_func，捕获Exception、打印并默认返回None，却没有在捕获处补执行后续清理。stop_trace失败时不会自动继续finalize_trace，不能只看调用没有向外抛异常就确认原生采集、Event、GC和目录状态都已恢复。

finalize本地依次_finalize_profiler、dump profiler_info、dump metadata，再把路径创建器is_prof_inited=False、销毁logger；任一前面步骤异常可跳过后面，不能视为一项原子收尾。内部analyse仅捕解析Exception并警告，主线返回NpuProfiler内部结果、发布不return；公开analyse封装和Future合同见[离线分析](profiler_analyse.md)。这些是Python关键链实际分支；native资源清理与全部metadata实现不在本卡来源内。

## 关键链增补证据

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler_interface.py)（47–223,251–307,428–429行；仅这些完整关键函数）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)（71–80行；仅这些完整关键函数）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_utils.py)（22–56行；仅这些完整关键函数）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler_interface.py)（42–193,282–283行；仅这些完整关键函数）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py)（67–76行；仅这些完整关键函数）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_utils.py)（22–33行；仅这些完整关键函数）
