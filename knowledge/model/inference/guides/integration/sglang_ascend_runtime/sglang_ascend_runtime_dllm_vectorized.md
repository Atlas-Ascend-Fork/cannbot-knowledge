---
type: Guide
title: SGLang NPU扩散语言模型的元数据复用与批量去噪
description: 说明dLLM同步去噪固定canvas的NPU元数据复用、JointThreshold默认向量化、强制一个位置的topk语义与FDFO状态分离。
tags:
- task.implementation
- topic.model_serving
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/dllm/algorithm/joint_threshold.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/dllm/algorithm/base.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/overrides.py
  role: supporting
created_at: '2026-11-08T12:10:30Z'
updated_at: '2026-11-08T12:10:30Z'
platforms: []
aliases:
- JointThreshold
- vectorized_decoding
- FDFO
---

# SGLang NPU扩散语言模型的元数据复用与批量去噪

dLLM同步循环先prepare_inputs并forward一次；没有待去噪mask直接返回空输出。NPU首forward后mark_forward_metadata_ready(replan_equivalent=False)，复用固定canvas attention元数据；这不同于其他平台仅在reuse_forward_metadata且can_run_graph时采用的条件，不能把canvas变化也当可无条件复用。

JointThreshold在NPU默认vectorized_decoding=True，可由algorithm_config覆盖。更新函数按[B,block,V]同时处理全部行，避免逐行Python与.item同步；先可选重复penalty，再argmax和softmax gather置信度，mask-to-token按threshold，token-to-token按edit_threshold，prompt位置不修改。

若仍有mask但未达阈值，强制选一个位置用topk(k=1)而非argmax，保留per-row路径在置信度相等时的选择约定。finished/post_edit_steps原地维护，编辑预算耗尽或没有传输位置结束；默认max_post_edit_steps16，max_steps为block+该值+1。源码注释称融合softmax快于另一log-domain方案，没有本次profile不能量化收益。

同步向量化共享batched状态；FDFO需逐request携带状态，完成者清空、未完成者跨轮保留，不能将共享对象直接套给动态进出batch。基础循环对保留生成KV的算法还要求最终token已经forward落缓存后再报告完成，mask更新不等于KV持久化。

NPU dLLM参数后处理选ascend attention。验收对齐per-row与vectorized的ties、penalty、prompt mask、编辑预算与输出，分开固定同步和FDFO，检查元数据、KV与token一致；该语言去噪路径与multimodal_gen图像/视频扩散是不同执行系统。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
