---
type: Guide
title: vLLM Ascend KV量化格式：INT8、MXFP8尺度与TurboQuant页布局
description: 区分INT8 C8、MXFP8与TurboQuant的尺度和缓存格式；追踪dense INT8量化/反量化分支、MXFP8四组件页分配、定点K-scale写入及QFA逐步metadata/layout/mask，保留非对称offset、PAD/null块、PD与外部算子ABI边界；补Mooncake V1的组件配对、stride READ和失败释放通知。
tags:
- task.implementation
- task.debugging
- topic.precision
- topic.kv_cache
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/kv_c8.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/mxfp_c8.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/turboquant/cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/turboquant/config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/turboquant/latent.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/turboquant/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/kv_cache/test_kv_c8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/test_mxfp_c8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/kv_cache/turboquant/test_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/kv_cache/turboquant/test_latent.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/kv_cache/turboquant/test_capacity.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/kv_cache/turboquant/test_packing.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_c8_mxfp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/attn_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/mxfp_k_scale.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/mxfp_k_scale.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_attention_c8_mxfp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_kv_cache_mxfp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mxfp_k_scale_scatter.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/kv_cache/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_connector.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/utils/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/utils/mooncake_transfer_engine.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/kv_p2p/test_mooncake_connector.py
  role: evidence
created_at: '2026-11-02T12:38:15Z'
updated_at: '2026-11-03T01:35:08Z'
platforms: []
aliases:
- AscendC8KVCacheAttentionMethod
- AscendC8MXFPKVCacheAttentionMethod
- TurboQuantLatent
- validate_turboquant
- packed_layout
- PHYSICAL_STRIDE_ALIGNMENT
- AscendC8AttentionBackendImpl
- AscendC8MXFPAttentionBackendImpl
- AscendC8MXFPMetadataBuilder
- scatter_k_scales
- _forward_c8_decode
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend KV量化格式：INT8、MXFP8尺度与TurboQuant页布局

## 接入任务与证据边界

新模型启用KV量化时，应把checkpoint尺度、运行时method、真实缓存页和Attention消费者连起来，不能只按C8、FP8或4bit名字替换dtype。本卡固定Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`。在原6份实现/6份UT全文基础上，补读MXFP8 backend全文933行、K-scale kernel/文档和3份专项UT全文；INT8 subclass1383–1830、相邻FIA/builder及MRv2 allocator只取来源简表中的明确范围。源码、文档和测试均只作数据，未导入、执行UT、调用算子、JIT或NPU；外部FIA/QFA实现、整项硬件、数值和性能仍未验证。

[ModelSlim接入](vllm_ascend_modelslim_scheme_adaptation.md)维护注册与加载生命周期，[KV recipe选择](../../runbooks/precision/vllm_ascend_modelslim_kv_recipe_selection.md)维护使能和名称映射。本卡聚焦method被选中之后的尺度与格式；[MRv2页回收](vllm_ascend_v2_kv_block_recycle_contract.md)、[DSV4 Attention计划](vllm_ascend_dsv4_kv_plan_contract.md)和[V4.1缓存池](vllm_ascend_v41_cache_pool_contract.md)继续维护各自消费者及物理资源合同。

## 五条路径分别登记

| 路径 | 当前实现创建或处理的内容 | 适配时不能混用 |
|---|---|---|
| FAKQuant MLA | `fa_q/k/v`的per-head scale/INT8 offset；派生K descale、reciprocal和latent quant_kscale。 | 它的dim0 TP loader不是dense MXFP8的GQA复制规则。 |
| INT8_DYNAMIC Indexer | `indexer.q_rot/k_rot`两个index_head_dim平方的FP32参数。 | Indexer旋转参数不等于主KV的INT8 scale或完整缓存格式。 |
| dense INT8 C8 | K/V各一份scale与offset，装载后flatten；安装C8 backend impl。 | 主KV、Indexer和MLA FAKQuant不是同一个C8分支。 |
| dense MXFP8 C8 | FP8 E4M3 payload；类约定K动态逐token-group尺度、V静态逐channel E8M0尺度。 | V原始E8M0字节与量化用reciprocal是两个对象，backend页格式仍需核对。 |
| TurboQuant | BF16模型上的512维旋转、固定16级codebook与紧凑latent行；另有模型族门禁和DSV4页规划。 | 它不是普通INT8、MXFP8，或V4.1 packed缓存的替代dtype。 |

这些方法的`quant_description/prefix`字段存在，不代表任意recipe自动选中它们。默认参数能创建也不证明checkpoint含正确校准尺度，实际选择仍按既有recipe入口核验。

kv_cache包的`__init__.py`仅导入/导出AscendC8KVCacheAttentionMethod、AscendFAQuantAttentionMethod与AscendSFAQuantAttentionMethod；没有自动导出MXFP8或TurboQuant类。导入此包不能替代专门method的选路、外部算子注册和依赖核验。

## INT8 C8的装载、角色与backend

`AscendC8KVCacheAttentionMethod`在构造时记录当前kv_transfer_config.is_kv_producer。只有该标志为False时，create_weights才把kv_cache_torch_dtype设为INT8；producer为True时本方法不覆盖该dtype，不能据此推导P/D两端缓存已经相同。

四个参数初始scale为1、offset为0，dtype取torch默认浮点类型。`_c8_kv_scale_weight_loader`先squeeze已加载值；shape不同则按param dtype克隆并替换其data，否则copy，最后postprocess统一flatten。这个loader没有实现FAK或MXFP8的TP切片逻辑，也没有因shape能装下就证明scale粒度、校准值和backend消费一致。

FAK的`_fa_quant_weight_loader`对双方均单元素时fill；其余按loaded_weight首维除TP的整数商narrow，并断言结果shape等于param。这里没有单独的首维整除检查，不能把它推广为所有GQA head复制规则。FAK postprocess的repeat/view也依赖实际K-scale几何，不能从单值测试外推任意head布局。

dense C8有impl时直接更换其`__class__`。这不会调用新类构造器；MXFP8安装另会设置attn_backend，并补`enable_hamming_sparse=False`。两种dense method的`apply`均明确抛错：缓存量化交给Attention backend，不能为了让统一scheme接口运行而绕过此拒绝。以下补到实际Host分支，不构成所有图或PD组合已运行的证明。

## MXFP8的E8M0与GQA尺度

`AscendC8MXFPKVCacheAttentionMethod`设置FP8 E4M3缓存dtype，按本rank的num_kv_heads×head_size_v创建uint8 V-scale参数，缺省字节127。loader先flatten ModelSlim列向量；若较小尺度能够整倍覆盖本地参数，则repeat共享尺度；仍不等宽时，按当前param宽度推导全量head片段，并以TP复制组选择来源，最后校验元素数并view_as后copy。

例如UT定义全量2个KV head、TP4时rank0/1取head0，rank2/3取head1；共享单head尺度还可铺到多个本地head。这是所读规则与测试例，不是任意head数、分片比例或预分片checkpoint均兼容的承诺。[Linear TP尺度](../../runbooks/precision/vllm_ascend_quant_scale_tp_sharding.md)处理另一套组相位，不能照搬其切片替换此loader。

postprocess把raw字节0改为中性127，随后以FP32计算exponent=raw−127、reciprocal=1/2^exponent，再转模型dtype；raw E8M0字节仍保留供V-scale cache使用。127表示尺度1，128表示尺度2、reciprocal为0.5。缺权重时的中性默认或零通道修正不代表完成校准，也不构成所有指数值在目标dtype下数值安全的证明。

静态尺度只说明来源；共享页被其他状态覆盖后仍需恢复。初始化填充、动态清零与静态V-scale恢复的次序沿已有页回收卡处理，不在这里重建另一套生命周期。

## INT8执行：有效行、对称反量化与分支边界

`AscendC8AttentionBackendImpl`先准备并缓存本rank尺度，只量化num_actual_tokens有效前缀：`round(x/scale+offset)`后clamp到[-128,127]再转INT8。尺度准备以`_c8_scales_prepared`属性是否存在为返回条件；后续替换checkpoint参数、device或backing不会由此自动重建。非scalar尺度会按head宽和TP起点切片，不能只凭默认scalar参数可创建就保证后续BNSD reshape成功。

DecodeOnly走NZ五维K/V视图和FIA V1 BNSD，block size要求32倍数；ChunkedPrefill将decode前缀交分页FIA，新prefill可直接用原浮点KV，续接prefill则按block table gather并反量化成dense TND。gather先读整张表指向的块，再mask无效token，故尾部块号也必须可寻址；dense materialization带来临时分配与字节成本，不能把decode的zero-gather收益套给续接prefill。

需明确对称限制：量化用了offset，但分页decode只传antiquant scale，paged gather仅乘scale；只有非分页INT8分支显式先减offset。源码没有在所有入口统一拒绝非零offset，不能宣称任意非对称C8在所有分支等价。应分别验证实际checkpoint和所走分支，而不是把offset删成0掩盖差异。

PD producer非decode分支复用父实现；consumer侧覆盖了capture/DecodeOnly，但该方法没有为所有其他PD state提供统一返回路径。capture还依赖父FIA的enable_c8_quant条件才安装C8 scale/NZ参数，不能仅因impl类已替换就推广到MTP、多token或全部PD场景。INT8 scatter未显式传入MXFP helper所用的PA_NZ cache_mode，两者的外部API默认值也需按实际版本核验。

## MXFP8四组件页与定点写入

物理顺序为`[K | K_scale | V | V_scale | padding]`，返回tuple却为`(K,V,K_scale,V_scale)`。K/V是五维PA_NZ视图，K-scale为`[blocks,H,B/16,Dk/64,16,2]`，V-scale为`[blocks,H,Dv/16,B/64,16,2]`。payload各项分别为H×B×Dk、H×B×Dk/32、H×B×Dv、H×B×Dv/32字节；例如H1/B512/Dk=Dv256共270336字节，不能漏算或重复算尺度。

`mxfp_cache_spec`保留真实K/V head维，以state_content_bytes计入尺度，要求tokens_per_state=1且物理head槽匹配；MRv2为精确FullAttentionSpec创建一个combined int8 raw allocation。scheduler页必须整除kernel block，padding页成本也必须可按ratio拆分。`mxfp_cache_views_for_spec`把page_size/ratio作为所有组件共同pitch，叠加raw的非零storage_offset；禁止将这些strided视图contiguous后仍沿用旧注册地址。

Q/K动态MX量化，V用checkpoint reciprocal静态量化；sharing consumer不写自己的dummy K/V。payload scatter以同itemsize INT8 view保留FP8位模式，显式cache_mode=PA_NZ，不作数值INT8转换。静态V scale由runner初始化及回收恢复，逐token仅写K-scale，写完后才notify缓存可用。

K-scale避免NPU IndexPut整视图copy-back覆盖其他请求的异步传输，改由`scatter_k_scales`逐字节定点store。Host验证源字节数等于T×H×G×2；Device按真实6维stride和索引stride计算int64地址，每program处理256字节。它不校验目的索引值、不原子合并重叠写、不同步同址DMA；调用者仍须保证范围、设备、别名和并发所有权正确。

PAD有两种处理：payload scatter交外部算子跳过负slot；K-scale将负slot夹到0并实际写null槽，不是跳过。安全性依赖block0确为保留null块、真实请求不占该地址；本卡未用独立Native快照冒充paired版本证明这一前提。定点写能保护未选页，不等于完整传输/Attention依赖已经建立。文档中的950DT验证陈述仅归属上游文档，本次没有执行其NPU用例。

## QFA的逐步缓存、长度与布局

backend入口声明kernel block512并拒绝PCP/DCP；forward另拒绝noncausal、SWA、Hamming sparse和fused输出量化。kv_transfer配置须通过uses_mooncake_connector检查，错误路径指向移动全部四组件的MooncakeConnectorV1约定；完整helper组合识别、远端格式和传输生命周期仍需沿connector核验。

每步共享AscendMetadata内的QFA缓存，builder每次创建新metadata对象。长度由持久GPU query_start_loc clamp/cummax、seq_lens clamp(min=1)派生并缓存，graph必须重放这段device计算；更新CPU列表不足以刷新capture。clamp不能凭空补齐缺失query，调用者仍需保证末边界、request extent和实际T一致，也不能跨步复用旧metadata缓存而不重建。

max_seqlen_q是最长单请求query，缺失才回退token总数。query-head可整分KV-head且G×maxQ≤80时，Q-scale按字节视图转N2TGD，否则留TND；这是模板选择阈值，不是测得吞吐。maxQ=1用NO_MASK，其余保持CAUSAL；metadata与主算子的layout/mask必须一致，MTP verify不能因被称作decode就去掉因果mask。

plan key包含head数、head维、maxQ、mask和Q-scale layout，依赖对象严格限于当前step。源码dataclass注释仍称capture绕开cache，但当前实现和专项UT没有这个绕过分支，应以实际调用为准。QFA边界把uint8尺度reinterpret为torch.float8_e8m0fnu并传给cann_ops_transformer的metadata/main双接口；位模式view不等于数值cast，安装包签名、stride支持与capture行为必须在目标版本实核。

新增CPU/mock UT定义了ratio1/2/8、非零offset、padding隔离、四组件copy、null-slot、最长query/80边界、mask及每步共享plan等断言；均未执行。自有kernel的地址合同已读，不把测试定义、源码注释中的on-device陈述或缓存调用减少当作本次设备/性能结果。

## TurboQuant按模型族校验

`validate_turboquant`先由精确cache dtype `turboquant_4bit_nc`决定是否进入；普通dtype直接返回，不探测这些能力。共同门禁是模型BF16和profile声明TURBOQUANT_4BIT_NC_CACHE能力。错误文本中的A2/A3不是本次真机支持结论。

之后由`model_uses_sfa_sparse`选择packed SFA主缓存或compressed DSV4分支，不能按名称把任意MLA模型放进同一路径：

| 分支 | 所读校验 |
|---|---|
| SFA | 与enable_sparse_sfa_c8互斥，禁用xLite graph，kv_lora_rank=512、qk_rope_head_dim=64。该分支没有把DCP/PCP=1或Runner V2列为共同前提；UT专门定义SFA允许DCP2及V1配置。 |
| compressed DSV4 | model_type必须deepseek_v4；要求V2、head_dim512/RoPE64、index_topk512或1024、Indexer INT8、总query heads可被4×TP整除、DCP=PCP=1、KVPP size不大于1、无KV transfer配置。 |

DSV4还探测当前进程或libnnopbase.so中的`NnopbaseSupportTensorV2`符号，缺失则拒绝；符号可见不是完整CANN/ops ABI或真实执行验证。SFA validator允许某项配置也不等于该模型全部CP、Runner、graph或connector组合已通过。具体Attention plan继续从既有DSV4卡追踪，不用删除门禁凑出可启动配置。

## 旋转、codebook与258字节行

`TurboQuantLatent`应在图捕获前初始化。默认路径按seed0构造signed Hadamard与固定16个centroid；legacy_hadamard路径先消费400000个历史Lloyd-Max RNG样本再取signs，以保持旧DSV4旋转序列。400000是兼容常量，不是任意可调优化参数。

legacy transforms按device缓存并在层间共享只读tensor，inverse保存连续转置；默认SFA路径各实例持有自己的transform。第一次初始化之后换device会报错。forward/inverse以FP32计算再转回输入dtype，并按512维reshape；lazy初始化存在不证明冷启动就能安全放进graph capture，变换地址、生命周期和捕获前准备仍须核对。

compress将旋转后的连续值交给懒加载的ops-nn TurboQuant；返回的packed值对应512个4bit code、256字节。Host显式后处理分支再附FP16 scale的2个字节，得到每行258字节；scale还需用选中centroid的norm校正，不能直接把算子原始norm当最终scale。legacy NPU的finalize、分页写入与allocator执行链另见[TurboQuant执行](vllm_ascend_turboquant_execution_contract.md)。UT注入CPU参考函数，不证明该ops-nn算子具有生产CPU backend或与真实算子逐位一致。

UT定义了旋转前后attention含sink的对应、空/零行、norm校正、共享transform及历史随机序列；均未执行。不要混用default和legacy basis，或只让写端旋转而读端query/输出使用另一套basis。

## DSV4 packed池、共同stride与容量

`cache.py`是DSV4紧凑页规划，不把它自动套给所有SFA backend。`uses_turboquant_groups`看spec的dtype标记而非必须存在C4，并跳过未物化的None group；UT覆盖只有C128的PP rank。`group_specs`按C4原组成本推预算，将各组切成可容纳的chunk，保留非C4 spec与state padding。

`packed_layout`在每个group内部按页大小安排对齐offset，再让完整groups覆盖同一个global block ID的物理slot，使用共同block stride。前提是一个global block ID同一时刻只归一个group；规划函数本身不是执行期所有权锁。不同活跃group不能同时占同一ID，也不能为每组改成互不一致的block stride后仍沿用相同ID算术。

页对齐取PHYSICAL_STRIDE_ALIGNMENT=256与各dtype/scale对齐的最小公倍数；含C4紧凑行时还纳入258，所以对应对齐量为33024字节。组内payload、页尾padding和共同stride分别记账，不能直接用logical numel作为相邻block地址距离。没有C4的组仍按实际spec算对齐，不强行套一个常量到所有rank。

capacity先取available_memory//pool_bytes_per_block，再交`may_override_num_blocks`；最终override不由这个除法证明仍在预算内。descriptor携带byte offset、layer_stride=0与共同block_stride，每条size可写整份backing成本，不能逐条相加当作实际已分配HBM。Native allocator如何实现共用backing及非连续view仍需实际接通。vLLM精确0.32.0从kv_cache_utils导入override helper，其他lane从kv_cache_planning导入；该分支不证明任意新版兼容。

每请求需求按各group的max_memory_usage_pages求和，再乘物理池每block字节。隔离C4 payload时1024/258的比值不能当整个模型容量增益：state精度/padding、非C4页、池slack、调度需求和其他显存都在总量中。容量UT使用合成PageSpec与CPU公式，packing UT定义跨block不别名；它们没有测量真实模型并发容量、NPU带宽或吞吐。

## 新模型接入的停止条件与后续缺口

先保存实际recipe/method、P/D角色、每层KV dtype、尺度原始key/编码/shape、rank切片、backend类、spec、descriptor及真实view stride。逐层核对数值单位：FP8 payload、E8M0原字节、浮点reciprocal和TQ code/scale分别由正确消费者读取。缺少匹配backend、权重或布局时恢复已验证完整KV格式，不吞apply拒绝、不截断尺度、不删除配置门禁。

随后比较浮点参考与量化输出，覆盖GQA复制、零尺度、partial/空/PAD、不同物理block、hybrid页复用以及捕获前后地址。正确性和隔离通过后再测可用block、峰值HBM、每步分配/转换、TTFT/TPOT和吞吐，保留质量指标及校准数据身份。

后续重点是外部FIA/QFA的实际ABI与数值、PD全部四组件的注册/传输/退役，以及paired版本在真实硬件上的capture和并发一致性。本卡已补Host后端、MRv2页视图与定点K-scale kernel，仍不把类安装、默认尺度、测试名称或压缩比写成设备验收结果。

## V1 PD：四组件地址、字节跨度与失败完成

本节仅接通Main固定版本的MooncakeConnectorV1 Host路径，不把它推广为V2、Hybrid、Layerwise或任意MultiConnector均支持MXFP8。`uses_mooncake_connector`递归查看dict/list/tuple及对象extra config，只要发现MooncakeConnector、MooncakeConnectorV1或MooncakeConnectorV2任一名称便为真；注册表另有MooncakePullConnector等名字。这个布尔检查既不协商四组件格式，也不验证MultiConnector其余child，不可通过随意重命名配置来代替真实路由与消费者核验。

V1的`register_kv_caches`对tuple/list保留全部组件；MRv1特殊的五维双K/V tensor才unbind第0维。每层按cache_idx分别保存view自己的data_ptr、每块logical payload字节、stride(0)字节及kernel/logical块比例。普通Attention注册再按共享storage合并实际view接触跨度，包含storage offset和strided间隙；合并范围只交注册引擎，握手metadata仍保留逐组件地址。不能把物理顺序[K|Ks|V|Vs]误当tuple顺序(K,V,Ks,Vs)，也不能用注册区起点替换每个组件的传输起点。

接收线程按local组件数量逐项索引远端同一cache_idx，使用本地block payload长度和两端独立block stride生成READ描述符。连续block ID只有在两端相邻地址距离均等于实际传输长度时才能合并；有页padding或分量交错时会重新拆分，不能以logical numel跨过其他组件或未选页。所读片段没有按组件名称、dtype/scale编码进行协议协商，也不构成所有两端几何均已校验；P/D必须事先一致地约定组件数量/顺序、scale位模式、head/TP分片、page/kernel比例和各自stride，重建view或backing后重新核对注册与握手身份。

READ非负返回之后，只有group-transfer-end项才暂存reformat，待本地请求全部pull task完成才应用。非对称TP/GQA和enable_kv_nz可能进入后处理，而所读reformat方法仍有只解包(K,V)的接口，不能将四组件tuple机械送入；唯一明确跳过的特定group检查是SFA Indexer，并非通用MXFP8免转换协议。应确认实际所走分支具备四组件合同，不通过删除门禁、任意关闭布局选项或只传前两个组件来制造成功。

`_handle_request`捕获传输或reformat异常，记录failed request/invalid block并排空本地任务；finally仍发送远端done通知用于源资源清理。因而收到ACK、finished_recving或P端释放，不等价于所有四组件成功且D可推理。消费端必须同时检查failed_recving与错误块，确认全部本地写入和必要转换结束，再交给对应的重算/回退策略；notification-only请求还可不报告WAITING_FOR_REMOTE_KVS完成。HTTP完成和单个shard完成不能替代这些条件。

GlobalTE的地址列表不持有tensor所有权；已注册标志为True时再次register不会自动替换新地址。注册中途失败、Sleep注销/重注册与真实backing寿命继续按[Sleep/Wake合同](vllm_ascend_sleep_wakeup_lifecycle.md)取证，通用Pull/Push/D2RH释放时序见[PD传输合同](vllm_ascend_pd_transfer_lifecycle.md)。不要把本节的V1字节READ边界当所有SDK、跨流或P/D并发安全已经通过。

新增有界UT阅读定义了不同P/D block stride、block-major双K/V view、未选页保持和注册metadata的CPU/mock断言；这些例子的组件数是2，不是MXFP8四组件真机或非对称TP验收。未运行这些测试、网络、SDK或NPU。验收时须额外记录四组件逐页校验、PAD/null块与共享请求隔离、故障后的错误块传播及实际恢复路径，再测传输字节与端到端性能。
