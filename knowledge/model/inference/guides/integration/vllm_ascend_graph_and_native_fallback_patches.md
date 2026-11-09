---
type: Guide
title: vLLM Ascend 图与原生算子回退：持久输入、捕获门禁和最终绑定
description: 核对Cudagraph descriptor、MRv2 InputBatch/BlockTables替换、adaptive index_fill，以及Triton/FLA/KDA/mHC回退的参数丢弃、状态更新和同步成本。
aliases:
- _create_padded_batch_descriptor
- _IndexFillMode
- _assign_draft_token_budget_ascend
- _fused_recurrent_packed_decode_pytorch
- _mhc_fused_post_pre_npu
tags:
- task.implementation
- task.debugging
- topic.graph_execution
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_cudagraph.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_input_batch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_adaptive_verification.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_triton.py
  role: implementation
created_at: '2026-11-03T05:22:33Z'
updated_at: '2026-11-03T05:22:33Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 图与原生算子回退：持久输入、捕获门禁和最终绑定

## 版本与读取边界

固定 Main ceac1a2 五个补丁整文件AST程序投影已审阅，未逐字全文阅读注释/docstring、导入/应用补丁、编译或运行NPU。这里只描述框架绑定和所含回退数学；依赖的完整kernel、Native父类、实际图捕获与性能仍需目标环境验收。[图融合合同](vllm_ascend_graph_fusion_pass_contract.md)管编译pattern，这里的dispatch/输入/算子替换是另一阶段。

## descriptor和MRv2输入绑定

_create_padded_batch_descriptor先从_bs_to_padded_graph_size取捕获token容量。只有uniform_decode、mode包含FULL且mode本身不等FULL时，按padded tokens/uniform_query取请求数并检查整除；其他分支把uniform=False、请求数=min(padded tokens,max_num_seqs)。has_lora与num_active_loras继续进入descriptor，不能只按token数选择图。

patch_v2.block_table按STANDARD_WORKER_PATCHES能力绑定普通AscendBlockTables或Ascend310PBlockTables至Native gpu.model_runner.BlockTables；patch_input_batch同时更新model_runner与cudagraph_utils的InputBatch。它们没有扫描任意已按名导入的消费者，静态类存在不保证旧实例已替换，也不解除专门310P路径的限制。

adaptive verification只把编译版_assign_draft_token_budget入口换成TorchFunctionMode包装：拦截精确torch.Tensor.index_fill_并委托DeviceOperator.index_fill，其他Torch调用保持原方法。作用域退出会恢复mode，不是永久修改所有Tensor.index_fill_，也不证明预算分配所有图分支已通过。

## FLA/Conv/KDA替换与参数消费

patch_triton更新triton.next_power_of_2：有constexpr_function用其包装原helper，否则解tl.constexpr.value再调用Native数学函数。它是JIT接口适配，不是改变tile大小性能规则。

初始causal_conv1d wrapper会删Native额外的null block、scheduled block、initial state、computed、alignment、validate等kwarg；update还删max_query_len/out/metadata，fn显式接metadata但不传。调用能接受这些参数不代表其语义已落实，依赖这些offset/输出复用的模型要核下层实现。随后绑定Ascend LayerNorm/chunk GDN与可选KDA函数，缺KDA导入时保持该局部原值。

fused_q_kv_rmsnorm回退分别调用两次torch_npu.npu_rms_norm，并更新common ops及已加载模块上同名引用；扫描不是严格只替换某一个原函数身份，不能假定其他库同名函数绝不受影响。ImportError被跳过时，也不能单看插件导入成功就认为该函数已经绑定。

文件末尾再次尝试将causal_conv1d_update绑定到Ascend Triton版本，成功会覆盖先前wrapper；异常时仅警告并保留前一实现。因此最终符号由完整导入顺序决定，不能按中间赋值描述运行行为。fallback警告提示每请求同步影响decode-FULL捕获，该提示不是本次性能测量。

## 无Triton的GDN递归与数值约定

fused_post_conv_prep按Q/K/V不同heads拆packed输入，可用FP32平方和+1e-6做L2norm，再恢复输入dtype；g=-exp(A_log)×softplus(a+dt_bias)，可选返回exp(g)，beta=sigmoid(b)。Q/K heads与V heads并非总相等，不能简单等分三块。

packed decode fallback按initial_state的[HV,V,K]求Q/K head复制比。每请求.item取ssm_state_index，<=0输出零且不更新state；有效时以FP32做H←H×exp(g)，delta=beta×(v-Hk)，H←H+delta⊗k，out=H×(q×scale)，最后按各自dtype写out/state。softplus阈值20，optional Q/K L2norm同样用1e-6。这是串行PyTorch参考路径，不是等价的高性能kernel；每请求Host同步和FP32临时量要计入成本。

同一state slot被多请求指向、state索引上界、HV/H整除及输入view连续性并未在这段全部校验。源码数学、混合dtype写回和单步reference可作为测试设计，不能直接声称长序列递归逐位一致或捕获可行。

## mHC回退与验收

mHC pre与fused post-pre分别调用Native torch pre/post，选填norm_weight时另用FP32 mean-square/rsqrt RMSNorm后cast；n_splits/tile_n在这些wrapper中未参与调用，不视作已实现相同调度。既绑定forward_oot也绑定forward_native，名字fused不意味着本路径变成单device kernel或保留另一实现的精度顺序。

验收记录HAS_TRITON、最终module/function identity、Native签名、被丢弃的参数、实际设备backend、descriptor与输入类。覆盖多次导入、已加载引用、MLA/混合heads、零/非法state、非默认输出buffer、不同dtype与capture/replay；先做数值/state一致，再把Host同步、临时分配及编译分别计时。回退可用、函数替换或少一次图break均不单独证明净收益。
