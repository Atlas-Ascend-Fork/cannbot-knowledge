---
type: Guide
title: vLLM Ascend MiniMax-M3 稀疏后端：AscendMiniMaxM3SparseBackend、索引缓存与融合入口
description: 适配MiniMax-M3稀疏后端时核对主/索引缓存、融合投影、活跃metadata、CANN与Triton真实分派及Split KV；补generic/A5 TopK返回ABI、128块与16对齐、-1尾槽、FP8和空行边界、tuple
  stack及split-K工作区，不从参考kernel外推生产支持。
aliases:
- AscendMiniMaxM3SparseBackend
- AscendMiniMaxM3IndexerCache
- AscendMiniMaxM3IndexerMetadataBuilder
- AscendMiniMaxM3QKVParallelLinearWithIndexer
- minimax_m3_fused_sparse_forward
- msa_m3_triton.minimax_m3_index_decode
- msa_m3_triton_a5.minimax_m3_index_decode
- _split_triton_main_kv_cache
- _as_triton_main_kv_cache
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/msa_m3.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/ops/msa_m3_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/minimax_m3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/minimax_m3/test_fused_sparse_prepare.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/minimax_m3/test_msa_m3.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/ops/msa_m3_triton.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/ops/msa_m3_triton_a5.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_config.py
  role: constraint
created_at: '2026-10-31T22:53:45Z'
updated_at: '2026-11-03T11:17:29Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MiniMax-M3 稀疏后端：AscendMiniMaxM3SparseBackend、索引缓存与融合入口

## 任务、版本和边界

MiniMax-M3 稀疏 attention 同时管理主 K/V、独立 index K、投影与 RoPE、稀疏块选择及 prefill/decode 调用。适配 Agent 应沿“布局—metadata—写缓存—选块—attention”检查实际契约；性能优化前先证明同一请求视图和缓存 dtype。语言模型层次与权重加载见[语言模型指南](vllm_ascend_minimax_m3_language_contract.md)，部署参数见[MiniMax-M3 部署指南](../models/vllm_ascend_minimax_m3_runtime_variants.md)。

固定 Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整阅读 msa_m3.py 1366 行、msa_m3_npu.py 504 行、语言调用方 1609 行及两个 CPU/mock UT（189、1766 行）。Main 配对 Native 是 544f182d9f0c9bfe8bd7645525951d5e3692a542。后续补充已完整阅读同提交[通用Triton实现](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/ops/msa_m3_triton.py)1618行与[950源码变体](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/ops/msa_m3_triton_a5.py)1378行；本卡蒸馏框架Host接口及其依赖的mask语义，没有建立完整Operator闭包，CANN Device实现仍未闭合。没有执行来源代码、测试或NPU。分支中的 A2/A3/A5 名称只描述源码路径，无法证明整个后端在任一硬件和版本组合都已可用，故保持 draft、空平台。

## 主缓存、Indexer 缓存与物理 dtype

AscendMiniMaxM3SparseBackend 的主 KV 形状为 `[2, blocks, block_size, kv_heads, head_dim]`。Indexer 后端为 `[blocks, block_size, index_head_dim]`，其形状计算不使用 num_kv_heads，缓存只保存 index K。两者都拒绝 include_layers stride 形式；不要把单 K cache 当成完整 K/V cache 或直接套用主缓存页预算。

AscendMiniMaxM3IndexerCache 按 prefix 注册到 static forward context，重复 prefix 报错，生成单 K 的 AscendSFAIndexerCacheSpec。语义 cache_dtype 和显式 physical dtype 要分别核对。UT 中相同 BF16 几何下的单 K 页字节为 FullAttentionSpec 的一半，仅证明这个对象的预算关系，不能推导整个模型 HBM 减半。

Indexer 声明 query 支持 BF16/FP16、head size 128，缓存枚举含 auto、BF16 和多种 FP8；接口枚举不保证所有执行分支都实现 E5M2。语言调用方把 fp8/fp8_e4m3 物理 dtype 固定为 float8_e4m3fn，skip_layers 按字符串层号退回 auto。普通 cache cast 对 E4 先钳到 ±448；独立 index scatter 的 cast 没有同样 clamp，实际输入生产路径必须一起核对。

混合 FP8 block 条件同时要求 M3 架构、cache 为 fp8/E4、非空 skip-layer 配置及 FP8_ATTENTION 能力。满足时三个后端可声明 `[64,128]`，否则为 `[128]`。dense attention 只有原后端类精确为 AscendAttentionBackend 且该条件成立时才覆盖声明，保留原 impl。来源注释说最终 FP8 block 对齐 128，尚不能替代 Native cache planner 的完整验证。

## 融合 QKV/Indexer 的分片合同

AscendMiniMaxM3QKVParallelLinearWithIndexer 的输出依次是 `[q | k | v | index_q | index_k]`。query heads 按 TP 分片；KV heads 少于 TP 时复制。index heads 必须与 KV heads 相同，index_q 跟随 KV 头分片，index_k 在各 rank 都加载第一分片。单个 replicated index K 不等于按 query heads 各存一份。

构造使用 index_head_size 计算部分输出宽度，但 loader 的部分 index_q offset/size 使用 main head_size；因此接受两个参数不证明任意异宽都能正确分片。先验证目标模型主头与索引头宽度和 loader 约定，再支持新的 head geometry。普通 loader、block quant scale 调整和 v2 参数 loader 还涉及不同 Native 私有协议；v2 为 index K 传递 num_heads=TP_size，不能用普通权重测试代替全部量化格式验收。

_use_fused_qkv_indexer 对 quant_config=None 返回 True。存在量化配置时按 prefix 和 language_model.prefix 查找 Q/K/V/index Q/index K 描述；任一描述缺失或为 None 就提前允许融合。只有五项齐全才校验 Q/K/V 类型一致、index Q/K 一致，再以两组类型相等决定融合。缺项不是“已证明类型兼容”。不一致时明确报错；split indexer 与融合投影必须匹配 checkpoint 分片。

量化模块注册 helper 原地修改传入映射，把 qkv 展开为 q/k/v，仅在 split 情况另加 indexer 对应 index Q/K；它没有全面清理历史条目。切换融合配置后要检查最终映射和加载目标，避免复用已被修改的配置对象造成歧义。

## 活跃请求 metadata 与持久 buffer

AscendMiniMaxM3IndexerMetadataBuilder 和稀疏 metadata builder 的 reorder threshold 为 1，声明 UNIFORM_BATCH 和 supports_spec_as_decode。decode 使用 require_uniform=True 的 split，再按首个 decode query 长度计算 `min(num_decodes, num_decode_tokens//query_len)`；query_len 非正时活跃数为零，graph padding 请求应裁掉。

prefill 从 CPU query_start_loc 计算每个实际 query 长度，跳过零长度，累计不超过实际 prefill token 预算。输入计数/token 非正时返回零；正输入却没有选出活跃请求时存在返回至少一个请求的 fallback，不能把这个 helper 当作对任意损坏 metadata 的完整校验器。FIA/SP 尾部 dummy 与真实请求必须分开。

context_lens 等于 seq_len 减 query_len；需要时 start_loc 为 `floor(context_len/block_size)`。prefill 的 cu_q 从 decode token 前缀之后归零；逻辑 KV block 通过 `ceil(seq_len/block_size)` 累计，CPU total/max 和设备 cu_k 一起传给后续处理。各数组必须描述同一份裁剪后的请求集合。

builder 复用按 max_num_batched_tokens 分配的 context_lens/start/cu_q buffer，并返回 view；部分字段还直接引用 Common metadata。后续 build 可覆盖此前返回对象的数据。重复调用两次且地址相同只证明复用，不证明并发、draft step 隔离或图重放正确。

## prepare、opaque op 和缓存写入顺序

minimax_m3_fused_sparse_forward 的真实 opaque 实现在 metadata 不是字典时清零 attn_output 并立即返回，不查 layer 或写缓存；fake 实现是 no-op，不清零输出。正常路径从 forward_context.no_compile_layers 按 layer_name 取对象。PrivateUse1 注册声明 mutates_args 包含 attn_output，不能由此认为隐藏 KV 写入已被所有编译/图模式自动建模。

语言调用方先拆开融合投影，对 Q/K/index Q/index K 做 norm/RoPE，写主 KV 与独立 index K，再执行 Indexer 选块，最后运行稀疏 attention。主 KV、index K 各自使用 metadata 与 slot mapping，按实际 token 前缀写入；不能共享另一组缓存的 slots。融合 prepare 已写 cache 时不再执行第二次插入。

完整融合 prepare 要求 HAS_TRITON、NPU BF16、一维 positions、主头和 index 头均为 128、Neox RoPE、合法偶数 rotary_dim、四个 norm epsilon 一致、缓存为 BF16/E4，且行数不超过 262144。split index Q/K 可直接传入而不 concat。较小 _sparse_prepare fallback 对 A5 有排除，但完整融合 guard 没有显式 A5 排除，不能把局部条件扩大成全局融合禁用。源码的 A3 测量注释没有在本次复测。

非融合插入中，A5 index cache 要求三维形状，经增加轴和连续 key 交给 npu_scatter_pa_cache；其他路径使用展平 cache 与 npu_scatter_nd_update_sk。空 slots 直接返回。主/索引缓存 dtype 与布局应独立验证。

## IndexScore、TopK 与平台分支

后端常量在模块导入时选择路径：prefill 使用 CANN；index decode在A2/A3走CANN score与后处理，A5保留Triton index score/topk入口；主稀疏attention仍从msa_m3_npu导入。改变外部配置不等于已经重新计算模块常量。CANN decode 把完整 index cache、block table、query 长度、context/start 和 mask 交给 facade，本次读到的选块路径没有额外 TP gather；不能据此宣称整个模型无 TP 通信。

msa_index_score 通过动态导入取得 CANN 接口，与可选 Split KV attention 的可用性判定是两件事。缺少 IndexScore 不会自动降级为另一实现。index cache facade 只自动解包 tuple，再扩为 BBND；这不是任意 list 都可输入的合同。

E4 index K 时，query 需要时钳到 ±448 再转 E4。IndexScore 传 BBND、q/k bounds、start/block table，mask 存在时 sparse_mode=3，否则为 0；init_blocks/local_blocks 固定 0，强制初始/局部块留给后续 TopK 处理。

prefill score 列数按最大序列的 128-token 块数计算，再向 16 对齐，切片作为 view 交 TopK。decode 的 index_decode_topk_fused 接收 context、query 长度、TopK、block-table 容量和 init/local 参数。本次已补读两个模型目录Triton文件中的TopK消费；CANN decode使用的独立msa_m3_index_postprocess Device及外部torch.topk实现仍未在本卡闭合，不能仅凭参数宣称完整算子算法已验收。

## Split KV prefill、CSR 与 decode 的 FP8 差异

prefill 通过每个 worker 的 lru_cache 探测 vendor Split KV 入口。探测仍会加载本仓 extension 并 enable_custom_op；实验入口不可用时回到 legacy Q-gather-KV 路径，A5 也可能回退。安装或变更扩展后需重启 worker 刷新缓存，不能把任意 bridge 导入错误都解释成自动 fallback。

Split KV 使用 K2Q 构造 CSR：logical cu_block_lens 来自实际 seq_len/block_size，保留 -1 哨兵，order=1、use_simt=0、q_global_offset=True，并使用 metadata 的 total_rows/max_kv。把 -1 改为 0 会额外引入 block 0 的边。CSR 转 int32/contiguous，每请求 query 长度取相邻 cu_q 差，调用 prefill 接口后 copy 到输出。total/max 缺失为负时才在 helper 中从设备数据 `.item()`/max 推导；传入预先计算值可避免这条推导。

legacy prefill 的 E4 K 要求能力支持且 V 同为 E4，query 钳位转换，使用单位 FP32 反量化 scale、BF16 输出及 inner_precise=4。Split KV prefill 的 BF16 inner_precise 随能力为 0/1，E4 为 4 且检查能力和 V；这个 bridge 没有显式传 decode 的三项反量化 scale/output dtype kwargs，不能跨分支复制合同。

decode attention 检查 `query_rows == seq_count*decode_query_len`，构造每请求 int32 query 长度。已有 selectcounts 时复用，否则由 topk>=0 计数。E4 K 要求 E4 V，但本 decode helper 没有 prefill 的显式能力检查；query 钳位转换，传共享单位 FP32 scale、BF16 输出和 inner_precise=4。SparseImpl 延迟分配并复用 `[1,1,1,1]` scale tensor。声明 cache 名以 fp8 开头会触发准备，但 facade 的具体 FP8 处理仍围绕 E4，不能扩大为所有 FP8 格式。

## 图接线、测试设计与适配验收

两个 update_graph_params 方法均为 no-op；注释依赖先扫描 GQA group 才更新实际 graph 参数。这是注册/扫描顺序前提，不能推导全稀疏模型、所有分组顺序或 MRv2 图模式都已验证。集成时记录实际 group 顺序、buffer 别名、active counts 和缓存地址，再做 capture/replay 数值比较。

来源 UT 用 CPU、mock NPU facade 和 stub module 检查融合 guard、split 无 concat、cache-before-selection、dummy 清零、E4 clamp、主/索引独立页、FIA/SP 活跃请求、CSR 哨兵与 fallback。参数化测试含 TP=1/4/8、decode query 长度 1/4 及 A2/A3 分支模拟；重复 CPU 调用并不等于真实 TP、NPU 或图回放已运行。本次只阅读这些测试。

适配验收先逐项核对 projection shard、物理 dtype/page budget、实际请求数组和写 cache 顺序，再比较 prefill/decode、BF16/E4、Split KV 可用/不可用、SP 与 graph padding 的数值。性能结果另记硬件、软件、序列、并发、warmup、重复次数和误差；本卡没有吞吐、延迟收益或全硬件支持结论。完整Triton/CANN Operator、Native planner与配对ABI仍需独立闭包和运行证据。


## Triton接口补充：真实分派与返回值

两个模型目录Triton实现同属MSA接入任务，但不能整文件互换。msa_m3.py在模块导入时仅为A5选用[950源码变体](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/ops/msa_m3_triton_a5.py)的index decode；prefill固定先经CANN IndexScore。msa_m3_npu再以FP8_ATTENTION能力选A5版prefill TopK，以RUNTIME_CUSTOM_OPS能力选generic版TopK。device_config.is_950把A5对应为950，但设备身份条件和能力条件仍须分别记录，不能用文件后缀代替实际函数绑定。

生产SparseImpl.forward的主prefill/decode attention都调用msa_m3_npu导入函数。两个Triton文件里的minimax_m3_sparse_attn及_decode属于另行直接调用/参考入口，不能由它们存在就声称生产950主attention已切换到Triton。测试可显式选择参考backend，与模型服务分派是两条路线。

| 接口 | generic msa_m3_triton | msa_m3_triton_a5 |
| --- | --- | --- |
| index decode返回 | 默认indices；return_scores=True返回(indices, scores) | 固定返回(indices, select_num_idx) |
| 块分片入参 | block_offset、block_count、global_seq_lens，输出加回global offset | 无同等分片参数 |
| index主存储 | 单K `[pages,128,D]`，部分兼容输入先解包 | 同样归一化为单K，不保留K/V对 |
| main KV接口 | K/V分离Tensor并独立传stride | 归一为 `[pages,2,128,kv_heads,D]` |

返回tuple第二项可能是FP32排序分数，也可能是INT32有效数量；不能只因tuple长度相同就接入同一caller。generic的block_offset以逻辑128-token块为单位，需同时保持local seq_lens与global_seq_lens语义；A5不能直接接受这些关键字完成跨分片选择。

## 布局、TopK与有效槽合同

generic主KV helper直接拆tuple/list的前两个Tensor或两种5D布局，不为适配接口重新stack整份缓存；A5收到tuple/list会torch.stack(dim=1)，引入新的聚合分配和copy。传已有5D Tensor时则按轴permute或直接返回。二者均未完整检查全部K/V shape、设备、dtype或页表范围，归一化成功不能替代缓存合法性和峰值内存验收。

两版稀疏块固定128，index head数要求等于num_kv_heads，score为FP32且末维按16对齐。decode要求total_query_tokens=请求数×decode_query_len，并将扁平query按request-major还原；传max_decode_query_len只执行当前长度不超过上限的断言，不改变当前query布局。main attention用num_heads//num_kv_heads求GQA组，caller还需保证头数整除与每组真实head映射。

选块阶段把init区域score置1e30、local区域置1e29，local后写，在重叠区域覆盖init。并列值的具体索引次序不应作为跨torch.topk实现的固定合同；强制区域数量超过topk也不证明所有强制块都会被返回。prefill TopK原位修改score，不能将score继续当未修改的原始点积分数使用。

generic通过_copy_topk_indices对短宽度补-1、输出INT32，并在decode返回scores时把无效槽置-inf。A5 decode把score宽扩到至少topk并预填-inf，TopK后一次输出INT32 indices和counts，counts对应合法ID数；传out时复用有效query前缀地址。A5 prefill的out分支直接copy原始TopK，没有generic同样的短宽自动补齐分支，短score宽与较大topk/out组合须独立核对。

-1是无效逻辑块哨兵，不能改成0，否则会引入block0。prefill attention及A5 decode按非负ID的数量处理前面若干槽，依赖有效ID集中在前缀；任意把-1夹进中间再保留后面有效ID，不满足同一消费合同。generic decode则扫描最后有效槽位置并逐槽检查逻辑块范围、页号与可见长度；其防护不能移植成A5也具有同样检查的保证。

## dtype、padding与空行的差异

index score有意省去sm_scale，因为消费正全局scale下的排序；参数被接受不代表负scale或非有限scale也与真实点积排序等价。main attention仍用真实sm_scale做softmax，两者不可混用。

main Triton wrapper在KV为E4M3FN/E5M2时启用FP8读后转q.dtype，没有接收独立反量化scale的接口。这只描述源码分支，不是当前生产CANN/E4能力检查或所有FP8格式支持证明。迁移前确认缓存是否已经按单位scale编码、Q/K/V dtype及容器位模式，不把“能cast”视为精度闭合。

decode把padding零长请求的可见长度clamp到0。generic merge对没有有限LSE的行输出零，并用LSE mask避免读取空chunk未写的partial；A5 merge直接计算exp2(lse−max)/sum，全部LSE为-inf时存在-inf−-inf边界，没有同等全空行兜底。A5 prefill的零选块归一化也没有generic的has_lse保护。不可从generic的零输出规则推导950参考attention全padding必定零；实际生产NPU attention是另一个实现，本次没有运行NaN复现或数值验证。

## 调度参数与性能诊断范围

generic decode score按检测AICore数（失败回退32）与total_query_tokens选择chunk，最大256；prefill score tile为96，prefill TopK prepare按Vector Core数（回退64）组织连续query范围。A5 decode score以至少32的检测AICore目标确定chunk，prefill score tile为128。设备探测结果被进程缓存，grid相同或减少specialization只是静态机制，不是时延收益结果。

A5文件声明的VLLM_MINIMAX_M3_DECODE_INDEX_SCORE_KQ、autotune配置和bool mask构造helper，在已读入口里未被消费；改环境变量不能据此宣告实际QK路线已经切为KQ，也不能把配置列表当已执行的autotune。NPU路径明确关闭CUDA PDL；ROCm gfx942专用num_stages=1注释描述另一硬件，不能拿gfx950字符串解释Ascend950的资源配置。

直接调用Triton decode attention时，generic split-K最多4chunk、目标grid64；A5目标grid256且无同样4chunk上限。二者都分配 `[chunks,total_q,num_heads,D]` 的q.dtype partial和对应FP32 LSE，再执行merge。若q每元素e字节，仅这两类工作区约为chunks×total_q×num_heads×(D×e+4)字节，不含输出、score、TopK、框架和编译缓存；A5 tuple stack还另有分配。该Host分配账不等于UB/L1/L0占用或实测峰值。

本次更新的来源增量是两文件2996行全文，调用方只补审msa_m3.py1–155、440–558、855–953，msa_m3_npu.py1–90、160–235，device_config.py1–70与既有UT的270–326、555–595。源码中tl.dot和多kernel调用需要独立Operator任务闭合实际编译执行族、外部torch.topk/CANN、平台/CANN版本、内存和同步；本卡仅作框架接口与诊断facet，不登记source_closed/direct_implementation_closed，不把完整文件阅读写成完整设备算子验收。
