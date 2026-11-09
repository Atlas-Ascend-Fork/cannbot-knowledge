---
type: Guide
title: vLLM Ascend 精度验收：评测工具、数据口径与模型回归合同
description: 核对AISBench、EvalScope、lm-eval与OpenCompass的中文评测、数据和答案解析，审查回归有效参数与相对容差，区分lm-eval报告的ACLGraph配置标记和实际capture/replay证据。
tags:
- task.testing
- task.design
- topic.model_adaptation
- topic.precision
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/test_lm_eval_correctness.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/evaluation/using_ais_bench.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/evaluation/using_evalscope.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/evaluation/using_lm_eval.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/evaluation/using_opencompass.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/conftest.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/report_template.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-8B.yaml
  role: example
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/verdict.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/utils.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/evaluation/using_ais_bench.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/evaluation/using_evalscope.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/evaluation/using_lm_eval.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/evaluation/using_opencompass.po
  role: supporting
created_at: '2026-10-29T16:27:59Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T07:40:31Z'
---


# vLLM Ascend 精度验收：评测工具、数据口径与模型回归合同


## 范围与验收层次

本卡蒸馏固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的四份评测指南和模型回归脚本。外部评测工具、数据集链接和CLI示例没有固定到本次已安装版本；实际使用需先固定工具与数据revision并核对相应CLI。指南的单NPU示例没有明确整套流程的硬件产品集合，本卡保持draft/空平台，不把Qwen样例的A2标签扩成所有工具的全部硬件支持。

[首请求smoke](../../runbooks/runtime/vllm_ascend_first_request_false_ready.md)、真实权重加载、任务精度和[性能基准](../optimization/vllm_ascend_benchmark_workflow.md)分别保留证据。服务200非空不是任务质量达标，压测成功不是精度达标，小样本示例也不是完整数据集验收。

## 选择工具与实际执行路径

| 工具/模式 | 固定指南的入口 | 需要对齐 | 产物与边界 |
|---|---|---|---|
| AISBench在线精度 | `ais_bench --models vllm_api_general_chat --datasets ... --mode all --dump-eval-details --merge-ds` | `attr=service`、API backend、served model name、host/port、tokenizer/权重path、generation与postprocessor | configs、infer/eval logs、predictions、results、summary；配置名属于工具版本合同 |
| AISBench性能 | `--mode perf --summarizer default_perf`；文本或stream chat/媒体adapter | 同一数据集配置和请求格式；accuracy与perf示例可能用不同配置别名 | performances明细/图表，不自动产生同口径任务精度；TextVQA在该页给的是图文perf例子 |
| EvalScope在线精度 | `evalscope eval --eval-type server --api-url .../v1 --datasets gsm8k` | 模型名、server客户端参数、数据集、limit | 文档`--limit 10`只取10项；示例AverageAccuracy不是本次结果 |
| EvalScope在线压测 | `evalscope perf --url .../v1/chat/completions --api openai` | parallel、number、dataset、stream和生成参数 | 请求成功/失败、吞吐、TTFT/ITL/时延分位与结果DB；不能拿perf代替eval |
| lm-eval在线 | `--model local-completions`，base_url含`/v1/completions`，tokenized_requests=False | 原始prompt与chat模板、server模型名、任务版本、few-shot与答案filter | 文本服务接口评测，保持实际server拓扑；示例与chat-completions不互换endpoint |
| lm-eval离线 | `--model vllm`，pretrained/长度及batch参数 | 新建模型实例的真实dtype、量化、TP、模板等 | 不测试另一个已启动HTTP服务；必须确认当前NPU插件和有效配置 |
| OpenCompass在线 | OpenAISDK，openai_api_base含`/v1` | path与tokenizer_path、meta_template角色、采样/长度、query_per_second/batch/retry | 文档仅`ceval_datasets[:1]`，不是全部C-Eval；Python3.10是该指南示例兼容选择，不是所有工具版本的通用要求 |

不要同时更改工具、模板、数据、解析和并行后仅比较最终分数。固定源中的模型名、时长、分数和token吞吐是使用示例，不提供本次结果、统一准确率基线或性能承诺。

## 数据、输入与结果口径

### 数据集与答案处理

AISBench指南列出C-Eval、MMLU、GPQA、MATH-500、LiveCodeBench、AIME2024、GSM8K；必须连同具体数据集配置revision保留，而不是只记录通称。`max_out_len+实际输入长度`必须满足服务实际context预算；文档中35000附近的server长度与32768输出配置是示例，不保证长prompt任意可用。

推理采样、seed、stop、chat/reasoning模板和`extract_non_reasoning_content`等后处理影响最终答案。保持与参考相同，不把移除推理文本或改变答案regex产生的分数变化直接归因于NPU算子。

lm-eval的GSM8K示例分别报告`exact_match,strict-match`与`exact_match,flexible-extract`；两种提取规则不能合并成一个准确率。few-shot数量、fewshot_split、test_split、模板和task metadata版本都要固定。OpenCompass只选一个subject、EvalScope只选10条、或任何limit截断，都必须在报告中明示。

### 下载来源与离线输入

lm-eval指南在vLLM使用ModelScope的环境中另设`USE_MODELSCOPE_HUB=0`，以免评测数据来源被误选；模型下载、tokenizer下载和评测数据下载是不同层。外部镜像地址和工具环境变量不构成数据内容等价证明。

离线lm-eval需`HF_DATASETS_OFFLINE=1`并给出可解析的本地dataset_path、dataset_kwargs.data_files、split与few-shot配置。GSM8K的train/test和MMLU的dev/test职责不同；只有缓存目录存在不能证明工具实际用了期望版本或划分。

### 多模态400先查客户端合同

AISBench文档给出的TextVQA错误同时包含相对图片路径和`image_url ... Input should be a valid dictionary`。文档建议修正路径；从错误本身还需检查客户端序列化后的请求字段结构，而不是只改路径便认定问题解决。确认媒体文件在实际读取它的进程环境可见、adapter产生正确payload后再发单请求。这个400不提供NPU数值故障证据；应先做输入协议排查。本段是对固定报错的静态诊断，未复现该外部工具版本。

## 仓内模型回归脚本的实际合同

### 配置选择与参数优先级

`tests/e2e/models/conftest.py`按`--config`选择单一YAML，或按`--config-list-file`逐行选择多个YAML。列表中的相对路径以列表文件父目录为根；单一配置按调用工作目录解析。`--tp-size`默认字符串1，`--report-dir`缺省为benchmarks/accuracy。

`test_lm_eval_correctness.py::build_model_args`先用`--tp-size`构造tensor_parallel_size，再由serve中的同名字段覆盖；因此不能只把CLI的TP值抄到报告。它只透传源码列出的serve键：max_images、gpu_memory_utilization、enable_expert_parallel、tensor_parallel_size、enforce_eager、enable_thinking、quantization；dtype、max_model_len和trust_remote_code另有默认值。任意新增YAML键不会自动变成vLLM参数。

有效模型名取model_name；model_type默认vllm。脚本对model_type=vllm-asr跳过，不能把该skip当作ASR已通过。hardware字符串用于报告，不是硬件调度或能力过滤器。Qwen3-8B.yaml中的Atlas A2、模型名和期望值只是该配置的声明，不证明在别的产品上运行过。

### 评测与判定

脚本直接调用`lm_eval.simple_evaluate`，传入tasks、模型参数、模板、fewshot_as_multiturn、limit、batch_size，并按配置覆盖num_fewshot等。每个task的metrics含name和value；name必须与返回字典的指标键完全一致。

```python
measured_value = round(task_result[metric_name], 4)
task_success = bool(np.isclose(ground_truth, measured_value, rtol=0.05))
```

这里的ground_truth来自YAML的value，measured来自本次结果；先round再比较。rtol是相对容差参数，不是放宽5个百分点；源码没有显式指定atol，其具体语义和默认值以实际NumPy版本为准。不得为让当前候选通过而反写期望值。提高或降低某项分数都要保留原始结果和接受标准，不能以更换filter或减少样本掩盖失败。

`success`对所有指标取累计AND，最后assert整体通过。报告表格的Value符号也使用这个累计success：前一项失败后，后续实际通过的项仍可能显示❌。逐项归因要看打印的task_success、ground_truth和measured，以及原始结果；不能仅按后续行图标推导每一项均失败。

### 报告的可追溯性与局限

环境版本字段从环境变量读取，缺失会写unknown；不是自动探测出真实安装版本。报告将未设enforce_eager的配置标作ACLGraph，这只是配置推导，不能替代capture/replay证据。

生成文件名是model_name的basename，未自动加TP、量化或run ID。不同实验共用report_dir可能覆盖结果；每次使用独立输出目录并保留已评审的基线。脚本生成Markdown汇总，没有足够证据表明它自动保存了每条原始预测；按所选工具核对详细日志与预测输出，不假定汇总分数可独立复算。

## 可审核的验收记录

每次至少记录模型/checkpoint/processor/tokenizer revision、两仓commit、实际硬件/卡数与软件版本、有效模型参数、工具版本、数据集与配置revision、样本数和split、few-shot/模板/采样/答案过滤、指标全名与参考/测量值、stderr、原始结果路径及失败/skip。

AISBench的configs/predictions/results/summary分别保留配置、预测、原始分数和汇总；其文档说明`--debug`将日志直接打到终端，不应假定仍有完整中间日志文件。EvalScope压测DB与准确率eval输出是不同证据。迁移新模型时先建立可信参考，再评估量化、并行、图或投机变化，最后进入性能对照。

本次仅静态阅读四份指南、模型回归定义、fixture和报告模板；未安装评测工具、下载数据/权重、执行回归、调用模型或生成精度/性能结果。工具接口与示例版本变化、缺少硬件声明或其他模型任务的专用评测仍保留为待核验。


## 模型精度回归与nightly JSON不是同一判据

本卡的模型lm-eval测试逐指标round后做isclose并最终assert；nightly benchmark另有accuracy绝对差、performance吞吐比例、spec_decode逐位置下界，以及pytest退出码加顶层pass_fail消费者。具体进入[pytest成功仍回归的判据排查](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)，不能把一个流程的threshold或成功状态套给另一个。定位引入变化的提交再按[auto_bisect合同](vllm_ascend_regression_bisect_contract.md)检查端点、环境与嫌疑区间；退出0、上传完成或非空first_bad字段都不是精度/性能已验收的充分证据。


## 短logprob差分与任务数据集评测的衔接

图后端/Xlite的compare_logprobs另有[3-token差分合同](vllm_ascend_graph_logprob_validation.md)：先核对删去整个additional_config后的eager基线、绝对logprob容差、单向top-20检查和外层输出完整性。该helper适合定位短prefill/decode差异；其通过不替代本卡的数据集、模板、指标与完整任务验收，Xlite双卡非空smoke及pass占位UT也不能补出任务准确率结果。


## 中文评测指南的输入与示例边界

固定来源的using_ais_bench.po、using_evalscope.po、using_lm_eval.po、using_opencompass.po均按当前英文逐项核对。它们提供工具使用入口；服务startup complete、单curl响应、下载完成、工具help与完整精度评测是不同验收阶段。四工具的外部仓库/依赖/数据版本仍需在实际实验中固定，本卡没有安装或执行它们，保持draft和未定位平台。

### AISBench：上下文预算与可复算产物

AISBench示例服务设置--max-model-len 35000，而随后的说明写“大于35000”，两者不一致。32768的max_out_len也是建议值，不能将任意输入都塞入该配置；按真实tokenizer、模板/特殊token及服务有效context核对输入加输出预算，并记录截断、拒绝和输出耗尽。配置中的xxx、xxxx需替换为本次实际值，不能把展示片段当完整可执行配置。

VLLMCustomAPIChat的attr、type、abbr、path、model、host_ip/host_port职责各异；本地任务名不证明服务实际checkpoint。示例generation_kwargs给temperature=0.6、top_k=10、top_p=0.95、seed=None、repetition_penalty=1.03，并用extract_non_reasoning_content处理预测，不能与另一套确定性解码或保留推理文本的结果直接归为同一精度基线。request_rate=0和retry=2是该示例工具配置，不据此推导vLLM bench的inf、吞吐或实际重试次数。

C-Eval、MMLU、GPQA、MATH-500、LiveCodeBench、AIME2024、GSM8K应固定具体配置别名、split、版本和样本数；GSM8K精度与perf命令的配置别名不同，不能只看通用数据集名判定同负载。准确率保存configs、predictions、results和summary，性能保存performances中的CSV/JSON、details.h5/details.json和分布图；后者不会自动补出前者。--debug文档说明中间日志转到屏幕，要另外保留终端输出。TextVQA修路径后仍要检查image_url对象结构和实际读图进程路径，不能以一次400认定NPU精度故障。

### EvalScope：10条精度样例与20请求流式压力样例

EvalScope精度例用--eval-type server、/v1、gsm8k和--limit 10；AverageAccuracy=0.8只是来源10条演示。性能例用/v1/chat/completions、--api openai、--parallel 5、--number 20、openqa与--stream，是另一任务。parallel是并发配置，不是固定QPS，不能把两组输出当同一次实验。

压力输出示例给20成功/0失败、38.3744秒、请求吞吐0.5212 req/s、输出吞吐132.6926 tok/s、总吞吐158.8819 tok/s；它们与平均输入50.25、输出254.6的汇总可做算术核对，允许展示值精度带来的小差异，不要求逐位相同；这不是本次设备测量。平均TTFT/每输出token时间、package latency/package数量与各分位ITL各有口径；分位行不是同一条请求的逐项组合，也不能把不同统计列混算一个端到端SLO。保存benchmark_data.db、失败项、客户端流式接收和服务配置，不能只截最终表。

### lm-eval：展示答案与答案过滤器都先校验

lm-eval指南的在线章节称GSM8K，但curl实际是资产负债率/流动比率选择题，max_completion_tokens=1，示例返回A且finish_reason=length。按该题数字，总资产31、负债16、流动资产19、流动负债7，算得约51.61%和2.71，与所列选项均不相符。因此该A只展示响应格式，不能当任务金标、数学正确性或完整GSM8K通过证据；这是文档玩具算术核对，没有调用模型。

在线local-completions与离线--model vllm启动/调用路径不同，文档约30分钟与1到2分钟也不是可承诺耗时。示例GSM8K输出在线flexible-extract/strict-match为0.3215/0.2077，离线为0.3412/0.3139，来源未给足条件将差异单独归因于硬件或HTTP。先核任务版本3、5-shot、实际prompt、tokenization、stop和采样再比较。

本地GSM8K YAML的doc_to_text要求“The answer is xxx”，strict-match却提取####后的数字；doc_to_target保留原answer，metric还有忽略####之前内容等处理。应检查工具最终生效的filter与metric链，先用已知预测/金标测试格式，再定位模型输出，不能盲改regex后宣称数值精度恢复。flexible-extract可能取到别的数字，两种filter各自留分数。MMLU示例则是multiple_choice/acc、dev作fewshot、test作测试，不与GSM8K generate_until/exact_match混用。

离线数据需HF_DATASETS_OFFLINE=1、dataset_path、dataset_name=null或匹配的多科目配置、data_files和本地split；设置离线标志本身不创建数据。vLLM模型来源变量VLLM_USE_MODELSCOPE与评测数据USE_MODELSCOPE_HUB=0按指南分开，HF_ENDPOINT不保证数据内容等价。trust_remote_code示例不是所有新模型必需的默认权限。

### OpenCompass：单科结果与客户端模板

OpenCompass示例固定datasets=ceval_datasets[:1]，只评ceval-computer_network；68.42是来源单科演示，不是全部C-Eval成绩。示例Python3.10为所引兼容问题的选择，pip包与另clone仓库没有共同冻结版本，应在实际实验记录两者以及加载到的模块/配置，不能仅凭目录名认定一致。

OpenAISDK的API base为/v1、path与tokenizer_path都指Qwen2.5-7B；meta_template给HUMAN/BOT/SYSTEM角色。client的max_seq_len=4096、max_out_len=1024与服务max_model_len=26240不是同一个上限；query_per_second=1、batch_size=8、retry=3也不能直接当8 QPS。保存最终请求、模板、工具有效配置、数据版本及失败重试计数，再对照参考分数。DATASET_SOURCE=ModelScope是此例的数据来源设置，不是所有评测工具通用开关。


## lm-eval报告中的ACLGraph标记如何解释

模型精度回归报告在未设置enforce_eager时写ACLGraph，只是由配置推导的展示标记，不是记录了实际capture/replay，也不证明没有发生Runner或图模式回退。核对报告标记时，同时保存有效enforce_eager、Worker/Runner、实际图模式、capture/replay或回退日志，再按本卡的任务数据集结果判断质量。

报告的环境字段缺失可写unknown，文件名只取model basename；不同拓扑/量化/图实验使用独立report_dir保留原始预测与配置，不能用同名Markdown、ACLGraph列或单条成功日志替代这组证据。此处补充的是固定回归脚本既有报告合同，未运行lm-eval、图捕获或NPU。
