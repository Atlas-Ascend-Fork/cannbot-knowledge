---
type: Guide
title: 实验Triton边界降精度：布局、副本缓存与输出回写
description: 区分metadata指针改写、输入/可变/纯输出缓冲、重叠布局的存储跨度、弱引用缓存及图池绕过条件。
tags:
- task.optimization
- topic.compilation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T08:09:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton边界降精度：布局、副本缓存与输出回写

## 固定路径与metadata入口

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf实验Triton的有界实现，区分signature改写、Tensor边界转换与计算本身。没有导入上游、建立图、转换Tensor、执行launcher或运行精度实验；平台未知，保持draft和空平台。外部PyTorch布局/版本计数、图池和实际生成kernel各自独立。

所列codegen片段将fp64标量和*fp64指针的signature分别改为fp32/*fp32，并记录原类型到downcast_args；*i64一般改为*i32，但_npu_has_wide_i64_const或_npu_int64_exempt标记成立时保留原*i64。后者注释对应宽整数常量及RNG需求，标记如何被设置不在此有界段。不能把这段注释推广成设备完全不支持全部INT64，也不能对所有kernel承诺统一降精度。

_wrap_downcast只在launcher尚无_npu_original_launcher且triton_meta.downcast_args非空时附包装；_make_launchers在launcher数等于compile_results数时早返回，否则委托上游创建后逐个包装。包装实际转换表只识别*i64→torch.int64/int32和*fp64→float64/float32，处理对应Tensor参数；scalar fp64的metadata改写不等于此wrapper会对Python标量执行Tensor转换。

## 按参数用途分配临时Tensor

包装从_npu_def_args取得位置名，缺失或为空就返回原launcher。只为downcast_args里已知类型建立cast_indices，参数名以in_out_ptr开头或出现在mutated_arg_names中表示保留输入；out_ptr前缀或这些可变参数都需要回写。

| 本地分类 | 临时Tensor与回写行为 |
| --- | --- |
| 只读输入 | 使用_memoized_downcast，命中时复用降精度副本，不加入回写表。 |
| in/out或mutated | 每次用保布局转换取得新副本，保留输入内容，并加入回写表。 |
| 纯out_ptr | 只创建相同shape/stride/device的empty_strided降精度缓冲，不把原输出内容当输入；加入回写表。 |

运行时若位置实参数量少于def_args，整个包装直接委托原launcher；未对同名kwargs补做转换。数量足够时也只转换实际为Tensor且dtype等于源dtype的项，其他实参保持。这里没有为任意跨参数共享Storage重建完整别名图，不能从单个Tensor的保步幅推导所有实参别名均保持。

转换完成后调用原launcher，正常返回才依序回写，最后返回原ret；没有finally保证异常时也完成回写，没有本地回滚或重新映射返回对象。这个wrapper解决的是部分指针dtype与ABI衔接，不检查整数值是否能装入INT32、浮点舍入误差或kernel中间算术溢出。

## 保步幅的转换和存储跨度

_to_dtype_preserving_layout在_debug_has_internal_overlap(src)==0时直接src.to(dst_dtype)。其他分类先计算_reachable_span：初值1，逐维在size非零时加stride*(size-1)；按原data_ptr覆盖跨度建立一维as_strided视图、转换其存储单元，再以原shape/stride包装。该函数没有独立校验任意负stride输入的合法性，不把注释的外部框架前提当作本地检查。

这样可以表达重叠、broadcast和带空隙view的本地转换路线，避免只按逻辑numel转连续后仍被kernel按原stride索引。代价是临时容量按span计算，可能大于numel；span>4*numel只记录DEBUG，并不拒绝分配或限制峰值。没有在此证明任意外部Storage布局、别名和精度都可用。

回写时只对orig的internal-overlap分类等于1使用同跨度的一维copy_，其余包括“too hard”分类2均用orig.copy_(tmp)。带空隙布局不能一律换成平坦copy，否则会写到逻辑view之外的存储单元。代码不捕获OOM或设备错误后改走另一种回写路线，异常按实际调用传播。

## 只读副本缓存的键与图池边界

_downcast_memo是模块级字典，以id(src)为键，值保存weakref、src._version、目标dtype和副本。命中须同时满足弱引用仍指向同一src、版本相同、dtype相同；源对象释放的weakref回调删除项。它不是按Tensor内容计算的哈希缓存，也不是按Storage为所有view共享一份副本。

npu_dedup_downcast为假、当前流正在capture，或检测到当前线程/设备图树manager.in_warmup时，都绕过memo但仍执行转换，避免这类临时Tensor被本地全局字典长期保留。图树helper只捕AttributeError/RuntimeError并返回False；取得src._version只对AttributeError回退，weakref构建只对TypeError退为不缓存，不能笼统描述成任意异常都被静默吞掉。

去重开关先从实验config赋给模块变量npu_dedup_downcast；所列config初始dedup_downcast=True、int64_boundary_cast=True，并最终安装config模块。缓存判断读取的是这个模块变量，不能把后续任意config.patch都当成已经追溯改变已捕获的值。所审wrapper本身按downcast_args与实参dtype决定转换，不在每次调用重新查询int64_boundary_cast配置。

包装复制config、runnable、寄存器/共享内存、cache_hash、静态/fast持有者和_npu_def_args等约定属性，留下_npu_original_launcher与_npu_downcast_wrapper供后续辨认。静态fast构建可能先取原launcher再套回这个包装，具体准入见[静态启动协议](torch_npu_experimental_triton_static_launch_contract.md)；不要把有包装标记当作所有参数都已转换或所有副本都缓存。

调优时应一起检查原signature与downcast_args、位置参数数量、输入/输出分类、跨度放大、capture/warmup状态、memo命中条件与回写完成情况。自动调优如何隔离候选输入和计时另见[调优输入与计时](torch_npu_experimental_triton_autotune_timing_and_input_isolation.md)，相关外部clone实现仍独立。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)：610–632、1657–1666、1683–1690、1693–1914；仅所列有界内容。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)：4661–4701；仅所列有界内容。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：141–143、471–471；仅所列有界内容。
