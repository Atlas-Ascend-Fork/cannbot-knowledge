---
type: Guide
title: vLLM Ascend 性能基准：在线、离线与多模态任务的可比测量
description: 结合中文指南与基准脚本核对QPS、dummy权重、数据集和指标，保留参数/服务身份、清理范围与失败产物证据，再按同负载评估真实模型性能。 补充 Native Completion 的 TTFT、排队、ITL、tokens_per_second公式与末尾usage发射条件。；补充索引量化微基准、压测配置与 VllmBenchRunner
  单吞吐门槛的证据边界。 补充固定3164 KV-pool CPU元数据ABBA微基准的等价性与计时边界。
tags:
- task.optimization
- task.testing
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/performance_and_debug/performance_benchmark.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/supported_hardware.inc.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/performance_and_debug/performance_benchmark.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/scripts/run-performance-benchmarks.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/generate/base/serving.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/openai/completion/serving.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/prepare_indexer_indices.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/quantize_indexer_query.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/vllm_bench.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/requirements-bench.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/tests/latency-tests.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/tests/serving-tests.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/benchmarks/tests/throughput-tests.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/benchmarks/README.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/benchmarks/benchmark_kv_pool_metadata.py
  role: primary
created_at: '2026-10-29T08:40:49Z'
updated_at: '2026-11-03T06:56:11Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- prepare_indexer_indices
- quantize_indexer_query
- VllmBenchRunner
---

# vLLM Ascend 性能基准：在线、离线与多模态任务的可比测量

## 适用范围与产物

基于 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的 benchmark 文档，运行入口以实际安装的 vLLM 版本为准。适用于已完成目标硬件和模型正确性验收的环境；本文不包含四个平台的实测结果。交付配置、数据版本、原始输出、指标口径、重复记录、失败与结论边界。

## 按任务选择入口

| 任务 | 入口与关键匹配 | 重点输出 |
| --- | --- | --- |
| 在线生成服务 | 先启动服务，再 `vllm bench serve`，匹配 backend、模型与 endpoint | 成功/失败请求、请求吞吐、输出/总 token 吞吐、TTFT、TPOT、ITL |
| 离线吞吐 | `vllm bench throughput`，固定输入/输出长度与数据集 | 总 token 与输出 token 吞吐、处理请求与实际 token 数 |
| 多模态 | 使用相应 chat endpoint、数据和媒体配置 | 编码/输入条件、服务指标及实际媒体样本 |
| Embedding | `openai-embeddings` backend 对 `/v1/embeddings` | 请求/输入 token 吞吐与端到端时延；不套用生成 TPOT |

使用 `--base-url` 指定远端服务地址，`--endpoint` 保留 API 路径；不能仅修改模型名就把 completions 测试用于 chat/embedding 服务。数据集枚举和参数先核对该版本 `--help`。

## 固定测量条件

保存硬件与卡数、镜像/源码/依赖、模型权重、dtype/量化、Runner、有效图模式、并行、部署拓扑、调度、缓存和 offload。workload 保存实际输入/输出长度分布、请求数、到达速率、并发限制、采样配置和媒体规格。

固定数据集版本与本地文件，说明预热、冷/热缓存及 prefix cache 状态。`VLLM_USE_MODELSCOPE=True` 控制 vLLM 模型/tokenizer 加载，不会把 benchmark 数据下载自动转到 ModelScope；`HF_ENDPOINT` 对支持它的下载库有效，也不会改写 `wget` 或 `git clone` 的原始 URL。

## 对照与统计

先验证正确性，再一次改变一个待测因素。在线测试明确负载形态；离线饱和吞吐不能直接解释线上 SLO。分报首次启动/编译、预热后稳态和资源成本；重复执行并保留波动。存在随机性或时间变化时交替运行基线与候选，保存运行顺序。

报告区分 req/s、输出 tok/s 和总 tok/s，TPOT 按报告的“排除首 token”口径解释，ITL 与请求级 TPOT 不混用。保留失败、超时、实际 token 数和没有产生有效指标的请求；不能只用成功子集宣称整体变快。吞吐改善还须同时检查目标分位时延与失败率。

来源展示的 10 请求输出属于使用示例，没有足够完整的硬件、控制变量和重复证据，不能转为 Benchmark Observation、性能上限或优化收益承诺。只有满足完整观测字段和对照要求的结果才另建性能观测卡。

## 验收、停止与回退

期望任务、backend、endpoint、输入规模、有效配置和指标口径一致后才比较。输出错误、样本变化、失败率升高、负载未受控或波动盖过差异时，保留原始结果并停止收益结论，恢复基线配置。需要归因时沿[服务剖析指南](vllm_ascend_service_profiling.md)采集线索，并用关闭 profiler 的运行复核最终性能。

## Evidence

固定 benchmark 文档提供在线、离线、多模态和 Embedding 入口、数据准备边界及报告字段。上述对照记录是基于这些测量口径组织的工程验收方法，本次未执行 benchmark，也没有生成性能数字。



## 与模型质量验收对齐

使用AISBench、EvalScope、lm-eval或OpenCompass时，先按[精度验收合同](../bringup/vllm_ascend_accuracy_evaluation_contract.md)固定数据、few-shot、模板、答案过滤和有效模型参数；工具的accuracy/eval与perf入口分别记录。服务启动或压测200不替代[首请求与真实权重](../../runbooks/runtime/vllm_ascend_first_request_false_ready.md)验证，少样本演示分数不作为全数据集门槛。归因性能变化时保留原质量标准，不能通过改变后处理或样本范围得到“性能和精度均通过”的表象。


## 系统参数实验的测量入口

实验 TCMalloc、NPU allocator、下发队列、HCCL 或 OS 配置时，先按[系统调优合同](vllm_ascend_system_tuning_contract.md)核对修改层级、框架回写与每个 Worker 的实际值；CPU/NUMA/IRQ 的部分成功见[绑定指南](vllm_ascend_cpu_numa_binding.md)。保留质量门槛和同一负载，再用本卡测量吞吐、失败率与尾延迟；配置设置成功和服务能启动都不是优化收益。


## AISBench 定时采集与产物追溯

自动采集按[定时剖析及产物完整性](vllm_ascend_aisbench_profile_artifacts.md)核对正式请求起点、成功请求阈值、服务实例表、各节点/rank、raw/parsed和上传/合并状态。小索引能下载、tar存在或控制端点返回成功都不单独证明采到了目标窗口；工具侧验证、报告JSON与性能基线应按各自判据解释。


## 中文基准资料、固定QPS与版本冲突

performance_benchmark.po的35条有效译文均匹配当前英文，另完整阅读同commit的benchmarks/README.md与run-performance-benchmarks.sh。主指南概述称固定QPS，但其基本在线命令未显式指定请求率；仓库脚本则从qps_list生成--request-rate。README列1/4/16/inf，称有限值按带固定seed的Poisson到达、inf为一起到达。实际seed、到达率/并发和采样序列仍要保存，不从章节标题认定每次CLI调用已构造同一种负载。

README的--endpoint-type示例与主指南--backend写法不同，其swap_space的磁盘解释也没有在本批得到原生配置证明；不把同commit旧README当所有CLI字段的当前真值。实际安装版本、有效argv、服务参数与client/backend/endpoint分别固定。README的约800秒/模型是来源估计，不作任意模型/拓扑的运行时间预算。

## dummy权重、数据集与指标分别留证

README推荐--load-format dummy以节省下载，说明会构造随机权重。dummy只作为明确标注的性能探针，不能替代真实权重适配、质量或真实模型工作负载验收；先按[首推理验收](../bringup/vllm_ascend_first_inference_acceptance.md)核对真实模型身份。

表中HuggingFace-展示名称通常对应dataset-name=hf，本地dataset-path还需匹配hf-name；RandomMultiModal在该表仅在线部分支持、离线开发中，Sonnet已deprecated。ShareGPT4V媒体需另备，allowed-local-media-path、chat payload和实际样本一起核对。HF_ENDPOINT只影响支持它的下载库，VLLM_USE_MODELSCOPE不重定向dataset；本批没有下载、安装或改全局pip镜像。

多模态示例使用--no-stream，客户端可见的响应时点与服务端生成首token时点需要按目标客户端实现区分，不凭TTFT列名宣告已观测后者。示例的10成功/0失败、均值/中位/p99、peak output tok/s和embedding E2EL都是演示输出；10请求不是所有命令省略num_prompts时的默认值，也不足以给任意部署承诺尾部SLO。区分req/s、输出/总tok/s与峰值，不能跨任务/冷暖/请求率直接比较。

## 仓库批量脚本的执行与失败边界

json2args把下划线改连字符、将值转成字符串，随后经eval或bash -c执行。它没有保留结构化argv边界；嵌套JSON、空格路径和特殊值不能假定原样传递。脚本配置需要受控，适配Agent生成实验时应保留结构化参数与实际有效配置，不直接将任意外部参数串交给该拼接路径。

wait_for_server对localhost:8000/health轮询最多1200秒，只使用curl退出状态，未核HTTP状态、响应内容或模型/进程身份；超时分支仅打印后仍继续QPS循环。server/client模型字符串一致的预检查不证明该端口属于刚启动的server_pid。ready、真实权重首请求、有效压测结果应各自作为可失败阶段。

kill_npu_processes会枚举全系统进程、处理8000端口，并广泛终止python3/VLLM进程及移除用户vLLM配置；不是只清理本次server_pid。main还可能安装系统依赖、下载固定路径数据；cleanup_on_error会删除结果目录，退出另有cleanup。不要在共享宿主直接复用整脚本；采用受控隔离环境或维护本任务进程生命周期和独立run目录，并预先保留配置、stdout/stderr和失败产物。本批只读取源码，没有调用脚本或任何清理函数。

TEST_SELECTOR可跳过用例，模型名不一致也会continue，不能以脚本退出或results存在证明全部case已跑。结果名来自test_name及QPS，所读流程没有自动把npu_type追加到每个文件名；硬件、驱动、模型revision与有效权重模式须另存。update_json_field添加的model_name也是字符串元数据，不替代原始服务/客户端日志或真实设备证明。


## Native Completion：服务端逐请求时间与客户端测量边界

本节对照固定 vLLM v0.32.0 的 `build_per_request_timing_metrics` 全文与 Completion 的实际响应映射选段。它补充上文客户端基准口径，未运行基准或上游模块，也不证明 Ascend 分支已接通这些字段。先核实部署版本、endpoint、采样与字段开关，再对齐时间边界。

令 Q、S、F、L 分别为 queued_ts、scheduled_ts、first_token_ts、last_token_ts，N 为本次实际生成的 token 数，时间戳单位为秒。以下是源码中的服务端计算口径：

| 字段 | 计算与前提 | Agent 解释边界 |
| --- | --- | --- |
| time_to_first_token_ms | (F−S)×1000，S/F 均正 | 从调度到首 token，排除初始排队；不等于客户端端到端 TTFT |
| queue_time_ms | (S−Q)×1000，Q/S 均正 | 排队单列；不能用上述 TTFT 的下降推断请求端总等待下降 |
| generation_time_ms | (L−F)×1000，F/L 均正 | 仅首末 token 间 decode 区间，排除排队和 prefill/TTFT |
| mean_itl_ms | (L−F)/(N−1)×1000，F/L 均正且 N>1 | 单 token 无此平均值；不直接替代客户端逐事件 ITL 分布 |
| tokens_per_second | N/(L−S)，S/L 均正且 L−S>0 | 包含首 token 前的推理区间，分子含全部生成 token；不是 mean_itl_ms 的倒数 |

缺少 metrics 或必要时间戳时，相应字段保持 None；多数差值仅检查时间戳为正，不保证乱序差值全部被钳到零。异常值应保留原始时间戳排查。示意 Q=1、S=2、F=3、L=5、N=3 可由公式推出 queue=1000ms、TTFT=1000ms、generation=2000ms、mean ITL=1000ms、输出吞吐=1 token/s；这只是算术示例，不是实测。这个例子恰好倒数相等，不代表普遍等价；例如 N=2 时吞吐=2/3 token/s，而 ITL=2000ms。

### 字段何时进入 Completion 响应

非流式 `request_output_to_completion_response` 只在 final_res_batch 恰好一个且 n（空值按1）为1时附加可归属的逐请求指标；时间字段还受 `enable_per_request_metrics` 控制。`build_spec_decoding_metrics` 从第一个输出序列读取已有统计，调用方抑制多 prompt 或 n>1；投机 acceptance 的存在检查独立于时间开关，可能创建只有 speculative_decoding 的 metrics 对象。不能看到 metrics 对象就认为所有计时字段已开启，更不能把缺失 acceptance 当零接受率。

流式指标附在最后的 usage chunk，要求 include_usage 已启用（注释指 stream_options.include_usage 或 enable-force-include-usage），同样要求一个 prompt、n=1；计时开关和投机统计分别处理。普通内容块没有 metrics，或者关闭 usage 后未收到末尾指标，不足以判断推理没有发生。system_fingerprint 在该最终 usage 块可携带，亦不是每块都发。

Usage 的 completion_tokens 按实际 output.token_ids 累加，echo 拼入 prompt 文本不让这些 prompt token 自动变成生成 token。多 prompt/n>1 的 usage 可以聚合，但本实现主动不附加对应单流计时，不得据此补造平均 TTFT 或 acceptance。

对照实验同时留客户端开始/首事件/结束、服务端 Q/S/F/L（若可取得）、实际输出 token、排队和错误事件；确认吞吐分母后再决定优化调度、prefill 或 decode。源码公式仅是控制端统计证据，不能代替 NPU kernel、通信或 Agent 任务完成率。完整 Chat/Responses 发射链和统计采集时钟不在已读范围。


## 索引微基准与压测入口的证据边界

本节以固定 Main 快照为准，不是当前各硬件的实测成绩。`prepare_indexer_indices.py` 和 `quantize_indexer_query.py` 是算子微基准；事件时间不能替代请求排队、调度、编译或端到端服务耗时。

| 入口 | 正确性先决条件与计时范围 | Agent 的解释边界 |
| --- | --- | --- |
| `prepare_indexer_indices.py` | 可见上界为 `(positions + 1) // compress_ratio`；筛选非负且小于可见上界的索引，无效项临时置 INT32_MAX，排序后还原 -1；重复索引保留。先以 rtol=atol=0 比较，再计时 | 默认 token 数 1/32/256/4096、TopK 128/2048、position=4095、压缩比 2；单一分布与设备 0，不能当动态位置或重复去重的证明 |
| `quantize_indexer_query.py` | FP32 最大绝对值除 127 后先转 FP16，再 clamp 至至少 2^-24；用该舍入后的 scale 做除法、round 和 ±127 截断，得到 int8。先精确比较量化值和 scale | 默认 BF16、32/64 个 head、head dim 128，与先用 FP32 scale 量化再转换不是同一数值合同；shape 正确不代表模型质量 |

两脚本均固定 seed=41，在设备 0 上先 warmup/synchronize，再 capture 与 replay，取 5 次事件计时的中位数并换算单次微秒。前者先估计时间，再把 batch 限在 1–32、repeat 限在 1–20；后者固定 batch=32、repeat=20。两者均有 3 次 capture 前 warmup 与 3 次 replay warmup。记录这些参数、输入分布、编译与预热是否另计，才能比较结果；不能把图内循环事件时间填写为线上 TTFT。

### 仓库 JSON 是计划输入，不是已通过的成绩

- `latency-tests.json` 含 Qwen3-8B 与 Qwen2.5-7B 两例，TP=1、dummy 权重、5 次 warmup 与 15 次测量；只有前者显式设置 max_model_len=16384。
- `serving-tests.json` 三例使用 QPS 1/4/16/inf 和 200 prompts。Qwen2.5-VL-7B 使用真实权重、`openai-chat`、`/v1/chat/completions`、vision-arena-bench-v0.1 的 train 切片且 no_stream；两个文本模型使用 dummy 权重与固定绝对路径的 ShareGPT 文件，需验证本地数据存在。
- `throughput-tests.json` 三例同样 200 prompts；VL 使用 `vllm-chat` 与 HF 数据，两个文本模型是 dummy 权重与 vllm backend。这不是所有模型、上下文长度、硬件或质量场景的覆盖。
- `requirements-bench.txt` 只列数据处理依赖（含 modelscope<1.38、pyarrow<26），不是 CANN、torch_npu 与推理框架环境锁文件；不能据此恢复运行 ABI。

### `VllmBenchRunner` 的副作用与单指标门槛

`tools/vllm_bench.py` 的构造阶段就可能下载 ModelScope 模型、执行 bench 子进程并读取成绩；失败可能发生在 `__enter__` 之前，因此不能仅凭有 context manager 就断言失败一定走 `__exit__` 清理。退出路径 terminate、最多 wait 8 秒后 kill，不等于管理了所有后台服务。

入口使用 `vllm bench serve`、openai-chat/chat-completions、trust_remote_code、50/90/99 分位数和保存结果，server-ready-timeout=0。`_concat_config_args` 会修改传入字典：ignore_eos=True 变成空字符串参数，False 删除该项；其他值统一 str 化，不能假定是通用 argparse 布尔参数序列化器。stdout/stderr 经 communicate 收集，没有显式子进程总超时。

成功后从当前工作目录读取按秒生成的文件名，只断言 `output_throughput >= baseline * threshold`，默认 threshold=0.97。这不是 TTFT/尾延迟、请求失败率、准确率或可重复性门槛。并发任务需分离工作目录和结果名，保留完整 argv、退出码、JSON 与服务配置，防止同秒覆盖及误取历史文件。


## 固定3164：KV-pool CPU元数据ABBA微基准

benchmark_kv_pool_metadata.py与README新增的是CPU准备成本实验，加载两份真实scheduler/worker模块、使用NumPy与立即返回的mock store；不启动模型、外部存储或NPU。两个源码修订必须能在同一已配置vLLM依赖环境导入，不能因为计时在CPU就按无依赖脚本处理。本次仅阅读，没有运行微基准。

baseline-root、candidate-root、output必填；warmup/rounds/iterations必须正数，默认3/5/3。每round顺序baseline,candidate,candidate,baseline，每variant默认30个样本。reset和verify放在计时之外，只计目标方法调用；scheduler的异步load回调替换为ID记录器，不包含真实加载、完整scheduler step、KV传输或服务耗时。

26个场景包括8个128/512/1024/4096请求、全部或一半已在scheduled cached列表的过滤；14个128/4096 cached ID与0/1/4 unfinished在头部、尾部或不存在的稀疏情况；4个128/512/2048/8192块的layerwise GVA准备。这里的cached关系不是外部KV命中率。回调顺序hash、GVA hash、metadata/lease次数与key数量会逐次核对，两variant指纹先相等再比较计时。

输出保存median、插值p95、全部raw_ms、样本数、loaded模块路径、文件SHA与可取得的Git revision。脚本没有自动收益门槛；不能只挑dense场景或单个中位数宣称整体优化，也不能把局部metadata加速换算成TTFT或端到端吞吐。环境线程数、源码身份、稀疏常数项和运行顺序应随结果保存。
