---
type: Guide
title: vLLM Ascend DeepSeek V4 索引器：DeepseekV4Indexer、TopK 缓存与多流接线
description: 解释 DeepseekV4Indexer、AscendDeepseekV4IndexerCache 与 IndexerOverlapPlan 的接入，核对计算和存储 dtype、TopK 缓冲、Hadamard、串行只读与多流写入、QLI 元数据等待及 Native 配对边界。
aliases:
- DeepseekV4Indexer
- AscendDeepseekV4IndexerCache
- IndexerOverlapPlan
- AscendIndexerOps
- get_indexer_k_dtype
- hadamard_linear
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/indexer.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_indexer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/attention.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/deepseek_v4/attention.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/attention/backends/mla/indexer.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-10-31T22:21:44Z'
updated_at: '2026-10-31T22:21:44Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DeepSeek V4 索引器：DeepseekV4Indexer、TopK 缓存与多流接线

## 接入任务与固定范围

新模型复用 V4 稀疏索引器，或在共享 TopK、多流、量化与缓存重用后出现结果错位时，沿“配置 → Indexer cache/state → Q/K 准备 → 选择 → 下游压缩 KV 发布”核对所有权。本卡串联模型调用方；[Lightning Indexer](../../concepts/modules/lightning_indexer.md)与[Indexer Prolog](../../concepts/kernels/indexer_prolog.md)保存算法和其他来源的实现，[SFA 地址视图](vllm_ascend_sfa_replicated_cache_views.md)保存 metadata builder 与地址生命周期，不能相互替代。

Main 固定 ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文阅读 indexer.py 768 行、UT 528 行和一行配对 pin；对照独立 Native 5df63a7203cdb9328d824a27b682e77c7b9928be 的 attention config 227 行，以及 cache 类 882–925 行、backend dtype/helper 45–97 行和类选段 265–373 行。两个 Native 实现文件均未全文闭合。Main 的配对 pin 为 544f182d9f0c9bfe8bd7645525951d5e3692a542，独立 Native 快照不是该提交。整项硬件、配对私有 API 和实际 kernel 未验证，保持 draft/空平台。

## 分开决定计算 dtype 与物理缓存

get_indexer_k_dtype 按当前 profile 的 DSV4_COMPRESSED_CACHE 能力选择白名单和默认值，随后调用 attention_config.resolve_indexer_kv_dtype(default)。无该能力时只接受 int8，auto 默认 int8，返回 torch.int8；有该能力时只接受 fp8，auto 默认 fp8，返回 torch.float8_e4m3fn。此处没有 BF16 写路径，不支持的显式值提前 ValueError。

这两个分支的变量名带 A3/A5，但实际判断是能力，不构成所有硬件、模型或运行组合的支持表。计算 dtype 也不能由 Native STR_DTYPE_TO_TORCH_DTYPE 的存储映射推导：该映射把 fp8 对应为 UINT8，而这里需要 E4M3 计算类型。主 attention KV 仍按自己的[KV 计划](vllm_ascend_dsv4_kv_plan_contract.md)解析，不能改一个主缓存选项就认为 Indexer 也完成同样切换。

独立 Native 的 IndexerKVDType 声明为 auto/bf16/fp8/mxfp4/nvfp4，不含 int8；其 resolve_indexer_kv_dtype 只是 auto 时原样返回调用者 default，否则返回配置值。因此 Main 传入 int8 默认值与独立 Native 的显式配置词表存在边界差异，不能仅凭 Literal 声明断言实际 CLI 已拒绝，也不能凭 resolver 返回值声称显式配置已通过整个校验链。应在真实配对版本分别核对配置生成、解析和模型白名单。

Native DSA helper 的白名单是 fp8/mxfp4，MXFP4 的 GPU/ROCm 条件与模型限制属于它自己的路径。config 中 indexer_sparse_logits 的 SM100、DeepGEMM、DeepSelect 和 ROCm gfx950 条件也不是 Ascend 950 的支持证据。V4.1 候选块机制复用[既有指南](../models/vllm_ascend_deepseek_v41_platform_boundary.md)，不把两个模型的默认值或 QLI 入口合并。

## AscendDeepseekV4IndexerCache 与构造职责

AscendDeepseekV4IndexerCache 的父类构造接收 head_dim、dtype、prefix、cache_config 和 compress_ratio。独立 Native 父类按 prefix 注册 static_forward_context 并拒绝重复层名，bind_kv_cache 使用 squeeze(1)。这些是已读父类选段，实际安装版本仍须核对相同接口。

Main spec 取 DSV4_BLOCK_SIZES[全局 cache block_size][0][0] 作为 storage block 行数，提交给 scheduler 的 block_size 为该值乘 compress_ratio，并传 tokens_per_state=ratio、单 KV head、head_size、model_version=deepseek_v4 与该层 cache_dtype_str。scale_dim 仅在 head_dim==128 时为 1；有压缩缓存能力时 scale_dtype 为 FP32，否则 FP16。逻辑原始 token、压缩行和物理页字节不是同一单位。

backend 维持 lazy import：ratio4 选 AscendDSAC4Backend，128 选 AscendDSAC128Backend，其他值报错。独立 Native cache spec 则直接用自己的 cache_config.block_size，max_tp_shards=1，按 fp8_ds_mla 选择 alignment576，否则512；其 V4 backend 声明 kernel block256，对应注释中的 C4 压缩64行。这些页面合同不能复制成 Main 的布局。

DeepseekV4Indexer 总会解析 K dtype，但只在 compress_ratio==4 时创建 k_cache，在 ratio>1 时创建 Compressor，并设置 rotate=True。Compressor 能构造 C4/C128，以及 cache 类有 C128 backend，并不证明该 Indexer 的完整 C128 TopK 路径可用：下述选择调用仍固定 cmp_ratio=4。

wq_b 是 q_lora_rank 到 n_heads*head_dim 的 ReplicatedLinear，包一层 CVLinearWrapper；weights_proj 从 hidden_size 到 n_heads，quant_config=None。分别保存 index_topk、rope_head_dim、skip_topk 与 use_index_cache。CV facade 的量化/通信合同复用[CVLinear 接入](vllm_ascend_cvlinear_qkv_overlap.md)，不据当前调用方假设任意 Linear 的 bias、hook 或量化格式均可复用。

## TopK 缓冲不是 Indexer K 缓存

skip_topk=True 要求构造时有 topk_indices_buffer，forward 直接读它，不重新计算 TopK；use_index_cache 则控制结果是否回写这个 buffer。二者与保存压缩 key 的 k_cache、压缩状态缓存不同，也不意味着跳过主 attention 的 KV 更新。

_get_cached_topk_indices 按 offset:offset+num_tokens 切行；二维结果补 singleton head 维。缺 buffer 的读操作 RuntimeError。_update_cached_topk_indices 无 buffer 时直接返回，按当前结果行数与 TopK 宽度切目标；三维输入写二维目标时要求 head 维恰为 1，否则 ValueError，再 squeeze/copy。forward 对两个 helper 均未传 offset，使用默认0；独立 helper 的 offset 能力不能推成调用链自动按请求分槽。

调用方须保证容量、dtype、有效 token 次序、跨层共享和每步生命周期一致。切片本身不验证全部容量与所有 shape；这套代码主要使用二维目标，不能外推任意三维目标也安全。use_index_cache=True 但未提供 buffer 时的静默写入跳过，也不是缓存已建立的证明。

## 压缩 key、Hadamard 与只更新缓存入口

_get_indexer_cache_metadata 取得 metadata.compressor.cache.req_metadata 和同组 hadamard，二者均断言非 None。AscendIndexerMetadata 是只封装 compressor 的 frozen dataclass，不等同于完整 metadata 字段 schema；cache/state 路由复用[压缩器接线](vllm_ascend_compressor_state_cache_contract.md)。

hadamard_linear 把最后一维摊平，补零到下一2次幂后调用 F.linear，同时返回原 shape 与原 dim。hadamard_scale 乘给定系数、裁回原维并 reshape；rotate_activation 使用原 dim**-0.5，而非补齐维度的倒平方根。矩阵形状、方向与来源也应核对，不能只看到 Hadamard 名称便替换矩阵。

update_cache 是不投影 query、不重新选择 TopK 的入口：空 hidden 行直接返回；解包 state/key/scale/full cache 后，调用 Compressor 得 key/slot，空 key 行返回；若 compressor.rotate 为真，在调用方做 rotate_activation，再量化写 K。返回 key_scale 非 None 时另写 scale。压缩器类仅保存 rotate 标志而未在自身 forward 旋转的边界，在这个调用方得到补充。

普通串行准备也先投影 Q，按 [T,N,D] 整形，只对尾部 rope_head_dim 做 interleave RoPE，再做 Hadamard。write_cache=True 时才压缩并旋转 Indexer K；空压缩结果改为 None，交给组合量化/写入 facade，而不由本方法自行推定所有底层空输入行为。

## 串行只读选项的实际范围

_is_w8a8_dynamic 在此模块只识别 quant_method.quant_method 的 inner W8A8，直接 scheme 不命中；_is_mxfp8_dynamic 同时接受直接或一层包装 MXFP8。二者与 CV facade 的检测规则不完全一样，不能按同名概念假设所有入口都走相同分支。

串行路径在 inner W8A8、有 qr_pertoken_scale 且 profile 没有 FP8_ATTENTION 能力时直接 npu_quant_matmul，输出 dtype 取 hidden_states.dtype；其他情况调用 wq_b(qr)。weights 为 weights_proj(x)*head_dim**-0.5*n_heads**-0.5，再交由 DeviceOperator 准备各 dtype/scale，不在本方法硬编码全部平台的准备格式。

write_cache=False 传入串行 helper 后，不压缩或组合写 Indexer KV，改为只量化 Q、选择已有 K；forward 外侧的主 attention 压缩/写入也由该开关跳过。但 use_index_cache 仍可回写 TopK buffer，因此它不是整个 forward 无状态变化的承诺。

尤其是 aux_stream 非 None 且 skip_topk=False 的多流分支，没有向内部 helper 传 write_cache：仍压缩/写 Indexer K，并执行主 attention KV 的 compute/scatter callback。不能把串行只读开关推广为多流只读。需要完全禁止写入的调用方应核对所选路径及所有 buffer 所有者，不通过删等待或屏蔽单个 scatter 假装实现同一语义。

## IndexerOverlapPlan 的两段多流顺序

IndexerOverlapPlan 声明 compute_attention_compressed_kv() 返回 KV/slot、scatter_attention_compressed_kv(KV,slot) 负责发布，以及可选 aux_stream。它串联主 attention 的压缩工作，不把 attention KV 与 Indexer K 当同一缓存。

第一段由 _cv_compute_query_and_update_cache_multistream 准备 Q/Indexer K。已有 qr scale 且匹配本层 W8A8/MXFP8 检测时复用预量化输入，否则使用 CV quantize。主流先压缩/旋转 K、record ready；辅助流等事件，量化并写 K；主流执行 Q_b GEMM。inner W8A8 且传入原 qr scale 时直接 quant matmul，其他情况用 CV matmul。

有 K 时主流等待辅助流，然后做 Q RoPE，并记录 rope_done。若 K 与 key_scale 均非 None，辅助流再等该事件写 scale；源码注释说明打包 epilog 已一并写 K/scale 时返回 None，跳过独立 part3。主流提交 hadamard_linear，等辅助流后再按原 head 维缩放/裁回。这里保存的是正常路径的数据依赖，不是异常清理、图重放或实际 Vector/Cube 重叠收益证明。

第二段 _select_topk_multistream 在辅助流启动 weights_proj 并记录完成事件；主流量化 Q，同时运行调用者提供的主 attention KV scatter callback，等 weight 完成后再选择。源码明确要求该 callback 仅提交当前主流上的独立 Vector/AIV 工作，不切流、不启动会争用的 Cube；此约束写在注释中，没有通用动态检查器。

无辅助流或 skip_topk 时，write_cache=True 的 forward 会在外侧执行主 attention KV compute/scatter；正常多流路径在内部 callback 已做该事，外侧不重复提交。新接入应同时核对两套缓存的实际更新次数、callback 的引擎和 stream、事件与 buffer 生命周期，不能仅用输出 shape 验收。

## AscendIndexerOps 与 QLI 参数

AscendIndexerOps 委托 DeviceOperator 解包缓存、量化 Q、K quant/scatter part1 和 scale scatter part3。组合路径调用 indexer_quant_scatter，使用其 Q/Qscale 后继续选择；这些 facade 调用不代表本卡已全文闭合所有 Device 实现。

select_topk 先 wait_for_device_metadata(DeviceMetadataStage.INDEXER,id(metadata.qli_metadata))，再调用 _C_ascend.npu_quant_lightning_indexer_v2，不能用压缩器的 group ID 替换此对象身份。传入原 block_table、qli_metadata、qli_cu_seqlens_q、qli_seqused_k、qli_cmp_residual_k；weights 与 Q/K scale 各经自己的 prepare 方法，quant_mode 由 DeviceOperator 返回。

接口固定 layout_q=TND、layout_k=PA_BBND、mask_mode=3、cmp_ratio=4、return_value=0，topk 取 config.index_topk；只返回索引，忽略第二返回值。QLI 块表/压缩长度/residual 必须与 Indexer 的 cache group 一致，不能拿主 attention 序列长度或其他模型的布局字符串代填。

## Agent 验收与回退

先记录实际 Main/配对 Native/算子包、能力 profile、用户与解析后 dtype、物理页 shape/stride、head/ratio、cache/state group、QLI 请求边界和 metadata readiness。分别覆盖自动/显式 dtype 与拒绝值、缓存页绑定、空更新、原维与补齐维 Hadamard、直接/包装量化 scheme、已有/缺失 scale、不同 TopK buffer/offset/head 维和容量。

再覆盖 skip_topk/use_index_cache 各组合、串行写入/只读、多流开启、两种 scale 写入形式、callback 顺序与主 KV 更新次数。空 forward 仍会取 cache metadata 与按层 cos/sin，不能据 update_cache 的空行早退推断所有入口都不会访问 metadata。

528行 UT 定义 CPU 张量与大量 mock：Hadamard 用单位矩阵验证补齐/原维缩放，TopK buffer 验证 offset 与 head 维，缓存和选择验证参数路由。只读 UT 选择 aux_stream=None；forward 的多流准备、选择、callback 和 NPU 算子被替换，不能把这些测试定义当真实设备、流同步或 kernel 数值证明。本次没有执行这些 UT，也未导入上游代码、JIT/编译、加载模型、执行 NPU/图/CP/精度/性能或 Agent A/B。

功能和数值通过后，再在固定权重、长度、并发、拓扑与图模式下比较 Q/K 准备、QLI、主 KV scatter 的时间线、峰值内存、TTFT/TPOT 与吞吐。源码的重叠意图不提供实测收益。失败保留原页与 metadata、恢复明确配对的串行/量化/缓存组合；不要去掉 dtype 拒绝、改固定 ratio 或删除事件掩盖接口分歧。完整 Device 路径仍需专用算子 producer，verified 事件保持缺省。
