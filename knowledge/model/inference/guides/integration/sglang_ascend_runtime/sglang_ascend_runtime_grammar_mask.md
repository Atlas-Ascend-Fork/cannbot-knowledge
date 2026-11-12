---
type: Guide
title: SGLang约束解码在NPU上的Token位图应用
description: 说明XGrammar与LLGuidance在NPU转入sgl_kernel_npu位图算子、mask设备搬移及静态入口的平台边界。
tags:
- task.implementation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/constrained/xgrammar_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/constrained/llguidance_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_ascend_vocab_mask.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_llguidance_npu_mask.py
  role: supporting
created_at: '2026-11-08T12:07:26Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
aliases:
- apply_vocab_mask
- GuidanceGrammar
---

# SGLang约束解码在NPU上的Token位图应用

XGrammar的apply_vocab_mask按logits.device.type分派，NPU先导入sgl_kernel_npu注册，再调用torch.ops.npu.apply_token_bitmask(logits,vocab_mask)。LLGuidance的GuidanceGrammar使用同一NPU算子，move_vocab_mask以non_blocking搬到目标设备。不能因XGrammar有CUDA/Triton函数就把NPU流量导入GPU实现。

XGrammar普通对象入口还处理CPU位图，静态入口只列cuda/xpu/musa与npu，否则抛错误；这两个入口的可接受设备集合不同。注册导入仅保证尝试建立符号，mask形状、词表尾块、有效行和logits dtype仍须满足对应kernel合同。

位图是对既有grammar状态的执行，不替代文法编译或matcher推进；CPU生成mask→异步搬移→设备应用→采样之间必须有正确stream依赖。验证包含尾词表、全禁止/单token、batch筛选与合并、两个grammar后端，并比对grammar允许token集合和生成合法性。通用底层接口另见已摄取的sgl-kernel-npu API。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。

## 测试定义的证据强度

manual XGrammar测试在真实NPU可见时比较64词表禁止token与B4/V257随机位图，包含尾32-bit块并要求有限位置相同、差值<1e-5；LLGuidance manual则显式伪造NPU device/ops在CPU验证分派，不能当作原生NPU kernel数值验证。本次都未运行。
