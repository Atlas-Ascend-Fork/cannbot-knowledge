---
type: API
title: 逐块动态量化（torch_npu.npu_dynamic_block_quant）
description: torch_npu.npu_dynamic_block_quant：对输入张量，通过给定的`row_block_size`和`col_block_size`将输入划分成多个数据块，以数据块为基本粒度进行量化。 按行列块划分输入后，逐块计算 scale 并逐块量化；返回量化结果和每块的 scale。 区分发布INT8固定块与主线产品扩展，明确950类型、尺度形状及V2幅度参数门槛。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_block_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicBlockQuantNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicBlockQuantNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_dynamic_block_quant
---


# npu_dynamic_block_quant：发布版与主线的分块量化矩阵

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_dynamic_block_quant(x, *, min_scale=0.0, round_mode="rint", dst_type=1, row_block_size=1, col_block_size=128) -> (Tensor, Tensor)
```

以 block 为粒度产生量化结果 y 与 scale。该固定提交的参数支持范围只有 INT8：dst_type=1、row_block_size=1、col_block_size=128、round_mode="rint"。功能概述出现 FP8/HiF8 公式，不代表当前参数表允许这些输出。

## 参数与组合限制

x 支持二维或三维 FP16/BF16 ND、非连续 Tensor；min_scale 必须非负。不要将 block scale 作为普通 pertoken scale 直接传入其他算子，须核对下游要求的粒度、方向和布局。来源公式与示例中的 scale 表达需要结合实际安装包确认，本文不重写为未经核验的通用反量化公式。

## 验证与模型关联

用多个块、非满 128 尾块检查 y 和 scale 的布局及实际还原误差；拒绝把固定块大小当可自由调节的性能参数。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py#L1150)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线块大小和950类型矩阵

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 新增dst_type_max参数，但旧发布段的固定INT8、1×128仍只代表原版本，不将下列新范围回推。

|主线产品|输出与舍入|行块|列块|dst_type_max|
|--|--|--|--|--|
|A2/A3|仅INT8，rint|1|1或128|不支持扩展值|
|950|INT8/FP8 E4M3FN/E5M2为rint；hifloat8为round|1/128/256/512|64/128/192/256|仅hifloat8，0/15/56/224/32768|

x仍为二维/三维FP16/BF16 ND，可非连续，但不支持空。y同shape，scale为FP32，最后两轴按行列块大小向上取整；这是每块尺度，不等同于MX E8M0。hifloat8在产品页区分单算子/静态图UINT8与动态图bits8容器，不能因逻辑类型相同就直接沿用物理dtype判断。

包装探测aclnnDynamicBlockQuantV2，只有V2才传dst_type_max，旧入口静默不接收该值；未获得最低版本证据，按符号能力核对。主线仍列训练/推理、单算子与TorchAir图模式，具体dtype容器、尺度公式和实际支持需按所用分支验证。

## 发布声明、公式差异与图默认值

发布公开页未列dst_type_max，但同固定发布schema及包装已存在该参数，并已按aclnnDynamicBlockQuantV2能力选择是否下传；主线公开签名补出参数，不表示它首次出现于主线代码。两版探测结果均以静态变量缓存，旧入口不传该值，没有保证非零值一定报错。

发布公式把目标最大值放在分子，主线中英文改为input_max/目标最大值，均再写min(...,1/min_scale)；这与“最小scale阈值”的文字仍需消歧。主线又把FP8最大值统写448，不能作为E4M3FN/E5M2共同的通用数值参考。包装只接线和分配，没有在此计算scale，不能据其反推出正确舍入、全零块或min_scale=0的设备规则。

主线英文参数总述仍有“仅INT8/rint/行1/列128”的旧文字，随后又列950扩展；按中文及产品分段保存上述矩阵，不用旧总述覆盖细表。主线图示例特别限定950PR/DT，并使用FP8。

更窄的实际GE边界：两个固定TorchAir Converter在本文件重定义dtype转换，仅直接识别23/24或>=256扩展值；公开默认INT8的dst_type=1会在转换阶段抛错，不能据“支持图模式”宣称发布INT8默认路径已可由该Converter成图。主线仍按950的PR/DT、A2/A3及具体后端分开核对；不把更换dtype当A2/A3公开INT8合同的修复。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 逐块动态量化：torch_npu.npu_dynamic_block_quant

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

对输入张量，通过给定的`row_block_size`和`col_block_size`将输入划分成多个数据块，以数据块为基本粒度进行量化。

### 输入、输出与行为

按行列块划分输入后，逐块计算 scale 并逐块量化；返回量化结果和每块的 scale。不能用全张量共享的单个 scale 代替逐块结果。

### 文档签名

```text
torch_npu.npu_dynamic_block_quant(x, *, min_scale=0.0, round_mode="rint", dst_type=1, row_block_size=1, col_block_size=128) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_block_quant.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicBlockQuantNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicBlockQuantNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
