---
type: API
title: SetValue
description: 设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
source_headers:
- include/basic_api/kernel_tensor.h
---

# SetValue<a name="ZH-CN_TOPIC_0000002167530617"></a>

## 功能说明<a name="section618mcpsimp"></a>

设置GlobalTensor相应偏移位置的值。

-   因为硬件实现不同，其与通用CPU标量赋值操作存在差异。SetValue赋值操作首先改写的是每个AI Core内部的DCache，不会立刻写出到Global Memory，且后续写出时以Cache Line（64B）为单位。使用该接口之前必须了解DCache结构和Cache一致性原理（参见[DataCacheCleanAndInvalid](../../cache_control/data_cache_clean_and_invalid.md)），否则可能存在误用的情况，**请谨慎使用。**
-   调用SetValue后，首先改写的是每个AI Core内部的DCache，如果需要立即写出到Global Memory，需要在调用此接口后，再调用[DataCacheCleanAndInvalid](../../cache_control/data_cache_clean_and_invalid.md)，确保DCache与Global Memory的Cache一致性。
-   多核操作GM地址时，要求不同核操作的地址（通过offset参数设置元素偏移，可以转换为地址）至少有Cache Line大小的偏移，否则会出现多核数据随机覆盖。同时需要考虑地址对齐（64B）的问题。详细内容请参考[调用示例](../../cache_control/data_cache_clean_and_invalid.md#section837496171220)。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void SetValue(const uint64_t offset, PrimType value)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  参数说明

<a name="zh-cn_topic_0235751031_table33761356"></a>
<table><thead align="left"><tr id="zh-cn_topic_0235751031_row27598891"><th class="cellrowborder" valign="top" width="13.94%" id="mcps1.2.4.1.1"><p id="zh-cn_topic_0235751031_p20917673"><a name="zh-cn_topic_0235751031_p20917673"></a><a name="zh-cn_topic_0235751031_p20917673"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="12.98%" id="mcps1.2.4.1.2"><p id="zh-cn_topic_0235751031_p16609919"><a name="zh-cn_topic_0235751031_p16609919"></a><a name="zh-cn_topic_0235751031_p16609919"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="73.08%" id="mcps1.2.4.1.3"><p id="zh-cn_topic_0235751031_p59995477"><a name="zh-cn_topic_0235751031_p59995477"></a><a name="zh-cn_topic_0235751031_p59995477"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row42461942101815"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="p151479166327"><a name="p151479166327"></a><a name="p151479166327"></a>offset</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p158449584436"><a name="p158449584436"></a><a name="p158449584436"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p126017529210"><a name="p126017529210"></a><a name="p126017529210"></a>偏移offset个元素。</p>
</td>
</tr>
<tr id="row16103112474710"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="p20103424124712"><a name="p20103424124712"></a><a name="p20103424124712"></a>value</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p1810310245476"><a name="p1810310245476"></a><a name="p1810310245476"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p5700191124716"><a name="p5700191124716"></a><a name="p5700191124716"></a>设置值。PrimType类型。</p>
<p id="p16103102414471"><a name="p16103102414471"></a><a name="p16103102414471"></a><span id="ph169021373405"><a name="ph169021373405"></a><a name="ph169021373405"></a>PrimType定义如下：</span></p>
<a name="zh-cn_topic_0000001491300625_screen115348581718"></a><a name="zh-cn_topic_0000001491300625_screen115348581718"></a><pre class="screen" codetype="Cpp" id="zh-cn_topic_0000001491300625_screen115348581718">// PrimT用于从T中提取基础数据类型：T传入基础数据类型，直接返回数据类型；T传入为TensorTrait类型时萃取TensorTrait中的LiteType基础数据类型
using PrimType = PrimT&lt;T&gt;;</pre>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

无。

## 约束说明<a name="section633mcpsimp"></a>

无。

## 调用示例<a name="section17531157161314"></a>

```cpp
// aGlobal数据 [1, 1, 1, 1, 1]
AscendC::GlobalTensor<T> aGlobal;
T val = 0;
aGlobal.SetValue(2, val);

//结果如下
aGlobal数据 [1, 1, 0, 1, 1]
```


<!-- cannbot:related:start -->
## 相关

- [GM SetValue 写回后 GetValue 读到旧值](../../../../../runbooks/precision/gm_setvalue_getvalue_reads_stale_within_kernel.md)（`exemplifies`）：“关键点：ProcessR 用 `CopyOutArray(rOutLocal, rOutGm_, n_)`（即 `rOutGm_.SetValue(...)`）把 r_out 写回 GM，ProcessC 同样把 c_out 写回 GM；ProcessU 随后用 `rOutGm_.GetValue(i)` 与 `CopyInArray(cOutLocal, cOutGm_, m_)` 再从 GM 读回。读回的值并未反映本 Kernel 刚写入的更新。”复现同 Kernel 写后读旧值，而“设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。”给出 SetValue 的 DCache 一致性合同；runbook 直接示范违反该合同的故障。
- [DataCacheCleanAndInvalid](../../cache_control/data_cache_clean_and_invalid.md)（`related`）：设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。；清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。。SetValue 明确产生 DCache 写入，DataCacheCleanAndInvalid 提供写回并失效的可见性动作，联合阅读可闭合 GM 一致性处理。
- [operator](operator_call.md)（`related`）：返回值为指定索引位置的 PrimType 类型引用，用于左值相当于 SetValue，用于右值相当于 GetValue。；设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。。GlobalTensor operator() 卡明确左值语境等价于 SetValue，SetValue 卡说明指定偏移写入及 DCache 一致性要求，二者连接运算符重载与显式写接口。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 14 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [NMS 950 Direct Invoke 算子知识](../../../../../operators/direct/cv/image/nms_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 219 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/experimental/image/nms_with_mask/op_kernel/nms_with_mask.h#L219)
- [MaskedSelect A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/masked_select.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 162 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/masked_select_v3/op_kernel/masked_select_v3.h#L162)
- [ForeachNonFiniteCheckAndUnscale A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_non_finite_check_and_unscale.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 197 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_non_finite_check_and_unscale/op_kernel/foreach_non_finite_check_and_unscale_n_d.h#L197)
- [MoeDistributeCombine A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_combine.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 291 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_a2_layered_aicpu.h#L291)
- [AddLora A2 ACLNN 算子知识](../../../../../operators/aclnn/math/math/add_lora.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 607 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/add_lora/op_kernel/add_lora_base.h#L607)
- [ForeachNonFiniteCheckAndUnscale 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_non_finite_check_and_unscale_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 142 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_non_finite_check_and_unscale/op_kernel/arch35/foreach_non_finite_check_and_unscale_regbase.h#L142)
- [MoeDistributeCombineSetup 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_combine_setup_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 238 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_setup/op_kernel/arch35/moe_distribute_combine_setup_arch35.h#L238)
- [CrossEntropyLoss 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/loss/cross_entropy_loss_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 54 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/loss/cross_entropy_loss/op_kernel/arch35/cross_entropy_loss_empty.h#L54)
- [MoeDistributeDispatch A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 321 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_a2_layered.h#L321)
- [AddLayerNormGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/add_layer_norm_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 49 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_layer_norm_grad/op_kernel/add_layer_norm_grad_cut_n.h#L49)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
