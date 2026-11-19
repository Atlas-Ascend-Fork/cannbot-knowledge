---
type: API
title: npu_quant_max：低精度输出、Amax与分组路由
description: 区分QuantMax的低精度y与原dtype amax、group_list长度路由、Meta承载及仅形状测试的边界。
tags:
- task.lookup
- topic.compute.quantization
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMaxKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_max.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T08:27:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_quant_max：低精度输出、Amax与分组路由

## 固定入口与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整Host包装79行、完整小测试134行及有界Meta/Schema。固定发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的同名CPP/测试精确路径没有Git条目，Schema未出现该符号；只记录这些固定入口差异，不推定发布软件栈没有任何同类能力。未执行参考函数、Meta、算子、设备或数值/性能实验，产品未知，保持draft与空平台。

```text
torch_npu.npu_quant_max(x, scale, *, round_mode="rint",
    dst_dtype=291, group_list=None) -> (y, amax)
```

Schema登记op_api all_version，不能据此认证任意版本组合。它返回低精度y与独立amax，不是原生量化Tensor的max归约协议；dst_dtype不能用来推定amax也采用相同精度。

## 分配、逻辑类型与可用性检查

包装通过GetAclDataType(dst_dtype)与convert_to_scalar_type选择y的物理承载，shape与x相同，再以TensorWrapper携带逻辑ACL dtype。y分配传入的是dtype选项；amax则复用x.options，二者选项来源不同，实际设备放置还依赖OpPreparation，不能仅按名称推定任意跨设备输入都成立。

两条分支各以static缓存对应SDK符号可用性。y在这次探测之前已分配；不可用时直接TORCH_CHECK提示更新CANN，函数没有本地DO_COMPATIBILITY或旧ACL回退分支，也没有捕获Kernel错误后重试。符号探测通过不等同于真实dtype、shape及产品可执行。

round_mode.data()被cast为char*下传，包装没有在此建立允许字符串集合、复制成独立字符串或改变舍入模式。scale、group_list内容、dtype组合及其它数值约束也不在这个函数完整验证。

## group_list按首轴长度选择不同SDK入口

| 本地路由 | 下传与amax形状 |
| --- | --- |
| group_list未传，或其sizes()[0]≤1 | aclnnQuantMax，参数为x、scale、round_mode、逻辑dtype、y、amax；**不下传group_list**。amax=[1]，dtype/设备选项来自x。 |
| group_list首轴长度>1 | aclnnGroupedQuantMax，另传group_list Tensor；amax=[group_list.size(0)]，dtype/设备选项来自x。 |

因此传入长度1的累计边界不表示会进入GroupedQuantMax，也不能期望该单个数值控制只处理某一输入前缀。空列表Tensor落入第一条路由也不证明它和scale的组合被底层支持。这里直接访问sizes()[0]，没有先检查可选Tensor是否defined、rank≥1、必须一维、INT64、累计单调、末端等于x首轴或scale数量匹配；缺少检查不等于这些输入任意合法。

## Meta只描述输出，不复刻SDK验证

Meta先用枚举映射查询dtype；dst_dtype为291或映射到FLOAT8_E5M2时申请该FP8类型，292或映射到FLOAT8_E4M3FN时申请E4M3FN，其余分支用UINT8承载，包括没有原生Torch dtype对应的HiFloat8。映射查询虽缺省torch.int8，后面的非FP8分支仍申请UINT8，不能把未知枚举直接当成已合法支持的INT8输出。

y用empty_like(x)，amax按相同group_list首轴规则分配[1]或[组数]，dtype为x dtype。它不执行GetAclDataType、SDK探测或数值计算，也不确认scale/round_mode/group端点合法。不能把Meta输出类型和形状当作Eager编码、设备或实际量化验证。

## 完整测试没有使用其数值参考

六个测试均以Ascend950装饰器筛选，输入分别为FP16、BF16、FP32，目标为E5M2、E4M3FN、HiFloat8；前两者传rint，HiFloat8传round。例子包括(8,256)、(4,16,128)、(2,64)，scale为FP32正值。两组实际多分组端点为[2,4,6,8]与[2,4]，而名为group_fp32_hifloat8的例子只给[2]，按上述C++条件仍是非分组分支。

这些方法只检查y.shape、amax.shape和amax.dtype，**没有比较y/amax的数值，也没有检查y.dtype**。文件虽然定义了两个CPU参考helper，六个测试都没有调用它们；assert_close也没有用于这些比较。本卡也未运行测试，不能据测试存在建立低精度编码或精度通过结论。

单组CPU参考的意图是将x/scale转FP32后相除，再to目标FP8；amax取原x的abs().max()并转回x dtype。注释写round，函数体没有独立round步骤，实际由dtype转换决定；HiFloat8分支只是to(uint8)数值转换，并未提供HiFloat8编码参考。

分组参考按group_list的累计端点切x首轴，按组scale相除、转换并拼接；空组只给amax零项、不追加y片段。代码分别处理2维与其它分支的切片/reshape，没有由此建立任意rank、非法/全空分组或空Tensor设备协议。这些未被调用的参考实现不能替代SDK真实行为。

## GE路径与接入模型

既有 [GE类型与索引转换指南](../../guides/optimization/torchair/torchair_ge_dtype_scatter_lowering.md) 已记录该default重载生成QuantMax并设置y描述符dtype，amax不作相同改写；这里只复用当前卡片的准确段落，不重审或重绑已完成Converter。

接入FP8/HiFloat8流程时，应分别对齐逻辑dtype与物理承载、scale方向、单组/分组选择、amax的输入dtype及下游消费，再做独立数值和收益验收。本卡没有给出全零/溢出/NaN、梯度、图捕获、吞吐或产品支持结论，也没有新增verified。

## Evidence

- [QuantMaxKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMaxKernelNpuOpApi.cpp)（primary）：1–79；完整本地文件。
- [test_npu_quant_max.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_max.py)（example）：1–134；完整本地文件。
- [_meta_registrations.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：7274–7288；仅所列完整函数或Schema。
- [op_plugin_functions.yaml](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：7593–7594；仅所列完整函数或Schema。
