---
type: Guide
title: TorchNPU类型准备：Iterator元数据与Sigmoid反向Cast消费者
description: 沿原生Sigmoid反向追踪公共dtype推断、out参与规则与OpCommand显式转换，区分a.sizes形状提示、真实申请和布局临时量。
tags:
- task.implementation
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/mirror/NPUTensorIterator.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/mirror/NPUTensorIterator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/mirror/NPUTensorIterator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/mirror/NPUTensorIterator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/mirror/NPUTypeProperties.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/mirror/NPUTypeProperties.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.h
  role: implementation
created_at: '2026-11-10T15:00:23Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU类型准备：Iterator元数据与Sigmoid反向Cast消费者

## 固定调用链与配套边界

定向核对PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf及发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b的NPUTensorIterator、NPUTypeProperties和OpPreparation/OpCommand选定方法；以OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布dedc316708372c9a8bfde4527abd2a94b74840f5的ACL sigmoid_backward作为实际源码消费者。两仓主线固定提交不据此认证已经配套，声明的ACL候选也不等于安装包运行必选ACL。

[OpCommand接口](../../../apis/torch_npu/cpp_opcommand.md)已有成员和同步说明，[公开激活约束](../../../../training/guides/torch_npu_native_activation_precision.md)与[GE激活转换](../torchair/torchair_ge_activation_lowering.md)已有其他证据层。本卡补“推断→准备→显式转换请求”，未知整卡平台，保持draft与空平台；未导入、生成、执行上游、自动求导或NPU。

## Iterator的PROMOTE先计算类型，不在此处转换Tensor

NPUOperandInfo从已定义Tensor读取target_dtype/current_dtype，并校验layout为Strided；这不要求其已经连续。add_output与add_input将Tensor包装加入operands，前者另增加num_outputs。选定compute_types只选择参与operands、计算common_dtype_，没有在其中调用dtype Cast、Tensor分配或广播扩展。不能从PROMOTE/CHECK枚举注释直接推定已经执行这些操作。

| 准确helper/包装 | 所读规则 |
| --- | --- |
| binary_op(out,a,b) | 先放out，再a/b，使用PROMOTE，因此已定义out也参与公共类型计算；返回的common_shape直接取a.sizes。 |
| comparison_op(out,a,b) | 使用PROMOTE_INPUTS，计算时按num_outputs跳过out；返回common_shape仍直接取a.sizes。 |
| binary_op(a,Scalar b) | 按Scalar类别先选Float/Bool/ComplexFloat/Int；a为Half或BFloat16时先把候选标量类型覆为该类型，再必要时调用本地result_type；同样返回a.sizes。 |
| OpPreparation::binary_op_check的Tensor/Tensor重载 | 仅a.dtype!=b.dtype时调用Iterator并填写common_type/common_shape；相同输入dtype时保留UnifiedResult的空optional。 |
| OpPreparation::comparison_op_check | 也在输入dtype不同才推断；若out.dtype同时不同于a/b，则置result_type_defined=True。 |

因此不能将这个binary_op_check当作任意out类型验证器，或把该common_shape当作已经计算出的完整广播输出shape。check_mem_overlap虽在准确入口中接受并传递，所读Iterator binary/comparison函数体没有使用它做重叠检查；外层CheckOut等路径仍可能另有检查，不由这个局部事实否定完整调用链的别名保护。

公共类型快速路径先检查参与的已定义非零维Tensor是否同type；出现零维或不同type后才走ResultTypeState。该状态将普通非零维、非wrapped零维和wrapped-number分类累积；wrapped浮点先采用当前default dtype，再按dim/zero/wrapped顺序合并。类别优先级和Scalar重载的Half/BF16覆写都来自这份本地helper，不把它认证成任意版本ATen TensorIterator或全部混合复数/标量的等价规范。

## 真正的Cast请求发生在OpCommand输入输出准备

Expect只保存common_type、common_shape和result_type_defined。常规Tensor Input先把format_contiguous_add_copy_optimize的结果存入OpCommand内部storage，再传AddTensorInput；若commonType非空且不同于该Tensor dtype，后者调用_npu_dtype_cast并重绑这个内部Tensor引用，再创建ACL输入描述。不能把它概括成Iterator直接原地修改调用方全部输入；也不能忽略布局整理和Cast可能增加的缓冲或工作量。

AddOutput在resultTypeDefined为false、commonType非空且与output dtype不同的条件下，调用_npu_dtype_cast并重绑传入Tensor引用，然后创建ACL输出描述。它不是仅替换描述中的dtype标签，也没有在这个方法中先按common_shape调整输出shape。外层Output在AddOutput之前已向outputTensor保存当前handle；不能据此假定后续重绑与原out的所有别名、最终写回合同已自动闭合。

这些是显式转换**调用**及对象重绑证据；本卡未展开_npu_dtype_cast的实际分派/全部分配实现或format优化内部，因此不承诺每次Cast/contiguous都分配独立存储、固定复制字节数、保持原有别名或完全没有临时量。输入类型推断、输出初次申请与后续输出重绑应分别记录。

## Sigmoid反向怎样消费这份结果

所读两版ACL sigmoid_backward无out先apply_tensor(grad_output)，再调用nocheck；apply_tensor沿grad_output.sizes/options和格式进入apply_tensor_with_format，最终请求unsafe_empty_with_format。该申请路径检查PrivateUse1设备、选择存储格式，Double配内部格式另换base格式；不是调用Iterator时才第一次准备grad_input。

nocheck以binary_op_check(result,output,grad_output,true)获得UnifiedResult，再构造SigmoidGrad的Expect→Input(output)→Input(grad_output)→Output(result)→Run。输入dtype不同且公共类型与初始result不同时，后续AddOutput可能再次重绑result；只看最初apply_tensor的dtype或元素字节数不能还原完整准备路径。相同输入dtype触发包装shortcut，也不能由此推导任何不匹配out均已在Iterator校验或修正。

out入口先CheckOut，并在grad_input不满足check_match时使用format_contiguous临时，调用nocheck后format_fresh_view；匹配时直接将grad_input交给nocheck。是否有额外布局缓冲、输出对象最终身份与类型，须覆盖准确out分支；不能由返回Tensor引用认证没有内存或别名变化。本卡不展开CheckOut的全部异常与重叠合同。

## 两版一致的范围与另一路声明

所选Iterator类型计算、TypeProperties、binary/comparison包装、Expect和Tensor输入/输出Cast条件及ACL Sigmoid反向的去注释/空白token一致；apply_tensor_with_format仅有日志字符串拼写差异。这个对照不表示完整文件、调度器、分配器或两仓主线运行组合相同。

两版sigmoid_backward的gen_opapi另声明广播shape及at::native::result_type输出dtype，out条目以grad_input为dtype参照；主线无out条目另列dvm。它们是OpAPI生成描述，不能替代这里ACL先按grad_output申请的事实，也不能拿声明推定已生成/安装的最终消费者。

诊断模型混合精度开销时，保留准确后端、输入与out dtype/shape/stride/format、是否相同dtype shortcut、Expect的commonType/resultTypeDefined，以及布局临时和显式Cast次数。先验证结果/梯度与别名，再比较内存和耗时；没有数值、性能或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/mirror/NPUTensorIterator.cpp)（primary）：8–63、139–211。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/mirror/NPUTensorIterator.cpp)（implementation）：8–68、136–210。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/mirror/NPUTensorIterator.h)（implementation）：14–54、83–119、124–132。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/mirror/NPUTensorIterator.h)（implementation）：14–55、88–133、138–146。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/mirror/NPUTypeProperties.cpp)（implementation）：6–55。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/mirror/NPUTypeProperties.cpp)（implementation）：6–60。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：21–63、238–293。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：20–63、241–292。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp)（implementation）：65–82、126–133、340–362、394–408。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp)（implementation）：68–82、124–129、344–363、403–419。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.h)（implementation）：18–26。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.h)（implementation）：18–25。
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp)（implementation）：19–57。
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp)（implementation）：19–68。
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4603–4620。
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：4452–4468。

## Output先存原始handle，重绑后谁是执行与返回对象

OpCommand::Output先把当前（转换前）的output句柄存进成员outputTensor，再调用AddOutput。AddOutput在resultTypeDefined为false且commonType有值且与输出dtype不同时，把按引用传入的output重绑为_npu_dtype_cast结果；ACL输出描述与DataBuffer由重绑后的Tensor构造，设备写入目标是转换后的新Tensor。调用方局部变量（如Sigmoid反向nocheck的result）同样被重绑，并作为该包装的返回值；转换前的原始handle留在outputTensor里。

outputTensor只在Run的非任务队列且sync（即调用过Sync(index)）分支被消费：OpCommandImpl::InnerRun在AclopCompileAndExecuteV2之后，按sync_index对保存的原始handle用aclGetTensorDescDimV2读出的真实shape逐个resize_。任务队列路径ExportParams后enCurrentNPUStream，不传outputTensor；非sync路径也不碰它。因此原始handle的既定用途只有"sync出口按实际输出shape修正尺寸"，所读调用链没有任何把设备结果写回转换前原out的代码；两版该结构一致。InnerRun还在IsOomError时按NPU_MAX_OP_EXEC_TRY_NUM上限重试整次aclop执行。

据此，Sigmoid反向out链在输出dtype与公共类型不一致时：设备写入Cast后的Tensor、函数返回同一Cast对象、CheckOut验证过的原grad_input不再接收数据；这不是自动回写合同，采用前需按准确输入组合复核。

## OpCommand 来源

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp)（implementation，全文1–467）。
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp)（implementation，核对范围120–186、395–415）。
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation）：245–372、431–489。
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation）：125–160、176–270。
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.h)（implementation）：240–361。
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.h)（implementation）：313–345。
