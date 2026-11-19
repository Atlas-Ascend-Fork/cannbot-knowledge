---
type: Guide
title: SwiGLU双轴MX前反向：结果配对、FP4承载与梯度边界
description: 补齐SwiGLU双轴MX显式前反向的四返回、E8M0尺度容量和FP4物理形状，区分前向偶数与反向64对齐。
tags:
- task.optimization
- topic.compute.quantization
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluMxQuantWithDualAxisOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluBackwardMxQuantWithDualAxisOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_mx_quant_with_dual_axis.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_backward_mx_quant_with_dual_axis.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_mx_quant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_swiglu_mx_quant.py
  role: example
created_at: '2026-11-10T11:36:06Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# SwiGLU双轴MX前反向：结果配对、FP4承载与梯度边界

## 固定来源与任务范围

本卡定向审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的SwiGLU双轴MX量化前向和显式反向包装、Schema及小规模测试。发布`dedc316708372c9a8bfde4527abd2a94b74840f5`不存在这两份同路径包装，不能将主线实现直接写成发布行为，也不能由缺路径推断发布没有其他SwiGLU方案。

这里关注低精度FFN训练集成中的四返回与物理shape；未追完自动求导注册、编译后端和完整设备kernel，整卡平台与软件配套未知，保留draft与空平台。测试的Ascend950条件不是整接口、产品子型或全部FP4/FP8模式的支持认证。

## 前向和反向都是四返回

```text
npu_swiglu_mx_quant_with_dual_axis(x, *, group_index=None,
  activate_left=True, round_mode="rint", scale_alg=1,
  dst_type=24, dst_type_max=0)
  -> (y1, mxscale1, y2, mxscale2)

_npu_swiglu_backward_mx_quant_with_dual_axis(x, y_grad, *,
  group_index=None, activate_left=True, round_mode="rint",
  scale_alg=1, dst_type=24, dst_type_max=0)
  -> (grad1, mxscale1, grad2, mxscale2)
```

前向把x尾维一分为二，输出激活结果的两套量化表示；反向以原x和上游y_grad作为输入，也返回两套量化梯度及其尺度。下划线反向入口是显式算子，不等于对前向调用`.backward()`必定自动走这条路径；两套梯度也不是两个独立模型参数的grad，不能按普通单Tensor梯度接口消费。

与[单轴SwiGLU MX](../../inference/apis/torch_npu/npu_swiglu_mx_quant.md)的两个返回、[独立双轴动态量化](../../inference/apis/torch_npu/npu_dynamic_mx_quant_with_dual_axis.md)的参数矩阵分开使用。本入口没有单轴接口的activate_dim/group_mode/swiglu_mode等参数，不继承其默认值、量化算法组合或公开平台矩阵。

## 先按逻辑维度配对，再解释物理承载

令前向输入为[...,M,2D]，逻辑激活形状S=[...,M,D]，G为给定group_index的第0轴长度。包装先按未打包的S分配两套尺度，再处理数据的FP4承载；尺度形状不能跟随物理尾维再次除2。

| 项 | 前向逻辑shape或尺度容量 | 反向逻辑shape或尺度容量 |
| --- | --- | --- |
| 两个量化数据结果 | S=[...,M,D] | X=[...,M,2D]，与原x逻辑shape一致 |
| mxscale1 | [...,M,ceil(D/64),2] | [...,M,ceil(2D/64),2] |
| mxscale2，无group_index | [...,ceil(M/64),D,2] | [...,ceil(M/64),2D,2] |
| mxscale2，有group_index | [...,floor(M/64)+G,D,2] | [...,floor(M/64)+G,2D,2] |

group_index存在与否使用不同的ceil/floor表达式；不要把分组容量替换成全局ceil(M/64)，也不要从G个槽推导所有尺度都有效。包装只按组数量分配，没有在这里验证边界值、完整性、dtype或分组语义；测试用[2,4]不能充当所有调用的group_index协议。

两套scale都是**UINT8物理Tensor、ACL_FLOAT8_E8M0解释**，尾维2是编码布局的一部分。这里只能由包装证明上述容量和dtype，不能把64这个分配除数当成完整数学量化块定义，或把普通整数cast成UINT8当成E8M0编码。必须连同所选后端的解码与两轴分组规则验证，不能把scale1直接与第二份数据配对。

指定FP4 E2M1或E1M2时，两份数据均使用UINT8承载，**都把物理尾维再除2**；第二轴量化不意味着改为压缩M。前向原x尾维必须被4整除，最终物理尾长为原来的1/4；反向数据物理尾长为原x的1/2。普通非FP4分支按dst_type换成ACL类型后再映射成相应Tensor scalar dtype；分配分支不认证所有枚举与round_mode/scale_alg组合已受设备支持。

例如x=[128,128]，前向逻辑两份数据各[128,64]、FP4物理各[128,32]，scale1为[128,1,2]；反向逻辑两份各[128,128]、FP4物理各[128,64]，scale1为[128,2,2]。同一个group_index下scale2的最后一个逻辑数据轴也不同，不能跨前反向直接复用尺度缓冲。

## 前向能分配不代表反向也接受

前向包装要求rank至少2、尾维偶数；FP4另要求减半后尾维仍为偶数。显式反向更严格，要求原x尾维为正且可被64整除；只满足前向偶数检查的FFN形状不自动满足这条低精度反向路线。

反向局部包装没有完整校验y_grad与前向输出的对应shape、device和dtype，也没有检查activate_left、round_mode、scale_alg、dst_type_max的完整合法矩阵。测试按y_grad尾长等于x尾长/2构造，但不能用未做局部检查来放开任意梯度形状。前反向必须固定相同门控两半与模型语义，并另外验证实际梯度公式、有限值、尾块和量化误差。

两个入口分别缓存检测`aclnnSwigluMxQuantWithDualAxis`和`aclnnSwigluBackwardMxQuantWithDualAxis`，缺失则提示升级CANN；没有在本函数回退成普通SwiGLU加独立量化。符号可找到只是包装条件，不是设备支持、量化精度或性能实测。

## 测试参考不足以代替训练验收

前向测试只有两个BF16常量1用例、FP8 E4M3目标，有分组和无分组；反向两个方法检查shape，另一个精度方法使用常量x/y_grad及硬编码字节。没有这组测试里的FP4数值验收、随机非均匀分布或完整训练步。测试把数据输出`.to(uint8)`后与字节表比较，而数值转换与位重解释是不同操作；必须先确认实际输出容器/逻辑dtype，不将这些断言当作通用FP8位编码金标准。本卡没有执行任何方法。

接入时先分别构造非量化SwiGLU前向与梯度参考，再按真实后端规则解码两份结果及各自scale；覆盖两种activate_left、分组边界、非64整块、FP4尾维、异常值和未分组路径。下游GEMM必须消费匹配轴的结果和尺度。融合可减少独立SwiGLU及两次量化的中间遍历，但同时分配两份数据和两份尺度；只有连同上下游矩阵乘、临时内存和完整训练步计时才能判断收益。没有新增verified或性能数字。

## 完整包装的空组与ABI补充

group_index缺省以未定义Tensor下传；一旦给定已定义Tensor，即使第0维长度为0，两个包装都会进入floor(M/64)+G的尺度容量分支。例如M=33、G=0的已定义空组在该表达式中得到0，无组则ceil(33/64)=1；这是Host形状分配的静态差别，不证明空组为合法后端输入。这里没有检查group_index的rank/值域、顺序或真实token覆盖，标量组也不能由size(0)访问推成受支持。

前向ACLNN参数按x、group_index、activate_left、round_mode指针、scale_alg、所选ACL dtype、dst_type_max，再交y1/scale1/y2/scale2四个wrapper；反向在x之后另插y_grad，其余对应。round_mode直接使用string_view.data cast，不在本函数复制成另一套字符串或检查所有枚举。两条缓存符号检查没有普通激活/量化回退；数据与尺度分配遵循前表逻辑形状，FP4数据打包不再次改变尺度容量。

## 双轴测试只给有限常量与形状参考

前向91行文件的两个golden helper都返回固定UINT8字节表，没有读取输入数值来计算一般SwiGLU/MX量化。两个Ascend950方法只用BF16全1的[4,8]、FP8 E4M3目标、activate_left=True、rint/scale_alg=1；分别传group_index=[2,4]和None。两份数据按[4,4]比较，scale1为[4,1,2]，scale2有组[2,4,2]、无组[1,4,2]；数据表均为128，尺度使用[118,0]。它没有逐项验证任意组边界，输入requires_grad=True之后也没有执行.backward或完整训练步。

反向107行文件的两个shape方法使用BF16 x=[128,128]和全1 y_grad=[128,64]，只核四输出shape，组[2,4]或None；expected-shape helper直接复刻ceil/floor公式，不能当作独立后端数值验证。精度方法改为x=[4,64]、y_grad=[4,32]，固定参考两份数据每行前32项240、后32项128，scale1每行为[119,118]，scale2按两组重复前半[119,0]/后半[118,0]；它没有调用真实前向生成y_grad或独立计算一般导数。

双轴这些数值比较都将实际数据`.to(torch.uint8)`，属于数值转换；它与位重解释的view不同。生成器只处理FP16/BF16两条分支，未覆盖其它dtype。固定表、设备装饰器、可执行的测试名称或requires_grad属性均不认证FP4、随机非均匀输入、两种门控方向、异常值、自动梯度或模型收敛；本卡没有运行任何方法。

## 单轴小样本与发布测试缺口对照

为区分四返回双轴与两返回单轴，本卡也完整静态审阅两版各56行的test_npu_swiglu_mx_quant.py。主线方法只用BF16全1[4,8]、FP4 E2M1目标及单轴helper默认参数；golden只对这一个数值/shape组合返回y=[4,2]且字节119、scale=[4,1,2]且编码[124,0]，其它输入分支隐式None。数据以view([4,2]).view(torch.uint8)做位重解释，尺度以.to(uint8)读取；另外对scale做atol=0.01/rtol=0.001比较，不是一般SwiGLU/FP4数学参考。helper透传的多个属性并不表示该方法实际覆盖了那些组合。

发布同路径测试有实质差异：golden条件却是全0[1,2,2]，方法仍生成全1[4,8]，所以这条调用不进入golden的返回分支；它还把scale取为npu_output[2]，与所保留[单轴接口两返回](../../inference/apis/torch_npu/npu_swiglu_mx_quant.md)合同冲突。该方法名残留add_rms_norm_quant_float8_e5m2_with_rstd，golden数据构造dtype也改成FP4，而主线固定表是UINT8；不能仅凭方法名判定实际测试对象或把两个版本当成相同验收证据。

这些是实际源代码/AST差异，本卡没有执行并报告某个异常已经复现。单轴测试两版均没有调用.backward；双轴两个CPP和两份测试在发布tree的相同路径均为空，也只证明路径差异，不否定发布其它SwiGLU实现。接入应分别验证单/双轴的返回槽、位表示、真实梯度和分组有效区，不能用一份常量表互相认证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluMxQuantWithDualAxisOpApi.cpp)（primary）

- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluBackwardMxQuantWithDualAxisOpApi.cpp)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_mx_quant_with_dual_axis.py)（example）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_backward_mx_quant_with_dual_axis.py)（example）

## 完整与有界来源

- [SwigluMxQuantWithDualAxisOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluMxQuantWithDualAxisOpApi.cpp)（primary）：1–126；完整本地文件。
- [SwigluBackwardMxQuantWithDualAxisOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluBackwardMxQuantWithDualAxisOpApi.cpp)（implementation）：1–127；完整本地文件。
- [test_npu_swiglu_mx_quant_with_dual_axis.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_mx_quant_with_dual_axis.py)（example）：1–91；完整本地文件。
- [test_npu_swiglu_backward_mx_quant_with_dual_axis.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_backward_mx_quant_with_dual_axis.py)（example）：1–107；完整本地文件。
- [test_npu_swiglu_mx_quant.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_swiglu_mx_quant.py)（example）：1–56；完整本地文件。
- [test_npu_swiglu_mx_quant.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_swiglu_mx_quant.py)（example）：1–56；完整本地文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：7023–7024、7026–7027；仅此Schema片段。
