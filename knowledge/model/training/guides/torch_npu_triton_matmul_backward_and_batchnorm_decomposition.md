---
type: Guide
title: Triton矩阵分解与BatchNorm：梯度折叠、复制和舍入条件
description: 区分普通与实验注册入口，记录padded ND折叠、按rank矩阵梯度路径、FP16保存统计量舍入及普通fast GELU。
tags:
- task.optimization
- topic.compilation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
created_at: '2026-11-11T09:16:03Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Triton矩阵分解与BatchNorm：梯度折叠、复制和舍入条件

## 固定共享文件，区分两种注册入口

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf decomposition.py前段完整矩阵/BatchNorm helper、普通Triton注册和所列实验注册入口。没有导入、安装分解、计算梯度、查询设备或运行性能实验；平台与完整数值范围未知，保持draft和空平台。这里不回推发布快照或其他后端的同名行为。

普通_register_triton_decompositions注册本地matmul前/反向；实验_register_triton_experimental_decompositions仅在matmul_backward.default没有现有分解时才补本地反向，并单独写BatchNorm两项。因此“同一文件有这些helper”不等于每个入口都会覆盖相同算子，已有表项和入口顺序必须一起核对。外部decomposition装饰器、下游mm/matmul/BN实现仍独立。

## ND矩阵折叠的额外布局门槛

_matmul_triton只有npu_config.enable_matmul_triton为真、self.device为NPU、self rank>=3、other rank恰2、上游should_fold判False，且_can_fold_padded_matmul_input通过时，才走本地二维mm；否则直接generic_matmul。

布局helper通过guard_or_false先接受numel==0；非空时要求最后stride=1，再从倒数第二维往前累计expected_stride。size==1跳过，其余stride须>=当前expected_stride，随后expected_stride=stride*size，允许连续行之间带padding，不把判据误写成所有stride必须严格等于dense乘积。guard_or_false的外部符号/guard行为不在本卡展开。

接受后以self前面各维乘积作folded_rows，reshape为(folded_rows,K)，mm(other)后用_unsafe_view恢复self前缀加other最后一维的输出形状。reshape是否额外分配依实际布局与外部实现，不是这里保证零复制；布局通过也不替代所有matmul尺寸、dtype或数值验收。enable_matmul_triton字段源码由TORCHINDUCTOR_ENABLE_MATMUL_TRITON解析，向解析器传默认False，未在本组展开完整环境值接受规则。

## 反向先处理整体单例批前缀

_matmul_backward_inductor先读取输入/grad的rank与size，两个输出初值None。两输入rank均>=3时，若self全部leading维能由guard_or_false证明等于1，就把self reshape成最后两维后递归，再按mask把对应梯度reshape回去；否则才尝试同样折叠other的整体单例前缀。它不是对每个局部广播维逐项做通用归约。

后续按原rank组合分路，mask[0]/mask[1]控制各输出计算：

| 输入rank | 本地表达式/组织 |
| --- | --- |
| 1×1 | 请求的梯度分别为other*grad和self*grad。 |
| 2×1 | self梯度为grad与other的外积；other梯度为self转置乘grad后squeeze。 |
| 1×2 | self梯度为grad乘other转置后squeeze；other梯度为self与grad外积。 |
| ND>=3 × rank1/2 | 把grad连续化后折叠成二维，与other或其转置做mm；other梯度另把self连续化再折叠做mm。 |
| rank1/2 × ND>=3 | 按另一侧批前缀乘末维建立folded_rows；梯度和other的转置可显式contiguous/view，计算后恢复shape并转置。 |
| 其余（含2×2和未整体折叠的双ND） | 直接用torch.matmul(grad,other转置)或torch.matmul(self转置,grad)。 |

ND折叠中部分unfolded_grad在检查各mask之前就构造，不能把未请求某个输出概括为这一路完全不做view/contiguous准备。rank1×ND分路的grad使用view而非先contiguous，其他分路也有自己的复制位置；不把所有路径都描述成只改变metadata或一律有同样的内存成本。

通用else没有在这个helper显式sum_to_size处理任意部分广播批维；整体单例前缀的特殊递归不等于覆盖所有广播组合。不能单凭熟悉的矩阵导数公式推断任意ND广播的返回梯度形状已正确，需结合实际调用前的展开/折叠、外部matmul与最终梯度验证。函数也没有统一转dtype、处理所有非法rank/shape或捕获全部mm/view错误。

## BatchNorm先委托，再有条件舍入重算

_batch_norm_with_update_inductor先按functional选择共享的普通或functional分解并调用generic；随后才检查NPU、input.dtype为FP16且running_mean.dtype为FP16。任一不满足就直接返回generic结果，不在此额外重算。该门槛没有同时要求running_var、weight或bias都为FP16，不能把全部参数dtype自动补成同一值。

命中时把result[1]的mean与result[2]的rstd先转为input.dtype，再以[1,C,1,...]形状广播；output用input.float减mean.float、乘rstd.float，有weight/bias时分别以其float值仿射变换，最后转回input.dtype。也就是说，输出使用的是已舍入到FP16的保存统计量，再回FP32参与计算，不能概括成一直保留原FP32统计量的普通BN路径。

functional分支还把result[4]/[5]转到running_mean/running_var各自dtype；返回新的(output,mean,rstd,*result[3:])。它没有在这里逐项重新证明generic返回长度、running-buffer副作用、所有epsilon/布局/形状和设备精度。注释描述对齐NPU CPU fallback的意图，不当作本次运行或所有组合逐位一致的证明。

## 普通注册的fast GELU与实验兼容GELU不同

普通注册先把nll_loss前后向、log_softmax backward、addmm、gelu、expm1、erfc、native_layer_norm、repeat_interleave.Tensor、slice_backward、matmul前后向等交add_overload形成集合，再删除存在的decompositions项；embedding_dense_backward是否加入受allow_embedding_dense_backward_lowering控制，is_ascend950变量为真另加入max_pool2d_with_indices。此处只记录变量门控与实际传参，外部展开helper及产品矩阵另核。

随后expm1为exp(x)-ones_like(x)，erfc为ones_like(x)-erf(x)。enable_fast_gelu为真才给gelu注册x*sigmoid(1.5957691216057308*(x+0.044715*x³))；只接受none/tanh，但两者都走相同近似，函数内没有像实验GELU那样统一先cast FP32。这个模式也不注册本地gelu_backward。不要将它与[实验GELU兼容开关及反向](../../inference/guides/optimization/torch_npu/torch_npu_experimental_triton_gelu_rmsnorm_dropout_rng_decompositions.md)混用或认为所有后端对none含义相同。

普通注册内部最后给matmul.default及matmul_backward.default装入本卡两个helper，并直接调用该内部注册函数。enable_matmul_triton只在前向helper的本地条件中读取，并不在这个注册入口阻止反向helper被注册；关闭一个前向开关不等于撤销全部本地矩阵分解。

排查优化与精度时同时记录注册入口/现有表项、开关、原rank与批前缀、布局guard、显式连续化与mask、实际返回梯度形状、BN保存统计量dtype及GELU模式。分解命中、mm数量或返回dtype不能代替完整模型的别名、梯度、数值与性能验证。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py)：1–287、1146–1221；仅所列有界内容。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)：468–468；仅所列有界内容。
