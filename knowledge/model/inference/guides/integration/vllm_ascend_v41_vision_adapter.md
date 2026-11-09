---
type: Guide
title: vLLM Ascend V4.1 视觉接入：图像 span、二维 RoPE 与补齐行接口
description: 适配V4.1图像时核对sentinel与角色span、resize预算、ViT/aligner、delimiter权重，以及MRv2有效行与图补齐行的分工；按固定Native版本保留ABI边界。 追踪num_tokens_after_padding从模型state传至vocab embedding，区分有效行、补齐行与idle批。
aliases:
- get_vision_cos_sin
- DeepseekV41Aligner
- _build_image_span
- image_token_types
- num_image_tokens
- V41视觉接入
- V4.1 num_tokens_after_padding 有效行与补齐行
tags:
- task.implementation
- topic.multimodal
- topic.model_adaptation
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/vision.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/vl_model.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_vision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_registration.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/default.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/deepseek_v41/common/mm_preprocess.py
  role: implementation
created_at: '2026-10-31T06:48:03Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T07:02:12Z'
---

# vLLM Ascend V4.1 视觉接入：图像 span、二维 RoPE 与补齐行接口

## 消费任务与固定版本

新模型接入图像encoder、替换processor或排查图文混batch静默精度错误时，按原始token→图像resize/patch→ViT/aligner→角色span→MM merge→Runner实际与补齐行核对。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，vision.py127、VL包装器336及视觉/注册UT全文；utils只读normalize_deepseek_v41_config，MRv2状态只读prepare_inputs_embeds。所有源码/测试作数据读取，未导入、运行PIL/torch处理、测试、模型或NPU，硬件整项证据未知，保持draft/空平台。

原生mm_preprocess.py376行来自独立Native5df63a7203cdb9328d824a27b682e77c7b9928be；单个Git blob取回并核对OID、全文读取，不等于Main配对544f182d9f0c9bfe8bd7645525951d5e3692a542的ABI已经验证。下文按这个Native版本说明processor；MMEncoderAttention、ApplyRotaryEmb、RMSNorm、merge/EncoderRunner父实现及checkpoint外部参考仍各有边界。[模型部署](../models/vllm_ascend_deepseek_v41_platform_boundary.md)的A2/A3教程不是本卡所有路径的实测。

## token ID与角色不是同一坐标

Native定义IMAGE_START/IMAGE/IMAGE_NEW_LINE/IMAGE_END为0/1/2/3，是types里的角色；每个图像span位置在input_ids都放同一个129264。validate_image_sentinel_ids要求tokenizer的IMAGE_PLACEHOLDER恰映射该ID，不允许自行分配四种delimiter token ID。image_sentinel_mask只识别精确base ID，注释所述MoE routing的base到base+5范围不能直接替换此谓词。

image_token_types按阅读顺序生成start + 每行W个IMAGE和一个newline + end，num_image_tokens=H×(W+1)+2。2×3网格是10个位置，不是6个视觉向量；IMAGE接aligner输出，三类delimiter接学习参数。当前Native明确没有compressor-alignment padding，不能把旧V4排列或“pad到compressor block”的经验带入。

normalize_deepseek_v41_config将image_sentinel_base_id设为image_token_id或缺省129264，image_pad_token_id=base+1，但不在此函数验证tokenizer。Native processor固定base检查与允许自定义config值不能不经核对拼成保证兼容；来源UT留有alignment pad命名与旧注释，实际当前输出没有该额外role，也没有image_pad参数。Engram同时排除image和image_pad ID，见[Engram历史](vllm_ascend_engram_model_adapter.md)。

## processor输出与预算的接入面

独立[图像预处理合同](vllm_ascend_v41_image_processor.md)拥有llm_grid、solve_resize_ratio、safe_resize、load_image、dummy预算与多图字段的具体算法。接入侧保存像素/ViT/LLM三坐标和H×(W+1)+2的span长度；预算包含newline和首尾delimiter，极宽/极高分别可能收为单行/单列。不要只按H×W或图像面积预留token。

processor将RGB归一化到BF16、按阅读顺序打patch，宽图resize、其余gray127 pad；patch先整除后按downsample向上取整，aligner不能丢边缘。DeepseekV4VLProcessor的多图patches/types分别按ViT与LLM grid切分，空images返回空BatchFeature；其text签名不等于执行tokenization。各字段的dtype、CPU保留、flat sizes、PromptReplacement对placeholder的展开及校验依processor合同逐项核对。

dummy按含newline的预算最大化ViT patch面积，使用min_pixels的等比策略，不能只选最大图像面积或将该输入当所有运行峰值。它属于processor规划，不代表模型已通过PIL/reference对照或capture验收。

## ViT、二维RoPE与空间合并

DeepseekV41PatchEmbed把每patch的3×patch_size²展平送Linear。get_vision_cos_sin以CPU FP32二维坐标和inv_freq生成cos/sin，lru_cache容量8；进入ViT后.to实际x.device。CPU缓存命中不能当NPU buffer地址永久不变或没有H2D。

VisionAttention将wqkv拆成[N,heads,head_dim]，stack q/k后ApplyRotaryEmb使用NeoX风格、启用FP32计算，接batch1的MMEncoderAttention，再wo。完整图像双向attention与文本causal/CSA/SWA路径分开；局部构造未给出所有head整除/维度/shape异常的完整schema。ViT每block是RMSNorm→attention残差→RMSNorm→SiluAndMul MLP残差，最后norm。

norm构造dtype FP32、eps1e-6，外层随后可对整个vision模块.to(model_config.dtype)，不能由构造参数推断最终所有权重始终FP32。Aligner将[N,C]还原H×W，转C/H/W，右与下按(-extent)%r补齐，再unfold r×r、stride r，Linear→GELU→Linear映射hidden_size。输出格子是ceil(H/r)×ceil(W/r)，不能丢掉不足整组的边缘。

## 包装器、图像关闭与权重加载

实际注册对象AscendDeepseekV41ForCausalLM是VL wrapper，并通过requires_raw_input_tokens=True声明原始token输入。vision_n_layers>0时先设置is_mm_prefix_lm与mm_prefix_clamp_sliding_window；构造tower还要求image limit>0。image=0关闭tower不自动清除前面config flags。启用时创建vision、aligner和image_start/end/newline三个学习参数，不创建image_pad。

_parse_and_validate_image_input只提取patches、vit_grid、llm_grid、types，不是完整dtype/shape/role检查器。_process_image_input按aligner dtype转换patches，strict zip两种grid，分别推进ViT offset和span offset；它没有在该方法穷尽检查所有尾部数据是否被消费。_build_image_span按四类已知role赋值；未知role可能留下new_empty位置，须由processor/调用方约束，不当已复现缺陷或自行把未知值清零来隐藏格式错。

embed_input_ids先用语言模型对原始IDs取embedding，非空multimodal_embeddings再交Native merge；input_ids与types、MM mask及aligner rows须逐位置一致。_vision_parameter_name去掉可选model.前缀，识别vision./aligner./image_。text-only tower=None时跳过这类checkpoint权重；启用tower则缺必要参数不能静默忽略。返回loaded集合为语言权重加language_model.命名空间，后处理可选转发LLM hook，不证明所有视觉量化格式受支持。

## MRv2实际行、图补齐与生命周期

AscendModelState.prepare_inputs_embeds在父类截取有效本地IDs之前，通过可选set_embedding_num_tokens_padded发布本批num_tokens_after_padding；wrapper一路转发到真实vocab embedding。每批覆盖，包括idle。实际MM fusion只消费valid rows，而Runner返回/通信buffer可保持padded shape；不能用图桶长度扩大MM mask或让上一批的有效长度泄漏。

视觉UT的CPU定义保留state→wrapper→LLM→vocab与持久EncoderRunner buffer链，步骤(实际/补齐)为3/5、1/2、0/0，检查第二步替换首图、idle不继承、底层地址不变；image encoding/cache选择被mock，Native gather也被替换。该用例是验收设计，未由本批执行，不能证明真实PCP通信、NPU图捕获或完整父方法。通用非连续position问题另见[PCP多模态错位](../../runbooks/precision/pcp_multimodal_noncontiguous_position.md)，不要将其旧Runner workaround机械搬到当前MRv2。

## Agent验收与回退

保存checkpoint/tokenizer/config/processor版本及配对身份；先验证RGB变换、极宽/极高/非整除网格、单图/多图/空图、每图patch与角色长度和delimiter位置，再比关闭图与eager基线。随后加入actual/padded行变化、请求重用、idle、图桶切换、PCP和原始token的Engram死行。84×42、patch14/downsample3的UT参考为ViT3×6、LLM1×2、5个span位置、无perm；它是固定CPU测试定义，不是所有输入的硬编码尺寸。

UT含Native config importorskip、CPU fixture和mock encoder/merge；注册测试只收集架构名，不实例化模型。全部依赖与真实设备数值通过后，再按图数/分辨率/并发分解TTFT里的预处理、encoder、merge和prefill，记录峰值HBM/host与capture工作区。失败恢复匹配checkpoint与完整processor配置，停止新增并行/图组合；不改sentinel、截断types、忽略权重或丢边缘patch来凑形状。
