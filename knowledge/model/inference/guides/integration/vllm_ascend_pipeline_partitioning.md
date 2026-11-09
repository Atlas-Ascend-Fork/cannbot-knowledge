---
type: Guide
title: vLLM Ascend PP 接入：层分区、最后阶段负载与 PD 拓扑
description: 核对 PP 层分区、末阶段 drafter 和 MP/Ray/PD 拓扑，裁决 Sparse KV Offload 与细粒度 TP 冲突，分别保留模型、图和硬件的单项组合条件。 补充MRv1 PP在飞行门禁、IPC cached tokens、草稿输出校验与未实际启用helper边界。
tags:
- task.implementation
- topic.parallelism
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/pipeline_parallel.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/Fine_grained_TP.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/pipeline_parallel.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_pp_mtp.py
  role: implementation
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-11-03T05:17:15Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---


# vLLM Ascend PP 接入：层分区、最后阶段负载与 PD 拓扑

## 范围与最小入口

PP 将 target Transformer 隐层分成连续 stage，每 stage 由一个 TP 组执行，跨 stage 发送中间激活。先检查模型实现的 SupportsPP 以及 Ascend 支持表，而非见到 pipeline_parallel_size 参数就认为支持。单节点能容纳时先以 TP-only 作基线，多节点候选是节点内 TP、节点间 PP。

## 分区契约

每个 PP rank 只执行 `[start_layer,end_layer)`，非本 stage 层跳过，并提供中间 tensor 收发。先用自动分区；自定义 VLLM_PP_LAYER_PARTITION 每项为正整数、项数=PP、和=target 隐层数，所有 worker 一致。embedding、final norm、LM-head 和 draft 层不计入和。Ray 启动前在各节点设置，改变分区后重启。

最后 stage 还可能承担 norm、logits、采样及本地 drafter；同层数不等于同耗时。记录各 stage 峰值与时延，每次移动一层后重测。来源61层例子 PP2=[31,30]、PP4=[15,15,16,15] 描述本版本自动策略，不能凭惯例把余数全部加在末 stage。

## Draft、图和 PD

draft 在最后 stage 加载，不按 target PP 分区；draft_tensor_parallel_size 仅控制 draft TP。V2 上 MTP、限定模型的 Eagle3/DSpark 有支持，DFlash 不支持。DSpark 中间 tap 可跨 stage 转发，tap id 必须落在有效 target 层。

PD 在 P 端使用 PP、D 端保持 PP1。V1 connector 双端要声明相同真实 prefill.pp_size 与可选 pp_layer_partition，D 进程不要照抄 P 的环境分区。P TP 应不小于 D TP 且整除。PP+PCP/DCP 传输优先按 V2 组合条件检查。

## 失效条件与验收

Xlite 与 PP 不兼容；RoCE 跨机 MoE 当前不能同时 PP>1、DP>1。KVPP 限 eager/PIECEWISE 且有间歇输出不一致调查；单项组合支持表不能证明任意全开。细粒度 TP 需遵守[专门校验](../optimization/vllm_ascend_finegrained_tp_contracts.md)。

先核对节点数、唯一 rank、master 连通、模型/版本一致，再验证 stage 激活与输出，最后测 pipeline bubble、通信和吞吐。末 stage OOM 时结合 drafter 后调层，不能仅增 memory utilization。失败回到原分区/较小拓扑；本次未运行多机测试。


## PP 与细粒度 TP、Sparse KV Offload 的冲突

PP表将LM-head TP、Sparse KV Offload列为支持，但Fine_grained_TP指南排斥PP>1；SparseKVOffloadConfig在enabled时则显式拒绝PP>1，也拒绝950、CP及compress_ratios模型。不能把“layerwise connector”字样当作绕过该配置校验的证据。若声称属于不同P/D角色或其他offload实现，先补实际配置与调用链；本次尚未消除该冲突。

SupportsPP接口清单与模型维护/功能表也需并查：DeepSeek-V4.1-Flash出现在PP接口表，不覆盖其A2/A3模型行PP❌。Eagle3+PP只覆盖MiniMax-M3 sparse；DSpark+PP仅覆盖指南指定的DeepSeek-V4及GLM-5.2 MoE-DSA，不能从单个Eagle3/DSpark✅推出任意模型支持。


## 中文PP表的三处变化与接口证据

pipeline_parallel.po共138条，135条与当前英文原串匹配，3处需更新理解：当前已去掉“supported即代码启用且CI覆盖”的总括；ACL graph行补PIECEWISE，FULL_DECODE_ONLY的MTP验证措辞只针对该项；KVPP明确eager或PIECEWISE、禁止full graph，间歇output mismatch调查仍保留。译文未跟上不能据此关闭当前PIECEWISE，也不能凭某行Supported写本次verified。

SupportsPP标记只提供模型类/父类的分层与中间激活接口线索，仍要并查Ascend模型维护表。输入embedding、输出norm/LM-head/sampling、target隐层和last-stage drafter分别核算。61层自动[31,30]/[15,15,16,15]及自定[32,29]是来源整数例，不是其他版本/任意模型自动分区算法已验证。

## MP与Ray的启动和观测阶段

两节点MP例是TP8 PP2、nnodes2，同model/TP/PP/master端点，node-rank0和1唯一，worker加--headless；只有head运行API。MP没有Ray集群不是少一个模型rank，nnodes不是PP的别名。Ray则先在所有节点固定环境再起集群，只在一个节点提交模型服务；资源数满足只是启动前提，不能代替实际rank到stage/device映射。详见[Ray多机启动](../deployment/vllm_ascend_ray_multinode_bootstrap.md)。

PP rank是逻辑stage身份，node是物理服务器，一机可含多个stage；不能永远以“PP=节点数”推拓扑。模型放得下一机时保留TP-only基线；跨机通信局部性、activation bytes、pipeline bubble和last-stage额外负载共同决定收益。不同prompt长度与并发可改变瓶颈，移动一层后同时重测精度和每stage峰值/步时，不仅比较总吞吐。

## 单项组合不解除当前代码冲突

当前中文仍把Sparse KV Cache Offload+PP列支持；所读同提交SparseKVOffloadConfig在enabled且PP>1时拒绝，950/CP亦有guard，组合表不绕过它。可能属于不同P/D角色或实现分支的解释尚未以完整调用链闭合，维持前述冲突而不将两条合并成全支持。跨机RoCE的MoeDistributeDispatch路径不支持PP>1且DP>1，需保持至少一维为1；这是具体通信组合限制，不是PP rank必须等于物理节点。LM-head TP与Fine-grained TP、PCP+DCP的connector/V2、MTP/Eagle3/DSpark模型限制各自验收；本批未启动MP/Ray或真实PP模型。


## MRv1 PP IPC与草稿输出的补丁合同

按同提交 patch_pp_mtp.py346原始行的完整AST程序投影核对：运行补丁只用于PP且非纯PD prefill、非MRv2；MTP子条件还要求speculative_config。类定义或文档V2支持不能替代这条MRv1代码路径，也不改变前文模型组合限制。

补丁为缺spec_token_ids的ModelRunnerOutput兼容构造kwarg与EMPTY输出，为Scheduler保存/返回drafter token；还将调度后的非prefill请求next_decode_eligible_step置1<<60，收到对应output后恢复0，防PP在飞行时重复调度。cached request构建临时把async_scheduling设False并finally恢复，必要时为缺失new_token_ids补最后已知token；这是IPC状态传递，不等于服务整体改成同步。

update_from_output仅在MTP条件下浅复制含非正token数量的输出，过滤这些请求及spec映射，再委托原实现；成功后按req_id_to_index取spec IDs，并经structured_output_manager.validate_tokens写回request。没有sampled结果时清旧draft，不能让上一轮spec缓存跨请求复用。原调用抛错时后续eligible恢复未在finally，失败现场仍需显式观察。

本地draft验证对Eagle/MTP/指定DSpark架构浅复制parallel_config，仅把PP设1交原验证，因为draft在最后stage本地加载；target真实PP不能因此被抹掉。文件定义了EngineCore.post_step补丁helper，但_apply_patch实际未调用该helper，不以“存在函数”宣称已经替换post_step。_PATCHED在多个子补丁执行前置True，部分失败后的自动重试不由该flag保证。

回归检查PP每步唯一在飞行、busy/idle rank、async cached token传递、零token输出、structured draft及异常后状态，再核target/draft真实分区。源码核对未执行IPC、模型或图；原平台与支持声明保持。
