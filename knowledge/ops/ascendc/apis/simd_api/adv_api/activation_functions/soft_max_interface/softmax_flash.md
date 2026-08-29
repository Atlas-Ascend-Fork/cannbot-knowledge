---
type: API
title: SoftmaxFlash
description: Softmax增强版本，可根据上一次Softmax计算的sum和max更新本次结果，适用于last轴切轴场景，不开启update时等同于SoftMax。即将废弃，建议使用SoftmaxFlashV2。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlash.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxFlash

注意：该接口后续即将废弃，请使用精度和性能更好的SoftmaxFlashV2接口。 Softmax增强版本，除了可以对输入tensor做SoftmaxFlash计算，还可以根据上一次Softmax计算的sum和max来更新本次的Softmax计算结果。last轴切轴的情况，每次计算的reduce结果并非是全轴的，需要根据上一次Softmax计算的sum和max来更新本次的Softmax计算结果，可以使用该增强接口。

函数原型：template <typename T, bool isReuseSource = false, bool isBasicBlock = false>

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：该参数预留，传入默认值false即可。
- isBasicBlock：srcTensor和dstTensor的shape信息和Tiling切分策略满足基本块要求的情况下，可以设置为true开启该参数用于提升性能，默认为false表示不开启。是否满足基本块的要求，可以采用如下两种方式之一判断：srcTensor和dstTensor的shape信息[m,n]需要满足如下条件：尾轴长度n小于2048并且大于等于256/sizeof(T)（即half场景下n最小为128，float场景下n最小为64），同时n是64的倍数；非尾轴长度的乘积m为8的倍数。

约束：
- srcTensor和dstTensor的空间可以复用，maxTensor和inMaxTensor的空间可以复用，sumTensor和inSumTensor的空间可以复用。
- sumTensor、maxTensor、expMaxTensor、inSumTensor、inMaxTensor的Tensor空间，last轴长度必须固定32Byte。
- 操作数地址对齐要求请参见通用地址对齐约束。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [SoftmaxFlash Tiling接口](softmax_flash_tiling_interface.md)（`related`）：“注意：该接口后续即将废弃，请使用精度和性能更好的SoftmaxFlashV2接口。 Softmax增强版本，除了可以对输入tensor做SoftmaxFlash计算，还可以根据上一次Softmax计算的sum和max来更新本次的Softmax计算结果。”与“注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。”分别给出两端正文事实；Kernel 侧 SoftmaxFlash 的 update 计算依赖 Host 侧同名 tiling 参数，二者共同构成旧版接口的调用合同与迁移警告。
<!-- cannbot:related:end -->
