---
{
  "type": "Runbook",
  "title": "DeepSeek V4 MoE TP 融合开关参数名不匹配导致 SwiGLU clamp 被跳过（PR804 审查发现）",
  "description": "模型/框架：DeepSeek V4（含 DeepSeek-V4-Flash 系 MXFP4/MXFP8 量化）在 cann-recipes-infer 新增的 Attention TP + MoE TP 路径（PR #804，head bf24d16）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# DeepSeek V4 MoE TP 融合开关参数名不匹配导致 SwiGLU clamp 被跳过（PR804 审查发现）

## 适用场景

- 模型/框架：DeepSeek V4（含 DeepSeek-V4-Flash 系 MXFP4/MXFP8 量化）在 cann-recipes-infer 新增的 Attention TP + MoE TP 路径（PR #804，head bf24d16）。
- 环境：审查环境为 CPU（torch 2.7.1+cpu / torch-npu 2.7.1.post4 安装但 NPU 算子 mock）；目标环境为 A3 NPU 推理。
- 目标：审查 MoE TP 与量化模块的融合开关传递是否正确。

## 触发与观测

- MoE TP 传入的融合开关与量化模块读取的参数名不一致：传入 `enable_custom_ops`，量化模块实际读取 `enable_cann_ops_nn`，导致进入忽略 `swiglu_limit` 的分支（source 0 seq 187）。
- CPU 探针逐字输出（AST 提取真实函数 + mock 量化算子，swiglu_limit=10.0，输入 merged=[[20.0, 20.0]]）：
  "CLAMP mxfp4.py: PR branch=400.0000; correct flag=99.9955 (mocked quantization)"
  "CLAMP mxfp8.py: PR branch=400.0000; correct flag=99.9955 (mocked quantization)"（source 0 seq 164/165）
- 官方模型配置（DeepSeek-V4-Flash config.json）要求 swiglu_limit=10.0，超阈值时会改变计算结果（source 0 seq 187）。

## 探针与操作

- 探针（CPU review probe）：AST 从被审 tree 提取 `DeepseekV3MoE._build_moe_tp_gmm_args` 与 `W4A8MxFp4MoEGMMMethod.apply` / `MxFp8MoEGMMMethod.apply`，用 TorchProxy 把 `torch.cann_ops_nn.swiglu_group_quant` 替换为带 trace 的 clamped 实现；断言 PR 分支 trace 为 `['unclamped_swiglu']`，补 `enable_cann_ops_nn: True` 后 trace 为 `[('clamp_limit', 10.0)]` 且两结果 `not torch.allclose`（source 0 seq 161）。
- 定位：`models/deepseek_v4/models/modeling_deepseek.py:416`（参数名传入处）；修复建议为修正参数名。

## 机制与判别

- 根因：参数名不匹配（`enable_custom_ops` vs `enable_cann_ops_nn`）使量化 apply 走非融合分支，`npu_swiglu` 无 clamp 版本被调用，`swiglu_limit` 失效。
- 判别信号：mock 分支 trace 直接区分 `unclamped_swiglu` 与 `('clamp_limit', 10.0)`；数值上 PR 分支 400.0000 vs 正确 99.9955（20×20 无 clamp 与 clamp 后的差异）。
- 未验证：NPU 整网精度影响未运行（"已完成 CPU 逻辑复现、语法检查及 Attention/O-proj 分片代数检查；未运行 NPU 整网"）。

## 验证信号

- tool_observed（CPU mock，source 0 seq 164/165）：两条 CLAMP 输出如上；ATTENTION TP=2/4 分片求和检查通过（对照，证明审查探针本身工作）。
- 单次探针、两份量化文件（mxfp4/mxfp8）一致复现。
- 证据等级：CPU 逻辑复现，非 NPU 设备验证。

## 适用与失效边界

- 适用于：cann-recipes-infer DeepSeek V4 MoE TP + compressed-tensors/MXFP 量化路径的融合开关自查。
- 失效边界：结论基于 PR #804 head bf24d16 的代码与 CPU mock；后续提交可能已修正参数名；无 NPU 精度数据，不能量化对整网输出的实际影响幅度。
- 停止条件：核对当前代码参数名一致后本规则失效。

## 附：断言存档

- DeepSeek V4 MoE TP 把融合开关以 `enable_custom_ops` 传入，而量化模块读取 `enable_cann_ops_nn`，导致走忽略 swiglu_limit 的非融合分支；CPU 探针（swiglu_limit=10.0、输入 20×20）实测 PR 分支输出 400.0000、正确分支 99.9955（mxfp4/mxfp8 一致）；官方 DeepSeek-V4-Flash config.json 要求 clamp 阈值 10。

```text
CLAMP mxfp4.py: PR branch=400.0000; correct flag=99.9955 (mocked quantization)
CLAMP mxfp8.py: PR branch=400.0000; correct flag=99.9955 (mocked quantization)
```

```text
传入的是 `enable_custom_ops`，量化模块实际读取 `enable_cann_ops_nn`，导致进入忽略 `swiglu_limit` 的分支。[官方模型配置](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/raw/main/config.json)要求裁剪阈值为 10，超过阈值时会改变计算结果。应修正参数名。
```
