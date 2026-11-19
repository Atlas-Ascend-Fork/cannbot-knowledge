---
type: Guide
title: 实验 Triton embedding：寄存器行 gather 的准入与回退
description: 保存 embedding 的本地 SoC/config 门控、间接坐标与寄存器 gather 几何，区分节点长度、真实 tile、常量 offset
  和外部 bound 合同。
tags:
- task.optimization
- topic.compilation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/device_props.py
  role: implementation
created_at: '2026-11-11T09:10:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验 Triton embedding：寄存器行 gather 的准入与回退

## 固定入口与局部产品门控

针对 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 embedding lowering、完整 index_select 发射器及所列 extension 导入和 SoC helper。整个 lowering、8617 行 codegen 与外部 CANN builtin 不在本卡范围。发布固定快照在这四个精确实验路径缺失，仅说明来源关系，不推导发布没有 embedding 优化。

代码把这条路线称为 A5；本文按 Ascend 950 系列（包含旧称 Atlas A5）描述其设计目标，**实际门控仍是本地 is_a5() 与配置**，不是产品支持认证。is_a5 先返回非 None 的 force_is_a5 配置，否则尝试底层 SoC getter，以 soc>=250 为 True，查询异常返回 False；这些编号和覆盖项不能扩成完整产品矩阵。此 helper 使用无参 lru_cache：上述是未命中缓存时的函数体逻辑，命中时不会重新读取后来改变的 force 配置或 SoC；本地没有自动刷新协议。没有导入、调用 SoC/IR/生成器、执行 SymPy 或设备验证，保持 draft 与空平台。

## embedding 入口并不直接保证扩展命中

npu_embedding 注册到 aten.embedding，type_promotion_kind=None。入口先要求 is_a5() 与 cann_index_select 同时为真；config 中后者默认 True。当前节点 meta.skip_lowering 为真、weight 不是二维、H 可证明等于 1，或 TensorBox 的 data 是 BaseView，都返回保存的上游路线；其他情况调用 `npu_lowering_index_select(weight,0,indices)`。

上游表项存在时 `_upstream()` 只传 weight、indices 两个参数；没有表项才通过 fallback_handler 显式传 padding_idx、scale_grad_by_freq、sparse。寄存器路径同样没有在这个函数内消费这三个选项，因此不能把这里当作全部 embedding 参数/反向合同的独立证明。

入口没有验证任意 weight 布局都连续，BaseView 检查也不等价于外部存储 offset、别名和所有嵌套表示均已认证。即使入口继续，后面的代码生成还会因具体 index、tile 或 mask 不符合局部条件而退到普通间接 load。

## Pointwise 生成与嵌套间接坐标

npu_lowering_index_select 以 assert 要求输入和 indices 都是 TensorBox，用 `"int" in str(indices.get_dtype())` 检查索引 dtype。输出尺寸用 indices 的全部尺寸替换选定轴；这里并没有把任意 select_dim 归一化成公共 index_select API，而本入口传的是轴 0。

inner_fn 要求坐标数量等于新尺寸数量，先加载 index 并调用 ops.indirect_indexing，再构造 weight 坐标。若任意输出坐标字符串包含 tmp 或 indirect，就直接 weight_loader；这是本地字符串判别，不是对任意嵌套表达式完成的结构证明。

其他情况尝试取得 weight indexer/名称，再调用 ops.index_select，传入 weight_index、原 index CSE 值、set_indirect 的字符串和 int(bound)。这个 try 的 Exception 退 weight_loader；但前面的 index 加载和 indirect_indexing 在 try 外，不存在整个 lowering 统一吞掉异常的合同。Pointwise 的 device、dtype 取自 weight，ranges 为上述新尺寸。

OpsHandler 与 dtype/shape 传播的注册见[激活与 IR 注册](torch_npu_experimental_triton_activation_and_lowering_routes.md)；其转发不等于设备 builtin 已执行。高级索引改成原生 index_select 链是[另一条独立路线](torch_npu_experimental_triton_separable_advanced_index.md)，本卡不重复摄取该实现。

## 发射器实际检查的几何

| 对象 | 本地要求或动作 |
|---|---|
| 间接轴 | weight_index.free_symbols 中恰一个 SymT.TMP |
| 行 stride H | 从系数字典取该 TMP 的系数，必须为正 int/SymPy Integer |
| 内轴 | 除 TMP 外恰一个符号；其系数经 int 转换后等于 1，且能找到对应 range-tree node |
| 内轴长度 | statically_known_equals(h_node.length,H) 必须成立 |
| 行 mask 身份 | indirect_var.mask_vars 中以 mask 结尾、且不等于 xmask 的项恰一个；去掉后缀后生成 real_block 行 token |
| 输出形状 | 从 TritonSymbols.get_block_shape(weight_index) 取得；index 临时形状优先用 indirect_var.shape |

这些是具体源码谓词：内轴系数检查没有另加完整整数类型验证；注释写“拒绝 constant offsets”，实际函数没有独立的常量 residue=0 检查。原存储 offset 是否能由其他前提排除仍需上游布局证据，不能只把注释变成已执行的准入规则。

同样，length==H 比较的是节点长度；发射时实际使用名为 real_block_<h> 的 tile token，没有在本函数再比较它运行时一定等于 H，也没有逐项确认所有 token 已定义或实际物理读取都合法。“完整 H 驻留”是该扩展的设计前提，不能由这里一个 length 谓词推广成所有调优配置都已证明满足。

## extension 表达式与真实边界

通过检查后，先发射 index reshape 为 `(row_block,)`，再按源 dtype 建立零值 `(row_block,h_block)` 输出；最后生成：

```text
extension.custom("__builtin_index_select", weight, index,
    dim=0, bound=int(bound),
    start_offset=(0,0), end_offset=(row_block,h_block),
    src_stride=(H,1), out=output)
```

set_indirect 虽随 ops 参数传入，此发射器没有独立消费该字符串；weight_index 的 TMP 仍被用于检查和普通 fallback。扩展表达式没有另传一份显式 mask，bound/end_offset 在底层如何处理越界、负索引、尾行和掩码未在本组展开，不能用变量名自行补全安全合同。

gen_triton_ext_imports 仅在 cann_index_select 与 is_a5 同时为真时插入 `import triton.language.extra.cann.extension as extension`。生成 import 文本不证明外部模块/API 兼容或 builtin 在当前设备可运行，也没有在这里安装实际设备库。

## fallback 与部分生成失败

不符合局部条件时 fallback_load 调用 kernel.load(src_name,weight_index)，保留带间接 TMP 的普通加载。发射器 try 内的 Exception 也交给该 fallback；它不重新选择独立 ATen embedding kernel，也没有在此执行失败设备 kernel 后再重编译的协议。

CSE/compute buffer 的中间发射发生在 try 内，后面异常转普通 load 时没有本地回滚此前所有 CSE 写入；fallback_load 本身继续失败也不保证被无限重试或吞掉。因此“任何不匹配都有普通 load 路线”不能升级成整个编译过程永不失败、或注释中的数值正确性已被设备验证。

排查时应保留有效门控、weight 原始 layout/offset、indices dtype/rank、skip 标记、TMP/系数、节点长度和真实 tile、mask 名、最终 bound/end_offset/stride、是否留下扩展或普通 load，以及真实数值/尾块表现。局部注册成功、候选生成或 fallback 存在都不代替完整模型的精度、反向、资源和性能验证；本次没有新增 verified。

## Evidence

- [固定源码 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py)（primary）：195–265；仅所列有界函数与分支，外部框架、真实 tile/存储不变量和设备 builtin 另计。
- [固定源码 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（implementation）：2031–2123、3788–3816；仅所列有界函数与分支，外部框架、真实 tile/存储不变量和设备 builtin 另计。
- [固定源码 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：40–44；仅所列有界函数与分支，外部框架、真实 tile/存储不变量和设备 builtin 另计。
- [固定源码 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/device_props.py)（implementation）：18–28、71–84；仅所列有界函数与分支，外部框架、真实 tile/存储不变量和设备 builtin 另计。
