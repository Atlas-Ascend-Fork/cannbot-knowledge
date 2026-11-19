---
type: API
title: npu_grouped_dynamic_block_quant：分组FP8块与尺度容量
description: 说明行列块大小、累计边界和列向上取整，区分FP32尺度与MX E8M0布局。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_block_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedDynamicBlockQuantNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_block_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedDynamicBlockQuantNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_block_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_block_quant.py
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

# npu_grouped_dynamic_block_quant：分组FP8块与尺度容量

## 固定版本与范围

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的950产品页、同提交Schema、Meta及包装实现。仅描述明确分支，不回推其他产品或发布基线；未执行上游代码、图编译或真机实验。

## 接口与粒度

```text
npu_grouped_dynamic_block_quant(input, group_list, *, min_scale=0.0,
    round_mode='rint', dst_type=291, row_block_size=1,
    col_block_size=128, group_list_type=0, dst_type_max=0.0)
    -> (y, scale)
```

input为(M,N)或(B,M,N)、FP16/BF16 ND，支持空与非连续；group_list为一维INT32、非负非递减、末值等于M。文档有“起始索引”措辞，但group_list_type=0是累计边界，应依末值和实际分组解释，不直接把count列表传入。

row_block_size仅1/128/256/512，col_block_size仅64/128/192/256；min_scale≥0。FP8 E4M3FN/E5M2只rint，hifloat8需round/hybrid，不能沿用默认rint；后者dst_type_max为0或[0,32768]范围内非零值，0代表默认幅度。

scale为FP32，不是MX E8M0。C++和Meta明确列轴向上取整：二维物理分配(M//row_block_size+G,ceil(N/col_block_size))，三维增加B轴。文档的N/col简写不能当作无需pad的精确除法；组边界也可能引入额外容量，不能全部当有效尺度。

C++只按group_list_type=0调整尺度形状，其他值仅打印不支持信息，不把“未立刻抛异常”视为有效新模式。后端有V2时才传dst_type_max，旧接口不传；参数配置存在不证明已影响量化结果。训练/推理及单算子/图模式按实际运行库分别核验。


## 验证

先检查逻辑dtype与容器、分组边界、尺度布局及后端接口版本，再对照同算法量化/反量化结果，覆盖尾块和空组。性能比较分开记录编译、内存和稳态开销；静态Meta和包装分配不是设备结果。

## 全文分组语义与版本接线

主线中英文明确950PR及950DT、训练/推理和单算子/图模式。group_list虽被称作“起始索引”，group_list_type=0实际声明cumsum，例子和末值=M按累计结束边界理解；不能传每组计数代替。页面同时写group_list可为空，但为空就无法满足非空输入的末值条件，不能由局部空支持扩展出任意空组合。

行块分组后的scale形状是分配容量M//row+G、列轴ceil(N/col)，不是每个槽都代表有效group块，也不是对M简单ceil即可替换。两版Meta不读取边界内容，不能用Meta通过证明非负、非递减和末值已检查。C++对非0 group_list_type仅打印说明，仍不构成有效模式支持。

发布快照有schema、Meta、包装及GE Converter但无同名公开页；发布三处均没有dst_type_max，主线新增该参数，C++仅V2下传、旧入口忽略，主线GE则按属性传递。HiFloat8必须显式round或hybrid，默认rint只适合相应FP8；类型段末尾“/36”没有清楚给出别名合同，本卡不据它新增可移植dtype编码。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_block_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedDynamicBlockQuantNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_dynamic_block_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedDynamicBlockQuantNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_block_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_grouped_dynamic_block_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
