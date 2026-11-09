---
type: Guide
title: vLLM Ascend 细粒度 TP：DP 轴分片和四个组件的不同契约
description: 按中文四组件合同核对DP轴固定容量与Decode对齐、MoE和图上界/PreemptOffload条件，区分启动降级、构造/采样拒绝及A2来源的显存和TPOT结果。
tags:
- task.optimization
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/Fine_grained_TP.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/pipeline_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/Fine_grained_TP.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/multi_node_dp_deepseek.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/multi_node_dp_kimi.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/user_guide/configuration/additional_config.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/user_guide/feature_guide/Fine_grained_TP.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ascend_config.py
  role: constraint
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-11-03T01:56:47Z'
platforms:
- a2
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 细粒度 TP：DP 轴分片和四个组件的不同契约

## 机制和适用范围

finegrained_tp_config 沿 DP 轴的组切分组件权重，当前仅 MoE 模型；不是把标准 TP 全局尺寸简单改小。来源未施加硬件配置限制，性能数据仅来自 A2 的 DeepSeek-R1-W8A8 DP32+EP32，不能作为其他平台的收益。本卡提供标准 Worker 下的条件判断流程。

四个尺寸为 embedding_tensor_parallel_size、lmhead_tensor_parallel_size、oproj_tensor_parallel_size、mlp_tensor_parallel_size，默认0关闭；开启尺寸必须不大于 DP 且整除 DP。Dense 模型不能因某个字段名匹配就冒充有可用 MoE DP 组。

## 两类交换契约

embedding/LM-head 使用全组固定容量、padding 后通信并裁掉尾部，idle ranks 仍需参加；可用 eager/graph、Prefill/Decode。与标准 TP 同用时，它们采用 DP 轴细粒度计划替代该组件的标准 TP 分片，不是两次相乘分片。

O-proj/MLP 仅 PD D 端 graph-dispatched decode，要求标准 TP=1、PCP=1、recompute scheduler，以及 connector chain 含 PreemptOffloadConnector。MLP 实际 token 数需全组一致，O-proj 有静态容量；不能静默让大 batch eager fallback 进入不对齐跨 DP collectives。source 将 shared experts 保持复制，MLP knob 不等于切 routed experts。

## 图覆盖与冲突

最大 capture size 必须覆盖 `min(max_num_batched_tokens, max_num_seqs*(1+num_speculative_tokens))`，不足会在启动告警并关闭 O-proj/MLP 两个开关；运行落在图外则显式失败。启动成功不能替代 enabled-knob 日志检查。

专门Fine_grained_TP指南声明任意knob不能与PP>1组合，但同提交PP总览的MRv2表将LM-head TP列为支持。已读FinegrainedTPConfig._validate_preconditions本体没有PP检查；不能声称该方法必然拦截此组合，也不能据此证明运行正确。保留文档冲突，在目标模型/Runner的验证闭合前不生成PP+细粒度TP可用结论。PCP默认embedding/LM-head分片也有专门冲突。LM-head TP 不支持 DFlash2、probabilistic draft、local argmax reduction、adaptive verification；prompt_logprobs 请求也失败。

## 验证与回退

先检查最终 enabled 列表、权重 shard、组成员与每步 collective shape，再比较显存、精度、TPOT 与通信。来源四项合计每卡9.72GB是特定 A2 配置，O-proj 单项 TPOT 变差，不能把节省显存直接等同延时收益。逐个 knob 回退至0，保留可运行拓扑。本次未运行性能对照。


## 平台范围复核

主指南Hardware项没有配置层硬件限制，但仅明确给出A2 DeepSeek-R1-W8A8的整项部署测量；本卡收窄到该明确实例范围，不据此推导A3/950支持或不支持。


## 中文四组件合同与有效启用信号

Fine_grained_TP.po的87条有效译文有86条匹配当前英文，1处仅expert parallel改expert parallelism，dense MLP/routed expert/shared expert的切分语义未变。高匹配率不解决本卡已经保留的PP总览冲突，也不把“配置无硬件限制”提升为A3/950已验证。

embedding的固定容量为max(potential_max_tokens,max_num_batched_tokens)，token IDs经all_gather、词表局部lookup后reduce_scatter回owner。LM-head把采样hidden rows补到max_num_reqs*decode_query_len，再all_gather、vocab GEMM、all_to_all；idle DP rank通过dummy compute_logits以同容量参与。不能只按本rank活跃请求数选择是否参加或改变collective形状。

o_proj的静态potential_max_tokens容量和MLP实际step token数量不是同一合同；MLP要求组内真实token数量对齐。两者需要MoE、TP=1、PCP=1、PD consumer、recompute scheduler、PreemptOffloadConnector与允许的图调度，图外step显式失败。若capture上界不足，启动可成功但两个knob已被warning关闭；HTTP 200和choices字段只算服务烟测，不能证明目标knob真正启用、数值正确或性能改善。

LM-head的DFlash2/probabilistic draft/local argmax/adaptive verification组合在构造阶段拒绝，prompt_logprobs在采样阶段拒绝，不把两种失败阶段混作包安装错误。MoE配置字段与模型架构、真实DP group分别核对；mlp_tensor_parallel_size不切routed experts，也不让共享专家自动分片。

来源实验是32×Atlas A2、每卡64GB、DeepSeek-R1-W8A8、DP32+EP32、fine-grained size8、batch24：o_proj节省5.8GB但TPOT+1.5ms，LM-head节省1.51GB/TPOT-1.2ms，MLP节省.9GB/TPOT-1.0ms，embedding节省1.51GB/TPOT-1.0ms。9.72GB是来源合计；不能把分项时延机械相加当独立实测的联合收益，也不把单位GB改成GiB或百分比吞吐。

示例的DP4+TP4 embedding/LM-head配置、DP16+TP1四knob8的PD配置，与上述DP32实验是不同部署。启用后保存最终摘要、shard/组/每步形状、真实HBM与TPOT/输出，再按单变量归因；本次未运行服务、预占offload、图或性能实验。

## 普通DP/TP示意与细粒度组件组分开

保留的两张多节点示意分别标注DeepSeek DP4+TP4+EP16和Kimi DP4+TP8+EP32：四个enginecore分布于两节点，worker组宽分别为4和8；前端API/AsyncLLM的数量也可与enginecore数量不同。它们是用于解释前端、引擎和worker层次的固定示例，不是本次部署或模型/硬件验证。

这些普通DP/TP/EP标记不能替代finegrained_tp_config沿DP轴建立的组件组，也不能据图把EP再作为独立倍数乘设备数。保存实际group成员、每组件shard、节点设备和前端路由；图未给出四个细粒度knob的生效证明、性能或新的平台范围，本卡既有A2证据边界保持。


## 2026-11-03 main 增量：默认尺寸从 0 迁到 1

固定3164adc8fe75892fbf7f99f524bb72fddf1e6efd的FinegrainedTPConfig1290–1408行全文核对，并与原ceac1330–1444行对照；只是这两个class的完整范围，不是ascend_config.py整文件。新文档/配置四个尺寸默认1，表示不分片，只有>1才启用；0仍作为旧配置的禁用别名容忍，但不属于新文档推荐范围。不能因文档从值域移除0就声称解析必然拒绝它，也不能把原ceac默认0写成新版本行为。

变化同时影响有效配置判据：LM-head/embedding的enabled列表、MoE与DP可整除检查从>0变成>1；o_proj/MLP图capture上界不足时回退为1，原版本回退0。只看字段为正数不再表示该knob启用，默认1也不会要求dense模型建立MoE DP分片。<0仍被拒绝；>1的TP/图/PD consumer/PCP和容量前提继续逐项核对，不由默认迁移推新组合支持。

新配置生成与回退使用明确1，再按最终enabled摘要、权重切分和collective形状验收；旧0可解析不证明其周围旧版本配方整体兼容。本节没有构造配置类、运行上游或改变本卡原A2实测范围，前述旧参数/性能表保持其来源版本。
