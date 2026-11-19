---
type: Guide
title: 存量TorchScript：方法、dtype与设备迁移表差异
description: 保留固定2.7.1/2.9/2.10文档的旧JIT支持范围，区分ScriptModule子项、弃用提示和Mobile优化入口。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-jit.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-jit.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-jit.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-jit.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-jit.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-jit.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-mobile_optimizer.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_libtorch_npu.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_libtorch_npu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-jit/(beta)torch_npu-jit-optimize.md
  role: constraint
created_at: '2026-11-09T13:42:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 存量TorchScript：方法、dtype与设备迁移表差异

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的固定原生支持页，具体文档版本与中英文范围分别保留；未收录不等于已证实不支持，不据支持清单补造参数、默认值或完整实现。产品为所列A2/A3训练系列与950DT，不扩展950PR，不回推26.0/PyTorch2.8发布基线。本次未执行上游、编译、导出、训练或设备实验。

## 存量版本与入口

该提交torch-jit页仅有PyTorch2.7.1/2.9/2.10中英文；2.9/2.10导言提示TorchScript已弃用，优先torch.export/torch.compile，页面保留继承支持信息供存量代码参考。新版本目录缺页不直接证明实际包删除，旧支持表也不能推广为当前TorchAir或所有编译后端的合同。

script/load/save、freeze/optimize_for_inference、enable_onednn_fusion/onednn_fusion_enabled、ignore/unused/isinstance列三类产品；export/is_scripting/is_tracing只在2.7.1收录，列三类产品。fork/wait/set_fusion_strategy/strict_fusion中文只列A2/A3、英文明确950不支持。oneDNN名称不证明NPU执行oneDNN Kernel，也不能由optimize_for_inference可调用承诺实际加速。

trace/trace_module/script_if_tracing/annotate的input仅FP32并列三类产品；ScriptFunction类及get_debug_state/save也仅FP32，save_to_buffer只给三产品表。Attribute及count/index在2.9/2.10增加input仅FP32，2.7.1只有产品表；type/value列三类产品。类型注解、保存和跟踪是不同操作，不能用一个FP32条目给全部模型参数改类型。

## ScriptModule的方法级范围

类列三类产品、input仅FP32。apply/buffers/cpu/cuda/double/eval/extra_repr/get_buffer/get_parameter/get_submodule、named_buffers/named_children/named_modules/named_parameters/parameters及列出的普通前反向、load-state注册钩子、requires_grad_/save/state_dict/to/to_empty/train/xpu/zero_grad等局部方法有FP32 input限制；其中children没有这句，中文load_state_dict/modules也未重复，而英文两者均写FP32。不能把返回迭代器、目标转换类型和模型所有Tensor混成一个input字段。

add_module/bfloat16/float/half/register_state_dict_pre_hook/register_state_dict_post_hook明确950DT不支持，其中float/half和两个状态钩子还写input仅FP32。type单独列FP16/FP32、UINT8/INT8/INT16/INT32/INT64、BOOL，不由类级FP32说明覆盖该局部表。code/code_with_constants/compile/graph/inlined_graph等元数据或方法只有产品表时不补完整输入规格。

英文额外对get_extra_state/set_extra_state/register_buffer/register_module/register_parameter/set_submodule/share_memory明确三类均不支持，中文未列。中文mtia也明确三类不支持；2.9/2.10另说明它是MTIA设备迁移接口、不表示NPU迁移。ipu中文标A2/A3不支持、950支持，英文却列三类支持并写FP32 input；中文2.9/2.10强调它迁移到IPU、不是NPU迁移。保留表的分歧，不从其他设备名字和产品表推导NPU转换。

英文2.9/2.10对state_dict提示destination/prefix/keep_vars位置参数弃用、使用关键字；2.7.1未重复。不从普通Module的同名方法覆盖ScriptModule，也不由compile方法支持推断TorchScript和torch.compile模型可无条件互换。

## Mobile优化的单独范围

utils.mobile_optimizer.optimize_for_mobile仅英文2.9..2.14列三类均不支持，且提示上游不再主动维护。2.7.1中英文页只说明PyTorch Mobile停止主动维护、不再列该入口支持条目，没有产品表；对应中文2.9..2.14没有页面。维护状态、未列条目与显式不支持分开保留，不据“优化”名称把它用于NPU模型转换。

## 验收与迁移

固定旧版本、实际对象/方法和输入，分别核对捕获、保存/恢复、前向/梯度、设备迁移和消费者，再比较首次与稳态开销。切换export/compile时重新验证动态约束、状态和副作用，不将弃用建议当作已完成迁移或性能保证。本次未跟踪、编译、加载或执行模型。

- [原生编译与Export对象边界](torch_npu_native_compiler_export_scope.md)
- [原生Module与容器范围](../../../../training/guides/torch_npu_native_module_and_container_scope.md)

## C++消费示例不扩大TorchScript支持矩阵

同提交libtorch_npu指南使用resnet_trace.py导出TorchScript，经ci/libtorch_resnet.sh构建并推理。它展示的是一个模型和C++消费路径，不使所有trace输入dtype、控制流或新版TorchScript接口自动受支持，也不等同AOTInductor部署文件。C++ bundle/ABI与生命周期见[libtorch_npu部署](../../bringup/torch_npu/torch_npu_libtorch_build_and_deployment.md)；没有在本次导出、编译、加载或执行模型。

## TorchNPU自有jit优化入口

OpPlugin固定主线另提供torch_npu.jit.optimize(ScriptFunction/ScriptModule)，与原生optimize_for_inference、Mobile优化和torch.compile后端分别消费。[自有API](../../../apis/torch_npu/torch_npu_jit_optimize.md)保存无返回值、FastGELU匹配图形及推理优化返回对象未接住的静态边界；不由一条“优化”描述承诺整模型加速或精度等价。发布文档与主线950DT新增产品分别保留。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-jit.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-jit.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-jit.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-jit.md)（primary）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-jit.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-jit.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-mobile_optimizer.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-mobile_optimizer.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-mobile_optimizer.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-mobile_optimizer.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-mobile_optimizer.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-mobile_optimizer.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-mobile_optimizer.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-mobile_optimizer.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_libtorch_npu.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_libtorch_npu.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-jit/(beta)torch_npu-jit-optimize.md)（constraint）
