---
type: Guide
title: SGLang Ascend批次不变运算：norm拆分与FIA图handler
description: 说明batch-invariant wrapper的dtype限制、add/RMSNorm拆分和FIA out重载保留，避免将图ABI适配当作数值验证。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/batch_invariant_ops/npu_batch_invariant_ops.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/batch_invariant_ops/batch_invariant_ops.py
  role: implementation
created_at: '2026-11-08T12:08:02Z'
updated_at: '2026-11-08T12:21:07Z'
platforms: []
aliases:
- NativeFIAGraphHandler
- batch_invariant_ops
---

# SGLang Ascend批次不变运算：norm拆分与FIA图handler

## 适用场景

batch invariant适配借助外部batch_invariant_ops包替换mm/matmul、mean、log_softmax等操作，目标是减少batch变化引起的数值路径差异。多维mean先FP32求和再除元素数，dtype只接受None/float32；log_softmax的half_to_float不支持。

fused add_rmsnorm被拆成显式add和native RMSNorm，因为原融合版本不满足这里的不变性要求。减少融合并非普遍性能优化，适配方须根据精度目标选择，并测量额外tensor与kernel开销。

## FIA图调用ABI

FIA OpOverloadPacket的.out重载需保留，否则graph handler不能转换到预分配输出形式。NativeFIAGraphHandler为actual_seq_lengths和actual_seq_lengths_kv补kwargs默认值，允许NPUGraph.update重绑定这些host输入。

默认op先查询最大workspace、按Q与V推导输出，再以.out传workspace与预分配out；输出shape依赖V而非K，QK/V维不同不能混淆。辅助推导只传需要的关键字，不把长度数据错误固化为输出推导输入。

## 验收与边界

检查外部包版本、受支持dtype、FIA packet与.out同时可访问、长度更新后图输出变化。用同请求单独/合批比较作为数值验收，再单独测延迟；handler注册成功只证明调用ABI接通，不能代替batch不变性或运行正确性验证。本次没有运行这些实验，平台范围未知。

## 全局绑定与退出边界

全局enable在NPU为ATen注册mm、matmul、mean.dim与_log_softmax，另原地替换torch.ops.npu和torch_npu中的FIA、最大workspace查询及add_rms_norm符号；GPU分支的addmm、mm.out、rms_norm、mm.dtype与bmm注册不自动出现在NPU分支。不可将非NPU Triton实现的约束套给这些NPU wrapper。

disable只销毁torch.library注册、恢复保存的torch.bmm并重置模式标记；源码没有保存并恢复上述NPU monkeypatch的原始对象。因此set_batch_invariant_mode上下文恢复标志不等于恢复全部NPU符号，运行中切换需核对函数身份和调用行为。本次只核对静态控制流，未执行全局绑定。
