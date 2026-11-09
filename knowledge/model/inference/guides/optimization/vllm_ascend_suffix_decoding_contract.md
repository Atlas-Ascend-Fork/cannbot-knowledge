---
type: Guide
title: vLLM Ascend Suffix Decoding：A2四卡Qwen3-32B与SLO评测口径
description: 限定A2四卡Qwen3-32B的Suffix Decoding配方，核对Arctic依赖、名义K=3与CPU草稿接线，区分18行来源性能表的TPOT倒数增益、延迟下降和SLO条件。
tags:
- task.optimization
- topic.speculative_decoding
- topic.performance.analysis
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/suffix_speculative_decoding.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/suffix_speculative_decoding.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/suffix_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/spec_decode/suffix_decoding.py
  role: implementation
created_at: '2026-10-30T13:07:50Z'
platforms:
- a2
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T13:07:50Z'
---

# vLLM Ascend Suffix Decoding：A2四卡Qwen3-32B与SLO评测口径


## 范围、依赖与设备

suffix_speculative_decoding.md及suffix_speculative_decoding.po的37条译文全文对照，全部原串匹配。来源配方为一台Atlas 800T A2、设备0–3、Qwen3-32B、TP4/mp executor，不据此确认A3/950/310P或所有模型。Suffix利用prompt/生成内容的重复模式，所读提议路径使用CPU token缓存；目标模型和验证仍有NPU、内存与调度成本，不能把“无需额外draft模型”写成无额外资源成本。

教程要求安装arctic-inference但没有给精确版本，镜像宏也需解析成实际身份。先固定vLLM/Ascend/CANN/HDK及Arctic包来源/版本与模型revision，不能把pip安装成功或工厂能找到suffix当成ABI与模型质量已验收。原生CPU缓存/变长草稿及Ascend接线见[Suffix proposer契约](../../concepts/frameworks/vllm_ascend_suffix_proposer_contract.md)。本批未安装、导入或下载这些依赖。

## 启动片段是特定配方

来源method=suffix、num_speculative_tokens=3、served-name qwen3、API8011、max-model-len5500、max-num-batched-tokens40960、memory0.9，TASK_QUEUE_ENABLE=1、HCCL_OP_EXPANSION_MODE=AIV。max-model-len约束单请求总token，不将batch token预算40960当单请求长度。名义K=3不保证每请求每步产生3个草稿。

来源additional_config给pa_shape_list=[48,64,72,80]和weight_prefetch_config.enable=true。实际解析/生效与所选版本另核，不能据示例注释推导ACLGraph手工内存控制策略，或仅凭包安装推导这些组合已被当前配置接受。保存无Suffix基线的完整启动参数与有效配置，避免将其他图/预取变化归因给Suffix。

## AISBench请求与输出条件

示例VLLMCustomAPIChatStream使用qwen3、8011、request_rate=0、retry=2、batch_size=16、max_out_len=4000、temperature=0、ignore_eos=false，允许自然结束；服务trust_remote_code=true与bench配置false分别是各自入口，不能合并成全链路同一开关。

gsm8k示例命令只取100 prompts，原始表却按数据集列出不同并发，ShareGPT为327 requests、其他为100；复现保存实际数据、prompt/template/tokenizer、样本顺序、每场景并发和重试/失败统计，不能拿单个batch_size16命令覆盖所有表行。性能模式、greedy和相同seed也不替代目标输出、精度/采样与Agent任务质量检查。

## 六数据集的来源结果与适用边界

原始18行覆盖HumanEval、ARC、GSM8K、ShareGPT、SuperGLUE_BoolQ、AGIEval，每数据集三种并发。下表保留全部18个来源场景，TPOT为毫秒、TPS按原表标记保留；TPS输入/输出token与成功请求的具体统计分母仍需运行记录，均非本次测量。

| 数据集 | 并发 | 平均输入/输出 | 请求数 | 基线TPOT/TPS | Suffix TPOT/TPS | 接受率 | 来源TPOT Gain/TPS Gain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HumanEval | 1 | 150 / 2700 | 100 | 55.1 / 18.1 | 37.9 / 26.3 | 27.0% | 45.2% / 45.1% |
| HumanEval | 15 | 150 / 2700 | 100 | 61.6 / 233.8 | 45.8 / 318.2 | 27.0% | 34.6% / 36.1% |
| HumanEval | 26 | 150 / 2700 | 100 | 64.7 / 403.8 | 50.9 / 519.2 | 27.0% | 27.2% / 28.6% |
| ARC | 1 | 76 / 960 | 100 | 52.8 / 18.9 | 39.5 / 25.4 | 23.9% | 33.7% / 34.6% |
| ARC | 8 | 76 / 960 | 100 | 59.1 / 125.4 | 47.0 / 163.1 | 23.9% | 25.7% / 30.0% |
| ARC | 15 | 76 / 960 | 100 | 59.8 / 245.8 | 48.9 / 311.7 | 23.9% | 22.3% / 26.8% |
| GSM8K | 1 | 67 / 1570 | 100 | 55.5 / 18.0 | 35.7 / 28.5 | 31.1% | 55.6% / 58.4% |
| GSM8K | 17 | 67 / 1570 | 100 | 61.5 / 279.8 | 45.4 / 403.0 | 31.1% | 35.6% / 44.0% |
| GSM8K | 26 | 67 / 1570 | 100 | 63.9 / 396.4 | 50.0 / 527.6 | 31.1% | 27.8% / 33.1% |
| ShareGPT | 1 | 666 / 231 | 327 | 54.1 / 18.3 | 39.2 / 24.1 | 23.9% | 37.9% / 31.5% |
| ShareGPT | 8 | 666 / 231 | 327 | 58.8 / 125.0 | 46.2 / 153.2 | 23.9% | 27.1% / 22.5% |
| ShareGPT | 14 | 666 / 231 | 327 | 61.8 / 227.0 | 49.9 / 273.9 | 23.9% | 23.8% / 20.7% |
| SuperGLUE_BoolQ | 1 | 207 / 314 | 100 | 54.1 / 18.4 | 36.1 / 26.8 | 33.4% | 49.8% / 45.6% |
| SuperGLUE_BoolQ | 16 | 207 / 314 | 100 | 60.0 / 229.7 | 43.5 / 303.9 | 33.4% | 38.0% / 32.3% |
| SuperGLUE_BoolQ | 32 | 207 / 314 | 100 | 62.7 / 396.4 | 47.8 / 507.5 | 33.4% | 31.3% / 28.0% |
| AGIEval | 1 | 735 / 1880 | 100 | 53.1 / 18.7 | 31.8 / 34.1 | 50.3% | 66.8% / 81.9% |
| AGIEval | 24 | 735 / 1880 | 100 | 64.0 / 381.2 | 43.3 / 629.0 | 50.3% | 47.8% / 65.0% |
| AGIEval | 34 | 735 / 1880 | 100 | 70.0 / 494.6 | 50.2 / 768.4 | 50.3% | 39.4% / 55.3% |

各数据集另两种并发为HumanEval15/26、ARC8/15、GSM8K17/26、ShareGPT8/14、BoolQ16/32、AGIEval24/34。所报Suffix TPS随这些并发变化；例如AGIEval24/34为629.0/768.4，TPOT43.3/50.2，不能由更高总TPS推导同一SLO下更优。接受率在该表每数据集三行相同，定义/分母仍需对应工具与运行记录，不能直接当模型精度。

TPOT Gain列与(基线TPOT/Suffix TPOT−1)的倒数时延增益口径相符，不能标成“时延下降百分比”。例如55.1与37.9对应倒数增益约45%，按(基线−优化)/基线的下降约31.2%；原表舍入后的百分数与原始展示小数可有差异，不据此改写源结果。TPS Gain另按吞吐比理解，不能和单请求latency混算。

## 严格SLO与基线比较

教程概述SLO TPOT<50ms，但18行基线展示值全大于50；Suffix在HumanEval26为50.9、AGIEval34为50.2，也大于50，GSM8K26显示50.0且未舍入值未知。因此不能将整表描述成两侧都满足严格<50的比较，或把BS1–10的摘要外推到所有并发。SLO是均值还是尾分位也未在该表闭合，需按实际服务目标重测。

来源约20–80%吞吐提升是这套A2配方的概述，非所有重复任务或之后Agent的保证。按同数据/输出长度/有效配置、相同SLO和成功分母比较基线与Suffix，分别看CPU提议、target verify、接受长度、TTFT/TPOT、整体吞吐和host/HBM。重复少、CPU拥塞或验证成本增加可能改变净收益；关闭Suffix后用完整基线复核。本批仅做静态来源与数值口径核对，未运行AISBench、NPU或Agent A/B。
