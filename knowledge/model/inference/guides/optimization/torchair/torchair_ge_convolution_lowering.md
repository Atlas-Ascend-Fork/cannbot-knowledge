---
type: Guide
title: GE卷积：转置尺寸、梯度裁剪与量化描述符
description: 补充QuantConv2D的ACLNN/旧ACL精度、成对HiF8提示、固定rint与Meta边界，保留原GE转置与梯度合同。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_conv2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_conv2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantConv2DKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantConv2DKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantConv2DKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantConv2DKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NpuVariables.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NpuVariables.cpp
  role: implementation
created_at: '2026-11-10T08:49:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE卷积：转置尺寸、梯度裁剪与量化描述符

## 版本与结论范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的convolution、convolution_backward与quant_conv2d。主线三文件全文与发布完整AST/注释差异均已审阅；两组AST差异只是all(generator)与all(list)写法，量化映射AST相同，不记为计算算法升级。

本文以前述Python Converter构图合同为基础，另补下文量化卷积Eager/Meta对照，整卡平台矩阵未知，保持draft与空平台；未运行上游、GE编译、NPU训练/精度或性能实验。Shape和Meta可参与构图，不代表来源所有候选Support、动态属性和存储布局已验证。

## Tensor属性被读取为Python值

convolution.default对padding、dilation、stride、output_padding的GE Tensor调用convert_tensor_to_list(...,int)，对groups/transposed调用convert_tensor_to_dtype；反向还转换bias_sizes和output_mask。辅助函数实际读取attr_tensor._meta，再在Python逐项int/bool转换或转单值，**不是用GE节点保留运行期变化的Tensor属性**。警告只在padding为Tensor时打印，其他属性单独为Tensor也会走同类转换，不能以没有警告判为动态安全。

前向bias非None且原始x.dtype不是HIFLOAT8时，按meta_outputs.dtype提升bias；x/weight始终按Meta dtype提升。该条件在x提升之前判断，因此不能概括为所有输入和bias总是统一转换。反向把grad_output/weight提升到x.dtype，保存x_dtype和提升后的grad_dtype，不按每个输出Meta独立选择dtype。

padding长度为1时前向先乘3；输入以Meta rank==3表示一维卷积时，向stride/padding/dilation/output_padding的首部insert对应1/0，同时x/weight在轴2补维，最后Squeeze输出。反向用x.rank==3判断，同样补x/weight/grad并按需Squeeze两个梯度。这里有Python列表原地修改，不能视为不影响复用实参的纯函数；前反向对padding长度的处理也不能互相照搬。

## 普通与转置卷积的尺寸路径

| 路线 | 节点、尺寸与布局 |
| --- | --- |
| 普通2D及补维的1D | Conv2D，strides/dilations扩为[1,1,H,W]，pads为[H,H,W,W]，groups透传，data_format=NCHW。 |
| 普通3D | Conv3D，strides/dilations扩为[1,1,D,H,W]，pads每轴成对，data_format=NCDHW；bias输入单独标ND。源码关于2024.02前padding小于kernel的warning不是本次实测或所有版本能力表。 |
| 转置2D | 用Shape(x)/Shape(weight)获取N、空间轴和weight通道1*groups，按下述公式计算H/W，提升为INT32并Pack；Conv2DTranspose收到该input_size及扩展output_padding。 |
| 转置3D | x和weight的symsize都存在且不含torch.SymInt时，在Python按_symsize计算；否则用Shape/Gather与GE算术。两种结果均转INT32/Pack，传Conv3DTranspose与output_padding。 |

每个转置空间轴的输出尺寸为(input-1)*stride+dilation*(kernel-1)+1-2*padding+output_padding。常量尺寸和GE尺寸不是相同的动态路径；最终INT32尺寸也不能保证任意极大索引无损。前向按meta_outputs.rank为3/4选2D，其余直接选3D，没有完整拒绝任意非法rank的本地校验。

specific_op_input_layout/output_layout只追加节点属性，不执行物理Transpose。转置卷积的input_size/bias标ND、数据与filter标NCHW或NCDHW，不能凭属性标记断言任意channels_last或非连续输入已经转换。

check_input_dtype只显式拒绝DT_FLOAT8_E4M3FN，前向在转置2D/3D辅助路径调用，普通Conv2D/3D没有同样检查。不能把“does not support 8-bit”报错文字扩为所有8位dtype、所有卷积入口的统一禁令；没有本层拒绝也不是底层支持证明。

## 反向mask能省去局部节点，但类型仍有分支

各npu_conv*_backward辅助函数先把grad_x/grad_weight/grad_bias置None，只在相应output_mask为True时构造该梯度。这个行为与其他归一化Converter只屏蔽部分输出不同；图中最终是否消除全部成本仍需核对编译结果。

| 反向路线 | 输入梯度 | 权重梯度 | bias梯度 |
| --- | --- | --- | --- |
| 普通2D/1D | Conv2DBackpropInput，静态_symsize可直接作input_size，否则Shape(x) | Conv2DBackpropFilter，filter_size=Shape(weight)，非FLOAT目标时Cast到原x.dtype | FlattenV2(axis=2)后沿[0,2] ReduceSum |
| 普通3D | Conv3DBackpropInput，input_size=Shape(x) | Conv3DBackpropFilter，filter_size=Shape(weight)，非FLOAT时Cast到x.dtype | FlattenV2(axis=3)后沿[0,2,3] ReduceSum |
| 转置2D/1D | 以grad为输入、weight为filter的普通Conv2D | Conv2DBackpropFilter把x=grad、out_backprop=原x，非FLOAT时Cast到提升后的grad.dtype | 与普通2D同样的Flatten和归约 |
| 转置3D | 以grad为输入的普通Conv3D | Conv3DBackpropFilter同样交换x/out_backprop，静态weight._symsize或Shape(weight)提供filter_size；非FLOAT时Cast到提升后的grad.dtype | 与普通3D同样的Flatten和归约 |

此处“非FLOAT”来自源码is not DataType.DT_FLOAT的判断；未认证kernel内部累加精度。bias_sizes虽可能被从Meta转为Python列表，后续未用于梯度shape或节点。转置反向辅助签名接受output_padding，但没有把它作为属性传给上述GE节点；不应据此承诺任意output_padding都完成验证。

普通分支只显式处理输入rank3/4/5；其他rank会落到后面的转置路径代码。应按合法模型输入核对，不把这个控制流当额外rank支持。反向的E4M3FN检查分布在输入/权重梯度辅助函数，转置输入梯度与bias归约没有相同检查，不能按一个报错概括整条反向。

## 量化Conv2D修改描述符，不是统一Cast

准确入口torch.ops.npu.npu_quant_conv2d.default检查**meta_outputs.rank==4**，不直接检查x.rank；offset非None明确拒绝。output_dtype仅允许源码集合中的Torch数值5(FP16)、6(FP32)、15(BF16)以及torch_npu.hifloat8；签名默认0不在这个允许集合，不能把默认值写成自动推导输出精度。

stride/pads/dilations为GE Tensor时直接拒绝，这与普通卷积读取_meta固化属性不同。虽然签名Optional，这里随后直接下标[0]/[1]，没有None默认列表补全。列表长度、scale/bias形状、offset_x和round_mode值域没有在此层完整校验；不由透传推导所有组合有效。

output_dtype经torch_dtype_value_to_ge_proto_type翻译为ProtoDataType后传QuantConv2D的dtype；x_dtype/weight_dtype非None时直接改写x.desc.dtype/weight.desc.dtype，**没有创建Cast节点**，不能用于任意数值重编码或当成无副作用的精度转换。对于hifloat8输出还改写out.desc.dtype。类型辅助函数接受其他数值，只代表翻译函数有分支，不给本QuantConv2D的kernel增加支持；TORCH_DTYPE_MAP中的bits8值21也不在其输出允许集合。

QuantConv2D传scale、bias、offset=None、data_format=NCHW、groups、offset_x、round_mode及展开的strides/pads/dilations。本层没有证明scale/offset量化公式、所有目标设备或描述符改写对共享边的安全性；优化需要继续结合准确IR和kernel核对。

## QuantConv2D的Eager路由改变输出精度与舍入合同

本节定向对照OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`及其对应固定TorchNPU helper。两版QuantConv C++主体去除注释/空白后的差异只有发布分支额外打印current soc not support aclnn警告；Meta函数AST相同。此处的路由与分配观察不认证任一设备的完整接口能力。

入口先通过DO_COMPATIBILITY检查`aclnnQuantConvolution`及其GetWorkspaceSize符号；缺符号时，IsAclnnOnly为True直接报错，其他情形调用旧ACL。符号齐全后也不是全部设备走ACLNN：仅IsAclnnOnly为True调用本地ACLNN包装，否则仍调旧ACL。固定TorchNPU两版的IsAclnnOnly定义均为SoC枚举>=Ascend950；这是源码路由门槛，不是本卡平台矩阵或后端算子的产品支持表。

| 事项 | 本地ACLNN包装 | 旧ACL QuantConv2D | 前述GE Converter |
| --- | --- | --- | --- |
| 输出容器/精度 | 必须显式给output_dtype，接受FP16/FP32/BF16/HiF8对应枚举，按[N,Co,Ho,Wo]用apply_tensor_without_format分配。 | 先分配NCHW FP16，out辅助层仅接受FP16枚举；其他输出类型不能因GE可构图而视为本路由已接受。 | 允许上述浮点/HiF8输出，输出dtype写入IR。 |
| HiF8提示 | input_dtype/weight_dtype必须同时None或同时HiF8；给提示时两个载体都须int8/uint8，再成对TensorWrapper重解释。 | 签名接收两提示，但此实现体没有应用它们，也没有用它们创建HiF8 wrapper。 | 分别直接改写x/filter描述符，局部没有同样的成对检查；整个构图仍可能先受Meta约束。 |
| round_mode | 原字符串经char*传入ACLNN。 | 忽略所传字符串，固定rint属性。 | 原字符串透传IR。 |
| offset | 本地CheckParams要求None。 | 接收该参数但未作为OpCommand输入或属性使用。 | 明确拒绝非None。 |

因此旧ACL回退改变的不仅是调用符号。保持同一个Schema或GE映射，不表示混合平台的精度、舍入与低比特解释完全一致。HiF8提示改变字节解释，不进行量化校准、数值转换或权重布局重排。ACLNN分支还把offset_x从int64收窄为int32；应按Meta的[-128,127]值域先约束合法输入，不能把任意大整数透传写成无损合同。

### Eager薄检查、Meta验证与底层能力分开

C++的两条分配路线都从NCHW位置读取N/H/W和weight的Co/kernel，按对称pads的通常卷积公式计算Ho/Wo并要求>0。rank检查实际为input/weight>=4，属性长度>=2；报错文字里的more than不应改写成严格>。这些薄检查没有证明rank>4、额外属性、负stride、任意groups或任意scale都能运行。

固定Meta更严格：input/weight恰为4维，scale为1维INT64且长度Co，Cin=weight_Cin*groups，Cin/Co可被groups整除；bias若存在须1维Co，对普通INT8输入为INT32，对HiF8/FP8为FP32。属性长度恰为2，pads>=0、stride/dilation>0、groups>=1并限制offset_x。无HiF8提示时，Meta仅接受成对INT8或成对E4M3FN；INT8输出限定FP16，E4M3FN输出限定FP16/BF16/FP32，HiF8提示路径还可输出HiF8字节容器。

这些是选定Meta函数的前端条件；它没有同样显式拒绝非None offset或校验round_mode枚举。Meta通过仍不能消除上表的Eager差异，也不证明后端内核接受全部组合。Schema的output_dtype默认None，而Meta与两个Eager辅助层均要求实际输出精度；不要将省略参数当作自动推导。接入时固定真实路由、量化输入载体、scale编码、bias及舍入，再逐层比较Meta/GE/Eager和参考；本次没有执行这些实验。

## 准确重载与验证

| 可构图入口 | 无条件拒绝的对应重载 |
| --- | --- |
| torch.ops.aten.convolution.default | torch.ops.aten.convolution.out：AssertionError |
| torch.ops.aten.convolution_backward.default | torch.ops.aten.convolution_backward.out：AssertionError |
| torch.ops.npu.npu_quant_conv2d.default | 所选文件没有其他注册重载；不据此否定其他文件能力 |

out报错的“before pytorch 2.1.0/might be supported”不是可用版本承诺。应以真实FX重载、输入rank、静态/动态尺寸、属性是否固化、group与转置参数、mask和输出dtype建立用例，再核对Eager/GE的数值、梯度、描述符和最终图后测性能；本文没有执行这些实验。

- [Converter开发与Meta职责](torchair_converter_implementation.md)
- [文档层卷积与动态限制](torchair_aten_constraint_review.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution_backward.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/convolution_backward.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_conv2d.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_conv2d.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）

## 补充实现证据

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantConv2DKernelNpuOpApi.cpp)（implementation）：所审范围24–268。

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantConv2DKernelNpuOpApi.cpp)（implementation）：所审范围24–156。

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantConv2DKernelNpu.cpp)（implementation）：所审范围13–133。

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantConv2DKernelNpu.cpp)（implementation）：所审范围13–104。

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：所审范围5578–5784。

- [固定实现来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）：所审范围5187–5393。

- [固定实现来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：所审范围6748–6750。

- [固定实现来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：所审范围6548–6550。

- [固定实现来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：所审范围94–119。

- [固定实现来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：所审范围96–110。

- [固定实现来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NpuVariables.cpp)（implementation）：所审范围109–111。

- [固定实现来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NpuVariables.cpp)（implementation）：所审范围108–111。

- [固定实现来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_conv2d.py)（implementation）：所审范围1–127。
