---
type: Guide
title: GE切片与写回：动态边界和形状恢复
description: 归并8组切片与写回转换，区分Concat/Scatter分支、INT32终点、负轴、Empty梯度基底及ViewCopy布局。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/select.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/select.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/select_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/select_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/select_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/select_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/slice.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/slice.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/flip.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/flip.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T08:14:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE切片与写回：动态边界和形状恢复

## 版本与证据强度

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013，本卡归并8组Select、切片写回与形状恢复Converter。主线全部非空源码及发布完整AST/注释差异均已核对；两版差异为named overload兼容声明和等价range/list写法，不把它们记成计算算法升级。

这里限定静态构图合同，平台矩阵未知，保持draft与空平台；未执行上游、GE编译、NPU精度/别名/确定性或性能实验。declare_supported只表示候选声明，源码警告和TODO不构成本次复现。需要区分准确overload、前反向、图中原地节点和外围函数化，不能只凭有注册就认证所有dtype、动态边界、重复索引及存储语义。

## Select与反向的基底

select.int直接GatherV2(self,index,[dim],negative_index_support=True)。来源有view输出case未修复TODO，不把列出的正/负索引候选当作本次运行通过或所有视图别名已保持。

select_scatter.default取Shape(self)，把index广播到整个输入shape，将src在dim处ExpandDims后也广播，再ScatterElements(self,index_,src_,axis=dim)。本层没有为所有负索引、重复写入和输出独立存储补完整检查，不能由函数式Schema独立认证设备更新别名。

select_backward.default把input_sizes转torch.int对应类型，以**Empty而非显式零值Fill**创建grad_input，再将index和展开后的grad_output广播至原输入shape并ScatterElements。此函数没有显式把未选中位置初始化为0，不能只按反向名字认定零梯度已保证；需要结合Empty/Scatter的实际合同和结果核对，本次未执行。

## Slice前向的快捷判定和INT32边界

slice.Tensor在处理边界之前，若输入和Meta都有_symsize且字符串相等，就直接返回self；这不是完整符号等式、step或别名校验。其余路径start=None补0，end=None补2147483647；非Tensor end为9223372036854775807时也改为2147483647，其他大于INT32_MAX的值直接RuntimeError。随后dim/start/end/step都转INT64，再StridedSliceV2。

因此“形参最终是INT64”不等于此路径支持任意64位尺寸/边界；GE Tensor end也没有经过同一Python上界检查。源码转置/切片消除注释只是优化意图，不能据shape字符串相同认证任意请求可跳过。

## slice_backward的三条路径

| 条件 | 本层恢复方式 |
| --- | --- |
| start/end/step都非GE Tensor且为0/sys.maxsize/1 | check_if_skip直接返回grad_output，未在此辅助里比较input_sizes与实际梯度shape。 |
| step为Python int且等于1 | start/end为int且input_sizes为list时走static_concat，否则dynamic_concat：分别在梯度前后填零，再ConcatV2。静态用Python边界计算，动态以Gather/SelectV2/FloorMod/Minimum表达。 |
| 其他步长/形参形式 | 用零Fill创建原shape基底，Range生成索引，按非目标轴Unsqueeze/Expand至grad_output形状，再ScatterElements。input_sizes、start/end/step在这里统一转INT32；Tensor input_sizes或原end时还用Minimum限制终点。 |

Concat路径不是一般Scatter路径的简单同义替换。静态start/end以长度取模处理负边界，动态也用FloorMod；没有独立覆盖全部极端负数、零长度和越界关系。不能把“支持负边界”泛化成所有切片规范已验证。

通用Scatter路径用range(grad_output.rank)再remove(dim)构造扩维轴，却没有在本函数先统一把负dim转正；负轴需要单独核对，不能因其他分支可用Python负下标就认为通用路径也相同。源码声明的step=2样例只是候选，不证明任意步长/动态组合正确。

## slice_scatter的静态拼接与动态索引

默认start补0、end补sys.maxsize。start/end/step都不是GE Tensor且step==1时，先进入static_slice_scatter_step1；全范围条件在这个辅助里直接返回src，所以不能把后面另一个Identity(src)分支当成唯一实际全范围行为。

静态辅助把dim%rank，取self.symsize[dim]为limit，负start/end用该长度取模，正值上限压到INT32_MAX，再取self前段、src和self后段ConcatV2。除了sys.maxsize哨兵，非Tensor end超过INT32_MAX会拒绝。**参数是Python常量不代表self形状已静态**，该分支仍访问symsize并在Python比较/取模；不能从分支名推导任意动态维度都安全。

其余路径取Shape(self)，必要时用目标轴长度替换sys.maxsize end，将shape/start/end/step转INT32；终点取Minimum，Range索引经Unsqueeze/Expand后ScatterElements。这里也有非负range列表remove(dim)的负轴边界，不能共享静态分支的dim%rank处理。

## AsStrided写回与Flip

as_strided_scatter.default将缺省storage_offset补0，self/src都按Meta输出dtype处理，然后构造ViewCopy。静态size List按size推导一份连续的src_stride，不是读取src实际stride；Tensor size分支使用size.rank当src_dim，而非读取shape向量长度，再构造stride。多维动态size、非连续src、存储跨度和重叠需按真实输入检查，不能由静态List候选推广全部布局。

最终ViewCopy分别接收目标size/stride/offset及src的size/所构造stride/0；不能只看函数名等同任意as_strided视图就地更新。flip.default则直接ReverseV2(self,dims)，不在本层认证所有dims与布局条件；两者的out入口都直接拒绝。

## 优化与验收

分别记录Python标量或GE Tensor边界、dim符号、input_sizes/Meta、step以及实际Empty/Fill/Concat/Range/Scatter/ViewCopy组合。覆盖零长度、极端负边界、INT32_MAX与sys.maxsize、负轴、静态参数加动态shape、未选中梯度、非连续写回及后续mutation。先核对数值、shape和别名，再比较Concat与Scatter的实际性能；本次没有执行这些实验。

高级索引和累加另见[GE索引与Scatter](torchair_ge_index_scatter_lowering.md)，符号shape和复制边界见[GE视图与复制](torchair_ge_view_copy_lowering.md)。

## 准确overload与直接拒绝清单

主线†表示getattr(...,None)兼容声明，目标缺失不形成有效Converter；发布版相应named目标用直接属性访问。表中有构图分支仍受正文条件限制，直接拒绝不扩展到高层函数、其他overload或其他后端。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| select | `torch.ops.aten.select.int` | RuntimeError：`torch.ops.aten.select.Dimname`† |
| select_backward | `torch.ops.aten.select_backward.default` | RuntimeError：`torch.ops.aten.select_backward.out` |
| select_scatter | `torch.ops.aten.select_scatter.default` | RuntimeError：`torch.ops.aten.select_scatter.out` |
| slice | `torch.ops.aten.slice.Tensor` | RuntimeError：`torch.ops.aten.slice.str` |
| slice_backward | `torch.ops.aten.slice_backward.default` | RuntimeError：`torch.ops.aten.slice_backward.out` |
| slice_scatter | `torch.ops.aten.slice_scatter.default` | RuntimeError：`torch.ops.aten.slice_scatter.out` |
| as_strided_scatter | `torch.ops.aten.as_strided_scatter.default` | RuntimeError：`torch.ops.aten.as_strided_scatter.out` |
| flip | `torch.ops.aten.flip.default` | NotImplementedError：`torch.ops.aten.flip.out` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/select.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/select.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/select_backward.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/select_backward.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/select_scatter.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/select_scatter.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/slice.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/slice.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_backward.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_backward.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_scatter.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/slice_scatter.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided_scatter.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided_scatter.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/flip.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/flip.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
