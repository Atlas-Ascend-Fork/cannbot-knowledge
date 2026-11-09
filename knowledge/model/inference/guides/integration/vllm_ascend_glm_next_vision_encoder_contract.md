---
type: Guide
title: vLLM Ascend GLM-Next视觉编码器：数值条件、空间合并与图元数据
description: 接入GLM-Next视觉tower时保留Conv3D patch布局、q/k RMSNorm、clamped SwiGLU、二维RoPE与合并权重，核对encoder元数据和真实多模态验收边界。
aliases:
- GLM-Next视觉编码器
- Glm5NextVisionTransformer
- Glm5NextVisionAttention
- Glm5NextPatchMerger
tags:
- task.implementation
- topic.multimodal
- topic.model_adaptation
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/multimodal.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/processor.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/model.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_loader_compat.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/multimodal.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/processor_config.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_glm5_3_flash.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_video_placeholders.py
  role: evidence
created_at: '2026-10-31T10:22:36Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T10:29:33Z'
---

# vLLM Ascend GLM-Next视觉编码器：数值条件、空间合并与图元数据

## 消费任务与固定证据

为GLM-Next适配视觉tower、替换attention/norm或接入encoder graph元数据时，沿pixel patch→Conv3D→视觉block→空间合并→语言hidden维度核对。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，multimodal.py810和processor.py889全文；四卡测试196及processor/模型JSON28/31全文，整模1114和loader UT47复用同SHA全文。

这些文件只作数据，没有执行torch/transformers、模型、权重加载、UT、NPU/CANN或图捕获。Native MMEncoderAttention、fused_q_kv_rmsnorm、RoPE与权重loader没有由本卡闭合；整项平台未知，保持draft/空平台。版本身份沿[框架入口](../../concepts/frameworks/vllm_ascend.md)，注册image/video接口不证明所有模型/硬件支持。

[媒体processor](vllm_ascend_glm_next_media_processor_contract.md)负责像素画布、采样、grid和prompt；[整模接入](vllm_ascend_glm_next_model_loading_contract.md)负责PP/mHC/文本checkpoint；本卡不替代这些来源拥有者。[V4.1视觉接入](vllm_ascend_v41_vision_adapter.md)的Linear patch、学习delimiter和Runner有效行协议不直接搬到当前GLM。

## Conv3D必须与processor排列一致

Glm5NextVisionPatchEmbed将展平patch行reshape为[-1,C,temporal_patch_size,patch_size,patch_size]，输入转patch weight的device/dtype，再用kernel=stride=(temporalP,patch,patch)的Conv3D提取embedding。默认构造值不等于所有checkpoint尺寸，processor的merge-block优先排列、展平行宽和grid必须逐一匹配。

原图像素token预算不等于视觉encoder的patch行数或合并后的语言token数。空间合并需网格整除merge_size，时间patch不能借文本KPool的pool_size替代；异常shape、空输入和超大网格仍需完整父实现/实际配置验证。

## 视觉并行和attention布局

is_vit_use_data_parallel()返回True时vision设TPsize1/rank0，否则取实际TP group；配置到该helper的完整解析另验。head数/每partition维度交Native divide；当前parent调用projection_size=embed_dim。不能因签名允许两个维度就认定任意不等维度已适配，也不能把vision DP选择直接当文本SP/MoE路由。

QKVParallelLinear与输出RowParallelLinear均带bias，量化相关prefix分别使用qkv_proj或qkv。split_qkv按本地head拆成q/k/v；后续MMEncoderAttention是视觉双向序列接口，不能复用文本MLA/KDA cache合同。

q/k分别持有RMSNorm权重，eps明确1e-5；fused_q_kv_rmsnorm在展平head向量上处理q/k并保留v。来源注释的FP32 bit-identical目标不是实测精度结论，底层融合函数和NPU算子需独立核对。

随后将q/k按batch拼接调用ApplyRotaryEmb，再拆回，接MMEncoderAttention、reshape与RowParallel输出。实际传入形状、TP shard和位置行号一并验证；不能只比模块名字或最后shape。

## norm eps与SwiGLU clamp逐层保留

实际VisionTransformer传入partial(RMSNorm,eps=norm_eps)；VisionBlock签名的默认nn.LayerNorm分支没有由当前调用证明兼容带residual参数的norm2。执行为norm1→attention，再norm2(x,residual=x_attn)，MLP后返回residual+MLP。

block MLP使用gate/up融合、SiluAndMulWithClamp和down projection；merger的gate/up也使用同一类clamp。clamp_limit先从vision_config读，不在时从text config取，并assert非None。GLM-5.3-Flash与其他GLM视觉结构不可仅凭家族名互换。

整模包装显式传vision_config.rms_norm_eps，vision quant_config=None并使用BF16路径，避免将文本eps和全局FP8策略机械传播。来源注释描述的真实checkpoint视觉eps1e-6与四卡JSON fixture的1e-5不同；不要把某一数字写成所有权重的固定值或本批复现的NaN结论。

post_layernorm使用vision_config.rms_norm_eps；PatchMerger内部LayerNorm未显式指定eps。这些norm的类型、参数来源和精度分别记录，不能统一改为一个“全局norm epsilon”。

## 二维位置与空间合并

Transformer按vision_config.depth构造block，RoPE用head_dim、max_position8192、is_neox_style=True和partial_rotary_factor0.5。这里不构造绝对pos embedding或post-conv norm；具体Native RoPE/cache行为与8192边界不由局部构造闭合。

rot_pos_emb为每图/时间patch生成H/W坐标，按merge-block优先重排并重复T次；按最大空间grid取cos/sin，将位置索引non_blocking搬至cos所在设备，组合并展平两个轴。重复视频帧与grid行顺序须对应，不能把时间帧索引直接替代空间RoPE。

视觉block结束先post_layernorm，再将空间merge块组织回Conv2D输入，kernel=stride=spatial_merge_size，输出out_hidden_size。PatchMerger随后走ColumnParallel且gather_output、LayerNorm、GELU、clamped gate/up和RowParallel，映射至语言模型hidden维度；不是简单丢弃多余patch行。

## checkpoint映射与量化边界

Glm5NextVisionTransformer.hf_to_vllm_mapper将q/k/v projection映射到qkv并传q/k/v shard，将gate/up映射到gate_up的0/1 shard。load_weights交Native AutoWeightsLoader处理mapper；当前局部读取不能证明所有quant格式、shard packing、缺项或PP过滤已验。

条件生成包装的hf_to_vllm_mapper将model.visual归到visual命名空间，顶层rot.*的load-local跳过与nested rot保留沿整模加载合同。loader UT用CPU假参数和quant开关检查这些映射，不进行真实vision数值或checkpoint覆盖验收；出现loaded参数名也不证明所有融合分片齐全。

## encoder元数据与图路径

prepare_encoder_metadata按每个grid的H×W、重复T生成每时间patch的序列长度，经NumPy int32累加得到cu_seqlens；优先按max_frames_per_batch、否则max_batch_size补最后一个累计终点，不会因实际数超上限就自动截短。五个字段为rotary_pos_emb_cos、rotary_pos_emb_sin、sequence_lengths、max_seqlen和cu_seqlens；后者还经Native maybe_recompute_cu_seqlens按backend/hidden/TP处理，不保证最终张量逐字等于NumPy前缀和。

max_seqlen_override非None时直接选其值，否则调用Native MMEncoderAttention.compute_max_seqlen；随后用torch.tensor创建max_seqlen而没有显式device。不能忽略全局默认device就断言一定CPU，也不能把提供override当作已校验真实最大长度。图buffer的device/dtype、有效长度和容量须按真实runner/backend验证；sequence_lengths虽在准备时返回，在本地VisionTransformer.forward并不直接读取。

有encoder_metadata时forward直接取cos/sin/cu_seqlens/max_seqlen，跳过本地CPU网格重建；无metadata的eager路径重算位置和cu_seqlens，只在FLASH_ATTN/ROCM_AITER_FA/TRITON_ATTN等分支构造所需max Tensor。get_vit_attn_backend接收torch.get_default_dtype()，不能据patch weight dtype替它推backend。

model包装的encoder graph config只从parent buffer_keys移除pos_embeds。源码关于CUDA graph capture的说明、提前算好cos/sin或重复cu终点，不证明NPU capture/replay、父buffer容量、混图/空闲批和所有注意力backend均安全。

这些是encoder输入元数据，不是RecoverSSM accepted-state，也不是[ECCPU缓存](vllm_ascend_encoder_cache_offload.md)的注册内存/传输完成记录。命中encoder cache与重算vision需要分别观测，不能把减少CPU元数据开销写成已测NPU吞吐提升。

## 来源测试能证明什么

四卡测试用local DummyLoader构建synthetic生产宽度模型，9层中7KDA/2MLA，加1MTP，K5/out16、MRv2、TP4+EP、PCP1/DCP1和graph/eager×RecoverSSM配置；实际image0/video0、只传文本token IDs。构造了vision模块不等于跑过视觉forward，更没有真实checkpoint、C8数值、视频精度或有意义的投机接受率。

multimodal JSON的vision eps1e-5和processor JSON的视频240000上界都属于fixture；实际from_pretrained的条件cap、真实模型eps来源、权重身份分别验。视频UT覆盖CPU采样/placeholder，没有验证MMEncoderAttention、Conv3D、CANN或图捕获。本批所有用例只读未运行。

## Agent交付与性能验证

交付实际vision/text config、patch/merge/temporal、pixel/grid/输出token数、逐norm eps/dtype、clamp来源、TP/DP布局、checkpoint key→shard以及encoder五字段的device/shape/容量。先固定处理器与真实权重，对比reference的像素、patch顺序和逐层值，再测单图/多图/视频、混batch、空输入、eager与graph。

在目标设备验证元数据预计算/复用、不同frame/分辨率桶、并发请求与父runner buffer生命周期，确认再拆分CPU预处理、encoder kernel、合并/prefill的耗时、HBM和通信。当前没有NPU/性能/Agent A/B结果；失败恢复完整已验证的配置与权重，不删位置字段、混用文本norm或只靠padding掩盖长度差异。
