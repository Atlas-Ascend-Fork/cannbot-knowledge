---
type: API
title: custom.npu_swiglu_clip_quant：A3 分组削波与有效输出范围
description: 限定 BF16 输入、count 分组与动态量化，说明激活方向、形状和尾部垃圾数据边界。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_swiglu_clip_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_swiglu_clip_quant.cpp
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp
  role: header
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py
  role: constraint
created_at: '2026-11-09T02:45:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
---

# custom.npu_swiglu_clip_quant：A3 分组削波与有效输出范围

## 来源与交付范围

依据 Recipes 固定提交 `944d2d3ece86f7df33dbb0cb155c72ca619a9c66` 的独立接口文档、Schema 与 PyTorch 包装层。该接口在 `torch.ops.custom` 注册；安装并导入对应 custom_ops 包后才可能挂到 torch_npu，不能据同名前缀认定为标准 TorchNPU/OpPlugin 内置接口。来源的产品支持和软件配套分别核对；这不是 `ascend_26_0_pt28` 标准包已内置该接口的声明。

## 接口

```text
custom.npu_swiglu_clip_quant(Tensor x, Tensor group_index, Tensor group_alpha, *, bool activate_left=False, int quant_mode=1, int clamp_mode=1) -> (Tensor, Tensor)
```

## 计算与返回

对 x 的一半施加 Swish、与另一半门控相乘，按 group_alpha 削波后动态量化。activate_left=True 激活左半，默认 False 激活右半；功能公式中的 A/B 名称不能取代这个参数方向。

包装层分配 y 为 INT8(TokensNum,H/2)，scale 为 FP32(TokensNum,)，返回二者；输入所有轴必须大于 0。文档没有完整明确削波 ReduceMax 的轴与异常值处理，不据文字公式生成未经核对的逐元素参考实现。

## 必须满足的条件

- 产品表只确认 A3 推理。x 为二维、连续 ND、BF16，H≤10496 且 64 对齐。
- group_index 是连续一维 INT64，每项为非负 token count；group_alpha 为对应一维 FP32，长度一致。不能直接传累计边界。
- count 总和不得超过 TokensNum；超过会越界。小于 TokensNum 时 y 和 scale 的未覆盖尾部不清理，是无效/垃圾数据，下游只能读取有效前缀。
- quant_mode 当前仅 1（动态），clamp_mode 仅 1。包装层包含字符串映射的 static 分支并不构成静态量化支持证明，不能按通用参数枚举放宽。
- 文档确认图模式，实际捕获和 GE 适配仍核对独立交付件。不得将其他 SwiGLU/量化接口的 dtype、分组和输出规则直接套用。

比较有效 token 前缀的量化输出与 scale，覆盖空组、未覆盖尾部和 activate_left 两个方向。


## 验证边界

核对自定义 .so、Schema、PrivateUse1/Meta 注册及所用图后端，分别比较输出、原地行为和多次调用。仅完成文档和包装层静态审阅；未分析完整 Device Kernel/Host/Tiling，未加载 .so、执行上游代码或进行设备数值和性能验证。

- [自定义算子交付与图适配](../../guides/integration/torchair/custom_operator_graph_contract.md)
- [软件栈基线](../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_swiglu_clip_quant.md)（primary）
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_swiglu_clip_quant.cpp)（implementation）
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp)（header）
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py)（constraint）
