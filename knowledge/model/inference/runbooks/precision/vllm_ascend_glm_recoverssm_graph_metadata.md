---
type: Runbook
title: vLLM Ascend GLM RecoverSSM：图填充行、接受状态与稳定缓冲区诊断
description: 当GLM RecoverSSM在满图、混合prefill/decode或batch收缩后状态错位时，核对实际请求裁剪、持久buffer尾部清理和commit视图，区分占位接受数与采样结果。
tags:
- task.debugging
- topic.precision
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/recoverssm_metadata.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_kda_recoverssm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/mamba_hybrid.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/kda.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_recoverssm_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kda_dispatch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/kimi_k3/nvidia/kda_metadata.py
  role: supporting
created_at: '2026-10-29T14:19:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:19:58Z'
---

# vLLM Ascend GLM RecoverSSM：图填充行、接受状态与稳定缓冲区诊断


## 症状和边界

仅针对固定Ascend ceac1a2b的AscendKDARecoverSSMMetadataBuilder及其GLM接入：图填充行进入sampler/commit、batch缩小后读旧state slot、混合prefill偏移错误，或verify后checkpoint提前变化时，使用下面探针定位。它是源码约束和待执行的诊断方法，不是本仓复现过的故障报告。整条执行路径的平台尚未逐项验证，保持draft与空平台；产品入口见[实验启用指南](../../guides/optimization/vllm_ascend_glm_kda_recoverssm.md)。

## 快速检查

先保存实际请求数、padding后请求数、CPU/device query_start_loc、draft counts、num_actual_tokens，以及spec_state_indices_tensor、spec_query_start_loc、num_accepted_tokens和recoverssm_commit引用的形状/地址。确认worker在适用GLM配置下安装KDARecoverSSMCommitContext替换，再由builder创建并缓存context；只看到导入类名不证明补丁已调用。

## 图填充与混合batch的诊断路径

1. `_normalize_graph_padding`在num_actual_reqs小于num_reqs时克隆CPU offsets和draft counts，把填充offsets压到最后真实请求终点，填充draft counts置-1；device侧用torch.minimum在当前流裁剪。例：K5、4行图而真实2请求，`[0,6,12,18,24]`应变为`[0,6,12,12,12]`，actual tokens为12，draft counts为`[5,5,-1,-1]`。原输入不应被改写。不要用blocking CPU→device复制修复该偏移，避免引入等待前一MTP图的同步。
2. 父builder运行期间临时关闭其CUDA专属graph staging，finally恢复真实graph标志，再构建Ascend描述符。未恢复标志或直接复用CUDA staging会破坏后续NPU缓冲区准备；这个finally是控制流证据，不是本仓异常注入测试结果。
3. speculative decode、prefill和普通decode分别构建conv描述符。混合batch的prefill offsets先去掉普通decode行并减去decode token数，state/initial-state也做对应切片；例如`[0,1,5,11]`含1个decode token时，prefill应为`[0,4,10]`。不能只修offset而保留未切片的state indices。
4. `_non_spec_cpu_starts`按同一分类将有效、非prefill的零draft decode视为spec行，从non-spec偏移集合排除，受每行长度<=K+1约束；长度为0的padding不成为有效行，超容量profiler行走non-spec。不要把draft count为-1或本轮没产生草稿简单解释为“这行一定绕过RecoverSSM”。

## 持久staging和接受数的两种含义

`_stage_spec`仅在full graph、没有prefill/普通decode、spec token数不超capture容量且batch不超state行/capture行的较小容量时启用。它复用已分配storage：有效state行copy，尾部state清零；offset尾部重复最后终点；accepted buffer全部填1；同时replace commit中的state_indices/query_start_loc以指向同一staged视图。连续大batch→小batch应保持地址并清掉上一轮有效尾行；token容量与请求行容量必须分别检查。

上面的1是执行conv/verify时的占位/输入协议，不是拒绝采样的真实接受结果。对应vLLM v0.32.0父类commit_recoverssm_state接收真实num_accepted_tokens，再按num_spec_decodes切片state/offset并调用context.commit；Ascend KDA dispatch先记录紧凑更新，不能在verify期间无条件把所有候选写入持久checkpoint。本卡只闭合已读父类和Ascend元数据接口，未宣称完整runner采样时序、Triton/AscendC kernel或PD同步闭包完成。

容量不足、混batch或eager fallback时本helper保留动态metadata和原commit引用，不强行写入capture缓冲；不能为了地址固定扩写越界或把guard改成始终开启。UT覆盖地址复用、尾部清理、padding裁剪、混合prefill和容量fallback；这些是上游测试断言，未在本仓运行。

## 修复后的验证和回退

按上述信号定位调用方、行裁剪、视图绑定或容量选择，再对照固定源码恢复协议；保留真实请求与图填充两个计数。目标环境先跑eager/graph对照、连续batch收缩、真实请求数0及混batch，检查输入未被意外修改、conv与commit共享正确视图、采样后仅接受前缀推进且下轮状态正确。分别记录质量及metadata同步开销，不能只看最终文本碰巧相同。

验证失败先关闭RecoverSSM并重启恢复native KDA基线；不继续复用异常递归状态。不将放宽dtype/并行/connector校验作为修复。仍需目标NPU数值与完整采样/commit调度验证。
