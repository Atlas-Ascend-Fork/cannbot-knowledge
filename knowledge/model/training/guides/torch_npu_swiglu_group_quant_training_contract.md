---
type: Guide
title: SwiGLU Group Quant训练接入：默认模式、占位输出与自动求导
description: 核对OpPlugin Group Quant仅mode2/3的HiF8分配、忽略的dst_type、Meta空值分歧及grads[2]自动求导依赖。
tags:
- task.implementation
- topic.compute.quantization
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluGroupQuantKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluGroupQuantBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_group_quant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_group_quant_backward.py
  role: example
created_at: '2026-11-10T11:58:33Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# SwiGLU Group Quant训练接入：默认模式、占位输出与自动求导

## 固定来源与同名实现边界

本卡定向审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的SwiGLU Group Quant前向、显式反向、Schema、Meta及derivatives配置。发布`dedc316708372c9a8bfde4527abd2a94b74840f5`无这两份同路径C++，仅作为准确tree差异，不能据此否定其余发布实现。完整平台和软件配套未知，保留draft、空平台；未执行上游、生成自动求导代码或做设备实验。

Recipes同名融合接口的[MXFP8尺度补齐修复](../../inference/runbooks/precision/swiglu_mxfp8_scale_padding_nan.md)及[模型激活默认失配](../../inference/runbooks/runtime/shared_fused_op_default_spec_mismatch.md)各有自己的固定实现/调用层。本快照的参数为clamp_limit，不是clamp_value；以下包装只明确构造HiF8输出，不将Recipes的FP8/MX算法和修复自动套到本接口。

## 三输出前向与显式反向分别消费

```text
npu_swiglu_group_quant(x, *, weight=None, group_index=None, scale=None,
  dst_type=291, quant_mode=0, block_size=0, round_scale=False,
  clamp_limit=-1.0, dst_type_max=15.0, output_origin=False)
  -> (y, y_scale, y_origin)

npu_swiglu_group_quant_backward(grad_y, x, *, weight=None,
  y_origin=None, group_index=None, clamp_limit=0.0)
  -> (grad_x, grad_weight)
```

SwiGLU先将x尾轴减半。C++只检查尾轴偶数，没有完整rank下限、输入类型/空组/scale值或clamp合法矩阵；Meta甚至不复刻这个奇数检查，直接整数除2推导shape。训练调用方应先固定激活两半、钳位语义和真实分组范围，再核对目标后端，不用Meta成功扩展输入域。

## 默认quant_mode=0没有在C++形成完整输出分支

Schema默认quant_mode=0，但C++只有在mode2或3时才初始化y_acltype=ACL_HIFLOAT8并分配UINT8 y，随后分别建立scale；其他mode没有在本函数的结果初始化分支，却仍继续构造wrapper、读取y_scale.scalar_type并调用ACLNN。不能把默认参数可绑定当作默认调用已受支持，也不从该静态缺口推导具体设备异常已经复现。

同一C++的dst_type虽在函数签名中接收，却没有参与实际类型选择或直接下传，ACLNN得到的是分支构造的y_acltype。因此传另一个dst_type不使这个快照自动变成FP4/FP8/MX量化路径。Schema的291与Meta函数签名默认296、dst_type_max的15.0与0.0还不同；调用Schema、直接调Meta helper和底层分配是不同层次，不把它们合成统一默认配方。

## mode2/3的尺度与原始输出

令S为x尾维减半后的shape，C++分配合同如下；这是前端容量/容器观察，不定义完整量化数学或所有参数的合法组合。

| 返回 | Eager分配与后端解释 | Meta差异 |
| --- | --- | --- |
| y | mode2/3都为UINT8[S]，wrapper标记HiF8 | 所有mode均分配UINT8[S]，不能验证C++默认分支有效。 |
| y_scale，mode2 | FP32[0]空Tensor | 同为[0]。 |
| y_scale，mode3 | group_index已定义则同其shape，否则FP32[1] | 只有group_index非None且numel>0才按其shape，否则[1]；已定义空组与Eager不同。 |
| y_origin | output_origin=True时按S、x.options分配；False时为x dtype的[0]空Tensor | 开启时同形状，关闭时为None，不能把None、空Tensor混成同一结构。 |

HiF8字节容器不是普通UINT8数值；尺度这里为FP32，不是两轴MX的E8M0字节对。不要用view或数值cast替代真实解码，也不要把同名的SwiGLU MX双轴四输出协议接到本组三输出上。

## 显式反向的weight和origin依赖

反向C++按x.sizes/options分配grad_x。weight存在且defined时按weight的shape/options分配grad_weight，否则返回FP32[0]；Meta以weight.numel()>0判断，有定义但为空的weight可能进入不同dtype占位分支。反向同样仅显式检查x尾维偶数，没有完整校验grad_y、y_origin、weight和group_index的配对内容。

前向的scale、block_size、round_scale、dst_type及quant_mode不是显式反向参数，不能从接口名字推导任意量化输出的梯度规则。需要先明确grad_y是对应哪个数学结果的梯度、y_origin来自哪个未量化中间值，以及weight梯度如何累加，再验前反向耦合。

## derivatives文件不等于自动训练已经闭环

固定配置写为：

```text
x, weight: npu_swiglu_group_quant_backward(
  grads[0], x, weight, grads[2], group_index, clamp_limit)
```

它把**第三输出的梯度grads[2]**放到显式反向的y_origin位置，并非直接把前向第三输出result[2]保存并传回。配置中也没有此条目的额外输出可微性说明；最终生成代码和autograd的dtype/未定义梯度处理未在本卡执行核对。该映射与“反向需要前向origin”的调用假设必须重新核对，不能只看存在derivatives条目就认证自动求导正确。

两份测试各只有一个方法。前向只选mode3、output_origin=True及HiF8参考，reference内部调用NPU dtype cast，并未用传入scale、dst_type或block_size去验证全部算法。group_index随机生成两组大小，未保证与8行输入形成完整有效覆盖。显式反向测试用独立随机y_origin直接调用backward，没有先调用真实前向，也没有运行自动autograd或完整训练步；它不能检查上述grads[2]数据依赖。

接入时先以非均匀小输入分别核对合法mode、容器/尺度、输出origin、空组与weight省略，再用真实前向输出构造显式梯度和独立数学参考；另用自动求导路径比较x/weight梯度、output_origin开关及跨步累加。未建立该闭环前，不以单个融合调用或测试名称宣称训练数值和性能均已验证。融合收益应包含量化、激活、weight梯度及保存中间值的内存成本，本卡无性能数字、设备运行或新增verified。

## 测试数学参考的完整边界

前向参考将x转FP32并展平为[token,2H]，左右两半为x0/x1。clamp_limit不等于0时，x0只做上限钳位、x1做对称钳位；之后计算silu(x0)*x1，再按可选weight逐token相乘。output_origin取此结果转回输入dtype，group_index按**每组长度**累加end，不是累计端点；每组absmax至少取1e-8，再除dst_type_max并通过NPU dtype cast得到HiF8字节。无组分支用全张量absmax。参考没有按quant_mode分支实现mode2，也未使用传入scale、block_size、round_scale或dst_type确定不同数学，因此不能拿它验证那些属性。

反向参考若weight存在，先计算grad_weight=sum(grad_y*y_origin,最后一轴)，再把grad_y乘weight；对钳位后的x0计算sigmoid(x0)*(1+x0*(1-sigmoid(x0)))，左右梯度分别乘x1和silu(x0)。clamp_limit非零时，原x0<limit、-limit<原x1<limit的严格掩码决定梯度，端点也被截断；若有group_index，前sum(group_index)行以外的grad_x和grad_weight均清零。这些是测试参考的规则，包装本身没有计算这些公式或验证长度总和。

前向114行测试只调用一个Ascend950方法，x=[8,16]、weight=[8,1]、随机两组长度为1..9、mode3、limit=0.01、dst_type_max=15和output_origin=True，比较三个返回。反向115行测试只调用一个Ascend950方法，x=[4,16]、grad_y/origin=[4,8]、weight=[4,1]、group_index=None、limit=5，比较grad_x/grad_weight；origin为独立随机输入。两文件均在导入层关闭allow_internal_format，不构成所有格式、空weight、组截断和无weight分支的设备覆盖。本卡仅静态审阅，没有执行这些测试或导入模块。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluGroupQuantKernelNpuOpApi.cpp)（primary）

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluGroupQuantBackwardKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [固定实现来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_group_quant.py)（example）

- [固定实现来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_group_quant_backward.py)（example）

## 本卡核对范围

- [SwigluGroupQuantKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluGroupQuantKernelNpuOpApi.cpp)（primary）：1–101；完整本地文件。
- [SwigluGroupQuantBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluGroupQuantBackwardKernelNpuOpApi.cpp)（implementation）：1–48；完整本地文件。
- [test_npu_swiglu_group_quant.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_group_quant.py)（example）：1–114；完整本地文件。
- [test_npu_swiglu_group_quant_backward.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_group_quant_backward.py)（example）：1–115；完整本地文件。
