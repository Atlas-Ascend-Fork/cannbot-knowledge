---
type: Guide
title: vLLM Ascend 3164状态kernel迁移：GDN准备、KDA提交与JIT键
description: '解析GDN对齐缓存元数据融合、KDA普通/边界提交分流、gated RMS激活与MiniMax调度变化，核对DSpark/indexer/Q-RMS预热身份和图buffer边界。 '
aliases:
- prepare_gdn
- _prepare_gdn_kernel
- AscendTritonJitKernel
- TritonQRmsKernel
- state_commit_lens
- boundary_commit_lens
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/mamba/gdn_prepare.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/ascend_jit_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/conv_state.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/gather_initial_states.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/gdn_prepare.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/kda_recoverssm.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/kda_state_copy.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/mamba_precopy.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/minimax_qknorm_rope_cache.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/swiglu_quant.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/dspark_swa_indices.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/kda/recoverssm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/layernorm_gated.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/mamba/precopy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/msa/minimax_qknorm_rope_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/prepare_indexer_indices.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/quantize_indexer_query.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/rms_norm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/docs/postprocess_mamba.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/mamba/postprocess.py
  role: implementation
created_at: '2026-11-03T07:06:48Z'
updated_at: '2026-11-03T07:06:48Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# 状态准备、提交与声明式编译的版本合同

## 版本与知识归属

固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd；完整变更、Python AST新增/替换程序体及必要上下文静态读取，R100文件用完整blob相等复用旧语义。这里不是目标所有源码原文FULL，也没有执行import、UT、Triton/JIT、图或NPU。平台为空表示没有足够证据给整张迁移合同统一硬件范围，不是硬件无关。

[统一启动预热](vllm_ascend_startup_kernel_warmup_contract.md)维护registry生命周期，[Mamba状态I/O](vllm_ascend_triton_mamba_state_io_contract.md)维护selected-row/物理页复制，[归一化与缓存融合](vllm_ascend_triton_norm_rope_activation_contract.md)维护数值基线。本卡只补这些合同在3164的kernel侧变化；生产Caller变更与模型配置门禁仍沿其各自owner核对。

## GDN：一份稳定分组布局驱动元数据与清零

新增prepare_gdn写caller预分配输出并返回None。普通请求取start_block=max((seq_len-1)//block_size,0)的物理state；spec请求从此列取spec_width块，第一块另写conv_indices。query[i+1]-query[i]是本次query长度，initial_state为seq_len>length，不能用累计seq_len替代本次token数。

homogeneous batch不传layout，以输入row直接作组row。mixed batch依赖CPU已稳定分组的[R,2] INT32 layout：非负第一列是spec组row，负值按-dst-1编码non-spec组row，第二列为对应组token起点。kernel按原query读source token区间，再在256-token循环把原token位置写入各组索引；它不在Device排序、搜索或自动修复重复group row。

spec_query/non_spec_query写组内累计边界，spec_lengths/non_spec_lengths写逐请求长度并留leading zero；两种数组不能因为相同shape就互换。accepted按原请求stride读取后重排至accepted_out，padded行填1是占位协议，不是采样接受结果。sequence_masks区分active且spec；prefill_query再减普通decode token数，caller须保证普通decode先于prefill。

NUM_ROWS=max(真实请求数,spec_states行数,non_spec_states行数)，多余行通过query[min(row,R)]产生零length，并写PAD_BLOCK_ID和相关边界。block table/seq_lens/accepted尊重各自输入stride，输出及query/layout按连续协议。caller必须保证query覆盖、组输出容量、混合layout在实际launch行域可读、正block_size/spec_width、state列范围与各目的唯一；wrapper没有全面验证这些条件。

同一grid后半program以1024元素块清conv_output。它与元数据任务无跨program等待，必须是互不冲突的输出区域；不能安排元数据或其他并行消费者在清零完成前读conv buffer。调用方拥有graph-stable storage与stream依赖，本wrapper不做D2H同步。元数据在模型图外准备的文档说明不等于元数据kernel自身已被任何图捕获配置验证。

新文档说明builder只在aligned cache、连续conv indices和足够spec容量时选该融合，其他保留generic路径。完整builder门禁需联查[GDN元数据合同](vllm_ascend_gdn_metadata_builder_contract.md)及其版本，不能只换import便假定所有Mamba布局都能使用。

## 状态搬运：真正的R100与strided conv文档

v2/mamba/precopy.py迁至mamba/precopy.py，旧mamba/postprocess.py迁至v1/mamba/postprocess.py，两者整blob各自相等，不是precopy与postprocess互换。对应文档也随路径迁移，原物理页stride、SD/DS布局、字节尾、8-byte对齐与accepted语义继续按[Mamba状态I/O](vllm_ascend_triton_mamba_state_io_contract.md)处理。

conv_state文档补充：正page/row stride且channel stride=1可直接处理，channel维非连续需pack；packed无效row映射独立null slot而非直接-1。该规则是其wrapper合同，不把所有state helper都概括为必须全池contiguous。gather_initial_states文档本轮仅更正测试位置；kda_state_copy删除旧paired benchmark配方不等于数值正确已自动建立，也不删除独立参考比对责任。

来源测试覆盖数量、A2/A5环境和无同步描述都是作者所记录范围，不是本次执行或所有state布局已通过。连续/非连续、不同物理页距、invalid row、padding尾部、batch收缩后重用应分别验，不只比较逻辑shape。

## KDA RecoverSSM：互斥提交集合与资源上界

prepare plan新增state_commit_lens与boundary_commit_lens：有效且无边界的请求只进入普通提交，有边界的只进入boundary提交，其余长度0。两个集合互斥，合起来覆盖本次有效提交；conv compaction仍消费完整commit长度，不能随SSM分流只处理其中一半。

普通与grouped SSM kernel改为一维(pid_v,layer/head)展平，并把request放入program内循环。num_layers成为do_not_specialize运行时值；commit长度0先continue，再读page ID，因此inactive请求不应触发无效页读取。以layer×head索引恢复正确group；不能把新的grid维和旧二维launch混搭。

grouped路径新增ALIGN_MODE，在boundary内按接受步恢复decay/correction并存snapshot。A5、FP32 state、K=V=128、H=32/64的grouped准入不再一概排除align，但不意味着所有K/V/H/平台都支持。BV<=64仍有静态约束。普通路径按同时活跃2个矩阵预算UB；boundary按6个矩阵并保留2行headroom，tile取资源上界内的2幂，不应把普通较大tile直接复用到边界路径。

host先对state_commit_lens发ALIGN_MODE=False，再在align时对boundary_commit_lens发ALIGN_MODE=True；两个launch均可含长度0的请求，但对应kernel在读地址前跳过。分开launch减少普通请求的边界工作与UB压力，不证明本次实测提速或同步开销可忽略。先验证两个长度向量、页表/accepted映射、边界前后snapshot，再按真实请求组成比较commit与端到端时延；[部署配置约束](../optimization/vllm_ascend_glm_kda_recoverssm.md)仍单独成立。

## Gated norm与MiniMax：新参数和调度不替代舍入合同

layernorm_gated新增activation映射：swish/silu→0，sigmoid→1，其他值ValueError。两个norm-before/after-gate位置都按constexpr选择z*sigmoid(z)或sigmoid(z)；它与[Python入口传播](vllm_ascend_triton_norm_rope_activation_contract.md)配套，不能仅把字符串透传就声称任意activation支持。归约轴、weight/bias及gate前后顺序不改变。

MiniMax Q/K/index Q/index K四份Gemma权重的FP32加载与1+weight移至token循环外，grid=min(tokens,实际Vector cores)，program以INT64起点/步长循环token；NUM_TOKENS加入do_not_specialize，与已有NUM_SLOTS一起减少具体长度特化。它不改变Q/K先BF16舍入、partial RoPE、主/index各自slot和FP8±448饱和合同；enable_fp_fusion=False保留。量化比例、cache dtype和positive slot容量仍由caller负责。

MiniMax文档和SwiGLU文档更新测试数量、路径或覆盖的直接/模型caller；这些证据导航不改变本轮未读改动的数学实现。SwiGLU仍须核group累计/计数、有效行、scale与zero输入，不从来源记录16个case推导所有MoE形状通过。

## 统一JIT wrapper：编译身份、注册时序与真实地址

AscendTritonJitKernel继承Native VllmTritonJitKernel，parallel compile条件为非autotune、triton.AsyncCompileMode存在且VLLM_TRITON_JIT_WARMUP_NUM_THREADS>1，去掉上游CUDA条件。是否允许CANN并发编译是部署属性，设线程1可串行回退；本卡没有测compiler并发安全或冷启动收益。

| kernel | 3164编译键/代表输入 | 必须核对的运行边界 |
| --- | --- | --- |
| DSpark SWA | window、block/table/index宽度、row/query的2幂bucket、真实table stride等 | device-metadata且受支持的路径；需等input batch/draft group建立后注册，不用builder尚未绑定的None表 |
| prepare_indexer_indices | topk、compress ratio、rows/cols tile、write_lengths、position dtype | 128KiB/8缓冲与列宽决定row上限，write_lengths的列宽至少32；真实positions与表布局仍须匹配 |
| quantize_indexer_query | input dtype、head_dim（从模型index_head_dim取，缺省128） | warmup fake[1,1,D]，实际量化保持BLOCK_ROWS16、127上限和2^-24最小scale；不证明所有实际签名命中 |
| Q-RMS | dim、BLOCK_M、dtype | 2/4-byte元素、UB减6144及5/7份活跃数据预算；dim>2048不注册，BLOCK_M覆盖可达2幂 |

SWA原kernel从HAS_TRITON内部提升为顶层定义后通过对象launch，主体未因缩进迁移改变。注册需要实际table宽/stride与可达shape，持久out在capture后不得重分配。其键以真实专门化代表代替穷举具体batch，不证明不同layout共享同二进制；数学索引、request slot和rope状态由[Attention并行迁移](vllm_ascend_3164_attention_parallel_migration.md)与既有DSpark合同维护。

indexer注册仅在目标V4.1配置下依实际非零compress ratios展开；prepare wrapper使用multibuffer=False、unit_flag=False。Q-RMS预热以最小shape和代表stride构造编译输入，runtime仍传hidden_states真实stride；其wrapper不新加weight或改变旧RMS舍入。选择warmup键、成功编译、真正运行目标tensor与图重放是四层证据。

## 给适配与性能Agent的检查顺序

先确认Runner、模型类型和实际Native/Ascend配对，再分离Host分组/容量、Device地址/布局、数值舍入和编译专门化。GDN验证query与group/token映射、mixed/homogeneous、accepted、graph padding和共享conv清零；KDA验证普通/边界集合与snapshot；norm/MiniMax逐中间tensor对齐舍入和cache未触区域。

最后在目标设备观察registry注册数量、实际JIT命中/新增、capture前后buffer地址、首次请求与稳态kernel/通信。记录编译器、冷/热cache、dtype、TP/spec配置和各rank；文档历史性能/测试表不写成当前环境结果，不把线程或本次文本处理耗时算成NPU推理收益。
