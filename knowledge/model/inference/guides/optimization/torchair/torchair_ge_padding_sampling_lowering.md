---
type: Guide
title: GE填充与采样：列表改写、尺寸与梯度精度
description: 区分常量反射复制padding、Nearest尺寸转换和GridSampler模式及精度回转，记录未消费的scale与梯度mask。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/constant_pad_nd.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/constant_pad_nd.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_3d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_3d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/adjust_implicit_decomposition.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/adjust_implicit_decomposition.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/adjust_implicit_decomposition.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/adjust_implicit_decomposition.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py
  role: implementation
created_at: '2026-11-10T08:56:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE填充与采样：列表改写、尺寸与梯度精度

## 固定版本与证据范围

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。主线对应文件全部非空源码及发布完整AST/注释差异已核对。本卡只说明Converter静态构图；平台矩阵未知，保持draft与空平台。未执行上游、GE编译、NPU精度/反向或性能实验，Support示例不充当实测矩阵。

## 常量、反射与复制Padding的形状和列表语义

本组十对文件AST相同，差异仅pylint注释。不要把不同padding模式的参数处理和动态边界合成一条规则。

| 准确default入口 | 构图与限制 |
| --- | --- |
| constant_pad_nd | pad为GE Tensor时NotImplementedError；要求偶数长度且不超过2*rank；先将末尾轴顺序的Torch列表补0至2*rank，再按轴对逆序，PadV3(self,pads,value)。value直接透传，没有按Meta统一Cast；负padding虽有声明样例，本次未验证任意裁剪范围。 |
| reflection_pad2d | padding为Tensor拒绝，长度必须4；rank3先补batch维，补齐padding并逆转轴对、Reshape成[rank,2]，MirrorPad(mode=REFLECT)，最后恢复rank3。其他rank直接沿该路径，并没有完整rank/反射窗口本地校验。 |
| reflection_pad2d_backward | rank3只对grad_output补维；对传入padding列表原地extend补0、reverse后每对再交换，PadV3Grad(mode=reflect,paddings_contiguous=True)，再按需Squeeze。没有前向同样的Tensor显式拒绝和len==4检查，不能据此认为Tensor已支持；本层依赖可变Python列表方法，复用同一列表需注意它已经被改写。 |
| replication_pad1d | padding为Tensor拒绝，长度只要求至少2；只取前两项形成[0,0,0,0,0,0,left,right]，self无条件补轴0，再PadV3(mode=edge)并Squeeze。Schema注释写SymInt[4]不能覆盖实际只取两项的逻辑，也不能据此认证任意rank。 |
| replication_pad1d_backward | 同样拒绝Tensor/长度<2；先构造grad_output补维，但sum(padding)==0时直接Identity(原grad_output)，否则取前两项走PadV3Grad(edge)再Squeeze。**总和为0不等于每项为0**，相反符号padding及额外元素会影响这个分支判断，不应概括为“仅无padding快捷返回”。 |

反射反向的self主要用于rank；复制反向self形参没有参与GE数据节点。需要结合真实原shape/参数核对梯度，不能从形参存在推导所有shape恢复已验证。

## Nearest插值主要依赖尺寸，scale形参未被消费

upsample_nearest2d.default把output_size提升为INT32，ResizeNearestNeighborV2指定align_corners=False、half_pixel_centers=False并标NCHW。scales_h/scales_w在该函数未参与计算或属性；vec准确重载仍直接NotImplementedError。需要确认上游已经把期望的scale语义体现在output_size，不能仅因接收参数就认证所有scale组合。

upsample_nearest2d_backward.default明确拒绝GE Tensor形式input_size；grad_output先转FP32，再以Python input_size[2]/[3]构造INT32 Const目标空间大小，ResizeNearestNeighborV2Grad后按Meta dtype回转。output_size、scales_h/scales_w形参未被使用，N/C不作为目标空间属性；这不是普遍运行期Tensor尺寸路径，也不能从前向的Tensor output_size处理推导反向同样支持。

## GridSampler的模式翻译与精度回转

2D前向和反向校验interpolation_mode在0..2，按列表映射bilinear/nearest/bicubic；3D前向只允许0..1，对应bilinear/nearest。padding_mode都为0..2，映射zeros/border/reflection，align_corners透传；局部列表取值与GE参数构造不独立认证所有组合kernel已可用。

前向对input/grid分别检查desc.dtype：FP16才转FP32，其他dtype保持，调用GridSampler2D/3D；当result.desc.dtype与原input.desc.dtype不同时，转回input.dtype。它不是对所有输入按Meta统一提升或输出按grid.dtype回转。

grid_sampler_2d_backward.default分别将FP16 grad_output/input/grid转FP32，调用GridSampler2DGrad。**output_mask未参与分支或节点属性，两项结果始终返回**。只有dx.dtype不同于input.dtype时，才把dx和dgrid一起转为input.dtype；没有独立按grid.dtype处理dgrid，也没有在dx无需Cast时单独修正dgrid。不同input/grid精度应据此设计核对用例，不能以mask签名或前向入图证明梯度裁剪、返回精度或确定性已验证。

## 验证与关联

逐项检查FX重载、pad顺序和列表复用、负padding、真实rank、尺寸来源、scale是否已经折入output_size、模式枚举以及两个梯度的dtype/shape；核对Eager和最终GE图后再测性能。来源没有提供本次实验结果，平台仍待核验。普通布局标注不执行Transpose，详见[归一化的布局属性解释](torchair_ge_batch_norm_lowering.md)。

- [Converter开发与动态符号](torchair_converter_implementation.md)
- [ATen文档层参数约束](torchair_aten_constraint_review.md)

## 准确重载清单

以下有构图分支仍受前文条件限制；拒绝只针对准确入口，不扩展为高层函数或其他后端的能力结论。

| 主题 | 有构图分支的准确入口 | 直接拒绝入口及异常 |
| --- | --- | --- |
| constant_pad_nd | `torch.ops.aten.constant_pad_nd.default` | `torch.ops.aten.constant_pad_nd.out` (NotImplementedError) |
| reflection_pad2d | `torch.ops.aten.reflection_pad2d.default` | `torch.ops.aten.reflection_pad2d.out` (NotImplementedError) |
| reflection_pad2d_backward | `torch.ops.aten.reflection_pad2d_backward.default` | `torch.ops.aten.reflection_pad2d_backward.grad_input` (RuntimeError) |
| replication_pad1d | `torch.ops.aten.replication_pad1d.default` | `torch.ops.aten.replication_pad1d.out` (AssertionError) |
| replication_pad1d_backward | `torch.ops.aten.replication_pad1d_backward.default` | `torch.ops.aten.replication_pad1d_backward.grad_input` (AssertionError) |
| upsample_nearest2d | `torch.ops.aten.upsample_nearest2d.default` | `torch.ops.aten.upsample_nearest2d.vec` (NotImplementedError)、`torch.ops.aten.upsample_nearest2d.out` (NotImplementedError) |
| upsample_nearest2d_backward | `torch.ops.aten.upsample_nearest2d_backward.default` | `torch.ops.aten.upsample_nearest2d_backward.grad_input` (NotImplementedError) |
| grid_sampler_2d | `torch.ops.aten.grid_sampler_2d.default` | `torch.ops.aten.grid_sampler_2d.out` (RuntimeError) |
| grid_sampler_2d_backward | `torch.ops.aten.grid_sampler_2d_backward.default` | `torch.ops.aten.grid_sampler_2d_backward.out` (RuntimeError) |
| grid_sampler_3d | `torch.ops.aten.grid_sampler_3d.default` | `torch.ops.aten.grid_sampler_3d.out` (RuntimeError) |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/constant_pad_nd.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/constant_pad_nd.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d_backward.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/reflection_pad2d_backward.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d_backward.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/replication_pad1d_backward.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d_backward.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/upsample_nearest2d_backward.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d_backward.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_2d_backward.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_3d.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/grid_sampler_3d.py)（implementation）
## 隐式分解改写让vec重载回到default转换器

TorchAir在`add_npu_patch`（`_utils/__init__.py`主线456，`run_once`包装）内先无条件调用`adjust_implicit_decomposition()`，再进入`npu_fx_pass`等后续分支。该函数改写进程共享的torch分解表：

- `disable_aten_ops=[aten.upsample_nearest2d.default]`：把该重载的`Autograd`与`CompositeImplicitAutograd`两个py kernel从dispatch键弹出，禁用torch对它的隐式分解。
- `replace_aten_ops={aten.upsample_nearest2d.vec: new_upsample_nearest2d_vec}`：把`.vec`重载的同名kernel替换为先用`upsample_compute_output_size`/`get_scale_value`重算osize与scale_h/scale_w、再调用`aten.upsample_nearest2d.default`的包装。

效果是Dynamo捕获到`.vec`重载时不再走torch隐式分解，而是回落到`.default`并命中上文`ResizeNearestNeighborV2`转换器；本卡前文「vec准确重载仍直接NotImplementedError」指的是GE转换器自身不实现vec，经此改写后vec调用已先被改道到default。独立npugraph_ex包的`_utils/adjust_implicit_decomposition.py`两pin与集成侧逐字节相同（`diff`零输出），同样经独立包`add_npu_patch`调用。

边界：这是进程级全局改写，导入并启用TorchAir后Eager路径的`upsample_nearest2d.vec`同样被改道；本节只证明静态改写存在，不证明所有输入组合下改道后的数值或性能等价。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/adjust_implicit_decomposition.py)（implementation）：1–39完整读取。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/adjust_implicit_decomposition.py)（implementation）：1–43完整读取；与主线仅排版差异。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/adjust_implicit_decomposition.py)（implementation）：与集成主线`diff`零输出。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/adjust_implicit_decomposition.py)（implementation）：与集成发布`diff`零输出。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py)（implementation）：调用点窗口449–461（`add_npu_patch`内`adjust_implicit_decomposition()`位于456，先于457起的`npu_fx_pass`分支）。
