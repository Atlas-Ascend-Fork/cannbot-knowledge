---
type: Guide
title: vLLM Ascend Qwen4Exp QSA：混合请求派发、压缩索引与 MTP 接线
description: 核对3164新增Qwen4Exp/Qwen3.8-Flash-Next实验适配的QSA indexer、24K FIA/GBSA派发、compact515/输出2051、MRv2 MTP namespace及HyperConnection替换。
aliases:
- AscendQwen4ExpForCausalLM AscendQwen4ExpMTP
- QSARequestPlan QWEN4_EXP_QSA_ASCEND
- QSA FIA 24K GBSA compact 515 2051
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/model.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/attention_dispatch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/fia.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/gbsa.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/lightning_indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/qsa.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/gbsa.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/qwen4_exp/qsa.py
  role: implementation
created_at: '2026-11-03T06:32:28Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Qwen4Exp QSA：混合请求派发、压缩索引与 MTP 接线

7d9e补充QSA CPU长度同步的Native版本接线，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的Qwen节；qsa_cache与qsa_indexer不是可按相似类名互换的导入路径，仍须按安装版本核父类。

固定 vLLM Ascend `3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 新增程序，完整 AST 程序投影已读，不执行 upstream import、JIT、NPU、真实模型或性能测试。Native私有类与CANN二进制仍须按安装版本成对验证；保持draft、空平台，不将实验类名当全硬件支持。

## 模型注册与状态所有者

qwen4_exp包lazy导出text/MM模型与MTP；model模块用Ascend Triton HC替换upstream全局函数、安装PLE patch，再绑定Ascend QSA。Backbone移除query_start_loc动态维注解；模型mamba specs只保留len(shapes)=2的GDN项，PLE的专用管理见[缓存所有权](vllm_ascend_qwen4_exp_cache_ownership.md)。这些是import时的全局绑定，不能把Python类继承当作当前进程已经完成注册。

MTP描述将checkpoint本地 `mtp.layers.0..L-1` 映射到target后续runtime层号，按锚定末级层路径替换，其余key保留。draft config创建后才重写quant_description。predictor在first PP或无intermediate时合成embedding/HC hidden，其他rank读intermediate；spec_step按MTP层数取模。非last PP先combine返回hidden容器，last返回(sample_hidden,multi_hidden)。这是Ascend局部PP布局适配，不证明任意PP/spec组合可用。

## QSA cache、RoPE 与选择链

Indexer要求raw/compressed metadata token数一致；无metadata时按skip_topk/out返回或填-1。先裁actual tokens，投影Q/K，再compress+cache更新，即使复用topk也不能跳cache推进。压缩读旧raw历史后将completed keys归一化/旋转并写compressed cache，最后写raw key和position历史，顺序不能任意交换。

fused norm+MRoPE有效ABI：BF16三维、index_head_dim128、rope64、NeoX、interleaved与section[11,11,10]、positions一维或[3,T]。不满足直接ValueError，不能说有任意通用fallback。position先clamp到RoPE表边界是实现行为，仍需实际模型位置语义正确。main attention先等connector，核对side token数，再写K/V、在attention_transfer_window内计算并通知保存；需要真实storage/lifetime与异步消费验收。

LightningIndexer用BF16 Q、[pages,page_size,1,128]压缩cache、ratio4、token_topk2048。每query独立成TND序列，令`position=query_positions[i]`为零基逻辑token位置，`seq_len=sequence_lengths[token_to_req[i]]`为所属request的序列token数；可见完整group数严格为`min((position+1)//4, seq_len//4)`。`position+1`才是包含当前token的长度，不能省略`+1`，也不能把request长度换成本轮query数或spec token数来猜phase。[LI可见长度源码](https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/lightning_indexer.py#L104-L107)

这一步把可见group数传给CANN的`actual_seq_lengths_key`，尚未按512截断；`sparse_count=2048//4=512`是选择预算。随后Triton compact packing使用`max(min((position+1)//4, seq_len//4, 512), 0)`限制可写group槽位数，余槽填-1；它不是LI输入长度的同一阶段。tail另按`tail_start=((position+1)//4)*4`、`max(min((position+1)-tail_start, 3, seq_len-tail_start), 0)`保留至多3个未满组token，仍受request长度裁剪。packing的非负截断不代表caller可以提交非法position或request映射。[compact packing源码](https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/qwen4_exp/qsa.py#L38-L60)

head数<=64，补到8/16/24/32/64并将补head权重置0；零head仍需caller拒绝。每head权重1/sqrt(128)。返回ABI仍[T,2051]，仅前515为compact group selection+3 residual；先全填-1，后端消费该前缀。515并非515个已展开token。

组边界验收须同时核对零基位置、request长度和两个阶段；下表是固定公式的纯算术预期，tail栏列逻辑token索引，不是本次CANN/NPU运行结果。

| 零基position | request seq_len | LI可见完整group数 | packing完整group槽位上限 | tail索引 |
| --- | --- | --- | --- | --- |
| 2 / 3 / 4 | 16 | 0 / 1 / 1 | 0 / 1 / 1 | [0,1,2] / [] / [4] |
| 6 / 7 / 8 | 16 | 1 / 2 / 2 | 1 / 2 / 2 | [4,5,6] / [] / [8] |
| 7 | 4 | 1 | 1 | [] |
| 6 | 6 | 1 | 1 | [4,5] |
| 3 | 3 | 0 | 0 | [] |
| 4095 | 4096 | 1024 | 512 | [] |

因此可见token长度3/4和7/8分别在position2→3、6→7跨完整组边界；单看position3/4或7/8的整数除4会少计边界token。真机验收还须核对选中group内容、compact余槽-1、tail与cache字节及注意力数值，不能用上述算术替代。

## 24K FIA 与 GBSA 的真实边界

请求plan来自scheduler的CPU query_start_loc/phase与CPU seq_len上界，每step构造一次跨QSA层复用。只有prefill可进FIA：总KV<=24K，或本chunk从24K以下跨越该界时整chunk仍FIA；后续chunk才GBSA。decode全部GBSA，不能从本地query_len=1推prefill/phase。相邻GBSA span合并；无plan（含FULL capture）直接GBSA。

FIA将完整group按4展开并重建implicit tail；当group宽>=512且存在tail时给tail预留预算。非法/不可见index转sentinel桶后丢弃，选择为空的行最终清零，不能让softmax对全mask的任意结果进入output。mask按4096 query tile与64MiB预算切块，NPU KV维再按32对齐；极长单行、所有shape仍需资源验证。

FIA paged KV要求匹配四维K/V、128 token页、dense页内布局且page stride为整页倍数；以as_strided暴露物理页空隙，table乘block_stride转换，避免全cache复制。negative block clamp到0不证明坏元数据被修复，物理row0必须可读。FP16/BF16 QKV一致，Q heads整除KV heads；CANN FIA v2用BSH、sparse_mode0和显式mask。

GBSA wrapper同样限定128页、QKV FP16/BF16，token→req、logical positions与seq_len形状匹配。prepare产生稀疏group/count、逐query可见长与row table；metadata和执行必须用同一组属性：TND/PA_BBND、pattern4、causal1、quant0、block_shape[1,4]、q_max1。Python通用GBSA枚举列出量化0..5并不证明QSA已经支持这些模式，当前QSA只NO_QUANT。底层C++adapter另由算子主题记录。

AscendQSAImpl显式supports_dcp=False、supports_pcp=False，输出量化拒绝；先zero完整output，空actual早退。builder为UNIFORM_BATCH，capture不保留Python请求plan，graph params回调是no-op因为依赖持久buffers；这不证明任意请求变化都可安全重放。后端仅128 kernel block，main descriptor要求K/V对称head宽与两head slot。

## HC参考与Agent验收

`qwen4_exp/ops.py`是portable reference：Gemma group RMS使用1+weight、HC silu先除hc_count、gate mix取stream mean、combine用2*sigmoid(injection/hc_count)注入。生产model绑定的是Triton版本，不是该reference。对照时保存真实FP32归约和最终cast，不能把两个同名实现当相同运行证据。

适配先核对Native私有Qwen4Exp接口、registry、QSA metadata、main/raw/compressed所有权、PLE/GDN状态与CANN GBSA包。覆盖混合phase、跨24K chunk、515/2051 ABI、尾部残组、head padding、空selection/空query、MM三轴位置、prefix/MTP拒绝与固定buffer重放；分别检查cache字节与注意力数值，再测端到端。实验源码不构成本次性能或全部模型支持结论。


## 3164 注册接线补充

同版本models.register_model显式将Qwen4ExpForCausalLM、Qwen4ExpForConditionalGeneration、Qwen4ExpMTP映射到Ascend lazy入口；HAS_TRITON时ops包导入qsa_rmsnorm_mrope触发custom-op注册。只创建模型类或看文件存在不代表注册函数已经在消费进程执行；缺Triton不会自动得到该fused ABI。
