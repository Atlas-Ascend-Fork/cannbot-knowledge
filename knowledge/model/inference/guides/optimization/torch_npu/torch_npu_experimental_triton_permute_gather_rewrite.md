---
type: Guide
title: 实验 Triton permute 归约加载：几何、UB 分块与回退边界
description: 说明跨步归约 load 的 gather/trans 准入、资源预算、静态单配置与动态 H 无 marker 重写，区分局部早退和未捕获异常。
tags:
- task.optimization
- topic.compilation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/permute_gather_rewrite.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/device_props.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: implementation
created_at: '2026-11-11T08:44:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验 Triton 的 permute 归约加载重写

## 固定实现与使用范围

本文针对 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，完整读取 `permute_gather_rewrite.py` 的 635 行和下列有界消费者。发布 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 在本轮列出的六个精确路径没有 Git 条目；这不能推导发布没有 permute、归约或其他 Triton 优化。未执行导入、AST 表达式解释器、SymPy 运算、生成器、模板或设备，注释的测时与“不会编译失败”不作为本次验证结果。产品适用范围未知。

优化目标是在满足单内轴几何时，保留 permute 视图并改变消费端的加载，而不是一律先物化转置。lowering 先调用上游 permute；开启重写时，静态 stride 由 `permute_gather_mode` 决定是否保留原结果，未知 stride 仅在 dynamic-trans 开关开启时提前保留。这里还没有检查完整 reduction 几何，保留视图不保证后续实际发生重写。未提前返回才进入有界实现中的 TensorBox、内轴、producer 可物化条件；复制失败捕获 Exception 后返回上游结果，成功且有 buffer 名才登记 no-fuse。

## 记录准入与模式选择

load 先由上游生成结果，再调用 `_npu_pg_record`；即使记录失败，该调用方的 finally 仍恢复加载的临时状态。记录要求 `enable_permute_gather`、`codegen_linearize` 均开启、处于 reduction、不是 persistent reduction，且结果有 name。默认重写开关是 False。dtype 从原 buffer 的 `V.graph.get_dtype(name).itemsize` 取，异常退到 4 字节，不能用已经提升到 FP32 的结果变量 dtype 代替原 buffer。

静态 stride_r 必须大于 1。以 `stride_r * elemsize` 与默认 256 字节门槛比较：严格小于走 gather，否则走 trans。默认 4096 的 XBLOCK 上限**仅在 gather 分支检查**；trans 不被此条件拒绝，而是以默认 ktile=64 分块。256 是这里的模式阈值，不是此处检查的地址对齐条件。动态 stride 只有 `permute_gather_dynamic_trans=True` 才继续，并直接选择 trans；不能把静态 `stride_r>1` 检查外推到动态符号的数值合法性。

## 必须满足的索引几何

| 局部对象 | 实际检查 |
|---|---|
| reduction leaf | 恰一个；静态系数作 stride_r，符号系数需 dynamic-trans 开关 |
| 两个 free leaf | 一个系数为 1 的 interior，一个系数为 `stride_r * r_numel` 的 row；必须属于同一 x-tree |
| interior 长度 | 静态时等于 stride_r；动态时符号表达式直接等于 stride_r |
| reduction 长度 | 静态整数必须为正；动态表达式的 free symbols 须包含于此前收集的非 range-tree 尺寸符号 |
| 去掉所有线性项后的 residue | 必须是 `sympy.Number`，保存时调用 int；没有在这里单独证明所有外部表达式都是合法整数地址 |

非 range-tree 符号先作为尺寸参数延迟处理，不是遇到动态 shape 就全部拒绝；但残余动态 base offset 会因 residue 检查拒绝。额外 reduction/free leaf、意外系数、跨 x-tree、内轴长度不匹配都返回 None。记录以加载结果变量名为键保存，真正重写时要求候选字典恰一项，多项不会选择其中“最好”的一项。

## UB 和 Tensor 大小预算

静态 H 路径的有效内宽 `eff`：gather 为 stride_r，trans 为 `min(stride_r, ktile)`。局部公式为：

```text
budget = int(0.5 * get_npu_ub_size_bytes())
cap_numel = 1_048_576 // eff
cap_ub = max(1, budget // (3 * 4 * eff * 2))
raw = min(cap_numel, cap_ub[, 静态 r_numel])
R0_BLOCK = 不大于 max(1, raw) 的最大 2 次幂
```

三份 tile、统一按 4 字节和双份 pipeline 是本地预算模型；即使 trans 实际不生成 gather 索引，仍使用这套保守公式。它不逐项测量整个融合 kernel 的所有活跃对象，也不证明真实 UB 分配必然成功。这里的 getter 缓存 SoC 查询：本地 soc>=260 返回 256 KiB，否则或查询异常返回 192 KiB；这是代码门控和回退，不是产品支持矩阵或本次设备容量测量。

R0_BLOCK 向下取 2 次幂，避免任意非幂次 tile 与上游常量 reduction mask 假设错配；大 reduction 可因此分多次 r-loop。动态 reduction 长度不参与 min，仅用上述容量预算；**动态 H** 更进一步不计算 r0_block，也不 pin XBLOCK，由生成的 block_ptr 形状和 boundary checks 处理分块。动态 H 的行为不应套用静态路径的容量 pin 结论。

## 分块复核与单候选配置

真正发射发生在 codegen_body 之后。此时才从 `var_tensor_dims` 和 reduction tree 取 int/row/r 的 slot；要求三者都是 int、非负且不同，ndim 取最大 slot 加 1，不要求固定的相对顺序。静态 gather 强制 XBLOCK=stride_r，静态 trans 强制 XBLOCK=min(stride_r,ktile)。

`_npu_pg_eval_real_blocks` 从 XBLOCK 环境依次扫描 pre-loop 行：非字符串、不可解析或非单目标赋值略过；AnnAssign 先归一为 Assign。已成功绑定的同名值保留。解释器只处理整数常量/已绑定名、负号、加减乘整除取余、单个支持比较、条件表达式和无 kwargs 的 min/max；不支持表达式或运算异常只跳过当前赋值。没有执行任意 Python eval，但这种局部静态解释也不是完整语言求值。

复核要求 real_block_row=1、real_block_int=min(int_numel,pin)。不匹配保留原行。成功静态重写返回 XBLOCK/R0_BLOCK marker，codegen 写入 triton_meta；所读 reduction 消费者在 size_hints 长度为 2 或 3 时先于诊断 pin_xr 使用 marker，向 cached_autotune 传单个配置。不能把“调用了 cached_autotune”理解成还在扫描任意不同 tile。

动态 H 成功重写后也返回 None，含义是**不返回配置 marker**；此时 kernel.body 已被替换，并不是所有 None 都表示没有重写。该路径保留自由调优，不据此声称所有配置的外部编译已验证。

## gather 和 trans 的生成差别

模块通过 `_ast_helpers` 延迟导入三个 codegen 解析/赋值 helper 并保存为模块全局，避免模块级循环导入；导入本身没有在这里统一捕获异常。替换按 AST 匹配赋值目标名，只替换第一个找到的字符串 `tl.load`；DeferredLine 等非字符串原样保留。解析器允许加载外层 `.to(...)` 链，发射器要求首参数是裸指针名加索引的 BinOp。其他形状返回空列表保留原加载。

gather 每个 r-loop trip 只读取 `r_offset*stride_r + arange(stride_r*R0_BLOCK)` 的连续片段，以 row 与 segment 范围构造 load mask；再用 int offset 加 stride_r*r 的索引作 `tl.gather`。结果 reshape 为 r-last 的 `[1, real_block_int, real_block_row, R0_BLOCK]`，再用 reduction mask 与原 other 填充值选择，不按旧 slot 顺序误置 reduction 轴。

trans 建立 `[row, r, int]` block_ptr，stride 为 `[int_numel*r_numel, int_numel, 1]`，三个轴都做 boundary_check，越界 load padding 为 zero；按实际 slot 顺序决定 tl.trans 置换和 reshape，最后仍用 reduction mask/other。静态长度写常量、动态长度用对应 numel 名。不能把 trans 描述成先生成一份 int32 gather 索引。

两条路径都通过 AST 替换原 load 节点，保留外层表达式，包括原 `.to(tl.float32)` 提升。other 默认 0.0；gather 保留可 literal_eval 的 eviction_policy，默认 evict_last；非法 literal 的 ValueError/TypeError 拒绝重写。trans 没有把该 eviction_policy 传入自己的新 load。原 mask 被几何推导的 mask 替代，其他未专门处理的 load kwargs 也没有通用复制协议，不能称任意 load 属性都原样保留。

## 失败边界与排查

局部早退包括开关、几何、候选数、slot、tiling、赋值解析和负载形状不匹配；在成功发射前只积累 new_lines，最后才替换 body。它没有给完整调用链包一个总 except：例如 `_npu_pg_eval_real_blocks` 可能留下缺失的 int_numel，在 row 条件已成立而继续求 min 时仍可抛 TypeError；geometry 的外部对象协议、发射/AST 替换异常也未统一转换成 None。因此注释中的“只多跑几次、不会编译失败”不能升级为异常恢复保证，也没有在这里提供设备编译失败后自动重新编译原加载的协议。

排查时分别保留原 index、buffer 元素字节、几何和 residue、三 slot、有效内宽/预算/R0_BLOCK、pre-loop 实际绑定、最终替换行及 marker。再检查实际编译结果、动态边界和数值；本次没有执行这些运行检查。相关的[归约索引别名](torch_npu_experimental_triton_reduction_index_alias_contract.md)和[clone 布局/UB 模型](torch_npu_experimental_triton_clone_fold_and_load_rescue.md)是独立机制，不能用本次重写资格替代它们。

## Evidence

- [固定源码 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/permute_gather_rewrite.py)（primary）：1–635；完整本地重写实现，外部框架、parser 和设备生成结果另计。
- [固定源码 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：196–289；仅列出的有界源码。
- [固定源码 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/device_props.py)（implementation）：18–28、57–68；仅列出的有界源码。
- [固定源码 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py)（implementation）：481–611；仅列出的有界源码。
- [固定源码 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（implementation）：126–151、166–180、2345–2377、2548–2558、4751–4767；仅列出的有界源码。
- [固定源码 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（implementation）：2728–2757；仅列出的有界源码。
