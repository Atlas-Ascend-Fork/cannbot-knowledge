---
type: API
title: 量化散点更新：保留原输入（torch_npu.npu_quant_scatter）
description: torch_npu.npu_quant_scatter：量化散点更新：保留原输入。量化 updates 后按 axis 与 indices 写入新输出，保留原 input。 区分复制返回与原地更新，记录 A2/950 的 dtype、取整、索引不重叠和图转换边界。
tags:
- task.lookup
- topic.precision
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_scatter.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_scatter.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_scatter_.md
  role: constraint
created_at: '2026-11-10T03:38:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
aliases:
- torch_npu.npu_quant_scatter
- 非原地量化散点更新
---


# npu_quant_scatter 与原地变体：量化写回、索引和 V2 参数

## 固定版本与产品

依据OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 两份API页、Schema、Meta与C++包装，图模式另读TorchAir `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。产品页支持Atlas A2与950PR/950DT，另列Atlas推理系列；本卡平台仅登记A2/950，不增加A3。主线组合配套仍需核对，不回推已固定发布组合。

## 两种写回契约

```python
torch_npu.npu_quant_scatter(self, indices, updates, quant_scales,
    quant_zero_points=None, axis=-2, quant_axis=-1, reduce='update',
    dst_type=None, round_mode='rint') -> Tensor
torch_npu.npu_quant_scatter_(self, indices, updates, quant_scales,
    quant_zero_points=None, axis=-2, quant_axis=-1, reduce='update',
    dst_type=None, round_mode='rint') -> Tensor
```

先量化updates，再按indices和axis替换目标self的数据段；仅支持reduce='update'，不是加法归约。无下划线版本C++先clone(self)，修改副本并返回，原self数据保留；原地版本修改self并返回同一Tensor，Schema用Tensor(a!)声明别名，Meta也直接返回self。两者输出shape/物理dtype都从self延续，dst_type是底层逻辑类型提示，不是任意self到新dtype的数值转换接口。原地页示例打印out[0]只是在取第一片，不能将其三维打印结果当作输出自动降维。

## 输入形状与确定性边界

self为ND、rank 3..8；updates同rank，首维等于indices首维且≤self首维，axis轴长度≤self对应轴，其余轴相等，updates末轴需32B对齐。axis不能选首轴或末轴，quant_axis只能选末轴，默认分别-2/-1。quant_scales及可选quant_zero_points的元素数等于updates末轴长度。

indices为INT32 ND，只能1维或二维且第二维大小2。调用方保证索引合法，框架不检查越界；映射到self的数据段不得重叠，否则多核并发可导致重复执行结果不同。开启确定性或使用原地接口不解除不重叠要求。上述输入支持非连续Tensor，但仍需满足形状、对齐和量化组合。

A2的self仅INT8；950可INT8、hifloat8、E5M2或E4M3FN。updates/quant_scales/quant_zero_points允许的配对为BF16/BF16/BF16或FP16/FP32/INT32；不能按各参数单独列出的dtype任意交叉组合。zero_points=None表示不提供偏移，不改变scale长度和其余类型约束。

## 新参数、逻辑存储和回退

A2不支持额外指定dst_type/round_mode，按INT8/rint处理。950的dst_type=None仍表示INT8；INT8、E5M2、E4M3FN仅rint，hifloat8只支持round/hybrid，因此不能只设置hifloat8后保留默认rint。

C++仅在SoC≥950且aclnnInplaceQuantScatterV2符号存在时，把dst_type及round_mode传入V2；否则调用旧aclnnInplaceQuantScatter，两个新参数不参与。不要把旧入口成功返回当作指定FP8/取整配置已生效，需核对实际CANN符号与路径。本次未确定最低CANN版本。包装将已有self/result连同逻辑类型交给TensorWrapper，未先把全部原数据数值转换为dst_type；hifloat8等场景需准备正确的底层存储/编码，不能混用逻辑类型提示和数值cast。

C++不读取reduce字符串而固定update枚举，GE则继续传reduce；非法字符串在某一路径未被拒绝，不构成新增归约方式支持。

## 图模式与复制开销

产品页声明单算子和TorchAir图模式。当前非原地Converter先TensorMove，再调用QuantUpdateScatter，并校验输出逻辑类型和对应round_mode；源码中旧的“可能意外修改输入”注释不能覆盖当前明确复制路径。使用非原地形式要计入整份self复制开销，不能仅按updates大小估算写回成本。

原地Converter签名仍是旧形式，缺dst_type/round_mode，默认axis=0、quant_axis=1也与公开接口不同；注释说明通常经functionalization转为非原地，保留它用于某些重新原地化路径。不能把原地单算子的V2能力直接推广为该直接Converter支持所有新参数，也不要采用旧Converter默认值替代公开-2/-1；入图时显式传轴，检查functionalization、最终节点和副作用保留。Meta只empty_like/返回self，不替代索引、dtype、量化和产品验证。

## 核验

保存输入副本，分别核对非原地版本的self保持、原地别名与写回结果；检查未更新区间、合法边界索引、配对dtype、32B对齐和所选取整。图模式再核对TensorMove、最终节点属性和实际CANN路径。示例中的eager/graph打印不是本次运行结果，本次未执行NPU、数值或性能测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布默认轴错误与两固定后端

完整发布两页把axis/quant_axis写为0/1，与同页“非首尾更新轴、末轴量化”及示例-2/-1不一致；两版schema实际都是-2/-1且已有dst_type/round_mode。主线中文两页及英文原地页已修，英文功能页的quant_axis参数段仍误写1，不能用这行覆盖实际声明。

发布页只确认A2及旧Atlas推理，主线950PR/DT新逻辑类型按上文消费，两版均未列A3。两固定C++都已有V2符号/SoC选择，旧路径忽略两个新参数；不因发布源码有FP8分支便扩大其公开合同。两个固定TorchAir非原地Converter都有TensorMove，旧警告文字不覆盖实际复制；直接原地Converter仍为旧签名与0/1默认，缺新参数，需保留函数化/重新原地化边界。

主线功能示例已改为打印完整输出，原地例仍打印out[0]；这些都是文档静态样例，没有在本次运行。索引不重叠按实际目标数据段核对，不能用样例随机值或切片打印作全量写回和数值验收。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 量化散点更新：保留原输入：torch_npu.npu_quant_scatter

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

量化 updates 后按 axis 与 indices 写入新输出，保留原 input。

### 文档签名

```text
torch_npu.npu_quant_scatter(input, indices, updates, quant_scales, quant_zero_points=None, axis=0, quant_axis=1, reduce='update') -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

返回新输出与原地版本的副作用不同，图捕获时应核对调用重载与别名。该文档只明确列出 A2。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_scatter.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter_.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantScatterKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_scatter.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_scatter.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantScatterKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_scatter.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_scatter_.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_scatter_.md)（constraint）
