---
type: Guide
title: GE层组与RMS归一化：精度、融合和反向边界
description: 补充量化RMS反向的Eager/Meta类型与shape分配、显式None差异和普通autograd边界，保留层组/RMS的原GE合同。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/_npu_rms_norm_backward_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_cast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_cast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_group_norm_silu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_group_norm_silu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/_RmsNormBackwardQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-10T08:42:35Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE层组与RMS归一化：精度、融合和反向边界

## 版本、架构选择与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。主线完整非空源码、发布版完整AST和注释差异均已审阅。18组实际成对文件中17组AST一致，GroupNormSilu仅docstring空白不同；量化RMSNorm反向的一条映射路径仅主线存在，不据此断言发布软件没有该能力。

is_arch35在主线按设备名包含Ascend910_95、Ascend950或Ascend350选分支，发布版只查前两种；仅捕获ImportError，不能当成完整产品支持矩阵。950对应Ascend950系列（包含旧称Atlas A5），原始设备字符串保留用于分支核对。本卡平台矩阵未知，保持draft与空平台；未执行上游、GE编译、精度/训练或性能实验。declare_supported是候选输入声明，不等于实测覆盖。

specific_op_input_layout/output_layout仅向节点属性追加索引和布局字符串，函数不执行Transpose、数据搬运或物理存储检查。因此下述NCHW/NCDHW/ND标注不独立证明数据已转换或任意stride可用。

## GroupNorm前向的rstd不能当variance

native_group_norm.default在weight/bias缺失时，以C为shape按meta_outputs[0].dtype填1/0。is_arch35调用GroupNormV2，直接返回y/mean/rstd；其他选择调用GroupNorm，拿到variance后把eps转Meta dtype，再Rsqrt(variance+eps)得到rstd。两条路径均标NCHW，is_training=True；N和HxW形参没有直接传入前向GE节点，不表示任意输入和动态形状都已验证。

native_group_norm_backward.default的is_arch35路线把dy/x reshape为[N,C,HxW]、统计量reshape为[N,group]、weight reshape为[C]，缺weight填input.dtype的1；GroupNormGrad收到三个output_mask属性，再将dx恢复Shape(input)。这里仍直接返回dx/dgamma/dbeta，没有额外按mask替换为None。

其他选择把group折进N，以BNTrainingUpdateGrad/BNTrainingReduceGrad复用计算：先用rstd平方的倒数减固定eps=1e-5还原variance，再以同eps构图；weight存在时先乘dy。中间形状含Python表达式-1 if N else 1，符号/Tensor N的Python真值与零输入应另验，不能视为完整动态合同。该路线始终构造dx，output_mask只控制dgamma/dbeta：已知symsize乘积为0时相应返回按mean/rstd dtype填的[C]零，否则dgamma从(dy*(x-mean)*rstd)沿[0,2]归约，dbeta从dy归约。mean rank1会先reshape[N,group]再广播，不能与任意统计量布局混用。

## LayerNorm前反向对默认参数的处理不同

native_layer_norm.default缺weight/bias时填input.dtype的1/0；normalized_shape若为GE Tensor，调用dtype_promote(...INT32)却**没有接回返回值**，随后Fill仍收到原normalized_shape，不能据此认定输入shape已转INT32。普通列表会显式Const(INT32)。最终LayerNormV4(input,normalized_shape,gamma,beta,epsilon=eps)。

native_layer_norm_backward.default缺weight时直接Const(normalized_shape,INT32)再Fill，不复用前向Tensor分支；LayerNormGradV3参数顺序为(grad_out,input,rstd,mean,weight)。bias与output_mask形参在该函数没有参与分支或节点属性，返回GE全部结果，不能由掩码签名断言梯度剪枝、None返回或bias默认路径完整性。GroupNorm/LayerNorm的out重载均直接拒绝，准确异常见表。

## RMSNorm、加法融合和输出顺序

| 准确入口 | GE构图合同 |
| --- | --- |
| torch.ops.npu.npu_rms_norm.default | RmsNorm(self,gamma,epsilon)，默认1e-6，原序返回GE结果。 |
| torch.ops.npu.npu_rms_norm_backward.default | RmsNormGrad(grad,self,rstd,gamma)，按dx/dgamma返回；GE实参顺序与Python签名gamma/rstd顺序不同。 |
| torch.ops.npu.npu_add_rms_norm.default | 直接AddRmsNorm(x1,x2,gamma,epsilon)，原序返回；不能从融合名称推导输入修改、别名或性能收益。 |
| torch.ops.npu.npu_add_rms_norm_v2_functional.default | 先分别TensorMove(x1/x2)，调用AddRmsNorm后返回(out1,out0,out2)，前两项交换；不是直接npu_add_rms_norm的等价返回顺序。函数化拷贝有隔离目的，不能随意消除。 |
| torch.ops.npu.npu_add_rms_norm_cast.default | 直接AddRmsNormCast，Schema列四返回；本层没有额外Cast、输出dtype推导或重新排序，不应补造各输出精度与任意平台支持。 |
| torch.ops.npu.npu_group_norm_silu.default | 直接GroupNormSilu(self,weight,bias,num_groups=group,eps=eps)，eps默认0.0001；可选weight/bias直接透传，没有native_group_norm那样的填1/0逻辑，也不等于已认证任意bias组合。 |

这些映射没有统一按Meta把输入或所有输出提升；需要结合准确IR/kernel和真实dtype验证精度。Support中的F16/F32示例是候选声明，不给所有形状、BF16或累加精度作保证。

## 主线量化反向映射的类型数值域

所选主线存在torch.ops.npu._npu_rms_norm_backward_quant.default：dst_type先经torch_dtype_value_to_ge_type，再传RmsNormGradQuant(dy,x,rstd,gamma,scale_x,offset_x=...,div_mode=...,quant_mode=...,dst_type=...)，返回dx_out/dgamma_out。默认offset_x=None、div_mode=True、quant_mode='static'、dst_type=1。

这里dst_type是该辅助函数解释的Torch dtype数值域，**1映射GE DT_INT8，5为FLOAT16，6为FLOAT，15为BF16，未知值抛RuntimeError**；不能直接把数字1按另一枚举当FP16。辅助函数还识别部分其他dtype数值，只证明类型翻译存在，不证明RmsNormGradQuant的kernel支持其全部取值。此Converter未对scale/offset、quant_mode或div_mode作完整值域校验，不能因原样透传就认证动态量化、所有模式或量化精度。

发布快照缺少同一路径，只记录这个固定tree事实。不能用它推断另一版本没有其他注册位置、其他后端或同名能力，也不将主线文件静默并入发布软件栈。

## 量化RMS反向的Eager分配与Meta缺口

本节补主线OpPlugin`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的_npu_rms_norm_backward_quant。发布`dedc316708372c9a8bfde4527abd2a94b74840f5`无同路径_RmsNormBackwardQuantKernelNpuOpApi.cpp，仅是固定tree差异，不认证任一版本的整栈产品能力；整卡继续draft与空平台。

该内部入口返回(dx_out,dgamma_out)。C++的dx物理shape取dy.sizes，不是x.sizes；dst_type未赋值时用ACL_INT8，赋值时经GetAclDataType和convert_to_scalar_type选择载体，再用TensorWrapper携带逻辑ACL类型。dgamma始终按gamma.shape、gamma设备选项及FP32申请，二者都请求ND格式。普通npu_rms_norm_backward则通过自己的尺寸辅助函数及self.options分配dx，并分配FP32 dgamma；不能仅按都是RMS反向就交换输出合同或量化梯度载体。

本地C++只显式检查dy/x的rank>=1，没有在这个函数验证两者shape一致、rstd/gamma的归一化轴、scale_x/offset_x形状、quant_mode允许集合或完整dtype矩阵。它把quant_mode字符串及Optional div_mode直接传给aclnnRmsNormGradQuant，没有将div_mode=None显式归一为True，也没有普通RmsNormGrad入口那样的旧ACL回退表达式。类型翻译或宏入口存在不证明全部量化模式与低精度kernel已经可用。

### 默认INT8与显式None要分开核对

Schema默认dst_type=1，C++也在Optional无值时选INT8；Meta却直接TORCH_DTYPE_ENUM_VALUE_TO_SCALAR_TYPE_MAP.get(dst_type)，然后以得到的dtype调用torch.empty，没有C++那样的None->INT8显式分支。对None或未知枚举，查表会得到None；本次未执行目标Torch版本，不据此断言最后一定形成哪种dtype或设备异常。前面的GE严格类型翻译又属于另一层，不应预期三条路径自动归一成同一结果。

常见非None枚举的Meta结果为1=INT8、5=FP16、6=FP32、15=BF16，dgamma总为FP32。它直接按dy.shape/gamma.shape及各自device申请，没有复刻C++的rank检查，也没有验证x、rstd、scale或Optional参数。字典中的低比特映射只说明Meta可描述相应载体；这个包装没有据此建立完整打包、scale编码或训练精度配方，不能用Meta通过取代后端验收。

### 普通RMSNorm自动求导没有在此自动接入量化反向

固定derivatives条目把npu_rms_norm的第一输出标为可微、rstd输出不可微，并明确调用npu_rms_norm_backward(grad,self,gamma,result1)。这条声明没有选择_npu_rms_norm_backward_quant；也不能由本次对该条目的局部核对推断其他自定义训练路径均不存在。

训练接入量化反向需明确谁构造dy、谁保存原始x/rstd/gamma、scale/offset来自哪里，以及后续算子如何解释量化dx；FP32 dgamma不代表全部反向中间量或累加都在FP32。分别核对默认/显式dst_type、dy与x形状、输出字节载体、scale/offset、普通与量化显式梯度，再验证真正自动训练路径和数值。此处只有静态合同，没有执行生成式自动求导、设备实验或新增verified。

## 优化与验证入口

从FX节点确认准确重载、归一化轴、mean/variance/rstd含义、输出顺序和Meta；检查Tensor形状、None参数、mask和函数化拷贝如何落入最终GE图，再与Eager核对精度、别名与空输入，最后测融合收益。本次只做静态源码审阅，未执行上述实验。参见[通用Converter开发](torchair_converter_implementation.md)和[文档层ATen约束](torchair_aten_constraint_review.md)。

## 准确入口与拒绝重载

表中仅表示所选Python映射有构图分支，不表示参数、平台或kernel已验证；范围由前文逐项限定。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| native_group_norm | `torch.ops.aten.native_group_norm.default` | `torch.ops.aten.native_group_norm.out` (NotImplementedError) |
| native_group_norm_backward | `torch.ops.aten.native_group_norm_backward.default` | `torch.ops.aten.native_group_norm_backward.out` (RuntimeError) |
| native_layer_norm | `torch.ops.aten.native_layer_norm.default` | `torch.ops.aten.native_layer_norm.out` (RuntimeError) |
| native_layer_norm_backward | `torch.ops.aten.native_layer_norm_backward.default` | `torch.ops.aten.native_layer_norm_backward.out` (RuntimeError) |
| npu_rms_norm | `torch.ops.npu.npu_rms_norm.default` | 无无条件拒绝壳；仍受正文条件限制 |
| npu_rms_norm_backward | `torch.ops.npu.npu_rms_norm_backward.default` | 无无条件拒绝壳；仍受正文条件限制 |
| _npu_rms_norm_backward_quant | `torch.ops.npu._npu_rms_norm_backward_quant.default` | 无无条件拒绝壳；仍受正文条件限制 |
| npu_add_rms_norm | `torch.ops.npu.npu_add_rms_norm.default` | 无无条件拒绝壳；仍受正文条件限制 |
| npu_add_rms_norm_v2 | `torch.ops.npu.npu_add_rms_norm_v2_functional.default` | 无无条件拒绝壳；仍受正文条件限制 |
| npu_add_rms_norm_cast | `torch.ops.npu.npu_add_rms_norm_cast.default` | 无无条件拒绝壳；仍受正文条件限制 |
| npu_group_norm_silu | `torch.ops.npu.npu_group_norm_silu.default` | 无无条件拒绝壳；仍受正文条件限制 |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm_backward.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_group_norm_backward.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm_backward.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_layer_norm_backward.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_backward.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_backward.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/_npu_rms_norm_backward_quant.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_v2.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_v2.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_cast.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_cast.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_group_norm_silu.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_group_norm_silu.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）

## 补充实现证据

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/_RmsNormBackwardQuantKernelNpuOpApi.cpp)（implementation）：1–82。

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormBackwardKernelOpApi.cpp)（implementation）：1–37。

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：35–62,2934–2944。

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：7529–7530。

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）：228–231。

- [固定实现来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/_npu_rms_norm_backward_quant.py)（implementation）：1–28。
