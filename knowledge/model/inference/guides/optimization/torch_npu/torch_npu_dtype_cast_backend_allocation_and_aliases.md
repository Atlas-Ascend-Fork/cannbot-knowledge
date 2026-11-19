---
type: Guide
title: 原生dtype转换的后端分配、同类型克隆与原地入口
description: 连接_npu_dtype_cast生成分派与ACL、OpAPI候选，说明同dtype clone请求、内部格式分配和连续empty的Storage申请，以及原地入口短路；并给出
  _npu_dtype_cast_backward 组合式反向、框架消费面与跨仓所有权澄清。
tags:
- task.implementation
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CastKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ToKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CastKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/custom_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/templates/CustomFunctions.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/op_api/CloneKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/ops/op_api/CloneKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
created_at: '2026-11-11T02:58:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# 原生dtype转换的后端分配、同类型克隆与原地入口

## 固定源码和接线范围

本卡对照OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda与发布dedc316708372c9a8bfde4527abd2a94b74840f5的_npu_dtype_cast、npu_dtype_cast_候选，以及PyTorch/TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf、发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b的准备和Tensor工厂。主线torchnpugen模板用于解释生成接线，实际生成物、安装分派及外部CANN执行仍需配套构建和运行证据。产品范围未知，保持draft、空平台。

[类型准备指南](torch_npu_tensor_iterator_type_inference_and_cast_consumers.md)已有OpCommand输入内部Tensor与输出引用的转换条件。[公开npu_dtype_cast接口](../../../apis/torch_npu/npu_dtype_cast.md)保留文档适用范围。本卡补准确的内部_npu_dtype_cast候选分支，采集时应保存接口全名和所选后端。

## 从custom_ops调用到后端候选

主线生成器先合并TorchNPU与OpPlugin YAML，再解析custom/custom_autograd列表，生成CustomFunctions分派包装。模板按schema base_name和overload查找npu命名空间的Dispatcher算子，随后调用typed op.call。生成的custom_ops函数在此构建路径中承担Dispatcher桥接，调用名本身不把执行固定到某个ACL或OpAPI函数。

所列两版OpPlugin YAML都为_npu_dtype_cast声明ACL与OpAPI候选，主线另列DVM，发布所读条目未列DVM。两版npu_dtype_cast_条目都只列ACL并标device_check: NoCheck。这些声明用于定位候选；本卡没有执行生成器或检查安装包中最终注册对象，DVM实现也保留单独核对范围。

## 同dtype与不同dtype分别计准备成本

| 准确候选与条件 | 所读实际请求 |
| --- | --- |
| ACL _npu_dtype_cast，self.dtype等于目标dtype | 通过npu_dtype_cast_impl返回self.clone()。 |
| OpAPI _npu_dtype_cast，兼容层之后且dtype相等 | 返回self.clone()。兼容宏位于该比较之前，先经过宏控制的分派判断。 |
| ACL _npu_dtype_cast，dtype不同 | 用self.sizes、目标dtype的options及self格式申请结果，随后执行Cast的Input(self)、Output(result)及dst_type属性。 |
| OpAPI _npu_dtype_cast，dtype不同 | apply_tensor_without_format申请目标dtype结果，再请求aclnnCast。 |

同dtype分支明确发出clone请求，分析重复转换开销时应把这条分支单独计入。实际clone的空Tensor、格式和底层搬运分支仍需使用准确Clone消费者；不能仅从函数名推定返回输入对象或测出固定复制量。

## 两条分配链实际交给哪个工厂

ACL路径经apply_tensor_with_format检查PrivateUse1设备并选择存储格式，Double配内部格式会选择base格式。随后unsafe_empty_with_format在keep_format=False且内部格式被禁止时继续调整dst_format，再转入empty_with_format。

empty_with_format以StorageDescHelper::GetMemorySize(size,format,dtype)计算存储元素量，乘dtype.itemsize得到申请字节数，构造新的NPUStorageImpl和NPUTensorImpl。Cast所用unsafe入口传空的对齐参数，落入allocator->allocate分支。内部格式的存储尺寸参与字节计算，记录逻辑numel不足以还原这个申请值。

OpAPI路径的apply_tensor_without_format经apply_tensor_use_empty转入NPUNativeFunctions::empty，要求Contiguous布局。该工厂按逻辑size的元素乘积与目标dtype.itemsize计算字节，向NPUCachingAllocator请求allocate，创建NPUStorageImpl及NPUTensorImpl，并设置连续尺寸和存储描述。若options没有PrivateUse1设备，准备helper会补成PrivateUse1设备；准确设备ordinal仍由options和当前设备语义核对。

所读主线两个工厂还在should_fill_empty_deterministic成立时调用fill_empty_deterministic_，发布所选工厂没有这一追加分支。新缓冲的准备成本因当前确定性设置而异；本卡没有执行该条件或测量填充开销。

这里证明的是固定工厂的Storage对象构造与分配器申请路径。分配器可以复用缓存，零元素、对齐、内存峰值及设备完成量仍按准确输入和分配器状态观察。

## 原地入口的短路和格式回写

两版ACL npu_dtype_cast_(self,src)先比较self与src的dtype，相同即返回self，所读分支没有继续复制src。dtype不同时，以self为输出执行Cast；self不满足check_match时先apply_tensor(self)准备临时，执行后format_fresh_view(self,temporary)。格式回写的copy_见[输出准备指南](torch_npu_out_preparation_resize_and_overlap.md)。

这个入口返回self引用，输出dtype取self，src提供Cast输入。调用方需要保留正确的self内容期望、shape和别名条件，不能把它按任意同dtype复制入口采用。后端选择、普通npu_dtype_cast的可选input_dtype及特殊打包类型仍按各自准确接口核对。

## 模型优化核验

固定软件栈和安装分派，记录完整算子名、后端、输入目标dtype、shape/format、是否经过兼容回退、clone和empty调用，再分别核数值、别名及申请字节。将输入公共类型推断、连续化、Cast申请和输出回写分开计时。两仓主线组合、算子数值、分配器峰值和设备性能均未运行验证，没有新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CastKernelNpuOpApi.cpp)（primary），定向范围93–102。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CastKernelNpuOpApi.cpp)（implementation），定向范围93–102。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CastKernelNpu.cpp)（implementation），定向范围27–80。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CastKernelNpu.cpp)（implementation），定向范围27–80。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation），定向范围6142–6150。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation），定向范围5890–5898。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation），定向范围238–240、257–259、392–399、250–255、269–293、409–411。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation），定向范围155–204、334–388、390–413。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation），定向范围241–241、258–261、385–393、253–256、271–292、405–408。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation），定向范围86–133、268–322、324–345。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp)（implementation），定向范围340–362、394–408。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp)（implementation），定向范围344–363、403–419。
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/custom_functions.py)（implementation），定向范围30–35、311–359。
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/templates/CustomFunctions.cpp)（implementation），定向范围1–14。
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py)（implementation），定向范围1645–1648、1746–1754。
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/utils.py)（implementation），定向范围124–166。

## 同dtype分支的clone实际换了新存储

TorchNPU把clone与copy_登记为本地实现（npu_native_functions.yaml，两条均标op_api，两版相同）。OpAPI clone先做aclnnInplaceCopy符号兼容检查，缺符号回退旧实现；再按memory_format分派：缺省Preserve且src非重叠稠密时用empty_strided按源sizes/strides申请、保留stride，否则empty_like；显式给定格式时走apply_tensor_without_format。三种申请都随后self.copy_(src)真复制并返回新Tensor。发布版OpAPI clone没有Preserve分支，一律apply_tensor_without_format申请连续存储、copy_后传播names。

旧实现（TensorFactories.cpp）先试TransContiguous能否按reshape/slice优化直接产出；否则ApplyTensorWithSizes按base格式申请结果，src非base格式时先转base再copy_d2d_dtype_baseformat。主线在该入口还前置了量化Tensor专用路径（CPU侧int_repr暂存与回写），与普通Cast链无关。

因此"相同dtype返回self.clone()"既不是返回原对象，也不共享Storage：两条版本路径都另申请存储并做一次真实复制。同dtype Cast的成本按一次clone计入；具体搬运字节与峰值仍取决于copy_/clone实现、格式与分配器状态，未测量。DVM侧同dtype不短路、直接建Cast节点的行为已由[Eager DVM逐元素融合](torch_npu_eager_dvm_elementwise_precision_and_fallback.md)闭合。

## 公开npu_dtype_cast的打包类型分支

两版token相同的OpAPI npu_dtype_cast_impl对目标为HIFLOAT8、FLOAT4_E2M1、FLOAT4_E1M2或INT4的请求走专门分支：按Byte dtype申请输出存储并返回普通ATen Byte张量，输出Tensor.dtype与底层storage dtype都是Byte，框架层没有名义dtype与存储dtype的分离；请求的自定义datatype只写进传给aclnnCast的ACL TensorWrapper描述符，由ACL侧按该类型解释这批字节，不是HiFloat8Tensor式的框架dtype包装。shape仅按类型条件变化且只发生在输入维度数大于0时的最后一维：输入侧（按input_dtype判定）为FLOAT4_E2M1/FLOAT4_E1M2时把推导的ACL输入最后一维乘2；目标为FLOAT4/INT4时要求推导输入最后一维能被2整除并把输出最后一维减半，违反即TORCH_CHECK报错；目标为HIFLOAT8不做减半与整除检查，常规输入下输出shape与输入一致。TensorWrapper允许input_dtype覆盖输入acl类型。这些分支不能按普通元素级cast校验数值或复用缓冲；除FLOAT4/INT4的尾轴打包外，也不存在普遍的存储shape与逻辑shape不一致。

## 源码级来源

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/op_api/CloneKernelOpApi.cpp)（implementation）：1–44。
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/ops/op_api/CloneKernelOpApi.cpp)（implementation）：1–36。
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）：734–876。
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）：679–699。
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）：1–60。
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）：1–62。
- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CastKernelNpuOpApi.cpp)（implementation，核对范围27–102）。

## _npu_dtype_cast_backward组合式反向、框架消费面与跨仓所有权澄清

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| `_npu_dtype_cast_backward`（opapi CastKernelNpuOpApi.cpp 114–118、aclops CastKernelNpu.cpp 92–97，两pin各自去空白等值）：`grad.requires_grad_()`后调`custom_ops::_npu_dtype_cast(grad, dtype)`——反向就是再走一次前向cast，目标dtype由derivatives公式传入的`self.scalar_type()`（derivatives.yaml两pin相同：`self: _npu_dtype_cast_backward(grad, self.scalar_type())`、output_differentiability `[isDifferentiableType(dtype)]`） | 无独立内核、无dtype白名单；跨dtype数值损失与前向同链（含上文打包类型分支）；requires_grad_()只保证高阶autograd可追踪 |
| `npu_dtype_cast_backward`（opapi 104–113、aclops 84–90）同构，多grad_dtype/input_dtype两个可选参数转发给公开npu_dtype_cast | 图模式对同名入口的GE Cast映射见[GE dtype/scatter lowering](../torchair/torchair_ge_dtype_scatter_lowering.md)，属另一层不与本节互推 |
| 框架消费面（六pin静态）：OpCommand commonType收敛（上文340–362/394–408）；ProcessGroupHCCL.cpp集合通信前设备侧预转（主线5228/5505/5588/5673/5677/5721/5728把Int32/Bool张量转到at::kInt/Bool，发布4565/4800/4879/4955/4959/5006/5013同构7处）；CopyKernelOpApi.cpp主线209在跨dtype非blocking copy_的D2H腿前用_npu_dtype_cast(src, dst.scalar_type())设备侧转换 | **发布CopyKernelOpApi.cpp:131同位置改用src.to(dst.dtype())**——两pin copy_的设备侧cast入口不同，迁移按pin分别核对；CopyKernel.cpp主线337–341/发布320–324在d2d copy_的跨dtype分支经npu_dtype_cast_复用（原地入口见上文） |
| op-plugin消费规模：主线123个/发布119个.cpp引用_npu_dtype_cast（OpUtils.cpp:258的calcu_type预转、各aclops文件的FP32中转与Int索引转换等） | 计数是rg文件级命中，不区分调用次数/分支可达性 |

所有权澄清：`_npu_dtype_cast` 的实现不在 torch_npu 仓（六 pin 静态对账）。算子`npu::_npu_dtype_cast(_backward)`的schema注册（op-plugin yaml custom段，主线6138–6157、发布5886–5904）、手写实现（CastKernelNpuOpApi.cpp/CastKernelNpu.cpp，两pin去空白等值）与derivatives公式全部位于op-plugin仓；torch_npu仓只持有torchnpugen生成的custom_ops分派桥（见上文"从custom_ops调用到后端候选"）与框架侧调用点。其他卡旧文按byte前缀保留不改写，与本节冲突时以本节为准。

### backward与消费面来源

- [CastKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CastKernelNpuOpApi.cpp)（implementation，核对93–118）：_npu_dtype_cast与两个backward完整函数体（文件已列于frontmatter来源）。
- [CastKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CastKernelNpu.cpp)（implementation，核对75–97）：acl_op侧同名实现（文件已列于frontmatter来源）。
- [derivatives.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）：129–135；npu_dtype_cast/_npu_dtype_cast两条autograd公式。
- [derivatives.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）：127–131；与主线相同公式。
- [ProcessGroupHCCL.cpp ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）：5228、5505、5588、5673、5677、5721、5728；_npu_dtype_cast设备侧预转调用点（行级核对，所在函数体未整读）。
- [ProcessGroupHCCL.cpp f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）：4565、4800、4879、4955、4959、5006、5013；发布同构7处。
- [CopyKernelOpApi.cpp ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp)（implementation）：200–215；跨dtype非blocking copy_的设备侧cast分支。
- [CopyKernelOpApi.cpp f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp)（implementation）：125–140；同位置发布实现为src.to(dst.dtype())（负向：该文件_npu_dtype_cast全文rg零命中）。
- [CopyKernel.cpp ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/CopyKernel.cpp)（implementation）：330–345；d2d copy_跨dtype分支的npu_dtype_cast_复用。
- [CopyKernel.cpp f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/CopyKernel.cpp)（implementation）：313–328；同口径。
- 负向证据：op-plugin主线/发布`grep -rl _npu_dtype_cast op_plugin --include=*.cpp`计数123/119；derivatives.yaml两pin均无_npu_index_add条目。

## 标准 `Tensor.to()` 的 `_to_copy` NPU 分支

主线 `torch_npu/csrc/aten/common/ToKernelNpu.cpp` 的 `NPUNativeFunctions::_to_copy`（:30-124）是 `to(..., copy=True)`/跨设备转换的准备入口，与上文 custom op 路线并列：仅指定 dtype 且目标为 Double 时 `TORCH_NPU_WARN_ONCE("Device do not support double dtype now, dtype cast replace with float.")` 并把目标改为 Float（:45-48）——`to(torch.float64)` 在该路径静默降为 FP32，只留一次性告警；layout 显式给值且与 self 不同时直接 `TORCH_CHECK NOT_SUPPORT`（:50-59）；memory_format 仅接受 Preserve/Contiguous（:61-70）；requires_grad 已设时报参数错误。`pin_out = non_blocking && is_npu(self) && 目标为 CPU && Strided`（:76-77）：D2H 非阻塞转换的输出按 pinned 内存申请。Preserve 路径优先 `empty_strided` 复制原 strides（非重叠稠密时）或 `infer_dense_strides`（:80-99），否则 `suggest_memory_format` 落到 Contiguous `empty` 后 `copy_`。该文件为整文件阅读；发布 pin 同名文件未比对。

## _to_copy 分支来源

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ToKernelNpu.cpp)（implementation）：全文 1-124。

## 发布 pin 对照（f3ecfe4a）

卡内涉及的 1 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 版本边界（发布 pin 行为不同，按 pin 分述）

- **`torch_npu/csrc/aten/common/ToKernelNpu.cpp`**：to(options)/_to_copy 准备入口两版行为不同。
  - 主线仅当 self.dtype()!=目标 dtype 时告警并把 Double 降 Float，且不提前返回——同 dtype 请求仍走拷贝路径（源码注释明确 copy=True 语义要求同 dtype 也完成拷贝，:36-45）。
  - 发布版 `self.dtype()==dtype` 时直接 `return self`（同 dtype 短路、不新建存储，:37-39）；随后 Double 告警/降 Float 无条件执行。
  - 主线未指定 memory_format 时默认 Preserve，Preserve 路径优先 supports_as_strided/empty_strided 保留原 strides，非重叠稠密之外还有 infer_dense_strides 分支（:75-77、:90-110）。
  - 发布版未指定 memory_format 时 NPU 张量默认 Contiguous、非 NPU 才 Preserve（:75-82）；Preserve 分支无 supports_as_strided/infer_dense_strides 两条子路径，非稠密直接 suggest_memory_format。
  - 对本卡结论的影响：本卡「标准 `Tensor.to()` 的 `_to_copy` NPU 分支」一节的主线结论（同 dtype 仍拷贝、Preserve 默认、stride 保留链）在发布 pin 均为不同形态；发布版 to() 同 dtype 返回原对象、NPU 默认 Contiguous。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
