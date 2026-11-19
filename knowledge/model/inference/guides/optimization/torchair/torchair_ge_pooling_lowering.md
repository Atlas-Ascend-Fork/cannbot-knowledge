---
type: Guide
title: GE池化：除数、索引占位与版本分支
description: 核对Adaptive与AvgPool前反向动态和除数差异、MaxPool索引占位及反向重算，并区分主线V3和发布V1分支。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool3d_with_indices.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool3d_with_indices.py
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
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-10T08:56:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE池化：除数、索引占位与版本分支

## 固定版本与证据范围

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。主线对应文件全部非空源码及发布完整AST/注释差异已核对。本卡只说明Converter静态构图；平台矩阵未知，保持draft与空平台。未执行上游、GE编译、NPU精度/反向或性能实验，Support示例不充当实测矩阵。

## AdaptiveAvgPool前反向的动态边界不同

torch.ops.aten._adaptive_avg_pool2d.default明确拒绝GE Tensor形式的output_size，列表直接传AdaptiveAvgPool2d的output_size属性；out重载直接RuntimeError。

_adaptive_avg_pool2d_backward.default主线直接以self.symsize传AdaptiveAvgPool2dGrad的orig_input_shape；发布版则要求symsize存在且每项不为torch.SymInt，否则NotImplementedError。**主线移除本地动态拒绝，不等于已验证符号/缺失shape可被该IR或kernel正确消费**，也没有改成运行时Shape(self)的GE路径。前向与反向不能共用一条动态支持判断。

## AvgPool2d的除数规则与前反向差异

avg_pool2d.default校验kernel_size长度1/2、stride长度0/1/2、padding长度1/2、输入rank3/4；divisor_override必须None或1..255。源码的“non-empty”报错对应的本地条件仅检查rank，不能由文字推导完整空维度检查。rank3先Unsqueeze轴0再在结果Squeeze。

单元素参数复制为空间两轴；stride省略时各轴取kernel大小，单stride复制两轴，padding展开成[H,H,W,W]；ksize/strides扩成[1,1,H,W]。divisor_override=None转GE属性0，非None使用其值。AvgPoolV2传ceil_mode；**输入FP16或INT8时exclusive固定True，count_include_pad不再决定该属性；其他dtype为not count_include_pad**。这是该映射的分支，不足以认证所有padding值下与Eager等价，应按真实dtype/边缘窗口核对数值。

avg_pool2d_backward.default同样展开参数，但没有复制前向的长度、rank和divisor_override范围检查，也没有rank3补维逻辑；以Shape(self)和grad_output调用AvgPoolV2Grad，data_format=NCHW、padding_mode=CALCULATED、global_pooling=False。exclusive始终按not count_include_pad，与前向FP16/INT8分支不同；divisor_override按Python真值决定保留还是0。输出直接写input_desc[1]/output_desc[0].layout=NCHW，不能等同实际数据转置。发布版的False if count_include_pad else True与主线布尔写法同义，不记为算法变化。

文档[ATen清单](torchair_aten_constraint_review.md)另列AvgPool2d的dynamic=False、kernel_size<=255、stride<=63；不能因Python本地没有重复所有检查就抹去文档条件。

## MaxPool2d的索引占位与反向重算

max_pool2d_with_indices.default校验kernel、stride、padding、dilation的列表长度，按省略/单值规则扩成H/W，但本层没有统一rank合法性检查。发布快照只有MaxPoolWithArgmaxV1路径；主线在is_arch35时增加V3路径：两元素ksize/strides/pads/dilation，传dtype=9与ceil_mode，直接返回output/argmax。

**V1路径丢弃GE原argmax，改为Identity(output)再转torch.int64作为第二返回值**。它不能作为一般意义的输入位置索引供用户消费。源码称为规避IR不兼容的临时办法，并称不设testcase，这是来源解释，不是本次测试结果；高层return_indices=True的正确性不能只凭这个注册入口认证。

max_pool2d_with_indices_backward.default在主线is_arch35时调用MaxPoolGradWithArgmaxV3，使用传入indices；其他主线分支和发布版均重新执行MaxPoolWithArgmaxV1取得真实argmax，再MaxPoolGradWithArgmaxV1，**函数形参indices在V1分支没有使用**。因此保存索引是否省掉重算、前向第二输出是否能外用和反向是否消费该输出，要按分支分别判断。V1使用[1,H,W,1]类属性和布局标注，不能与V3的二元素属性简单混换。

is_arch35在主线按设备名包含Ascend910_95、Ascend950或Ascend350选择；发布版辅助选择器只列前两种且池化文件没有该V3分支。950是Ascend950系列（包含旧称Atlas A5），字符串判断不替代产品能力表。

## MaxPool3d不能继承2D占位结论

max_pool3d_with_indices.default校验空间列表长度为1/3（stride还可为空），展开成三元素；rank4先补batch轴0，调用MaxPool3DWithArgmaxV2，原GE argmax转torch.int64，然后按需同时Squeeze输出和索引。它没有把索引替换为Identity(output)，不能将2D V1的占位规则扩到3D。

主线与发布版3D计算分支相同，AST差异为说明文字由字符串变注释；本卡只审阅这个前向文件，不以相邻反向文件或缺少某个注册作超范围结论。所有out/grad_input拒绝见下表，报错中的未来支持措辞不是版本承诺。

## 优化验收

先检查FX准确重载、dtype、ceil_mode、边缘窗口除数、输出shape及indices后续用途；分别验证Adaptive反向动态条件、AvgPool前反向除数、MaxPool V1重算与V3索引ABI，再检查最终图和性能。specific_op_input_layout/output_layout只是节点属性追加，不能认证物理布局已转换。本次没有执行这些实验。

## 准确重载清单

以下有构图分支仍受前文条件限制；拒绝只针对准确入口，不扩展为高层函数或其他后端的能力结论。

| 主题 | 有构图分支的准确入口 | 直接拒绝入口及异常 |
| --- | --- | --- |
| _adaptive_avg_pool2d | `torch.ops.aten._adaptive_avg_pool2d.default` | `torch.ops.aten._adaptive_avg_pool2d.out` (RuntimeError) |
| _adaptive_avg_pool2d_backward | `torch.ops.aten._adaptive_avg_pool2d_backward.default` | `torch.ops.aten._adaptive_avg_pool2d_backward.out` (RuntimeError) |
| avg_pool2d | `torch.ops.aten.avg_pool2d.default` | `torch.ops.aten.avg_pool2d.out` (NotImplementedError) |
| avg_pool2d_backward | `torch.ops.aten.avg_pool2d_backward.default` | `torch.ops.aten.avg_pool2d_backward.grad_input` (AssertionError) |
| max_pool2d_with_indices | `torch.ops.aten.max_pool2d_with_indices.default` | `torch.ops.aten.max_pool2d_with_indices.out` (NotImplementedError) |
| max_pool2d_with_indices_backward | `torch.ops.aten.max_pool2d_with_indices_backward.default` | `torch.ops.aten.max_pool2d_with_indices_backward.grad_input` (RuntimeError) |
| max_pool3d_with_indices | `torch.ops.aten.max_pool3d_with_indices.default` | `torch.ops.aten.max_pool3d_with_indices.out` (NotImplementedError) |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d_backward.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_adaptive_avg_pool2d_backward.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d_backward.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/avg_pool2d_backward.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices_backward.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool2d_with_indices_backward.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool3d_with_indices.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max_pool3d_with_indices.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）
