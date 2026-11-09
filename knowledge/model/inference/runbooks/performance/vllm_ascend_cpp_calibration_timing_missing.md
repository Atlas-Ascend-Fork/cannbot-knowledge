---
type: Runbook
title: vLLM Ascend CPP 校准排障：无计时、拟合失败与停采判据
description: 沿 _record_execution_timing 核对 startup ready、execution_time_ms、history_fitted/with_history_ready
  和 disable_profiling_timing，区分样本缺失、停止拟合与真正可用的时延模型。
tags:
- task.debugging
- task.testing
- topic.performance.analysis
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_profiling_chunk.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/profiling_chunk_predictor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/scheduler_profiling_chunk.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_engine_core.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_profiling_chunk.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_profiling_chunk_performance.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/dynamic_chunk_pipeline_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/executor/multiproc_executor.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/parallel.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/mrv2_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/vllm.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_use_v2_model_runner.py
  role: supporting
created_at: '2026-10-30T00:05:35Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T01:36:59Z'
---

# vLLM Ascend CPP 校准排障：无计时、拟合失败与停采判据


## 触发、原始信号与版本

CPP已配置，但动态chunk没有预期变化、在线样本不增长、出现拟合warning，或need_timing已关闭却无法证明历史模型可用。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与参考vLLM v0.32.0；本卡只蒸馏Host计时/拟合/回传路径，不是本环境的故障复现。整项硬件集合未明确证明，保持draft/空平台。

可检索的原始信号来自源码字面日志：Profiling failed: only %d/8 samples collected、Failed to fit non-negative chunked model、Skipping timing sample: unable to extract per-request chunk info，以及Profiling completed successfully。前三项是已定义的分支信号，最后一项只代表启动模型fit成功和ready设置，不是在线拟合、整机性能或所有PP stage均衡的证明。

## 先分启动与在线的五组状态

| 状态 | 固定代码含义 | 排障时不能替代的证据 |
| --- | --- | --- |
| _profiling_initialized | 启动profiling函数已经进入过，置位早于executor检查/拟合 | 不表示采样成功；None executor、少样本或fit失败后同对象也不会自动重试 |
| manager.is_ready | _profiling_done且predictor.is_ready | 只代表启动阶段已准备，不表示在线历史模型存在 |
| with_history_ready / history_ready | 至少一次record_batch_execution_time里的fit_chunk成功，且manager ready | 仍需看系数、时间单位、输入范围和实际chunk，不是全负载拟合质量门槛 |
| _set_time_done | 首批无历史条件满足计数达到3，目标时延更新阶段结束 | 计数在request_chunks为空检查之前，不能直接当3条可归因拟合样本 |
| history_fitted | 采样条数超过max_fit_chunk后停止继续拟合的标志 | 不要求此前NNLS已成功；与with_history_ready是独立标志 |

保存这些状态、chunked_fit_data长度/内容、target_latency、启动/在线两套系数及原始日志。不要用一个“completed”、need_timing=false或history_fitted=true替换整条状态链。

## 启动采样、输出rank和重试边界

Scheduler在executor就绪后通过collective_rpc调用所有Worker的profile_prefill_latency。Worker把token数钳到有效范围，前后torch.npu.synchronize并返回ms；所有rank执行以保持PP协同。Scheduler仅在RPC签名支持unique_reply_rank时传world_size-TP×PCP，标准MP无聚合器路径只读该rank回复。Worker的PP0和“not used”注释不决定实际消费rank，其他executor/launcher另核对。

启动循环首轮warm-up不入拟合，目标约64个样本；RPC异常以debug记录后继续，_extract_latency仅取数值或list[0]。无executor、少于8个有效项或fit失败会保持不ready，_profiling_initialized已为true。先定位RPC/实际Runner/返回形状和采样日志；不能把第二次调用被跳过当作恢复，本文没有清guard、调用RPC或重启服务。

_build_rpc_kwargs用inspect.signature检查显式unique_reply_rank参数；仅有**kwargs不自动满足这项检查。没有collective_rpc或没有显式参数时返回空kwargs，读取parallel_config的AttributeError也会省略该参数；签名反射本身的其他异常并未在这段配置try内兜底。回报形状与选rank因此要同时核对，不能由方法名含collective就默认取得目标PP rank。

启动fit用最小二乘，异常时尝试polyfit；在线fit_chunk用NNLS。二者模型、系数、失败分支与ready不同，不能互用。调用已返回或可预测一个chunk，不代表样本内容/误差已满足目标模型要求。

## execution_time_ms从哪里来

V1/V2 execute_model所读入口先清_cpp_execution_time_ms，再调用_start_profiling_chunk_timing；need_timing=false直接不计时，收到disable_profiling_timing也把本进程开关关掉。有效开始/结束会同步NPU，用perf_counter生成ms。V1在所读_model_forward后结束，V2在所读执行尾部结束，不应假设两者包住完全相同的工作。

NPUWorker.sample_tokens在Runner采样返回后调用_attach_profiling_chunk_execution_time。helper读取并清空暂存时间，再在开关/值允许时写入返回对象；MRV2 AsyncOutput使用其内层model_runner_output。只查外层对象、只查execute_model返回值，或忽略采样阶段，可能误判没有时延；不据helper存在保证任意pooling/零token/异常早返路径都会携带该字段。

CPP启动dummy与运行计时也分开。V2的_cpp_profile_dummy将profile_cpp、speculator和max_num_reqs暂时改为目标prefill语义，finally恢复；V1所读profile_cpp分支使用单请求并强制eager。它们不是两种Runner/所有功能已通过NPU验收的事件。

## 在线样本为何被跳过或停采

_record_execution_timing要求manager ready；elapsed_time_ms缺失或非正、total_num_scheduled_tokens非正都会返回。对new/cached请求按request_id与num_scheduled_tokens提取(C,H)，cached缺computed项时默认0；无法归因则debug并跳过。这些默认值/字段读取需要与实际版本对齐，不以字段缺失默认为0证明真实历史为0。

没有历史时更新目标并累计_set_time_count，即使随后发现request_chunks为空也可能已经计数。有效列表交给record_batch_execution_time，特征为[ΣC(C+H),ΣC,N]；Engine先把ms除1000转秒，manager再乘1000存回ms。将入口秒与观测ms混用会改变目标与系数，先核对单位再调smooth_factor。

这3次目标更新并非求平均：每次set_target_latency覆盖先前目标。拟合成功后predict仍可能因未ready、二次系数为0、负判别式或非正根返回None；不能只看fit日志便要求每步一定使用动态预测，更不能强置ready绕过实际模型条件。

默认至少5、最多30个点调用NNLS；第31个点触发history_fitted=true并返回false，不再做一次新拟合。若此前拟合全失败，该标志仍可能为true，with_history_ready却仍false。随后_set_time_done与history_fitted同时为true时，Engine尝试关闭自身need_timing；读取配置的RuntimeError被忽略，但仍置scheduler停采flag，并在后续SchedulerOutput传播disable_profiling_timing。Worker在后续计时入口才消费该标志。停采流程没有再次要求with_history_ready，也没有残差质量验收。

因此“停止收集”与“在线模型可用”要分别核对；保留此前fit错误和是否曾成功的证据。错误类型也分层：归因try内仅捕获AttributeError/TypeError并debug，NNLS有自己的失败集合；不要笼统认为任何异常都会静默skip。

## 多进程patch与恢复判据

patch_profiling_chunk模块导入时安装EngineCore.__init__ wrapper；初始化原逻辑后，按scheduler是否提供接口执行profiling并包装update_from_output/schedule。spawn子进程入口的重装职责在patch_engine_core.py，不能照旧模块注释假设父进程patch会自动传入每个子解释器。

_profiling_patches_applied是每进程全局guard；_original_update_from_output和_original_schedule也为全局单槽，包装首个符合条件的scheduler类后不再按新类建立独立记录。它们不构成任意多模型/多scheduler切换和并发的通用隔离/回滚契约。核对目标进程、实际类/方法和输出flag，不能只看前端导入过模块。

恢复时先核对[CPP工作流与配置](../../guides/optimization/vllm_ascend_cpp_prefill_calibration.md)，对齐实际executor/Runner、样本与单位、startup/history状态及各进程停采flag，再用固定拓扑/输入比较关闭动态chunk的基线。输出正确性、实际chunk与拟合误差/范围通过后，才比较关闭采样后的稳态TTFT/吞吐。本文未修改上游、构造scheduler、执行torch/NPU/pytest或取得恢复结果。

## 测试定义的证明范围

所读UT片段定义smooth=0拒绝、need_timing联动、启动少样本/重复调用、RPC rank选择及async placeholder/MRO等断言，并mock配置/计时/模型。它们不是本次执行结果，亦非完整1002行测试、完整schedule主体或Device/多机闭包。四卡performance用例的5.45秒阈值、近似TTFT和sync/async组合按主指南分别解释，不作为本卡实际修复或全平台性能承诺。


## 先确认V1 PP实际是否启用了异步

看到V1和PP>1，不要仅凭上游错误文本或旧CPP测试注释判定当前Ascend必然拒绝异步。反过来，patch_use_v2_model_runner.py允许列表移除了pipeline parallelism with async scheduling，也不能证明当前scheduler已启用异步。检查下列控制面证据，再进入本卡的计时/拟合排障：

1. 区分输入async_scheduling=None、False与True。固定原生默认分支在该点为V1 PP时会设async_scheduling=False；后续允许列表不会自动改回True。
2. 保存最终async_scheduling及ProfilingChunkScheduler/ProfilingChunkAsyncScheduler类，确认没有把同步路径当成异步路径采集或比较。最终值还受其他已配置条件和平台钩子影响，不能仅用默认分支解释全部配置。
3. 对实际前端/EngineCore/Worker核对_get_v1_model_runner_unsupported_features是否安装Ascend wrapper。mrv2_utils的property/V2验证patch与platform模块的V1允许列表分别核对；只看前者不能证明后者已安装。
4. 检查batch_job_sched_config.enabled及最终scheduler_cls。CPP分支后还有batch-job赋值；若两者都走到该处，最终可能是BatchJobAwareScheduler/BatchJobAwareAsyncScheduler，不能把CPP配置开启当作已用CPP调度。这里只陈述条件下的局部顺序，不据此保证组合可用。
5. 保留_validate_v1_model_runner返回的剩余拒绝项；prefill context parallel等不因PP异步这一项被允许而消失。不要删除整个列表、清guard或强置ready绕过错误。

固定UT只定义了允许列表和PP/async/PCP的控制面断言，CPP UT的V2配置也不代表这里已运行了V1异步模型。类与配置一致后，仍按startup/history状态、输出载荷、采样归因、时间单位与停采flag验证；最后才比较目标模型的真实精度与性能。本次未执行这些调用、修改运行配置或得到NPU恢复结果。
