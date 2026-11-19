---
type: Guide
title: FlexAttention 前向实际选路：短 Query、GQA 与动态分派
description: 解释主线 lowering 的 decoding 优先级、mask-out 条件、Python-only 分派与实际 wrapper 检查，避免把配置或短序列当作命中证明。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_dispatch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/scheduling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
created_at: '2026-11-10T11:45:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FlexAttention 前向实际选路：短 Query、GQA 与动态分派

## 固定范围

依据 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 FlexAttention lowering、dispatch、候选选择和 scheduling 消费者，按关键函数定向审阅。发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 不含本卡两份 `kernel/flex_attention*.py` 主源的对应精确路径；不把主线行为直接用于该发布版，也不推断它没有其他注意力路线。

未验证设备、梯度或收益；未知平台保持 `draft`、空列表。[文档层接口与 GQA](torch_npu_inductor_flex_attention.md)仍给出独立支持范围，本卡不因局部源码放宽产品矩阵。

## 先尝试 decoding，再进入普通前向

注册的 `higher_order.flex_attention` lowering 首先构建 score/mask 子图；Query/Key 和 Value 的 head 维小于 16 会在本处拒绝。BlockMask 元组长度 13 直接使用，长度 17 经指定切片归一化，其他长度报错；不是任意 PyTorch 内部布局都能直接传入。

`_use_flex_decoding()` 同时检查：

- Query 序列长度大于 0 且小于 128；batch 和 Query head 数是 Python/sympy 整数。
- `FORCE_USE_FLEX_ATTENTION` 未置真，且没有请求 `OUTPUT_MAX`。
- GQA 时 mask 的 head 维为 1；非 GQA 时为 1 或 Query head 数。
- `FloorDiv(Hq,Hkv)` 得到的 head 比值为正的 2 次幂。

因此短 Query 不是充分条件；普通接口支持的 GQA 整数倍也不都命中 decoding。这里只解释判据，不能用这层 FloorDiv 检查代替上游对整体 head 合法性的校验。

lowering 在移除 GPU backend 参数前保留 `BACKEND` 的值：明确选 `TRITON_DECODE` 却不满足上述判据会报错。满足判据后尝试生成 decoding kernel；该过程抛出 Exception 时会告警并落到普通 FlexAttention lowering。即使明确选了这个名字，也不能忽略后面的生成失败与实际产物。

`BACKEND`、`generate_with_caching` 随后从传给 NPU 模板的选项中移除，不能据 CUDA 后端字符串推断 NPU 使用了同名实现。这里的回退是另一条编译 lowering，不是自动退到 Eager 的证明。

## mask-out 与 fwd dispatch 另有条件

普通前向通过显式 score_mod 标记和子图是否直接返回首个 score 占位判断非恒等 score 修改；存在这种修改时不走本处 mask-out 路线。还需稀疏 BlockMask，即两个块大小不同时为 `NO_SPARSE_BLOCK_SIZE`。本固定源码的 `_supports_flex_attention_mask_out()` 直接返回真，因此不能把函数名解读成它已经逐设备/逐 wrapper 验证能力。

配置 `TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_DISPATCH_STRATEGY` 由模块配置读取，消费者只接受实际 `None`、`"fwd"`、`"bwd_dkdv"`；没有大小写归一化。选 `fwd` 还必须已经进入 mask-out，才为前向候选附上分派 plan；开关本身不创建缺失的 mask-out 条件。

plan 声明 `PYTHON_ONLY`：C++ wrapper、AOT 或 subgraph 上下文不具备能力时，在 `select_algorithm` 中解析为普通 primary caller，并记录回退原因；并非所有 wrapper 都会产生动态分支。存在 plan 也不代表对应候选最终被调优选中。

## 运行期看 full-block 元数据，不是重新判断全部 mask

最终 Python helper 接收四个元数据参数，但判断只使用 `FULL_KV_NUM_BLKS` 和 `FULL_KV_IDX`：两者存在且所有值均为零，才返回 `ALL_SPARSE_BLOCKS`；否则用 primary。`KV_NUM_BLKS/KV_IDX` 未参与这段判据。

这里的 all-sparse 表示没有 full blocks，部分可见块仍需要应用 mask，不等于所有 token 不可见或结果应全零。helper 通过 `torch.all(...).item()` 得到 Python 分支条件，应把这段运行期开销纳入实际测量；本卡没有测量或宣称它对任意稀疏度都有收益。

variant 生成时将 `HAS_FULL_BLOCKS=False`，并复用同一调用参数和 grid。代码生成还验证 primary/variant 的参数 ABI、grid、call sizes、输出契约及 mutated inputs；不匹配会抛断言，不能把分派当成任意两个注意力 kernel 可互换的接口。

该复合模板拒绝 Epilogue 节点；scheduling 也拒绝其 source-only codegen。后处理融合、离线生成与正常运行分派是不同能力，不能由 primary 可以编译推导 variant 的所有组合都已支持。

调试时分别保存 decoding 判据日志、生成失败告警、dispatch 回退原因和最终 wrapper 的分支/调用。对照数值、mask 内容变化与真实设备时间线之后，再比较首编译和稳态；本卡未新增 verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_dispatch.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/scheduling.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation）
