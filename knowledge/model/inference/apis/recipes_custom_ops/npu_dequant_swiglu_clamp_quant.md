---
type: API
title: custom.npu_dequant_swiglu_clamp_quant：A3 INT8 输出与变体门控
description: 聚焦二维 INT8 输出路径，明确静态/动态量化、反量化输入及变体截断的区别。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_dequant_swiglu_clamp_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_dequant_swiglu_clamp_quant.cpp
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

# custom.npu_dequant_swiglu_clamp_quant：A3 INT8 输出与变体门控

## 来源与交付范围

依据 Recipes 固定提交 `944d2d3ece86f7df33dbb0cb155c72ca619a9c66` 的独立接口文档、Schema 与 PyTorch 包装层。该接口在 `torch.ops.custom` 注册；安装并导入对应 custom_ops 包后才可能挂到 torch_npu，不能据同名前缀认定为标准 TorchNPU/OpPlugin 内置接口。来源的产品支持和软件配套分别核对；这不是 `ascend_26_0_pt28` 标准包已内置该接口的声明。

## 接口

```text
custom.npu_dequant_swiglu_clamp_quant(Tensor x, *, Tensor? weight_scale=None, Tensor? activation_scale=None, Tensor? bias=None, Tensor? quant_scale=None, Tensor? quant_offset=None, Tensor? group_index=None, bool activate_left=False, int quant_mode=0, int? dst_type=None, int? round_mode=None, int? activate_dim=None, int swiglu_mode=0, float clamp_limit=7.0, float glu_alpha=1.702, float glu_bias=1.0) -> (Tensor, Tensor)
```

## 本卡覆盖路径

产品表确认 A3 推理；本卡限定二维 x=(TokensNum,H)、末轴切分、INT8 输出 dst_type=1，返回 (y,scale)。包装层默认 dst_type=1、round_mode=0(rint)、activate_dim=-1。其他切分轴以及 FP8/FP4 编码不纳入本卡调用配方，不能只凭枚举或 byte 分配代码推定物理打包约束。

## 反量化与门控

x 支持 INT32/FP16/BF16、连续 ND。INT32 必须提供 FP32 weight_scale，可选 activation_scale 和 bias；非 INT32 路径不允许提供这三项。weight_scale 为 H 或 (groupNum,H)，activation_scale 为 (TokensNum,1)，分组输入按来源逐项核对。

swiglu_mode=0 是标准 SiLU 门控；1 在激活支路仅做上界 clamp，另一支路做正负对称 clamp，再计算 sigmoid(glu_alpha*激活值) 与另一支路加 glu_bias 的乘积。默认 clamp_limit=7、glu_alpha=1.702、glu_bias=1，仅在变体模式生效。它与另一接口基于 group_alpha 的削波不是同一个规则。

## 量化与输出

H 必须为偶数，输出末维 H/2≤5120。quant_mode=0 时 quant_scale、quant_offset 都必须提供；=1 时不接受 quant_offset。文档列举的 round_mode 编码 0/1/2/3/4 分别对应 rint/round/floor/ceil/trunc，必须验证采用的舍入方式。

y 为 INT8(TokensNum,H/2)，scale 为 FP32(TokensNum,)；静态模式文档只称 scale 为固定值，没有给出可供通用调用方依赖的数值常量，不把它当作动态反量化 scale 使用。group_index 是每组 token count，不是累计边界；不要因相近接口允许某种 scale 广播就推定本接口也允许。

先在非分组、二维末轴、明确量化模式的路径比较输出与有效 scale，再扩展到实际 MoE 分组。


## 验证边界

核对自定义 .so、Schema、PrivateUse1/Meta 注册及所用图后端，分别比较输出、原地行为和多次调用。仅完成文档和包装层静态审阅；未分析完整 Device Kernel/Host/Tiling，未加载 .so、执行上游代码或进行设备数值和性能验证。

- [自定义算子交付与图适配](../../guides/integration/torchair/custom_operator_graph_contract.md)
- [软件栈基线](../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_dequant_swiglu_clamp_quant.md)（primary）
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_dequant_swiglu_clamp_quant.cpp)（implementation）
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp)（header）
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py)（constraint）
