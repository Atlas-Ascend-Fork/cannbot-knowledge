---
type: Guide
title: vLLM Ascend V4.1 图像预处理：sentinel、resize预算与多图字段
description: 按固定Native实现适配V4.1图像processor，核对token ID与角色span、resize和dummy预算、RGB patch顺序、多图字段切分及prompt替换，避免token预算和模型输入错位。
aliases:
- DeepseekV4VLProcessor
- DeepseekV4VLMultiModalProcessor
- solve_resize_ratio
- safe_resize
- load_image
- V41图像预处理
tags:
- task.implementation
- topic.multimodal
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/deepseek_v41/common/mm_preprocess.py
  role: primary
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

# vLLM Ascend V4.1 图像预处理：sentinel、resize预算与多图字段

## 消费任务与来源身份

为V4.1适配新媒体入口、替换图像processor或定位图像token预算/字段切分错误时，先固定tokenizer、图像变换、span角色与模型消费接口。本卡主来源为原生vLLM 5df63a7203cdb9328d824a27b682e77c7b9928be的vllm/models/deepseek_v41/common/mm_preprocess.py全文376行，Git blob017f5f87a2b493542fc83080e5518fa124b60c6c已按实际bytes核对，全部只作数据阅读。没有导入torch/PIL/transformers或运行processor、UT、模型与NPU，整项硬件未知，保持draft/空平台。

Ascend ceac版本配对Native为544f182d9f0c9bfe8bd7645525951d5e3692a542，不能把独立5df的源合同当作配对ABI已经验证。来源称变换从官方reference image_processor移植并保持token数量，不等于本次取得reference逐字对照或运行bit-match。Ascend的ViT、aligner、delimiter权重和MRv2补齐行另由[视觉接入指南](vllm_ascend_v41_vision_adapter.md)消费；通用旧Runner非连续位置经验见[PCP多模态错位](../../runbooks/precision/pcp_multimodal_noncontiguous_position.md)。

## tokenizer ID、role与span长度

IMAGE_PLACEHOLDER为特殊图像占位符，IMAGE_SENTINEL_BASE_ID固定129264。validate_image_sentinel_ids检查tokenizer转换结果必须等于该值，否则ValueError；ProcessingInfo.get_image_placeholder_token_id只在None时失败，两处条件不同，不能只调用前一个取ID的方法就省略最终一致性校验。

input_ids的每个图像位置都重复同一个base ID。IMAGE_START=0、IMAGE=1、IMAGE_NEW_LINE=2、IMAGE_END=3是独立types张量中的角色，不是四种token ID；image_sentinel_mask只按精确129264判定。注释中MoE router使用base到base+5的范围，不扩大此mask，也不代表processor实际发五种ID。

image_token_types按start、每行W个IMAGE加一个newline、end输出INT64；num_image_tokens(H,W)=H×(W+1)+2。2×3格子共10个span位置，其中6行接视觉向量，其余delimiter位置接模型学习参数；不是只替换H×W个普通词嵌入。当前版本明确不插compressor-alignment pad，也不输出旧V4的perm字段。

## resize预算的两个坐标

llm_grid(Hpx,Wpx,p,r)分别为ceil((Hpx//p)/r)、ceil((Wpx//p)/r)，ViT网格为像素尺寸整除patch p。先分清像素尺寸、ViT patches、LLM格子及含newline的span，不按图像面积或patch个数直接替代LLM token预算。

load_image转RGB后取宽高。max_wh_ratio非None且过宽时先限制目标width；0<width×height<min_pixels则按面积平方根比放大并取整数，再将目标宽高向上取patch倍数。safe_resize计算实际LLM span，超过max_n_token才调用solve_resize_ratio；求得新尺寸后重算并assert预算，不是无条件采用最大预算图。

solve_resize_ratio令r=height/width、max_w=sqrt((budget-2)/r+.25)-.5、max_h=max_w×r，cell=patch_size×downsample_ratio。max_w<1时单列，目标高为((budget-2)//2)×cell；max_h<1时单行，目标宽为(budget-3)×cell。普通分支取两个floor格子对应缩放的较小者，再向下取patch倍数。边界常数2和3分别包含首尾与行换行，不改成平方根budget就声称等价。

本文件没有为任意非正宽高、极小/负budget、零patch/downsample、异常比例或所有浮点极值提供完整schema。接入方先验证配置与媒体尺寸；不能把末尾assert当对全部坏输入的用户错误恢复，也不能按一个正常fixture推理所有极端比例。

## 实际图像变换与patch顺序

若原图宽达到max_wh_ratio×原高，实际走image.resize；其他图走ImageOps.pad，目标为预算收敛后的宽高、填色(127,127,127)。这是宽图分支与保持比例pad的实现区别；PIL的具体插值默认不在本卡擅自固定，外部PIL版本和reference对齐需留证。

像素按NumPy FP32数组→CHW→除255，再(x-.5)/.5归一化，最后BF16。reshape(3,Hvit,p,Wvit,p)后permute为(Hvit,Wvit,3,p,p)，展平得到[Hvit×Wvit,3,p,p]，保持阅读顺序；不能把颜色通道或patch内部维度的连续排列换掉后只比shape。

load_image返回patches、Hvit、Wvit、Hllm、Wllm。downsample不足一整组的边缘仍形成ceil格子，和模型aligner右/下补齐协议共同验证；processor自己不进行ViT编码、空间unfold或学习delimiter投影。

## 多图BatchFeature和字段切分

DeepseekV4VLImageProcessor从config读取vision_patch_size、vision_downsample_ratio、vision_max_n_token、vision_min_pixels、vision_max_wh_ratio，逐图调用load_image。DeepseekV4VLProcessor将多图patches/types各自cat，vit_grid与llm_grid分别生成[num_images,2] INT64；总patch数为各Hvit×Wvit之和，types长度为各Hllm×(Wllm+1)+2之和。

images为空/None返回空BatchFeature。text、return_tensors和kwargs在签名中被接受，本函数没有实现通用文本tokenization或按return_tensors转换输出；不能从HF风格类名推导完整HF processor行为。官方reference没有auto_map processor是本类存在的来源说明，不是所有checkpoint均不需其他remote-code的承诺。

DeepseekV4VLProcessingInfo.get_hf_processor拒绝任何非空额外kwargs；get_supported_mm_limits返回image=None，仅是processor能力声明，实际服务limit-per-prompt仍由模型/运行配置决定。get_mm_max_tokens_per_item返回vision_max_n_token，与seq_len参数或当前请求的实际图像token数不是一回事。

_get_mm_fields_config以vit_grid.prod(-1)切patches，以Hllm×(Wllm+1)+2切types；vit_grid、llm_grid和types保留CPU，patches按框架字段规则传递。缺grid时使用空sizes，并不证明patches单独存在时可正确消费。多图顺序、每图flat sizes与后续span offset必须对应。

## prompt替换与delimiter消费

_get_prompt_updates先取实际placeholder ID，再调用validate_image_sentinel_ids。每图从out_mm_kwargs读取types.numel，构造同长度base ID列表，并用PromptUpdateDetails.select_token_id标记全部位置为embed位置；target为单个placeholder token。

角色始终走types旁路，token序列只重复base ID；IMAGE向量和start/newline/end学习向量由模型embed_multimodal形成，delimiter也不直接沿用词表embedding。多图、多个placeholder、实际MM mask与展开后token长度共同验收；本文件没有提供整个PromptReplacement框架实现、缓存和调度的闭包。

## dummy最大特征与min_pixels

get_image_size_with_most_features枚举LLM行数1到(budget-2)//2，令ViT高为行数×downsample，宽由扣除newline后的预算决定，再按max_wh_ratio限制；目标最大化ViT patch面积而不是简单选正方形或最大的LLM H×W。

找不到非零面积时ValueError。选中像素尺寸后，若不足vision_min_pixels则用2的幂等比放大输入尺寸，避免最小面积放大器改变选定宽高比。DummyInputsBuilder按image数量重复占位符，按该尺寸生成图像并允许MultiModalDummyOptions覆盖；dummy值不证明真实内容数值、最坏并发HBM或实际capture桶覆盖。

## Agent验证与回退

先记录源码/依赖与tokenizer身份、p/r、budget、min_pixels、max_wh_ratio、实际输入尺寸、resize/pad分支和三种网格。检查普通、极宽、极高、非整除边缘、多图、无图及非法配置；对每图逐个核对patch顺序、归一化dtype/数值、types序列、span长度、flat sizes与placeholder展开。再用视觉接入指南核对aligner行数、学习delimiter、raw IDs、MM mask和actual/padded Runner接口。

来源声称reference移植不是本批精度结果；这里只完成固定实现阅读与知识检索验收。真实PIL/reference变换、模型数值、图/PCP和硬件仍需按完整版本独立验证，通过后再拆分预处理、encoder、prefill的TTFT和内存开销。失败恢复匹配processor/config/tokenizer，不改129264、删newline、增加旧pad、截断types或忽略预算来凑形状。
