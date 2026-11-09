---
type: Guide
title: vLLM Ascend TurboQuant执行：紧凑行、共享页与Attention读写
description: 串接TurboQuantLatent、turboquant_finalize、write_dsa_cache与MixedQuantSparseFlashMla，区分DSV4 C4的258字节行和SFA的386字节槽，核对旋转basis、共同backing、PAD写入、压缩长度及外部算子边界。
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/turboquant_finalize.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/mixed_quant_sparse_flash_mla.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/sparse_flash_mla.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/kv_cache/turboquant/test_operators.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_turboquant_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_turboquant_finalize.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/turboquant_finalize.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_attn_kv_plan.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/sfa_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/attn_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_kv_cache_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/turboquant/latent.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/turboquant/cache.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/turboquant/config.py
  role: constraint
created_at: '2026-11-03T01:17:16Z'
updated_at: '2026-11-03T01:17:16Z'
platforms: []
aliases:
- turboquant_finalize
- _finalize
- write_dsa_cache
- mixed_quant_sparse_flash_mla_turboquant
- mixed_quant_sparse_flash_mla_metadata_turboquant
- turboquant_kv_rmsnorm_rope
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend TurboQuant执行：紧凑行、共享页与Attention读写

## 任务与固定范围

新模型接入TurboQuant，或出现压缩行正确但Attention错误、page覆盖和graph重放旧值时，需要同时追踪量化后处理、分页写入、allocator和读取端basis。本卡固定Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`；全文阅读finalize kernel/文档、MixedQuant adapter及所列直接测试，DSA/SFA、slot writer、planner hooks和MRv2 allocator按简来源表中的范围读取。SFA/FP8其他分支与外部CANN kernel不因此全部闭合。

来源和测试仅作数据，未导入、执行UT/e2e、JIT或NPU。上游finalize文档报告过A3验证，这只是该文档的证据归属，不是本次硬件复验；保持draft/空平台。配置门禁、尺度编码和Hadamard版本见[KV格式合同](vllm_ascend_kv_quant_format_contract.md)，DSV4的普通BF16/FP8计划仍见[既有计划](vllm_ascend_dsv4_kv_plan_contract.md)。

## 先区分两套缓存与basis

| 路径 | 存储与读取 |
|---|---|
| DSV4 C4 | 512维latent的256字节code加2字节FP16 scale，共258字节；同一C4执行中的原SWA KV保持BF16，但也转到对应旋转basis。C4 query旋转，Attention结果再逆变换。 |
| packed SFA | 256字节NoPE code、64个BF16 RoPE的128字节和2字节scale，共386字节；使用default SFA旋转，不沿用legacy DSV4随机序列。 |

DSA仅在TQ dtype且compress_ratio=4时构造legacy_hadamard对象并缓存固定plan；其他模式仍按原planner逐次选择。运行中改dtype、压缩比或basis不能只替换一个标志后继续使用旧plan/transform。forward会触发初始化，但调用者仍须让首次分配发生在capture之前，不能凭函数名推断冷启动捕获安全。

## finalize只做尺度校正与新行打包

外部ops-nn量化给出packed code和原向量norm；`turboquant_finalize`逐行计算`selected_norm=sqrt(sum(norm_lut[packed_byte]))`，再把`fp16(original_norm/selected_norm)`位模式的低、高字节依次写到256/257位置，前256个code字节原样复制。LUT必须使用同一centroid与高低nibble顺序。它不做旋转、不训练codebook、不计算Attention，也不直接写分页cache。

输出是新分配的`[R,1,258]` uint8。R0不launch；其余最多min(R,vectorcore数)个program以grid-stride循环处理行。rows排除值特化，改变eager行数可复用编译变体，但capture仍固定地址、shape与launch参数，不产生动态shape graph保证。

wrapper没有通用输入schema检查：依赖同设备、contiguous packed `[R,256]`、contiguous norm和256项FP32 LUT。Device按固定行宽寻址，不消费任意输入stride。没有epsilon、饱和或NaN/Inf修复；有限非负norm、正有限LUT行和及可表示的FP16商是有效数值前提。零norm产生零scale。文档关于一kernel减少中间张量是结构性说明，不是本次测得加速。

## DSV4写入：C4压缩、SWA旋转和PAD

`AscendDSAImpl._write_kv_cache`在quantize=True时要求uint8 C4 cache，压缩后将cache/updates同itemsize reinterpret为INT8交`write_dsa_cache`，不把code数值重新量化成INT8。quantize=False保留BF16 SWA dtype，只旋转而不压缩。None/零行直接返回；非TQ分支维持原scatter调用，不把新的dtype要求套给全部缓存。

Host writer要求四维`[pages,page_size,1,width]`、连续末维，updates为二维或中间维1的三维张量，宽度/dtype一致；slots为flat或`[T,2]`，INT32/INT64、行数一致且三者同device。kernel消费真实page/row/update/index stride，地址坐标升INT64；负slot、越界block或offset跳过，只有width以内的列被写入。PAD不会clamp到活跃0槽。

这里的bounds检查不解决重复有效slot的并发覆盖，也不是对任意alias storage的验证。tokens/width不按值特化只控制编译变体，不能删除shape和生命周期约束；全PAD仍是固定shape提交，与Python按valid数量生成动态索引不同。

MRv2先为各group按实际storage block size生成block/offset对，保留负slot的[-1,-1]。若无DSA metadata builder的packed SFA路径，不消费这份DSA格式化slot；不能凭同一TQ dtype把两套slot接口互换。

## allocator：先核descriptor，再分配一次

TQ planner的共同stride与容量算术之外，MRv2实际DSV4分支要求所有descriptor的size一致。它先逐层检查stride至少容纳spec page、offset及最后一页payload不超过backing，且至少有可物化层，再只调用一次int8 raw分配，将各层保存为对应span的slice；后续descriptor循环遇到已建backing直接continue，避免按每条size重复分配。

非TQ DSV4在这条路径另要求逐层页连续，TQ才保留更大的physical stride。`_view_dsv4_cache`检查字节容量和所需extent，typed view把raw storage offset、dtype字节数与descriptor pitch共同换算成as_strided地址；不把逻辑numel或不同group的页大小直接当作共同跨度。一个全局block ID同一时刻只属于一个group仍是scheduler前提，allocator本身没有额外所有权锁。

planner patch同时接通grouping、cache_config、pool bytes、admission/max-memory与可选builder的aggregate-size hook；导入赋值存在不证明任意Native版本都匹配。0.32.0与main的不同签名有显式分支，不能用独立5df快照替代Main实际paired版本的运行验证。跨rank归一化必须沿同一pool divisor，否则re-plan可能改变实际block数。

`test_turboquant_v2`用真实生产allocator函数加CPU allocation替身定义了单backing、非零offset、padded stride、三个C4 view隔离和不支持几何在分配前拒绝。它没有执行NPU allocator，也不代表一切混合组、并发或动态重配都已安全。

## 读取端的mode、长度与sink

TQ plan选择MixedQuantSparseFlashMla adapter，强制quant_mode=3、rope_head_dim64、cmp_ratio4和PA_BBND；它不同于同文件FP8的mode1，不能因接口同名套用FP8 608字节页。paged接口去掉KV侧cu_seqlens，将普通KV长度映射为original-KV长度。

metadata adapter显式生成compressed长度的floor除法与余数，及对应max长度；attention adapter则让融合算子推导，不能把两个kwargs字典机械复制成一样。UT定义7/128/513个原token分别得到1/32/128个压缩项、余数3/0/1，纯属接口断言而非实测有效长度。

DSA caller传入SWA原页、C4压缩页、各自block table和稀疏indices，旋转query后调用选择出的op，再逆变换结果。sink必须由caller持有以覆盖graph寿命；helper只拒绝None，没有完整检查其shape/dtype和存储生命周期。临时补一个sink、从其他layer重用plan或仅看到metadata返回均不足以证明真实读取正确。

## SFA的386字节槽不可复用C4布局

SFA的NoPE经RMSNorm及TQ压缩，RoPE另做位置变换，再按scale预除RoPE并保留BF16；store按`[NoPE codes | RoPE bytes | scale bytes]`拼接并校验总宽386。query只旋转NoPE再接RoPE，输出逆变换。写入依赖DeviceOperator.scatter_cache；本卡闭合到该调用边界，不代替其全部设备实现与跨流依赖。

读取通过torch_npu的`npu_kv_quant_sparse_flash_attention`，不是仓库同名csrc绑定：K/V quant_mode均3、PA_BSND、attention_mode2、quant_scale_repo_mode1、tile_size128。它不是DSV4的PA_BBND MixedQuant入口。SFA路径另在prolog选择中拒绝TQ配MLAPO/PROLOG_V3；validator放过某项CP配置不代表全部前处理/通信分支均闭合。

## 取证与停止条件

记录checkpoint/basis版本、centroid/LUT、实际row宽、code与scale byte序、cache spec和所有descriptor、raw/view地址/offset/stride、group与slot、plan mode、长度张量、caller-owned sink及capture前后寿命。分别验证压缩后行、scatter未选页、allocator单backing和最后Attention数值，避免把某一环通过当成整链通过。

所读e2e定义包含所有packed byte、零/随机norm、graph中原位更新norm和不同R编译复用；CPU UT覆盖adapter参数及写入/allocator调用。均未执行。finalize和slot writer属于已读自有kernel；外部ops-nn量化、MixedQuant/SFA Attention kernel、所有SDK ABI及真实质量/性能仍待设备取证，失败时恢复整套格式与basis，不吞dtype/shape拒绝或伪造有效slot。
