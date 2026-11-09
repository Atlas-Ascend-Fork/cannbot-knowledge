---
type: Runbook
title: vLLM Ascend pytest 退出 0 仍回归：pass_fail JSON 与判据漏检
description: 追踪 nightly benchmark 的 accuracy、performance、spec_decode 和 pass_fail JSON，核对投机接受率的 Prometheus draft 计数器增量与逐位置阈值；检查 pytest 退出0、缺失结果、zip截断、二分消费者和报告标签，避免误报通过。 补多节点task_passed、无顶层pass_fail及报告身份/覆盖限制。
  核对报告字段vllm_ascend_version与VLLM_ASCEND_REF标签，避免将分支标签解释为真实源码SHA。
tags:
- task.debugging
- task.testing
- topic.model_serving
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/verdict.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/single_node/test_single_node.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/single_node/single_node_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/result_postprocess.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/test_multi_node.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/dp_mode.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/aisbench.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/spec_decode_metrics.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/benchmark_results.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/internal_dp/test_multi_node.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/test_external_dp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/runtime.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/external_dp_config.py
  role: implementation
created_at: '2026-10-29T17:03:39Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T03:14:50Z'
aliases:
- benchmark_results.py
- task_passed
- build_task_entry
- write_results_json
- external_dp_pd
- benchmark vllm_ascend_version 报告身份
---

# vLLM Ascend pytest 退出 0 仍回归：pass_fail JSON 与判据漏检


## 信号与范围

固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`：pytest退出0、进程完成或日志显示通过，但nightly benchmark未达目标，或结果信息不足却被二分消费者记为PASS。本卡追踪单机JSON生产、后处理及`tools/bisect/verdict.py`消费者；没有全产品声明与本次硬件运行结果，保持draft/空平台。

模型lm-eval回归脚本的`np.isclose(...,rtol=0.05)`与这里的nightly阈值是不同协议，不能混用。先保留原始YAML、effective配置、工具/模型/硬件身份、pytest退出码、整轮日志和当轮JSON，再解释判据。

## JSON生产与pytest返回是两条信号

common单机入口收集配置中启用的benchmark，调用run_aisbench_cases；随后`_save_benchmark_results_json`将各task和顶层pass_fail写入`benchmark_results/<safe_job>.json`。只有test_content包含benchmark_comparisons才额外调用相对对照assert；写出顶层fail本身没有assert。因此pytest退出0与JSON fail可以同时发生。

| `_task_passed`分支 | 实际接受条件 | 不能错误套用的解释 |
|---|---|---|
| result为空字符串 | False | 不是有效测量0 |
| baseline或threshold任一缺失 | 对其余非空结果直接True | 不能据此宣称比较过基线 |
| accuracy且result是数值 | abs(result-baseline)<=threshold | threshold是绝对差值，不是lm-eval的rtol，也不是吞吐比例 |
| performance且result为长度2的list | 从Output Token Throughput.total解析数值，要求>=threshold*baseline | output tok/s，不是总tok/s、TTFT或统一百分比；解析失败False |
| spec_decode且result为list | baseline必须为同长度list，各位置actual>=golden*(1-threshold) | 逐位置下界，不是统一平均接受率 |
| 其他类型/未命中形状 | 当前实现最终返回True | 不等于该类型和结果已被专用验证器覆盖 |

顶层`_all_passed`对zip(case_configs,results)取all，没有先验证两侧数量相等。空配对的all为True，长度不匹配会截断；tasks构造也用zip。必须核对实际期望case数、结果数及每个case的身份，不能只读顶层pass。

性能报告的指标清洗会去掉token/s、ms、s等字符串，并未做通用时间单位换算。hardware从CI runner名推导，dtype仅按模型名含w8a8且quantization=ascend判w8a8，否则写bf16；feature也多从参数/环境推导。这些报告标签不是实际设备、每层dtype、内存layout或功能重放的证明。

## 比较配置可能没有实际执行

`run_benchmark_comparisons`当前只实现TTFT，支持<、>、<=、>=，阈值为指定baseline测试值乘ratio。空比较列表、缺baseline/target、缺指标数据、不支持的metric/operator都可能warning后continue，并不自动使pytest失败。

test_content的未知handler也只warning；spec_decode_acceptance未给baseline会warning返回。配置拼错、漏项、没有有效benchmark或比较未执行，不能用总退出0代替“已覆盖目标检查”。SingleNodeConfigLoader要求非空test_cases与相应必需字段，但没有替每个性能比较建立完备schema证明。

标准服务路径会保存dispatch错误，仍运行benchmark后再抛出第一条dispatch异常；因此同一轮可能有可读benchmark文件而pytest失败。应同时判断功能与benchmark，不能用后生成的JSON覆盖先前功能失败。EPD和多机路径需要继续按各自实际实现核对，不把单机控制流泛化到全部部署。

## 二分消费者的精确优先级

| 顺序 | RunOutcome条件 | evaluate结果 |
|---:|---|---|
| 1 | infra_error=true | SKIP，使用原因说明 |
| 2 | pytest rc为2/3/4/5/124 | SKIP；124是工具timeout哨兵 |
| 3 | 其余非零rc | FAIL，不再以JSON覆盖 |
| 4 | rc=0且结果目录直接子级任一可读JSON的顶层pass_fail恰等于小写fail | FAIL，baseline/threshold miss |
| 5 | rc=0且未发现该信号 | PASS，含下述证据缺口情形 |

消费者只glob目录直接子级的`*.json`，不递归、不逐task验证、不核对expected case数，也不强制必须存在结果。目录不存在/未提供返回“没有失败”；JSON解码或读取错误warning后跳过；缺key、大小写不同或只有nested fail也不会命中。解析成功但不是字典的类型不在统一容错范围，不能宣称所有坏输入都被安全转成SKIP。

这是消费者的实现行为，不是“缺结果可视为真实通过”的验收准则。没有benchmark要求的功能用例可另按功能证据判断；需要证明精度/性能的任务若缺期望结果，应保持未验证，修复采集后重跑。

## 排查探针与结果隔离

1. 确认实际运行的整份YAML、test_cases数、启用benchmark键、test_content、baseline/threshold和比较列表，不只看作业名。
2. 对齐producer结果数与配置数，逐项确认case_type、结果类型、解析出的指标、单位和原始值；核对每个期望case都出现。
3. 保存pytest rc、第一条异常和warning。确认比较是否实际执行；集合错误被归SKIP仍可能来自候选代码/配置回归，不能当作代码无问题。
4. 检查二分runner实际传入的results_dir：单机repo下benchmark_results，多机master为按job命名的缓存目录。它每轮尝试清理后重建；删除错误被忽略，仍需确认没有上一轮残留。
5. 逐文件确认有效JSON对象、run/commit/config对应关系、顶层与task的pass_fail、任务数量和完整指标。缺失/坏JSON、未匹配的目录或混入旧文件时停止性能通过结论。
6. 保持同一版本、负载和验收口径复跑，并按[回归二分合同](../../guides/bringup/vllm_ascend_regression_bisect_contract.md)重新确认端点和嫌疑范围。

## 后处理与上报不能替代判据

result_postprocess另外生成`/root/.cache/upload_perf/results`下的嵌套testcase_info/testIndicator并调用上报模块；它不是二分消费者读取的顶层pass_fail JSON。预设/脚本不存在、部分读写失败或上传脚本非零返回会warning，不提供“已上传”或“benchmark达标”的证据；部分schema/枚举构造异常仍可能传播，不能把文档的宽泛never-fail描述当所有异常都被吞。

后处理填入nightly/weekly、branch、case key、数据与指标等字段，不在本次执行，也未对外上报。不能用上传成功替换原始结果完整性，或把上传warning当成NPU数值失败。

## 验收与停止

功能请求、任务精度、性能基线、采集完整性、工具可判定性和外部上报分别报告。只有真实结果完整、逐项比较确已执行、没有未解释功能失败且满足约定条件，才声明目标通过。二分工具的PASS/FAIL/SKIP及first_bad字段按其有限合同解释，不能合成为模型已经适配或性能已优化的结论。

本次只读定义与静态控制流，未执行上游测试、AISBench、二分、编译、服务请求、NPU精度/性能或上传。本批已补充AISBench结果生产与投机指标定义；目标DP运行时、外部工具实现及完整请求/缓存生命周期仍有待补。


## AISBench 实际生产与第一层验证

补充完整阅读 tools/aisbench.py：入口 `_init_request_conf` 生成请求配置，`_wait_for_task` 轮询完成日志，`_performance_verify` 读取并验证性能结果。AisbenchRunner 初始化就准备数据、改配置、启动和等待工具；默认 verify=True，成功后才返回 result。run_aisbench_cases 对每个非空 case 构造 Runner，失败则追加空字符串，继续其余 case，最后 assert 无错误。外层 JSON `_task_passed` 是另一层检查，不能只读它就推断工具没有任何 assert，也不能把两层门槛当作完全同一协议。初始化若抛错，with 尚未进入，不能把 __exit__ 当成总能执行的进程清理。

| 工具内路径 | 接受条件/结果口径 | 与外层 JSON 的差别 |
| --- | --- | --- |
| accuracy/range（默认） | baseline-threshold<=value<=baseline+threshold；baseline 默认1、threshold 默认1 | 仍是绝对范围，默认门槛可能很宽；不是相对百分比 |
| accuracy/verify_mode=ge | value>=baseline | threshold 不参与，外层缺 threshold 可能直接标 pass，须读实际工具 assert |
| performance | 指定 threshold 才要求输出吞吐>=threshold*baseline；指定 input_throughput_threshold 则另验输入吞吐比例；指定 tpot_threshold 则验CSV TPOT Average<=绝对毫秒门槛 | 外层 `_task_passed` 的输出吞吐判断不覆盖输入吞吐或 TPOT；不设置这些门槛时不能称已经检查过 |
| spec_decode | 请求前抓 Prometheus 基线，结束后按 counters 增量计算每位置接受率，再 validate_acceptance_rates | 不是从accuracy CSV推导，必须核对指标端点、draft数和全位置 |
| verify=False | 跳过工具验证分支，性能/精度结果读取也位于验证方法内 | 不能只将它解释为“有完整结果但不assert”；实际调用是否取到 result 需要另查 |

accuracy CSV 通常取首行最后列；dataset_conf 包含 longbenchv2 时改取 accuracy 列均值。performance 从日志给出的目录读取按 dataset_conf 第一段命名的 CSV/JSON。示例名字、首行或均值不是自动穷尽数据集/子任务的证明，需保留原始表与数据版本。

请求配置通过正则替换生成 *_custom.py，不是受类型约束的配置对象合并；需检查生成文件是否真的替换到了目标行。performance 默认temperature=0且ignore_eos=True，accuracy/spec默认temperature=0.6；之后显式非None temperature还会覆盖默认。seed、top_k、top_p、min_p、penalty 等多项用 truthiness 分支，seed=0不会写入；thinking只在truthy时置True，no_pred可注释pred_postprocessor。不能由YAML字段存在就推断实际采样/后处理相同。多任务/多进程共享 *_custom.py 和 output_<case_type>.txt 还需隔离，不能把旧日志当本轮结果。

工具通过 shell 后台启动，等待每5秒读取日志末100行，先找 Current exp folder，再找特定结果短语；仅检测大写 ERROR，没有统一退出码/存活/超时截止判断。缺短语、错误行被滚出窗口或子进程退出可能持续等待；不能把“没看到ERROR”当完成。__exit__只对保存的shell进程terminate/wait8秒/kill，不能据此证明后台工具进程树已全部释放。这里是静态边界，本次未启动或终止任何服务。

选中performance的profiling收尾会先 finish 并打包 trace；采集失败可能使本来完成的 benchmark 抛错。异常清理时记录二次profiling错误并重抛原异常，正常路径则传播采集错误。因此“benchmark失败”还要区分指标未达标、功能错误与采集/归档失败，保留双方证据；参见[定时剖析及产物完整性](../../guides/optimization/vllm_ascend_aisbench_profile_artifacts.md)。

## 投机接受率计数的分母与局限

tools/spec_decode_metrics.py 从 /metrics 拉取并解析 vllm:spec_decode_num_drafts 和 vllm:spec_decode_num_accepted_tokens_per_pos，对所有匹配 sample 求和，并按 position 限定配置的位置数。未按model/实例标签进一步过滤；共享端点其他业务流量会进入计数。请求前后差分时不能跨进程重启/counter reset或混入其他run，聚合值也不是逐请求配对证据。

每个位置接受率=该位置accepted增量/总draft增量；draft增量<=0时全部置0，而不是标未定义。因此缺指标与真的零接受率可能混同，先检查原始counter、有效draft数和端点覆盖；多个DP实例是否都进入该端点也另验。返回的pos0_rate只是第一位置，不是全位置均值或整体加速比。

validate_acceptance_rates 要求非空基线，实际列表长度至少为基线长度，逐位actual>=baseline*(1-tolerance)，没有上界；多余actual不参与。另一个 validate_acceptance_rate 对单个pos0使用对称±tolerance，两者不是可互换判据。外层JSON要求相同长度，更严格的形状条件也不能据单函数名统一。指标辅助函数未执行NPU或业务质量测试，高接受率仍需功能、精度与端到端性能证据。

## 多节点JSON生产与报告范围

补读common/multi_node/benchmark_results.py、internal_dp/test_multi_node.py及external_dp的utils/test/runtime/config：内部只有node0保存，外部master执行benchmark后保存。两条路径tasks都zip配置与results，无长度相等断言；这里的公共task_passed没有单机的spec_decode list专用分支，不能把上表逐位置协议套到这份生产器。

公共多机task_passed先把空字符串记False；baseline或threshold缺失直接True。accuracy数值按abs(actual-baseline)<=threshold，performance长度2的list按Output Token Throughput.total去token/s后与threshold×baseline比较；解析失败False。其他类型/形状最终True，包含没有专用处理的spec_decode形状。读取到task pass不证明该形状真的被验证，也不能掩盖tools/aisbench.py在返回结果前的独立assert。

多机write_results_json只写model_name、hardware、dtype、feature、versions、tasks、serve_cmd和environment，**没有顶层pass_fail**。而既有二分verdict消费者只查看顶层小写fail；若pytest退出0，nested task fail不在其现有检查范围。这里明确区分“可能漏检的静态生产/消费组合”与真实事故，本次没有运行二分或NPU；需要benchmark通过证据时逐项核对完整tasks及期望数量，并按原工具合同保留实际rc/原始结果。

内部serve_cmd来自配置节点字符串与PD角色，feature只看首节点和当前env；外部serve_cmd按角色/node/localrank展开，environment仅保留所有命令都有且相等的键。实际外部server manager另合入derived network/KV pool覆盖，报告侧build_all_server_commands不带这些最终覆盖，因此JSON不是完整执行环境证明。hardware来自runner名中a3/a2，dtype按w8a8模型名及ascend量化字符串否则bf16；这些都是启发式标签，不是设备探测、全模型dtype或功能激活证明。

环境过滤只排固定基础设施/端口键，不是完整敏感信息清洗；format_server_cmd按SENSITIVE_ENV_TOKENS对TOKEN/SECRET/PASSWORD/ACCESS_KEY键遮盖，也不覆盖全部继承环境。vllm_ascend_version写入VLLM_ASCEND_REF标签，不是自动读取真实源码SHA。外部rank日志追加写入，首行可能属于旧实验；不要把报告字段或某条命令文本当作不可变run身份。按run隔离日志，另保留配置/源码/镜像与实际安装SHA、全部rank映射及必要环境证据。

JSON写到/root/.cache/benchmark_results/<job>/<job>.json，BENCHMARK_JOB_NAME固定job名可被后续运行覆盖；内部job为空时路径/文件名还可能不带可识别任务名，外部有test_name回退。postprocess在写JSON之后调用，故已有文件不证明后处理、benchmark、服务清理或整个pytest成功。工作流的成功good_table、JSON存在、归档上传与任务达标分别报告；具体部署、节点日志和AOP返回边界见[多节点测试合同](../../guides/bringup/vllm_ascend_multi_node_test_contract.md)。

本节仍为固定提交的源码静态结论，保留原主来源、生命周期和空平台范围；未运行上游测试、服务、二分、上传或NPU/Agent A/B。
