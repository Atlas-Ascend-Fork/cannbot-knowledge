---
type: Guide
title: GE复数与FFT：重建精度、轴和归一化
description: 记录复数view重建、FFT轴和归一化路径及未消费的forward形参，避免把注册入口当作完整精度或别名保证。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_fft_c2c.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_fft_c2c.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_complex.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_complex.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_real.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_real.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T09:13:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE复数与FFT：重建精度、轴和归一化

## 固定版本与证据边界

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。主线完整非空源码、发布完整AST/注释差异均已阅读；本卡平台矩阵未知，保持draft与空平台，未执行上游、GE编译、NPU精度/反向或性能实验。Support只是候选声明，静态构图不替代kernel、ABI和高层函数验证。

## 复数view在这里是重建图

view_as_complex.default先将self提升为FP32，再沿最后一轴分别Gather第0/1项，调用Complex(real,imag)。本层未显式验证最后轴长度恰为2、原dtype或stride，也未按Meta输出dtype选择更高精度；不能凭Schema中的Tensor(a)认证零拷贝、存储共享或所有FP64输入都保留复数双精度。

view_as_real.default调用Real/Imag并沿最后轴Pack(N=2)，没有物理视图构造或统一Meta Cast。其C64候选声明不证明所有复数类型与别名合同；需结合外围函数化和后续mutation核对实际行为。

## FFT轴的本地限制

_fft_c2c.default明确拒绝GE Tensor形式dim；每一轴必须0<=d<rank，**负轴没有本地规范化**。仅len(dim)==1或2有实现，空列表也进入else拒绝；报错写len(dim)>2不能掩盖空列表实际控制流。没有独立重复轴校验。

一维把目标轴与最后轴交换；二维把非目标轴排前、目标轴排后，构造排序及逆置换。辅助函数先把Complex输入拆Real/Imag并Pack末尾二分量，Permute后又SplitV、Squeeze并**转FP32**再Complex；FFT/FFT2D后还走类似重建与恢复置换。不能把这些节点当零成本view或全精度复数变换，置换与新增分量轴的IR合同也需核对。

## 方向形参与归一化

forward形参在该Converter及调用的FFT辅助函数中没有被消费，始终使用FFT或FFT2D；本层没有根据forward选择逆变换或共轭路径。不能由一个bool签名认证正逆变换都正确，也不能超范围推断其他后端没有逆变换。

归一化辅助函数按变换后self的最后signal个轴，用Shape/Gather和Mul计算元素数，Cast成COMPLEX64。normalization==1时除以该数量的Sqrt，==2时直接除，其他值原样返回，没有完整枚举值检查。维度乘积的中间类型、极大shape、数值精度和特殊值均未由该静态计算认证。

两快照_fft_c2c差异只在range列表写法，两个view文件AST相同；不能把等价源码或固定提交当成实验通过。优化前检查准确轴、顺序、dtype、forward/normalization、输入stride、重建节点及后续别名，再比对数值后测性能。

- [GE视图与复制合同](torchair_ge_view_copy_lowering.md)
- [文档层复数与FFT能力边界](torchair_aten_constraint_review.md)

## 准确入口与拒绝重载

可构图入口仍受正文条件限制；拒绝仅指准确映射，不扩高层函数或其他后端。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| _fft_c2c | `torch.ops.aten._fft_c2c.default` | `torch.ops.aten._fft_c2c.out` (RuntimeError) |
| view_as_complex | `torch.ops.aten.view_as_complex.default` | 无无条件拒绝壳；仍有正文参数边界 |
| view_as_real | `torch.ops.aten.view_as_real.default` | 无无条件拒绝壳；仍有正文参数边界 |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_fft_c2c.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_fft_c2c.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_complex.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_complex.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_real.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/view_as_real.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
