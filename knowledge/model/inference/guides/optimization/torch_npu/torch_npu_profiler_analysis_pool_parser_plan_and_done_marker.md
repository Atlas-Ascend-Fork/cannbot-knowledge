---
type: Guide
title: TorchNPU Profiler的进程池、解析计划与完成标志
description: 记录解析池版本差异、完整parser配置和清理/完成标志的真实边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_npu_profiler.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiling_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_multi_process_pool.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_npu_profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiling_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_multi_process_pool.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_config/_parser_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_path_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_path_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-11T06:58:03Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler的进程池、解析计划与完成标志

## 固定范围和已有API合同

依据PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。完整核对NpuProfiler、ProfilingParser、MultiProcessPool、analysis工具函数及两张parser配置表；没有启动池、删除数据、运行msprof或解析采集内容。公开参数/产品边界沿用[analyse API](../../../apis/torch_npu/profiler_analyse.md)，不由内部实现扩大支持。

## 池生命周期与Future的版本差异

NpuProfiler先get_realpath、校验输入并找采集路径，空列表直接返回；daemon进程只打印离线解析提示然后返回。非空时强制set_start_method('fork', force=True)，进程数min(max_process_number或DEFAULT_PROCESS_NUMBER, 路径数)，常量默认os.cpu_count()//2，内部这里没有再做至少1的保护或完整参数校验。每个目录先检查写权限，再在提交进程中构造ProfilingParser，最后submit其绑定方法。

主线_check_input_path在公共输入路径检查后显式os.path.exists；发布改调check_path_owner_consistent。后者缺路径会抛错，但owner不一致只是warnings.warn，不是严格拒绝。每目录writeable helper主线对软链接和os.access失败警告，发布对应分支抛错；这些具体helper差异不等价整个路径规则或所有祖先都相同。

MultiProcessPool为单例；第一次init_pool才建ProcessPoolExecutor，已有池复用，不因新max_workers自动重建。主线worker initializer调用gc.disable，目的是注释所说规避fork/GC冲突，不能据此保证无死锁；发布没有该initializer。close_pool默认shutdown(wait=True)，之后_pool=None；atexit也注册此关闭函数。无池submit返回None。

主线submit_task返回Future，NpuProfiler收集并返回列表；发布submit_task不return提交结果，NpuProfiler也不返回该列表。sync调用会close_pool等候，但本地没有逐个Future.result取异常；async不主动关闭池，可留给后续调用或atexit。即使主线Future正常返回None，也不能证明全部子任务成功，因为内层装饰器和manager还会吞掉错误。公开analyse封装是否返回内部列表仍按API卡的合同，不把内部变化回推所有公开入口。

## 构造时就可能清理旧输出

ProfilingParser保存原kwargs引用并记起始墙钟时间；tensorboard_trace_handler构造时把output_path改成采集目录下ASCEND_PROFILER_OUTPUT，先remove_path_safety再make_dir_safety。这发生在提交进程池前，不是等解析全部成功才替换旧输出。其他analysis_type沿传入output_path。

analyse_profiling_data先初始化日志、load_info、更新export_type、删除旧CANN DB，再进入只包run_parser的内部try。主线在load_info前还reset_is_load，只把_is_load设False；发布没有该调用。load_info若_is_load已True就返回，因此不能把发布的同进程复用写成每次必重载目录配置，也不能说主线reset清空了所有状态或缓存。

外层@no_exception_func()捕获Exception、打印错误后默认返回None；正常返回也可能None，不捕获BaseException。run_parser异常由更内层catch记录后继续后处理；更早配置/删除异常或后处理异常可直接到装饰器，后续步骤不会保证完成。

## 导出选择与parser集合

update_export_type仅在kwargs.export_type非None时覆盖共享ProfilerConfig.export_type，该setter直接赋值；不是在本函数重新校验每个模式。含Db且analysis_type为Chrome trace或stack时强制改[Text]，两者都写回配置；其他含Db场景只有实际存在CANN路径才检测是否支持DB。缺CANN不会在这一处分支拒绝Db。

run_parser先建profiler_path/output_path字典，再param_dict.update(kwargs)，所以调用者kwargs可覆盖这两个键；随后用ProfilerConfig覆盖_export_type和activities。存在CANN时先删device summary/timeline和mindstudio_profiler_output，再根据get_level=='Level_none'选LEVEL_NONE_CONFIG，否则COMMON_CONFIG；无CANN用ONLY_FWK_CONFIG。这些清理不是失败回滚事务，删除helper的完整文件实现不在本卡来源内。

配置候选以set(export_type)遍历，跨Text/Db的合并顺序不保证稳定；每类parser只加入一次、保留首次遇到的位置。即使没显式Db，只要help检测支持默认导DB，还会追加当前配置对应的Db任务。对应analysis_type不存在时只取空列表，未在此报“无解析器”。最终用PARSER_NAME_MAP名字构造任务并add_task，再manager.run；返回注解list不表示函数实际返回列表。

| 配置/导出 | 完整候选组成的要点 |
|---|---|
| COMMON Text的trace handler | TorchOp、TaskQueue、TracePre、TreeBuild、CANNExport、CANNTimeline、Relation、MemoryPrepare、CANNAnalyze、OperatorView、TraceView、KernelView、TraceStepTime、MemoryView、Integrate、Communication |
| LEVEL_NONE Text的trace handler | 保留上述框架/关系/内存/导出分析链，去掉KernelView、TraceStepTime、Communication；表内TaskQueue在TorchOp之前 |
| COMMON/LEVEL_NONE Db的trace handler | TorchOp、TaskQueue、DbPre、CANNExport、CANNTimeline、CANNAnalyze、TreeBuild、MemoryPrepare、DbParser |
| ONLY_FWK Text的trace handler | TorchOp、TaskQueue、MemoryPrepare、OperatorView、TraceView、MemoryView |
| ONLY_FWK Db的trace handler | TorchOp、TaskQueue、DbPre、TreeBuild、MemoryPrepare、DbParser |
| COMMON Chrome / stack | Chrome为TorchOp、TaskQueue、TracePre、TreeBuild、CANNExport、CANNTimeline、TraceView；stack为TorchOp、TaskQueue、TreeBuild、CANNExport、CANNTimeline、StackView |
| ONLY_FWK Chrome / stack | Chrome为TorchOp、TaskQueue、TraceView；stack为TorchOp、TaskQueue、StackView |
| 内存时间线 | COMMON/ONLY_FWK的Text下只MemoryTimelineParser；LEVEL_NONE表没有此analysis_type条目 |

PARSER_NAME_MAP覆盖这些20类候选的本地名字，名字用于依赖匹配；候选表顺序不是运行时串行顺序。

## 依赖边决定何时能消费输出

两版依赖表原始字节相同。共同配置中TorchOp/TaskQueue无依赖、线程模式；TreeBuild依赖两者、线程模式；TracePre依赖两者但用子进程。CANNExport无依赖、子进程；CANNTimeline无依赖、NON_BLOCKING线程；CANNAnalyze等Timeline。Relation线程等TaskQueue和Timeline。

OperatorView等TreeBuild/Timeline/Relation/TorchOp；TraceView等TreeBuild/TracePre/Timeline/TaskQueue/TorchOp；KernelView等TreeBuild/Export/Relation；TraceStepTime等TreeBuild/Timeline/Relation/TorchOp；MemoryView等Export/MemoryPrepare；Integrate只等Export；Communication等TreeBuild/Analyze/Relation；Stack等TreeBuild/Timeline/TaskQueue/TorchOp。这些view为子进程。MemoryPrepare线程等TreeBuild/TaskQueue/TorchOp，DbPre线程等TorchOp/TaskQueue；DbParser线程等Export/MemoryPrepare/TreeBuild/Analyze/DbPre。

ONLY_FWK保留TorchOp/TaskQueue/TreeBuild关系；OperatorView只等TorchOp，TraceView和Stack等TaskQueue/TorchOp，MemoryView只等MemoryPrepare；MemoryPrepare等TaskQueue/TorchOp，DbPre等二者，DbParser等DbPre/MemoryPrepare/TreeBuild。该表也有无依赖CANNExport但不表示候选表必选它。两表MemoryTimelineParser配置{}，模式和依赖回到BaseParser默认，而非完整声明了一种特别并行模式。任务执行/错误释放规则见[调度和IPC](torch_npu_profiler_task_dependencies_ipc_and_failure_states.md)。

## analyse.done不是全任务成功凭证

tensorboard_trace_handler在run_parser的内部异常已被记录后仍会simplify_data、主线还update_platform_analysis_dir，再generate_parser_done_file。因此analyse.done可与失败任务、空候选集合或部分产物并存；manager本身也没有向调用者返回汇总成功码。反过来，后处理或写文件失败可导致没有done。FileManager实际创建/检查目录后以'w'打开空文件，标记不含逐任务状态或校验和。

simplify_data即使simplify_flag=False也尝试删host/device的sqlite；True再删summary/timeline、CANN analyze/mindstudio_profiler_log/mindstudio_profiler_output及匹配msprof_analysis_数字.log的常规文件。不要把False描述成完全保留原始目录，也不能将解析视为全程只读。主线额外搬PLATFORM目录：空目录删除，否则采集目录名按下划线拆后第3项isnumeric才移动到父目录PLATFORM_该项，已存在目标先删除再os.replace；发布无这段。它不是从任意worker命名中可靠提取时间戳的证明。

## 工具函数还会采集和缓存哪些环境信息

collect_env_vars两版登记相同九项，缺省空串，包在ENV_VARIABLES：ASCEND_GLOBAL_LOG_LEVEL、HCCL_RDMA_TC、HCCL_RDMA_SL、ACLNN_CACHE_LIMIT、HOST_CACHE_CAPACITY、ASCEND_ENHANCE_ENABLE、PYTORCH_NPU_ALLOC_CONF、ASCEND_LAUNCH_BLOCKING、HCCL_ALGO。它只读取字符串，不校验参数是否生效、不列出所有影响性能的环境变量。

主线另外有check_msprof_env，按PROFILER_SAMPLECONFIG/PROFILING_MODE非空发警告并缓存False，否则True；检测的是字符串真值，不解析'0'/'false'为布尔False。函数先设_called再写_cached_result，没有锁或自动失效，环境之后变化不强制重算。发布工具模块没有这个本地函数；也不能仅凭定义就称解析入口已经调用它。

验收同时保留固定版本、目录保留策略、最终export_type/activities、候选和依赖状态、Future结果及实际文件/表，解析总墙钟耗时不替代Kernel、通信或内存指标。[CANN导出与等待](torch_npu_profiler_cann_export_analyze_and_timeline_readiness.md)说明单个外部步骤的另一层返回码边界。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_npu_profiler.py)（1–51行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiling_parser.py)（1–199行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_multi_process_pool.py)（1–34行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_utils.py)（1–56行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py)（1–155行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py)（1–90行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_npu_profiler.py)（1–46行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiling_parser.py)（1–146行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_multi_process_pool.py)（1–26行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_utils.py)（1–33行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_config/_parser_config.py)（1–155行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py)（1–90行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiler_config.py)（27–28,85–86,92–98,175–186行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（1–9行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（194–208行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_path_manager.py)（17–32,51–69行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)（292–307行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（16–16,17–17,26–26,70–70,71–71,72–72,73–73,106–106,118–118,132–132,133–133,234–234,235–235行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiler_config.py)（25–26,68–74,147–156行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（1–10行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（206–220行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_path_manager.py)（17–32,51–84行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)（212–225行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)（15–15,16–16,73–73,74–74,75–75,76–76,106–106,118–118,132–132,133–133行；有界辅助）
