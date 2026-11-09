---
type: Guide
title: vLLM Ascend CPP：PD Prefill 流水并行的动态分块与校准
description: 在 PP>1 的 PD P 端先建立固定 chunk 基线，再完成在线时延校准并调节动态 chunk，避免未校准预测、前缀命中和 balance
  互斥造成误判。
tags:
- task.optimization
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/dynamic_chunk_pipeline_parallel.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/dynamic_chunked_pipeline_parallel.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/profiling_chunk_predictor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/dynamic_chunk_pipeline_parallel.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/dynamic_chunked_pipeline_parallel.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/scheduler_profiling_chunk.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_profiling_chunk.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_profiling_chunk.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_profiling_chunk_performance.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_prefill_v1/load_balance_proxy_server_example.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/executor/multiproc_executor.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/parallel.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/mrv2_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/vllm.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_use_v2_model_runner.py
  role: supporting
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-10-30T01:36:59Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
      phase:
      - prefill
---

# vLLM Ascend CPP：PD Prefill 流水并行的动态分块与校准

## 适用范围与支持依据

CPP 是基于 profiling 的动态 chunk 策略，目标是 PD P 端 PP>1 的长序列 Prefill。来源性能配置在 A3 64GB、DeepSeek-V3.1-W8A8 与 Qwen3-235B 上给出；本卡平台仅按这项直接配置依据声明。其他硬件需补证，不因调度是 Python 实现就认定全平台已验证。

启用 chunked prefill，在 scheduler_config.profiling_chunk_config 设 enabled=true，关闭 enable_balance_scheduling。D 端不配置 CPP。支持 SRF 队列的组合仍需单独核对图、模型与 connector；Mooncake V1/V2 的 PP 支持是来源推荐入口。

## 基线和动态参数

先关闭 CPP，搜索固定 max_num_batched_tokens，例如来源的 8192/16384/24576/32768 候选；这些值是搜索起点。动态路径将该值视为初始/上限相关预算，太大会浪费计算，太小降低算子效率。不要把“固定最优的2–4倍”当作所有流量的公式。

smooth_factor 在 (0,1]；min_chunk 应小于 token budget，当前校验可按预算下调最小值并告警。need_timing 未显式设置时跟随 enabled（CPP 开启时为 true），显式 false 保留；启动 profiling 额外约64次 forward，不能并入稳态性能。max_fit_chunk 控制拟合点数量。

## 在线校准与验收

使用与 max-model-len 相当的真实或合成长输入、batch_size=1；启用 prefix cache 时确保样本不同，避免命中绕过待拟合计算。完成校准后再测不同长度与并发。need_timing=true 时先保持 smooth_factor；若关闭 timing，可搜索较低平滑系数，但可能次优。

记录 chunk-size 序列、阶段耗时、TTFT 和吞吐；固定长度并发1与变长并发4不可混作同一收益。未完成校准可严重退化。关闭 enabled 回到固定 chunk，保留同一 PP 拓扑以定位收益来源。本次未复测来源 A3 数字。


## 两阶段预测模型分别验收

启动阶段拟合 f(l)=a·l²+b·l+c，以 T=f(base_chunk)-f(0) 为目标，从 a·x²+(2aL+b)·x-T=0 求当前历史长度L下的下一chunk。预测经smooth_factor向base平滑、min_chunk下限，再向上对齐max(page_size,64)；scheduler随后按剩余token/预算截断，因此最终实际chunk不保证仍为该对齐倍数。

在线阶段另拟合 f(C,H)=a·C(C+H)+b·C+c，batch特征为[ΣC(C+H),ΣC,N]，使用非负最小二乘；至少5个点、默认最多30个拟合点。它与启动 f(C+H)-f(H) 的2CH项不同，不能共用系数或混称同一个公式。实现时延观测用ms，record_batch_execution_time入口的秒会乘1000；参数docstring存在seconds描述时仍以调用链/数值单位核对。

启动profiling各worker执行forward；所读标准MP路径在支持unique_reply_rank时按world_size-TP×PCP选输出，常规拓扑对应末PP阶段的首个TP/PCP位置，其他executor/外部launcher须另核对。验收保存启动拟合系数、history-ready转换、在线系数、实际chunk和时间单位；无效预测应走既定回退，不把一次拟合成功当作全部stage时延均衡。设计与predictor均为静态证据，本次未执行采样或拟合。


## 中文资料与当前英文的差异裁决

固定user_guide/feature_guide/dynamic_chunk_pipeline_parallel.po有69条有效非空译文，其中64条msgid匹配当前英文；developer_guide/Design_Documents/dynamic_chunked_pipeline_parallel.po有55条，其中49条匹配。两者均0fuzzy/obsolete，但共11条未匹配仍含旧信息。这里比较的是源码PO，不证明zh-cn/latest页面实际显示了哪些句子或构建版本。

| 源级差异 | 本卡采用的当前依据与边界 |
| --- | --- |
| smooth_factor=0退化固定chunk | 当前配置校验只接受(0,1]，0会被拒绝；关闭CPP用profiling_chunk_config.enabled=false，不用旧PO的0配方 |
| 向下对齐page_size | 当前预测器先取min_chunk下限，再向上对齐max(page_size,64)；后续预算截断与预测值分开 |
| 历史模型b·(C+H)、特征Σ(C+H) | 当前为b·C、特征[ΣC(C+H),ΣC,N]，在线用nnls；不要复用启动模型或旧译文的系数/输入 |
| 第一个PP rank计时 | 当前Scheduler按unique_reply_rank=world_size-TP×PCP选输出；Worker仍有PP0/“not used”旧注释，不能只读注释归因 |
| V1 profile_cpp位置、零额外内存声明 | 当前设计指向V2，V1代码也有CPP入口；已删除的“无额外开销”不补成通用保证，源读不等实际运行覆盖 |
| --prefiller-port单数 | 当前示例/代理声明复数--prefiller-ports；标准ArgumentParser是否接受缩写取决于实际策略，未显式别名不等于已证明单数运行失败 |

旧PO的异步CPP段落与UT注释均称V2限定，UT也将use_v2_model_runner固定True。后续沿固定v0.32.0控制面核对发现，Ascend实际V1允许列表会移除上游V1 PP异步的特定拒绝项；原生async未指定时仍可能将V1 PP解析为同步，CPP再按最终开关选类。具体链路见下节。保留V2测试意图，不再把旧限定当成当前整条控制面的硬拒绝；也不把该拒绝项移除或V1计时入口存在当作V1异步CPP已通过真实运行。SRF队列组合按现有[短请求优先](vllm_ascend_prefill_short_request_first.md)与有效Runner裁决。

## 配置联动与启动样本不是完成标志

ProfilingChunkConfig的_validate_and_link_need_timing用None区分未设置与显式false：省略时跟随enabled；CPP关闭但need_timing=true时warning后改false。min_chunk必须正，max_fit_chunk必须大于5；CPP启用时可把过大的min_chunk钳到max_num_batched_tokens并告警，PP<=1或balance同时启用会拒绝。

run_profiling_chunk_init先置_profiling_initialized，再检查executor和采样。循环目标是1次warm-up加约64次采样，并非保证64个不同/成功样本：整数取整、Worker把num_tokens钳在[1,max_num_batched_tokens]、RPC异常与空结果都影响有效数据。少于8个样本或fit返回false时不ready；同对象再调用会直接跳过，不能靠反复调用此函数认定恢复。

当前标准MP collective_rpc在无聚合器且提供unique_reply_rank时只消费该rank回复并返回标量；不指定时返回list。CPP的_extract_latency只接受数值或list第0项，不是遍历挑选正确PP结果。常规world_size为PP×TP×PCP，external_launcher还可能乘DP，所以不同executor/启动器须核对实际rank空间，不能把world rank公式当任意拓扑的PP编号。

在线样本、history_ready、history_fitted、停采信号与失败排查进入[CPP校准计时排障](../../runbooks/performance/vllm_ascend_cpp_calibration_timing_missing.md)。同步时延采集本身可能增加停顿；关闭计时的最终基准与校准阶段分开报告。

## 来源性能数字与四卡回归的不同口径

| 材料 | DeepSeek-V3.1-W8A8 128k，CPP/固定PP TTFT | Qwen3-235B 256k，CPP/固定PP TTFT |
| --- | --- | --- |
| 固定英文用户指南，A3 64GB、并发1、chunk32k | 24.04s / 28.33s | 51.41s / 55.61s |
| 未匹配PO msgid中的旧数字 | 22.5s / 27.0s | 53.5s / 61.4s |

这些是两组来源自报数字，本次未复测，不混算提升比例或当作新硬件基线。变长并发4、99% prefix命中的吞吐表也不能替代上述固定长度并发1口径；“短序列不退化”是来源描述，不提供所有负载的保证。

four_card/test_profiling_chunk_performance.py另定义Qwen3-30B-A3B、PP2TP2/EP、eager、prefix cache关闭、budget12288、smooth0.9、5次warmup+5次顺序测量，取整次generate_greedy(max_tokens=1)墙钟中位数<=BASELINE_TTFT_S=5.45。输入是重复hello的字符串，约64k token，实际tokenizer长度未在该段assert；它近似prefill/TTFT，不是流式首token时间戳。sync、sync-SRF、async共用阈值，未定义async+SRF的第四组合，也未显式冻结Runner覆盖环境。源注释要求团队同意后改基线，本次没有修改或执行该测试；5.45不推广为所有硬件、模型或产品SLO。


## CPP的V1异步选择与实际验收边界

CPP要求PP>1，但Runner选择和异步开关独立。对固定vLLM v0.32.0，async_scheduling=None进入原生默认分支；当该点读到V1且PP>1时会将async_scheduling=False，其他更早的互斥条件也能关闭它。Ascend的patch_use_v2_model_runner.py过滤pipeline parallelism with async scheduling这个后续V1拒绝项，不会因此把False重新打开。显式async_scheduling=True仍有executor/投机配置等检查，不能只凭允许列表生成通用开启配方。

平台_setup_worker_and_scheduler的CPP分支按该点的async_scheduling选择ProfilingChunkScheduler或ProfilingChunkAsyncScheduler，而不是按Runner名字猜类。其后还有batch_job_sched_config.enabled分支：若有效配置同时进入两分支，后面的BatchJobAwareScheduler/BatchJobAwareAsyncScheduler赋值会覆盖CPP类。这个局部赋值顺序不声明两项可安全联用，也不证明别处不存在校验；最终必须核对平台钩子结束后的scheduler_cls，不能只看CPP enabled。先记录用户输入（未指定/false/true）、property/补丁安装进程与时机、最终开关、实际scheduler、Runner和PP拓扑，再看profile/计时数据。允许列表、原生默认逻辑与旧PO/UT的V2意图是不同证据层；实际V1异步CPP的模型/并行/Device正确性、性能及SRF等组合仍需目标配置验证。

_validate_v1_model_runner仍存在，调用的helper仅移除允许列表中的准确标签；PCP、其他DFlash/扩展条件等不能据此一并绕过。具体字符串/多进程安装边界见[Runner规则](../../optimizations/rules/vllm_ascend_model_runner_selection.md)。本卡仍限定原A3 Prefill工作流，没有扩展硬件范围或新增NPU验证事件。
