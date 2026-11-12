---
type: Optimization
title: MiniMax-M2.5在8张910B4的上游有限性能与质量观测
description: 保存A2 W8A8无草稿低并发的版本、KV容量修正、合成性能负载与固定50题GSM8K结果，限定重复和证据缺口。
tags:
- task.optimization
- task.testing
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/MiniMax/MiniMax-M2.5.mdx
  role: primary
created_at: '2026-11-08T12:38:11Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a2
---

# MiniMax-M2.5在8张910B4的上游有限性能与质量观测

## 上游记录与环境

本卡蒸馏上游Cookbook所报告的2026年9月22–24日观测，本次未运行模型、下载产物或重新核验结果，不填写verified。硬件8×Ascend910B4、每设备32GiB，TP8/ModelSlim W8A8/BF16，无草稿；权重Eco-Tech/MiniMax-M2.5-w8a8-QuaRot约230.82GB。A3参考是另一配置，见[部署指南](../../../guides/models/sglang_ascend/sglang_ascend_doc_minimax_m2_5.md)。

记录SGLang0.5.14.dev172+gf308abc05（运行commit f308abc05212c2f5f455de22a525e14afa63ee4f）、Python3.11.15、Torch2.10.0+cpu、TorchNPU2.10.0、Transformers5.8.1、sgl-kernel-npu2026.5.1；后续检查CANN9.0.0/driver25.5.2。环境有修改的pyproject.toml及删除的pyproject_npu.toml，非干净源码构建验证；镜像digest、不可变模型revision未保存，网络/CPU拓扑细节及完整环境锁定未知。

## 容量修正与单请求探测

共同设置HCCL_BUFFSIZE128、OMP_NUM_THREADS1、expandable_segments、TP8、context4096、max-running1、chunk128/max-prefill4096、禁graph/Radix。早期static0.95且无max-total，启动只有896 KV tokens，1024/2048输入被拒、最大输入890；这是早期基线，不能当最终模型能力。

最终static0.96/max-total4096后，八rank均报告4096 KV tokens。两次warmup后6条chat检查（首都、加法、JSON乘法、中文首都、复制单词、排序）全部正确、temperature0/max512/finish stop；completion53–185 tokens、E2E12.598–43.747秒、首次可见输出0.456–0.477秒。推理及special tokens计入completion。minimax parser分离reasoning，tool parser虽配置但未测工具调用。

另有6条重复合成文本的native generate，准确token IDs、ignore_eos、输出恰128；每行只测一次，C1、未flush：

| input tokens | E2E秒 | 首次可见输出秒 |
|---:|---:|---:|
| 64 | 29.970 | 0.494 |
| 128 | 29.313 | 0.478 |
| 256 | 30.193 | 0.700 |
| 1024 | 32.165 | 2.103 |
| 2048 | 34.451 | 4.218 |
| 3500 | 39.803 | 10.055 |

这些是HTTP/SSE到DONE的端到端时间，首输出可为content、reasoning或positive output-token count，受parser buffering和多token chunk影响，不是kernel延迟、final-answer TTFT或时延分位。每轮后health200，不证明持续稳定或完整4096边界。

## 分开的合成吞吐实验

吞吐服务改static0.97/max-total16384/context8192/max-running8，其它设置相同，selector仍保留上节单请求配置。数据是16条本地自编英语合成prompt（ShareGPT格式，**不是ShareGPT数据集**），random/range1/tokenize-prompt得到精确128或1024输入，输出恰128；rate∞、temp0、每run warmup1、flush-cache。共10 runs/76有效请求，全部成功；serial seed17，重复组seeds17/29/43各一次。

下表括号为三次run-level均值或速率的min–max，非请求极值或合并分位；C1只有一次。

| 输入/输出、C、每run N | output tok/s | TTFT ms | TPOT ms | E2E ms |
|---|---:|---:|---:|---:|
| 128/128,C1,N4 | 4.266 | 486.589 | 232.385 | 29999.459 |
| 128/128,C4,N8，3次 | 16.731（16.618–16.810） | 807.497（801.011–814.685） | 234.492（233.452–236.043） | 30588.025（30449.379–30792.190） |
| 128/128,C8,N8，3次 | 32.457（32.373–32.532） | 1312.882（1276.591–1359.876） | 237.912（237.480–238.622） | 31527.731（31456.127–31607.222） |
| 1024/128,C8,N8，3次 | 13.694（13.291–13.942） | 12582.293（12329.436–13062.333） | 272.578（268.251–280.396） | 47199.685（46422.970–48672.617） |

每run保存command/log/JSONL，要求completed=N、所有input/output长度与计划一致、errors项齐全且全空；失败和缺失run也应保留。100%请求成功率不是准确率，输出吞吐是总完成token/总时间，不是单请求decode速度。

随后context改9216，3500/1500、客户端C2/N2、seeds1/17/29，服务max-running仍8，每run一次32-output-token warmup。6/6有效请求、总input21000/output9000、无错误。三run平均output8.004（7.896–8.065）tok/s、total26.680（26.319–26.882）tok/s、TTFT10317.118（10267.749–10365.114）ms、TPOT243.163（241.222–246.570）ms、E2E374.818（371.957–379.927）秒。只匹配A3参考token长度，不匹配其硬件、ShareGPT负载、并发320或EAGLE3，不能比较A2/A3优劣或验证50ms目标。

## 固定50题部署回归

同A2环境，context9216、服务max-running2/static0.97/max-total16384，客户端串行chat、temperature1/max6144、seed=42+原test row index，minimax parser且只评分final content。上游报告49/50=98%，错1、capped0、transport/protocol错误0、completion292–2507；50条均预检通过，含预检总耗时9444.598秒，不是单请求延迟。它是固定子集，不是完整GSM8K、EvalScope或GPQA。

协议在独立3题pilot前冻结：官方GSM8K数据revision3101c7d5072418e28b9008a6636bde82a006892c，train0–4作5shot完整解答，test1319索引用Random(20260924).shuffle，前三留pilot，随后50按原顺序且不更换。单user消息按Question/Answer模板拼接；先tokenize确认prompt+6144≤9216，每题只发一次、墙钟1800秒、传输错误后停且不重试。评分去逗号，用`-?\d+\.?\d*`取最后数字与gold比，缺数/错答/截断/协议错误计0、分母固定50；不完整必须报告不完整。

来源称下载的172条manifest hash通过且重评分仍49/50，本次未取得或复核这些产物。复现需保留固定ID、prompt hash、采样、所有响应/raw SSE及失败；这些有限观测不证明长上下文质量、长期稳定或A3参考通过。

## Evidence

- [docs/cookbook/autoregressive/MiniMax/MiniMax-M2.5.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/MiniMax/MiniMax-M2.5.mdx)（primary）
