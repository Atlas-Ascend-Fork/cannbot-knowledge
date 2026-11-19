---
type: Guide
title: 实验Triton数学分解：GELU兼容模式、RMSNorm与Dropout掩码
description: 保存GELU/erf计算dtype和兼容选择、RMS归约/转回边界、dropout按shape选路及首Tensor RNG设备门槛。
tags:
- task.optimization
- topic.compilation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py
  role: primary
created_at: '2026-11-11T08:49:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton数学分解：GELU兼容模式、RMSNorm与Dropout掩码

## 固定注册层与数值边界

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf decomposition.py中完整的GELU/erf、RMSNorm、native dropout、bilinear vec dispatcher与RNG gate函数。安装顺序和共享表关系见[分解注册与softmax](torch_npu_experimental_triton_softmax_decomposition_and_mask_domain.md)。没有导入、注册、运算Tensor、调用兼容开关、随机数或设备实验；产品及完整数值范围未知，保持draft和空平台。

这些是实验后端写入共享分解表的Python函数，不等于每个同名原生算子的完整硬件合同。外部兼容API、torch数学/广播、私有dropout和原生fallback仍独立。源码中对齐设备实现、bit-exact或示例收益的文字不作为本次执行证据。

## GELU的none取决于兼容开关

_use_tanh_approx在approximate为tanh时返回True；为none时返回not are_compatible_impl_enabled()；其他值抛RuntimeError。兼容查询的任意Exception被转成False，因此查询不可用也使none走True分支。不能把默认none无条件等同于erf数学路线，更不能从参数名字推断当前会话实际采用的近似。

GELU前向先记x.dtype，非FP32就转FP32。True分支实际表达式为x/(1+exp(-beta*(x+kappa*x^3)))，beta=1.595769121605730711759、kappa=0.044715；False分支为(1+erf_pade(x/√2))*(0.5*x)。最后非FP32输入转回原dtype，没有在此做输入值域或误差界检查。

erf_pade先将输入依序clamp_max(3.92)、clamp_min(-3.92)，以x²计算固定P/Q Horner多项式并返回P/Q。单独注册的aten.erf.default也先将非FP32输入转FP32，再转回原dtype；它不是在这个分解里调用系统原生erf。FP64输入转回FP64并不恢复中途舍去的精度，不能据输出dtype称为全FP64计算或任意特殊值都与其他实现逐位一致。

GELU反向以grad.dtype决定转换：只有grad非FP32时，grad与self都显式转FP32；grad已为FP32时，没有对self独立cast。True分支用固定beta/AN/A3常量形成px、div、resp，只把resp中的NaN替换为0，然后返回grad*(resp+div)。False分支用erf_pade构造cdf，以exp(-0.5*self²)构造pdf，再返回grad*(cdf+self*pdf)。输出按原grad dtype恢复。

resp局部NaN替换不等于整条前/反向对所有NaN/Inf作同一处理；混合grad/self dtype也不能概括为所有路径都在同一计算dtype运行。安装函数分别覆盖aten.erf.default、gelu.default与gelu_backward.default，wrapper自身没有单独NPU device门槛；适用范围需结合共享注册和实际后端核对。

## RMSNorm只在明确位置转换与归约

npu_rms_norm先记录x.dtype并执行x.float()，按最后一维计算mean(x²,keepdim=True)，加epsilon（默认1e-6）后rsqrt；输出为(x*rsqrt*weight).to原x.dtype，返回(output,rsqrt)。weight没有在此显式转为同一dtype，rsqrt也作为该中间值返回，不能由output的转回推断全部中间dtype和所有广播均已认证。

反向直接按输入表达式计算dx，没有在本函数统一cast或将dx转回原x dtype。dgamma为(grad_output*x*rsqrt).sum(tuple(range(grad_output.dim()-1)),keepdim=False)，意图覆盖所有leading维，不只sum(0)。rank、空tuple归约、外部Tensor.sum语义与实际权重形状仍按调用合同核对，不能从这行代码推断所有rank均已完成运行验证。

两项注册针对npu.npu_rms_norm.default和npu_rms_norm_backward.default，不是在这里覆写所有torch.nn.RMSNorm或任意多维normalized_shape实现，也没有补本地shape、epsilon正数或dtype组合校验。

## native dropout按设备、训练和概率分路

安装时快照原_inductor forward/backward及extra_random_decomps forward表项。_is_npu只接受torch.Tensor且device.type为npu；非NPU输入分别调用保存的原函数，不存在时返回NotImplemented。重新安装可形成快照委托链，不能从三个函数上的_npu_decomp_override标记推断本函数自身拒绝所有重复安装。

NPU前向将train=None视为训练。p==0或非训练时返回input.clone和同shape bool全1 mask；p==1时返回zeros_like output和bool全0 mask；其余直接调用npu._npu_dropout(input,p)，注释描述该路线产生packed uint8 mask。这里没有独立对任意p类型/范围作完整检查，剩余前提交下游。

反向先由scale求p：scale==0时p=1，否则p=1-1/scale；p==0返回grad clone，p==1返回zeros。其余**按mask.shape是否与grad_output.shape相同**选择路线：相同就用grad*mask.to(grad.dtype)*scale；不同才把grad_output.contiguous后调用npu.npu_dropout_backward(grad,mask,p)。实际谓词不是mask.dtype==bool，也没有在此全面解析packed编码或验证任意mask来源。

连续化只在这条私有backward路线显式执行，解决注释所述bit mask与梯度遍历顺序的衔接意图；不从一次contiguous推断所有别名、跨流、mask长度和梯度精度均已验收。三个wrapper写入两个分解表，其中extra_random表的forward需单独替换，不能只看_inductor字典的同名项判断fast_random实际调用哪个函数。

## RNG gate只找第一个直接Tensor

_npu_rng_gate处理uniform/uniform_、rrelu_with_noise各列出的packet及bernoulli，枚举packet overload，只对两张表中已存在且没有_npu_rng_gate属性的函数套wrapper，不凭空补全所有随机算子。

wrapper按位置实参顺序找第一个直接Tensor，再按kwargs值顺序找；不递归容器，也不扫描到所有Tensor后再综合判设备。该第一个Tensor为NPU时返回NotImplemented，其他情况委托orig；不能把它概括为“任意实参包含NPU Tensor都退原生”。属性存在就跳过重包，未在这里验证任意外部函数同名属性的值或完整行为。

末尾只在bernoulli.default缺lowering时直接写fallback_handler(add_to_fallback_set=False)。这是使幸存节点有lowering的局部处理，不是在这里关闭所有编译，也不保证每个随机op都能在图捕获中重放；[激活与fallback指南](torch_npu_experimental_triton_activation_and_lowering_routes.md)另有Bernoulli整图捕获原因门槛。注释的精确eager随机序列要求仍需结合真实原生generator和最终运行验证。

## bilinear vec是进程级dispatcher入口

_register_upsample_bilinear2d_vec_dispatcher先检查自己的_done属性，未完成时为Autograd和CompositeImplicitAutograd两key安装py_impl。wrapper通过外部upsample_compute_output_size得osize，用truthy scale_factors或(None,None)提供两个scale，再调用aten.upsample_bilinear2d.default。它没有在本地验证任意scale列表长度，也没有额外设备gate。

_done只在两个注册调用都完成后置True；不能从“只注册一次”的注释推导中途失败会自动回滚第一个key或重试必定成功。外部尺寸计算、dispatcher重入和原生插值精度不在本卡展开。

排查模型精度或反向差异时，应分别记录兼容模式、原始/中间dtype、GELU近似路线、RMS归约维、dropout训练状态与scale/p、mask形状与实际编码、连续化、RNG实参扫描和实际表项。函数注册成功、输出dtype恢复或退出通用随机分解，都不能单独替代完整数值、梯度、确定性和性能验证。

## 固定来源

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py)：1–20、804–1143；仅所列完整函数与导入，外部实现另计。
