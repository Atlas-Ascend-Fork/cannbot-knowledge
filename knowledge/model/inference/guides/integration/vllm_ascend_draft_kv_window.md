---
type: Guide
title: vLLM Ascend Draft KV 滑窗：读窗口与绝对写入不变量
description: 按中英文设计在MRv1适配draft_window_size，核对SlidingWindowAdapter块对齐、future_offset与全部长度镜像，保持绝对写入并标注MRv2迁移缺口。
tags:
- task.implementation
- topic.speculative_decoding
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/speculative_kv_sliding_window.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/dspark_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/speculative_kv_sliding_window.po
  role: supporting
created_at: '2026-10-29T09:49:02Z'
updated_at: '2026-10-30T05:23:56Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Draft KV 滑窗：读窗口与绝对写入不变量

## 范围和启用理由

仅MRv1 EAGLE3/DFlash/DSpark，additional_config.draft_window_size 正数，缺省关闭。MRv2尚未覆盖；MTP强制关闭，因为会影响target共享层。适合短训练上下文draft在长输入接受率塌陷；原生长上下文/SWA draft可被过小窗口损伤。来源GLM-5.2的恢复与吞吐数字是特定draft实验，未复测，不推广。

## 数学关系和两个不变量

令W为window、b为kernel block、F为future_offset：start=floor(max(seq_lens+F-W,0)/b)×b，windowed_len=seq_lens-start，start_block=start/b。clone block table从该列开始取，越needed/原表宽度的列置零，所有KV length限制为同一windowed_len。block对齐意味着实际可读窗口不必恰等W。

EAGLE3 的F=K，因为seq_lens只含context；DFlash/DSpark的seq_lens已含bonus/mask伸展，F=0，不能重复加K。slot_mapping永不window：写入用完整表与绝对位置，只裁FIA读。NPU seq_lens和CPU mirrors/upper bound全部同步裁剪，不能留任一路径读出窗口外。

## 接入顺序与验收

共享metadata在per-layer builder前应用；DSpark会覆盖为per-group完整表，必须在覆盖之后再应用，不能只在base proposer提前裁一次。MRv2移植需改builder输入和每组clone，不是在最终metadata上照搬旧common对象。

比较窗口关/开在短/长context的接受率、数值、绝对KV写入与端到端时延，覆盖block边界、不同seq长度、draft query伸展和窗口变化。短于native训练window可能退化；无塌陷则先保持关闭。移除key回退，并恢复选定Runner。本次仅核对设计，没有执行device数学或模型测试。


## 平台证据待补

滑窗设计限定MRv1及draft方法，但未为该功能声明硬件范围；一般投机功能支持表不能提升为该滑窗的整卡平台集合。据此撤回原平台枚举，保持draft/空平台；这是证据不足，不能解读为这些平台不支持。


## DSpark长度诊断入口

裁读窗口之前先按[DSpark query/KV长度与缓存组](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)核对实际Q、拒绝后的device长度与已校正CPU mirror。MRv1 CPU不再次减拒绝数；MRv2无DCP MLA另外从draft有效长度供FIA使用，这个修正不等于MRv2已经支持本卡draft_window_size。不能把target乐观上界或图padding的query累计长度当成真实已写KV长度。


## 中文窗口数学与迁移验收

speculative_kv_sliding_window.po的25条有效译文均匹配当前英文。设计给出的max_window_blocks=W//b+1，needed为ceil(windowed_len/b)并受其上界限制；clone按start_block取列，超过needed或原表宽度的列清零。block向下对齐导致设计中的windowed_len可达W+b-1，不能要求实际每步恰好读取W个token，更不能裁写入slot_mapping来“对齐”读窗口。

SlidingWindowAdapter保留[max_num_reqs,max_window_blocks] clone buffer，EAGLE3的future_offset来自num_speculative_tokens；DFlash/DSpark已包含bonus/mask伸展，不再叠加。CPU seq_lens_cpu、_seq_lens_cpu、seq_lens_cpu_upper_bound与device seq_lens应服从同一裁剪关系；只改block_table_tensor或其中一个长度镜像会破坏读边界。

MRv2部分是尚未实现的迁移方向：围绕_build_draft_attn_metadata改builder inputs、input_buffers.seq_lens、每组表clone和CPU上界，而不是构建后修改不存在的共享common_attn_metadata。已有MRv2 DSpark长度修正也不能当本滑窗已移植完成。

原文的GLM-5.2早期DSpark在32k上下文接受长度约5降到1、开窗恢复约4.7–5.5及最高+381%吞吐是其原始评估叙述，不是本次结果或所有draft收益。与DeepSeek-V4原生联合训练的DSpark长上下文已稳定时来源提示warning；不能因同名DSpark默认套2048窗口。目标保留全上下文是设计不变量，仍须用真实输出和目标/草稿KV轨迹验证实现，不单凭描述宣告精度保持。
