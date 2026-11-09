---
type: Runbook
title: vLLM Ascend 首请求失败：假就绪与 Dynamo interpolate、contiguous 排查
description: 排查服务假就绪与首请求失败，按 Dynamo interpolate 与 contiguous 错误、processor skip_tensor_conversion、MLA
  和图捕获栈分层，验证同一文本或图文请求，区分 dummy 与真实权重证据。
tags:
- task.debugging
- task.testing
- topic.multimodal
- topic.compilation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/troubleshooting.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/workflow-checklist.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/multimodal-ep-aclgraph-lessons.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/fp8-on-npu-lessons.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/deliverables.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/SKILL.md
  role: supporting
created_at: '2026-10-29T16:27:59Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T16:41:18Z'
---



# vLLM Ascend 首请求失败：假就绪与 Dynamo interpolate、contiguous 排查


## 适用范围与失败判据

固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的模型适配经验，环境范围取配套 workflow 明确的 A2/A3；不是所有模型、CANN 或后续版本均有相同报错的声明。适用于启动完成、服务目录可访问，却在首个文本或图文请求暴露执行错误的场景。来源给出诊断模式，没有本次新模型实测记录；下面的开关是定位候选，不能直接写成已验证修复。

`Application startup complete` 只提供启动线索；`GET /v1/models` 返回 200 只证明服务目录路径可达。首个实际推理请求崩溃仍判为运行失败。文本成功也不证明 processor、视觉编码、媒体输入和混合 batch 均正确。

## 最小证据与真实就绪探针

| 探针 | 至少保存 | 能说明什么 | 不能说明什么 |
|---|---|---|---|
| 运行环境 | 两仓 commit、实际导入模块路径、镜像/依赖、模型/processor/checkpoint revision、SoC与卡数 | 当前测的是哪份实现与权重 | 编辑目录正确不等于运行 import 已命中 |
| 服务目录 | 实际 base URL、端口、served model name、状态码和响应 | API目录可访问 | Worker 首请求或模型数值已通过 |
| 固定文本请求 | endpoint、完整采样参数、请求ID、输入/输出、状态码、首个原始异常栈 | 文本数据路径是否真正执行 | 媒体、长上下文、EP或图重放均可用 |
| 固定图文请求 | 同上，加可复现媒体、尺寸、processor/tokenizer配置与实际可见路径 | 目标图文路径可执行 | 任意视频/音频或多轮状态正确 |
| 执行模式 | 实际Runner、eager/图配置、capture与replay日志或时间线 | 哪条执行路径被测 | 仅命令未写enforce-eager就等于图已重放 |
| 两阶段加载 | dummy/real各自启动和请求记录；real完整shard/层数与必需参数加载 | dummy做了哪些路径检查，real做了哪些权重检查 | dummy成功不能证明真实scale配对/分片和输出质量 |

先固定一个简短请求、`temperature=0` 和有界输出长度，匹配 `/v1/chat/completions` 或 `/v1/completions` 与模型模板。保留 HTTP 状态和输出内容；200加非空只完成 smoke，最终正确性仍需[精度验收](../../guides/bringup/vllm_ascend_accuracy_evaluation_contract.md)。不要把错误响应体、空 choices、仅含模板标记的输出记作模型验收成功。

## 按第一条错误分层

| 信号/阶段 | 初步定位 | 下一步对照 | 停止错误归因的条件 |
|---|---|---|---|
| 编辑后行为仍旧 | 安装或import来源不一致 | 在目标运行环境确认vllm/插件实际模块路径与版本；记录启动目录和入口 | 尚未证明加载到改动代码时，不继续猜kernel错误 |
| ready后 `AtbRingMLAGetWorkspaceSize`、`AtbRingMLA`，或伴随 `aclnnFusedInferAttentionScoreV3`/561002 | Attention/模型后端在实际请求才触发 | 同一最小文本请求仅切eager，区分图相关；继续追实际MLA/RoPE/backend和版本 | eager仍失败时，不把继续换图开关当成修好模型 |
| `TorchRuntimeError` 栈含 `interpolate`，并有 `NPU contiguous operator only supported contiguous memory format` | 视觉路径与Dynamo/连续格式交互 | 保持serve参数，仅以 `TORCHDYNAMO_DISABLE=1` 做受控诊断，重测文本和图文 | 回退通过只能报告该配置稳定性；不能声称代码根因已修复或原图模式已通过 |
| `convert_to_tensors()` 的 `skip_tensor_conversion` 非预期关键字 | remote processor 与当前依赖接口不匹配 | 对齐具体processor/模型dispatch和依赖版本；必要时限制媒体输入做层间隔离 | 文本隔离不是图文最终修复；没有媒体请求证据时不能标记VL通过 |
| 禁媒体后 `Cannot copy out of meta tensor; no data!` | 绕过第一层后暴露另一个模型加载路径 | 同时保留原processor错误与新meta tensor栈，回到目标模型加载/构造代码 | 不把次级错误替换成唯一根因，不认定text-only对所有VL模型安全 |
| `AclmdlRICaptureEnd`/507903、`rtStreamEndCapture`失效序列 | capture被失效，需定位捕获中的真实失败 | 来源建议AIV通信展开和较小shape作为候选；一次改变一个因素，记录eager对照 | 尚无完整capture/replay与请求成功证据时，不据进程存活判通过 |
| TP大于KV-head数时 `128 vs 64` 类norm shape失配 | KV复制/本地norm分片假设可能不一致 | 核对KV-head复制、Q/K norm真实维度和local shard loader；覆盖常规与边界拓扑 | 不能只裁剪张量、换较小TP后把原拓扑记为可用 |
| FP8-origin checkpoint在真实加载才失败 | weight/scale配对、模型remap或实际执行方法有差异 | 按[原生FP8规则](../../optimizations/rules/vllm_ascend_native_fp8_execution.md)核对层方法、dtype和scale；保存漏键 | 不将历史“FP8不支持”推广为当前950或任意格式的全局结论 |

本表是以栈和阶段组织的诊断入口，不是错误码到唯一根因的映射。共同出现的后续超时、通信失败和Worker退出要与首个异常分开记录；只换启动参数不能替代模型适配。

## 受控回退与复验

1. 在实际加载到目标代码、模型和设备后，以同一请求复现；区分启动、首请求、持续服务和退出阶段。
2. 仅切 `--enforce-eager` 做图相关性对照。eager仍失败，转模型/backend；成功则保存该模式结果，再定位图路径。
3. 只有命中上述Dynamo/视觉格式栈时才评估禁Dynamo的候选，不把它当所有NPU失败的默认修法。
4. 只有怀疑processor时才做文本隔离；记录禁用媒体的具体限制。它不产生完整多模态验收结论。
5. 修正后恢复所需功能，重测同一文本与媒体样本，再覆盖完整权重、完整层数、并行和目标工作负载。临时减层不移除ViT结构，最终仍需完整模型验收。

每次回退记录基线、唯一变化、请求结果、第一条异常及后续限制。图编译、capture和视觉profiling可能拉长启动；依据进度、明确错误和事先约定的超时判断，不能无限等候，也不能只因启动慢即宣称失败。

## 功能、容量与报告边界

报告分别给出ACLGraph、EP、FlashComm1、MTP和媒体能力的证据。EP不适用于无专家的模型；该来源的MoE验证清单不能替代其他版本的通用SP能力裁决。MTP既要核对config也要核对weight index中的实际参数；框架无能力、checkpoint缺参数、不适用和尚未验证必须分开。

同时给出config理论上下文上限与当前硬件、权重、TP/EP和模式下真实启动并服务过的实践上限。来源的128k+bs16是容量候选，32/64是后续并发候选，不是每个平台的硬性可达指标。减长度、减层、关图或关媒体后的通过都要写清范围。

本次仅蒸馏固定来源，未启动服务、下载checkpoint、执行请求、编译、NPU精度/性能或下游Agent A/B。来源旧配置及诊断开关与最新实现不一致时，以明确版本和实际调用链继续裁决，不能跳过现有guard。
