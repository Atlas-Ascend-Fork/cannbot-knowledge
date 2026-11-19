---
type: Guide
title: GE ATen 入图约束：精度、形状与前反向分别核对
description: 从 ATen 清单提炼影响混合精度、池化、索引和优化器的参数限制，说明入图清单不能代替具体 overload 验证。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/aten_api.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/aten_api.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py
  role: implementation
created_at: '2026-11-09T04:39:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# GE ATen 入图约束：精度、形状与前反向分别核对

## 版本与证据含义

依据 TorchAir `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的 ATen 入图清单，选择 A2/A3 的 GE 路线；清单声称所列能力对等对应 Eager 能力，仍不能外推为 npugraph_ex 捕获安全性或所有 dtype/overload 均可用。未列出的接口可能能力不完备，应检查准确 FX 节点和 Converter，不能仅凭缺表认定绝对不支持。

## 优化时容易遗漏的约束

|类别|固定清单的限制与评估方法|
|--|--|
|BatchNorm|BatchNorm1d/2d/3d 列 FP16/FP32 且 track_running_stats=True；内部 `_native_batch_norm_legit` 列 track_running_stats=False。高层模块和内部算子不能混用参数规则。|
|精度与前反向|`_softmax` 及其 backward、select、as_strided、new_empty 清单仅列 FP32；new_full 列 INT64。addmm 和 Conv1d/2d、ConvTranspose1d/2d 列 FP16/FP32，不能从其他算子支持 BF16 推导它们也在该清单中支持。|
|池化|MaxPool2d 前向列 FP16/FP32、return_indice=False、dynamic=True；反向列 FP16/FP32/BF16 且输入四维。avg_pool2d 前向要求 dynamic=False、kernel_size≤255、stride≤63，前反向列 FP16/FP32。AdaptiveAvgPool2d 的 output_size 仅列 list。不同池化不能共享同一动态形状假设。|
|激活|hardswish 前向 FP16/FP32，反向另列 BF16 且 inplace=False；hardtanh 的 min_val/max_val 为浮点时输入可为 BF16/FP16/FP32/FP64，为整型时输入列 INT32/INT64，反向列 BF16/FP16/FP32。GLU 要求 dim 合法、相应轴长度为偶数，前反向列 FP16/FP32。|
|索引与边界|where 输入少于八维，并且不支持动态的单参数 where(condition) 返回索引元组路径；scatter_add 的 index 必须非空。clamp 清单要求 min<max。as_strided_scatter 的 src.stride 与 stride 参数存在额外大小关系，具体维度对应须回到准确实现核对，不把简短表述扩展为任意 stride 均可用。|
|损失|MSE 前反向 FP16/FP32，input/target dtype 相同；NLL 前向 weight/input 同 dtype，列 BF16/FP16/FP32，target 列 UINT8/INT32/INT64。NLL 输入一维时 target 零维，输入二维时 target 一维且 batch 长度一致；不能只核对总元素个数。|
|复数|fft 与 fft2 主线列 complex64；view_as_real 列 complex64，view_as_complex 列 FP32/FP64，mean 另列 complex64/complex128。不能把复数支持从逐元素算子传播到所有算子。|
|Foreach 优化器路径|foreach_add/div/mul 对 BF16/FP16/FP32 Tensor 的 scalar 列 FP32，对 INT32 Tensor 的 scalar 列 INT64；foreach_addcdiv/addcmul 仅列 FP32/BF16。切换 foreach 路线要单独检查每种运算、标量与 Tensor 列表 dtype，不能由 add 的覆盖推导组合更新也覆盖 FP16。|

## 表述不完备时的处理

embedding 条目的 max_norm、scale_grad_by_freq、_freeze 说明混合了不同层次的参数；foreach_pow/sub 的 scalar 描述也未分离所有 overload。保留这些为核对线索，读取具体 Schema、Meta、Converter 与底层支持后再给出可运行参数，不从含混条目生成优化配方。new_empty_strided 的约束栏为横线，只代表该栏未说明，不等于任意输入无限制。

发布快照 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的 fft2 约束栏未给 dtype，主线才明确 complex64；文档增补不等于已证明两个软件版本运行行为改变。下方另列该固定清单全部名称和约束；其他dtype、overload或实际运行能力仍须核对实现。

## 验收

在 FX 图中确认名称、overload、前反向路径；覆盖真实 shape/dtype、动态标量、空输入及特殊参数。比较 Eager 和 GE 输出，再测性能。本文未执行 NPU 编译或精度测试。

- [Converter 的准确注册接口](../../../apis/torchair/register_fx_node_ge_converter.md)
- [按诊断阶段补齐入图能力](torchair_converter_implementation.md)

## 固定清单的全部151项入口与约束

以下按发布快照逐项保留名称及参数关系，共151项、69组约束（包含未填写组），其余只合并完全相同的约束；同名不同命名空间不合并，正向/反向条件不互相继承。它是这一页的文档能力表，仍不是所有产品、所有 overload 或实际运行已验证的矩阵。dtype名称沿用源表，不能把仅写dtype的条目扩为任意shape、stride和参数。

|准确入口（同一格仅合并完全相同的约束）|发布清单所列限制|
|--|--|
|`torch.nn.BatchNorm1d`、`torch.nn.BatchNorm2d`、`torch.nn.BatchNorm3d`|列出fp16，fp32。track_running_stats为True|
|`torch._native_batch_norm_legit_no_training`、`torch.addmm`、`torch.bernoulli`、`torch.nn.functional.hardsigmoid`、`torch.nn.Conv2d`、`torch.nn.Conv1d`、`torch.nn.ConvTranspose1d`、`torch.nn.ConvTranspose2d`、`torch.ops.aten.floor.default`、`torch.nn.functional.elu`|列出fp16，fp32|
|`torch._softmax`、`torch._softmax_backward_data`、`torch.select`、`torch.as_strided`、`torch.new_empty`|列出fp32|
|`torch.ops.aten._to_copy.default`、`torch.div`、`torch.sum`、`torch.detach`、`torch.le`、`torch.minimum`、`torch.ones_like`、`torch.triu`|列出bf16，fp16，fp32，uint8，int8，int16，int32，int64，bool|
|`torch.clone`、`torch.t`|列出bf16，fp16，fp32，uint8，int8，int16，int32，int64|
|`torch.empty_like`、`torch.abs`、`torch.empty`、`torch.sort`、`torch.searchsorted`|列出fp16，fp32，uint8，int8，int16，int32，int64|
|`torch.Tensor.expand`、`torch.nn.functional.pad`|列出bf16，fp16，fp32，int16，int32，int64|
|`torch.nn.functional.gelu`、`torch.nn.functional.leaky_relu`、`torch.native_layer_norm`、`torch.nn.functional.layer_norm`、`torch.ops.aten.slice.Tensor`、`torch.ops.aten.slice_backward.default`、`torch.nn.functional.group_norm`、`torch.nn.LogSoftmax`、`torch._foreach_abs`、`torch._foreach_acos`、`torch._foreach_asin`、`torch._foreach_atan`、`torch._foreach_ceil`、`torch._foreach_cos`、`torch._foreach_cosh`、`torch._foreach_erf`、`torch._foreach_erfc`、`torch._foreach_exp`、`torch._foreach_expm1`、`torch._foreach_log`、`torch._foreach_log10`、`torch._foreach_log1p`、`torch._foreach_log2`、`torch._foreach_sigmoid`、`torch._foreach_sin`、`torch._foreach_sinh`、`torch._foreach_tan`、`torch._foreach_tanh`、`torch._foreach_trunc`|列出bf16，fp16，fp32|
|`torch.nn.functional.hardswish`|正向：列出fp16，fp32；<br>反向：列出bf16，fp16，fp32，参数约束inplace=False|
|`torch.mean`|列出bf16，fp16，fp32，complex64，complex128|
|`torch.ops.aten.new_empty_strided.default`|该栏未说明；不表示无限制或所有 overload 均可用|
|`torch.permute`、`torch.fill`、`torch.mul`、`torch.sqrt`、`torch.zeros_like`、`torch.ne`|列出bf16，fp16，fp32，uint8，int8，int16，int32，int64，bool，complex64，complex128|
|`torch.nn.Threshold`|列出fp32，uint8，int8，int16，int32，int64|
|`torch.nn.MaxPool2d`|正向：列出fp16，fp32参数约束return_indice=False，dynamic=True<br>反向：列出fp16，fp32，bf16，input为四维|
|`torch.slice_scatter`、`torch.index_select`、`torch.ops.aten.alias.default`、`self.new_ones(...)`、`torch.unbind`|列出bf16，fp16，fp32，fp64，uint8，int8，int16，int32，int64，bool|
|`torch.nn.functional.avg_pool2d`|正向：列出fp16，fp32，参数约束dynamic=False，kernel/_size≤255，stride≤63<br>反向：列出fp16，fp32|
|`sigmoid`|列出fp16，fp32，int8，int32，int64|
|`torch.sigmoid`、`torch.nn.functional.sigmoid`|列出bf16，fp16，fp32，fp64|
|`torch._native_batch_norm_legit`|列出fp16，fp32参数约束track_running_stats=False|
|`torch.sub`、`torch.stack`、`torch.argmax`|列出bf16，fp16，fp32，fp64，uint8，int8，int16，int32，int64|
|`self.new_zeros(...)`|列出fp16，fp32，fp64，bf16，int8，int16，int32，int64，uint8，bool，complex64，complex128|
|`torch.clamp`|列出bf16，fp16，fp32，uint8，int8，int16，int32，int64参数约束min<max|
|`torch.nn.functional.embedding`|列出int32，int64参数约束max_norm=False，sparse=False，scale_grad_by_freq=False前向不支持，_freeze=False|
|`torch.nn.functional.hardtanh`|正向：min_val和max_val为浮点型，input列出bf16，fp16，fp32，fp64<br>min_val和max_val为整型时，input列出int32，int64<br>反向：列出bf16，fp16，fp32|
|`torch.constant_pad_nd`|列出bf16，fp16，fp32，int32，int64，bool参数约束inplace=False|
|`torch.nn.avgpool2d`|列出fp16，fp32参数约束dynamic=False，kernelsize≤255, stride≤63|
|`torch.nn.AdaptiveAvgPool2d`|列出fp16，fp32output_size仅列出list|
|`torch.fft.fft`、`torch.view_as_real`|列出complex64|
|`torch.arange`、`torch._foreach_round`|列出bf16，fp16，fp32，int32，int64|
|`torch.as_strided_scatter`|列出bf16，fp16，fp32，fp64，uint8，int8，int16，int32，int64，bool，complex64，complex128输入tensor src的stride属性要小于stride参数|
|`torch.bitwise_and`、`torch.bitwise_not`|列出uint8，int8，int16，int32，int64，bool|
|`torch.ceil`|列出fp32，fp16|
|`torch.cumsum`|列出bf16，fp16，fp32，int8，int16，int32，int64，bool|
|`torch.exp`、`torch.log`|列出bf16，fp16，fp32，int64，bool，complex64，complex128|
|`torch.nn.functional.grid_sample`|列出fp16，fp32，fp64|
|`torch.ops.aten.index.Tensor`|列出fp16，fp32，uint8，int8，int32，int64，bool|
|`torch.index_add`|列出fp16，fp32，int64，bool|
|`torch.linspace`|参数start和end为浮点类型参数steps为非负整数|
|`torch.logsumexp`、`torch.select_scatter`|列出fp16，fp32，uint8，int8，int16，int32，int64，bool|
|`torch.max`|列出bf16，fp16，fp32，int64，bool|
|`torch.nn.functional.mse_loss`|正向：列出fp16，fp32<br>反向：列出fp16，fp32<br>参数self和target的数据类型要一致|
|`torch.new_full`|列出int64|
|`torch.nn.functional.nll_loss`|正向：参数weight和input的数据类型必须相同，数据类型列出bf16，fp16，fp32<br>参数target的数据类型列出uint8，int32，int64<br>当参数self为1D-tensor时，target需要为0D-tensor；<br>当self为2D-tensor时，target需要为1D-tensor，两个参数的shape关系需满足：self.shape[0] = target.shape[0]<br>反向：列出bf16，fp16，fp32，int64|
|`torch.rand`、`torch.randint`、`torch.randn`|输入为生成tensor的shape|
|`torch.remainder`|列出fp16，fp32，int32，int64|
|`torch.scatter`|列出int16，int32，int64|
|`torch.scatter_add`|列出bf16，fp16，fp32，fp64，uint8，int8，int16，int32，int64，bool参数index必须为非空tensor|
|`torch.sgn`|列出bf16，fp16，fp32，int32|
|`torch.nn.functional.tanh`、`torch._foreach_lerp`、`torch._foreach_norm`|列出fp16，fp32，bf16|
|`torch.view_as_complex`|列出fp32，fp64|
|`torch.where`|列出fp16，fp32，fp64，uint8，int8，int16，int32，int64，bool输入tensor的shape小于8维不支持动态场景torch.where(condition) → tuple of LongTensor|
|`torch.zeros`|列出fp16，fp32，fp64，uint8，int8，int16，int32，int64|
|`torch.eq`|列出bf16，fp16，fp32，uint8，int8，int32，int64，bool|
|`torch.erf`|列出bf16，fp16，fp32，|
|`torch.full_like`|列出fp16，fp32，int32，uint8，int16，int64，bool，complex64，complex128|
|`torch.lt`|列出bf16，fp16，fp32，uint8，int8，int32，int64|
|`torch.nn.functional.glu`|正向：列出fp16，fp32<br>dim值在input维度范围内，且input.shape[dim]为偶数<br>反向：列出fp16，fp32|
|`torch.ge`|输入Tensor列出bool，uint8，int8，int16，int32，int64，fp16，bf16，fp32，fp64|
|`torch.ops.aten.sym_size.int`|输入Tensor列出bf16，fp32，fp16，int8，uint8，int16，int32，int64|
|`math.ceil`|列出bf16，fp32，fp16，fp64|
|`torch.logical_and`、`torch.sym_sum`|列出bf16，fp16，fp32，fp64，uint8，int8，int16，int32，int64，bool，complex64，complex128|
|`torch._foreach_add`|列出bf16，fp16，fp32，int32tensor是bf16，fp16，fp32时，scalar列出fp32tensor是int32，scalar列出int64|
|`torch._foreach_addcdiv`、`torch._foreach_addcmul`|列出fp32，bf16|
|`torch._foreach_div`、`torch._foreach_mul`|列出bf16，fp16，fp32，int32tensor是bf16，fp16，fp32，scalar列出fp32tensor是int32，scalar列出int64|
|`torch._foreach_floor`、`torch._foreach_frac`|列出bf16，fp16，fp32，int8，uint8，int32，int64|
|`torch._foreach_maximum`、`torch._foreach_minimum`|列出fp16，fp32，int32，bf16|
|`torch._foreach_pow`|列出bf16，fp16，fp32tensor_list输入dtype和scalar dtype相同tensor_list输入dtype为浮点数，scalar type为int|
|`torch._foreach_sub`|列出bf16，fp16，fp32，int32tensor_list输入dtype和scalar dtype相同tensor_list输入dtype为浮点数，scalar type为int|
|`torch.fft.fft2`|未填写约束；不能补成不支持或无限制|

主线表与此表的技术增量是 `torch.fft.fft2` 明确列出complex64；发布表该格未填写。`torch.fft.fft` 两版均列complex64。未带命名空间的 `sigmoid` 与 `torch.sigmoid`、`torch.nn.functional.sigmoid` 分开保留，不从名称相似推导同一类型集合。embedding条目混合参数层次、foreach部分标量表述及as_strided_scatter简述仍按前文的不完备边界核对。

这份关系表补齐页面内的逐项约束，不将“与Eager对等”的概述用于覆盖具体限制，也不改变npugraph_ex对RNG、反向捕获的独立约束。

## 未填写单元格与明确否定分别保留

源表的fft2行只有名称与分隔符，没有完整的约束单元格；其仍是第151项入口，按未填写处理，而new_empty_strided使用明确横线。完整表因此为151项、69组（含未填写组）。表中的embedding“前向不支持”和where动态单参数路径“不支持”仍是明确否定，不能改写成仅未列出。缺失、横线及明确否定不互作同义。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/aten_api.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/aten_api.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
## 附录清单与转换器注册表的反向核对

本节把附录页「所列API能力均对等Eager模式下能力、不在表1说明能力可能不完备」的承诺同两固定 pin 的转换器注册表做机械反向核对。方法：本地脚本统计 `python/torchair` 树内全部 `@register_fx_node_ge_converter(...)` 装饰器的字面目标（未 import 上游；92 组 dimname/names overload 主线以 `getattr(..., None)` 写法、发布以直接属性写法，归一后同目标）；清单 151 行按「高层入口 → 分解后 aten 目标」映射核对（约 30 组手写映射随批次 evidence 脚本留档可复算，如 F.layer_norm→native_layer_norm、nn.Conv1d/2d/ConvTranspose1d/2d→convolution、AdaptiveAvgPool2d→_adaptive_avg_pool2d、LogSoftmax→_log_softmax、F.pad→constant_pad_nd、grid_sample→grid_sampler_2d、MaxPool2d→max_pool2d_with_indices、BatchNorm1d/2d/3d→native_batch_norm/_native_batch_norm_legit）。

| 核对项 | 结果（静态读到） | 边界 |
| --- | --- | --- |
| 注册规模 | 装饰器出现主线 2112 处（其中 3 处是 fx2ge_converter.py:1045/1063/1081 的 codegen 模板字符串）、发布 2106 处（4 处模板 701/849/867/885）；实际注册点 2109/2102、不同目标 2108/2102；aten 目标两版各 1787 个且归一后集合完全一致，非 aten 目标 321/315 个（npu/npu_define/npu_inference/prims/quantized/mkldnn/higher_order/c10d_functional/rngprims/operator.*/math.ceil/torch.sym_sum） | 清单 151 行约为注册表规模的 7%：注册表远大于清单，「不在表1」不能反推未注册或不支持；反向地注册存在也不证明清单级能力（下行） |
| 逐行映射 | 两 pin 均 151/151 至少命中一个注册目标 | 清单是高层用户入口视角、注册表是分解后 overload 键控，不一一对应；`sigmoid`/`torch.sigmoid`/`torch.nn.functional.sigmoid` 三行共用 aten.sigmoid（sigmoid.py 主线 10/16、发布 10/16）、`torch.nn.functional.avg_pool2d` 与 `torch.nn.avgpool2d` 两行共用 aten.avg_pool2d——行间 dtype 差异不来自不同注册 |
| 注册即抛错的占位 | `aten.sigmoid.out` 的注册体直接 raise RuntimeError（ge_converter/aten/sigmoid.py 主线 16–21、发布 16–22，文案称 pytorch 2.1.0 前冗余） | 「注册存在」不等于可用；「对等Eager」仍须按前文逐项约束核对，不从注册推导 |
| 非 aten 字面键 | `math.ceil` 以 callable 直接注册、非 Tensor 输入回落原函数（builtin_converters.py 主线 103–107、发布 125–132）；`torch.sym_sum` 在 torch≥2.6.0 且 hasattr 门控下注册、非 Tensor 输入回落 sum（主线 110–121、发布 135–147） | 注册目标不全是 aten overload；版本门控意味着旧 torch 下没有该注册，不能跨 torch 版本外推 |

注册机制：`register_fx_node_ge_converter` 对 None 返回空函数，否则返回 `Converter`（fx2ge_converter.py 主线 539–552、发布 373–385）；`Converter.__call__` 优先把包装函数写为 `aten_op._ge_converter` 属性、写失败才落全局 `_CONVERTERS` 字典（主线 478–506、发布 320–339）。版本差异：主线注册机制带 lite converter 模式（539–552 读取 `_is_lite_converter_mode()` 函数属性开关 452–453，`__call__` 内 `_LITE_CONVERTER_OPS` 去重跳过 494–499），发布版 `__init__`/注册均无该分支——同一注册入口两版机制不同，但两版静态装饰器计数口径一致（均为字面注册）。主线另有 2 处变量目标的编程注册点：`ensure_triton_hop_converter_registered` 进程级一次注册 triton hop 转换器（custom_op_codegen_common.py:1632–1641）与自定义算子 codegen 的通用转换器注册（:2320–2329）；发布版无该文件——静态计数是下界，运行期可再增加。两版 docs 页本身仅两行差异（行 5 链接形态、行 69 fft2 约束栏，fft2 差异是本卡既有结论不重述）。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 460–552（`Converter` 464、`__init__` 472–477、`__call__` 478–506、`declare_supported` 520–524、`_is_lite_converter_mode` 452–453、`register_fx_node_ge_converter` 539–552）与 1030–1095（codegen 模板字符串三处）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 300–385（`Converter` 308、`__init__` 314–317、`__call__` 320–339、`_ge_converter` 属性写 336、`_CONVERTERS.update` 339、`register_fx_node_ge_converter` 373–385）；模板字符串行 701/849/867/885 rg 行号确认。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py)（implementation）：窗口 100–125（math.ceil 103–107、sym_sum 门控与注册 110–121）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py)（implementation）：窗口 120–147（math.ceil 125–132、sym_sum 门控 135–147）。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py)（implementation）：窗口 1630–1645、2320–2331（两处变量目标编程注册点；发布版无该文件）。
- 抽样行锚（rg + 定向 sed/Read 实读）：ge_converter/aten/ 下 sigmoid.py（主线 1–21、发布 1–22 全读）、native_layer_norm.py:22、constant_pad_nd.py:10、_adaptive_avg_pool2d.py:9、_log_softmax.py:10、grid_sampler_2d.py:9、max_pool2d_with_indices.py:4、convolution.py:281、_foreach_add.py:12/25/45、gelu.py:10、t.py:10、linspace.py:9、randint.py:40、max.py:11、sym_size.py:46、fft_fft2.py:4、expand.py:12、new_zeros.py:12、sort.py:12、searchsorted.py:14、bernoulli.py:28。附录页全量复读（主线 1–161、发布 diff+行 1–8/69 定向），151 个数据行两版一致。全部为静态读取，未 import/运行上游。
