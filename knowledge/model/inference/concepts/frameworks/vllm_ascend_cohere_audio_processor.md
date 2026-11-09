---
type: Concept
title: vLLM Ascend Cohere 音频处理：CPU Mel、长度与处理缓存
description: 按固定原生代码核对 CohereASRFeatureExtractor、FilterbankFeatures 的采样率/形状、dither、精度、逻辑帧与占位token；CPU输入契约不扩展NPU支持。
tags:
- task.design
- task.implementation
- task.optimization
- topic.multimodal
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/transformers_utils/processors/cohere_asr.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/cohere_asr.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Cohere-Transcribe.md
  role: constraint
created_at: '2026-10-30T11:21:27Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T11:21:27Z'
---

# vLLM Ascend Cohere 音频处理：CPU Mel、长度与处理缓存


## 范围与真实消费入口

本卡完整读取vLLM v0.32.0的processors/cohere_asr.py（573行），并读取模型文件1863–2046的factory/parser/长度/dummy/MM/cache/prompt及注册范围；不是完整2334行模型实现，也不是Ascend设备验证。未知硬件保持draft；A2部署与来源WER/RTF见[Cohere指南](../../guides/models/vllm_ascend_cohere_transcribe_asr.md)。

CohereASRProcessingInfo.get_hf_processor首次根据hf_config.preprocessor构造本地CohereASRFeatureExtractor及ctx.tokenizer，再缓存CohereASRProcessor；本工厂未读取传入**kwargs作为配置覆盖，也不是仅凭trust-remote-code选择远端同名processor。window_size/window_stride以秒乘实际sample_rate再取int，features/FFT/dither等来自配置，max_duration来自max_audio_clip_s；不把类默认值当每个checkpoint实际值。

该factory固定device=cpu；get_data_parser另把feature_extractor.sampling_rate设为MultiModalDataParser的target_sr。这里只闭合目标采样率接线，媒体解码/真正重采样和进程安装还需查parser与实际路径。AutoFeatureExtractor/AutoProcessor的注册是模块导入副作用，本次只读，没有触发导入。

## ndarray、采样率与返回字段

CohereASRFeatureExtractor.__call__接收ndarray时把它包装为一个样本；否则逐样本读取shape[0]，复制到float32的右补零批次，提取后返回CPU input_features及length。它没有使用sampling_rate参数校验或重采样，也没有在本方法里做声道混合/任意Python浮点列表转换。不要把立体声二维数组、空batch/空音频或错误实际采样率当成已支持输入。

模型路径可能先经target_sr parser；“该方法不重采样”不能扩成“全服务不重采样”。独立调用与服务路径分别保存原采样率、真实样本数、声道、dtype、目标采样率及处理后shape，不能只传一个sampling_rate数字就宣称音频已转换。

CohereASRProcessor允许audio与text独立或同时存在，音频走feature_extractor，text走tokenizer并仅复制input_ids；本方法不统一验证两者批次对齐，也不把tokenizer全部字段自动转交。model_input_names只列input_features，但实际BatchFeature还有length；接框架时不要丢掉长度或用补零宽度替代。

## Mel 配置、精度与有效帧

类fallback为16kHz、window320、hop160、64 mel、preemph0.97、Hann窗、power2、per_feature、log/add 2^-24及pad_to16。实际以factory读到的checkpoint preprocessor为准。window/hop需正int，exact_pad不接受奇数hop；旧stft_conv/stft_exact_pad只留弃用警告，不表示另一个加速STFT实现已可用。

window和filter bank在构造时转BF16，STFT使用转回float的window且关闭autocast，Mel乘法也关闭autocast；把已舍入buffer转float不会恢复原FP32数值。模型BF16、输入float32和各阶段算子精度分别记录，不把处理器称为纯BF16/FP16全链。本文件没有证明所有这些路径能在Ascend Device执行。

前向按可选preemphasis、STFT magnitude/power、Mel、log/add或clamp、frame_splicing、normalize、有效帧mask及pad顺序处理；linear_spec分支提前返回，绕过后面的Mel/log/归一化/pad。STFT标dynamo.disable、forward标torch.compile/no_grad包装，不证明全图或NPU图成功。

get_seq_len使用floor((samples+pad_amount-n_fft)/hop)，没有额外+1。seq_len_unfixed先按公式计算，forward对原始0 samples另保逻辑0；这不保证STFT等后续都接受空输入。默认even FFT/center路径下等于floor(samples/hop)；这才是返回length。实际STFT矩阵宽度另由张量得到，mask把>=逻辑length的位置置pad，再补到pad_to倍数。以默认参数16000 samples得逻辑100帧只是算术例，不是模型或NPU执行结果；音频token还要经subsampling。log_zero_guard_type只在本构造接受add或clamp，数值guard另可取tiny/eps或数值；不要混为任意log激活模式。

max_duration参与max_length计算，不在常规pad_to16分支里裁剪/拒绝超过30s音频。forward虽然有pad_to='max'分支，构造先对pad_to做>0及模运算，不能据分支文字认定字符串max已能通过此构造。pad_min_duration实际置0，不能许诺空/短音频都会自动补成可用长度。

per_feature按有效帧计算均值和N-1标准差，将std的NaN置0后加1e-5；这不是对零有效帧全部NaN/错误的通用保证。all_features含逐样本item循环，不能由CUDA图注释推NPU时延。固定均值/方差模式也需实际shape匹配；未知配置不自动成为已验证归一化。

frame_splicing>1的实际代码拼x[:n]与x[n:]再沿feature维合并，不靠常见邻帧移位算法猜结果。narrow-band参数在构造里出现不证明前向已应用增强；部分非默认配置还引用原始n_fft参数。窗口none/未知值会得到None并遇到后续assert，不能从候选字典就列为有效配置。本批没有修上游代码或执行这些边界。

## dither、对象状态与缓存

FilterbankFeatures在dither>0时推理也做x+=noise，eval不会关闭。generator在构造时seed0，状态随调用推进，固定seed不等于每次重置；独立Filterbank前向还有in-place输入变化，而FeatureExtractor先构造自己的pad批次，不混为原始ndarray必然被改。

CohereASRMultiModalProcessor._cached_apply_hf_processor检查preprocessor配置，dither（默认1e-5）>0直接_apply_hf_processor，绕过假设输出不变的处理缓存；dither<=0才走父类缓存路径。这不改变KV prefix cache、Csrc cache或Torch compile cache。关噪声换缓存是特征语义变化，需对齐有效配置、调用次序和WER/CER后测性能，不能只比首次/稳态时间宣称无损优化。

## 从 samples 到占位 token

支持的音频项上限在此为1。get_num_audio_tokens先取Mel逻辑帧，再按config.encoder.subsampling_factor做ceil；参数因子来自实际配置，不直接把帧数当decoder token数。16000 samples/默认hop=100帧，若因子为4则25占位token，是带条件的算术例，不声明真实checkpoint因子或转写长度。

默认tokenize设置add_special_tokens=False以免自动EOS扰动，task/language特殊token由请求协议/用户语义提供。dummy text使用startoftranscript，dummy音频长max_duration×sr，仅为资源探针；它不验证语言质量或真实最长音频。encoder prompt置[0]，PromptReplacement再以相应数量0替换，input_features和length按audio batched字段打包；skip_decoder_start_token=True也不等于可删除所有任务/语言token。

本卡未运行torch/torchaudio/transformers导入、feature extractor、JIT、模型、音频下载或NPU。后续沿完整encoder/subsampling/attention/decoder、媒体parser和真实配置闭合，再分别验输入、数值、精度及性能。
