---
type: API
title: TorchNPU C++ Dropout mask：概率、seed与offset参数
description: 保存npu_dropout_gen_mask的显式参数与可选类型边界，不把mask生成当完整Dropout合同；并给出 op-plugin 侧 aten/_npu_dropout_gen_mask 与 npu_dropout_gen_mask 绑定的双派发host合同、副流parallel/sync形态与V2概率dtype透传。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_dropout_gen_mask.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_dropout_gen_mask.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-npu_dropout_gen_mask.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DropoutGenMaskKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DropoutGenMaskKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/ops.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/ops.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/include/ops.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/include/ops.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md
  role: constraint
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU C++ Dropout mask：概率、seed与offset参数

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 声明

`at_npu::native::npu_dropout_gen_mask`定义文件为`third_party/op-plugin/op_plugin/include/ops.h`：

```cpp
at::Tensor npu_dropout_gen_mask(const at::Tensor& self,
    at::IntArrayRef size, double p, int64_t seed, int64_t offset,
    c10::optional<bool> parallel, c10::optional<bool> sync);
```

self是输入Tensor，size给出mask对应尺寸，p表示元素置零概率，seed和offset控制随机状态，返回生成的mask Tensor。parallel/sync是optional类型，但文档原型没有给C++默认实参，不能把它们自动省略或擅自指定默认false。

## 使用限制

接口页未给出所有dtype、shape、概率边界或并行/同步参数的完整运行规则，不能补成无条件支持。它只描述mask生成，不独立证明Dropout缩放、反向、mask位打包布局或与任意高层Dropout的逐位一致性；训练复现还要与[生成器状态](cpp_generator_and_hooks.md)的seed/offset管理配套。静态审阅不构成随机分布、数值和性能验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_dropout_gen_mask.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-native-npu_dropout_gen_mask.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-native-npu_dropout_gen_mask.md)（constraint）

## op-plugin侧host合同：aten入口与Python绑定

上文只覆盖C++接口页的声明边界。本节补OpPlugin两pin的实现层：aten内部`_npu_dropout_gen_mask.Tensor`（主线yaml 5745–5748、发布5505–5508，`acl_op: all_version + op_api: all_version`，tags nondeterministic_seeded）与Python绑定`npu_dropout_gen_mask`（主线6123–6129、发布5871–5877，同派发标签外加`dispatch: CompositeExplicitAutograd: npu_dropout_gen_mask`）。两份实现文件两pin去空白字符流逐字相等（DropoutGenMaskKernelNpuOpApi.cpp main 107行/rel 104行；DropoutGenMaskKernelNpu.cpp main 83行/rel 80行）。docs树没有gen_mask独立Python页；唯一文档级消费是[npu_fusion_attention页](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md)（两pin同文，141行参数说明与479行示例）：外部传入dropout_mask时须用本内部接口生成。全部静态阅读，未运行。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| aten入口`_npu_dropout_gen_mask`（opapi 42–73）：先`DO_COMPATIBILITY(aclnnDropoutGenMaskV2, acl_op::同名)`；`TORCH_CHECK(p >= 0 && p <= 1, "dropout probability has to be between 0 and 1, but got ", p, ErrCode::VALUE)`；`parallel.value_or(true)`为真时`SecondaryStreamGuard(getCurrentSecondaryStream())`内执行，`sync.value_or(false)`为真时`NPU_CHECK_ERROR(acl::AclrtSynchronizeStreamWithTimeout(original_stream))`——同步目标是**进入守卫前捕获的原当前流**，不是副流（照录不解释）；parallel假则直接在当前流执行 | DO_COMPATIBILITY宏语义见[CPU回退与兼容实现指南](../../guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)（同一主线pin）；AclnnOnly且V2符号缺失时抛"Current device only support aclnn operators, ..."。副流分配遵循one-stream-one-pool（源注释自述），内存池行为不在本卡来源范围；`sync=True`同步原流与副流完成顺序的运行效果未验证 |
| V2实现gen_mask_impl（opapi 25–39）：mask长度`ceil(numels/128)*128/8`字节、`apply_tensor_without_format`按**Byte**申请；`probDataType = convert_to_acl_data_type(self.scalar_type())`把self dtype作为概率dtype透传；`EXEC_NPU_CMD(aclnnDropoutGenMaskV2, {numels}, p, seed, offset, probDataType, mask)` | 128bit对齐使mask字节按元素数向上取整；self只是dtype/设备载体（官方示例传`torch.randn(1)`哑张量）；设备侧按该dtype解释p的精度不在本卡来源范围 |
| Python绑定`npu_dropout_gen_mask(size, p, dtype?, layout?, device?, pin_memory?)`（opapi 75–106）：`DO_COMPATIBILITY(aclnnDropoutGenMask, acl_op::同名)`；同p检查；同长度公式、`apply_tensor_with_format(..., Byte, ACL_FORMAT_ND)`；`seed/offset`来自`getDefaultNPUGenerator()`的`philox_engine_inputs(10)`；`EXEC_NPU_CMD(aclnnDropoutGenMask, {numels}, p, seed, offset, mask)`——**不透传probDataType**（V1签名） | 绑定不接收外部seed/offset（与aten入口不同），每次调用消耗默认NPU生成器状态；与[生成器状态](cpp_generator_and_hooks.md)的seed/offset管理配套核对 |
| acl_op回退（aclops两pin同文，52–82）：同p检查与parallel/sync结构（同上副流语义，DO_COMPATIBILITY的另一端，无再回退）；gen_mask_impl（26–49）按同长度公式Byte申请，ACE `OpCommand("StatelessDropOutGenMask")`输入{numels}、`keep_prob=1-p`（以self dtype作host编译输入）、seed与**seed1=0**两个Int标量、offset_list={0, offset}（Long） | ACE路把p换算成保留概率keep_prob并固定seed1=0/offset前缀0（V2路原样透传p与seed/offset）——两派发路对同参数的设备侧解释不同，不互换数值预期；StatelessDropOutGenMask内核语义不在本卡来源范围 |
| C++接口桥（op_plugin/utils/ops.cpp 20–30，两pin同文）：`at_npu::native::npu_dropout_gen_mask`先`OptionalDeviceGuard(device_of(self))`再转`op_plugin::_npu_dropout_gen_mask(...)` | 声明在op_plugin/include/ops.h 25（两pin同文）；ops.cpp include的聚合头`op_plugin/OpInterface.h`在两pin树内find零命中（生成/链接期产物），C++桥最终选中acl_op还是op_api实现的解析不在固定树内，不据本节断言 |
| Meta注册`_npu_dropout_gen_mask.Tensor`（主线_meta_registrations.py 1753–1762，**发布侧零命中**）：按同长度公式返回`torch.empty(length, uint8, meta)`，不校验p、不消费self dtype | Meta只覆盖aten入口（绑定走CompositeExplicitAutograd无Meta）；主线Meta的uint8长度与两实现一致，但Meta通过不证明设备执行；发布无Meta注册是版本差异，照录 |
| 消费面（docs级） | FA页示例（两pin）固定调用形态`torch_npu._npu_dropout_gen_mask(torch.randn(1, device="npu"), [B, N, S, S], p=1-keep_prob, seed=seed, offset=offset, parallel=True, sync=False)`——size给四维attention score形状；op-plugin仓内FlashAttention*OpApi.cpp的同名/近名局部helper不是本aten入口的消费证据（rg核对，其内部实现不在本卡来源范围） |

### op-plugin host合同来源

- [DropoutGenMaskKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp)（primary）：1–107；完整本地小文件。
- [DropoutGenMaskKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp)（implementation）：1–104；完整本地小文件；与主线去空白字符流相同（仅排版）。
- [DropoutGenMaskKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DropoutGenMaskKernelNpu.cpp)（primary）：16–83；acl_op命名空间完整实现。
- [DropoutGenMaskKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DropoutGenMaskKernelNpu.cpp)（implementation）：16–80；同实现发布侧；与主线去空白字符流相同（仅排版）。
- [ops.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/ops.cpp)（implementation）：1–32；C++桥完整文件。
- [ops.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/ops.cpp)（implementation）：1–32；与主线去空白字符流相同。
- [ops.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/include/ops.h)（implementation）：23–27；at_npu::native::npu_dropout_gen_mask声明。
- [ops.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/include/ops.h)（implementation）：23–27；同声明，与主线去空白字符流相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5745–5748（_npu_dropout_gen_mask.Tensor）、6123–6129（npu_dropout_gen_mask含dispatch块）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5505–5508、5871–5877；同口径，与主线逐字相同。
- [meta_registrations.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：1753–1762；_npu_dropout_gen_mask.Tensor Meta注册；发布侧对dropout_gen_mask零命中（负证据，限定两pin的此Meta文件）。
- [torch_npu-npu_fusion_attention.md d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md)（constraint）：141、473–492；dropout_mask参数说明与_npu_dropout_gen_mask调用示例定向读。
