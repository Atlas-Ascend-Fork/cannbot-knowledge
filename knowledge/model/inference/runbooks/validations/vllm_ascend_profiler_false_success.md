---
type: Runbook
title: vLLM Ascend Profiler 控制成功却无目标trace：生命周期、步数与配置差异
description: 沿 TorchNPUProfilerWrapper 与 vLLM WorkerProfiler 核对惰性创建、启动停止warning、active/running状态、Worker step时点、首次trace名和未接入的schedule字段，避免把控制返回当作采集完成。 补充请求级profiling签名预检、delay/max覆盖与REST/RPC会话占用，区分Worker结构检查、控制返回和实际trace。
  解释首次trace_name的前缀与后续profile_prefix复用，按实际trace文件辨别会话。
tags:
- task.debugging
- task.testing
- topic.performance.analysis
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/profiler/wrapper.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/profiler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/profiler/torch_npu_profiler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/profiling/capture.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/serve/profile/api_router.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/async_llm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/core.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/core_client.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/executor/abstract.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/llm_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/exceptions.py
  role: implementation
created_at: '2026-10-29T18:12:42Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T13:35:15Z'
aliases:
- Profiler 首次 trace_name 前缀复用
---

# vLLM Ascend Profiler 控制成功却无目标trace：生命周期、步数与配置差异


## 触发与版本边界

服务的profiling控制调用正常返回，但没有目标trace、时间窗/步数不符、第二次采集仍用旧前缀，或设置warmup等参数没有预期效果。本文对照Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与原生vLLM v0.32.0 `5df63a7203cdb9328d824a27b682e77c7b9928be` 的具体接口；不据两个固定版本就宣称所有环境二进制兼容。硬件集合未被该组合来源明确证明，保持draft/空平台。

已阅读原生WorkerProfiler父类、ProfilerConfig、Ascend wrapper/Worker及下述REST/RPC有关调用点；未执行服务、HTTP、torch_npu或NPU测试。HTTP/RPC返回具体行为仍依目标端点；这里证明部分底层异常不会从父类start/stop直接抛出，因此“控制返回成功”本身不足以证明采集成功。

## 第一层：配置是否是Ascend真正消费的字段

ProfilerConfig允许torch/cuda/proton，Ascend的TorchNPUProfilerWrapper只接受profiler=torch和非空torch_profiler_dir；与additional_config.msmonitor_use_daemon不能同时开启。get_ascend_config发生RuntimeError会被wrapper的suppress忽略，并按daemon=False继续，不能把未取到配置解释为已完成互斥核验。

原生配置会将本地目录expanduser/abspath，URI路径保持原状；这只证明原生配置解析，不证明torch_npu的trace handler支持所有URI scheme。原生活动枚举与校验也不代表Ascend采集活动跟随该列表，需按实际wrapper核对：

| 参数/能力 | 固定Ascend wrapper中的实际接线 |
| --- | --- |
| 活动 | 固定CPU和NPU，不读取torch_profiler_activities列表 |
| Python/module堆栈 | 底层with_stack固定False；torch_profiler_with_stack传给with_modules，源码说明后者对应torch堆栈含义；不能把torch_npu同名with_stack开关原样套过来 |
| 内存 | torch_profiler_with_memory传给profile_memory |
| 实验配置 | Text导出、Level1、PipeUtilization，msprof_tx/l2_cache/op_attr/record_op_args关闭，data_simplification=True，gc_detect_threshold=None |
| warmup_iterations / active_iterations / wait_iterations | 此wrapper未用这些字段构造schedule，_profiler_step仅返回True，未调用底层profiler.step；不能照原生TorchProfilerWrapper的schedule语义声称它们已生效 |
| flops/gzip/dump_cuda_time_total/record_shapes等 | 本wrapper未将这些原生字段传入创建函数；配置能被解析不等于采集支持 |
| capture/annotation相关字段 | 不能由原生字段存在推断此wrapper具有CUDA graph归因/详细标注能力；父类默认capture上下文和annotation为空操作，具体模型路径另验 |

## 第二层：首次创建、trace身份与重复控制

NPUWorker在第一次profile(start)时用profile_prefix和get_worker_rank_suffix(global_rank)组成trace_name并创建wrapper；后续start复用同一对象，不更新首次trace_name。换profile_prefix不会自动得到新命名会话；需按实际文件和rank区分，避免把旧目录当新采集。stop先于start时只warning返回。

Ascend的profile签名为is_start和profile_prefix，调用父类start时没有传请求级delay/max覆盖参数。父类支持这些参数不证明Ascend端到端RPC已接入；有效delay/max先按创建时ProfilerConfig默认值解释；同一v0.32.0的请求级签名预检见后文，其他版本仍需核对。

## 第三层：active、running和warning不是同一信号

WorkerProfiler有lifecycle lock串行化start/stop。start已active时忽略重复请求；否则验证非负delay/max，置active=True，delay=0就尝试_start。_call_start只在底层成功后置running=True；异常只记warning，active仍可为True。于是再次start可能被忽略，不能靠重复发送start保证恢复；先保留错误和产物，核对配置后按stop/start状态重新处理。

delay>0的启动只在active_iteration_count恰等于delay时尝试一次，不是失败后每步重试。_call_stop也捕获底层异常并记warning，随后无论实际底层如何都置running=False；状态清零不证明trace已flush或NPU采集已停止。stop会重置active、计数；shutdown仅在running时调用stop，不是对任意失配状态的完整恢复保证。

因此需同时核对控制调用、warning、wrapper状态（可观测时）、目标目录和实际目标事件。无trace、失败后仍active、底层stop报错或目录只有旧文件时，保持未完成；不要把这些源码状态当成本次实际观察到的故障。

## 第四层：step发生在forward前，最大步数用严格大于

NPUWorker.execute_model在调用model_runner.execute_model之前调用profiler.step；只要求profiler对象非None，没有在该调用处按forward_pass过滤。零token/DP协调等Worker调用可能计入控制步数，不能按HTTP请求数、生成token数或有效forward数直接换算。

父类step先增加active_iteration_count；达到正delay则启动。running时调用_profiler_step，Ascend直接返回True，所以profiling_for_iters随这些Worker步骤增加。max>0且计数**大于**max才stop，并在当前forward前完成控制；不能改写成大于等于停止的伪代码，也不能脱离step放置位置判断采到哪几个forward。max=0不设此上限，delay=0立即尝试启动；这些零值与其他工具的profiler_step_num语义不互换。

AISBench定时采集还按正式请求起点/成功计数和秒数控制窗口，见[产物完整性合同](../../guides/optimization/vllm_ascend_aisbench_profile_artifacts.md)。它强制max_iterations=0且ignore_frontend=True；若原命令已有delay_iterations，合并函数没有清掉它，实际目标窗口仍可能延迟。Controller的duration_reached不能单独证明底层覆盖了全段。

## 验收与回退

保存原生/Ascend/torch_npu/CANN版本、实际ProfilerConfig、Runner、rank与trace名称、所有warning、控制时点、Worker步数、目标请求和解析产物。先按[服务剖析](../../guides/optimization/vllm_ascend_service_profiling.md)定位正确实例；确认数据可解析且含目标事件后才作性能归因。正常控制调用、running=False、一个非空trace文件或父类计数达到阈值都不是完整采集的单独证据。

恢复采集配置，用关闭采集的基准验证性能；若stop失败，不能只据Python状态假定底层已释放，需要目标环境的实际健康检查与受控重启策略。本卡不替代外部工具生命周期、CANN行为或硬件测试。


## 请求级覆盖、RPC签名预检与会话占用

补读同一原生v0.32.0：StartProfileRequest为strict类型、额外字段ignore，包含profile_prefix/delay_iterations/max_iterations三个可空字段。REST仅传非None项，空请求仍可走无覆盖调用；字段拼错被忽略不表示功能生效。prefix验证为1–128个ASCII字符、首字母数字、其后仅字母数字及._-，迭代上限非负；配置合法与Worker能接参数是两层检查。

AsyncLLM经profile_async/EngineCore派发到Executor.profile。后者只把非None的delay/max加入kwargs，在collective_rpc前用_check_worker_profile_kwargs检查实际worker_cls.profile签名；有**kwargs则通过结构检查，否则缺参数名即抛ValueError，避免失败RPC留下未读回复。Ascend固定NPUWorker原始签名只有is_start和profile_prefix，所以显式覆盖（即使值为0）不能据原生GPU Worker支持就推定可用；省略值则不触发这组kwargs检查。最终客户端异常/HTTP状态、运行时patch和自定义Worker仍按实际接线核验，未运行请求。

原生GPU Worker会set_output_name并向start传delay/max，Ascend固定Worker复用首次名称且不传这些覆盖，两者行为确有差异。适配Agent应验证能力并选择启动配置或受支持的请求参数，不以“原生字段存在”替代后端验收。

AsyncLLM在client_count==1时启用会话guard，重复start可抛携带HTTPStatus.CONFLICT的ProfilerAlreadyActiveError；多API client时该guard和自动前端CPU profiler条件不同，不构成跨进程全局锁。其start先标session active，再await引擎，普通Exception清标；取消可能已经作用到后端，源码要求随后stop。stop并发等待引擎与前端，成功后才清session；部分停止失败不能据局部状态宣称完全收尾。

同步LLMEngine则在start的except BaseException清session，与异步路径不同。前端/Engine会话、Worker active/running和底层trace文件是独立状态；不要对409、超时、取消、未接入覆盖或底层warning统一用重发start处理。仍保留原始请求、实际Worker类、配置/会话状态和采集产物，再作判断。
