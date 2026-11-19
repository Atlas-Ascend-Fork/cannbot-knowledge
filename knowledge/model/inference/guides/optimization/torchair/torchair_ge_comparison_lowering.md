---
type: Guide
title: GE比较与逻辑转换：混合类型和重载边界
description: 比较13组Converter对输入公共类型、单侧Cast、bool运算和缺Meta的不同处理，限定准确重载与静态证据。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/eq.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/eq.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ne.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ne.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ge.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ge.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/le.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/le.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/lt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/lt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/less.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/less.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_and.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_and.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_or.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_or.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_not.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_not.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_and.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_and.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_or.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_or.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_not.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_not.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T06:58:25Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE比较与逻辑转换：混合类型和重载边界

## 固定版本与证据强度

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的准确Converter、导入绑定及辅助函数。逐个审阅主线全部非空源码，发布版以完整AST比对、全部AST差异和注释差异复核；不把语法相同写成字节相同。两个快照分开管理，不推导与任意TorchNPU主线配套。

本文是构图层静态合同，未执行上游代码、smoke、GE编译、NPU数值或性能测试；没有覆盖整卡的产品矩阵，保持draft和空平台。declare_supported列出的shape、dtype、混合类型及标量仅是声明/测试输入候选，不是运行通过记录，也不是完整输入域或硬件支持表。Meta规格、显式Cast、GE后续类型处理及实际kernel仍需分别核对。

dtype_promote按调用方指定的target_dtype处理：GE Tensor在dtype不同时插Cast，torch.Tensor也仅在类型不同时转Cast，非Tensor转对应dtype的Const；它本身不计算PyTorch公共类型，也不自动把所有输入扩成相同shape。单输入返回对象，多输入返回tuple。需要动态运行值时不能拿Python标量Const替代；广播与真实数值正确性不由此函数独立证明。

## 比较器不能共用一条类型提升规则

比较结果的bool dtype不能拿来作为操作数的统一计算dtype；这些Converter实际分别采用输入dtype、torch.result_type或私有get_higher_dtype。后两者依赖该快照配套PyTorch，不能从命名推导任意PyTorch版本规则相同。

| 准确入口 | 此层的类型处理与分支 |
| --- | --- |
| eq.Tensor | 输入dtype不相等就AssertionError；消息误把other.dtype打印两次，错误文本不能还原self真实dtype。相同则Equal，没有通用混合类型提升。 |
| eq.Scalar | 从self.meta与other（GE Tensor时取other.meta）用torch.result_type选择操作数dtype；Meta缺失得到None时跳过显式提升，再Equal。 |
| ne.Tensor、ne.Scalar | 通过Meta的torch.result_type后NotEqual；Scalar分支却以isinstance(other,torch.Tensor)决定是否取other.meta，与eq/gt使用GE Tensor检查不同。不能由类型注解Union[Number,Tensor]推定图Tensor实参一定正确处理；缺Meta也不代表已验证兼容。 |
| gt.Tensor、gt.Scalar | 从Meta用torch.result_type；结果bool时改FP32，显式处理输入后Greater。 |
| ge.Tensor | 检查两输入为BOOL、UINT8、INT8/16/32/64、FP16/BF16/FP32/FP64之一；类型不同用torch._prims_common.get_higher_dtype，相同且bool时转FP32，再GreaterEqual。此列表属于本层校验，不独立认证目标产品kernel。 |
| ge.Scalar | 仅将other按self.dtype处理后GreaterEqual，没有调用Tensor分支的check_support_dtype或相同的混合类型算法。大浮点标量与整型self不能直接假定遵循gt.Scalar的计算精度。 |
| le.Tensor、le.Scalar | 都检查上述类型集合；Tensor读取双方dtype，Scalar把Python类型经type_to_dtype（GE Tensor则读dtype），不同类型用get_higher_dtype，同为bool则FP32，再LessEqual；不等同于仅将other转self.dtype。 |
| lt.Tensor、lt.Scalar | Tensor直接Less；Scalar显式Cast(other,dst_type=self.dtype)再Less。没有在这两个函数中共享eq的不同类型拒绝、gt的result_type或le的提升代码。原注释说bool未实现且dtype需相同，而declare_supported又含INT8/FP32混合样例；保留为声明/注释冲突，不记录成混合输入已实测通过。两版AST差异只是说明字符串与注释表达，计算分支相同。 |
| less.Tensor | dtype不同时只将other转换为self.dtype后Less，可能与交换输入或选择公共类型得到不同计算精度；less.Scalar仍是未实现壳，不能由数学别名推导与lt.Scalar转换合同相同。 |

## 按位与逻辑操作分开审阅

bitwise_and.Tensor先按Meta输出dtype处理输入，bool时LogicalAnd，否则BitwiseAnd；bitwise_or.Tensor相同地选择LogicalOr/BitwiseOr。bitwise_not.default按输入是否bool选择LogicalNot/Invert。标量按位重载及out在所审阅文件中都直接拒绝，不能从Tensor转换中出现标量Const就认定Scalar overload已接入。

logical_and.default明确将两个输入转BOOL再LogicalAnd；logical_or.default按meta_outputs.dtype处理后LogicalOr，不能把前者的硬编码BOOL写成后者原码。logical_not.default先转BOOL、LogicalNot，若Meta存在且输出非BOOL，再转指定输出dtype。逻辑真值与整数逐位运算是不同合同；不能为消除Cast随意互换。

## 验收与适用边界

定位时记录准确overload、双方dtype、Python标量类型及输入Meta是否存在；同为比较器，不从布尔输出反推输入统一为bool。检查Cast是否发生在比较前、是否只处理右操作数，覆盖超出整数范围的浮点标量、同为bool、混合整浮点、广播和缺Meta的诊断分支。需要设备实验分别验证数值及编译支持，当前均未执行。

下表列出全部注册重载的直接拒绝情况，表中存在入口不表示所有声明shape/dtype均可执行。通用方法见[Converter开发](torchair_converter_implementation.md)，算术与舍入见[GE算术转换](torchair_ge_arithmetic_lowering.md)，纯占位文件见[GE未实现overload](torchair_ge_unimplemented_overloads.md)。

## 精确overload与直接拒绝清单

每格使用完整torch.ops标识；有构图分支仍须满足上文条件。拒绝栏仅指实际选中此内置Converter后的无条件异常，不否定高层函数可以经分解、其他overload或其他后端执行。两快照本表身份和直接拒绝类型相同；字符串中的旧PyTorch版本提示只保留为诊断消息，不当作当前兼容矩阵。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝的准确入口及异常 |
| --- | --- | --- |
| eq | `torch.ops.aten.eq.Tensor`、`torch.ops.aten.eq.Scalar` | RuntimeError：`torch.ops.aten.eq.Scalar_out`、`torch.ops.aten.eq.Tensor_out`、`torch.ops.aten.eq.int_list`、`torch.ops.aten.eq.device`、`torch.ops.aten.eq.bool`、`torch.ops.aten.eq.int`、`torch.ops.aten.eq.complex`、`torch.ops.aten.eq.float`、`torch.ops.aten.eq.int_float`、`torch.ops.aten.eq.float_int`、`torch.ops.aten.eq.float_complex`、`torch.ops.aten.eq.complex_float`、`torch.ops.aten.eq.default`、`torch.ops.aten.eq.str`、`torch.ops.aten.eq.float_list`、`torch.ops.aten.eq.Tensor_list`、`torch.ops.aten.eq.bool_list`、`torch.ops.aten.eq.str_list` |
| ne | `torch.ops.aten.ne.Tensor`、`torch.ops.aten.ne.Scalar` | RuntimeError：`torch.ops.aten.ne.Scalar_out`、`torch.ops.aten.ne.Tensor_out`、`torch.ops.aten.ne.int_list`、`torch.ops.aten.ne.device`、`torch.ops.aten.ne.bool`、`torch.ops.aten.ne.int`、`torch.ops.aten.ne.complex`、`torch.ops.aten.ne.float`、`torch.ops.aten.ne.int_float`、`torch.ops.aten.ne.float_int`、`torch.ops.aten.ne.float_complex`、`torch.ops.aten.ne.complex_float`、`torch.ops.aten.ne.default`、`torch.ops.aten.ne.str`、`torch.ops.aten.ne.float_list`、`torch.ops.aten.ne.Tensor_list`、`torch.ops.aten.ne.bool_list`、`torch.ops.aten.ne.str_list` |
| ge | `torch.ops.aten.ge.Tensor`、`torch.ops.aten.ge.Scalar` | NotImplementedError：`torch.ops.aten.ge.Scalar_out`、`torch.ops.aten.ge.Tensor_out`、`torch.ops.aten.ge.int`、`torch.ops.aten.ge.float`、`torch.ops.aten.ge.int_float`、`torch.ops.aten.ge.float_int`、`torch.ops.aten.ge.default`、`torch.ops.aten.ge.str` |
| gt | `torch.ops.aten.gt.Tensor`、`torch.ops.aten.gt.Scalar` | RuntimeError：`torch.ops.aten.gt.Scalar_out`、`torch.ops.aten.gt.Tensor_out`、`torch.ops.aten.gt.int`、`torch.ops.aten.gt.float`、`torch.ops.aten.gt.int_float`、`torch.ops.aten.gt.float_int`、`torch.ops.aten.gt.default`、`torch.ops.aten.gt.str` |
| le | `torch.ops.aten.le.Tensor`、`torch.ops.aten.le.Scalar` | RuntimeError：`torch.ops.aten.le.Scalar_out`、`torch.ops.aten.le.Tensor_out`、`torch.ops.aten.le.int`、`torch.ops.aten.le.float`、`torch.ops.aten.le.int_float`、`torch.ops.aten.le.float_int`、`torch.ops.aten.le.default`、`torch.ops.aten.le.str` |
| lt | `torch.ops.aten.lt.Tensor`、`torch.ops.aten.lt.Scalar` | RuntimeError：`torch.ops.aten.lt.Scalar_out`、`torch.ops.aten.lt.Tensor_out`、`torch.ops.aten.lt.int`、`torch.ops.aten.lt.float`、`torch.ops.aten.lt.int_float`、`torch.ops.aten.lt.float_int`、`torch.ops.aten.lt.default`、`torch.ops.aten.lt.str` |
| less | `torch.ops.aten.less.Tensor` | NotImplementedError：`torch.ops.aten.less.Scalar`、`torch.ops.aten.less.Scalar_out`、`torch.ops.aten.less.Tensor_out` |
| bitwise_and | `torch.ops.aten.bitwise_and.Tensor` | RuntimeError：`torch.ops.aten.bitwise_and.Scalar`、`torch.ops.aten.bitwise_and.Scalar_Tensor`、`torch.ops.aten.bitwise_and.Tensor_out`、`torch.ops.aten.bitwise_and.Scalar_out`、`torch.ops.aten.bitwise_and.Scalar_Tensor_out` |
| bitwise_or | `torch.ops.aten.bitwise_or.Tensor` | NotImplementedError：`torch.ops.aten.bitwise_or.Scalar_Tensor`、`torch.ops.aten.bitwise_or.Scalar`、`torch.ops.aten.bitwise_or.Tensor_out`、`torch.ops.aten.bitwise_or.Scalar_out`、`torch.ops.aten.bitwise_or.Scalar_Tensor_out` |
| bitwise_not | `torch.ops.aten.bitwise_not.default` | RuntimeError：`torch.ops.aten.bitwise_not.out` |
| logical_and | `torch.ops.aten.logical_and.default` | NotImplementedError：`torch.ops.aten.logical_and.out` |
| logical_or | `torch.ops.aten.logical_or.default` | NotImplementedError：`torch.ops.aten.logical_or.out` |
| logical_not | `torch.ops.aten.logical_not.default` | NotImplementedError：`torch.ops.aten.logical_not.out` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/eq.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/eq.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ne.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ne.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ge.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ge.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gt.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gt.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/le.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/le.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/lt.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/lt.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/less.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/less.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_and.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_and.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_or.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_or.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_not.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_not.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_and.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_and.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_or.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_or.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_not.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logical_not.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
