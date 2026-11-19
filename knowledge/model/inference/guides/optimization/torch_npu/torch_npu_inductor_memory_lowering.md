---
type: Guide
title: Inductor访存：间接索引、随路转置与地址复用
description: 区分950DT离散访存模式、NDDMA默认和输入输出复用对multi-buffer的影响。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/non_contiguous_accesses/INDUCTOR_INDIRECT_MEMORY_MODE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/non_contiguous_accesses/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/non_contiguous_accesses/arch.drawio.svg
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/TORCHINDUCTOR_NDDMA.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/ENABLE_INPLACE_BUFFERS.md
  role: primary
created_at: '2026-11-09T15:10:31Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# Inductor访存：间接索引、随路转置与地址复用

## 固定来源与范围

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf内部特性说明。间接访存变量页只列950DT并明确A2/A3不支持这类Inductor融合；概述则讨论950PR/DT硬件的SIMT能力，保留两种粒度，不把概述当作每个PR模式已独立验证。NDDMA和地址复用详情页也只列950DT。未执行代码、编译或设备实验，不回推发布基线。

## 间接load/store的三条候选

load类包括aten.embedding/index/gather/index_select，store类包括index_put/scatter。索引需先从GM读入再据它访问另一处GM；页面embedding示例注释把初始索引与load后数值写得不一致，只说明索引依赖，不把其注释当可复现数值测试。

INDUCTOR_INDIRECT_MEMORY_MODE默认simd_simt_mix，文档合法模式仅fallback与simd_simt_mix。fallback不进行这类融合、回Eager路径，不等于CPU计算；混合模式仍用tl.load/store描述，由Autotune选择纯SIMT、SIMT模板（间接搬运SIMT、其余SIMD）或纯SIMD优化候选，并以inductor_meta的npu_kernel_type=simd_simt_mix标识。选中模板名字不代表整个Kernel都是SIMT。

源码配置还容忍simt_template/simt_only等值，属于配置层额外分支，不作为公开文档模式推荐。架构SVG中的直接/间接分流、三种compile_mode及旧A5标签与正文共同核对；图中SIMD路线旁的A2/A3/A5标注不覆盖变量页明确的A2/A3融合排除。

## 随路转置与指针复用是另两种控制

TORCHINDUCTOR_NDDMA控制Triton-Ascend load随路转置，950DT默认1、其他代默认0，0/1关闭/开启。详情称A2/A3开启对性能无影响，不从此推定这两个产品支持950DT转置加速；也不把来源“明显增益”当本模型的实测收益。

ENABLE_INPLACE_BUFFERS未配或1/true/yes时输入输出参数可复用地址（如in_out_ptr），0/false/no等关闭后生成分开的in_ptr/out_ptr。复用会妨碍后端在load-compute-store间的multi-buffer流水，故关闭可能提供更多掩盖空间，但也改变缓冲使用，应同时测时间与内存，不能把不复用写成必然更快。

这里是编译生成Kernel参数空间的选择，不改变用户对原地操作、别名和生命周期的责任。按真实dtype/shape、索引分布、选定候选与稳态测量评估，不能从硬件具备SIMT或NDDMA就推定所有索引/转置均已融合。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/non_contiguous_accesses/INDUCTOR_INDIRECT_MEMORY_MODE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/non_contiguous_accesses/overview.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/non_contiguous_accesses/arch.drawio.svg)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/TORCHINDUCTOR_NDDMA.md)（primary）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/ENABLE_INPLACE_BUFFERS.md)（primary）
