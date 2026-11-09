---
type: Guide
title: vLLM Ascend Triton草稿输入、拒绝验证与重采样合同
description: 区分逐token/整块/合成接受、n-gram回写、DFlash/DSpark DCP槽映射和MRv2 categorical resample的数据所有权与随机语义。
aliases:
- rejection_random_sample_kernel
- rejection_random_sample_block_verify_kernel
- triton_ngram_spec_decode
- copy_and_expand_dflash_and_dspark_inputs_kernel
- dflash2_greedy_selector_walk_kernel
tags:
- task.implementation
- topic.speculative_decoding
- topic.precision
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/reject_sample.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/spec_decode/ngram.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/spec_decode/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/v2/spec_decode/prepare_dflash_inputs.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/v2/spec_decode/resample.md
  role: supporting
created_at: '2026-11-03T06:00:17Z'
updated_at: '2026-11-03T06:00:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Triton草稿输入、拒绝验证与重采样合同

## 范围

固定 Main 中reject_sample、spec_decode/ngram与utils三个完整Python AST，及MRv2 prepare_dflash_inputs/resample两份完整文档。未运行采样、Triton/JIT或NPU；源码函数与文档中的MRv2独立入口有不同ABI，不能按同名阶段交换实现。

## 拒绝验证与回填所有权

普通greedy按draft是否等于target argmax逐步接受，首个不等写target并停止，全部接受后追加bonus；全batch spec_len=1且is_greedy=None时有专门kernel。输出未写的后缀必须预初始化，不能把整个empty输出矩阵都当有效token。

random路径以p_target/p_draft对uniform接受，draft为-1直接recover；NO_DRAFT_PROBS视作单点draft，概率读取有vocab_size/global_vocab_size两种跨度，必须与生产者实际布局一致。拒绝后只写对应recovered token，全部接受才bonus。sample_recovered_tokens以max(p-q,0)/随机指数变量择最大，one-hot模式去掉draft token；随机q按request×vocab共享，不用错位到各draft行。

ENTROPY_VERIFY以min(exp(-entropy*alpha),posterior_threshold)缩放接受阈值，改变标准接受规则；SYNTHETIC_MODE直接按提供的条件接受率，不看模型精度。二者不构成普通拒绝采样的无偏/模型质量证明。整块verify累积概率比和uniform乘积并寻找last_accepted_position，与逐步遇首拒绝即停的路径不同，必须按确切算法验证，不能只比总体接受率。

## n-gram与valid count

triton_ngram_spec_decode可将Python列表补-1，按device vectorcore上界分配请求。kernel跳discard请求，过滤sentinel-1和>=vocab ID，保存raw valid count，再按历史空间截断；实现没有完整负值检查，其他负ID不得传入。它按valid_count前缀写filtered结果，没有自动compact中间无效洞，因此输入应是有效前缀后跟padding。

先把本次有效sample写历史，再匹配[min_n,max_n]后缀，优先最长、同长度取最早历史位置，从匹配后续复制最多k个草稿；无匹配草稿=-1/count0。有空间截断时raw valid count、实际写入量和草稿长度不同，调度者不可互换。prepare_inputs_padded_kernel用draft+1-valid_count计算rejected、定位最后可sample行，无draft请求强制rejected0。

## DFlash、DSpark与DCP输入生产

copy_and_expand_dflash_and_dspark_inputs_kernel复制context位置/slot，再按每请求拒绝数量调整最后有效context与seq_len，anchor用bonus token，其余parallel_drafting_token_id。有效context为空时用本请求首pos-1，不读上一请求。query slot按interleave×DCP的虚拟轮次选owner，不属本rank则-1；block table仍需有效范围，helper未自动验证所有地址。

sample_from_anchor=True将query offset直接映射sample，False跳anchor并偏移一；num_query/spec token capacity必须与此模式闭合。DFlash2 greedy selector从prev_idx=0开始逐step走top_k×top_k转移得分，最大分并列选最小索引，不是每step无条件独立argmax。

MRv2文档另述v0.32 ABI的2D workers_per_req入口：Context宽256、Query/Sample宽16，三个域独立商余数分区，worker0写标量，全grid分担固定buffer padding。物理kv_cache_block_size负责DCP ownership，attention block_size负责block-table页，二者如384/128不能混用；文档wrapper显式透传cp_rank/cp_size/cp_interleave。它不等于上面legacy helper所有行为。

MRv2输入文档要求num_reqs>0、标量token position、无多模态/MRoPE、physical size可整除kernel page、request state映射合法与足够graph容量。query位置可clamp至max_model_len-1、null block/非owner给PAD_SLOT；clamp只定义该边界行为，不保证越长请求语义正确。来源独立Python参考要求metadata/所有padding bit-exact，不是本次通过。

## MRv2 categorical resample

文档resample在验证之后接sampled/num_sampled，entry step定位cu_num_logits[start]+step，最后logit行是bonus。随机full-draft使用(max(p-q,0))，one-hot去掉draft token，bonus按target softmax；greedy bonus写全局argmax，greedy非bonus保留验证kernel已写值，只推进num_sampled=step+1。

两级1024词表块质量，先并行统计再每request一次uniform阈值选block/token，不再生成全词表Gumbel。None draft与上层dummy pointer必须由has_draft_logits=False保留原语义；存在tensor不证明full-draft。pos收窄int32、词表末轴连续、state映射/shifted draft_sampled[row+1]有效由调用者保证。

部分-inf合法零质量；NaN、+Inf或全-inf没有新增强保证，FP32 p≈q可能丢小残差，没有FP64模式。新旧随机算法分布目标等价但不保持同seed token流；随机正确性用独立概率和统计，greedy/单点支持用精确值，性能单独msprof op，不以数值UT Python墙钟替代。

## Agent验收

固定实际Runner与入口、draft概率存在性、sentinel/有效前缀、query/candidate/bonus映射、request state和DCP块尺度；检查首拒绝/后拒绝/全接受、空draft、ragged、取消回退与padding。保存接受决策、恢复分布与所有输出写入范围，先验证正确性和真实有效长度，再比较接受率、extra compute、缓存及端到端TPOT。
