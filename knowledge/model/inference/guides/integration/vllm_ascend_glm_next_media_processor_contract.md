---
type: Guide
title: vLLM Ascend GLM-Next媒体前端：像素预算、视频采样与占位符
description: 适配GLM-Next图像与视频时核对token到像素预算、对齐画布、patch排列、帧采样与prompt展开，保留配置加载上限、fps参数解析和统计helper边界。
aliases:
- GLM-Next媒体前端
- Glm5NextProcessingInfo
- Glm5NextProcessor
- glm_sample_frame_indices
- _fit_aligned_size_within_budget
- _construct_video_placeholder
tags:
- task.implementation
- topic.multimodal
- topic.model_adaptation
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/processor.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/multimodal.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_video_placeholders.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/processor_config.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/multimodal.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_glm5_3_flash.py
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

# vLLM Ascend GLM-Next媒体前端：像素预算、视频采样与占位符

## 消费任务与固定证据

为GLM-Next接入图像/视频、替换媒体processor或排查视觉token预算/placeholder错位时，依次核对配置、像素画布、patch网格、采样帧和prompt展开。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：processor.py889、multimodal.py810、视频UT139、两份JSON资产28/31行和四卡测试196行全文；整模1114与loader UT47复用同SHA全文记录。

上游全部作为数据阅读，没有运行媒体解码、tokenizer、图像变换、UT、模型、NPU或CANN。Native/Transformers/Torchvision父实现、线上HTML和真实checkpoint未闭合；Main配对Native与独立Native快照的身份沿[框架版本入口](../../concepts/frameworks/vllm_ascend.md)区分。整项硬件证据未知，保持draft/空平台。

本卡负责像素和prompt前端；[视觉编码器](vllm_ascend_glm_next_vision_encoder_contract.md)负责Conv3D、norm、位置与encoder元数据；[整模加载](vllm_ascend_glm_next_model_loading_contract.md)负责语言模型/PP/mHC和checkpoint映射。GLM-5.3-Flash部署指南中video0的配方仍保留，不能用代码接口声明扩大支持。

## 本地processor与配置加载边界

Glm5NextProcessingInfo的cached_property实际创建Ascend本地Glm5NextProcessor.from_pretrained(ctx.model_config.model)，docstring的旧Native路径不是当前调用目标。get_hf_processor返回同一缓存对象并忽略它收到的kwargs；每请求参数的合并必须在实际处理链核对，不能假设调用此getter就重建配置。

from_pretrained将kwargs交AutoTokenizer，图像配置经Native get_image_processor_config，视频配置从本地processor_config.json取video_processor，再删除类型键构造本地类。没有实际访问checkpoint或下载配置；配置名称相似不证明与任意HF版本兼容。

_MAX_VIDEO_TOKENS为30000，但只在from_pretrained中视频cfg的max_image_tokens非None时执行min(config,30000)。图像值原样保留；视频缺字段时的类默认240000、之后的请求覆盖值，没有由这条加载分支无条件再钳为30000。来源注释的KV余量动机不是本次测得的HBM收益，不能把该常量称为所有请求的硬上限。

fixture写图像16..8000、视频16..240000 tokens，patch14、merge2、temporal2、expand1、fps2；它是功能测试资产。进入from_pretrained的240000与实际加载后预算分开记录，且不替代真实模型revision/config。

## token预算、对齐画布与resize分开

_pixel_budget要求min/max_image_tokens都存在；每视觉token对应的像素单位为temporal_patch_size×(patch_size×merge_size)²。patch_expand_factor不在这项单位中；空间画布对齐factor却为patch_size×merge_size×patch_expand_factor。不能将两个factor互换。

smart_resize检查正尺寸/factor、预算与min<=max。t_bar=max(t_factor,round(t/t_factor)×t_factor)，使用最近整数倍而非ceil；H/W向上对齐空间factor。超过max_pixels时，_fit_aligned_size_within_budget二分内容高度、按比例floor宽度，再向上对齐画布；连一块对齐画布都容纳不了则ValueError。

低于min_pixels时按sqrt(min/(t×h×w))放大、ceil空间尺寸，若又越max则重新收敛。后续真实video patchify按ceil补帧，与这里round的时间预算不是一条运算；非默认temporal配置的交集仍需实际shape/预算验证。

resize_mode=pad保持内容比例：过大时缩小，只有允许且低于最小预算才放大，右/下补原始像素0，之后才normalize。resize模式直接拉伸至画布；其他mode报错。不能借用[V4.1图像预处理](vllm_ascend_v41_image_processor.md)的灰127 pad、含newline预算或sentinel/span公式；颜色/插值由实际依赖验证。

## 像素行、网格与模型输入

图像按shape分组，resize后恢复顺序、再分组做rescale/normalize，重复最后帧补到temporal_patch_size倍数。patchify采用空间merge-block优先的排列，展平patch行宽为C×temporal_patch_size×patch_size²，grid_thw为[T/P,H/patch,W/patch]；输出pixel_values和image_grid_thw。仅比总元素数不能证明像素顺序一致。

get_number_of_image_patches返回空间merge前的Hgrid×Wgrid，时间因子来自self.temporal_patch_size；视觉embedding token数还要按merge_size²换算。关闭resize或改patch/merge时要检查模型Conv3D和网格整除，不能按方法名认定已返回最终语言token数。

视频输出pixel_values_videos与video_grid_thw，也按实际temporal因子重复末帧。_preprocess可取请求patch/merge/temporal和token上下界，但patch_expand_factor在函数内被self属性覆盖；valid_kwargs里声明了某字段，不证明它在所有子路径都实际生效。

## 帧采样的目标参数解析

glm_sample_frame_indices缺duration时按round(last_frame_idx/input_fps)+1推时长；目标extract_t=int(duration×target_fps)，再受max_frames限制，默认2fps/2048。短片按间距floor取帧，较密分支按1/(temporal_patch_size×target_fps)的时间步贪心选取，再linspace补/收至目标，去重后若奇数则重复最后一帧补偶数。

这里的偶数补齐不是任意temporal_patch_size的倍数保证；像素patchify还会按真实P补齐。注释里的video grounding改善没有本批质量或吞吐证据，不可当性能结果。

Glm5NextVideoProcessor.sample_frames要求metadata.fps存在，目标采样率优先fps参数，再target_fps，再self.fps_interval；max_frames或self.max_frame_count_dynamic决定上限，方法传给采样器的是self.temporal_patch_size。fps_interval/max_frame_count_dynamic/temporal等声明参数不都直接进入该方法，实际Native预处理参数解析另验。

## placeholder必须复用同一帧选择

ProcessingInfo._get_video_second_idx_glm46v对input_fps检查有限且>0。已预采样时要求frame_indices长度等于total_num_frames并保留重复；否则按请求合并后的fps/target_fps/max_frames调用同一sample_frames，包括显式fps=None。不能在placeholder侧另做一遍不同公式的均匀采样。

每个temporal patch的timestamp来自int(frame_idx/input_fps)，随后才格式为一位小数，分数秒已经被取整；不能声称保留亚秒精度。选不到帧报错，timestamp数量必须等于processed video_grid_thw中的T。

_construct_video_placeholder生成video-start/end，内部每时间patch由image-start/end包围Hgrid×Wgrid/merge²个image_token_id并插编码后的时间字符串。视频中的视觉embedding位置仍选image_token_id，不能把video标志本身当全部视觉行。processed grid在CPU预处理阶段.tolist，不据此泛称模型前向有设备同步。

Glm5NextMultiModalProcessor沿用父类image updates，为video构造request-local _merge_kwargs闭包，并从out_mm_kwargs读取本次处理后的grid。PromptUpdateDetails只选择image token的embedding位置，_hf_processor_applies_updates=False；本地HF式processor对text只是tokenize，真正marker展开由Native prompt-update链负责。

## request隔离与独立helper缺口

__call__合并image/video kwargs；视频默认带video_metadata，但除非TOPLEVEL kwargs含return_metadata键，否则会pop。不能由嵌套videos_kwargs的同名字段推返回行为等价。可选mm_token_type_ids仅标记image token；post_process_image_text_to_text委托tokenizer.batch_decode，不是视频质量评测。

_get_num_multimodal_tokens是另一条统计helper：video-only分支使用的局部merge_size仅在image_sizes分支赋值；image/video kwargs都直接取共享_defaults字典再update。像素/placeholder的请求隔离UT未覆盖此helper。这里记录静态调用边界，没有运行证明异常，也没有修改上游；接入前确认Native实际调用链、视频patch统计和跨请求状态。

ProcessingInfo的max_pixels覆盖可用于预算查询，而pixel预处理使用token上下界换算，不能宣称二者对所有kwargs自动一致。_get_vision_info做profiling时将max预算至少提升到一块对齐时间画布、min_pixels设1，按补帧后的ceil T计算prod(grid)/merge²；profiling提升预算不等于运行时接受任意过小预算。

## 测试证据与Agent验收

视频UT139行有8个test定义：toy WordLevelTokenizer和CPU填0的28×28帧，覆盖0.5/2/30/60/301/600秒、扁平/嵌套kwargs、预采样重复帧、3线程隔离、非法fps/空帧/网格不一致和image update不变。target_fps=1单独设置仍预期gridT2，原因是默认fps2优先；temporal4在该2秒fixture预期gridT1。这些是测试设计，本次未执行，也不覆盖统计helper的全部问题。

四卡用例构建9层synthetic模型、7KDA/2MLA加MTP，TP4/EP、graph/eager与RecoverSSM组合；image0/video0且只传文本token IDs。视觉构造发生不代表图像/视频参与推理，不能将它写成多模态实机通过。

Agent先保存完整config/tokenizer/依赖身份与最终参数来源；逐项对比图片/视频画布、patch顺序、采样索引含重复、实际grid、timestamp、prompt和embedding mask。覆盖短/长/奇帧、预采样、temporal变化、并发和image/video-only helper，再验证实际checkpoint、eager/graph与目标硬件。按媒体下载/解码、预处理、encoder、merge/prefill拆TTFT和峰值；失败恢复完整匹配配置，避免截token、改帧索引或吞掉校验来凑shape。
