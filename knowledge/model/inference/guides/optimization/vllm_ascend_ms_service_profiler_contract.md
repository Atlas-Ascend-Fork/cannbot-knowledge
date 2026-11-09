---
type: Guide
title: vLLM Ascend MS Service Profiler：符号配置、版本与框架链路采集
description: 说明 SERVICE_PROF_CONFIG_PATH、PROFILING_SYMBOLS_PATH、generate_service_profiling_config
  的版本与符号合同，区分时间线和独立 Metric 与 Prometheus，关联 recorder 旧值和链路完整性排查。 补充 profiler_step_num
  与 torch_prof_step_num 的零值差异。
tags:
- task.debugging
- task.optimization
- topic.performance.analysis
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/profiling_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/performance_and_debug/service_profiling_guide.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/performance_and_debug/service_profiling_guide.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/setup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/ms_service_metric.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/provider.py
  role: implementation
created_at: '2026-10-29T18:12:42Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-02T01:11:40Z'
---

# vLLM Ascend MS Service Profiler：符号配置、版本与框架链路采集


## 任务与固定来源

依据 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的符号生成实现、服务剖析文档及对应中文PO。目标是为请求、调度、模型执行和KV传输定位框架时间线，不是把函数计时直接解释成NPU kernel耗时或端到端收益。整项工具没有明确硬件支持集合，保持draft/空平台；本次未运行服务、构建工具或采集数据。

工具选择见[服务剖析](vllm_ascend_service_profiling.md)：TorchNPU Profiler通常用API控制；MS Service Profiler另有JSON开关和YAML符号配置，二者不互换。文档比较表写需源码构建，正文又写随CANN Toolkit预装；应检查目标环境实际可用的工具和版本，不能据任一表述保证所有Toolkit镜像已具备它。外部msserviceprofiler的加载、patch、表达式和解析实现未在本批闭合。

## 配置文件生成与加载是不同阶段

setup.py以vllm.general_plugins登记 `ascend_service_profiling = vllm_ascend:register_service_profiling`。注册函数先确保全局patch，再调用 `generate_service_profiling_config`；此函数生成符号模板，没有在自身调用start、采集请求或解析trace。插件存在、函数被调用、符号文件存在，都不等于采集开启。

文件名直接取模块导入时的 `vllm.__version__`：`~/.config/vllm_ascend/service_profiling_symbols.<version>.yaml`。文档示意MAJOR.MINOR.PATCH，源码没有在这里规范化或剥离版本后缀。记录实际版本字符串、实际文件路径及加载日志，不将目录名当作二进制配对证明，也不假定外部消费者必然使用同样的版本匹配规则。

若目标文件已存在，生成器直接返回，不合并默认新符号、不比较内容，也不刷新旧文件；升级后若版本字符串没变，旧模板可能继续保留。需要自定义时保存原文件，以独立副本设置PROFILING_SYMBOLS_PATH，并按文档重启服务。不能只靠重启或再次注册插件期待文件自动更新。

目录创建失败返回None并记日志。写入使用同目录临时文件，再replace到目标，失败记录异常并清理临时文件；这保护完整写入，不构成跨进程排他锁。前置exists与replace之间仍有竞争窗口，不能把“先检查存在”解读为任何并发下都不会覆盖。调用方没有用返回值阻止服务启动，故服务正常不证明模板已写入。

## 启动与控制清单

| 项目 | 文档定义与检查点 |
| --- | --- |
| SERVICE_PROF_CONFIG_PATH | 指向性能JSON配置；文档说缺文件会生成默认配置，此行为属于外部工具，不是本仓符号生成函数的保证 |
| PROFILING_SYMBOLS_PATH | 指向待加载的YAML；未设置时走默认版本路径，改符号后须重启；核对Worker进程看到的路径与文件内容 |
| enable | JSON采集开关，默认0，设1启用；不等价于TorchNPU的/start_profile |
| prof_dir / profiler_level | 输出目录，默认用户目录下.ms_server_profiler；采集级别默认INFO，实际目录还按启动时刻分组 |
| timelimit | 文档范围0–7200秒，0无限制，建议至少120秒以免缺解析数据；“停止进程”的具体作用对象/清理语义需目标工具验证，不能据此推断业务服务一定退出或不退出 |
| domain | 文档使用区分大小写的分号分隔域，空表示全部；列Request/KVCache/ModelExecute/BatchSchedule/Communication，当前模板另有Engine/Execute/SpecDecode/ModelForward等标签，须核对实际工具过滤和目标事件，不能仅据文档列表认定覆盖完整 |

保存启动前配置、目标负载与原始产物，结束后恢复采集开关。请求成功、enable=1或无异常日志，都不能代替目标事件、rank与时间窗口的验收。

## 算子时间采集的几组参数不能混用

acl_task_time=0或无效值在文档中为关闭；1使用ACL_PROF_TASK_TIME_L0调用aclprofCreateConfig；2走MSPTI，需启动前加载对应CANN根目录的libmspti.so；3走Torch Profiler。这些是不同路径，不能把任意LD_PRELOAD、原生ProfilerConfig和此JSON拼成同一个已验证配方。

acl_prof_task_time_level支持L0（调度/执行）与L1（再含AscendCL拷贝/同步及基本信息）；可带1–999秒时间段，例如L1;10。未设或无效按文档回退默认，acl_task_time=3不支持这个时间段。torch_prof_stack只在模式3有意义；torch_prof_step_num默认0取全部步骤，而profiler_step_num的0或无效值会停止整体profiling。这两个“step数=0”含义相反，不得统一补默认值。后者计数依赖modelRunnerExec事件，符号没有真正接入时尤其要核对。

所有这些参数的外部SDK支持、实际开销、NPU图模式及组合仍需目标版本验证；本批没有生成任何测量结果。

## 符号、事件和属性逐层对齐

YAML的symbol是Python模块和属性链；name为事件名称，domain为筛选标签，min_version/max_version约束工具的版本选择；没有handler通常用timer，具名handler指向外部Python处理函数。文档自定义示例存在点式路径，模板多用module:callable；本批不保证外部resolver把二者等价处理。文档称导入失败回退timer，即使目标环境如此，也不保证保留handler提供的请求/批次关联数据。

attributes仅在文档的timer路径支持；表达式可读取参数、this/args/kwargs、return与索引，经attr/len/str等管道取值。高级bool示例又要求自定义handler支持，不能将例子当作通用任意Python求值。先核对目标版本函数签名和返回结构，属性名存在于YAML不证明运行时可取值。

当前模板按任务覆盖下列链路；应以具体配置、已选Runner和实际事件核验，而不是将整个清单视为全路径已自动插桩：

| 链路 | 模板中的主要采样面与身份信息 |
| --- | --- |
| API到引擎 | Chat/Completion、AsyncLLM.generate/add_request、EngineCore.add_request/step/step_with_batch_queue与输出处理；用于对齐请求入口、排队和输出 |
| Scheduler与Executor | Scheduler/AscendScheduler及recompute/async/dynamic/balance变体、UniProc/MultiProc/抽象Executor；部分scheduler属性取返回的num_scheduled_tokens，不能直接当成纯req_id数组 |
| Runner与模型 | 多个V1 NPUModelRunner执行/输入/metadata/graph/DP同步/forward/sampling/dummy点及部分GPUModelRunner继承路径；forward属性取input_batch.req_ids、dp_rank和device.index |
| 多模态与投机 | wildcard embed_multimodal、encoder、draft_propose、draft_model_forward、draft token与rejection；名称和版本下限不证明全部新模型或V2都已绑定 |
| KV分配到接收 | 匹配remote KV、alloc后更新、构建metadata、start_load、接收线程enqueue/transfer、task完成、get_finished、KVOutputAggregator和scheduler推进；按request/remote_request/engine/TP身份追踪，不能只按时间相邻认定是同一请求 |
| 元信息与兼容点 | DP初始化、旧ProfileExecuteDuration.capture_async（max_version=0.14.0rc1）和record_function_or_nullcontext（min_version=0.15.0rc1）；这些是符号选择条件，不是功能删除版本证明 |

模板同一symbol可出现多次以提供不同handler/元信息，外部处理的去重、组合和调用次序未在本仓生成函数中实现。许多项目只设min_version=0.9.1而无max，不意味着未来任意版本的模块、方法和属性不变。默认模板明显含V1路径，V2默认选择也不自动补齐相应事件；遇缺事件时核对实际Runner及具体方法，而非只看模板生成成功。

## 解析、验证与停止条件

文档使用 `msserviceprofiler parse --input-path=<run> --output-path=<output>`，产物包括chrome_tracing.json、profiler.db、request.csv、kvcache.csv、batch.csv。先确认目标run、各进程/rank、负载与窗口，再检查请求/批次/KV事件能否按身份关联，以及handler/属性/符号缺失warning。某CSV缺失可能来自域过滤、步数、短采样或未绑定符号，不能直接判定业务没有执行该阶段。

中文service_profiling_guide.po的108项有效译文已逐项阅读；它保留相同字段和两个step=0的差别，也保留安装方式的两处表述。PO存在和条目数不证明当前服务端HTML完整等于本快照，实际构建与渲染仍需单独核验。

修复配置后保持同负载复采，正式收益用关闭采集的[基准测量](vllm_ascend_benchmark_workflow.md)。符号没有接入、文件沿用旧模板、handler退化、采集窗口不完整或rank不齐时停止完整链路结论。外部工具行为、NPU和下游Agent验证仍未执行。


## Prometheus指标的独立入口

需要长期运行指标时，按[MS Service Metric provider接入](vllm_ascend_ms_service_metric_provider.md)核对独立的ms_service_metric.providers、MS_SERVICE_METRIC_CONFIG_PATH和Prometheus进程目录。这里的时间线JSON/YAML、SERVICE_PROF_CONFIG_PATH与PROFILING_SYMBOLS_PATH仍按本卡的Profiler版本合同使用，不能互换开关或把一边的文件成功当成另一边已采集。

指标缺失、recorder重建、EPLB旧快照与updated imbalance提案口径见[Metric缺失/旧值排障](../../runbooks/runtime/vllm_ascend_ms_metric_missing_or_stale.md)。两类工具的外部Core/解析实现、真实Runner和NPU开销仍需目标环境取证；本批没有新增实测结果或扩大平台范围。
