---
type: API
title: npu_grouped_dynamic_mx_quant：组内分块与V2运行库门槛
description: 说明累计边界、按第0轴分组及E8M0容量，明确旧CANN分支对Optional默认值的拒绝。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_mx_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedDynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedDynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:34:54Z'
updated_at: '2026-11-09T21:57:27Z'
platforms:
- '950'
---

# npu_grouped_dynamic_mx_quant：组内分块与V2运行库门槛

## 固定版本与范围

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的950产品页、同提交Schema、Meta及包装实现。仅描述明确分支，不回推其他产品或发布基线；未执行上游代码、图编译或真机实验。

## 接口与数据结构

```text
npu_grouped_dynamic_mx_quant(x, group_index, *, round_mode='rint',
    dst_type=23, blocksize=32, scale_alg=0, dst_type_max=0.0)
    -> (y, mxscale)
```

x为二维(M,N)、FP16/BF16 ND，可非连续、支持空；group_index为非空一维INT32，非递减、非负、末值=M，是累计边界而非每组计数。按第0轴分组后每32元素量化，每组尺度数有独立偶数pad。

FP8的y同shape；FP4要求N偶数，实际UINT8的(M,N/2)，FP4输出不能按非连续布局处理。mxscale实际UINT8承载E8M0，物理容量(M//64+G,N,2)，该分配容量不表示每个元素都对应有效块；按组边界与pad解释。

FP8支持算法0/1且仅rint；FP4支持0/2与rint/round/floor。算法2的E2M1幅度参数为0或[6,12]，E1M2为0或[1.75,3.5]。blocksize只32，不从同名参数推导可调任意块。

## V2与默认值的实际边界

C++首次探测aclnnGroupedDynamicMxQuantV2并缓存结果，有V2才传scale_alg/dst_type_max。旧分支要求这两个Optional都**没有值**；但Schema省略时默认0/0.0仍是有值，因此不能把“没手动写参数”视为满足旧分支。显式None还会被进入分支前的C++算法检查拒绝，不能作为Eager或图路径的兼容修复；完整检查顺序见下文。

本卡优先描述包含V2的栈；具体CANN版本号未由这些源码给出，不猜测最低版本。文档列训练/推理和图模式，但每条运行库分支必须另核对。


## 验证

先检查逻辑dtype与容器、分组边界、尺度布局及后端接口版本，再对照同算法量化/反量化结果，覆盖尾块和空组。性能比较分开记录编译、内存和稳态开销；静态Meta和包装分配不是设备结果。

## 完整旧分支与None冲突修正

主线中英文仅950DT，默认确定性及训练/推理、图模式均为公开声明，未确认PR。group_index示例[4,8]表示[0:4]与[4:8]，并非起点列表；包装注释也写不带起始0、末值为M。边界非递减允许相等，不擅自改为严格递增。每组独立pad后的尺度容量M//64+G不等于有效scale总数。

主线C++在探测V2前已经要求Optional scale_alg等于0/1/2，因此显式None会先被该检查拒绝。无V2的旧分支又要求scale_alg和dst_type_max都无值，和前面的要求矛盾：不能把显式None写成Eager兼容办法，也不能把省略时的默认0/0.0当无值。此为固定源码的静态冲突，不是已执行的失败实验；使用含V2的已配套栈仍需实际核验。

固定发布Meta和TorchAir仅接受FP8 E4M3FN/E5M2、rint、blocksize=32，发布schema/包装也没有新算法和幅度属性；主线才扩FP4并重打包UINT8。主线E1M2可算法2及[1.75,3.5]幅度，不能套双轴接口E1M2仅算法0的矩阵。主线Converter的单项检查更宽，不能代替公开dtype×算法×舍入组合校验；文档的指数位描述也不当独立数值参考。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_mx_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedDynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedDynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
