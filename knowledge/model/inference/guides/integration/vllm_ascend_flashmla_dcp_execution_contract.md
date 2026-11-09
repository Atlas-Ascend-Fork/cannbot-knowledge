---
type: Guide
title: vLLM Ascend FlashMLA与DCP执行：页格式、逐步schedule和历史合并
description: 适配外部FlashMLA时核对576维query、128-token原始BBND页、MLA_FLASH和本地/DCP总head门禁；保持真实prefill排序、graph地址与device schedule刷新，区分分片history、复制current、跨流事件及FP32 LSE单次合并。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/flashmla.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/mla_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_flashmla_auto_select.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_flashmla_dcp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/mla_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/common_cp.py
  role: constraint
created_at: '2026-11-03T01:40:25Z'
updated_at: '2026-11-03T01:47:05Z'
platforms: []
aliases:
- FlashMLAImpl
- FlashMLAMetadataBuilder
- FlashMLAConfig
- prepare_flashmla_batch_req_state
- split_flashmla_requests
- AscendMlaDCPImpl
- MLASplitAttentionGraphParams
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend FlashMLA与DCP执行：页格式、逐步schedule和历史合并

## 任务与固定范围

新MLA模型选择外部FlashMLA、DCP出现数值偏差或graph重放旧长度时，先核对消费者的页与metadata合同。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2；FlashMLA475行、MLA_CP1203行及两份直接UT全文已读，父MLA、runner和通用CP helper只按简来源表的选段读取。没有导入或执行上游、UT、外部算子、JIT、通信或NPU；profile中的能力与测试定义不是本次硬件支持/性能结果，保持draft和空平台。

本卡维护未量化的FlashMLA读端及其DCP编排；[KV量化格式](vllm_ascend_kv_quant_format_contract.md)、[TurboQuant执行](vllm_ascend_turboquant_execution_contract.md)和[GLM DSpark模型适配](vllm_ascend_glm_mla_dspark_adapter.md)继续维护各自格式与模型协议。这里的Main父类选段不等于独立Native5df或Main实际paired544已做兼容性复验。

## 先选择，再分配匹配缓存

父实现仅在V2 runner、无投机或method为dspark、profile声明MLA_FLASH、单KV head、latent512/RoPE64、BF16/FP16、无FA量化、无KV NZ、无PCP且PD兼容检查成立、未启用SFA时考虑FlashMLA。支持的本地Q heads是8/12/64/96，且本地heads×DCP size也必须在同一集合。例：8×2不满足，8×8或12×8满足head检查；这仅是门禁算术，不保证其他条件或真实算子可用。同一attention group的层不能混选FIA与FlashMLA。

还需cann_ops_transformer.ops同时提供callable flash_mla和flash_mla_metadata。包或目标模块/API确实缺失可在缓存分配前回FIA选择；已安装包内部依赖损坏会保留异常，不能吞成“未安装”。发现检查有进程缓存，安装/切换包后不能假设原进程自动重新探测。实际worker device应先选定；Meta metadata查询也可能读取NPU core信息，不能把它当完全无设备依赖的shape推断。

选择之后不要以失败重试方式改contiguous缓存或偷偷换Attention：FIA component-major与FlashMLA原始fused BBND的ABI不同，重选需要重建整套cache/metadata/graph身份。

## 外部FFI的形状与未检查内容

| 对象 | Host合同 |
|---|---|
| query | 非空TND，最后两维[local heads,576]，BF16或FP16 |
| persistent KV | 原始Tensor，[pages,128,1,576]，与query同dtype；不是拆出的(NoPE,RoPE) tuple |
| 长度 | cache_seqlens为1..65535项INT32；cu_seqlens_q为B+1项，可选seqused_q为B项，同device |
| block table / schedule | table为[B,正容量] INT32；metadata为非空一维INT32，均同device |
| mask | mode0必须None；mode3要求2048×2048 INT8 mask，真实上三角语义由producer保证 |

metadata与attention使用同一config和同一组长度；max_seqlen_q/kv都传-1，不能用CPU估计上界替换。query为TND、KV为PA_BBND、输出为NTD；DCP开启return_softmax_lse后额外严格核对输出[heads,T,512]、LSE[heads,T] FP32。布局或精度不符会拒绝，不猜测安装包返回顺序。

这些检查没有读取tensor内容验证cu单调/末值、正长度与page容量、block ID有效性、scale/softmax有限性或mask内容，也没有证明任意stride被外部二进制支持。接受strided view只保留其身份；部署前单独验证内容与真实算子，decode hot path不为做检查同步拷回CPU。

## 真实阶段排序先于输入与graph派发

runner按is_prefilling稳定排序，real decode在前、prefill在后，同时重排req_id、scheduled tokens、index/prefill/computed-prefix及存在的draft/max-seq等数组。不能只重排token行而留下sampling或KV slot的旧请求映射。有任何prefill时清uniform_token_count并限制decode graph；原decode_graph_eligible=False也继续保留限制。

split只读runner提供的CPU阶段与query边界，裁到num_actual_tokens，忽略尾部零长度padding请求；活跃decode不能出现在真实prefill之后。缺失阶段行只容许对应空行。一token prompt suffix仍属于FIA prefill，不凭query长度1走FlashMLA。mixed eager还保留FIA所需精确CPU prefill长度及原prefill slot切片；FULL捕获必须decode-only。

## 每步刷新数据，按捕获容量保留地址

buffer key为(tokens,rows,block-table columns,causal)。decode-only按实际/输入padding容量和max requests分配，另加一个zero-used请求接管padding；mixed eager只分配当前decode子批，不将所有prefill形状长期缓存。只有显式retain_for_graph才新增长期缓存，之后同key可复用；不能把每个eager长度都留下，形成随shape数量增长的query HBM。

每次build在caller stream重新填cu/used_q、cache长度、block table、slot、position/RoPE及schedule。seq_len<=0使used_q为0，差分live boundaries生成token_live，死行slot置-1；padding输出不在有效Attention结果合同内。仅地址稳定不表示值新鲜：graph replay也必须消费相同device刷新计算，不能只改CPU镜像或复用旧schedule。

DCP rank预先物化为device INT32 scalar，refresh复用它，避免helper每步因Python int重建H2D张量。Meta阶段只确定schedule容量，再分配真实device schedule；外部package的容量规则、core数与worker device变更仍需重建/核对，不凭同shape跨device复用。

## DCP：历史分片与当前chunk只贡献一次

DCP history使用聚合后的heads、mode0及原始paged cache。普通decode或非因果draft直接读取完整本地序列，不额外复制current。配置了投机且causal时保留固定history/current结构，即使本批query只有1行也不按临时长度改变捕获结构。

causal split先在全局长度中减去各请求query，再按interleave分片history；不能对local长度再减全局query。current保留全部query行，在独立临时128-token页中按请求分配、使用本地heads与因果mask，持久历史写入仍按各rank拥有的slot。不能把已包括current的history再次与复制current相加，或将非因果DSpark误套causal split。

主stream先运行history Attention，再stage current KV/Q并record ready event。side stream等ready后算current；相关输入record_stream延长寿命，结果反向记录到main，main在最终合并前等current done。history输出与FP32 LSE交dcp_a2a_fused交换，defer combine后由fused_dcp_lse_combine把全部history分片和本rank current合并一次，再做V-up。这里闭合Host编排到自有/外部op调用，未把通信或LSE合并Device kernel本身算作全文/真机验收。

仅平均各rank输出、累加输出而不按LSE权重归一化、重复加入current或跨stream提早复用workspace都会改变结果。空history rank与全PAD仍需保留各自有效性语义，不能把无效LSE当普通零。

## 通用MLA_CP与FlashMLA的graph路径分开

普通FIA的history/current split用带attention_kind和layer_name的MLASplitAttentionGraphParams标记两个任务；更新时先按正确layer/draft step取metadata，history不提前推进layer计数。history用分片历史长度和block table，current用query长度且无paged table。target、draft decode和draft prefill使用各自registry；不能仅按相同num_tokens共享更新身份。

FIA分支在捕获前比较history/current所需workspace并保留较大的一份，current等待history相关工作后使用，地址在捕获后保持。DCP当前KV workspace按scheduler及投机上界分配；decode与prefill使用分开的backing，weight reload不替换被捕获地址。legacy MLAPO还受自己的token cap约束，不能把其容量当PROLOG_V3的通用容量。

external_flashmla层被排除在FIA graph task更新之外，因其schedule由device metadata刷新。不能因FIA更新函数没有该层就“补一个”错误task；反过来，忽略FlashMLA schedule刷新也会留下旧长度。父PROLOG writer对interleaved组件先用预分配dense workspace，再交由caller写入持久页；本卡只读workspace选择与读端调用段，未闭合全部writer、权重加载和外部PROLOG kernel。

## PCP+DCP prefill的另一组边界

MLA_CP另按LCM(block size,interleave×DCP)对齐chunk；默认workspace至少容纳每全局请求两个对齐local fragment。PCP与DCP组合时共享发送plan以全局请求长度/table为界，local attention仍消费各fragment自己的history，默认workspace再按两fragment预算折半；显式传入workspace不能自动继承所有默认安全推导。

collective实际按sorted global ranks返回，代码保存logical DCP rank到collective offset的映射。重组按全局PCP request→local fragment关系、rank offsets及各rank实际剩余chunk裁切，空集合返回空view，并核对累计token与max长度。不能按rank数组位置盲取，或把短replicated prefill强当固定2:1行数。这些规则属于MLA_CP的FIA prefill，不解除FlashMLA选择明确拒绝PCP的门禁。

底层payload的四lane编码、非有限贡献屏蔽及batched dispatch沿[已有DCP数值合同](vllm_ascend_dcp_lse_kernel_contract.md)维护；不要从通信shape推断全部FP32值域无损或将无效LSE当零。

## 接入与诊断产物

保存实际profile/包版本、local与DCP总heads、页dtype/shape/stride/storage offset、请求阶段与排序映射、token_live/slot、cu/used/cache lengths、captured key及地址、history/current分支、事件顺序和LSE layout/precision。先与未量化参考比较普通/投机/非因果、mixed、空rank、跨页、PAD与多次replay，再测query pack、metadata生成、临时current HBM、通信和V-up各自成本。

两份已读UT定义缺包与坏依赖区分、选路head门禁、真实阶段排序、device rank复用、相同地址刷新、strided history/未选backing保持、history/current事件顺序、FP32 LSE拒绝和CPU dense参考；均未运行，也没有真实ACL/NPU执行。缺接口、几何或数值不符时回到分配前选择匹配完整backend，不修改phase、mask或页格式掩盖错误。
