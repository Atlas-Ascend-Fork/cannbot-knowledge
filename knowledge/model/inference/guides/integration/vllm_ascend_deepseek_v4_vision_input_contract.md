---
type: Guide
title: vLLM Ascend DeepSeek-V4 视觉接入：五类 sentinel、压缩对齐与嵌入契约
description: 适配 DeepSeek-V4 VisionExp 的图像预处理、N-layout 与 perm、多图字段、prompt 对齐、ViT/aligner 和学习 delimiter；显式保留独立 Native 快照的私有接口差异及未知硬件边界。
aliases:
- DeepSeek V4 VisionExp
- AscendDeepseekV4ForConditionalGeneration
- DeepseekV4VLMultiModalProcessor
- build_image_block_pad_free
- IMAGE_SENTINEL_TOKEN_NAMES
- _get_thread_local_tokenizer
- _call_hf_processor
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/vl_model.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/mm_preprocess.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/vision.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/multimodal/processing/processor.py
  role: primary
created_at: '2026-10-31T20:30:25Z'
updated_at: '2026-10-31T20:30:25Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DeepSeek-V4 视觉接入：五类 sentinel、压缩对齐与嵌入契约

## 任务、版本与适用范围

新模型接入需要同时对齐图像 token、视觉特征顺序、压缩器位置和模型嵌入入口。这里描述 Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2 的 DeepSeek-V4 VisionExp 实现；主类为 AscendDeepseekV4ForConditionalGeneration。模型注册表把相关架构接入插件，不能据此认定 checkpoint、tokenizer、私有 Native API 和任意硬件已经兼容。视觉整项硬件范围缺少独立依据，保留 draft 与空平台，不借用 DeepSeek-V4 Flash/Pro 文本部署的产品支持范围。

Main 配对 Native 是 544f182d9f0c9bfe8bd7645525951d5e3692a542；本卡用于对照的独立 Native 为 5df63a7203cdb9328d824a27b682e77c7b9928be。下面的签名差异是真实源码观察，尚未运行重现，也不代表已读取配对 544 的相同接口。config 导入还按 vllm_version_is("0.32.0") 在 Native DeepseekV4Config 与 Transformers 路径之间选择，版本号分支不能替代接口逐项核对。

V4.1 使用另一套协议，见 [V4.1 图像 processor](vllm_ascend_v41_image_processor.md) 和 [V4.1 视觉接入](vllm_ascend_v41_vision_adapter.md)。V4.1 的单一重复 ID、独立角色张量、无旧版 compress pad/perm 约定不能直接迁到这里。

## 五种 ID 与线程内 tokenizer

IMAGE_SENTINEL_BASE_ID 为 129257。IMAGE_SENTINEL_TOKEN_NAMES 对应 place_holder_mm_span_0431 到 0435，validate_image_sentinel_ids 要求 tokenizer 将它们映射为连续的 base+i；只检查 placeholder 非 None 不足以替代该一致性检查。图像占位文本为 `<｜deepseek_image｜>`。

| 类型值 | 名称 | token ID | 嵌入用途 |
|---|---|---|---|
| 0 | IMAGE_START | 129257 | 学习的 image_start |
| 1 | IMAGE_PAD | 129258 | 学习的 image_pad |
| 2 | IMAGE | 129259 | 后续由视觉特征替换 |
| 3 | IMAGE_NEW_LINE | 129260 | 学习的 image_new_line |
| 4 | IMAGE_END | 129261 | 学习的 image_end |

image_sentinel_mask 按 `[base,base+5)` 覆盖五种 ID；PromptUpdateDetails.select_token_id 只选择 IMAGE 的 base+2 接收视觉 embedding。不能把“sentinel 范围”与“视觉向量替换位置”混为同一 mask。

_get_thread_local_tokenizer 对原 tokenizer 作 deepcopy，每个线程缓存一份，并用 source_id=id(original) 判断是否重建。它避免在线程之间共享 fast tokenizer 可变的 truncation/padding 状态；不是已执行的并发正确性或吞吐实验，原对象内容原地变化也不是该缓存键的一部分。

## resize 预算、三种坐标与像素顺序

先区分像素 Hpx/Wpx、ViT 网格 Hvit=Hpx//patch_size、Wvit，以及 LLM 网格 H=ceil(Hvit/downsample_ratio)、W=ceil(Wvit/downsample_ratio)。num_image_tokens 的 pad-free 长度为 `H*(W+1)+2`，H 为奇数时另加一行 `W+1`，再加 `((H+1)//2*(W+1)%2)*2` 个尾部 pad。newline、补齐行和尾 pad 都计入 span，不能以 H*W 代替。

safe_resize 先从 max_n_token 保留 3 个 alignment token。若实际网格超过预算，循环调用 solve_resize_ratio 并递减求解预算，然后重新计算实际 token 数。solve_resize_ratio 令 ratio=height/width，max_w=sqrt((budget-2)/ratio+.25)-.5，max_h=max_w*ratio；宽不足一格时取单列、把可用行数向下调成偶数，高不足两格时取两行并要求剩余宽大于一。普通分支分别取 floor，并把行数调成偶数，再选缩放比并向下取 patch 倍数。该过程与 V4.1 的单行退化分支不同。

load_image 转 RGB，按 max_wh_ratio 限制过宽目标，低于 min_pixels 时按面积平方根放大，随后向上取 patch 倍数，再进入预算收敛。原图宽达到 max_wh_ratio*原高时使用 resize，其他分支使用 ImageOps.pad、填色 (127,127,127)。外部 PIL 的具体插值行为需要随依赖版本留证，不能由本卡补造。

像素按 NumPy FP32→CHW→除 255→(x-.5)/.5→BF16 处理。reshape(3,Hvit,p,Wvit,p) 后 permute(1,3,0,2,4)，输出 `[Hvit*Wvit,3,p,p]`。宽高、通道和 patch 内部顺序都要核对，只比 shape 会漏掉图像内容重排。非正尺寸、极小预算、零 patch/downsample 等没有完整的用户输入恢复协议，接入层应先验证配置。

## N-layout、perm 与位置相关的 compress pad

build_image_block(H,W,start_pos) 的前置 compress_pad 是 `3-start_pos%4`，用于 COMPRESS_PAD_TO=4 的位置对齐。真实图像行含 W 个 IMAGE 和一个 newline；行数补成 H+H%2，补出的整行用 IMAGE_PAD。两行一组的索引先 view(rows//2,2,W+1)，再交换行内/行维并展平，形成两行交错的 N-layout。另按 rows//2*(W+1) 的奇偶性补 0 或 2 个尾 pad。

types 顺序为 compress pad、START、交错后的行、尾 pad、END。image_idx 只给真实 IMAGE 格子编号，其他位置为 -1；perm 是 image_idx 按相同 order 重排后过滤非负值的结果，长度严格为 H*W。不要把 newline/pad 索引送进 aligner 特征，也不要只重排 types 而保留原图像特征顺序。

build_image_block_pad_free 以 start_pos=3 消除前置 compress pad，供 processor 独立构建每图信息。真正插入到 prompt 后，由当前位置重新计算 pad；pad-free token 数和最终序列长度不是同一统计口径。

## 多图字段、prompt 替换与 Native 边界

DeepseekV4VLProcessor 逐图生成并拼接五类字段：patches 按 Hvit*Wvit 切，vit_grid 与 llm_grid 为 `[num_images,2]` INT64，perm 按 H*W 切，types 按包含奇数行/尾 pad 的 pad-free 长度切。vit_grid、llm_grid 和 types 保留 CPU。空图像返回空 BatchFeature；ProcessingInfo 拒绝非空额外 kwargs。image=None 的 supported limit 只是 processor 声明，服务侧仍需限制实际媒体数量。

DeepseekV4VLMultiModalProcessor._call_hf_processor 接收 prompt、mm_data、mm_kwargs、tok_kwargs，先处理 images，再用线程内 tokenizer 处理 prompt。_hf_processor_applies_updates 返回 False；_get_prompt_updates 验证五种 ID，用 base+types 替换单个占位符，只有 IMAGE 对应位置标为多模态嵌入。

_apply_prompt_updates 先调用父类，再按 placeholder 顺序插入位置相关的前置 pad：每次使用当前 start，更新后续 offset，在当前 is_embed 前补 False，并重建 PlaceholderFeaturesInfo；非 image span 只随已有插入量移动。多图时必须核对每次插入后的绝对 start、span 长度、视觉位置 mask 和后续文本位置。

独立 Native processor.py 的 1287–1335 行把 _call_hf_processor 定义为 `(hf_data,hf_kwargs)`，调用方也传两个字典；Main override 需要四个参数。若该调用路径直接分派到此 override，会产生参数契约不匹配，这是静态推导，尚未执行。Native 1690–1756 行的 _apply_prompt_updates 接受 token_ids/mm_prompt_updates，包含 token 匹配和可能的解码文本回退；Main 的旧版本注释或 _hf_processor_applies_updates 不能证明当前 Native 一定调用该 hook。适配前须在实际版本核对父类调用链，不能把两个独立固定提交组合成已验收运行环境。

get_mm_max_tokens_per_item 返回 vision_max_n_token+3 的保守上界，不等于每图实际 span。dummy 输入按预算减 3 求尺寸，来源用正方形估计；本卡不将该注释提升为所有纵横比的数学最大值证明。

## ViT、aligner 与视觉位置

vision.py 的实现为普通 Torch replicated ViT/aligner，没有实现视觉 TP/DP 分片。patch embedder 是 Linear(3*p*p,vision_dim)。get_vision_cos_sin 以 lru_cache(maxsize=8) 缓存 CPU FP32 网格频率，运行时转到 x.device；RoPE 先转 FP32，按最后维度两半旋转后还原原 dtype。RMSNorm 在 FP32 求平方均值、rsqrt(eps=1e-6)，再还原输入 dtype，外层 module.to(model_dtype) 仍可能转换其参数 dtype。

attention 将 wqkv 拆成 q/k/v，按 heads/head_dim reshape，q/k 做 RoPE；F.scaled_dot_product_attention 对每图完整 token 维计算，再经 wo。MLP 的 w1 同时产生 gate/up，Silu(gate)*up 后经 w2，两处均配 pre-norm/residual。这里没有 V4.1 的 AscendMMEncoderAttention 私有 scratch/ApplyRotaryEmb 契约。

aligner 把特征还原 C/H/W，在右侧和下侧按 `(-W)%r`、`(-H)%r` 补齐，unfold r*r、stride=r，经 Linear→GELU→Linear 输出 ceil 网格。vl_model 对每图分别推进 ViT offset 与 LLM offset，把 patches 转为 aligner.w1 的 dtype，再将该图 perm 移到特征 device 后索引输出。strict zip、两种 offset 和 perm 的取值范围共同决定多图是否错位。

## 学习 delimiter、raw IDs 与权重加载

vision_n_layers>0 时设置 mm_prefix_clamp_sliding_window=True 和 leading_pad_modulus=4；实际 image_enabled 还要求 image limit>0。image 关闭时视觉模块和四种学习参数为 None，但不能推导前面已写入的配置标志自动清除。类声明 requires_raw_input_tokens=True，并委托语言模型的中间张量、logits、专家与辅助接口。

sentinel 表按 `[start,pad,pad,newline,end]` 堆叠，匹配当前 embedding 的 dtype/device 后 detach 缓存。IMAGE 槽先占用 pad 向量，之后由多模态合并替换。该表是普通属性，不能靠 Module.to 自动迁移，因此 dtype/device 变化会重建；缓存键不包含权重值，权重原地重载后的失效需要另外检查。

embed_input_ids 先查语言词嵌入，再用五类 sentinel mask 和 clamp 后的索引通过 torch.where(out=inputs_embeds) 写回学习向量。无多模态特征时返回该结果；有特征时还必须提供 is_multimodal，随后进入 Native 合并接口。输入 parser 看到 patches 才要求其余 grid/perm，但没有实现完整的形状、dtype 和所有字段一致性校验。

load_weights 去掉可选 model. 前缀后区分 vision/aligner/image_ 权重，用参数自己的 loader 或 default loader；未知视觉参数会触发 KeyError，其余交给 language_model 并合并已加载名称。不能照搬 V4.1 在关闭图像时跳过全部视觉权重的规则。process_weights_after_loading 的语言模型 hook 也不等于显式清理 sentinel 缓存。

## Agent 的验证次序与证据

先核对实际 Native 调用签名与 tokenizer 五个 ID，再用普通、极宽、极高、奇数行、非整除边缘、多图、空图及位置 start%4=0..3 的样本检查 resize、types、perm、patch/grid 分段和最终 prompt offset。逐图核对 aligner 行数、真实视觉位置和 delimiter 向量；覆盖 image limit=0、权重重载和 dtype/device 迁移。接口不匹配时先回到明确配对的依赖环境，保留原始版本和失败位置，不以关闭校验掩盖 token/特征错位。

上述步骤是待执行验证方案。本次仅把 mm_preprocess.py 全文 549 行、vision.py 全文 132 行、vl_model.py 全文 297 行和注册表作为固定源码数据阅读，并对照 Native processor.py 的注明范围；未导入上游模块，未执行模型、UT、编译、NPU、精度或性能实验。其他 Native helper、实际 checkpoint、全部硬件模式和完整图捕获闭包仍需独立证据。
