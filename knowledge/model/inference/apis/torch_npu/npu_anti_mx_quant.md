---
type: API
title: npu_anti_mx_quant：E8M0配对、FP4展开与None差异
description: 说明MX反量化的尾轴和配套尺度，区分省略src_type与显式None触发不同默认分支。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_anti_mx_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AntiMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_anti_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_anti_mx_quant.py
  role: implementation
created_at: '2026-11-09T06:34:54Z'
updated_at: '2026-11-09T21:57:27Z'
platforms:
- '950'
---

# npu_anti_mx_quant：E8M0配对、FP4展开与None差异

## 固定版本与范围

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的950产品页、同提交Schema、Meta及包装实现。仅描述明确分支，不回推其他产品或发布基线；未执行上游代码、图编译或真机实验。

## 接口与计算

```text
npu_anti_mx_quant(x, mxscale, *, axis=-1,
    dst_type=15, src_type=292) -> Tensor
```

按量化值乘E8M0尺度解码后的2的指数；这与普通FP32乘法scale的anti_quant不同。x为rank1..7，mxscale为rank2..8，尺度逻辑E8M0、实际UINT8、尾轴2。文档只支持尾轴axis=-1或D-1；C++只做轴范围检查不能证明其他轴受支持。

FP8输入为真实FP8 Tensor，可非连续，输出同shape；FP4输入为连续UINT8打包，每字节两个逻辑值，输出末轴扩大2倍。src_type须匹配实际输入逻辑类型，dst_type可FP16/FP32/BF16，默认BF16。

建议与block_size=32的npu_dynamic_mx_quant配套，保留其尺度pad布局。FP4的物理x末轴只有原逻辑长度一半，不能把文档中的x形状公式机械套到物理字节数去重造mxscale；实际配对与逻辑长度单独核验。

## 省略参数不等于None

Schema省略src_type时默认292（E4M3FN）；但C++ Optional未取值即显式None时回到内部默认296（FP4 E2M1）。因此None不是自动按x推断，也不等于省略。Meta则按x的物理dtype区分FP8/FP4，不能用Meta成功证明错误src_type的Eager路径可用。明确指定与量化输出一致的逻辑类型更便于核对。

- [普通反量化接口](npu_anti_quant.md)
- [基础MX量化](npu_dynamic_mx_quant.md)


## 验证

先检查逻辑dtype与容器、分组边界、尺度布局及后端接口版本，再对照同算法量化/反量化结果，覆盖尾块和空组。性能比较分开记录编译、内存和稳态开销；静态Meta和包装分配不是设备结果。

## 完整双语与TorchAir接线

主线中英文只确认Ascend950的PR及DT产品，训练/推理、单算子和图模式；不能把元数据中的950扩为所有产品形态。src_type的291/292分别表示E5M2/E4M3FN，296/297分别表示FP4 E2M1/E1M2，dst_type的5/6/15表示FP16/FP32/BF16。用实际逻辑类型明确指定，不能把UINT8容器当普通整数输入。

尺度按逻辑量化轴长度L分为32元素组，再将组数配对为(ceil(ceil(L/32)/2),2)。FP4物理x的尾维仅L/2，而反量化输出为L，配套尺度应来自原量化结果；中英文公式仍用x.shape写分组长度，不能直接按打包后的字节长度自行重建。C++只校验x/mxscale秩及axis范围、并展开FP4输出，没有在这层完整检查配套尺度。

固定TorchAir主线Converter先校验逻辑类型与x物理类型匹配，UINT8路径Bitcast成FP4并把尾轴扩大2，再接GE AntiMxQuant；它直接传mxscale，没有替调用者把原始UINT8转成E8M0。中英文图例在编译forward之外显式用view恢复尺度逻辑类型，这不是数值cast，也不是完整图兼容保证。Meta不消费src_type/mxscale内容来验证配对；省略src_type与显式None的差异仍按上文保留。固定发布快照没有该公开页及本接口包装/Converter，缺文件不等同于证明全部安装版本不支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_anti_mx_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AntiMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_anti_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_anti_mx_quant.py)（implementation）
