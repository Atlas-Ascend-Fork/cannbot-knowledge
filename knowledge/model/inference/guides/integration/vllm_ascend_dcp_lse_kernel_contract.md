---
type: Guide
title: vLLM Ascend DCP打包归并：LSE编码、无效贡献与分块调度
description: 接入DCP归并时核对低精度payload中的FP32 LSE编码、非有限贡献清理和local计数，按行数、stride与core数选择分块路径，并区分测试定义与设备结果。
aliases:
- DCP打包归并
- LSE编码
- _pack_dcp_output_lse_batched_kernel
- _fused_dcp_lse_combine_batched_kernel
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/dcp/dcp_a2a_batched.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/dcp/dcp_a2a.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_dcp_a2a.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_dcp_a2a.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_dcp_a2a_combine.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/triton_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/dcp_a2a_fused.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/fused_dcp_lse_combine.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/mla_cp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/pack_dcp_output_lse.md
  role: supporting
created_at: '2026-10-31T08:55:28Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T01:47:48Z'
---

# vLLM Ascend DCP打包归并：LSE编码、无效贡献与分块调度

## 消费任务与固定范围

模型开启DCP后出现低精度LSE失真、无效分片污染、batched路径未触发或stride相关差异时，先检查payload、有效贡献和实际dispatch，再分析设备性能。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取batched kernel231行、主打包归并622行、单卡定义539行、多卡定义153行、UT36行和Triton工具115行。主文件的前端选段来自同SHA前批阅读，本批补读20–245完成全文；不将新增阅读倒记成前批内核生产。

全部源码与测试仅作数据，未导入上游模块、运行UT/e2e、JIT、编译、NPU或HCCL。整项硬件支持未知，保持draft/空平台。这里是框架消费者的源码契约，不表示完整Operator producer、Triton编译器、Native/CANN ABI、物理设备或性能验证完成。

[GQA/CP执行协议](vllm_ascend_gqa_cp_history_current.md)说明history/current贡献、group、graph和跨流等待；本卡补足打包与归并实现。[旧decode空位置屏蔽](../../runbooks/precision/cp_dcp_online_softmax_merge_mask_out_not_only_lse.md)与[prefill空KV占位](../../runbooks/runtime/cp_prefill_empty_kv_shard_none_lse_merge.md)各有PR版本和故障信号；不能用那些修复直接证明当前融合路径。缓存stride与数据面问题另见[非连续KV缓存](vllm_ascend_non_contiguous_kv_cache.md)。

## payload坐标与stride

pack_dcp_output_lse接收output[T,H,D]及同设备FP32 LSE[T,H,1]。前端检查NPU、非空维、正整数且非bool的scatter world、scatter_dim为0/1及相应轴整除。payload为[destination rank, local scatter, replicated axis, D+LSE_PACK_DIM]；FP32激活的LSE_PACK_DIM=1，BF16/FP16为4。

kernel把token/head展平成row：token=row//num_heads，head=row%num_heads，并转int64索引。scatter token时rank=token//local_scatter、scatter=token%local_scatter、replicated=head；scatter head时改由head分rank、token作replicated轴。output的T/H/D stride及LSE的T/H stride都参与寻址，不能只拿连续Tensor结果验收带stride的FIA输出。

_pack_dcp_output_lse_kernel每次处理一行，按program数量跨步；_pack_dcp_output_lse_batched_kernel每次处理8行，按program数量乘8跨步。BLOCK_D取head_dim的下一二次幂，feature mask屏蔽D尾部；batched再用row_mask屏蔽不满8行的尾tile，避免读取或写入无效行。

## 四lane数值编码

FP32 payload直接存FP32 LSE；BF16/FP16 payload以四个数值lane保存signed exponent code和三个base-256 significand数字。它使用浮点log2/exp2算术，不是把LSE直接cast成激活dtype，也没有在这里使用raw bitcast。

finite_lse只接受有限值。令a=abs(LSE)，在LSE有限且不等于0时取e=floor(log2(a))并clamp到[-126,127]，significand=a*exp2(23-e)；零或非有限值的significand取0。高位significand_hi=floor(significand/65536)，再从余数提取significand_mid和significand_lo。exponent_code为带原符号的(e+128)，非有限值强制code=0。

| 输入/存储 | 编码与归并含义 | 接入边界 |
|---|---|---|
| 有限非零LSE | signed exponent code和三位significand | 保持四lane顺序及原payload dtype，不能只搬最后一个值 |
| 数值零 | code=128、三个数字为0 | 符号分支只看LSE<0，不由此证明负零bit身份保留 |
| NaN、+inf、-inf | code=0作为无效贡献 | +inf也被排除，不按普通softmax的支配项解释 |
| FP32 payload | 一个FP32 LSE lane | return_lse模式还要求FP32接收/输出契约 |

解码公式为sign*(hi*65536+mid*256+lo)*exp2(abs(code)-151)，要求code非0且解码值有限。源码意图利用小整数在BF16/FP16中的精确保存避免直接低精度LSE溢出；整数lane可保存，并不能单独证明整个浮点编码对所有有限FP32逐bit无损。极小值、subnormal、符号零以及log2/exp2中间量需独立验收，本卡没有复现或确认这些边界的NPU故障。

单卡定义中的70000+rank*0.25针对超出激活dtype范围的有限LSE；这是具体输入与断言，不是全部FP32值域、全部编译选项或所有设备的证明。

## 两遍rank归并与无效贡献

fallback _fused_dcp_lse_combine_kernel每行先扫描各rank的有限LSE求max，再扫描rank计算exp(LSE-safe_max)、FP32加权output与weight_sum。source只保留一个D向量accumulator和标量LSE状态；不能据此推断编译后全部寄存器/UB用量。

无效LSE对应的partial_output先用where置零，再乘权重。这个顺序防止0权重乘NaN垃圾值继续污染结果；有限LSE配NaN output仍可传播NaN，本逻辑没有清洗任意坏输入的承诺。local_output/local_lse用相同有限性条件，按调用协议只添加一次。

所有贡献无效时，safe_max取0、weight_sum为0、denominator改为1，源码将output写为0；fallback RETURN_LSE写-inf。存在有效贡献时，merged LSE为max+log(denominator)。分阶段合并history再加current时必须保存这份merged LSE，不能只把已平均的output再作无权平均。

_fused_dcp_lse_combine_batched_kernel同时处理8个独立row，并逐rank累加。FP32 accumulator形状为[8,BLOCK_D]，而不是[DCP_SIZE,8,BLOCK_D]；D=512时仅这个accumulator算术大小为16KiB。实际峰值还涉及LSE、临时变量、编译调度及设备，源码注释不能当作测得的总UB占用或提速。

batched归并由caller限定BF16 recv、head scatter、提供local贡献且不返回LSE。前端没有强制local dtype与recv相同，kernel会转FP32累加；A5现有定义主要用BF16 local，不能把A2/A3的FP32 recv/mixed local定义合并成全部A5覆盖。

## pack与combine分别选路

令V为初始化后get_vectorcore_num返回的vector core数。pack行数为T*H，head scatter后的combine行数为T*local_H，两个计数不能混用；各自grid取min(自己的行数,V)。

| batched分支 | 当前前端必要条件 |
|---|---|
| pack | is_950、BF16、scatter_dim=1、D<=2048、T*H>=8V、output feature stride=1 |
| combine | is_950、BF16 recv、DCP_SIZE在1..8、scatter_dim=1、D<=512、local存在、return_lse=False |
| combine行数/stride附加条件 | DCP<=2且D>256时至少8V行，其余至少4V；还要求DCP>2或D<=256或local feature stride=1 |

D=1024/2048可以batch pack而走fallback combine；DCP9/16也可以仅batch pack。不能记录一个总“batched开关”代替两个实际kernel分支。特殊SKU和这些guard是固定代码的dispatch，不代表所有模型/硬件的支持声明或最优阈值。

fused_dcp_lse_combine还检查连续四维NPU recv、head_dim/packed宽度、paired local的post-scatter shape和设备。return_lse需要FP32，defer_combine与return_lse互斥；defer返回通信后的packed贡献，local仍由调用方在join后补入一次。group weakref、world及Fake shape接口的细节见[GQA/CP指南](vllm_ascend_gqa_cp_history_current.md)，FakeTensor传播不执行HCCL。

## core属性、UB与Triton依赖

init_device_properties_triton只在进程全局AICORE尚为-1且HAS_TRITON时，读取current NPU的driver properties；core计数必须为正。get_vectorcore_num要求先初始化。缓存没有按device建key，也没有覆盖并发初始化、切换异构设备或所有部分失败的事务恢复；接入方应记录进程、device和初始化时机。

初始化函数从若干property key取首个>=4KiB的数值，否则使用192KiB默认值，get_ub_size_bytes返回该缓存。默认值的来源注释涉及A2/A3，不能把它当所有设备实测容量。当前DCP分支使用V和固定D/row条件，没有调用get_ub_size_bytes自动调整tile；不要把工具中存在UB getter解释成DCP已动态适配任意UB。

_resolve_triton_ascend_op在HAS_TRITON时先找cann.extension，再找tl；缺少需要的op会报RuntimeError，HAS_TRITON=False时相应导出为None。此处读取了导入时逻辑，没有实际导入或安装扩展。安装包目标和运行设备的核对见[设备类型不匹配](../../runbooks/runtime/vllm_ascend_build_runtime_device_mismatch.md)，ABI与编译器配对另按固定版本验证。

## 测试矩阵只记录已读定义

_A5_FIXED_CASES定义17个固定业务形状，另有5个相对core阈值/尾tile场景。定义在A5条件下先强制is_950=False取scalar，再True比较batched，并用LaunchSpy核实际launch次数。包含DCP1/2/3/4/8/9/16、D128/257/512/1024/2048、stride2、tokens257及不满8行；不能只为跨阈值改业务形状后宣称覆盖原任务。

| 来源定义 | 断言范围 | 本卡的证据强度 |
|---|---|---|
| A5 scalar/batched | payload output精确一致、解码LSE容差1e-2、归并对scalar及reference容差2e-2、dispatch次数 | 未执行；这些是声明容差，没有性能、UB或编译结果 |
| A2/A3单卡模拟receive | BF16/FP16、两个scatter轴、D96/128/160/256、独立stride、NaN/inf LSE及全无效行 | sender pack后stack模拟接收，没有真实HCCL |
| FP32 staged及raw local | 16个history加1个current；36组DCP1/2/8、D96/256/512和local FP32/BF16/FP16，含空贡献 | 定义独立reference；不能改写成所有A5 mixed dtype已验 |
| 多卡定义 | world2 HCCL、两个scatter轴、rank偏置LSE、BF16普通及FP32 deferred+local | 定义barrier和finally销毁group，未启动进程/端口 |
| UT36 | meta/Fake BF16/FP32 shape及mock deferred不提前combine | 未执行，也不验证设备kernel |

A5随机dispatch定义没有注入invalid/all-invalid LSE，不能用A2/A3带guard的无效值定义替代A5实测。多卡文件在A3目录也不证明全部world、PCP、网络或硬件组合。测试guard、预期shape、assert容差、退出码和真实结果是不同证据；选择方法见[测试证据指南](../bringup/vllm_ascend_test_evidence_selection.md)，报告判据见[benchmark结果合同](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)。

## Agent接入与性能验收

接入记录至少包括输入/接收/local的dtype、shape与stride，scatter坐标、四lane顺序、每row有效rank集合、local贡献次数，V和device属性来源，以及pack/combine各自的实际分支。先按独立FP32 reference检查数值、invalid/all-invalid、带stride与尾tile，再覆盖分阶段合并、跨rank通信和目标设备的dispatch边界。

获准执行后，固定版本、模型负载、硬件和质量门槛，分别测pack、通信、combine及端到端时延，保存同步方法、重复统计、编译产物和资源水位。源码中的register/UB动机和16KiB算术不是实测收益；[系统调优](../optimization/vllm_ascend_system_tuning_contract.md)的环境候选不能替代kernel数据。当前没有NPU、HCCL、性能或下游Agent A/B结果。

## 三份op文档的接口说明与证据裁决

补读同一ceac提交的dcp_a2a_fused.md119行、fused_dcp_lse_combine.md49行及pack_dcp_output_lse.md全文。它们把pack→HCCL交换→combine、contiguous recv与strided local、FP32 return_lse及defer互斥整理成直接调用合同；这与前述实际实现范围配合使用，不新增硬件验证。文档列A2/A3 scalar和A5 batched是来源的模式说明，pytest命令和测试覆盖列表也只是定义/入口，本次未执行。

文档称四lane重构保持原有限FP32 LSE，这不能替代本卡对实际log2/exp2编码的值域边界裁决。小整数lane可精确表示、70000附近用例、既定容差和所有有限值逐bit保持是不同命题；subnormal、极小值、符号零和编译中间量仍按独立reference取证，不由概述升级成普遍无损保证。

文档Split MLA小节把history交换放comm stream、current FIA放main；固定当前MLA_CP724–925的decode实现实际先在main算history并stage current，再在side stream等ready算current，main执行history交换后等current完成再单次combine。[GQA/CP合同](vllm_ascend_gqa_cp_history_current.md)也单列decode与prefill各自事件链，不能按这段概述统一交换stream角色。诊断以实际调用路径、event/wait和buffer owner为准；[FlashMLA/DCP执行](vllm_ascend_flashmla_dcp_execution_contract.md)维护外部读端schedule、NTD/FP32 LSE和复制current边界，MLA_CP来源owner保留在那里。

pack文档另明确pack本身不做collective，send的rank-major排列由scatter轴决定；FakeTensor shape传播不代表真实pack或HCCL完成。测试中的payload数据排列atol=0/rtol=0，不等于LSE解码、softmax加权和端到端Attention均逐bit相同，必须分开记录对应断言。
