---
type: Guide
title: vLLM Ascend MoE输入准备与复原：TP/DP/EP切分、scale与路由元数据
description: 核对All2All、MC2和AllGather的padding、token轴切分、量化scale前传与逆向reduce-scatter，并区分共享专家事件、logical到physical路由、负载计数和force-EPLB合成索引，避免新模型二次量化、错位复原或图引用失效。
aliases:
- PrepareAndFinalizeWithAll2All
- PrepareAndFinalizeWithMC2
- PrepareAndFinalizeWithAllGather
- MoEPrepareOutput
- MoeRouterInput
- RoutedMoEMilestones
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.mixture_of_experts
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/dataclass/prepare_finalize.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/dataclass/router_input.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/dataclass/shared_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/dataclass/token_dispatcher.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/force_eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/prepare_finalize.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/fused_moe/routed_experts.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/fused_moe/eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/fused_moe/prepare_finalize.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/fused_moe/token_dispatcher.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/register_custom_ops.py
  role: implementation
created_at: '2026-11-03T06:19:11Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MoE输入准备与复原：TP/DP/EP切分、scale与路由元数据

## 固定任务与数据流

固定Main ceac1a2，本卡完整静态阅读prepare_finalize569行、四份typed dataclass以及EPLB路由/force-EPLB两实现。另两份GateLinear/grouped router归[TopK主合同](vllm_ascend_moe_topk_host_dispatch.md)，导出包仅包装skip。这里只生产模型集成合同，未执行上游、collective、NPU、图或性能；外部maybe_all_gather/maybe_pad、LoRA helper、真实dispatcher与Device consumer仍需各自证据，保持draft/空平台。

MoEPrepareOutput同步携带hidden_states、router_logits、mc2_mask、padded_hidden_states_shape与可选pertoken_scale。下游MoeRouterInput明确把pertoken_scale传给dispatch，避免预量化activation重新量化；frozen dataclass只冻结字段重绑定，不冻结Tensor内容或自动校验shape/device。Router、dispatch、GMM和combine必须用同一活动token范围及量化代数，不能单独保留一份scale跨batch。

## 三种prepare/finalize路径

| 路径 | prepare的token组织 | finalize的实际动作 |
| --- | --- | --- |
| All2All，replace_allreduce=False | pad_size=TP-num_tokens，仅当正值时pad；TP>1按token轴tensor_split取本rank | TP组all_gather各slice到保存shape，再裁回num_tokens |
| MC2，普通路线 | 从context取mc2_mask/DP-wide padded_num_tokens，必要时pad激活/logits，再按TP切分 | 复用All2All gather与裁剪 |
| MC2，replace_allreduce=True | 输入已是本地TP shard；取mask对应本地段，再pad到padded_num_tokens//TP，mask补False | 只裁回本地原num_tokens，不另gather |
| AllGather，EP sequence parallel | 本地可先量化，hidden/logits/scale分别maybe_all_gather_and_maybe_unpad | maybe_pad_and_reduce |
| AllGather，DP/PCP路线 | 先按DP最大token补齐和all_gather，再按PCP最大token补齐和all_gather | 逆序PCP reduce_scatter/裁剪，再DP reduce_scatter/裁剪 |

普通All2All的代码不是“补到下一TP倍数”：num_tokens≥TP时不会补齐。因此大于TP且不整除时tensor_split可产生不等长slice，不能由注释或TP>1推断后续backend all_gather总能接受。保存padded_hidden_states_shape是复原容量证据，不能只按local shape重新猜总量。该prepare本身不做EP All2All交换，真正dispatch/combine属于其他层。

replace_allreduce=True的All2All跳过切分/聚合，MC2则仍有本地padding；两者不能共用“完全不处理输入”的解释。MC2要求context mask、target长度和本地TP行区间一致，负pad只表示此处不补，并没有自动truncate或证明容量合法。input_ids还有独立pad/split helper：MC2 SP输入长度不等本地num_tokens时先sequence_parallel_chunk，必须与hidden/logits来自相同token顺序。

这些覆盖没有按reduce_results参数再执行一套通用TP all_reduce；该参数存在不代表会额外归约。pipeline的其它归约若由外层完成，不能再在这里重复；反之也不应仅因传True就认为所需归约已生效。

## 预量化scale与通信必须对齐

EP-SP路线由moe_config.is_sequence_parallel选择，不是仅凭EP size。W8A8先npu_dynamic_quant；W8A8MXFP/W4A8MXFP先dynamic_mx_quant到FP8 E4M3，传dynamic scale算法；W4A4MXFP到packed FP4 E2M1并round。它们在all_gather之前执行，再分别gather/unpad activation与scale，router_logits沿同样token顺序通信。

非EP-SP的DP/PCP路线不执行这套预量化，返回pertoken_scale=None；不能把量化类型参数存在或MoEQuantParams字段非空解释成这里已量化。consumer需区分原浮点activation和已经量化的activation，精确保存per-token/per-group scale形状与dtype，不能再动态量化一次或用别的batch scale。

AllGather的DP/PCP finalize按逆通信顺序恢复；input_ids也需要相同DP、PCP padding与gather顺序。context max_tokens必须由全组一致的有效输入统计准备，本文件没有重新验证任意负值/不一致值、模型并发或持久字段self.num_tokens的重入安全。

## dispatch与shared-expert的元数据是协议

MC2 combine metadata保存topk IDs/weights、expert map、EP/TP recv counts、assist info、expand scales、quant与mask；AllGather保存weights、expanded row index和restore shape；All2All保存两个split数组、逆局部/全局置换以及两套hidden shape。build_token_dispatch_input只是将fused-experts字段原样打包，不替新backend计算这些逆映射。

MoETokenDispatchOutput同时给group_list与group_list_type，可有dynamic_scale/topk_scales。prefix累计与每专家count必须按type区分，不能由Tensor为一维就自行判定；真实GMM/负载计数consumer合同见[执行族](vllm_ascend_gmm_swiglu_execution_family.md)。

RoutedMoEMilestones按阶段描述shared_input_ready、router_output_ready、dispatch start、activation overlap start、combine start和finalize done。结构注释约定AllGather的distributed gather在prepare已发生，All2All的交换在dispatch/combine边界开始；不同backend可将activation overlap挂在GMM1或GMM2。这里只说明发布协议，不证明所有实际producer都已record这些event。

has_fine_grained_stage_events在三个内部event任一非None时就为真，部分发布不能被消费方当成无细粒度事件整体fallback；缺边界应继续检查producer。PreparedSharedExpertInput把is_gathered与ready_event独立保存：前者是布局，后者是调度，不以“等过event”推断已经全量gather，也不以layout正确推断跨流可读。

## EPLB logical→physical及统计接口

build_expert_replica_routing_table生成1024行周期表，第r行对逻辑专家e选择(r+ep_rank+e)%replica_count的物理副本，count先clamp_min1。校验map/count的维数与逻辑轴长度，但不证明count不超过map容量、每个物理ID有效或count0对应有效副本；这些仍是placement合同。

CPU map_to_physical按token行每1024重用表，空topk直接返回原输入，输出恢复索引dtype；NPU路径转独立Triton实现，本卡没有将CPU算法当作其Device全文。映射只选副本，不重新评分或改变权重，必须与同代实际weight/scale匹配。

record_expert_tokens要求1D及type0/1，核对本地物理区间。CPU type0将prefix作相邻差分，type1原样当counts，再乘record_enabled并累加对应load view；没有在此修复非单调prefix/负数或把任意record值转bool。NPU走另一个Triton函数，custom op声明仅expert_load_view为mutates_args，fake实现不更新数值。图Meta成功不能代替真实计数与映射代数新鲜度。

## force-EPLB是合成负载工具

force-EPLB按token数、k、逻辑专家数、EP size/rank、dtype和device缓存round-robin IDs，capture前为配置桶或max_tokens及I32/I64预建。helper自身不判断用户enable policy，get只在缺moe_comm_method时返回None；调用方要有明确门禁，否则可能替代真实路由。

round-robin以cursor=arange(T*k)+(T*k)*ep_rank+ep_rank，列为cursor%EP、行为floor(cursor/EP)%experts_per_rank，ID=row+col*experts_per_rank。要求T/k/EP为正、逻辑专家数整除EP；未完整验证EP rank和零专家域。它不是从模型logits得来的正确路由，也没有保证所有k组合无重复专家。性能可用它控制热点实验，模型正确性必须恢复真实topk及权重。

新backend接入先明确prepare输出的token范围、量化状态与scale，再交完整dispatch/combine逆映射，最后按对应finalize复原；保存每条collective组身份、大小/顺序、pad/mask、event与graph引用。只有真实输出、负载计数及多轮状态通过后再报告有效token时延或吞吐，本次没有执行这些验证。


## 3164 版本补充：有效 token 的 EPLB 负载与 CEIL 通信量化

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

MRv2负载记录移到AscendEplbLayerState.record_load，caller传operator expert_tokens/group_list_type以及topk IDs、prepare前source token数、SP标志与可选mask gather。仅hardware policy=CAPACITY_AND_WORLD_SIZE且当前ALLGATHER时提供mask gather；mask先转int32沿input-id同样pad/gather再转bool，防止图padding/无效source计入heat。routing table构造移到distributed/eplb.tensor_ops，不能继续从旧ops函数位置导入。完整record/generation语义依赖新版state实现，独立helper不保证迁移commit。

MC2在W8A8MXFP且CEIL算法时先显式dynamic_mx_quant，再用E8M0 scales和quant_mode0派发，避免融合量化器忽略scale_alg。combine缺省此类设quant_mode0，显式combine_quant_mode/通信模式仍有优先级；不能把默认0解释为所有配置都禁止通信量化。ALLGATHER同样在必要时显式CEIL量化，且router weight on input的topk1乘法先于量化，不能互换顺序。

EP gather/reduce的uniform SP分支跳过identity重建；DP1 FlashComm只裁实际尾或补SP尾再RS，DP>1/不均匀分片仍按各rank实际长度重建。优化保持rank顺序、补齐长度和输出归属，不是随意跳collective；输入local_sizes非空、容量与padded_length有效仍依赖caller。
