---
type: Guide
title: 原生Softmax执行：升精度、out整理与反向分配
description: 区分Softmax及LogSoftmax的ACL分配和输入转换，核对out格式回写、input_dtype边界与两版生成声明差异。并含 aten::_masked_scale 生成直发aclnnMaskedScale的注册与包装边界。
tags:
- task.optimization
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftmaxKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftmaxBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftmaxBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSoftmaxBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSoftmaxBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/LogSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/LogSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SoftmaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SoftmaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedSoftMaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedSoftMaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py
  role: implementation
created_at: '2026-11-10T14:44:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生Softmax执行：升精度、out整理与反向分配

## 固定入口与证据层次

本卡对照OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的Softmax/LogSoftmax ACL前反向、LogSoftmax helper、softmax.int OpAPI包装及相应生成描述。两反向文件和LogSoftmax helper分别去注释/空白、拼接续行后token相同；前向与Schema差异按下文保留，不宣称全部实现相同。

[公开激活约束](torch_npu_native_activation_precision.md)已有产品和dtype表，[GE Softmax](../../inference/guides/optimization/torchair/torchair_ge_softmax_lowering.md)已有图转换。这里补Eager准备合同，不用GE Cast替代ACL行为，也不把生成描述当已核对的安装包生成物。整卡平台及配套未知，保持draft、空平台；未运行上游、生成器、自动求导或设备。

## 公开softmax与内部_softmax不能合并成一次直接调用

softmax.int OpAPI先经aclnnSoftmax兼容宏，指定dtype且与self不同才显式_npu_dtype_cast，然后在NoNamesGuard中调用`at::_softmax(converted,dim,false)`，最后propagate_names。它没有在这里直接EXEC_NPU_CMD；内部ATen调用仍有分派边界，不能据外层进入OpAPI就断言里面一定走哪个实现。

ACL的公开softmax也通过ATen调用内部入口，但只要dtype有值就调用_npu_dtype_cast，即使值与self相同；这不表示同dtype的底层转换必然产生新存储。主线两路Dimname重载额外置于`!VERSION_BETWEEN(V2R13,VERSION_NEWEST)`条件，发布所读C++没有该条件；不从源码存在推定任意PyTorch版本均注册该重载。

## half_to_float的输出申请和输入转换分别核对

| 已读ACL准确入口 | 局部分配与调用 |
| --- | --- |
| _softmax无out | half_to_float=True时按self shape、FP32 options申请result，否则按self申请；当result dtype与self不同，先_npu_dtype_cast输入，再以SoftmaxV2执行。 |
| _log_softmax无out | 先按self申请result，再以half_to_float选择传给log_softmax_nocheck的目标类型；helper需要转换时用self.toType(dst_type)，然后把同一result对象交给LogSoftmaxV2。 |

因此不能把“输入先升到FP32”与“输出明确按FP32申请”混为一条事实。LogSoftmax这几段没有在helper中将result重绑成FP32；OpCommand内部如何处理输入/输出类型仍需下层证据，不能直接宣称已运行得到错误dtype或数学错误。

无out ACL入口没有复制下述out分支的Half-only检查，不等于任意dtype已被支持。dim以单元素axes属性传交，没有在这些局部函数建立全部负轴、越界或空输入验证；也没有全负无穷行的专用安全处理，不用普通SoftmaxV2名字认证safe-softmax语义。

## out准备可以引入额外格式缓冲

ACL _softmax_out先以half_to_float选择目标dtype并CheckOut；True时要求self为Half，否则要求浮点。随后必要时转输入dtype，若out不满足check_match，则format_contiguous准备临时结果，算子写临时对象后format_fresh_view回写；满足时直接写out。返回仍是传入out引用，不能从原地别名推定没有临时量或格式开销。

主线新增的ACL _log_softmax_out采用同类检查与临时回写，调用LogSoftmax helper；发布所读LogSoftmax C++只有无out函数，发布对应Schema段也没有该out条目。这个缺项仅限定固定文件和声明，不等于高层log_softmax或全部其他后端不支持out。

CheckOut发生在后面的显式类型检查之前；这里只记录次序，不把辅助准备当作无副作用事务，也不假设每种不匹配out都被自动修正成功。

## 反向的input_dtype不自动控制最终梯度类型

两类ACL无out反向都取grad_output的shape，再以temp_output为参照申请grad_input；input_dtype没有在这些函数中选取输出dtype或作为算子属性传入。SoftmaxGrad的输入顺序是(output,grad_output)、属性axes；LogSoftmaxGrad是(grad_output,output)、属性axis，不能互换调用模板。

当temp_output的格式为NC1HWC0时，Softmax调用`npu_format_cast_`，LogSoftmax则调用无下划线的`npu_format_cast`且未接回返回值。这里没有展开格式转换实现，不能把两条调用当成等价，也不能只凭丢弃返回值断言运行一定错误或output原对象必被改写。

反向out以grad_output作CheckOut参照，并在格式不匹配时使用连续临时及format_fresh_view；没有在本函数按input_dtype统一Cast。这与GE Converter的混合梯度检查是不同层，不把局部未消费参数扩大成全部自动求导或混合精度必然失败。

## OpAPI生成描述的版本差异

两版_log_softmax生成描述为同self shape，half_to_float时输出dtype选FP32；_log_softmax_backward_data则指定grad_output的shape/dtype。所列exec只传实际Tensor、dim和输出，没有把input_dtype单独传给ACLNN；这些是描述，不是本卡已生成或执行的结果。

_softmax无out同样声明half_to_float时FP32；_softmax.out段只列exec。反向则不能合并版本：发布无out生成描述以output为参照指定grad_input的shape/dtype，而发布out以grad_output为参照；主线无out改structured_delegate到out，out标structured=True并列exec，未在本段重复完整输出推导。不能在未展开结构化Meta/生成器消费者时替主线补出最终分配或断言修复了某数值问题。

## 模型优化验收

保存准确入口、实际后端、half_to_float、dtype/input_dtype、dim、input/output/grad stride与内部格式，分别核无out和out的输出dtype、格式临时量及输入是否转换。把指定dtype的前置Cast与Softmax本体分开计成本，先核数值和梯度，再比较吞吐/内存。本卡没有运行这些验收，不提供设备支持推断、性能数字或verified记录。

## aten::_masked_softmax：显式Host往返与NPU准入（新增）

新增对照同一固定主线与发布的MaskedSoftMaxKernelNpuOpApi完整实现，以及符号探针完整helper和精确Schema。它是ATen内部 `_masked_softmax`，不是[custom npu_scaled_masked_softmax](../apis/torch_npu/npu_scaled_masked_softmax.md)的完整公共合同；即使局部最终复用aclnnScaledMaskedSoftmax，参数准入也不能互相替代。本卡没有导入、CPU/NPU执行、CANN切换、自动梯度、图捕获或性能实验。

Schema给dim=None、mask_type=None，所选条目只列op_api: all_version。包装先调用fallback-condition；符号探针在函数内以static const bool保存第一次返回值，检查aclnnScaledMaskedSoftmax及其GetWorkspaceSize两个地址是否都存在。这是地址查找的局部结果，不认证设备、shape、dtype或kernel可执行；运行中后装/换库不证明该static结果会重新计算。

只有探针返回真并同时满足以下三条，才继续本地NPU准备：self rank为4；dim为None、-1或self.dim()-1；mask_type显式存在且等于2。缺符号先用一类WARN_ONCE提示；几何/参数不合再用另一类WARN_ONCE提示。默认mask_type=None因此会进入回退，不能由Schema有默认值推导默认调用留在NPU，也不能把mask_type=0/1的src_mask/src_key_padding_mask名称当成本实现的设备路线。

这里的回退不是一句抽象的“可能CPU”：代码实际依次取得self_.cpu()和mask_.cpu()，调用at::_masked_softmax(self_cpu,mask_cpu,dim_,mask_type_)，再把结果.to(self_.device())返回。结果看起来仍在原设备，不能据输出位置判定中间没有Host运算或往返；本卡未测复制、同步、图行为或耗时，CPU入口的完整合法性/错误检查另计。

只有没有回退后，包装才执行mask-type helper：要求mask dtype为Bool、类型存在且是0/1/2；类型2还要求mask.sizes()==self.sizes()。从入口控制流看，此时已被限定为类型2；helper接受0/1的分支不解除外层CPU准入条件。bool与shape检查也在fallback之后，不能把所有非法输入的报错次序都按这个helper描述；某些输入会先被送到CPU实现。

NPU路径固定scale=1.0、fixed_triu_mask=False，按self shape/options申请无格式输出，执行aclnnScaledMaskedSoftmax并返回结果。该函数没有从dim或mask_type生成新的SDK参数，类型的用途在此主要是选择和校验路径；也没有把整个输入转换到FP32或half_to_float分支。虽然本地还写有self/mask为0维时view(1)的表达式，self rank=4和类型2的同shape准入使其不能构成“本入口支持标量NPU路径”的证据。

这里没有DO_COMPATIBILITY宏或包围EXEC_NPU_CMD的总catch；显式CPU路线由前面的条件选择，不能将它描述为NPU kernel执行异常后的自动重试。两版完整CPP的phase2 token、全部规范化注释和有序include相同，仅排版不同；probe helper和Schema所选块也同token/逐行一致，不推导底层库或运行环境相同。

定位模型中的意外Host开销时，先记录真实入口是否为aten::_masked_softmax、首次符号探针环境、rank/dim/mask_type以及mask dtype/shape，再分辨CPU往返和设备准备错误。它与公开softmax指定dtype的Cast、custom缩放掩码接口及图转换都是不同路径；需要同参输出和实际运行证据后才能判断替换或优化收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftmaxKernelNpu.cpp)（primary）：19–123。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftmaxKernelNpu.cpp)（implementation）：19–121。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftmaxBackwardKernelNpu.cpp)（implementation）：19–70。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftmaxBackwardKernelNpu.cpp)（implementation）：19–78。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSoftmaxKernelNpu.cpp)（implementation）：19–57。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSoftmaxKernelNpu.cpp)（implementation）：19–31。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSoftmaxBackwardKernelNpu.cpp)（implementation）：19–70。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSoftmaxBackwardKernelNpu.cpp)（implementation）：19–82。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/LogSoftmaxKernelNpu.cpp)（implementation）：19–48。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/LogSoftmaxKernelNpu.cpp)（implementation）：19–57。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SoftmaxKernelNpuOpApi.cpp)（implementation）：19–45。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SoftmaxKernelNpuOpApi.cpp)（implementation）：19–43。
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：643–677,708–735。
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：628–653,677–708。

## masked入口新增固定来源

- [MaskedSoftMaxKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedSoftMaxKernelNpuOpApi.cpp)（implementation）：1–88；完整本地小文件。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773；仅所选完整helper/Schema。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3380–3381；仅所选完整helper/Schema。
- [MaskedSoftMaxKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedSoftMaxKernelNpuOpApi.cpp)（implementation）：1–78；完整本地小文件。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792；仅所选完整helper/Schema。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3275–3276；仅所选完整helper/Schema。

## aten::_masked_scale：gen_opapi生成直发aclnnMaskedScale

补充同一固定主线与发布的aten::_masked_scale注册面。它没有手写内核文件（主线与发布两版本的op_plugin/ops/全树rg负向），包装由gen_opapi声明在构建期生成，与上文`_masked_softmax`的手写探针+CPU回退是不同形态；主线与发布两版本的yaml条目逐字节相同（主线744–750、发布719–725）。本节为静态阅读（yaml条目与torchnpugen生成器模板、ResInfo解析行段逐字），未构建生成物、未导入、未执行；[950设备层aclnnMaskedScale卡](../../../ops/ascendc/operators/aclnn/math/math/masked_scale_950.md)的接口/tiling/数值语义不在此复制，ops/ascendc域的direct路径950卡也不属本卡范围。

| 实际门槛→动作 | 结果与边界 |
| --- | --- |
| Schema/gen_opapi声明 | `- func: _masked_scale(Tensor self, Tensor mask, float scale) -> Tensor`，只标`op_api: all_version`；`gen_opapi.out`声明`size: self, dtype: self`，`exec: aclnnMaskedScale, self, mask, scale, out`。无acl_op条目、无cpu_scalar/integral/structured/infer-name键。 |
| 无DO_COMPATIBILITY | 生成器仅在`struct.acl_op`为真时才把DO_COMPATIBILITY宏填进模板槽位（主线struct_codegen.py 326–330、发布184–186行已读）；本条目无acl_op键，生成包装没有任何acl_op备选路径。符号缺失时的行为落在EXEC_NPU_CMD宏与aclnnMaskedScale自身，本卡未核对EXEC_NPU_CMD宏内部，不预测报错形态。 |
| functional生成分支的完整展开 | 按主线模板槽位顺序（43–59行）与ResInfo公式（model.py 60–105行：size/dtype引用输入张量时展开为`self.sizes()`/`self.scalar_type()`，option取首个输入张量），本条目生成体仅含：`auto output_size_0 = self.sizes(); auto output_dtype_0 = self.scalar_type();`、`at::Tensor out = npu_preparation::apply_tensor_without_format(output_size_0, self.options().dtype(output_dtype_0));`、单次`EXEC_NPU_CMD(aclnnMaskedScale, self, mask, scale, out)`并返回生成的out。integral_identity_guard/cpu_scalar/compute_names/infer_name槽位对本条目全为空（CHECK_TENSOR仅用于out类schema，functional走APPLY_TENSOR分配，415–427行），此形态下生成包装没有本地rank/dtype/shape TORCH_CHECK；apply_tensor_without_format内部实现未展开。 |
| 版本边界 | 发布生成器是无cpu_scalar槽位的旧版（struct_codegen.py 296行对主线503行），但对本无cpu_scalar键条目，两版模板可用槽位与DO_COMPATIBILITY门控一致，发布ResInfo公式与主线相同（发布model.py 60–100行已读），主线与发布两版本最终生成结论一致。以上是模板+声明的静态推导，不宣称已实际生成或运行该包装。 |

排查掩码缩放开销时，先确认入口确实是aten::_masked_scale（而非上文`_masked_softmax`或[custom npu_scaled_masked_softmax](../apis/torch_npu/npu_scaled_masked_softmax.md)），再核对当前CANN是否提供aclnnMaskedScale；包装层无回退、无本地参数检查，mask/scale按声明原样下传，mask准入与广播语义由aclnn层决定，不在本节证据内。canonical的model/graph/common域此前零命中该入口（rg负向，命中仅ops/ascendc域设备卡），本节是该入口的首个model面行为记录。

## masked_scale 补充来源

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：744–750；仅所选完整gen_opapi条目，其余注册行未核对。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：719–725；仅所选完整gen_opapi条目，其余注册行未核对。
- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（implementation）：20–107,160–188,295–470；模板、gen_size_dtype_map与compute_op_api_definition主体，其余行段未核对。
- [struct_codegen.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py)（implementation）：38–46,184–186；发布模板与DO_COMPATIBILITY门控，其余行段未核对。
- [model.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py)（implementation）：60–105；ResInfo size/dtype/option公式，其余未核对。
- [model.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py)（implementation）：60–100；发布ResInfo公式，其余未核对。
