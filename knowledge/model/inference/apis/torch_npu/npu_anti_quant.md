---
type: API
title: 整数量化反变换（torch_npu.npu_anti_quant）
description: torch_npu.npu_anti_quant：整数权重反量化为浮点，以 scale 和可选 offset 恢复量化数据；区别于动态量化和量化参数位域编码。 说明 (x+offset)*scale 的符号约定及INT32承载INT4的尾轴展开，不与通用零点减法混同。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_anti_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_anti_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_anti_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_anti_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AntiQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AntiQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_anti_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_anti_quant.py
  role: implementation
created_at: '2026-11-10T03:38:40Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_anti_quant
---


# npu_anti_quant：偏移符号、反量化轴与逻辑 dtype

## 版本和支持范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，按产品表和具体参数分支使用，不回推发布基线，不从单页类型名单推导任意混合组合。未执行上游代码、设备算子或图编译。

## 接口与公式

```text
torch_npu.npu_anti_quant(x, scale, *, offset=None,
    dst_dtype=None, src_dtype=None) -> Tensor
```

公式是cast((x+offset)*scale)，无offset则cast(x*scale)，不是一律(x-zero_point)*scale；传入的offset符号要符合该约定。x/scale不能None，x最大8维ND，可非连续、支持空；输出FP16默认或BF16，输入INT8或INT32打包的INT4，950另支持FP8/hifloat8。

## 轴和产品限制

A2/A3的scale为一维、FP32/BF16，长度1或尾轴；INT32打包时按展开后的INT4尾轴8倍匹配。950还允许与x同rank的scale，最多一个非1维且只可在最后两轴；一维scale长度1、末轴或倒数第二轴，x一维时只能1或同长度。950 FP8/hifloat8输入的scale仅FP32。offset同scale shape/dtype，不能任意广播到高维多轴。

文档对src_dtype同时提默认INT8与不传自动推断，Schema默认None，应按实际x与逻辑类型核对。INT32容器不能解释为普通INT32量化数值；950的src_dtype可明确int4/hifloat8/FP8，A2/A3按各自INT8/quint4x2范围。仅因容器都是UINT8，也不能互换hifloat8和普通整数量化。

支持训练/推理及单算子/TorchAir，仍不表示任意混合精度、空shape和反向组合均由本次验证。


## 验证

先核对计算顺序、分组语义、scale方向与真实存储形状，再比较量化/反量化数值；覆盖空组、尾块、非连续和打包解码的实际需要。分别测内存与稳态收益，本文只有静态证据。

## 发布、双语轴约束与实际展开

发布中文只给INT8/打包INT4及一维scale；主线中英文新增950PR及950DT的HiFloat8/E4M3FN/E5M2，FP8/HiFloat8的scale与offset都只能FP32。主线中文允许950的scale为一维或同x秩、最多一个非1轴且只能最后两轴，英文总参数仍只写一维；两种文字不互相抹去。A2/A3产品段仍只确认一维尾轴/标量scale。

两固定包装在src_dtype省略时按实际物理dtype选择，显式给定时检查匹配；INT32必须解释为INT4，不能把页面“默认INT8”当成强制用INT8解码INT32。UINT8作为HiFloat8承载并按该逻辑类型包装，不是普通无符号整数反量化。

INT32输入的输出尾轴乘8，标量INT32直接拒绝；两版Meta与两个固定TorchAir Converter同样展开，后者先Bitcast为INT4再Reshape。普通INT8/FP8不扩尾轴。src/dst类型的转换与输出形状并不证明scale广播、极值或全套设备组合已经验证。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 整数量化反变换：torch_npu.npu_anti_quant

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

以 scale 和可选 offset 将整数量化值恢复到目标浮点类型。

### 文档签名

```text
torch_npu.npu_anti_quant(x, scale, *, offset=None, dst_dtype=None, src_dtype=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

反变换为 `(x + offset) * scale` 后转换到目标 dtype。该版 scale 为一维，int32 打包 int4 输入的尾维关系与 int8 不同；不能将 int32 的逻辑元素数当成普通 int32 权重。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_anti_quant.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_anti_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_anti_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_anti_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AntiQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AntiQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_anti_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_anti_quant.py)（implementation）
