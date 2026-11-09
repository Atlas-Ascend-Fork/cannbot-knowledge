---
type: Guide
title: vLLM Ascend残差bank与KDA门控归约：架构迁移、累加及舍入边界
description: 分别核对AttnResFwd arch22驻留/重载残差bank与共享KDA gate cumsum的布局、chunk重置、两类gate、220/310快速路径、BF16物化和手动事件；不混同950
  Operator或两族数学语义。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/attn_res_fwd/op_kernel/arch22/attn_res_fwd_reload.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/attn_res_fwd/op_kernel/arch22/attn_res_fwd_resident.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/attn_res_fwd/op_kernel/arch22/reduce_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kda_gate_cumsum_vllm/op_kernel/kda_gate_cumsum_vllm_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/attn_res_fwd/op_kernel/attn_res_fwd_apt.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/attn_res_fwd/op_kernel/attn_res_fwd_tiling_data.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/attn_res_fwd/op_kernel/tiling_key_attn_res_fwd.h
  role: constraint
created_at: '2026-11-03T15:00:00Z'
updated_at: '2026-11-03T15:00:00Z'
platforms: []
aliases:
- AttnResFwdReload
- AttnResFwdResident
- KdaGateCumsumVllmKernel
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# 残差bank与KDA门控归约的迁移合同

## 适用任务和证据

固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。本卡完整分析AttnRes arch22三份程序和共享KDA gate header，另全文读取AttnRes入口/POD/key作为路由constraint；程序投影去除注释、保留宏与所有分支，Resident用已读Reload的完整差异复用。它帮助新模型适配与数值/性能Agent区分“减少搬运”和“改变计算顺序”，不声称完整Operator闭包或实机验证。

[950 AttnRes Operator](../../operators/aclnn/transformer/attention/vllm_ascend_attn_res_fwd_950.md)保持arch35、950/CANN与Host闭包；[KDA A2/A3 Operator](../../operators/aclnn/transformer/attention/vllm_ascend_kda_gate_cumsum.md)及[950卡](../../operators/aclnn/transformer/attention/vllm_ascend_kda_gate_cumsum_950.md)保持其公开入口边界。当前共享header与旧自包含CPP存在不同实现，不能把header新增softplus/布局/快速分支自动视为旧公开ABI已接通。未运行上游、编译、UT或NPU，平台保持空且status=draft。

## AttnRes：驻留和两遍重载

共享entry在__CCE_AICORE__==220选arch22，否则选arch35；它只实例化BF16、FUSED_PREFIX=true的Reload40010、Resident40020及带PREFILL_CACHE的40011/40021，AIV_ONLY且不消费用户GM workspace。未知key没有兜底body，不能自行拼POD。POD还含needBackward/invRms/probs相关能力，但当前entry将两个GM输出传nullptr，模板存在不等于公开反向已支持。

两种body按token分核并连续处理tokensPerCore，bank行由token*blockTokenStride+n*H寻址，逻辑最后一行是prefix。先可选prefix+addend升FP32相加再BF16 CAST_RINT；按写槽写回原始prefix并等待MTE3，再做混合。若写槽覆盖当前参与混合的bank，其后读取会看到被改行，caller必须维持既有Host的“写入未参与bank槽”合同。

scoreWeight在核内由projWeight*normWeight合成FP32，每bank行做平方和、乘invHiddenSize、加eps、sqrt、1/x，乘原行和scoreWeight再归约；meta softmax后按概率加权。mix=false或无bank的FUSED_PREFIX快路直接输出prefix，不能当一般空softmax。Resident把每行原始BF16常驻UB，score和weighted消费同一份；Reload用双深度输入队列，score一遍、weighted再读一遍并预取下一行。由此Resident减少GM重读但UB随blockCount*align16(H)*2增长，Reload也仍需三条FP32 H行、BF16输入/输出及B规模meta缓冲，不是无限容量fallback。

arch22 weighted helper实际用MulAddDst累加，不能把950旧卡关于逐步Mul/Add、不融合的数值结论复制过来。FP32结果先CAST_RINT成BF16；可选saveMaterialized将这份BF16写GM并以MTE3_V等完，再把同一outLocal升FP32做输出RMSNorm、乘gamma、重新BF16舍入。不能在FP32混合结果上直接做输出Norm而跳过物化舍入；materialized与最终output也不能任意互换别名。

## AttnRes：归约、尾部与缓存身份

arch22的H归约以64个FP32/向量为基本单元：非幂二先把尾部折入body，再二分到64，用WholeReduce；helper会原地改scratch并恢复mask。softmax B<=64走直接WholeReduce，B>64使用half-interval，padding max取-1e20、sum拷有效B后把尾部置零。B项概率再向8元素广播；Brcb repeat转uint8、部分repeat/stride域也有限，不能由动态H/B承诺无限范围。

InvRms使用乘invHiddenSize、sqrt和显式Div，不能与另一架构Rsqrt/Exp近似/归约结合顺序混作bitwise等价。部分尾折按8元素对齐读取，必须按实际Host准入与UB初始化证明有效尾部；不能仅因GM copy只搬H元素就断言所有padding都为零。

PREFILL_CACHE只在cacheOutputNorm置位时核内缓存一行BF16 gamma；它沿一个kernel实例跨token复用，不代表跨调用缓存权重。prefix/bank/输出原地别名、writeIdx及mask/event顺序均属于模型接线合同。分别保存Route、H/B、资源预算、eps、写槽和地址，对小B/大B、Resident/Reload、加法/禁混合/输出Norm及不同尾宽验参考，再量化GM读量收益。

## KDA：chunk局部前缀，不是残差softmax

共享header的输入寻址由rank3/4与inputSequenceMajor分支决定，输出固定head-major：[B,H,T,K]或[H,T,K]。定长task按batch/head/chunk分配；变长task按sequence/head分配，在原始cu[seq]:cu[seq+1]内按chunkSize步进。每个chunk先把acc清零，绝不跨chunk继承；不能在packed序列里按全局0、64边界代替每序列相对分块。

useGateInKernel=false时输入已经是gate；true时先取exp(A_log[h])、按需加FP32 bias。SAFE_GATE为lowerBound*sigmoid(exp(A_log)*(g+bias))；非SAFE分支为-exp(A_log)*softplus(g+bias)，用max(x,0)+log(1+exp(-abs(x)))组织。二者均逐row乘RCP_LN2=1/ln2后再FP32累加并输出，不是cumsum之后再sigmoid，也不是对累积结果clamp。hasALog字段虽保存，USE_GATE_IN_KERNEL实际直接读aLog，不把它当自动缺省安全证明。

普通行路径用两组输入/输出slot，预取下一行，只有对应V_MTE2/MTE3_V回收后才复用；尾部显式drain。K维缓冲固定256元素，bulk固定64x128，两份8192 FP32 chunk缓冲；需要上层Host的K、chunk、cu、地址和有限值门禁，header本身不统一重验。FP16/BF16升float，输出float；eps、gate上下界、NaN/Inf与INT64前缀不能从另一个算子借校验。

## KDA：架构快路影响误差和调度

| 分支 | 实际选择条件 | 累加/尾部 |
|---|---|---|
| 220 bulk | 输入FP32、内核safe gate、K128、chunk64且本段恰64行 | 先批量sigmoid和换底，再1/2/4/8/16/32距离树scan；短尾退逐row |
| 310 safe Regbase | FP32内核safe gate、K128、chunk64 | Regbase逐row累加，允许短尾，bias模板分别实例化 |
| 310预计算bulk | FP32、不在内核gate、K128、chunk64 | 两寄存器行序累加，可原位UB读写 |
| 310预计算行 | FP32、不在内核gate、K为128倍数 | 两寄存器pair的row累加；其余走通用Vector |
| 通用 | 其余模板/几何 | row→gate→换底→acc，双slot/drain |

220树scan与310/通用顺序加法不保证同一舍入；把chunk64改128也可能关闭快路，不能只按数学cumsum推导吞吐。inputSequenceMajor的bulk通过带stride copy转成连续head行，输出仍head-major。bulk写出后等MTE3_MTE2与MTE3_V，防下chunk复用UB；释放event前也保留行路径drain。

适配应记录真实entry命中的是旧CPP还是共享header、宏架构值、dtype/rank/layout、gate两开关、K/chunk/有效尾、cu边界及数值参考。确认接线后再分别比较220树scan和310顺序路径的误差与性能；当前源码分支不构成950/310P名称映射或所有模型支持证明。
