---
type: Guide
title: 推理Dequant-SwiGLU：Meta类型与FP4承载形状差异
description: 核对独立npu_inference入口的激活轴、量化枚举及FP4 Meta形状与GE重打包，避免套用公共npu接口。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/auto_register_custom_torch_ops.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_dequant_swiglu_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/auto_register_custom_torch_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_dequant_swiglu_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T13:28:56Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 推理Dequant-SwiGLU：Meta类型与FP4承载形状差异

## 图入口和两版范围

本卡针对`torch.ops.npu_inference.npu_dequant_swiglu_quant.default`，由TorchAir自定义包的Schema、Meta及GE装饰器定义；不能与`torch.ops.npu.npu_dequant_swiglu_quant.default`按同名互换。固定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`和发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的这两个选定函数AST相同；不是整个库、所有分类或kernel相同。

包初始化枚举并导入模块，本卡只审显式启用该包后的入口，未闭合普通`import torchair`自动加载链。所审层只有Schema/Meta/Converter不能证明Eager设备执行或产品范围；平台未知，保持draft、空平台。没有执行上游、图编译、反序列化或设备验证。

## Meta只按激活轴减半

默认dst_type=1、round_mode=0、activate_dim=-1；负轴加x.dim()转为select_dim。此Meta显式要求rank>1、轴在范围内、选中轴长度为偶数，quant_mode只能0或1。报错写last dim，但实际偶数检查针对select_dim，不总是尾轴。

随后y_size只把选中激活轴减半，scale_size取这个y_size去掉最后一轴，scale为FP32。dtype选择是局部分支：23为E5M2、24为E4M3FN、296/297为UINT8，其余均INT8；不是通用dtype映射。函数不完整检查输入dtype、分组count内容、scale/bias、clamp有效值或所有静态/动态组合；Meta能分配不证明这些组合有效，动态符号形状也没有在本卡运行验证。

## FP4承载形状与GE重打包分开

当dst_type为296/297，Meta虽选UINT8，却**没有再把物理尾轴减半**。GE Converter在DequantSwigluQuant之后，反而按`Shape(y)/[1,...,1,2]`请求尾轴一半的uint8 shape，再追加2做Reshape、Bitcast为UINT8、最后Reshape到该承载shape。

例如，若节点量化后逻辑shape为(M,H)，所审Meta请求UINT8(M,H)，图上的后处理则请求UINT8(M,H/2)；这里描述静态构图差异，不是已经编译/执行得到的数值或错误复现。选中轴不是尾轴时，激活轴减半与FP4承载尾轴减半仍是两件事。局部Meta只要求激活轴偶数，没有另外检查量化后尾轴还能按两值打包；不能据Meta通过保证合法FP4尺寸。

同名公共npu入口的OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda` Meta会在FP4分支进一步减半y_size[-1]，所以不能把公共API的FakeTensor合同直接套给这个独立命名空间。其产品支持、count分组和ACLNN版本选择继续查[公共接口](../../../apis/torch_npu/npu_dequant_swiglu_quant.md)，本卡不复制或扩大这些矩阵。

## 扩展类型和舍入也要核对消费者

Converter通过通用整数类型映射取得GE dst_type并设置y描述符；例如整数290映射HiFloat8，291/292映射两种FP8。自定义Meta未为这些整数写同样分支，仍落INT8；不能因为公共包使用相同类型常量就认为图和Meta描述一致。

quant_mode在Converter仅当1选dynamic，其余选static；Meta却会拒绝0/1之外的值。round_mode=0或未列值均落rint，1/2/3/4分别round/floor/ceil/trunc；Meta本地并不校验舍入枚举。swiglu_mode/clamp_limit/glu_alpha/glu_bias及可选scale、bias、group_index原样下传，没有在Converter完成全部合法性检查。仅修改某一整数或字符串，不证明对应kernel和输入组合可用。

集成时先核准命名空间、实际dst_type整数和激活轴，再比对Meta、逻辑输出、UINT8承载shape、scale shape与返回消费。FP4路径额外出现的Reshape/Bitcast节点不独立证明复制成本、零拷贝或最终布局；需要结合编译结果与真实存储验证。未新增verified、泄漏结论或性能数据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/auto_register_custom_torch_ops.py)（primary）：定向范围1–7, 29–35, 165–218。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_dequant_swiglu_quant.py)（implementation）：定向范围46–119。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/auto_register_custom_torch_ops.py)（implementation）：定向范围6–6, 20–24, 115–151。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_dequant_swiglu_quant.py)（implementation）：定向范围18–77。
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/__init__.py)（implementation）：定向范围1–7。
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）：定向范围205–262。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：定向范围5936–5966。
